#!/bin/bash
# Hermes Agent v0.17.0 — Podman 完整部署
# 與 K3s 標準配置對齊：所有工具、技能、MCP、ddgs web search
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

echo "═══════════════════════════════════════"
echo "  Hermes Agent v0.17.0 — Podman Deploy"
echo "═══════════════════════════════════════"

# Step 1: Generate .env if missing
if [ ! -f "$ENV_FILE" ]; then
    cp "${SCRIPT_DIR}/.env.example" "$ENV_FILE"
    sed -i "s/^API_SERVER_KEY=.*/API_SERVER_KEY=$(openssl rand -hex 32)/" "$ENV_FILE"
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)/" "$ENV_FILE"
    sed -i "s/^HERMES_UID=.*/HERMES_UID=$(id -u)/" "$ENV_FILE"
    sed -i "s/^HERMES_GID=.*/HERMES_GID=$(id -g)/" "$ENV_FILE"
    echo "已生成 .env — 編輯 MINIMAX_API_KEY 後重新執行"
    exit 0
fi

# Step 2: Start containers
cd "$SCRIPT_DIR"
echo "Step 2: Starting containers..."
podman-compose up -d
sleep 20

# Step 3: Hermes CLI symlink + cleanup
echo "Step 3: Hermes CLI + cleanup..."
podman exec hermes-agent sh -c '
  ln -sf /opt/hermes/.venv/bin/hermes /usr/local/bin/hermes 2>/dev/null
  rm -f /usr/local/bin/argocd /usr/local/bin/helm /usr/bin/docker 2>/dev/null
  rm -rf /opt/hermes/skills/apple /opt/hermes/skills/gaming /opt/hermes/skills/email /opt/hermes/skills/social-media /opt/hermes/skills/yuanbao /opt/hermes/skills/media/heartmula /opt/hermes/skills/media/songsee /opt/hermes/skills/media/spotify /opt/hermes/skills/media/youtube-content /opt/hermes/skills/smart-home/openhue 2>/dev/null
'

# Step 4: Install ddgs web search
echo "Step 4: Install ddgs web search..."
podman exec hermes-agent sh -c '
  SITE=$(/opt/hermes/.venv/bin/python3 -c "import site;print(site.getsitepackages()[0])" 2>/dev/null)
  uv pip install --target="$SITE" ddgs 2>/dev/null
  /opt/hermes/.venv/bin/python3 -c "from ddgs import DDGS; print(\"ddgs OK\")" 2>&1 | grep OK
'

# Step 5: Agent source copy (for WebUI gateway mode)
echo "Step 5: Agent source copy..."
podman exec hermes-agent sh -c 'test -d /opt/data/hermes-agent || (cp -a /opt/hermes /opt/data/hermes-agent && rm -rf /opt/data/hermes-agent/.git)'

# Step 6: TUI PVC fix
echo "Step 6: TUI PVC setup..."
podman exec hermes-agent sh -c '
  test -d /opt/data/ui-tui || cp -r /opt/hermes/ui-tui /opt/data/ui-tui 2>/dev/null
  chown -R hermes:hermes /opt/data/ui-tui/ 2>/dev/null || true
'

# Step 7: tmux
echo "Step 7: tmux install..."
podman exec hermes-agent sh -c 'which tmux || (apt-get update -qq && apt-get install -y -qq tmux)' 2>/dev/null

# Step 8: Superpowers skills
echo "Step 8: Superpowers skills..."
if ! podman exec hermes-agent test -f /opt/data/skills/brainstorming/SKILL.md 2>/dev/null; then
    T=$(mktemp -d)
    git clone --depth 1 https://github.com/obra/superpowers.git "$T/sp" 2>/dev/null
    tar czf "$T/sp.tar.gz" -C "$T/sp" skills/
    podman cp "$T/sp.tar.gz" hermes-agent:/tmp/
    podman exec hermes-agent tar xzf /tmp/sp.tar.gz -C /opt/data/
    rm -rf "$T"
    echo "  Superpowers installed"
fi

# Step 9: Config optimize
echo "Step 9: Config optimize..."
podman exec hermes-agent sh -c '
  # Fix approvals
  sed -i "s/mode: manual/mode: off/" /opt/data/config.yaml 2>/dev/null
  sed -i "s/cron_mode: deny/cron_mode: yolo/" /opt/data/config.yaml 2>/dev/null
  sed -i "s/hooks_auto_accept: false/hooks_auto_accept: true/" /opt/data/config.yaml 2>/dev/null
  sed -i "s/subagent_auto_approve: false/subagent_auto_approve: true/" /opt/data/config.yaml 2>/dev/null
  # Fix terminal
  sed -i "/^terminal:/,/^[a-z]/{s/  backend: auto/  backend: local/}" /opt/data/config.yaml 2>/dev/null
  # Fix web search backend
  sed -i "/^web:/,/^[a-z]/{s/  backend: .*/  backend: ddgs/}" /opt/data/config.yaml 2>/dev/null
  sed -i "/^web:/,/^[a-z]/{s/  search_backend: .*/  search_backend: ddgs/}" /opt/data/config.yaml 2>/dev/null
  # Remove toolsets restriction
  sed -i "/^toolsets:/d" /opt/data/config.yaml 2>/dev/null
  sed -i "/^- hermes-cli$/d" /opt/data/config.yaml 2>/dev/null
  sed -i "/^  - hermes-cli$/d" /opt/data/config.yaml 2>/dev/null
  # Write .env for TUI
  echo "MINIMAX_API_KEY=$(printenv MINIMAX_API_KEY)" > /opt/data/.env
  # Enable extra toolsets
  hermes tools enable video 2>/dev/null | tail -1
  hermes tools enable moa 2>/dev/null | tail -1
  hermes tools enable context_engine 2>/dev/null | tail -1
  hermes tools enable homeassistant 2>/dev/null | tail -1
  # Enable plugins
  hermes plugins enable disk-cleanup 2>/dev/null | tail -1
  hermes plugins enable security-guidance 2>/dev/null | tail -1
  echo "  Config optimized"
'

# Step 10: Wait for WebUI healthy
echo "Step 10: Waiting for WebUI..."
for i in $(seq 1 60); do
  S=$(podman inspect hermes-webui --format '{{.State.Health.Status}}' 2>/dev/null)
  [ "$S" = "healthy" ] && break
  sleep 10
done

# Step 11: Branding
echo "Step 11: Branding..."
if [ -d "${SCRIPT_DIR}/icons" ]; then
    podman exec hermes-agent mkdir -p /opt/data/icons
    for I in "${SCRIPT_DIR}"/icons/*; do [ -f "$I" ] && podman cp "$I" hermes-agent:/opt/data/icons/; done
    [ -f "${SCRIPT_DIR}/apply_branding.py" ] && podman cp "${SCRIPT_DIR}/apply_branding.py" hermes-agent:/opt/data/apply_branding.py
    podman exec hermes-agent sh -c 'printf "#!/bin/sh\ncp /home/hermeswebui/.hermes/icons/* /app/static/ 2>/dev/null\npython3 /home/hermeswebui/.hermes/apply_branding.py 2>/dev/null\n" > /opt/data/replace_icons.sh && chmod +x /opt/data/replace_icons.sh'
    podman exec hermes-webui sh -c 'grep -q replace_icons /hermeswebui_init.bash || sed -i "/cd \/app; python server.py/i test -f /home/hermeswebui/.hermes/replace_icons.sh && sh /home/hermeswebui/.hermes/replace_icons.sh 2>/dev/null || true" /hermeswebui_init.bash'
    podman restart hermes-webui
    sleep 30
fi

# Step 12: Enable all skills
echo "Step 12: Enable skills..."
PW=$(grep WEBUI_PASSWORD .env 2>/dev/null | cut -d= -f2 || echo admin)
podman exec hermes-webui python3 -c "
import http.cookiejar,urllib.request,json;cj=http.cookiejar.CookieJar()
o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
o.open(urllib.request.Request('http://localhost:8787/api/auth/login',json.dumps({'password':'$PW'}).encode(),headers={'Content-Type':'application/json'}),timeout=10)
sk=json.loads(o.open(urllib.request.Request('http://localhost:8787/api/skills'),timeout=10).read()).get('skills',[])
c=sum(1 for s in sk if s.get('disabled',True) and not(o.open(urllib.request.Request('http://localhost:8787/api/skills/toggle',json.dumps({'name':s['name'],'enabled':True}).encode(),headers={'Content-Type':'application/json'},method='POST'),timeout=5) and False))
print(f'Enabled {c}/{len(sk)} skills')
" 2>/dev/null

# Step 13: Clear caches
echo "Step 13: Clear caches..."
podman exec hermes-agent sh -c 'rm -f /opt/data/.skills_prompt_snapshot.json /opt/data/skills/.bundled_manifest /opt/data/provider_models_cache.json /opt/data/models_dev_cache.json'

echo ""
echo "═══════════════════════════════════════"
echo "  部署完成！Hermes Agent v0.17.0"
echo "═══════════════════════════════════════"
echo "  WebUI:     http://localhost:18787"
echo "  Dashboard: http://localhost:19119"
echo "  API:       http://localhost:18642"
echo "  密碼:      admin (WebUI + Dashboard)"
echo "═══════════════════════════════════════"
