#!/bin/bash

# ProjectX Gateway API クローラー実行スクリプト

# 環境設定
VENV_DIR="./crawler_env"
CACHE_DIR="./crawler_cache"
OUTPUT_DIR="./projectx_docs_output"
LOG_FILE="$OUTPUT_DIR/crawler_run.log"

# 引数の処理
URL=${1:-"https://gateway.docs.projectx.com/"}
MAX_PAGES=${2:-200}
DELAY=${3:-2.0}

# 実行時間の記録
echo "クロール開始: $(date)" | tee -a "$LOG_FILE"

# 出力ディレクトリとキャッシュディレクトリの作成
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CACHE_DIR"

# 仮想環境のアクティベートとクローラー実行
echo "クローラーを実行しています..." | tee -a "$LOG_FILE"
source "$VENV_DIR/bin/activate" && \
  python crawler_script.py \
    --url "$URL" \
    --pages "$MAX_PAGES" \
    --delay "$DELAY" \
    --output "$OUTPUT_DIR" \
    --cache "$CACHE_DIR" \
    | tee -a "$LOG_FILE"

# 実行完了の通知
echo "クロール完了: $(date)" | tee -a "$LOG_FILE"
echo "出力ファイルは $OUTPUT_DIR ディレクトリに保存されました" | tee -a "$LOG_FILE"

# 結果ファイル一覧の表示
echo "生成されたファイル:" | tee -a "$LOG_FILE"
ls -lh "$OUTPUT_DIR" | tee -a "$LOG_FILE"