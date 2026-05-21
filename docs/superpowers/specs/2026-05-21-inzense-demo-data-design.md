# Design: Inzense Odoo 18 Demo Data Build-out

## Goal

Populate the clean Inzense Odoo 18 instance with representative demo data for sales demonstrations: products from inzense.com.tw, a portal customer, sales/invoice/member center records, 3 POS stores with dedicated warehouses, and a central warehouse with resupply routes.

## Decisions

| Item | Decision |
|---|---|
| Products | 10 representative items from different series |
| Customer | Single portal customer, login `portal` / `portal` |
| Sales/Invoices | 10 orders, all within past month, all invoiced and paid |
| Member Center | Loyalty points, coupons, gift cards, e-wallet for portal customer |
| POS | 3 stores: 信義旗艦店, 板橋店, 台中店 |
| Warehouses | 4 total: 1 central + 3 store-specific |
| Modules to install | `sale_management`, `account`, `point_of_sale`, `stock` |
| Implementation | Python scripts via XML-RPC (following existing project pattern) |

## 1. Module Installation

Install these 4 core modules (and their auto-dependencies):

- `sale_management` — Sales orders
- `account` — Invoicing / Accounting
- `point_of_sale` — POS terminals
- `stock` — Inventory / Warehouses

These are installed via XML-RPC `button_immediate_install` (same pattern as previous scripts).

## 2. Products (10 items)

Selected to cover all major product categories from inzense.com.tw:

| # | Name | Category | Price (NT$) | Type |
|---|---|---|---|---|
| 1 | 線香功能系列 – 善緣香 | 功能系列 | 899 | storable |
| 2 | 線香功能系列 – 財神香 | 功能系列 | 899 | storable |
| 3 | 線香功能系列 – 三清檀香 | 功能系列 | 650 | storable |
| 4 | 線香脈輪系列 – 心輪香 | 脈輪系列 | 750 | storable |
| 5 | 線香五行系列 – 木神香 | 五行系列 | 750 | storable |
| 6 | 柬埔寨沉香 | 拜拜用香 | 1,200 | storable |
| 7 | 巴拉圭綠檀 | 拜拜用香 | 1,000 | storable |
| 8 | 決策穩心組 | 優惠組合 | 807 | storable |
| 9 | 穩定能量組 | 優惠組合 | 712 | storable |
| 10 | 神馬都順 全能順遂組合 | 年節禮盒 | 2,888 | storable |

Product type is `storable` (not `consu`) so inventory tracking works with warehouses.

**Product Images:** Use local files from `images/products/` directory. Each product has a matching cover image already downloaded. Images are base64-encoded and set as `image_1920`.

**Product Categories (internal):** Create internal categories matching the series names for organization in POS and backend.

## 3. Company Setup

Update the default company:
- Name: 禪香不二 Inzense
- Currency: TWD (New Taiwan Dollar)
- Country: Taiwan
- Address: 台北市北投區光明路240號2樓之8
- Phone: 0926-926-851

## 4. Portal Customer

| Field | Value |
|---|---|
| Name | 禪香不二 展示客戶 |
| Email | portal@inzense.com.tw |
| Phone | 0912-345-678 |
| Login | portal@inzense.com.tw |
| Password | portal |
| Portal access | Yes (add to portal group) |

Created as `res.partner` with a linked `res.users` record in the portal group.

## 5. Sales Orders & Invoices (10 records)

All orders belong to the portal customer. Dates span the past ~30 days. Each order is:
1. Created as `sale.order`
2. Confirmed (`action_confirm`)
3. Invoice created (`_create_invoices`)
4. Invoice posted (`action_post`)
5. Payment registered

| # | Date (~) | Products | Approx Total |
|---|---|---|---|
| 1 | 30 days ago | 善緣香 x2 | NT$1,798 |
| 2 | 27 days ago | 財神香 x1, 三清檀香 x1 | NT$1,549 |
| 3 | 24 days ago | 心輪香 x3 | NT$2,250 |
| 4 | 21 days ago | 木神香 x1, 柬埔寨沉香 x1 | NT$1,950 |
| 5 | 18 days ago | 巴拉圭綠檀 x2 | NT$2,000 |
| 6 | 15 days ago | 決策穩心組 x1, 善緣香 x1 | NT$1,706 |
| 7 | 12 days ago | 穩定能量組 x2, 財神香 x1 | NT$2,323 |
| 8 | 9 days ago | 神馬都順 x1 | NT$2,888 |
| 9 | 6 days ago | 三清檀香 x2, 心輪香 x1 | NT$2,050 |
| 10 | 3 days ago | 善緣香 x1, 木神香 x1, 巴拉圭綠檀 x1 | NT$2,649 |

## 6. Member Center / Loyalty Data

Using the installed WOOW member center modules and Odoo `loyalty` module:

### Loyalty Program (集點卡)
- Create a loyalty program: 每消費 NT$100 得 1 點
- Portal customer should have accumulated points from the 10 orders (~210 points)

### Coupons (優惠券)
- Create a coupon program: 「滿千折百」(NT$1,000 以上折 NT$100)
- Generate 3 coupons for portal customer:
  - 1 already used (linked to order #8)
  - 2 unused / available

### Gift Cards (禮品卡)
- Create a gift card program
- Issue 2 gift cards to portal customer:
  - Card A: NT$500 balance (NT$1,000 original, NT$500 used)
  - Card B: NT$2,000 balance (unused)

### E-Wallet (電子錢包)
- Create an e-wallet program
- Portal customer balance: NT$3,000

## 7. POS Configuration (3 Stores)

| POS | Name | Location |
|---|---|---|
| 1 | 禪香不二 信義旗艦店 | 台北市信義區 |
| 2 | 禪香不二 板橋店 | 新北市板橋區 |
| 3 | 禪香不二 台中店 | 台中市西區 |

Each POS config:
- Linked to its dedicated warehouse (stock picking type)
- All 10 products available
- TWD currency
- POS categories: 功能系列, 脈輪系列, 五行系列, 拜拜用香, 優惠組合

## 8. Warehouse Architecture

### Warehouses

| Warehouse | Short Name | Location (address) |
|---|---|---|
| 禪香不二 中央倉庫 | 中央 | 台北市北投區光明路240號 |
| 信義旗艦店倉庫 | 信義 | 台北市信義區 |
| 板橋店倉庫 | 板橋 | 新北市板橋區 |
| 台中店倉庫 | 台中 | 台中市西區 |

### Initial Stock

| Warehouse | Qty per product |
|---|---|
| 中央倉庫 | 1,000 units |
| 信義旗艦店倉庫 | 100 units |
| 板橋店倉庫 | 100 units |
| 台中店倉庫 | 100 units |

Stock is set via `stock.quant` adjustments (inventory adjustment).

### Resupply Routes

Each store warehouse has a resupply route from the central warehouse:
- 中央倉庫 → 信義旗艦店倉庫
- 中央倉庫 → 板橋店倉庫
- 中央倉庫 → 台中店倉庫

Configured via `resupply_wh_ids` on each store warehouse.

## Implementation Approach

Single Python script (`scripts/50_demo_data_setup.py`) executed via `kubectl port-forward` + XML-RPC, following the existing project pattern. The script handles all steps in order:

1. Install modules
2. Configure company
3. Create product categories and products
4. Create portal customer
5. Create warehouses and configure resupply
6. Create POS configs
7. Set initial stock levels
8. Create sales orders and invoices
9. Create loyalty/coupon/gift card/e-wallet data

## What Is NOT Included

- Website/eCommerce frontend customization (already handled by website module auto-install)
- Blog or activity pages
- Multiple customers (only 1 portal customer)
- KOL/channel-specific product variants
- Accounting chart of accounts configuration (use Odoo defaults)
