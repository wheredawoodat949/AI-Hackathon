"""Draw GSR ground-truth boxes onto a real panorama frame — visual data validation.

The Phase-0/pre-SAM 'the boxes really land on players' check (complements
src.data.inspect, which only prints). Pulls one frame from the panoramic mp4 with
OpenCV, draws every GSR `bbox_image` colored by team_side/role, labels it with the
jersey/track_id, and writes a PNG to outputs/ (gitignored).

    python -m src.data.overlay                          # dev_match, half 1, frame 0
    python -m src.data.overlay --match 117093 --half 1 --image-id 500

Why this matters: it validates the whole data path end-to-end (loader parse ->
bbox_image coords -> the actual pixels) BEFORE we trust any model output. The same
bbox_image coords are what we feed YOLO/SAM, so if these land correctly the
detection inputs are sound. cv2 is imported lazily so `make test` stays green.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Optional

from src.config import load_config
from src.data.loader import Frame, load_match

# BGR colors (OpenCV) by team_side; referees/unknown fall back to yellow.
_TEAM_COLOR = {
    "left": (255, 80, 80),    # blue-ish
    "right": (80, 80, 255),   # red-ish
}
_REF_COLOR = (0, 215, 255)    # amber
_OTHER_COLOR = (200, 200, 200)


def _color_for(role: str, team_side: Optional[str]) -> tuple[int, int, int]:
    if role == "referee":
        return _REF_COLOR
    if team_side in _TEAM_COLOR:
        return _TEAM_COLOR[team_side]
    return _OTHER_COLOR


def find_video(data_root: Path, match_id: str, half: int = 1) -> Optional[Path]:
    """Locate the panorama mp4 for a match+half under <root>/videos/ (None if absent)."""
    vdir = data_root / "videos"
    if not vdir.is_dir():
        return None
    # Mirror nests them as videos/<id>/<id>_calibrated_panorama_{1st,2nd}_half.mp4
    # (some layouts flatten to videos/<id>_...). Search recursively, then prefer the
    # file whose name carries this half ("1st"/"2nd"); fall back to first match.
    cands = sorted(vdir.glob(f"**/{match_id}*.mp4"))
    if not cands:
        return None
    suffix = "1st" if half == 1 else "2nd"
    for c in cands:
        if suffix in c.name:
            return c
    return cands[0]


def read_frame(video_path: Path, image_id: int) -> Any:
    """Grab a single frame (0-based index) from the video as a BGR ndarray."""
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f"OpenCV could not open {video_path}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, image_id))
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise SystemExit(f"Could not read frame {image_id} from {video_path}")
    return frame


def draw_overlay(frame_img: Any, gsr_frame: Frame) -> Any:
    """Draw every GSR bbox_image (with a jersey/track_id label) onto frame_img."""
    import cv2

    drawn = 0
    for e in gsr_frame.entities:
        if e.bbox_image is None:
            continue
        x, y, w, h = e.bbox_image
        color = _color_for(e.role, e.team_side)
        cv2.rectangle(frame_img, (x, y), (x + w, y + h), color, 2)
        tag = f"#{e.jersey_number}" if e.jersey_number is not None else f"id{e.track_id}"
        cv2.putText(frame_img, tag, (x, max(0, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        drawn += 1
    return frame_img, drawn


def main() -> None:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Overlay GSR boxes on a real panorama frame.")
    p.add_argument("--match", default=cfg.dev_match)
    p.add_argument("--half", type=int, default=1)
    p.add_argument("--image-id", type=int, default=None,
                   help="Frame index within the half (default: first GSR frame).")
    p.add_argument("--out", default=None, help="Output PNG (default: outputs/overlay_<id>_h<half>_f<frame>.png).")
    args = p.parse_args()

    m = load_match(cfg.data_root, match_id=args.match)
    if args.image_id is None:
        frames = m.gsr_frames(args.half)
        if not frames:
            raise SystemExit(f"No GSR frames for {args.match} half {args.half}.")
        gsr_frame = frames[0]
    else:
        gsr_frame = m.gsr_frame(args.half, args.image_id)
        if gsr_frame is None:
            raise SystemExit(f"No GSR frame at half={args.half} image_id={args.image_id}.")

    video = find_video(cfg.data_root, args.match, args.half)
    if video is None:
        raise SystemExit(
            f"No video for match {args.match} under {cfg.data_root}/videos/.\n"
            "Download with video: python -m src.data.download --match "
            f"{args.match} --source drive"
        )

    import cv2

    frame_img = read_frame(video, gsr_frame.image_id)
    frame_img, drawn = draw_overlay(frame_img, gsr_frame)

    out = Path(args.out) if args.out else (
        cfg.outputs / f"overlay_{args.match}_h{args.half}_f{gsr_frame.image_id}.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), frame_img)
    print(f"[overlay] match {args.match} half {args.half} frame {gsr_frame.image_id}: "
          f"drew {drawn}/{len(gsr_frame.entities)} boxes")
    print(f"[overlay] wrote {out.resolve()}")


if __name__ == "__main__":
    main()
