"""saved-only 04n tables, figure and bounded interpretation."""

import csv
import json
from pathlib import Path

from hockey_stats.artifacts import artifact, clean_implementation, require, write_json
from hockey_stats.chance_cli import identity, output_path, read_json
from attribution_complete_assessment import CONTRASTS, SCHEMES

COMPARISON_FIELDS = (
    "comparison",
    "contrast",
    "metric",
    "region",
    "component",
    "loss_numerator",
    "directed_hours",
    "metric_normalizer",
    "loss_denominator",
    "estimate",
    "scheme",
    "lower",
    "upper",
    "undefined_draws",
    "direction",
    "reason",
)
COLORS = ("#206080", "#b56928", "#6c5684")


def _number(value):
    return "unavailable" if value is None else f"{value:.7g}"


def _csv(output, name, rows, fields=None):
    require(bool(rows), name + ": saved assessment rows are missing")
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    path = output / name
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(row.get(key), separators=(",", ":"), allow_nan=False)
                        if isinstance(row.get(key), (list, dict, tuple))
                        else row.get(key)
                    )
                    for key in fields
                }
            )
    return identity(path)


def _aggregate(assessment, contrast, scheme, metric="regional", component="complete", comparison="main"):
    rows = [
        row
        for row in assessment["comparison_rows"]
        if (row["comparison"], row["contrast"], row["scheme"], row["metric"], row["region"], row["component"])
        == (comparison, contrast, scheme, metric, "all", component)
    ]
    require(len(rows) == 1, "saved complete aggregate is missing or repeated")
    return rows[0]


def _figure(output, assessment):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    for panel, labels in enumerate((CONTRASTS, ("weighted_volume", "shape", "interaction"))):
        for index, label in enumerate(labels):
            for si, scheme in enumerate(SCHEMES):
                row = _aggregate(
                    assessment,
                    label if panel == 0 else CONTRASTS[0],
                    scheme,
                    component="complete" if panel == 0 else label,
                )
                position = index + (si - 1) * 0.19
                if row["lower"] is not None:
                    axes[panel].plot(
                        [row["lower"], row["upper"]], [position, position], color=COLORS[si], linewidth=1.5
                    )
                else:
                    axes[panel].annotate(
                        "interval unavailable",
                        (row["estimate"], position),
                        xytext=(5, 0),
                        textcoords="offset points",
                        fontsize=7,
                    )
                axes[panel].plot(
                    row["estimate"],
                    position,
                    "o",
                    color=COLORS[si],
                    markersize=4,
                    label=scheme.replace("_", " ") if panel == 0 and index == 0 else None,
                )
        axes[panel].set_yticks(range(3), [label.replace("-", " − ").replace("_", " ") for label in labels])
        axes[panel].invert_yaxis()
        axes[panel].axvline(0, color="#777777", linewidth=0.8)
        axes[panel].grid(axis="x", alpha=0.18)
        axes[panel].tick_params(labelsize=9)
        axes[panel].set_xlabel(
            "paired loss difference (recorded unblocked attempts/60)²\nlower favors the first arm", fontsize=9
        )
    axes[0].set_title("complete regional rates", loc="left", fontsize=11)
    axes[1].set_title("borrowing − independent: signed contributions", loc="left", fontsize=11)
    title = "held-out complete recorded rates: joint lineup prediction"
    if assessment["purpose"] == "fixture_exercise":
        title = "synthetic fixture exercise: complete recorded rates"
    figure.suptitle(title, x=0.04, ha="left", fontsize=13)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.91), ncol=3, frameon=False, fontsize=8
    )
    figure.text(
        0.04,
        0.145,
        "all terms divide by twelve × directed hours. weighted volume uses ||p′W||²; contributions sum to the complete difference.\n"
        "two-sided 95% linear percentile intervals; 2,000 shared paired draws per scheme, conditional on fitted states, split and source population.\n"
        "fitting and selection uncertainty are omitted. signed contributions are not percentages of blame. comparison.csv is the numeric companion.\n"
        "no absolute regional mse/rmse, player accuracy or publishable ability follows from these paired losses.",
        fontsize=8,
        linespacing=1.5,
    )
    figure.subplots_adjust(left=0.18, right=0.97, top=0.79, bottom=0.28, wspace=0.9)
    path = output / "comparison.png"
    with path.open("xb") as stream:
        figure.savefig(stream, format="png", dpi=160, facecolor="white")
    plt.close(figure)
    return identity(path)


def render_reports(output, assessment, assessment_reference):
    """render only saved scalar rows; never read fits, native arrays or sources."""
    output = Path(output)
    require(
        assessment["kind"] == "attribution_complete_assessment"
        and assessment["schema_version"] == 1
        and assessment["execution_status"] == "complete",
        "complete report requires complete schema-1 assessment",
    )
    require(
        assessment["numerical_status"] in ("verified", "unresolved") and len(assessment["rate_rows"]) == 9,
        "complete assessment lacks numerical status or all arm/resolution rate rows",
    )
    tables = dict(
        comparison=_csv(output, "comparison.csv", assessment["comparison_rows"], COMPARISON_FIELDS),
        games=_csv(output, "game-scores.csv", assessment["game_rows"]),
        diagnostics=_csv(output, "diagnostics.csv", assessment["diagnostic_rows"]),
        rates=_csv(output, "rate-diagnostics.csv", assessment["rate_rows"]),
    )
    figure = _figure(output, assessment)
    fixture = assessment["purpose"] == "fixture_exercise"
    verified = assessment["numerical_status"] == "verified"
    coverage = assessment["coverage"]
    numerical = {key: value for key, value in assessment["numerical"].items() if key != "probe_rows"}
    numerical["probe_verdicts"] = [row["verified"] for row in assessment["numerical"]["probe_rows"]]
    numerical["complete_probe_receipts_in_assessment"] = assessment_reference
    correction = assessment["source_correction"]
    correction_text = (
        f"the synthetic correction removes {len(correction['rows'])} directed zero-count rows and "
        f"{_number(correction['directed_seconds'])} directed seconds, with count loss {correction['count_loss']}. "
        if fixture
        else "the accepted correction removes six complete directed zero-count historical rows: "
        "132 physical / 264 directed seconds, with no retained spatial count loss and no final-season change. "
    )
    costs = dict(
        prepare=assessment["preparation_resources"],
        fit=assessment["fit_resources"],
        assessment=assessment["resources"],
        states=assessment["state_resources"],
    )
    lines = [
        "# complete recorded-rate adequacy",
        "",
        "**does annual borrowing improve held-out complete regional unblocked-attempt rates, and where do volume, shape or composition fail?**",
        "",
        f"purpose: `{assessment['purpose']}`; numerics: `{assessment['numerical_status']}`; admission: `not_admitted`.",
        "",
        "this is recorded joint lineup prediction on matched genuine-5v5 spatial support, including zero-event exposure. "
        "it is not separate offensive/defensive ability, all-attempt opportunity value or a forecast available before the games. "
        "all seasons remain research-exposed.",
    ]
    if fixture:
        lines += [
            "",
            "this synthetic fixture verifies software contracts; it is not empirical hockey evidence.",
        ]
    lines += [
        "",
        "## complete-rate evidence",
        "",
        "| contrast | games estimate | games 95% interval | direction across three schemes |",
        "|---|---:|---|---|",
    ]
    for contrast in CONTRASTS:
        row = _aggregate(assessment, contrast, "games")
        lines.append(
            f"| {contrast.replace('-',' − ')} | {_number(row['estimate'])} | [{_number(row['lower'])}, {_number(row['upper'])}] | `{row['direction']}` |"
        )
    lines += [
        "",
        "negative paired differences mean lower error. regional aggregate units are "
        "`(recorded unblocked attempts/60)^2`, dividing the pooled numerator by twelve × directed hours. "
        "all three valid 95% intervals must lie below zero for `supported_lower_loss`, or above zero for "
        "`supported_higher_loss`; otherwise the direction is `unresolved`. no gain threshold or admission gate is introduced.",
        "",
        f"coverage: {coverage['training_games']} training and {coverage['assessment_games']} assessment games; "
        f"{_number(coverage['training_directed_hours'])} training directed hours and "
        f"{_number(coverage['assessment_directed_hours'])} assessment directed hours; "
        f"{_number(coverage['assessment_recorded_unblocked_attempts'])} retained assessment attempts. "
        f"{coverage['assessment_zero_time_games']} zero-time assessment games remain sampling/calendar units.",
        "",
        "## source correction",
        "",
        correction_text + "original captures and grouped archives remain bound. "
        "count moments and scalar response energy are preserved only after checking the excluded rows are zero-count. "
        "exposure, league rate, residualization and training references are recomputed; nine new states and three exact reuses are selected.",
        "",
        (
            "the synthetic fixture uses its declared tiny counted histories and exclusions rather than asserting these empirical counts."
            if fixture
            else "the correction changes borrowing volume and shape history; source-only sensitivity below isolates the borrowing-shape consequence."
        ),
        "",
        "## volume, shape and interaction",
        "",
        "| borrowing − independent component | estimate | games 95% interval |",
        "|---|---:|---|",
    ]
    for component in ("weighted_volume", "shape", "interaction"):
        row = _aggregate(assessment, CONTRASTS[0], "games", component=component)
        lines.append(
            f"| {component.replace('_',' ')} | {_number(row['estimate'])} | [{_number(row['lower'])}, {_number(row['upper'])}] |"
        )
    volume = _aggregate(assessment, CONTRASTS[0], "games", metric="volume", component="volume")
    lines += [
        "",
        f"standalone volume difference: {_number(volume['estimate'])}, divided by directed hours. "
        "the regional volume contribution weights its numerator by `||p′W||²`; all three contributions share twelve × hours. "
        "interaction is a signed cross residual computed directly from grouped moments. contributions are not percentages of blame. "
        "inverse-share native error has unit volume weight and zero interaction. paired moments do not establish absolute regional mse/rmse.",
        "",
        "## physical-rate limitations",
        "",
        "| arm | resolution | strict negative entries | exposure-weighted entry fraction | any-negative-row exposure fraction | negative mass (predicted attempts) | minimum rate |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in assessment["rate_rows"]:
        lines.append(
            f"| {row['arm']} | {row['resolution']} | {row['negative_entries']} | "
            f"{_number(row['negative_entry_exposure_fraction'])} | {_number(row['any_negative_entry_row_exposure_fraction'])} | "
            f"{_number(row['negative_mass_predicted_attempts'])} | {_number(row['minimum'])} |"
        )
    lines += [
        "",
        "strict signs use `prediction < 0`, separate from numerical closure tolerances. entry fractions divide "
        "exposure-weighted negative entries by location count × directed exposure; any-negative-row fractions count each row once. "
        "negative mass integrates exposure × negative predicted rate, with a common dimensionless reference "
        "`training_r × assessment_directed_hours`. total, twelve-region and native resolutions retain their own denominators and exact worst-row/location locators in rate-diagnostics.csv. "
        "historical negative-total-rate meaning is retained separately from any-negative-entry exposure. "
        "signed effects may be negative; a negative complete prediction cannot be interpreted as an event intensity. "
        "no clipping or zero-negative-cell pass gate is applied. regional adequacy is primary; native shortcomings remain visible.",
        "",
        "## shape-only source sensitivity",
        "",
    ]
    source = _aggregate(
        assessment, "corrected-original", "games", component="shape", comparison="source_only"
    )
    lines.append(
        f"corrected minus original borrowing shape: {_number(source['estimate'])}; games interval "
        f"[{_number(source['lower'])}, {_number(source['upper'])}]; `{source['direction']}` across all schemes. "
        "this compares corrected and frozen original final borrowing shape on unchanged held-out games. "
        "it does not estimate the complete-rate consequence of correcting volume."
    )
    lines += [
        "",
        "## conditional uncertainty and numerical scope",
        "",
        "2,000 shared PCG64(404130) draws each for games, seven-day blocks and fourteen-day blocks pool numerators and float exposure. "
        "empty calendar blocks, zero-time games and undefined zero-denominator draws are retained; unavailable intervals carry reasons. "
        "these intervals condition on fitted models, selection, split and source population. there is no refitting, scheme selection or multiplicity control. "
        "month and support residual associations are descriptive diagnostics, not subgroup accuracy claims.",
        "",
        f"all {numerical['primary_probe_combinations']} final component combinations and "
        f"{numerical['source_probe_combinations']} source-only combinations were rescored on shared draws. "
        f"complete-regional direction stability: `{numerical['aggregate_direction_stable']}`; "
        f"source-only shape stability: `{numerical['source_direction_stable']}`. "
        "each bounded probe conditions on incoming primary history; no propagated probe histories or further fitting is implied. "
        "finite endpoint winners and inherited unresolved scale flags remain limitations in the saved receipts.",
        "",
        "useful joint prediction does not resolve latent recovery, richer context, empirical player uncertainty or supported chance valuation. "
        "publication remains separate.",
    ]
    unresolved = assessment["unresolved_reason"]
    next_question = assessment["next_question"]
    if not fixture and unresolved is None and next_question is None:
        unresolved = "this diagnostic study does not uniquely identify the next model revision"
    require(not (unresolved and next_question), "report has both unresolved reason and next question")
    if unresolved:
        lines += ["", "unresolved: " + unresolved + "."]
    elif next_question and not fixture:
        lines += ["", "next question: " + next_question]
    lines += [
        "",
        "![complete regional comparisons and signed contributions](comparison.png)",
        "",
        "comparison.csv supplies all twelve individual-region differences, native inverse-share diagnostics and intervals.",
    ]
    (output / "decision.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    verification = [
        "# verification",
        "",
        "this report renders the saved assessment only. it reads no fitted arrays, source rows or original moments, "
        "and performs no bootstrap or fitting. source, fit, row reconciliation, identities, preservation and temporary-test "
        "deletion evidence remain explicit in the assessment verification object.",
        "",
        f"assessment: `{assessment_reference['path']}`; sha256 `{assessment_reference['sha256']}`.",
        "",
        "```json",
        json.dumps(
            dict(
                inventory=assessment["inventory"],
                verification=assessment["verification"],
                numerical=numerical,
                resources=costs,
                consumed=assessment["consumed"],
            ),
            indent=2,
            allow_nan=False,
        ),
        "```",
        "",
        "the figure and csv files preserve signed contributions, strict-rate limitations and unavailable values. "
        "software completion does not admit a model.",
    ]
    (output / "verification.md").write_text("\n".join(verification) + "\n", encoding="utf-8")
    result = artifact(
        "attribution_complete_result",
        assessment["purpose"],
        dict(assessment=assessment_reference),
        schema_version=1,
        execution_status="complete",
        numerical_status=assessment["numerical_status"],
        study_status=(
            ("fixture_verified" if fixture else "diagnosed") if verified else "numerically_unresolved"
        ),
        nomination=None,
        admission="not_admitted",
        handoff=None,
        next_question=None if fixture else next_question,
        unresolved_reason=unresolved,
        coverage=coverage,
        numerical=numerical,
        inventory=assessment["inventory"],
        verification=assessment["verification"],
        resources=costs,
        source_references=assessment["sources"],
        tables=tables,
        figure=figure,
        decision=identity(output / "decision.md"),
        verification_document=identity(output / "verification.md"),
        aggregate_comparisons=[
            _aggregate(assessment, contrast, scheme) for contrast in CONTRASTS for scheme in SCHEMES
        ],
    )
    write_json(output / "result.json", result)
    return identity(output / "result.json")


def report(assessment, output):
    source = Path(assessment).resolve(strict=True)
    document = read_json(source)
    require(
        document["kind"] == "attribution_complete_assessment"
        and document["schema_version"] == 1
        and document["purpose"] in ("research", "fixture_exercise"),
        "report requires schema-1 complete assessment",
    )
    if document["purpose"] == "research":
        clean_implementation(document["implementation"])
    destination = output_path(str(output), [str(source.parent)])
    destination.mkdir()
    return render_reports(destination, document, identity(source))
