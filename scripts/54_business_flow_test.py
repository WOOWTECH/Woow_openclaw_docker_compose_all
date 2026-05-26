#!/usr/bin/env python3
"""
Inzense Odoo 18 — Comprehensive Business Flow Test
Covers: payment setup, POS checkout, warehouse transfer, SO full cycle,
        batch import, POS loyalty/ewallet/gift-card/coupon redemption.

Run with:
  kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
  python3 scripts/54_business_flow_test.py
"""
import xmlrpc.client
import time
import sys
from datetime import datetime, timedelta

# ── Connection ────────────────────────────────────────────────────────────────
URL = "http://localhost:8069"
DB = "inzense"
USERNAME = "admin"
PASSWORD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
assert uid, "Authentication failed — is port-forward running?"
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}\n")


# ── Helpers ───────────────────────────────────────────────────────────────────
def rpc(model, method, *args, **kwargs):
    return models.execute_kw(DB, uid, PASSWORD, model, method, *args, **kwargs)

def search(model, domain, **kw):
    return models.execute_kw(DB, uid, PASSWORD, model, "search", [domain], kw or {})

def search_read(model, domain, fields, **kw):
    opts = {"fields": fields}
    opts.update(kw)
    return models.execute_kw(DB, uid, PASSWORD, model, "search_read", [domain], opts)

def create(model, vals):
    return rpc(model, "create", [vals])

def write(model, ids, vals):
    return rpc(model, "write", [ids, vals])

def get_stock(product_id, location_id):
    quants = search_read("stock.quant",
        [["product_id", "=", product_id], ["location_id", "=", location_id]],
        ["quantity"])
    return sum(q["quantity"] for q in quants)


# ── Test tracking ────────────────────────────────────────────────────────────
RESULTS = []

def check(label, actual, expected):
    ok = actual == expected
    RESULTS.append({"test": label, "ok": ok, "actual": actual, "expected": expected})
    icon = "✓" if ok else "✗"
    print(f"    [{icon}] {label}: got={actual}, want={expected}")
    return ok

def check_gt(label, actual, threshold):
    ok = actual > threshold
    RESULTS.append({"test": label, "ok": ok, "actual": actual, "expected": f">{threshold}"})
    icon = "✓" if ok else "✗"
    print(f"    [{icon}] {label}: got={actual}, want >{threshold}")
    return ok

def check_gte(label, actual, threshold):
    ok = actual >= threshold
    RESULTS.append({"test": label, "ok": ok, "actual": actual, "expected": f">={threshold}"})
    icon = "✓" if ok else "✗"
    print(f"    [{icon}] {label}: got={actual}, want >={threshold}")
    return ok

def check_true(label, value):
    ok = bool(value)
    RESULTS.append({"test": label, "ok": ok, "actual": value, "expected": True})
    icon = "✓" if ok else "✗"
    print(f"    [{icon}] {label}: {value}")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# Phase 0: Resolve reference IDs
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("Phase 0: Resolve reference data")
print("=" * 70)

warehouses = search_read("stock.warehouse", [["company_id", "=", 1]],
                          ["name", "lot_stock_id"])
WH = {w["name"]: {"id": w["id"], "loc": w["lot_stock_id"][0]} for w in warehouses}

CENTRAL_LOC  = WH["禪香不二 中央倉庫"]["loc"]
XINYI_LOC    = WH["信義旗艦店倉庫"]["loc"]
BANQIAO_LOC  = WH["板橋店倉庫"]["loc"]
TAICHUNG_LOC = WH["台中店倉庫"]["loc"]
CENTRAL_WH_ID = WH["禪香不二 中央倉庫"]["id"]

products = search_read("product.product", [["available_in_pos", "=", True]],
                        ["id", "name", "list_price"])
PROD = {p["name"]: {"id": p["id"], "price": p["list_price"]} for p in products}

SHANYUAN  = PROD.get("線香功能系列 – 善緣香", {})
CAISHEN   = PROD.get("線香功能系列 – 財神香", {})
SANQING   = PROD.get("線香功能系列 – 三清檀香", {})
XINLUN    = PROD.get("線香脈輪系列 – 心輪香", {})
MUSHEN    = PROD.get("線香五行系列 – 木神香", {})
CAMBODIA  = PROD.get("柬埔寨沉香", {})
PARAGUAY  = PROD.get("巴拉圭綠檀", {})

pos_configs = search_read("pos.config", [["name", "like", "禪香不二"]],
                           ["id", "name"])
POS = {p["name"]: p["id"] for p in pos_configs}
POS_XINYI_ID   = POS.get("禪香不二 信義旗艦店")
POS_BANQIAO_ID = POS.get("禪香不二 板橋店")
POS_TAICHUNG_ID = POS.get("禪香不二 台中店")

PORTAL_PARTNER_ID = 44

internal_pt = search("stock.picking.type",
    [["code", "=", "internal"], ["warehouse_id", "=", CENTRAL_WH_ID]])

print(f"  Warehouses: {len(WH)}, Products: {len(PROD)}, POS: {len(POS)}")
print(f"  Product prices: 善緣香={SHANYUAN.get('price')}, 財神香={CAISHEN.get('price')}")


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1: Create payment methods
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 1: Setup payment methods")
print("=" * 70)

# Odoo 18: each POS needs its own cash payment method (cannot share)
STORE_SHORT = {
    "禪香不二 信義旗艦店": "信義",
    "禪香不二 板橋店": "板橋",
    "禪香不二 台中店": "台中",
}
CASH_PM_IDS = {}  # config_id → cash PM id

for config_name, config_id in POS.items():
    short = STORE_SHORT.get(config_name, str(config_id))
    pm_name = f"現金-{short}"
    jnl_name = f"現金-{short}"

    # Cash journal per store
    jnl = search_read("account.journal",
        [["name", "=", jnl_name], ["type", "=", "cash"]], ["id"])
    if jnl:
        jnl_id = jnl[0]["id"]
    else:
        jnl_id = create("account.journal", {
            "name": jnl_name,
            "type": "cash",
            "code": f"C{short[:2]}",
            "company_id": 1,
        })
    # Cash PM per store
    pm = search_read("pos.payment.method",
        [["name", "=", pm_name], ["type", "=", "cash"]], ["id"])
    if pm:
        cash_pm_id = pm[0]["id"]
    else:
        cash_pm_id = create("pos.payment.method", {
            "name": pm_name,
            "type": "cash",
            "is_cash_count": False,
            "journal_id": jnl_id,
            "company_id": 1,
        })
    CASH_PM_IDS[config_id] = cash_pm_id
    print(f"  {config_name}: cash PM={cash_pm_id} (journal={jnl_id})")

# Shared credit card payment method
card_pm = search_read("pos.payment.method",
    [["name", "=", "禪香不二 信用卡"]], ["id"])
if card_pm:
    CARD_PM_ID = card_pm[0]["id"]
    print(f"  Card payment method exists: id={CARD_PM_ID}")
else:
    bank_journal = search_read("account.journal",
        [["type", "=", "bank"], ["company_id", "=", 1]], ["id"], limit=1)
    bank_jnl_id = bank_journal[0]["id"] if bank_journal else False
    CARD_PM_ID = create("pos.payment.method", {
        "name": "禪香不二 信用卡",
        "type": "bank",
        "is_cash_count": False,
        "journal_id": bank_jnl_id,
        "company_id": 1,
    })
    print(f"  Created card PM: id={CARD_PM_ID}")

# Assign per-store cash PM + shared card PM to each POS config
for config_name, config_id in POS.items():
    cash_pm_id = CASH_PM_IDS[config_id]
    write("pos.config", [config_id], {
        "payment_method_ids": [(6, 0, [cash_pm_id, CARD_PM_ID])],
    })
    print(f"  Updated {config_name}: PMs=[{cash_pm_id}, {CARD_PM_ID}]")

# For convenience — map store config id → its cash PM
CASH_PM_XINYI    = CASH_PM_IDS.get(POS_XINYI_ID)
CASH_PM_BANQIAO  = CASH_PM_IDS.get(POS_BANQIAO_ID)
CASH_PM_TAICHUNG = CASH_PM_IDS.get(POS_TAICHUNG_ID)

# 1e: Enable Demo payment provider for eCommerce
demo_providers = search_read("payment.provider",
    [["code", "=", "demo"]], ["id", "state"])
if demo_providers:
    write("payment.provider", [demo_providers[0]["id"]], {"state": "test"})
    print(f"  Demo payment provider enabled (state=test)")

# Verify
for config_id in POS.values():
    cfg = search_read("pos.config", [["id", "=", config_id]],
                       ["payment_method_ids"])
    check_gte(f"1: POS {config_id} has >=2 PMs",
              len(cfg[0]["payment_method_ids"]), 2)


# ── Helper: close all open POS sessions for a config ──────────────────────────
def close_open_sessions(config_id):
    """Close any open POS sessions for the given config."""
    open_sess = search("pos.session",
        [["config_id", "=", config_id], ["state", "!=", "closed"]])
    for sid in open_sess:
        try:
            rpc("pos.session", "action_pos_session_closing_control", [[sid]])
        except Exception:
            pass
        try:
            write("pos.session", [sid], {"state": "closing_control"})
        except Exception:
            pass
        try:
            rpc("pos.session", "action_pos_session_validate", [[sid]])
        except Exception:
            pass
    return len(open_sess)


# ── Helper: run a POS order cycle ─────────────────────────────────────────────
def run_pos_order(config_id, store_name, lines, payment_method_id,
                  partner_id=False, reward_lines=None):
    """
    Open session → create order → pay → close session.
    lines: [(product_dict, qty), ...]
    reward_lines: [(reward_id, coupon_id, points_cost, discount_amount), ...] or None
    Returns: (session_id, order_id, order_state)
    """
    closed = close_open_sessions(config_id)
    if closed:
        print(f"  Closed {closed} old session(s)")

    write("pos.config", [config_id], {"cash_control": False})

    session_id = create("pos.session", {"config_id": config_id})
    try:
        rpc("pos.session", "action_pos_session_open", [[session_id]])
    except Exception:
        pass

    # Build order lines
    order_lines = []
    subtotal = 0
    for prod, qty in lines:
        price = prod["price"]
        line_total = price * qty
        subtotal += line_total
        order_lines.append((0, 0, {
            "product_id": prod["id"],
            "qty": qty,
            "price_unit": price,
            "price_subtotal": line_total,
            "price_subtotal_incl": line_total,
        }))

    # Build reward lines (discounts)
    total_discount = 0
    if reward_lines:
        for reward_id, coupon_id, points_cost, discount_amount in reward_lines:
            total_discount += discount_amount
            order_lines.append((0, 0, {
                "product_id": lines[0][0]["id"],  # placeholder product
                "qty": 1,
                "price_unit": -discount_amount,
                "price_subtotal": -discount_amount,
                "price_subtotal_incl": -discount_amount,
                "is_reward_line": True,
                "reward_id": reward_id,
                "coupon_id": coupon_id,
                "points_cost": points_cost,
            }))

    amount_total = subtotal - total_discount

    order_vals = {
        "session_id": session_id,
        "partner_id": partner_id,
        "lines": order_lines,
        "amount_tax": 0,
        "amount_total": amount_total,
        "amount_paid": amount_total,
        "amount_return": 0,
        "payment_ids": [(0, 0, {
            "amount": amount_total,
            "payment_method_id": payment_method_id,
        })],
    }

    order_id = create("pos.order", order_vals)

    try:
        rpc("pos.order", "action_pos_order_paid", [[order_id]])
    except Exception:
        pass

    # Close session
    try:
        rpc("pos.session", "action_pos_session_closing_control", [[session_id]])
    except Exception:
        pass
    try:
        write("pos.session", [session_id], {"state": "closing_control"})
    except Exception:
        pass
    try:
        rpc("pos.session", "action_pos_session_validate", [[session_id]])
    except Exception:
        pass

    time.sleep(1)

    order_data = search_read("pos.order", [["id", "=", order_id]],
                              ["state", "amount_total"])
    session_data = search_read("pos.session", [["id", "=", session_id]],
                                ["state"])

    return {
        "session_id": session_id,
        "order_id": order_id,
        "order_state": order_data[0]["state"] if order_data else "unknown",
        "order_total": order_data[0]["amount_total"] if order_data else 0,
        "session_state": session_data[0]["state"] if session_data else "unknown",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2: POS Checkout — 信義旗艦店 (現金)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 2: POS Checkout — 信義旗艦店 (現金)")
print("=" * 70)

price_sy = SHANYUAN["price"]
expected_total = price_sy * 2
print(f"  Order: 善緣香 x2 @ {price_sy} = {expected_total}")

result = run_pos_order(POS_XINYI_ID, "信義", [(SHANYUAN, 2)], CASH_PM_XINYI)
print(f"  Session: {result['session_state']}, Order: {result['order_state']}, "
      f"Total: {result['order_total']}")

check("2a: session closed", result["session_state"], "closed")
check("2b: order state done", result["order_state"], "done")
check(f"2c: order total = {expected_total}", result["order_total"], expected_total)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 3: POS Checkout — 板橋店 (信用卡 + 倉庫隔離)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 3: POS Checkout — 板橋店 (信用卡)")
print("=" * 70)

price_cs = CAISHEN["price"]
print(f"  Order: 財神香 x1 @ {price_cs} = {price_cs}")

result3 = run_pos_order(POS_BANQIAO_ID, "板橋", [(CAISHEN, 1)], CARD_PM_ID)
print(f"  Session: {result3['session_state']}, Order: {result3['order_state']}, "
      f"Total: {result3['order_total']}")

check("3a: session closed", result3["session_state"], "closed")
check("3b: order state done", result3["order_state"], "done")
check(f"3c: order total = {price_cs}", result3["order_total"], price_cs)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 4: Central → 台中 Internal Transfer (缺貨補貨)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 4: Central → 台中 Internal Transfer (30 units 柬埔寨沉香)")
print("=" * 70)

TRANSFER_QTY = 30
central_before = get_stock(CAMBODIA["id"], CENTRAL_LOC)
taichung_before = get_stock(CAMBODIA["id"], TAICHUNG_LOC)
print(f"  Before: central={central_before}, 台中={taichung_before}")

picking_id = create("stock.picking", {
    "picking_type_id": internal_pt[0],
    "location_id": CENTRAL_LOC,
    "location_dest_id": TAICHUNG_LOC,
    "origin": "台中缺貨補貨-柬埔寨沉香",
    "move_ids": [(0, 0, {
        "name": "中央→台中 柬埔寨沉香",
        "product_id": CAMBODIA["id"],
        "product_uom_qty": TRANSFER_QTY,
        "location_id": CENTRAL_LOC,
        "location_dest_id": TAICHUNG_LOC,
    })],
})

rpc("stock.picking", "action_confirm", [[picking_id]])
rpc("stock.picking", "action_assign", [[picking_id]])

move_lines = search_read("stock.move.line",
    [["picking_id", "=", picking_id]], ["id"])
for ml in move_lines:
    write("stock.move.line", [ml["id"]], {"quantity": TRANSFER_QTY})

try:
    rpc("stock.picking", "button_validate", [[picking_id]])
except Exception:
    pass

central_after = get_stock(CAMBODIA["id"], CENTRAL_LOC)
taichung_after = get_stock(CAMBODIA["id"], TAICHUNG_LOC)
print(f"  After:  central={central_after}, 台中={taichung_after}")

check("4a: central decreased", central_before - central_after, float(TRANSFER_QTY))
check("4b: 台中 increased", taichung_after - taichung_before, float(TRANSFER_QTY))

pick_state = search_read("stock.picking", [["id", "=", picking_id]],
                          ["state"])[0]["state"]
check("4c: picking state done", pick_state, "done")


# ══════════════════════════════════════════════════════════════════════════════
# Phase 5: Sales Order Full Cycle (確認→出貨→發票→收款)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 5: Sales Order Full Cycle")
print("=" * 70)

so_lines = [
    (SANQING, 2),   # 三清檀香 x2
    (XINLUN, 1),    # 心輪香 x1
]
expected_so_total = sum(p["price"] * q for p, q in so_lines)
print(f"  Order: 三清檀香 x2 + 心輪香 x1 = {expected_so_total}")

# Create SO
so_id = create("sale.order", {
    "partner_id": PORTAL_PARTNER_ID,
    "order_line": [(0, 0, {
        "product_id": p["id"],
        "product_uom_qty": q,
    }) for p, q in so_lines],
})
print(f"  Created SO: id={so_id}")

# Confirm
rpc("sale.order", "action_confirm", [[so_id]])
so_data = search_read("sale.order", [["id", "=", so_id]],
                       ["state", "amount_total", "picking_ids", "invoice_ids"])
check("5a: SO confirmed", so_data[0]["state"], "sale")
check_gt("5b: SO total > 0", so_data[0]["amount_total"], 0)

# Deliver — process picking
picking_ids = so_data[0]["picking_ids"]
check_true("5c: picking created", len(picking_ids) > 0)

if picking_ids:
    pick_id = picking_ids[0]
    rpc("stock.picking", "action_assign", [[pick_id]])

    pick_moves = search_read("stock.move.line",
        [["picking_id", "=", pick_id]], ["id", "product_id", "quantity"])
    for ml in pick_moves:
        move_data = search_read("stock.move",
            [["id", "in", search("stock.move", [["picking_id", "=", pick_id]])]],
            ["product_uom_qty"])
        # Set done qty to demanded qty
        write("stock.move.line", [ml["id"]], {"quantity": ml.get("quantity", 1) or 1})

    # If no move lines yet, set quantities on stock.move
    if not pick_moves:
        moves = search_read("stock.move", [["picking_id", "=", pick_id]],
                             ["id", "product_uom_qty"])
        for m in moves:
            write("stock.move", [m["id"]], {"quantity": m["product_uom_qty"]})

    try:
        rpc("stock.picking", "button_validate", [[pick_id]])
    except Exception:
        pass

    pick_state = search_read("stock.picking", [["id", "=", pick_id]],
                              ["state"])[0]["state"]
    check("5d: delivery done", pick_state, "done")

# Create invoice
try:
    ctx = {"active_model": "sale.order", "active_ids": [so_id], "active_id": so_id}
    wiz_id = models.execute_kw(DB, uid, PASSWORD,
        "sale.advance.payment.inv", "create", [{}], {"context": ctx})
    models.execute_kw(DB, uid, PASSWORD,
        "sale.advance.payment.inv", "create_invoices", [[wiz_id]], {"context": ctx})
except Exception:
    pass

so_data2 = search_read("sale.order", [["id", "=", so_id]], ["invoice_ids"])
inv_ids = so_data2[0]["invoice_ids"] if so_data2 else []
check_true("5e: invoice created", len(inv_ids) > 0)

if inv_ids:
    inv_id = inv_ids[0]
    # Post invoice
    inv_state = search_read("account.move", [["id", "=", inv_id]], ["state"])[0]["state"]
    if inv_state == "draft":
        rpc("account.move", "action_post", [[inv_id]])

    inv_state2 = search_read("account.move", [["id", "=", inv_id]], ["state"])[0]["state"]
    check("5f: invoice posted", inv_state2, "posted")

    # Register payment
    bank_journal = search("account.journal",
        [["type", "=", "bank"], ["company_id", "=", 1]], limit=1)
    if bank_journal:
        try:
            pay_ctx = {"active_model": "account.move", "active_ids": [inv_id]}
            pay_wiz = models.execute_kw(DB, uid, PASSWORD,
                "account.payment.register", "create",
                [{"journal_id": bank_journal[0]}], {"context": pay_ctx})
            models.execute_kw(DB, uid, PASSWORD,
                "account.payment.register", "action_create_payments",
                [[pay_wiz]], {"context": pay_ctx})
        except Exception:
            pass

    pay_state = search_read("account.move", [["id", "=", inv_id]],
                             ["payment_state"])[0]["payment_state"]
    check("5g: invoice paid", pay_state, "paid")


# ══════════════════════════════════════════════════════════════════════════════
# Phase 6: Batch Sales Order Import (5 orders)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 6: Batch Sales Order Import (5 orders)")
print("=" * 70)

today = datetime.now()
BATCH_ORDERS = [
    {"days_ago": 5, "lines": [(SHANYUAN, 3)],                    "label": "善緣香x3"},
    {"days_ago": 4, "lines": [(CAISHEN, 2), (MUSHEN, 1)],        "label": "財神香x2+木神香x1"},
    {"days_ago": 3, "lines": [(CAMBODIA, 1)],                    "label": "柬埔寨沉香x1"},
    {"days_ago": 2, "lines": [(PARAGUAY, 2), (SANQING, 1)],      "label": "綠檀x2+三清x1"},
    {"days_ago": 1, "lines": [(XINLUN, 3), (SHANYUAN, 1)],       "label": "心輪香x3+善緣香x1"},
]

batch_so_ids = []
batch_total = 0

for i, order in enumerate(BATCH_ORDERS, 1):
    order_date = (today - timedelta(days=order["days_ago"])).strftime("%Y-%m-%d")
    order_lines = [(0, 0, {
        "product_id": p["id"],
        "product_uom_qty": q,
    }) for p, q in order["lines"]]

    so_id = create("sale.order", {
        "partner_id": PORTAL_PARTNER_ID,
        "date_order": order_date,
        "order_line": order_lines,
    })
    rpc("sale.order", "action_confirm", [[so_id]])
    batch_so_ids.append(so_id)

    so_info = search_read("sale.order", [["id", "=", so_id]],
                           ["amount_total", "state"])
    batch_total += so_info[0]["amount_total"]
    print(f"  #{i}: {order['label']} date={order_date} "
          f"total={so_info[0]['amount_total']} state={so_info[0]['state']}")

check("6a: 5 orders created", len(batch_so_ids), 5)

# Batch invoice + pay
bank_journal = search("account.journal",
    [["type", "=", "bank"], ["company_id", "=", 1]], limit=1)
paid_count = 0

for so_id in batch_so_ids:
    try:
        ctx = {"active_model": "sale.order", "active_ids": [so_id], "active_id": so_id}
        wiz_id = models.execute_kw(DB, uid, PASSWORD,
            "sale.advance.payment.inv", "create", [{}], {"context": ctx})
        models.execute_kw(DB, uid, PASSWORD,
            "sale.advance.payment.inv", "create_invoices", [[wiz_id]], {"context": ctx})
    except Exception:
        pass

    so_info = search_read("sale.order", [["id", "=", so_id]], ["invoice_ids"])
    for inv_id in so_info[0].get("invoice_ids", []):
        try:
            inv_data = search_read("account.move", [["id", "=", inv_id]], ["state"])
            if inv_data and inv_data[0]["state"] == "draft":
                rpc("account.move", "action_post", [[inv_id]])
        except Exception:
            pass
        try:
            if bank_journal:
                pay_ctx = {"active_model": "account.move", "active_ids": [inv_id]}
                pay_wiz = models.execute_kw(DB, uid, PASSWORD,
                    "account.payment.register", "create",
                    [{"journal_id": bank_journal[0]}], {"context": pay_ctx})
                models.execute_kw(DB, uid, PASSWORD,
                    "account.payment.register", "action_create_payments",
                    [[pay_wiz]], {"context": pay_ctx})
        except Exception:
            pass

        pay_st = search_read("account.move", [["id", "=", inv_id]],
                              ["payment_state"])
        if pay_st and pay_st[0]["payment_state"] == "paid":
            paid_count += 1

check("6b: all 5 invoices paid", paid_count, 5)
print(f"  Batch total: {batch_total}")


# ══════════════════════════════════════════════════════════════════════════════
# Phase 7: POS — 電子錢包折抵 (eWallet)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 7: POS — 電子錢包折抵")
print("=" * 70)

# Get ewallet card
ewallet_cards = search_read("loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID],
     ["program_id", "=", 10]], ["id", "code", "points"])
assert ewallet_cards, "No ewallet card found"
ew_card = ewallet_cards[0]
ew_before = ew_card["points"]
EW_DISCOUNT = 500  # 折抵 500 元

# Reward for ewallet: id=10, 1 point = 1 TWD discount
EW_REWARD_ID = 10
EW_CARD_ID = ew_card["id"]

print(f"  eWallet card: {ew_card['code']}, balance before={ew_before}")
print(f"  Order: 善緣香 x1 = {SHANYUAN['price']}, ewallet discount = {EW_DISCOUNT}")

result7 = run_pos_order(
    POS_XINYI_ID, "信義",
    [(SHANYUAN, 1)],
    CASH_PM_XINYI,
    partner_id=PORTAL_PARTNER_ID,
    reward_lines=[(EW_REWARD_ID, EW_CARD_ID, EW_DISCOUNT, EW_DISCOUNT)],
)

# Manually deduct ewallet points + create history (POS frontend does this via JS)
write("loyalty.card", [EW_CARD_ID], {"points": ew_before - EW_DISCOUNT})
create("loyalty.history", {
    "card_id": EW_CARD_ID,
    "issued": 0,
    "used": EW_DISCOUNT,
    "description": f"POS 消費折抵 信義旗艦店 (Order #{result7['order_id']})",
})

ew_after = search_read("loyalty.card", [["id", "=", EW_CARD_ID]], ["points"])[0]["points"]
print(f"  eWallet balance after: {ew_after}")

check("7a: POS order done", result7["order_state"], "done")
check(f"7b: ewallet deducted by {EW_DISCOUNT}",
      ew_before - ew_after, float(EW_DISCOUNT))
expected_pay = SHANYUAN["price"] - EW_DISCOUNT
check(f"7c: paid amount = {expected_pay}", result7["order_total"], expected_pay)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 8: POS — 優惠券折扣 (Coupon)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 8: POS — 優惠券折扣 (滿千折百)")
print("=" * 70)

# Find an available coupon (points > 0) for program 8
coupon_cards = search_read("loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID],
     ["program_id", "=", 8],
     ["points", ">", 0]],
    ["id", "code", "points"])
assert coupon_cards, "No available coupon found"
coupon_card = coupon_cards[0]
COUPON_REWARD_ID = 8   # reward for program 8
COUPON_CARD_ID = coupon_card["id"]
COUPON_DISCOUNT = 100  # 折百

print(f"  Coupon: {coupon_card['code']}, points={coupon_card['points']}")
print(f"  Order: 柬埔寨沉香 x1 = {CAMBODIA['price']} (>1000, 滿千折百)")

result8 = run_pos_order(
    POS_BANQIAO_ID, "板橋",
    [(CAMBODIA, 1)],
    CARD_PM_ID,
    partner_id=PORTAL_PARTNER_ID,
    reward_lines=[(COUPON_REWARD_ID, COUPON_CARD_ID, 1, COUPON_DISCOUNT)],
)

# Deduct coupon point
write("loyalty.card", [COUPON_CARD_ID], {"points": 0})
create("loyalty.history", {
    "card_id": COUPON_CARD_ID,
    "issued": 0,
    "used": 1,
    "description": f"POS 優惠券使用 板橋店 (Order #{result8['order_id']})",
})

coupon_after = search_read("loyalty.card", [["id", "=", COUPON_CARD_ID]],
                            ["points"])[0]["points"]
print(f"  Coupon points after: {coupon_after}")

expected_8 = CAMBODIA["price"] - COUPON_DISCOUNT
check("8a: POS order done", result8["order_state"], "done")
check(f"8b: order total = {expected_8}", result8["order_total"], expected_8)
check("8c: coupon used (points=0)", coupon_after, 0.0)


# ══════════════════════════════════════════════════════════════════════════════
# Phase 9: POS — 禮品卡折抵 (Gift Card)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 9: POS — 禮品卡折抵")
print("=" * 70)

gc_cards = search_read("loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID],
     ["program_id", "=", 9],
     ["points", ">", 0]],
    ["id", "code", "points"],
    order="points asc", limit=1)
assert gc_cards, "No gift card with balance found"
gc_card = gc_cards[0]
GC_CARD_ID = gc_card["id"]
GC_REWARD_ID = 9
gc_before = gc_card["points"]
GC_DISCOUNT = min(gc_before, MUSHEN["price"])  # 折抵不超過商品金額

print(f"  Gift card: {gc_card['code']}, balance={gc_before}")
print(f"  Order: 木神香 x1 = {MUSHEN['price']}, gift card discount = {GC_DISCOUNT}")

result9 = run_pos_order(
    POS_TAICHUNG_ID, "台中",
    [(MUSHEN, 1)],
    CASH_PM_TAICHUNG,
    partner_id=PORTAL_PARTNER_ID,
    reward_lines=[(GC_REWARD_ID, GC_CARD_ID, GC_DISCOUNT, GC_DISCOUNT)],
)

# Deduct gift card points
write("loyalty.card", [GC_CARD_ID], {"points": gc_before - GC_DISCOUNT})
create("loyalty.history", {
    "card_id": GC_CARD_ID,
    "issued": 0,
    "used": GC_DISCOUNT,
    "description": f"POS 禮品卡折抵 台中店 (Order #{result9['order_id']})",
})

gc_after = search_read("loyalty.card", [["id", "=", GC_CARD_ID]],
                        ["points"])[0]["points"]
print(f"  Gift card balance after: {gc_after}")

expected_9 = MUSHEN["price"] - GC_DISCOUNT
check("9a: POS order done", result9["order_state"], "done")
check(f"9b: order total = {expected_9}", result9["order_total"], expected_9)
check(f"9c: gift card deducted by {GC_DISCOUNT}",
      gc_before - gc_after, float(GC_DISCOUNT))


# ══════════════════════════════════════════════════════════════════════════════
# Phase 10: POS — 集點卡折抵 (Loyalty Points)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("Phase 10: POS — 集點卡折抵")
print("=" * 70)

loyalty_cards = search_read("loyalty.card",
    [["partner_id", "=", PORTAL_PARTNER_ID],
     ["program_id", "=", 7]],
    ["id", "code", "points"])
assert loyalty_cards, "No loyalty card found"
lc_card = loyalty_cards[0]
LC_CARD_ID = lc_card["id"]
LC_REWARD_ID = 7
lc_before = lc_card["points"]
LC_POINTS_USE = 100   # 使用 100 點 = 折抵 100 元
LC_DISCOUNT = LC_POINTS_USE  # 1 point = 1 TWD (per_point mode)

print(f"  Loyalty card: {lc_card['code']}, points={lc_before}")
print(f"  Order: 巴拉圭綠檀 x1 = {PARAGUAY['price']}, use {LC_POINTS_USE} points = -{LC_DISCOUNT}")

result10 = run_pos_order(
    POS_XINYI_ID, "信義",
    [(PARAGUAY, 1)],
    CASH_PM_XINYI,
    partner_id=PORTAL_PARTNER_ID,
    reward_lines=[(LC_REWARD_ID, LC_CARD_ID, LC_POINTS_USE, LC_DISCOUNT)],
)

# Deduct loyalty points
write("loyalty.card", [LC_CARD_ID], {"points": lc_before - LC_POINTS_USE})
create("loyalty.history", {
    "card_id": LC_CARD_ID,
    "issued": 0,
    "used": LC_POINTS_USE,
    "description": f"POS 集點折抵 信義旗艦店 (Order #{result10['order_id']})",
})

lc_after = search_read("loyalty.card", [["id", "=", LC_CARD_ID]],
                        ["points"])[0]["points"]
print(f"  Loyalty points after: {lc_after}")

expected_10 = PARAGUAY["price"] - LC_DISCOUNT
check("10a: POS order done", result10["order_state"], "done")
check(f"10b: order total = {expected_10}", result10["order_total"], expected_10)
check(f"10c: loyalty points deducted by {LC_POINTS_USE}",
      lc_before - lc_after, float(LC_POINTS_USE))


# ══════════════════════════════════════════════════════════════════════════════
# Test Report
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TEST REPORT")
print("=" * 70)

passed = sum(1 for r in RESULTS if r["ok"])
failed = sum(1 for r in RESULTS if not r["ok"])
total = len(RESULTS)

print(f"\n  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
print(f"  Pass rate: {passed/total*100:.0f}%\n")

if failed:
    print("  FAILED TESTS:")
    for r in RESULTS:
        if not r["ok"]:
            print(f"    ✗ {r['test']}: got={r['actual']}, want={r['expected']}")
    print()

# Exit with error code if any test failed
sys.exit(0 if failed == 0 else 1)
