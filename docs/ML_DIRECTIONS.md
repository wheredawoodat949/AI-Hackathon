# ML Directions & Fine-Tuning Assessment

What we can do in the ML space on top of tracking, ranked by **value × feasibility by
the 6 PM-tomorrow deadline**, plus an honest verdict on QLoRA.

> Guiding rule (CLAUDE.md): the committed demo is *track → 2D minimap → real HOTA → sponsors*.
> Everything below is layered on **only after** that works. Cut from the bottom if behind.

## A. Directions, ranked

| # | Idea | What it adds | Needs | GPU? | By 6pm? |
|---|------|--------------|-------|------|---------|
| 1 | **2D tactical minimap** (core, Role B) | the headline visual | homography from `raw/` calib + GSR pitch coords | no | ✅ yes |
| 2 | **Team identification** (jersey-color k-means on player crops) | colors the minimap by team automatically | crop pixels + k-means (scikit-learn) | no | ✅ yes |
| 3 | **Tactical analytics** — heatmaps, possession %, formation, pitch-control / xT | "pro analytics for amateur teams" story | just GSR/tracked pitch coords + numpy | no | ✅ yes (high ROI) |
| 4 | **Claude tactical commentary** (LLM) | natural-language analysis of events/positions; uses our **Anthropic credits**, no GPU | feed events+coords → Claude API | no | ✅ yes (high ROI) |
| 5 | **Re-ID embeddings** → fewer ID-swaps + feeds Redis vector search (Role C) | robustness + the Redis "semantic search" sponsor story | a re-ID/appearance model (e.g. OSNet) on crops | yes (light) | ⚠️ maybe |
| 6 | **BAS event spotting** (12 classes, Role D) | auto-detect Pass/Shot/Goal… for highlights | classifier over trajectories; GT in `bas/` | yes (light) | ⚠️ stretch |
| 7 | **Trajectory forecasting** (predict next positions) | flashy but research-y | sequence model on tracks | yes | ❌ unlikely |

**Highest ROI for the time we have: 1 → 3 → 4 → 2.** Items 3 and 4 are *pure analysis on data we
already have*, need **no GPU**, and tell the strongest story (accessible pro-level tactics + an
LLM that explains them). Item 4 specifically turns our Anthropic credits into a differentiator.

## B. The tracking model itself (Role A)

SAM 3.1 with text prompts is the plan, but **have a fallback** in case weights/access aren't
ready: behind the same `SamBackend` interface you can drop in **Grounding-DINO + SAM 2** (text→box→mask+track),
**YOLO-World** (open-vocab detection) + ByteTrack, or even a YOLO fine-tuned on the GSR boxes. The
`GsrReplayBackend` (no GPU) already exercises the whole pipeline so this swap is the only unknown.

## C. Fine-tuning — is QLoRA feasible / beneficial here?

**Short answer: no, not for this project within the deadline. Don't QLoRA.**

- **QLoRA is an LLM technique.** It loads a large *language/transformer* model in 4-bit and trains
  small LoRA adapters, to make fine-tuning fit on one GPU. Our core task is **segmentation/detection/
  tracking** (SAM, YOLO) — QLoRA doesn't apply to those; you'd fine-tune them with ordinary SGD, not QLoRA.
- **We don't need to train at all for the demo.** SAM 3.1 is *zero-shot/promptable* — that's the whole
  point. The committed path needs zero training.
- **The only legitimate "training" option is small and not-QLoRA:** fine-tune a **YOLO detector from the
  GSR `bbox_image` boxes** (the SoccerTrack repo even ships a GSR→YOLO converter). On a RunPod A100 that's
  ~a couple of GPU-hours and gives a real before/after number for the Arize story. Do this **only** if
  Phases 1–3 are done with time to spare.
- **Where QLoRA *could* technically fit, but we shouldn't:** if we fine-tuned an LLM/VLM for soccer
  tactical commentary (Direction 4). But (a) we have **no labeled instruction dataset**, (b) it needs a
  GPU + hours we don't have, and (c) **Claude via our Anthropic credits is a far stronger model for free** —
  prompt it instead of training a weaker one. QLoRA here is strictly worse use of 24 hours.

**Verdict:** skip QLoRA. If asked "did you train a model?", the honest, higher-value answer is: *"SAM is
zero-shot; we optionally fine-tuned a YOLO detector from the dataset's own ground-truth boxes, and we use
Claude for tactical reasoning rather than training a weaker LLM ourselves."* See [COMPUTE.md](COMPUTE.md)
for the RunPod path if you do the YOLO fine-tune.
