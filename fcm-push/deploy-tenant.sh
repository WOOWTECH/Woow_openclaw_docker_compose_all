#!/usr/bin/env bash
# deploy-tenant.sh — render + deploy a fresh Odoo 18 + FCM push tenant.
#
# This wraps the tenant-template/ manifests: it renders the __PLACEHOLDERS__,
# creates the required secrets from files/env (NEVER hardcoded, NEVER echoed),
# applies the manifest set, and optionally maps the namespace in central.
#
# It is idempotent: re-running reconciles (kubectl apply + ON CONFLICT mapping).
#
# ---------------------------------------------------------------------------
# USAGE
#   ./deploy-tenant.sh <tenant> <domain> <firebase_project> [dbname]
#
#   <tenant>            DNS-safe slug = namespace + resource prefix  (e.g. bnidistrict)
#   <domain>            public FQDN (informational + cloudflared)    (e.g. bni.woowtech.app)
#   <firebase_project>  Firebase project id                          (e.g. woow-odoo-de2cb)
#   [dbname]            optional; default = <tenant> with dashes removed (alphanumeric)
#
# REQUIRED env (paths to secret material — files are read, values never printed):
#   GHCR_PULL_PAT_FILE     path to a read:packages GitHub PAT (for ghcr.io pulls)
#   GITHUB_CLONE_PAT_FILE  path to a Contents:read GitHub PAT (private plugin clone)
#
# OPTIONAL env:
#   TENANT_ID              stable tenant id for central mapping (default = <tenant>)
#   DBPASS                 postgres password (default: generated via openssl)
#   ADMIN_PASSWD           odoo master password (default: generated via openssl)
#   CENTRAL_PG_PASSWORD    if set, inserts namespace_tenant_map row in central
#   CF_TUNNEL_TOKEN_FILE   if set, also deploys optional-cloudflared/ using this token
#   DEPLOY_MODE            "apply" (default) or "render" (render only, no cluster writes)
#   WORKDIR                render output dir (default: /tmp/fcm-tenant-<tenant>)
# ---------------------------------------------------------------------------
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "[deploy-tenant] $*"; }

# --- args ---
[ $# -ge 3 ] || die "usage: $0 <tenant> <domain> <firebase_project> [dbname]"
TENANT="$1"; DOMAIN="$2"; FIREBASE_PROJECT="$3"
DBNAME="${4:-$(echo "$TENANT" | tr -cd 'a-z0-9')}"
TENANT_ID="${TENANT_ID:-$TENANT}"
DEPLOY_MODE="${DEPLOY_MODE:-apply}"
WORKDIR="${WORKDIR:-/tmp/fcm-tenant-$TENANT}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/tenant-template"

echo "$TENANT" | grep -Eq '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$' || die "tenant must be a DNS label"
echo "$DBNAME" | grep -Eq '^[a-z0-9]+$' || die "dbname must be alphanumeric (no dashes)"
[ -d "$TEMPLATE_DIR" ] || die "tenant-template/ not found next to this script"

# --- generated secrets (only if not supplied) ---
DBPASS="${DBPASS:-$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)}"
ADMIN_PASSWD="${ADMIN_PASSWD:-$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)}"

info "tenant=$TENANT ns=$TENANT db=$DBNAME firebase=$FIREBASE_PROJECT mode=$DEPLOY_MODE"
info "(secret values are generated/loaded but never printed)"

# --- render placeholders into WORKDIR ---
mkdir -p "$WORKDIR"
render() {
  sed -e "s|__TENANT__|$TENANT|g" \
      -e "s|__DBNAME__|$DBNAME|g" \
      -e "s|__DBPASS__|$DBPASS|g" \
      -e "s|__ADMIN_PASSWD__|$ADMIN_PASSWD|g" \
      -e "s|__FIREBASE_PROJECT__|$FIREBASE_PROJECT|g" \
      -e "s|__DOMAIN__|$DOMAIN|g" "$1"
}
for f in "$TEMPLATE_DIR"/*.yaml; do render "$f" > "$WORKDIR/$(basename "$f")"; done
mkdir -p "$WORKDIR/optional-cloudflared"
render "$TEMPLATE_DIR/optional-cloudflared/50-cloudflared.yaml" > "$WORKDIR/optional-cloudflared/50-cloudflared.yaml"
info "rendered manifests -> $WORKDIR  (contains db password; gitignored, delete after use)"

if [ "$DEPLOY_MODE" = "render" ]; then
  info "DEPLOY_MODE=render — stopping before any cluster write. Review $WORKDIR then re-run with DEPLOY_MODE=apply"
  exit 0
fi

# --- preflight gates (fail closed) ---
[ -n "${GHCR_PULL_PAT_FILE:-}" ] && [ -f "$GHCR_PULL_PAT_FILE" ] || die "GHCR_PULL_PAT_FILE must point to a read:packages PAT file"
[ -n "${GITHUB_CLONE_PAT_FILE:-}" ] && [ -f "$GITHUB_CLONE_PAT_FILE" ] || die "GITHUB_CLONE_PAT_FILE must point to a Contents:read PAT file"
kubectl get ns woow-fcm-central >/dev/null 2>&1 || die "central namespace woow-fcm-central missing — deploy central first (DEPLOY-RUNBOOK Phase 2)"

# --- namespace ---
info "applying namespace"
kubectl apply -f "$WORKDIR/00-namespace.yaml"

# --- secrets (created here, not in the manifest set; values never echoed) ---
info "creating tenant secrets (postgres, ghcr-pull, github-token)"
kubectl -n "$TENANT" create secret generic "$TENANT-postgres-secret" \
  --from-literal=POSTGRES_USER="$DBNAME" \
  --from-literal=POSTGRES_PASSWORD="$DBPASS" \
  --from-literal=POSTGRES_DB="$DBNAME" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "$TENANT" create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io --docker-username=WOOWTECH \
  --docker-password="$(cat "$GHCR_PULL_PAT_FILE")" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n "$TENANT" create secret generic github-token \
  --from-literal=token="$(cat "$GITHUB_CLONE_PAT_FILE")" \
  --dry-run=client -o yaml | kubectl apply -f -

# --- central authorization mapping (business gate; unmapped ns -> enroll 403) ---
if [ -n "${CENTRAL_PG_PASSWORD:-}" ]; then
  info "mapping namespace_tenant_map[$TENANT] = $TENANT_ID in central"
  kubectl -n woow-fcm-central exec -i postgres-0 -- \
    sh -c "PGPASSWORD='$CENTRAL_PG_PASSWORD' psql -U fcm_central -d fcm_central -v ON_ERROR_STOP=1 -c \
    \"INSERT INTO namespace_tenant_map (namespace, tenant_id, created_by) VALUES ('$TENANT','$TENANT_ID','deploy-tenant.sh') ON CONFLICT (namespace) DO NOTHING;\""
else
  info "WARNING: CENTRAL_PG_PASSWORD not set — you MUST insert the namespace_tenant_map row manually (see DEPLOY-RUNBOOK Phase 3.4) or self-enroll will 403"
fi

# --- apply the tenant manifest set (non-recursive: skips optional-cloudflared/) ---
info "applying tenant manifests"
kubectl apply -f "$WORKDIR/"

# --- optional cloudflared ---
if [ -n "${CF_TUNNEL_TOKEN_FILE:-}" ] && [ -f "$CF_TUNNEL_TOKEN_FILE" ]; then
  info "creating cloudflared tunnel secret + deploying cloudflared"
  kubectl -n "$TENANT" create secret generic "$TENANT-cf-tunnel-token" \
    --from-literal=TUNNEL_TOKEN="$(cat "$CF_TUNNEL_TOKEN_FILE")" \
    --dry-run=client -o yaml | kubectl apply -f -
  kubectl apply -f "$WORKDIR/optional-cloudflared/"
fi

info "waiting for Odoo rollout (initContainers clone+init can take a few minutes)"
kubectl -n "$TENANT" rollout status deploy/"$TENANT-odoo" --timeout=600s || \
  info "rollout not complete yet — inspect: kubectl -n $TENANT get pods; kubectl -n $TENANT logs deploy/$TENANT-odoo -c init-db"

info "DONE. Run the VERIFY block in DEPLOY-RUNBOOK.md Phase 4 against ns=$TENANT"
info "Remember to delete the rendered dir (holds the db password): rm -rf $WORKDIR"
