#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude APIを使用してHTML変換後のMarkdownを整形するモジュール
"""

import os
import re
import json
import logging
import requests
import time
from typing import Dict, Optional, List, Any
import argparse

# 環境変数からAPIキーを取得
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

class ClaudeFormatter:
    """
    Claude APIを使用してMarkdownを整形するクラス
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = CLAUDE_MODEL):
        """
        初期化
        
        Args:
            api_key: Anthropic API Key（なければ環境変数から取得）
            model: 使用するClaudeモデル名
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model
        
        # APIキーがない場合はエラー
        if not self.api_key:
            raise ValueError("APIキーが設定されていません。環境変数ANTHROPIC_API_KEYを設定するか、コンストラクタで指定してください。")
        
        # ロガーを設定
        self.logger = logging.getLogger("ClaudeFormatter")
        
        # 整形用プロンプトテンプレート
        self.format_prompt = """
あなたはMarkdown整形の専門家です。与えられたMarkdownファイルを分析し、より読みやすく、構造的に正しい形式に整形してください。

特に以下の点に注意して整形してください：

1. 見出し構造を修正してください：
   - 見出しが適切に階層化されているか確認する
   - 見出しの前後に適切な改行がない場合は追加する
   - 見出しが連結している場合（## [A]()## [B]()）は分割して適切な改行を入れる
   - 「## Getting Started ProjectX Trading」のような見出し+テキストパターンは分割する

2. 特殊文字を処理してください：
   - 「ðï」「ðï¸」などの不要な特殊文字を削除する
   - 絵文字や制御文字を適切に処理する

3. リンクを修正してください：
   - 改行を含むリンクを適切に結合する
   - リンク内のURL部分に含まれる改行やスペースを削除する
   - URLエンコードされた文字（%20など）を適切に処理する

4. テーブル形式を整えてください：
   - テーブルの前後に適切な改行を入れる
   - 列の幅を揃え、整列を適切に設定する

5. コードブロックを適切に整形してください：
   - JSON、コードなどの構文を分析し、適切な言語タグを付ける
   - インデントを整える
   - cURLコマンド内のJSONは整形しない

下記のMarkdownコンテンツを整形し、読みやすく構造的に正しい形に変換してください。

内容を理解してから整形を行い、元のコンテンツの意味や情報が失われないよう注意してください。

生成されるOutputは整形後のMarkdownのみにしてください。余分な説明は不要です。

---
{content}
---
"""
    
    def format_markdown(self, markdown_content: str, max_retries: int = 3, retry_delay: int = 2) -> str:
        """
        Claude APIを使用してMarkdownを整形する
        
        Args:
            markdown_content: 整形するMarkdownコンテンツ
            max_retries: 最大リトライ回数
            retry_delay: リトライ間の待機時間（秒）
            
        Returns:
            整形されたMarkdownコンテンツ
        """
        if not markdown_content or not markdown_content.strip():
            return markdown_content
        
        # コンテンツを長すぎる場合は分割して処理
        if len(markdown_content) > 100000:
            return self._process_large_content(markdown_content)
        
        # プロンプトを作成
        prompt = self.format_prompt.replace("{content}", markdown_content)
        
        # APIリクエストの準備
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "max_tokens": 100000,  # 十分な長さを確保
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # リクエスト実行（リトライあり）
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Claude APIにリクエスト送信中 (試行 {attempt + 1}/{max_retries})...")
                response = requests.post(CLAUDE_API_URL, headers=headers, json=data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    formatted_content = result.get("content", [{}])[0].get("text", "")
                    self.logger.info("Markdownの整形に成功しました")
                    return formatted_content
                else:
                    error_info = response.text
                    try:
                        error_info = json.loads(error_info)
                    except:
                        pass
                    self.logger.error(f"APIエラー: {response.status_code}, {error_info}")
                    
                    # レート制限エラーの場合は長めに待機
                    if response.status_code == 429:
                        wait_time = retry_delay * 5
                        self.logger.info(f"レート制限に達しました。{wait_time}秒後にリトライします...")
                        time.sleep(wait_time)
                    else:
                        time.sleep(retry_delay)
            
            except Exception as e:
                self.logger.error(f"リクエスト実行エラー: {e}")
                time.sleep(retry_delay)
        
        # すべてのリトライが失敗した場合は元のコンテンツを返す
        self.logger.warning("Claude APIでの整形に失敗しました。元のコンテンツを返します。")
        return markdown_content
    
    def _process_large_content(self, markdown_content: str) -> str:
        """
        大きなコンテンツを分割して処理する
        
        Args:
            markdown_content: 整形する大きなMarkdownコンテンツ
            
        Returns:
            整形されたMarkdownコンテンツ
        """
        self.logger.info("コンテンツが長すぎるため分割して処理します...")
        
        # 最初にセクション単位で分割を試みる
        sections = self._split_by_headers(markdown_content)
        
        if len(sections) <= 1 or max(len(s) for s in sections) > 90000:
            # セクション分割がうまくいかない場合は、固定サイズで分割
            chunks = self._split_by_size(markdown_content, chunk_size=90000)
        else:
            chunks = sections
        
        self.logger.info(f"コンテンツを{len(chunks)}個のチャンクに分割しました")
        
        # 各チャンクを処理
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            self.logger.info(f"チャンク {i+1}/{len(chunks)} を処理中...")
            formatted_chunk = self.format_markdown(chunk)
            formatted_chunks.append(formatted_chunk)
            
            # APIレート制限を回避するために少し待機
            if i < len(chunks) - 1:
                time.sleep(2)
        
        # 結合
        return "\n\n".join(formatted_chunks)
    
    def _split_by_headers(self, markdown_content: str) -> List[str]:
        """
        ヘッダーでコンテンツを分割する
        
        Args:
            markdown_content: 分割するMarkdownコンテンツ
            
        Returns:
            分割されたセクションのリスト
        """
        # 大見出し（# または ##）でコンテンツを分割
        header_pattern = r'^#{1,2}\s+'
        lines = markdown_content.split('\n')
        
        sections = []
        current_section = []
        
        for line in lines:
            if re.match(header_pattern, line) and current_section:
                # 新しいセクションが始まったら、現在のセクションを保存
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # 最後のセクションを追加
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _split_by_size(self, content: str, chunk_size: int = 90000) -> List[str]:
        """
        コンテンツを指定サイズで分割する
        
        Args:
            content: 分割するコンテンツ
            chunk_size: 各チャンクの最大サイズ
            
        Returns:
            分割されたチャンクのリスト
        """
        if len(content) <= chunk_size:
            return [content]
        
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > chunk_size and current_chunk:
                # チャンクが最大サイズに達したら保存して新しいチャンクを開始
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def format_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        ファイルを読み込んで整形し、結果を保存する
        
        Args:
            input_path: 入力ファイルのパス
            output_path: 出力ファイルのパス（Noneの場合は入力ファイルを上書き）
            
        Returns:
            出力ファイルのパス
        """
        # ファイルが存在するか確認
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"ファイルが見つかりません: {input_path}")
        
        # 出力パスの設定
        if output_path is None:
            output_path = input_path
        
        # ファイル読み込み
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 整形処理
        formatted_content = self.format_markdown(content)
        
        # 結果を保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        return output_path
    
    def process_directory(self, input_dir: str, output_dir: Optional[str] = None, pattern: str = "*.md") -> Dict[str, str]:
        """
        ディレクトリ内のファイルを一括で処理する
        
        Args:
            input_dir: 入力ディレクトリのパス
            output_dir: 出力ディレクトリのパス（Noneの場合は入力ディレクトリと同じ）
            pattern: 処理対象のファイルパターン
            
        Returns:
            処理したファイルの辞書 {入力パス: 出力パス}
        """
        import glob
        
        # 出力ディレクトリの設定
        if output_dir is None:
            output_dir = input_dir
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # ファイル一覧を取得
        file_paths = glob.glob(os.path.join(input_dir, pattern))
        processed_files = {}
        
        self.logger.info(f"{len(file_paths)}個のファイルが見つかりました")
        
        # 各ファイルを処理
        for input_path in file_paths:
            try:
                file_name = os.path.basename(input_path)
                output_path = os.path.join(output_dir, file_name)
                
                self.logger.info(f"ファイルを処理中: {file_name}")
                self.format_file(input_path, output_path)
                
                processed_files[input_path] = output_path
                self.logger.info(f"ファイルの処理が完了しました: {file_name}")
                
                # APIレート制限を回避するために少し待機
                time.sleep(2)
            
            except Exception as e:
                self.logger.error(f"ファイル処理エラー {input_path}: {e}")
        
        return processed_files

def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )

def main():
    """メイン実行関数"""
    setup_logging()
    logger = logging.getLogger("claude_formatter")
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description="Claude APIを使用してMarkdownファイルを整形します")
    parser.add_argument("input", help="入力ファイルまたはディレクトリのパス")
    parser.add_argument("-o", "--output", help="出力ファイルまたはディレクトリのパス（指定しない場合は入力を上書き）")
    parser.add_argument("-k", "--api-key", help="Anthropic API Key（指定しない場合は環境変数から取得）")
    parser.add_argument("-m", "--model", default=CLAUDE_MODEL, help=f"使用するClaudeモデル（デフォルト: {CLAUDE_MODEL}）")
    
    args = parser.parse_args()
    
    try:
        # フォーマッターの初期化
        formatter = ClaudeFormatter(api_key=args.api_key, model=args.model)
        
        # 入力の種類によって処理を分岐
        if os.path.isdir(args.input):
            # ディレクトリ処理
            logger.info(f"ディレクトリ処理: {args.input}")
            processed_files = formatter.process_directory(args.input, args.output)
            logger.info(f"{len(processed_files)}個のファイルの処理が完了しました")
        else:
            # 単一ファイル処理
            logger.info(f"ファイル処理: {args.input}")
            output_path = formatter.format_file(args.input, args.output)
            logger.info(f"処理完了: {output_path}")
    
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())