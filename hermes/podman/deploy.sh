#!/bin/bash
set -euo pipefail
# =============================================================
# Hermes Agent — Podman 一鍵部署
# =============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# 1. 自動生成 .env (如不存在)
if [ ! -f "$ENV_FILE" ]; then
    cp "${SCRIPT_DIR}/.env.example" "$ENV_FILE"
    sed -i "s/^API_SERVER_KEY=.*/API_SERVER_KEY=$(openssl rand -hex 32)/" "$ENV_FILE"
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)/" "$ENV_FILE"
    sed -i "s/^HERMES_UID=.*/HERMES_UID=$(id -u)/" "$ENV_FILE"
    sed -i "s/^HERMES_GID=.*/HERMES_GID=$(id -g)/" "$ENV_FILE"
    echo "已生成 .env — 請編輯 MINIMAX_API_KEY 後重新執行此腳本"
    exit 0
fi

# 2. 啟動
cd "$SCRIPT_DIR"
podman-compose up -d
echo "等待服務啟動..."
sleep 15
podman-compose ps

# 3. 等待 Agent 就緒
echo "等待 Gateway 就緒..."
for i in $(seq 1 30); do
    HTTP=$(podman exec hermes-agent curl -s -o /dev/null -w "%{http_code}" http://localhost:8642/health 2>/dev/null || echo "000")
    [ "$HTTP" = "200" ] && echo "Gateway OK!" && break
    sleep 5
done

# 4. 修復 TUI 權限
podman exec hermes-agent chown -R hermes:hermes /opt/hermes/ui-tui/ 2>/dev/null || true

# 5. 安裝 Superpowers Skills
if ! podman exec hermes-agent test -f /opt/data/skills/brainstorming/SKILL.md 2>/dev/null; then
    echo "安裝 Superpowers Skills..."
    TMPDIR=$(mktemp -d)
    git clone --depth 1 https://github.com/obra/superpowers.git "$TMPDIR/sp" 2>/dev/null
    tar czf "$TMPDIR/sp.tar.gz" -C "$TMPDIR/sp" skills/
    podman cp "$TMPDIR/sp.tar.gz" hermes-agent:/tmp/
    podman exec hermes-agent tar xzf /tmp/sp.tar.gz -C /opt/data/
    podman exec hermes-agent chown -R 1000:1000 /opt/data/skills
    rm -rf "$TMPDIR"
    echo "14 個 Superpowers Skills 已安裝"
fi

# 6. 安裝 tmux
podman exec hermes-agent sh -c 'which tmux >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq tmux)' 2>/dev/null

echo ""
echo "============================================================"
echo "  Hermes Agent 已部署完成！"
echo "  WebUI:     http://localhost:8787"
echo "  Dashboard: http://localhost:9119 (含 Chat/Terminal TUI)"
echo "  Gateway:   http://localhost:8642"
echo "  密碼:      $(grep WEBUI_PASSWORD .env | cut -d= -f2)"
echo "============================================================"
