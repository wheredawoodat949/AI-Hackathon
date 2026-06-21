"""Image -> 2D pitch coordinate mapping (Role B — feat/pitch-eval).

The GSR ground truth gives every entity a pitch position in meters (bbox_pitch
bottom-middle, see src.data.loader). For our predictions we need the same: a
homography from panoramic-image pixels to pitch meters.

The dataset ships pitch keypoints / camera calibration (raw/<id>/...). Prefer
those over estimating from scratch. cv2 is imported lazily.
"""
from __future__ import annotations

from typing import Any, Sequence

# Standard soccer pitch dimensions (meters). SoccerTrack uses pitch-centered
# coords (origin at center), so x in [-52.5, 52.5], y in [-34, 34] roughly.
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0


def estimate_homography(image_points: Sequence, pitch_points: Sequence) -> Any:
    """Solve the 3x3 homography mapping image px -> pitch meters.

    TODO(Role B): use cv2.findHomography(image_points, pitch_points). Defer the
    import: `import cv2`.
    """
    raise NotImplementedError("estimate_homography() not implemented yet.")


def image_to_pitch(points: Sequence, homography: Any) -> Any:
    """Apply a homography to image points -> pitch meters.

    TODO(Role B): cv2.perspectiveTransform. Returns Nx2 pitch coords.
    """
    raise NotImplementedError("image_to_pitch() not implemented yet.")
