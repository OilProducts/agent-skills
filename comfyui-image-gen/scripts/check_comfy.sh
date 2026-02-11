#!/usr/bin/env bash
set -euo pipefail

COMFY_URL="http://127.0.0.1:8188"
CHECK_OBJECT_INFO=0
TIMEOUT=5

usage() {
  cat <<USAGE
Usage: $0 [--comfy-url URL] [--check-object-info] [--timeout-sec N]

Options:
  --comfy-url URL         ComfyUI base URL (default: http://127.0.0.1:8188)
  --check-object-info     Also verify GET /object_info
  --timeout-sec N         curl timeout seconds (default: 5)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --comfy-url) COMFY_URL="$2"; shift 2 ;;
    --check-object-info) CHECK_OBJECT_INFO=1; shift ;;
    --timeout-sec) TIMEOUT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

echo "[INFO] Checking $COMFY_URL/system_stats"
if curl -fsS -m "$TIMEOUT" "$COMFY_URL/system_stats" >/dev/null; then
  echo "[OK] ComfyUI system_stats reachable"
else
  echo "[ERROR] Cannot reach $COMFY_URL/system_stats" >&2
  exit 1
fi

if [[ "$CHECK_OBJECT_INFO" -eq 1 ]]; then
  echo "[INFO] Checking $COMFY_URL/object_info"
  if curl -fsS -m "$TIMEOUT" "$COMFY_URL/object_info" >/dev/null; then
    echo "[OK] ComfyUI object_info reachable"
  else
    echo "[ERROR] Cannot reach $COMFY_URL/object_info" >&2
    exit 1
  fi
fi

echo "[OK] ComfyUI health check complete"
