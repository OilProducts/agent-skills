#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-}"
COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8188}"

auto_detect_repo() {
  if [ -n "$REPO" ]; then
    return
  fi
  if [ -f "$PWD/comfyui/main.py" ]; then
    REPO="$PWD"
    return
  fi
  if [ -d "/home/chris/projects/local-image-gen" ] && [ -f "/home/chris/projects/local-image-gen/comfyui/main.py" ]; then
    REPO="/home/chris/projects/local-image-gen"
    return
  fi
  echo "[ERROR] Could not auto-detect repo. Set REPO=/path/to/local-image-gen" >&2
  exit 1
}

auto_detect_repo
LOG="${LOG:-$REPO/comfyui/comfy.log}"

if curl -fsS "$COMFY_URL/system_stats" >/dev/null 2>&1; then
  echo "[OK] ComfyUI already running at $COMFY_URL"
  exit 0
fi

if [ ! -f "$REPO/.venv/bin/python" ]; then
  echo "[ERROR] Missing venv python at $REPO/.venv/bin/python" >&2
  exit 1
fi

if [ ! -f "$REPO/comfyui/main.py" ]; then
  echo "[ERROR] Missing $REPO/comfyui/main.py" >&2
  exit 1
fi

mkdir -p "$(dirname "$LOG")"
cd "$REPO/comfyui"
nohup "$REPO/.venv/bin/python" main.py --listen "$HOST" --port "$PORT" > "$LOG" 2>&1 &
PID=$!
echo "[OK] Started ComfyUI pid=$PID log=$LOG"
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
