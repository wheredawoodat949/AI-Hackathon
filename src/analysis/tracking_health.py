"""Local tracking-health agent with explicit evidence and uncertainty.

The agent consumes the same measured frame summaries sent to Arize. It can flag
rolling high churn, low confidence, and their coincidence, but does not infer true
identity swaps or causal explanations without identity ground truth.
"""
from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HealthEvent:
    kind: str
    severity: str
    frame_start: int
    frame_end: int
    message: str
    evidence: dict[str, float | int | str]


@dataclass(frozen=True)
class ClipHealthReport:
    frames_observed: int
    mean_detection_count: float
    mean_tracked_agent_count: float
    mean_confidence: float
    mean_track_churn_rate: float | None
    max_track_churn_rate: float | None
    events: tuple[HealthEvent, ...]
    narrative: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrackingHealthAgent:
    """Watch rolling measured signals and generate bounded factual narratives."""

    def __init__(
        self,
        *,
        window_size: int = 15,
        churn_threshold: float = 0.5,
        confidence_threshold: float = 0.4,
        alert_cooldown_frames: int = 30,
    ) -> None:
        if window_size <= 1 or alert_cooldown_frames < 0:
            raise ValueError("window_size must exceed one and cooldown must be non-negative")
        for name, value in (
            ("churn_threshold", churn_threshold),
            ("confidence_threshold", confidence_threshold),
        ):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        self.window_size = int(window_size)
        self.churn_threshold = float(churn_threshold)
        self.confidence_threshold = float(confidence_threshold)
        self.alert_cooldown_frames = int(alert_cooldown_frames)
        self._window: deque[Any] = deque(maxlen=self.window_size)
        self._events: list[HealthEvent] = []
        self._last_alert: dict[str, int] = {}
        self._frame_count = 0
        self._detection_total = 0
        self._tracked_total = 0
        self._confidence_total = 0.0
        self._churn_values: list[float] = []
        self._last_frame = -1

    @property
    def events(self) -> tuple[HealthEvent, ...]:
        return tuple(self._events)

    def observe(self, frame: Any) -> tuple[HealthEvent, ...]:
        """Consume a FrameObservation-compatible object and return new alerts."""
        frame_index = int(frame.frame_index)
        if frame_index <= self._last_frame:
            raise ValueError("frame indices must be strictly increasing")
        self._validate_frame(frame)
        self._last_frame = frame_index
        self._window.append(frame)
        self._frame_count += 1
        self._detection_total += int(frame.detection_count)
        self._tracked_total += int(frame.tracked_agent_count)
        self._confidence_total += float(frame.mean_confidence)
        if frame.track_churn_rate is not None:
            self._churn_values.append(float(frame.track_churn_rate))

        before = len(self._events)
        if len(self._window) == self.window_size:
            self._evaluate_window()
        return tuple(self._events[before:])

    def finalize(self) -> ClipHealthReport:
        """Return a report containing only values observed so far."""
        if not self._frame_count:
            return ClipHealthReport(
                frames_observed=0,
                mean_detection_count=0.0,
                mean_tracked_agent_count=0.0,
                mean_confidence=0.0,
                mean_track_churn_rate=None,
                max_track_churn_rate=None,
                events=(),
                narrative="No frames were observed; tracking health was not assessed.",
            )
        mean_churn = (
            sum(self._churn_values) / len(self._churn_values)
            if self._churn_values
            else None
        )
        max_churn = max(self._churn_values) if self._churn_values else None
        narrative = (
            f"Observed {self._frame_count} frames with mean confidence "
            f"{self._confidence_total / self._frame_count:.3f} and mean tracked-agent count "
            f"{self._tracked_total / self._frame_count:.2f}."
        )
        if mean_churn is None:
            narrative += " No frame-to-frame churn value was available."
        else:
            narrative += (
                f" Mean track-set churn was {mean_churn:.3f}; this measures ID set changes, "
                "not confirmed identity swaps."
            )
        if self._events:
            narrative += f" {len(self._events)} threshold event(s) were recorded with evidence."
        else:
            narrative += " No configured rolling threshold was crossed."
        return ClipHealthReport(
            frames_observed=self._frame_count,
            mean_detection_count=self._detection_total / self._frame_count,
            mean_tracked_agent_count=self._tracked_total / self._frame_count,
            mean_confidence=self._confidence_total / self._frame_count,
            mean_track_churn_rate=mean_churn,
            max_track_churn_rate=max_churn,
            events=self.events,
            narrative=narrative,
        )

    def write_report(self, path: str | Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.finalize().to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return destination

    def _evaluate_window(self) -> None:
        start = int(self._window[0].frame_index)
        end = int(self._window[-1].frame_index)
        mean_confidence = sum(
            float(frame.mean_confidence) for frame in self._window
        ) / len(self._window)
        churn_values = [
            float(frame.track_churn_rate)
            for frame in self._window
            if frame.track_churn_rate is not None
        ]
        mean_churn = sum(churn_values) / len(churn_values) if churn_values else None
        high_churn = mean_churn is not None and mean_churn >= self.churn_threshold
        low_confidence = mean_confidence <= self.confidence_threshold

        if high_churn and self._ready("high_track_churn", end):
            self._events.append(HealthEvent(
                kind="high_track_churn",
                severity="warning",
                frame_start=start,
                frame_end=end,
                message=(
                    f"Rolling track-set churn reached {mean_churn:.3f} "
                    f"(threshold {self.churn_threshold:.3f}). This may reflect entries/exits "
                    "or tracker fragmentation; identity ground truth is required to identify swaps."
                ),
                evidence={
                    "mean_track_churn_rate": mean_churn,
                    "threshold": self.churn_threshold,
                    "window_frames": len(self._window),
                },
            ))
        if low_confidence and self._ready("low_detection_confidence", end):
            self._events.append(HealthEvent(
                kind="low_detection_confidence",
                severity="warning",
                frame_start=start,
                frame_end=end,
                message=(
                    f"Rolling mean detection confidence fell to {mean_confidence:.3f} "
                    f"(threshold {self.confidence_threshold:.3f})."
                ),
                evidence={
                    "mean_confidence": mean_confidence,
                    "threshold": self.confidence_threshold,
                    "window_frames": len(self._window),
                },
            ))
        if high_churn and low_confidence and self._ready("coincident_instability", end):
            self._events.append(HealthEvent(
                kind="coincident_instability",
                severity="warning",
                frame_start=start,
                frame_end=end,
                message=(
                    "Low confidence and high track churn occurred in the same rolling window. "
                    "This is coincidence evidence, not a causal conclusion."
                ),
                evidence={
                    "mean_confidence": mean_confidence,
                    "mean_track_churn_rate": mean_churn,
                    "window_frames": len(self._window),
                },
            ))

    def _ready(self, kind: str, frame_index: int) -> bool:
        previous = self._last_alert.get(kind)
        if previous is not None and frame_index - previous < self.alert_cooldown_frames:
            return False
        self._last_alert[kind] = frame_index
        return True

    @staticmethod
    def _validate_frame(frame: Any) -> None:
        for name in ("detection_count", "tracked_agent_count"):
            if int(getattr(frame, name)) < 0:
                raise ValueError(f"{name} must be non-negative")
        confidence = float(frame.mean_confidence)
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("mean_confidence must be between 0 and 1")
        churn = frame.track_churn_rate
        if churn is not None and (
            not math.isfinite(float(churn)) or not 0 <= float(churn) <= 1
        ):
            raise ValueError("track_churn_rate must be between 0 and 1")
