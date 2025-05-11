#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webサイトクローラーの応用例スクリプト
様々なユースケース向けの実装例を提供

使用方法:
    python crawler_use_cases.py [use_case] [url]

ユースケース:
    monitor  - サイトの変更を監視し、変更があった場合のみ通知
    archive  - サイト全体をアーカイブ
    sitemap  - サイトマップの生成
    blog     - ブログやニュースサイト専用設定
    docs     - ドキュメントサイト向け設定

例:
    python crawler_use_cases.py monitor https://example.com
"""

import os
import sys
import argparse
import logging
import json
import asyncio
from datetime import datetime
from urllib.parse import urlparse

# クローラーコンポーネントが同じディレクトリにある場合にインポート
try:
    from crawler_components import CrawlerConfig
    from crawler_advanced import run_colab_crawler, generate_sitemap
except ImportError:
    # 実行ディレクトリをモジュール検索パスに追加
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    try:
        from crawler_components import CrawlerConfig
        from crawler_advanced import run_colab_crawler, generate_sitemap
    except ImportError:
        print("Error: クローラーコンポーネントが見つかりません。")
        sys.exit(1)


def setup_logging(output_dir="logs"):
    """ロギング設定"""
    os.makedirs(output_dir, exist_ok=True)
    
    log_file = os.path.join(output_dir, f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    
    return log_file


def get_config_for_use_case(use_case, url):
    """ユースケースに応じた設定を生成"""
    base_config = {
        "base_url": url,
        "output_dir": "output",
        "cache_dir": "cache"
    }
    
    # ユースケース別の設定
    configs = {
        # 監視用（変更検知に最適化）
        "monitor": {
            "max_pages": 500,
            "delay": 1.0,
            "max_workers": 5,
            "diff_detection": True,
            "skip_no_changes": True,
            "normalize_urls": True,
            "respect_robots_txt": True
        },
        
        # アーカイブ用（大規模サイト向け）
        "archive": {
            "max_pages": 2000,
            "delay": 2.0,
            "max_workers": 3,
            "diff_detection": False,
            "skip_no_changes": False,
            "normalize_urls": True,
            "respect_robots_txt": True
        },
        
        # サイトマップ生成用（最小構成）
        "sitemap": {
            "max_pages": 1000,
            "delay": 1.0,
            "max_workers": 5,
            "diff_detection": False,
            "skip_no_changes": False,
            "normalize_urls": True,
            "respect_robots_txt": True
        },
        
        # ブログ専用（記事に最適化）
        "blog": {
            "max_pages": 200,
            "delay": 1.0,
            "max_workers": 5,
            "diff_detection": True,
            "skip_no_changes": True,
            "normalize_urls": True,
            "respect_robots_txt": True,
            # ブログ専用の除外パターン
            "static_extensions": {
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.css',
                '.js', '.pdf', '.zip', '.tar', '.gz', '.mp3',
                '.mp4', '.avi', '.mov', '.webm', '.webp', '.ico',
                '.woff', '.woff2', '.eot', '.ttf'
            }
        },
        
        # ドキュメントサイト向け
        "docs": {
            "max_pages": 500,
            "delay": 1.0,
            "max_workers": 5,
            "diff_detection": True,
            "skip_no_changes": False,
            "normalize_urls": True,
            "respect_robots_txt": True,
            # PDFなどのドキュメントも含める
            "static_extensions": {
                '.jpg', '.jpeg', '.png', '.gif', '.svg', '.css',
                '.js', '.zip', '.tar', '.gz', '.mp3',
                '.mp4', '.avi', '.mov', '.webm', '.webp', '.ico',
                '.woff', '.woff2', '.eot', '.ttf'
            }
        }
    }
    
    # 存在しないユースケースの場合はエラー
    if use_case not in configs:
        valid_cases = ", ".join(configs.keys())
        print(f"Error: 無効なユースケースです。有効なユースケース: {valid_cases}")
        sys.exit(1)
        
    # 設定をマージ
    merged_config = {**base_config, **configs[use_case]}
    
    # 出力ディレクトリをカスタマイズ（ドメイン名とユースケースを含める）
    domain = urlparse(url).netloc
    output_dir = os.path.join("output", f"{domain}_{use_case}")
    cache_dir = os.path.join("cache", domain)
    
    merged_config["output_dir"] = output_dir
    merged_config["cache_dir"] = cache_dir
    
    return CrawlerConfig.from_dict(merged_config)


def monitoring_use_case(url):
    """監視ユースケース: サイトの変更を監視し、変更があった場合のみ通知"""
    print(f"Webサイト監視モードを開始: {url}")
    
    # 専用ディレクトリを作成
    log_file = setup_logging("logs/monitor")
    
    # 監視用の設定
    config = get_config_for_use_case("monitor", url)
    
    # Discordの設定（オプション）
    discord_webhook = os.environ.get("DISCORD_WEBHOOK")
    if discord_webhook:
        config.discord_webhook = discord_webhook
        
    # 実行
    markdown_path, pdf_path, diff_path = run_colab_crawler(config)
    
    # 結果の処理
    if diff_path:
        print(f"\n変更が検出されました。詳細なレポート: {diff_path}")
        return True
    elif markdown_path:
        print(f"\n変更は検出されませんでした。最新コンテンツ: {markdown_path}")
        return False
    else:
        print("\nエラーが発生したか、クロールをスキップしました。ログを確認してください。")
        return False


def archive_use_case(url):
    """アーカイブユースケース: サイト全体を可能な限りアーカイブ"""
    print(f"Webサイトアーカイブモードを開始: {url}")
    
    # 専用ディレクトリを作成
    log_file = setup_logging("logs/archive")
    
    # アーカイブ用の設定
    config = get_config_for_use_case("archive", url)
    
    # 特定のアーカイブ設定を追加
    archive_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    domain = urlparse(url).netloc
    archive_dir = os.path.join(config.output_dir, f"archive_{archive_time}")
    os.makedirs(archive_dir, exist_ok=True)
    
    config.output_dir = archive_dir
    config.skip_no_changes = False  # 常に出力を生成
    
    # 実行
    markdown_path, pdf_path, diff_path = run_colab_crawler(config)
    
    # 結果の処理
    if markdown_path:
        print(f"\nアーカイブが完了しました: {archive_dir}")
        
        # アーカイブメタデータの保存
        metadata = {
            "url": url,
            "archive_time": archive_time,
            "pages": None,  # ここでは不明
            "generated_files": [
                os.path.basename(p) for p in [markdown_path, pdf_path, diff_path] if p
            ]
        }
        
        with open(os.path.join(archive_dir, "archive_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return True
    else:
        print("\nアーカイブに失敗しました。ログを確認してください。")
        return False


def sitemap_use_case(url):
    """サイトマップ生成ユースケース: XMLサイトマップを生成"""
    print(f"サイトマップ生成モードを開始: {url}")
    
    # 専用ディレクトリを作成
    log_file = setup_logging("logs/sitemap")
    
    # サイトマップ用の設定
    config = get_config_for_use_case("sitemap", url)
    
    # 特定のサイトマップ設定を追加
    config.diff_detection = False  # 差分検知は不要
    
    try:
        # 実行
        from crawler_components import UrlFilter, Fetcher, Parser, MarkdownConverter, ContentRepository
        from crawler_advanced import AsyncCrawler
        
        # 必要なコンポーネントの初期化
        url_filter = UrlFilter(config)
        fetcher = Fetcher(config)
        parser = Parser(url_filter)
        markdown_converter = MarkdownConverter()
        repository = ContentRepository()
        
        # コンポーネントを準備
        components = {
            'url_filter': url_filter,
            'fetcher': fetcher,
            'parser': parser,
            'markdown_converter': markdown_converter,
            'repository': repository
        }
        
        # 非同期クローラーを初期化
        crawler = AsyncCrawler(config, components)
        
        # クローラーを実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            repository, diff_data = loop.run_until_complete(crawler.crawl())
        finally:
            loop.close()
            
        # サイトマップ生成
        domain = urlparse(url).netloc
        os.makedirs(config.output_dir, exist_ok=True)
        
        # インデックス除外パターン
        url_blacklist = [
            '/tag/', '/category/', '/page/', '/wp-content/',
            '/feed/', '/comments/', '/trackback/', '/cgi-bin/',
            '?s=', '?p=', '&p=', '?replytocom='
        ]
        
        sitemap_path = generate_sitemap(repository, config.output_dir, domain, url_blacklist)
        
        if sitemap_path and os.path.exists(sitemap_path):
            print(f"\nサイトマップが生成されました: {sitemap_path}")
            
            # 生成されたサイトマップの簡易統計
            with open(sitemap_path, 'r', encoding='utf-8') as f:
                content = f.read()
                url_count = content.count('<url>')
                
            print(f"サイトマップには {url_count} ページが含まれています。")
            return True
        else:
            print("\nサイトマップ生成に失敗しました。")
            return False
            
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        logging.error(f"サイトマップ生成エラー: {e}", exc_info=True)
        return False


def blog_use_case(url):
    """ブログユースケース: ブログやニュースサイト向けの特別設定"""
    print(f"ブログ・ニュース専用モードを開始: {url}")
    
    # 専用ディレクトリを作成
    log_file = setup_logging("logs/blog")
    
    # ブログ用の設定
    config = get_config_for_use_case("blog", url)
    
    # ブログ向けの特別な処理を追加
    domain = urlparse(url).netloc
    
    # 実行
    markdown_path, pdf_path, diff_path = run_colab_crawler(config)
    
    # 新しい記事リストを生成（差分レポートから）
    if diff_path and os.path.exists(diff_path):
        with open(diff_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()
            
        # 新しい記事を抽出
        new_articles = []
        in_new_pages_section = False
        
        for line in diff_content.split('\n'):
            if line.startswith('## 新規ページ'):
                in_new_pages_section = True
                continue
            elif line.startswith('##'):
                in_new_pages_section = False
                
            if in_new_pages_section and line.startswith('- ['):
                # Markdown形式のリンクを解析
                parts = line.split('](')
                if len(parts) == 2:
                    title = parts[0][3:]  # '- [' を削除
                    url = parts[1][:-1]  # 閉じ括弧を削除
                    new_articles.append({"title": title, "url": url})
        
        # 新しい記事リストを保存
        if new_articles:
            new_articles_path = os.path.join(config.output_dir, f"{domain}_new_articles.json")
            with open(new_articles_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "date": datetime.now().isoformat(),
                    "articles": new_articles
                }, f, indent=2, ensure_ascii=False)
                
            print(f"\n新しい記事が {len(new_articles)} 件見つかりました。リスト: {new_articles_path}")
            
        return True
    elif markdown_path:
        print(f"\n処理は完了しましたが、新しい記事は見つかりませんでした。")
        return True
    else:
        print("\nエラーが発生したか、クロールをスキップしました。ログを確認してください。")
        return False


def docs_use_case(url):
    """ドキュメントユースケース: ドキュメントサイト向けの特別設定"""
    print(f"ドキュメントサイト専用モードを開始: {url}")
    
    # 専用ディレクトリを作成
    log_file = setup_logging("logs/docs")
    
    # ドキュメント用の設定
    config = get_config_for_use_case("docs", url)
    
    # ドキュメント向けの特別な処理を追加
    domain = urlparse(url).netloc
    
    # 実行
    markdown_path, pdf_path, diff_path = run_colab_crawler(config)
    
    # ドキュメント検索インデックスの生成
    if markdown_path and os.path.exists(markdown_path):
        try:
            # 簡易的な検索インデックスを作成
            index = []
            current_section = {"title": "", "content": "", "url": ""}
            
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line in content.split('\n'):
                # 新しいセクション（ページ）の開始
                if line.startswith('# '):
                    # 前のセクションを保存（存在する場合）
                    if current_section["title"]:
                        index.append(current_section)
                        
                    # 新しいセクションを開始
                    current_section = {
                        "title": line[2:],  # '# ' を削除
                        "content": "",
                        "url": ""
                    }
                
                # URLを抽出
                elif line.startswith('*Source:') and 'http' in line:
                    url_start = line.find('http')
                    url_end = line.find('*', url_start)
                    if url_end == -1:
                        url_end = len(line)
                        
                    current_section["url"] = line[url_start:url_end]
                
                # コンテンツを追加
                elif current_section["title"] and not line.startswith('#') and not line.startswith('*Source:'):
                    current_section["content"] += line + " "
                    
            # 最後のセクションを保存
            if current_section["title"]:
                index.append(current_section)
                
            # インデックスを保存
            index_path = os.path.join(config.output_dir, f"{domain}_search_index.json")
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "date": datetime.now().isoformat(),
                    "pages": index
                }, f, indent=2, ensure_ascii=False)
                
            print(f"\n検索インデックスが作成されました（{len(index)} ページ）: {index_path}")
            
            return True
        except Exception as e:
            print(f"\n検索インデックス作成中にエラーが発生しました: {e}")
            logging.error(f"検索インデックス作成エラー: {e}", exc_info=True)
            return False
    elif markdown_path:
        print(f"\nマークダウンは生成されましたが、検索インデックスの作成に失敗しました。")
        return True
    else:
        print("\nエラーが発生したか、クロールをスキップしました。ログを確認してください。")
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Webサイトクローラー応用例スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("use_case", choices=["monitor", "archive", "sitemap", "blog", "docs"],
                       help="実行するユースケース")
    parser.add_argument("url", help="クロールするWebサイトのURL")
    parser.add_argument("-o", "--output", help="出力ディレクトリ（省略時はデフォルト）")
    parser.add_argument("-d", "--discord", help="Discord Webhook URL")
    
    args = parser.parse_args()
    
    # Discordの環境変数設定
    if args.discord:
        os.environ["DISCORD_WEBHOOK"] = args.discord
    
    # ユースケースに応じた実行
    use_case_functions = {
        "monitor": monitoring_use_case,
        "archive": archive_use_case,
        "sitemap": sitemap_use_case,
        "blog": blog_use_case,
        "docs": docs_use_case
    }
    
    try:
        success = use_case_functions[args.use_case](args.url)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nユーザーによって中断されました。")
        sys.exit(130)
    except Exception as e:
        print(f"\n実行中にエラーが発生しました: {e}")
        logging.error(f"実行エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()