# Doer Artifact Contract

The doer must emit two artifacts.

## `patch.diff`

- Generated with `git diff --binary`.
- Must apply cleanly on the expected base checkout.
- Must include all implementation changes for the round.

## `handoff.json`

Required top-level keys:

- `task_id` (string)
- `summary` (string)
- `requirements_touched` (array of requirement IDs)
- `files_touched` (array of strings)
- `assumptions` (array of strings)
- `smoke_checks` (array of objects)
- `notes` (string)

`smoke_checks` item shape:

- `command` (string)
- `status` (string, one of `pass`, `fail`, `skip`, `unknown`)

Example:

```json
{
  "task_id": "TASK-0042",
  "summary": "Implemented password-reset endpoint and request validation.",
  "requirements_touched": [
    "RQ-0102",
    "NFR-0001"
  ],
  "files_touched": [
    "src/auth/reset.py",
    "tests/test_reset.py"
  ],
  "assumptions": [
    "ASMP-0012"
  ],
  "smoke_checks": [
    {"command": "pytest -q tests/test_reset.py", "status": "pass"},
    {"command": "ruff check src/auth/reset.py", "status": "pass"}
  ],
  "notes": "No migration required."
}
```
