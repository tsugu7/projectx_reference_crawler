#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Markdownファイル内の連結見出しの修正を行うスタンドアロンスクリプト
"""

import re
import os
import sys
import glob

def fix_markdown_headings(file_path):
    """ファイル内の連結見出しを修正する"""
    try:
        # ファイルを読み込む
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修正前の内容を保存
        original_content = content
        
        # 見出し連結パターンを修正
        concatenated_pattern = r'(#{1,6}\s*\[[^\]]+\]\([^)]+\))(#{1,6}\s*\[)'
        content = re.sub(concatenated_pattern, r'\1\n\n\2', content)
        
        # 異なるレベルの見出し連結を処理
        level_mix_pattern = r'(#{1,6}[^\n\#]{1,50})(#{1,6}\s*\[)'
        content = re.sub(level_mix_pattern, r'\1\n\n\2', content)
        
        # 空白を含む連結見出しを処理
        spaced_pattern = r'(#{1,6}\s*\[[^\]]+\]\([^)]+\))\s{2,}(#{1,6})'
        content = re.sub(spaced_pattern, r'\1\n\n\2', content)
        
        # 変更がない場合は何もしない
        if content == original_content:
            print(f"- {os.path.basename(file_path)}: 変更なし")
            return False
        
        # 変更がある場合は上書き保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {os.path.basename(file_path)}: 連結見出しを修正しました")
        return True
        
    except Exception as e:
        print(f"✗ {os.path.basename(file_path)}: エラー: {e}")
        return False

def process_directory(directory, pattern="*.md"):
    """ディレクトリ内のMarkdownファイルを処理する"""
    print(f"\n===== {directory} のMarkdownファイルを処理中 =====\n")
    
    # ファイルを検索
    files = glob.glob(os.path.join(directory, pattern))
    
    # 結果を集計
    total = len(files)
    fixed = 0
    
    # 各ファイルを処理
    for file_path in files:
        if fix_markdown_headings(file_path):
            fixed += 1
    
    # 結果を表示
    print(f"\n処理完了: {total}ファイル中{fixed}ファイルを修正しました")

def main():
    """メイン関数"""
    # コマンドライン引数を取得
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        
        # ディレクトリかファイルかを判定
        if os.path.isdir(path):
            process_directory(path)
        elif os.path.isfile(path):
            fix_markdown_headings(path)
        else:
            print(f"エラー: {path} はファイルもディレクトリも存在しません")
    else:
        # 引数がない場合はカレントディレクトリを処理
        process_directory(".")

if __name__ == "__main__":
    main()