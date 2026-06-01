#!/usr/bin/env python3
"""
Phase 57: Sync all 3 category systems to the same hierarchy.

Ensures product.category (internal), pos.category (POS), and
product.public.category (eCommerce) all follow the same structure:

  主類別 (系列): 功能/特色/脈輪/五行/檀香/沉香/台灣/外國/降真/神明
  次類別 (產品型態): 長線香/迷你香/拜拜用香/盤香

Runs inside the Odoo pod or with port-forward.
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

SERIES = [
    "功能系列", "特色系列", "脈輪系列", "五行系列", "檀香系列",
    "沉香系列", "台灣系列", "外國系列", "降真系列", "神明系列",
]
PRODUCT_TYPES = ["長線香", "迷你香", "拜拜用香", "盤香"]

# default_code prefix -> series
CODE_TO_SERIES = {
    "LIE": "功能系列", "MIE": "功能系列",
    "LID": "特色系列", "MID": "特色系列",
    "LIC": "脈輪系列", "MIC": "脈輪系列",
    "LIFE": "五行系列", "MIFE": "五行系列",
    "LIS": "檀香系列", "MIS": "檀香系列",
    "LIA": "沉香系列", "MIA": "沉香系列",
    "LIT": "台灣系列", "MIT": "台灣系列",
    "LIF": "外國系列", "MIF": "外國系列",
    "LIAP": "降真系列", "MIAP": "降真系列",
    "LIG": "神明系列", "MIG": "神明系列",
    "IS01": "檀香系列", "IS02": "檀香系列", "IS04": "檀香系列", "IS05": "檀香系列",
    "IS03": "降真系列",
    "IS06": "沉香系列", "IS07": "沉香系列", "IS08": "沉香系列", "IS09": "沉香系列",
    "ICAP": "降真系列", "ICS": "檀香系列", "ICA": "沉香系列",
}

def get_series(code, name):
    if code:
        for prefix in sorted(CODE_TO_SERIES.keys(), key=len, reverse=True):
            if code.startswith(prefix):
                return CODE_TO_SERIES[prefix]
    if "尤加利" in name:
        return "外國系列"
    return None

def get_product_type(name):
    if name.startswith("長線香"):
        return "長線香"
    elif name.startswith("迷你香"):
        return "迷你香"
    elif name.startswith("拜拜用香"):
        return "拜拜用香"
    elif name.startswith("盤香"):
        return "盤香"
    return None


def get_or_create(model, name, parent_id=False, extra=None):
    domain = [["name", "=", name]]
    if parent_id:
        domain.append(["parent_id", "=", parent_id])
    else:
        domain.append(["parent_id", "=", False])
    ids = m.execute_kw(DB, uid, PWD, model, "search", [domain], {"limit": 1})
    if ids:
        return ids[0]
    vals = {"name": name}
    if parent_id:
        vals["parent_id"] = parent_id
    if extra:
        vals.update(extra)
    return m.execute_kw(DB, uid, PWD, model, "create", [vals])


# ================================================================
# PART A: product.category (內部分類)
# ================================================================
print("\n" + "=" * 60)
print("PART A: Rebuild product.category (internal)")
print("=" * 60)

# Keep 'All' (id=1) as root. Create our hierarchy under a 'Inzense' parent.
# First find or create the Inzense root
inzense_root = get_or_create("product.category", "禪香不二 Inzense")
print(f"  Inzense root: id={inzense_root}")

# Create series under Inzense
int_series = {}
for sn in SERIES:
    int_series[sn] = get_or_create("product.category", sn, inzense_root)

# Create product types under each series
int_sub = {}
for sn in SERIES:
    for pt in PRODUCT_TYPES:
        int_sub[(sn, pt)] = get_or_create("product.category", pt, int_series[sn])

# Create combo category
int_combo = get_or_create("product.category", "優惠組合", inzense_root)

print(f"  Created/found {len(int_series)} series + {len(int_sub)} sub + combo")

# First reassign ALL products to new categories, then clean up old ones
print("  Reassigning products first...")
all_products = m.execute_kw(DB, uid, PWD, "product.template", "search_read", [
    [["sale_ok", "=", True]]
], {"fields": ["id", "name", "default_code"], "order": "id asc", "limit": 500})

int_assigned = 0
for prod in all_products:
    series = get_series(prod["default_code"] or "", prod["name"])
    pt = get_product_type(prod["name"])

    if series and pt and (series, pt) in int_sub:
        target = int_sub[(series, pt)]
    elif series and series in int_series:
        target = int_series[series]
    elif "組" in prod["name"]:
        target = int_combo
    else:
        target = inzense_root

    m.execute_kw(DB, uid, PWD, "product.template", "write", [[prod["id"]], {
        "categ_id": target,
    }])
    int_assigned += 1

print(f"  Assigned internal categories to {int_assigned} products")

# Now clean up old standalone categories
old_standalone = ["功能系列", "脈輪系列", "五行系列", "優惠組合", "拜拜用香", "年節禮盒"]
for oname in old_standalone:
    old_ids = m.execute_kw(DB, uid, PWD, "product.category", "search", [
        [["name", "=", oname], ["parent_id", "=", False]]
    ])
    if old_ids:
        try:
            m.execute_kw(DB, uid, PWD, "product.category", "unlink", [old_ids])
            print(f"  Removed old standalone: {oname}")
        except Exception as e:
            print(f"  Could not remove {oname}: {e}")

# Also clean up junk under Inzense root (like "123")
junk = m.execute_kw(DB, uid, PWD, "product.category", "search", [
    [["name", "=", "123"]]
])
if junk:
    try:
        m.execute_kw(DB, uid, PWD, "product.category", "unlink", [junk])
        print(f"  Removed junk category: 123")
    except:
        pass

# (Products already reassigned above)


# ================================================================
# PART B: pos.category (POS 分類)
# ================================================================
print("\n" + "=" * 60)
print("PART B: Rebuild pos.category (POS)")
print("=" * 60)

# Clean up _OLD_ categories — can't delete while POS is open, so just clear product links
old_pos = m.execute_kw(DB, uid, PWD, "pos.category", "search", [
    [["name", "like", "_OLD_"]]
])
if old_pos:
    prods_with_old = m.execute_kw(DB, uid, PWD, "product.template", "search", [
        [["pos_categ_ids", "in", old_pos]]
    ])
    if prods_with_old:
        for pid in prods_with_old:
            current = m.execute_kw(DB, uid, PWD, "product.template", "read", [[pid], ["pos_categ_ids"]])[0]
            new_ids = [c for c in current["pos_categ_ids"] if c not in old_pos]
            m.execute_kw(DB, uid, PWD, "product.template", "write", [[pid], {
                "pos_categ_ids": [(6, 0, new_ids)],
            }])
    # Try to delete; if POS session is open, just leave them (harmless)
    try:
        m.execute_kw(DB, uid, PWD, "pos.category", "unlink", [old_pos])
        print(f"  Removed {len(old_pos)} _OLD_ POS categories")
    except Exception as e:
        print(f"  Cannot delete _OLD_ POS categories (POS session open), skipped")

# Get or create series (top-level)
pos_series = {}
for sn in SERIES:
    pos_series[sn] = get_or_create("pos.category", sn)

# Create product type sub-categories under each series
pos_sub = {}
for sn in SERIES:
    for pt in PRODUCT_TYPES:
        pos_sub[(sn, pt)] = get_or_create("pos.category", pt, pos_series[sn])

# Create combo
pos_combo = get_or_create("pos.category", "優惠組合")

print(f"  Created/found {len(pos_series)} series + {len(pos_sub)} sub + combo")

# Reassign all products
pos_assigned = 0
for prod in all_products:
    series = get_series(prod["default_code"] or "", prod["name"])
    pt = get_product_type(prod["name"])

    cat_ids = []
    if series and series in pos_series:
        cat_ids.append(pos_series[series])
    if series and pt and (series, pt) in pos_sub:
        cat_ids.append(pos_sub[(series, pt)])
    if "組" in prod["name"]:
        cat_ids.append(pos_combo)

    if not cat_ids:
        continue

    m.execute_kw(DB, uid, PWD, "product.template", "write", [[prod["id"]], {
        "pos_categ_ids": [(6, 0, cat_ids)],
    }])
    pos_assigned += 1

print(f"  Assigned POS categories to {pos_assigned} products")


# ================================================================
# PART C: Verification report
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION REPORT")
print("=" * 60)

def print_tree(model, label):
    order = "parent_id asc, id asc"
    if model != "product.category":
        order = "parent_id asc, sequence asc, id asc"
    cats = m.execute_kw(DB, uid, PWD, model, "search_read", [
        []
    ], {"fields": ["id", "name", "parent_id"], "order": order})
    top = [c for c in cats if not c["parent_id"]]
    children = [c for c in cats if c["parent_id"]]

    # For product.category, only show Inzense subtree
    if model == "product.category":
        inz = [c for c in top if "Inzense" in c["name"] or "禪香" in c["name"]]
        if inz:
            top = inz

    print(f"\n{label} ({len(top)} top, {len(children)} sub):")
    for t in top:
        print(f"  {t['name']}")
        kids = [c for c in children if c["parent_id"][0] == t["id"]]
        for k in kids:
            grandkids = [c for c in children if c["parent_id"][0] == k["id"]]
            if grandkids:
                print(f"    ├─ {k['name']}")
                for gk in grandkids:
                    print(f"    │   └─ {gk['name']}")
            else:
                print(f"    └─ {k['name']}")

print_tree("product.public.category", "電商分類 (product.public.category)")
print_tree("product.category", "內部分類 (product.category)")
print_tree("pos.category", "POS分類 (pos.category)")

# Sample product check
print(f"\n{'Product':<35} {'Internal':<30} {'POS':<15} {'Public'}")
print("-" * 95)
sample = m.execute_kw(DB, uid, PWD, "product.template", "search_read", [
    [["sale_ok", "=", True]]
], {"fields": ["name", "categ_id", "pos_categ_ids", "public_categ_ids"], "limit": 15, "order": "id asc"})

for p in sample:
    int_name = p["categ_id"][1].split(" / ")[-1] if p["categ_id"] else "-"
    # Get POS category names
    pos_names = []
    if p["pos_categ_ids"]:
        pos_data = m.execute_kw(DB, uid, PWD, "pos.category", "read", [p["pos_categ_ids"], ["name", "parent_id"]])
        pos_names = [d["name"] for d in pos_data if d["parent_id"]]  # show sub only
        if not pos_names:
            pos_names = [d["name"] for d in pos_data]
    # Get public category names
    pub_names = []
    if p["public_categ_ids"]:
        pub_data = m.execute_kw(DB, uid, PWD, "product.public.category", "read", [p["public_categ_ids"], ["name", "parent_id"]])
        pub_names = [d["name"] for d in pub_data if d["parent_id"]]
        if not pub_names:
            pub_names = [d["name"] for d in pub_data]

    print(f"  {p['name'][:33]:<33} {int_name:<28} {','.join(pos_names):<13} {','.join(pub_names)}")

print("\n=== Phase 57 COMPLETE ===")
