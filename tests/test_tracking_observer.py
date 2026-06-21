"""Sponsor observer tests use adapter fakes and no external services."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.integrations.tracking_observer import ObservedDetection, TrackingObserver
from src.obs import arize
from src.store import redis_store


@pytest.fixture
def adapter_fakes(monkeypatch):
    redis_batches = []
    arize_detections = []
    arize_frames = []
    monkeypatch.setattr(redis_store, "init", lambda _cfg: True)
    monkeypatch.setattr(
        redis_store,
        "publish_positions",
        lambda batch: redis_batches.append(batch) or len(batch),
    )
    monkeypatch.setattr(redis_store, "close", lambda: None)
    monkeypatch.setattr(arize, "init", lambda _cfg: True)
    monkeypatch.setattr(
        arize,
        "log_detection",
        lambda record: arize_detections.append(record) or True,
    )
    monkeypatch.setattr(arize, "log_frame", lambda record: arize_frames.append(record) or True)
    monkeypatch.setattr(arize, "close", lambda: (0, 0))
    return redis_batches, arize_detections, arize_frames


def test_observer_publishes_positions_and_measured_churn(adapter_fakes):
    redis_batches, detection_logs, frame_logs = adapter_fakes
    observer = TrackingObserver(SimpleNamespace(), clip_id="game")
    first = observer.observe_frame(
        0,
        [
            ObservedDetection("person", 0.9, track_id=1, x=10, y=20, team=0),
            ObservedDetection("person", 0.7, track_id=2, x=30, y=40, team=1),
            ObservedDetection("sports ball", 0.6),
        ],
        timestamp=100,
    )
    second = observer.observe_frame(
        1,
        [
            ObservedDetection("person", 0.8, track_id=2, x=31, y=41, team=1),
            ObservedDetection("person", 0.75, track_id=3, x=50, y=60, team=0),
        ],
        timestamp=101,
    )

    assert first.track_churn_rate is None
    assert second.new_track_count == 1 and second.lost_track_count == 1
    assert second.track_churn_rate == pytest.approx(2 / 3)
    assert len(redis_batches) == 2 and len(redis_batches[0]) == 2
    assert redis_batches[0][0].coordinate_space == "image"
    assert len(detection_logs) == 5
    assert len(frame_logs) == 1
    assert frame_logs[0].id_swap_rate is None
    assert frame_logs[0].track_churn_rate == pytest.approx(2 / 3)


def test_noop_observer_still_returns_real_summary(monkeypatch):
    monkeypatch.setattr(redis_store, "init", lambda _cfg: False)
    monkeypatch.setattr(arize, "init", lambda _cfg: False)
    observer = TrackingObserver(SimpleNamespace(), clip_id="game")
    summary = observer.observe_frame(0, [ObservedDetection("person", 0.5, track_id=4)])
    assert observer.active is False
    assert summary.detection_count == 1
    assert summary.tracked_agent_count == 1


def test_observation_validation():
    with pytest.raises(ValueError, match="confidence"):
        ObservedDetection("person", 2.0)
    with pytest.raises(ValueError, match="both"):
        ObservedDetection("person", 0.5, x=1)
