# PRD: OpenClaw Memory-LanceDB-Pro 本地向量記憶系統

## 文件資訊

| 欄位 | 值 |
|------|-----|
| 版本 | 1.0 |
| 建立日期 | 2026-03-31 |
| 作者 | Woowtech / Claude Opus 4.6 |
| 狀態 | 已部署 (Production) |
| 分支 | `k3s`, `main` |
| Repo | https://github.com/WOOWTECH/Woow_openclaw_docker_compose_all |

---

## 1. 背景與動機

OpenClaw 作為 Woowtech Smart Space 的核心 AI 閘道器，支援 LINE、Telegram、WhatsApp、Web 等多頻道對話。然而，原架構缺乏**跨 session 長期記憶能力**——每次新對話都從零開始，無法記住使用者之前告知的偏好、技術環境、個人資訊等。

### 問題陳述

- 使用者需要反覆告知相同資訊（住址、公司、技術配置等）
- AI 無法累積對使用者的理解，降低使用體驗
- 無法建立個人化的長期知識庫

### 解決方案

整合 **memory-lancedb-pro** 插件 + **Ollama** 本地推論服務，實現全本地、零 API 成本的向量記憶系統。

---

## 2. 目標

### 必須達成 (Must Have)

- [x] 對話內容自動萃取有價值的記憶片段（autoCapture）
- [x] 新 session 開始時自動召回相關記憶（autoRecall）
- [x] 支援語義搜尋（向量相似度），不需完全匹配關鍵字
- [x] 噪音過濾：閒聊/無意義對話不被儲存
- [x] 記憶持久化：pod 重啟不遺失資料
- [x] 全本地運行：不依賴外部 API，零額外費用

### 應該達成 (Should Have)

- [x] 記憶更新能力：使用者可修正舊資訊
- [x] 跨語言召回：英文問題能搜尋中文記憶
- [x] 複合查詢：一次召回多領域資訊（個人 + 技術 + 偏好）
- [x] Memory-First 行為：AI 優先查記憶而非執行系統指令

### 可以達成 (Nice to Have)

- [ ] Reranker 整合（Jina / SiliconFlow）
- [ ] 記憶過期與衰減（recencyHalfLifeDays）
- [ ] 多 Agent 記憶隔離（scope isolation）
- [ ] 記憶匯出/匯入功能

---

## 3. 系統架構

### 3.1 元件概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                     K3s Cluster (9 nodes)                        │
│                                                                   │
│  ┌──────────────── control-plane (16C/16GB) ────────────────┐   │
│  │                                                            │   │
│  │  ┌─────────────────┐  ┌────────────────────────────────┐ │   │
│  │  │   Cloudflared    │  │    OpenClaw Gateway            │ │   │
│  │  │   (tunnel)       │  │    - memory-lancedb-pro plugin │ │   │
│  │  └─────────────────┘  │    - nomic-embed-text (768d)   │ │   │
│  │                        │    - llama3:8b extraction      │ │   │
│  │  ┌─────────────────┐  │    - LanceDB (embedded)        │ │   │
│  │  │  Setup Wizard   │  │    - skills/                    │ │   │
│  │  └─────────────────┘  └────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  PVC: openclaw-agents-pvc (1Gi)                           │   │
│  │    ├── _workspace/    (SOUL.md, MEMORY.md, skills/)       │   │
│  │    ├── _memory/       (lancedb-pro/memories.lance)        │   │
│  │    ├── _extensions/   (plugin backup cache)               │   │
│  │    ├── _config/       (GOG OAuth, Chromium)               │   │
│  │    └── _openclaw.json (plugins config)                    │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌── woowtechopenclaw-default-string (4C/16GB) ──┐              │
│  │                                                 │              │
│  │  ┌─────────────────────────────────────────┐   │              │
│  │  │         Ollama Server                    │   │              │
│  │  │   - nomic-embed-text (274MB, F16)       │   │              │
│  │  │   - llama3:8b (4.7GB, Q4_0)            │   │              │
│  │  │   - API: http://ollama-svc:11434        │   │              │
│  │  └─────────────────────────────────────────┘   │              │
│  │                                                 │              │
│  │  PVC: ollama-models-pvc (15Gi)                 │              │
│  └─────────────────────────────────────────────────┘              │
│                                                                   │
│  ┌──────── cluster4 (4C/4GB) ────────┐                          │
│  │  PostgreSQL + pgvector             │                          │
│  │  PVC: openclaw-db-pvc (10Gi)      │                          │
│  └────────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 記憶處理流程

```
使用者對話 (LINE/Telegram/Web)
         │
         ▼
┌─────────────────────┐
│  OpenClaw Gateway    │
│  (MiniMax-M2.5)     │◄── autoRecall: 新 session 啟動時
│                     │    查詢 LanceDB 找相關記憶
│  ┌───────────────┐  │
│  │ memory_recall │──┼──► LanceDB hybrid search
│  │ memory_store  │  │    (vector 0.7 + BM25 0.3)
│  │ memory_update │  │
│  │ memory_forget │  │
│  └───────────────┘  │
└────────┬────────────┘
         │ session 結束
         ▼ autoCapture 觸發
┌─────────────────────┐     ┌─────────────────────┐
│  llama3:8b          │     │  nomic-embed-text    │
│  (Ollama CPU)       │     │  (Ollama CPU)        │
│                     │     │                      │
│  Smart Extraction:  │     │  向量化:              │
│  - 判斷是否有價值   │────►│  - 768 維 embedding   │
│  - 萃取結構化事實   │     │  - 存入 LanceDB      │
│  - 過濾噪音        │     │                      │
└─────────────────────┘     └─────────────────────┘
```

---

## 4. 技術規格

### 4.1 新增 K8s 資源

| 資源 | 檔案 | 說明 |
|------|------|------|
| **Ollama Deployment** | `07-ollama.yaml` | CPU 推論伺服器 |
| **Ollama Service** | `07-ollama.yaml` | `ollama-svc:11434` (ClusterIP) |
| **Ollama PVC** | `07-ollama.yaml` | 15Gi 模型儲存 |
| **Model Init Job** | `08-ollama-model-init.yaml` | 自動拉取模型 |

### 4.2 修改的 K8s 資源

| 資源 | 變更 |
|------|------|
| **Gateway Deployment** | 新增 extensions 復原邏輯、plugin 安裝、config 注入 |
| **Gateway Resources** | requests 2C/4Gi, limits 12C/12Gi |
| **Gateway Strategy** | RollingUpdate → Recreate（PVC 互斥） |
| **PostgreSQL Limits** | cpu 500m → 2C, memory 512Mi → 2Gi |
| **Agents PVC** | 1Gi → 5Gi（manifest; live 仍 1Gi，local-path 不支援擴容） |
| **SOUL.md** | 新增 Memory-First Principle |

### 4.3 Plugin 配置

```json
{
  "autoCapture": true,
  "autoRecall": true,
  "smartExtraction": true,
  "extractMinMessages": 2,
  "extractMaxChars": 12000,
  "embedding": {
    "provider": "openai-compatible",
    "baseURL": "http://ollama-svc:11434/v1",
    "model": "nomic-embed-text",
    "apiKey": "ollama"
  },
  "llm": {
    "baseURL": "http://ollama-svc:11434/v1",
    "model": "llama3:8b",
    "apiKey": "ollama"
  },
  "retrieval": {
    "mode": "hybrid",
    "vectorWeight": 0.7,
    "bm25Weight": 0.3,
    "minScore": 0.2,
    "hardMinScore": 0.25,
    "candidatePoolSize": 50
  }
}
```

### 4.4 環境變數

| 變數 | 值 | 用途 |
|------|-----|------|
| `OLLAMA_BASE_URL` | `http://ollama-svc:11434` | Ollama API 端點 |
| `OLLAMA_API_BASE` | `http://ollama-svc:11434/v1` | OpenAI 相容端點 |

---

## 5. 資源消耗

### 5.1 整體專案資源

| 元件 | CPU Request | Memory Request | CPU Limit | Memory Limit | 節點 |
|------|------------|----------------|-----------|--------------|------|
| OpenClaw Gateway | 2C | 4Gi | 12C | 12Gi | control-plane |
| Ollama | 2C | 4Gi | 4C | 14Gi | openclaw-default |
| PostgreSQL | 100m | 256Mi | 2C | 2Gi | cluster4 |
| Cloudflared | 50m | 64Mi | 200m | 128Mi | control-plane |
| Setup Wizard | 50m | 64Mi | 200m | 256Mi | control-plane |
| **合計** | **4.2C** | **8.4Gi** | **18.4C** | **28.4Gi** | 3 nodes |

### 5.2 實際消耗（測量值）

| 元件 | CPU 實際 | Memory 實際 |
|------|----------|-------------|
| Gateway | ~885m | ~1.1Gi |
| Ollama（待機） | ~617m | ~448Mi |
| Ollama（推論中） | ~4C | ~5-6Gi |
| PostgreSQL | ~63m | ~28Mi |
| **專案合計** | ~1.6C | ~1.6Gi |

### 5.3 儲存消耗

| PVC | 容量 | 用途 |
|-----|------|------|
| ollama-models-pvc | 15Gi | llama3:8b (4.7GB) + nomic-embed-text (274MB) |
| openclaw-db-pvc | 10Gi | PostgreSQL + pgvector |
| openclaw-agents-pvc | 1Gi | config, skills, LanceDB, workspace |
| **合計** | **26Gi** | |

---

## 6. 持久化策略

### 6.1 Plugin 持久化（關鍵設計）

`openclaw plugins install` 不支援 symlink 目錄，因此採用 **real directory + PVC backup/restore** 策略：

```
啟動時:
  PVC/_extensions/memory-lancedb-pro ─── cp -a ──► /home/node/.openclaw/extensions/

首次安裝後:
  /home/node/.openclaw/extensions/memory-lancedb-pro ─── cp -a ──► PVC/_extensions/
```

### 6.2 LanceDB 資料持久化

```
/home/node/.openclaw/memory ──symlink──► PVC/_memory/
  └── lancedb-pro/
      └── memories.lance/     ← 向量資料庫（自動持久化）
```

### 6.3 Config 持久化

```
/home/node/.openclaw/openclaw.json ──symlink──► PVC/_openclaw.json
  └── plugins.entries.memory-lancedb-pro.config  ← 插件配置
```

---

## 7. 測試結果

### 7.1 測試總覽

共執行 **17 項測試**，優化後全數通過。

### 7.2 測試矩陣

| # | 類型 | 測試名稱 | 結果 | 說明 |
|---|------|---------|------|------|
| 1 | 寫入 | SEED-TECH | PASS | 技術基礎設施資訊寫入 |
| 2 | 寫入 | SEED-SCHEDULE | PASS | 行程/偏好寫入 |
| 3 | 寫入 | SEED-NETWORK | PASS | IP/網路資訊寫入 |
| 4 | 召回 | T01-DIRECT | PASS | 直接事實召回（姓名+地址） |
| 5 | 召回 | T02-SEMANTIC | PASS | 語義召回（「寫程式工具」→ VS Code） |
| 6 | 召回 | T03-INFRA | PASS* | 基礎設施召回（優化後通過） |
| 7 | 召回 | T04-NETWORK | PASS | IP/品牌召回 |
| 8 | 召回 | T05-SCHEDULE | PASS | 行程召回（週三/週五） |
| 9 | 召回 | T06-COMPOSITE | PASS* | 綜合整理 11/12 項（優化後通過） |
| 10 | 邊緣 | T07-NEGATION | PASS | 否定記憶（「討厭的食物」→ 香菜） |
| 11 | 邊緣 | T08-FUZZY | PASS | 模糊召回（「好像說過生日」） |
| 12 | 邊緣 | T09-ENGLISH | PASS | 跨語言（英文問中文記憶） |
| 13 | 更新 | T10-UPDATE | PASS | 記憶更新（搬家後新地址） |
| 14 | 過濾 | T11-NOISE | PASS | 噪音過濾（閒聊未儲存） |
| 15 | 長文 | SEED-LONG | PASS | 長文架構資訊寫入 |
| 16 | 長文 | T12-LONGRECALL | PASS | 長文技術細節召回 |
| 17 | 工具 | T06-TOOL | PASS | memory_recall 直接呼叫 |

*\* 標記項目在第一輪測試失敗，經優化後通過*

### 7.3 優化歷程

| 輪次 | 變更 | 效果 |
|------|------|------|
| Round 1 | 初始部署 | 13/17 通過 (76%) |
| Round 2 | minScore 0.3→0.2, candidatePoolSize 20→30 | 改善技術事實召回 |
| Round 3 | SOUL.md Memory-First, candidatePoolSize 30→50 | 17/17 通過 (100%) |

---

## 8. 已知限制

1. **PVC 無法線上擴容**：`local-path` StorageClass 不支援 volume expansion。agents-pvc 仍為 1Gi（manifest 標記 5Gi 供新建環境使用）
2. **Ollama CPU 推論延遲**：llama3:8b 記憶萃取耗時 5-15 秒（CPU only）
3. **plugins.allow 警告**：gateway 日誌中顯示 plugins.allow 未設定，插件以 untracked 模式載入
4. **記憶容量**：1Gi PVC 中 LanceDB 目前佔 2.8MB（120 筆記憶），長期使用需監控

---

## 9. 部署指南

### 9.1 首次部署

```bash
# 1. 部署 Ollama
kubectl apply -f k8s-manifests/07-ollama.yaml

# 2. 等 Ollama Ready 後，拉取模型
kubectl apply -f k8s-manifests/08-ollama-model-init.yaml
kubectl logs -f job/ollama-model-init -n openclaw-tenant-1

# 3. 部署/更新 OpenClaw Gateway
kubectl apply -f k8s-manifests/06-openclaw-core.yaml

# 4. 驗證
kubectl logs deployment/openclaw-gateway -n openclaw-tenant-1 | grep "plugin registered"
```

### 9.2 驗證指令

```bash
# 檢查 plugin 狀態
kubectl logs deployment/openclaw-gateway -n openclaw-tenant-1 | grep memory-lancedb-pro

# 測試 Ollama 連線
kubectl exec deployment/openclaw-gateway -n openclaw-tenant-1 -- \
  wget -qO- http://ollama-svc:11434/api/tags

# 測試 embedding
kubectl exec deployment/openclaw-gateway -n openclaw-tenant-1 -- \
  wget -qO- --post-data '{"model":"nomic-embed-text","prompt":"test"}' \
  --header='Content-Type: application/json' http://ollama-svc:11434/api/embeddings

# 測試記憶寫入/召回
kubectl exec deployment/openclaw-gateway -n openclaw-tenant-1 -- \
  openclaw agent --session-id test-001 --message "記住：我叫測試使用者"
kubectl exec deployment/openclaw-gateway -n openclaw-tenant-1 -- \
  openclaw agent --session-id test-002 --message "我叫什麼名字？"
```

### 9.3 重新拉取模型

```bash
kubectl delete job ollama-model-init -n openclaw-tenant-1
kubectl apply -f k8s-manifests/08-ollama-model-init.yaml
```

---

## 10. Commit 歷程

| Commit | 說明 |
|--------|------|
| `c01ac00` | Add Ollama + memory-lancedb-pro integration for local vector memory |
| `0f36c27` | Fix plugin persistence, tune resources, and target Ollama to idle node |
| `d04bfaa` | Tune memory-lancedb-pro retrieval: lower minScore, expand pool |
| `020121b` | Add memory-first principle to SOUL.md, expand candidate pool to 50 |

---

## 11. 後續規劃

| 優先級 | 項目 | 說明 |
|--------|------|------|
| P1 | 監控 LanceDB 儲存增長 | 當前 2.8MB / 1Gi PVC |
| P2 | 加入 Reranker | Jina reranker-v3 提升排序品質 |
| P2 | plugins.allow 白名單 | 消除 untracked plugin 警告 |
| P3 | GPU 加速 | 若有 GPU 節點可大幅降低推論延遲 |
| P3 | 記憶衰減機制 | timeDecayHalfLifeDays 自動淘汰過時記憶 |
