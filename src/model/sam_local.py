"""Self-hosted SAM 3.1 backend (runs weights on our GPU).

Implements the SamBackend interface. Heavy deps (torch, the SAM package) are
imported lazily inside methods so this module imports cleanly on any machine —
only constructing/using the backend requires the GPU stack.

Role A (tracking lead) fills in `track()`. Everything it needs is already typed
by the interface; return per-frame FrameResult(Detection(...)) streaming.
"""
from __future__ import annotations

from typing import Any, Sequence

from src.model.sam_backend import TrackResult


class SamLocalBackend:
    """SAM 3.1 with locally-loaded weights. Requires a CUDA GPU."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self._model = None  # lazily loaded in _ensure_model()

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        # Defer heavy imports + GPU check until we actually load weights.
        from src.utils.gpu import require_gpu

        device = require_gpu()  # fails loud if no CUDA (CLAUDE.md §2)
        # TODO(Role A): load SAM 3.1 weights onto `device` and assign self._model.
        raise NotImplementedError(
            "SamLocalBackend weight loading not implemented yet. "
            f"(device={device}) Load SAM 3.1 here, then implement track()."
        )

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        self._ensure_model()
        # TODO(Role A): run promptable concept segmentation + video tracking,
        # yielding FrameResult(frame_index, (Detection(...), ...)) per frame.
        raise NotImplementedError("SamLocalBackend.track() not implemented yet.")

    def close(self) -> None:
        self._model = None
