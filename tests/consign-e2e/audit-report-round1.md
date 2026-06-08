# 寄品卡模組品質審計報告 — 第一輪

**審計日期**: 2026-06-09
**審計角色**: 獨立品質審計專家（不參與修復）
**測試結果**: 71/71 Playwright E2E 測試通過

---

## 評分總表

| 面向 | 權重 | 得分 | 扣分原因 |
|------|------|------|---------|
| 建卡流程正確性 | 20% | 17/20 | -3: 無 partner_id 防護，可能建出無主卡片 |
| 核銷流程正確性 | 20% | 16/20 | -4: 核銷明細無跨卡驗證，可從他人卡片扣除品項 |
| 數據完整性 | 15% | 13/15 | -2: qty_remaining 可為負值；累積無行鎖 |
| Portal UI/UX | 15% | 14/15 | -1: 封存卡片可透過直接 URL 存取；無分頁 |
| 異常處理 | 10% | 9/10 | -1: POS 無客戶時可繞過擁有者檢查 |
| 通知與追蹤 | 10% | 9/10 | -1: 累積購買也發「建卡」通知，語意混淆 |
| 商業合理性 | 10% | 9/10 | -1: 已部分核銷品項可取消，造成資料矛盾 |

**總分: 87/100**

---

## 詳細扣分說明

### 建卡流程 (17/20)

**-3 分: sale_order.py 無 partner_id 防護**
- `_action_create_consign_card()` 中 `self.partner_id.id` 未驗證是否存在
- 若 SO 無客戶（walk-in 場景），卡片建立 `partner_id=False`
- 後續搜尋 `partner_id=False` 會匹配所有無主卡片，造成跨客戶資料洩漏
- 業界對標：所有套票系統都要求客戶身份才能建卡

### 核銷流程 (16/20)

**-4 分: 核銷明細無跨卡驗證（Issue 4.5 + Cross-3）**
- `action_done()` 驗證 qty 和 state，但不驗證 `consign_line_id.card_id == redemption.card_id`
- POS `confirm_consign_redemptions` 直接信任前端傳入的 `consign_line_id`
- 惡意或 bug 的前端可從 Card A 的核銷單扣除 Card B 的品項
- 這是最嚴重的商業邏輯漏洞

### 數據完整性 (13/15)

**-1 分: qty_remaining 可為負值**
- `qty_remaining = qty_deposited - qty_redeemed` 無 `max(0, ...)` 保護
- 雖有 FOR UPDATE 鎖，但極端並發下仍可能出現負值
- Portal 會顯示負餘額給客戶

**-1 分: consign_add_line 累積無行鎖**
- 與核銷的 `SELECT FOR UPDATE` 不對稱
- 兩個訂單同時確認同客戶同產品時存在 TOCTOU 風險

### Portal UI/UX (14/15)

**-1 分: 封存卡片可存取 + 無分頁**
- `/my/consign-cards/{id}` 不檢查 `active=True`
- 卡片列表無分頁實作（路由接受 page 參數但未使用）

### 異常處理 (9/10)

**-1 分: POS 無客戶時繞過擁有者檢查**
- `use_consign_card_code` 中 `partner_id=False` 時跳過擁有者驗證
- 任何條碼都可被查詢

### 通知與追蹤 (9/10)

**-1 分: 累積也發建卡通知**
- 客戶第二次購買觸發 `_send_creation_communication`
- 收到「新卡片」通知但卡片不是新的

### 商業合理性 (9/10)

**-1 分: 已部分核銷品項可取消**
- `action_cancel` 不檢查 `qty_redeemed > 0`
- 取消後品項狀態為 `cancelled`，但已完成的核銷紀錄仍參照此品項
- 業界做法：已使用品項不可取消，只可退款

---

## 通過標準檢查

| 標準 | 要求 | 實際 | 狀態 |
|------|------|------|------|
| 總分 | ≥ 98 | 87 | ❌ 未達標 |
| 建卡流程 | ≥ 90% | 85% | ❌ 未達標 |
| 核銷流程 | ≥ 90% | 80% | ❌ 未達標 |
| 數據完整性 | ≥ 90% | 87% | ❌ 未達標 |
| Portal UI/UX | ≥ 90% | 93% | ✅ 達標 |
| 異常處理 | ≥ 90% | 90% | ✅ 達標 |
| 通知與追蹤 | ≥ 90% | 90% | ✅ 達標 |
| 商業合理性 | ≥ 90% | 90% | ✅ 達標 |

---

## 結論

**第一輪評分 87/100，未達 98 分標準。需進行第二輪修復迭代。**

### 優先修復項（可挽回最多分數）

1. **核銷跨卡驗證** (+4 分) — 在 `action_done` 加入 `consign_line_id.card_id == self.card_id` 檢查
2. **建卡 partner_id 防護** (+3 分) — 在 `_action_create_consign_card` 加入 `if not self.partner_id: return`
3. **qty_remaining 下限保護** (+1 分) — 使用 `max(0, deposited - redeemed)`
4. **POS 擁有者檢查** (+1 分) — `partner_id` 為 False 時回傳 error
5. **累積通知語意** (+1 分) — 區分「新卡」和「品項更新」通知
6. **取消防護** (+1 分) — 已有核銷的品項不可取消

修復以上 6 項可得 **87 + 11 = 98 分**，達標。
