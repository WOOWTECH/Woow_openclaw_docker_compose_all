#!/usr/bin/env python3
"""
Fix 67 products missing ingredient/formula information in their `description` field.

For each product:
1. Read the current description HTML
2. Find the `<p><b>成分與說明</b></p><p>...</p>` section
3. INSERT a new `<p><b>成分</b></p><p>{ingredients}</p>` section right after it
4. Write back the updated description
5. Count and report fixes

Does NOT replace existing content - only ADDS the missing ingredients section.
"""
import xmlrpc.client
import re

url = "http://localhost:8069"
db = "inzense"
password = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# ================================================================
# Ingredient mapping: default_code -> ingredient string
# ================================================================
INGREDIENTS = {
    # === 神明系列 長線香 (LIG001-027) ===
    "LIG001": "西澳新山檀香根部、古邦老山檀香、柬埔寨沉香、安息香、印尼楠木黏粉",
    "LIG002": "巴拉圭綠檀、非洲降真檀、西澳新山檀香、琥珀、印尼楠木黏粉",
    "LIG003": "西澳洲檀香根部、非洲降真檀、伊利安沉香、秘魯聖木、伊朗玫瑰、印尼楠木黏粉",
    "LIG004": "巴拉圭綠檀、紫檀、西澳新山檀香、玫瑰花、依蘭依蘭花、印尼楠木黏粉",
    "LIG005": "上等老山檀香、古邦老山檀香、西澳新山檀香、非洲降真檀、白安息香、印尼楠木黏粉",
    "LIG006": "柬埔寨沉香、越南惠安沉香、古邦老山檀香、白安息香、香草安息香、印尼楠木黏粉",
    "LIG007": "非洲降真檀、緬甸降真、西澳新山檀香根部、琥珀、紅安息香、印尼楠木黏粉",
    "LIG008": "西澳新山檀香根部、巴拉圭綠檀、秘魯聖木、白色鼠尾草、安息香、印尼楠木黏粉",
    "LIG009": "非洲降真檀、緬甸降真、紫檀、琥珀、龍血、紅安息香、印尼楠木黏粉",
    "LIG010": "西澳新山檀香根部、非洲降真檀、緬甸降真、柬埔寨沉香、琥珀、印尼楠木黏粉",
    "LIG011": "非洲降真檀、緬甸降真、西澳新山檀香、艾草、白色鼠尾草、印尼楠木黏粉",
    "LIG012": "古邦老山檀香、柬埔寨沉香、越南惠安沉香、白安息香、阿曼乳香、印尼楠木黏粉",
    "LIG013": "紫檀、西澳新山檀香、柬埔寨沉香、玫瑰花、依蘭花、印尼楠木黏粉",
    "LIG014": "非洲降真檀、緬甸降真、秘魯聖木、艾草、紅安息香、印尼楠木黏粉",
    "LIG015": "巴拉圭綠檀、西澳新山檀香、玫瑰花、梔子花、白安息香、印尼楠木黏粉",
    "LIG016": "非洲降真檀、緬甸降真、紫檀、柬埔寨沉香、琥珀、紅安息香、印尼楠木黏粉",
    "LIG017": "非洲降真檀、緬甸降真、西澳新山檀香、秘魯聖木、白色鼠尾草、印尼楠木黏粉",
    "LIG018": "柬埔寨沉香、西澳新山檀香、古邦老山檀香、甘草、花米、印尼楠木黏粉",
    "LIG019": "古邦老山檀香、柬埔寨沉香、越南惠安沉香、阿曼乳香、白安息香、印尼楠木黏粉",
    "LIG020": "西澳新山檀香根部、巴拉圭綠檀、玫瑰花、依蘭花、白安息香、印尼楠木黏粉",
    "LIG021": "巴拉圭綠檀、西澳新山檀香、秘魯聖木、安息香、印尼楠木黏粉",
    "LIG022": "柬埔寨沉香、古邦老山檀香、非洲降真檀、白安息香、香草安息香、印尼楠木黏粉",
    "LIG023": "西澳新山檀香根部、古邦老山檀香、玫瑰花、依蘭花、阿曼乳香、印尼楠木黏粉",
    "LIG024": "古邦老山檀香、柬埔寨沉香、越南惠安沉香、白安息香、印尼楠木黏粉",
    "LIG025": "非洲降真檀、緬甸降真、紫檀、柬埔寨沉香、琥珀、龍血、印尼楠木黏粉",
    "LIG026": "古邦老山檀香、西澳新山檀香、柬埔寨沉香、阿曼乳香、白安息香、印尼楠木黏粉",
    "LIG027": "非洲降真檀、緬甸降真、秘魯聖木、艾草、紅安息香、印尼楠木黏粉",

    # === 神明系列 迷你香 (MIG001-027) - same ingredients as LIG counterparts ===
    "MIG001": "西澳新山檀香根部、古邦老山檀香、柬埔寨沉香、安息香、印尼楠木黏粉",
    "MIG002": "巴拉圭綠檀、非洲降真檀、西澳新山檀香、琥珀、印尼楠木黏粉",
    "MIG003": "西澳洲檀香根部、非洲降真檀、伊利安沉香、秘魯聖木、伊朗玫瑰、印尼楠木黏粉",
    "MIG004": "巴拉圭綠檀、紫檀、西澳新山檀香、玫瑰花、依蘭依蘭花、印尼楠木黏粉",
    "MIG005": "上等老山檀香、古邦老山檀香、西澳新山檀香、非洲降真檀、白安息香、印尼楠木黏粉",
    "MIG006": "柬埔寨沉香、越南惠安沉香、古邦老山檀香、白安息香、香草安息香、印尼楠木黏粉",
    "MIG007": "非洲降真檀、緬甸降真、西澳新山檀香根部、琥珀、紅安息香、印尼楠木黏粉",
    "MIG008": "西澳新山檀香根部、巴拉圭綠檀、秘魯聖木、白色鼠尾草、安息香、印尼楠木黏粉",
    "MIG009": "非洲降真檀、緬甸降真、紫檀、琥珀、龍血、紅安息香、印尼楠木黏粉",
    "MIG010": "西澳新山檀香根部、非洲降真檀、緬甸降真、柬埔寨沉香、琥珀、印尼楠木黏粉",
    "MIG011": "非洲降真檀、緬甸降真、西澳新山檀香、艾草、白色鼠尾草、印尼楠木黏粉",
    "MIG012": "古邦老山檀香、柬埔寨沉香、越南惠安沉香、白安息香、阿曼乳香、印尼楠木黏粉",
    "MIG013": "紫檀、西澳新山檀香、柬埔寨沉香、玫瑰花、依蘭花、印尼楠木黏粉",
    "MIG014": "非洲降真檀、緬甸降真、秘魯聖木、艾草、紅安息香、印尼楠木黏粉",
    "MIG015": "巴拉圭綠檀、西澳新山檀香、玫瑰花、梔子花、白安息香、印尼楠木黏粉",
    "MIG016": "非洲降真檀、緬甸降真、紫檀、柬埔寨沉香、琥珀、紅安息香、印尼楠木黏粉",
    "MIG017": "非洲降真檀、緬甸降真、西澳新山檀香、秘魯聖木、白色鼠尾草、印尼楠木黏粉",
    "MIG018": "柬埔寨沉香、西澳新山檀香、古邦老山檀香、甘草、花米、印尼楠木黏粉",
    "MIG019": "古邦老山檀香、柬埔寨沉香、越南惠安沉香、阿曼乳香、白安息香、印尼楠木黏粉",
    "MIG020": "西澳新山檀香根部、巴拉圭綠檀、玫瑰花、依蘭花、白安息香、印尼楠木黏粉",
    "MIG021": "巴拉圭綠檀、西澳新山檀香、秘魯聖木、安息香、印尼楠木黏粉",
    "MIG022": "柬埔寨沉香、古邦老山檀香、非洲降真檀、白安息香、香草安息香、印尼楠木黏粉",
    "MIG023": "西澳新山檀香根部、古邦老山檀香、玫瑰花、依蘭花、阿曼乳香、印尼楠木黏粉",
    "MIG024": "古邦老山檀香、柬埔寨沉香、越南惠安沉香、白安息香、印尼楠木黏粉",
    "MIG025": "非洲降真檀、緬甸降真、紫檀、柬埔寨沉香、琥珀、龍血、印尼楠木黏粉",
    "MIG026": "古邦老山檀香、西澳新山檀香、柬埔寨沉香、阿曼乳香、白安息香、印尼楠木黏粉",
    "MIG027": "非洲降真檀、緬甸降真、秘魯聖木、艾草、紅安息香、印尼楠木黏粉",

    # === 五行系列 長線香 (LIFE001-005) ===
    "LIFE001": "西澳新山檀香、非洲降真檀、琥珀、白安息香、印尼楠木黏粉",
    "LIFE002": "台灣肖楠、台灣龍柏、巴拉圭綠檀、秘魯聖木、印尼楠木黏粉",
    "LIFE003": "柬埔寨沉香、越南惠安沉香、甘草、花米、印尼楠木黏粉",
    "LIFE004": "非洲降真檀、緬甸降真、紫檀、琥珀、龍血、印尼楠木黏粉",
    "LIFE005": "巴拉圭綠檀、西澳新山檀香根部、琥珀、安息香、印尼楠木黏粉",

    # === 五行系列 迷你香 (MIFE001-005) - same ingredients as LIFE counterparts ===
    "MIFE001": "西澳新山檀香、非洲降真檀、琥珀、白安息香、印尼楠木黏粉",
    "MIFE002": "台灣肖楠、台灣龍柏、巴拉圭綠檀、秘魯聖木、印尼楠木黏粉",
    "MIFE003": "柬埔寨沉香、越南惠安沉香、甘草、花米、印尼楠木黏粉",
    "MIFE004": "非洲降真檀、緬甸降真、紫檀、琥珀、龍血、印尼楠木黏粉",
    "MIFE005": "巴拉圭綠檀、西澳新山檀香根部、琥珀、安息香、印尼楠木黏粉",

    # === 善緣香 (LIE008/MIE008) ===
    "LIE008": "巴拉圭綠檀、西澳新山檀香根部、非洲降真檀、秘魯聖木、玫瑰花、依蘭花、白安息香、印尼楠木黏粉",
    "MIE008": "巴拉圭綠檀、西澳新山檀香根部、非洲降真檀、秘魯聖木、玫瑰花、依蘭花、白安息香、印尼楠木黏粉",

    # === 其他 3 products - only add if missing ===
    # LIT001 (台灣黃檜): already says "100%台灣黃檜粉製成" -> add explicit ingredient
    "LIT001": "台灣黃檜香粉、印尼楠木黏粉",
    # LIT003 (台灣牛樟): already says "100%台灣牛樟粉製成" -> add explicit ingredient
    "LIT003": "台灣牛樟香粉、印尼楠木黏粉",
    # LIF002 (美國杜松): already says "100%美國杜松粉製成" -> add explicit ingredient
    "LIF002": "美國杜松香粉、印尼楠木黏粉",
}

print("=" * 60)
print(f"Fixing {len(INGREDIENTS)} products with missing ingredient info")
print("=" * 60)

# ================================================================
# Fetch all target products
# ================================================================
all_codes = list(INGREDIENTS.keys())
products = models.execute_kw(db, uid, password, 'product.template', 'search_read', [
    [['default_code', 'in', all_codes], ['active', '=', True]]
], {'fields': ['id', 'name', 'default_code', 'description'], 'order': 'default_code'})

print(f"\nFound {len(products)} matching products in Odoo")

# ================================================================
# Check which already have a dedicated 成分 section (separate from 成分與說明)
# A dedicated section looks like: <p><b>成分</b></p> (NOT <p><b>成分與說明</b></p>)
# ================================================================
def has_dedicated_ingredients_section(desc):
    """Check if description already has a standalone <p><b>成分</b></p> section."""
    if not desc:
        return False
    # Match <p><b>成分</b></p> but NOT <p><b>成分與說明</b></p>
    # Use regex to find <p><b>成分</b></p> that is NOT followed by 與說明
    pattern = r'<p><b>成分</b></p>'
    return bool(re.search(pattern, desc))


def insert_ingredients(desc, ingredients_str):
    """Insert a <p><b>成分</b></p><p>ingredients</p> section after the 成分與說明 block.

    The 成分與說明 block structure is:
    <p><b>成分與說明</b></p>
    <p>...description text...</p>

    We insert our new section right after that second <p>...</p>.
    """
    if not desc:
        return desc

    ingredient_html = f'<p><b>成分</b></p>\n<p>{ingredients_str}</p>'

    # Strategy 1: Find 成分與說明 section and insert after its content paragraph
    # Pattern: <p><b>成分與說明</b></p>\n<p>...text...</p>
    pattern = r'(<p><b>成分與說明</b></p>\s*<p>.*?</p>)'
    match = re.search(pattern, desc, re.DOTALL)
    if match:
        insert_pos = match.end()
        new_desc = desc[:insert_pos] + '\n' + ingredient_html + desc[insert_pos:]
        return new_desc

    # Strategy 2: Find 說明 section
    pattern2 = r'(<p><b>說明</b></p>\s*<p>.*?</p>)'
    match2 = re.search(pattern2, desc, re.DOTALL)
    if match2:
        insert_pos = match2.end()
        new_desc = desc[:insert_pos] + '\n' + ingredient_html + desc[insert_pos:]
        return new_desc

    # Strategy 3: Append before 保存方式 if exists
    pattern3 = r'(<p><b>保存方式</b></p>)'
    match3 = re.search(pattern3, desc)
    if match3:
        insert_pos = match3.start()
        new_desc = desc[:insert_pos] + ingredient_html + '\n' + desc[insert_pos:]
        return new_desc

    # Strategy 4: Append at end
    new_desc = desc + '\n' + ingredient_html
    return new_desc


# ================================================================
# Process each product
# ================================================================
success_count = 0
skip_count = 0
fail_count = 0
not_found = []

# Build a lookup by default_code
product_map = {p['default_code']: p for p in products}

for code, ingredients_str in sorted(INGREDIENTS.items()):
    if code not in product_map:
        not_found.append(code)
        continue

    product = product_map[code]
    pid = product['id']
    name = product['name']
    desc = product.get('description') or ''

    # Check if already has a dedicated 成分 section
    if has_dedicated_ingredients_section(desc):
        skip_count += 1
        print(f"  [SKIP] {code:10s} {name[:30]:30s} - already has 成分 section")
        continue

    # Insert ingredients
    new_desc = insert_ingredients(desc, ingredients_str)

    if new_desc == desc:
        skip_count += 1
        print(f"  [SKIP] {code:10s} {name[:30]:30s} - no change needed")
        continue

    try:
        models.execute_kw(db, uid, password, 'product.template', 'write', [
            [pid], {'description': new_desc}
        ])
        success_count += 1
        print(f"  [OK]   {code:10s} {name[:30]:30s}")
    except Exception as e:
        fail_count += 1
        print(f"  [FAIL] {code:10s} {name[:30]:30s}: {e}")

print(f"\n{'=' * 60}")
print(f"RESULTS:")
print(f"  Updated:    {success_count}")
print(f"  Skipped:    {skip_count}")
print(f"  Failed:     {fail_count}")
print(f"  Not found:  {len(not_found)}")
if not_found:
    print(f"  Missing codes: {', '.join(not_found)}")
print(f"  Total expected: {len(INGREDIENTS)}")
print(f"{'=' * 60}")

# ================================================================
# Verify: Check a sample of updated products
# ================================================================
print("\n--- VERIFICATION ---")
verify_codes = ['LIG001', 'LIG005', 'LIG027', 'MIG001', 'MIG015', 'LIFE001', 'MIFE003', 'LIE008', 'MIE008', 'LIT001', 'LIF002']
for code in verify_codes:
    prods = models.execute_kw(db, uid, password, 'product.template', 'search_read', [
        [['default_code', '=', code], ['active', '=', True]]
    ], {'fields': ['id', 'name', 'default_code', 'description']})
    if prods:
        p = prods[0]
        desc = p.get('description') or ''
        has_section = has_dedicated_ingredients_section(desc)
        # Extract the ingredient line for verification
        match = re.search(r'<p><b>成分</b></p>\s*<p>(.*?)</p>', desc, re.DOTALL)
        ingredient_line = match.group(1)[:80] + '...' if match and len(match.group(1)) > 80 else (match.group(1) if match else 'N/A')
        print(f"  {code:10s} | has_成分={has_section} | ingredients={ingredient_line}")

# Final count of all products with dedicated 成分 section
all_target = models.execute_kw(db, uid, password, 'product.template', 'search_read', [
    [['default_code', 'in', all_codes], ['active', '=', True]]
], {'fields': ['id', 'default_code', 'description']})

count_with = sum(1 for p in all_target if has_dedicated_ingredients_section(p.get('description') or ''))
print(f"\nFinal check: {count_with}/{len(all_target)} target products now have dedicated 成分 section")
