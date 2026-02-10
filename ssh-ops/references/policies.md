# Policies

## Blocked interactive commands by default
- less
- more
- man
- vim
- vi
- nano
- top
- htop
- watch
- tmux
- screen

## PTY guardrails
- Default to non-PTY (`exec`).
- Use PTY only when required.
- Enforce idle and wall-clock limits.
- Cap output during reads.
- Log override usage and transcript offsets.

## Environment defaults for remote command mode
- `PAGER=cat`
- `GIT_PAGER=cat`
- `MANPAGER=cat`
