# Basketball Path-B training

Phase 3 fine-tunes YOLO11n on the separate labeled Roboflow Universe dataset.
Basketball-51 remains inference footage only; it does not contain detection labels.

The workflow follows Roboflow's official
[Universe dataset download guidance](https://docs.roboflow.com/universe/download-a-universe-dataset)
and uses the authenticated Python SDK's actual project versions. It does not hardcode
an unverified version number.

## Prerequisites

- A Roboflow API key with access to
  [basketball-player-detection-2](https://universe.roboflow.com/roboflow-jvuqo/basketball-player-detection-2).
- Review the dataset license on its Universe landing page before download/use.
- A CUDA GPU for the default training command (Colab T4 is sufficient for this scale).
- `pip install -r requirements.txt`.

Keep `ROBOFLOW_API_KEY` in `.env`, a Colab secret, or the shell environment. Never
write it into a notebook cell that will be committed.

## 1. Download and inspect

```bash
export ROBOFLOW_API_KEY=<secret>
python -m src.training.basketball download
```

The command authenticates, queries real version objects, selects the highest numeric
version unless `--version N` is supplied, downloads into `data/basketball_det/`,
and validates the splits plus exact class map.

Rerun validation without downloading:

```bash
python -m src.training.basketball inspect --data data/basketball_det/data.yaml
```

The printed player/ball ID lists are suggestions based on exact class names. Review
them against the real downloaded map before using them.

## 2. Train

```bash
python -m src.training.basketball train \
  --data data/basketball_det/data.yaml \
  --base-model yolo11n.pt \
  --epochs 50 --imgsz 640 --batch 16 --device cuda
```

Artifacts stay gitignored:

- full Ultralytics run: `runs/basketball/yolo11n_finetune/`;
- best checkpoint copy: `weights/basketball_best.pt`;
- returned real metrics/class metadata: `phase3_summary.json` inside the run.

Do not report a metric until it appears in that summary or the Ultralytics run.

## 3. Run the fine-tuned model

Use the exact IDs printed during dataset inspection:

```bash
export BASKETBALL_DETECTION_MODEL=weights/basketball_best.pt
export BASKETBALL_PERSON_CLASS_IDS=<verified-comma-separated-ids>
export BASKETBALL_BALL_CLASS_IDS=<verified-comma-separated-ids>

cd sports/examples/basketball
python main.py \
  --source_video_path <real_clip.mp4> \
  --target_video_path <output.mp4> \
  --device cuda --mode POSSESSION
```
