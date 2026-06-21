"""Optional Pika synthetic-video integration.

The client implements Pika's documented direct Developer API:

* POST ``/generate/turbo/t2v`` for text-to-video
* POST ``/generate/turbo/i2v`` for image-to-video
* GET ``/videos/{video_id}`` for status and the output URL

Generated videos and their manifests live under the gitignored ``synthetic/``
directory. They are deliberately marked ineligible for training: Pika returns media,
not detection annotations. A person must review and label extracted frames before a
training split can reference them.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import mimetypes
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from src.config import REPO_ROOT, env, load_config

LOGGER = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://devapi.pika.art"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "synthetic" / "pika"

_session: Any = None
_api_key: str | None = None
_base_url = DEFAULT_BASE_URL
_output_root = DEFAULT_OUTPUT_ROOT
_last_error: str | None = None


@dataclass(frozen=True)
class PikaJob:
    """A submitted Pika generation job."""

    video_id: str
    mode: str
    prompt: str
    negative_prompt: str | None = None
    seed: int | None = None
    source_image: str | None = None

    def __post_init__(self) -> None:
        if not self.video_id.strip():
            raise ValueError("video_id must not be empty")
        if self.mode not in {"t2v", "i2v"}:
            raise ValueError("mode must be 't2v' or 'i2v'")
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")


@dataclass(frozen=True)
class PikaVideo:
    """Current state returned by Pika's Get Video endpoint."""

    video_id: str
    status: str
    url: str | None
    progress: int | None

    @property
    def ready(self) -> bool:
        """Pika documents a nullable URL but not status enum values."""
        return bool(self.url)


def init(cfg: Any, *, session: Any = None) -> bool:
    """Enable the client when ``sponsors.pika`` and ``PIKA_API_KEY`` are set."""
    global _session, _api_key, _base_url, _output_root, _last_error

    _session = None
    _api_key = None
    _last_error = None
    if not cfg.sponsor_enabled("pika"):
        return False
    api_key = env("PIKA_API_KEY")
    if not api_key:
        _last_error = "PIKA_API_KEY is not set"
        return False

    if session is None:
        try:
            import requests

            session = requests.Session()
        except Exception as exc:  # noqa: BLE001 - optional integration
            _record_error("Pika disabled", exc)
            return False

    _session = session
    _api_key = api_key
    _base_url = (env("PIKA_API_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL).rstrip("/")
    configured_root = env("PIKA_OUTPUT_DIR")
    _output_root = Path(configured_root).expanduser() if configured_root else DEFAULT_OUTPUT_ROOT
    return True


def close() -> None:
    """Close the HTTP session and return to no-op mode."""
    global _session, _api_key
    session, _session = _session, None
    _api_key = None
    if session is not None and hasattr(session, "close"):
        try:
            session.close()
        except Exception:  # noqa: BLE001 - best-effort shutdown
            pass


def active() -> bool:
    return _session is not None and bool(_api_key)


def last_error() -> str | None:
    return _last_error


def generate_text_video(
    prompt: str,
    *,
    negative_prompt: str | None = None,
    seed: int | None = None,
    aspect_ratio: float | None = None,
) -> PikaJob | None:
    """Submit one documented Turbo text-to-video request."""
    _require_prompt(prompt)
    if aspect_ratio is not None and not 0.4 <= float(aspect_ratio) <= 2.5:
        raise ValueError("aspect_ratio must be between 0.4 and 2.5")
    payload: dict[str, str | int | float] = {"promptText": prompt}
    _add_optional_generation_fields(payload, negative_prompt, seed)
    if aspect_ratio is not None:
        payload["aspectRatio"] = float(aspect_ratio)
    response = _request("post", "/generate/turbo/t2v", data=payload)
    return _job_from_response(response, "t2v", prompt, negative_prompt, seed)


def generate_image_video(
    image_path: str | Path,
    *,
    prompt: str,
    negative_prompt: str | None = None,
    seed: int | None = None,
) -> PikaJob | None:
    """Submit one documented Turbo image-to-video request."""
    _require_prompt(prompt)
    image = Path(image_path).expanduser().resolve()
    if not image.is_file():
        raise FileNotFoundError(f"Pika source image not found: {image}")
    payload: dict[str, str | int] = {"promptText": prompt}
    _add_optional_generation_fields(payload, negative_prompt, seed)
    media_type = mimetypes.guess_type(image.name)[0] or "application/octet-stream"
    try:
        with image.open("rb") as handle:
            response = _request(
                "post",
                "/generate/turbo/i2v",
                data=payload,
                files={"image": (image.name, handle, media_type)},
            )
    except OSError as exc:
        _record_error("Pika source image read failed", exc)
        return None
    return _job_from_response(response, "i2v", prompt, negative_prompt, seed, str(image))


def get_video(video_id: str) -> PikaVideo | None:
    """Read a job via Pika's documented Get Video endpoint."""
    if not video_id.strip():
        raise ValueError("video_id must not be empty")
    response = _request("get", f"/videos/{video_id}")
    if response is None:
        return None
    try:
        payload = response.json()
        progress = payload.get("progress")
        return PikaVideo(
            video_id=str(payload["id"]),
            status=str(payload["status"]),
            url=str(payload["url"]) if payload.get("url") else None,
            progress=int(progress) if progress is not None else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        _record_error("Invalid Pika video response", exc)
        return None


def wait_for_video(
    video_id: str,
    *,
    timeout: float = 600.0,
    poll_interval: float = 5.0,
    sleep: Callable[[float], None] = time.sleep,
) -> PikaVideo | None:
    """Poll until Pika supplies an output URL or the bounded timeout expires."""
    global _last_error
    if timeout <= 0 or poll_interval <= 0:
        raise ValueError("timeout and poll_interval must be positive")
    deadline = time.monotonic() + timeout
    latest: PikaVideo | None = None
    while time.monotonic() < deadline:
        latest = get_video(video_id)
        if latest is None or latest.ready:
            return latest
        sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
    status = latest.status if latest else "unknown"
    _last_error = f"Timed out waiting for Pika video {video_id} (status={status})"
    return None


def download_video(video: PikaVideo, destination: str | Path | None = None) -> Path | None:
    """Download a ready result without forwarding the Pika API key to its media host."""
    if not video.url:
        raise ValueError("Pika video is not ready: response has no URL")
    if not active():
        return None
    destination = Path(destination) if destination else _output_root / f"{video.video_id}.mp4"
    destination = destination.expanduser().resolve()
    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Supply no Pika auth headers: output URLs may be hosted by another domain.
        response = _session.get(video.url, stream=True, timeout=120)
        response.raise_for_status()
        with partial.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        partial.replace(destination)
        return destination
    except Exception as exc:  # noqa: BLE001 - optional integration
        partial.unlink(missing_ok=True)
        _record_error("Pika video download failed", exc)
        return None


def record_manifest(
    job: PikaJob,
    video: PikaVideo,
    output_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
) -> Path:
    """Append provenance while explicitly keeping generated media out of training."""
    path = Path(manifest_path) if manifest_path else _output_root / "manifest.jsonl"
    path = path.expanduser().resolve()
    record = {
        "provider": "pika",
        "generated_at": int(time.time()),
        "job": asdict(job),
        "result": asdict(video),
        "output_path": str(Path(output_path).expanduser().resolve()),
        "synthetic": True,
        "reviewed": False,
        "annotated": False,
        "eligible_for_training": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def extract_frames(video_path: str | Path, output_dir: str | Path, *, fps: float = 1.0) -> Path:
    """Extract review frames with ffmpeg; this does not create detection labels."""
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be a positive finite number")
    video = Path(video_path).expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(f"Pika video not found: {video}")
    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vf", f"fps={fps:g}", str(destination / "frame_%05d.jpg")],
        check=True,
    )
    return destination


def _request(method: str, path: str, **kwargs: Any) -> Any:
    if not active():
        return None
    global _last_error
    try:
        response = getattr(_session, method)(
            f"{_base_url}{path}",
            headers={"X-API-KEY": _api_key, "Accept": "application/json"},
            timeout=120,
            **kwargs,
        )
        response.raise_for_status()
        _last_error = None
        return response
    except Exception as exc:  # noqa: BLE001 - generation must not break tracking
        _record_error("Pika API request failed", exc)
        return None


def _job_from_response(
    response: Any,
    mode: str,
    prompt: str,
    negative_prompt: str | None,
    seed: int | None,
    source_image: str | None = None,
) -> PikaJob | None:
    if response is None:
        return None
    try:
        video_id = str(response.json()["video_id"])
        return PikaJob(video_id, mode, prompt, negative_prompt, seed, source_image)
    except (KeyError, TypeError, ValueError) as exc:
        _record_error("Invalid Pika generation response", exc)
        return None


def _add_optional_generation_fields(
    payload: dict[str, Any], negative_prompt: str | None, seed: int | None
) -> None:
    if negative_prompt:
        payload["negativePrompt"] = negative_prompt
    if seed is not None:
        payload["seed"] = int(seed)


def _require_prompt(prompt: str) -> None:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")


def _record_error(prefix: str, exc: Exception) -> None:
    global _last_error
    _last_error = f"{type(exc).__name__}: {exc}"
    LOGGER.warning("%s: %s", prefix, _last_error)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic review media with Pika")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image", type=Path, help="Source image; omit for text-to-video")
    parser.add_argument("--negative-prompt")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--aspect-ratio", type=float, default=16 / 9)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--poll-interval", type=float, default=5)
    parser.add_argument("--extract-fps", type=float, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = load_config()
    if not init(cfg):
        raise SystemExit(f"Pika is disabled: {last_error() or 'set sponsors.pika: true'}")
    job = (
        generate_image_video(
            args.image,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
        )
        if args.image
        else generate_text_video(
            args.prompt,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
            aspect_ratio=args.aspect_ratio,
        )
    )
    if job is None:
        raise SystemExit(last_error() or "Pika submission failed")
    print(f"submitted video_id={job.video_id}")
    result = wait_for_video(job.video_id, timeout=args.timeout, poll_interval=args.poll_interval)
    if result is None:
        raise SystemExit(last_error() or "Pika generation did not complete")
    output = download_video(result, args.output)
    if output is None:
        raise SystemExit(last_error() or "Pika download failed")
    manifest = record_manifest(job, result, output)
    print(f"video: {output}")
    print(f"manifest: {manifest}")
    print("training eligibility: false (review and annotation required)")
    if args.extract_fps > 0:
        frames = extract_frames(output, output.with_suffix(""), fps=args.extract_fps)
        print(f"unlabeled review frames: {frames}")
    close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
