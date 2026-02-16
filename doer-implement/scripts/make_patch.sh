#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  make_patch.sh --repo <repo> --output <patch-file> [--allow-empty]

Options:
  --repo <path>         Git repository root
  --output <path>       Output patch file path
  --allow-empty         Permit empty patch output
  -h, --help            Show this help
USAGE
}

repo=""
output=""
allow_empty="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --output)
      output="${2:-}"
      shift 2
      ;;
    --allow-empty)
      allow_empty="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "${repo}" || -z "${output}" ]]; then
  echo "error: --repo and --output are required" >&2
  usage
  exit 2
fi

if [[ ! -d "${repo}" ]]; then
  echo "error: repo not found: ${repo}" >&2
  exit 1
fi
if ! git -C "${repo}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: ${repo}" >&2
  exit 1
fi

mkdir -p "$(dirname "${output}")"

# Include intent-to-add entries so untracked files appear in diff output.
git -C "${repo}" add -N .
git -C "${repo}" diff --binary > "${output}"

if [[ "${allow_empty}" != "1" && ! -s "${output}" ]]; then
  echo "error: patch is empty: ${output}" >&2
  exit 1
fi

python3 - "${output}" <<'PY'
import os
import sys
path = os.path.abspath(sys.argv[1])
print(path)
PY
