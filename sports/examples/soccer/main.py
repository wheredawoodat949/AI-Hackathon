import argparse
from enum import Enum
from typing import Iterator, List

import os
import cv2
import numpy as np
import supervision as sv
from tqdm import tqdm
from ultralytics import YOLO

from sports.annotators.soccer import draw_pitch, draw_points_on_pitch
from sports.common.ball import BallTracker, BallAnnotator
from sports.common.possession import PossessionTracker
from sports.common.team import TeamClassifier
from sports.common.trace import TraceAnnotator
from sports.common.view import ViewTransformer
from sports.configs.soccer import SoccerPitchConfiguration

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DETECTION_MODEL_PATH = os.path.join(PARENT_DIR, 'data/football-player-detection.pt')
PITCH_DETECTION_MODEL_PATH = os.path.join(PARENT_DIR, 'data/football-pitch-detection.pt')
BALL_DETECTION_MODEL_PATH = os.path.join(PARENT_DIR, 'data/football-ball-detection.pt')

BALL_CLASS_ID = 0
GOALKEEPER_CLASS_ID = 1
PLAYER_CLASS_ID = 2
REFEREE_CLASS_ID = 3

STRIDE = 60
CONFIG = SoccerPitchConfiguration()

# Possession tuning. The pitch config is expressed in centimetres (width
# 7000 cm = 70 m), so the possession radius is in centimetres: ~200 cm (2 m) is
# a sensible "the ball is at this player's feet" threshold. When the pitch
# homography is unavailable for a frame we fall back to pixel-space distance and
# treat POSSESSION_PIXEL_FALLBACK_RADIUS pixels as equivalent to that radius.
POSSESSION_RADIUS = 200.0
POSSESSION_PIXEL_FALLBACK_RADIUS = 80.0
# Ball detection compute tradeoff: the slicer (run_ball_detection) runs many
# 640x640 tiled inferences per frame. For the combined possession mode we
# default to a single full-frame inference (imgsz=1280) smoothed by BallTracker,
# which is far cheaper. Flip this to True to opt into the higher-cost slicer.
USE_BALL_SLICER = False

COLORS = ['#FF1493', '#00BFFF', '#FF6347', '#FFD700']
COLOR_PALETTE = sv.ColorPalette.from_hex(COLORS)
VERTEX_LABEL_ANNOTATOR = sv.VertexLabelAnnotator(
    color=[sv.Color.from_hex(color) for color in CONFIG.colors],
    text_color=sv.Color.from_hex('#FFFFFF'),
    border_radius=5,
    text_thickness=1,
    text_scale=0.5,
    text_padding=5,
)
EDGE_ANNOTATOR = sv.EdgeAnnotator(
    color=sv.Color.from_hex('#FF1493'),
    thickness=2,
    edges=CONFIG.edges,
)
TRIANGLE_ANNOTATOR = sv.TriangleAnnotator(
    color=sv.Color.from_hex('#FF1493'),
    base=20,
    height=15,
)
BOX_ANNOTATOR = sv.BoxAnnotator(
    color=sv.ColorPalette.from_hex(COLORS),
    thickness=2
)
ELLIPSE_ANNOTATOR = sv.EllipseAnnotator(
    color=sv.ColorPalette.from_hex(COLORS),
    thickness=2
)
BOX_LABEL_ANNOTATOR = sv.LabelAnnotator(
    color=sv.ColorPalette.from_hex(COLORS),
    text_color=sv.Color.from_hex('#FFFFFF'),
    text_padding=5,
    text_thickness=1,
)
ELLIPSE_LABEL_ANNOTATOR = sv.LabelAnnotator(
    color=sv.ColorPalette.from_hex(COLORS),
    text_color=sv.Color.from_hex('#FFFFFF'),
    text_padding=5,
    text_thickness=1,
    text_position=sv.Position.BOTTOM_CENTER,
)


class Mode(Enum):
    """
    Enum class representing different modes of operation for Soccer AI video analysis.
    """
    PITCH_DETECTION = 'PITCH_DETECTION'
    PLAYER_DETECTION = 'PLAYER_DETECTION'
    BALL_DETECTION = 'BALL_DETECTION'
    PLAYER_TRACKING = 'PLAYER_TRACKING'
    TEAM_CLASSIFICATION = 'TEAM_CLASSIFICATION'
    RADAR = 'RADAR'
    POSSESSION = 'POSSESSION'


def get_crops(frame: np.ndarray, detections: sv.Detections) -> List[np.ndarray]:
    """
    Extract crops from the frame based on detected bounding boxes.

    Args:
        frame (np.ndarray): The frame from which to extract crops.
        detections (sv.Detections): Detected objects with bounding boxes.

    Returns:
        List[np.ndarray]: List of cropped images.
    """
    return [sv.crop_image(frame, xyxy) for xyxy in detections.xyxy]


def resolve_goalkeepers_team_id(
    players: sv.Detections,
    players_team_id: np.array,
    goalkeepers: sv.Detections
) -> np.ndarray:
    """
    Resolve the team IDs for detected goalkeepers based on the proximity to team
    centroids.

    Args:
        players (sv.Detections): Detections of all players.
        players_team_id (np.array): Array containing team IDs of detected players.
        goalkeepers (sv.Detections): Detections of goalkeepers.

    Returns:
        np.ndarray: Array containing team IDs for the detected goalkeepers.

    This function calculates the centroids of the two teams based on the positions of
    the players. Then, it assigns each goalkeeper to the nearest team's centroid by
    calculating the distance between each goalkeeper and the centroids of the two teams.
    """
    goalkeepers_xy = goalkeepers.get_anchors_coordinates(sv.Position.BOTTOM_CENTER)
    players_xy = players.get_anchors_coordinates(sv.Position.BOTTOM_CENTER)
    team_0_centroid = players_xy[players_team_id == 0].mean(axis=0)
    team_1_centroid = players_xy[players_team_id == 1].mean(axis=0)
    goalkeepers_team_id = []
    for goalkeeper_xy in goalkeepers_xy:
        dist_0 = np.linalg.norm(goalkeeper_xy - team_0_centroid)
        dist_1 = np.linalg.norm(goalkeeper_xy - team_1_centroid)
        goalkeepers_team_id.append(0 if dist_0 < dist_1 else 1)
    return np.array(goalkeepers_team_id)


def render_radar(
    detections: sv.Detections,
    keypoints: sv.KeyPoints,
    color_lookup: np.ndarray
) -> np.ndarray:
    mask = (keypoints.xy[0][:, 0] > 1) & (keypoints.xy[0][:, 1] > 1)
    transformer = ViewTransformer(
        source=keypoints.xy[0][mask].astype(np.float32),
        target=np.array(CONFIG.vertices)[mask].astype(np.float32)
    )
    xy = detections.get_anchors_coordinates(anchor=sv.Position.BOTTOM_CENTER)
    transformed_xy = transformer.transform_points(points=xy)

    radar = draw_pitch(config=CONFIG)
    radar = draw_points_on_pitch(
        config=CONFIG, xy=transformed_xy[color_lookup == 0],
        face_color=sv.Color.from_hex(COLORS[0]), radius=20, pitch=radar)
    radar = draw_points_on_pitch(
        config=CONFIG, xy=transformed_xy[color_lookup == 1],
        face_color=sv.Color.from_hex(COLORS[1]), radius=20, pitch=radar)
    radar = draw_points_on_pitch(
        config=CONFIG, xy=transformed_xy[color_lookup == 2],
        face_color=sv.Color.from_hex(COLORS[2]), radius=20, pitch=radar)
    radar = draw_points_on_pitch(
        config=CONFIG, xy=transformed_xy[color_lookup == 3],
        face_color=sv.Color.from_hex(COLORS[3]), radius=20, pitch=radar)
    return radar


def run_pitch_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    """
    Run pitch detection on a video and yield annotated frames.

    Args:
        source_video_path (str): Path to the source video.
        device (str): Device to run the model on (e.g., 'cpu', 'cuda').

    Yields:
        Iterator[np.ndarray]: Iterator over annotated frames.
    """
    pitch_detection_model = YOLO(PITCH_DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    for frame in frame_generator:
        result = pitch_detection_model(frame, verbose=False)[0]
        keypoints = sv.KeyPoints.from_ultralytics(result)

        annotated_frame = frame.copy()
        annotated_frame = VERTEX_LABEL_ANNOTATOR.annotate(
            annotated_frame, keypoints, CONFIG.labels)
        yield annotated_frame


def run_player_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    """
    Run player detection on a video and yield annotated frames.

    Args:
        source_video_path (str): Path to the source video.
        device (str): Device to run the model on (e.g., 'cpu', 'cuda').

    Yields:
        Iterator[np.ndarray]: Iterator over annotated frames.
    """
    player_detection_model = YOLO(PLAYER_DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    for frame in frame_generator:
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)

        annotated_frame = frame.copy()
        annotated_frame = BOX_ANNOTATOR.annotate(annotated_frame, detections)
        annotated_frame = BOX_LABEL_ANNOTATOR.annotate(annotated_frame, detections)
        yield annotated_frame


def run_ball_detection(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    """
    Run ball detection on a video and yield annotated frames.

    Args:
        source_video_path (str): Path to the source video.
        device (str): Device to run the model on (e.g., 'cpu', 'cuda').

    Yields:
        Iterator[np.ndarray]: Iterator over annotated frames.
    """
    ball_detection_model = YOLO(BALL_DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    ball_tracker = BallTracker(buffer_size=20)
    ball_annotator = BallAnnotator(radius=6, buffer_size=10)

    def callback(image_slice: np.ndarray) -> sv.Detections:
        result = ball_detection_model(image_slice, imgsz=640, verbose=False)[0]
        return sv.Detections.from_ultralytics(result)

    slicer = sv.InferenceSlicer(
        callback=callback,
        overlap_filter_strategy=sv.OverlapFilter.NONE,
        slice_wh=(640, 640),
    )

    for frame in frame_generator:
        detections = slicer(frame).with_nms(threshold=0.1)
        detections = ball_tracker.update(detections)
        annotated_frame = frame.copy()
        annotated_frame = ball_annotator.annotate(annotated_frame, detections)
        yield annotated_frame


def run_player_tracking(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    """
    Run player tracking on a video and yield annotated frames with tracked players.

    Args:
        source_video_path (str): Path to the source video.
        device (str): Device to run the model on (e.g., 'cpu', 'cuda').

    Yields:
        Iterator[np.ndarray]: Iterator over annotated frames.
    """
    player_detection_model = YOLO(PLAYER_DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    for frame in frame_generator:
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = tracker.update_with_detections(detections)

        labels = [str(tracker_id) for tracker_id in detections.tracker_id]

        annotated_frame = frame.copy()
        annotated_frame = ELLIPSE_ANNOTATOR.annotate(annotated_frame, detections)
        annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
            annotated_frame, detections, labels=labels)
        yield annotated_frame


def run_team_classification(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    """
    Run team classification on a video and yield annotated frames with team colors.

    Args:
        source_video_path (str): Path to the source video.
        device (str): Device to run the model on (e.g., 'cpu', 'cuda').

    Yields:
        Iterator[np.ndarray]: Iterator over annotated frames.
    """
    player_detection_model = YOLO(PLAYER_DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(
        source_path=source_video_path, stride=STRIDE)

    crops = []
    for frame in tqdm(frame_generator, desc='collecting crops'):
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        crops += get_crops(frame, detections[detections.class_id == PLAYER_CLASS_ID])

    team_classifier = TeamClassifier(device=device)
    team_classifier.fit(crops)

    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    for frame in frame_generator:
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = tracker.update_with_detections(detections)

        players = detections[detections.class_id == PLAYER_CLASS_ID]
        crops = get_crops(frame, players)
        players_team_id = team_classifier.predict(crops)

        goalkeepers = detections[detections.class_id == GOALKEEPER_CLASS_ID]
        goalkeepers_team_id = resolve_goalkeepers_team_id(
            players, players_team_id, goalkeepers)

        referees = detections[detections.class_id == REFEREE_CLASS_ID]

        detections = sv.Detections.merge([players, goalkeepers, referees])
        color_lookup = np.array(
                players_team_id.tolist() +
                goalkeepers_team_id.tolist() +
                [REFEREE_CLASS_ID] * len(referees)
        )
        labels = [str(tracker_id) for tracker_id in detections.tracker_id]

        annotated_frame = frame.copy()
        annotated_frame = ELLIPSE_ANNOTATOR.annotate(
            annotated_frame, detections, custom_color_lookup=color_lookup)
        annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
            annotated_frame, detections, labels, custom_color_lookup=color_lookup)
        yield annotated_frame


def run_radar(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    player_detection_model = YOLO(PLAYER_DETECTION_MODEL_PATH).to(device=device)
    pitch_detection_model = YOLO(PITCH_DETECTION_MODEL_PATH).to(device=device)
    frame_generator = sv.get_video_frames_generator(
        source_path=source_video_path, stride=STRIDE)

    crops = []
    for frame in tqdm(frame_generator, desc='collecting crops'):
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        crops += get_crops(frame, detections[detections.class_id == PLAYER_CLASS_ID])

    team_classifier = TeamClassifier(device=device)
    team_classifier.fit(crops)

    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    for frame in frame_generator:
        result = pitch_detection_model(frame, verbose=False)[0]
        keypoints = sv.KeyPoints.from_ultralytics(result)
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = tracker.update_with_detections(detections)

        players = detections[detections.class_id == PLAYER_CLASS_ID]
        crops = get_crops(frame, players)
        players_team_id = team_classifier.predict(crops)

        goalkeepers = detections[detections.class_id == GOALKEEPER_CLASS_ID]
        goalkeepers_team_id = resolve_goalkeepers_team_id(
            players, players_team_id, goalkeepers)

        referees = detections[detections.class_id == REFEREE_CLASS_ID]

        detections = sv.Detections.merge([players, goalkeepers, referees])
        color_lookup = np.array(
            players_team_id.tolist() +
            goalkeepers_team_id.tolist() +
            [REFEREE_CLASS_ID] * len(referees)
        )
        labels = [str(tracker_id) for tracker_id in detections.tracker_id]

        annotated_frame = frame.copy()
        annotated_frame = ELLIPSE_ANNOTATOR.annotate(
            annotated_frame, detections, custom_color_lookup=color_lookup)
        annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
            annotated_frame, detections, labels,
            custom_color_lookup=color_lookup)

        h, w, _ = frame.shape
        radar = render_radar(detections, keypoints, color_lookup)
        radar = sv.resize_image(radar, (w // 2, h // 2))
        radar_h, radar_w, _ = radar.shape
        rect = sv.Rect(
            x=w // 2 - radar_w // 2,
            y=h - radar_h,
            width=radar_w,
            height=radar_h
        )
        annotated_frame = sv.draw_image(annotated_frame, radar, opacity=0.5, rect=rect)
        yield annotated_frame


def draw_rounded_panel(
    frame: np.ndarray,
    top_left: tuple,
    bottom_right: tuple,
    color: tuple,
    radius: int = 12,
    opacity: float = 0.55,
) -> np.ndarray:
    """Draw a semi-transparent rounded filled panel via a single blend."""
    overlay = frame.copy()
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    for cx, cy in ((x1 + radius, y1 + radius), (x2 - radius, y1 + radius),
                   (x1 + radius, y2 - radius), (x2 - radius, y2 - radius)):
        cv2.circle(overlay, (cx, cy), radius, color, -1, lineType=cv2.LINE_AA)
    return cv2.addWeighted(overlay, opacity, frame, 1.0 - opacity, 0.0)


def draw_possession_hud(
    frame: np.ndarray,
    possession_tracker: PossessionTracker,
) -> np.ndarray:
    """Draw a scoreboard-style possession HUD (top-centre split bar)."""
    stats = possession_tracker.get_team_possession()
    pct_0 = stats['team_0_pct']
    pct_1 = stats['team_1_pct']

    h, w, _ = frame.shape
    panel_w = 360
    panel_h = 78
    x1 = w // 2 - panel_w // 2
    y1 = 20
    x2 = x1 + panel_w
    y2 = y1 + panel_h

    frame = draw_rounded_panel(frame, (x1, y1), (x2, y2), (20, 20, 20), radius=14)

    color_0 = sv.Color.from_hex(COLORS[0]).as_bgr()
    color_1 = sv.Color.from_hex(COLORS[1]).as_bgr()
    white = (255, 255, 255)

    cv2.putText(frame, 'POSSESSION', (x1 + 16, y1 + 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, white, 1, cv2.LINE_AA)

    # Single split bar coloured by team, widths proportional to possession.
    bar_x1 = x1 + 16
    bar_x2 = x2 - 16
    bar_y1 = y1 + 38
    bar_y2 = y1 + 58
    bar_w = bar_x2 - bar_x1
    split = bar_x1 + int(bar_w * (pct_0 / 100.0)) if (pct_0 + pct_1) > 0 \
        else bar_x1 + bar_w // 2
    cv2.rectangle(frame, (bar_x1, bar_y1), (split, bar_y2), color_0, -1)
    cv2.rectangle(frame, (split, bar_y1), (bar_x2, bar_y2), color_1, -1)
    cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2), white, 1, cv2.LINE_AA)

    cv2.putText(frame, f'{pct_0:.0f}%', (bar_x1 + 4, bar_y2 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, white, 1, cv2.LINE_AA)
    text_1 = f'{pct_1:.0f}%'
    (tw, _), _ = cv2.getTextSize(text_1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.putText(frame, text_1, (bar_x2 - tw - 4, bar_y2 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, white, 1, cv2.LINE_AA)
    return frame


def draw_holder_marker(
    frame: np.ndarray,
    center: tuple,
    color: tuple,
) -> np.ndarray:
    """Highlight the current ball holder with an anti-aliased ring marker."""
    cx, cy = int(center[0]), int(center[1])
    cv2.ellipse(frame, (cx, cy), (22, 9), 0, 0, 360, (255, 255, 255), 3,
                lineType=cv2.LINE_AA)
    cv2.ellipse(frame, (cx, cy), (22, 9), 0, 0, 360, color, 2,
                lineType=cv2.LINE_AA)
    return frame


def run_possession(source_video_path: str, device: str) -> Iterator[np.ndarray]:
    """Run combined possession analysis and yield annotated frames.

    Modelled on ``run_radar``: first collect player crops at STRIDE and fit the
    TeamClassifier, then per frame run player detection + ByteTrack + team
    classification + (cheap) ball detection, compute possession in pitch space
    and render movement traces, a ball-holder marker and a possession HUD.
    """
    player_detection_model = YOLO(PLAYER_DETECTION_MODEL_PATH).to(device=device)
    pitch_detection_model = YOLO(PITCH_DETECTION_MODEL_PATH).to(device=device)
    ball_detection_model = YOLO(BALL_DETECTION_MODEL_PATH).to(device=device)

    video_info = sv.VideoInfo.from_video_path(source_video_path)

    frame_generator = sv.get_video_frames_generator(
        source_path=source_video_path, stride=STRIDE)
    crops = []
    for frame in tqdm(frame_generator, desc='collecting crops'):
        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        crops += get_crops(frame, detections[detections.class_id == PLAYER_CLASS_ID])

    team_classifier = TeamClassifier(device=device)
    team_classifier.fit(crops)

    # Optional high-cost tiled ball slicer (disabled by default, see constant).
    ball_slicer = None
    if USE_BALL_SLICER:
        def _ball_callback(image_slice: np.ndarray) -> sv.Detections:
            result = ball_detection_model(image_slice, imgsz=640, verbose=False)[0]
            return sv.Detections.from_ultralytics(result)

        ball_slicer = sv.InferenceSlicer(
            callback=_ball_callback,
            overlap_filter_strategy=sv.OverlapFilter.NONE,
            slice_wh=(640, 640),
        )

    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    tracker = sv.ByteTrack(minimum_consecutive_frames=3)
    ball_tracker = BallTracker(buffer_size=20)
    ball_annotator = BallAnnotator(radius=6, buffer_size=10)
    trace_annotator = TraceAnnotator(
        color_palette=COLOR_PALETTE, fps=video_info.fps)
    possession_tracker = PossessionTracker(possession_radius=POSSESSION_RADIUS)
    pixel_scale = POSSESSION_RADIUS / POSSESSION_PIXEL_FALLBACK_RADIUS

    for frame in frame_generator:
        pitch_result = pitch_detection_model(frame, verbose=False)[0]
        keypoints = sv.KeyPoints.from_ultralytics(pitch_result)

        result = player_detection_model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(result)
        detections = tracker.update_with_detections(detections)

        players = detections[detections.class_id == PLAYER_CLASS_ID]
        players_crops = get_crops(frame, players)
        players_team_id = team_classifier.predict(players_crops)

        goalkeepers = detections[detections.class_id == GOALKEEPER_CLASS_ID]
        goalkeepers_team_id = resolve_goalkeepers_team_id(
            players, players_team_id, goalkeepers)

        referees = detections[detections.class_id == REFEREE_CLASS_ID]

        # Ball: a single full-frame inference (cheap) smoothed by BallTracker,
        # which also bridges short gaps where the ball is briefly undetected.
        if ball_slicer is not None:
            ball_detections = ball_slicer(frame).with_nms(threshold=0.1)
        else:
            ball_result = ball_detection_model(frame, imgsz=1280, verbose=False)[0]
            ball_detections = sv.Detections.from_ultralytics(ball_result)
        ball_detections = ball_tracker.update(ball_detections)

        # Field players (team 0/1) are the possession candidates.
        field_players = sv.Detections.merge([players, goalkeepers])
        field_team_id = np.array(
            players_team_id.tolist() + goalkeepers_team_id.tolist())
        field_ids = (
            field_players.tracker_id
            if field_players.tracker_id is not None
            else np.array([], dtype=int)
        )

        player_xy_img = field_players.get_anchors_coordinates(
            sv.Position.BOTTOM_CENTER)
        ball_xy_img = (
            ball_detections.get_anchors_coordinates(sv.Position.CENTER)[0]
            if len(ball_detections) else None
        )

        # Prefer pitch-space distance (perspective makes pixels unreliable).
        transformer = None
        valid_mask = (keypoints.xy[0][:, 0] > 1) & (keypoints.xy[0][:, 1] > 1)
        if int(valid_mask.sum()) >= 4:
            try:
                transformer = ViewTransformer(
                    source=keypoints.xy[0][valid_mask].astype(np.float32),
                    target=np.array(CONFIG.vertices)[valid_mask].astype(np.float32),
                )
            except ValueError:
                transformer = None

        if transformer is not None and len(player_xy_img):
            poss_player_xy = transformer.transform_points(player_xy_img)
            poss_ball_xy = (
                transformer.transform_points(
                    np.asarray(ball_xy_img, dtype=np.float32).reshape(1, 2))[0]
                if ball_xy_img is not None else None
            )
        else:
            # Fallback: pixel space, scaled so the pixel radius maps onto the
            # pitch radius the PossessionTracker was configured with.
            poss_player_xy = player_xy_img * pixel_scale if len(player_xy_img) else player_xy_img
            poss_ball_xy = (
                np.asarray(ball_xy_img, dtype=np.float32) * pixel_scale
                if ball_xy_img is not None else None
            )

        possession_tracker.update(
            ball_xy=poss_ball_xy,
            players_xy=poss_player_xy,
            tracker_ids=field_ids,
            team_ids=field_team_id,
        )
        holder_id, holder_team = possession_tracker.current_holder()

        merged = sv.Detections.merge([players, goalkeepers, referees])
        color_lookup = np.array(
            players_team_id.tolist() +
            goalkeepers_team_id.tolist() +
            [REFEREE_CLASS_ID] * len(referees)
        )
        labels = [str(tracker_id) for tracker_id in merged.tracker_id]

        # Movement traces are updated every frame and drawn beneath players.
        trace_annotator.update(field_players, field_team_id)

        annotated_frame = frame.copy()
        annotated_frame = trace_annotator.annotate(annotated_frame)
        annotated_frame = ELLIPSE_ANNOTATOR.annotate(
            annotated_frame, merged, custom_color_lookup=color_lookup)
        annotated_frame = ELLIPSE_LABEL_ANNOTATOR.annotate(
            annotated_frame, merged, labels, custom_color_lookup=color_lookup)
        annotated_frame = ball_annotator.annotate(annotated_frame, ball_detections)

        if holder_id is not None and len(field_ids):
            match = np.where(field_ids == holder_id)[0]
            if len(match):
                holder_color = COLOR_PALETTE.by_idx(
                    int(holder_team) if holder_team is not None else 0).as_bgr()
                annotated_frame = draw_holder_marker(
                    annotated_frame, player_xy_img[match[0]], holder_color)

        annotated_frame = draw_possession_hud(annotated_frame, possession_tracker)
        yield annotated_frame


def main(source_video_path: str, target_video_path: str, device: str, mode: Mode) -> None:
    if mode == Mode.PITCH_DETECTION:
        frame_generator = run_pitch_detection(
            source_video_path=source_video_path, device=device)
    elif mode == Mode.PLAYER_DETECTION:
        frame_generator = run_player_detection(
            source_video_path=source_video_path, device=device)
    elif mode == Mode.BALL_DETECTION:
        frame_generator = run_ball_detection(
            source_video_path=source_video_path, device=device)
    elif mode == Mode.PLAYER_TRACKING:
        frame_generator = run_player_tracking(
            source_video_path=source_video_path, device=device)
    elif mode == Mode.TEAM_CLASSIFICATION:
        frame_generator = run_team_classification(
            source_video_path=source_video_path, device=device)
    elif mode == Mode.RADAR:
        frame_generator = run_radar(
            source_video_path=source_video_path, device=device)
    elif mode == Mode.POSSESSION:
        frame_generator = run_possession(
            source_video_path=source_video_path, device=device)
    else:
        raise NotImplementedError(f"Mode {mode} is not implemented.")

    video_info = sv.VideoInfo.from_video_path(source_video_path)
    gui_available = True
    with sv.VideoSink(target_video_path, video_info) as sink:
        for frame in frame_generator:
            sink.write_frame(frame)

            if gui_available:
                try:
                    cv2.imshow("frame", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                except cv2.error:
                    gui_available = False
        if gui_available:
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--source_video_path', type=str, required=True)
    parser.add_argument('--target_video_path', type=str, required=True)
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--mode', type=Mode, default=Mode.TEAM_CLASSIFICATION)
    args = parser.parse_args()
    main(
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path,
        device=args.device,
        mode=args.mode
    )
