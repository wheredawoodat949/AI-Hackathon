# Pika synthetic-media workflow

This integration submits synthetic basketball video jobs without putting generated
media on the tracking pipeline's critical path. Pika's current direct Developer API
documents Turbo text-to-video, Turbo image-to-video, and video-status endpoints:

- [Pika Developer API introduction](https://dev.pika.art/docs/api-reference/introduction)
- [Turbo text-to-video](https://dev.pika.art/docs/api-reference/generate-turbo-t2v)
- [Turbo image-to-video](https://dev.pika.art/docs/api-reference/generate-turbo-i2v)
- [Get video](https://dev.pika.art/docs/api-reference/get-video)

Direct access is partner-gated. The introduction instructs developers to contact Pika
for an API URL and key. Pika's public API page also advertises its models through
[fal.ai](https://pika.art/api); this module deliberately targets only the documented
direct endpoints because the project requirement calls for a Pika API key.

## Configure

Copy `.env.example` to `.env`, then set:

```dotenv
PIKA_API_KEY=<secret>
PIKA_API_BASE_URL=https://devapi.pika.art
PIKA_OUTPUT_DIR=./synthetic/pika
```

Set `sponsors.pika: true` in `config.yaml`. Keep the key out of source control.

## Generate

Text-to-video:

```bash
python -m src.synthetic.pika \
  --prompt "broadcast view of a basketball game under uneven arena lighting" \
  --negative-prompt "logos, text, watermark" \
  --seed 123 --extract-fps 1
```

Image-to-video:

```bash
python -m src.synthetic.pika \
  --image path/to/reviewed_source.jpg \
  --prompt "camera pans along the sideline while players move down court" \
  --extract-fps 1
```

Outputs and `manifest.jsonl` are saved under `synthetic/pika/`, which is gitignored.
Generated videos are not guaranteed by Pika to remain hosted beyond 30 days, so the
CLI downloads successful outputs immediately.

## Training-data boundary

Pika returns pixels, not ground-truth bounding boxes. Every manifest record therefore
starts with:

```json
{"synthetic": true, "reviewed": false, "annotated": false, "eligible_for_training": false}
```

Extracted frames may be reviewed and annotated in the same format as the real Roboflow
dataset. Do not point `data.yaml` at them, report augmented metrics, or mark them eligible
until that work actually happens.
