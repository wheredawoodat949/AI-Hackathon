"""GPU / CUDA check that FAILS LOUDLY before any heavy run.

Per CLAUDE.md §2: assume CUDA; verify with torch.cuda.is_available() and fail
hard if False. Heavy steps (SAM inference, video decode/encode) must call
`require_gpu()` first so we never silently fall back to a 100x-slower CPU path.

    from src.utils.gpu import require_gpu, gpu_report
    print(gpu_report())     # human-readable, never raises
    dev = require_gpu()     # returns "cuda"; raises GPUNotAvailable otherwise

Escape hatch for pure-Python smoke tests only: set ALLOW_CPU=1 in .env. This is
ignored by anything that actually needs the GPU — it only relaxes require_gpu()
for loader/config tests on a laptop.
"""
from __future__ import annotations

import os


class GPUNotAvailable(RuntimeError):
    """Raised when a CUDA GPU is required but unavailable."""


def _torch():
    try:
        import torch  # noqa: WPS433 (deferred import: torch is heavy)

        return torch
    except ImportError as exc:  # pragma: no cover
        raise GPUNotAvailable(
            "PyTorch is not installed. Install the CUDA build on the GPU box:\n"
            "  see https://pytorch.org/get-started/locally/"
        ) from exc


def gpu_report() -> str:
    """Human-readable device summary. Never raises — safe to print anywhere."""
    try:
        torch = _torch()
    except GPUNotAvailable as exc:
        return f"[gpu] torch unavailable: {exc}"

    if torch.cuda.is_available():
        idx = torch.cuda.current_device()
        name = torch.cuda.get_device_name(idx)
        cap = ".".join(map(str, torch.cuda.get_device_capability(idx)))
        total_gb = torch.cuda.get_device_properties(idx).total_memory / 1e9
        return (
            f"[gpu] CUDA available: {name} (device {idx}, "
            f"compute {cap}, {total_gb:.1f} GB) | torch {torch.__version__}"
        )

    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return f"[gpu] No CUDA. Apple MPS available | torch {torch.__version__}"
    return f"[gpu] No CUDA device found | torch {torch.__version__}"


def require_gpu() -> str:
    """Return the device string for heavy work, or raise GPUNotAvailable.

    Returns "cuda" when a CUDA GPU is present. With ALLOW_CPU=1 set (smoke tests
    only) it returns "cpu" instead of raising. Never returns silently on a box
    that was supposed to have a GPU.
    """
    torch = _torch()
    if torch.cuda.is_available():
        return "cuda"

    if os.environ.get("ALLOW_CPU", "0") == "1":
        return "cpu"

    raise GPUNotAvailable(
        "No CUDA GPU detected and ALLOW_CPU != 1.\n"
        f"  {gpu_report()}\n"
        "Heavy runs require a CUDA GPU. If you are intentionally on a CPU box for a\n"
        "pure-Python smoke test, set ALLOW_CPU=1 in .env (loader/config only)."
    )


if __name__ == "__main__":
    # `python -m src.utils.gpu` — quick environment check.
    print(gpu_report())
    try:
        print(f"[gpu] require_gpu() -> {require_gpu()}")
    except GPUNotAvailable as exc:
        print(f"[gpu] require_gpu() FAILED:\n{exc}")
        raise SystemExit(1)
