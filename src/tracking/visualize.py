"""Draw tracked detections onto a frame (Role A — feat/tracking).

Boxes + persistent IDs + labels, colored by role/team. Works on a real video frame
or the synthetic canvas from src.data.video. cv2 imported lazily.

    from src.tracking.visualize import draw_detections
    annotated = draw_detections(frame_bgr, frame_result.detections)
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from src.model import Detection

# BGR colors by role (cv2 uses BGR).
_ROLE_COLOR = {
    "player": (80, 200, 80),
    "goalkeeper": (60, 180, 255),
    "referee": (40, 220, 220),
    "ball": (255, 255, 255),
    "other": (180, 180, 180),
}
_DEFAULT_COLOR = (200, 120, 120)


def color_for(label: str) -> tuple[int, int, int]:
    return _ROLE_COLOR.get((label or "").lower(), _DEFAULT_COLOR)


def draw_detections(
    frame: np.ndarray,
    detections: Iterable[Detection],
    *,
    scale: float = 1.0,
    draw_labels: bool = True,
) -> np.ndarray:
    """Return a copy of `frame` with each detection's box + id/label drawn.

    `scale` multiplies bbox coords — use it when rendering on a downscaled canvas
    (e.g. scale=0.25 to draw 4K-space boxes on a 960px canvas).
    """
    import cv2  # lazy

    out = frame.copy()
    for det in detections:
        x, y, w, h = (v * scale for v in det.bbox)
        p1 = (int(x), int(y))
        p2 = (int(x + w), int(y + h))
        col = color_for(det.label)
        cv2.rectangle(out, p1, p2, col, 2)
        if draw_labels:
            tag = f"{det.instance_id}:{det.label[:3]}"
            cv2.putText(out, tag, (p1[0], max(0, p1[1] - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    return out
