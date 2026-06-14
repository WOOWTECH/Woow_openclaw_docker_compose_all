---
name: inzense-mid-year-promo
status: in-progress
created: 2026-06-14T04:38:00Z
updated: 2026-06-14T04:38:00Z
progress: 0%
prd: .claude/prds/inzense-mid-year-promo.md
github: (will be set on sync)
---

# Epic: inzense-mid-year-promo

## Overview
建置禪香不二誠品板橋店開幕暨年中慶完整優惠體系，使用 Odoo 18 原生模組。

## Architecture Decisions
1. 價目表用 product.pricelist，applied_on 由細到粗自動排他
2. 促銷/優惠券/集點卡統一用 loyalty.program，不同 program_type 區分
3. 不累贈靠「一張碼一方案」的物理特性，不寫排他程式
4. 贈品保留真實價值，reward 折 0 發放

## Implementation Strategy

Phase 1 (並行):
  Task 1: 啟用功能 + 建立贈品/服務商品
  Task 2: 建立價目表

Phase 2 (並行, 依賴 Phase 1):
  Task 3: 建立促銷方案（滿千贈+任選3盒）
  Task 4: 建立轉盤優惠券 x4
  Task 5: 建立滿額贈優惠券 x4

Phase 3 (依賴 Phase 1):
  Task 6: 建立忠誠集點卡

Phase 4:
  Task 7: 全面驗收測試（7項）

## Tasks Created
- [ ] 001.md - 啟用功能 + 建立贈品/服務商品 (parallel: true)
- [ ] 002.md - 建立年中慶價目表 (parallel: true)
- [ ] 003.md - 建立促銷方案 (parallel: true, depends: 001)
- [ ] 004.md - 建立轉盤優惠券 x4 (parallel: true, depends: 001)
- [ ] 005.md - 建立滿額贈優惠券 x4 (parallel: true, depends: 001)
- [ ] 006.md - 建立忠誠集點卡 (parallel: true, depends: 001)
- [ ] 007.md - 全面驗收測試 7 項 (depends: all)

Total tasks: 7
Parallel tasks: 6
Sequential tasks: 1
Estimated total effort: 4 hours
