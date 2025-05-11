"""
再利用可能なWebクローラーコンポーネント
- 非同期サポート追加
- エラーハンドリング強化
- パフォーマンス最適化
"""

import os
import re
import time
import json
import hashlib
import logging
import sqlite3
import asyncio
import requests
import html2text
import markdown
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from typing import Set, Dict, List, Optional, Tuple, Any, Union, Callable
from datetime import datetime
import difflib
import lxml.html
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from contextlib import contextmanager


# 設定クラス
@dataclass
class CrawlerConfig:
    """クローラーの設定を管理するクラス"""
    base_url: str
    max_pages: int = 100
    delay: float = 1.0
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    timeout: int = 10
    max_retries: int = 3
    max_workers: int = 5  # 並列実行用のワーカー数
    output_dir: str = "output"
    cache_dir: str = "cache"
    discord_webhook: Optional[str] = None
    diff_detection: bool = True
    skip_no_changes: bool = True
    normalize_urls: bool = True  # URL正規化の有効化
    respect_robots_txt: bool = True  # robots.txtの尊重
    follow_redirects: bool = True  # リダイレクトの追跡
    static_extensions: Set[str] = field(default_factory=lambda: {
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.css',
        '.js', '.pdf', '.zip', '.tar', '.gz', '.mp3',
        '.mp4', '.avi', '.mov', '.webm', '.webp', '.ico'
    })
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'CrawlerConfig':
        """辞書から設定オブジェクトを作成する"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書に変換する"""
        return {k: v for k, v in self.__dict__.items()}
    
    @classmethod
    def from_json(cls, json_path: str) -> 'CrawlerConfig':
        """JSONファイルから設定オブジェクトを作成する"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"設定ファイルの読み込みに失敗しました: {e}")
            raise


class UrlFilter:
    """URLをフィルタリングして、同一ドメイン内のURLのみを許可するコンポーネント（改善版）"""
    
    def __init__(self, config: CrawlerConfig):
        """
        URLフィルタークラスの初期化
        
        Args:
            config: クローラーの設定
        """
        self.base_url = config.base_url
        self.base_domain = urlparse(config.base_url).netloc
        self.static_extensions = config.static_extensions
        self.normalize_urls = config.normalize_urls
        
        # 除外パターンの正規表現（オプション）
        self.exclude_patterns = [
            r'\/(?:calendar|login|logout|signup|register|password-reset)(?:\/|$)',
            r'\/feed(?:\/|$)',
            r'\/wp-admin(?:\/|$)',
            r'\/wp-content\/(?:cache|uploads)(?:\/|$)',
            r'\/cart(?:\/|$)',
            r'\/checkout(?:\/|$)',
            r'\/my-account(?:\/|$)',
        ]
        self.exclude_regex = re.compile('|'.join(self.exclude_patterns))
    
    def normalize_url(self, url: str) -> str:
        """URLを正規化する（相対URLを絶対URLに変換、フラグメントの削除等）"""
        # 相対URLを絶対URLに変換
        normalized_url = urljoin(self.base_url, url)
        
        # フラグメント (#) を削除
        normalized_url = normalized_url.split('#')[0]
        
        if self.normalize_urls:
            # クエリパラメータを正規化（オプション）
            parsed = urlparse(normalized_url)
            if parsed.query:
                # クエリパラメータを正規化：アルファベット順にソート
                params = parse_qs(parsed.query)
                # UTM系パラメータなど、特定のトラッキングパラメータを除外
                for param in list(params.keys()):
                    if param.startswith('utm_') or param in ['fbclid', 'gclid', 'ref']:
                        del params[param]
                # クエリを再構築
                normalized_query = urlencode(params, doseq=True)
                # URLを再構築
                normalized_url = parsed._replace(query=normalized_query).geturl()
            
        # トレーリングスラッシュを統一
        if normalized_url.endswith('/'):
            normalized_url = normalized_url[:-1]
            
        return normalized_url
    
    def should_crawl(self, url: str) -> bool:
        """URLがクロール対象かどうかを判定する"""
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
        
        # 除外パターンに該当するURLはクロールしない
        if self.exclude_regex.search(parsed_url.path):
            return False
            
        return True


class Fetcher:
    """指定されたURLからHTMLコンテンツを取得するコンポーネント（改善版）"""
    
    def __init__(self, config: CrawlerConfig):
        self.delay = config.delay
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        self.follow_redirects = config.follow_redirects
        self.last_request_time = 0
        
        # ユーザーエージェントをより多様化
        self.headers = {
            'User-Agent': config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',  # 圧縮対応
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # ドメインごとのリクエスト制限を追跡するための辞書
        self.domain_last_request = {}
        
        # セッションオブジェクトの作成（接続の再利用によるパフォーマンス向上）
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def __del__(self):
        """クリーンアップ処理"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except Exception:
            pass
        
    def _wait_for_rate_limit(self, domain: str):
        """ドメインごとのレート制限を適用する"""
        current_time = time.time()
        
        # ドメイン固有の最終リクエスト時間を取得
        domain_last_time = self.domain_last_request.get(domain, 0)
        
        # グローバルな最終リクエスト時間との間で長い方を取得
        last_time = max(self.last_request_time, domain_last_time)
        
        elapsed = current_time - last_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
            
        # 最終リクエスト時間を更新
        current_time = time.time()
        self.last_request_time = current_time
        self.domain_last_request[domain] = current_time
        
    async def fetch_async(self, url: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Tuple[Optional[str], Dict[str, str]]:
        """URLからHTMLコンテンツを非同期で取得する"""
        # 非同期実行のためのラッパー
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.fetch(url, etag, last_modified))
        
    def fetch(self, url: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Tuple[Optional[str], Dict[str, str]]:
        """URLからHTMLコンテンツを取得する"""
        # ドメインを抽出してレート制限を適用
        domain = urlparse(url).netloc
        self._wait_for_rate_limit(domain)
        
        # 条件付きリクエスト用ヘッダーを準備
        headers = {}
        if etag:
            headers['If-None-Match'] = etag
        if last_modified:
            headers['If-Modified-Since'] = last_modified
            
        retries = 0
        retry_delay = self.delay
        
        while retries <= self.max_retries:
            try:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    allow_redirects=self.follow_redirects
                )
                
                # ステータスコードに基づく処理
                if response.status_code == 304:  # Not Modified
                    logging.info(f"Content not modified: {url}")
                    return None, {
                        'etag': etag,
                        'last_modified': last_modified,
                        'status_code': 304
                    }
                
                elif response.status_code == 429:  # Too Many Requests
                    # レート制限に引っかかった場合、遅延を増加させる
                    retry_after = int(response.headers.get('Retry-After', retry_delay * 2))
                    logging.warning(f"Rate limited: {url}. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                    
                elif response.status_code >= 400:  # エラーコード
                    if response.status_code == 404:
                        logging.warning(f"Page not found: {url}")
                        return None, {'status_code': 404, 'error': 'Not Found'}
                        
                    logging.warning(f"Failed to fetch {url}: status code {response.status_code}")
                    if retries < self.max_retries:
                        retries += 1
                        time.sleep(retry_delay * (2 ** retries))  # 指数バックオフ
                        continue
                    return None, {'status_code': response.status_code, 'error': f'HTTP error: {response.status_code}'}
                
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
                    'status_code': response.status_code,
                    'encoding': response.encoding
                }
                
                # テキストエンコーディングの処理を改善
                if response.encoding is None:
                    # エンコーディングの自動検出
                    response.encoding = response.apparent_encoding
                
                try:
                    return response.text, headers_info
                except UnicodeDecodeError as e:
                    logging.error(f"Unicode decode error for {url}: {e}")
                    # フォールバックとしてバイナリからUTF-8でデコード
                    return response.content.decode('utf-8', errors='replace'), headers_info
                
            except requests.exceptions.Timeout as e:
                logging.warning(f"Timeout for {url}: {e}")
                retries += 1
                if retries <= self.max_retries:
                    time.sleep(retry_delay * (2 ** retries))
                else:
                    return None, {'status_code': 0, 'error': f'Timeout: {str(e)}'}
                
            except requests.exceptions.TooManyRedirects as e:
                logging.error(f"Too many redirects for {url}: {e}")
                return None, {'status_code': 0, 'error': f'Too many redirects: {str(e)}'}
                
            except requests.RequestException as e:
                logging.error(f"Error fetching {url}: {e}")
                retries += 1
                if retries <= self.max_retries:
                    time.sleep(retry_delay * (2 ** retries))
                else:
                    return None, {'status_code': 0, 'error': str(e)}
        
        return None, {'status_code': 0, 'error': 'Max retries exceeded'}


class Parser:
    """HTMLコンテンツを解析し、コンテンツとリンクを抽出するコンポーネント（改善版）"""
    
    def __init__(self, url_filter: UrlFilter):
        self.url_filter = url_filter
        
        # メインコンテンツを特定するためのセレクタ（優先順）
        self.content_selectors = [
            '//main', '//article', 
            '//div[@id="content"]', '//div[@class="content"]',
            '//div[@id="main"]', '//div[@class="main"]',
            '//div[contains(@class, "post-content")]', '//div[contains(@class, "entry-content")]',
            '//div[@role="main"]'
        ]
        
        # 不要な要素を除外するセレクタ
        self.exclude_selectors = [
            '//header', '//footer', '//nav', 
            '//aside', '//div[contains(@class, "sidebar")]',
            '//div[contains(@class, "advertisement")]', '//div[contains(@class, "ad-")]',
            '//script', '//style', '//iframe', '//noscript',
            '//div[contains(@class, "comment")]'
        ]
    
    def parse(self, html: str, url: str) -> Tuple[Dict, List[str]]:
        """HTMLからコンテンツとリンクを抽出する"""
        try:
            # lxmlを使用してHTMLを解析
            doc = lxml.html.fromstring(html)
            doc.make_links_absolute(url)  # 相対リンクを絶対URLに変換
            
            # タイトルを抽出
            title_elem = doc.xpath('//title')
            title = title_elem[0].text_content().strip() if title_elem else "No Title"
            
            # ページのメタ情報を抽出
            meta_description = ""
            meta_elems = doc.xpath('//meta[@name="description"]')
            if meta_elems:
                meta_description = meta_elems[0].get('content', '')
            
            # メインコンテンツを抽出
            content_elem = None
            for selector in self.content_selectors:
                elements = doc.xpath(selector)
                if elements:
                    content_elem = elements[0]
                    break
            
            # メインコンテンツが見つからない場合はbody全体を使用
            if not content_elem:
                body_elem = doc.xpath('//body')
                content_elem = body_elem[0] if body_elem else doc
            
            # 不要な要素を除外（コピーを作成して処理）
            content_elem_copy = copy_element(content_elem)
            for selector in self.exclude_selectors:
                for element in content_elem_copy.xpath(selector):
                    parent = element.getparent()
                    if parent is not None:  # 親がある場合のみ削除
                        parent.remove(element)
            
            # HTMLコンテンツを取得
            html_content = lxml.html.tostring(content_elem_copy, encoding='unicode')
            
            # リンクを抽出
            links = []
            for a_tag in doc.xpath('//a[@href]'):
                href = a_tag.get('href')
                if self.url_filter.should_crawl(href):
                    normalized_url = self.url_filter.normalize_url(href)
                    links.append(normalized_url)
            
            # ページ情報の辞書を作成（拡張版）
            page_data = {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'html_content': html_content,
                'fetch_time': datetime.now().isoformat(),
            }
            
            return page_data, links
            
        except Exception as e:
            logging.error(f"Error parsing HTML from {url}: {e}")
            # エラー時は空のデータと空のリンクリストを返す
            return {'url': url, 'title': 'Error', 'html_content': ''}, []


def copy_element(element):
    """lxml要素のディープコピーを作成する（直接deepcopyが使えないため）"""
    return lxml.html.fromstring(lxml.html.tostring(element, encoding='unicode'))


class MarkdownConverter:
    """HTMLコンテンツをMarkdown形式に変換するコンポーネント（改善版）"""

    def __init__(self, config: Optional[Dict] = None):
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = False
        self.converter.ignore_tables = False
        self.converter.body_width = 0  # 行の折り返しを無効化
        self.converter.unicode_snob = True  # Unicode文字を維持
        self.converter.single_line_break = True  # 単一の改行を維持
        self.converter.wrap_links = False  # リンクを折り返さない
        self.converter.emphasis_mark = '*'  # 強調のマークとして*を使用
        self.converter.skip_internal_links = True  # アンカーリンクをスキップ

        # オプション設定を適用
        if config:
            for key, value in config.items():
                if hasattr(self.converter, key):
                    setattr(self.converter, key, value)

    def convert(self, page_data: Dict) -> Dict:
        """HTMLをMarkdownに変換する"""
        title = page_data['title']
        html_content = page_data['html_content']
        url = page_data['url']
        meta_description = page_data.get('meta_description', '')

        # HTMLの前処理（不要な要素や属性の削除）
        html_content = self._preprocess_html(html_content)

        # HTMLをMarkdownに変換
        try:
            markdown_content = self.converter.handle(html_content)

            # 画像パスを修正（相対パスがある場合）
            markdown_content = self._fix_image_paths(markdown_content, url)

            # 変換後の後処理
            markdown_content = self._postprocess_markdown(markdown_content)

        except Exception as e:
            logging.error(f"Markdown conversion error for {url}: {e}")
            markdown_content = f"Error converting content: {str(e)}"

        # Markdownタイトルを作成
        markdown_title = f"# {title}\n\n"

        # メタ説明を追加（あれば）
        meta_section = f"*{meta_description}*\n\n" if meta_description else ""

        # URL情報を追加
        url_info = f"*Source: {url}*\n\n"

        # 最終的なMarkdownコンテンツを組み立て
        full_markdown = markdown_title + meta_section + url_info + markdown_content

        # 結果を返す
        result = page_data.copy()
        result['markdown_content'] = full_markdown

        return result

    def _preprocess_html(self, html_content: str) -> str:
        """HTMLの前処理を行う"""
        try:
            # lxmlを使用してHTMLを解析
            doc = lxml.html.fromstring(html_content)

            # 「Direct link to」などの不要なテキストを含むa要素を修正
            for a_elem in doc.xpath('//a[contains(text(), "Direct link to")]'):
                # テキストを空にする
                a_elem.text = ""

            # â などの特殊文字を含む要素を修正
            for elem in doc.xpath('//*[contains(text(), "â")]'):
                # テキストを置換
                if elem.text:
                    elem.text = elem.text.replace('â', '')

            # ドキュメント全体から ðï¸ などの絵文字や特殊文字を削除（より徹底的なアプローチ）
            for elem in doc.xpath('//*'):
                # テキストノードをチェック
                if elem.text:
                    # 特殊文字を削除
                    elem.text = elem.text.replace('ðï', '').replace('ðï¸', '')

                # テイルテキスト（要素と次の要素の間のテキスト）もチェック
                if elem.tail:
                    elem.tail = elem.tail.replace('ðï', '').replace('ðï¸', '')

            # カテゴリページのフォーマットを修正（h2内の絵文字などを削除）
            for h2 in doc.xpath('//h2'):
                # スペースの後の数字（items）などが含まれている場合は削除
                if h2.text and re.search(r'\d+\s*items', h2.text):
                    h2.text = re.sub(r'\d+\s*items', '', h2.text)

            # リンクテキスト内の特殊文字を削除（アンカーなどを含む）
            for a in doc.xpath('//a'):
                if a.text and ('ðï' in a.text or 'ðï¸' in a.text):
                    a.text = a.text.replace('ðï', '').replace('ðï¸', '')

            # 表組みの整形を改善（table要素にクラスを追加）
            for table in doc.xpath('//table'):
                # Markdownでの表組み変換を改善するためのクラスを追加
                table.attrib['class'] = 'markdown-table'

                # テーブルのセルにあるスペースを調整
                for cell in table.xpath('.//th | .//td'):
                    if cell.text:
                        cell.text = cell.text.strip()
                        # セル内の特殊文字も削除
                        cell.text = cell.text.replace('ðï', '').replace('ðï¸', '')

            # HTML文字列に戻す前に最終チェック - 絵文字コードのようなものをすべて削除
            # すべてのテキストノードを取得してから文字列に戻す
            # これによりまだ処理されていない特殊文字を徹底的に削除
            for elem in doc.xpath('//*'):
                for attr_name in elem.attrib:
                    if isinstance(elem.attrib[attr_name], str):
                        elem.attrib[attr_name] = elem.attrib[attr_name].replace('ðï', '').replace('ðï¸', '')

                if hasattr(elem, 'text') and elem.text:
                    elem.text = re.sub(r'[^\x00-\x7F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF]+', '', elem.text)

                if hasattr(elem, 'tail') and elem.tail:
                    elem.tail = re.sub(r'[^\x00-\x7F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF]+', '', elem.tail)

            # HTML文字列に戻す
            html_cleaned = lxml.html.tostring(doc, encoding='unicode')

            # バイトで処理できる文字列表現に変換して、非ASCII文字を確実に処理
            byte_html = html_cleaned.encode('ascii', 'ignore')
            html_cleaned = byte_html.decode('ascii')

            # 最終的なセーフティネット：直接文字列置換で残っている可能性のある特殊文字を削除
            html_cleaned = html_cleaned.replace('ðï', '').replace('ðï¸', '')

            return html_cleaned
        except Exception as e:
            logging.warning(f"HTML preprocessing error: {e}")
            # エラーが発生した場合は元のHTMLを返す
            return html_content

    def _postprocess_markdown(self, markdown_content: str) -> str:
        """Markdown変換後の後処理を行う"""
        # 余分な空行を削除（3つ以上連続する改行を2つに縮小）
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        # 表組みの整形を改善
        markdown_content = self._improve_tables(markdown_content)

        # 「Direct link to」などの不要なテキストを削除
        markdown_content = re.sub(r'\[â\]\([^)]+\s+"Direct link to [^"]+"\)', '', markdown_content)
        markdown_content = re.sub(r'\[\]\([^)]+\s+"Direct link to [^"]+"\)', '', markdown_content)
        markdown_content = re.sub(r'\[[^\]]*\]\([^)]+\s+"Direct link to [^"]+"\)', '', markdown_content)

        # 特殊文字を修正
        markdown_content = markdown_content.replace('â', '')
        markdown_content = markdown_content.replace('ðï¸', '')
        markdown_content = markdown_content.replace('ðï', '')

        # 連続する空白を1つに
        markdown_content = re.sub(r' {2,}', ' ', markdown_content)

        # リスト項目の後の不要な改行を修正
        markdown_content = re.sub(r'(\* .*)\n\n(?=\* )', r'\1\n', markdown_content)

        # カテゴリページの見出しフォーマットを改善
        # ヘッダーの中の"ðï¸"を削除
        markdown_content = re.sub(r'##\s*\[(ðï¸\s*)?([^\]]*?)(\s*\d+\s*items)?\]\(([^)]+)\)', r'## [\2](\4)', markdown_content)

        # マークダウンリンク内の特殊文字のみを置換
        # [ðï¸ Something] の形式で特殊文字だけを削除し [Something] に変換
        # カテゴリ情報などのテキストは保持
        markdown_content = re.sub(r'\[ðï¸\s*([^\]]*?)(\s*\d+\s*items)?\]', r'[\1]', markdown_content)

        # ##+ で始まる見出し行内の特殊文字を削除
        markdown_content = re.sub(r'(#{1,6})\s+\[(ðï¸?\s*)?([^\]]*?)\](\([^)]+\))', r'\1 [\3]\4', markdown_content)

        # 残りの特殊文字をすべてのリンクテキストから削除 (##, ###, #### のすべての見出しレベル)
        markdown_content = re.sub(r'(#{1,4})\s*\[ðï¸?\s*([^\]]*)\]\(([^)]+)\)', r'\1 [\2](\3)', markdown_content)

        # 連続するヘッダーの間に改行を追加
        markdown_content = re.sub(r'(##\s*\[.*?\]\(.*?\))\s*(##)', r'\1\n\n\2', markdown_content)

        # カテゴリページのリンクリストの間隔を調整
        markdown_content = re.sub(r'(\]\([^)]+\))\n\n(\*)', r'\1\n\2', markdown_content)

        # カテゴリページの説明文が見出しとリンクされている場合、適切に分離
        # ## [Placing Your First Order...](http://) のようなテキストを保持
        markdown_content = re.sub(r'##\s*\[(.*?)\]\((.*?)\)(.*?)##', r'## [\1](\2)\n\3\n\n##', markdown_content)

        # 見出し + リンク + 説明文のパターンを処理
        # 例: ## [Title](url)Description
        markdown_content = re.sub(r'(##\s*\[[^\]]+\]\([^)]+\))([A-Za-z])', r'\1\n\2', markdown_content)

        # リンク内のテキストを保持しつつ、その直後に続く説明文を適切に改行
        markdown_content = re.sub(r'(\]\(https?://[^)]+\))([A-Za-z])', r'\1\n\2', markdown_content)

        # 連続する ## が残っている場合は削除（最後の ## など）
        markdown_content = re.sub(r'##\s*$', '', markdown_content)

        # テーブル内の特殊文字も削除
        markdown_content = re.sub(r'\|(.*?)ðï¸(.*?)\|', r'|\1\2|', markdown_content)
        markdown_content = re.sub(r'\|(.*?)ðï(.*?)\|', r'|\1\2|', markdown_content)

        # 残っている特殊文字を直接置換（最終セーフティネット）
        markdown_content = markdown_content.replace('ðï¸', '')
        markdown_content = markdown_content.replace('ðï', '')

        # JSONやコードブロックを整形
        markdown_content = self._format_code_blocks(markdown_content)

        # 非ASCII文字を確実に処理するための最終対策
        # ASCII文字のみを許可（バイト操作でエンコード/デコード）
        markdown_bytes = markdown_content.encode('ascii', 'ignore')
        markdown_content = markdown_bytes.decode('ascii')

        # 全体を整理（余分な改行を調整）
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        # ダブルダッシュを削除（-- を空行に置換）
        markdown_content = re.sub(r'\n--\n', '\n\n', markdown_content)

        return markdown_content

    def _format_code_blocks(self, markdown_content: str) -> str:
        """コードブロックとJSONの整形を行う"""
        # コードブロックを検出するパターン（既存のコードブロック）
        code_block_pattern = r'```(?:json|javascript|python|bash|typescript|ts|js)?\s*\n(.*?)\n```'

        # コードブロックでない複数行の整形（JSON候補）
        multiline_pattern = r'(\s*\{\s*\n.*?\n\s*\}\s*\n)'

        def format_code_block(match):
            code = match.group(1)
            language = match.group(0).split('```')[1].strip() if '```' in match.group(0) and match.group(0).split('```')[1].strip() else ''

            # JSONの場合は整形を試みる
            if language.lower() == 'json' or (not language and code.strip().startswith('{')):
                try:
                    # JSONとして解析して整形
                    parsed_json = json.loads(code.strip())
                    formatted_json = json.dumps(parsed_json, indent=2)
                    return f"```json\n{formatted_json}\n```"
                except:
                    pass

            # インデントを揃え、余分な空白を削除
            lines = code.split('\n')
            if len(lines) > 1:
                # 行頭の共通インデントを検出
                common_indent = None
                for line in lines:
                    if line.strip():  # 空行は無視
                        # 行頭の空白を数える
                        indent = len(line) - len(line.lstrip())
                        if common_indent is None or indent < common_indent:
                            common_indent = indent

                # 共通インデントを削除して整形
                if common_indent and common_indent > 0:
                    formatted_lines = []
                    for line in lines:
                        if line.strip():  # 空行は無視
                            formatted_lines.append(line[common_indent:])
                        else:
                            formatted_lines.append(line)

                    # 言語指定があれば保持、なければ自動検出を試みる
                    if not language:
                        if any(keyword in code.lower() for keyword in ['function', 'const', 'var', 'let', '=>']):
                            language = 'javascript'
                        elif any(keyword in code.lower() for keyword in ['def ', 'class ', 'import ', 'from ']):
                            language = 'python'

                    lang_tag = language if language else ''
                    return f"```{lang_tag}\n" + "\n".join(formatted_lines) + "\n```"

            # PDFのフォーマットを改善するために前後に空行を入れる
            return "\n" + match.group(0) + "\n"

        # コードブロックを整形
        markdown_content = re.sub(code_block_pattern, format_code_block, markdown_content, flags=re.DOTALL)

        # インラインのJSONを検出して整形（コードブロック以外）
        inline_json_pattern = r'(\{\s*"[^"]+"\s*:(?:[^{}]|(?:\{\s*(?:[^{}]|(?:\{\s*[^{}]*\s*\}))*\s*\}))*\})'

        def format_inline_json(match):
            json_text = match.group(1)
            try:
                # 整形を試みる
                parsed_json = json.loads(json_text)
                formatted_json = json.dumps(parsed_json, indent=2)
                return f"```json\n{formatted_json}\n```"
            except:
                return json_text

        # インラインJSONの置換は慎重に（段落内のみ）
        lines = markdown_content.split('\n')
        i = 0
        while i < len(lines):
            # 1行のJSON形式を検出して整形
            if len(lines[i]) > 5 and lines[i].strip().startswith('{') and lines[i].strip().endswith('}') and '"' in lines[i]:
                try:
                    # JSONとして解析して整形
                    json_text = lines[i].strip()
                    parsed_json = json.loads(json_text)
                    formatted_json = json.dumps(parsed_json, indent=2)
                    lines[i] = f"```json\n{formatted_json}\n```"
                except:
                    # JSONとして解析できない場合は元のまま
                    pass

            # コード部分のような連続した行を検出して整形
            elif i < len(lines) - 3 and not lines[i].startswith('#') and not '](http' in lines[i] and (' { ' in lines[i] or lines[i].strip().endswith('{')):
                start_idx = i
                # JSONブロックの終わりを探す
                block_content = []
                is_code_block = True
                j = i

                while j < min(i + 30, len(lines)):  # 最大30行まで探索
                    if '}' in lines[j] and j > i:
                        block_content.append(lines[j])
                        end_idx = j
                        break
                    block_content.append(lines[j])
                    j += 1
                else:
                    is_code_block = False  # 終わりが見つからない

                if is_code_block and len(block_content) > 2:
                    # コードブロックとして整形を試みる
                    code_text = "\n".join(block_content)

                    # JSONとしての整形を試みる
                    try:
                        # 余分な先頭と末尾の行を削除しつつ整形
                        clean_code = code_text.strip()
                        if "{" in clean_code and "}" in clean_code:
                            # JSONブロックに変換する試み
                            formatted_code = code_text.replace("'", '"')  # シングルクォートをダブルクォートに置き換え
                            lines[start_idx] = f"```json\n{formatted_code}\n```"

                            # 整形した分の行を削除
                            for _ in range(end_idx - start_idx):
                                if start_idx + 1 < len(lines):
                                    lines.pop(start_idx + 1)

                            # インデックスを更新
                            i = start_idx
                    except:
                        # JSONでない場合はコードブロックとして整形
                        language = "javascript" if any(keyword in code_text.lower() for keyword in ["function", "const", "var"]) else ""
                        lines[start_idx] = f"```{language}\n{code_text}\n```"

                        # 整形した分の行を削除
                        for _ in range(end_idx - start_idx):
                            if start_idx + 1 < len(lines):
                                lines.pop(start_idx + 1)

                        # インデックスを更新
                        i = start_idx

            i += 1

        return '\n'.join(lines)

    def _improve_tables(self, markdown_content: str) -> str:
        """表組みのマークダウン表現を改善する"""
        # マークダウンの表を検出して改善
        table_pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n)+)'

        def fix_table(match):
            table = match.group(1)

            # 列の幅を揃える
            lines = table.strip().split('\n')
            if len(lines) < 2:
                return table

            # 各行のセル数をカウント
            cells_per_row = [line.count('|') - 1 for line in lines]
            max_cells = max(cells_per_row)

            # 各行を調整
            for i in range(len(lines)):
                cells = lines[i].split('|')
                cells = [c.strip() for c in cells if c]  # 空のセルを削除

                # セルの足りない分を追加
                while len(cells) < max_cells:
                    cells.append('')

                # 行を再構成
                lines[i] = '| ' + ' | '.join(cells) + ' |'

            # 修正された表を返す（PDF表示向けに前後に改行を追加）
            return '\n' + '\n'.join(lines) + '\n\n'

        # 表組みを修正
        markdown_content = re.sub(table_pattern, fix_table, markdown_content)

        return markdown_content

    def _fix_image_paths(self, markdown_content: str, base_url: str) -> str:
        """Markdown内の画像パスを修正する"""
        # ![alt](relative/path.jpg) 形式の画像タグを検出して修正
        def replace_img_path(match):
            alt_text = match.group(1)
            img_path = match.group(2)

            # 既に絶対URLなら変更しない
            if img_path.startswith(('http://', 'https://', '//')):
                return f"![{alt_text}]({img_path})"

            # 相対パスを絶対パスに変換
            absolute_path = urljoin(base_url, img_path)
            return f"![{alt_text}]({absolute_path})"

        # 画像パターンを正規表現で検索して置換
        return re.sub(r'!\[(.*?)\]\(([^)]+)\)', replace_img_path, markdown_content)


class ContentRepository:
    """クロールしたコンテンツを管理するコンポーネント（改善版）"""
    
    def __init__(self):
        self.contents = {}  # URLをキーとしたコンテンツ辞書
        self.urls_by_status = {
            'success': set(),  # 正常に取得できたURL
            'error': set(),    # エラーが発生したURL
            'skipped': set(),  # スキップされたURL
        }
        self.metadata = {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_urls': 0,
            'success_count': 0,
            'error_count': 0,
            'skipped_count': 0,
        }
        
    def add(self, page_data: Dict, status: str = 'success') -> None:
        """コンテンツを追加する"""
        url = page_data['url']
        self.contents[url] = page_data
        
        # ステータス別URLセットを更新
        if status in self.urls_by_status:
            self.urls_by_status[status].add(url)
            
        # メタデータを更新
        self.metadata['total_urls'] += 1
        status_count_key = f'{status}_count'
        if status_count_key in self.metadata:
            self.metadata[status_count_key] += 1
        
    def get(self, url: str) -> Optional[Dict]:
        """URLに対応するコンテンツを取得する"""
        return self.contents.get(url)
    
    def get_all(self) -> Dict[str, Dict]:
        """すべてのコンテンツを取得する"""
        return self.contents
    
    def get_urls_by_status(self, status: str) -> Set[str]:
        """指定されたステータスのURLセットを取得する"""
        return self.urls_by_status.get(status, set())
    
    def count(self) -> int:
        """コンテンツの数を取得する"""
        return len(self.contents)
    
    def finalize(self) -> None:
        """クロール完了時にメタデータを更新する"""
        self.metadata['end_time'] = datetime.now().isoformat()
        
    def get_metadata(self) -> Dict:
        """リポジトリのメタデータを取得する"""
        if self.metadata['end_time'] is None:
            self.metadata['end_time'] = datetime.now().isoformat()
            
        # 各カウントを最新の状態に更新
        self.metadata['success_count'] = len(self.urls_by_status['success'])
        self.metadata['error_count'] = len(self.urls_by_status['error'])
        self.metadata['skipped_count'] = len(self.urls_by_status['skipped'])
        
        return self.metadata


class CrawlCache:
    """クロール結果を永続的に保存し、差分検知に使用するコンポーネント（改善版）"""
    
    def __init__(self, domain: str, cache_dir: str = "cache"):
        self.domain = domain
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.db_path = os.path.join(cache_dir, f"{domain}.db")
        self._initialize_db()
        
    def _initialize_db(self):
        """データベースを初期化する"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # pages テーブルを作成（拡張版）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            title TEXT,
            content_hash TEXT,
            etag TEXT,
            last_modified TEXT,
            last_crawled TEXT,
            markdown_content TEXT,
            meta_description TEXT,
            status_code INTEGER
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
            deleted_count INTEGER,
            duration_seconds INTEGER
        )
        ''')
        
        # インデックスを作成（パフォーマンス向上）
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_last_crawled ON pages(last_crawled)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_history_date ON crawl_history(crawl_date)')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        """SQLite接続を取得する（接続プールの実装）"""
        return sqlite3.connect(self.db_path)
    
    @contextmanager
    def _db_transaction(self):
        """データベーストランザクションのコンテキストマネージャ"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logging.error(f"Database transaction error: {e}")
            raise
        finally:
            conn.close()
    
    def get_page(self, url: str) -> Optional[Dict]:
        """URLに対応するキャッシュされたページ情報を取得する"""
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pages WHERE url = ?', (url,))
            row = cursor.fetchone()
            
        if row:
            return dict(row)
        return None
    
    def add_or_update_page(self, page_data: Dict) -> bool:
        """ページ情報をキャッシュに追加または更新する"""
        url = page_data['url']
        title = page_data['title']
        markdown_content = page_data.get('markdown_content', '')
        meta_description = page_data.get('meta_description', '')
        content_hash = self._compute_hash(markdown_content)
        etag = page_data.get('etag')
        last_modified = page_data.get('last_modified')
        status_code = page_data.get('status_code', 200)
        last_crawled = datetime.now().isoformat()
        
        with self._db_transaction() as conn:
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
                    last_crawled = ?, markdown_content = ?, meta_description = ?, status_code = ?
                WHERE url = ?
                ''', (title, content_hash, etag, last_modified, last_crawled, markdown_content, meta_description, status_code, url))
            else:
                # 新規追加
                cursor.execute('''
                INSERT INTO pages 
                (url, title, content_hash, etag, last_modified, last_crawled, markdown_content, meta_description, status_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (url, title, content_hash, etag, last_modified, last_crawled, markdown_content, meta_description, status_code))
            
            conn.commit()
        
        return is_update
    
    def get_all_urls(self) -> Set[str]:
        """キャッシュに保存されているすべてのURLを取得する"""
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT url FROM pages')
            urls = {row[0] for row in cursor.fetchall()}
        
        return urls
    
    def delete_urls(self, urls: List[str]) -> int:
        """指定されたURLをキャッシュから削除する"""
        if not urls:
            return 0
            
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            
            # SQLインジェクション対策のためにプレースホルダーを使用
            placeholders = ', '.join(['?'] * len(urls))
            cursor.execute(f'DELETE FROM pages WHERE url IN ({placeholders})', urls)
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        return deleted_count
    
    def save_crawl_history(self, page_count: int, new_count: int, updated_count: int, deleted_count: int, duration_seconds: int) -> int:
        """クロール履歴を保存する（拡張版：所要時間を追加）"""
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            
            crawl_date = datetime.now().isoformat()
            
            cursor.execute('''
            INSERT INTO crawl_history 
            (crawl_date, page_count, new_count, updated_count, deleted_count, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (crawl_date, page_count, new_count, updated_count, deleted_count, duration_seconds))
            
            history_id = cursor.lastrowid
            conn.commit()
        
        return history_id
    
    def is_content_changed(self, url: str, markdown_content: str) -> bool:
        """ページのコンテンツが前回のクロール時から変更されているかどうかを確認する"""
        current_hash = self._compute_hash(markdown_content)
        
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT content_hash FROM pages WHERE url = ?', (url,))
            row = cursor.fetchone()
        
        if not row:
            return True  # 新規ページなので変更ありとみなす
        
        return current_hash != row[0]
    
    def _compute_hash(self, content: str) -> str:
        """コンテンツのハッシュ値を計算する"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_diff(self, url: str, current_content: str) -> str:
        """前回のコンテンツとの差分を取得する（改善版：コンテキスト差分表示）"""
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT markdown_content FROM pages WHERE url = ?', (url,))
            row = cursor.fetchone()
        
        if not row:
            return "新規ページ"
            
        old_content = row[0]
        if not old_content:
            return "前回のコンテンツが空"
            
        # 差分を計算（コンテキスト形式、より多くのコンテキスト行を表示）
        diff = difflib.unified_diff(
            old_content.splitlines(),
            current_content.splitlines(),
            fromfile="前回のバージョン",
            tofile="現在のバージョン",
            lineterm='',
            n=3  # コンテキスト行数を3行に増加
        )
        
        return '\n'.join(diff)
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """最新のクロール履歴を取得する"""
        with self._db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM crawl_history 
            ORDER BY crawl_date DESC 
            LIMIT ?
            ''', (limit,))
            
            history = [dict(row) for row in cursor.fetchall()]
        
        return history


class FileExporter:
    """クロールしたコンテンツをファイルに出力するコンポーネント（改善版）"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_markdown(self, repository: ContentRepository, filename: str) -> str:
        """コンテンツをMarkdownファイルとしてエクスポートする"""
        contents = repository.get_all()
        
        # 出力ファイルのパス
        output_path = os.path.join(self.output_dir, filename)
        
        # コンテンツを目次付きでまとめる
        markdown_contents = []
        
        # 目次の作成
        toc = ["# 目次\n"]
        for i, (url, page_data) in enumerate(sorted(contents.items()), 1):
            title = page_data.get('title', 'No Title')
            toc.append(f"{i}. [{title}](#{self._make_anchor(title)})")
        
        markdown_contents.append("\n".join(toc) + "\n\n---\n\n")
        
        # 本文の追加
        for url, page_data in sorted(contents.items()):
            if 'markdown_content' in page_data:
                markdown_contents.append(page_data['markdown_content'])
            
        # ファイルに書き込む
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n---\n\n'.join(markdown_contents))
            
        return output_path
    
    def _make_anchor(self, text: str) -> str:
        """テキストからアンカーIDを生成する"""
        # 小文字に変換し、アルファベット・数字・ハイフン以外の文字をハイフンに置換
        anchor = re.sub(r'[^\w\- ]', '', text.lower())
        # スペースをハイフンに置換し、連続するハイフンを1つにまとめる
        anchor = re.sub(r'[\- ]+', '-', anchor)
        return anchor.strip('-')
    
    def export_diff_report(self, diff_data: Dict, filename: str) -> str:
        """差分レポートをMarkdownファイルとして出力する（改善版）"""
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # レポートヘッダーとメタデータ
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"# 差分レポート - {now}\n\n")
            
            # サマリー情報
            f.write("## サマリー\n\n")
            f.write(f"- 合計ページ数: {diff_data['total']}\n")
            f.write(f"- 新規ページ: {len(diff_data['new_pages'])}\n")
            f.write(f"- 更新ページ: {len(diff_data['updated_pages'])}\n")
            f.write(f"- 削除ページ: {len(diff_data['deleted_pages'])}\n")
            # 経過時間があれば表示
            if 'duration_seconds' in diff_data:
                duration = diff_data['duration_seconds']
                minutes, seconds = divmod(duration, 60)
                f.write(f"- クロール時間: {minutes}分{seconds}秒\n")
            f.write("\n")
            
            # 新規ページ
            if diff_data['new_pages']:
                f.write("## 新規ページ\n\n")
                for url in sorted(diff_data['new_pages']):
                    f.write(f"- [{url}]({url})\n")
                f.write("\n")
            
            # 更新ページ
            if diff_data['updated_pages']:
                f.write("## 更新ページ\n\n")
                for url in sorted(diff_data['updated_pages']):
                    f.write(f"- [{url}]({url})\n")
                f.write("\n")
            
            # 削除ページ
            if diff_data['deleted_pages']:
                f.write("## 削除ページ\n\n")
                for url in sorted(diff_data['deleted_pages']):
                    f.write(f"- {url}\n")
                f.write("\n")
            
            # 詳細な差分情報
            if diff_data.get('diffs'):
                f.write("## 詳細な差分\n\n")
                for url, diff in sorted(diff_data['diffs'].items()):
                    f.write(f"### {url}\n\n")
                    f.write("```diff\n")
                    f.write(diff)
                    f.write("\n```\n\n")
        
        return output_path
    
    def export_summary(self, repository: ContentRepository, diff_data: Dict, filename: str) -> str:
        """クロール結果の概要レポートをエクスポートする"""
        output_path = os.path.join(self.output_dir, filename)
        
        metadata = repository.get_metadata()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# クロール概要レポート - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # クロール概要
            f.write("## クロール情報\n\n")
            f.write(f"- 開始時間: {metadata['start_time']}\n")
            f.write(f"- 終了時間: {metadata['end_time']}\n")
            if 'duration_seconds' in diff_data:
                minutes, seconds = divmod(diff_data['duration_seconds'], 60)
                f.write(f"- 所要時間: {minutes}分{seconds}秒\n")
            f.write(f"- 合計URL: {metadata['total_urls']}\n")
            f.write(f"- 成功: {metadata['success_count']}\n")
            f.write(f"- エラー: {metadata['error_count']}\n")
            f.write(f"- スキップ: {metadata['skipped_count']}\n\n")
            
            # 差分概要
            f.write("## 変更概要\n\n")
            f.write(f"- 新規ページ: {len(diff_data['new_pages'])}\n")
            f.write(f"- 更新ページ: {len(diff_data['updated_pages'])}\n")
            f.write(f"- 削除ページ: {len(diff_data['deleted_pages'])}\n\n")
            
            # エラーページのリスト
            error_urls = repository.get_urls_by_status('error')
            if error_urls:
                f.write("## エラーページ\n\n")
                for url in sorted(error_urls):
                    f.write(f"- {url}\n")
                f.write("\n")
        
        return output_path