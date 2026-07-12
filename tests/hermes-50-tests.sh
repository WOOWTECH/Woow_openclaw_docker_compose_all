#!/usr/bin/env bash
# =============================================================================
# Hermes Agent 50-Test Suite — OfficeCLI + FFmpeg Capabilities
# =============================================================================
set -euo pipefail

POD="hermes-mcp-admin-5f985979d7-jkgx8"
NS="hermes-mcp-admin"
CTX="woow-k3s"
API_URL="http://hermes-agent-svc.hermes.svc.cluster.local:8642/v1/responses"
API_KEY="REDACTED_API_SERVER_KEY_2"
RESULTS_DIR="/var/tmp/vibe-kanban/worktrees/c38b-k3s-kubernetes-h/k3s project/tests/results-50"
TIMEOUT=120
RATE_DELAY=6  # seconds between individual requests

mkdir -p "$RESULTS_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# Helper: send a message and capture raw JSON response
# ─────────────────────────────────────────────────────────────────────────────
send_msg() {
  local msg="$1"
  local test_num="$2"
  local session_id="${3:-}"

  local payload
  if [[ -n "$session_id" ]]; then
    payload=$(python3 -c "
import json, sys
d = {'model':'default','input': sys.argv[1], 'previous_response_id': sys.argv[2]}
print(json.dumps(d, ensure_ascii=False))
" "$msg" "$session_id")
  else
    payload=$(python3 -c "
import json, sys
d = {'model':'default','input': sys.argv[1]}
print(json.dumps(d, ensure_ascii=False))
" "$msg")
  fi

  local resp
  resp=$(kubectl --context="$CTX" -n "$NS" exec "$POD" -- \
    curl -s -w '\n___HTTP_CODE___%{http_code}' \
    -X POST "$API_URL" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    --connect-timeout 15 --max-time "$TIMEOUT" 2>&1) || true

  local http_code
  http_code=$(echo "$resp" | grep '___HTTP_CODE___' | sed 's/.*___HTTP_CODE___//')
  local body
  body=$(echo "$resp" | grep -v '___HTTP_CODE___')

  echo "$body" > "$RESULTS_DIR/test_${test_num}_raw.json"
  echo "$http_code" > "$RESULTS_DIR/test_${test_num}_http.txt"

  # Extract text and response_id
  local text resp_id
  text=$(echo "$body" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    out = d.get('output', [])
    texts = []
    for o in out:
        if o.get('type') == 'message':
            for c in o.get('content', []):
                if c.get('type') == 'output_text':
                    texts.append(c['text'])
    print(' '.join(texts) if texts else '[no text]')
except:
    print('[parse error]')
" 2>/dev/null) || text="[error]"

  resp_id=$(echo "$body" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('id', ''))
except:
    print('')
" 2>/dev/null) || resp_id=""

  echo "$text" > "$RESULTS_DIR/test_${test_num}_text.txt"
  echo "$resp_id" > "$RESULTS_DIR/test_${test_num}_respid.txt"

  echo "$resp_id"
}

# ─────────────────────────────────────────────────────────────────────────────
# Evaluate test result: PASS if HTTP 200 + non-empty text + no error
# ─────────────────────────────────────────────────────────────────────────────
evaluate() {
  local test_num="$1"
  local http_code
  http_code=$(cat "$RESULTS_DIR/test_${test_num}_http.txt" 2>/dev/null || echo "0")
  local text
  text=$(cat "$RESULTS_DIR/test_${test_num}_text.txt" 2>/dev/null || echo "")

  if [[ "$http_code" == "200" ]] && [[ -n "$text" ]] && [[ "$text" != "[no text]" ]] && [[ "$text" != "[parse error]" ]] && [[ "$text" != "[error]" ]]; then
    echo "PASS"
  else
    echo "FAIL"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Run a single test
# ─────────────────────────────────────────────────────────────────────────────
run_test() {
  local num="$1"
  local category="$2"
  local msg="$3"
  local session_id="${4:-}"

  echo "  [Test $num] Sending: ${msg:0:50}..."
  local resp_id
  resp_id=$(send_msg "$msg" "$num" "$session_id")
  local result
  result=$(evaluate "$num")

  local text_preview
  text_preview=$(head -c 100 "$RESULTS_DIR/test_${num}_text.txt" 2>/dev/null | tr '\n' ' ')

  echo "  [Test $num] $result | ${text_preview:0:80}"
  echo "$num|$category|${msg:0:40}|$result|${text_preview:0:100}" >> "$RESULTS_DIR/summary.csv"

  # Return the response ID for multi-turn
  echo "$resp_id" > "$RESULTS_DIR/test_${num}_session.txt"
}

# ─────────────────────────────────────────────────────────────────────────────
# Clean up old results
# ─────────────────────────────────────────────────────────────────────────────
rm -f "$RESULTS_DIR"/*.json "$RESULTS_DIR"/*.txt "$RESULTS_DIR"/*.csv
echo "num|category|message|result|response_preview" > "$RESULTS_DIR/summary.csv"

echo "=============================================="
echo " Hermes Agent 50-Test Suite"
echo " Model: MiniMax-M1 (minimax provider)"
echo " Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=============================================="

# ═══════════════════════════════════════════════════════════════════════════════
# BATCH 1: Word Tests (1-5)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "=== BATCH 1: Word Tests (1-5) ==="

run_test 1 "Word" "幫我建立一個 Word 文件，標題是「AI 月報」，內容包含三段：摘要、分析、結論。請把文件存到 /tmp/ai_report.docx"
sleep $RATE_DELAY

SID1=$(cat "$RESULTS_DIR/test_1_respid.txt")
run_test 2 "Word" "在剛才的文件 /tmp/ai_report.docx 加入一個表格，欄位是：項目、狀態、負責人" "$SID1"
sleep $RATE_DELAY

run_test 3 "Word" "讀取 /tmp/ai_report.docx 的內容給我看" "$SID1"
sleep $RATE_DELAY

run_test 4 "Word" "把文件 /tmp/ai_report.docx 裡的「摘要」改成「執行摘要」" "$SID1"
sleep $RATE_DELAY

run_test 5 "Word" "在 /tmp/ai_report.docx 文件最後加入「附錄：參考資料」段落" "$SID1"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 2: Word Tests (6-8) + Excel (9-10) ==="

run_test 6 "Word" "顯示 /tmp/ai_report.docx 文件的結構大綱" "$SID1"
sleep $RATE_DELAY

run_test 7 "Word" "把 /tmp/ai_report.docx 匯出為 HTML 存到 /tmp/ai_report.html" "$SID1"
sleep $RATE_DELAY

run_test 8 "Word" "建立一個合約範本 /tmp/contract.docx，包含甲方乙方資訊欄位"
sleep $RATE_DELAY

run_test 9 "Excel" "建立一個 Excel 檔案 /tmp/sales.xlsx，工作表名稱是「銷售報表」，欄位：月份、營收、成本、利潤"
sleep $RATE_DELAY

SID9=$(cat "$RESULTS_DIR/test_9_respid.txt")
run_test 10 "Excel" "在 /tmp/sales.xlsx 第二行填入 1月、100000、60000，利潤用公式計算" "$SID9"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 3: Excel Tests (11-15) ==="

run_test 11 "Excel" "在 /tmp/sales.xlsx 加入第三行：2月、120000、70000" "$SID9"
sleep $RATE_DELAY

run_test 12 "Excel" "讀取 /tmp/sales.xlsx 整個工作表內容" "$SID9"
sleep $RATE_DELAY

run_test 13 "Excel" "在 /tmp/sales.xlsx 的 B5 儲存格加入 SUM 公式計算總營收" "$SID9"
sleep $RATE_DELAY

run_test 14 "Excel" "在 /tmp/sales.xlsx 建立第二個工作表叫「費用明細」" "$SID9"
sleep $RATE_DELAY

run_test 15 "Excel" "把 /tmp/sales.xlsx 營收欄的數字格式設為貨幣" "$SID9"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 4: Excel (16), PowerPoint (17-21) ==="

run_test 16 "Excel" "把 /tmp/sales.xlsx 匯出為 CSV 格式存到 /tmp/sales.csv" "$SID9"
sleep $RATE_DELAY

run_test 17 "PowerPoint" "建立一個簡報 /tmp/plan2026.pptx，第一頁標題是「2026 年度計畫」"
sleep $RATE_DELAY

SID17=$(cat "$RESULTS_DIR/test_17_respid.txt")
run_test 18 "PowerPoint" "在 /tmp/plan2026.pptx 加入第二頁，內容是三個重點項目的清單" "$SID17"
sleep $RATE_DELAY

run_test 19 "PowerPoint" "在 /tmp/plan2026.pptx 第一頁加入公司 logo 文字方塊" "$SID17"
sleep $RATE_DELAY

run_test 20 "PowerPoint" "讀取 /tmp/plan2026.pptx 簡報的大綱結構" "$SID17"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 5: PowerPoint (21), Cross-format (22-25) ==="

run_test 21 "PowerPoint" "在 /tmp/plan2026.pptx 加入第三頁做為「謝謝」頁面" "$SID17"
sleep $RATE_DELAY

run_test 22 "Cross-format" "幫我建立一套完整的專案文件：一個 Word 需求文件 /tmp/proj_req.docx、一個 Excel 時程表 /tmp/proj_schedule.xlsx、一個 PowerPoint 簡報 /tmp/proj_pres.pptx"
sleep $RATE_DELAY

SID22=$(cat "$RESULTS_DIR/test_22_respid.txt")
run_test 23 "Cross-format" "讀取所有剛才建立的 /tmp 底下的專案文件內容摘要" "$SID22"
sleep $RATE_DELAY

run_test 24 "Cross-format" "用 OfficeCLI 的 JSON 模式輸出 /tmp/sales.xlsx 的結構"
sleep $RATE_DELAY

run_test 25 "Cross-format" "列出 /tmp 底下所有 Office 文件（.docx .xlsx .pptx）"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 6: FFmpeg Audio (26-30) ==="

run_test 26 "FFmpeg-Audio" "用 FFmpeg 生成一個 5 秒的 440Hz 正弦波音調，存到 /tmp/tone440.wav"
sleep $RATE_DELAY

SID26=$(cat "$RESULTS_DIR/test_26_respid.txt")
run_test 27 "FFmpeg-Audio" "把 /tmp/tone440.wav 轉成 mp3 格式存到 /tmp/tone440.mp3" "$SID26"
sleep $RATE_DELAY

run_test 28 "FFmpeg-Audio" "用 FFmpeg 生成一個白噪音音檔 3 秒，存到 /tmp/whitenoise.wav"
sleep $RATE_DELAY

run_test 29 "FFmpeg-Audio" "把 /tmp/tone440.wav 和 /tmp/whitenoise.wav 兩個音檔合併成 /tmp/merged.wav"
sleep $RATE_DELAY

run_test 30 "FFmpeg-Audio" "裁切 /tmp/tone440.wav 前 2 秒存到 /tmp/tone_cut.wav"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 7: FFmpeg Audio (31-33), Video (34-35) ==="

run_test 31 "FFmpeg-Audio" "把 /tmp/tone440.wav 調整音量到 50% 存到 /tmp/tone_quiet.wav"
sleep $RATE_DELAY

run_test 32 "FFmpeg-Audio" "用 ffprobe 顯示 /tmp/tone440.wav 的詳細資訊"
sleep $RATE_DELAY

run_test 33 "FFmpeg-Audio" "用 FFmpeg 生成一個 C 大調音階（do re mi fa sol la si do），存到 /tmp/scale.wav"
sleep $RATE_DELAY

run_test 34 "FFmpeg-Video" "用 FFmpeg 生成一個 3 秒的彩色條紋測試影片，存到 /tmp/testbars.mp4"
sleep $RATE_DELAY

SID34=$(cat "$RESULTS_DIR/test_34_respid.txt")
run_test 35 "FFmpeg-Video" "把 /tmp/testbars.mp4 影片縮放到 320x240 存到 /tmp/testbars_small.mp4" "$SID34"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 8: FFmpeg Video (36-37), Combined (38-40) ==="

run_test 36 "FFmpeg-Video" "從 /tmp/testbars.mp4 影片提取第 1 秒的畫面存為 /tmp/frame1.png" "$SID34"
sleep $RATE_DELAY

run_test 37 "FFmpeg-Video" "用 ffprobe 顯示 /tmp/testbars.mp4 影片的 codec 和解析度資訊"
sleep $RATE_DELAY

run_test 38 "FFmpeg-Combined" "用 FFmpeg 生成一段有音效的測試影片（影片+音訊），存到 /tmp/testvideo_audio.mp4"
sleep $RATE_DELAY

SID38=$(cat "$RESULTS_DIR/test_38_respid.txt")
run_test 39 "FFmpeg-Combined" "從 /tmp/testvideo_audio.mp4 分離音訊軌存到 /tmp/extracted_audio.wav" "$SID38"
sleep $RATE_DELAY

run_test 40 "FFmpeg-Combined" "用 FFmpeg 先生成 5 張 PNG 圖片序列到 /tmp/frames/ 然後把它們組成影片 /tmp/slideshow.mp4"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 9: Combined OfficeCLI+FFmpeg (41-45) ==="

run_test 41 "Combined" "先用 FFmpeg 生成一段 3 秒的 880Hz 音訊到 /tmp/audio_880.wav，然後在 /tmp/audio_log.xlsx 的 Excel 裡記錄音檔名稱、長度、格式"
sleep $RATE_DELAY

run_test 42 "Combined" "建立一份 Word 報告 /tmp/ffmpeg_report.docx，內容描述 FFmpeg 可用的功能，至少列出 5 個常用指令"
sleep $RATE_DELAY

run_test 43 "Combined" "先用 FFmpeg 生成一個測試影片 /tmp/test_for_pptx.mp4，然後在 /tmp/video_spec.pptx 的 PowerPoint 裡記錄影片的解析度、codec、檔案大小"
sleep $RATE_DELAY

run_test 44 "Combined" "建立一個 Excel 追蹤表 /tmp/media_tracker.xlsx，列出 /tmp 底下所有的多媒體檔案（.wav .mp3 .mp4 .png），記錄檔名和檔案大小"
sleep $RATE_DELAY

run_test 45 "Combined" "執行 /opt/data/officecli/OfficeCLI --help 列出所有可用命令，然後把結果記錄在 /tmp/officecli_help.docx 裡"
sleep $RATE_DELAY

echo ""
echo "=== BATCH 10: Basic Agent Tests (46-50) ==="

run_test 46 "Basic" "你現在有哪些工具可以用？請列出所有可用的 CLI 工具路徑"
sleep $RATE_DELAY

run_test 47 "Basic" "搜尋網路上最新的 AI 新聞，列出 3 條"
sleep $RATE_DELAY

run_test 48 "Basic" "幫我寫一個 Python 腳本來分析 CSV 檔案，能讀取 /tmp/sales.csv 並計算總營收"
sleep $RATE_DELAY

run_test 49 "Basic" "用 Playwright 截取 https://www.google.com 的畫面存到 /tmp/google.png"
sleep $RATE_DELAY

run_test 50 "Basic" "你是誰？你的版本是什麼？你能做什麼？請詳細說明"
sleep $RATE_DELAY

# ═══════════════════════════════════════════════════════════════════════════════
# Generate final report
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "=============================================="
echo " Test Suite Complete: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=============================================="
echo ""

# Count results
TOTAL=$(tail -n +2 "$RESULTS_DIR/summary.csv" | wc -l)
PASS=$(tail -n +2 "$RESULTS_DIR/summary.csv" | grep '|PASS|' | wc -l)
FAIL=$(tail -n +2 "$RESULTS_DIR/summary.csv" | grep '|FAIL|' | wc -l)

echo "TOTAL: $TOTAL | PASS: $PASS | FAIL: $FAIL | RATE: $(( PASS * 100 / TOTAL ))%"
echo ""

# Per-category breakdown
echo "=== Per-Category Results ==="
for cat in Word Excel PowerPoint Cross-format FFmpeg-Audio FFmpeg-Video FFmpeg-Combined Combined Basic; do
  cat_total=$(tail -n +2 "$RESULTS_DIR/summary.csv" | grep "|$cat|" | wc -l)
  cat_pass=$(tail -n +2 "$RESULTS_DIR/summary.csv" | grep "|$cat|" | grep '|PASS|' | wc -l)
  if [[ $cat_total -gt 0 ]]; then
    echo "  $cat: $cat_pass/$cat_total ($(( cat_pass * 100 / cat_total ))%)"
  fi
done

echo ""
echo "=== Full Results Table ==="
echo "| # | Category | Message (first 40 chars) | Result | Response (first 100 chars) |"
echo "|---|----------|--------------------------|--------|----------------------------|"
while IFS='|' read -r num category msg result resp; do
  [[ "$num" == "num" ]] && continue
  printf "| %s | %s | %s | %s | %s |\n" "$num" "$category" "$msg" "$result" "$resp"
done < "$RESULTS_DIR/summary.csv"

echo ""
echo "Done. Raw responses in: $RESULTS_DIR/"
