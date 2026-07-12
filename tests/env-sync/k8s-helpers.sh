#!/bin/bash
# Helper functions for .env sync tests
# Usage: source this file, then call functions

CTX="woow-k3s"
NS="hermes"
POD="hermes-59fbdd5456-2vjmv"
CONTAINER="hermes-webui"
ENV_PATH="/home/hermeswebui/.hermes/.env"

MINIMAX_KEY="${MINIMAX_API_KEY:?Set MINIMAX_API_KEY env var}"
OPENAI_KEY="${OPENAI_API_KEY:?Set OPENAI_API_KEY env var}"

kexec() {
  kubectl --context "$CTX" -n "$NS" exec "$POD" -c "$CONTAINER" -- "$@"
}

# Set .env to have both keys
env_set_both() {
  kexec bash -c "printf 'MINIMAX_API_KEY=%s\nOPENAI_API_KEY=%s\n' '$MINIMAX_KEY' '$OPENAI_KEY' > $ENV_PATH"
  echo "[env] Set: MINIMAX + OPENAI"
}

# Set .env with only MINIMAX
env_set_minimax_only() {
  kexec bash -c "printf 'MINIMAX_API_KEY=%s\n' '$MINIMAX_KEY' > $ENV_PATH"
  echo "[env] Set: MINIMAX only"
}

# Set .env with only OPENAI
env_set_openai_only() {
  kexec bash -c "printf 'OPENAI_API_KEY=%s\n' '$OPENAI_KEY' > $ENV_PATH"
  echo "[env] Set: OPENAI only"
}

# Set .env with invalid OPENAI key
env_set_invalid_openai() {
  kexec bash -c "printf 'MINIMAX_API_KEY=%s\nOPENAI_API_KEY=sk-invalid-key-12345\n' '$MINIMAX_KEY' > $ENV_PATH"
  echo "[env] Set: MINIMAX + INVALID_OPENAI"
}

# Empty .env completely
env_set_empty() {
  kexec bash -c "truncate -s 0 $ENV_PATH"
  echo "[env] Set: EMPTY"
}

# Show current .env
env_show() {
  echo "[env] Current .env:"
  kexec cat "$ENV_PATH"
}

# Check if patches are applied
check_patches() {
  echo "[check] Patches in config.py:"
  kexec grep -c "_get_env_file_path\|_delete_models_cache_on_disk" /app/api/config.py
}
