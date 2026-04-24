#!/usr/bin/env bash
# Deploy woow_pos_portal_style addon to Odoo K8s pod
# Usage: ./scripts/deploy-pos-portal-style.sh [NAMESPACE] [POD_NAME]
#
# Copies the addon to the Odoo extra-addons PVC and triggers module install.

set -euo pipefail

NAMESPACE="${1:-harumi}"
POD="${2:-}"
ADDON_DIR="$(cd "$(dirname "$0")/../addons/woow_pos_portal_style" && pwd)"
DEST="/mnt/extra-addons/woow_pos_portal_style"

# Auto-detect pod if not specified
if [ -z "$POD" ]; then
    POD=$(kubectl -n "$NAMESPACE" get pod -l app.kubernetes.io/name=odoo -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || \
          kubectl -n "$NAMESPACE" get pod -l app=odoo -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
    if [ -z "$POD" ]; then
        echo "ERROR: Could not find Odoo pod in namespace '$NAMESPACE'"
        echo "Usage: $0 [NAMESPACE] [POD_NAME]"
        exit 1
    fi
fi

echo "=== Deploy woow_pos_portal_style ==="
echo "  Namespace: $NAMESPACE"
echo "  Pod:       $POD"
echo "  Source:    $ADDON_DIR"
echo ""

# Copy addon files to pod
echo "Copying addon files..."
kubectl -n "$NAMESPACE" exec "$POD" -c odoo -- mkdir -p "$DEST/static/src/css" "$DEST/static/src/js" "$DEST/static/src/img" "$DEST/static/description"

kubectl cp "$ADDON_DIR/__init__.py"      "$NAMESPACE/$POD:$DEST/__init__.py"       -c odoo
kubectl cp "$ADDON_DIR/__manifest__.py"  "$NAMESPACE/$POD:$DEST/__manifest__.py"   -c odoo
kubectl cp "$ADDON_DIR/static/src/css/pos_portal_cards.css" "$NAMESPACE/$POD:$DEST/static/src/css/pos_portal_cards.css" -c odoo
kubectl cp "$ADDON_DIR/static/src/js/pos_portal_cards.js"   "$NAMESPACE/$POD:$DEST/static/src/js/pos_portal_cards.js"   -c odoo
kubectl cp "$ADDON_DIR/static/src/img/icon_pos.svg"         "$NAMESPACE/$POD:$DEST/static/src/img/icon_pos.svg"         -c odoo
kubectl cp "$ADDON_DIR/static/src/img/icon_kitchen.svg"     "$NAMESPACE/$POD:$DEST/static/src/img/icon_kitchen.svg"     -c odoo
kubectl cp "$ADDON_DIR/static/description/icon.svg"         "$NAMESPACE/$POD:$DEST/static/description/icon.svg"         -c odoo

# Fix permissions
kubectl -n "$NAMESPACE" exec "$POD" -c odoo -- chmod -R a+rX "$DEST"

echo ""
echo "=== Addon copied successfully ==="
echo ""
echo "Next steps:"
echo "  1. Go to Odoo > Settings > Apps > Update Apps List"
echo "  2. Search for 'Woow POS Portal Style'"
echo "  3. Click Install"
echo ""
echo "Or install via CLI:"
echo "  kubectl -n $NAMESPACE exec $POD -c odoo -- odoo -d odoo -i woow_pos_portal_style --stop-after-init"
