# MCP OAuth Button for All HTTP Servers — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every HTTP/SSE MCP server in the Hermes Dashboard shows an "Authenticate" button by default. Servers that don't need OAuth connect automatically; servers that need OAuth prompt the user via the button.

**Architecture:** Two surgical changes — (1) a one-line `sed` replacement in the compiled React SPA to change the button visibility condition from `auth==="oauth"` to `transport==="http"`, and (2) a backend pre-flight probe in the `POST /api/mcp/servers/{name}/auth` endpoint that auto-detects whether OAuth is actually needed before starting the full flow.

**Tech Stack:** Bash `sed` for SPA patch, Python for backend patch, Playwright MCP for browser testing, `kubectl` for K8s deployment.

---

## File Structure

| File | Location (inside Pod) | Change | Responsibility |
|------|-----------------------|--------|---------------|
| `index-BxxFYFhq.js` | `/opt/hermes/hermes_cli/web_dist/assets/` | sed replace | React SPA — button visibility condition |
| `web_server.py` | `/opt/hermes/hermes_cli/web_server.py` | patch function | Backend — add pre-flight OAuth probe |
| Deploy script | Local `/tmp/mcp-oauth-patch.sh` | create | One-shot deploy script for all patches |

---

### Task 1: Patch React SPA — Show Authenticate Button for All HTTP Servers

**Files:**
- Modify: `/opt/hermes/hermes_cli/web_dist/assets/index-BxxFYFhq.js` (inside agent container)

The compiled React SPA has this condition at one location:
```javascript
e.auth===`oauth`&&(0,W.jsx)(G,{ghost:!0,size:`sm`,title:`Authenticate with OAuth`
```

Change it to show for all HTTP transport servers:
```javascript
e.transport===`http`&&(0,W.jsx)(G,{ghost:!0,size:`sm`,title:`Authenticate with OAuth`
```

- [ ] **Step 1: Apply the sed replacement**

```bash
POD=$(kubectl --context woow-k3s -n hermes get pod -l app=hermes -o jsonpath='{.items[0].metadata.name}')

kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- \
  sed -i 's/e\.auth===`oauth`&&(0,W\.jsx)(G,{ghost:\!0,size:`sm`,title:`Authenticate with OAuth`/e.transport===`http`\&\&(0,W.jsx)(G,{ghost:!0,size:`sm`,title:`Authenticate with OAuth`/' \
  /opt/hermes/hermes_cli/web_dist/assets/index-BxxFYFhq.js
```

- [ ] **Step 2: Verify the replacement**

```bash
kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- \
  grep -c 'e\.transport===.http.&&(0,W\.jsx)(G,{ghost' \
  /opt/hermes/hermes_cli/web_dist/assets/index-BxxFYFhq.js
```

Expected: `1` (one match confirms replacement succeeded)

- [ ] **Step 3: Verify old condition is gone**

```bash
kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- \
  grep -c 'e\.auth===.oauth.&&(0,W\.jsx)(G,{ghost' \
  /opt/hermes/hermes_cli/web_dist/assets/index-BxxFYFhq.js
```

Expected: `0` (old condition no longer exists)

---

### Task 2: Patch Backend — Add Pre-flight OAuth Probe

**Files:**
- Modify: `/opt/hermes/hermes_cli/web_server.py:12792-12830` (inside agent container)

The `POST /api/mcp/servers/{name}/auth` endpoint currently forces `cfg["auth"] = "oauth"` for every call. When a server doesn't need OAuth (e.g., URL-token or proxy), the flow times out waiting for an authorization URL that never comes.

Add a pre-flight probe: HTTP POST to the server URL. If it returns 200 (no auth needed), skip OAuth and return success. Only proceed with OAuth if 401 + `WWW-Authenticate: Bearer` is received.

- [ ] **Step 1: Create the patch script**

```bash
cat > /tmp/mcp-oauth-preflight-patch.py << 'PYEOF'
"""Patch web_server.py to add pre-flight OAuth probe in auth_mcp_server."""
import pathlib

ws = pathlib.Path("/opt/hermes/hermes_cli/web_server.py")
c = ws.read_text()

# Find the line: cfg["auth"] = "oauth"
# Right before it, add a pre-flight probe
old = '''    cfg["auth"] = "oauth"

    flow_id = secrets.token_urlsafe(24)'''

new = '''    # Pre-flight probe: check if server actually needs OAuth
    import httpx as _httpx
    try:
        _probe_r = _httpx.post(cfg["url"], json={"jsonrpc":"2.0","method":"initialize","id":1},
                               headers={"Content-Type":"application/json"}, timeout=10, follow_redirects=True)
        if _probe_r.status_code == 200:
            # Server connected without OAuth — no authentication needed
            return {"flow_id": "", "server_name": name, "status": "approved",
                    "authorization_url": None, "error": None,
                    "message": "Server connected without authentication — no OAuth needed."}
        if _probe_r.status_code == 401:
            _www_auth = _probe_r.headers.get("www-authenticate", "")
            if "bearer" not in _www_auth.lower():
                return {"flow_id": "", "server_name": name, "status": "error",
                        "authorization_url": None,
                        "error": "Server requires authentication but does not support OAuth (no Bearer challenge). Use headers/API key instead."}
    except Exception:
        pass  # Probe failed — proceed with OAuth flow as fallback

    cfg["auth"] = "oauth"

    flow_id = secrets.token_urlsafe(24)'''

if "Pre-flight probe" not in c:
    c = c.replace(old, new)
    ws.write_text(c)
    print("Patched web_server.py: added pre-flight OAuth probe")
else:
    print("Already patched")
PYEOF
```

- [ ] **Step 2: Apply the patch**

```bash
kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- \
  python3 /tmp/mcp-oauth-preflight-patch.py
```

- [ ] **Step 3: Verify the patch**

```bash
kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- \
  grep -c "Pre-flight probe" /opt/hermes/hermes_cli/web_server.py
```

Expected: `1`

---

### Task 3: Restart Processes and Deploy

**Files:**
- No new files — restart existing processes to load patches

- [ ] **Step 1: Clear pycache and restart dashboard + gateway**

```bash
kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- bash -c '
  find /opt/hermes -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  for PID in $(ps aux | grep -E "hermes (dashboard|gateway)" | grep -v grep | awk "{print \$2}"); do
    kill -9 $PID 2>/dev/null && echo "Killed $PID"
  done'
```

- [ ] **Step 2: Wait for processes to restart**

```bash
sleep 45
kubectl --context woow-k3s -n hermes exec $POD -c hermes-agent -- \
  curl -s http://localhost:9119/api/status | python3 -c "import json,sys; print(json.load(sys.stdin).get('overall'))"
```

Expected: `ok`

---

### Task 4: Browser Test — Verify All HTTP Servers Show Button

**Files:**
- No files — Playwright browser testing

- [ ] **Step 1: Navigate to MCP page**

Use Playwright MCP: `browser_navigate` to `https://woowtech-dashboard.woowtech.io/mcp`
Login if needed (admin/admin via password-login form).

- [ ] **Step 2: Take screenshot and verify buttons**

Use Playwright MCP: `browser_take_screenshot`

Expected: ALL three HTTP servers (Higgsfield, browserless mcp, woowtech odoo mcp) show 🔑 Authenticate button.

- [ ] **Step 3: Click Authenticate on Higgsfield**

Use Playwright MCP: `browser_click` on Higgsfield's Authenticate button.

Expected: New tab opens to `clerk.higgsfield.ai/oauth/authorize?...` (Higgsfield login page).

- [ ] **Step 4: Click Authenticate on woowtech odoo mcp**

Use Playwright MCP: `browser_click` on woowtech odoo mcp's Authenticate button.

Expected: Returns immediately with "Server connected without authentication — no OAuth needed." (pre-flight probe success). No popup opens.

- [ ] **Step 5: Click Authenticate on browserless mcp**

Use Playwright MCP: `browser_click` on browserless mcp's Authenticate button.

Expected: New tab opens to Browserless OAuth login page (similar to Higgsfield).

- [ ] **Step 6: Final screenshot**

Use Playwright MCP: `browser_take_screenshot` — capture final state showing all buttons.

---

### Task 5: Create Persistent Deploy Script

**Files:**
- Create: `/var/tmp/vibe-kanban/worktrees/c38b-k3s-kubernetes-h/k3s project/hermes/patches/mcp-oauth-all-http.sh`

Since Pod restarts wipe runtime patches, create a deploy script that can be re-run after any restart.

- [ ] **Step 1: Write the deploy script**

```bash
#!/bin/bash
# Deploy MCP OAuth Button patches to Hermes Agent
# Run after pod restart to re-apply patches
set -euo pipefail

CONTEXT="${1:-woow-k3s}"
NS="${2:-hermes}"
POD=$(kubectl --context "$CONTEXT" -n "$NS" get pod -l app=hermes -o jsonpath='{.items[0].metadata.name}')
echo "Pod: $POD"

# 1. Patch React SPA: show Authenticate for ALL HTTP servers
echo "Patching React SPA..."
kubectl --context "$CONTEXT" -n "$NS" exec "$POD" -c hermes-agent -- \
  sed -i 's/e\.auth===`oauth`&&(0,W\.jsx)(G,{ghost:\!0,size:`sm`,title:`Authenticate with OAuth`/e.transport===`http`\&\&(0,W.jsx)(G,{ghost:!0,size:`sm`,title:`Authenticate with OAuth`/' \
  /opt/hermes/hermes_cli/web_dist/assets/index-BxxFYFhq.js

# 2. Patch backend: add pre-flight OAuth probe
echo "Patching backend..."
kubectl --context "$CONTEXT" -n "$NS" exec "$POD" -c hermes-agent -- python3 -c "
import pathlib
ws = pathlib.Path('/opt/hermes/hermes_cli/web_server.py')
c = ws.read_text()
old = '    cfg[\"auth\"] = \"oauth\"\\n\\n    flow_id = secrets.token_urlsafe(24)'
new = '''    # Pre-flight probe: check if server actually needs OAuth
    import httpx as _httpx
    try:
        _probe_r = _httpx.post(cfg['url'], json={'jsonrpc':'2.0','method':'initialize','id':1},
                               headers={'Content-Type':'application/json'}, timeout=10, follow_redirects=True)
        if _probe_r.status_code == 200:
            return {'flow_id':'','server_name':name,'status':'approved',
                    'authorization_url':None,'error':None,
                    'message':'Server connected without authentication.'}
        if _probe_r.status_code == 401:
            _www_auth = _probe_r.headers.get('www-authenticate','')
            if 'bearer' not in _www_auth.lower():
                return {'flow_id':'','server_name':name,'status':'error',
                        'authorization_url':None,
                        'error':'Server requires auth but does not support OAuth. Use headers/API key.'}
    except Exception:
        pass
    cfg['auth'] = 'oauth'
    flow_id = secrets.token_urlsafe(24)'''
if 'Pre-flight probe' not in c:
    c = c.replace(old, new)
    ws.write_text(c)
    print('  backend patched')
else:
    print('  backend already patched')
"

# 3. Restart processes
echo "Restarting processes..."
kubectl --context "$CONTEXT" -n "$NS" exec "$POD" -c hermes-agent -- bash -c '
  find /opt/hermes -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  for PID in $(ps aux | grep -E "hermes (dashboard|gateway)" | grep -v grep | awk "{print \$2}"); do
    kill -9 $PID 2>/dev/null
  done'

echo "Waiting 45s for restart..."
sleep 45
echo "Done. Reload the Dashboard MCP page to see changes."
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x hermes/patches/mcp-oauth-all-http.sh
git add hermes/patches/mcp-oauth-all-http.sh
git commit -m "feat: add MCP OAuth button patch script for all HTTP servers"
```
