"""YOLO + ByteTrack tracking backend (Ultralytics) — the pragmatic, ungated path.

Why this exists: SAM 3.1's weights are gated on Hugging Face (slow/uncertain
approval) and require a heavier GPU runtime. For a 24h deadline that can be too
much friction. Ultralytics YOLO is **ungated, free, auto-downloads its COCO
weights, and runs on a free Colab T4 in seconds**, with built-in multi-object
tracking (ByteTrack) that gives persistent IDs — exactly what the rest of the
pipeline (visualize, pitch, HOTA eval) needs.

It satisfies the SAME `SamBackend` interface, so swapping SAM<->YOLO is one line
in config.yaml and nothing downstream changes. SAM 3.1 (`sam_local`/`sam_api`)
stays available if access ever clears; YOLO is the reliable default for the demo.

Tradeoff vs SAM: YOLO detects COCO classes, so every player/keeper/referee is
just "person" (class 0) — no role split from the model itself. That's fine for
tracking + the 2D minimap; role/team can be recovered later (jersey-color
k-means, see docs/ML_DIRECTIONS.md). The ball is COCO "sports ball" (class 32).

    from ultralytics import YOLO
    model = YOLO("yolo11n.pt")                      # ungated, auto-downloads
    for r in model.track(source="clip.mp4", stream=True, classes=[0, 32]):
        r.boxes.xyxy, r.boxes.id, r.boxes.cls, r.boxes.conf
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from src.model.sam_backend import Detection, FrameResult, TrackResult

DEFAULT_WEIGHTS = "yolo11n.pt"  # nano: fast on a T4; bump to yolo11s/m for accuracy

# Map our SAM-style noun-phrase prompts to COCO class indices.
_PROMPT_TO_COCO = {
    "soccer player": 0, "player": 0, "goalkeeper": 0, "keeper": 0, "referee": 0, "person": 0,
    "sports ball": 32, "ball": 32,
}


class YoloBackend:
    """Ultralytics YOLO detection + ByteTrack tracking. Runs on any CUDA GPU (or CPU)."""

    def __init__(self, cfg: Any) -> None:
        sam_cfg = cfg.raw.get("sam", {})
        self.weights = str(sam_cfg.get("yolo_weights", DEFAULT_WEIGHTS))
        self.device = getattr(cfg, "device", "cuda")
        self.conf = float(sam_cfg.get("conf", 0.25))
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "ultralytics is required for the YOLO backend.  pip install -U ultralytics"
            ) from exc
        self._model = YOLO(self.weights)  # auto-downloads COCO weights (ungated)

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        self._ensure_model()

        classes = sorted({_PROMPT_TO_COCO.get(p.strip().lower()) for p in prompts} - {None})
        results = self._model.track(
            source=str(video_path),
            stream=True,           # lazy per-frame generator
            classes=classes or None,
            conf=self.conf,
            device=self.device,
            verbose=False,
            persist=True,          # keep track IDs stable across frames
        )
        # 1-based frame_index to match iter_frames / GSR conventions.
        for frame_index, r in enumerate(results, start=1):
            yield _to_frame_result(r, frame_index, max_objects)

    def close(self) -> None:
        self._model = None


def _to_frame_result(r, frame_index: int, max_objects: int | None) -> FrameResult:
    """Convert one Ultralytics Results object into our FrameResult."""
    orig_shape = getattr(r, "orig_shape", None)
    height, width = (int(orig_shape[0]), int(orig_shape[1])) if orig_shape else (None, None)
    boxes = getattr(r, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return FrameResult(frame_index=frame_index, detections=(), width=width, height=height)

    names = getattr(r, "names", None)  # {cls_index: label}
    xyxy = boxes.xyxy.cpu().numpy()
    cls = boxes.cls.cpu().numpy().astype(int) if boxes.cls is not None else np.zeros(len(xyxy), int)
    conf = boxes.conf.cpu().numpy() if boxes.conf is not None else np.ones(len(xyxy))
    ids = (
        boxes.id.cpu().numpy().astype(int)
        if getattr(boxes, "id", None) is not None
        else np.arange(len(xyxy))  # tracker may give no IDs on the very first frame
    )

    n = len(xyxy) if max_objects is None else min(len(xyxy), max_objects)
    dets: list[Detection] = []
    for i in range(n):
        label = names.get(int(cls[i]), f"class_{cls[i]}") if isinstance(names, dict) else str(cls[i])
        x1, y1, x2, y2 = (float(v) for v in xyxy[i])
        dets.append(
            Detection(
                instance_id=int(ids[i]),
                label=label,
                bbox=(x1, y1, x2 - x1, y2 - y1),  # x, y, w, h — canonical Detection shape
                mask=None,
                score=float(conf[i]),
            )
        )
    return FrameResult(frame_index=frame_index, detections=tuple(dets), width=width, height=height)
