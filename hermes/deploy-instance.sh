#!/bin/bash
set -euo pipefail

# =============================================================
# Hermes Multi-Instance Deployer
# Usage: ./deploy-instance.sh <instance-name>
# Example: ./deploy-instance.sh apporoalan
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}/template/k8s"
INSTANCES_DIR="${SCRIPT_DIR}/instances"
INSTANCES_JSON="${INSTANCES_DIR}/instances.json"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[ OK ]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
die()   { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# ── Validate arguments ──
INSTANCE_NAME="${1:-}"
[[ -z "$INSTANCE_NAME" ]] && die "Usage: $0 <instance-name>\n  Available: $(python3 -c "import json; print(', '.join(json.load(open('$INSTANCES_JSON'))['instances'].keys()))")"

# ── Read instance config ──
info "Reading instance config for '${INSTANCE_NAME}'..."
INSTANCE_CFG=$(python3 -c "
import json, sys
data = json.load(open('${INSTANCES_JSON}'))
inst = data['instances'].get('${INSTANCE_NAME}')
if not inst:
    print('NOT_FOUND', file=sys.stderr); sys.exit(1)
# Merge defaults
inst['agent_image'] = inst.get('agent_image', data['default_agent_image'])
inst['webui_password'] = inst.get('webui_password', data['default_webui_password'])
inst['llm_provider'] = inst.get('llm_provider', data['default_llm_provider'])
inst['llm_model'] = inst.get('llm_model', data['default_llm_model'])
json.dump(inst, sys.stdout)
") || die "Instance '${INSTANCE_NAME}' not found in instances.json"

NAMESPACE=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['namespace'])")
DOMAIN=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['domain'])")
TUNNEL_NAME=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnel_name'])")
AGENT_IMAGE=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['agent_image'])")
WEBUI_PASSWORD=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['webui_password'])")
LLM_PROVIDER=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['llm_provider'])")
LLM_MODEL=$(echo "$INSTANCE_CFG" | python3 -c "import sys,json; print(json.load(sys.stdin)['llm_model'])")

echo ""
echo "============================================================"
echo "  Hermes Instance Deployment: ${INSTANCE_NAME}"
echo "  Namespace: ${NAMESPACE}"
echo "  Domain:    ${DOMAIN}"
echo "  Model:     ${LLM_MODEL}"
echo "============================================================"
echo ""

# ── Prerequisites ──
command -v kubectl >/dev/null 2>&1 || die "kubectl not installed"
command -v python3 >/dev/null 2>&1 || die "python3 not installed"

# ── Step 1: Generate instance manifests from template ──
INST_DIR="${INSTANCES_DIR}/${INSTANCE_NAME}"
INST_K8S="${INST_DIR}/k8s"
mkdir -p "$INST_K8S"

info "Generating manifests from template..."
for f in "${TEMPLATE_DIR}"/*.yaml; do
  BASE=$(basename "$f")
  sed \
    -e "s|__NAMESPACE__|${NAMESPACE}|g" \
    -e "s|__DOMAIN__|${DOMAIN}|g" \
    -e "s|__AGENT_IMAGE__|${AGENT_IMAGE}|g" \
    -e "s|__WEBUI_PASSWORD__|${WEBUI_PASSWORD}|g" \
    -e "s|__CF_ACCOUNT_ID__|PLACEHOLDER_ACCOUNT_ID|g" \
    -e "s|__CF_TUNNEL_ID__|PLACEHOLDER_TUNNEL_ID|g" \
    "$f" > "${INST_K8S}/${BASE}"
done
ok "Manifests generated at ${INST_K8S}/"

# ── Step 2: Update WebUI init-config for LLM model ──
info "Setting LLM model to ${LLM_MODEL} (provider: ${LLM_PROVIDER})..."
sed -i \
  -e "s|minimax/MiniMax-M2.7|${LLM_MODEL}|g" \
  -e "s|provider: \"minimax\"|provider: \"${LLM_PROVIDER}\"|g" \
  "${INST_K8S}/07-hermes-webui.yaml"
ok "LLM model configured"

# ── Step 3: Cloudflare tunnel initialization ──
CF_CONFIG="${INST_DIR}/cf-config.json"
if [[ ! -f "$CF_CONFIG" ]]; then
  info "Initializing Cloudflare tunnel for ${TUNNEL_NAME}..."
  if [[ -z "${CF_API_TOKEN:-}" ]]; then
    read -rp "Enter Cloudflare API token: " CF_API_TOKEN
    export CF_API_TOKEN
  fi
  export TUNNEL_NAME="${TUNNEL_NAME}"
  export HERMES_DOMAIN="${DOMAIN}"
  export HERMES_NAMESPACE="${NAMESPACE}"
  export CF_CONFIG_OUTPUT_DIR="${INST_DIR}"

  # Run init script — saves cf-config.json directly to instance dir
  python3 "${SCRIPT_DIR}/init-cloudflare-hermes.py"
  ok "Cloudflare tunnel initialized"
else
  ok "Using existing Cloudflare config: $CF_CONFIG"
fi

# ── Step 4: Read Cloudflare config and update manifests ──
info "Applying Cloudflare config to manifests..."
CF_API_TOKEN_VAL=$(python3 -c "import json; print(json.load(open('${CF_CONFIG}'))['CF_API_TOKEN'])")
CF_TUNNEL_TOKEN=$(python3 -c "import json; print(json.load(open('${CF_CONFIG}'))['CF_TUNNEL_TOKEN'])")
CF_ACCOUNT_ID=$(python3 -c "import json; print(json.load(open('${CF_CONFIG}'))['CF_ACCOUNT_ID'])")
CF_TUNNEL_ID=$(python3 -c "import json; print(json.load(open('${CF_CONFIG}'))['CF_TUNNEL_ID'])")

sed -i \
  -e "s|PLACEHOLDER_ACCOUNT_ID|${CF_ACCOUNT_ID}|g" \
  -e "s|PLACEHOLDER_TUNNEL_ID|${CF_TUNNEL_ID}|g" \
  "${INST_K8S}/02-configmap.yaml"

# ── Step 5: Generate secrets ──
info "Generating secrets..."
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)}"
MINIMAX_API_KEY="${MINIMAX_API_KEY:-}"
if [[ -z "$MINIMAX_API_KEY" ]]; then
  read -rp "Enter Minimax API key (or press Enter to skip): " MINIMAX_API_KEY
fi

CF_API_TOKEN_B64=$(echo -n "${CF_API_TOKEN_VAL}" | base64 -w0)
CF_TUNNEL_TOKEN_B64=$(echo -n "${CF_TUNNEL_TOKEN}" | base64 -w0)
POSTGRES_PASSWORD_B64=$(echo -n "${POSTGRES_PASSWORD}" | base64 -w0)
MINIMAX_API_KEY_B64=$(echo -n "${MINIMAX_API_KEY}" | base64 -w0)

cat > "${INST_K8S}/01-secrets.yaml" <<EOYAML
# Auto-generated by deploy-instance.sh — DO NOT commit real secrets
apiVersion: v1
kind: Secret
metadata:
  name: cf-secrets
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: hermes
type: Opaque
data:
  CF_API_TOKEN: "${CF_API_TOKEN_B64}"
  CF_TUNNEL_TOKEN: "${CF_TUNNEL_TOKEN_B64}"
---
apiVersion: v1
kind: Secret
metadata:
  name: hermes-secrets
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: hermes
type: Opaque
data:
  POSTGRES_PASSWORD: "${POSTGRES_PASSWORD_B64}"
  MINIMAX_API_KEY: "${MINIMAX_API_KEY_B64}"
EOYAML
ok "Secrets generated"

# ── Step 6: Apply manifests in order ──
info "Applying K8s manifests for namespace ${NAMESPACE}..."
kubectl apply -f "${INST_K8S}/00-namespace.yaml"
kubectl apply -f "${INST_K8S}/01-secrets.yaml"
kubectl apply -f "${INST_K8S}/01a-rbac.yaml"

for manifest in \
  02-configmap.yaml 03-pvc.yaml 04-postgresql.yaml 05-redis.yaml \
  06-hermes-agent.yaml 07-hermes-webui.yaml 08-cloudflared.yaml \
  09-ingress.yaml 10-network-policy.yaml; do
  if [[ -f "${INST_K8S}/${manifest}" ]]; then
    info "  Applying ${manifest}..."
    kubectl apply -f "${INST_K8S}/${manifest}"
  fi
done
ok "All manifests applied"

# ── Step 7: Wait for rollouts ──
echo ""
info "Waiting for services to be ready..."
kubectl rollout status deployment/hermes-postgresql -n "${NAMESPACE}" --timeout=120s || warn "PostgreSQL not ready"
kubectl rollout status deployment/hermes-redis -n "${NAMESPACE}" --timeout=60s || warn "Redis not ready"
kubectl rollout status deployment/hermes-agent -n "${NAMESPACE}" --timeout=180s || warn "Agent not ready"
kubectl rollout status deployment/hermes-webui -n "${NAMESPACE}" --timeout=120s || warn "WebUI not ready"

# ── Step 8: Configure Cloudflare route ──
info "Configuring Cloudflare tunnel route..."
ROUTE_RESPONSE=$(curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/cfd_tunnel/${CF_TUNNEL_ID}/configurations" \
  -H "Authorization: Bearer ${CF_API_TOKEN_VAL}" \
  -H "Content-Type: application/json" \
  -d "{\"config\":{\"ingress\":[{\"hostname\":\"${DOMAIN}\",\"service\":\"http://hermes-webui-svc.${NAMESPACE}.svc.cluster.local:8787\"},{\"service\":\"http_status:404\"}]}}")
ROUTE_OK=$(echo "$ROUTE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success','false'))" 2>/dev/null || echo "false")
[[ "$ROUTE_OK" == "True" || "$ROUTE_OK" == "true" ]] && ok "Route: ${DOMAIN} → webui:8787" || warn "Route config response: ${ROUTE_RESPONSE}"

# ── Step 9: Update instance status ──
python3 -c "
import json
data = json.load(open('${INSTANCES_JSON}'))
data['instances']['${INSTANCE_NAME}']['status'] = 'deployed'
json.dump(data, open('${INSTANCES_JSON}', 'w'), indent=2, ensure_ascii=False)
print('  Status updated: deployed')
"

# ── Summary ──
echo ""
echo "============================================================"
ok "Instance '${INSTANCE_NAME}' deployed!"
echo ""
echo "  Domain:    https://${DOMAIN}"
echo "  Namespace: ${NAMESPACE}"
echo "  Password:  ${WEBUI_PASSWORD}"
echo "  Model:     ${LLM_MODEL}"
echo "  PostgreSQL: ${POSTGRES_PASSWORD}"
echo "============================================================"
