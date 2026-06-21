"""Ball-Action Spotting / event classification (Role D — feat/events-demo, stretch).

The 12 BAS classes (see src.data.loader.BAS_LABELS) are the vocabulary for event
detection AND for Redis semantic search. Ground-truth events come from
Match.bas_events(). This module classifies events from tracked output and feeds
them to the highlight exporter + Redis.
"""
from __future__ import annotations

from typing import Iterable

from src.data.loader import BAS_LABELS, Event


def classify_events(tracked_frames: Iterable) -> list[Event]:
    """Predict BAS events from tracked output.

    TODO(Role D): implement a simple classifier over the 12 BAS_LABELS. Stretch
    goal — keep off the Phase 0-2 critical path.
    """
    _ = BAS_LABELS
    raise NotImplementedError("classify_events() not implemented yet (stretch).")
