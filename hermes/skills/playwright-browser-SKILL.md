---
name: playwright-browser
description: Browser automation with Playwright - navigate, click, fill forms, extract data, screenshot, and automate any website
version: 1.0
platforms: [webui, cli, api_server]
conditions:
  tools: [terminal]
---

# Playwright Browser Automation

## When to Use
Use this skill when the user asks to:
- Open, navigate, or interact with any website
- Fill forms, click buttons, login to websites
- Extract data or content from web pages
- Take screenshots of web pages
- Automate repetitive web tasks (e.g. BNI TYFCB submission)

## Environment Setup
Always set these before launching Playwright:

    import os
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/playwright-browsers"

## Quick Start Template

    import os
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/playwright-browsers"
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        page.goto("https://example.com", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)

        # Your automation here
        print(f"Title: {page.title()}")

        browser.close()

## Common Operations

### Login to a Website

    page.goto("https://site.com/login")
    page.wait_for_load_state("networkidle")
    page.fill("input[name=username]", "user@email.com")
    page.fill("input[name=password]", "password123")
    page.click("button:has-text('Sign In')")
    page.wait_for_url("**/dashboard**", timeout=30000)

### Fill a Form (Standard HTML)

    page.fill("input#name", "John")
    page.fill("input[type=email]", "john@example.com")
    page.select_option("select#country", "Taiwan")
    page.check("input[type=checkbox]#agree")
    page.click("button[type=submit]")

### Fill a Form (React MUI Components)

MUI components need JavaScript to trigger React's onChange:

For MUI TextField / Input:

    page.evaluate("""(selector, value) => {
        const el = document.querySelector(selector);
        const nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeSetter.call(el, value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }""", "input#amount", "2000")

For MUI Select dropdown:

    page.click(".MuiSelect-select")
    page.wait_for_selector("[role=option]")
    items = page.query_selector_all("[role=option]")
    for item in items:
        if "desired text" in item.text_content():
            item.click()
            break

For MUI Radio buttons:

    page.evaluate("""(name, value) => {
        const radio = document.querySelector(
            'input[name="' + name + '"][value="' + value + '"]'
        );
        radio.click();
    }""", "businessType", "NEW")

For MUI Textarea:

    page.evaluate("""(value) => {
        const el = document.querySelector('textarea');
        const nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        ).set;
        nativeSetter.call(el, value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
    }""", "Comment text here")

### Extract Data from a Page

    body_text = page.inner_text("body")
    title = page.text_content("h1")

    items = page.query_selector_all("table tr")
    for row in items:
        cells = row.query_selector_all("td")
        print([c.text_content().strip() for c in cells])

    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]')).map(a => ({
            text: a.textContent.trim().substring(0, 50),
            href: a.href
        }))
    }""")

### Wait for Dynamic Content

    page.wait_for_selector(".data-loaded", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_url("**/success**", timeout=30000)
    page.wait_for_selector("text=Success")

### Handle Popups and Dialogs

    with page.expect_popup() as popup_info:
        page.click("a[target=_blank]")
    popup = popup_info.value

    page.on("dialog", lambda dialog: dialog.accept())

### Take Screenshots

    page.screenshot(path="/tmp/screenshot.png")
    page.screenshot(path="/tmp/full.png", full_page=True)
    element = page.query_selector(".card")
    element.screenshot(path="/tmp/card.png")

## Playwright CLI Commands

Available via terminal for quick operations:

    playwright-cli open https://example.com
    playwright-cli goto https://other-page.com
    playwright-cli click "button#submit"
    playwright-cli fill "input#email" "user@example.com"
    playwright-cli snapshot
    playwright-cli screenshot
    playwright-cli close

## Important Rules

1. Always use headless=True with --no-sandbox and --disable-dev-shm-usage
2. Always set PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
3. Use timeout=30000 for page loads (30 seconds)
4. Use wait_for_load_state("networkidle") after navigation
5. For React/MUI sites, use evaluate() + dispatchEvent for inputs
6. Close the browser in a finally block or with statement

## Pitfalls

- page.fill() does NOT work on MUI components — use nativeInputValueSetter
- page.click("text=...") may timeout if element is behind a modal — use evaluate("el => el.click()") instead
- Radio buttons in React need .click() via JavaScript, not Playwright's .check()
- Always wait for dropdown options to render before selecting
- Some sites block headless browsers — add a realistic user agent if needed
