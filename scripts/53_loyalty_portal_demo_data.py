#!/usr/bin/env python3
"""
Inzense Odoo 18 — Loyalty Portal Demo Data
Creates sample data for 4 loyalty program types so the member center portal
shows meaningful content for the demo portal user.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/53_loyalty_portal_demo_data.py
"""
import xmlrpc.client
from datetime import datetime, timedelta

# --- Connection ---
URL = "http://localhost:8069"
DB = "inzense"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
assert uid, "Authentication failed"
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")


def execute(model, method, *args, **kwargs):
    return models.execute_kw(DB, uid, PASSWORD, model, method, *args, **kwargs)


def search(model, domain, **kwargs):
    return execute(model, "search", [domain], **kwargs)


def search_read(model, domain, fields=None, **kwargs):
    kw = {}
    if fields:
        kw["fields"] = fields
    kw.update(kwargs)
    return execute(model, "search_read", [domain], kw)


def create(model, vals):
    return execute(model, "create", [vals])


def write(model, ids, vals):
    return execute(model, "write", [ids, vals])


# ============================================================
# Find portal user
# ============================================================
PORTAL_PARTNER_ID = 44  # 禪香不二 展示客戶

partner = search_read("res.partner", [["id", "=", PORTAL_PARTNER_ID]], ["name"])
assert partner, f"Partner {PORTAL_PARTNER_ID} not found"
print(f"Portal user: {partner[0]['name']} (partner_id={PORTAL_PARTNER_ID})")


# ============================================================
# Phase 1: Update existing programs — portal_visible + point_name
# ============================================================
print("\n=== Phase 1: Update program settings ===")

PROGRAM_SETTINGS = {
    7: {"portal_visible": True, "portal_point_name": "點數"},       # 集點卡
    8: {"portal_visible": True, "portal_point_name": "張"},         # 優惠券
    9: {"portal_visible": True, "portal_point_name": "元"},         # 禮品卡
    10: {"portal_visible": True, "portal_point_name": "元"},        # 電子錢包
}

for prog_id, vals in PROGRAM_SETTINGS.items():
    prog = search_read("loyalty.program", [["id", "=", prog_id]], ["name"])
    if prog:
        write("loyalty.program", [prog_id], vals)
        print(f"  Updated program [{prog_id}] {prog[0]['name']}: {vals}")
    else:
        print(f"  WARNING: Program {prog_id} not found")


# ============================================================
# Phase 2: Ensure portal user has cards for all 4 types
# ============================================================
print("\n=== Phase 2: Verify/create loyalty cards ===")

existing_cards = search_read(
    "loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID]],
    ["id", "code", "points", "program_id"],
)
cards_by_program = {}
for c in existing_cards:
    pid = c["program_id"][0]
    cards_by_program.setdefault(pid, []).append(c)

CARD_DEFAULTS = {
    7: {"points": 210, "code": "INZENSE-LOYALTY-001"},   # 集點卡 210 點
    8: [],  # 優惠券 — handled separately (multiple coupons)
    9: {"points": 500, "code": "GIFT-A-500"},             # 禮品卡 500 元
    10: {"points": 3000, "code": "EWALLET-001"},           # 電子錢包 3000 元
}

for prog_id in [7, 9, 10]:
    if prog_id in cards_by_program:
        card = cards_by_program[prog_id][0]
        print(f"  Program {prog_id}: card exists (id={card['id']}, code={card['code']}, pts={card['points']})")
    else:
        defaults = CARD_DEFAULTS[prog_id]
        card_id = create("loyalty.card", {
            "program_id": prog_id,
            "partner_id": PORTAL_PARTNER_ID,
            "points": defaults["points"],
            "code": defaults["code"],
        })
        print(f"  Program {prog_id}: created card id={card_id} code={defaults['code']}")

# Coupons (program 8) — ensure at least 3 coupons
coupon_cards = cards_by_program.get(8, [])
print(f"  Program 8 (coupons): {len(coupon_cards)} existing coupons")
if len(coupon_cards) < 3:
    needed = 3 - len(coupon_cards)
    for i in range(needed):
        code = f"COUPON-{2027+len(coupon_cards)+i}"
        card_id = create("loyalty.card", {
            "program_id": 8,
            "partner_id": PORTAL_PARTNER_ID,
            "points": 1,
            "code": code,
        })
        print(f"    Created coupon: {code} (id={card_id})")


# ============================================================
# Phase 3: Create loyalty.history records
# ============================================================
print("\n=== Phase 3: Create transaction history ===")

# Refresh card list
all_cards = search_read(
    "loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID]],
    ["id", "code", "points", "program_id"],
)

# Check existing history count
existing_history = search_read("loyalty.history", [], ["id", "card_id"])
existing_card_ids_with_history = set()
for h in existing_history:
    if h["card_id"]:
        existing_card_ids_with_history.add(h["card_id"][0])

now = datetime.now()

for card in all_cards:
    card_id = card["id"]
    prog_id = card["program_id"][0]
    prog_name = card["program_id"][1]

    if card_id in existing_card_ids_with_history:
        print(f"  Card {card['code']} ({prog_name}): history already exists, skipping")
        continue

    print(f"  Card {card['code']} ({prog_name}): creating history...")

    if prog_id == 7:
        # 集點卡 — purchase history
        histories = [
            {"issued": 50, "used": 0, "description": "購買 神明沉香線香 x2"},
            {"issued": 30, "used": 0, "description": "購買 檀香臥香 x1"},
            {"issued": 80, "used": 0, "description": "購買 禪意香爐套組"},
            {"issued": 0, "used": 20, "description": "兌換 迷你試香組"},
            {"issued": 100, "used": 0, "description": "購買 沉香精油 10ml"},
            {"issued": 0, "used": 30, "description": "兌換 薰香石 x1"},
        ]
    elif prog_id == 8:
        # 優惠券 — issue/use
        histories = [
            {"issued": 1, "used": 0, "description": "滿千折百活動 獲得優惠券"},
        ]
    elif prog_id == 9:
        # 禮品卡 — gift card balance changes
        histories = [
            {"issued": 1000, "used": 0, "description": "購買禮品卡 NT$1,000"},
            {"issued": 0, "used": 300, "description": "消費折抵 訂單 S00081"},
            {"issued": 0, "used": 200, "description": "消費折抵 訂單 S00085"},
        ]
    elif prog_id == 10:
        # 電子錢包 — top-up and spend
        histories = [
            {"issued": 5000, "used": 0, "description": "儲值 NT$5,000"},
            {"issued": 0, "used": 800, "description": "消費折抵 訂單 S00076"},
            {"issued": 0, "used": 650, "description": "消費折抵 訂單 S00079"},
            {"issued": 0, "used": 550, "description": "消費折抵 訂單 S00083"},
            {"issued": 500, "used": 0, "description": "儲值回饋 NT$500"},
            {"issued": 0, "used": 500, "description": "消費折抵 訂單 S00088"},
        ]
    else:
        continue

    for i, h in enumerate(histories):
        # Spread dates over the past 60 days
        days_ago = len(histories) * 8 - i * 8
        create("loyalty.history", {
            "card_id": card_id,
            "issued": h["issued"],
            "used": h["used"],
            "description": h["description"],
        })

    print(f"    Created {len(histories)} history records")


# ============================================================
# Phase 4: Update point_name on cards
# ============================================================
print("\n=== Phase 4: Update card point names ===")

POINT_NAMES = {
    7: "點數",
    8: "張",
    9: "元",
    10: "元",
}

for card in all_cards:
    prog_id = card["program_id"][0]
    if prog_id in POINT_NAMES:
        write("loyalty.card", [card["id"]], {"point_name": POINT_NAMES[prog_id]})

print("  Point names updated for all cards")


# ============================================================
# Phase 5: Verify
# ============================================================
print("\n=== Phase 5: Verification ===")

final_cards = search_read(
    "loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID]],
    ["id", "code", "points", "point_name", "program_id"],
)

for card in final_cards:
    prog_name = card["program_id"][1]
    history_count = len(search("loyalty.history", [["card_id", "=", card["id"]]]))
    print(f"  {card['code']:25s}  {card['points']:>8.0f} {card.get('point_name', ''):<4s}  "
          f"({prog_name})  history={history_count}")

programs = search_read("loyalty.program", [["id", "in", [7, 8, 9, 10]]], ["name", "portal_visible", "portal_point_name"])
print()
for p in programs:
    print(f"  Program [{p['id']}] {p['name']}: portal_visible={p['portal_visible']}, "
          f"portal_point_name={p['portal_point_name']}")

print("\nDone! Visit the portal as '禪香不二 展示客戶' to test:")
print("  https://inzense.openclaw.com/my/member-center")
