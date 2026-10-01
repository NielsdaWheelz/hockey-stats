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
from datetime import date
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
from hockey_stats.chance_evaluation import (
    GROUP_DOMAINS,
    PROBABILITY_POPULATIONS,
    PROBABILITY_SUMS,
)
from hockey_stats.cli import Once

POPULATIONS = {name: predictors for name, (_, predictors) in PROBABILITY_POPULATIONS.items()}
OUTCOMES = {name: outcome for name, (outcome, _) in PROBABILITY_POPULATIONS.items()}
SUMS = PROBABILITY_SUMS
STATUSES = ("valued", "out_of_scope", "unavailable")
TIP_GROUPS = ("tip_distance", "tip_below_goal_line")


def require(condition, message):
    if not condition:
        raise InputContractError(message)


def integer(value):
    require(type(value) is int and value >= 0, "expected nonnegative integer")
    return value


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), "expected finite number")
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
            and document["schema_version"] == (3 if kind == "assessments" else 2)
            and document["purpose"] == "research",
            f"{path}: research {'evaluation schema 3' if kind == 'assessments' else 'score schema 2'} required; fixture evidence forbidden",
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
            and all(isinstance(gid, str) and len(gid) == 10 and gid.isdigit() for gid in game_ids),
            "invalid selected game identities",
        )
        require(
            game_ids == list(document["game_dates"]),
            "selection and ordered game dates disagree",
        )
        dates = document["game_dates"]
        require(
            all(
                isinstance(value, str) and date.fromisoformat(value).isoformat() == value
                for value in dates.values()
            ),
            "invalid game dates",
        )
        require(
            game_ids == sorted(game_ids, key=lambda gid: (dates[gid], gid)),
            "selected games are not chronological",
        )
        require(
            isinstance(document["inputs"], list) and bool(document["inputs"]),
            "missing consumed input identities",
        )
        for reference in document["inputs"]:
            require(
                isinstance(reference["path"], str) and Path(reference["path"]).is_absolute(),
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
            and document["reference"] == model["reference"]
            and document["reference_season"] == model["reference_season"],
            "artifact/model geometry or reference mismatch",
        )
        if kind == "assessments":
            require(
                not set(model["training_game_dates"]) & set(game_ids)
                and min(dates.values()) > max(model["training_game_dates"].values()),
                "assessment must be disjoint and strictly later than training",
            )
        else:
            require(
                document["quantity"] == "reference_opportunity_value"
                and document["units"] == "expected_goals",
                "unsupported scored quantity or units",
            )
        if loaded:
            previous = loaded[0]
            for field in (
                "implementation",
                "selection",
                "inputs",
                "game_dates",
                "coverage",
                "geometry",
                "reference",
                "reference_season",
            ):
                require(
                    document[field] == previous["document"][field],
                    f"{kind}: incompatible {field}; regenerate under one clean preparation revision",
                )
            for field in ("selection", "inputs", "training_game_dates"):
                require(
                    model[field] == previous["model"][field],
                    f"{kind}: incompatible model training {field}",
                )
            if kind == "assessments":
                require(
                    document["prediction_definitions"]
                    == previous["document"]["prediction_definitions"],
                    "incompatible prediction definitions",
                )
                for left, right in zip(
                    document["per_game"], previous["document"]["per_game"], strict=True
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
                                for key in (
                                    "outcome",
                                    "count",
                                    "observed_positive_count",
                                )
                            ),
                            "incompatible per-game metric populations",
                        )
                    paired_groups(left["groups"], right["groups"])
                paired_groups(document["groups"], previous["document"]["groups"])
            else:
                for field in ("quantity", "units", "conditioning", "reference_definition"):
                    require(
                        document[field] == previous["document"][field],
                        f"scores: incompatible {field}",
                    )
        loaded.append({"label": label, "path": path, "document": document, "model": model})
    return loaded


def paired_groups(left, right):
    require(set(left) == set(right), "incompatible subgroup categories")
    for category, groups in left.items():
        for current, previous in zip(groups, right[category], strict=True):
            require(
                {key: value for key, value in current.items() if key != "metrics"}
                == {key: value for key, value in previous.items() if key != "metrics"},
                "incompatible subgroup identities",
            )
            require(
                set(current["metrics"]) == set(previous["metrics"]),
                "incompatible subgroup probability populations",
            )
            for population, metrics in current["metrics"].items():
                if population == "observed_record_likelihood":
                    continue
                candidate = POPULATIONS[population][0]
                require(
                    all(
                        metrics[candidate][key] == previous["metrics"][population][candidate][key]
                        for key in ("outcome", "count", "observed_positive_count")
                    ),
                    "incompatible per-game/global subgroup populations",
                )


def validate_probability(metric, outcome, compact=False):
    n = integer(metric["count"])
    positives = integer(metric["observed_positive_count"])
    require(
        metric["outcome"] == outcome and positives <= n,
        "probability outcome/population mismatch",
    )
    for key in SUMS[2:]:
        require(number(metric[key]) >= 0, "negative probability metric sum")
    require(
        metric["brier_score_sum"] <= n and metric["predicted_probability_sum"] <= n,
        "probability sums exceed population",
    )
    if n == 0:
        require(all(metric[key] == 0 for key in SUMS), "empty population has nonzero sums")
    if compact:
        require(
            set(metric) == {"outcome", *SUMS},
            "unexpected per-game subgroup metric fields",
        )
        return
    for key, total in (
        ("log_loss", "log_loss_sum"),
        ("brier_score", "brier_score_sum"),
    ):
        require(
            metric[key] is None if n == 0 else agrees(number(metric[key]), metric[total] / n),
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
        count = integer(bucket["count"])
        observed = integer(bucket["observed_positive_count"])
        predicted = number(bucket["predicted_probability_sum"])
        require(
            observed <= count
            and (
                predicted == 0
                if count == 0
                else bucket["lower"] - 1e-10 <= predicted / count <= bucket["upper"] + 1e-10
            ),
            "invalid calibration sums",
        )
        for key, total in (("predicted_rate", predicted), ("observed_rate", observed)):
            require(
                bucket[key] is None if count == 0 else agrees(number(bucket[key]), total / count),
                "calibration rate disagrees with sum/count",
            )
    require(
        sum(b["count"] for b in bins) == n
        and sum(b["observed_positive_count"] for b in bins) == positives
        and agrees(
            math.fsum(b["predicted_probability_sum"] for b in bins),
            metric["predicted_probability_sum"],
        ),
        "calibration bins do not reconcile",
    )


def validate_metrics(metrics, tip=False, compact=False):
    populations = (
        {"unblocked_conversion": POPULATIONS["unblocked_conversion"]} if tip else POPULATIONS
    )
    expected = set(populations)
    if not tip and not compact:
        expected.add("observed_record_likelihood")
    require(set(metrics) == expected, "unexpected probability population fields")
    for population, names in populations.items():
        require(set(metrics[population]) == set(names), "unexpected predictor fields")
        for name in names:
            validate_probability(metrics[population][name], OUTCOMES[population], compact)
        require(
            all(
                (
                    metrics[population][name]["count"],
                    metrics[population][name]["observed_positive_count"],
                )
                == (
                    metrics[population][names[0]]["count"],
                    metrics[population][names[0]]["observed_positive_count"],
                )
                for name in names
            ),
            "candidate/benchmark population mismatch",
        )
    if tip:
        return
    unblocked = metrics["unblocked_conversion"]["candidate_r"]
    all_attempts = metrics["all_attempt_recorded_context"]["candidate_all"]
    marginal = metrics["marginal_unblocked"]["candidate_unblocked"]
    require(
        unblocked["count"] <= all_attempts["count"]
        and unblocked["observed_positive_count"] == all_attempts["observed_positive_count"]
        and marginal["count"] == all_attempts["count"]
        and marginal["observed_positive_count"] == unblocked["count"],
        "unblocked/all-attempt outcomes disagree",
    )
    if compact:
        return
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


def reconcile_metrics(parts, total, populations):
    for population in populations:
        for name in POPULATIONS[population]:
            for key in SUMS:
                require(
                    agrees(
                        math.fsum(part[population][name][key] for part in parts),
                        total[population][name][key],
                    ),
                    "probability subgroup/per-game sums do not reconcile",
                )


def validate_assessment(document):
    metrics, per_game = document["metrics"], document["per_game"]
    require(
        [row["game_id"] for row in per_game] == list(document["game_dates"]),
        "per-game metric identities/order disagree",
    )
    validate_metrics(metrics)
    for row in per_game:
        validate_metrics(row["metrics"])
    reconcile_metrics([row["metrics"] for row in per_game], metrics, POPULATIONS)
    for population, names in POPULATIONS.items():
        for name in names:
            for index, bucket in enumerate(metrics[population][name]["calibration"]):
                for key in (
                    "count",
                    "observed_positive_count",
                    "predicted_probability_sum",
                ):
                    require(
                        agrees(
                            math.fsum(
                                row["metrics"][population][name]["calibration"][index][key]
                                for row in per_game
                            ),
                            bucket[key],
                        ),
                        "per-game calibration bins do not reconcile",
                    )
    for name in ("all", "blocked", "unblocked"):
        for key in ("count", "negative_log_likelihood_sum"):
            require(
                agrees(
                    math.fsum(
                        row["metrics"]["observed_record_likelihood"][name][key] for row in per_game
                    ),
                    metrics["observed_record_likelihood"][name][key],
                ),
                "per-game likelihood sums do not reconcile",
            )
    coverage = document["coverage"]
    require(
        [row["game_id"] for row in coverage["per_game"]] == list(document["game_dates"]),
        "per-game coverage identities/order disagree",
    )
    for row, covered in zip(per_game, coverage["per_game"], strict=True):
        supported = covered["attempts_by_status"]
        require(
            row["metrics"]["all_attempt_recorded_context"]["candidate_all"]["count"]
            == (integer(supported["eligible"]) if supported else 0),
            "per-game metric/coverage population mismatch",
        )
    require(
        metrics["all_attempt_recorded_context"]["candidate_all"]["count"]
        == (
            integer(coverage["attempts_by_status"]["eligible"])
            if coverage["attempts_by_status"]["eligible"] is not None
            else 0
        ),
        "overall metric/coverage population mismatch",
    )
    groups = document["groups"]
    require(
        set(groups) == {*GROUP_DOMAINS, "season", "actor_evidence"},
        "native subgroup categories missing or unexpected",
    )
    seasons = sorted({gid[:4] + str(int(gid[:4]) + 1) for gid in document["game_dates"]})
    actor_pairs = (("u", "shooter"), ("r", "shooter"), ("r", "goalie"))
    actor_keys = [(row["stage"], row["actor"], row["value"]) for row in groups["actor_evidence"]]
    require(
        actor_keys
        == [
            (stage, actor, basis)
            for stage, actor in actor_pairs
            for basis in ("observed_in_state", "other_seasons_only", "unseen")
        ],
        "native stage-specific actor groups missing or duplicated",
    )
    for category, rows in groups.items():
        if category != "actor_evidence":
            expected = seasons if category == "season" else GROUP_DOMAINS[category]
            require(
                len(rows) == len(expected)
                and all(
                    type(row["value"]) is type(value) and row["value"] == value
                    for row, value in zip(rows, expected, strict=True)
                ),
                f"{category}: native subgroup entries missing or unexpected",
            )
        for index, row in enumerate(rows):
            validate_metrics(row["metrics"], tip=category in TIP_GROUPS)
            parts = []
            for game in per_game:
                require(
                    set(game["groups"]) == set(groups)
                    and len(game["groups"][category]) == len(rows),
                    "per-game subgroup categories/dimensions disagree",
                )
                part = game["groups"][category][index]
                require(
                    {key: value for key, value in part.items() if key != "metrics"}
                    == {key: value for key, value in row.items() if key != "metrics"},
                    "per-game subgroup descriptors disagree",
                )
                validate_metrics(part["metrics"], tip=category in TIP_GROUPS, compact=True)
                parts.append(part["metrics"])
            reconcile_metrics(
                parts,
                row["metrics"],
                ("unblocked_conversion",) if category in TIP_GROUPS else POPULATIONS,
            )
    for scope in [document, *per_game]:
        for category, rows in scope["groups"].items():
            if category == "actor_evidence":
                partitions = [
                    [row["metrics"] for row in rows if (row["stage"], row["actor"]) == pair]
                    for pair in actor_pairs
                ]
            else:
                partitions = [[row["metrics"] for row in rows]]
            for partition in partitions:
                if category in TIP_GROUPS:
                    tip_rows = [
                        row["metrics"]
                        for row in scope["groups"]["shot_type"]
                        if row["value"] in ("tip-in", "deflected")
                    ]
                    total = {
                        "unblocked_conversion": {
                            name: {
                                key: math.fsum(
                                    row["unblocked_conversion"][name][key] for row in tip_rows
                                )
                                for key in SUMS
                            }
                            for name in POPULATIONS["unblocked_conversion"]
                        }
                    }
                    reconcile_metrics(partition, total, ("unblocked_conversion",))
                else:
                    reconcile_metrics(partition, scope["metrics"], POPULATIONS)
                    if scope is document:
                        for name in ("all", "blocked", "unblocked"):
                            for key in ("count", "negative_log_likelihood_sum"):
                                require(
                                    agrees(
                                        math.fsum(
                                            part["observed_record_likelihood"][name][key]
                                            for part in partition
                                        ),
                                        metrics["observed_record_likelihood"][name][key],
                                    ),
                                    "subgroup likelihood sums do not reconcile",
                                )


def calendar_blocks(dates, days):
    parsed = [date.fromisoformat(value) for value in dates]
    first = min(parsed)
    return np.array([(value - first).days // days for value in parsed], dtype=np.int64)


def ratio_interval(numerators, denominators, seed, *, observed=None, blocks=None, samples=None):
    """pool additive sums; retain zero-contribution units and every undefined draw."""
    numerators = np.asarray(numerators, dtype=np.float64)
    denominators = np.asarray(denominators, dtype=np.float64)
    require(
        numerators.shape == denominators.shape
        and numerators.ndim == 1
        and len(numerators) > 0
        and np.isfinite(numerators).all()
        and np.isfinite(denominators).all()
        and (denominators >= 0).all(),
        "invalid resampling sums",
    )
    contributing_games = int(np.count_nonzero(denominators))
    total = float(denominators.sum())
    estimate = float(numerators.sum() / total) if total else None
    all_one_label = False
    if observed is not None:
        observed = np.asarray(observed, dtype=np.float64)
        require(
            observed.shape == denominators.shape
            and np.isfinite(observed).all()
            and (observed >= 0).all()
            and (observed <= denominators).all(),
            "invalid observed label sums",
        )
        all_one_label = bool(total and (observed.sum() == 0 or observed.sum() == total))
    if blocks is not None:
        n = int(max(blocks)) + 1
        numerators = np.bincount(blocks, weights=numerators, minlength=n)
        denominators = np.bincount(blocks, weights=denominators, minlength=n)
    else:
        n = len(numerators)
    if samples is None:
        samples = np.random.Generator(np.random.PCG64(seed)).integers(0, n, size=(2000, n))
    require(samples.shape == (2000, n), "resampling dimensions disagree")
    sampled_denominators = denominators[samples].sum(axis=1)
    undefined = int(np.count_nonzero(sampled_denominators == 0))
    sampled = np.divide(
        numerators[samples].sum(axis=1),
        sampled_denominators,
        out=np.full(2000, np.nan),
        where=sampled_denominators != 0,
    )
    require(estimate is None or math.isfinite(estimate), "nonfinite pooled estimate")
    require(np.isfinite(sampled).sum() + undefined == 2000, "nonfinite bootstrap estimate")
    reason = (
        "zero attempt denominator in at least one resampled draw"
        if undefined
        else "all-one-label population cannot establish calibration support"
        if all_one_label
        else None
    )
    result = {
        "estimate": estimate,
        "count": int(total),
        "contributing_games": contributing_games,
        "interval": None
        if undefined
        else np.percentile(sampled, [2.5, 97.5], method="linear").tolist(),
        "undefined_draws": undefined,
        "missing_reason": "zero attempt denominator in at least one resampled draw"
        if undefined
        else None,
    }
    if observed is not None:
        result.update(
            observed_positive_count=int(observed.sum()),
            all_one_label=all_one_label,
            calibration_support_missing_reason=reason,
        )
    if blocks is not None:
        result.update(contributing_blocks=int(np.count_nonzero(denominators)), selected_blocks=n)
    return result


def assessment_review(entry, benchmarks, seed):
    document = entry["document"]
    validate_assessment(document)
    metrics, per_game = document["metrics"], document["per_game"]
    dates = list(document["game_dates"].values())
    units = {
        "games": None,
        "calendar_7_day": calendar_blocks(dates, 7),
        "calendar_14_day": calendar_blocks(dates, 14),
    }
    samples = {
        name: np.random.Generator(np.random.PCG64(seed)).integers(
            0,
            len(dates) if blocks is None else int(max(blocks)) + 1,
            size=(2000, len(dates) if blocks is None else int(max(blocks)) + 1),
        )
        for name, blocks in units.items()
    }

    def intervals(rows, numerator, calibration=False):
        return {
            name: ratio_interval(
                numerator,
                [row["count"] for row in rows],
                seed,
                observed=[row["observed_positive_count"] for row in rows] if calibration else None,
                blocks=blocks,
                samples=samples[name],
            )
            for name, blocks in units.items()
        }

    comparisons, calibration = {}, {}
    for population, names in POPULATIONS.items():
        comparisons[population], calibration[population] = {}, {}
        for name in names:
            origin = entry if name == names[0] else benchmarks[population]
            saved = origin["document"]["metrics"][population][name]
            games = [row["metrics"][population][name] for row in origin["document"]["per_game"]]
            overall = intervals(
                games,
                [
                    row["predicted_probability_sum"] - row["observed_positive_count"]
                    for row in games
                ],
                True,
            )
            bins = []
            for index, bucket in enumerate(saved["calibration"]):
                selected = [row["calibration"][index] for row in games]
                results = intervals(
                    selected,
                    [
                        row["predicted_probability_sum"] - row["observed_positive_count"]
                        for row in selected
                    ],
                    True,
                )
                count_fraction = bucket["count"] / saved["count"] if saved["count"] else None
                mass_fraction = (
                    bucket["predicted_probability_sum"] / saved["predicted_probability_sum"]
                    if saved["predicted_probability_sum"]
                    else None
                )
                bins.append(
                    dict(
                        bucket,
                        **results["games"],
                        dependence={
                            key: value for key, value in results.items() if key != "games"
                        },
                        attempt_fraction=count_fraction,
                        predicted_positive_mass_fraction=mass_fraction,
                        assessment_consequential=bool(
                            (count_fraction is not None and count_fraction >= 0.05)
                            or (mass_fraction is not None and mass_fraction >= 0.05)
                        ),
                    )
                )
            calibration[population][name] = {
                "outcome": OUTCOMES[population],
                "source_label": origin["label"],
                "overall": dict(
                    overall["games"],
                    dependence={key: value for key, value in overall.items() if key != "games"},
                ),
                "bins": bins,
            }
        if len(names) == 1:
            comparisons[population] = {"missing_reason": "no native marginal-unblocked benchmark"}
            continue
        candidate, benchmark = names
        benchmark_document = benchmarks[population]["document"]
        candidate_games = [row["metrics"][population][candidate] for row in per_game]
        benchmark_games = [
            row["metrics"][population][benchmark] for row in benchmark_document["per_game"]
        ]
        for measure, key in (
            ("log_loss", "log_loss_sum"),
            ("brier_score", "brier_score_sum"),
        ):
            results = intervals(
                candidate_games,
                [
                    left[key] - right[key]
                    for left, right in zip(candidate_games, benchmark_games, strict=True)
                ],
            )
            count = results["games"]["count"]
            comparisons[population][measure] = dict(
                results["games"],
                dependence={name: row for name, row in results.items() if name != "games"},
                benchmark_label=benchmarks[population]["label"],
                candidate_mean=metrics[population][candidate][key] / count if count else None,
                benchmark_mean=benchmark_document["metrics"][population][benchmark][key] / count
                if count
                else None,
            )
    subgroup_reviews = {}
    for category, groups in document["groups"].items():
        subgroup_reviews[category] = []
        for index, group in enumerate(groups):
            row = {key: value for key, value in group.items() if key != "metrics"}
            row["calibration"], row["comparisons"] = {}, {}
            row["metrics"], row["benchmark_calibration"] = {}, {}
            row["criterion_scope"] = (
                "omission_diagnostic"
                if category in ("period", "minute_band")
                else "prospective_calibration"
            )
            for population, native in group["metrics"].items():
                if population == "observed_record_likelihood":
                    continue
                candidate = POPULATIONS[population][0]
                saved = native[candidate]
                row["metrics"][population] = {
                    candidate: {key: saved[key] for key in ("outcome", *SUMS)}
                }
                games = [
                    game["groups"][category][index]["metrics"][population][candidate]
                    for game in per_game
                ]
                results = intervals(
                    games,
                    [
                        game["predicted_probability_sum"] - game["observed_positive_count"]
                        for game in games
                    ],
                    True,
                )
                total = metrics[population][candidate]
                count_fraction = saved["count"] / total["count"] if total["count"] else None
                mass_fraction = (
                    saved["predicted_probability_sum"] / total["predicted_probability_sum"]
                    if total["predicted_probability_sum"]
                    else None
                )
                row["calibration"][population] = dict(
                    results["games"],
                    outcome=OUTCOMES[population],
                    dependence={
                        name: result for name, result in results.items() if name != "games"
                    },
                    attempt_fraction=count_fraction,
                    predicted_positive_mass_fraction=mass_fraction,
                    assessment_consequential=bool(
                        (count_fraction is not None and count_fraction >= 0.05)
                        or (mass_fraction is not None and mass_fraction >= 0.05)
                    ),
                )
                if len(POPULATIONS[population]) == 1:
                    continue
                benchmark = POPULATIONS[population][1]
                benchmark_document = benchmarks[population]["document"]
                benchmark_saved = benchmark_document["groups"][category][index]["metrics"][
                    population
                ][benchmark]
                row["metrics"][population][benchmark] = {
                    key: benchmark_saved[key] for key in ("outcome", *SUMS)
                }
                benchmark_games = [
                    game["groups"][category][index]["metrics"][population][benchmark]
                    for game in benchmark_document["per_game"]
                ]
                benchmark_results = intervals(
                    benchmark_games,
                    [
                        game["predicted_probability_sum"] - game["observed_positive_count"]
                        for game in benchmark_games
                    ],
                    True,
                )
                row["benchmark_calibration"][population] = dict(
                    benchmark_results["games"],
                    outcome=OUTCOMES[population],
                    source_label=benchmarks[population]["label"],
                    dependence={
                        name: result
                        for name, result in benchmark_results.items()
                        if name != "games"
                    },
                )
                row["comparisons"][population] = {}
                for measure, key in (
                    ("log_loss", "log_loss_sum"),
                    ("brier_score", "brier_score_sum"),
                ):
                    paired = intervals(
                        games,
                        [
                            left[key] - right[key]
                            for left, right in zip(games, benchmark_games, strict=True)
                        ],
                    )
                    row["comparisons"][population][measure] = dict(
                        paired["games"],
                        benchmark_label=benchmarks[population]["label"],
                        dependence={
                            name: result for name, result in paired.items() if name != "games"
                        },
                    )
            subgroup_reviews[category].append(row)
    monthly = []
    for month in sorted({value[:7] for value in dates}):
        games = [game for game in per_game if document["game_dates"][game["game_id"]][:7] == month]
        populations = {}
        for population, names in POPULATIONS.items():
            selected = [game["metrics"][population][names[0]] for game in games]
            count = sum(row["count"] for row in selected)
            predicted = math.fsum(row["predicted_probability_sum"] for row in selected)
            observed = sum(row["observed_positive_count"] for row in selected)
            populations[population] = {
                "outcome": OUTCOMES[population],
                "count": count,
                "predicted_probability_sum": predicted,
                "observed_positive_count": observed,
                "predicted_minus_observed": (predicted - observed) / count if count else None,
            }
        monthly.append({"month": month, "populations": populations})
    return {
        "label": entry["label"],
        "population_definitions": document["prediction_definitions"],
        "reference_season": document["reference_season"],
        "coverage": document["coverage"],
        "selection": document["selection"],
        "game_dates": document["game_dates"],
        "comparisons": comparisons,
        "calibration": calibration,
        "subgroups": subgroup_reviews,
        "native_subgroup_summaries": document["groups"],
        "monthly_diagnostics": monthly,
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
        isinstance(distribution, list) and len(distribution) == (cells if blocked else 1),
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
        0 <= value <= 1 and agrees(float(weights.sum()), 1) and agrees(float(masses.sum()), value),
        "origin normalization/value conservation failed",
    )
    return weights, masses, value


def change_summary(current, reference, change, blocked):
    n = current["count"]
    current_total, reference_total = (
        float(current["mass"].sum()),
        float(reference["mass"].sum()),
    )
    absolute_mass = float(np.abs(current["mass"] - reference["mass"]).sum()) if n else None
    require(
        current["count"] == reference["count"]
        and current["goals"] == reference["goals"]
        and agrees(change["value_sum"], current_total - reference_total),
        "event/spatial opportunity changes do not conserve population or mass",
    )
    return {
        "count": n,
        "observed_goals": current["goals"],
        "reference_total_value": reference_total if n else None,
        "alternative_total_value": current_total if n else None,
        "value_change": {
            "total": change["value_sum"] if n else None,
            "mean": change["value_sum"] / n if n else None,
            "mean_absolute": change["absolute_value_sum"] / n if n else None,
            "root_mean_square": math.sqrt(change["squared_value_sum"] / n) if n else None,
            "maximum_absolute": change["maximum_absolute_value"] if n else None,
            "absolute_total_fraction_of_reference": abs(change["value_sum"]) / reference_total
            if reference_total
            else None,
        },
        "blocked_posterior_total_variation": {
            "mean": change["origin_tv_sum"] / n if n and blocked else None,
            "maximum": change["origin_tv_maximum"] if n and blocked else None,
            "missing_reason": None
            if blocked and n
            else "no valued blocked events"
            if blocked
            else "unblocked recorded-proxy origins are point masses",
            "maximum_event": change["posterior_maximum_event"] if blocked else None,
        },
        "absolute_spatial_mass_change": absolute_mass,
        "absolute_spatial_mass_change_fraction_of_reference": absolute_mass / reference_total
        if reference_total
        else None,
        "spatial_shape_total_variation": float(
            np.abs(current["mass"] / current_total - reference["mass"] / reference_total).sum() / 2
        )
        if current_total and reference_total
        else None,
        "maximum_event": change["maximum_event"],
        "missing_reason": "no valued events in this population" if not n else None,
        "ratio_missing_reason": "zero reference opportunity mass" if not reference_total else None,
        "shape_missing_reason": "zero total opportunity mass makes spatial shape undefined"
        if not current_total or not reference_total
        else None,
    }


def sensitivity_review(entries, reference_label):
    reference_index = next(
        index for index, entry in enumerate(entries) if entry["label"] == reference_label
    )
    cells = len(entries[0]["model"]["grid"]["centers"])
    game_ids = list(entries[0]["document"]["game_dates"])
    game_order = {gid: index for index, gid in enumerate(game_ids)}
    # each tuple defines one independently conserved population; grouping never changes native values.
    keys = [(name, "overall", None) for name in ("blocked", "unblocked")]
    keys += [
        (name, category, value)
        for name in ("blocked", "unblocked")
        for category in ("shot_type", "role")
        for value in GROUP_DOMAINS[category]
    ]
    totals = [
        {key: {"count": 0, "goals": 0, "mass": np.zeros(cells)} for key in keys} for _ in entries
    ]
    changes = [
        {
            key: {
                "value_sum": 0.0,
                "absolute_value_sum": 0.0,
                "squared_value_sum": 0.0,
                "maximum_absolute_value": 0.0,
                "origin_tv_sum": 0.0,
                "origin_tv_maximum": 0.0,
                "maximum_event": None,
                "posterior_maximum_event": None,
            }
            for key in keys
        }
        for _ in entries
    ]
    tips = [{} for _ in entries]
    counts, per_game, origins = (
        Counter(),
        {gid: Counter() for gid in game_ids},
        Counter(),
    )
    previous = None
    model_fields = {
        "season_basis",
        "state_season",
        "actor_evidence",
        "origin_basis",
        "origin_distribution",
        "reference_opportunity_value",
    }
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
            row_keys = [(row["game_id"], row["source_index"], row["status"]) for row in rows]
            require(
                all(key == row_keys[0] for key in row_keys),
                "scored stream keys/statuses differ or are reordered",
            )
            gid, source_index, status = row_keys[0]
            integer(source_index)
            require(gid in game_order and status in STATUSES, "invalid scored key/status")
            order = game_order[gid], source_index
            require(
                previous is None or order > previous,
                "scored stream violates ordered selection/source indices",
            )
            previous = order
            source = {key: value for key, value in rows[0].items() if key not in model_fields}
            for row in rows:
                require(
                    type(row["schema_version"]) is int and row["schema_version"] == 2,
                    "unsupported scored row schema",
                )
                require(
                    row["event_id"] is None or type(row["event_id"]) is int,
                    "invalid scored event identity",
                )
                require(
                    type(row["blocked"]) is bool
                    and type(row["goal"]) is bool
                    and not (row["blocked"] and row["goal"]),
                    "invalid scored outcome",
                )
                require(
                    {key: value for key, value in row.items() if key not in model_fields}
                    == source,
                    "scored source records differ across same events",
                )
                if status != "valued":
                    require(
                        all(row[key] is None for key in model_fields),
                        "unvalued attempt has invented model state/origin/value",
                    )
            counts[status] += 1
            per_game[gid][status] += 1
            name = "blocked" if rows[0]["blocked"] else "unblocked"
            is_tip = rows[0]["shot_type"] in ("tip-in", "deflected")
            tip_key = (rows[0]["shot_type"], rows[0]["season"], name)
            if is_tip:
                for index in range(len(entries)):
                    ledger = tips[index].setdefault(
                        tip_key,
                        {
                            "count": 0,
                            "goals": 0,
                            "counts_by_status": Counter(),
                            "mass": np.zeros(cells),
                            "valued_count": 0,
                            "valued_goals": 0,
                        },
                    )
                    ledger["count"] += 1
                    ledger["goals"] += rows[0]["goal"]
                    ledger["counts_by_status"][status] += 1
            if status != "valued":
                continue
            require(
                rows[0]["shot_type"] in GROUP_DOMAINS["shot_type"]
                and rows[0]["role"] in GROUP_DOMAINS["role"],
                "unsupported valued type/role",
            )
            distributions = [scored_distribution(row, cells) for row in rows]
            origins[rows[0]["origin_basis"]] += 1
            reference = distributions[reference_index]
            selected = [
                (name, "overall", None),
                (name, "shot_type", rows[0]["shot_type"]),
                (name, "role", rows[0]["role"]),
            ]
            for index, (weights, mass, value) in enumerate(distributions):
                if is_tip:
                    tips[index][tip_key]["mass"] += mass
                    tips[index][tip_key]["valued_count"] += 1
                    tips[index][tip_key]["valued_goals"] += rows[0]["goal"]
                for key in selected:
                    total = totals[index][key]
                    total["count"] += 1
                    total["goals"] += rows[0]["goal"]
                    total["mass"] += mass
                    if index == reference_index:
                        continue
                    change = changes[index][key]
                    delta = value - reference[2]
                    tv = (
                        float(np.abs(weights - reference[0]).sum() / 2)
                        if name == "blocked"
                        else 0.0
                    )
                    change["value_sum"] += delta
                    change["absolute_value_sum"] += abs(delta)
                    change["squared_value_sum"] += delta * delta
                    if (
                        change["maximum_event"] is None
                        or abs(delta) > change["maximum_absolute_value"]
                    ):
                        change["maximum_absolute_value"] = abs(delta)
                        change["maximum_event"] = {
                            "game_id": gid,
                            "source_index": source_index,
                            "event_id": rows[0]["event_id"],
                            "original_type": rows[0]["shot_type"],
                            "role": rows[0]["role"],
                            "reference_value": reference[2],
                            "alternative_value": value,
                            "signed_change": delta,
                            "blocked_posterior_total_variation": tv if name == "blocked" else None,
                        }
                    change["origin_tv_sum"] += tv
                    if name == "blocked" and (
                        change["posterior_maximum_event"] is None
                        or tv > change["origin_tv_maximum"]
                    ):
                        change["posterior_maximum_event"] = {
                            "game_id": gid,
                            "source_index": source_index,
                            "event_id": rows[0]["event_id"],
                            "original_type": rows[0]["shot_type"],
                            "role": rows[0]["role"],
                            "total_variation": tv,
                        }
                    change["origin_tv_maximum"] = max(change["origin_tv_maximum"], tv)
    for index, entry in enumerate(entries):
        document = entry["document"]
        for manifest in [
            document["counts_by_status"],
            *document["per_game"].values(),
            document["counts_by_origin_basis"],
        ]:
            for value in manifest.values():
                integer(value)
        require(
            {status: counts[status] for status in STATUSES} == document["counts_by_status"],
            "scored row counts disagree with manifest",
        )
        require(
            {gid: {status: row[status] for status in STATUSES} for gid, row in per_game.items()}
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
        require(
            all(
                counts[status]
                == (
                    integer(covered["eligible" if status == "valued" else status])
                    if covered["eligible" if status == "valued" else status] is not None
                    else 0
                )
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
        for name in ("blocked", "unblocked"):
            overall = totals[index][(name, "overall", None)]
            for category in ("shot_type", "role"):
                parts = [
                    totals[index][(name, category, value)] for value in GROUP_DOMAINS[category]
                ]
                require(
                    sum(part["count"] for part in parts) == overall["count"]
                    and np.allclose(
                        np.sum([part["mass"] for part in parts], axis=0),
                        overall["mass"],
                        rtol=1e-10,
                        atol=1e-10,
                    ),
                    "spatial subgroup mass/count conservation failed",
                )
    comparisons = []
    for index, entry in enumerate(entries):
        if index == reference_index:
            continue
        model, reference_model = entry["model"], entries[reference_index]["model"]
        populations = {
            name: change_summary(
                totals[index][(name, "overall", None)],
                totals[reference_index][(name, "overall", None)],
                changes[index][(name, "overall", None)],
                name == "blocked",
            )
            for name in ("blocked", "unblocked")
        }
        comparisons.append(
            {
                "label": entry["label"],
                "reference_label": reference_label,
                "populations": populations,
                "subgroups": {
                    category: [
                        {
                            "value": value,
                            "populations": {
                                name: change_summary(
                                    totals[index][(name, category, value)],
                                    totals[reference_index][(name, category, value)],
                                    changes[index][(name, category, value)],
                                    name == "blocked",
                                )
                                for name in ("blocked", "unblocked")
                            },
                        }
                        for value in GROUP_DOMAINS[category]
                    ]
                    for category in ("shot_type", "role")
                },
                "kernel_changed": model["kernel"] != reference_model["kernel"],
                "config_changed_fields": [
                    key
                    for key in model["config"]
                    if model["config"][key] != reference_model["config"][key]
                ],
                "reference_weights_equal": model["reference"] == reference_model["reference"],
                "training_selection_equal": model["selection"] == reference_model["selection"],
                "model_digest_equal": entry["document"]["model"]["sha256"]
                == entries[reference_index]["document"]["model"]["sha256"],
            }
        )
    population_counts = {
        "blocked": origins["inferred_block"],
        "unblocked": origins["recorded_proxy"],
    }
    maps = []
    ledgers = []
    for index, entry in enumerate(entries):
        maps.append(
            {
                "label": entry["label"],
                **{
                    name: totals[index][(name, "overall", None)]["mass"].tolist()
                    if population_counts[name]
                    else None
                    for name in population_counts
                },
                "missing_reasons": {
                    name: None
                    if population_counts[name]
                    else "no valued events in this population"
                    for name in population_counts
                },
            }
        )
        ledger_rows = []
        for (original_type, season, population), ledger in sorted(tips[index].items()):
            ledger_rows.append(
                {
                    "original_type": original_type,
                    "season": season,
                    "population": population,
                    "count": ledger["count"],
                    "goals": ledger["goals"],
                    "valued_count": ledger["valued_count"],
                    "valued_goals": ledger["valued_goals"],
                    "counts_by_status": {
                        status: ledger["counts_by_status"][status] for status in STATUSES
                    },
                    "opportunity_total": float(ledger["mass"].sum())
                    if ledger["valued_count"]
                    else None,
                    "spatial_opportunity_mass": ledger["mass"].tolist()
                    if ledger["valued_count"]
                    else None,
                    "missing_opportunity_count": ledger["count"] - ledger["valued_count"],
                    "missing_reason": None
                    if ledger["valued_count"]
                    else "no valued tip events in this population",
                }
            )
        ledgers.append(
            {
                "label": entry["label"],
                "rows": ledger_rows,
                "measurement_limit": "recorded unblocked tip locations are proxies; inferred blocked origins do not establish tip location; kernel variants do not bracket proxy error",
            }
        )
    return {
        "population_counts": population_counts,
        "reference_score": reference_label,
        "reference_season": entries[0]["document"]["reference_season"],
        "selection": entries[0]["document"]["selection"],
        "game_dates": entries[0]["document"]["game_dates"],
        "counts_by_status": {status: counts[status] for status in STATUSES},
        "grid": entries[0]["model"]["grid"],
        "spatial_opportunity_mass": maps,
        "tip_measurement_ledger": ledgers,
        "comparisons": comparisons,
        "comparison_missing_reason": None if comparisons else "no compatible alternative supplied",
        "units": "reference opportunity mass in expected goals; event differences are alternative minus reference",
        "uncertainty_reason": "point estimates; probability bootstrap intervals exclude origin-law and fitted-parameter uncertainty",
    }


def save_figures(assessments, sensitivity, output):
    figures = []
    for index, assessment in enumerate(assessments):
        figure, axes = plt.subplots(
            3,
            3,
            figsize=(18, 11),
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
                            markerfacecolor=color
                            if bucket["interval"]
                            and not bucket["all_one_label"]
                            and bucket["contributing_games"] >= 100
                            else "none",
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
                    label=f"{assessment['calibration'][population][name]['source_label']} {'candidate' if offset == 0 else 'benchmark'}; n={sum(b['count'] for b in bins)}",
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
            f"held-out selected cohort: {len(assessment['game_dates'])} games, {min(assessment['game_dates'].values())} to {max(assessment['game_dates'].values())}; model reference season {assessment['reference_season']}.\n"
            "factual actor-state probabilities: conversion conditions on unblocked and its quantized recorded-origin proxy; recorded-context goal/unblocked probabilities integrate the origin prior.\n"
            "origin-integrated probabilities omit focal location, outcome and posterior. reconciled type/eligibility remain retrospective; this is not a demonstrated live forecast.\n"
            "95% paired game-bootstrap intervals condition on fitted models; fitting, selection and origin-law uncertainty excluded. no simultaneous-coverage claim.\n"
            "hollow points: undefined draws, all-one labels or fewer than 100 contributing games. undefined draws omit intervals; degenerate label intervals cannot establish support.\n"
            "diagnostic zoom clips display at ±0.02; full-range panels retain every point/interval. all 20 fixed bins remain; count axes use symlog (linear 0–1, then log).\n"
            "seven-/fourteen-calendar-day dependence results and consequential subgroup intervals are saved in comparison.json; protocol owns margins and frozen groups.",
            fontsize=8,
        )
        figure.tight_layout(rect=(0, 0.15, 1, 0.94))
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
    reference_notes = [
        f"selected cohort: {len(sensitivity['game_dates'])} games, {min(sensitivity['game_dates'].values())} to {max(sensitivity['game_dates'].values())}; reference season {sensitivity['reference_season']}.",
        f"reference score: {sensitivity['reference_score']}; every model uses identical target-season joint matchup counts/weights and training population.",
        "standardization preserves recorded type and supported preceding-play/scalar context; exact joint-reference averaging removes modeled residual execution.",
    ]
    for comparison in sensitivity["comparisons"]:
        reference_notes.append(
            f"{comparison['label']} versus {comparison['reference_label']}: matched events, coverage, geometry and reference; {'kernel changed' if comparison['kernel_changed'] else 'kernel matched'}; refitting effects retained."
        )
    reference_caption = "\n".join(textwrap.fill(note, width=135) for note in reference_notes)
    caption_height = 0.15 * (4 + reference_caption.count("\n"))
    maps = sensitivity["spatial_opportunity_mass"]
    centers = np.asarray(sensitivity["grid"]["centers"])
    reference = next(row for row in maps if row["label"] == sensitivity["reference_score"])
    for difference in (False, True) if sensitivity["comparisons"] else (False,):
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
    if not sensitivity["comparisons"]:
        figures.extend(
            {"kind": kind, "missing_reason": "no compatible alternative supplied"}
            for kind in ("spatial_opportunity_mass_change", "event_value_change")
        )
        return figures
    figure, axes = plt.subplots(1, 2, figsize=(12, 3.4 + caption_height), sharex=True, sharey=True)
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
    figure.tight_layout(rect=(0, (caption_height + 0.1) / (3.4 + caption_height), 1, 0.82))
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
                "benchmarks",
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
            and evidence["schema_version"] == 2
            and evidence["purpose"] == "research",
            "research evidence schema 2 required",
        )
        protocol = absolute_path(evidence["protocol"])
        settings = evidence["resampling"]
        require(
            set(settings) == {"draws", "seed"}
            and type(settings["draws"]) is int
            and settings["draws"] == 2000
            and type(settings["seed"]) is int
            and settings["seed"] == 3032026,
            "resampling requires 2000 draws and seed 3032026",
        )
        assessments = load_entries(evidence["assessments"], "assessments")
        scores = load_entries(evidence.get("scores", []), "scores")
        require(bool(assessments or scores), "no assessment or score evidence supplied")
        require(
            ("benchmarks" in evidence) == bool(assessments),
            "benchmarks required exactly when assessments are nonempty",
        )
        benchmarks = {}
        if assessments:
            selected = evidence["benchmarks"]
            require(
                isinstance(selected, dict)
                and set(selected) == {"unblocked_conversion", "all_attempt_recorded_context"},
                "invalid benchmark populations",
            )
            for population, label in selected.items():
                require(
                    isinstance(label, str) and label in {entry["label"] for entry in assessments},
                    "benchmark label must identify a supplied assessment",
                )
                benchmarks[population] = next(
                    entry for entry in assessments if entry["label"] == label
                )
        require(
            ("reference_score" in evidence) == ("scores" in evidence),
            "reference_score required exactly when scores are supplied",
        )
        if "scores" in evidence:
            require(
                bool(scores)
                and isinstance(evidence["reference_score"], str)
                and evidence["reference_score"] in {entry["label"] for entry in scores},
                "scores require a supplied reference label",
            )
        if assessments and scores:
            for field in (
                "implementation",
                "selection",
                "inputs",
                "game_dates",
                "coverage",
                "geometry",
                "reference",
                "reference_season",
            ):
                require(
                    assessments[0]["document"][field] == scores[0]["document"][field],
                    f"cohort: incompatible assessment/score {field}",
                )
            for field in ("selection", "inputs", "training_game_dates"):
                require(
                    assessments[0]["model"][field] == scores[0]["model"][field],
                    f"cohort: incompatible assessment/score model training {field}",
                )
        roots = [
            str(evidence_path.parent),
            str(protocol.parent),
            *[str(entry["path"].parent) for entry in assessments + scores],
        ]
        for entry in assessments + scores:
            document = entry["document"]
            roots.append(str(Path(document["model"]["path"]).parent))
            roots.extend(str(Path(reference["path"]).parent) for reference in document["inputs"])
            roots.extend(
                str(Path(reference["path"]).parent) for reference in entry["model"]["inputs"]
            )
            if "attempts" in document:
                roots.append(str(Path(document["attempts"]["path"]).parent))
        output = output_path(args.out, roots)
        implementation = implementation_identity()
        implementation.update(
            numpy_version=np.__version__,
            scipy_version=scipy.__version__,
            matplotlib_version=matplotlib.__version__,
            lockfile_sha256=identity(Path(__file__).resolve().parents[1] / "uv.lock")["sha256"],
        )
        clean_implementation(implementation)
        reviews = [assessment_review(entry, benchmarks, settings["seed"]) for entry in assessments]
        sensitivity = sensitivity_review(scores, evidence["reference_score"]) if scores else None
        artifacts = []
        for kind, entries in (("assessment", assessments), ("score", scores)):
            for entry in entries:
                document = entry["document"]
                artifacts.append(
                    {
                        "label": entry["label"],
                        "kind": kind,
                        "artifact": identity(entry["path"]),
                        "executing_implementation": document["implementation"],
                        "model": document["model"],
                        "model_implementation": entry["model"]["implementation"],
                        "model_training_selection": entry["model"]["selection"],
                        "model_consumed_inputs": entry["model"]["inputs"],
                        "model_config_identity": entry["model"]["config_identity"],
                        "reference": document["reference"],
                        "reference_season": document["reference_season"],
                        "selection": document["selection"],
                        "consumed_inputs": document["inputs"],
                        "attempts": document.get("attempts"),
                    }
                )
        output.mkdir()
        figures = save_figures(reviews, sensitivity, output)
        for figure in figures:
            if "path" in figure:
                figure["sha256"] = identity(output / figure["path"])["sha256"]
        comparison = {
            "schema_version": 2,
            "purpose": "research",
            "scientific_assessment": "not_performed",
            "implementation": implementation,
            "evidence": identity(evidence_path),
            "protocol": identity(protocol),
            "consumed_artifacts": artifacts,
            "selected_benchmarks": {
                population: {
                    "label": entry["label"],
                    "artifact": identity(entry["path"]),
                    "model": entry["document"]["model"],
                }
                for population, entry in benchmarks.items()
            },
            "reference_season": (assessments or scores)[0]["document"]["reference_season"],
            "resampling": dict(
                settings,
                generator="numpy.random.Generator / PCG64",
                method="paired whole-game and nonoverlapping seven-/fourteen-calendar-day block sampling with replacement; original number of units, including empty units; pooled attempt-weighted ratios; 95% linear-percentile intervals",
                uncertainty="conditional on fitted models and resampling assumptions; pointwise intervals exclude fitting, selection and origin-law uncertainty",
            ),
            "assessments": reviews,
            "sensitivity": sensitivity,
            "figures": figures,
            "missing_reasons": {
                "assessments": None if reviews else "no assessment evidence supplied",
                "sensitivity": None if sensitivity else "no score evidence supplied",
                "pairwise_sensitivity": sensitivity["comparison_missing_reason"]
                if sensitivity
                else "no score evidence supplied",
                "independent_blocked_origin_evidence": "not supplied by saved artifacts; attributable independent evidence belongs in the written decision",
            },
        }
        write_json(output / "comparison.json", comparison)
        print(f"comparison saved to {output}; scientific judgment belongs in the written decision")
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
