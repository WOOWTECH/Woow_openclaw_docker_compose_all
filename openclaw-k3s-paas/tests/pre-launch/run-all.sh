#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/report.sh"

RESULTS_LOG="/tmp/pre-launch-results.log"
export RESULTS_LOG
> "$RESULTS_LOG"

START_TIME=$(date +%s)
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     OpenClaw Pre-Launch Test Suite — 6 Rounds           ║"
echo "║     $(date -u +"%Y-%m-%d %H:%M:%S UTC")                          ║"
echo "╚══════════════════════════════════════════════════════════╝"

TOTAL_PASS=0; TOTAL_FAIL=0; TOTAL_SKIP=0

run_round() {
  local script="$1"
  local name="$2"
  echo ""
  echo "▶ Starting: $name"
  PASS=0; FAIL=0; SKIP=0; TOTAL=0
  source "$SCRIPT_DIR/lib/assert.sh"
  bash "$script"
  TOTAL_PASS=$((TOTAL_PASS + PASS))
  TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
  TOTAL_SKIP=$((TOTAL_SKIP + SKIP))
  echo "  ── $name: $PASS pass / $FAIL fail / $SKIP skip ──"
}

run_round "$SCRIPT_DIR/round1-infra.sh"     "Round 1: Infrastructure"
run_round "$SCRIPT_DIR/round2-security.sh"   "Round 2: Security"
run_round "$SCRIPT_DIR/round3-llm-switch.sh" "Round 3: LLM Switch"
run_round "$SCRIPT_DIR/round4-channel.sh"    "Round 4: LINE Channel"
run_round "$SCRIPT_DIR/round5-features.sh"   "Round 5: Features"
run_round "$SCRIPT_DIR/round6-resilience.sh" "Round 6: Resilience"

# Playwright (optional — skip if not installed)
echo ""
echo "▶ Starting: Playwright GUI Tests"
if command -v npx &> /dev/null; then
  cd "$SCRIPT_DIR/../../" && npx playwright test --config tests/pre-launch/playwright/playwright.config.mjs 2>&1 | tail -5
  PW_EXIT=$?
  [[ $PW_EXIT -eq 0 ]] && echo "PASS|Playwright GUI suite" >> "$RESULTS_LOG" && ((TOTAL_PASS++)) \
    || echo "FAIL|Playwright GUI suite|exit=$PW_EXIT" >> "$RESULTS_LOG" && ((TOTAL_FAIL++))
else
  echo "SKIP|Playwright|npx not found" >> "$RESULTS_LOG"
  ((TOTAL_SKIP++))
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              FINAL RESULTS                              ║"
echo "║  ✅ Pass: $TOTAL_PASS  |  ❌ Fail: $TOTAL_FAIL  |  ⏭️ Skip: $TOTAL_SKIP     ║"
echo "║  Duration: ${DURATION}s                                        ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Generate HTML report
REPORT_FILE="$SCRIPT_DIR/report-$(date +%Y-%m-%d).html"
generate_html_report "$RESULTS_LOG" "$REPORT_FILE"

[[ $DURATION -le 1800 ]] && echo "✅ Suite completed within 30min" || echo "⚠️ Suite took ${DURATION}s (>30min)"
exit $TOTAL_FAIL
