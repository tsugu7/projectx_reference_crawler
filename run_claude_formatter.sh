#!/bin/bash

# Claude API を使用してMarkdownを整形するスクリプト

# 環境設定
VENV_DIR="./crawler_env"
INPUT_DIR=${1:-"./temp_output"}
OUTPUT_DIR=${2:-"./formatted_output"}
LOG_FILE="$OUTPUT_DIR/claude_formatter.log"

# APIキーの確認
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "エラー: ANTHROPIC_API_KEYが設定されていません。"
    echo "使用方法: ANTHROPIC_API_KEY=your_api_key ./run_claude_formatter.sh [入力ディレクトリ] [出力ディレクトリ]"
    exit 1
fi

# 実行時間の記録
echo "Claude Markdown整形開始: $(date)" | tee -a "$LOG_FILE"

# 出力ディレクトリの作成
mkdir -p "$OUTPUT_DIR"

# 仮想環境のアクティベートとフォーマッター実行
echo "Markdownファイルを整形しています..." | tee -a "$LOG_FILE"
source "$VENV_DIR/bin/activate" && \
  python3 claude_formatter.py "$INPUT_DIR" -o "$OUTPUT_DIR" | tee -a "$LOG_FILE"

# 実行完了の通知
echo "Claude Markdown整形完了: $(date)" | tee -a "$LOG_FILE"
echo "整形されたファイルは $OUTPUT_DIR ディレクトリに保存されました" | tee -a "$LOG_FILE"

# 結果ファイル一覧の表示
echo "生成されたファイル:" | tee -a "$LOG_FILE"
ls -lh "$OUTPUT_DIR" | tee -a "$LOG_FILE"