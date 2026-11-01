# ComfyUI workflows for Notebook 1

Notebook 1 runs FLUX.2, MiniMax H3 and ACE-Step through ComfyUI (one server per T4), so the model
graph is data, not code. Each `<name>.json` is an API-format graph built from the official ComfyUI
template named below, with GGUF loaders (city96/ComfyUI-GGUF) so the weights fit a 16 GB T4. Each
`<name>.map.json` lists the `[node_id, input_name]` pairs the notebook fills.

| File | GPU | From template | Mapped inputs |
| --- | --- | --- | --- |
| `flux2_klein_ref.json` | cuda:0 | `image_flux2_klein_image_edit_9b_distilled` (product photo as reference latent, 4 steps, CFG 1) | `prompt`, `image`, `seed`, `width`, `height` |
| `flux2_klein_t2i.json` | cuda:0 | same graph without the reference image | `prompt`, `seed`, `width`, `height` |
| `minimax_h3_i2va.json` | cuda:1 | `video_minimax_h3_i2v` with the Turbo LoRA (8 steps), video + audio | `prompt`, `image`, `length` (frames, 17k+5), `seed`, `width`, `height` |
| `ace_step_bgm.json` | cuda:0 | `audio_ace_step_1_5_split` (turbo, 8 steps, instrumental) | `prompt` (tags), `seconds`, `seed` |

Loader filenames must match the `MODELS` list in `nb1_generative_studio.py` (the 4B FLUX variant is
swapped in by `FILE_SWAP`). Graphs were checked against ComfyUI's `/prompt` validation (Nov 2026
master); to edit one, load it in ComfyUI, change it and use **Export (API)**. Without GPUs, run the
notebook with `GP_DRY_RUN=1` to test the job loop end to end.
