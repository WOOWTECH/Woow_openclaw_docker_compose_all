#!/usr/bin/env bash
line_msg_id() { echo "test$(date +%s%N | tail -c 10)"; }

line_send_webhook() {
  local body="$1"
  local sig
  sig=$(echo -n "$body" | openssl dgst -sha256 -hmac "$LINE_CHANNEL_SECRET" -binary | base64)
  curl -s -w "\n%{http_code}" -X POST "${GATEWAY_URL}/line/webhook" \
    -H "Content-Type: application/json" \
    -H "x-line-signature: $sig" \
    -d "$body"
}

line_text_event() {
  local text="$1"
  local msgid="${2:-$(line_msg_id)}"
  local ts; ts=$(date +%s)000
  printf '{"destination":"%s","events":[{"type":"message","message":{"type":"text","id":"%s","text":"%s"},"timestamp":%s,"source":{"type":"user","userId":"%s"},"replyToken":"%s","mode":"active","webhookEventId":"evt_%s","deliveryContext":{"isRedelivery":false}}]}' \
    "$LINE_BOT_ID" "$msgid" "$text" "$ts" "$LINE_USER_ID" "$(openssl rand -hex 24)" "$msgid"
}

line_follow_event() {
  local ts; ts=$(date +%s)000
  printf '{"destination":"%s","events":[{"type":"follow","timestamp":%s,"source":{"type":"user","userId":"%s"},"replyToken":"%s","mode":"active","webhookEventId":"evt_follow_%s","deliveryContext":{"isRedelivery":false}}]}' \
    "$LINE_BOT_ID" "$ts" "$LINE_USER_ID" "$(openssl rand -hex 24)" "$(date +%s)"
}

line_typed_event() {
  local etype="$1"
  local ts; ts=$(date +%s)000
  local msgid; msgid=$(line_msg_id)
  local msg
  if [ "$etype" = "sticker" ]; then
    msg=$(printf '{"type":"sticker","id":"%s","packageId":"1","stickerId":"1"}' "$msgid")
  else
    msg=$(printf '{"type":"image","id":"%s","contentProvider":{"type":"line"}}' "$msgid")
  fi
  printf '{"destination":"%s","events":[{"type":"message","message":%s,"timestamp":%s,"source":{"type":"user","userId":"%s"},"replyToken":"%s","mode":"active","webhookEventId":"evt_%s","deliveryContext":{"isRedelivery":false}}]}' \
    "$LINE_BOT_ID" "$msg" "$ts" "$LINE_USER_ID" "$(openssl rand -hex 24)" "$msgid"
}

line_push() {
  local text="$1"
  curl -s "https://api.line.me/v2/bot/message/push" \
    -H "Authorization: Bearer ${LINE_ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"to\":\"${LINE_USER_ID}\",\"messages\":[{\"type\":\"text\",\"text\":\"${text}\"}]}"
}
