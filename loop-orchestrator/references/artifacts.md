# Artifact Contract

Use stable machine-readable artifacts so roles do not communicate through prose.

## `handoff.json`

Required fields:

```json
{
  "task_id": "TASK-0042",
  "summary": "Implemented X and Y",
  "requirements_touched": ["RQ-0102"],
  "files_touched": ["src/a.py", "tests/test_a.py"],
  "assumptions": ["ASMP-0012"],
  "smoke_checks": [
    {"command": "pytest -q tests/test_a.py", "status": "pass"}
  ],
  "notes": "Optional short note"
}
```

## `verdict.json`

Required fields:

```json
{
  "task_id": "TASK-0042",
  "verdict": "reject",
  "reasons": [
    {"check": "tests", "details": "2 failures in tests/test_a.py"}
  ],
  "required_changes": [
    "Handle invalid token error path"
  ],
  "suggested_tests": [
    "pytest -q tests/test_a.py::test_invalid_token"
  ],
  "requirements_checked": ["RQ-0102"],
  "requirements_missing": ["NFR-0001"],
  "notes": ""
}
```

Rules:
- `verdict` must be `pass|reject|needs-human`.
- `required_changes` should be actionable and implementation-neutral.

## `audit.json`

Required fields:

```json
{
  "task_id": "TASK-0042",
  "gate": "fail",
  "risk": {
    "level": "high",
    "reasons": ["Traceability mismatch"]
  },
  "findings": [
    {"category": "traceability", "details": "task_id mismatch across artifacts"}
  ],
  "policy": {
    "artifact_integrity": "fail",
    "eval_commands": "pass"
  },
  "traceability": {
    "task_id_match": "fail",
    "requirements_coverage": "unknown",
    "issues": ["task_id mismatch across artifacts"]
  },
  "required_actions": [
    "Regenerate artifacts with aligned task_id"
  ],
  "notes": ""
}
```

Rules:
- `gate` must be `pass|fail|needs-human`.
- `required_actions` should explain what blocks landing.

## `summary.json`

Produced by orchestrator after loop completion.

```json
{
  "task_id": "TASK-0042",
  "final_verdict": "reject",
  "rounds_completed": 2,
  "run_dir": "/abs/path/.orchestrator/runs/TASK-0042-20260216-130000",
  "judge_verdict": "pass",
  "audit_gate": "fail",
  "audit_enabled": true
}
```
