---
name: local-comfy-image-gen
description: "Run local ComfyUI image generation pipelines with RenderSpec-driven orchestration for books and multi-page projects. Use when working in a local ComfyUI repo (especially /home/chris/projects/local-image-gen) to start/check ComfyUI, run draft/refine/inpaint/upscale phases, manage renderspec.json and review.json, and produce reproducible page artifacts under books/{book_id}/pages/{page}/."
---

# Local Comfy Image Gen

## Overview

Execute local ComfyUI rendering workflows through the project orchestrator, not ad-hoc prompt rerolls. Keep outputs reproducible by storing RenderSpec, compiled workflow JSON, seeds, job manifest, and generated files per page.

## Workflow

1. Verify setup first.
- Run `scripts/check_setup.sh`.
- If required files are missing, fix setup before rendering.

2. Ensure ComfyUI server is available.
- If already running on `http://192.168.1.224:8188`, reuse it.
- Else run `scripts/start_comfy.sh`.

3. Build or update RenderSpec using a structured prompt pattern.
- Use the prompt-spec style from `imagegen` (scene, subject, style, composition, constraints, avoids).
- Keep constraints explicit (`no text`, character count, safety, composition requirements).

4. Choose phase and inputs.
- `draft`: requires `--renderspec`.
- `refine` / `inpaint` / `upscale_print`: usually require `--source-image` and often `--review`.

5. Run the orchestrator phase.
- Use `scripts/run_phase.sh` for all phases.
- Prefer one phase at a time so artifacts and review stay clean.

6. Inspect output and iterate deliberately.
- Inspect generated images under `books/<book_id>/pages/<page>/draft|refine|final/`.
- Record selection rationale in `review.json` before refine/final steps.

7. Keep reproducibility artifacts.
- Keep `renderspec.json`, `review.json`, and `jobs/*.json` manifests.
- Do not delete job manifests during iteration.

## Prompt pattern

Use this compact prompt shape when constructing `render.scene` or style blocks:

```text
Use case: illustration-story
Asset type: storybook page art
Primary request: <scene goal>
Subject: <characters + key action>
Style/medium: <visual style>
Composition/framing: <camera + focal clarity>
Lighting/mood: <time + emotion>
Constraints: <must-keep invariants>
Avoid: <must-not-generate items>
```

Keep this concise and deterministic. Do not invent new creative requirements beyond user intent.

## Commands

Run setup check:

```bash
$CODEX_HOME/skills/local-comfy-image-gen/scripts/check_setup.sh
```

Start ComfyUI (if needed):

```bash
$CODEX_HOME/skills/local-comfy-image-gen/scripts/start_comfy.sh
```

Run draft:

```bash
$CODEX_HOME/skills/local-comfy-image-gen/scripts/run_phase.sh \
  --book-id gingerbear_01 \
  --page 7 \
  --phase draft \
  --renderspec templates/renderspec.example.json
```

Run refine:

```bash
$CODEX_HOME/skills/local-comfy-image-gen/scripts/run_phase.sh \
  --book-id gingerbear_01 \
  --page 7 \
  --phase refine \
  --renderspec books/gingerbear_01/pages/0007/renderspec.json \
  --review books/gingerbear_01/pages/0007/review.json \
  --source-image books/gingerbear_01/pages/0007/draft/001_some_image.png
```

Dry-run compile only:

```bash
$CODEX_HOME/skills/local-comfy-image-gen/scripts/run_phase.sh \
  --book-id gingerbear_01 \
  --page 7 \
  --phase draft \
  --renderspec templates/renderspec.example.json \
  --dry-run
```

## Operating rules

- Use workflow JSON + bindings from `workflows/`; do not hardcode node edits per run.
- Treat `review.json` as agent judgment log, not a score sheet.
- Prefer targeted edits to RenderSpec or bindings instead of random seed thrashing.
- Use one model track per book for visual consistency.
- Keep text out generated art; add typography at layout stage.

## References

Load `references/local-workflow.md` when you need exact path contracts, expected artifacts, or troubleshooting guidance.
