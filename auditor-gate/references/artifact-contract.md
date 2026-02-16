# Auditor Artifact Contract

The auditor emits one required artifact and one optional evidence report.

## Required: `audit.json`

Required top-level keys:

- `task_id` (string)
- `gate` (`pass` | `fail` | `needs-human`)
- `risk` (object)
- `findings` (array)
- `policy` (object)
- `traceability` (object)
- `required_actions` (array of strings)
- `notes` (string)

`risk` shape:
- `level` (`low` | `medium` | `high`)
- `reasons` (array of strings)

`findings` item shape:
- `category` (string)
- `details` (string)

`policy` shape:
- `artifact_integrity` (`pass` | `fail` | `unknown`)
- `eval_commands` (`pass` | `fail` | `unknown`)

`traceability` shape:
- `task_id_match` (`pass` | `fail` | `unknown`)
- `requirements_coverage` (`pass` | `fail` | `unknown`)
- `issues` (array of strings)

Example:

```json
{
  "task_id": "TASK-0042",
  "gate": "fail",
  "risk": {
    "level": "high",
    "reasons": ["Traceability mismatch between handoff and verdict"]
  },
  "findings": [
    {"category": "traceability", "details": "handoff task_id differs from verdict task_id"}
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
  "notes": "Gate failed due to artifact inconsistency."
}
```

## Optional: `audit-results.json`

Contains:
- artifact check list (`name`, `status`, `details`)
- executed command results (`command`, `status`, `exit_code`)
- summary counts
