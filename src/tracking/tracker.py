"""Tracker / ID management (Role A — feat/tracking).

SAM 3.1 already emits persistent instance IDs, but we still need a thin layer to:
  - stabilize IDs across dropped frames / re-detections,
  - map SAM instance_id -> our stable track_id,
  - flag ID-swaps (Sentry alerts on these, CLAUDE.md §6).

Consumes SamBackend output (src.model.FrameResult); emits stable tracks. Pure
Python + numpy only — no GPU here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from src.model import FrameResult


@dataclass
class Track:
    """One entity followed across frames."""

    track_id: int
    label: str
    last_frame: int = -1
    history: list[tuple[int, tuple[float, float, float, float]]] = field(default_factory=list)


def stabilize(frames: Iterable[FrameResult]) -> Iterator[FrameResult]:
    """Re-key SAM instance_ids to stable track_ids and smooth gaps.

    TODO(Role A): implement ID stabilization + swap detection. For now this is a
    pass-through so the pipeline wiring is testable end-to-end.
    """
    for fr in frames:
        yield fr
