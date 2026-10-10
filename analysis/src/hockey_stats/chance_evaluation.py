"""factual probability diagnostics from one native prediction pass."""

from collections import Counter
import math

import numpy as np
from scipy.special import logsumexp

from .captures import InputContractError
from .chance import CONTEXT_CATEGORIES, ROLES, TYPES
from .chance_cohort import SOURCE_STATUSES, STUDY_INCLUSIONS


PROBABILITY_POPULATIONS = {
    "unblocked_conversion": ("goal", ("candidate_r", "benchmark_r")),
    "all_attempt_recorded_context": ("goal", ("candidate_all", "benchmark_all")),
    "marginal_unblocked": ("unblocked", ("candidate_unblocked",)),
}
PROBABILITY_SUMS = (
    "count",
    "observed_positive_count",
    "predicted_probability_sum",
    "log_loss_sum",
    "brier_score_sum",
)

REGION_NAMES = (
    "behind_goal", "outside_attacking_zone", "in_zone_0_10", "in_zone_10_20",
    "in_zone_20_40", "in_zone_40_plus",
)


def compound_regions(centers) -> np.ndarray:
    """partition native cell centers in the declared geometric precedence."""
    result = []
    for x, y in centers:
        if x > 89:
            region = 0
        elif x <= 25:
            region = 1
        else:
            distance = math.hypot(89 - x, y)
            region = 2 if distance < 10 else 3 if distance < 20 else 4 if distance < 40 else 5
        result.append(region)
    return np.asarray(result, dtype=np.int64)


def compound_region_records(attempt: dict, cell_regions: np.ndarray, cells: dict) -> dict:
    """binary evidence for unblocked/goal and proxy cell in each fixed region.

    denominators contain every eligible attempt. a blocked record has zero
    compound labels and its block-contact cell is never a shooting proxy.
    complement sums stay in log space; no clipping or fabricated origin rows.
    """
    if attempt["status"] != "eligible":
        raise InputContractError("regional evaluation requires an eligible attempt")
    log_pi, log_u = cells["log_pi"], cells["log_u"]
    log_not_u, log_r, log_not_r = (
        cells["log_not_u"], cells["log_r"], cells["log_not_r"]
    )
    terms = {
        "unblocked": (log_pi + log_u, log_pi + log_not_u),
        "goal": (log_pi + log_u + log_r,
                 log_pi + np.logaddexp(log_not_u, log_u + log_not_r)),
    }
    result = {}
    for quantity, (positive, negative) in terms.items():
        records = []
        for region in range(len(REGION_NAMES)):
            included = cell_regions == region
            observed = not attempt["blocked"] and cell_regions[cells["cell_id"]] == region
            if quantity == "goal":
                observed = observed and attempt["goal"]
            records.append(binary_record(
                bool(observed), float(logsumexp(positive[included])),
                float(logsumexp(np.concatenate((negative, positive[~included])))),
            ))
        result[quantity] = records
    return result


GROUP_DOMAINS = {
    "score_bucket": CONTEXT_CATEGORIES["score_bucket"],
    "period": CONTEXT_CATEGORIES["period"],
    "minute_band": CONTEXT_CATEGORIES["minute_band"],
    "role": ROLES,
    "home_away": CONTEXT_CATEGORIES["home_away"],
    "shot_type": [
        "wrist", "snap", "slap", "backhand", "tip-in", "deflected",
        "wrap-around", "poke", "bat", "between-legs", "cradle", None,
    ],
    "model_shot_type": TYPES + [None],
    "recent_context": ["recent", "none"],
    "season_basis": ["fitted", "unobserved", "carried_forward"],
    "tip_distance": ["0_10", "10_20", "20_40", "40_plus"],
    "tip_below_goal_line": [False, True],
}


def binary_metrics(*, calibration: bool = True, outcome: str = "goal") -> dict:
    """additive sufficient statistics for one observed binary quantity."""
    metric = dict(outcome=outcome, **dict.fromkeys(PROBABILITY_SUMS, 0))
    if calibration:
        metric["calibration"] = [
            dict(
                lower=i / 20, upper=(i + 1) / 20, upper_inclusive=i == 19,
                count=0, predicted_probability_sum=0.0, observed_positive_count=0,
            )
            for i in range(20)
        ]
    return metric


def binary_record(observed: bool | int, log_p: float, log_not_p: float) -> dict:
    """log probabilities own loss arithmetic; probabilities are never clipped."""
    if type(observed) not in (bool, int) or observed not in (0, 1):
        raise InputContractError("evaluation: expected binary observed label")
    if not all(
        type(v) in (int, float) and math.isfinite(v) and v <= 0
        for v in (log_p, log_not_p)
    ):
        raise InputContractError("evaluation: nonfinite or positive log probability")
    probability = math.exp(log_p)
    if abs(probability + math.exp(log_not_p) - 1) > 1e-10:
        raise InputContractError("evaluation: probability and complement do not sum to one")
    return dict(
        count=1, observed_positive_count=int(observed),
        predicted_probability_sum=probability,
        log_loss_sum=-(log_p if observed else log_not_p),
        brier_score_sum=(probability - observed) ** 2,
    )


def calibration_bin(probability: float) -> int:
    """bin an already validated native binary probability; the final bin includes one."""
    return next((i for i in range(19) if probability < (i + 1) / 20), 19)


def add_binary(target: dict, record: dict) -> None:
    for field in PROBABILITY_SUMS:
        target[field] += record[field]
    if "calibration" in target:
        probability = record["predicted_probability_sum"]
        index = calibration_bin(probability)
        for field in ("count", "predicted_probability_sum", "observed_positive_count"):
            target["calibration"][index][field] += record[field]


def finish_binary(metric: dict) -> None:
    if not all(math.isfinite(metric[field]) for field in PROBABILITY_SUMS):
        raise InputContractError("evaluation: nonfinite probability metric sums")
    n = metric["count"]
    metric["log_loss"] = metric["log_loss_sum"] / n if n else None
    metric["brier_score"] = metric["brier_score_sum"] / n if n else None
    metric["predicted_minus_observed_pp"] = (
        100 * (metric["predicted_probability_sum"] - metric["observed_positive_count"]) / n
        if n else None
    )
    for bucket in metric.get("calibration", []):
        n = bucket["count"]
        bucket["predicted_rate"] = bucket["predicted_probability_sum"] / n if n else None
        bucket["observed_rate"] = bucket["observed_positive_count"] / n if n else None


def diagnostic_groups(attempt: dict, game_date: str, actor_evidence: dict) -> dict:
    """fixed, separate descriptors; missing context never becomes no recent action."""
    previous = attempt["previous_event"]
    recent = previous["status"] != "none"
    groups = {
        "original_type": attempt["shot_type"], "model_type": attempt["model_shot_type"],
        "recent_context": previous["status"],
        "recent_kind": previous["kind"] if recent else None,
        "recent_team": previous["owner_team_relation"] if recent else None,
        "recent_delay": previous["time_gap_seconds"] if recent else None,
        "home_away": attempt["home_away"], "role": attempt["role"],
        "calendar_month": game_date[:7],
        "sequence_index": None,
    }
    sequence = attempt.get("feature_facts", {}).get("sequence", {})
    index = sequence.get("values", {}).get("defender_sequence_index")
    if index is not None:
        groups["sequence_index"] = str(index) if index < 4 else "4+"
    for actor, evidence in actor_evidence.items():
        if "basis" in evidence:
            groups[f"actor_support:{actor}"] = evidence["basis"]
        else:
            for name, state in evidence.items():
                groups[f"actor_support:{actor}:{name}"] = state["basis"]
    return groups


def summarize_component(rows, game_dates: dict, *, outcome: str = "goal") -> dict:
    """main metrics use study inclusion; source and prediction counts stay separate."""
    statuses = ("predicted", "study_excluded", "not_applicable", "out_of_scope", "unavailable")
    domains = {
        "recent_context": ["recent", "none"], "model_type": TYPES + [None],
        "sequence_index": ["1", "2", "3", "4+", None], "role": ROLES,
        "calendar_month": sorted({date[:7] for date in game_dates.values()}),
        **{f"actor_support:{actor}": ["observed_in_state", "other_seasons_only", "unseen", None]
           for actor in ("shooter", "goalie")},
    }
    metrics = binary_metrics(outcome=outcome)
    omitted = binary_metrics(outcome=outcome)
    groups = {
        category: {value: dict(value=value, recognized_count=0, excluded_count=0,
                               non_applicable_count=0, study_excluded_count=0,
                               metrics=binary_metrics(outcome=outcome))
                   for value in values}
        for category, values in domains.items()
    }
    games = {
        gid: dict(game_id=gid, metrics=binary_metrics(outcome=outcome), counts_by_status={})
        for gid in game_dates
    }
    omitted_games = {
        gid: dict(game_id=gid, metrics=binary_metrics(outcome=outcome)) for gid in game_dates
    }
    accounting = {
        gid: dict(game_id=gid, game_date=date,
                  source_statuses=dict.fromkeys(SOURCE_STATUSES, 0),
                  study_inclusions=dict.fromkeys(STUDY_INCLUSIONS, 0),
                  source_applicable_count=0, included_count=0, excluded_count=0)
        for gid, date in game_dates.items()
    }
    counts, reasons = Counter(), Counter()
    source_reasons, study_reasons = Counter(), Counter()
    game_order = {gid: index for index, gid in enumerate(game_dates)}
    previous_key = (-1, -1)
    for row in rows:
        status, gid = row["status"], row["game_id"]
        if gid not in games or status not in statuses:
            raise InputContractError("component summary: foreign game or prediction disposition")
        source, study = row["source_status"], row["study_inclusion"]
        if source not in SOURCE_STATUSES or study not in STUDY_INCLUSIONS:
            raise InputContractError("component summary: unknown source or study disposition")
        index = row["source_index"]
        if type(index) is not int or index < 0 or (game_order[gid], index) <= previous_key:
            raise InputContractError("component summary: duplicate or reordered source key")
        previous_key = (game_order[gid], index)
        counts[status] += 1
        reasons.update(row["reasons"])
        source_reasons.update(row["source_reasons"])
        study_reasons.update(row["study_reasons"])
        game = games[gid]
        game["counts_by_status"][status] = game["counts_by_status"].get(status, 0) + 1
        evidence = accounting[gid]
        evidence["source_statuses"][source] += 1
        evidence["study_inclusions"][study] += 1
        evidence["source_applicable_count"] += source == "eligible" and row["applicable"]
        evidence["included_count"] += study == "included"
        evidence["excluded_count"] += study == "feature_unavailable"
        for category, value in row["diagnostic_groups"].items():
            group = groups.setdefault(category, {}).setdefault(
                value, dict(value=value, recognized_count=0, excluded_count=0,
                            non_applicable_count=0, study_excluded_count=0,
                            metrics=binary_metrics(outcome=outcome))
            )
            group["recognized_count"] += 1
            group["excluded_count"] += study == "source_excluded"
            group["non_applicable_count"] += study == "not_applicable"
            group["study_excluded_count"] += study == "feature_unavailable"
        if status != "predicted":
            continue
        record = binary_record(row["observed"], row["log_p"], row["log_not_p"])
        if study == "included":
            add_binary(metrics, record)
            add_binary(game["metrics"], record)
            for category, value in row["diagnostic_groups"].items():
                add_binary(groups[category][value]["metrics"], record)
        elif study == "feature_unavailable":
            add_binary(omitted, record)
            add_binary(omitted_games[gid]["metrics"], record)
        else:
            raise InputContractError("component summary: prediction outside source-applicable cohort")
    for game in games.values():
        game["counts_by_status"] = {status: game["counts_by_status"].get(status, 0) for status in statuses}
    for metric in (
        [metrics, omitted] + [game["metrics"] for game in games.values()] +
        [game["metrics"] for game in omitted_games.values()] +
        [group["metrics"] for category in groups.values() for group in category.values()]
    ):
        finish_binary(metric)
        metric["observed_rate"] = metric["observed_positive_count"] / metric["count"] if metric["count"] else None
    aggregate = dict(
        source_statuses={s: sum(v["source_statuses"][s] for v in accounting.values()) for s in SOURCE_STATUSES},
        study_inclusions={s: sum(v["study_inclusions"][s] for v in accounting.values()) for s in STUDY_INCLUSIONS},
        **{field: sum(v[field] for v in accounting.values())
           for field in ("source_applicable_count", "included_count", "excluded_count")},
        counts_by_source_reason=dict(source_reasons), counts_by_study_reason=dict(study_reasons),
        per_game=list(accounting.values()),
    )
    if aggregate["source_applicable_count"] != aggregate["included_count"] + aggregate["excluded_count"]:
        raise InputContractError("component summary: source-applicable cohort does not reconcile")
    if metrics["count"] != aggregate["included_count"]:
        raise InputContractError("component summary: included rows must all be predicted")
    return dict(
        metrics=metrics, per_game=list(games.values()),
        groups={name: list(values.values()) for name, values in groups.items()},
        counts_by_status={s: counts[s] for s in statuses}, counts_by_reason=dict(reasons),
        accounting=aggregate, omitted_baseline=dict(metrics=omitted, per_game=list(omitted_games.values())),
    )


def _new_metrics(full: bool, tip: bool = False) -> dict:
    result = {}
    for population, (outcome, predictors) in PROBABILITY_POPULATIONS.items():
        if tip and population != "unblocked_conversion":
            continue
        result[population] = {}
        for predictor in predictors:
            result[population][predictor] = binary_metrics(calibration=full, outcome=outcome)
    if full and not tip:
        result["observed_record_likelihood"] = {
            name: dict(count=0, negative_log_likelihood_sum=0.0)
            for name in ("all", "blocked", "unblocked")
        }
    return result


def _record_metrics(row: dict) -> dict:
    """validate once, then share additive probability evidence among summaries."""
    result = {}
    for population, (outcome, predictors) in PROBABILITY_POPULATIONS.items():
        if population == "unblocked_conversion" and row["blocked"]:
            continue
        positive = not row["blocked"] if outcome == "unblocked" else row["goal"]
        result[population] = {}
        for predictor in predictors:
            lp, ln = row[predictor]["log_p"], row[predictor]["log_not_p"]
            result[population][predictor] = binary_record(positive, lp, ln)
    observed = row["observed_log_likelihood"]
    if not math.isfinite(observed) or observed > 0:
        raise InputContractError("evaluation: invalid observed-record log likelihood")
    result["observed_record_likelihood"] = {
        name: dict(count=1, negative_log_likelihood_sum=-observed)
        for name in ("all", "blocked" if row["blocked"] else "unblocked")
    }
    return result


def _add_metrics(target: dict, record: dict) -> None:
    for population, predictors in record.items():
        if population not in target:
            continue
        for predictor, values in predictors.items():
            metric = target[population][predictor]
            if population == "observed_record_likelihood":
                for field, value in values.items():
                    metric[field] += value
            else:
                add_binary(metric, values)


def _finish_metrics(metrics: dict) -> None:
    for population, predictors in metrics.items():
        for metric in predictors.values():
            if population == "observed_record_likelihood":
                total = metric["negative_log_likelihood_sum"]
                if not math.isfinite(total):
                    raise InputContractError("evaluation: nonfinite likelihood sum")
                metric["mean_negative_log_likelihood"] = (
                    total / metric["count"] if metric["count"] else None
                )
                continue
            if not all(math.isfinite(metric[field]) for field in PROBABILITY_SUMS):
                raise InputContractError("evaluation: nonfinite probability metric sums")
            if "calibration" not in metric:
                continue
            n = metric["count"]
            metric["log_loss"] = metric["log_loss_sum"] / n if n else None
            metric["brier_score"] = metric["brier_score_sum"] / n if n else None
            for bucket in metric["calibration"]:
                n = bucket["count"]
                bucket["predicted_rate"] = (
                    bucket["predicted_probability_sum"] / n if n else None
                )
                bucket["observed_rate"] = (
                    bucket["observed_positive_count"] / n if n else None
                )


def _new_groups(categories: dict, full: bool) -> dict:
    return {
        category: [
            dict(
                descriptor,
                metrics=_new_metrics(
                    full, category in ("tip_distance", "tip_below_goal_line")
                ),
            )
            for descriptor in descriptors
        ]
        for category, descriptors in categories.items()
    }


def evaluate(model: dict, prepared: dict) -> dict:
    """evaluate saved predictors; selected games share exact subgroup domains."""
    from .chance import predict_attempt, prediction_context

    values = {"season": sorted({r["season"] for r in prepared["games"]}), **GROUP_DOMAINS}
    categories = {
        key: [dict(value=v) for v in domain] for key, domain in values.items()
    }
    categories["actor_evidence"] = [
        dict(stage=stage, actor=actor, value=value)
        for stage, actors in (("u", ("shooter",)), ("r", ("shooter", "goalie")))
        for actor in actors
        for value in ("observed_in_state", "other_seasons_only", "unseen")
    ]
    indices = {
        category: {
            (
                (d["stage"], d["actor"], d["value"])
                if category == "actor_evidence" else d["value"]
            ): i
            for i, d in enumerate(descriptors)
        }
        for category, descriptors in categories.items()
    }
    metrics = _new_metrics(full=True)
    groups = _new_groups(categories, full=True)
    games = {
        game_id: dict(
            game_id=game_id,
            metrics=_new_metrics(full=True),
            groups=_new_groups(categories, full=False),
        )
        for game_id in prepared["game_dates"]
    }
    context = prediction_context(model, feature_games=prepared["feature_games"], feature_player_games=prepared["feature_player_games"])
    for attempt in prepared["attempts"]:
        if attempt["status"] != "eligible":
            continue
        row = dict(attempt, **predict_attempt(model, attempt, context))
        record = _record_metrics(row)
        game = games[row["game_id"]]
        _add_metrics(metrics, record)
        _add_metrics(game["metrics"], record)
        memberships = [
            (category, row[category])
            for category in (
                "season", "role", "home_away", "shot_type", "model_shot_type",
                "season_basis",
            )
        ]
        memberships.extend(
            (category, row["context"][category])
            for category in ("score_bucket", "period", "minute_band")
        )
        memberships.append(("recent_context", row["previous_event"]["status"]))
        for stage, actors in row["actor_evidence"].items():
            for actor, evidence in actors.items():
                memberships.append(
                    ("actor_evidence", (stage, actor, evidence["basis"]))
                )
        if not row["blocked"] and row["shot_type"] in ("tip-in", "deflected"):
            distance = math.hypot(89 - row["attacking_x"], row["attacking_y"])
            band = (
                "0_10" if distance < 10 else "10_20" if distance < 20
                else "20_40" if distance < 40 else "40_plus"
            )
            memberships.extend(
                (
                    ("tip_distance", band),
                    ("tip_below_goal_line", row["attacking_x"] > 89),
                )
            )
        for category, value in memberships:
            index = indices[category][value]
            _add_metrics(groups[category][index]["metrics"], record)
            _add_metrics(game["groups"][category][index]["metrics"], record)
    _finish_metrics(metrics)
    for category in groups.values():
        for group in category:
            _finish_metrics(group["metrics"])
    for game in games.values():
        _finish_metrics(game["metrics"])
        for category in game["groups"].values():
            for group in category:
                _finish_metrics(group["metrics"])
    included = metrics["all_attempt_recorded_context"]["candidate_all"]
    return {
        "status": "evaluated" if included["count"] else "insufficient_evidence",
        "prediction_definitions": {
            "unblocked_conversion": "factual goal probability conditional on unblocked and its quantized recorded-origin proxy; six type-specific geometry benchmark",
            "all_attempt_recorded_context": "goal probability integrated over the origin prior; holds recorded type and preceding-play/scalar context; omits focal location, outcome and posterior; geometry-free benchmark",
            "marginal_unblocked": "unblocked probability integrated over the origin prior; same recorded conditioning and no focal location, outcome or posterior",
            "observed_record_likelihood": "fixed-grid joint observation law; compare only matching quantization, population and observation definitions",
            "measurement_limit": "reconciled type and eligibility are retrospective and potentially outcome-influenced; these are not demonstrated pre-release forecasts",
        },
        "metrics": metrics,
        "groups": groups,
        "inclusion": {
            "recognized_attempts": len(prepared["attempts"]),
            "model_included_attempts": included["count"],
            "recognized_goals": sum(r["goal"] for r in prepared["attempts"]),
            "model_included_goals": included["observed_positive_count"],
            "excluded_goals_by_reason": prepared["coverage"]["attempts"][
                "excluded_goals_by_reason"
            ],
        },
        "per_game": list(games.values()),
        "scientific_assessment": "not_performed",
    }
