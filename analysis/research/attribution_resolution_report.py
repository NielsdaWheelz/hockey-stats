"""04h's tables and figure; numerical assessment remains with the study."""

import csv
from collections import Counter
from pathlib import Path

import numpy as np

from hockey_stats.artifacts import require
from hockey_stats.chance_cli import identity


CONDITIONS = ("base", "half_effect", "double_games", "broad")
CONDITION_LABELS = ("base · 40 modes", "half effect · 40 modes",
                    "independent double games · 40 modes", "broad · 11 modes")
ARM_LABELS = {
    "annual": "annual borrowing, 40 spatial modes",
    "adaptive": "pooled history, training-selected",
    "fixed_reference": "fixed penalty selected with calibration truth — diagnostic",
    "zero": "zero player maps",
}
TARGET_LABELS = {
    "twelve_region_vector": "twelve-region vector",
    "within_20_ft": "within 20 ft, in front of goal",
    "lateral_redistribution": "lateral redistribution",
}


def _number(value):
    return "unavailable" if value is None else f"{value:.5g}"


def _figure(output, assessment):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(6, 5, figsize=(21, 21), squeeze=False,
                                gridspec_kw={"width_ratios": [1, 1, 1, 1, 1.3]})
    primary = assessment["curves"][0]["target"]
    variances = sorted({row["prior_variance"] for row in assessment["curves"]})
    require(len(variances) == 18 and variances[0] == 0,
            "figure requires the exact eighteen-point variance grid")
    cell_ids = [(population, law) for population in ("sparse", "diffuse", "null")
                for law in ("gaussian", "game_pace")]
    for cell, (population, law) in enumerate(cell_ids):
        for column, condition in enumerate(CONDITIONS):
            axis = axes[cell, column]
            selected_condition = "base" if population == "null" and condition == "half_effect" else condition
            rows = sorted((row for row in assessment["curves"]
                           if (row["population"], row["law"], row["condition"], row["target"])
                           == (population, law, selected_condition, primary)),
                          key=lambda row: row["prior_variance"])
            require([row["prior_variance"] for row in rows] == variances,
                    "figure fixed curves are incomplete")
            means = np.array([row["rms"]["mean"] for row in rows])
            axis.plot(np.arange(18), means, color="#255b83", linewidth=1.5)
            if all(row["rms"]["lower"] is not None for row in rows):
                axis.fill_between(np.arange(18), [row["rms"]["lower"] for row in rows],
                                  [row["rms"]["upper"] for row in rows],
                                  color="#255b83", alpha=.15, linewidth=0)
            selected = [i for i, row in enumerate(rows) if row["calibration_selected"]]
            require(len(selected) == 1, "figure calibration selection is missing or duplicated")
            axis.scatter(selected, means[selected], marker="D", color="#b55b22", s=24, zorder=3)
            axis.set_xticks([0, 3, 7, 11, 15, 17], ["0", "1e−7", "1e−5", "1e−3", ".1", "1"])
            axis.tick_params(axis="both", labelsize=8)
            axis.set_ylim(bottom=0)
            axis.grid(axis="y", alpha=.2)
            if cell == 0:
                axis.set_title(CONDITION_LABELS[column], fontsize=10)
            if column == 0:
                axis.set_ylabel(f"{population} · {law.replace('_', ' ')}\nregional rms, attempts/60", fontsize=9)
            if cell == 5:
                axis.set_xlabel("prior variance · ordered finite grid", fontsize=9)
            if population == "null" and condition == "half_effect":
                axis.text(.04, .94, "exact alias of base", transform=axis.transAxes, va="top", fontsize=8)

        axis = axes[cell, 4]
        arms = ("annual", "adaptive", "fixed_reference")
        colors = ("#777777", "#255b83", "#b55b22")
        for arm_index, (arm, color) in enumerate(zip(arms, colors, strict=True)):
            for condition_index, condition in enumerate(("base", "broad")):
                matches = [row for row in assessment["comparisons"]
                           if (row["population"], row["law"], row["condition"], row["target"], row["arm"])
                           == (population, law, condition, primary, arm)]
                require(len(matches) == 1, "categorical figure comparison is missing or duplicated")
                summary = matches[0]["rms"]
                x = condition_index + (arm_index - 1) * .22
                if summary["lower"] is not None:
                    axis.plot([x, x], [summary["lower"], summary["upper"]], color=color, linewidth=1)
                    axis.plot([x-.025, x+.025], [summary["lower"]]*2, color=color, linewidth=1)
                    axis.plot([x-.025, x+.025], [summary["upper"]]*2, color=color, linewidth=1)
                axis.plot(x, summary["mean"], color=color,
                          marker=("o", "s", "D")[arm_index], markersize=4, linestyle="none",
                          label=ARM_LABELS[arm] if cell == condition_index == 0 else None)
        axis.set_xticks([0, 1], ["pooled 40 modes", "pooled 11 modes"], fontsize=8)
        axis.set_xlim(-.5, 1.5)
        axis.set_ylim(0, axis.get_ylim()[1]*1.18)
        axis.grid(axis="y", alpha=.2)
        axis.set_ylabel("regional rms, attempts/60", fontsize=9)
        if cell == 0:
            axis.set_title("aggregate errors · separate estimators", fontsize=10)
        axis.text(.03, .97, "annual baseline: 40 modes in both groups", transform=axis.transAxes,
                  va="top", fontsize=7)
    handles, labels = axes[0, 4].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .014),
                  ncol=1, frameon=False, fontsize=9)
    fixture = "fixture exercise · no research conclusion\n" if assessment["purpose"] == "fixture_exercise" else ""
    figure.suptitle(f"{fixture}five-season spatial recovery · numerical status: {assessment['numerical_status']}\n"
                    "fixed curves: assessment truths; diamonds: twelve-region penalty selected with calibration truth",
                    fontsize=13, y=.988)
    figure.text(.5, .071,
        f"rms = sqrt(mean twelve-region squared error / 12); rank-{assessment['target_rank']} identifiable player target, denominator 64\n"
        "bands/bars: 95% intervals for mean experimental risk, conditional on designs/calibration; no player intervals\n"
        "fixed curves/reference: analytic known-law risk; annual/training-selected: realized saved-response errors\n"
        f"base synthetic mean {assessment['real_context']['synthetic_mean_minutes']:.4g} minutes; "
        "double games uses independent game/pace copies; no new research responses",
        ha="center", va="center", fontsize=9)
    figure.subplots_adjust(left=.065, right=.985, top=.945, bottom=.12, wspace=.38, hspace=.48)
    path = output/"resolution.png"
    figure.savefig(path, dpi=150, facecolor="white")
    plt.close(figure)
    return identity(path)


def render_reports(output, assessment):
    """write one complete comparison table, one limits table and one figure."""
    output = Path(output)
    path = output/"comparison.csv"
    labels = ("record_type", "population", "law", "condition", "target", "arm", "partition",
              "prior_variance", "calibration_selected", "analytic_null", "spatial_modes", "calculation", "target_label")
    fields = (*labels, "metric", "mean", "lower", "upper", "reason")
    with path.open("x", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        for record_type, records in (("fixed_curve", assessment["curves"]),
                                     ("comparison", assessment["comparisons"]),
                                     ("partition", assessment["partitions"])):
            for row in records:
                row_labels = {name: row[name] for name in labels if name in row}
                row_labels["target_label"] = TARGET_LABELS[row["target"]]
                if record_type == "fixed_curve":
                    row_labels.update(spatial_modes=11 if row["condition"] == "broad" else 40,
                                      calculation="analytic known-law fixed-family")
                for metric, summary in row.items():
                    if isinstance(summary, dict) and "mean" in summary:
                        writer.writerow(dict(record_type=record_type, **row_labels, metric=metric,
                            mean=summary["mean"], lower=summary["lower"], upper=summary["upper"],
                            reason=summary.get("reason")))
        for row in assessment["selections"]:
            row_labels = {key: row[key] for key in ("population", "law", "condition")}
            writer.writerow(dict(record_type="calibration_selection", **row_labels,
                prior_variance=row["fixed_variance"], metric="fixed_variance", mean=row["fixed_variance"]))
            adaptive = row["adaptive"]
            if adaptive["status"] == "run":
                for frequency in adaptive["counts"]:
                    writer.writerow(dict(record_type="adaptive_selection", **row_labels,
                        prior_variance=frequency["prior_variance"], metric="count", mean=frequency["count"]))
                for endpoint in ("lower_endpoint", "upper_endpoint"):
                    writer.writerow(dict(record_type="adaptive_selection", **row_labels,
                        metric=endpoint, mean=adaptive[endpoint]))
            else:
                for arm in ("annual", "adaptive"):
                    writer.writerow(dict(record_type="comparison", **row_labels, arm=arm,
                        metric="assessment", reason="not_run: fixed-family curves only"))
        for law in ("gaussian", "game_pace"):
            writer.writerow(dict(record_type="condition_alias", population="null", law=law,
                condition="half_effect", metric="alias", reason="exact alias of base; no replicated analytic truth"))
    table = identity(path)

    path = output/"limits-context.md"
    lines = ["# limits and real-data context", "", "| boundary | meaning |", "|---|---|"]
    lines.extend(f"| limit {index + 1} | {limit.replace('|', '/')} |"
                 for index, limit in enumerate(assessment["limits"]))
    lines.extend([
        "| experimental population | four teams, eight slots each; randomized fixed deployment; inseparable 26/31 average retains weight two; individual difference is not estimable |",
        "| temporal assumption | constant pooled effects; entrants retain their own evidence; returner 8 can change physical field while retaining identity |",
        f"| spatial representation | 40 or 11 saved spatial modes; distinct from the rank-{assessment['target_rank']} identifiable player target; eleven modes retain actual native truth and can omit detail |",
        "| target units | redistributed recorded unblocked attempts per 60 team minutes, with unchanged total rate; offense and attempts allowed remain separate |",
        "| functionals | within 20 ft, in front of goal; lateral redistribution is half positive-y minus negative-y mass. neither is xg, total offense, high danger or handedness |",
        "| prediction | spatial/inverse-share-weighted full-lineup error; signed coupling retained; no fitted volume or complete-intensity validation |",
        "| reference | fixed penalty selected on calibration truths by mean twelve-region risk; conditional expected risk, not a usable selector or an attainable universal bound |",
        "| comparisons | unchanged annual 40-mode control repeated for both pooled representations; temporal assumptions, selector and sometimes representation differ |",
        "| intervals | 10,000 paired outer resamples; conditional on designs, calibration sample and selected reference. no reference-selection uncertainty or individual-player precision |",
        "| null | one analytic truth per law/three unique conditions; half effect aliases base. observed null fits retain distinct saved samples and intervals |",
        "| incomplete calculations | half-effect and double-game adaptive/annual assessments are not_run; null ratios unavailable because zero risk is zero |",
        "| historical margin | .75 × mean zero risk − mean fitted risk is a labeled historical reference, not an accuracy or nomination gate |",
        "| penalty grid | exact zero plus seventeen positive variances; selected endpoint frequencies appear in the comparison table. endpoints limit the examined range and are not optimizer failures |",
        "| transport | research-exposed cases; real spatial deployment spectrum unavailable. comparable minutes do not imply comparable lineup information |",
        "| publication | nomination:null, admission:not_admitted, handoff:null; no real-player ability or chance-valued quantity supplied |",
    ])
    context = assessment["real_context"]
    lines.append(f"| real context, 04a unblocked population | final median exposure "
        f"{context['final_median_minutes']:.2f} minutes; synthetic mean {context['synthetic_mean_minutes']:.4g} "
        f"minutes and rate {context['synthetic_rate']:.4g}/60. equal minutes do not imply equal lineup information |")
    for row in context["annual"]:
        lines.append(f"| real context, {row['season']} | {row['current_players']} players; "
            f"recorded unblocked rate {row['league_team_rate_per_60']:.5f}/60; "
            f"{row['recorded_attempts']} attempts / {row['team_seconds']} team seconds |")
    for row in context["exposure_quartiles"]:
        cutpoints = ", ".join(f"{value/60:.2f}" for value in row["cutpoints_seconds"])
        lines.append(f"| real context, {row['role']} exposure quartiles | cutpoints {cutpoints} minutes; "
            "final-season unblocked population; descriptive exposure only |")
    lines.append(f"| saved source numerical status | `{assessment['source_status']['numerical_status']}`; "
        "retained independently of this study's numerical verification |")
    for cell in assessment["source_status"]["controls"]:
        annual = [year["scale"] for record in cell["audit"] for year in record["annual"]]
        final = [record["annual"][-1]["scale"] for record in cell["audit"]]
        all_statuses = ", ".join(f"{name}: {count}" for name, count in sorted(Counter(row["status"] for row in annual).items()))
        final_statuses = ", ".join(f"{name}: {count}" for name, count in sorted(Counter(row["status"] for row in final).items()))
        reasons = Counter(reason for row in annual for reason in row["own_reasons"])
        reasons_text = ", ".join(f"{name}: {count}" for name, count in sorted(reasons.items())) or "none"
        lines.append(f"| saved controls, {cell['population']} / {cell['law']} | final {len(final)} states "
            f"({final_statuses}); all {len(annual)} annual states ({all_statuses}); "
            f"inherited limitations {sum(row['inherited_limitation'] for row in final)}/{len(final)} final and "
            f"{sum(row['inherited_limitation'] for row in annual)}/{len(annual)} annual; own reasons {reasons_text}. "
            "all records remain in their denominators |")
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")
    limits = identity(path)

    figure = _figure(output, assessment)
    question = assessment["next_question"]
    path = output/"decision.md"
    lines = ["# 04h decision", "",
        f"status: {assessment['purpose']}; numerical status `{assessment['numerical_status']}`. "
        "`nomination:null,admission:not_admitted,handoff:null`.", "",
        "this study compares conditional expected recovery within one finite constant-history family "
        "with realized errors from saved-response training-selected fits and unchanged annual borrowing. "
        "truth-selected penalties are diagnostic and cannot be deployed.", "",
        f"saved source numerical status: `{assessment['source_status']['numerical_status']}`. "
        "annual scale and inherited limitations remain visible in the limits table and every denominator.", "",
        "| population / law | pooled modes | annual regional rms | pooled regional rms | fixed-reference regional rms | annual − pooled spatial prediction error |",
        "|---|---:|---:|---:|---:|---:|"]
    primary = assessment["curves"][0]["target"]
    for population in ("sparse", "diffuse", "null"):
        for law in ("gaussian", "game_pace"):
            for condition, columns in (("base", 40), ("broad", 11)):
                rows = {row["arm"]: row for row in assessment["comparisons"]
                        if (row["population"], row["law"], row["condition"], row["target"])
                        == (population, law, condition, primary)}
                lines.append(f"| {population} / {law} | {columns} | "
                    f"{_number(rows['annual']['rms']['mean'])} | {_number(rows['adaptive']['rms']['mean'])} | "
                    f"{_number(rows['fixed_reference']['rms']['mean'])} | "
                    f"{_number(rows['adaptive']['annual_minus_pooled_prediction']['mean'])} |")
    base = [row for row in assessment["comparisons"] if row["population"] != "null"
            and row["condition"] == "base" and row["target"] == primary and row["arm"] == "adaptive"]
    recovery_improved = sum(row["annual_minus_pooled"]["mean"] > 0 for row in base)
    prediction_improved = sum(row["annual_minus_pooled_prediction"]["mean"] > 0 for row in base)
    lines.extend(["",
        f"in the four non-null base cells, training-selected pooling has lower mean recovery error than annual borrowing "
        f"in {recovery_improved}/4 and lower mean spatial prediction error in {prediction_improved}/4. "
        "these descriptive counts impose no new gate; intervals crossing zero establish neither equivalence nor noninferiority.", "",
        "regional rms is sqrt(mean twelve-region error / 12), in redistributed attempts/60 per player-role/region. "
        "prediction is spatial/inverse-share-weighted; positive annual-minus-pooled favors pooling. "
        "the complete [comparison table](comparison.csv) includes every fixed condition, target, signed term, "
        "paired interval and transition partition. [limits and real context](limits-context.md) identify the claim boundaries. "
        "[the figure](resolution.png) separates fixed curves from adaptive aggregate errors.", ""])
    if question == "penalty_selection":
        nonnull = [row for row in assessment["comparisons"] if row["population"] != "null"
                   and row["target"] == primary and row["arm"] == "adaptive"]
        reference_lower = sum(row["adaptive_minus_reference"]["mean"] > 0 for row in nonnull)
        broad = [row for row in nonnull if row["condition"] == "broad"]
        broad_recovery = sum(row["annual_minus_pooled"]["mean"] > 0 for row in broad)
        broad_prediction = sum(row["annual_minus_pooled_prediction"]["mean"] > 0 for row in broad)
        diffuse_base = {(row["law"], row["arm"]): row for row in assessment["comparisons"]
                        if row["population"] == "diffuse" and row["condition"] == "base"
                        and row["target"] == primary}
        reference_prediction = "/".join(_number(diffuse_base[(law, "fixed_reference")]["prediction_excess"]["mean"])
                                        for law in ("gaussian", "game_pace"))
        adaptive_prediction = "/".join(_number(diffuse_base[(law, "adaptive")]["prediction_excess"]["mean"])
                                       for law in ("gaussian", "game_pace"))
        lateral_worse = sum(row["annual_minus_pooled"]["mean"] < 0 for row in assessment["comparisons"]
                            if row["law"] == "game_pace" and row["population"] != "null"
                            and row["condition"] == "broad" and row["target"] == "lateral_redistribution"
                            and row["arm"] == "adaptive")
        null_rms = [row["rms"]["mean"] for row in assessment["comparisons"]
                    if row["population"] == "null" and row["target"] == primary and row["arm"] == "adaptive"]
        selected_curves = [row for row in assessment["curves"] if row["population"] != "null"
                           and row["target"] == primary and row["calibration_selected"]]
        half_ratios = [row["ratio"]["mean"] for row in selected_curves if row["condition"] == "half_effect"]
        double_ratios = [row["ratio"]["mean"] for row in selected_curves if row["condition"] == "double_games"]
        lines.extend([
            "next question: `penalty_selection`. which observable selection/prior assumptions can improve "
            "twelve-region recovery at a prospectively justified spatial prediction cost?", "",
            f"fixed-reference expected recovery risk is below adaptive realized recovery risk in {reference_lower}/{len(nonnull)} "
            f"non-null base/broad comparisons. eleven-mode adaptive pooling improves mean recovery in {broad_recovery}/{len(broad)} "
            f"and spatial prediction in {broad_prediction}/{len(broad)}. these contrasts change temporal assumptions, selector "
            "and sometimes representation; they do not isolate a causal mechanism.", "",
            f"the region-selected reference has a prediction cost: diffuse/base spatial prediction excess is "
            f"{reference_prediction} for gaussian/game pace, versus {adaptive_prediction} for training selection "
            "((attempts/60)^2, inverse-share-weighted). its regional potential is not a free or deployable gain.", "",
            f"broad lateral mean recovery error increases in {lateral_worse}/2 game-pace cells. adaptive null regional rms remains "
            f"{_number(min(null_rms))}–{_number(max(null_rms))} attempts/60. fixed half-effect recovery/zero ratios are "
            f"{_number(min(half_ratios))}–{_number(max(half_ratios))}; independent double-game ratios are "
            f"{_number(min(double_ratios))}–{_number(max(double_ratios))}. neither condition has adaptive assessment.", "",
        ])
    else:
        lines.extend([f"next question: `{question}`.", ""])
    lines.extend([
        "no new campaign, narrower supported product claim or admission follows. "
        "constant pooling can bias changing players; eleven modes lose spatial detail; "
        "the finite grid and conditional intervals do not establish universal information limits.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return dict(reports=[identity(path), table, limits], figures=[figure], next_question=question)
