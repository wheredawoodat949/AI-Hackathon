# CLAUDE.md

> Project context for Claude Code. Read this fully before doing anything. When in doubt, prefer the **simplest thing that produces a visible result**, then iterate. Cal Hacks 2026 — judging is imminent.

---

## 0. TL;DR for Claude

We are building **real-time multi-agent tracking of athletes (+ ball) in sports footage**,
packaged for sponsor tracks. The soccer line (Vincent, `sam_model_vincent`) already works:
pretrained detector + tracker + team classification on a soccer clip. **Current task: replicate
that on basketball footage** — but Basketball-51 (the dataset named in the kickoff) has **no
detection labels**, so the path is "run an existing pretrained detector + tracker on basketball
clips," not "train a basketball model from scratch." See §4.

- **Soccer (done, reference):** Roboflow's `sports` toolkit (vendored under `sports/`) +
  3 pretrained checkpoints (ball/player/pitch detection) + `supervision`'s ByteTrack, run via
  `sports/examples/soccer/main.py --mode {PLAYER_DETECTION,TEAM_CLASSIFICATION,...}`. **Not a
  custom-trained model** — Vincent did not train anything; he ran Roboflow's pretrained example.
- **Basketball (current task):** no labeled detection dataset exists for this sport in-repo or in
  Basketball-51. Path A (do first): generic pretrained person+ball detector (COCO classes, e.g.
  Ultralytics YOLO — already built and verified at `feat/tracking-ashmeet`'s `yolo_backend.py`)
  + ByteTrack on Basketball-51 clips → one annotated demo video. Path B (after A): fine-tune from
  a *separately sourced labeled* basketball detection set (Basketball-51 itself can't supply
  labels). See `ONBOARDING.md` for full findings and open questions.
- **Sponsor tracks in scope:** Redis (live state/streaming), Pika Labs (synthetic training
  imagery + demo visuals), Arize (ML observability/drift). Anthropic/Claude Code is the build
  layer (meta).
- **Decided 2026-06-21:** for basketball, use Roboflow's `sports` toolkit **directly** (its
  `main.py`-style runner, `team.py` classifier, annotators) rather than wrapping it behind the
  separate `SamBackend` interface from `feat/tracking-ashmeet`. Caveat: Roboflow's pretrained
  `football-player-detection.pt`/`football-ball-detection.pt` are soccer-domain-trained and may
  not generalize to basketball broadcast footage — for Path A, swap in a generic COCO
  `person`/`sports ball` detector (e.g. plain Ultralytics YOLO weights) through the same runner
  pattern, not the football-specific checkpoints.
- **Basketball-51 access:** via `kagglehub.dataset_download("sarbagyashakya/basketball-51-dataset")`,
  run in the Colab notebook (Kaggle auth already works there). No local Kaggle credentials exist
  on the dev machine — don't assume `kaggle.json` is available outside Colab.
- **"The old repo" = this repo's own `CLAUDE.md`** as it existed on `sam_model_vincent` before this
  basketball rewrite (the SoccerTrack-v2/SAM-3.1 pipeline doc) — not a separate project. Its
  conventions (environment/secrets pattern, branch-ownership table, phase structure) are folded
  into this file already.

---

## 1. Repositories & branches

- **This repo:** https://github.com/wheredawoodat949/AI-Hackathon
- **`sam_model_vincent`** — Vincent's branch, **the base of truth for the soccer artifact**.
  Contains `Soccer_1.ipynb`, `segment_videos_with_segment_anything_3.ipynb` (generic SAM3
  tutorial, not sport-specific), and the vendored `sports/` (Roboflow) toolkit. Never push to it
  directly without asking.
- **`basketball`** — branched off `sam_model_vincent`. Where this task's work happens.
- **`feat/tracking-ashmeet`** — a sibling soccer-tracking line (SoccerTrack-v2 dataset, different
  from Vincent's). Independently hit the same SAM 3.1 gating wall and pivoted to Ultralytics
  YOLO + ByteTrack (`src/model/yolo_backend.py`, verified working on Colab T4). Worth reusing for
  basketball Path A — not yet merged anywhere.
- **The old reference repo** — separate, unrelated, READ-ONLY. **Path not yet confirmed** — ask
  before reading/borrowing from it.

**Do not commit dataset video files or model weights to this repo.** `data/`, `*.mp4`, `*.pt`,
`*.pth`, `weights/`, `outputs/`, `synthetic/` are gitignored. Large artifacts stay in Drive/Kaggle
cache, not git. (Verified: no `.pt`/`.mp4`/`data.yaml` has ever been committed on any branch —
Vincent's checkpoints are `gdown`'d at runtime, not committed.)

### Current branch ownership
| Branch | Owner | What |
|---|---|---|
| `sam_model_vincent` | Vincent | Soccer artifact (Roboflow `sports` toolkit) — base of truth, don't push directly |
| `basketball` | (this task) | Basketball pivot, branched off `sam_model_vincent` |
| `feat/tracking-ashmeet` | Ashmeet | Separate SoccerTrack-v2 line; `yolo_backend.py` is the reusable piece |
| `feat/pitch-eval-shaaz` | Shaaz | Training notebook (25+10 epoch) — not yet inspected for basketball relevance |
| `feat/events-demo-dawood` | Dawood | No work yet |

---

## 2. Environment & secrets

- **Compute:** all model code runs in Google Colab (GPU). Notebooks mount Drive, pull data via
  Kaggle/`kagglehub`, save weights/outputs back to Drive and/or the repo. Don't assume a local GPU.
- **Config:** keep paths, dataset IDs, and sponsor keys out of hardcoded strings — prefer a single
  config source (`config.yaml`/`src/config.py` pattern from the soccer line, or equivalent) as the
  basketball pipeline takes shape.
- **Secrets:** all API keys (Kaggle, Pika, Redis, Arize, Anthropic) load from `.env` via
  `python-dotenv`, or from Colab secrets (`google.colab.userdata`) inside notebooks. **`.env` is
  gitignored — never commit keys.** Keep `.env.example` listing required variable names with empty
  values.

---

## 3. Verified model facts (corrected — do not assume YOLOv5/custom-trained)

> Corrected 2026-06-21 by reading `sam_model_vincent`'s actual notebooks/files — see
> `ONBOARDING.md` §2 for the full derivation.

- **Vincent's soccer detector is NOT a custom-trained YOLOv5 model.** It's
  [Roboflow's `sports`](https://github.com/roboflow/sports) example pipeline running **3
  separate pretrained checkpoints** (`football-ball-detection.pt`, `football-player-detection.pt`,
  `football-pitch-detection.pt`, ~137–140MB each, Ultralytics-compatible, pinned
  `ultralytics==8.2.0`/`>=8.3.0`), downloaded via `gdown` from Roboflow's own Drive links — never
  committed to git, never trained by Vincent.
- **No `best.pt`, no `data.yaml`, no training step exists anywhere in this pipeline.** It is
  100% pretrained-checkpoint inference.
- **`sports/examples/soccer/main.py` supports 6 modes** (confirmed in source):
  `PITCH_DETECTION`, `PLAYER_DETECTION`, `BALL_DETECTION`, `PLAYER_TRACKING`,
  `TEAM_CLASSIFICATION`, `RADAR`.
- **Team classification works and is sport-agnostic:** `sports/sports/common/team.py` uses SigLIP
  embeddings + UMAP + KMeans on player crops — directly reusable for basketball.
- **Pitch/radar features are soccer-specific** (`sports/sports/configs/soccer.py` bakes in pitch
  geometry) — **do not expect these to transfer to basketball** without a basketball court
  config, which doesn't exist yet.
- **SAM 3.1 is gated and was a dead end for both Vincent and us.** `facebook/sam3` on Hugging
  Face requires approved access (slow/uncertain) AND `transformers` from git main (the stable
  wheel is missing `Sam3ImageProcessor`). Don't reach for SAM 3.1 for basketball — use a
  pretrained detector instead (Path A).
- **Basketball-51** (`sarbagyashakya/basketball-51-dataset` on Kaggle): 10,311 six-second
  action-recognition clips, labeled ONLY by shot outcome (2pt/3pt/FT/mid × make/miss). **No
  player/ball bounding boxes.** Low-res 320×240. Cannot train a detector directly on it — see §4.

---

## 4. The Basketball-51 label gap — read before writing training code

Basketball-51 has no detection labels, so:
- **Path A (do this first, no training):** run an existing pretrained `person`+`sports ball`
  detector (Ultralytics YOLO via COCO classes is the proven, ungated, free option — see
  `feat/tracking-ashmeet`'s `src/model/yolo_backend.py`) + ByteTrack on selected Basketball-51
  clips. Produces an annotated demo video with zero training. Priority deliverable.
- **Path B (after A, if time allows):** fine-tune from a *separately sourced labeled* basketball
  detection set (e.g. a Roboflow basketball dataset, or pseudo-labeled Basketball-51 frames +
  hand review). Needs a real `data.yaml`. Only do this once Path A works.
- Pick cleaner/higher-quality Basketball-51 clips; 320×240 looks rough on a big screen — consider
  upscaling or just picking visually clean clips for the demo.
- **If the dataset or Kaggle access is missing when you need it, STOP and ask — do not fabricate
  data or assume credentials exist.** (As of this writing, no `~/.kaggle/kaggle.json` exists on
  this machine.)

---

## 5. Sponsor integrations (Redis, Pika Labs, Arize — document each clearly for judges)

Each integration lives in its own module, is **toggleable via config**, and never sits on the
critical path (pipeline still runs with all three off).

- **Redis** (`src/store/`): live state + speed. Cache latest per-track positions; push tracking
  results via Streams/pub-sub to a demo dashboard; optionally cache inference results keyed by
  frame hash. Currently a no-op stub (`src/store/redis_store.py`) inherited from the soccer scaffold
  — needs real wiring for basketball.
- **Pika Labs** (net-new — nothing exists yet): generate synthetic basketball imagery (courts,
  jerseys, lighting, angles) to augment training data for Path B; secondary use — polished
  demo/intro visuals. Keep generated assets in a clearly labeled `synthetic/` folder, separate
  from real data, and flag which `data.yaml` splits include synthetic images.
- **Arize** (`src/obs/`): log per-detection class, confidence, tracked-agent count, track
  stability over time; surface drift signals (soccer-trained vs basketball-trained, real vs
  synthetic-augmented). Currently a no-op stub (`src/obs/arize.py`) — needs real wiring.
- **Anthropic / Claude Code** (meta): the build + orchestration layer for this whole project.

**Adding a sponsor pattern:** create `src/<area>/<sponsor>.py`, expose one `init(config)` + one
integration function, register behind a config flag, document it here and in `ONBOARDING.md`.

---

## 6. Git workflow — strict rules

- **Branch off `sam_model_vincent`** for basketball work (already done: `basketball` branch).
  It is the base of truth for the soccer artifact — never push to it directly without asking.
- **Never touch the old reference repo.** Read-only, if/when its path is confirmed.
- **Maintain `UPDATE.md` at the repo root, updated on every push.** Append (never overwrite) a
  dated entry with: What changed / Current state / How to run it right now / Next step / Blocked
  on. Treat this as part of the commit, not an afterthought.
- **Small, working, clearly-messaged commits.** Push the working branch regularly.
- **No destructive git operations** (force-push, branch delete, history rewrite) without asking
  first.
- **Never fabricate data, weights, or eval numbers.** If something's missing (dataset, credentials,
  a notebook), stop and ask — don't guess or invent a placeholder that looks real.

---

## 7. Phases

**Phase 0 — Orientation & ground truth** (this phase). Branch map, model facts verified against
real files (not assumptions), `ONBOARDING.md` + initial `UPDATE.md`, this `CLAUDE.md` draft.
No training yet.

**Phase 1 — Basketball demo video (Path A).** Pull Basketball-51 (needs Kaggle creds), run an
existing pretrained detector + ByteTrack on a few clean clips, produce one annotated basketball
tracking video in the style of Vincent's soccer demo. Priority deliverable.

**Phase 2 — Basketball detection data (Path B prep).** Source/build a *labeled* basketball
detection set (Basketball-51 itself has no labels). Build `data.yaml`, sanity-check, split
train/val. Halt-and-ask if blocked.

**Phase 3 — Train basketball model.** Fine-tune from a pretrained checkpoint → `weights/basketball_best.pt`,
log real metrics, re-run tracking for a sharper demo video.

**Phase 4 — Sponsor wiring.** Pika Labs synthetic augmentation, Redis live state/streaming, Arize
observability — each independently demoable.

**Phase 5 — Agentic layer + polish.** Build the agentic analysis layer (Arize-driven) on top,
end-to-end demo, and a one-paragraph "how this qualifies for each sponsor track" writeup in
`UPDATE.md`.

---

## 8. What "done" looks like for Phase 1

One command (or one Colab run) that: loads a Basketball-51 clip → tracks every player + the ball
with a pretrained detector + ByteTrack → saves an annotated output video, matching the visual
style of Vincent's soccer demo. Everything in §4 Path B and §5 is bonus on top of this.
