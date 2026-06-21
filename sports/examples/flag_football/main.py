"""Flag football player + ball tracking — Path A (generic COCO detector + ByteTrack).

Adapted from sports/examples/soccer/main.py, simplified for basketball:

- Soccer uses 3 SEPARATE soccer-domain checkpoints (ball/player/pitch detection)
  with custom 4-class labels (ball/goalkeeper/player/referee). Basketball-51 has
  no detection labels at all, and there's no basketball-specific pretrained
  checkpoint in this repo — so per CLAUDE.md §0/§3, Path A uses ONE generic
  COCO-pretrained Ultralytics model (default yolo11n.pt, ungated, auto-downloads)
  detecting COCO class 0 (person) and 32 (sports ball) in a single pass.
- No PITCH_DETECTION/RADAR modes — there is no basketball court keypoint model.
  (Soccer's pitch/radar modes are explicitly soccer-specific; CLAUDE.md §3 says
  not to expect them to transfer.)
- Team classification reuses `sports.common.team.TeamClassifier` UNCHANGED
  (SigLIP + UMAP + KMeans on player crops) — it's sport-agnostic, just clusters
  crops by appearance. No goalkeeper/referee sub-roles to resolve (COCO `person`
  doesn't distinguish them) — every detected person is a TeamClassifier input.
- Ball smoothing reuses `sports.common.ball.BallTracker`/`BallAnnotator`
  unchanged, fed from the SAME generic model's class-32 detections (no separate
  slicer/ball model needed since COCO already includes `sports ball`).

Usage (mirrors the soccer script):
    python main.py --source_video_path clip.mp4 --target_video_path out.mp4 \
        --device cuda --mode TEAM_CLASSIFICATION

Modes: PLAYER_DETECTION, BALL_DETECTION, PLAYER_TRACKING, TEAM_CLASSIFICATION,
POSSESSION. POSSESSION adds image-space trails and a proximity-based estimate;
it is not possession ground truth because no basketball court homography exists.
"""
# Direct script execution needs both repository package roots before first-party imports.
# ruff: noqa: E402
import argparse
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Iterator, List

REPO_ROOT = Path(__file__).resolve().parents[3]
for package_root in (REPO_ROOT, REPO_ROOT / "sports"):
    package_path = str(package_root)
    if package_path not in sys.path:
        sys.path.insert(0, package_path)

import cv2
import numpy as np
import supervision as sv
from sports.common.ball import BallAnnotator, BallTracker
from sports.common.possession import PossessionTracker
from sports.common.team import TeamClassifier
from sports.common.trace import TraceAnnotator
from tqdm import tqdm
from ultralytics import YOLO

from src.config import load_config
from src.integrations.tracking_observer import ObservedDetection, TrackingObserver

# Generic COCO-pretrained weights — ungated, auto-downloads. Override with a
# basketball-specific checkpoint here later (Phase 3) without touching the rest
# of this file: just point DETECTION_MODEL_PATH elsewhere.
DETECTION_MODEL_PATH = os.environ.get("FLAG_FOOTBALL_DETECTION_MODEL", "yolo11n.pt")


def parse_class_ids(name: str, default: str) -> tuple[int, ...]:
    try:
        values = tuple(dict.fromkeys(int(value.strip()) for value in os.environ.get(
            name, default).split(",") if value.strip()))
    except ValueError as exc:
        raise ValueError(f"{name} must be a comma-separated list of integer class ids") from exc
    if not values or any(value < 0 for value in values):
        raise ValueError(f"{name} must contain non-negative class ids")
    return values


PERSON_CLASS_IDS = parse_class_ids("FLAG_FOOTBALL_PERSON_CLASS_IDS", "0")  # COCO person
BALL_CLASS_IDS = parse_class_ids("FLAG_FOOTBALL_BALL_CLASS_IDS", "32")  # COCO sports ball
DETECTION_CLASS_IDS = tuple(dict.fromkeys(PERSON_CLASS_IDS + BALL_CLASS_IDS))

COLORS = ['#FF1493', '#00BFFF', '#FFD700']  # team 0, team 1, unresolved
COLOR_PALETTE = sv.ColorPalette.from_hex(COLORS)
BOX_ANNOTATOR = sv.BoxAnnotator(color=COLOR_PALETTE, thickness=2)
BOX_LABEL_ANNOTATOR = sv.LabelAnnotator(
    color=COLOR_PALETTE,
    text_color=sv.Color.from_hex('#FFFFFF'),
    text_padding=5,
    text_thickness=1,
)
ELLIPSE_ANNOTATOR = sv.EllipseAnnotator(color=COLOR_PALETTE, thickness=2)
ELLIPSE_LABEL_ANNOTATOR = sv.LabelAnnotator(
    color=COLOR_PALETTE,
    text_color=sv.Color.from_hex('#FFFFFF'),
    text_padding=5,
    text_thickness=1,
    text_position=sv.Position.BOTTOM_CENTER,
)

STRIDE = 30  # crop-collection stride for fitting the team classifier (shorter clips than soccer's)
POSSESSION_PIXEL_RADIUS = 80.0
POSSESSION_SWITCH_MARGIN = 20.0


class Mode(Enum):
    PLAYER_DETECTION = 'PLAYER_DETECTION'
    BALL_DETECTION = 'BALL_DETECTION'
    PLAYER_TRACKING = 'PLAYER_TRACKING'
    TEAM_CLASSIFICATION = 'TEAM_CLASSIFICATION'
    POSSESSION = 'POSSESSION'


def get_crops(frame: np.ndarray, detections: sv.Detections) -> List[np.ndarray]:
    return [sv.crop_image(frame, xyxy) for xyxy in detections.xyxy]


def to_observations(
    detections: sv.Detections,
    class_name: str,
    *,
    team_ids: np.ndarray | None = None,
) -> list[ObservedDetection]:
    """Translate Supervision detections without inventing missing confidence."""
    if detections.confidence is None:
        return []
    tracker_ids = detections.tracker_id
    anchors = (
        detections.get_anchors_coordinates(sv.Position.BOTTOM_CENTER)
        if tracker_ids is not None
        else None
    )
    result = []
    for index, confidence in enumerate(detections.confidence):
        track_id = int(tracker_ids[index]) if tracker_ids is not None else None
        x = float(anchors[index][0]) if anchors is not None else None
        y = float(anchors[index][1]) if anchors is not None else None
        team = int(team_ids[index]) if team_ids is not None else None
        result.append(ObservedDetection(
            class_name=class_name,
            confidence=float(confidence),
            track_id=track_id,
            x=x,
            y=y,
            team=team,
        ))
    return result


def tracking_observer(source_video_path: str) -> TrackingObserver:
    """Build the Redis/Arize fan-out; both remain no-ops unless enabled."""
    return TrackingObserver.for_video(load_config(), source_video_path, sport="flag_football")


def draw_possession_hud(
    frame: np.ndarray,
    possession_tracker: PossessionTracker,
) -> np.ndarray:
    """Draw estimated two-team possession percentages."""
    stats = possession_tracker.get_team_possession()
    pct_0 = float(stats["team_0_pct"])
    pct_1 = float(stats["team_1_pct"])
    height, width = frame.shape[:2]
    panel_width = min(360, max(220, width - 20))
    panel_height = 72
    x1 = max(10, width // 2 - panel_width // 2)
    y1 = min(20, max(4, height // 20))
    x2 = min(width - 10, x1 + panel_width)
    y2 = min(height - 4, y1 + panel_height)

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, dst=frame)
    cv2.putText(
        frame,
        "EST. POSSESSION",
        (x1 + 12, y1 + 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    bar_x1, bar_x2 = x1 + 12, x2 - 12
    bar_y1, bar_y2 = y1 + 33, y2 - 10
    total = pct_0 + pct_1
    split = (
        bar_x1 + int((bar_x2 - bar_x1) * pct_0 / total)
        if total
        else (bar_x1 + bar_x2) // 2
    )
    cv2.rectangle(frame, (bar_x1, bar_y1), (split, bar_y2), COLOR_PALETTE.by_idx(0).as_bgr(), -1)
    cv2.rectangle(frame, (split, bar_y1), (bar_x2, bar_y2), COLOR_PALETTE.by_idx(1).as_bgr(), -1)
    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (255, 255, 255), 1)
    cv2.putText(
        frame,
        f"{pct_0:.0f}%",
        (bar_x1 + 4, bar_y2 - 3),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    right_label = f"{pct_1:.0f}%"
    (label_width, _), _ = cv2.getTextSize(
        right_label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.putText(
        frame,
        right_label,
        (bar_x2 - label_width - 4, bar_y2 - 3),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return frame


def draw_holder_marker(frame: np.ndarray, center: np.ndarray, team_id: int | None) -> None:
    """Mark the current estimated holder at the player's foot anchor."""
    point = (int(center[0]), int(center[1]))
    color = COLOR_PALETTE.by_idx(team_id if team_id is not None else 2).as_bgr()
    cv2.ellipse(frame, point, (22, 9), 0, 0, 360, (255, 255, 255), 3, cv2.LINE_AA)
    cv2.ellipse(frame, point, (22, 9), 0, 0, 360, color, 2, cv2.LINE_AA)


def run_player_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    observer = tracking_observer(source_video_path)
    try:
        for frame_index, frame in enumerate(frame_generator):
            result = model(frame, classes=list(PERSON_CLASS_IDS), verbose=False)[0]
            detections = sv.Detections.from_ultralytics(result)
            observer.observe_frame(frame_index, to_observations(detections, "person"))
            annotated_frame = frame.copy()
            annotated_frame = BOX_ANNOTATOR.annotate(annotated_frame, detections)
            annotated_frame = BOX_LABEL_ANNOTATOR.annotate(annotated_frame, detections)
            yield annotated_frame
    finally:
        observer.close()


def run_ball_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    ball_tracker = BallTracker(buffer_size=20)
    ball_annotator = BallAnnotator(radius=6, buffer_size=10)
    observer = tracking_observer(source_video_path)
    try:
        for frame_index, frame in enumerate(frame_generator):
            result = model(frame, classes=list(BALL_CLASS_IDS), verbose=False)[0]
            detections = sv.Detections.from_ultralytics(result)
            detections = ball_tracker.update(detections)
            observer.observe_frame(frame_index, to_observations(detections, "sports ball"))
            annotated_frame = frame.copy()
            annotated_frame = ball_annotator.annotate(annotated_frame, detections)
            yield annotated_frame
    finally:
        observer.close()


def run_player_tracking(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    observer = tracking_observer(source_video_path)
    try:
        for frame_index, frame in enumerate(frame_generator):
            result = model(frame, classes=list(PERSON_CLASS_IDS), verbose=False)[0]
            detections = sv.Detections.from_ultralytics(result)
            detections = tracker.update_with_detections(detections)
            observer.observe_frame(frame_index, to_observations(detections, "person"))
            labels = [str(tracker_id) for tracker_id in detections.tracker_id]
            annotated_frame = frame.copy()
            annotated_frame = ELLIPSE_ANNOTATOR.annotate(annotated_frame, detections)
            annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
                annotated_frame, detections, labels=labels)
            yield annotated_frame
    finally:
        observer.close()


def run_team_classification(
    source_video_path: str,
    device: str,
    *,
    include_possession: bool = False,
) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)

    # Pass 1: collect player crops (strided) to fit the team classifier.
    crops: List[np.ndarray] = []
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path, stride=STRIDE)
    for frame in tqdm(frame_generator, desc='collecting crops'):
        result = model(frame, classes=list(PERSON_CLASS_IDS), verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        crops += get_crops(frame, detections)

    team_classifier = TeamClassifier(device=device)
    team_classifier.fit(crops)

    # Pass 2: track + classify + render every frame.
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    ball_tracker = BallTracker(buffer_size=20)
    ball_annotator = BallAnnotator(radius=6, buffer_size=10)
    video_info = sv.VideoInfo.from_video_path(source_video_path)
    trace_annotator = (
        TraceAnnotator(color_palette=COLOR_PALETTE, fps=video_info.fps)
        if include_possession
        else None
    )
    possession_tracker = (
        PossessionTracker(
            possession_radius=POSSESSION_PIXEL_RADIUS,
            hysteresis_frames=3,
            switch_margin=POSSESSION_SWITCH_MARGIN,
        )
        if include_possession
        else None
    )
    observer = tracking_observer(source_video_path)
    try:
        for frame_index, frame in enumerate(frame_generator):
            result = model(frame, classes=list(DETECTION_CLASS_IDS), verbose=False)[0]
            detections = sv.Detections.from_ultralytics(result)

            players = detections[np.isin(detections.class_id, PERSON_CLASS_IDS)]
            players = tracker.update_with_detections(players)
            player_crops = get_crops(frame, players)
            color_lookup = (
                team_classifier.predict(player_crops)
                if player_crops
                else np.array([], dtype=int)
            )

            ball = detections[np.isin(detections.class_id, BALL_CLASS_IDS)]
            ball = ball_tracker.update(ball)

            observations = to_observations(
                players, "person", team_ids=color_lookup
            ) + to_observations(ball, "sports ball")
            observer.observe_frame(frame_index, observations)

            player_anchors = players.get_anchors_coordinates(sv.Position.BOTTOM_CENTER)
            holder_id = holder_team = None
            if possession_tracker is not None and trace_annotator is not None:
                ball_anchors = ball.get_anchors_coordinates(sv.Position.CENTER)
                ball_xy = ball_anchors[0] if len(ball_anchors) else None
                tracker_ids = (
                    players.tracker_id
                    if players.tracker_id is not None
                    else np.array([], dtype=int)
                )
                holder_id, holder_team = possession_tracker.update(
                    ball_xy=ball_xy,
                    players_xy=player_anchors,
                    tracker_ids=tracker_ids,
                    team_ids=color_lookup,
                )
                trace_annotator.update(players, color_lookup)

            labels = [str(tracker_id) for tracker_id in players.tracker_id]
            annotated_frame = frame.copy()
            if trace_annotator is not None:
                annotated_frame = trace_annotator.annotate(annotated_frame)
            annotated_frame = ELLIPSE_ANNOTATOR.annotate(
                annotated_frame, players, custom_color_lookup=color_lookup)
            annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
                annotated_frame, players, labels, custom_color_lookup=color_lookup)
            annotated_frame = ball_annotator.annotate(annotated_frame, ball)
            if holder_id is not None and players.tracker_id is not None:
                holder_matches = np.where(players.tracker_id == holder_id)[0]
                if len(holder_matches):
                    draw_holder_marker(
                        annotated_frame,
                        player_anchors[holder_matches[0]],
                        holder_team,
                    )
            if possession_tracker is not None:
                annotated_frame = draw_possession_hud(
                    annotated_frame, possession_tracker)
            yield annotated_frame
    finally:
        observer.close()


def main(source_video_path: str, target_video_path: str, device: str, mode: Mode) -> None:
    if mode == Mode.PLAYER_DETECTION:
        frame_generator = run_player_detection(source_video_path, device)
    elif mode == Mode.BALL_DETECTION:
        frame_generator = run_ball_detection(source_video_path, device)
    elif mode == Mode.PLAYER_TRACKING:
        frame_generator = run_player_tracking(source_video_path, device)
    elif mode == Mode.TEAM_CLASSIFICATION:
        frame_generator = run_team_classification(source_video_path, device)
    elif mode == Mode.POSSESSION:
        frame_generator = run_team_classification(
            source_video_path, device, include_possession=True)
    else:
        raise NotImplementedError(f"Mode {mode} is not implemented.")

    video_info = sv.VideoInfo.from_video_path(source_video_path)
    with sv.VideoSink(target_video_path, video_info) as sink:
        for frame in tqdm(frame_generator, desc='processing video'):
            sink.write_frame(frame)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flag football player + ball tracking (Path A).')
    parser.add_argument('--source_video_path', type=str, required=True)
    parser.add_argument('--target_video_path', type=str, required=True)
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--mode', type=Mode, default=Mode.TEAM_CLASSIFICATION)
    args = parser.parse_args()
    main(
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path,
        device=args.device,
        mode=args.mode,
    )
