# Local Workflow Reference

## Layout and ownership

Pipeline assets are bundled with this skill:

- `$CODEX_HOME/skills/comfyui-image-gen/orchestrator/run_page.py`
- `$CODEX_HOME/skills/comfyui-image-gen/workflows/*.api.json`
- `$CODEX_HOME/skills/comfyui-image-gen/workflows/*.bindings.json`
- `$CODEX_HOME/skills/comfyui-image-gen/schemas/*.json`
- `$CODEX_HOME/skills/comfyui-image-gen/templates/*.json`

Comfy runtime is separate (GPU host):

- Default runtime repo: `~/projects/local-image-gen`
- Runtime entrypoint: `~/projects/local-image-gen/comfyui/main.py`

## Script path resolution

`run_phase.sh` and `check_setup.sh` resolve pipeline assets in this order:

- explicit `--repo` / `PIPELINE_REPO`
- current working directory (if it contains `orchestrator/run_page.py`)
- skill root (`$CODEX_HOME/skills/comfyui-image-gen`)

`start_comfy.sh` resolves runtime repo in this order:

- `COMFY_RUNTIME_REPO`
- current working directory (if it contains `comfyui/main.py`)
- `~/projects/local-image-gen`

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

- `http://127.0.0.1:8188`

Useful health checks:

```bash
curl -sS http://127.0.0.1:8188/system_stats
curl -sS http://127.0.0.1:8188/object_info
```

## Remote-agent mode (GPU host + laptop)

Use this when ComfyUI runs on a GPU host and Codex runs on another machine.

### On GPU host

1. Start ComfyUI on LAN interface:

```bash
COMFY_RUNTIME_REPO=/path/to/local-image-gen \
HOST=0.0.0.0 \
COMFY_URL=http://127.0.0.1:8188 \
$CODEX_HOME/skills/comfyui-image-gen/scripts/start_comfy.sh
```

2. Confirm LAN reachability:

```bash
curl -sS http://<gpu-host-ip>:8188/system_stats
```

### On laptop agent machine

1. Ensure this skill exists:

- `~/.codex/skills/comfyui-image-gen`

2. Run phase against remote ComfyUI:

```bash
COMFY_URL=http://<gpu-host-ip>:8188 \
~/.codex/skills/comfyui-image-gen/scripts/run_phase.sh \
  --book-id my_book \
  --page 1 \
  --phase draft \
  --renderspec ~/.codex/skills/comfyui-image-gen/templates/renderspec.example.json \
  --books-dir /path/to/project/books
```

Notes:

- Artifacts are written to `--books-dir` (or default `./books`).
- GPU execution happens on the remote ComfyUI host.
- Keep both machines on the same trusted LAN.
- For `refine`/`inpaint`/`upscale_print` with `--source-image`, pass `--comfy-input-dir` when the source must be copied to Comfy's `input/`.

## Runtime model layout (on GPU host)

- `comfyui/models/diffusion_models/flux1-dev.safetensors`
- `comfyui/models/diffusion_models/FHDR_ComfyUI.safetensors`
- `comfyui/models/text_encoders/clip_l.safetensors`
- `comfyui/models/text_encoders/t5xxl_fp16.safetensors`
- `comfyui/models/vae/ae.safetensors`
- `comfyui/models/checkpoints/v1-5-pruned-emaonly.safetensors` (fallback)

## Troubleshooting

1. `Operation not permitted` posting to `/prompt`:
- Run orchestration command with escalated permissions.

2. ComfyUI starts but no GPU:
- Start ComfyUI with escalated permissions so CUDA devices are visible.

3. Workflow submission errors:
- Verify node ids and input keys in `workflows/<phase>.api.json` against `/object_info/<NodeType>`.
- Verify `workflows/<phase>.bindings.json` node/input mappings.

4. Output style drift:
- Adjust bindings/templates first.
- Keep seed fixed while tuning prompt/bindings.
