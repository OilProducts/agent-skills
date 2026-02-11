# Validation Checklist

## Preflight

- App launches cleanly without instrumentation regressions.
- BRP endpoint is reachable on localhost.

## Deterministic Contract Check

1. Run one BRP capability/probe request and record the response.
2. Confirm deterministic-related flags/fields reflect actual implementation.
3. Confirm required fields for gating exist (for example menu/gameplay state).

## Deterministic Scenario Check

1. Execute one scenario JSONL with actions and at least one `probe`+`until` gate using `bevy-eyes-on`.
2. Confirm state transitions occur in intended order.
3. Confirm the `until` gate resolves within timeout.
4. Confirm screenshot file is written after gate satisfaction.

## Negative Path Check

- Execute a scenario gate for an intentionally unavailable state/capability.
- Confirm timeout or explicit method error is returned, not silent fallback.

## Cleanup

- Stop/close the app process if it was launched for the run.
