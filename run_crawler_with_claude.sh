#!/bin/bash

# Claude API を使用した高度なフォーマット機能付きのクローラー実行スクリプト

# 環境設定
VENV_DIR="./crawler_env"
CACHE_DIR="./fresh_cache"
TEMP_OUTPUT_DIR="./temp_output"
FINAL_OUTPUT_DIR="./claude_output"
LOG_FILE="$FINAL_OUTPUT_DIR/full_process.log"

# 引数の処理
URL=${1:-"https://gateway.docs.projectx.com/"}
MAX_PAGES=${2:-200}
DELAY=${3:-1.0}

# APIキーの確認
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "警告: ANTHROPIC_API_KEYが設定されていません。Claude APIによる高度な整形は実行されません。"
    echo "Claude APIによる整形を有効にするには: ANTHROPIC_API_KEY=your_api_key ./run_crawler_with_claude.sh [URL] [ページ数] [遅延]"
    USE_CLAUDE=false
else
    USE_CLAUDE=true
fi

# 出力ディレクトリの作成
mkdir -p "$TEMP_OUTPUT_DIR"
mkdir -p "$FINAL_OUTPUT_DIR"

# ログファイルの初期化
echo "===== 処理開始: $(date) =====" > "$LOG_FILE"
echo "URL: $URL" >> "$LOG_FILE"
echo "最大ページ数: $MAX_PAGES" >> "$LOG_FILE"
echo "遅延時間: $DELAY" >> "$LOG_FILE"
echo "Claude API使用: $USE_CLAUDE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 仮想環境のアクティベート
source "$VENV_DIR/bin/activate"

# ステップ1: クローラーの実行
echo "ステップ1: クローラーを実行しています..." | tee -a "$LOG_FILE"
python3 crawler_script.py \
  --url "$URL" \
  --pages "$MAX_PAGES" \
  --delay "$DELAY" \
  --output "$TEMP_OUTPUT_DIR" \
  --cache "$CACHE_DIR" \
  | tee -a "$LOG_FILE"

# 処理結果の確認
CRAWLER_STATUS=$?
if [ $CRAWLER_STATUS -ne 0 ]; then
    echo "エラー: クローラーの実行に失敗しました。ログを確認してください。" | tee -a "$LOG_FILE"
    exit 1
fi

# ステップ2: 連結見出しの修正
echo "" >> "$LOG_FILE"
echo "ステップ2: 連結見出しを修正しています..." | tee -a "$LOG_FILE"
python3 fix_markdown.py "$TEMP_OUTPUT_DIR" | tee -a "$LOG_FILE"

# ステップ3: Claude APIによる高度な整形（APIキーがある場合のみ）
if [ "$USE_CLAUDE" = true ]; then
    echo "" >> "$LOG_FILE"
    echo "ステップ3: Claude APIを使用して高度な整形を行っています..." | tee -a "$LOG_FILE"
    
    # APIの接続状態をチェック
    python3 claude_check.py | tee -a "$LOG_FILE"
    CLAUDE_CHECK_STATUS=$?
    
    if [ $CLAUDE_CHECK_STATUS -eq 0 ]; then
        # Claude APIによるMarkdown整形
        python3 claude_formatter.py "$TEMP_OUTPUT_DIR" -o "$FINAL_OUTPUT_DIR" | tee -a "$LOG_FILE"
        CLAUDE_STATUS=$?
        
        if [ $CLAUDE_STATUS -ne 0 ]; then
            echo "警告: Claude APIによる整形に失敗しました。標準の整形結果を使用します。" | tee -a "$LOG_FILE"
            
            # 標準の整形結果をコピー
            cp -r "$TEMP_OUTPUT_DIR"/* "$FINAL_OUTPUT_DIR"/
        fi
    else
        echo "警告: Claude APIとの接続に失敗しました。標準の整形結果を使用します。" | tee -a "$LOG_FILE"
        
        # 標準の整形結果をコピー
        cp -r "$TEMP_OUTPUT_DIR"/* "$FINAL_OUTPUT_DIR"/
    fi
else
    echo "" >> "$LOG_FILE"
    echo "ステップ3: Claude APIが設定されていないため、標準の整形結果を使用します..." | tee -a "$LOG_FILE"
    
    # 標準の整形結果をコピー
    cp -r "$TEMP_OUTPUT_DIR"/* "$FINAL_OUTPUT_DIR"/
fi

# ステップ4: PDF生成
echo "" >> "$LOG_FILE"
echo "ステップ4: PDFを生成しています..." | tee -a "$LOG_FILE"

# ドメイン名を抽出
DOMAIN=$(echo $URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')
MARKDOWN_FILE="$FINAL_OUTPUT_DIR/$DOMAIN.md"

# PDFが未生成の場合のみ生成
if [ -f "$MARKDOWN_FILE" ]; then
    # PDFコンバーターを使用
    echo "PDFファイルを生成中: ${MARKDOWN_FILE%.md}.pdf" | tee -a "$LOG_FILE"
    python3 -c "
from crawler_advanced import PdfConverter
converter = PdfConverter('$FINAL_OUTPUT_DIR')
converter.convert('$MARKDOWN_FILE', title='$DOMAIN - クロール結果')
"
    # 結果を確認
    if [ -f "${MARKDOWN_FILE%.md}.pdf" ]; then
        echo "PDFファイルの生成に成功しました: ${MARKDOWN_FILE%.md}.pdf" | tee -a "$LOG_FILE"
    else
        echo "警告: PDFファイルの生成に失敗しました" | tee -a "$LOG_FILE"
    fi
else
    echo "警告: Markdownファイルが見つかりません: $MARKDOWN_FILE" | tee -a "$LOG_FILE"
fi

# 実行完了の通知
echo "" >> "$LOG_FILE"
echo "===== 処理完了: $(date) =====" | tee -a "$LOG_FILE"
echo "処理が完了しました。" | tee -a "$LOG_FILE"
echo "最終出力は $FINAL_OUTPUT_DIR ディレクトリに保存されました。" | tee -a "$LOG_FILE"

# 結果ファイル一覧の表示
echo "" >> "$LOG_FILE"
echo "生成されたファイル:" | tee -a "$LOG_FILE"
ls -lh "$FINAL_OUTPUT_DIR" | tee -a "$LOG_FILE"

exit 0