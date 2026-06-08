# 寄品卡商業場景測試矩陣

## 業界對標

| 業態 | 對標系統 | 核心流程 | 我們的對應 |
|------|---------|---------|-----------|
| 美容院套票 | 美業SaaS (美務通等) | 購買套票→分次消費→餘額追蹤→到期提醒 | SO confirm→card→redeem→qty tracking |
| 酒窖寄存 | Wine POS (VinTracker等) | POS購卡→選酒取用→即時餘額→批號追蹤 | POS order→card→scan redeem→lot_id |
| 健身房次卡 | Punchpass/GymMaster | 購買次卡→每次到訪打卡→剩餘次數可見→過期管理 | purchase→card→each visit redeem→portal visible |
| SPA 預付套組 | Dotbooker/Mangomint | 套組購買→自動追蹤→即時更新→到期提醒 | package buy→auto-track→real-time update |

## 場景矩陣

### A. 建卡流程（3 管道）

| ID | 場景 | 管道 | 步驟 | 驗證點 |
|----|------|------|------|--------|
| A1 | 後台銷售建卡 | 後台 SO | 建 SO(trigger+items) → confirm | card created, lines correct, trigger marked |
| A2 | 同客戶重複購買 | 後台 SO | 同客戶再建 SO → confirm | 同一張卡, lines 累積 |
| A3 | 多觸發產品方案 | 後台 SO | 方案有多個 trigger products | 任一 trigger 都能觸發建卡 |
| A4 | 純觸發產品訂單 | 後台 SO | SO 只有 trigger, 無其他品項 | card created but 0 consign lines |
| A5 | 無觸發產品訂單 | 後台 SO | SO 無 trigger product | 不建卡 |
| A6 | POS 購票建卡 | POS RPC | 模擬 POS order 含 trigger | card created (如模組支援) |

### B. 核銷流程

| ID | 場景 | 方式 | 步驟 | 驗證點 |
|----|------|------|------|--------|
| B1 | 後台 wizard 核銷 | wizard | card form → 核銷按鈕 → wizard → confirm | redemption created, qty decreased |
| B2 | 後台直接核銷單 | 表單 | 建 redemption → add lines → action_done | state=done, qty updated |
| B3 | POS 掃碼核銷 | RPC | use_consign_card_code → confirm | qty decreased |
| B4 | POS 按鈕核銷 | RPC | get_partner_consign_cards → select → confirm | redemption created |
| B5 | 部分核銷 | any | 核銷部分數量 | qty_remaining > 0, state=active |
| B6 | 全部核銷 | any | 核銷全部剩餘 | qty_remaining=0, state=depleted |
| B7 | 多品項同時核銷 | any | 一次核銷多個 consign_line | 所有 line qty 都正確更新 |
| B8 | 分多次核銷到完 | any | 多輪核銷同一 line | 最終 depleted, 中間 active |

### C. 後台管理

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| C1 | 直接增加品項 | consign_add_line(new product) | 新 line created |
| C2 | 同品同價累積 | consign_add_line(same prod, same price) | qty_deposited 增加 |
| C3 | 同品不同價 | consign_add_line(same prod, diff price) | 新 line created |
| C4 | 保護欄位寫入 | write qty_deposited directly | ValidationError |
| C5 | 取消品項 | action_cancel on line | state=cancelled, 不可核銷 |
| C6 | 刪除品項拒絕 | unlink on redeemed line | 拒絕 |

### D. Portal 使用者介面

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| D1 | 卡片列表 | /my/consign-cards | 表格顯示, 欄位正確 |
| D2 | 卡片詳情 | /my/consign-cards/{id} | heading, items, summary |
| D3 | 核銷紀錄詳情 | /my/consign-redemptions/{id} | heading, items, total |
| D4 | 安全隔離 | 存取他人卡片 | redirect/403 |
| D5 | 匿名存取 | 未登入存取 | redirect to login |

### E. 異常與邊界

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| E1 | 超額核銷 | redeem qty > remaining | ValidationError |
| E2 | 無效條碼 | POS scan invalid code | not_found response |
| E3 | 非本人卡片 | POS scan with wrong partner | error response |
| E4 | 已用完品項核銷 | redeem on depleted line | 被過濾/拒絕 |
| E5 | 零數量核銷 | redeem qty=0 | 拒絕或無效 |
| E6 | 取消的品項核銷 | redeem on cancelled line | 被過濾/拒絕 |

### F. 通知與追蹤

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| F1 | 建卡 chatter | SO confirm → card created | mail.message on card |
| F2 | 核銷 chatter | redemption done | mail.message 含核銷資訊 |
| F3 | Portal chatter | portal card detail | discussion 區可見 |

## 測試檔案規劃

- `08-multichannel-card-creation.spec.mjs` → A1-A6
- `09-redemption-workflows.spec.mjs` → B1-B8
- `10-backend-management.spec.mjs` → C1-C6
- `11-portal-comprehensive.spec.mjs` → D1-D5
- `12-edge-cases-errors.spec.mjs` → E1-E6
- `13-notifications.spec.mjs` → F1-F3

總計：6 個新 spec, 約 33 個新測試場景
