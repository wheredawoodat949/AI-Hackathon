# AI-Hackathon — Soccer Game-State Analysis (SAM 3.1 → Minimap → HOTA)

Full-pitch panoramic match video → **Meta SAM 3.1** segments + tracks every
player/goalkeeper/referee → live **2D tactical minimap** → evaluated against
**SoccerTrack v2** GSR ground truth (real HOTA, never fabricated). Instrumented
for reliability (Sentry), eval/observability (Arize), and semantic search (Redis).

> Mission framing: accessible tactical analysis for amateur/university teams who
> can't afford pro analytics — the dataset is amateur matches.

See [`CLAUDE.md`](CLAUDE.md) for the full architecture, dataset facts, phase
ordering, and working agreement. See [`PROGRESS.md`](PROGRESS.md) for live status.

## Quickstart
```bash
make setup                      # venv + editable install (.venv) with dev tools
source .venv/bin/activate
make test                       # ruff + pytest (no GPU/data needed) — should be green
make gpu                        # CUDA check (fails loud if no GPU)
make frame MATCH=117093         # download from Drive mirror + print a real GSR frame
```
Or the explicit commands: `pip install -r requirements.txt`, then
`python -m src.data.download --match 117093 [--no-videos]` and
`python -m src.data.inspect --match 117093`. Data comes from the link-public **Google Drive
mirror** by default (no auth); use `--source hf` for the gated HF copy (`HF_TOKEN`).
`notebooks/demo.ipynb` imports from `src/` and holds no logic.

**Compute / GPUs:** see [docs/COMPUTE.md](docs/COMPUTE.md). **Team & branches:** see CLAUDE.md §10.

## Layout
```
src/
  config.py        # single source of truth (config.yaml + .env)
  data/            # download.py (one-match HF) + loader.py (GSR/BAS reader) + inspect.py
  utils/gpu.py     # CUDA check, fails loud
  model/           # SAM 3.1 backend abstraction (local | api) — Phase 1
  tracking/ pitch/ events/ eval/ obs/ store/   # per-phase modules
  pipeline.py      # end-to-end orchestration entrypoint
notebooks/demo.ipynb   # the thing we run for judges
outputs/  frontend/    # gitignored artifacts / web app (last phase)
```
All reusable logic lives in `src/`; notebooks and the frontend import it. Heavy
artifacts (videos, weights, `data/`, `outputs/`) are gitignored and stay local.

## Dataset
[SoccerTrack v2](https://github.com/AtomScott/SoccerTrack-v2) ·
[docs](https://atomscott.github.io/SoccerTrack-v2/) ·
[Hugging Face](https://huggingface.co/datasets/atomscott/soccertrack-v2) ·
[paper](https://arxiv.org/abs/2508.01802).

- Dev match **117093**. Real mirror match IDs (verified by listing it; the docs' assumed
  117091–117100 don't match the files): `117092, 117093, 118575, 118576, 118577, 118578,
  128057, 128058, 132831, 132877`. Split 80/10/10: train (8) · eval `132831` · test `132877`.
- Mirror carries `gsr/ bas/ raw/ videos/` (no `mot/`) → eval with GSR HOTA
  (`python -m src.evaluation.gs_hota …`); we do **not** reimplement metrics.

**Attribution:** SoccerTrack v2 is licensed **CC BY 4.0** (A. Scott et al.). Dataset code is MIT.
No player names — IDs are jersey-number based.

## Sponsors (each toggleable in `config.yaml`, none on the critical path)
Sentry (reliability) · Arize (eval/observability) · Redis (vector search) · Anthropic / Claude Code (build layer).
