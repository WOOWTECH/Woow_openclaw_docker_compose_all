# Portal POS Shop Picker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge portal POS + KDS entries into a single "銷售點" card that links to a shop picker page with session status and KDS access.

**Architecture:** Modify 3 files in the existing `pos_self_order_enhancement` Odoo 18 module deployed on a K8s pod. All changes are XML templates and Python controller logic — no new JS/CSS/models.

**Tech Stack:** Odoo 18 (QWeb templates, Python controllers), K8s (kubectl)

**Deployment context:** The module lives at `/mnt/extra-addons/pos_self_order_enhancement/` on the Odoo pod in namespace `harumi`. The module source is NOT in this git repo — it is cloned from GitHub during pod init. All edits are applied directly to the pod via `kubectl exec`, then activated with a module upgrade. The pod name may change after restarts; always discover it first:

```bash
POD=$(kubectl -n harumi get pod -l app.kubernetes.io/name=odoo -o jsonpath='{.items[0].metadata.name}')
```

---

## File Map

| File (on pod at `/mnt/extra-addons/pos_self_order_enhancement/`) | Action | Responsibility |
|---|---|---|
| `views/portal_templates.xml` | Modify | Remove KDS card from portal home |
| `views/portal_pos_picker_templates.xml` | Rewrite | New shop picker page + delete KDS picker |
| `controllers/pos_portal.py` | Modify | Remove auto-redirect, simplify KDS route, clean up `_prepare_home_portal_values` |

---

### Task 1: Remove KDS card from portal home

**Target file:** `views/portal_templates.xml` on the pod

- [ ] **Step 1: Write the updated file to the pod**

Delete the entire `portal_my_home_kds` template block. Keep `portal_my_home_pos` unchanged.

```bash
POD=$(kubectl -n harumi get pod -l app.kubernetes.io/name=odoo -o jsonpath='{.items[0].metadata.name}')
kubectl -n harumi exec "$POD" -c odoo -- bash -c 'cat > /mnt/extra-addons/pos_self_order_enhancement/views/portal_templates.xml << '\''XMLEOF'\''
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <template id="portal_my_home_pos"
              name="Portal My Home: Point of Sale"
              inherit_id="portal.portal_my_home"
              customize_show="True"
              priority="50">
        <xpath expr="//div[hasclass('"'"'o_portal_docs'"'"')]" position="before">
            <t t-set="portal_client_category_enable" t-value="True"/>
        </xpath>
        <div id="portal_client_category" position="inside">
            <t t-call="portal.portal_docs_entry">
                <t t-set="icon" t-value="'"'"'/pos_self_order_enhancement/static/src/img/portal-pos.svg'"'"'"/>
                <t t-set="title">銷售點</t>
                <t t-set="text">管理您的銷售收款與訂單</t>
                <t t-set="url" t-value="'"'"'/my/pos'"'"'"/>
                <t t-set="placeholder_count" t-value="'"'"'portal_pos_config_count'"'"'"/>
            </t>
        </div>
    </template>

</odoo>
XMLEOF'
```

- [ ] **Step 2: Verify file was written**

```bash
kubectl -n harumi exec "$POD" -c odoo -- cat /mnt/extra-addons/pos_self_order_enhancement/views/portal_templates.xml
```

Expected: file contains only `portal_my_home_pos` template, no `portal_my_home_kds`.

---

### Task 2: Rewrite shop picker template

**Target file:** `views/portal_pos_picker_templates.xml` on the pod

- [ ] **Step 1: Write the new file to the pod**

Replace both `portal_pos_picker` and `portal_kds_picker` with a single redesigned `portal_pos_picker`:

```bash
kubectl -n harumi exec "$POD" -c odoo -- bash -c 'cat > /mnt/extra-addons/pos_self_order_enhancement/views/portal_pos_picker_templates.xml << '\''XMLEOF'\''
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <template id="portal_pos_picker" name="Portal POS Shop Picker">
        <t t-call="portal.portal_layout">
            <t t-set="my_details" t-value="False"/>
            <div class="o_portal_my_home">
                <!-- Header -->
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h3 class="mb-0">銷售點</h3>
                    <a href="/my" class="btn btn-sm btn-outline-secondary">
                        <i class="fa fa-arrow-left"/> 返回
                    </a>
                </div>
                <p class="text-muted mb-4">查看並管理您負責的營業點</p>

                <!-- Empty state -->
                <t t-if="not configs">
                    <div class="text-center py-5 text-muted">
                        <i class="fa fa-store fa-3x mb-3 d-block opacity-50"/>
                        <p class="mb-0">目前沒有指派給您的營業點</p>
                    </div>
                </t>

                <!-- Shop cards -->
                <div t-if="configs" class="row g-3">
                    <t t-foreach="configs" t-as="config">
                        <div class="col-12 col-md-6">
                            <div class="card h-100 bg-100 border-0 rounded-3">
                                <div class="card-body position-relative">
                                    <!-- KDS badge (top-right) -->
                                    <a t-if="config.kds_enabled and config.kds_access_token"
                                       t-att-href="'"'"'/pos-kds/%s?token=%s'"'"' % (config.id, config.kds_access_token)"
                                       class="position-absolute top-0 end-0 mt-3 me-3 text-decoration-none"
                                       title="廚房螢幕">
                                        <span class="badge bg-warning text-dark">
                                            <i class="fa fa-cutlery"/> KDS
                                        </span>
                                    </a>

                                    <!-- Shop name + status (inline) -->
                                    <div class="d-flex align-items-center gap-2 mb-3">
                                        <h5 class="card-title mb-0">
                                            <t t-out="config.name"/>
                                        </h5>
                                        <span t-if="config.has_active_session"
                                              class="badge text-success border border-success">
                                            <i class="fa fa-circle small"/> 營業中
                                        </span>
                                        <span t-else=""
                                              class="badge text-muted border">
                                            <i class="fa fa-circle small"/> 已關閉
                                        </span>
                                    </div>

                                    <!-- Action button -->
                                    <a t-att-href="'"'"'/pos/ui?config_id=%s'"'"' % config.id"
                                       class="btn btn-primary w-100"
                                       style="background-color: #714B67; border-color: #714B67;">
                                        <t t-if="config.has_active_session">繼續銷售</t>
                                        <t t-else="">開啟銷售</t>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </t>
                </div>
            </div>
        </t>
    </template>

</odoo>
XMLEOF'
```

Key design points:
- Name and status badge are on the same line (`d-flex align-items-center gap-2`) per spec "名稱右側"
- KDS badge uses `t-if="config.kds_enabled and config.kds_access_token"` (both fields checked)
- Empty state shows "目前沒有指派給您的營業點" when `not configs`

- [ ] **Step 2: Verify file was written**

```bash
kubectl -n harumi exec "$POD" -c odoo -- cat /mnt/extra-addons/pos_self_order_enhancement/views/portal_pos_picker_templates.xml
```

Expected: single `portal_pos_picker` template, no `portal_kds_picker`.

---

### Task 3: Update controller logic

**Target file:** `controllers/pos_portal.py` on the pod

- [ ] **Step 1: Write the updated controller to the pod**

Three changes to the `PortalHomePosCard` class:
1. `portal_my_pos` — remove auto-redirect, always render picker (including 0 configs)
2. `portal_my_kds` — simplify to redirect to `/my/pos`
3. `_prepare_home_portal_values` — keep only `portal_pos_config_count`, remove all KDS/label keys

Leave `PosPortalController` class unchanged.

```bash
kubectl -n harumi exec "$POD" -c odoo -- python3 -c "
import re

path = '/mnt/extra-addons/pos_self_order_enhancement/controllers/pos_portal.py'
with open(path, 'r') as f:
    content = f.read()

# Replace PortalHomePosCard class
old_class = content[content.index('class PortalHomePosCard'):]
new_class = '''class PortalHomePosCard(CustomerPortal):

    @http.route(['/my/pos'], type='http', auth='user', website=True)
    def portal_my_pos(self, **kw):
        user = request.env.user
        if user._is_internal():
            return request.redirect('/odoo/action-point_of_sale.action_client_pos_menu')
        if not user._is_portal():
            return request.redirect('/my')

        partner = user.sudo().partner_id
        configs = partner.portal_pos_config_ids.filtered('active')

        return request.render(
            'pos_self_order_enhancement.portal_pos_picker',
            {
                'page_name': 'portal_pos',
                'configs': configs,
            },
        )

    @http.route(['/my/kds'], type='http', auth='user', website=True)
    def portal_my_kds(self, **kw):
        return request.redirect('/my/pos')

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if not counters or 'portal_pos_config_count' in counters:
            partner = request.env.user.sudo().partner_id
            configs = partner.portal_pos_config_ids.filtered('active')
            values['portal_pos_config_count'] = len(configs)
        return values
'''

content = content[:content.index('class PortalHomePosCard')] + new_class

# Update docstring
content = content.replace(
    'renders the shop picker when the user has\n   multiple shops assigned, and auto-redirects when there is only one.',
    'renders the shop picker page showing all\n   assigned POS shops with session status and KDS access.'
)

with open(path, 'w') as f:
    f.write(content)

print('OK')
"
```

- [ ] **Step 2: Verify the controller was updated**

```bash
kubectl -n harumi exec "$POD" -c odoo -- grep -A 5 'def portal_my_pos' /mnt/extra-addons/pos_self_order_enhancement/controllers/pos_portal.py
kubectl -n harumi exec "$POD" -c odoo -- grep -A 3 'def portal_my_kds' /mnt/extra-addons/pos_self_order_enhancement/controllers/pos_portal.py
kubectl -n harumi exec "$POD" -c odoo -- grep -A 8 '_prepare_home_portal_values' /mnt/extra-addons/pos_self_order_enhancement/controllers/pos_portal.py
```

Expected:
- `portal_my_pos` always returns `request.render(...)`, no `if len(configs) == 1: redirect`
- `portal_my_kds` is just `return request.redirect('/my/pos')`
- `_prepare_home_portal_values` only sets `portal_pos_config_count`, no KDS/label keys

---

### Task 4: Deploy and verify

- [ ] **Step 1: Upgrade module on pod**

```bash
kubectl -n harumi exec "$POD" -c odoo -- odoo -d odoo -u pos_self_order_enhancement --stop-after-init --no-http
```

Expected: output ends with `Modules loaded.` and `Stopping gracefully` — no errors.

- [ ] **Step 2: Verify portal home — KDS card removed, POS card present with count**

Open browser to `https://harumi-odoo.woowtech.io/my` (login as portal user `toypark1234@gmail.com` / `test1234`).

Verify:
- 「銷售點」card is present with icon and description 「管理您的銷售收款與訂單」
- 「廚房顯示螢幕」card is **gone**
- Count badge on 銷售點 card renders correctly (not empty/broken)

- [ ] **Step 3: Verify /my/pos shop picker page**

Click 「銷售點」card. Verify:
- Page loads within portal layout (website header/footer visible)
- Title: 「銷售點」with subtitle 「查看並管理您負責的營業點」
- 「← 返回」button links to `/my`
- Shop cards show name + status badge **on the same line** (營業中 green / 已關閉 grey)
- Action button text matches status (繼續銷售 / 開啟銷售)
- KDS badge visible in top-right only on configs with KDS enabled + valid token

- [ ] **Step 4: Verify POS entry works**

Click 「繼續銷售」or 「開啟銷售」on a shop card. Verify POS UI loads.

- [ ] **Step 5: Verify KDS entry works**

Click KDS badge on a card with KDS enabled. Verify Kitchen Display loads.

- [ ] **Step 6: Verify /my/kds redirect**

Navigate directly to `https://harumi-odoo.woowtech.io/my/kds`. Verify it redirects to `/my/pos`.
