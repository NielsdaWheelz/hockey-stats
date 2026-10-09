"""one explicit offline invocation, attributed output, and concise checks."""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import stat
import sys
import time

from .artifacts import implementation_identity, write_json
from .captures import InputContractError
from .interpret import GameDocument, interpret_game


class Once(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str, option_string: str | None = None) -> None:
        if getattr(namespace, self.dest) is not None:
            parser.error(f"{option_string} must occur exactly once")
        setattr(namespace, self.dest, values)


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
            output_document = {"schema_version": 4, "implementation": implementation_identity(),
                               "interpreted": document, "reconstruction": reconstruction}
        else:
            document["interpretation"] = implementation_identity()
            output_document = document
        write_json(output, output_document)
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


def corpus_main() -> int:
    parser = argparse.ArgumentParser(
        description="audit one season inventory against explicit local game captures",
        allow_abbrev=False,
    )
    for option in ("reference", "games", "out"):
        parser.add_argument(f"--{option}", required=True, action=Once, metavar="DIRECTORY")
    args = parser.parse_args()
    from .corpus import audit_corpus, report_corpus
    from .references import interpret_references

    try:
        reference = Path(args.reference).resolve(strict=True)
        games = Path(args.games).resolve(strict=True)
        for root in (reference, games):
            if not stat.S_ISDIR(root.stat().st_mode):
                raise InputContractError(f"{root}: input must be an existing directory")
        output = Path(args.out).absolute()
        try:
            output.lstat()
        except FileNotFoundError:
            pass
        else:
            raise InputContractError(f"{output}: output already exists; choose a new directory")
        parent = output.parent.resolve(strict=True)
        if not stat.S_ISDIR(parent.stat().st_mode):
            raise InputContractError(f"{parent}: output parent must be an existing directory")
        output = parent / output.name
        if any(output.is_relative_to(root) for root in (reference, games)):
            raise InputContractError(f"{output}: output must be outside both input roots")
        references = interpret_references(reference)
        output.mkdir()
        document = audit_corpus(references, games, output, implementation_identity())
        write_json(output / "corpus.json", document)
    except (InputContractError, OSError) as error:
        print(f"corpus audit failed: {error}", file=sys.stderr)
        return 1
    report_corpus(document, output)
    return 1 if document["summary"] is None or document["summary"]["games_by_status"]["input_error"] else 0


def _inspect_fields(value, path, key, season, outcome, availability, representatives, input_ref):
    """count exact located fields without emitting another row stream."""
    if isinstance(value, list):
        for item in value:
            label = item["source"] if isinstance(item, dict) and isinstance(item.get("source"), str) else "*"
            _inspect_fields(item, path + "." + label, key, season, outcome, availability, representatives, input_ref)
        return
    if not isinstance(value, dict):
        return
    if isinstance(value.get("input_ref"), str):
        input_ref = value["input_ref"]
    if {"values", "problems", "evidence"} <= set(value):
        for field, observed in value["values"].items():
            name = path + "." + field
            problem = value["problems"].get(field)
            status = "available" if observed is not None else problem["status"]
            counts = availability.setdefault(name, {"denominator": 0, "available": 0, "unavailable": 0,
                "conflict": 0, "not_applicable": 0, "by_season": {}, "by_outcome": {}})
            counts["denominator"] += 1
            counts[status] += 1
            for category, label in (("by_season", season), ("by_outcome", outcome)):
                if label is None:
                    continue
                subtotal = counts[category].setdefault(label, {"denominator": 0, "available": 0,
                    "unavailable": 0, "conflict": 0, "not_applicable": 0})
                subtotal["denominator"] += 1
                subtotal[status] += 1
            examples = representatives.setdefault(name, {})
            if status not in examples:
                sample = observed
                if isinstance(observed, list):
                    sample = {"collection_length": len(observed)}
                elif isinstance(observed, dict):
                    sample = {"mapping_size": len(observed), "first_keys": list(observed)[:3]}
                refs = problem["evidence_refs"] if problem else range(len(value["evidence"]))
                if not problem:
                    field_refs = [ref for ref in refs if "input_index" in value["evidence"][ref]
                        and (value["evidence"][ref]["path"].endswith("/" + field)
                             or value["evidence"][ref]["path"].endswith("/" + field + "/default"))]
                    if field_refs:
                        refs = field_refs
                examples[status] = {"key": key, "value": sample,
                    "problem": {"status": problem["status"], "reason": problem["reason"]} if problem else None,
                    "evidence": [{**value["evidence"][ref], "input_ref": value["evidence"][ref].get("input_ref", input_ref)}
                                 for ref in refs[:3]],
                    "evidence_count": len(refs)}
                if "scope" in value:
                    examples[status]["window"] = {field: value[field] for field in ("scope", "start", "cutoff", "complete")}
            _inspect_fields(observed, name, key, season, outcome, availability, representatives, input_ref)
        return
    for field, child in value.items():
        parent = path.rsplit(".", 1)[-1]
        label, nested_key = field, key
        if parent in ("players", "teams"):
            label = "*"
            nested_key = {**key, "player_id" if parent == "players" else "team_id": field}
        _inspect_fields(child, path + "." + str(label), nested_key, season, outcome, availability, representatives, input_ref)


def _inspect_designs(prepared, layouts):
    """inspect requested bases; source gaps are distinct from invalid contracts."""
    from .chance_features import FeatureUnavailableError, STAGES, encode_stage
    from .shot_origins import cell_id, grid

    centers, _ = grid()
    eligible = [attempt for attempt in prepared["attempts"] if attempt["status"] == "eligible"]
    design_availability = {}
    for stage in STAGES:
        rows = [attempt for attempt in eligible if not attempt["blocked"]] if stage in ("r", "unblocked") else eligible
        counts = {"denominator": len(rows), "available": 0, "unavailable": 0,
                  "by_season": {}, "by_outcome": {}, "requirement_errors": {}}
        for attempt in rows:
            outcome = attempt["source_event"]["type_key"]
            origin_xy = None
            if stage in ("u", "r", "unblocked"):
                origin_xy = centers[0] if attempt["blocked"] else centers[cell_id((attempt["attacking_x"], attempt["attacking_y"]), centers)]
            try:
                encode_stage(attempt, layouts[stage]["design"], game_facts=prepared["feature_games"][attempt["game_id"]],
                    player_game_facts=prepared["feature_player_games"][attempt["game_id"]], origin_xy=origin_xy)
            except FeatureUnavailableError as error:
                message = str(error)
                status = "unavailable"
                requirement = message.split(": ", 1)[0].split(".", 1)[-1]
                errors = counts["requirement_errors"].setdefault(requirement, {"count": 0, "example": message})
                errors["count"] += 1
            else:
                status = "available"
            counts[status] += 1
            for category, label in (("by_season", attempt["season"]), ("by_outcome", outcome)):
                subtotal = counts[category].setdefault(label, {"denominator": 0, "available": 0, "unavailable": 0})
                subtotal["denominator"] += 1
                subtotal[status] += 1
        design_availability[stage] = counts
    return design_availability


def features_main() -> int:
    parser = argparse.ArgumentParser(description="inspect retained local feature facts and explicit stage designs",
                                     allow_abbrev=False)
    for option in ("selection", "config", "out"):
        parser.add_argument(f"--{option}", required=True, action=Once)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        from .chance import compile_designs, validate_config
        from .chance_cli import identity, output_path, read_json
        from .chance_data import prepare
        from .chance_features import STAGES
        import numpy
        import scipy

        selection = Path(args.selection).resolve(strict=True)
        config_path = Path(args.config).resolve(strict=True)
        config = validate_config(read_json(config_path))
        prepared = prepare(selection)
        output = output_path(args.out, prepared["input_roots"] + [str(selection.parent), str(config_path.parent)])
        years = [int(game["season"][:4]) for game in prepared["games"]]
        seasons = [f"{year:04d}{year + 1:04d}" for year in range(min(years), max(years) + 1)]
        layouts = compile_designs(prepared["attempts"], config, seasons=seasons)
        availability, representatives = {}, {}
        game_seasons = {game["game_id"]: game["season"] for game in prepared["games"]}
        game_inputs = {game_id: facts["game"]["evidence"][0]["input_ref"]
                       for game_id, facts in prepared["feature_games"].items()}
        for game_id, facts in prepared["feature_games"].items():
            _inspect_fields(facts, "game", {"game_id": game_id}, game_seasons[game_id], None, availability, representatives, game_inputs[game_id])
        for game_id, players in prepared["feature_player_games"].items():
            for player_id, facts in players.items():
                _inspect_fields(facts, "player_game", {"game_id": game_id, "player_id": player_id},
                                game_seasons[game_id], None, availability, representatives, game_inputs[game_id])
        for attempt in prepared["attempts"]:
            outcome = attempt["source_event"]["type_key"]
            _inspect_fields(attempt["feature_facts"], "attempt", {"game_id": attempt["game_id"],
                "source_index": attempt["source_index"]}, attempt["season"], outcome, availability, representatives, game_inputs[attempt["game_id"]])
        design_availability = _inspect_designs(prepared, layouts)
        implementation = implementation_identity()
        implementation.update(numpy_version=numpy.__version__, scipy_version=scipy.__version__,
            lockfile_sha256=identity(Path(__file__).resolve().parents[2] / "uv.lock")["sha256"])
        config_identity = identity(config_path)
        execution = {"implementation": implementation, "preparation_identity": prepared["preparation_identity"],
                     "inputs": prepared["inputs"], "config_identity": config_identity, "selection": prepared["selection"]}
        execution_sha256 = hashlib.sha256(json.dumps(execution, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        input_bytes = sum(Path(item["path"]).stat().st_size for item in prepared["inputs"]) + config_path.stat().st_size
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        resources = {"elapsed_seconds": time.perf_counter() - started,
                     "peak_rss_bytes": peak_rss if sys.platform == "darwin" else peak_rss * 1024,
                     "input_bytes": input_bytes, "output_bytes": 0}
        report = {"schema_version": 1, "artifact_kind": "feature_preparation", "purpose": prepared["purpose"],
            **execution, "execution_sha256": execution_sha256, "coverage": prepared["coverage"],
            "field_completion": {"disposition": "inspected", "fields": list(availability)},
            "field_availability": availability, "design_availability": design_availability,
            "stage_designs": {stage: layouts[stage]["design"] for stage in STAGES},
            "representative_values": representatives,
            "availability_meaning": "denominators count records carrying each exact field; nested fields are counted separately; a value does not imply completeness or scientific support",
            "candidate_geometry_probe": "unblocked assigned cell center; blocked first grid cell as an explicit hypothetical candidate; no recorded blocked release",
            "external_inference_prerequisites": ["absent coach/scratch feeds", "neutral-site and actual-time evidence",
                "travel and physical-recovery evidence", "passes/screens/entries/exits/tracking", "calibrated setter/possession/freeze targets",
                "physical origin/tip/scorer corrections", "compatible dated historical fitted-effect producers", "later component targets/exposure"],
            "scientific_assessment": "not_performed", "resource_measurement": "process high-water rss; elapsed through inspection; bytes include both output artifacts",
            **resources}
        completion = {"schema_version": 1, "artifact_kind": "feature_preparation_completion",
            "execution_sha256": execution_sha256, "report": {"path": str(output / "features.json"), "sha256": "0" * 64},
            "resources": dict(resources)}
        while True:
            output_bytes = sum(len((json.dumps(document, allow_nan=False, indent=2) + "\n").encode()) for document in (report, completion))
            if output_bytes == report["output_bytes"]:
                break
            report["output_bytes"] = completion["resources"]["output_bytes"] = output_bytes
        output.mkdir()
        write_json(output / "features.json", report)
        completion["report"] = identity(output / "features.json")
        write_json(output / "completion.json", completion)
    except (InputContractError, OSError) as error:
        print(f"feature inspection failed: {error}", file=sys.stderr)
        return 1
    print(f"feature preparation complete: {prepared['coverage']['games']['selected']} games; {len(prepared['attempts'])} retained baseline attempts")
    print("selected designs: " + "; ".join(f"{stage} {design_availability[stage]['available']}/{design_availability[stage]['denominator']} available" for stage in STAGES))
    print(f"output: {output / 'features.json'}; scientific assessment not performed")
    return 0
