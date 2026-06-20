"""SoccerTrack v2 GSR/BAS reader — self-contained, dependency-free.

Mirrors the verified on-disk schema of atomscott/soccertrack-v2 (see the dataset
repo's docs/format-gsr.md & docs/format-bas.md). We parse data here; we do NOT
reimplement eval metrics — HOTA/MOT/BAS scoring uses the dataset package's
`src.evaluation.*` per CLAUDE.md §5.

On-disk layout under the data root:
    gsr/<id>/<id>_1st.json , <id>_2nd.json      # per-frame entity records
    bas/<id>/<id>_12_class_events.json          # ball-action events
    videos/<id>...                              # panoramic mp4s (not parsed here)

Usage:
    from src.data.loader import load_match
    m = load_match("./data", match_id="117093")
    frame = m.gsr_frames(half=1)[0]
    for p in frame.entities:
        print(frame.image_id, p.track_id, p.role, p.jersey_number, p.x, p.y)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Literal, Optional

Role = Literal["player", "goalkeeper", "referee", "other"]
TeamSide = Literal["left", "right"]

FPS: int = 25

# The 12 BAS action classes (CLAUDE.md §5). The real files store them UPPERCASE
# (e.g. "PASS", "HIGH PASS"); we compare/normalize case-insensitively rather than
# hard-failing, since the on-disk casing differs from the docs' Title Case.
BAS_LABELS: tuple[str, ...] = (
    "Pass",
    "Drive",
    "Header",
    "High Pass",
    "Out",
    "Cross",
    "Throw In",
    "Shot",
    "Ball Player Block",
    "Player Successful Tackle",
    "Free Kick",
    "Goal",
)
_BAS_BY_UPPER: dict[str, str] = {lbl.upper(): lbl for lbl in BAS_LABELS}


def normalize_bas_label(label: str) -> str:
    """Map an on-disk label ('PASS', 'HIGH PASS') to canonical Title Case if known."""
    return _BAS_BY_UPPER.get(label.strip().upper(), label.strip())


@dataclass(frozen=True)
class Player:
    """Per-frame GSR record for one entity (player/keeper/referee/other)."""

    track_id: int
    role: Role
    jersey_number: Optional[int]
    team_side: Optional[TeamSide]
    x: float  # pitch coords in meters
    y: float
    player_id: Optional[str | int] = None
    bbox_image: Optional[tuple[int, int, int, int]] = None
    bbox_pitch: Optional[tuple[float, float, float, float]] = None


@dataclass(frozen=True)
class Frame:
    """All GSR entities observed in a single panoramic frame of a half."""

    half: int
    image_id: int
    entities: tuple[Player, ...]

    @property
    def t_ms(self) -> int:
        return int(round(self.image_id * 1000 / FPS))


@dataclass(frozen=True)
class Event:
    """One BAS (ball-action) annotation."""

    half: int
    clock: str  # "mm:ss" within the half
    t_ms: int  # ms since kickoff of `half`
    label: str
    team: Optional[TeamSide] = None
    player_id: Optional[str | int] = None
    visibility: Optional[str] = None

    @property
    def image_id(self) -> int:
        return int(round(self.t_ms * FPS / 1000))


@dataclass
class Match:
    """A lazy handle to one match; JSONs parse on first access per half."""

    root: Path
    match_id: str
    _gsr_cache: dict[int, tuple[Frame, ...]] = field(default_factory=dict, repr=False)
    _bas_cache: Optional[tuple[Event, ...]] = field(default=None, repr=False)

    # ---- GSR -----------------------------------------------------------------

    def gsr_path(self, half: int) -> Path:
        return self.root / "gsr" / self.match_id / f"{self.match_id}_{_half_suffix(half)}.json"

    def gsr_frames(self, half: int) -> tuple[Frame, ...]:
        if half not in self._gsr_cache:
            self._gsr_cache[half] = tuple(_parse_gsr(self.gsr_path(half), half))
        return self._gsr_cache[half]

    def gsr_frame(self, half: int, image_id: int) -> Optional[Frame]:
        """O(log n) lookup of the Frame at `image_id` (None if absent)."""
        frames = self.gsr_frames(half)
        lo, hi = 0, len(frames)
        while lo < hi:
            mid = (lo + hi) // 2
            if frames[mid].image_id < image_id:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(frames) and frames[lo].image_id == image_id:
            return frames[lo]
        return None

    def first_gsr_frame(self) -> Frame:
        """First frame of half 1 — handy for smoke tests and demos."""
        frames = self.gsr_frames(half=1)
        if not frames:
            raise ValueError(f"No GSR frames for match {self.match_id} half 1.")
        return frames[0]

    # ---- BAS -----------------------------------------------------------------

    def bas_path(self) -> Path:
        return self.root / "bas" / self.match_id / f"{self.match_id}_12_class_events.json"

    def bas_events(self) -> tuple[Event, ...]:
        if self._bas_cache is None:
            self._bas_cache = tuple(_parse_bas(self.bas_path()))
        return self._bas_cache

    def events_of(self, label: str) -> tuple[Event, ...]:
        target = normalize_bas_label(label)
        return tuple(e for e in self.bas_events() if e.label == target)


# ---- Parsers -----------------------------------------------------------------


def _half_suffix(half: int) -> str:
    if half == 1:
        return "1st"
    if half == 2:
        return "2nd"
    raise ValueError(f"half must be 1 or 2, got {half!r}")


# The real GSR files are SoccerNet Game-State-Reconstruction / COCO format:
#   {info, images:[{image_id, file_name, ...}], annotations:[...], categories:[...]}
# Object annotations (categories 1-4,7 = player/goalkeeper/referee/ball/other) carry
# track_id, attributes{role,jersey,team,player_id}, bbox_image{x,y,w,h},
# bbox_pitch{...x_bottom_middle,y_bottom_middle}. We expose each as a Player whose
# (x, y) is the on-pitch foot position in meters (bbox_pitch bottom-middle).
_OBJECT_SUPERCATEGORY = "object"


def _parse_gsr(path: Path, half: int) -> Iterator[Frame]:
    if not path.exists():
        raise FileNotFoundError(
            f"GSR annotation not found: {path}\n"
            "Has the match been downloaded? Run: python -m src.data.download --match <id>"
        )
    data = json.loads(path.read_text())
    # image_id (str) -> frame number (int) from the MOT-style file name (000001.jpg -> 1)
    frame_of: dict[str, int] = {}
    for img in data.get("images", []):
        frame_of[str(img["image_id"])] = _frame_number(img)
    cat_name: dict[int, str] = {c["id"]: c["name"] for c in data.get("categories", [])}

    grouped: dict[int, list[Player]] = {}
    for a in data.get("annotations", []):
        if a.get("supercategory") != _OBJECT_SUPERCATEGORY:
            continue  # skip pitch lines / camera calibration records
        fno = frame_of.get(str(a["image_id"]))
        if fno is None:
            continue
        grouped.setdefault(fno, []).append(_player_from(a, cat_name))
    for fno in sorted(grouped):
        yield Frame(half=half, image_id=fno, entities=tuple(grouped[fno]))


def _frame_number(img: dict) -> int:
    """MOT frame index from an images[] record (file_name '000123.jpg' -> 123)."""
    name = str(img.get("file_name", ""))
    stem = name.rsplit(".", 1)[0]
    if stem.isdigit():
        return int(stem)
    # fallback: last 6 digits of the string image_id
    iid = str(img["image_id"])
    return int(iid[-6:]) if iid[-6:].isdigit() else int(iid)


def _player_from(a: dict, cat_name: dict[int, str]) -> Player:
    attrs = a.get("attributes") or {}
    role = attrs.get("role") or cat_name.get(a.get("category_id"), "other")
    bi = a.get("bbox_image") or {}
    bbox_image = (
        (int(bi["x"]), int(bi["y"]), int(bi["w"]), int(bi["h"]))
        if {"x", "y", "w", "h"} <= bi.keys()
        else None
    )
    bp = a.get("bbox_pitch") or {}
    x = _maybe_float(bp.get("x_bottom_middle"))
    y = _maybe_float(bp.get("y_bottom_middle"))
    bbox_pitch = (
        (
            _maybe_float(bp.get("x_bottom_left")),
            _maybe_float(bp.get("y_bottom_left")),
            _maybe_float(bp.get("x_bottom_right")),
            _maybe_float(bp.get("y_bottom_right")),
        )
        if bp
        else None
    )
    return Player(
        track_id=int(a["track_id"]),
        role=role,
        jersey_number=_maybe_int(attrs.get("jersey")),
        team_side=attrs.get("team"),
        x=x if x is not None else float("nan"),
        y=y if y is not None else float("nan"),
        player_id=attrs.get("player_id"),
        bbox_image=bbox_image,  # type: ignore[arg-type]
        bbox_pitch=bbox_pitch,  # type: ignore[arg-type]
    )


def _parse_bas(path: Path) -> Iterator[Event]:
    # Real BAS file: {match_id, fps, actions:[{gameTime:"1 - 0:01", label:"PASS",
    #                 position:"680"(ms), team, player_id}]}
    if not path.exists():
        raise FileNotFoundError(f"BAS annotation not found: {path}")
    data = json.loads(path.read_text())
    for a in data.get("actions", []):
        half_str, clock = a["gameTime"].split(" - ")
        yield Event(
            half=int(half_str),
            clock=clock.strip(),
            t_ms=int(a["position"]),
            label=normalize_bas_label(a["label"]),
            team=a.get("team"),
            player_id=a.get("player_id"),
            visibility=a.get("visibility"),
        )


def _maybe_int(v) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _maybe_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---- Public entry points -----------------------------------------------------


def load_match(root: str | Path, match_id: str) -> Match:
    """Return a lazy Match rooted at `root` (the folder containing gsr/, bas/, ...)."""
    root = Path(root)
    if not (root / "gsr").is_dir():
        raise FileNotFoundError(
            f"Expected `gsr/` under {root}. Is this a SoccerTrack v2 root? "
            "Download a match first: python -m src.data.download --match <id>"
        )
    return Match(root=root, match_id=str(match_id))


def list_matches(root: str | Path) -> list[str]:
    """Available match IDs (sorted) under a SoccerTrack v2 root."""
    root = Path(root)
    gsr_root = root / "gsr"
    if not gsr_root.is_dir():
        return []
    return sorted(p.name for p in gsr_root.iterdir() if p.is_dir())


def iter_matches(root: str | Path) -> Iterable[Match]:
    for mid in list_matches(root):
        yield load_match(root, mid)
