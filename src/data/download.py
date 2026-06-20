"""Fetch ONE SoccerTrack v2 match — Hugging Face (default) or Google Drive mirror.

Two sources (CLAUDE.md §6.1 acquire step), selectable via config `dataset.source`
or `--source`:
  * hf    — canonical, GATED (needs HF_TOKEN / `hf auth login`). Supports per-match
            allow_patterns so we never pull all ~900 min of 4K. PREFERRED.
  * drive — the official Drive mirror (folder shared with the owner; no HF gating),
            fetched with `gdown`. Coarser: pulls the whole mirror folder (mirrors
            may lag and may be video-only) — use when HF gating blocks you.

CLI:
    python -m src.data.download                       # dev_match (117093) via config source
    python -m src.data.download --match 117094
    python -m src.data.download --match 117093 --no-videos     # HF annotations only (fast)
    python -m src.data.download --source drive                 # whole Drive mirror via gdown

Programmatic:
    from src.data.download import download_match
    root = download_match("117093", include_videos=False)         # HF
    root = download_match("117093", source="drive")               # Drive mirror

The annotations (gsr/bas/mot) are small; the panoramic videos are large. For
Phase 0 you only need annotations to print a GSR frame, so HF + --no-videos is the
fast path. Phase 1 needs the video.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from src.config import load_config


def _allow_patterns(match_id: str, include_videos: bool) -> list[str]:
    pats = [
        f"gsr/{match_id}/*",
        f"bas/{match_id}/*",
        f"mot/{match_id}/*",
        f"raw/{match_id}/*",
    ]
    if include_videos:
        pats.append(f"videos/{match_id}*")
    return pats


def download_match(
    match_id: str,
    *,
    dest: str | Path | None = None,
    include_videos: bool = True,
    repo_id: str | None = None,
    revision: str | None = None,
    source: str | None = None,
) -> Path:
    """Download one match into `dest` (default: cfg.data_root). Returns the root.

    source="hf" (default) uses per-match allow_patterns; source="drive" pulls the
    whole official mirror with gdown. Either way the result is a SoccerTrack v2
    root (gsr/, bas/, ...) that loader.load_match can read.
    """
    cfg = load_config()
    dest = Path(dest) if dest else cfg.data_root
    source = (source or cfg.source).lower()
    dest.mkdir(parents=True, exist_ok=True)

    if source == "drive":
        return _download_drive_mirror(dest, cfg.gdrive_mirror, match_id, include_videos)
    if source != "hf":
        raise SystemExit(f"Unknown source {source!r}. Expected 'hf' or 'drive'.")

    repo_id = repo_id or cfg.hf_repo_id
    revision = revision or cfg.revision

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "huggingface_hub not installed. pip install -U huggingface_hub"
        ) from exc

    patterns = _allow_patterns(match_id, include_videos)
    kind = "annotations + videos" if include_videos else "annotations only"
    print(f"[download] match {match_id} ({kind}) via HF -> {dest}")
    print(f"[download] repo={repo_id} revision={revision}")
    print(f"[download] allow_patterns={patterns}")

    try:
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            local_dir=str(dest),
            allow_patterns=patterns,
        )
    except Exception as exc:  # noqa: BLE001 - surface the gating hint, then re-raise
        msg = str(exc)
        if "401" in msg or "RepositoryNotFound" in msg or "gated" in msg.lower():
            print(
                "\n[download] HF returned an auth/gating error. This dataset is GATED.\n"
                "  Fix: accept terms at https://huggingface.co/datasets/atomscott/soccertrack-v2\n"
                "       then `hf auth login` (or set HF_TOKEN in .env).\n"
                "  Or fall back to the Drive mirror: python -m src.data.download --source drive\n"
            )
        raise
    print(f"[download] done. SoccerTrack v2 root: {dest.resolve()}")
    return dest


_DRIVE_KINDS = ("gsr", "bas", "mot", "raw", "videos")


def _drive_match_files(entries, match_id: str, include_videos: bool) -> list[tuple[str, str]]:
    """Filter a gdown folder listing to exactly one match's files.

    The mirror's relative paths are clean: `<kind>/<id>/<file>` for annotations
    and `videos/<id>_...` for video. Returns (file_id, relative_path) pairs.
    """
    selected: list[tuple[str, str]] = []
    for e in entries:
        parts = e.path.split("/")
        if not parts or parts[0] not in _DRIVE_KINDS:
            continue
        if parts[-1].startswith("."):  # .DS_Store etc.
            continue
        kind = parts[0]
        if kind == "videos":
            if not include_videos:
                continue
            if not parts[-1].startswith(match_id):  # videos/<id>_panorama_...mp4
                continue
        else:
            if len(parts) < 2 or parts[1] != match_id:  # <kind>/<id>/<file>
                continue
        selected.append((e.id, e.path))
    return selected


def _download_drive_mirror(
    dest: Path, folder_id: str | None, match_id: str, include_videos: bool
) -> Path:
    """Fetch ONE match from the official Drive mirror via gdown (no HF auth).

    The mirror is link-public, so gdown lists it without cookies. We list the
    whole tree (metadata only, fast), keep just `match_id`'s files (optionally
    skipping the large videos), and download each into `dest/<relative_path>` so
    loader.load_match can read it.
    """
    if not folder_id:
        raise SystemExit("No dataset.gdrive_mirror set in config.yaml.")
    try:
        import gdown  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("gdown not installed. pip install gdown") from exc

    url = f"https://drive.google.com/drive/folders/{folder_id}"
    kind = "annotations + videos" if include_videos else "annotations only"
    print(f"[download] match {match_id} ({kind}) via Drive mirror -> {dest}")
    print(f"[download] listing {url} ...")
    entries = gdown.download_folder(url=url, skip_download=True, quiet=True, use_cookies=False)
    if not entries:
        raise SystemExit("gdown returned no files. Is the mirror still shared/public?")

    selected = _drive_match_files(entries, match_id, include_videos)
    if not selected:
        avail = sorted({e.path.split("/")[1] for e in entries
                        if len(e.path.split("/")) > 1 and not e.path.split("/")[1].startswith(".")})
        raise SystemExit(
            f"No Drive files for match {match_id} (include_videos={include_videos}).\n"
            f"Available match ids in mirror: {avail}"
        )

    print(f"[download] {len(selected)} file(s) selected for {match_id}.")
    for file_id, rel in selected:
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        gdown.download(id=file_id, output=str(out), quiet=False, use_cookies=False, resume=True)
    print(f"[download] done. SoccerTrack v2 root: {dest.resolve()}")
    return dest


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Download one SoccerTrack v2 match from Hugging Face.")
    p.add_argument(
        "--match",
        default=cfg.dev_match,
        help=f"Match ID to download (default: dev_match={cfg.dev_match}).",
    )
    p.add_argument(
        "--dest",
        default=None,
        help="Destination root (default: paths.data_root from config.yaml).",
    )
    p.add_argument(
        "--no-videos",
        action="store_true",
        help="(HF only) Skip the large panoramic mp4s; fetch gsr/bas/mot/raw only (fast).",
    )
    p.add_argument(
        "--source",
        default=None,
        choices=["hf", "drive"],
        help=f"Where to pull from (default: dataset.source={cfg.source}). "
             "'drive' uses the official Drive mirror via gdown (no HF gating).",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> None:
    args = _parse_args(argv)
    download_match(
        args.match,
        dest=args.dest,
        include_videos=not args.no_videos,
        source=args.source,
    )


if __name__ == "__main__":
    main()
