# Workflow Files

Place ComfyUI API workflow JSON exports here.

Expected files:

- `draft.api.json`
- `refine.api.json`
- `inpaint.api.json`
- `upscale_print.api.json`

Optional binding files:

- `draft.bindings.json`
- `refine.bindings.json`
- `inpaint.bindings.json`
- `upscale_print.bindings.json`

The runner (`orchestrator/run_page.py`) reads `*.api.json` first, then falls back to `*.json`.

## Export Tip

From ComfyUI, save/export your workflow in API format so node ids and inputs match what `/prompt` expects.

