"""Arize telemetry tests never send network requests."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.obs import arize


class FakeFuture:
    def __init__(self, response=None, error=None):
        self.response = response or SimpleNamespace(ok=True, status_code=200)
        self.error = error

    def result(self, timeout):
        assert timeout > 0
        if self.error:
            raise self.error
        return self.response


class FakeMLClient:
    def __init__(self):
        self.calls = []

    def log_stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeFuture()


@pytest.fixture(autouse=True)
def reset_arize(monkeypatch):
    arize.close()
    monkeypatch.setattr(arize, "_client", None)
    monkeypatch.setattr(arize, "_space_id", None)
    monkeypatch.setattr(arize, "_detection_model", "sports-detections")
    monkeypatch.setattr(arize, "_health_model", "sports-tracker-health")
    monkeypatch.setattr(arize, "_model_version", "test")
    monkeypatch.setattr(arize, "_last_error", None)
    yield
    arize.close()


def test_disabled_is_a_safe_noop():
    cfg = SimpleNamespace(sponsor_enabled=lambda _name: False)
    assert arize.init(cfg) is False
    assert arize.log_detection({}) is False
    assert arize.log_frame({}) is False
    assert arize.flush() == (0, 0)


def test_detection_and_frame_records_use_current_stream_api(monkeypatch):
    fake = FakeMLClient()
    monkeypatch.setattr(arize, "_client", fake)
    monkeypatch.setattr(arize, "_space_id", "space-1")

    assert arize.log_detection(arize.DetectionTelemetry(
        prediction_id="clip:4:7",
        class_name="person",
        confidence=0.91,
        frame_index=4,
        track_id=7,
        tracked_agent_count=10,
        clip_id="clip",
        timestamp=123,
    ))
    assert arize.log_frame(arize.FrameTelemetry(
        prediction_id="clip:4:health",
        frame_index=4,
        tracked_agent_count=10,
        detection_count=11,
        mean_confidence=0.8,
        id_swap_rate=0.02,
        clip_id="clip",
        timestamp=123,
    ))

    from arize.ml.types import ModelTypes

    detection, health = fake.calls
    assert detection["model_type"] == ModelTypes.SCORE_CATEGORICAL
    assert detection["prediction_label"] == ("person", 0.91)
    assert detection["features"]["tracked_agent_count"] == 10
    assert detection["tags"] == {"sport": "basketball", "clip_id": "clip", "track_id": 7}
    assert health["model_type"] == ModelTypes.REGRESSION
    assert health["prediction_label"] == 0.02
    assert health["features"]["detection_count"] == 11
    assert arize.flush() == (2, 0)


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError, match="between 0 and 1"):
        arize.DetectionTelemetry("id", "person", 1.5, 1)


def test_flush_reports_async_failure(monkeypatch):
    monkeypatch.setattr(arize, "_pending", [FakeFuture(error=RuntimeError("offline"))])
    assert arize.flush() == (0, 1)
    assert "offline" in arize.last_error()
