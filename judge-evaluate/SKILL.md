---
name: judge-evaluate
description: Evaluate a proposed implementation patch and handoff artifact against task scope and verification checks, then produce a machine-readable `verdict.json`. Use when a doer has delivered `patch.diff` and `handoff.json` and a separate judging role must accept, reject, or escalate without editing source files.
---

# Judge Evaluate

Assess doer output and produce a structured verdict artifact.

## Role Boundaries

- Evaluate; do not implement fixes.
- Base conclusions on concrete evidence (commands, logs, artifacts).
- Write verdict output only.
- Do not claim merge/release readiness unless explicitly asked as a separate gate.

## Required Inputs

- `task_id` and task statement
- `patch.diff`
- `handoff.json`
- output path for `verdict.json`

Optional:
- explicit eval command list
- scoring rubric overrides

## Workflow

### 1) Verify handoff integrity

- Validate that required doer artifacts exist.
- Read `handoff.json` for touched files, assumptions, and smoke checks.
- Flag malformed or missing handoff fields as `needs-human` or `reject` depending on severity.

### 2) Evaluate implementation evidence

Run deterministic checks when commands are provided:

```bash
python3 <path-to-skill>/scripts/run_eval.py \
  --repo <repo-root> \
  --output <artifact-path>/eval-results.json \
  --command "pytest -q" \
  --command "ruff check ."
```

- Keep outputs in machine-readable form.
- Treat failed eval commands as evidence for rejection unless out of scope.

### 3) Build verdict

Run:

```bash
python3 <path-to-skill>/scripts/write_verdict.py \
  --task-id <task-id> \
  --output <artifact-path>/verdict.json \
  --eval-results <artifact-path>/eval-results.json \
  --verdict reject \
  --reason "tests::2 failures in auth reset flow" \
  --requirement-checked "RQ-0102" \
  --requirement-missing "NFR-0001" \
  --required-change "Handle invalid token branch" \
  --suggested-test "pytest -q tests/test_reset.py::test_invalid_token"
```

Use one of:
- `pass`
- `reject`
- `needs-human`

### 4) Validate verdict artifact

Run:

```bash
python3 <path-to-skill>/scripts/validate_verdict.py \
  --input <artifact-path>/verdict.json
```

## Evaluation Rules

- Prefer `reject` when evidence shows unmet behavior or failing checks.
- Use `needs-human` for ambiguous requirements, missing context, or conflicting constraints.
- Keep `required_changes` implementation-neutral and actionable.

## Output Rules

- Always produce `verdict.json`.
- Include concrete `reasons` with `check` and `details`.
- Keep `suggested_tests` runnable.
- Keep `requirements_checked` and `requirements_missing` in stable ID form (`RQ-####`, `NFR-####`, `ASMP-####`, `ADR-####`).

## Resources

### scripts/
- `scripts/run_eval.py`: execute eval commands and persist structured results.
- `scripts/write_verdict.py`: synthesize `verdict.json` from evidence and explicit findings.
- `scripts/validate_verdict.py`: enforce required verdict shape and enums.

### references/
- `references/artifact-contract.md`: canonical verdict schema and examples.
- `references/scoring-rubric.md`: lightweight scoring framework for consistent decisions.
