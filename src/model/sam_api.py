"""Hosted SAM 3.1 backend via fal.ai (no GPU of ours required).

Verified against fal's published docs (2026-06-20): `fal-ai/sam-3-1/video` takes a
comma-separated text `prompt` (e.g. "soccer player, goalkeeper, referee, sports
ball" — exactly our cfg.sam_prompts), costs **$0.01 per 16 input frames**
(~$0.16 for a 10s/25fps clip), and needs only a FAL_KEY (sign up at fal.ai). This
is our primary real-SAM path when no team GPU/RunPod/Annapurna credit is in hand
— see docs/COMPUTE.md.

Known limitation (NOT live-tested against a real key — verify on first real run):
the documented Output schema only lists `video` (the masked/boxed result file)
and `boundingbox_frames_zip` (an image overlay zip) — there is no clearly
documented per-frame numeric box/track JSON. So `track()`:
  1. ALWAYS downloads the real annotated output video to outputs/ — this alone is
     a legitimate "real SAM 3.1 ran on our footage" demo artifact, zero GPU.
  2. Best-effort parses any structured per-object data fal returns (the `mask`
     metadata type in their schema suggests some models expose `box`/`score`/
     `index`); if none is found, yields empty-detection frames and tells you so
     via `last_output_video` / `structured_detections_available` rather than
     silently fabricating boxes.
If your run shows structured data is present, tighten `_frame_results_from_fal()`
to build real Detection objects — the plumbing (FrameResult/Detection, stabilize,
visualize, demo.py) is already wired for it.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence

from src.config import env
from src.model.sam_backend import Detection, FrameResult, TrackResult

DEFAULT_FAL_MODEL = "fal-ai/sam-3-1/video"


class SamApiBackend:
    """SAM 3.1 via the fal.ai hosted endpoint. No local GPU required."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.model = getattr(cfg, "sam_fal_model", None) or DEFAULT_FAL_MODEL
        self.fal_key = env("FAL_KEY") or env("SAM_API_KEY")
        self.last_output_video: Path | None = None
        self.structured_detections_available = False

    def _require_creds(self) -> None:
        if not self.fal_key:
            raise RuntimeError(
                "No FAL_KEY (or SAM_API_KEY) set. Sign up at https://fal.ai, create a key, "
                "and add FAL_KEY=... to .env. (~$0.01/16 frames — a 10s clip is ~$0.16.)"
            )
        # fal_client reads FAL_KEY from the environment itself.
        os.environ.setdefault("FAL_KEY", self.fal_key)

    def track(
        self,
        video_path: str,
        prompts: Sequence[str],
        *,
        max_objects: int | None = None,
    ) -> TrackResult:
        self._require_creds()
        try:
            import fal_client
        except ImportError as exc:  # pragma: no cover
            raise SystemExit("fal-client not installed. pip install fal-client") from exc

        video_url = self._resolve_video_url(video_path, fal_client)
        prompt = ", ".join(p.strip() for p in prompts if p.strip())

        print(f"[sam_api] submitting {self.model} | prompt={prompt!r} | video={video_url}")
        result = fal_client.subscribe(
            self.model,
            arguments={
                "video_url": video_url,
                "prompt": prompt,
                "apply_mask": True,
                "boundingbox_zip": True,
                "max_num_objects": max_objects or 16,
                "detection_threshold": 0.5,
            },
            with_logs=True,
        )

        self.last_output_video = self._download_output(result)
        return self._frame_results_from_fal(result)

    def _resolve_video_url(self, video_path: str, fal_client) -> str:
        if str(video_path).startswith(("http://", "https://")):
            return str(video_path)
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found for SAM API upload: {path}")
        print(f"[sam_api] uploading {path} to fal storage...")
        return fal_client.upload_file(str(path))

    def _download_output(self, result: dict) -> Path | None:
        video_info = (result or {}).get("video")
        url = video_info.get("url") if isinstance(video_info, dict) else None
        if not url:
            print("[sam_api] WARNING: no `video` field in fal result; nothing downloaded.")
            return None
        import requests  # lazy

        out_dir = self.cfg.outputs
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "sam_api_output.mp4"
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        print(f"[sam_api] downloaded real-SAM annotated video -> {out_path}")
        return out_path

    def _frame_results_from_fal(self, result: dict) -> TrackResult:
        """Best-effort: build Detections if fal returns structured per-frame data.

        Defensive — the documented schema doesn't guarantee this field exists.
        Checks a couple of plausible keys; falls back to empty detections (the
        masked video in `last_output_video` is still a valid demo artifact).
        """
        frames_data = (result or {}).get("frames") or (result or {}).get("masks")
        if not frames_data:
            print(
                "[sam_api] No structured per-frame boxes in the fal response — "
                "only the annotated video was available. See last_output_video. "
                "If you're testing live, inspect `result.keys()` and extend "
                "_frame_results_from_fal() if real data is present."
            )
            yield FrameResult(frame_index=0, detections=())
            return

        self.structured_detections_available = True
        for i, frame in enumerate(frames_data, start=1):
            dets = []
            for obj in frame.get("objects", frame if isinstance(frame, list) else []):
                box = obj.get("box")
                if not box:
                    continue
                dets.append(
                    Detection(
                        instance_id=int(obj.get("index", obj.get("object_id", 0))),
                        label=obj.get("label", "object"),
                        bbox=tuple(float(v) for v in box),
                        score=obj.get("score"),
                    )
                )
            yield FrameResult(frame_index=i, detections=tuple(dets))

    def close(self) -> None:
        return None
