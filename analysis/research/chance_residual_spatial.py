"""saved regional triples, fixed common-support composition and paired uncertainty."""

import hashlib
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hockey_stats.chance import TYPES
from hockey_stats.chance_evaluation import REGION_NAMES
from chance_assessment import BIN_SUMS, RESAMPLING
from chance_review import agrees, calendar_blocks, caption_layout, integer, ratio_interval, require


CONTEXTS = ("none", "recent")
QUANTITIES = ("unblocked", "goal")
PREDICTORS = ("baseline", "revision")
VIEWS = ("full_raw", "common_raw", "standardized")


def compact_triples(values):
    """retain integer labels and counts in the ledger-bound numerical arrays."""
    result = values.tolist()

    def convert(value):
        if isinstance(value[0], list):
            for child in value:
                convert(child)
        else:
            value[0], value[1] = int(value[0]), int(value[1])

    convert(result)
    return result


def support(denominators, blocks):
    record = dict(count=int(denominators.sum()), selected_games=len(denominators),
                  contributing_games=int(np.count_nonzero(denominators)),
                  selected_blocks=None, contributing_blocks=None)
    if blocks is not None:
        n = int(max(blocks)) + 1
        totals = np.bincount(blocks, weights=denominators, minlength=n)
        record.update(selected_blocks=n, contributing_blocks=int(np.count_nonzero(totals)))
    return record


def paired_interval(estimate, draws, denominators, blocks, *, missing_reason=None):
    """paired and weighted statistics keep every undefined draw, without repair."""
    finite = np.isfinite(draws)
    require(estimate is None or math.isfinite(estimate), "nonfinite spatial estimate")
    require(np.all(finite | np.isnan(draws)), "nonfinite spatial bootstrap estimate")
    undefined = int(np.count_nonzero(~finite))
    return dict(estimate=estimate, interval=None if undefined else
                np.percentile(draws, [2.5, 97.5], method="linear").tolist(),
                undefined_draws=undefined,
                missing_reason=missing_reason if undefined else None,
                **support(denominators, blocks))


class SpatialAccumulator:
    """consume checked rows once; own regional validation and additive arithmetic.

    public consume arguments bind the caller's checked descriptors and proxy region.
    finish reconciles native evidence before any composition arithmetic. consumers
    receive ledger-bound triples and rates, never another stream or model execution.
    """

    def __init__(self, game_dates, comparison):
        require(comparison["regions"]["names"] == list(REGION_NAMES)
                and comparison["regions"]["contexts"] == ["all", *CONTEXTS],
                "native region/context domains changed")
        self._game_dates = game_dates
        self._comparison = comparison
        self._months = sorted({day[:7] for day in game_dates.values()})
        self._strata = [(month, shot_type) for month in self._months for shot_type in TYPES]
        self._game_index = {gid: i for i, gid in enumerate(game_dates)}
        self._stratum_index = {key: i for i, key in enumerate(self._strata)}
        self._triples = np.zeros((len(game_dates), len(self._strata), len(CONTEXTS),
                                 len(QUANTITIES), len(REGION_NAMES), len(PREDICTORS), 3))

    def consume(self, row, records, context, month, model_type, proxy_region):
        vectors = row["region_probabilities"]
        require(isinstance(vectors, dict) and set(vectors) == set(PREDICTORS),
                "regional predictor domains disagree")
        if row["status"] != "eligible":
            require(all(value is None for value in vectors.values()),
                    "inapplicable regional predictions must be null")
            return
        require(context in CONTEXTS and (month, model_type) in self._stratum_index,
                "spatial descriptors outside declared domains")
        probabilities = np.empty((len(QUANTITIES), len(REGION_NAMES), len(PREDICTORS)))
        for predictor_index, predictor in enumerate(PREDICTORS):
            require(isinstance(vectors[predictor], dict)
                    and set(vectors[predictor]) == set(QUANTITIES),
                    "regional quantity domains disagree")
            for quantity_index, quantity in enumerate(QUANTITIES):
                values = vectors[predictor][quantity]
                require(isinstance(values, list) and len(values) == len(REGION_NAMES)
                        and all(type(p) in (int, float) and math.isfinite(p) and 0 <= p <= 1
                                for p in values), "six finite regional probabilities required")
                native = "marginal_unblocked" if quantity == "unblocked" else "all_attempt_recorded_context"
                require(agrees(math.fsum(values), records[predictor][native]["predicted_probability_sum"]),
                        "regional probabilities do not sum to saved marginal")
                probabilities[quantity_index, :, predictor_index] = values
        require(all(agrees(a, b) for a, b in zip(probabilities[0, :, 0], probabilities[0, :, 1], strict=True)),
                "conversion replacement changed regional unblocked probabilities")
        require(np.all(probabilities[1] <= probabilities[0] + 1e-10),
                "regional goal probability exceeds unblocked probability")
        observed = np.zeros((len(QUANTITIES), len(REGION_NAMES)))
        if not row["blocked"]:
            observed[0, proxy_region] = 1
            observed[1, proxy_region] = int(row["goal"])
        target = self._triples[self._game_index[row["game_id"]], self._stratum_index[(month, model_type)],
                              CONTEXTS.index(context)]
        target[..., 0] += 1
        target[..., 1] += observed[:, :, None]
        target[..., 2] += probabilities

    def finish(self):
        # native global/context/per-game reconciliation precedes new diagnostics.
        for context in ("all", *CONTEXTS):
            per_game = self._triples.sum(axis=(1, 2)) if context == "all" else \
                self._triples[:, :, CONTEXTS.index(context)].sum(axis=1)
            for predictor_index, predictor in enumerate(PREDICTORS):
                for quantity_index, quantity in enumerate(QUANTITIES):
                    saved_regions = self._comparison["regions"]["summaries"][predictor][quantity][context]
                    require(len(saved_regions) == len(REGION_NAMES), "native regional summary length changed")
                    for region, saved in enumerate(saved_regions):
                        actual = per_game[:, quantity_index, region, predictor_index]
                        require([part["game_id"] for part in saved["per_game"]] == list(self._game_dates),
                                "native regional game ledger disagrees")
                        for values, record in [(actual.sum(axis=0), saved), *zip(actual, saved["per_game"], strict=True)]:
                            require(integer(record["count"]) >= integer(record["observed_positive_count"]),
                                    "native regional labels exceed count")
                            for index, field in enumerate(BIN_SUMS):
                                value = record[field]
                                require(type(value) in (int, float) and math.isfinite(value)
                                        and agrees(values[index], value), f"native regional {field} disagrees")

        counts = self._triples[:, :, :, 0, 0, 0, 0]
        excess = self._triples[:, :, :, :, :, 1, 2] - self._triples[:, :, :, :, :, 1, 1]
        total_counts = counts.sum(axis=0)
        common = np.all(total_counts > 0, axis=1)
        pooled_count = float(total_counts[common].sum())
        weights = np.zeros(len(self._strata))
        if pooled_count:
            weights[common] = total_counts[common].sum(axis=1) / pooled_count
            require(agrees(float(weights.sum()), 1), "common-support weights do not sum to one")
        full_counts, common_counts = counts.sum(axis=1), counts[:, common].sum(axis=1)
        raw_counts = dict(full_raw=full_counts, common_raw=common_counts)
        raw_excess = dict(full_raw=excess.sum(axis=1), common_raw=excess[:, common].sum(axis=1))
        points = {
            view: np.divide(values.sum(axis=0), raw_counts[view].sum(axis=0)[:, None, None],
                            out=np.full((2, 2, 6), np.nan),
                            where=raw_counts[view].sum(axis=0)[:, None, None] != 0)
            for view, values in raw_excess.items()
        }
        points["standardized"] = np.sum(
            weights[common, None, None, None] * excess[:, common].sum(axis=0) /
            total_counts[common, :, None, None], axis=0) if pooled_count else np.full((2, 2, 6), np.nan)
        views = {view: {context: {q: [dict(region=r, methods={}) for r in REGION_NAMES]
                                 for q in QUANTITIES} for context in CONTEXTS} for view in VIEWS}
        contrasts = {view: {q: [dict(region=r, methods={}) for r in REGION_NAMES]
                           for q in QUANTITIES} for view in VIEWS}
        shift = {q: [dict(region=r, methods={}) for r in REGION_NAMES] for q in QUANTITIES}
        methods = dict(games=None, calendar_7_day=calendar_blocks(list(self._game_dates.values()), 7),
                       calendar_14_day=calendar_blocks(list(self._game_dates.values()), 14))
        method_records = {}
        for method, blocks in methods.items():
            n = len(counts) if blocks is None else int(max(blocks)) + 1
            samples = np.random.Generator(np.random.PCG64(RESAMPLING["seed"])).integers(
                0, n, size=(RESAMPLING["draws"], n))
            method_records[method] = dict(selected_games=len(counts), selected_blocks=None if blocks is None else n,
                                          draw_matrix_shape=list(samples.shape),
                                          draw_matrix_sha256=hashlib.sha256(samples.tobytes()).hexdigest())
            multiplicities = np.zeros(samples.shape)
            np.add.at(multiplicities, (np.arange(RESAMPLING["draws"])[:, None], samples), 1)
            unit_counts, unit_excess = counts, excess
            if blocks is not None:
                unit_counts = np.zeros((n, *counts.shape[1:]))
                unit_excess = np.zeros((n, *excess.shape[1:]))
                np.add.at(unit_counts, blocks, counts)
                np.add.at(unit_excess, blocks, excess)
            drawn_counts = (multiplicities @ unit_counts.reshape(n, -1)).reshape(RESAMPLING["draws"], *counts.shape[1:])
            drawn_excess = (multiplicities @ unit_excess.reshape(n, -1)).reshape(RESAMPLING["draws"], *excess.shape[1:])
            drawn = {}
            for view, selected in (("full_raw", np.ones(len(self._strata), dtype=bool)), ("common_raw", common)):
                denominator = drawn_counts[:, selected].sum(axis=1)
                drawn[view] = np.divide(drawn_excess[:, selected].sum(axis=1), denominator[:, :, None, None],
                                        out=np.full((RESAMPLING["draws"], 2, 2, 6), np.nan),
                                        where=denominator[:, :, None, None] != 0)
            if pooled_count:
                ratios = np.divide(drawn_excess[:, common], drawn_counts[:, common, :, None, None],
                                   out=np.full((RESAMPLING["draws"], int(common.sum()), 2, 2, 6), np.nan),
                                   where=drawn_counts[:, common, :, None, None] != 0)
                drawn["standardized"] = np.sum(weights[None, common, None, None, None] * ratios, axis=1)
            else:
                drawn["standardized"] = np.full((RESAMPLING["draws"], 2, 2, 6), np.nan)
            stratum_support = [dict(key=list(key), weight=float(weights[s]),
                                    contexts={c: support(counts[:, s, ci], blocks) for ci, c in enumerate(CONTEXTS)})
                                for s, key in enumerate(self._strata) if common[s]]
            no_common = "no common-support strata"
            standardized_missing = no_common if not pooled_count else "positive-weight stratum absent in at least one resampled draw"
            for view in VIEWS:
                selected_counts = full_counts if view == "full_raw" else common_counts
                for qi, quantity in enumerate(QUANTITIES):
                    for region in range(len(REGION_NAMES)):
                        for ci, context in enumerate(CONTEXTS):
                            if view != "standardized":
                                record = ratio_interval(raw_excess[view][:, ci, qi, region], selected_counts[:, ci],
                                                        RESAMPLING["seed"], blocks=blocks, samples=samples)
                                record.update(support(selected_counts[:, ci], blocks))
                                if view == "common_raw" and not pooled_count:
                                    record["missing_reason"] = no_common
                            else:
                                point = points[view][ci, qi, region]
                                record = paired_interval(float(point) if np.isfinite(point) else None,
                                                         drawn[view][:, ci, qi, region], selected_counts[:, ci], blocks,
                                                         missing_reason=standardized_missing)
                                record["per_stratum_support"] = [dict(key=s["key"], weight=s["weight"], **s["contexts"][context])
                                                                   for s in stratum_support]
                            require(record["estimate"] is None and not np.isfinite(points[view][ci, qi, region])
                                    or record["estimate"] is not None and agrees(record["estimate"], points[view][ci, qi, region]),
                                    "spatial point estimate disagrees with native pooled helper")
                            views[view][context][quantity][region]["methods"][method] = record
                        point = points[view][1, qi, region] - points[view][0, qi, region]
                        paired = drawn[view][:, 1, qi, region] - drawn[view][:, 0, qi, region]
                        reason = standardized_missing if view == "standardized" else \
                            no_common if view == "common_raw" and not pooled_count else \
                            "context denominator absent in at least one resampled draw"
                        record = paired_interval(float(point) if np.isfinite(point) else None, paired,
                                                 selected_counts.sum(axis=1), blocks, missing_reason=reason)
                        record["counts_by_context"] = {c: int(selected_counts[:, ci].sum()) for ci, c in enumerate(CONTEXTS)}
                        if view == "standardized":
                            record["per_stratum_support"] = stratum_support
                        contrasts[view][quantity][region]["methods"][method] = record
            for qi, quantity in enumerate(QUANTITIES):
                for region in range(len(REGION_NAMES)):
                    point = points["standardized"][1, qi, region] - points["standardized"][0, qi, region] - \
                        (points["common_raw"][1, qi, region] - points["common_raw"][0, qi, region])
                    paired = drawn["standardized"][:, 1, qi, region] - drawn["standardized"][:, 0, qi, region] - \
                        (drawn["common_raw"][:, 1, qi, region] - drawn["common_raw"][:, 0, qi, region])
                    record = paired_interval(float(point) if np.isfinite(point) else None, paired,
                                             common_counts.sum(axis=1), blocks, missing_reason=standardized_missing)
                    record.update(per_stratum_support=stratum_support,
                                  counts_by_context={c: int(common_counts[:, ci].sum()) for ci, c in enumerate(CONTEXTS)})
                    shift[quantity][region]["methods"][method] = record

        if self._comparison["purpose"] == "research":
            for context in CONTEXTS:
                for quantity in QUANTITIES:
                    for region, record in enumerate(views["full_raw"][context][quantity]):
                        actual = record["methods"]["games"]
                        saved = self._comparison["regions"]["summaries"]["revision"][quantity][context][region]["residual_interval"]
                        require(all(actual[field] == saved[field] for field in
                                    ("count", "contributing_games", "undefined_draws")),
                                "native full-raw game interval support disagrees")
                        require(actual["estimate"] is None and saved["estimate"] is None or
                                actual["estimate"] is not None and saved["estimate"] is not None
                                and agrees(actual["estimate"], saved["estimate"] / 100),
                                "native full-raw game interval estimate disagrees")
                        require(actual["interval"] is None and saved["interval"] is None or
                                actual["interval"] is not None and saved["interval"] is not None
                                and all(agrees(a, b / 100) for a, b in zip(actual["interval"], saved["interval"], strict=True)),
                                "native full-raw game interval bounds disagree")

        strata = []
        coverage = {c: {} for c in CONTEXTS}
        for s, key in enumerate(self._strata):
            strata.append(dict(key=list(key), common_support=bool(common[s]),
                               weight=float(weights[s]) if common[s] else None,
                               missing_reason=None if common[s] else "stratum absent in at least one original context",
                               contexts={c: dict(**support(counts[:, s, ci], None),
                                                 triples=compact_triples(self._triples[:, s, ci].sum(axis=0)))
                                         for ci, c in enumerate(CONTEXTS)}))
        for ci, context in enumerate(CONTEXTS):
            for label, selected in (("full", np.ones(len(self._strata), dtype=bool)), ("common", common), ("excluded", ~common)):
                coverage[context][label] = dict(**support(counts[:, selected, ci].sum(axis=1), None),
                                                triples=compact_triples(self._triples[:, selected, ci].sum(axis=(0, 1))))
        return dict(
            domains=dict(months=self._months, model_shot_types=list(TYPES), contexts=list(CONTEXTS),
                         quantities=list(QUANTITIES), regions=list(REGION_NAMES), predictors=list(PREDICTORS),
                         strata=[list(key) for key in self._strata], game_axis="diagnosis.game_dates insertion order",
                         per_game_axis_order=["game", "stratum", "context", "quantity", "region", "predictor", "triple"],
                         summary_triple_axis_order=["quantity", "region", "predictor", "triple"], triple_fields=list(BIN_SUMS)),
            per_game=compact_triples(self._triples), strata=strata,
            common_support=dict(pooled_count=int(pooled_count), stratum_indices=np.flatnonzero(common).tolist(),
                                missing_reason=None if pooled_count else "no common-support strata",
                                excluded_strata=[list(key) for s, key in enumerate(self._strata) if not common[s]],
                                definition="positive original counts in both contexts; fixed pooled original weights"),
            coverage=coverage, views=views, contrasts=contrasts, adjustment_shift=shift,
            resampling=dict(RESAMPLING, methods=method_records, interval_units="proportion", confidence=.95,
                            undefined="null interval if any required draw is undefined; no redraw, reweighting or support changes",
                            interpretation="shared paired draws condition on saved fits and original common support/weights; fitting, selection and origin-law uncertainty excluded"),
            definition="all eligible attempts in context; unblocked and recorded proxy in region, or goal and recorded proxy in region; blocked labels zero without an assigned origin",
            predictor="revision; regional unblocked probabilities unchanged from baseline",
            reconciled=dict(native_regional_global_context_and_per_game=True),
        )


def save_spatial_figure(spatial, path):
    """two quantities, three methods, three views; absent intervals stay visible."""
    colors = {"full_raw": "#777777", "common_raw": "#287a96", "standardized": "#a15e38"}
    titles = {"games": "whole games", "calendar_7_day": "seven-day calendar", "calendar_14_day": "fourteen-day calendar"}
    caption, height = caption_layout([
        "recent minus none signed residual contrasts; positive means more excess predicted probability in recent context. every context denominator includes all eligible attempts, including blocks. points and intervals are per 100 eligible attempts.",
        "native cell-center regions use behind-goal x > 89 and outside-zone x ≤ 25 precedence, then distance to (89,0) in 0–10, 10–20, 20–40 and 40+ feet. they describe recorded unblocked proxies; blocked compound labels are zero without assigned origins. full to common changes population; common to standardized applies fixed pooled month × shot-type weights. A is unchanged by conversion replacement; G includes conversion.",
        "filled points have pointwise 95% linear-percentile intervals; open points explicitly mark absent intervals. missing point estimates are labeled at the right. paired draws condition on saved fits and original support/weights; fitting, selection and origin-law uncertainty excluded. global calendar draws may omit positive-weight strata; no redraw or reweighting.",
    ], 15)
    fig, axes = plt.subplots(2, 3, figsize=(15, 7 + height), sharex="row", sharey=True)
    labels = [r.replace("_", " ") for r in REGION_NAMES]
    for qi, quantity in enumerate(QUANTITIES):
        for mi, method in enumerate(titles):
            ax = axes[qi, mi]
            for vi, view in enumerate(VIEWS):
                offset = (vi - 1) * .2
                for region, record in enumerate(spatial["contrasts"][view][quantity]):
                    result = record["methods"][method]
                    y = region + offset
                    if result["estimate"] is None:
                        ax.text(.98, y, f"{view.replace('_', ' ')}: no estimate", transform=ax.get_yaxis_transform(),
                                ha="right", va="center", fontsize=6, color=colors[view])
                        continue
                    estimate = 100 * result["estimate"]
                    present = result["interval"] is not None
                    ax.plot(estimate, y, "o", color=colors[view], markerfacecolor=colors[view] if present else "none", ms=4)
                    if present:
                        ax.hlines(y, *(100 * np.asarray(result["interval"])), color=colors[view], lw=1)
            ax.axvline(0, color="#333333", lw=.7)
            ax.set_yticks(np.arange(len(labels)), labels, fontsize=8)
            ax.set_title(f"{quantity} and proxy in region; {titles[method]}", fontsize=10)
            ax.set_xlabel("recent − none, percentage points", fontsize=8)
            standardized = spatial["contrasts"]["standardized"][quantity][0]["methods"][method]
            if standardized["interval"] is None:
                ax.text(.02, .01, f"standardized interval absent: {standardized['undefined_draws']}/2000 undefined draws",
                        transform=ax.transAxes, fontsize=7, va="bottom")
    axes[0, 0].invert_yaxis()
    fig.legend(handles=[plt.Line2D([], [], marker="o", color=colors[view], linestyle="none", label=view.replace("_", " "))
                        for view in VIEWS], loc="upper center", ncols=3, fontsize=9)
    fig.tight_layout(rect=(0, height / fig.get_figheight(), 1, .96))
    fig.text(.035, .02, caption, fontsize=8, va="bottom")
    fig.savefig(path, dpi=180)
    plt.close(fig)
