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
