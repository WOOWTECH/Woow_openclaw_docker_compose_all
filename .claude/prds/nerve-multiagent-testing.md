---
name: nerve-multiagent-testing
description: Enterprise-grade testing of Nerve WebGUI multi-agent CRUD, sync, memory, and cross-module interaction
status: active
created: 2026-04-03T00:00:00Z
---

# PRD: Nerve Multi-Agent Enterprise Testing

## Executive Summary

驗證 Nerve WebGUI 的多 Agent 功能在商用部署環境下的穩定性、完整性和可靠度。涵蓋 Agent CRUD 操作、CLI↔GUI 雙向同步、記憶面板存取、MODEL dropdown、跨 Agent 對話正確性、邊緣條件容錯，以及 Pod 重啟後的持久化恢復。

## Problem Statement

Nerve WebGUI 的多 Agent 模式存在已識別的限制（已修復）和未經充分驗證的功能邊界：
1. CLI 建立的 Agent 是否在 Nerve 重啟後仍可見
2. 非 main Agent 的 workspace/memory 是否持久化到 PVC
3. 多 Agent 並行對話時的穩定性
4. Agent 刪除後的清理完整性
5. 不同 Agent 之間的對話隔離

## User Stories

### US1: Agent CRUD via Nerve GUI
**As** 系統管理員
**I want** 在 Nerve GUI 中建立、查看、切換、刪除 Agent
**So that** 不需要 SSH 到 Pod 就能管理 Agent
**Acceptance Criteria**:
- 點 "+" 可建立新 Top-level Agent，填寫 name/task/model
- 新 Agent 立即出現在 sidebar
- 可以在 Agent 之間切換對話
- 可以刪除 Agent（如支援）

### US2: CLI → Nerve 同步
**As** DevOps 工程師
**I want** CLI 建立的 Agent 自動出現在 Nerve GUI
**So that** 不論從哪邊建立 Agent，兩邊都保持同步
**Acceptance Criteria**:
- `openclaw agents add` 建立的 Agent 在 Pod 重啟後出現在 Nerve sidebar
- Agent 的 model、workspace 設定一致

### US3: Agent 對話正確性
**As** 使用者
**I want** 每個 Agent 根據其設定的角色回答問題
**So that** odoo-erp Agent 只做 ERP 查詢，sys-admin 只做系統管理
**Acceptance Criteria**:
- 每個 Agent 的回應標籤顯示正確的 Agent name
- 回應內容符合 opening task 設定的角色
- Agent 使用正確的工具（exec、ha_*、web_search 等）

### US4: 記憶面板存取
**As** 使用者
**I want** 在 Nerve GUI 中查看非 main Agent 的記憶
**So that** 所有 Agent 的記憶都可管理
**Acceptance Criteria**:
- 切換到非 main Agent 時不顯示 "Sandboxed Workspace"
- 記憶面板可以查看、新增記憶

### US5: Pod 重啟持久化
**As** SRE 工程師
**I want** Pod 重啟後所有 Agent 和對話歷史保持完整
**So that** 維護操作不會遺失 Agent 配置
**Acceptance Criteria**:
- 重啟前後 Agent 數量一致
- 重啟前後 session 數量不減少
- workspace 資料完整

## Functional Requirements

### FR1: Browser Automation Tests (Playwright)
- **R1.1** 登入 Nerve，確認 sidebar 顯示所有已註冊 Agent
- **R1.2** 透過 GUI 建立新 Agent（Top-level），確認建立成功
- **R1.3** 切換到不同 Agent 的對話，發送訊息，驗證回應
- **R1.4** 驗證 MODEL dropdown 顯示可選模型
- **R1.5** 測試快速連續切換 Agent（穩定性壓力測試）

### FR2: Backend API Tests
- **R2.1** `/api/gateway/models` 返回模型列表
- **R2.2** `/api/workspace` 返回 workspace 檔案列表
- **R2.3** `/api/files/tree` 返回每個 Agent workspace 的檔案樹
- **R2.4** `/api/files/read` 可讀取非 main Agent 的 SOUL.md
- **R2.5** `/api/files?path=...` 可讀取非 main Agent workspace 中的圖片

### FR3: Cross-Module Interaction Tests
- **R3.1** Agent A (odoo-erp) 查詢 Odoo 資料 → memory_store → Agent B (main) 可 memory_recall
- **R3.2** Agent A 用 exec 工具 → 結果保存到 workspace → 其他 Agent 可讀取
- **R3.3** Cron job 觸發 → 指定 Agent 處理 → Telegram 推送

### FR4: Edge Cases
- **R4.1** 建立名稱含特殊字元的 Agent（如空格、中文）
- **R4.2** 建立已存在名稱的 Agent（應優雅處理）
- **R4.3** 同時向多個 Agent 發送訊息
- **R4.4** 超長 opening task 文字
- **R4.5** MODEL dropdown 選擇後又切換回來

### FR5: Persistence Tests (Pod Restart)
- **R5.1** 記錄重啟前的 Agent 數量和 session 數量
- **R5.2** 執行 `kubectl rollout restart`
- **R5.3** 驗證重啟後 Agent 數量和 session 數量一致
- **R5.4** 驗證重啟後可正常切換到每個 Agent 並對話

## Non-Functional Requirements

- **NF1** 所有測試在 10 分鐘內完成
- **NF2** Pod 在測試期間 0 restarts
- **NF3** 所有測試截圖保存在 /tmp/ 作為審計證據
- **NF4** 支援 headless 和 headed 模式

## Success Criteria

| Metric | Target |
|--------|--------|
| FR1 Browser Tests | 5/5 pass |
| FR2 API Tests | 5/5 pass |
| FR3 Cross-Module | 3/3 pass |
| FR4 Edge Cases | 4/5 pass (1 may be unsupported) |
| FR5 Persistence | 4/4 pass |
| Total | ≥90% pass rate |
| Pod Restarts | 0 during testing |

## Constraints & Assumptions

- Nerve v1.5.2 on K3s, OpenClaw v2026.3.31
- MiniMax-M2.7 as default (and only configured) model
- 9 agents currently registered (main + 8 custom)
- Tests run via Playwright headless Chromium
- Gateway and Nerve share PVC at /mnt/openclaw-agents

## Out of Scope

- WhatsApp/LINE channel testing (requires physical device)
- Load testing (>100 concurrent users)
- Nerve source code modification (only init script changes)
- Model switching mid-conversation

## Dependencies

- Nerve WebGUI accessible at https://cindytech1-nerve.woowtech.io
- Gateway health: `{"ok":true,"status":"live"}`
- Ollama models: nomic-embed-text + llama3:8b
- Odoo ERP: https://woowtech-odoo.woowtech.io
- Home Assistant: https://woowtech-ha.woowtech.io

## Test Rounds

### Round 1: Smoke Test — API + Sidebar
確認基礎設施正常，所有 Agent 可見

### Round 2: Agent CRUD — GUI 建立 + 刪除
完整 CRUD 生命週期

### Round 3: Cross-Agent 對話
每個 Agent 發送任務，驗證回應正確性

### Round 4: Edge Cases
特殊字元、重複名稱、並行訊息

### Round 5: Persistence
Pod 重啟前後對比

### Round 6: 綜合壓力
多輪快速切換 + 連續對話
