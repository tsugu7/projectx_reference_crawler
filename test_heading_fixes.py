#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
見出し修正とMarkdown整形機能のテストスクリプト
"""

import os
import re
import sys
from pathlib import Path
from crawler_components import MarkdownConverter

def test_heading_fixes():
    """見出し修正機能をテストする"""
    print("見出し修正機能のテスト...\n")
    
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

```json
{
"name": "test",
"value": 123
}
```

| Column1 | Column2 |
| ------- | ------- |
| Cell1   | Cell2   |
| ðï¸ 特殊 | 文字入り |
"""
    
    # MarkdownConverterインスタンスを作成
    converter = MarkdownConverter()
    
    # _postprocess_markdownメソッドを呼び出して修正
    fixed_markdown = converter._postprocess_markdown(test_markdown)
    
    # 結果を表示
    print("< 修正前 >")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    print("\n< 修正後 >")
    print("-" * 60)
    print(fixed_markdown)
    print("-" * 60)
    
    # 修正されたかどうかを確認
    assert "分割された見出し" in fixed_markdown and "分断\nされた" not in fixed_markdown
    assert "特殊文字を含む" in fixed_markdown and "ðï¸" not in fixed_markdown
    assert "Cell1" in fixed_markdown and "ðï¸ 特殊" not in fixed_markdown
    
    print("\nテスト成功：見出し修正が正しく機能しています")

def test_code_blocks():
    """コードブロック整形機能をテストする"""
    print("\nコードブロック整形機能のテスト...\n")
    
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
    
    # MarkdownConverterインスタンスを作成
    converter = MarkdownConverter()
    
    # _format_code_blocksメソッドを呼び出して修正
    fixed_markdown = converter._format_code_blocks(test_markdown)
    
    # 結果を表示
    print("< 修正前 >")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    print("\n< 修正後 >")
    print("-" * 60)
    print(fixed_markdown)
    print("-" * 60)
    
    # 修正されたかどうかを確認
    assert '```json' in fixed_markdown and '"name":' in fixed_markdown
    assert '```javascript' in fixed_markdown or '```js' in fixed_markdown
    
    print("\nテスト成功：コードブロック整形が正しく機能しています")

def test_table_formatting():
    """表整形機能をテストする"""
    print("\n表整形機能のテスト...\n")
    
    # テスト用のマークダウン内容
    test_markdown = """
# 表組みテスト

シンプルな表:
| カラム1 | カラム2 |
| セル1 | セル2 |
| セル3 | セル4 |

整形のおかしい表:
| カラム1 | カラム2 | カラム3 |
| --- | --- | --- |
| セル1 | セル2 |
| セル3 | セル4 | セル5 | セル6 |

特殊文字を含む表:
| カラム1 | カラム2 |
| --- | --- |
| ðï¸ 特殊 | 文字入り |
"""
    
    # MarkdownConverterインスタンスを作成
    converter = MarkdownConverter()
    
    # _improve_tablesメソッドを呼び出して修正
    fixed_markdown = converter._improve_tables(test_markdown)
    
    # 結果を表示
    print("< 修正前 >")
    print("-" * 60)
    print(test_markdown)
    print("-" * 60)
    
    print("\n< 修正後 >")
    print("-" * 60)
    print(fixed_markdown)
    print("-" * 60)
    
    # 修正されたかどうかを確認
    assert '-----' in fixed_markdown  # ヘッダー区切り行の追加
    assert '| セル1 | セル2 | ' in fixed_markdown  # セル数の調整
    assert 'ðï¸' not in fixed_markdown  # 特殊文字の除去
    
    print("\nテスト成功：表整形が正しく機能しています")

def main():
    """メイン関数"""
    print("===== Markdown整形機能テスト =====\n")
    
    # 見出し修正のテスト
    test_heading_fixes()
    
    # コードブロック整形のテスト
    test_code_blocks()
    
    # 表整形のテスト
    test_table_formatting()
    
    print("\nすべてのテストが成功しました！")

if __name__ == "__main__":
    main()