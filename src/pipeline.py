"""End-to-end orchestration entrypoint (CLAUDE.md §9).

Sequences the stages each role owns; holds NO logic itself. This skeleton makes
the wiring explicit and importable now — each stage raises NotImplementedError
until its owner fills it in, but the shape is stable so the notebook and frontend
can target `from src.pipeline import run` from day one.

Target flow (§9): match clip -> SAM 3.1 track -> stabilize IDs -> pitch coords ->
minimap -> HOTA vs GSR -> sponsors live -> one Redis query.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import Config, load_config


@dataclass
class PipelineResult:
    """What a run produces (filled in as stages come online)."""

    match_id: str
    minimap_video: Path | None = None
    hota: dict | None = None
    notes: str = ""


def run(
    video_path: str | Path,
    *,
    match_id: str | None = None,
    cfg: Config | None = None,
) -> PipelineResult:
    """Run the full pipeline on one clip. Stages are wired but not all implemented.

    Order matters: tracking (Role A) -> pitch+eval (Role B) -> sponsors (Role C,
    off critical path) -> events (Role D, stretch).
    """
    cfg = cfg or load_config()
    match_id = match_id or cfg.dev_match

    # --- sponsors: init off the critical path; failures must not stop the run ---
    _init_sponsors(cfg)

    # --- Role A: tracking ---
    from src.model import get_backend
    from src.tracking.tracker import stabilize

    backend = get_backend(cfg)
    frames = stabilize(backend.track(str(video_path), cfg.sam_prompts,
                                     max_objects=cfg.max_tracked))

    # --- Role B: pitch mapping + minimap + HOTA (consumes `frames`) ---
    # TODO(Role B): homography -> pitch coords -> render_minimap -> run_gs_hota.
    _ = frames
    raise NotImplementedError(
        "pipeline.run() is wired but Role A/B stages aren't implemented yet. "
        "See PROGRESS.md for the current per-phase demo commands."
    )


def _init_sponsors(cfg: Any) -> None:
    """Best-effort sponsor init; never raises (CLAUDE.md §6)."""
    try:
        from src.obs import arize, sentry
        from src.store import redis_store

        sentry.init(cfg)
        arize.init(cfg)
        redis_store.init(cfg)
    except Exception:  # noqa: BLE001 - sponsors are never on the critical path
        pass
