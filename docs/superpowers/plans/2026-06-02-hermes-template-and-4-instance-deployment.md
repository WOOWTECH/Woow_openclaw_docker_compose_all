# Hermes Deployment Template & 4-Instance Upgrade Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract WoowTech Hermes into a reusable template, then deploy 4 aligned instances (apporoalan, johhanlin, alanlin, torchmedia) from that template.

**Architecture:** Create a `hermes/template/` directory with parameterized K8s manifests (using `__NAMESPACE__`, `__DOMAIN__` placeholders). Build a `deploy-instance.sh` script that copies the template, substitutes per-instance values, runs Cloudflare init, and deploys. Each instance gets its own directory (`hermes/instances/<name>/`) with generated manifests and a `config.json` defining its identity.

**Tech Stack:** Bash, kubectl, Python 3 (Cloudflare API), K8s YAML manifests, jq

---

## Current State Analysis

### Hardcoded values in existing `hermes/k8s-manifests/` that need parameterizing:

| File | Hardcoded Value | Replacement Placeholder |
|------|----------------|------------------------|
| All 12 manifests | `namespace: hermes` | `__NAMESPACE__` |
| 02-configmap.yaml | `hermes-woowtechjac.woowtech.io` | `__DOMAIN__` |
| 02-configmap.yaml | `hermes-postgresql-svc` | Stays same (internal service name) |
| 06-hermes-agent.yaml | `10.43.80.213:5000/hermes-agent-custom:latest` | `__AGENT_IMAGE__` |
| 07-hermes-webui.yaml | `HERMES_WEBUI_PASSWORD: "woowtech"` | `__WEBUI_PASSWORD__` |
| 09-ingress.yaml | `hermes-woowtechjac.woowtech.io` | `__DOMAIN__` |
| 01a-rbac.yaml | ClusterRole name `hermes-agent-cluster-reader` | `__NAMESPACE__-agent-cluster-reader` |
| 01a-rbac.yaml | ClusterRoleBinding name | `__NAMESPACE__-agent-cluster-reader-binding` |
| deploy.sh | `NAMESPACE="hermes"` | Parameter from config |
| init-cloudflare-hermes.py | `hermes-webui-svc.hermes.svc.cluster.local:3000` | Uses namespace param |

### 5 Instances to support:

| Instance ID | Namespace | Domain | Purpose |
|-------------|-----------|--------|---------|
| `woowtech` | `hermes` | `woowtech-hermes.woowtech.io` | WoowTech Odoo 18 ERP (reference) |
| `apporoalan` | `apporoalan-hermes` | `apporoalan-hermes.woowtech.io` | ESG/WELL 健康建築 |
| `johhanlin` | `johhanlin-hermes` | `johhanlin-hermes.woowtech.io` | HSBC 外匯交易 |
| `alanlin` | `alanlin-hermes` | `alanlin-hermes.woowtech.io` | 通用 AI 助手 |
| `torchmedia` | `torchmedia-hermes` | `torchmedia-hermes.woowtech.io` | 通用 AI 助手 |

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `hermes/template/k8s/00-namespace.yaml` | Namespace template with `__NAMESPACE__` |
| Create | `hermes/template/k8s/01-secrets.yaml` | Secrets template (placeholder values) |
| Create | `hermes/template/k8s/01a-rbac.yaml` | RBAC template with `__NAMESPACE__` |
| Create | `hermes/template/k8s/02-configmap.yaml` | ConfigMap template with `__DOMAIN__` |
| Create | `hermes/template/k8s/03-pvc.yaml` | PVC template with `__NAMESPACE__` |
| Create | `hermes/template/k8s/04-postgresql.yaml` | PostgreSQL template |
| Create | `hermes/template/k8s/05-redis.yaml` | Redis template |
| Create | `hermes/template/k8s/06-hermes-agent.yaml` | Agent template with `__AGENT_IMAGE__` |
| Create | `hermes/template/k8s/07-hermes-webui.yaml` | WebUI template with `__DOMAIN__`, `__WEBUI_PASSWORD__` |
| Create | `hermes/template/k8s/08-cloudflared.yaml` | Cloudflare tunnel template |
| Create | `hermes/template/k8s/09-ingress.yaml` | Ingress template with `__DOMAIN__` |
| Create | `hermes/template/k8s/10-network-policy.yaml` | Network policy template |
| Create | `hermes/instances/instances.json` | Registry of all 5 instances |
| Create | `hermes/deploy-instance.sh` | One-command instance deployer |
| Create | `hermes/tests/test-instance.sh` | Per-instance test runner (parameterized) |
| Modify | `hermes/init-cloudflare-hermes.py` | Fix port 3000→8787, add CF_CONFIG_OUTPUT_DIR support |
| Modify | `hermes/deploy.sh` | Fix port 3000→8787 in Cloudflare route |
| Modify | `hermes/tests/config.env` | Fix NP_POSTGRES/NP_REDIS names to match actual manifests |
| Modify | `.gitignore` | Add `**/01-secrets.yaml` to prevent secret leaks |
| Preserve | `hermes/k8s-manifests/` | Keep as-is (WoowTech's live manifests) |

---

### Task 0: Fix Existing Bugs (Port 3000→8787, config.env, .gitignore)

**Files:**
- Modify: `hermes/init-cloudflare-hermes.py:103` — Fix service port from 3000 to 8787, add `CF_CONFIG_OUTPUT_DIR` env support
- Modify: `hermes/deploy.sh:188` — Fix Cloudflare route port from 3000 to 8787
- Modify: `hermes/tests/config.env` — Fix network policy names
- Modify: `.gitignore` — Add `**/01-secrets.yaml`

- [ ] **Step 1: Fix init-cloudflare-hermes.py — port 3000→8787 and configurable output dir**

In `hermes/init-cloudflare-hermes.py`, change line 103:
```python
# OLD:
"service": "http://hermes-webui-svc.hermes.svc.cluster.local:3000",
# NEW:
"service": f"http://hermes-webui-svc.{NAMESPACE}.svc.cluster.local:8787",
```

Where `NAMESPACE` is derived from env:
```python
NAMESPACE = os.environ.get("HERMES_NAMESPACE", "hermes")
```

And change line 126 to respect `CF_CONFIG_OUTPUT_DIR`:
```python
# OLD:
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf-config.json")
# NEW:
output_dir = os.environ.get("CF_CONFIG_OUTPUT_DIR", os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(output_dir, "cf-config.json")
```

Also update line 96 and 112 similarly for the print statement.

- [ ] **Step 2: Fix deploy.sh — port 3000→8787**

In `hermes/deploy.sh` line 188, change:
```bash
# OLD:
"service\":\"http://hermes-webui-svc.${NAMESPACE}.svc.cluster.local:3000\"
# NEW:
"service\":\"http://hermes-webui-svc.${NAMESPACE}.svc.cluster.local:8787\"
```

Also fix line 192:
```bash
# OLD:
ok "Cloudflare route: ${DOMAIN} → hermes-webui-svc:3000"
# NEW:
ok "Cloudflare route: ${DOMAIN} → hermes-webui-svc:8787"
```

- [ ] **Step 3: Fix config.env — network policy names**

In `hermes/tests/config.env`, change:
```bash
# OLD:
export NP_POSTGRES="hermes-postgresql-netpol"
export NP_REDIS="hermes-redis-netpol"
# NEW:
export NP_POSTGRES="hermes-postgresql-policy"
export NP_REDIS="hermes-redis-policy"
```

- [ ] **Step 4: Fix .gitignore — exclude generated secrets**

Add to `.gitignore`:
```
**/01-secrets.yaml
hermes/instances/**/cf-config.json
```

- [ ] **Step 5: Commit**

```bash
git add hermes/init-cloudflare-hermes.py hermes/deploy.sh hermes/tests/config.env .gitignore
git commit -m "fix(hermes): correct Cloudflare port 3000→8787, fix config.env NP names, gitignore secrets

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 1: Create Template K8s Manifests

**Files:**
- Create: `hermes/template/k8s/00-namespace.yaml`
- Create: `hermes/template/k8s/01-secrets.yaml`
- Create: `hermes/template/k8s/01a-rbac.yaml`
- Create: `hermes/template/k8s/02-configmap.yaml`
- Create: `hermes/template/k8s/03-pvc.yaml`
- Create: `hermes/template/k8s/04-postgresql.yaml`
- Create: `hermes/template/k8s/05-redis.yaml`
- Create: `hermes/template/k8s/06-hermes-agent.yaml`
- Create: `hermes/template/k8s/07-hermes-webui.yaml`
- Create: `hermes/template/k8s/08-cloudflared.yaml`
- Create: `hermes/template/k8s/09-ingress.yaml`
- Create: `hermes/template/k8s/10-network-policy.yaml`

Copy every file from `hermes/k8s-manifests/` into `hermes/template/k8s/` and replace all hardcoded instance-specific values with placeholders.

**Placeholders used:**
- `__NAMESPACE__` — K8s namespace (e.g. `apporoalan-hermes`)
- `__DOMAIN__` — External domain (e.g. `apporoalan-hermes.woowtech.io`)
- `__AGENT_IMAGE__` — Agent container image URI
- `__WEBUI_PASSWORD__` — WebUI login password
- `__CF_ACCOUNT_ID__` — Cloudflare account ID (placeholder for deploy time)
- `__CF_TUNNEL_ID__` — Cloudflare tunnel ID (placeholder for deploy time)

- [ ] **Step 1: Create template directory**

```bash
mkdir -p hermes/template/k8s
```

- [ ] **Step 2: Copy existing manifests as templates and apply placeholder substitution**

For each file, copy from `hermes/k8s-manifests/` to `hermes/template/k8s/` and replace:
- All `namespace: hermes` → `namespace: __NAMESPACE__`
- All `hermes-woowtechjac.woowtech.io` → `__DOMAIN__`
- `10.43.80.213:5000/hermes-agent-custom:latest` → `__AGENT_IMAGE__`
- RBAC cluster-scoped resource names: prefix with `__NAMESPACE__` to avoid collisions
  - `hermes-agent-cluster-reader` → `__NAMESPACE__-agent-cluster-reader`
  - `hermes-agent-cluster-reader-binding` → `__NAMESPACE__-agent-cluster-reader-binding`
- ConfigMap CF placeholders: `9c27f623ee596e0b67be56263bcb1974` → `__CF_ACCOUNT_ID__`
- ConfigMap CF placeholders: `b9be7e6e-3e90-4472-b3c9-91781b5b9140` → `__CF_TUNNEL_ID__`
- WebUI password `"woowtech"` → `"__WEBUI_PASSWORD__"`
- Network policy names: `hermes-postgresql-policy` → `__NAMESPACE__-postgresql-policy`
- Network policy names: `hermes-redis-policy` → `__NAMESPACE__-redis-policy`

Use a script to automate:

```bash
for f in hermes/k8s-manifests/*.yaml; do
  BASE=$(basename "$f")
  cp "$f" "hermes/template/k8s/$BASE"
done

# Apply placeholder substitutions to all template files
for f in hermes/template/k8s/*.yaml; do
  sed -i \
    -e 's|namespace: hermes|namespace: __NAMESPACE__|g' \
    -e 's|hermes-woowtechjac\.woowtech\.io|__DOMAIN__|g' \
    -e 's|10\.43\.80\.213:5000/hermes-agent-custom:latest|__AGENT_IMAGE__|g' \
    -e 's|9c27f623ee596e0b67be56263bcb1974|__CF_ACCOUNT_ID__|g' \
    -e 's|b9be7e6e-3e90-4472-b3c9-91781b5b9140|__CF_TUNNEL_ID__|g' \
    "$f"
done

# RBAC: cluster-scoped names need namespace prefix to avoid collision
sed -i \
  -e 's|name: hermes-agent-cluster-reader-binding|name: __NAMESPACE__-agent-cluster-reader-binding|' \
  -e 's|name: hermes-agent-cluster-reader$|name: __NAMESPACE__-agent-cluster-reader|' \
  -e 's|name: hermes-agent-cluster-reader\b|name: __NAMESPACE__-agent-cluster-reader|' \
  hermes/template/k8s/01a-rbac.yaml

# WebUI password placeholder
sed -i 's|HERMES_WEBUI_PASSWORD|HERMES_WEBUI_PASSWORD|' hermes/template/k8s/07-hermes-webui.yaml
# The password value itself:
sed -i 's|value: "woowtech"|value: "__WEBUI_PASSWORD__"|' hermes/template/k8s/07-hermes-webui.yaml

# Network policy names (avoid cross-namespace collision)
sed -i \
  -e 's|name: hermes-postgresql-policy|name: __NAMESPACE__-postgresql-policy|' \
  -e 's|name: hermes-redis-policy|name: __NAMESPACE__-redis-policy|' \
  hermes/template/k8s/10-network-policy.yaml
```

- [ ] **Step 3: Verify all templates have no remaining hardcoded 'hermes-woowtechjac' references**

```bash
grep -r "hermes-woowtechjac" hermes/template/k8s/ && echo "FAIL: hardcoded domain found" || echo "OK: no hardcoded domains"
grep -r "namespace: hermes$" hermes/template/k8s/ && echo "FAIL: hardcoded namespace" || echo "OK: all namespaces parameterized"
```

- [ ] **Step 4: Commit**

```bash
git add hermes/template/
git commit -m "feat(hermes): create parameterized K8s manifest templates from WoowTech reference

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Create Instance Registry (`instances.json`)

**Files:**
- Create: `hermes/instances/instances.json`

A single JSON file that defines all 5 Hermes instances. The deploy script reads this to know what values to substitute.

- [ ] **Step 1: Create instances directory and registry**

```bash
mkdir -p hermes/instances
```

```json
{
  "default_agent_image": "10.43.80.213:5000/hermes-agent-custom:latest",
  "default_webui_password": "woowtech",
  "default_llm_provider": "minimax",
  "default_llm_model": "minimax/MiniMax-M2.7",
  "instances": {
    "woowtech": {
      "namespace": "hermes",
      "domain": "woowtech-hermes.woowtech.io",
      "tunnel_name": "woowtech-hermes",
      "purpose": "WoowTech Odoo 18 ERP 顧問",
      "status": "deployed"
    },
    "apporoalan": {
      "namespace": "apporoalan-hermes",
      "domain": "apporoalan-hermes.woowtech.io",
      "tunnel_name": "apporoalan-hermes",
      "purpose": "ESG/WELL/LEED 健康建築顧問",
      "status": "pending"
    },
    "johhanlin": {
      "namespace": "johhanlin-hermes",
      "domain": "johhanlin-hermes.woowtech.io",
      "tunnel_name": "johhanlin-hermes",
      "purpose": "HSBC 外匯交易顧問",
      "status": "pending"
    },
    "alanlin": {
      "namespace": "alanlin-hermes",
      "domain": "alanlin-hermes.woowtech.io",
      "tunnel_name": "alanlin-hermes",
      "purpose": "通用 AI 助手",
      "status": "pending"
    },
    "torchmedia": {
      "namespace": "torchmedia-hermes",
      "domain": "torchmedia-hermes.woowtech.io",
      "tunnel_name": "torchmedia-hermes",
      "purpose": "通用 AI 助手",
      "status": "pending"
    }
  }
}
```

- [ ] **Step 2: Validate JSON**

```bash
python3 -m json.tool hermes/instances/instances.json > /dev/null && echo "JSON valid"
```

- [ ] **Step 3: Commit**

```bash
git add hermes/instances/instances.json
git commit -m "feat(hermes): add instance registry with 5 Hermes instances

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Create `deploy-instance.sh` — Multi-Instance Deployer

**Files:**
- Create: `hermes/deploy-instance.sh`

This is the core script. Given an instance name (e.g. `apporoalan`), it:
1. Reads `instances.json` for config
2. Copies templates to `instances/<name>/k8s/`
3. Substitutes all placeholders with instance values
4. Runs `init-cloudflare-hermes.py` for the instance
5. Generates secrets from cf-config.json + env vars
6. Applies all manifests
7. Waits for rollouts
8. Configures Cloudflare route

- [ ] **Step 1: Create deploy-instance.sh**

```bash
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
# Update the init-config container's config.yaml generation in 07-hermes-webui.yaml
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
```

- [ ] **Step 2: Make executable**

```bash
chmod +x hermes/deploy-instance.sh
```

- [ ] **Step 3: Verify syntax**

```bash
bash -n hermes/deploy-instance.sh && echo "Syntax OK"
```

- [ ] **Step 4: Commit**

```bash
git add hermes/deploy-instance.sh
git commit -m "feat(hermes): add multi-instance deployer script

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Create Per-Instance Test Runner

**Files:**
- Create: `hermes/tests/test-instance.sh`

A parameterized wrapper around the existing test framework that can test any instance by namespace/domain.

- [ ] **Step 1: Create test-instance.sh**

```bash
#!/bin/bash
set -uo pipefail

# =============================================================
# Hermes Per-Instance Test Runner
# Usage: ./test-instance.sh <instance-name>
# Example: ./test-instance.sh apporoalan
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_DIR="$(dirname "$SCRIPT_DIR")"
INSTANCES_JSON="${HERMES_DIR}/instances/instances.json"

INSTANCE_NAME="${1:-}"
[[ -z "$INSTANCE_NAME" ]] && { echo "Usage: $0 <instance-name>"; exit 1; }

# Read instance config
INST=$(python3 -c "
import json, sys
data = json.load(open('${INSTANCES_JSON}'))
inst = data['instances'].get('${INSTANCE_NAME}')
if not inst: sys.exit(1)
print(inst['namespace'])
print(inst['domain'])
" 2>/dev/null) || { echo "Instance '${INSTANCE_NAME}' not found"; exit 1; }

NAMESPACE=$(echo "$INST" | sed -n '1p')
DOMAIN=$(echo "$INST" | sed -n '2p')

echo ""
echo "============================================================"
echo "  Hermes Instance Test: ${INSTANCE_NAME}"
echo "  Namespace: ${NAMESPACE}  Domain: ${DOMAIN}"
echo "============================================================"

# Create instance-specific config.env override
# Round scripts source config.env which would reset NAMESPACE/DOMAIN to WoowTech defaults.
# We write a temp config.env that overrides those values, then point SCRIPT_DIR at it.
TEMP_DIR=$(mktemp -d)
cp "$SCRIPT_DIR/lib/assert.sh" "$TEMP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/lib/report.sh" "$TEMP_DIR/" 2>/dev/null || true
mkdir -p "$TEMP_DIR/lib"
cp "$SCRIPT_DIR/lib/assert.sh" "$TEMP_DIR/lib/"
cp "$SCRIPT_DIR/lib/report.sh" "$TEMP_DIR/lib/"

# Write instance-specific config.env
cat > "$TEMP_DIR/config.env" <<CFGEOF
# Auto-generated for instance: ${INSTANCE_NAME}
source "$SCRIPT_DIR/config.env"
# Override instance-specific values
export NAMESPACE="${NAMESPACE}"
export DOMAIN="${DOMAIN}"
export EXTERNAL_URL="https://${DOMAIN}"
export NP_POSTGRES="${NAMESPACE}-postgresql-policy"
export NP_REDIS="${NAMESPACE}-redis-policy"
CFGEOF

# Point round scripts to our override config
export HERMES_TEST_CONFIG_DIR="$TEMP_DIR"

# Export for round scripts
export NAMESPACE DOMAIN
export EXTERNAL_URL="https://${DOMAIN}"
export NP_POSTGRES="${NAMESPACE}-postgresql-policy"
export NP_REDIS="${NAMESPACE}-redis-policy"

# Source libraries
source "$SCRIPT_DIR/lib/assert.sh"
source "$SCRIPT_DIR/lib/report.sh"

RESULTS_LOG="/tmp/hermes-test-${INSTANCE_NAME}.log"
export RESULTS_LOG
> "$RESULTS_LOG"

TOTAL_PASS=0; TOTAL_FAIL=0; TOTAL_SKIP=0

run_round() {
  local script="$1" name="$2"
  echo ""
  echo ">> $name"
  PASS=0; FAIL=0; SKIP=0; TOTAL=0
  source "$SCRIPT_DIR/lib/assert.sh"
  bash "$script"
  TOTAL_PASS=$((TOTAL_PASS + PASS))
  TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
  TOTAL_SKIP=$((TOTAL_SKIP + SKIP))
  echo "  -- $name: $PASS pass / $FAIL fail / $SKIP skip --"
}

run_round "$SCRIPT_DIR/round1-infra.sh"            "Round 1: Infrastructure"
run_round "$SCRIPT_DIR/round6-llm-integration.sh"   "Round 6: LLM Integration"
run_round "$SCRIPT_DIR/round7-webui-features.sh"    "Round 7: WebGUI Features"

GRAND_TOTAL=$((TOTAL_PASS + TOTAL_FAIL + TOTAL_SKIP))
echo ""
echo "============================================================"
echo "  ${INSTANCE_NAME}: Pass=$TOTAL_PASS Fail=$TOTAL_FAIL Skip=$TOTAL_SKIP Total=$GRAND_TOTAL"
echo "============================================================"

REPORT_FILE="$SCRIPT_DIR/report-${INSTANCE_NAME}-$(date +%Y-%m-%d).html"
generate_html_report "$RESULTS_LOG" "$REPORT_FILE"
echo "Report: $REPORT_FILE"
exit $TOTAL_FAIL
```

- [ ] **Step 2: Make executable and verify**

```bash
chmod +x hermes/tests/test-instance.sh
bash -n hermes/tests/test-instance.sh && echo "Syntax OK"
```

- [ ] **Step 3: Commit**

```bash
git add hermes/tests/test-instance.sh
git commit -m "feat(hermes-tests): add per-instance test runner

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Deploy Instance — Apporoalan Hermes

**Files:** None (execution only, uses deploy-instance.sh)

- [ ] **Step 1: Deploy**

```bash
CF_API_TOKEN="<token>" MINIMAX_API_KEY="<key>" \
  bash hermes/deploy-instance.sh apporoalan
```

- [ ] **Step 2: Verify pods running**

```bash
kubectl -n apporoalan-hermes get pods
```
Expected: 5 pods Running (postgresql, redis, agent, webui, cloudflared)

- [ ] **Step 3: Run instance tests**

```bash
bash hermes/tests/test-instance.sh apporoalan
```

- [ ] **Step 4: Commit instance manifests (sans secrets)**

```bash
git add hermes/instances/apporoalan/ && git reset HEAD hermes/instances/apporoalan/k8s/01-secrets.yaml 2>/dev/null || true
git commit -m "deploy(hermes): apporoalan-hermes instance deployed

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Deploy Instance — Johhanlin Hermes

- [ ] **Step 1: Deploy**

```bash
CF_API_TOKEN="<token>" MINIMAX_API_KEY="<key>" \
  bash hermes/deploy-instance.sh johhanlin
```

- [ ] **Step 2: Verify pods**

```bash
kubectl -n johhanlin-hermes get pods
```

- [ ] **Step 3: Run tests**

```bash
bash hermes/tests/test-instance.sh johhanlin
```

- [ ] **Step 4: Commit**

```bash
git add hermes/instances/johhanlin/ && git reset HEAD hermes/instances/johhanlin/k8s/01-secrets.yaml 2>/dev/null || true
git commit -m "deploy(hermes): johhanlin-hermes instance deployed

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Deploy Instance — Alanlin Hermes

- [ ] **Step 1: Deploy**

```bash
CF_API_TOKEN="<token>" MINIMAX_API_KEY="<key>" \
  bash hermes/deploy-instance.sh alanlin
```

- [ ] **Step 2: Verify pods**

```bash
kubectl -n alanlin-hermes get pods
```

- [ ] **Step 3: Run tests**

```bash
bash hermes/tests/test-instance.sh alanlin
```

- [ ] **Step 4: Commit**

```bash
git add hermes/instances/alanlin/ && git reset HEAD hermes/instances/alanlin/k8s/01-secrets.yaml 2>/dev/null || true
git commit -m "deploy(hermes): alanlin-hermes instance deployed

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Deploy Instance — TorchMedia Hermes

- [ ] **Step 1: Deploy**

```bash
CF_API_TOKEN="<token>" MINIMAX_API_KEY="<key>" \
  bash hermes/deploy-instance.sh torchmedia
```

- [ ] **Step 2: Verify pods**

```bash
kubectl -n torchmedia-hermes get pods
```

- [ ] **Step 3: Run tests**

```bash
bash hermes/tests/test-instance.sh torchmedia
```

- [ ] **Step 4: Commit**

```bash
git add hermes/instances/torchmedia/ && git reset HEAD hermes/instances/torchmedia/k8s/01-secrets.yaml 2>/dev/null || true
git commit -m "deploy(hermes): torchmedia-hermes instance deployed

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Verify All 5 Instances Running

- [ ] **Step 1: Check all namespaces**

```bash
for NS in hermes apporoalan-hermes johhanlin-hermes alanlin-hermes torchmedia-hermes; do
  echo "=== $NS ==="
  kubectl -n "$NS" get pods --no-headers | head -6
  echo ""
done
```

Expected: All 5 namespaces show 5 Running pods each.

- [ ] **Step 2: Check all external URLs**

```bash
for DOMAIN in woowtech-hermes apporoalan-hermes johhanlin-hermes alanlin-hermes torchmedia-hermes; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 -k "https://${DOMAIN}.woowtech.io")
  echo "$DOMAIN: HTTP $CODE"
done
```

Expected: All return HTTP 200 or 302.

- [ ] **Step 3: Update instances.json — all deployed**

Verify all instances show `"status": "deployed"` in `instances.json`.

- [ ] **Step 4: Final commit**

```bash
git add hermes/instances/instances.json
git commit -m "deploy(hermes): all 5 instances verified running

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Summary

| Task | Deliverable | Tests |
|------|------------|-------|
| Task 1 | Template K8s manifests (`hermes/template/k8s/`) | grep validation |
| Task 2 | Instance registry (`instances.json`) | JSON validation |
| Task 3 | `deploy-instance.sh` multi-instance deployer | syntax check |
| Task 4 | `test-instance.sh` per-instance test runner | syntax check |
| Task 5 | Apporoalan Hermes deployed | Round 1+6+7 tests |
| Task 6 | Johhanlin Hermes deployed | Round 1+6+7 tests |
| Task 7 | Alanlin Hermes deployed | Round 1+6+7 tests |
| Task 8 | TorchMedia Hermes deployed | Round 1+6+7 tests |
| Task 9 | All 5 instances verified | kubectl + curl |
