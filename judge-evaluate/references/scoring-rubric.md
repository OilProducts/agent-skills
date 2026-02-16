# Judge Scoring Rubric

Use this rubric to keep verdicts consistent.

## Core Dimensions

- Functional correctness
- Task-scope adherence
- Regression risk from touched files
- Evidence quality (tests/check outputs)

## Decision Guidance

- `pass`:
  - No failing required checks
  - No unmet task-critical behavior
- `reject`:
  - Required checks fail
  - Task-critical behavior missing or incorrect
- `needs-human`:
  - Requirements are ambiguous or conflicting
  - Evidence is incomplete and cannot be reproduced reliably

## Required Changes Style

- Phrase as actionable constraints, not implementation prescriptions.
- Keep each change independently testable.
- Prefer 1:1 mapping between reasons and required changes where possible.
