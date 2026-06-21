# Compute & Training Guide

What we actually need GPUs for, and where to get them during the 24-hour UC
Berkeley AI Hackathon. **Read this before burning time chasing clusters** — the
fastest path is almost always the team GPU box or a sponsor cloud, not a
DOE supercomputer.

> ## ⚡ CONFIRMED from the hackathon Slack (2026-06-20)
> - **The hackathon itself provides NO GPUs** and no general GPU/HuggingFace credits.
>   (Director, `#0-ask-directors`: *"We unfortunately won't have GPUs. There will be 3 3D printers!"*)
> - **RunPod** is a sponsor (`#spons-runpod`) → on-demand GPU cloud (A100/H100/4090). Credits are
>   **not auto-granted** — get the promo/code at the RunPod booth or in `#spons-runpod`. **This is our
>   primary GPU path for self-hosting SAM.**
> - **Annapurna Labs** (AWS silicon) is a **cohost** (`#cohost-annapurna-labs`) with a track + workshop.
>   AWS-credit availability still unanswered in Slack — **ask at their booth.** Caveat: their accelerators
>   are Trainium/Inferentia (AWS Neuron, training-oriented) — not drop-in CUDA for SAM inference.
> - **Anthropic** gives **~$25–50 Claude API credits/hacker** (apply with a school email; see `#spons-anthropic`).
>   That's for the Claude API (our AI layer / a tactical-LLM feature), **not** a GPU.
> - Net: plan on **RunPod (ask for credits) or the team GPU box**; Colab/Kaggle as free fallback. Don't
>   count on NERSC/JGI (see §3).

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

## 2. Where to get a GPU (ranked, fastest first)

### A. The team GPU box (primary — CLAUDE.md §2)
JupyterLab-in-VSCode with a GPU is our assumed environment. Verify before any heavy
run:
```bash
python -m src.utils.gpu      # prints the device; fails loud if no CUDA
```
Everything is built to run here. Use this unless you hit a memory wall on full-match
4K, in which case drop to shorter clips or a lower-res proxy first.

### B. RunPod — our primary GPU path (sponsor, confirmed)
RunPod (`#spons-runpod`) is an on-demand GPU cloud: spin up an A100/H100/4090 pod in
minutes, with NVIDIA CUDA (so `sam_local` works directly). Workflow:
1. **Get credits** — ask at the RunPod booth or in `#spons-runpod` for the hackathon promo
   code (not auto-granted as of 2026-06-20). Sign up at runpod.io.
2. Launch a **GPU Pod** with a PyTorch/CUDA template (or a Jupyter template). A single
   A100-40GB is plenty for short-clip SAM inference; H100 if you push full matches.
3. SSH in (or use their Jupyter), then the standard bring-up in §5. Pull our repo, install,
   run. Persist outputs to a volume or `scp` them back before the pod is torn down.
- If credits don't come through, fall back to §C/§D, or use the **hosted SAM API backend**
  (`sam.backend: api`) which needs no GPU of our own at all.

### B2. Annapurna Labs / AWS (cohost — ask at booth)
AWS-silicon cohost with a dedicated track. If they hand out **AWS credits**, you can launch
a `g5`/`g6` (NVIDIA A10G/L4) or `p4`/`p5` (A100/H100) EC2 instance — standard CUDA, our
`sam_local` runs as-is. Their *own* Trainium/Inferentia chips need the AWS Neuron SDK and a
model port, so **don't** target those for SAM in 24h; only relevant if we pivot to an LLM
training/inference demo on Neuron. Ask in `#cohost-annapurna-labs`.

### C. Free standby GPUs (no waiting on organizers)
- **Google Colab** — free T4; Pro gives L4/A100. Mount the repo, `pip install -r
  requirements.txt`, run notebooks. Good for short-clip SAM inference + YOLO fine-tune.
- **Kaggle Notebooks** — 2×T4 or P100, ~30 GPU-hours/week free. Good for a YOLO fine-tune.

### D. Pay-as-you-go (if someone has a card / credits)
Modal, Lambda Cloud, RunPod, Together, Hyperbolic — spin up an A100/H100 in minutes.
Modal in particular is nice for wrapping `src/` functions as serverless GPU jobs.

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

## 4. "Anupurna lab" GPUs — UNVERIFIED, confirm before relying on it

We could not confirm a lab by this name or its GPU access terms, so **do not plan around
it until verified.** If it's a campus research lab willing to lend GPU time, ask the lab
admin for, specifically:
1. An account / SSH host (and whether it needs campus VPN).
2. Scheduler: bare GPUs (just `nvidia-smi` + run) or **SLURM** (then use the §3 sbatch
   pattern with their `-A`/partition names).
3. GPU model + count + any time limits, and whether external-data downloads (our gdown
   pull of the SoccerTrack mirror) are allowed from their network.
Once you have that, our repo runs there unchanged: `pip install -r requirements.txt` →
`python -m src.utils.gpu` → `python -m src.data.download` → notebooks.

---

## 5. Once you have ANY GPU — the standard bring-up
```bash
git clone https://github.com/wheredawoodat949/AI-Hackathon && cd AI-Hackathon
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt            # CUDA build of torch per pytorch.org
python -m src.utils.gpu                     # MUST show CUDA before heavy runs
python -m src.data.download --match 117093  # Drive mirror, incl. video (no auth)
# then run notebooks/demo.ipynb or the Phase-1 tracking entrypoint
```
For SAM specifically, if no local CUDA is available, set `sam.backend: api` in
`config.yaml` and use a hosted endpoint instead of self-hosted weights.
