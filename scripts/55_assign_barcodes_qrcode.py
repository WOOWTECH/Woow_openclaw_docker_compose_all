#!/usr/bin/env python3
"""
Phase 55: Assign EAN-13 barcodes, internal references, and QR codes to all products.
Runs inside the Odoo pod.

Barcode format: 471 (Taiwan) + 0001 (Inzense) + 5-digit sequential + 1 check digit
Internal ref:   INZ-001 ~ INZ-NNN
QR Code:        Generated via product.label.template and stored as ir.attachment
"""
import xmlrpc.client

URL = "http://localhost:8069"
DB = "inzense"
PWD = "admin"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, "admin", PWD, {})
assert uid, "Auth failed"
m = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
print(f"Connected as uid={uid}")


# ================================================================
# EAN-13 check digit calculator
# ================================================================
def ean13_check_digit(code12):
    """Calculate EAN-13 check digit for a 12-digit string."""
    assert len(code12) == 12 and code12.isdigit(), f"Need 12 digits, got: {code12}"
    total = 0
    for i, ch in enumerate(code12):
        total += int(ch) * (1 if i % 2 == 0 else 3)
    return str((10 - (total % 10)) % 10)


def make_ean13(seq):
    """Generate EAN-13 barcode for sequential number.
    Format: 471 + 0001 + 5-digit seq + check digit
    """
    code12 = f"471000{seq:06d}"
    return code12 + ean13_check_digit(code12)


# ================================================================
# STEP 1: Get all products (sorted by id for stable ordering)
# ================================================================
print("\n" + "=" * 60)
print("STEP 1: Fetch all products")
print("=" * 60)

# Get all product variants (product.product) that are our incense products
all_products = m.execute_kw(DB, uid, PWD, "product.product", "search_read", [
    ["|", "|", "|", "|", "|", "|", "|",
     ["name", "ilike", "線香"],
     ["name", "ilike", "迷你香"],
     ["name", "ilike", "香品"],
     ["name", "ilike", "系列"],
     ["name", "ilike", "組合"],
     ["name", "ilike", "沉香"],
     ["name", "ilike", "檀香"],
     ["name", "ilike", "香"],
    ]
], {"fields": ["id", "name", "barcode", "default_code"], "order": "id asc", "limit": 500})

# Deduplicate by name (keep first occurrence)
seen_names = set()
products = []
for p in all_products:
    if p["name"] not in seen_names:
        seen_names.add(p["name"])
        products.append(p)

print(f"Found {len(products)} unique products")


# ================================================================
# STEP 2: Assign barcodes and internal references
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Assign EAN-13 barcodes and internal references")
print("=" * 60)

# Collect already-used barcodes to avoid conflicts
used_barcodes = set()
for p in products:
    if p["barcode"]:
        used_barcodes.add(p["barcode"])

assigned = 0
skipped = 0
seq = 1

# Track mapping for report
mapping = []

for p in products:
    pid = p["id"]
    name = p["name"]

    # Generate barcode
    barcode = make_ean13(seq)
    # Skip if this barcode is already used by another product
    while barcode in used_barcodes:
        seq += 1
        barcode = make_ean13(seq)

    # Internal reference
    default_code = f"INZ-{seq:03d}"

    # Check if product already has correct barcode and ref
    if p["barcode"] and p["default_code"]:
        # Already has both, keep existing
        mapping.append({
            "id": pid,
            "name": name,
            "barcode": p["barcode"],
            "default_code": p["default_code"],
            "status": "existing",
        })
        skipped += 1
        seq += 1
        continue

    # Write barcode and internal reference
    update_vals = {}
    if not p["barcode"]:
        update_vals["barcode"] = barcode
    else:
        barcode = p["barcode"]  # keep existing

    if not p["default_code"]:
        update_vals["default_code"] = default_code
    else:
        default_code = p["default_code"]  # keep existing

    if update_vals:
        try:
            m.execute_kw(DB, uid, PWD, "product.product", "write", [[pid], update_vals])
            assigned += 1
            mapping.append({
                "id": pid,
                "name": name,
                "barcode": barcode,
                "default_code": default_code,
                "status": "assigned",
            })
        except Exception as e:
            print(f"  ERROR writing product {pid} ({name[:30]}): {e}")
            mapping.append({
                "id": pid,
                "name": name,
                "barcode": barcode,
                "default_code": default_code,
                "status": f"error: {e}",
            })
    else:
        mapping.append({
            "id": pid,
            "name": name,
            "barcode": barcode,
            "default_code": default_code,
            "status": "existing",
        })
        skipped += 1

    used_barcodes.add(barcode)
    seq += 1

print(f"\nAssigned: {assigned}")
print(f"Skipped (already had barcode+ref): {skipped}")


# ================================================================
# STEP 3: Generate QR Codes via product.label.template
# ================================================================
print("\n" + "=" * 60)
print("STEP 3: Generate QR Codes")
print("=" * 60)

# Ensure label template exists
templates = m.execute_kw(DB, uid, PWD, "product.label.template", "search_read",
    [[["name", "=", "Inzense QR Label"]]], {"fields": ["id"], "limit": 1})

if templates:
    tmpl_id = templates[0]["id"]
    print(f"  Using existing template: id={tmpl_id}")
else:
    try:
        tmpl_id = m.execute_kw(DB, uid, PWD, "product.label.template", "create", [{
            "name": "Inzense QR Label",
            "barcode_type": "qr",
            "show_product_name": True,
            "show_price": True,
            "show_internal_ref": True,
        }])
        print(f"  Created template: id={tmpl_id}")
    except Exception as e:
        print(f"  WARNING: Could not create label template: {e}")
        tmpl_id = None

qr_generated = 0
qr_errors = 0

if tmpl_id:
    for item in mapping:
        if item["status"].startswith("error"):
            continue

        barcode = item["barcode"]
        name = item["name"]
        pid = item["id"]

        try:
            # Generate QR code image (base64 PNG)
            qr_img = m.execute_kw(DB, uid, PWD, "product.label.template",
                "generate_barcode_image", [[tmpl_id], barcode, "qr"])

            if qr_img and len(str(qr_img)) > 100:
                # Store as ir.attachment linked to the product
                # Check if attachment already exists
                existing_att = m.execute_kw(DB, uid, PWD, "ir.attachment", "search", [
                    [["name", "=", f"QR-{barcode}"],
                     ["res_model", "=", "product.product"],
                     ["res_id", "=", pid]]
                ])
                if not existing_att:
                    m.execute_kw(DB, uid, PWD, "ir.attachment", "create", [{
                        "name": f"QR-{barcode}",
                        "datas": qr_img if isinstance(qr_img, str) else str(qr_img),
                        "type": "binary",
                        "mimetype": "image/png",
                        "res_model": "product.product",
                        "res_id": pid,
                        "public": True,
                    }])
                qr_generated += 1
            else:
                qr_errors += 1
        except Exception as e:
            qr_errors += 1
            if qr_errors <= 3:
                print(f"  QR error for {name[:30]}: {e}")
            elif qr_errors == 4:
                print(f"  ... suppressing further QR errors")

    print(f"\nQR codes generated: {qr_generated}")
    if qr_errors:
        print(f"QR errors: {qr_errors}")
else:
    print("  Skipping QR generation (no label template available)")


# ================================================================
# STEP 4: Print complete mapping report
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Complete Barcode Mapping Report")
print("=" * 60)
print(f"\n{'No.':<5} {'Internal Ref':<10} {'EAN-13 Barcode':<16} {'Status':<10} {'Product Name'}")
print("-" * 90)

for i, item in enumerate(mapping, 1):
    print(f"{i:<5} {item['default_code']:<10} {item['barcode']:<16} {item['status']:<10} {item['name'][:50]}")

# Verify no gaps in sequential numbering
codes = sorted([item["default_code"] for item in mapping if item["default_code"].startswith("INZ-")])
if codes:
    first_num = int(codes[0].split("-")[1])
    last_num = int(codes[-1].split("-")[1])
    expected_count = last_num - first_num + 1
    if expected_count == len(codes):
        print(f"\n  Numbering: INZ-{first_num:03d} ~ INZ-{last_num:03d} — CONTINUOUS (no gaps)")
    else:
        print(f"\n  WARNING: Expected {expected_count} codes but found {len(codes)} — has gaps!")

# Verify no duplicate barcodes
barcodes = [item["barcode"] for item in mapping if item["barcode"]]
if len(barcodes) == len(set(barcodes)):
    print(f"  Barcodes: {len(barcodes)} unique — NO DUPLICATES")
else:
    dupes = [b for b in barcodes if barcodes.count(b) > 1]
    print(f"  WARNING: Duplicate barcodes found: {set(dupes)}")

print(f"\nTotal products: {len(mapping)}")
print("\n=== Phase 55 COMPLETE ===")
