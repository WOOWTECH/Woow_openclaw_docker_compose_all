#!/usr/bin/env python3
"""Fix YourCompany display in blog and hide author company prefix."""
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Clear company_name from ALL partners
partners = models.execute_kw(db, uid, password, "res.partner", "search_read", [
    [["company_name", "ilike", "YourCompany"]]
], {"fields": ["id", "name", "company_name"], "context": {"active_test": False}})
print(f"Partners with YourCompany: {len(partners)}")
for p in partners:
    models.execute_kw(db, uid, password, "res.partner", "write", [[p["id"]], {"company_name": False}])
    print(f"  Cleared: {p['name']} (ID={p['id']})")

# Archive fake partners
fake = models.execute_kw(db, uid, password, "res.partner", "search", [
    [["name", "ilike", "My Company"]]
], {"context": {"active_test": False}})
for fid in fake:
    try:
        models.execute_kw(db, uid, password, "res.partner", "write", [[fid], {"active": False, "name": "禪香不二"}])
    except:
        pass
print(f"Archived {len(fake)} fake company partners")

# Add CSS hide
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search", [
    [["name", "=", "Inzense Custom CSS"]]
])
if css_views:
    cd = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = cd[0]["arch"]
    if "yourcompany-hide" not in arch:
        hide_css = """
/* yourcompany-hide */
.o_record_cover_component .o_not_editable {
    font-size: 0 !important;
    color: transparent !important;
}
.o_record_cover_component .o_not_editable .o_author_avatar_card {
    font-size: 13px !important;
    color: #fff !important;
}
.o_record_cover_component .o_not_editable .o_author_avatar_card ~ * {
    font-size: 13px !important;
    color: #fff !important;
}
"""
        arch = arch.replace("</style>", hide_css + "\n</style>")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
        print("Added CSS hide for author prefix")

# Verify
import urllib.request
resp = urllib.request.urlopen("http://localhost:8069/blog/xiang-pin-xue-tang-3")
html = resp.read().decode()
print(f"\nBlog page: YourCompany in HTML = {'YourCompany' in html}")
print(f"Blog page: size = {len(html)} bytes")
