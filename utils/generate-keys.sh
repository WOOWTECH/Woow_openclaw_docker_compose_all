#!/bin/bash
# Generate secure passwords and tokens for OpenClaw deployment
# 為 OpenClaw 部署產生安全密碼和 token

set -e

echo "============================================"
echo "  OpenClaw — Key Generator"
echo "============================================"
echo ""

GATEWAY_TOKEN=$(openssl rand -hex 16)
DB_PASSWORD=$(openssl rand -hex 16)

echo "Generated credentials:"
echo ""
echo "  GATEWAY_TOKEN=${GATEWAY_TOKEN}"
echo "  DB_PASSWORD=${DB_PASSWORD}"
echo ""

if [ "$1" = "--write" ]; then
  if [ -f .env ]; then
    echo "⚠️  .env already exists. Skipping write."
  else
    cp .env.example .env
    sed -i "s/your-gateway-token/${GATEWAY_TOKEN}/" .env
    sed -i "s/your-database-password/${DB_PASSWORD}/" .env
    echo "✅ Written to .env"
  fi
fi

echo "Usage: Copy these values into the Setup Wizard form."
echo "Or run: $0 --write  to auto-fill .env"
