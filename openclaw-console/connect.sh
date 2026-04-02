#!/bin/sh
# ttyd wrapper: kubectl exec into the openclaw-gateway container
NAMESPACE="openclaw-tenant-1"
LABEL="app=openclaw-gateway"
CONTAINER="openclaw-gateway"

while true; do
  POD=$(kubectl get pod -l "$LABEL" -n "$NAMESPACE" \
    --field-selector=status.phase=Running \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  if [ -n "$POD" ]; then
    echo "Connecting to $POD ..."
    kubectl exec -it "$POD" -n "$NAMESPACE" -c "$CONTAINER" -- sh
    echo ""
    echo "Session ended. Reconnecting in 2s..."
    sleep 2
  else
    echo "Waiting for openclaw-gateway pod..."
    sleep 5
  fi
done
