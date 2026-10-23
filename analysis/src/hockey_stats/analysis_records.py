"""closed prepared-evidence records and recursive, source-independent validation."""

from datetime import date
from functools import cache
import math
import re
import types
from typing import (
    Any,
    Generic,
    Literal,
    NotRequired,
    TypeVar,
    TypedDict,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

from .captures import InputContractError
from .interpret import (
    BoxscorePlayer,
    Check,
    Event,
    FieldProblem,
    Game,
    Input,
    Issue,
    ReportRow,
    Result,
    RosterRecord,
    ScoreCounts,
    SourceFields,
    SourceObservation,
    GameDocument,
    Interpretation,
    SourceEvidence,
    SKATER_SOURCE_FIELDS,
    GOALIE_SOURCE_FIELDS,
    RECORDING_FIELDS,
    SUMMARY_RECORDING_FIELDS,
)
from .references import (
    BioObservation,
    BIO_INTEGER_SOURCE_FIELDS,
    InventoryGame,
    BIO_SKATER_SOURCE_FIELDS,
    BIO_GOALIE_SOURCE_FIELDS,
)
from .reconstruct import (
    Interval,
    Membership,
    Period,
    ReconstructedEvent,
    Reconstruction,
)
from .corpus import GameStatus
from .feature_data import COUNTERS, ACTION_KINDS

Number = int | float
T = TypeVar("T")


class InputReference(TypedDict):
    path: str
    sha256: str


class ConsumedInput(InputReference):
    kind: str


class Evidence(TypedDict):
    input_ref: InputReference
    source: str
    path: str
    requested_at: NotRequired[str | None]
    requested_season: NotRequired[str]
    season: NotRequired[str]
    game_id: NotRequired[str]
    field: NotRequired[str]
    input_index: NotRequired[int]


class Fact(TypedDict, Generic[T]):
    values: T
    problems: dict[str, FieldProblem]
    evidence: list[Evidence]


class GeometryValues(TypedDict):
    x_ft: Number | None
    y_ft: Number | None
    frame: Literal["home_attack"] | None
    location_kind: Literal["reported_event", "block_contact", "unavailable"]


class ChronologyValues(TypedDict):
    order_index: int | None
    predecessor_source_index: int | None
    successor_source_index: int | None
    episode_index: int | None
    reset_source_index: int | None


class PrefixValues(TypedDict):
    toi_all_seconds: Number | None
    toi_5v5_seconds: Number | None
    attempts: int | None
    goals: int | None
    shifts_begun: int | None
    shifts_completed: int | None
    known_toi_all_seconds: Number | None
    known_toi_5v5_seconds: Number | None
    known_attempts: int | None
    known_goals: int | None
    known_shifts_begun: int | None
    known_shifts_completed: int | None
    on_net_faced: int | None
    known_on_net_faced: int | None


class TransitionValues(TypedDict):
    exists: bool | None
    prior_shorthanded_side: Literal["home", "away"] | None
    return_seconds: Number | None
    age_seconds: Number | None


class EventContext(TypedDict):
    prefix_by_player: dict[str, Fact[PrefixValues]]
    live_episode_index: int | None
    strength_transition: Fact[TransitionValues]


class PreparedEvent(TypedDict):
    source: Event
    pre_score: Fact[ScoreCounts]
    geometry: Fact[GeometryValues]
    chronology: Fact[ChronologyValues]
    context: EventContext


class Association(TypedDict):
    source_index: int
    native: ReconstructedEvent | None
    touching_segment_indices: list[int]
    matching_segment_indices: list[int]
    temporal_case: Literal["interior", "boundary", "unavailable"]
    issue_indices: list[int]


class Segment(TypedDict):
    segment_index: int
    native_interval_indices: list[int]
    period_number: int
    start_seconds: Number
    end_seconds: Number
    membership: Membership
    issue_indices: list[int]


class UnitValues(TypedDict):
    member_count: int | None
    known_count: int | None
    known_toi_all_sum_seconds: Number | None
    toi_all_mean_seconds: Number | None
    toi_all_max_seconds: Number | None


class ScalarValue(TypedDict):
    value: Number | None


class MemberContext(TypedDict):
    player_id: int
    player_shift_index: int | None
    shift_age_seconds: Fact[ScalarValue]
    elapsed_prefix: Fact[PrefixValues]


class Chunk(TypedDict):
    chunk_index: int
    segment_index: int
    start_seconds: Number
    end_seconds: Number
    score: Fact[ScoreCounts]
    strength_transition: Fact[TransitionValues]
    member_contexts: list[MemberContext]
    away_unit: Fact[UnitValues]
    home_unit: Fact[UnitValues]
    issue_indices: list[int]


class StartValues(TypedDict):
    kind: Literal["faceoff", "on_the_fly", "unknown"]
    zone: Literal["offensive", "neutral", "defensive"] | None
    event_source_index: int | None
    episode_index: int | None
    rest_seconds: Number | None


class PlayerShift(TypedDict):
    player_shift_index: int
    player_id: int
    team_id: int
    period_number: int
    start_seconds: Number
    end_seconds: Number
    native_shift_indices: list[int]
    native_interval_indices: list[int]
    start: Fact[StartValues]
    issue_indices: list[int]


class Episode(TypedDict):
    episode_index: int
    period_number: int
    start_seconds: Number
    end_seconds: Number | None
    start_source_index: int
    end_source_index: int | None
    start_kind: Literal["faceoff", "first_live_action"]
    left_censored: bool
    end_reason: Literal["reset", "faceoff", "terminal", "unknown"]
    issue_indices: list[int]


class DetailsValues(TypedDict):
    outcome: Literal["block", "miss", "save", "goal"] | None
    physical_status: Literal["ordinary", "outside_population", "unresolved"]
    credited_shooter_id: int | None
    physical_shooter_id: int | None
    shooting_team_id: int | None
    opposing_goalie_id: int | None
    location_kind: Literal["reported_attempt", "block_contact", "unavailable"]


class ImmediateValues(TypedDict):
    recorded_goalie_stop: bool | None
    reattempt_within_5s: bool | None
    reattempt_source_index: int | None
    next_event_source_index: int | None
    next_event_delay_seconds: Number | None


class RecordedGeometry(TypedDict):
    recorded_shot_type: str | None
    reconciled_shot_type: str | None
    model_shot_type: str | None
    reported_x: Number | None
    reported_y: Number | None
    location_kind: Literal["block_evidence", "recorded_proxy"]
    coordinate_status: Literal[
        "normalized", "missing_coordinates", "unresolved_frame", "not_applicable"
    ]


class AttemptGeometry(TypedDict):
    x: Number | None
    y: Number | None
    distance_ft: Number | None
    signed_angle_rad: Number | None
    absolute_angle_rad: Number | None
    region: Literal["outside_zone", "beyond_goal", "attacking_zone"] | None
    side: Literal["positive_y", "negative_y", "centerline"] | None
    off_wing: bool | None
    dx_ft: Number | None
    dy_ft: Number | None
    displacement_ft: Number | None
    crossed_centerline: bool | None
    recorded: Fact[RecordedGeometry]


class StateValues(TypedDict):
    away_score: int | None
    home_score: int | None
    score_margin: int | None
    period_number: int | None
    period_type: str | None
    elapsed_seconds: Number | None
    remaining_seconds: Number | None
    nominal_length_seconds: Number | None
    game_seconds: Number | None
    even_period_proxy: bool | None
    first_minute: bool | None
    last_minute: bool | None
    home_away: str | None
    shooting_team_id: int | None
    opponent_team_id: int | None
    situation_code: str | None
    away_skaters: list[int] | None
    away_skater_count: int | None
    home_skaters: list[int] | None
    home_skater_count: int | None
    away_goalies: list[int] | None
    away_goalie_count: int | None
    home_goalies: list[int] | None
    home_goalie_count: int | None


class ImmediateGeometry(TypedDict):
    reported_x: Number | None
    reported_y: Number | None
    current_attack_x: Number | None
    current_attack_y: Number | None
    location_basis: str | None


class PrecedingValues(TypedDict):
    status: Literal["unavailable", "none", "recent"]
    source_index: int | None
    event_id: int | None
    kind: str | None
    time_gap_seconds: Number | None
    owner_team_relation: Literal["same", "opponent"] | None
    current_attack_x: Number | None
    current_attack_y: Number | None
    location_basis: str | None
    same_shooter: bool | None
    reason: str | None
    roles: dict[str, int | None] | None
    context_reason: str | None
    secondary_reason: str | None
    penalty_description: str | None
    recent_same_team_attempt: bool | None
    recent_saved_shot: bool | None
    inside_zone: bool | None
    outside_zone: bool | None
    owner_team_id: int | None
    shooting_team_id: int | None
    immediate_geometry: Fact[ImmediateGeometry] | None


ActionValues = TypedDict(
    "ActionValues",
    {
        key: int | None
        for kind in (*ACTION_KINDS, "attempts")
        for key in (kind, "known_" + kind)
    },
)


class ActionSides(TypedDict):
    same: Fact[ActionValues]
    opponent: Fact[ActionValues]


ActionWindows = TypedDict(
    "ActionWindows", {str(width): Fact[ActionSides] for width in (5, 15, 30)}
)


class SequenceValues(TypedDict):
    defender_sequence_index: int | None
    defender_sequence_age_seconds: Number | None
    prior_zone_run_count: int | None
    prior_zone_run_start_seconds: Number | None
    prior_zone_run_age_seconds: Number | None
    action_counts: ActionWindows


class DeploymentPlayer(TypedDict):
    shift_source_index: int | None
    start_seconds: Number | None
    end_seconds: Number | None
    age_seconds: Number | None
    previous_shift_gap_seconds: Number | None
    start_type: str | None
    start_zone: str | None


class AgeUnit(TypedDict):
    member_count: int | None
    known_count: int | None
    known_age_sum_seconds: Number | None
    age_min_seconds: Number | None
    age_mean_seconds: Number | None
    age_max_seconds: Number | None


class DeploymentValues(TypedDict):
    players: dict[str, Fact[DeploymentPlayer]]
    attacking_unit: Fact[AgeUnit]
    opposing_unit: Fact[AgeUnit]
    last_faceoff_exists: bool | None
    last_faceoff_source_index: int | None
    last_faceoff_zone: str | None
    last_faceoff_age_seconds: Number | None
    strength_transition_exists: bool | None
    previous_strength_side: str | None
    strength_transition_age_seconds: Number | None
    penalty_source_index: int | None
    penalty_team_id: int | None
    penalty_roles: dict[str, int | None] | None
    penalty_type: str | None
    penalty_description: str | None
    penalty_duration_minutes: int | None
    penalty_age_seconds: Number | None
    interval_substitution_count: int | None
    endpoint_change_count: int | None


class WorkloadValues(TypedDict):
    players: dict[str, Fact[PrefixValues]]
    opposing_unit: Fact[UnitValues]


class OutcomeValues(TypedDict):
    recorded_outcome: str | None
    outcome: str | None
    on_net: bool | None
    modifier: str | None
    blocker_id: int | None
    miss_reason: str | None
    penalty_reason: str | None
    stoppage_reason: str | None
    next_event_source_index: int | None
    next_event_id: int | None
    next_event_kind: str | None
    next_event_delay_seconds: Number | None
    next_event_roles: dict[str, int | None] | None
    next_event_reason: str | None
    next_event_secondary_reason: str | None
    next_stoppage_source_index: int | None
    next_stoppage_event_id: int | None
    next_stoppage_delay_seconds: Number | None
    next_stoppage_reason: str | None
    next_stoppage_secondary_reason: str | None
    intervening_source_indices: list[int] | None
    intervening_kinds: list[str | None] | None
    next_same_team_attempt_within_5s: bool | None
    next_same_team_attempt_source_index: int | None
    goalie_stopped_after_sog: bool | None
    goalie_stoppage_delay_seconds: Number | None


class RetainedAttemptFacts(TypedDict):
    geometry: Fact[AttemptGeometry]
    state: Fact[StateValues]
    preceding: Fact[PrecedingValues]
    sequence: Fact[SequenceValues]
    deployment: Fact[DeploymentValues]
    current_workload: Fact[WorkloadValues]
    outcome: Fact[OutcomeValues]


class Attempt(TypedDict):
    source_index: int
    details: Fact[DetailsValues]
    feature_facts: RetainedAttemptFacts
    immediate_outcomes: Fact[ImmediateValues]


class PositionObservation(TypedDict):
    reported_position: str | None
    source: str
    path: str


class IdentityObservations(TypedDict):
    roster: list[RosterRecord]
    boxscore: list[BoxscorePlayer]


class BoundBio(BioObservation):
    input_ref: NotRequired[InputReference]


class PersonValues(TypedDict):
    player_id: int
    team_id: int | None
    reported_position: str | None
    first_name: str | None
    last_name: str | None
    name: str | None
    birth_date: str | None
    shoots_catches: str | None
    age_days: int | None
    bio_observations: list[BoundBio]
    reported_totals: SourceFields | None
    position_observations: list[PositionObservation]
    identity_observations: NotRequired[IdentityObservations]


CounterValues = TypedDict(
    "CounterValues",
    {key: int | None for field in COUNTERS for key in (field, "known_" + field)},
)


class Window(Fact[CounterValues]):
    scope: str
    start: str | None
    cutoff: str | None
    complete: bool
    contributing_game_ids: list[str]
    unavailable_game_ids: list[str]


class WorkloadWindows(TypedDict):
    days_7: Window
    days_14: Window
    season_prefix: Window
    previous_game: Window


class RestValues(TypedDict):
    prior_appearance_exists: bool | None
    prior_game_date: str | None
    calendar_gap_days: int | None
    prior_one_date: bool | None
    prior_two_date: bool | None
    games_days_7: int | None
    games_days_14: int | None


class FirstAppearance(TypedDict):
    game_date: str | None
    game_id: str | None
    game_ids: list[str]


class TeamRole(TypedDict):
    game_id: str
    game_date: str
    team_id: int | None
    role: str | None


class HistoryIdentity(TypedDict):
    first_observed_appearance: Fact[FirstAppearance]
    first_observation_left_censored: bool
    prior_teams: list[int]
    prior_roles: list[str]
    team_role_observations: list[TeamRole]
    team_changes: int | None
    role_changes: int | None


class History(TypedDict):
    prior_season_1: Window
    prior_season_2: Window
    identity: Fact[HistoryIdentity]


class Sweater(TypedDict):
    team_id: int
    game_id: str
    number: int


class GamePerson(TypedDict):
    people: Fact[PersonValues]
    roster: list[RosterRecord]
    boxscore: list[BoxscorePlayer]
    sweaters: list[Sweater]
    workload: WorkloadWindows
    calendar_rest: Fact[RestValues]
    history: History


class SeasonPersonValues(TypedDict):
    player_id: int
    name: str | None
    team_ids: list[int]
    reported_positions: list[str]
    position_group: Literal["F", "D", "G"] | None
    sweaters: list[Sweater]
    birth_date: str | None
    shoots_catches: Literal["L", "R"] | None
    age_reference_date: str
    age_days: int | None
    height_cm: Number | None


class LocatedIssue(Issue):
    evidence: list[Evidence]


class Ledger(TypedDict):
    status: GameStatus
    reason: str | None


class GameEvidence(TypedDict):
    inventory: InventoryGame
    ledger: Ledger
    identity: Game | None
    inputs: list[Input]
    reported_results: list[Result]
    checks: list[Check]
    periods: list[Period] | None
    native_intervals: list[Interval] | None
    report_rows: list[ReportRow] | None
    recording_observations: list[SourceObservation]
    source_issues: list[Issue]
    native_issues: list[Issue]


class CreditEvidence(TypedDict):
    source: str
    capture_path: str
    body_sha256: str | None
    field: str


class Credit(TypedDict):
    source_index: int
    status: Literal["credited", "unresolved"]
    scorer_or_shooter_id: int | None
    primary_assister_id: int | None
    evidence_refs: list[CreditEvidence]
    reason: str | None


class SegmentSupport(TypedDict):
    segment_index: int
    disposition: Literal["included", "excluded"]
    reason_indices: list[int]


class EventSupport(TypedDict):
    source_index: int
    disposition: Literal["included", "excluded", "not_applicable", "unresolved"]
    segment_index: int | None
    chunk_index: int | None
    reason_indices: list[int]


class ReportSupport(TypedDict):
    report_source_index: int
    affected_segment_indices: list[int]
    reason_indices: list[int]


class SupportReason(TypedDict):
    code: Literal[
        "source_unavailable",
        "count_accounting_conflict",
        "membership_unavailable",
        "identity_conflict",
        "strength_conflict",
        "ambiguous_assignment",
        "event_evidence_unresolved",
        "unmatched_report_attempt",
        "clock_unavailable",
        "horizon_unavailable",
    ]
    scope: Literal["segment", "period", "game"]
    period_number: int | None
    event_source_indices: list[int]
    report_source_indices: list[int]
    affected_segment_indices: list[int]
    evidence: list[Evidence]


class Support(TypedDict):
    segments: list[SegmentSupport] | None
    events: list[EventSupport] | None
    report_only: list[ReportSupport] | None
    reasons: list[SupportReason]


class NativeEnvelope(TypedDict):
    schema_version: Literal[4]
    implementation: NotRequired[Interpretation]
    interpreted: GameDocument
    reconstruction: Reconstruction


class PreparedGame(TypedDict):
    schema_version: Literal[1]
    season: str
    game_id: str
    game: GameEvidence
    events: list[PreparedEvent] | None
    associations: list[Association] | None
    segments: list[Segment] | None
    chunks: list[Chunk] | None
    player_shifts: list[PlayerShift] | None
    episodes: list[Episode] | None
    people: dict[str, GamePerson] | None
    attempts: list[Attempt] | None
    credits: list[Credit] | None
    ordinary_attempt_support: Support
    issues: list[LocatedIssue]


class PreparedPeople(TypedDict):
    schema_version: Literal[1]
    season: str
    people: list[Fact[SeasonPersonValues]]


class CompletenessCount(TypedDict):
    available: int
    partial: int
    unavailable: int
    not_applicable: int


Completeness = TypedDict(
    "Completeness",
    {
        name: CompletenessCount
        for name in (
            "order",
            "score",
            "frame",
            "identity",
            "history",
            "event_context",
            "elapsed_context",
            "immediate_stop",
            "reattempt",
        )
    },
)
StatusCounts = TypedDict("StatusCounts", {name: int for name in get_args(GameStatus)})


class SourceCoverage(TypedDict):
    source: str
    available_games: int
    unavailable_games: int


class EventCoverage(TypedDict):
    kind: str | None
    outcome: Literal["block", "miss", "save", "goal"] | None
    count: int


class TimeCoverage(TypedDict):
    away_skaters: int
    home_skaters: int
    away_goalies: int
    home_goalies: int
    physical_seconds: Number
    included_seconds: Number
    excluded_seconds: Number
    team_seconds: Number
    skater_slot_seconds: Number
    goalie_slot_seconds: Number


class SeasonCoverage(TypedDict):
    season: str
    inventory_games: int
    selected_games: int
    game_status_counts: StatusCounts
    game_sources: list[SourceCoverage]
    events: list[EventCoverage]
    report_only_attempts: int
    time: list[TimeCoverage]
    unknown_horizon_games: int
    unresolved_known_seconds: Number
    completeness: Completeness


class Coverage(TypedDict):
    schema_version: Literal[1]
    seasons: list[SeasonCoverage]


class SelectionSeason(TypedDict):
    season: str
    corpus_manifest: str
    sha256: str
    game_ids: list[str] | None


class Selection(TypedDict):
    schema_version: Literal[1]
    purpose: Literal["real", "fixture"]
    seasons: list[SelectionSeason]


class ManifestSeason(TypedDict):
    season: str
    inventory_games: int
    selected_game_ids: list[str]


class Member(TypedDict):
    kind: Literal["game", "people", "coverage"]
    season: str | None
    game_id: str | None
    path: str
    sha256: str


class Implementation(TypedDict):
    git_commit: str | None
    git_dirty: bool | None
    python_version: str
    preparation_policy_sha256: str
    source_code_sha256: str


class Resources(TypedDict):
    wall_seconds: Number
    peak_memory_bytes: int
    output_bytes: int


class Manifest(TypedDict):
    schema_version: Literal[1]
    kind: Literal["prepared-analysis"]
    purpose: Literal["real", "fixture"]
    preparation_id: Literal["experimental-evidence-v1"]
    implementation: Implementation
    selection: InputReference
    inputs: list[ConsumedInput]
    seasons: list[ManifestSeason]
    files: list[Member]
    resources: Resources


def require(condition, location, message):
    if not condition:
        raise InputContractError(f"{location}: {message}")


@cache
def _fields(record):
    return get_type_hints(record, include_extras=True)


def validate(value, annotation, location="record", substitutions=None):
    """validate exact typed fields, finite scalars and located null facts."""
    substitutions = substitutions or {}
    if isinstance(annotation, TypeVar):
        annotation = substitutions[annotation]
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, types.UnionType):
        if value is not None and type(None) in args and len(args) == 2:
            validate(
                value,
                next(option for option in args if option is not type(None)),
                location,
                substitutions,
            )
            return
        for option in args:
            try:
                validate(value, option, location, substitutions)
                return
            except InputContractError:
                pass
        raise InputContractError(f"{location}: value does not match declared union")
    if origin is Literal:
        require(
            any(type(value) is type(item) and value == item for item in args),
            location,
            "invalid literal",
        )
    elif annotation is Any:
        require(
            value is None or type(value) in (bool, int, float, str),
            location,
            "expected source scalar",
        )
        if type(value) is float:
            require(math.isfinite(value), location, "nonfinite number")
    elif annotation is type(None):
        require(value is None, location, "expected null")
    elif origin in (NotRequired,):
        validate(value, args[0], location, substitutions)
    elif origin is list:
        require(type(value) is list, location, "expected array")
        for i, item in enumerate(value):
            validate(item, args[0], f"{location}/{i}", substitutions)
    elif origin is dict:
        require(type(value) is dict, location, "expected object")
        for key, item in value.items():
            validate(key, args[0], location, substitutions)
            validate(item, args[1], f"{location}/{key}", substitutions)
    elif is_typeddict(annotation) or is_typeddict(origin):
        record = origin or annotation
        mapping = dict(substitutions)
        mapping.update(zip(getattr(record, "__parameters__", ()), args))
        for base in getattr(record, "__orig_bases__", ()):
            base_origin = get_origin(base)
            if base_origin is not None:
                mapping.update(
                    zip(getattr(base_origin, "__parameters__", ()), get_args(base))
                )
        fields = _fields(record)
        required = set(record.__required_keys__)
        require(
            type(value) is dict
            and required <= value.keys()
            and value.keys() <= fields.keys(),
            location,
            "record fields differ from closed schema",
        )
        if record is SourceFields:
            _source_fields(value, location)
            return
        for field, item in value.items():
            validate(item, fields[field], f"{location}/{field}", mapping)
        if {"values", "problems", "evidence"} <= fields.keys():
            _fact(value, location)
        _record_semantics(value, record, location)
        if record is Evidence:
            require(
                value["path"].startswith("/"),
                location,
                "source pointer must be absolute",
            )
            _input_reference(value["input_ref"], location)
        if record in (InputReference, ConsumedInput):
            _input_reference(value, location)
    else:
        require(type(value) is annotation, location, "incorrect scalar type")
        if type(value) is float:
            require(math.isfinite(value), location, "nonfinite number")


def _input_reference(value, location):
    require(
        type(value["path"]) is str and value["path"].startswith("/"),
        location,
        "input path must be absolute",
    )
    require(
        re.fullmatch("[0-9a-f]{64}", value["sha256"]) is not None,
        location,
        "invalid input digest",
    )


def _fact(record, location):
    values, problems, evidence = (
        record["values"],
        record["problems"],
        record["evidence"],
    )
    require(
        set(problems) == {key for key, value in values.items() if value is None},
        location,
        "null fields must have exactly one located problem",
    )
    for key, problem in problems.items():
        require(
            bool(problem["reason"]) and bool(problem["evidence_refs"]),
            location + "/" + key,
            "missing located reason",
        )
        require(
            len(problem["evidence_refs"]) == len(set(problem["evidence_refs"]))
            and all(0 <= i < len(evidence) for i in problem["evidence_refs"]),
            location + "/" + key,
            "broken evidence reference",
        )


def _source_fields(record, location):
    allowed = (
        set(SKATER_SOURCE_FIELDS),
        set(GOALIE_SOURCE_FIELDS),
        set(RECORDING_FIELDS),
        set(SUMMARY_RECORDING_FIELDS),
        set(BIO_SKATER_SOURCE_FIELDS),
        set(BIO_GOALIE_SOURCE_FIELDS),
        {"even_strength_saves", "power_play_saves", "shorthanded_saves"},
        set(),
        {"coaches", "scratches"},
    )
    require(set(record["values"]) in allowed, location, "unknown source-field contract")
    integer_fields = set(BIO_INTEGER_SOURCE_FIELDS) | {
        "playerId",
        "shifts",
        "goals",
        "assists",
        "sog",
        "blockedShots",
        "points",
        "plusMinus",
        "pim",
        "hits",
        "powerPlayGoals",
        "giveaways",
        "takeaways",
        "saves",
        "shotsAgainst",
        "goalsAgainst",
        "evenStrengthGoalsAgainst",
        "powerPlayGoalsAgainst",
        "shorthandedGoalsAgainst",
        "attendance",
        "even_strength_saves",
        "power_play_saves",
        "shorthanded_saves",
    }
    for key, item in record["values"].items():
        if item is None:
            continue
        if key == "officials":
            validate(item, dict[str, list[str]], location + "/" + key)
        elif key in ("coaches", "scratches"):
            validate(item, list[str], location + "/" + key)
        elif key in integer_fields:
            validate(item, int, location + "/" + key)
            require(
                key == "plusMinus" or item >= (1 if key == "playerId" else 0),
                location + "/" + key,
                "negative source count or invalid id",
            )
        elif key == "starter":
            validate(item, bool, location + "/" + key)
        elif key in ("savePctg", "faceoffWinningPctg"):
            validate(item, Number, location + "/" + key)
            require(
                0 <= item <= 1, location + "/" + key, "source fraction outside [0,1]"
            )
        else:
            validate(item, str, location + "/" + key)
    validate(record["problems"], dict[str, FieldProblem], location + "/problems")
    from .interpret import SourceEvidence

    validate(record["evidence"], list[SourceEvidence], location + "/evidence")
    _fact(record, location)
    for field in record["values"]:
        links = [
            i for i, item in enumerate(record["evidence"]) if item["field"] == field
        ]
        expected = (
            2
            if field in ("even_strength_saves", "power_play_saves", "shorthanded_saves")
            else 1
        )
        require(
            len(links) == expected,
            location + "/" + field,
            "source field requires its named evidence locators",
        )
        if field in record["problems"]:
            require(
                set(record["problems"][field]["evidence_refs"]) <= set(links),
                location + "/" + field,
                "field problem cites unrelated evidence",
            )
    require(
        all(item["field"] in record["values"] for item in record["evidence"]),
        location,
        "source locator names unknown field",
    )


def _indices(values, keys, location):
    require(
        len(values) == len(set(values))
        and all(type(i) is int and i >= 0 and i in keys for i in values),
        location,
        "duplicate or broken reference",
    )


def validate_game(value):
    validate(value, PreparedGame, "game")
    season, gid = value["season"], value["game_id"]
    require(
        re.fullmatch("[0-9]{8}", season)
        and re.fullmatch("[0-9]{10}", gid)
        and season == gid[:4] + str(int(gid[:4]) + 1),
        "game",
        "season/game identity differs",
    )
    require(
        value["game"]["inventory"]["season"] == season
        and value["game"]["inventory"]["game_id"] == gid,
        "game",
        "inventory identity differs",
    )
    identity = value["game"]["identity"]
    require(
        identity is None
        or value["game"]["ledger"]["status"] != "reconstructed"
        or all(
            identity[key] == value["game"]["inventory"][key]
            for key in (
                "game_id",
                "season",
                "game_type",
                "game_date",
                "away_team_id",
                "home_team_id",
            )
        ),
        "game",
        "identity differs",
    )
    events = {row["source"]["source_index"]: row for row in value["events"] or []}
    require(
        len(events) == len(value["events"] or []),
        "game/events",
        "duplicate source index",
    )
    segments = {row["segment_index"]: row for row in value["segments"] or []}
    chunks = {row["chunk_index"]: row for row in value["chunks"] or []}
    shifts = {row["player_shift_index"]: row for row in value["player_shifts"] or []}
    episodes = {row["episode_index"]: row for row in value["episodes"] or []}
    for rows, index_name in (
        (value["segments"], "segment_index"),
        (value["chunks"], "chunk_index"),
        (value["player_shifts"], "player_shift_index"),
        (value["episodes"], "episode_index"),
    ):
        require(
            rows is None or [row[index_name] for row in rows] == list(range(len(rows))),
            "game/" + index_name,
            "indexes must be consecutive",
        )
    issues = set(range(len(value["issues"])))
    native_intervals = value["game"]["native_intervals"] or []
    for kind in ("associations", "segments", "chunks", "player_shifts", "episodes"):
        for row in value[kind] or []:
            _indices(row["issue_indices"], issues, "game/" + kind + "/issues")
    associations = value["associations"]
    require(
        (associations is None) == (value["events"] is None)
        and {row["source_index"] for row in associations or []} == events.keys()
        and len(associations or []) == len(events),
        "game/associations",
        "must cover every event exactly once",
    )
    for row in associations or []:
        for field in ("touching_segment_indices", "matching_segment_indices"):
            _indices(row[field], segments, "game/associations/" + field)
        require(
            set(row["matching_segment_indices"])
            <= set(row["touching_segment_indices"]),
            "game/associations",
            "matching segment does not touch event",
        )
        require(
            row["native"] is None
            or row["native"]["source_index"] == row["source_index"],
            "game/associations",
            "native source link differs",
        )
    for segment in segments.values():
        require(
            0 <= segment["start_seconds"] < segment["end_seconds"],
            "game/segments",
            "invalid positive span",
        )
        _indices(
            segment["native_interval_indices"],
            set(range(len(native_intervals))),
            "game/segments/intervals",
        )
        selected = [native_intervals[i] for i in segment["native_interval_indices"]]
        require(
            bool(selected)
            and selected[0]["start_seconds"] == segment["start_seconds"]
            and selected[-1]["end_seconds"] == segment["end_seconds"]
            and all(
                row["period_number"] == segment["period_number"]
                and all(
                    row[field] == members
                    for field, members in segment["membership"].items()
                )
                for row in selected
            )
            and all(
                a["end_seconds"] == b["start_seconds"]
                for a, b in zip(selected, selected[1:])
            ),
            "game/segments",
            "native segment partition differs",
        )
        children = [
            row
            for row in chunks.values()
            if row["segment_index"] == segment["segment_index"]
        ]
        require(
            bool(children)
            and children[0]["start_seconds"] == segment["start_seconds"]
            and children[-1]["end_seconds"] == segment["end_seconds"]
            and all(
                a["end_seconds"] == b["start_seconds"]
                for a, b in zip(children, children[1:])
            ),
            "game/chunks",
            "children do not partition segment",
        )
    for chunk in chunks.values():
        require(
            chunk["segment_index"] in segments
            and 0 <= chunk["start_seconds"] < chunk["end_seconds"],
            "game/chunks",
            "invalid parent or span",
        )
        parent = segments[chunk["segment_index"]]
        members = sum((items or [] for items in parent["membership"].values()), [])
        require(
            {row["player_id"] for row in chunk["member_contexts"]} == set(members)
            and len(chunk["member_contexts"]) == len(members),
            "game/chunks",
            "member context differs",
        )
        for member in chunk["member_contexts"]:
            index = member["player_shift_index"]
            require(
                index is None
                or index in shifts
                and shifts[index]["player_id"] == member["player_id"]
                and shifts[index]["period_number"] == parent["period_number"]
                and shifts[index]["start_seconds"]
                <= chunk["start_seconds"]
                < shifts[index]["end_seconds"],
                "game/chunks",
                "shift link differs",
            )
    for event in events.values():
        for field in (
            "predecessor_source_index",
            "successor_source_index",
            "reset_source_index",
        ):
            index = event["chronology"]["values"][field]
            require(
                index is None or index in events,
                "game/events",
                "broken chronological link",
            )
        for index in (
            event["chronology"]["values"]["episode_index"],
            event["context"]["live_episode_index"],
        ):
            require(
                index is None or index in episodes, "game/events", "broken episode link"
            )
    for row in value["attempts"] or []:
        require(
            row["source_index"] in events
            and events[row["source_index"]]["source"]["type_key"]
            in ("goal", "shot-on-goal", "missed-shot", "blocked-shot"),
            "game/attempts",
            "broken source link",
        )
        for field in ("reattempt_source_index", "next_event_source_index"):
            index = row["immediate_outcomes"]["values"][field]
            require(
                index is None or index in events, "game/attempts", "broken outcome link"
            )
    require(
        len({row["source_index"] for row in value["attempts"] or []})
        == len(value["attempts"] or []),
        "game/attempts",
        "duplicate attempt",
    )
    support = value["ordinary_attempt_support"]
    reasons = support["reasons"]
    require(
        {row["segment_index"] for row in support["segments"] or []} == segments.keys()
        and len(support["segments"] or []) == len(segments),
        "game/support",
        "segment support coverage differs",
    )
    require(
        {row["source_index"] for row in support["events"] or []} == events.keys()
        and len(support["events"] or []) == len(events),
        "game/support",
        "event support coverage differs",
    )
    included = set()
    for row in support["segments"] or []:
        _indices(
            row["reason_indices"], set(range(len(reasons))), "game/support/reasons"
        )
        require(
            (row["disposition"] == "excluded") == bool(row["reason_indices"]),
            "game/support",
            "excluded support requires reasons",
        )
        actual = {
            i
            for i, reason in enumerate(reasons)
            if row["segment_index"] in reason["affected_segment_indices"]
        }
        require(
            set(row["reason_indices"]) == actual,
            "game/support",
            "saved exclusion union differs",
        )
        if row["disposition"] == "included":
            included.add(row["segment_index"])
    for row in support["events"] or []:
        _indices(
            row["reason_indices"],
            set(range(len(reasons))),
            "game/support/event/reasons",
        )
        si, ci = row["segment_index"], row["chunk_index"]
        require(
            si is None or si in segments, "game/support/event", "broken segment link"
        )
        require(
            ci is None or ci in chunks and chunks[ci]["segment_index"] == si,
            "game/support/event",
            "broken chunk link",
        )
        if row["disposition"] == "included":
            require(
                si in included and ci is not None and not row["reason_indices"],
                "game/support/event",
                "included event lacks included segment and child",
            )
    for reason in reasons:
        _indices(
            reason["affected_segment_indices"], segments, "game/support/reason/segments"
        )
        _indices(reason["event_source_indices"], events, "game/support/reason/events")
    if value["people"] is not None:
        for player, person in value["people"].items():
            require(
                re.fullmatch("[1-9][0-9]*", player)
                and int(player) == person["people"]["values"]["player_id"],
                "game/people",
                "person key differs",
            )
            require(
                all(
                    row["player_id"] == int(player)
                    for row in person["roster"] + person["boxscore"]
                ),
                "game/people",
                "roster or boxscore row belongs to a different person",
            )
            expected_sweaters = [
                dict(team_id=row["team_id"], game_id=gid, number=row["sweater_number"])
                for row in person["roster"]
                if row["team_id"] is not None and row["sweater_number"] is not None
            ]
            require(
                person["sweaters"] == expected_sweaters,
                "game/people/sweaters",
                "dated sweater observations differ from retained roster",
            )
    _validate_event_links(value, events, shifts, episodes)
    _validate_units(value, events, segments)
    from .analysis_support import validate_support

    validate_support(value)
    return value


def validate_people(value):
    validate(value, PreparedPeople, "people")
    season = value["season"]
    require(
        re.fullmatch("[0-9]{8}", season) and int(season[4:]) == int(season[:4]) + 1,
        "people",
        "invalid season identity",
    )
    reference = season[4:] + "-02-01"
    ids = [person["values"]["player_id"] for person in value["people"]]
    require(ids == sorted(set(ids)), "people", "duplicate or unordered person id")
    for person in value["people"]:
        fields = person["values"]
        require(
            fields["age_reference_date"] == reference,
            "people/age_reference_date",
            "age reference must be season-ending february 1",
        )
        days = (
            (
                date.fromisoformat(reference) - date.fromisoformat(fields["birth_date"])
            ).days
            if fields["birth_date"] is not None
            else None
        )
        expected_age = days if days is not None and days >= 0 else None
        require(
            fields["age_days"] == expected_age,
            "people/age_days",
            "age does not match supported birth date and reference",
        )
        groups = {
            "F"
            if position in ("C", "L", "R", "F")
            else position
            if position in ("D", "G")
            else None
            for position in fields["reported_positions"]
        }
        expected_group = (
            next(iter(groups)) if len(groups) == 1 and None not in groups else None
        )
        require(
            fields["position_group"] == expected_group,
            "people/position_group",
            "position group differs from retained observations",
        )
        for sweater in fields["sweaters"]:
            gid = sweater["game_id"]
            require(
                re.fullmatch("[1-9][0-9]{9}", gid)
                and gid[:4] + str(int(gid[:4]) + 1) == season
                and gid[4:6] == "02",
                "people/sweaters",
                "sweater game is outside this regular season",
            )
            require(
                sweater["team_id"] in fields["team_ids"],
                "people/sweaters",
                "sweater team is absent from dated team observations",
            )
    return value


def _validate_event_links(value, events, shifts, episodes):
    require(
        set(events) == set(range(len(events))),
        "game/events",
        "source event indexes do not cover original array",
    )
    rows = value["events"] or []
    order = [row["chronology"]["values"]["order_index"] for row in rows]
    supported = bool(rows) and all(index is not None for index in order)
    require(
        not rows or supported or all(index is None for index in order),
        "game/events",
        "partial verified event ordering",
    )
    if supported:
        require(
            order == list(range(len(rows))),
            "game/events",
            "verified order indexes differ from saved order",
        )
    positions = {
        row["source"]["source_index"]: position for position, row in enumerate(rows)
    }
    for position, row in enumerate(rows):
        chronology = row["chronology"]["values"]
        predecessor = (
            rows[position - 1]["source"]["source_index"]
            if supported and position
            else None
        )
        successor = (
            rows[position + 1]["source"]["source_index"]
            if supported and position + 1 < len(rows)
            else None
        )
        require(
            chronology["predecessor_source_index"] == predecessor
            and chronology["successor_source_index"] == successor,
            "game/events",
            "chronology links do not follow verified source order",
        )
        reset = chronology["reset_source_index"]
        require(
            reset is None
            or supported
            and positions[reset] < position
            and events[reset]["source"]["type_key"]
            in (
                "goal",
                "stoppage",
                "penalty",
                "period-start",
                "period-end",
                "game-end",
                "shootout-complete",
            ),
            "game/events",
            "reset link is not an earlier reset",
        )
    expected = {
        index
        for index, row in events.items()
        if row["source"]["type_key"]
        in ("goal", "shot-on-goal", "missed-shot", "blocked-shot")
    }
    attempts = value["attempts"]
    require(
        (attempts is None) == (value["events"] is None)
        and {row["source_index"] for row in attempts or []} == expected,
        "game/attempts",
        "recognized attempt coverage differs",
    )
    credits = value["credits"]
    require(
        credits is None
        or len({row["source_index"] for row in credits}) == len(credits)
        and all(row["source_index"] in expected for row in credits),
        "game/credits",
        "duplicate or broken credit link",
    )
    native_issues = set(range(len(value["game"]["native_issues"])))
    intervals = value["game"]["native_intervals"] or []
    for row in (value["game"]["periods"] or []) + intervals:
        _indices(row["issue_indices"], native_issues, "game/native/issue_indices")
    reports = {row["source_index"]: row for row in value["game"]["report_rows"] or []}
    require(
        len(reports) == len(value["game"]["report_rows"] or []),
        "game/report_rows",
        "duplicate report source index",
    )
    for association in value["associations"] or []:
        native = association["native"]
        if native is not None:
            _indices(
                native["issue_indices"], native_issues, "game/association/native/issues"
            )
            _indices(
                native["interval_indices"],
                set(range(len(intervals))),
                "game/association/native/intervals",
            )
            require(
                native["report_source_index"] is None
                or native["report_source_index"] in reports,
                "game/association/native",
                "broken report link",
            )
    for shift in shifts.values():
        require(
            0 <= shift["start_seconds"] < shift["end_seconds"],
            "game/player_shifts",
            "invalid positive player span",
        )
        _indices(
            shift["native_interval_indices"],
            set(range(len(intervals))),
            "game/player_shifts/intervals",
        )
        require(
            all(
                intervals[i]["period_number"] == shift["period_number"]
                and intervals[i]["start_seconds"] >= shift["start_seconds"]
                and intervals[i]["end_seconds"] <= shift["end_seconds"]
                for i in shift["native_interval_indices"]
            ),
            "game/player_shifts",
            "native participation link differs",
        )
        start = shift["start"]["values"]
        require(
            start["event_source_index"] is None
            or start["event_source_index"] in events,
            "game/player_shifts",
            "broken start event link",
        )
        require(
            start["episode_index"] is None or start["episode_index"] in episodes,
            "game/player_shifts",
            "broken start episode link",
        )
        require(
            start["kind"] != "unknown" or bool(shift["issue_indices"]),
            "game/player_shifts",
            "unknown start requires a located issue",
        )
    for episode in episodes.values():
        require(
            episode["start_source_index"] in events
            and (
                episode["end_source_index"] is None
                or episode["end_source_index"] in events
            ),
            "game/episodes",
            "broken source link",
        )
        require(
            episode["end_seconds"] is None
            or episode["end_seconds"] >= episode["start_seconds"],
            "game/episodes",
            "invalid episode span",
        )
        require(
            episode["left_censored"] == (episode["start_kind"] == "first_live_action"),
            "game/episodes",
            "episode censoring differs from anchor",
        )


def _validate_units(value, events, segments):
    from .analysis_context import unit_workload, _unit_ages

    for chunk in value["chunks"] or []:
        membership = segments[chunk["segment_index"]]["membership"]
        prefixes = {
            str(row["player_id"]): row["elapsed_prefix"]
            for row in chunk["member_contexts"]
        }
        for side in ("away", "home"):
            saved = chunk[side + "_unit"]
            expected = unit_workload(
                membership[side + "_skaters"], prefixes, saved["evidence"]
            )
            require(
                saved["values"] == expected["values"],
                "game/chunks/" + side + "_unit",
                "actual-unit workload accounting differs",
            )
    associations = {
        row["source_index"]: row["native"] for row in value["associations"] or []
    }
    game = value["game"]["inventory"]
    for attempt in value["attempts"] or []:
        event = events[attempt["source_index"]]
        facts = attempt["feature_facts"]
        prefixes = facts["current_workload"]["values"]["players"]
        require(
            prefixes == event["context"]["prefix_by_player"],
            "game/attempts/current_workload",
            "event prefix composition differs",
        )
        team = event["source"]["shooting_team_id"]
        side = (
            "away"
            if team == game["away_team_id"]
            else "home"
            if team == game["home_team_id"]
            else None
        )
        opposing = "away" if side == "home" else "home" if side == "away" else None
        native = associations[attempt["source_index"]]
        members = (
            native[opposing + "_skaters"] if native is not None and opposing else None
        )
        saved = facts["current_workload"]["values"]["opposing_unit"]
        require(
            saved["values"]
            == unit_workload(members, prefixes, saved["evidence"])["values"],
            "game/attempts/current_workload",
            "actual opposing-unit workload accounting differs",
        )
        deployment = facts["deployment"]["values"]
        for field, member_side in (
            ("attacking_unit", side),
            ("opposing_unit", opposing),
        ):
            members = (
                native[member_side + "_skaters"]
                if native is not None and member_side
                else None
            )
            saved = deployment[field]
            expected = _unit_ages(members, deployment["players"], saved["evidence"])
            require(
                saved["values"] == expected["values"],
                "game/attempts/deployment/" + field,
                "actual-unit shift-age accounting differs",
            )


# these are named record contracts, not a policy inferred from arbitrary keys.
_NONNEGATIVE = {
    ScoreCounts: ("away", "home"),
    PrefixValues: tuple(PrefixValues.__annotations__),
    TransitionValues: ("return_seconds", "age_seconds"),
    UnitValues: (
        "member_count",
        "known_count",
        "known_toi_all_sum_seconds",
        "toi_all_mean_seconds",
        "toi_all_max_seconds",
    ),
    AgeUnit: tuple(AgeUnit.__annotations__),
    ScalarValue: ("value",),
    Event: (
        "source_index",
        "event_id",
        "sort_order",
        "type_code",
        "period_number",
        "elapsed_seconds",
        "penalty_duration_minutes",
        "away_score",
        "home_score",
    ),
    RosterRecord: ("source_index", "sweater_number"),
    BoxscorePlayer: (
        "toi_seconds",
        "shift_count",
        "goals",
        "assists",
        "sog",
        "blocked_shots",
    ),
    Result: ("away_score", "home_score", "away_sog", "home_sog"),
    InventoryGame: (
        "source_index",
        "game_type",
        "reported_game_state",
        "reported_schedule_state",
    ),
    Game: ("game_type",),
    Period: ("period_number", "end_seconds", "end_event_source_index"),
    Interval: ("period_number", "start_seconds", "end_seconds"),
    ReconstructedEvent: ("source_index", "report_source_index"),
    ChronologyValues: tuple(ChronologyValues.__annotations__),
    Association: ("source_index",),
    Segment: ("segment_index", "period_number", "start_seconds", "end_seconds"),
    Chunk: ("chunk_index", "segment_index", "start_seconds", "end_seconds"),
    MemberContext: ("player_shift_index",),
    StartValues: ("event_source_index", "episode_index", "rest_seconds"),
    PlayerShift: (
        "player_shift_index",
        "period_number",
        "start_seconds",
        "end_seconds",
    ),
    Episode: (
        "episode_index",
        "period_number",
        "start_seconds",
        "end_seconds",
        "start_source_index",
        "end_source_index",
    ),
    Attempt: ("source_index",),
    ImmediateValues: (
        "reattempt_source_index",
        "next_event_source_index",
        "next_event_delay_seconds",
    ),
    RecordedGeometry: (),
    AttemptGeometry: ("distance_ft", "absolute_angle_rad", "displacement_ft"),
    StateValues: (
        "away_score",
        "home_score",
        "period_number",
        "elapsed_seconds",
        "remaining_seconds",
        "nominal_length_seconds",
        "game_seconds",
        "away_skater_count",
        "home_skater_count",
        "away_goalie_count",
        "home_goalie_count",
    ),
    PrecedingValues: ("source_index", "event_id", "time_gap_seconds"),
    SequenceValues: (
        "defender_sequence_index",
        "defender_sequence_age_seconds",
        "prior_zone_run_count",
        "prior_zone_run_start_seconds",
        "prior_zone_run_age_seconds",
    ),
    ActionValues: tuple(ActionValues.__annotations__),
    DeploymentPlayer: (
        "shift_source_index",
        "start_seconds",
        "end_seconds",
        "age_seconds",
        "previous_shift_gap_seconds",
    ),
    DeploymentValues: (
        "last_faceoff_source_index",
        "last_faceoff_age_seconds",
        "strength_transition_age_seconds",
        "penalty_source_index",
        "penalty_duration_minutes",
        "penalty_age_seconds",
        "interval_substitution_count",
        "endpoint_change_count",
    ),
    OutcomeValues: (
        "next_event_source_index",
        "next_event_id",
        "next_event_delay_seconds",
        "next_stoppage_source_index",
        "next_stoppage_event_id",
        "next_stoppage_delay_seconds",
        "next_same_team_attempt_source_index",
        "goalie_stoppage_delay_seconds",
    ),
    PersonValues: ("age_days",),
    BoundBio: ("source_index",),
    CounterValues: tuple(CounterValues.__annotations__),
    RestValues: ("calendar_gap_days", "games_days_7", "games_days_14"),
    HistoryIdentity: ("team_changes", "role_changes"),
    Sweater: ("number",),
    SeasonPersonValues: ("age_days", "height_cm"),
    Credit: ("source_index",),
    SegmentSupport: ("segment_index",),
    EventSupport: ("source_index", "segment_index", "chunk_index"),
    ReportSupport: ("report_source_index",),
    SupportReason: ("period_number",),
    CompletenessCount: tuple(CompletenessCount.__annotations__),
    StatusCounts: tuple(StatusCounts.__annotations__),
    SourceCoverage: ("available_games", "unavailable_games"),
    EventCoverage: ("count",),
    TimeCoverage: tuple(TimeCoverage.__annotations__),
    SeasonCoverage: (
        "inventory_games",
        "selected_games",
        "report_only_attempts",
        "unknown_horizon_games",
        "unresolved_known_seconds",
    ),
    ManifestSeason: ("inventory_games",),
    Resources: tuple(Resources.__annotations__),
}
_IDS = {
    Game: ("away_team_id", "home_team_id"),
    InventoryGame: ("away_team_id", "home_team_id"),
    Event: ("owner_team_id", "shooting_team_id"),
    RosterRecord: ("player_id", "team_id"),
    BoxscorePlayer: ("player_id", "team_id"),
    PersonValues: ("player_id", "team_id"),
    BoundBio: ("player_id",),
    PlayerShift: ("player_id", "team_id"),
    MemberContext: ("player_id",),
    DetailsValues: (
        "credited_shooter_id",
        "physical_shooter_id",
        "shooting_team_id",
        "opposing_goalie_id",
    ),
    StateValues: ("shooting_team_id", "opponent_team_id"),
    PrecedingValues: ("owner_team_id", "shooting_team_id"),
    DeploymentValues: ("penalty_team_id",),
    OutcomeValues: ("blocker_id",),
    TeamRole: ("team_id",),
    Sweater: ("team_id",),
    SeasonPersonValues: ("player_id",),
    Credit: ("scorer_or_shooter_id", "primary_assister_id"),
}
_DATE_FIELDS = {
    Game: ("game_date",),
    InventoryGame: ("game_date",),
    BoundBio: ("birth_date",),
    PersonValues: ("birth_date",),
    SeasonPersonValues: ("birth_date", "age_reference_date"),
    Window: ("start", "cutoff"),
    RestValues: ("prior_game_date",),
    FirstAppearance: ("game_date",),
    TeamRole: ("game_date",),
}


def _record_semantics(value, record, location):
    for field in _NONNEGATIVE.get(record, ()):
        item = value[field]
        require(
            item is None or item >= 0,
            location + "/" + field,
            "negative counter, index or time",
        )
    for field in _IDS.get(record, ()):
        item = value[field]
        require(item is None or item > 0, location + "/" + field, "id must be positive")
    for field in _DATE_FIELDS.get(record, ()):
        item = value[field]
        if item is not None:
            try:
                valid = date.fromisoformat(item).isoformat() == item
            except (ValueError, TypeError):
                valid = False
            require(valid, location + "/" + field, "expected canonical calendar date")
    for field in (
        "native_interval_indices",
        "native_shift_indices",
        "interval_indices",
        "shift_source_indices",
        "issue_indices",
        "reason_indices",
        "event_source_indices",
        "report_source_indices",
        "affected_segment_indices",
        "touching_segment_indices",
        "matching_segment_indices",
        "intervening_source_indices",
    ):
        if field in value and value[field] is not None:
            items = value[field]
            require(
                len(items) == len(set(items))
                and all(type(item) is int and item >= 0 for item in items),
                location + "/" + field,
                "duplicate or negative index",
            )
    if record in (Membership, Interval, ReconstructedEvent):
        all_members = []
        for field in Membership.__annotations__:
            items = value[field]
            require(
                items is None
                or len(items) == len(set(items))
                and all(item > 0 for item in items),
                location + "/" + field,
                "duplicate or invalid member id",
            )
            all_members.extend(items or [])
        require(
            len(all_members) == len(set(all_members)),
            location,
            "member occurs on multiple sides or roles",
        )
    if record is SourceEvidence:
        require(
            value["input_index"] >= 0 and value["path"].startswith("/"),
            location,
            "invalid source locator",
        )
    if record is LocatedIssue:
        require(
            bool(value["evidence"])
            and bool(value["message"])
            and value["path"].startswith("/"),
            location,
            "issue needs a located evidence reference",
        )
    if record is FieldProblem:
        require(
            bool(value["reason"])
            and len(value["evidence_refs"]) == len(set(value["evidence_refs"]))
            and all(i >= 0 for i in value["evidence_refs"]),
            location,
            "invalid located problem",
        )
    if record is Input:
        from .captures import SOURCES, REFERENCE_SOURCES

        require(
            value["source"] in (*SOURCES, *REFERENCE_SOURCES)
            and value["capture_path"].startswith("/"),
            location,
            "invalid source input",
        )
        require(
            value["http_status"] is None or 100 <= value["http_status"] <= 599,
            location,
            "invalid http status",
        )
        require(
            value["body_sha256"] is None
            or re.fullmatch("[0-9a-f]{64}", value["body_sha256"]),
            location,
            "invalid body digest",
        )
        require(
            value["status"] == "unavailable" or value["body_sha256"] is not None,
            location,
            "available input lacks body identity",
        )
    if record is CreditEvidence:
        require(
            value["capture_path"].startswith("/")
            and value["field"].startswith("/")
            and (
                value["body_sha256"] is None
                or re.fullmatch("[0-9a-f]{64}", value["body_sha256"])
            ),
            location,
            "invalid credit locator",
        )
    if record in (EventContext, WorkloadValues, DeploymentValues):
        fields = ("prefix_by_player",) if record is EventContext else ("players",)
        for field in fields:
            require(
                all(re.fullmatch("[1-9][0-9]*", key) for key in value[field]),
                location + "/" + field,
                "player keys must be decimal positive ids",
            )
    if record is Event:
        from .interpret import _ROLES

        require(
            value["roles"].keys() <= (_ROLES.keys() | {"turnover_player"})
            and all(item is None or item > 0 for item in value["roles"].values()),
            location + "/roles",
            "unknown role or invalid player id",
        )
    if record in (Game, InventoryGame):
        gid, season = value["game_id"], value["season"]
        require(
            re.fullmatch("[0-9]{8}", season)
            and re.fullmatch("[1-9][0-9]{9}", gid)
            and season == gid[:4] + str(int(gid[:4]) + 1)
            and value["game_type"] == 2
            and gid[4:6] == "02",
            location,
            "invalid regular-season identity",
        )
        require(
            value["away_team_id"] != value["home_team_id"],
            location,
            "teams must differ",
        )
    if record is GameEvidence:
        from .captures import SOURCES

        sources = [item["source"] for item in value["inputs"]]
        require(
            len(sources) == len(set(sources)) and set(sources) <= set(SOURCES),
            location + "/inputs",
            "duplicate or unknown game source",
        )
        require(
            value["ledger"]["status"] != "reconstructed"
            or set(sources) == set(SOURCES),
            location + "/inputs",
            "reconstructed game must retain every native source disposition",
        )
        for item in value["recording_observations"]:
            expected = (
                SUMMARY_RECORDING_FIELDS
                if item["source"] == "game-summary"
                else RECORDING_FIELDS
            )
            require(
                set(item["source_fields"]["values"]) == set(expected),
                location + "/recording_observations",
                "recording collection contains a different source-field contract",
            )
    if record is GamePerson:
        fields = value["people"]["values"]
        unresolved_join = (
            len(value["roster"]) > 1
            or len(value["boxscore"]) > 1
            or fields["team_id"] is None
        )
        require(
            ("identity_observations" in fields) == unresolved_join,
            location + "/people/values",
            "identity observations must occur exactly for an unresolved roster/boxscore join",
        )
        if unresolved_join:
            require(
                fields["identity_observations"]
                == {"roster": value["roster"], "boxscore": value["boxscore"]},
                location + "/people/values/identity_observations",
                "identity observations differ from retained roster/boxscore evidence",
            )
    if record is BoxscorePlayer:
        expected = (
            GOALIE_SOURCE_FIELDS
            if "/goalies/" in value["source_path"]
            else SKATER_SOURCE_FIELDS
        )
        require(
            set(value["source_fields"]["values"]) == set(expected),
            location,
            "boxscore source-field contract differs",
        )
        derived = (
            {"even_strength_saves", "power_play_saves", "shorthanded_saves"}
            if "/goalies/" in value["source_path"]
            else set()
        )
        require(
            set(value["derived_fields"]["values"]) == derived,
            location,
            "derived boxscore field contract differs",
        )
    if record is BoundBio:
        expected = (
            BIO_GOALIE_SOURCE_FIELDS
            if value["source"] == "goalie-bios"
            else BIO_SKATER_SOURCE_FIELDS
        )
        require(
            value["source"] in ("skater-bios", "goalie-bios")
            and set(value["source_fields"]["values"]) == set(expected),
            location,
            "bio source-field contract differs",
        )
    if record is SourceObservation:
        expected = (
            SUMMARY_RECORDING_FIELDS
            if value["source"] == "game-summary"
            else RECORDING_FIELDS
        )
        require(
            value["source"] in ("play-by-play", "boxscore", "landing", "game-summary")
            and (
                set(value["source_fields"]["values"]) == set(expected)
                or set(value["source_fields"]["values"]) == {"coaches", "scratches"}
            ),
            location,
            "recording source-field contract differs",
        )
    if record is GeometryValues:
        if value["location_kind"] == "unavailable":
            require(
                value["x_ft"] is None
                and value["y_ft"] is None
                and value["frame"] is None,
                location,
                "unavailable geometry carries located values",
            )
        else:
            from .shot_origins import in_rink

            require(
                value["frame"] == "home_attack"
                and in_rink(value["x_ft"], value["y_ft"]),
                location,
                "located event has invalid frame or rink position",
            )
    if record in (UnitValues, AgeUnit):
        count, known = value["member_count"], value["known_count"]
        require(
            count is None
            and known is None
            or count is not None
            and known is not None
            and known <= count,
            location,
            "known unit count exceeds membership",
        )
    if record is SeasonPersonValues:
        require(
            value["team_ids"] == sorted(set(value["team_ids"]))
            and all(item > 0 for item in value["team_ids"])
            and value["reported_positions"] == sorted(set(value["reported_positions"])),
            location,
            "season observations must be unique sorted values",
        )
    if record is Implementation:
        for field in ("source_code_sha256", "preparation_policy_sha256"):
            require(
                re.fullmatch("[0-9a-f]{64}", value[field]),
                location,
                "invalid implementation digest",
            )
        require(
            value["git_commit"] is None
            or re.fullmatch("[0-9a-f]{40}", value["git_commit"]),
            location,
            "invalid git identity",
        )
        require(bool(value["python_version"]), location, "missing runtime identity")
