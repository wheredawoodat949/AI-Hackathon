"""Hosted SAM 3.1 backend (calls a remote endpoint).

Implements the SamBackend interface against a hosted API. Reads SAM_API_URL and
SAM_API_KEY from the environment (.env). `requests` is imported lazily so the
module imports without it installed.

Use this only if we end up with a hosted SAM 3 service (Modal/Replicate/RunPod).
For Colab/GPU runtimes there's no reason to add a network hop — run the weights
in-process with `sam.backend: local`. Left intentionally unimplemented until/
unless we host SAM 3; local is the primary path.
"""
from __future__ import annotations

from typing import Any, Sequence

from src.config import env
from src.model.sam_backend import TrackResult


class SamApiBackend:
    """SAM 3.1 via a hosted endpoint. No local GPU required."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.api_url = env("SAM_API_URL")
        self.api_key = env("SAM_API_KEY")

    def _require_creds(self) -> None:
        if not self.api_url:
            raise RuntimeError(
                "SAM_API_URL is not set. Add it to .env (or switch sam.backend to "
                "'local' in config.yaml)."
            )

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        self._require_creds()
        # import requests  # lazy: only needed when actually calling the API
        # TODO(Role A): POST video/frames + prompts; decode the response into
        # FrameResult(frame_index, (Detection(...), ...)) and yield per frame.
        raise NotImplementedError("SamApiBackend.track() not implemented yet.")

    def close(self) -> None:
        return None
