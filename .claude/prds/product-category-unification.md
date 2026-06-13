---
name: product-category-unification
description: 統一產品分類與新增周邊商品，完成商用部署前的資料品質優化
status: active
created: 2026-06-13T04:07:05Z
---

# PRD: product-category-unification

## Executive Summary

禪香不二 Inzense Odoo 18 系統需要在正式商用部署前，完成產品資料庫的全面優化。根據 115 年商品庫存表（CSV master data），系統需從現有 240 個產品/10 個系列/4 種產品型態，擴展至 269 個產品/18 個系列/6 種產品型態，同時統一內部分類、POS 分類、電商分類三端的分類架構，清理歷史殘留資料，確保所有產品具備完整的編號、條碼、QR Code、售價、庫存追蹤等商用必要資訊。

## Problem Statement

1. **產品缺口**：CSV 有 269 個產品，Odoo 只有 240 個。缺少 47 個周邊商品（手串、念珠、精油、原木、原木筆、檀香扇、香器）和 2 個贈品
2. **分類缺口**：缺少 8 個新系列（手串/108念珠/精油/原木/原木筆/檀香扇/香器/贈品系列）和 2 個新產品型態（周邊商品/贈品）
3. **殘留髒資料**：Odoo demo 分類（All/AVCO、All/Consumable 等 9 個）、POS `_OLD_` 分類（5 個）、空的次類別（14 個）
4. **三端不一致風險**：新增分類後需確保 internal/POS/eCommerce 三端同步
5. **新產品缺乏必要屬性**：新產品需要編號、條碼、QR Code、售價、庫存追蹤（is_storable）

## User Stories

### US-1: 分類架構統一
**As** 營運管理者
**I want** 所有銷售通路（POS、電商、內部）使用相同的產品分類結構
**So that** 庫存報表、銷售分析、產品搜尋在各端一致
**Acceptance Criteria:**
- 三端（product.category / pos.category / product.public.category）結構完全一致
- 每個啟用產品在三端都有正確分類
- 不存在 0 產品的無用次類別（如功能系列/拜拜用香）
- 不存在 Odoo demo 殘留分類

### US-2: 新增周邊商品
**As** 門市銷售人員
**I want** 所有周邊商品（手串、念珠、精油、原木、原木筆、檀香扇、香器）都在系統中
**So that** 可以在 POS 掃碼結帳並追蹤庫存
**Acceptance Criteria:**
- 47 個周邊商品全部建立，含正確編號、售價、分類
- 每個產品有 QR Code 條碼記錄
- 每個產品設為可追蹤庫存（is_storable=True）
- 在 POS 和電商都可見

### US-3: 贈品管理
**As** 營運管理者
**I want** 贈品（黃銅九孔香插、黑色銅錢紋木製臥香盒）在系統中管理
**So that** 可以追蹤贈品庫存和出貨
**Acceptance Criteria:**
- 2 個贈品建立，售價 $0，設為可追蹤庫存
- 有正確分類和編號

### US-4: 清理歷史殘留
**As** 系統管理者
**I want** 清除所有 demo data 殘留和無用分類
**So that** 系統乾淨、專業，不會造成使用者混淆
**Acceptance Criteria:**
- Odoo demo 分類（All/AVCO、Consumable 等）全部移除或隱藏
- POS `_OLD_` 分類移除
- 空的不適用次類別移除（如功能系列/拜拜用香）
- 優惠組合分類有產品或移除

### US-5: 資料完整性
**As** 營運管理者
**I want** 所有啟用產品都有完整的商用必要資訊
**So that** 可以安心正式上線營運
**Acceptance Criteria:**
- 0 個產品缺少編號（default_code）
- 0 個產品缺少條碼（barcode）
- 0 個產品缺少 QR Code 記錄（product.barcode）
- 0 個啟用售價產品價格為 $0（贈品除外）
- 所有產品 is_storable=True

## Functional Requirements

### FR-1: 新增分類
- 建立 8 個新主類別（系列）：手串系列、108念珠系列、精油系列、原木系列、原木筆系列、檀香扇系列、香器系列、贈品系列
- 建立對應的次類別結構（周邊商品不需要長線香/迷你香/拜拜用香/盤香的次類別，只需要一個平面分類）
- 三端同步建立

### FR-2: 新增產品
- 從 CSV 建立 47 個周邊商品 + 2 個贈品
- 每個產品設定：name、default_code（=CSV 貨號）、barcode（=CSV 貨號）、list_price、categ_id、public_categ_ids、pos_categ_ids、is_storable=True
- 建立 product.barcode QR Code 記錄

### FR-3: 清理分類
- 移除/隱藏 Odoo demo 分類
- 移除 POS _OLD_ 分類
- 移除沒有產品且不適用的次類別

### FR-4: 驗證
- 全產品分類一致性驗證
- 全產品屬性完整性驗證
- POS 掃碼測試
- 銷售訂單掃碼測試

## Non-Functional Requirements

- 所有操作透過 XML-RPC 執行，不需要 pod 重啟
- 變更必須是冪等的（重複執行不會產生重複資料）
- 執行過程中不影響現有 POS session

## Success Criteria

1. Odoo 產品總數 = CSV 產品總數（扣除停售）
2. 三端分類結構 100% 一致
3. 0 個產品缺少任何必要屬性
4. 0 個殘留 demo 分類
5. 所有新產品可在 POS 掃碼辨識
6. 所有新產品可在銷售訂單掃碼辨識

## Constraints & Assumptions

- Odoo 18 XML-RPC API
- 透過 kubectl port-forward 連接
- CSV 為唯一正確資料來源（115年商品庫存表）
- 周邊商品不需要長線香/迷你香等次類別，用獨立系列分類即可
- 原木系列以克計價的產品 list_price 設為 0（特殊定價）

## Out of Scope

- 庫存數量設定（只設定可追蹤，不設初始庫存）
- 產品圖片上傳
- 電商頁面設計
- 會員/集點方案

## Dependencies

- kubectl port-forward 到 Odoo pod（8069）
- CSV 檔案已提供（6 個 CSV 檔案）
- 現有 barcode_scanner_label 模組已安裝
