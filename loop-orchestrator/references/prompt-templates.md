# Prompt Templates

Use these templates when overriding defaults in `scripts/run_loop.sh`.

## Doer Template

Expected behavior:
- Implement task scope only.
- Run smoke checks.
- Write `handoff.json` and `patch.diff`.
- Include `requirements_touched` with stable IDs when available.
- Do not grade correctness beyond smoke checks.

## Judge Template

Expected behavior:
- Evaluate patch against task and required checks.
- Do not modify repository files.
- Write `verdict.json`.
- Include `requirements_checked` and `requirements_missing`.
- Keep reasons evidence-based and actionable.

## Auditor Template

Expected behavior:
- Evaluate governance gate readiness after judge pass.
- Do not modify repository files.
- Write `audit.json` with `gate` decision.
- Verify requirement traceability coverage across handoff and verdict artifacts.
- Keep findings and required actions evidence-based.

## Override Pattern

```bash
bash scripts/run_loop.sh \
  --repo /path/to/repo \
  --task-id TASK-0042 \
  --task "Implement ..." \
  --doer-prompt-file /path/to/doer_prompt.md \
  --judge-prompt-file /path/to/judge_prompt.md \
  --audit-prompt-file /path/to/audit_prompt.md
```

`run_loop.sh` appends an orchestration context block to custom prompt files so required paths stay explicit.
