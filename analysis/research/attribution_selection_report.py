"""04i's paired comparison, adjacent diagnostics and interval figure."""

import csv
from pathlib import Path

import numpy as np

from hockey_stats.artifacts import load_arrays, require
from hockey_stats.chance_cli import identity


ARM_LABELS = dict(candidate="pooled history, regional-score selection, 11 spatial modes",
    control="pooled history, marginal-likelihood selection, 11 spatial modes")
TARGET_LABELS = dict(twelve_region_vector="twelve-region vector",
    within_20_ft="within 20 ft, in front of goal", lateral_redistribution="lateral redistribution")


def _number(value):
    return "unavailable" if value is None else f"{value:.5g}"


def _interval(value):
    if value["mean"] is None:
        return "unavailable"
    return f"{_number(value['mean'])} [{_number(value['lower'])}, {_number(value['upper'])}]"


def _figure(output, assessment):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [row for row in assessment["cells"] if row["population"] != "null"]
    require([(row["population"], row["law"]) for row in rows] ==
        [(population, law) for population in ("sparse", "diffuse") for law in ("gaussian", "game_pace")],
        "figure requires four ordered non-null cells")
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    titles = ("regional recovery benefit", "99% prediction-gain retention margin")
    keys = ("regional_benefit", "retention_margin")
    for axis, key, title in zip(axes, keys, titles, strict=True):
        axis.axvline(0, color="#555555", linewidth=1)
        for y, row in enumerate(rows):
            summary = row[key]
            axis.plot([summary["lower"], summary["upper"]], [y, y], color="#255b83", linewidth=2)
            axis.plot(summary["mean"], y, "o", color="#255b83", markersize=5)
            axis.plot([summary["lower"]]*2, [y-.06, y+.06], color="#255b83", linewidth=1)
            axis.plot([summary["upper"]]*2, [y-.06, y+.06], color="#255b83", linewidth=1)
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("recorded unblocked (attempts/60)²\npositive favors candidate", fontsize=9)
        axis.grid(axis="x", alpha=.18)
        axis.tick_params(axis="both", labelsize=9)
    axes[0].set_yticks(range(4), [f"{row['population']} / {row['law'].replace('_', ' ')}" for row in rows])
    axes[0].invert_yaxis()
    fixture = "fixture exercise; no research conclusion\n" if assessment["purpose"] == "fixture_exercise" else ""
    figure.suptitle(f"{fixture}observable regional penalty selection\n"
        "95% intervals for mean experimental performance", fontsize=12)
    figure.text(.5, .045,
        "conditional on fixed designs and exposed truth populations; no player intervals or simultaneous bands\n"
        "benefit = control risk − candidate risk; margin = candidate gain − .99 × control gain",
        ha="center", fontsize=8)
    figure.subplots_adjust(left=.16, right=.98, top=.77, bottom=.23, wspace=.24)
    path = output/"selection.png"
    require(not path.exists(), "figure output already exists")
    figure.savefig(path, dpi=150, facecolor="white")
    plt.close(figure)
    return identity(path)


def render_reports(output, assessment):
    output = Path(output)
    path = output/"comparison.csv"
    fields = ("record_type", "population", "law", "outer", "target", "partition", "arm", "arm_label",
        "metric", "mean", "lower", "upper", "reason", "status", "prior_variance")
    with path.open("x", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        for row in assessment["cells"]:
            for metric, summary in row.items():
                if isinstance(summary, dict) and "mean" in summary:
                    writer.writerow(dict(record_type="comparison", population=row["population"], law=row["law"],
                        metric=metric, **summary, status=row["progress_status"]))
            for criterion, status in row["criteria"].items():
                writer.writerow(dict(record_type="criterion", population=row["population"], law=row["law"],
                    metric=criterion, status=status, reason=row["reason"]))
        for row in assessment["diagnostics"]:
            labels = {key: row[key] for key in ("population", "law", "target", "partition", "arm") if key in row}
            if "arm" in row:
                labels["arm_label"] = ARM_LABELS[row["arm"]]
            for metric, summary in row.items():
                if isinstance(summary, dict) and "mean" in summary:
                    writer.writerow(dict(record_type="diagnostic_"+row["kind"], **labels, metric=metric, **summary))
        for row in assessment["selections"]:
            for arm in ("candidate", "control"):
                for count in row[arm]:
                    writer.writerow(dict(record_type="selection", population=row["population"], law=row["law"],
                        arm=arm, arm_label=ARM_LABELS[arm], metric="count", mean=count["count"],
                        prior_variance=count["prior_variance"]))
        for row in assessment["errors"]:
            arrays = load_arrays(row["arrays"])
            for index, outer in enumerate(arrays["outer_ids"]):
                metrics = dict(regional_benefit=arrays["control_risk"][index, 0]-arrays["candidate_risk"][index, 0],
                    control_gain=-arrays["control_prediction_excess"][index],
                    candidate_gain=-arrays["candidate_prediction_excess"][index],
                    prediction_cost=arrays["candidate_prediction"][index]-arrays["control_prediction"][index],
                    prediction_allowance=-.01*arrays["control_prediction_excess"][index],
                    retention_margin=-arrays["candidate_prediction_excess"][index]+.99*arrays["control_prediction_excess"][index],
                    prediction_zero=arrays["prediction_zero"][index],
                    candidate_selected_index=arrays["candidate_selected_index"][index],
                    candidate_selected_a=arrays["candidate_selected_a"][index],
                    control_selected_a=arrays["control_selected_a"][index],
                    candidate_selected_score=arrays["candidate_selected_score"][index],
                    candidate_error_minus_zero=arrays["candidate_risk"][index, 0]-arrays["zero_risk"][index, 0],
                    post_selection_optimism=arrays["candidate_risk"][index, 0]-arrays["zero_risk"][index, 0]-arrays["candidate_selected_score"][index])
                for metric, value in metrics.items():
                    writer.writerow(dict(record_type="paired_record", population=row["population"], law=row["law"],
                        outer=int(outer), metric=metric, mean=float(value)))
                for ti, target in enumerate(TARGET_LABELS):
                    writer.writerow(dict(record_type="paired_record", population=row["population"], law=row["law"],
                        outer=int(outer), target=target, arm="zero", metric="risk", mean=arrays["zero_risk"][index, ti]))
                    for arm in ("candidate", "control"):
                        writer.writerow(dict(record_type="paired_record", population=row["population"], law=row["law"],
                            outer=int(outer), target=target, arm=arm, arm_label=ARM_LABELS[arm], metric="risk",
                            mean=arrays[f"{arm}_risk"][index, ti]))
                for arm in ("candidate", "control"):
                    for metric in ("prediction", "prediction_excess", "coupling"):
                        writer.writerow(dict(record_type="paired_record", population=row["population"], law=row["law"],
                            outer=int(outer), arm=arm, arm_label=ARM_LABELS[arm], metric=metric,
                            mean=arrays[f"{arm}_{metric}"][index]))
    comparison = identity(path)

    path = output/"diagnostics.md"
    lines = ["# adjacent diagnostics", "",
        "all risk contributions retain denominator 64; partitions are not retuned or independently normalized. "
        "negative benefit means deterioration. diagnostics qualify the conclusion and do not add vetoes.", "",
        "| population / law | target / partition | candidate risk | control risk | control − candidate, 95% interval |",
        "|---|---|---:|---:|---:|"]
    for row in assessment["diagnostics"]:
        if row["kind"] in ("target", "partition"):
            lines.append(f"| {row['population']} / {row['law'].replace('_', ' ')} | "
                f"{TARGET_LABELS[row['target']]} / {row['partition'].replace('_', ' ')} | "
                f"{_number(row['candidate_risk']['mean'])} | {_number(row['control_risk']['mean'])} | {_interval(row['benefit'])} |")
    lines.extend(["", "| population / law | diagnostic | value, 95% interval |", "|---|---|---:|"])
    for row in assessment["diagnostics"]:
        if row["kind"] in ("omitted_detail", "selected_score"):
            label = f"{TARGET_LABELS[row['target']]} / {row.get('arm', 'candidate')}"
            for key, summary in row.items():
                if isinstance(summary, dict) and "mean" in summary:
                    lines.append(f"| {row['population']} / {row['law'].replace('_', ' ')} | "
                        f"{label} / {key.replace('_', ' ')} | {_interval(summary)} |")
    lines.extend(["", "selected-score optimism compares selected score with realized candidate risk minus zero-map risk. "
        "the selected minimum is not post-selection unbiased error, prediction risk or player precision.", "",
        "| population / law | candidate zero / upper | control zero / upper |", "|---|---:|---:|"])
    for row in assessment["selections"]:
        lines.append(f"| {row['population']} / {row['law'].replace('_', ' ')} | "
            f"{row['candidate_zero']} / {row['candidate_upper']} | {row['control_zero']} / {row['control_upper']} |")
    lines.extend(["", "all eighteen variance frequencies and signed functional partitions appear in comparison.csv. "
        "the upper endpoint is 1; endpoint selection does not silently expand the grid.", ""])
    with path.open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines))
    diagnostic = identity(path)

    figure = _figure(output, assessment)
    path = output/"decision.md"
    fixture = assessment["purpose"] == "fixture_exercise"
    lines = ["# observable regional penalty selection", "",
        f"execution: `{assessment['execution_status']}`; numerics: `{assessment['numerical_status']}`; "
        f"progress: `{assessment['progress_status']}`.", ""]
    if fixture:
        lines.append("this fixture exercises the contracts and supplies no research conclusion.")
    elif assessment["progress_status"] == "supported":
        lines.append("the observable regional rule supports developmental progress in all four non-null cells: "
            "regional recovery improves, control gain is positive, and the candidate retains at least 99% of that gain.")
    elif assessment["progress_status"] == "failed":
        failures = [f"{row['population']} / {row['law'].replace('_', ' ')}: {name.replace('_', ' ')}"
            for row in assessment["cells"] if row["population"] != "null"
            for name, status in row["criteria"].items() if status == "failed"]
        lines.append("the prospective comparison fails: "+"; ".join(failures)+". partial improvements remain below.")
    elif assessment["progress_status"] == "numerically_unresolved":
        lines.append("the comparison is numerically unresolved; numerical disagreement overrides a scientific progress claim.")
    else:
        uncertainties = [f"{row['population']} / {row['law'].replace('_', ' ')}: {name.replace('_', ' ')}"
            for row in assessment["cells"] if row["population"] != "null"
            for name, status in row["criteria"].items() if status == "inconclusive"]
        lines.append("the prospective comparison is inconclusive: "+"; ".join(uncertainties)+
            ". crossing zero establishes neither equivalence nor acceptable prediction cost.")
    deteriorations = [row for row in assessment["diagnostics"] if row["kind"] in ("target", "partition")
        and row["benefit"]["mean"] < 0]
    lines.extend(["", f"{len(deteriorations)} target/partition diagnostics deteriorate in mean. "
        "each appears with its interval in [the adjacent diagnostic table](diagnostics.md); these are not extra vetoes."])
    if deteriorations:
        grouped = []
        for cell in assessment["cells"]:
            affected = [row for row in deteriorations if (row["population"], row["law"]) == (cell["population"], cell["law"])]
            if affected:
                targets = [TARGET_LABELS[target] for target in TARGET_LABELS if any(row["target"] == target for row in affected)]
                transitions = any(row["partition"].startswith(("entrant", "returner")) for row in affected)
                grouped.append(f"{cell['population']} / {cell['law'].replace('_', ' ')}: {len(affected)} "
                    f"across {', '.join(targets)}"+("; transitions included" if transitions else ""))
        lines.append("contrary diagnostics by cell: "+". ".join(grouped)+".")
    lines.extend(["", f"candidate: {ARM_LABELS['candidate']}. control: {ARM_LABELS['control']}.", "",
        "| population / law | candidate / control regional rms | regional benefit, 95% interval | candidate / control error:zero ratio | control gain, 95% interval | prediction cost / allowance | retention margin, 95% interval | benefit / gain / retention |",
        "|---|---:|---:|---:|---:|---:|---:|---|"])
    for row in assessment["cells"]:
        lines.append(f"| {row['population']} / {row['law'].replace('_', ' ')} | "
            f"{_number(row['candidate_rms']['mean'])} / {_number(row['control_rms']['mean'])} | {_interval(row['regional_benefit'])} | "
            f"{_number(row['candidate_ratio']['mean'])} / {_number(row['control_ratio']['mean'])} | {_interval(row['control_gain'])} | "
            f"{_number(row['prediction_cost']['mean'])} / {_number(row['prediction_allowance']['mean'])} | {_interval(row['retention_margin'])} | "
            f"{' / '.join(row['criteria'].values())} |")
    lines.extend(["", "regional rms = sqrt(mean regional risk / 12), in redistributed recorded unblocked attempts/60 "
        "per player-role/region. benefit, gains, cost, allowance and margin use (attempts/60)²; prediction uses "
        "the inverse-share full-lineup metric. allowance is 1% of mean control gain. ratios use mean risks; null ratios "
        "are unavailable, with absolute false-map risks shown below.", ""])
    for row in assessment["cells"]:
        if row["population"] == "null":
            lines.append(f"null / {row['law'].replace('_', ' ')} absolute false-map risk: candidate {_interval(row['candidate_risk'])}; "
                f"control {_interval(row['control_risk'])}; paired change {_interval(row['regional_benefit'])}. diagnostic only.")
    lines.extend(["", "[paired values and full diagnostics](comparison.csv) · [adjacent diagnostics](diagnostics.md) · "
        "[benefit and retention figure](selection.png)", "",
        "the figure and intervals describe mean experimental performance across complete outer records, conditional "
        "on fixed designs and exposed truth populations. they are not individual-player intervals, simultaneous bands "
        "or untouched confirmation. within-20-ft and lateral functionals retain their single-functional rms; full "
        "target denominators and signed context/projection terms are preserved.", "",
        "risk:zero ratios and .75 × mean zero risk − mean fitted risk in the csv are historical context, not gates. "
        "selection scores are not player precision, prediction risk or post-selection unbiased error.", ""])
    lines.extend(f"- {limit}" for limit in assessment["limits"])
    lines.extend(["", "`nomination:null, admission:not_admitted, handoff:null`.", ""])
    with path.open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines))
    return dict(reports=[identity(path), comparison, diagnostic], figures=[figure])
