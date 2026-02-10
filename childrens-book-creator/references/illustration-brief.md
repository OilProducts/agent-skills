# Illustration brief + prompt patterns

Use this when the user wants illustrations, consistent character design, or you’re generating per-spread prompts.

## Art direction checklist (`art_direction.md`)
- **Format + trim:** (if known) and whether art bleeds to edges
- **Style keywords:** (e.g., “soft gouache, cozy, warm palette, gentle texture”)
- **Palette:** 5–8 colors; note “always” colors for key characters/props
- **Line + texture:** thick/thin lines, grain, brush texture, flat vs shaded
- **Camera language:** mostly wide, occasional close-ups, consistent horizon/scale
- **Mood:** cheerful/cozy/spooky-light; how to show it in lighting
- **Continuity rules:** outfits, props, left/right orientation, recurring motifs

## Character sheet prompt pattern
Create a single, reusable prompt that pins the character design:

- “Character sheet, turnaround, front/side/back, neutral pose + 3 expressions, consistent outfit, clean background…”

Store this in `art_prompts.md` so each spread can reference it.

## Per-spread prompt template
For each spread, include:

- **Scene goal:** what emotion/beat this image must communicate
- **Characters + continuity:** outfit/props/pose; reference the character sheet
- **Setting + key objects:** what must be visible for the text/joke to work
- **Composition:** camera distance + framing; where the page-turn focus sits
- **Style lock:** repeat the style line verbatim across prompts
- **Avoid:** anything that would confuse the story or misrepresent characters

Example structure (fill in specifics):

1. Style lock: “…”
2. Characters: “(reference character sheet) …”
3. Scene: “In …, doing …, showing …”
4. Composition: “wide shot, low angle, lots of negative space on right page…”
5. Notes: “prop X must be visible; keep colors consistent; no extra characters”

