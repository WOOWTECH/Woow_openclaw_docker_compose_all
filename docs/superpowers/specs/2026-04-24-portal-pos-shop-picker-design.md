# Portal POS 營業點選擇頁面設計

**Date:** 2026-04-24
**Module:** `pos_self_order_enhancement`
**Scope:** Portal user 的 POS 入口重新設計

---

## 目標

將 portal user 的 POS 入口從「銷售點 + 廚房顯示螢幕」兩張獨立卡片，整合為單一「銷售點」入口，點擊後顯示營業點列表頁，每張卡片可進入 POS 或 KDS。

## 現況

- Portal `/my` 顯示兩張卡片：「銷售點」和「廚房顯示螢幕」
- 點擊「銷售點」→ `/my/pos` → 只有 1 個營業點時自動跳轉 POS UI；多個才顯示 picker
- 點擊「廚房顯示螢幕」→ `/my/kds` → 類似邏輯
- Picker 頁面設計簡陋，只有名稱和連結

## 設計

### 1. Portal 首頁 (`/my`) 變更

- **移除** `portal_my_home_kds` template（廚房顯示螢幕卡片）
- **保留** `portal_my_home_pos`（銷售點卡片），template body 不修改 — 現有的 `url` 已設為 `'/my/pos'`，無需調整
- 「不再自動跳轉」的行為變更在 controller 層處理（見 Section 3）

### 2. `/my/pos` 營業點列表頁

**框架：** `portal.portal_layout`（保留網站 header/footer）

**標題區：**
- 標題：「銷售點」
- 副標題：「查看並管理您負責的營業點」（11 字，中性，適用零售/餐飲/服務業）
- 右上角「← 返回」按鈕回到 `/my`

**卡片列表：** 顯示 `partner.portal_pos_config_ids` 中 `active=True` 的 POS config

每張卡片包含：

| 元素 | 位置 | 說明 |
|------|------|------|
| 營業點名稱 | 左側 | `pos.config.name` |
| 狀態標籤 | 名稱右側 | `has_active_session` → 綠色「營業中」/ 灰色「已關閉」 |
| 操作按鈕 | 卡片底部 | 營業中 → 「繼續銷售」/ 已關閉 → 「開啟銷售」 |
| KDS 圖示按鈕 | 卡片右上角 | 用 `t-if="config.kds_enabled and config.kds_access_token"` 條件渲染（不是 CSS 隱藏），點擊進入 KDS |

**操作行為：**
- 「繼續銷售」/「開啟銷售」→ 導向 `/pos/ui?config_id=N`（controller 自動處理 session 開啟）
- KDS 圖示 → 導向 `/pos-kds/{config.id}?token={config.kds_access_token}`（`kds_access_token` 是 `pos.config` 模型上的欄位）

**空狀態：** 當使用者沒有被分享到任何營業點時，顯示「目前沒有指派給您的營業點」提示文字，不做 redirect

**視覺風格：**
- Odoo portal 風格：`bg-100` 淺色卡片背景、圓角
- 按鈕色系：Odoo primary `#714B67`
- 狀態標籤：綠色 `text-success` / 灰色 `text-muted`
- 響應式佈局：`<div class="row g-3">` 包裹，每張卡片 `col-12 col-md-6`

### 3. 程式碼修改

所有修改限於 `pos_self_order_enhancement` 模組，不建新模組。修改同時部署（module upgrade 是原子操作）。

#### `views/portal_templates.xml`

- 刪除 `portal_my_home_kds` template 整個 `<template>` block
- `portal_my_home_pos` template 不修改（已使用固定描述文字 `管理您的銷售收款與訂單`，不依賴 `portal_pos_config_label`）

#### `views/portal_pos_picker_templates.xml`

直接編輯檔案內容，原地替換現有的 `<template id="portal_pos_picker">` 區塊（非新增第二個定義，是修改同一個 XML node）：

- 使用 `portal.portal_layout` 框架
- 標題區（h3 + 副標題 + 返回按鈕）
- `t-foreach="configs" t-as="config"` 迴圈渲染卡片
- 每張卡片：名稱、狀態標籤（`t-if="config.has_active_session"`）、操作按鈕、KDS 圖示（`t-if="config.kds_enabled"`）
- 空狀態：`t-if="not configs"` 顯示提示文字

刪除 `portal_kds_picker` template（整個 `<template>` block）

#### `controllers/pos_portal.py`

**`PortalHomePosCard.portal_my_pos` 方法：**

```python
@http.route(['/my/pos'], type='http', auth='user', website=True)
def portal_my_pos(self, **kw):
    user = request.env.user
    if user._is_internal():
        return request.redirect('/odoo/action-point_of_sale.action_client_pos_menu')
    if not user._is_portal():
        return request.redirect('/my')

    partner = user.sudo().partner_id
    configs = partner.portal_pos_config_ids.filtered('active')

    # 一律顯示列表頁，不再自動跳轉
    return request.render(
        'pos_self_order_enhancement.portal_pos_picker',
        {
            'page_name': 'portal_pos',
            'configs': configs,
        },
    )
```

Template context 中的 `configs` 是 `pos.config` recordset，透過 `sudo()` 取得（沿用現有程式碼的做法 — portal user 對 `pos.config` 沒有直接 read 權限，需 sudo 繞過 record rule 才能讀取 `has_active_session`、`kds_enabled`、`kds_access_token` 等欄位）。安全性由 `portal_pos_config_ids` Many2many 關聯控制：只有被明確指派的 config 才會出現。

**`PortalHomePosCard.portal_my_kds` 方法：**

保留路由避免舊書籤 404，改為 redirect：

```python
@http.route(['/my/kds'], type='http', auth='user', website=True)
def portal_my_kds(self, **kw):
    return request.redirect('/my/pos')
```

**`PortalHomePosCard._prepare_home_portal_values` 方法：**

保留的 key：
- `portal_pos_config_count` — portal 首頁卡片仍需要

移除的 key：
- `portal_kds_config_count`
- `portal_kds_config_label`
- `portal_pos_config_label`（首頁卡片已改用固定描述文字，不需動態 label）

### 4. 邊界情況

| 情境 | 處理方式 |
|------|----------|
| Portal user 沒有任何 `portal_pos_config_ids` | 列表頁顯示空狀態提示文字 |
| POS config 的 `self_ordering_default_user_id` 為空 | 不影響列表頁渲染；進入 POS UI 時由現有 `pos_web` controller 處理（回傳 404） |
| 所有 config 都沒有啟用 KDS | 每張卡片的 KDS 圖示都不渲染（`t-if` 條件），頁面正常顯示 |
| `kds_enabled=True` 但 `kds_access_token` 為空 | KDS 按鈕不渲染（`t-if` 同時檢查兩個欄位） |
| `/my/kds` 舊連結 | Redirect 到 `/my/pos` |

### 5. 不修改的部分

- `PosPortalController.pos_web` — POS UI 入口邏輯不變
- `controllers/kds.py` — KDS 頁面本身不變
- POS 後台設定（`portal_pos_config_ids`、`kds_enabled`）不變
- 其他 portal 卡片（發票、訂單、付款方式等）不變
