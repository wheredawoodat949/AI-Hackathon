"""Pure/unit tests for the shared possession and trail primitives."""
from __future__ import annotations

import numpy as np
import pytest
import supervision as sv

from sports.sports.common.possession import PossessionTracker
from sports.sports.common.trace import TraceAnnotator


def test_possession_tracks_holder_and_team_continuity():
    tracker = PossessionTracker(
        possession_radius=20,
        hysteresis_frames=2,
        switch_margin=5,
    )
    assert tracker.update((0, 0), [(2, 0), (15, 0)], [10, 20], [0, 1]) == (10, 0)
    assert tracker.update(None, [(2, 0), (15, 0)], [10, 20], [0, 1]) == (None, 0)
    stats = tracker.get_team_possession()
    assert stats["team_0_frames"] == 2
    assert stats["team_0_pct"] == 100
    assert tracker.get_player_possession()[10]["frames"] == 1


def test_possession_hysteresis_prevents_one_frame_near_tie():
    tracker = PossessionTracker(
        possession_radius=20,
        hysteresis_frames=2,
        switch_margin=5,
    )
    tracker.update((0, 0), [(2, 0), (10, 0)], [1, 2], [0, 1])
    assert tracker.update((0, 0), [(4, 0), (3, 0)], [1, 2], [0, 1]) == (1, 0)
    assert tracker.update((0, 0), [(4, 0), (3, 0)], [1, 2], [0, 1]) == (2, 1)


def test_possession_rejects_misaligned_inputs():
    tracker = PossessionTracker(possession_radius=20)
    with pytest.raises(ValueError, match="align"):
        tracker.update((0, 0), [(1, 1)], [1, 2], [0])


def test_trace_annotator_draws_and_prunes():
    palette = sv.ColorPalette.from_hex(["#FF0000", "#00FF00"])
    annotator = TraceAnnotator(
        color_palette=palette,
        max_length=3,
        speed_styling=False,
        draw_arrowhead=False,
        prune_after=0,
    )
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    first = sv.Detections(
        xyxy=np.array([[10, 10, 20, 30]], dtype=float),
        tracker_id=np.array([7]),
    )
    second = sv.Detections(
        xyxy=np.array([[20, 10, 30, 30]], dtype=float),
        tracker_id=np.array([7]),
    )
    annotator.update(first, np.array([0]))
    assert np.array_equal(annotator.annotate(frame), frame)
    annotator.update(second, np.array([0]))
    assert np.any(annotator.annotate(frame) != frame)
    annotator.update(sv.Detections.empty())
    assert 7 not in annotator.tracks
