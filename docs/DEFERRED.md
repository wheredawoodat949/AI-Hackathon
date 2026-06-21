# Deferred — pick up later

Things that are real, valid next steps but not the current priority. Don't lose
these; do them when there's slack in the schedule or Colab hits a wall.

## fal.ai hosted SAM 3.1 (no GPU needed) — deferred in favor of Colab

We verified `fal-ai/sam-3-1/video` is a real hosted SAM 3.1 endpoint that needs no
GPU of ours: ~$0.01 per 16 frames (~$0.16 for a 10s clip), implemented in
`src/model/sam_api.py`. **Currently deferred** because we're pursuing the free
Google Colab T4 path first (`sam.backend: local`, see `docs/COMPUTE.md` §2).

Pick this up if Colab hits a wall (quota exhausted, weights won't load, session
keeps disconnecting) — it's a clean fallback that needs no GPU at all:

1. Sign up at [fal.ai](https://fal.ai), create an API key.
2. Add a payment method and create a `FAL_KEY`. Budget only a small test run first.
3. Add `FAL_KEY=<key>` to `.env` (copy from `.env.example` if you haven't). `.env` is
   gitignored; never paste the key into a notebook output or commit it.
4. `pip install fal-client` (already in `requirements.txt`).
5. Download match 117093 and trim a short clip so the first paid call stays bounded:
   ```bash
   python -m src.data.download --match 117093
   mkdir -p data/clips
   ffmpeg -y -ss 0 -i data/videos/<the_117093_file>.mp4 -t 10 \
     -vf scale=1280:-2 -an data/clips/117093_10s_1280.mp4
   ```
6. Set `sam.backend: api` in `config.yaml`, or pass `--backend api` directly:
   ```bash
   python -m src.tracking.demo --backend api --video data/clips/117093_10s_1280.mp4
   ```
7. Capture and keep the complete console output. **This path has never been live-tested**
   (no key was available when it was
   built) — the first real run is the actual test. Watch the console: it'll
   tell you whether fal returned structured per-frame boxes or only the masked
   video. If only the video, that's still a legitimate demo artifact; tighten
   `_frame_results_from_fal()` in `src/model/sam_api.py` if real box data shows up.

## Why this was deferred
The team's only physical GPU (a K1900, ~2GB Kepler-era) can't run SAM 3.1 locally
(needs ~4GB). Colab's free T4 (16GB) clears that bar with real CUDA and zero
ongoing cost, so it's the first thing to try. fal.ai is the backup if Colab's
free tier runs out of time/quota before the deadline.
