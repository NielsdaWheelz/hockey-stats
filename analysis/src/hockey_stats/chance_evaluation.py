"""factual probability diagnostics on explicit held-out populations."""

import math

from .captures import InputContractError


def probability_summary(rows: list[dict], outcome: str) -> dict:
    bins = [
        {
            "lower": i / 20,
            "upper": (i + 1) / 20,
            "upper_inclusive": i == 19,
            "count": 0,
            "predicted_probability_sum": 0.0,
            "observed_positive_count": 0,
        }
        for i in range(20)
    ]
    loss = brier = predicted = 0.0
    positives = 0
    for row in rows:
        lp, ln, y = row["log_p"], row["log_not_p"], row["positive"]
        if not all(
            type(v) in (int, float) and math.isfinite(v) and v <= 0 for v in (lp, ln)
        ):
            raise InputContractError(
                "evaluation: nonfinite or positive log probability"
            )
        if type(y) not in (bool, int) or y not in (0, 1):
            raise InputContractError("evaluation: expected binary observed label")
        if abs(math.exp(lp) + math.exp(ln) - 1) > 1e-10:
            raise InputContractError(
                "evaluation: probability and complement do not sum to one"
            )
        p = math.exp(lp)
        loss -= lp if y else ln
        brier += (p - y) ** 2
        predicted += p
        positives += y
        bucket = bins[next((i for i in range(19) if p < (i + 1) / 20), 19)]
        bucket["count"] += 1
        bucket["predicted_probability_sum"] += p
        bucket["observed_positive_count"] += y
    for bucket in bins:
        n = bucket["count"]
        bucket["predicted_rate"] = (
            bucket["predicted_probability_sum"] / n if n else None
        )
        bucket["observed_rate"] = bucket["observed_positive_count"] / n if n else None
    n = len(rows)
    if not all(math.isfinite(v) for v in (loss, brier, predicted)):
        raise InputContractError("evaluation: nonfinite probability metric sums")
    return {
        "outcome": outcome,
        "count": n,
        "observed_positive_count": positives,
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
            raise InputContractError(
                "evaluation: invalid observed-record log likelihood"
            )
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
                [dict(r[name], positive=r["goal"]) for r in rows if not r["blocked"]],
                "goal",
            )
            for name in ("candidate_r", "benchmark_r")
        },
        "all_attempt_recorded_context": {
            name: probability_summary(
                [dict(r[name], positive=r["goal"]) for r in rows], "goal"
            )
            for name in ("candidate_all", "benchmark_all")
        },
        "marginal_unblocked": {
            "candidate_unblocked": probability_summary(
                [
                    dict(r["candidate_unblocked"], positive=not r["blocked"])
                    for r in rows
                ],
                "unblocked",
            )
        },
        "observed_record_likelihood": likelihood_summary(rows),
    }


def evaluate(model: dict, prepared: dict) -> dict:
    """use saved predictors and reference; assessment never updates a model."""
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
        "score_bucket": [
            "trailing_2_plus",
            "trailing_1",
            "tied",
            "leading_1",
            "leading_2_plus",
        ],
        "role": ["F", "D", "unknown"],
        "home_away": ["home", "away"],
        "shot_type": [
            "wrist",
            "snap",
            "slap",
            "backhand",
            "tip-in",
            "deflected",
            "wrap-around",
            "poke",
            "bat",
            "between-legs",
            "cradle",
            None,
        ],
        "model_shot_type": ["wrist", "snap", "slap", "backhand", "tip", "other", None],
        "recent_context": ["recent", "none"],
        "season_basis": ["fitted", "unobserved", "carried_forward"],
    }
    groups = {}
    for key, values in categories.items():
        groups[key] = []
        for value in values:
            if key == "score_bucket":
                selected = [r for r in rows if r["context"][key] == value]
            elif key == "recent_context":
                selected = [r for r in rows if r["previous_event"]["status"] == value]
            else:
                selected = [r for r in rows if r[key] == value]
            groups[key].append({"value": value, "metrics": summarize(selected)})
    groups["actor_evidence"] = []
    for stage, actors in (("u", ("shooter",)), ("r", ("shooter", "goalie"))):
        for actor in actors:
            for value in ("observed_in_state", "other_seasons_only", "unseen"):
                selected = [
                    r
                    for r in rows
                    if r["actor_evidence"][stage][actor]["basis"] == value
                ]
                groups["actor_evidence"].append(
                    {
                        "stage": stage,
                        "actor": actor,
                        "value": value,
                        "metrics": summarize(selected),
                    }
                )
    return {
        "status": "evaluated" if rows else "insufficient_evidence",
        "prediction_definitions": {
            "unblocked_conversion": "factual goal probability conditional on unblocked and its quantized recorded-origin proxy; six type-specific geometry benchmark",
            "all_attempt_recorded_context": "goal probability integrated over the origin prior; holds recorded type and preceding-play/scalar context; omits focal location, outcome and posterior; geometry-free benchmark",
            "marginal_unblocked": "unblocked probability integrated over the origin prior; same recorded conditioning and no focal location, outcome or posterior",
            "observed_record_likelihood": "fixed-grid joint observation law; compare only matching quantization, population and observation definitions",
            "measurement_limit": "reconciled type and eligibility are retrospective and potentially outcome-influenced; these are not demonstrated pre-release forecasts",
        },
        "metrics": summarize(rows),
        "groups": groups,
        "inclusion": {
            "recognized_attempts": len(prepared["attempts"]),
            "model_included_attempts": len(rows),
            "recognized_goals": sum(r["goal"] for r in prepared["attempts"]),
            "model_included_goals": sum(r["goal"] for r in rows),
            "excluded_goals_by_reason": prepared["coverage"]["attempts"][
                "excluded_goals_by_reason"
            ],
        },
        "per_game": [
            {
                "game_id": game_id,
                "metrics": summarize([r for r in rows if r["game_id"] == game_id]),
            }
            for game_id in prepared["game_dates"]
        ],
        "scientific_assessment": "not_performed",
    }
