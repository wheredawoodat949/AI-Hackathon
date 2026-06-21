"""Phase 1 visible result: render a tracked clip (Role A — feat/tracking).

Runs the SAM-interface tracker over a clip and writes an annotated video to
outputs/. Two modes, same code path (only the backend + frames differ):

  --backend replay   (default) GSR ground truth on a synthetic canvas — NO GPU,
                     NO 4K video needed. Proves track -> visualize -> video works.
  --backend local|api  real SAM 3.1; overlays on the real panorama video (needs
                     the downloaded mp4 + a GPU). Wire this on the RunPod/GPU box.

    python -m src.tracking.demo                          # replay, synthetic canvas
    python -m src.tracking.demo --backend local --video data/videos/117093_...mp4

Output: outputs/track_<match>_<backend>.mp4 (or a PNG folder if no mp4 codec).
"""
from __future__ import annotations

import argparse

from src.config import load_config
from src.data.video import blank_frame, iter_frames, write_video
from src.tracking.tracker import stabilize
from src.tracking.visualize import draw_detections


def main() -> None:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Render an annotated tracked clip.")
    p.add_argument("--backend", default="yolo", choices=["yolo", "replay", "local", "api"])
    p.add_argument("--match", default=cfg.dev_match)
    p.add_argument("--half", type=int, default=1)
    p.add_argument("--video", default=None, help="Real panorama mp4 (yolo/local/api backends).")
    p.add_argument("--seconds", type=int, default=cfg.clip_seconds)
    p.add_argument("--canvas-scale", type=float, default=0.25,
                   help="Downscale factor for the synthetic canvas (replay mode).")
    args = p.parse_args()

    max_frames = args.seconds * cfg.fps

    # --- backend (all behind the SamBackend interface) ---
    if args.backend == "replay":
        from src.model.replay import GsrReplayBackend

        backend = GsrReplayBackend(cfg, match_id=args.match, half=args.half)
        results = stabilize(backend.track(args.video or "", cfg.sam_prompts,
                                          max_objects=cfg.max_tracked))
        frames = _replay_frames(results, max_frames, args.canvas_scale)
    else:
        from src.model import get_backend

        # Force the requested backend regardless of config.
        cfg.raw["sam"]["backend"] = args.backend
        backend = get_backend(cfg)
        if not args.video:
            raise SystemExit(f"--backend {args.backend} needs --video <clip.mp4>")
        results = stabilize(backend.track(args.video, cfg.sam_prompts,
                                          max_objects=cfg.max_tracked))
        frames = _overlay_frames(args.video, results, max_frames)

    out = cfg.outputs / f"track_{args.match}_{args.backend}.mp4"
    written = write_video(frames, out, fps=cfg.fps)
    backend.close()
    print(f"[demo] wrote {written}")


def _replay_frames(results, max_frames, scale):
    """Draw each FrameResult on a fresh synthetic canvas (no source video)."""
    # 4K panorama is 3840x1504; scale it down for a light clip.
    w, h = int(3840 * scale), int(1504 * scale)
    for n, fr in enumerate(results):
        if n >= max_frames:
            break
        yield draw_detections(blank_frame(w, h), fr.detections, scale=scale)


def _overlay_frames(video_path, results, max_frames):
    """Overlay detections on the real video frames (frame indices aligned)."""
    by_index = {}
    for n, fr in enumerate(results):
        if n >= max_frames:
            break
        by_index[fr.frame_index] = fr.detections
    for idx, frame in iter_frames(video_path, max_frames=max_frames):
        yield draw_detections(frame, by_index.get(idx, ()))


if __name__ == "__main__":
    main()
