"""Download, inspect, and train the labeled basketball detection dataset.

Nothing in this module invents a dataset version, class map, checkpoint, or metric.
The newest Roboflow version is selected from the authenticated project's real version
objects unless an explicit version is supplied. Training consumes the downloaded
data.yaml, copies the real best checkpoint, and writes metrics returned by Ultralytics.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from src.config import REPO_ROOT

DEFAULT_WORKSPACE = "roboflow-jvuqo"
DEFAULT_PROJECT = "basketball-player-detection-2"
DEFAULT_DATASET_DIR = REPO_ROOT / "data" / "basketball_det"
DEFAULT_WEIGHTS_PATH = REPO_ROOT / "weights" / "basketball_best.pt"
DEFAULT_RUNS_DIR = REPO_ROOT / "runs" / "basketball"


@dataclass(frozen=True)
class DatasetInspection:
    data_yaml: Path
    names: dict[int, str]
    split_paths: dict[str, Path]
    suggested_player_ids: tuple[int, ...]
    suggested_ball_ids: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["data_yaml"] = str(self.data_yaml)
        payload["split_paths"] = {
            name: str(path) for name, path in self.split_paths.items()
        }
        return payload


def require_api_key(value: str | None = None) -> str:
    key = value or os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        raise RuntimeError(
            "ROBOFLOW_API_KEY is required for the authenticated Universe download"
        )
    return key


def select_version(versions: Iterable[Any], requested: int | None = None) -> Any:
    """Select an actual SDK Version object; never assume a numeric version."""
    candidates = list(versions)
    if not candidates:
        raise RuntimeError("Roboflow project returned no dataset versions")

    def number(version: Any) -> int:
        try:
            return int(version.version)
        except (AttributeError, TypeError, ValueError) as exc:
            raise RuntimeError("Roboflow returned a version without a numeric id") from exc

    if requested is not None:
        for version in candidates:
            if number(version) == requested:
                return version
        available = sorted(number(version) for version in candidates)
        raise RuntimeError(
            f"Roboflow version {requested} was not found; available versions: {available}"
        )
    return max(candidates, key=number)


def download_dataset(
    *,
    api_key: str | None = None,
    workspace: str = DEFAULT_WORKSPACE,
    project_slug: str = DEFAULT_PROJECT,
    version_number: int | None = None,
    location: str | Path = DEFAULT_DATASET_DIR,
    overwrite: bool = False,
    roboflow_factory: Any = None,
) -> DatasetInspection:
    """Download one authenticated Roboflow version in Ultralytics YOLO format."""
    key = require_api_key(api_key)
    if roboflow_factory is None:
        try:
            from roboflow import Roboflow
        except ImportError as exc:
            raise RuntimeError("Install the Phase 3 dependency: pip install roboflow") from exc
        roboflow_factory = Roboflow

    project = roboflow_factory(api_key=key).workspace(workspace).project(project_slug)
    version = select_version(project.versions(), requested=version_number)
    destination = Path(location).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    dataset = version.download("yolov8", location=str(destination), overwrite=overwrite)
    dataset_root = Path(dataset.location).expanduser().resolve()
    data_yaml = dataset_root / "data.yaml"
    inspection = inspect_dataset(data_yaml)
    print(f"Roboflow project: {workspace}/{project_slug}")
    print(f"Downloaded version: {version.version}")
    print(f"Dataset YAML: {inspection.data_yaml}")
    print_class_mapping(inspection)
    return inspection


def inspect_dataset(data_yaml: str | Path) -> DatasetInspection:
    """Validate actual YAML, classes, and image split directories before training."""
    path = Path(data_yaml).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Downloaded dataset YAML not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    names = normalize_names(payload.get("names"))
    if not names:
        raise ValueError(f"Dataset has no class names: {path}")

    split_paths = {}
    for split in ("train", "val", "test"):
        raw = payload.get(split)
        if split == "test" and not raw:
            continue
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(f"Dataset YAML is missing the {split} image split")
        resolved = resolve_split_path(path, payload.get("path"), raw)
        if not resolved.is_dir():
            raise FileNotFoundError(f"{split} image directory not found: {resolved}")
        split_paths[split] = resolved

    player_ids, ball_ids = suggest_runtime_ids(names)
    return DatasetInspection(
        data_yaml=path,
        names=names,
        split_paths=split_paths,
        suggested_player_ids=player_ids,
        suggested_ball_ids=ball_ids,
    )


def normalize_names(value: Any) -> dict[int, str]:
    if isinstance(value, list):
        return {index: str(name) for index, name in enumerate(value)}
    if isinstance(value, Mapping):
        try:
            return {int(index): str(name) for index, name in value.items()}
        except (TypeError, ValueError) as exc:
            raise ValueError("Dataset class ids must be integers") from exc
    raise ValueError("Dataset names must be a list or id-to-name mapping")


def resolve_split_path(data_yaml: Path, root_value: Any, split_value: str) -> Path:
    """Resolve both Roboflow-generated and standard Ultralytics relative layouts."""
    yaml_dir = data_yaml.parent
    roots = [yaml_dir]
    if isinstance(root_value, str) and root_value.strip():
        declared = Path(root_value).expanduser()
        roots.insert(0, declared if declared.is_absolute() else yaml_dir / declared)
    raw = Path(split_value).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    candidates = [(root / raw).resolve() for root in roots]
    # Roboflow exports sometimes use ../train/images from the YAML location.
    candidates.append((yaml_dir / split_value.lstrip("./")).resolve())
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def suggest_runtime_ids(names: Mapping[int, str]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Suggest, but never apply, IDs using explicit class-name semantics."""
    player_ids = []
    ball_ids = []
    for class_id, raw_name in names.items():
        name = raw_name.strip().lower().replace("_", "-").replace(" ", "-")
        if name == "player" or name.startswith("player-"):
            player_ids.append(int(class_id))
        if name == "ball" or name.startswith("ball-"):
            ball_ids.append(int(class_id))
    return tuple(sorted(player_ids)), tuple(sorted(ball_ids))


def print_class_mapping(inspection: DatasetInspection) -> None:
    print("Verified class map:")
    for class_id, name in sorted(inspection.names.items()):
        print(f"  {class_id}: {name}")
    print(
        "Suggested runtime env (review before use):\n"
        f"  BASKETBALL_PERSON_CLASS_IDS={','.join(map(str, inspection.suggested_player_ids))}\n"
        f"  BASKETBALL_BALL_CLASS_IDS={','.join(map(str, inspection.suggested_ball_ids))}"
    )


def train_model(
    data_yaml: str | Path,
    *,
    base_model: str = "yolo11n.pt",
    epochs: int = 50,
    image_size: int = 640,
    batch: int = 16,
    device: str = "cuda",
    output_weights: str | Path = DEFAULT_WEIGHTS_PATH,
    runs_dir: str | Path = DEFAULT_RUNS_DIR,
    run_name: str = "yolo11n_finetune",
    model_factory: Any = None,
) -> dict[str, Any]:
    """Train on validated data and persist only real returned artifacts/metrics."""
    if epochs <= 0 or image_size <= 0 or batch == 0:
        raise ValueError("epochs/image_size must be positive and batch must be non-zero")
    inspection = inspect_dataset(data_yaml)
    require_training_device(device)
    if model_factory is None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Install ultralytics before training") from exc
        model_factory = YOLO

    runs = Path(runs_dir).expanduser().resolve()
    model = model_factory(base_model)
    result = model.train(
        data=str(inspection.data_yaml),
        epochs=epochs,
        imgsz=image_size,
        batch=batch,
        device=device,
        project=str(runs),
        name=run_name,
        exist_ok=False,
        seed=42,
        deterministic=True,
        plots=True,
    )
    trainer = getattr(model, "trainer", None)
    if trainer is None or not getattr(trainer, "save_dir", None):
        raise RuntimeError("Ultralytics completed without exposing its trainer artifacts")
    save_dir = Path(trainer.save_dir).expanduser().resolve()
    best = Path(getattr(trainer, "best", save_dir / "weights" / "best.pt"))
    if not best.is_file():
        raise FileNotFoundError(f"Ultralytics did not produce best.pt at {best}")
    destination = Path(output_weights).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, destination)

    metrics = json_safe(
        getattr(result, "results_dict", result if isinstance(result, Mapping) else {})
    )
    summary = {
        "data_yaml": str(inspection.data_yaml),
        "base_model": base_model,
        "epochs": epochs,
        "image_size": image_size,
        "batch": batch,
        "device": device,
        "run_dir": str(save_dir),
        "best_checkpoint": str(destination),
        "class_names": inspection.names,
        "suggested_player_ids": inspection.suggested_player_ids,
        "suggested_ball_ids": inspection.suggested_ball_ids,
        "metrics": metrics,
    }
    summary_path = save_dir / "phase3_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Best checkpoint: {destination}")
    print(f"Actual training summary: {summary_path}")
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return summary


def require_training_device(device: str) -> None:
    if not device.lower().startswith("cuda"):
        return
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("CUDA training requested but PyTorch is not installed") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA training requested but no CUDA GPU is available")


def json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Basketball Path-B dataset and training")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="download + validate the real dataset")
    download.add_argument("--workspace", default=DEFAULT_WORKSPACE)
    download.add_argument("--project", default=DEFAULT_PROJECT)
    download.add_argument("--version", type=int)
    download.add_argument("--location", type=Path, default=DEFAULT_DATASET_DIR)
    download.add_argument("--overwrite", action="store_true")

    inspect = subparsers.add_parser("inspect", help="validate downloaded data and print classes")
    inspect.add_argument("--data", type=Path, default=DEFAULT_DATASET_DIR / "data.yaml")

    train = subparsers.add_parser("train", help="train YOLO on a validated download")
    train.add_argument("--data", type=Path, default=DEFAULT_DATASET_DIR / "data.yaml")
    train.add_argument("--base-model", default="yolo11n.pt")
    train.add_argument("--epochs", type=int, default=50)
    train.add_argument("--imgsz", type=int, default=640)
    train.add_argument("--batch", type=int, default=16)
    train.add_argument("--device", default="cuda")
    train.add_argument("--output", type=Path, default=DEFAULT_WEIGHTS_PATH)
    train.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    train.add_argument("--name", default="yolo11n_finetune")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "download":
            download_dataset(
                workspace=args.workspace,
                project_slug=args.project,
                version_number=args.version,
                location=args.location,
                overwrite=args.overwrite,
            )
        elif args.command == "inspect":
            print_class_mapping(inspect_dataset(args.data))
        elif args.command == "train":
            train_model(
                args.data,
                base_model=args.base_model,
                epochs=args.epochs,
                image_size=args.imgsz,
                batch=args.batch,
                device=args.device,
                output_weights=args.output,
                runs_dir=args.runs_dir,
                run_name=args.name,
            )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Phase 3 stopped: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
