"""Phase 3 workflow tests use fake SDK/model objects and no data/API/GPU."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.training import basketball


def make_dataset(root: Path) -> Path:
    for split in ("train", "valid", "test"):
        (root / split / "images").mkdir(parents=True)
    data_yaml = root / "data.yaml"
    data_yaml.write_text(
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n"
        "names:\n"
        "  0: ball\n"
        "  1: player\n"
        "  2: player-dribble\n"
        "  3: referee\n",
        encoding="utf-8",
    )
    return data_yaml


def test_select_version_uses_real_numeric_ids():
    versions = [SimpleNamespace(version="2"), SimpleNamespace(version="11")]
    assert basketball.select_version(versions).version == "11"
    assert basketball.select_version(versions, requested=2).version == "2"
    with pytest.raises(RuntimeError, match="available versions"):
        basketball.select_version(versions, requested=5)


def test_inspect_validates_splits_and_reports_suggested_ids(tmp_path):
    inspection = basketball.inspect_dataset(make_dataset(tmp_path))
    assert inspection.names == {0: "ball", 1: "player", 2: "player-dribble", 3: "referee"}
    assert inspection.suggested_player_ids == (1, 2)
    assert inspection.suggested_ball_ids == (0,)
    assert inspection.split_paths["val"] == tmp_path / "valid" / "images"


def test_missing_split_fails_before_training(tmp_path):
    data_yaml = make_dataset(tmp_path)
    (tmp_path / "valid" / "images").rmdir()
    with pytest.raises(FileNotFoundError, match="val image"):
        basketball.inspect_dataset(data_yaml)


def test_download_selects_latest_authenticated_version(tmp_path):
    selected = []

    class FakeVersion:
        def __init__(self, number):
            self.version = number

        def download(self, model_format, location, overwrite):
            selected.append((self.version, model_format, overwrite))
            make_dataset(Path(location))
            return SimpleNamespace(location=location)

    class FakeProject:
        def versions(self):
            return [FakeVersion("1"), FakeVersion("3")]

    class FakeWorkspace:
        def project(self, slug):
            assert slug == basketball.DEFAULT_PROJECT
            return FakeProject()

    class FakeRoboflow:
        def __init__(self, api_key):
            assert api_key == "key"

        def workspace(self, name):
            assert name == basketball.DEFAULT_WORKSPACE
            return FakeWorkspace()

    inspection = basketball.download_dataset(
        api_key="key",
        location=tmp_path,
        roboflow_factory=FakeRoboflow,
    )
    assert inspection.data_yaml == tmp_path / "data.yaml"
    assert selected == [("3", "yolov8", False)]


def test_train_copies_real_best_and_serializes_returned_metrics(tmp_path):
    data_yaml = make_dataset(tmp_path / "dataset")
    run_dir = tmp_path / "run"
    best = run_dir / "weights" / "best.pt"
    best.parent.mkdir(parents=True)
    best.write_bytes(b"real-checkpoint")
    calls = []

    class FakeModel:
        def __init__(self, base_model):
            assert base_model == "yolo11n.pt"
            self.trainer = None

        def train(self, **kwargs):
            calls.append(kwargs)
            self.trainer = SimpleNamespace(save_dir=run_dir, best=best)
            return SimpleNamespace(results_dict={"metrics/mAP50(B)": 0.42})

    output = tmp_path / "weights" / "basketball_best.pt"
    summary = basketball.train_model(
        data_yaml,
        epochs=2,
        device="cpu",
        output_weights=output,
        runs_dir=tmp_path / "runs",
        model_factory=FakeModel,
    )
    assert output.read_bytes() == b"real-checkpoint"
    assert summary["metrics"]["metrics/mAP50(B)"] == 0.42
    assert calls[0]["data"] == str(data_yaml)
    persisted = json.loads((run_dir / "phase3_summary.json").read_text())
    assert persisted["best_checkpoint"] == str(output)
