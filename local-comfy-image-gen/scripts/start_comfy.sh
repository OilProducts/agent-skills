#!/usr/bin/env bash
set -euo pipefail

COMFY_RUNTIME_REPO="${COMFY_RUNTIME_REPO:-}"
COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
DEFAULT_RUNTIME_REPO="$HOME/projects/local-image-gen"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8188}"

auto_detect_runtime_repo() {
  if [ -n "$COMFY_RUNTIME_REPO" ]; then
    return
  fi
  if [ -f "$PWD/comfyui/main.py" ]; then
    COMFY_RUNTIME_REPO="$PWD"
    return
  fi
  if [ -f "$DEFAULT_RUNTIME_REPO/comfyui/main.py" ]; then
    COMFY_RUNTIME_REPO="$DEFAULT_RUNTIME_REPO"
    return
  fi
  echo "[ERROR] Could not auto-detect runtime repo. Set COMFY_RUNTIME_REPO." >&2
  exit 1
}

auto_detect_runtime_repo
LOG="${LOG:-$COMFY_RUNTIME_REPO/comfyui/comfy.log}"

if curl -fsS "$COMFY_URL/system_stats" >/dev/null 2>&1; then
  echo "[OK] ComfyUI already running at $COMFY_URL"
  exit 0
fi

if [ ! -f "$COMFY_RUNTIME_REPO/.venv/bin/python" ]; then
  echo "[ERROR] Missing venv python at $COMFY_RUNTIME_REPO/.venv/bin/python" >&2
  exit 1
fi

if [ ! -f "$COMFY_RUNTIME_REPO/comfyui/main.py" ]; then
  echo "[ERROR] Missing $COMFY_RUNTIME_REPO/comfyui/main.py" >&2
  exit 1
fi

mkdir -p "$(dirname "$LOG")"
cd "$COMFY_RUNTIME_REPO/comfyui"
nohup "$COMFY_RUNTIME_REPO/.venv/bin/python" main.py --listen "$HOST" --port "$PORT" > "$LOG" 2>&1 &
PID=$!
echo "[OK] Started ComfyUI pid=$PID log=$LOG"
echo "[INFO] Runtime repo: $COMFY_RUNTIME_REPO"
echo "[INFO] Bound to host=$HOST port=$PORT"

echo "[INFO] Waiting for API at $COMFY_URL ..."
for _ in $(seq 1 60); do
  if curl -fsS "$COMFY_URL/system_stats" >/dev/null 2>&1; then
    echo "[OK] ComfyUI ready at $COMFY_URL"
    exit 0
  fi
  sleep 1
done

echo "[ERROR] ComfyUI did not become ready in time" >&2
exit 1
