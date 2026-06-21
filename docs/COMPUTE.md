# Compute & Training Guide

What we actually need GPUs for, and where to get them during the 24-hour UC
Berkeley AI Hackathon. **Read this before burning time chasing clusters** — the
fastest path is almost always the team GPU box or a sponsor cloud, not a
DOE supercomputer.

> ## ⚡ DECISION (2026-06-20, updated): use Google Colab's free T4 GPU. Here's why.
> - **The hackathon provides NO GPUs**, confirmed twice: Slack director (`#0-ask-directors`:
>   *"We unfortunately won't have GPUs. There will be 3 3D printers!"*) AND the official live
>   site (live.hackberkeley.org) sponsor-resource list — **RunPod isn't even on it** (Slack-only,
>   credits not auto-granted, requires a booth visit) and **Annapurna Labs is a "Showcase — Coming
>   Soon" prize category**, not a GPU-credit program (also: their chips are AWS Trainium/Neuron,
>   not CUDA — wrong fit for SAM regardless).
> - **Our only team GPU is a K1900** (~2009-2013 Kepler-era workstation mobile GPU, ~2GB VRAM) —
>   **below SAM 3.1's ~4GB inference floor.** Self-hosting on that machine is not viable.
> - **Current path: Google Colab.** Free T4 runtime (16GB VRAM, real CUDA) clears SAM 3.1's bar
>   easily and costs nothing. `sam.backend: local` runs there via 🤗 Transformers
>   (`Sam3VideoModel`/`Sam3VideoProcessor`, `src/model/sam_local.py`) — see §2.A below. Access
>   request submitted to huggingface.co/facebook/sam3, awaiting Meta's review.
> - **fal.ai hosted SAM 3.1 API is DEFERRED, not abandoned** — verified real and working
>   (`fal-ai/sam-3-1/video`, ~$0.16 per 10s clip, zero GPU needed), implemented in
>   `src/model/sam_api.py`. Picking it up is now documented in
>   [docs/DEFERRED.md](DEFERRED.md) — use it if Colab hits a wall.
> - `sam.backend: replay` needs no GPU/key at all and is already verified working (Phase 1) — the
>   safety net if both of the above run out of time.
> - **Anthropic** gives ~$25–50 Claude API credits/hacker (school email, `#spons-anthropic`) — for
>   Claude, not a GPU. NERSC/JGI remains off-policy (§3) — don't.

---

## 1. What do we even need compute for?

Be honest about the workload before requesting hardware:

- **SAM 3.1 inference on 4K panoramic video — this is the expensive part.** Cost
  scales ~linearly with (#tracked objects × #frames). One match is 4K × ~90 min ×
  25 fps × ~23 objects. We develop on **short clips** (`run.clip_seconds: 10` in
  config) precisely to keep this tractable. A single modern GPU (A100/L4/4090/even
  T4 for short clips) is enough for the demo.
- **Training is OPTIONAL and a stretch.** SAM 3.1 is *promptable / zero-shot* — you
  give it noun-phrase prompts and it segments+tracks with no training. For the
  Phase 0–2 demo we do **not** train anything. If we want a "we trained a model"
  story (Phase 4+), the realistic, scoped options are:
  - **Fine-tune a detector (YOLO) from GSR boxes.** The GSR ground truth already has
    `bbox_image` for every player/keeper/ref (see `src/data/loader.py`). The
    SoccerTrack-v2 repo ships `src/data_utils/create_yolo_dataset.py` to convert
    GSR → a YOLO detection set. Fine-tuning a small YOLO on one match is a few
    GPU-hours and gives a measurable number — a good Arize before/after story.
  - **Train a re-ID / tracker head** to cut ID-swaps (feeds the Sentry ID-swap
    metric). Smaller still.
  - Full SAM fine-tuning is **out of scope** for 24h — don't.

**Bottom line:** one GPU for inference is the requirement; training is a bonus that
needs at most a few GPU-hours. Size your compute ask accordingly.

---

## 2. Where to get SAM 3.1 inference (ranked, fastest/most-certain first)

### A. Google Colab free T4 — PRIMARY, `sam.backend: local`
Free, real CUDA, 16GB VRAM — clears SAM 3.1's ~4GB floor easily; our only physical GPU
(K1900, ~2GB) doesn't. Notebook: `notebooks/colab_sam_tracking.ipynb`.
1. Open the notebook in Colab, **Runtime → Change runtime type → T4 GPU**.
2. Clone the repo + `pip install -U transformers accelerate` (cell 2).
3. Request access at [huggingface.co/facebook/sam3](https://huggingface.co/facebook/sam3) —
   **not guaranteed/instant, can be denied** (real reports of denials exist). Check approval
   status any time at [huggingface.co/settings/gated-repos](https://huggingface.co/settings/gated-repos).
4. Once approved: create a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens),
   `huggingface_hub.login(token=...)` (cell in the notebook) — weights then auto-download via
   `from_pretrained("facebook/sam3")`, no manual file placement.
5. Run the rest of the notebook → real tracked, annotated clip in `outputs/`.

`src/model/sam_local.py` uses the **official 🤗 Transformers path** straight from the live
model card (`Sam3VideoModel`/`Sam3VideoProcessor`) — not a third-party wrapper. Promptable
Concept Segmentation finds all instances of ONE concept per call, so it runs one full video
pass per prompt (4 short passes for our 4 prompts) and merges results by frame, with
instance IDs offset so two prompts' objects never collide. Uses fp16 (not the model card's
default bf16 — Colab's T4 is pre-Ampere and doesn't support bf16 well).
**Caveat (untested live):** access was pending as of 2026-06-21 — the inference call itself
hasn't run yet end-to-end. If access stalls, don't wait — switch to B or C below.

### B. fal.ai hosted SAM 3.1 — DEFERRED fallback, no GPU needed at all
No GPU, no gating, ~$0.16 for a 10s clip — just a `FAL_KEY`. Verified real and implemented
in `src/model/sam_api.py`, just not the current focus. Exact pickup steps in
[docs/DEFERRED.md](DEFERRED.md) — use this if Colab's gated access stalls.

### C. `sam.backend: replay` — the safety net, zero cost, zero GPU, zero gating
Replays GSR ground truth through the exact same interface so the whole pipeline
(track → visualize → encode) already runs today with nothing external required. The
config default. Falls back to this if both A and B run out of time before the deadline.
See Phase 1 in `PROGRESS.md`.

### D. Other free standby GPUs (backup, not primary)
- **Kaggle Notebooks** — 2×T4, ~30 GPU-hours/week free. Same `sam_local.py` path applies.

---

## 3. NERSC / JGI Perlmutter — can we use it? (Short answer: almost certainly not for this)

**What it is:** NERSC's Perlmutter has thousands of NVIDIA **A100** GPU nodes (40 GB and
80 GB HBM), SLURM-scheduled. JGI is a DOE user facility whose users get NERSC allocations
**under JGI's DOE project**.

**Why it's the wrong tool here — verified against NERSC docs:**
- **Allocations are scoped to approved DOE science.** GPU node-hours are requested via
  the **ERCAP** process, drawn from a specific DOE Office of Science **program pool**, and
  require justifying the *code and science questions*. A soccer-CV hackathon is **outside
  the approved scope** of a JGI genomics allocation. Running it there spends JGI's
  node-hours on non-JGI work — a usage-policy problem, not just a technicality. **Get
  explicit PI / allocation-manager sign-off before even considering it.**
- **It's batch + MFA + annual allocations**, not built for a 24-hour iteration loop. You
  submit SLURM jobs to a queue and wait; you can't interactively poke at it like a dev box.

**If (and only if) you have a NERSC account with a GPU allocation you're allowed to use**,
the mechanics are:
```bash
ssh <user>@perlmutter.nersc.gov          # requires NERSC MFA (sallinst / app token)
# interactive GPU node:
salloc -A <project> -C gpu -q interactive -t 60 --gpus-per-node=1
# or a batch job:
#   #SBATCH -A <project>
#   #SBATCH -C gpu
#   #SBATCH --gpus-per-node=1
#   #SBATCH -q regular -t 02:00:00
sbatch run.slurm
```
**Recommendation:** don't plan the demo around NERSC. Treat it as a non-option unless a PI
explicitly green-lights non-project use — which is unusual. Use §2 instead.

Refs: [NERSC ERCAP](https://docs.nersc.gov/allocations/ercap_form/) ·
[Perlmutter jobs](https://nersc.gitlab.io/systems/perlmutter/running-jobs/) ·
[Queues & charges](https://docs.nersc.gov/jobs/policy/)

## 4. "Annapurna Labs" — resolved: it's an AWS-silicon hackathon cohost, not a GPU lender

Confirmed via Slack (`#cohost-annapurna-labs`) and the live site: Annapurna Labs (AWS's
chip division) is a **cohost with a "Showcase — Coming Soon" prize**, not a GPU-credit
program. Their hardware is Trainium/Inferentia (AWS Neuron SDK) — even if they hand out
AWS credits, that's the wrong accelerator family for SAM (no CUDA). Only relevant if your
team separately gets general AWS credits and launches a `g5`/`g6`/`p4` (NVIDIA) EC2
instance — ask in their channel, but don't plan the demo around it.

---

## 5. Standard bring-up (works with or without a GPU)
```bash
git clone https://github.com/wheredawoodat949/AI-Hackathon && cd AI-Hackathon
make setup && source .venv/bin/activate
make test                                    # should be green with no GPU/data
python -m src.data.download --match 117093 --no-videos   # Drive mirror, no auth
python -m src.tracking.demo                  # backend: replay — verifies the whole path
```
**Only if you have a real CUDA GPU**, also run `python -m src.utils.gpu` (fails loud
otherwise) and `python -m src.data.download --match 117093` (adds the panorama video) before
`python -m src.tracking.demo --backend local --video data/videos/...`. **Otherwise**, set
`FAL_KEY` in `.env` and use `--backend api` — see §2.A. No CUDA build of torch is required
unless you're actually using `sam.backend: local`.
