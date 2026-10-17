"""04j's response-free deployment information and saved selector closure."""

import argparse
import csv
import json
import os
from pathlib import Path
import sys
import time

for _thread in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_thread] = "1"

import numpy as np
from scipy.linalg import block_diag, helmert

from hockey_stats.artifacts import (
    artifact, clean_implementation, json_values, linked_path, load_arrays,
    ordered_array_digest, read_artifact, require, resources, write_arrays, write_json,
)
from hockey_stats.attribution_data import (
    contrast_information, deployment_accounting,
    deployment_design_from_rows, exposure_centering, likelihood_spectrum,
    physical_history_information, read_real_deployment_designs, read_synthetic_deployment_designs,
)
from hockey_stats.attribution_simulation import shape_operators, shape_regions
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path, read_json


SPEC = Path(__file__).resolve().parents[2]/"docs/specs/04j-attribution-deployment.md"
RESEARCH_ROOT = Path("/Volumes/Expansion/hockey-stats/runs")
SEASONS = tuple(f"{year}{year+1}" for year in range(2021, 2026))
REAL_RESULT_SHA256 = "d0c0f6a7af3888cd0d0920d152f322447a984cbc20edac596aa70f60dbb0f2de"
SYNTHETIC_RESULT_SHA256 = "c962c9d4c38c86150fceff15036c1f19bc5bfea897127b7fd08d4f929cdcdbb7"
SELECTION_RESULT_SHA256 = "c32ac2c9b03584c0435e9be2a23d621ec80b1bb15ef748f64e1b4146584dfd19"
RULES = dict(
    population="unblocked_spatial", assumptions=["annual", "constant_history"],
    physical_information="L_y=H_y/r_y**2; sum identity-aligned L_y with separate annual contexts",
    reference="annual exposure weights; identical final-current weights for annual/history targets",
    cutoff_factors=[.1, 1., 10.], tau="100*dimension*float64_eps*lambda_max",
    null_relative_tolerance=1e-8, overlap_integer_atol=1e-6,
    eigen_residual_max=1e-10, gauge_residual_max=1e-10, solve_residual_max=1e-8,
    svd_atol=1e-10, svd_rtol=1e-6, svd_null_atol=1e-8,
    minutes_bins=[0, 300, 600, 1000], quantile="linear",
    units="redistributed recorded unblocked attempts/60", new_responses=0, new_fits=0,
)
LIMITS = [
    "sampling standard deviations condition on independent-row reference noise and unchanged unknown context means",
    "no empirical game-noise calibration, observed player effects or universal estimation limit is supplied",
    "constant physical effects across seasons are a diagnostic assumption; false persistence can supply misleading precision",
    "coverage is matched and selective; presence does not establish complete-season exposure or nhl debut",
    "real and synthetic designs have different contexts; their comparison does not isolate teammate mixing",
    "total native shape is zero by construction; volume is not known",
    "no chance valuation, model admission, publication or website change follows",
]


def _cost(started, process_started, root, *, input_bytes=0):
    return dict(**resources(started), process_seconds=time.process_time()-process_started,
        input_bytes=input_bytes, input_bytes_scope="unique bound selected-source files; full archive bytes",
        output_bytes=sum(path.stat().st_size for path in root.rglob("*") if path.is_file()),
        output_bytes_scope="tree_before_current_manifest_serialization")


def _reference(path):
    return identity(Path(path).absolute())


def _selected_result(reference, kind, sha256):
    require(reference["sha256"] == sha256, "research result differs from pinned source")
    document = read_json(linked_path(reference))
    require(document["kind"] == kind and document["purpose"] == "research"
        and (document["completion"] if kind == "attribution_revision_result" else document["execution_status"]) == "complete",
        "selected research result is incomplete or wrong")
    clean_implementation(document["implementation"])
    return document


def selector_closure(synthetic_result, selection_result):
    """copy exactly 46 inspected summary rows; never score responses or tune a grid."""
    selected = []
    sources = (
        ("04h", _selected_result(synthetic_result, "attribution_resolution_result", SYNTHETIC_RESULT_SHA256)),
        ("04i", _selected_result(selection_result, "attribution_selection_result", SELECTION_RESULT_SHA256)),
    )
    settings = dict(sparse=3.1622776601683795e-5, diffuse=.0001)
    for study, document in sources:
        reports = [ref for ref in document["reports"] if Path(ref["path"]).name == "comparison.csv"]
        require(len(reports) == 1, f"{study}: exact comparison report is absent or duplicated")
        reference = reports[0]
        with linked_path(reference).open(newline="", encoding="utf-8") as source:
            for number, row in enumerate(csv.DictReader(source), 2):
                if study == "04h":
                    if not (row["population"] in settings and row["law"] in ("gaussian", "game_pace")
                        and row["condition"] == "broad" and row["target"] == "twelve_region_vector"
                        and row["spatial_modes"] == "11" and row["metric"] in ("risk", "rms", "prediction_excess")):
                        continue
                    fixed = row["record_type"] == "fixed_curve" and float(row["prior_variance"]) == settings[row["population"]]
                    adaptive = row["record_type"] == "comparison" and row["arm"] == "adaptive"
                    if not (fixed or adaptive):
                        continue
                    label = "expected, inspected fixed setting" if fixed else "realized adaptive selection"
                else:
                    score = row["record_type"] == "diagnostic_selected_score" and row["metric"] in (
                        "score", "realized_error_minus_zero", "post_selection_optimism")
                    null = (row["record_type"] == "diagnostic_target" and row["population"] == "null"
                        and row["partition"] == "all" and row["target"] == "twelve_region_vector"
                        and row["metric"] in ("candidate_risk", "control_risk"))
                    if not (score or null):
                        continue
                    label = "saved observable-selector diagnostic" if score else "realized null risk"
                values = {name: float(row[name]) if row[name] else None for name in ("mean", "lower", "upper")}
                require(all(value is None or np.isfinite(value) for value in values.values()), "nonfinite saved closure value")
                units = (RULES["units"] if row["metric"] == "rms" else
                    "squared redistributed recorded unblocked attempts/60; inverse-share-weighted spatial prediction excess relative to zero player shape" if row["metric"] == "prediction_excess" else
                    "squared redistributed recorded unblocked attempts/60")
                selected.append(dict(source_study=study, source=reference, source_row=number,
                    selectors={name: value for name, value in row.items() if name not in ("mean", "lower", "upper", "reason")},
                    population=row["population"], law=row["law"], metric=row["metric"], label=label,
                    units=units, reason=row["reason"] or None, **values))
    require(len(selected) == 46 and sum(row["source_study"] == "04h" for row in selected) == 24,
        "selector closure does not contain the frozen 24+22 summary rows")
    identities = [(row["source_study"], json.dumps(row["selectors"], sort_keys=True)) for row in selected]
    require(len(set(identities)) == 46, "duplicate selector-closure row")
    return selected


def _fixture(reference):
    document = read_json(linked_path(reference))
    require(document["kind"] == "attribution_deployment_fixture" and document["schema_version"] == 1
        and document["purpose"] == "fixture_exercise" and len(document["seasons"]) == 3
        and list(document["designs"]) == ["real", "synthetic"], "invalid deployment fixture contract")
    archive = dict(document)
    archive["arrays"] = dict(document["arrays"], path=str(linked_path(reference).parent/document["arrays"]["path"]))
    arrays, designs = load_arrays(archive), {}
    fields = ("H", "xbar", "stratum_weight", "player_exposure", "u", "p")
    row_fields = ("offense", "defense", "seconds", "si", "row_game_ids")
    for name, entries in document["designs"].items():
        require([row["season"] for row in entries] == document["seasons"], "fixture seasons differ from design order")
        current = []
        for entry in entries:
            prefix = entry["prefix"]
            values = {key: arrays[f"{prefix}_{key}"] for key in (*fields, *row_fields)}
            rows = {key: values[key] for key in (*row_fields, "u", "player_exposure")}
            source_refs = dict(fixture=reference, arrays=archive["arrays"], row_count=len(values["seconds"]),
                coverage=dict(kind="explicit synthetic rows", complete=True), masks=dict(kind="synthetic fixture"))
            design = deployment_design_from_rows(season=entry["season"], player_ids=tuple(entry["player_ids"]),
                strata=tuple(map(tuple, entry["strata"])), arrays=rows, p=values["p"], r=entry["r"], source_refs=source_refs)
            require(all(np.array_equal(getattr(design, key), values[key]) if key in ("u", "p", "player_exposure")
                else np.allclose(getattr(design, key), values[key], atol=1e-10, rtol=1e-12) for key in fields),
                "fixture moments differ from independently explicit rows")
            current.append(design)
        designs[name] = tuple(current)
    return document, designs


def _research(parents):
    _selected_result(parents["real_result"], "attribution_revision_result", REAL_RESULT_SHA256)
    _selected_result(parents["synthetic_result"], "attribution_resolution_result", SYNTHETIC_RESULT_SHA256)
    _selected_result(parents["selection_result"], "attribution_selection_result", SELECTION_RESULT_SHA256)
    real = read_real_deployment_designs(parents["real_result"], SEASONS)
    synthetic = read_synthetic_deployment_designs(parents["synthetic_result"], SEASONS, real[0].p)
    require([len(row.player_ids) for row in real] == [1003, 951, 924, 910, 940]
        and [row.source_refs["row_count"] for row in real] == [698940, 881742, 864050, 857462, 881612]
        and all(len(row.strata) == 42 for row in real)
        and all(len(row.player_ids) == 32 and len(row.strata) == 6 and row.source_refs["row_count"] == 9600
            and row.source_refs["games"] == 96 and row.r == 40. for row in synthetic),
        "research annual populations, contexts or directed row counts differ")
    require(len({player for row in real for player in row.player_ids}) == 1477
        and len({player for row in synthetic for player in row.player_ids}) == 34,
        "research identity unions differ")
    return dict(real=real, synthetic=synthetic)


def _history(designs, year, player):
    years = [row.season for row in designs[:year+1] if player in row.player_ids]
    return dict(history_seasons=years, observed_seasons=len(years), first_observed=len(years) == 1,
        history_minutes=sum(float(row.player_exposure[row.player_ids.index(player)]/60)
            for row in designs[:year+1] if player in row.player_ids),
        return_after_absence=year > 0 and len(years) > 1 and player not in designs[year-1].player_ids)


def _maximum_pair(player_ids, accounting):
    seconds = accounting["same_team_seconds"].copy()
    np.fill_diagonal(seconds, -1)
    maximum = int(seconds.max())
    pairs = [(a, b) for i, a in enumerate(player_ids) for j, b in enumerate(player_ids)
        if i < j and int(seconds[i, j]) == maximum]
    return min(pairs)


def _cases(designs, accountings, declared):
    if declared is not None:
        require(set(declared) == {"real", "synthetic"}, "fixture case design labels differ")
        cases = declared
    else:
        pair = _maximum_pair(designs["real"][-1].player_ids, accountings["real"][-1])
        cases = dict(real=[dict(label="historical_scalar_shared", members=[8476460, 8478398], coefficients=[1., -1.]),
            dict(label="historical_scalar_no_shared", members=[8480336, 8480800], coefficients=[1., -1.]),
            dict(label="maximum_final_spatial_shared", members=list(pair), coefficients=[1., -1.])],
            synthetic=[dict(label="inseparable_26_31_difference", members=[26, 31], coefficients=[1., -1.]),
                dict(label="inseparable_26_31_mean", members=[26, 31], coefficients=[.5, .5])])
    for name, rows in cases.items():
        require(len({row["label"] for row in rows}) == len(rows), "duplicate case label")
        for row in rows:
            require(len(row["members"]) == len(row["coefficients"]) > 0
                and len(set(row["members"])) == len(row["members"])
                and all(type(player) is int for player in row["members"])
                and all(np.isfinite(value) for value in row["coefficients"]), "invalid explicit case coefficients")
    return cases


def _inventory(designs, accountings, cases):
    inventory, references = [], []
    for name, annual in designs.items():
        union = sorted({player for row in annual for player in row.player_ids})
        for year, (row, accounting) in enumerate(zip(annual, accountings[name], strict=True)):
            reference = f"{name}:{row.season}:exposure"
            reference_digest = ordered_array_digest(dict(player_ids=np.asarray(row.player_ids, dtype=np.int64), u=row.u))
            references.append(dict(id=reference, player_ids=row.player_ids, weights=row.u, sha256=reference_digest))
            inventory.append(dict(design=name, assumption="annual", season=row.season, final_target=year == len(annual)-1,
                source_refs=row.source_refs, coverage=row.source_refs["coverage"], masks=row.source_refs["masks"],
                player_ids=row.player_ids, current_players=len(row.player_ids),
                union_players=len(union), context_count=len(row.strata), strata=row.strata, rate=row.r,
                exposure_seconds=float(row.player_exposure.sum()), directed_team_seconds=accounting["directed_team_seconds"],
                physical_elapsed_seconds=accounting["physical_elapsed_seconds"],
                first_observed_count=sum(_history(annual, year, player)["first_observed"] for player in row.player_ids),
                return_after_absence_count=sum(_history(annual, year, player)["return_after_absence"] for player in row.player_ids),
                reference=reference, reference_sha256=reference_digest, p_sha256=ordered_array_digest(dict(p=row.p)),
                reconstruction=accounting["reconstruction_residuals"]))
        final = inventory[-1]
        inventory.append(dict(final, assumption="constant_history", player_ids=union, annual_rates=[row.r for row in annual],
            rate=None, context_count=sum(len(row.strata) for row in annual), contexts_per_season=[len(row.strata) for row in annual],
            source_refs={row.season: row.source_refs for row in annual},
            strata={row.season: row.strata for row in annual},
            coverage={row.season: row.source_refs["coverage"] for row in annual},
            masks={row.season: row.source_refs["masks"] for row in annual},
            reconstruction={row.season: accounting["reconstruction_residuals"]
                for row, accounting in zip(annual, accountings[name], strict=True)},
            entry_return_count_scope="final-current target; first observed or returned in final year",
            exposure_seconds=float(sum(row.player_exposure.sum() for row in annual)),
            directed_team_seconds=sum(accounting["directed_team_seconds"] for accounting in accountings[name]),
            physical_elapsed_seconds=sum(accounting["physical_elapsed_seconds"] for accounting in accountings[name])))
    annual_count = sum(2*len(row.player_ids) for annual in designs.values() for row in annual)
    history_count = sum(2*len(annual[-1].player_ids) for annual in designs.values())
    case_labels = sum(4*len(rows) for rows in cases.values())
    absent = sum(4*sum(not set(row["members"]).issubset(designs[name][-1].player_ids) for row in rows)
        for name, rows in cases.items())
    distinct_cases = sum(4*len({tuple(sorted(zip(row["members"], row["coefficients"], strict=True))) for row in rows
        if set(row["members"]).issubset(designs[name][-1].player_ids)}) for name, rows in cases.items())
    budget = dict(spectra=sum(len(annual)+1 for annual in designs.values()), annual_player_contrasts=annual_count,
        historical_player_contrasts=history_count, case_labels=case_labels, contrast_rows=annual_count+history_count+case_labels,
        distinct_calculations=annual_count+history_count+distinct_cases, absent_case_labels=absent, svd_probes=12,
        svd_decompositions=2, new_responses=0, new_fits=0)
    return json_values(inventory), json_values(references), budget


def _sources(parents, purpose):
    if purpose == "research":
        return _research(parents), None
    document, designs = _fixture(parents["fixture_designs"])
    return designs, document


def prepare(real_result=None, synthetic_result=None, selection_result=None, fixture_designs=None, *, purpose, output):
    started, process_started = time.monotonic(), time.process_time()
    require(purpose in ("research", "fixture_exercise"), "invalid deployment purpose")
    require((purpose == "research" and fixture_designs is None and all((real_result, synthetic_result, selection_result)))
        or (purpose == "fixture_exercise" and fixture_designs is not None and not any((real_result, synthetic_result, selection_result))),
        "fixture input and three research parents are mutually exclusive")
    parents = ({"real_result": _reference(real_result), "synthetic_result": _reference(synthetic_result),
        "selection_result": _reference(selection_result)} if purpose == "research" else {"fixture_designs": _reference(fixture_designs)})
    designs, fixture = _sources(parents, purpose)
    first = designs["real"][0].p
    require(all(np.array_equal(row.p, first) for annual in designs.values() for row in annual),
        "annual native spatial references differ; substitution is forbidden")
    accountings = {name: [deployment_accounting(row) for row in annual] for name, annual in designs.items()}
    cases = _cases(designs, accountings, None if fixture is None else fixture["cases"])
    inventory, references, budget = _inventory(designs, accountings, cases)
    if purpose == "research":
        require(budget["spectra"] == 12 and budget["annual_player_contrasts"] == 9776
            and budget["historical_player_contrasts"] == 1944 and budget["case_labels"] == 20
            and budget["contrast_rows"] == 11740, "research contrast budget differs")
    else:
        expected = fixture["expected_inventory"]
        require(all(budget[key] == expected[key] for key in (
                "spectra", "annual_player_contrasts", "historical_player_contrasts", "case_labels",
                "contrast_rows", "distinct_calculations", "absent_case_labels"))
            and budget["spectra"] == 8 and budget["annual_player_contrasts"] == 144
            and budget["historical_player_contrasts"] == 48
            and expected["current_players_per_season"] == 12 and expected["union_players_per_design"] == 14
            and all(len(row.player_ids) == 12 for annual in designs.values() for row in annual)
            and all(len({player for row in annual for player in row.player_ids}) == 14 for annual in designs.values()),
            "fixture expected inventory differs")
    closure = selector_closure(parents["synthetic_result"], parents["selection_result"]) if purpose == "research" else []
    selected_refs = {ref["path"]: ref for annual in designs.values() for row in annual
        for ref in row.source_refs.values() if isinstance(ref, dict) and set(ref) == {"path", "sha256"}}
    selected_refs.update({row["source"]["path"]: row["source"] for row in closure})
    selected_paths = [Path(ref["path"]).resolve(strict=True) for ref in selected_refs.values()]
    input_bytes = sum(path.stat().st_size for path in set(selected_paths))
    roots = [str(path.parent) for path in selected_paths]
    root = output_path(str(output), roots)
    if purpose == "research":
        require(root.is_relative_to(RESEARCH_ROOT) and any(part.startswith("attribution-04j-") for part in root.parts),
            "research requires an external attribution-04j run directory")
    root.mkdir()
    snapshot = root/"spec-snapshot.md"
    with snapshot.open("xb") as destination:
        destination.write(SPEC.read_bytes())
    W, names = shape_regions()
    operators = shape_operators(W)
    operator_identity = ordered_array_digest(dict(p=first, W=W, near=operators[1], lateral=operators[2]))
    fields = dict(sources=parents, seasons=[row.season for row in designs["real"]], inventory=inventory,
        references=references, cases=cases, budget=budget, p_sha256=ordered_array_digest(dict(p=first)),
        operator_sha256=operator_identity, region_names=list(names), selector_closure=closure,
        closure_status="saved_summary_rows" if purpose == "research" else "not_applicable,fixture_exercise")
    protocol = artifact("attribution_deployment_protocol", purpose, dict(**parents, spec_snapshot=identity(snapshot)),
        schema_version=1, rules=RULES, **fields, resources=_cost(started, process_started, root, input_bytes=input_bytes))
    protocol_path = root/"protocol.json"
    write_json(protocol_path, json_values(protocol))
    document = artifact("attribution_deployment_prepared", purpose, dict(**parents, protocol=identity(protocol_path)),
        schema_version=1, protocol=identity(protocol_path), **fields,
        resources=_cost(started, process_started, root, input_bytes=input_bytes))
    path = root/"prepared.json"
    write_json(path, json_values(document))
    return identity(path)


def read_prepared(path):
    reference = _reference(path)
    document = read_artifact(linked_path(reference), "attribution_deployment_prepared", expected_schema=1)
    protocol = read_artifact(linked_path(document["protocol"]), "attribution_deployment_protocol", expected_schema=1)
    fields = ("sources", "seasons", "inventory", "references", "cases", "budget", "p_sha256", "operator_sha256",
        "region_names", "selector_closure", "closure_status")
    require(document["purpose"] == protocol["purpose"] and protocol["rules"] == RULES
        and all(document[field] == protocol[field] for field in fields), "deployment preparation and protocol differ")
    designs, fixture = _sources(document["sources"], document["purpose"])
    require(all(np.array_equal(row.p, designs["real"][0].p) for annual in designs.values() for row in annual),
        "prepared native spatial references differ")
    accountings = {name: [deployment_accounting(row) for row in annual] for name, annual in designs.items()}
    cases = _cases(designs, accountings, None if fixture is None else fixture["cases"])
    inventory, references, budget = _inventory(designs, accountings, cases)
    require(document["inventory"] == inventory and document["references"] == references
        and document["cases"] == cases and document["budget"] == budget,
        "prepared selected design inventory, references, cases or budget differ")
    return reference, document, designs, accountings


def _targets(name, annual, year, accounting, cases, assumption):
    design = annual[year]
    n, rows, coefficients = len(design.player_ids), [], []
    reference = f"{name}:{design.season}:exposure"
    for role_index, role in enumerate(("offense", "defense")):
        for i, player in enumerate(design.player_ids):
            shared = accounting["same_team_seconds"][i].copy()
            shared[i] = -1
            partner_index = int(np.argmax(shared))
            partner = design.player_ids[partner_index]
            c = np.zeros(2*n)
            c[role_index*n+i] = 1.
            rows.append(dict(design=name, assumption=assumption, season=design.season, final_target=year == len(annual)-1,
                role=role, role_label="offense" if role == "offense" else "attempts allowed", record_type="player_reference",
                label=str(player), player_id=player, members=[player], coefficients=[1.], reference=reference,
                minutes=float(design.player_exposure[i]/60), member_minutes=[float(design.player_exposure[i]/60)],
                strongest_partner_id=partner, shared_minutes=float(shared[partner_index]/60),
                without_partner_minutes=float((design.player_exposure[i]-shared[partner_index])/60),
                opponent_minutes=float(accounting["opponent_seconds"][i, partner_index]/60),
                **_history(annual, year, player)))
            coefficients.append(c)
        if year != len(annual)-1:
            continue
        for case in cases:
            present = set(case["members"]).issubset(design.player_ids)
            indices = [design.player_ids.index(player) for player in case["members"]] if present else []
            c = np.zeros(2*n)
            if present:
                c[role_index*n+np.asarray(indices)] = case["coefficients"]
            pair = len(indices) == 2
            together = int(accounting["same_team_seconds"][tuple(indices)]) if pair else None
            rows.append(dict(design=name, assumption=assumption, season=design.season, final_target=True,
                role=role, role_label="offense" if role == "offense" else "attempts allowed", record_type="case",
                label=case["label"], player_id=None, members=case["members"], coefficients=case["coefficients"],
                reference=reference, minutes=None, member_minutes=[float(design.player_exposure[i]/60) for i in indices],
                shared_minutes=None if together is None else together/60,
                without_partner_minutes=[float((design.player_exposure[i]-together)/60) for i in indices] if pair else None,
                opponent_minutes=float(accounting["opponent_seconds"][tuple(indices)]/60) if pair else None,
                absent=not present, history_seasons={str(player): _history(annual, year, player)["history_seasons"]
                    for player in case["members"]} if present else {}))
            coefficients.append(c)
    return rows, np.column_stack(coefficients)


def _spectrum_checks(L, spectrum, D, information):
    values, vectors, tau, masks = spectrum
    scale = max(1., float(np.linalg.norm(L)))
    eigen = float(np.linalg.norm(L @ vectors-vectors*values)/scale)
    n = len(L)//2
    gauges = np.kron(np.eye(2), np.ones((n, 1))/np.sqrt(n))
    gauge = np.linalg.norm(L @ gauges, axis=0)/scale
    selected = [i for i, row in enumerate(information) if row["status"] == "available"]
    residual = 0.
    if selected:
        V = vectors[:, masks[1]]
        X = V @ ((V.T @ D[:, selected])/values[masks[1], None])
        residual = float(np.max(np.linalg.norm(L @ X-D[:, selected], axis=0)/np.maximum(1., np.linalg.norm(D[:, selected], axis=0))))
    checks = [dict(label="eigen_equation", value=eigen, limit=1e-10, verified=eigen <= 1e-10),
        dict(label="role_gauges", value=float(gauge.max()), limit=1e-10, verified=bool(np.all(gauge <= 1e-10))),
        dict(label="available_contrast_solve", value=residual, limit=1e-8, verified=residual <= 1e-8)]
    return checks


def _evaluate(L, D, rows, regional_covariance, functional_covariance, *, rate, spectrum):
    keys, columns, indices = {}, [], []
    for index, row in enumerate(rows):
        if row.get("absent", False):
            indices.append(None)
            continue
        key = D[:, index].tobytes()
        if key not in keys:
            keys[key] = len(columns)
            columns.append(index)
        indices.append(keys[key])
    unique = D[:, columns]
    information = contrast_information(L, unique, spectrum)
    for row, index in zip(rows, indices, strict=True):
        if index is None:
            row.update(status="not_in_target_population", reason="one or more declared case members are absent", null_projection=None,
                q=None, geometry_inverse=None, regional_sd=None, near_sd=None, lateral_sd=None, regional_rms_sd=None,
                status_at_tau_factors=None, null_at_tau_factors=None)
            continue
        info = information[index]
        q = info["contrast_information_inverse"]
        row.update(status=info["status"], reason=None if info["status"] == "available" else
            "contrast is outside the observed likelihood row space" if info["status"] == "not_estimable" else
            "cutoff ranks or contrast availability disagree" if info["status"] == "numerically_unresolved" else "centered functional is zero",
            null_projection=info["null_projection"], status_at_tau_factors=info["status_at_tau_factors"],
            null_at_tau_factors=info["null_at_tau_factors"], q=q,
            geometry_inverse=q/rate if q is not None and rate is not None else None,
            regional_sd=np.sqrt(q*np.diag(regional_covariance)).tolist() if q is not None else None,
            near_sd=float(np.sqrt(q*functional_covariance[0, 0])) if q is not None else None,
            lateral_sd=float(np.sqrt(q*functional_covariance[1, 1])) if q is not None else None,
            regional_rms_sd=float(np.sqrt(q*np.trace(regional_covariance)/12)) if q is not None else None)
    return rows, len(columns), _spectrum_checks(L, spectrum, unique, information)


def _svd_probes(L, D, rows, spectrum, accounting, player_ids):
    """remove only known role gauges, then independently use the same absolute cutoffs."""
    n = len(L)//2
    Q = block_diag(helmert(n, full=False).T, helmert(n, full=False).T)
    reduced = Q.T @ L @ Q
    U, singular, _ = np.linalg.svd(reduced, full_matrices=False)
    V_all = Q @ U
    maximum = _maximum_pair(player_ids, accounting)
    player_rows = [row for row in rows if row["record_type"] == "player_reference" and row["role"] == "offense"]
    highest = min(player_rows, key=lambda row: (-row["minutes"], row["player_id"]))["player_id"]
    lowest = min(player_rows, key=lambda row: (row["minutes"], row["player_id"]))["player_id"]
    probes = []
    for role in ("offense", "defense"):
        for label, members in (("highest_exposure", (highest,)), ("lowest_exposure", (lowest,)), ("maximum_overlap_pair", maximum)):
            if len(members) == 1:
                index = next(i for i, row in enumerate(rows) if row["record_type"] == "player_reference"
                    and row["role"] == role and row["player_id"] == members[0])
                d = D[:, index]
            else:
                first = next(i for i, row in enumerate(rows) if row["record_type"] == "player_reference"
                    and row["role"] == role and row["player_id"] == members[0])
                second = next(i for i, row in enumerate(rows) if row["record_type"] == "player_reference"
                    and row["role"] == role and row["player_id"] == members[1])
                d = D[:, first]-D[:, second]
            eig = contrast_information(L, d[:, None], spectrum)[0]
            norm = float(np.linalg.norm(d))
            nulls, statuses, qs = [], [], []
            for factor in RULES["cutoff_factors"]:
                positive = singular > factor*spectrum[2]
                V = V_all[:, positive]
                projected = V.T @ d
                null = float(np.linalg.norm(d-V @ projected)/norm) if norm else 0.
                status = "zero_functional" if norm == 0 else "not_estimable" if null > 1e-8 else "available"
                nulls.append(null)
                statuses.append(status)
                qs.append(float(np.sum(projected**2/singular[positive])) if status == "available" else None)
            eigen_qs = [float(np.sum((spectrum[1][:, mask].T @ d)**2/spectrum[0][mask]))
                if status == "available" else None
                for mask, status in zip(spectrum[3], eig["status_at_tau_factors"], strict=True)]
            eig_q = eig["contrast_information_inverse"]
            verified = (statuses == eig["status_at_tau_factors"]
                and np.allclose(nulls, eig["null_at_tau_factors"], atol=1e-8, rtol=0)
                and all(a is None and b is None or a is not None and b is not None
                    and np.isclose(a, b, atol=1e-10, rtol=1e-6)
                    for a, b in zip(qs, eigen_qs, strict=True)))
            probes.append(dict(assumption=rows[0]["assumption"], role=role, label=label, members=members,
                absolute_cutoffs=[factor*spectrum[2] for factor in RULES["cutoff_factors"]],
                status_at_tau_factors=statuses, null_at_tau_factors=nulls, q=qs[1], eigen_q=eig_q,
                q_at_tau_factors=qs, eigen_q_at_tau_factors=eigen_qs, verified=bool(verified)))
    return probes


def analyze(prepared, output):
    started, process_started = time.monotonic(), time.process_time()
    prepared_ref, document, designs, accountings = read_prepared(prepared)
    purpose = document["purpose"]
    root = output_path(str(output), [])
    if purpose == "research":
        require(root.is_relative_to(linked_path(prepared_ref).parent), "research analysis requires the prepared run directory")
    root.mkdir()
    p = designs["real"][0].p
    W, names = shape_regions()
    operators = shape_operators(W)
    C = np.diag(p)-np.outer(p, p)
    functionals = np.hstack(operators[1:])
    regional_covariance, functional_covariance = W.T @ C @ W, functionals.T @ C @ functionals
    require(ordered_array_digest(dict(p=p, W=W, near=operators[1], lateral=operators[2])) == document["operator_sha256"],
        "prepared operators differ")
    arrays = dict(p=p, W=W, C=C, region_covariance=regional_covariance,
        functionals=functionals, functional_covariance=functional_covariance)
    output_designs, contrasts, checks, probes, persistence = [], [], [], [], []
    distinct = 0
    for name, annual in designs.items():
        _, selections, history_L = physical_history_information(annual)
        final_rows = None
        for year, design in enumerate(annual):
            spectrum_started, spectrum_process = time.monotonic(), time.process_time()
            L = design.H/design.r**2
            spectrum = likelihood_spectrum(L)
            rows, c = _targets(name, annual, year, accountings[name][year], document["cases"][name], "annual")
            D = exposure_centering(design.u).T @ c
            rows, count, current_checks = _evaluate(L, D, rows, regional_covariance, functional_covariance,
                rate=design.r, spectrum=spectrum)
            distinct += count
            design_row = dict(next(row for row in document["inventory"] if row["design"] == name
                and row["assumption"] == "annual" and row["season"] == design.season))
            values, _, tau, masks = spectrum
            index = len(output_designs)
            arrays[f"spectrum_{index:02d}_eigenvalues"] = values
            arrays[f"spectrum_{index:02d}_cutoff_masks"] = np.asarray(masks, dtype=np.int8)
            design_row.update(rank=int(masks[1].sum()), nullity=len(L)-int(masks[1].sum()), dimension=len(L), tau=tau,
                rank_at_tau_factors=[int(mask.sum()) for mask in masks],
                resources=_cost(spectrum_started, spectrum_process, root))
            output_designs.append(design_row)
            for row in rows:
                row["reference_sha256"] = design_row["reference_sha256"]
                row["design_origin"] = "synthetic fixture" if purpose == "fixture_exercise" else name
                row["index"] = len(contrasts)
                contrasts.append(row)
            checks.extend(dict(design=name, assumption="annual", season=design.season, **check) for check in current_checks)
            if year == len(annual)-1:
                final_rows = rows
                if name == "real":
                    probes.extend(_svd_probes(L, D, rows, spectrum, accountings[name][year], design.player_ids))
            del spectrum, L
        spectrum_started, spectrum_process = time.monotonic(), time.process_time()
        spectrum = likelihood_spectrum(history_L)
        target = annual[-1]
        rows, c = _targets(name, annual, len(annual)-1, accountings[name][-1], document["cases"][name], "constant_history")
        D = selections[-1].T @ exposure_centering(target.u).T @ c
        rows, count, current_checks = _evaluate(history_L, D, rows, regional_covariance, functional_covariance,
            rate=None, spectrum=spectrum)
        distinct += count
        design_row = dict(next(row for row in document["inventory"] if row["design"] == name and row["assumption"] == "constant_history"))
        values, _, tau, masks = spectrum
        index = len(output_designs)
        arrays[f"spectrum_{index:02d}_eigenvalues"] = values
        arrays[f"spectrum_{index:02d}_cutoff_masks"] = np.asarray(masks, dtype=np.int8)
        design_row.update(rank=int(masks[1].sum()), nullity=len(history_L)-int(masks[1].sum()), dimension=len(history_L), tau=tau,
            rank_at_tau_factors=[int(mask.sum()) for mask in masks], resources=_cost(spectrum_started, spectrum_process, root))
        output_designs.append(design_row)
        for annual_row, row in zip(final_rows, rows, strict=True):
            if annual_row["status"] == "available":
                verified = row["status"] == "available" and row["q"]-annual_row["q"] <= 1e-10+1e-6*abs(annual_row["q"])
                persistence.append(dict(design=name, role=row["role"], label=row["label"], annual_q=annual_row["q"],
                    history_q=row["q"], verified=bool(verified)))
            row["reference_sha256"] = design_row["reference_sha256"]
            row["design_origin"] = "synthetic fixture" if purpose == "fixture_exercise" else name
            row["index"] = len(contrasts)
            contrasts.append(row)
        checks.extend(dict(design=name, assumption="constant_history", season=target.season, **check) for check in current_checks)
        if name == "real":
            probes.extend(_svd_probes(history_L, D, rows, spectrum, accountings[name][-1], target.player_ids))
        del spectrum, history_L, selections, D
    available = [row for row in contrasts if row["status"] == "available"]
    arrays["contrast_available_indices"] = np.asarray([row["index"] for row in available], dtype=np.int64)
    arrays["contrast_available_values"] = np.asarray([[row["q"], row["regional_rms_sd"], row["near_sd"], row["lateral_sd"],
        *row["regional_sd"]] for row in available], dtype=np.float64).reshape(-1, 16)
    arrays["contrast_diagnostic_indices"] = np.asarray([row["index"] for row in contrasts if row["null_projection"] is not None], dtype=np.int64)
    arrays["contrast_null_at_cutoffs"] = np.asarray([row["null_at_tau_factors"] for row in contrasts if row["null_projection"] is not None], dtype=np.float64)
    arrays["contrast_status_at_cutoffs"] = np.asarray([[dict(available=1, not_estimable=2, numerically_unresolved=3, zero_functional=4)[status]
        for status in row["status_at_tau_factors"]] for row in contrasts if row["null_projection"] is not None], dtype=np.int8)
    counts = dict(spectra=len(output_designs), annual_player_contrasts=sum(row["record_type"] == "player_reference"
        and row["assumption"] == "annual" for row in contrasts), historical_player_contrasts=sum(row["record_type"] == "player_reference"
        and row["assumption"] == "constant_history" for row in contrasts), case_labels=sum(row["record_type"] == "case" for row in contrasts),
        contrast_rows=len(contrasts), distinct_calculations=distinct,
        absent_case_labels=sum(row["status"] == "not_in_target_population" for row in contrasts), svd_probes=len(probes),
        svd_decompositions=2, new_responses=0, new_fits=0)
    require(counts == document["budget"], "completed analysis differs from prepared work inventory")
    verified = (all(row["verified"] for row in (*checks, *probes, *persistence))
        and not any(row["status"] == "numerically_unresolved" for row in contrasts))
    binding = write_arrays(root, "information.npz", arrays)
    fields = dict(prepared=prepared_ref, protocol=document["protocol"], seasons=document["seasons"],
        designs=output_designs, contrasts=contrasts, references=document["references"], region_names=list(names),
        selector_closure=document["selector_closure"], closure_status=document["closure_status"], information=binding,
        information_columns=["q", "regional_rms_sd", "near_sd", "lateral_sd", *[f"region_{index:02d}_sd" for index in range(12)]],
        cutoff_status_codes=dict(available=1, not_estimable=2, numerically_unresolved=3, zero_functional=4),
        numerical=dict(checks=checks, probes=probes, persistence=persistence, verified=verified),
        numerical_status="verified" if verified else "unresolved", execution_status="complete", exact_completeness=counts,
        units=RULES["units"], limits=LIMITS, sources=document["sources"], budget=document["budget"],
        nomination=None, admission="not_admitted", handoff=None)
    analysis = artifact("attribution_deployment_analysis", purpose,
        dict(prepared=prepared_ref, protocol=document["protocol"], information=binding["arrays"]), schema_version=1,
        **fields, resources=_cost(started, process_started, root,
            input_bytes=document["resources"]["input_bytes"]))
    path = root/"analysis.json"
    write_json(path, json_values(analysis))
    return identity(path)


def report(analysis, output):
    started, process_started = time.monotonic(), time.process_time()
    reference = _reference(analysis)
    document = read_artifact(linked_path(reference), "attribution_deployment_analysis", expected_schema=1)
    require(document["execution_status"] == "complete" and document["exact_completeness"] == document["budget"],
        "report requires complete saved analysis")
    load_arrays(document["information"])
    root = output_path(str(output), [])
    if document["purpose"] == "research":
        require(root.is_relative_to(linked_path(document["prepared"]).parent), "research report requires the prepared run directory")
    root.mkdir()
    from attribution_deployment_report import render_reports
    rendered = render_reports(root, document)
    numerical = document["numerical_status"]
    study_status = ("numerically_unresolved" if numerical != "verified" else
        "diagnosed" if document["purpose"] == "research" else "fixture_verified")
    require(document["purpose"] == "fixture_exercise" or rendered.get("next_benchmark") is not None
        or bool(rendered.get("unresolved_reason")), "research report requires a next-benchmark proposal or explicit unresolved diagnosis")
    result = artifact("attribution_deployment_result", document["purpose"],
        dict(analysis=reference, prepared=document["prepared"], protocol=document["protocol"],
            **{f"report_{index:02d}": ref for index, ref in enumerate(rendered["reports"])},
            **{f"figure_{index:02d}": ref for index, ref in enumerate(rendered["figures"])}), schema_version=1,
        analysis=reference, prepared=document["prepared"], protocol=document["protocol"],
        execution_status="complete", numerical_status=numerical, study_status=study_status,
        next_benchmark=rendered.get("next_benchmark") if document["purpose"] == "research" else None,
        unresolved_reason=rendered.get("unresolved_reason"), reports=rendered["reports"], figures=rendered["figures"],
        exact_completeness=document["exact_completeness"], units=RULES["units"], limits=LIMITS,
        nomination=None, admission="not_admitted", handoff=None, resources=_cost(started, process_started, root,
            input_bytes=Path(reference["path"]).stat().st_size+Path(document["information"]["arrays"]["path"]).stat().st_size))
    path = root/"result.json"
    write_json(path, json_values(result))
    return identity(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare", allow_abbrev=False)
    for name in ("real-result", "synthetic-result", "selection-result", "fixture-designs"):
        preparation.add_argument(f"--{name}")
    preparation.add_argument("--purpose", choices=("research", "fixture_exercise"), required=True)
    preparation.add_argument("--output", required=True)
    for name, input_name in (("analyze", "prepared"), ("report", "analysis")):
        command = commands.add_parser(name, allow_abbrev=False)
        command.add_argument(f"--{input_name}", required=True)
        command.add_argument("--output", required=True)
    arguments = vars(parser.parse_args(argv))
    command = arguments.pop("command")
    try:
        reference = dict(prepare=prepare, analyze=analyze, report=report)[command](**arguments)
    except (InputContractError, OSError, ValueError, KeyError, TypeError, np.linalg.LinAlgError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(reference, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
