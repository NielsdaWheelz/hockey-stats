"""implementation attribution and exclusive finite-json artifact writing."""

import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import subprocess
import time

from .captures import InputContractError, strict_json
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


def json_values(value):
    """convert numerical report values; write_json still rejects nonfinite data."""
    import numpy as np

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: json_values(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_values(item) for item in value]
    return value


def require(condition, message):
    if not condition:
        raise InputContractError(message)


def agrees(left, right):
    return math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10)


def digest(value):
    require(
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value),
        "invalid sha256",
    )


def clean_implementation(value):
    commit = value["git_commit"]
    require(
        isinstance(commit, str)
        and len(commit) == 40
        and all(c in "0123456789abcdef" for c in commit)
        and value["git_dirty"] is False,
        "scientific evidence requires an identified clean implementation",
    )
    for key in ("python_version", "numpy_version", "scipy_version"):
        require(
            isinstance(value[key], str) and bool(value[key]),
            "missing implementation dependency version",
        )
    digest(value["lockfile_sha256"])


def absolute_path(value):
    require(
        isinstance(value, str) and Path(value).is_absolute(),
        "artifact paths must be absolute",
    )
    return Path(value).resolve(strict=True)


def linked_path(reference):
    require(isinstance(reference, dict) and set(reference) == {"path", "sha256"},
            "artifact reference requires exactly path and sha256")
    path = absolute_path(reference["path"])
    digest(reference["sha256"])
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    require(actual == reference["sha256"], f"{path}: linked artifact digest mismatch")
    return path


def implementation():
    """bind numerical artifacts to analysis code, runtime and the locked environment."""
    import numpy as np
    import scipy

    value = implementation_identity()
    with (Path(__file__).resolve().parents[2] / "uv.lock").open("rb") as source:
        lockfile_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    value.update(numpy_version=np.__version__, scipy_version=scipy.__version__,
                 lockfile_sha256=lockfile_sha256)
    return value


def resources(started):
    return dict(wall_seconds=time.monotonic() - started,
                peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def rows(path):
    with path.open(encoding="utf-8") as source:
        for index, line in enumerate(source):
            try:
                value = strict_json(line.encode())
            except ValueError as error:
                raise InputContractError(f"{path}:{index + 1}: invalid prediction json") from error
            require(isinstance(value, dict), "prediction row must be an object")
            yield value


def artifact_roots(value):
    """locate bound input parents before choosing an exclusive output directory."""
    if isinstance(value, dict):
        if set(value) == {"path", "sha256"}:
            return [str(linked_path(value).parent)]
        return [root for item in value.values() for root in artifact_roots(item)]
    if isinstance(value, list):
        return [root for item in value for root in artifact_roots(item)]
    return []
