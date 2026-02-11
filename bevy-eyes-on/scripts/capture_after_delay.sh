#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  capture_after_delay.sh [options]

Options:
  --delay-seconds <n>    Seconds to wait before capture (default: 2)
  --app <name>           App name for targeted capture
  --window-id <id>       Window id for targeted capture
  --mode <mode>          Screenshot mode passed to take_screenshot.py (default: temp)
  --path <file>          Explicit output file path
  --launch-cmd <cmd>     Optional command to launch app before waiting
  --launch-cwd <dir>     Working directory for --launch-cmd (default: current dir)
  --launch-wait <n>      Wait after launch before delay starts (default: 2)
  --keep-running         Keep launched process running after capture
  --debug-dir <dir>      Optional debug output directory
  -h, --help             Show this help
EOF
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
screenshot_dir="$(cd "${script_dir}/../../screenshot/scripts" && pwd)"
take_script="${screenshot_dir}/take_screenshot.py"
perm_script="${screenshot_dir}/ensure_macos_permissions.sh"

delay_seconds="2"
app_name=""
window_id=""
mode="temp"
output_path=""
launch_cmd=""
launch_cwd=""
launch_wait="2"
keep_running="0"
debug_dir=""
launch_pid=""
launch_log=""

is_non_negative_number() {
  [[ "${1}" =~ ^[0-9]+([.][0-9]+)?$ ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --delay-seconds) delay_seconds="${2:-}"; shift 2 ;;
    --app) app_name="${2:-}"; shift 2 ;;
    --window-id) window_id="${2:-}"; shift 2 ;;
    --mode) mode="${2:-}"; shift 2 ;;
    --path) output_path="${2:-}"; shift 2 ;;
    --launch-cmd) launch_cmd="${2:-}"; shift 2 ;;
    --launch-cwd) launch_cwd="${2:-}"; shift 2 ;;
    --launch-wait) launch_wait="${2:-}"; shift 2 ;;
    --keep-running) keep_running="1"; shift ;;
    --debug-dir) debug_dir="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ ! -f "${take_script}" ]]; then
  echo "error: screenshot helper not found at ${take_script}" >&2
  exit 1
fi
if ! is_non_negative_number "${delay_seconds}"; then
  echo "error: --delay-seconds must be a non-negative number" >&2
  exit 2
fi
if ! is_non_negative_number "${launch_wait}"; then
  echo "error: --launch-wait must be a non-negative number" >&2
  exit 2
fi
if [[ -n "${window_id}" && ! "${window_id}" =~ ^[0-9]+$ ]]; then
  echo "error: --window-id must be an integer" >&2
  exit 2
fi
if [[ -n "${window_id}" && -n "${app_name}" ]]; then
  echo "error: pass either --window-id or --app, not both" >&2
  exit 2
fi
if [[ -z "${launch_cmd}" && -n "${launch_cwd}" ]]; then
  echo "error: --launch-cwd requires --launch-cmd" >&2
  exit 2
fi
if [[ -z "${launch_cmd}" && "${keep_running}" == "1" ]]; then
  echo "error: --keep-running requires --launch-cmd" >&2
  exit 2
fi
if [[ -n "${output_path}" && -n "${mode}" ]]; then
  mode=""
fi

if [[ -n "${debug_dir}" ]]; then
  mkdir -p "${debug_dir}"
fi

cleanup() {
  if [[ -n "${launch_pid}" && "${keep_running}" != "1" ]]; then
    kill "${launch_pid}" >/dev/null 2>&1 || true
    wait "${launch_pid}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ -x "${perm_script}" ]]; then
  if [[ -n "${debug_dir}" ]]; then
    bash "${perm_script}" > "${debug_dir}/permission.log" 2>&1 || true
  else
    bash "${perm_script}" >/dev/null 2>&1 || true
  fi
fi

if [[ -n "${launch_cmd}" ]]; then
  launch_root="${launch_cwd:-$PWD}"
  if [[ ! -d "${launch_root}" ]]; then
    echo "error: --launch-cwd directory does not exist: ${launch_root}" >&2
    exit 1
  fi
  if [[ -n "${debug_dir}" ]]; then
    launch_log="${debug_dir}/launch.log"
  else
    launch_log="/tmp/bevy-eyes-on-launch-$$.log"
  fi
  bash -lc "cd \"${launch_root}\" && ${launch_cmd}" > "${launch_log}" 2>&1 &
  launch_pid="$!"
  sleep "${launch_wait}"
fi

sleep "${delay_seconds}"

capture_one() {
  local label="$1"
  shift
  local out
  out="$(python3 "${take_script}" "$@" 2>&1 || true)"
  if [[ -n "${debug_dir}" ]]; then
    printf '%s\n' "${out}" > "${debug_dir}/capture-${label}.out"
  fi
  local shot_path
  shot_path="$(printf '%s\n' "${out}" | awk '/^\// {print; exit}')"
  if [[ -n "${shot_path}" && -f "${shot_path}" ]]; then
    printf '%s\n' "${shot_path}"
    return 0
  fi
  return 1
}

capture_args=()
if [[ -n "${output_path}" ]]; then
  capture_args+=(--path "${output_path}")
else
  if [[ -z "${mode}" ]]; then
    mode="temp"
  fi
  capture_args+=(--mode "${mode}")
fi

shot=""
if [[ -n "${window_id}" ]]; then
  shot="$(capture_one targeted-window --window-id "${window_id}" "${capture_args[@]}")" || true
elif [[ -n "${app_name}" ]]; then
  shot="$(capture_one targeted-app --app "${app_name}" "${capture_args[@]}")" || true
fi

if [[ -z "${shot}" ]]; then
  shot="$(capture_one fallback-full "${capture_args[@]}")" || true
fi

if [[ -z "${shot}" ]]; then
  echo "error: capture failed for targeted and fallback capture paths" >&2
  exit 1
fi

printf '%s\n' "${shot}"
