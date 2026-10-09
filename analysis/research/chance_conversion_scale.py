"""saved conversion-scale research benchmark; no model or probability admission."""

import argparse
from collections import Counter
import math
from pathlib import Path
import platform
import sys
import time

import matplotlib
import numpy as np
from scipy.special import expit, log_expit

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance import TYPES, fit_logistic
from hockey_stats.chance_cli import identity, output_path
from hockey_stats.chance_evaluation import (
    PROBABILITY_SUMS, add_binary, binary_metrics, binary_record, calibration_bin, finish_binary,
)
from hockey_stats.cli import Once
import chance_assessment as assessment
from chance_development import implementation
from chance_review import agrees, calendar_blocks, clean_implementation, require


WINDOWS = {
    "fit": ("2025-01-01", "2025-02-28"),
    "assessment": ("2025-03-01", "2025-04-17"),
}
CONTEXTS = ("none", "recent")
SETTINGS = dict(optimizer_max_iterations=200, optimizer_ftol=1e-14, optimizer_gtol=1e-10)
DRAW_COLUMNS = ("a", "b", "delta_log_loss", "delta_brier", "unchanged_residual", "adjusted_residual")
METHODS = {"games": None, "calendar_7_day": 7, "calendar_14_day": 14}
DRAWS = 2000
SEED = 3032026
PREFIX = 20
WALL_SECONDS = 900
MEMORY_BYTES = 2 * 1024 ** 3


def check_resources(started):
    measured = assessment.measured_resources(started)
    require(measured["wall_seconds"] <= WALL_SECONDS,
            f"conversion benchmark wall-time ceiling exceeded: {measured['wall_seconds']:.3f} > {WALL_SECONDS} seconds")
    require(measured["peak_memory_bytes"] <= MEMORY_BYTES,
            f"conversion benchmark peak-memory ceiling exceeded: {measured['peak_memory_bytes']} > {MEMORY_BYTES} bytes")
    return measured


class Collector:
    """retain only checked conversion arrays; reconstruction owns source reconciliation."""

    def __init__(self, loaded):
        self._loaded = loaded
        dates = loaded["comparison"]["game_dates"]
        require(max(loaded["composition"]["compatibility"]["training_game_dates"].values()) < WINDOWS["fit"][0],
                "base-model training overlaps the fixed adjustment-fit window")
        require(all(WINDOWS["fit"][0] <= day <= WINDOWS["assessment"][1] for day in dates.values()),
                "saved games fall outside the fixed conversion windows")
        self._windows = {}
        self._games = {}
        for name, (first, last) in WINDOWS.items():
            selected = {gid: day for gid, day in dates.items() if first <= day <= last}
            require(bool(selected), f"no selected games in {name} window")
            self._windows[name] = dict(
                game_dates=selected, x=[], y=[], log_p=[], log_not_p=[], game_index=[],
                recent_context=[], model_type=[],
            )
            self._games.update({gid: (name, i) for i, gid in enumerate(selected)})
        self._identity = binary_metrics(calibration=False)

    def consume(self, row, revised_records):
        _, model_type, _, recent = assessment.saved_descriptors(row)
        if "unblocked_conversion" not in revised_records:
            return
        record = revised_records["unblocked_conversion"]
        logs = row["predictions"]["revision"]["candidate_r"]
        x = logs["log_p"] - logs["log_not_p"]
        require(math.isfinite(x), "saved conversion logit is not finite")
        reproduced = binary_record(row["goal"], float(log_expit(x)), float(log_expit(-x)))
        require(all(abs(reproduced[field] - record[field]) <= 1e-12
                    for field in ("predicted_probability_sum", "log_loss_sum", "brier_score_sum")),
                "identity adjustment does not reproduce saved row probabilities/losses")
        add_binary(self._identity, reproduced)
        name, index = self._games[row["game_id"]]
        window = self._windows[name]
        for field, value in dict(
            x=x, y=row["goal"], log_p=logs["log_p"], log_not_p=logs["log_not_p"],
            game_index=index, recent_context=CONTEXTS.index(recent), model_type=TYPES.index(model_type),
        ).items():
            window[field].append(value)

    def finish(self, reconstructed):
        for field in PROBABILITY_SUMS:
            require(agrees(self._identity[field], reconstructed["metrics"]["unblocked_conversion"][field]),
                    "identity adjustment aggregate disagrees")
        for window in self._windows.values():
            for field in ("x", "log_p", "log_not_p"):
                window[field] = np.asarray(window[field], dtype=np.float64)
            window["y"] = np.asarray(window["y"], dtype=np.bool_)
            window["game_index"] = np.asarray(window["game_index"], dtype=np.int64)
            for field in ("recent_context", "model_type"):
                window[field] = np.asarray(window[field], dtype=np.uint8)
        if self._loaded["completion"]["purpose"] == "research":
            require(max(self._loaded["composition"]["compatibility"]["training_game_dates"].values())
                    == "2024-12-31", "frozen base-model training cutoff changed")
            counts = reconstructed["coverage"]["attempts_by_status"]
            require(counts == dict(eligible=68775, out_of_scope=16270, unavailable=272)
                    and reconstructed["metrics"]["marginal_unblocked"]["count"] == 68775
                    and reconstructed["metrics"]["marginal_unblocked"]["observed_positive_count"] == 49014
                    and reconstructed["metrics"]["unblocked_conversion"]["observed_positive_count"] == 2804,
                    "frozen source population changed")
            for name, expected in (("fit", (346, 23987, 1332)), ("assessment", (366, 25027, 1472))):
                window = self._windows[name]
                require((len(window["game_dates"]), len(window["y"]), int(window["y"].sum())) == expected,
                        f"frozen {name} population changed")
        return self._windows


def support_reason(x, y, weights):
    require(x.ndim == 1 and x.shape == y.shape == weights.shape
            and np.isfinite(x).all() and np.isfinite(weights).all()
            and np.all(weights >= 0) and np.all((y == 0) | (y == 1)),
            "invalid weighted conversion arrays")
    selected = weights > 0
    if not np.any(selected):
        return "zero_fit_mass"
    positive = selected & (y == 1)
    negative = selected & (y == 0)
    if not np.any(positive) or not np.any(negative):
        return "one_fit_label"
    if np.min(x[selected]) == np.max(x[selected]):
        return "rank_deficient_fit"
    if np.max(x[negative]) <= np.min(x[positive]) or np.max(x[positive]) <= np.min(x[negative]):
        return "separated_fit"
    return None


def objective(theta, x_scaled, y, weights):
    eta = theta[0] + theta[1] * x_scaled
    log_p, log_not_p = log_expit(eta), log_expit(-eta)
    mass = np.sum(weights)
    value = math.fsum(weights * np.where(y, -log_p, -log_not_p)) / mass
    residual = weights * np.where(y, -expit(-eta), expit(eta))
    gradient = np.array([math.fsum(residual), math.fsum(residual * x_scaled)]) / mass
    return float(value), gradient


def solve(x, y, weights, m, s):
    reason = support_reason(x, y, weights)
    require(reason is None, f"unsupported conversion fit: {reason}")
    require(math.isfinite(m) and math.isfinite(s) and s > 0, "invalid fixed fit-window scaling")
    mass = float(np.sum(weights))
    require(math.isfinite(mass), "nonfinite total conversion fit weight")
    z = (x - m) / s
    initial = np.array([m, s], dtype=np.float64)
    theta, optimizer = fit_logistic(lambda value: objective(value, z, y, weights), initial, SETTINGS)
    value, gradient = objective(theta, z, y, weights)
    identity_value, _ = objective(initial, z, y, weights)
    eta = theta[0] + theta[1] * z
    curvature = weights * expit(eta) * expit(-eta) / mass
    cross = float(np.sum(curvature * z))
    hessian = np.array([[np.sum(curvature), cross], [cross, np.sum(curvature * z * z)]])
    b = float(theta[1] / s)
    a = float(theta[0] - b * m)
    gradient_norm = float(np.max(np.abs(gradient)))
    require(optimizer["converged"] and np.isfinite(theta).all() and math.isfinite(a)
            and math.isfinite(b) and math.isfinite(value) and np.isfinite(gradient).all()
            and np.isfinite(log_expit(eta)).all() and np.isfinite(log_expit(-eta)).all()
            and np.isfinite(hessian).all(), f"conversion optimizer did not converge to finite quantities: {optimizer}")
    eigenvalues = np.linalg.eigvalsh(hessian)
    require(gradient_norm <= 1e-8, f"conversion scaled gradient exceeds tolerance: {gradient_norm:.12g} > 1e-8")
    require(np.all(eigenvalues > 0), "conversion analytic hessian is not positive definite")
    require(agrees(value, optimizer["objective"]), "conversion optimizer objective disagrees")
    require(value <= identity_value or agrees(value, identity_value),
            "conversion objective is worse than identity")
    require(np.allclose(a + b * x, eta, rtol=1e-12, atol=1e-12),
            "scaled and raw conversion coefficients disagree")
    selected = weights > 0
    return dict(
        a=a, b=b, m=m, s=s, theta=theta.tolist(), objective=value, identity_objective=identity_value,
        gradient=gradient.tolist(), gradient_infinity_norm=gradient_norm, hessian=hessian.tolist(),
        hessian_eigenvalues=eigenvalues.tolist(), optimizer=optimizer,
        support=dict(total_weight=mass, positive_weight_rows=int(selected.sum()),
                     weighted_goals=float(np.sum(weights * y)), design_rank=2, separation=False,
                     class_ranges={str(label): [float(np.min(x[selected & (y == label)])),
                                                float(np.max(x[selected & (y == label)]))]
                                   for label in (0, 1)}),
    )


def finish_metric(metric, games):
    finish_binary(metric)
    n = metric["count"]
    metric.update(predicted_rate=metric["predicted_probability_sum"] / n if n else None,
                  observed_rate=metric["observed_positive_count"] / n if n else None,
                  residual_rate=metric["predicted_minus_observed_pp"] / 100 if n else None,
                  contributing_games=len(games))


def reconcile_parts(parts, total, description):
    for field in PROBABILITY_SUMS:
        require(agrees(math.fsum(part[field] for part in parts), total[field]),
                f"{description}: {field} does not reconcile")


def summarize(windows, nominal):
    metrics, per_game = {}, []
    domains = dict(calendar_month=("2025-03", "2025-04"), recent_context=CONTEXTS, model_type=tuple(TYPES))
    groups = {family: {key: {predictor: binary_metrics(calibration=False)
                             for predictor in ("unchanged", "adjusted")} for key in keys}
              for family, keys in domains.items()}
    group_games = {family: {key: set() for key in keys} for family, keys in domains.items()}
    own_bins = {predictor: [dict(binary_metrics(calibration=False), index=i, lower=i / 20,
                                 upper=(i + 1) / 20, upper_inclusive=i == 19,
                                 predictor=predictor, cohort=f"{predictor}_probability_bin", window="assessment")
                            for i in range(20)] for predictor in ("unchanged", "adjusted")}
    matched_bins = [dict(index=i, lower=i / 20, upper=(i + 1) / 20, upper_inclusive=i == 19,
                         cohort="unchanged_probability_bin", window="assessment", predictors={
                             predictor: binary_metrics(calibration=False)
                             for predictor in ("unchanged", "adjusted")}) for i in range(20)]
    own_games = {predictor: [set() for _ in range(20)] for predictor in own_bins}
    matched_games = [set() for _ in range(20)]
    for name, window in windows.items():
        dates = list(window["game_dates"].values())
        games = [dict(game_id=gid, game_date=day, window=name, predictors={
                     predictor: binary_metrics(calibration=False) for predictor in own_bins})
                 for gid, day in window["game_dates"].items()]
        pooled = {predictor: binary_metrics(calibration=False) for predictor in own_bins}
        contributing = set()
        eta = nominal["a"] + nominal["b"] * window["x"]
        adjusted_p, adjusted_not = log_expit(eta), log_expit(-eta)
        for i, observed in enumerate(window["y"]):
            game_index = int(window["game_index"][i])
            contributing.add(game_index)
            records = dict(
                unchanged=binary_record(bool(observed), float(window["log_p"][i]), float(window["log_not_p"][i])),
                adjusted=binary_record(bool(observed), float(adjusted_p[i]), float(adjusted_not[i])),
            )
            for predictor, record in records.items():
                add_binary(pooled[predictor], record)
                add_binary(games[game_index]["predictors"][predictor], record)
            if name != "assessment":
                continue
            cohort = calibration_bin(records["unchanged"]["predicted_probability_sum"])
            matched_games[cohort].add(game_index)
            descriptors = dict(calendar_month=dates[game_index][:7],
                               recent_context=CONTEXTS[int(window["recent_context"][i])],
                               model_type=TYPES[int(window["model_type"][i])])
            for family, key in descriptors.items():
                group_games[family][key].add(game_index)
            for predictor, record in records.items():
                for family, key in descriptors.items():
                    add_binary(groups[family][key][predictor], record)
                own = calibration_bin(record["predicted_probability_sum"])
                add_binary(own_bins[predictor][own], record)
                own_games[predictor][own].add(game_index)
                add_binary(matched_bins[cohort]["predictors"][predictor], record)
        for predictor, metric in pooled.items():
            finish_metric(metric, contributing)
            for game in games:
                part = game["predictors"][predictor]
                finish_metric(part, [game["game_id"]] if part["count"] else [])
            reconcile_parts([game["predictors"][predictor] for game in games], metric, f"{name} games")
        metrics[name] = dict(interpretation="apparent/in-sample" if name == "fit" else "later-window assessment",
                             **pooled)
        per_game.extend(games)
    unchanged, adjusted = metrics["assessment"]["unchanged"], metrics["assessment"]["adjusted"]
    metrics["assessment"]["paired_differences"] = {
        field: adjusted[field] - unchanged[field] if unchanged[field] is not None else None
        for field in ("log_loss", "brier_score", "residual_rate")}
    for family, table in groups.items():
        for key, predictors in table.items():
            for predictor, metric in predictors.items():
                finish_metric(metric, group_games[family][key])
                metric.update(predictor=predictor, cohort=f"{family}={key}", window="assessment")
        for predictor in own_bins:
            reconcile_parts([predictors[predictor] for predictors in table.values()],
                            metrics["assessment"][predictor], family)
    for predictor, bins in own_bins.items():
        for i, bucket in enumerate(bins):
            finish_metric(bucket, own_games[predictor][i])
            matched = matched_bins[i]["predictors"][predictor]
            finish_metric(matched, matched_games[i])
            matched.update(predictor=predictor, cohort="unchanged_probability_bin", window="assessment")
        reconcile_parts(bins, metrics["assessment"][predictor], f"{predictor} own bins")
        reconcile_parts([bucket["predictors"][predictor] for bucket in matched_bins],
                        metrics["assessment"][predictor], f"{predictor} matched bins")
    return dict(metrics=metrics, groups=groups, own_bins=own_bins, matched_bins=matched_bins, per_game=per_game)


def bootstrap(fit, later, nominal, started):
    """independent window samples, paired assessment weights, and one adjustment refit per draw."""
    states = {}
    for name, days in METHODS.items():
        generator = np.random.Generator(np.random.PCG64(SEED))
        state = dict(draw_values=[], draw_missing_reasons=[], units={}, samples={}, game_units={},
                     fit_diagnostics=dict(supported_solves=0, maximum_iterations=0,
                                          maximum_gradient_infinity_norm=0.0, minimum_hessian_eigenvalue=None))
        for label, window in (("fit", fit), ("assessment", later)):
            dates = list(window["game_dates"].values())
            units = np.arange(len(dates)) if days is None else calendar_blocks(dates, days)
            count = int(units.max()) + 1
            state["game_units"][label] = units
            state["samples"][label] = generator.integers(0, count, size=(DRAWS, count))
            contributing_games = np.unique(window["game_index"])
            state["units"][label] = dict(
                selected_games=len(dates), contributing_games=len(contributing_games),
                selected_units=count, contributing_units=len(np.unique(units[contributing_games])),
                selected_blocks=count if days else None,
                contributing_blocks=len(np.unique(units[contributing_games])) if days else None,
                calendar_days=days, anchor_date=dates[0] if days else None,
                game_unit_indices=units.tolist(),
            )
        states[name] = state
    unchanged_loss = np.where(later["y"], -later["log_p"], -later["log_not_p"])
    unchanged_probability = np.exp(later["log_p"])
    unchanged_brier = (unchanged_probability - later["y"]) ** 2
    unchanged_residual = unchanged_probability - later["y"]
    prefix_seconds = {}
    for start, stop in ((0, PREFIX), (PREFIX, DRAWS)):
        for name, state in states.items():
            phase_started = time.monotonic()
            for draw in range(start, stop):
                check_resources(started)
                row_weights = {}
                for label, window in (("fit", fit), ("assessment", later)):
                    multiplicity = np.bincount(state["samples"][label][draw],
                                               minlength=state["units"][label]["selected_units"])
                    row_weights[label] = multiplicity[state["game_units"][label][window["game_index"]]]
                fit_weights, weights = row_weights["fit"], row_weights["assessment"]
                reason = support_reason(fit["x"], fit["y"], fit_weights)
                evaluation_mass = float(np.sum(weights))
                evaluation_reason = None if evaluation_mass > 0 else "zero_assessment_mass"
                values = [None] * len(DRAW_COLUMNS)
                missing = [[] for _ in DRAW_COLUMNS]
                if evaluation_reason is None:
                    values[4] = float(np.sum(weights * unchanged_residual) / evaluation_mass)
                if reason is None:
                    try:
                        fitted = solve(fit["x"], fit["y"], fit_weights, nominal["m"], nominal["s"])
                    except InputContractError as error:
                        raise InputContractError(f"{name} draw {draw}: {error}") from error
                    values[:2] = [fitted["a"], fitted["b"]]
                    diagnostics = state["fit_diagnostics"]
                    diagnostics["supported_solves"] += 1
                    diagnostics["maximum_iterations"] = max(
                        diagnostics["maximum_iterations"], fitted["optimizer"]["iterations"])
                    diagnostics["maximum_gradient_infinity_norm"] = max(
                        diagnostics["maximum_gradient_infinity_norm"], fitted["gradient_infinity_norm"])
                    smallest = fitted["hessian_eigenvalues"][0]
                    if diagnostics["minimum_hessian_eigenvalue"] is None or smallest < diagnostics["minimum_hessian_eigenvalue"]:
                        diagnostics["minimum_hessian_eigenvalue"] = smallest
                    if evaluation_reason is None:
                        eta = fitted["a"] + fitted["b"] * later["x"]
                        log_p, log_not_p = log_expit(eta), log_expit(-eta)
                        require(np.isfinite(log_p).all() and np.isfinite(log_not_p).all(),
                                "nonfinite bootstrap assessment probabilities")
                        probability = np.exp(log_p)
                        loss = np.where(later["y"], -log_p, -log_not_p)
                        values[2] = float(np.sum(weights * (loss - unchanged_loss)) / evaluation_mass)
                        values[3] = float(np.sum(
                            weights * ((probability - later["y"]) ** 2 - unchanged_brier)) / evaluation_mass)
                        values[5] = float(np.sum(weights * (probability - later["y"])) / evaluation_mass)
                for i in range(len(DRAW_COLUMNS)):
                    if reason is not None and i != 4:
                        missing[i].append(reason)
                    if evaluation_reason is not None and i >= 2:
                        missing[i].append(evaluation_reason)
                    require(values[i] is None and bool(missing[i]) or values[i] is not None
                            and not missing[i] and math.isfinite(values[i]), "invalid bootstrap statistic/missingness")
                state["draw_values"].append(values)
                state["draw_missing_reasons"].append(missing)
                check_resources(started)
            if start == 0:
                prefix_seconds[name] = time.monotonic() - phase_started
        if start == 0:
            measured = check_resources(started)
            projected = measured["wall_seconds"] + sum((DRAWS - PREFIX) * seconds / PREFIX
                                                       for seconds in prefix_seconds.values())
            require(projected <= WALL_SECONDS,
                    f"conversion benchmark projected wall-time ceiling exceeded: {projected:.3f} > {WALL_SECONDS} seconds "
                    f"at elapsed {measured['wall_seconds']:.3f}; prefix seconds {prefix_seconds}")
            projection = dict(prefix_draws_per_method=PREFIX, prefix_draw_seconds=prefix_seconds,
                              elapsed_at_projection_seconds=measured["wall_seconds"],
                              projected_total_seconds=projected)
    nominal_eta = nominal["a"] + nominal["b"] * later["x"]
    nominal_p = np.exp(log_expit(nominal_eta))
    nominal_loss = np.where(later["y"], -log_expit(nominal_eta), -log_expit(-nominal_eta))
    estimates = [nominal["a"], nominal["b"]] + [
        float(np.mean(values)) if len(values) else None
        for values in (nominal_loss - unchanged_loss, (nominal_p - later["y"]) ** 2 - unchanged_brier,
                       unchanged_residual, nominal_p - later["y"])]
    methods = {}
    for name, state in states.items():
        intervals = {}
        for i, field in enumerate(DRAW_COLUMNS):
            values = [row[i] for row in state["draw_values"]]
            undefined = sum(value is None for value in values)
            reasons = Counter(reason for row in state["draw_missing_reasons"] for reason in row[i])
            intervals[field] = dict(
                estimate=estimates[i],
                interval=None if undefined else np.percentile(values, [2.5, 97.5], method="linear").tolist(),
                undefined_draws=undefined, missing_reason="undefined_draws" if undefined else None,
                reason_counts=dict(reasons), units=state["units"],
            )
        methods[name] = dict(units=state["units"], draws=state["draw_values"],
                             draw_missing_reasons=state["draw_missing_reasons"], intervals=intervals,
                             fit_diagnostics=state["fit_diagnostics"])
    return dict(
        draws_per_method=DRAWS, seed=SEED, generator="PCG64", percentile_method="linear", confidence=0.95,
        draw_columns=list(DRAW_COLUMNS), residual_units="proportion", methods=methods,
        interpretation="paired pooled attempt-weighted assessment differences; adjustment refitted on independently resampled fit-window units",
        included_uncertainty=["adjustment_estimation", "selected_fit_window_sampling", "selected_assessment_window_sampling"],
        excluded_uncertainty=["saved_base_model_fitting", "adaptive_selection", "origin_assumptions", "dependence_between_windows"],
        undefined="retain every draw; any undefined statistic makes its interval null; no redraws",
        resource_projection=projection,
    )


def recommendation(b, methods):
    intervals = {name: method["intervals"]["delta_log_loss"]["interval"] for name, method in methods.items()}
    adverse = [name for name, interval in intervals.items() if interval is not None and interval[0] > 0]
    if b <= 0 or adverse:
        classification = "conflicting_or_adverse"
        reasons = (["nonpositive_nominal_slope"] if b <= 0 else []) + [f"{name}_supports_harm" for name in adverse]
    elif intervals["games"] is not None and intervals["games"][1] < 0 and all(
        intervals[name] is not None for name in ("calendar_7_day", "calendar_14_day")
    ):
        classification = "scale_priority"
        reasons = ["positive_slope", "whole_game_supports_benefit", "calendar_sensitivities_defined_without_harm"]
    else:
        classification, reasons = "inconclusive", ["strict_benefit_and_defined_calendar_sensitivity_not_established"]
    return dict(classification=classification, reasons=reasons, nominal_b=b, log_loss_intervals=intervals,
                interpretation="research priority only; no probability admission or automatic dependent fit",
                rule="adverse if b <= 0 or any defined lower > 0; scale_priority if b > 0 and games upper < 0 "
                "with both calendar intervals defined and neither lower > 0; otherwise inconclusive")


def save_figure(own_bins, path, purpose):
    figure, axes = plt.subplots(2, 2, figsize=(11.5, 8.7), sharex=True, sharey="row",
                                gridspec_kw=dict(height_ratios=[2.2, 1]))
    colors = ("#3b596f", "#a3452d")
    maximum = max(bucket["count"] for bins in own_bins.values() for bucket in bins)
    for column, (predictor, bins) in enumerate(own_bins.items()):
        x = [100 * (bucket["lower"] + bucket["upper"]) / 2 for bucket in bins]
        residuals = [bucket["predicted_minus_observed_pp"] if bucket["count"] else np.nan for bucket in bins]
        axes[0, column].scatter(x, residuals, color=colors[column], s=27, clip_on=False, zorder=3)
        axes[0, column].axhline(0, color="0.45", linewidth=0.8)
        axes[0, column].set(title=predictor, ylim=(-100, 100))
        axes[0, column].set_yscale("symlog", linthresh=5)
        axes[0, column].set_yticks([-100, -25, -10, -5, 0, 5, 10, 25, 100],
                                  ["−100", "−25", "−10", "−5", "0", "5", "10", "25", "100"])
        axes[1, column].scatter(x, [bucket["count"] for bucket in bins], color=colors[column],
                                s=23, clip_on=False, zorder=3)
        axes[1, column].set_yscale("symlog", linthresh=1)
        axes[1, column].set(ylim=(0, max(2, maximum * 1.35)), xlim=(0, 100),
                            xlabel="own-bin probability midpoint (%)")
        ticks = [0, 1] + [10 ** power for power in range(1, int(math.log10(max(1, maximum))) + 1)]
        axes[1, column].set_yticks(ticks, [str(value) for value in ticks])
        for axis in axes[:, column]:
            axis.grid(axis="y", color="0.88", linewidth=0.6)
            axis.spines[["top", "right"]].set_visible(False)
    axes[0, 0].set_ylabel("predicted − observed goals / attempts (pp)")
    axes[1, 0].set_ylabel("unblocked attempts")
    figure.suptitle("conversion-scale benchmark · later-window own-bin residuals", fontsize=15, x=0.08, ha="left")
    exposure = "both windows are research-exposed" if purpose == "research" else "synthetic fixture exercise"
    caption = (
        "fit: 2025-01-01–2025-02-28; assessment: 2025-03-01–2025-04-17; " + exposure + ".\n"
        "each bin uses its predictor's eligible unblocked attempts; positive residual means overprediction. own-bin memberships differ.\n"
        "residual axes: linear within ±5 pp, logarithmic tails to ±100 pp. count axes: linear 0–1, logarithmic above 1.\n"
        "all 20 bins are retained; empty bins have no residual marker and show zero counts.\n"
        "nonlinear tails trade proportional spacing for readability; exact values remain in tables.\n"
        "bins are descriptive. reported pooled intervals refit the adjustment, conditional on the saved base model.\n"
        "retrospective observed-cell conversion; neither a live pre-release forecast nor standardized opportunity."
    )
    figure.text(0.08, 0.025, caption, fontsize=9, va="bottom", linespacing=1.55)
    figure.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.27, hspace=0.2, wspace=0.14)
    figure.savefig(path, dpi=180, facecolor="white")
    plt.close(figure)


def run(completion_path, protocol_path, output_value):
    started = time.monotonic()
    loaded = assessment.load_evidence(completion_path)
    protocol = identity(Path(protocol_path).resolve(strict=True))
    output = output_path(output_value, [str(Path(ref["path"]).parent)
                                        for ref in (*loaded["identities"].values(), protocol)])
    require(not any((parent / ".git").exists() for parent in output.parents),
            "conversion benchmark outputs must be outside git repositories/worktrees")
    execution = implementation()
    execution.update(platform=platform.platform(), python_executable=sys.executable)
    purpose = loaded["completion"]["purpose"]
    if purpose == "research":
        clean_implementation(execution)
    check_resources(started)
    collector = Collector(loaded)
    pass_started = time.monotonic()
    reconstructed = assessment.reconstruct(loaded, diagnostic=collector)
    stream_seconds = time.monotonic() - pass_started
    windows = collector.finish(reconstructed)
    check_resources(started)
    fit, later = windows["fit"], windows["assessment"]
    require(len(fit["y"]) > 0, "fit window requires eligible unblocked attempts")
    m, s = float(np.mean(fit["x"])), float(np.std(fit["x"]))
    nominal = solve(fit["x"], fit["y"], np.ones(len(fit["y"])), m, s)
    check_resources(started)
    summaries = summarize(windows, nominal)
    original_games = {game["game_id"]: game for game in reconstructed["per_game"]}
    for game in summaries["per_game"]:
        original = original_games[game["game_id"]]
        assessment.reconcile_metric(game["predictors"]["unchanged"],
                                    original["quantities"]["unblocked_conversion"]["metrics"])
    check_resources(started)
    uncertainty = bootstrap(fit, later, nominal, started)
    for field, value in (
        ("delta_log_loss", summaries["metrics"]["assessment"]["paired_differences"]["log_loss"]),
        ("delta_brier", summaries["metrics"]["assessment"]["paired_differences"]["brier_score"]),
        ("unchanged_residual", summaries["metrics"]["assessment"]["unchanged"]["residual_rate"]),
        ("adjusted_residual", summaries["metrics"]["assessment"]["adjusted"]["residual_rate"]),
    ):
        require(all(method["intervals"][field]["estimate"] is None and value is None or
                    method["intervals"][field]["estimate"] is not None and value is not None
                    and agrees(method["intervals"][field]["estimate"], value)
                    for method in uncertainty["methods"].values()), "native and vectorized nominal metrics disagree")
    result = recommendation(nominal["b"], uncertainty["methods"])
    output.mkdir()
    save_figure(summaries["own_bins"], output / "conversion-scale.png", purpose)
    figure = identity(output / "conversion-scale.png")
    measured = dict(
        check_resources(started), limits=dict(wall_seconds=WALL_SECONDS, peak_memory_bytes=MEMORY_BYTES),
        stream_passes=1, stream_pass_seconds=stream_seconds, attempts_bytes_read=reconstructed["attempts_bytes"],
        recognized_rows_per_second=sum(reconstructed["coverage"]["attempts_by_status"].values()) / stream_seconds,
        stream_bytes_per_second=reconstructed["attempts_bytes"] / stream_seconds,
        input_bytes=reconstructed["attempts_bytes"] + sum(Path(ref["path"]).stat().st_size
                    for name, ref in loaded["identities"].items() if name != "attempts") + Path(protocol["path"]).stat().st_size,
        bootstrap_projection=uncertainty["resource_projection"], figure_bytes=Path(figure["path"]).stat().st_size,
    )
    composition = loaded["composition"]
    benchmark = dict(
        schema_version=1, artifact_kind="chance_conversion_scale_benchmark", purpose=purpose,
        model_admission="not_assessed", historical_admission_status="withheld" if purpose == "research" else "not_applicable",
        parent_scientific_assessment=loaded["completion"]["scientific_assessment"],
        inputs=loaded["identities"], protocol=protocol, implementation=execution,
        parent_implementations=dict(composition=composition["implementation"],
                                   fitted_and_assessed_parents=composition["parent_implementations"]),
        population=dict(coverage=reconstructed["coverage"], base_training_game_dates=composition["compatibility"]["training_game_dates"],
                        windows={name: dict(first_date=WINDOWS[name][0], last_date=WINDOWS[name][1],
                                            game_dates=window["game_dates"], selected_games=len(window["game_dates"]),
                                            unblocked_attempts=len(window["y"]), goals=int(window["y"].sum()))
                                 for name, window in windows.items()},
                        research_exposure="both windows previously examined; adjustment receives newer labels than the saved model"
                        if purpose == "research" else "synthetic fixture exercise; no scientific inference",
                        quantity="factual observed-cell goal conversion among all eligible unblocked attempts"),
        fit=dict(nominal, settings=SETTINGS, penalty=None, coefficient_constraints=None,
                 objective_description="weighted mean bernoulli negative log likelihood", initialization=[m, s],
                 scaling="nominal fit-window population mean and standard deviation, fixed in every draw"),
        **summaries, uncertainty=uncertainty, recommendation=result, figure=figure, resources=measured,
    )
    write_json(output / "benchmark.json", benchmark)
    benchmark_identity = identity(output / "benchmark.json")
    completion_resources = dict(measured, **check_resources(started),
                               output_bytes_before_completion=(output / "benchmark.json").stat().st_size + measured["figure_bytes"])
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_conversion_scale_benchmark_completion", purpose=purpose,
        inputs=loaded["identities"], protocol=protocol, implementation=execution,
        benchmark=benchmark_identity, figure=figure, resources=completion_resources,
    ))
    return benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("completion", "protocol", "out"):
        parser.add_argument(f"--{name}", required=True, action=Once)
    args = parser.parse_args()
    try:
        result = run(Path(args.completion), Path(args.protocol), args.out)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError, FloatingPointError) as error:
        print(f"conversion-scale benchmark failed: {error}", file=sys.stderr)
        return 1
    print(f"conversion-scale benchmark complete: {result['recommendation']['classification']}; {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
