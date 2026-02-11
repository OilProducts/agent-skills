---
name: bevy-brp-instrumentation
description: Add and validate BRP hooks in Bevy projects so BRP consumers (especially bevy-eyes-on) can drive deterministic state transitions and capture reliable screenshots. Use when a task requires reproducible camera/player pose, frame-based stabilization, state probes, deterministic screenshots, or explicit capability reporting for Bevy apps.
---

# Bevy BRP Instrumentation

## Overview

Instrument an existing Bevy app so deterministic BRP control and state-probe paths are available and testable.

Keep edits minimal, additive, and feature-gated so normal app behavior stays unchanged.

## Workflow

1. Enable Bevy remote support in the app.
2. Add deterministic BRP methods for the required contract.
3. Wire methods to existing game state systems with stable semantics.
4. Validate capability discovery and deterministic flows through BRP scenario runs (for example with `bevy-eyes-on`).

For the exact method list and behavior, read `references/capability-contract.md`.

For a practical implementation sequence, read `references/implementation-workflow.md`.

## Guardrails

- Preserve existing controls and gameplay loops unless the task explicitly allows behavior changes.
- Return deterministic unavailability explicitly when a required capability is not implemented.
- Keep BRP exposure local-first for development (localhost endpoints).
- Add small integration checks for capability discovery and deterministic calls.

## Validation

After instrumentation, verify deterministic paths with BRP scenario execution:

- At least one action call mutates state as expected.
- At least one probe call returns machine-readable state for gating (`until`).
- Frame-based wait/progression behaves deterministically when implemented.
- Screenshot capture succeeds after a state gate condition is met.

Use `references/validation-checklist.md` for a step-by-step validation pass.
