# AGENT TASKS — multi-agent coordination (Claude = lead, Codex 5.5 Max = secondary)

**If you are Codex (or any agent) picking this up: read this file fully, then `CLAUDE.md` and
`ONBOARDING.md`, then `UPDATE.md`'s most recent entries, in that order, before touching anything.**
You're on branch `basketball`. `git pull` before you start and before every push — Claude (lead)
and the user are also pushing to this branch.

Phase list extended from CLAUDE.md's original 0–5 to 0–8 (the user asked for "all the way to
phase 8"; 6–8 are a proposed extension, not yet confirmed — flag to the user if you think these
are wrong):

| # | Phase | Owner | Status |
|---|---|---|---|
| 0 | Orientation & ground truth | Claude | ✅ done |
| 1 | Basketball demo video (Path A) | Claude | ✅ code done, GPU validation pending |
| 2 | Basketball detection data (Path B prep) | Claude | ✅ scaffolded, download pending |
| 3 | Train basketball model | **Codex** | 🟡 reproducible code/Colab ready; credentials + GPU run pending |
| 4 | Sponsor wiring (Redis, Pika Labs, Arize) | **Codex** | 🟡 wired/tested offline; hosted validation pending |
| 5 | Agentic layer + polish | **Codex** (+ Claude reviews) | 🟡 evidence-backed health agent ready; real-signal review pending |
| 6 | Cross-sport polish (soccer + basketball demo parity) | **Codex** | 🔲 not started |
| 7 | Devpost writeup + pitch prep | **Codex** (+ user content) | 🔲 not started |
| 8 | Final QA + submission rehearsal | shared | 🔲 not started |

---

## What's already done (Phase 0–2 — read before redoing any of this)

- **`sports/examples/basketball/main.py`** — Path A pipeline. One generic COCO detector
  (`yolo11n.pt`, ungated) + ByteTrack + `sports.common.team.TeamClassifier` (unmodified Roboflow
  code) + `sports.common.ball.BallTracker`. Modes: `PLAYER_DETECTION`, `BALL_DETECTION`,
  `PLAYER_TRACKING`, `TEAM_CLASSIFICATION`. See its own docstring + `README.md` next to it for
  exactly what's verified vs not.
- **Verified locally (Mac, CPU, synthetic test clip):** `PLAYER_TRACKING`/`PLAYER_DETECTION`/
  `BALL_DETECTION` run end-to-end, produce valid annotated video. `TEAM_CLASSIFICATION` hit a
  SIGSEGV in Roboflow's own `TeamClassifier.fit()` (UMAP/numba) on a **degenerate 1-frame-repeated
  test clip** — almost certainly a tiny-sample artifact, not a real bug, but **NOT YET confirmed on
  real multi-frame footage**. First thing to check if you get GPU/Colab access.
- **`Basketball_1.ipynb`** (repo root) — the Colab notebook to actually run Phase 1 for real:
  GPU check → clone this repo → install → `kagglehub.dataset_download(...)` for Basketball-51 →
  pick a clip → run all 4 modes → render+preview. **Needs the user's Kaggle auth in Colab** — no
  Kaggle credentials exist outside Colab. If you have your own way to get Basketball-51 (or to run
  this notebook with GPU access), use it; otherwise this step may need the user to run it and
  report back the actual output (frame counts, any errors) in `UPDATE.md`.
- **`data.yaml`** (repo root) — Phase 2 template. Points at a **verified-real** Roboflow Universe
  dataset (`roboflow-jvuqo/basketball-player-detection-2`, 1.4k images, 94.6% mAP@50) as the Path-B
  labeled source, since Basketball-51 itself has no detection labels. **Not yet downloaded** —
  needs a free Roboflow API key (same credential-gating pattern as Kaggle; ask the user, see §3).

---

## Codex tasks (Phase 3–8) — pick up in this order, commit small, update `UPDATE.md` per push

### Phase 3 — Train basketball model (do this first if you have GPU + the data)
1. Get a Roboflow API key from the user (see "What I need from you" below) and download
   `basketball-player-detection-2` per the instructions in `data.yaml`'s header comment.
2. Fine-tune from `yolo11n.pt` (warm start — classes mostly overlap: `person`→`player` is the
   closest analog; don't expect a clean class-ID match, check the downloaded dataset's own
   generated `data.yaml` for the real names/order before training).
3. Save to `weights/basketball_best.pt` (gitignored — don't fight the `.gitignore`, that's correct).
4. Log real metrics (mAP, precision/recall) in `UPDATE.md` — **never fabricate a number**, say "not
   measured yet" if training hasn't finished.
5. Re-point `sports/examples/basketball/main.py`'s `BASKETBALL_DETECTION_MODEL` env var (or just
   set it when invoking) at the new checkpoint and re-run Phase 1's notebook modes for a sharper
   demo video. **Don't change the file's `DETECTION_MODEL_PATH` default** — keep `yolo11n.pt` as
   the zero-setup fallback; override via env var only.

### Phase 4 — Sponsor wiring (independent of Phase 3 — can run in parallel/first if no GPU yet)
Each integration: toggleable, off the critical path (pipeline still runs with all three off),
mirrors the existing stub pattern in `src/obs/` and `src/store/` (inherited from the soccer line —
read those files first, they're no-ops with the right shape already).
1. **Redis** (`src/store/redis_store.py`): cache latest per-track positions (track_id → x,y,
   team, timestamp); push updates via Streams or pub/sub for a live dashboard. Test against a
   local `redis-server` or a free Redis Cloud instance — ask the user for `REDIS_URL` if not
   already in `.env`.
2. **Arize** (`src/obs/arize.py`): log per-detection class/confidence, tracked-agent count, track
   stability (ID-swap rate) per frame/clip. Needs `ARIZE_API_KEY`/`ARIZE_SPACE_ID` from the user.
3. **Pika Labs** (net-new — no file exists yet, create `src/synthetic/pika.py` or similar):
   generate synthetic basketball imagery (courts/jerseys/lighting/angles) for Phase-3 data
   augmentation + demo visuals. Save to `/synthetic/` (gitignored — large generated images don't
   belong in git). Needs a Pika API key from the user — **does not exist in `.env.example` yet,
   add it there** (empty value, never the real key).
4. Update `.env.example` with any new variable names (empty values only).

### Phase 5 — Agentic layer + polish
Build the analysis layer on top of Arize's signals (e.g., an agent that watches drift/ID-swap
rate and narrates "the basketball model is less stable than soccer because X"). Scope this
loosely until Phase 3–4 give you real signals to build on — don't build this against fabricated
data.

### Phase 6 — Cross-sport polish
Soccer (`sports/examples/soccer/`) and basketball (`sports/examples/basketball/`) should look
like one coherent product, not two unrelated scripts. Consider: a single top-level runner that
takes `--sport {soccer,basketball}`, consistent annotator colors/styling, a side-by-side or
toggle demo view.

### Phase 7 — Devpost writeup + pitch prep
One paragraph per sponsor track (Redis, Pika Labs, Arize) on how this project qualifies — ground
it in what was ACTUALLY built (Phase 4), not aspirational claims. Compile the best demo clips
(soccer + basketball). This phase needs user input (team name, table number, etc.) — ask.

### Phase 8 — Final QA + submission rehearsal
Run the full pipeline end to end one more time from a clean checkout (catches "works on my
machine" bugs). Time the 5-minute pitch. Shared — loop the user in directly for this one.

---

## Rules (from `CLAUDE.md` §6 — repeating the ones that matter most for a second agent)

- **Never fabricate data, weights, or eval numbers.** If something's missing, stop and ask.
- **No destructive git ops** (force-push, branch delete, history rewrite) without asking first.
- **`UPDATE.md` gets an entry on every push** — append, never overwrite. Use the template at the
  top of that file. This is the ONLY way Claude (lead) and the user know what you did, since we
  don't share a live session — treat it as part of the commit, not an afterthought.
- **Don't touch `sam_model_vincent` or `main` directly.** Everything happens on `basketball`.
- **Pull before you push.** If you hit a merge conflict, resolve it carefully (don't blindly
  take "ours" or "theirs") — re-read both sides, same as Claude did for an earlier Vincent-branch
  conflict (see git log if curious: commit `9b084c2` on a different branch).
- **Small, frequent commits.** Don't batch a huge multi-phase commit — easier for everyone to
  follow `UPDATE.md` if commits map roughly 1:1 to tasks above.

---

## What I (the user) need to provide the secondary agent

Codex will need these directly in its own environment — **none of this goes in the repo** (all
gitignored / secrets):
1. **Roboflow API key** (free account at roboflow.com) — for Phase 3's dataset download.
2. **Redis connection** — either a `REDIS_URL` for a hosted instance, or confirm Codex should
   spin up a local `redis-server` for dev/demo purposes.
3. **Arize credentials** — `ARIZE_API_KEY` + `ARIZE_SPACE_ID`.
4. **Pika Labs API key** — for Phase 4's synthetic image generation.
5. **Confirm GPU access** — does Codex's environment have a GPU? If not, Phase 3 training and
   Phase 1's real-footage validation may still need to run in Colab with you driving, and Codex's
   role shifts to code-authoring + Phase 4/6/7 work that doesn't need a GPU.
6. **Confirm the Phase 6–8 extension above** is what you meant by "until phase 8" — I proposed it,
   didn't find it pre-defined anywhere.
