# ProjectX Gateway API クローラーの使用方法

このドキュメントでは、ProjectX Gateway APIドキュメントのクロールと出力方法について説明します。

## 前提条件

クローラーを実行するには以下が必要です：

1. Python 3.7以上
2. 仮想環境（`crawler_env`）
3. 必要なパッケージ（`requests`、`html2text`、`lxml`、`markdown`、`pdfkit`、`discord-webhook`）
4. `wkhtmltopdf`（PDF変換用）

## セットアップ

初回実行時は、以下のコマンドで環境をセットアップしてください：

```bash
# 仮想環境の作成
python3 -m venv crawler_env

# 仮想環境の有効化
source crawler_env/bin/activate

# 必要なパッケージのインストール
pip install requests html2text lxml markdown pdfkit discord-webhook

# wkhtmltopdfのインストール（システムによって異なります）
# Ubuntuの場合：
sudo apt-get install wkhtmltopdf
```

## 使用方法

### 基本的な実行方法

シンプルなスクリプトを使用：

```bash
./run_crawler.sh
```

このコマンドは以下のデフォルト設定で実行されます：
- URL: https://gateway.docs.projectx.com/
- 最大ページ数: 200
- 遅延時間: 2.0秒

### カスタムパラメータの指定

シンプルスクリプトに引数を渡す：

```bash
./run_crawler.sh "https://example.com" 100 1.5
```

引数の順序：
1. URL（クロール開始URL）
2. 最大ページ数
3. 遅延時間（秒）

### 高度な実行方法

より詳細なオプションを指定する場合は、高度なスクリプトを使用してください：

```bash
./run_crawler_advanced.sh --url "https://gateway.docs.projectx.com/" --pages 200 --delay 2.0 --output "./projectx_docs" --force
```

使用可能なオプション：

```
使用方法: ./run_crawler_advanced.sh [オプション]
オプション:
  -u, --url URL         クロールするURL
  -p, --pages NUM       クロールする最大ページ数
  -d, --delay NUM       リクエスト間の遅延秒数
  -w, --workers NUM     並列ワーカー数
  -o, --output DIR      出力ディレクトリ
  -c, --cache DIR       キャッシュディレクトリ
  -f, --force           変更がなくても出力を生成
  --no-diff             差分検知を無効化
  -h, --help            このヘルプメッセージを表示
```

## 出力ファイル

クロール完了後、以下のファイルが出力ディレクトリに生成されます：

1. `gateway.docs.projectx.com.md` - Markdownフォーマットのドキュメント
2. `gateway.docs.projectx.com.pdf` - PDF形式のドキュメント
3. `gateway.docs.projectx.com_diff_report.md` - 前回との差分レポート（Markdown）
4. `gateway.docs.projectx.com_diff_report.pdf` - 差分レポート（PDF）
5. `gateway.docs.projectx.com_summary.md` - クロール概要
6. `sitemap-gateway.docs.projectx.com.xml` - サイトマップ
7. `crawler.log` - クロールログ
8. `crawler_run.log` - スクリプト実行ログ

## 推奨パラメータ

ProjectX Gateway APIドキュメントを効果的にクロールするための推奨パラメータ：

```bash
./run_crawler_advanced.sh --url "https://gateway.docs.projectx.com/" --pages 200 --delay 2.0 --workers 5
```

これらの設定は以下のために最適化されています：
- **delay 2.0秒**: ページ内容を完全に読み込むのに十分な待機時間
- **workers 5**: 効率的な並列処理のためのワーカー数
- **pages 200**: すべての利用可能なドキュメントページを確実に取得

## トラブルシューティング

1. **コンテンツが不完全な場合**:
   - `--delay`パラメータを増やして（例：3.0秒）、ページロード時間を長くしてみてください。

2. **PDFが生成されない場合**:
   - `wkhtmltopdf`がインストールされていることを確認してください。
   - エラーログを確認して、具体的な問題を特定してください。

3. **クロールが早く終了する場合**:
   - 対象ウェブサイトの構造やクロールポリシーを確認してください。
   - サイトマップを確認して、利用可能なページ数を確認してください。