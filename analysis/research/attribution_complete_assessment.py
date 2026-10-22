"""04n's fixed complete-rate comparisons; no fitting or source decoding."""

import numpy as np

from hockey_stats.artifacts import require
from hockey_stats.attribution_prediction import (
    complete_paired_decomposition,
    empirical_paired_loss,
    empirical_residuals,
)
from hockey_stats.paired_evaluation import paired_ratio_intervals, paired_samples

ARMS = ("borrowing", "independent", "context")
CONTRASTS = ("borrowing-independent", "borrowing-context", "independent-context")
SCHEMES = ("games", "calendar_7_day", "calendar_14_day")
GROUPS = ("current_training", "carried_only", "new_to_fit", "first_in_corpus_final")


def direction(intervals):
    require(len(intervals) == 3, "complete direction requires all three schemes")
    if all(value is not None and value[1] < 0 for value in intervals):
        return "supported_lower_loss"
    if all(value is not None and value[0] > 0 for value in intervals):
        return "supported_higher_loss"
    return "unresolved"


def _close(left, right, label):
    error = float(np.max(np.abs(left - right)))
    scale = max(1.0, float(np.max(np.abs(left))), float(np.max(np.abs(right))))
    require(error <= 1e-9 * scale, label + " does not close")
    return error


def _metrics(names):
    return (
        [
            ("regional", "all", component, 12.0)
            for component in ("complete", "weighted_volume", "shape", "interaction")
        ]
        + [("regional", name, "complete", 1.0) for name in names]
        + [
            ("native_inverse_share", "all", component, 1.0)
            for component in ("complete", "weighted_volume", "shape", "interaction")
        ]
        + [("volume", "all", "volume", 1.0)]
    )


def _values(game, left, right, regions):
    parts = complete_paired_decomposition(game, left, right, regions)
    return np.r_[
        [parts["regional"][key] for key in ("complete", "weighted_volume", "shape", "interaction")],
        parts["regional"]["region_numerators"],
        [
            parts["native_inverse_share"][key]
            for key in ("complete", "weighted_volume", "shape", "interaction")
        ],
        parts["volume"],
    ]


def _interval_rows(values, hours, dates, metrics, variants, samples, comparison, contrasts):
    normalizers = np.array([metric[3] for metric in metrics])
    denominator = np.broadcast_to(hours[:, None, None, None] * normalizers, values.shape)
    schemes = paired_ratio_intervals(
        values.reshape(len(hours), -1), denominator.reshape(len(hours), -1), dates, 404130, samples=samples
    )
    rows, directions = [], {}
    estimates = values.sum(axis=0) / (hours.sum() * normalizers)
    for vi, variant in enumerate(variants):
        for ci, contrast in enumerate(contrasts):
            for mi, (metric, region, component, normalizer) in enumerate(metrics):
                index = np.ravel_multi_index((vi, ci, mi), values.shape[1:])
                intervals = [schemes[scheme]["interval"][index] for scheme in SCHEMES]
                intervals = [value.tolist() if np.isfinite(value).all() else None for value in intervals]
                label = direction(intervals)
                directions[variant, contrast, metric, region, component] = label
                for scheme, interval in zip(SCHEMES, intervals, strict=True):
                    rows.append(
                        dict(
                            comparison=comparison,
                            variant=variant,
                            contrast=contrast,
                            metric=metric,
                            region=region,
                            component=component,
                            loss_numerator=float(values[:, vi, ci, mi].sum()),
                            directed_hours=float(hours.sum()),
                            metric_normalizer=normalizer,
                            loss_denominator=float(normalizer * hours.sum()),
                            estimate=float(estimates[vi, ci, mi]),
                            scheme=scheme,
                            lower=None if interval is None else interval[0],
                            upper=None if interval is None else interval[1],
                            undefined_draws=int(schemes[scheme]["undefined_draws"][index]),
                            direction=label,
                            reason=schemes[scheme]["missing_reason"][index],
                        )
                    )
    return rows, directions, schemes


def assess_games(
    games, predictions, p, regions, region_names, support, alternatives, probe_rows, *, source_predictions
):
    """score sixteen final-component combinations and four frozen-source combinations.

    alternatives maps variant names to the three complete-rate arms, including
    primary. source_predictions similarly maps four variants to corrected/original
    borrowing shape predictions. every variant shares training and held-out axes.
    """
    p, regions = np.asarray(p), np.asarray(regions)
    require(
        set(predictions) == set(ARMS)
        and len(alternatives) == 16
        and "primary" in alternatives
        and len(source_predictions) == 4
        and "primary" in source_predictions
        and regions.shape == (len(p), 12)
        and len(region_names) == 12
        and np.all(p > 0)
        and abs(float(p.sum()) - 1.0) <= 1e-12,
        "complete arms, sixteen/four variants or twelve-region axes differ",
    )
    require(
        all(set(value) == set(ARMS) for value in alternatives.values())
        and all(set(value) == {"corrected", "original"} for value in source_predictions.values()),
        "complete or source-only arm inventory differs",
    )
    variants = ("primary", *(name for name in alternatives if name != "primary"))
    source_variants = ("primary", *(name for name in source_predictions if name != "primary"))
    metrics = _metrics(region_names)
    source_metrics = [("regional", "all", "shape", 12.0)]
    source_metrics += [("regional", name, "shape", 1.0) for name in region_names]
    source_metrics += [("native_inverse_share", "all", "shape", 1.0)]
    game_rows, dates, hours, all_values, source_values, ids = [], [], [], [], [], []
    diagnostics, means, observed_means = [], [], []
    player_ids, player_hours, player_residuals = None, None, None
    seen = set()
    for game in games:
        game_id = game["game_id"]
        require(
            game_id not in seen and game["partition"] in ("training", "assessment"),
            "invalid complete game inventory",
        )
        seen.add(game_id)
        exposure, counts = float(np.sum(game["E"])), float(np.sum(game["N"]))
        require(
            np.isfinite(exposure) and exposure >= 0 and np.isfinite(counts) and counts >= 0,
            "invalid complete assessment time/counts",
        )
        row = dict(
            game_id=game_id,
            game_date=game["date"],
            partition=game["partition"],
            directed_hours=exposure,
            retained_recorded_unblocked_attempts=counts,
            coverage=game["coverage"],
            reference_identity=game["source_identity"],
            metric_normalizer=12.0,
            loss_denominator=12.0 * exposure,
            reason=(
                "training game; excluded from assessment"
                if game["partition"] == "training"
                else "zero retained directed exposure" if not exposure else None
            ),
        )
        game_rows.append(row)
        if game["partition"] == "training":
            continue
        if player_ids is None:
            player_ids = tuple(game["player_ids"])
            require(set(support) == set(player_ids), "complete support ids differ")
            require(
                all(
                    value["group"] in GROUPS[:3] and type(value["first_in_corpus_final"]) is bool
                    for value in support.values()
                ),
                "complete support groups differ",
            )
            player_hours = np.zeros(2 * len(player_ids))
            player_residuals = np.zeros((3, 2 * len(player_ids), len(p)))
        require(tuple(game["player_ids"]) == player_ids, "complete game player axes changed")
        values, cache = [], {}
        for variant in variants:
            arms = alternatives[variant]
            contrasts = []
            for left, right in (
                ("borrowing", "independent"),
                ("borrowing", "context"),
                ("independent", "context"),
            ):
                key = id(arms[left]), id(arms[right])
                if key not in cache:
                    cache[key] = _values(game, arms[left], arms[right], regions)
                contrasts.append(cache[key])
            values.append(contrasts)
        values = np.array(values)
        _close(values[:, 0], values[:, 1] - values[:, 2], f"game {game_id} paired")
        _close(values[:, :, 0], values[:, :, 1:4].sum(axis=2), f"game {game_id} regional decomposition")
        _close(values[:, :, 16], values[:, :, 17:20].sum(axis=2), f"game {game_id} native decomposition")
        source = []
        for variant in source_variants:
            arms = source_predictions[variant]
            regional = empirical_paired_loss(game, arms["corrected"], arms["original"], regions)
            native = empirical_paired_loss(game, arms["corrected"], arms["original"], 1.0 / p)
            source.append(
                [[regional["loss_numerator"], *regional["component_numerators"], native["loss_numerator"]]]
            )
        source_values.append(source)
        for ci, contrast in enumerate(CONTRASTS):
            for mi, (metric, region, component, _) in enumerate(metrics):
                row[f"{contrast}:{metric}:{region}:{component}:loss_numerator"] = float(values[0, ci, mi])
        all_values.append(values)
        hours.append(exposure)
        dates.append(game["date"])
        ids.append(game_id)
        residuals = [empirical_residuals(game, predictions[arm], response="complete") for arm in ARMS]
        player_hours += residuals[0]["player_hours"]
        observed_means.append(residuals[0]["observed_sum"] / exposure if exposure else np.zeros(len(p)))
        predicted = []
        for ai, arm in enumerate(ARMS):
            predicted.append(residuals[ai]["predicted_sum"] / exposure if exposure else np.zeros(len(p)))
            player_residuals[ai] += residuals[ai]["player_residual_sum"]
        means.append(predicted)
        if not exposure:
            require(
                counts == 0 and not np.any(values) and not np.any(source),
                "zero-time game contains response or loss",
            )
    require(bool(hours) and sum(hours) > 0, "complete assessment has zero total exposure")
    values, hours, source_values = np.array(all_values), np.array(hours), np.array(source_values)
    samples = paired_samples(dates, 404130)
    interval_rows, directions, schemes = _interval_rows(
        values, hours, dates, metrics, variants, samples, "main", CONTRASTS
    )
    source_rows, source_directions, source_schemes = _interval_rows(
        source_values,
        hours,
        dates,
        source_metrics,
        source_variants,
        samples,
        "source_only",
        ("corrected-original",),
    )
    closure = {}
    for scheme, result in schemes.items():
        draws = result["draws"].reshape(2000, *values.shape[1:])
        valid = np.isfinite(draws).all(axis=(1, 2, 3))
        closure[scheme] = dict(paired=None, regional_decomposition=None, native_decomposition=None)
        if valid.any():
            selected = draws[valid]
            closure[scheme] = dict(
                paired=_close(
                    selected[:, :, 0], selected[:, :, 1] - selected[:, :, 2], scheme + " paired draws"
                ),
                regional_decomposition=_close(
                    selected[:, :, :, 0], selected[:, :, :, 1:4].sum(axis=3), scheme + " regional draws"
                ),
                native_decomposition=_close(
                    selected[:, :, :, 16], selected[:, :, :, 17:20].sum(axis=3), scheme + " native draws"
                ),
            )
    stable = all(
        directions[variant, contrast, "regional", "all", "complete"]
        == directions["primary", contrast, "regional", "all", "complete"]
        for variant in variants
        for contrast in CONTRASTS
    )
    source_stable = all(
        source_directions[variant, "corrected-original", "regional", "all", "shape"]
        == source_directions["primary", "corrected-original", "regional", "all", "shape"]
        for variant in source_variants
    )
    require(
        len(probe_rows) == 13 and all(type(row["verified"]) is bool for row in probe_rows),
        "complete assessment requires twelve selected-state probes and frozen-control probe",
    )
    verified = stable and source_stable and all(row["verified"] for row in probe_rows)
    for row in interval_rows + source_rows:
        if row["variant"] != "primary":
            lookup = directions if row["comparison"] == "main" else source_directions
            primary = lookup["primary", row["contrast"], row["metric"], row["region"], row["component"]]
            diagnostics.append(
                dict(record_type="bounded_probe_rescore", **row, direction_stable=row["direction"] == primary)
            )
    for month in sorted({date[:7] for date in dates}):
        selected = np.array([date.startswith(month) for date in dates])
        exposure = float(hours[selected].sum())
        for ci, contrast in enumerate(CONTRASTS):
            for mi, (metric, region, component, normalizer) in enumerate(metrics):
                numerator = float(values[selected, 0, ci, mi].sum())
                diagnostics.append(
                    dict(
                        record_type="calendar_month",
                        month=month,
                        contrast=contrast,
                        metric=metric,
                        region=region,
                        component=component,
                        game_count=int(selected.sum()),
                        loss_numerator=numerator,
                        directed_hours=exposure,
                        metric_normalizer=normalizer,
                        loss_denominator=normalizer * exposure,
                        estimate=numerator / (normalizer * exposure) if exposure else None,
                        reason=None if exposure else "zero directed exposure",
                    )
                )
    observed_means, means = np.array(observed_means), np.array(means)
    for gi, game_id in enumerate(ids):
        for ai, arm in enumerate(ARMS):
            for ri, region in enumerate(region_names):
                diagnostics.append(
                    dict(
                        record_type="game_mean_complete",
                        game_id=game_id,
                        game_date=dates[gi],
                        arm=arm,
                        region=region,
                        directed_hours=float(hours[gi]),
                        observed=float(observed_means[gi] @ regions[:, ri]) if hours[gi] else None,
                        predicted=float(means[gi, ai] @ regions[:, ri]) if hours[gi] else None,
                        signed_residual=(
                            float((observed_means[gi] - means[gi, ai]) @ regions[:, ri])
                            if hours[gi]
                            else None
                        ),
                        reason=None if hours[gi] else "zero directed exposure",
                    )
                )
    support_rows = []
    n = len(player_ids)
    for role_index, role in enumerate(("offense", "defense")):
        for group in GROUPS:
            selected = np.array(
                [
                    (
                        support[player]["first_in_corpus_final"]
                        if group == GROUPS[-1]
                        else support[player]["group"] == group
                    )
                    for player in player_ids
                ]
            )
            indices = (
                np.flatnonzero(selected & (player_hours[role_index * n : (role_index + 1) * n] > 0))
                + role_index * n
            )
            exposure = float(player_hours[indices].sum())
            metadata = dict(
                role=role,
                support_group=group,
                member_count=len(indices),
                on_ice_hours=exposure,
                participation_overlaps=True,
                reason=None if exposure else "zero on-ice hours",
            )
            support_rows.append(metadata)
            for ai, arm in enumerate(ARMS):
                for ri, region in enumerate(region_names):
                    diagnostics.append(
                        dict(
                            record_type="support_signed_residual_association",
                            arm=arm,
                            region=region,
                            **metadata,
                            signed_residual=(
                                float(player_residuals[ai, indices].sum(axis=0) @ regions[:, ri] / exposure)
                                if exposure
                                else None
                            ),
                        )
                    )
    numerical = dict(
        verified=verified,
        aggregate_direction_stable=stable,
        source_direction_stable=source_stable,
        primary_probe_combinations=len(variants),
        source_probe_combinations=len(source_variants),
        probe_rows=probe_rows,
        per_game_closure_max_absolute=_close(values[:, :, 0], values[:, :, 1] - values[:, :, 2], "all games"),
        pooled_closure_max_absolute=_close(
            values.sum(axis=0)[:, 0], values.sum(axis=0)[:, 1] - values.sum(axis=0)[:, 2], "pooled"
        ),
        bootstrap_closure=closure,
    )
    return dict(
        comparison_rows=[
            {key: value for key, value in row.items() if key != "variant"}
            for row in interval_rows + source_rows
            if row["variant"] == "primary"
        ],
        game_rows=game_rows,
        diagnostic_rows=diagnostics,
        region_names=list(region_names),
        support_rows=support_rows,
        assessment_game_ids=ids,
        coverage=dict(
            inventory_games=len(game_rows),
            assessment_games=len(ids),
            training_games=len(game_rows) - len(ids),
            actual_assessment_fraction=len(ids) / len(game_rows),
            assessment_directed_hours=float(hours.sum()),
            assessment_recorded_unblocked_attempts=sum(
                row["retained_recorded_unblocked_attempts"]
                for row in game_rows
                if row["partition"] == "assessment"
            ),
            assessment_zero_time_games=int(np.sum(hours == 0)),
            training_directed_hours=sum(
                row["directed_hours"] for row in game_rows if row["partition"] == "training"
            ),
            training_recorded_unblocked_attempts=sum(
                row["retained_recorded_unblocked_attempts"]
                for row in game_rows
                if row["partition"] == "training"
            ),
        ),
        numerical=numerical,
        numerical_status="verified" if verified else "unresolved",
        unresolved_reason=(
            None
            if verified
            else "a bounded probe failed or a complete-regional/source-only direction changed"
        ),
        native_axes=dict(
            game_ids=ids,
            arms=list(ARMS),
            native_cell_count=len(p),
            unavailable_game_ids=[ids[i] for i in range(len(ids)) if not hours[i]],
            unavailable_reason="zero directed exposure; zero array placeholders are unavailable means",
            array_axes=dict(
                observed_mean_complete=["game", "native_cell"],
                predicted_mean_complete=["game", "arm", "native_cell"],
            ),
        ),
        next_question=None,
    ), dict(observed_mean_complete=observed_means, predicted_mean_complete=means)
