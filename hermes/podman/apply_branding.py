import re, os

LOGO_PATH = "M256 348.25L256 256L244.5 256L233 256L233 163.5L233 71L244.5 71L256 71L256 163.5L256 256L267.5 256L279 256L279 347.94L279 439.88L267.5 440.19L256 440.5L256 348.25ZM476.25 440.22L465 439.93L465 347.97L465 256L477 256L489 256L489 347.94C489 398.51 488.66 440.02 488.25 440.19C487.84 440.36 482.44 440.37 476.25 440.22ZM118 438.12C76.69 429.12 44.77 395.83 37.47 354.12C32.67 326.72 39.94 295.95 56.28 274.5C57.96 272.3 62.51 267.24 66.39 263.25L73.45 256L62.72 256C56.52 256 52 255.59 52 255.04C52 253.72 110.02 74.94 111.16 72.75C111.96 71.22 113.7 71 125.04 71C132.17 71 138 71.38 138 71.84C138 72.48 85.9 233.81 81 248.33L80.05 251.17L83.27 249.01C85.05 247.82 90.55 244.88 95.5 242.49C127.99 226.77 166.8 229.58 197.96 249.9C199.32 250.78 200.15 251.05 199.82 250.5C198.92 249.01 142 73.4 142 72.11C142 71.35 146.17 71 155.02 71C167.57 71 168.08 71.08 169 73.25C170.22 76.11 228 254.42 228 255.32C228 255.7 223.22 256 217.37 256L206.73 256L214.21 263.83C227.49 277.73 235.83 292.49 240.74 310.79C243.03 319.34 243.35 322.42 243.35 336.5C243.35 350.67 243.04 353.64 240.68 362.43C230.96 398.72 202.72 427.13 166.5 437.06C155.03 440.2 130.05 440.75 118 438.12ZM284 439.56C284 439.31 295.93 402.38 310.5 357.49C325.07 312.6 337 275.22 337 274.43C337 273.64 336.41 273 335.69 273C333.03 273 316.28 263.72 309.3 258.38C290.46 243.95 277.51 224.49 271.26 201.21C268.97 192.66 268.65 189.58 268.65 175.5C268.65 161.33 268.96 158.36 271.32 149.57C284.64 99.83 331.69 66.88 382.02 72.05C406.14 74.52 426.52 83.95 444.15 100.78C486.93 141.59 486.55 210.08 443.32 251C434.28 259.55 422.09 267.64 412.8 271.24C409.61 272.48 407 273.9 407 274.41C407 274.91 418.93 312.08 433.5 357C448.07 401.92 460 438.97 460 439.34C460 439.7 454 440 446.67 440L433.34 440L407.3 359.8L381.26 279.6L372.13 279.54L363 279.49L358.56 292.99C356.11 300.42 345.74 332.38 335.5 364C325.26 395.62 315.52 425.66 313.86 430.75L310.84 440L297.42 440C290.04 440 284 439.8 284 439.56ZM160.33 414.04C182.45 408.38 203.49 390.63 213.05 369.56C218.38 357.8 220.29 347.31 219.72 333C219.15 318.59 217.09 310.73 210.82 299C195.77 270.83 166.4 254.3 135.04 256.35C123.19 257.12 115.8 259.03 105.42 264.01C88.57 272.1 76.34 284.36 68.01 301.5C61.99 313.91 60 322.67 60 336.79C60 389.2 109.23 427.11 160.33 414.04ZM23.46 254.75C23.2 254.06 23.1 212.55 23.24 162.5L23.5 71.5L35.25 71.22L47 70.94L47 163.47L47 256L35.47 256C27.16 256 23.8 255.65 23.46 254.75ZM384.31 254.89C394.61 253.29 406.88 248.56 415.77 242.76C438.94 227.63 452 203.39 452 175.5C452 117.4 393.21 78.98 339.54 101.98C327.43 107.17 312.94 119.56 304.97 131.53C287.88 157.2 287.59 192.48 304.25 218.27C321.99 245.72 352.71 259.78 384.31 254.89Z"

SVG_SMALL = f'<svg viewBox="0 0 512 512" width="16" height="16"><path d="{LOGO_PATH}" fill="#6183fc" fill-rule="evenodd"/></svg>'
SVG_BIG = f'<svg viewBox="0 0 512 512" width="80" height="80"><path d="{LOGO_PATH}" fill="#6183fc" fill-rule="evenodd"/></svg>'
SVG_LOGIN = f'<svg viewBox="0 0 512 512" width="32" height="32"><path d="{LOGO_PATH}" fill="#6183fc" fill-rule="evenodd"/></svg>'

# index.html: titlebar + empty state + hide tabs
try:
    with open("/app/static/index.html") as f:
        html = f.read()
    
    # Titlebar icon
    m = re.search(r'<span class="app-titlebar-icon".*?</span>', html, re.DOTALL)
    if m and "6183fc" not in m.group():
        html = html[:m.start()] + f'<span class="app-titlebar-icon" aria-hidden="true">{SVG_SMALL}</span>' + html[m.end():]
    
    # Empty state icon
    m2 = re.search(r'<div class="empty-logo">.*?</div>', html, re.DOTALL)
    if m2 and "6183fc" not in m2.group():
        html = html[:m2.start()] + f'<div class="empty-logo">{SVG_BIG}</div>' + html[m2.end():]
    
    # Hide tabs CSS
    if "HIDE_KANBAN_TODOS" not in html:
        html = html.replace("</head>", '<style>/* HIDE_KANBAN_TODOS */ [data-panel="kanban"],[data-panel="todos"]{display:none!important;}</style></head>')
    
    with open("/app/static/index.html", "w") as f:
        f.write(html)
except Exception as e:
    print(f"index.html error: {e}")

# routes.py: login page logo
try:
    with open("/app/api/routes.py") as f:
        c = f.read()
    
    c = c.replace(
        '.logo{width:48px;height:48px;border-radius:12px;background:linear-gradient(145deg,#e8a030,#e94560);',
        '.logo{width:48px;height:48px;border-radius:12px;background:#1a1a2e;'
    )
    c = c.replace(
        '<div class="logo">{{BOT_NAME_INITIAL}}</div>',
        f'<div class="logo">{SVG_LOGIN}</div>'
    )
    
    with open("/app/api/routes.py", "w") as f:
        f.write(c)
except Exception as e:
    print(f"routes.py error: {e}")

print("Branding applied")
