---
name: consign-card-qa-iteration
status: backlog
created: 2026-06-08T22:12:29Z
updated: 2026-06-08T22:12:29Z
progress: 0%
prd: .claude/prds/consign-card-qa-iteration.md
github: (will be set on sync)
---

# Epic: consign-card-qa-iteration

## Overview

組建 5 角色 Agent 團隊，對寄品卡模組進行多輪品質迭代。每輪由「商業場景設計→流程測試→錯誤解析→程式修復→獨立審計」五步驟組成，迭代至評分 ≥ 98%。

## Team Architecture (5 Roles)

### Role 1: 商業場景設計專家 (Business Scenario Designer)
- **職責**：從使用者視角設計真實商業場景，對標業界案例
- **輸入**：PRD user stories、業界寄品/套票系統調研
- **輸出**：Playwright test spec（新場景測試）
- **對標範圍**：美容院套票、酒窖寄存、健身房次卡、按摩療程

### Role 2: Odoo 流程測試專家 (Odoo Flow Tester)
- **職責**：執行所有 Playwright 測試，驗證 Odoo 流程正確性
- **輸入**：test spec files
- **輸出**：測試報告（通過/失敗/截圖/log）

### Role 3: 錯誤解析專家 (Error Analyst)
- **職責**：分析失敗測試的根因，判斷是 bug、設計缺陷還是測試問題
- **輸入**：失敗測試 log、截圖、source code
- **輸出**：根因報告 + 修復建議 + 優化方向

### Role 4: 程式碼修復專家 (Code Fixer)
- **職責**：根據錯誤分析修復 Python/JS/XML 程式碼
- **輸入**：根因報告
- **輸出**：修復 commit + 模組升級驗證

### Role 5: 獨立品質審計專家 (QA Auditor)
- **職責**：不參與修復，純粹以商業合理性 + 技術正確性評分
- **輸入**：完整測試報告、修復記錄、Portal/POS 截圖
- **輸出**：評分報告（100 分制，7 大面向各佔分數）

## Scoring Framework (QA Auditor)

| 面向 | 權重 | 評分標準 |
|------|------|---------|
| 建卡流程正確性 | 20% | 三管道建卡（網站/POS/後台）全部成功，觸發產品正確識別 |
| 核銷流程正確性 | 20% | POS 掃碼/按鈕核銷 + 後台 wizard/直接核銷全部正確 |
| 數據完整性 | 15% | qty 計算正確、state 轉換正確、write 保護有效 |
| Portal UI/UX | 15% | 列表/詳情/核銷詳情頁面完整、資料正確、安全隔離 |
| 異常處理 | 10% | 超額核銷拒絕、無效碼錯誤、非本人存取阻擋 |
| 通知與追蹤 | 10% | Email 發送、Chatter 訊息、Portal 通訊紀錄 |
| 商業合理性 | 10% | 對標業界流程、使用者體驗合理、無反直覺操作 |

**通過標準**：總分 ≥ 98 分，且每個面向 ≥ 90 分

## Technical Approach

### Iteration Loop
```
Round N:
  1. 商業場景設計 → 新增/更新 test specs
  2. 流程測試 → 執行 Playwright 全套測試
  3. 錯誤解析 → 分析失敗根因
  4. 程式修復 → 修改代碼 + 部署 + 升級模組
  5. 品質審計 → 獨立評分
  → if score < 98%: goto Round N+1
  → if score >= 98%: DONE
```

### Test Infrastructure
- 現有測試：`tests/consign-e2e/01-07.spec.mjs` (35 tests)
- 新增測試：`tests/consign-e2e/08-business-scenarios.spec.mjs` (多管道購票)
- 新增測試：`tests/consign-e2e/09-edge-cases.spec.mjs` (邊界異常)
- 審計報告：`tests/consign-e2e/audit-report.md`

### Code Repos
- 核心模組：`Woow_odoo_loyalty_card_enhance/addons/woow_loyalty_consign/`
- POS 整合：`Woow_odoo_loyalty_card_enhance/addons/woow_loyalty_consign_pos/`
- Portal：`Woow_odoo_loyalty_card_enhance/addons/woow_mc_consign/`

### Deployment
- K8s namespace: `markstudio-odoo`
- Git push → pod restart → module upgrade → test

## Task Breakdown Preview

1. **商業場景設計 + 業界對標**——設計完整測試場景
2. **新增商業場景測試**——寫 Playwright specs
3. **第一輪測試執行**——跑全套測試
4. **錯誤解析 + 修復**——分析失敗、修 code
5. **第二輪測試 + 修復**——迭代
6. **獨立品質審計**——評分
7. **最終修復 + 審計通過**——達標

## Dependencies

- 現有 35 個測試必須仍然通過
- K8s 集群可部署
- GitHub 可 push

## Success Criteria (Technical)

- Playwright 全套測試（含新增）100% 通過
- 獨立審計評分 ≥ 98%
- 每個面向 ≥ 90%
- 零 Critical bug 遺留

## Estimated Effort

- 預計 3-5 輪迭代
- 每輪：設計(1) + 測試(1) + 分析修復(1-2) + 審計(1) = 4-5 步

## Tasks Created
- [ ] 001.md - 商業場景設計與業界對標 (parallel: true) [商業場景設計專家]
- [ ] 002.md - 新增商業場景 Playwright 測試 (parallel: false, depends: 001) [場景設計+流程測試]
- [ ] 003.md - 第一輪全套測試執行 (parallel: false, depends: 002) [Odoo流程測試專家]
- [ ] 004.md - 錯誤根因分析與修復建議 (parallel: false, depends: 003) [錯誤解析專家]
- [ ] 005.md - 程式碼修復與部署 (parallel: false, depends: 004) [程式碼修復專家]
- [ ] 006.md - 第二輪測試與迭代修復 (parallel: false, depends: 005) [流程測試+修復]
- [ ] 007.md - 獨立品質審計與評分 (parallel: false, depends: 006) [獨立品質審計專家]

Total tasks: 7
Parallel tasks: 1 (001 can start independently)
Sequential tasks: 6 (002→003→004→005→006→007 chain)
Estimated total effort: 19 hours
