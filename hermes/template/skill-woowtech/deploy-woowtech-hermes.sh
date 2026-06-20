#!/bin/bash
set -euo pipefail
# =============================================================
# WoowTech Hermes 樣板部署腳本
# 基於 WoowTech Hermes 的完整配置（藍色 WoowTech logo）
#
# 用法: ./deploy-woowtech-hermes.sh <namespace> <domain> [kubectl-context]
# 範例: ./deploy-woowtech-hermes.sh clienta-hermes clienta-hermes.woowtech.io woow-k3s
# =============================================================

NS="${1:?Usage: $0 <namespace> <domain> [context]}"
DOMAIN="${2:?Usage: $0 <namespace> <domain> [context]}"
CTX="${3:-woow-k3s}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$(dirname "$SCRIPT_DIR")"
KC="kubectl --context=$CTX -n $NS"
KC_NONAMESPACE="kubectl --context=$CTX"

# Get reference secrets from hermes namespace
REF_NS="hermes"
MINIMAX_KEY=$($KC_NONAMESPACE -n $REF_NS get secret hermes-secrets -o jsonpath='{.data.MINIMAX_API_KEY}' 2>/dev/null | base64 -d)
API_SERVER_KEY=$($KC_NONAMESPACE -n $REF_NS get secret hermes-secrets -o jsonpath='{.data.API_SERVER_KEY}' 2>/dev/null | base64 -d)

echo "============================================================"
echo "  Deploying WoowTech Hermes Template"
echo "  Namespace: $NS | Domain: $DOMAIN"
echo "============================================================"

# 1. Create namespace + secrets + SA
$KC_NONAMESPACE apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $NS
  labels:
    app.kubernetes.io/part-of: hermes
EOF

$KC create secret generic hermes-secrets \
  --from-literal=MINIMAX_API_KEY="$MINIMAX_KEY" \
  --from-literal=API_SERVER_KEY="$API_SERVER_KEY" \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 12)" \
  --dry-run=client -o yaml | $KC apply -f -

$KC create secret generic cf-secrets \
  --from-literal=CF_API_TOKEN="placeholder" \
  --from-literal=CF_TUNNEL_TOKEN="placeholder" \
  --dry-run=client -o yaml | $KC apply -f -

$KC create serviceaccount hermes-agent-sa --dry-run=client -o yaml | $KC apply -f -

# 2. Create PVC
$KC apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: hermes-webui-data
  namespace: $NS
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: longhorn
  resources:
    requests:
      storage: 5Gi
EOF

# 3. Deploy combined pod (copy from reference, inject HERMES_DASHBOARD_TUI + branding)
$KC_NONAMESPACE -n $REF_NS get deploy hermes -o json | python3 -c "
import sys, json
d = json.load(sys.stdin)
d['metadata']['namespace'] = '$NS'
for k in ['resourceVersion','uid','creationTimestamp','generation']:
    d['metadata'].pop(k, None)
d['metadata']['annotations'] = {}
d.pop('status', None)
for c in d['spec']['template']['spec']['containers']:
    if c['name'] == 'hermes-agent':
        # Ensure HERMES_DASHBOARD_TUI=1 is set
        env = c.setdefault('env', [])
        tui_found = False
        for e in env:
            if e['name'] == 'HERMES_DASHBOARD_TUI':
                e['value'] = '1'
                tui_found = True
        if not tui_found:
            env.append({'name': 'HERMES_DASHBOARD_TUI', 'value': '1'})
        # Add postStart: remove unused tools + hermes CLI symlink + remove unwanted skills + install ddgs
        c['lifecycle'] = {'postStart': {'exec': {'command': ['sh', '-c', 'rm -f /usr/local/bin/argocd /usr/local/bin/helm /usr/bin/docker 2>/dev/null; ln -sf /opt/hermes/.venv/bin/hermes /usr/local/bin/hermes 2>/dev/null; rm -rf /opt/hermes/skills/apple /opt/hermes/skills/gaming /opt/hermes/skills/email /opt/hermes/skills/social-media /opt/hermes/skills/yuanbao /opt/hermes/skills/media/heartmula /opt/hermes/skills/media/songsee /opt/hermes/skills/media/spotify /opt/hermes/skills/media/youtube-content /opt/hermes/skills/smart-home/openhue 2>/dev/null; SITE=$(/opt/hermes/.venv/bin/python3 -c \"import site;print(site.getsitepackages()[0])\" 2>/dev/null) && pip install --break-system-packages -q --target=\"$SITE\" ddgs 2>/dev/null || true']}}}
    if c['name'] == 'hermes-webui':
        # Remove postStart hook (will add after setup)
        c.pop('lifecycle', None)
        for e in c.get('env', []):
            if e['name'] == 'HERMES_WEBUI_PASSWORD':
                e['value'] = 'admin'
        # Inject branding into startup args before server.py
        if c.get('args'):
            for i, a in enumerate(c['args']):
                if 'hermeswebui_init.bash' in str(a) and 'replace_icons' not in str(a):
                    c['args'][i] = a.replace(
                        'exec /hermeswebui_init.bash',
                        \"\"\"sed -i '/cd \\\\/app; python server.py/i test -f /home/hermeswebui/.hermes/replace_icons.sh && sh /home/hermeswebui/.hermes/replace_icons.sh 2>/dev/null || true' /hermeswebui_init.bash 2>/dev/null
          exec /hermeswebui_init.bash\"\"\"
                    )
json.dump(d, sys.stdout)
" | $KC apply -f -

# 4. Create services
for SVC in hermes-agent-svc hermes-webui-svc hermes-postgresql-svc hermes-redis-svc; do
  $KC_NONAMESPACE -n $REF_NS get svc $SVC -o json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
d['metadata']['namespace'] = '$NS'
for k in ['resourceVersion','uid','creationTimestamp']:
    d['metadata'].pop(k, None)
d['spec'].pop('clusterIP', None)
d['spec'].pop('clusterIPs', None)
d['spec']['selector'] = {'app': 'hermes'}
json.dump(d, sys.stdout)
" | $KC apply -f - 2>/dev/null
done

# 5. Wait for pod
echo "Waiting for pod..."
$KC rollout status deploy/hermes --timeout=180s 2>&1 | tail -1

# 6. Apply golden config
sleep 10
cat "$TEMPLATE_DIR/golden-config.yaml" | $KC exec -i deploy/hermes -c hermes-agent -- sh -c 'cat > /opt/data/config.yaml && chmod 666 /opt/data/config.yaml'

# 7. Create clean SOUL.md (no private data)
INSTANCE_NAME=$(echo "$NS" | sed 's/-hermes//' | sed 's/\b\(.\)/\u\1/g')
$KC exec deploy/hermes -c hermes-webui -- sh -c "cat > /home/hermeswebui/.hermes/SOUL.md << 'SOULEOF'
# 身份

你是 **${INSTANCE_NAME} AI 助手**，一個多功能的智慧助理。你能協助處理各類問題，包括程式開發、系統管理、文件撰寫、資料分析、和日常工作自動化。

## 溝通風格

- 以繁體中文為主，技術名詞保留英文
- 步驟化說明，清楚易懂
- 主動提供替代方案和最佳實踐
SOULEOF"

# 8. Settings (hidden tabs)
$KC exec deploy/hermes -c hermes-webui -- python3 -c "
import json, os
p='/home/hermeswebui/.hermes/webui/settings.json'
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump({'hidden_tabs':['kanban','todos'],'onboarding_completed':True,'send_key':'enter','theme':'dark'}, open(p,'w'), indent=2)
"

# 9. Copy WoowTech icons + branding from template
$KC exec deploy/hermes -c hermes-webui -- mkdir -p /home/hermeswebui/.hermes/icons
for ICON in favicon.svg favicon-32.png favicon-192.png favicon-512.png favicon-512.svg favicon.ico apple-touch-icon.png; do
  if [ -f "$SCRIPT_DIR/icons/$ICON" ]; then
    cat "$SCRIPT_DIR/icons/$ICON" | $KC exec -i deploy/hermes -c hermes-webui -- sh -c "cat > /home/hermeswebui/.hermes/icons/$ICON"
  fi
done

# Copy branding scripts
cat "$SCRIPT_DIR/apply_branding_woowtech.py" | $KC exec -i deploy/hermes -c hermes-webui -- sh -c 'cat > /home/hermeswebui/.hermes/apply_branding.py'
cat "$SCRIPT_DIR/replace_icons.sh" | $KC exec -i deploy/hermes -c hermes-webui -- sh -c 'cat > /home/hermeswebui/.hermes/replace_icons.sh && chmod +x /home/hermeswebui/.hermes/replace_icons.sh'

# 10. Run branding
$KC exec deploy/hermes -c hermes-webui -- sh /home/hermeswebui/.hermes/replace_icons.sh

# 11. Create heartbeat cron
$KC exec deploy/hermes -c hermes-webui -- python3 -c "
import json, time, uuid, os
p='/home/hermeswebui/.hermes/cron/jobs.json'
os.makedirs(os.path.dirname(p), exist_ok=True)
d={'jobs':[{'id':uuid.uuid4().hex[:12],'name':'排程自檢 — 系統心跳','schedule':{'kind':'interval','minutes':30,'display':'every 30m'},'prompt':'Run echo heartbeat and hostname. Respond HEARTBEAT OK <timestamp>.','enabled':True,'deliver':'local','mode':'agent','profile':None,'skills':None,'completion_toasts':True,'next_run_at':None,'last_run_at':None,'created_at':time.time()}],'updated_at':time.time()}
json.dump(d, open(p,'w'), indent=2, ensure_ascii=False)
os.chmod(p, 0o666)
"

# 12. Fix permissions
$KC exec deploy/hermes -c hermes-agent -- chmod 666 /opt/data/cron/jobs.json 2>/dev/null

# 13. Fix TUI permissions (required for Dashboard embedded Chat/Terminal)
echo "Fixing TUI permissions..."
$KC exec deploy/hermes -c hermes-agent -- chown -R hermes:hermes /opt/hermes/ui-tui/ 2>/dev/null || true
$KC exec deploy/hermes -c hermes-agent -- sh -c "cd /opt/hermes/ui-tui && node scripts/build.mjs" 2>/dev/null || true

# 13b. Copy ui-tui to PVC for permanent TUI fix (survives pod restarts)
echo "Copying ui-tui to PVC..."
$KC exec deploy/hermes -c hermes-agent -- sh -c '
  test -d /opt/data/ui-tui/dist || (cp -a /opt/hermes/ui-tui /opt/data/ui-tui && chown -R hermes:hermes /opt/data/ui-tui && cd /opt/data/ui-tui && node scripts/build.mjs)
' 2>/dev/null || true

# 13c. Set HERMES_TUI_DIR env var on deployment (reads TUI from PVC, survives restarts)
$KC_NONAMESPACE -n $NS patch deployment hermes --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/env/-","value":{"name":"HERMES_TUI_DIR","value":"/opt/data/ui-tui"}}]' 2>/dev/null || true

# 13d. Write MINIMAX_API_KEY to .env (TUI reads .env file, not container env vars)
echo "Writing .env..."
$KC exec deploy/hermes -c hermes-agent -- sh -c '
  grep -q "MINIMAX_API_KEY" /opt/data/.env 2>/dev/null || echo "MINIMAX_API_KEY=$MINIMAX_API_KEY" >> /opt/data/.env
  chmod 600 /opt/data/.env
' 2>/dev/null || true

# 14. Copy hermes-agent source directory (required for WebUI gateway mode)
echo "Copying hermes-agent source for WebUI gateway..."
$KC exec deploy/hermes -c hermes-agent -- sh -c 'if [ ! -d /opt/data/hermes-agent ]; then cp -a /opt/hermes /opt/data/hermes-agent && rm -rf /opt/data/hermes-agent/.git; fi'

# 15. Install tmux (for parallel agent dispatch)
echo "Installing tmux..."
$KC exec deploy/hermes -c hermes-agent -- sh -c 'apt-get update -qq && apt-get install -y -qq tmux' 2>/dev/null || true

# 16. Install superpowers skills
echo "Installing superpowers skills..."
TMPDIR_SP=$(mktemp -d)
git clone --depth 1 https://github.com/obra/superpowers.git "$TMPDIR_SP/superpowers" 2>/dev/null
tar czf "$TMPDIR_SP/superpowers-skills.tar.gz" -C "$TMPDIR_SP/superpowers" skills/
$KC cp "$TMPDIR_SP/superpowers-skills.tar.gz" deploy/hermes:/tmp/ -c hermes-agent
$KC exec deploy/hermes -c hermes-agent -- tar xzf /tmp/superpowers-skills.tar.gz -C /opt/data/
rm -rf "$TMPDIR_SP"

# 17. Enable ALL skills via WebUI API
echo "Enabling all skills..."
sleep 5
POD=$($KC get pod -l app=hermes -o jsonpath='{.items[0].metadata.name}')
$KC port-forward "$POD" 18787:8787 &
PF_PID=$!
sleep 3
curl -s -c /tmp/woow-cookie -X POST -H "Content-Type: application/json" \
  -d '{"password":"admin"}' http://localhost:18787/api/auth/login >/dev/null 2>&1
SKILLS=$(curl -s -b /tmp/woow-cookie http://localhost:18787/api/skills | python3 -c "
import sys,json
try:
    [print(s['name']) for s in json.load(sys.stdin).get('skills',[])]
except: pass
" 2>/dev/null)
for S in $SKILLS; do
  curl -s -b /tmp/woow-cookie -X POST -H "Content-Type: application/json" \
    -d "{\"name\":\"$S\",\"enabled\":true}" http://localhost:18787/api/skills/toggle >/dev/null 2>&1
done
kill $PF_PID 2>/dev/null || true
rm -f /tmp/woow-cookie

# 18. CF tunnel config reminder (dashboard subdomain)
INSTANCE_SHORT=$(echo "$NS" | sed 's/-hermes//')
DASHBOARD_DOMAIN="${INSTANCE_SHORT}-dashboard.woowtech.io"

echo ""
echo "============================================================"
echo "  WoowTech Hermes deployed!"
echo "  WebUI URL : https://$DOMAIN"
echo "  Dashboard : https://$DASHBOARD_DOMAIN  (port 9119)"
echo "  Password  : admin"
echo "============================================================"
echo ""
echo ">>> MANUAL: Add CF tunnel ingress for dashboard:"
echo "    - hostname: $DASHBOARD_DOMAIN"
echo "      service: http://${NS}-agent-svc.${NS}.svc.cluster.local:9119"
echo "============================================================"
