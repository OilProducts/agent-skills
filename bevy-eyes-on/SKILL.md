---
name: bevy-eyes-on
description: "Capture Bevy visuals with BRP state-gated scenarios first, and timed screenshots only as fallback. Use when a task needs reliable screenshots of specific game states."
---

# Bevy Eyes-On

Use a minimal visual-check workflow for any Bevy app.

Default to BRP state-gated capture. Use timed capture only when BRP hooks are unavailable.

## 1) BRP State-Gated Screenshot (Primary)

```bash
bash /Users/chris/.codex/skills/bevy-eyes-on/scripts/capture_after_brp_sequence.sh \
  --requests-jsonl /path/to/scenario.jsonl \
  --brp-url http://127.0.0.1:15702 \
  --settle-ms 250 \
  --app "<AppName>"
```

Use for screenshots of gameplay/submenus/precise states.

`scenario.jsonl` is one JSON object per line:
- action call: raw BRP body, or `{"body": <request>, "wait_ms": <n>}`
- state probe with gate:
`{"probe": <request>, "until": {"path": "result.menu", "equals": "settings", "timeout_ms": 5000, "interval_ms": 100}}`
- `until` supports exactly one matcher: `equals` or `in`.
- `path` uses dot lookup through objects/lists (list index by numeric segment, e.g. `result.items.0.id`).

Example:
```json
{"body":{"method":"open_pause_menu","params":{}},"wait_ms":120}
{"probe":{"method":"ui_state","params":{}},"until":{"path":"result.current_menu","equals":"pause","timeout_ms":4000,"interval_ms":100}}
{"body":{"method":"open_settings","params":{}}}
{"probe":{"method":"ui_state","params":{}},"until":{"path":"result.current_menu","equals":"settings","timeout_ms":4000,"interval_ms":100}}
```

If BRP hooks are missing, use [$bevy-brp-instrumentation](/Users/chris/.codex/skills/bevy-brp-instrumentation/SKILL.md).

## 2) Timed Screenshot (Fallback)

```bash
bash /Users/chris/.codex/skills/bevy-eyes-on/scripts/capture_after_delay.sh \
  --delay-seconds 3 \
  --app "<AppName>"
```

Use only for non-specific capture when state-driven BRP is unavailable.

## Behavior

- Reuse a running app by default.
- Prefer state-driven BRP scenarios; do not rely on fixed sleeps for state transitions.
- Targeted capture once (`--app` or `--window-id`), then one full-display fallback.
- No loops, no heavyweight run artifacts.

## Output

- Print one absolute screenshot path on success.
- Exit non-zero with a short error on failure.

Run `--help` on either script for full flags.
