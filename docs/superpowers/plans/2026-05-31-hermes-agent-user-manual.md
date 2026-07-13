# Hermes Agent 使用手冊 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a comprehensive Hermes Agent user manual (`docs/hermes/README.md`) in the WOOWTECH/Woow_odoo_instance repo, matching the depth and quality of the Inzense manual (2252 lines, 27 chapters, 194 screenshots, 71 tables).

**Architecture:** Use `playwright-cli` to capture all screenshots from `https://woowtech-hermes.woowtech.io`. Manual covers all WebUI features (Chat, Tasks, Kanban, Skills, Memory, Profiles, Settings, Insights, Logs) plus Agent CLI tools and automation capabilities. Images stored in `docs/hermes/images/`, manual in `docs/hermes/README.md`. Follow the exact structure pattern of the Inzense manual: version header → TOC table → step-by-step chapters with screenshots.

**Tech Stack:** Playwright CLI (screenshots), GitHub CLI (push), Markdown

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `docs/hermes/README.md` | Complete user manual (~2500 lines, 25 chapters) |
| Create | `docs/hermes/images/ch*.png` | ~150-200 screenshots from woowtech-hermes |

---

## Chapter Outline (25 Chapters)

| # | Chapter | Screens to Capture | Tables |
|---|---------|-------------------|--------|
| 1 | 平台總覽與帳號說明 | — | 3 (URLs, accounts, architecture) |
| 2 | 登入與首次設定 | login page, password fill, login success, first-run wizard steps 1-5 | 2 |
| 3 | Chat 對話介面 | empty chat, quick actions, message sent, response received, activity panel, model selector | 3 |
| 4 | Chat 進階功能 | file attach, dictate, fork, copy, regenerate, edit message, conversation list, filter | 2 |
| 5 | Skills 技能中心 | skills sidebar, skill categories, skill detail, search | 3 |
| 6 | Skills — Odoo 18 ERP 專屬技能 | 8 odoo skills detail | 1 |
| 7 | Tasks 任務管理 | tasks list, new task, task detail, task status | 2 |
| 8 | Kanban 看板 | kanban board, new board, card drag, dispatcher | 2 |
| 9 | Memory 記憶管理 | memory page, SOUL.md editor, USER.md, MEMORY.md | 3 |
| 10 | Agent Profiles 設定檔 | profiles list, new profile, switch profile | 2 |
| 11 | Spaces 工作區 | spaces list, add space, workspace files panel | 2 |
| 12 | Todos 待辦事項 | todos list, add todo, check/uncheck | 1 |
| 13 | Insights 數據分析 | insights dashboard, token usage chart, model breakdown, daily stats | 3 |
| 14 | Logs 日誌查看 | logs viewer, error log, agent log | 1 |
| 15 | Settings 設定 | settings page, conversation export, import, clear | 2 |
| 16 | 模型與 Provider 設定 | model selector dropdown, provider list, Minimax config | 3 |
| 17 | Gateway 閘道管理 | gateway status, gateway running indicator | 2 |
| 18 | Workspace Files 面板 | file tree, artifacts tab | 1 |
| 19 | CLI 工具總覽 — 網路與連線 | terminal examples (curl, ssh, nmap) | 2 |
| 20 | CLI 工具總覽 — 開發與搜尋 | terminal examples (git, jq, python3, node) | 2 |
| 21 | CLI 工具總覽 — 雲端與 DevOps | terminal examples (helm, gcloud, gh) | 2 |
| 22 | CLI 工具總覽 — 文件與媒體 | terminal examples (pandoc, ffmpeg, yt-dlp) | 2 |
| 23 | Playwright + Chromium 瀏覽器自動化 | browser automation demo | 2 |
| 24 | 行動裝置操作指南 | mobile login, mobile chat, mobile nav | 1 |
| 25 | 常見問題 FAQ | — | 1 |

**Estimated totals:** ~2500 lines, 25 chapters, ~180 screenshots, ~45 tables

---

### Task 1: Capture Chapter 1-2 Screenshots (Login & Setup)

**Files:**
- Create: `docs/hermes/images/ch01_*.png` (0 images, text-only chapter)
- Create: `docs/hermes/images/ch02_*.png` (8 images)

- [ ] **Step 1: Open browser and capture login page**

```bash
playwright-cli open https://woowtech-hermes.woowtech.io
playwright-cli screenshot --filename=docs/hermes/images/ch02_01_login_page.png
```

- [ ] **Step 2: Fill password and capture**

```bash
playwright-cli fill "getByRole('textbox', { name: 'Password' })" "${WEBUI_PASSWORD}"
playwright-cli screenshot --filename=docs/hermes/images/ch02_02_login_filled.png
```

- [ ] **Step 3: Submit and capture main page + wizard**

```bash
playwright-cli press Enter
# Wait for page load
playwright-cli screenshot --filename=docs/hermes/images/ch02_03_login_success.png
# Capture wizard steps
playwright-cli screenshot --filename=docs/hermes/images/ch02_04_wizard_step1.png
playwright-cli click "getByRole('button', { name: 'Continue' })"
playwright-cli screenshot --filename=docs/hermes/images/ch02_05_wizard_step2.png
playwright-cli click "getByRole('button', { name: 'Skip setup' })"
playwright-cli screenshot --filename=docs/hermes/images/ch02_06_main_page.png
```

- [ ] **Step 4: Capture wrong password error**

```bash
# Open new session for error screenshot
playwright-cli goto https://woowtech-hermes.woowtech.io/login
playwright-cli fill "getByRole('textbox', { name: 'Password' })" "wrongpassword"
playwright-cli press Enter
playwright-cli screenshot --filename=docs/hermes/images/ch02_07_login_error.png
```

---

### Task 2: Capture Chapter 3-4 Screenshots (Chat)

**Files:**
- Create: `docs/hermes/images/ch03_*.png` (10 images)
- Create: `docs/hermes/images/ch04_*.png` (8 images)

- [ ] **Step 1: Capture empty chat page with quick actions**

```bash
playwright-cli screenshot --filename=docs/hermes/images/ch03_01_chat_empty.png
```

- [ ] **Step 2: Send a message and capture conversation flow**

```bash
playwright-cli fill "getByRole('textbox', { name: 'Message Hermes' })" "你好，請介紹一下你的功能"
playwright-cli screenshot --filename=docs/hermes/images/ch03_02_chat_typing.png
playwright-cli click "getByRole('button', { name: 'Send message' })"
# Wait 20s for response
playwright-cli screenshot --filename=docs/hermes/images/ch03_03_chat_response.png
```

- [ ] **Step 3: Capture model selector, profile selector, workspace controls**

```bash
playwright-cli click "getByRole('button', { name: 'Minimax M2.7' })"
playwright-cli screenshot --filename=docs/hermes/images/ch03_04_model_selector.png
# Close dropdown
playwright-cli press Escape
```

- [ ] **Step 4: Capture chat advanced features (fork, copy, regenerate, edit)**

Screenshot the message action buttons, conversation list sidebar, filter controls.

---

### Task 3: Capture Chapter 5-6 Screenshots (Skills)

**Files:**
- Create: `docs/hermes/images/ch05_*.png` (6 images)
- Create: `docs/hermes/images/ch06_*.png` (4 images)

- [ ] **Step 1: Navigate to Skills and capture list**

```bash
playwright-cli click "getByRole('button', { name: 'Skills' })"
playwright-cli screenshot --filename=docs/hermes/images/ch05_01_skills_list.png
```

- [ ] **Step 2: Search and capture filtered results**

```bash
# Type in search box
playwright-cli fill "getByRole('searchbox')" "odoo"
playwright-cli screenshot --filename=docs/hermes/images/ch05_02_skills_search.png
```

- [ ] **Step 3: Click a skill and capture detail view**

```bash
playwright-cli click "text=odoo-sales-crm"
playwright-cli screenshot --filename=docs/hermes/images/ch06_01_skill_detail.png
```

---

### Task 4: Capture Chapter 7-12 Screenshots (Tasks, Kanban, Memory, Profiles, Spaces, Todos)

**Files:**
- Create: `docs/hermes/images/ch07_*.png` through `ch12_*.png` (~24 images)

- [ ] **Step 1: Navigate to each section and capture**

For each of: Tasks, Kanban, Memory, Agent Profiles, Spaces, Todos:
1. Click nav button
2. Screenshot the main view
3. If applicable, click "New" and screenshot the creation form
4. Screenshot any detail views

---

### Task 5: Capture Chapter 13-18 Screenshots (Insights, Logs, Settings, Model, Gateway, Files)

**Files:**
- Create: `docs/hermes/images/ch13_*.png` through `ch18_*.png` (~20 images)

- [ ] **Step 1: Capture Insights dashboard**

```bash
playwright-cli click "getByRole('button', { name: 'Insights' })"
playwright-cli screenshot --filename=docs/hermes/images/ch13_01_insights.png
```

- [ ] **Step 2: Capture Logs viewer**

```bash
playwright-cli click "getByRole('button', { name: 'Logs' })"
playwright-cli screenshot --filename=docs/hermes/images/ch14_01_logs.png
```

- [ ] **Step 3: Capture Settings**

```bash
playwright-cli click "getByRole('button', { name: 'Settings' })"
playwright-cli screenshot --filename=docs/hermes/images/ch15_01_settings.png
```

---

### Task 6: Capture Chapter 19-23 Screenshots (CLI Tools & Playwright)

**Files:**
- Create: `docs/hermes/images/ch19_*.png` through `ch23_*.png` (~15 images)

These are terminal output screenshots captured via the Hermes chat interface, asking Hermes to run CLI commands and screenshotting the results.

- [ ] **Step 1: Send CLI demo messages via chat**

Ask Hermes to run various commands and capture the output in chat:
- `curl https://api.github.com` (networking)
- `python3 --version && node --version` (dev tools)
- `helm version` (DevOps)
- `pandoc --version` (content)
- Playwright browser automation demo

---

### Task 7: Capture Chapter 24 Screenshots (Mobile)

**Files:**
- Create: `docs/hermes/images/ch24_*.png` (6 images)

- [ ] **Step 1: Resize to mobile and capture key screens**

```bash
playwright-cli resize 375 812
playwright-cli goto https://woowtech-hermes.woowtech.io
playwright-cli screenshot --filename=docs/hermes/images/ch24_01_mobile_login.png
# Login
playwright-cli fill "getByRole('textbox', { name: 'Password' })" "${WEBUI_PASSWORD}" --submit
playwright-cli screenshot --filename=docs/hermes/images/ch24_02_mobile_chat.png
# Open nav
playwright-cli screenshot --filename=docs/hermes/images/ch24_03_mobile_nav.png
```

---

### Task 8: Write README.md — Chapters 1-6

**Files:**
- Create: `docs/hermes/README.md`

- [ ] **Step 1: Write header, TOC, and Chapters 1-6**

Write the manual following the Inzense pattern:
- Version header with metadata
- TOC table with all 25 chapters
- Ch 1: Platform overview (URLs, accounts, architecture, CLI tools summary)
- Ch 2: Login & first-run wizard (step-by-step with screenshots)
- Ch 3: Chat basics (empty state, send message, response, model selector)
- Ch 4: Chat advanced (fork, copy, regenerate, file attach, dictate)
- Ch 5: Skills center (browsing, search, categories)
- Ch 6: Odoo 18 ERP custom skills (8 skills detail)

Each chapter follows:
```markdown
## N. Chapter Title

本章說明 ...

### 步驟 1：Description

![Alt text](images/chNN_01_name.png)

> **提示**：Useful tip here
```

---

### Task 9: Write README.md — Chapters 7-12

- [ ] **Step 1: Write Chapters 7-12**

- Ch 7: Tasks management
- Ch 8: Kanban boards
- Ch 9: Memory management (SOUL.md, USER.md, MEMORY.md)
- Ch 10: Agent Profiles
- Ch 11: Spaces / Workspaces
- Ch 12: Todos

---

### Task 10: Write README.md — Chapters 13-18

- [ ] **Step 1: Write Chapters 13-18**

- Ch 13: Insights analytics
- Ch 14: Logs viewer
- Ch 15: Settings (export, import, clear)
- Ch 16: Model & Provider configuration
- Ch 17: Gateway management
- Ch 18: Workspace Files panel

---

### Task 11: Write README.md — Chapters 19-25

- [ ] **Step 1: Write Chapters 19-25**

- Ch 19: CLI tools — networking (curl, ssh, nmap, dig, etc.)
- Ch 20: CLI tools — development (git, jq, python3, node, etc.)
- Ch 21: CLI tools — cloud/DevOps (helm, gcloud, gh, argocd, etc.)
- Ch 22: CLI tools — content (pandoc, ffmpeg, imagemagick, yt-dlp)
- Ch 23: Playwright + Chromium automation
- Ch 24: Mobile guide
- Ch 25: FAQ

---

### Task 12: Push to GitHub

**Files:**
- Push: `docs/hermes/` to WOOWTECH/Woow_odoo_instance main branch

- [ ] **Step 1: Clone repo and add files**

```bash
cd /tmp
gh repo clone WOOWTECH/Woow_odoo_instance
cd Woow_odoo_instance
cp -r /path/to/docs/hermes docs/hermes
git add docs/hermes/
git commit -m "docs: add Hermes Agent comprehensive user manual (25 chapters, ~180 screenshots)"
git push origin main
```

- [ ] **Step 2: Verify on GitHub**

```bash
gh browse docs/hermes/README.md
```

---

## Summary

| Metric | Target | Reference (Inzense) |
|--------|--------|-------------------|
| Lines | ~2500 | 2252 |
| Chapters | 25 | 27 |
| Screenshots | ~180 | 194 |
| Tables | ~45 | 71 |
| Language | 繁體中文 | 繁體中文 |
| Demo URL | woowtech-hermes.woowtech.io | inzense-odoo.woowtech.io |
