# Webサイトクローラー（差分検知機能付き）

同一ドメイン内のすべてのページを自動的にクロールし、コンテンツをMarkdown形式でエクスポートするPythonプログラムです。前回のクロール結果との差分を検知して変更点をレポートする機能も備えています。

## 特徴

- **同一ドメイン限定クローリング** - 指定したURLと同じドメイン内のページのみを収集
- **Markdown/PDF出力** - 取得したコンテンツをMarkdownファイルとPDFファイルに変換
- **差分検知機能** - 前回のクロール結果と比較し、追加/更新/削除されたページを検出
- **詳細な変更レポート** - 変更内容を詳細に記録したレポートを生成
- **Discord通知** - クロール完了時にDiscordへ通知を送信し、ファイルを添付
- **永続的キャッシュ** - SQLiteデータベースを使用してクロール結果を保存
- **robots.txt対応** - Webサイトのクロールポリシーを尊重
- **モジュラー設計** - 再利用可能なコンポーネントに分割された柔軟な設計

## 必要なライブラリ

```bash
pip install requests html2text lxml markdown pdfkit discord-webhook
```

PDFの生成には `wkhtmltopdf` というコマンドラインツールも必要です：

- **Ubuntu**: `sudo apt-get install wkhtmltopdf`
- **macOS**: `brew install wkhtmltopdf`
- **Windows**: [公式サイト](https://wkhtmltopdf.org/downloads.html)からインストーラーをダウンロード

## 使用方法

### ローカル実行

```bash
# 基本的な使用方法
python website_crawler_with_diff_detection.py https://example.com

# 詳細なオプションを指定
python website_crawler_with_diff_detection.py https://example.com --max-pages 200 --delay 2.0 --output-dir ./site_content --discord-webhook https://discord.com/api/webhooks/your-webhook-url --skip-no-changes
```

### Google Colab上での実行

1. `website_crawler_colab.ipynb` ノートブックをGoogle Colabにアップロード
2. 必要なライブラリをインストールするセルを実行
3. Google Driveをマウント（キャッシュと出力の永続化のため）
4. コード定義セルを実行
5. フォームで設定を入力して「クローラーを実行」ボタンをクリック

## コマンドラインオプション

| オプション | 説明 |
|----------|------|
| `url` | クロールを開始するURL（必須） |
| `--max-pages` | クロールする最大ページ数（デフォルト: 100） |
| `--delay` | リクエスト間の遅延秒数（デフォルト: 1.0） |
| `--output-dir` | 出力ディレクトリ（デフォルト: output） |
| `--discord-webhook` | Discord通知用のWebhook URL（省略可） |
| `--no-diff` | 差分検知を無効にする |
| `--skip-no-changes` | 変更がない場合、ファイル生成と通知をスキップ |

## Google Colabでの設定項目

- **URL**: クロールを開始するWebサイトのURL
- **最大ページ数**: クロールする最大ページ数（10〜500）
- **遅延時間**: リクエスト間の待機時間（0.5〜5.0秒）
- **Discord Webhook URL**: 通知先のWebhook URL（省略可）
- **差分検知**: 前回からの変更を検出する機能の有効/無効
- **変更がない場合はスキップ**: 前回から変更がない場合に処理をスキップ
- **出力ディレクトリ**: 結果を保存するパス
- **キャッシュディレクトリ**: キャッシュを保存するパス

## 出力ファイル

- **Markdownファイル** - すべてのページのコンテンツをまとめたファイル
- **PDFファイル** - Markdownファイルから生成されたPDF
- **差分レポート** - 前回との変更点をまとめたレポート（Markdown形式とPDF形式）

## 注意点

- 対象Webサイトのクロールポリシーを尊重してください
- リクエスト間の遅延時間を適切に設定し、サーバーに負荷をかけないようにしてください
- 大規模サイトのクロールは時間がかかるため、適切な最大ページ数を設定してください
- Google Colabのセッションは一定時間で終了するため、長時間のクロールには適していません
- 定期的なクロールを行いたい場合は、ローカルマシンやサーバー環境での実行をお勧めします

## 定期実行について

定期的なクロールを行いたい場合は、以下の選択肢があります：

1. ローカルマシンでPythonスクリプトとcronを使用
2. Google Cloud FunctionsやCloud Runなどのサーバーレスサービスで定期実行
3. GitHub ActionsやCircle CIなどのCI/CDサービスを利用して定期実行

## ライセンス

MITライセンス