"""render 04l's saved compact accounting; original scientific inputs stay closed."""

import csv
import json
from pathlib import Path
import time

from hockey_stats.artifacts import (
    artifact, clean_implementation, linked_path, require, resources, write_json,
)
from hockey_stats.chance_cli import identity, output_path, read_json


CELLS = ("gaussian_half", "gaussian_base", "gaussian_double", "gaussian_null", "game_shared_base")
ROLES = ("offense", "attempts_allowed")
RECEIVERS = ("all", "stable", "reversal", "onset", "no_prior_observation")
ALLOCATIONS = ("signal_allocation", "noise_allocation", "carry_allocation")
QUADRATICS = ("signal_error_square", "noise_square", "carry_square",
              "signal_noise_cross", "signal_carry_cross", "noise_carry_cross")
COMPARISONS = ("regional_mse", "regional_rms", "within_20_ft_mse", "lateral_redistribution_mse",
               "recovery_benefit", "directional_bias", "prediction_excess", "prediction_cost")
KEYS = ("cell", "role", "receiver", "operator", "arm", "metric", "source_group", "source_role")
LABEL = "simulated effects on observed deployment; no player ability estimates"
LOSS_UNITS = "(recorded unblocked attempts/60)²"


def _number(value):
    return "unavailable" if value is None else f"{value:.5g}"


def _interval(row):
    if row["mean"] is None:
        return "unavailable: " + row["reason"]
    return f"{_number(row['mean'])} [{_number(row['ci_low'])}, {_number(row['ci_high'])}]"


def _label(value):
    return value.replace("_", " ")


def _summary_index(diagnosis):
    index = {}
    for row in diagnosis["summary_rows"]:
        key = tuple(row[name] for name in KEYS)
        require(key not in index, "duplicate saved summary key")
        index[key] = row
    return index


def _row(index, cell, role, receiver, metric, arm="paired_change"):
    operator = "same_deployment" if metric == "prediction_cost" else "twelve_region_vector"
    key = (cell, role, receiver, operator, arm, metric, None, None)
    require(key in index, "missing saved report summary: " + str(key))
    return index[key]


def _table(output, name, rows, purpose):
    require(bool(rows), "empty saved report table: " + name)
    metadata = dict(study_label=LABEL, purpose=purpose)
    if name == "scales.csv":
        metadata["scale_interpretation"] = (
            "a and q are relative-rate coefficient variances; selected_exponent is "
            "log10(selected variance), not a physical attempt-rate scale")
    else:
        metadata["sign_convention"] = (
            "paired_change and prediction_cost: positive harm; recovery_benefit: "
            "positive improvement; cross terms retain signs")
    fields = list(metadata)
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    path = output / name
    with path.open("x", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            values = {key: json.dumps(value, allow_nan=False, ensure_ascii=False)
                      if isinstance(value, (dict, list, tuple)) else value for key, value in row.items()}
            writer.writerow(dict(values, **metadata))
    return identity(path)


def _figure(output, diagnosis, index):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    panels = [(cell, role) for cell in ("gaussian_base", "gaussian_null") for role in ROLES]
    selected = [[_row(index, cell, role, receiver, "loss_change") for receiver in RECEIVERS]
                for cell, role in panels]
    matrices = [[[ _row(index, cell, role, receiver, metric)["mean"] for metric in ALLOCATIONS]
                 for receiver in RECEIVERS] for cell, role in panels]
    bound = max((abs(value) for matrix in matrices for row in matrix for value in row
                 if value is not None), default=1.) or 1.
    limits = {}
    for cell in ("gaussian_base", "gaussian_null"):
        endpoints = [row[key] for (panel_cell, _), rows in zip(panels, selected, strict=True)
                     if panel_cell == cell for row in rows for key in ("ci_low", "ci_high")
                     if row[key] is not None]
        lower, upper = min([0., *endpoints]), max([0., *endpoints])
        margin = max((upper - lower) * .07, 1e-12)
        limits[cell] = (lower - margin, upper + margin)
    figure, axes = plt.subplots(4, 2, figsize=(14.5, 13), gridspec_kw={"width_ratios": (1.3, 1.)})
    for (cell, role), rows, matrix, (interval_axis, matrix_axis) in zip(
            panels, selected, matrices, axes, strict=True):
        for position, row in enumerate(rows):
            if row["mean"] is None:
                interval_axis.text(.02, position, "unavailable: " + row["reason"], fontsize=7,
                                   transform=interval_axis.get_yaxis_transform())
            else:
                interval_axis.plot([row["ci_low"], row["ci_high"]], [position] * 2,
                                   color="#384f65", linewidth=1.5)
                interval_axis.plot(row["mean"], position, "o", color="#384f65", markersize=4)
        interval_axis.axvline(0, color="#777777", linewidth=.8)
        interval_axis.set_xlim(*limits[cell])
        interval_axis.set_yticks(range(len(RECEIVERS)),
            [f"{_label(receiver)} (n={row['n_players']})" for receiver, row in zip(RECEIVERS, rows, strict=True)])
        interval_axis.set_ylim(len(RECEIVERS) - .5, -.5)
        interval_axis.grid(axis="x", alpha=.18)
        interval_axis.set_title(f"{_label(cell)}; {_label(role)}", loc="left", fontsize=10)
        interval_axis.tick_params(labelsize=8)
        values = np.array([[np.nan if value is None else value for value in row] for row in matrix])
        image = matrix_axis.imshow(np.ma.masked_invalid(values), cmap="RdBu_r", vmin=-bound,
                                   vmax=bound, aspect="auto")
        for y, row in enumerate(matrix):
            for x, value in enumerate(row):
                matrix_axis.text(x, y, _number(value), ha="center", va="center", fontsize=8,
                    color="white" if value is not None and abs(value) > .55 * bound else "black")
        matrix_axis.set_xticks(range(3), ["current signal", "realized noise", "history carry"])
        matrix_axis.set_yticks(range(len(RECEIVERS)), [_label(receiver) for receiver in RECEIVERS])
        matrix_axis.tick_params(labelsize=8)
        matrix_axis.set_title("signed symmetric allocations; sum = paired loss change", fontsize=10)
    axes[-1, 0].set_xlabel("borrowing − independent regional mse\n" + LOSS_UNITS + "; positive = harm", fontsize=9)
    axes[-1, 1].set_xlabel(LOSS_UNITS + "; positive = harm", fontsize=9)
    color_axis = figure.add_axes((.91, .23, .012, .54))
    figure.colorbar(image, cax=color_axis).set_label("signed allocation; positive = harm", fontsize=9)
    fixture = "fixture software exercise; no research conclusion\n" if diagnosis["purpose"] == "fixture_exercise" else ""
    figure.suptitle(fixture + LABEL, fontsize=12, y=.985)
    count = selected[0][0]["n_records"]
    figure.text(.02, .025, f"{count} paired records; 95% t intervals measure monte carlo error under fixed truth/design/noise. "
        "no player intervals.\ninterval axes share scales within each cell; base and null scales differ. "
        "the signed matrix uses one common color scale.\nall five cells remain in decision.md and csv; cells share histories. "
        "allocations interact and are not causal shares. positive attempts allowed means more allowed.", fontsize=8)
    figure.subplots_adjust(left=.22, right=.88, top=.93, bottom=.10, wspace=.66, hspace=.60)
    path = output / "accounting.png"
    figure.savefig(path, dpi=160, facecolor="white")
    plt.close(figure)
    return identity(path)


def _decision(output, diagnosis, index):
    fixture = diagnosis["purpose"] == "fixture_exercise"
    lines = ["# saved annual-prior accounting", "", LABEL, "",
        "this fixture supplies software evidence only; it cannot recommend scientific work." if fixture else
        diagnosis["diagnostic_answer"], "",
        "positive loss change means borrowing harms recovery; negative means improvement. "
        "brackets are two-sided 95% monte carlo intervals across paired histories.", "",
        "| primary cell | role | receiver | players | borrowing − independent mse | signal | noise | carry |",
        "|---|---|---|---:|---:|---:|---:|---:|"]
    for cell in ("gaussian_base", "gaussian_null"):
        for role in ROLES:
            for receiver in RECEIVERS:
                row = _row(index, cell, role, receiver, "loss_change")
                values = [_number(_row(index, cell, role, receiver, metric)["mean"]) for metric in ALLOCATIONS]
                lines.append(f"| {cell} | {_label(role)} | {_label(receiver)} | {row['n_players']} | "
                             f"{_interval(row)} | {' | '.join(values)} |")
    lines += ["", "all loss changes, allocations and quadratic terms use " + LOSS_UNITS + ". "
        "the denominator is twelve times each selected receiver count. receiver flags overlap; counts cannot be summed. "
        "null trajectory labels are bookkeeping, not changes in a zero truth.", "",
        "| sensitivity cell | role | all | stable | reversal | onset | no prior observation |",
        "|---|---|---:|---:|---:|---:|---:|"]
    for cell in CELLS:
        for role in ROLES:
            values = [_interval(_row(index, cell, role, receiver, "loss_change")) for receiver in RECEIVERS]
            lines.append(f"| {cell} | {_label(role)} | {' | '.join(values)} |")
    lines += ["", "these are the same signed paired loss changes and intervals in every cell; "
        "the five cells are sensitivities on shared histories, not independent populations.", "",
        "| cell | role | borrowing / independent / zero rms |",
        "|---|---|---:|"]
    for cell in CELLS:
        for role in ROLES:
            values = [_number(_row(index, cell, role, "all", "regional_rms", arm)["mean"])
                      for arm in ("borrowing", "independent", "zero")]
            lines.append(f"| {cell} | {_label(role)} | {' / '.join(values)} |")
    lines += ["", "rms is the saved sqrt(mean mse), in recorded unblocked attempts/60; "
        "its source-mse sd/se remain separately labeled in comparison.csv. null rms is absolute false-map error. "
        "no gain ratio is defined against zero null truth.", "",
        "| cell | same-deployment prediction cost, 95% interval |",
        "|---|---:|"]
    for cell in CELLS:
        lines.append(f"| {cell} | {_interval(_row(index, cell, 'both', 'all', 'prediction_cost', 'paired_cost'))} |")
    lines += ["", "prediction cost is borrowing minus independent excess against the same fitted-context "
        "zero-player baseline, with the original directed-hour denominator and " + LOSS_UNITS + ". "
        "positive is harm. the unchanged original recovery benefits, near/lateral functionals, prediction "
        "excesses and their denominator/zero-target rules remain in comparison.csv.", "",
        "| primary cell | role | receiver | arm | signal error² | noise² | carry² | signal × noise | signal × carry | noise × carry |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for cell in ("gaussian_base", "gaussian_null"):
        for role in ROLES:
            for receiver in ("all", "no_prior_observation"):
                for arm in ("borrowing", "independent"):
                    values = [_number(_row(index, cell, role, receiver, metric, arm)["mean"]) for metric in QUADRATICS]
                    lines.append(f"| {cell} | {_label(role)} | {_label(receiver)} | {arm} | {' | '.join(values)} |")
    lines += ["", "cross columns include the factor of two and retain negative cancellation. all six terms sum "
        "to each arm's mse. signal error includes omitted native detail, shrinkage and player mixing. "
        "selected covariances depend on responses: noise need not average to zero, its square is not sampling "
        "variance, and this is not a classical bias–variance decomposition.", "",
        "| primary cell | role | no-prior players | reference allocation | update allocation | total carry |",
        "|---|---|---:|---:|---:|---:|"]
    for cell in ("gaussian_base", "gaussian_null"):
        for role in ROLES:
            row = _row(index, cell, role, "no_prior_observation", "carry_allocation")
            values = [_number(_row(index, cell, role, "no_prior_observation", metric)["mean"])
                      for metric in ("reference_carry_allocation", "update_carry_allocation", "carry_allocation")]
            lines.append(f"| {cell} | {_label(role)} | {row['n_players']} | {' | '.join(values)} |")
    lines += ["", "a no-prior player's personal incoming mean is zero. exposure centering can still shift its "
        "reference, and coupled updating can transmit other input rows. these are noncausal channels under "
        "the frozen prior/reference convention. accounting.csv retains all eight source-mask allocations "
        "for every receiving cohort; history-only direct carry is zero. source masks trace saved rows, "
        "not ultimate historical origins or named-teammate causal influence.", "",
        "intervals measure monte carlo error for response-dependent statistics under the fixed truth, design "
        "and declared noise law. scales/covariances vary across records; intervals do not condition on the "
        "realized fitted states. they are not player intervals or population uncertainty. crossing zero "
        "establishes neither equivalence nor acceptable prediction cost.", ""]
    decision = diagnosis["decision"]
    if decision["next_hypothesis"] is None:
        lines += ["next hypothesis: none.", ""]
        if not fixture:
            lines += ["unresolved: `" + decision["unresolved_reason"] + "`. "
                "the allocations and scale receipts do not distinguish inherited variance, carried covariance, "
                "selected update scale and coupling as an actionable intervention. no further diagnosis or "
                "experiment follows automatically.", ""]
    else:
        require(not fixture, "fixture cannot recommend scientific work")
        lines += ["one next hypothesis, as saved by the diagnosis:", "", "```json",
                  json.dumps(decision["next_hypothesis"], indent=2, ensure_ascii=False), "```", ""]
    lines += ["- " + limit for limit in diagnosis["limitations"]]
    lines += ["", "scale receipts are supporting context only; no refit, entry-prior reset, scale reselection, "
        "prediction threshold or new scientific gate is evaluated. truth-defined reversal/onset labels are "
        "assessment inputs only. no causal isolation, real-player support or private-model parity is established.", "",
        "`nomination:null, admission:not_admitted, handoff:null`.", "",
        "[paired intervals and signed terms](accounting.png) · [frozen comparisons](comparison.csv) · "
        "[complete accounting](accounting.csv) · [scale receipts](scales.csv) · [verification](verification.md)", ""]
    path = output / "decision.md"
    with path.open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines))
    return identity(path)


def render(diagnosis_path: Path, output: Path):
    """copy saved numeric rows and render their labels; never follow scientific input refs."""
    started = time.monotonic()
    diagnosis_path = Path(diagnosis_path).resolve(strict=True)
    diagnosis = read_json(diagnosis_path)
    require(diagnosis.get("schema_version") == 1 and diagnosis.get("kind") == "attribution_prior_diagnosis"
            and diagnosis.get("purpose") in ("research", "fixture_exercise"), "expected schema-1 prior diagnosis")
    require(diagnosis["execution_status"] == "complete" and diagnosis["numerical_status"] == "verified",
            "report requires a complete verified diagnosis")
    if diagnosis["purpose"] == "research":
        clean_implementation(diagnosis["implementation"])
    protocol_path = linked_path(diagnosis["consumed"]["protocol"])
    protocol = read_json(protocol_path)
    require(protocol.get("schema_version") == 1 and protocol.get("kind") == "attribution_prior_protocol"
            and protocol.get("purpose") == diagnosis["purpose"], "report protocol identity differs")
    index = _summary_index(diagnosis)
    output = output_path(str(output), [str(diagnosis_path.parent), str(protocol_path.parent)])
    output.mkdir()
    rows = [dict(row_type=kind, **row) for kind, key in (("record", "record_rows"), ("summary", "summary_rows"))
            for row in diagnosis[key]]
    reports = [_table(output, name, [row for row in rows if (row["metric"] in COMPARISONS) == comparison],
                      diagnosis["purpose"])
               for name, comparison in (("comparison.csv", True), ("accounting.csv", False))]
    reports.append(_table(output, "scales.csv", diagnosis["scale_rows"], diagnosis["purpose"]))
    figure = _figure(output, diagnosis, index)
    reports.append(_decision(output, diagnosis, index))
    reference = identity(diagnosis_path)
    lines = ["# saved prior-accounting verification", "", LABEL, "",
        "the fixture supplies software verification only." if diagnosis["purpose"] == "fixture_exercise" else
        "the diagnosis owns all scientific calculations and numerical closure checks.", "",
        f"saved diagnosis: `{reference['path']}`; sha256 `{reference['sha256']}`.", "",
        "reporting reads only this compact diagnosis and its bound protocol. original arrays, source manifests, "
        "fitted states and parent assessment are not opened. tables copy saved record/summary/scale rows; "
        "rendering computes no scientific scores, intervals, rms or recommendations.", ""]
    for name in ("inventory", "read_accounting", "closure_summary", "preflight_resources", "resources"):
        lines += [name.replace("_", " ") + ":", "", "```json", json.dumps(diagnosis[name], indent=2), "```", ""]
    lines += ["the complete record-level receipts remain in the saved diagnosis; the summary above is copied "
        "from that diagnosis, without recalculation.", "",
        "the bounded base-record-zero preflight belongs to the same frozen inventory. no research solve "
        "or scale evaluation is authorized. numerical completion establishes accounting closure, not a "
        "scientific pass/fail, acceptable cost or model admission.", "",
        "`nomination:null, admission:not_admitted, handoff:null`.", ""]
    path = output / "verification.md"
    with path.open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines))
    reports.append(identity(path))
    fixture = diagnosis["purpose"] == "fixture_exercise"
    result = artifact("attribution_prior_result", diagnosis["purpose"],
        dict(diagnosis=reference, protocol=diagnosis["consumed"]["protocol"]), schema_version=1,
        execution_status="complete", numerical_status="verified", study_status="fixture_verified" if fixture else "diagnosed",
        nomination=None, admission="not_admitted", handoff=None, **diagnosis["decision"],
        inventory=diagnosis["inventory"], reports=reports, figures=[figure], resources=resources(started))
    path = output / "result.json"
    write_json(path, result)
    return identity(path)
