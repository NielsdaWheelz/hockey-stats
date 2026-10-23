"""explicit offline player-analysis commands."""

import argparse
from pathlib import Path
import sqlite3
import sys

from .captures import InputContractError
from .cli import Once


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="hockey-stats-analysis", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", allow_abbrev=False)
    prepare.add_argument("--selection", required=True, action=Once)
    prepare.add_argument("--out", required=True, action=Once)
    publish = commands.add_parser("publish", allow_abbrev=False)
    publish.add_argument("--observed", required=True, action=Once, metavar="FILE")
    publish.add_argument("--results", required=True, action=Once, metavar="DIRECTORY")
    publish.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            from .analysis_data import prepare_analysis

            manifest = prepare_analysis(args.selection, args.out)
            print(str(manifest.directory / "manifest.json"))
        else:
            from .publication import build_publication

            verification = build_publication(Path(args.observed), Path(args.results), Path(args.out))
            print(f"publication {verification['publication_id']}: {verification['purpose']}")
            print(f"output: {verification['database']['path']}; scientific admission not performed")
    except (InputContractError, OSError, ValueError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
