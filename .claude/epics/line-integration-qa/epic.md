---
name: line-integration-qa
status: backlog
created: 2026-06-09T00:23:40Z
updated: 2026-06-09T00:23:40Z
progress: 0%
prd: .claude/prds/line-integration-qa.md
github: (will be set on sync)
---

# Epic: line-integration-qa

## Overview

組建 5 角色 Agent 團隊，對 LINE 三套件進行多輪品質迭代。每輪由「LINE 商業對標→流程測試→錯誤解析→程式修復→獨立審計」五步驟組成，迭代至評分 ≥ 98%。

## Team Architecture (5 Roles)

### Role 1: LINE/LIFF 官方商業專家 (LINE Business Expert)
- **職責**：對標 LINE 官方帳號 2.0 最佳實踐、LIFF v2 標準、健身/醫美/按摩業 LINE 整合案例
- **輸出**：商業場景矩陣、LINE 官方規範檢查清單

### Role 2: Odoo 流程測試操作專家 (Odoo Flow Tester)
- **職責**：執行 Playwright + API 測試，驗證 LIFF 登入、Flex 推播、webhook、LiveChat
- **輸出**：測試報告（通過/失敗/截圖/log）

### Role 3: 錯誤解析專家 (Error Analyst)
- **職責**：分析失敗根因，判斷是 code bug、LINE API 限制還是設定問題
- **輸出**：根因報告 + 修復建議

### Role 4: 程式碼修復專家 (Code Fixer)
- **職責**：修復 Python/JS/XML 程式碼，推送到各 GitHub repo，部署驗證
- **輸出**：修復 commit + 模組升級驗證

### Role 5: 獨立品質審計專家 (QA Auditor)
- **職責**：不參與修復，純粹以 7 大面向評分
- **輸出**：評分報告（100 分制）

## Scoring Framework (QA Auditor)

| 面向 | 權重 | 評分標準 |
|------|------|---------|
| LIFF 登入流程 | 20% | bridge page→LIFF login→id_token→session 全流程正確 |
| Flex Message 推播 | 20% | 通用卡片+Automated Action卡片、灰階設計、雙重推播防護 |
| Webhook 接收 | 10% | signature 驗證、event 分派、error handling |
| Rich Menu 整合 | 10% | LIFF URL path concat、頁面導向正確 |
| LiveChat 串接 | 15% | LINE→Odoo→LINE 雙向即時通訊 |
| Portal/LIFF 頁面 | 10% | /liff/redirect、/home 等頁面正確載入 |
| 商業合理性 | 15% | LINE 官方最佳實踐、灰階設計系統、業界對標 |

**通過標準**：總分 ≥ 98 分，且每個面向 ≥ 90 分

## Technical Approach

### Three Modules Under Test

| 模組 | Repo | 功能 |
|------|------|------|
| woow_line_base | WOOWTECH/woow_line_base | LINE 平台基礎、Flex 工廠、notification hook、Automated Action 範本 |
| woow_line_bridge | WOOWTECH/Woow_odoo_line_liff | LIFF/bridge 層、通用預約卡片、LIFF redirect、Rich Menu |
| woow_odoo_livechat_line | WOOWTECH/woow_odoo_livechat_line | LINE + Odoo LiveChat 雙向整合 |

### Test Strategy

| 層級 | 方法 | 覆蓋範圍 |
|------|------|---------|
| API/RPC | Playwright page.evaluate + fetch | 後台設定、line.user CRUD、config_parameter |
| HTTP 端點 | curl / Playwright request | /liff/redirect、/line/webhook、/liff/home |
| Webhook 模擬 | curl + HMAC 簽名 | follow/unfollow/message events |
| UI 後台 | Playwright browser | 設定頁面、line.user 清單 |
| LIFF 頁面 | Playwright GET + DOM 檢查 | bridge page HTML、redirect 行為 |

### Iteration Loop
```
Round N:
  1. LINE 商業對標 → 場景矩陣 + 規範檢查清單
  2. 流程測試 → 執行全套測試
  3. 錯誤解析 → 分析失敗根因
  4. 程式修復 → 修改代碼 + 部署
  5. 品質審計 → 獨立評分
  → if score < 98%: goto Round N+1
```

## Task Breakdown Preview

1. **LINE 商業對標 + 場景矩陣設計** — 調研 LINE 官方帳號最佳實踐、健身/醫美案例
2. **新增 LINE 整合測試** — Playwright + API specs
3. **第一輪測試執行** — 跑全套
4. **錯誤解析 + 修復** — 分析 + 修 code
5. **第二輪測試 + 迭代修復** — 再測再修
6. **獨立品質審計** — 評分

## Dependencies

- 既有 LINE Bridge E2E 測試 (tests/e2e-line-bridge/)
- LINE Bot Channel 已設定
- LIFF App 已設定 (ID: 2010231694-HISHTNHL)
- Webhook URL 已指向

## Success Criteria (Technical)

- 全套 Playwright 測試（含新增）100% 通過
- 獨立審計評分 ≥ 98%
- 每個面向 ≥ 90%
- 零 Critical bug

## Estimated Effort

- 預計 2-4 輪迭代
- 每輪 4-5 步

## Tasks Created
- [ ] 001.md - LINE 商業對標與場景矩陣設計 (parallel: true) [LINE商業專家]
- [ ] 002.md - 新增 LINE 整合 Playwright 測試 (parallel: false, depends: 001) [場景設計+流程測試]
- [ ] 003.md - 第一輪全套測試執行 (parallel: false, depends: 002) [流程測試專家]
- [ ] 004.md - 錯誤根因分析與修復建議 (parallel: false, depends: 003) [錯誤解析專家]
- [ ] 005.md - 程式碼修復與部署 (parallel: false, depends: 004) [程式碼修復專家]
- [ ] 006.md - 第二輪測試與迭代修復 (parallel: false, depends: 005) [流程測試+修復]
- [ ] 007.md - 獨立品質審計與評分 (parallel: false, depends: 006) [獨立品質審計專家]

Total tasks: 7
Parallel tasks: 1 (001)
Sequential tasks: 6 (002→003→004→005→006→007)
Estimated total effort: 19 hours
