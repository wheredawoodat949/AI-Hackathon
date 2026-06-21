# PROGRESS

Running status of what works, what's stubbed, and the current demo command.
Update at the end of every phase (CLAUDE.md §7).

## Current demo command (Drive mirror — no auth needed)
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python -m src.utils.gpu                                   # CUDA check (fails loud if no GPU)
python -m src.data.download --match 117093 --no-videos    # Drive mirror, annotations only (fast)
python -m src.data.inspect  --match 117093 --half 1       # print one real GSR frame
# Phase 1 (needs video): python -m src.data.download --match 117093   (adds the panorama mp4s)
```

## Data sources (verified 2026-06-20 by listing the mirror)
- **Drive mirror `1N2Qx2qkFgRtpbHitl2Vh6sLVYGgqkWwn`** — DEFAULT (`dataset.source: drive`).
  Official mirror (per repo docs), **link-public** → `gdown` lists+fetches it with no auth.
  Downloader filters to ONE match (skips videos with `--no-videos`). Contains `gsr/ bas/ raw/ videos/`.
- **HF `atomscott/soccertrack-v2`** — canonical but **GATED** (401 without token). Kept as
  `--source hf` alternative; needs `hf auth login` / `HF_TOKEN`.
- stc2025 challenge Drive (`1_o78gcL4…`) = competition subset, not used.

## Real match IDs (from the mirror — NOT the docs' assumed 117091–117100)
`117092, 117093, 118575, 118576, 118577, 118578, 128057, 128058, 132831, 132877` (10 matches,
each with gsr+bas+raw+videos). **No `mot/` in the mirror** → use GSR HOTA (`gs_hota`), not MOT HOTA.

## Phase 0 — Foundation  ✅ scaffolded (verify on GPU box)
- [x] Repo layout per CLAUDE.md §3 (`src/` packages, `notebooks/`, `outputs/`, `frontend/`).
- [x] `.gitignore` (data/videos/weights/.env), `.env.example`, `config.yaml`, `requirements.txt`.
- [x] `src/config.py` — single source of truth (paths, dev_match, 80/10/10 split, SAM backend, sponsor flags).
- [x] `src/utils/gpu.py` — CUDA check, **fails loud** if no GPU (ALLOW_CPU=1 escape hatch for pure-Python smoke tests).
- [x] `src/data/download.py` — one-match HF download (mirrors dataset `download.sh`, `--no-videos` fast path).
- [x] `src/data/loader.py` — self-contained GSR/BAS reader matching the verified on-disk schema.
- [x] `src/data/inspect.py` — prints one GSR frame's entities.
- [ ] **Verify on GPU box:** run the 4 commands above; confirm CUDA + a printed GSR frame.

**Stubbed / not yet built:** `src/pitch`, `src/events`, `src/eval`, `src/obs`, `src/store`,
`src/pipeline.run()`. `frontend/` empty.

**Eval status:** not measured yet (HOTA wired in Phase 2 via the dataset's `src.evaluation.gs_hota`).

## Phase 1 — Core tracking  ⏳ code written, UNVERIFIED (needs Colab GPU run)
Compute decision: **Google Colab is the GPU box** (free T4 16GB runs SAM 3, 848M params).
This laptop CANNOT run SAM 3 (no usable Python; GPU is a 2GB Quadro K2100M) — code only here.
- [x] `src/model/sam_backend.py` — `SamBackend` protocol + `Detection`/`FrameResult` types
      (`foot_xy` = bbox bottom-middle = the point Phase 2 projects to pitch meters).
- [x] `src/model/sam_local.py` — SAM 3.1 via Ultralytics `SAM3VideoSemanticPredictor`
      (text-prompted detect+track). Lazy imports; fails loud if `sam3.pt` missing (gated).
- [x] `src/model/sam_api.py` — hosted-endpoint stub (NotImplemented; local is the path).
- [x] `src/model/__init__.py` — `get_backend(cfg)` factory reading `sam.backend`.
- [x] `src/tracking/annotate.py` — draw tracked boxes+IDs onto a clip -> annotated mp4.
- [x] `notebooks/colab_run.ipynb` — end-to-end Colab runner (GPU check -> clone -> install
      -> gated weights -> download 1 match -> cut clip -> track -> tracks.json + annotated mp4).
- [x] `config.yaml`: `sam.backend: local` + `sam.weights: sam3.pt`; `requirements.txt` += ultralytics.
- [ ] **RUN IT on Colab:** accept SAM 3 HF access, run the notebook, confirm a saved clip with
      tracked players + a non-zero detection count. (Watch: tiny players in 4K — we downscale to
      1920w in the notebook; may need tiling to recover recall.)

## Known gated/manual steps for the GPU run
- SAM 3 weights `sam3.pt`: request access at https://huggingface.co/facebook/sam3, then HF token.
- If SAM errors on `clip`: `pip install git+https://github.com/openai/CLIP.git` (in the notebook).
- Private repo clone in Colab needs a GitHub token (prompted in notebook cell 2).

## Dataset facts in use
- Dev match: **117093** (exists in mirror; canonical example in the docs).
- Split (80/10/10 over the 10 REAL mirror matches): train `117092,117093,118575,118576,118577,118578,128057,128058`
  · eval `132831` · test `132877`. (Mirror has no documented held-out set; this is our deterministic holdout.)
- FPS 25. GSR fields: track_id, role, jersey_number, team_side, x, y (+ player_id, bboxes).
- Attribution required: dataset is CC BY 4.0.

## Phase 1+ — not started
See CLAUDE.md §8 and the branch plan in the kickoff. Phase 1 = SAM 3.1 backend abstraction + one
working impl + annotated clip (Role A, `feat/tracking`).
