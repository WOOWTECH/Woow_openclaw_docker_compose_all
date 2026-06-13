---
name: product-category-unification
status: in-progress
created: 2026-06-13T04:08:24Z
updated: 2026-06-13T04:08:24Z
progress: 0%
prd: .claude/prds/product-category-unification.md
github: (will be set on sync)
---

# Epic: product-category-unification

## Overview

統一禪香不二 Inzense Odoo 18 的產品分類架構，新增周邊商品/贈品類別與產品，清理歷史殘留，確保三端（internal/POS/eCommerce）完全一致。

## Architecture Decisions

1. **分類結構**：主類別=系列（18個），次類別=產品型態（6個），但周邊商品系列不需要長線香/迷你香/拜拜用香/盤香的次類別
2. **新系列的次類別策略**：手串/念珠/精油/原木/原木筆/檀香扇/香器/贈品系列直接作為頂層分類，不建立次類別
3. **條碼策略**：barcode = default_code = CSV 貨號（如 MBB00108）
4. **原木系列定價**：以克計價的產品 list_price=0，備註在 description_sale

## Technical Approach

### Data Operations (XML-RPC)
- 所有操作透過 `xmlrpc.client` 連接 `http://localhost:8069`
- 冪等設計：先 search 確認不存在再 create
- 批次操作需逐一處理以避免 constraint 錯誤

### Three-System Sync
- product.category（內部）：直接建立頂層系列
- pos.category（POS）：同結構建立
- product.public.category（電商）：同結構建立

### Product Creation
- product.template → 自動建立 product.product variant
- 設定 barcode、default_code 在 product.product 上
- 建立 product.barcode QR Code 記錄

## Implementation Strategy

分 6 個任務，3 個可並行：

```
Phase 1 (並行):
  Task 1: 清理殘留分類
  Task 2: 新增系列分類（三端同步）

Phase 2 (依賴 Phase 1):
  Task 3: 建立新產品（周邊商品 + 贈品）

Phase 3 (依賴 Task 3):
  Task 4: 產品屬性完整性修復（barcode/QR/storable）

Phase 4 (並行):
  Task 5: 清理空次類別 + 優化現有分類
  Task 6: 全面驗證與評分
```

## Task Breakdown Preview

1. 清理殘留分類 — 移除 demo 分類、POS _OLD_、信義/台中封存倉庫相關
2. 新增 8 個系列分類 — 三端同步建立
3. 建立 49 個新產品 — 周邊商品 + 贈品
4. 產品屬性補齊 — barcode/QR/storable/price
5. 分類優化 — 移除空次類別、確保一致性
6. 全面驗證 — 資料完整性檢查、POS 掃碼測試、評分

## Dependencies

- Odoo pod 運行中 + kubectl port-forward 8069
- CSV 資料已讀取分析完成
- barcode_scanner_label 模組已安裝

## Success Criteria (Technical)

- 產品總數 = CSV 扣除停售後的總數
- 三端分類 hash 一致
- `product.product` search_count where barcode=False AND active=True → 0
- `product.product` search_count where default_code=False AND active=True → 0
- find_by_barcode_with_info 對所有新產品回傳正確結果

## Estimated Effort

- Total: ~4 hours
- Parallel tasks: 4/6
- Sequential bottleneck: Task 3 (最多產品建立)
