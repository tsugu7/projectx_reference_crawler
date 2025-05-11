#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
マークダウン内の連結見出しを修正するユーティリティ
crawler_components.pyに組み込むための関数
"""

import re

def fix_concatenated_headings(markdown_content):
    """
    マークダウンテキスト内の連結された見出しを修正する
    最もシンプルかつ確実な方法

    Args:
        markdown_content (str): 修正するマークダウンコンテンツ

    Returns:
        str: 連結見出しを修正済みのマークダウンコンテンツ
    """
    # 1. 基本的なヘッダーパターン : ## [何か](URL)## [別の何か]
    pattern1 = r'(\#{1,6}\s*\[[^\]]+\]\([^)]+\))(\#{1,6}\s*\[)'
    markdown_content = re.sub(pattern1, r'\1\n\n\2', markdown_content)

    # 2. 空白を含む連結見出し : ## [何か](URL)    ## [別の何か]
    pattern2 = r'(\#{1,6}\s*\[[^\]]+\]\([^)]+\))\s{2,}(\#{1,6})'
    markdown_content = re.sub(pattern2, r'\1\n\n\2', markdown_content)

    # 3. 異なるレベルの見出し連結 : ### テキスト## [リンク付き見出し]
    pattern3 = r'(\#{1,6}[^\n\#]{1,50})(\#{1,6}\s*\[)'
    markdown_content = re.sub(pattern3, r'\1\n\n\2', markdown_content)

    # 4. 見出し後にテキストが続く : ## Getting Started ProjectX Trading
    pattern4 = r'(\#{1,6}\s+[A-Za-z][A-Za-z0-9\s]+)\s+([A-Z][a-z])'
    markdown_content = re.sub(pattern4, r'\1\n\n\2', markdown_content)

    # 5. 複数の連続改行を2つに標準化
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

    return markdown_content