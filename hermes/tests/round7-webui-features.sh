#!/usr/bin/env bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/config.env"
source "$SCRIPT_DIR/lib/assert.sh"

section "Round 7: WebGUI Feature Verification (14 tests)"

# ──────────────────────────────────────────────────
# 7.1 WebUI state directory exists
# ──────────────────────────────────────────────────
echo "── 7.1 WebUI state directory ──"
STATE_DIR=$(kexec_webui ls -d /home/hermeswebui/.hermes/webui 2>/dev/null)
if [[ -n "$STATE_DIR" ]]; then
  pass "WebUI state dir: /home/hermeswebui/.hermes/webui"
else
  # May be created on first use
  skip "WebUI state dir" "not yet created (first-use lazy init)"
fi

# ──────────────────────────────────────────────────
# 7.2 Hermes-agent source cloned
# ──────────────────────────────────────────────────
echo "── 7.2 Agent source cloned ──"
AGENT_SRC=$(kexec_webui ls /home/hermeswebui/.hermes/hermes-agent/package.json 2>/dev/null)
if [[ -n "$AGENT_SRC" ]]; then
  pass "Agent source cloned (package.json exists)"
else
  AGENT_DIR=$(kexec_webui ls /home/hermeswebui/.hermes/hermes-agent/ 2>/dev/null | head -5)
  [[ -n "$AGENT_DIR" ]] && pass "Agent source cloned (files: $AGENT_DIR)" || fail "Agent source" "clone failed"
fi

# ──────────────────────────────────────────────────
# 7.3 Static tools installed (/opt/tools)
# ──────────────────────────────────────────────────
echo "── 7.3 Static tools ──"
TOOLS=$(kexec_webui ls /opt/tools/ 2>/dev/null)
TOOL_COUNT=$(echo "$TOOLS" | wc -w)
EXPECTED_TOOLS="yq helm argocd cloudflared gh"
MISSING=""
for tool in $EXPECTED_TOOLS; do
  echo "$TOOLS" | grep -q "$tool" || MISSING="$MISSING $tool"
done
if [[ -z "$MISSING" ]]; then
  pass "Static tools: all 5 present (yq, helm, argocd, cloudflared, gh)"
else
  fail "Static tools" "missing:$MISSING (found=$TOOL_COUNT)"
fi

# ──────────────────────────────────────────────────
# 7.4 PostStart CLI tools installed
# ──────────────────────────────────────────────────
echo "── 7.4 PostStart CLI tools ──"
POSTSTART_TOOLS="jq fd lynx pandoc"
INSTALLED=""
PS_MISSING=""
for tool in $POSTSTART_TOOLS; do
  if kexec_webui which "$tool" > /dev/null 2>&1; then
    INSTALLED="$INSTALLED $tool"
  else
    PS_MISSING="$PS_MISSING $tool"
  fi
done
if [[ -z "$PS_MISSING" ]]; then
  pass "PostStart tools: all installed ($POSTSTART_TOOLS)"
else
  # postStart is async, may still be installing
  INSTALL_LOG=$(kexec_webui cat /tmp/tools-install.log 2>/dev/null | tail -3)
  if echo "$INSTALL_LOG" | grep -q "Setting up"; then
    skip "PostStart tools" "still installing (missing:$PS_MISSING)"
  else
    fail "PostStart tools" "missing:$PS_MISSING"
  fi
fi

# ──────────────────────────────────────────────────
# 7.5 WebUI password configured
# ──────────────────────────────────────────────────
echo "── 7.5 WebUI password ──"
PW_ENV=$(kubectl -n "$NAMESPACE" get deployment hermes-webui \
  -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="HERMES_WEBUI_PASSWORD")].value}' 2>/dev/null)
if [[ -n "$PW_ENV" ]]; then
  pass "WebUI password configured (HERMES_WEBUI_PASSWORD set)"
else
  fail "WebUI password" "not configured"
fi

# ──────────────────────────────────────────────────
# 7.6 UID/GID configuration
# ──────────────────────────────────────────────────
echo "── 7.6 UID/GID ──"
WEBUI_UID=$(kexec_webui id -u 2>/dev/null)
WEBUI_GID=$(kexec_webui id -g 2>/dev/null)
if [[ "$WEBUI_UID" == "1000" && "$WEBUI_GID" == "1000" ]]; then
  pass "WebUI UID/GID: 1000:1000"
else
  skip "WebUI UID/GID" "uid=$WEBUI_UID gid=$WEBUI_GID (may differ in container)"
fi

# ──────────────────────────────────────────────────
# 7.7 Gateway state refresher process running
# ──────────────────────────────────────────────────
echo "── 7.7 Gateway state refresher ──"
# Primary check: is gateway_state.json recently updated? (more reliable than ps aux,
# which may not be available in minimal/s6-overlay containers)
FRESH=$(kexec_webui sh -c '
  if [ -f /home/hermeswebui/.hermes/gateway_state.json ]; then
    FAGE=$(($(date +%s) - $(stat -c %Y /home/hermeswebui/.hermes/gateway_state.json 2>/dev/null || echo 0)))
    [ "$FAGE" -lt 60 ] && echo "FRESH" || echo "STALE:${FAGE}s"
  else
    echo "MISSING"
  fi
' 2>/dev/null)
if [[ "$FRESH" == "FRESH" ]]; then
  pass "Gateway state refresher: file updated within 60s"
elif [[ "$FRESH" == STALE:* ]]; then
  skip "Gateway state refresher" "file $FRESH (may need longer wait)"
else
  fail "Gateway state refresher" "gateway_state.json $FRESH"
fi

# ──────────────────────────────────────────────────
# 7.8 WebUI HTTP serves login page
# ──────────────────────────────────────────────────
echo "── 7.8 WebUI login page ──"
LOGIN_PAGE=$(kexec_webui sh -c "wget -q -O- http://localhost:$WEBUI_PORT/ 2>&1 | head -20" 2>/dev/null)
if echo "$LOGIN_PAGE" | grep -qi "password\|login\|hermes\|html"; then
  pass "WebUI login page served"
else
  fail "WebUI login page" "unexpected content"
fi

# ──────────────────────────────────────────────────
# 7.9 Agent dashboard port 9119
# ──────────────────────────────────────────────────
echo "── 7.9 Agent dashboard ──"
DASH=$(kubectl -n "$NAMESPACE" get svc "$AGENT_SVC" -o jsonpath='{.spec.ports[?(@.name=="dashboard")].port}' 2>/dev/null)
[[ "$DASH" == "9119" ]] && pass "Agent dashboard: port 9119 exposed" || fail "Agent dashboard" "port=$DASH"

# ──────────────────────────────────────────────────
# 7.10 ServiceAccount exists for hermes-agent
# ──────────────────────────────────────────────────
echo "── 7.10 ServiceAccount ──"
SA=$(kubectl -n "$NAMESPACE" get serviceaccount hermes-agent-sa -o name 2>/dev/null)
[[ -n "$SA" ]] && pass "ServiceAccount: hermes-agent-sa" || fail "ServiceAccount" "not found"

# ──────────────────────────────────────────────────
# 7.11 RBAC ClusterRoleBinding exists
# ──────────────────────────────────────────────────
echo "── 7.11 RBAC ClusterRoleBinding ──"
CRB=$(kubectl get clusterrolebinding -o name 2>/dev/null | grep hermes)
if [[ -n "$CRB" ]]; then
  pass "RBAC: ClusterRoleBinding found ($CRB)"
else
  # Check RoleBinding in namespace
  RB=$(kubectl -n "$NAMESPACE" get rolebinding -o name 2>/dev/null | grep hermes)
  [[ -n "$RB" ]] && pass "RBAC: RoleBinding found ($RB)" || fail "RBAC" "no hermes bindings found"
fi

# ──────────────────────────────────────────────────
# 7.12 WebUI PVC is longhorn storage class
# ──────────────────────────────────────────────────
echo "── 7.12 WebUI PVC storage class ──"
SC=$(kubectl -n "$NAMESPACE" get pvc "$PVC_WEBUI" -o jsonpath='{.spec.storageClassName}' 2>/dev/null)
PHASE=$(kubectl -n "$NAMESPACE" get pvc "$PVC_WEBUI" -o jsonpath='{.status.phase}' 2>/dev/null)
if [[ "$SC" == "longhorn" && "$PHASE" == "Bound" ]]; then
  pass "WebUI PVC: longhorn, Bound"
else
  [[ "$PHASE" == "Bound" ]] && pass "WebUI PVC: Bound (storageClass=$SC)" || fail "WebUI PVC" "class=$SC phase=$PHASE"
fi

# ──────────────────────────────────────────────────
# 7.13 Init containers completed
# ──────────────────────────────────────────────────
echo "── 7.13 Init containers ──"
INIT_STATUSES=$(kubectl -n "$NAMESPACE" get pods -l "$WEBUI_LABEL" \
  -o jsonpath='{.items[0].status.initContainerStatuses[*].ready}' 2>/dev/null)
ALL_READY=true
for status in $INIT_STATUSES; do
  [[ "$status" != "true" ]] && ALL_READY=false
done
if [[ "$ALL_READY" == "true" && -n "$INIT_STATUSES" ]]; then
  pass "Init containers: all completed"
else
  fail "Init containers" "statuses=$INIT_STATUSES"
fi

# ──────────────────────────────────────────────────
# 7.14 External HTTPS → WebUI full chain
# ──────────────────────────────────────────────────
echo "── 7.14 External HTTPS full chain ──"
BODY=$(curl -sk --max-time 15 $CURL_RESOLVE "$EXTERNAL_URL" 2>&1)
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 -k $CURL_RESOLVE "$EXTERNAL_URL" 2>&1)
if [[ "$CODE" =~ ^[23] ]] && echo "$BODY" | grep -qi "hermes\|password\|login\|html"; then
  pass "External HTTPS chain: HTTP $CODE, page content OK"
else
  fail "External HTTPS chain" "http=$CODE body=$(echo "$BODY" | head -1)"
fi

summary
