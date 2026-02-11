#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-}"
COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
BOOK_ID=""
PAGE=""
PHASE=""
RENDERSPEC=""
REVIEW=""
SOURCE_IMAGE=""
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: $0 --book-id ID --page PAGE --phase PHASE --renderspec PATH [options]

Required:
  --book-id ID
  --page PAGE
  --phase draft|refine|inpaint|upscale_print
  --renderspec PATH

Optional:
  --review PATH
  --source-image PATH
  --repo PATH                (default: auto-detect from cwd)
  --comfy-url URL            (default: COMFY_URL env or http://127.0.0.1:8188)
  --dry-run
USAGE
}

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
  echo "[ERROR] Could not auto-detect repo. Use --repo /path/to/local-image-gen" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --book-id) BOOK_ID="$2"; shift 2 ;;
    --page) PAGE="$2"; shift 2 ;;
    --phase) PHASE="$2"; shift 2 ;;
    --renderspec) RENDERSPEC="$2"; shift 2 ;;
    --review) REVIEW="$2"; shift 2 ;;
    --source-image) SOURCE_IMAGE="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --comfy-url) COMFY_URL="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[ -n "$BOOK_ID" ] || { echo "--book-id is required" >&2; exit 1; }
[ -n "$PAGE" ] || { echo "--page is required" >&2; exit 1; }
[ -n "$PHASE" ] || { echo "--phase is required" >&2; exit 1; }
[ -n "$RENDERSPEC" ] || { echo "--renderspec is required" >&2; exit 1; }

case "$PHASE" in
  draft|refine|inpaint|upscale_print) ;;
  *) echo "Invalid --phase: $PHASE" >&2; exit 1 ;;
esac

auto_detect_repo

[ -f "$REPO/orchestrator/run_page.py" ] || { echo "missing $REPO/orchestrator/run_page.py" >&2; exit 1; }

cmd=(python3 "$REPO/orchestrator/run_page.py"
  --book-id "$BOOK_ID"
  --page "$PAGE"
  --phase "$PHASE"
  --renderspec "$RENDERSPEC"
  --workflow-dir "$REPO/workflows"
  --books-dir "$REPO/books"
  --comfy-url "$COMFY_URL"
)

if [ -n "$REVIEW" ]; then
  cmd+=(--review "$REVIEW")
fi
if [ -n "$SOURCE_IMAGE" ]; then
  cmd+=(--source-image "$SOURCE_IMAGE")
fi
if [ "$DRY_RUN" -eq 1 ]; then
  cmd+=(--dry-run)
fi

echo "[INFO] Using repo: $REPO"
echo "[INFO] Using ComfyUI: $COMFY_URL"
echo "[INFO] Running: ${cmd[*]}"
"${cmd[@]}"
