"""Self-hosted SAM 3.1 backend via 🤗 Transformers (CLAUDE.md §4).

Runs SAM 3 weights IN-PROCESS on a local CUDA device — what you get on a Colab
GPU runtime (free T4, 16GB — clears SAM 3's ~4GB floor easily; our team's only
physical GPU, a K1900 with ~2GB, does not). Implements the `SamBackend`
protocol using `Sam3VideoModel`/`Sam3VideoProcessor`, copied verbatim-pattern
from the live model card at https://huggingface.co/facebook/sam3 (2026-06-21).

This is the OFFICIAL distribution path for these exact gated weights — no
manual `sam3.pt` download/placement needed. `from_pretrained("facebook/sam3")`
auto-downloads once your HF account has approved access AND you're
authenticated (`huggingface_hub.login()` or `HF_TOKEN` env var).

Setup (do this on the Colab GPU runtime, NOT a laptop):
  1. pip install -U transformers accelerate
  2. Request access at https://huggingface.co/facebook/sam3 (NOT auto-approved —
     can be denied/delayed; this is the main risk to this path before the deadline.
     Check status: https://huggingface.co/settings/gated-repos)
  3. huggingface_hub.login(token=...) or set HF_TOKEN — then from_pretrained just works.

If access is denied/delayed, see docs/DEFERRED.md (fal.ai hosted API, no gating)
or fall back to `sam.backend: replay` (already verified, no GPU/weights needed).

Promptable Concept Segmentation (PCS) finds ALL instances of ONE concept per
text prompt — there's no documented multi-concept-per-call syntax. We run one
full video pass per prompt (cfg.sam_prompts has 4: short clips, so 4 passes is
cheap) and merge per-frame results by frame_index, offsetting each pass's
object_ids so two different prompts' objects never collide.

Reference (HF model card, Sam3VideoModel "Pre-loaded Video Inference"):
    from transformers import Sam3VideoModel, Sam3VideoProcessor
    model = Sam3VideoModel.from_pretrained("facebook/sam3").to(device, dtype=torch.float16)
    processor = Sam3VideoProcessor.from_pretrained("facebook/sam3")
    session = processor.init_video_session(video=frames, inference_device=device, dtype=torch.float16)
    session = processor.add_text_prompt(inference_session=session, text="person")
    for out in model.propagate_in_video_iterator(inference_session=session):
        result = processor.postprocess_outputs(session, out)
        # result["object_ids"], result["scores"], result["boxes"] (XYXY abs px), result["masks"]
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from src.model.sam_backend import Detection, FrameResult, TrackResult

HF_REPO = "facebook/sam3"
_OFFSET_PER_PROMPT = 100_000  # keeps instance_ids unique across separate per-prompt passes


class SamLocalBackend:
    """Run SAM 3.1 weights locally (Colab T4 or any CUDA box) via 🤗 Transformers."""

    def __init__(self, cfg: Any) -> None:
        sam_cfg = cfg.raw.get("sam", {})
        self.repo_id = str(sam_cfg.get("hf_repo", HF_REPO))
        self.device = getattr(cfg, "device", "cuda")
        self._model = None
        self._processor = None

    # -- construction -----------------------------------------------------------

    def _build(self) -> None:
        from src.utils.gpu import require_gpu

        require_gpu()  # fails loud if no CUDA (CLAUDE.md §2) — e.g. Colab CPU runtime
        try:
            import torch
            from transformers import Sam3VideoModel, Sam3VideoProcessor
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "transformers (with SAM3 support) + accelerate are required for the\n"
                "local SAM 3 backend.  pip install -U transformers accelerate"
            ) from exc

        # T4 (Colab free tier, compute capability 7.5) doesn't support bfloat16 well —
        # the model card defaults to bf16 (assumes Ampere+); we use fp16 instead.
        self._dtype = torch.float16
        try:
            self._model = Sam3VideoModel.from_pretrained(self.repo_id).to(self.device, dtype=self._dtype)
            self._processor = Sam3VideoProcessor.from_pretrained(self.repo_id)
        except Exception as exc:  # noqa: BLE001 - surface the gating/auth hint, then re-raise
            raise RuntimeError(
                f"Could not load {self.repo_id} from Hugging Face.\n"
                "  1. Request access: https://huggingface.co/facebook/sam3\n"
                "     (can be denied/delayed — check https://huggingface.co/settings/gated-repos)\n"
                "  2. Authenticate: huggingface_hub.login(token=...) or set HF_TOKEN.\n"
                "If access doesn't come through in time, see docs/DEFERRED.md (fal.ai)\n"
                "or use sam.backend: replay.\n"
                f"--- original error ---\n{exc}"
            ) from exc

    # -- SamBackend ---------------------------------------------------------------

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        if self._model is None:
            self._build()

        from transformers.video_utils import load_video

        video_frames, _ = load_video(str(video_path))
        height, width = video_frames[0].shape[:2] if len(video_frames) else (None, None)

        # frame_index -> accumulated detections across all prompt passes
        merged: dict[int, list[Detection]] = {}
        for prompt_idx, prompt in enumerate(prompts):
            session = self._processor.init_video_session(
                video=video_frames,
                inference_device=self.device,
                processing_device="cpu",
                video_storage_device="cpu",
                dtype=self._dtype,
            )
            session = self._processor.add_text_prompt(inference_session=session, text=prompt)
            for model_outputs in self._model.propagate_in_video_iterator(inference_session=session):
                out = self._processor.postprocess_outputs(session, model_outputs)
                dets = _dets_from_output(out, prompt, prompt_idx, max_objects)
                merged.setdefault(model_outputs.frame_idx, []).extend(dets)

        for frame_index in sorted(merged):
            yield FrameResult(
                frame_index=frame_index,
                detections=tuple(merged[frame_index]),
                width=width,
                height=height,
            )

    def close(self) -> None:
        self._model = None
        self._processor = None


def _dets_from_output(out: dict, label: str, prompt_idx: int, max_objects: int | None) -> list[Detection]:
    """Convert one postprocess_outputs() dict (one frame, one prompt pass) to Detections."""
    object_ids = _to_numpy(out.get("object_ids"))
    scores = _to_numpy(out.get("scores"))
    boxes = _to_numpy(out.get("boxes"))  # XYXY, absolute pixel coords
    masks = out.get("masks")

    if object_ids is None or boxes is None or len(boxes) == 0:
        return []

    n = len(boxes) if max_objects is None else min(len(boxes), max_objects)
    dets: list[Detection] = []
    for i in range(n):
        x1, y1, x2, y2 = (float(v) for v in boxes[i])
        mask = None
        if masks is not None and i < len(masks):
            mask = _to_numpy(masks[i])
            mask = mask.astype(bool) if mask is not None else None
        dets.append(
            Detection(
                instance_id=prompt_idx * _OFFSET_PER_PROMPT + int(object_ids[i]),
                label=label,
                bbox=(x1, y1, x2 - x1, y2 - y1),  # x, y, w, h — canonical Detection shape
                mask=mask,
                score=float(scores[i]) if scores is not None and i < len(scores) else None,
            )
        )
    return dets


def _to_numpy(x):
    if x is None:
        return None
    if hasattr(x, "detach"):  # torch.Tensor
        return x.detach().cpu().numpy()
    return np.asarray(x)
