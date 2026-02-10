# Error Handling

## Unknown session_id or pty_id
- Open a new session or check `session-list`.

## Host key mismatch
- Treat as security-sensitive.
- Stop and ask for confirmation before bypassing checks.

## Command blocked by policy
- Use `--override-block` only when interactive behavior is truly required.

## Timeout
- Increase timeout if expected.
- Prefer command mode unless PTY is necessary.

## Authentication failure
- Verify credential or auth args.
- Re-save credential and retry.
