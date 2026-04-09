#!/usr/bin/env python3
"""Remove demo POS configs (服裝店, 麵包店) and related demo data."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Close and delete sessions for demo configs (2=服裝店, 3=麵包店)
print("--- Close demo POS sessions ---")
for cid in [2, 3]:
    sessions = models.execute_kw(db, uid, password, "pos.session", "search", [
        [["config_id", "=", cid]]
    ])
    for sid in sessions:
        try:
            models.execute_kw(db, uid, password, "pos.session", "write", [[sid], {"state": "closed"}])
            models.execute_kw(db, uid, password, "pos.session", "unlink", [[sid]])
        except:
            pass
    if sessions:
        print(f"  Cleaned {len(sessions)} sessions for config {cid}")

# 2. Delete or archive demo POS configs
print("\n--- Remove demo POS configs ---")
for cid in [2, 3]:
    try:
        cfg = models.execute_kw(db, uid, password, "pos.config", "read", [[cid], ["name"]])
        if cfg:
            try:
                models.execute_kw(db, uid, password, "pos.config", "unlink", [[cid]])
                print(f"  Deleted: {cfg[0]['name']}")
            except:
                models.execute_kw(db, uid, password, "pos.config", "write", [[cid], {"active": False}])
                print(f"  Archived: {cfg[0]['name']}")
    except:
        print(f"  Config {cid} already gone")

# 3. Remove demo POS categories
print("\n--- Remove demo POS categories ---")
all_pos_cats = models.execute_kw(db, uid, password, "pos.category", "search_read", [[]],
    {"fields": ["id", "name"]})
our_cats = {"線香", "迷你香", "拜拜用香", "優惠組合"}
for c in all_pos_cats:
    if c["name"] not in our_cats:
        try:
            models.execute_kw(db, uid, password, "pos.category", "unlink", [[c["id"]]])
            print(f"  Deleted: {c['name']}")
        except:
            print(f"  Could not delete: {c['name']}")

# 4. Remove unused payment methods
print("\n--- Clean payment methods ---")
keep = set(models.execute_kw(db, uid, password, "pos.config", "read", [[1], ["payment_method_ids"]])[0]["payment_method_ids"])
all_pm = models.execute_kw(db, uid, password, "pos.payment.method", "search_read", [[]],
    {"fields": ["id", "name"]})
for pm in all_pm:
    if pm["id"] not in keep:
        try:
            models.execute_kw(db, uid, password, "pos.payment.method", "unlink", [[pm["id"]]])
            print(f"  Deleted: {pm['name']}")
        except:
            pass

# 5. Verify
print("\n=== Final State ===")
configs = models.execute_kw(db, uid, password, "pos.config", "search_read", [
    [["active", "in", [True, False]]]
], {"fields": ["id", "name", "active"], "context": {"active_test": False}})
for c in configs:
    print(f"  POS: {c['name']} active={c['active']}")

cats = models.execute_kw(db, uid, password, "pos.category", "search_read", [[]],
    {"fields": ["name"]})
print(f"  POS Categories: {[c['name'] for c in cats]}")

count = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["available_in_pos", "=", True]]
])
print(f"  Products in POS: {count}")
