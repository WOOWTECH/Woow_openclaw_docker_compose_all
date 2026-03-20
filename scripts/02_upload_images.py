#!/usr/bin/env python3
"""Phase 2: Upload all images to Odoo as ir.attachment records."""
import xmlrpc.client
import base64
import os
import json
import mimetypes

url = "http://localhost:8069"
db = "inzense"
uid_val = None
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid_val = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

IMAGE_DIR = "/tmp/inzense-images"
mapping = {}

mime_map = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}

for filename in sorted(os.listdir(IMAGE_DIR)):
    filepath = os.path.join(IMAGE_DIR, filename)
    if not os.path.isfile(filepath):
        continue

    ext = os.path.splitext(filename)[1].lower()
    mimetype = mime_map.get(ext, "application/octet-stream")
    if mimetype == "application/octet-stream":
        continue

    # Check if already uploaded
    existing = models.execute_kw(db, uid_val, password, "ir.attachment", "search", [
        [["name", "=", f"inzense_{filename}"]]
    ])
    if existing:
        mapping[filename] = existing[0]
        print(f"SKIP (exists): {filename} -> ID={existing[0]}")
        continue

    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    size_kb = os.path.getsize(filepath) / 1024
    att_id = models.execute_kw(db, uid_val, password, "ir.attachment", "create", [{
        "name": f"inzense_{filename}",
        "datas": data,
        "type": "binary",
        "mimetype": mimetype,
        "public": True,
        "res_model": "ir.ui.view",
        "res_id": 0,
    }])
    mapping[filename] = att_id
    print(f"UPLOAD: {filename} ({size_kb:.0f}KB) -> ID={att_id}")

# Save mapping
with open("/tmp/inzense-image-mapping.json", "w") as f:
    json.dump(mapping, f, indent=2)

print(f"\n=== Uploaded {len(mapping)} images ===")
print(f"Mapping saved to /tmp/inzense-image-mapping.json")

# Print mapping for reference
for k, v in mapping.items():
    print(f"  {k}: /web/image/{v}")
