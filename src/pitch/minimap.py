"""2D tactical minimap renderer (Role B — feat/pitch-eval).

Draws entities at their pitch (meter) coordinates onto a top-down pitch image,
colored by team_side. Output frames are written to outputs/ (gitignored) and the
frontend reads them later.
"""
from __future__ import annotations

from typing import Any, Iterable

from src.pitch.homography import PITCH_LENGTH_M, PITCH_WIDTH_M


def render_minimap(entities_in_pitch_coords: Iterable, *, width_px: int = 1050) -> Any:
    """Render one top-down minimap frame.

    `entities_in_pitch_coords` = iterable of objects with (x, y, team_side, role).
    TODO(Role B): draw the pitch + dots with cv2/PIL; return an HxWx3 array.
    Scale: width_px spans PITCH_LENGTH_M; height = width_px * W/L.
    """
    _ = (PITCH_LENGTH_M, PITCH_WIDTH_M, width_px)  # referenced for the eventual draw
    raise NotImplementedError("render_minimap() not implemented yet.")
