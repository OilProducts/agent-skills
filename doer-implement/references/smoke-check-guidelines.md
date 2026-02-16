# Smoke Check Guidelines

Use smoke checks to quickly catch obvious breakage in touched areas.

## Selection Rules

- Prefer targeted tests over full-suite runs.
- Include at least one check that executes changed behavior.
- Include static checks when they are cheap and relevant.
- Skip heavyweight checks only when clearly out of scope; mark as `skip` with reason in `notes`.

## Reporting Rules

- Record every attempted check in `smoke_checks`.
- Keep command strings exactly runnable.
- Use only statuses: `pass`, `fail`, `skip`, `unknown`.
- Never convert failures into prose-only caveats; keep them in structured output.
