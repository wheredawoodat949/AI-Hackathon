"""Self-hosted SAM 3.1 backend via the Ultralytics package (CLAUDE.md §4).

Runs the SAM 3 weights IN-PROCESS on the local CUDA device — what you get on a
Colab GPU runtime or any GPU box. Implements the `SamBackend` protocol using
Ultralytics' `SAM3VideoSemanticPredictor`, the text-prompted detect+track
interface for Promptable Concept Segmentation over video. Heavy imports
(ultralytics/torch) are deferred to the first `track()` call, so this module
imports cleanly on any machine — only constructing the predictor needs the GPU stack.

Prereqs (do these on the GPU box / Colab, NOT the laptop):
  1. pip install -U ultralytics            # SAM 3 needs ultralytics >= 8.3.237
  2. Request access + download weights:    https://huggingface.co/facebook/sam3
     SAM 3 weights (`sam3.pt`) are GATED and NOT auto-downloaded — set
     `sam.weights` in config.yaml (or place `sam3.pt` in the repo root).
  3. If prediction errors on `clip`, install the correct package:
         pip install git+https://github.com/openai/CLIP.git

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

from src.model.sam_backend import Detection, FrameResult, TrackResult

DEFAULT_WEIGHTS = "sam3.pt"


class SamLocalBackend:
    """Run SAM 3.1 weights locally (Colab/GPU box) via Ultralytics."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        sam_cfg = getattr(cfg, "raw", {}).get("sam", {}) if cfg is not None else {}
        self.weights = str(sam_cfg.get("weights", DEFAULT_WEIGHTS))
        self.device = getattr(cfg, "device", "cuda")
        self.conf = float(sam_cfg.get("conf", 0.25))
        self.imgsz = int(sam_cfg.get("imgsz", 640))
        self.half = bool(sam_cfg.get("half", True))
        self._predictor = None  # lazily built on first track() call

    # -- construction ----------------------------------------------------------

    def _ensure_weights(self) -> None:
        if Path(self.weights).exists() or os.path.isabs(self.weights):
            return
        raise FileNotFoundError(
            f"SAM 3 weights '{self.weights}' not found. They are GATED and not\n"
            "auto-downloaded. Request access + download `sam3.pt` from\n"
            "  https://huggingface.co/facebook/sam3\n"
            "then place it in the repo root or set sam.weights in config.yaml."
        )

    def _build_predictor(self):
        try:
            from ultralytics.models.sam import SAM3VideoSemanticPredictor
        except ImportError as exc:  # pragma: no cover - exercised only on the GPU box
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

        prompts = list(prompts)
        results = self._predictor(source=str(video_path), text=prompts, stream=True)
        for frame_index, r in enumerate(results):
            yield _to_frame_result(r, frame_index, prompts, max_objects)

    def close(self) -> None:
        self._predictor = None


def _to_frame_result(
    r, frame_index: int, prompts: Sequence[str], max_objects: int | None
) -> FrameResult:
    """Convert one Ultralytics Results object into our FrameResult (bbox = x, y, w, h)."""
    import numpy as np  # lazy: only needed when actually decoding model results

    boxes = getattr(r, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return FrameResult(frame_index=frame_index, detections=())

    names = getattr(r, "names", None)  # {cls_index: label}
    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy().astype(int) if boxes.cls is not None else np.zeros(len(xyxy), int)
    conf = boxes.conf.cpu().numpy() if boxes.conf is not None else np.ones(len(xyxy))
    ids = (
        boxes.id.cpu().numpy().astype(int)
        if getattr(boxes, "id", None) is not None
        else np.arange(len(xyxy))  # fall back to per-frame index if tracker gave no IDs
    )

    dets: list[Detection] = []
    for i in range(len(xyxy)):
        if max_objects is not None and len(dets) >= max_objects:
            break
        x1, y1, x2, y2 = (float(v) for v in xyxy[i])
        dets.append(
            Detection(
                instance_id=int(ids[i]),
                label=_label_for(int(cls[i]), names, prompts),
                bbox=(x1, y1, x2 - x1, y2 - y1),  # xyxy -> x, y, w, h
                mask=None,
                score=float(conf[i]),
            )
        )
    return FrameResult(frame_index=frame_index, detections=tuple(dets))


def _label_for(cls_index: int, names, prompts: Sequence[str]) -> str:
    if isinstance(names, dict) and cls_index in names:
        return str(names[cls_index])
    if 0 <= cls_index < len(prompts):
        return prompts[cls_index]
    return f"class_{cls_index}"
