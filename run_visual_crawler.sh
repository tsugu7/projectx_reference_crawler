#!/bin/bash

# ProjectX Gateway API クローラー実行スクリプト（ビジュアルクローリングモード）

# 環境設定
VENV_DIR="./crawler_env"
CACHE_DIR="./visual_cache"
OUTPUT_DIR="./visual_output"
LOG_FILE="$OUTPUT_DIR/visual_crawler_run.log"

# 引数の処理
URL=${1:-"https://gateway.docs.projectx.com/"}
MAX_PAGES=${2:-10}  # ビジュアルモードではページ数を制限
DELAY=${3:-2.0}     # スクリーンショット処理のために長めの遅延

# 実行時間の記録
echo "ビジュアルクローリング開始: $(date)" | tee -a "$LOG_FILE"

# 出力ディレクトリとキャッシュディレクトリの作成
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CACHE_DIR"

# Pythonスクリプトでビジュアルモードフラグを設定
TEMP_CONFIG="$OUTPUT_DIR/visual_config.json"
cat > "$TEMP_CONFIG" << EOF
{
  "base_url": "$URL",
  "max_pages": $MAX_PAGES,
  "delay": $DELAY,
  "max_workers": 1,
  "output_dir": "$OUTPUT_DIR",
  "cache_dir": "$CACHE_DIR",
  "visual_mode": true,
  "visual_config": {
    "save_screenshots": true,
    "ocr_lang": "eng+jpn"
  }
}
EOF

# 仮想環境のアクティベートとクローラー実行
echo "ビジュアルモードでクローラーを実行しています..." | tee -a "$LOG_FILE"
source "$VENV_DIR/bin/activate" && \
  python3 crawler_script.py \
    --config "$TEMP_CONFIG" \
    | tee -a "$LOG_FILE"

# クロール完了後、連結見出しを修正
echo "連結見出しを修正しています..." | tee -a "$LOG_FILE"
python3 fix_markdown.py "$OUTPUT_DIR"

# 実行完了の通知
echo "ビジュアルクローリング完了: $(date)" | tee -a "$LOG_FILE"
echo "出力ファイルは $OUTPUT_DIR ディレクトリに保存されました" | tee -a "$LOG_FILE"

# 結果ファイル一覧の表示
echo "生成されたファイル:" | tee -a "$LOG_FILE"
ls -lh "$OUTPUT_DIR" | tee -a "$LOG_FILE"