"""read-only native-04b response replay and frozen recovery assessment rules."""

import math

import numpy as np

from hockey_stats.artifacts import require
from hockey_stats.attribution_simulation import synthetic_designs
from hockey_stats.shot_origins import grid

SEASONS = tuple(f"{year}{year + 1}" for year in range(2021, 2026))
CASES = ("gaussian", "game_pace")


def native_designs(p: np.ndarray) -> list[dict]:
    """known centered truths on every native cell; no response-derived reference."""
    centers, _ = grid()
    p = np.asarray(p, dtype=float)
    require(p.shape == (656,) and np.isfinite(p).all() and np.all(p > 0)
            and abs(float(p.sum()) - 1) <= 1e-12, "synthetic native shares must be positive and normalized")
    order = np.lexsort((np.arange(len(p)), np.sum((centers - [89, 0]) ** 2, axis=1)))
    stop = int(np.searchsorted(np.cumsum(p[order]), .5, side="left")) + 1
    broad = -np.ones(len(p))
    broad[order[:stop]] = 1
    local = (np.exp(-np.sum((centers - [80, 15]) ** 2, axis=1) / 200)
             - np.exp(-np.sum((centers - [80, -15]) ** 2, axis=1) / 200))
    shapes = []
    for g in (broad, local):
        centered = g - p @ g
        shapes.append(.10 * p * centered / np.max(np.abs(centered)))
    years = synthetic_designs()["paired"]
    for year in years:
        n = len(year["players"])
        scalar = year["scalar_ticks"].astype(float) / 40
        shape = np.zeros((2 * n, len(p)))
        positions = {player: i for i, player in enumerate(year["players"])}
        shape[positions[3]], shape[positions[4]] = shapes[0], -shapes[0]
        shape[positions[18]], shape[positions[19]] = shapes[1], -shapes[1]
        for offset in (0, n):
            scalar[offset:offset + n] -= year["u"] @ scalar[offset:offset + n]
            shape[offset:offset + n] -= year["u"] @ shape[offset:offset + n]
        truth_map = scalar[:, None] * p + shape
        mu = np.column_stack((40 * (p + year["X"] @ truth_map),
                              15 * (1 + year["X"] @ scalar)))
        require(np.isfinite(mu).all() and np.all(mu > 0),
                "native generating rates must be positive without clipping or redrawing")
        require(np.max(np.abs(truth_map.sum(axis=1) - scalar)) <= 1e-14,
                "native truth map does not sum to centered scalar truth")
        year.update(truth_scalar=scalar, truth_shape=shape, truth_map=truth_map, mu=mu, p=p.copy())
    return years


def synthetic_counts(design: dict, case_id: int, outer_id: int, year_index: int) -> np.ndarray:
    """separate response streams in sorted game/stint/direction/native-cell order."""
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40420, case_id, outer_id, year_index])))
    means = design["e"][:, None] * design["mu"]
    if CASES[case_id] == "gaussian":
        variance = design["e"][:, None] * np.concatenate((40 * design["p"], [15]))
        return rng.normal(means, np.sqrt(variance))
    counts = np.empty_like(means)
    for game in range(96):
        pace = rng.gamma(shape=2, scale=.5)
        counts[100 * game:100 * (game + 1)] = rng.poisson(pace * means[100 * game:100 * (game + 1)])
    return counts


def wilson(successes: int, total: int) -> list[float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [center - half, center + half]


def coverage_support(covered: int, total: int) -> dict:
    interval = wilson(covered, total)
    status = ("supported" if interval[0] >= .90 else "failed" if interval[1] < .90 else "inconclusive")
    return dict(covered=covered, n=total, rate=covered / total, wilson=interval, status=status,
                nominal_coverage=.95, developmental_floor=.90)


def false_claim_support(count: int, total: int) -> dict:
    interval = wilson(count, total)
    return dict(count=count, n=total, rate=count / total, wilson=interval,
                status="supported" if interval[1] <= .10 else "failed" if interval[0] > .10 else "inconclusive",
                developmental_ceiling=.10)


def _coverage_summary(rows: list[dict], procedure: str, expected: int) -> dict:
    intervals = [row[procedure] for row in rows if row[procedure] is not None]
    covered = sum(row[procedure]["lower"] <= row["truth"] <= row[procedure]["upper"]
                  for row in rows if row[procedure] is not None)
    result = (coverage_support(covered, expected) if len(intervals) == expected else
              dict(covered=covered, n=expected, rate=None, wilson=None, status="inconclusive",
                   nominal_coverage=.95, developmental_floor=.90,
                   reason="not_data_identified" if rows[0]["identification"] == "not_data_identified" else
                   "incomplete_numerical_execution"))
    result.update(observed=len(intervals), mean_width=float(np.mean([value["upper"] - value["lower"]
                                                                   for value in intervals])) if intervals else None)
    return result


def summarize_recovery(outer: list[dict], protocol: dict) -> dict:
    """claim-by-claim denominators; diagnostics never enlarge the frozen nomination set."""
    expected = protocol["budgets"]["outer_per_case"]
    inner = protocol["budgets"]["inner_refits"]
    actual_ids = [(row["case"], row["outer_id"]) for row in outer]
    expected_ids = {(case, outer_id) for case in CASES for outer_id in range(expected)}
    require(len(actual_ids) == len(set(actual_ids)) and set(actual_ids) <= expected_ids,
            "recovery outer ids must be unique and within the frozen case/replicate budget")
    complete = (set(actual_ids) == expected_ids and all(row["status"] == "complete"
                and row["inner_completed_ids"] == list(range(inner)) for row in outer))
    bins = {}
    for record in outer:
        for cell in record["cells"]:
            bins.setdefault(cell["name"], []).append(cell)
    coverage, false_rows, matrix = [], [], []
    for name, cells in sorted(bins.items()):
        first = cells[0]
        summary = {key: first[key] for key in ("name", "case", "benchmark", "year", "contrast", "role",
            "coefficients", "functional", "group", "nomination", "truth", "relative_truth",
            "exact_relative_truth", "identification", "reason")}
        summary.update(working=_coverage_summary(cells, "working", expected),
                       control_working=_coverage_summary(cells, "control_working", expected),
                       refit=_coverage_summary(cells, "refit", expected),
                       bias=float(np.mean([row["bias"] for row in cells])),
                       rmse=math.sqrt(float(np.mean([row["bias"] ** 2 for row in cells]))),
                       control_bias=float(np.mean([row["control_working"]["mean"] - row["truth"] for row in cells])),
                       control_rmse=math.sqrt(float(np.mean([(row["control_working"]["mean"] - row["truth"]) ** 2
                                                            for row in cells]))))
        summary["working_interval_meaning"] = ("prior-conditioned diagnostic; not data identified"
            if first["identification"] == "not_data_identified" else "gaussian conditional working interval")
        coverage.append(summary)
        if summary["nomination"]:
            matrix.append(dict(name=name, group=summary["group"], rule="refit_coverage",
                               status=summary["refit"]["status"], evidence=summary["refit"]))
        if first["functional"] != "scalar":
            continue
        scalar = {key: summary[key] for key in ("name", "case", "benchmark", "year", "contrast", "group",
                                               "nomination", "relative_truth", "exact_relative_truth")}
        for procedure, field in (("refit", "false_claims"), ("working", "working_false_claims")):
            assertions = [row[field] for row in cells if row[field] is not None]
            count = sum(value["any_false_claim"] for value in assertions)
            result = (false_claim_support(count, expected) if len(assertions) == expected else
                      dict(count=count, n=expected, rate=None, wilson=None, status="inconclusive",
                           reason="not_data_identified" if first["identification"] == "not_data_identified" else
                           "incomplete_numerical_execution"))
            result.update(observed=len(assertions), components={key: sum(value[key] for value in assertions)
                          for key in ("positive_zero_exclusion", "negative_zero_exclusion", "meaningful_positive",
                                      "meaningful_negative", "within_meaningful_band")})
            scalar[procedure] = result
        available = [row for row in cells if row["refit"] is not None]
        scalar["usefulness"] = dict(n=expected, observed=len(available),
            zero_exclusion=sum(row["refit"]["lower"] > 0 or row["refit"]["upper"] < 0 for row in available),
            meaningful_separation=sum(row["meaningful_claim"] in ("meaningful_positive", "meaningful_negative")
                                      for row in available),
            near_zero_resolution=sum(row["meaningful_claim"] == "within_meaningful_band" for row in available),
            mean_relative_width=float(np.mean([(row["refit"]["upper"] - row["refit"]["lower"]) / row["r"]
                                               for row in available])) if available else None,
            interpretation="descriptive resolution at the exact declared truth; no universal power gate")
        false_rows.append(scalar)
        if summary["nomination"]:
            matrix.append(dict(name=name, group=summary["group"], rule="false_claim",
                               status=scalar["refit"]["status"], evidence=scalar["refit"]))
    shape_gains, error_metrics = [], []
    for case_id, case in enumerate(CASES):
        records = [row for row in outer if row["case"] == case]
        keys = sorted({(metric["year"], metric["contrast"]) for row in records for metric in row["map_metrics"]})
        for year, contrast in keys:
            values = [metric for row in records for metric in row["map_metrics"]
                      if metric["year"] == year and metric["contrast"] == contrast]
            error_metrics.append(dict(case=case, year=year, contrast=contrast, observed=len(values),
                n=expected, means={key: float(np.mean([value[key] for value in values])) for key in values[0]
                                   if key not in ("year", "contrast", "unit")}, unit=values[0]["unit"]))
        for contrast_id, contrast in enumerate(("broad", "local")):
            differences = np.asarray([metric["paired_reduction"] for row in records for metric in row["map_metrics"]
                                      if metric["year"] == 5 and metric["contrast"] == contrast])
            interval = None
            if len(differences) == expected:
                rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([40423, case_id, contrast_id])))
                draws = rng.integers(0, expected, size=(protocol["budgets"]["paired_error_resamples"], expected))
                interval = np.quantile(differences[draws].mean(axis=1), [.025, .975], method="linear").tolist()
            status = ("inconclusive" if interval is None else "supported" if interval[0] > 0 else
                      "failed" if interval[1] <= 0 else "inconclusive")
            row = dict(case=case, contrast=contrast, year=5, observed=len(differences), n=expected,
                mean_reduction=float(differences.mean()) if len(differences) else None,
                interval=interval, status=status, seed=[40423, case_id, contrast_id],
                resamples=protocol["budgets"]["paired_error_resamples"],
                unit="paired reduction in squared attempts/60 native map norm",
                reason=None if interval is not None else "incomplete_numerical_execution")
            shape_gains.append(row)
            matrix.append(dict(name=f"{case}/{contrast}/final_native_error_reduction", group=f"native_shape_{contrast}",
                               rule="shape_gain", status=status, evidence=row))
    nomination_coverage = [row for row in coverage if row["nomination"]]
    nomination_false = [row for row in false_rows if row["nomination"]]
    if complete:
        require(len(nomination_coverage) == 12 and len(nomination_false) == 8 and len(shape_gains) == 4,
                "frozen nomination cells differ from 12 coverage / 8 false-claim / 4 shape gains")
    null_records = [row for row in outer if "null_handling" in row]
    null_passed = (len(null_records) == 2 * expected
                   and all(row["null_handling"]["status"] == "passed" for row in null_records))
    if not complete:
        for row in coverage:
            for procedure in ("working", "control_working", "refit"):
                row[procedure].update(status="inconclusive", reason="incomplete_numerical_execution")
        for row in false_rows:
            for procedure in ("working", "refit"):
                row[procedure].update(status="inconclusive", reason="incomplete_numerical_execution")
        for row in shape_gains:
            row.update(status="inconclusive", reason="incomplete_numerical_execution")
        for row in matrix:
            row.update(status="inconclusive", reason="incomplete_numerical_execution")
    groups = []
    for group in ("native_shape_broad", "native_shape_local", "volume", "annual_transition", "paired_sum"):
        rules = [row for row in matrix if row["group"] == group]
        groups.append(dict(group=group, status="supported" if rules and all(row["status"] == "supported" for row in rules)
                           else "failed" if any(row["status"] == "failed" for row in rules) else "inconclusive",
                           rules=[row["name"] + "/" + row["rule"] for row in rules]))
    recommendation = None
    if complete:
        recommendation = ("nominate_revision" if null_passed and all(row["status"] == "supported" for row in matrix) else
                          "mixed" if any(row["status"] == "supported" for row in groups) else
                          "withheld" if any(row["status"] == "failed" for row in matrix) else "inconclusive")
    return dict(status="complete" if complete else "incomplete", support_matrix=matrix, shape_gains=shape_gains,
                coverage_cells=coverage, false_claim_cells=false_rows, error_metrics=error_metrics, claim_groups=groups,
                null_handling=dict(status="passed" if null_passed else "incomplete", outer_checked=len(null_records),
                                   expected_outer=2 * expected,
                                   meaning="individuals 26/31 and their difference retain prior-conditioned diagnostics only"),
                recommendation=recommendation)
