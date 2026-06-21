"""Redis integration tests use an in-memory protocol fake, never a real service."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.store import redis_store


class FakePipeline:
    def __init__(self, client):
        self.client = client
        self.calls = []

    def hset(self, *args, **kwargs):
        self.calls.append((self.client.hset, args, kwargs))
        return self

    def xadd(self, *args, **kwargs):
        self.calls.append((self.client.xadd, args, kwargs))
        return self

    def expire(self, *args, **kwargs):
        self.calls.append((self.client.expire, args, kwargs))
        return self

    def execute(self):
        return [fn(*args, **kwargs) for fn, args, kwargs in self.calls]


class FakeRedis:
    def __init__(self):
        self.hashes = {}
        self.streams = {}
        self.expirations = {}
        self.closed = False

    def ping(self):
        return True

    def pipeline(self, transaction=False):
        assert transaction is False
        return FakePipeline(self)

    def hset(self, name, mapping):
        self.hashes.setdefault(name, {}).update(mapping)
        return len(mapping)

    def hgetall(self, name):
        return dict(self.hashes.get(name, {}))

    def expire(self, name, seconds):
        self.expirations[name] = seconds
        return True

    def xadd(self, name, fields, **kwargs):
        self.streams.setdefault(name, []).append((fields, kwargs))
        return f"{len(self.streams[name])}-0"

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_redis_state(monkeypatch):
    redis_store.close()
    monkeypatch.setattr(redis_store, "_key_prefix", "sports")
    monkeypatch.setattr(redis_store, "_ttl_seconds", 3_600)
    monkeypatch.setattr(redis_store, "_stream_maxlen", 10_000)
    monkeypatch.setattr(redis_store, "_last_error", None)
    yield
    redis_store.close()


def test_disabled_is_a_safe_noop():
    cfg = SimpleNamespace(sponsor_enabled=lambda _name: False)
    assert redis_store.init(cfg) is False
    assert redis_store.publish_track_position(1, 2, 3) is False
    assert redis_store.latest_positions() == []
    assert redis_store.search([1.0]) == []


def test_publish_positions_updates_latest_hash_and_stream(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(redis_store, "_client", fake)

    written = redis_store.publish_positions([
        redis_store.TrackPosition(7, 12.5, 44.0, team=1, timestamp=10.0, frame_index=3),
        redis_store.TrackPosition(2, 4.0, 8.0, team=0, timestamp=10.0, frame_index=3),
    ])

    assert written == 2
    latest = redis_store.latest_positions()
    assert [position["track_id"] for position in latest] == [2, 7]
    assert latest[1]["team"] == 1 and latest[1]["coordinate_space"] == "image"
    latest_key = "sports:tracks:basketball:latest"
    stream_key = "sports:tracks:basketball:stream"
    assert fake.expirations[latest_key] == 3_600
    assert len(fake.streams[stream_key]) == 2
    encoded = fake.streams[stream_key][0][0]["data"]
    assert json.loads(encoded)["frame_index"] == 3
    assert fake.streams[stream_key][0][1] == {"maxlen": 10_000, "approximate": True}


def test_embedding_search_ranks_cosine_similarity(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(redis_store, "_client", fake)
    assert redis_store.upsert_track_embedding(1, [1.0, 0.0], {"label": "guard"})
    assert redis_store.upsert_track_embedding(2, [0.0, 1.0], {"label": "center"})

    results = redis_store.search([0.9, 0.1], top_k=2)

    assert [result["track_id"] for result in results] == [1, 2]
    assert results[0]["score"] > results[1]["score"]
    assert results[0]["label"] == "guard"


def test_invalid_position_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        redis_store.TrackPosition(1, float("nan"), 0.0)
