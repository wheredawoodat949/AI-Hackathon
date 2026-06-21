"""Draw SAM tracks onto a clip -> annotated mp4 (Phase 1 visual proof).

Reusable so the notebook stays thin (CLAUDE.md §2): the demo notebook calls
`annotate_video(...)`; the logic lives here and the frontend can reuse it later.

    from src.model import get_backend
    from src.tracking.annotate import annotate_video

    backend = get_backend(cfg)
    frames = backend.track(clip, cfg.sam_prompts, max_frames=250)
    annotate_video(clip, frames, cfg.outputs / "tracked.mp4")
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.model.sam_backend import FrameResult

# Stable BGR colors per label (OpenCV is BGR). Unknown labels fall back to gray.
_LABEL_BGR: dict[str, tuple[int, int, int]] = {
    "soccer player": (60, 220, 60),
    "goalkeeper": (60, 220, 220),
    "referee": (220, 60, 220),
    "sports ball": (40, 120, 255),
}
_FALLBACK_BGR = (180, 180, 180)


def annotate_video(
    video_path: str | Path,
    frames: Iterable[FrameResult],
    out_path: str | Path,
    *,
    show_ids: bool = True,
    thickness: int = 2,
) -> tuple[Path, int]:
    """Overlay tracked boxes + IDs from `frames` onto `video_path`.

    Returns (out_path, n_frames_written). `frames` is materialized into a
    {frame_index: FrameResult} map, so a generator from backend.track() is fine.
    """
    try:
        import cv2  # noqa: WPS433 (deferred: heavy, only needed for rendering)
    except ImportError as exc:  # pragma: no cover
        raise ImportError("opencv-python is required: pip install opencv-python") from exc

    by_idx = {f.frame_index: f for f in frames}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    written = 0
    idx = 0
    try:
        while True:
            ok, img = cap.read()
            if not ok:
                break
            fr = by_idx.get(idx)
            if fr is not None:
                for det in fr.detections:
                    _draw_box(cv2, img, det, show_ids, thickness)
            writer.write(img)
            written += 1
            idx += 1
    finally:
        cap.release()
        writer.release()
    return out_path, written


def _draw_box(cv2, img, det, show_ids: bool, thickness: int) -> None:
    x1, y1, x2, y2 = (int(v) for v in det.bbox_xyxy)
    color = _LABEL_BGR.get(det.label, _FALLBACK_BGR)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    if show_ids:
        tag = f"#{det.instance_id}"
        cv2.putText(img, tag, (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
