"""explicit offline common-evidence preparation command."""

import argparse
import sys

from .analysis_data import prepare_analysis
from .captures import InputContractError

from .cli import Once


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hockey-stats-analysis", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", allow_abbrev=False)
    prepare.add_argument("--selection", required=True, action=Once)
    prepare.add_argument("--out", required=True, action=Once)
    args = parser.parse_args(argv)
    try:
        manifest = prepare_analysis(args.selection, args.out)
    except (InputContractError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(str(manifest.directory / "manifest.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
