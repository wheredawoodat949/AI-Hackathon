"""SAM 3.1 backend abstraction (CLAUDE.md §4) — the architectural lynchpin.

We don't yet know if SAM 3.1 runs self-hosted on our GPU or via a hosted API, so
ALL downstream code (tracking, pitch, eval) depends ONLY on the `SamBackend`
interface and the `Detection`/`FrameResult` data shapes below — never on a
concrete backend. Swap local<->api<->replay by flipping `sam.backend` in config.yaml.

    from src.model import get_backend
    backend = get_backend()                      # reads config.yaml: local | api | replay
    for fr in backend.track(video_path, ["soccer player", "goalkeeper"]):
        for det in fr.detections:
            det.instance_id, det.bbox, det.label, det.foot_xy

Reference behavior: SAM 3.1 takes simple noun-phrase prompts ("soccer player",
"goalkeeper", "referee", "sports ball") and returns masks + persistent IDs for
every matching instance, tracked across frames. It does NOT handle complex
referring expressions, and inference cost scales ~linearly with tracked objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterator, Protocol, Sequence, runtime_checkable

if TYPE_CHECKING:  # heavy/optional types only for static checkers, never at runtime
    import numpy as np


@dataclass(frozen=True)
class Detection:
    """One tracked instance in one frame.

    `bbox` is (x, y, w, h) in image pixels. `mask` is a boolean HxW array (or RLE)
    when available, else None — kept `Any` so this module imports with zero heavy
    deps (numpy is optional here).
    """

    instance_id: int
    label: str
    bbox: tuple[float, float, float, float]  # x, y, w, h in image pixels
    mask: "np.ndarray | Any | None" = None
    score: float | None = None

    @property
    def foot_xy(self) -> tuple[float, float]:
        """Bottom-middle of the bbox in pixels — the point Phase 2 projects to pitch.

        Matches how SoccerTrack v2 GSR ground truth stores positions (bbox bottom-middle).
        """
        x, y, w, h = self.bbox
        return (x + w / 2.0, y + h)

    @property
    def center_xy(self) -> tuple[float, float]:
        x, y, w, h = self.bbox
        return (x + w / 2.0, y + h / 2.0)


@dataclass(frozen=True)
class FrameResult:
    """All instances SAM tracked in a single video frame."""

    frame_index: int
    detections: tuple[Detection, ...] = field(default_factory=tuple)

    def of_label(self, label: str) -> tuple[Detection, ...]:
        return tuple(d for d in self.detections if d.label == label)


# A TrackResult is just an iterator of per-frame results — lets backends stream
# frames lazily instead of materializing a whole 4K video in memory.
TrackResult = Iterator[FrameResult]


@runtime_checkable
class SamBackend(Protocol):
    """The one interface downstream code is allowed to depend on."""

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        """Yield per-frame detections for every instance matching `prompts`."""
        ...

    def close(self) -> None:
        """Release weights / sessions / sockets. Safe to call twice."""
        ...


def get_backend(cfg: Any | None = None) -> SamBackend:
    """Factory: return the configured backend (`sam.backend` in config.yaml).

    Downstream code calls this and nothing else. Adding a 4th backend = add a
    module + one branch here.
    """
    from src.config import load_config

    cfg = cfg or load_config()
    backend = cfg.sam_backend.lower()
    if backend == "local":
        from src.model.sam_local import SamLocalBackend

        return SamLocalBackend(cfg)
    if backend == "api":
        from src.model.sam_api import SamApiBackend

        return SamApiBackend(cfg)
    if backend == "replay":
        # No-GPU ground-truth replay — runs the whole pipeline on data we already have.
        from src.model.replay import GsrReplayBackend

        return GsrReplayBackend(cfg)
    raise ValueError(
        f"Unknown sam.backend={backend!r} in config.yaml. Expected 'local', 'api', or 'replay'."
    )
