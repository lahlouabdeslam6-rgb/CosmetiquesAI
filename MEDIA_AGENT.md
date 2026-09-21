# Product Media Agent — local description-driven rendering

The agent reads the current photo/video descriptions with Ollama (`qwen2.5:3b`). Its structured plan is validated before rendering. Explicit colors, formats, durations and zoom instructions override conflicting model guesses. The displayed summary is derived from the executed parameters.

The original product is segmented with local U2Net and composited without redrawing its label. Output photos are lossless WebP. The renderer supports solid/studio backgrounds or scenery generated with the locally cached OpenVINO model. Video is a silent 2D composition with configurable framing, camera motion and duration (3–15 seconds), not reconstruction of unseen views.

Each request stores the original reference URL, raw descriptions and executed plan. Corrections create a child version with feedback and retain the earlier results. Photos/videos are previews until an administrator approves them. Generated images cannot serve as the original reference, avoiding successive regeneration of the label.

Unsupported instructions are returned as requests to change the brief. Model/interpreter/render failures do not produce a substitute image. The CPU models run sequentially within the API worker. Changing the description does not train the model; revisions apply the supplied feedback to the product's previous plan.

## Running and checking

- `docker compose exec ollama ollama pull qwen2.5:3b`
- `docker compose build backend frontend`
- `docker compose up -d backend frontend` (Alembic applies migration 0017)
- `docker compose exec backend pytest -q`
- `docker compose exec frontend npx tsc --noEmit`

Model downloads require internet once. Model caches and cutouts live in the existing data volume. Inference then uses local services. Detailed scenery is generated at the local diffusion model's resolution and can be less sharp than the preserved product.

`python -m tests.manual_media_check` is an opt-in acceptance check: it creates unpublished media versions for product 1 using two different descriptions and verifies the encoded video durations. Do not run it automatically against a different catalogue.
