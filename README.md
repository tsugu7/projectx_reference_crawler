# Webサイトクローラー（差分検知機能付き）

## 概要

このWebサイトクローラーは、指定したURLから始めて同一ドメイン内のWebページを自動的にクロールし、コンテンツをMarkdown形式で保存します。前回のクロール結果との差分を検出し、変更点をレポートする機能も備えています。HTML→Markdown変換中に発生する様々な形式問題（特殊文字、連結見出し、リンク形式など）を自動的に修正する機能を搭載しています。Google Colab環境での実行に対応し、Python環境でのスタンドアロン実行も可能です。

**【注意】実行方法の詳細については [CRAWLER_USAGE.md](./CRAWLER_USAGE.md) を参照してください。**

## 主な機能

- **ウェブサイト全体のクロール**: 同一ドメイン内のページを自動的に巡回
- **コンテンツ変換**: HTMLをMarkdownおよびPDFに変換
- **差分検知**: 前回のクロール結果との比較による変更点の検出（新規/更新/削除ページ）
- **非同期処理**: 複数のページを並列でクロールし、処理を高速化
- **通知機能**: Discord Webhookを通じた結果の通知
- **Google Drive連携**: クロール結果やキャッシュの永続的保存
- **サイトマップ生成**: クロールしたページからサイトマップXMLを自動生成
- **詳細なレポート**: 変更点や統計情報の包括的なレポート
- **Markdown修正機能**: 以下の問題を自動的に修正
  - 特殊文字「ðï」「ðï¸」の除去
  - 連結見出しの修正（「## [A]()## [B]()」→「## [A]()\n\n## [B]()」）
  - 見出し内のテキスト結合問題の修正（「## Getting Started ProjectX Trading」）
  - リンクの修正（改行を含むリンク、エンコードされた文字を含むリンク）
  - コードブロック・JSON形式の整形
  - テーブル形式の整形

## 要件

- Python 3.7以上
- 必要なライブラリ:
  - requests
  - html2text
  - lxml
  - markdown
  - pdfkit
  - discord-webhook
  - aiohttp
  - dataclasses-json (オプション)
  - ipywidgets (Google Colab用)
- wkhtmltopdf (PDF変換用)

## インストール方法

### ローカル環境でのインストール

1. リポジトリをクローンまたはダウンロードします

2. 必要なパッケージをインストールします:
   ```bash
   pip install requests html2text lxml markdown pdfkit discord-webhook aiohttp
   ```

3. wkhtmltopdfをインストールします:
   - Ubuntu/Debian: `apt-get install wkhtmltopdf`
   - CentOS/RHEL: `yum install wkhtmltopdf`
   - macOS: `brew install wkhtmltopdf`
   - Windows: [公式サイト](https://wkhtmltopdf.org/downloads.html)からインストーラをダウンロード

### Google Colabでの使用

1. `website_crawler_colab.ipynb` をGoogle Colabにアップロード
2. ノートブック内の指示に従って実行

## 使用方法

### コマンドラインでの実行

```bash
# 基本的な使用法
python crawler_script.py --url https://example.com

# 詳細オプションを指定
python crawler_script.py --url https://example.com --pages 200 --delay 1.5 --workers 3 --output results

# 設定ファイルを使用
python crawler_script.py --config my_config.json

# クリーンなキャッシュから実行（前回の結果を保持しつつ新しくクロール）
./run_fresh_crawler.sh https://example.com
```

### 設定ファイルを作成

```bash
# 対話式ウィザードで設定を作成
python crawler_config_util.py create -o my_config.json

# 既存の設定を表示
python crawler_config_util.py show my_config.json

# 設定をHTMLで視覚化
python crawler_config_util.py visualize my_config.json -o config_report.html

# サンプル設定を生成
python crawler_config_util.py samples
```

### 特定ユースケース向けの実行

```bash
# Webサイトの変更を監視
python crawler_use_case.py monitor https://example.com

# サイト全体をアーカイブ
python crawler_use_case.py archive https://example.com

# サイトマップを生成
python crawler_use_case.py sitemap https://example.com

# ブログ・ニュースサイト向け
python crawler_use_case.py blog https://example.com

# ドキュメントサイト向け
python crawler_use_case.py docs https://example.com
```

### Google Colabでの実行

1. ノートブック内の「クローラー用のユーザーインターフェース」セルを実行
2. 表示されたフォームに必要な情報を入力:
   - URL: クロールを開始するWebサイトのURL
   - 最大ページ数: 処理するページの上限
   - 遅延時間: リクエスト間の待機時間（秒）
   - 並列数: 同時に処理するページ数
   - Discord Webhook URL (オプション): 通知先
3. オプション設定を選択
4. 「クローラーを実行」ボタンをクリック

## コマンドラインオプション

| オプション | 説明 |
|------------|------|
| `-u, --url URL` | クロールするWebサイトのURL（必須） |
| `-p, --pages NUM` | 最大ページ数（デフォルト: 100） |
| `-d, --delay NUM` | リクエスト間の遅延秒数（デフォルト: 1.0） |
| `-w, --workers NUM` | 並列ワーカー数（デフォルト: 5） |
| `-o, --output DIR` | 出力ディレクトリ（デフォルト: "output"） |
| `-c, --cache DIR` | キャッシュディレクトリ（デフォルト: "cache"） |
| `--discord URL` | Discord Webhook URL |
| `--no-diff` | 差分検知を無効化 |
| `--force` | 変更がなくても出力を生成 |
| `--no-normalize` | URL正規化を無効化 |
| `--ignore-robots` | robots.txtを無視 |
| `--config FILE` | 設定JSONファイルパス |

## 設定ファイル形式

設定はJSON形式で以下のように指定できます:

```json
{
  "base_url": "https://example.com",
  "max_pages": 100,
  "delay": 1.0,
  "max_workers": 5,
  "output_dir": "output",
  "cache_dir": "cache",
  "discord_webhook": "https://discord.com/api/webhooks/your-webhook-url",
  "diff_detection": true,
  "skip_no_changes": true,
  "normalize_urls": true,
  "respect_robots_txt": true,
  "follow_redirects": true
}
```

## 出力結果

クロール処理が完了すると、以下のファイルが生成されます:

1. **Markdownファイル**: クロールしたページのコンテンツ（`{ドメイン名}.md`）
2. **PDFファイル**: Markdownを変換したPDF（`{ドメイン名}.pdf`）
3. **差分レポート**: 前回からの変更を記録（`{ドメイン名}_diff_report.md`）
4. **概要レポート**: クロール統計情報（`{ドメイン名}_summary.md`）
5. **サイトマップ**: XMLサイトマップ（`sitemap-{ドメイン名}.xml`）
6. **ログファイル**: クロール処理のログ（`crawler.log`）

## ファイル構成

このプロジェクトは以下のファイルで構成されています:

- **`crawler_components.py`**: 基本クローラーコンポーネント
- **`crawler_advanced.py`**: 拡張機能と非同期処理エンジン
- **`crawler_script.py`**: コマンドライン実行用スクリプト
- **`crawler_config_util.py`**: 設定管理ユーティリティ
- **`crawler_use_case.py`**: 特定ユースケース向けスクリプト
- **`heading_fixer.py`**: 連結見出し修正ユーティリティ
- **`fix_markdown.py`**: Markdownファイル修正スクリプト
- **`website_crawler_colab.ipynb`**: Google Colab用ノートブック
- **`run_crawler.sh`**: 基本的なクローリングスクリプト
- **`run_crawler_advanced.sh`**: 高度なオプション指定が可能なクローリングスクリプト
- **`run_fresh_crawler.sh`**: キャッシュクリア版クローリングスクリプト
- **`CRAWLER_USAGE.md`**: クローラーの詳細な使用方法

## 差分検知について

差分検知機能は、前回のクロール結果との比較を行い、以下の変更を検出します:

- **新規ページ**: 前回のクロールには存在せず、今回新たに見つかったページ
- **更新ページ**: 前回から内容が変更されたページ
- **削除ページ**: 前回は存在したが、今回は見つからなかったページ

差分レポートには、URL一覧と、更新ページの詳細な差分（diff形式）が含まれます。

## Markdown修正機能

本クローラーには以下のMarkdown修正機能が搭載されています:

### 連結見出しの修正

連結見出し問題とは、以下のような見出しが正しく改行されない問題です:

```
## [最初のセクション](https://example.com/first)## [次のセクション](https://example.com/second)
```

これを以下のように修正します:

```
## [最初のセクション](https://example.com/first)

## [次のセクション](https://example.com/second)
```

### 見出し内テキスト結合問題の修正

見出しの後に適切な改行なしでテキストが続く問題を修正します:

```
## Getting Started ProjectX Trading
このテキストは見出しと結合してしまっています
```

これを以下のように修正します:

```
## Getting Started ProjectX Trading

このテキストは見出しと結合してしまっています
```

### 特殊文字の除去

ドキュメント内の不要な特殊文字「ðï」「ðï¸」を自動的に除去します。

### リンク形式の修正

改行を含むリンクや、エンコードされた文字を含むURLを自動的に修正します。

### コードブロックとJSONの整形

コードブロックを検出して適切に整形し、言語ヒントを追加します。JSON形式のコードは自動的に整形されます（ただしcURLコマンド内のJSONは除く）。

### テーブル形式の修正

テーブルの行と列の幅を整え、セル内の空白を調整します。

## 定期実行の設定

### Linuxのcrontabでの設定例

```bash
# 毎日午前3時に実行
0 3 * * * /path/to/python /path/to/crawler_script.py --url https://example.com --output /path/to/output
```

### GitHub Actionsでの設定例

```yaml
name: Website Crawler

on:
  schedule:
    - cron: '0 3 * * *'  # 毎日午前3時に実行
  workflow_dispatch:      # 手動実行も可能

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
          
      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y wkhtmltopdf
          pip install requests html2text lxml markdown pdfkit discord-webhook aiohttp
          
      - name: Run crawler
        run: |
          python crawler_script.py --url https://example.com --output ./output
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: crawler-output
          path: ./output
```

## カスタマイズ

### URL正規化とフィルタリングのカスタマイズ

`crawler_components.py` の `UrlFilter` クラスを編集することで、クロール対象URLのルールをカスタマイズできます。

```python
# 除外パターンの例
self.exclude_patterns = [
    r'\/(?:calendar|login|logout|signup|register|password-reset)(?:\/|$)',
    r'\/feed(?:\/|$)',
    r'\/wp-admin(?:\/|$)',
    # 他のパターンを追加
]
```

### PDFスタイルのカスタマイズ

`crawler_advanced.py` の `PdfConverter` クラスの `default_css` を編集するか、外部CSSファイルを指定することで、PDF出力のスタイルをカスタマイズできます。

### Markdown修正機能のカスタマイズ

`heading_fixer.py` の正規表現パターンを編集することで、特定の問題に対応する修正を追加できます:

```python
# 見出し後にテキストが続く新しいパターンを追加
pattern5 = r'(\#{1,6}\s+[^\n]+)\s+([A-Za-z][a-z0-9]+)'
markdown_content = re.sub(pattern5, r'\1\n\n\2', markdown_content)
```

## 応用例

### ウェブサイトの監視システム

サイトの変更を監視し、変更があった場合のみDiscordに通知します。

```bash
python crawler_use_case.py monitor https://example.com --discord https://discord.com/api/webhooks/your-webhook
```

### コンテンツアーカイブ

Webサイト全体をアーカイブします。

```bash
python crawler_use_case.py archive https://example.com
```

### サイトマップ生成

サイトマップを生成するための最小構成です。

```bash
python crawler_use_case.py sitemap https://example.com
```

## トラブルシューティング

### PDFが生成されない

- wkhtmltopdfがシステムにインストールされているか確認
- パーミッションの問題がないか確認
- ログファイルでエラーメッセージを確認

### 特定のページがクロールされない

- UrlFilterの設定を確認（除外パターンや静的ファイル拡張子）
- robots.txtの設定を確認
- JavaScriptで動的に生成されるコンテンツはクロールできない場合があります

### メモリ使用量が多い

- `max_pages`の値を小さくする
- `max_workers`の値を小さくする

### Markdown変換の問題

- 特定のHTML要素が正しく変換されない場合は、`_preprocess_html`または`_postprocess_markdown`メソッドをカスタマイズ
- 見出し修正に関する問題は`heading_fixer.py`の正規表現パターンを調整

## API

主要なクラスは以下の通りです:

- `CrawlerConfig`: クローラーの設定を管理
- `UrlFilter`: URLをフィルタリング
- `Fetcher`: HTMLコンテンツを取得
- `Parser`: HTMLを解析してリンクを抽出
- `MarkdownConverter`: HTMLをMarkdownに変換
- `ContentRepository`: クロールしたコンテンツを管理
- `CrawlCache`: 差分検知用のデータをキャッシュ
- `FileExporter`: 結果をファイルとして出力
- `PdfConverter`: MarkdownをPDFに変換
- `DiscordNotifier`: Discord通知を送信
- `AsyncCrawler`: 非同期クロールエンジン
- `fix_concatenated_headings`: 連結見出しを修正する関数