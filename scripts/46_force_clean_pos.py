#!/usr/bin/env python3
"""Force close ALL POS sessions, then delete demo categories."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Force close ALL sessions
print("--- Force close ALL POS sessions ---")
all_sessions = models.execute_kw(db, uid, password, "pos.session", "search_read", [
    [["state", "!=", "closed"]]
], {"fields": ["id", "name", "state", "config_id"]})
print(f"Open sessions: {len(all_sessions)}")
for s in all_sessions:
    print(f"  {s['name']}: {s['state']} -> closing...")
    try:
        # Try normal close
        models.execute_kw(db, uid, password, "pos.session", "action_pos_session_closing_control", [[s["id"]]])
        models.execute_kw(db, uid, password, "pos.session", "action_pos_session_validate", [[s["id"]]])
        print("    closed normally")
    except:
        try:
            # Force state change
            models.execute_kw(db, uid, password, "pos.session", "write", [[s["id"]], {"state": "closed"}])
            print("    force closed")
        except Exception as e:
            print(f"    error: {str(e)[:60]}")

# Also clear current_session_id on config
try:
    models.execute_kw(db, uid, password, "pos.config", "write", [[1], {"current_session_id": False}])
except:
    pass

# 2. Delete demo POS categories
print("\n--- Delete demo POS categories ---")
our_cats = {"線香", "迷你香", "拜拜用香", "優惠組合"}
demo_cats = models.execute_kw(db, uid, password, "pos.category", "search_read", [
    [["name", "not in", list(our_cats)]]
], {"fields": ["id", "name"]})

for c in demo_cats:
    # Unlink from all products
    prods = models.execute_kw(db, uid, password, "product.template", "search", [
        [["pos_categ_ids", "in", [c["id"]]]]
    ])
    for pid in prods:
        models.execute_kw(db, uid, password, "product.template", "write", [[pid], {
            "pos_categ_ids": [(3, c["id"])]
        }])
    try:
        models.execute_kw(db, uid, password, "pos.category", "unlink", [[c["id"]]])
        print(f"  Deleted: {c['name']}")
    except Exception as e:
        print(f"  Failed: {c['name']}: {str(e)[:80]}")

# 3. Verify
print("\n=== Result ===")
remaining = models.execute_kw(db, uid, password, "pos.category", "search_read", [[]],
    {"fields": ["name"]})
print(f"POS categories: {[c['name'] for c in remaining]}")
configs = models.execute_kw(db, uid, password, "pos.config", "search_read", [[]],
    {"fields": ["name"]})
print(f"POS configs: {[c['name'] for c in configs]}")
