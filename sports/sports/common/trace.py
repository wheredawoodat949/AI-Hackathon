"""Fading movement trails for tracked detections.

Ported from Vincent's soccer implementation (sam_model_vincent c76c85d). The
annotator is sport-agnostic and uses image-space anchor history.
"""
from __future__ import annotations

from collections import deque

import cv2
import numpy as np
import supervision as sv


class TraceAnnotator:
    """Render fading, palette-coloured movement trails."""

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
        if max_length < 2 or thickness < 1 or prune_after < 0:
            raise ValueError("invalid trace dimensions")
        if not 0 <= base_opacity <= 1:
            raise ValueError("base_opacity must be between 0 and 1")
        self.color_palette = color_palette
        self.max_length = int(max_length)
        self.thickness = int(thickness)
        self.base_opacity = float(base_opacity)
        self.anchor = anchor
        self.draw_arrowhead = bool(draw_arrowhead)
        self.speed_styling = bool(speed_styling)
        self.fps = float(fps) if fps else 30.0
        self.prune_after = int(prune_after)
        self.tracks: dict[int, deque[tuple[int, int]]] = {}
        self.track_color: dict[int, int] = {}
        self._missing: dict[int, int] = {}

    def update(
        self,
        detections: sv.Detections,
        color_lookup: np.ndarray | None = None,
    ) -> None:
        """Append current anchors and prune stale track histories."""
        if detections.tracker_id is None:
            self._prune(set())
            return
        anchors = detections.get_anchors_coordinates(self.anchor)
        if color_lookup is None:
            color_lookup = (
                detections.class_id
                if detections.class_id is not None
                else np.zeros(len(detections), dtype=int)
            )
        if len(color_lookup) != len(detections):
            raise ValueError("color_lookup must align with detections")

        present = set()
        for index, raw_track_id in enumerate(detections.tracker_id):
            track_id = int(raw_track_id)
            present.add(track_id)
            point = (int(anchors[index][0]), int(anchors[index][1]))
            self.tracks.setdefault(track_id, deque(maxlen=self.max_length)).append(point)
            self.track_color[track_id] = int(color_lookup[index])
            self._missing[track_id] = 0
        self._prune(present)

    def _prune(self, present: set[int]) -> None:
        for track_id in list(self.tracks):
            if track_id in present:
                continue
            self._missing[track_id] = self._missing.get(track_id, 0) + 1
            if self._missing[track_id] > self.prune_after:
                self.tracks.pop(track_id, None)
                self.track_color.pop(track_id, None)
                self._missing.pop(track_id, None)

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        """Draw all current histories on a copy-blended overlay."""
        overlay = frame.copy()
        drew = False
        for track_id, points in self.tracks.items():
            if len(points) < 2:
                continue
            drew = True
            base_color = self.color_palette.by_idx(
                self.track_color.get(track_id, 0)
            ).as_bgr()
            head_thickness = (
                self._speed_thickness(points) if self.speed_styling else self.thickness
            )
            for index in range(1, len(points)):
                fraction = index / (len(points) - 1)
                segment_thickness = max(1, int(round(head_thickness * fraction)))
                shade = 0.25 + 0.75 * fraction
                color = tuple(int(channel * shade) for channel in base_color)
                cv2.line(
                    overlay,
                    points[index - 1],
                    points[index],
                    color=color,
                    thickness=segment_thickness,
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

    def _speed_thickness(self, points: deque[tuple[int, int]]) -> int:
        (x0, y0), (x1, y1) = points[-2], points[-1]
        pixels_per_second = float(np.hypot(x1 - x0, y1 - y0)) * self.fps
        return self.thickness + int(min(3.0, pixels_per_second / 400.0))
