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
]
