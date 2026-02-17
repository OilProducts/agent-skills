#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-${1:-}}"
COMFY_URL="${COMFY_URL:-http://192.168.1.224:8188}"

auto_detect_repo() {
  if [ -n "$REPO" ]; then
    return
  fi
  if [ -f "$PWD/orchestrator/run_page.py" ]; then
    REPO="$PWD"
    return
  fi
  if [ -d "/home/chris/projects/local-image-gen" ] && [ -f "/home/chris/projects/local-image-gen/orchestrator/run_page.py" ]; then
    REPO="/home/chris/projects/local-image-gen"
    return
  fi
  echo "[ERROR] Could not auto-detect repo. Pass path as first arg or set REPO." >&2
  exit 1
}

fail() {
  echo "[ERROR] $1" >&2
  exit 1
}

ok() {
  echo "[OK] $1"
}

auto_detect_repo

[ -d "$REPO" ] || fail "repo not found: $REPO"
[ -f "$REPO/orchestrator/run_page.py" ] || fail "missing orchestrator/run_page.py"
[ -f "$REPO/workflows/draft.api.json" ] || fail "missing workflows/draft.api.json"
[ -f "$REPO/workflows/draft.bindings.json" ] || fail "missing workflows/draft.bindings.json"
[ -d "$REPO/comfyui" ] || fail "missing comfyui directory"
[ -f "$REPO/comfyui/main.py" ] || fail "missing comfyui/main.py"

if [ -f "$REPO/comfyui/models/diffusion_models/flux1-dev.safetensors" ]; then
  ok "found FLUX model"
else
  echo "[WARN] FLUX model not found; fallback workflows may still run"
fi

if command -v python3 >/dev/null 2>&1; then
  ok "python3 available: $(python3 --version 2>/dev/null)"
else
  fail "python3 not found"
fi

if curl -fsS "$COMFY_URL/system_stats" >/dev/null 2>&1; then
  ok "ComfyUI API reachable at $COMFY_URL"
else
  echo "[WARN] ComfyUI API not reachable at $COMFY_URL"
fi

ok "setup check complete"
