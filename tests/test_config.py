"""Config + split invariants (no GPU/data needed)."""
from src.config import load_config


def test_config_loads():
    cfg = load_config()
    assert cfg.dev_match == "117093"
    assert cfg.source in ("drive", "hf")
    assert cfg.gdrive_mirror  # mirror folder id present


def test_split_is_80_10_10_over_real_ids():
    cfg = load_config()
    train, ev, test = cfg.split["train"], cfg.split["eval"], cfg.split["test"]
    assert len(train) == 8 and len(ev) == 1 and len(test) == 1
    all_ids = set(train) | set(ev) | set(test)
    assert len(all_ids) == 10, "splits must be disjoint and cover 10 matches"
    # dev match is something we train/dev on, never the held-out eval/test
    assert cfg.dev_match in train
    assert cfg.dev_match not in cfg.held_out
    # real mirror IDs, not the docs' assumed 117091-117100
    assert "117099" not in all_ids and "132877" in all_ids


def test_sponsor_flags_default_off():
    cfg = load_config()
    for s in ("sentry", "arize", "redis", "pika", "anthropic"):
        assert cfg.sponsor_enabled(s) is False
