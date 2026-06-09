---
name: line-integration-qa
description: LINE 三套件全面品質迭代：LIFF登入、Flex推播、LiveChat、Webhook、Rich Menu 至98%+評分
status: active
created: 2026-06-09T00:23:40Z
---

# PRD: line-integration-qa

## Executive Summary

對 Odoo 與 LINE 整合的三個套件（woow_line_base、woow_line_bridge、woow_odoo_livechat_line）進行全面品質迭代。組建 5 角色 Agent 團隊，以真實商業場景為基準（健身房/醫美/按摩預約通知），執行「測試→找錯→分析→修復→再測試」的迭代循環，直到獨立品質審計評分達 98% 以上。

## Problem Statement

LINE 三套件已開發完成並部署至 Mark Studio（馬克健身），但尚未經過以下驗證：
1. **端對端流程**——客戶從 LINE Rich Menu 點擊→LIFF 登入→預約→收到 Flex Message 通知的完整生命週期
2. **LINE 官方最佳實踐對標**——LIFF v2 標準流程、LINE 官方帳號 2.0 推播策略、Rich Menu 設計規範
3. **三套件協作**——base 的通知 hook + bridge 的 LIFF/card + livechat 的即時通訊是否無縫銜接
4. **異常與邊界**——token 過期、webhook 重試、無效 id_token、LIFF 環境外開啟等

## User Stories

### US-1: 客戶透過 LINE Rich Menu 預約
- 作為客戶，我點擊 LINE Rich Menu 的「預約」按鈕
- LIFF 開啟 → bridge page → LIFF login → 取得 id_token → POST 驗證 → session 建立
- 導向預約頁面，完成預約
- **驗收標準**：Rich Menu URL 正確 → LIFF 開啟 → 登入成功 → 預約頁面可用

### US-2: 客戶預約後收到 Flex Message 通知
- 作為客戶，我完成預約後收到 LINE Flex Message
- 通用基本卡片（bridge）：表單名稱、階段變更、通知時間、查看詳情按鈕
- 補充詳情卡片（Automated Action）：預約日期/時間、地點、服務人員、客戶、人數
- **驗收標準**：兩張卡片資訊不重疊、灰階設計、按鈕用 LIFF URL

### US-3: 客戶透過 LINE 諮詢即時客服
- 作為客戶，我在 LINE 聊天室發送訊息
- 訊息透過 webhook 進入 Odoo LiveChat
- 客服在 Odoo 後台回覆，客戶在 LINE 收到回覆
- **驗收標準**：雙向訊息傳遞正確、延遲 < 5 秒

### US-4: LIFF 會員頁面
- 作為客戶，我點擊 Rich Menu 的「會員中心」
- LIFF 開啟 /home 頁面，顯示我的資訊
- **驗收標準**：LIFF 正確開啟、頁面內容正確、未登入時導向登入

### US-5: 管理者後台 LINE 設定
- 作為管理者，我在 Odoo 設定頁面管理 LINE 整合
- 可設定 Channel Token、Secret、LIFF ID
- 可查看 line.user 清單
- **驗收標準**：設定頁面載入正確、欄位可讀寫、computed fields 正確

### US-6: Webhook 事件處理
- LINE 平台發送 follow/unfollow/message 事件
- Odoo webhook 端點正確接收並處理
- **驗收標準**：signature 驗證、事件分派、錯誤不崩潰

### US-7: 異常場景
- LIFF 在外部瀏覽器開啟時正確 redirect
- 無效 id_token 被拒絕
- Token 過期時自動刷新或提示
- Webhook 簽名驗證失敗時回傳 400
- **驗收標準**：每個異常有明確處理

## Functional Requirements

### FR-1: LIFF 登入流程 (woow_line_bridge)
- GET `/liff/redirect` → bridge page → LIFF SDK login
- POST id_token → verify via LINE API → session.authenticate → 302 redirect
- LIFF Endpoint URL: `/liff/redirect`（無 target suffix，用 path concat）
- 所有卡片按鈕用 LIFF URL（`liff.line.me/{id}/{target}`）

### FR-2: Flex Message 推播 (woow_line_base + woow_line_bridge)
- 通用基本卡片：`_build_generic_booking_card()` — 灰階設計系統
- mail.notification.create() hook 自動推送
- `woow_line_base.auto_line_notify` 配置開關
- 灰階設計：CLR_BLACK #1A1A1A、CLR_DARK #333333、status colors 僅用於 4px header strip
- Double notification prevention: `skip_line_notification` context

### FR-3: LINE LiveChat (woow_odoo_livechat_line)
- LINE 訊息 → webhook → Odoo LiveChat channel
- Odoo 回覆 → LINE Messaging API → 客戶
- 雙向即時通訊

### FR-4: Webhook 端點 (woow_line_base)
- POST `/line/webhook` 接收 LINE platform events
- X-Line-Signature 驗證
- Follow/Unfollow/Message 事件處理
- line.user 自動建立/更新

### FR-5: Rich Menu 整合 (woow_line_bridge)
- LIFF path concat: `liff.line.me/{LIFF_ID}/{target}`
- `/liff/member` 頁面已移除，改用 path concat
- Rich Menu 按鈕導向：/home、/appointment/schedule 等

### FR-6: 後台設定 (woow_line_base + woow_line_bridge)
- ir.config_parameter 以 `woow_line_bridge.` 前綴儲存
- Token sync: `woow_line_bridge.messaging_access_token` 必須與 `woow_line_base.messaging_access_token` 一致

## Non-Functional Requirements

- 所有測試在 live Mark Studio Odoo instance 運行
- LINE API 測試需實際 Bot（已設定好）
- LIFF 測試受限於 Playwright（無法模擬 LINE 內建瀏覽器），改用 API/RPC 驗證
- Webhook 測試可用 curl 模擬（需正確簽名）

## Success Criteria

1. **獨立品質審計評分 ≥ 98%**
2. **零 Critical/High bug**
3. **LINE 官方最佳實踐對標通過**
4. **三套件協作無縫**——base hook → bridge card → livechat 雙向

## Constraints & Assumptions

- Mark Studio LINE Bot 和 LIFF 已設定完成
- Webhook URL 已指向 markstudio-odoo.woowtech.io
- LIFF ID: 2010231694-HISHTNHL
- LINE 內建瀏覽器無法用 Playwright 模擬，改用 API 層測試
- 假設 LINE Messaging API 和 LIFF SDK 本身功能正確

## Out of Scope

- LINE Pay 整合
- LINE Beacon
- LINE Mini App
- LINE Messaging API 的效能壓測
- LIFF ShareTargetPicker

## Dependencies

- Odoo 18 (markstudio-odoo.woowtech.io)
- LINE Messaging API (Bot channel)
- LIFF v2 (2010231694-HISHTNHL)
- woow_line_base (GitHub: WOOWTECH/woow_line_base)
- woow_line_bridge (GitHub: WOOWTECH/Woow_odoo_line_liff)
- woow_odoo_livechat_line (GitHub: WOOWTECH/woow_odoo_livechat_line)
- Playwright test framework
- 既有 LINE Bridge E2E 測試 (tests/e2e-line-bridge/)
