#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"
source "$SCRIPT_DIR/lib/line-webhook.sh"

section "Round 2: Security & Stress (15 tests)"

WEBHOOK="${GATEWAY_URL}/line/webhook"

# 2.1 XSS in webhook body
echo "── 2.1 XSS injection ──"
BODY=$(line_text_event '<script>alert("xss")</script>')
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "XSS payload accepted safely" || fail "XSS" "code=$CODE"

# 2.2 SQL injection
echo "── 2.2 SQL injection ──"
BODY=$(line_text_event "'; DROP TABLE users; --")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "SQL injection handled" || fail "SQLi" "code=$CODE"

# 2.3 Invalid signature
echo "── 2.3 Invalid signature ──"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" -H "x-line-signature: INVALIDSIG==" \
  -d '{"events":[]}')
[[ "$CODE" == "400" || "$CODE" == "401" ]] && pass "Invalid sig rejected ($CODE)" || fail "Invalid sig" "code=$CODE"

# 2.4 Empty signature
echo "── 2.4 Empty signature ──"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" -d '{"events":[]}')
[[ "$CODE" == "400" || "$CODE" == "401" ]] && pass "No sig rejected ($CODE)" || fail "No sig" "code=$CODE"

# 2.5 Oversized payload (1MB)
echo "── 2.5 1MB payload ──"
BIG=$(python3 -c "print('{\"events\":[{\"text\":\"' + 'A'*1000000 + '\"}]}')")
SIG=$(echo -n "$BIG" | openssl dgst -sha256 -hmac "$LINE_CHANNEL_SECRET" -binary | base64)
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" -H "x-line-signature: $SIG" \
  --max-time 10 -d "$BIG" 2>/dev/null)
[[ "$CODE" =~ ^(200|400|413)$ ]] && pass "1MB payload handled ($CODE)" || fail "1MB payload" "code=$CODE"

# 2.6 Malformed JSON
echo "── 2.6 Malformed JSON ──"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" -H "x-line-signature: dummy" \
  -d '{invalid json!!!}')
[[ "$CODE" == "400" || "$CODE" == "401" ]] && pass "Malformed JSON rejected ($CODE)" || fail "Malformed JSON" "code=$CODE"

# 2.7 Binary data
echo "── 2.7 Binary data ──"
CODE=$(dd if=/dev/urandom bs=256 count=1 2>/dev/null | curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" --data-binary @- 2>/dev/null)
[[ "$CODE" =~ ^(400|401|413)$ ]] && pass "Binary rejected ($CODE)" || fail "Binary data" "code=$CODE"

# 2.8 50 concurrent requests
echo "── 2.8 50 concurrent ──"
TMPDIR_CONC=$(mktemp -d)
for i in $(seq 1 50); do
  curl -s -o /dev/null -w "%{http_code}\n" "$GATEWAY_URL/" > "$TMPDIR_CONC/$i.txt" 2>/dev/null &
done
wait
OK_COUNT=$(cat "$TMPDIR_CONC"/*.txt | grep -c "200" || true)
rm -rf "$TMPDIR_CONC"
[[ $OK_COUNT -ge 45 ]] && pass "Concurrent: $OK_COUNT/50 OK" || fail "Concurrent" "$OK_COUNT/50"

# 2.9 Rapid fire (100 sequential)
echo "── 2.9 Rapid fire ──"
FAIL_COUNT=0
for i in $(seq 1 100); do
  CODE=$(http_code "$GATEWAY_URL/")
  [[ "$CODE" != "200" ]] && ((FAIL_COUNT++))
done
[[ $FAIL_COUNT -le 5 ]] && pass "Rapid fire: $((100-FAIL_COUNT))/100 OK" || fail "Rapid fire" "$FAIL_COUNT failures"

# 2.10 Path traversal
echo "── 2.10 Path traversal ──"
CODE=$(http_code "${GATEWAY_URL}/../../../etc/passwd")
BODY=$(curl -s "${GATEWAY_URL}/../../../etc/passwd")
echo "$BODY" | grep -q "root:" && fail "Path traversal" "leaked /etc/passwd" || pass "Path traversal blocked ($CODE)"

# 2.11 CRLF injection
echo "── 2.11 CRLF injection ──"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/%0d%0aX-Injected:%20true")
[[ "$CODE" =~ ^(400|404|200)$ ]] && pass "CRLF handled ($CODE)" || fail "CRLF" "code=$CODE"

# 2.12 Unicode bomb (10KB emoji)
echo "── 2.12 Unicode bomb ──"
EMOJI=$(python3 -c "print('🎉'*2500)")
BODY=$(line_text_event "$EMOJI")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "Unicode bomb handled" || fail "Unicode bomb" "code=$CODE"

# 2.13 Null bytes
echo "── 2.13 Null bytes ──"
BODY=$(line_text_event "hello\x00world")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" =~ ^(200|400)$ ]] && pass "Null bytes handled ($CODE)" || fail "Null bytes" "code=$CODE"

# 2.14 Replay attack
echo "── 2.14 Replay attack ──"
BODY=$(line_text_event "replay-test" "replay123")
line_send_webhook "$BODY" > /dev/null
RESP2=$(line_send_webhook "$BODY")
CODE2=$(echo "$RESP2" | tail -1)
[[ "$CODE2" == "200" ]] && pass "Replay handled idempotently" || fail "Replay" "code=$CODE2"

# 2.15 Wrong HTTP method
echo "── 2.15 GET /line/webhook ──"
CODE=$(http_code "${GATEWAY_URL}/line/webhook")
[[ "$CODE" =~ ^(404|405)$ ]] && pass "GET webhook rejected ($CODE)" || fail "GET webhook" "code=$CODE"

summary
