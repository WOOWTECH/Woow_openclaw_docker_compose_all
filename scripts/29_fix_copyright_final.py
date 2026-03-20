#!/usr/bin/env python3
"""Fix the footer copyright 公司名稱 - find the exact template."""
import xmlrpc.client
import re

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Read the copyright view (ID 1370)
v = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1370], ["arch", "key"]])
print(f"View 1370 key: {v[0]['key']}")
print(f"View 1370 arch:\n{v[0]['arch']}")

# Check if the arch has the literal text or a t-esc expression
arch = v[0]["arch"]

# Replace the company name in the copyright view
# The view likely replaces a placeholder with company name
if "公司名稱" in arch:
    new_arch = arch.replace("公司名稱", "禪香不二 Inzense")
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1370], {"arch": new_arch}])
    print("Fixed view 1370 directly")
else:
    print("View 1370 does not contain 公司名稱 literally")
    # It might use t-esc="res_company.name" or similar
    # Check if it uses a QWeb expression

# The text "版權所有 © 公司名稱" might come from a different source:
# It could be the default snippet content saved when the footer was first generated.
# Let's check the footer_custom view for website_id=1
footer_custom = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["key", "=", "website.footer_custom"], ["website_id", "=", 1]]
], {"fields": ["id", "arch"]})
if footer_custom:
    farch = footer_custom[0]["arch"]
    if "公司名稱" in farch:
        farch = farch.replace("公司名稱", "禪香不二 Inzense")
        models.execute_kw(db, uid, password, "ir.ui.view", "write",
                         [[footer_custom[0]["id"]], {"arch": farch}])
        print("Fixed footer_custom for website 1")

# Also check the global footer_custom (no website_id)
footer_global = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["key", "=", "website.footer_custom"], ["website_id", "=", False]]
], {"fields": ["id", "arch"]})
if footer_global:
    farch = footer_global[0]["arch"]
    if "公司名稱" in farch:
        farch = farch.replace("公司名稱", "禪香不二 Inzense")
        models.execute_kw(db, uid, password, "ir.ui.view", "write",
                         [[footer_global[0]["id"]], {"arch": farch}])
        print("Fixed global footer_custom")

# The copyright text might also be in the main layout view
# Let's search more broadly
all_with = models.execute_kw(db, uid, password, "ir.ui.view", "search_read", [
    [["arch", "like", "公司名稱"], ["active", "=", True]]
], {"fields": ["id", "key", "arch"], "limit": 10, "context": {"active_test": False}})

print(f"\nRemaining views with 公司名稱: {len(all_with)}")
for vv in all_with:
    new_arch = vv["arch"].replace("公司名稱", "禪香不二 Inzense")
    models.execute_kw(db, uid, password, "ir.ui.view", "write", [[vv["id"]], {"arch": new_arch}])
    print(f"  Fixed ID={vv['id']} key={vv.get('key')}")

# Also hide it with CSS as backup
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
if css_views:
    cdata = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    carch = cdata[0]["arch"]
    if "o_footer_copyright_name" not in carch:
        hide_css = """
/* Override copyright text */
.o_footer_copyright_name {
    font-size: 0 !important;
    color: transparent !important;
}
.o_footer_copyright_name::after {
    content: '\\00A9 2024 禪香不二 Inzense. All Rights Reserved.' !important;
    font-size: 12px !important;
    color: #666 !important;
}
"""
        carch = carch.replace("</style>", hide_css + "\n</style>")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": carch}])
        print("\nAdded CSS override for copyright text")

# Verify
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/about-us")
html = resp.read().decode()
print(f"\nFinal check: '公司名稱' in page: {'公司名稱' in html}")
print(f"'禪香不二' in page: {'禪香不二' in html}")
