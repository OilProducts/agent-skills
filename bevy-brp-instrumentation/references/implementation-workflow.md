# Implementation Workflow

## 1) Enable Remote Access

- Add Bevy remote plugin support in the target app.
- Ensure BRP endpoint binding is reachable by local consumers (typically localhost).

## 2) Add Deterministic Surface

- Create a small instrumentation module/plugin dedicated to BRP method handlers.
- Route deterministic operations into existing ECS resources/systems.
- Keep method handlers thin; put logic in testable systems/functions.

## 3) Stabilize Semantics

- Define pose ownership clearly (camera entity vs player entity).
- Ensure frame waiting is tied to rendered frames, not wall-clock sleep.
- Ensure screenshot path writes complete files before method returns.
- Ensure state-probe outputs are stable and machine-readable for `until` gating.

## 4) Keep Feature Flags Clean

- Gate instrumentation behind a feature flag or explicit app mode when needed.
- Keep production/default runtime behavior unchanged unless requested.

## 5) Add Lightweight Tests

- Add at least one integration check per deterministic method family.
- Validate capability output matches actual implementation availability.
