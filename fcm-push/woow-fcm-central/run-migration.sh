#!/usr/bin/env bash
# Run schema migrations against central postgres.
#
# PREFERRED: run alembic upgrade head from the woow_fcm_central repo against
# the central postgres. This is the canonical migration path — the raw SQL
# fallback below is a convenience for environments without a local Python/pip.
#
# IMPORTANT — schema drift warning:
#   If reusing a DB from a prior deploy that was populated by raw SQL (not
#   alembic), the alembic_version table will be MISSING and alembic will
#   try to replay all migrations, hitting "already exists" errors. A fresh
#   deploy MUST start from a CLEAN DB or stamp the alembic version first:
#     alembic stamp head   # (marks the DB as up-to-date without running DDL)
#   The rate_counter table had a known drift: the raw SQL below uses
#   (box_uuid, window_key) but the alembic migration uses (box_uuid,
#   bucket_start). Always prefer alembic upgrade head over raw SQL.
#
# Usage:
#   # Option A: alembic (preferred, requires woow_fcm_central repo + pip)
#   bash fcm-push/woow-fcm-central/run-migration.sh --alembic [PG_PASSWORD]
#
#   # Option B: raw SQL fallback (idempotent, no pip needed)
#   bash fcm-push/woow-fcm-central/run-migration.sh [PG_PASSWORD]
set -euo pipefail

NS="woow-fcm-central"
PW="${2:-${1:-REPLACE-AT-DEPLOY-TIME}}"
MODE="sql"

if [ "${1:-}" = "--alembic" ]; then
  MODE="alembic"
  PW="${2:-REPLACE-AT-DEPLOY-TIME}"
fi

echo "[migration] Waiting for postgres..."
kubectl -n "$NS" wait --for=condition=ready pod -l app=postgres --timeout=120s

if [ "$MODE" = "alembic" ]; then
  echo "[migration] Running alembic upgrade head (preferred path)..."
  echo "[migration] Starting port-forward..."
  kubectl -n "$NS" port-forward svc/postgres 15432:5432 &
  PF_PID=$!
  sleep 2

  CENTRAL_REPO="${WOOW_FCM_CENTRAL_REPO:-/tmp/woow_fcm_central}"
  if [ ! -d "$CENTRAL_REPO/migrations" ]; then
    echo "[migration] ERROR: woow_fcm_central repo not found at $CENTRAL_REPO"
    echo "[migration] Clone it first: git clone https://github.com/WOOWTECH/woow_fcm_central.git $CENTRAL_REPO"
    kill "$PF_PID" 2>/dev/null || true
    exit 1
  fi

  cd "$CENTRAL_REPO"
  DATABASE_URL="postgresql://fcm_central:${PW}@localhost:15432/fcm_central" \
    python3 -m alembic upgrade head

  if [ $? -ne 0 ]; then
    echo "[migration] ERROR: alembic upgrade head FAILED"
    echo "[migration] If the DB was populated by raw SQL, run: alembic stamp head"
    kill "$PF_PID" 2>/dev/null || true
    exit 1
  fi

  echo "[migration] alembic upgrade head succeeded."
  kill "$PF_PID" 2>/dev/null || true
  exit 0
fi

# --- Raw SQL fallback (idempotent) ---
echo "[migration] Applying schema via raw SQL..."

RESULT=$(cat <<'EOSQL' | kubectl -n "$NS" exec -i postgres-0 -- sh -c "PGPASSWORD=\"${PW}\" psql -U fcm_central -d fcm_central -v ON_ERROR_STOP=1" 2>&1
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS boxes (box_uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(), api_key_hash CHAR(64) NOT NULL, api_key_label VARCHAR(16) NOT NULL DEFAULT '', customer_label VARCHAR(255) NOT NULL DEFAULT '', status VARCHAR(16) NOT NULL DEFAULT 'active', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS rate_counter (box_uuid UUID NOT NULL REFERENCES boxes(box_uuid), window_key VARCHAR(32) NOT NULL, count INT NOT NULL DEFAULT 0, PRIMARY KEY (box_uuid, window_key));
CREATE TABLE IF NOT EXISTS box_audit_log (id BIGSERIAL PRIMARY KEY, box_uuid UUID, event TEXT NOT NULL, detail JSONB, ts TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS admin_users (id SERIAL PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
ALTER TABLE boxes ADD COLUMN IF NOT EXISTS tenant_id TEXT;
DO $$ BEGIN ALTER TABLE boxes ADD CONSTRAINT boxes_tenant_id_key UNIQUE (tenant_id); EXCEPTION WHEN duplicate_table THEN NULL; END $$;
CREATE TABLE IF NOT EXISTS namespace_tenant_map (namespace TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, created_by TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE INDEX IF NOT EXISTS namespace_tenant_map_tenant ON namespace_tenant_map(tenant_id);
CREATE TABLE IF NOT EXISTS enrollment_audit (id BIGSERIAL PRIMARY KEY, tenant_id TEXT, namespace TEXT, sa TEXT, jti TEXT, source_ip TEXT, event TEXT NOT NULL, ts TIMESTAMPTZ NOT NULL DEFAULT NOW());
CREATE TABLE IF NOT EXISTS enroll_tokens (token_hash CHAR(64) PRIMARY KEY, tenant_id TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL, consumed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
EOSQL
)

echo "$RESULT"

if echo "$RESULT" | grep -qi "ERROR"; then
  echo "[migration] ERROR: SQL migration failed. See output above."
  exit 1
fi

echo "[migration] Verifying tables..."
echo "\dt" | kubectl -n "$NS" exec -i postgres-0 -- sh -c "PGPASSWORD=\"${PW}\" psql -U fcm_central -d fcm_central"
echo "[migration] Done."
