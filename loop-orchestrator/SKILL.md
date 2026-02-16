---
name: loop-orchestrator
description: Orchestrate separated doer-judge-auditor software development loops with git worktrees, codex exec runs, and machine-readable handoff/verdict/audit artifacts. Use when a user asks to implement and verify iteratively with strict role separation, including optional governance gating before final acceptance.
---

# Loop Orchestrator

Run a repeatable `doer -> judge -> auditor` loop with explicit artifact handoff.

## Workflow

### 1) Define one task and one run

- Require a stable task ID (for example `TASK-0042`) and a concise task statement.
- Create a run directory under `.orchestrator/runs/`.
- Keep all loop evidence in the run directory.

### 2) Create separated worktrees

Run:

```bash
bash <path-to-skill>/scripts/mk_worktrees.sh --repo <repo> --run-dir <run-dir> --base-ref <ref>
```

- Keep `doer` worktree writable.
- Keep `judge` worktree read-only by default.
- Reuse judge worktree for auditor execution.

### 3) Run doer

Run `codex exec` in the doer worktree and require:
- `handoff.json`
- `patch.diff`

### 4) Apply patch and run judge

- Apply `patch.diff` to judge worktree.
- Run judge in read-only mode.
- Require `verdict.json`.

### 5) Run auditor gate (default)

- Run auditor in read-only mode after judge `pass`.
- Require `audit.json` with gate status `pass|fail|needs-human`.
- Map gate status to loop outcome:
  - `pass` -> final `pass`
  - `fail` -> final `reject` with feedback
  - `needs-human` -> final `needs-human`

Disable auditor stage only when explicitly needed:

```bash
bash <path-to-skill>/scripts/run_loop.sh ... --skip-audit
```

### 6) Iterate with feedback

- Feed judge/auditor required changes back to doer on the next round.
- Cap iterations with `--max-rounds`.
- Persist `summary.json` with judge and audit outcomes.
- Keep requirement-ID traceability across artifacts (`requirements_touched` -> `requirements_checked|requirements_missing`).

## Quick Start

```bash
bash <path-to-skill>/scripts/run_loop.sh \
  --repo /path/to/repo \
  --task-id TASK-0042 \
  --task "Implement password reset endpoint and tests" \
  --judge-eval "pytest -q" \
  --audit-eval "pip-audit" \
  --max-rounds 2
```

Inspect run artifacts:
- `rounds/round-*/handoff.json`
- `rounds/round-*/patch.diff`
- `rounds/round-*/verdict.json`
- `rounds/round-*/audit.json`
- `summary.json`

## Non-Negotiables

- Keep role separation strict.
- Exchange machine-readable artifacts only.
- Preserve traceability from task to evidence.

## Resources

### scripts/
- `scripts/mk_worktrees.sh`: create doer/judge worktrees with judge read-only by default.
- `scripts/run_loop.sh`: orchestrate doer, judge, and optional auditor rounds.

### references/
- `references/artifacts.md`: artifact contracts for handoff, verdict, audit, and summary.
- `references/prompt-templates.md`: default prompts and override pattern.
