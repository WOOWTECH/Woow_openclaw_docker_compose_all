#!/bin/bash
# MCP OAuth Button Patch — Show Authenticate for ALL HTTP MCP servers
#
# What: Patches the React SPA to show the Authenticate button for every
#       HTTP transport MCP server, not just those with auth:oauth configured.
#
# When:  Run after any pod restart (image pulls wipe runtime patches).
#
# How:   sed replaces the visibility condition in the compiled JS bundle:
#          BEFORE: e.auth===`oauth`&&  (only auth:oauth servers)
#          AFTER:  e.transport===`http`&&  (all HTTP servers)
#
# Prerequisites:
#   - HERMES_DASHBOARD_PUBLIC_URL must be set on the agent container
#     (e.g., https://woowtech-dashboard.woowtech.io)
#   - MCP servers needing OAuth should have auth:oauth in config
#     for the agent's background reconnect to work.
#
set -euo pipefail
CONTEXT="${1:-woow-k3s}"
NS="${2:-hermes}"
KC="kubectl --context $CONTEXT -n $NS"
POD=$($KC get pod -l app=hermes -o jsonpath='{.items[0].metadata.name}')
echo "Pod: $POD"

# 1. Find the JS bundle filename
JS_FILE=$($KC exec "$POD" -c hermes-agent -- \
  find /opt/hermes/hermes_cli/web_dist/assets -name 'index-*.js' -type f 2>/dev/null | head -1)
echo "JS bundle: $JS_FILE"

# 2. Apply the sed replacement
$KC exec "$POD" -c hermes-agent -- \
  sed -i "s/e\.auth===\`oauth\`&&(0,W\.jsx)(G,{ghost:\!0,size:\`sm\`,title:\`Authenticate with OAuth\`/e.transport===\`http\`\&\&(0,W.jsx)(G,{ghost:!0,size:\`sm\`,title:\`Authenticate with OAuth\`/" \
  "$JS_FILE"

# 3. Cache-bust: copy to a new filename and update index.html
OLD_NAME=$(basename "$JS_FILE")
NEW_NAME="index-OAuthFix$(date +%s).js"
$KC exec "$POD" -c hermes-agent -- bash -c "
  cp '$JS_FILE' '$(dirname $JS_FILE)/$NEW_NAME'
  sed -i 's/$OLD_NAME/$NEW_NAME/g' /opt/hermes/hermes_cli/web_dist/index.html
"

# 4. Verify
MATCHES=$($KC exec "$POD" -c hermes-agent -- \
  grep -c "e\.transport===.http.\&\&(0,W\.jsx)(G,{ghost" "$(dirname $JS_FILE)/$NEW_NAME" 2>/dev/null)
if [ "$MATCHES" = "1" ]; then
  echo "✅ Patch applied successfully. Reload the Dashboard MCP page."
else
  echo "❌ Patch verification failed (expected 1 match, got $MATCHES)"
  exit 1
fi
