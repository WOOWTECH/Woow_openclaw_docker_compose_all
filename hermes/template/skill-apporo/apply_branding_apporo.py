import re, os

LOGO_CIRCLE = '<circle cx="256" cy="288.72" r="15.09" fill="#fff"/>'
LOGO_PATH = "M458.85,342.01c-1.6-5.2-3.76-10.24-6.46-15.01,0-.1-131.86-228.35-131.9-228.44-13.38-22.15-38.27-36.39-64.48-36.22-26.16-.17-51.03,14.02-64.42,36.13L59.4,327.46c-2.82,5.06-4.52,9.28-6.21,14.59-14.98,48.37,21.67,97.69,72.21,97.61,0-.02,261.29.03,261.25-.02,5.71,0,11.41-.66,16.95-1.93,12.73-2.91,24.75-9.14,34.55-18.3,20.87-18.94,29.33-50.72,20.69-77.4ZM331.48,157.84c.14.24,75.46,130.73,75.62,130.97,0,0-.16-.09-.16-.09l-75.46-43.57v-87.32ZM331.48,268.49c1.22.71,38.44,22.18,38.36,22.14-7.08,1.62-13.93,4.26-20.28,7.86l-18.08,10.44v-40.44ZM311.26,365.34c.11,7.13,1.24,14.2,3.32,20.98l-38.35-22.13,35.03-20.23s0,21.38,0,21.39ZM207.23,111.88c27.56-50.33,103.21-31.75,104.03,25.91,0,20.02-10.65,37.55-26.6,47.24l-2.31,1.33-26.34,15.21-26.32-15.21c-25.93-13.45-36.95-48.24-22.47-74.48ZM311.27,189.2s0,44.27,0,44.27l-35.01-20.21c2.38-1.38,16.93-9.8,18.94-10.93,5.95-3.64,11.37-8.06,16.09-13.13ZM200.79,189.23c4.67,5,9.99,9.37,15.85,12.96,2.14,1.26,16.69,9.63,19.17,11.07l-35.02,20.21v-44.24ZM200.79,256.83l55.25-31.89,55.23,31.87s0,63.8,0,63.8l-55.25,31.89s-55.24-31.89-55.23-31.9v-63.78ZM200.79,343.95l35.02,20.21-38.35,22.15c2.2-7.17,3.34-14.66,3.34-22.2,0,0,0-20.16,0-20.16ZM180.56,363.25c.31,56.35-73.36,77.98-103.08,28.54-27.59-49.9,26.28-102.53,75.05-75.69,0,0,28.02,16.17,28.02,16.17v30.98ZM180.56,308.93l-17.61-10.17-.62-.35c-6.32-3.55-13.09-6.16-20.1-7.77l3.31-1.91,35.02-20.21v40.42ZM105.15,288.69c-.1.18,75.43-130.65,75.43-130.65l-.02,87.12-75.41,43.53ZM180.57,419.41l75.46-43.57,75.44,43.57h-150.9ZM331.48,364.11s0-31.81,0-31.81l26.48-15.28c48.68-28.88,104.63,24.09,76.6,74.78-29.5,49.07-102.51,28.2-103.08-27.69Z"

SVG_SMALL = f'<svg viewBox="0 0 512 512" width="16" height="16">{LOGO_CIRCLE}<path d="{LOGO_PATH}" fill="#fff"/></svg>'
SVG_BIG = f'<svg viewBox="0 0 512 512" width="80" height="80">{LOGO_CIRCLE}<path d="{LOGO_PATH}" fill="#fff"/></svg>'
SVG_LOGIN = f'<svg viewBox="0 0 512 512" width="32" height="32">{LOGO_CIRCLE}<path d="{LOGO_PATH}" fill="#fff"/></svg>'

try:
    with open("/app/static/index.html") as f:
        html = f.read()
    m = re.search(r'<span class="app-titlebar-icon".*?</span>', html, re.DOTALL)
    if m:
        html = html[:m.start()] + f'<span class="app-titlebar-icon" aria-hidden="true">{SVG_SMALL}</span>' + html[m.end():]
    m2 = re.search(r'<div class="empty-logo">.*?</div>', html, re.DOTALL)
    if m2:
        html = html[:m2.start()] + f'<div class="empty-logo">{SVG_BIG}</div>' + html[m2.end():]
    if "HIDE_KANBAN_TODOS" not in html:
        html = html.replace("</head>", '<style>/* HIDE_KANBAN_TODOS */ [data-panel="kanban"],[data-panel="todos"]{display:none!important;}</style></head>')
    with open("/app/static/index.html", "w") as f:
        f.write(html)
except Exception as e:
    print(f"index.html error: {e}")

try:
    with open("/app/api/routes.py") as f:
        c = f.read()
    c = c.replace('.logo{width:48px;height:48px;border-radius:12px;background:linear-gradient(145deg,#e8a030,#e94560);', '.logo{width:48px;height:48px;border-radius:12px;background:#1a1a2e;')
    old_logo = re.search(r'<div class="logo">.*?</div>', c, re.DOTALL)
    if old_logo:
        c = c[:old_logo.start()] + f'<div class="logo">{SVG_LOGIN}</div>' + c[old_logo.end():]
    with open("/app/api/routes.py", "w") as f:
        f.write(c)
except Exception as e:
    print(f"routes.py error: {e}")

print("Branding v2 applied")
