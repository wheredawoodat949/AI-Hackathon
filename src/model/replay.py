"""GsrReplayBackend — a SAM backend that replays GSR ground truth (Role A).

Why this exists: it satisfies the exact `SamBackend` interface but emits the GSR
ground-truth boxes instead of running a model. That buys us three things with ZERO
GPU and only the data we already have:

  1. Build + verify the whole track -> visualize -> video -> (pitch -> eval) pipeline
     end-to-end on a laptop, before SAM is wired in.
  2. A "perfect tracker" upper bound — eval against it should score ~1.0 HOTA, which
     sanity-checks the eval harness itself (Role B).
  3. A demo that runs anywhere if the real GPU/SAM path isn't ready by the deadline.

Swap `get_backend()` to `local`/`api` once SAM works; downstream code doesn't change.
"""
from __future__ import annotations

from typing import Any, Iterator, Sequence

from src.model.sam_backend import Detection, FrameResult, TrackResult

# Map SAM-style noun-phrase prompts to GSR roles, so `prompts` actually filters.
_PROMPT_TO_ROLE = {
    "soccer player": "player",
    "player": "player",
    "goalkeeper": "goalkeeper",
    "keeper": "goalkeeper",
    "referee": "referee",
    "sports ball": "ball",
    "ball": "ball",
}


class GsrReplayBackend:
    """Emits GSR ground-truth entities as if they were SAM detections."""

    def __init__(self, cfg: Any, *, match_id: str | None = None, half: int = 1) -> None:
        from src.data.loader import load_match

        self.cfg = cfg
        self.match_id = str(match_id or cfg.dev_match)
        self.half = half
        self._match = load_match(cfg.data_root, self.match_id)

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        wanted = {_PROMPT_TO_ROLE.get(p.strip().lower()) for p in prompts}
        wanted.discard(None)
        return self._frames(wanted, max_objects)

    def _frames(self, wanted_roles: set, max_objects: int | None) -> Iterator[FrameResult]:
        for frame in self._match.gsr_frames(self.half):
            dets = []
            for e in frame.entities:
                if wanted_roles and e.role not in wanted_roles:
                    continue
                if e.bbox_image is None:
                    continue
                dets.append(
                    Detection(
                        instance_id=e.track_id,
                        label=e.role,
                        bbox=tuple(float(v) for v in e.bbox_image),  # x, y, w, h
                        mask=None,
                        score=1.0,
                    )
                )
                if max_objects is not None and len(dets) >= max_objects:
                    break
            yield FrameResult(frame_index=frame.image_id, detections=tuple(dets))

    def close(self) -> None:
        self._match = None
