# ONBOARDING — Basketball Pivot (2026-06-21)

Orientation findings before any basketball code is written. **Several facts in the kickoff
prompt don't match what's actually in the repo — corrected below.** Nothing destructive done;
no training, no commits to `main`/`sam_model_vincent`. New branch `basketball` created off
`origin/sam_model_vincent` for this work.

> **Status update (2026-06-21, later same day):** Phase 0 (this doc) is done; Phase 1 (basketball
> demo pipeline) and Phase 2 (detection-data scaffold) are also done — see `AGENT_TASKS.md` for
> current status and `UPDATE.md` for the detailed log. This doc is left as-is below as the
> point-in-time orientation record; don't edit history, append new findings to `UPDATE.md` instead.

---

## 1. Repo & branch map (`git fetch --all`, verified 2026-06-21)

| Branch | Owner | Last commit | What it actually contains |
|---|---|---|---|
| `main` | shared | `faf3652` (merge of tracking-ashmeet PR #4) | Soccer/SoccerTrack-v2 pipeline scaffold: `src/` packages, tests, `SamBackend` interface, GSR-replay backend. **Does NOT yet have the YOLO pivot** (see below). |
| `sam_model_vincent` | **Vincent** | `257bea4` "Add sports module (team differentiation) as standalone folder" | Branched from `main` @ `faf3652`. Adds: `Soccer_1.ipynb`, `segment_videos_with_segment_anything_3.ipynb`, and the **entire Roboflow `sports` repo** vendored under `sports/`. **This is the real soccer artifact** — see §2. |
| `feat/tracking-ashmeet` | Ashmeet (me) | `6065c29` "Pivot to YOLO+ByteTrack" | The SoccerTrack-v2 pipeline's tracking work. Independently hit the SAME SAM 3.1 gating/transformers wall Vincent hit, and pivoted to **Ultralytics YOLO + ByteTrack** (`src/model/yolo_backend.py`) — verified working on a Colab T4. **Not yet merged into `main` or `sam_model_vincent`.** |
| `feat/pitch-eval-shaaz` | Shaaz | `14a10d0` "notebook: 25-epoch train, +10-epoch continuation cell" | Shaaz is training something (25+10 epochs) in a notebook — not yet inspected in depth; flag for follow-up if relevant to basketball. |
| `feat/sponsors-vincent` | Vincent (older) | `9b084c2` | An EARLIER, separate line of Vincent's work (sponsor/infra stubs + a different, now-superseded SAM-local attempt). Not the branch referenced in the kickoff prompt — superseded by `sam_model_vincent`. |
| `feat/events-demo-dawood` | Dawood | `16486e3` | Unchanged since Phase 0.5 scaffold; no events/demo work yet. |

**New branch created:** `basketball`, off `origin/sam_model_vincent` @ `257bea4`. Not yet pushed pending your go-ahead beyond this orientation.

---

## 2. Vincent's actual soccer pipeline (corrected facts)

> **The kickoff prompt's assumed facts — YOLOv5s, a custom-trained `best.pt`, a `data.yaml`,
> classes `{0: person, 1: ball}`, a committed `soccer_1_cv.mp4` demo — do not match what's in
> the repo.** Searched the full git history of every branch for `best.pt`, `data.yaml`, and
> `soccer_1_cv.mp4`: **zero matches, on any branch, ever.** Here's what's actually there.

**Vincent vendored the [Roboflow `sports`](https://github.com/roboflow/sports) repo and ran its
pre-built soccer example — he did not train anything himself.**

`Soccer_1.ipynb` (14 cells, Colab) does, in order:
1. `git clone https://github.com/roboflow/sports.git` + `pip install -e .`
2. `pip install -r examples/soccer/requirements.txt`, plus pinned `numpy<2.1`, `numba>=0.59`,
   `umap-learn==0.5.6`, `supervision==0.23.0`, `ultralytics==8.2.0` (later bumped to
   `ultralytics>=8.3.0`).
3. Downloads **three separate pretrained checkpoints** via `gdown` from Roboflow's own Google
   Drive (NOT trained by Vincent, NOT YOLOv5 — Roboflow's models are Ultralytics-compatible,
   likely YOLOv8-family given the `ultralytics==8.2.0` pin):
   - `football-ball-detection.pt` (~137MB)
   - `football-player-detection.pt` (~137MB)
   - `football-pitch-detection.pt` (~140MB)
4. Patches `sports/examples/soccer/main.py` to remove `cv2.imshow`/`waitKey`/`destroyAllWindows`
   (headless Colab).
5. Runs `main.py --source_video_path data/2e57b9_0.mp4 --mode PLAYER_DETECTION` then again with
   `--mode TEAM_CLASSIFICATION`. `data/2e57b9_0.mp4` is **Roboflow's own published sample clip**
   from their soccer-analytics tutorial — not from our SoccerTrack-v2 dataset, not committed to
   this repo (lives only in the Colab session / Vincent's Drive).
6. Renders an H.264 preview inline in the notebook. **No demo video is committed to git** —
   `soccer_1_cv.mp4` either lives only in Vincent's Drive/Colab session, or was shared outside
   GitHub (Slack?). **Please locate/share it if you want it as a literal visual target file.**

**There is no training step in this pipeline at all** — it's 100% pretrained-checkpoint
inference. `sports/examples/soccer/main.py` supports 6 modes (confirmed in source):
`PITCH_DETECTION`, `PLAYER_DETECTION`, `BALL_DETECTION`, `PLAYER_TRACKING`,
`TEAM_CLASSIFICATION`, `RADAR`. Team classification (`sports/sports/common/team.py`) uses
SigLIP embeddings + UMAP + KMeans clustering on player crops — this is the "team
differentiation" in Vincent's commit message, and it's a real, working, reusable component.

**The second notebook, `segment_videos_with_segment_anything_3.ipynb`, is just Roboflow's
generic public SAM3 tutorial notebook** ("How to Segment Videos with Segment Anything 3"),
not soccer- or basketball-specific. It requires the same gated `facebook/sam3` HF access we
spent hours on today (`os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")`). **Vincent hit the
same SAM3 gating/access wall we did**, and — like us — appears to have pivoted to a
pretrained-checkpoint approach (Roboflow's `sports` toolkit) instead of fighting it further.
This is a genuine, useful convergence: two independent paths landed on "skip SAM3, use an
ungated pretrained detector."

**The training notebooks under `sports/examples/soccer/notebooks/`**
(`train_ball_detector.ipynb`, `train_player_detector.ipynb`, `train_pitch_keypoint_detector.ipynb`)
are **Roboflow's own example notebooks for training their models from scratch on Roboflow
Universe data** — vendored as reference/instructions, not run or customized by Vincent (no
evidence in git history that these were executed or modified).

---

## 3. Basketball: dataset, notebook, Kaggle — all MISSING (per your own "stop and tell me" rule)

- **No basketball notebook** exists in this repo, on any branch.
- **No basketball dataset** (Basketball-51 or otherwise) exists in this repo.
- **No Kaggle API credentials** found on this machine (`~/.kaggle/kaggle.json` does not exist),
  so I cannot pull `sarbagyashakya/basketball-51-dataset` from Kaggle right now even if asked to.
- **No Pika Labs, Redis-for-this-feature, or Arize-for-this-feature integration** exists yet —
  `src/obs/arize.py` and `src/store/redis_store.py} exist only as Phase-0.5 stub modules (no-ops,
  `TODO` markers) from the earlier soccer-tracking scaffold; no Pika code anywhere.

**Per your own instruction: STOPPING here rather than fabricating any of this.** I need from you:
1. The Kaggle API key (`kaggle.json`) or your Kaggle credentials, to pull Basketball-51, **and/or**
2. Vincent's basketball notebook + dataset, if they exist outside GitHub (you mentioned Discord
   links you'd need to export manually).
3. Confirmation on the Basketball-51 label gap (see §4 — this affects which Path A/B you want).

---

## 4. The Basketball-51 label problem (flagging now, before you decide)

Per your own kickoff note: Basketball-51 (Kaggle `sarbagyashakya/basketball-51-dataset`) is
**10,311 six-second action-recognition clips labeled only by shot outcome** (2pt/3pt/FT/mid ×
make/miss) — **no player/ball bounding boxes**, and clips are low-res 320×240 QVGA. This matches
your own Path A / Path B framing:
- **Path A (no training):** run an existing pretrained `person`+`sports ball` detector (YOLO
  COCO classes, exactly what `feat/tracking-ashmeet`'s new `yolo_backend.py` already does, or
  Roboflow's `football-player-detection.pt`/`football-ball-detection.pt` as Vincent already
  proved out) + ByteTrack on Basketball-51 clips. **No labels needed.** Fastest path to a demo
  video matching the soccer one's style.
- **Path B (fine-tune):** needs a *labeled* basketball detection set — Basketball-51 itself can't
  supply this. Either pull a separate Roboflow basketball-detection dataset, or pseudo-label
  Basketball-51 frames with the Path-A detector + hand-review. Real extra work; do after Path A.

---

## 5. Old reference repo — need the path

You mentioned "an old repo (my previous project) with good `CLAUDE.md` files" to borrow
conventions from, read-only. **I don't have its path** — the only candidate I can see from this
session's context is `/Users/ashmeetsingh/Downloads/CLAUDE.md` (the CS189@Home ML-course-platform
project), but I'm not confident that's the one you mean. **Please give me the exact path** before
I fold its conventions into the basketball `CLAUDE.md` draft.

---

## 6. Sponsor integration status

| Sponsor | Status | Notes |
|---|---|---|
| **Redis** | Stub only (`src/store/redis_store.py`, no-op `init()`/`upsert`/`search`) | From the soccer-tracking scaffold. Needs real wiring for basketball live-state/streaming. |
| **Arize** | Stub only (`src/obs/arize.py`, no-op) | Same — needs real per-detection logging wiring. |
| **Pika Labs** | Nothing exists | No code, no API key plumbing, no `synthetic/` folder. Net-new for this pivot. |

---

## 7. A decision worth making explicitly: which detector/tracker stack?

We now have **two independently-built, working, ungated tracking paths** that solve the same
problem two different ways:

| | `feat/tracking-ashmeet` (`yolo_backend.py`) | `sam_model_vincent` (Roboflow `sports`) |
|---|---|---|
| Detector | Ultralytics YOLO11n, COCO `person`/`sports ball` (generic) | Roboflow's 3 sport-specific checkpoints (ball/player/pitch) |
| Tracker | ByteTrack via `model.track()` | Roboflow's own `PLAYER_TRACKING` mode (also ByteTrack-based, via `supervision`) |
| Team split | Not yet (planned: jersey-color k-means) | **Already working** (`sports/sports/common/team.py`, SigLIP+UMAP+KMeans) |
| Interface | Behind our `SamBackend` protocol (swappable) | Roboflow's own bespoke `main.py` CLI (not behind any shared interface) |
| Pitch mapping | Not yet (planned: homography from raw calib) | **Already working** (`PITCH_DETECTION`/`RADAR` modes, pitch keypoint model) |

Roboflow's toolkit is *more soccer-complete* (pitch mapping + team split already work) but is
*not behind any interface* and is *soccer-specific* (sport config baked into
`sports/sports/configs/soccer.py`). Your `yolo_backend.py` is *interface-clean* and
*sport-agnostic* but *missing* team/pitch features. **For basketball, Roboflow's pitch-specific
pieces (pitch keypoints, radar view) won't transfer** — basketball needs different court
geometry — but **`sports/sports/common/team.py` (team classification) is sport-agnostic and
directly reusable**, and Roboflow's player/ball detection + tracking pattern is exactly Path A.

**DECIDED (2026-06-21):** use Roboflow's `sports` toolkit directly for basketball — no
`SamBackend` wrapping. **Caveat flagged and accepted:** Roboflow's pretrained
`football-player-detection.pt`/`football-ball-detection.pt` are soccer-domain-trained and may not
generalize to basketball broadcast footage; Path A swaps in a generic COCO `person`/`sports ball`
detector (plain Ultralytics YOLO weights) through the same runner pattern instead of those two
checkpoints. `sports/sports/common/team.py` (team classification) is reused as-is — sport-agnostic.

---

## 8. Proposed `data.yaml` / directory layout for basketball (Path A first, Path B-ready)

```
basketball/
├── data/
│   ├── basketball51/            # raw Kaggle download (gitignored — large)
│   └── clips/                   # selected clean clips for the Path-A demo (gitignored)
├── weights/
│   ├── soccer_best.pt           # if/when we ever fine-tune soccer (not yet — Vincent uses Roboflow's pretrained 3)
│   └── basketball_best.pt       # Path B output (fine-tuned), once we have labels
├── data.yaml                    # Path B only — created once a labeled basketball det. set exists:
│                                 #   names: [person, ball]  (matching Roboflow's class scheme)
│                                 #   train/val: paths into data/basketball_labeled/
├── runs/
│   ├── soccer/                  # kept separate, untouched (Vincent's domain)
│   └── basketball/               # basketball training/inference runs
├── synthetic/                    # Pika Labs-generated basketball imagery (Phase 4), flagged in data.yaml
├── src/
│   └── model/
│       └── (proposal) basketball_backend.py or reuse yolo_backend.py with classes=[0] + sports/team.py
└── ONBOARDING.md, UPDATE.md, CLAUDE.md  (this orientation)
```

No basketball data has been downloaded; this layout is proposed, not yet created on disk.

---

## 9. Resolution (2026-06-21)

1. **Kaggle access:** via `kagglehub.dataset_download("sarbagyashakya/basketball-51-dataset")`,
   run inside the Colab notebook where Kaggle auth already works. No local credentials needed/used.
2. **"Old repo"** = this repo's own prior `CLAUDE.md` (the SoccerTrack-v2/SAM3 pipeline doc) — not
   a separate project. Conventions folded into the new `CLAUDE.md` (environment/secrets section,
   branch-ownership table).
3. **`soccer_1_cv.mp4`** — still unresolved; not found in git, not blocking Phase 1 (Path A
   produces its own fresh basketball demo video regardless).
4. **Detector stack — DECIDED:** Roboflow's `sports` toolkit directly (see §7 update above), with
   a generic COCO detector swapped in for Path A instead of the soccer-specific checkpoints.
5. **Go-ahead:** pending — this orientation (Phase 0) is committed to `basketball`; next message
   should confirm before Phase 1 (actual Kaggle pull + first tracking run) starts.
