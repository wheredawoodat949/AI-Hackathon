<<<<<<< HEAD
"""Self-hosted SAM 3.1 backend via the Ultralytics package (CLAUDE.md §4).

This runs the SAM 3 weights IN-PROCESS on the local CUDA device — which is what
you get on a Colab GPU runtime or any GPU box. It implements the `SamBackend`
protocol using Ultralytics' `SAM3VideoSemanticPredictor`, the text-prompted
detect+track interface for Promptable Concept Segmentation over video.

Prereqs (do these on the GPU box / Colab, NOT the laptop):
  1. pip install -U ultralytics            # SAM 3 needs ultralytics >= 8.3.237
  2. Request access + download weights:    https://huggingface.co/facebook/sam3
     SAM 3 weights (`sam3.pt`) are GATED and NOT auto-downloaded — place the file
     in the repo root or set `sam.weights` / SAM3_WEIGHTS to its path.
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
from typing import Iterator, Optional

import numpy as np

from src.model.sam_backend import Detection, FrameResult

DEFAULT_WEIGHTS = "sam3.pt"


class SamLocalBackend:
    """Run SAM 3.1 weights locally (Colab/GPU box) via Ultralytics."""

    def __init__(
        self,
        weights: str | Path = DEFAULT_WEIGHTS,
        *,
        device: str = "cuda",
        conf: float = 0.25,
        imgsz: int = 640,
        half: bool = True,
    ) -> None:
        self.weights = str(weights)
        self.device = device
        self.conf = conf
        self.imgsz = imgsz
        self.half = half
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
        video_path: str | Path,
        prompts: list[str],
        *,
        max_frames: Optional[int] = None,
        include_masks: bool = False,
    ) -> Iterator[FrameResult]:
        if self._predictor is None:
            self._predictor = self._build_predictor()

        results = self._predictor(source=str(video_path), text=list(prompts), stream=True)
        for frame_index, r in enumerate(results):
            if max_frames is not None and frame_index >= max_frames:
                break
            yield _to_frame_result(r, frame_index, prompts, include_masks)


def _to_frame_result(r, frame_index: int, prompts: list[str], include_masks: bool) -> FrameResult:
    """Convert one Ultralytics Results object into our FrameResult."""
    height, width = (int(r.orig_shape[0]), int(r.orig_shape[1])) if getattr(r, "orig_shape", None) else (0, 0)
    boxes = getattr(r, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return FrameResult(frame_index=frame_index, width=width, height=height, detections=())

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

    dets: list[Detection] = []
    for i in range(len(xyxy)):
        label = _label_for(int(cls[i]), names, prompts)
        mask = None
        if include_masks and masks_xy is not None and masks_xy.data is not None and i < len(masks_xy.data):
            mask = masks_xy.data[i].cpu().numpy().astype(bool)
        x1, y1, x2, y2 = (float(v) for v in xyxy[i])
        dets.append(
            Detection(
                instance_id=int(ids[i]),
                label=label,
                score=float(conf[i]),
                bbox_xyxy=(x1, y1, x2, y2),
                mask=mask,
            )
        )
    return FrameResult(
        frame_index=frame_index, width=width, height=height, detections=tuple(dets)
    )


def _label_for(cls_index: int, names, prompts: list[str]) -> str:
    if isinstance(names, dict) and cls_index in names:
        return str(names[cls_index])
    if 0 <= cls_index < len(prompts):
        return prompts[cls_index]
    return f"class_{cls_index}"
=======
"""Self-hosted SAM 3.1 backend (runs weights on our GPU).

Implements the SamBackend interface. Heavy deps (torch, the SAM package) are
imported lazily inside methods so this module imports cleanly on any machine —
only constructing/using the backend requires the GPU stack.

Role A (tracking lead) fills in `track()`. Everything it needs is already typed
by the interface; return per-frame FrameResult(Detection(...)) streaming.
"""
from __future__ import annotations

from typing import Any, Sequence

from src.model.sam_backend import TrackResult


class SamLocalBackend:
    """SAM 3.1 with locally-loaded weights. Requires a CUDA GPU."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self._model = None  # lazily loaded in _ensure_model()

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        # Defer heavy imports + GPU check until we actually load weights.
        from src.utils.gpu import require_gpu

        device = require_gpu()  # fails loud if no CUDA (CLAUDE.md §2)
        # TODO(Role A): load SAM 3.1 weights onto `device` and assign self._model.
        raise NotImplementedError(
            "SamLocalBackend weight loading not implemented yet. "
            f"(device={device}) Load SAM 3.1 here, then implement track()."
        )

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        self._ensure_model()
        # TODO(Role A): run promptable concept segmentation + video tracking,
        # yielding FrameResult(frame_index, (Detection(...), ...)) per frame.
        raise NotImplementedError("SamLocalBackend.track() not implemented yet.")

    def close(self) -> None:
        self._model = None
>>>>>>> origin/main
