"""Print one GSR frame's entities — the Phase 0 'it really loads' deliverable.

    python -m src.data.inspect                       # dev_match, half 1, first frame
    python -m src.data.inspect --match 117093 --half 1 --image-id 0

Reads real annotations via src.data.loader. Never fabricates — if the match
isn't downloaded, it tells you exactly which download command to run.
"""
from __future__ import annotations

import argparse

from src.config import load_config
from src.data.loader import load_match


def main() -> None:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Print one GSR frame's entities.")
    p.add_argument("--match", default=cfg.dev_match)
    p.add_argument("--half", type=int, default=1)
    p.add_argument("--image-id", type=int, default=None, help="Default: first frame of the half.")
    args = p.parse_args()

    m = load_match(cfg.data_root, match_id=args.match)
    frame = m.gsr_frame(args.half, args.image_id) if args.image_id is not None else None
    if frame is None and args.image_id is not None:
        raise SystemExit(f"No GSR frame at half={args.half} image_id={args.image_id}.")
    if frame is None:
        frames = m.gsr_frames(args.half)
        if not frames:
            raise SystemExit(f"No GSR frames for match {args.match} half {args.half}.")
        frame = frames[0]

    print(f"\nMatch {args.match} | half {frame.half} | image_id {frame.image_id} "
          f"| t={frame.t_ms} ms | {len(frame.entities)} entities\n")
    header = f"{'track_id':>8}  {'role':<11}  {'jersey':>6}  {'team':>5}  {'x (m)':>8}  {'y (m)':>8}"
    print(header)
    print("-" * len(header))
    for e in sorted(frame.entities, key=lambda p: p.track_id):
        jersey = "" if e.jersey_number is None else e.jersey_number
        team = e.team_side or ""
        print(f"{e.track_id:>8}  {e.role:<11}  {jersey!s:>6}  {team:>5}  {e.x:>8.2f}  {e.y:>8.2f}")
    print()


if __name__ == "__main__":
    main()
