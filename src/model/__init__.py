"""model — SAM 3.1 backend abstraction + factory (CLAUDE.md §4).

Downstream code imports the interface/types and `get_backend()` from here and
NOTHING else from this package, so swapping local <-> api never ripples out:

    from src.model import get_backend
    from src.config import load_config

    cfg = load_config()
    backend = get_backend(cfg)                    # reads sam.backend: local | api
    for frame in backend.track(video, cfg.sam_prompts, max_frames=250):
        for det in frame.detections:
            print(frame.frame_index, det.instance_id, det.label, det.foot_xy)
"""
from __future__ import annotations

from src.model.sam_backend import Detection, FrameResult, SamBackend

__all__ = ["Detection", "FrameResult", "SamBackend", "get_backend"]


def get_backend(cfg=None) -> SamBackend:
    """Return the configured SAM backend. Reads config.yaml if `cfg` is None."""
    if cfg is None:
        from src.config import load_config

        cfg = load_config()

    backend = cfg.sam_backend.lower()
    if backend == "local":
        from src.model.sam_local import SamLocalBackend

        sam_cfg = cfg.raw.get("sam", {})
        return SamLocalBackend(
            weights=sam_cfg.get("weights", "sam3.pt"),
            device=cfg.device,
        )
    if backend == "api":
        from src.model.sam_api import SamApiBackend

        return SamApiBackend()
    raise ValueError(f"Unknown sam.backend {backend!r} — expected 'local' or 'api'.")
