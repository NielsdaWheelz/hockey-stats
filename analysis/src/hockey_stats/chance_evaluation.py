"""probability scores and explicit held-out populations; no scientific acceptance."""

import math

from .captures import InputContractError


def probability_summary(rows: list[dict]) -> dict:
    bins = [
        {
            "lower": i / 20,
            "upper": (i + 1) / 20,
            "upper_inclusive": i == 19,
            "count": 0,
            "predicted_probability_sum": 0.0,
            "goals": 0,
        }
        for i in range(20)
    ]
    loss = brier = predicted = 0.0
    goals = 0
    for row in rows:
        lp, ln, y = row["log_p"], row["log_not_p"], row["goal"]
        if not all(math.isfinite(v) and v <= 0 for v in (lp, ln)):
            raise InputContractError("evaluation: nonfinite or positive log probability")
        if abs(math.exp(lp) + math.exp(ln) - 1) > 1e-10:
            raise InputContractError("evaluation: probability and complement do not sum to one")
        p = math.exp(lp)
        loss -= lp if y else ln
        brier += (p - y) ** 2
        predicted += p
        goals += y
        bucket = bins[next((i for i in range(19) if p < (i + 1) / 20), 19)]
        bucket["count"] += 1
        bucket["predicted_probability_sum"] += p
        bucket["goals"] += y
    for bucket in bins:
        n = bucket["count"]
        bucket["predicted_rate"] = bucket["predicted_probability_sum"] / n if n else None
        bucket["observed_rate"] = bucket["goals"] / n if n else None
    n = len(rows)
    if not all(math.isfinite(v) for v in (loss, brier, predicted)):
        raise InputContractError("evaluation: nonfinite probability metric sums")
    return {
        "count": n,
        "goals": goals,
        "log_loss_sum": loss,
        "brier_score_sum": brier,
        "predicted_probability_sum": predicted,
        "log_loss": loss / n if n else None,
        "brier_score": brier / n if n else None,
        "calibration": bins,
    }


def likelihood_summary(rows: list[dict]) -> dict:
    result = {}
    for name, selected in (
        ("all", rows),
        ("blocked", [r for r in rows if r["blocked"]]),
        ("unblocked", [r for r in rows if not r["blocked"]]),
    ):
        values = [r["observed_log_likelihood"] for r in selected]
        if any(not math.isfinite(v) or v > 0 for v in values):
            raise InputContractError("evaluation: invalid observed-record log likelihood")
        total = -math.fsum(values)
        if not math.isfinite(total):
            raise InputContractError("evaluation: nonfinite likelihood sum")
        result[name] = {
            "count": len(values),
            "negative_log_likelihood_sum": total,
            "mean_negative_log_likelihood": total / len(values) if values else None,
        }
    return result


def summarize(rows: list[dict]) -> dict:
    return {
        "unblocked_conversion": {
            name: probability_summary(
                [dict(r[name], goal=r["goal"]) for r in rows if not r["blocked"]]
            )
            for name in ("candidate_r", "benchmark_r")
        },
        "all_attempt_outcome_blind": {
            name: probability_summary([dict(r[name], goal=r["goal"]) for r in rows])
            for name in ("candidate_all", "benchmark_all")
        },
        "observed_record_likelihood": likelihood_summary(rows),
    }


def evaluate(model: dict, prepared: dict) -> dict:
    """consume the same fitted predictors for candidate and benchmark comparisons."""
    from .chance import predict_attempt, prediction_context

    context = prediction_context(model)
    rows = []
    for attempt in prepared["attempts"]:
        if attempt["status"] == "eligible":
            prediction = predict_attempt(model, attempt, context)
            prediction.pop("origin_weights", None)
            rows.append(dict(attempt, **prediction))
    categories = {
        "season": sorted({r["season"] for r in prepared["games"]}),
        "score": ["trailing", "tied", "leading"],
        "role": ["F", "D", "unknown"],
        "home_away": ["home", "away"],
        "shot_type": sorted(
            {r["shot_type"] for r in prepared["attempts"] if r["shot_type"] is not None}
        )
        + [None],
    }
    groups = {}
    for key, values in categories.items():
        groups[key] = []
        for value in values:
            selected = [r for r in rows if r[key] == value]
            if key == "shot_type":
                selected = [r for r in selected if not r["blocked"]]
            groups[key].append({"value": value, "metrics": summarize(selected)})
    # each stage has its own evidence population; a shooter seen only in blocks
    # remains unseen in conversion, even when seen in block avoidance.
    groups["actor_evidence"] = []
    for stage, actors in (("u", ("shooter",)), ("r", ("shooter", "goalie"))):
        for actor in actors:
            for value in ("seen", "unseen"):
                selected = [r for r in rows if r["actor_evidence"][stage][actor]["basis"] == value]
                groups["actor_evidence"].append(
                    {"stage": stage, "actor": actor, "value": value, "metrics": summarize(selected)}
                )
    return {
        "status": "evaluated" if rows else "insufficient_evidence",
        "prediction_definitions": {
            "unblocked_conversion": "factual r conditional on recorded quantized origin; unblocked attempts only; distance/angle benchmark",
            "all_attempt_outcome_blind": "sum of origin prior times u times r; excludes current location, block outcome and inferred origin; score/role benchmark",
            "observed_record_likelihood": "fixed-grid joint observation law; blocked and unblocked contributions; different quantizations are not comparable",
        },
        "metrics": summarize(rows),
        "groups": groups,
        "per_game": [
            {"game_id": game_id, "metrics": summarize([r for r in rows if r["game_id"] == game_id])}
            for game_id in prepared["game_dates"]
        ],
        "scientific_assessment": "not_performed",
    }
