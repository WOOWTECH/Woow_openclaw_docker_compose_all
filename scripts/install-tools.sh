#!/bin/bash
set -euo pipefail
# ============================================================
# Vibe Kanban — CLI Toolkit Installer
# Runs as init container (K8s) or init service (podman-compose)
# Installs 50+ CLI tools to PVC / bind-mount for persistence
# ============================================================
W="/var/tmp/vibe-kanban"
PERSIST="$W/.tools"
BIN="$PERSIST/bin"
VENV="$PERSIST/venv"
MARKER="$PERSIST/.installed-v6"

# --- OpenCode ---
OC_DEST="$W/.bin"
mkdir -p "$OC_DEST"
chown 10001:10001 "$OC_DEST" 2>/dev/null || true
if [ ! -f "$OC_DEST/opencode" ] || ! "$OC_DEST/opencode" --version 2>&1 | grep -q "^[0-9]"; then
  apt-get update && apt-get install -y --no-install-recommends curl ca-certificates npm
  rm -f "$OC_DEST/opencode"
  curl -fsSL https://opencode.ai/install | HOME=/tmp bash -s -- --no-modify-path
  cp /tmp/.opencode/bin/opencode "$OC_DEST/opencode"
  chmod +x "$OC_DEST/opencode"
  chown 10001:10001 "$OC_DEST/opencode" 2>/dev/null || true
  echo "OpenCode installed: $($OC_DEST/opencode --version 2>&1)"
else
  echo "OpenCode OK: $($OC_DEST/opencode --version 2>&1)"
fi

# Always fix shared dir permissions (before marker check)
for d in "$W/.openchamber-config/opencode" "$W/.openchamber-config/opencode-share" "$W/.openchamber-config/opencode-state" "$W/.openchamber-config/openchamber" "$W/.host-repos" "$W/.host-local/share/vibe-kanban" "$W/.host-local/share/opencode" "$W/.host-local/state/opencode"; do
  mkdir -p "$d" && chmod 777 "$d" 2>/dev/null || true
done
chmod 777 "$W/.host-local" "$W/.host-local/share" "$W/.host-local/state" 2>/dev/null || true
# Seed profiles.json with OpenCode command override (if not exists)
if [ ! -f "$W/.host-local/share/vibe-kanban/profiles.json" ]; then
  echo '{"executors":{"OPENCODE":{"DEFAULT":{"OPENCODE":{"auto_approve":true,"auto_compact":true,"base_command_override":"/var/tmp/vibe-kanban/.bin/opencode"}}}}}' > "$W/.host-local/share/vibe-kanban/profiles.json"
  chmod 666 "$W/.host-local/share/vibe-kanban/profiles.json"
fi

if [ -f "$MARKER" ]; then
  echo "[SKIP] All tools already installed"
  exit 0
fi

# Remove old marker
rm -f "$PERSIST/.installed-v3" "$PERSIST/.installed-v4"

echo "========================================="
echo "  Installing full CLI toolkit to $PERSIST"
echo "========================================="
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  python3 python3-pip python3-venv python3-dev \
  curl ca-certificates wget gnupg unzip jq \
  build-essential pkg-config libssl-dev

mkdir -p "$BIN" "$PERSIST/dotnet" "$PERSIST/officecli"

# --- Static binaries (persist on PVC, not apt) ---
echo "[1/9] Static binaries (ffmpeg, rg, tmux)..."
# ripgrep
if [ ! -f "$BIN/rg" ]; then
  curl -sL "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-unknown-linux-musl.tar.gz" | \
    tar -xz --strip-components=1 -C /tmp ripgrep-14.1.1-x86_64-unknown-linux-musl/rg
  cp /tmp/rg "$BIN/rg" && chmod +x "$BIN/rg"
fi
# tmux (from apt, copy binary + deps to PVC)
apt-get install -y --no-install-recommends tmux
cp /usr/bin/tmux "$BIN/tmux" 2>/dev/null || true
# ffmpeg static
if [ ! -f "$BIN/ffmpeg" ]; then
  curl -sL "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" | \
    tar -xJ --strip-components=1 -C /tmp --wildcards '*/ffmpeg' '*/ffprobe' || \
  curl -sL "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz" | \
    tar -xJ --strip-components=2 -C /tmp --wildcards '*/bin/ffmpeg' '*/bin/ffprobe' || true
  cp /tmp/ffmpeg "$BIN/ffmpeg" 2>/dev/null && chmod +x "$BIN/ffmpeg" || true
  cp /tmp/ffprobe "$BIN/ffprobe" 2>/dev/null && chmod +x "$BIN/ffprobe" || true
fi

# --- uv ---
echo "[2/9] uv..."
if [ ! -f "$BIN/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | env CARGO_HOME=/tmp/cargo UV_INSTALL_DIR="$BIN" sh || true
fi

# --- Python venv (correct path = same as host mount) ---
echo "[3/9] Python venv..."
rm -rf "$VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install \
  anthropic openai mcp \
  httpx requests aiohttp websockets \
  fastapi uvicorn starlette \
  pydantic pillow lxml \
  rich click Jinja2 Markdown PyYAML \
  duckduckgo-search playwright \
  beautifulsoup4 html5lib cssselect \
  python-dotenv toml tomli \
  cryptography paramiko jsonschema pyjwt \
  tqdm colorama python-multipart \
  sse-starlette watchfiles orjson ujson \
  typing-extensions annotated-types anyio sniffio \
  certifi charset-normalizer idna urllib3 distro filelock \
  regex tenacity wrapt deprecated attrs cattrs \
  arrow python-dateutil markupsafe pygments numpy pandas

# --- Playwright Chromium + shared libs ---
echo "[4/9] Playwright Chromium..."
PLAYWRIGHT_BROWSERS_PATH="$PERSIST/pw-browsers" "$VENV/bin/python" -m playwright install --with-deps chromium || true
# Copy Chromium's shared lib deps to PVC so host container can use them
mkdir -p "$PERSIST/lib"
for lib in libglib-2.0.so.0 libgobject-2.0.so.0 libnspr4.so libnss3.so libnssutil3.so \
           libgio-2.0.so.0 libatk-1.0.so.0 libatk-bridge-2.0.so.0 libdbus-1.so.3 \
           libX11.so.6 libXcomposite.so.1 libXdamage.so.1 libXext.so.6 libXfixes.so.3 \
           libXrandr.so.2 libgbm.so.1 libxcb.so.1 libxkbcommon.so.0 libasound.so.2 \
           libatspi.so.0 libXi.so.6 libsmime3.so libplds4.so libplc4.so libgmodule-2.0.so.0 \
           libffi.so.8 libpcre2-8.so.0 libmount.so.1 libselinux.so.1 libblkid.so.1 \
           libXau.so.6 libXdmcp.so.6 libXrender.so.1 libdrm.so.2 libwayland-server.so.0 \
           libexpat.so.1 libxcb-dri3.so.0; do
  src=$(find /usr/lib /lib -name "$lib*" 2>/dev/null | head -1)
  if [ -n "$src" ] && [ ! -f "$PERSIST/lib/$lib" ]; then
    cp -L "$src" "$PERSIST/lib/$lib" 2>/dev/null || true
  fi
done
echo "  Copied $(ls $PERSIST/lib/*.so* 2>/dev/null | wc -l) shared libs to PVC"

# --- .NET Runtime ---
echo "[5/9] .NET Runtime..."
if [ ! -f "$PERSIST/dotnet/dotnet" ]; then
  curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin \
    --channel 8.0 --runtime dotnet --install-dir "$PERSIST/dotnet" --no-path || true
fi

# --- OfficeCLI ---
echo "[6/9] OfficeCLI..."
if [ ! -f "$BIN/officecli" ] || ! "$BIN/officecli" --version >/dev/null 2>&1; then
  curl -sL "https://github.com/iOfficeAI/OfficeCLI/releases/download/v1.0.135/officecli-linux-x64" \
    -o "$BIN/officecli" && chmod +x "$BIN/officecli" && \
  echo "  OfficeCLI: $($BIN/officecli --version 2>&1)" || echo "[WARN] OfficeCLI download failed"
fi

# --- Symlinks (use ABSOLUTE paths matching host mount) ---
echo "[7/9] Symlinks..."
for cmd in python3 pip pip3 ddgs uvicorn playwright; do
  ln -sf "$VENV/bin/$cmd" "$BIN/$cmd" 2>/dev/null || true
done
ln -sf "$PERSIST/dotnet/dotnet" "$BIN/dotnet" 2>/dev/null || true

# --- Fix ownership (including shared OpenChamber config dirs) ---
echo "[8/9] Fixing ownership..."
chown -R 10001:10001 "$PERSIST" "$OC_DEST" 2>/dev/null || true
# Ensure OpenChamber shared config dirs are writable by both host (10001) and openchamber (1000)
for d in "$W/.openchamber-config/opencode" "$W/.openchamber-config/opencode-share" "$W/.openchamber-config/opencode-state"; do
  mkdir -p "$d"
  chmod 777 "$d"
done

# --- Verify ---
echo "[9/9] Verification..."
echo "  rg: $($BIN/rg --version 2>&1 | head -1)"
echo "  ffmpeg: $($BIN/ffmpeg -version 2>&1 | head -1)"
echo "  tmux: $($BIN/tmux -V 2>&1)"
echo "  uv: $($BIN/uv --version 2>&1)"
echo "  python3: $($VENV/bin/python3 --version 2>&1)"
echo "  pip pkgs: $($VENV/bin/pip list 2>/dev/null | wc -l)"

date > "$MARKER"
echo "========================================="
echo "  All tools installed!"
echo "========================================="
rm -rf /var/lib/apt/lists/*
