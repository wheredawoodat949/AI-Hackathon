<<<<<<< HEAD
"""Hosted-endpoint SAM 3.1 backend (CLAUDE.md §4) — stub.

Same `SamBackend` interface as `sam_local`, but talks to a remote SAM 3 endpoint
over HTTP instead of running weights in-process. Use this only if we end up with
a hosted SAM 3 service (e.g. a Modal/Replicate/RunPod endpoint) rather than a
Colab/GPU runtime. For Colab, use `sam.backend: local` — there's no reason to add
a network hop when the weights run right there on the T4/L4.

Wire it up by setting in .env:
    SAM_API_URL=https://<your-endpoint>/track
    SAM_API_KEY=<token>
and `sam.backend: api` in config.yaml. The response contract should mirror
FrameResult (per-frame instances with id/label/score/bbox). Left intentionally
unimplemented until/unless we host SAM 3 — local is the primary path.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

from src.config import env
from src.model.sam_backend import FrameResult


class SamApiBackend:
    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self.url = url or env("SAM_API_URL")
        self.api_key = api_key or env("SAM_API_KEY")

    def track(
        self,
        video_path: str | Path,
        prompts: list[str],
        *,
        max_frames: Optional[int] = None,
        include_masks: bool = False,
    ) -> Iterator[FrameResult]:
        raise NotImplementedError(
            "Hosted SAM 3 backend is not implemented — we run SAM 3 locally on the\n"
            "Colab/GPU runtime (sam.backend: local). Implement this only if we stand\n"
            "up a remote SAM 3 endpoint; until then set sam.backend: local."
        )
=======
"""Hosted SAM 3.1 backend (calls a remote endpoint).

Implements the SamBackend interface against a hosted API. Reads SAM_API_URL and
SAM_API_KEY from the environment (.env). `requests` is imported lazily so the
module imports without it installed.

Role A (tracking lead): implement `track()` to POST the video/frames + prompts
and stream decoded FrameResults. Keep the wire format isolated here — nothing
downstream knows this is an API.
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
>>>>>>> origin/main
