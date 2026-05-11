#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# Mujimed Odoo 18 - K3s Deployment Script
#
# Deploys:
#   - PostgreSQL 16 (db/user/pass: mujimed)
#   - Odoo 18 with Taiwan locale + WOOWTECH custom addons
#   - Cloudflare Tunnel -> mujimed-odoo.woowtech.io
#
# Prerequisites:
#   - kubectl configured for target K3s cluster
#   - curl and jq installed
#
# Usage:
#   ./deploy.sh
###############################################################################

CF_API_TOKEN="REDACTED_CF_API_TOKEN"
DOMAIN="mujimed-odoo.woowtech.io"
TUNNEL_NAME="mujimed-odoo"
NAMESPACE="mujimed-odoo"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==========================================="
echo " Mujimed Odoo 18 - K3s Deployment"
echo "==========================================="
echo ""

# ─── Preflight checks ────────────────────────────────────────────────────
for cmd in kubectl curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd is required but not installed."
        exit 1
    fi
done

# ─── Step 1: Cloudflare Tunnel Setup ─────────────────────────────────────
echo "[1/5] Setting up Cloudflare Tunnel..."

# Get account ID from zone (zone-scoped tokens don't list accounts)
CF_ZONES=$(curl -sf -X GET "https://api.cloudflare.com/client/v4/zones?name=woowtech.io" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")
CF_ZONE_ID=$(echo "$CF_ZONES" | jq -r '.result[0].id')
CF_ACCOUNT_ID=$(echo "$CF_ZONES" | jq -r '.result[0].account.id')

if [ -z "$CF_ZONE_ID" ] || [ "$CF_ZONE_ID" = "null" ]; then
    echo "  ERROR: Could not find zone for woowtech.io"
    echo "  Check your CF_API_TOKEN"
    exit 1
fi
echo "  Account ID: $CF_ACCOUNT_ID"
echo "  Zone ID: $CF_ZONE_ID"

# Check if tunnel already exists
EXISTING_TUNNEL=$(curl -sf -X GET \
    "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/tunnels?name=$TUNNEL_NAME&is_deleted=false" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")
TUNNEL_ID=$(echo "$EXISTING_TUNNEL" | jq -r '.result[0].id // empty')

if [ -z "$TUNNEL_ID" ]; then
    echo "  Creating tunnel: $TUNNEL_NAME"
    TUNNEL_SECRET=$(openssl rand -base64 32)
    CREATE_RESULT=$(curl -sf -X POST \
        "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/tunnels" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{\"name\":\"$TUNNEL_NAME\",\"tunnel_secret\":\"$TUNNEL_SECRET\",\"config_src\":\"cloudflare\"}")
    TUNNEL_ID=$(echo "$CREATE_RESULT" | jq -r '.result.id')

    if [ -z "$TUNNEL_ID" ] || [ "$TUNNEL_ID" = "null" ]; then
        echo "  ERROR: Failed to create tunnel"
        echo "  Response: $CREATE_RESULT"
        exit 1
    fi
    echo "  Created tunnel: $TUNNEL_ID"
else
    echo "  Using existing tunnel: $TUNNEL_ID"
fi

# Get tunnel token
TUNNEL_TOKEN_RESULT=$(curl -sf -X GET \
    "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")
CF_TUNNEL_TOKEN=$(echo "$TUNNEL_TOKEN_RESULT" | jq -r '.result')

if [ -z "$CF_TUNNEL_TOKEN" ] || [ "$CF_TUNNEL_TOKEN" = "null" ]; then
    echo "  ERROR: Failed to get tunnel token"
    exit 1
fi
echo "  Tunnel token retrieved"

# Configure tunnel ingress rules
echo "  Configuring tunnel ingress -> http://mujimed-odoo-svc:8069"
INGRESS_RESULT=$(curl -sf -X PUT \
    "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
        \"config\": {
            \"ingress\": [
                {
                    \"hostname\": \"$DOMAIN\",
                    \"service\": \"http://mujimed-odoo-svc.${NAMESPACE}.svc.cluster.local:8069\",
                    \"originRequest\": {
                        \"httpHostHeader\": \"$DOMAIN\",
                        \"noTLSVerify\": true
                    }
                },
                {
                    \"service\": \"http_status:404\"
                }
            ]
        }
    }")
echo "  Ingress rules configured"

# Create/update DNS CNAME record
echo "  Setting up DNS: $DOMAIN -> $TUNNEL_ID.cfargotunnel.com"
EXISTING_DNS=$(curl -sf -X GET \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$DOMAIN&type=CNAME" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json")
DNS_RECORD_ID=$(echo "$EXISTING_DNS" | jq -r '.result[0].id // empty')

DNS_DATA="{\"type\":\"CNAME\",\"name\":\"$DOMAIN\",\"content\":\"$TUNNEL_ID.cfargotunnel.com\",\"proxied\":true}"

if [ -z "$DNS_RECORD_ID" ]; then
    curl -sf -X POST \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "$DNS_DATA" >/dev/null
    echo "  DNS CNAME record created"
else
    curl -sf -X PUT \
        "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$DNS_RECORD_ID" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "$DNS_DATA" >/dev/null
    echo "  DNS CNAME record updated"
fi

echo "  [OK] Cloudflare Tunnel setup complete"
echo ""

# ─── Step 2: Create namespace and secrets ─────────────────────────────────
echo "[2/5] Creating namespace and secrets..."
kubectl apply -f "$SCRIPT_DIR/00-namespace.yaml"

kubectl create secret generic mujimed-secrets \
    --namespace="$NAMESPACE" \
    --from-literal=POSTGRES_PASSWORD=mujimed \
    --from-literal=CF_TUNNEL_TOKEN="$CF_TUNNEL_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "  [OK] Namespace and secrets ready"
echo ""

# ─── Step 3: Deploy PostgreSQL ────────────────────────────────────────────
echo "[3/5] Deploying PostgreSQL 16..."
kubectl apply -f "$SCRIPT_DIR/01-postgres.yaml"

echo "  Waiting for PostgreSQL to be ready..."
kubectl rollout status deployment/mujimed-db -n "$NAMESPACE" --timeout=180s
echo "  [OK] PostgreSQL is running"
echo ""

# ─── Step 4: Deploy Odoo 18 ──────────────────────────────────────────────
echo "[4/5] Deploying Odoo 18..."
kubectl apply -f "$SCRIPT_DIR/02-odoo.yaml"

echo "  Odoo is starting (first boot takes 5-10 minutes for module installation)"
echo ""

# ─── Step 5: Deploy Cloudflare Tunnel ─────────────────────────────────────
echo "[5/5] Deploying Cloudflare Tunnel..."
kubectl apply -f "$SCRIPT_DIR/03-cloudflared.yaml"
echo "  [OK] Cloudflared deployed"
echo ""

# ─── Wait for Odoo readiness ─────────────────────────────────────────────
echo "Waiting for Odoo to become ready..."
echo "(Monitor: kubectl logs -f deployment/mujimed-odoo -n $NAMESPACE)"
echo ""

if kubectl rollout status deployment/mujimed-odoo -n "$NAMESPACE" --timeout=900s; then
    echo ""
    echo "==========================================="
    echo " Deployment Complete!"
    echo "==========================================="
    echo ""
    echo "  URL:        https://$DOMAIN"
    echo "  Admin:      admin / admin"
    echo "  Database:   mujimed"
    echo "  DB User:    mujimed"
    echo "  DB Pass:    mujimed"
    echo ""
    echo "  Installed modules: base, web (clean Odoo 18)"
    echo "  Custom addons: install manually via Apps menu"
    echo ""
    echo "  Taiwan config:"
    echo "    - Language:  Traditional Chinese (zh_TW)"
    echo "    - Currency:  TWD"
    echo "    - Timezone:  Asia/Taipei"
    echo ""
else
    echo ""
    echo "WARNING: Odoo deployment is still initializing."
    echo "Check logs: kubectl logs -f deployment/mujimed-odoo -n $NAMESPACE"
    echo "The service will be available at https://$DOMAIN once ready."
fi
