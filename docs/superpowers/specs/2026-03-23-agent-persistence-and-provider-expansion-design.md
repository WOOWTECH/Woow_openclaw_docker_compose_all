# Agent 持久化與 AI Provider 擴充設計

## 問題

1. 使用者透過 OpenClaw web GUI 建立的 agent（如 GPT、MiniMax 等）在 pod 重啟後消失，因為容器 filesystem 是 ephemeral 的。
2. Setup Wizard 只支援 4 個 AI provider（OpenAI、Anthropic、Google、Ollama），缺少 MiniMax、DeepSeek、Qwen 等主流模型。
3. Setup Wizard 目前是深色模式，需改回淺色模式。

## 方案

採用**方案 B：PVC 只掛載 `agents/` 子目錄**。

- `agents/` 持久化 → web GUI 建立的 agent 在 pod 重啟後保留
- `openclaw.json` 和其他 config 每次啟動仍從 env vars 重建 → API key 更新自動生效
- 最小變動，風險最低

## 變更範圍

### 1. PersistentVolumeClaim — agents 目錄持久化

**檔案**：`openclaw-k3s-paas/k8s-manifests/06-openclaw-core.yaml`

#### PVC 定義

```yaml
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
```

使用 K3s 預設 StorageClass（`local-path`），`ReadWriteOnce` 即可（單 replica 部署）。

#### Gateway Deployment 新增 volume/volumeMount

```yaml
# 在 containers[0].volumeMounts 新增：
- name: agents-data
  mountPath: /home/node/.openclaw/agents

# 在 spec.template.spec.volumes 新增：
- name: agents-data
  persistentVolumeClaim:
    claimName: openclaw-agents-pvc
```

PVC 在容器啟動前掛載，因此現有的 `mkdir -p /home/node/.openclaw/agents/main/agent` 會在 PV 內建立目錄，可保持不變。

#### 啟動腳本 auth-profiles.json 合併邏輯

現有做法（每次從空物件覆寫）：
```sh
AUTH='{}'
[ -n "${OPENAI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "...overwrite...")
echo "$AUTH" > /home/node/.openclaw/agents/main/agent/auth-profiles.json
```

改為合併模式（讀取既有 → 合併 env vars → 寫回）：
```sh
AUTH_FILE="/home/node/.openclaw/agents/main/agent/auth-profiles.json"
# 讀取既有的 auth-profiles.json，若不存在或無效則用空物件
AUTH=$(cat "$AUTH_FILE" 2>/dev/null || echo '{}')
# 驗證 JSON 有效，無效則重置
echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{try{JSON.parse(d)}catch(e){process.exit(1)}})" || AUTH='{}'

# 合併 env vars（只新增/更新，不刪除既有 key）
[ -n "${OPENAI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.openai={apiKey:process.env.OPENAI_API_KEY};console.log(JSON.stringify(o))})")
[ -n "${ANTHROPIC_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.anthropic={apiKey:process.env.ANTHROPIC_API_KEY};console.log(JSON.stringify(o))})")
[ -n "${GEMINI_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.google={apiKey:process.env.GEMINI_API_KEY};console.log(JSON.stringify(o))})")
[ -n "${MINIMAX_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.minimax={apiKey:process.env.MINIMAX_API_KEY};console.log(JSON.stringify(o))})")
[ -n "${DEEPSEEK_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.deepseek={apiKey:process.env.DEEPSEEK_API_KEY};console.log(JSON.stringify(o))})")
[ -n "${QWEN_API_KEY:-}" ] && AUTH=$(echo "$AUTH" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const o=JSON.parse(d);o.qwen={apiKey:process.env.QWEN_API_KEY};console.log(JSON.stringify(o))})")

echo "$AUTH" > "$AUTH_FILE"
```

效果：使用者透過 web GUI 手動加入的 provider key（如 MiniMax）會被保留，env vars 裡的 key 會新增或更新。所有 provider 統一使用 `{"apiKey": "..."}` 格式。

### 2. Setup Wizard — 新增 AI Provider

**檔案**：`openclaw-k3s-paas/setup-wizard/app.py`、`openclaw-k3s-paas/setup-wizard/templates/index.html`

新增 3 個 AI Provider：

| Provider | env var | 預設模型 | auth key |
|----------|---------|---------|----------|
| MiniMax | `MINIMAX_API_KEY` | `minimax/MiniMax-M2.5` | `minimax` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` | `deepseek` |
| Qwen | `QWEN_API_KEY` | `qwen/qwen-max` | `qwen` |

所有新 provider 統一使用 `{"apiKey": "..."}` 格式寫入 `auth-profiles.json`，與現有 OpenAI/Anthropic/Google 一致。

#### app.py 變更

`AI_ENV_MAP` 新增：
```python
"minimax": "MINIMAX_API_KEY",
"deepseek": "DEEPSEEK_API_KEY",
"qwen": "QWEN_API_KEY",
```

`AI_MODEL_MAP` 新增：
```python
"minimax": "minimax/MiniMax-M2.5",
"deepseek": "deepseek/deepseek-chat",
"qwen": "qwen/qwen-max",
```

`AI_AUTH_KEY` 新增：
```python
"minimax": "minimax",
"deepseek": "deepseek",
"qwen": "qwen",
```

`run_setup` 和 `configure_gateway` 不需改動 — 它們已透過 `AI_ENV_MAP` 和 `AI_AUTH_KEY` dict 動態取值。Setup wizard 的 `create_secret` 使用 `patch_namespaced_secret`（strategic merge patch），會新增 key 而不移除既有 key。

#### index.html 變更

`<select id="ai_provider">` 新增選項：
```html
<option value="minimax">MiniMax</option>
<option value="deepseek">DeepSeek</option>
<option value="qwen">Qwen (通義千問)</option>
```

`aiConfig` 新增：
```javascript
minimax:  { label: 'MiniMax API Key', hint: 'MiniMax platform key', placeholder: 'Enter MiniMax API key' },
deepseek: { label: 'DeepSeek API Key', hint: 'DeepSeek platform key', placeholder: 'sk-...' },
qwen:     { label: 'Qwen API Key', hint: 'Alibaba DashScope key', placeholder: 'sk-...' },
```

`aiModels` 新增：
```javascript
minimax:  ['MiniMax-M2.5', 'MiniMax-M2.1'],
deepseek: ['deepseek-chat', 'deepseek-reasoner'],
qwen:     ['qwen-max', 'qwen-plus', 'qwen-turbo'],
```

#### Gateway Manifest 變更

`06-openclaw-core.yaml` 的 env 區塊新增：
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

### 3. Setup Wizard — 淺色模式

**檔案**：`openclaw-k3s-paas/setup-wizard/templates/index.html`

CSS 變數替換：

| 變數 | 深色（原） | 淺色（新） |
|------|-----------|-----------|
| `--bg-body` | `#1a1a2e` | `#f5f7fa` |
| `--bg-card` | `rgba(30,30,50,0.85)` | `rgba(255,255,255,0.95)` |
| `--bg-input` | `#2a2a3e` | `#f0f2f5` |
| `--border-card` | `rgba(97,131,252,0.15)` | `rgba(97,131,252,0.2)` |
| `--border-input` | `rgba(97,131,252,0.1)` | `rgba(200,210,230,0.6)` |
| `--text-primary` | `#ffffff` | `#1a1a2e` |
| `--text-body` | `#e0e0e0` | `#333344` |
| `--text-muted` | `#8888a0` | `#6b7280` |
| `--text-hint` | `#7a7a94` | `#9ca3af` |

非變數的硬編碼顏色修正：

| 選擇器 | 屬性 | 深色（原） | 淺色（新） |
|--------|------|-----------|-----------|
| `body::before` | background gradients | 深色漸層 | `radial-gradient(ellipse at 20% 0%, rgba(97,131,252,0.08) 0%, transparent 60%), radial-gradient(ellipse at 80% 100%, rgba(123,219,224,0.05) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(245,247,250,1) 0%, transparent 100%)` |
| `input:focus` | background | `#323250` | `#ffffff` |
| `select option` | background | `var(--bg-input)` | `#ffffff` |
| `.step-dot` | background | `rgba(255,255,255,0.15)` | `rgba(0,0,0,0.15)` |
| `.card` | box-shadow | `0 1px 3px rgba(0,0,0,0.2), 0 8px 32px rgba(0,0,0,0.3)` | `0 1px 3px rgba(0,0,0,0.08), 0 8px 32px rgba(0,0,0,0.1)` |
| `.status-row` | border-bottom | `rgba(255,255,255,0.05)` | `rgba(0,0,0,0.06)` |
| `.chat-info-box` | background | `rgba(97,131,252,0.06)` | `rgba(97,131,252,0.06)`（不變，淺色背景下對比度足夠） |
| `.btn:disabled` | color | `rgba(255,255,255,0.5)` | `rgba(255,255,255,0.7)` （按鈕底色仍為藍色，白字不變但提高可見度） |
| `.check-circle::after` | border color | `white` | `white`（不變，綠底白勾） |

保持 Outfit 字型和 `--primary-blue: #6183FC` 主色不變。

## 遷移注意事項

- **首次套用 PVC 時**：PV 掛載後為空目錄，現有 pod 內 ephemeral 的 agent 資料會被空 PV 覆蓋。如有需要保留的 agent，應先用 `kubectl cp` 匯出，套用後再匯入。
- **回滾方式**：如遇問題，移除 Deployment 中的 `agents-data` volume/volumeMount，刪除 PVC，回到 ephemeral 模式即可。

## 不在範圍內

- 自動建立預設 agent（使用者透過 web GUI 自行建立）
- 修改 OpenClaw 內建的 chat UI（使用既有下拉選單）
- Workspace 或其他資料的持久化
