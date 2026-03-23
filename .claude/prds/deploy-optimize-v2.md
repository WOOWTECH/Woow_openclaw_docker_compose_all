---
name: deploy-optimize-v2
description: OpenClaw K3s PaaS deployment optimization and issue fixes v2
status: backlog
created: 2026-03-22T02:23:42Z
---

# PRD: deploy-optimize-v2

## Executive Summary

優化 OpenClaw K3s PaaS 的部署流程和運行穩定性。解決 setup wizard 不跳轉、gateway workspace 缺少 MEMORY.md、Cloudflare Tunnel ghost 連線導致 502、以及 Control UI 事件間隔警告等問題。同時建立 3 個 cron job 驗證排程功能。

## Problem Statement

目前部署和運行存在以下問題：

1. **Setup Wizard 不自動跳轉**：初始部署完成後，頁面卡在 "Switching network routes..." 步驟，即使 OpenClaw gateway 已就緒，使用者必須手動刷新頁面才能登入。
2. **MEMORY.md 缺失**：OpenClaw agent workspace 中 MEMORY.md 顯示 MISSING，影響 agent 的持久記憶功能。
3. **Gateway Event Gap 警告**：Control UI 首頁出現紅色 "Gateway Error: event gap detected (expected seq N, got N+2)" 警告，嚇到使用者但實際上只是 WebSocket 序列號間隔。
4. **Cron Job 未設定**：定時任務功能顯示 0 jobs，需要建立測試用的 cron job 驗證排程系統正常。
5. **Cloudflare Tunnel 502 不穩定**：force-delete cloudflared pod 後 ghost connections 持續存在，導致 50% 請求返回 502。

## User Stories

### US-1: Setup Wizard 自動跳轉
**As a** 首次部署的管理員
**I want** setup wizard 在 gateway 就緒後自動跳轉到 OpenClaw 登入頁面
**So that** 我不需要手動刷新頁面或知道正確的 URL
**Acceptance criteria:**
- Setup wizard 偵測到 gateway 就緒後 3 秒內自動 redirect
- 顯示 "系統就緒，正在跳轉..." 提示訊息
- 如果 30 秒內無法跳轉，顯示手動連結

### US-2: MEMORY.md 預設建立
**As a** OpenClaw 使用者
**I want** agent workspace 自動建立預設的 MEMORY.md
**So that** agent 可以正常使用持久記憶功能
**Acceptance criteria:**
- Gateway 啟動時自動在 `/home/node/.openclaw/workspace/MEMORY.md` 建立預設檔案
- 如果檔案已存在，不覆蓋
- 預設內容包含基本的 agent 使用說明

### US-3: Event Gap 警告自動處理
**As a** Control UI 使用者
**I want** event gap 警告自動恢復而不顯示嚇人的紅色錯誤
**So that** 我不會誤以為系統出了嚴重問題
**Acceptance criteria:**
- Event gap 偵測到後自動 refresh WebSocket 連線
- 不在首頁顯示紅色 Gateway Error（改為 info 級別或自動處理）
- 如果持續發生，才升級為警告

### US-4: Cron Job 測試
**As a** 系統管理員
**I want** 3 個測試用 cron jobs 來驗證排程功能
**So that** 我確認 OpenClaw 的排程系統正常運作
**Acceptance criteria:**
- 建立 3 個不同頻率的 cron jobs（每 5 分鐘、每小時、每天）
- 每個 job 執行簡單的測試任務（如回報系統狀態）
- 在 GUI dashboard 上顯示 3 jobs 及其執行歷史

### US-5: Cloudflare Tunnel 穩定性
**As a** 系統管理員
**I want** cloudflared pod 重建時不產生 ghost connections
**So that** 重啟後不會出現 502 錯誤
**Acceptance criteria:**
- cloudflared deployment 加入 preStop hook 做 graceful shutdown
- terminationGracePeriodSeconds 足夠讓連線清理
- 重啟後 30 秒內 100% 可用

## Functional Requirements

### FR-1: Setup Wizard Redirect
- 在 Cloudflare route 切換完成後，前端 JavaScript 加入 polling 機制
- 每 3 秒用 fetch 嘗試存取 `https://domain/`
- 收到 200 回應後自動 redirect 到 `https://domain/#token=gateway_token`
- 加入 countdown timer 顯示等待進度

### FR-2: MEMORY.md Bootstrap
- 在 gateway 啟動腳本中加入 MEMORY.md 建立邏輯
- 路徑: `/home/node/.openclaw/workspace/MEMORY.md`
- 使用 `[ -f ... ] || cat > ...` 防止覆蓋

### FR-3: Event Gap Handling
- 這是 OpenClaw Control UI 的行為，由 OpenClaw 本身處理
- 在 gateway config 中設定 `gateway.trustedProxies` 減少不必要的連線中斷
- 文檔說明此警告為正常現象

### FR-4: Cron Jobs
- 透過 OpenClaw GUI 的 Cron 頁面建立 3 個 jobs
- Job 1: 每 5 分鐘執行 `echo "heartbeat check at $(date)"`
- Job 2: 每小時執行系統狀態檢查
- Job 3: 每天早上 9 點執行每日摘要

### FR-5: Cloudflared Graceful Shutdown
- 加入 `preStop` hook: `sleep 5` 讓 tunnel 連線有時間清理
- 設定 `terminationGracePeriodSeconds: 30`
- 部署 strategy 使用 `Recreate` 而非 `RollingUpdate` 避免雙 connector

## Non-Functional Requirements

- Setup wizard redirect 不需要後端修改，純前端 JavaScript
- MEMORY.md 建立不影響啟動速度（< 1ms）
- Cloudflared 重啟後 30 秒內恢復可用
- 所有修改需向後兼容現有部署

## Success Criteria

1. 新部署時 setup wizard 自動跳轉到 OpenClaw（不需手動刷新）
2. MEMORY.md 在 gateway 啟動後自動存在
3. Dashboard 不再顯示紅色 event gap 錯誤（或自動恢復）
4. 3 個 cron jobs 正常運行並在 dashboard 顯示
5. cloudflared pod 重啟後 100% 可用（無 502）

## Constraints & Assumptions

- 不修改 OpenClaw 核心程式碼（只修改部署配置）
- Event gap 是 OpenClaw Control UI 的內建行為，只能透過配置或文檔處理
- Cron jobs 需要 OpenAI API 金鑰正常運作
- Cloudflare API Token 只有 tunnel 管理權限（無 zone 設定權限）

## Out of Scope

- OpenClaw 版本升級
- LINE webhook 設定（已在前一個迭代完成）
- Cloudflare WAF/Bot Protection 配置（需要更高權限的 API Token）
- 多租戶支援

## Dependencies

- OpenClaw gateway image: `ghcr.io/openclaw/openclaw:latest`
- Cloudflare Tunnel API
- OpenAI API（cron jobs 需要）
- K3s cluster 正常運行
