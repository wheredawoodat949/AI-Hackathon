"""Self-hosted SAM 3.1 backend via the Ultralytics package (CLAUDE.md §4).

Runs SAM 3 weights IN-PROCESS on a local CUDA device — what you get on a Colab
GPU runtime (free T4, 16GB — clears SAM 3's ~4GB floor easily; our team's only
physical GPU, a K1900 with ~2GB, does not). Implements the `SamBackend`
protocol using Ultralytics' `SAM3VideoSemanticPredictor`, the text-prompted
detect+track interface for Promptable Concept Segmentation over video.
Verified against the official Ultralytics SAM 3 docs (docs.ultralytics.com/models/sam-3).

Setup (do this on the Colab GPU runtime, NOT a laptop):
  1. pip install -U ultralytics            # SAM 3 needs ultralytics >= 8.3.237
  2. Request access at https://huggingface.co/facebook/sam3 (NOT auto-approved —
     can be denied/delayed; this is the main risk to this path before the deadline).
  3. Once approved, download `sam3.pt` directly:
     https://huggingface.co/facebook/sam3/resolve/main/sam3.pt?download=true
     Place it in the repo root, or set `sam.weights: <path>` in config.yaml.
  4. If prediction errors on `clip`: pip install git+https://github.com/openai/CLIP.git

If access is denied/delayed, see docs/DEFERRED.md (fal.ai hosted API, no gating)
or fall back to `sam.backend: replay` (already verified, no GPU/weights needed).

Reference (Ultralytics docs):
    from ultralytics.models.sam import SAM3VideoSemanticPredictor
    overrides = dict(conf=0.25, task="segment", mode="predict",
                     imgsz=640, model="sam3.pt", half=True)
    predictor = SAM3VideoSemanticPredictor(overrides=overrides)
    results = predictor(source="video.mp4", text=["person", "bicycle"], stream=True)
    for r in results: ...      # r is an Ultralytics Results (boxes.id = track IDs)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from src.model.sam_backend import Detection, FrameResult, TrackResult

DEFAULT_WEIGHTS = "sam3.pt"


class SamLocalBackend:
    """Run SAM 3.1 weights locally (Colab T4 or any CUDA box) via Ultralytics."""

    def __init__(self, cfg: Any) -> None:
        sam_cfg = cfg.raw.get("sam", {})
        self.weights = str(sam_cfg.get("weights", DEFAULT_WEIGHTS))
        self.device = getattr(cfg, "device", "cuda")
        self.conf = float(sam_cfg.get("conf", 0.25))
        self.imgsz = int(sam_cfg.get("imgsz", 640))
        self.half = bool(sam_cfg.get("half", True))
        self._predictor = None  # lazily built on first track() call

    # -- construction ---------------------------------------------------------

    def _ensure_weights(self) -> None:
        if Path(self.weights).exists() or os.path.isabs(self.weights):
            return
        raise FileNotFoundError(
            f"SAM 3 weights '{self.weights}' not found. They are GATED and not\n"
            "auto-downloaded:\n"
            "  1. Request access: https://huggingface.co/facebook/sam3\n"
            "     (NOT guaranteed/instant — can be denied or delayed)\n"
            "  2. Once approved, download directly:\n"
            "     https://huggingface.co/facebook/sam3/resolve/main/sam3.pt?download=true\n"
            "  3. Place sam3.pt in the repo root, or set sam.weights in config.yaml.\n"
            "If access doesn't come through in time, see docs/DEFERRED.md (fal.ai) "
            "or use sam.backend: replay."
        )

    def _build_predictor(self):
        from src.utils.gpu import require_gpu

        require_gpu()  # fails loud if no CUDA (CLAUDE.md §2) — e.g. Colab CPU runtime
        try:
            from ultralytics.models.sam import SAM3VideoSemanticPredictor
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "ultralytics (>=8.3.237) is required for the local SAM 3 backend.\n"
                "  pip install -U ultralytics"
            ) from exc
        self._ensure_weights()
        overrides = dict(
            conf=self.conf,
            task="segment",
            mode="predict",
            imgsz=self.imgsz,
            model=self.weights,
            half=self.half,
            device=self.device,
            verbose=False,
        )
        return SAM3VideoSemanticPredictor(overrides=overrides)

    # -- SamBackend ------------------------------------------------------------

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        if self._predictor is None:
            self._predictor = self._build_predictor()

        results = self._predictor(source=str(video_path), text=list(prompts), stream=True)
        for frame_index, r in enumerate(results):
            yield _to_frame_result(r, frame_index, list(prompts), max_objects)

    def close(self) -> None:
        self._predictor = None


def _to_frame_result(
    r, frame_index: int, prompts: list[str], max_objects: int | None
) -> FrameResult:
    """Convert one Ultralytics Results object into our FrameResult."""
    orig_shape = getattr(r, "orig_shape", None)
    height, width = (int(orig_shape[0]), int(orig_shape[1])) if orig_shape else (None, None)
    boxes = getattr(r, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return FrameResult(frame_index=frame_index, detections=(), width=width, height=height)

    names = getattr(r, "names", None)  # {cls_index: label}
    masks_xy = getattr(r, "masks", None)

    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy().astype(int) if boxes.cls is not None else np.zeros(len(xyxy), int)
    conf = boxes.conf.cpu().numpy() if boxes.conf is not None else np.ones(len(xyxy))
    ids = (
        boxes.id.cpu().numpy().astype(int)
        if getattr(boxes, "id", None) is not None
        else np.arange(len(xyxy))  # fall back to per-frame index if tracker gave no IDs
    )

    n = len(xyxy) if max_objects is None else min(len(xyxy), max_objects)
    dets: list[Detection] = []
    for i in range(n):
        label = _label_for(int(cls[i]), names, prompts)
        mask = None
        if masks_xy is not None and masks_xy.data is not None and i < len(masks_xy.data):
            mask = masks_xy.data[i].cpu().numpy().astype(bool)
        x1, y1, x2, y2 = (float(v) for v in xyxy[i])
        dets.append(
            Detection(
                instance_id=int(ids[i]),
                label=label,
                bbox=(x1, y1, x2 - x1, y2 - y1),  # x, y, w, h — canonical Detection shape
                mask=mask,
                score=float(conf[i]),
            )
        )
    return FrameResult(frame_index=frame_index, detections=tuple(dets), width=width, height=height)


def _label_for(cls_index: int, names, prompts: list[str]) -> str:
    if isinstance(names, dict) and cls_index in names:
        return str(names[cls_index])
    if 0 <= cls_index < len(prompts):
        return prompts[cls_index]
    return f"class_{cls_index}"
