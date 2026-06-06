# Generic LINE Notification System + LIFF Grayscale Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a universal LINE notification system that auto-pushes Flex Messages for ANY Odoo model's stage changes via `mail.notification` hook, replace all brand-specific colors with grayscale design, and remove the redundant LIFF member page.

**Architecture:** Hook into Odoo's `mail.notification.create()` in `woow_line_base` — when a notification targets a partner with a bound LINE user, automatically build a grayscale Flex Message from the `mail.message` tracking data and push it. In `woow_line_bridge`, refactor all Flex templates and LIFF pages to grayscale, remove the redundant `/liff/member` page. The two modules remain independently installable (no new cross-dependency).

**Tech Stack:** Odoo 18 CE, LINE Messaging API v2, LINE Flex Message, LIFF SDK v2, Python 3.12

---

## Design Reference: Grayscale Color System

All Flex Messages and LIFF pages use this unified palette:

| Token | Hex | Usage |
|-------|-----|-------|
| `CLR_BLACK` | `#1A1A1A` | Header text, primary emphasis |
| `CLR_DARK` | `#333333` | Body text, button backgrounds |
| `CLR_MID` | `#666666` | Secondary text |
| `CLR_LABEL` | `#999999` | Labels, captions |
| `CLR_BORDER` | `#E5E5E5` | Separators, borders |
| `CLR_BG` | `#F5F5F5` | Card body background |
| `CLR_WHITE` | `#FFFFFF` | Card surface, button text |

Semantic status colors (used ONLY for the 4px header accent strip):

| Status | Hex | Meaning |
|--------|-----|---------|
| `STATUS_SUCCESS` | `#22C55E` | Confirmed, approved, completed |
| `STATUS_ERROR` | `#EF4444` | Cancelled, failed, rejected |
| `STATUS_WARNING` | `#F59E0B` | Pending, waiting, needs action |
| `STATUS_INFO` | `#3B82F6` | In progress, updated, new |

## Design Reference: Generic Flex Bubble Layout

```
┌─────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓ 4px status strip ▓▓▓▓▓│ ← semantic color only
├─────────────────────────────────┤
│  Title (record name)       #1A  │ ← bold, near-black
│  Subtitle (model/ref)      #999 │ ← caption gray
├─────── #E5E5E5 separator ───────┤
│  Label A:        Value A        │ ← #999 / #333
│  Label B:        Value B        │
│  Label C:        Value C        │
├─────── #E5E5E5 separator ───────┤
│  🕐 2026/06/06 14:30       #999 │ ← timestamp
├─────────────────────────────────┤
│  ┌─────────────────────────┐    │
│  │      查看詳情            │    │ ← #333 bg, #FFF text
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

## Repos & Deployment

| Repo | Module | Changes |
|------|--------|---------|
| `WOOWTECH/woow_line_base` | `woow_line_base` | Add generic Flex factory + mail.notification hook |
| `WOOWTECH/Woow_odoo_line_liff` | `woow_line_bridge` | Grayscale templates, LIFF redirect, remove member page |
| `WOOWTECH/woow_odoo_livechat_line` | `woow_odoo_livechat_line` | No code changes (already depends on `woow_line_base`, auto-benefits) |

**Test instance:** markstudio-odoo.woowtech.io

---

## File Structure

### woow_line_base (new files + modifications)

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `models/line_flex_factory.py` | Generic grayscale Flex template builder (AbstractModel `line.flex.factory`) |
| Create | `models/mail_notification_line.py` | Override `mail.notification.create()` to auto-push LINE notifications |
| Modify | `models/__init__.py` | Add imports for new models |
| Modify | `__manifest__.py` | Version bump to `18.0.2.0.0`, add `mail` to depends if missing |

### woow_line_bridge (modifications + deletions)

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `models/line_flex_template.py` | Replace brand colors → grayscale constants, remove hardcoded shop references |
| Modify | `models/line_bridge.py` | Keep booking hooks but use grayscale templates |
| Modify | `models/appointment_booking.py` | Add `skip_line_notification` context to `super().action_confirm()` to prevent double notification |
| Modify | `controllers/liff_redirect.py` | Grayscale bridge page (spinner, text, background), update error redirects |
| Modify | `controllers/liff_pages.py` | Remove `/liff/member` route, update `/liff/debug` + `/liff/clear-session` to grayscale |
| Modify | `controllers/webhook.py` | Update `_postback_rebook` and `_postback_richmenu` to remove `/liff/member` references |
| Modify | `views/liff_base.xml` | Grayscale the `liff_redirect_bridge` template (second copy of bridge page) |
| Modify | `__manifest__.py` | Remove `views/liff_member.xml` from data list |
| Delete | `views/liff_member.xml` | Dead template (was never used by route, route used inline HTML) |
| Delete | `static/src/js/liff_member.js` | Member page JS (no longer needed) |
| Delete | `static/src/css/liff_markstudio.css` | Brand-specific CSS |

---

## Task 1: Generic Flex Factory in woow_line_base

**Files:**
- Create: `woow_line_base/models/line_flex_factory.py`
- Modify: `woow_line_base/models/__init__.py`
- Modify: `woow_line_base/__manifest__.py`

- [ ] **Step 1: Clone woow_line_base repo locally**

```bash
cd /var/tmp/vibe-kanban/worktrees/925d-/k3s\ project/
gh repo clone WOOWTECH/woow_line_base
```

- [ ] **Step 2: Create `line_flex_factory.py` with grayscale color constants and generic builder**

```python
# woow_line_base/models/line_flex_factory.py
# Generic LINE Flex Message factory — grayscale + semantic status colors
# Any module can call env['line.flex.factory'].build_notification(...)
import logging
import re
import pytz

from odoo import api, models

_logger = logging.getLogger(__name__)

# ── Grayscale palette ───────────────────────────────────────────
CLR_BLACK = '#1A1A1A'
CLR_DARK = '#333333'
CLR_MID = '#666666'
CLR_LABEL = '#999999'
CLR_BORDER = '#E5E5E5'
CLR_BG = '#F5F5F5'
CLR_WHITE = '#FFFFFF'

# ── Semantic status (header accent strip only) ──────────────────
STATUS_COLORS = {
    'success': '#22C55E',
    'error':   '#EF4444',
    'warning': '#F59E0B',
    'info':    '#3B82F6',
}
DEFAULT_STATUS = 'info'


class LineFlexFactory(models.AbstractModel):
    """Generic LINE Flex Message factory — grayscale design.

    Usage from any Odoo module:
        factory = self.env['line.flex.factory']
        flex = factory.build_notification(
            event_type='success',
            title='預約確認',
            subtitle='APT00003',
            info_rows=[('服務', '專業按摩'), ('時間', '2026/06/07 14:30')],
            buttons=[{'label': '查看詳情', 'uri': 'https://...'}],
        )
    """
    _name = 'line.flex.factory'
    _description = 'Generic LINE Flex Message Factory'

    # ── Public API ──────────────────────────────────────────────

    def build_notification(self, event_type, title, subtitle='',
                           info_rows=None, buttons=None, timestamp=''):
        """Build a generic grayscale Flex bubble.

        :param event_type: 'success' | 'error' | 'warning' | 'info'
        :param title: Main title text (e.g. '預約確認', '設備已借出')
        :param subtitle: Secondary text (e.g. record reference 'APT00003')
        :param info_rows: list of (label, value) tuples
        :param buttons: list of dicts with 'label' and 'uri' or 'postback'
        :param timestamp: Optional timestamp string
        :return: Flex Message contents dict (bubble)
        """
        info_rows = info_rows or []
        buttons = buttons or []
        status_color = STATUS_COLORS.get(event_type, STATUS_COLORS[DEFAULT_STATUS])

        # Header with accent strip
        header = self._build_header(title, status_color)

        # Body with info rows
        body_contents = []
        if subtitle:
            body_contents.append({
                'type': 'text',
                'text': subtitle,
                'color': CLR_LABEL,
                'size': 'sm',
            })
        if info_rows:
            body_contents.append({'type': 'separator', 'margin': 'md', 'color': CLR_BORDER})
            for label, value in info_rows:
                body_contents.append(self._build_info_row(label, value))
        if timestamp:
            body_contents.append({'type': 'separator', 'margin': 'md', 'color': CLR_BORDER})
            body_contents.append({
                'type': 'text',
                'text': timestamp,
                'color': CLR_LABEL,
                'size': 'xs',
                'margin': 'md',
            })

        body = {
            'type': 'box',
            'layout': 'vertical',
            'backgroundColor': CLR_WHITE,
            'paddingAll': '20px',
            'spacing': 'md',
            'contents': body_contents,
        }

        bubble = {
            'type': 'bubble',
            'size': 'mega',
            'header': header,
            'body': body,
        }

        # Footer with buttons
        if buttons:
            bubble['footer'] = self._build_footer(buttons)

        return bubble

    def build_tracking_notification(self, message, partner=None):
        """Build a Flex bubble from a mail.message with tracking values.

        Designed to be called from mail.notification hook.

        :param message: mail.message record
        :param partner: res.partner record (optional, for context)
        :return: (flex_contents, alt_text) tuple, or (None, None) if no content
        """
        if not message:
            return None, None

        record_name = message.record_name or ''
        model_name = message.model or ''
        subject = message.subject or record_name or 'Notification'

        # Determine event_type from tracking values
        event_type = 'info'
        info_rows = []

        tracking_values = message.tracking_value_ids if hasattr(message, 'tracking_value_ids') else []
        for tv in tracking_values:
            old_val = tv.old_value_char or tv.old_value_text or str(tv.old_value_integer or tv.old_value_float or tv.old_value_monetary or '')
            new_val = tv.new_value_char or tv.new_value_text or str(tv.new_value_integer or tv.new_value_float or tv.new_value_monetary or '')
            field_desc = tv.field_desc or tv.field_id.field_description or ''

            if old_val or new_val:
                info_rows.append((field_desc, f'{old_val} → {new_val}'))

            # Heuristic: detect status semantics from new value
            new_lower = (new_val or '').lower()
            if new_lower in ('done', 'confirmed', 'paid', 'approved', 'completed'):
                event_type = 'success'
            elif new_lower in ('cancelled', 'cancel', 'rejected', 'failed', 'refused'):
                event_type = 'error'
            elif new_lower in ('pending', 'waiting', 'draft', 'to_approve'):
                event_type = 'warning'

        # If no tracking values, try to extract from body
        if not info_rows:
            body_text = message.body or ''
            if body_text:
                # Strip HTML tags for preview
                clean = re.sub(r'<[^>]+>', '', body_text).strip()
                if clean:
                    info_rows.append(('', clean[:100]))

        if not info_rows:
            return None, None

        # Build button linking to portal document
        buttons = []
        doc_url = self._get_document_url(model_name, message.res_id)
        if doc_url:
            buttons.append({'label': '查看詳情', 'uri': doc_url})

        # Timestamp
        timestamp = ''
        if message.date:
            tz = pytz.timezone('Asia/Taipei')
            local_dt = pytz.utc.localize(message.date).astimezone(tz)
            timestamp = local_dt.strftime('%Y/%m/%d %H:%M')

        # Model display name for subtitle
        model_display = ''
        if model_name:
            try:
                model_display = self.env['ir.model'].sudo().search(
                    [('model', '=', model_name)], limit=1
                ).name or ''
            except Exception:
                pass
        subtitle = record_name
        if model_display and record_name:
            subtitle = f'{model_display} - {record_name}'

        flex = self.build_notification(
            event_type=event_type,
            title=subject,
            subtitle=subtitle,
            info_rows=info_rows,
            buttons=buttons,
            timestamp=timestamp,
        )

        alt_text = f'{subject} - {record_name}' if record_name else subject
        return flex, alt_text

    # ── Private helpers ─────────────────────────────────────────

    def _build_header(self, title, status_color):
        """Header with 4px semantic color accent strip on top."""
        return {
            'type': 'box',
            'layout': 'vertical',
            'paddingAll': '0px',
            'contents': [
                {
                    'type': 'box',
                    'layout': 'vertical',
                    'backgroundColor': status_color,
                    'height': '4px',
                    'contents': [],
                },
                {
                    'type': 'box',
                    'layout': 'vertical',
                    'backgroundColor': CLR_BG,
                    'paddingAll': '16px',
                    'contents': [
                        {
                            'type': 'text',
                            'text': title,
                            'color': CLR_BLACK,
                            'weight': 'bold',
                            'size': 'lg',
                            'align': 'center',
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def _build_info_row(label, value):
        """Horizontal label-value row in grayscale."""
        if not label:
            # Value-only row (e.g. body text preview)
            return {
                'type': 'text',
                'text': str(value) if value else '-',
                'color': CLR_DARK,
                'size': 'sm',
                'wrap': True,
            }
        return {
            'type': 'box',
            'layout': 'horizontal',
            'contents': [
                {
                    'type': 'text',
                    'text': label,
                    'color': CLR_LABEL,
                    'size': 'sm',
                    'flex': 0,
                },
                {
                    'type': 'text',
                    'text': str(value) if value else '-',
                    'color': CLR_DARK,
                    'size': 'sm',
                    'flex': 1,
                    'align': 'end',
                    'wrap': True,
                },
            ],
        }

    @staticmethod
    def _build_footer(buttons):
        """Footer with grayscale action buttons."""
        btn_components = []
        for i, btn in enumerate(buttons):
            if 'uri' in btn:
                action = {'type': 'uri', 'label': btn['label'], 'uri': btn['uri']}
            elif 'postback' in btn:
                action = {'type': 'postback', 'label': btn['label'], 'data': btn['postback']}
            else:
                continue

            style = 'primary' if i == 0 else 'secondary'
            btn_comp = {
                'type': 'button',
                'action': action,
                'style': style,
                'height': 'sm',
            }
            if style == 'primary':
                btn_comp['color'] = CLR_DARK
            btn_components.append(btn_comp)

        return {
            'type': 'box',
            'layout': 'vertical',
            'spacing': 'sm',
            'paddingAll': '16px',
            'contents': btn_components,
        }

    def _get_document_url(self, model, res_id):
        """Resolve portal URL for a record (same pattern as portal notification module)."""
        if not model or not res_id:
            return ''
        try:
            record = self.env[model].sudo().browse(res_id)
            if record.exists() and hasattr(record, 'access_url'):
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
                return base_url + record.access_url
        except Exception:
            pass
        return ''
```

- [ ] **Step 3: Update `models/__init__.py`**

Add to imports:
```python
from . import line_flex_factory
from . import mail_notification_line
```

- [ ] **Step 4: Update `__manifest__.py`**

Bump version to `18.0.2.0.0`. Ensure `'mail'` is in `depends` list.

- [ ] **Step 5: Commit**

```bash
cd woow_line_base
git add models/line_flex_factory.py models/__init__.py __manifest__.py
git commit -m "feat: add generic grayscale Flex factory (line.flex.factory)"
```

---

## Task 2: mail.notification LINE Auto-Push in woow_line_base

**Files:**
- Create: `woow_line_base/models/mail_notification_line.py`
- Modify: `woow_line_base/models/__init__.py` (already done in Task 1)

- [ ] **Step 1: Create `mail_notification_line.py`**

```python
# woow_line_base/models/mail_notification_line.py
# Hook mail.notification.create() to auto-push LINE Flex Messages
# When a notification targets a partner with bound LINE user(s),
# build a generic Flex from mail.message tracking data and push.
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MailNotificationLine(models.Model):
    _inherit = 'mail.notification'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger LINE push for partners with LINE users."""
        notifications = super().create(vals_list)

        # Skip if caller explicitly disabled LINE notifications
        # (e.g. woow_line_bridge booking hooks that send their own Flex)
        if self.env.context.get('skip_line_notification'):
            return notifications

        # Check if auto-push is enabled
        auto_push = self.env['ir.config_parameter'].sudo().get_param(
            'woow_line_base.auto_line_notify', 'False'
        )
        if auto_push not in ('True', 'true', '1'):
            return notifications

        # Batch: collect partner IDs needing LINE push
        # NOTE: This runs synchronously inside create(). The try/except
        # in _push_line_notifications() fully swallows all exceptions
        # so it won't break the ORM transaction. The LINE API client
        # (line.api.service) uses a 10s timeout on HTTP calls.
        self._push_line_notifications(notifications)
        return notifications

    def _push_line_notifications(self, notifications):
        """Push LINE notifications for eligible mail.notification records.

        Filters:
        - notification_type == 'inbox' (portal/internal notifications only)
        - Partner has bound LINE user(s) (is_follower=True, is_blocked=False)
        - mail.message has tracking_value_ids (field change tracking)
        - Skip if message was already handled (debounce per message_id)
        """
        LineUser = self.env['line.user'].sudo()
        factory = self.env['line.flex.factory']
        api_service = self.env['line.api.service']

        # Deduplicate by message — one push per message, not per notification
        seen_messages = set()

        for notif in notifications:
            try:
                # Only process inbox notifications (portal/internal),
                # skip email-type notifications
                if notif.notification_type != 'inbox':
                    continue

                msg = notif.mail_message_id
                if not msg or msg.id in seen_messages:
                    continue

                partner = notif.res_partner_id
                if not partner:
                    continue

                # Find LINE users for this partner
                line_users = LineUser.search([
                    ('partner_id', '=', partner.id),
                    ('is_follower', '=', True),
                    ('is_blocked', '=', False),
                ])
                if not line_users:
                    continue

                seen_messages.add(msg.id)

                # Build generic Flex from tracking data
                flex, alt_text = factory.build_tracking_notification(msg, partner)
                if not flex:
                    continue

                messages = [{
                    'type': 'flex',
                    'altText': alt_text or 'Notification',
                    'contents': flex,
                }]

                api_service.push(line_users, messages)
                _logger.info(
                    'LINE auto-push: message %s → partner %s (%d LINE users)',
                    msg.id, partner.id, len(line_users),
                )
            except Exception:
                _logger.exception(
                    'LINE auto-push failed: notification %s', notif.id,
                )
```

- [ ] **Step 2: Add config parameter XML**

Add to `woow_line_base/data/ir_config_parameter.xml`:
```xml
<record id="config_auto_line_notify" model="ir.config_parameter">
    <field name="key">woow_line_base.auto_line_notify</field>
    <field name="value">False</field>
</record>
```

- [ ] **Step 3: Add toggle to Settings view**

Add to `woow_line_base/views/res_config_settings_views.xml`:
A boolean toggle "自動推送 LINE 通知" with help text explaining that enabling this will auto-push LINE Flex Messages when any `mail.thread` model's tracked fields change and the follower has a bound LINE user.

- [ ] **Step 4: Commit**

```bash
git add models/mail_notification_line.py data/ir_config_parameter.xml views/res_config_settings_views.xml
git commit -m "feat: auto-push LINE on mail.notification via mail.thread tracking"
```

---

## Task 3: Grayscale LIFF Redirect Page in woow_line_bridge

**Files:**
- Modify: `woow_line_bridge/controllers/liff_redirect.py:166-208`
- Modify: `woow_line_bridge/views/liff_base.xml:21-24` (second copy of bridge page as XML template)

- [ ] **Step 1: Replace brand-color inline HTML with grayscale in `_render_liff_bridge_page()`**

In `liff_redirect.py`, replace the inline HTML/CSS:

**Before:**
```css
background:#FAF6F2;
border:4px solid #E0D5C8;border-top-color:#B8956A;
color:#6B5B4E;
```

**After:**
```css
background:#F5F5F5;
border:4px solid #E5E5E5;border-top-color:#333333;
color:#666666;
```

Also update the status text element `id="st"` color from `#6B5B4E` to `#666666`.

- [ ] **Step 2: Update `views/liff_base.xml` bridge template to grayscale**

The `liff_redirect_bridge` template (lines 21-24) has a **second copy** of the same brand colors:
```xml
background:#FAF6F2  →  background:#F5F5F5
border:4px solid #E0D5C8;border-top-color:#B8956A  →  border:4px solid #E5E5E5;border-top-color:#333333
color:#6B5B4E  →  color:#666666
```

- [ ] **Step 3: Update error redirect URLs from `/liff/member` to `/web/login`**

Since we're removing the member page, update all `request.redirect('/liff/member?error=...')` calls in `_authenticate_liff_user()` to redirect to a sensible fallback.

Replace: `return None, request.redirect('/liff/member?error=no_token')`
With: `return None, request.redirect('/web/login?error=no_token')`

Apply to all 4 error redirects in the method (lines 66, 84, 88, 94).

- [ ] **Step 4: Update `_get_redirect_url()` default fallback**

Replace: `return '/liff/member'` (line 316)
With: `return '/web/login'`

- [ ] **Step 5: Commit**

```bash
cd woow_line_bridge
git add controllers/liff_redirect.py views/liff_base.xml
git commit -m "refactor: grayscale LIFF redirect page, remove /liff/member references"
```

---

## Task 4: Remove LIFF Member Page from woow_line_bridge

**Files:**
- Modify: `woow_line_bridge/controllers/liff_pages.py` — remove `/liff/member` route + `_build_member_html()`
- Modify: `woow_line_bridge/__manifest__.py` — remove `views/liff_member.xml` from data list
- Delete: `woow_line_bridge/views/liff_member.xml`
- Delete: `woow_line_bridge/static/src/js/liff_member.js`
- Delete: `woow_line_bridge/static/src/css/liff_markstudio.css`
- Modify: `woow_line_bridge/controllers/webhook.py` — update any `/liff/member` references

- [ ] **Step 1: Remove `/liff/member` route and `_build_member_html` from `liff_pages.py`**

Remove:
- The entire `liff_member()` method (lines 53-77)
- The entire `_build_member_html()` method (lines 79-152)
- The `_heal_session()` method (lines 20-35) — never called by other methods

Keep: `/liff/clear-session`, `/liff/news`, `/liff/locations`, `/liff/debug` routes.

- [ ] **Step 2: Update `liff_clear_session()` default redirect**

In `liff_pages.py` line 46, update the default redirect:
```python
# Before
redirect_to = kwargs.get('r', '/liff/member')
# After
redirect_to = kwargs.get('r', '/web/login')
```

- [ ] **Step 3: Update `/liff/debug` page to grayscale**

In `liff_debug()` method, replace `background:#FAF6F2` with `background:#F5F5F5`.

- [ ] **Step 4: Delete static files**

```bash
rm woow_line_bridge/static/src/js/liff_member.js
rm woow_line_bridge/static/src/css/liff_markstudio.css
```

- [ ] **Step 5: Update `__manifest__.py`**

Remove from `data` list:
```python
'views/liff_member.xml',
```

Remove from `assets.web.assets_frontend`:
```python
'woow_line_bridge/static/src/css/liff_markstudio.css',
```

- [ ] **Step 6: Delete `views/liff_member.xml`**

```bash
rm woow_line_bridge/views/liff_member.xml
```

- [ ] **Step 7: Update webhook.py — remove all `/liff/member` references**

Three changes needed in `webhook.py`:

**7a.** `_postback_rebook()` (line 295): Replace `_liff_url('member')` with a valid LIFF page:
```python
# Before
member_url = request.env['line.flex.template'].sudo()._liff_url('member')
# After — use the booking redirect URL
base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
rebook_url = f'{base_url}/liff/redirect/book'
```

**7b.** `_postback_richmenu()` (line 346): Remove `'member'` from valid targets:
```python
# Before
page = target if target in ('news', 'locations', 'member') else 'member'
# After
page = target if target in ('news', 'locations') else 'book'
```

**7c.** `_postback_richmenu()` target_labels dict (line 338-344): Remove `'member'` entry:
```python
# Before
'member': '會員中心',
# After — remove this line, update default label
label = target_labels.get(target, '立即預約')
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: remove LIFF member page, clean up brand-specific assets"
```

---

## Task 5: Grayscale Booking Flex Templates in woow_line_bridge

**Files:**
- Modify: `woow_line_bridge/models/line_flex_template.py`

- [ ] **Step 1: Replace brand color constants with grayscale**

**Before (lines 12-19):**
```python
BRAND_PRIMARY = '#B8956A'
BRAND_SECONDARY = '#8B6F47'
BRAND_BG = '#FAF6F2'
BRAND_CARD = '#FFFFFF'
BRAND_TEXT = '#2D2620'
BRAND_TEXT_SUB = '#6B5B4E'
LINE_GREEN = '#06C755'
```

**After:**
```python
# Grayscale palette (matches line.flex.factory in woow_line_base)
CLR_BLACK = '#1A1A1A'
CLR_DARK = '#333333'
CLR_MID = '#666666'
CLR_LABEL = '#999999'
CLR_BORDER = '#E5E5E5'
CLR_BG = '#F5F5F5'
CLR_WHITE = '#FFFFFF'

# Semantic status colors (header accent strip only)
STATUS_SUCCESS = '#22C55E'
STATUS_ERROR = '#EF4444'
STATUS_WARNING = '#F59E0B'
STATUS_INFO = '#3B82F6'
```

- [ ] **Step 2: Update `_info_row()` to use grayscale**

Replace `BRAND_TEXT_SUB` → `CLR_LABEL`, `BRAND_TEXT` → `CLR_DARK`.

- [ ] **Step 3: Update `_booking_header()` to use accent strip pattern**

Replace the full-color header with the 4px accent strip + grayscale body pattern (matching the generic factory design).

**Before:**
```python
def _booking_header(self, title, bg_color=None):
    return {
        'type': 'box', 'layout': 'vertical',
        'backgroundColor': bg_color or BRAND_PRIMARY,
        'paddingAll': '16px',
        'contents': [{'type': 'text', 'text': title, 'color': '#FFFFFF', ...}],
    }
```

**After:**
```python
def _booking_header(self, title, status_color=None):
    return {
        'type': 'box', 'layout': 'vertical', 'paddingAll': '0px',
        'contents': [
            {'type': 'box', 'layout': 'vertical',
             'backgroundColor': status_color or STATUS_INFO,
             'height': '4px', 'contents': []},
            {'type': 'box', 'layout': 'vertical',
             'backgroundColor': CLR_BG, 'paddingAll': '16px',
             'contents': [{'type': 'text', 'text': title,
                           'color': CLR_BLACK, 'weight': 'bold',
                           'size': 'lg', 'align': 'center'}]},
        ],
    }
```

- [ ] **Step 4: Update all 6 template methods**

For each `build_*()` method:
1. Replace `BRAND_BG` → `CLR_WHITE` (card background)
2. Replace `BRAND_TEXT` → `CLR_DARK` (body text)
3. Replace `BRAND_TEXT_SUB` → `CLR_LABEL` (labels)
4. Replace `BRAND_PRIMARY` → `CLR_DARK` (button color)
5. Replace `'#E74C3C'` → `STATUS_ERROR` (cancelled header)
6. Replace `'#F39C12'` → `STATUS_WARNING` (payment header)
7. Replace `LINE_GREEN` → `STATUS_SUCCESS` (payment button)
8. Replace `'#9B8E82'` → `CLR_LABEL` (news shop name)
9. Update `_booking_header()` calls to use `status_color=` parameter

Specific status mappings:
- `build_booking_confirmed` → `STATUS_SUCCESS`
- `build_booking_cancelled` → `STATUS_ERROR`
- `build_booking_reminder` → `STATUS_INFO`
- `build_booking_payment_required` → `STATUS_WARNING`
- `build_welcome` → `STATUS_INFO`
- `build_news_card` → `STATUS_INFO`

- [ ] **Step 5: Remove hardcoded shop name default**

Replace `'Mark Studio 馬克健身'` default in `_get_shop_name()` with empty string or generic name.

- [ ] **Step 6: Remove hardcoded welcome message text and fix dead URI**

In `build_welcome()`:

6a. Replace Mark Studio specific text:
```python
# Before
'感謝您加入我們的 LINE 好友！\n點擊下方按鈕開始體驗專業按摩伸展服務。'
# After
'感謝您加入我們的 LINE 好友！\n點擊下方按鈕開始使用服務。'
```

6b. Fix button URIs — they currently point to `_liff_url('member')` which will be a dead page:
```python
# Before
member_url = self._liff_url('member')
# After — point to the booking redirect URL
base_url = self._get_base_url()
book_url = f'{base_url}/liff/redirect/book'
```

Update button labels/actions to use `book_url` instead of `member_url`.

- [ ] **Step 7: Fix double notification — update `appointment_booking.py`**

When both `woow_line_base` and `woow_line_bridge` are installed, a booking confirmation would trigger BOTH the bridge's booking-specific Flex AND the base's generic mail.notification Flex.

Fix: Pass `skip_line_notification` context during `super().action_confirm()` so the mail.notification hook won't fire, then send the booking-specific notification separately:

```python
# Before
def action_confirm(self):
    result = super().action_confirm()
    if not self.env.context.get('skip_line_notification'):
        ...

# After
def action_confirm(self):
    result = super(AppointmentBookingLine, self.with_context(
        skip_line_notification=True
    )).action_confirm()
    if not self.env.context.get('skip_line_notification'):
        ...
```

Same pattern for `action_cancel()`.

- [ ] **Step 8: Commit**

```bash
git add models/line_flex_template.py models/appointment_booking.py
git commit -m "refactor: grayscale Flex templates, fix double notification, remove brand-specific colors"
```

---

## Task 6: Deploy, Test & Push to GitHub

- [ ] **Step 1: Deploy woow_line_base to Mark Studio Odoo**

Follow existing deploy process. Ensure module is upgraded (`-u woow_line_base`).

- [ ] **Step 2: Deploy woow_line_bridge to Mark Studio Odoo**

Upgrade the bridge module (`-u woow_line_bridge`).

- [ ] **Step 3: Enable auto LINE notify**

In Odoo Settings → LINE Configuration → toggle "自動推送 LINE 通知" ON.

- [ ] **Step 4: Test — Booking Confirm**

Create and confirm a booking. Verify:
- LINE Flex card uses grayscale design (dark gray button, white background)
- Header has 4px green (success) accent strip, NOT full-color brand header
- No Mark Studio brand colors visible

- [ ] **Step 5: Test — LIFF Redirect**

Open a LIFF redirect URL in LINE. Verify:
- Loading page has `#F5F5F5` background (light gray, not beige)
- Spinner uses `#333333` accent (dark gray, not gold)
- "正在登入中..." text is `#666666` (medium gray)

- [ ] **Step 6: Test — LIFF Member Page Removed**

Verify `/liff/member` returns 404 or redirects appropriately.

- [ ] **Step 7: Test — Generic mail.notification → LINE**

Trigger a state change on any `mail.thread` model (e.g. change a task stage, confirm a sale order). Verify:
- If the record has a follower with a bound LINE user → LINE Flex card is auto-pushed
- Flex card shows field change tracking (old → new values)
- Card has correct semantic status color strip

- [ ] **Step 8: Push to GitHub repos**

```bash
# woow_line_base
cd woow_line_base
git push origin main

# woow_line_bridge (Woow_odoo_line_liff)
cd ../woow_line_bridge
git push origin main

# woow_odoo_livechat_line — no code changes, but verify compatibility
```

---

## Dependency Notes

### No New Cross-Dependency Required

The two modules remain independently installable:

- **`woow_line_base` alone**: Generic `mail.notification` → LINE push works for ANY model. Uses its own `line.api.service` for push, its own `line.user` for partner lookup.
- **`woow_line_bridge` alone**: Booking-specific Flex templates + LIFF redirect continue to work with its own `line.service` model.
- **Both installed**: Both notification paths work. The bridge's booking hooks produce booking-specific Flex cards. The base's `mail.notification` hook produces generic tracking cards for everything else.

### Future: Module Unification

After this task, a separate refactoring should:
1. Add `woow_line_base` to `woow_line_bridge`'s `depends`
2. Remove duplicate models from bridge (`line_service.py`, `line_user.py`, `line_event_log.py`, `line_push_log.py`)
3. Bridge's `line.bridge` should call `line.api.service` instead of `line.service`
4. This is tracked as a separate task, NOT part of this plan.

### Preventing Double Notifications

When both modules are installed, a booking confirmation could trigger BOTH:
1. Bridge's `on_booking_confirmed()` → booking-specific Flex
2. Base's `mail.notification` hook → generic tracking Flex

This is prevented at TWO levels:

**Level 1 (Base module):** `mail_notification_line.py` checks `self.env.context.get('skip_line_notification')` at the top of `create()`. If True, it skips LINE push entirely.

**Level 2 (Bridge module):** `appointment_booking.py` wraps `super().action_confirm()` and `super().action_cancel()` with `self.with_context(skip_line_notification=True)`, so the `mail.notification` records created during the state change inherit this context and won't trigger the generic LINE push. The bridge then sends its own booking-specific Flex separately.

This means:
- Models handled by the bridge (booking) → bridge sends booking-specific Flex, generic hook is suppressed
- Models NOT handled by the bridge (sale.order, project.task, etc.) → generic hook fires and sends tracking Flex
- Config parameter `woow_line_base.auto_line_notify` must be set to `True` to enable the generic hook (default is `False` for safety)
