"""saved chance evidence: paired game uncertainty and streamed spatial sensitivity.

this command computes no scientific verdict. intervals condition on fitted models;
independent origin evidence and the frozen protocol remain scientific judgments.
"""

import argparse
import hashlib
import math
import sys
import textwrap
from collections import Counter
from contextlib import ExitStack
from itertools import zip_longest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

from hockey_stats.artifacts import implementation_identity, write_json
from hockey_stats.captures import InputContractError, strict_json
from hockey_stats.chance import validate_model
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.cli import Once

POPULATIONS = {
    "unblocked_conversion": ("candidate_r", "benchmark_r"),
    "all_attempt_outcome_blind": ("candidate_all", "benchmark_all"),
}
STATUSES = ("valued", "out_of_scope", "unavailable")


def require(condition, message):
    if not condition:
        raise InputContractError(message)


def integer(value):
    require(type(value) is int and value >= 0, "expected nonnegative integer")
    return value


def number(value):
    require(
        type(value) in (int, float) and math.isfinite(value), "expected finite number"
    )
    return value


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
    path = absolute_path(reference["path"])
    digest(reference["sha256"])
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    require(actual == reference["sha256"], f"{path}: linked artifact digest mismatch")
    return path


def load_entries(entries, kind):
    require(isinstance(entries, list), f"{kind}: expected entry list")
    loaded = []
    labels = set()
    for entry in entries:
        require(
            isinstance(entry, dict) and set(entry) == {"label", "path"},
            f"{kind}: expected label/path",
        )
        label = entry["label"]
        require(
            isinstance(label, str) and bool(label) and label not in labels,
            f"{kind}: labels must be nonempty and unique",
        )
        labels.add(label)
        path = absolute_path(entry["path"])
        document = read_json(path)
        require(
            type(document["schema_version"]) is int
            and document["schema_version"] == 1
            and document["purpose"] == "research",
            f"{path}: research schema 1 required; fixture evidence forbidden",
        )
        require(
            document["scientific_assessment"] == "not_performed",
            "command artifacts cannot claim scientific acceptance",
        )
        clean_implementation(document["implementation"])
        selection = document["selection"]
        require(
            type(selection["schema_version"]) is int
            and selection["schema_version"] == 1
            and selection["purpose"] == "research",
            "invalid research selection",
        )
        game_ids = []
        for corpus in selection["corpora"]:
            require(
                Path(corpus["path"]).is_absolute()
                and isinstance(corpus["game_ids"], list)
                and bool(corpus["game_ids"]),
                "invalid selected corpus",
            )
            game_ids.extend(corpus["game_ids"])
        require(
            bool(game_ids)
            and len(set(game_ids)) == len(game_ids)
            and all(
                isinstance(gid, str) and len(gid) == 10 and gid.isdigit()
                for gid in game_ids
            ),
            "invalid selected game identities",
        )
        require(
            game_ids == list(document["game_dates"]),
            "selection and ordered game dates disagree",
        )
        require(
            isinstance(document["inputs"], list) and bool(document["inputs"]),
            "missing consumed input identities",
        )
        for reference in document["inputs"]:
            require(
                isinstance(reference["path"], str)
                and Path(reference["path"]).is_absolute(),
                "invalid consumed input path",
            )
            digest(reference["sha256"])
        model_path = linked_path(document["model"])
        model = validate_model(read_json(model_path))
        require(
            model["purpose"] == "research",
            "fixture model forbidden as scientific evidence",
        )
        clean_implementation(model["implementation"])
        require(
            document["geometry"] == model["grid"]
            and document["reference"] == model["reference"],
            "artifact/model geometry or reference mismatch",
        )
        if loaded:
            previous = loaded[0]["document"]
            for field in (
                "implementation",
                "selection",
                "inputs",
                "game_dates",
                "coverage",
                "geometry",
            ):
                require(
                    document[field] == previous[field],
                    f"{kind}: incompatible {field}; regenerate under one clean preparation revision",
                )
            if kind == "assessments":
                require(
                    document["prediction_definitions"]
                    == previous["prediction_definitions"],
                    "incompatible prediction definitions",
                )
                for left, right in zip(
                    document["per_game"], previous["per_game"], strict=True
                ):
                    require(
                        left["game_id"] == right["game_id"],
                        "incompatible per-game metric identities",
                    )
                    for population, names in POPULATIONS.items():
                        require(
                            all(
                                left["metrics"][population][names[0]][key]
                                == right["metrics"][population][names[0]][key]
                                for key in ("count", "goals")
                            ),
                            "incompatible per-game metric populations",
                        )
        loaded.append(
            {"label": label, "path": path, "document": document, "model": model}
        )
    return loaded


def validate_probability(metric):
    n, goals = integer(metric["count"]), integer(metric["goals"])
    require(goals <= n, "goals exceed population")
    for key in ("log_loss_sum", "brier_score_sum", "predicted_probability_sum"):
        require(number(metric[key]) >= 0, "negative probability metric sum")
    require(
        metric["brier_score_sum"] <= n and metric["predicted_probability_sum"] <= n,
        "probability sums exceed population",
    )
    for key, total in (
        ("log_loss", "log_loss_sum"),
        ("brier_score", "brier_score_sum"),
    ):
        require(
            metric[key] is None
            if n == 0
            else agrees(number(metric[key]), metric[total] / n),
            "metric mean disagrees with saved sum/count",
        )
    bins = metric["calibration"]
    require(
        isinstance(bins, list) and len(bins) == 20,
        "expected fixed twenty calibration bins",
    )
    for index, bucket in enumerate(bins):
        require(
            number(bucket["lower"]) == index / 20
            and number(bucket["upper"]) == (index + 1) / 20
            and bucket["upper_inclusive"] is (index == 19),
            "calibration bin definitions changed",
        )
        count, observed = integer(bucket["count"]), integer(bucket["goals"])
        predicted = number(bucket["predicted_probability_sum"])
        require(
            observed <= count
            and (
                predicted == 0
                if count == 0
                else bucket["lower"] - 1e-10
                <= predicted / count
                <= bucket["upper"] + 1e-10
            ),
            "invalid calibration sums",
        )
        for key, total in (("predicted_rate", predicted), ("observed_rate", observed)):
            require(
                bucket[key] is None
                if count == 0
                else agrees(number(bucket[key]), total / count),
                "calibration rate disagrees with sum/count",
            )
    require(
        sum(b["count"] for b in bins) == n
        and sum(b["goals"] for b in bins) == goals
        and agrees(
            math.fsum(b["predicted_probability_sum"] for b in bins),
            metric["predicted_probability_sum"],
        ),
        "calibration bins do not reconcile",
    )
    if n == 0:
        require(
            all(
                metric[key] == 0
                for key in (
                    "goals",
                    "log_loss_sum",
                    "brier_score_sum",
                    "predicted_probability_sum",
                )
            ),
            "empty population has nonzero sums",
        )


def validate_metrics(metrics):
    for population, names in POPULATIONS.items():
        for name in names:
            validate_probability(metrics[population][name])
        candidate, benchmark = (metrics[population][name] for name in names)
        require(
            (candidate["count"], candidate["goals"])
            == (benchmark["count"], benchmark["goals"]),
            "candidate/benchmark population mismatch",
        )
    unblocked = metrics["unblocked_conversion"]["candidate_r"]
    all_attempts = metrics["all_attempt_outcome_blind"]["candidate_all"]
    require(
        unblocked["count"] <= all_attempts["count"]
        and unblocked["goals"] == all_attempts["goals"],
        "unblocked/all-attempt populations disagree",
    )
    likelihood = metrics["observed_record_likelihood"]
    for name in ("all", "blocked", "unblocked"):
        selected = likelihood[name]
        n = integer(selected["count"])
        total = number(selected["negative_log_likelihood_sum"])
        require(
            total >= 0
            and (
                selected["mean_negative_log_likelihood"] is None
                if n == 0
                else agrees(number(selected["mean_negative_log_likelihood"]), total / n)
            ),
            "invalid likelihood diagnostic",
        )
        require(n != 0 or total == 0, "empty likelihood population has nonzero sum")
    require(
        likelihood["all"]["count"] == all_attempts["count"]
        and likelihood["unblocked"]["count"] == unblocked["count"]
        and likelihood["all"]["count"]
        == likelihood["blocked"]["count"] + likelihood["unblocked"]["count"]
        and agrees(
            likelihood["all"]["negative_log_likelihood_sum"],
            likelihood["blocked"]["negative_log_likelihood_sum"]
            + likelihood["unblocked"]["negative_log_likelihood_sum"],
        ),
        "likelihood populations/sums disagree",
    )


def ratio_interval(numerators, denominators, seed):
    """one paired whole-game resample per draw; never discard undefined draws."""
    numerators = np.asarray(numerators, dtype=np.float64)
    denominators = np.asarray(denominators, dtype=np.float64)
    n = len(numerators)
    total = float(denominators.sum())
    estimate = float(numerators.sum() / total) if total else None
    rng = np.random.Generator(np.random.PCG64(seed))
    sampled = np.empty(2000)
    undefined = 0
    for draw in range(2000):
        indices = rng.integers(0, n, size=n)
        denominator = float(denominators[indices].sum())
        if denominator == 0:
            undefined += 1
            sampled[draw] = np.nan
        else:
            sampled[draw] = float(numerators[indices].sum() / denominator)
    require(estimate is None or math.isfinite(estimate), "nonfinite pooled estimate")
    require(
        np.isfinite(sampled).sum() + undefined == 2000, "nonfinite bootstrap estimate"
    )
    return {
        "estimate": estimate,
        "count": int(total),
        "contributing_games": int(np.count_nonzero(denominators)),
        "interval": None
        if undefined
        else np.percentile(sampled, [2.5, 97.5], method="linear").tolist(),
        "undefined_draws": undefined,
        "missing_reason": "zero attempt denominator in at least one game-resampled draw"
        if undefined
        else None,
    }


def assessment_review(entry, seed):
    document = entry["document"]
    metrics, per_game = document["metrics"], document["per_game"]
    require(
        [row["game_id"] for row in per_game] == list(document["game_dates"]),
        "per-game metric identities/order disagree",
    )
    validate_metrics(metrics)
    for row in per_game:
        validate_metrics(row["metrics"])
    coverage = document["coverage"]
    require(
        [row["game_id"] for row in coverage["per_game"]]
        == list(document["game_dates"]),
        "per-game coverage identities/order disagree",
    )
    for row, covered in zip(per_game, coverage["per_game"]):
        count = row["metrics"]["all_attempt_outcome_blind"]["candidate_all"]["count"]
        supported = covered["attempts_by_status"]
        if supported is not None:
            for value in supported.values():
                integer(value)
        require(
            count == (supported["eligible"] if supported else 0),
            "per-game metric/coverage population mismatch",
        )
    total_count = metrics["all_attempt_outcome_blind"]["candidate_all"]["count"]
    require(
        total_count
        == (
            integer(coverage["attempts_by_status"]["eligible"])
            if coverage["attempts_by_status"]["eligible"] is not None
            else 0
        ),
        "overall metric/coverage population mismatch",
    )
    groups = document["groups"]
    require(
        set(groups)
        == {"season", "score", "role", "home_away", "shot_type", "actor_evidence"},
        "native subgroup categories missing or unexpected",
    )
    for category, group in groups.items():
        require(
            isinstance(group, list) and bool(group),
            "expected nonempty native subgroup summaries",
        )
        for row in group:
            validate_metrics(row["metrics"])
        if category != "actor_evidence":
            values = [row["value"] for row in group]
            require(
                all(
                    isinstance(value, str)
                    or (category == "shot_type" and value is None)
                    for value in values
                )
                and len(set(values)) == len(values),
                "invalid or duplicate subgroup labels",
            )
    fixed_domains = {
        "score": {"trailing", "tied", "leading"},
        "role": {"F", "D", "unknown"},
        "home_away": {"home", "away"},
    }
    for category, expected in fixed_domains.items():
        require(
            {row["value"] for row in groups[category]} == expected,
            f"{category}: native subgroup entries missing or unexpected",
        )
    # admission establishes this season/game-id relation; preserve zero-event seasons too.
    seasons = {gid[:4] + str(int(gid[:4]) + 1) for gid in document["game_dates"]}
    require(
        {row["value"] for row in groups["season"]} == seasons,
        "selected season subgroup missing or unexpected",
    )
    actor_pairs = (("u", "shooter"), ("r", "shooter"), ("r", "goalie"))
    actor_keys = [
        (row["stage"], row["actor"], row["value"]) for row in groups["actor_evidence"]
    ]
    expected_actors = {
        (stage, actor, basis)
        for stage, actor in actor_pairs
        for basis in ("seen", "unseen")
    }
    require(
        len(actor_keys) == 6 and set(actor_keys) == expected_actors,
        "native stage-specific actor groups missing or duplicated",
    )
    partitions = [
        groups[category] for category in ("season", "score", "role", "home_away")
    ]
    partitions.extend(
        [
            row
            for row in groups["actor_evidence"]
            if (row["stage"], row["actor"]) == (stage, actor)
        ]
        for stage, actor in actor_pairs
    )
    for partition in partitions:
        for population, names in POPULATIONS.items():
            for name in names:
                for key in ("count", "goals"):
                    require(
                        sum(row["metrics"][population][name][key] for row in partition)
                        == metrics[population][name][key],
                        "subgroup population does not conserve overall count/goals",
                    )
                for key in (
                    "log_loss_sum",
                    "brier_score_sum",
                    "predicted_probability_sum",
                ):
                    require(
                        agrees(
                            math.fsum(
                                row["metrics"][population][name][key]
                                for row in partition
                            ),
                            metrics[population][name][key],
                        ),
                        "subgroup probability/loss sums do not reconcile",
                    )
    shot_types = groups["shot_type"]
    require(
        any(row["value"] is None for row in shot_types), "missing shot-type null group"
    )
    for row in shot_types:
        require(
            row["metrics"]["all_attempt_outcome_blind"]["candidate_all"]["count"]
            == row["metrics"]["unblocked_conversion"]["candidate_r"]["count"],
            "shot-type groups must contain only unblocked attempts",
        )
    for name in POPULATIONS["unblocked_conversion"]:
        for key in ("count", "goals"):
            require(
                sum(
                    row["metrics"]["unblocked_conversion"][name][key]
                    for row in shot_types
                )
                == metrics["unblocked_conversion"][name][key],
                "shot-type groups do not conserve unblocked count/goals",
            )
        for key in ("log_loss_sum", "brier_score_sum", "predicted_probability_sum"):
            require(
                agrees(
                    math.fsum(
                        row["metrics"]["unblocked_conversion"][name][key]
                        for row in shot_types
                    ),
                    metrics["unblocked_conversion"][name][key],
                ),
                "shot-type conversion probability/loss sums do not reconcile",
            )
    for name in ("all", "blocked", "unblocked"):
        saved = metrics["observed_record_likelihood"][name]
        for key in ("count", "negative_log_likelihood_sum"):
            require(
                agrees(
                    math.fsum(
                        row["metrics"]["observed_record_likelihood"][name][key]
                        for row in per_game
                    ),
                    saved[key],
                ),
                "per-game likelihood sums do not reconcile",
            )
    comparisons, calibration = {}, {}
    for population, names in POPULATIONS.items():
        comparisons[population], calibration[population] = {}, {}
        for name in names:
            saved = metrics[population][name]
            games = [row["metrics"][population][name] for row in per_game]
            for key in (
                "count",
                "goals",
                "log_loss_sum",
                "brier_score_sum",
                "predicted_probability_sum",
            ):
                require(
                    agrees(math.fsum(row[key] for row in games), saved[key]),
                    "per-game sums do not reconcile to overall metrics",
                )
            for index, bucket in enumerate(saved["calibration"]):
                for key in ("count", "goals", "predicted_probability_sum"):
                    require(
                        agrees(
                            math.fsum(row["calibration"][index][key] for row in games),
                            bucket[key],
                        ),
                        "per-game calibration bins do not reconcile",
                    )
            overall = ratio_interval(
                [row["predicted_probability_sum"] - row["goals"] for row in games],
                [row["count"] for row in games],
                seed,
            )
            bins = []
            for index, bucket in enumerate(saved["calibration"]):
                selected = [row["calibration"][index] for row in games]
                bins.append(
                    dict(
                        bucket,
                        **ratio_interval(
                            [
                                row["predicted_probability_sum"] - row["goals"]
                                for row in selected
                            ],
                            [row["count"] for row in selected],
                            seed,
                        ),
                    )
                )
            calibration[population][name] = {"overall": overall, "bins": bins}
        candidate, benchmark = names
        for measure, key in (
            ("log_loss", "log_loss_sum"),
            ("brier_score", "brier_score_sum"),
        ):
            games = [row["metrics"][population] for row in per_game]
            comparisons[population][measure] = ratio_interval(
                [row[candidate][key] - row[benchmark][key] for row in games],
                [row[candidate]["count"] for row in games],
                seed,
            )
            count = comparisons[population][measure]["count"]
            comparisons[population][measure].update(
                candidate_mean=metrics[population][candidate][key] / count
                if count
                else None,
                benchmark_mean=metrics[population][benchmark][key] / count
                if count
                else None,
            )
    return {
        "label": entry["label"],
        "population_definitions": document["prediction_definitions"],
        "coverage": coverage,
        "comparisons": comparisons,
        "calibration": calibration,
        "subgroups": document["groups"],
        "subgroup_interval_reason": "artifacts contain aggregate summaries without per-game subgroup sums",
        "observed_record_likelihood": metrics["observed_record_likelihood"],
    }


def scored_distribution(row, cells):
    require(
        type(row["blocked"]) is bool
        and type(row["goal"]) is bool
        and not (row["blocked"] and row["goal"]),
        "invalid scored outcome",
    )
    blocked = row["blocked"]
    require(
        row["origin_basis"] == ("inferred_block" if blocked else "recorded_proxy"),
        "scored origin basis disagrees with outcome",
    )
    distribution = row["origin_distribution"]
    require(
        isinstance(distribution, list)
        and len(distribution) == (cells if blocked else 1),
        "invalid origin distribution dimensions",
    )
    weights, masses = np.zeros(cells), np.zeros(cells)
    ids = []
    for cell in distribution:
        h = integer(cell["cell_id"])
        require(h < cells, "origin cell outside model grid")
        ids.append(h)
        weight, mass = number(cell["weight"]), number(cell["opportunity_mass"])
        require(0 <= mass <= weight <= 1, "invalid origin weight/opportunity mass")
        weights[h], masses[h] = weight, mass
    require(
        (ids == list(range(cells))) if blocked else len(ids) == 1,
        "origin cells reordered or duplicated",
    )
    value = number(row["reference_opportunity_value"])
    require(
        0 <= value <= 1
        and agrees(float(weights.sum()), 1)
        and agrees(float(masses.sum()), value),
        "origin normalization/value conservation failed",
    )
    return weights, masses, value


def sensitivity_review(entries, reference_label):
    reference_index = next(
        index
        for index, entry in enumerate(entries)
        if entry["label"] == reference_label
    )
    cells = len(entries[0]["model"]["grid"]["centers"])
    game_ids = list(entries[0]["document"]["game_dates"])
    game_order = {gid: index for index, gid in enumerate(game_ids)}
    spatial = [
        {name: np.zeros(cells) for name in ("blocked", "unblocked")} for _ in entries
    ]
    counts, per_game = Counter(), {gid: Counter() for gid in game_ids}
    origins = Counter()
    changes = [
        {
            name: {
                "count": 0,
                "value_sum": 0.0,
                "absolute_value_sum": 0.0,
                "squared_value_sum": 0.0,
                "maximum_absolute_value": 0.0,
                "origin_tv_sum": 0.0,
                "origin_tv_maximum": 0.0,
            }
            for name in ("blocked", "unblocked")
        }
        for _ in entries
    ]
    previous = None
    with ExitStack() as stack:
        streams = [
            stack.enter_context(linked_path(entry["document"]["attempts"]).open("rb"))
            for entry in entries
        ]
        for lines in zip_longest(*streams):
            require(
                all(line is not None for line in lines),
                "scored streams have different lengths",
            )
            rows = [strict_json(line) for line in lines]
            keys = [
                (row["game_id"], row["source_index"], row["status"]) for row in rows
            ]
            require(
                all(key == keys[0] for key in keys),
                "scored stream keys/statuses differ or are reordered",
            )
            gid, source_index, status = keys[0]
            integer(source_index)
            require(
                gid in game_order and status in STATUSES, "invalid scored key/status"
            )
            order = game_order[gid], source_index
            require(
                previous is None or order > previous,
                "scored stream violates ordered selection/source indices",
            )
            previous = order
            for row in rows:
                require(
                    type(row["schema_version"]) is int and row["schema_version"] == 1,
                    "unsupported scored row schema",
                )
                require(
                    row["event_id"] is None or type(row["event_id"]) is int,
                    "invalid scored event identity",
                )
                require(
                    (row["blocked"], row["goal"])
                    == (rows[0]["blocked"], rows[0]["goal"]),
                    "scored outcomes differ across same events",
                )
                if status != "valued":
                    require(
                        all(
                            row[key] is None
                            for key in (
                                "origin_basis",
                                "origin_distribution",
                                "reference_opportunity_value",
                            )
                        ),
                        "unvalued attempt has invented origin/value",
                    )
            counts[status] += 1
            per_game[gid][status] += 1
            if status != "valued":
                continue
            distributions = [scored_distribution(row, cells) for row in rows]
            name = "blocked" if rows[0]["blocked"] else "unblocked"
            origins[rows[0]["origin_basis"]] += 1
            reference = distributions[reference_index]
            for index, (weights, mass, value) in enumerate(distributions):
                spatial[index][name] += mass
                if index == reference_index:
                    continue
                change = changes[index][name]
                delta = value - reference[2]
                tv = float(np.abs(weights - reference[0]).sum() / 2)
                change["count"] += 1
                change["value_sum"] += delta
                change["absolute_value_sum"] += abs(delta)
                change["squared_value_sum"] += delta * delta
                change["maximum_absolute_value"] = max(
                    change["maximum_absolute_value"], abs(delta)
                )
                change["origin_tv_sum"] += tv
                change["origin_tv_maximum"] = max(change["origin_tv_maximum"], tv)
    for entry in entries:
        document = entry["document"]
        for manifest in [
            document["counts_by_status"],
            *document["per_game"].values(),
            document["counts_by_origin_basis"],
        ]:
            for value in manifest.values():
                integer(value)
        require(
            {status: counts[status] for status in STATUSES}
            == document["counts_by_status"],
            "scored row counts disagree with manifest",
        )
        require(
            {
                gid: {status: row[status] for status in STATUSES}
                for gid, row in per_game.items()
            }
            == document["per_game"],
            "scored per-game counts disagree with manifest",
        )
        require(
            dict(origins)
            == {
                key: integer(value)
                for key, value in document["counts_by_origin_basis"].items()
                if value
            },
            "scored origin counts disagree with manifest",
        )
        covered = document["coverage"]["attempts_by_status"]
        for value in covered.values():
            if value is not None:
                integer(value)
        require(
            all(
                counts[status]
                == (covered["eligible" if status == "valued" else status] or 0)
                for status in STATUSES
            ),
            "scored manifest/coverage populations disagree",
        )
        require(
            [row["game_id"] for row in document["coverage"]["per_game"]] == game_ids,
            "scored coverage game order differs",
        )
        for row in document["coverage"]["per_game"]:
            covered = row["attempts_by_status"]
            require(
                all(
                    per_game[row["game_id"]][status]
                    == (
                        integer(covered["eligible" if status == "valued" else status])
                        if covered is not None
                        else 0
                    )
                    for status in STATUSES
                ),
                "scored per-game coverage populations disagree",
            )
    comparisons = []
    for index, entry in enumerate(entries):
        if index == reference_index:
            continue
        populations = {}
        for name, change in changes[index].items():
            n = change["count"]
            current, reference = spatial[index][name], spatial[reference_index][name]
            current_total, reference_total = (
                float(current.sum()),
                float(reference.sum()),
            )
            populations[name] = {
                "count": n,
                "reference_total_value": reference_total if n else None,
                "alternative_total_value": current_total if n else None,
                "value_change": {
                    "total": change["value_sum"] if n else None,
                    "mean": change["value_sum"] / n if n else None,
                    "mean_absolute": change["absolute_value_sum"] / n if n else None,
                    "root_mean_square": math.sqrt(change["squared_value_sum"] / n)
                    if n
                    else None,
                    "maximum_absolute": change["maximum_absolute_value"] if n else None,
                },
                "origin_total_variation": {
                    "mean": change["origin_tv_sum"] / n if n else None,
                    "maximum": change["origin_tv_maximum"] if n else None,
                },
                "absolute_spatial_mass_change": float(np.abs(current - reference).sum())
                if n
                else None,
                "spatial_shape_total_variation": float(
                    np.abs(current / current_total - reference / reference_total).sum()
                    / 2
                )
                if current_total and reference_total
                else None,
                "missing_reason": "no valued events in this population"
                if not n
                else "zero total opportunity mass makes spatial shape undefined"
                if not current_total or not reference_total
                else None,
            }
        model, reference_model = entry["model"], entries[reference_index]["model"]
        comparisons.append(
            {
                "label": entry["label"],
                "reference_label": reference_label,
                "populations": populations,
                "kernel_changed": model["kernel"] != reference_model["kernel"],
                "config_changed_fields": [
                    key
                    for key in model["config"]
                    if model["config"][key] != reference_model["config"][key]
                ],
                "reference_weights_equal": {
                    (pair["shooter_id"], pair["goalie_id"]): pair["weight"]
                    for pair in model["reference"]
                }
                == {
                    (pair["shooter_id"], pair["goalie_id"]): pair["weight"]
                    for pair in reference_model["reference"]
                },
                "training_selection_equal": model["selection"]
                == reference_model["selection"],
                "model_digest_equal": entry["document"]["model"]["sha256"]
                == entries[reference_index]["document"]["model"]["sha256"],
            }
        )
    population_counts = {
        "blocked": origins["inferred_block"],
        "unblocked": origins["recorded_proxy"],
    }
    return {
        "population_counts": population_counts,
        "reference_score": reference_label,
        "counts_by_status": {status: counts[status] for status in STATUSES},
        "grid": entries[0]["model"]["grid"],
        "spatial_opportunity_mass": [
            {
                "label": entry["label"],
                **{
                    name: values.tolist() if population_counts[name] else None
                    for name, values in spatial[index].items()
                },
                "missing_reasons": {
                    name: None
                    if population_counts[name]
                    else "no valued events in this population"
                    for name in population_counts
                },
            }
            for index, entry in enumerate(entries)
        ],
        "comparisons": comparisons,
        "units": "reference opportunity mass in expected goals; event differences are alternative minus reference",
        "uncertainty_reason": "point estimates; game-bootstrap probability intervals do not measure origin or fitted-parameter uncertainty",
    }


def save_figures(assessments, sensitivity, output):
    figures = []
    for index, assessment in enumerate(assessments):
        figure, axes = plt.subplots(
            3,
            2,
            figsize=(12, 11),
            sharex="col",
            gridspec_kw={"height_ratios": [3, 3, 1]},
        )
        extent = 0.05
        for column, (population, names) in enumerate(POPULATIONS.items()):
            for offset, (name, color) in enumerate(zip(names, ("#195e83", "#b65d2b"))):
                bins = assessment["calibration"][population][name]["bins"]
                for bucket in bins:
                    if bucket["estimate"] is None:
                        continue
                    x = (bucket["lower"] + bucket["upper"]) / 2 + (offset - 0.5) * 0.012
                    y = bucket["estimate"]
                    extent = max(extent, abs(y))
                    for axis in axes[:2, column]:
                        axis.plot(
                            x,
                            y,
                            "o",
                            color=color,
                            markerfacecolor=color if bucket["interval"] else "none",
                        )
                    if bucket["interval"]:
                        lower, upper = bucket["interval"]
                        extent = max(extent, abs(lower), abs(upper))
                        for axis in axes[:2, column]:
                            axis.vlines(x, lower, upper, color=color)
                axes[0, column].plot(
                    [],
                    [],
                    "o",
                    color=color,
                    label=f"{'candidate' if offset == 0 else 'benchmark'}; n={sum(b['count'] for b in bins)}",
                )
                axes[2, column].bar(
                    [0.025 + 0.05 * i + (offset - 0.5) * 0.02 for i in range(20)],
                    [b["count"] for b in bins],
                    width=0.019,
                    color=color,
                )
            axes[0, column].set_title(population.replace("_", " ") + "\nfull range")
            axes[0, column].legend(
                fontsize=8,
                loc="lower center",
                bbox_to_anchor=(0.5, 1.18),
                ncol=2,
                frameon=False,
            )
            axes[1, column].set_title("near-zero diagnostic view · display only")
            for axis in axes[:2, column]:
                axis.axhline(0, color="#777777", linewidth=0.7)
                axis.set_ylabel("predicted minus observed rate")
            axes[1, column].set_ylim(-0.02, 0.02)
            axes[2, column].set_yscale("symlog", linthresh=1)
            axes[2, column].set(
                xlim=(0, 1),
                xlabel="fixed predicted-probability bin",
                ylabel="attempt count (symlog)",
            )
        for axis in axes[0]:
            axis.set(
                ylim=(-extent * 1.1, extent * 1.1),
                ylabel="predicted minus observed rate",
            )
        figure.suptitle(assessment["label"].replace("_", " "))
        figure.text(
            0.02,
            0.015,
            "95% paired game-bootstrap intervals, conditional on fitted model. hollow points: at least one undefined draw; no interval.\n"
            "diagnostic zoom clips display at ±0.02; this is not an acceptance boundary. full-range panels retain every point and interval.\n"
            "all 20 fixed bins remain; count axes use symlog (linear 0–1, then log). support and acceptable margins belong to the frozen protocol.",
            fontsize=8,
        )
        figure.tight_layout(rect=(0, 0.075, 1, 0.94))
        filename = f"calibration-{index + 1}.png"
        figure.savefig(output / filename, dpi=160)
        plt.close(figure)
        figures.append(
            {
                "path": filename,
                "kind": "factual_calibration",
                "assessment": assessment["label"],
            }
        )
    if sensitivity is None:
        return figures
    reference_notes = ["each model uses its own empirical joint training reference."]
    for comparison in sensitivity["comparisons"]:
        same_training = comparison["training_selection_equal"]
        same_weights = comparison["reference_weights_equal"]
        if same_training and same_weights:
            note = "matched training selection and reference weights; model/refitting sensitivity"
        elif same_weights:
            note = "changed training selection; matched reference weights; refitting effects"
        elif same_training:
            note = "matched training selection; changed reference weights; model and reference effects are combined"
        else:
            note = "changed training selection and reference weights; refitting and reference effects are combined"
        kernel = "kernel changed" if comparison["kernel_changed"] else "kernel matched"
        reference_notes.append(
            f"{comparison['label']} versus {comparison['reference_label']}: {note}; {kernel}."
        )
    reference_caption = "\n".join(
        textwrap.fill(note, width=135) for note in reference_notes
    )
    caption_height = 0.15 * (4 + reference_caption.count("\n"))
    maps = sensitivity["spatial_opportunity_mass"]
    centers = np.asarray(sensitivity["grid"]["centers"])
    reference = next(
        row for row in maps if row["label"] == sensitivity["reference_score"]
    )
    for difference in (False, True):
        panels = []
        for name in ("blocked", "unblocked"):
            panels.append(
                [
                    None
                    if row[name] is None
                    else np.asarray(row[name]) - np.asarray(reference[name])
                    if difference
                    else np.asarray(row[name])
                    for row in maps
                ]
            )
        limit = (
            max(
                (
                    float(np.abs(values).max())
                    for row in panels
                    for values in row
                    if values is not None
                ),
                default=0,
            )
            or 1e-12
        )
        figure, axes = plt.subplots(
            2,
            len(maps),
            figsize=(5 * len(maps), 7 + caption_height),
            squeeze=False,
            sharex=True,
            sharey=True,
        )
        figure.subplots_adjust(
            left=0.08,
            bottom=(caption_height + 0.25) / (7 + caption_height),
            right=0.84,
            top=0.84,
            hspace=0.9,
            wspace=0.3,
        )
        rendered = None
        for i, name in enumerate(("blocked", "unblocked")):
            for j, row in enumerate(maps):
                values = panels[i][j]
                label = textwrap.fill(row["label"].replace("_", " "), width=24)
                if values is None:
                    axes[i, j].text(
                        0.5,
                        0.5,
                        "unavailable: no valued events",
                        ha="center",
                        transform=axes[i, j].transAxes,
                    )
                    axes[i, j].set(
                        title=f"{label}\n{name}",
                        xlim=(-100, 100),
                        ylim=(-42.5, 42.5),
                        aspect="equal",
                    )
                    continue
                surface = np.full((17, 40), np.nan)
                for (x, y), value in zip(centers, values):
                    surface[int((y + 40) / 5), int((x + 97.5) / 5)] = value
                rendered = axes[i, j].pcolormesh(
                    np.arange(-100, 105, 5),
                    np.arange(-42.5, 47.5, 5),
                    surface,
                    cmap="RdBu_r" if difference else "viridis",
                    vmin=-limit if difference else 0,
                    vmax=limit,
                )
                axes[i, j].set(
                    title=f"{label}\n{name} · n={sensitivity['population_counts'][name]}\n{'total change' if difference else 'total'}={float(values.sum()):+.5g} expected goals",
                    xlim=(-100, 100),
                    ylim=(-42.5, 42.5),
                    xlabel="attacking x (feet)",
                    ylabel="attacking y (feet)",
                    aspect="equal",
                )
        if rendered is not None:
            figure.colorbar(
                rendered,
                cax=figure.add_axes([0.89, 0.27, 0.018, 0.5]),
                label="opportunity mass change per cell (expected goals)"
                if difference
                else "opportunity mass per cell (expected goals)",
            )
        caption = (
            "absolute changes from the declared reference score; one symmetric color scale across all panels."
            if difference
            else "absolute opportunity mass; one color scale across blocked/unblocked populations and alternatives. totals are preserved."
        )
        figure.text(
            0.015,
            0.02,
            caption
            + "\npoint estimates of standardized values; no origin accuracy or causal attribution.\n"
            + reference_caption,
            fontsize=8,
        )
        filename = "spatial-mass-changes.png" if difference else "spatial-mass.png"
        figure.savefig(output / filename, dpi=160)
        plt.close(figure)
        figures.append(
            {
                "path": filename,
                "kind": "spatial_opportunity_mass_change"
                if difference
                else "spatial_opportunity_mass",
                "shared_color_limits": [-limit if difference else 0, limit]
                if rendered is not None
                else None,
                "missing_reason": None
                if rendered is not None
                else "no valued events in either population",
            }
        )
    figure, axes = plt.subplots(
        1, 2, figsize=(12, 3.4 + caption_height), sharex=True, sharey=True
    )
    measures = ("mean", "mean_absolute", "root_mean_square", "maximum_absolute")
    extent = 0.0
    for column, name in enumerate(("blocked", "unblocked")):
        for offset, comparison in enumerate(sensitivity["comparisons"]):
            row = comparison["populations"][name]
            values = [row["value_change"][measure] for measure in measures]
            if row["count"] == 0:
                axes[column].text(
                    0.5,
                    0.5,
                    "unavailable: no valued events",
                    ha="center",
                    transform=axes[column].transAxes,
                )
                continue
            extent = max(extent, max(abs(value) for value in values))
            axes[column].plot(
                values,
                np.arange(4) + offset * 0.08,
                "o",
                label=comparison["label"].replace("_", " "),
            )
        axes[column].axvline(0, color="#777777", linewidth=0.7)
        axes[column].set(
            title=f"{name} · n={sensitivity['population_counts'][name]}",
            yticks=np.arange(4),
            yticklabels=[name.replace("_", " ") for name in measures],
            xlabel="event opportunity-value change (expected goals)",
        )
    if any(sensitivity["population_counts"].values()):
        handles, labels = axes[
            0 if sensitivity["population_counts"]["blocked"] else 1
        ].get_legend_handles_labels()
        figure.legend(
            handles,
            labels,
            fontsize=8,
            loc="upper center",
            ncol=2,
            frameon=False,
        )
    extent = extent * 1.1 or 0.001
    axes[0].set_xlim(-extent, extent)
    axes[0].set_xticks(np.linspace(-extent, extent, 5))
    figure.text(
        0.01,
        0.01,
        "alternative minus reference; signed mean and absolute-change summaries on shared axes. no fitted-parameter/origin uncertainty.\n"
        + reference_caption,
        fontsize=8,
    )
    figure.tight_layout(
        rect=(0, (caption_height + 0.1) / (3.4 + caption_height), 1, 0.82)
    )
    figure.savefig(output / "event-value-changes.png", dpi=160)
    plt.close(figure)
    figures.append(
        {
            "path": "event-value-changes.png",
            "kind": "event_value_change",
            "shared_x_limits": [-extent, extent]
            if any(sensitivity["population_counts"].values())
            else None,
            "missing_reason": None
            if any(sensitivity["population_counts"].values())
            else "no valued events in either population",
        }
    )
    return figures


def main():
    parser = argparse.ArgumentParser(
        description="compare saved research chance artifacts without issuing a scientific verdict",
        allow_abbrev=False,
    )
    parser.add_argument("--evidence", required=True, action=Once)
    parser.add_argument("--out", required=True, action=Once)
    args = parser.parse_args()
    try:
        evidence_path = absolute_path(args.evidence)
        evidence = read_json(evidence_path)
        require(
            isinstance(evidence, dict)
            and set(evidence)
            <= {
                "schema_version",
                "purpose",
                "protocol",
                "assessments",
                "scores",
                "reference_score",
                "resampling",
            }
            and {"schema_version", "purpose", "protocol", "assessments", "resampling"}
            <= set(evidence),
            "invalid evidence fields",
        )
        require(
            type(evidence["schema_version"]) is int
            and evidence["schema_version"] == 1
            and evidence["purpose"] == "research",
            "research evidence schema 1 required",
        )
        protocol = absolute_path(evidence["protocol"])
        settings = evidence["resampling"]
        require(
            set(settings) == {"draws", "seed"}
            and type(settings["draws"]) is int
            and settings["draws"] == 2000
            and type(settings["seed"]) is int
            and settings["seed"] >= 0,
            "resampling requires 2000 draws and a nonnegative integer seed",
        )
        assessments = load_entries(evidence["assessments"], "assessments")
        scores = load_entries(evidence.get("scores", []), "scores")
        require(
            ("reference_score" in evidence) == ("scores" in evidence),
            "reference_score required exactly when scores are supplied",
        )
        if "scores" in evidence:
            require(
                len(scores) >= 2
                and evidence["reference_score"] in {entry["label"] for entry in scores},
                "sensitivity needs at least two scores and a supplied reference label",
            )
        roots = [
            str(evidence_path.parent),
            str(protocol.parent),
            *[str(entry["path"].parent) for entry in assessments + scores],
        ]
        output = output_path(args.out, roots)
        reviews = [assessment_review(entry, settings["seed"]) for entry in assessments]
        sensitivity = (
            sensitivity_review(scores, evidence["reference_score"]) if scores else None
        )
        implementation = implementation_identity()
        implementation.update(
            numpy_version=np.__version__,
            scipy_version=scipy.__version__,
            matplotlib_version=matplotlib.__version__,
            lockfile_sha256=identity(Path(__file__).resolve().parents[1] / "uv.lock")[
                "sha256"
            ],
        )
        artifacts = []
        for entry in assessments + scores:
            document = entry["document"]
            artifacts.append(
                {
                    "label": entry["label"],
                    "kind": "assessment" if entry in assessments else "score",
                    "artifact": identity(entry["path"]),
                    "implementation": document["implementation"],
                    "model": document["model"],
                    "model_implementation": entry["model"]["implementation"],
                    "model_training_selection": entry["model"]["selection"],
                    "model_consumed_inputs": entry["model"]["inputs"],
                    "model_config_identity": entry["model"]["config_identity"],
                    "reference": document["reference"],
                    "selection": document["selection"],
                    "consumed_inputs": document["inputs"],
                    "attempts": document.get("attempts"),
                }
            )
        output.mkdir()
        figures = save_figures(reviews, sensitivity, output)
        for figure in figures:
            figure["sha256"] = identity(output / figure["path"])["sha256"]
        comparison = {
            "schema_version": 1,
            "purpose": "research",
            "implementation": implementation,
            "evidence": identity(evidence_path),
            "protocol": identity(protocol),
            "consumed_artifacts": artifacts,
            "resampling": dict(
                settings,
                generator="numpy.random.Generator / PCG64",
                method="paired whole-game sampling with replacement; pooled attempt-weighted ratios; 95% percentile interval with linear interpolation",
                uncertainty="conditional on fitted models; game independence approximation; excludes parameter and latent-origin uncertainty",
            ),
            "assessments": reviews,
            "sensitivity": sensitivity,
            "figures": figures,
            "missing_reasons": {
                "assessments": None if reviews else "no assessment evidence supplied",
                "sensitivity": None
                if sensitivity
                else "no compatible scored alternatives supplied",
                "independent_blocked_origin_evidence": "not supplied by saved assessment/score artifacts; attributable independent evidence belongs in the written decision",
            },
        }
        write_json(output / "comparison.json", comparison)
        print(
            f"comparison saved to {output}; scientific judgment belongs in the written decision"
        )
        return 0
    except (
        InputContractError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as error:
        print(f"comparison failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
