"""Fan basketball tracking observations out to optional sponsor adapters.

The observer is dependency-light and knows nothing about Ultralytics or Supervision.
Sport runners translate detections into ObservedDetection records. Redis receives
tracked foot positions; Arize receives confidence plus observed track-set churn.
Churn is not mislabeled as a ground-truth ID swap: true ID-swap measurement requires
identity annotations or a validated association.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from src.obs import arize
from src.store import redis_store


@dataclass(frozen=True)
class ObservedDetection:
    """One model observation in image coordinates."""

    class_name: str
    confidence: float
    track_id: int | None = None
    x: float | None = None
    y: float | None = None
    team: str | int | None = None

    def __post_init__(self) -> None:
        if not self.class_name.strip():
            raise ValueError("class_name must not be empty")
        if not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.track_id is not None and self.track_id < 0:
            raise ValueError("track_id must be non-negative")
        if (self.x is None) != (self.y is None):
            raise ValueError("x and y must either both be set or both be absent")
        if self.x is not None and not (math.isfinite(self.x) and math.isfinite(self.y)):
            raise ValueError("x and y must be finite")


@dataclass(frozen=True)
class FrameObservation:
    """Exact frame-level values derived from tracker output."""

    frame_index: int
    detection_count: int
    tracked_agent_count: int
    mean_confidence: float
    new_track_count: int
    lost_track_count: int
    track_churn_rate: float | None


class TrackingObserver:
    """Initialize and feed Redis/Arize while keeping both off the critical path."""

    def __init__(self, cfg: Any, *, clip_id: str, sport: str = "basketball") -> None:
        if not clip_id.strip() or not sport.strip():
            raise ValueError("clip_id and sport must not be empty")
        self.clip_id = clip_id
        self.sport = sport
        self.redis_active = redis_store.init(cfg)
        self.arize_active = arize.init(cfg)
        self._previous_track_ids: set[int] | None = None

    @classmethod
    def for_video(cls, cfg: Any, video_path: str | Path, *, sport: str = "basketball"):
        return cls(cfg, clip_id=Path(video_path).stem, sport=sport)

    @property
    def active(self) -> bool:
        return self.redis_active or self.arize_active

    def observe_frame(
        self,
        frame_index: int,
        detections: Iterable[ObservedDetection],
        *,
        timestamp: float | None = None,
    ) -> FrameObservation:
        """Publish one frame and return its measured summary even when sponsors are off."""
        if frame_index < 0:
            raise ValueError("frame_index must be non-negative")
        records = list(detections)
        now = time.time() if timestamp is None else float(timestamp)
        if not math.isfinite(now) or now < 0:
            raise ValueError("timestamp must be a finite non-negative number")

        tracked = [record for record in records if record.track_id is not None]
        current_ids = {int(record.track_id) for record in tracked}
        previous_ids = self._previous_track_ids
        new_ids = current_ids - previous_ids if previous_ids is not None else set()
        lost_ids = previous_ids - current_ids if previous_ids is not None else set()
        churn = None
        if previous_ids is not None:
            population = len(previous_ids | current_ids)
            churn = (len(new_ids) + len(lost_ids)) / population if population else 0.0

        mean_confidence = (
            sum(record.confidence for record in records) / len(records) if records else 0.0
        )
        summary = FrameObservation(
            frame_index=frame_index,
            detection_count=len(records),
            tracked_agent_count=len(current_ids),
            mean_confidence=mean_confidence,
            new_track_count=len(new_ids),
            lost_track_count=len(lost_ids),
            track_churn_rate=churn,
        )

        if self.redis_active:
            positions = [
                redis_store.TrackPosition(
                    track_id=int(record.track_id),
                    x=float(record.x),
                    y=float(record.y),
                    team=record.team,
                    timestamp=now,
                    frame_index=frame_index,
                    sport=self.sport,
                    coordinate_space="image",
                )
                for record in tracked
                if record.x is not None
            ]
            redis_store.publish_positions(positions)

        if self.arize_active:
            timestamp_seconds = int(now)
            for index, record in enumerate(records):
                arize.log_detection(arize.DetectionTelemetry(
                    prediction_id=f"{self.clip_id}:{frame_index}:{index}",
                    class_name=record.class_name,
                    confidence=record.confidence,
                    frame_index=frame_index,
                    track_id=record.track_id,
                    tracked_agent_count=len(current_ids),
                    sport=self.sport,
                    clip_id=self.clip_id,
                    timestamp=timestamp_seconds,
                ))
            if churn is not None:
                arize.log_frame(arize.FrameTelemetry(
                    prediction_id=f"{self.clip_id}:{frame_index}:health",
                    frame_index=frame_index,
                    tracked_agent_count=len(current_ids),
                    detection_count=len(records),
                    mean_confidence=mean_confidence,
                    track_churn_rate=churn,
                    new_track_count=len(new_ids),
                    lost_track_count=len(lost_ids),
                    sport=self.sport,
                    clip_id=self.clip_id,
                    timestamp=timestamp_seconds,
                ))

        self._previous_track_ids = current_ids
        return summary

    def close(self) -> None:
        """Flush telemetry and close external connections."""
        if self.arize_active:
            arize.close()
        if self.redis_active:
            redis_store.close()
        self.arize_active = False
        self.redis_active = False

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.close()
