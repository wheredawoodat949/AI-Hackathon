# PROGRESS

Running status of what works, what's stubbed, and the current demo command.
Update at the end of every phase (CLAUDE.md §7).

## Repo health check (2026-06-20)
`git fsck --full --strict` clean on both this repo and the `_reference_soccertrack` clone; no
files >5MB ever committed; `.gitignore` correctly excludes `data/`, `outputs/`, `.venv/`,
`__pycache__/`. **One real issue found and fixed:** `feat/sponsors-vincent`'s merge commit
(`c98204c`) had left literal unresolved `<<<<<<<`/`=======`/`>>>>>>>` conflict markers committed
into `src/model/{__init__,sam_api,sam_backend,sam_local}.py` (invalid Python — broke every import
in that package). Vincent independently fixed it (`9b084c2`) before a parallel fix landed here;
verified clean (no markers anywhere across all 5 refs, his resolution lints + tests green). All
branches now import-clean.

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

**Stubbed / not yet built:** `src/model` (SAM backend — Phase 1), `src/tracking`, `src/pitch`,
`src/events`, `src/eval`, `src/obs`, `src/store`, `src/pipeline.run()`. `frontend/` empty.

**Eval status:** not measured yet (HOTA wired in Phase 2 via the dataset's `src.evaluation.gs_hota`).

## Dataset facts in use
- Dev match: **117093** (exists in mirror; canonical example in the docs).
- Split (80/10/10 over the 10 REAL mirror matches): train `117092,117093,118575,118576,118577,118578,128057,128058`
  · eval `132831` · test `132877`. (Mirror has no documented held-out set; this is our deterministic holdout.)
- FPS 25. GSR fields: track_id, role, jersey_number, team_side, x, y (+ player_id, bboxes).
- Attribution required: dataset is CC BY 4.0.

## Phase 0.5 — Rapid-dev scaffolding  ✅ (verified: ruff clean, 11/11 pytest green)
- [x] `pyproject.toml` — `pip install -e ".[dev]"`; ruff + pytest config. `Makefile` for common commands.
- [x] **SAM 3.1 abstraction** (`src/model/`): `SamBackend` Protocol + `Detection`/`FrameResult`/`TrackResult`,
      `get_backend()` factory (local|api), `sam_local.py` + `sam_api.py` impls (heavy imports deferred, `track()` stubbed).
- [x] Per-role stub modules with `TODO(Role X)` + real signatures: `tracking/tracker.py`, `pitch/homography.py`,
      `pitch/minimap.py`, `eval/hota.py` (shells to dataset `gs_hota`), `obs/sentry.py`, `obs/arize.py`,
      `store/redis_store.py`, `events/bas.py`. `pipeline.run()` wires the stages.
- [x] `tests/` — import-smoke (every module imports with no heavy deps), config/split invariants, loader, gpu.
- [x] 4 role branches pushed: `feat/tracking-ashmeet`, `feat/pitch-eval-shaaz`, `feat/sponsors-vincent`, `feat/events-demo-dawood`.
- [x] `docs/COMPUTE.md` — GPU/training options (team box, sponsor cloud, Colab/Kaggle; NERSC/JGI off-policy; Anupurna unverified).

**Guard rail:** heavy/optional imports (torch, cv2, sentry, arize, redis, requests) stay deferred inside
functions so `make test` stays green on any machine. Don't add them at module top level.

## Phase 1 — Core tracking  🟡 in progress (Role A, `feat/tracking-ashmeet`)
- [x] `GsrReplayBackend` (`src/model/replay.py`) — satisfies `SamBackend` by replaying GSR ground
      truth. Runs the whole pipeline with **no GPU**; doubles as the "perfect tracker" eval upper bound.
- [x] `src/data/video.py` (frame iter, mp4 writer w/ PNG fallback, synthetic canvas) +
      `src/tracking/visualize.py` (boxes + IDs + role colors).
- [x] `src/tracking/demo.py` — `python -m src.tracking.demo` renders an annotated clip to `outputs/`.
- [x] **VERIFIED on Mac (no GPU):** produced `outputs/track_117093_replay.mp4` — 100 frames, 960x376,
      25 fps; 20 players (green) + 2 keepers (orange) with persistent IDs. Tests: 14/14 green, ruff clean.
- [x] **`sam_local.py` implemented for real** via 🤗 Transformers `Sam3VideoModel`/`Sam3VideoProcessor`
      (the official distribution path per the live model card at huggingface.co/facebook/sam3 —
      weights auto-download via `from_pretrained()` once access is approved, no manual file
      placement). Runs one full video pass per prompt (PCS finds all instances of ONE concept per
      call; no documented multi-concept syntax) and merges per-frame results, offsetting instance
      IDs so prompts never collide. Adapted to our `Detection(bbox=(x,y,w,h))`/`FrameResult` shapes
      incl. new `foot_xy`/`center_xy` helpers on `Detection` and `of_label()`/`width`/`height` on
      `FrameResult` (additive, backward compatible). Targets the Colab T4 GPU (fp16, not the model
      card's default bf16 — T4 is pre-Ampere). **NOT yet live-tested** (access request submitted,
      awaiting Meta's review as of 2026-06-21) — error paths are unit-tested (18/18 tests), the
      actual inference call needs a live run + approved access to confirm.
- [x] **`notebooks/colab_sam_tracking.ipynb`** — full Colab bring-up: GPU check, clone+install,
      gated SAM3 weight request/download (flags the real risk: access can be denied/delayed),
      download a real clip, run `--backend local`, preview the output. **Next action: open it in
      Colab, select the T4 runtime, and run it for real.**
- [x] **`sam_api.py` (fal.ai) implemented and verified-real but DEFERRED** in favor of Colab — see
      [docs/DEFERRED.md](docs/DEFERRED.md) for when/how to pick it back up (e.g. if Colab's gated
      weights access stalls). Credential-check path tested; network path still needs a real FAL_KEY.

**GPU access — CONFIRMED (Slack + live.hackberkeley.org, 2026-06-20):** hackathon provides none;
RunPod isn't even on the official sponsor-resource list (Slack-only, booth visit needed, not
guaranteed); Annapurna Labs is a prize showcase, not GPU credits (and uses AWS Neuron, not CUDA,
anyway); our only team GPU (K1900, ~2GB) is below SAM 3.1's ~4GB floor. **Current plan: Google
Colab's free T4** (`sam.backend: local`); fal.ai stays as a documented, ready fallback. Full
writeup: [docs/COMPUTE.md](docs/COMPUTE.md). ML extensions + QLoRA verdict (skip QLoRA):
[docs/ML_DIRECTIONS.md](docs/ML_DIRECTIONS.md).

## Phase 2+ — not started
Phase 2 = homography → minimap → HOTA (Role B). The replay backend gives Role B real tracked input now.
