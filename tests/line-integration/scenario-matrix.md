# LINE 整合商業場景測試矩陣

## 業界對標

| 業態 | 對標方案 | 核心 LINE 功能 | 我們的對應 |
|------|---------|--------------|-----------|
| 健身房 (17FIT/BookFast) | LINE 預約+會員+課表 | Rich Menu→LIFF 預約、推播提醒、會員綁定 | bridge LIFF redirect + Flex 推播 |
| 醫美診所 | LINE 掛號+回診提醒 | Rich Menu→預約、Flex 確認/提醒卡片 | bridge booking cards + webhook |
| 按摩/伸展 (Mark Studio) | LINE 預約+寄品卡通知 | Rich Menu→LIFF 會員、Flex 預約通知 | bridge + base notification hook |
| LINE 官方帳號 2.0 | 以量計價推播策略 | Narrowcast 分眾、自動回覆、標籤管理 | base push/multicast/broadcast |

Sources:
- [LINE OA 2.0 健身業因應](https://bookfastpos.com/gym-management/articles-line-official-account-volume-based-pricing-gym-adaption/)
- [LINE 官方帳號 111 件事](https://blog.cresclab.com/zh-tw/line-official-account-line-oa-101-things-to-know)
- [17FIT LINE 預約外掛](https://tw.line-oa-marketplace.com/list/17fit-extension/)

---

## 場景矩陣

### A. LIFF 登入流程 (woow_line_bridge)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| A1 | LIFF redirect 端點可存取 | GET /liff/redirect | 回傳 200，HTML 含 LIFF SDK script |
| A2 | LIFF redirect 帶 target | GET /liff/redirect/book | HTML 含正確 target 值 |
| A3 | LIFF redirect 帶 booking ID | GET /liff/redirect/booking/1 | HTML 含 booking/1 path |
| A4 | LIFF API /bind 端點 | POST /api/line/bind (無 token) | 回傳 401/error |
| A5 | LIFF API /me 端點 | POST /api/line/me (無 token) | 回傳 401/error |
| A6 | LIFF API /notification/toggle | POST /api/line/notification/toggle (無 token) | 回傳 401/error |
| A7 | LIFF debug 頁面 | GET /liff/debug | 回傳 200，含 LIFF SDK 診斷 |
| A8 | Clear session 端點 | GET /liff/clear-session | redirect 正確 |

### B. Flex Message 推播 (woow_line_base + bridge)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| B1 | 通用通知 Flex 結構 | 呼叫 line.flex.factory.build_notification() | 回傳正確 bubble JSON |
| B2 | 通知 Flex 灰階設計 | 檢查 build_notification 輸出 | 只有 header strip 用 status color |
| B3 | 預約確認 Flex | 呼叫 line.flex.template.build_booking_confirmed() | 含表單名稱、狀態、按鈕 |
| B4 | 預約取消 Flex | 呼叫 build_booking_cancelled() | 含取消原因、重新預約按鈕 |
| B5 | 預約提醒 Flex | 呼叫 build_booking_reminder() | 含時間、地點、導航按鈕 |
| B6 | 新聞卡片 Flex | 呼叫 build_news_card() | 含標題、摘要、hero image |
| B7 | 歡迎 Flex | 呼叫 build_welcome() | 含顯示名稱 |
| B8 | 通用預約卡片 | 呼叫 _build_generic_booking_card() | 含表單名稱、階段變更、查看按鈕 |
| B9 | Flex 按鈕用 LIFF URL | 檢查所有按鈕 URI | 用 liff.line.me/{id}/xxx 格式 |
| B10 | auto_line_notify 開關 | 設定 config=True/False | True 時自動推播，False 時靜默 |
| B11 | skip_line_notification context | mail.notification 帶 context | 不觸發 LINE 推播 |

### C. Webhook 接收 (woow_line_bridge)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| C1 | Webhook 端點可存取 | POST /line/webhook | 回傳 200 |
| C2 | 無效簽名被拒絕 | POST 帶錯誤 X-Line-Signature | 回傳 403/error |
| C3 | Follow 事件 | 模擬 follow webhook | line.user created, is_follower=True |
| C4 | Unfollow 事件 | 模擬 unfollow webhook | is_follower=False, is_blocked=True |
| C5 | Text 訊息事件 | 模擬 message webhook | event log created |
| C6 | Postback 事件 | 模擬 postback webhook | 正確路由處理 |
| C7 | Event logging | 任何事件 | line.event.log 記錄完整 |

### D. Rich Menu 整合 (woow_line_bridge)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| D1 | Rich Menu model CRUD | RPC create/read/write line.richmenu | 欄位正確 |
| D2 | Rich Menu area 定義 | 建立 richmenu.area | action_type/coordinates 正確 |
| D3 | Rich Menu alias | 建立 richmenu.alias | alias_id unique |
| D4 | Rich Menu build data | _build_menu_data() | JSON 結構符合 LINE 規格 |
| D5 | LIFF URL path concat | 檢查 button URI | liff.line.me/{id}/{target} 格式 |

### E. LiveChat 串接 (woow_odoo_livechat_line)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| E1 | LiveChat channel LINE 設定 | RPC read im_livechat.channel | line_enabled, line_channel_id 欄位存在 |
| E2 | LiveChat webhook 端點 | POST /line/webhook/{channel_id} | 回傳 200 |
| E3 | LiveChat 無效 channel | POST /line/webhook/99999 | 回傳 {}（不崩潰） |
| E4 | Guest 自動建立 | 模擬 LINE message → webhook | mail.guest created |
| E5 | Discuss channel 建立 | 模擬 LINE message | discuss.channel with line_user_id |
| E6 | 訊息類型處理 | text/image/sticker/location | 正確轉換為 message body |
| E7 | 回覆 LINE 用戶 | Odoo discuss → LINE | _notify_line_user() 呼叫正確 |

### F. 後台設定與 line.user 管理 (base + bridge)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| F1 | 設定頁面載入 | goto /odoo/settings | LINE 區塊可見 |
| F2 | Config parameters | RPC read ir.config_parameter | 所有 LINE keys 存在 |
| F3 | line.user CRUD | RPC create/read line.user | 欄位正確 |
| F4 | line.user 綁定 partner | bind_partner() | partner_id 設定正確 |
| F5 | line.user 解綁 | unbind() | partner_id=False |
| F6 | Push log 記錄 | RPC read line.push.log | 推播記錄存在 |
| F7 | Event log 記錄 | RPC read line.event.log | 事件記錄存在 |

### G. LIFF 頁面 (woow_line_bridge)

| ID | 場景 | 步驟 | 驗證點 |
|----|------|------|--------|
| G1 | News 頁面 | GET /liff/news | 回傳 200，含已發布新聞 |
| G2 | Locations 頁面 | GET /liff/locations | 回傳 200，含地址/電話/地圖 |
| G3 | News 詳情 | GET /liff/news?article_id=X | 含文章標題和內容 |

### H. 商業合理性（LINE 官方最佳實踐）

| ID | 場景 | 檢查項 | 驗證方式 |
|----|------|--------|---------|
| H1 | Rich Menu 設計規範 | 尺寸 2500×1686 / 2500×843 | line.richmenu.size 選項正確 |
| H2 | Flex Message 規格 | bubble 結構符合 LINE spec | JSON schema 檢查 |
| H3 | 推播配額意識 | push 過濾 blocked/unfollowed | line.api.service.push() 過濾邏輯 |
| H4 | Webhook 安全 | HMAC-SHA256 驗證 | signature 驗證實作正確 |
| H5 | LIFF URL 規範 | path concat 格式 | liff.line.me/{id}/{target} |
| H6 | Double notification 防護 | skip_line_notification | context 傳遞正確 |

---

## 測試檔案規劃

| Spec 檔案 | 場景 | 測試數 |
|-----------|------|--------|
| `14-liff-endpoints.spec.mjs` | A1-A8 | 8 |
| `15-flex-message.spec.mjs` | B1-B11 | 11 |
| `16-webhook.spec.mjs` | C1-C7 | 7 |
| `17-richmenu.spec.mjs` | D1-D5 | 5 |
| `18-livechat.spec.mjs` | E1-E7 | 7 |
| `19-backend-settings.spec.mjs` | F1-F7 | 7 |
| `20-liff-pages.spec.mjs` | G1-G3 | 3 |
| `21-line-best-practices.spec.mjs` | H1-H6 | 6 |

**總計：8 個新 spec, 54 個測試場景**
