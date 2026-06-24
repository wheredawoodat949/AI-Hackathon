"""GSR -> YOLOv5 detection dataset builder (pre-model data validation).

Converts SoccerTrack v2 GSR ground truth into an Ultralytics-YOLOv5 dataset
(images/ + labels/ + data.yaml), so we can train/run YOLOv5 on real boxes as an
honest "the data is sound" check before SAM. The mirror has NO mot/, so we read
GSR `bbox_image` directly (the dataset's own create_yolo_dataset.py needs mot/).

WHY THIS IS CAREFUL ABOUT COORDINATES
-------------------------------------
GSR `bbox_image` boxes are in a per-frame image space (`img1/000001.jpg`) whose
exact pixels do NOT match the mirror's `calibrated_panorama` mp4 (verified: boxes
land in the black padding band). The normal `panorama` mp4 is the likely match but
is unverified. So this module does NOT assume an alignment:

  * `overlay_check()` draws GSR boxes on extracted video frames so you can EYEBALL
    alignment on Colab BEFORE exporting thousands of mislabeled images.
  * `build()` takes the frame source + the (w, h) the boxes are normalized against,
    so once alignment is confirmed the export is a one-liner.

YOLO label format (Ultralytics): one .txt per image, one line per box:
    <class_id> <x_center> <y_center> <w> <h>      # all normalized to [0,1]

Classes (collapsed from GSR categories): 0=person (player/goalkeeper/referee),
1=ball. `other` is dropped. This 2-class scheme matches the dataset's own YOLO
convention and is what YOLOv5 expects.

cv2 + numpy imported lazily so `make test` stays green with no heavy deps.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from src.data.loader import Frame, Match, load_match

# GSR role -> collapsed YOLO class id. Anything not here is skipped.
_ROLE_TO_CLASS: dict[str, int] = {
    "player": 0,
    "goalkeeper": 0,
    "referee": 0,
    "ball": 1,
}
CLASS_NAMES: dict[int, str] = {0: "person", 1: "ball"}


@dataclass(frozen=True)
class YoloBox:
    """One YOLO label line (normalized, already class-collapsed)."""

    cls: int
    xc: float
    yc: float
    w: float
    h: float

    def line(self) -> str:
        return f"{self.cls} {self.xc:.6f} {self.yc:.6f} {self.w:.6f} {self.h:.6f}"


def gsr_to_yolo_boxes(frame: Frame, img_w: int, img_h: int) -> list[YoloBox]:
    """Convert one GSR Frame's bbox_image entities to normalized YOLO boxes.

    `img_w/img_h` = the pixel size of the IMAGE these boxes index (the space the
    GSR boxes were annotated in). Boxes are clipped to [0,1]; out-of-frame or
    zero-area boxes are dropped.
    """
    out: list[YoloBox] = []
    for e in frame.entities:
        cls = _ROLE_TO_CLASS.get(e.role)
        if cls is None or e.bbox_image is None:
            continue
        x, y, w, h = e.bbox_image
        if w <= 0 or h <= 0:
            continue
        xc = (x + w / 2) / img_w
        yc = (y + h / 2) / img_h
        nw = w / img_w
        nh = h / img_h
        # Drop boxes whose center falls outside the frame; clip the rest.
        if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0):
            continue
        out.append(YoloBox(cls, _clip01(xc), _clip01(yc), _clip01(nw), _clip01(nh)))
    return out


def _clip01(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v


# ---- Frame sourcing ----------------------------------------------------------


def iter_labeled_frames(
    match: Match,
    half: int,
    *,
    stride: int = 1,
    limit: Optional[int] = None,
) -> Iterator[Frame]:
    """Yield GSR frames for a half, every `stride`-th, up to `limit` frames.

    A 90-min half is ~67k frames; for a YOLO sanity check you want a strided
    subset (e.g. stride=25 ≈ 1 fps), not all of them.
    """
    n = 0
    for i, frame in enumerate(match.gsr_frames(half)):
        if i % stride != 0:
            continue
        yield frame
        n += 1
        if limit is not None and n >= limit:
            return


def _read_frame(cap: Any, image_id: int) -> Any:
    """Grab the video frame for a GSR image_id (GSR is 1-based; cv2 is 0-based)."""
    import cv2

    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, image_id - 1))
    ok, img = cap.read()
    return img if ok else None


# ---- Diagnostic overlay (run on Colab BEFORE a full export) ------------------


def overlay_check(
    data_root: str | Path,
    match_id: str,
    video_path: str | Path,
    *,
    half: int = 2,
    image_ids: Iterable[int] = (1000, 5000, 20000),
    out_dir: str | Path = "outputs/yolo_check",
) -> list[Path]:
    """Draw GSR boxes on real extracted frames to verify coordinate alignment.

    Returns the written PNG paths. If boxes don't sit on players, the (img_w,img_h)
    you'd pass to build() is wrong for this video — fix before exporting.
    """
    import cv2

    match = load_match(data_root, match_id)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f"OpenCV could not open {video_path}")
    vw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for image_id in image_ids:
        frame = match.gsr_frame(half, image_id)
        if frame is None:
            continue
        img = _read_frame(cap, image_id)
        if img is None:
            continue
        for e in frame.entities:
            if e.bbox_image is None or e.role not in _ROLE_TO_CLASS:
                continue
            x, y, w, h = e.bbox_image
            col = (255, 255, 255) if e.role == "ball" else (80, 200, 80)
            cv2.rectangle(img, (x, y), (x + w, y + h), col, 2)
        p = out_dir / f"check_{match_id}_h{half}_f{image_id}_{vw}x{vh}.png"
        cv2.imwrite(str(p), img)
        written.append(p)
    cap.release()
    return written


# ---- Full export -------------------------------------------------------------


def build(
    data_root: str | Path,
    match_id: str,
    video_path: str | Path,
    out_dir: str | Path,
    *,
    half: int = 2,
    img_wh: Optional[tuple[int, int]] = None,
    stride: int = 25,
    limit: Optional[int] = None,
    val_every: int = 5,
) -> Path:
    """Export a YOLOv5 dataset from one match-half into `out_dir`.

    Writes images/{train,val}/, labels/{train,val}/, and data.yaml.

    `img_wh` = the (w,h) the GSR boxes are normalized against. Defaults to the
    VIDEO's native size — correct ONLY if the boxes align with this video (verify
    with overlay_check first!). Every `val_every`-th sampled frame goes to val.
    """
    import cv2

    match = load_match(data_root, match_id)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f"OpenCV could not open {video_path}")
    vw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    img_w, img_h = img_wh if img_wh else (vw, vh)

    out_dir = Path(out_dir)
    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)

    n_img = n_box = 0
    for k, frame in enumerate(iter_labeled_frames(match, half, stride=stride, limit=limit)):
        boxes = gsr_to_yolo_boxes(frame, img_w, img_h)
        if not boxes:
            continue
        img = _read_frame(cap, frame.image_id)
        if img is None:
            continue
        split = "val" if (k % val_every == 0) else "train"
        stem = f"{match_id}_h{half}_{frame.image_id:06d}"
        cv2.imwrite(str(out_dir / "images" / split / f"{stem}.jpg"), img)
        (out_dir / "labels" / split / f"{stem}.txt").write_text(
            "\n".join(b.line() for b in boxes) + "\n"
        )
        n_img += 1
        n_box += len(boxes)
    cap.release()

    yaml_path = _write_data_yaml(out_dir)
    print(f"[yolo] wrote {n_img} images / {n_box} boxes to {out_dir.resolve()}")
    print(f"[yolo] data.yaml: {yaml_path}")
    return out_dir


def _write_data_yaml(out_dir: Path) -> Path:
    """Write the Ultralytics data.yaml. PyYAML kept optional (manual format)."""
    names = "\n".join(f"  {i}: {n}" for i, n in sorted(CLASS_NAMES.items()))
    text = (
        f"path: {out_dir.resolve()}\n"
        "train: images/train\n"
        "val: images/val\n"
        f"nc: {len(CLASS_NAMES)}\n"
        "names:\n"
        f"{names}\n"
    )
    p = out_dir / "data.yaml"
    p.write_text(text)
    return p
