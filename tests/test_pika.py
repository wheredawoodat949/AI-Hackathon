"""Pika integration tests use a fake HTTP session and never spend API credits."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.synthetic import pika


class FakeResponse:
    def __init__(self, payload=None, chunks=None):
        self.payload = payload or {}
        self.chunks = chunks or []

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload

    def iter_content(self, chunk_size):
        assert chunk_size > 0
        return iter(self.chunks)


class FakeSession:
    def __init__(self):
        self.calls = []
        self.responses = []
        self.closed = False

    def _call(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        return self._call("post", url, **kwargs)

    def get(self, url, **kwargs):
        return self._call("get", url, **kwargs)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_pika(monkeypatch, tmp_path):
    pika.close()
    monkeypatch.setattr(pika, "_session", None)
    monkeypatch.setattr(pika, "_api_key", None)
    monkeypatch.setattr(pika, "_base_url", pika.DEFAULT_BASE_URL)
    monkeypatch.setattr(pika, "_output_root", tmp_path)
    monkeypatch.setattr(pika, "_last_error", None)
    yield
    pika.close()


def enable(monkeypatch, session):
    monkeypatch.setattr(pika, "_session", session)
    monkeypatch.setattr(pika, "_api_key", "secret")


def test_disabled_is_safe_noop():
    cfg = SimpleNamespace(sponsor_enabled=lambda _name: False)
    assert pika.init(cfg) is False
    assert pika.generate_text_video("basketball game") is None
    assert pika.get_video("job-1") is None


def test_text_generation_and_status_use_documented_endpoints(monkeypatch):
    session = FakeSession()
    session.responses = [
        FakeResponse({"video_id": "job-1"}),
        FakeResponse({"id": "job-1", "status": "processing", "url": None, "progress": 20}),
        FakeResponse({"id": "job-1", "status": "complete", "url": "https://media/video.mp4", "progress": 100}),
    ]
    enable(monkeypatch, session)

    job = pika.generate_text_video(
        "basketball players under arena lights",
        negative_prompt="watermark",
        seed=7,
        aspect_ratio=16 / 9,
    )
    assert job == pika.PikaJob("job-1", "t2v", "basketball players under arena lights", "watermark", 7)
    result = pika.wait_for_video("job-1", timeout=1, poll_interval=0.001, sleep=lambda _n: None)
    assert result and result.ready and result.progress == 100

    method, url, kwargs = session.calls[0]
    assert (method, url) == ("post", "https://devapi.pika.art/generate/turbo/t2v")
    assert kwargs["headers"]["X-API-KEY"] == "secret"
    assert kwargs["data"]["promptText"].startswith("basketball")
    assert session.calls[1][1].endswith("/videos/job-1")


def test_image_generation_uses_multipart_file(monkeypatch, tmp_path):
    source = tmp_path / "court.jpg"
    source.write_bytes(b"jpeg")
    session = FakeSession()
    session.responses = [FakeResponse({"video_id": "image-job"})]
    enable(monkeypatch, session)

    job = pika.generate_image_video(source, prompt="camera pans across the court")
    assert job and job.mode == "i2v" and job.source_image == str(source)
    _, url, kwargs = session.calls[0]
    assert url.endswith("/generate/turbo/i2v")
    filename, handle, media_type = kwargs["files"]["image"]
    assert filename == "court.jpg" and media_type == "image/jpeg"
    assert handle.closed


def test_download_does_not_forward_api_key_and_manifest_is_unlabeled(monkeypatch, tmp_path):
    session = FakeSession()
    session.responses = [FakeResponse(chunks=[b"video", b"bytes"])]
    enable(monkeypatch, session)
    video = pika.PikaVideo("job-2", "complete", "https://cdn.example/video.mp4", 100)
    destination = tmp_path / "result.mp4"

    assert pika.download_video(video, destination) == destination
    assert destination.read_bytes() == b"videobytes"
    _, url, kwargs = session.calls[0]
    assert url == video.url
    assert "headers" not in kwargs

    job = pika.PikaJob("job-2", "t2v", "basketball court")
    manifest = pika.record_manifest(job, video, destination, manifest_path=tmp_path / "manifest.jsonl")
    record = json.loads(manifest.read_text().strip())
    assert record["synthetic"] is True
    assert record["annotated"] is False
    assert record["eligible_for_training"] is False


def test_input_validation(tmp_path):
    with pytest.raises(ValueError, match="aspect_ratio"):
        pika.generate_text_video("basketball", aspect_ratio=3)
    with pytest.raises(FileNotFoundError):
        pika.generate_image_video(tmp_path / "missing.jpg", prompt="basketball")
    with pytest.raises(ValueError, match="no URL"):
        pika.download_video(pika.PikaVideo("id", "processing", None, 1), tmp_path / "x.mp4")
