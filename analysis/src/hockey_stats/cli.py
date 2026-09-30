"""one explicit offline invocation, attributed output, and concise checks."""

import argparse
import json
from pathlib import Path
import platform
import stat
import subprocess
import sys

from .captures import InputContractError
from .interpret import GameDocument, Interpretation, interpret_game


class Once(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str, option_string: str | None = None) -> None:
        if getattr(namespace, self.dest) is not None:
            parser.error(f"{option_string} must occur exactly once")
        setattr(namespace, self.dest, values)


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


def report(document: GameDocument, output: Path) -> None:
    if document["game"] is None:
        print(f"game interpretation unavailable; diagnostic saved to {output}")
    else:
        print(f"interpreted game {document['requested_game_id']} from local captures")
    for source in document["inputs"]:
        if source["status"] == "unavailable":
            print(f"{source['source']} unavailable: {source['reason']}")
    if document["events"] is not None:
        print(f"play-by-play: {len(document['events'])} source records")
    for check in document["checks"]:
        if "player_id" in check:
            continue
        name = check["name"]
        observed = check["observed"]
        expected = check["expected"]
        source = check.get("source", "shifts")
        if name == "shift_collection":
            if check["status"] == "match":
                other = sum(row["kind"] == "other" for row in document["shift_records"])
                print(f"shifts: {observed} records match advertised total; {other} non-shift records")
            elif check["status"] == "mismatch":
                print(f"shifts incomplete: {observed} records received; source advertises {expected}; duration reconciliation unavailable")
            else:
                print(f"shifts collection unavailable: {check['reason']}")
        elif (name == "timed_goals" and observed is not None and expected is not None
              and None not in expected.values()):
            result = next(row for row in document["reported_results"] if row["source"] == source)
            suffix = " after shootout" if result["last_period_type"] == "SO" else ""
            print(f"{source} scoring: {observed['away']}–{observed['home']} timed-play goals; {expected['away']}–{expected['home']} reported final{suffix}")
            if check["status"] != "match":
                print(f"{source} timed_goals {check['status']}: {check['reason']}")
        elif check["status"] != "match":
            team = f", team {check['team_id']}" if "team_id" in check else ""
            print(f"{source} {name}{team} {check['status']}: observed {observed}; expected {expected}; {check['reason']}")
    print("5v5 exposure: not reconstructed by this command")
    if document["game"] is not None:
        print(f"output: {output}")


def invoke(reconstruct: bool = False) -> int:
    parser = argparse.ArgumentParser(
        description=("reconstruct" if reconstruct else "interpret") + " one explicitly selected local game capture",
        allow_abbrev=False,
    )
    parser.add_argument("--capture", required=True, action=Once, metavar="DIRECTORY")
    parser.add_argument("--out", required=True, action=Once, metavar="FILE")
    args = parser.parse_args()
    try:
        directory = Path(args.capture).resolve(strict=True)
        if not stat.S_ISDIR(directory.stat().st_mode):
            raise InputContractError(f"{directory}: capture must be an existing directory; select a capture directory")
        output = Path(args.out).absolute()
        try:
            output.lstat()
        except FileNotFoundError:
            pass
        else:
            raise InputContractError(f"{output}: output already exists; choose a new output path")
        parent = output.parent.resolve(strict=True)
        if not stat.S_ISDIR(parent.stat().st_mode):
            raise InputContractError(f"{parent}: output parent must be an existing directory; create it first")
        output = parent / output.name
        if output.is_relative_to(directory):
            raise InputContractError(f"{output}: output must be outside the capture directory; choose another parent")
        document = interpret_game(directory)
        if reconstruct:
            from .reconstruct import reconstruct_game
            reconstruction = reconstruct_game(document)
            output_document = {"schema_version": 1, "implementation": implementation_identity(),
                               "interpreted": document, "reconstruction": reconstruction}
        else:
            document["interpretation"] = implementation_identity()
            output_document = document
        serialized = json.dumps(output_document, allow_nan=False, indent=2) + "\n"
        with output.open("x", encoding="utf-8") as destination:
            destination.write(serialized)
    except InputContractError as error:
        stage = "reconstruction" if reconstruct else "interpretation"
        print(f"{stage} failed: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        stage = "reconstruction" if reconstruct else "interpretation"
        print(f"{stage} failed: {error}; repair the affected path or choose an accessible input/output", file=sys.stderr)
        return 1
    if reconstruct:
        coverage = reconstruction["coverage"]
        time = coverage["time"]
        attempts = coverage["attempts"]
        locations = coverage["locations"]
        def value(item: int | None, suffix: str = "") -> str:
            return "unavailable" if item is None else f"{item}{suffix}"
        expected = time["expected_periods"]
        supported = time["supported_periods"]
        horizons = "unavailable" if expected is None else f"{len(supported)}/{len(expected)}"
        print(f"reconstructed game {document['requested_game_id']}")
        print(f"time: {horizons} period horizons; {value(time['five_on_five_seconds'], 's')} 5v5; {value(time['other_seconds'], 's')} other; {value(time['unresolved_seconds'], 's')} unresolved")
        print(f"timed attempts: {value(attempts['five_on_five'])} 5v5; {value(attempts['other'])} other; {value(attempts['unresolved'])} unresolved")
        if attempts["five_on_five"] is None:
            linked = "unavailable"
        elif attempts["five_on_five"] == 0:
            linked = "0; no 5v5 attempts"
        else:
            linked = f"{value(attempts['linked_five_on_five'])}/{attempts['five_on_five']}"
        print(f"5v5 attempts linked to exposure: {linked}")
        if attempts["unclassified_events"]:
            print(f"unclassified events: {attempts['unclassified_events']}")
        print(f"recorded locations: {value(locations['normalized'])} normalized; {value(locations['missing_coordinates'])} missing; {value(locations['unresolved_frame'])} frame unresolved")
        print("shooting origins: not computed")
        print(f"output: {output}")
        supported_rows = (reconstruction["intervals"] or []) + (reconstruction["events"] or [])
        return 0 if document["game"] is not None and any(
            row["classification"] in ("five_on_five", "other") for row in supported_rows
        ) else 1
    report(document, output)
    return 0 if document["game"] is not None else 1


def main() -> int:
    return invoke()


def reconstruct_main() -> int:
    return invoke(reconstruct=True)
