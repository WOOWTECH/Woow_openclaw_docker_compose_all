#!/bin/bash
set -e

# Workaround: OpenChamber's SPA catch-all uses res.sendFile() with
# an absolute path. The send module (used by Express 5) applies
# dotfile detection to every path component. Because the yarn
# global install lives under /usr/local/share/.config/..., the
# ".config" segment triggers dotfiles="ignore" -> 404 for ALL
# SPA routes (including /mcp/oauth/callback used by MCP OAuth).
# Symlinking the dist dir to a dotfile-free path fixes this.
DIST_SRC="/usr/local/share/.config/yarn/global/node_modules/@openchamber/web/dist"
if [ -d "$DIST_SRC" ]; then
  ln -sfn "$DIST_SRC" /tmp/openchamber-dist
  export OPENCHAMBER_DIST_DIR=/tmp/openchamber-dist
fi

# Set a known password BEFORE openchamber starts so both the
# OpenCode server and OpenChamber proxy use the same password.
export OPENCODE_SERVER_PASSWORD="vk-oc-shared-secret-2026"

echo "Starting OpenChamber on :3080..."
openchamber serve --host 0.0.0.0 --port 3080 --ui-password "${OPENCHAMBER_UI_PASSWORD:-lemon0116}"

# openchamber daemonizes itself, so keep container alive
sleep 2
LOG_DIR="$HOME/.config/openchamber/logs"
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/server.log"
exec tail -f "$LOG_DIR/server.log" /dev/null
