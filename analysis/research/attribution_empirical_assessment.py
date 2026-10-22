"""04m's fixed paired empirical comparisons and bounded diagnostics.

inputs are aligned recorded game moments and training-only predictions. the
returned tables and native arrays are the complete saved assessment; rendering
never repeats these contractions or makes a scientific selection.
"""

import numpy as np

from hockey_stats.artifacts import require
from hockey_stats.attribution_prediction import empirical_paired_loss, empirical_residuals
from hockey_stats.paired_evaluation import paired_ratio_intervals, paired_samples


ARMS = ("borrowing", "independent", "context")
CONTRASTS = ("borrowing-independent", "borrowing-context", "independent-context")
SCHEMES = ("games", "calendar_7_day", "calendar_14_day")
GROUPS = ("current_training", "carried_only", "new_to_fit", "first_in_corpus_final")
VARIANTS = ("primary", "borrowing_probe", "independent_probe", "both_probes")


def direction(intervals):
    """all three valid intervals must have the same strict sign."""
    require(len(intervals) == 3, "empirical direction requires all three schemes")
    if all(value is not None and value[1] < 0 for value in intervals):
        return "supported_lower_loss"
    if all(value is not None and value[0] > 0 for value in intervals):
        return "supported_higher_loss"
    return "unresolved"


def _closure(values, label):
    error = float(np.max(np.abs(values[..., 0, :] - values[..., 1, :] + values[..., 2, :])))
    scale = max(1., float(np.max(np.abs(values))))
    require(error <= 1e-10 * scale, f"{label}: paired contrasts do not close")
    return error


def assess_games(games, predictions, p, regions, region_names, support, alternatives, probe_rows):
    """consume each game once; return saved scalar rows and native mean arrays.

    games carry moments plus game_id/date/partition/coverage/source_identity.
    support maps every source player id to an exclusive group and the separate
    first_in_corpus_final boolean. alternatives contain the two final bounded
    probe predictions. every prediction shares the source player universe.
    """
    p, regions = np.asarray(p), np.asarray(regions)
    require(set(predictions) == set(ARMS)
            and set(alternatives) == {"borrowing_probe", "independent_probe"}
            and regions.shape == (len(p), 12) and len(region_names) == 12
            and np.all(p > 0) and abs(float(p.sum()) - 1) <= 1e-12,
            "empirical arms, references or twelve-region axes differ")
    metrics = [("regional", "all", 12.)]
    metrics += [("regional", name, 1.) for name in region_names]
    metrics += [("native_inverse_share", "all", 1.)]
    normalizers = np.array([row[2] for row in metrics])
    variants = (
        predictions,
        dict(predictions, borrowing=alternatives["borrowing_probe"]),
        dict(predictions, independent=alternatives["independent_probe"]),
        dict(predictions, borrowing=alternatives["borrowing_probe"],
             independent=alternatives["independent_probe"]),
    )
    game_rows, numerators, hours, dates, assessment_ids = [], [], [], [], []
    observed, predicted, residual, native_ids = [], [], [], []
    zero_time_ids, player_hours, player_residuals, player_ids = [], None, None, None
    seen = set()
    for game in games:
        game_id = game["game_id"]
        require(game_id not in seen and game["partition"] in ("training", "assessment"),
                "empirical game inventory repeats or has an unknown partition")
        seen.add(game_id)
        exposure = float(np.sum(game["E"]))
        counts = float(np.sum(game["N"]))
        require(np.isfinite(exposure) and exposure >= 0 and np.isfinite(counts) and counts >= 0,
                "empirical game has invalid recorded exposure or counts")
        row = dict(game_id=game_id, game_date=game["date"], partition=game["partition"],
                   directed_hours=exposure, retained_recorded_unblocked_attempts=counts,
                   coverage=game["coverage"], reference_identity=game["source_identity"],
                   metric_normalizer=12., loss_denominator=12. * exposure,
                   reason="training game; excluded from empirical assessment"
                   if game["partition"] == "training" else
                   "zero retained directed exposure" if exposure == 0 else None)
        row.update({name + "_loss_numerator": None for name in CONTRASTS})
        game_rows.append(row)
        if game["partition"] == "training":
            continue
        if player_ids is None:
            player_ids = tuple(game["player_ids"])
            require(set(support) == set(player_ids), "empirical player support inventory differs")
            require(all(value["group"] in GROUPS[:3]
                        and type(value["first_in_corpus_final"]) is bool
                        for value in support.values()), "empirical support classification differs")
            player_hours = np.zeros(2 * len(player_ids))
            player_residuals = np.zeros((len(ARMS), 2 * len(player_ids), len(p)))
        require(tuple(game["player_ids"]) == player_ids, "empirical game player axes changed")
        game_values = np.zeros((len(VARIANTS), len(CONTRASTS), len(metrics)))
        cache = {}
        for vi, arms in enumerate(variants):
            for ci, (left, right) in enumerate((("borrowing", "independent"),
                                               ("borrowing", "context"),
                                               ("independent", "context"))):
                key = (id(arms[left]), id(arms[right]))
                if key not in cache:
                    regional = empirical_paired_loss(game, arms[left], arms[right], regions)
                    native = empirical_paired_loss(game, arms[left], arms[right], 1. / p)
                    require(regional["directed_hours"] == native["directed_hours"] == exposure,
                            "empirical paired losses use different exposure")
                    cache[key] = np.r_[regional["loss_numerator"], regional["component_numerators"],
                                       native["loss_numerator"]]
                game_values[vi, ci] = cache[key]
        _closure(game_values, f"game {game_id}")
        row.update({name + "_loss_numerator": float(game_values[0, index, 0])
                    for index, name in enumerate(CONTRASTS)})
        numerators.append(game_values)
        hours.append(exposure)
        dates.append(game["date"])
        assessment_ids.append(game_id)
        means = [empirical_residuals(game, predictions[arm]) for arm in ARMS]
        require(all(np.array_equal(means[0]["player_hours"], value["player_hours"])
                    for value in means), "empirical residual arms have different support")
        player_hours += means[0]["player_hours"]
        for ai, value in enumerate(means):
            player_residuals[ai] += value["player_residual_sum"]
        if exposure:
            native_ids.append(game_id)
            observed.append(means[0]["observed_sum"] / exposure)
            predicted.append([value["predicted_sum"] / exposure for value in means])
            residual.append([value["residual_sum"] / exposure for value in means])
        else:
            require(counts == 0 and not np.any(game_values), "zero-time game has recorded response or loss")
            zero_time_ids.append(game_id)
    require(bool(numerators) and sum(hours) > 0, "fixed empirical partition has no assessment exposure")
    values = np.array(numerators)
    hours = np.array(hours)
    pooled_closure = _closure(values.sum(axis=0), "pooled empirical assessment")
    # columns are variant, contrast, metric; one draw matrix serves them all.
    denominators = np.broadcast_to(hours[:, None, None, None] * normalizers[None, None, None, :],
                                   values.shape).reshape(len(hours), -1)
    schemes = paired_ratio_intervals(values.reshape(len(hours), -1), denominators, dates, 404130,
                                    samples=paired_samples(dates, 404130))
    require(tuple(schemes) == SCHEMES, "empirical bootstrap schemes changed")
    bootstrap_closure = {}
    for name, scheme in schemes.items():
        draws = scheme["draws"].reshape(2000, len(VARIANTS), len(CONTRASTS), len(metrics))
        valid = np.isfinite(draws).all(axis=(1, 2, 3))
        bootstrap_closure[name] = _closure(draws[valid], name + " bootstrap") if valid.any() else None
    estimates = values.sum(axis=0) / (hours.sum() * normalizers)
    directions, interval_rows = {}, []
    for vi, variant in enumerate(VARIANTS):
        for ci, contrast in enumerate(CONTRASTS):
            for mi, (metric, region, normalizer) in enumerate(metrics):
                index = np.ravel_multi_index((vi, ci, mi), values.shape[1:])
                intervals = []
                for name in SCHEMES:
                    scheme = schemes[name]
                    interval = scheme["interval"][index]
                    intervals.append(tuple(map(float, interval)) if np.isfinite(interval).all() else None)
                label = direction(intervals)
                directions[variant, contrast, metric, region] = label
                for name, interval in zip(SCHEMES, intervals, strict=True):
                    scheme = schemes[name]
                    interval_rows.append(dict(variant=variant, contrast=contrast, metric=metric, region=region,
                        loss_numerator=float(values[:, vi, ci, mi].sum()), directed_hours=float(hours.sum()),
                        metric_normalizer=normalizer, loss_denominator=float(normalizer * hours.sum()),
                        estimate=float(estimates[vi, ci, mi]), scheme=name,
                        lower=None if interval is None else interval[0], upper=None if interval is None else interval[1],
                        undefined_draws=int(scheme["undefined_draws"][index]), direction=label,
                        reason=scheme["missing_reason"][index]))
    comparison_rows = [{key: value for key, value in row.items() if key != "variant"}
                       for row in interval_rows if row["variant"] == "primary"]
    diagnostic_rows = []
    for month in sorted({value[:7] for value in dates}):
        selected = np.array([value.startswith(month) for value in dates])
        exposure = float(hours[selected].sum())
        for ci, contrast in enumerate(CONTRASTS):
            for mi, (metric, region, normalizer) in enumerate(metrics):
                numerator = float(values[selected, 0, ci, mi].sum())
                diagnostic_rows.append(dict(record_type="calendar_month", month=month, contrast=contrast,
                    metric=metric, region=region, game_count=int(selected.sum()), loss_numerator=numerator,
                    directed_hours=exposure, metric_normalizer=normalizer, loss_denominator=normalizer * exposure,
                    estimate=numerator / (normalizer * exposure) if exposure else None,
                    reason=None if exposure else "zero retained directed exposure"))
    native_observed, native_predicted, native_residual = map(np.array, (observed, predicted, residual))
    for index, game_id in enumerate(native_ids):
        for ai, arm in enumerate(ARMS):
            for ri, name in enumerate(region_names):
                diagnostic_rows.append(dict(record_type="game_mean_shape", game_id=game_id, arm=arm,
                    metric="regional", region=name, observed=float(native_observed[index] @ regions[:, ri]),
                    predicted=float(native_predicted[index, ai] @ regions[:, ri]),
                    signed_residual=float(native_residual[index, ai] @ regions[:, ri]), reason=None))
    group_metadata, group_native_residual = [], []
    n = len(player_ids)
    for role_index, role in enumerate(("offense", "defense")):
        role_hours = player_hours[role_index * n:(role_index + 1) * n]
        for group in GROUPS:
            selected = np.array([support[player]["first_in_corpus_final"] if group == GROUPS[-1]
                                 else support[player]["group"] == group for player in player_ids])
            selected &= role_hours > 0
            indices = np.flatnonzero(selected) + role_index * n
            exposure = float(role_hours[selected].sum())
            metadata = dict(role=role, support_group=group, member_count=int(selected.sum()),
                            on_ice_hours=exposure, participation_overlaps=True,
                            group_overlap="separate first-in-corpus flag overlaps exclusive support groups",
                            reason=None if exposure else "zero on-ice hours in assessment")
            if exposure:
                native = player_residuals[:, indices].sum(axis=1) / exposure
                metadata["native_array_index"] = len(group_native_residual)
                group_native_residual.append(native)
            else:
                native = None
                metadata["native_array_index"] = None
            group_metadata.append(metadata)
            for ai, arm in enumerate(ARMS):
                for ri, region in enumerate(region_names):
                    diagnostic_rows.append(dict(record_type="support_signed_residual_association", arm=arm,
                        metric="regional", region=region, **metadata,
                        signed_residual=None if native is None else float(native[ai] @ regions[:, ri])))
    numerical_rows = []
    for row in interval_rows:
        if row["variant"] != "primary":
            primary = estimates[0, CONTRASTS.index(row["contrast"]), metrics.index(
                (row["metric"], row["region"], row["metric_normalizer"]))]
            numerical_rows.append(dict(record_type="bounded_probe_rescore", **row,
                estimate_movement=float(row["estimate"] - primary),
                direction_stable=row["direction"] == directions["primary", row["contrast"], row["metric"], row["region"]]))
    diagnostic_rows.extend(numerical_rows)
    stable = all(row["direction_stable"] for row in numerical_rows
                 if row["metric"] == "regional" and row["region"] == "all")
    require(bool(probe_rows) and all(type(row["verified"]) is bool for row in probe_rows),
            "empirical numerical assessment lacks explicit bounded-probe verdicts")
    verified = stable and all(row["verified"] for row in probe_rows)
    numerical = dict(verified=verified, aggregate_direction_stable=stable, probe_rows=probe_rows,
                     per_game_closure_max_absolute=_closure(values, "all game empirical assessment"),
                     pooled_closure_max_absolute=pooled_closure,
                     bootstrap_closure_max_absolute=bootstrap_closure,
                     alternative_aggregate_rows=[row for row in numerical_rows
                                                if row["metric"] == "regional" and row["region"] == "all"])
    arrays = dict(observed_mean_shape=native_observed, predicted_mean_shape=native_predicted,
                  signed_mean_residual=native_residual,
                  support_signed_residual_association=np.array(group_native_residual))
    return dict(comparison_rows=comparison_rows, game_rows=game_rows, diagnostic_rows=diagnostic_rows,
                region_names=list(region_names), support_rows=group_metadata,
                assessment_game_ids=assessment_ids,
                coverage=dict(inventory_games=len(game_rows), training_games=sum(row["partition"] == "training" for row in game_rows),
                    assessment_games=len(assessment_ids), actual_assessment_fraction=len(assessment_ids) / len(game_rows),
                    assessment_directed_hours=float(hours.sum()),
                    assessment_recorded_unblocked_attempts=sum(row["retained_recorded_unblocked_attempts"] for row in game_rows
                                                              if row["partition"] == "assessment"),
                    training_directed_hours=sum(row["directed_hours"] for row in game_rows if row["partition"] == "training"),
                    training_recorded_unblocked_attempts=sum(row["retained_recorded_unblocked_attempts"] for row in game_rows
                                                            if row["partition"] == "training"),
                    assessment_zero_time_games=len(zero_time_ids)),
                native_axes=dict(game_ids=native_ids, unavailable_game_ids=zero_time_ids,
                    unavailable_reason="zero retained directed exposure", arms=list(ARMS),
                    support_rows=group_metadata, native_cell_count=len(p),
                    array_axes=dict(observed_mean_shape=["game", "native_cell"],
                        predicted_mean_shape=["game", "arm", "native_cell"],
                        signed_mean_residual=["game", "arm", "native_cell"],
                        support_signed_residual_association=["available_support_group", "arm", "native_cell"]),
                    coverage_in="assessment.game_rows, joined by game_id",
                    array_semantics="native recorded/predicted means and signed residuals; not player-effect maps"),
                numerical=numerical, numerical_status="verified" if verified else "unresolved",
                unresolved_reason=None if verified else
                "a bounded state probe failed or a final probe changed an aggregate conditional direction"), arrays
