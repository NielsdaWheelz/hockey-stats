"""explicit finite circumstance bases over located, prepared hockey facts."""

from collections import OrderedDict
from copy import deepcopy
import json
import math

import numpy as np

from .captures import InputContractError
from .feature_data import ACTION_KINDS

PREPARATION_IDENTITY = {
    "version": "features-03k-1",
    "interpretation_schema": 4,
    "reference_schema": 2,
    "corpus_schema": 2,
    "selection_schema": 2,
}
STAGES = ("origin", "u", "r", "unblocked", "all_attempt")
FAMILY_ORDER = (
    "game_additive", "recent_additive", "recent_interactions", "game_detail",
    "recent_detail", "recent_geometry", "off_wing", "action_windows", "zone_run",
    "sequence", "shift_age", "shift_start", "workload", "calendar_rest",
    "historical", "strength_transition",
)
CONTEXT_CATEGORIES = OrderedDict(
    score_bucket=["trailing_2_plus", "trailing_1", "tied", "leading_1", "leading_2_plus"],
    period=["1", "2", "3", "OT"],
    home_away=["home", "away"],
    minute_band=["first", "middle", "last"],
    recent_kind=list(ACTION_KINDS),
    recent_team=["same", "opponent"],
    recent_delay=list(range(6)),
    recent_zone=["attacking", "other"],
    recent_shooter=["same", "different"],
)
CONTEXT_FIELDS = list(CONTEXT_CATEGORIES)
CONTEXT_REFERENCES = dict(score_bucket="tied", period="1", home_away="away", minute_band="middle")
GAME_FEATURES = [
    f"{key}:{level}"
    for key, levels in list(CONTEXT_CATEGORIES.items())[:4]
    for level in levels if level != CONTEXT_REFERENCES[key]
]
RECENT_FEATURES = [
    f"{key}:{level}"
    for key, levels in list(CONTEXT_CATEGORIES.items())[4:]
    for level in levels
]
RECENT_INTERACTION_FEATURES = [
    f"recent_kind:{kind}:recent_team:same" for kind in ACTION_KINDS[1:]
] + [
    f"recent_kind:{kind}:recent_delay:{delay}"
    for kind in ACTION_KINDS[1:] for delay in range(1, 6)
]


class FeatureUnavailableError(InputContractError):
    """a valid prepared fact cannot fulfill a selected numerical requirement."""

    def __init__(self, *reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(reasons))


def validate_context(context, *, family=None):
    if not isinstance(context, dict) or list(context) != CONTEXT_FIELDS:
        raise InputContractError("attempt context fields/order disagree with current chance contract")
    for key, levels in CONTEXT_CATEGORIES.items():
        if (
            family == "game_additive" and key.startswith("recent_")
            or family in ("recent_additive", "recent_interactions")
            and not key.startswith("recent_")
        ):
            continue
        value = context[key]
        if key.startswith("recent_") and value is None:
            continue
        if value not in levels or key == "recent_delay" and type(value) is not int:
            raise InputContractError(f"unsupported context {key}")
    if family == "game_additive":
        return
    recent = context["recent_kind"] is not None
    if any((context[key] is not None) != recent for key in ("recent_team", "recent_delay", "recent_zone")):
        raise InputContractError("recent context factors disagree")
    if (context["recent_shooter"] is not None) != (context["recent_kind"] in ACTION_KINDS[4:]):
        raise InputContractError("recent shooter applicability disagrees")


def validate_stage_selection(stage, families, trait_assumptions):
    if stage not in STAGES or not isinstance(families, list) or any(not isinstance(f, str) for f in families):
        raise InputContractError("stage requires an ordered family array")
    if len(set(families)) != len(families) or any(f not in FAMILY_ORDER for f in families):
        raise InputContractError(f"{stage}: unknown or duplicate family")
    if families != [f for f in FAMILY_ORDER if f in families]:
        raise InputContractError(f"{stage}: family order disagrees with canonical order")
    if not isinstance(trait_assumptions, list) or trait_assumptions not in ([], ["reported_hand_stable_trait"]):
        raise InputContractError("unknown, duplicate or unordered trait assumption")
    if "recent_interactions" in families and (stage == "origin" or "recent_additive" not in families):
        raise InputContractError(f"{stage}: recent interactions require recent additive outside origin")
    if "recent_detail" in families and any(f in families for f in ("recent_additive", "recent_interactions")):
        raise InputContractError(f"{stage}: equivalent recent encodings cannot coexist")
    if stage in ("origin", "all_attempt") and any(f in families for f in ("recent_geometry", "off_wing")):
        raise InputContractError(f"{stage}: candidate geometry is forbidden")
    if "off_wing" in families and "reported_hand_stable_trait" not in trait_assumptions:
        raise InputContractError(f"{stage}: off-wing requires reported_hand_stable_trait")


def _columns(family):
    if family == "game_additive":
        return GAME_FEATURES.copy()
    if family == "recent_additive":
        return RECENT_FEATURES.copy()
    if family == "recent_interactions":
        return RECENT_INTERACTION_FEATURES.copy()
    if family == "game_detail":
        return ["score_margin/3", "period_fraction", "score_margin/3:period_fraction", "home:period2", "home:period3"]
    if family == "recent_detail":
        return ["recent_attempt_same", "recent_saved_shot_same", "recent_outside_zone_same", "recent_delay/5"]
    if family == "recent_geometry":
        return ["dx_ft/100", "dy_ft/100", "displacement_ft/100", "crossed_centerline"]
    if family == "off_wing":
        return ["off_wing"]
    if family == "action_windows":
        return [
            f"action_count:{window}:{side}:{kind}/10"
            for window in (5, 15, 30) for side in ("same", "opponent")
            for kind in ACTION_KINDS
        ]
    if family == "zone_run":
        return ["prior_zone_run_count/10", "prior_zone_run_age_seconds/60"]
    if family == "sequence":
        return [
            "defender_sequence_index:2", "defender_sequence_index:3",
            "defender_sequence_index:4+", "defender_sequence_age_seconds/60",
        ]
    if family == "shift_age":
        return ["shooter_age_seconds/60"] + [f"opposing_age_{stat}_seconds/60" for stat in ("min", "mean", "max")]
    if family == "shift_start":
        return [
            f"shooter_start_zone:{zone}" for zone in ("offensive", "neutral", "defensive")
        ] + [
            "last_faceoff:none", "last_faceoff_zone:offensive",
            "last_faceoff_zone:defensive", "last_faceoff_age_seconds/60",
        ]
    if family == "workload":
        return [
            "shooter_prefix_toi_all_seconds/3600", "shooter_prefix_shifts_completed/30",
            "shooter_prefix_attempts/10", "opposing_prefix_toi_all_mean_seconds/3600",
            "opposing_prefix_toi_all_max_seconds/3600",
        ] + [
            f"shooter_{scope}_{field}/{scale}" for scope in ("days_7", "days_14")
            for field, scale in (("toi_all_seconds", 3600), ("shifts", 30), ("attempts", 10))
        ]
    if family == "calendar_rest":
        return [
            f"{who}:{field}" for who in ("shooter", "opposing_team")
            for field in (
                "prior_exists", "calendar_gap_days", "prior_one_date", "prior_two_date",
                "games_days_7", "games_days_14",
            )
        ]
    if family == "historical":
        return [
            f"shooter_{scope}_{field}/{scale}" for scope in ("prior_season_1", "prior_season_2")
            for field, scale in (
                ("ice_appearances", 82), ("toi_all_seconds", 3600),
                ("toi_5v5_seconds", 3600), ("attempts", 100),
            )
        ]
    if family == "strength_transition":
        return ["previous_strength:same_fewer", "previous_strength:same_more", "return_to_5v5_age_seconds/60"]
    raise InputContractError(f"unknown family {family}")


def _transform_definition(family):
    return {
        "game_additive": "fixed category contrasts; tied,period1,away,middle references",
        "recent_additive": "fixed category indicators; supported none zeros",
        "recent_interactions": "six non-faceoff kind × same-team and kind × delay1..5 indicators",
        "game_detail": "margin/3; elapsed/nominal; their product; home×period2; home×period3",
        "recent_detail": "same-team attempt, saved-shot and outside-zone proxies; delay/5; supported none zeros",
        "recent_geometry": "candidate minus preceding current attacking coordinates; dx,dy,hypot/100; opposite nonzero y signs",
        "off_wing": "original reported right hand and candidate y>0, or left hand and y<0; supported centerline false",
        "action_windows": "reset-bounded prior kind counts/10; windows5,15,30; same then opponent",
        "zone_run": "recorded prior offensive-zone run count/10 and age/60; proven empty age0",
        "sequence": "persistent defender index2,index3,index4+ indicators and age/60; index1 reference",
        "shift_age": "original shooter and opposing-five min,mean,max compatible shift ages/60",
        "shift_start": "shooter offensive,neutral,defensive contrasts; no_same_clock_faceoff reference; last-faceoff none and offensive,defensive contrasts with neutral reference; age/60",
        "workload": "shooter current all-strength toi/3600,completed shifts/30,attempts/10; opposing-five mean,max prefix toi/3600; shooter7,14-day toi/3600,shifts/30,attempts/10",
        "calendar_rest": "shooter then opposing team: prior exists,gap days,prior-one/two-date,7/14-day games; proven no prior gap0",
        "historical": "shooter prior-one/two regular-season appearances/82,all-strength toi/3600,5v5 toi/3600,attempts/100; complete only",
        "strength_transition": "preceding same-team fewer/more membership indicators and return age/60; supported none zeros",
    }[family]


def stage_design(stage, families, *, core_layout, trait_assumptions):
    """compile syntax and coefficient identity without inspecting any record."""
    validate_stage_selection(stage, families, trait_assumptions)
    columns, slices, owners = [], {}, []
    for family in families:
        start = len(columns)
        additions = _columns(family)
        columns += additions
        slices[family] = [start, len(columns)]
        if stage == "origin":
            owner = "ridge_origin_factor+smooth_origin"
        elif stage in ("unblocked", "all_attempt") and family in FAMILY_ORDER[:3]:
            owner = "ridge_benchmark"
        else:
            owner = "ridge_context"
        owners += [owner] * len(additions)
    core = deepcopy(core_layout)
    prefix, suffix = core["prefix"], core["suffix"]
    if stage == "origin":
        maps = prefix + columns
        ordered = [f"{name}:cell:{cell}" for name in maps for cell in range(core["cells"])]
        numerical_slices = dict(core["slices"], scalar=[len(prefix) * core["cells"], len(ordered)])
    else:
        ordered = prefix + columns + suffix
        numerical_slices = dict(core["slices"], scalar=[len(prefix), len(prefix) + len(columns)])
        numerical_slices["shooter"] = [
            len(prefix) + len(columns),
            len(prefix) + len(columns) + core.get("shooter_size", 0),
        ]
        numerical_slices["goalie"] = [numerical_slices["shooter"][1], len(ordered)]
    return dict(
        schema_version=1, stage=stage, families=families.copy(),
        trait_assumptions=trait_assumptions.copy(), preparation_identity=deepcopy(PREPARATION_IDENTITY),
        core_layout=core, columns=ordered, circumstance_columns=columns,
        family_slices=slices, slices=numerical_slices, penalty_owners=owners,
        fixed_transforms={family: _transform_definition(family) for family in families},
        core_penalties=(
            "base ridge_origin_base; other maps ridge_origin_factor; all maps smooth_origin"
            if stage == "origin" else
            "unpenalized intercept; season ridge_context; cells ridge_cell/type_cell and smooth_cell; actor ridge and adjacent-season change"
            if stage in ("u", "r") else
            "unpenalized intercept; core ridge_benchmark; actor ridge and adjacent-season change"
        ),
        reference_treatment="freeze_original_circumstances_swap_residual_actor_coefficients",
    )


def requirement_reason_prefix(key, field, *, status, reason):
    """the located requirement description shared by errors and saved audit checks."""
    return f"{key}.{field}: {status}: {reason}; evidence="


def _required(record, field, key):
    if (
        not isinstance(record, dict) or not isinstance(record.get("values"), dict)
        or field not in record["values"]
    ):
        raise InputContractError(f"{key}.{field}: unavailable prepared requirement")
    value = record["values"][field]
    if value is None:
        problems = record.get("problems")
        problem = problems.get(field) if isinstance(problems, dict) else None
        if (
            not isinstance(problem, dict)
            or problem.get("status") not in ("unavailable", "conflict", "not_applicable")
            or not isinstance(problem.get("reason"), str) or not problem["reason"]
            or not isinstance(problem.get("evidence_refs"), list)
            or not isinstance(record.get("evidence"), list)
            or any(type(index) is not int or not 0 <= index < len(record["evidence"])
                   for index in problem["evidence_refs"])
        ):
            raise InputContractError(f"{key}.{field}: null has no located problem")
        evidence = [record["evidence"][index] for index in problem["evidence_refs"]]
        if any(
            not isinstance(locator, dict) or set(locator) != {"input_ref", "source", "path"}
            or any(not isinstance(value, str) or not value for value in locator.values())
            for locator in evidence
        ):
            raise InputContractError(f"{key}.{field}: invalid missing-field evidence")
        raise FeatureUnavailableError(
            requirement_reason_prefix(key, field, status=problem["status"], reason=problem["reason"])
            + json.dumps(evidence, sort_keys=True, separators=(",", ":"))
        )
    return value


def encode_stage_inputs(attempt, design, *, game_facts, player_game_facts):
    """encode fixed values once and retain only selected candidate inputs."""
    key = f"{attempt.get('game_id')}:{attempt.get('source_index')}:{design['stage']}"
    local = attempt.get("feature_facts", {})
    shooter_key = str(attempt.get("shooter_id"))
    player = player_game_facts.get(shooter_key, {})
    values, candidate = [], {}
    for family in design["families"]:
        family_key = f"{key}.{family}"
        if family in ("game_additive", "recent_additive", "recent_interactions"):
            context = attempt.get("context")
            try:
                validate_context(context, family=family)
                if (
                    family != "game_additive"
                    and attempt.get("previous_event", {}).get("status") not in ("none", "recent")
                ):
                    raise InputContractError("supported preceding-action disposition required")
            except InputContractError as error:
                raise InputContractError(f"{family_key}: {error}") from error
            if family in ("game_additive", "recent_additive"):
                items = (
                    list(CONTEXT_CATEGORIES.items())[:4] if family == "game_additive"
                    else list(CONTEXT_CATEGORIES.items())[4:]
                )
                values += [
                    context[field] == level for field, levels in items for level in levels
                    if level != CONTEXT_REFERENCES.get(field)
                ]
            else:
                values += [
                    context["recent_kind"] == kind and context["recent_team"] == "same"
                    for kind in ACTION_KINDS[1:]
                ]
                values += [
                    context["recent_kind"] == kind and context["recent_delay"] == delay
                    for kind in ACTION_KINDS[1:] for delay in range(1, 6)
                ]
        elif family == "game_detail":
            state = local.get("state", {})
            margin = _required(state, "score_margin", family_key) / 3
            elapsed = _required(state, "elapsed_seconds", family_key)
            nominal = _required(state, "nominal_length_seconds", family_key)
            fraction = elapsed / nominal
            if (
                attempt.get("home_away") not in ("home", "away")
                or attempt.get("context", {}).get("period") not in ("1", "2", "3", "OT")
            ):
                raise InputContractError(f"{family_key}: home/period unavailable")
            home = attempt["home_away"] == "home"
            values += [
                margin, fraction, margin * fraction,
                home and attempt["context"]["period"] == "2",
                home and attempt["context"]["period"] == "3",
            ]
        elif family == "recent_detail":
            preceding = local.get("preceding", {})
            status = _required(preceding, "status", family_key)
            if status == "none":
                values += [0] * 4
            elif status == "recent":
                values += [
                    _required(preceding, field, family_key)
                    for field in ("recent_same_team_attempt", "recent_saved_shot", "outside_zone")
                ]
                values.append(_required(preceding, "time_gap_seconds", family_key) / 5)
            elif status == "unavailable":
                raise FeatureUnavailableError(
                    f"{family_key}.status: unavailable: preceding evidence"
                )
            else:
                raise InputContractError(f"{family_key}.status: unsupported preceding disposition")
        elif family == "recent_geometry":
            previous = attempt.get("previous_event")
            if not isinstance(previous, dict) or previous.get("status") not in ("recent", "none", "unavailable"):
                raise InputContractError(f"{family_key}.previous_event: unsupported preceding disposition")
            if previous["status"] != "recent":
                status = "not_applicable" if previous["status"] == "none" else "unavailable"
                raise FeatureUnavailableError(
                    f"{family_key}.previous_event: {status}: supported recent preceding location required"
                )
            for axis in ("x", "y"):
                field = "current_attack_" + axis
                value = previous.get(field) if isinstance(previous, dict) else None
                if field not in previous or type(value) not in (int, float) or not math.isfinite(value):
                    raise InputContractError(f"{family_key}.previous_event.{field}: invalid supported preceding location")
                candidate["previous_" + axis] = value
            values += [0] * 4
        elif family == "off_wing":
            hand = _required(player.get("people", {}), "shoots_catches", f"{family_key}.player:{shooter_key}")
            if hand not in ("L", "R"):
                raise InputContractError(f"{family_key}.shoots_catches: unsupported reported hand")
            candidate["hand"] = 1 if hand == "R" else -1
            values.append(0)
        elif family == "action_windows":
            sequence = local.get("sequence", {})
            counts = _required(sequence, "action_counts", family_key)
            for window in (5, 15, 30):
                window_values = counts.get(str(window), {}).get("values", {})
                for side in ("same", "opponent"):
                    side_record = window_values.get(side, {})
                    values += [
                        _required(side_record, kind, f"{family_key}.{window}.{side}") / 10
                        for kind in ACTION_KINDS
                    ]
        elif family == "zone_run":
            record = local.get("sequence", {})
            count = _required(record, "prior_zone_run_count", family_key)
            age = 0 if count == 0 else _required(record, "prior_zone_run_age_seconds", family_key)
            values += [count / 10, age / 60]
        elif family == "sequence":
            record = local.get("sequence", {})
            sequence, reasons = {}, []
            for field in ("defender_sequence_index", "defender_sequence_age_seconds"):
                try:
                    sequence[field] = _required(record, field, family_key)
                except FeatureUnavailableError as error:
                    if not record["problems"][field]["evidence_refs"]:
                        raise InputContractError(f"{family_key}.{field}: missing sequence evidence locator") from error
                    reasons.extend(error.reasons)
            index = sequence.get("defender_sequence_index")
            age = sequence.get("defender_sequence_age_seconds")
            if (
                index is not None and (type(index) is not int or index < 1)
                or age is not None and (type(age) not in (int, float) or not math.isfinite(age) or age < 0)
            ):
                raise InputContractError(f"{family_key}: invalid sequence index or age")
            if reasons:
                raise FeatureUnavailableError(*reasons)
            values += [index == 2, index == 3, index >= 4, age / 60]
        elif family == "shift_age":
            record = local.get("deployment", {})
            players = _required(record, "players", family_key)
            values.append(_required(
                players.get(shooter_key, {}), "age_seconds",
                f"{family_key}.player:{shooter_key}",
            ) / 60)
            opposing = _required(record, "opposing_five", family_key)
            values += [
                _required(opposing, "age_" + stat + "_seconds", family_key) / 60
                for stat in ("min", "mean", "max")
            ]
        elif family == "shift_start":
            record = local.get("deployment", {})
            players = _required(record, "players", family_key)
            shooter = players.get(shooter_key, {})
            start_type = _required(shooter, "start_type", f"{family_key}.player:{shooter_key}")
            zone = None if start_type == "no_same_clock_faceoff" else _required(shooter, "start_zone", family_key)
            if zone is not None and zone not in ("offensive", "neutral", "defensive"):
                raise InputContractError(f"{family_key}.start_zone: unsupported zone")
            values += [zone == z for z in ("offensive", "neutral", "defensive")]
            exists = _required(record, "last_faceoff_exists", family_key)
            if not exists:
                values += [1, 0, 0, 0]
            else:
                zone = _required(record, "last_faceoff_zone", family_key)
                if zone not in ("offensive", "neutral", "defensive"):
                    raise InputContractError(f"{family_key}.last_faceoff_zone: unsupported zone")
                values += [
                    0, zone == "offensive", zone == "defensive",
                    _required(record, "last_faceoff_age_seconds", family_key) / 60,
                ]
        elif family == "workload":
            record = local.get("current_workload", {})
            players = _required(record, "players", family_key)
            shooter = players.get(shooter_key, {})
            values += [
                _required(shooter, field, family_key) / scale for field, scale in (
                    ("toi_all_seconds", 3600), ("shifts_completed", 30), ("attempts", 10),
                )
            ]
            opposing = _required(record, "opposing_five", family_key)
            values += [
                _required(opposing, field, family_key) / 3600
                for field in ("toi_all_mean_seconds", "toi_all_max_seconds")
            ]
            for scope in ("days_7", "days_14"):
                window = player.get("workload", {}).get(scope, {})
                values += [
                    _required(window, field, f"{family_key}.{scope}") / scale
                    for field, scale in (("toi_all_seconds", 3600), ("shifts", 30), ("attempts", 10))
                ]
        elif family == "calendar_rest":
            opponent_id = _required(local.get("state", {}), "opponent_team_id", family_key)
            opponents = game_facts.get("teams", {}).get(str(opponent_id), {})
            for who, record, exists_field in (
                ("shooter", player.get("calendar_rest", {}), "prior_appearance_exists"),
                ("opposing_team", opponents.get("calendar_rest", {}), "prior_game_exists"),
            ):
                rest_key = f"{family_key}.{who}"
                exists = _required(record, exists_field, rest_key)
                gap = _required(record, "calendar_gap_days", rest_key) if exists else 0
                values += [exists, gap] + [
                    _required(record, field, rest_key) for field in (
                        "prior_one_date", "prior_two_date", "games_days_7", "games_days_14",
                    )
                ]
        elif family == "historical":
            for scope in ("prior_season_1", "prior_season_2"):
                window = player.get("history", {}).get(scope, {})
                values += [
                    _required(window, field, f"{family_key}.{scope}") / scale
                    for field, scale in (
                        ("ice_appearances", 82), ("toi_all_seconds", 3600),
                        ("toi_5v5_seconds", 3600), ("attempts", 100),
                    )
                ]
        elif family == "strength_transition":
            record = local.get("deployment", {})
            exists = _required(record, "strength_transition_exists", family_key)
            if not exists:
                values += [0, 0, 0]
            else:
                side = _required(record, "previous_strength_side", family_key)
                if side not in ("same", "opponent"):
                    raise InputContractError(f"{family_key}.previous_strength_side: unsupported side")
                values += [
                    side == "same", side == "opponent",
                    _required(record, "strength_transition_age_seconds", family_key) / 60,
                ]
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (len(design["circumstance_columns"]),) or not np.isfinite(array).all():
        raise InputContractError(f"{key}: invalid finite encoded values")
    return array, candidate


def candidate_columns(inputs, design, origin_xy):
    """yield one candidate column at a time; never allocate an n×cells×features tensor."""
    x, y = origin_xy
    for family in design["families"]:
        if family == "recent_geometry":
            start = design["family_slices"][family][0]
            dx, dy = x - inputs["previous_x"], y - inputs["previous_y"]
            yield start, dx / 100
            yield start + 1, dy / 100
            yield start + 2, np.hypot(dx, dy) / 100
            yield start + 3, np.asarray(
                ((y > 0) & (inputs["previous_y"] < 0))
                | ((y < 0) & (inputs["previous_y"] > 0)),
                dtype=np.float64,
            )
        elif family == "off_wing":
            start = design["family_slices"][family][0]
            yield start, np.asarray(y * inputs["hand"] > 0, dtype=np.float64)


def encode_stage(attempt, design, *, game_facts, player_game_facts, origin_xy=None):
    """return the matching circumstance vector or a keyed requirement error."""
    values, inputs = encode_stage_inputs(attempt, design, game_facts=game_facts, player_game_facts=player_game_facts)
    if inputs:
        if (
            not isinstance(origin_xy, (tuple, list, np.ndarray)) or len(origin_xy) != 2
            or any(type(v) not in (int, float, np.float64) or not math.isfinite(v) for v in origin_xy)
        ):
            key = f"{attempt.get('game_id')}:{attempt.get('source_index')}:{design['stage']}"
            raise InputContractError(f"{key}.origin_xy: explicit finite candidate required")
        for index, value in candidate_columns(inputs, design, origin_xy):
            values[index] = value
    return values
