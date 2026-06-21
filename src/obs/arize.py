"""Optional Arize ML observability for detections and tracker health.

Uses the Arize Python SDK v8 streaming API. Detection records are logged as
score-categorical predictions (label + confidence); one regression record per
frame carries a measured stability value plus count/confidence features. Callers
may supply a true ID-swap rate when identity ground truth exists. The basketball
runtime instead supplies observed track-set churn and labels it accordingly.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from src.config import env

LOGGER = logging.getLogger(__name__)

DEFAULT_DETECTION_MODEL = "sports-detections"
DEFAULT_HEALTH_MODEL = "sports-tracker-health"

_client = None
_space_id: str | None = None
_detection_model = DEFAULT_DETECTION_MODEL
_health_model = DEFAULT_HEALTH_MODEL
_model_version = "path-a-yolo11n"
_pending: list[Any] = []
_last_error: str | None = None


@dataclass(frozen=True)
class DetectionTelemetry:
    prediction_id: str
    class_name: str
    confidence: float
    frame_index: int
    track_id: int | None = None
    tracked_agent_count: int = 0
    sport: str = "basketball"
    clip_id: str = "unknown"
    timestamp: int = 0

    def __post_init__(self) -> None:
        _validate_common(self.prediction_id, self.sport, self.clip_id, self.frame_index)
        if not self.class_name.strip():
            raise ValueError("class_name must not be empty")
        if not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.tracked_agent_count < 0:
            raise ValueError("tracked_agent_count must be non-negative")


@dataclass(frozen=True)
class FrameTelemetry:
    prediction_id: str
    frame_index: int
    tracked_agent_count: int
    detection_count: int
    mean_confidence: float
    id_swap_rate: float | None = None
    track_churn_rate: float | None = None
    new_track_count: int = 0
    lost_track_count: int = 0
    sport: str = "basketball"
    clip_id: str = "unknown"
    timestamp: int = 0

    def __post_init__(self) -> None:
        _validate_common(self.prediction_id, self.sport, self.clip_id, self.frame_index)
        if self.tracked_agent_count < 0 or self.detection_count < 0:
            raise ValueError("counts must be non-negative")
        if not math.isfinite(self.mean_confidence) or not 0.0 <= self.mean_confidence <= 1.0:
            raise ValueError("mean_confidence must be between 0 and 1")
        if self.new_track_count < 0 or self.lost_track_count < 0:
            raise ValueError("track counts must be non-negative")
        if self.id_swap_rate is None and self.track_churn_rate is None:
            raise ValueError("one tracker-health metric is required")
        for name, value in (
            ("id_swap_rate", self.id_swap_rate),
            ("track_churn_rate", self.track_churn_rate),
        ):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be finite and non-negative")


def init(cfg: Any) -> bool:
    """Initialize Arize v8 when enabled and both credentials are available."""
    global _client, _space_id, _detection_model, _health_model, _model_version, _last_error

    _client = None
    _space_id = None
    _pending.clear()
    _last_error = None
    if not cfg.sponsor_enabled("arize"):
        return False
    api_key, space_id = env("ARIZE_API_KEY"), env("ARIZE_SPACE_ID")
    if not (api_key and space_id):
        _last_error = "ARIZE_API_KEY and ARIZE_SPACE_ID are required"
        return False
    _detection_model = env("ARIZE_DETECTION_MODEL_NAME", DEFAULT_DETECTION_MODEL) or DEFAULT_DETECTION_MODEL
    _health_model = env("ARIZE_HEALTH_MODEL_NAME", DEFAULT_HEALTH_MODEL) or DEFAULT_HEALTH_MODEL
    _model_version = env("ARIZE_MODEL_VERSION", "path-a-yolo11n") or "path-a-yolo11n"
    try:
        from arize import ArizeClient

        _client = ArizeClient(api_key=api_key).ml
        _space_id = space_id
    except Exception as exc:  # noqa: BLE001 - observability must not stop tracking
        _last_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Arize disabled: %s", _last_error)
        _client = None
        _space_id = None
    return _client is not None


def active() -> bool:
    return _client is not None and _space_id is not None


def last_error() -> str | None:
    return _last_error


def log_detection(record: DetectionTelemetry | Mapping[str, Any]) -> bool:
    """Queue one class/confidence prediction through Arize's streaming ML API."""
    if not active():
        return False
    telemetry = record if isinstance(record, DetectionTelemetry) else DetectionTelemetry(**record)
    try:
        from arize.ml.types import Environments, ModelTypes

        future = _client.log_stream(
            space_id=_space_id,
            model_name=_detection_model,
            model_type=ModelTypes.SCORE_CATEGORICAL,
            environment=Environments.PRODUCTION,
            model_version=_model_version,
            prediction_id=telemetry.prediction_id,
            prediction_timestamp=_timestamp(telemetry.timestamp),
            prediction_label=(telemetry.class_name, float(telemetry.confidence)),
            features={
                "confidence": float(telemetry.confidence),
                "frame_index": int(telemetry.frame_index),
                "tracked_agent_count": int(telemetry.tracked_agent_count),
            },
            tags=_tags(telemetry),
        )
        _track_future(future)
        return True
    except Exception as exc:  # noqa: BLE001
        _record_error("Arize detection log failed", exc)
        return False


def log_frame(record: FrameTelemetry | Mapping[str, Any]) -> bool:
    """Queue one frame-level tracker-health observation."""
    if not active():
        return False
    telemetry = record if isinstance(record, FrameTelemetry) else FrameTelemetry(**record)
    try:
        from arize.ml.types import Environments, ModelTypes

        metric_name, metric_value = (
            ("id_swap_rate", telemetry.id_swap_rate)
            if telemetry.id_swap_rate is not None
            else ("track_churn_rate", telemetry.track_churn_rate)
        )
        features = {
            "frame_index": int(telemetry.frame_index),
            "tracked_agent_count": int(telemetry.tracked_agent_count),
            "detection_count": int(telemetry.detection_count),
            "mean_confidence": float(telemetry.mean_confidence),
            "new_track_count": int(telemetry.new_track_count),
            "lost_track_count": int(telemetry.lost_track_count),
        }
        if telemetry.id_swap_rate is not None:
            features["id_swap_rate"] = float(telemetry.id_swap_rate)
        if telemetry.track_churn_rate is not None:
            features["track_churn_rate"] = float(telemetry.track_churn_rate)
        future = _client.log_stream(
            space_id=_space_id,
            model_name=_health_model,
            model_type=ModelTypes.REGRESSION,
            environment=Environments.PRODUCTION,
            model_version=_model_version,
            prediction_id=telemetry.prediction_id,
            prediction_timestamp=_timestamp(telemetry.timestamp),
            prediction_label=float(metric_value),
            features=features,
            tags={**_tags(telemetry), "health_metric": metric_name},
        )
        _track_future(future)
        return True
    except Exception as exc:  # noqa: BLE001
        _record_error("Arize frame log failed", exc)
        return False


def log_prediction(record: dict) -> bool:
    """Backward-compatible dispatcher for the original stub API."""
    payload = dict(record)
    kind = payload.pop("kind", "detection")
    return log_frame(payload) if kind == "frame" else log_detection(payload)


def flush(*, timeout: float = 10.0) -> tuple[int, int]:
    """Wait for queued asynchronous sends. Returns ``(succeeded, failed)``."""
    global _last_error
    succeeded = failed = 0
    pending, _pending[:] = list(_pending), []
    for future in pending:
        if future is None:
            succeeded += 1
            continue
        try:
            response = future.result(timeout=timeout)
            if getattr(response, "ok", True):
                succeeded += 1
            else:
                failed += 1
                _last_error = f"Arize HTTP {getattr(response, 'status_code', 'error')}"
        except Exception as exc:  # noqa: BLE001
            failed += 1
            _record_error("Arize async send failed", exc)
    return succeeded, failed


def close() -> tuple[int, int]:
    """Flush queued records and disable the adapter."""
    global _client, _space_id
    result = flush()
    _client = None
    _space_id = None
    return result


def _track_future(future: Any) -> None:
    _pending.append(future)
    # Keep long videos bounded and surface completed failures incrementally.
    if len(_pending) >= 256:
        flush()


def _timestamp(value: int) -> int:
    return int(time.time()) if value <= 0 else int(value)


def _tags(record: Any) -> dict[str, str | int]:
    data = asdict(record)
    tags: dict[str, str | int] = {
        "sport": str(data["sport"]),
        "clip_id": str(data["clip_id"]),
    }
    track_id = data.get("track_id")
    if track_id is not None:
        tags["track_id"] = int(track_id)
    return tags


def _validate_common(prediction_id: str, sport: str, clip_id: str, frame_index: int) -> None:
    if not prediction_id.strip():
        raise ValueError("prediction_id must not be empty")
    if not sport.strip() or not clip_id.strip():
        raise ValueError("sport and clip_id must not be empty")
    if frame_index < 0:
        raise ValueError("frame_index must be non-negative")


def _record_error(prefix: str, exc: Exception) -> None:
    global _last_error
    _last_error = f"{type(exc).__name__}: {exc}"
    LOGGER.warning("%s: %s", prefix, _last_error)
