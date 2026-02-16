#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_loop.sh --repo <repo> --task-id <id> (--task <text> | --task-file <file>) [options]

Options:
  --repo <path>               Git repository root
  --task-id <id>              Task identifier (for example TASK-0042)
  --task <text>               Task statement
  --task-file <file>          Task statement file
  --base-ref <ref>            Base ref for doer/judge worktrees (default: HEAD)
  --run-root <path>           Root directory for loop runs (default: <repo>/.orchestrator/runs)
  --max-rounds <n>            Max doer->judge rounds (default: 1)
  --judge-eval <cmd>          Judge-side eval command (repeatable)
  --audit-eval <cmd>          Auditor-side eval command (repeatable)
  --doer-prompt-file <file>   Optional doer prompt template
  --judge-prompt-file <file>  Optional judge prompt template
  --audit-prompt-file <file>  Optional auditor prompt template
  --skip-audit                Disable auditor stage
  --judge-writable            Leave judge worktree writable
  --dry-run                   Write prompts and print commands without running codex
  -h, --help                  Show this help
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: required command not found: $1" >&2
    exit 1
  fi
}

json_field() {
  python3 - "$1" "$2" <<'PY'
import json, sys
path, key = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
value = data.get(key, "")
if isinstance(value, str):
    print(value)
else:
    print("")
PY
}

extract_feedback() {
  python3 - "$1" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
lines = []
for reason in data.get('reasons', []):
    check = str(reason.get('check', 'unknown')).strip()
    details = str(reason.get('details', '')).strip()
    if details:
        lines.append(f"- [{check}] {details}")
for change in data.get('required_changes', []):
    change = str(change).strip()
    if change:
        lines.append(f"- {change}")
print("\n".join(lines))
PY
}

extract_audit_feedback() {
  python3 - "$1" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
lines = []
for item in data.get('findings', []):
    category = str(item.get('category', 'finding')).strip()
    details = str(item.get('details', '')).strip()
    if details:
        lines.append(f"- [{category}] {details}")
for action in data.get('required_actions', []):
    action = str(action).strip()
    if action:
        lines.append(f"- {action}")
print("\n".join(lines))
PY
}

write_fallback_verdict() {
  local verdict_file="$1"
  local task_id="$2"
  cat > "${verdict_file}" <<JSON
{
  "task_id": "${task_id}",
  "verdict": "needs-human",
  "reasons": [
    {"check": "orchestrator", "details": "judge did not write verdict.json"}
  ],
  "required_changes": [
    "Re-run judge with explicit artifact output instructions"
  ],
  "suggested_tests": [],
  "requirements_checked": [],
  "requirements_missing": [],
  "notes": ""
}
JSON
}

write_fallback_audit() {
  local audit_file="$1"
  local task_id="$2"
  cat > "${audit_file}" <<JSON
{
  "task_id": "${task_id}",
  "gate": "needs-human",
  "risk": {
    "level": "high",
    "reasons": ["auditor did not write audit.json"]
  },
  "findings": [
    {"category": "orchestrator", "details": "auditor did not write audit.json"}
  ],
  "policy": {
    "artifact_integrity": "unknown",
    "eval_commands": "unknown"
  },
  "traceability": {
    "task_id_match": "unknown",
    "requirements_coverage": "unknown",
    "issues": ["missing audit artifact"]
  },
  "required_actions": [
    "Re-run auditor with explicit artifact output instructions"
  ],
  "notes": ""
}
JSON
}

repo=""
task_id=""
task_text=""
task_file=""
base_ref="HEAD"
run_root=""
max_rounds="1"
doer_prompt_file=""
judge_prompt_file=""
audit_prompt_file=""
dry_run="0"
judge_readonly="1"
run_audit="1"
declare -a judge_eval_cmds
declare -a audit_eval_cmds

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --task-id)
      task_id="${2:-}"
      shift 2
      ;;
    --task)
      task_text="${2:-}"
      shift 2
      ;;
    --task-file)
      task_file="${2:-}"
      shift 2
      ;;
    --base-ref)
      base_ref="${2:-}"
      shift 2
      ;;
    --run-root)
      run_root="${2:-}"
      shift 2
      ;;
    --max-rounds)
      max_rounds="${2:-}"
      shift 2
      ;;
    --judge-eval)
      judge_eval_cmds+=("${2:-}")
      shift 2
      ;;
    --audit-eval)
      audit_eval_cmds+=("${2:-}")
      shift 2
      ;;
    --doer-prompt-file)
      doer_prompt_file="${2:-}"
      shift 2
      ;;
    --judge-prompt-file)
      judge_prompt_file="${2:-}"
      shift 2
      ;;
    --audit-prompt-file)
      audit_prompt_file="${2:-}"
      shift 2
      ;;
    --skip-audit)
      run_audit="0"
      shift
      ;;
    --judge-writable)
      judge_readonly="0"
      shift
      ;;
    --dry-run)
      dry_run="1"
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

if [[ -z "${repo}" || -z "${task_id}" ]]; then
  echo "error: --repo and --task-id are required" >&2
  usage
  exit 2
fi
if [[ -n "${task_text}" && -n "${task_file}" ]]; then
  echo "error: use either --task or --task-file, not both" >&2
  exit 2
fi
if [[ -z "${task_text}" && -z "${task_file}" ]]; then
  echo "error: pass --task or --task-file" >&2
  exit 2
fi
if [[ -n "${task_file}" && ! -f "${task_file}" ]]; then
  echo "error: task file not found: ${task_file}" >&2
  exit 1
fi
if [[ -n "${task_file}" ]]; then
  task_text="$(cat "${task_file}")"
fi
if [[ -z "${task_text}" ]]; then
  echo "error: task text is empty" >&2
  exit 2
fi
if [[ ! "${max_rounds}" =~ ^[1-9][0-9]*$ ]]; then
  echo "error: --max-rounds must be a positive integer" >&2
  exit 2
fi
if [[ -n "${doer_prompt_file}" && ! -f "${doer_prompt_file}" ]]; then
  echo "error: doer prompt file not found: ${doer_prompt_file}" >&2
  exit 1
fi
if [[ -n "${judge_prompt_file}" && ! -f "${judge_prompt_file}" ]]; then
  echo "error: judge prompt file not found: ${judge_prompt_file}" >&2
  exit 1
fi
if [[ -n "${audit_prompt_file}" && ! -f "${audit_prompt_file}" ]]; then
  echo "error: audit prompt file not found: ${audit_prompt_file}" >&2
  exit 1
fi
if [[ -n "${task_id}" && ! "${task_id}" =~ ^TASK-[0-9A-Za-z._-]+$ ]]; then
  echo "warning: task id does not match TASK-* pattern: ${task_id}" >&2
fi

require_cmd git
require_cmd python3
if [[ "${dry_run}" != "1" ]]; then
  require_cmd codex
fi

repo="$(cd "${repo}" && pwd)"
if [[ ! -d "${repo}" ]]; then
  echo "error: repo not found: ${repo}" >&2
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

if [[ -z "${run_root}" ]]; then
  run_root="${repo}/.orchestrator/runs"
fi
mkdir -p "${run_root}"
run_root="$(cd "${run_root}" && pwd)"

stamp="$(date +%Y%m%d-%H%M%S)"
run_dir="${run_root}/${task_id}-${stamp}"
mkdir -p "${run_dir}/rounds"

echo "${task_text}" > "${run_dir}/task.txt"

judge_eval_lines=""
if [[ ${#judge_eval_cmds[@]} -eq 0 ]]; then
  judge_eval_lines="- No eval commands supplied. Judge must state evidence limits explicitly."
else
  for cmd in "${judge_eval_cmds[@]}"; do
    judge_eval_lines+="- ${cmd}"$'\n'
  done
fi

audit_eval_lines=""
if [[ ${#audit_eval_cmds[@]} -eq 0 ]]; then
  audit_eval_lines="- No audit commands supplied. Auditor must state evidence limits explicitly."
else
  for cmd in "${audit_eval_cmds[@]}"; do
    audit_eval_lines+="- ${cmd}"$'\n'
  done
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mk_script="${script_dir}/mk_worktrees.sh"
if [[ ! -x "${mk_script}" ]]; then
  echo "error: missing executable helper: ${mk_script}" >&2
  exit 1
fi

if [[ "${dry_run}" == "1" ]]; then
  doer_dir="${run_dir}/worktrees/doer"
  judge_dir="${run_dir}/worktrees/judge"
  echo "[DRY-RUN] skipping worktree creation"
else
  mk_args=(
    --repo "${repo}"
    --run-dir "${run_dir}"
    --base-ref "${base_ref}"
  )
  if [[ "${judge_readonly}" == "0" ]]; then
    mk_args+=(--judge-writable)
  fi
  bash "${mk_script}" "${mk_args[@]}" >/dev/null

  env_file="${run_dir}/worktrees.env"
  if [[ ! -f "${env_file}" ]]; then
    echo "error: missing worktree metadata: ${env_file}" >&2
    exit 1
  fi
  # shellcheck source=/dev/null
  source "${env_file}"
  doer_dir="${DOER_DIR}"
  judge_dir="${JUDGE_DIR}"
  judge_readonly="${JUDGE_READONLY}"
fi

round=1
final_verdict="needs-human"
feedback=""
rounds_completed="0"
last_judge_verdict="not-run"
last_audit_gate="not-run"

while [[ "${round}" -le "${max_rounds}" ]]; do
  round_dir="${run_dir}/rounds/round-${round}"
  mkdir -p "${round_dir}"

  handoff_file="${round_dir}/handoff.json"
  patch_file="${round_dir}/patch.diff"
  verdict_file="${round_dir}/verdict.json"
  audit_file="${round_dir}/audit.json"
  doer_last="${round_dir}/doer.last.md"
  judge_last="${round_dir}/judge.last.md"
  audit_last="${round_dir}/audit.last.md"
  doer_prompt="${round_dir}/doer.prompt.md"
  judge_prompt="${round_dir}/judge.prompt.md"
  audit_prompt="${round_dir}/audit.prompt.md"

  if [[ -n "${doer_prompt_file}" ]]; then
    cat "${doer_prompt_file}" > "${doer_prompt}"
  else
    cat > "${doer_prompt}" <<DOER
You are the doer agent in a separated doer/judge loop.
Use \$doer-implement as your primary workflow.

Task ID: ${task_id}
Task: ${task_text}
Round: ${round}/${max_rounds}

Implement the task in this repository checkout. Keep changes minimal.
Run smoke checks relevant to touched files.

Write JSON artifact to: ${handoff_file}
Write patch file to: ${patch_file}

Patch command requirement:
1) Run: git add -N .
2) Run: git diff --binary > "${patch_file}"

The handoff JSON must include keys:
- task_id
- summary
- requirements_touched (array of requirement IDs)
- files_touched (array)
- assumptions (array)
- smoke_checks (array of {command,status})
- notes
DOER
  fi

  {
    echo
    echo "## Orchestration Context"
    echo
    echo "- Doer worktree: ${doer_dir}"
    echo "- Round directory: ${round_dir}"
    echo "- Previous feedback (from judge/auditor):"
    if [[ -n "${feedback}" ]]; then
      printf '%s\n' "${feedback}"
    else
      echo "- none"
    fi
    echo
    echo "Do not evaluate final correctness beyond smoke checks."
  } >> "${doer_prompt}"

  doer_cmd=(
    codex exec
    --full-auto
    -C "${doer_dir}"
    --add-dir "${round_dir}"
    -o "${doer_last}"
    -
  )

  if [[ "${dry_run}" == "1" ]]; then
    echo "[DRY-RUN] doer command: ${doer_cmd[*]}"
  else
    "${doer_cmd[@]}" < "${doer_prompt}"

    if [[ ! -f "${patch_file}" ]]; then
      echo "error: doer did not produce patch file: ${patch_file}" >&2
      exit 1
    fi
    if [[ ! -f "${handoff_file}" ]]; then
      echo "error: doer did not produce handoff file: ${handoff_file}" >&2
      exit 1
    fi

    if [[ "${judge_readonly}" == "1" ]]; then
      chmod -R u+w "${judge_dir}"
    fi

    git -C "${judge_dir}" reset --hard "${base_ref}" >/dev/null
    git -C "${judge_dir}" clean -fd >/dev/null
    git -C "${judge_dir}" apply --check "${patch_file}"
    git -C "${judge_dir}" apply "${patch_file}"

    if [[ "${judge_readonly}" == "1" ]]; then
      chmod -R u-w,go-w "${judge_dir}"
    fi
  fi

  if [[ -n "${judge_prompt_file}" ]]; then
    cat "${judge_prompt_file}" > "${judge_prompt}"
  else
    cat > "${judge_prompt}" <<JUDGE
You are the judge agent in a separated doer/judge loop.
Use \$judge-evaluate as your primary workflow.

Task ID: ${task_id}
Task: ${task_text}
Round: ${round}/${max_rounds}

Do not modify repository source files.
Evaluate the applied patch for correctness and definition-of-done fit.

Inputs:
- Handoff JSON: ${handoff_file}
- Patch file: ${patch_file}

Eval commands to run when feasible:
${judge_eval_lines}

Write verdict JSON to: ${verdict_file}

The verdict JSON must include keys:
- task_id
- verdict (pass|reject|needs-human)
- reasons (array of {check,details})
- required_changes (array)
- suggested_tests (array)
- requirements_checked (array of IDs)
- requirements_missing (array of IDs)
- notes
JUDGE
  fi

  {
    echo
    echo "## Orchestration Context"
    echo
    echo "- Judge worktree: ${judge_dir}"
    echo "- Round directory: ${round_dir}"
    echo
    echo "Base verdict strictly on evidence from checks and artifacts."
  } >> "${judge_prompt}"

  judge_cmd=(
    codex exec
    --sandbox read-only
    --ask-for-approval never
    -C "${judge_dir}"
    --add-dir "${round_dir}"
    -o "${judge_last}"
    -
  )

  if [[ "${dry_run}" == "1" ]]; then
    echo "[DRY-RUN] judge command: ${judge_cmd[*]}"
    last_judge_verdict="dry-run"
    if [[ "${run_audit}" != "1" ]]; then
      final_verdict="dry-run"
      last_audit_gate="not-run"
      rounds_completed="1"
      break
    fi
  else
    "${judge_cmd[@]}" < "${judge_prompt}"

    if [[ ! -f "${verdict_file}" ]]; then
      write_fallback_verdict "${verdict_file}" "${task_id}"
    fi

    last_judge_verdict="$(json_field "${verdict_file}" "verdict")"
    if [[ -z "${last_judge_verdict}" ]]; then
      last_judge_verdict="needs-human"
    fi

    if [[ "${last_judge_verdict}" != "pass" ]]; then
      final_verdict="${last_judge_verdict}"
      feedback="$(extract_feedback "${verdict_file}")"
      rounds_completed="${round}"
      round=$((round + 1))
      continue
    fi
  fi

  if [[ "${run_audit}" != "1" ]]; then
    final_verdict="pass"
    last_audit_gate="not-run"
    rounds_completed="${round}"
    break
  fi

  if [[ -n "${audit_prompt_file}" ]]; then
    cat "${audit_prompt_file}" > "${audit_prompt}"
  else
    cat > "${audit_prompt}" <<AUDIT
You are the auditor in a separated doer/judge/auditor loop.
Use \$auditor-gate as your primary workflow.

Task ID: ${task_id}
Task: ${task_text}
Round: ${round}/${max_rounds}

Do not modify repository source files.
Apply governance and gate checks to decide whether this change is acceptable to land.

Inputs:
- Handoff JSON: ${handoff_file}
- Verdict JSON: ${verdict_file}
- Patch file: ${patch_file}

Audit commands to run when feasible:
${audit_eval_lines}

Write audit JSON to: ${audit_file}

The audit JSON must include keys:
- task_id
- gate (pass|fail|needs-human)
- findings (array of {category,details})
- required_actions (array)
- traceability (include task_id_match and requirements_coverage)
- notes
AUDIT
  fi

  {
    echo
    echo "## Orchestration Context"
    echo
    echo "- Auditor worktree: ${judge_dir}"
    echo "- Round directory: ${round_dir}"
    echo
    echo "Base gate decision strictly on artifact integrity, policy evidence, and traceability."
  } >> "${audit_prompt}"

  audit_cmd=(
    codex exec
    --sandbox read-only
    --ask-for-approval never
    -C "${judge_dir}"
    --add-dir "${round_dir}"
    -o "${audit_last}"
    -
  )

  if [[ "${dry_run}" == "1" ]]; then
    echo "[DRY-RUN] audit command: ${audit_cmd[*]}"
    final_verdict="dry-run"
    last_judge_verdict="dry-run"
    last_audit_gate="dry-run"
    rounds_completed="1"
    break
  fi

  "${audit_cmd[@]}" < "${audit_prompt}"

  if [[ ! -f "${audit_file}" ]]; then
    write_fallback_audit "${audit_file}" "${task_id}"
  fi

  last_audit_gate="$(json_field "${audit_file}" "gate")"
  if [[ -z "${last_audit_gate}" ]]; then
    last_audit_gate="needs-human"
  fi

  case "${last_audit_gate}" in
    pass)
      final_verdict="pass"
      rounds_completed="${round}"
      break
      ;;
    fail)
      final_verdict="reject"
      feedback="$(extract_audit_feedback "${audit_file}")"
      rounds_completed="${round}"
      round=$((round + 1))
      ;;
    *)
      final_verdict="needs-human"
      feedback="$(extract_audit_feedback "${audit_file}")"
      rounds_completed="${round}"
      round=$((round + 1))
      ;;
  esac
done

if [[ "${dry_run}" != "1" && "${rounds_completed}" == "0" ]]; then
  rounds_completed="${max_rounds}"
fi

summary_file="${run_dir}/summary.json"
python3 - "${summary_file}" "${task_id}" "${final_verdict}" "${rounds_completed}" "${run_dir}" "${last_judge_verdict}" "${last_audit_gate}" "${run_audit}" <<'PY'
import json, sys
(
    path,
    task_id,
    final_verdict,
    rounds_completed,
    run_dir,
    judge_verdict,
    audit_gate,
    audit_enabled,
) = sys.argv[1:]
payload = {
    "task_id": task_id,
    "final_verdict": final_verdict,
    "rounds_completed": int(rounds_completed),
    "run_dir": run_dir,
    "judge_verdict": judge_verdict,
    "audit_gate": audit_gate,
    "audit_enabled": audit_enabled == "1",
}
with open(path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2)
    f.write('\n')
PY

echo "run_dir=${run_dir}"
echo "final_verdict=${final_verdict}"
echo "judge_verdict=${last_judge_verdict}"
echo "audit_gate=${last_audit_gate}"
