---
name: enterprise-deployment-validation
description: Enterprise-grade validation of OpenClaw + Nerve + Ollama + LanceDB deployment on K3s
status: active
created: 2026-04-01T05:47:00Z
---

# PRD: OpenClaw + Nerve Enterprise Deployment Validation

## Executive Summary

Validate the complete OpenClaw AI Gateway stack deployed on a 9-node K3s cluster for enterprise production readiness. The system integrates 8 core components: OpenClaw Gateway (v2026.3.31), Nerve WebGUI (v1.5.2), Ollama local inference, memory-lancedb-pro vector memory, PostgreSQL+pgvector, Cloudflare Tunnel ingress, and multi-channel messaging (Telegram/LINE). This PRD defines a 5-round test suite covering API, browser E2E, cross-module integration, stress/edge cases, and security/persistence — producing auditable evidence that the deployment meets commercial-grade reliability.

## Problem Statement

The system was built incrementally across multiple implementation sessions. Individual components were tested in isolation, but no comprehensive end-to-end validation exists to confirm:
- All components interoperate correctly under realistic usage patterns
- The system survives pod restarts, network interruptions, and concurrent usage
- Security controls (auth, token injection, origin checks) function correctly
- Performance meets acceptable thresholds for commercial deployment
- Known limitations are documented with workarounds for operators

Without this validation, the deployment cannot be classified as production-ready for Woowtech's Smart Space platform.

## System Under Test

### Architecture

```
Internet
  │
  ├── https://cindytech1-openclaw.woowtech.io ──┐
  ├── https://cindytech1-nerve.woowtech.io ─────┤
  │                                              │
  │  Cloudflare Tunnel (cloudflared pod)         │
  │  ┌───────────────────────────────────────────┘
  │  │
  │  ▼  K3s Cluster (9 nodes)
  │
  │  ┌─ control-plane (16C/16GB) ──────────────────────┐
  │  │  Pod: openclaw-gateway (2 containers)            │
  │  │  ├── openclaw-gateway (v2026.3.31)  port 18789   │
  │  │  │   ├── memory-lancedb-pro (LanceDB + Ollama)   │
  │  │  │   ├── Telegram channel                        │
  │  │  │   └── Skills (64 installed)                   │
  │  │  └── nerve (v1.5.2)                 port 3080    │
  │  │      ├── Cron management                         │
  │  │      ├── Session management                      │
  │  │      └── Workspace file browser                  │
  │  │                                                  │
  │  │  PVC: openclaw-agents-pvc (1Gi, local-path)      │
  │  │    ├── _workspace/ _memory/ _extensions/         │
  │  │    ├── _nerve_app/ _nerve/ _openclaw_runtime/    │
  │  │    └── _openclaw.json                            │
  │  └─────────────────────────────────────────────────┘
  │
  │  ┌─ woowtechopenclaw-default-string (4C/16GB) ─┐
  │  │  Pod: ollama                                  │
  │  │  ├── nomic-embed-text (274MB, 768d vectors)   │
  │  │  └── llama3:8b (4.7GB, memory extraction)     │
  │  │  PVC: ollama-models-pvc (15Gi, nfs-data)      │
  │  └───────────────────────────────────────────────┘
  │
  │  ┌─ cluster4 (4C/4GB) ─────────────────────────┐
  │  │  Pod: openclaw-db (pgvector/pg16)             │
  │  │  PVC: openclaw-db-pvc (10Gi, local-path)      │
  │  └───────────────────────────────────────────────┘
```

### Component Versions

| Component | Version | Image | Node |
|-----------|---------|-------|------|
| OpenClaw Gateway | 2026.3.31 | openclaw-custom:latest + PVC runtime | control-plane |
| Nerve WebGUI | 1.5.2 | node:22-slim + PVC build cache | control-plane (sidecar) |
| Ollama | latest | ollama/ollama:latest | openclaw-default-string |
| memory-lancedb-pro | 1.1.0-beta.9 | PVC extension | control-plane |
| PostgreSQL | 16 + pgvector | pgvector/pgvector:pg16 | cluster4 |
| Cloudflared | latest | cloudflare/cloudflared:latest | control-plane |
| nomic-embed-text | latest | Ollama model (274MB) | openclaw-default-string |
| llama3:8b | latest | Ollama model (4.7GB) | openclaw-default-string |

## User Stories

### US-1: Operator validates Nerve WebGUI
**As** a platform operator, **I want** to log into Nerve, manage crons and skills, and chat with the AI agent **so that** I can confirm the web cockpit is fully functional for daily operations.

**Acceptance Criteria:**
- Login with password authentication succeeds
- Gateway handshake auto-connects (serverSideAuth)
- CHAT tab: send messages and receive streamed responses
- CRONS tab: lists existing cron jobs with status
- SKILLS tab: lists all 64 installed skills
- CONFIG tab: displays model/settings without errors
- MEMORY panel: shows stored memories
- WORKSPACE panel: browse files (MEMORY.md, SOUL.md, etc.)

### US-2: Operator validates memory system
**As** a platform operator, **I want** to verify that the AI remembers information across sessions **so that** I can confirm the LanceDB + Ollama memory pipeline works end-to-end.

**Acceptance Criteria:**
- Store facts in session A via natural conversation
- Recall facts in session B (different session ID)
- Semantic search returns results for paraphrased queries
- Noise filtering excludes trivial chat from storage
- Memory survives gateway pod restart

### US-3: Operator validates cron execution
**As** a platform operator, **I want** to verify cron jobs execute on schedule and deliver results **so that** I can trust automated tasks in production.

**Acceptance Criteria:**
- List crons via Nerve API returns job metadata
- Cron execution status shows lastRunStatus: ok
- Manual cron trigger via API succeeds
- Cron results visible in session history

### US-4: Operator validates multi-channel
**As** a platform operator, **I want** to verify Telegram channel works **so that** I can confirm the AI is reachable from messaging platforms.

**Acceptance Criteria:**
- Telegram bot responds to messages
- Telegram sessions visible in Nerve session list
- Memory recall works from Telegram-originated sessions

### US-5: Operator validates persistence
**As** a platform operator, **I want** to verify all data survives pod restarts **so that** I can trust the system won't lose state during maintenance.

**Acceptance Criteria:**
- Gateway pod restart: config, skills, memory, crons preserved
- Nerve sidecar restart: login works, cron/skill tabs load, chat reconnects
- Ollama pod restart: models still available, embedding works
- LanceDB data: memories accessible after restart

## Functional Requirements

### FR-1: API Layer Testing
- **FR-1.1**: Nerve auth API (login, logout, status, session validity)
- **FR-1.2**: Nerve crons API (list, create, toggle, delete, run, history)
- **FR-1.3**: Nerve skills API (list all skills with metadata)
- **FR-1.4**: Nerve gateway API (models, session-info, session-patch)
- **FR-1.5**: Nerve sessions API (list, history, send message)
- **FR-1.6**: Nerve connect-defaults API (wsUrl, serverSideAuth)
- **FR-1.7**: Nerve memory API (store, recall, search, forget)
- **FR-1.8**: Gateway /tools/invoke (cron tool via HTTP)
- **FR-1.9**: Ollama API (tags, embeddings, generate)
- **FR-1.10**: Gateway health/readiness probes

### FR-2: Browser E2E Testing
- **FR-2.1**: Login flow (password entry → authenticated state)
- **FR-2.2**: Auto-connect (serverSideAuth, no manual token needed)
- **FR-2.3**: Chat flow (type → send → receive streamed response)
- **FR-2.4**: Multi-turn conversation (context maintained within session)
- **FR-2.5**: Crons panel (view, toggle enable/disable)
- **FR-2.6**: Skills panel (list skills with descriptions)
- **FR-2.7**: Memory panel (view stored memories)
- **FR-2.8**: Workspace file browser (navigate, view file contents)
- **FR-2.9**: Session management (list sessions, switch sessions)
- **FR-2.10**: Model/effort selector (change model, change thinking effort)

### FR-3: Cross-Module Integration
- **FR-3.1**: Memory write via Nerve → recall via CLI agent command
- **FR-3.2**: Cron create via Nerve → verify execution via gateway logs
- **FR-3.3**: Workspace file edit via Nerve → verify via kubectl exec
- **FR-3.4**: Multi-session isolation (session A data not leaked to B)
- **FR-3.5**: Ollama embedding → LanceDB storage → vector search → recall

### FR-4: Stress & Edge Cases
- **FR-4.1**: Long message (>4000 characters) send and response
- **FR-4.2**: Rapid sequential messages (10 messages in 30 seconds)
- **FR-4.3**: WebSocket reconnection after network interruption
- **FR-4.4**: Concurrent sessions (3 simultaneous chat sessions)
- **FR-4.5**: Unicode/emoji/CJK handling in messages and memory
- **FR-4.6**: Empty message handling
- **FR-4.7**: Session reset and conversation clear

### FR-5: Security & Persistence
- **FR-5.1**: Unauthenticated API access returns 401
- **FR-5.2**: Invalid password returns 401
- **FR-5.3**: Gateway token not exposed to browser
- **FR-5.4**: OpenClaw port 18789 not externally accessible
- **FR-5.5**: Pod restart: gateway preserves all PVC data
- **FR-5.6**: Pod restart: Nerve reconnects and loads cached build
- **FR-5.7**: Pod restart: Ollama models persist on PVC
- **FR-5.8**: Pod restart: LanceDB memories survive
- **FR-5.9**: CORS: only allowed origins accepted for WebSocket

## Non-Functional Requirements

- **NFR-1**: Gateway response latency < 5 seconds for simple queries
- **NFR-2**: Nerve page load time < 3 seconds
- **NFR-3**: Memory recall accuracy > 80% for previously stored facts
- **NFR-4**: System uptime > 99% (excluding planned restarts)
- **NFR-5**: All PVC data survives at least 10 pod restart cycles
- **NFR-6**: WebSocket reconnection within 30 seconds of disruption

## Success Criteria

1. **Round 1 (API)**: All 10 API test groups return expected responses
2. **Round 2 (Browser)**: All 10 E2E scenarios pass with screenshot evidence
3. **Round 3 (Integration)**: All 5 cross-module tests demonstrate data flow
4. **Round 4 (Edge Cases)**: All 7 stress/edge tests handled gracefully
5. **Round 5 (Security)**: All 9 security/persistence checks pass
6. **Overall**: ≥90% test pass rate with all critical paths passing
7. **Documentation**: Known limitations catalogued with severity and workarounds

## Constraints & Assumptions

- Gateway pinned to v2026.3.31 (LINE channel has runtime module issue)
- PVC uses local-path StorageClass (no online volume expansion)
- Ollama runs CPU-only (no GPU, inference takes 5-15 seconds)
- Nerve image built from source at container startup (cached on PVC)
- Webchat protocol does not support binary image attachments
- Tests run from the K3s control-plane node (same network as cluster)

## Out of Scope

- LINE channel testing (known broken in v2026.3.31)
- WhatsApp channel testing (requires separate QR login)
- GPU acceleration for Ollama
- High-availability / multi-replica testing
- Load testing beyond 3 concurrent sessions
- Mobile-specific responsive testing
- TTS/STT voice features in Nerve
- Automated CI/CD pipeline for tests

## Dependencies

- K3s cluster operational with all 9 nodes
- Cloudflare tunnel active with DNS records
- Telegram bot token configured and valid
- At least one LLM API key (MiniMax, OpenAI, etc.) active
- Ollama models downloaded (nomic-embed-text, llama3:8b)
- Playwright installed on control-plane node
