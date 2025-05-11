"""
Webクローラーの拡張コンポーネント
- 非同期クロールエンジン
- 並列処理のサポート
- PDF生成機能の改善
- Discord通知機能
- ビジュアルクローリング機能
"""

import os
import time
import json
import logging
import asyncio
import pdfkit
import markdown
from typing import Dict, List, Optional, Set, Tuple, Any, Union, Callable
from datetime import datetime
from urllib.parse import urlparse
from discord_webhook import DiscordWebhook, DiscordEmbed
import threading
from concurrent.futures import ThreadPoolExecutor

# ビジュアルクローリング機能をインポート
try:
    from visual_crawler import crawl_url_visual
    VISUAL_CRAWLING_AVAILABLE = True
except ImportError:
    VISUAL_CRAWLING_AVAILABLE = False
    logging.warning("ビジュアルクローリング機能が利用できません。依存ライブラリがインストールされていない可能性があります。")


class PdfConverter:
    """MarkdownファイルをPDF形式に変換するコンポーネント（改善版）"""
    
    def __init__(self, output_dir: str = "output", css_path: Optional[str] = None):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # カスタムCSSのパス（指定がなければデフォルト使用）
        self.css_path = css_path
        
        # デフォルトのCSSスタイル
        self.default_css = """
        body { 
            font-family: 'Helvetica', 'Arial', sans-serif; 
            line-height: 1.6; 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; color: #333; }
        h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { border-bottom: 1px solid #eee; padding-bottom: 5px; }
        code { background-color: #f8f8f8; padding: 2px 4px; border-radius: 3px; }
        pre { background-color: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; }
        blockquote { border-left: 5px solid #ccc; padding-left: 15px; color: #555; }
        a { color: #0366d6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        table, th, td { border: 1px solid #ddd; }
        th, td { padding: 10px; text-align: left; }
        th { background-color: #f2f2f2; }
        img { max-width: 100%; height: auto; }
        """
    
    def convert(self, markdown_path: str, title: Optional[str] = None) -> str:
        """MarkdownファイルをPDFに変換する（改善版）"""
        # 入力ファイル名からPDFファイル名を生成
        pdf_filename = os.path.basename(markdown_path).replace('.md', '.pdf')
        pdf_path = os.path.join(self.output_dir, pdf_filename)
        
        try:
            # Markdownを読み込む
            with open(markdown_path, 'r', encoding='utf-8') as md_file:
                md_content = md_file.read()
            
            # MarkdownをHTML形式に変換（拡張機能を有効化）
            html_content = markdown.markdown(
                md_content, 
                extensions=[
                    'markdown.extensions.tables', 
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.toc',
                    'markdown.extensions.footnotes'
                ]
            )
            
            # HTMLにスタイルとメタデータを追加
            html_path = os.path.join(self.output_dir, "temp.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{title or 'Crawled Content'}</title>
                    <style>
                    {self.default_css}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>""")
            
            # カスタムCSSがあれば使用
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': True
            }
            
            if self.css_path and os.path.exists(self.css_path):
                options['user-style-sheet'] = self.css_path
                
            # タイトルがあれば設定
            if title:
                options['title'] = title
            
            # Google Colab用の設定（パスを指定）
            try:
                config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
                
                # wkhtmltopdfを使用してPDFに変換
                pdfkit.from_file(html_path, pdf_path, options=options, configuration=config)
            except Exception as e:
                logging.warning(f"特定のwkhtmltopdfパスでの変換に失敗しました: {e}")
                # パスを指定せずに再試行
                pdfkit.from_file(html_path, pdf_path, options=options)
                
            # 一時ファイルを削除
            if os.path.exists(html_path):
                os.remove(html_path)
                
            return pdf_path
            
        except Exception as e:
            logging.error(f"PDF変換エラー: {e}")
            return None


class DiscordNotifier:
    """Discordに通知を送信するコンポーネント（改善版）"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    def notify(self, 
               message: str, 
               title: Optional[str] = None,
               color: int = 0x3498db,  # デフォルト：青色
               markdown_path: Optional[str] = None, 
               pdf_path: Optional[str] = None,
               diff_path: Optional[str] = None) -> bool:
        """Discord通知を送信する（改善版：Embedsサポート）"""
        try:
            # Webhookインスタンスを作成
            webhook = DiscordWebhook(url=self.webhook_url)
            
            # 埋め込みメッセージを作成
            embed = DiscordEmbed(
                title=title or "クロール結果通知",
                description=message,
                color=color
            )
            
            # タイムスタンプを追加
            embed.set_timestamp()
            
            # フッターを追加
            embed.set_footer(text="Webサイトクローラー")
            
            # 埋め込みメッセージをWebhookに追加
            webhook.add_embed(embed)
            
            # ファイルリストを作成
            file_paths = []
            if markdown_path and os.path.exists(markdown_path):
                file_paths.append((markdown_path, os.path.basename(markdown_path)))
            
            if pdf_path and os.path.exists(pdf_path):
                file_paths.append((pdf_path, os.path.basename(pdf_path)))
                
            if diff_path and os.path.exists(diff_path):
                file_paths.append((diff_path, os.path.basename(diff_path)))
            
            # ファイルを分割して送信（Discordの添付ファイル制限に対応）
            if file_paths:
                # 最大8MBの制限があるため、ファイルを小分けにして送信
                remaining_files = file_paths.copy()
                current_batch = []
                current_size = 0
                max_size = 8 * 1024 * 1024  # 8MB in bytes
                
                while remaining_files:
                    file_path, file_name = remaining_files[0]
                    file_size = os.path.getsize(file_path)
                    
                    # 単一ファイルが8MBを超える場合はスキップ
                    if file_size > max_size:
                        logging.warning(f"ファイルサイズが大きすぎるためスキップ: {file_name}")
                        remaining_files.pop(0)
                        continue
                    
                    # このバッチに追加できるか確認
                    if current_size + file_size <= max_size:
                        current_batch.append((file_path, file_name))
                        current_size += file_size
                        remaining_files.pop(0)
                    else:
                        # このバッチを送信して新しいバッチを開始
                        if current_batch:
                            self._send_webhook_with_files(webhook, current_batch)
                            # 次のバッチのために新しいWebhookを作成
                            webhook = DiscordWebhook(url=self.webhook_url)
                            current_batch = []
                            current_size = 0
                
                # 最後のバッチを送信
                if current_batch:
                    self._send_webhook_with_files(webhook, current_batch)
                    
                return True
            
            else:
                # ファイルなしで通知を送信
                response = webhook.execute()
                
                # レスポンスコードをチェック
                if response and 200 <= response.status_code < 300:
                    logging.info("Discord通知を送信しました")
                    return True
                else:
                    status_code = response.status_code if response else 'No response'
                    logging.error(f"Discord通知の送信に失敗: {status_code}")
                    return False
                
        except Exception as e:
            logging.error(f"Discord通知エラー: {e}")
            return False
    
    def _send_webhook_with_files(self, webhook, file_batch):
        """ファイルバッチをDiscordに送信する"""
        for file_path, file_name in file_batch:
            with open(file_path, 'rb') as f:
                webhook.add_file(file=f.read(), filename=file_name)
        
        response = webhook.execute()
        if not response or not (200 <= response.status_code < 300):
            status_code = response.status_code if response else 'No response'
            logging.error(f"ファイル付きDiscord通知の送信に失敗: {status_code}")


class AsyncCrawler:
    """並列処理を活用した非同期クローラーエンジン"""
    
    def __init__(self, config, components):
        """
        非同期クローラーの初期化

        Args:
            config: クローラー設定
            components: 必要なコンポーネント（url_filter, fetcher, parser, markdown_converter, cache, repository）
        """
        self.config = config
        self.url_filter = components['url_filter']
        self.fetcher = components['fetcher']
        self.parser = components['parser']
        self.markdown_converter = components['markdown_converter']
        self.cache = components.get('cache')
        self.repository = components['repository']

        # ビジュアルクローリングモードの設定
        self.visual_mode = getattr(config, 'visual_mode', False)
        self.visual_config = getattr(config, 'visual_config', {})

        # クロール状態の追跡
        self.visited_urls = set()
        self.queued_urls = set([config.base_url])
        self.queue = asyncio.Queue()
        self.queue.put_nowait(config.base_url)

        # 差分情報の追跡
        self.new_pages = []
        self.updated_pages = []
        self.deleted_pages = []
        self.page_diffs = {}

        # 統計データ
        self.stats = {
            'start_time': time.time(),
            'end_time': None,
            'processed_urls': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'skipped_urls': 0,
            'visual_mode': self.visual_mode
        }

        # 並列処理の制御
        self.max_workers = config.max_workers
        self.semaphore = asyncio.Semaphore(self.max_workers)

        # 状態制御
        self.is_running = False
        self.stop_event = asyncio.Event()
    
    async def crawl(self) -> Tuple[Dict, Dict]:
        """Webサイトを非同期でクロールする"""
        self.is_running = True
        workers = []
        
        # 進捗ロギング用タスク
        progress_task = asyncio.create_task(self._log_progress())
        
        try:
            # ワーカータスクを作成
            for _ in range(self.max_workers):
                worker = asyncio.create_task(self._worker())
                workers.append(worker)
            
            # すべてのワーカーが完了するまで待機
            await asyncio.gather(*workers)
            
        except asyncio.CancelledError:
            logging.info("クロールがキャンセルされました")
            # すべてのワーカーをキャンセル
            for worker in workers:
                worker.cancel()
        finally:
            # 進捗ロギング用タスクをキャンセル
            progress_task.cancel()
            self.is_running = False
            
            # 削除されたページを特定（差分検知が有効な場合）
            if self.cache and self.config.diff_detection:
                cached_urls = self.cache.get_all_urls()
                current_urls = set(self.repository.get_all().keys())
                self.deleted_pages = list(cached_urls - current_urls)
                
                # 削除されたページをキャッシュから削除
                if self.deleted_pages:
                    self.cache.delete_urls(self.deleted_pages)
                
                # 統計情報を記録
                self.stats['end_time'] = time.time()
                duration_seconds = int(self.stats['end_time'] - self.stats['start_time'])
                
                # クロール履歴を保存
                self.cache.save_crawl_history(
                    page_count=self.repository.count(),
                    new_count=len(self.new_pages),
                    updated_count=len(self.updated_pages),
                    deleted_count=len(self.deleted_pages),
                    duration_seconds=duration_seconds
                )
            else:
                self.stats['end_time'] = time.time()
            
            # 差分情報を作成
            diff_data = {
                'total': self.repository.count(),
                'new_pages': self.new_pages,
                'updated_pages': self.updated_pages,
                'deleted_pages': self.deleted_pages,
                'diffs': self.page_diffs,
                'has_changes': bool(self.new_pages or self.updated_pages or self.deleted_pages),
                'duration_seconds': int(self.stats['end_time'] - self.stats['start_time'])
            }
            
            # リポジトリを確定
            self.repository.finalize()
            
            logging.info(f"クロールが完了しました。訪問したURL数: {len(self.visited_urls)}、保存したページ数: {self.repository.count()}。")
            logging.info(f"変更点: 新規: {len(self.new_pages)}、更新: {len(self.updated_pages)}、削除: {len(self.deleted_pages)}。")
            
            return self.repository, diff_data
    
    async def _worker(self):
        """非同期ワーカープロセス"""
        while not self.stop_event.is_set():
            try:
                # キューが空の場合はクロール完了
                if self.queue.empty() and all(u in self.visited_urls for u in self.queued_urls):
                    break
                
                # タイムアウト付きでURLを取得（キューが空の場合に永遠に待機しないため）
                try:
                    url = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 既に訪問済みのURLならスキップ
                if url in self.visited_urls:
                    self.queue.task_done()
                    continue
                
                # セマフォーを使用して同時実行数を制限
                async with self.semaphore:
                    await self._process_url(url)
                
                # タスク完了通知
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"ワーカープロセスでエラー発生: {e}")
    
    async def _process_url(self, url):
        """URLを処理する"""
        try:
            # 訪問済みとしてマーク
            self.visited_urls.add(url)
            self.stats['processed_urls'] += 1

            # ビジュアルモードが有効かつライブラリが利用可能な場合
            if self.visual_mode and VISUAL_CRAWLING_AVAILABLE:
                # スレッドプールでビジュアルクローリングを実行
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(crawl_url_visual, url, self.visual_config)
                    page_data = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: future.result()
                    )

                if "error" in page_data:
                    logging.error(f"ビジュアルクローリングエラー {url}: {page_data['error']}")
                    self.stats['failed_fetches'] += 1
                    self.repository.add({'url': url, 'title': 'Error', 'html_content': ''}, status='error')
                    return

                # リンクはビジュアルモードでは抽出されないため空のリストを使用
                links = []

                logging.info(f"ビジュアルモードでページをクロール: {url}")

            else:
                # 通常のクローリングプロセス
                # キャッシュからページ情報を取得
                cached_page = None
                if self.cache and self.config.diff_detection:
                    cached_page = self.cache.get_page(url)

                # ページのHTMLを取得（条件付きリクエスト）
                etag = cached_page.get('etag') if cached_page else None
                last_modified = cached_page.get('last_modified') if cached_page else None

                html, headers_info = await self.fetcher.fetch_async(url, etag, last_modified)

                # 304 Not Modified の場合、キャッシュから前回のコンテンツを使用
                if headers_info.get('status_code') == 304 and cached_page:
                    logging.info(f"キャッシュされたコンテンツを使用: {url}")
                    page_data = {
                        'url': url,
                        'title': cached_page['title'],
                        'html_content': '', # HTMLは保存不要
                        'markdown_content': cached_page['markdown_content'],
                        'etag': cached_page['etag'],
                        'last_modified': cached_page['last_modified'],
                        'meta_description': cached_page.get('meta_description', '')
                    }
                    self.repository.add(page_data)
                    return

                # HTMLが取得できなかった場合はスキップ
                if html is None:
                    self.stats['skipped_urls'] += 1
                    self.repository.add({'url': url, 'title': 'Error', 'html_content': ''}, status='skipped')
                    return

                self.stats['successful_fetches'] += 1

                # HTMLを解析してコンテンツとリンクを抽出
                page_data, links = self.parser.parse(html, url)

                # コンテンツがない場合はスキップ
                if not page_data.get('html_content'):
                    self.stats['skipped_urls'] += 1
                    return

                # ヘッダー情報を追加
                page_data['etag'] = headers_info.get('etag')
                page_data['last_modified'] = headers_info.get('last_modified')

                # HTMLをMarkdownに変換
                page_data = self.markdown_converter.convert(page_data)

            # 差分検知（有効な場合）- ビジュアルモードでも共通
            if self.cache and self.config.diff_detection:
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

            # 新しいリンクをキューに追加（ビジュアルモードでは空のリストになる可能性がある）
            await self._add_new_links_to_queue(links)

        except Exception as e:
            logging.error(f"URL処理エラー {url}: {e}")
            self.stats['failed_fetches'] += 1
            self.repository.add({'url': url, 'title': 'Error', 'html_content': ''}, status='error')
    
    async def _add_new_links_to_queue(self, links):
        """新しいリンクをキューに追加する"""
        for link in links:
            # 訪問済みかキューに入っている場合はスキップ
            if link in self.visited_urls or link in self.queued_urls:
                continue
                
            # 最大ページ数に達していたらスキップ
            if len(self.visited_urls) + len(self.queued_urls) >= self.config.max_pages:
                break
                
            # キューに追加
            self.queued_urls.add(link)
            await self.queue.put(link)
    
    async def _log_progress(self):
        """現在の進捗を定期的にログに記録する"""
        try:
            while self.is_running:
                queue_size = self.queue.qsize()
                visited = len(self.visited_urls)
                total = visited + queue_size
                
                if total > 0:
                    progress = (visited / (visited + queue_size)) * 100
                    elapsed = time.time() - self.stats['start_time']
                    pages_per_second = visited / elapsed if elapsed > 0 else 0
                    
                    logging.info(f"進捗: {visited}/{total} ({progress:.1f}%) 完了 - 処理速度: {pages_per_second:.2f} ページ/秒")
                
                await asyncio.sleep(10)  # 10秒ごとに進捗を更新
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"進捗ロギングエラー: {e}")
    
    def stop(self):
        """クロールを停止する"""
        if self.is_running:
            self.stop_event.set()
            logging.info("クロールを停止中...")


def generate_sitemap(repository, output_dir, domain, url_blacklist=None):
    """サイトマップXMLを生成する"""
    from xml.dom import minidom
    import xml.etree.ElementTree as ET
    
    # XMLのルート要素とネームスペースを作成
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # 現在の日付
    today = datetime.now().strftime("%Y-%m-%d")
    
    # コンテンツを取得
    contents = repository.get_all()
    
    # 除外URLパターン（指定がなければ空のセット）
    url_blacklist = url_blacklist or set()
    
    # URLを追加
    for url, page_data in contents.items():
        # 除外URLパターンに一致するURLはスキップ
        skip = False
        for pattern in url_blacklist:
            if pattern in url:
                skip = True
                break
                
        if skip:
            continue
            
        url_element = ET.SubElement(root, "url")
        loc = ET.SubElement(url_element, "loc")
        loc.text = url
        
        lastmod = ET.SubElement(url_element, "lastmod")
        lastmod.text = today
        
        # 更新頻度の推測（パスの深さによって変更）
        path_depth = url.count('/') - 2  # http://domain.com/ の基本的な部分を除く
        
        changefreq = ET.SubElement(url_element, "changefreq")
        if path_depth <= 1:  # トップレベルページ
            changefreq.text = "daily"
        elif path_depth == 2:  # セカンドレベルページ
            changefreq.text = "weekly"
        else:  # 深いレベルのページ
            changefreq.text = "monthly"
        
        # 優先度の設定（パスの深さに応じて下げる）
        priority = ET.SubElement(url_element, "priority")
        if path_depth == 0:  # ホームページ
            priority.text = "1.0"
        else:
            priority_value = max(0.1, 1.0 - (path_depth * 0.2))
            priority.text = f"{priority_value:.1f}"
    
    # XMLをきれいにフォーマット
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    # ファイルに保存
    sitemap_path = os.path.join(output_dir, f"sitemap-{domain}.xml")
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(xmlstr)
        
    return sitemap_path


def run_colab_crawler(config):
    """Google Colab向けの改善されたクローラー実行関数"""
    from crawler_components import (
        UrlFilter, Fetcher, Parser, MarkdownConverter,
        ContentRepository, CrawlCache, FileExporter
    )

    # ビジュアルモードの確認
    visual_mode = getattr(config, 'visual_mode', False)
    if visual_mode:
        if not VISUAL_CRAWLING_AVAILABLE:
            logging.warning("ビジュアルクローリングモードが指定されましたが、必要な依存関係が不足しています。標準モードにフォールバックします。")
            config.visual_mode = False
        else:
            logging.info("ビジュアルクローリングモードが有効です。")

    # ロガーの設定
    log_file = os.path.join(config.output_dir, "crawler.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

    try:
        # 出力ディレクトリを作成
        os.makedirs(config.output_dir, exist_ok=True)

        # ドメイン名を取得
        domain = urlparse(config.base_url).netloc

        # 各コンポーネントの初期化
        url_filter = UrlFilter(config)
        fetcher = Fetcher(config)
        parser = Parser(url_filter)
        markdown_converter = MarkdownConverter()
        repository = ContentRepository()

        # 差分検知が有効な場合はキャッシュを初期化
        cache = CrawlCache(domain, config.cache_dir) if config.diff_detection else None

        # 非同期クローラーを初期化
        components = {
            'url_filter': url_filter,
            'fetcher': fetcher,
            'parser': parser,
            'markdown_converter': markdown_converter,
            'repository': repository,
            'cache': cache
        }

        crawler = AsyncCrawler(config, components)
        
        # クローラーを実行（非同期実行をイベントループで処理）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            repository, diff_data = loop.run_until_complete(crawler.crawl())
        finally:
            loop.close()
        
        # 結果がない場合はエラー
        if repository.count() == 0:
            logging.error("No content was crawled.")
            if config.discord_webhook:
                notifier = DiscordNotifier(config.discord_webhook)
                notifier.notify(
                    message=f"Webサイトのクロールが完了しましたが、コンテンツは取得できませんでした。\n**URL**: {config.base_url}",
                    title="クロール失敗",
                    color=0xff0000  # 赤色
                )
            return None, None, None
        
        # 変更がなく、スキップオプションが有効な場合はスキップ
        if config.skip_no_changes and not diff_data['has_changes'] and cache:
            logging.info("No changes detected. Skipping file generation and notification.")
            if config.discord_webhook:
                notifier = DiscordNotifier(config.discord_webhook)
                notifier.notify(
                    message=f"Webサイトのクロールが完了しましたが、前回から変更はありませんでした。\n**URL**: {config.base_url}\n**取得ページ数**: {repository.count()}",
                    title="変更なし",
                    color=0x3498db  # 青色
                )
            return None, None, None
        
        # Markdownファイル名の生成
        markdown_filename = f"{domain}.md"
        
        # Markdownファイルとして出力
        exporter = FileExporter(config.output_dir)
        markdown_path = exporter.export_markdown(repository, markdown_filename)
        logging.info(f"Exported Markdown to {markdown_path}")
        
        # 差分レポートを出力（差分検知が有効な場合）
        diff_report_path = None
        if config.diff_detection and diff_data['has_changes']:
            diff_report_filename = f"{domain}_diff_report.md"
            diff_report_path = exporter.export_diff_report(diff_data, diff_report_filename)
            logging.info(f"Exported diff report to {diff_report_path}")
        
        # 概要レポートを出力
        summary_filename = f"{domain}_summary.md"
        summary_path = exporter.export_summary(repository, diff_data, summary_filename)
        logging.info(f"Exported summary to {summary_path}")
        
        # PDFファイルとして出力
        pdf_converter = PdfConverter(config.output_dir)
        pdf_path = pdf_converter.convert(markdown_path, title=f"{domain} - クロール結果")
        if pdf_path:
            logging.info(f"Exported PDF to {pdf_path}")
        
        # 差分レポートのPDFを生成（差分がある場合）
        diff_report_pdf_path = None
        if diff_report_path:
            diff_report_pdf_path = pdf_converter.convert(diff_report_path, title=f"{domain} - 差分レポート")
            if diff_report_pdf_path:
                logging.info(f"Exported diff report PDF to {diff_report_pdf_path}")
                
        # サイトマップを生成
        try:
            sitemap_path = generate_sitemap(repository, config.output_dir, domain)
            logging.info(f"Generated sitemap at {sitemap_path}")
        except Exception as e:
            logging.error(f"Failed to generate sitemap: {e}")
            sitemap_path = None
        
        # Discord通知
        if config.discord_webhook:
            notifier = DiscordNotifier(config.discord_webhook)
            
            # 差分検知が有効かつ変更がある場合
            if config.diff_detection and diff_data['has_changes']:
                message = f"Webサイトのクロールが完了しました。**変更が検出されました**。\n"
                message += f"**URL**: {config.base_url}\n"
                message += f"**取得ページ数**: {diff_data['total']}\n"
                message += f"**新規ページ**: {len(diff_data['new_pages'])}\n"
                message += f"**更新ページ**: {len(diff_data['updated_pages'])}\n"
                message += f"**削除ページ**: {len(diff_data['deleted_pages'])}\n"
                
                # 所要時間があれば表示
                if 'duration_seconds' in diff_data:
                    minutes, seconds = divmod(diff_data['duration_seconds'], 60)
                    message += f"**所要時間**: {minutes}分{seconds}秒"
                
                # 差分レポートを添付
                success = notifier.notify(
                    message=message,
                    title=f"{domain} - クロール完了（変更あり）",
                    color=0x2ecc71,  # 緑色
                    markdown_path=diff_report_path,
                    pdf_path=diff_report_pdf_path or pdf_path,
                )
            else:
                # 変更がない場合または差分検知が無効の場合
                message = f"Webサイトのクロールが完了しました。\n**URL**: {config.base_url}\n**取得ページ数**: {repository.count()}"
                if 'duration_seconds' in diff_data:
                    minutes, seconds = divmod(diff_data['duration_seconds'], 60)
                    message += f"\n**所要時間**: {minutes}分{seconds}秒"
                    
                success = notifier.notify(
                    message=message,
                    title=f"{domain} - クロール完了",
                    color=0x3498db,  # 青色
                    markdown_path=markdown_path,
                    pdf_path=pdf_path,
                )
                
            if success:
                logging.info("Discord通知を送信しました")
            else:
                logging.error("Discord通知の送信に失敗しました")
        
        logging.info("処理が正常に完了しました")
        
        return markdown_path, pdf_path, diff_report_path
        
    except Exception as e:
        logging.error(f"実行中にエラーが発生しました: {e}", exc_info=True)
        if config.discord_webhook:
            notifier = DiscordNotifier(config.discord_webhook)
            notifier.notify(
                message=f"Webサイトのクロール中にエラーが発生しました。\n**URL**: {config.base_url}\n**エラー**: {str(e)}",
                title="クロールエラー",
                color=0xff0000  # 赤色
            )
        return None, None, None