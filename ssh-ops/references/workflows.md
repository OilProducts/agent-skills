# Workflows

State root defaults to `/tmp/ssh-ops-$USER/<cwd-hash>`.
You can override with `--state-dir ...` or `SSH_OPS_STATE_DIR`.
Use the same state dir for a full session lifecycle.

## Command workflow (preferred)
1. `session-open`
2. `exec`
3. Repeat `exec` as needed
4. `session-close`

## PTY workflow (guarded)
1. `session-open`
2. `pty-open`
3. Loop: `pty-write`, `pty-read`
4. `pty-resize` when needed
5. `session-close`

## Copy workflow
1. `session-open`
2. `scp-copy`
3. `session-close`

## Credential workflow
1. `credential-save`
2. `session-open --credential-id ...`
3. Rotate or remove with `credential-delete`
