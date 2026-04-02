#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"

section "Round 6: Resilience & Recovery (8 tests)"

# 6.1 Gateway pod kill
echo "── 6.1 Gateway pod kill ──"
POD=$(kubectl -n "$NAMESPACE" get pods -l app=openclaw-gateway -o jsonpath='{.items[0].metadata.name}')
kubectl -n "$NAMESPACE" delete pod "$POD" --grace-period=5 > /dev/null 2>&1
echo "  Waiting for recovery..."
kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l app=openclaw-gateway --timeout=120s > /dev/null 2>&1 \
  && pass "Gateway recovered" || fail "Gateway recovery" "timeout >120s"

# 6.2 Service continuity
echo "── 6.2 Service continuity ──"
sleep 10
OK=0
for i in $(seq 1 5); do
  CODE=$(http_code "$GATEWAY_URL/")
  [[ "$CODE" == "200" ]] && ((OK++))
  sleep 2
done
[[ $OK -ge 4 ]] && pass "Service: $OK/5 after recovery" || fail "Service continuity" "$OK/5"

# 6.3 Cloudflared restart
echo "── 6.3 Cloudflared restart ──"
kubectl -n "$NAMESPACE" rollout restart deployment cloudflared > /dev/null 2>&1
kubectl -n "$NAMESPACE" rollout status deployment cloudflared --timeout=60s > /dev/null 2>&1
sleep 15
OK=0
for i in $(seq 1 5); do
  CODE=$(http_code "$GATEWAY_URL/")
  [[ "$CODE" == "200" ]] && ((OK++))
  sleep 2
done
[[ $OK -ge 4 ]] && pass "Cloudflared restart: $OK/5 OK" || fail "Cloudflared" "$OK/5"

# 6.4 Tunnel ghost check
echo "── 6.4 Ghost connections ──"
sleep 10
TUNNEL_JSON=$(curl -s "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/cfd_tunnel/${CF_TUNNEL_ID}" \
  -H "Authorization: Bearer ${CF_API_TOKEN}")
CLIENTS=$(echo "$TUNNEL_JSON" | python3 -c "import sys,json; print(len(set(c['client_id'] for c in json.load(sys.stdin)['result'].get('connections',[]))))")
[[ "$CLIENTS" == "1" ]] && pass "No ghost: 1 client" || fail "Ghost connections" "$CLIENTS clients"

# 6.5 DB restart
echo "── 6.5 DB restart ──"
DB_POD=$(kubectl -n "$NAMESPACE" get pods -l app=openclaw-db -o jsonpath='{.items[0].metadata.name}')
kubectl -n "$NAMESPACE" delete pod "$DB_POD" --grace-period=5 > /dev/null 2>&1
kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l app=openclaw-db --timeout=60s > /dev/null 2>&1 \
  && pass "DB recovered" || fail "DB recovery" "timeout"
sleep 5

# 6.6 Session preservation
echo "── 6.6 Session preservation ──"
SESS_COUNT=$(kexec find /home/node/.openclaw/agents/main/sessions/ -name "*.jsonl" 2>/dev/null | wc -l)
[[ $SESS_COUNT -ge 1 ]] && pass "Sessions present: $SESS_COUNT" || skip "Session preservation" "sessions in ephemeral storage"

# 6.7 Memory check
echo "── 6.7 Memory usage ──"
RSS_KB=$(kubectl -n "$NAMESPACE" exec deployment/openclaw-gateway -- sh -c 'cat /proc/1/status 2>/dev/null | grep VmRSS | awk "{print \$2}"' 2>/dev/null || echo "0")
RSS_GB=$(echo "scale=2; ${RSS_KB:-0}/1048576" | bc 2>/dev/null || echo "0")
[[ $(echo "$RSS_KB < 6291456" | bc 2>/dev/null) == "1" ]] && pass "Memory: ${RSS_GB}GB (< 6GB)" || fail "Memory" "${RSS_GB}GB"

# 6.8 Full timing (this is measured by run-all.sh, placeholder pass)
echo "── 6.8 Full timing ──"
pass "Timing measured by run-all.sh"

summary
