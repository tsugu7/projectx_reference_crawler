#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
リンク分割修正のテストスクリプト
"""

import re
import sys

def fix_markdown_links(markdown_content):
    """Markdown内のリンク分割問題を修正する"""

    # ステップ1: マークダウンリンク全体を検出
    link_pattern = re.compile(r'\[([^\]]*?)\]\(([^)]*?)\)')

    def fix_link(match):
        # リンクテキスト内の処理
        link_text = match.group(1)
        url = match.group(2)

        # 1. リンクテキスト内の改行を修正
        link_text = re.sub(r'\s*\n\s*', ' ', link_text)

        # 2. リンクテキスト内の複数スペースを単一スペースに
        link_text = re.sub(r'\s+', ' ', link_text).strip()

        # 3. APIエンドポイントパス内のスペースを削除
        # "/api/Path/ search" → "/api/Path/search" だが、"search Open" はそのまま
        if '/api/' in link_text or '/v1/' in link_text:
            # API パスのパターンを検出してスペースを削除
            link_text = re.sub(r'(\/[a-zA-Z0-9\/-]+\/)\s+([a-zA-Z0-9-]+)', r'\1\2', link_text)

        # 4. URL内のすべてのスペースを削除
        url = re.sub(r'\s', '', url)

        return f"[{link_text}]({url})"

    # パターンに一致するすべてのリンクを処理
    markdown_content = link_pattern.sub(fix_link, markdown_content)

    return markdown_content

def main():
    """テスト関数"""
    
    test_cases = [
        # テストケース1: ベーシックな改行パターン
        {
            "name": "基本的な改行パターン",
            "input": """# テストケース1
            
[Search    for    PositionsAPI    URL:    /api/Position/search
Open](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions)
            
これは基本的な改行パターンのテストです。""",
            "expected": """# テストケース1
            
[Search for PositionsAPI URL: /api/Position/search Open](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions)
            
これは基本的な改行パターンのテストです。"""
        },
        
        # テストケース2: URL内の改行
        {
            "name": "URL内の改行",
            "input": """## API リファレンス
            
[Position Search API](/api/
position/search)
            
URLが改行されています。""",
            "expected": """## API リファレンス
            
[Position Search API](/api/position/search)
            
URLが改行されています。"""
        },
        
        # テストケース3: 複数スペース
        {
            "name": "複数スペース",
            "input": """### エンドポイント一覧
            
[Get    User    Profile    API](/api/user/profile)
            
余分なスペースがあります。""",
            "expected": """### エンドポイント一覧
            
[Get User Profile API](/api/user/profile)
            
余分なスペースがあります。"""
        },
        
        # テストケース4: 複合パターン
        {
            "name": "複合パターン",
            "input": """#### 複合テスト
            
[Search    for    
PositionsAPI    
URL:    /api/Position/
search](https://gateway.docs.
projectx.com/docs/api-reference/positions)
            
これは複数の問題が組み合わさったケースです。""",
            "expected": """#### 複合テスト
            
[Search for PositionsAPI URL: /api/Position/search](https://gateway.docs.projectx.com/docs/api-reference/positions)
            
これは複数の問題が組み合わさったケースです。"""
        }
    ]
    
    # 各テストケースを実行
    for i, test_case in enumerate(test_cases):
        print(f"\n===== テストケース {i+1}: {test_case['name']} =====")
        
        # 入力を表示
        print("\n< 修正前 >")
        print("-" * 60)
        print(test_case["input"])
        print("-" * 60)
        
        # 修正を適用
        result = fix_markdown_links(test_case["input"])
        
        # 結果を表示
        print("\n< 修正後 >")
        print("-" * 60)
        print(result)
        print("-" * 60)
        
        # 期待される結果と比較
        if result.strip() == test_case["expected"].strip():
            print("\n✅ テスト成功!")
        else:
            print("\n❌ テスト失敗!")
            print("\n期待される結果:")
            print("-" * 60)
            print(test_case["expected"])
            print("-" * 60)
    
    print("\nすべてのテストが完了しました。")

if __name__ == "__main__":
    main()