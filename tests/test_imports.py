"""Smoke test: EVERY src module imports with zero heavy/optional deps installed.

This is the guarantee that the scaffold has no import-time errors — heavy imports
(torch, cv2, sentry, arize, redis, requests) must be deferred inside functions.
If someone adds a top-level `import torch`, this test fails immediately.
"""
import importlib
import pkgutil

import src


def _all_modules() -> list[str]:
    mods = ["src"]
    for info in pkgutil.walk_packages(src.__path__, prefix="src."):
        mods.append(info.name)
    return mods


def test_every_module_imports():
    failures = {}
    for name in _all_modules():
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - we want to report all failures
            failures[name] = f"{type(exc).__name__}: {exc}"
    assert not failures, "Modules failed to import:\n" + "\n".join(
        f"  {k}: {v}" for k, v in failures.items()
    )


def test_sam_factory_rejects_unknown_backend():
    from types import SimpleNamespace

    from src.model import get_backend

    bad = SimpleNamespace(sam_backend="nope")
    try:
        get_backend(bad)
        raise AssertionError("expected ValueError for unknown backend")
    except ValueError:
        pass
