"""04k's saved-assessment tables and conditional diagnostic comparison."""

import csv
import json
from pathlib import Path
import time

import numpy as np

from hockey_stats.artifacts import artifact, read_artifact, require, resources, write_json
from hockey_stats.chance_cli import identity, output_path


STUDY_LABEL = "simulated effects on observed deployment — not player ability estimates"
CELLS = ("gaussian_half", "gaussian_base", "gaussian_double", "gaussian_null", "game_shared_base")
ROLES = ("offense", "attempts_allowed")
ARMS = ("borrowing", "independent", "zero")
COLORS = ("#21618c", "#b35806", "#666666")


def _number(value):
    return "unavailable" if value is None else f"{value:.5g}"


def _interval(row):
    return f"{_number(row['mean'])} [{_number(row['ci_low'])}, {_number(row['ci_high'])}]"


def _summary(assessment, cell, role, cohort, metric, arm):
    operator = "same_deployment" if metric == "prediction_cost" else "twelve_region_vector"
    rows = [row for row in assessment["comparison_rows"]
            if (row["cell"], row["role"], row["cohort"], row["metric"], row["arm"])
            == (cell, role, cohort, metric, arm) and row["operator"] == operator]
    require(len(rows) == 1, f"report requires one summary for {cell}/{role}/{cohort}/{metric}/{arm}")
    return rows[0]


def _write_table(output, name, rows, purpose):
    require(bool(rows), f"{name} has no report rows")
    fields = ["study_label", "purpose"]
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    path = output / name
    with path.open("x", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            values = {key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                      if isinstance(value, (dict, list, tuple)) else value
                      for key, value in row.items()}
            writer.writerow(dict(values, study_label=STUDY_LABEL, purpose=purpose))
    return identity(path)


def _study_resources(assessment):
    costs = assessment["fit_resources"]
    return dict(preparation=assessment["preparation_resources"],
        primary_fits=dict(pairs=len(costs), wall_seconds=sum(row["wall_seconds"] for row in costs),
            peak_memory_bytes=max(row["peak_memory_bytes"] for row in costs),
            output_bytes=sum(row["output_bytes"] for row in costs)),
        preflight_gaussian_base_0=assessment["preflight_resources"], assessment=assessment["resources"])


def _figure(output, assessment):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(16.2, 8.2))
    grid = figure.add_gridspec(2, 3, height_ratios=(1.8, 1), hspace=.75, wspace=.32)
    axes = [figure.add_subplot(grid[0, index]) for index in range(3)]
    recovery_max = 0.
    for axis, role in zip(axes[:2], ROLES, strict=True):
        for index, cell in enumerate(CELLS):
            for offset, arm, color in zip((-.2, 0., .2), ARMS, COLORS, strict=True):
                row = _summary(assessment, cell, role, "all", "regional_mse", arm)
                if row["mean"] is None:
                    axis.text(0, index + offset, row["reason"], fontsize=7)
                    continue
                mean, low, high = np.sqrt(np.maximum(0., [row["mean"], row["ci_low"], row["ci_high"]]))
                axis.plot([low, high], [index + offset] * 2, color=color, linewidth=1.4)
                axis.plot(mean, index + offset, "o", color=color, markersize=4,
                          label=arm if index == 0 else None)
                recovery_max = max(recovery_max, high)
        axis.axvline(0, color="#777777", linewidth=.8)
        count = _summary(assessment, "gaussian_base", role, "all", "regional_mse", "borrowing")["n_players"]
        axis.set_title(role.replace("_", " ") + f" regional recovery (n={count})", fontsize=11)
        axis.set_xlabel("rms recorded unblocked attempts/60\nlower is less map error", fontsize=9)
        axis.set_yticks(range(len(CELLS)), [cell.replace("_", " ") for cell in CELLS])
        axis.invert_yaxis()
        axis.grid(axis="x", alpha=.18)
        axis.tick_params(labelsize=8)
    for axis in axes[:2]:
        axis.set_xlim(-.035 * recovery_max, max(recovery_max * 1.06, 1e-12))
    axes[1].set_yticklabels([])
    axes[0].legend(fontsize=8, frameon=False, loc="lower right")

    axis = axes[2]
    for index, cell in enumerate(CELLS):
        row = _summary(assessment, cell, "both", "all", "prediction_cost", "paired_cost")
        if row["mean"] is None:
            axis.text(0, index, row["reason"], fontsize=7)
            continue
        axis.plot([row["ci_low"], row["ci_high"]], [index] * 2, color="#6b4c7b", linewidth=1.5)
        axis.plot(row["mean"], index, "o", color="#6b4c7b", markersize=4)
    axis.axvline(0, color="#777777", linewidth=.8)
    axis.set_title("same-deployment prediction cost", fontsize=11)
    axis.set_xlabel("borrowing − independent excess\n(recorded unblocked attempts/60)²; positive is cost", fontsize=9)
    axis.set_yticks(range(len(CELLS)), [cell.replace("_", " ") for cell in CELLS])
    axis.invert_yaxis()
    axis.grid(axis="x", alpha=.18)
    axis.tick_params(labelsize=8)

    harms = [figure.add_subplot(grid[1, index]) for index in range(2)]
    harm_min, harm_max = 0., 0.
    for axis, role in zip(harms, ROLES, strict=True):
        cohort_labels = []
        for index, cohort in enumerate(("stable", "reversal", "onset", "no_prior_observation")):
            row = _summary(assessment, "gaussian_base", role, cohort, "recovery_benefit", "paired_benefit")
            label = cohort.replace("_", " ")
            cohort_labels.append(f"{label} (n={row['n_players']})")
            if row["mean"] is None:
                axis.text(0, index, row["reason"], fontsize=7)
                continue
            mean, low, high = -row["mean"], -row["ci_high"], -row["ci_low"]
            axis.plot([low, high], [index] * 2, color="#a13e35", linewidth=1.5)
            axis.plot(mean, index, "o", color="#a13e35", markersize=4)
            harm_min, harm_max = min(harm_min, low), max(harm_max, high)
        axis.axvline(0, color="#777777", linewidth=.8)
        axis.set_title("gaussian base: " + role.replace("_", " "), fontsize=10)
        axis.set_xlabel("borrowing − independent regional mse\n(recorded unblocked attempts/60)²; positive is harm", fontsize=8)
        axis.set_yticks(range(4), cohort_labels)
        axis.invert_yaxis()
        axis.tick_params(labelsize=8)
        axis.grid(axis="x", alpha=.18)
    margin = max((harm_max - harm_min) * .06, 1e-12)
    for axis in harms:
        axis.set_xlim(harm_min - margin, harm_max + margin)
    harms[1].set_yticklabels([])
    annotation = figure.add_subplot(grid[1, 2])
    annotation.axis("off")
    n_records = _summary(assessment, "gaussian_base", "offense", "all", "regional_mse", "borrowing")["n_records"]
    annotation.text(0, 1, f"{n_records} paired noise histories per cell\n"
        "95% t intervals for mean simulation performance\n"
        "rms = sqrt(mean mse); transformed mse endpoints\n\n"
        "one fixed truth and observed deployment population\n"
        "cells share gaussian histories; do not pool them\n"
        "positive attempts-allowed effects mean more allowed\n"
        "cohort flags overlap; their counts cannot be summed\n"
        "no player intervals or scientific pass/fail gate",
        va="top", fontsize=8, linespacing=1.65)
    fixture = "fixture exercise; no research conclusion\n" if assessment["purpose"] == "fixture_exercise" else ""
    figure.suptitle(fixture + STUDY_LABEL, fontsize=12, y=.98)
    figure.subplots_adjust(left=.13, right=.98, top=.88, bottom=.09)
    path = output / "comparison.png"
    require(not path.exists(), "figure output already exists")
    figure.savefig(path, dpi=160, facecolor="white")
    plt.close(figure)
    return identity(path)


def render_reports(output, assessment, assessment_reference):
    """format saved numeric rows without loading truth, source or fitted arrays."""
    output = Path(output)
    reports = [_write_table(output, name + ".csv", assessment[key], assessment["purpose"])
               for name, key in (("design", "design_rows"), ("truth", "truth_rows"),
                                ("metrics", "metric_rows"), ("comparison", "comparison_rows"),
                                ("diagnostics", "diagnostic_rows"))]
    player_rows = []
    for row in assessment["player_rows"]:
        exported = {key: value for key, value in row.items()
                    if key not in ("target", "mean_error", "mean_squared_error")}
        for metric in ("target", "mean_error", "mean_squared_error"):
            exported.update({metric + "_" + region: value for region, value in
                             zip(assessment["region_names"], row[metric], strict=True)})
        player_rows.append(exported)
    reports.append(_write_table(output, "players.csv", player_rows, assessment["purpose"]))
    figure = _figure(output, assessment)
    fixture = assessment["purpose"] == "fixture_exercise"
    lines = ["# annual borrowing on observed deployment", "", STUDY_LABEL, "",
             f"purpose: `{assessment['purpose']}`; execution: `{assessment['execution_status']}`; "
             f"numerics: `{assessment['numerical_status']}`.", "",
             "this fixture exercises software contracts and supplies no research conclusion." if fixture
             else assessment["diagnostic_answer"], "",
             "| cell | role | borrowing / independent / zero regional rms | independent − borrowing mse, 95% interval |",
             "|---|---|---:|---:|"]
    for cell in CELLS:
        for role in ROLES:
            rms = []
            for arm in ARMS:
                row = _summary(assessment, cell, role, "all", "regional_mse", arm)
                rms.append(_number(np.sqrt(row["mean"])) if row["mean"] is not None else "unavailable")
            benefit = _summary(assessment, cell, role, "all", "recovery_benefit", "paired_benefit")
            lines.append(f"| {cell} | {role.replace('_', ' ')} | {' / '.join(rms)} | {_interval(benefit)} |")
    lines.extend(["", "rms uses sqrt(mean regional mse), in recorded unblocked attempts/60. "
                  "regional mse divides by twelve times the selected player-role count. "
                  "near and lateral diagnostics use their own single-functional denominators.", "",
                  "| cell | borrowing − independent prediction excess, 95% interval |",
                  "|---|---:|"])
    for cell in CELLS:
        row = _summary(assessment, cell, "both", "all", "prediction_cost", "paired_cost")
        lines.append(f"| {cell} | {_interval(row)} |")
    lines.extend(["", "prediction cost and recovery benefit use (recorded unblocked attempts/60)². "
                  "negative prediction excess is retained; positive paired cost means borrowing harms prediction. "
                  "the reference is the same fitted-context zero-player predictor on identical deployment.", "",
                  "| gaussian base cohort | role | count | independent − borrowing regional mse, 95% interval |",
                  "|---|---|---:|---:|"])
    for cohort in ("stable", "reversal", "onset", "no_prior_observation"):
        for role in ROLES:
            row = _summary(assessment, "gaussian_base", role, cohort, "recovery_benefit", "paired_benefit")
            lines.append(f"| {cohort.replace('_', ' ')} | {role.replace('_', ' ')} | "
                         f"{row.get('n_players', 'see csv')} | {_interval(row)} |")
    lines.extend(["", "negative cohort benefit means borrowing harm. injected changes start at the final season; "
                  "entry/return flags describe this corpus, not nhl debut or actual ability change. "
                  "minute, returner, template, near/lateral and directional-bias diagnostics appear in "
                  "[diagnostics.csv](diagnostics.csv). cohort flags overlap and cannot be summed.", "",
                  "the gaussian null cell reports absolute false-map error against the zero map. "
                  "zero-target ratios are unavailable. endpoint winners and bounded-search limitations are "
                  "reported without expanding the grid.", "",
                  "intervals describe monte carlo error across paired records, conditional on one fixed truth/deployment "
                  "population and the declared gaussian laws. they are neither player intervals nor uncertainty over "
                  "plausible populations. cells share noise histories. crossing zero establishes neither equivalence "
                  "nor acceptable prediction cost. no winner, nominee or scientific pass/fail gate is assigned.", ""])
    lines.extend("- " + limit for limit in assessment["limits"])
    if assessment["numerical_status"] == "unresolved":
        lines.extend(["", "unresolved: " + assessment["unresolved_reason"]])
    elif not fixture:
        lines.extend(["", "next question: " + assessment["next_question"]])
    lines.extend(["", "`nomination:null, admission:not_admitted, handoff:null`.", "",
                  "[comparison and intervals](comparison.png) · [all metric records](metrics.csv) · "
                  "[audit players](players.csv) · [verification](verification.md)", ""])
    path = output / "decision.md"
    with path.open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines))
    reports.append(identity(path))

    lines = ["# annual-borrowing verification", "", STUDY_LABEL, "",
             f"purpose: `{assessment['purpose']}`; numerical status: `{assessment['numerical_status']}`.", "",
             "this fixture supplies software verification only." if fixture else "the saved assessment owns all numeric checks.", "",
             f"exact checks, candidates and substitutions: [saved assessment]({assessment_reference['path']}) "
             f"(sha256 `{assessment_reference['sha256']}`).", "",
             "inventory:", "", "```json", json.dumps(assessment["inventory"], indent=2), "```", "",
             "checks:", "", "```json", json.dumps(assessment["verification_checks"], indent=2), "```", "",
             "| cell / arm / season | probe | saved scale limits | native / regional map change, relative to league rate | max mean movement / mc se |",
             "|---|---|---|---:|---:|"]
    for probe in assessment["probes"]:
        movement = probe["maximum_league_relative_current_player_movement"]
        limits = probe["saved_scale_status"]
        shifts = [abs(row["movement_in_mc_se"]) for row in probe["metric_movement"]
                  if row["movement_in_mc_se"] is not None]
        lines.append(f"| {probe['cell']} / {probe['arm']} / {probe['season']} | {probe['status']} | "
                     f"{limits['status']}; {', '.join(limits['own_reasons']) or 'no own limits'}; "
                     f"inherited: {str(limits['inherited_limitation']).lower()} | "
                     f"{_number(movement['native_cells'])} / {_number(movement['regions'])} | "
                     f"{_number(max(shifts)) if shifts else 'unavailable; no nonzero mc se'} |")
    lines.extend(["", "probe map changes are bounded by 1e-4 times the relevant season rate. "
                  "incoming priors stay fixed; these are conditional numerical checks. no primary state is replaced. "
                  "missing mc se ratios remain unavailable; exact metric movements and reasons remain in the assessment.", "",
             "resources:", "", "```json", json.dumps(_study_resources(assessment), indent=2), "```", "",
             "reports read saved assessment rows only. no recorded responses or fitted arrays are decoded. "
             "unexpected missing pairs prevent assessment completion; no scientific gate is introduced.", "",
             "`nomination:null, admission:not_admitted, handoff:null`.", ""])
    path = output / "verification.md"
    with path.open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines))
    reports.append(identity(path))
    return dict(reports=reports, figures=[figure])


def report(assessment, output):
    started = time.monotonic()
    source = Path(assessment).resolve(strict=True)
    assessment = read_artifact(source, "attribution_history_assessment", expected_schema=1)
    require(assessment["execution_status"] == "complete", "report requires a complete assessment")
    require(assessment["numerical_status"] in ("verified", "unresolved"), "unknown assessment numerical status")
    output = output_path(str(output), [str(source.parent)])
    output.mkdir()
    reference = identity(source)
    reports = render_reports(output, assessment, reference)
    fixture = assessment["purpose"] == "fixture_exercise"
    verified = assessment["numerical_status"] == "verified"
    result = artifact("attribution_history_result", assessment["purpose"],
        dict(assessment=reference, prepared=assessment["consumed"]["prepared"],
             protocol=assessment["consumed"]["protocol"]), schema_version=1,
        study_label=STUDY_LABEL, execution_status="complete", numerical_status=assessment["numerical_status"],
        study_status=("fixture_verified" if fixture else "diagnosed") if verified else "numerically_unresolved",
        nomination=None, admission="not_admitted", handoff=None,
        next_question=None if fixture or not verified else assessment["next_question"],
        unresolved_reason=assessment.get("unresolved_reason") if not verified else None,
        inventory=assessment["inventory"], resources=dict(_study_resources(assessment), report=resources(started)),
        **reports)
    path = output / "result.json"
    write_json(path, result)
    return identity(path)
