"""explicit offline player-analysis commands."""

import argparse
from pathlib import Path
import sqlite3
import sys
from time import perf_counter

from .captures import InputContractError
from .cli import Once


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="hockey-stats-analysis", description="prepare evidence, reduce facts, fit and score annual execution, compose results, or publish checked analysis", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", allow_abbrev=False)
    prepare.add_argument("--selection", required=True, action=Once, metavar="FILE")
    prepare.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
    facts = commands.add_parser("facts", allow_abbrev=False)
    facts.add_argument("--prepared", required=True, action=Once, metavar="DIRECTORY")
    facts.add_argument("--observed", required=True, action=Once, metavar="FILE")
    facts.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
    fit = commands.add_parser("fit", allow_abbrev=False)
    fit.add_argument("--family", required=True, choices=("execution",), action=Once)
    fit.add_argument("--prepared", required=True, action=Once, metavar="DIRECTORY")
    fit.add_argument("--coaches", required=True, action=Once, metavar="FILE")
    fit.add_argument("--season", required=True, action=Once)
    fit.add_argument("--previous", action=Once, metavar="DIRECTORY")
    fit.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
    score = commands.add_parser("score", allow_abbrev=False)
    score.add_argument("--family", required=True, choices=("execution",), action=Once)
    score.add_argument("--prepared", required=True, action=Once, metavar="DIRECTORY")
    score.add_argument("--coaches", required=True, action=Once, metavar="FILE")
    score.add_argument("--state", required=True, action=Once, metavar="DIRECTORY")
    score.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
    summarize = commands.add_parser("summarize", allow_abbrev=False)
    summarize.add_argument("--family", required=True, choices=("execution",), action=Once)
    summarize.add_argument("--prepared", required=True, action=Once, metavar="DIRECTORY")
    summarize.add_argument("--facts", required=True, action=Once, metavar="DIRECTORY")
    summarize.add_argument("--scores", required=True, action=Once, metavar="FILE")
    summarize.add_argument("--out", required=True, action=Once, metavar="DIRECTORY")
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
        elif args.command == "facts":
            from .descriptive import build_factual_results

            manifest = build_factual_results(Path(args.prepared), Path(args.observed), Path(args.out))
            print(f"factual results: {manifest['purpose']}; {Path(args.out) / 'manifest.json'}")
        elif args.command == "fit":
            from .analysis_data import read_prepared
            from .artifacts import require
            from .captures import strict_json
            from .execution import (prepare_execution, fit_execution_year, read_execution_state, RECIPE)
            read_started = perf_counter()
            manifest = strict_json((Path(args.prepared) / "manifest.json").read_bytes())
            require(type(manifest) is dict and manifest.get("purpose") in ("real", "fixture"), "invalid prepared manifest purpose")
            purpose = manifest["purpose"]
            prepared = read_prepared(args.prepared, purpose)
            input_read_wall_seconds = perf_counter() - read_started
            design = prepare_execution(prepared, args.coaches, RECIPE, args.season)
            design.resources["input_read_wall_seconds"] = input_read_wall_seconds
            previous = read_execution_state(args.previous, purpose) if args.previous is not None else None
            state = fit_execution_year(design, previous, RECIPE, args.out)
            print(str(state.path))
            unavailable = [head for head in ("u", "q", "r", "g") if state.heads[head]["status"] != "complete"]
            unresolved = [head for head in ("u", "q", "r", "g")
                          if state.heads[head]["status"] == "complete"
                          and state.heads[head]["resolution"]["status"] not in ("passed", "not_applicable")]
            if unavailable or unresolved:
                print("execution family incomplete: " + "; ".join(
                    (["unavailable heads " + ",".join(unavailable)] if unavailable else [])
                    + (["unresolved numerical probes " + ",".join(unresolved)] if unresolved else [])), file=sys.stderr)
                return 1
        elif args.command == "score":
            from .execution_scores import write_execution_scores

            scores = write_execution_scores(Path(args.prepared), Path(args.coaches), Path(args.state), Path(args.out))
            print(f"execution scores {scores.manifest['season']}: {scores.manifest['purpose']}; {scores.path}")
        elif args.command == "summarize":
            from .execution_scores import compose_results

            manifest = compose_results(Path(args.prepared), Path(args.facts), Path(args.scores), Path(args.out))
            print(f"composed results: {manifest['purpose']}; {Path(args.out) / 'manifest.json'}")
        else:
            from .publication import build_publication

            verification = build_publication(Path(args.observed), Path(args.results), Path(args.out))
            print(f"publication {verification['publication_id']}: {verification['purpose']}")
            print(f"output: {verification['database']['path']}; scientific admission not performed")
    except (InputContractError, OSError, ValueError, sqlite3.Error) as error:
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
