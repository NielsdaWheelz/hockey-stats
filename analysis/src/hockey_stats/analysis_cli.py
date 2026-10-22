"""explicit offline product commands."""

import argparse
from pathlib import Path
import sqlite3
import sys

from .captures import InputContractError
from .cli import Once


def main() -> int:
    parser = argparse.ArgumentParser(description="build a checked player-analysis publication", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    publish = commands.add_parser("publish", allow_abbrev=False)
    publish.add_argument("--observed", required=True, action=Once, metavar="FILE")
    publish.add_argument("--results", required=True, action=Once, metavar="DIRECTORY")
    publish.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
    args = parser.parse_args()
    from .publication import build_publication

    try:
        verification = build_publication(Path(args.observed), Path(args.results), Path(args.out))
    except (InputContractError, OSError, ValueError, sqlite3.Error) as error:
        print(f"publication failed: {error}", file=sys.stderr)
        return 1
    print(f"publication {verification['publication_id']}: {verification['purpose']}")
    print(f"output: {verification['database']['path']}; scientific admission not performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
