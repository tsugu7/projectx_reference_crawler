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
            markdown_content = f"コンテンツの変換中にエラーが発生しました: {str(e)}"

        # Markdownタイトルを作成
        markdown_title = f"# {title}\n\n"

        # メタ説明を追加（あれば）
        meta_section = f"*{meta_description}*\n\n" if meta_description else ""

        # URL情報を追加
        url_info = f"*出典: {url}*\n\n"

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

            # すべての特殊文字パターンを定義（より網羅的に）
            special_chars = ['ðï', 'ðï¸', 'â', '\xa0', '\u2028', '\u2029']
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # 絵文字
                "\U0001F300-\U0001F5FF"  # シンボル
                "\U0001F680-\U0001F6FF"  # 乗り物とマップ記号
                "\U0001F700-\U0001F77F"  # 顔文字
                "\U0001F780-\U0001F7FF"  # 絵文字の追加
                "\U0001F800-\U0001F8FF"  # 絵文字の追加
                "\U0001F900-\U0001F9FF"  # 絵文字の追加
                "\U0001FA00-\U0001FA6F"  # 絵文字の追加
                "\U0001FA70-\U0001FAFF"  # 絵文字の追加
                "\U00002702-\U000027B0"  # その他のシンボル
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )

            # 「Direct link to」などの不要なテキストを含むa要素を修正
            for a_elem in doc.xpath('//a[contains(text(), "Direct link to")]'):
                # テキストを空にする
                a_elem.text = ""

            # スペーシング修正：見出し内の不要なスペースを調整
            for h in doc.xpath('//h1 | //h2 | //h3 | //h4 | //h5 | //h6'):
                if h.text:
                    # 連続スペースを1つに置換
                    h.text = re.sub(r'\s+', ' ', h.text).strip()

                    # 絵文字や特殊文字を削除
                    h.text = emoji_pattern.sub('', h.text)
                    for char in special_chars:
                        h.text = h.text.replace(char, '')

            # 見出し要素内のaタグを特別処理（見出しリンクを確実に処理）
            for a in doc.xpath('//h1//a | //h2//a | //h3//a | //h4//a | //h5//a | //h6//a'):
                if a.text:
                    # 特殊文字を削除しつつスペースを調整
                    a.text = re.sub(r'\s+', ' ', a.text).strip()
                    a.text = emoji_pattern.sub('', a.text)
                    for char in special_chars:
                        a.text = a.text.replace(char, '')

            # ドキュメント全体の特殊文字を処理
            for elem in doc.xpath('//*'):
                # テキストノードをチェック
                if elem.text:
                    # 絵文字を削除
                    elem.text = emoji_pattern.sub('', elem.text)
                    # 特殊文字を削除
                    for char in special_chars:
                        elem.text = elem.text.replace(char, '')

                # テイルテキストもチェック
                if elem.tail:
                    elem.tail = emoji_pattern.sub('', elem.tail)
                    for char in special_chars:
                        elem.tail = elem.tail.replace(char, '')

            # カテゴリページのフォーマットを修正（h2内の絵文字などを削除）
            for h2 in doc.xpath('//h2'):
                # スペースの後の数字（items）などが含まれている場合は削除
                if h2.text and re.search(r'\d+\s*items', h2.text):
                    h2.text = re.sub(r'\d+\s*items', '', h2.text)

            # テーブル整形の改善
            for table in doc.xpath('//table'):
                # Markdownでの表組み変換を改善するためのクラスを追加
                table.attrib['class'] = 'markdown-table'

                # テーブルのセルを整形
                for cell in table.xpath('.//th | .//td'):
                    if cell.text:
                        cell.text = cell.text.strip()
                        cell.text = emoji_pattern.sub('', cell.text)
                        for char in special_chars:
                            cell.text = cell.text.replace(char, '')

            # コードブロックの整形
            for code in doc.xpath('//pre/code | //code'):
                # コードブロック内のHTML実体参照を保持しておく
                if code.text:
                    # インデントと空白を保持しながら特殊文字のみ削除
                    code.text = emoji_pattern.sub('', code.text)
                    for char in special_chars:
                        code.text = code.text.replace(char, '')

            # 属性値も処理
            for elem in doc.xpath('//*[@*]'):  # 属性を持つすべての要素
                for attr_name in elem.attrib:
                    if isinstance(elem.attrib[attr_name], str):
                        # 特殊文字を削除
                        elem.attrib[attr_name] = emoji_pattern.sub('', elem.attrib[attr_name])
                        for char in special_chars:
                            elem.attrib[attr_name] = elem.attrib[attr_name].replace(char, '')

            # 最終的なセーフティネット - 不要な文字を削除
            for elem in doc.xpath('//*'):
                # テキストをUnicode正規化
                if hasattr(elem, 'text') and elem.text:
                    # 不要な特殊文字を削除
                    elem.text = re.sub(r'[^\x00-\x7F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF\s\.,;:!?\-_\'\"\/\\\[\]\(\)\{\}\+\*\&\^\%\$\#\@<>=~`|]', '', elem.text)

                if hasattr(elem, 'tail') and elem.tail:
                    elem.tail = re.sub(r'[^\x00-\x7F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF\s\.,;:!?\-_\'\"\/\\\[\]\(\)\{\}\+\*\&\^\%\$\#\@<>=~`|]', '', elem.tail)

            # HTML文字列に戻す
            html_cleaned = lxml.html.tostring(doc, encoding='unicode')

            # 最終的なセーフティネット：直接文字列置換で残っている可能性のある特殊文字を削除
            for char in special_chars:
                html_cleaned = html_cleaned.replace(char, '')

            # 複数の連続改行を整理
            html_cleaned = re.sub(r'\n{3,}', '\n\n', html_cleaned)

            return html_cleaned
        except Exception as e:
            logging.warning(f"HTML preprocessing error: {e}")
            # エラーが発生した場合は元のHTMLを返す
            return html_content

    def _postprocess_markdown(self, markdown_content: str) -> str:
        """Markdown変換後の後処理を行う"""
        # 処理順序を最適化 - 最初にダブルダッシュを処理
        markdown_content = re.sub(r'\n--\n', '\n\n', markdown_content)

        # 特殊文字を先に削除
        markdown_content = markdown_content.replace('â', '')
        markdown_content = markdown_content.replace('ðï¸', '')
        markdown_content = markdown_content.replace('ðï', '')

        # 「Direct link to」などの不要なテキストを削除
        markdown_content = re.sub(r'\[â\]\([^)]+\s+"Direct link to [^"]+"\)', '', markdown_content)
        markdown_content = re.sub(r'\[\]\([^)]+\s+"Direct link to [^"]+"\)', '', markdown_content)
        markdown_content = re.sub(r'\[[^\]]*\]\([^)]+\s+"Direct link to [^"]+"\)', '', markdown_content)

        # 見出し修正を優先的に先に処理 (重要: 他の変換の前に行う)
        # 複数行にまたがる見出しを一行に結合
        # 例: ## [
        # Text] -> ## [Text]
        for _ in range(3):
            # 見出しタグの後の改行を修正
            markdown_content = re.sub(r'(#{1,6})\s*\n\s*', r'\1 ', markdown_content)

            # 見出しのリンク開始括弧内の改行を修正
            markdown_content = re.sub(r'(#{1,6}\s*)\[\s*\n\s*', r'\1[', markdown_content)

            # 見出しのリンクテキスト内の改行を修正
            markdown_content = re.sub(r'(\[\s*[^\n\]]*)\n\s*([^\]]*\])', r'\1 \2', markdown_content)

            # 見出しのリンク全体の途中改行を修正
            markdown_content = re.sub(r'(#{1,6}\s+\[[^\]]+\])\s*\n\s*(\([^)]+\))', r'\1\2', markdown_content)

            # 見出し全体が複数行に分かれている場合を修正
            markdown_content = re.sub(r'(#{1,6}\s+[A-Za-z][^\n]*)\s*\n\s*([A-Za-z][^\n]*)', r'\1 \2', markdown_content)

            # リンクテキストとURL間の改行を修正（例: [Search for PositionsAPI URL: /api/Position/search\nOpen](https://...)）
            markdown_content = re.sub(r'(\[(?:[^\[\]]|\[[^\[\]]*\])*?)\n\s*([^\]]*?\]\([^)]+\))', r'\1 \2', markdown_content)

            # リンクのURL部分が改行されている場合も修正
            markdown_content = re.sub(r'(\]\()([^)\n]*)\n\s*([^)]*\))', r'\1\2\3', markdown_content)

        # カテゴリページの見出しフォーマットを改善（特殊文字を削除しつつ）
        markdown_content = re.sub(r'##\s*\[(ðï¸\s*)?([^\]]*?)(\s*\d+\s*items)?\]\(([^)]+)\)', r'## [\2](\4)', markdown_content)

        # 見出し内のスペース調整
        markdown_content = re.sub(r'(#{1,6})\s*\[ ', r'\1 [', markdown_content)

        # マークダウンリンク内の特殊文字のみを置換
        markdown_content = re.sub(r'\[ðï¸\s*([^\]]*?)(\s*\d+\s*items)?\]', r'[\1]', markdown_content)

        # 見出し行内の特殊文字を削除（すべての見出しレベルに対応）
        markdown_content = re.sub(r'(#{1,6})\s+\[(ðï¸?\s*)?([^\]]*?)\](\([^)]+\))', r'\1 [\3]\4', markdown_content)
        markdown_content = re.sub(r'(#{1,4})\s*\[ðï¸?\s*([^\]]*)\]\(([^)]+)\)', r'\1 [\2](\3)', markdown_content)

        # 任意のリンクパターンの修正 - 特に見出し以外の場所にある分割されたリンク
        # 例: [Search    for    PositionsAPI    URL:    /api/Position/search\n Open](...) のような場合
        markdown_content = re.sub(r'\[([^\]]*?)\n\s*([^\]]*?)\](\([^)]+\))', r'[\1 \2]\3', markdown_content)

        # 複数の連続スペースをひとつに修正（リンク内での整形）
        markdown_content = re.sub(r'\[([^\]]*?)\s{2,}([^\]]*?)\]', r'[\1 \2]', markdown_content)

        # リンク後の説明文を適切に区切る処理（改良版）
        # URL直後に続く説明文があれば改行して区切る
        markdown_content = re.sub(r'(\]\([^)]+\))([\w])', r'\1\n\2', markdown_content)

        # 見出し + URL + 説明文のパターンをより強固に処理
        markdown_content = re.sub(r'(#{1,6}\s+\[[^\]]+\]\([^)]+\))\s+([A-Z][a-z])', r'\1\n\n\2', markdown_content)

        # カテゴリページの説明文が見出しとリンクされている場合、適切に分離
        markdown_content = re.sub(r'(#{1,6}\s*\[[^\]]+\]\([^)]+\))([A-Za-z])', r'\1\n\2', markdown_content)

        # 連続するヘッダーの間に適切な空白を挿入
        markdown_content = re.sub(r'(#{1,6}\s*\[.*?\]\(.*?\))\s*(#{1,6})', r'\1\n\n\2', markdown_content)

        # 連続する空白を1つに
        markdown_content = re.sub(r' {2,}', ' ', markdown_content)

        # リスト項目の間隔を最適化
        markdown_content = re.sub(r'(\* .*)\n\n(?=\* )', r'\1\n', markdown_content)
        markdown_content = re.sub(r'(\]\([^)]+\))\n\n(\*)', r'\1\n\2', markdown_content)

        # 見出しの後ろに不要な## マークが残っている場合は削除
        markdown_content = re.sub(r'##\s*$', '', markdown_content)

        # テーブル内の特殊文字も削除
        markdown_content = re.sub(r'\|(.*?)ðï¸(.*?)\|', r'|\1\2|', markdown_content)
        markdown_content = re.sub(r'\|(.*?)ðï(.*?)\|', r'|\1\2|', markdown_content)

        # 表組みの整形を改善
        markdown_content = self._improve_tables(markdown_content)

        # JSONやコードブロックを整形
        markdown_content = self._format_code_blocks(markdown_content)

        # 見出しの前後に適切な改行を追加して読みやすくする
        markdown_content = re.sub(r'\n(#{1,6}\s+[^\n]+)\n', r'\n\1\n\n', markdown_content)

        # 複数見出しの間の余分な改行を修正（最大2行まで）
        markdown_content = re.sub(r'(#{1,6}[^\n]+)\n\n\n+(#{1,6})', r'\1\n\n\2', markdown_content)

        # 残っている特殊文字を最終的に削除（セーフティネット）
        markdown_content = markdown_content.replace('ðï¸', '')
        markdown_content = markdown_content.replace('ðï', '')

        # コンテンツの区切りを明確にする（見出し間の区切り）
        markdown_content = re.sub(r'(#{2,4}\s+[^\n]+)\n([^#\n])', r'\1\n\n\2', markdown_content)

        # 非ASCII文字を確実に処理
        try:
            # まずはヘッダーや重要なセクションを保持する方法を試す
            clean_content = ''
            for line in markdown_content.splitlines():
                # 見出し行やその他の重要なパターンは特別に処理
                if re.match(r'^#{1,6}\s+', line) or '[' in line or '*' in line or '|' in line:
                    # 不要な特殊文字だけを削除
                    line = re.sub(r'[^\x00-\x7F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF\s\[\]\(\)\*\|\.,:;\'"!?-]', '', line)
                else:
                    # 一般のテキスト行はより厳密に処理
                    line = re.sub(r'[^\x00-\x7F]', '', line)

                clean_content += line + '\n'
            markdown_content = clean_content
        except Exception:
            # エラーが発生した場合は単純に非ASCII文字を削除するフォールバック
            markdown_bytes = markdown_content.encode('ascii', 'ignore')
            markdown_content = markdown_bytes.decode('ascii')

        # 全体的な整理（余分な改行を最終調整）
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

        return markdown_content

    def _format_code_blocks(self, markdown_content: str) -> str:
        """コードブロックとJSONの整形を行う（改良版）"""
        # 既存コードブロックのパターン（より柔軟な対応）
        code_block_pattern = r'```(?:json|javascript|js|typescript|ts|python|py|bash|sh|xml|html|css)?\s*\n(.*?)\n```'

        # コードとして扱うキーワードリスト（言語検出用）
        code_keywords = {
            'javascript': ['function', 'const', 'var', 'let', '=>', 'return', 'import ', 'export ', 'class ', 'extends'],
            'typescript': ['interface', 'type ', 'enum ', 'namespace', '<T>', 'implements'],
            'python': ['def ', 'class ', 'import ', 'from ', 'if __name__', 'return', 'self.', 'async def'],
            'bash': ['#!/bin/bash', 'chmod', 'sudo ', 'apt ', 'yum ', 'grep ', 'awk ', 'sed '],
            'json': ['":', '": ', '"name":', '"version":', '"dependencies":'],
            'xml': ['<?xml', '<tag>', '</tag>', '<node ', '<element'],
            'html': ['<!DOCTYPE', '<html>', '</html>', '<div>', '<span>', '<p>']
        }

        def detect_language(code_text):
            """コードブロックの言語を検出する"""
            # JSON形式を優先的に検出
            if code_text.strip().startswith('{') and code_text.strip().endswith('}') and ('"' in code_text or ':' in code_text):
                try:
                    # JSON構文として解析可能か確認
                    # シングルクォートをダブルクォートに置換（JavaScriptスタイルをJSON対応にする）
                    test_json = code_text.replace("'", '"').replace("//", "#")
                    json.loads(test_json.strip())
                    return 'json'
                except:
                    pass

            # 各言語の特徴的なキーワードを探す
            for lang, keywords in code_keywords.items():
                # いくつかのキーワードが存在するかチェック
                matches = sum(1 for keyword in keywords if keyword in code_text.lower())
                if matches >= 2:  # 2つ以上のキーワードがマッチしたら
                    return lang

            # 単一行の簡単な検出
            code_lower = code_text.lower()
            if 'function' in code_lower or 'const ' in code_lower or code_lower.count(';') > 2:
                return 'javascript'
            if code_lower.count('def ') > 0 or code_lower.count('import ') > 0:
                return 'python'
            if code_lower.count('<') > 2 and code_lower.count('>') > 2:
                return 'html' if '<html' in code_lower or '<body' in code_lower else 'xml'

            # 判別できない場合は空文字を返す
            return ''

        def format_code_block(match):
            """コードブロックを整形する"""
            code = match.group(1)
            # 言語タグを取得（定義されていれば）
            if '```' in match.group(0) and match.group(0).split('```')[1].strip():
                language = match.group(0).split('```')[1].strip()
            else:
                language = ''

            # 空のコードブロックは処理しない
            if not code.strip():
                return match.group(0)

            # JSONの整形を試みる
            if language.lower() == 'json' or (not language and (code.strip().startswith('{') and code.strip().endswith('}'))):
                try:
                    # シングルクォートをダブルクォートに置換（JavaScriptスタイルのJSONも対応）
                    json_code = code.replace("'", '"').replace("//", "#")
                    parsed_json = json.loads(json_code.strip())
                    formatted_json = json.dumps(parsed_json, indent=2)
                    return f"```json\n{formatted_json}\n```"
                except:
                    # JSON解析に失敗した場合は通常のコードとして処理
                    if not language:
                        language = detect_language(code)

            # 言語が指定されていない場合は自動検出
            if not language:
                language = detect_language(code)

            # コードのインデント整形
            # 行頭の共通インデントを検出して削除
            lines = code.split('\n')
            if len(lines) > 1:
                # 空でない行のみを対象に共通インデント検出
                non_empty_lines = [line for line in lines if line.strip()]
                if non_empty_lines:
                    # 各行のインデント数を計算
                    indents = [len(line) - len(line.lstrip()) for line in non_empty_lines]
                    # 最小のインデント数を共通インデントとして使用
                    common_indent = min(indents) if indents else 0

                    # 共通インデントを削除
                    if common_indent > 0:
                        formatted_lines = []
                        for line in lines:
                            if line.strip():  # 空行は無視
                                # 共通インデント分だけ削除
                                formatted_lines.append(line[common_indent:])
                            else:
                                formatted_lines.append(line)

                        code = "\n".join(formatted_lines)

            # 言語タグを準備（検出した言語または指定された言語）
            lang_tag = language if language else ''

            # PDFフォーマット改善のため前後に空行を追加
            return f"\n```{lang_tag}\n{code}\n```\n"

        # コードブロックを整形
        markdown_content = re.sub(code_block_pattern, format_code_block, markdown_content, flags=re.DOTALL)

        # インラインJSONの検出と整形（段落内の１行JSONなど）
        lines = markdown_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 単一行のJSONらしき構造を検出して整形
            if (line.startswith('{') and line.endswith('}') and '"' in line and ':' in line and
                len(line) > 10 and not line.startswith('```')):
                try:
                    # JSONとして解析
                    parsed_json = json.loads(line.replace("'", '"'))
                    # 整形されたJSONを作成
                    formatted_json = json.dumps(parsed_json, indent=2)
                    # コードブロックに置き換え
                    lines[i] = f"```json\n{formatted_json}\n```"
                except:
                    # JSONではない場合はそのまま
                    pass

            # コードブロックっぽい連続した行を探す（ブレース開始など）
            elif i < len(lines) - 2 and not lines[i].startswith('#') and not lines[i].startswith('```'):
                # 開始ブレース・括弧があるかチェック
                if (('{' in lines[i] and lines[i].strip().endswith('{')) or
                    ('(' in lines[i] and lines[i].strip().endswith('('))):

                    # コードブロックの範囲を特定
                    start_idx = i
                    block_content = [lines[i]]
                    matching_char = '}' if '{' in lines[i] else ')'

                    # 終了ブレース・括弧を探す
                    j = i + 1
                    while j < min(i + 30, len(lines)):  # 最大30行までを探索範囲とする
                        if matching_char in lines[j]:
                            block_content.append(lines[j])
                            end_idx = j
                            break
                        block_content.append(lines[j])
                        j += 1
                    else:
                        # 終了文字が見つからなかった場合
                        i += 1
                        continue

                    # コードブロックとしての整形を試みる
                    code_text = "\n".join(block_content)

                    # 言語を自動検出
                    language = detect_language(code_text)

                    # JSONの場合は特別処理
                    if language == 'json':
                        try:
                            # JavaScriptスタイルJSONをスタンダードJSONに変換
                            json_code = code_text.replace("'", '"').replace("//", "#")
                            parsed_json = json.loads(json_code.strip())
                            formatted_json = json.dumps(parsed_json, indent=2)
                            lines[start_idx] = f"```json\n{formatted_json}\n```"
                        except:
                            # 通常のコードブロックとして整形
                            lines[start_idx] = f"```{language}\n{code_text}\n```"
                    else:
                        # 非JSONコードとして整形
                        lines[start_idx] = f"```{language}\n{code_text}\n```"

                    # 整形した分の行を削除
                    for _ in range(end_idx - start_idx):
                        if start_idx + 1 < len(lines):
                            lines.pop(start_idx + 1)

                    # インデックス更新
                    i = start_idx

            i += 1

        # 行を結合して戻す
        return '\n'.join(lines)

    def _improve_tables(self, markdown_content: str) -> str:
        """表組みのマークダウン表現を改善する（PDF出力向け強化版）"""
        # マークダウンの表を検出して改善
        table_pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n)+)'

        def fix_table(match):
            table = match.group(1)

            # 空の表は処理しない
            if not table.strip():
                return table

            # 行に分割
            lines = table.strip().split('\n')
            if len(lines) < 2:
                return table

            # 各行のセル数と最大幅を計算
            max_cells = 0
            row_cells = []

            for line in lines:
                # |で分割し、前後の空セルを取り除く
                cells = [c.strip() for c in line.split('|')[1:-1]]
                row_cells.append(cells)
                max_cells = max(max_cells, len(cells))

            # 各列の最大文字幅を計算（見た目を整えるため）
            col_widths = [0] * max_cells
            for row in row_cells:
                for i, cell in enumerate(row):
                    if i < max_cells:
                        col_widths[i] = max(col_widths[i], len(cell))

            # ヘッダー行を修正（2行目の区切り行）
            if len(lines) > 1:
                header_sep = []
                for i, width in enumerate(col_widths):
                    # 元の区切り行をチェックして左右寄せを保持
                    align_marker = ""
                    if i < len(row_cells[1]):
                        cell = row_cells[1][i]
                        if cell.startswith(':') and cell.endswith(':'):
                            align_marker = ":"  # 中央寄せ
                            col_sep = ':' + '-' * max(3, width) + ':'
                        elif cell.startswith(':'):
                            align_marker = ":"  # 左寄せ
                            col_sep = ':' + '-' * max(3, width) + ' '
                        elif cell.endswith(':'):
                            align_marker = ":"  # 右寄せ
                            col_sep = ' ' + '-' * max(3, width) + ':'
                        else:
                            col_sep = '-' * max(3, width + 2)  # デフォルト（左寄せ）
                    else:
                        col_sep = '-' * max(3, width + 2)  # 新しい列はデフォルト

                    header_sep.append(col_sep)

                # 区切り行を再構築
                lines[1] = '|' + '|'.join(header_sep) + '|'

            # 各行を再構築
            formatted_lines = []
            for i, row in enumerate(row_cells):
                if i == 1:  # 区切り行はすでに処理済み
                    continue

                # 各セルを整形
                formatted_cells = []
                for j in range(max_cells):
                    if j < len(row):
                        cell = row[j]
                        # セルの内容をクリーンアップ - 特殊文字を削除
                        cell = re.sub(r'[^\x00-\x7F\s\.,;:!?\-_\'\"\/\\\[\]\(\)\{\}\+\*\&\^\%\$\#\@<>=~`|]', '', cell)
                        formatted_cells.append(cell)
                    else:
                        # 足りないセルを空で追加
                        formatted_cells.append('')

                # 行を再構築
                formatted_lines.append('| ' + ' | '.join(formatted_cells) + ' |')

            # 区切り行を挿入
            if len(formatted_lines) > 0:
                formatted_lines.insert(1, lines[1])

            # 修正された表を返す（PDF表示向けに前後に適切な余白を追加）
            return '\n\n' + '\n'.join(formatted_lines) + '\n\n'

        # 表組みを修正
        markdown_content = re.sub(table_pattern, fix_table, markdown_content)

        # シンプルな表のパターン（ヘッダーなし）も検出
        simple_table_pattern = r'(\|[^\n]+\|\n(?:\|[^\n]+\|\n){2,})'

        def fix_simple_table(match):
            table = match.group(1)
            lines = table.strip().split('\n')

            # すでに整形済みの表は処理しない（区切り行がある場合）
            if any(re.match(r'\|\s*[-:]+\s*\|', line) for line in lines):
                return table

            # ヘッダー区切り行を作成して挿入
            header_line = lines[0]
            cells_count = header_line.count('|') - 1
            sep_line = '|' + '|'.join([' ----- ' for _ in range(cells_count)]) + '|'

            # 新しい表を構築
            new_table = [lines[0], sep_line] + lines[1:]
            return '\n\n' + '\n'.join(new_table) + '\n\n'

        # シンプルな表も修正
        markdown_content = re.sub(simple_table_pattern, fix_simple_table, markdown_content)

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
            title = page_data.get('title', 'タイトルなし')
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