# Local Workflow Reference

## Repo assumptions

Default project path:

- `/home/chris/projects/local-image-gen`

Key files:

- Orchestrator: `orchestrator/run_page.py`
- Workflows: `workflows/draft.api.json`, `workflows/refine.api.json`, `workflows/inpaint.api.json`, `workflows/upscale_print.api.json`
- Bindings: `workflows/*.bindings.json`
- Schemas: `schemas/renderspec.v0.json`, `schemas/review.v0.json`
- Templates: `templates/renderspec.example.json`, `templates/review.example.json`

## Artifact contract

Per page output root:

- `books/<book_id>/pages/<page>/`

Expected subfolders:

- `draft/`
- `selected/`
- `refine/`
- `final/`
- `jobs/`

High-value artifacts:

- `renderspec.json`
- `review.json` (if used)
- `jobs/*_compiled_workflow.json`
- `jobs/*_<phase>_<prompt_id>.json`

## ComfyUI runtime

Default local URL:

- `http://192.168.1.224:8188`

Useful health checks:

```bash
curl -sS http://192.168.1.224:8188/system_stats
curl -sS http://192.168.1.224:8188/object_info
```

## Remote-agent mode (GPU box + laptop)

Use this when ComfyUI runs on a GPU host and Codex/agent runs on a different machine (laptop).

### On GPU host

1. Start ComfyUI on LAN interface:

```bash
REPO=/path/to/local-image-gen \
HOST=0.0.0.0 \
COMFY_URL=http://192.168.1.224:8188 \
$CODEX_HOME/skills/local-comfy-image-gen/scripts/start_comfy.sh
```

2. Confirm LAN reachability from another machine:

```bash
curl -sS http://<gpu-host-ip>:8188/system_stats
```

### On laptop agent machine

1. Ensure the same skill exists on laptop under:

- `~/.codex/skills/local-comfy-image-gen`

2. Clone/copy `local-image-gen` repo locally on laptop.

3. Run orchestrator against remote ComfyUI:

```bash
COMFY_URL=http://<gpu-host-ip>:8188 \
~/.codex/skills/local-comfy-image-gen/scripts/run_phase.sh \
  --repo /path/to/local-image-gen \
  --book-id my_book \
  --page 1 \
  --phase draft \
  --renderspec /path/to/local-image-gen/templates/renderspec.example.json
```

Notes:

- Artifacts are written on the laptop repo under `books/`.
- GPU execution happens on the remote ComfyUI host.
- Keep both machines on the same trusted LAN.

## Model layout used in this project

- `comfyui/models/diffusion_models/flux1-dev.safetensors`
- `comfyui/models/diffusion_models/FHDR_ComfyUI.safetensors`
- `comfyui/models/text_encoders/clip_l.safetensors`
- `comfyui/models/text_encoders/t5xxl_fp16.safetensors`
- `comfyui/models/vae/ae.safetensors`

SD1.5 fallback present:

- `comfyui/models/checkpoints/v1-5-pruned-emaonly.safetensors`

## Troubleshooting

1. `Operation not permitted` when posting to `/prompt`:
- Run orchestrator with escalated permissions.

2. ComfyUI starts but no GPU:
- Launch ComfyUI with escalated permissions so CUDA device is visible.

3. Workflow submission fails with node/input errors:
- Verify node ids and input keys in `workflows/<phase>.api.json` against `/object_info/<NodeType>`.
- Verify `workflows/<phase>.bindings.json` maps to existing node ids.

4. Output generated but wrong style:
- Adjust binding templates first (`clip_l`, `t5xxl`, constraints).
- Keep seed fixed while tuning prompt/bindings to compare changes.
