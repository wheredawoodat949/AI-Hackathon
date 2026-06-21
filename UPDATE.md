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

---

## 2026-06-21 — basketball — Possession + movement-trail demo mode (Codex)

**What changed:** Reviewed Vincent's latest `sam_model_vincent` commits after fetching them.
Ported the two sport-agnostic primitives from `c76c85d` (possession hysteresis and fading
movement trails) with attribution, validation, and tests. Added a basketball `POSSESSION` mode
that reuses the existing team-classification pass, overlays player trails, marks the estimated
holder, and draws an `EST. POSSESSION` HUD. Added a Colab run/preview cell for the enhanced
artifact.

**Scope correction:** Vincent's soccer implementation can measure distances after pitch
homography. Basketball currently has no court keypoint/homography model, so this adaptation uses
an explicitly documented 80-pixel radius and 20-pixel switch margin with temporal hysteresis.
The result is a demo heuristic, not ground truth, an evaluation metric, or a physical-distance
claim.

**Current state / what works:** Possession continuity/switching and trail draw/prune behavior are
covered by dependency-light tests. Complete suite: 38 passed, 2 data-dependent skips. Ruff,
Python compilation, notebook JSON, and CLI loading are clean. The real `POSSESSION` video has
not been rendered locally because this environment has no GPU or basketball clip/model artifact.

**How to run it:** In `Basketball_1.ipynb`, run through the team-classifier setup and then the
new enhanced-demo cells. CLI equivalent:
`python main.py --source_video_path <clip> --target_video_path <out> --device cuda --mode POSSESSION`.

**Next step:** Run the new mode on a diverse real Basketball-51 clip, verify the generic COCO ball
detection is sufficiently continuous for a useful HUD, and tune the documented pixel radius only
from observed output. Record actual results rather than assuming quality.

**Blocked on / open questions:** Real visual validation needs the user's Colab GPU + clip.
Phase 3 still needs `ROBOFLOW_API_KEY` and GPU compute. Hosted sponsor checks still need their
credentials. Phase 6–8 scope remains unconfirmed.

---

## 2026-06-21 — basketball — Phase 3 reproducible training workflow (Codex)

**What changed:** Added `src.training.basketball` with separate download, inspect, and train
commands plus `Basketball_Training.ipynb` for a Colab T4. The download command uses the
authenticated Roboflow SDK's real `project.versions()` result and selects the highest numeric
version (or a requested verified version), rather than filling the old `<latest>` placeholder.
It validates real split directories and the exact class map before training. The trainer enforces
CUDA by default, copies only an actually produced `best.pt`, and serializes only metrics returned
by Ultralytics.

**Runtime compatibility:** The basketball runner now accepts comma-separated
`BASKETBALL_PERSON_CLASS_IDS` and `BASKETBALL_BALL_CLASS_IDS`. This supports datasets whose
real class map includes multiple player/action classes without changing the zero-setup COCO
defaults. The inspector prints suggestions from explicit class names, but does not apply them
without review.

**Current state / what works:** Version selection, YAML/split validation, class-map suggestions,
download orchestration, real checkpoint copying, and returned metric persistence are tested with
fakes. Complete suite: 43 passed, 2 data-dependent skips; Ruff, compilation, notebook JSON, and
CLI smoke checks are clean. The local inspect command correctly stops because
`data/basketball_det/data.yaml` does not exist. No dataset, checkpoint, or metric is claimed.

**How to run it:** Open `Basketball_Training.ipynb` on a Colab T4, store
`ROBOFLOW_API_KEY` as a private Colab secret, review the Universe dataset's current license,
then run the cells. CLI details and artifact paths are in `docs/TRAINING_BASKETBALL.md`.

**Next step:** Perform the real authenticated download, review the printed class map, run
training, copy the resulting checkpoint/summary to Drive, and append the actual metrics here.
Then set the printed runtime class IDs and render the real `POSSESSION` mode.

**Blocked on / open questions:** Execution now immediately needs `ROBOFLOW_API_KEY` and the
user's Colab GPU. Hosted Redis/Arize/Pika validation still needs credentials. Phase 6–8 scope
remains unconfirmed.

---

## 2026-06-21 — basketball — Phase 5 evidence-backed health agent (Codex)

**What changed:** Added a local `TrackingHealthAgent` that consumes the exact frame summaries
sent to Arize. It records observed counts/confidence/churn, emits rolling threshold events with
the frame window/value/threshold, and writes a factual JSON report when
`TRACKING_ANALYSIS_OUTPUT` is configured. `Basketball_1.ipynb` now enables a local report and
prints the narrative/evidence after the enhanced demo run.

**Guardrails:** The agent explicitly states that track-set churn is not confirmed ID swaps,
lists entry/exit and fragmentation only as possibilities, and labels low-confidence/high-churn
overlap as coincidence rather than causation. It embeds no baseline or cross-sport comparison;
those claims require real reports from both runs.

**Current state / what works:** Thresholding, cooldown, evidence, report serialization, empty
input, ordering validation, and observer lifecycle integration are tested. Complete suite:
48 passed, 2 data-dependent skips; Ruff, compilation, notebook JSON, and diff checks are clean.
No real run narrative is claimed because no basketball footage was processed in this environment.

**How to run it:** Set
`TRACKING_ANALYSIS_OUTPUT=outputs/basketball_tracking_health.json` and run any basketball mode,
or run the updated `Basketball_1.ipynb`. Interpretation details are in
`docs/TRACKING_HEALTH.md`.

**Next step:** Generate a report from a real clip, review threshold events alongside the video
and Arize dashboard, and tune thresholds only from observed behavior. A soccer/basketball
comparison can be added after both real reports exist.

**Blocked on / open questions:** The remaining immediate work needs user-controlled resources:
Roboflow + GPU for Phase 3, hosted sponsor credentials for live Phase 4 validation, and a decision
on whether to proceed with the proposed Phase 6–8 extension.

---

## 2026-06-21 — basketball — Flag football demo + minimal frontend (deadline pass, Claude)

**Context:** User had ~30 min left. Deferred all live Redis/Arize/Pika validation, Phase 3
training, and Roboflow access per their explicit instruction. Priority: flag football demo
video → frontend with both sports playable.

**No frontend was found.** Searched this checkout (`frontend/` had only `.gitkeep`, no
`package.json` anywhere in the repo) and the broader filesystem (`~/Documents`, `~/Downloads`)
for any recently-modified frontend project — found none. Built a minimal one from scratch
(`frontend/index.html`) since it was genuinely missing, not because the existing one (if it
exists somewhere outside this checkout/this agent's reach) was disregarded.

**Flag football — exact facts:**
- **Input:** the file attached as `~/Downloads/Screen Recording 2026-06-21 at 11.20.28 AM.mov`
  is misleadingly named — its actual content is real flag-football broadcast footage (USA vs
  Italy, "The World Games", Birmingham AL), confirmed by extracting and viewing frames before
  processing. No separate URL was provided or needed.
- **Clip duration used:** full 8.02s source (`ffprobe`-confirmed), no trimming needed (already
  under the suggested 10–15s window). Re-encoded: `ffmpeg -i <raw> -vf "fps=15,scale=-2:720" -an
  -c:v libx264 -preset veryfast <clip.mp4>` → 1280x720, 15fps, 120 frames, H.264.
  (Original source was 1280x720 @ 120fps — downsampled to 15fps so CPU inference would finish in
  the time available; this was a deliberate quality/speed tradeoff, not a default.)
- **Command run:** `python sports/examples/flag_football/main.py --source_video_path
  <clip.mp4> --target_video_path <out.mp4> --device cpu --mode PLAYER_TRACKING`
  (new file, copied from the basketball script — identical generic-COCO-detector logic, person
  class 0 only used for this run; ball class 32 wired but not separately verified for the
  American football's shape). Runtime: **~6 seconds** for 120 frames on CPU (no GPU on this
  machine). `yolo11n.pt` auto-downloaded (ungated, 5.4MB).
- **Result:** exit code 0. Output verified by extracting and viewing 4 frames spread across the
  clip — real ellipse annotations with ByteTrack IDs correctly positioned under detected players
  in multiple frames (not just one lucky frame). Transcoded for the frontend: `ffmpeg -i
  <tracked.mp4> -c:v libx264 -pix_fmt yuv420p -movflags +faststart -an
  outputs/flag_football_tracking_h264.mp4` — confirmed via `ffprobe`: `codec_name=h264,
  width=1280, height=720, pix_fmt=yuv420p`.
- **Ball detection:** NOT separately verified as useful for this clip — only `PLAYER_TRACKING`
  mode was run (the explicit minimum-acceptable bar). Per instruction, did not invent ball
  locations.
- **TEAM_CLASSIFICATION/POSSESSION:** not run for flag football — out of scope for this pass
  (player tracking was the stated priority; these modes are inherited from the basketball script
  unchanged and untested here).

**Basketball — exact facts:**
- Did **not** re-run the model on `~/Downloads/download.mp4` (correctly identified as an
  *already-annotated* output, not raw input — would have contaminated inference, per instruction).
- Did **not** locate the original raw basketball source clip in the time available.
- Per the explicit fallback instruction, copied `download.mp4` as-is into
  `outputs/basketball_tracking_h264.mp4` for the frontend. **This is the existing generated
  artifact, not a new inference run.** `ffprobe` confirms it's already `h264`/`yuv420p`/320x240
  — no transcode needed. Documenting clearly: **this video's actual tracking quality/provenance
  predates this session and was not evaluated here.**
- The improved basketball pipeline (re-running `sports/examples/basketball/main.py` on a raw
  source) was **not executed** — no raw clip located, no GPU on this machine, and time ran out.
  This remains open (see below).

**Frontend — exact facts:**
- `frontend/index.html`: single static file, no build step, no framework. Two tab buttons
  (🏀 Basketball / 🏈 Flag Football) switch a single native `<video controls>` element's `src`
  between `outputs/basketball_tracking_h264.mp4` and `outputs/flag_football_tracking_h264.mp4`.
  Native controls give play/pause/scrub/fullscreen for free — no custom JS for those. Each tab
  shows a label clarifying what's actually playing (the basketball label explicitly says it's
  the pre-existing artifact).
- **Verified reachable**, not just "should work": ran `python3 -m http.server 8123` from the
  repo root, then `curl -o /dev/null -w '%{http_code}'` against
  `http://localhost:8123/frontend/index.html`,
  `http://localhost:8123/outputs/basketball_tracking_h264.mp4`, and
  `.../flag_football_tracking_h264.mp4` — **all three returned 200**. Did not load it in an
  actual browser (no browser-automation tool available in this environment) — HTTP-level
  verification only.
- **Startup command:** from the repo root, `python3 -m http.server 8123`, then open
  `http://localhost:8123/frontend/index.html` in a browser.

**Sponsor integrations:** untouched — left exactly as Codex built them (disabled by default,
code preserved, no new validation attempted), per instruction.

**Tests run:** `./.venv/bin/python -m pytest -q` → exit 0, all passed except 2 skips (consistent
with Codex's reported "data-dependent skips"). `python3 -m py_compile
sports/examples/flag_football/main.py` → clean. Did not run `ruff` in this pass (time).

**How to run it right now:**
```bash
# Frontend (both videos already generated and in outputs/):
python3 -m http.server 8123   # from repo root
# open http://localhost:8123/frontend/index.html

# Re-run flag football tracking from scratch:
ffmpeg -i <raw_flag_football.mov> -vf "fps=15,scale=-2:720" -an -c:v libx264 -preset veryfast clip.mp4
python sports/examples/flag_football/main.py --source_video_path clip.mp4 \
  --target_video_path tracked.mp4 --device cpu --mode PLAYER_TRACKING
ffmpeg -i tracked.mp4 -c:v libx264 -pix_fmt yuv420p -movflags +faststart -an out_h264.mp4
```

**Next step for whoever picks this up:**
1. Find the **original raw basketball clip** (not `download.mp4`) and re-run
   `sports/examples/basketball/main.py` on it for a real, current basketball artifact —
   `outputs/basketball_tracking_h264.mp4` currently holds a pre-existing artifact, not a fresh run.
2. If a GPU becomes available, re-run flag football at full 120fps/no downsampling for a smoother
   result, and try `TEAM_CLASSIFICATION`/`POSSESSION` modes on the flag-football clip.
3. Load `frontend/index.html` in an actual browser (only HTTP-level reachability was verified
   here, not visual/interactive correctness) and confirm playback, tab-switching, fullscreen.
4. `ruff check` wasn't run this pass — worth a quick pass before the next commit.

**Blocked on / open questions:**
1. Original raw basketball source clip — not located.
2. No GPU available in this environment — flag football ran on CPU at reduced frame rate.
3. Frontend not visually verified in a real browser (HTTP 200s confirmed, rendering not).
4. Phase 3 (Roboflow + GPU), Phase 4 live validation (Redis/Arize/Pika creds), Phase 6–8
   confirmation — all still open from before, untouched this pass per instruction.
