"""manual 04b research commands; study policy lives here, numerics in the package."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

import numpy as np

from hockey_stats.artifacts import (
    clean_implementation,
    implementation,
    json_values,
    linked_path,
    require,
    resources,
    rows,
    write_json,
)
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.cli import Once


def _annual_assessment(document: dict, states: dict, fits: dict) -> list[dict]:
    from hockey_stats.attribution import (
        map_mean,
        context_mean,
        negative_rates,
        read_control_annual,
        control_negative_rates,
    )

    controls = {
        (row["benchmark"], row["season"]): row["state"]
        for row in document["baseline_controls"]
    }
    result = []
    for annual in document["annual"]:
        key = (annual["population"], annual["season"])
        state = states[key]
        mean, context = map_mean(state), context_mean(state)
        errors = dict(
            map_sum=float(np.max(np.abs(mean.sum(axis=1) - state.volume.M[:, 0]))),
            context_sum=float(
                np.max(np.abs(context.sum(axis=1) - state.volume.A[:, 0]))
            ),
        )
        n = len(state.player_ids)
        for name in ("volume", "shape"):
            block = getattr(state, name)
            if block is not None:
                errors[name + "_centering"] = float(
                    max(
                        np.max(np.abs(state.u @ block.M[:n])),
                        np.max(np.abs(state.u @ block.M[n:])),
                    )
                )
        require(max(errors.values()) <= 1e-8, "annual map/centering accounting failed")
        negative = negative_rates(
            state, rows(linked_path(annual["rows"])), annual["strata"]
        )
        require(
            negative["rows"] == annual["row_count"]
            and negative["team_seconds"] == annual["team_seconds"],
            "native complete-rate assessment differs from original row/time population",
        )
        control_negative = None
        if key in controls:
            control = read_control_annual(linked_path(controls[key]))
            control_negative = control_negative_rates(
                control, rows(linked_path(annual["rows"])), annual["strata"]
            )
            require(
                control_negative["rows"] == negative["rows"]
                and control_negative["team_seconds"] == negative["team_seconds"],
                "control and revision diagnostic exposures differ",
            )
        fitted = next(
            row for row in fits["annual"] if (row["benchmark"], row["season"]) == key
        )
        fit_evidence = read_json(linked_path(fitted["state"]))
        result.append(
            dict(
                benchmark=key[0],
                season=key[1],
                rows=annual["rows"],
                source_population_id=state.population_id,
                r=state.r,
                accounting_errors=errors,
                observed_count=annual["total_count"],
                admitted_team_seconds=annual["team_seconds"],
                revision_negative_rates=negative,
                control_negative_rates=control_negative,
                volume_scale=state.volume.scale,
                shape_scale=None if state.shape is None else state.shape.scale,
                control_replay=fit_evidence["control_replay"],
                shape_resolution_check=fit_evidence["shape_resolution_check"],
                equation_diagnostics=dict(
                    volume=state.volume.diagnostics,
                    shape=None if state.shape is None else state.shape.diagnostics,
                ),
                fit=fitted,
                coverage=annual["coverage"],
            )
        )
    return result


def _exposure_summary(document: dict, projections: list[dict]) -> list[dict]:
    result = []
    for benchmark in document["populations"]:
        annual = next(
            row
            for row in document["annual"]
            if row["population"] == benchmark
            and row["season"] == document["target_season"]
        )
        with np.load(linked_path(annual["references"]), allow_pickle=False) as source:
            exposure = dict(
                zip(annual["players"], source["player_exposure"].tolist(), strict=True)
            )
        for role in ("offense", "defense"):
            points = []
            for row in projections:
                request = row["request"]
                if (
                    request["benchmark"] != benchmark
                    or request["role"] != role
                    or request["functional"] != "scalar"
                    or len(request["coefficients"]) != 1
                ):
                    continue
                player, coefficient = request["coefficients"][0]
                require(
                    coefficient == 1,
                    "exposure summary requires individual player requests",
                )
                if player not in exposure:
                    require(
                        row["status"] == "unavailable",
                        "absent frozen example needs an unavailable reason",
                    )
                    continue
                working = row["working"]
                refit = row["refit"]
                points.append(
                    dict(
                        player_id=player,
                        seconds=exposure[player],
                        status=row["status"],
                        reason=row["reason"],
                        working_relative_width=None
                        if working is None
                        else (working["upper"] - working["lower"]) / annual["r"],
                        refit_relative_width=None
                        if refit is None
                        else (refit["upper"] - refit["lower"]) / annual["r"],
                        meaningful_claim=row["meaningful_claim"],
                    )
                )
            require(
                len(points) == len(annual["players"]),
                "exposure summary omitted current players",
            )
            result.append(
                dict(
                    benchmark=benchmark,
                    role=role,
                    players=len(points),
                    points=points,
                    statuses=dict(Counter(point["status"] for point in points)),
                    refit_unavailable=sum(
                        point["refit_relative_width"] is None for point in points
                    ),
                )
            )
    return result


def _figures(
    output: Path,
    document: dict,
    recovery: dict,
    projections: list[dict],
    exposure: list[dict],
) -> list[dict]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from hockey_stats.shot_origins import grid

    plt.rcParams.update(
        {"font.size": 9, "axes.spines.top": False, "axes.spines.right": False}
    )
    working_color, refit_color = "#626c75", "#b4512a"
    evidence_label = (
        "fixture exercise: synthetic inputs; no research completion"
        if document["purpose"] == "fixture_exercise"
        else "research-only recorded evidence"
    )
    if recovery["status"] != "complete" or any(
        row["refit_reason"] == "incomplete_refit_set" for row in projections
    ):
        evidence_label += "\nincomplete numerical execution; no scientific verdict"
    figures = []
    fig, axes = plt.subplots(
        1, 2, figsize=(17, 9), gridspec_kw={"width_ratios": [1, 2.4]}
    )
    gains = recovery["shape_gains"]
    for index, row in enumerate(gains):
        if row["interval"] is None:
            axes[0].text(
                0, index, "unavailable: incomplete numerical execution", fontsize=7
            )
        else:
            mean, (low, high) = row["mean_reduction"], row["interval"]
            axes[0].plot([low, high], [index, index], color="#234a5b", linewidth=2)
            axes[0].plot(mean, index, "o", color="#234a5b")
    gain_labels = []
    for row in gains:
        metric = next(
            (
                value
                for value in recovery["error_metrics"]
                if value["case"] == row["case"]
                and value["contrast"] == row["contrast"]
                and value["year"] == 5
            ),
            None,
        )
        errors = (
            ""
            if metric is None
            else f"\ncontrol {metric['means']['control']:.3g}; revision {metric['means']['revision']:.3g}"
        )
        gain_labels.append(
            f"{row['case'].replace('_', ' ')} / {row['contrast']}\n{row['status']}"
            + errors
        )
    axes[0].set_yticks(range(len(gains)), gain_labels)
    axes[0].axvline(0, color="black", linewidth=0.8)
    axes[0].set_xlabel(
        "control minus revision native map squared error\n"
        + gains[0]["unit"]
        + "\npaired 95% monte carlo interval"
    )
    axes[0].set_title("final-year shape gains; independent outer replicates")
    cells = [row for row in recovery["coverage_cells"] if row["nomination"]]
    for index, row in enumerate(cells):
        for name, offset, color in [
            ("working", -0.13, working_color),
            ("refit", 0.13, refit_color),
        ]:
            interval = row[name]
            if interval is not None and interval["wilson"] is not None:
                axes[1].plot(
                    interval["wilson"], [index + offset] * 2, color=color, linewidth=1.8
                )
                axes[1].plot(
                    interval["rate"],
                    index + offset,
                    "o",
                    color=color,
                    label=name if index == 0 else None,
                    markersize=4,
                )
    labels = []
    for row in cells:
        contrast = (
            row["contrast"]
            .replace("pair_", "")
            .replace("_minus_", " − ")
            .replace("_plus_", " + ")
            .replace("_", " ")
        )
        population = (
            "all attempts" if row["benchmark"] == "all_attempts" else "unblocked"
        )
        truth = (
            f"{100 * row['relative_truth']:.3g}% of league rate"
            if row["relative_truth"] is not None
            else f"{row['truth']:.3g} attempts/60"
        )
        labels.append(
            f"{row['case'].replace('_', ' ')} / {population} / year {row['year']} / {contrast}\ntruth {truth}"
        )
    axes[1].set_yticks(range(len(cells)), labels)
    axes[1].axvline(0.95, color="black", linewidth=0.8, label="nominal .95")
    axes[1].axvline(
        0.90,
        color="black",
        linewidth=0.8,
        linestyle=":",
        label="developmental floor .90",
    )
    axes[1].set_xlim(0, 1.015)
    axes[1].set_xlabel("truth coverage; two-sided 95% wilson intervals")
    axes[1].set_title(
        f"12 frozen nomination cells; outer denominator {recovery['expected_outer_per_case']}"
    )
    axes[1].legend(loc="lower left", bbox_to_anchor=(0, 1.04), ncol=2, fontsize=8)
    axes[0].invert_yaxis()
    axes[1].invert_yaxis()
    fig.suptitle(
        "recorded-rate recovery: pointwise claims, conditional references\n"
        + evidence_label,
        fontsize=13,
    )
    fig.text(
        0.02,
        0.015,
        "entry, return and paired sum remain separate claims. paired differences and either individual are unidentified; no empirical zero claim.\n"
        "nominal 95% intervals face a 90% developmental coverage floor; these finite cells imply no universal or simultaneous calibration.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.065, 1, 0.95))
    path = output / "recovery.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    figures.append(dict(name="recovery", reference=identity(path)))

    centers, _ = grid()
    examples = [
        row
        for row in recovery["figures_data"]
        if row["case"] == "gaussian" and row["outer_id"] == 0
    ]
    synthetic = {}
    if examples:
        example = examples[0]
        with np.load(linked_path(example["arrays"]), allow_pickle=False) as source:
            synthetic = {
                row["contrast"]: {
                    kind: source[row[kind]].copy()
                    for kind in ("truth", "control", "revision", "error")
                }
                for row in example["maps"]
                if row["year"] == 5
            }
    real = [
        row
        for row in projections
        if row["request"]["functional"] == "native"
        and len(row["request"]["coefficients"]) == 1
    ]
    require(
        len(real) <= 8,
        "native figure received more than the frozen four examples in both roles",
    )
    fig, axes = plt.subplots(4, 4, figsize=(17, 11), layout="constrained")
    for row_index, name in enumerate(("broad", "local")):
        if name not in synthetic:
            for ax in axes[row_index]:
                ax.text(
                    0.5,
                    0.5,
                    "synthetic outer 0 unavailable",
                    ha="center",
                    transform=ax.transAxes,
                )
            continue
        values = synthetic[name]
        limit = max(float(np.max(np.abs(value))) for value in values.values())
        for col, kind in enumerate(("truth", "control", "revision", "error")):
            ax = axes[row_index, col]
            scale = limit
            if scale == 0:
                scale = 1
            mappable = ax.scatter(
                centers[:, 0],
                centers[:, 1],
                c=values[kind],
                s=9,
                marker="s",
                cmap="RdBu_r",
                vmin=-scale,
                vmax=scale,
                linewidths=0,
            )
            ax.set_title(f"{name}: {kind}\nvolume {values[kind].sum():.4g} attempts/60")
            fig.colorbar(mappable, ax=ax, shrink=0.65)
    real_limit = max(
        (float(np.max(np.abs(row["mean"]))) for row in real if row["mean"] is not None),
        default=0,
    )
    if real_limit == 0:
        real_limit = 1
    for index, row in enumerate(real):
        ax = axes[2 + index // 4, index % 4]
        request = row["request"]
        role = "suppression" if request["role"] == "defense" else "offense"
        if row["mean"] is None:
            ax.text(
                0.5,
                0.5,
                f"{request['coefficients'][0][0]} {role}\nplayer not currently observed",
                ha="center",
                transform=ax.transAxes,
            )
            continue
        scalar = next(
            value
            for value in projections
            if value["request"]["benchmark"] == request["benchmark"]
            and value["request"]["name"] == request["name"]
            and value["request"]["functional"] == "scalar"
        )
        mappable = ax.scatter(
            centers[:, 0],
            centers[:, 1],
            c=row["mean"],
            s=9,
            marker="s",
            cmap="RdBu_r",
            vmin=-real_limit,
            vmax=real_limit,
            linewidths=0,
        )
        diagnostic = (
            "\nunidentified; prior-conditioned diagnostic"
            if row["status"] == "not_data_identified"
            else ""
        )
        ax.set_title(
            f"{request['coefficients'][0][0]} {role}\nmatched volume {scalar['mean']:.3g} attempts/60"
            + diagnostic
        )
        fig.colorbar(mappable, ax=ax, shrink=0.65)
    for index in range(len(real), 8):
        ax = axes[2 + index // 4, index % 4]
        ax.text(
            0.5, 0.5, "frozen example unavailable", ha="center", transform=ax.transAxes
        )
    for ax in axes.ravel():
        ax.set(
            xlim=(-100, 100),
            ylim=(-42.5, 42.5),
            xlabel="attacking x (feet)",
            ylabel="y (feet)",
        )
        ax.set_aspect("equal")
    fig.suptitle(
        "native recorded-rate associations, attempts per 60 per cell\n"
        "synthetic: fixed gaussian outer 0, year 5; matched unblocked 2025–26.\n"
        + evidence_label
        + "\n"
        "cells are parameters, not proven five-foot physical accuracy; pointwise bands imply no simultaneous certainty.",
        fontsize=12,
    )
    path = output / "native-maps.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    figures.append(dict(name="native_maps", reference=identity(path)))

    pairs = [
        row
        for row in projections
        if row["request"]["functional"] == "scalar"
        and len(row["request"]["coefficients"]) == 2
    ]
    fig, axes = plt.subplots(
        2, 3, figsize=(17, 10), gridspec_kw={"width_ratios": [1.7, 1, 1]}
    )
    ax = axes[0, 0]
    for index, row in enumerate(pairs):
        if row["mean"] is None:
            ax.annotate(row["reason"], (0, index), fontsize=6)
            continue
        for kind, offset, color in [
            ("working", -0.13, working_color),
            ("refit", 0.13, refit_color),
        ]:
            interval = row[kind]
            if interval is not None:
                ax.plot(
                    [interval["lower"] / row["r"], interval["upper"] / row["r"]],
                    [index + offset] * 2,
                    color=color,
                    linewidth=1.8,
                    label=kind if index == 0 else None,
                )
                ax.plot(
                    row["mean"] / row["r"],
                    index + offset,
                    "o",
                    color=color,
                    markersize=3,
                )
            elif kind == "refit":
                reason = (
                    "unidentified: persistent co-deployment"
                    if row["status"] == "not_data_identified"
                    else "refit unavailable: incomplete draws"
                )
                ax.annotate(reason, (row["mean"] / row["r"], index + 0.16), fontsize=6)
    ax.axvspan(-0.05, 0.05, color="#e8e6df")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(
        range(len(pairs)),
        [
            row["request"]["benchmark"]
            + " / "
            + ("suppression" if row["request"]["role"] == "defense" else "offense")
            + " / "
            + " − ".join(str(value[0]) for value in row["request"]["coefficients"])
            for row in pairs
        ],
    )
    ax.set_xlabel("effect / original league team rate; strict 5% scalar band")
    ax.set_title("frozen pair contrasts; first id minus second")
    ax.invert_yaxis()
    ax.legend(fontsize=8)
    axes[1, 0].axis("off")
    axes[1, 0].text(
        0,
        1,
        "recorded-rate associations, not supported ability\n\n"
        "working: gaussian, conditional on fitted scales and references\n"
        "refit: basic intervals from joint historical trajectories\n\n"
        "persistent duplicate-group null component:\n"
        "empirical interval and meaningful claim are unavailable;\n"
        "point estimate, raw spread and working interval are diagnostic.\n\n"
        "reference uncertainty, source error and cross-game dependence\n"
        "are excluded. no rank or causal claim.",
        va="top",
        linespacing=1.5,
    )
    for index, record in enumerate(exposure):
        ax = axes[index // 2, 1 + index % 2]
        for kind, color in [("working", working_color), ("refit", refit_color)]:
            selected = [
                point
                for point in record["points"]
                if point[kind + "_relative_width"] is not None
            ]
            ax.scatter(
                [point["seconds"] / 3600 for point in selected],
                [point[kind + "_relative_width"] for point in selected],
                s=7,
                alpha=0.45,
                color=color,
                label=kind,
            )
        role = "suppression" if record["role"] == "defense" else "offense"
        ax.set_title(
            f"{record['benchmark']} / {role}\n{record['players']} current players; {record['refit_unavailable']} refit unavailable"
        )
        ax.set_xlabel("original admitted exposure (hours)")
        ax.set_ylabel("interval width / original team rate")
        ax.legend(fontsize=8)
    fig.suptitle(
        "2025–26 scalar resolution; fixed evidence and references\n" + evidence_label,
        fontsize=13,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = output / "resolution.png"
    fig.savefig(path, dpi=170)
    plt.close(fig)
    figures.append(dict(name="resolution", reference=identity(path)))
    return figures


def assess(
    prepared: Path | str,
    fits: Path | str,
    refits: list[Path | str],
    simulation: Path | str,
    out: Path | str,
) -> dict:
    """reconcile explicit artifacts and report scoped results; never fit or publish."""
    from hockey_stats.attribution import read_fits
    from hockey_stats.attribution_data import read_revision_prepared
    from hockey_stats.attribution_uncertainty import summarize_refits

    started = time.monotonic()
    prepared_path, fits_path, simulation_path = [
        Path(value).resolve(strict=True) for value in (prepared, fits, simulation)
    ]
    document = read_revision_prepared(prepared_path)
    protocol = read_json(linked_path(document["protocol"]))
    current_implementation = implementation()
    if document["purpose"] == "research":
        clean_implementation(current_implementation)
    fit_document, states = read_fits(fits_path)
    recovery = read_json(simulation_path)
    require(
        recovery["schema_version"] == 2
        and recovery["kind"] == "attribution_revision_recovery"
        and recovery["purpose"] == document["purpose"]
        and recovery["prepared"] == identity(prepared_path)
        and recovery["protocol"] == document["protocol"],
        "recovery identity differs from assessment inputs",
    )
    budgets = protocol["budgets"]
    require(
        recovery["expected_outer_per_case"] == budgets["outer_per_case"]
        and recovery["inner_refits"] == budgets["inner_refits"]
        and recovery["paired_error_resamples"] == budgets["paired_error_resamples"],
        "recovery budgets differ from frozen assessment",
    )
    completed_ids = [tuple(value) for value in recovery["completed_outer_ids"]]
    error_ids = [tuple(value) for value in recovery["error_outer_ids"]]
    expected_ids = {
        (case, outer) for case in range(2) for outer in range(budgets["outer_per_case"])
    }
    require(
        len(completed_ids + error_ids) == len(set(completed_ids + error_ids))
        and set(completed_ids + error_ids) <= expected_ids
        and (
            recovery["status"] != "complete"
            or set(completed_ids) == expected_ids
            and not error_ids
        ),
        "recovery completion ledger differs from frozen denominators",
    )
    if document["purpose"] == "research":
        require(
            recovery["implementation"] == protocol["implementation"],
            "recovery producer differs from frozen implementation",
        )
    summary = summarize_refits(prepared_path, fits_path, refits)
    output = output_path(
        str(out),
        [str(path.parent) for path in (prepared_path, fits_path, simulation_path)]
        + [str(Path(path).resolve(strict=True).parent) for path in refits],
    )
    require(
        output.is_relative_to(Path(protocol["output_root"]).resolve()),
        "assessment differs from frozen output root",
    )
    if document["purpose"] == "research":
        require(
            output.is_relative_to(Path("/Volumes/Expansion/hockey-stats")),
            "research assessment requires external output",
        )
    output.mkdir()
    annual = _annual_assessment(document, states, fit_document)
    projections = json_values(summary["projections"])
    projection_path = output / "projections.jsonl"
    with projection_path.open("x", encoding="utf-8") as destination:
        for projection in projections:
            destination.write(
                json.dumps(projection, allow_nan=False, separators=(",", ":")) + "\n"
            )
    exposure = _exposure_summary(document, projections)
    figures = _figures(output, document, recovery, projections, exposure)
    complete = summary["status"] == "complete" and recovery["status"] == "complete"
    resolution = [
        dict(
            benchmark=row["benchmark"],
            season=row["season"],
            **row["shape_resolution_check"],
        )
        for row in annual
        if row["shape_resolution_check"] is not None
    ]
    require(
        len(resolution) == 2,
        "assessment requires first- and final-year conditional shape checks",
    )
    real_shape_resolved = all(row["status"] == "verified" for row in resolution)
    recommendation = recovery["recommendation"] if complete else None
    if recommendation == "nominate_revision" and not real_shape_resolved:
        recommendation = "mixed"
    costs = dict(
        preparation=document["resources"],
        fits=fit_document["resources"],
        refit_ranges=[
            dict(
                reference=identity(Path(path).resolve(strict=True)),
                resources=read_json(Path(path).resolve(strict=True))["resources"],
            )
            for path in refits
        ],
        recovery=recovery["resources"],
        assessment=resources(started),
        interpretation="process wall times; concurrent durations are not summed elapsed time",
    )
    result = dict(
        schema_version=2,
        kind="attribution_revision_assessment",
        purpose=document["purpose"],
        implementation=current_implementation,
        model_implementation=protocol["implementation"],
        protocol=document["protocol"],
        prepared=identity(prepared_path),
        fits=identity(fits_path),
        refits=[identity(Path(path).resolve(strict=True)) for path in refits],
        simulation=identity(simulation_path),
        status="complete" if complete else "incomplete",
        annual=annual,
        source_population_ids=document["population_ids"],
        pairs=document["pairs"],
        coverage=document["ledgers"]["coverage"],
        projections=identity(projection_path),
        exposure_summary=exposure,
        refit_summary={
            key: value
            for key, value in summary.items()
            if key not in ("projections", "requests")
        },
        support_matrix=recovery["support_matrix"],
        null_handling=recovery["null_handling"],
        figures=figures,
        conditional_real_shape_resolution=dict(
            status="verified" if real_shape_resolved else "withheld",
            checks=resolution,
            consequence=None
            if real_shape_resolved
            else "withhold affected real shape claims; numerical issue requires review",
        ),
        costs=costs,
        interval_meanings=dict(
            working="pointwise gaussian; conditional on references and fitted scales",
            refit="basic game-refit; fixed references, refitted scales and complete historical carry",
        ),
        limitations=[
            "recorded-rate associations; no causal isolation or supported ability",
            "selective matched coverage and omitted deployment remain conditional",
            "age-neutral annual history; unseen players and cross-game dependence excluded",
            "native cells are parameters, not established five-foot physical accuracy",
            "negative complete rates retained; no intensity-model claim",
            "pointwise intervals; no simultaneous map or total uncertainty claim",
            "scale endpoints and inherited limitations remain in every denominator",
        ],
        admission="not_admitted",
        handoff=None,
        resources=resources(started),
    )
    write_json(output / "assessment.json", json_values(result))
    verdict = dict(
        schema_version=2,
        kind="attribution_revision_result",
        purpose=document["purpose"],
        implementation=current_implementation,
        model_implementation=protocol["implementation"],
        protocol=document["protocol"],
        evidence=dict(
            prepared=identity(prepared_path),
            fits=identity(fits_path),
            refits=result["refits"],
            simulation=identity(simulation_path),
            assessment=identity(output / "assessment.json"),
        ),
        completion=result["status"],
        scientific_verdict=None
        if not complete
        else dict(
            native_shape_gain=recovery["shape_gains"],
            interval_recovery=[
                row for row in recovery["coverage_cells"] if row["nomination"]
            ],
            false_claims=[
                row for row in recovery["false_claim_cells"] if row["nomination"]
            ],
            null_handling=recovery["null_handling"],
            claim_groups=recovery["claim_groups"],
            conditional_real_shape_resolution=result[
                "conditional_real_shape_resolution"
            ],
            meaningful_resolution=[
                dict(
                    benchmark=row["benchmark"],
                    role=row["role"],
                    players=row["players"],
                    refit_unavailable=row["refit_unavailable"],
                    statuses=row["statuses"],
                )
                for row in exposure
            ],
        ),
        recommendation=recommendation
        if complete
        else "complete_missing_numerical_work",
        admission="not_admitted",
        handoff=None,
        limitations=result["limitations"],
        costs=costs,
    )
    write_json(output / "result.json", json_values(verdict))
    return identity(output / "assessment.json")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="manual research-only attribution revision", allow_abbrev=False
    )
    commands = parser.add_subparsers(dest="command", required=True)
    options = {
        "prepare": ("baseline-prepared", "protocol", "out"),
        "fit": ("prepared", "out"),
        "refit": ("prepared", "fits", "draw-start", "draw-stop", "out"),
        "simulate": ("prepared", "out"),
        "assess": ("prepared", "fits", "simulation", "out"),
    }
    for name, fields in options.items():
        child = commands.add_parser(name, allow_abbrev=False)
        for field in fields:
            child.add_argument(
                "--" + field,
                required=True,
                action=Once,
                type=int if field in ("draw-start", "draw-stop") else str,
            )
        if name == "assess":
            child.add_argument("--refits", action="append", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            from hockey_stats.attribution_data import prepare_revision

            reference = prepare_revision(
                args.baseline_prepared, args.protocol, args.out
            )
        elif args.command == "fit":
            from hockey_stats.attribution import fit_prepared

            reference = fit_prepared(args.prepared, args.out)
        elif args.command == "refit":
            from hockey_stats.attribution_uncertainty import refit_range

            reference = refit_range(
                args.prepared, args.fits, args.draw_start, args.draw_stop, args.out
            )
        elif args.command == "simulate":
            from attribution_revision_recovery import simulate

            reference = simulate(args.prepared, args.out)
        else:
            reference = assess(
                args.prepared, args.fits, args.refits, args.simulation, args.out
            )
        print(json.dumps(reference, allow_nan=False))
        return 0
    except (
        InputContractError,
        OSError,
        ValueError,
        KeyError,
        np.linalg.LinAlgError,
    ) as failure:
        print(str(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
