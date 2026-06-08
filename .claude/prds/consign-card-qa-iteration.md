---
name: consign-card-qa-iteration
description: 寄品卡模組全面品質迭代：多角色團隊測試→修復→再測試循環至98%+評分
status: active
created: 2026-06-08T22:11:33Z
---

# PRD: consign-card-qa-iteration

## Executive Summary

對寄品卡模組（woow_loyalty_consign + woow_loyalty_consign_pos + woow_mc_consign）進行全面品質迭代。組建 5 角色 Agent 團隊，以真實商業場景為基準，執行「測試→找錯→分析→修復→再測試」的迭代循環，直到獨立品質審計評分達 98% 以上。

## Problem Statement

寄品卡模組已完成開發且 35 個 Playwright E2E 測試通過，但尚未經過以下驗證：
1. **真實商業場景端到端**——客戶從各管道（網站、POS、後台銷售）購票到卡片用完的完整生命週期
2. **業界流程對標**——與市面上同類寄品/套票系統的商業流程比較，確保流程合理性
3. **邊界與異常**——並發核銷、部分退款、客戶重複購買、跨方案觸發等邊界條件
4. **前端 UI/UX**——Portal 頁面、POS 彈窗、後台表單的使用者體驗完整性

## User Stories

### US-1: 客戶從網站購買套票
- 作為客戶，我在網站商店購買「按摩伸展套票服務」
- 確認付款後，系統自動建立寄品卡，email 通知我
- 我可以在 Portal 的 /my/consign-cards 看到我的卡片和品項餘額
- **驗收標準**：SO confirmed → card created → email sent → portal visible

### US-2: 客戶從 POS 購買套票
- 作為客戶，我在門市 POS 購買套票
- 收銀員掃描套票產品，結帳確認後，系統建立寄品卡
- **驗收標準**：POS order → card created → lines correct

### US-3: 後台銷售建立寄品卡
- 作為業務人員，我在後台建立銷售訂單（含觸發產品+服務項目）
- 確認訂單後自動建立寄品卡
- **驗收標準**：SO with trigger+items → confirm → card + lines created

### US-4: POS 掃碼核銷
- 作為店員，客戶到店消費，我在 POS 掃描客戶寄品卡條碼
- 系統顯示可用品項，我選擇核銷數量，確認後扣除
- **驗收標準**：barcode scan → popup → select qty → order confirm → qty decreased

### US-5: 後台核銷（wizard）
- 作為管理者，我在後台打開寄品卡，點擊「核銷」按鈕
- wizard 顯示品項清單，勾選並輸入數量，確認後扣除
- **驗收標準**：card form → wizard → select lines → confirm → redemption created

### US-6: 後台直接增加品項
- 作為管理者，我需要手動補品項到客戶的寄品卡（例如補償）
- 使用 consign_add_line 或表單內聯新增
- **驗收標準**：add_line → line created/accumulated → totals updated

### US-7: Portal 查看卡片與核銷紀錄
- 作為客戶，我在會員中心查看寄品卡餘額、已用量、核銷歷史
- 點擊核銷紀錄可看到詳細明細
- **驗收標準**：list page → detail page → redemption detail → all data correct

### US-8: 異常場景
- 超額核銷被拒絕
- 無效條碼返回錯誤
- 非本人卡片無法存取（Portal 安全隔離）
- 品項全部用完後狀態變 depleted
- **驗收標準**：每個異常場景都有明確錯誤訊息或正確狀態轉換

### US-9: Chatter 通知
- 寄品卡建立、核銷完成時在卡片 chatter 產生訊息
- Portal 使用者可在詳情頁看到通訊紀錄
- **驗收標準**：mail.message records created → visible in UI

## Functional Requirements

### FR-1: 多管道建卡
- 網站購買（website_sale 流程）→ SO confirm → 建卡
- POS 購買 → POS order sync → 建卡（如適用）
- 後台銷售訂單 → SO confirm → 建卡

### FR-2: 核銷流程
- POS 掃碼核銷（use_consign_card_code RPC）
- POS 按鈕核銷（get_partner_consign_cards → ConsignCardPopup）
- 後台 wizard 核銷（action_open_redeem_wizard）
- 後台直接建立核銷單

### FR-3: 數據完整性
- consign_add_line 累積同品同價（consign_accumulate context）
- write 保護核心欄位（qty_deposited, product_id, unit_price）
- 核銷時 SQL FOR UPDATE 鎖防止並發
- qty_remaining = qty_deposited - sum(redeemed)
- state 自動轉換（active → depleted when qty_remaining == 0）

### FR-4: Portal 介面
- /my/consign-cards（卡片列表）
- /my/consign-cards/{id}（卡片詳情 + 品項 + 核銷紀錄）
- /my/consign-redemptions/{id}（核銷詳情）
- Portal record rules 確保資料隔離

### FR-5: 通知與追蹤
- Email 通知（mail_template_consign_card）
- Chatter 訊息（核銷完成時 post_message）

## Non-Functional Requirements

- 所有測試必須在 live Odoo instance 上運行（markstudio-odoo.woowtech.io）
- 測試資料用 E2E- 前綴，測試後清理
- 每個迭代必須有獨立評分報告
- 評分標準需對標業界同類產品（美容院套票、酒窖寄存、健身房次卡）

## Success Criteria

1. **獨立品質審計評分 ≥ 98%**
2. **零 Critical/High bug**——所有影響核心流程的問題已修復
3. **商業流程合理性**——經業界對標確認流程完整且合理
4. **全管道覆蓋**——網站、POS、後台銷售三種建卡管道都已測試
5. **所有 Playwright 測試通過**——含新增的場景測試

## Constraints & Assumptions

- 運行在 Mark Studio 的 live Odoo 18 instance
- POS 測試限於 RPC 端點（不啟動實際 POS session）
- 網站購買流程可通過 RPC 模擬（create SO + confirm）
- 假設 Odoo 基礎模組（loyalty, sale_loyalty, pos_loyalty）功能正確

## Out of Scope

- Odoo 基礎 loyalty 模組的 bug 修復
- 效能壓力測試（並發 1000+ 用戶）
- 多語系翻譯完整性
- 移動端 App（僅測手機瀏覽器 Portal）

## Dependencies

- Odoo 18 (markstudio-odoo.woowtech.io)
- Playwright test framework (已安裝)
- 現有 35 個 E2E 測試（tests/consign-e2e/）
- GitHub: WOOWTECH/Woow_odoo_loyalty_card_enhance
