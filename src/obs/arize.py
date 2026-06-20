"""Arize logging (Role C — feat/sponsors).

Log every tracking/event prediction and build an eval set from GSR ground truth
so we can show a real HOTA delta before/after tuning (CLAUDE.md §6 — the number
must be real and citable). Behind `sponsors.arize` + ARIZE_API_KEY/SPACE_ID.
arize imported lazily; a no-op when disabled.
"""
from __future__ import annotations

from typing import Any

from src.config import env

_client = None


def init(cfg: Any) -> bool:
    """Initialize the Arize client if enabled + credentials present."""
    global _client
    if not cfg.sponsor_enabled("arize"):
        return False
    api_key, space_id = env("ARIZE_API_KEY"), env("ARIZE_SPACE_ID")
    if not (api_key and space_id):
        return False
    try:
        from arize.api import Client

        _client = Client(space_id=space_id, api_key=api_key)
    except Exception:  # noqa: BLE001 - never break the pipeline
        _client = None
    return _client is not None


def log_prediction(record: dict) -> None:
    """Log one prediction record. No-op when disabled.

    TODO(Role C): map `record` to Arize's schema and send via _client.
    """
    if _client is None:
        return
    # TODO(Role C): _client.log(...)
