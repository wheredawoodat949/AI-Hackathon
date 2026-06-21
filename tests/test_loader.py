"""Loader behavior that needs no downloaded data."""
import pytest

from src.data.loader import BAS_LABELS, load_match, normalize_bas_label


def test_bas_label_normalization():
    assert normalize_bas_label("PASS") == "Pass"
    assert normalize_bas_label("HIGH PASS") == "High Pass"
    assert normalize_bas_label("free kick") == "Free Kick"
    # unknown labels pass through trimmed rather than crashing
    assert normalize_bas_label("  weird ") == "weird"
    assert len(BAS_LABELS) == 12


def test_load_match_missing_root_is_helpful(tmp_path):
    with pytest.raises(FileNotFoundError) as exc:
        load_match(tmp_path, "117093")
    assert "gsr/" in str(exc.value)


def test_maybe_int_handles_blanks_and_strings():
    from src.data.loader import _maybe_int

    assert _maybe_int("12") == 12
    assert _maybe_int("") is None
    assert _maybe_int(None) is None
    assert _maybe_int("notanumber") is None
