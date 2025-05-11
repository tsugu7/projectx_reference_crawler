#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
リンク修正機能の実際のテスト
"""

import sys
from crawler_components import MarkdownConverter

def test_link_conversion():
    """リンク修正のライブテスト"""
    
    # 問題のあるHTMLを作成（マークダウン変換時に問題を起こす）
    html_content = """
    <h2>API リファレンス</h2>
    
    <h3>Positions API</h3>
    
    <ul>
        <li>
            <a href="/api/Position/search">
                Search    for    PositionsAPI    URL:    /api/Position/search
                Open
            </a>
        </li>
        <li>
            <a href="/api/
            Position/details">Position Details API</a>
        </li>
        <li>
            <a href="/api/v1/Position/
            history">
                Position    History    
                API
            </a>
        </li>
    </ul>
    
    <h3>Orders API</h3>
    
    <ul>
        <li><a href="/api/Order/create">Create Order</a></li>
        <li><a href="/api/Order/cancel">Cancel Order</a></li>
    </ul>
    """
    
    # URLダミー
    url = "https://gateway.docs.projectx.com/docs/api-reference"
    
    # ページデータ作成
    page_data = {
        'url': url,
        'title': 'API Reference Test',
        'html_content': html_content,
        'meta_description': 'API reference documentation test'
    }
    
    # MarkdownConverterインスタンスを作成
    converter = MarkdownConverter()
    
    # 変換を実行
    result = converter.convert(page_data)
    
    # 結果を表示
    print("== 変換結果 ==")
    print("=" * 60)
    print(result['markdown_content'])
    print("=" * 60)
    
    # リンクが含まれている行を抽出
    lines = result['markdown_content'].split('\n')
    link_lines = [line for line in lines if '[' in line and '](' in line]
    
    print("\n== リンク行のみ ==")
    print("-" * 60)
    for line in link_lines:
        print(line)
    print("-" * 60)
    
    # チェックポイント
    check_phrases = [
        "Search for PositionsAPI URL: /api/Position/search Open",
        "Position Details API",
        "Position History API"
    ]
    
    print("\n== リンク修正検証 ==")
    for phrase in check_phrases:
        found = any(phrase in line for line in link_lines)
        status = "✓ 成功" if found else "✗ 失敗"
        print(f"{status}: '{phrase}' が見つかる")

if __name__ == "__main__":
    test_link_conversion()