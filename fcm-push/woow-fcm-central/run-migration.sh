#!/usr/bin/env bash
# Run schema migrations against central postgres.
#
# This applies the full schema (boxes, rate_counter, box_audit_log,
# admin_users, self-enrollment tables) via kubectl exec into the
# postgres-0 pod. Idempotent — safe to re-run.
#
# Prerequisites:
#   - postgres-0 is Ready in woow-fcm-central
#   - POSTGRES_PASSWORD matches the deployed db-credentials secret
#
# Usage:
#   bash fcm-push/woow-fcm-central/run-migration.sh [POSTGRES_PASSWORD]
set -euo pipefail

NS="woow-fcm-central"
PW="${1:-REPLACE-AT-DEPLOY-TIME}"

echo "[migration] Waiting for postgres..."
kubectl -n "$NS" wait --for=condition=ready pod -l app=postgres --timeout=120s

echo "[migration] Applying schema..."
cat <<'EOSQL' | kubectl -n "$NS" exec -i postgres-0 -- sh -c "PGPASSWORD=\"$PW\" psql -U fcm_central -d fcm_central"
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

echo "[migration] Verifying tables..."
echo "\dt" | kubectl -n "$NS" exec -i postgres-0 -- sh -c "PGPASSWORD=\"$PW\" psql -U fcm_central -d fcm_central"
echo "[migration] Done."
