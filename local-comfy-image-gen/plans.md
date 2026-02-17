# Local, Agent-Driven Image Generation for Children’s Books (RTX 5090 / 32GB VRAM)

This doc describes a practical self-hosted setup and workflow optimized for:
- **LLM-agent-driven** generation (minimal human babysitting)
- **Children’s book production** (consistent characters + style, reproducible outputs)
- **Low iteration cost** (burst → review → refine, instead of prompt ping-pong)
- Willingness to **trade time + system RAM** for quality, where it actually helps

---

## Guiding principles

1. **Workflow graphs > prompt strings**
   - The agent should submit **structured render jobs** (workflow + params), not “chat” with an image model.

2. **Draft cheap, finalize expensive**
   - Generate many **fast drafts**, have the agent visually review them, refine only the best.

3. **Image-conditioned fixes**
   - Prefer **img2img (low denoise)** and **inpainting** over “rewrite the prompt and reroll.”

4. **Keep typography out of the generator**
   - Render clean illustrations; do text and layout deterministically in PDF/SVG.

5. **Everything is reproducible**
   - Store: model identifiers, workflow JSON, RenderSpec JSON, seed, and outputs.

---

## High-level architecture

**One GPU box** running:
- **ComfyUI** (headless) as the pipeline runtime and queue
- Model storage on fast local disk
- Agent-side orchestration (direct ComfyUI API calls):
  - submits workflows to ComfyUI
  - tracks jobs
  - stores outputs + metadata
  - records agent review decisions and selected candidates for refinement
- Optional thin **“render broker”** wrapper later, if orchestration logic needs centralization
- A **layout step** to produce print-ready pages (PDF)

### Suggested directory layout

```

/srv/artfarm/
  comfyui/                  # ComfyUI install or container data
  models/                   # shared model store
    checkpoints/
    loras/
    vae/
    controlnet/
    clip_vision/
    upscalers/
  workflows/
    draft.json
    refine.json
    inpaint.json
    upscale_print.json
  orchestrator/
    run_page.py              # direct ComfyUI submission/poll/fetch + artifact logging
  broker/                    # optional later: thin wrapper around ComfyUI + storage
    render_broker.py
  books/
    <book_id>/
      bible/
        style_refs/
        character_refs/
        palettes/
      prompt_templates/
      pages/
        0001/
          renderspec.json
          draft/
          review.json
          selected/
          refine/
          final/
        0002/ ...
      layout/
        book.yaml
        pages.pdf
        cover.pdf
      exports/
        print/
        web/

```

---

## Model strategy (swap-friendly)

Pick **two tiers**:

### Tier A: Draft model (fast exploration)
Goal: generate 8–16 candidates quickly for composition/story beats.

Common choices:
- A “turbo/schnell” type model that’s strong at low steps.

### Tier B: Final model (quality)
Goal: refine selected drafts with higher fidelity, better coherence, and fewer artifacts.

Common choices:
- A higher-quality baseline model used only on the finalists.

> Notes:
> - You can plug in whatever models you like. The workflow assumes “draft model” and “final model” are replaceable.
> - Licensing differs by model family; track this if any outputs are commercial.

---

## ComfyUI runtime setup

### Run mode
- Prefer **high/normal VRAM mode** so models stay resident and the agent loop is fast.
- Avoid full CPU-offload unless you’re truly OOM; it’s slow and usually not a quality win.

### Concurrency
- With one 5090: run **one ComfyUI server** and let it queue.
- Use batching in the draft workflow (N candidates per job) to maximize throughput.

### Observability
- Capture:
  - workflow JSON submitted
  - params injected
  - job id
  - seed(s)
  - runtime + VRAM stats (nice-to-have)
  - output filenames + hashes

---

## The agent contract: RenderSpec JSON

Instead of “prompting,” the agent produces a **RenderSpec** and compiles it into workflow params (directly or via an optional broker).

### Minimal RenderSpec schema (example)

```json
{
  "book_id": "gingerbear_01",
  "page": 7,
  "intent": "illustration",
  "scene": "Bear and Gingerbread Boy cross a creek on stepping stones at sunset",
  "characters": [
    {"id":"bear", "pose":"carefully stepping", "emotion":"focused"},
    {"id":"gingerbread", "pose":"arms wide balancing", "emotion":"excited"}
  ],
  "camera": {"shot":"wide", "angle":"slightly above", "lens":"storybook"},
  "environment": {"time":"golden hour", "weather":"clear", "location":"forest creek"},
  "constraints": [
    "no text",
    "two characters only",
    "no extra limbs",
    "kid-friendly",
    "clean background"
  ],
  "style_pack": "watercolor_whimsy_v1",
  "refs": {
    "style": ["bible/style_refs/style_03.png"],
    "characters": {
      "bear": ["bible/character_refs/bear_sheet_A.png"],
      "gingerbread": ["bible/character_refs/gb_sheet_B.png"]
    }
  },
  "seed": 1234567
}
```

### Style packs (critical for consistency)

A `style_pack` is a directory containing:

* prompt template (positive/negative blocks)
* optional style LoRA(s)
* palette references
* default sampler/steps recommendations

This keeps “style variability” controlled and deliberate.

---

## Workflow graphs (what to build)

You want 4 canonical workflows.

### 1) `draft.json` — burst generation

**Inputs**

* scene prompt (templated)
* negative prompt (templated)
* refs (style + character refs if using reference conditioning)
* base resolution (3:4 portrait)
* batch size (8–16)
* steps low (fast)

**Outputs**

* N images + metadata

**Purpose**

* Explore composition and staging, not perfect details.

### 2) `refine.json` — improve the winner without changing it

**Inputs**

* selected draft image
* same prompt template (more constrained)
* steps higher
* img2img denoise low (preserve composition)
* optional ControlNet for pose/depth/line stability

**Outputs**

* 1–3 refined variants

**Purpose**

* Turn “good draft” into “nearly final art” while keeping continuity.

### 3) `inpaint.json` — surgical fixes

**Inputs**

* image
* mask (agent can generate mask programmatically or from heuristics)
* inpaint prompt (“fix hands/eyes/etc.”) + global constraints
* denoise tuned for minimal disruption

**Outputs**

* fixed image

**Purpose**

* Kill the “reroll the whole page because a hand is cursed” loop.

### 4) `upscale_print.json` — print-ready upscaling + tiled decode

**Inputs**

* final art
* upscale factor (often 2×)
* tiled diffusion (if available) for large size
* tiled VAE decode to avoid VRAM spikes
* optional light sharpen / grain control (keep subtle)

**Outputs**

* print-resolution image (croppable to trim + bleed)

**Purpose**

* Efficiently reach 300DPI-ish output without generating huge images from scratch.

---

## Resolution and print targets (Dr. Seuss-ish)

Use **3:4 portrait** as your working aspect ratio.

Recommended ladder:

* Draft: **768×1024** or **1024×1365**
* Final: **1536×2048** (or **1792×2368** if you like the look)
* Print: **2× upscale** → 3072×4096 (then crop to your trim + bleed)

You generally want to **crop at the very end** to match your exact trim.

---

## Agent visual review (selection without auto-scoring)

After draft burst, the agent should inspect candidates directly and decide what to refine.

### Review checklist (simple, effective)

1. **Scene match**

   * Does the image clearly depict the requested action/composition?

2. **Constraint compliance**

   * No text/signage
   * Correct character count
   * Kid-friendly tone
   * No obvious anatomy/artifact failures

3. **Character consistency**

   * Faces, proportions, and palette should match character/style refs.

4. **Page readability**

   * Clear focal point and enough calm space for later page layout.

### Selection logic

* Keep the best 1–2 drafts.
* Refine those.
* Keep the best refined output as page final.

---

## The end-to-end book workflow

### Phase 0 — Book bible (one-time per book)

1. Decide `style_pack` (or create it).
2. Create **style references** (3–8 “golden” images).
3. Create **character sheets** (front/side/expression for each main character).
4. Lock naming, palette, recurring motifs, and “forbidden” elements.

Outputs live in: `books/<book_id>/bible/`

### Phase 1 — Story + page planning

1. Agent writes story text.
2. Agent breaks into pages and creates a `RenderSpec` per page.
3. Agent optionally generates rough thumbnails / storyboard (very low-res).

### Phase 2 — Page rendering loop (per page)

1. Submit `draft.json` with injected params → get 12 candidates
2. Agent reviews drafts and selects 1–2 candidates
3. Submit `refine.json` on selected candidates
4. If defects remain: `inpaint.json` targeted fixes
5. Submit `upscale_print.json` (2×)
6. Save final art + metadata

### Phase 3 — Layout (text + art → PDF)

* Use deterministic layout tooling:

  * place art
  * add text in consistent fonts
  * control margins/bleed
  * generate print-ready PDF
* Store layout config in `books/<book_id>/layout/book.yaml` for reproducibility.

---

## Quality knobs (when you’re willing to wait)

If you want “quality over speed,” spend time on:

* **More steps on final/refine**, not on draft.
* **Hi-res refine pass** (img2img low denoise at higher res).
* **Tiled upscaling / tiled VAE decode** for large outputs.
* **More candidates in the draft burst** (N=16) when the agent needs broader composition exploration.

Avoid “quality knobs” that mostly waste time:

* CPU offload for everything (usually slow, not better)
* generating at huge resolution from scratch (often less stable than 2-pass)

---

## Reproducibility and auditing

For each page, store:

* `renderspec.json`
* submitted workflow json (exact)
* seed(s)
* model identifiers (filenames + hashes if possible)
* prompts (rendered templates)
* outputs (drafts, refined, final, print)
* `review.json` with selection decisions and brief rationale

This makes it easy to:

* regenerate a page later
* swap a model and re-run only finals
* debug agent behavior

---

## Operational notes

### Backups

* Bible + RenderSpecs + finals are the gold.
* Drafts can be pruned later if disk is a concern.

### Upgrades

* Treat models like dependencies:

  * version pin per book
  * don’t “upgrade mid-book” unless you’re willing to re-render for consistency

### Security

* Keep the box offline if required.
* Make sure ComfyUI is not exposed publicly without auth.

---

## Implementation checklist (for the build agent)

1. Install/launch ComfyUI as a service
2. Standardize model directories and symlinks
3. Create 4 workflows:

   * `draft.json`
   * `refine.json`
   * `inpaint.json`
   * `upscale_print.json`
4. Implement direct ComfyUI orchestration:

   * submit workflow + params
   * poll job status
   * fetch outputs
   * write all artifacts to the `books/` structure
5. Implement agent visual-review logging:

   * selected candidates
   * rejection reasons
   * final selection rationale
6. Implement page layout pipeline (PDF)
7. Optional optimization:

   * caching by RenderSpec hash
8. Optional later:

   * add a thin `render_broker` wrapper if you want a stable local API boundary

---

## Appendix: “don’t fight these” rules for children’s books

* Don’t render text inside the art.
* Use references (character sheets / style refs) for consistency.
* Fix defects with img2img + inpaint, not rerolling prompts.
* Lock seeds for continuity once composition is approved.
* Always record everything needed to reproduce a page.

---
