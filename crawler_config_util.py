#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webサイトクローラーの設定ユーティリティ
対話式の設定ツールとJSONエクスポート機能を提供
"""

import os
import sys
import json
import argparse
import readline
from urllib.parse import urlparse
from dataclasses import asdict
import datetime

# クローラーコンポーネントが同じディレクトリにある場合にインポート
try:
    from crawler_components import CrawlerConfig
except ImportError:
    # 実行ディレクトリをモジュール検索パスに追加
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    try:
        from crawler_components import CrawlerConfig
    except ImportError:
        print("Error: crawler_components.py が見つかりません。")
        sys.exit(1)


class ConfigWizard:
    """対話式設定ウィザード"""
    
    def __init__(self):
        self.config = {}
        self.prompts = {
            'base_url': {
                'message': 'クロールするWebサイトのURL: ',
                'validator': self._validate_url
            },
            'max_pages': {
                'message': 'クロールする最大ページ数 [100]: ',
                'default': 100,
                'validator': self._validate_positive_int
            },
            'delay': {
                'message': 'リクエスト間の遅延時間（秒） [1.0]: ',
                'default': 1.0,
                'validator': self._validate_positive_float
            },
            'max_workers': {
                'message': '並列ワーカー数 [5]: ',
                'default': 5,
                'validator': self._validate_positive_int
            },
            'output_dir': {
                'message': '出力ディレクトリ [output]: ',
                'default': 'output',
                'validator': self._validate_path
            },
            'cache_dir': {
                'message': 'キャッシュディレクトリ [cache]: ',
                'default': 'cache',
                'validator': self._validate_path
            },
            'discord_webhook': {
                'message': 'Discord Webhook URL (オプション): ',
                'default': None,
                'validator': self._validate_webhook_url
            }
        }
        
        self.boolean_options = [
            {'name': 'diff_detection', 'message': '差分検知を有効にする', 'default': True},
            {'name': 'skip_no_changes', 'message': '変更がない場合はスキップする', 'default': True},
            {'name': 'normalize_urls', 'message': 'URLの正規化を有効にする', 'default': True},
            {'name': 'respect_robots_txt', 'message': 'robots.txtを尊重する', 'default': True},
            {'name': 'follow_redirects', 'message': 'リダイレクトを追跡する', 'default': True},
        ]
    
    def run(self):
        """ウィザードを実行して設定を収集"""
        print("\n===== Webサイトクローラー設定ウィザード =====\n")
        print("基本設定を入力してください。デフォルト値を使用する場合は空欄のままEnterを押してください。\n")
        
        # 基本設定
        for key, options in self.prompts.items():
            message = options['message']
            default = options.get('default')
            validator = options['validator']
            
            while True:
                value = input(message)
                
                # デフォルト値の使用
                if value == '' and default is not None:
                    value = default
                    break
                
                # 値の検証
                try:
                    value = validator(value)
                    break
                except ValueError as e:
                    print(f"エラー: {e}")
            
            self.config[key] = value
        
        print("\n詳細設定（Y/nで選択）:\n")
        
        # 真偽値オプション
        for option in self.boolean_options:
            name = option['name']
            message = option['message']
            default = option['default']
            
            default_str = "Y" if default else "n"
            while True:
                value = input(f"{message} [{default_str}]: ")
                if value == '':
                    value = default
                    break
                elif value.lower() in ('y', 'yes'):
                    value = True
                    break
                elif value.lower() in ('n', 'no'):
                    value = False
                    break
                else:
                    print("エラー: Y/n で入力してください。")
            
            self.config[name] = value
        
        # 設定オブジェクトの作成
        try:
            self.crawler_config = CrawlerConfig.from_dict(self.config)
            print("\n設定が正常に作成されました。")
            return self.crawler_config
        except Exception as e:
            print(f"\nエラー: 設定の作成に失敗しました: {e}")
            return None
    
    def _validate_url(self, value):
        """URLの検証"""
        if not value:
            raise ValueError("URLは必須です。")
            
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("有効なURLを指定してください (例: https://example.com)")
            
        return value
    
    def _validate_positive_int(self, value):
        """正の整数の検証"""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError("0より大きい値を指定してください。")
            return int_value
        except ValueError:
            raise ValueError("有効な整数を入力してください。")
    
    def _validate_positive_float(self, value):
        """正の浮動小数点数の検証"""
        try:
            float_value = float(value)
            if float_value <= 0:
                raise ValueError("0より大きい値を指定してください。")
            return float_value
        except ValueError:
            raise ValueError("有効な数値を入力してください。")
    
    def _validate_path(self, value):
        """パスの検証"""
        # 簡易的な検証のみ
        return value
    
    def _validate_webhook_url(self, value):
        """Discord Webhook URLの検証"""
        if not value:
            return None
            
        if not value.startswith("https://discord.com/api/webhooks/"):
            print("警告: Discord WebhookのURLが標準的な形式ではありません。")
            
        return value


def save_config(config, filename):
    """設定をJSONファイルに保存"""
    config_dir = os.path.dirname(filename)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir)
        
    with open(filename, 'w', encoding='utf-8') as f:
        # データクラス→辞書に変換
        config_dict = config.to_dict()
        # static_extensionsをリストに変換（JSONシリアライズ可能にするため）
        if 'static_extensions' in config_dict:
            config_dict['static_extensions'] = list(config_dict['static_extensions'])
            
        # 追加情報
        config_dict['_created'] = datetime.datetime.now().isoformat()
        config_dict['_version'] = '1.0'
        
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
    print(f"設定をファイルに保存しました: {filename}")


def load_config(filename):
    """JSONファイルから設定を読み込み"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
            
        # メタ情報を除去
        for key in list(config_dict.keys()):
            if key.startswith('_'):
                del config_dict[key]
                
        # static_extensionsをセットに変換
        if 'static_extensions' in config_dict and isinstance(config_dict['static_extensions'], list):
            config_dict['static_extensions'] = set(config_dict['static_extensions'])
            
        return CrawlerConfig.from_dict(config_dict)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        return None


def print_config(config):
    """設定内容を表示"""
    if not config:
        print("設定が読み込まれていません。")
        return
        
    print("\n===== クローラー設定 =====\n")
    
    # 基本設定を表示
    print(f"クロールURL: {config.base_url}")
    print(f"最大ページ数: {config.max_pages}")
    print(f"遅延時間: {config.delay} 秒")
    print(f"並列ワーカー数: {config.max_workers}")
    print(f"出力ディレクトリ: {config.output_dir}")
    print(f"キャッシュディレクトリ: {config.cache_dir}")
    print(f"Discord Webhook: {config.discord_webhook or '未設定'}")
    
    # 真偽値オプションを表示
    print("\n詳細設定:")
    print(f"差分検知: {'有効' if config.diff_detection else '無効'}")
    print(f"変更がない場合はスキップ: {'有効' if config.skip_no_changes else '無効'}")
    print(f"URL正規化: {'有効' if config.normalize_urls else '無効'}")
    print(f"robots.txtの尊重: {'有効' if config.respect_robots_txt else '無効'}")
    print(f"リダイレクトの追跡: {'有効' if config.follow_redirects else '無効'}")
    
    # 除外する静的ファイル拡張子
    print("\n除外する静的ファイル拡張子:")
    for ext in sorted(config.static_extensions):
        print(f"  {ext}")
    print()


def visualize_config(config, filename=None):
    """設定を視覚的に表示またはHTMLファイルとして保存"""
    if not config:
        print("設定が読み込まれていません。")
        return
        
    # 基本的なHTMLレポート
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>クローラー設定 - {config.base_url}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1, h2 {{ color: #333; }}
        .section {{ margin-bottom: 20px; }}
        .item {{ margin: 5px 0; }}
        .label {{ font-weight: bold; width: 200px; display: inline-block; }}
        .value {{ }}
        .enabled {{ color: green; }}
        .disabled {{ color: #999; }}
        .url {{ color: blue; text-decoration: underline; }}
        .extension-list {{ list-style-type: none; padding-left: 20px; columns: 3; }}
    </style>
</head>
<body>
    <h1>Webサイトクローラー設定</h1>
    
    <div class="section">
        <h2>基本設定</h2>
        <div class="item"><span class="label">クロールURL:</span> <span class="value url">{config.base_url}</span></div>
        <div class="item"><span class="label">最大ページ数:</span> <span class="value">{config.max_pages}</span></div>
        <div class="item"><span class="label">遅延時間:</span> <span class="value">{config.delay} 秒</span></div>
        <div class="item"><span class="label">並列ワーカー数:</span> <span class="value">{config.max_workers}</span></div>
        <div class="item"><span class="label">出力ディレクトリ:</span> <span class="value">{config.output_dir}</span></div>
        <div class="item"><span class="label">キャッシュディレクトリ:</span> <span class="value">{config.cache_dir}</span></div>
        <div class="item"><span class="label">Discord Webhook:</span> <span class="value">{config.discord_webhook or '未設定'}</span></div>
    </div>
    
    <div class="section">
        <h2>詳細設定</h2>
        <div class="item"><span class="label">差分検知:</span> <span class="value {'enabled">有効' if config.diff_detection else 'disabled">無効'}</span></div>
        <div class="item"><span class="label">変更がない場合はスキップ:</span> <span class="value {'enabled">有効' if config.skip_no_changes else 'disabled">無効'}</span></div>
        <div class="item"><span class="label">URL正規化:</span> <span class="value {'enabled">有効' if config.normalize_urls else 'disabled">無効'}</span></div>
        <div class="item"><span class="label">robots.txtの尊重:</span> <span class="value {'enabled">有効' if config.respect_robots_txt else 'disabled">無効'}</span></div>
        <div class="item"><span class="label">リダイレクトの追跡:</span> <span class="value {'enabled">有効' if config.follow_redirects else 'disabled">無効'}</span></div>
    </div>
    
    <div class="section">
        <h2>除外する静的ファイル拡張子</h2>
        <ul class="extension-list">
            {"".join([f'<li>{ext}</li>' for ext in sorted(config.static_extensions)])}
        </ul>
    </div>
    
    <div class="section">
        <h2>生成日時</h2>
        <div class="item">{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</body>
</html>
"""
    
    # ファイルに保存または標準出力に表示
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"HTML設定レポートを生成しました: {filename}")
    else:
        print("\n設定を表示するにはHTMLファイルを指定してください。")


def create_sample_configs():
    """サンプル設定を生成"""
    samples = {
        # Webサイト監視用
        'monitoring': CrawlerConfig(
            base_url="https://example.com",
            max_pages=500,
            delay=1.0,
            max_workers=5,
            diff_detection=True,
            skip_no_changes=True
        ),
        
        # アーカイブ用（大規模サイト向け）
        'archive': CrawlerConfig(
            base_url="https://example.com",
            max_pages=2000,
            delay=2.0,
            max_workers=3,
            diff_detection=False,
            skip_no_changes=False
        ),
        
        # パフォーマンス優先（高速クロール）
        'performance': CrawlerConfig(
            base_url="https://example.com",
            max_pages=100,
            delay=0.5,
            max_workers=10,
            diff_detection=False,
            skip_no_changes=False
        ),
        
        # ブログ・ニュースサイト専用
        'blog': CrawlerConfig(
            base_url="https://example.com",
            max_pages=200,
            delay=1.0,
            max_workers=5,
            diff_detection=True,
            normalize_urls=True
        )
    }
    
    # サンプルディレクトリの作成
    samples_dir = "config_samples"
    os.makedirs(samples_dir, exist_ok=True)
    
    # サンプル設定の保存
    for name, config in samples.items():
        save_config(config, os.path.join(samples_dir, f"{name}_config.json"))
    
    print(f"\nサンプル設定を {samples_dir} ディレクトリに生成しました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Webサイトクローラーの設定ユーティリティ")
    
    subparsers = parser.add_subparsers(dest="command", help="コマンド")
    
    # 新規作成コマンド
    create_parser = subparsers.add_parser("create", help="対話式ウィザードで設定を作成")
    create_parser.add_argument("-o", "--output", default="crawler_config.json", help="出力ファイル名")
    
    # 表示コマンド
    show_parser = subparsers.add_parser("show", help="設定内容を表示")
    show_parser.add_argument("config_file", help="表示する設定ファイル")
    
    # ビジュアライズコマンド
    viz_parser = subparsers.add_parser("visualize", help="設定をHTMLで視覚化")
    viz_parser.add_argument("config_file", help="視覚化する設定ファイル")
    viz_parser.add_argument("-o", "--output", help="出力HTMLファイル")
    
    # サンプル作成コマンド
    subparsers.add_parser("samples", help="サンプル設定を生成")
    
    # 検証コマンド
    validate_parser = subparsers.add_parser("validate", help="設定ファイルを検証")
    validate_parser.add_argument("config_file", help="検証する設定ファイル")
    
    args = parser.parse_args()
    
    # コマンドなしの場合は対話式ウィザード
    if not args.command:
        wizard = ConfigWizard()
        config = wizard.run()
        if config:
            output_file = input("\n設定ファイル名 [crawler_config.json]: ") or "crawler_config.json"
            save_config(config, output_file)
    
    # 対話式ウィザード
    elif args.command == "create":
        wizard = ConfigWizard()
        config = wizard.run()
        if config:
            save_config(config, args.output)
    
    # 設定表示
    elif args.command == "show":
        config = load_config(args.config_file)
        if config:
            print_config(config)
    
    # 設定視覚化
    elif args.command == "visualize":
        config = load_config(args.config_file)
        if config:
            visualize_config(config, args.output)
    
    # サンプル作成
    elif args.command == "samples":
        create_sample_configs()
    
    # 設定検証
    elif args.command == "validate":
        config = load_config(args.config_file)
        if config:
            print("設定ファイルは有効です。")
            print_config(config)


if __name__ == "__main__":
    main()