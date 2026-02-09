# Critique Checklist

Run this after the first implementation pass.

## 1) Composition

- Verify the screen has one clear focal action.
- Verify proportions communicate priority (sidebar, content width, panel weight).
- Verify density varies intentionally by section instead of repeating one rhythm everywhere.

## 2) Craft

- Verify spacing values stay on the declared scale.
- Verify surface hierarchy is visible without relying on heavy borders.
- Verify controls have complete interactive states.
- Verify type hierarchy is readable from quick scanning distance.

## 3) Content Coherence

- Verify labels, headings, and data belong to one product story.
- Verify examples and placeholder values match domain language.
- Verify empty/loading/error states use meaningful product language.

## 4) Structure

- Remove one-off layout hacks when a structural fix exists.
- Prefer consistent primitives over duplicated custom styles.
- Consolidate repeated values into tokens/variables/utilities.

## 5) Final Gate

- Ask: "What part still feels default instead of deliberate?"
- Fix that part before finalizing.
