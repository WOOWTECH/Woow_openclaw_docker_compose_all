#!/usr/bin/env python3
"""Fix the last remaining 公司名稱 in footer copyright."""
import xmlrpc.client

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Find ALL views containing 公司名稱
views = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["arch", "like", "公司名稱"]]
], {"fields": ["id", "key", "name"], "limit": 50})
print(f"Views with 公司名稱: {len(views)}")

for v in views:
    vdata = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[v["id"]], ["arch"]])
    new_arch = vdata[0]["arch"].replace("公司名稱", "禪香不二 Inzense")
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[v["id"]], {"arch": new_arch}])
    print(f"  Fixed: ID={v['id']} {v.get('key') or v.get('name')}")

# Verify
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/about-us")
html = resp.read().decode()
still_has = "公司名稱" in html
print(f"\nStill has 公司名稱: {still_has}")
if still_has:
    import re
    idx = html.find("公司名稱")
    ctx = re.sub(r'\s+', ' ', html[max(0,idx-80):idx+80])
    print(f"  Context: {ctx}")
