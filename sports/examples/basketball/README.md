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

Modes: `PLAYER_DETECTION`, `BALL_DETECTION`, `PLAYER_TRACKING`, `TEAM_CLASSIFICATION`.

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
Set the `BASKETBALL_DETECTION_MODEL` env var (or edit `DETECTION_MODEL_PATH` in `main.py`) to a
fine-tuned checkpoint's path. Everything else in this file is unaffected — same COCO-style
class IDs (`person=0`) only if the fine-tuned model keeps that scheme; adjust `PERSON_CLASS_ID`/
`BALL_CLASS_ID` at the top of `main.py` if not.

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
