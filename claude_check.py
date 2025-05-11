#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude APIの利用可能性をチェックするユーティリティ
"""

import os
import sys
import logging
import requests
import json

def check_claude_api():
    """
    Claude APIが利用可能かチェックする
    
    Returns:
        tuple: (bool: 利用可能か, str: 状態メッセージ, dict: 追加情報)
    """
    # APIキーの確認
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "APIキーが設定されていません", {"tip": "環境変数 ANTHROPIC_API_KEY を設定してください"}
    
    # モデル名の確認（デフォルト値があるので常に有効）
    model = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
    
    # APIへの接続テスト（軽量なリクエスト）
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # 最小限のプロンプトでトークン数だけ取得
        data = {
            "model": model,
            "max_tokens": 1,
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages", 
            headers=headers,
            json=data,
            timeout=10
        )
        
        # レスポンスの解析
        if response.status_code == 200:
            return True, "Claude APIは正常に利用可能です", {"model": model}
        else:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "不明なエラー")
                return False, f"API接続エラー: {error_message}", {"status_code": response.status_code}
            except json.JSONDecodeError:
                return False, f"API接続エラー: HTTP {response.status_code}", {"response": response.text[:100]}
    
    except requests.exceptions.RequestException as e:
        return False, f"API接続エラー: {str(e)}", {}
    except Exception as e:
        return False, f"予期せぬエラー: {str(e)}", {}

if __name__ == "__main__":
    # ロギングの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # APIの状態をチェック
    available, message, info = check_claude_api()
    
    if available:
        logging.info(f"✓ {message}")
        if "model" in info:
            logging.info(f"モデル: {info['model']}")
        sys.exit(0)
    else:
        logging.error(f"✗ {message}")
        for key, value in info.items():
            logging.info(f"{key}: {value}")
        sys.exit(1)