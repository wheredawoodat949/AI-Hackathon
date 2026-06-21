"""SAM 3.1 model abstraction (CLAUDE.md §4).

Downstream code imports ONLY from here:
    from src.model import get_backend, SamBackend, Detection, FrameResult
"""

from src.model.sam_backend import (
    Detection,
    FrameResult,
    SamBackend,
    TrackResult,
    get_backend,
)

__all__ = [
    "Detection",
    "FrameResult",
    "SamBackend",
    "TrackResult",
    "get_backend",
    "GsrReplayBackend",
]


def __getattr__(name):  # lazy: avoid importing the loader unless replay is used
    if name == "GsrReplayBackend":
        from src.model.replay import GsrReplayBackend

        return GsrReplayBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
