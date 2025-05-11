#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webサイトクローラー：同一ドメイン内のすべてのコンテンツをMarkdown形式で出力し、
完了後にDiscordに通知を送信するプログラム
前回からの差分検知機能付き
"""

import requests
import html2text
from urllib.parse import urlparse, urljoin
import time
import os
import logging
import re
import json
import hashlib
from collections import deque
from typing import Set, Dict, List, Optional, Tuple, Any
import markdown
import pdfkit
from discord_webhook import DiscordWebhook, DiscordEmbed
import lxml.html
import argparse
import sqlite3
from datetime import datetime
import difflib


class UrlFilter:
    """URLをフィルタリングして、同一ドメイン内のURLのみを許可するコンポーネント"""
    
    def __init__(self, base_url: str):
        """
        URLフィルタークラスの初期化
        
        Args:
            base_url (str): クロールする基本URL
        """
        self.base_domain = urlparse(base_url).netloc
        self.base_url = base_url
        self.static_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', 
            '.js', '.pdf', '.zip', '.tar', '.gz', '.mp3', 
            '.mp4', '.avi', '.mov', '.webm', '.webp', '.ico'
        }
    
    def normalize_url(self, url: str) -> str:
        """
        URLを正規化する（相対URLを絶対URLに変換、フラグメントの削除等）
        
        Args:
            url (str): 正規化する URL
        
        Returns:
            str: 正規化された URL
        """
        # 相対URLを絶対URLに変換
        normalized_url = urljoin(self.base_url, url)
        
        # フラグメント (#) を削除
        normalized_url = normalized_url.split('#')[0]
        
        # トレーリングスラッシュを統一
        if normalized_url.endswith('/'):
            normalized_url = normalized_url[:-1]
            
        return normalized_url
    
    def should_crawl(self, url: str) -> bool:
        """
        URLがクロール対象かどうかを判定する
        
        Args:
            url (str): 判定する URL
        
        Returns:
            bool: クロール対象の場合は True、そうでない場合は False
        """
        # 空のURLはクロールしない
        if not url:
            return False
        
        # URLを正規化
        url = self.normalize_url(url)
        
        # URLのドメインを取得
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # 同一ドメインでない場合はクロールしない
        if domain != self.base_domain:
            return False
        
        # 静的ファイルはクロールしない
        path = parsed_url.path.lower()
        if any(path.endswith(ext) for ext in self.static_extensions):
            return False
        
        # メールアドレスリンクはクロールしない
        if url.startswith('mailto:'):
            return False
        
        # 電話番号リンクはクロールしない
        if url.startswith('tel:'):
            return False
            
        return True


class Fetcher:
    """指定されたURLからHTMLコンテンツを取得するコンポーネント"""
    
    def __init__(self, delay: float = 1.0, max_retries: int = 3, timeout: int = 10):
        """
        Fetcherクラスの初期化
        
        Args:
            delay (float): リクエスト間の遅延秒数（サーバー負荷軽減のため）
            max_retries (int): 最大再試行回数
            timeout (int): リクエストタイムアウト秒数
        """
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_request_time = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
    def fetch(self, url: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Tuple[Optional[str], Dict[str, str]]:
        """
        URLからHTMLコンテンツを取得する
        
        Args:
            url (str): コンテンツを取得するURL
            etag (Optional[str]): 前回取得時のETag
            last_modified (Optional[str]): 前回取得時のLast-Modified
        
        Returns:
            Tuple[Optional[str], Dict[str, str]]: (取得したHTMLコンテンツ, レスポンスヘッダー情報)
                                                 取得失敗時はコンテンツはNone
        """
        # リクエスト間隔を確保する
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        
        # 条件付きリクエスト用ヘッダーを準備
        headers = self.headers.copy()
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified
            
        retries = 0
        while retries <= self.max_retries:
            try:
                self.last_request_time = time.time()
                response = requests.get(url, headers=headers, timeout=self.timeout)
                
                # 304 Not Modified の場合、コンテンツは変更されていない
                if response.status_code == 304:
                    logging.info(f"Content not modified: {url}")
                    return None, {
                        'etag': etag,
                        'last_modified': last_modified,
                        'status_code': 304
                    }
                
                # ステータスコードが200以外の場合は失敗とみなす
                if response.status_code != 200:
                    logging.warning(f"Failed to fetch {url}: status code {response.status_code}")
                    retries += 1
                    time.sleep(self.delay * (2 ** retries))  # 指数バックオフ
                    continue
                
                # content-typeがHTMLでない場合はスキップ
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type.lower():
                    logging.info(f"Skipping non-HTML content: {url}, Content-Type: {content_type}")
                    return None, {'status_code': response.status_code, 'content_type': content_type}
                
                # ヘッダー情報を取得
                headers_info = {
                    'etag': response.headers.get('ETag'),
                    'last_modified': response.headers.get('Last-Modified'),
                    'content_type': content_type,
                    'status_code': response.status_code
                }
                
                return response.text, headers_info
                
            except requests.RequestException as e:
                logging.error(f"Error fetching {url}: {e}")
                retries += 1
                if retries <= self.max_retries:
                    time.sleep(self.delay * (2 ** retries))  # 指数バックオフ
                else:
                    return None, {'status_code': 0, 'error': str(e)}
        
        return None, {'status_code': 0, 'error': 'Max retries exceeded'}


class Parser:
    """HTMLコンテンツを解析し、コンテンツとリンクを抽出するコンポーネント（BeautifulSoup非使用）"""
    
    def __init__(self, url_filter: UrlFilter):
        """
        Parserクラスの初期化
        
        Args:
            url_filter (UrlFilter): URLフィルターインスタンス
        """
        self.url_filter = url_filter
    
    def parse(self, html: str, url: str) -> Tuple[Dict, List[str]]:
        """
        HTMLからコンテンツとリンクを抽出する
        
        Args:
            html (str): 解析するHTMLコンテンツ
            url (str): HTMLのURL（リンクの絶対URL化に使用）
        
        Returns:
            Tuple[Dict, List[str]]: (抽出したコンテンツ, 抽出したリンクのリスト)
        """
        try:
            # lxmlを使用してHTMLを解析
            doc = lxml.html.fromstring(html)
            
            # タイトルを抽出
            title_elem = doc.xpath('//title')
            title = title_elem[0].text_content().strip() if title_elem else "No Title"
            
            # メインコンテンツを抽出 (lxmlのXPath機能を使用)
            content_selectors = [
                '//main', '//article', 
                '//div[@class="content"]', '//div[@id="content"]', 
                '//div[@class="post-content"]'
            ]
            
            content_elem = None
            for selector in content_selectors:
                elements = doc.xpath(selector)
                if elements:
                    content_elem = elements[0]
                    break
            
            # メインコンテンツが見つからない場合はbody全体を使用
            if not content_elem:
                body_elem = doc.xpath('//body')
                content_elem = body_elem[0] if body_elem else doc
            
            # HTMLコンテンツを取得（lxml.html.tostring を使用）
            html_content = lxml.html.tostring(content_elem, encoding='unicode')
            
            # リンクを抽出
            links = []
            for a_tag in doc.xpath('//a[@href]'):
                href = a_tag.get('href')
                if self.url_filter.should_crawl(href):
                    normalized_url = self.url_filter.normalize_url(href)
                    links.append(normalized_url)
            
            # ページ情報の辞書を作成
            page_data = {
                'url': url,
                'title': title,
                'html_content': html_content,
            }
            
            return page_data, links
            
        except Exception as e:
            logging.error(f"Error parsing HTML from {url}: {e}")
            # エラー時は空のデータと空のリンクリストを返す
            return {'url': url, 'title': 'Error', 'html_content': ''}, []


class MarkdownConverter:
    """HTMLコンテンツをMarkdown形式に変換するコンポーネント"""
    
    def __init__(self):
        """
        MarkdownConverterクラスの初期化
        """
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = False
        self.converter.ignore_tables = False
        self.converter.body_width = 0  # 行の折り返しを無効化
        self.converter.unicode_snob = True  # Unicode文字を維持
        self.converter.single_line_break = True  # 単一の改行を維持
        
    def convert(self, page_data: Dict) -> Dict:
        """
        HTMLをMarkdownに変換する
        
        Args:
            page_data (Dict): 変換するページデータ
        
        Returns:
            Dict: Markdownに変換されたページデータ
        """
        title = page_data['title']
        html_content = page_data['html_content']
        url = page_data['url']
        
        # HTMLをMarkdownに変換
        markdown_content = self.converter.handle(html_content)
        
        # Markdownタイトルを作成
        markdown_title = f"# {title}\n\n"
        
        # URL情報を追加
        url_info = f"*Source: {url}*\n\n"
        
        # 最終的なMarkdownコンテンツを組み立て
        full_markdown = markdown_title + url_info + markdown_content
        
        # 結果を返す
        result = page_data.copy()
        result['markdown_content'] = full_markdown
        
        return result


class CrawlCache:
    """クロール結果を永続的に保存し、差分検知に使用するコンポーネント"""
    
    def __init__(self, domain: str, cache_dir: str = "cache"):
        """
        CrawlCacheクラスの初期化
        
        Args:
            domain (str): キャッシュを保存するドメイン名
            cache_dir (str): キャッシュディレクトリ
        """
        self.domain = domain
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.db_path = os.path.join(cache_dir, f"{domain}.db")
        self._initialize_db()
        
    def _initialize_db(self):
        """データベースを初期化する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # pages テーブルを作成
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            title TEXT,
            content_hash TEXT,
            etag TEXT,
            last_modified TEXT,
            last_crawled TEXT,
            markdown_content TEXT
        )
        ''')
        
        # crawl_history テーブルを作成
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_date TEXT,
            page_count INTEGER,
            new_count INTEGER,
            updated_count INTEGER,
            deleted_count INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_page(self, url: str) -> Optional[Dict]:
        """
        URLに対応するキャッシュされたページ情報を取得する
        
        Args:
            url (str): 取得するページのURL
        
        Returns:
            Optional[Dict]: キャッシュされたページ情報、存在しない場合はNone
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM pages WHERE url = ?', (url,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def add_or_update_page(self, page_data: Dict) -> bool:
        """
        ページ情報をキャッシュに追加または更新する
        
        Args:
            page_data (Dict): 追加/更新するページデータ
        
        Returns:
            bool: 更新された場合はTrue、新規追加の場合はFalse
        """
        url = page_data['url']
        title = page_data['title']
        markdown_content = page_data.get('markdown_content', '')
        content_hash = self._compute_hash(markdown_content)
        etag = page_data.get('etag')
        last_modified = page_data.get('last_modified')
        last_crawled = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 既存のページかチェック
        cursor.execute('SELECT content_hash FROM pages WHERE url = ?', (url,))
        row = cursor.fetchone()
        
        is_update = row is not None
        
        if is_update:
            # 更新
            cursor.execute('''
            UPDATE pages 
            SET title = ?, content_hash = ?, etag = ?, last_modified = ?, 
                last_crawled = ?, markdown_content = ?
            WHERE url = ?
            ''', (title, content_hash, etag, last_modified, last_crawled, markdown_content, url))
        else:
            # 新規追加
            cursor.execute('''
            INSERT INTO pages 
            (url, title, content_hash, etag, last_modified, last_crawled, markdown_content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (url, title, content_hash, etag, last_modified, last_crawled, markdown_content))
        
        conn.commit()
        conn.close()
        
        return is_update
    
    def get_all_urls(self) -> Set[str]:
        """
        キャッシュに保存されているすべてのURLを取得する
        
        Returns:
            Set[str]: キャッシュされているすべてのURL
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT url FROM pages')
        urls = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        
        return urls
    
    def delete_urls(self, urls: List[str]) -> int:
        """
        指定されたURLをキャッシュから削除する
        
        Args:
            urls (List[str]): 削除するURLのリスト
        
        Returns:
            int: 削除されたURLの数
        """
        if not urls:
            return 0
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ', '.join(['?'] * len(urls))
        cursor.execute(f'DELETE FROM pages WHERE url IN ({placeholders})', urls)
        
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def save_crawl_history(self, page_count: int, new_count: int, updated_count: int, deleted_count: int) -> int:
        """
        クロール履歴を保存する
        
        Args:
            page_count (int): クロールしたページの総数
            new_count (int): 新規追加されたページ数
            updated_count (int): 更新されたページ数
            deleted_count (int): 削除されたページ数
        
        Returns:
            int: 履歴のID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        crawl_date = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO crawl_history 
        (crawl_date, page_count, new_count, updated_count, deleted_count)
        VALUES (?, ?, ?, ?, ?)
        ''', (crawl_date, page_count, new_count, updated_count, deleted_count))
        
        history_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return history_id
    
    def get_latest_crawl_history(self) -> Optional[Dict]:
        """
        最新のクロール履歴を取得する
        
        Returns:
            Optional[Dict]: 最新のクロール履歴、存在しない場合はNone
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM crawl_history ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_pages(self) -> List[Dict]:
        """
        すべてのキャッシュされたページ情報を取得する
        
        Returns:
            List[Dict]: キャッシュされたすべてのページ情報
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM pages')
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def is_content_changed(self, url: str, markdown_content: str) -> bool:
        """
        ページのコンテンツが前回のクロール時から変更されているかどうかを確認する
        
        Args:
            url (str): チェックするページのURL
            markdown_content (str): 現在のMarkdownコンテンツ
        
        Returns:
            bool: コンテンツが変更されている場合はTrue、変更がない場合はFalse
        """
        current_hash = self._compute_hash(markdown_content)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT content_hash FROM pages WHERE url = ?', (url,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return True  # 新規ページなので変更ありとみなす
        
        return current_hash != row[0]
    
    def _compute_hash(self, content: str) -> str:
        """
        コンテンツのハッシュ値を計算する
        
        Args:
            content (str): ハッシュ値を計算するコンテンツ
        
        Returns:
            str: コンテンツのSHA256ハッシュ値
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_diff(self, url: str, current_content: str) -> str:
        """
        前回のコンテンツとの差分を取得する
        
        Args:
            url (str): チェックするページのURL
            current_content (str): 現在のMarkdownコンテンツ
        
        Returns:
            str: 差分情報（unified diff形式）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT markdown_content FROM pages WHERE url = ?', (url,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return "新規ページ"
            
        old_content = row[0]
        if not old_content:
            return "前回のコンテンツが空"
            
        # 差分を計算
        diff = difflib.unified_diff(
            old_content.splitlines(),
            current_content.splitlines(),
            fromfile="前回のバージョン",
            tofile="現在のバージョン",
            lineterm=''
        )
        
        return '\n'.join(diff)


class ContentRepository:
    """クロールしたコンテンツを管理するコンポーネント"""
    
    def __init__(self):
        """
        ContentRepositoryクラスの初期化
        """
        self.contents = {}  # URLをキーとしたコンテンツ辞書
        
    def add(self, page_data: Dict) -> None:
        """
        コンテンツを追加する
        
        Args:
            page_data (Dict): 追加するページデータ
        """
        url = page_data['url']
        self.contents[url] = page_data
        
    def get(self, url: str) -> Optional[Dict]:
        """
        URLに対応するコンテンツを取得する
        
        Args:
            url (str): 取得するコンテンツのURL
        
        Returns:
            Optional[Dict]: 取得したコンテンツ、存在しない場合はNone
        """
        return self.contents.get(url)
    
    def get_all(self) -> Dict[str, Dict]:
        """
        すべてのコンテンツを取得する
        
        Returns:
            Dict[str, Dict]: すべてのコンテンツ（URLをキーとする辞書）
        """
        return self.contents
    
    def count(self) -> int:
        """
        コンテンツの数を取得する
        
        Returns:
            int: コンテンツの数
        """
        return len(self.contents)


class FileExporter:
    """クロールしたコンテンツをファイルに出力するコンポーネント"""
    
    def __init__(self, output_dir: str = "output"):
        """
        FileExporterクラスの初期化
        
        Args:
            output_dir (str): 出力ディレクトリ
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_markdown(self, repository: ContentRepository, filename: str) -> str:
        """
        コンテンツをMarkdownファイルとしてエクスポートする
        
        Args:
            repository (ContentRepository): コンテンツリポジトリ
            filename (str): 出力ファイル名
        
        Returns:
            str: 出力したファイルのパス
        """
        contents = repository.get_all()
        
        # 出力ファイルのパス
        output_path = os.path.join(self.output_dir, filename)
        
        # コンテンツをリストにまとめる
        markdown_contents = []
        for url, page_data in sorted(contents.items()):
            if 'markdown_content' in page_data:
                markdown_contents.append(page_data['markdown_content'])
            
        # ファイルに書き込む
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n---\n\n'.join(markdown_contents))
            
        return output_path
    
    def export_diff_report(self, diff_data: Dict, filename: str) -> str:
        """
        差分レポートをMarkdownファイルとして出力する
        
        Args:
            diff_data (Dict): 差分データ
            filename (str): 出力ファイル名
        
        Returns:
            str: 出力したファイルのパス
        """
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 差分レポート - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 概要情報
            f.write("## 概要\n\n")
            f.write(f"- 合計ページ数: {diff_data['total']}\n")
            f.write(f"- 新規ページ: {len(diff_data['new_pages'])}\n")
            f.write(f"- 更新ページ: {len(diff_data['updated_pages'])}\n")
            f.write(f"- 削除ページ: {len(diff_data['deleted_pages'])}\n\n")
            
            # 新規ページ
            if diff_data['new_pages']:
                f.write("## 新規ページ\n\n")
                for url in diff_data['new_pages']:
                    f.write(f"- [{url}]({url})\n")
                f.write("\n")
            
            # 更新ページ
            if diff_data['updated_pages']:
                f.write("## 更新ページ\n\n")
                for url in diff_data['updated_pages']:
                    f.write(f"- [{url}]({url})\n")
                f.write("\n")
            
            # 削除ページ
            if diff_data['deleted_pages']:
                f.write("## 削除ページ\n\n")
                for url in diff_data['deleted_pages']:
                    f.write(f"- {url}\n")
                f.write("\n")
            
            # 詳細な差分情報 (オプション)
            if diff_data.get('diffs'):
                f.write("## 詳細な差分\n\n")
                for url, diff in diff_data['diffs'].items():
                    f.write(f"### {url}\n\n")
                    f.write("```diff\n")
                    f.write(diff)
                    f.write("\n```\n\n")
        
        return output_path


class PdfConverter:
    """MarkdownファイルをPDF形式に変換するコンポーネント"""
    
    def __init__(self, output_dir: str = "output"):
        """
        PdfConverterクラスの初期化
        
        Args:
            output_dir (str): 出力ディレクトリ
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def convert(self, markdown_path: str) -> str:
        """
        MarkdownファイルをPDFに変換する
        
        Args:
            markdown_path (str): Markdownファイルのパス
        
        Returns:
            str: 出力したPDFファイルのパス
        """
        # 入力ファイル名からPDFファイル名を生成
        pdf_filename = os.path.basename(markdown_path).replace('.md', '.pdf')
        pdf_path = os.path.join(self.output_dir, pdf_filename)
        
        try:
            # Markdownを読み込む
            with open(markdown_path, 'r', encoding='utf-8') as md_file:
                md_content = md_file.read()
            
            # MarkdownをHTML形式に変換
            html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # HTMLをPDFに変換
            html_path = os.path.join(self.output_dir, "temp.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"<html><head><meta charset='utf-8'></head><body>{html_content}</body></html>")
            
            # Google Colab用の設定（パスを指定）
            config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
            
            # wkhtmltopdfを使用してPDFに変換
            pdfkit.from_file(html_path, pdf_path, configuration=config)
            
            # 一時ファイルを削除
            if os.path.exists(html_path):
                os.remove(html_path)
                
            return pdf_path
            
        except Exception as e:
            logging.error(f"Error converting to PDF: {e}")
            return None


class DiscordNotifier:
    """Discordに通知を送信するコンポーネント"""
    
    def __init__(self, webhook_url: str):
        """
        DiscordNotifierクラスの初期化
        
        Args:
            webhook_url (str): Discord Webhook URL
        """
        self.webhook_url = webhook_url
        
    def notify(self, message: str, markdown_path: Optional[str] = None, pdf_path: Optional[str] = None) -> bool:
        """
        Discord通知を送信する
        
        Args:
            message (str): 通知メッセージ
            markdown_path (Optional[str]): 添付するMarkdownファイルのパス
            pdf_path (Optional[str]): 添付するPDFファイルのパス
        
        Returns:
            bool: 通知が成功した場合はTrue、失敗した場合はFalse
        """
        try:
            # Webhookインスタンスを作成
            webhook = DiscordWebhook(url=self.webhook_url, content=message)
            
            # Markdownファイルを添付
            if markdown_path and os.path.exists(markdown_path):
                with open(markdown_path, 'rb') as f:
                    webhook.add_file(file=f.read(), filename=os.path.basename(markdown_path))
            
            # PDFファイルを添付
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    webhook.add_file(file=f.read(), filename=os.path.basename(pdf_path))
            
            # 通知を送信
            response = webhook.execute()
            
            # レスポンスコードをチェック
            if response and 200 <= response.status_code < 300:
                logging.info("Discord notification sent successfully")
                return True
            else:
                logging.error(f"Failed to send Discord notification: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending Discord notification: {e}")
            return False


class RobotsTxtParser:
    """robots.txtを解析してクロール許可を確認するコンポーネント"""
    
    def __init__(self, base_url: str, user_agent: str = "*"):
        """
        RobotsTxtParserクラスの初期化
        
        Args:
            base_url (str): ベースURL
            user_agent (str): User-Agent文字列
        """
        self.base_url = base_url
        self.user_agent = user_agent
        self.disallowed_paths = []
        self.crawl_delay = 0
        
        parsed_url = urlparse(base_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                self._parse_robots_txt(response.text)
            else:
                logging.warning(f"Could not fetch robots.txt: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Error fetching robots.txt: {e}")
    
    def _parse_robots_txt(self, robots_txt: str) -> None:
        """
        robots.txtの内容を解析する
        
        Args:
            robots_txt (str): robots.txtの内容
        """
        current_agent = None
        
        for line in robots_txt.split('\n'):
            line = line.strip().lower()
            
            if not line or line.startswith('#'):
                continue
                
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
                
            directive, value = parts
            directive = directive.strip()
            value = value.strip()
            
            if directive == 'user-agent':
                current_agent = value
            elif current_agent in (self.user_agent, '*') and directive == 'disallow' and value:
                self.disallowed_paths.append(value)
            elif current_agent in (self.user_agent, '*') and directive == 'crawl-delay':
                try:
                    self.crawl_delay = float(value)
                except ValueError:
                    pass
    
    def is_allowed(self, url: str) -> bool:
        """
        URLがrobots.txtによりクロールを許可されているかを確認する
        
        Args:
            url (str): 確認するURL
        
        Returns:
            bool: クロールが許可されている場合はTrue、禁止されている場合はFalse
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        for disallowed in self.disallowed_paths:
            if path.startswith(disallowed):
                return False
                
        return True


class WebCrawler:
    """Webクローラーのメインコントローラー"""
    
    def __init__(self, base_url: str, max_pages: int = 100, delay: float = 1.0, diff_detection: bool = True, cache_dir: str = "cache"):
        """
        WebCrawlerクラスの初期化
        
        Args:
            base_url (str): クロールを開始するURL
            max_pages (int): クロールする最大ページ数
            delay (float): リクエスト間の遅延秒数
            diff_detection (bool): 差分検知を有効にするかどうか
            cache_dir (str): キャッシュディレクトリ
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.diff_detection = diff_detection
        
        # ドメイン名を取得
        self.domain = urlparse(base_url).netloc
        
        # 各コンポーネントの初期化
        self.url_filter = UrlFilter(base_url)
        self.robots_parser = RobotsTxtParser(base_url)
        self.fetcher = Fetcher(delay=max(delay, self.robots_parser.crawl_delay))
        self.parser = Parser(self.url_filter)
        self.markdown_converter = MarkdownConverter()
        self.repository = ContentRepository()
        
        if self.diff_detection:
            self.cache = CrawlCache(self.domain, cache_dir)
        
        # クロール状態の追跡
        self.visited_urls = set()
        self.queue = deque([base_url])
        
        # 差分情報の追跡
        self.new_pages = []
        self.updated_pages = []
        self.deleted_pages = []
        self.page_diffs = {}
        
    def crawl(self) -> Tuple[ContentRepository, Dict]:
        """
        Webサイトをクロールする
        
        Returns:
            Tuple[ContentRepository, Dict]: (クロールしたコンテンツのリポジトリ, 差分情報)
        """
        count = 0
        
        while self.queue and count < self.max_pages:
            # キューからURLを取得
            url = self.queue.popleft()
            
            # 既に訪問済みのURLはスキップ
            if url in self.visited_urls:
                continue
            
            # robots.txtで禁止されているURLはスキップ
            if not self.robots_parser.is_allowed(url):
                logging.info(f"Skipping URL disallowed by robots.txt: {url}")
                self.visited_urls.add(url)
                continue
            
            logging.info(f"Crawling {url} ({count + 1}/{self.max_pages})")
            
            # キャッシュからページ情報を取得
            cached_page = None
            if self.diff_detection:
                cached_page = self.cache.get_page(url)
            
            # ページのHTMLを取得（条件付きリクエスト）
            etag = cached_page.get('etag') if cached_page else None
            last_modified = cached_page.get('last_modified') if cached_page else None
            
            html, headers_info = self.fetcher.fetch(url, etag, last_modified)
            
            # 304 Not Modified の場合、キャッシュから前回のコンテンツを使用
            if headers_info.get('status_code') == 304 and cached_page:
                logging.info(f"Using cached content for {url}")
                page_data = {
                    'url': url,
                    'title': cached_page['title'],
                    'html_content': '', # HTMLは保存不要
                    'markdown_content': cached_page['markdown_content'],
                    'etag': cached_page['etag'],
                    'last_modified': cached_page['last_modified'],
                }
                self.repository.add(page_data)
                self.visited_urls.add(url)
                count += 1
                continue
            
            # HTMLが取得できなかった場合はスキップ
            if html is None:
                self.visited_urls.add(url)
                continue
            
            # HTMLを解析してコンテンツとリンクを抽出
            page_data, links = self.parser.parse(html, url)
            
            # コンテンツがない場合はスキップ
            if not page_data.get('html_content'):
                self.visited_urls.add(url)
                continue
            
            # ヘッダー情報を追加
            page_data['etag'] = headers_info.get('etag')
            page_data['last_modified'] = headers_info.get('last_modified')
            
            # HTMLをMarkdownに変換
            page_data = self.markdown_converter.convert(page_data)
            
            # 差分検知（有効な場合）
            if self.diff_detection:
                markdown_content = page_data.get('markdown_content', '')
                
                # キャッシュに追加または更新
                is_update = self.cache.add_or_update_page(page_data)
                
                if is_update:
                    # コンテンツが変更されている場合のみ更新ページとしてマーク
                    if self.cache.is_content_changed(url, markdown_content):
                        self.updated_pages.append(url)
                        self.page_diffs[url] = self.cache.get_diff(url, markdown_content)
                else:
                    # 新規ページ
                    self.new_pages.append(url)
            
            # コンテンツを保存
            self.repository.add(page_data)
            
            # 訪問済みとしてマーク
            self.visited_urls.add(url)
            count += 1
            
            # 新しいリンクをキューに追加
            for link in links:
                if link not in self.visited_urls and link not in self.queue:
                    self.queue.append(link)
        
        # 削除されたページを特定（差分検知が有効な場合）
        if self.diff_detection:
            cached_urls = self.cache.get_all_urls()
            current_urls = set(self.repository.get_all().keys())
            self.deleted_pages = list(cached_urls - current_urls)
            
            # 削除されたページをキャッシュから削除
            if self.deleted_pages:
                self.cache.delete_urls(self.deleted_pages)
            
            # クロール履歴を保存
            self.cache.save_crawl_history(
                page_count=self.repository.count(),
                new_count=len(self.new_pages),
                updated_count=len(self.updated_pages),
                deleted_count=len(self.deleted_pages)
            )
        
        # 差分情報を作成
        diff_data = {
            'total': self.repository.count(),
            'new_pages': self.new_pages,
            'updated_pages': self.updated_pages,
            'deleted_pages': self.deleted_pages,
            'diffs': self.page_diffs,
            'has_changes': bool(self.new_pages or self.updated_pages or self.deleted_pages)
        }
        
        logging.info(f"Crawling completed. Visited {len(self.visited_urls)} URLs, stored {self.repository.count()} pages.")
        logging.info(f"Changes detected: {len(self.new_pages)} new, {len(self.updated_pages)} updated, {len(self.deleted_pages)} deleted.")
        
        return self.repository, diff_data


# Google Colab用のメイン関数
def run_crawler(url, max_pages=100, delay=1.0, output_dir="output", cache_dir="cache", discord_webhook=None, no_diff=False, skip_no_changes=False):
    """Google Colab向けのクローラー実行関数"""
    # ロガーの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(output_dir, "crawler.log")),
            logging.StreamHandler()
        ]
    )
    
    try:
        # 出力ディレクトリを作成
        os.makedirs(output_dir, exist_ok=True)
        
        # クローラーの初期化と実行
        crawler = WebCrawler(url, max_pages, delay, diff_detection=not no_diff, cache_dir=cache_dir)
        repository, diff_data = crawler.crawl()
        
        # 結果がない場合はエラー
        if repository.count() == 0:
            logging.error("No content was crawled.")
            if discord_webhook:
                notifier = DiscordNotifier(discord_webhook)
                notifier.notify(message=f"Webサイトのクロールが完了しましたが、コンテンツは取得できませんでした。\n**URL**: {url}")
            return None, None, None
        
        # 変更がなく、スキップオプションが有効な場合はスキップ
        if skip_no_changes and not diff_data['has_changes']:
            logging.info("No changes detected. Skipping file generation and notification.")
            if discord_webhook:
                notifier = DiscordNotifier(discord_webhook)
                notifier.notify(message=f"Webサイトのクロールが完了しましたが、前回から変更はありませんでした。\n**URL**: {url}\n**取得ページ数**: {repository.count()}")
            return None, None, None
        
        # ドメイン名をファイル名として使用
        domain = urlparse(url).netloc
        markdown_filename = f"{domain}.md"
        
        # Markdownファイルとして出力
        exporter = FileExporter(output_dir)
        markdown_path = exporter.export_markdown(repository, markdown_filename)
        logging.info(f"Exported Markdown to {markdown_path}")
        
        # 差分レポートを出力（差分検知が有効な場合）
        diff_report_path = None
        if not no_diff and diff_data['has_changes']:
            diff_report_filename = f"{domain}_diff_report.md"
            diff_report_path = exporter.export_diff_report(diff_data, diff_report_filename)
            logging.info(f"Exported diff report to {diff_report_path}")
        
        # PDFファイルとして出力
        pdf_converter = PdfConverter(output_dir)
        pdf_path = pdf_converter.convert(markdown_path)
        if pdf_path:
            logging.info(f"Exported PDF to {pdf_path}")
        
        # 差分レポートのPDFを生成（差分がある場合）
        diff_report_pdf_path = None
        if diff_report_path:
            diff_report_pdf_path = pdf_converter.convert(diff_report_path)
            if diff_report_pdf_path:
                logging.info(f"Exported diff report PDF to {diff_report_pdf_path}")
        
        # Discord通知
        if discord_webhook:
            notifier = DiscordNotifier(discord_webhook)
            
            # 差分検知が有効かつ変更がある場合
            if not no_diff and diff_data['has_changes']:
                message = f"Webサイトのクロールが完了しました。**変更が検出されました**。\n"
                message += f"**URL**: {url}\n"
                message += f"**取得ページ数**: {diff_data['total']}\n"
                message += f"**新規ページ**: {len(diff_data['new_pages'])}\n"
                message += f"**更新ページ**: {len(diff_data['updated_pages'])}\n"
                message += f"**削除ページ**: {len(diff_data['deleted_pages'])}"
                
                # 差分レポートを添付
                success = notifier.notify(
                    message=message,
                    markdown_path=diff_report_path,
                    pdf_path=diff_report_pdf_path or pdf_path
                )
            else:
                # 変更がない場合または差分検知が無効の場合
                message = f"Webサイトのクロールが完了しました。\n**URL**: {url}\n**取得ページ数**: {repository.count()}"
                success = notifier.notify(
                    message=message,
                    markdown_path=markdown_path,
                    pdf_path=pdf_path
                )
                
            if success:
                logging.info("Discord notification sent successfully")
            else:
                logging.error("Failed to send Discord notification")
        
        logging.info("Process completed successfully")
        
        return markdown_path, pdf_path, diff_report_path
        
    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
        if discord_webhook:
            notifier = DiscordNotifier(discord_webhook)
            notifier.notify(message=f"Webサイトのクロール中にエラーが発生しました。\n**URL**: {url}\n**エラー**: {str(e)}")
        return None, None, None


# Colabで実行する場合は、以下のコードを実行してください
# ---------------------------------------------------------
# Google Driveのマウント
# from google.colab import drive
# drive.mount('/content/drive')

# # クローラー用のディレクトリを作成
# import os
# crawler_dir = '/content/drive/MyDrive/website_crawler'
# output_dir = os.path.join(crawler_dir, 'output')
# cache_dir = os.path.join(crawler_dir, 'cache')

# os.makedirs(crawler_dir, exist_ok=True)
# os.makedirs(output_dir, exist_ok=True)
# os.makedirs(cache_dir, exist_ok=True)

# # クローラーの実行
# markdown_path, pdf_path, diff_path = run_crawler(
#     url="https://example.com",
#     max_pages=100,
#     delay=1.0,
#     output_dir=output_dir,
#     cache_dir=cache_dir,
#     discord_webhook=None,
#     no_diff=False,
#     skip_no_changes=True
# )

# ローカル環境で実行する場合は、以下のコードを実行してください
# ---------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Web Crawler to export site content as Markdown with diff detection')
    parser.add_argument('url', help='URL to start crawling from')
    parser.add_argument('--max-pages', type=int, default=100, help='Maximum number of pages to crawl')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')
    parser.add_argument('--output-dir', default='output', help='Output directory for files')
    parser.add_argument('--cache-dir', default='cache', help='Cache directory')
    parser.add_argument('--discord-webhook', help='Discord webhook URL for notifications')
    parser.add_argument('--no-diff', action='store_true', help='Disable diff detection')
    parser.add_argument('--skip-no-changes', action='store_true', help='Skip processing if no changes detected')
    
    args = parser.parse_args()
    
    # Colabかローカル環境か自動判定して実行
    try:
        import google.colab
        in_colab = True
    except:
        in_colab = False
    
    if in_colab:
        print("Google Colab環境を検出しました。run_crawler関数を使用してください。")
    else:
        # ローカル環境での実行
        markdown_path, pdf_path, diff_path = run_crawler(
            url=args.url,
            max_pages=args.max_pages,
            delay=args.delay,
            output_dir=args.output_dir,
            cache_dir=args.cache_dir,
            discord_webhook=args.discord_webhook,
            no_diff=args.no_diff,
            skip_no_changes=args.skip_no_changes
        )
        
        if markdown_path:
            print(f"\n処理が完了しました！")
            print(f"\nMarkdownファイル: {markdown_path}")
            if pdf_path:
                print(f"PDFファイル: {pdf_path}")
            if diff_path:
                print(f"差分レポート: {diff_path}")
        else:
            print("\nエラーが発生したかクロールをスキップしました。ログを確認してください。")