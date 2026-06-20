# CLAUDE.md

> Project context for Claude Code. Read this fully before doing anything. When in doubt, prefer the **simplest thing that produces a visible result**, then iterate. We are on a 24-hour hackathon clock.

---

## 0. TL;DR for Claude

We are building a **soccer game-state analysis pipeline**: take full-pitch panoramic match video, run **Meta SAM 3.1** to segment + track every player/goalkeeper/referee, and produce a live **2D tactical minimap** plus event analysis. We evaluate our tracker against ground-truth annotations and instrument the whole thing for reliability and observability.

- **Core model:** Meta SAM 3.1 (Promptable Concept Segmentation — text prompts like `"soccer player"` return masks + persistent IDs for *all* instances, with built-in video tracking).
- **Dataset:** SoccerTrack v2 — 10 full-length 4K panoramic matches with per-frame Game State Reconstruction (GSR) ground truth and Ball Action Spotting (BAS) labels.
- **Primary deliverable (now):** Python + Jupyter notebook that runs the pipeline on one match and saves output videos/minimaps.
- **Secondary deliverable (end):** a thin web frontend showing video + live minimap side-by-side. **Build everything so this bolt-on is easy — keep logic out of notebooks and in importable modules.**
- **Deadline reality:** Devpost draft due **Sunday 11 AM** (hard requirement to be judged), edits until 12 PM, judging 1–3 PM. A working narrow demo beats an ambitious broken one.

---

## 1. Repositories

- **Our project repo (work happens here):** https://github.com/wheredawoodat949/AI-Hackathon
- **Dataset repo (reference + loaders + eval scripts):** https://github.com/AtomScott/SoccerTrack-v2
- **Dataset homepage / docs:** https://atomscott.github.io/SoccerTrack-v2/
- **Dataset on Hugging Face (canonical download):** https://huggingface.co/datasets/atomscott/soccertrack-v2
- **Dataset paper:** https://arxiv.org/abs/2508.01802

**Do not commit dataset video files or model weights to our repo.** Add `data/`, `*.mp4`, `*.pt`, `*.pth`, `weights/`, `outputs/` to `.gitignore`. Large artifacts stay local on the GPU box.

---

## 2. Environment

- **Compute:** JupyterLab running inside VSCode, with GPU access. Assume CUDA is available; verify with `torch.cuda.is_available()` before any heavy run and FAIL LOUDLY if it's False.
- **Python:** use a virtual environment. Pin versions in `requirements.txt`.
- **Notebooks are for demoing and eyeballing, NOT for core logic.** All reusable logic lives in `src/` as importable modules. Notebooks import from `src/` and call functions. This is what makes the frontend bolt-on cheap later.
- Keep a single `config.yaml` (or `src/config.py`) for all paths, match IDs, prompt strings, and sponsor keys. No hardcoded paths scattered around.

### Secrets
- All API keys (SAM endpoint, Sentry DSN, Redis URL, Arize keys, Anthropic key) load from a `.env` file via `python-dotenv`. **`.env` is gitignored. Never commit keys.** Provide a committed `.env.example` listing required variable names with empty values.

---

## 3. Repository layout (create this in our repo)

```
.
├── CLAUDE.md                 # this file
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config.yaml
├── src/
│   ├── data/                 # SoccerTrack v2 loading + GSR/BAS parsing
│   │   ├── download.py
│   │   └── loader.py
│   ├── model/                # SAM 3.1 abstraction (see §4)
│   │   ├── sam_backend.py     # abstract interface
│   │   ├── sam_local.py       # self-hosted impl
│   │   └── sam_api.py         # hosted-API impl
│   ├── tracking/             # tracker wrapper, ID management
│   ├── pitch/                # homography → 2D pitch coords, minimap render
│   ├── events/               # BAS classification (stretch)
│   ├── eval/                 # HOTA + comparison vs GSR ground truth
│   ├── obs/                  # Sentry + Arize instrumentation
│   ├── store/                # Redis embedding store + semantic search
│   └── pipeline.py           # end-to-end orchestration entrypoint
├── notebooks/
│   └── demo.ipynb            # the thing we run for judges
├── outputs/                  # saved videos/minimaps (gitignored)
└── frontend/                 # empty for now; web app at the end
```

---

## 4. SAM 3.1 — model abstraction (IMPORTANT)

We do **not** yet know if we'll run SAM 3.1 self-hosted on our GPU or via a hosted API. **Build so it does not matter.**

- Define an abstract interface in `src/model/sam_backend.py`, e.g. a `SamBackend` protocol with methods like:
  - `track(video_path, prompts: list[str]) -> TrackResult` where `TrackResult` yields per-frame `{instance_id, mask, bbox, label}`.
- Provide two implementations behind the same interface: `sam_local.py` (self-hosted weights) and `sam_api.py` (hosted endpoint).
- A factory reads `config.yaml` (`sam_backend: local | api`) and returns the right one. **All downstream code depends only on the interface, never on a concrete backend.**
- Start with whichever is fastest to get a single working frame, then swap freely.
- Reference behavior: SAM 3.1 takes **text/noun-phrase prompts** (`"soccer player"`, `"goalkeeper"`, `"referee"`, `"sports ball"`) and returns masks + unique IDs for every matching instance, tracked across video frames. Note: inference cost scales linearly with number of tracked objects, and SAM 3.1 does NOT handle complex referring expressions — keep prompts to simple noun phrases.

---

## 5. Dataset facts Claude must respect

- **Do NOT download all 10 matches.** ~900 minutes of 4K is too much. Pull ONE match for dev using the repo's helper: `./scripts/download.sh --dest ./data --match <ID>`. Prefer a daytime match for cleaner demo visuals.
- **GSR annotations** (per frame): `track_id`, `player_id`, `role` (player/goalkeeper/referee/other), `jersey_number`, `team_side` (left/right/null), `x`,`y` (pitch coords in meters). **This is our tracking ground truth — wire eval against it from day one, not at the end.**
- **BAS annotations:** 12 action classes (Pass, Drive, Header, High Pass, Out, Cross, Throw In, Shot, Ball Player Block, Player Successful Tackle, Free Kick, Goal) with global timestamps + the acting player_id. This is the vocabulary for event detection AND for Redis semantic search.
- **MOT annotations** in MOTChallenge format (`gt/gt.txt`) for tracking eval.
- The repo ships **eval scripts**: `src.evaluation.gs_hota`, `src.evaluation.bas_map`, `src.evaluation.mot_hota`. Use the repo's HOTA implementation — do NOT reimplement metrics.
- Held-out test matches: 117099, 117100. Develop on others; never tune on the held-out set.
- License: dataset is CC BY 4.0 (attribution required, commercial OK); code is MIT. No player names in data — IDs are jersey-number based. Safe for a public Devpost.

---

## 6. Sponsor integrations (all 4 in scope; design for a cheap 5th)

Each integration lives in its own module and is **toggleable via config** so it can never break the core pipeline. Integrations consume pipeline output; they don't sit on the critical path.

- **Sentry** (`src/obs/`): error + performance monitoring. Alert on dropped frames, model timeouts, and tracker ID-swap events (detected by comparing ID continuity vs GSR). Reliability is judged — instrument from hour one, not bolted on.
- **Arize** (`src/obs/`): log every tracking/event prediction; build an eval set from GSR ground truth; show a measurable accuracy delta (HOTA) before/after any tuning. The number must be real and citable.
- **Redis** (`src/store/`): embed player track segments (appearance + trajectory) and store as vectors; semantic search keyed on BAS action vocabulary ("show every cross from the left", "find similar attacking sequences"). Must be "beyond caching" — vector search / retrieval.
- **Anthropic / Claude Code** (`meta`): Claude Code is our build + orchestration layer. Framing for the prize: accessible tactical analysis for amateur/university teams (the dataset is amateur matches) who can't afford pro analytics.

**Adding a sponsor pattern:** create `src/<area>/<sponsor>.py`, expose one `init(config)` and one integration function, register it behind a config flag, and document it here. Never let a new integration touch `pipeline.py`'s core path.

---

## 7. Working agreement for Claude Code

- **Commit small and often** with clear messages. One logical change per commit.
- **Branch per role/phase** (see the kickoff prompt's roles). Open PRs into `main`; don't push broken code to `main`.
- After each meaningful step, **run something and show the result** (a frame, a number, a saved clip). Visible progress > silent scaffolding.
- If a dependency or download stalls, **say so and propose a fallback** rather than waiting. (e.g., single-match download, lower-res proxy, fewer tracked classes.)
- **Never fabricate eval numbers.** If eval isn't wired yet, say "not measured yet."
- Keep a running `PROGRESS.md` with what works, what's stubbed, and the current demo command. Update it at the end of every phase.
- Respect the deadline ordering in §8. If behind, cut from the bottom (stretch) up — never cut Phase 0–2.
- Attribute the dataset (CC BY 4.0) in README and the Devpost.

---

## 8. Phases (priority order — do NOT skip ahead)

**Phase 0 — Foundation (everyone, first ~1–2h).** Repo scaffold per §3, `.gitignore`, `.env.example`, `config.yaml`, venv + `requirements.txt`, GPU check, single-match download kicked off in background, dataset loader reads one GSR frame and prints entities.

**Phase 1 — Core tracking (de-risk the hard thing).** SAM 3.1 backend abstraction + one working implementation; run text-prompted tracking on a short clip; save an annotated output video with masks + IDs. Success = a saved clip showing tracked players.

**Phase 2 — Pitch mapping + eval.** Homography from panoramic frame → 2D pitch coords; render the live minimap; wire HOTA eval vs GSR ground truth and print a real number. Success = minimap video + a HOTA score.

**Phase 3 — Sponsor layer.** Sentry instrumentation, Arize logging + before/after number, Redis embedding store + one working semantic query. Each behind a config flag.

**Phase 4 — Event analysis (stretch).** BAS classifier on the 12 classes; feed events into Redis search and into a simple highlight-clip exporter.

**Phase 5 — Polish + frontend (end).** `frontend/` web app: video + live minimap side-by-side, reading saved pipeline outputs. Demo script, README, Devpost text. Rehearse the 5-minute pitch.

---

## 9. What "done" looks like for the demo

One command (or one notebook run) that: loads a match clip → tracks all players with SAM 3.1 → renders the 2D minimap → prints a HOTA accuracy number vs ground truth → has Sentry/Arize live → answers one Redis semantic query. Everything else is bonus.
