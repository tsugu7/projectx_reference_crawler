#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ビジュアルクローリングモジュール
WebページのスクリーンショットからOCRを使用してコンテンツを抽出し、
マークダウンに変換する機能を提供します。
"""

import os
import time
import logging
import re
import base64
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class VisualCrawler:
    """
    ビジュアルクローリングのためのクラス
    スクリーンショットベースでWebページからコンテンツを抽出します
    """
    
    def __init__(self, config=None):
        """
        コンストラクタ
        
        Args:
            config: 設定オブジェクト（オプション）
        """
        self.config = config or {}
        self.browser = None
        
        # OCR言語設定
        self.ocr_lang = self.config.get('ocr_lang', 'eng+jpn')
        
        # 出力設定
        self.output_dir = self.config.get('output_dir', 'visual_output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # スクリーンショット保存設定
        self.save_screenshots = self.config.get('save_screenshots', True)
        
        # ロギング設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('VisualCrawler')
    
    def setup_browser(self):
        """ブラウザを初期化"""
        try:
            # Chromeオプションの設定
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # 日本語フォントのサポート
            chrome_options.add_argument("--lang=ja")
            
            # ChromeDriverをセットアップ
            service = Service(ChromeDriverManager().install())
            
            # ブラウザインスタンスを生成
            self.browser = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("ブラウザセットアップ完了")
            
            return True
        
        except Exception as e:
            self.logger.error(f"ブラウザセットアップエラー: {e}")
            return False
    
    def crawl_url(self, url):
        """
        指定されたURLをクロールしてビジュアル情報を抽出
        
        Args:
            url: クロール対象のURL
            
        Returns:
            dict: 抽出結果データ
        """
        if not self.browser:
            if not self.setup_browser():
                return {"error": "ブラウザのセットアップに失敗しました"}
        
        try:
            # ページにアクセス
            self.logger.info(f"ページにアクセス中: {url}")
            self.browser.get(url)
            
            # ページのロードを待機
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # JavaScript実行完了のため少し待機
            time.sleep(3)
            
            # ページタイトルを取得
            title = self.browser.title
            
            # スクリーンショットの取得
            self.logger.info("スクリーンショットを取得中...")
            full_page_screenshot = self.take_full_page_screenshot()
            
            if self.save_screenshots:
                # スクリーンショットを保存
                domain = self.extract_domain(url)
                screenshot_path = os.path.join(self.output_dir, f"{domain}_screenshot.png")
                cv2.imwrite(screenshot_path, full_page_screenshot)
                self.logger.info(f"スクリーンショットを保存しました: {screenshot_path}")
            
            # スクリーンショットからテキストを抽出
            self.logger.info("OCRを実行中...")
            extracted_text = self.extract_text_from_image(full_page_screenshot)
            
            # ドキュメント構造を解析
            self.logger.info("ドキュメント構造を解析中...")
            document_structure = self.analyze_document_structure(full_page_screenshot, extracted_text)
            
            # マークダウンに変換
            self.logger.info("マークダウンに変換中...")
            markdown_content = self.convert_to_markdown(document_structure, title, url)
            
            # 結果を返す
            result = {
                "url": url,
                "title": title,
                "markdown_content": markdown_content
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"クロールエラー: {e}")
            return {"error": str(e)}
    
    def take_full_page_screenshot(self):
        """
        ページ全体のスクリーンショットを取得
        
        Returns:
            numpy.ndarray: スクリーンショット画像
        """
        # ページの高さを取得
        page_height = self.browser.execute_script("return document.body.scrollHeight")
        
        # ビューポートの高さを取得
        viewport_height = self.browser.execute_script("return window.innerHeight")
        
        # スクロール回数を計算
        num_scrolls = int(page_height / viewport_height) + 1
        
        # スクリーンショットのリスト
        screenshots = []
        
        # ページを少しずつスクロールしながらスクリーンショットを取得
        for i in range(num_scrolls):
            # 現在のスクロール位置
            scroll_top = i * viewport_height
            
            # スクロール
            self.browser.execute_script(f"window.scrollTo(0, {scroll_top});")
            time.sleep(0.2)  # スクロール後に少し待機
            
            # スクリーンショットを取得
            screenshot = self.browser.get_screenshot_as_base64()
            screenshot_data = base64.b64decode(screenshot)
            
            # PILイメージとして読み込み
            img = Image.open(BytesIO(screenshot_data))
            
            # numpy配列に変換（OpenCV形式）
            screenshots.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        
        # すべてのスクリーンショットを結合
        if len(screenshots) == 1:
            return screenshots[0]
        
        # 複数のスクリーンショットを垂直方向に結合
        full_screenshot = cv2.vconcat(screenshots)
        
        return full_screenshot
    
    def extract_text_from_image(self, image):
        """
        画像からOCRでテキストを抽出
        
        Args:
            image: OpenCV形式の画像
            
        Returns:
            str: 抽出されたテキスト
        """
        try:
            # グレースケールに変換
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # ノイズ除去
            gray = cv2.medianBlur(gray, 3)
            
            # コントラスト強調
            gray = cv2.equalizeHist(gray)
            
            # pytesseractを使用してOCR実行
            extracted_text = pytesseract.image_to_string(gray, lang=self.ocr_lang)
            
            return extracted_text
        
        except Exception as e:
            self.logger.error(f"テキスト抽出エラー: {e}")
            return ""
    
    def analyze_document_structure(self, image, text):
        """
        ドキュメント構造を解析
        
        Args:
            image: OpenCV形式の画像
            text: 抽出されたテキスト
            
        Returns:
            dict: ドキュメント構造情報
        """
        # 画像からレイアウト情報を取得
        layout_data = self.extract_layout_info(image)
        
        # テキストの行に分割
        lines = text.split('\n')
        
        # 各行の行高を推定
        line_heights = self.estimate_line_heights(lines)
        
        # 見出しを検出
        headings = self.detect_headings(lines, line_heights, layout_data)
        
        # リストを検出
        lists = self.detect_lists(lines, layout_data)
        
        # 表を検出
        tables = self.detect_tables(image, layout_data)
        
        # 画像を検出
        images = self.detect_images(image, layout_data)
        
        # コードブロックを検出
        code_blocks = self.detect_code_blocks(lines, layout_data)
        
        # ドキュメント構造を構築
        document_structure = {
            "text": text,
            "lines": lines,
            "headings": headings,
            "lists": lists,
            "tables": tables,
            "images": images,
            "code_blocks": code_blocks
        }
        
        return document_structure
    
    def extract_layout_info(self, image):
        """
        画像からレイアウト情報を抽出
        
        Args:
            image: OpenCV形式の画像
            
        Returns:
            dict: レイアウト情報
        """
        # レイアウト解析の実装（単純な例）
        height, width = image.shape[:2]
        
        # 線を検出（表の境界線を見つけるのに役立つ）
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 水平・垂直線の検出
        horizontal_lines = []
        vertical_lines = []
        
        # ハフ変換で線を検出
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(x2 - x1) > abs(y2 - y1):  # 水平線
                    horizontal_lines.append((x1, y1, x2, y2))
                else:  # 垂直線
                    vertical_lines.append((x1, y1, x2, y2))
        
        # 領域を検出（単純な例 - 実際にはより高度な実装が必要）
        regions = {
            "top": (0, 0, width, height // 4),
            "middle": (0, height // 4, width, height * 3 // 4),
            "bottom": (0, height * 3 // 4, width, height)
        }
        
        return {
            "width": width,
            "height": height,
            "horizontal_lines": horizontal_lines,
            "vertical_lines": vertical_lines,
            "regions": regions
        }
    
    def estimate_line_heights(self, lines):
        """
        テキスト行の高さを推定
        
        Args:
            lines: テキスト行のリスト
            
        Returns:
            list: 各行の推定高さ
        """
        # 単純な実装 - 実際にはフォントサイズなどからの推定が必要
        line_heights = []
        
        for line in lines:
            # 行の文字数と先頭の#の数に基づく単純な高さ推定
            if line.strip().startswith('#'):
                # 見出しの場合、#の数に応じて高さを設定
                heading_level = len(re.match(r'^#+', line.strip()).group())
                line_heights.append(7 - heading_level)  # h1が最も大きく、h6が最も小さい
            elif len(line.strip()) > 0:
                # 通常のテキスト
                line_heights.append(1)
            else:
                # 空行
                line_heights.append(0)
        
        return line_heights
    
    def detect_headings(self, lines, line_heights, layout_data):
        """
        見出しを検出
        
        Args:
            lines: テキスト行のリスト
            line_heights: 各行の高さ
            layout_data: レイアウト情報
            
        Returns:
            list: 検出された見出し情報
        """
        headings = []
        
        for i, line in enumerate(lines):
            text = line.strip()
            if not text:
                continue
            
            # パターンによる見出し検出（'#'で始まる行や行末が':'で終わる行）
            if re.match(r'^#+\s+', text) or text.endswith(':'):
                level = 1
                if re.match(r'^#+\s+', text):
                    level = len(re.match(r'^#+', text).group())
                
                # 行高に基づく見出しレベルの調整
                if i < len(line_heights) and line_heights[i] > 1:
                    if level > line_heights[i]:
                        level = line_heights[i]
                
                # 見出しテキストを整形（'#'を除去）
                heading_text = re.sub(r'^#+\s+', '', text).rstrip(':')
                
                headings.append({
                    "level": level,
                    "text": heading_text,
                    "line_index": i
                })
        
        return headings
    
    def detect_lists(self, lines, layout_data):
        """
        リストを検出
        
        Args:
            lines: テキスト行のリスト
            layout_data: レイアウト情報
            
        Returns:
            list: 検出されたリスト情報
        """
        lists = []
        current_list = None
        
        for i, line in enumerate(lines):
            text = line.strip()
            
            # 箇条書きパターンの検出
            bullet_match = re.match(r'^[-*•]\s+(.+)$', text)
            ordered_match = re.match(r'^(\d+)[.)]\s+(.+)$', text)
            
            if bullet_match:
                if current_list is None or current_list["type"] != "unordered":
                    # 新しい箇条書きリストを開始
                    current_list = {
                        "type": "unordered",
                        "items": [],
                        "start_line": i,
                        "end_line": i
                    }
                    lists.append(current_list)
                
                # リストアイテムを追加
                current_list["items"].append(bullet_match.group(1))
                current_list["end_line"] = i
                
            elif ordered_match:
                if current_list is None or current_list["type"] != "ordered":
                    # 新しい番号付きリストを開始
                    current_list = {
                        "type": "ordered",
                        "items": [],
                        "start_line": i,
                        "end_line": i
                    }
                    lists.append(current_list)
                
                # リストアイテムを追加
                current_list["items"].append(ordered_match.group(2))
                current_list["end_line"] = i
                
            elif text == "" and current_list is not None:
                # 空行でリストが終了
                current_list = None
        
        return lists
    
    def detect_tables(self, image, layout_data):
        """
        表を検出
        
        Args:
            image: OpenCV形式の画像
            layout_data: レイアウト情報
            
        Returns:
            list: 検出された表情報
        """
        tables = []
        
        # 水平線と垂直線から表の候補を検出
        h_lines = layout_data["horizontal_lines"]
        v_lines = layout_data["vertical_lines"]
        
        # 線の交差ポイントを見つける簡易な実装
        # 実際にはより高度なアルゴリズムが必要
        if len(h_lines) > 1 and len(v_lines) > 1:
            # 表の可能性がある領域を見つける
            h_lines_y = sorted([line[1] for line in h_lines])
            v_lines_x = sorted([line[0] for line in v_lines])
            
            # 表の行数と列数を推定
            row_count = len(h_lines) - 1
            col_count = len(v_lines) - 1
            
            if row_count > 0 and col_count > 0:
                # 表の候補を検出
                table_data = {
                    "rows": row_count,
                    "cols": col_count,
                    "cells": []
                }
                
                # 単純なセルデータを作成（実際にはOCRで各セルのテキストを検出）
                for r in range(row_count):
                    row = []
                    for c in range(col_count):
                        cell = {
                            "row": r,
                            "col": c,
                            "text": f"[Cell {r},{c}]"  # 実際にはOCRで検出
                        }
                        row.append(cell)
                    table_data["cells"].append(row)
                
                tables.append(table_data)
        
        return tables
    
    def detect_images(self, image, layout_data):
        """
        画像を検出
        
        Args:
            image: OpenCV形式の画像
            layout_data: レイアウト情報
            
        Returns:
            list: 検出された画像情報
        """
        # この実装では、実際の画像検出は行いません
        # 実際の実装では、画像認識やオブジェクト検出が必要です
        return []
    
    def detect_code_blocks(self, lines, layout_data):
        """
        コードブロックを検出
        
        Args:
            lines: テキスト行のリスト
            layout_data: レイアウト情報
            
        Returns:
            list: 検出されたコードブロック情報
        """
        code_blocks = []
        in_code_block = False
        current_block = None
        
        for i, line in enumerate(lines):
            # コードブロックの開始・終了を示す可能性のあるパターン
            if line.strip() in ['```', '~~~'] or re.match(r'^```\w*$', line.strip()):
                if not in_code_block:
                    # コードブロック開始
                    language = ""
                    lang_match = re.match(r'^```(\w+)$', line.strip())
                    if lang_match:
                        language = lang_match.group(1)
                    
                    current_block = {
                        "language": language,
                        "content": [],
                        "start_line": i,
                        "end_line": None
                    }
                    in_code_block = True
                else:
                    # コードブロック終了
                    current_block["end_line"] = i
                    code_blocks.append(current_block)
                    current_block = None
                    in_code_block = False
            elif in_code_block and current_block is not None:
                # コードブロック内容を追加
                current_block["content"].append(line)
        
        # 閉じられていないコードブロックを処理
        if in_code_block and current_block is not None:
            current_block["end_line"] = len(lines) - 1
            code_blocks.append(current_block)
        
        return code_blocks
    
    def convert_to_markdown(self, document_structure, title, url):
        """
        ドキュメント構造をマークダウンに変換
        
        Args:
            document_structure: ドキュメント構造データ
            title: ページタイトル
            url: ページURL
            
        Returns:
            str: マークダウンテキスト
        """
        markdown_lines = []
        
        # タイトル
        markdown_lines.append(f"# {title}")
        markdown_lines.append("")
        
        # URL情報
        markdown_lines.append(f"*出典: {url}*")
        markdown_lines.append("")
        
        # ドキュメント構造からマークダウン生成
        lines = document_structure["lines"]
        headings = document_structure["headings"]
        lists = document_structure["lists"]
        tables = document_structure["tables"]
        code_blocks = document_structure["code_blocks"]
        
        # 行ごとに処理
        skip_until_line = -1
        for i, line in enumerate(lines):
            if i <= skip_until_line:
                continue
            
            # この行が見出しかチェック
            heading_match = next((h for h in headings if h["line_index"] == i), None)
            if heading_match:
                level = heading_match["level"]
                text = heading_match["text"]
                markdown_lines.append(f"{'#' * level} {text}")
                markdown_lines.append("")
                continue
            
            # この行がリストの一部かチェック
            list_match = next((l for l in lists if l["start_line"] <= i <= l["end_line"]), None)
            if list_match:
                if i == list_match["start_line"]:
                    # リストの開始
                    markdown_lines.append("")
                    for j, item in enumerate(list_match["items"]):
                        prefix = "* " if list_match["type"] == "unordered" else f"{j+1}. "
                        markdown_lines.append(f"{prefix}{item}")
                    markdown_lines.append("")
                    skip_until_line = list_match["end_line"]
                continue
            
            # この行がコードブロックの一部かチェック
            code_block_match = next((c for c in code_blocks if c["start_line"] <= i <= c["end_line"]), None)
            if code_block_match:
                if i == code_block_match["start_line"]:
                    # コードブロックの開始
                    lang = code_block_match["language"]
                    markdown_lines.append(f"```{lang}")
                    for content_line in code_block_match["content"]:
                        markdown_lines.append(content_line)
                    markdown_lines.append("```")
                    markdown_lines.append("")
                    skip_until_line = code_block_match["end_line"]
                continue
            
            # 通常のテキスト行
            if line.strip():
                markdown_lines.append(line)
                # 段落が続く場合は改行を追加しない
                if i + 1 < len(lines) and not lines[i + 1].strip():
                    markdown_lines.append("")
        
        # 表の追加
        if tables:
            markdown_lines.append("")
            markdown_lines.append("## 検出された表")
            markdown_lines.append("")
            
            for table in tables:
                # 表ヘッダー
                markdown_lines.append("| " + " | ".join([f"列{j+1}" for j in range(table["cols"])]) + " |")
                # 表区切り
                markdown_lines.append("| " + " | ".join(["----" for j in range(table["cols"])]) + " |")
                
                # 表内容
                for row in table["cells"]:
                    markdown_lines.append("| " + " | ".join([cell["text"] for cell in row]) + " |")
                
                markdown_lines.append("")
        
        # マークダウンテキストを結合
        markdown_text = "\n".join(markdown_lines)
        
        return markdown_text
    
    def extract_domain(self, url):
        """
        URLからドメイン名を抽出
        
        Args:
            url: URL文字列
            
        Returns:
            str: ドメイン名
        """
        # URLからドメイン部分を抽出
        domain = url.split('//')[-1].split('/')[0]
        # 特殊文字を除去
        domain = re.sub(r'[^a-zA-Z0-9]', '_', domain)
        return domain
    
    def close(self):
        """リソースを解放"""
        if self.browser:
            self.browser.quit()
            self.browser = None

def crawl_url_visual(url, config=None):
    """
    URLを視覚的にクロールして結果を返す
    
    Args:
        url: クロール対象のURL
        config: 設定オブジェクト（オプション）
        
    Returns:
        dict: クロール結果
    """
    crawler = VisualCrawler(config)
    try:
        result = crawler.crawl_url(url)
        return result
    finally:
        crawler.close()

if __name__ == "__main__":
    # テスト用コード
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"URLをクロール中: {url}")
        
        result = crawl_url_visual(url)
        
        if "error" in result:
            print(f"エラー: {result['error']}")
        else:
            print(f"タイトル: {result['title']}")
            print("マークダウン内容:")
            print(result['markdown_content'][:500] + "...")
            
            # 結果をファイルに保存
            output_path = os.path.join("visual_output", f"{result['title'].replace(' ', '_')}.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['markdown_content'])
            print(f"結果を保存しました: {output_path}")
    else:
        print("使用方法: python visual_crawler.py <URL>")