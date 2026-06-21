# UPDATE LOG

Running handoff log, updated on every push to this branch. **Append, never overwrite.**

---

## 2026-06-21 22:40 — basketball — (pre-commit, orientation only)
**What changed:** Created `basketball` branch off `origin/sam_model_vincent` @ `257bea4`. Wrote
`ONBOARDING.md` (full findings) and this initial `UPDATE.md`. No code, no training, no
destructive git ops. Did not touch `main`, `sam_model_vincent`, or any other branch.

**Current state / what works:**
- Vincent's soccer pipeline (`Soccer_1.ipynb` on `sam_model_vincent`) is **pretrained-checkpoint
  inference only** (Roboflow `sports` toolkit, 3 gdown'd `.pt` files) — not a custom-trained
  model. No `best.pt`/`data.yaml`/`soccer_1_cv.mp4` exist anywhere in this repo's git history.
- Basketball: **nothing exists yet** — no notebook, no dataset, no Kaggle credentials on this
  machine. Per the kickoff prompt's own rule, stopping rather than fabricating.
- `feat/tracking-ashmeet` (a sibling soccer-tracking effort) independently hit the same SAM 3.1
  gating wall Vincent did and pivoted to Ultralytics YOLO + ByteTrack — verified working on a
  Colab T4. Not yet merged anywhere; flagged as a possible reusable piece for basketball Path A.

**How to run it right now:** Nothing to run yet — orientation only. To inspect what Vincent
built: `git checkout sam_model_vincent` then open `Soccer_1.ipynb` in Colab (needs Drive/gdown
access for the 3 pretrained checkpoints, ~140MB each; no HF token needed for this notebook —
only `segment_videos_with_segment_anything_3.ipynb` needs the gated SAM3 token).

**Next step for whoever picks this up:** Resolve the 5 open questions in `ONBOARDING.md` §9
(Kaggle creds, old-repo path, demo video location, detector-stack decision, go-ahead) before
writing any basketball code. Once resolved: Phase 1 is "run an existing pretrained
person+ball detector + ByteTrack on a few Basketball-51 clips" (Path A, no training).

**Blocked on / open questions:**
1. Kaggle API credentials to pull `sarbagyashakya/basketball-51-dataset`.
2. Exact path to "the old repo" referenced in the kickoff prompt (CLAUDE.md conventions to borrow).
3. Location of the `soccer_1_cv.mp4` demo video (not in git — Drive? Slack? or just the notebook's inline preview?).
4. Decision: reuse Roboflow's `sports` toolkit directly for basketball, or wrap it (+ `yolo_backend.py`) behind our `SamBackend` interface?
5. Go-ahead to start Phase 1 (Basketball-51 + existing detector + ByteTrack demo video).

---

## 2026-06-21 23:10 — basketball — (Phase 0 complete, committing)
**What changed:** Resolved 3 of the 5 open questions above; finalized `CLAUDE.md` (shown as a
diff before committing, per instruction) with the basketball-pivot rewrite. Committing
`ONBOARDING.md`, `UPDATE.md`, `CLAUDE.md` to `basketball` and pushing for the first time.

**Current state / what works:** Phase 0 orientation complete and accurate (see `ONBOARDING.md`
for full derivation). No basketball code/data/training yet — that's Phase 1, pending final
go-ahead.

**Resolutions:**
1. **Kaggle access** — `kagglehub.dataset_download("sarbagyashakya/basketball-51-dataset")`, run
   in the Colab notebook (Kaggle auth works there; none configured on the local dev machine).
2. **"Old repo"** = this repo's own prior `CLAUDE.md` (the SoccerTrack-v2/SAM3 doc) — not a
   separate project. Folded its environment/secrets + branch-ownership conventions into the new one.
4. **Detector stack** — DECIDED: Roboflow's `sports` toolkit directly, no `SamBackend` wrapping.
   Caveat flagged and accepted: swap in a generic COCO `person`/`sports ball` detector for Path A
   instead of Roboflow's soccer-specific `football-player-detection.pt`/`football-ball-detection.pt`
   (domain mismatch risk), reusing `sports/sports/common/team.py` as-is for team classification.

**How to run it right now:** Still nothing to run — Phase 0 is docs-only. Next runnable thing is
Phase 1: pull Basketball-51 via `kagglehub` in Colab, run a generic detector + ByteTrack through
Roboflow's `sports` runner pattern on a few clean clips, render one annotated demo video.

**Next step for whoever picks this up:** Get explicit go-ahead, then start Phase 1 exactly as
scoped in `CLAUDE.md` §7/§8 — no further blockers identified.

**Blocked on / open questions:**
1. `soccer_1_cv.mp4` location — still unresolved, not blocking.
2. Go-ahead to start Phase 1.

---

## 2026-06-21 23:55 — basketball — Phase 1 + 2 executed; multi-agent handoff set up

**What changed:** Got go-ahead. Executed Phase 1 (basketball demo pipeline) and Phase 2 (detection
data scaffold). Created `AGENT_TASKS.md` — coordination doc for a second agent (Codex 5.5 Max)
joining on this same branch, since user asked me to lead and hand off Phases 3–8.

**Phase 1 — what was built and verified:**
- `sports/examples/basketball/main.py`: adapted from the soccer script. Key difference: ONE
  generic COCO-pretrained model (`yolo11n.pt`, ungated, auto-downloads) instead of soccer's 3
  sport-specific checkpoints — no basketball-specific model/labels exist. 4 modes
  (`PLAYER_DETECTION`, `BALL_DETECTION`, `PLAYER_TRACKING`, `TEAM_CLASSIFICATION`). No pitch/radar
  mode — no basketball court keypoint model exists.
- **Verified locally** (Mac, CPU, synthetic 15-frame test clip built from a real photo with
  people, using the real `ultralytics`/`supervision`/`sports` packages, not mocks):
  `PLAYER_DETECTION`/`BALL_DETECTION`/`PLAYER_TRACKING` ran end-to-end → valid annotated mp4
  (confirmed readable, correct frame count/dimensions, real annotation pixels present).
  `TEAM_CLASSIFICATION` SIGSEGV'd inside Roboflow's **unmodified** `TeamClassifier.fit()`
  (UMAP/numba) — traced to the test clip being degenerate (1 unique frame repeated 15x → near-
  duplicate crops, `n_neighbors larger than dataset size` warning right before the crash). This is
  a known small-sample UMAP/numba fragility, not a logic bug in the new code, but **genuinely not
  yet confirmed on real diverse footage** — first thing to check on Colab.
- `Basketball_1.ipynb` (repo root): the real run — GPU check, clone+install, `kagglehub` pull of
  Basketball-51 (needs the user's Kaggle auth — not available outside Colab), clip selection, all
  4 modes, H.264 preview. **Not yet executed for real** (no local Kaggle/GPU access) — this is the
  next concrete action for whoever has Colab access (user or Codex).

**Phase 2 — what was built:**
- `data.yaml` (repo root): Path-B template. Points at a **verified-real** Roboflow Universe
  dataset, `roboflow-jvuqo/basketball-player-detection-2` (1.4k images, 94.6% mAP@50, classes incl.
  plain ball/player/referee/number + action sub-classes) — found via live web search, not guessed.
  Download needs a free Roboflow API key (same gating pattern as Kaggle) — not yet pulled.
- Fixed a real `.gitignore` gap: `/runs/` and `/synthetic/` were referenced in `CLAUDE.md` as
  gitignored but weren't actually in `.gitignore` — added them.

**Multi-agent setup:** `AGENT_TASKS.md` created — full Phase 3–8 task breakdown, explicit
ownership (Codex: Phases 3–8; Claude: reviews + Phase 1/2 follow-up), file/directory boundaries to
avoid conflicts, and a list of credentials the user needs to hand Codex directly (Roboflow API
key, Redis URL, Arize creds, Pika Labs key — none of this goes in the repo). **Flagged to the
user:** the original phase list only went to 5; Phases 6–8 (cross-sport polish, Devpost writeup,
final QA) are a proposed extension, not pre-confirmed.

**How to run it right now:**
```bash
git checkout basketball && git pull
# Local CPU smoke test (no GPU/dataset needed, mirrors what was already verified):
cd sports && pip install -e . && pip install -r examples/basketball/requirements.txt \
  supervision umap-learn scikit-learn tqdm
cd examples/basketball
python main.py --source_video_path <any.mp4> --target_video_path out.mp4 \
  --device cpu --mode PLAYER_TRACKING
# Real run (needs GPU + Kaggle auth): open Basketball_1.ipynb in Colab, Run all.
```

**Next step for whoever picks this up:** If you're Codex — read `AGENT_TASKS.md` in full, start
on Phase 3 or 4 (whichever fits your environment — see that doc's "what I need from you" section
for the credential-availability decision tree). If you're the user — run `Basketball_1.ipynb` in
Colab when you get a chance and paste the real output (or errors) back; that's the one thing
neither agent can self-verify without your Kaggle/Colab access.

**Blocked on / open questions:**
1. Real GPU/Colab run of `Basketball_1.ipynb` — needs the user.
2. Roboflow API key for Phase 3's dataset download — needs the user.
3. Redis/Arize/Pika Labs credentials for Phase 4 — needs the user, see `AGENT_TASKS.md`.
4. Confirm the Phase 6–8 extension is what was meant by "until phase 8."
5. `soccer_1_cv.mp4` location — still unresolved, still not blocking.
