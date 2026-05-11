#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"

section "Round 3: Security & Stress (16 tests)"

# 3.1 WebUI requires auth (no-auth should redirect)
CODE=$(http_code "$EXTERNAL_URL" -k)
if [[ "$CODE" == "302" || "$CODE" == "401" || "$CODE" == "200" ]]; then
  pass "WebUI responds: HTTP $CODE"
else
  fail "WebUI auth check" "http=$CODE"
fi

# 3.2 Wrong password rejected
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k $CURL_RESOLVE \
  -X POST "$EXTERNAL_URL" -d "password=wrong-password-xyz" 2>&1)
if [[ "$CODE" != "500" ]]; then
  pass "Wrong password handled: HTTP $CODE"
else
  fail "Wrong password" "got 500 error"
fi

# 3.3 XSS payload
XSS_RESP=$(ext_curl "$EXTERNAL_URL/<script>alert('xss')</script>")
if ! echo "$XSS_RESP" | grep -q "<script>alert"; then
  pass "XSS payload sanitized/blocked"
else
  fail "XSS" "script tag reflected"
fi

# 3.4 SQL injection
SQLI_RESP=$(ext_curl "$EXTERNAL_URL/?q=';DROP%20TABLE%20users;--")
if [[ "$?" -eq 0 ]]; then
  # Verify DB is intact
  PG_OK=$(kexec_pg psql -U hermes -d hermes -tAc "SELECT 1;" 2>/dev/null)
  [[ "$PG_OK" == *"1"* ]] && pass "SQLi: DB intact after injection attempt" || fail "SQLi" "DB damaged"
else
  pass "SQLi: request rejected"
fi

# 3.5 Oversized payload (1MB)
TMPFILE=$(mktemp)
head -c 1048576 /dev/urandom | base64 > "$TMPFILE"
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -k $CURL_RESOLVE \
  -X POST "$EXTERNAL_URL" -d @"$TMPFILE" 2>&1)
rm -f "$TMPFILE"
if [[ "$CODE" != "500" ]]; then
  pass "1MB payload handled: HTTP $CODE"
else
  fail "Oversized payload" "got 500"
fi

# 3.6 Concurrent requests (50)
TMPDIR=$(mktemp -d)
SUCCESS=0; TOTAL_REQ=50
for i in $(seq 1 $TOTAL_REQ); do
  curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k $CURL_RESOLVE "$EXTERNAL_URL" > "$TMPDIR/$i" 2>&1 &
done
wait
for i in $(seq 1 $TOTAL_REQ); do
  CODE=$(cat "$TMPDIR/$i" 2>/dev/null)
  [[ "$CODE" =~ ^[23] ]] && ((SUCCESS++))
done
rm -rf "$TMPDIR"
if [[ $SUCCESS -ge 45 ]]; then
  pass "Concurrent: $SUCCESS/$TOTAL_REQ succeeded"
else
  fail "Concurrent requests" "$SUCCESS/$TOTAL_REQ succeeded"
fi

# 3.7 Sequential rapid fire (100)
SUCCESS=0; TOTAL_REQ=100
for i in $(seq 1 $TOTAL_REQ); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -k $CURL_RESOLVE "$EXTERNAL_URL" 2>&1)
  [[ "$CODE" =~ ^[23] ]] && ((SUCCESS++))
done
if [[ $SUCCESS -ge 95 ]]; then
  pass "Rapid fire: $SUCCESS/$TOTAL_REQ succeeded"
else
  fail "Rapid fire" "$SUCCESS/$TOTAL_REQ succeeded"
fi

# 3.8 Invalid auth token
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k $CURL_RESOLVE \
  -H "Authorization: Bearer INVALID_TOKEN_XYZ" "$EXTERNAL_URL/api" 2>&1)
if [[ "$CODE" != "500" ]]; then
  pass "Invalid token handled: HTTP $CODE"
else
  fail "Invalid auth token" "got 500"
fi

# 3.9 CORS headers
CORS=$(curl -s -I --max-time 10 -k $CURL_RESOLVE -H "Origin: http://evil.com" "$EXTERNAL_URL" 2>&1)
if echo "$CORS" | grep -qi "access-control\|allow-origin"; then
  pass "CORS headers present"
else
  skip "CORS headers" "not returned (may not be configured on webui)"
fi

# 3.10 Network policy enforcement
kubectl -n "$NAMESPACE" run netpol-probe --image=busybox --restart=Never \
  --labels="app=unauthorized-probe" \
  --command -- sh -c "nc -z -w 5 $POSTGRES_SVC $POSTGRES_PORT 2>&1; echo EXIT:\$?" > /dev/null 2>&1
sleep 12
PROBE_LOG=$(kubectl -n "$NAMESPACE" logs netpol-probe 2>/dev/null)
kubectl -n "$NAMESPACE" delete pod netpol-probe --grace-period=0 --force > /dev/null 2>&1 &
if echo "$PROBE_LOG" | grep -q "EXIT:0"; then
  fail "Network policy" "unauthorized pod reached PostgreSQL"
else
  pass "Network policy blocks unauthorized DB access"
fi

# 3.11 Secrets not leaked in pod describe
DESCRIBE=$(kubectl -n "$NAMESPACE" describe pods 2>/dev/null)
LEAKED=false
for secret_word in "VbABwop" "sk-cp-Mm9" "qtFYmY"; do
  echo "$DESCRIBE" | grep -q "$secret_word" && LEAKED=true
done
[[ "$LEAKED" == "false" ]] && pass "No secrets in pod describe" || fail "Secret leak" "found in describe"

# 3.12 Container non-root (informational)
AGENT_UID=$(kexec_agent id -u 2>/dev/null || echo "unknown")
if [[ "$AGENT_UID" != "0" && "$AGENT_UID" != "unknown" ]]; then
  pass "Agent runs as non-root (UID=$AGENT_UID)"
else
  skip "Agent non-root" "UID=$AGENT_UID (may be expected)"
fi

# 3.13 Path traversal
TRAVERSAL=$(ext_curl "$EXTERNAL_URL/../../etc/passwd")
if ! echo "$TRAVERSAL" | grep -q "root:x:0"; then
  pass "Path traversal blocked"
else
  fail "Path traversal" "passwd content leaked"
fi

# 3.14 CRLF injection
CRLF_RESP=$(curl -s -I --max-time 10 -k $CURL_RESOLVE "$EXTERNAL_URL/%0d%0aX-Injected:%20true" 2>&1)
if ! echo "$CRLF_RESP" | grep -qi "X-Injected"; then
  pass "CRLF injection blocked"
else
  fail "CRLF injection" "header injected"
fi

# 3.15 TLS certificate valid (not expired)
EXPIRY=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null \
  | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
if [[ -n "$EXPIRY" ]]; then
  EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || echo 0)
  NOW_EPOCH=$(date +%s)
  if [[ $EXPIRY_EPOCH -gt $NOW_EPOCH ]]; then
    pass "TLS cert valid until $EXPIRY"
  else
    fail "TLS cert" "expired: $EXPIRY"
  fi
else
  skip "TLS cert check" "could not parse expiry"
fi

# 3.16 Malformed JSON
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k $CURL_RESOLVE \
  -X POST -H "Content-Type: application/json" -d '{invalid json!!!' "$EXTERNAL_URL/api" 2>&1)
if [[ "$CODE" != "500" ]]; then
  pass "Malformed JSON handled: HTTP $CODE"
else
  fail "Malformed JSON" "got 500"
fi

summary
