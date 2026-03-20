#!/usr/bin/env python3
"""
Performance optimization:
1. Compress GIFs → JPEG (extract first frame)
2. Compress oversized course JPEGs
3. Update all page views to reference optimized images
4. Add performance CSS (lazy loading, content-visibility)
"""
import xmlrpc.client
import base64
import io
from PIL import Image

url = "http://localhost:8069"
db = "inzense"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

MAX_WIDTH = 1920
JPEG_QUALITY = 78

def compress_attachment(att_id, att_name):
    """Download attachment, compress, upload as new attachment. Return new ID."""
    # Read the attachment data
    att_data = models.execute_kw(db, uid, password, "ir.attachment", "read",
        [[att_id], ["datas", "mimetype"]])
    if not att_data or not att_data[0]["datas"]:
        print(f"    No data for attachment {att_id}")
        return att_id

    raw = base64.b64decode(att_data[0]["datas"])
    original_size = len(raw)

    # Open with PIL
    img = Image.open(io.BytesIO(raw))

    # For GIFs: extract first frame
    if img.format == "GIF":
        img = img.convert("RGB")

    # For RGBA: convert to RGB
    if img.mode in ("RGBA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg

    # Resize if too large
    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_height = int(img.height * ratio)
        img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

    # Compress to JPEG
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    compressed = buf.getvalue()
    new_size = len(compressed)

    reduction = (1 - new_size / original_size) * 100
    print(f"    {original_size/1024:.0f}KB → {new_size/1024:.0f}KB ({reduction:.0f}% reduction)")

    # Create new optimized attachment
    new_name = f"opt_{att_name.replace('.gif', '.jpg').replace('.png', '.jpg')}"
    # Check if already exists
    existing = models.execute_kw(db, uid, password, "ir.attachment", "search",
        [[["name", "=", new_name]]])
    if existing:
        # Update existing
        models.execute_kw(db, uid, password, "ir.attachment", "write", [existing, {
            "datas": base64.b64encode(compressed).decode(),
        }])
        print(f"    Updated existing: {new_name} ID={existing[0]}")
        return existing[0]

    new_id = models.execute_kw(db, uid, password, "ir.attachment", "create", [{
        "name": new_name,
        "datas": base64.b64encode(compressed).decode(),
        "type": "binary",
        "mimetype": "image/jpeg",
        "public": True,
        "res_model": "ir.ui.view",
        "res_id": 0,
    }])
    print(f"    Created: {new_name} ID={new_id}")
    return new_id


# ================================================================
# STEP 1: Compress the two huge GIFs
# ================================================================
print("=" * 60)
print("STEP 1: Compress GIF animations → JPEG")
print("=" * 60)

print("  Processing video-sequence.gif (ID=1638, ~28MB)...")
new_1638 = compress_attachment(1638, "video-sequence.gif")

print("  Processing incense-animation.gif (ID=1633, ~3.4MB)...")
new_1633 = compress_attachment(1633, "incense-animation.gif")

# ================================================================
# STEP 2: Compress oversized course JPEGs
# ================================================================
print("\n" + "=" * 60)
print("STEP 2: Compress course photos")
print("=" * 60)

course_images = {
    5697: "course-incense-workshop.jpg",
    5698: "course-tea-ceremony.jpg",
    5699: "course-incense-ceremony.jpg",
    5700: "course-multi-sensory.jpg",
}

new_course_ids = {}
for att_id, name in course_images.items():
    print(f"  Processing {name} (ID={att_id})...")
    new_id = compress_attachment(att_id, name)
    new_course_ids[att_id] = new_id

# ================================================================
# STEP 3: Update all page views to use compressed images
# ================================================================
print("\n" + "=" * 60)
print("STEP 3: Update page references")
print("=" * 60)

# Build replacement map: old_id -> new_id
replacements = {
    str(1638): str(new_1638),
    str(1633): str(new_1633),
}
for old_id, new_id in new_course_ids.items():
    if new_id != old_id:
        replacements[str(old_id)] = str(new_id)

print(f"  Replacement map: {replacements}")

# Update homepage (view 1303)
hp = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[1303], ["arch"]])
if hp:
    arch = hp[0]["arch"]
    changed = False
    for old_id, new_id in replacements.items():
        old_ref = f"/web/image/{old_id}"
        new_ref = f"/web/image/{new_id}"
        if old_ref in arch:
            arch = arch.replace(old_ref, new_ref)
            changed = True
            print(f"    Homepage: {old_ref} → {new_ref}")
    if changed:
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[1303], {"arch": arch}])

# Update about page
about_pages = models.execute_kw(db, uid, password, "website.page", "search_read",
    [[["url", "=", "/about-us"]]], {"fields": ["view_id"]})
if about_pages:
    av_id = about_pages[0]["view_id"][0]
    av = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[av_id], ["arch"]])
    arch = av[0]["arch"]
    changed = False
    for old_id, new_id in replacements.items():
        old_ref = f"/web/image/{old_id}"
        new_ref = f"/web/image/{new_id}"
        if old_ref in arch:
            arch = arch.replace(old_ref, new_ref)
            changed = True
            print(f"    About: {old_ref} → {new_ref}")
    if changed:
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[av_id], {"arch": arch}])

# Update activity page
act_pages = models.execute_kw(db, uid, password, "website.page", "search_read",
    [[["url", "=", "/activity"]]], {"fields": ["view_id"]})
if act_pages:
    act_id = act_pages[0]["view_id"][0]
    actv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [[act_id], ["arch"]])
    arch = actv[0]["arch"]
    changed = False
    for old_id, new_id in replacements.items():
        old_ref = f"/web/image/{old_id}"
        new_ref = f"/web/image/{new_id}"
        if old_ref in arch:
            arch = arch.replace(old_ref, new_ref)
            changed = True
            print(f"    Activity: {old_ref} → {new_ref}")
    if changed:
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [[act_id], {"arch": arch}])

# Update CSS view (blog header background)
css_views = models.execute_kw(db, uid, password, "ir.ui.view", "search",
    [[["name", "=", "Inzense Custom CSS"]]])
if css_views:
    cv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = cv[0]["arch"]
    changed = False
    for old_id, new_id in replacements.items():
        old_ref = f"/web/image/{old_id}"
        new_ref = f"/web/image/{new_id}"
        if old_ref in arch:
            arch = arch.replace(old_ref, new_ref)
            changed = True
            print(f"    CSS: {old_ref} → {new_ref}")
    if changed:
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])

# Update blog.blog cover
blog_cover = models.execute_kw(db, uid, password, "blog.blog", "read", [[3], ["cover_properties"]])
if blog_cover:
    cp = blog_cover[0]["cover_properties"]
    changed = False
    for old_id, new_id in replacements.items():
        old_ref = f"/web/image/{old_id}"
        new_ref = f"/web/image/{new_id}"
        if old_ref in cp:
            cp = cp.replace(old_ref, new_ref)
            changed = True
            print(f"    Blog cover: {old_ref} → {new_ref}")
    if changed:
        models.execute_kw(db, uid, password, "blog.blog", "write", [[3], {"cover_properties": cp}])

# Update blog post covers
all_posts = models.execute_kw(db, uid, password, "blog.post", "search_read",
    [[["blog_id", "=", 3]]], {"fields": ["id", "cover_properties"]})
for post in all_posts:
    cp = post.get("cover_properties") or ""
    changed = False
    for old_id, new_id in replacements.items():
        if f"/web/image/{old_id}" in cp:
            cp = cp.replace(f"/web/image/{old_id}", f"/web/image/{new_id}")
            changed = True
    if changed:
        models.execute_kw(db, uid, password, "blog.post", "write",
            [[post["id"]], {"cover_properties": cp}])

print("  Page references updated")

# ================================================================
# STEP 4: Add performance CSS
# ================================================================
print("\n" + "=" * 60)
print("STEP 4: Performance CSS")
print("=" * 60)

if css_views:
    cv = models.execute_kw(db, uid, password, "ir.ui.view", "read", [css_views, ["arch"]])
    arch = cv[0]["arch"]

    perf_css = """
/* === PERFORMANCE OPTIMIZATION === */

/* Lazy load all images below fold */
img:not([loading]) {
    content-visibility: auto;
}

/* Prevent layout shift */
.oe_product_cart .oe_product_image {
    aspect-ratio: 1 / 1;
    overflow: hidden;
}

/* Optimize below-fold sections */
#wrap > section:nth-child(n+3) {
    content-visibility: auto;
    contain-intrinsic-size: auto 500px;
}

/* Blog post cards - contain rendering */
.o_blog_post {
    content-visibility: auto;
    contain-intrinsic-size: auto 400px;
}

/* Product grid items */
.oe_product {
    content-visibility: auto;
    contain-intrinsic-size: auto 350px;
}

/* Optimize font loading */
@font-face {
    font-display: swap !important;
}
"""

    if "PERFORMANCE OPTIMIZATION" not in arch:
        safe_css = perf_css.replace("&", "&amp;")
        arch = arch.replace("</style>", safe_css + "\n</style>")
        models.execute_kw(db, uid, password, "ir.ui.view", "write", [css_views, {"arch": arch}])
        print("  Added performance CSS")
    else:
        print("  Already has performance CSS")

# ================================================================
# VERIFY
# ================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

# Check new image sizes
import urllib.request

for img_id, name in [(new_1638, "video-seq→jpeg"), (new_1633, "animation→jpeg")]:
    try:
        resp = urllib.request.urlopen(f"http://localhost:8069/web/image/{img_id}")
        data = resp.read()
        print(f"  {name} (ID={img_id}): {len(data)/1024:.0f} KB")
    except Exception as e:
        print(f"  {name}: ERROR {e}")

for old_id, new_id in new_course_ids.items():
    try:
        resp = urllib.request.urlopen(f"http://localhost:8069/web/image/{new_id}")
        data = resp.read()
        name = course_images[old_id]
        print(f"  {name} (ID={new_id}): {len(data)/1024:.0f} KB")
    except:
        pass

# Check pages still load
for p in ["/", "/about-us", "/activity", "/shop", "/blog/xiang-pin-xue-tang-3"]:
    try:
        resp = urllib.request.urlopen(f"http://localhost:8069{p}")
        print(f"  [200] {p}: {len(resp.read())/1024:.0f} KB")
    except Exception as e:
        print(f"  [ERR] {p}: {e}")

print("\n=== Performance optimization complete ===")
