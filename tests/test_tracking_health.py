"""Tracking health narratives are derived only from supplied measurements."""
from __future__ import annotations

import json

import pytest

from src.analysis.tracking_health import TrackingHealthAgent
from src.integrations.tracking_observer import FrameObservation


def frame(index, confidence, churn):
    return FrameObservation(
        frame_index=index,
        detection_count=8,
        tracked_agent_count=7,
        mean_confidence=confidence,
        new_track_count=1 if churn else 0,
        lost_track_count=0,
        track_churn_rate=churn,
    )


def test_agent_records_threshold_evidence_without_claiming_id_swaps():
    agent = TrackingHealthAgent(
        window_size=3,
        churn_threshold=0.5,
        confidence_threshold=0.4,
        alert_cooldown_frames=10,
    )
    agent.observe(frame(0, 0.3, None))
    agent.observe(frame(1, 0.3, 0.6))
    events = agent.observe(frame(2, 0.3, 0.8))
    assert {event.kind for event in events} == {
        "high_track_churn",
        "low_detection_confidence",
        "coincident_instability",
    }
    churn_event = next(event for event in events if event.kind == "high_track_churn")
    assert "identity ground truth" in churn_event.message
    assert churn_event.evidence["mean_track_churn_rate"] == pytest.approx(0.7)
    assert "causal conclusion" in events[-1].message


def test_finalize_and_write_report_use_observed_values(tmp_path):
    agent = TrackingHealthAgent(window_size=3)
    agent.observe(frame(0, 0.9, None))
    agent.observe(frame(1, 0.7, 0.2))
    report = agent.finalize()
    assert report.frames_observed == 2
    assert report.mean_confidence == pytest.approx(0.8)
    assert report.mean_track_churn_rate == pytest.approx(0.2)
    assert "not confirmed identity swaps" in report.narrative
    output = agent.write_report(tmp_path / "health.json")
    payload = json.loads(output.read_text())
    assert payload["frames_observed"] == 2
    assert payload["mean_confidence"] == pytest.approx(0.8)


def test_empty_agent_reports_no_assessment():
    report = TrackingHealthAgent().finalize()
    assert report.frames_observed == 0
    assert "not assessed" in report.narrative


def test_agent_rejects_out_of_order_or_invalid_frames():
    agent = TrackingHealthAgent(window_size=3)
    agent.observe(frame(2, 0.8, None))
    with pytest.raises(ValueError, match="strictly increasing"):
        agent.observe(frame(2, 0.8, 0.1))
    with pytest.raises(ValueError, match="confidence"):
        TrackingHealthAgent(window_size=3).observe(frame(0, 1.5, None))
