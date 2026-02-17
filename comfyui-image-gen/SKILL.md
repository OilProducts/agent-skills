---
name: comfyui-image-gen
description: "Unified ComfyUI skill for direct API workflow runs and RenderSpec-based multi-page pipeline phases (draft/refine/inpaint/upscale_print) with reproducibility artifacts. Use for both ad-hoc workflow execution and full storybook/page production loops."
---

# ComfyUI Image Gen

## Overview

Use this single skill for both:
- direct ComfyUI API workflow runs (`run_workflow.sh`)
- orchestrated page pipelines (`run_phase.sh` + RenderSpec/review artifacts)

Keep runs reproducible by preserving workflow JSON, explicit bindings, seeds, run metadata, and per-page artifacts.

## Modes

### Mode A: Direct workflow run

Use when you already have an `.api.json` workflow and want to queue/download outputs quickly.

Flow:
1. Check endpoint health (`scripts/check_comfy.sh`).
2. Select strongest available model stack (prefer `FLUX` > `SDXL` > SD1.x/2.x).
3. Run `scripts/run_workflow.sh` with explicit `--set` overrides.
4. Inspect outputs and iterate one variable at a time.

### Mode B: Orchestrated page pipeline

Use when producing books/multi-page assets with stable artifacts and deliberate QA.

Flow:
1. Verify setup (`scripts/check_setup.sh`).
2. Ensure Comfy runtime is available (`scripts/start_comfy.sh`) when hosting locally.
3. Author/update `renderspec.json`.
4. Run one phase at a time via `scripts/run_phase.sh`.
5. Inspect per-page outputs and record decisions in `review.json` before refine/final steps.
6. Keep `renderspec.json`, `review.json`, and `jobs/*.json` manifests.

## Commands

Endpoint health:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/check_comfy.sh \
  --comfy-url http://192.168.1.224:8188 \
  --check-object-info
```

Direct workflow run:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/run_workflow.sh \
  --comfy-url http://192.168.1.224:8188 \
  --workflow workflows/draft.api.json \
  --set "3.inputs.text=storybook scene, no text" \
  --set "7.inputs.noise_seed=123456" \
  --out-dir output/comfy
```

Pipeline setup check:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/check_setup.sh
```

Pipeline draft phase:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/run_phase.sh \
  --book-id gingerbear_01 \
  --page 7 \
  --phase draft \
  --renderspec $CODEX_HOME/skills/comfyui-image-gen/templates/renderspec.example.json \
  --books-dir books
```

Pipeline refine phase:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/run_phase.sh \
  --book-id gingerbear_01 \
  --page 7 \
  --phase refine \
  --renderspec books/gingerbear_01/pages/0007/renderspec.json \
  --review books/gingerbear_01/pages/0007/review.json \
  --source-image books/gingerbear_01/pages/0007/draft/001_some_image.png \
  --books-dir books
```

## Model selection rule

Before queueing, state the exact model components used (checkpoint/UNet, text encoders, VAE).
Always prefer the strongest compatible family available:
- `FLUX`
- `SDXL`
- SD1.x/2.x (fallback only)

## Operating rules

- Do not assume a fixed workspace path; use explicit paths/URLs when available.
- Prefer workflow JSON + explicit bindings over manual UI node edits.
- Treat prompt + workflow + seed as a reproducibility unit.
- Keep generated art free of text unless explicitly requested.
- For multi-page books, QA in small batches and regenerate only flagged pages.

## References

- `references/comfy-api.md` for endpoint contracts and run lifecycle.
- `references/prompting.md` for compact prompt-spec patterns.
- `references/local-workflow.md` for RenderSpec/pipeline path contracts.
- `plans.md` for phase-by-phase orchestration guidance.
