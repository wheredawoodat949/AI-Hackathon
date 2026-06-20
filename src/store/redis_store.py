"""Redis vector store + semantic search (Role C — feat/sponsors).

"Beyond caching": embed player track segments (appearance + trajectory) as
vectors, store in Redis, and answer BAS-vocabulary semantic queries
("show every cross from the left"). Behind `sponsors.redis` + REDIS_URL.
redis imported lazily; a no-op when disabled.

Module named `redis_store` (not `redis`) so it doesn't shadow the pip package.
"""
from __future__ import annotations

from typing import Any, Sequence

from src.config import env

_client = None


def init(cfg: Any) -> bool:
    """Connect to Redis if enabled + REDIS_URL set. Returns active state."""
    global _client
    if not cfg.sponsor_enabled("redis"):
        return False
    url = env("REDIS_URL")
    if not url:
        return False
    try:
        import redis

        _client = redis.from_url(url)
        _client.ping()
    except Exception:  # noqa: BLE001 - never break the pipeline
        _client = None
    return _client is not None


def upsert_track_embedding(track_id: int, vector: Sequence[float], meta: dict) -> None:
    """Store one track-segment embedding. No-op when disabled.

    TODO(Role C): write the vector + metadata via a RediSearch vector index.
    """
    if _client is None:
        return
    # TODO(Role C): HSET / vector index write


def search(query_vector: Sequence[float], *, top_k: int = 5) -> list[dict]:
    """Vector search for similar track segments. Returns [] when disabled.

    TODO(Role C): KNN query against the RediSearch index.
    """
    if _client is None:
        return []
    raise NotImplementedError("redis_store.search() not implemented yet.")
