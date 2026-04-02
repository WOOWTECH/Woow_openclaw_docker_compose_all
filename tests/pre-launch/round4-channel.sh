#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"
source "$SCRIPT_DIR/lib/line-webhook.sh"

section "Round 4: LINE Channel Bidirectional (12 tests)"

# 4.1 Empty events (verify endpoint)
echo "── 4.1 Webhook verify ──"
BODY='{"events":[]}'
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
RBODY=$(echo "$RESP" | head -1)
[[ "$CODE" == "200" && "$RBODY" == *"ok"* ]] && pass "Webhook verify 200 OK" || fail "Webhook verify" "code=$CODE body=$RBODY"

# 4.2 Single message in
echo "── 4.2 Single message ──"
LINES_BEFORE=$(kexec find /home/node/.openclaw/agents/main/sessions/ -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1}END{print sum+0}')
BODY=$(line_text_event "Round4 test message")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "Message accepted (200)" || fail "Message in" "code=$CODE"

# 4.3 AI response generated
echo "── 4.3 AI response ──"
sleep 10
LINES_AFTER=$(kexec find /home/node/.openclaw/agents/main/sessions/ -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1}END{print sum+0}')
[[ $LINES_AFTER -gt $LINES_BEFORE ]] && pass "Session grew: $LINES_BEFORE → $LINES_AFTER" || fail "AI response" "no new entries"

# 4.4 Push API reply
echo "── 4.4 Push API ──"
PUSH_RESP=$(line_push "[test] Round 4 push verification")
echo "$PUSH_RESP" | grep -q "sentMessages" && pass "Push API OK" || fail "Push API" "$PUSH_RESP"

# 4.5 Multi-turn conversation
echo "── 4.5 Multi-turn (3 rounds) ──"
BEFORE=$(kexec find /home/node/.openclaw/agents/main/sessions/ -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1}END{print sum+0}')
for msg in "What is 2+2?" "And what is that times 3?" "Thanks!"; do
  B=$(line_text_event "$msg")
  line_send_webhook "$B" > /dev/null
  sleep 8
done
AFTER=$(kexec find /home/node/.openclaw/agents/main/sessions/ -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum+=$1}END{print sum+0}')
GROWTH=$((AFTER - BEFORE))
[[ $GROWTH -ge 6 ]] && pass "Multi-turn: +$GROWTH entries" || fail "Multi-turn" "only +$GROWTH entries"

# 4.6 Follow event
echo "── 4.6 Follow event ──"
BODY=$(line_follow_event)
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "Follow event handled" || fail "Follow event" "code=$CODE"

# 4.7 Empty text
echo "── 4.7 Empty text ──"
BODY=$(line_text_event "")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" =~ ^(200|400)$ ]] && pass "Empty text handled ($CODE)" || fail "Empty text" "code=$CODE"

# 4.8 Max length (5000 chars)
echo "── 4.8 Max length message ──"
LONG=$(python3 -c "print('A'*5000)")
BODY=$(line_text_event "$LONG")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "5000-char message OK" || fail "Max length" "code=$CODE"

# 4.9 Emoji only
echo "── 4.9 Emoji only ──"
BODY=$(line_text_event "🎉🔥💯🚀🎊")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "Emoji-only OK" || fail "Emoji" "code=$CODE"

# 4.10 Image event
echo "── 4.10 Image event ──"
BODY=$(line_typed_event "image")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "Image event handled" || fail "Image event" "code=$CODE"

# 4.11 Sticker event
echo "── 4.11 Sticker event ──"
BODY=$(line_typed_event "sticker")
RESP=$(line_send_webhook "$BODY")
CODE=$(echo "$RESP" | tail -1)
[[ "$CODE" == "200" ]] && pass "Sticker event handled" || fail "Sticker event" "code=$CODE"

# 4.12 Concurrent webhooks
echo "── 4.12 Concurrent 5 webhooks ──"
TMPDIR_CH=$(mktemp -d)
for i in $(seq 1 5); do
  B=$(line_text_event "concurrent-$i" "conc$i$(date +%s)")
  line_send_webhook "$B" | tail -1 > "$TMPDIR_CH/$i.txt" &
done
wait
OK_CNT=$(cat "$TMPDIR_CH"/*.txt | grep -c "200" || true)
rm -rf "$TMPDIR_CH"
[[ $OK_CNT -eq 5 ]] && pass "Concurrent: $OK_CNT/5 OK" || fail "Concurrent" "$OK_CNT/5"

summary
