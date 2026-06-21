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

---

## 2026-06-22 00:05 — basketball — Codex handoff prompt finalized

**What changed:** Wrote the actual kickoff prompt for Codex 5.5 Max (the secondary agent) and
gave it to the user to paste into a Codex session. No repo changes beyond this log entry — the
prompt itself isn't a file, it's what initializes Codex's cold session, pointing it at this repo,
branch `basketball`, and — in order — `AGENT_TASKS.md`, `CLAUDE.md`, `ONBOARDING.md`, `UPDATE.md`.

**Current state / what works:** Same as the entry above — Phase 0–2 done, Phase 3–8 assigned to
Codex in `AGENT_TASKS.md`. This entry exists so anyone reading the log later knows exactly when
Codex was actually kicked off, separate from when the coordination docs were written.

**Next step for whoever picks this up:** If you're Codex reading this because you just started —
welcome, see `AGENT_TASKS.md` for your actual task list. If you're Claude or the user checking in
later — look for a NEW entry below this one from Codex; if there isn't one yet, Codex hasn't
pushed anything since this handoff.

**Blocked on / open questions:** Same five as the entry above — none resolved by this entry
alone, it's just the handoff marker.

---

## 2026-06-21 — basketball — Phase 4 Redis implementation (Codex)

**What changed:** Replaced the Redis no-op with a disabled-by-default live-state adapter.
Tracked positions are written to a latest-state hash and a bounded Redis Stream; the legacy
track-embedding API now has portable hash storage and cosine search without requiring
RediSearch. Added TTL/key-prefix/stream-size environment settings and protocol-level tests with
an in-memory fake. Also corrected an existing bare-checkout test so the data-dependent replay
factory skips when SoccerTrack data is absent.

**Current state / what works:** Redis behavior is fully unit-tested without external services.
The complete local suite is `21 passed, 2 skipped`; Ruff is clean. Sponsor-off mode remains a
safe no-op. No claim is made about a hosted Redis connection because no `REDIS_URL` or local
`redis-server` is available in Codex's environment.

**How to run it right now:** Set `sponsors.redis: true`, copy `.env.example` to `.env`, set a real
`REDIS_URL`, then call `src.store.redis_store.init(cfg)`. Publish via
`publish_track_position(...)`/`publish_positions(...)`; dashboards read the
`sports:tracks:basketball:latest` hash and consume `sports:tracks:basketball:stream`.

**Next step for whoever picks this up:** Wire per-frame player foot positions from the
basketball runner into `publish_positions`, then validate against a real Redis instance and
record only observed behavior.

**Blocked on / open questions:** Live validation needs `REDIS_URL`. Phase 3 still needs a GPU
and `ROBOFLOW_API_KEY`. Phase 6–8 scope still needs user confirmation.

---

## 2026-06-21 — basketball — Phase 4 Arize implementation (Codex)

**What changed:** Replaced the Arize no-op with an adapter for the current official `arize`
8.35 streaming ML API. Detection records log class/confidence plus track/frame context; a
separate tracker-health model logs ID-swap rate with per-frame counts and mean confidence.
Asynchronous sends are bounded and explicitly flushed. Added validation dataclasses, safe
disabled/error behavior, SDK-protocol tests, optional model-name environment settings, and pinned
the runtime dependency to the compatible v8 range.

**Current state / what works:** The adapter imports and its exact `log_stream` argument shape are
tested against the installed Arize 8.35 SDK without making network calls. Complete suite:
`25 passed, 2 skipped`; Ruff clean. No hosted telemetry or dashboard result is claimed because
no Arize credentials are available in this environment.

**How to run it right now:** Set `sponsors.arize: true`, configure `ARIZE_API_KEY` and
`ARIZE_SPACE_ID` in `.env`, call `src.obs.arize.init(cfg)`, log `DetectionTelemetry` and
`FrameTelemetry` records, then call `flush()`/`close()` at clip completion.

**Next step for whoever picks this up:** Wire these calls into the basketball runner, calculate
observed ID-swap rate from frame-to-frame assignments, and validate in a real Arize Space.

**Blocked on / open questions:** Hosted validation needs `ARIZE_API_KEY` and `ARIZE_SPACE_ID`.
Phase 3 still needs GPU + Roboflow credentials. Phase 6–8 remains unconfirmed.

---

## 2026-06-21 — basketball — Phase 4 Pika integration (Codex)

**What changed:** Added a disabled-by-default client for Pika's documented direct Developer API.
It submits Turbo text-to-video or image-to-video jobs, polls the documented video endpoint,
downloads completed media without forwarding the API key to the media host, and records a JSONL
provenance manifest. Added a CLI, optional ffmpeg review-frame extraction, sponsor config/env
plumbing, official-endpoint documentation, and fake-session tests that spend no API credits.

**Current state / what works:** The request, polling, download, and manifest lifecycle is covered
by local tests. Generated assets remain under the gitignored `synthetic/` tree. Every new manifest
record is explicitly `synthetic: true`, `reviewed: false`, `annotated: false`, and
`eligible_for_training: false`; Pika supplies media, not detection labels, so no generated frame
is silently added to `data.yaml`. Full suite: 30 passed, 2 data-dependent skips; Ruff clean.

**Verified external contract:** Pika's official direct docs currently specify
`POST /generate/turbo/t2v`, `POST /generate/turbo/i2v`, `GET /videos/{video_id}`, and
`X-API-KEY` authentication. Direct API access is partner-gated; Pika's public API page also points
general users to fal.ai. This implementation uses only the documented direct API because the
project requirement calls for a Pika API key.

**How to run it:** Put `PIKA_API_KEY` in `.env`, set `sponsors.pika: true`, then follow
`docs/PIKA.md`. Example: `python -m src.synthetic.pika --prompt "broadcast basketball game under
uneven arena lighting" --extract-fps 1`.

**Next step:** With a real Pika partner key, submit one bounded job, inspect the real response and
downloaded output, then manually review/annotate any frames intended for Phase 3 augmentation.

**Blocked on / open questions:** Live validation needs `PIKA_API_KEY` and direct Developer API
access. Phase 3 still needs a GPU and `ROBOFLOW_API_KEY`. Phase 6–8 scope still needs user
confirmation.

---

## 2026-06-21 — basketball — Phase 4 sponsor runtime wiring (Codex)

**What changed:** Added a dependency-light tracking observer that fans real basketball detections
out to the Redis and Arize adapters. All four Path-A modes now log actual model confidence;
tracked modes also publish ByteTrack foot positions, team assignments when available, agent
counts, and frame-to-frame track-set churn. The Colab install now makes the root package
importable, and direct script execution resolves both vendored package roots.

**Metric correction:** Path A has no identity ground truth, so a true ID-swap rate cannot be
measured honestly. The runtime records exact new/lost track counts and their observed churn rate,
tagged as `track_churn_rate`. Arize still accepts a separately computed `id_swap_rate` when a
future evaluator supplies one, but the two metrics are not conflated.

**Current state / what works:** Sponsor-off behavior remains a no-op and all basketball CLI modes
still load. Observer fan-out and metric labeling are tested with no external services. Complete
suite: 34 passed, 2 data-dependent skips; Ruff, Python compilation, notebook JSON validation, and
`main.py --help` are clean. No hosted Redis/Arize success is claimed without credentials.

**How to run it:** Use the existing basketball command. To enable integrations, set the desired
`sponsors.redis`/`sponsors.arize` flags in `config.yaml`, populate the matching root `.env`
credentials, and install the optional clients as documented in
`sports/examples/basketball/README.md`.

**Next step:** Validate one short real clip against hosted Redis and Arize, then inspect the exact
stored stream/telemetry records. Vincent's newly pushed possession and movement-trail modules were
also reviewed from `sam_model_vincent`; they are useful inputs for the next basketball analytics
task but were not copied blindly into this sponsor-wiring commit.

**Blocked on / open questions:** Hosted checks need `REDIS_URL`,
`ARIZE_API_KEY`/`ARIZE_SPACE_ID`. Phase 3 still needs GPU + `ROBOFLOW_API_KEY`. Phase 6–8
scope remains unconfirmed.
