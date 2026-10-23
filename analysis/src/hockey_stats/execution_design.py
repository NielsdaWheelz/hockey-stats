"""annual source selection and explicit execution circumstances, without fitting."""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from functools import cache
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.sparse import csr_matrix
from scipy.special import logsumexp

from .analysis_data import (PreparedManifest, read_prepared, read_prepared_game,
                            read_prepared_people)
from .artifacts import require as _require
from .captures import InputContractError
from .chance import TYPES
from .chance_features import (_columns, _transform_definition, candidate_columns,
                              CONTEXT_CATEGORIES, CONTEXT_REFERENCES)
from .coaches import read_coaches
from .feature_data import ACTION_KINDS
from .feature_history import _team_rest
from .shot_origins import cell_id, forward_kernel, grid, mirror_cell_representatives

HEADS = ("u", "q", "r", "g")
BLOCKS = ("shooter", "goalie", "setter", "attacking_coach", "defending_coach")
FAMILIES = ("game_additive", "recent_additive", "recent_interactions", "recent_geometry",
            "off_wing", "sequence", "shift_age", "shift_start", "workload",
            "calendar_rest", "strength_transition")
TARGETS = {
    "u": "ordinary physical attempt: unblocked versus block",
    "q": "unblocked attempt: on-net versus miss",
    "r": "on-net, known immediate stop: goal or continuing save versus recorded stopped save",
    "g": "on-net, known not stopped: goal versus continuing save; auxiliary setter mixture",
}
DEFINITION = {
    "version": "execution-v1-05-1", "heads": TARGETS, "families": list(FAMILIES),
    "types": TYPES, "grid": "native-656-mirror-y; full native penalty",
    "origin": {"distance_ft": 20, "direction_strength": 4, "blocks": "K(contact|origin) normalized over all origins"},
    "strength": "32 membership categories, (5,5,1) reference",
    "missingness": "head-training applicable weighted mean; unavailable and structural absence distinct; constant indicators zero",
    "actors": "tip-masked shooter; q/r/g goalie; g setter; separate known coach directions",
    "setter": ".2 none,.8 role-weighted supported pre-event and earlier-episode participants; incomplete unknown; current-skater linear mean",
    "history": "entry OR carry; last likelihood-supported raw state; separate block/head/role age curves; no role-change reset",
    "penalties": {"base_map": .25, "type_map": 1., "neighbor": 4., "circumstance": 4.,
                  "shooter": [4., 16.], "setter": [4., 16.], "goalie": [16., 64.],
                  "attacking_coach": [256., 1024.], "defending_coach": [256., 1024.], "age": 64.},
    "solver": {"maxiter": 2000, "ftol": 1e-10, "gtol": 1e-6, "em_maxiter": 100,
               "em_objective": 1e-8, "em_responsibility": 1e-6},
    "reference": "raw-minus-training-centers; preserve applicability offsets; virtual neutral execution",
    "population": {"game_type": 2, "physical_status": "ordinary", "skaters_each": [3, 4, 5, 6],
                   "opposing_goalies": 1, "attacking_goalies": [0, 1],
                   "required": ["focal_identity", "shooting_team", "membership", "shooter", "goalie", "six_type", "normalized_location", "outcome"],
                   "elapsed_clock": "optional; resolved membership suffices",
                   "u": {"block": 0, "miss": 1, "save": 1, "goal": 1},
                   "q": {"miss": 0, "save": 1, "goal": 1},
                   "r": {"recorded_stopped_save": 0, "continuing_save": 1, "goal": 1},
                   "g": {"continuing_save": 0, "goal": 1},
                   "stop": "v1-01 recorded_goalie_stop; unavailable withholds r/g only"},
    "family_columns": {family: _columns(family) for family in FAMILIES},
    "fixed_transforms": {family: _transform_definition(family) for family in FAMILIES},
    "adaptations": {"unit": "all actual opposing members; no known-only sums",
                    "shift_start": "on_the_fly reference; faceoff offensive/neutral/defensive; unknown unavailable",
                    "recent_geometry": "candidate origin; none absent; unavailable predecessor unavailable",
                    "team_rest": "feature_history._team_rest; verified complete prepared current-season inventory only",
                    "goalie_columns": ["prefix_toi_all_seconds/3600", "prefix_on_net_faced/30", "days_7.shots_against/30", "days_14.shots_against/30",
                                       "prior_appearance_exists", "calendar_gap_days", "prior_one_date", "prior_two_date", "games_days_7", "games_days_14"],
                    "goalie_prefix": "all supported earlier actions including penalty shots; never focal or later actions",
                    "source_support": "supported segment/event membership and candidate occurrences; coaches in dated assignments"},
    "missingness_definition": {"numeric": "head-training mean among available applicable transformed values, weighted by frozen origin mass",
                               "unavailable": "centered zero plus one shared condition indicator",
                               "structural_absence": "centered zero plus declared existence/category indicator",
                               "categories": "fixed ordered contrasts with separate unavailable indicator",
                               "unsupported_or_constant_indicator": "zero coefficient and explicit training support",
                               "unknown_coach": "no actor identity; unavailable circumstance; known-only center applicability"},
    "availability_conditions": {"preceding_status": ["recent_additive", "recent_interactions", "recent_geometry", "recent_exists"],
                                "preceding_status_rule": "one shared unavailable indicator; producer status recent requires complete applicable preceding facts; none remains structural absence",
                                "independent_fields": "separate supported selected counter/sequence fields retain their own availability; do not group empirical co-missingness"},
    "setter_definition": {"none_mass": .2, "setup_mass": .8, "forward_shooter_forward_weight": 2.,
                          "defense_shooter_forward_weight": 3., "other_weight": 1.,
                          "candidate_universe": "pre-event teammates and every supported earlier episode event's complete attacking unit plus named participants, excluding shooter; incomplete earlier membership or order -> unknown",
                          "known_assist": "likelihood-only local candidate position; never enlarge universe",
                          "unknown_or_goalie": "fixed pre-outcome skater candidate-weighted current linear mean; differentiate coupling",
                          "empty_mean": "prior-only zero", "setup": "I[candidate!=none]",
                          "objective": "sum origin weights times negative log branch mixture, not log origin mixture"},
    "age_definition": {"reference": "february-1 of season ending year", "days_per_year": 365.2425,
                       "center": 27., "scale": 10., "powers": [1, 2], "roles": ["F", "D", "G"],
                       "transition": "last-supported raw + (z(current_age)-z(last_age)) dot current annual block/head/role curve",
                       "unavailable_or_role_change": "age-neutral carry, no history reset", "coach": "age-neutral"},
    "history_definition": {"first": "source-first entry ridge only", "returning": "carry around declared mean only, no additional level ridge",
                           "ledger": "only likelihood-supported completed state updates; absent and prior-only years preserve last observation",
                           "zero_likelihood": "analytic current prior mean after age estimation",
                           "centers": "included pre-outcome opportunity weights; exclude tips for shooter, unknown coaches, none/unknown/goalie setters",
                           "setter_mean_coupling": "actual derivative support; reference weights alone not support"},
    "em_definition": {"max_updates": 100, "objective_relative_change": 1e-8, "max_responsibility_change": 1e-6,
                      "allowed_increase": 1e-10, "increase_scale": "1+abs(previous observed penalized objective)",
                      "inner_failure": "fails start", "starts": ["zero", "current actor prior means, other terms zero"],
                      "select": "minimum completed exact objective; zero start wins exact tie"},
}
DEFINITION["fixed_transforms"].update(
    shift_age="original shooter and complete actual opposing-unit min,mean,max compatible shift ages/60",
    shift_start="on_the_fly reference; faceoff offensive,neutral,defensive; unknown unavailable; last-faceoff existence,zone,age/60",
    workload="shooter prefix toi/3600,completed shifts/30,attempts/10; complete actual opposing-unit mean,max prefix toi/3600; shooter7,14-day toi/3600,shifts/30,attempts/10",
)
RECIPE = {"name": "experimental-v1", "version": "execution-v1-05-1",
          "sha256": hashlib.sha256(json.dumps(DEFINITION, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
          "definition": DEFINITION}


@dataclass(frozen=True)
class SetterCandidate:
    actor_id: str | None
    kind: str
    probability: float


@dataclass(frozen=True)
class ExecutionPredictor:
    key: str
    shot_type: int
    proxy_cell: int
    blocked: bool
    tip: bool
    actors: dict
    actor_facts: dict
    setter_prior: tuple[SetterCandidate, ...]
    context: dict


@dataclass
class ExecutionDesign:
    purpose: str
    season: str
    prepared: dict
    coaches: dict
    training_cutoff: str | None
    predictors: tuple[ExecutionPredictor, ...]
    heads: dict
    coverage: dict
    seasons: tuple[str, ...]
    recipe: dict
    resources: dict = field(default_factory=dict)


def _sha(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def _value(record, field):
    """supported selected fields survive unrelated missing counters."""
    if not isinstance(record, dict) or field in record.get("problems", {}):
        return None
    return record.get("values", {}).get(field)


def _role(person):
    role = _value(person.get("people", {}), "reported_position")
    return "F" if role in ("F", "C", "L", "R") else role if role in ("D", "G") else None


def _feature_context(attempt, game, shooter, goalie, strength, coaches, team_rest):
    """reuse fixed family columns/scales while retaining optional fact status."""
    facts = attempt["feature_facts"]
    local_people = game.get("people") or {}
    player = local_people.get(str(shooter), {})
    goalie_person = local_people.get(str(goalie), {})
    values, conditions = {}, {}

    def put(name, value, condition=None, *, kind="numeric", absent=False):
        condition = condition or name
        status = "absent" if absent else "unavailable" if value is None else "available"
        values[name] = {"value": value, "status": status, "condition": condition, "kind": kind}
        conditions.setdefault(condition, []).append(name)

    def numeric(name, record, field, scale=1, condition=None, absent=False):
        value = _value(record, field)
        put(name, value / scale if value is not None else None, condition, absent=absent)

    def categorical(prefix, value, levels, reference=None, condition=None, absent=False):
        for level in levels:
            if level != reference:
                put(prefix + ":" + str(level), None if value is None and not absent else float(value == level),
                    condition or prefix, kind="indicator", absent=absent)

    state = facts["state"]
    margin = _value(state, "score_margin")
    bucket = None if margin is None else ("trailing_2_plus" if margin <= -2 else "trailing_1" if margin == -1
                                           else "tied" if margin == 0 else "leading_1" if margin == 1 else "leading_2_plus")
    period = _value(state, "period_number")
    period = str(period) if period in (1, 2, 3) else "OT" if period is not None and period > 3 else None
    remaining = _value(state, "remaining_seconds")
    elapsed = _value(state, "elapsed_seconds")
    minute = None if elapsed is None or remaining is None else "first" if elapsed < 60 else "last" if remaining <= 60 else "middle"
    game_categories = dict(score_bucket=bucket, period=period,
                           home_away=_value(state, "home_away"), minute_band=minute)
    for field, value in game_categories.items():
        categorical(field, value, CONTEXT_CATEGORIES[field], CONTEXT_REFERENCES[field])

    preceding = facts["preceding"]
    preceding_status = _value(preceding, "status")
    recent = preceding_status == "recent"
    absent = preceding_status == "none"
    prior_kind = _value(preceding, "kind") if recent else None
    gap = _value(preceding, "time_gap_seconds") if recent else None
    prior_x = _value(preceding, "current_attack_x") if recent else None
    prior_y = _value(preceding, "current_attack_y") if recent else None
    recent_categories = {
        "recent_kind": prior_kind,
        "recent_team": _value(preceding, "owner_team_relation") if recent else None,
        "recent_delay": gap,
        "recent_zone": ("attacking" if prior_x > 25 else "other") if prior_x is not None else None,
        "recent_shooter": ("same" if _value(preceding, "same_shooter") else "different")
        if recent and _value(preceding, "same_shooter") is not None else None,
    }
    for field, value in recent_categories.items():
        not_applicable = absent or field == "recent_shooter" and recent and prior_kind not in ACTION_KINDS[4:]
        categorical(field, value, CONTEXT_CATEGORIES[field], condition="preceding_status", absent=not_applicable)
    put("recent_exists", None if preceding_status not in ("none", "recent") else float(recent), "preceding_status", kind="indicator")
    for name in _columns("recent_interactions"):
        parts = name.split(":")
        left = recent_categories["recent_kind"]
        right = recent_categories[parts[2]]
        value = None if not absent and (left is None or right is None) else float(left == parts[1] and str(right) == parts[3])
        put(name, value, "preceding_status", kind="indicator", absent=absent)
    for name in _columns("recent_geometry"):
        put(name, 0. if recent and prior_x is not None and prior_y is not None else None,
            "preceding_status", absent=absent)
    hand = _value(player.get("people", {}), "shoots_catches")
    put("off_wing", 0. if hand in ("L", "R") else None, "off_wing", kind="indicator")

    sequence = facts["sequence"]
    index = _value(sequence, "defender_sequence_index")
    for label, truth in (("2", index == 2), ("3", index == 3), ("4+", index is not None and index >= 4)):
        put("defender_sequence_index:" + label, float(truth) if index is not None else None, "defender_sequence_index", kind="indicator")
    numeric("defender_sequence_age_seconds/60", sequence, "defender_sequence_age_seconds", 60)
    deployment = facts["deployment"]
    deployed = _value(deployment, "players") or {}
    shooter_deployment = deployed.get(str(shooter), {})
    numeric("shooter_age_seconds/60", shooter_deployment, "age_seconds", 60)
    opposing = _value(deployment, "opposing_unit") or {}
    for stat in ("min", "mean", "max"):
        numeric(f"opposing_age_{stat}_seconds/60", opposing, f"age_{stat}_seconds", 60, "opposing_shift_age")
    start = _value(shooter_deployment, "start_type")
    zone = _value(shooter_deployment, "start_zone") if start == "faceoff" else "on_the_fly" if start == "on_the_fly" else None
    categorical("shooter_start_zone", zone, ("offensive", "neutral", "defensive"), condition="shooter_shift_start")
    exists = _value(deployment, "last_faceoff_exists")
    put("last_faceoff:none", None if exists is None else float(not exists), "last_faceoff_exists", kind="indicator")
    zone = _value(deployment, "last_faceoff_zone") if exists else None
    for zone_name in ("offensive", "defensive"):
        put("last_faceoff_zone:" + zone_name, None if exists is None or exists and zone is None else float(zone == zone_name),
            "last_faceoff_zone", kind="indicator", absent=exists is False)
    numeric("last_faceoff_age_seconds/60", deployment, "last_faceoff_age_seconds", 60, absent=exists is False)

    workload = facts["current_workload"]
    prefixes = _value(workload, "players") or {}
    prefix = prefixes.get(str(shooter), {})
    for field, scale in (("toi_all_seconds", 3600), ("shifts_completed", 30), ("attempts", 10)):
        numeric(f"shooter_prefix_{field}/{scale}", prefix, field, scale)
    opposing_workload = _value(workload, "opposing_unit") or {}
    for stat in ("mean", "max"):
        numeric(f"opposing_prefix_toi_all_{stat}_seconds/3600", opposing_workload,
                f"toi_all_{stat}_seconds", 3600, "opposing_prefix_toi")
    for scope in ("days_7", "days_14"):
        window = player.get("workload", {}).get(scope, {})
        for field, scale in (("toi_all_seconds", 3600), ("shifts", 30), ("attempts", 10)):
            numeric(f"shooter_{scope}_{field}/{scale}", window, field, scale)
    for who, record, exists_field in (("shooter", player.get("calendar_rest", {}), "prior_appearance_exists"),
                                      ("opposing_team", team_rest, "prior_game_exists")):
        exists = _value(record, exists_field)
        put(f"{who}:prior_exists", None if exists is None else float(exists), kind="indicator")
        numeric(f"{who}:calendar_gap_days", record, "calendar_gap_days", absent=exists is False)
        for field in ("prior_one_date", "prior_two_date", "games_days_7", "games_days_14"):
            numeric(f"{who}:{field}", record, field)
    transition = _value(deployment, "strength_transition_exists")
    previous_side = _value(deployment, "previous_strength_side")
    for name, side in (("same_fewer", "same"), ("same_more", "opponent")):
        put("previous_strength:" + name, None if transition is None or transition and previous_side is None else float(previous_side == side),
            "strength_transition", kind="indicator", absent=transition is False)
    numeric("return_to_5v5_age_seconds/60", deployment, "strength_transition_age_seconds", 60,
            "strength_transition_age", absent=transition is False)

    goalie_prefix = prefixes.get(str(goalie), {})
    for field, scale in (("toi_all_seconds", 3600), ("on_net_faced", 30)):
        numeric(f"goalie_prefix_{field}/{scale}", goalie_prefix, field, scale)
    for scope in ("days_7", "days_14"):
        numeric(f"goalie_{scope}_shots_against/30", goalie_person.get("workload", {}).get(scope, {}), "shots_against", 30)
    rest = goalie_person.get("calendar_rest", {})
    exists = _value(rest, "prior_appearance_exists")
    put("goalie:prior_appearance_exists", None if exists is None else float(exists), kind="indicator")
    numeric("goalie:calendar_gap_days", rest, "calendar_gap_days", absent=exists is False)
    for field in ("prior_one_date", "prior_two_date", "games_days_7", "games_days_14"):
        numeric("goalie:" + field, rest, field)
    for group in ("attacking_coach", "defending_coach"):
        put(group + ":unavailable", float(coaches[group] is None), kind="indicator")
    for a in range(3, 7):
        for d in range(3, 7):
            for g in (0, 1):
                if (a, d, g) != (5, 5, 1):
                    put(f"strength:{a},{d},{g}", float(strength == (a, d, g)), kind="indicator")
    # every unavailable condition has one indicator, shared by its derived columns.
    for condition, names in list(conditions.items()):
        missing = any(values[name]["status"] == "unavailable" for name in names)
        put("unavailable:" + condition, float(missing), "flag:" + condition, kind="indicator")
    return {"features": values, "candidate": {"previous_x": prior_x, "previous_y": prior_y,
                                               "hand": 1 if hand == "R" else -1 if hand == "L" else None},
            "strength": list(strength), "setter_universe_complete": True}


@cache
def origin_law():
    centers, edges = grid()
    log_kernel = forward_kernel(centers, 20., 4.)
    return centers, edges, np.exp(log_kernel - logsumexp(log_kernel, axis=1, keepdims=True))


def origins_for(predictor):
    if predictor.blocked:
        return np.arange(len(origin_law()[0]), dtype=np.int64), origin_law()[2][predictor.proxy_cell]
    return np.asarray([predictor.proxy_cell], dtype=np.int64), np.ones(1, dtype=np.float64)


def _origin_features(predictor, cells):
    result = {key: dict(value) for key, value in predictor.context["features"].items()}
    xy = origin_law()[0][cells].T
    candidate = predictor.context["candidate"]
    for family in ("recent_geometry", "off_wing"):
        names = _columns(family)
        if result[names[0]]["status"] != "available":
            continue
        tiny_design = {"families": [family], "family_slices": {family: [0, len(names)]}}
        for index, values in candidate_columns(candidate, tiny_design, xy):
            result[names[index]]["value"] = values
    return result


def predictor_matrix(layout, predictors, origin_cells):
    """full global-coordinate sparse base logits; setup/setter stay separate."""
    _require(len(predictors) == len(origin_cells), "predictors and explicit origins differ")
    n = len(predictors)
    if not n:
        return csr_matrix((0, layout["size"]), dtype=np.float64)
    cells = np.asarray(origin_cells)
    _require(cells.dtype.kind in ("i", "u") and cells.ndim == 1 and np.all((cells >= 0) & (cells < len(origin_law()[0]))),
             "origin cells must be explicit native integer indices")
    rows, columns, values = [], [], []
    actor_indices = layout["actor_indices"]
    maps = np.asarray(layout["map_indices"], dtype=np.int64)
    start = 0
    while start < n:
        predictor = predictors[start]
        end = start + 1
        while end < n and predictors[end] is predictor:
            end += 1
        run_rows = np.arange(start, end, dtype=np.int64)
        run_cells = cells[start:end]
        one = np.ones(end - start, dtype=np.float64)

        def append(coordinate, value):
            array = np.broadcast_to(value, (end - start,))
            selected = array != 0
            if np.any(selected):
                rows.append(run_rows[selected])
                columns.append(np.broadcast_to(coordinate, (end - start,))[selected])
                values.append(array[selected])

        append(0, one)
        append(maps[0, run_cells], one)
        if predictor.shot_type:
            append(maps[predictor.shot_type, run_cells], one)
        features = _origin_features(predictor, run_cells)
        for name, coordinate, mean, active in zip(layout["columns"], layout["circumstance_indices"], layout["means"], layout["active"], strict=True):
            _require(name in features, "predictor misses fixed circumstance " + name)
            if not active:
                continue
            record = features[name]
            value = record["value"]
            if record["status"] != "available":
                value = 0.
            else:
                value = np.asarray(value) - mean
            append(coordinate, value)
        for block, axis in actor_indices.items():
            if block == "setter" or block == "shooter" and predictor.tip:
                continue
            actor = predictor.actors.get(block)
            if actor is None:
                _require(block.endswith("coach"), "missing required execution actor " + block)
                continue
            _require(actor in axis, "unknown execution actor " + block + ":" + actor)
            append(axis[actor], one)
        start = end
    matrix = csr_matrix((np.concatenate(values) if values else [],
                         (np.concatenate(rows) if rows else [], np.concatenate(columns) if columns else [])),
                        shape=(n, layout["size"]), dtype=np.float64)
    _require(np.isfinite(matrix.data).all(), "nonfinite execution predictors")
    return matrix


def _setter_prior(game, attempt, event, state, people):
    """pre-event membership and supported earlier episode participants only."""
    source_index = attempt["source_index"]
    shooter = _value(attempt["details"], "physical_shooter_id")
    side = _value(state, "home_away")
    team = _value(state, "shooting_team_id")
    members = _value(state, side + "_skaters") if side in ("home", "away") else None
    goalies = _value(state, side + "_goalies") if side in ("home", "away") else None
    complete = members is not None and goalies is not None
    candidates = set((members or []) + (goalies or [])) - {shooter}
    goalie_candidates = set(goalies or [])
    episode = _value(event["chronology"], "episode_index")
    order = _value(event["chronology"], "order_index")
    if episode is None or order is None:
        complete = False
    else:
        episode_record = next((row for row in game.get("episodes") or [] if row["episode_index"] == episode), None)
        if episode_record is None or episode_record["left_censored"]:
            complete = False
        earlier = [e for e in game["events"] or []
                   if _value(e["chronology"], "episode_index") == episode
                   and _value(e["chronology"], "order_index") is not None
                   and _value(e["chronology"], "order_index") < order]
        associations = {row["source_index"]: row["native"] for row in game.get("associations") or []}
        for prior in earlier:
            if not prior["source"]["kind_valid"]:
                complete = False
            membership = associations.get(prior["source"]["source_index"])
            prior_skaters = membership.get(side + "_skaters") if membership is not None else None
            prior_goalies = membership.get(side + "_goalies") if membership is not None else None
            if prior_skaters is None or prior_goalies is None:
                complete = False
            else:
                candidates.update(prior_skaters)
                candidates.update(prior_goalies)
                goalie_candidates.update(prior_goalies)
            roles = prior["source"].get("roles")
            if roles is None:
                complete = False
            for role_name, actor in (roles or {}).items():
                if actor is None or actor == shooter:
                    continue
                person = people.get(str(actor))
                if person is None or _value(person.get("people", {}), "team_id") is None:
                    complete = False
                elif _value(person["people"], "team_id") == team:
                    candidates.add(actor)
                    if role_name == "goalie":
                        goalie_candidates.add(actor)
    candidates.discard(shooter)
    for actor in candidates:
        person = people.get(str(actor), {})
        if _value(person.get("people", {}), "team_id") != team:
            complete = False
    if not complete:
        return (SetterCandidate(None, "none", .2), SetterCandidate(None, "unknown", .8)), False
    # an empty supported universe has no justified recipient; retain unknown setup.
    if not candidates:
        return (SetterCandidate(None, "none", .2), SetterCandidate(None, "unknown", .8)), True
    shooter_role = _role(people.get(str(shooter), {}))
    weights = {actor: (2. if shooter_role == "F" else 3. if shooter_role == "D" else 1.)
               if _role(people[str(actor)]) == "F" else 1. for actor in sorted(candidates)}
    total = sum(weights.values())
    result = [SetterCandidate(None, "none", .2)]
    for actor, weight in weights.items():
        result.append(SetterCandidate(str(actor), "goalie" if actor in goalie_candidates or _role(people[str(actor)]) == "G" else "skater", .8 * weight / total))
    return tuple(result), True


def _head_design(head, predictors, labels, people, source_actors=None):
    rows = np.asarray([i for i, label in enumerate(labels) if label[head] is not None], dtype=np.int64)
    targets = np.asarray([labels[i][head] for i in rows], dtype=np.float64)
    template = predictors[0].context["features"] if predictors else {}
    names = [name for name in template if head != "u" or not name.startswith(("goalie_", "goalie:", "unavailable:goalie"))]
    sums = np.zeros(len(names)); mass = np.zeros(len(names)); lows = np.full(len(names), np.inf); highs = np.full(len(names), -np.inf)
    missing = Counter(); structural = Counter()
    for i in rows:
        predictor = predictors[i]
        cells, weights = origins_for(predictor) if head == "u" else (np.asarray([predictor.proxy_cell]), np.ones(1))
        features = _origin_features(predictor, cells)
        for j, name in enumerate(names):
            record = features[name]
            if record["status"] != "available":
                (structural if record["status"] == "absent" else missing)[name] += 1
                continue
            values = np.broadcast_to(record["value"], weights.shape)
            sums[j] += float(weights @ values)
            mass[j] += float(weights.sum())
            lows[j] = min(lows[j], float(values.min())); highs[j] = max(highs[j], float(values.max()))
    means = np.divide(sums, mass, out=np.zeros_like(sums), where=mass > 0)
    # indicators retain fixed references; only optional numeric values are centered.
    for j, name in enumerate(names):
        if template[name]["kind"] == "indicator":
            means[j] = 0.
    active = (mass > 0) & (highs > lows)
    # numeric variation around missing/structural reference can carry information.
    for j, name in enumerate(names):
        if template[name]["kind"] == "numeric":
            active[j] = mass[j] > 0 and highs[j] > lows[j]
    centers, edges, _ = origin_law()
    representatives = mirror_cell_representatives(centers)
    unique = {representative: i for i, representative in enumerate(sorted(set(representatives)))}
    mirror = [unique[representative] for representative in representatives]
    coefficients = ["intercept"]
    maps = []
    for map_name in ["base"] + ["type:" + value for value in TYPES[1:]]:
        offset = len(coefficients)
        maps.append([offset + orbit for orbit in mirror])
        coefficients.extend(map_name + ":orbit:" + str(i) for i in range(len(unique)))
    circumstance_indices = list(range(len(coefficients), len(coefficients) + len(names)))
    coefficients.extend("circumstance:" + name for name in names)
    actor_rows = {}
    blocks = ["shooter"] + (["goalie"] if head != "u" else []) + (["setter"] if head == "g" else []) + ["attacking_coach", "defending_coach"]
    for block in blocks:
        for actor, count in (source_actors or {}).get(block, {}).items():
            actor_rows[block, actor] = {"block": block, "id": actor, "source_support": count,
                                        "likelihood_support": 0., "center_weight": 0., "role": None, "age": None}
    for block in blocks:
        for predictor in predictors:
            candidates = [(candidate.actor_id, candidate.probability) for candidate in predictor.setter_prior if candidate.kind == "skater"] if block == "setter" else [(predictor.actors.get(block), 1.)]
            for actor, _ in candidates:
                if actor is not None:
                    actor_rows.setdefault((block, actor), {"block": block, "id": actor, "source_support": 0,
                                                          "likelihood_support": 0., "center_weight": 0.,
                                                          "role": None, "age": None})["source_support"] += 1
    setter_weight = Counter()
    for local_i, source_i in enumerate(rows):
        predictor = predictors[source_i]
        for block in blocks:
            if block == "setter":
                for candidate_index, candidate in enumerate(predictor.setter_prior):
                    if candidate.kind == "skater":
                        setter_weight[candidate.actor_id] += candidate.probability
                        actor_rows[block, candidate.actor_id]["center_weight"] += candidate.probability
                        if labels[source_i]["observed_setter"] < 0 or labels[source_i]["observed_setter"] == candidate_index:
                            actor_rows[block, candidate.actor_id]["likelihood_support"] += 1.
            else:
                actor = predictor.actors.get(block)
                if actor is not None and not (block == "shooter" and predictor.tip):
                    actor_rows[block, actor]["likelihood_support"] += 1.
                    actor_rows[block, actor]["center_weight"] += 1.
    # mean coupling in any marginalized unknown/goalie branch gives likelihood support.
    coupled = head == "g" and any(
        any(c.kind in ("unknown", "goalie") and (labels[i]["observed_setter"] < 0 or labels[i]["observed_setter"] == j)
            for j, c in enumerate(predictors[i].setter_prior)) for i in rows)
    actor_indices = {block: {} for block in blocks}
    actors = []
    for (block, actor), record in sorted(actor_rows.items(), key=lambda item: (BLOCKS.index(item[0][0]), item[0][1])):
        if block == "setter" and coupled and setter_weight[actor] > 0:
            record["likelihood_support"] += 1.
        person = people.get(actor)
        if person is not None:
            record["role"] = _value(person, "position_group")
            age = _value(person, "age_days")
            record["age"] = age / 365.2425 if age is not None else None
        record["index"] = len(coefficients)
        record["prior_only"] = record["likelihood_support"] == 0
        record.update(mean=0., precision=DEFINITION["penalties"][block][0], age_delta=[], age_indices=[])
        actor_indices[block][actor] = len(coefficients)
        coefficients.append(block + ":" + actor)
        actors.append(record)
    setup_index = None
    if head == "g":
        setup_index = len(coefficients); coefficients.append("setup")
    penalized_circumstances = circumstance_indices + ([] if setup_index is None else [setup_index])
    age_indices_by_block_role = {}
    for block in blocks:
        if block.endswith("coach"):
            continue
        age_indices_by_block_role[block] = {}
        for role in ("F", "D", "G"):
            indices = [len(coefficients), len(coefficients) + 1]
            coefficients.extend([f"age:{block}:{role}:linear", f"age:{block}:{role}:quadratic"])
            age_indices_by_block_role[block][role] = indices
    total_setter_weight = sum(setter_weight.values())
    mean_ids = sorted(actor for actor in setter_weight if setter_weight[actor] > 0)
    availability_conditions = {}
    for name in names:
        condition = template[name]["condition"]
        if not condition.startswith("flag:"):
            availability_conditions.setdefault(condition, []).append(name)
    layout = dict(size=len(coefficients), coefficient_names=coefficients, columns=names,
                  means=means.tolist(), active=active.tolist(),
                  conditions={name: template[name]["condition"] for name in names},
                  availability_conditions=availability_conditions,
                  feature_support={name: {"available_weight": float(mass[j]), "unavailable_attempts": missing[name],
                                          "structural_absence_attempts": structural[name], "active": bool(active[j])}
                                   for j, name in enumerate(names)},
                  map_indices=maps, native_neighbors=edges.tolist(), mirror_cells=mirror,
                  circumstance_indices=circumstance_indices, actor_indices=actor_indices,
                  age_indices_by_block_role=age_indices_by_block_role, setup_index=setup_index,
                  families=list(FAMILIES) + ([] if head == "u" else ["goalie_workload", "goalie_calendar_rest"]),
                  trait_assumptions=["reported_hand_stable_trait"],
                  fixed_transforms=DEFINITION["fixed_transforms"],
                  penalties=DEFINITION["penalties"],
                  setter_mean_indices=[actor_indices.get("setter", {})[actor] for actor in mean_ids],
                  setter_mean_weights=[setter_weight[actor] / total_setter_weight for actor in mean_ids])
    result = dict(head=head, size=layout["size"], target=targets, rows=rows, keys=[predictors[i].key for i in rows],
                        weight=np.ones(len(rows)), design=layout, actors=actors,
                        map_indices=np.asarray(maps, dtype=np.int64), native_neighbors=edges,
                        circumstance_indices=np.asarray(penalized_circumstances, dtype=np.int64),
                        age_indices=np.asarray([i for roles in age_indices_by_block_role.values() for pair in roles.values() for i in pair], dtype=np.int64),
                        age_indices_by_block_role=age_indices_by_block_role, setup_index=setup_index,
                        setter_mean_indices=np.asarray(layout["setter_mean_indices"], dtype=np.int64),
                        setter_mean_weights=np.asarray(layout["setter_mean_weights"], dtype=np.float64))

    # retain one compact physical-row matrix, never its blocked origin expansion.
    # optimizer iterations expand bounded sparse rows and just five geometry
    # columns; they do not repeatedly interpret source facts.
    selected_predictors = [predictors[i] for i in rows]
    fixed = predictor_matrix(layout, selected_predictors, [p.proxy_cell for p in selected_predictors]).tocoo()
    dynamic_names = _columns("recent_geometry") + _columns("off_wing")
    name_indices = {name: i for i, name in enumerate(names)}
    dynamic_coordinates = [circumstance_indices[name_indices[name]] for name in dynamic_names if name in name_indices]
    removed = np.asarray(sorted(set(np.asarray(maps).ravel()) | set(dynamic_coordinates)), dtype=np.int64)
    keep = ~np.isin(fixed.col, removed)
    fixed = csr_matrix((fixed.data[keep], (fixed.row[keep], fixed.col[keep])), shape=fixed.shape)
    candidate_inputs = {
        field: np.asarray([p.context["candidate"][field] if p.context["candidate"][field] is not None else np.nan
                           for p in selected_predictors], dtype=np.float64)
        for field in ("previous_x", "previous_y", "hand")
    }
    candidate_available = {
        family: np.asarray([p.context["features"][_columns(family)[0]]["status"] == "available"
                            for p in selected_predictors], dtype=bool)
        for family in ("recent_geometry", "off_wing")
    }
    selected_types = np.asarray([p.shot_type for p in selected_predictors], dtype=np.int64)
    map_array = np.asarray(maps, dtype=np.int64)

    def expanded_matrix(local_rows, cells):
        count = len(local_rows)
        expanded_rows = np.arange(count, dtype=np.int64)
        matrix = fixed[local_rows]
        map_rows = [expanded_rows]; map_columns = [map_array[0, cells]]
        map_values = [np.ones(count)]
        typed = selected_types[local_rows] != 0
        map_rows.append(expanded_rows[typed]); map_columns.append(map_array[selected_types[local_rows][typed], cells[typed]])
        map_values.append(np.ones(np.count_nonzero(typed)))
        xy = origin_law()[0][cells].T
        inputs = {field: values[local_rows] for field, values in candidate_inputs.items()}
        for family in ("recent_geometry", "off_wing"):
            family_names = _columns(family)
            tiny_design = {"families": [family], "family_slices": {family: [0, len(family_names)]}}
            available = candidate_available[family][local_rows]
            for index, values in candidate_columns(inputs, tiny_design, xy):
                name = family_names[index]
                column = name_indices[name]
                if not active[column]:
                    continue
                values = np.where(available, values - means[column], 0.)
                nonzero = values != 0
                map_rows.append(expanded_rows[nonzero]); map_columns.append(np.full(np.count_nonzero(nonzero), circumstance_indices[column], dtype=np.int64))
                map_values.append(values[nonzero])
        return matrix + csr_matrix((np.concatenate(map_values), (np.concatenate(map_rows), np.concatenate(map_columns))), shape=matrix.shape)

    def batches():
        expanded_predictors, cell_batch, row_batch, weight_batch, observed = [], [], [], [], []
        def emit():
            batch = {"matrix": expanded_matrix(np.asarray(row_batch, dtype=np.int64), np.asarray(cell_batch, dtype=np.int64)),
                     "row": np.asarray(row_batch, dtype=np.int64), "weight": np.asarray(weight_batch, dtype=np.float64)}
            if head == "g":
                offsets, indices, prior = [0], [], []
                for predictor in expanded_predictors:
                    for candidate in predictor.setter_prior:
                        indices.append(-1 if candidate.kind == "none" else -2 if candidate.kind in ("unknown", "goalie")
                                       else actor_indices["setter"][candidate.actor_id])
                        prior.append(candidate.probability)
                    offsets.append(len(indices))
                batch.update(offsets=np.asarray(offsets, dtype=np.int64), setter_index=np.asarray(indices, dtype=np.int64),
                             prior=np.asarray(prior, dtype=np.float64), observed=np.asarray(observed, dtype=np.int64))
            return batch
        for local_i, source_i in enumerate(rows):
            predictor = predictors[source_i]
            cells, weights = origins_for(predictor) if head == "u" else (np.asarray([predictor.proxy_cell]), np.ones(1))
            if cell_batch and len(cell_batch) + len(cells) > 4096:
                yield emit()
                expanded_predictors.clear(); cell_batch.clear(); row_batch.clear(); weight_batch.clear(); observed.clear()
            expanded_predictors.extend([predictor] * len(cells)); cell_batch.extend(cells.tolist())
            row_batch.extend([local_i] * len(cells)); weight_batch.extend(weights.tolist())
            observed.extend([labels[source_i]["observed_setter"]] * len(cells))
        if cell_batch:
            yield emit()
    result["batches"] = batches
    return result


def prepare_execution(base_prepared, coaches, recipe, season):
    """bind exact selected evidence, keeping every recognized attempt disposition."""
    started = perf_counter()
    _require(recipe == RECIPE, "execution recipe differs")
    _require(isinstance(base_prepared, PreparedManifest), "execution needs a checked prepared manifest")
    purpose = base_prepared["purpose"]
    # re-read detached identities to bind supplied objects to their member bytes.
    prepared = read_prepared(base_prepared.directory, purpose)
    _require(dict(prepared) == dict(base_prepared), "supplied prepared identity differs")
    prepared_identity = {"path": str(prepared.directory / "manifest.json"),
                         "sha256": _sha(prepared.directory / "manifest.json")}
    _require(isinstance(coaches, (str, Path)), "coaches must be its explicit artifact path")
    coach_path = Path(coaches).resolve()
    coach_data = read_coaches(coach_path, purpose)
    seasons = tuple(row["season"] for row in prepared["seasons"])
    _require(season in seasons, "execution season not selected")
    _require(all(int(b[:4]) == int(a[:4]) + 1 for a, b in zip(seasons, seasons[1:])), "fixture execution seasons must be consecutive")
    selected = next(row for row in prepared["seasons"] if row["season"] == season)
    prepared_corpora = {(row["path"], row["sha256"]) for row in prepared["inputs"] if row["kind"] == "corpus"}
    coach_corpora = [row for row in coach_data["corpora"] if row["season"] == season]
    _require(len(coach_corpora) == 1 and (coach_corpora[0]["corpus_manifest"], coach_corpora[0]["sha256"]) in prepared_corpora,
             "prepared/coach current-season source corpus differs")
    people = {str(_value(person, "player_id")): person for person in read_prepared_people(prepared, season)["people"]}
    coaches_by_game = {row["game_id"]: row for row in coach_data["games"] if row["season"] == season}
    _require(set(selected["selected_game_ids"]) <= set(coaches_by_game), "coach binder misses selected prepared games")
    predictors, labels, coverage_rows, game_rows, dates = [], [], [], [], []
    # team history was computed but not serialized by v1-01. reuse its arithmetic
    # only over a verified complete prepared inventory; sparse fixture dates do
    # not prove that a team had no earlier game.
    complete_schedule = len(selected["selected_game_ids"]) == selected["inventory_games"]
    schedule = []
    if complete_schedule:
        for game_id in selected["selected_game_ids"]:
            # tentative compact schedule; the ordinary single pass below verifies
            # every field against prepared facts before returning any design.
            entry = coaches_by_game[game_id]
            schedule.append({field: entry[field] for field in ("game_id", "season", "game_date", "home_team_id", "away_team_id")}
                            | {"input_ref": prepared_identity})
    team_schedules = {}
    for entry in schedule:
        for which in ("home", "away"):
            team_schedules.setdefault(entry[which + "_team_id"], []).append(entry)
    for team_id, entries in team_schedules.items():
        entries.sort(key=lambda row: (row["game_date"], row["game_id"]))
        team_schedules[team_id] = {"rows": entries, "dates": [row["game_date"] for row in entries],
                                   "inventory_evidence": {"input_ref": entries[0]["input_ref"], "source": "prepared-analysis", "path": "/files"}}
    totals = {head: Counter() for head in HEADS}
    source_actors = {block: Counter() for block in BLOCKS}
    for game_id in selected["selected_game_ids"]:
        game = read_prepared_game(prepared, season, game_id)
        inventory = game["game"]["inventory"]
        coach_game = coaches_by_game[game_id]
        _require(all(coach_game[field] == inventory[field] for field in ("season", "game_id", "game_date", "home_team_id", "away_team_id")),
                 "prepared/coach game identity differs: " + game_id)
        _require(not complete_schedule or game["game"]["identity"] is not None,
                 "full team schedule requires supported prepared game identities")
        dates.append(inventory["game_date"])
        for segment in game.get("segments") or []:
            membership = segment["membership"]
            for source_side in ("home", "away"):
                for actor in membership[source_side + "_skaters"] or []:
                    source_actors["shooter"][str(actor)] += 1
                    source_actors["setter"][str(actor)] += 1
                for actor in membership[source_side + "_goalies"] or []:
                    source_actors["goalie"][str(actor)] += 1
                    source_actors["shooter"][str(actor)] += 1
        for coach_side in ("home", "away"):
            coach_id = coach_game[coach_side]["coach_id"]
            if coach_id is not None:
                for block in ("attacking_coach", "defending_coach"):
                    source_actors[block][coach_id] += 1
        events = {event["source"]["source_index"]: event for event in game["events"] or []}
        credits = {credit["source_index"]: credit for credit in game["credits"] or []}
        start_count = len(coverage_rows)
        for attempt in game["attempts"] or []:
            source_index = attempt["source_index"]
            key = game_id + ":" + str(source_index)
            event = events.get(source_index)
            facts = attempt["feature_facts"]
            state = facts["state"]
            for source_side in ("home", "away"):
                for actor in _value(state, source_side + "_skaters") or []:
                    source_actors["shooter"][str(actor)] += 1
                    source_actors["setter"][str(actor)] += 1
                for actor in _value(state, source_side + "_goalies") or []:
                    source_actors["goalie"][str(actor)] += 1
                    source_actors["shooter"][str(actor)] += 1
            details = attempt["details"]
            geometry = facts["geometry"]
            recorded = _value(geometry, "recorded") or {}
            shot_type = _value(recorded, "model_shot_type")
            outcome = _value(details, "outcome")
            shooter = _value(details, "physical_shooter_id")
            goalie = _value(details, "opposing_goalie_id")
            side = _value(state, "home_away")
            opposing_side = "away" if side == "home" else "home" if side == "away" else None
            reasons = []
            if _value(details, "physical_status") != "ordinary": reasons.append("physical_attempt_not_supported_ordinary")
            if outcome not in ("block", "miss", "save", "goal"): reasons.append("outcome_unavailable")
            if event is None or not event["source"]["kind_valid"]: reasons.append("focal_identity_unavailable")
            if side is None or _value(state, "shooting_team_id") != _value(details, "shooting_team_id"): reasons.append("shooting_team_unavailable")
            strength = []
            for which in (side, opposing_side):
                members = _value(state, str(which) + "_skaters")
                goalies = _value(state, str(which) + "_goalies")
                if members is None or not 3 <= len(members) <= 6 or goalies is None:
                    reasons.append("membership_unavailable_or_outside_population")
                strength.append((len(members), len(goalies)) if members is not None and goalies is not None else (None, None))
            if strength[0][1] not in (0, 1) or strength[1][1] != 1: reasons.append("goalie_population_unavailable_or_outside")
            local_people = game.get("people") or {}
            if shooter is None or str(shooter) not in local_people: reasons.append("shooter_unavailable")
            if goalie is None or str(goalie) not in local_people: reasons.append("goalie_unavailable")
            if shot_type not in TYPES: reasons.append("shot_type_unavailable")
            try:
                if outcome == "block" and event is not None:
                    contact = event["geometry"]
                    _require(_value(contact, "frame") == "home_attack" and _value(contact, "location_kind") == "block_contact",
                             "block contact frame unavailable")
                    sign = 1 if side == "home" else -1
                    x, y = _value(contact, "x_ft"), _value(contact, "y_ft")
                    proxy = cell_id((sign * x, sign * y)) if x is not None and y is not None else cell_id((None, None))
                else:
                    proxy = cell_id((_value(geometry, "x"), _value(geometry, "y")))
            except (InputContractError, TypeError):
                reasons.append("location_or_frame_unavailable"); proxy = None
            stop = _value(attempt["immediate_outcomes"], "recorded_goalie_stop")
            head_labels = dict(u=None, q=None, r=None, g=None, observed_setter=-1)
            candidate_complete = None
            setter_discrepancy = None
            if not reasons:
                actor_coaches = {"attacking_coach": coach_game[side]["coach_id"],
                                 "defending_coach": coach_game[opposing_side]["coach_id"]}
                actors = {"shooter": str(shooter), "goalie": str(goalie), **actor_coaches}
                setter_prior, candidate_complete = _setter_prior(game, attempt, event, state, local_people)
                team_rest = _team_rest(team_schedules.get(_value(state, "opponent_team_id")), inventory["game_date"],
                                       {"input_ref": prepared_identity,
                                        "source": "prepared-analysis", "path": "/seasons"})
                context = _feature_context(attempt, game, shooter, goalie,
                                           (strength[0][0], strength[1][0], strength[0][1]), actor_coaches, team_rest)
                context["setter_universe_complete"] = candidate_complete
                context["attacking_skaters"] = [str(actor) for actor in _value(state, side + "_skaters")]
                context["attacking_goalies"] = [str(actor) for actor in _value(state, side + "_goalies")]
                context["setter_universe_reason"] = None if candidate_complete else "pre_event_membership_or_uninterrupted_prior_participants_unavailable"
                predictor = ExecutionPredictor(key, TYPES.index(shot_type), proxy, outcome == "block", shot_type == "tip",
                                               actors, {actor: people.get(actor) for actor in actors.values() if actor is not None}, setter_prior, context)
                head_labels["u"] = float(outcome != "block")
                if outcome != "block": head_labels["q"] = float(outcome in ("save", "goal"))
                if outcome in ("save", "goal") and stop is not None:
                    head_labels["r"] = float(not stop)
                    if not stop: head_labels["g"] = float(outcome == "goal")
                if outcome == "goal":
                    credit = credits.get(source_index)
                    if credit and credit["status"] == "credited":
                        assistant = credit["primary_assister_id"]
                        match = next((i for i, candidate in enumerate(setter_prior)
                                      if assistant is None and candidate.kind == "none" or assistant is not None and candidate.actor_id == str(assistant)), None)
                        if match is not None: head_labels["observed_setter"] = match
                        else: setter_discrepancy = "reported_primary_assistant_outside_pre_outcome_candidate_universe"
                predictors.append(predictor); labels.append(head_labels)
            dispositions = {}
            for head in HEADS:
                exclusion = reasons.copy()
                if not exclusion and head_labels[head] is None:
                    exclusion = ["requires_unblocked"] if head == "q" else ["requires_on_net"] if outcome not in ("save", "goal") else ["immediate_stop_label_unavailable"] if stop is None else ["recorded_stopped_save"]
                dispositions[head] = {"included": head_labels[head] is not None, "target": head_labels[head], "reasons": exclusion}
                totals[head]["included" if head_labels[head] is not None else "excluded"] += 1
                if head_labels[head] is not None:
                    totals[head]["class:" + str(int(head_labels[head]))] += 1
                    totals[head]["type:" + shot_type] += 1
                    totals[head]["strength:" + ",".join(map(str, (strength[0][0], strength[1][0], strength[0][1])))] += 1
            coverage_rows.append({"key": key, "game_id": game_id, "source_index": source_index,
                                  "outcome": outcome,
                                  "pointer": "/attempts/" + str(len(coverage_rows) - start_count), "heads": dispositions,
                                  "source_supported": not reasons, "candidate_universe_complete": candidate_complete,
                                  "setter_discrepancy": setter_discrepancy, "immediate_stop_known": stop is not None})
        game_rows.append({"game_id": game_id, "game_date": inventory["game_date"], "status": game["game"]["ledger"]["status"],
                          "recognized_attempts": len(coverage_rows) - start_count, "prepared_member": next(row for row in prepared["files"] if row["kind"] == "game" and row["game_id"] == game_id)})
    heads = {head: _head_design(head, predictors, labels, people, source_actors) for head in HEADS}
    selected_members = [row for row in prepared["files"] if row["season"] == season]
    prepared_ref = {"purpose": purpose, **prepared_identity, "members": selected_members}
    coach_ref = {"purpose": purpose, "path": str(coach_path), "sha256": _sha(coach_path), "selected_game_ids": list(selected["selected_game_ids"])}
    coverage = {"purpose": purpose, "season": season, "games": game_rows, "attempts": coverage_rows,
                "heads": {head: dict(counts) for head, counts in totals.items()},
                "optional_features": {head: heads[head]["design"]["feature_support"] for head in HEADS}}
    return ExecutionDesign(purpose, season, prepared_ref, coach_ref, max(dates, default=None), tuple(predictors), heads, coverage, seasons, RECIPE,
                           {"design_wall_seconds": perf_counter() - started, "input_read_wall_seconds": 0.})


def build_resolution_witness(design, requirement, block, actor_id):
    """construct an attributed synthetic shot for a present zero-shot actor."""
    if block != "shooter":
        return None
    actor_id = str(actor_id)
    context = next((predictor for predictor in sorted(design.predictors, key=lambda row: (row.key.split(":")[0], int(row.key.split(":")[1])))
                    if not predictor.tip and actor_id in predictor.context["attacking_skaters"] + predictor.context["attacking_goalies"]), None)
    if context is None:
        return None
    source_head = requirement.split(":")[1]
    actor = next((row for row in design.heads[source_head]["actors"]
                  if row["block"] == block and row["id"] == actor_id), None)
    if actor is None:
        return None
    prepared = read_prepared(design.prepared["path"], design.purpose)
    _require(_sha(design.prepared["path"]) == design.prepared["sha256"], "resolution prepared identity differs")
    game_id, source_index = context.key.split(":")
    source_index = int(source_index)
    game = read_prepared_game(prepared, design.season, game_id)
    people = game["people"] or {}
    if actor_id not in people:
        return None
    original = next(row for row in game["attempts"] if row["source_index"] == source_index)
    attempt = deepcopy(original)
    attempt["details"]["values"]["physical_shooter_id"] = int(actor_id)
    attempt["details"]["problems"].pop("physical_shooter_id", None)
    preceding = attempt["feature_facts"]["preceding"]
    if _value(preceding, "status") == "recent" and _value(preceding, "kind") in ACTION_KINDS[4:]:
        previous_index = _value(preceding, "source_index")
        previous = next((row for row in game["attempts"] if row["source_index"] == previous_index), None)
        previous_actor = _value(previous["details"], "physical_shooter_id") if previous is not None else None
        preceding["values"]["same_shooter"] = previous_actor == int(actor_id) if previous_actor is not None else None
        if previous_actor is not None:
            preceding["problems"].pop("same_shooter", None)
    state = attempt["feature_facts"]["state"]
    event = next(row for row in game["events"] if row["source"]["source_index"] == source_index)
    prior, complete = _setter_prior(game, attempt, event, state, people)
    coaches = {name: context.actors[name] for name in ("attacking_coach", "defending_coach")}
    features = _feature_context(attempt, game, int(actor_id), int(context.actors["goalie"]),
                                tuple(context.context["strength"]), coaches, {})
    # opponent-team rest is unchanged and already source-bound; do not fabricate
    # a second schedule from this one game while rebuilding actor circumstances.
    for name, value in context.context["features"].items():
        if name.startswith(("opposing_team:", "unavailable:opposing_team:")):
            features["features"][name] = dict(value)
    features.update(attacking_skaters=list(context.context["attacking_skaters"]),
                    attacking_goalies=list(context.context["attacking_goalies"]),
                    setter_universe_complete=complete,
                    setter_universe_reason=None if complete else "pre_event_membership_or_uninterrupted_prior_participants_unavailable")
    actors = dict(context.actors, shooter=actor_id)
    actor_facts = dict(context.actor_facts)
    actor_facts[actor_id] = people[actor_id]["people"]
    predictor = ExecutionPredictor("synthetic-resolution:" + context.key + ":shooter:" + actor_id,
                                   context.shot_type, context.proxy_cell, context.blocked, False,
                                   actors, actor_facts, prior, features)
    witness = {"kind": "synthetic", "source_key": context.key,
               "reason": "supported current actor has no focal shot; hypothetical shot at an actual on-ice source context",
               "changed_fields": ["shooter", "shooter_deployment", "shooter_prefix_workload", "shooter_calendar_rest",
                                  "reported_hand_off_wing", "recent_same_shooter", "setter_candidates_and_role_weights"],
               "actor": {"block": block, "id": actor_id, "role": actor["role"], "likelihood_support": actor["likelihood_support"]},
               "source_prepared_member": next(row for row in design.prepared["members"] if row["kind"] == "game" and row["game_id"] == game_id),
               "actual_attacking_skaters": list(context.context["attacking_skaters"]),
               "actual_attacking_goalies": list(context.context["attacking_goalies"]),
               "setter_universe_complete": complete}
    return predictor, witness
