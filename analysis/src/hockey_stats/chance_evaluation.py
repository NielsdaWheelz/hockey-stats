"""factual probability diagnostics from one native prediction pass."""

from collections import Counter
from itertools import zip_longest
import math

import numpy as np
from scipy.special import logsumexp

from .artifacts import agrees, require, rows
from .captures import InputContractError
from .chance import CONTEXT_CATEGORIES, ROLES, TYPES, component_prediction_context, predict_component
from .chance_cohort import SOURCE_STATUSES, STUDY_INCLUSIONS
from .chance_targets import DECOMPOSITION_QUANTITIES, component_target, recorded_on_net
from .paired_evaluation import calendar_blocks, paired_samples as ratio_samples, ratio_bootstrap


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


def summarize_component(rows, game_dates: dict, *, outcome: str = "goal",
                        group_categories: tuple[str, ...] | None = None) -> dict:
    """main metrics use study inclusion; source and prediction counts stay separate."""
    statuses = ("predicted", "study_excluded", "not_applicable", "out_of_scope", "unavailable")
    domains = {
        "recent_context": ["recent", "none"], "model_type": TYPES + [None],
        "sequence_index": ["1", "2", "3", "4+", None], "role": ROLES,
        "calendar_month": sorted({date[:7] for date in game_dates.values()}),
        **{f"actor_support:{actor}": ["observed_in_state", "other_seasons_only", "unseen", None]
           for actor in ("shooter", "goalie")},
    }
    if group_categories is not None:
        domains = {category: values for category, values in domains.items() if category in group_categories}
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
        descriptors = row["diagnostic_groups"]
        if group_categories is not None:
            descriptors = {category: value for category, value in descriptors.items() if category in group_categories}
        for category, value in descriptors.items():
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
            for category, value in descriptors.items():
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



COMPOSED_METRICS = ("on_net", "goal_given_on_net", "composed_goal")
COMPOSED_SOURCE_GROUPS = (
    "original_type", "model_type", "recent_context", "recent_kind", "recent_team",
    "recent_delay", "home_away", "role", "calendar_month", "sequence_index",
)
COMPOSED_ROW_FIELDS = {
    "schema_version", "game_id", "source_index", "event_id", "game_date", "season",
    "source_identity", "source_status", "source_reasons", "study_inclusion",
    "study_reasons", "status", "blocked", "goal", "on_net", "diagnostic_groups",
    "stages", "composed_goal",
}
COMPOSED_STAGE_FIELDS = {
    "metric_applicable", "observed", "log_p", "log_not_p", "season_basis",
    "state_season", "actor_evidence",
}

def compose_logs(q, g):
    """evaluate the same 1-q*g identity using its numerically resolved tail.

    log1p(-exp(log_p)) preserves the complement sign for p <= 1/2.
    the stage-complement sum retains the failure tail when p approaches one
    and native log_p can round to -0.0. neither branch clips probabilities.
    """
    binary_record(0, q["log_p"], q["log_not_p"])
    binary_record(0, g["log_p"], g["log_not_p"])
    log_p = q["log_p"] + g["log_p"]
    log_not_p = (math.log1p(-math.exp(log_p)) if log_p <= -math.log(2) else
                 float(np.logaddexp(q["log_not_p"], q["log_p"] + g["log_not_p"])))
    result = dict(log_p=log_p, log_not_p=log_not_p)
    binary_record(0, result["log_p"], result["log_not_p"])
    return result


def composed_rows(prepared, cohorts, components):
    from .chance_components import source_identities

    contexts = {quantity: component_prediction_context(
        component, feature_games=prepared["feature_games"],
        feature_player_games=prepared["feature_player_games"])
        for quantity, component in components.items()}
    sources = source_identities(prepared)
    for attempt, qmember, gmember in zip(prepared["attempts"], cohorts[DECOMPOSITION_QUANTITIES[0]]["rows"],
                                        cohorts[DECOMPOSITION_QUANTITIES[1]]["rows"], strict=True):
        gid = attempt["game_id"]
        included = qmember["study_inclusion"] == "included"
        row = dict(
            schema_version=1, game_id=gid, source_index=attempt["source_index"],
            event_id=attempt["event_id"], game_date=prepared["game_dates"][gid],
            season=attempt["season"], source_identity=sources[gid],
            **{field: qmember[field] for field in
               ("source_status", "source_reasons", "study_inclusion", "study_reasons")},
            status=("predicted" if included else "not_applicable"
                    if attempt["status"] == "eligible" else attempt["status"]),
            blocked=attempt["blocked"], goal=attempt["goal"], on_net=recorded_on_net(attempt),
            diagnostic_groups=diagnostic_groups(attempt, prepared["game_dates"][gid], {}),
            stages={}, composed_goal=None)
        for quantity, member in ((DECOMPOSITION_QUANTITIES[0], qmember), (DECOMPOSITION_QUANTITIES[1], gmember)):
            stage = dict(metric_applicable=False, observed=None, log_p=None, log_not_p=None,
                         season_basis=None, state_season=None, actor_evidence=None)
            if included:
                observed = component_target(attempt, quantity)
                stage.update(predict_component(components[quantity], attempt, contexts[quantity]),
                             metric_applicable=member["study_inclusion"] == "included",
                             observed=int(observed) if observed is not None else None)
            row["stages"][quantity] = stage
        if included:
            row["composed_goal"] = compose_logs(*(row["stages"][quantity] for quantity in DECOMPOSITION_QUANTITIES))
        yield row


def metric_rows(stream, metric):
    """an explicit binary scoring view; serialized source/composition rows stay intact."""
    require(metric in COMPOSED_METRICS, "unknown composed binary metric")
    for row in stream:
        if metric == "composed_goal":
            applicable = row["status"] == "predicted"
            predicted = row["composed_goal"]
            observed = int(row["goal"]) if applicable else None
            groups = row["diagnostic_groups"]
        else:
            quantity = DECOMPOSITION_QUANTITIES[0] if metric == "on_net" else DECOMPOSITION_QUANTITIES[1]
            stage = row["stages"][quantity]
            applicable = stage["metric_applicable"]
            predicted = stage if applicable else None
            observed = stage["observed"] if applicable else None
            groups = dict(row["diagnostic_groups"], **{
                f"actor_support:{actor}": stage["actor_evidence"][actor]["basis"]
                if stage["actor_evidence"] is not None else None for actor in ("shooter", "goalie")})
        status = ("predicted" if applicable else "not_applicable"
                  if row["source_status"] == "eligible" else row["source_status"])
        yield dict(
            game_id=row["game_id"], source_index=row["source_index"], status=status,
            reasons=row["source_reasons"], source_status=row["source_status"],
            source_reasons=row["source_reasons"],
            study_inclusion=("included" if applicable else "not_applicable"
                             if row["source_status"] == "eligible" else "source_excluded"),
            study_reasons=[], applicable=(row["on_net"] is True if metric == "goal_given_on_net"
                                         else not row["blocked"]), observed=observed,
            log_p=None if predicted is None else predicted["log_p"],
            log_not_p=None if predicted is None else predicted["log_not_p"],
            probability=None if predicted is None else math.exp(predicted["log_p"]),
            diagnostic_groups=groups)


def composed_summaries(stream_path, game_dates):
    result = {}
    for metric in COMPOSED_METRICS:
        kwargs = dict(outcome="on_net" if metric == "on_net" else "goal")
        if metric == "composed_goal":
            kwargs["group_categories"] = COMPOSED_SOURCE_GROUPS
        result[metric] = summarize_component(metric_rows(rows(stream_path), metric), game_dates, **kwargs)
    return result


def ratio_interval(numerators, denominators, seed, *, observed=None, blocks=None, samples=None):
    """retain historical attempt labels around the shared float ratio kernel."""
    result = ratio_bootstrap(numerators, denominators, seed, blocks=blocks, samples=samples)
    total = result.pop("denominator")
    result.pop("draws")
    result["count"] = int(total)
    if result["missing_reason"] is not None:
        result["missing_reason"] = "zero attempt denominator in at least one resampled draw"
    if observed is not None:
        observed, denominators = (np.asarray(value, dtype=np.float64)
                                  for value in (observed, denominators))
        require(observed.shape == denominators.shape and np.isfinite(observed).all()
                and np.all(observed >= 0) and np.all(observed <= denominators),
                "invalid observed label sums")
        all_one_label = bool(total and (observed.sum() == 0 or observed.sum() == total))
        result.update(observed_positive_count=int(observed.sum()), all_one_label=all_one_label,
            calibration_support_missing_reason=(result["missing_reason"] if result["undefined_draws"]
                else "all-one-label population cannot establish calibration support" if all_one_label else None))
    return result


def compare_paired_records(baseline, changed, pairs, *, resampling=True, samples=None):
    """compare bound binary numerical views; baseline owns paired groups and bins."""
    require(baseline["game_dates"] == changed["game_dates"], "paired selected game ledgers changed")
    require(baseline["metrics"]["outcome"] == changed["metrics"]["outcome"], "paired binary outcomes changed")
    outcome = baseline["metrics"]["outcome"]
    bins = [dict(lower=b["lower"], upper=b["upper"], upper_inclusive=b["upper_inclusive"],
                 baseline=binary_metrics(calibration=False, outcome=outcome),
                 changed=binary_metrics(calibration=False, outcome=outcome))
            for b in binary_metrics()["calibration"]]

    def paired_predictions():
        for before, after in pairs:
            require(all(before[field] == after[field] for field in
                        ("game_id", "source_index", "source_status", "source_reasons",
                         "study_inclusion", "study_reasons", "applicable")),
                    "paired numerical keys or scoring populations changed")
            if before["study_inclusion"] == "included":
                require(before["status"] == after["status"] == "predicted" and
                        before["observed"] == after["observed"], "paired binary labels changed")
                bucket = bins[calibration_bin(before["probability"])]
                for name, row in (("baseline", before), ("changed", after)):
                    add_binary(bucket[name], binary_record(row["observed"], row["log_p"], row["log_not_p"]))
            yield dict(after, diagnostic_groups=before["diagnostic_groups"])

    paired_summary = summarize_component(
        paired_predictions(), baseline["game_dates"], outcome=outcome,
        group_categories=tuple(baseline["groups"]))
    for field in ("count", "observed_positive_count"):
        require(paired_summary["metrics"][field] == baseline["metrics"][field],
                "paired quantity population mismatch")
    for key in PROBABILITY_SUMS:
        require(agrees(paired_summary["metrics"][key], changed["metrics"][key]),
                "stream and saved changed metrics disagree")
    if resampling and samples is None:
        samples = paired_samples(baseline["game_dates"])
    before_games = baseline["per_game"]
    after_games = paired_summary["per_game"]
    require([v["game_id"] for v in before_games] == [v["game_id"] for v in after_games],
            "paired game order mismatch")
    denominators = [v["metrics"]["count"] for v in before_games]
    require(denominators == [v["metrics"]["count"] for v in after_games],
            "paired per-game cohort denominators changed")
    results = {}
    if resampling:
        for name, field, scale in (("log_loss", "log_loss_sum", 1),
                                   ("brier_score", "brier_score_sum", 1),
                                   ("predicted_minus_observed_pp", "predicted_probability_sum", 100)):
            numerators = [scale * (a["metrics"][field] - b["metrics"][field])
                          for b, a in zip(before_games, after_games, strict=True)]
            results[name] = paired_additive(numerators, denominators, baseline["game_dates"], samples=samples)
    groups = {}
    for category, before_groups in baseline["groups"].items():
        after_groups = {g["value"]: g for g in paired_summary["groups"][category]}
        groups[category] = []
        for before in before_groups:
            after = after_groups[before["value"]]
            groups[category].append(dict(
                value=before["value"], baseline=before["metrics"], changed=after["metrics"],
                delta_log_loss=(after["metrics"]["log_loss"] - before["metrics"]["log_loss"])
                if before["metrics"]["count"] else None,
                delta_brier=(after["metrics"]["brier_score"] - before["metrics"]["brier_score"])
                if before["metrics"]["count"] else None,
                delta_predicted_minus_observed_pp=(after["metrics"]["predicted_minus_observed_pp"] -
                                                   before["metrics"]["predicted_minus_observed_pp"])
                if before["metrics"]["count"] else None,
            ))
    for bucket in bins:
        before, after = bucket["baseline"], bucket["changed"]
        finish_binary(before)
        finish_binary(after)
        bucket.update(
            delta_log_loss=after["log_loss"] - before["log_loss"] if before["count"] else None,
            delta_brier=after["brier_score"] - before["brier_score"] if before["count"] else None,
            delta_predicted_minus_observed_pp=(after["predicted_minus_observed_pp"] -
                                               before["predicted_minus_observed_pp"])
            if before["count"] else None,
        )
    for name, expected in (("baseline", baseline["metrics"]), ("changed", changed["metrics"])):
        require(all(agrees(sum(bucket[name][field] for bucket in bins), expected[field])
                    for field in PROBABILITY_SUMS), "paired calibration sums do not reconcile")
    return dict(delta=results, baseline_metrics=baseline["metrics"], changed_metrics=changed["metrics"],
                paired_groups=groups, paired_calibration=bins,
                group_definition="baseline component defines actor-support memberships for both predictors; own calibration bins remain separate",
                changed_own_groups=changed["groups"], counts_by_status=changed["counts_by_status"])


def paired_samples(game_dates, seed=3032026):
    """one selected draw matrix per unit; retain empty dates and zero-count games."""
    return ratio_samples(game_dates, seed)


def paired_additive(numerators, denominators, game_dates, *, samples=None):
    """resample an already paired additive contrast with pooled attempt weights."""
    require(len(numerators) == len(denominators) == len(game_dates),
            "paired additive sums differ from the selected game ledger")
    if samples is None:
        samples = paired_samples(game_dates)
    require(set(samples) == {"games", "calendar_7_day", "calendar_14_day"},
            "paired resampling methods differ")
    return {name: ratio_interval(numerators, denominators, 3032026, **unit)
            for name, unit in samples.items()}


def validate_composed_stream(path, prepared, cohorts, components):
    """rejoin original source rows and replay native stage predictions in order."""
    recognized, included, goals = 0, 0, 0
    for saved, expected in zip_longest(rows(path), composed_rows(prepared, cohorts, components)):
        require(saved is not None and expected is not None, "composed source stream length mismatch")
        validate_composed_pair(expected, saved, predictions=True)
        recognized += 1
        included += expected["status"] == "predicted"
        goals += expected["status"] == "predicted" and expected["goal"]
    return dict(recognized=recognized, included=included, goals=goals,
                source_labels_dispositions_order="verified", native_predictions="verified",
                prediction_absolute_tolerance=1e-12)


def validate_composed_pair(source, changed, *, predictions=False):
    """join full source identity and targets; optionally replay saved native logs."""
    for row in (source, changed):
        require(isinstance(row, dict) and set(row) == COMPOSED_ROW_FIELDS and
                type(row["schema_version"]) is int and row["schema_version"] == 1 and
                type(row["source_index"]) is int and row["source_index"] >= 0 and
                type(row["blocked"]) is bool and type(row["goal"]) is bool and
                (row["on_net"] is None or type(row["on_net"]) is bool) and
                isinstance(row["stages"], dict) and set(row["stages"]) == set(DECOMPOSITION_QUANTITIES),
                "invalid composed source row schema")
        for stage in row["stages"].values():
            require(isinstance(stage, dict) and set(stage) == COMPOSED_STAGE_FIELDS and
                    type(stage["metric_applicable"]) is bool and
                    (stage["observed"] is None or type(stage["observed"]) is int),
                    "invalid composed stage schema")
            if row["status"] == "predicted":
                binary_record(0, stage["log_p"], stage["log_not_p"])
            else:
                require(all(stage[field] is None for field in COMPOSED_STAGE_FIELDS - {"metric_applicable"})
                        and stage["metric_applicable"] is False, "stage prediction outside U must be null")
        if row["status"] == "predicted":
            q, g = (row["stages"][quantity] for quantity in DECOMPOSITION_QUANTITIES)
            require(row["study_inclusion"] == "included" and row["source_status"] == "eligible" and
                    not row["blocked"] and q["metric_applicable"] and
                    q["observed"] == int(row["on_net"]) and
                    g["metric_applicable"] == row["on_net"] and
                    g["observed"] == (int(row["goal"]) if row["on_net"] else None),
                    "composed U/O/U labels or scoring populations changed")
            product = compose_logs(q, g)
            require(isinstance(row["composed_goal"], dict) and set(row["composed_goal"]) == set(product) and
                    all(type(row["composed_goal"][key]) in (int, float) and
                        math.isfinite(row["composed_goal"][key]) and
                        abs(row["composed_goal"][key] - value) <= 1e-12
                        for key, value in product.items()), "composed probability arithmetic differs")
        else:
            require(row["composed_goal"] is None, "product prediction outside U must be null")
    for field in COMPOSED_ROW_FIELDS - {"stages", "composed_goal"}:
        require(source[field] == changed[field], "composed source keys/labels/dispositions/descriptors changed")
    for quantity in DECOMPOSITION_QUANTITIES:
        before, after = source["stages"][quantity], changed["stages"][quantity]
        for field in ("metric_applicable", "observed"):
            require(before[field] == after[field], "composed stage target population changed")
        if predictions:
            for field in COMPOSED_STAGE_FIELDS - {"log_p", "log_not_p"}:
                require(before[field] == after[field], "saved stage basis or actor support changed")
            if source["status"] == "predicted":
                require(all(abs(before[field] - after[field]) <= 1e-12 for field in ("log_p", "log_not_p")),
                        "saved stage differs from native source/design/coefficients")


def paired_composed_rows(left, right):
    """no intersections: every recognized source record must pair in order."""
    for before, after in zip_longest(rows(left), rows(right)):
        require(before is not None and after is not None, "composed stream length mismatch")
        validate_composed_pair(before, after)
        yield before, after
