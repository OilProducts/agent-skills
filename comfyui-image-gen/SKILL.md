---
name: comfyui-image-gen
description: "Run ComfyUI local API image-generation workflows (local or remote) with deterministic workflow JSON + bindings, queue monitoring, and output retrieval. Use when a task should be executed via ComfyUI instead of hosted image APIs."
---

# ComfyUI Image Gen

## Overview

Execute image generation through ComfyUI's Local API using workflow JSON files and explicit input bindings.

Prefer deterministic runs:
- keep workflow JSON under version control
- set input overrides explicitly per run
- preserve run metadata and output manifests

## When to use

- User explicitly wants ComfyUI generation
- You have a compatible workflow JSON and reachable ComfyUI endpoint
- You need local/remote GPU execution outside hosted image APIs

## Workflow

1. Check ComfyUI health.
- Run `scripts/check_comfy.sh`.
- Confirm `system_stats` and (optionally) `object_info` respond.

2. Prepare workflow JSON.
- Start from a known-good `.api.json` workflow export.
- Avoid ad-hoc node rewiring in prompts; change inputs through explicit bindings.

3. Shape generation intent with a structured prompt spec.
- Use compact fields: use case, primary request, subject, style, composition, lighting, constraints, avoid.
- Keep constraints explicit (`no text`, anatomy continuity, composition, safety).

4. Run workflow.
- Use `scripts/run_workflow.sh`.
- Pass `--workflow` and optional `--set node.input=value` overrides.
- Use `--out-dir` to download generated images.

5. Inspect outputs and iterate deliberately.
- Change one thing at a time (prompt text, seed, one binding).
- Keep successful workflow + binding combinations as reusable presets.

## Commands

Health check:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/check_comfy.sh \
  --comfy-url http://127.0.0.1:8188
```

Queue a workflow and download outputs:

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/run_workflow.sh \
  --comfy-url http://127.0.0.1:8188 \
  --workflow workflows/draft.api.json \
  --set "6.inputs.text=anthropomorphic beetle eating a balanced breakfast, storybook style" \
  --set "3.inputs.seed=123456" \
  --out-dir output/comfy
```

Dry-run (validate and print request metadata without queueing):

```bash
$CODEX_HOME/skills/comfyui-image-gen/scripts/run_workflow.sh \
  --workflow workflows/draft.api.json \
  --dry-run
```

## Operating rules

- Do not assume a fixed repo path; always accept explicit paths/URLs.
- Prefer API workflow JSON + explicit bindings over manual UI-only steps.
- Treat prompt, workflow, and seed as a reproducibility unit.
- For remote GPUs, set `--comfy-url http://<host>:<port>` explicitly.
- If a run fails, report the exact API endpoint/response and failing node id when available.

## References

- `references/comfy-api.md` for endpoint contracts and run lifecycle.
- `references/prompting.md` for compact prompt spec patterns.
