# Vibe Kanban — Podman/Docker Compose Deployment

Self-hosted Vibe Kanban suite via Docker Compose / Podman. Feature parity with the K3s deployment.

---

## Architecture

```
              Docker Network: vk-net
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
│ postgres │  │  remote  │  │ electric │  │  relay  │
│  :5432   │  │  :8081   │  │ (internal)│  │  :8082  │
└──────────┘  └──────────┘  └──────────┘  └─────────┘

    ┌── network_mode: service:host (shared localhost) ──┐
    │                                                   │
┌───┴──────┐  ┌──────────────┐  ┌─────────────┐
│   host   │  │ openchamber  │  │ mcp-service │
│  :3000   │  │   :3080      │  │ :8080/:8000 │
└──────────┘  └──────────────┘  └─────────────┘

┌─────────────┐
│ cloudflared │
│  (tunnel)   │
└─────────────┘
```

**9 services** (init runs once then exits):

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `db` | `postgres:16-alpine` | 5432 | PostgreSQL with `wal_level=logical` |
| `init` | `ubuntu:24.04` | — | Installs 50+ CLI tools, exits when done |
| `remote` | `vk-remote:v0.1.43` | 8081 | API server |
| `electric` | `electricsql/electric:1.4.13` | 3000 (internal) | Real-time sync engine |
| `relay` | `vk-relay:v0.1.43` | 8082 | Relay server |
| `host` | `vk-host:v0.1.43` | 3000 | Host UI (main container) |
| `openchamber` | `openchamber:latest` | 3080 | OpenCode Web GUI (sidecar) |
| `mcp-service` | `vk-mcp:v1.0` | 8080/8000 | MCP Admin + StreamableHttp (sidecar) |
| `cloudflared` | `cloudflared:latest` | — | Cloudflare Tunnel |

---

## Prerequisites

- Podman 4.x+ or Docker 24.x+ with Compose v2
- At least 8 GB RAM, 4 CPU cores
- Pre-built Vibe Kanban images (see [Build Images](#build-images))

---

## Quick Start

```bash
# 1. Clone
git clone -b podman https://github.com/WOOWTECH/Woow_vibekanban_docker_compose_all.git
cd Woow_vibekanban_docker_compose_all

# 2. Configure
cp .env.example .env
# Edit .env with your passwords and API keys

# 3. Build images (if not already built)
# See "Build Images" section below

# 4. Start
podman-compose up -d

# 5. Check status
podman-compose ps
podman-compose logs -f
```

### Access Points

| Service | URL |
|---------|-----|
| Host UI | `http://localhost:3000` |
| OpenChamber | `http://localhost:3080` |
| MCP Admin | `http://localhost:8080` |
| Remote API | `http://localhost:8081` |

---

## Build Images

The deployment requires 5 custom images. Build them using the script from the K3s branch:

```bash
# Ensure vibe-kanban source is available
# Then run: (from k3s branch)
bash k8s-manifests/vibe-kanban/build-vk-images.sh

# Verify images exist
podman images | grep -E "vk-|openchamber"
```

Required images:
- `localhost/vk-remote:v0.1.43`
- `localhost/vk-relay:v0.1.43`
- `localhost/vk-host:v0.1.43`
- `localhost/openchamber:latest`
- `localhost/vk-mcp:v1.0`

---

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `SERVER_DATABASE_URL` | Yes | Full database URL for remote/relay |
| `ELECTRIC_DATABASE_URL` | Yes | Database URL for ElectricSQL |
| `ELECTRIC_ROLE_PASSWORD` | Yes | ElectricSQL role password |
| `VIBEKANBAN_REMOTE_JWT_SECRET` | Yes | JWT secret (32+ chars) |
| `SELF_HOST_LOCAL_AUTH_EMAIL` | Yes | Admin login email |
| `SELF_HOST_LOCAL_AUTH_PASSWORD` | Yes | Admin login password |
| `MINIMAX_API_KEY` | No | MiniMax LLM API key |
| `CF_TUNNEL_TOKEN` | No | Cloudflare Tunnel token |
| `OPENCHAMBER_UI_PASSWORD` | No | OpenChamber login password |

---

## Persistence

All data persists via bind mounts under `./data/`:

| Host Path | Content |
|-----------|---------|
| `./data/postgres/` | PostgreSQL database files |
| `./data/electric/` | ElectricSQL sync state |
| `./data/workspace/` | CLI tools, OpenCode config, repos, profiles |

The workspace directory structure:
```
./data/workspace/
├── .tools/           # 50+ CLI tools (persisted)
├── .bin/             # OpenCode binary
├── .openchamber-config/
│   ├── opencode/     # Shared OpenCode config (Host + OpenChamber)
│   ├── openchamber/  # OpenChamber settings
│   ├── opencode-share/
│   └── opencode-state/
├── .host-repos/      # User git repos
└── .host-local/      # XDG local data + profiles.json
```

---

## Key Features

### Sidecar Pattern
OpenChamber and MCP Service use `network_mode: "service:host"` to share the Host container's network namespace. This replicates K8s pod sidecar behavior — all three containers communicate via `localhost`.

### Config Sharing
Host and OpenChamber share the same OpenCode config directory (`./data/workspace/.openchamber-config/opencode/`). Providers added in OpenChamber GUI are immediately visible to the Host's OpenCode executor.

### profiles.json Persistence
The init script seeds `profiles.json` with `base_command_override` pointing to the locally-installed OpenCode binary, ensuring the Host uses the correct version.

### Dotfile SPA Fix
OpenChamber's startup script works around an Express 5 dotfile detection bug by symlinking the dist directory to a dotfile-free path.

---

## Common Commands

```bash
# Start all services
podman-compose up -d

# Stop all services
podman-compose down

# View logs
podman-compose logs -f host
podman-compose logs -f openchamber

# Shell into host container
podman exec -it vk-host bash

# Check tool installation
podman exec vk-host rg --version
podman exec vk-host opencode --version

# Restart a single service
podman-compose restart host

# Full rebuild
podman-compose down && podman-compose up -d
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Init container fails | Check logs: `podman logs vk-init`. May need internet for downloads. |
| Remote not starting | Ensure DB is healthy: `podman exec vk-db pg_isready` |
| Electric connection error | Check `ELECTRIC_DATABASE_URL` has correct password. Remote must be running first. |
| OpenChamber 404 on routes | The dotfile fix should handle this. Check startup script logs. |
| Config not persisting | Verify `./data/workspace/.openchamber-config/` exists and has correct permissions (777). |
| Sidecar can't reach host | Verify `network_mode: "service:host"` is working. Fallback: use container name on vk-net. |

---

## License

MIT License — Copyright (c) 2026 Woowtech Smart Space Solution
