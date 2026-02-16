# Gate Rubric

Use this rubric for consistent gate decisions.

## Core Dimensions

- Artifact integrity (`handoff.json`, `verdict.json` present and valid)
- Traceability consistency (`task_id` aligned across artifacts)
- Policy evidence (required audit commands and checks)
- Remediation clarity for non-pass decisions

## Decision Mapping

- `pass`:
  - no failed artifact/traceability checks
  - no failed required policy checks
- `fail`:
  - deterministic policy/traceability violation exists
- `needs-human`:
  - evidence missing or policy interpretation ambiguous

## Required Actions Quality

- Keep actions actionable and testable.
- Prefer one action per finding when practical.
- Avoid implementation-level prescriptions.
