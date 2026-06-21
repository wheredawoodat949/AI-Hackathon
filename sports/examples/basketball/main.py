"""Basketball player + ball tracking — Phase 1 (Path A), CLAUDE.md §4/§7/§8.

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

Modes: PLAYER_DETECTION, BALL_DETECTION, PLAYER_TRACKING, TEAM_CLASSIFICATION.
"""
import argparse
import os
from enum import Enum
from typing import Iterator, List

import numpy as np
import supervision as sv
from tqdm import tqdm
from ultralytics import YOLO

from sports.common.ball import BallAnnotator, BallTracker
from sports.common.team import TeamClassifier

# Generic COCO-pretrained weights — ungated, auto-downloads. Override with a
# basketball-specific checkpoint here later (Phase 3) without touching the rest
# of this file: just point DETECTION_MODEL_PATH elsewhere.
DETECTION_MODEL_PATH = os.environ.get("BASKETBALL_DETECTION_MODEL", "yolo11n.pt")

PERSON_CLASS_ID = 0     # COCO
BALL_CLASS_ID = 32      # COCO "sports ball"

COLORS = ['#FF1493', '#00BFFF', '#FFD700']  # team 0, team 1, unresolved
BOX_ANNOTATOR = sv.BoxAnnotator(color=sv.ColorPalette.from_hex(COLORS), thickness=2)
BOX_LABEL_ANNOTATOR = sv.LabelAnnotator(
    color=sv.ColorPalette.from_hex(COLORS),
    text_color=sv.Color.from_hex('#FFFFFF'),
    text_padding=5,
    text_thickness=1,
)
ELLIPSE_ANNOTATOR = sv.EllipseAnnotator(color=sv.ColorPalette.from_hex(COLORS), thickness=2)
ELLIPSE_LABEL_ANNOTATOR = sv.LabelAnnotator(
    color=sv.ColorPalette.from_hex(COLORS),
    text_color=sv.Color.from_hex('#FFFFFF'),
    text_padding=5,
    text_thickness=1,
    text_position=sv.Position.BOTTOM_CENTER,
)

STRIDE = 30  # crop-collection stride for fitting the team classifier (shorter clips than soccer's)


class Mode(Enum):
    PLAYER_DETECTION = 'PLAYER_DETECTION'
    BALL_DETECTION = 'BALL_DETECTION'
    PLAYER_TRACKING = 'PLAYER_TRACKING'
    TEAM_CLASSIFICATION = 'TEAM_CLASSIFICATION'


def get_crops(frame: np.ndarray, detections: sv.Detections) -> List[np.ndarray]:
    return [sv.crop_image(frame, xyxy) for xyxy in detections.xyxy]


def run_player_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    for frame in frame_generator:
        result = model(frame, classes=[PERSON_CLASS_ID], verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        annotated_frame = frame.copy()
        annotated_frame = BOX_ANNOTATOR.annotate(annotated_frame, detections)
        annotated_frame = BOX_LABEL_ANNOTATOR.annotate(annotated_frame, detections)
        yield annotated_frame


def run_ball_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    ball_tracker = BallTracker(buffer_size=20)
    ball_annotator = BallAnnotator(radius=6, buffer_size=10)
    for frame in frame_generator:
        result = model(frame, classes=[BALL_CLASS_ID], verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = ball_tracker.update(detections)
        annotated_frame = frame.copy()
        annotated_frame = ball_annotator.annotate(annotated_frame, detections)
        yield annotated_frame


def run_player_tracking(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    for frame in frame_generator:
        result = model(frame, classes=[PERSON_CLASS_ID], verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = tracker.update_with_detections(detections)
        labels = [str(tracker_id) for tracker_id in detections.tracker_id]
        annotated_frame = frame.copy()
        annotated_frame = ELLIPSE_ANNOTATOR.annotate(annotated_frame, detections)
        annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(annotated_frame, detections, labels=labels)
        yield annotated_frame


def run_team_classification(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    model = YOLO(DETECTION_MODEL_PATH).to(device=device)

    # Pass 1: collect player crops (strided) to fit the team classifier.
    crops: List[np.ndarray] = []
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path, stride=STRIDE)
    for frame in tqdm(frame_generator, desc='collecting crops'):
        result = model(frame, classes=[PERSON_CLASS_ID], verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        crops += get_crops(frame, detections)

    team_classifier = TeamClassifier(device=device)
    team_classifier.fit(crops)

    # Pass 2: track + classify + render every frame.
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    ball_tracker = BallTracker(buffer_size=20)
    ball_annotator = BallAnnotator(radius=6, buffer_size=10)
    for frame in frame_generator:
        result = model(frame, classes=[PERSON_CLASS_ID, BALL_CLASS_ID], verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)

        players = detections[detections.class_id == PERSON_CLASS_ID]
        players = tracker.update_with_detections(players)
        player_crops = get_crops(frame, players)
        color_lookup = team_classifier.predict(player_crops) if player_crops else np.array([])

        ball = detections[detections.class_id == BALL_CLASS_ID]
        ball = ball_tracker.update(ball)

        labels = [str(tracker_id) for tracker_id in players.tracker_id]
        annotated_frame = frame.copy()
        annotated_frame = ELLIPSE_ANNOTATOR.annotate(
            annotated_frame, players, custom_color_lookup=color_lookup)
        annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
            annotated_frame, players, labels, custom_color_lookup=color_lookup)
        annotated_frame = ball_annotator.annotate(annotated_frame, ball)
        yield annotated_frame


def main(source_video_path: str, target_video_path: str, device: str, mode: Mode) -> None:
    if mode == Mode.PLAYER_DETECTION:
        frame_generator = run_player_detection(source_video_path, device)
    elif mode == Mode.BALL_DETECTION:
        frame_generator = run_ball_detection(source_video_path, device)
    elif mode == Mode.PLAYER_TRACKING:
        frame_generator = run_player_tracking(source_video_path, device)
    elif mode == Mode.TEAM_CLASSIFICATION:
        frame_generator = run_team_classification(source_video_path, device)
    else:
        raise NotImplementedError(f"Mode {mode} is not implemented.")

    video_info = sv.VideoInfo.from_video_path(source_video_path)
    with sv.VideoSink(target_video_path, video_info) as sink:
        for frame in tqdm(frame_generator, desc='processing video'):
            sink.write_frame(frame)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Basketball player + ball tracking (Path A).')
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
