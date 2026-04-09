#!/usr/bin/env python3
"""Remove demo POS categories by first unlinking products."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

our_cats = {"線香", "迷你香", "拜拜用香", "優惠組合"}
demo_cats = models.execute_kw(db, uid, password, "pos.category", "search_read", [
    [["name", "not in", list(our_cats)]]
], {"fields": ["id", "name"]})

for c in demo_cats:
    # Unlink from products
    prods = models.execute_kw(db, uid, password, "product.template", "search", [
        [["pos_categ_ids", "in", [c["id"]]]]
    ])
    for pid in prods:
        models.execute_kw(db, uid, password, "product.template", "write", [[pid], {
            "pos_categ_ids": [(3, c["id"])]
        }])
    # Delete
    try:
        models.execute_kw(db, uid, password, "pos.category", "unlink", [[c["id"]]])
        print(f"Deleted: {c['name']} (removed from {len(prods)} products)")
    except Exception as e:
        print(f"Can't delete {c['name']}: {e}")

remaining = models.execute_kw(db, uid, password, "pos.category", "search_read", [[]],
    {"fields": ["name"]})
print(f"\nPOS categories: {[c['name'] for c in remaining]}")
configs = models.execute_kw(db, uid, password, "pos.config", "search_read", [[]],
    {"fields": ["name"]})
print(f"POS configs: {[c['name'] for c in configs]}")
