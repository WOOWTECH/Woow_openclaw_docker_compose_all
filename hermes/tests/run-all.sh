#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/report.sh"

RESULTS_LOG="/tmp/hermes-test-results.log"
export RESULTS_LOG NAMESPACE
> "$RESULTS_LOG"

START_TIME=$(date +%s)
echo ""
echo "============================================================"
echo "  Hermes Enterprise Test Suite -- 7 Rounds + Playwright"
echo "  $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

TOTAL_PASS=0; TOTAL_FAIL=0; TOTAL_SKIP=0

run_round() {
  local script="$1" name="$2"
  echo ""
  echo ">> Starting: $name"
  PASS=0; FAIL=0; SKIP=0; TOTAL=0
  source "$SCRIPT_DIR/lib/assert.sh"
  bash "$script"
  TOTAL_PASS=$((TOTAL_PASS + PASS))
  TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
  TOTAL_SKIP=$((TOTAL_SKIP + SKIP))
  echo "  -- $name: $PASS pass / $FAIL fail / $SKIP skip --"
}

run_round "$SCRIPT_DIR/round1-infra.sh"       "Round 1: Infrastructure Health"
run_round "$SCRIPT_DIR/round2-api.sh"          "Round 2: Backend API"
run_round "$SCRIPT_DIR/round3-security.sh"     "Round 3: Security & Stress"
run_round "$SCRIPT_DIR/round4-resilience.sh"   "Round 4: Resilience & Recovery"
run_round "$SCRIPT_DIR/round5-integration.sh"  "Round 5: Cross-Service Integration"
run_round "$SCRIPT_DIR/round6-llm-integration.sh" "Round 6: LLM Integration & Gateway"
run_round "$SCRIPT_DIR/round7-webui-features.sh"   "Round 7: WebGUI Features"

# Playwright (optional — uses port-forward for local access)
echo ""
echo ">> Starting: Playwright Browser Tests"
if command -v npx &> /dev/null; then
  # Start port-forward in background (kept alive for ALL Playwright suites)
  kubectl -n "$NAMESPACE" port-forward svc/hermes-webui-svc 18787:8787 &>/dev/null &
  PF_PID=$!
  sleep 3
  export HERMES_TEST_URL="http://localhost:18787"

  # Suite 1: Basic WebUI E2E (12 tests)
  cd "$SCRIPT_DIR/../../" && npx playwright test \
    --config hermes/tests/playwright/playwright.config.mjs \
    hermes/tests/playwright/hermes-webui.spec.mjs 2>&1 | tail -20
  PW_EXIT=$?
  if [[ $PW_EXIT -eq 0 ]]; then
    echo "PASS|Playwright GUI suite (12 tests)" >> "$RESULTS_LOG"
    ((TOTAL_PASS++))
  else
    echo "FAIL|Playwright GUI suite|exit=$PW_EXIT" >> "$RESULTS_LOG"
    ((TOTAL_FAIL++))
  fi

  # Suite 2: Feature Verification E2E (18 tests)
  cd "$SCRIPT_DIR/../../" && npx playwright test \
    --config hermes/tests/playwright/playwright.config.mjs \
    hermes/tests/playwright/hermes-webui-features.spec.mjs 2>&1 | tail -20
  FEAT_EXIT=$?
  if [[ $FEAT_EXIT -eq 0 ]]; then
    echo "PASS|Playwright Feature suite (18 tests)" >> "$RESULTS_LOG"
    ((TOTAL_PASS++))
  else
    echo "FAIL|Playwright Feature suite|exit=$FEAT_EXIT" >> "$RESULTS_LOG"
    ((TOTAL_FAIL++))
  fi

  # Now kill port-forward after ALL suites complete
  kill $PF_PID 2>/dev/null; wait $PF_PID 2>/dev/null
else
  echo "SKIP|Playwright|npx not found" >> "$RESULTS_LOG"
  ((TOTAL_SKIP++))
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

GRAND_TOTAL=$((TOTAL_PASS + TOTAL_FAIL + TOTAL_SKIP))
echo ""
echo "============================================================"
echo "  FINAL RESULTS"
echo "  Pass: $TOTAL_PASS  |  Fail: $TOTAL_FAIL  |  Skip: $TOTAL_SKIP  |  Total: $GRAND_TOTAL"
echo "  Duration: ${DURATION}s"
if [[ $GRAND_TOTAL -gt 0 ]]; then
  PASS_RATE=$((TOTAL_PASS * 100 / GRAND_TOTAL))
  echo "  Pass Rate: ${PASS_RATE}%"
fi
echo "============================================================"

REPORT_FILE="$SCRIPT_DIR/report-$(date +%Y-%m-%d).html"
generate_html_report "$RESULTS_LOG" "$REPORT_FILE"
echo "HTML report: $REPORT_FILE"

[[ $DURATION -le 1800 ]] && echo "Suite completed within 30min" \
  || echo "Warning: Suite took ${DURATION}s (>30min)"
exit $TOTAL_FAIL
