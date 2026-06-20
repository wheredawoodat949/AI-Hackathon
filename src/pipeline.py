"""End-to-end orchestration entrypoint (filled in across phases).

Target shape (CLAUDE.md §9): load match clip → SAM 3.1 track → render minimap →
HOTA vs GSR → sponsors live → one Redis query. Each stage lives in its own
`src/` package and is wired here. Phase 0 only stubs the entrypoint so notebooks
and the future frontend have a single, stable import:

    from src.pipeline import run   # not implemented until Phase 1+

Keep ALL logic in the stage modules; this file only sequences them and reads
config. Sponsors are consumed off the critical path, never inline here.
"""
from __future__ import annotations

from src.config import Config, load_config


def run(cfg: Config | None = None):
    """Run the full pipeline. Not implemented yet — built up Phase 1 → Phase 4."""
    cfg = cfg or load_config()
    raise NotImplementedError(
        "pipeline.run() is a Phase 1+ entrypoint. Phase 0 ships data loading + GPU "
        "check only. See PROGRESS.md for the current demo command."
    )
