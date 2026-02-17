#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PIPELINE_REPO="${PIPELINE_REPO:-${1:-}}"
COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
COMFY_RUNTIME_REPO="${COMFY_RUNTIME_REPO:-}"
DEFAULT_PIPELINE_REPO="$SKILL_ROOT"
DEFAULT_RUNTIME_REPO="$HOME/projects/local-image-gen"

auto_detect_pipeline_repo() {
  if [ -n "$PIPELINE_REPO" ]; then
    return
  fi
  if [ -f "$PWD/orchestrator/run_page.py" ]; then
    PIPELINE_REPO="$PWD"
    return
  fi
  if [ -f "$DEFAULT_PIPELINE_REPO/orchestrator/run_page.py" ]; then
    PIPELINE_REPO="$DEFAULT_PIPELINE_REPO"
    return
  fi
  echo "[ERROR] Could not auto-detect pipeline repo. Pass path arg, set PIPELINE_REPO, or run from pipeline repo." >&2
  exit 1
}

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
}

ok() {
  echo "[OK] $1"
}

warn() {
  echo "[WARN] $1"
}

auto_detect_pipeline_repo
auto_detect_runtime_repo

[ -d "$PIPELINE_REPO" ] || { echo "[ERROR] pipeline repo not found: $PIPELINE_REPO" >&2; exit 1; }
[ -f "$PIPELINE_REPO/orchestrator/run_page.py" ] || { echo "[ERROR] missing orchestrator/run_page.py in $PIPELINE_REPO" >&2; exit 1; }
[ -f "$PIPELINE_REPO/workflows/draft.api.json" ] || { echo "[ERROR] missing workflows/draft.api.json in $PIPELINE_REPO" >&2; exit 1; }
[ -f "$PIPELINE_REPO/workflows/draft.bindings.json" ] || { echo "[ERROR] missing workflows/draft.bindings.json in $PIPELINE_REPO" >&2; exit 1; }
ok "pipeline repo: $PIPELINE_REPO"

if [ -n "$COMFY_RUNTIME_REPO" ] && [ -f "$COMFY_RUNTIME_REPO/comfyui/main.py" ]; then
  ok "runtime repo: $COMFY_RUNTIME_REPO"
else
  warn "runtime repo not detected. Set COMFY_RUNTIME_REPO if this host should run ComfyUI."
fi

if [ -n "$COMFY_RUNTIME_REPO" ] && [ ! -f "$COMFY_RUNTIME_REPO/.venv/bin/python" ]; then
  warn "missing venv python at $COMFY_RUNTIME_REPO/.venv/bin/python"
fi

if [ -n "$COMFY_RUNTIME_REPO" ] && [ -f "$COMFY_RUNTIME_REPO/comfyui/models/diffusion_models/flux1-dev.safetensors" ]; then
  ok "found FLUX model in runtime repo"
elif [ -n "$COMFY_RUNTIME_REPO" ]; then
  warn "FLUX model not found in runtime repo; fallback workflows may still run"
fi

if command -v python3 >/dev/null 2>&1; then
  ok "python3 available: $(python3 --version 2>/dev/null)"
else
  echo "[ERROR] python3 not found" >&2
  exit 1
fi

if curl -fsS "$COMFY_URL/system_stats" >/dev/null 2>&1; then
  ok "ComfyUI API reachable at $COMFY_URL"
else
  warn "ComfyUI API not reachable at $COMFY_URL"
fi

ok "setup check complete"
