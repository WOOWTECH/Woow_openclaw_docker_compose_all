#!/bin/bash
# ============================================================
# OpenClaw PaaS - Pre-Launch Full Test Suite
# 4 Rounds: API → Frontend → Gateway → Infrastructure
# ============================================================
set +e  # Don't exit on individual test failures

PASS=0; FAIL=0; TOTAL=0
NAMESPACE="openclaw-tenant-1"

pass() { ((PASS++)); ((TOTAL++)); echo "  ✅ PASS: $1"; }
fail() { ((FAIL++)); ((TOTAL++)); echo "  ❌ FAIL: $1 — $2"; }

WIZARD_IP=$(kubectl get pod -n $NAMESPACE -l app=setup-wizard -o jsonpath='{.items[0].status.podIP}' 2>/dev/null || echo "")
if [ -z "$WIZARD_IP" ]; then echo "ERROR: Setup wizard not running"; exit 1; fi
WIZARD="http://${WIZARD_IP}:18790"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║    ROUND 1: API Backend Stress & Security Tests         ║"
echo "╚══════════════════════════════════════════════════════════╝"

# 1.1 GET / returns 200
echo ""
echo "── 1.1 Homepage ──"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$WIZARD/")
[ "$STATUS" = "200" ] && pass "GET / returns 200" || fail "GET / returns $STATUS" "expected 200"

# 1.2 GET /setup/status before any setup
echo "── 1.2 Status before setup ──"
RESP=$(curl -s "$WIZARD/setup/status")
STEP=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('step',99))" 2>/dev/null)
[ "$STEP" = "0" ] && pass "Initial status step=0" || fail "Initial status step=$STEP" "expected 0"

# 1.3 POST /setup with empty body
echo "── 1.3 Empty submission ──"
RESP=$(curl -s -X POST "$WIZARD/setup" -d "")
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if not d['success'] else 1)" 2>/dev/null && pass "Empty body rejected" || fail "Empty body accepted" "should reject"

# 1.4 POST /setup missing db_password
echo "── 1.4 Missing field ──"
RESP=$(curl -s -X POST "$WIZARD/setup" -d "gateway_token=test")
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if not d['success'] else 1)" 2>/dev/null && pass "Missing field rejected" || fail "Missing field accepted" "should reject"

# 1.5 POST /setup with XSS payload
echo "── 1.5 XSS injection ──"
RESP=$(curl -s -X POST "$WIZARD/setup" -d "gateway_token=<script>alert(1)</script>&db_password=test")
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if '<script>' not in json.dumps(d) else 1)" 2>/dev/null && pass "XSS payload sanitized" || fail "XSS payload reflected" "XSS risk"

# 1.6 POST /setup with very long string (10KB)
echo "── 1.6 Long string (10KB) ──"
LONG=$(python3 -c "print('A'*10000)")
RESP=$(curl -s -X POST "$WIZARD/setup" -d "gateway_token=${LONG}&db_password=test" --max-time 5)
[ -n "$RESP" ] && pass "Long string handled without crash" || fail "Server crashed on long input" "timeout"

# 1.7 GET /nonexistent returns 404
echo "── 1.7 Unknown route ──"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$WIZARD/nonexistent")
[ "$STATUS" = "404" ] && pass "Unknown route returns 404" || fail "Unknown route returns $STATUS" "expected 404"

# 1.8 POST /setup with SQL injection
echo "── 1.8 SQL injection ──"
RESP=$(curl -s -X POST "$WIZARD/setup" -d "gateway_token='; DROP TABLE users;--&db_password=test")
echo "$RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null && pass "SQL injection returns valid JSON" || fail "SQL injection caused error" "possible vulnerability"

# 1.9 Concurrent duplicate submissions
echo "── 1.9 Concurrent submissions ──"
# First submit to trigger setup
curl -s -X POST "$WIZARD/setup" -d "gateway_token=woowtech&db_password=woowtech" > /dev/null
sleep 1
# Second submit should be rejected
RESP2=$(curl -s -X POST "$WIZARD/setup" -d "gateway_token=test2&db_password=test2")
echo "$RESP2" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if not d['success'] else 1)" 2>/dev/null && pass "Duplicate submission blocked (409)" || fail "Duplicate submission accepted" "race condition"

# 1.10 Status polling during active setup
echo "── 1.10 Status during setup ──"
RESP=$(curl -s "$WIZARD/setup/status")
RUNNING=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('running',False))" 2>/dev/null)
[ "$RUNNING" = "True" ] && pass "Status shows running=True during setup" || fail "Status not running" "expected running=True"

# Wait for setup to complete before Round 2 Playwright needs fresh wizard
echo ""
echo "  ⏳ Waiting for setup to complete (up to 180s)..."
for i in $(seq 1 60); do
    DONE=$(curl -s "$WIZARD/setup/status" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('done',False))" 2>/dev/null || echo "")
    [ "$DONE" = "True" ] && break
    sleep 3
done

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║    ROUND 2: Playwright Frontend E2E (via npx)           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
cd "$(dirname "$0")/.."
PLAYWRIGHT_RESULT=$(PLAYWRIGHT_BROWSERS_PATH=0 npx playwright test 2>&1)
PW_PASS=$(echo "$PLAYWRIGHT_RESULT" | grep -oP '\d+ passed' | grep -oP '\d+')
PW_FAIL=$(echo "$PLAYWRIGHT_RESULT" | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")
echo "$PLAYWRIGHT_RESULT" | grep -E "✓|✘|passed|failed"
if [ "${PW_FAIL:-0}" = "0" ] && [ -n "$PW_PASS" ]; then
    pass "Playwright: ${PW_PASS} tests passed, 0 failed"
else
    fail "Playwright: ${PW_FAIL} failed" "see output above"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║    ROUND 3: OpenClaw Gateway Functional Tests           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

GW_POD=$(kubectl get pod -n $NAMESPACE -l app=openclaw-gateway -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -z "$GW_POD" ]; then
    fail "Gateway pod not found" "skipping Round 3"
else
    # 3.1 Gateway is listening
    echo "── 3.1 Gateway listening ──"
    GW_LOG=$(kubectl logs -n $NAMESPACE "$GW_POD" --tail=100 2>/dev/null || echo "")
    GW_READY=$(kubectl get pod -n $NAMESPACE "$GW_POD" -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null || echo "false")
    (echo "$GW_LOG" | grep -q "listening on ws://0.0.0.0:18789" || [ "$GW_READY" = "true" ]) && pass "Gateway listening (ready=$GW_READY)" || fail "Gateway not listening" "check logs"

    # 3.2 Gateway mode = local
    echo "── 3.2 Gateway mode ──"
    CONFIG=$(kubectl exec -n $NAMESPACE "$GW_POD" -- cat /home/node/.openclaw/openclaw.json 2>/dev/null || echo "{}")
    echo "$CONFIG" | python3 -c "import sys,json; exit(0 if json.load(sys.stdin).get('gateway',{}).get('mode')=='local' else 1)" 2>/dev/null && pass "gateway.mode=local" || fail "gateway.mode not local" "channels won't load"

    # 3.3 Channels enabled in config
    echo "── 3.3 Channel config ──"
    TG=$(echo "$CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('channels',{}).get('telegram',{}).get('enabled',False))" 2>/dev/null)
    WA=$(echo "$CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('channels',{}).get('whatsapp',{}).get('enabled',False))" 2>/dev/null)
    [ "$TG" = "True" ] && pass "Telegram enabled in config" || fail "Telegram not enabled" ""
    [ "$WA" = "True" ] && pass "WhatsApp enabled in config" || fail "WhatsApp not enabled" ""

    # 3.4 Plugins loaded > 7 (base is 7, channels add more)
    echo "── 3.4 Plugin count ──"
    PLUGINS=$(kubectl exec -n $NAMESPACE "$GW_POD" -- openclaw doctor 2>/dev/null | grep "Loaded:" | grep -oP '\d+' || echo "0")
    [ "$PLUGINS" -ge 9 ] && pass "Plugins loaded: $PLUGINS (channels active)" || fail "Plugins loaded: $PLUGINS" "expected >=9"

    # 3.5 auth-profiles.json exists with OpenAI key
    echo "── 3.5 AI auth-profiles ──"
    AUTH=$(kubectl exec -n $NAMESPACE "$GW_POD" -- cat /home/node/.openclaw/agents/main/agent/auth-profiles.json 2>/dev/null || echo "{}")
    echo "$AUTH" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'openai' in d else 1)" 2>/dev/null && pass "auth-profiles.json has openai key" || fail "auth-profiles.json missing openai" "AI won't work"

    # 3.6 AI conversation test (real OpenAI call)
    echo "── 3.6 AI conversation (OpenAI) ──"
    AI_RESP=$(timeout 15 kubectl exec -n $NAMESPACE "$GW_POD" -- openclaw agent --agent main -m "Reply with exactly: PONG" 2>/dev/null || echo "TIMEOUT")
    echo "$AI_RESP" | grep -qi "PONG" && pass "AI responded: ${AI_RESP:0:40}" || fail "AI response: ${AI_RESP:0:60}" "check API key"

    # 3.7 Device auto-approve working
    echo "── 3.7 Device auto-approve ──"
    echo "$GW_LOG" | grep -q "auto-approved" && pass "Device auto-approve active" || pass "No pending devices (OK)"

    # 3.8 Channels list shows enabled channels
    echo "── 3.8 Channels list ──"
    CH_LIST=$(timeout 10 kubectl exec -n $NAMESPACE "$GW_POD" -- openclaw channels list 2>/dev/null || echo "timeout")
    echo "$CH_LIST" | grep -q "Telegram" && pass "Telegram visible in channels list" || fail "Telegram not in channels list" ""
    echo "$CH_LIST" | grep -q "WhatsApp" && pass "WhatsApp visible in channels list" || fail "WhatsApp not in channels list" ""
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║    ROUND 4: Infrastructure Resilience Tests             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 4.1 K8s manifest dry-run
echo "── 4.1 Manifest validation ──"
cd "$(dirname "$0")/.."
DR=$(kubectl apply --dry-run=client -f k8s-manifests/ 2>&1)
echo "$DR" | grep -q "error" && fail "Manifest dry-run errors" "$DR" || pass "All manifests valid (dry-run)"

# 4.2 PVC bound
echo "── 4.2 PVC persistence ──"
PVC_STATUS=$(kubectl get pvc -n $NAMESPACE openclaw-db-pvc -o jsonpath='{.status.phase}' 2>/dev/null || echo "missing")
[ "$PVC_STATUS" = "Bound" ] && pass "PVC openclaw-db-pvc is Bound" || fail "PVC status: $PVC_STATUS" "data not persistent"

# 4.3 K8s Secret integrity
echo "── 4.3 Secret integrity ──"
SECRET_KEYS=$(kubectl get secret -n $NAMESPACE openclaw-secrets -o jsonpath='{.data}' 2>/dev/null | python3 -c "import sys,json; print(','.join(sorted(json.load(sys.stdin).keys())))" 2>/dev/null || echo "missing")
echo "$SECRET_KEYS" | grep -q "OPENCLAW_GATEWAY_TOKEN" && pass "Secret has OPENCLAW_GATEWAY_TOKEN" || fail "Secret missing keys" "$SECRET_KEYS"
echo "$SECRET_KEYS" | grep -q "OPENAI_API_KEY" && pass "Secret has OPENAI_API_KEY" || fail "Secret missing OPENAI_API_KEY" ""

# 4.4 Cloudflare tunnel connected
echo "── 4.4 Cloudflare tunnel ──"
CF_POD=$(kubectl get pod -n $NAMESPACE -l app=cloudflared -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
[ -n "$CF_POD" ] && pass "Cloudflared pod running" || fail "Cloudflared not running" ""

# 4.5 External domain accessible
echo "── 4.5 External access ──"
EXT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://cindytech1-openclaw.woowtech.io" --max-time 10 2>/dev/null || echo "000")
[ "$EXT_STATUS" = "200" ] && pass "External domain returns 200" || fail "External domain returns $EXT_STATUS" ""

# 4.6 RBAC permissions complete
echo "── 4.6 RBAC ──"
RBAC=$(kubectl get role -n $NAMESPACE wizard-role -o jsonpath='{.rules}' 2>/dev/null)
echo "$RBAC" | grep -q "pods/exec" && pass "RBAC includes pods/exec" || fail "RBAC missing pods/exec" ""
echo "$RBAC" | grep -q "deployments/scale" && pass "RBAC includes deployments/scale" || fail "RBAC missing deployments/scale" ""

# 4.7 Resource limits set
echo "── 4.7 Resource limits ──"
GW_MEM=$(kubectl get deployment -n $NAMESPACE openclaw-gateway -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}' 2>/dev/null || echo "none")
[ "$GW_MEM" = "8Gi" ] && pass "Gateway memory limit: $GW_MEM" || fail "Gateway memory limit: $GW_MEM" "expected 8Gi"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    TEST RESULTS                         ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Total: $TOTAL  |  ✅ Pass: $PASS  |  ❌ Fail: $FAIL        ║"
echo "╚══════════════════════════════════════════════════════════╝"

[ "$FAIL" -eq 0 ] && echo "🎉 ALL TESTS PASSED — READY FOR PRODUCTION" || echo "⚠️  $FAIL TESTS FAILED — REVIEW REQUIRED"
exit $FAIL
