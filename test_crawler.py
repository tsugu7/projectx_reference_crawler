#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webサイトクローラーのテストスイート
主要機能の単体テストを実行します
"""

import os
import sys
import unittest
import tempfile
import shutil
import hashlib
from urllib.parse import urlparse

# テスト用にパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# クローラーコンポーネントをインポート
from crawler_components import (
    CrawlerConfig, 
    UrlFilter, 
    Fetcher, 
    Parser,
    MarkdownConverter,
    ContentRepository,
    CrawlCache,
    FileExporter
)


class TestCrawlerConfig(unittest.TestCase):
    """CrawlerConfig クラスのテスト"""
    
    def test_config_creation(self):
        """設定オブジェクトの作成をテスト"""
        config = CrawlerConfig(base_url="https://example.com")
        self.assertEqual(config.base_url, "https://example.com")
        self.assertEqual(config.max_pages, 100)  # デフォルト値
        
    def test_config_from_dict(self):
        """辞書からの設定オブジェクト作成をテスト"""
        config_dict = {
            "base_url": "https://example.org",
            "max_pages": 50,
            "delay": 2.0,
            "invalid_key": "value"  # 無視されるべき
        }
        config = CrawlerConfig.from_dict(config_dict)
        self.assertEqual(config.base_url, "https://example.org")
        self.assertEqual(config.max_pages, 50)
        self.assertEqual(config.delay, 2.0)
        self.assertFalse(hasattr(config, "invalid_key"))
        
    def test_config_to_dict(self):
        """設定オブジェクトから辞書への変換をテスト"""
        config = CrawlerConfig(
            base_url="https://example.net",
            max_pages=200,
            discord_webhook="https://discord.com/api/webhooks/test"
        )
        config_dict = config.to_dict()
        self.assertEqual(config_dict["base_url"], "https://example.net")
        self.assertEqual(config_dict["max_pages"], 200)
        self.assertEqual(config_dict["discord_webhook"], "https://discord.com/api/webhooks/test")


class TestUrlFilter(unittest.TestCase):
    """UrlFilter クラスのテスト"""
    
    def setUp(self):
        """テスト用のフィルタを準備"""
        config = CrawlerConfig(base_url="https://example.com")
        self.url_filter = UrlFilter(config)
        
    def test_normalize_url(self):
        """URL正規化のテスト"""
        # 相対URLの変換
        self.assertEqual(
            self.url_filter.normalize_url("/path/to/page"),
            "https://example.com/path/to/page"
        )
        
        # フラグメントの削除
        self.assertEqual(
            self.url_filter.normalize_url("https://example.com/page#section"),
            "https://example.com/page"
        )
        
        # トレーリングスラッシュの統一
        self.assertEqual(
            self.url_filter.normalize_url("https://example.com/page/"),
            "https://example.com/page"
        )
        
    def test_should_crawl(self):
        """クロール判定のテスト"""
        # 同一ドメインのURL
        self.assertTrue(self.url_filter.should_crawl("https://example.com/page"))
        
        # 異なるドメインのURL
        self.assertFalse(self.url_filter.should_crawl("https://example.org/page"))
        
        # 静的ファイル
        self.assertFalse(self.url_filter.should_crawl("https://example.com/image.jpg"))
        
        # メールリンク
        self.assertFalse(self.url_filter.should_crawl("mailto:test@example.com"))
        
        # 除外パターン（wp-admin）
        self.assertFalse(self.url_filter.should_crawl("https://example.com/wp-admin/settings"))


class TestFetcher(unittest.TestCase):
    """Fetcher クラスのテスト"""
    
    def setUp(self):
        """テスト用のフェッチャーを準備"""
        config = CrawlerConfig(base_url="https://example.com", delay=0.1, timeout=5)
        self.fetcher = Fetcher(config)
        
    def test_fetch_valid_url(self):
        """有効なURLからのコンテンツ取得テスト"""
        html, headers = self.fetcher.fetch("https://httpbin.org/html")
        self.assertIsNotNone(html)
        self.assertIn("<html", html)
        self.assertEqual(headers["status_code"], 200)
        
    def test_fetch_not_found(self):
        """存在しないURLのテスト"""
        html, headers = self.fetcher.fetch("https://httpbin.org/status/404")
        self.assertIsNone(html)
        self.assertEqual(headers["status_code"], 404)
        
    def test_fetch_non_html(self):
        """HTMLでないコンテンツのテスト"""
        html, headers = self.fetcher.fetch("https://httpbin.org/json")
        self.assertIsNone(html)
        self.assertIn("content_type", headers)


class TestMarkdownConverter(unittest.TestCase):
    """MarkdownConverter クラスのテスト"""
    
    def setUp(self):
        """テスト用のコンバーターを準備"""
        self.converter = MarkdownConverter()
        
    def test_convert_html_to_markdown(self):
        """HTMLからMarkdownへの変換テスト"""
        page_data = {
            "url": "https://example.com/page",
            "title": "Test Page",
            "html_content": "<h1>Hello</h1><p>This is a <strong>test</strong>.</p>"
        }
        
        result = self.converter.convert(page_data)
        
        self.assertIn("markdown_content", result)
        self.assertIn("# Test Page", result["markdown_content"])
        self.assertIn("# Hello", result["markdown_content"])
        self.assertIn("This is a **test**.", result["markdown_content"])


class TestContentRepository(unittest.TestCase):
    """ContentRepository クラスのテスト"""
    
    def setUp(self):
        """テスト用のリポジトリを準備"""
        self.repository = ContentRepository()
        
    def test_add_and_get(self):
        """コンテンツの追加と取得テスト"""
        page_data = {
            "url": "https://example.com/page1",
            "title": "Test Page 1",
            "content": "Test content"
        }
        
        self.repository.add(page_data)
        
        # 取得
        retrieved = self.repository.get("https://example.com/page1")
        self.assertEqual(retrieved["title"], "Test Page 1")
        
        # 存在しないURLの取得
        self.assertIsNone(self.repository.get("https://example.com/nonexistent"))
        
    def test_count_and_get_all(self):
        """カウントと全取得のテスト"""
        page1 = {"url": "https://example.com/page1", "title": "Page 1"}
        page2 = {"url": "https://example.com/page2", "title": "Page 2"}
        
        self.repository.add(page1)
        self.repository.add(page2)
        
        self.assertEqual(self.repository.count(), 2)
        all_content = self.repository.get_all()
        self.assertEqual(len(all_content), 2)
        self.assertIn("https://example.com/page1", all_content)
        self.assertIn("https://example.com/page2", all_content)


class TestCrawlCache(unittest.TestCase):
    """CrawlCache クラスのテスト"""
    
    def setUp(self):
        """テスト用のキャッシュを準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CrawlCache("example.com", self.temp_dir)
        
    def tearDown(self):
        """テスト後の後片付け"""
        shutil.rmtree(self.temp_dir)
        
    def test_add_or_update_page(self):
        """ページの追加・更新テスト"""
        page_data = {
            "url": "https://example.com/page",
            "title": "Test Page",
            "markdown_content": "# Test\nThis is a test page."
        }
        
        # 新規追加
        is_update = self.cache.add_or_update_page(page_data)
        self.assertFalse(is_update)
        
        # 更新
        is_update = self.cache.add_or_update_page(page_data)
        self.assertTrue(is_update)
        
    def test_get_page(self):
        """ページ取得テスト"""
        page_data = {
            "url": "https://example.com/gettest",
            "title": "Get Test",
            "markdown_content": "Get test content"
        }
        
        self.cache.add_or_update_page(page_data)
        
        retrieved = self.cache.get_page("https://example.com/gettest")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["title"], "Get Test")
        
    def test_is_content_changed(self):
        """コンテンツ変更検出テスト"""
        url = "https://example.com/changetest"
        
        # 初期コンテンツ
        page_data = {
            "url": url,
            "title": "Change Test",
            "markdown_content": "Initial content"
        }
        self.cache.add_or_update_page(page_data)
        
        # 同じコンテンツで変更なし
        self.assertFalse(self.cache.is_content_changed(url, "Initial content"))
        
        # 異なるコンテンツで変更あり
        self.assertTrue(self.cache.is_content_changed(url, "Changed content"))


class TestFileExporter(unittest.TestCase):
    """FileExporter クラスのテスト"""
    
    def setUp(self):
        """テスト用のエクスポーターを準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = FileExporter(self.temp_dir)
        self.repository = ContentRepository()
        
        # テスト用のコンテンツを追加
        page1 = {
            "url": "https://example.com/page1",
            "title": "Page 1",
            "markdown_content": "# Page 1\nContent of page 1."
        }
        page2 = {
            "url": "https://example.com/page2",
            "title": "Page 2",
            "markdown_content": "# Page 2\nContent of page 2."
        }
        
        self.repository.add(page1)
        self.repository.add(page2)
        
    def tearDown(self):
        """テスト後の後片付け"""
        shutil.rmtree(self.temp_dir)
        
    def test_export_markdown(self):
        """Markdownエクスポートのテスト"""
        output_path = self.exporter.export_markdown(self.repository, "test_export.md")
        
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("# Page 1", content)
        self.assertIn("# Page 2", content)
        
    def test_export_diff_report(self):
        """差分レポートエクスポートのテスト"""
        diff_data = {
            "total": 10,
            "new_pages": ["https://example.com/new1", "https://example.com/new2"],
            "updated_pages": ["https://example.com/update1"],
            "deleted_pages": ["https://example.com/delete1", "https://example.com/delete2"],
            "diffs": {
                "https://example.com/update1": "--- old\n+++ new\n@@ -1,1 +1,1 @@\n-Old content\n+New content"
            }
        }
        
        output_path = self.exporter.export_diff_report(diff_data, "test_diff.md")
        
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("新規ページ", content)
        self.assertIn("https://example.com/new1", content)
        self.assertIn("更新ページ", content)
        self.assertIn("https://example.com/update1", content)
        self.assertIn("削除ページ", content)
        self.assertIn("https://example.com/delete1", content)


if __name__ == "__main__":
    unittest.main()