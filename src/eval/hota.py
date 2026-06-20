"""GSR HOTA evaluation wrapper (Role B — feat/pitch-eval).

We do NOT reimplement metrics (CLAUDE.md §5). This shells out to the dataset
package's official scorer:

    python -m src.evaluation.gs_hota --pred <PRED_ROOT> --gt <GT_ROOT> --matches <ids...>

Install it on the GPU box:  pip install git+https://github.com/AtomScott/SoccerTrack-v2
(Note: the Drive mirror has gsr/ but no mot/, so use GSR HOTA, not MOT HOTA.)

Predictions must mirror the GT layout: pred/gsr/<id>/<id>_{1st,2nd}.json in the
same SoccerNet/COCO schema src.data.loader reads.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def run_gs_hota(pred_root: str | Path, gt_root: str | Path, matches: Sequence[str]) -> dict:
    """Run the official GS-HOTA scorer and return the parsed result dict.

    Raises if the scorer isn't importable (dataset package not installed) or the
    run fails — we never fabricate a number (CLAUDE.md §7).
    """
    out_path = Path(pred_root) / "_gs_hota.json"
    cmd = [
        sys.executable, "-m", "src.evaluation.gs_hota",
        "--pred", str(pred_root),
        "--gt", str(gt_root),
        "--matches", *map(str, matches),
        "--out", str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "gs_hota failed. Is the SoccerTrack-v2 package installed on this box?\n"
            "  pip install git+https://github.com/AtomScott/SoccerTrack-v2\n"
            f"--- stderr ---\n{proc.stderr.strip()}"
        )
    if out_path.exists():
        return json.loads(out_path.read_text())
    return {"raw_stdout": proc.stdout.strip()}
