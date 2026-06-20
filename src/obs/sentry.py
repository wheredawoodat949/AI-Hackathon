"""Sentry instrumentation (Role C — feat/sponsors).

Reliability monitoring: dropped frames, model timeouts, tracker ID-swaps. Behind
the `sponsors.sentry` config flag and the SENTRY_DSN env var — a no-op when off,
so it can NEVER break the core pipeline (CLAUDE.md §6). sentry_sdk imported lazily.

    from src.obs import sentry
    sentry.init(cfg)                       # no-op unless enabled + DSN present
    sentry.capture("tracker_id_swap", extra={...})
"""
from __future__ import annotations

from typing import Any

from src.config import env

_enabled = False


def init(cfg: Any) -> bool:
    """Initialize Sentry if enabled in config AND SENTRY_DSN is set. Returns active state."""
    global _enabled
    if not cfg.sponsor_enabled("sentry"):
        return False
    dsn = env("SENTRY_DSN")
    if not dsn:
        return False
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)
        _enabled = True
    except Exception:  # noqa: BLE001 - sponsors must never crash the pipeline
        _enabled = False
    return _enabled


def capture(message: str, *, extra: dict | None = None) -> None:
    """Record an event/exception if Sentry is active; otherwise a no-op."""
    if not _enabled:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for k, v in (extra or {}).items():
                scope.set_extra(k, v)
            sentry_sdk.capture_message(message)
    except Exception:  # noqa: BLE001
        pass
