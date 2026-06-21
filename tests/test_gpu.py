"""GPU check behavior (works with or without torch installed)."""
from src.utils.gpu import GPUNotAvailable, gpu_report, require_gpu


def test_gpu_report_never_raises():
    r = gpu_report()
    assert isinstance(r, str) and r.startswith("[gpu]")


def test_require_gpu_fails_loud_without_cuda(monkeypatch):
    """On a box with no CUDA and ALLOW_CPU unset, require_gpu must raise."""
    monkeypatch.delenv("ALLOW_CPU", raising=False)
    try:
        dev = require_gpu()
        # If we get here, this box actually has a CUDA GPU — that's fine.
        assert dev == "cuda"
    except GPUNotAvailable:
        pass  # expected on CPU-only / torch-less machines


def test_allow_cpu_escape_hatch(monkeypatch):
    monkeypatch.setenv("ALLOW_CPU", "1")
    try:
        assert require_gpu() in ("cuda", "cpu")
    except GPUNotAvailable:
        # Only happens if torch itself is missing; acceptable for a smoke box.
        pass
