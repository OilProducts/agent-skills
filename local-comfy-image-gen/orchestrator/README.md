# Orchestrator Scaffold

`orchestrator/run_page.py` runs one workflow phase against ComfyUI and stores reproducible artifacts under `books/<book_id>/pages/<page>/`.

## What It Does

- Reads `renderspec.json` (and optional `review.json`).
- Loads a ComfyUI API workflow JSON for the requested phase.
- Applies optional bindings from `<phase>.bindings.json` into specific node inputs.
- Submits the workflow to ComfyUI (`/prompt`), waits for completion (`/history/{prompt_id}`), and downloads outputs (`/view`).
- Writes compiled workflow + run manifest under `books/.../jobs/`.

## Expected Files

- `workflows/draft.api.json`, `workflows/refine.api.json`, `workflows/inpaint.api.json`, `workflows/upscale_print.api.json`
- Optional bindings: `workflows/<phase>.bindings.json`
- Schemas/templates are in `schemas/` and `templates/`.

## Example Usage

```bash
python orchestrator/run_page.py \
  --book-id gingerbear_01 \
  --page 7 \
  --phase draft \
  --renderspec templates/renderspec.example.json \
  --workflow-dir workflows \
  --books-dir books \
  --comfy-url http://127.0.0.1:8188
```

Refine with a selected source image:

```bash
python orchestrator/run_page.py \
  --book-id gingerbear_01 \
  --page 7 \
  --phase refine \
  --renderspec books/gingerbear_01/pages/0007/renderspec.json \
  --review books/gingerbear_01/pages/0007/review.json \
  --source-image books/gingerbear_01/pages/0007/draft/001_ComfyUI_00001_.png \
  --comfy-input-dir /srv/artfarm/comfyui/input \
  --workflow-dir workflows
```

Dry-run compilation only:

```bash
python orchestrator/run_page.py \
  --book-id gingerbear_01 \
  --page 7 \
  --phase draft \
  --renderspec templates/renderspec.example.json \
  --dry-run
```

## Binding File Format

The optional `workflows/<phase>.bindings.json` uses this structure:

```json
{
  "actions": [
    {"op": "set", "node": "6", "input": "text", "from": "render.scene", "optional": true},
    {"op": "set", "node": "3", "input": "seed", "from": "render.seed", "default": 42, "optional": true},
    {"op": "format", "node": "7", "input": "text", "template": "{render.scene}, no text", "optional": true}
  ]
}
```

Supported operations:

- `set`: set node input from `value` or `from` dotted path (`default` optional).
- `format`: interpolate `{dotted.path}` placeholders from runtime context.
- `optional: true`: skip this action instead of failing if source data or node/input is missing.

Context roots exposed to bindings:

- `render` (`renderspec.json`)
- `review` (optional)
- `phase_inputs` (`source_image_*` values when provided)
- `book_id`, `page`, `phase`, `paths`, `runtime`
