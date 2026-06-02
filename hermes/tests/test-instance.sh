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

# Copy round scripts to temp dir so they source the override config.env
for f in "$SCRIPT_DIR"/round*.sh; do
  cp "$f" "$TEMP_DIR/"
done

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
  bash "$TEMP_DIR/$(basename "$script")"
  TOTAL_PASS=$((TOTAL_PASS + PASS))
  TOTAL_FAIL=$((TOTAL_FAIL + FAIL))
  TOTAL_SKIP=$((TOTAL_SKIP + SKIP))
  echo "  -- $name: $PASS pass / $FAIL fail / $SKIP skip --"
}

run_round "$SCRIPT_DIR/round1-infra.sh"            "Round 1: Infrastructure"
run_round "$SCRIPT_DIR/round6-llm-integration.sh"   "Round 6: LLM Integration"
run_round "$SCRIPT_DIR/round7-webui-features.sh"    "Round 7: WebGUI Features"

# Cleanup
rm -rf "$TEMP_DIR"

GRAND_TOTAL=$((TOTAL_PASS + TOTAL_FAIL + TOTAL_SKIP))
echo ""
echo "============================================================"
echo "  ${INSTANCE_NAME}: Pass=$TOTAL_PASS Fail=$TOTAL_FAIL Skip=$TOTAL_SKIP Total=$GRAND_TOTAL"
echo "============================================================"

REPORT_FILE="$SCRIPT_DIR/report-${INSTANCE_NAME}-$(date +%Y-%m-%d).html"
generate_html_report "$RESULTS_LOG" "$REPORT_FILE"
echo "Report: $REPORT_FILE"
exit $TOTAL_FAIL
