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


def test_sam_api_backend_requires_fal_key(monkeypatch):
    """No FAL_KEY -> a clear RuntimeError before any network call, not a crash."""
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("SAM_API_KEY", raising=False)
    from src.model.sam_api import SamApiBackend

    cfg = load_config()
    backend = SamApiBackend(cfg)
    with pytest.raises(RuntimeError, match="FAL_KEY"):
        next(iter(backend.track("dummy.mp4", cfg.sam_prompts)))


def test_get_backend_yolo_is_default():
    from src.model import get_backend
    from src.model.yolo_backend import YoloBackend

    cfg = load_config()
    assert cfg.sam_backend == "yolo"
    assert isinstance(get_backend(cfg), YoloBackend)


def test_yolo_prompts_map_to_coco_classes():
    from src.model.yolo_backend import _PROMPT_TO_COCO

    cfg = load_config()
    mapped = {_PROMPT_TO_COCO.get(p.lower()) for p in cfg.sam_prompts}
    assert None not in mapped          # every prompt maps to a COCO class
    assert mapped == {0, 32}           # person (players/keeper/ref) + sports ball


def test_yolo_to_frame_result_converts_boxes():
    """_to_frame_result handles an Ultralytics-Results-shaped object without ultralytics."""
    from src.model.yolo_backend import _to_frame_result

    class _Boxes:
        def __init__(self):
            self.xyxy = _Arr([[10.0, 20.0, 40.0, 80.0]])
            self.cls = _Arr([0])
            self.conf = _Arr([0.9])
            self.id = _Arr([7])

        def __len__(self):
            return 1

    class _Arr:
        def __init__(self, v):
            self._v = np.asarray(v)

        def cpu(self):
            return self

        def numpy(self):
            return self._v

    class _Result:
        orig_shape = (1504, 3840)
        names = {0: "person", 32: "sports ball"}
        boxes = _Boxes()

    fr = _to_frame_result(_Result(), frame_index=5, max_objects=None)
    assert fr.frame_index == 5 and fr.width == 3840 and fr.height == 1504
    assert len(fr.detections) == 1
    d = fr.detections[0]
    assert d.instance_id == 7 and d.label == "person"
    assert d.bbox == (10.0, 20.0, 30.0, 60.0) and d.score == 0.9


def test_detection_foot_and_center_xy():
    d = Detection(instance_id=1, label="player", bbox=(10.0, 20.0, 30.0, 40.0))
    assert d.center_xy == (25.0, 40.0)
    assert d.foot_xy == (25.0, 60.0)  # bottom-middle: x + w/2, y + h


def test_sam_local_backend_reads_hf_repo_from_config():
    from src.model.sam_local import HF_REPO, SamLocalBackend

    cfg = load_config()
    backend = SamLocalBackend(cfg)
    assert backend.repo_id == HF_REPO == "facebook/sam3"


def test_sam_local_backend_fails_loud_without_gpu(monkeypatch):
    """No CUDA -> require_gpu() raises before any HF network/auth call.

    On an actual CUDA box this instead proceeds to the from_pretrained() call,
    which will fail on network/auth in this sandboxed test environment — either
    outcome is acceptable; we only assert it never silently fabricates detections.
    """
    from src.model.sam_local import SamLocalBackend
    from src.utils.gpu import GPUNotAvailable

    monkeypatch.delenv("ALLOW_CPU", raising=False)
    cfg = load_config()
    backend = SamLocalBackend(cfg)
    try:
        next(iter(backend.track("dummy.mp4", cfg.sam_prompts)))
        raise AssertionError("expected this to fail without GPU/HF access in the test sandbox")
    except (GPUNotAvailable, ImportError, RuntimeError):
        pass
