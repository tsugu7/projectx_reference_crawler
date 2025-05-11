#!/bin/bash

# ProjectX Gateway API クローラー - 高度な実行スクリプト

# デフォルト設定
VENV_DIR="./crawler_env"
CACHE_DIR="./crawler_cache"
OUTPUT_DIR="./projectx_docs_output"
URL="https://gateway.docs.projectx.com/"
MAX_PAGES=200
DELAY=2.0
WORKERS=5
FORCE_OUTPUT=false
NO_DIFF=false

# 使用方法の表示
function show_usage {
    echo "使用方法: $0 [オプション]"
    echo "オプション:"
    echo "  -u, --url URL         クロールするURL (デフォルト: $URL)"
    echo "  -p, --pages NUM       クロールする最大ページ数 (デフォルト: $MAX_PAGES)"
    echo "  -d, --delay NUM       リクエスト間の遅延秒数 (デフォルト: $DELAY)"
    echo "  -w, --workers NUM     並列ワーカー数 (デフォルト: $WORKERS)"
    echo "  -o, --output DIR      出力ディレクトリ (デフォルト: $OUTPUT_DIR)"
    echo "  -c, --cache DIR       キャッシュディレクトリ (デフォルト: $CACHE_DIR)"
    echo "  -f, --force           変更がなくても出力を生成"
    echo "  --no-diff             差分検知を無効化"
    echo "  -h, --help            このヘルプメッセージを表示"
    echo ""
    echo "例:"
    echo "  $0 -u https://example.com -p 100 -d 1.5 -o ./output"
    echo "  $0 --url https://api.example.com --pages 50 --force"
}

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            URL="$2"
            shift 2
            ;;
        -p|--pages)
            MAX_PAGES="$2"
            shift 2
            ;;
        -d|--delay)
            DELAY="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--cache)
            CACHE_DIR="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_OUTPUT=true
            shift
            ;;
        --no-diff)
            NO_DIFF=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "エラー: 不明なオプション '$1'" >&2
            show_usage
            exit 1
            ;;
    esac
done

# ログファイルの設定
LOG_FILE="$OUTPUT_DIR/crawler_run_$(date +%Y%m%d_%H%M%S).log"

# 出力ディレクトリとキャッシュディレクトリの作成
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CACHE_DIR"

# 実行設定の表示
echo "=======================================================" | tee -a "$LOG_FILE"
echo "ProjectX Gateway API クローラー - 実行開始" | tee -a "$LOG_FILE"
echo "=======================================================" | tee -a "$LOG_FILE"
echo "実行時刻: $(date)" | tee -a "$LOG_FILE"
echo "URL: $URL" | tee -a "$LOG_FILE"
echo "最大ページ数: $MAX_PAGES" | tee -a "$LOG_FILE"
echo "遅延時間: $DELAY 秒" | tee -a "$LOG_FILE"
echo "並列ワーカー数: $WORKERS" | tee -a "$LOG_FILE"
echo "出力ディレクトリ: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "キャッシュディレクトリ: $CACHE_DIR" | tee -a "$LOG_FILE"
echo "強制出力: $FORCE_OUTPUT" | tee -a "$LOG_FILE"
echo "差分検知無効: $NO_DIFF" | tee -a "$LOG_FILE"
echo "=======================================================" | tee -a "$LOG_FILE"

# コマンドオプションの構築
CMD_OPTIONS="--url \"$URL\" --pages $MAX_PAGES --delay $DELAY --workers $WORKERS --output \"$OUTPUT_DIR\" --cache \"$CACHE_DIR\""

if [ "$FORCE_OUTPUT" = true ]; then
    CMD_OPTIONS="$CMD_OPTIONS --force"
fi

if [ "$NO_DIFF" = true ]; then
    CMD_OPTIONS="$CMD_OPTIONS --no-diff"
fi

# 仮想環境のアクティベートとクローラー実行
echo "クローラーを実行しています..." | tee -a "$LOG_FILE"
source "$VENV_DIR/bin/activate"

# 評価と実行
eval "python crawler_script.py $CMD_OPTIONS" | tee -a "$LOG_FILE"

# 実行結果の表示
RESULT=$?
echo "=======================================================" | tee -a "$LOG_FILE"
if [ $RESULT -eq 0 ]; then
    echo "クロール成功: $(date)" | tee -a "$LOG_FILE"
    echo "出力ファイルは $OUTPUT_DIR ディレクトリに保存されました" | tee -a "$LOG_FILE"
    
    # 結果ファイル一覧の表示
    echo "生成されたファイル:" | tee -a "$LOG_FILE"
    ls -lh "$OUTPUT_DIR" | tee -a "$LOG_FILE"
else
    echo "クロール失敗: $(date)" | tee -a "$LOG_FILE"
    echo "エラーログを確認してください: $LOG_FILE" | tee -a "$LOG_FILE"
fi
echo "=======================================================" | tee -a "$LOG_FILE"