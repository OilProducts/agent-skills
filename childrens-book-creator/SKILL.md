---
name: childrens-book-creator
description: End-to-end workflow for creating original children's books (picture books, early readers, chapter books) including brief, outline, page-by-page plan, manuscript drafting, revision checklists, and illustration/art direction prompts. Use when a user asks for help writing, outlining, revising, or planning a children's book; creating page breakdowns/spreads; generating illustration prompts; or scaffolding a book project folder with structured files.
---

# Childrens Book Creator

## Overview

Create original, age-appropriate children's book manuscripts with a clear structure (brief → outline → page plan → draft → revision) and optional illustration guidance (art direction + per-spread prompts).

## Quick Start (5 questions)

Ask these first, then proceed through the workflow:

- Target reader age range (e.g., 2–4, 4–6, 6–8, 8–12)
- Format (picture book / early reader / chapter book / middle grade)
- Target length (words + page count if relevant)
- Tone + theme (funny, cozy, adventurous; what feeling should remain?)
- Illustrations? (yes/no; style references and constraints)

If the user has no preferences, default to: picture book, ages 3–7, 32 pages, 300–600 words, humorous or warm tone.

## Non-Negotiables

- Write an original story; do not imitate or reuse copyrighted characters, worlds, or distinctive proprietary styles.
- Keep language age-appropriate; avoid graphic harm and adult themes.
- Prefer “show” over moralizing; keep lessons implicit unless requested.

## Illustrated Book Defaults (when user wants writing + art)

- Use the full pipeline in order: brief -> bible -> outline -> page plan -> manuscript -> art prompts -> image generation -> QA -> final package.
- Keep one source of truth for continuity (character lock + palette + props) and reuse it everywhere.
- Use deterministic file naming for page art: `<slug>-page-00-cover.png`, `<slug>-page-01.png`, etc.
- Keep image prompts per page explicit; do not rely on shorthand like "same character lock" between JSONL lines.

## Consistency-First Illustration Workflow (recommended)

- Approve 1-2 canonical character reference images before bulk rendering.
- Start with generation for composition, then switch to targeted edits for failed pages.
- Prefer editing (`images.edit`) over full rerenders when identity/style drift appears.
- Use `input_fidelity=high` for strict character-preservation edits.
- Use masks for localized fixes (face/hands/prop) instead of replacing the whole page.
- QA in small batches (2-3 pages), not only at the end of all pages.
- Regenerate only flagged pages; avoid touching already-approved pages.

Escalation rule:
- If 2+ pages in a batch show cast/species/style drift, stop full-page generation and move to edit-first repair with reference images.

## Workflow

### 0) Scaffold a book project (optional, recommended)

Run the scaffold script to create a structured workspace (brief, outline, manuscript, page plan, art prompts):

- `python3 scripts/new_book_project.py --title "My Book Title" --format picture-book --age "3-7" --page-count 32 --out books`

This creates `books/<slug>/` with starter files you can fill in during the steps below.

### 1) Write the brief (1 page)

Produce `book_brief.md` with:

- One-sentence premise (character + want + obstacle)
- Audience + format + target word count
- Promise of the book (what the reader gets: laughs, comfort, wonder)
- Character list (1–3 leads) and what each wants
- Setting + constraints (time/place, taboo topics, vocabulary constraints)

If unsure about format/length norms, consult `references/formats.md`.

### 2) Build the book bible (consistency)

Produce `characters.md` and (if illustrated) `art_direction.md`:

- Voice: narration POV, tense, read-aloud rhythm notes
- Characters: name, look, quirks, fears, catchphrases (if any), growth arc
- Continuity rules: colors, props, recurring visual gags, scale notes

If illustrated, consult `references/illustration-brief.md`.

### 3) Outline the story (beats)

Create `outline.md` in a beat format appropriate to the chosen format:

- Picture book: setup → problem → attempts → escalation → twist → resolution → cozy landing
- Early reader/chapter: chapter beats and mini-cliffhangers

Make stakes child-sized but emotionally real.

### 4) Create a page plan / spread plan

For picture books, create `page_plan.md` as 12–14 spreads (each spread = 2 pages) with:

- Spread goal (what changes)
- Text (1–4 short lines) + optional refrain
- Illustration note (what must be visible to carry meaning/joke)

If you need a 32-page map, consult `references/page-plans.md`.

### 5) Draft the manuscript

Write `manuscript.md` aligned to the page plan.

Rules of thumb:

- Prefer short sentences and concrete verbs.
- Read aloud; fix tongue-twisters and awkward cadence.
- Use repetition intentionally (refrains, patterns, rule-of-3).

### 6) Revise (2–3 passes)

Create `revision_notes.md` and do:

1. Structure pass (clarity, stakes, payoff)
2. Language pass (simplicity, rhythm, word economy)
3. Sensitivity pass (representation, stereotypes, unintended messaging)

Use `references/revision-checklist.md` for a pass-by-pass checklist.

### 7) Illustrations (optional)

Create `art_prompts.md`:

- Character sheet prompts (consistent outfit, colors, proportions)
- Per-spread prompts that reference the character sheet + style guide
- Negative prompts (what to avoid) and continuity reminders

If image generation is desired and available, use `comfyui-image-gen` for local/remote ComfyUI workflows or `imagegen` for hosted OpenAI image generation after prompts are ready.
For production runs and QA loops, follow `references/illustrated-production.md`.

Practical prompt rules:
- Keep invariants short and explicit (who must appear, fixed outfit/props, what must never appear).
- Keep style directives concise and stable across all pages.
- Avoid overloading prompts with conflicting requirements.
- For edit passes, include "change only X, keep Y unchanged" constraints.

### 8) Final package (optional, recommended for full-book requests)

- Regenerate only flagged pages after QA; avoid rerunning clean pages unless the style lock changed.
- Build a print-ready PDF from manuscript + page images.
- Verify page count and spot-check multiple pages before delivery.

QA gate before final package:
- Character identity continuity (face, age band, outfit, props).
- World continuity (setting logic and recurring landmarks).
- Visual sanity checks (hands, geometry, perspective, stray text/watermarks).
- Page-to-page style consistency (line, texture, color treatment).

## Resources (optional)

### scripts/
Utilities for scaffolding a new book project.

### references/
Quick reference docs for formats, page planning, illustration briefs, and revision checklists.
For full illustrated production runs, load `references/illustrated-production.md`.
