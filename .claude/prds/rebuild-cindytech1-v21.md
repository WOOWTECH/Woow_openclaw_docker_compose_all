---
name: rebuild-cindytech1-v21
description: Full rebuild of cindytech1-openclaw instance using k3s branch v2.1 with persistence, multi-model, and skills
status: active
created: 2026-03-23T22:16:40Z
---

# PRD: rebuild-cindytech1-v21

## Executive Summary

使用 k3s branch 最新版本 (v2.1) 從零開始重建 cindytech1-openclaw.woowtech.io 實體。包含完整重設（刪除所有 secrets、PVC、部署）、重新建構自訂 Docker image（含 skill 依賴）、重建 setup wizard image、透過 setup wizard 完成初始設定、設定聊天頻道（LINE/Telegram）、安裝 workspace skills、以及最終驗證所有功能正常運作且資料可在 pod 重啟後保留。

## Problem Statement

目前的 cindytech1-openclaw 實體是經過多次 hotfix 和手動修改累積的狀態，需要用最新的 v2.1 codebase 乾淨重建，確保：
1. 所有 manifest 和 image 都是最新版本
2. 完整持久化矩陣（agents、workspace、memory、cron、telegram、config）正常運作
3. 多模型切換功能（MiniMax/DeepSeek/Qwen）正常
4. 15 個 skills 可用
5. 聊天頻道（LINE、Telegram）正確設定且持久化

## User Stories

### US-1: 全新部署
**As** 系統管理員
**I want** 用最新的 k3s v2.1 codebase 從零重建 OpenClaw 實體
**So that** 所有功能都基於乾淨的最新版本運作
**Acceptance Criteria:**
- 所有舊資源（secrets、PVC、deployments）已完全清除
- 使用最新的 manifest 和自訂 Docker image
- Setup wizard 可正常存取並完成設定

### US-2: 頻道設定持久化
**As** 使用者
**I want** 設定的 LINE 和 Telegram 頻道在 pod 重啟後仍然有效
**So that** 不需要每次重啟都重新設定
**Acceptance Criteria:**
- 透過 web GUI 設定 LINE/Telegram channel
- 手動重啟 pod 後頻道仍然 configured & running
- openclaw.json 保留在 PVC 上

### US-3: Skill 安裝持久化
**As** 使用者
**I want** 安裝的 workspace skills（如 homeassistant）在 pod 重啟後仍然存在
**So that** 不需要每次重啟都重新安裝
**Acceptance Criteria:**
- 透過 web GUI 或聊天安裝 skill
- Pod 重啟後 skill 仍然在 skills 列表中
- workspace 上傳的檔案也保留

### US-4: 多模型可切換
**As** 使用者
**I want** 在 web GUI 左上角下拉選單切換不同 AI 模型
**So that** 可以比較不同模型的回答品質
**Acceptance Criteria:**
- 建立多個 agent（如 GPT、MiniMax）
- 透過左上角下拉選單切換
- Agent 設定在 pod 重啟後保留

## Functional Requirements

### FR-1: 完整重設
- 刪除 `openclaw-secrets` K8s secret
- 刪除所有 PVC（`openclaw-agents-pvc`、`openclaw-db-pvc`）
- Scale down gateway 和 DB deployments
- 清除 Cloudflare tunnel ghost connections

### FR-2: 重建自訂 Docker Image
- 使用 `Dockerfile.custom` build `openclaw-custom:latest`
- 包含：jq, ripgrep, tmux, ffmpeg, gh CLI, clawhub, mcporter, gog, goplaces, summarize, uv
- Export 為 docker archive 並 import 到 K3s containerd

### FR-3: 重建 Setup Wizard Image
- 使用 `setup-wizard/Dockerfile` build `openclaw-setup-wizard:latest`
- 包含最新的 app.py（7 providers + CF retry + auth merge）和 index.html（淺色模式）
- Import 到 K3s containerd

### FR-4: Apply Manifests 並啟動 Setup Wizard
- Apply 全部 K8s manifests（00-06）
- 切換 Cloudflare route 到 setup-wizard
- Scale up setup-wizard
- 驗證 setup wizard 可透過 `https://cindytech1-openclaw.woowtech.io` 存取

### FR-5: 執行初始設定
- 透過 setup wizard web UI 填入：
  - Gateway Token
  - Database Password
  - AI Provider + API Key + Model
- Setup wizard 自動：建立 secrets → 啟動 DB → 啟動 Gateway → 設定 AI → 切換 CF route → 自毀

### FR-6: 設定聊天頻道
- 透過 web GUI 設定 LINE channel（Access Token + Secret）
- 透過 web GUI 設定 Telegram bot（Bot Token）
- 驗證頻道狀態為 Configured & Running

### FR-7: 安裝 Workspace Skills
- 透過 web GUI 安裝 homeassistant-skill
- 驗證 skill 出現在 skills 列表

### FR-8: 驗證持久化
- 手動刪除 pod 觸發重啟
- 確認以下全部保留：
  - openclaw.json（頻道設定）
  - agents/（agent profiles、auth keys）
  - workspace/（skills、上傳檔案、.md 檔）
  - memory/（對話記憶）
  - cron/（排程任務）
  - telegram/（bot state）

## Non-Functional Requirements

- Setup wizard 完成時間 < 3 分鐘
- Gateway cold start < 60 秒
- Pod 重啟後所有服務恢復時間 < 90 秒
- PVC storage: DB 10Gi, Agents 1Gi
- Gateway memory: 2Gi request, 8Gi limit

## Success Criteria

1. `https://cindytech1-openclaw.woowtech.io` 可正常存取
2. AI 模型可正常回答問題
3. 15 個 built-in skills ready
4. LINE 和 Telegram 頻道 configured & running
5. Pod 重啟後所有設定和資料保留
6. 左上角 agent 切換功能正常

## Constraints & Assumptions

- 自訂 Docker image 只能在 control-plane node 上 build（buildah 只在該 node 可用）
- Gateway pod 必須跑在 control-plane node（nodeSelector + image locality）
- PVC 使用 K3s local-path provisioner（node-local storage）
- Cloudflare tunnel 已建立（ID: 6cedc4aa...）
- 使用者會透過 setup wizard 選擇 AI provider

## Out of Scope

- 新增或修改 OpenClaw 內建 chat UI
- Docker Compose 部署方式
- 多租戶支援
- CI/CD pipeline 自動化
- SSL certificate 管理（由 Cloudflare 處理）

## Dependencies

- K3s cluster (4 nodes) 運作正常
- Cloudflare tunnel 已建立且 cloudflared pod running
- GitHub token 用於 push（如需要）
- AI provider API key（使用者在 setup wizard 提供）
- LINE channel token/secret（使用者在 web GUI 提供）
- Telegram bot token（使用者在 web GUI 提供）
