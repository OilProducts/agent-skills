#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  mk_worktrees.sh --repo <repo> --run-dir <run-dir> [options]

Options:
  --repo <path>          Git repository root
  --run-dir <path>       Run directory where worktrees are created
  --base-ref <ref>       Base ref for both worktrees (default: HEAD)
  --doer-branch <name>   Branch name for doer worktree (default: generated)
  --judge-branch <name>  Branch name for judge worktree (default: generated)
  --judge-writable       Leave judge worktree writable
  --force                Remove existing worktrees at target paths
  -h, --help             Show this help
USAGE
}

repo=""
run_dir=""
base_ref="HEAD"
doer_branch=""
judge_branch=""
judge_readonly="1"
force="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --run-dir)
      run_dir="${2:-}"
      shift 2
      ;;
    --base-ref)
      base_ref="${2:-}"
      shift 2
      ;;
    --doer-branch)
      doer_branch="${2:-}"
      shift 2
      ;;
    --judge-branch)
      judge_branch="${2:-}"
      shift 2
      ;;
    --judge-writable)
      judge_readonly="0"
      shift
      ;;
    --force)
      force="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "${repo}" || -z "${run_dir}" ]]; then
  echo "error: --repo and --run-dir are required" >&2
  usage
  exit 2
fi

if [[ ! -d "${repo}" ]]; then
  echo "error: repo directory not found: ${repo}" >&2
  exit 1
fi

if ! git -C "${repo}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: ${repo}" >&2
  exit 1
fi

if ! git -C "${repo}" rev-parse --verify "${base_ref}^{commit}" >/dev/null 2>&1; then
  echo "error: base ref not found: ${base_ref}" >&2
  exit 1
fi

mkdir -p "${run_dir}"
run_dir="$(cd "${run_dir}" && pwd)"
repo="$(cd "${repo}" && pwd)"

stamp="$(date +%Y%m%d-%H%M%S)"
if [[ -z "${doer_branch}" ]]; then
  doer_branch="codex/loop-${stamp}-doer"
fi
if [[ -z "${judge_branch}" ]]; then
  judge_branch="codex/loop-${stamp}-judge"
fi

worktrees_dir="${run_dir}/worktrees"
doer_dir="${worktrees_dir}/doer"
judge_dir="${worktrees_dir}/judge"

if [[ "${force}" == "1" ]]; then
  git -C "${repo}" worktree remove --force "${doer_dir}" >/dev/null 2>&1 || true
  git -C "${repo}" worktree remove --force "${judge_dir}" >/dev/null 2>&1 || true
  rm -rf "${doer_dir}" "${judge_dir}"
fi

if [[ -e "${doer_dir}" || -e "${judge_dir}" ]]; then
  echo "error: worktree path already exists (use --force to replace)" >&2
  echo "doer: ${doer_dir}" >&2
  echo "judge: ${judge_dir}" >&2
  exit 1
fi

mkdir -p "${worktrees_dir}"

git -C "${repo}" worktree add -B "${doer_branch}" "${doer_dir}" "${base_ref}" >/dev/null
git -C "${repo}" worktree add -B "${judge_branch}" "${judge_dir}" "${base_ref}" >/dev/null

if [[ "${judge_readonly}" == "1" ]]; then
  chmod -R u-w,go-w "${judge_dir}"
fi

env_file="${run_dir}/worktrees.env"
cat > "${env_file}" <<ENV
REPO=${repo}
BASE_REF=${base_ref}
DOER_BRANCH=${doer_branch}
JUDGE_BRANCH=${judge_branch}
DOER_DIR=${doer_dir}
JUDGE_DIR=${judge_dir}
JUDGE_READONLY=${judge_readonly}
ENV

printf '%s\n' "${env_file}"
