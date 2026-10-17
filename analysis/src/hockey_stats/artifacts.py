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


def ordered_array_digest(arrays: dict) -> str:
    """bind array names, order, dtype, shape and c-order numerical bytes."""
    import numpy as np

    digest = hashlib.sha256()
    for name, value in arrays.items():
        value = np.ascontiguousarray(value)
        digest.update(json.dumps([name, value.dtype.str, list(value.shape)], separators=(",", ":")).encode())
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


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


def write_arrays(output: Path, name: str, arrays: dict) -> dict:
    import numpy as np
    from .chance_cli import identity

    require(bool(arrays) and all(value.dtype.kind in "biuf" and np.isfinite(value).all()
                                for value in arrays.values()), "artifact arrays must be finite numeric data")
    path = output / name
    with path.open("xb") as destination:
        np.savez(destination, **arrays)
    return dict(arrays=identity(path), array_shapes=[dict(name=key, shape=list(value.shape), dtype=value.dtype.str)
                for key, value in arrays.items()])


def load_arrays(document: dict) -> dict:
    import numpy as np

    shapes = document["array_shapes"]
    require(isinstance(shapes, list) and len({row["name"] for row in shapes}) == len(shapes),
            "array order contains duplicate names")
    with np.load(linked_path(document["arrays"]), allow_pickle=False) as arrays:
        require(arrays.files == [row["name"] for row in shapes], "artifact array order differs")
        values = {name: arrays[name] for name in arrays.files}
    require(all(list(values[row["name"]].shape) == row["shape"]
                and values[row["name"]].dtype.str == row["dtype"]
                and values[row["name"]].dtype.kind in "biuf"
                and np.isfinite(values[row["name"]]).all() for row in shapes),
            "artifact arrays differ from ordered shape/dtype contract")
    return values


def artifact(kind: str, purpose: str, consumed: dict, **fields) -> dict:
    """one explicit producer and input identity boundary for active 04c artifacts."""
    require(purpose in ("research", "fixture_exercise"), "invalid artifact purpose")
    producer = implementation()
    if purpose == "research":
        clean_implementation(producer)
    return dict(schema_version=3, kind=kind, purpose=purpose, implementation=producer,
                consumed=consumed, **fields)


def read_artifact(path: Path | str, kind: str) -> dict:
    from .chance_cli import read_json

    document = read_json(Path(path).resolve(strict=True))
    require(isinstance(document, dict) and type(document.get("schema_version")) is int
            and document["schema_version"] == 3 and document.get("kind") == kind
            and document.get("purpose") in ("research", "fixture_exercise"),
            "expected schema-3 " + kind)
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
    require(isinstance(document.get("consumed"), dict), "artifact consumed identities missing")
    for reference in document["consumed"].values():
        if reference is not None:
            linked_path(reference)
    return document
