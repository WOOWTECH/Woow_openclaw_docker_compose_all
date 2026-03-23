# Agent Persistence & Provider Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist OpenClaw agent configs across pod restarts via PVC, add MiniMax/DeepSeek/Qwen to setup wizard, and switch wizard to light mode.

**Architecture:** PVC mounted at `/home/node/.openclaw/agents` preserves user-created agents. Startup script merges env-var API keys into existing `auth-profiles.json` instead of overwriting. Setup wizard expanded with 3 new providers and CSS converted to light theme.

**Tech Stack:** K8s YAML manifests, Python/Flask (setup wizard), HTML/CSS/JS (wizard frontend)

**Spec:** `docs/superpowers/specs/2026-03-23-agent-persistence-and-provider-expansion-design.md`

**Note:** All find/replace blocks use textual anchors (the exact text to find), not line numbers. Line numbers in comments are for initial reference only and will shift as earlier tasks modify the file.

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml` | Add PVC, volumeMount, env vars, merge startup script |
| Modify | `openclaw-k3s-paas/setup-wizard/app.py` | Add MiniMax/DeepSeek/Qwen to provider dicts + fix configure_gateway merge |
| Modify | `openclaw-k3s-paas/setup-wizard/templates/index.html` | Add providers to UI + light mode CSS |

---

### Task 1: Add PVC for agents directory

**Files:**
- Modify: `openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml`

- [ ] **Step 1: Add PVC resource block**

Find the line `# OpenClaw Gateway - Deployment` and insert the following PVC block **before** it (after the PostgreSQL Service's `---` separator):

```yaml
---
# =============================================================
# OpenClaw Gateway - Agents PersistentVolumeClaim
# =============================================================
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: openclaw-agents-pvc
  namespace: openclaw-tenant-1
  labels:
    app: openclaw-gateway
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
```

- [ ] **Step 2: Add volumeMount and volume to Gateway Deployment**

Find the `livenessProbe` block in the Gateway Deployment container that ends with:

```yaml
          livenessProbe:
            tcpSocket:
              port: 18789
            initialDelaySeconds: 300
            periodSeconds: 30
            failureThreshold: 10
```

Insert `volumeMounts` immediately after the `livenessProbe` block (same indentation level as `livenessProbe`, `resources`, `ports`):

```yaml
          volumeMounts:
            - name: agents-data
              mountPath: /home/node/.openclaw/agents
```

Then find the end of the `containers` array (after all container properties) and add `volumes` at the `spec.template.spec` level (same indentation as `containers`):

```yaml
      volumes:
        - name: agents-data
          persistentVolumeClaim:
            claimName: openclaw-agents-pvc
```

The resulting structure should look like:

```yaml
    spec:
      containers:
        - name: openclaw-gateway
          ...
          livenessProbe:
            ...
            failureThreshold: 10
          volumeMounts:
            - name: agents-data
              mountPath: /home/node/.openclaw/agents
      volumes:
        - name: agents-data
          persistentVolumeClaim:
            claimName: openclaw-agents-pvc
```

- [ ] **Step 3: Validate YAML syntax**

Run: `cd "openclaw-k3s-paas" && python3 -c "import yaml; list(yaml.safe_load_all(open('k8s-manifests/06-openclaw-core.yaml')))" && echo "YAML valid"`

Expected: `YAML valid`

- [ ] **Step 4: Commit**

```bash
git add openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml
git commit -m "feat: add PVC for openclaw agents directory persistence"
```

---

### Task 2: Add new provider env vars to Gateway Deployment

**Files:**
- Modify: `openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml` (env section of Gateway Deployment)

- [ ] **Step 1: Add MINIMAX_API_KEY, DEEPSEEK_API_KEY, QWEN_API_KEY env vars**

Find the last env var block (LINE_CHANNEL_SECRET):

```yaml
            - name: LINE_CHANNEL_SECRET
              valueFrom:
                secretKeyRef:
                  name: openclaw-secrets
                  key: LINE_CHANNEL_SECRET
                  optional: true
```

Insert immediately after it:

```yaml
            - name: MINIMAX_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openclaw-secrets
                  key: MINIMAX_API_KEY
                  optional: true
            - name: DEEPSEEK_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openclaw-secrets
                  key: DEEPSEEK_API_KEY
                  optional: true
            - name: QWEN_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openclaw-secrets
                  key: QWEN_API_KEY
                  optional: true
```

- [ ] **Step 2: Validate YAML syntax**

Run: `cd "openclaw-k3s-paas" && python3 -c "import yaml; list(yaml.safe_load_all(open('k8s-manifests/06-openclaw-core.yaml')))" && echo "YAML valid"`

Expected: `YAML valid`

- [ ] **Step 3: Commit**

```bash
git add openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml
git commit -m "feat: add MiniMax/DeepSeek/Qwen env vars to gateway deployment"
```

---

### Task 3: Rewrite startup script auth-profiles.json to merge mode

**Files:**
- Modify: `openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml` (startup script inside Gateway Deployment command block)

- [ ] **Step 1: Replace the auth-profiles.json section in the startup script**

Find this exact block (including the comment above it):

```
              # Write auth-profiles.json from env vars (survives pod restart)
              mkdir -p /home/node/.openclaw/agents/main/agent
              AUTH='{}'
              [ -n "${OPENAI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.openai={apiKey:process.env.OPENAI_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${ANTHROPIC_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.anthropic={apiKey:process.env.ANTHROPIC_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${GEMINI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.google={apiKey:process.env.GEMINI_API_KEY};console.log(JSON.stringify(o))})")
              echo "$AUTH" > /home/node/.openclaw/agents/main/agent/auth-profiles.json
```

Replace with:

```
              # Write auth-profiles.json: merge mode (preserve user-added keys, update env-var keys)
              mkdir -p /home/node/.openclaw/agents/main/agent
              AUTH_FILE="/home/node/.openclaw/agents/main/agent/auth-profiles.json"
              AUTH=$(cat "$AUTH_FILE" 2>/dev/null || echo '{}')
              echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{JSON.parse(d)}catch(e){process.exit(1)}})" || AUTH='{}'
              [ -n "${OPENAI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.openai={apiKey:process.env.OPENAI_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${ANTHROPIC_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.anthropic={apiKey:process.env.ANTHROPIC_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${GEMINI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.google={apiKey:process.env.GEMINI_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${MINIMAX_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.minimax={apiKey:process.env.MINIMAX_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${DEEPSEEK_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.deepseek={apiKey:process.env.DEEPSEEK_API_KEY};console.log(JSON.stringify(o))})")
              [ -n "${QWEN_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.qwen={apiKey:process.env.QWEN_API_KEY};console.log(JSON.stringify(o))})")
              echo "$AUTH" > "$AUTH_FILE"
```

- [ ] **Step 2: Validate YAML syntax**

Run: `cd "openclaw-k3s-paas" && python3 -c "import yaml; list(yaml.safe_load_all(open('k8s-manifests/06-openclaw-core.yaml')))" && echo "YAML valid"`

Expected: `YAML valid`

- [ ] **Step 3: Commit**

```bash
git add openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml
git commit -m "feat: switch auth-profiles.json to merge mode with new providers"
```

---

### Task 4: Add MiniMax/DeepSeek/Qwen to setup wizard backend + fix configure_gateway

**Files:**
- Modify: `openclaw-k3s-paas/setup-wizard/app.py` (AI provider dicts + configure_gateway function)

- [ ] **Step 1: Add providers to AI_ENV_MAP**

Find:
```python
AI_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "ollama": "OLLAMA_HOST",
}
```

Replace with:
```python
AI_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "ollama": "OLLAMA_HOST",
    "minimax": "MINIMAX_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "QWEN_API_KEY",
}
```

- [ ] **Step 2: Add providers to AI_MODEL_MAP**

Find:
```python
AI_MODEL_MAP = {
    "openai": "openai/gpt-4o",
    "anthropic": "anthropic/claude-sonnet-4-20250514",
    "google": "google/gemini-2.0-flash",
    "ollama": "ollama/llama3",
}
```

Replace with:
```python
AI_MODEL_MAP = {
    "openai": "openai/gpt-4o",
    "anthropic": "anthropic/claude-sonnet-4-20250514",
    "google": "google/gemini-2.0-flash",
    "ollama": "ollama/llama3",
    "minimax": "minimax/MiniMax-M2.5",
    "deepseek": "deepseek/deepseek-chat",
    "qwen": "qwen/qwen-max",
}
```

- [ ] **Step 3: Add providers to AI_AUTH_KEY**

Find:
```python
AI_AUTH_KEY = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
}
```

Replace with:
```python
AI_AUTH_KEY = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "minimax": "minimax",
    "deepseek": "deepseek",
    "qwen": "qwen",
}
```

- [ ] **Step 4: Fix configure_gateway to use merge mode instead of overwriting auth-profiles.json**

The current `configure_gateway` function overwrites auth-profiles.json with only the single chosen provider, losing any other keys. Since the agents directory is now on a PVC, this would wipe user-configured keys. The setup wizard only runs once during initial provisioning, and the startup script will re-merge env vars on next pod restart, so a simple read-merge-write is sufficient.

Find:
```python
    # Write auth-profiles.json with API key (critical for AI to work)
    if ai_provider and ai_api_key:
        auth_key = AI_AUTH_KEY.get(ai_provider)
        if auth_key:
            auth_json = json.dumps({auth_key: {"apiKey": ai_api_key}})
            exec_cmd(
                f'mkdir -p /home/node/.openclaw/agents/main/agent && '
                f'echo \'{auth_json}\' > /home/node/.openclaw/agents/main/agent/auth-profiles.json'
            )
            log.info(f"Wrote auth-profiles.json for {auth_key}")
```

Replace with:
```python
    # Merge API key into auth-profiles.json (preserve existing keys from PVC)
    if ai_provider and ai_api_key:
        auth_key = AI_AUTH_KEY.get(ai_provider)
        if auth_key:
            new_entry = json.dumps({auth_key: {"apiKey": ai_api_key}})
            exec_cmd(
                f'mkdir -p /home/node/.openclaw/agents/main/agent && '
                f'node -e "const fs=require(\'fs\'),f=\'/home/node/.openclaw/agents/main/agent/auth-profiles.json\';"'
                f'"let o={{}};try{{o=JSON.parse(fs.readFileSync(f,\'utf8\'))}}catch(e){{}}"'
                f'"Object.assign(o,{new_entry});"'
                f'"fs.writeFileSync(f,JSON.stringify(o))"'
            )
            log.info(f"Merged auth-profiles.json for {auth_key}")
```

- [ ] **Step 5: Verify Python syntax**

Run: `python3 -c "import py_compile; py_compile.compile('openclaw-k3s-paas/setup-wizard/app.py', doraise=True)" && echo "Python syntax OK"`

Expected: `Python syntax OK`

- [ ] **Step 6: Commit**

```bash
git add openclaw-k3s-paas/setup-wizard/app.py
git commit -m "feat: add MiniMax/DeepSeek/Qwen providers + fix auth-profiles merge in setup wizard"
```

---

### Task 5: Add new providers to setup wizard frontend

**Files:**
- Modify: `openclaw-k3s-paas/setup-wizard/templates/index.html` (provider select, aiConfig, aiModels)

- [ ] **Step 1: Add provider options to HTML select**

Find:
```html
                <select id="ai_provider" name="ai_provider">
                    <option value="">-- Select AI Provider --</option>
                    <option value="openai">OpenAI (GPT-4o, o1, ...)</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="google">Google (Gemini)</option>
                    <option value="ollama">Ollama (Local)</option>
                </select>
```

Replace with:
```html
                <select id="ai_provider" name="ai_provider">
                    <option value="">-- Select AI Provider --</option>
                    <option value="openai">OpenAI (GPT-4o, o1, ...)</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="google">Google (Gemini)</option>
                    <option value="minimax">MiniMax</option>
                    <option value="deepseek">DeepSeek</option>
                    <option value="qwen">Qwen (通義千問)</option>
                    <option value="ollama">Ollama (Local)</option>
                </select>
```

- [ ] **Step 2: Add provider configs to aiConfig JS object**

Find:
```javascript
const aiConfig = {
    openai:    { label: 'OpenAI API Key', hint: 'Starts with sk-...', placeholder: 'sk-proj-...' },
    anthropic: { label: 'Anthropic API Key', hint: 'Starts with sk-ant-...', placeholder: 'sk-ant-api03-...' },
    google:    { label: 'Gemini API Key', hint: 'Google AI Studio key', placeholder: 'AIzaSy...' },
    ollama:    { label: 'Ollama Host', hint: 'Default: http://localhost:11434', placeholder: 'http://localhost:11434' },
};
```

Replace with:
```javascript
const aiConfig = {
    openai:    { label: 'OpenAI API Key', hint: 'Starts with sk-...', placeholder: 'sk-proj-...' },
    anthropic: { label: 'Anthropic API Key', hint: 'Starts with sk-ant-...', placeholder: 'sk-ant-api03-...' },
    google:    { label: 'Gemini API Key', hint: 'Google AI Studio key', placeholder: 'AIzaSy...' },
    minimax:   { label: 'MiniMax API Key', hint: 'MiniMax platform key', placeholder: 'Enter MiniMax API key' },
    deepseek:  { label: 'DeepSeek API Key', hint: 'DeepSeek platform key', placeholder: 'sk-...' },
    qwen:      { label: 'Qwen API Key', hint: 'Alibaba DashScope key', placeholder: 'sk-...' },
    ollama:    { label: 'Ollama Host', hint: 'Default: http://localhost:11434', placeholder: 'http://localhost:11434' },
};
```

- [ ] **Step 3: Add provider models to aiModels JS object**

Find:
```javascript
const aiModels = {
    openai:    ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-mini', 'gpt-4-turbo'],
    anthropic: ['claude-sonnet-4-20250514', 'claude-opus-4-20250514', 'claude-haiku-4-5-20251001'],
    google:    ['gemini-2.0-flash', 'gemini-2.5-pro'],
};
```

Replace with:
```javascript
const aiModels = {
    openai:    ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-mini', 'gpt-4-turbo'],
    anthropic: ['claude-sonnet-4-20250514', 'claude-opus-4-20250514', 'claude-haiku-4-5-20251001'],
    google:    ['gemini-2.0-flash', 'gemini-2.5-pro'],
    minimax:   ['MiniMax-M2.5', 'MiniMax-M2.1'],
    deepseek:  ['deepseek-chat', 'deepseek-reasoner'],
    qwen:      ['qwen-max', 'qwen-plus', 'qwen-turbo'],
};
```

- [ ] **Step 4: Commit**

```bash
git add openclaw-k3s-paas/setup-wizard/templates/index.html
git commit -m "feat: add MiniMax/DeepSeek/Qwen providers to setup wizard UI"
```

---

### Task 6: Convert setup wizard to light mode CSS

**Files:**
- Modify: `openclaw-k3s-paas/setup-wizard/templates/index.html` (CSS throughout)

- [ ] **Step 1: Replace CSS custom properties in :root**

Find:
```css
        :root {
            --primary-blue: #6183FC;
            --bg-body: #1a1a2e;
            --bg-card: rgba(30, 30, 50, 0.85);
            --bg-input: #2a2a3e;
            --border-card: rgba(97, 131, 252, 0.15);
            --border-input: rgba(97, 131, 252, 0.1);
            --text-primary: #ffffff;
            --text-body: #e0e0e0;
            --text-muted: #8888a0;
            --text-hint: #7a7a94;
            --green: #4ade80;
            --error: #f87171;
            --cyan: #7BDBE0;
            --royal-blue: #6791DE;
            --lavender: #C09FE0;
            --sand: #F1C692;
        }
```

Replace with:
```css
        :root {
            --primary-blue: #6183FC;
            --bg-body: #f5f7fa;
            --bg-card: rgba(255, 255, 255, 0.95);
            --bg-input: #f0f2f5;
            --border-card: rgba(97, 131, 252, 0.2);
            --border-input: rgba(200, 210, 230, 0.6);
            --text-primary: #1a1a2e;
            --text-body: #333344;
            --text-muted: #6b7280;
            --text-hint: #9ca3af;
            --green: #4ade80;
            --error: #f87171;
            --cyan: #7BDBE0;
            --royal-blue: #6791DE;
            --lavender: #C09FE0;
            --sand: #F1C692;
        }
```

- [ ] **Step 2: Replace body::before gradient**

Find:
```css
            background:
                radial-gradient(ellipse at 20% 0%, rgba(97,131,252,0.1) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 100%, rgba(123,219,224,0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(26,26,46,1) 0%, transparent 100%);
```

Replace with:
```css
            background:
                radial-gradient(ellipse at 20% 0%, rgba(97,131,252,0.08) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 100%, rgba(123,219,224,0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(245,247,250,1) 0%, transparent 100%);
```

- [ ] **Step 3: Replace card box-shadow**

Find:
```css
            box-shadow: 0 1px 3px rgba(0,0,0,0.2), 0 8px 32px rgba(0,0,0,0.3);
```

Replace with:
```css
            box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.1);
```

- [ ] **Step 4: Replace input:focus background**

Find:
```css
            background: #323250;
```

Replace with:
```css
            background: #ffffff;
```

- [ ] **Step 5: Replace select option background**

Find:
```css
        select option { background: var(--bg-input); color: var(--text-body); }
```

Replace with:
```css
        select option { background: #ffffff; color: var(--text-body); }
```

- [ ] **Step 6: Replace btn:disabled color**

Find:
```css
        .btn:disabled { background: rgba(97,131,252,0.35); cursor: not-allowed; transform: none; box-shadow: none; color: rgba(255,255,255,0.5); }
```

Replace with:
```css
        .btn:disabled { background: rgba(97,131,252,0.35); cursor: not-allowed; transform: none; box-shadow: none; color: rgba(255,255,255,0.7); }
```

- [ ] **Step 7: Replace step-dot background**

Find:
```css
        .step-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.15); }
```

Replace with:
```css
        .step-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(0,0,0,0.15); }
```

- [ ] **Step 8: Replace status-row border-bottom**

Find:
```css
        .status-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
```

Replace with:
```css
        .status-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.06); }
```

Note: `.chat-info-box` background (`rgba(97,131,252,0.06)`) is intentionally unchanged — provides sufficient contrast on the light background.

- [ ] **Step 9: Commit**

```bash
git add openclaw-k3s-paas/setup-wizard/templates/index.html
git commit -m "feat: convert setup wizard from dark mode to light mode"
```

---

### Task 7: Deploy and verify

- [ ] **Step 1: Apply the updated manifest**

```bash
echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl apply -f openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml
```

Expected: PVC created, deployment updated.

- [ ] **Step 2: Wait for gateway pod to restart**

```bash
echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n openclaw-tenant-1 rollout status deployment/openclaw-gateway --timeout=300s
```

Expected: `deployment "openclaw-gateway" successfully rolled out`

- [ ] **Step 3: Verify PVC is bound**

```bash
echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n openclaw-tenant-1 get pvc openclaw-agents-pvc
```

Expected: STATUS = `Bound`

- [ ] **Step 4: Verify agents directory is on PVC and auth-profiles.json is correct**

Run all verification commands in a single block (so `$POD` variable is available across steps):

```bash
POD=$(echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n openclaw-tenant-1 get pods -l app=openclaw-gateway -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "=== Pod: $POD ==="
echo "=== Agents directory ==="
echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n openclaw-tenant-1 exec "$POD" -- ls -la /home/node/.openclaw/agents/
echo "=== auth-profiles.json ==="
echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n openclaw-tenant-1 exec "$POD" -- cat /home/node/.openclaw/agents/main/agent/auth-profiles.json
echo "=== New env vars ==="
echo 'woowtech' | sudo -S KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl -n openclaw-tenant-1 exec "$POD" -- env | grep -E 'MINIMAX|DEEPSEEK|QWEN' || echo "No keys set (expected - optional)"
```

Expected:
- `main` directory present in agents/
- auth-profiles.json contains `openai.apiKey`
- New env vars either present or "No keys set" (both OK)
