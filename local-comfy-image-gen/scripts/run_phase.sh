#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PIPELINE_REPO="${PIPELINE_REPO:-}"
COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
DEFAULT_PIPELINE_REPO="$SKILL_ROOT"
BOOK_ID=""
PAGE=""
PHASE=""
RENDERSPEC=""
REVIEW=""
SOURCE_IMAGE=""
COMFY_INPUT_DIR=""
BOOKS_DIR="${BOOKS_DIR:-}"
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
  --comfy-input-dir PATH     (optional: copy source image for Comfy LoadImage)
  --books-dir PATH           (default: BOOKS_DIR env or ./books)
  --repo PATH                (default: pipeline auto-detect from cwd)
  --comfy-url URL            (default: COMFY_URL env or http://127.0.0.1:8188)
  --dry-run
USAGE
}

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
  echo "[ERROR] Could not auto-detect pipeline repo. Use --repo or set PIPELINE_REPO." >&2
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
    --comfy-input-dir) COMFY_INPUT_DIR="$2"; shift 2 ;;
    --books-dir) BOOKS_DIR="$2"; shift 2 ;;
    --repo) PIPELINE_REPO="$2"; shift 2 ;;
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

auto_detect_pipeline_repo

[ -f "$PIPELINE_REPO/orchestrator/run_page.py" ] || { echo "missing $PIPELINE_REPO/orchestrator/run_page.py" >&2; exit 1; }
if [ ! -f "$RENDERSPEC" ] && [ -f "$PIPELINE_REPO/$RENDERSPEC" ]; then
  RENDERSPEC="$PIPELINE_REPO/$RENDERSPEC"
fi
[ -f "$RENDERSPEC" ] || { echo "--renderspec not found: $RENDERSPEC" >&2; exit 1; }
if [ -z "$BOOKS_DIR" ]; then
  BOOKS_DIR="$PWD/books"
fi

cmd=(python3 "$PIPELINE_REPO/orchestrator/run_page.py"
  --book-id "$BOOK_ID"
  --page "$PAGE"
  --phase "$PHASE"
  --renderspec "$RENDERSPEC"
  --workflow-dir "$PIPELINE_REPO/workflows"
  --books-dir "$BOOKS_DIR"
  --comfy-url "$COMFY_URL"
)

if [ -n "$REVIEW" ]; then
  cmd+=(--review "$REVIEW")
fi
if [ -n "$SOURCE_IMAGE" ]; then
  cmd+=(--source-image "$SOURCE_IMAGE")
fi
if [ -n "$COMFY_INPUT_DIR" ]; then
  cmd+=(--comfy-input-dir "$COMFY_INPUT_DIR")
fi
if [ "$DRY_RUN" -eq 1 ]; then
  cmd+=(--dry-run)
fi

echo "[INFO] Using pipeline repo: $PIPELINE_REPO"
echo "[INFO] Using books dir: $BOOKS_DIR"
echo "[INFO] Using ComfyUI: $COMFY_URL"
echo "[INFO] Running: ${cmd[*]}"
"${cmd[@]}"
