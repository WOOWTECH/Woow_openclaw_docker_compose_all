#!/usr/bin/env python3
"""Configure POS: close sessions, rename, add all products."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# 1. Close any open sessions
sessions = models.execute_kw(db, uid, password, "pos.session", "search_read", [
    [["state", "!=", "closed"]]
], {"fields": ["id", "name", "state"]})
print(f"Open sessions: {len(sessions)}")
for s in sessions:
    print(f"  {s['name']}: {s['state']}")
    try:
        if s["state"] == "opened":
            models.execute_kw(db, uid, password, "pos.session", "action_pos_session_closing_control", [[s["id"]]])
        models.execute_kw(db, uid, password, "pos.session", "action_pos_session_validate", [[s["id"]]])
        print("    -> closed")
    except:
        try:
            models.execute_kw(db, uid, password, "pos.session", "write", [[s["id"]], {"state": "closed"}])
            print("    -> force closed")
        except Exception as e:
            print(f"    -> error: {e}")

# 2. Rename
models.execute_kw(db, uid, password, "pos.config", "write", [[1], {"name": "誠品板橋店"}])
print("\nRenamed to 誠品板橋店")

# 3. Remove category restrictions
try:
    models.execute_kw(db, uid, password, "pos.config", "write", [[1], {"limit_categories": False}])
    print("Removed category restrictions")
except Exception as e:
    print(f"Category error: {e}")

# 4. Set all products available_in_pos
templates = models.execute_kw(db, uid, password, "product.template", "search", [
    [["sale_ok", "=", True], ["active", "=", True]]
])
models.execute_kw(db, uid, password, "product.template", "write", [templates, {"available_in_pos": True}])
print(f"{len(templates)} products -> available_in_pos=True")

# 5. Create POS categories + assign
cats = {"線香": None, "迷你香": None, "拜拜用香": None, "優惠組合": None}
for name in cats:
    existing = models.execute_kw(db, uid, password, "pos.category", "search", [[["name", "=", name]]])
    cats[name] = existing[0] if existing else models.execute_kw(db, uid, password, "pos.category", "create", [{"name": name}])

products = models.execute_kw(db, uid, password, "product.template", "search_read", [
    [["available_in_pos", "=", True]]
], {"fields": ["id", "name"]})
for p in products:
    n = p["name"]
    cid = cats["迷你香"] if "迷你香" in n else cats["拜拜用香"] if "拜拜" in n else cats["優惠組合"] if "組" in n else cats["線香"]
    models.execute_kw(db, uid, password, "product.template", "write", [[p["id"]], {"pos_categ_ids": [(4, cid)]}])

count = models.execute_kw(db, uid, password, "product.template", "search_count", [
    [["available_in_pos", "=", True]]
])
print(f"\nResult: 誠品板橋店 with {count} products")
