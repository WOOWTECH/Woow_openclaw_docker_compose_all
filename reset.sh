#!/bin/sh
set -e

NAMESPACE="openclaw-tenant-1"

confirm() {
  printf "⚠️  This will DELETE all OpenClaw data in namespace '%s'. Continue? [y/N] " "$NAMESPACE"
  read -r ans
  case "$ans" in [yY]*) ;; *) echo "Aborted."; exit 0;; esac
}

[ "$1" = "-y" ] || confirm

echo "===> Scaling down deployments..."
kubectl -n "$NAMESPACE" scale deployment openclaw-gateway --replicas=0 2>/dev/null || true
kubectl -n "$NAMESPACE" scale deployment openclaw-db --replicas=0 2>/dev/null || true
kubectl -n "$NAMESPACE" scale deployment setup-wizard --replicas=0 2>/dev/null || true

echo "===> Deleting PVC (database data)..."
kubectl -n "$NAMESPACE" delete pvc openclaw-db-pvc --ignore-not-found 2>/dev/null || true

echo "===> Deleting secrets..."
kubectl -n "$NAMESPACE" delete secret openclaw-secrets --ignore-not-found 2>/dev/null || true

echo "===> Cleaning Cloudflare tunnel connections..."
if [ -f cf-config.json ]; then
  CF_API_TOKEN=$(python3 -c "import json; print(json.load(open('cf-config.json'))['CF_API_TOKEN'])")
  CF_ACCOUNT_ID=$(python3 -c "import json; print(json.load(open('cf-config.json'))['CF_ACCOUNT_ID'])")
  CF_TUNNEL_ID=$(python3 -c "import json; print(json.load(open('cf-config.json'))['CF_TUNNEL_ID'])")
  curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/cfd_tunnel/${CF_TUNNEL_ID}/connections" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" > /dev/null 2>&1
  echo "  Tunnel connections cleaned."
fi

echo "===> Restarting cloudflared..."
kubectl -n "$NAMESPACE" rollout restart deployment cloudflared 2>/dev/null || true

echo "===> Done. Run ./deploy.sh to redeploy."
