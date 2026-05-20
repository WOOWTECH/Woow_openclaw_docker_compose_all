# Odoo 品牌移除 + B2C/B2B 全流程 UI/UX 優化計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 移除所有頁面的 Odoo 品牌標識，並修復購物車、預約、商店、Portal 等頁面的 UI/UX 排版與設計問題。

**Architecture:** 透過 XML 模板繼承 (xpath) 移除 Odoo 品牌元素，並針對 Odoo 18 實際 DOM 結構更新 SCSS 選擇器以確保樣式正確套用。所有修改限定在 `mujimed_theme` 模組內，不修改 Odoo 核心檔案。

**Tech Stack:** Odoo 18 XML Templates, SCSS (compiled via Odoo asset pipeline), Odoo 18 QWeb template inheritance

---

## 問題分析（來自截圖）

### 截圖對照問題清單

| # | 截圖 | 頁面 | 問題 |
|---|------|------|------|
| 1 | 171728 | 首頁底部 | **Odoo 品牌標識**：「版權所有 © 公司名稱」+「由 odoo - 最強的 開源電商平台 驅動」（紅圈標註）|
| 2 | 171903 | 首頁底部 | 同上，Odoo 品牌標識依然顯示 |
| 3 | 171805 | 預約時段選擇 | 時段按鈕使用 **Bootstrap 預設藍色邊框**（#0d6efd），未套用 clay/mocha 主題色；底部 Odoo 品牌可見 |
| 4 | 171748 | 預約日曆 | 日曆格子為 **預設樣式**，無主題色；「自動分配」下拉選單未美化；月份導航箭頭樣式普通 |
| 5 | 171945 | B2B 商店列表 | 產品圖片為 **破損佔位符**；分類標籤頁樣式需改進；搜尋欄與檢視切換按鈕樣式不一致 |
| 6 | 172002 | 購物車 | 產品描述顯示 **原始 HTML `<p>` 標籤**（未渲染）；數量 +/- 按鈕需美化；價格摘要區視覺層次不足 |
| 7 | 171407 | Portal 儀表板 | Header 顯示「YourLogo」佔位符；整體佈局可微調優化 |

---

## 檔案結構

### 將修改的檔案

```
mujimed_theme/
├── views/
│   ├── layout.xml              ← 修改：修復 Odoo 品牌移除（當前 xpath 未生效）
│   └── snippets.xml            ← 新建：移除購物車 HTML 標籤 + 其他模板修正
├── static/src/scss/
│   ├── _shop.scss              ← 修改：修復商店列表、購物車、結帳樣式
│   ├── _appointment.scss       ← 修改：修復日曆、時段選擇器樣式
│   ├── _portal.scss            ← 修改：Portal 儀表板微調
│   ├── _global.scss            ← 修改：全域補充（select, quantity controls）
│   └── _rwd.scss               ← 修改：行動版修正
└── __manifest__.py             ← 修改：新增 snippets.xml 到 data 列表
```

---

## Task 1: 移除所有頁面的 Odoo 品牌標識

**問題根因：** 當前 `layout.xml` 使用 `xpath expr="//div[@id='footer']"` 移除 footer，但 Odoo 18 的「Powered by Odoo」版權文字位於 `div#footer` **之外**，或使用了不同的 DOM 結構（例如 `<div class="o_footer_copyright">` 或直接在 `website.layout` 模板末尾）。

**Files:**
- Modify: `mujimed_theme/views/layout.xml:1-11`

- [ ] **Step 1: 研究 Odoo 18 footer 結構**

在 Odoo 18 中，版權文字通常來自以下模板之一：
- `website.layout` 底部的 copyright section
- `website.footer_copyright` 模板
- `website.layout_footer_copyright` 模板

需要在瀏覽器開發者工具 (F12) 中檢查實際 DOM 結構，確認 Odoo 品牌文字所在的確切元素及 CSS class。

- [ ] **Step 2: 更新 layout.xml 移除所有 Odoo 品牌**

替換現有的 footer 移除邏輯，改為更精準的 xpath 定位。新的 `layout.xml` 需要覆蓋：

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- Hide footer entirely per design spec (HANDOFF §4.1) -->
    <template id="hide_footer" inherit_id="website.layout" name="Mujimed: Hide Footer">
        <xpath expr="//div[@id='footer']" position="replace">
            <!-- Footer removed per Mujimed design spec -->
        </xpath>
    </template>

    <!-- Remove Odoo copyright / "Powered by" branding -->
    <!-- Target 1: website.layout 中的 footer copyright section -->
    <template id="hide_odoo_copyright" inherit_id="website.layout"
              name="Mujimed: Remove Odoo Copyright">
        <xpath expr="//small[hasclass('o_footer_copyright_name')]" position="replace"/>
    </template>

    <!-- Target 2: 如果存在獨立的 footer_copyright 模板 -->
    <template id="hide_footer_copyright_badge"
              inherit_id="website.footer_copyright"
              name="Mujimed: Remove Powered by Odoo Badge"
              active="True" priority="99">
        <xpath expr="//span[hasclass('o_footer_copyright_name')]" position="replace"/>
        <xpath expr="//a[contains(@href, 'odoo.com')]" position="replace"/>
    </template>

</odoo>
```

**注意：** 上方 xpath 為假設值。Step 1 確認 DOM 後需調整確切路徑。核心策略是：
1. 保留 `div#footer` 移除
2. **額外** 針對 copyright 區塊做移除（它可能在 `#footer` 外面）
3. 用 CSS `display: none` 做兜底保險

- [ ] **Step 3: 在 _global.scss 加入 CSS 兜底**

```scss
// ─── Odoo branding removal (belt & suspenders) ──────────────
// CSS fallback in case XML xpath doesn't catch all instances
.o_footer_copyright_name,
a[href*="odoo.com"],
.o_powered_by_odoo,
small:has(> a[href*="odoo.com"]) {
    display: none !important;
}
```

加入到 `_global.scss` 檔案末尾（在 `@media (max-width: 767px)` 之前）。

- [ ] **Step 4: 驗證移除**

部署後在以下頁面驗證 Odoo 品牌已消失：
- 首頁 (`/`)
- 預約頁 (`/appointment`)
- 商店頁 (`/shop`)
- Portal (`/my`)
- 購物車 (`/shop/cart`)

Run: 瀏覽器巡覽各頁面，檢查頁尾區域

- [ ] **Step 5: Commit**

```bash
git add mujimed_theme/views/layout.xml mujimed_theme/static/src/scss/_global.scss
git commit -m "fix: remove Odoo branding from all pages (footer copyright + CSS fallback)"
```

---

## Task 2: 修復購物車頁面 — HTML 標籤外露 + 排版

**問題：** 購物車中產品描述顯示原始 `<p>` 標籤文字（如 `<p>A型肉毒桿菌素100單位裝，經濟包裝</p>`），數量控制按鈕樣式需統一。

**Files:**
- Modify: `mujimed_theme/static/src/scss/_shop.scss:129-155`
- Create: `mujimed_theme/views/snippets.xml` (cart template override)
- Modify: `mujimed_theme/__manifest__.py:9-14`

- [ ] **Step 1: 新建 snippets.xml 處理購物車描述 HTML 渲染**

HTML 標籤外露通常是因為 Odoo 在購物車中使用 `t-esc` 而非 `t-raw`/`t-out` 來渲染產品描述。需要繼承購物車模板來修復。

建立 `mujimed_theme/views/snippets.xml`：

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!--
        Fix cart product description: strip HTML tags via CSS
        Odoo 18 cart renders short_description with t-esc (displays raw HTML).
        We use CSS to hide the raw description and show only the product name.
    -->
    <template id="muji_cart_description_fix"
              inherit_id="website_sale.cart_lines"
              name="Mujimed: Clean Cart Descriptions">
        <!--
            If the raw HTML is coming from a specific element,
            hide it via xpath. This needs DOM inspection first.
            Fallback: handle via CSS below.
        -->
    </template>

</odoo>
```

**注意：** 需先用 F12 確認購物車描述的確切 DOM 元素，再決定用 xpath 隱藏還是用 `t-out` 替換 `t-esc`。

- [ ] **Step 2: CSS 方案 — 隱藏購物車中的原始 HTML 描述文字**

在 `_shop.scss` 的 cart 區塊加入：

```scss
// ─── Cart ───────────────────────────────────────────────────
.oe_cart,
#wrap .oe_cart {
    background: $muji-cream !important;

    // Hide raw HTML description text (shows <p> tags)
    .td-product_name small,
    .o_cart_product .text-muted,
    .o_cart_product .o_wsale_product_information small {
        display: none;
    }

    // Quantity controls styling
    .css_quantity {
        display: inline-flex;
        align-items: center;
        border: 1px solid $muji-line-2;
        border-radius: $muji-r-pill;
        overflow: hidden;

        .js_add_cart_json,
        .btn-link {
            width: 36px;
            height: 36px;
            display: grid;
            place-items: center;
            background: transparent;
            border: none;
            color: $muji-espresso;
            font-size: 16px;
            text-decoration: none;

            &:hover {
                background: $muji-cream-2;
            }
        }

        input.quantity {
            width: 44px;
            text-align: center;
            border: none;
            border-left: 1px solid $muji-line-2;
            border-right: 1px solid $muji-line-2;
            font-family: $muji-ff-display;
            font-size: 15px;
            color: $muji-espresso;
            padding: 6px 0;
            background: transparent;

            &:focus { outline: none; }
        }
    }

    // Delete button
    .js_delete_product,
    .td-action .btn {
        color: $muji-mist;
        border: none;
        background: transparent;

        &:hover { color: $muji-rust; }
    }

    // Cart summary card
    #cart_total, .o_cart_summary {
        background: #fff;
        border: 1px solid $muji-line;
        border-radius: $muji-r-md;
        padding: 28px;

        // Price summary labels
        .text-muted, label {
            font-size: 13px;
            color: $muji-slate;
            letter-spacing: .04em;
        }

        // Total amount
        .oe_currency_value,
        .o_total_amount {
            font-family: $muji-ff-display;
            font-style: italic;
            font-size: 28px;
            color: $muji-mocha;
        }

        // Subtotal / tax lines
        .o_subtotal, .o_tax {
            font-size: 14px;
            color: $muji-ink;
        }
    }

    // Coupon input
    .oe_website_sale_coupon,
    form[action*="coupon"] {
        display: flex;
        gap: 8px;

        input {
            flex: 1;
            border: 1px solid $muji-line-2;
            border-radius: $muji-r-sm;
            padding: 12px 16px;
            font-size: 14px;

            &:focus {
                border-color: $muji-clay;
                box-shadow: 0 0 0 2px rgba($muji-clay, .15);
            }
        }

        .btn {
            background: $muji-mocha;
            color: $muji-cream;
            border-radius: $muji-r-sm;
            padding: 12px 20px;
            font-size: 13px;
            letter-spacing: .12em;
            border: none;

            &:hover { background: $muji-espresso; }
        }
    }

    // Checkout button
    a[href="/shop/checkout"],
    .btn-primary {
        border-radius: $muji-r-pill !important;
        padding: 16px 32px;
        font-size: 14px;
        letter-spacing: .14em;
    }

    table {
        th {
            font-size: 11px;
            letter-spacing: .18em;
            text-transform: uppercase;
            color: $muji-slate;
            font-weight: 500;
        }
    }
}
```

- [ ] **Step 3: 更新 __manifest__.py**

```python
'data': [
    'data/ir_asset.xml',
    'views/layout.xml',
    'views/snippets.xml',    # 新增
    'views/login.xml',
    'views/homepage.xml',
],
```

- [ ] **Step 4: Commit**

```bash
git add mujimed_theme/views/snippets.xml mujimed_theme/static/src/scss/_shop.scss mujimed_theme/__manifest__.py
git commit -m "fix: cart page HTML tag rendering + quantity controls + summary card styling"
```

---

## Task 3: 修復預約日曆 + 時段選擇器樣式

**問題：**
- 時段按鈕（09:00-10:00 等）使用 Bootstrap 預設**藍色邊框**（#0d6efd），而非 clay/mocha
- 日曆格子為預設白色方塊樣式
- 「自動分配」下拉選單未美化
- 月份導航箭頭樣式平淡

**Files:**
- Modify: `mujimed_theme/static/src/scss/_appointment.scss:70-93`

- [ ] **Step 1: 修正時段按鈕選擇器**

Odoo 18 預約模組的時段按鈕 class 可能與我們當前 SCSS 中的選擇器不匹配。從截圖看，藍色邊框說明 `.o_slot_button` / `.o_appointment_slot` 選擇器**未命中**。

需要更新選擇器以匹配 Odoo 18 實際 DOM。常見的 Odoo 18 時段按鈕結構：

```scss
// ─── Appointment calendar ───────────────────────────────────
// Odoo 18 appointment slot selectors (broader coverage)
.o_appointment_calendar,
.o_appointment_slots,
.o_appointment_select_slots,
[id*="slots"] {

    // Time slot buttons — override Bootstrap blue border
    .o_slot_button,
    .o_appointment_slot,
    .btn-outline-primary,      // Odoo 18 uses this Bootstrap class!
    a.btn[href*="slot"],
    button[data-slot] {
        border: 1px solid $muji-line-2 !important;
        border-radius: $muji-r-sm !important;
        padding: 14px 18px;
        font-size: 14px;
        font-family: $muji-ff-sans;
        color: $muji-espresso !important;
        background: #fff !important;
        transition: all .2s;
        text-decoration: none;

        &:hover, &:focus, &.active, &.selected {
            background: $muji-clay !important;
            border-color: $muji-clay !important;
            color: #fff !important;
            box-shadow: none !important;
        }

        &.disabled, &:disabled {
            opacity: .4;
            cursor: not-allowed;
        }

        // "1可用" availability text
        small, .text-muted, .o_appointment_slot_availabilities {
            font-size: 11px;
            color: $muji-mist;
            letter-spacing: .06em;
        }
    }
}
```

- [ ] **Step 2: 美化日曆格子**

```scss
// ─── Calendar widget ────────────────────────────────────────
.o_appointment_calendar,
.o_appointment_select_date,
.o_daterange_picker,
table.table-bordered {

    // Month header (五月 2026)
    .o_appointment_month,
    caption,
    .ui-datepicker-title,
    th.month {
        font-family: $muji-ff-serif;
        font-size: 22px;
        color: $muji-espresso;
        font-weight: 500;
        text-align: center;
        padding: 16px 0;
    }

    // Weekday headers (日 一 二 三 四 五 六)
    thead th,
    .o_appointment_weekday {
        font-size: 12px;
        color: $muji-slate;
        font-weight: 500;
        letter-spacing: .08em;
        text-align: center;
        padding: 8px;
    }

    // Date cells
    td {
        text-align: center;
        padding: 0;

        a, button, .o_day {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: $muji-r-sm;
            color: $muji-ink;
            font-size: 14px;
            border: 1px solid transparent;
            transition: all .15s;

            &:hover {
                background: $muji-cream-2;
                border-color: $muji-line;
                text-decoration: none;
            }

            &.active, &.o_selected, &.ui-state-active {
                background: $muji-clay !important;
                color: #fff !important;
                border-color: $muji-clay !important;
            }

            &.today, &.o_today {
                border-color: $muji-clay;
                font-weight: 600;
            }

            &.disabled, &.ui-state-disabled {
                color: $muji-mist;
                cursor: not-allowed;
            }
        }
    }

    // Navigation arrows (< >)
    .o_appointment_prev,
    .o_appointment_next,
    .ui-datepicker-prev,
    .ui-datepicker-next,
    .btn-light {
        border: 1px solid $muji-line-2 !important;
        border-radius: $muji-r-pill !important;
        color: $muji-espresso !important;
        background: transparent !important;
        width: 40px;
        height: 40px;
        display: inline-grid;
        place-items: center;

        &:hover {
            background: $muji-cream-2 !important;
            border-color: $muji-espresso !important;
        }
    }
}

// ─── Resource/Staff dropdown ────────────────────────────────
.o_appointment_select_resources,
.o_appointment_select_staff {
    select, .form-select {
        border: 1px solid $muji-line-2;
        border-radius: $muji-r-sm;
        padding: 12px 16px;
        font-size: 14px;
        font-family: $muji-ff-sans;
        color: $muji-espresso;
        background-color: #fff;
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%233D2B22' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 16px center;
        padding-right: 40px;

        &:focus {
            border-color: $muji-clay;
            box-shadow: 0 0 0 2px rgba($muji-clay, .15);
        }
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add mujimed_theme/static/src/scss/_appointment.scss
git commit -m "fix: appointment calendar + time slots — replace Bootstrap blue with theme colors"
```

---

## Task 4: 修復商店頁面 — 分類標籤、搜尋欄、產品卡片

**問題：**
- 分類標籤（注射耗材 / 雷射耗材 / 體雕設備耗材）下方有粗黑線，風格突兀
- 搜尋欄 + 格狀/列表檢視切換按鈕樣式不統一
- 產品卡片圖片為破損佔位符（內容問題，非 CSS）
- 產品名稱截斷顯示

**Files:**
- Modify: `mujimed_theme/static/src/scss/_shop.scss:1-87`

- [ ] **Step 1: 美化分類標籤/篩選列**

```scss
// ─── Category tabs / pills ──────────────────────────────────
.o_wsale_categories,
.o_shop_category_nav {
    // Horizontal category tabs
    .nav-pills, .nav-tabs, .nav {
        gap: 4px;
        border-bottom: 1px solid $muji-line;
        padding-bottom: 12px;
        margin-bottom: 24px;

        .nav-link, .nav-item a {
            font-family: $muji-ff-sans;
            font-size: 13px;
            letter-spacing: .08em;
            color: $muji-slate;
            padding: 10px 18px;
            border-radius: $muji-r-pill;
            border: none;
            background: transparent;
            transition: all .2s;
            white-space: nowrap;

            &.active, &:hover {
                background: $muji-espresso;
                color: $muji-cream;
            }
        }
    }
}

// ─── Search bar + view toggles ──────────────────────────────
.o_wsale_search,
.o_searchbar_form {
    .form-control, input[type="search"] {
        border: 1px solid $muji-line-2;
        border-radius: $muji-r-pill;
        padding: 10px 20px 10px 44px;
        font-size: 14px;
        background-image: none; // remove default search icon
        font-family: $muji-ff-sans;

        &:focus {
            border-color: $muji-clay;
            box-shadow: 0 0 0 2px rgba($muji-clay, .15);
        }

        &::placeholder {
            color: $muji-mist;
        }
    }

    .btn, button[type="submit"] {
        position: absolute;
        right: 4px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: $muji-slate;

        &:hover { color: $muji-espresso; }
    }
}

// View toggle buttons (grid/list/filter)
.o_wsale_display_toggle,
.o_wsale_apply_options {
    .btn, button {
        border: 1px solid $muji-line-2;
        border-radius: $muji-r-sm;
        color: $muji-slate;
        padding: 8px 12px;
        background: transparent;

        &.active, &:hover {
            background: $muji-cream-2;
            border-color: $muji-line;
            color: $muji-espresso;
        }
    }
}
```

- [ ] **Step 2: 改善產品卡片文字截斷**

```scss
// Product card name — prevent ugly truncation
.oe_product_cart,
.o_wsale_product_grid_wrapper .oe_product {
    .o_wsale_product_information h6 {
        // Allow 2-line display instead of truncation
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.6em; // Reserve space for 2 lines
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add mujimed_theme/static/src/scss/_shop.scss
git commit -m "fix: shop page — category tabs, search bar, view toggles, product card text"
```

---

## Task 5: Portal 儀表板微調

**問題：** 整體佈局已大致合理，但需要微調：
- 會員問候區文字層次
- 待付款發票提示卡片的背景色
- 通知區域空白太多

**Files:**
- Modify: `mujimed_theme/static/src/scss/_portal.scss:19-64`

- [ ] **Step 1: 增強 Portal 首頁組件**

```scss
// ─── Portal home /my — enhanced ──────────────────────────────
.o_portal_my_home {

    // Member greeting area
    .o_portal_my_details_card,
    .o_portal_my_home_greeting {
        background: $muji-cream-2;
        border: 1px solid $muji-line;
        border-radius: $muji-r-md;
        padding: 24px;
        margin-bottom: 28px;

        // Name / greeting
        h3, .o_greeting_title {
            font-family: $muji-ff-serif;
            font-size: 24px;
            color: $muji-espresso;
            margin-bottom: 4px;
        }

        // Date / time info
        .text-muted, .o_greeting_subtitle {
            font-size: 13px;
            color: $muji-slate;
            letter-spacing: .04em;
        }
    }

    // Pending invoice banner
    .o_portal_my_home_banner,
    .alert {
        background: $muji-bisque !important;
        border: none !important;
        border-radius: $muji-r-md;
        padding: 20px 24px;
        color: $muji-espresso;

        .btn, a.btn {
            background: $muji-mocha;
            color: $muji-cream;
            border: none;
            border-radius: $muji-r-pill;
            padding: 10px 24px;
            font-size: 13px;
            letter-spacing: .12em;

            &:hover { background: $muji-espresso; }
        }
    }

    // Notification area
    .o_portal_my_home_notifications,
    .o_portal_notifications {
        .card {
            border-color: $muji-line;

            .text-muted {
                color: $muji-mist !important;
                font-size: 13px;
            }
        }
    }

    // Quick action cards (你的訂單, 發票)
    .o_portal_category,
    .o_portal_docs .card {
        border-color: $muji-line;
        border-radius: $muji-r-md;
        padding: 20px;
        transition: all .2s;

        &:hover {
            box-shadow: $muji-sh-1;
            border-color: $muji-clay;
        }

        img, .o_portal_icon {
            width: 48px;
            height: 48px;
            object-fit: contain;
        }

        h5 {
            font-family: $muji-ff-serif;
            font-size: 18px;
            color: $muji-espresso;
        }

        .text-muted {
            font-size: 13px;
            color: $muji-slate !important;
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add mujimed_theme/static/src/scss/_portal.scss
git commit -m "fix: portal dashboard — greeting card, invoice banner, action cards styling"
```

---

## Task 6: 全域 select / form-select / quantity 控制補充

**問題：** 多個頁面的下拉選單（`<select>`）和數量控制元素（`+/-`）未套用主題樣式。

**Files:**
- Modify: `mujimed_theme/static/src/scss/_global.scss:70-80`

- [ ] **Step 1: 新增全域 select 和 quantity 樣式**

在 `_global.scss` 的 `.form-control` 區塊後加入：

```scss
// ─── Select / Dropdown ────────────────────────────────────────
.form-select, select.form-control {
    border-color: $muji-line-2;
    border-radius: $muji-r-sm;
    font-family: $muji-ff-sans;
    font-size: 14px;
    color: $muji-espresso;
    padding: 10px 40px 10px 14px;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%233D2B22' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 14px center;

    &:focus {
        border-color: $muji-clay;
        box-shadow: 0 0 0 2px rgba($muji-clay, .15);
    }
}

// ─── Quantity widget (shared across shop/cart) ────────────────
.css_quantity, .o_quantity {
    display: inline-flex;
    align-items: center;
    border: 1px solid $muji-line-2;
    border-radius: $muji-r-pill;
    overflow: hidden;

    a, button, .btn-link, .js_add_cart_json {
        width: 36px;
        height: 36px;
        display: grid;
        place-items: center;
        color: $muji-espresso;
        background: transparent;
        border: none;
        text-decoration: none;
        font-size: 16px;
        cursor: pointer;

        &:hover { background: $muji-cream-2; }
    }

    input[type="text"], input.quantity {
        width: 44px;
        text-align: center;
        border: none;
        border-left: 1px solid $muji-line-2;
        border-right: 1px solid $muji-line-2;
        font-family: $muji-ff-display;
        font-size: 15px;
        color: $muji-espresso;
        padding: 6px 0;
        background: transparent;

        &:focus { outline: none; }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add mujimed_theme/static/src/scss/_global.scss
git commit -m "fix: global select/dropdown + quantity widget styling"
```

---

## Task 7: 行動版 RWD 修正

**問題：** 行動版多處需要調整以配合新增的樣式。

**Files:**
- Modify: `mujimed_theme/static/src/scss/_rwd.scss:12-103`

- [ ] **Step 1: 補充行動版修正**

在 `_rwd.scss` 的 `@media (max-width: 767px)` 區塊內加入：

```scss
    // Appointment time slots — 2-column grid on mobile
    .o_appointment_select_slots,
    .o_appointment_slots {
        display: grid !important;
        grid-template-columns: 1fr 1fr;
        gap: 8px;

        .o_slot_button,
        .o_appointment_slot,
        .btn-outline-primary {
            width: 100%;
            padding: 12px 8px;
            font-size: 13px;
            text-align: center;
        }
    }

    // Calendar date cells smaller
    .o_appointment_calendar td a,
    .o_appointment_calendar td button,
    .o_appointment_calendar td .o_day {
        width: 36px;
        height: 36px;
        font-size: 13px;
    }

    // Cart: stack product info and quantity
    .oe_cart {
        .td-product_name,
        .td-qty,
        .td-price {
            display: block;
            width: 100%;
        }

        .css_quantity {
            margin: 8px 0;
        }

        #cart_total, .o_cart_summary {
            padding: 20px;
        }
    }

    // Portal greeting — smaller
    .o_portal_my_home {
        .o_portal_my_details_card,
        .o_portal_my_home_greeting {
            padding: 16px;

            h3 { font-size: 20px; }
        }
    }

    // Category tabs — horizontal scroll
    .o_wsale_categories .nav,
    .o_shop_category_nav .nav {
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 8px;
    }
```

- [ ] **Step 2: Commit**

```bash
git add mujimed_theme/static/src/scss/_rwd.scss
git commit -m "fix: mobile RWD — appointment slots grid, cart stack, portal greeting, category scroll"
```

---

## Task 8: 現場 DOM 驗證 + 選擇器修正

**重要：** 以上 Task 1-7 的 SCSS 選擇器基於 Odoo 18 的常見 DOM 結構推斷。在部署到測試環境後，**必須**用瀏覽器 F12 開發者工具逐頁驗證。

**Files:** 可能涉及前述所有 SCSS 檔案的選擇器調整

- [ ] **Step 1: 部署到測試環境**

```bash
# 在 K3s cluster 上重建 Odoo pod 或更新模組
# 或進入 Odoo 後台 → 設定 → 技術 → 模組 → 升級 mujimed_theme
```

- [ ] **Step 2: 逐頁驗證（開 F12 對照）**

檢查清單：

| 頁面 | 驗證項目 | 方法 |
|------|---------|------|
| 所有頁面 | Odoo 品牌消失 | 捲到底部 |
| `/shop` | 分類標籤顏色、搜尋欄樣式、產品卡片 hover | 點擊交互 |
| `/shop/cart` | 無 `<p>` 標籤、數量控制器美觀、總計卡片 | 加入商品後查看 |
| `/appointment` | 日曆主題色、時段無藍框、下拉選單美觀 | 選擇日期 |
| `/my` | 問候卡片、發票提示、訂單/發票卡片 hover | 登入後查看 |

- [ ] **Step 3: 記錄不匹配的選擇器並修正**

對於每個未命中的選擇器：
1. 在 F12 Elements 中找到目標元素的實際 class
2. 更新對應 SCSS 檔案的選擇器
3. 在 Odoo 後台升級模組 → 重新整理頁面驗證

- [ ] **Step 4: 最終 Commit**

```bash
git add mujimed_theme/
git commit -m "fix: adjust SCSS selectors to match Odoo 18 actual DOM structure"
```

---

## 優化方向總結

| 區域 | 改動數量 | 優化內容 |
|------|---------|---------|
| **Odoo 品牌移除** | 2 處 | XML xpath 移除 + CSS display:none 兜底 |
| **購物車頁** | 5 處 | HTML 標籤隱藏、數量控制器美化、摘要卡片、優惠碼輸入、結帳按鈕 |
| **預約頁** | 4 處 | 時段按鈕改色、日曆格子美化、月份標題字體、下拉選單美化 |
| **商店列表** | 3 處 | 分類標籤 pill 化、搜尋欄圓角+focus、檢視切換按鈕統一 |
| **Portal 儀表板** | 3 處 | 問候卡片底色、發票提示美化、快速操作卡片 hover |
| **全域元素** | 2 處 | select 下拉選單全域美化、quantity 數量控制器統一 |
| **行動版 RWD** | 4 處 | 預約時段 grid、購物車堆疊、Portal 問候縮小、分類標籤滾動 |
| **合計** | **23 處** | |
