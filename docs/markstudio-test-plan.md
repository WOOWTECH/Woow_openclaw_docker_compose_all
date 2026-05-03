# Mark Studio Odoo 18 — Module Integration Test Plan

## Test Environment
- **URL**: http://localhost:18069 (via kubectl port-forward)
- **External**: https://markstudio-odoo.woowtech.io
- **Credentials**: admin / woowtech
- **Database**: markstudio
- **Namespace**: markstudio-odoo

## Test Matrix

| # | Module | Type | Test Description | Pass Criteria |
|---|--------|------|-----------------|---------------|
| T1 | website | Native | Homepage renders with Website Builder | Page loads, no 500 errors, edit mode accessible |
| T2 | reservation_module | Custom | Booking page accessible at /reservation or /appointment | Step wizard renders, service types visible |
| T3 | im_livechat | Native | Live chat widget appears on frontend | Chat button visible on website pages |
| T4 | woow_odoo_livechat_line | Custom | LINE config fields in Live Chat settings | LINE Channel Token/Secret fields visible in backend |
| T5 | im_livechat_n8n | Custom | n8n webhook config in Live Chat settings | Webhook URL field visible, log menu accessible |
| T6 | point_of_sale | Native | POS session opens | POS interface loads, product grid visible |
| T7 | website_blog | Native | Blog page at /blog | Blog listing renders, create post works |
| T8 | hr_expense | Native | Expense menu accessible | Expense form opens, can create expense |

## Detailed Test Steps

### T1: Website Module
1. Navigate to `/` → homepage loads
2. Click "Edit" in top bar → Website Builder opens
3. Check no 500 errors in console

### T2: Reservation Module
1. Navigate to backend → Reservation menu exists
2. Create an appointment type
3. Check frontend `/appointment` route accessible
4. Verify step wizard renders (service → date → info → confirm)

### T3: Live Chat (im_livechat)
1. Backend → Live Chat menu exists
2. Create a chat channel
3. Visit frontend → chat bubble visible

### T4: LINE Integration (woow_odoo_livechat_line)
1. Backend → Live Chat → Channels
2. Open a channel → LINE tab/fields visible
3. LINE Channel Token, Channel Secret fields present

### T5: n8n Integration (im_livechat_n8n)
1. Backend → Live Chat → Channels
2. n8n Webhook URL field visible
3. Backend → Live Chat → n8n Webhook Logs menu accessible

### T6: Point of Sale
1. Backend → Point of Sale menu exists
2. Create/open a POS config
3. Start POS session → POS interface loads

### T7: Blog (website_blog)
1. Navigate to `/blog` → blog listing page
2. Create a blog post from backend
3. Post visible on frontend

### T8: HR Expense
1. Backend → Expenses menu exists
2. Open expense form
3. Can create a new expense entry
