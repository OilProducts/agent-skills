# ComfyUI Local API Notes

Primary references:
- https://docs.comfy.org/development/comfyui-server/comms_overview
- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://docs.comfy.org/development/comfyui-server/comms_messages
- https://github.com/comfyanonymous/ComfyUI/tree/master/script_examples

## Core routes used by this skill

- `GET /system_stats`
: service health, runtime info, devices.

- `GET /object_info`
: node definitions and inputs.

- `POST /prompt`
: queue workflow prompt payload. Returns `prompt_id`.

- `GET /history/{prompt_id}`
: retrieve run status and outputs for a queued prompt.

- `GET /view?filename=...&subfolder=...&type=...`
: fetch binary output files (for example generated images).

## Typical run lifecycle

1. Confirm health (`/system_stats`).
2. Queue workflow (`/prompt`).
3. Poll run history (`/history/{prompt_id}`) until completed.
4. Enumerate output images in history payload.
5. Download outputs with `/view`.

## Notes

- `client_id` is useful for associating prompts with a client session.
- Keep workflow JSON stable and use narrow input overrides per run.
- Treat API errors as actionable diagnostics (bad node ids, missing inputs, invalid payload).
