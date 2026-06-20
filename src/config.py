"""Load config.yaml + .env once and hand back a typed-ish config object.

    from src.config import load_config
    cfg = load_config()
    cfg.dev_match            # "117093"
    cfg.data_root            # Path("./data")
    cfg.sam_backend          # "api"
    cfg.split["train"]       # [...]

No other module hardcodes paths, match IDs, or prompt strings — they all read
from here. `.env` is loaded as a side effect so os.environ has the secrets.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is a hard dep, but degrade gracefully
    def load_dotenv(*_a, **_k):  # type: ignore
        return False

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any]
    repo_root: Path

    # --- paths ---
    @property
    def data_root(self) -> Path:
        return self._path(self.raw["paths"]["data_root"])

    @property
    def outputs(self) -> Path:
        return self._path(self.raw["paths"]["outputs"])

    # --- dataset ---
    @property
    def hf_repo_id(self) -> str:
        return self.raw["dataset"]["hf_repo_id"]

    @property
    def revision(self) -> str:
        return self.raw["dataset"]["revision"]

    @property
    def fps(self) -> int:
        return int(self.raw["dataset"]["fps"])

    @property
    def gdrive_mirror(self) -> str | None:
        return self.raw["dataset"].get("gdrive_mirror")

    @property
    def source(self) -> str:
        return self.raw["dataset"].get("source", "hf")

    @property
    def dev_match(self) -> str:
        return str(self.raw["dataset"]["dev_match"])

    @property
    def split(self) -> dict[str, list[str]]:
        return self.raw["dataset"]["split"]

    @property
    def held_out(self) -> list[str]:
        """eval + test matches — never train on these."""
        return list(self.split.get("eval", [])) + list(self.split.get("test", []))

    # --- SAM ---
    @property
    def sam_backend(self) -> str:
        return self.raw["sam"]["backend"]

    @property
    def sam_prompts(self) -> list[str]:
        return list(self.raw["sam"]["prompts"])

    @property
    def max_tracked(self) -> int:
        return int(self.raw["sam"]["max_tracked"])

    # --- sponsors ---
    def sponsor_enabled(self, name: str) -> bool:
        return bool(self.raw.get("sponsors", {}).get(name, False))

    # --- run knobs ---
    @property
    def clip_seconds(self) -> int:
        return int(self.raw["run"]["clip_seconds"])

    @property
    def device(self) -> str:
        return self.raw["run"]["device"]

    # --- helpers ---
    def _path(self, value: str) -> Path:
        p = Path(value)
        return p if p.is_absolute() else (self.repo_root / p)


def load_config(path: str | Path | None = None) -> Config:
    """Read config.yaml and load .env. Cached-free: cheap enough to call freely."""
    load_dotenv(REPO_ROOT / ".env")
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {cfg_path}")
    raw = yaml.safe_load(cfg_path.read_text()) or {}
    return Config(raw=raw, repo_root=REPO_ROOT)


def env(name: str, default: str | None = None) -> str | None:
    """Read a secret from the environment (populated from .env by load_config)."""
    return os.environ.get(name, default)
