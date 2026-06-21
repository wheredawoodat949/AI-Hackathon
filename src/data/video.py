"""Video I/O helpers (Role A — feat/tracking).

Frame iteration + annotated-video writing + a synthetic canvas so we can render a
tracking visualization WITHOUT the 4K panorama (handy on a laptop / no-GPU box).
cv2 is imported lazily; numpy is a core dep.

    from src.data.video import iter_frames, write_video, blank_frame
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator

import numpy as np


def blank_frame(width: int, height: int, color: tuple[int, int, int] = (28, 32, 28)) -> np.ndarray:
    """An HxWx3 BGR canvas — a stand-in for a real frame when no video is present."""
    frame = np.empty((height, width, 3), dtype=np.uint8)
    frame[:, :] = color
    return frame


def iter_frames(video_path: str | Path, *, max_frames: int | None = None) -> Iterator[tuple[int, np.ndarray]]:
    """Yield (frame_index, BGR frame) from a video. Requires opencv + the file.

    Frame indices are 1-based to match the GSR/MOT convention.
    """
    import cv2  # lazy

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")
    try:
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            idx += 1
            yield idx, frame
            if max_frames is not None and idx >= max_frames:
                break
    finally:
        cap.release()


def write_video(
    frames: Iterable[np.ndarray],
    out_path: str | Path,
    *,
    fps: int = 25,
) -> Path:
    """Write BGR frames to an mp4. Falls back to per-frame PNGs if no mp4 codec.

    Returns the path actually written (the mp4, or the frames/ dir on fallback).
    """
    import cv2  # lazy

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    frames = iter(frames)
    try:
        first = next(frames)
    except StopIteration:
        raise ValueError("write_video got no frames.")
    h, w = first.shape[:2]

    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if writer.isOpened():
        writer.write(first)
        for f in frames:
            writer.write(f)
        writer.release()
        return out_path

    # Fallback: dump PNGs (some headless boxes lack an mp4 encoder).
    writer.release()
    png_dir = out_path.with_suffix("")
    png_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(png_dir / "frame_00001.png"), first)
    for i, f in enumerate(frames, start=2):
        cv2.imwrite(str(png_dir / f"frame_{i:05d}.png"), f)
    return png_dir
