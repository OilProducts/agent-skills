---
name: web-ui-design
description: Design and refine web UI interfaces with deliberate visual direction, reusable design-system decisions, and consistency checks for product UIs (dashboards, apps, tools, and admin panels). Use when a user asks to create, redesign, critique, or standardize web pages/components; establish visual tokens and patterns; extract a system from existing code; or audit design drift in implemented UI files.
---

# Web UI Design

Create intentional interfaces instead of default-looking layouts. Persist design decisions in a project system file so every page and component stays coherent across sessions.

## Workflow

### 1) Confirm scope and intent

Use this skill for application interfaces, not marketing pages.

Establish these three anchors before designing:
- Human: Who uses this screen right now?
- Task: What concrete action must they finish?
- Feel: What emotional/brand tone should the UI convey?

If the user did not specify enough context, ask concise questions or make a clearly labeled best-fit assumption.

### 2) Load or establish the design system

Use `.interface-design/system.md` as project memory.

- If the file exists: apply it as the default source of truth.
- If the file does not exist: propose one direction and explain why it fits the product and user task.

To bootstrap from existing code, run:

```bash
python3 <path-to-skill>/scripts/extract_interface_system.py --path <project-root>
```

Use `references/system-template.md` when creating or updating `.interface-design/system.md`.

### 3) Declare choices before implementation

Before each major component/page, state a short design contract:
- Intent
- Palette/foundation
- Depth strategy
- Surface hierarchy
- Typography approach
- Spacing grid

Then implement the component and keep every value consistent with that contract.

### 4) Enforce non-negotiables

- Use one spacing base (4px or 8px), then keep all spacing on that scale.
- Keep depth strategy explicit and consistent (`borders-only`, `subtle-shadows`, or `layered-shadows`).
- Keep typography hierarchy intentional through size, weight, and contrast.
- Include interactive states for controls (hover/focus/active/disabled).
- Keep content coherent with the product domain (no placeholder mismatch).

### 5) Critique and rebuild

After the first pass, run a critique pass using `references/critique-checklist.md`. Rebuild weak sections instead of patching with one-off style fixes.

### 6) Audit drift when editing existing code

Run:

```bash
python3 <path-to-skill>/scripts/audit_interface_system.py --path <project-root> --system <project-root>/.interface-design/system.md
```

Use violations to fix off-grid spacing and depth inconsistencies.

### 7) Persist new decisions

When the implementation introduces new stable patterns, update `.interface-design/system.md` so future sessions inherit the same design language.

## Direction Selection

Use `references/direction-profiles.md` only when choosing or revising direction. Pick one dominant direction, then tune details inside that direction instead of mixing incompatible styles.

## Resources

### scripts/
- `scripts/extract_interface_system.py`: extract repeated tokens and suggest a starting system.
- `scripts/audit_interface_system.py`: check spacing/depth violations against the active system file.

### references/
- `references/system-template.md`: canonical system structure for project memory.
- `references/direction-profiles.md`: concise direction options with tradeoffs.
- `references/critique-checklist.md`: craft review checklist for second-pass improvements.
