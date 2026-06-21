"""Optional Redis live-state and track-search integration.

The basketball runner publishes each tracked player's latest position to a Redis
hash and appends the same update to a bounded Redis Stream. A dashboard can read
the hash for an immediate snapshot, then consume the stream for live updates.

The module is deliberately off the critical path: imports are lazy, every public
write is a no-op while disabled, and Redis failures return ``False`` instead of
stopping video processing.
"""
from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from src.config import env

LOGGER = logging.getLogger(__name__)

DEFAULT_KEY_PREFIX = "sports"
DEFAULT_TTL_SECONDS = 3_600
DEFAULT_STREAM_MAXLEN = 10_000

_client = None
_key_prefix = DEFAULT_KEY_PREFIX
_ttl_seconds = DEFAULT_TTL_SECONDS
_stream_maxlen = DEFAULT_STREAM_MAXLEN
_last_error: str | None = None


@dataclass(frozen=True)
class TrackPosition:
    """One observable track position at a point in time."""

    track_id: int
    x: float
    y: float
    team: str | int | None = None
    timestamp: float = 0.0
    frame_index: int | None = None
    sport: str = "basketball"
    coordinate_space: str = "image"

    def __post_init__(self) -> None:
        if self.track_id < 0:
            raise ValueError("track_id must be non-negative")
        if not (math.isfinite(self.x) and math.isfinite(self.y)):
            raise ValueError("x and y must be finite")
        if self.timestamp < 0 or not math.isfinite(self.timestamp):
            raise ValueError("timestamp must be a finite non-negative number")
        if not self.sport.strip():
            raise ValueError("sport must not be empty")
        if not self.coordinate_space.strip():
            raise ValueError("coordinate_space must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def init(cfg: Any) -> bool:
    """Connect when ``sponsors.redis`` and ``REDIS_URL`` are both configured."""
    global _client, _key_prefix, _ttl_seconds, _stream_maxlen, _last_error

    _client = None
    _last_error = None
    if not cfg.sponsor_enabled("redis"):
        return False
    url = env("REDIS_URL")
    if not url:
        _last_error = "REDIS_URL is not set"
        return False

    _key_prefix = (env("REDIS_KEY_PREFIX", DEFAULT_KEY_PREFIX) or DEFAULT_KEY_PREFIX).strip(":")
    _ttl_seconds = _positive_int_env("REDIS_TRACK_TTL_SECONDS", DEFAULT_TTL_SECONDS)
    _stream_maxlen = _positive_int_env("REDIS_STREAM_MAXLEN", DEFAULT_STREAM_MAXLEN)
    try:
        import redis

        _client = redis.from_url(url, decode_responses=True)
        _client.ping()
    except Exception as exc:  # noqa: BLE001 - sponsor outage must not stop tracking
        _last_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Redis disabled: %s", _last_error)
        _client = None
    return _client is not None


def close() -> None:
    """Close the active connection, if any, and return to no-op mode."""
    global _client
    client, _client = _client, None
    if client is not None and hasattr(client, "close"):
        try:
            client.close()
        except Exception:  # noqa: BLE001 - best-effort shutdown
            pass


def active() -> bool:
    return _client is not None


def last_error() -> str | None:
    return _last_error


def publish_track_position(
    track_id: int,
    x: float,
    y: float,
    *,
    team: str | int | None = None,
    timestamp: float | None = None,
    frame_index: int | None = None,
    sport: str = "basketball",
    coordinate_space: str = "image",
) -> bool:
    """Cache one latest position and append it to the sport's Redis Stream."""
    if _client is None:
        return False
    position = TrackPosition(
        track_id=int(track_id),
        x=float(x),
        y=float(y),
        team=team,
        timestamp=time.time() if timestamp is None else float(timestamp),
        frame_index=frame_index,
        sport=sport,
        coordinate_space=coordinate_space,
    )
    return publish_positions([position]) == 1


def publish_positions(positions: Iterable[TrackPosition | Mapping[str, Any]]) -> int:
    """Publish a batch atomically. Returns the number written, or zero on failure."""
    global _last_error
    if _client is None:
        return 0

    normalized = [p if isinstance(p, TrackPosition) else TrackPosition(**p) for p in positions]
    if not normalized:
        return 0

    try:
        pipeline = _client.pipeline(transaction=False)
        latest_keys: set[str] = set()
        for position in normalized:
            latest_key = _latest_key(position.sport)
            latest_keys.add(latest_key)
            encoded = json.dumps(position.to_dict(), separators=(",", ":"), sort_keys=True)
            pipeline.hset(latest_key, mapping={str(position.track_id): encoded})
            pipeline.xadd(
                _stream_key(position.sport),
                {"data": encoded},
                maxlen=_stream_maxlen,
                approximate=True,
            )
        for latest_key in latest_keys:
            pipeline.expire(latest_key, _ttl_seconds)
        pipeline.execute()
        _last_error = None
        return len(normalized)
    except Exception as exc:  # noqa: BLE001 - sponsor outage must not stop tracking
        _last_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Redis track publish failed: %s", _last_error)
        return 0


def latest_positions(*, sport: str = "basketball") -> list[dict[str, Any]]:
    """Return the cached latest position for every active track."""
    global _last_error
    if _client is None:
        return []
    try:
        values = _client.hgetall(_latest_key(sport)).values()
        result = [json.loads(_decode(value)) for value in values]
        return sorted(result, key=lambda item: int(item["track_id"]))
    except Exception as exc:  # noqa: BLE001
        _last_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Redis latest-position read failed: %s", _last_error)
        return []


def upsert_track_embedding(track_id: int, vector: Sequence[float], meta: dict) -> bool:
    """Store a track embedding in basic Redis, without requiring RediSearch."""
    global _last_error
    if _client is None:
        return False
    values = [float(value) for value in vector]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("vector must contain finite values")
    record = {"track_id": int(track_id), "vector": values, "meta": dict(meta)}
    try:
        _client.hset(_embedding_key(), mapping={str(track_id): json.dumps(record)})
        _last_error = None
        return True
    except Exception as exc:  # noqa: BLE001
        _last_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Redis embedding write failed: %s", _last_error)
        return False


def search(query_vector: Sequence[float], *, top_k: int = 5) -> list[dict[str, Any]]:
    """Return cosine-nearest track embeddings using portable Redis hash storage."""
    global _last_error
    if _client is None or top_k <= 0:
        return []
    query = [float(value) for value in query_vector]
    if not query or not all(math.isfinite(value) for value in query):
        raise ValueError("query_vector must contain finite values")
    try:
        records = [json.loads(_decode(value)) for value in _client.hgetall(_embedding_key()).values()]
        scored = []
        for record in records:
            vector = record.get("vector", [])
            if len(vector) != len(query):
                continue
            score = _cosine_similarity(query, vector)
            scored.append({"track_id": record["track_id"], "score": score, **record.get("meta", {})})
        _last_error = None
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]
    except Exception as exc:  # noqa: BLE001
        _last_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("Redis embedding search failed: %s", _last_error)
        return []


def _latest_key(sport: str) -> str:
    return f"{_key_prefix}:tracks:{sport}:latest"


def _stream_key(sport: str) -> str:
    return f"{_key_prefix}:tracks:{sport}:stream"


def _embedding_key() -> str:
    return f"{_key_prefix}:track_embeddings"


def _positive_int_env(name: str, default: int) -> int:
    raw = env(name)
    if raw is None or raw == "":
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _decode(value: Any) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
