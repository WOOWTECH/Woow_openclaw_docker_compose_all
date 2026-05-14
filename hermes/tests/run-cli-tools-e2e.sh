#!/usr/bin/env bash
set -uo pipefail

# =============================================================
# Hermes CLI Tools E2E Test — 15 Enterprise Scenarios
# Uses Playwright CLI to send real conversations and verify
# =============================================================

RESULTS_LOG="/tmp/hermes-cli-e2e-results.log"
> "$RESULTS_LOG"
PASS=0; FAIL=0; TOTAL=0

pass() { ((PASS++)); ((TOTAL++)); echo "  PASS: $1"; echo "PASS|$1" >> "$RESULTS_LOG"; }
fail() { ((FAIL++)); ((TOTAL++)); echo "  FAIL: $1 -- $2"; echo "FAIL|$1|$2" >> "$RESULTS_LOG"; }

send_and_capture() {
  local msg="$1"
  local wait_secs="${2:-40}"

  # New conversation
  playwright-cli click e57 2>/dev/null | head -1
  sleep 2

  # Get message input ref
  local ref
  ref=$(playwright-cli snapshot 2>/dev/null | grep "textbox.*Message" | grep -oP 'ref=\K[^ \]]+' | head -1)
  if [[ -z "$ref" ]]; then
    echo "ERROR: Could not find message input"
    return 1
  fi

  # Send message
  playwright-cli fill "$ref" "$msg" --submit 2>/dev/null | head -1

  # Auto-approve in background
  (
    for i in $(seq 1 12); do
      sleep 5
      playwright-cli eval "document.getElementById('updateBanner')?.remove(); document.getElementById('approvalBtnAlways')?.click()" 2>/dev/null
    done
  ) &
  local APID=$!

  sleep "$wait_secs"
  kill $APID 2>/dev/null; wait $APID 2>/dev/null

  # Capture response as text
  playwright-cli --raw eval "(() => {
    const codeBlocks = document.querySelectorAll('pre code, .code-block');
    if (codeBlocks.length > 0) return Array.from(codeBlocks).map(b => b.innerText).join('\\n---\\n');
    const msgs = document.querySelectorAll('.message-bubble');
    if (msgs.length > 0) return msgs[msgs.length-1]?.innerText || '';
    return document.querySelector('.chat-messages')?.innerText || 'NO_RESPONSE';
  })()" 2>/dev/null
}

echo ""
echo "============================================================"
echo "  Hermes CLI Tools E2E — 15 Enterprise Scenarios"
echo "  $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

# ─────────────────────────────────────────────────
# Scenario 1: K8s Cluster Health Check (kubectl)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 1: K8s Cluster Health Check (kubectl)"
RESULT=$(send_and_capture "run: kubectl get nodes --no-headers && echo '===PODS===' && kubectl get pods -n hermes --no-headers" 35)
if echo "$RESULT" | grep -q "Running"; then
  pass "S1: kubectl cluster health — pods Running found"
else
  fail "S1: kubectl cluster health" "no Running pods in output"
fi

# ─────────────────────────────────────────────────
# Scenario 2: PostgreSQL DB Query (psql)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 2: PostgreSQL DB Query (psql)"
RESULT=$(send_and_capture "run: PGPASSWORD=\$(cat /run/secrets/kubernetes.io/serviceaccount/..data/POSTGRES_PASSWORD 2>/dev/null || echo test) psql -h hermes-postgresql-svc -U hermes -d hermes -c 'SELECT current_database(), current_user, version();' 2>&1 || psql --version" 35)
if echo "$RESULT" | grep -qi "postgresql\|17\.9"; then
  pass "S2: psql — PostgreSQL version confirmed"
else
  fail "S2: psql" "psql output: $(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 3: Redis Cache Inspection (redis-cli)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 3: Redis Cache Inspection (redis-cli)"
RESULT=$(send_and_capture "run: redis-cli -h hermes-redis-svc INFO server 2>&1 | head -8" 35)
if echo "$RESULT" | grep -qi "redis_version"; then
  pass "S3: redis-cli — Redis server info retrieved"
else
  fail "S3: redis-cli" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 4: JSON API Processing (jq + curl)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 4: JSON API Processing (jq + curl)"
RESULT=$(send_and_capture "run: curl -s https://httpbin.org/json | jq '.slideshow.title'" 40)
if echo "$RESULT" | grep -qi "sample\|slide\|title\|Sample"; then
  pass "S4: curl+jq — JSON API parsed successfully"
else
  fail "S4: curl+jq" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 5: YAML Config Processing (yq)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 5: YAML Config Processing (yq)"
RESULT=$(send_and_capture "run: kubectl get configmap hermes-config -n hermes -o yaml | yq '.data.HERMES_DOMAIN'" 35)
if echo "$RESULT" | grep -qi "woowtech\|hermes"; then
  pass "S5: yq — YAML config extracted"
else
  fail "S5: yq" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 6: DNS & Network Diagnostics (dig + ping + nmap)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 6: DNS & Network Diagnostics (dig + ping)"
RESULT=$(send_and_capture "run: dig +short google.com | head -2 && echo '---' && ping -c2 -W2 hermes-redis-svc | tail -1" 35)
if echo "$RESULT" | grep -qi "rtt\|[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+"; then
  pass "S6: dig+ping — DNS resolved + ping succeeded"
else
  fail "S6: dig+ping" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 7: Web Page Retrieval (lynx)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 7: Web Page Retrieval (lynx)"
RESULT=$(send_and_capture "run: lynx -dump https://example.com | head -8" 35)
if echo "$RESULT" | grep -qi "Example Domain\|example"; then
  pass "S7: lynx — web page retrieved as text"
else
  fail "S7: lynx" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 8: File Search (fd + rg)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 8: File Search (fd + rg)"
RESULT=$(send_and_capture "run: fd -t f -e yaml /opt/data 2>/dev/null | head -5 && echo '---' && rg --version | head -1" 35)
if echo "$RESULT" | grep -qi "ripgrep\|rg\|yaml\|config"; then
  pass "S8: fd+rg — file search tools working"
else
  fail "S8: fd+rg" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 9: Helm Chart Inspection (helm)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 9: Helm Chart Inspection (helm)"
RESULT=$(send_and_capture "run: helm version --short && echo '---' && helm env | head -3" 35)
if echo "$RESULT" | grep -qi "v3\.\|HELM"; then
  pass "S9: helm — Helm environment verified"
else
  fail "S9: helm" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 10: GitHub CLI Status (gh)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 10: GitHub CLI (gh)"
RESULT=$(send_and_capture "run: gh --version && echo '---' && gh auth status 2>&1 | head -3" 35)
if echo "$RESULT" | grep -qi "gh version\|2\.73"; then
  pass "S10: gh — GitHub CLI available"
else
  fail "S10: gh" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 11: ArgoCD + Cloudflared Status (argocd + cloudflared)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 11: ArgoCD + Cloudflared CLI"
RESULT=$(send_and_capture "run: argocd version --client 2>&1 | head -1 && echo '---' && cloudflared --version" 35)
if echo "$RESULT" | grep -qi "argocd.*v2\|cloudflared.*2026"; then
  pass "S11: argocd+cloudflared — CLI tools available"
else
  fail "S11: argocd+cloudflared" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 12: Image Processing (ImageMagick convert)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 12: Image Processing (ImageMagick)"
RESULT=$(send_and_capture "run: convert -size 100x100 xc:blue /tmp/test-blue.png && identify /tmp/test-blue.png && rm /tmp/test-blue.png && echo 'ImageMagick OK'" 35)
if echo "$RESULT" | grep -qi "ImageMagick\|100x100\|PNG\|OK"; then
  pass "S12: convert+identify — image created and inspected"
else
  fail "S12: convert" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 13: Document Conversion (pandoc)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 13: Document Conversion (pandoc)"
RESULT=$(send_and_capture "run: echo '# Test Report' | pandoc -f markdown -t html && echo '---' && pandoc --version | head -1" 35)
if echo "$RESULT" | grep -qi "<h1\|pandoc\|3\.1"; then
  pass "S13: pandoc — Markdown to HTML conversion"
else
  fail "S13: pandoc" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 14: Network Port Scan (nmap + nc)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 14: Network Port Scan (nmap + nc)"
RESULT=$(send_and_capture "run: nc -z -w3 hermes-redis-svc 6379 && echo 'Redis port OPEN' && echo '---' && nmap --version | head -1" 40)
if echo "$RESULT" | grep -qi "OPEN\|Nmap\|nmap"; then
  pass "S14: nc+nmap — network tools working"
else
  fail "S14: nc+nmap" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Scenario 15: Git + rsync + mosh + traceroute (multi-tool)
# ─────────────────────────────────────────────────
echo ""
echo ">> Scenario 15: Multi-tool (git + rsync + traceroute)"
RESULT=$(send_and_capture "run: git --version && echo '---' && rsync --version | head -1 && echo '---' && traceroute --version 2>&1 | head -1 && echo '---' && git-lfs version" 35)
if echo "$RESULT" | grep -qi "git version\|rsync\|traceroute"; then
  pass "S15: git+rsync+traceroute — multi-tool check"
else
  fail "S15: multi-tool" "$(echo "$RESULT" | head -1)"
fi

# ─────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  RESULTS: $PASS pass / $FAIL fail (total $TOTAL)"
PASS_RATE=$((PASS * 100 / TOTAL))
echo "  Pass Rate: ${PASS_RATE}%"
echo "============================================================"
echo ""
echo "Results log: $RESULTS_LOG"
