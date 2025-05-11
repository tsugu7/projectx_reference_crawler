#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webサイトクローラーのメイン実行スクリプト
コマンドラインからクローラーを実行するためのエントリーポイント

使用方法:
    python crawler_script.py --url https://example.com [options]
    または
    python crawler_script.py --config config.json

オプション:
    -u, --url URL           クロールするWebサイトのURL
    -p, --pages NUM         クロールする最大ページ数 (デフォルト: 100)
    -d, --delay NUM         リクエスト間の遅延時間（秒）(デフォルト: 1.0)
    -w, --workers NUM       並列ワーカー数 (デフォルト: 5)
    -o, --output DIR        出力ディレクトリ (デフォルト: "output")
    -c, --cache DIR         キャッシュディレクトリ (デフォルト: "cache")
    --discord URL           Discord Webhook URL
    --no-diff               差分検知を無効化
    --force                 変更がなくても出力を生成
    --no-normalize          URL正規化を無効化
    --ignore-robots         robots.txtを無視
    --config FILE           設定JSONファイル
"""

import os
import sys
import json
import argparse
import logging
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta

# クローラーコンポーネントが同じディレクトリにある場合にインポート
try:
    from crawler_components import CrawlerConfig
    from crawler_advanced import run_colab_crawler
except ImportError:
    # 実行ディレクトリをモジュール検索パスに追加
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    try:
        from crawler_components import CrawlerConfig
        from crawler_advanced import run_colab_crawler
    except ImportError:
        print("Error: クローラーコンポーネントが見つかりません。")
        sys.exit(1)


def setup_logging(output_dir):
    """ロギングの設定"""
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "crawler.log")
    
    # ロガーの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    
    return log_file


def parse_args():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(
        description="Webサイトクローラー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # 基本オプション
    parser.add_argument("-u", "--url", help="クロールするWebサイトのURL")
    parser.add_argument("-p", "--pages", type=int, default=100, help="クロールする最大ページ数")
    parser.add_argument("-d", "--delay", type=float, default=1.0, help="リクエスト間の遅延時間（秒）")
    parser.add_argument("-w", "--workers", type=int, default=5, help="並列ワーカー数")
    parser.add_argument("-o", "--output", default="output", help="出力ディレクトリ")
    parser.add_argument("-c", "--cache", default="cache", help="キャッシュディレクトリ")
    
    # Discord連携
    parser.add_argument("--discord", help="Discord Webhook URL")
    
    # 動作オプション
    parser.add_argument("--no-diff", action="store_true", help="差分検知を無効化")
    parser.add_argument("--force", action="store_true", help="変更がなくても出力を生成")
    parser.add_argument("--no-normalize", action="store_true", help="URL正規化を無効化")
    parser.add_argument("--ignore-robots", action="store_true", help="robots.txtを無視")
    
    # 設定ファイル
    parser.add_argument("--config", help="設定JSONファイル")
    
    args = parser.parse_args()
    
    # 設定ファイルか直接指定のURLのどちらかは必須
    if not args.config and not args.url:
        parser.error("--url または --config のどちらかを指定してください。")
    
    return args


def load_config_from_file(config_file):
    """設定ファイルから設定を読み込む"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
            
        # メタ情報を除去
        for key in list(config_dict.keys()):
            if key.startswith('_'):
                del config_dict[key]
                
        # static_extensionsをセットに変換
        if 'static_extensions' in config_dict and isinstance(config_dict['static_extensions'], list):
            config_dict['static_extensions'] = set(config_dict['static_extensions'])
            
        config = CrawlerConfig.from_dict(config_dict)
        print(f"設定ファイルを読み込みました: {config_file}")
        
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)


def config_from_args(args):
    """コマンドライン引数から設定を作成"""
    config = CrawlerConfig(
        base_url=args.url,
        max_pages=args.pages,
        delay=args.delay,
        max_workers=args.workers,
        output_dir=args.output,
        cache_dir=args.cache,
        discord_webhook=args.discord,
        diff_detection=not args.no_diff,
        skip_no_changes=not args.force,
        normalize_urls=not args.no_normalize,
        respect_robots_txt=not args.ignore_robots
    )
    
    return config


def print_summary(start_time, markdown_path, pdf_path, diff_path, has_changes=None):
    """実行サマリーを表示"""
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("クロール実行サマリー")
    print("=" * 60)
    print(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"終了時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"所要時間: {duration}")
    
    print("\n結果:")
    if markdown_path:
        print(f"✓ Markdownファイル: {markdown_path}")
        
    if pdf_path:
        print(f"✓ PDFファイル: {pdf_path}")
        
    if diff_path:
        print(f"✓ 差分レポート: {diff_path}")
        
    if has_changes is not None:
        if has_changes:
            print("\n変更状態: 変更が検出されました")
        else:
            print("\n変更状態: 変更はありません")
            
    print("=" * 60)


def main():
    """メイン実行関数"""
    # 引数の解析
    args = parse_args()
    
    # 設定を読み込む
    if args.config:
        config = load_config_from_file(args.config)
    else:
        config = config_from_args(args)
    
    # URL検証
    if not config.base_url:
        print("Error: クロールするURLが指定されていません。")
        sys.exit(1)
    
    # 出力ディレクトリの作成
    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(config.cache_dir, exist_ok=True)
    
    # ロギングの設定
    log_file = setup_logging(config.output_dir)
    
    # クロール開始
    start_time = datetime.now()
    print(f"\nクロールを開始します: {config.base_url}")
    print(f"実行時刻: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"最大ページ数: {config.max_pages}、遅延時間: {config.delay}秒、並列数: {config.max_workers}")
    print(f"出力先: {config.output_dir}")
    
    try:
        # カスタム設定情報を保存
        config_path = os.path.join(config.output_dir, "crawler_config_used.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            config_dict = config.to_dict()
            # static_extensionsをJSONシリアライズ可能なリストに変換
            if 'static_extensions' in config_dict:
                config_dict['static_extensions'] = list(config_dict['static_extensions'])
            # 実行情報を追加    
            config_dict['_execution_time'] = start_time.isoformat()
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        # クローラーを実行
        markdown_path, pdf_path, diff_path = run_colab_crawler(config)
        
        # 結果の処理
        has_changes = diff_path is not None
        
        if markdown_path:
            print_summary(start_time, markdown_path, pdf_path, diff_path, has_changes)
            return 0
        else:
            print("\nエラーが発生したか、クロールをスキップしました。ログファイルを確認してください。")
            print(f"ログファイル: {log_file}")
            return 1
            
    except KeyboardInterrupt:
        print("\nユーザーによって中断されました。")
        return 130
    except Exception as e:
        print(f"\n実行中にエラーが発生しました: {e}")
        logging.error(f"実行エラー: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())