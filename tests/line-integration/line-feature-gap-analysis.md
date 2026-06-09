# LINE 整合功能差距分析 + 重複檢查

## 一、LINE 官方 API 全功能 vs 我們的實作

### Messaging API

| LINE 官方功能 | 我們有嗎 | 模組 | 備註 |
|-------------|---------|------|------|
| Push Message | ✅ | base | push_message() |
| Multicast (≤500) | ✅ | base | multicast() |
| Broadcast | ✅ | base | broadcast() |
| Reply Message | ✅ | base | reply() |
| Narrowcast (受眾分群推播) | ❌ | - | LINE 官方支援按年齡/性別/區域推播 |
| Text Message | ✅ | base | build_text_message() |
| Image Message | ✅ | base | build_image_message() |
| Video Message | ✅ | base | build_video_message() |
| Audio Message | ✅ | base | build_audio_message() |
| File Message | ✅ | base | build_file_message() |
| Flex Message | ✅ | bridge | line.flex.factory + line.flex.template |
| Location Message | ❌ | - | LINE 有原生 location message type |
| Sticker Message | ❌ | - | LINE 有原生 sticker message type |
| Template Message (Buttons/Confirm/Carousel) | ❌ | - | 用 Flex 取代，合理 |
| Imagemap Message | ❌ | - | 較少用，可忽略 |
| Get Message Content | ✅ | base | get_content() |
| Message Statistics | ❌ | - | 推播數據統計 API |
| Quota API | ❌ | - | 查詢月推播配額/已用量 |
| Loading Animation | ❌ | - | 顯示「正在輸入」動畫 |

### User/Profile API

| LINE 官方功能 | 我們有嗎 | 模組 | 備註 |
|-------------|---------|------|------|
| Get Profile | ✅ | base | get_profile() |
| Get Group Member Profile | ❌ | - | 群組成員資料（不需要，B2C 場景） |
| Get Room Member Profile | ❌ | - | 聊天室成員（不需要） |
| Get Followers IDs | ❌ | - | 取得所有好友 UID 清單 |

### Rich Menu API

| LINE 官方功能 | 我們有嗎 | 模組 | 備註 |
|-------------|---------|------|------|
| Create Rich Menu | ✅ | base+bridge | richmenu_create() + line.richmenu |
| Upload Image | ✅ | base+bridge | richmenu_upload_image() |
| Set Default | ✅ | base+bridge | richmenu_set_default() |
| Clear Default | ✅ | base | richmenu_clear_default() |
| Link to User | ✅ | base | richmenu_link_to_user() |
| Unlink from User | ✅ | base | richmenu_unlink_from_user() |
| Batch Link (500) | ✅ | base | richmenu_link_to_users() |
| Get User Menu | ✅ | base | richmenu_get_user_menu() |
| Delete Rich Menu | ✅ | base+bridge | richmenu_delete() |
| Rich Menu Alias (Tab) | ✅ | base+bridge | richmenu_create_alias() + line.richmenu.alias |
| Rich Menu Batch Control | ❌ | - | 批次替換/批次解除 Rich Menu |
| Validate Rich Menu | ❌ | - | 驗證 Rich Menu JSON 格式 |

### Webhook Events

| LINE 官方事件 | 我們處理嗎 | 模組 | 備註 |
|-------------|-----------|------|------|
| Follow | ✅ | bridge | _handle_follow() |
| Unfollow | ✅ | bridge | _handle_unfollow() |
| Message (text) | ✅ | bridge | _handle_message() |
| Message (image/video/audio) | ❌ | - | 僅處理 text，其他 media 未處理 |
| Postback | ✅ | bridge | _handle_postback() |
| Join (群組) | ❌ | - | 加入群組事件（B2C 不需要） |
| Leave (群組) | ❌ | - | 離開群組事件 |
| MemberJoined | ❌ | - | 成員加入（event_type 已定義但未處理） |
| MemberLeft | ❌ | - | 成員離開 |
| Beacon | ❌ | - | OUT OF SCOPE |
| AccountLink | ❌ | - | 帳號連動事件（用 LIFF 代替） |
| Things (IoT) | ❌ | - | OUT OF SCOPE |
| Unsend | ❌ | - | 使用者收回訊息事件 |
| VideoPlayComplete | ❌ | - | 影片播放完成 |

### LIFF v2 API

| LIFF 功能 | 我們用了嗎 | 模組 | 備註 |
|----------|-----------|------|------|
| liff.init() | ✅ | bridge | liff_helper.js |
| liff.login() | ✅ | bridge | bridge page 自動登入 |
| liff.getProfile() | ✅ | bridge | liff_helper.js |
| liff.getIDToken() | ✅ | bridge | bridge page 取得 token |
| liff.getAccessToken() | ✅ | bridge | 備用驗證方式 |
| liff.isLoggedIn() | ✅ | bridge | liff_helper.js |
| liff.isInClient() | ✅ | bridge | WoowLiff.isInLine() |
| liff.closeWindow() | ✅ | bridge | WoowLiff.close() |
| liff.sendMessages() | ❌ | - | 以使用者名義發送訊息到聊天室 |
| liff.shareTargetPicker() | ❌ | - | OUT OF SCOPE |
| liff.scanCodeV2() | ❌ | - | 掃碼功能（可用於核銷） |
| liff.requestFriendship() | ❌ | - | 提示加好友（v2.28.0 新增） |
| liff.permission.* | ❌ | - | 權限管理 API |
| liff.permanentLink.* | ❌ | - | 永久連結管理 |

### LINE Login

| 功能 | 我們有嗎 | 模組 | 備註 |
|------|---------|------|------|
| ID Token 驗證 | ✅ | base | verify_id_token() |
| Access Token 驗證 | ✅ | base | verify_access_token() |
| Channel Access Token (OAuth) | ✅ | base | get_access_token() |
| Token 快取 + 自動刷新 | ✅ | base | _TOKEN_CACHE |

---

## 二、模組間重複與架構問題

### 已知重複（MEMORY 記錄）

| 問題 | 嚴重度 | 說明 |
|------|--------|------|
| `line.user` 雙重 `_name` 定義 | 🔴 HIGH | base 和 bridge 都用 `_name = 'line.user'`（不是 `_inherit`），模組升級可能失敗 |

### 設定 Key 重疊

| Key | base 設定 | bridge 設定 | 問題 |
|-----|----------|------------|------|
| `woow_line_base.messaging_access_token` | ✅ base 設定頁 | ❌ | 正常，base 負責 |
| `woow_line_base.auto_line_notify` | ❌ | ✅ bridge 設定頁 | 跨模組：base 的 key 在 bridge 設定頁面管理 |
| `woow_line_base.admin_line_user_id` | ❌ | ✅ bridge 設定頁 | 跨模組：同上 |

### Token Sync 問題

- `woow_line_bridge.messaging_access_token` 必須與 `woow_line_base.messaging_access_token` 一致
- 但 MEMORY 只提到需要 sync，未見自動同步機制
- 需驗證是否有兩個獨立 token 設定還是共用同一個

### Controller 職責分離

| Controller | 模組 | 問題 |
|-----------|------|------|
| webhook.py | bridge | ✅ 只在 bridge，但依賴 base 的 signature 驗證 |
| liff_redirect.py | bridge | ✅ 只在 bridge |
| liff_pages.py | bridge | ✅ 只在 bridge |
| liff_api.py | bridge | ✅ 只在 bridge |
| (無 controller) | base | ✅ base 是純 API service |
| (livechat) | livechat | ❓ 未確認（模組未 clone） |

---

## 三、業界對標差距

### vs 夯客 HOTCAKE (美業)

| 功能 | 夯客 | 我們 | 差距 |
|------|------|------|------|
| LINE 預約通知 | ✅ | ✅ | 無 |
| LINE 推播行銷 | ✅ 分眾推播 | ⚠️ 僅全體廣播 | 缺 Narrowcast |
| LINE 會員卡 | ✅ | ⚠️ LIFF Portal | 不同實作方式 |
| 課程提醒 | ✅ | ✅ 24h+2h | 無 |
| POS 整合 | ✅ | ✅ 寄品卡 POS | 無 |

### vs 17FIT (健身房)

| 功能 | 17FIT | 我們 | 差距 |
|------|-------|------|------|
| LINE 綁定 CRM | ✅ | ✅ partner 綁定 | 無 |
| 課表查詢 | ✅ LINE 內 | ✅ LIFF /appointment | 無 |
| 簽到打卡 | ✅ QR Code | ❌ | 缺 liff.scanCodeV2() |
| 套票管理 | ✅ | ✅ 寄品卡 | 無 |
| 即時客服 | ❌ | ✅ LiveChat | 我們更好 |

### vs 醫美診所 LINE

| 功能 | 診所方案 | 我們 | 差距 |
|------|---------|------|------|
| 線上掛號 | ✅ | ✅ LIFF 預約 | 無 |
| 回診提醒 | ✅ | ✅ Flex 推播 | 無 |
| 療程紀錄查詢 | ✅ | ✅ Portal | 無 |
| 衛教訊息推播 | ✅ | ✅ line.news | 無 |
| 線上付款 | ✅ LINE Pay | ❌ | OUT OF SCOPE |

---

## 四、優先修復/優化建議

### 必須修復（影響正常運作）

1. **`line.user` _name 重複定義** — bridge 應改用 `_inherit` 而非 `_name`
2. **Token sync 機制驗證** — 確認兩模組不會各自存不同 token
3. **LiveChat 模組 clone 並測試** — 目前不在本地

### 建議優化（提升商業價值）

4. **Webhook media 處理** — 圖片/影片/音訊訊息目前被忽略
5. **liff.scanCodeV2()** — 可用於 POS 核銷替代方案（掃碼打卡）
6. **Narrowcast 分眾推播** — 業界標配，按標籤/屬性推播

### 可接受現狀

- Template Message → 用 Flex 取代 ✅
- Sticker/Location Message → 非核心 ✅
- 群組相關 API → B2C 不需要 ✅
- Beacon/Things → OUT OF SCOPE ✅

---

Sources:
- [LINE Messaging API Reference](https://developers.line.biz/en/reference/messaging-api/)
- [LIFF v2 API Reference](https://developers.line.biz/en/reference/liff/)
- [LINE 美業預約神器 HOTCAKE](https://tw.line-oa-marketplace.com/list/hotcake-linemodule/)
- [17FIT LINE 預約外掛](https://tw.line-oa-marketplace.com/list/17fit-extension/)
- [LINE 醫療業應用](https://tw.linebiz.com/column/healthcare-oa/)
- [LINE 預約系統推薦 2026](https://autodev-ai.com/blog/line-bot-booking-system.html)
