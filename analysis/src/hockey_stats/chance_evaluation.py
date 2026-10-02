"""factual probability diagnostics from one native prediction pass."""

import math

from .captures import InputContractError
from .chance import CONTEXT_CATEGORIES, ROLES, TYPES


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


def add_binary(target: dict, record: dict) -> None:
    for field in PROBABILITY_SUMS:
        target[field] += record[field]
    if "calibration" in target:
        probability = record["predicted_probability_sum"]
        index = next((i for i in range(19) if probability < (i + 1) / 20), 19)
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
    }
    for actor, evidence in actor_evidence.items():
        if "basis" in evidence:
            groups[f"actor_support:{actor}"] = evidence["basis"]
        else:
            for name, state in evidence.items():
                groups[f"actor_support:{actor}:{name}"] = state["basis"]
    return groups


def summarize_component(rows, game_dates: dict, *, outcome: str = "goal") -> dict:
    """consume quantity-specific prediction rows, retaining every selected game."""
    from collections import Counter

    metrics = binary_metrics(outcome=outcome)
    groups = {}
    games = {
        gid: dict(game_id=gid, metrics=binary_metrics(outcome=outcome), counts_by_status={})
        for gid in game_dates
    }
    counts, reasons = Counter(), Counter()
    for row in rows:
        status, gid = row["status"], row["game_id"]
        counts[status] += 1
        reasons.update(row["reasons"])
        game = games[gid]
        game["counts_by_status"][status] = game["counts_by_status"].get(status, 0) + 1
        for category, value in row["diagnostic_groups"].items():
            group = groups.setdefault(category, {}).setdefault(
                value, dict(value=value, recognized_count=0, excluded_count=0,
                            non_applicable_count=0, metrics=binary_metrics(outcome=outcome))
            )
            group["recognized_count"] += 1
            group["excluded_count"] += status in ("out_of_scope", "unavailable")
            group["non_applicable_count"] += status == "not_applicable"
        if status != "predicted":
            continue
        record = binary_record(row["observed"], row["log_p"], row["log_not_p"])
        add_binary(metrics, record)
        add_binary(game["metrics"], record)
        for category, value in row["diagnostic_groups"].items():
            add_binary(groups[category][value]["metrics"], record)
    finish_binary(metrics)
    for game in games.values():
        finish_binary(game["metrics"])
    for category in groups.values():
        for group in category.values():
            finish_binary(group["metrics"])
    return dict(
        metrics=metrics, per_game=list(games.values()),
        groups={name: list(values.values()) for name, values in groups.items()},
        counts_by_status={s: counts[s] for s in ("predicted", "not_applicable", "out_of_scope", "unavailable")},
        counts_by_reason=dict(reasons),
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
    context = prediction_context(model)
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
