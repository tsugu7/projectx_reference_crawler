#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
正規表現パターンのテストスクリプト
"""

import re

def test_heading_fixes():
    """見出し修正の正規表現をテスト"""
    print("\n===== 見出し修正パターンのテスト =====\n")
    
    # テスト用のマークダウン内容
    test_markdown = """
# 見出しテスト

## [
分割された見出し] (https://example.com)

### ðï¸ 特殊文字を含む
見出し

## 改行で分断
された見出し

## [ðï¸ カテゴリ](https://example.com/category)
これはカテゴリの説明文です。

## [別のカテゴリ](https://example.com/other)これは区切りのない説明文
"""

    # 特殊文字を先に削除
    test_markdown = test_markdown.replace('ðï¸', '')
    test_markdown = test_markdown.replace('ðï', '')
    
    # 見出し修正の正規表現パターン群
    patterns = [
        # 見出しタグの後の改行を修正
        (r'(#{1,6})\s*\n\s*', r'\1 '),
        
        # 見出しのリンク開始括弧内の改行を修正
        (r'(#{1,6}\s*)\[\s*\n\s*', r'\1['),
        
        # 見出しのリンクテキスト内の改行を修正
        (r'(\[\s*[^\n\]]*)\n\s*([^\]]*\])', r'\1 \2'),
        
        # 見出しのリンク全体の途中改行を修正
        (r'(#{1,6}\s+\[[^\]]+\])\s*\n\s*(\([^)]+\))', r'\1\2'),
        
        # 見出し全体が複数行に分かれている場合を修正
        (r'(#{1,6}\s+[A-Za-z][^\n]*)\s*\n\s*([A-Za-z][^\n]*)', r'\1 \2'),
        
        # リンク後の説明文を適切に区切る処理
        (r'(\]\([^)]+\))([\w])', r'\1\n\2'),
        
        # 見出し + URL + 説明文のパターンをより強固に処理
        (r'(#{1,6}\s+\[[^\]]+\]\([^)]+\))\s+([A-Z][a-z])', r'\1\n\n\2')
    ]
    
    # 修正前を表示
    print("< 修正前 >")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    # 各パターンを順番に適用
    for i, (pattern, replacement) in enumerate(patterns):
        test_markdown = re.sub(pattern, replacement, test_markdown)
        print(f"\n適用後 {i+1}: {pattern} -> {replacement}")
        print("-" * 60)
        print(test_markdown)
        print("-" * 60)
    
    print("\n見出し修正パターンのテスト完了!")

def test_code_block_patterns():
    """コードブロック検出の正規表現をテスト"""
    print("\n===== コードブロック検出パターンのテスト =====\n")
    
    # テスト用のマークダウン内容
    test_markdown = """
# コードブロックテスト

インラインJSONの例:
{"name": "test", "values": [1, 2, 3], "nested": {"key": "value"}}

コードブロック例:
```
function test() {
  console.log("hello");
}
```

言語付きコードブロック:
```javascript
const x = 10;
function hello() {
  return "world";
}
```

JSON例:
```json
{
"invalid": format,
'single': 'quotes',
}
```

未整形コード:
if (condition) {
  doSomething();
  if (nested) {
    moreActions();
  }
}
"""

    # コードブロック検出パターン
    code_block_pattern = r'```(?:json|javascript|js|typescript|ts|python|py|bash|sh|xml|html|css)?\s*\n(.*?)\n```'
    
    # インラインJSONパターン
    inline_json_pattern = r'(\{\s*"[^"]+"\s*:(?:[^{}]|(?:\{\s*(?:[^{}]|(?:\{\s*[^{}]*\s*\}))*\s*\}))*\})'
    
    # 修正前を表示
    print("< テスト対象 >")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    # コードブロックの検出
    print("\n検出されたコードブロック:")
    matches = re.finditer(code_block_pattern, test_markdown, re.DOTALL)
    for i, match in enumerate(matches):
        code = match.group(1)
        lang = match.group(0).split('```')[1].strip() if '```' in match.group(0) else ''
        print(f"\nコードブロック {i+1} (言語: {lang or '未指定'}):")
        print("-" * 40)
        print(code)
        print("-" * 40)
    
    # インラインJSONの検出
    print("\n検出されたインラインJSON:")
    matches = re.finditer(inline_json_pattern, test_markdown)
    for i, match in enumerate(matches):
        json_text = match.group(1)
        print(f"\nインラインJSON {i+1}:")
        print("-" * 40)
        print(json_text)
        print("-" * 40)
    
    # 未整形コードブロックの検出
    print("\n未整形コードブロックの検出テスト:")
    lines = test_markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 開始ブレース・括弧があるかチェック
        if not line.startswith('#') and not line.startswith('```') and (
            ('{' in line and line.endswith('{')) or
            ('(' in line and line.endswith('('))
        ):
            start_idx = i
            block_content = [lines[i]]
            matching_char = '}' if '{' in line else ')'
            
            # 終了ブレース・括弧を探す
            found_end = False
            for j in range(i + 1, min(i + 10, len(lines))):
                if matching_char in lines[j]:
                    block_content.append(lines[j])
                    end_idx = j
                    found_end = True
                    break
                block_content.append(lines[j])
            
            if found_end:
                code_text = "\n".join(block_content)
                print(f"\n未整形コードブロック (行 {start_idx+1}-{end_idx+1}):")
                print("-" * 40)
                print(code_text)
                print("-" * 40)
                i = end_idx  # 次の位置に進む
        
        i += 1
    
    print("\nコードブロック検出パターンのテスト完了!")

def test_table_patterns():
    """表検出と修正の正規表現をテスト"""
    print("\n===== 表検出パターンのテスト =====\n")
    
    # テスト用のマークダウン内容
    test_markdown = """
# 表組みテスト

シンプルな表:
| カラム1 | カラム2 |
| セル1 | セル2 |
| セル3 | セル4 |

整形済みの表:
| カラム1 | カラム2 | カラム3 |
| --- | --- | --- |
| セル1 | セル2 | セル3 |
| セル4 | セル5 | セル6 |

特殊文字を含む表:
| カラム1 | カラム2 |
| --- | --- |
| ðï¸ 特殊 | 文字入り |
"""

    # 表検出パターン
    table_pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n)+)'
    
    # シンプルな表のパターン（ヘッダーなし）
    simple_table_pattern = r'(\|[^\n]+\|\n(?:\|[^\n]+\|\n){2,})'
    
    # 修正前を表示
    print("< テスト対象 >")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    # 表の検出（ヘッダー付き）
    print("\n検出された表（ヘッダー付き）:")
    matches = re.finditer(table_pattern, test_markdown, re.DOTALL)
    for i, match in enumerate(matches):
        table = match.group(1)
        print(f"\n表 {i+1}:")
        print("-" * 40)
        print(table)
        print("-" * 40)
    
    # シンプルな表の検出（ヘッダーなし）
    print("\n検出されたシンプルな表（ヘッダーなし）:")
    matches = re.finditer(simple_table_pattern, test_markdown)
    found_simple = False
    for i, match in enumerate(matches):
        table = match.group(1)
        # ヘッダー区切り行を含む表は除外
        if not re.search(r'\|[-:| ]+\|', table):
            found_simple = True
            print(f"\nシンプルな表 {i+1}:")
            print("-" * 40)
            print(table)
            print("-" * 40)
            
            # シンプルな表にヘッダー区切り行を追加する例
            lines = table.strip().split('\n')
            header_line = lines[0]
            cells_count = header_line.count('|') - 1
            sep_line = '|' + '|'.join([' ----- ' for _ in range(cells_count)]) + '|'
            
            # 新しい表を構築
            new_table = [lines[0], sep_line] + lines[1:]
            
            print("\n修正後:")
            print("-" * 40)
            print('\n'.join(new_table))
            print("-" * 40)
    
    if not found_simple:
        print("シンプルな表（ヘッダーなし）は検出されませんでした。")
    
    print("\n表検出パターンのテスト完了!")

def main():
    """メイン関数"""
    print("===== 正規表現パターンテスト =====")
    
    # 見出し修正の正規表現をテスト
    test_heading_fixes()
    
    # コードブロック検出の正規表現をテスト
    test_code_block_patterns()
    
    # 表検出と修正の正規表現をテスト
    test_table_patterns()
    
    print("\nすべてのテストが完了しました！")

if __name__ == "__main__":
    main()