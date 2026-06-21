# Basketball tracking (Path A — CLAUDE.md §3/§4)

Adapted from `sports/examples/soccer/main.py`. Differences explained in `main.py`'s module
docstring — short version: **one generic COCO-pretrained detector** (`yolo11n.pt`, ungated,
auto-downloads) instead of soccer's 3 sport-specific checkpoints, because no basketball-specific
detection model or labeled dataset exists yet. No pitch/radar modes — there is no basketball
court keypoint model.

## Usage
```bash
pip install -e ../..
pip install -e ../../.. --no-deps
pip install -r requirements.txt
python main.py \
  --source_video_path <clip.mp4> \
  --target_video_path <out.mp4> \
  --device cuda \
  --mode TEAM_CLASSIFICATION
```

Modes: `PLAYER_DETECTION`, `BALL_DETECTION`, `PLAYER_TRACKING`, `TEAM_CLASSIFICATION`,
`POSSESSION`.

`POSSESSION` reuses the same detection/tracking/team pass and adds movement trails, an estimated
holder marker, and a two-team possession HUD. Vincent's shared soccer possession/trail work from
`sam_model_vincent` commit `c76c85d` is the basis for these shared primitives. Basketball has
no court homography yet, so holder selection uses an 80-pixel player-to-ball radius with temporal
hysteresis. The HUD is explicitly labeled `EST. POSSESSION`; it is a demo heuristic, not an
evaluation metric or ground truth.

## Verified (2026-06-21, CPU, synthetic test clip)
- `PLAYER_DETECTION` / `PLAYER_TRACKING` / `BALL_DETECTION`: run end-to-end, produce a valid
  annotated output video. Detection + tracking logic is the same proven pattern as the soccer
  script, just pointed at a generic model.
- `TEAM_CLASSIFICATION`: crashed (SIGSEGV) on a **degenerate local test** (1 real frame repeated
  15x — near-duplicate crops triggered a UMAP/numba edge case, a known small-sample fragility on
  macOS, not a logic bug in this file — `TeamClassifier` itself is unmodified Roboflow code).
  **Not yet verified on a real multi-frame clip with genuine crop diversity** — that's what the
  Colab run on real Basketball-51 footage will confirm.

## Swapping in a basketball-specific model later (Phase 3)
Set the `BASKETBALL_DETECTION_MODEL` env var to a fine-tuned checkpoint's path. The defaults
remain COCO (`person=0`, `sports ball=32`). A fine-tuned dataset may use multiple player/action
classes, so set comma-separated `BASKETBALL_PERSON_CLASS_IDS` and
`BASKETBALL_BALL_CLASS_IDS` to the exact IDs printed by
`python -m src.training.basketball inspect`. See `docs/TRAINING_BASKETBALL.md` from the root.

## Optional Redis + Arize output

The runner always constructs the shared tracking observer, but it is a no-op while sponsor flags
remain false. To publish tracked player foot positions and telemetry:

1. Install the optional clients: `pip install redis "arize>=8.35,<9"`.
2. Put `REDIS_URL` and/or `ARIZE_API_KEY` + `ARIZE_SPACE_ID` in the root `.env`.
3. Enable only the relevant flags under `sponsors` in the root `config.yaml`.
4. Run the same commands above. Redis/Arize failures are logged and do not stop video output.

The runtime reports observed track-set churn (new/lost ByteTrack IDs between frames). It does not
call that value an ID-swap rate: true ID swaps require identity ground truth or a validated
association, neither of which Path A currently has.
