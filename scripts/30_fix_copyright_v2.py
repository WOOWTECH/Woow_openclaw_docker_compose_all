#!/usr/bin/env python3
import xmlrpc.client
url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

new_arch = '<data inherit_id="website.layout">\n'
new_arch += '    <xpath expr="//footer//span[hasclass(\'o_footer_copyright_name\')]" position="replace">\n'
new_arch += '        <span class="o_footer_copyright_name me-2">Copyright &#169; 2024 &#31146;&#39321;&#19981;&#20108; Inzense</span>\n'
new_arch += '    </xpath>\n'
new_arch += '</data>'

models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1370], {"arch": new_arch}])
print("Updated view 1370")

import urllib.request, re
resp = urllib.request.urlopen("http://localhost:8069/about-us")
html = resp.read().decode()
idx = html.find("o_footer_copyright_name")
if idx > 0:
    ctx = re.sub(r'\s+', ' ', html[idx:idx+200])
    print(f"Copyright: {ctx[:150]}")
still = "公司名稱" in html or "Company name" in html
print(f"Still has placeholder: {still}")
