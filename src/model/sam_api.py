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
