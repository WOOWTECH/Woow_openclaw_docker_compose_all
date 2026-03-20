#!/usr/bin/env python3
"""Fix blog.blog cover_properties to show workshop photo as banner."""
import xmlrpc.client
import json
import re
import urllib.request

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Check current state
blog = models.execute_kw(db, uid, password, "blog.blog", "read", [[3], ["name", "cover_properties"]])
print(f"Blog: {blog[0]['name']}")
print(f"Current cover: {blog[0]['cover_properties']}")

# Set cover_properties on the blog.blog record (NOT blog.post)
workshop_id = 5697
cover_props = json.dumps({
    "background-image": f"url('/web/image/{workshop_id}')",
    "resize_class": "o_record_has_cover cover_auto",
    "opacity": "0.4",
})

models.execute_kw(db, uid, password, "blog.blog", "write", [[3], {
    "cover_properties": cover_props,
}])
print(f"Set blog cover: /web/image/{workshop_id}")

# Verify rendered page
resp = urllib.request.urlopen("http://localhost:8069/blog/xiang-pin-xue-tang-3")
html = resp.read().decode()

cover_div = re.search(r'o_record_cover_image[^>]*style="([^"]*)"', html)
if cover_div:
    style = cover_div.group(1)
    has_image = "/web/image/" in style and "none" not in style
    print(f"Rendered cover style: {style[:100]}")
    print(f"Has actual image: {has_image}")
else:
    print("No cover image div found")

# Also check if the cover container has the right classes
cover_container = re.search(r'o_record_cover_container[^>]*class="([^"]*)"', html)
if cover_container:
    classes = cover_container.group(1)
    has_cover_class = "o_record_has_cover" in classes
    print(f"Cover classes: {classes[:150]}")
    print(f"Has o_record_has_cover: {has_cover_class}")
