"""implementation attribution and exclusive finite-json artifact writing."""

import json
from pathlib import Path
import platform
import subprocess

from .interpret import Interpretation


def implementation_identity() -> Interpretation:
    analysis = Path(__file__).resolve().parents[2]
    commit = None
    dirty = None
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=analysis, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
            cwd=analysis, check=True, capture_output=True, text=True,
        ).stdout)
    except (OSError, subprocess.CalledProcessError):
        commit = None
        dirty = None
    return {"git_commit": commit, "git_dirty": dirty,
            "python_version": platform.python_version()}


def write_json(output: Path, document: object) -> None:
    serialized = json.dumps(document, allow_nan=False, indent=2) + "\n"
    with output.open("x", encoding="utf-8") as destination:
        destination.write(serialized)
