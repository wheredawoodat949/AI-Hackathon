# Flag football tracking (Path A)

Copied from `sports/examples/basketball/main.py` (same generic COCO detector + ByteTrack
approach — no flag-football-specific model exists, none was trained). Verified on real footage:
USA vs Italy, The World Games, Birmingham AL (source: a local screen-capture clip, 8s @ 720p).

## Verified (2026-06-21, CPU)
```bash
python main.py --source_video_path <clip.mp4> --target_video_path out.mp4 \
  --device cpu --mode PLAYER_TRACKING
```
Ran in ~6s for a 120-frame (15fps, 8s) 720p clip. Produced a valid annotated video — ellipse
markers + ByteTrack IDs correctly tracking players. Output transcoded to H.264/yuv420p for the
frontend: `outputs/flag_football_tracking_h264.mp4`.

Ball detection (COCO class 32, `sports ball`) was **not specifically verified** as reliable for
the American-football-shaped ball — per the run plan, player tracking is the priority and does
not depend on ball detection quality. `TEAM_CLASSIFICATION`/`POSSESSION` modes inherited from the
basketball script were not exercised here (out of scope for this pass).
