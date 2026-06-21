"""Velocity / movement trace annotator for the soccer pipeline.

Draws fading, anti-aliased trajectory trails behind tracked objects. The trail
fade is produced cheaply: every segment is rendered once onto a single overlay
(with thickness + brightness tapered from a faint tail to a bold head) and the
whole overlay is blended back with a single ``cv2.addWeighted`` call. There are
no per-pixel Python loops -- only a handful of ``cv2`` draw calls per tracked
object -- so the cost stays negligible even with a full team on screen.
"""

from collections import deque
from typing import Deque, Dict, Optional, Tuple

import cv2
import numpy as np
import supervision as sv


class TraceAnnotator:
    """Render fading, team-coloured movement trails for tracked detections.

    Usage::

        trace = TraceAnnotator(color_palette=palette, fps=video_info.fps)
        trace.update(detections, color_lookup)
        frame = trace.annotate(frame)
    """

    def __init__(
        self,
        color_palette: sv.ColorPalette,
        max_length: int = 27,
        thickness: int = 4,
        base_opacity: float = 0.85,
        anchor: sv.Position = sv.Position.BOTTOM_CENTER,
        draw_arrowhead: bool = True,
        speed_styling: bool = True,
        fps: float = 30.0,
        prune_after: int = 30,
    ) -> None:
        """
        Args:
            color_palette: Palette indexed by ``color_lookup`` values.
            max_length: Max number of recent points kept per track (trail tail).
            thickness: Thickness of the bold head segment (tapers toward tail).
            base_opacity: Global opacity of the blended trail overlay.
            anchor: Detection anchor used as the trail point (foot position).
            draw_arrowhead: Draw a small arrowhead at the head for direction.
            speed_styling: Modulate head thickness by recent speed.
            fps: Video frame rate, used to convert pixel deltas to speed.
            prune_after: Drop a track after this many frames without an update
                (keeps memory bounded as players enter/leave the frame).
        """
        self.color_palette = color_palette
        self.max_length = int(max_length)
        self.thickness = int(thickness)
        self.base_opacity = float(base_opacity)
        self.anchor = anchor
        self.draw_arrowhead = bool(draw_arrowhead)
        self.speed_styling = bool(speed_styling)
        self.fps = float(fps) if fps else 30.0
        self.prune_after = int(prune_after)

        self.tracks: Dict[int, Deque[Tuple[int, int]]] = {}
        self.track_color: Dict[int, int] = {}
        self._missing: Dict[int, int] = {}

    def update(
        self,
        detections: sv.Detections,
        color_lookup: Optional[np.ndarray] = None,
    ) -> None:
        """Append the current anchor positions and prune stale tracks.

        Args:
            detections: Tracked detections (must carry ``tracker_id``).
            color_lookup: Per-detection palette indices aligned with
                ``detections``. Defaults to class ids when not provided.
        """
        if detections.tracker_id is None:
            self._prune(set())
            return

        xy = detections.get_anchors_coordinates(self.anchor)
        if color_lookup is None:
            color_lookup = (
                detections.class_id
                if detections.class_id is not None
                else np.zeros(len(detections), dtype=int)
            )

        present = set()
        for i, tracker_id in enumerate(detections.tracker_id):
            tracker_id = int(tracker_id)
            present.add(tracker_id)
            point = (int(xy[i][0]), int(xy[i][1]))
            if tracker_id not in self.tracks:
                self.tracks[tracker_id] = deque(maxlen=self.max_length)
            self.tracks[tracker_id].append(point)
            self.track_color[tracker_id] = int(color_lookup[i])
            self._missing[tracker_id] = 0

        self._prune(present)

    def _prune(self, present: set) -> None:
        """Increment idle counters and drop tracks unseen for too long."""
        for tracker_id in list(self.tracks.keys()):
            if tracker_id in present:
                continue
            self._missing[tracker_id] = self._missing.get(tracker_id, 0) + 1
            if self._missing[tracker_id] > self.prune_after:
                self.tracks.pop(tracker_id, None)
                self.track_color.pop(tracker_id, None)
                self._missing.pop(tracker_id, None)

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        """Draw all trails onto ``frame`` and return the annotated frame."""
        overlay = frame.copy()
        drew = False

        for tracker_id, points in self.tracks.items():
            if len(points) < 2:
                continue
            drew = True
            base_color = self.color_palette.by_idx(
                self.track_color.get(tracker_id, 0)
            ).as_bgr()

            n = len(points)
            head_thickness = self.thickness
            if self.speed_styling:
                head_thickness = self._speed_thickness(points)

            for i in range(1, n):
                frac = i / (n - 1)  # 0 at tail, 1 at head
                seg_thickness = max(1, int(round(head_thickness * frac)))
                # Darken older segments toward the tail for a clean fade.
                shade = 0.25 + 0.75 * frac
                color = tuple(int(c * shade) for c in base_color)
                cv2.line(
                    overlay,
                    points[i - 1],
                    points[i],
                    color=color,
                    thickness=seg_thickness,
                    lineType=cv2.LINE_AA,
                )

            if self.draw_arrowhead:
                cv2.arrowedLine(
                    overlay,
                    points[-2],
                    points[-1],
                    color=base_color,
                    thickness=max(1, head_thickness),
                    line_type=cv2.LINE_AA,
                    tipLength=0.4,
                )

        if not drew:
            return frame
        return cv2.addWeighted(
            overlay, self.base_opacity, frame, 1.0 - self.base_opacity, 0.0
        )

    def _speed_thickness(self, points: Deque[Tuple[int, int]]) -> int:
        """Scale head thickness by recent speed (pixels/sec), clamped."""
        (x0, y0), (x1, y1) = points[-2], points[-1]
        speed = float(np.hypot(x1 - x0, y1 - y0)) * self.fps
        # Map ~[0, 1200] px/s onto a [base, base+3] thickness range.
        extra = int(min(3.0, speed / 400.0))
        return self.thickness + extra
