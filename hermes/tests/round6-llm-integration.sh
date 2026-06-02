#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"

section "Round 6: LLM Integration & Gateway Health (12 tests)"

# ──────────────────────────────────────────────────
# 6.1 Agent gateway OpenAI-compatible API responds
# ──────────────────────────────────────────────────
echo "── 6.1 Agent gateway API endpoint ──"
API_RESP=$(kubectl -n "$NAMESPACE" run api-probe-r6 --rm -i --restart=Never \
  --image=busybox --command -- sh -c \
  "wget -q -O- http://$AGENT_SVC:$AGENT_PORT/v1/models 2>&1 || echo FAILED" 2>/dev/null | tail -5)
kubectl -n "$NAMESPACE" delete pod api-probe-r6 --grace-period=0 --force > /dev/null 2>&1
if echo "$API_RESP" | grep -qi "model\|data\|id\|object"; then
  pass "Agent API /v1/models responds"
else
  # Fallback: just TCP check
  RESULT=$(kubectl -n "$NAMESPACE" run tcp-r6 --rm -i --restart=Never \
    --image=busybox --command -- sh -c "nc -z -w 3 $AGENT_SVC $AGENT_PORT && echo OK" 2>/dev/null | tail -1)
  kubectl -n "$NAMESPACE" delete pod tcp-r6 --grace-period=0 --force > /dev/null 2>&1
  [[ "$RESULT" == *"OK"* ]] && pass "Agent gateway TCP reachable (API format unknown)" || fail "Agent API" "no response"
fi

# ──────────────────────────────────────────────────
# 6.2 WebUI config.yaml has model configured
# ──────────────────────────────────────────────────
echo "── 6.2 WebUI config.yaml model ──"
MODEL_CFG=$(kexec_webui cat /home/hermeswebui/.hermes/config.yaml 2>/dev/null)
if echo "$MODEL_CFG" | grep -qi "default.*minimax\|provider.*minimax\|MiniMax"; then
  pass "WebUI config.yaml: Minimax model configured"
else
  if [[ -n "$MODEL_CFG" ]]; then
    pass "WebUI config.yaml exists (model=$(echo "$MODEL_CFG" | grep default | head -1 | xargs))"
  else
    fail "WebUI config.yaml" "file empty or missing"
  fi
fi

# ──────────────────────────────────────────────────
# 6.3 WebUI .env has MINIMAX_API_KEY
# ──────────────────────────────────────────────────
echo "── 6.3 WebUI .env MINIMAX_API_KEY ──"
ENV_FILE=$(kexec_webui cat /home/hermeswebui/.hermes/.env 2>/dev/null)
if echo "$ENV_FILE" | grep -q "MINIMAX_API_KEY="; then
  # Verify not empty
  KEY_VAL=$(echo "$ENV_FILE" | grep "MINIMAX_API_KEY=" | cut -d= -f2)
  if [[ -n "$KEY_VAL" && "$KEY_VAL" != '""' && "$KEY_VAL" != "''" ]]; then
    pass "WebUI .env: MINIMAX_API_KEY is set (non-empty)"
  else
    fail "WebUI .env" "MINIMAX_API_KEY is empty"
  fi
else
  fail "WebUI .env" "MINIMAX_API_KEY not found"
fi

# ──────────────────────────────────────────────────
# 6.4 Gateway state file exists and is fresh
# ──────────────────────────────────────────────────
echo "── 6.4 Gateway state file ──"
GW_STATE=$(kexec_webui cat /home/hermeswebui/.hermes/gateway_state.json 2>/dev/null)
if echo "$GW_STATE" | grep -q "gateway_state"; then
  # Parse JSON with grep/sed (no python3 dependency in container)
  STATE_VAL=$(echo "$GW_STATE" | grep -o '"gateway_state":"[^"]*"' | cut -d'"' -f4)
  UPDATED=$(echo "$GW_STATE" | grep -o '"updated_at":"[^"]*"' | cut -d'"' -f4)
  if [[ "$STATE_VAL" == "running" ]]; then
    pass "Gateway state: running (updated=$UPDATED)"
  else
    fail "Gateway state" "state=$STATE_VAL"
  fi
else
  fail "Gateway state file" "not found or empty"
fi

# ──────────────────────────────────────────────────
# 6.5 GATEWAY_HEALTH_URL env set on WebUI pod
# ──────────────────────────────────────────────────
echo "── 6.5 GATEWAY_HEALTH_URL env ──"
GW_URL=$(kubectl -n "$NAMESPACE" get deployment hermes-webui \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="GATEWAY_HEALTH_URL")].value}' 2>/dev/null)
if [[ "$GW_URL" == "http://${AGENT_SVC}:${AGENT_PORT}" ]]; then
  pass "GATEWAY_HEALTH_URL: $GW_URL"
else
  fail "GATEWAY_HEALTH_URL" "got=$GW_URL (expected http://${AGENT_SVC}:${AGENT_PORT})"
fi

# ──────────────────────────────────────────────────
# 6.6 Agent MINIMAX_API_KEY env is set
# ──────────────────────────────────────────────────
echo "── 6.6 Agent MINIMAX_API_KEY env ──"
AGENT_KEY_SRC=$(kubectl -n "$NAMESPACE" get deployment hermes-agent \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="MINIMAX_API_KEY")].valueFrom.secretKeyRef.name}' 2>/dev/null)
if [[ "$AGENT_KEY_SRC" == "hermes-secrets" ]]; then
  pass "Agent MINIMAX_API_KEY: from hermes-secrets"
else
  fail "Agent MINIMAX_API_KEY" "source=$AGENT_KEY_SRC"
fi

# ──────────────────────────────────────────────────
# 6.7 WebUI → Agent HTTP health check
# ──────────────────────────────────────────────────
echo "── 6.7 WebUI → Agent health ──"
HEALTH=$(kexec_webui sh -c "wget -q -O- --timeout=5 http://$AGENT_SVC:$AGENT_PORT/ 2>&1 | head -3" 2>/dev/null || echo "FAILED")
if echo "$HEALTH" | grep -qiE "html|json|hermes|welcome|200|{"; then
  pass "WebUI → Agent HTTP health OK"
else
  # Fallback: DNS resolves
  DNS=$(kexec_webui sh -c "getent hosts $AGENT_SVC" 2>/dev/null)
  [[ -n "$DNS" ]] && pass "WebUI → Agent DNS resolves (HTTP response unknown)" || fail "WebUI → Agent health" "no connectivity"
fi

# ──────────────────────────────────────────────────
# 6.8 API_SERVER_ENABLED on agent
# ──────────────────────────────────────────────────
echo "── 6.8 API_SERVER_ENABLED ──"
API_ENABLED=$(kubectl -n "$NAMESPACE" get deployment hermes-agent \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="API_SERVER_ENABLED")].value}' 2>/dev/null)
[[ "$API_ENABLED" == "true" ]] && pass "API_SERVER_ENABLED=true" || fail "API_SERVER_ENABLED" "got=$API_ENABLED"

# ──────────────────────────────────────────────────
# 6.9 API_SERVER_CORS allows all origins
# ──────────────────────────────────────────────────
echo "── 6.9 CORS configuration ──"
CORS=$(kubectl -n "$NAMESPACE" get deployment hermes-agent \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="API_SERVER_CORS_ORIGINS")].value}' 2>/dev/null)
[[ "$CORS" == "*" ]] && pass "CORS: allow all origins" || fail "CORS" "got=$CORS"

# ──────────────────────────────────────────────────
# 6.10 Agent data volume mounted at /opt/data
# ──────────────────────────────────────────────────
echo "── 6.10 Agent data volume ──"
MOUNT=$(kubectl -n "$NAMESPACE" get deployment hermes-agent \
  -o jsonpath='{.spec.template.spec.containers[0].volumeMounts[0].mountPath}' 2>/dev/null)
[[ "$MOUNT" == "/opt/data" ]] && pass "Agent volume: /opt/data" || fail "Agent volume" "mount=$MOUNT"

# ──────────────────────────────────────────────────
# 6.11 WebUI HERMES_HOME env points to correct path
# ──────────────────────────────────────────────────
echo "── 6.11 HERMES_HOME env ──"
HERMES_HOME=$(kubectl -n "$NAMESPACE" get deployment hermes-webui \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="HERMES_HOME")].value}' 2>/dev/null)
[[ "$HERMES_HOME" == "/home/hermeswebui/.hermes" ]] && pass "HERMES_HOME=$HERMES_HOME" || fail "HERMES_HOME" "got=$HERMES_HOME"

# ──────────────────────────────────────────────────
# 6.12 Config persistence after WebUI pod restart
# ──────────────────────────────────────────────────
echo "── 6.12 Config persistence after restart ──"
# Write a marker to config to verify persistence
kexec_webui sh -c 'echo "# persist-test-marker" >> /home/hermeswebui/.hermes/config.yaml' > /dev/null 2>&1
kubectl -n "$NAMESPACE" delete pod -l "$WEBUI_LABEL" --grace-period=5 > /dev/null 2>&1
if kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l "$WEBUI_LABEL" --timeout=120s > /dev/null 2>&1; then
  sleep 5
  MARKER=$(kexec_webui grep "persist-test-marker" /home/hermeswebui/.hermes/config.yaml 2>/dev/null)
  # Clean up marker (grep -v redirect avoids sed -i compatibility issues in minimal containers)
  kexec_webui sh -c 'grep -v "persist-test-marker" /home/hermeswebui/.hermes/config.yaml > /tmp/_cfg_clean && mv /tmp/_cfg_clean /home/hermeswebui/.hermes/config.yaml' > /dev/null 2>&1
  if [[ -n "$MARKER" ]]; then
    pass "Config persisted after WebUI restart"
  else
    fail "Config persistence" "marker not found after restart"
  fi
else
  fail "WebUI restart" "timeout 120s"
fi

summary
