#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"

section "Round 1: Infrastructure Health (12 tests)"

# 1.1 Gateway pod Running
echo "── 1.1 Gateway pod ──"
STATUS=$(kubectl -n "$NAMESPACE" get pods -l app=openclaw-gateway -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
READY=$(kubectl -n "$NAMESPACE" get pods -l app=openclaw-gateway -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>/dev/null)
[[ "$STATUS" == "Running" && "$READY" == "true" ]] && pass "Gateway pod Running (1/1)" || fail "Gateway pod" "status=$STATUS ready=$READY"

# 1.2 DB pod Running
echo "── 1.2 DB pod ──"
STATUS=$(kubectl -n "$NAMESPACE" get pods -l app=openclaw-db -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
[[ "$STATUS" == "Running" ]] && pass "DB pod Running" || fail "DB pod" "status=$STATUS"

# 1.3 Cloudflared pod Running
echo "── 1.3 Cloudflared pod ──"
STATUS=$(kubectl -n "$NAMESPACE" get pods -l app=cloudflared -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
[[ "$STATUS" == "Running" ]] && pass "Cloudflared pod Running" || fail "Cloudflared pod" "status=$STATUS"

# 1.4 Gateway service endpoint
echo "── 1.4 Gateway service endpoint ──"
EP=$(kubectl -n "$NAMESPACE" get endpoints openclaw-gateway-svc -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null)
[[ -n "$EP" ]] && pass "Gateway endpoint: $EP" || fail "Gateway endpoint" "no IP"

# 1.5 External HTTPS access (10 consecutive)
echo "── 1.5 External HTTPS ×10 ──"
OK=0
for i in $(seq 1 10); do
  CODE=$(http_code "$GATEWAY_URL/")
  [[ "$CODE" == "200" ]] && ((OK++))
  sleep 0.5
done
[[ $OK -eq 10 ]] && pass "External HTTPS 10/10" || fail "External HTTPS" "$OK/10 succeeded"

# 1.6 CF tunnel healthy, single client
echo "── 1.6 Tunnel health ──"
TUNNEL_JSON=$(curl -s "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/cfd_tunnel/${CF_TUNNEL_ID}" \
  -H "Authorization: Bearer ${CF_API_TOKEN}")
T_STATUS=$(echo "$TUNNEL_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['status'])")
T_CLIENTS=$(echo "$TUNNEL_JSON" | python3 -c "import sys,json; print(len(set(c['client_id'] for c in json.load(sys.stdin)['result'].get('connections',[]))))")
[[ "$T_STATUS" == "healthy" && "$T_CLIENTS" == "1" ]] && pass "Tunnel healthy, 1 client" || fail "Tunnel" "status=$T_STATUS clients=$T_CLIENTS"

# 1.7 DB connection
echo "── 1.7 DB connection ──"
kubectl -n "$NAMESPACE" exec deployment/openclaw-db -- pg_isready -U openclaw > /dev/null 2>&1 \
  && pass "DB pg_isready" || fail "DB connection" "pg_isready failed"

# 1.8 Gateway config valid
echo "── 1.8 Gateway config ──"
CFG=$(kexec cat /home/node/.openclaw/openclaw.json)
echo "$CFG" | python3 -c "import sys,json; c=json.load(sys.stdin); assert 'trustedProxies' in c.get('gateway',{})" 2>/dev/null \
  && pass "Config valid with trustedProxies" || fail "Config" "invalid JSON or missing trustedProxies"

# 1.9 Workspace files
echo "── 1.9 Workspace files ──"
FCOUNT=$(kexec sh -c 'ls /home/node/.openclaw/workspace/*.md 2>/dev/null | wc -l')
[[ "$FCOUNT" -ge 8 ]] && pass "Workspace: $FCOUNT files" || fail "Workspace files" "only $FCOUNT"

# 1.10 LINE channel running
echo "── 1.10 LINE channel ──"
CH=$(kexec openclaw channels status 2>&1 | grep "LINE default")
echo "$CH" | grep -q "running" && pass "LINE channel running" || fail "LINE channel" "$CH"

# 1.11 Cron scheduler
echo "── 1.11 Cron scheduler ──"
CRON=$(kexec openclaw cron status 2>&1)
echo "$CRON" | grep -q '"enabled": true' && pass "Cron enabled" || fail "Cron" "not enabled"
JOBS=$(echo "$CRON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('jobs',0))" 2>/dev/null)
[[ "$JOBS" -ge 3 ]] && pass "Cron jobs: $JOBS" || fail "Cron jobs" "only $JOBS"

# 1.12 Auth profiles
echo "── 1.12 Auth profiles ──"
AUTH=$(kexec cat /home/node/.openclaw/agents/main/agent/auth-profiles.json 2>/dev/null)
echo "$AUTH" | grep -q "openai" && pass "OpenAI auth configured" || fail "Auth profiles" "no openai key"

summary
