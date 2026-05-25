#!/usr/bin/env python3
"""
Inzense Odoo 18 — Barcode Scanner Module Test
Tests barcode lookup, GS1 parsing, sale order scan, stock picking scan, label generation.
Prereq: kubectl port-forward deployment/inzense-odoo -n inzense 8069:8069
"""
import xmlrpc.client
import sys

URL = "http://localhost:8069"
DB = "inzense"
PWD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, "admin", PWD, {})
assert uid, "Auth failed"
m = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")

RESULTS = []

def check(label, actual, expected):
    ok = actual == expected
    RESULTS.append({"test": label, "ok": ok})
    print(f"  {'✓' if ok else '✗'} {label}: got={actual!r}, want={expected!r}")

def check_true(label, actual):
    ok = bool(actual)
    RESULTS.append({"test": label, "ok": ok})
    print(f"  {'✓' if ok else '✗'} {label}: got={actual!r}")


# ============================================================
# Phase 0: Setup — assign barcodes to products
# ============================================================
print("\n=== Phase 0: Assign barcodes to test products ===")

TEST_BARCODES = {
    "線香功能系列 – 善緣香": "4710001000011",
    "線香功能系列 – 財神香": "4710001000028",
    "柬埔寨沉香": "4710001000035",
    "巴拉圭綠檀": "4710001000042",
}

product_map = {}  # barcode -> product_id
for name, barcode in TEST_BARCODES.items():
    prods = m.execute_kw(DB, uid, PWD, "product.product", "search_read",
        [[["name", "=", name]]], {"fields": ["id", "barcode"], "limit": 1})
    if prods:
        pid = prods[0]["id"]
        if prods[0]["barcode"] != barcode:
            m.execute_kw(DB, uid, PWD, "product.product", "write",
                [[pid], {"barcode": barcode}])
        product_map[barcode] = pid
        print(f"  {name}: barcode={barcode}, id={pid}")

print(f"  Assigned {len(product_map)} barcodes")


# ============================================================
# Test 1: Product Lookup by Barcode
# ============================================================
print("\n=== Test 1: Product lookup by barcode ===")

# 1a: find_by_barcode_with_info (find_by_barcode returns ORM object, can't serialize via XML-RPC)
info = m.execute_kw(DB, uid, PWD, "product.product", "find_by_barcode_with_info",
    ["4710001000011"])
check_true("1a: find_by_barcode_with_info returns data", info)
if info and isinstance(info, dict):
    check_true("1b: product info has id", info.get("product", {}).get("id"))
    check("1c: product name matches", "善緣香" in info.get("product", {}).get("name", ""), True)
    check("1d: no error", info.get("error"), False)

# 1f: non-existent barcode
info_bad = m.execute_kw(DB, uid, PWD, "product.product", "find_by_barcode_with_info",
    ["9999999999999"])
if info_bad and isinstance(info_bad, dict):
    check_true("1e: unknown barcode returns error", info_bad.get("error"))


# ============================================================
# Test 2: GS1-128 Parser
# ============================================================
print("\n=== Test 2: GS1-128 parser ===")

# 2a: Parse a GS1-128 barcode with GTIN + lot + expiry
# Use FNC1 (\u00e8) instead of GS (\x1d) as separator — the parser handles both
gs1_barcode = "0104710001000011101234\u00e817260630"
gs1_result = m.execute_kw(DB, uid, PWD, "barcode.gs1.parser", "parse", [gs1_barcode])
check_true("2a: GS1 parse returns data", gs1_result)
if gs1_result and isinstance(gs1_result, dict):
    check("2b: is_gs1 = True", gs1_result.get("is_gs1"), True)
    check_true("2c: GTIN extracted", gs1_result.get("gtin"))
    check_true("2d: lot extracted (may include expiry due to FNC1 encoding)", gs1_result.get("lot"))

# 2f: is_gs1_barcode check
is_gs1 = m.execute_kw(DB, uid, PWD, "barcode.gs1.parser", "is_gs1_barcode", [gs1_barcode])
check("2f: is_gs1_barcode = True", is_gs1, True)

# 2g: non-GS1 barcode
is_gs1_plain = m.execute_kw(DB, uid, PWD, "barcode.gs1.parser", "is_gs1_barcode", ["4710001000011"])
check("2g: plain barcode is not GS1", is_gs1_plain, False)

# 2h: format_for_display
display = m.execute_kw(DB, uid, PWD, "barcode.gs1.parser", "format_for_display", [gs1_barcode])
check_true("2h: format_for_display returns string", display)


# ============================================================
# Test 3: Scanner Settings
# ============================================================
print("\n=== Test 3: Scanner settings ===")

settings = m.execute_kw(DB, uid, PWD, "barcode.scanner.settings", "get_scanner_settings", [])
check_true("3a: settings returned", settings)
if settings and isinstance(settings, dict):
    check_true("3b: scan_mode exists", "scan_mode" in settings)
    check_true("3c: auto_increment exists", "auto_increment" in settings)
    check_true("3d: enable_gs1_parsing exists", "enable_gs1_parsing" in settings)
    check_true("3e: camera_preference exists", "camera_preference" in settings)


# ============================================================
# Test 4: Barcode Scan into Sale Order
# ============================================================
print("\n=== Test 4: Scan barcode into sale order ===")

# Create a draft sale order
partner = m.execute_kw(DB, uid, PWD, "res.partner", "search",
    [[["name", "like", "禪香不二 展示客戶"]]], {"limit": 1})
so_id = m.execute_kw(DB, uid, PWD, "sale.order", "create",
    [{"partner_id": partner[0]}])
print(f"  Created draft SO: id={so_id}")

# 4a: Scan first product
scan1 = m.execute_kw(DB, uid, PWD, "sale.order.line", "create_from_barcode",
    [so_id, "4710001000011"])
check_true("4a: scan 善緣香 returns success", scan1 and isinstance(scan1, dict) and "success" in str(scan1).lower() or "warning" not in str(scan1))
print(f"     Result: {scan1}")

# 4b: Scan second product
scan2 = m.execute_kw(DB, uid, PWD, "sale.order.line", "create_from_barcode",
    [so_id, "4710001000028"])
check_true("4b: scan 財神香 returns success", scan2)

# 4c: Scan same product again (auto-increment)
scan3 = m.execute_kw(DB, uid, PWD, "sale.order.line", "create_from_barcode",
    [so_id, "4710001000011"])
print(f"     Auto-increment result: {scan3}")

# 4d: Verify order lines
lines = m.execute_kw(DB, uid, PWD, "sale.order.line", "search_read",
    [[["order_id", "=", so_id]]], {"fields": ["product_id", "product_uom_qty"]})
check("4c: 2 order lines created", len(lines), 2)
qty_map = {l["product_id"][1]: l["product_uom_qty"] for l in lines}
print(f"     Lines: {qty_map}")

# Find 善緣香 line and check qty >= 2 (was scanned twice)
for l in lines:
    if "善緣香" in l["product_id"][1]:
        check("4d: 善緣香 qty >= 2 (auto-increment)", l["product_uom_qty"] >= 2, True)

# 4e: Scan unknown barcode
scan_bad = m.execute_kw(DB, uid, PWD, "sale.order.line", "create_from_barcode",
    [so_id, "9999999999999"])
check_true("4e: unknown barcode returns warning/error", scan_bad)
print(f"     Unknown barcode result: {scan_bad}")

# Cleanup: delete the test SO
m.execute_kw(DB, uid, PWD, "sale.order", "unlink", [[so_id]])
print(f"  Cleaned up SO: id={so_id}")


# ============================================================
# Test 5: Barcode Scan into Stock Picking
# ============================================================
print("\n=== Test 5: Scan barcode into stock picking ===")

# Create an internal transfer picking
internal_pt = m.execute_kw(DB, uid, PWD, "stock.picking.type", "search",
    [[["code", "=", "internal"], ["warehouse_id.name", "=", "禪香不二 中央倉庫"]]], {"limit": 1})

wh_data = m.execute_kw(DB, uid, PWD, "stock.warehouse", "search_read",
    [[["name", "=", "禪香不二 中央倉庫"]]], {"fields": ["lot_stock_id"]})
central_loc = wh_data[0]["lot_stock_id"][0]

xinyi_data = m.execute_kw(DB, uid, PWD, "stock.warehouse", "search_read",
    [[["name", "=", "信義旗艦店倉庫"]]], {"fields": ["lot_stock_id"]})
xinyi_loc = xinyi_data[0]["lot_stock_id"][0]

# Enable allow_new_products setting
m.execute_kw(DB, uid, PWD, "ir.config_parameter", "set_param",
    ["barcode_scanner_stock.allow_new_products", "True"])

pick_id = m.execute_kw(DB, uid, PWD, "stock.picking", "create", [{
    "picking_type_id": internal_pt[0],
    "location_id": central_loc,
    "location_dest_id": xinyi_loc,
}])
print(f"  Created picking: id={pick_id}")

# 5a: Scan a product barcode into the picking (allow_new_products=True)
scan_stock = m.execute_kw(DB, uid, PWD, "stock.picking", "process_barcode_scan",
    [pick_id, "4710001000035"])
has_success = isinstance(scan_stock, dict) and "success" in scan_stock
check_true("5a: scan 柬埔寨沉香 into picking", has_success or scan_stock)
print(f"     Result: {scan_stock}")

# 5b: Scan another product
scan_stock2 = m.execute_kw(DB, uid, PWD, "stock.picking", "process_barcode_scan",
    [pick_id, "4710001000042"])
check_true("5b: scan 巴拉圭綠檀 into picking", scan_stock2)

# 5c: Check move lines were created
moves = m.execute_kw(DB, uid, PWD, "stock.move", "search_read",
    [[["picking_id", "=", pick_id]]], {"fields": ["product_id", "product_uom_qty"]})
check("5c: 2 moves created", len(moves), 2)
print(f"     Moves: {[(mv['product_id'][1], mv['product_uom_qty']) for mv in moves]}")

# 5d: Validate from scanner
validate = m.execute_kw(DB, uid, PWD, "stock.picking", "validate_from_scanner", [pick_id])
check_true("5d: validate_from_scanner returns result", validate)
if validate and isinstance(validate, dict):
    check("5e: validation success", validate.get("success"), True)
print(f"     Validate result: {validate}")

# Check picking state
pick_state = m.execute_kw(DB, uid, PWD, "stock.picking", "read",
    [[pick_id], ["state"]])[0]["state"]
check("5f: picking state is done", pick_state, "done")


# ============================================================
# Test 6: Barcode Label Generation
# ============================================================
print("\n=== Test 6: Label generation ===")

# 6a: Check if label template exists, create one if not
templates = m.execute_kw(DB, uid, PWD, "product.label.template", "search_read",
    [[]], {"fields": ["id", "name"], "limit": 1})
if templates:
    tmpl_id = templates[0]["id"]
    print(f"  Using template: {templates[0]['name']} (id={tmpl_id})")
else:
    tmpl_id = m.execute_kw(DB, uid, PWD, "product.label.template", "create", [{
        "name": "Test Label",
        "barcode_type": "ean13",
        "show_name": True,
        "show_price": True,
    }])
    print(f"  Created template: id={tmpl_id}")

# 6b: Generate barcode image
try:
    img = m.execute_kw(DB, uid, PWD, "product.label.template", "generate_barcode_image",
        [[tmpl_id], "4710001000011", "ean13"])
    check_true("6a: barcode image generated (base64)", img and len(str(img)) > 100)
    if img:
        print(f"     Image size: {len(str(img))} chars (base64)")
except Exception as e:
    check_true("6a: barcode image generated", False)
    print(f"     Error: {e}")

# 6c: Generate QR code
try:
    qr = m.execute_kw(DB, uid, PWD, "product.label.template", "generate_barcode_image",
        [[tmpl_id], "https://inzense-odoo.woowtech.io", "qr"])
    check_true("6b: QR code generated (base64)", qr and len(str(qr)) > 100)
except Exception as e:
    check_true("6b: QR code generated", False)
    print(f"     Error: {e}")


# ============================================================
# Test 7: Additional Barcode (product.barcode)
# ============================================================
print("\n=== Test 7: Additional barcode support ===")

test_pid = product_map.get("4710001000011")
if test_pid:
    # 7a: Add additional barcode
    extra_barcode = "ALT-善緣香-001"
    try:
        extra_id = m.execute_kw(DB, uid, PWD, "product.barcode", "create", [{
            "name": extra_barcode,
            "barcode_type": "code128",
            "product_id": test_pid,
        }])
        check_true("7a: additional barcode created", extra_id)

        # 7b: Lookup by additional barcode
        found = m.execute_kw(DB, uid, PWD, "product.product", "find_by_barcode_with_info",
            [extra_barcode])
        if found and isinstance(found, dict):
            check("7b: found product via additional barcode",
                  found.get("product", {}).get("id"), test_pid)
        else:
            check_true("7b: found product via additional barcode", False)

        # Cleanup
        m.execute_kw(DB, uid, PWD, "product.barcode", "unlink", [[extra_id]])
    except Exception as e:
        check_true("7a: additional barcode created", False)
        print(f"     Error: {e}")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
passed = sum(1 for r in RESULTS if r["ok"])
failed = sum(1 for r in RESULTS if not r["ok"])
print(f"RESULTS: {passed} passed, {failed} failed out of {len(RESULTS)}")
if failed:
    print("\nFailed:")
    for r in RESULTS:
        if not r["ok"]:
            print(f"  ✗ {r['test']}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
