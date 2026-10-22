"""04m's saved-only empirical tables, figure and bounded interpretation."""

import csv
import json
from pathlib import Path

from hockey_stats.artifacts import artifact, clean_implementation, require, write_json
from hockey_stats.chance_cli import identity, output_path, read_json

from attribution_empirical_assessment import CONTRASTS, SCHEMES


COMPARISON_FIELDS = ("contrast", "metric", "region", "loss_numerator", "directed_hours", "metric_normalizer",
                     "loss_denominator", "estimate", "scheme", "lower", "upper", "undefined_draws", "direction", "reason")
COLORS = ("#206080", "#b56928", "#6c5684")


def _number(value):
    return "unavailable" if value is None else f"{value:.7g}"


def _csv(output, name, rows, fields=None):
    require(bool(rows), f"{name}: saved assessment has no rows")
    if fields is None:
        fields = list(dict.fromkeys(key for row in rows for key in row))
    path = output / name
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row.get(key), separators=(",", ":"), allow_nan=False)
                             if isinstance(row.get(key), (list, dict, tuple)) else row.get(key) for key in fields})
    return identity(path)


def _aggregate(assessment, contrast, scheme):
    rows = [row for row in assessment["comparison_rows"]
            if (row["contrast"], row["metric"], row["region"], row["scheme"])
            == (contrast, "regional", "all", scheme)]
    require(len(rows) == 1, "saved assessment aggregate comparison is missing or repeated")
    return rows[0]


def _figure(output, assessment):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1, 1.15]})
    for ci, contrast in enumerate(CONTRASTS):
        for si, scheme in enumerate(SCHEMES):
            row = _aggregate(assessment, contrast, scheme)
            position = ci + (si - 1) * .19
            color = COLORS[si]
            if row["lower"] is not None and row["upper"] is not None:
                axes[0].plot([row["lower"], row["upper"]], [position, position], color=color, linewidth=1.7)
            else:
                axes[0].annotate("unavailable", (row["estimate"], position), xytext=(6, 0),
                                 textcoords="offset points", fontsize=7, va="center")
            axes[0].plot(row["estimate"], position, "o", color=color, markersize=4,
                         label=scheme.replace("_", " ") if ci == 0 else None)
    axes[0].set_yticks(range(3), [name.replace("-", " − ") for name in CONTRASTS])
    axes[0].set_title("aggregate: three paired contrasts", loc="left", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, frameon=False, fontsize=8, loc="upper center",
                  bbox_to_anchor=(.48, .925), ncol=3)
    for ri, region in enumerate(assessment["region_names"]):
        rows = [row for row in assessment["comparison_rows"]
                if (row["contrast"], row["metric"], row["region"], row["scheme"])
                == (CONTRASTS[0], "regional", region, "games")]
        require(len(rows) == 1, "saved assessment regional comparison is missing or repeated")
        axes[1].plot(rows[0]["estimate"], ri, "o", color="#206080", markersize=4)
    axes[1].set_yticks(range(12), [name.replace("_", " ") for name in assessment["region_names"]])
    axes[1].set_title("twelve regions: borrowing − independent", loc="left", fontsize=11)
    for axis in axes:
        axis.axvline(0., color="#777777", linewidth=.8)
        axis.invert_yaxis()
        axis.grid(axis="x", alpha=.18)
        axis.tick_params(labelsize=8)
        axis.set_xlabel("paired loss difference (recorded unblocked attempts/60)²\nnegative means lower error for the first arm", fontsize=9)
    title = "recorded held-out shape: joint lineup prediction"
    if assessment["purpose"] == "fixture_exercise":
        title = "synthetic fixture exercise: " + title
    figure.suptitle(title, fontsize=13, x=.04, ha="left", y=.97)
    figure.text(.04, .095,
        "left: two-sided 95% percentile intervals; 2,000 paired draws per scheme; linear quantiles.\n"
        "right: pooled regional point differences; comparison.csv supplies all regional intervals and numeric values.\n"
        "all intervals condition on this split, population and fitted states; fitting and selection uncertainty are omitted.\n"
        "regional aggregate divides by twelve × directed hours; individual regions divide by directed hours. no absolute mse or player accuracy.",
        fontsize=8, va="top", linespacing=1.5)
    figure.subplots_adjust(left=.2, right=.98, top=.84, bottom=.23, wspace=.92)
    path = output / "comparison.png"
    with path.open("xb") as stream:
        figure.savefig(stream, format="png", dpi=160, facecolor="white")
    plt.close(figure)
    return identity(path)


def _numerical_summary(assessment):
    numerical = assessment["numerical"]
    probes = []
    for probe in numerical["probe_rows"]:
        receipt = probe["receipt"]
        scale = probe["alternative"]["scale"]
        probes.append(dict(index=probe["index"], season=probe["season"], arm=probe["arm"],
            verified=probe["verified"], status=receipt["status"],
            maximum_league_relative_current_player_movement=receipt["maximum_league_relative_current_player_movement"],
            saved_scale_status=scale["status"], own_scale_reasons=scale["own_reasons"],
            inherited_scale_limitation=scale["inherited_limitation"]))
    return {**{key: value for key, value in numerical.items() if key != "probe_rows"}, "probes": probes}


def _native_reference(assessment, assessment_reference):
    native = assessment["native_diagnostics"]
    return dict(arrays=native["arrays"], array_shapes=native["array_shapes"], axes_in_assessment=assessment_reference,
                meaning="native game means and group signed residual associations; not player-effect maps")


def render_reports(output, assessment, assessment_reference):
    """render saved rows only; no source arrays, fitted states or resampling."""
    output = Path(output)
    require(assessment["kind"] == "attribution_empirical_assessment" and assessment["schema_version"] == 1,
            "empirical report requires the complete schema-1 saved assessment")
    require(assessment["execution_status"] == "complete", "incomplete empirical assessment cannot be reported as complete")
    tables = dict(comparison=_csv(output, "comparison.csv", assessment["comparison_rows"], COMPARISON_FIELDS),
                  games=_csv(output, "game-scores.csv", assessment["game_rows"]),
                  diagnostics=_csv(output, "diagnostics.csv", assessment["diagnostic_rows"]))
    figure = _figure(output, assessment)
    fixture = assessment["purpose"] == "fixture_exercise"
    verified = assessment["numerical_status"] == "verified"
    coverage = assessment["coverage"]
    numerical = _numerical_summary(assessment)
    native_reference = _native_reference(assessment, assessment_reference)
    costs = dict(prepare=assessment["preparation_resources"], fit=assessment["fit_resources"],
                 assessment=assessment["resources"], states=assessment["state_resources"])
    lines = ["# empirical attribution benchmark", "",
        "does existing annual borrowing reduce error for recorded spatial shape in held-out final-season games, "
        "compared with an independent-season fit and training-fitted context alone?", "",
        f"purpose: `{assessment['purpose']}`; execution: `complete`; numerics: `{assessment['numerical_status']}`.", ""]
    if fixture:
        lines.extend(["these are explicitly synthetic counted-stint recordings. this fixture verifies software contracts and supplies no research conclusion.", ""])
    lines.extend([
        "## evidence and partition", "",
        "the recorded population is locatable unblocked attempts during reconstructed genuine 5v5, with paired team directions, "
        "matched spatial counts/time and zero-event exposure. block-contact locations and unsupported complete player rates are excluded.", "",
        f"the admitted final inventory has {coverage['inventory_games']} games: {coverage['training_games']} training and "
        f"{coverage['assessment_games']} assessment ({coverage['actual_assessment_fraction']:.3%}). "
        f"training retains {_number(coverage['training_directed_hours'])} directed hours and "
        f"{_number(coverage['training_recorded_unblocked_attempts'])} recorded unblocked attempts; assessment retains "
        f"{_number(coverage['assessment_directed_hours'])} directed hours and "
        f"{_number(coverage['assessment_recorded_unblocked_attempts'])} attempts. "
        f"{coverage['assessment_zero_time_games']} assessment games have zero retained time and remain sampling/calendar units. "
        "directed hours count both team directions and equal twice matched physical game-clock hours; "
        "source-ledger retained_seconds remains physical game-clock time.", "",
        "the fixed split reserves the first floor(month game count / 5) ids after the declared sha256 ordering within each inventory calendar month. "
        "[game-scores.csv](game-scores.csv) names every withheld game, date, retained count/time, coverage record and source identity. "
        "all earlier seasons are training; final references, players, context means and penalties use final training games only. "
        "the first-season spatial reference and forty-mode basis stay fixed.", "",
        "annual training coverage:", "",
        "| season | training games | active training players | directed hours | recorded attempts | source zero-time games |",
        "|---|---:|---:|---:|---:|---:|"])
    for year in assessment["years"]:
        lines.append(f"| {year['season']} | {len(year['game_ids'])} | {len(year['player_ids'])} | "
            f"{_number(year['directed_hours'])} | {_number(year['training_attempts'])} | {year['zero_time_source_games']} |")
    lines.extend(["", "all earlier seasons are wholly training; the final row contains final training games only. "
        "source zero-time games count the full annual source inventory, including the final season before partitioning. "
        "historical source gaps affect incoming history and are separate from final assessment coverage. "
        "the research source's zero-time historical games include unresolved captured-source gaps. the frozen ledgers do not distinguish "
        "newly catalogued failure types, so their measured attribution impact remains unresolved. "
        "no source correction, additional exclusion or later coverage estimate is substituted here.", ""])
    lines.extend(["source-ledger coverage retains its original units and overlapping categories:", "",
                  "| source field | value |", "|---|---:|"])
    for key, value in coverage["source_annual"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "recording and reconstructed membership/exposure gaps can be selective; shared source defects need not cancel. "
        "matching counts/time does not establish ignorable missingness. exact source lineage and producer identities are bound in result.json.", "",
        "## conditional paired differences", "",
        "negative means the first arm has lower recorded-shape error; positive means higher error. units are "
        "(recorded unblocked attempts/60)². these are signed differences of error, without observed self energy; absolute mse and rmse are unavailable. "
        "the denominator is twelve times pooled directed hours, rather than an average of game rates. both team directions remain one game.", "",
        "| contrast | pooled difference | scheme | 95% interval | direction across all schemes |", "|---|---:|---|---:|---|"])
    for contrast in CONTRASTS:
        for scheme in SCHEMES:
            row = _aggregate(assessment, contrast, scheme)
            interval = (f"[{_number(row['lower'])}, {_number(row['upper'])}]" if row["lower"] is not None
                        else "unavailable: " + str(row["reason"]))
            lines.append(f"| {contrast.replace('-', ' − ')} | {_number(row['estimate'])} | {scheme} | {interval} | `{row['direction']}` |")
    lines.extend(["",
        "a supported direction requires all three valid intervals to lie strictly on the same side of zero. otherwise direction is unresolved. "
        "these conditional diagnostics have no new minimum-gain gate, multiplicity control, equivalence, noninferiority or model nomination. "
        "2,000 draws use one paired matrix per scheme across all contrasts and regions, with seed 404130 and linear percentile quantiles. "
        "seven- and fourteen-day blocks begin at the earliest withheld inventory date and include intervening empty blocks. "
        "zero-denominator draws remain unavailable. intervals omit fitting/selection, split and population uncertainty.", "",
        "## support and bounded diagnostics", "",
        "support groups are exclusive within each role: positive final training exposure (`current_training`), earlier exposure only (`carried_only`), "
        "or neither (`new_to_fit`). the separate `first_in_corpus_final` flag overlaps them and means first observed in this corpus during the final season; "
        "it does not mean nhl debut or an ability change. player participation overlaps within a lineup, so on-ice hours are not independent observations.", "",
        "| role | support group | assessment members | on-ice hours |", "|---|---|---:|---:|"])
    for row in assessment["support_rows"]:
        lines.append(f"| {row['role']} | {row['support_group']} | {row['member_count']} | {_number(row['on_ice_hours'])} |")
    lines.extend(["",
        "new-to-fit identities receive their declared zero raw prior mean; carried-only identities use the borrowing posterior, including covariance-mediated updates. "
        "their assessment exposure remains included. each arm compensates context using its own uncentered maps. "
        "support signed residual associations divide summed on-ice residuals by group on-ice hours; zero hours is unavailable. "
        "they supply neither individual accuracy, cohort squared loss nor a residual ranking.", "",
        "[comparison.csv](comparison.csv) retains twelve regional contrasts and the native inverse-share metric; "
        "[diagnostics.csv](diagnostics.csv) retains fixed calendar, game mean-shape, support residual and bounded-probe summaries. "
        "the bound native diagnostic archive preserves cell coordinates, coverage and observed/predicted means with signed residuals. "
        "these native means describe joint recorded shape; they are not player-effect maps. "
        "the [figure](comparison.png) shares the signed-loss convention and has its numeric companion in comparison.csv.", "",
        "## numerical interpretation and remaining question", "",
        "each saved state has its declared bounded probe with fixed incoming history; final alternatives are rescored alone and together on the same assessment draws. "
        "a failed state probe or changed aggregate classification makes numerical interpretation unresolved. "
        "regional/native movement remains diagnostic. endpoint winners and inherited `scale_unresolved` are bounded-search limitations; "
        "these checks are neither global-optimization guarantees nor propagated-history sensitivity. ",
        "home/period/score context, forty-mode geometry and relative-rate annual carry remain limited assumptions.", ""])
    if numerical["probes"] and numerical["probes"][0]["season"] is not None:
        lines.extend(["| season / arm | probe | scale status | own reasons / inherited limitation | relative native / regional movement |",
                      "|---|---|---|---|---:|"])
        for probe in numerical["probes"]:
            movement = probe["maximum_league_relative_current_player_movement"]
            lines.append(f"| {probe['season']} / {probe['arm']} | {probe['status']} | {probe['saved_scale_status']} | "
                f"{', '.join(probe['own_scale_reasons'] or []) or 'none'} / {str(probe['inherited_scale_limitation']).lower()} | "
                f"{_number(movement['native_cells'])} / {_number(movement['regions'])} |")
        lines.append("")
    if not verified:
        lines.append("unresolved: " + assessment["unresolved_reason"] + ".")
    elif fixture:
        lines.append("the fixture is verified. no next scientific question is selected from fixture performance.")
    elif assessment["unresolved_reason"]:
        lines.append("unresolved scientific question: " + assessment["unresolved_reason"] + ".")
    elif assessment["next_question"]:
        lines.append("next question: " + assessment["next_question"])
    else:
        lines.append("no successor model is selected by this diagnostic comparison.")
    lines.extend(["",
        "this is joint lineup prediction of recorded spatial shape during the selected season, not separately validated offensive/defensive ability or a forecast "
        "available before the withheld games. all five research seasons were already exposed. "
        "prediction cannot repair prior synthetic recovery failures or isolate the prior as their cause. "
        "synthetic recovery, empirical player uncertainty, richer deployment/age adjustment, complete rates and supported chance valuation remain separate work. "
        "nomination: none; admission: not admitted; handoff: none.", ""])
    decision = output / "decision.md"
    decision.write_text("\n".join(lines), encoding="utf-8")
    verification_lines = ["# empirical attribution verification", "",
        "this report renders the saved assessment. no original moments, source arrays, fitted coefficients or bootstrap calculations are read during rendering.", "",
        f"assessment: `{assessment_reference['path']}`; sha256 `{assessment_reference['sha256']}`.", "",
        "```json", json.dumps(dict(numerical=numerical, coverage=coverage,
            resources=costs, inventory=assessment["inventory"], verification=assessment["verification"],
            consumed=assessment["consumed"], native_diagnostics=native_reference),
            indent=2, allow_nan=False), "```", "",
        "per-game, pooled and draw-wise paired closure is checked before saving. final probe alternatives preserve primary fits. "
        "producer/dependency and bound source identities remain in the assessment and result. "
        "source-preservation and temporary-check deletion evidence is recorded in the execution verification receipt; "
        "missing verification evidence is not implied by successful rendering.", ""]
    verification = output / "verification.md"
    verification.write_text("\n".join(verification_lines), encoding="utf-8")
    result = artifact("attribution_empirical_result", assessment["purpose"], dict(assessment=assessment_reference),
        schema_version=1, execution_status="complete", numerical_status=assessment["numerical_status"],
        study_status=("fixture_verified" if fixture else "diagnosed") if verified else "numerically_unresolved",
        nomination=None, admission="not_admitted", handoff=None,
        next_question=None if fixture or not verified else assessment["next_question"],
        unresolved_reason=assessment["unresolved_reason"], coverage=coverage,
        numerical=numerical, inventory=assessment["inventory"],
        aggregate_comparisons=[_aggregate(assessment, contrast, scheme) for contrast in CONTRASTS for scheme in SCHEMES],
        resources=costs, verification=assessment["verification"],
        source_references=assessment["sources"], native_diagnostics=native_reference,
        outputs=dict(**tables, figure=figure, decision=identity(decision), verification=identity(verification)))
    write_json(output / "result.json", result)
    return result


def report(assessment, output):
    """validate the saved document's producer, then render without following inputs."""
    source = Path(assessment).resolve(strict=True)
    assessment = read_json(source)
    require(assessment["kind"] == "attribution_empirical_assessment" and assessment["schema_version"] == 1
            and assessment["purpose"] in ("research", "fixture_exercise")
            and assessment["numerical_status"] in ("verified", "unresolved"),
            "empirical report requires the schema-1 saved assessment")
    if assessment["purpose"] == "research":
        clean_implementation(assessment["implementation"])
    destination = output_path(str(output), [str(source.parent)])
    destination.mkdir()
    render_reports(destination, assessment, identity(source))
    return identity(destination / "result.json")
