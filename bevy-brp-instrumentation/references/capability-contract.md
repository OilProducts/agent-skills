# Capability Contract

Implement a small BRP control surface for deterministic scenario driving.
Method names are project-defined, but the capability categories below should exist.

- Capability probe (recommended): returns supported deterministic features.
- Pose/state mutation action: sets camera/player pose or equivalent gameplay state.
- Frame progression/wait action: advances or waits by frame count deterministically.
- UI/game state probe: returns machine-readable state for scenario gating.
- Screenshot action (optional if external capture is used): captures deterministic frame output.
- Cursor/input mode action (recommended): toggles capture/free behavior when needed.

## Semantics

- Capability probe: return booleans/flags describing implemented deterministic features.
- Pose/state mutation: apply atomically for the next frame when possible.
- Frame progression/wait: resolve only after requested frame count has elapsed.
- UI/game state probe: return structured fields stable enough for path-based gating.
- Screenshot action: write image deterministically and return metadata when available.
- Cursor/input mode: apply capture/free behavior without changing unrelated input state.

## Failure Rules

- Return explicit method-level failure for unimplemented calls.
- Do not silently downgrade deterministic requests to best-effort behavior.
- Keep error payloads machine-readable when possible.
