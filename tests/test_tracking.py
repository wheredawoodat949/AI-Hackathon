"""Phase 1 tracking: visualize + GSR replay backend.

cv2-dependent tests importorskip cv2; data-dependent tests skip if the dev match
isn't downloaded — so `make test` stays green on a bare machine.
"""

import numpy as np
import pytest

from src.config import load_config
from src.model import Detection, FrameResult
from src.model.replay import _PROMPT_TO_ROLE


def test_prompt_to_role_covers_sam_prompts():
    cfg = load_config()
    mapped = {_PROMPT_TO_ROLE.get(p.lower()) for p in cfg.sam_prompts}
    # every configured prompt maps to a real GSR role
    assert None not in mapped
    assert {"player", "goalkeeper", "referee", "ball"} <= set(_PROMPT_TO_ROLE.values())


def test_draw_detections_preserves_shape_and_draws():
    cv2 = pytest.importorskip("cv2")  # noqa: F841
    from src.data.video import blank_frame
    from src.tracking.visualize import draw_detections

    frame = blank_frame(320, 200)
    dets = [Detection(instance_id=7, label="player", bbox=(50, 40, 30, 60), score=1.0)]
    out = draw_detections(frame, dets)
    assert out.shape == frame.shape
    assert not np.array_equal(out, frame), "expected something to be drawn"


def _have_dev_data() -> bool:
    cfg = load_config()
    return (cfg.data_root / "gsr" / cfg.dev_match).is_dir()


@pytest.mark.skipif(not _have_dev_data(), reason="dev match not downloaded")
def test_replay_backend_emits_detections():
    from src.model.replay import GsrReplayBackend

    cfg = load_config()
    backend = GsrReplayBackend(cfg, half=1)
    first = next(iter(backend.track("", cfg.sam_prompts)))
    assert isinstance(first, FrameResult)
    assert len(first.detections) > 0
    d = first.detections[0]
    assert len(d.bbox) == 4 and d.score == 1.0
    backend.close()
