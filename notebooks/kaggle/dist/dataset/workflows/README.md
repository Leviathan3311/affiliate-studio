# ComfyUI workflows for Notebook 1

Notebook 1 runs FLUX.2, MiniMax H3 and ACE-Step through ComfyUI (one server per T4), so the model
graph is data, not code. For each workflow below, build it in ComfyUI, then **Workflow → Export
(API)** and save it here, plus a `.map.json` telling the notebook which node inputs to fill.

| File | GPU | Must contain | Inputs to map |
| --- | --- | --- | --- |
| `flux2_klein_ref.json` | cuda:0 | FLUX.2 [klein] 9B (FP8/GGUF Q8) with a reference-image input (product photo kept unchanged) | `prompt`, `image`, `seed`, `width`, `height` |
| `flux2_klein_t2i.json` | cuda:0 | Same model, text-to-image (no product photo uploaded) | `prompt`, `seed`, `width`, `height` |
| `minimax_h3_i2va.json` | cuda:1 | MiniMax H3 GGUF Q4_K_M + H3-Turbo-LoRA 8 steps, image-to-video with audio (32 kHz) | `prompt`, `negative`, `image`, `seconds`, `seed` |
| `ace_step_bgm.json` | cuda:0 | ACE-Step 1.5 text-to-music | `prompt`, `seconds`, `seed` |

`.map.json` format: each field lists `[node_id, input_name]` pairs from the exported graph:

```json
{"prompt": [["6", "text"]], "image": [["12", "image"]], "seed": [["3", "seed"]],
 "width": [["5", "width"]], "height": [["5", "height"]]}
```

The `MODELS` list at the top of `nb1_generative_studio.py` downloads the weight files into
`ComfyUI/models/...`; keep its filenames identical to the loader nodes in these workflows.
Until these files exist, run the notebook with `GP_DRY_RUN=1` to test the job loop end to end.
