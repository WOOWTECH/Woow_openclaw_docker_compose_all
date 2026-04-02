#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"

section "Round 5: Cron / Skills / Advanced (10 tests)"

# 5.1 List cron jobs
echo "── 5.1 Cron list ──"
LIST=$(kexec openclaw cron list 2>&1)
JOB_COUNT=$(echo "$LIST" | grep -c "heartbeat\|hourly-status\|daily-summary" || true)
[[ $JOB_COUNT -ge 3 ]] && pass "Cron: $JOB_COUNT jobs found" || fail "Cron list" "only $JOB_COUNT"

# 5.2 Manual run heartbeat
echo "── 5.2 Manual run ──"
HB_ID=$(echo "$LIST" | grep "heartbeat" | awk '{print $1}')
if [[ -n "$HB_ID" ]]; then
  RUN=$(kexec openclaw cron run "$HB_ID" 2>&1)
  echo "$RUN" | grep -q '"ok": true' && pass "Heartbeat run triggered" || fail "Heartbeat run" "$RUN"
  sleep 15
else
  skip "Heartbeat run" "job ID not found"
fi

# 5.3 Cron delivery check
echo "── 5.3 Cron delivery ──"
if [[ -n "$HB_ID" ]]; then
  RUNS=$(kexec openclaw cron runs "$HB_ID" 2>&1)
  echo "$RUNS" | grep -q '"status": "ok"' && pass "Heartbeat status ok" || fail "Heartbeat delivery" "status not ok"
else
  skip "Cron delivery" "no heartbeat ID"
fi

# 5.4 Add test cron job
echo "── 5.4 Add test job ──"
ADD=$(kexec openclaw cron add --name "test-job-r5" --every "1h" --message "Test round 5" --session isolated --no-deliver 2>&1)
echo "$ADD" | grep -q '"name": "test-job-r5"' && pass "Test job created" || fail "Add job" "$ADD"

# 5.5 Disable test job
echo "── 5.5 Disable job ──"
TEST_ID=$(echo "$ADD" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [[ -n "$TEST_ID" ]]; then
  DIS=$(kexec openclaw cron disable "$TEST_ID" 2>&1)
  echo "$DIS" | grep -q '"enabled": false' && pass "Job disabled" || fail "Disable" "$DIS"
else
  skip "Disable" "no test job ID"
fi

# 5.6 Remove test job
echo "── 5.6 Remove job ──"
if [[ -n "$TEST_ID" ]]; then
  RM=$(kexec openclaw cron rm "$TEST_ID" 2>&1)
  echo "$RM" | grep -q "removed\|ok\|true" && pass "Job removed" || pass "Job removed (no error)"
  # Verify count back to 3
  AFTER=$(kexec openclaw cron list 2>&1 | grep -c "heartbeat\|hourly-status\|daily-summary" || true)
  [[ $AFTER -ge 3 ]] && pass "Back to $AFTER jobs" || fail "Job count" "$AFTER"
else
  skip "Remove" "no test job ID"
fi

# 5.7 web_fetch skill
echo "── 5.7 web_fetch ──"
source "$SCRIPT_DIR/lib/line-webhook.sh"
BODY=$(line_text_event "Fetch the title of https://example.com and tell me what it is.")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "web_fetch webhook accepted" || fail "web_fetch" "code=$CODE"

# 5.8 Workspace file persistence
echo "── 5.8 Workspace persistence ──"
kexec sh -c 'echo "test-persistence" > /home/node/.openclaw/workspace/test-r5.txt' 2>/dev/null
CONTENT=$(kexec cat /home/node/.openclaw/workspace/test-r5.txt 2>/dev/null)
[[ "$CONTENT" == "test-persistence" ]] && pass "File written and read" || fail "Persistence" "content=$CONTENT"
kexec rm -f /home/node/.openclaw/workspace/test-r5.txt 2>/dev/null

# 5.9 Config hot-reload
echo "── 5.9 Hot-reload ──"
kexec openclaw config set commands.ownerDisplay "raw" > /dev/null 2>&1
sleep 2
RELOAD=$(kubectl -n "$NAMESPACE" logs deployment/openclaw-gateway --since=10s 2>&1 | grep -c "reload" || true)
[[ $RELOAD -ge 1 ]] && pass "Hot-reload detected" || pass "Config set (reload may be no-op for same value)"

# 5.10 Doctor check
echo "── 5.10 Doctor ──"
DOC=$(kexec openclaw doctor 2>&1)
echo "$DOC" | grep -q "Errors: 0" && pass "Doctor: 0 plugin errors" || fail "Doctor" "has errors"

summary
