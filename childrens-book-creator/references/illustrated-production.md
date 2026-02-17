# Illustrated Production Guide

Use this guide when the user asks for a full write-and-illustrate workflow.

## 1) Choose generation backend

- Use `imagegen` for OpenAI API generation/editing workflows.
- Use `local-comfy-image-gen` when ComfyUI/FLUX is running locally or on a trusted LAN GPU host.
- Do not mix both backends in the same batch unless the user explicitly wants that.

## 2) Preflight checks (before live generation)

### If using `imagegen`

- Confirm key and runtime in the active shell:
  - `OPENAI_API_KEY` is set in the shell that will run generation.
  - `python3 -c "import openai"` succeeds (or project venv equivalent).
- If the key exists in `~/.zshenv` but generation runs via `bash`, import from login zsh before running.
- Run a dry run first:
  - `image_gen.py generate-batch --dry-run ...`
  - Verify prompt wiring, output paths, and job count.

### If using `local-comfy-image-gen`

- Confirm `local-image-gen` repo is available and pass `--repo` (or set `REPO` / `LOCAL_IMAGE_GEN_REPO`).
- Confirm ComfyUI endpoint is reachable (`COMFY_URL=http://<gpu-host-ip>:8188` for remote GPU host).
- Run a dry run first:
  - `run_phase.sh --phase draft --dry-run ...`
  - Verify compiled workflow output and page/job paths.

## 3) Prompt lock rules

- Repeat the full character/style lock in every per-page prompt.
- Avoid cross-line shorthand in JSONL:
  - Do not use phrases like "same lock as above".
- Disambiguate ambiguous names directly:
  - Example: if character is "Teddy", state "real dog, never teddy bear/plush".
- Repeat "no text/no watermark" in each prompt.

## 4) Batch generation rules

- Use stable, flat output names:
  - `<slug>-page-00-cover.png`, `<slug>-page-01.png`, ...
- Start with one variant per page (`n=1`) for consistency.
- If one page fails moderation, reword only that prompt and rerun only that page.

## 5) QA loop (required for illustrated books)

Run at least one page-by-page visual pass and check:

- Character identity consistency (face, age, outfit, species).
- Continuity anchors (collar color, bandana pattern, key props).
- Scene-match with manuscript/page plan.
- Style consistency (medium, lighting, composition).
- Forbidden output (text overlays, logos, watermarks).

If issues appear:

- Create a targeted fix JSONL for only flagged pages.
- Strengthen lock language for failed dimensions (identity, props, style).
- Re-run and re-check flagged pages.

## 6) Final package checks

- Build print-ready PDF from manuscript + final images.
- Validate PDF page count.
- Render a few sample pages from the PDF for quick sanity checks (beginning, middle, end).
- Deliver absolute output paths for:
  - final images directory
  - final PDF
  - generation/fix JSONL files (if user may iterate again)
