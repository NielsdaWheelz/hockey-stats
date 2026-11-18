"""machine-local locations for retained inputs; artifact provenance stays unchanged."""

from functools import cache
import os
from pathlib import Path


@cache
def _roots():
    """read one process-local snapshot; installations without relocations need no file."""
    from .captures import InputContractError, strict_json

    config = Path.home() / "Documents/hockey-stats/locations.json"
    try:
        data = config.read_bytes()
    except FileNotFoundError:
        return ()
    try:
        value = strict_json(data)
        if (type(value) is not dict or set(value) != {"schema_version", "roots"}
                or type(value["schema_version"]) is not int or value["schema_version"] != 1
                or type(value["roots"]) is not list):
            raise ValueError("expected schema-1 location roots")
        roots = []
        for row in value["roots"]:
            if type(row) is not dict or set(row) != {"from", "to"}:
                raise ValueError("location root requires from and to")
            for name in ("from", "to"):
                text = row[name]
                if (type(text) is not str or not Path(text).is_absolute()
                        or os.path.normpath(text) != text or str(Path(text)) != text):
                    raise ValueError("location roots must be normalized absolute paths")
            roots.append((Path(row["from"]), Path(row["to"])))
        if len({source for source, _ in roots}) != len(roots):
            raise ValueError("duplicate source root")
        if any(target.is_relative_to(source) for _, target in roots for source, _ in roots):
            raise ValueError("mapped targets cannot be within source roots")
        return tuple(sorted(roots, key=lambda row: len(row[0].parts), reverse=True))
    except (ValueError, TypeError) as error:
        raise InputContractError(f"{config}: invalid input locations: {error}") from error


def input_path(value, *, strict=False):
    """locate an input once; mapped targets never fall back to an old file."""
    path = Path(os.path.abspath(value))
    for source, target in _roots():
        if path.is_relative_to(source):
            path = target / path.relative_to(source)
            break
    return path.resolve(strict=strict)


def same_input_reference(left, right):
    """compare one declared locator; every other reference field remains exact."""
    if (type(left) is not dict or type(right) is not dict or left.keys() != right.keys()
            or type(left.get("path")) is not str or type(right.get("path")) is not str):
        return False
    if left == right:
        return True
    if not Path(left["path"]).is_absolute() or not Path(right["path"]).is_absolute():
        return False
    return (all(left[key] == right[key] for key in left if key != "path")
            and input_path(left["path"]) == input_path(right["path"]))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="print the current location of a retained input")
    parser.add_argument("path")
    print(input_path(parser.parse_args().path, strict=True))
