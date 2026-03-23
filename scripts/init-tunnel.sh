#!/bin/bash
# ===========================================
# OpenClaw - Cloudflare Tunnel Initialization
# 建立 Cloudflare Tunnel 並設定 DNS
# ===========================================
# This script:
#   1. Creates a Cloudflare tunnel named "openclaw"
#   2. Configures ingress to route traffic to the gateway
#   3. Creates a CNAME DNS record for the domain
#   4. Retrieves the tunnel token
#   5. Updates .env with CF_TUNNEL_ID and CF_TUNNEL_TOKEN
# ===========================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env"

# Load .env
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file not found at $ENV_FILE"
    echo "Copy .env.example to .env and fill in the values first."
    exit 1
fi
set -a
source "$ENV_FILE"
set +a

# Validate required variables
if [ -z "${CF_API_TOKEN:-}" ]; then
    echo "ERROR: CF_API_TOKEN is not set in .env"
    exit 1
fi
if [ -z "${CF_ACCOUNT_ID:-}" ]; then
    echo "ERROR: CF_ACCOUNT_ID is not set in .env"
    exit 1
fi

DOMAIN="${CF_TUNNEL_DOMAIN:-woowtech-openclaw.woowtech.io}"
TUNNEL_NAME="openclaw"
GATEWAY_PORT="${GATEWAY_PORT:-18789}"
CF_API="https://api.cloudflare.com/client/v4"
AUTH_HEADER="Authorization: Bearer ${CF_API_TOKEN}"

echo "============================================"
echo " OpenClaw Cloudflare Tunnel Initialization"
echo "============================================"
echo "Domain:  ${DOMAIN}"
echo "Tunnel:  ${TUNNEL_NAME}"
echo "Gateway: localhost:${GATEWAY_PORT}"
echo "============================================"

# -------------------------------------------------------------------
# Step 1: Check if tunnel already exists
# -------------------------------------------------------------------
echo ""
echo "[1/5] Checking for existing tunnel..."

EXISTING=$(curl -s "${CF_API}/accounts/${CF_ACCOUNT_ID}/cfd_tunnel?name=${TUNNEL_NAME}&is_deleted=false" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json")

EXISTING_ID=$(echo "$EXISTING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
results = data.get('result', [])
if results:
    print(results[0]['id'])
else:
    print('')
" 2>/dev/null || echo "")

if [ -n "$EXISTING_ID" ]; then
    echo "  Tunnel '${TUNNEL_NAME}' already exists: ${EXISTING_ID}"
    TUNNEL_ID="$EXISTING_ID"
else
    # -------------------------------------------------------------------
    # Step 2: Create tunnel
    # -------------------------------------------------------------------
    echo "  No existing tunnel found. Creating new tunnel..."

    # Generate a random tunnel secret (32 bytes, base64)
    TUNNEL_SECRET=$(python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")

    CREATE_RESP=$(curl -s -X POST "${CF_API}/accounts/${CF_ACCOUNT_ID}/cfd_tunnel" \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${TUNNEL_NAME}\", \"tunnel_secret\": \"${TUNNEL_SECRET}\", \"config_src\": \"cloudflare\"}")

    TUNNEL_ID=$(echo "$CREATE_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print(data['result']['id'])
else:
    print('ERROR: ' + json.dumps(data.get('errors', [])))
    sys.exit(1)
" 2>/dev/null)

    if [[ "$TUNNEL_ID" == ERROR* ]]; then
        echo "  Failed to create tunnel: $TUNNEL_ID"
        exit 1
    fi
    echo "  Tunnel created: ${TUNNEL_ID}"
fi

# -------------------------------------------------------------------
# Step 3: Configure tunnel ingress
# -------------------------------------------------------------------
echo ""
echo "[2/5] Configuring tunnel ingress..."

CONFIG_RESP=$(curl -s -X PUT "${CF_API}/accounts/${CF_ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/configurations" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -d "{
        \"config\": {
            \"ingress\": [
                {\"hostname\": \"${DOMAIN}\", \"service\": \"http://openclaw-gateway:${GATEWAY_PORT}\"},
                {\"service\": \"http_status:404\"}
            ]
        }
    }")

CONFIG_OK=$(echo "$CONFIG_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "False")

if [ "$CONFIG_OK" = "True" ]; then
    echo "  Ingress configured: ${DOMAIN} -> localhost:${GATEWAY_PORT}"
else
    echo "  WARNING: Ingress configuration may have failed."
    echo "  Response: ${CONFIG_RESP}"
fi

# -------------------------------------------------------------------
# Step 4: Create DNS CNAME record
# -------------------------------------------------------------------
echo ""
echo "[3/5] Creating DNS record..."

# Extract zone name (parent domain)
ZONE_NAME=$(echo "$DOMAIN" | rev | cut -d. -f1-2 | rev)
echo "  Zone: ${ZONE_NAME}"

# Get zone ID
ZONE_RESP=$(curl -s "${CF_API}/zones?name=${ZONE_NAME}" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json")

ZONE_ID=$(echo "$ZONE_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
results = data.get('result', [])
if results:
    print(results[0]['id'])
else:
    print('')
" 2>/dev/null || echo "")

if [ -z "$ZONE_ID" ]; then
    echo "  WARNING: Could not find zone for ${ZONE_NAME}. DNS record not created."
    echo "  You may need to create the CNAME record manually:"
    echo "    ${DOMAIN} -> ${TUNNEL_ID}.cfargotunnel.com"
else
    # Check if CNAME already exists
    DNS_CHECK=$(curl -s "${CF_API}/zones/${ZONE_ID}/dns_records?name=${DOMAIN}&type=CNAME" \
        -H "${AUTH_HEADER}" \
        -H "Content-Type: application/json")

    DNS_EXISTS=$(echo "$DNS_CHECK" | python3 -c "
import sys, json
data = json.load(sys.stdin)
results = data.get('result', [])
if results:
    print(results[0]['id'])
else:
    print('')
" 2>/dev/null || echo "")

    if [ -n "$DNS_EXISTS" ]; then
        # Update existing record
        DNS_RESP=$(curl -s -X PUT "${CF_API}/zones/${ZONE_ID}/dns_records/${DNS_EXISTS}" \
            -H "${AUTH_HEADER}" \
            -H "Content-Type: application/json" \
            -d "{
                \"type\": \"CNAME\",
                \"name\": \"${DOMAIN}\",
                \"content\": \"${TUNNEL_ID}.cfargotunnel.com\",
                \"proxied\": true
            }")
        echo "  DNS record updated: ${DOMAIN} -> ${TUNNEL_ID}.cfargotunnel.com"
    else
        # Create new record
        DNS_RESP=$(curl -s -X POST "${CF_API}/zones/${ZONE_ID}/dns_records" \
            -H "${AUTH_HEADER}" \
            -H "Content-Type: application/json" \
            -d "{
                \"type\": \"CNAME\",
                \"name\": \"${DOMAIN}\",
                \"content\": \"${TUNNEL_ID}.cfargotunnel.com\",
                \"proxied\": true
            }")
        echo "  DNS record created: ${DOMAIN} -> ${TUNNEL_ID}.cfargotunnel.com"
    fi
fi

# -------------------------------------------------------------------
# Step 5: Get tunnel token
# -------------------------------------------------------------------
echo ""
echo "[4/5] Retrieving tunnel token..."

TOKEN_RESP=$(curl -s "${CF_API}/accounts/${CF_ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/token" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json")

TUNNEL_TOKEN=$(echo "$TOKEN_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print(data['result'])
else:
    print('ERROR')
" 2>/dev/null || echo "ERROR")

if [ "$TUNNEL_TOKEN" = "ERROR" ] || [ -z "$TUNNEL_TOKEN" ]; then
    echo "  WARNING: Could not retrieve tunnel token automatically."
    echo "  You can get it from the Cloudflare Zero Trust dashboard."
else
    echo "  Tunnel token retrieved successfully."
fi

# -------------------------------------------------------------------
# Step 6: Update .env file
# -------------------------------------------------------------------
echo ""
echo "[5/5] Updating .env file..."

# Update CF_TUNNEL_ID
if grep -q "^CF_TUNNEL_ID=" "$ENV_FILE"; then
    sed -i "s|^CF_TUNNEL_ID=.*|CF_TUNNEL_ID=${TUNNEL_ID}|" "$ENV_FILE"
else
    echo "CF_TUNNEL_ID=${TUNNEL_ID}" >> "$ENV_FILE"
fi

# Update CF_TUNNEL_TOKEN
if [ "$TUNNEL_TOKEN" != "ERROR" ] && [ -n "$TUNNEL_TOKEN" ]; then
    if grep -q "^CF_TUNNEL_TOKEN=" "$ENV_FILE"; then
        sed -i "s|^CF_TUNNEL_TOKEN=.*|CF_TUNNEL_TOKEN=${TUNNEL_TOKEN}|" "$ENV_FILE"
    else
        echo "CF_TUNNEL_TOKEN=${TUNNEL_TOKEN}" >> "$ENV_FILE"
    fi
    echo "  .env updated with CF_TUNNEL_ID and CF_TUNNEL_TOKEN"
else
    echo "  .env updated with CF_TUNNEL_ID only (token needs manual entry)"
fi

echo ""
echo "============================================"
echo " Tunnel initialization complete!"
echo "============================================"
echo " Tunnel ID:  ${TUNNEL_ID}"
echo " Domain:     ${DOMAIN}"
echo " Target:     localhost:${GATEWAY_PORT}"
echo ""
echo " Next steps:"
echo "   1. Start core services:   podman-compose up -d"
echo "   2. Start tunnel:          podman-compose --profile tunnel up -d cloudflared"
echo "   3. Verify:                curl https://${DOMAIN}"
echo "============================================"
