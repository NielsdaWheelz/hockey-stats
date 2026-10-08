"""one saved-stream residual localization and fixed spatial composition diagnosis."""

import argparse
import math
from pathlib import Path
import platform
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance import CONTEXT_CATEGORIES
from hockey_stats.chance_cli import identity, output_path, read_json
from hockey_stats.chance_data import MODEL_SHOT_TYPES
from hockey_stats.chance_evaluation import (
    GROUP_DOMAINS, REGION_NAMES, add_binary, binary_metrics, binary_record, calibration_bin,
    compound_regions, finish_binary,
)
from hockey_stats.cli import Once
import chance_assessment as assessment
from chance_development import implementation
from chance_residual_spatial import SpatialAccumulator, save_spatial_figure
from chance_review import agrees, caption_layout, clean_implementation, linked_path, require


FROZEN_DIGESTS = {
    "assessment_completion": "d1ec15ffb51748049efc79d847f0a454cfae5a8a90072880d276487e9d8dca2f",
    "assessment": "9f226f0934244a22ff3fb8212bac271c3bfb589d63516c5664a31c79d085b889",
}
FOCAL_BINS = {"unblocked_conversion": 3, "all_attempt_recorded_context": 2}
PREDICTORS = ("revision", "baseline", "historical_stronger")
PARTITIONS = ("calendar_month", "original_shot_type", "preceding_kind", "observed_proxy_region")


def load_evidence(completion_path):
    """resolve completed 03h/03g evidence; fitted parents remain unopened identities."""
    completion_path = Path(completion_path).resolve(strict=True)
    completion = read_json(completion_path)
    purpose = completion["purpose"]
    require(purpose in ("research", "fixture_exercise"), "invalid residual diagnosis purpose")
    assessment_path = linked_path(completion["assessment"])
    parent = read_json(assessment_path)
    for document, kind in (
        (completion, "chance_necessary_calibration_assessment_completion"),
        (parent, "chance_necessary_calibration_assessment"),
    ):
        require(type(document["schema_version"]) is int and document["schema_version"] == 1
                and document["artifact_kind"] == kind and document["purpose"] == purpose,
                "schema-1 completed assessment kinds/purposes required")
    require(parent["identities"] == completion["identities"]
            and parent["implementation"] == completion["implementation"],
            "completed assessment identities or execution disagree")
    loaded = assessment.load_evidence(linked_path(parent["identities"]["completion"]))
    require(loaded["completion"]["purpose"] == purpose
            and all(parent["identities"][name] == reference
                    for name, reference in loaded["identities"].items()),
            "assessment and original diagnosis links disagree")
    linked_path(parent["identities"]["protocol"])
    composition, comparison = loaded["composition"], loaded["comparison"]
    require(parent["original_execution"] == dict(
                implementation=composition["implementation"],
                parent_implementations=composition["parent_implementations"],
                identities=composition["identities"])
            and parent["game_dates"] == comparison["game_dates"]
            and parent["coverage"] == comparison["coverage"]
            and parent["population"] == dict(
                description=comparison["population_description"],
                training_game_dates=composition["compatibility"]["training_game_dates"],
                selected_games=len(comparison["game_dates"]),
                recognized_rows=sum(comparison["coverage"]["attempts_by_status"].values()))
            and set(parent["quantities"]) == set(assessment.QUANTITIES)
            and [part["game_id"] for part in parent["per_game"]] == list(comparison["game_dates"])
            and all(parent["resampling"][key] == value
                    for key, value in assessment.RESAMPLING.items())
            and parent["decision"] in ("withheld", "further_assessment_required"),
            "assessment parent execution/population/resampling/decision disagree")
    loaded["identities"].update(
        assessment_completion=identity(completion_path), assessment=completion["assessment"],
        assessment_protocol=parent["identities"]["protocol"],
    )
    if purpose == "research":
        require(all(loaded["identities"][name]["sha256"] == value
                    for name, value in FROZEN_DIGESTS.items()) and parent["decision"] == "withheld",
                "frozen withheld research assessment identity changed")
        clean_implementation(parent["implementation"])
        require(len(comparison["game_dates"]) == 712
                and max(composition["compatibility"]["training_game_dates"].values()) == "2024-12-31"
                and min(comparison["game_dates"].values()) == "2025-01-01"
                and max(comparison["game_dates"].values()) == "2025-04-17",
                "frozen training/assessment calendar changed")
    loaded["assessment"] = parent
    return loaded


def triple_summary(parts):
    """compact ledger-aligned triples retain additive evidence, including empty games."""
    count = int(math.fsum(parts[:, 0]))
    observed = int(math.fsum(parts[:, 1]))
    predicted = math.fsum(parts[:, 2])
    require(math.isfinite(predicted), "nonfinite scalar predicted probability sum")
    excess = predicted - observed
    return dict(
        count=count, observed_positive_count=observed, predicted_probability_sum=predicted,
        signed_excess_goals=excess, residual_rate=excess / count if count else None,
        contributing_games=int(np.count_nonzero(parts[:, 0])),
        per_game=[[int(part[0]), int(part[1]), float(part[2])] for part in parts],
    )


def reconcile_triple(actual, saved, description):
    require(all(agrees(actual[index], saved[field])
                for index, field in enumerate(assessment.BIN_SUMS)), description)


class ResidualAccumulator:
    """checked rows become four separate exhaustive tables and a spatial ledger."""

    def __init__(self, loaded):
        self._loaded = loaded
        comparison = loaded["comparison"]
        self._game_dates = comparison["game_dates"]
        self._game_index = {gid: index for index, gid in enumerate(self._game_dates)}
        self._cell_regions = comparison["regions"]["cell_regions"]
        require(comparison["regions"]["names"] == list(REGION_NAMES)
                and isinstance(self._cell_regions, list) and bool(self._cell_regions)
                and all(type(region) is int and 0 <= region < len(REGION_NAMES)
                        for region in self._cell_regions)
                and self._cell_regions == compound_regions(comparison["geometry"]["centers"]).tolist(),
                "native proxy region domain/map changed")
        domains = dict(
            calendar_month=list(dict.fromkeys(day[:7] for day in self._game_dates.values())),
            original_shot_type=GROUP_DOMAINS["shot_type"],
            preceding_kind=["none", *["recent/" + kind for kind in CONTEXT_CATEGORIES["recent_kind"]]],
            observed_proxy_region=list(REGION_NAMES),
        )
        self._tables = {}
        for quantity in FOCAL_BINS:
            quantity_domains = dict(domains)
            if quantity == "all_attempt_recorded_context":
                quantity_domains["observed_proxy_region"] = [*REGION_NAMES, "blocked_origin_unobserved"]
            self._tables[quantity] = {
                cohort: dict(
                    predictors={name: np.zeros((len(self._game_dates), 3)) for name in PREDICTORS},
                    partitions={family: {
                        key: {name: np.zeros((len(self._game_dates), 3)) for name in PREDICTORS}
                        for key in keys}
                        for family, keys in quantity_domains.items()},
                ) for cohort in ("whole", "focal")
            }
        self._native = {
            name: {quantity: binary_metrics(calibration=False, outcome=outcome)
                   for quantity, (_, outcome) in assessment.QUANTITIES.items()
                   if name == "baseline" or quantity in FOCAL_BINS}
            for name in ("baseline", "historical_stronger")
        }
        self._native_games = {
            name: {quantity: {gid: binary_metrics(calibration=False, outcome=metric["outcome"])
                              for gid in self._game_dates}
                   for quantity, metric in quantities.items()}
            for name, quantities in self._native.items()
        }
        self._spatial = SpatialAccumulator(self._game_dates, comparison)

    def consume(self, row, revised_records):
        original, model_type, month, recent = assessment.saved_descriptors(row)
        applicable = row["status"] == "eligible"
        proxy = row["proxy_cell_id"]
        if applicable and not row["blocked"]:
            require(type(proxy) is int and 0 <= proxy < len(self._cell_regions),
                    "unblocked saved native proxy cell is invalid")
            proxy_region = self._cell_regions[proxy]
        else:
            require(proxy is None, "blocked/inapplicable saved proxy must be null")
            proxy_region = None
        records = {"revision": revised_records}
        for name, quantities in self._native.items():
            predictions = row["predictions"][name]
            fields = {quantity: assessment.QUANTITIES[quantity][0] if name == "baseline" else
                      "benchmark_r" if quantity == "unblocked_conversion" else "benchmark_all"
                      for quantity in quantities}
            require(isinstance(predictions, dict) and set(predictions) == set(fields.values()),
                    "saved control probability quantities disagree")
            records[name] = {}
            for quantity, metric in quantities.items():
                value = predictions[fields[quantity]]
                if not applicable or quantity == "unblocked_conversion" and row["blocked"]:
                    require(value is None, "inapplicable saved control prediction must be null")
                    continue
                require(isinstance(value, dict) and set(value) == {"log_p", "log_not_p"},
                        "saved control complementary log probabilities required")
                positive = not row["blocked"] if metric["outcome"] == "unblocked" else row["goal"]
                record = binary_record(positive, value["log_p"], value["log_not_p"])
                records[name][quantity] = record
                add_binary(metric, record)
                add_binary(self._native_games[name][quantity][row["game_id"]], record)
        self._spatial.consume(row, records, recent, month, model_type, proxy_region)
        if not applicable:
            return
        keys = dict(
            calendar_month=month, original_shot_type=original,
            preceding_kind="none" if recent == "none" else "recent/" + row["previous_event"]["kind"],
            observed_proxy_region="blocked_origin_unobserved" if row["blocked"] else REGION_NAMES[proxy_region],
        )
        index = self._game_index[row["game_id"]]
        for quantity, focal_bin in FOCAL_BINS.items():
            if quantity == "unblocked_conversion" and row["blocked"]:
                continue
            probability = revised_records[quantity]["predicted_probability_sum"]
            own_bin = calibration_bin(probability)
            for cohort in (("whole", "focal") if own_bin == focal_bin else ("whole",)):
                target = self._tables[quantity][cohort]
                for name in PREDICTORS:
                    record = records[name][quantity]
                    triple = [record[field] for field in assessment.BIN_SUMS]
                    target["predictors"][name][index] += triple
                    for family, key in keys.items():
                        target["partitions"][family][key][name][index] += triple

    def finish(self, reconstructed):
        comparison, parent = self._loaded["comparison"], self._loaded["assessment"]
        for quantity, metric in reconstructed["metrics"].items():
            assessment.reconcile_metric(metric, parent["quantities"][quantity]["metrics"], calibration=True)
        for actual, saved in zip(reconstructed["per_game"], parent["per_game"], strict=True):
            require(actual["game_id"] == saved["game_id"] and actual["game_date"] == saved["game_date"],
                    "reconstructed assessment game ledger disagrees")
            for quantity, part in actual["quantities"].items():
                assessment.reconcile_metric(part["metrics"], saved["quantities"][quantity]["metrics"])
        for name, quantities in self._native.items():
            for quantity, metric in quantities.items():
                saved = comparison["probabilities"][quantity]["own"][name]
                finish_binary(metric)
                assessment.reconcile_metric(metric, saved["metrics"])
                require([part["game_id"] for part in saved["per_game"]] == list(self._game_dates),
                        "saved control game ledger disagrees")
                for gid, original in zip(self._game_dates, saved["per_game"], strict=True):
                    part = self._native_games[name][quantity][gid]
                    finish_binary(part)
                    assessment.reconcile_metric(part, original["metrics"])
        localization = dict(
            predictors=list(PREDICTORS), partition_order=list(PARTITIONS),
            triple_fields=list(assessment.BIN_SUMS), interval_units="proportion",
            per_game_axis="diagnosis.game_dates insertion order",
            interpretation="descriptive exhaustive partitions on identical revised membership; separate families overlap and cannot be added; controls are conditional comparisons, not their own calibration bins",
            control_comparison="revision-selected memberships are asymmetric; smaller control residuals do not establish superior own-bin calibration or a causal revision defect",
            quantities={},
        )
        for quantity, cohorts in self._tables.items():
            result = dict(
                population="eligible_unblocked_attempts" if quantity == "unblocked_conversion"
                else "every_eligible_attempt", saved_revised_field=assessment.QUANTITIES[quantity][0],
                partition_interpretation=dict(observed_proxy_region=
                    "conversion conditions on the quantized recorded shooting proxy; regional residuals describe conditional prediction errors"
                    if quantity == "unblocked_conversion" else
                    "realized outcome-path accounting: recorded-context prediction omits focal blocked status and proxy; blocked positive excess is mechanically expected and does not establish a calibration defect"),
            )
            focal_bin = FOCAL_BINS[quantity]
            for cohort, table in cohorts.items():
                predictors = {name: triple_summary(parts) for name, parts in table["predictors"].items()}
                partitions = {}
                for family, groups in table["partitions"].items():
                    partitions[family] = []
                    for key, parts in groups.items():
                        group = dict(key=key, predictors={name: triple_summary(value) for name, value in parts.items()})
                        if family == "original_shot_type":
                            group.update(original_type=key, model_type=MODEL_SHOT_TYPES.get(key))
                        partitions[family].append(group)
                    for name in PREDICTORS:
                        for index in range(len(self._game_dates)):
                            for field_index in range(3):
                                require(agrees(math.fsum(parts[name][index, field_index] for parts in groups.values()),
                                               table["predictors"][name][index, field_index]),
                                        "scalar partition/per-game population reconciliation failed")
                saved_metric = reconstructed["metrics"][quantity]
                if cohort == "focal":
                    saved_metric = saved_metric["calibration"][focal_bin]
                reconcile_triple([predictors["revision"][field] for field in assessment.BIN_SUMS],
                                 saved_metric, "revised scalar cohort does not reconcile to native bins")
                for index, (actual, saved) in enumerate(zip(reconstructed["per_game"], parent["per_game"], strict=True)):
                    expected = actual["quantities"][quantity]["metrics"]
                    inherited = saved["quantities"][quantity]["metrics"]
                    if cohort == "focal":
                        expected, inherited = expected["calibration"][focal_bin], inherited["calibration"][focal_bin]
                    reconcile_triple(table["predictors"]["revision"][index], expected,
                                     "revised scalar per-game cohort disagrees with 03g")
                    reconcile_triple(table["predictors"]["revision"][index], inherited,
                                     "revised scalar per-game cohort disagrees with 03h")
                for name in PREDICTORS:
                    require(all(predictors[name][field] == predictors["revision"][field]
                                for field in ("count", "observed_positive_count")),
                            "scalar control population differs from revised membership")
                    if cohort == "whole" and name != "revision":
                        reconcile_triple([predictors[name][field] for field in assessment.BIN_SUMS],
                                         self._native[name][quantity],
                                         "scalar control whole population does not reconcile")
                        for index, gid in enumerate(self._game_dates):
                            reconcile_triple(table["predictors"][name][index], self._native_games[name][quantity][gid],
                                             "scalar control whole per-game population does not reconcile")
                result[cohort] = dict(predictors=predictors, partitions=partitions)
                if cohort == "focal":
                    original = parent["quantities"][quantity]["bins"][focal_bin]
                    require(original["quantity"] == quantity and original["index"] == focal_bin
                            and original["lower"] == focal_bin / 20 and original["upper"] == (focal_bin + 1) / 20
                            and original["upper_inclusive"] is False,
                            "linked focal assessment bin definition disagrees")
                    reconcile_triple([predictors["revision"][field] for field in assessment.BIN_SUMS], original,
                                     "linked focal assessment cohort disagrees")
                    result[cohort].update(
                        definition=f"revised own bin [{focal_bin / 20:.2f},{(focal_bin + 1) / 20:.2f})",
                        index=focal_bin, lower=focal_bin / 20, upper=(focal_bin + 1) / 20,
                        upper_inclusive=False, inherited_calibration=original,
                    )
            localization["quantities"][quantity] = result
        return localization, self._spatial.finish()


def save_localization_figure(localization, path):
    caption, caption_height = caption_layout([
        "four descriptive partitions of each revised focal cohort; all predictors use the SAME rows. dots show signed excess predicted goals (P−O); labels give n and revision residual rate per 100 attempts. a small group can have a high rate while contributing little excess mass. empty groups retain n=0 and a missing rate without a point. scales match within each partition row; units are common across rows.",
        "conversion denominator: eligible unblocked attempts; recorded-context denominator: every eligible attempt. regions use quantized recorded shooting proxies in native cell partitions; blocked_origin_unobserved assigns no shooting origin. separate partition families overlap and cannot be added.",
        "all-attempt geometry is realized outcome-path accounting: blocked attempts have zero goals by construction, so positive blocked excess does not establish a calibration defect. spatial G_R coherently splits predicted regional goal mass instead.",
        "revision-selected control comparisons are asymmetric; smaller control residuals do not establish superior own-bin calibration or a causal revision defect. no subgroup intervals or significance ranking; 03h's linked cohort intervals remain unchanged. these inspected development data are research-exposed.",
        "native cell-center regions: behind goal x>89 ft; outside attacking zone x≤25 ft; remaining distance to (89,0) is [0,10), [10,20), [20,40), or ≥40 ft. block contacts are never shooting proxies.",
    ], 18)
    figure, axes = plt.subplots(4, 2, figsize=(18, 16 + caption_height), sharex="row")
    extents = dict.fromkeys(PARTITIONS, 0.01)
    for value in localization["quantities"].values():
        for family, groups in value["focal"]["partitions"].items():
            for group in groups:
                for metric in group["predictors"].values():
                    if metric["residual_rate"] is not None:
                        extents[family] = max(extents[family], abs(metric["signed_excess_goals"]))
    for column, (quantity, value) in enumerate(localization["quantities"].items()):
        focal = value["focal"]
        total = focal["predictors"]["revision"]
        for row, family in enumerate(PARTITIONS):
            axis = axes[row, column]
            groups = focal["partitions"][family]
            for name, offset, color in zip(PREDICTORS, (-0.16, 0, 0.16), ("#b65d2b", "#195e83", "#666666"), strict=True):
                points = [(index + offset, group["predictors"][name]["signed_excess_goals"])
                          for index, group in enumerate(groups)
                          if group["predictors"][name]["residual_rate"] is not None]
                axis.scatter([excess for _, excess in points], [position for position, _ in points],
                             s=22, color=color, label=name.replace("_", " "))
            labels = []
            for group in groups:
                key = "missing" if group["key"] is None else str(group["key"])
                if family == "original_shot_type":
                    key += " → " + (group["model_type"] or "missing")
                metric = group["predictors"]["revision"]
                rate = "missing" if metric["residual_rate"] is None else f"{100 * metric['residual_rate']:+.1f}/100"
                labels.append(f"{key}  n={metric['count']:,}  rate={rate}")
            axis.set_yticks(range(len(groups)), labels, fontsize=8)
            axis.set_ylim(len(groups) - 0.5, -0.5)
            axis.set_xlim(-extents[family] * 1.06, extents[family] * 1.06)
            axis.axvline(0, color="#888888", linewidth=0.7)
            axis.grid(axis="x", alpha=0.15)
            axis.spines[["top", "right"]].set_visible(False)
            partition_title = "realized outcome path" if family == "observed_proxy_region" and quantity == "all_attempt_recorded_context" else family.replace("_", " ")
            axis.set_title(f"{partition_title} · {quantity.replace('_', ' ')}\n"
                           f"{focal['definition']}; n={total['count']:,}, goals={total['observed_positive_count']:,}", fontsize=10)
            if row == 0:
                axis.legend(fontsize=8, loc="best")
            axis.set_xlabel("excess predicted goals (P−O)")
    figure.tight_layout(rect=(0, caption_height / (16 + caption_height), 1, 1))
    figure.text(0.015, 0.01, caption, fontsize=8, va="bottom")
    figure.savefig(path, dpi=160)
    plt.close(figure)


def run(completion_path, protocol_path, output_value):
    started = time.monotonic()
    loaded = load_evidence(completion_path)
    protocol = Path(protocol_path).resolve(strict=True)
    loaded["identities"]["protocol"] = identity(protocol)
    output = output_path(output_value, [str(Path(ref["path"]).parent) for ref in loaded["identities"].values()])
    execution = implementation()
    execution.update(platform=platform.platform(), python_executable=sys.executable)
    purpose = loaded["completion"]["purpose"]
    if purpose == "research":
        clean_implementation(execution)
    accumulator = ResidualAccumulator(loaded)
    pass_started = time.monotonic()
    reconstructed = assessment.reconstruct(loaded, diagnostic=accumulator)
    pass_seconds = time.monotonic() - pass_started
    localization, spatial = accumulator.finish(reconstructed)
    if purpose == "research":
        require(reconstructed["coverage"]["attempts_by_status"] == dict(
                    eligible=68775, out_of_scope=16270, unavailable=272)
                and localization["quantities"]["unblocked_conversion"]["whole"]["predictors"]["revision"]["count"] == 49014
                and localization["quantities"]["all_attempt_recorded_context"]["whole"]["predictors"]["revision"]["observed_positive_count"] == 2804,
                "frozen recognized/eligible/unblocked/goal population changed")
        for quantity, counts in (("unblocked_conversion", (2465, 356)),
                                 ("all_attempt_recorded_context", (1999, 192))):
            metric = localization["quantities"][quantity]["focal"]["predictors"]["revision"]
            require((metric["count"], metric["observed_positive_count"]) == counts,
                    "frozen revised focal cohort changed")
    output.mkdir()
    figures = output / "figures"
    figures.mkdir()
    save_localization_figure(localization, figures / "localization.png")
    save_spatial_figure(spatial, figures / "spatial-composition.png")
    figure_identities = {name: identity(figures / name) for name in ("localization.png", "spatial-composition.png")}
    input_bytes = reconstructed["attempts_bytes"] + sum(
        Path(ref["path"]).stat().st_size for name, ref in loaded["identities"].items() if name != "attempts")
    measured = dict(assessment.measured_resources(started), stream_passes=1,
                    stream_pass_seconds=pass_seconds, attempts_bytes_read=reconstructed["attempts_bytes"],
                    input_bytes=input_bytes)
    composition, parent = loaded["composition"], loaded["assessment"]
    diagnosis = dict(
        schema_version=1, artifact_kind="chance_residual_diagnosis", purpose=purpose,
        identities=loaded["identities"], implementation=execution,
        parent_execution=dict(assessment=parent["implementation"],
                              composition=composition["implementation"],
                              fitted_and_assessed_parents=composition["parent_implementations"],
                              original_identities=composition["identities"]),
        inherited_decision=parent["decision"], admission="not_assessed; no handoff",
        population=parent["population"], coverage=reconstructed["coverage"],
        game_dates=loaded["comparison"]["game_dates"],
        localization=localization, spatial=spatial, figures=figure_identities,
        scope="saved-evidence localization and measured assessment-population composition; no causal identification, origin-law validation, recalibration or admission decision",
        resources=measured,
    )
    write_json(output / "diagnosis.json", diagnosis)
    diagnosis_identity = identity(output / "diagnosis.json")
    completion_resources = dict(measured, **assessment.measured_resources(started),
                               output_bytes_before_completion=(output / "diagnosis.json").stat().st_size
                               + sum(Path(ref["path"]).stat().st_size for ref in figure_identities.values()))
    write_json(output / "completion.json", dict(
        schema_version=1, artifact_kind="chance_residual_diagnosis_completion", purpose=purpose,
        identities=loaded["identities"], implementation=execution,
        diagnosis=diagnosis_identity, figures=figure_identities, resources=completion_resources,
    ))
    return diagnosis


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("completion", "protocol", "out"):
        parser.add_argument(f"--{name}", required=True, action=Once)
    args = parser.parse_args()
    try:
        run(Path(args.completion), Path(args.protocol), args.out)
    except (InputContractError, OSError, KeyError, TypeError, ValueError, OverflowError) as error:
        print(f"saved residual diagnosis failed: {error}", file=sys.stderr)
        return 1
    print(f"saved residual diagnosis complete; {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
