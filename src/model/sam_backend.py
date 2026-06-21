"""SAM backend interface + datatypes (CLAUDE.md §4).

ALL downstream code (tracking, pitch, eval, frontend) depends ONLY on the types
and `SamBackend` protocol here — never on a concrete backend. A factory in
`src.model.get_backend()` reads `config.yaml` (`sam.backend: local | api`) and
returns the right implementation, so we can run SAM 3.1 self-hosted (Colab/GPU
box) or behind a hosted endpoint without touching anything downstream.

Contract (CLAUDE.md §4):
    backend.track(video_path, prompts) -> Iterator[FrameResult]
where each FrameResult yields per-frame detections of {instance_id, label,
bbox, foot point, (optional) mask} with persistent instance_id across frames.

The `foot_xy` (bottom-middle of the image bbox) is the point Phase 2 feeds
through the homography to get on-pitch (x, y) in meters — it matches how the
SoccerTrack v2 GSR ground truth stores positions (bbox_pitch bottom-middle).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional, Protocol, runtime_checkable

import numpy as np


@dataclass(frozen=True)
class Detection:
    """One tracked instance in one frame."""

    instance_id: int                      # persistent track ID across frames
    label: str                            # which prompt matched ("soccer player", ...)
    score: float                          # detection confidence [0, 1]
    bbox_xyxy: tuple[float, float, float, float]  # pixels (x1, y1, x2, y2)
    mask: Optional[np.ndarray] = None     # HxW bool mask, only if include_masks=True

    @property
    def foot_xy(self) -> tuple[float, float]:
        """Bottom-middle of the bbox in pixels — the point to project to pitch."""
        x1, _y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) / 2.0, y2)

    @property
    def center_xy(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


@dataclass(frozen=True)
class FrameResult:
    """All tracked detections in a single video frame."""

    frame_index: int                      # 0-based index within the processed clip
    width: int                            # source frame width  (px)
    height: int                           # source frame height (px)
    detections: tuple[Detection, ...] = field(default_factory=tuple)

    def of_label(self, label: str) -> tuple[Detection, ...]:
        return tuple(d for d in self.detections if d.label == label)


@runtime_checkable
class SamBackend(Protocol):
    """The only surface downstream code is allowed to depend on."""

    def track(
        self,
        video_path: str | Path,
        prompts: list[str],
        *,
        max_frames: Optional[int] = None,
        include_masks: bool = False,
    ) -> Iterator[FrameResult]:
        """Detect + track every instance of each text prompt across the video.

        Yields one FrameResult per processed frame, in order. Implementations
        should stream (yield as they go) so callers can render/score without
        holding the whole video in memory. `max_frames` caps work for fast
        iteration; `include_masks` attaches per-detection masks (memory-heavy).
        """
        ...
