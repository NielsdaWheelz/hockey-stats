"""three explicit offline chance-model commands and exclusive artifacts."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from .artifacts import implementation_identity, write_json
from .captures import InputContractError, strict_json
from .cli import Once


def read_json(path: Path) -> object:
    try:
        return strict_json(path.read_bytes())
    except ValueError as error:
        raise InputContractError(f"{path}: invalid finite json: {error}") from error


def identity(path: Path) -> dict:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def output_path(value: str, roots: list[str]) -> Path:
    output = Path(value).absolute()
    try:
        output.lstat()
    except FileNotFoundError:
        pass
    else:
        raise InputContractError(f"{output}: output already exists; choose a new output path")
    parent = output.parent.resolve(strict=True)
    if not parent.is_dir():
        raise InputContractError(f"{parent}: output parent must be an existing directory")
    output = parent / output.name
    if any(output.is_relative_to(Path(root)) for root in roots):
        raise InputContractError(f"{output}: output must be outside input directories")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="fit, assess or score an offline chance-model candidate", allow_abbrev=False
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("fit", "evaluate", "score"):
        child = commands.add_parser(command, allow_abbrev=False)
        for option in ("selection", "config" if command == "fit" else "model", "out"):
            child.add_argument(f"--{option}", required=True, action=Once)
    args = parser.parse_args()
    try:
        from .chance_data import prepare
        from .chance import (
            fit_model,
            validate_model,
            reference_probabilities,
            score_attempt,
            prediction_context,
        )
        from .chance_evaluation import evaluate
        import numpy
        import scipy

        selection = Path(args.selection).resolve(strict=True)
        auxiliary = Path(args.config if args.command == "fit" else args.model).resolve(strict=True)
        prepared = prepare(selection)
        output = output_path(
            args.out, prepared["input_roots"] + [str(selection.parent), str(auxiliary.parent)]
        )
        common = {
            "schema_version": 1,
            "purpose": prepared["purpose"],
            "inputs": prepared["inputs"],
            "selection": prepared["selection"],
            "game_dates": prepared["game_dates"],
            "coverage": prepared["coverage"],
            "scientific_assessment": "not_performed",
        }
        if args.command == "fit":
            config = read_json(auxiliary)
            implementation = implementation_identity()
            implementation.update(
                numpy_version=numpy.__version__,
                scipy_version=scipy.__version__,
                lockfile_sha256=identity(Path(__file__).resolve().parents[2] / "uv.lock")["sha256"],
            )
            metadata = dict(
                common,
                implementation=implementation,
                config_identity=identity(auxiliary),
                training_game_dates=prepared["game_dates"],
                training_game_ids=list(prepared["game_dates"]),
                training_dates=sorted(set(prepared["game_dates"].values())),
            )
            model, diagnostics = fit_model(
                [r for r in prepared["attempts"] if r["status"] == "eligible"], config, metadata
            )
            output.mkdir()
            write_json(output / "fit.json", dict(metadata, **diagnostics))
            if model is None:
                print(
                    f"fit failed: {diagnostics['termination']}; diagnostics saved to {output}",
                    file=sys.stderr,
                )
                return 1
            write_json(output / "model.json", model)
            print(f"fit: {prepared['purpose'].replace('_', ' ')}; converged; saved to {output}")
            counts = Counter(r["status"] for r in prepared["attempts"])
            print(
                f"training: {len(prepared['game_dates'])} games; {counts['eligible']} eligible attempts; {counts['unavailable']} unavailable"
            )
        else:
            model = read_json(auxiliary)
            validate_model(model)
            if model["purpose"] == "fixture_exercise" and prepared["purpose"] != "fixture_exercise":
                raise InputContractError("fixture exercise model cannot be relabeled research")
            common["model"] = identity(auxiliary)
            common["geometry"] = model["grid"]
            common["reference"] = model["reference"]
            if args.command == "evaluate":
                training = model["training_game_dates"]
                if set(training) & set(prepared["game_dates"]):
                    raise InputContractError("assessment game ids must be disjoint from training")
                if any(date <= max(training.values()) for date in prepared["game_dates"].values()):
                    raise InputContractError(
                        "assessment dates must be strictly after the latest training date"
                    )
                document = dict(common, **evaluate(model, prepared))
                write_json(output, document)
                print(
                    f"assessment: {prepared['purpose'].replace('_', ' ')}; {len(prepared['game_dates'])} held-out games"
                )
                for key, label, candidate in (
                    ("unblocked_conversion", "unblocked conversion", "candidate_r"),
                    (
                        "all_attempt_outcome_blind",
                        "all-attempt outcome-blind prediction",
                        "candidate_all",
                    ),
                ):
                    metric = document["metrics"][key][candidate]
                    print(
                        f"{label}: {metric['count']} attempts; log loss {metric['log_loss']}; brier score {metric['brier_score']}"
                    )
            else:
                reference = reference_probabilities(model)
                context = prediction_context(model)
                output.mkdir()
                counts, reasons, origins = Counter(), Counter(), Counter()
                per_game = {game_id: Counter() for game_id in prepared["game_dates"]}
                with (output / "attempts.jsonl").open("x", encoding="utf-8") as destination:
                    for attempt in prepared["attempts"]:
                        row = {k: v for k, v in attempt.items() if k != "source_event"}
                        row.update(
                            schema_version=1,
                            actor_evidence=None,
                            origin_basis=None,
                            origin_distribution=None,
                            reference_opportunity_value=None,
                        )
                        if attempt["status"] == "eligible":
                            row.update(score_attempt(model, attempt, reference, context))
                            row["status"] = "valued"
                        counts[row["status"]] += 1
                        reasons.update(row["reasons"])
                        per_game[row["game_id"]][row["status"]] += 1
                        if row["origin_basis"] is not None:
                            origins[row["origin_basis"]] += 1
                        destination.write(json.dumps(row, allow_nan=False) + "\n")
                document = dict(
                    common,
                    counts_by_status={
                        key: counts[key] for key in ("valued", "out_of_scope", "unavailable")
                    },
                    counts_by_reason=dict(reasons),
                    counts_by_origin_basis=dict(origins),
                    per_game={
                        k: {
                            status: v[status]
                            for status in ("valued", "out_of_scope", "unavailable")
                        }
                        for k, v in per_game.items()
                    },
                    attempts=dict(identity(output / "attempts.jsonl"), filename="attempts.jsonl"),
                )
                write_json(output / "score.json", document)
                print(f"score: {prepared['purpose'].replace('_', ' ')}; saved to {output}")
                print(
                    f"values: {counts['valued']} supported; {counts['unavailable']} unavailable; {counts['out_of_scope']} outside scope"
                )
                print(
                    f"origins: {origins['recorded_proxy']} recorded proxies; {origins['inferred_block']} inferred distributions"
                )
        print("scientific assessment: not performed")
        return 0
    except (InputContractError, OSError) as error:
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 1
