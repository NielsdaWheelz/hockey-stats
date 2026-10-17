"""04j's saved-information tables, figure and bounded scientific interpretation."""

from collections import Counter
import csv
import json
from pathlib import Path

import numpy as np

from hockey_stats.artifacts import require
from hockey_stats.chance_cli import identity


ROLES = {"offense": "offense", "defense": "attempts allowed"}
ASSUMPTIONS = {"annual": "final annual", "constant_history": "constant physical history"}
STATUSES = ("available", "not_estimable", "numerically_unresolved", "zero_functional",
            "not_in_target_population")
METRICS = ("regional_rms_sd", "near_sd", "lateral_sd")
MINUTES = (("all", 0., float("inf")), ("[0,300)", 0., 300.),
           ("[300,600)", 300., 600.), ("[600,1000)", 600., 1000.),
           ("[1000,infinity)", 1000., float("inf")))


def summarize(analysis):
    """final individual denominators, available-only quantiles and matched ratios."""
    players = [row for row in analysis["contrasts"]
               if row["record_type"] == "player_reference"
               and row["season"] == analysis["seasons"][-1]]
    summaries = []
    for design in ("real", "synthetic"):
        for role in ROLES:
            annual = {row["player_id"]: row for row in players
                      if (row["design"], row["role"], row["assumption"]) == (design, role, "annual")}
            for assumption in ASSUMPTIONS:
                population = [row for row in players
                              if (row["design"], row["role"], row["assumption"])
                              == (design, role, assumption)]
                require(len(population) == len(annual)
                        and {row["player_id"] for row in population} == set(annual),
                        "final annual/history player populations differ")
                for group, lower, upper in MINUTES:
                    rows = [row for row in population if lower <= row["minutes"] < upper]
                    counts = Counter(row["status"] for row in rows)
                    require(set(counts).issubset(STATUSES), "unknown contrast status in report")
                    available = [row for row in rows if row["status"] == "available"]
                    summary = dict(design=design, role=role, role_label=ROLES[role], assumption=assumption,
                                   minutes_group=group, n_all=len(rows), n_available=len(available))
                    summary.update({"n_" + status: counts[status] for status in STATUSES[1:]})
                    summary["unavailable_reasons"] = dict(sorted(Counter(
                        row["reason"] for row in rows if row["status"] != "available").items()))
                    matched = [row for row in available if annual[row["player_id"]]["status"] == "available"]
                    summary["matched_available"] = len(matched) if assumption == "constant_history" else None
                    summary["newly_estimable"] = sum(annual[row["player_id"]]["status"] == "not_estimable"
                                                      for row in available) if assumption == "constant_history" else None
                    for metric in METRICS:
                        values = [row[metric] for row in available]
                        require(all(value is not None and np.isfinite(value) and value >= 0 for value in values),
                                "available contrast has invalid physical sampling sd")
                        quantiles = np.quantile(values, [.1, .5, .9], method="linear") if values else [None] * 3
                        summary.update({metric + "_" + name: value
                                        for name, value in zip(("p10", "median", "p90"), quantiles, strict=True)})
                        ratios = [row[metric] / annual[row["player_id"]][metric] for row in matched
                                  if annual[row["player_id"]][metric] > 0] if assumption == "constant_history" else []
                        require(assumption != "constant_history" or len(ratios) == len(matched),
                                "matched contrast has zero annual functional sd")
                        quantiles = np.quantile(ratios, [.1, .5, .9], method="linear") if ratios else [None] * 3
                        summary.update({metric + "_ratio_" + name: value
                                        for name, value in zip(("p10", "median", "p90"), quantiles, strict=True)})
                    summaries.append(summary)
    return summaries


def _csv(path, rows, fields, purpose):
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["purpose", "deployment_semantics", *fields])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(purpose=purpose, deployment_semantics="both design labels are synthetic"
                                 if purpose == "fixture_exercise" else "real and synthetic training deployment",
                                 **{key: json.dumps(value, separators=(",", ":"), allow_nan=False)
                                    if isinstance(value, (dict, list, tuple)) else value for key, value in row.items()}))
    return identity(path)


def _number(value):
    return "unavailable" if value is None else f"{value:.6g}"


def _figure(output, analysis):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fixture = analysis["purpose"] == "fixture_exercise"
    rows = [row for row in analysis["contrasts"] if row["record_type"] == "player_reference"
            and row["season"] == analysis["seasons"][-1]]
    figure, axes = plt.subplots(2, 2, figsize=(12, 10), sharex=True, sharey=True)
    for ri, assumption in enumerate(ASSUMPTIONS):
        for ci, role in enumerate(ROLES):
            axis = axes[ri, ci]
            notes = []
            for design, color, marker in (("real", "#225e80", "o"), ("synthetic", "#af6425", "D")):
                selected = [row for row in rows if (row["assumption"], row["role"], row["design"])
                            == (assumption, role, design)]
                available = [row for row in selected if row["status"] == "available"]
                axis.scatter([row["minutes"] for row in available], [row["near_sd"] for row in available],
                             s=17 if design == "real" else 37, marker=marker, linewidths=.8,
                             facecolors=color if design == "real" else "none", edgecolors=color,
                             alpha=.65 if design == "real" else .9,
                             label=f"{design} label (synthetic)" if fixture else design)
                counts = Counter(row["status"] for row in selected if row["status"] != "available")
                detail = "; ".join(f"{status.replace('_', ' ')} {count}" for status, count in sorted(counts.items()))
                notes.append(f"{design}: {len(available)}/{len(selected)} available" + (f"; {detail}" if detail else ""))
            axis.text(.025, .975, "\n".join(notes), transform=axis.transAxes, va="top", fontsize=8,
                      bbox=dict(facecolor="white", edgecolor="none", alpha=.9, pad=3))
            axis.grid(alpha=.18)
            axis.tick_params(labelsize=9)
            axis.set_title(f"{ASSUMPTIONS[assumption]} · {ROLES[role]}", fontsize=11, loc="left", pad=10)
            axis.set_xlim(left=0)
            axis.set_ylim(bottom=0)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", bbox_to_anchor=(.56, .948), ncol=2, frameon=False)
    figure.suptitle("deployment information under the independent-row working-noise model", fontsize=14, y=.982)
    figure.supxlabel("included final-season minutes", fontsize=11, y=.225)
    figure.supylabel("within-20-ft, in-front-of-goal sampling sd\nredistributed recorded unblocked attempts/60", fontsize=10, x=.025)
    final = [row for row in analysis["designs"] if row["assumption"] == "annual" and row["final_target"]]
    require(len(final) == 2 and {row["design"] for row in final} == {"real", "synthetic"},
            "figure requires two final annual designs")
    final = {row["design"]: row for row in final}
    context = f"{final['real']['context_count']} real / {final['synthetic']['context_count']} synthetic contexts"
    reference = final["real"]["p_sha256"]
    require(reference == final["synthetic"]["p_sha256"], "figure references differ")
    footnotes = [
        "both design labels are synthetic; fixture exercise only." if fixture else "real and synthetic training deployment; " + context + ".",
        "final league rates, recorded unblocked attempts/60: "
        f"real {final['real']['rate']!r}; synthetic {final['synthetic']['rate']!r}. " + (context + "." if fixture else ""),
        "common 656-cell reference sha256: " + reference,
        "history uses each season's own rate (designs.csv); constant physical effects and separate annual context means are assumed.",
        "sampling sds condition on estimability and the working-noise model; they are not calibrated player uncertainty.",
    ]
    figure.text(.1, .18, "\n".join(footnotes), fontsize=8, va="top", linespacing=1.65)
    figure.subplots_adjust(left=.1, right=.98, top=.88, bottom=.29, hspace=.24, wspace=.1)
    path = output / "information.png"
    with path.open("xb") as stream:
        figure.savefig(stream, format="png", dpi=160, facecolor="white")
    plt.close(figure)
    return identity(path)


def render_reports(output: Path, analysis: dict):
    """render saved values only; no eigensolves, source reselection or response reads."""
    fixture = analysis["purpose"] == "fixture_exercise"
    summaries = summarize(analysis)
    reports = [_csv(output / "designs.csv", analysis["designs"],
                    list(dict.fromkeys(key for row in analysis["designs"] for key in row)), analysis["purpose"])]
    contrasts = []
    for original in analysis["contrasts"]:
        row = {key: value for key, value in original.items() if key != "regional_sd"}
        regional = original["regional_sd"]
        require(regional is None or len(regional) == 12, "contrast regional sd axis differs")
        row.update({f"regional_sd_{name}": None if regional is None else regional[index]
                    for index, name in enumerate(analysis["region_names"])})
        contrasts.append(row)
    reports.append(_csv(output / "contrasts.csv", contrasts,
                        list(dict.fromkeys(key for row in contrasts for key in row)), analysis["purpose"]))
    reports.append(_csv(output / "summary.csv", summaries, list(summaries[0]), analysis["purpose"]))
    closure = analysis["selector_closure"]
    require(not fixture or not closure, "fixture cannot supply selector-closure substitutes")
    if fixture:
        closure = [dict(record_type="status", closure_status="not_applicable,fixture_exercise")]
    fields = list(dict.fromkeys(key for row in closure for key in row))
    reports.append(_csv(output / "selector-closure.csv", closure, fields, analysis["purpose"]))
    figure = _figure(output, analysis)
    numerical = analysis["numerical"]
    verified = numerical["verified"]
    proposal = None
    unresolved = None
    if not fixture and verified:
        real_designs = [row for row in analysis["designs"] if row["design"] == "real"
                        and row["assumption"] == "annual"]
        proposal = dict(
            status="proposal_only_not_assigned",
            actual_design=[{key: row[key] for key in ("season", "source_refs", "player_ids", "context_count",
                                                     "exposure_seconds", "directed_team_seconds", "coverage")
                            if key in row} for row in real_designs],
            targets="final-current exposure-centered individual and declared pair broad-region contrasts; history-only identities remain nuisance columns",
            groups=dict(exposure_minutes=["[0,300)", "[300,600)", "[600,1000)", "[1000,infinity)"],
                        overlap="strongest-partner shared/focal exposure fractions [0,.25),[.25,.75),[.75,1]; preserve exact inseparable pairs",
                        estimability="report identified individuals, nonestimable individuals and available pair means separately"),
            physical_magnitudes=dict(primary_transfer_attempts_per_60=1., sensitivity_transfers_attempts_per_60=[.5, 2.],
                justification="a one-attempt/60 transfer between broad regions moves 16 2/3 recorded attempts over 1000 player minutes; a counting-scale scenario, selected independently of this study's precision and never an inferred effect distribution"),
            scenarios=["stable physical fields across observed history", "first-observed and return-after-absence identities with no invented prior exposure",
                       "one broad physical component changes in the final season; compare sign reversal and entry from zero"],
            noise="declared independent-row working covariance as primary; separately predeclare game-shared pace sensitivity, without claiming empirical calibration",
            estimator_question="does annual borrowing improve final-season broad-region recovery over season-independent estimation at a prospectively justified prediction-cost budget?",
            limits="design information cannot choose actual effect magnitudes, required accuracy, empirical noise or a supported estimator")
    elif not verified:
        unresolved = "declared numerical checks disagree; preserve contrast statuses and resolve those discrepancies before an empirical-benchmark specification"

    lines = ["# real-deployment attribution information", "",
             f"execution: `complete`; numerics: `{'verified' if verified else 'unresolved'}`.", ""]
    if fixture:
        lines.extend(["both design labels are synthetic. this fixture exercise supplies no real-player diagnosis, selector closure or next-benchmark proposal.", ""])
    lines.extend([
        "these are conditional sampling standard deviations for unbiased linear contrasts under the independent-row working-noise model, "
        "not calibrated player uncertainty, observed ability or universal estimation limits. units are redistributed recorded unblocked attempts/60. "
        "near sd means the within-20-ft, in-front-of-goal functional. total-shape variance is zero by construction; volume remains outside this analysis.", "",
        "## final individual contrasts", "",
        "all-player denominators include unavailable individuals. finite-sd quantiles condition on availability and use linear interpolation. "
        "pair means stay outside these distributions; they do not identify inseparable individuals.", "",
        "| design / assumption / role | available / all | near sd p10 / median / p90 | regional rms sd median |", "|---|---:|---:|---:|"])
    for row in summaries:
        if row["minutes_group"] == "all":
            lines.append(f"| {row['design']} / {ASSUMPTIONS[row['assumption']]} / {ROLES[row['role']]} | "
                         f"{row['n_available']} / {row['n_all']} | "
                         f"{_number(row['near_sd_p10'])} / {_number(row['near_sd_median'])} / {_number(row['near_sd_p90'])} | "
                         f"{_number(row['regional_rms_sd_median'])} |")
    lines.extend(["", "weak conditional precision is shown by the magnitude and spread of sampling sds, with minutes groups in [summary.csv](summary.csv). "
                  "no absolute accuracy threshold is inferred from those values. structural nonestimability differs from numerical disagreement.", ""])
    lines.extend(["| design / role / assumption | minutes group with largest available median near sd | median | available / all |",
                  "|---|---|---:|---:|"])
    for design in ("real", "synthetic"):
        for role in ROLES:
            for assumption in ASSUMPTIONS:
                bins = [row for row in summaries if (row["design"], row["role"], row["assumption"])
                        == (design, role, assumption) and row["minutes_group"] != "all" and row["near_sd_median"] is not None]
                if bins:
                    weakest = max(bins, key=lambda row: row["near_sd_median"])
                    lines.append(f"| {design} / {ROLES[role]} / {ASSUMPTIONS[assumption]} | {weakest['minutes_group']} | "
                                 f"{_number(weakest['near_sd_median'])} | {weakest['n_available']} / {weakest['n_all']} |")
    lines.append("")
    for row in summaries:
        if row["minutes_group"] == "all" and row["n_available"] != row["n_all"]:
            counts = "; ".join(f"{status.replace('_', ' ')}: {row['n_' + status]}" for status in STATUSES[1:] if row["n_" + status])
            lines.append(f"- {row['design']} / {ASSUMPTIONS[row['assumption']]} / {ROLES[row['role']]}: {counts}.")
    lines.extend(["", "## persistence and selected cases", "",
        "constant physical history retains the final-current population and final exposure weights. history-only identities remain nuisance columns. "
        "its precision gain depends on the assumption that physical effects do not change, with separate unknown context means each year.", "",
        "| design / role | matched available | newly estimable | history / annual near-sd p10 / median / p90 |", "|---|---:|---:|---:|"])
    for row in summaries:
        if row["minutes_group"] == "all" and row["assumption"] == "constant_history":
            lines.append(f"| {row['design']} / {ROLES[row['role']]} | {row['matched_available']} | {row['newly_estimable']} | "
                         f"{_number(row['near_sd_ratio_p10'])} / {_number(row['near_sd_ratio_median'])} / {_number(row['near_sd_ratio_p90'])} |")
    cases = [row for row in analysis["contrasts"] if row["record_type"] == "case"]
    lines.extend(["", "| design / case / role / assumption | status | near sd |", "|---|---|---:|"])
    for row in cases:
        lines.append(f"| {row['design']} / {row['label']} / {ROLES[row['role']]} / {ASSUMPTIONS[row['assumption']]} | "
                     f"{row['status']} | {_number(row['near_sd'])} |")
    lines.extend(["", "case overlap is descriptive, not an estimability test. absent members remain `not_in_target_population`; "
                  "case coefficients and references are explicit in [contrasts.csv](contrasts.csv). duplicate labels preserve their meaning without extra calculation.", "",
                  "## deployment and saved selector evidence", "",
                  "| design / season | current / union players | contexts | directed team hours | rate, recorded attempts/60 |", "|---|---:|---:|---:|---:|"])
    for row in analysis["designs"]:
        if row["assumption"] == "annual":
            lines.append(f"| {row['design']} / {row['season']} | {row['current_players']} / {row['union_players']} | "
                         f"{row['context_count']} | {_number(row['directed_team_seconds']/3600)} | {row['rate']!r} |")
    lines.extend(["", "source coverage, exclusions, rate/reference identities and costs remain in [designs.csv](designs.csv). "
                  "included exposure does not establish complete-season time. physical elapsed time is half directed team time; pair minutes are not halved.", ""])
    if fixture:
        lines.append("selector closure: `not_applicable,fixture_exercise`. [selector-closure.csv](selector-closure.csv) contains one nonnumeric status row and no fabricated closure summaries.")
    else:
        lines.extend(["the real design has 42 contexts and synthetic training deployment has six; the comparison does not isolate teammate mixing. "
                      "the synthetic design is one training deployment, not 600 independent deployments.", "",
                      f"[selector-closure.csv](selector-closure.csv) retains {len(closure)} saved summary rows and their original intervals. "
                      "truth-inspected fixed settings describe expected performance; adaptive rows describe realized performance. "
                      "prediction excess stays separate from absolute prediction error. no paired interval is invented and no fixed setting becomes a deployable winner. "
                      "04i's selected-score optimism and null false-map risks qualify the historical failed selector verdict without changing it."])
    lines.extend(["", "[four-panel exposure and working-precision figure](information.png) · "
                  "[complete designs](designs.csv) · [complete contrasts](contrasts.csv) · [denominators and quantiles](summary.csv)", ""])
    if proposal is not None:
        lines.extend(["## one subsequent benchmark proposal", "",
            "use the bound five-season real spatial design and its recorded coverage; retain all final-current players and history-only nuisance identities. "
            "report the fixed exposure groups, strongest-partner overlap fractions and structurally available/unavailable targets separately. "
            "keep exact inseparable-pair means distinct from individuals.", "",
            "predeclare a one-attempt/60 transfer between broad regions, with half/double sensitivity. this moves 16 2/3 recorded attempts over "
            "1000 player minutes: a counting-scale scenario chosen independently of observed precision, not an estimated effect distribution or required accuracy. "
            "assess stable effects, corpus entry/return and final-season changes including reversal and entry from zero.", "",
            "retain the declared independent-row working covariance as the primary noise assumption and predeclare a separate game-shared pace sensitivity. "
            "ask one estimator question: does annual borrowing improve final-season broad-region recovery over season-independent estimation at a "
            "prospectively justified prediction-cost budget? this proposes a next specification; it assigns no fitting or benchmark execution.", ""])
    elif unresolved is not None:
        lines.extend(["## unresolved diagnosis", "", unresolved + ".", ""])
    lines.extend(["the historical recovery and selector verdicts remain unchanged. no player ability, complete-rate adequacy, empirical uncertainty, "
                  "supported chance valuation, admission or publication follows.", "", "`nomination:null, admission:not_admitted, handoff:null`.", ""])
    path = output / "decision.md"
    with path.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    reports.append(identity(path))

    lines = ["# deployment-information verification", "",
             "this report reads saved analysis and closure values; it performs no source selection, response decoding or eigendecomposition.", "",
             "both design labels are synthetic; fixture exercise only." if fixture else "research uses the bound corrected real and original synthetic training designs.", "",
             f"numerical status: `{'verified' if verified else 'unresolved'}`.", "",
             "| check | verified | value | limit |", "|---|---|---:|---:|"]
    for row in numerical["checks"]:
        lines.append(f"| {row['label']} | {row['verified']} | {_number(row.get('value'))} | {_number(row.get('limit'))} |")
    lines.extend(["", f"independent reduced-gauge probes: {len(numerical['probes'])}; "
                  f"verified: {sum(row['verified'] for row in numerical['probes'])}. "
                  f"persistence comparisons: {len(numerical['persistence'])}; "
                  f"verified: {sum(row['verified'] for row in numerical['persistence'])}.", "",
                  "exact inventory:", "", "```json", json.dumps(analysis["exact_completeness"], indent=2, allow_nan=False), "```", "",
                  "resources:", "", "```json", json.dumps(analysis["resources"], indent=2, allow_nan=False), "```", "",
                  "regional covariance is stored once; contrast q scales it. functional sds retain covariance cross terms. "
                  "finite information arrays use explicit available-row indices; unavailable values remain null in tables. "
                  "temporary integration/review receipts and their deletion record belong to the repository verification, not a permanent test suite.", ""])
    with (output / "verification.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    reports.append(identity(output / "verification.md"))
    return dict(reports=reports, figures=[figure], summary_rows=summaries,
                next_benchmark=proposal, unresolved_reason=unresolved)
