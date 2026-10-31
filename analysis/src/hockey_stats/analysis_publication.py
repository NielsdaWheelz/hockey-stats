"""fixed player-analysis exchange and sqlite storage; no source or fit interpretation."""

from dataclasses import dataclass
from contextlib import ExitStack
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re

from .artifacts import digest, implementation_identity, require, write_json
from .captures import strict_json


SEASONS = ("20232024", "20242025", "20252026")
EXECUTION_STRENGTHS = ("5v5", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4")
SPATIAL_STRENGTHS = (*EXECUTION_STRENGTHS, "pp", "pk")
GOALIE_STRENGTHS = ("5v5", "4v4", "3v3", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4", "ev", "pk")
CONTEXT_POPULATIONS = ("recorded_all_attempts", "recorded_goals", "recorded_locatable_unblocked", "neutral_locatable_unblocked_value", "neutral_all_attempt_value")
FAMILY_TABLES = {
    "descriptive": ("skater_descriptive", "skater_context"),
    "microstats": ("skater_microstats",),
    "spatial": ("skater_spatial", "analysis_map", "adjustment_decomposition"),
    "execution": ("skater_execution", "analysis_map", "execution_breakdown", "attempt_value", "attempt_setter", "attempt_execution_share"),
    "shootiness": ("skater_shootiness",),
    "penalties": ("skater_penalties",),
    "territory": ("skater_territory", "analysis_map"),
    "goalie": ("goalie_result", "goalie_observed", "goalie_evidence_map", "goalie_danger", "analysis_map", "execution_breakdown"),
    "ledger": ("value_ledger",),
    "evidence": ("attempt_fact", "dressed_game", "interval_fact", "interval_player", "interval_location", "context_coverage"),
}
KEYS = {
    "people": ("season", "player_id"), "sources": ("source_id",), "methods": ("method_id",), "supports": ("support_id",),
    "skater_descriptive": ("season", "player_id"), "skater_context": ("season", "player_id"), "skater_microstats": ("season", "player_id"),
    "skater_spatial": ("season", "player_id", "strength"), "skater_execution": ("season", "player_id", "strength"),
    "skater_shootiness": ("season", "player_id", "strength"), "skater_penalties": ("season", "player_id"), "skater_territory": ("season", "player_id"),
    "goalie_result": ("season", "player_id", "strength"), "goalie_observed": ("season", "player_id", "strength"),
    "goalie_evidence_map": ("season", "player_id", "strength", "population", "type"), "goalie_danger": ("season", "player_id", "strength", "population"),
    "value_ledger": ("season", "player_id"), "analysis_map": ("season", "player_id", "map_kind", "strength", "view"),
    "execution_breakdown": ("season", "player_id", "strength", "kind", "stratum"),
    "adjustment_decomposition": ("season", "player_id", "strength", "target"),
    "attempt_fact": ("season", "game_id", "source_index"), "attempt_value": ("season", "game_id", "source_index"),
    "attempt_setter": ("season", "game_id", "source_index", "candidate_id"),
    "attempt_execution_share": ("season", "game_id", "source_index", "group", "recipient_id"),
    "dressed_game": ("season", "player_id", "game_id"),
    "interval_fact": ("season", "game_id", "interval_id", "team_id", "population"),
    "interval_player": ("season", "game_id", "interval_id", "team_id", "player_id"),
    "interval_location": ("season", "game_id", "interval_id", "team_id", "population", "cell_id"),
    "context_coverage": ("season", "player_id", "population"),
}
FACT_TABLES = {"attempt_fact", "attempt_value", "attempt_setter", "attempt_execution_share", "dressed_game", "interval_fact", "interval_player", "interval_location", "context_coverage"}
ESTIMATE_FIELDS = {
    "skater_spatial": tuple(f"{role}_{quantity}_per60{suffix}" for role in ("offense", "defense") for quantity in ("attempts", "xg") for suffix in ("", "_complete", "_neutral")) + tuple(f"{role}_{quantity}_relative_percent" for role in ("offense", "defense") for quantity in ("attempts", "xg")),
    "skater_execution": ("finishing_goals_per100_attempts", "setting_goals_per100_assisted_opportunities", "avoid_block_probability", "on_net_probability", "recorded_stop_probability", "conversion_probability", "avoid_block_probability_difference", "on_net_probability_difference", "recorded_stop_probability_difference", "conversion_probability_difference"),
    "skater_shootiness": ("probability", "neutral_probability", "difference"),
    "skater_penalties": ("drawn_per60", "taken_per60", "drawn_value_per60", "taken_value_per60"),
    "goalie_result": ("stopping_goals_per100_on_net", "miss_probability", "recorded_stop_probability", "conversion_probability", "recorded_reattempt_probability", "reattempt_neutral_goal_probability", "followup_danger", "miss_probability_difference", "recorded_stop_probability_difference", "conversion_probability_difference", "recorded_reattempt_probability_difference", "reattempt_neutral_goal_probability_difference", "followup_danger_difference"),
    "attempt_value": ("actor_all_attempt_opportunity", "neutral_all_attempt_opportunity", "actor_unblocked_goal_probability", "actor_on_net_goal_probability", "neutral_goalie_on_net_goal_probability"),
}
LEDGER_COMPONENTS = ("five_on_five_offense", "five_on_five_defense", "power_play_offense", "penalty_kill_defense", "finishing", "setting", "penalties_drawn", "penalties_taken", "ice_won", "ice_lost")
MICROSTATS = ("goals_per60", "primary_assists_per60", "unblocked_attempts_per60", "hits_per60", "reference_xg_per60", "blocked_attempt_share", "primary_pass_xg_per60", "primary_shot_assists_per60", "in_zone_attempts_per60", "rush_attempts_per60", "high_danger_pass_attempts_per60", "in_zone_shot_assists_per60", "rush_shot_assists_per60", "high_danger_passes_per60", "zone_entries_per60", "possession_entries_per60", "zone_exits_per60", "possession_exits_per60", "forecheck_involvements_per60", "defensive_zone_touches_per60", "pass_exits_per60", "carry_exits_per60", "defensive_zone_retrievals_per60", "successful_retrievals_per60", "shot_assisting_passes_per60", "puck_management_xga_saved_per100_plays", "entry_denial_fraction", "possession_entry_denial_fraction", "skating_max_speed_mph", "skating_bursts_over20_count")
CONSTRUCTIONS = ("recorded", "reconstructed", "inferred", "model_valued", "modeled", "source_modeled")

QUANTITY_PATHS = frozenset((
    'skater_spatial.offense_attempts_per60',
    'skater_spatial.defense_attempts_per60',
    'skater_spatial.offense_xg_per60',
    'skater_spatial.defense_xg_per60',
    'skater_spatial.offense_attempts_per60_complete',
    'skater_spatial.defense_attempts_per60_complete',
    'skater_spatial.offense_xg_per60_complete',
    'skater_spatial.defense_xg_per60_complete',
    'skater_spatial.offense_attempts_per60_neutral',
    'skater_spatial.defense_attempts_per60_neutral',
    'skater_spatial.offense_xg_per60_neutral',
    'skater_spatial.defense_xg_per60_neutral',
    'skater_spatial.offense_attempts_relative_percent',
    'skater_spatial.defense_attempts_relative_percent',
    'skater_spatial.offense_xg_relative_percent',
    'skater_spatial.defense_xg_relative_percent',
    'skater_execution.finishing_goals_per100_attempts',
    'skater_execution.setting_goals_per100_assisted_opportunities',
    'skater_execution.avoid_block_probability',
    'skater_execution.on_net_probability',
    'skater_execution.recorded_stop_probability',
    'skater_execution.conversion_probability',
    'skater_execution.avoid_block_probability_difference',
    'skater_execution.on_net_probability_difference',
    'skater_execution.recorded_stop_probability_difference',
    'skater_execution.conversion_probability_difference',
    'skater_shootiness.probability',
    'skater_shootiness.neutral_probability',
    'skater_shootiness.difference',
    'skater_penalties.drawn_per60',
    'skater_penalties.taken_per60',
    'skater_penalties.drawn_value_per60',
    'skater_penalties.taken_value_per60',
    'skater_territory.ice_won_goals_per_basket',
    'skater_territory.ice_lost_goals_per_basket',
    'skater_territory.exit_offense.hazard_per_second',
    'skater_territory.exit_offense.one_second_probability',
    'skater_territory.entry_offense.hazard_per_second',
    'skater_territory.entry_offense.one_second_probability',
    'skater_territory.zone_retention.opponent_exit_hazard_per_second',
    'skater_territory.zone_retention.one_second_probability',
    'skater_territory.entry_prevention.opponent_entry_hazard_per_second',
    'skater_territory.entry_prevention.one_second_probability',
    'goalie_result.stopping_goals_per100_on_net',
    'goalie_result.miss_probability',
    'goalie_result.recorded_stop_probability',
    'goalie_result.conversion_probability',
    'goalie_result.recorded_reattempt_probability',
    'goalie_result.reattempt_neutral_goal_probability',
    'goalie_result.followup_danger',
    'goalie_result.miss_probability_difference',
    'goalie_result.recorded_stop_probability_difference',
    'goalie_result.conversion_probability_difference',
    'goalie_result.recorded_reattempt_probability_difference',
    'goalie_result.reattempt_neutral_goal_probability_difference',
    'goalie_result.followup_danger_difference',
    'goalie_observed.on_net_evidence.expected_goals',
    'goalie_observed.on_net_evidence.goals_saved_above_expected',
    'goalie_observed.on_net_evidence.goals_per100_expected',
    'goalie_observed.on_net_evidence.mean_goal_probability',
    'goalie_observed.on_net_evidence.league_mean_goal_probability',
    'goalie_observed.on_net_evidence.difficulty_relative_percent',
    'goalie_observed.on_net_evidence.expected_save_fraction',
    'goalie_observed.unblocked_evidence.expected_goals',
    'goalie_observed.unblocked_evidence.goals_saved_above_expected',
    'goalie_observed.unblocked_evidence.goals_per100_expected',
    'goalie_observed.unblocked_evidence.mean_goal_probability',
    'goalie_observed.unblocked_evidence.league_mean_goal_probability',
    'goalie_observed.unblocked_evidence.difficulty_relative_percent',
    'goalie_observed.stage_evidence.miss',
    'goalie_observed.stage_evidence.recorded_stop',
    'goalie_observed.stage_evidence.conversion',
    'goalie_observed.stage_evidence.reattempt',
    'goalie_observed.stage_evidence.next_attempt_danger',
    'analysis_map.integrated_value',
    'analysis_map.cells',
    'analysis_map.display_cells.mass',
    'analysis_map.display_cells.density_per100sqft',
    'execution_breakdown.probability',
    'execution_breakdown.effect',
    'execution_breakdown.expected_successes',
    'execution_breakdown.reference.expected_goals',
    'execution_breakdown.reference.mean_opportunity',
    'execution_breakdown.reference.observed_minus_expected_goals',
    'execution_breakdown.actor.expected_goals',
    'execution_breakdown.actor.mean_opportunity',
    'execution_breakdown.actor.observed_minus_expected_goals',
    'adjustment_decomposition.baseline',
    'adjustment_decomposition.self',
    'adjustment_decomposition.teammates',
    'adjustment_decomposition.opponents',
    'adjustment_decomposition.coaching_other_context',
    'adjustment_decomposition.numerical_residual',
    'adjustment_decomposition.factual_prediction',
    'goalie_evidence_map.totals.expected_goals',
    'goalie_evidence_map.native_cells.expected_goals',
    'goalie_evidence_map.unmapped.expected_goals',
    'goalie_evidence_map.display_cells.mass_saved',
    'goalie_evidence_map.display_cells.ratio',
    'goalie_danger.expected_goal_mass',
    'goalie_danger.totals.expected_goals',
    'attempt_value.actor_all_attempt_opportunity',
    'attempt_value.neutral_all_attempt_opportunity',
    'attempt_value.actor_unblocked_goal_probability',
    'attempt_value.actor_on_net_goal_probability',
    'attempt_value.neutral_goalie_on_net_goal_probability',
    'skater_microstats.reference_xg_per60',
    'skater_microstats.primary_pass_xg_per60',
    'skater_microstats.puck_management_xga_saved_per100_plays',
    'value_ledger.league_total',
    'value_ledger.replacement_total',
    'value_ledger.penalties_combined.league_goals',
    'value_ledger.penalties_combined.replacement_goals',
    'value_ledger.components.five_on_five_offense.league_goals',
    'value_ledger.components.five_on_five_offense.replacement_goals',
    'value_ledger.components.five_on_five_defense.league_goals',
    'value_ledger.components.five_on_five_defense.replacement_goals',
    'value_ledger.components.power_play_offense.league_goals',
    'value_ledger.components.power_play_offense.replacement_goals',
    'value_ledger.components.penalty_kill_defense.league_goals',
    'value_ledger.components.penalty_kill_defense.replacement_goals',
    'value_ledger.components.finishing.league_goals',
    'value_ledger.components.finishing.replacement_goals',
    'value_ledger.components.setting.league_goals',
    'value_ledger.components.setting.replacement_goals',
    'value_ledger.components.penalties_drawn.league_goals',
    'value_ledger.components.penalties_drawn.replacement_goals',
    'value_ledger.components.penalties_taken.league_goals',
    'value_ledger.components.penalties_taken.replacement_goals',
    'value_ledger.components.ice_won.league_goals',
    'value_ledger.components.ice_won.replacement_goals',
    'value_ledger.components.ice_lost.league_goals',
    'value_ledger.components.ice_lost.replacement_goals',
))

SUPPORT_REASON_CODES = frozenset((
    "required_source_unavailable", "count_accounting_conflict", "event_evidence_unresolved", "unpaired_report_attempt", "elapsed_membership_unresolved", "period_horizon_unavailable", "player_toi_conflict", "roster_identity_unresolved", "unassigned_player_games", "event_exposure_conflict", "shift_source_empty", "no_5v5_exposure", "no_personal_5v5_exposure", "personal_credit_unresolved", "spatial_coordinates_missing", "spatial_frame_unresolved", "spatial_location_outside_rink", "no_spatial_5v5_exposure",
    "reported_shifts_unavailable", "source_unavailable", "membership_unavailable", "identity_conflict", "strength_conflict", "ambiguous_assignment", "unmatched_report_attempt", "clock_unavailable", "horizon_unavailable", "not_computed", "not_applicable", "no_exposure", "missing_source", "failed_fit", "type_unavailable", "context_unavailable", "elapsed_unavailable", "value_unavailable",
))


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), f"expected exact fields {','.join(names)}")


def text(value):
    require(type(value) is str and bool(value.strip()), "expected nonempty text")


def number(value, *, minimum=None, maximum=None, integer=False, nullable=False):
    if nullable and value is None:
        return
    require(type(value) is int if integer else type(value) in (int, float), "expected numeric value")
    require(abs(value) <= (9007199254740991 if integer else 1.7976931348623157e308), "number exceeds its representable domain")
    require(math.isfinite(value)
            and (minimum is None or value >= minimum) and (maximum is None or value <= maximum), "number outside declared domain")


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[1-9][0-9]*", value) is not None and int(value) <= 9007199254740991, "invalid canonical decimal id")


def season(value):
    require(type(value) is str and re.fullmatch(r"[1-9][0-9]{7}", value) is not None and int(value[4:]) == int(value[:4]) + 1, "invalid season")


def iso_date(value):
    require(type(value) is str and date.fromisoformat(value).isoformat() == value, "invalid iso date")


def strings(value, *, ordered=False):
    require(type(value) is list, "expected array")
    for item in value:
        text(item)
    require(len(value) == len(set(value)) and (not ordered or value == sorted(value)), "duplicate or unordered strings")


def close(left, right):
    return math.isfinite(left) and math.isfinite(right) and abs(left-right) <= 1e-9 + 1e-9 * max(abs(left), abs(right))


def reference(value, catalogs):
    fields(value, ("kind", "id"))
    require(value["kind"] in ("source", "method"), "invalid reference kind")
    text(value["id"])
    require(value["id"] in catalogs[value["kind"]], "dangling reference")


def estimate(value, catalogs, *, probability=False, nonnegative=False):
    fields(value, ("value", "unavailable_reason", "reason_detail", "uncertainty"))
    uncertainty = value["uncertainty"]
    require(type(uncertainty) is dict, "invalid uncertainty")
    if uncertainty.get("kind") == "not_estimated":
        fields(uncertainty, ("kind",))
    else:
        fields(uncertainty, ("kind", "lower", "upper", "level", "method", "conditional_on"))
        require(uncertainty["kind"] == "interval", "invalid uncertainty kind")
        for key in ("lower", "upper", "level"):
            number(uncertainty[key])
        require(0 < uncertainty["level"] < 1 and uncertainty["lower"] <= uncertainty["upper"], "invalid interval")
        text(uncertainty["method"])
        require(type(uncertainty["conditional_on"]) is list and uncertainty["conditional_on"], "missing conditional assumptions")
        for assumption in uncertainty["conditional_on"]:
            text(assumption)
    if value["value"] is not None:
        number(value["value"], minimum=0 if probability or nonnegative else None, maximum=1 if probability else None)
        require(value["unavailable_reason"] is None and value["reason_detail"] is None, "available estimate has unavailable reason")
    else:
        reason = value["unavailable_reason"]
        require(reason in ("not_applicable", "no_exposure", "missing_source", "failed_fit", "not_computed") and uncertainty["kind"] == "not_estimated", "invalid unavailable estimate")
        detail = value["reason_detail"]
        fields(detail, ("explanation", "evidence"))
        text(detail["explanation"])
        require(type(detail["evidence"]) is list and (detail["evidence"] or reason in ("not_computed", "not_applicable", "no_exposure")), "missing unavailable evidence")
        for item in detail["evidence"]:
            reference(item, catalogs)
        require(reason != 'missing_source' or any(item['kind'] == 'source' for item in detail['evidence']), 'missing-source reason lacks source evidence')
        require(reason != 'failed_fit' or any(item['kind'] == 'method' for item in detail['evidence']), 'failed-fit reason lacks method evidence')


def reason_counts(value):
    require(type(value) is list, "expected reason counts")
    codes = []
    for row in value:
        fields(row, ("code", "count"))
        require(row["code"] in SUPPORT_REASON_CODES, "unknown support reason")
        number(row["count"], minimum=1, integer=True)
        codes.append(row["code"])
    require(codes == sorted(set(codes)), "duplicate or unordered reasons")


def support(value):
    fields(value, ("included_seconds", "events", "eligible_weight", "known_excluded_seconds", "unquantified_gap", "reason_counts", "inferred_inputs", "current_season_information", "prior_only", "prior_seasons"))
    for key in ("included_seconds", "events", "eligible_weight", "known_excluded_seconds"):
        number(value[key], minimum=0, integer=key == "events", nullable=True)
    for key in ("unquantified_gap", "current_season_information", "prior_only"):
        require(type(value[key]) is bool, "expected support boolean")
    reason_counts(value["reason_counts"])
    strings(value["inferred_inputs"], ordered=True)
    require(set(value["inferred_inputs"]) <= {"blocked_origin", "setter", "territory", "historical_borrowing"}, "invalid inferred input")
    strings(value["prior_seasons"], ordered=True)
    for item in value["prior_seasons"]:
        season(item)
    require(not value["prior_only"] or not value["current_season_information"], "prior-only support claims current information")


def fact_value(value, catalogs, *, unit=None, denominator_kind=None):
    fields(value, ("value", "unavailable_reason", "reason_detail", "uncertainty", "support", "unit", "numerator", "denominator", "denominator_kind", "construction", "provenance"))
    estimate({key: value[key] for key in ("value", "unavailable_reason", "reason_detail", "uncertainty")}, catalogs)
    support(value["support"])
    text(value["unit"])
    text(value["denominator_kind"])
    require(unit is None or value["unit"] == unit, "wrong fact unit")
    require(denominator_kind is None or value["denominator_kind"] == denominator_kind, "wrong fact denominator")
    require(value["construction"] in CONSTRUCTIONS, "invalid construction")
    reference(value["provenance"], catalogs)
    for key in ("numerator", "denominator"):
        number(value[key], minimum=0, nullable=True)
    require(value["denominator"] is None or value["denominator"] >= 0, "negative denominator")
    require(not value["support"]["prior_only"] and not value["support"]["prior_seasons"], "fact claims model prior")
    require(value["provenance"]["kind"] == ("source" if value["construction"] in ("recorded", "reconstructed", "source_modeled") else "method"), "fact provenance kind differs from construction")
    if value["value"] is not None and value["denominator_kind"] == "included_seconds":
        require(value["denominator"] is not None and value["denominator"] > 0 and value["numerator"] is not None
                and value["support"]["included_seconds"] == value["denominator"]
                and close(value["value"], 3600 * value["numerator"] / value["denominator"]), "count/time fact does not reconcile")


def _receipts(value, *, nullable_digest=False):
    require(type(value) is list, "expected receipts")
    for row in value:
        fields(row, ("uri", "sha256"))
        text(row["uri"])
        if row["sha256"] is not None or not nullable_digest:
            digest(row["sha256"])


def validate_catalog(table, row, purpose, catalogs, prepared):
    if table == "sources":
        fields(row, ("source_id", "label", "purpose", "origin", "acquisition", "construction", "population", "definition", "receipts", "limitations"))
        for key in ("source_id", "label", "population", "definition"):
            text(row[key])
        require(row["purpose"] == purpose and row["origin"] in ("source_capture", "synthetic") and (row["origin"] != "synthetic" or purpose == "fixture"), "mixed or invalid source purpose")
        require(row["acquisition"] in ("admitted", "not_acquired", "access_unverified") and row["construction"] in CONSTRUCTIONS, "invalid source disposition")
        strings(row["limitations"])
        _receipts(row["receipts"])
        require(bool(row["receipts"]) if row["acquisition"] == "admitted" else bool(row["limitations"]), "source lacks admission receipts or unavailable limitation")
    elif table == "methods":
        fields(row, ("method_id", "family", "recipe_id", "design_sha256", "input_sha256", "fit_seasons", "training_cutoff", "target", "population", "reference", "limitations", "evidence", "purpose", "inputs", "reference_id", "support_policy_id", "assessment"))
        for key in ("method_id", "recipe_id", "target", "population", "reference", "reference_id", "support_policy_id"):
            text(row[key])
        text(row["family"])
        require(row["family"] in FAMILY_TABLES and row["purpose"] == purpose, "invalid method family or purpose")
        if row["design_sha256"] is not None:
            digest(row["design_sha256"])
        if row["training_cutoff"] is not None:
            iso_date(row["training_cutoff"])
        digest(row["input_sha256"])
        strings(row["fit_seasons"], ordered=True)
        for year in row["fit_seasons"]:
            season(year)
        strings(row["limitations"])
        _receipts(row["evidence"])
        require(type(row["inputs"]) is list, "missing method inputs")
        for item in row["inputs"]:
            fields(item, ("role", "sha256", "seasons"))
            require(item["role"] in ("prepared", "coaches", "annual_state", "opportunity_panel", "source_results", "predecessor"), "invalid method input role")
            digest(item["sha256"])
            strings(item["seasons"], ordered=True)
            for year in item["seasons"]:
                season(year)
            if item["role"] in ("annual_state", "predecessor"):
                require(set(item["seasons"]) <= set(row["fit_seasons"]), "state input season is outside method fit seasons")
        require(hashlib.sha256(json_bytes(row["inputs"])).hexdigest() == row["input_sha256"], "method input digest differs")
        require(prepared is not None and any(item["role"] == "prepared" and item["sha256"] == prepared for item in row["inputs"]), "method lacks bound preparation")
        assessment = row["assessment"]
        fields(assessment, ("status", "findings"))
        require(assessment["status"] == "experimental" and type(assessment["findings"]) is list, "invalid assessment")
        for item in assessment["findings"]:
            fields(item, ("quantities", "population", "summary", "evidence"))
            strings(item["quantities"])
            require(item["quantities"] and set(item["quantities"]) <= QUANTITY_PATHS, "assessment has unknown quantities")
            if row['family'] == 'execution':
                require(not set(item['quantities']) & {'execution_breakdown.probability','execution_breakdown.effect','execution_breakdown.expected_successes'},
                        'execution assessment names retired skater breakdown quantities')
            text(item["population"])
            text(item["summary"])
            _receipts(item["evidence"], nullable_digest=True)
        require(row["design_sha256"] is not None and row["training_cutoff"] is not None or bool(assessment["findings"]) and bool(row["evidence"]), "unavailable fit lacks evidence")
    elif table == "supports":
        fields(row, ("support_id", "season", "population_id", "policy_id", "definition", "source_ids", "method_ids"))
        for key in ("support_id", "policy_id", "definition"):
            text(row[key])
        season(row["season"])
        require(row["population_id"] in ("source_supported_attempts", *CONTEXT_POPULATIONS), "invalid support population")
        for field, catalog in (("source_ids", "source"), ("method_ids", "method")):
            strings(row[field], ordered=True)
            require(set(row[field]) <= set(catalogs[catalog]), "dangling support reference")
        _method_supports(row,row['season'],catalogs)
    else:
        fields(row, ("season", "player_id", "kind", "display_name", "reported_position", "teams", "source", "birth_date", "age_as_of", "age_years", "height_cm", "handedness", "sweater_numbers", "identity_support"))
        season(row["season"])
        identifier(row["player_id"])
        require(row["kind"] in ("skater", "goalie") and row["reported_position"] in ((None, "G") if row["kind"] == "goalie" else (None, "C", "L", "R", "D", "F")), "invalid person kind/position")
        if row["display_name"] is not None:
            text(row["display_name"])
        require(type(row["teams"]) is list, "invalid person teams")
        ids = []
        for team in row["teams"]:
            fields(team, ("id", "abbreviation"))
            identifier(team["id"])
            require(team["abbreviation"] is None or type(team["abbreviation"]) is str and bool(team["abbreviation"]), "invalid team abbreviation")
            ids.append(team["id"])
        require(len(ids) == len(set(ids)), "duplicate person team")
        require(type(row["source"]) is list, "invalid person source references")
        for item in row["source"]:
            reference(item, catalogs)
        for field in ("birth_date", "age_as_of"):
            if row[field] is not None:
                iso_date(row[field])
        require(row["age_as_of"] == row["season"][4:] + "-02-01", "wrong age reference date")
        number(row["age_years"], minimum=0, nullable=True)
        if row['age_years'] is not None:
            require(row['birth_date'] is not None and close(row['age_years'], (date.fromisoformat(row['age_as_of'])-date.fromisoformat(row['birth_date'])).days/365.25), 'age differs from dated birth evidence')
        number(row["height_cm"], minimum=0, nullable=True)
        require(row['height_cm'] is None or row['height_cm'] > 0, 'nonpositive normalized height')
        require(row['birth_date'] is None or row['birth_date'] <= row['age_as_of'], 'birth date follows age reference')
        require(row["handedness"] in (None, "L", "R"), "invalid handedness")
        require(type(row["sweater_numbers"]) is list, "invalid sweater observations")
        sweaters = set()
        for item in row["sweater_numbers"]:
            fields(item, ("team_id", "game_id", "number"))
            identifier(item["team_id"])
            game_id(item["game_id"], row["season"])
            require(type(item["number"]) is str and re.fullmatch(r"[0-9]{1,2}", item["number"]) is not None, "invalid sweater number")
            key = (item["team_id"], item["game_id"], item["number"])
            require(key not in sweaters, "duplicate sweater observation")
            sweaters.add(key)
        fields(row["identity_support"], ("problems", "evidence"))
        require(type(row["identity_support"]["problems"]) is list and type(row["identity_support"]["evidence"]) is list, "invalid identity support arrays")
        for item in row["identity_support"]["evidence"]:
            reference(item, catalogs)
        problem_fields = set()
        for item in row["identity_support"]["problems"]:
            fields(item, ("field", "code", "explanation"))
            require(item["field"] in ("display_name", "birth_date", "age_years", "height_cm", "handedness", "sweater_numbers", "reported_position", "teams", "age_as_of"), "invalid identity problem field")
            text(item["code"])
            text(item["explanation"])
            problem_fields.add(item["field"])
        require(all(row[field] is not None or field in problem_fields for field in ("display_name", "reported_position", "birth_date", "age_years", "height_cm", "handedness")) and (row["teams"] or "teams" in problem_fields), "missing identity reason")


def game_id(value, year):
    require(type(value) is str and re.fullmatch(r"[1-9][0-9]{9}", value) is not None and value[:4] == year[:4] and value[4:6] == "02", "invalid regular-season game id")


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


PERSON_SCHEMA = """
CREATE TABLE person (
    season TEXT NOT NULL REFERENCES season(season),
    player_id TEXT NOT NULL CHECK(player_id GLOB '[1-9]*' AND player_id NOT GLOB '*[^0-9]*'),
    kind TEXT NOT NULL CHECK(kind IN ('skater','goalie')),
    display_name TEXT,
    reported_position TEXT CHECK(reported_position IN ('C','L','R','D','F','G')),
    teams_json TEXT NOT NULL CHECK(json_valid(teams_json)),
    source_json TEXT NOT NULL CHECK(json_valid(source_json)),
    birth_date TEXT,
    age_as_of TEXT NOT NULL,
    age_years REAL CHECK(age_years>=0),
    height_cm REAL CHECK(height_cm>0),
    handedness TEXT CHECK(handedness IN ('L','R')),
    sweater_numbers_json TEXT NOT NULL CHECK(json_valid(sweater_numbers_json)),
    identity_support_json TEXT NOT NULL CHECK(json_valid(identity_support_json)),
    name_source_json TEXT CHECK(name_source_json IS NULL OR json_valid(name_source_json)),
    position_source_json TEXT CHECK(position_source_json IS NULL OR json_valid(position_source_json)),
    PRIMARY KEY(season,player_id),
    CHECK(reported_position IS NULL OR (kind='goalie')=(reported_position='G'))
) STRICT;
"""

SCHEMA = """
CREATE TABLE analysis_source (
    source_id TEXT NOT NULL PRIMARY KEY,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json))
) STRICT;
CREATE TABLE analysis_method (
    method_id TEXT NOT NULL PRIMARY KEY,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json))
) STRICT;
CREATE TABLE analysis_support (
    support_id TEXT NOT NULL PRIMARY KEY,
    season TEXT NOT NULL REFERENCES season(season),
    population_id TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json))
) STRICT;
CREATE TABLE analysis_family (
    season TEXT NOT NULL REFERENCES season(season),
    family TEXT NOT NULL CHECK(family IN ('descriptive','microstats','spatial','execution','shootiness','penalties','territory','goalie','ledger','evidence')),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    PRIMARY KEY(season,family),
    CHECK((availability='provided' AND explanation IS NULL) OR (availability='not_computed' AND length(trim(explanation))>0))
) STRICT;
CREATE TABLE analysis_grid (
    grid_id TEXT NOT NULL PRIMARY KEY CHECK(grid_id IN ('native656','display668')),
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json))
) STRICT;
CREATE TABLE skater_descriptive (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_context (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_microstats (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_spatial (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_execution (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_shootiness (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_penalties (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE skater_territory (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE goalie_result (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE goalie_observed (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE goalie_evidence_map (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    population TEXT NOT NULL,
    type TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength,population,type),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE goalie_danger (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    population TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength,population),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE value_ledger (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE analysis_map (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    map_kind TEXT NOT NULL,
    strength TEXT NOT NULL,
    view TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,map_kind,strength,view),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE execution_breakdown (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    kind TEXT NOT NULL,
    stratum TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength,kind,stratum),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE adjustment_decomposition (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    strength TEXT NOT NULL,
    target TEXT NOT NULL,
    method_id TEXT REFERENCES analysis_method(method_id),
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    explanation TEXT,
    payload_json TEXT CHECK(payload_json IS NULL OR json_valid(payload_json)),
    PRIMARY KEY(season,player_id,strength,target),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    CHECK((availability='provided' AND explanation IS NULL AND payload_json IS NOT NULL) OR
          (availability='not_computed' AND length(trim(explanation))>0 AND payload_json IS NULL AND method_id IS NULL))
) STRICT;
CREATE TABLE attempt_fact (
    season TEXT NOT NULL,
    game_id TEXT NOT NULL,
    source_index INTEGER NOT NULL CHECK(source_index BETWEEN 0 AND 9007199254740991),
    shooter_id TEXT,
    goalie_id TEXT,
    strength TEXT,
    outcome TEXT NOT NULL CHECK(outcome IN ('goal','save','miss','block')),
    shot_type TEXT,
    support_id TEXT NOT NULL REFERENCES analysis_support(support_id),
    method_id TEXT REFERENCES analysis_method(method_id),
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY(season,game_id,source_index),
    FOREIGN KEY(season,game_id) REFERENCES game(season,game_id),
    FOREIGN KEY(season,shooter_id) REFERENCES person(season,player_id),
    FOREIGN KEY(season,goalie_id) REFERENCES person(season,player_id)
) STRICT;
CREATE TABLE attempt_setter (
    season TEXT NOT NULL,
    game_id TEXT NOT NULL,
    source_index INTEGER NOT NULL,
    candidate_id TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY(season,game_id,source_index,candidate_id),
    FOREIGN KEY(season,game_id,source_index) REFERENCES attempt_fact(season,game_id,source_index)
) STRICT;
CREATE TABLE attempt_execution_share (
    season TEXT NOT NULL,
    game_id TEXT NOT NULL,
    source_index INTEGER NOT NULL,
    "group" TEXT NOT NULL CHECK("group" IN ('shooter','setter','goalie','coach')),
    recipient_id TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY(season,game_id,source_index,"group",recipient_id),
    FOREIGN KEY(season,game_id,source_index) REFERENCES attempt_fact(season,game_id,source_index)
) STRICT;
CREATE TABLE dressed_game (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY(season,player_id,game_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id),
    FOREIGN KEY(season,game_id) REFERENCES game(season,game_id)
) STRICT;
CREATE TABLE interval_fact (
    season TEXT NOT NULL,
    game_id TEXT NOT NULL,
    interval_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    population TEXT NOT NULL,
    period_number INTEGER NOT NULL CHECK(period_number BETWEEN 1 AND 4),
    start_seconds REAL NOT NULL CHECK(start_seconds>=0),
    end_seconds REAL NOT NULL CHECK(end_seconds>start_seconds AND end_seconds<=1200),
    support_id TEXT NOT NULL REFERENCES analysis_support(support_id),
    for_mass REAL NOT NULL CHECK(for_mass>=0),
    against_mass REAL NOT NULL CHECK(against_mass>=0),
    on_net_for INTEGER CHECK(on_net_for>=0),
    on_net_against INTEGER CHECK(on_net_against>=0),
    period_horizon_seconds REAL NOT NULL CHECK(period_horizon_seconds>0 AND period_horizon_seconds<=1200 AND end_seconds<=period_horizon_seconds),
    PRIMARY KEY(season,game_id,interval_id,team_id,population),
    FOREIGN KEY(season,game_id) REFERENCES game(season,game_id)
) STRICT;
CREATE TABLE interval_player (
    season TEXT NOT NULL,
    game_id TEXT NOT NULL,
    interval_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    PRIMARY KEY(season,game_id,interval_id,team_id,player_id),
    FOREIGN KEY(season,game_id) REFERENCES game(season,game_id),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id)
) STRICT;
CREATE TABLE interval_location (
    season TEXT NOT NULL,
    game_id TEXT NOT NULL,
    interval_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    population TEXT NOT NULL,
    cell_id INTEGER NOT NULL CHECK(cell_id BETWEEN 0 AND 679),
    for_mass REAL NOT NULL CHECK(for_mass>=0),
    against_mass REAL NOT NULL CHECK(against_mass>=0),
    PRIMARY KEY(season,game_id,interval_id,team_id,population,cell_id),
    FOREIGN KEY(season,game_id,interval_id,team_id,population) REFERENCES interval_fact(season,game_id,interval_id,team_id,population)
) STRICT;
CREATE TABLE context_coverage (
    season TEXT NOT NULL,
    player_id TEXT NOT NULL,
    population TEXT NOT NULL,
    availability TEXT NOT NULL CHECK(availability IN ('provided','not_computed')),
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY(season,player_id,population),
    FOREIGN KEY(season,player_id) REFERENCES person(season,player_id)
) STRICT;
"""


def actual_state(value):
    fields(value, ('attacking_skaters', 'defending_skaters', 'attacking_goalie_present', 'defending_goalie_present'))
    for key in ('attacking_skaters', 'defending_skaters'):
        number(value[key], minimum=0, maximum=6, integer=True)
    require(type(value['attacking_goalie_present']) is bool and type(value['defending_goalie_present']) is bool, 'invalid goalie presence')


def _usage(value, catalogs, *, teams=True):
    names = ('positive_toi_appearances', 'reported_seconds', 'minutes_per_appearance', 'reported_shifts', 'listed_games', 'supported_games', 'missing_games', 'support')
    fields(value, (*names, 'teams', 'provenance') if teams else (*names, 'team_id'))
    if teams:
        source_reference(value['provenance'],catalogs)
    for key in ('positive_toi_appearances', 'reported_shifts', 'listed_games', 'supported_games', 'missing_games'):
        number(value[key], minimum=0, integer=True, nullable=key == 'reported_shifts')
    number(value['reported_seconds'], minimum=0, nullable=True)
    support(value['support'])
    estimate(value['minutes_per_appearance'], catalogs, nonnegative=True)
    require(value['supported_games'] + value['missing_games'] == value['listed_games'] and value['positive_toi_appearances'] <= value['supported_games'], 'usage game coverage differs')
    if value['minutes_per_appearance']['value'] is not None:
        require(value['positive_toi_appearances'] > 0 and value['reported_seconds'] is not None and close(value['minutes_per_appearance']['value'], value['reported_seconds'] / (60*value['positive_toi_appearances'])), 'usage minutes differ')
    if teams:
        require(type(value['teams']) is list, 'expected team usage')
        ids = []
        for team in value['teams']:
            identifier(team['team_id'])
            ids.append(team['team_id'])
            _usage(team, catalogs, teams=False)
        require(len(ids) == len(set(ids)), 'duplicate usage team')
    else:
        identifier(value['team_id'])


def _scoring(value, catalogs, *, state=False, unclassified=False):
    names = ('goals', 'primary_assists', 'primary_points', 'support')
    if not unclassified:
        names += ('seconds', 'goals_per60', 'primary_assists_per60', 'primary_points_per60')
    fields(value, (*names, 'state') if state else names)
    if state:
        actual_state(value['state'])
    for key in ('goals', 'primary_assists', 'primary_points'):
        number(value[key], minimum=0, integer=True, nullable=True)
    support(value['support'])
    if value['goals'] is not None and value['primary_assists'] is not None:
        require(value['primary_points'] == value['goals'] + value['primary_assists'], 'primary points differ')
    if not unclassified:
        number(value['seconds'], minimum=0, nullable=True)
        for key in ('goals', 'primary_assists', 'primary_points'):
            rate = value[key+'_per60']
            estimate(rate, catalogs, nonnegative=True)
            if rate['value'] is not None:
                require(value['seconds'] is not None and value['seconds'] > 0 and value[key] is not None and close(rate['value'], 3600*value[key]/value['seconds']), 'scoring rate differs')


def _on_off(value, catalogs, *, goals=False):
    fields(value, ('on', 'off', 'league'))
    for row in value.values():
        fields(row, ('for_count', 'against_count', 'seconds', 'for_per60', 'against_per60', 'share_minus_half', 'support', 'on_net_for', 'on_net_against') if goals else ('for_count', 'against_count', 'seconds', 'for_per60', 'against_per60', 'share_minus_half', 'support'))
        for key in ('for_count', 'against_count', *(('on_net_for', 'on_net_against') if goals else ())):
            number(row[key], minimum=0, integer=True, nullable=True)
        number(row['seconds'], minimum=0, nullable=True)
        support(row['support'])
        for side in ('for', 'against'):
            rate = row[side+'_per60']
            estimate(rate, catalogs, nonnegative=True)
            if rate['value'] is not None:
                require(row['seconds'] is not None and row['seconds'] > 0 and row[side+'_count'] is not None and close(rate['value'], 3600*row[side+'_count']/row['seconds']), 'on/off rate differs')
        estimate(row['share_minus_half'], catalogs)
        if row['share_minus_half']['value'] is not None:
            require(row['for_count'] is not None and row['against_count'] is not None and row['for_count']+row['against_count'] > 0 and close(row['share_minus_half']['value'], 100*(row['for_count']/(row['for_count']+row['against_count'])-.5)), 'share differs')


def _penalty(value, catalogs):
    fields(value, ('count', 'reported_seconds', 'per1000minutes', 'categories', 'support'))
    number(value['count'], minimum=0, integer=True, nullable=True)
    number(value['reported_seconds'], minimum=0, nullable=True)
    estimate(value['per1000minutes'], catalogs, nonnegative=True)
    support(value['support'])
    require(type(value['categories']) is list, 'expected penalty categories')
    codes = []
    for item in value['categories']:
        fields(item, ('code', 'count'))
        text(item['code'])
        number(item['count'], minimum=0, integer=True)
        codes.append(item['code'])
    require(codes == sorted(set(codes)) and (value['count'] is None or sum(item['count'] for item in value['categories']) == value['count']), 'penalty categories differ')
    if value['per1000minutes']['value'] is not None:
        require(value['reported_seconds'] is not None and value['reported_seconds'] > 0 and value['count'] is not None and close(value['per1000minutes']['value'], 60000*value['count']/value['reported_seconds']), 'penalty rate differs')


def _descriptive(value, catalogs):
    fields(value, ('reported_usage', 'strength_usage', 'scoring_by_strength', 'on_off_attempts', 'on_off_goals', 'on_ice_conversion', 'recorded_penalties', 'deployment', 'provenance'))
    source_reference(value['provenance'],catalogs)
    _usage(value['reported_usage'], catalogs)
    for name in ('strength_usage', 'scoring_by_strength'):
        groups = value[name]
        fields(groups, ('ev', 'pp', 'pk', 'other', 'five_on_five', 'states', 'unclassified') if name == 'scoring_by_strength' else ('ev', 'pp', 'pk', 'other', 'five_on_five', 'states'))
        for key in ('ev', 'pp', 'pk', 'other', 'five_on_five'):
            if name == 'scoring_by_strength':
                _scoring(groups[key], catalogs)
            else:
                _strength_usage(groups[key], catalogs)
        states = []
        require(type(groups['states']) is list, 'expected exact strength states')
        for row in groups['states']:
            if name == 'scoring_by_strength':
                _scoring(row, catalogs, state=True)
            else:
                _strength_usage(row, catalogs, state=True)
            states.append(json_bytes(row['state']))
        require(len(states) == len(set(states)), 'duplicate exact strength state')
        if name == 'scoring_by_strength':
            _scoring(groups['unclassified'], catalogs, unclassified=True)
    _on_off(value['on_off_attempts'], catalogs)
    _on_off(value['on_off_goals'], catalogs, goals=True)
    for name in ('on_ice_conversion', 'recorded_penalties', 'deployment'):
        fields(value[name], ('focal', 'team', 'league'))
        for row in value[name].values():
            if name == 'on_ice_conversion':
                fields(row, ('goals_for', 'goals_against', 'on_net_for', 'on_net_against', 'shooting_for', 'shooting_against', 'save_fraction', 'support'))
                for field in ('goals_for', 'goals_against', 'on_net_for', 'on_net_against'):
                    number(row[field], minimum=0, integer=True, nullable=True)
                support(row['support'])
                for field, numerator, denominator in (('shooting_for', 'goals_for', 'on_net_for'), ('shooting_against', 'goals_against', 'on_net_against'), ('save_fraction', 'goals_against', 'on_net_against')):
                    estimate(row[field], catalogs, probability=True)
                    if row[field]['value'] is not None:
                        require(row[denominator] is not None and row[denominator] > 0 and row[numerator] is not None, 'conversion lacks denominator')
                        expected = row[numerator]/row[denominator]
                        require(close(row[field]['value'], 1-expected if field == 'save_fraction' else expected), 'conversion ratio differs')
            elif name == 'recorded_penalties':
                fields(row, ('drawn', 'taken', 'served'))
                for item in row.values():
                    _penalty(item, catalogs)
            else:
                fields(row, ('shift_starts', 'score', 'support'))
                support(row['support'])
                for group, names, field in (('shift_starts', ('offensive','neutral','defensive','on_the_fly','unknown'), 'count'), ('score', ('leading','tied','trailing','unknown'), 'seconds')):
                    fields(row[group], names)
                    for item in row[group].values():
                        fields(item, (field, 'share'))
                        number(item[field], minimum=0, integer=field == 'count', nullable=True)
                        estimate(item['share'], catalogs, probability=True)
                    for key, item in row[group].items():
                        denominator_keys = names if group == 'shift_starts' or key == 'unknown' else names[:-1]
                        parts = [row[group][name][field] for name in denominator_keys]
                        total = sum(parts) if all(part is not None for part in parts) else None
                        if item['share']['value'] is not None:
                            require(item[field] is not None and total is not None and total > 0 and close(item['share']['value'], item[field]/total), 'deployment share differs')


def _strength_usage(value, catalogs, *, state=False):
    fields(value, ('seconds', 'appearances', 'minutes_per_appearance', 'support', 'state') if state else ('seconds', 'appearances', 'minutes_per_appearance', 'support'))
    if state:
        actual_state(value['state'])
    number(value['seconds'], minimum=0, nullable=True)
    number(value['appearances'], minimum=0, integer=True)
    support(value['support'])
    estimate(value['minutes_per_appearance'], catalogs, nonnegative=True)
    if value['minutes_per_appearance']['value'] is not None:
        require(value['appearances'] > 0 and value['seconds'] is not None and close(value['minutes_per_appearance']['value'], value['seconds']/(60*value['appearances'])), 'strength usage differs')


def _counterparts(value, catalogs, *, bands=None):
    fields(value, ('usage_minutes_per_appearance', 'known_slot_seconds', 'all_slot_seconds', 'unique_counterparts', 'forward', 'defense', 'coverage') if bands is None else ('usage_minutes_per_appearance', 'mean_band_index', 'known_slot_seconds', 'all_slot_seconds', 'unique_counterparts', 'bands', 'coverage'))
    estimate(value['usage_minutes_per_appearance'], catalogs, nonnegative=True)
    number(value['known_slot_seconds'], minimum=0)
    number(value['all_slot_seconds'], minimum=0)
    number(value['unique_counterparts'], minimum=0, integer=True)
    support(value['coverage'])
    require(value['known_slot_seconds'] <= value['all_slot_seconds'] and (value['usage_minutes_per_appearance']['value'] is None or value['known_slot_seconds'] > 0), 'counterpart support differs')
    if bands is None:
        _counterparts(value['forward'], catalogs, bands=4)
        _counterparts(value['defense'], catalogs, bands=3)
    else:
        estimate(value['mean_band_index'], catalogs, nonnegative=True)
        require(type(value['bands']) is list and len(value['bands']) == bands, 'wrong band count')
        for index, item in enumerate(value['bands'], 1):
            fields(item, ('band', 'counterparts', 'slot_seconds'))
            require(item['band'] == index, 'wrong band identity')
            number(item['counterparts'], minimum=0, integer=True)
            number(item['slot_seconds'], minimum=0)
        require(close(sum(item['slot_seconds'] for item in value['bands']), value['known_slot_seconds']), 'band weights differ')
        if value['mean_band_index']['value'] is not None:
            require(value['known_slot_seconds'] > 0 and close(value['mean_band_index']['value'], sum(item['band']*item['slot_seconds'] for item in value['bands'])/value['known_slot_seconds']), 'mean band differs')


def _source_counts(value, catalogs):
    fields(value, ('unblocked_attempts', 'misses', 'shots_on_goal', 'saves', 'goals_against', 'save_percentage', 'support', 'provenance'))
    source_reference(value['provenance'],catalogs)
    for key in ('unblocked_attempts', 'misses', 'shots_on_goal', 'saves', 'goals_against'):
        number(value[key], minimum=0, integer=True, nullable=True)
    support(value['support'])
    estimate(value['save_percentage'], catalogs, probability=True)
    for total, left, right in (('unblocked_attempts','misses','shots_on_goal'), ('shots_on_goal','saves','goals_against')):
        if value[left] is not None and value[right] is not None:
            require(value[total] == value[left]+value[right], 'goalie count closure differs')
    if value['save_percentage']['value'] is not None:
        require(value['shots_on_goal'] is not None and value['shots_on_goal'] > 0 and value['saves'] is not None and close(value['save_percentage']['value'], value['saves']/value['shots_on_goal']), 'save fraction differs')


def _paired(value, catalogs, *, on_net=False):
    names = ('attempts','goals','expected_goals','goals_saved_above_expected','goals_per100_expected','mean_goal_probability','league_mean_goal_probability','difficulty_relative_percent','support','method_id')
    fields(value, (*names, 'expected_save_fraction') if on_net else names)
    number(value['attempts'], minimum=0, integer=True)
    number(value['goals'], minimum=0, maximum=value['attempts'], integer=True)
    number(value['expected_goals'], minimum=0, maximum=value['attempts'])
    support(value['support'])
    _method(value['method_id'], catalogs)
    require(catalogs['method'][value['method_id']]['family'] == 'goalie', 'paired goalie evidence uses another method family')
    if value['attempts'] > 0 or _has_available_estimate(value):
        _available_method(value['method_id'], catalogs)
    for field in ('goals_saved_above_expected','goals_per100_expected','mean_goal_probability','league_mean_goal_probability','difficulty_relative_percent', *(('expected_save_fraction',) if on_net else ())):
        estimate(value[field], catalogs, probability=field in ('mean_goal_probability','league_mean_goal_probability','expected_save_fraction'), nonnegative=field == 'goals_per100_expected')
    expected = {'goals_saved_above_expected':value['expected_goals']-value['goals']}
    if value['attempts'] > 0:
        expected['mean_goal_probability'] = value['expected_goals']/value['attempts']
        if on_net:
            expected['expected_save_fraction'] = 1-value['expected_goals']/value['attempts']
    if value['expected_goals'] > 0:
        expected['goals_per100_expected'] = 100*value['goals']/value['expected_goals']
    if value['attempts'] > 0 and value['league_mean_goal_probability']['value'] is not None and value['league_mean_goal_probability']['value'] > 0:
        expected['difficulty_relative_percent'] = 100*((value['expected_goals']/value['attempts'])/value['league_mean_goal_probability']['value']-1)
    for key in expected:
        if value[key]['value'] is not None:
            require(close(value[key]['value'], expected[key]), 'paired goalie reduction differs')


def _goalie_summary(value, catalogs, *, game=False):
    names = ('source_counts','reported_boxscore_counts','on_net_evidence','unblocked_evidence','stage_evidence','actual_states','provenance')
    if game:
        fields(value, (*names,'game_id','date','team','opponent','start_status','reported_seconds'))
        iso_date(value['date'])
        require(value['start_status'] in ('start','relief','did_not_play','unknown'), 'invalid start status')
        number(value['reported_seconds'], minimum=0, nullable=True)
        for key in ('team','opponent'):
            fields(value[key], ('id','abbreviation'))
            identifier(value[key]['id'])
            require(value[key]['abbreviation'] is None or type(value[key]['abbreviation']) is str, 'invalid abbreviation')
    else:
        fields(value, (*names,'starts','relief_appearances','unknown_start_status','reported_usage','coverage','games'))
        for key in ('starts','relief_appearances','unknown_start_status'):
            number(value[key], minimum=0, integer=True)
        _usage(value['reported_usage'], catalogs)
        support(value['coverage'])
        require(type(value['games']) is list, 'expected goalie games')
        ids = []
        for row in value['games']:
            _goalie_summary(row, catalogs, game=True)
            ids.append(row['game_id'])
        require(len(ids) == len(set(ids)), 'duplicate goalie game')
    source_reference(value['provenance'],catalogs)
    for key in ('source_counts','reported_boxscore_counts'):
        _source_counts(value[key], catalogs)
    _paired(value['on_net_evidence'], catalogs, on_net=True)
    _paired(value['unblocked_evidence'], catalogs)
    _goalie_actual_states(value,catalogs)
    _goalie_stages(value['stage_evidence'])


def _goalie_stages(stages):
    fields(stages, ('miss','recorded_stop','conversion','reattempt','next_attempt_danger'))
    for key, row in stages.items():
        fields(row, ('fractional_response_sum','eligible_count','matched_expected_sum','support') if key == 'next_attempt_danger' else ('success_count','eligible_count','matched_expected_sum','support'))
        number(row['eligible_count'], minimum=0, integer=True)
        number(row['matched_expected_sum'], minimum=0, maximum=row['eligible_count'])
        numerator = 'fractional_response_sum' if key == 'next_attempt_danger' else 'success_count'
        number(row[numerator], minimum=0, maximum=row['eligible_count'], integer=key != 'next_attempt_danger')
        support(row['support'])


def _method(method_id, catalogs):
    text(method_id)
    require(method_id in catalogs['method'], 'dangling method id')


def _available_method(method_id, catalogs):
    _method(method_id, catalogs)
    method = catalogs['method'][method_id]
    require(method['design_sha256'] is not None and method['training_cutoff'] is not None, 'unavailable fit supports available fitted output')


def native_display_mass(native):
    """the fixed native656 to blurred display668 mass transport."""
    from .observed_spatial import cells, cell_id, pooling
    from .shot_origins import grid
    import numpy as np

    indices = {item['cell_id']:index for index,item in enumerate(cells())}
    unpooled = np.zeros(668)
    require(len(native) == 656, 'wrong native transport length')
    for mass,(x,y) in zip(native,grid()[0]):
        unpooled[indices[cell_id(float(x),float(y))]] += mass
    return pooling() @ unpooled


def _map(value, row, catalogs):
    from .observed_spatial import cells

    fields(value, ('grid_id','unit','reference','cells','display_cells','integrated_value','unavailable_reason','reason_detail','support','method_id'))
    require(value['grid_id'] == 'native656', 'invalid model grid')
    unit = {'offense_attempts':'attempts_per60','defense_attempts':'attempts_per60','offense_xg':'xg_per60','defense_xg':'xg_per60','finishing':'goals_per100_attempts','setting':'goals_per100_assisted_opportunities','ice_won':'goals_per_basket','ice_lost':'goals_per_basket','goalie_stopping':'goals_per100_on_net'}[row['map_kind']]
    require(value['unit'] == unit, 'wrong map unit')
    text(value['reference'])
    support(value['support'])
    _method(value['method_id'], catalogs)
    if value['cells'] is None:
        require(value['display_cells'] is None and value['integrated_value'] is None, 'unavailable map contains values')
        estimate({'value':None,'unavailable_reason':value['unavailable_reason'],'reason_detail':value['reason_detail'],'uncertainty':{'kind':'not_estimated'}}, catalogs)
        return
    _available_method(value['method_id'], catalogs)
    require(type(value['cells']) is list and len(value['cells']) == 656 and value['unavailable_reason'] is None and value['reason_detail'] is None, 'invalid native map')
    native = []
    for index, item in enumerate(value['cells']):
        fields(item, ('cell_id','value'))
        require(type(item['cell_id']) is int and item['cell_id'] == index, 'invalid native map cell')
        number(item['value'], minimum=0 if row['view'] == 'complete' else None)
        native.append(item['value'])
    number(value['integrated_value'])
    require(close(sum(native), value['integrated_value']), 'native map mass differs')
    geometry = cells()
    expected = native_display_mass(native)
    require(type(value['display_cells']) is list and len(value['display_cells']) == 668, 'wrong display map length')
    for item, shape, mass in zip(value['display_cells'], geometry, expected):
        fields(item, ('cell_id','mass','density_per100sqft'))
        require(type(item['cell_id']) is int and item['cell_id'] == shape['cell_id'], 'display cell identity differs')
        number(item['mass'])
        number(item['density_per100sqft'])
        require(close(item['mass'], float(mass)) and close(item['density_per100sqft'], 100*item['mass']/shape['area_sqft']), 'display map transport differs')
    require(close(sum(item['mass'] for item in value['display_cells']), value['integrated_value']), 'display mass differs')


def _evidence_mass(value, *, cell=False):
    fields(value, ('cell_id','goals','expected_goals','attempts') if cell else ('goals','expected_goals','attempts'))
    number(value['attempts'], minimum=0, integer=not cell)
    number(value['goals'], minimum=0, maximum=value['attempts'], integer=not cell)
    number(value['expected_goals'], minimum=0, maximum=value['attempts'])


def _execution_details(value):
    panel = value['reference_panel']
    fields(panel, ('panel_id','opportunities','setup_weight','neutral','focal_shooter','setting_setup'))
    text(panel['panel_id'])
    number(panel['opportunities'],minimum=0,integer=True)
    number(panel['setup_weight'],minimum=0)
    require(close(panel['setup_weight'],.8*panel['opportunities']), 'execution setup weight differs')
    for key in ('neutral','focal_shooter'):
        fields(panel[key], ('u','uq','uqr','uqrg'))
        previous = panel['opportunities']
        for prefix in ('u','uq','uqr','uqrg'):
            mass = panel[key][prefix]
            number(mass,minimum=0,nullable=key == 'focal_shooter')
            require(mass is None or previous is not None and mass <= previous, 'execution prefix mass not nested')
            previous = mass
    fields(panel['setting_setup'], ('neutral_goal_mass','focal_goal_mass'))
    for key, mass in panel['setting_setup'].items():
        number(mass,minimum=0,maximum=panel['setup_weight'],nullable=key == 'focal_goal_mass')
    require(panel['setting_setup']['neutral_goal_mass'] <= panel['neutral']['uqrg'], 'setup neutral goal mass exceeds total')
    coefficients = value['coefficient_support']
    fields(coefficients, ('shooter','setter'))
    fields(coefficients['shooter'], ('u','q','r','g'))
    fields(coefficients['setter'], ('g',))
    for role, heads in coefficients.items():
        for coefficient in heads.values():
            fields(coefficient, ('available','likelihood_events','prior_only','prior_seasons','reason',
                                *(('candidate_events','mean_coupled_events') if role == 'setter' else ())))
            require(type(coefficient['available']) is bool, 'invalid coefficient availability')
            number(coefficient['likelihood_events'],minimum=0,integer=True,nullable=True)
            require(coefficient['prior_only'] is None or type(coefficient['prior_only']) is bool, 'invalid coefficient prior flag')
            strings(coefficient['prior_seasons'],ordered=True)
            for year in coefficient['prior_seasons']:
                season(year)
            if coefficient['reason'] is not None:
                text(coefficient['reason'])
            if coefficient['available']:
                require(coefficient['prior_only'] is not None and (coefficient['likelihood_events'] is not None or coefficient['reason'] is not None), 'available coefficient lacks information')
            else:
                require(coefficient['likelihood_events'] is None and coefficient['prior_only'] is None
                        and not coefficient['prior_seasons'] and coefficient['reason'] is not None, 'absent coefficient invents support')
            if role == 'setter':
                for key in ('candidate_events','mean_coupled_events'):
                    number(coefficient[key],minimum=0,integer=True,nullable=True)
                    require(coefficient['available'] or coefficient[key] is None, 'absent setter invents event count')
                    require(coefficient[key] is None or coefficient['likelihood_events'] is None
                            or coefficient[key] <= coefficient['likelihood_events'], 'setter subset exceeds likelihood union')
    available = True
    for head,prefix in zip(('u','q','r','g'),('u','uq','uqr','uqrg')):
        available &= coefficients['shooter'][head]['available']
        require((panel['focal_shooter'][prefix] is not None) == available, 'focal prefix coefficient prerequisites differ')
    require((panel['setting_setup']['focal_goal_mass'] is not None) == coefficients['setter']['g']['available'], 'setting coefficient prerequisite differs')
    def ratio(numerator, denominator):
        return numerator/denominator if numerator is not None and denominator else None
    neutral, focal = panel['neutral'],panel['focal_shooter']
    levels = [('avoid_block_probability',ratio(focal['u'],panel['opportunities']),ratio(neutral['u'],panel['opportunities'])),
              ('on_net_probability',ratio(focal['uq'],focal['u']),ratio(neutral['uq'],neutral['u'])),
              ('recorded_stop_probability',ratio(focal['uqr'],focal['uq']),ratio(neutral['uqr'],neutral['uq'])),
              ('conversion_probability',ratio(focal['uqrg'],focal['uqr']),ratio(neutral['uqrg'],neutral['uqr']))]
    expected, unresolved = {},set()
    for field,level,baseline in levels:
        if field == 'recorded_stop_probability':
            level = 1-level if level is not None else None
            baseline = 1-baseline if baseline is not None else None
        expected[field] = level
        expected[field+'_difference'] = level-baseline if level is not None and baseline is not None else None
        # integrated masses can underflow although a log-domain conditional
        # ratio remains representable. its numerical owner checks that ratio.
        needed = {'avoid_block_probability':'u','on_net_probability':'uq',
                  'recorded_stop_probability':'uqr','conversion_probability':'uqrg'}[field]
        if panel['opportunities'] and focal[needed] is not None:
            if level is None:
                unresolved.add(field)
            if level is None or baseline is None:
                unresolved.add(field+'_difference')
    expected['finishing_goals_per100_attempts'] = ratio(100*(focal['uqrg']-neutral['uqrg']) if focal['uqrg'] is not None else None,panel['opportunities'])
    setting = panel['setting_setup']
    expected['setting_goals_per100_assisted_opportunities'] = ratio(100*(setting['focal_goal_mass']-setting['neutral_goal_mass']) if setting['focal_goal_mass'] is not None else None,panel['setup_weight'])
    for field, magnitude in expected.items():
        actual = value[field]['value']
        if field in unresolved:
            require(actual is not None, 'supported execution conditional ratio unavailable')
            number(actual,minimum=-1 if field.endswith('_difference') else 0,maximum=1)
        else:
            require(actual is None if magnitude is None else actual is not None and close(actual,magnitude), 'execution panel/scalar closure differs')
        require(value['support'][field]['eligible_weight'] is None, 'execution mixed-head support invents eligible weight')
        if field == 'setting_goals_per100_assisted_opportunities':
            records = [coefficients['setter']['g']]
        else:
            count = 4 if field == 'finishing_goals_per100_attempts' else (
                'avoid_block_probability','on_net_probability','recorded_stop_probability','conversion_probability').index(field.removesuffix('_difference'))+1
            records = [coefficients['shooter'][head] for head in ('u','q','r','g')[:count]]
        metric = value['support'][field]
        complete = all(record['available'] for record in records)
        require(metric['prior_only'] == (complete and all(record['prior_only'] for record in records)), 'execution prior-only support differs from coefficients')
        require(metric['prior_seasons'] == sorted({year for record in records for year in record['prior_seasons']}), 'execution prior seasons differ from coefficients')
        counts = [record['likelihood_events'] for record in records]
        if not complete or any(count is None for count in counts):
            require(metric['events'] is None, 'execution event union invents an unavailable count')
            if not complete:
                require(not metric['current_season_information'], 'absent execution coefficient claims current information')
        else:
            require(metric['events'] is not None and max(counts) <= metric['events'] <= sum(counts), 'execution event union outside contributing head bounds')
            require(metric['current_season_information'] == bool(metric['events']), 'execution current information differs from event union')
    qualification = ('included_seconds','known_excluded_seconds','unquantified_gap','reason_counts')
    first_support = value['support']['finishing_goals_per100_attempts']
    require(all(all(metric[key] == first_support[key] for key in qualification) for metric in value['support'].values()),
            'execution exact-strength participation differs across fields')
    paired = value['paired_evidence']
    fields(paired, ('source_attempts','paired_attempts','unvalued_source_attempts','danger_unavailable'))
    for key in ('source_attempts','paired_attempts','unvalued_source_attempts'):
        number(paired[key],minimum=0,integer=True)
    require(paired['source_attempts'] == paired['paired_attempts']+paired['unvalued_source_attempts'], 'paired source count differs')
    omitted = paired['danger_unavailable']
    fields(omitted, ('events','observed_goals','reference_expected_goals','actor_expected_goals'))
    number(omitted['events'],minimum=0,maximum=paired['paired_attempts'],integer=True)
    for key in ('observed_goals','reference_expected_goals','actor_expected_goals'):
        number(omitted[key],minimum=0,maximum=omitted['events'],integer=key == 'observed_goals')


def validate_payload(table, value, row, catalogs, *, person_kind=None):
    if table in ESTIMATE_FIELDS and table != 'attempt_value':
        extra = ('state_weights',) if table == 'skater_spatial' else ('reference_panel','coefficient_support','paired_evidence') if table == 'skater_execution' else ('recorded_drawn','recorded_taken','recorded_served') if table == 'skater_penalties' else ()
        fields(value, (*ESTIMATE_FIELDS[table], *extra, 'support','method_id'))
        for field in ESTIMATE_FIELDS[table]:
            probability = field in ('probability','neutral_probability') or field.endswith('_probability') or field == 'followup_danger'
            estimate(value[field], catalogs, probability=probability, nonnegative=field.endswith(('_complete','_neutral')))
        if table in ('skater_execution','goalie_result'):
            fields(value['support'], ESTIMATE_FIELDS[table])
            for item in value['support'].values():
                support(item)
        else:
            support(value['support'])
        _method(value['method_id'], catalogs)
        if table == 'skater_execution':
            _execution_details(value)
        elif table == 'skater_spatial':
            require(type(value['state_weights']) is list and value['state_weights'], 'missing state weights')
            states = []
            for item in value['state_weights']:
                fields(item, ('strength','weight'))
                require(item['strength'] in EXECUTION_STRENGTHS, 'invalid state weight')
                number(item['weight'], minimum=0, maximum=1)
                states.append(item['strength'])
            require(len(states) == len(set(states)) and close(sum(item['weight'] for item in value['state_weights']),1), 'state weights differ')
            expected_states = ('5v4','5v3','4v3') if row['strength'] == 'pp' else ('4v5','3v5','3v4') if row['strength'] == 'pk' else (row['strength'],)
            require(set(states) == set(expected_states), 'state mixture differs from selector')
            for role in ('offense','defense'):
                if row['strength'] in (('5v4','5v3','4v3','pp') if role == 'defense' else ('4v5','3v5','3v4','pk')):
                    require(all(value[key]['value'] is None and value[key]['unavailable_reason'] == 'not_applicable' for key in ESTIMATE_FIELDS[table] if key.startswith(role+'_')), 'inapplicable spatial role carries an estimate')
                for suffix in ('complete','neutral'):
                    attempts = value[f'{role}_attempts_per60_{suffix}']['value']
                    xg = value[f'{role}_xg_per60_{suffix}']['value']
                    require(attempts is None or xg is None or 0 < xg <= attempts, 'invalid complete chance rate')
                for quantity in ('attempts','xg'):
                    effect = value[f'{role}_{quantity}_per60']['value']
                    complete = value[f'{role}_{quantity}_per60_complete']['value']
                    neutral = value[f'{role}_{quantity}_per60_neutral']['value']
                    relative = value[f'{role}_{quantity}_relative_percent']['value']
                    if all(item is not None for item in (effect,complete,neutral)):
                        require(close(effect,complete-neutral), 'spatial contrast differs')
                    if relative is not None:
                        require(effect is not None and neutral is not None and neutral > 0 and close(relative,100*effect/neutral), 'spatial relative contrast differs')
        elif table == 'skater_shootiness':
            if all(value[key]['value'] is not None for key in ('probability','neutral_probability','difference')):
                require(close(value['difference']['value'],value['probability']['value']-value['neutral_probability']['value']), 'shootiness contrast differs')
        elif table == 'skater_penalties':
            for key in extra:
                _penalty(value[key], catalogs)
    elif table == 'skater_descriptive':
        _descriptive(value, catalogs)
    elif table == 'skater_context':
        fields(value, ('teammates','opponents','provenance'))
        source_reference(value['provenance'],catalogs)
        for key in ('teammates','opponents'):
            _counterparts(value[key], catalogs)
    elif table == 'skater_microstats':
        fields(value, MICROSTATS)
        for key, item in value.items():
            unit, denominator = ('per60','included_seconds') if key.endswith('_per60') else ('fraction','opponent_attempts') if key == 'blocked_attempt_share' else ('fraction','tracked_plays') if key.endswith('_fraction') else ('xga_saved_per100_plays','tracked_plays') if key == 'puck_management_xga_saved_per100_plays' else ('mph','none') if key == 'skating_max_speed_mph' else ('count','none')
            fact_value(item, catalogs, unit=unit, denominator_kind=denominator)
            if item['value'] is not None:
                require(key == 'puck_management_xga_saved_per100_plays' or item['value'] >= 0, 'negative factual value')
                if unit == 'fraction':
                    require(item['value'] <= 1 and item['numerator'] is not None and item['denominator'] is not None and item['denominator'] > 0 and close(item['value'],item['numerator']/item['denominator']), 'fraction differs')
                if key == 'skating_bursts_over20_count':
                    number(item['value'],minimum=0,integer=True)
                    number(item['numerator'],minimum=0,integer=True)
                if denominator == 'none':
                    require(item['denominator'] is None and (item['numerator'] is None if unit == 'mph' else item['numerator'] == item['value'] and type(item['value']) is int), 'raw source aggregate bases differ')
                if key == 'puck_management_xga_saved_per100_plays':
                    require(item['numerator'] is None and item['denominator'] is not None and item['denominator'] > 0 and item['construction'] == 'source_modeled', 'source estimate bases differ')
    elif table == 'skater_territory':
        fields(value, ('ice_won_goals_per_basket','ice_lost_goals_per_basket','exit_offense','entry_offense','zone_retention','entry_prevention','support','method_id'))
        for key in ('ice_won_goals_per_basket','ice_lost_goals_per_basket'):
            estimate(value[key], catalogs)
        support(value['support'])
        _method(value['method_id'], catalogs)
        for key in ('exit_offense','entry_offense','zone_retention','entry_prevention'):
            hazard = 'opponent_exit_hazard_per_second' if key == 'zone_retention' else 'opponent_entry_hazard_per_second' if key == 'entry_prevention' else 'hazard_per_second'
            item = value[key]
            fields(item, (hazard,'one_second_probability','support'))
            estimate(item[hazard], catalogs, nonnegative=True)
            estimate(item['one_second_probability'], catalogs, probability=True)
            support(item['support'])
            if item['one_second_probability']['value'] is not None:
                require(item[hazard]['value'] is not None, 'transition probability lacks hazard')
                expected = math.exp(-item[hazard]['value']) if key in ('zone_retention','entry_prevention') else -math.expm1(-item[hazard]['value'])
                require(close(item['one_second_probability']['value'],expected), 'transition probability differs')
    elif table == 'goalie_observed':
        _goalie_summary(value, catalogs)
        _actual_selection(value['actual_states'],row['strength'])
        for game in value['games']:
            _actual_selection(game['actual_states'],row['strength'])
    elif table == 'value_ledger':
        fields(value, ('reference_minutes','components','league_total','replacement_total','penalties_combined','method_id'))
        fields(value['reference_minutes'], ('five_on_five','power_play','penalty_kill'))
        require(value['reference_minutes'] == dict(five_on_five=1000,power_play=100,penalty_kill=100), 'wrong reference workload')
        fields(value['components'], LEDGER_COMPONENTS)
        _method(value['method_id'], catalogs)
        for item in (*value['components'].values(),value['penalties_combined']):
            fields(item, ('league_goals','replacement_goals'))
            for item in item.values():
                estimate(item, catalogs)
        for reference_name in ('league','replacement'):
            total = value[reference_name+'_total']
            estimate(total, catalogs)
            components = [item[reference_name+'_goals']['value'] for item in value['components'].values()]
            if total['value'] is not None:
                require(all(item is not None for item in components) and close(total['value'],sum(components)), 'ledger total differs')
            penalties = value['penalties_combined'][reference_name+'_goals']['value']
            parts = [value['components'][key][reference_name+'_goals']['value'] for key in ('penalties_drawn','penalties_taken')]
            if penalties is not None:
                require(all(item is not None for item in parts) and close(penalties,sum(parts)), 'combined penalties differ')
    elif table == 'analysis_map':
        _map(value, row, catalogs)
    elif table == 'execution_breakdown':
        _method(value['method_id'],catalogs)
        require(person_kind in ('skater','goalie'), 'execution breakdown lacks checked person kind')
        if person_kind == 'skater':
            fields(value, ('events','observed_goals','reference','actor','support','method_id'))
            number(value['events'],minimum=0,integer=True)
            if value['events']:
                _available_method(value['method_id'],catalogs)
            number(value['observed_goals'],minimum=0,maximum=value['events'],integer=True)
            for key in ('reference','actor'):
                comparison = value[key]
                fields(comparison, ('expected_goals','mean_opportunity','observed_minus_expected_goals'))
                number(comparison['expected_goals'],minimum=0,maximum=value['events'])
                estimate(comparison['mean_opportunity'],catalogs,probability=True)
                estimate(comparison['observed_minus_expected_goals'],catalogs)
                mean = comparison['mean_opportunity']['value']
                if value['events'] == 0:
                    require(mean is None and comparison['mean_opportunity']['unavailable_reason'] in ('no_exposure','missing_source'), 'empty paired opportunity mean lacks unavailable reason')
                    if comparison['mean_opportunity']['unavailable_reason'] == 'missing_source':
                        require(value['support']['unquantified_gap'] and any(r['code'] == 'source_unavailable' for r in value['support']['reason_counts']), 'missing paired source collection lacks located gap support')
                else:
                    require(mean is not None and close(mean,comparison['expected_goals']/value['events']), 'paired opportunity mean differs')
                residual = comparison['observed_minus_expected_goals']['value']
                require(residual is not None and close(residual,value['observed_goals']-comparison['expected_goals']), 'paired opportunity residual differs')
            support(value['support'])
            require(value['support']['included_seconds'] is None, 'paired attempt evidence invents elapsed support')
            return
        _available_method(value['method_id'],catalogs)
        fields(value, ('events','eligible_weight','observed_successes','expected_successes','probability','effect','support','method_id'))
        number(value['events'], minimum=0, integer=True)
        for key in ('eligible_weight','observed_successes','expected_successes'):
            number(value[key], minimum=0)
        require(value['observed_successes'] <= value['eligible_weight'] and value['expected_successes'] <= value['eligible_weight'], 'breakdown exceeds denominator')
        estimate(value['probability'], catalogs, probability=True)
        estimate(value['effect'], catalogs)
        support(value['support'])
        _method(value['method_id'], catalogs)
    elif table == 'adjustment_decomposition':
        names = ('baseline','self','teammates','opponents','coaching_other_context','numerical_residual','factual_prediction')
        fields(value, (*names,'method_id'))
        _method(value['method_id'], catalogs)
        for key in names:
            estimate(value[key], catalogs)
        if all(value[key]['value'] is not None for key in names):
            require(close(sum(value[key]['value'] for key in names[:-1]),value['factual_prediction']['value']), 'adjustment does not close')
            unadjusted = sum(value[key]['value'] for key in ('baseline','self','teammates','opponents','coaching_other_context'))
            require(close(value['numerical_residual']['value'],value['factual_prediction']['value']-unadjusted) and abs(value['numerical_residual']['value']) <= 1e-9+1e-9*max(abs(unadjusted),abs(value['factual_prediction']['value'])), 'adjustment residual exceeds expression arithmetic tolerance')
    elif table in ('goalie_evidence_map','goalie_danger'):
        _goalie_distribution(table,value,catalogs)
        _actual_selection(value['actual_states'],row['strength'])
    else:
        raise ValueError(f'unknown fixed payload {table}')


def _goalie_distribution(table, value, catalogs):
    from .observed_spatial import cells, cell_id, pooling
    from .shot_origins import grid
    import numpy as np

    names = ('native_cells','unmapped','totals','league_goals','league_expected_goals','display_cells','reference','support','method_id','actual_states') if table == 'goalie_evidence_map' else ('edges','attempt_counts','goal_mass','expected_goal_mass','totals','support','method_id','actual_states')
    fields(value,names)
    support(value['support'])
    _available_method(value['method_id'],catalogs)
    _evidence_mass(value['totals'])
    _actual_masses(value['actual_states'],value['totals'])
    if table == 'goalie_danger':
        require(type(value['edges']) is list and len(value['edges']) == 101 and all(type(item) in (int,float) and item == index/100 for index,item in enumerate(value['edges'])), 'wrong danger edges')
        for key, total in (('attempt_counts','attempts'),('goal_mass','goals'),('expected_goal_mass','expected_goals')):
            require(type(value[key]) is list and len(value[key]) == 100, 'wrong danger bins')
            for item in value[key]:
                number(item,minimum=0,integer=key == 'attempt_counts')
            require(close(sum(value[key]),value['totals'][total]), 'danger total differs')
        require(all(goals <= attempts and expected <= attempts for attempts,goals,expected in zip(value['attempt_counts'],value['goal_mass'],value['expected_goal_mass'])), 'danger probability mass exceeds attempts')
        for index,(count,goals,expected) in enumerate(zip(value['attempt_counts'],value['goal_mass'],value['expected_goal_mass'])):
            lower,upper = count*value['edges'][index],count*value['edges'][index+1]
            require((expected >= lower or close(expected,lower)) and (expected <= upper or close(expected,upper)) and (count > 0 or goals == expected == 0), 'danger expected mass contradicts fixed probability bin')
        return
    text(value['reference'])
    _evidence_mass(value['unmapped'])
    number(value['league_goals'],minimum=0,integer=True)
    number(value['league_expected_goals'],minimum=0)
    require(type(value['native_cells']) is list and len(value['native_cells']) == 656, 'wrong evidence native grid')
    for index,item in enumerate(value['native_cells']):
        _evidence_mass(item,cell=True)
        require(type(item['cell_id']) is int and item['cell_id'] == index, 'wrong evidence cell id')
    for key in ('goals','expected_goals','attempts'):
        require(close(sum(item[key] for item in value['native_cells'])+value['unmapped'][key],value['totals'][key]), 'evidence mass total differs')
    geometry = cells()
    positions = {item['cell_id']:index for index,item in enumerate(geometry)}
    unpooled = np.zeros((668,3))
    for item,(x,y) in zip(value['native_cells'],grid()[0]):
        unpooled[positions[cell_id(float(x),float(y))]] += [item[key] for key in ('goals','expected_goals','attempts')]
    expected = pooling() @ unpooled
    require(type(value['display_cells']) is list and len(value['display_cells']) == 668, 'wrong evidence display grid')
    for item,shape,masses in zip(value['display_cells'],geometry,expected):
        fields(item, ('cell_id','goals','expected_goals','attempts','mass_saved','ratio','unavailable_reason'))
        require(item['cell_id'] == shape['cell_id'], 'wrong evidence display id')
        for key,mass in zip(('goals','expected_goals','attempts'),masses):
            number(item[key],minimum=0)
            require(close(item[key],float(mass)), 'evidence display transport differs')
        number(item['mass_saved'])
        require(close(item['mass_saved'],item['expected_goals']-item['goals']), 'saved mass differs')
        if item['expected_goals'] > 0 and value['league_goals'] > 0 and value['league_expected_goals'] > 0:
            number(item['ratio'])
            require(item['unavailable_reason'] is None and close(item['ratio'],100*((item['goals']/item['expected_goals'])/(value['league_goals']/value['league_expected_goals'])-1)), 'goalie evidence ratio differs')
        else:
            require(item['ratio'] is None and item['unavailable_reason'] == 'no_exposure', 'undefined ratio lacks reason')


def validate_fact(table, row, catalogs, people):
    keys = KEYS[table]
    require(type(row) is dict and set(keys) <= set(row), 'fact row missing fixed primary key fields')
    year = row['season']
    season(year)
    if 'game_id' in keys:
        game_id(row['game_id'],year)
    if 'source_index' in keys:
        number(row['source_index'],minimum=0,integer=True)
    if 'player_id' in keys:
        identifier(row['player_id'])
        require((year,row['player_id']) in people, 'unknown fact person')
    if 'team_id' in row:
        if row['team_id'] is not None:
            identifier(row['team_id'])
    if 'interval_id' in keys:
        text(row['interval_id'])
    if 'population' in keys:
        require(row['population'] in CONTEXT_POPULATIONS, 'invalid context population')
    if table in ('attempt_fact','attempt_value'):
        names = (*keys,'event_id','period_number','time_seconds','team_id','shooter_id','goalie_id','actual_state','outcome','shot_type','x_ft','y_ft','location_kind','recorded_stop','recorded_stop_reason','recorded_reattempt','recorded_reattempt_reason','support_id','source') if table == 'attempt_fact' else (*keys,*ESTIMATE_FIELDS['attempt_value'],'method_id','support_id')
        fields(row,names)
        text(row['support_id'])
        require(row['support_id'] in catalogs['support'] and catalogs['support'][row['support_id']]['season'] == year and catalogs['support'][row['support_id']]['population_id'] == 'source_supported_attempts', 'attempt support differs')
        if table == 'attempt_value':
            _method(row['method_id'],catalogs)
            for field in ESTIMATE_FIELDS['attempt_value']:
                estimate(row[field],catalogs,probability=True)
            return
        number(row['event_id'],minimum=0,integer=True,nullable=True)
        number(row['period_number'],minimum=1,maximum=4,integer=True)
        number(row['time_seconds'],minimum=0,maximum=300 if row['period_number'] == 4 else 1200)
        if row['actual_state'] is not None:
            actual_state(row['actual_state'])
        require(row['outcome'] in ('goal','save','miss','block'), 'invalid attempt outcome')
        require(row['shot_type'] is None or type(row['shot_type']) is str and bool(row['shot_type'].strip()), 'invalid source shot type')
        for key,kind in (('shooter_id',None),('goalie_id','goalie')):
            if row[key] is not None:
                identifier(row[key])
            require(row[key] is None or (year,row[key]) in people and (kind is None or people[(year,row[key])]['kind'] == kind), 'attempt recipient kind differs')
        require((row['x_ft'] is None) == (row['y_ft'] is None), 'incomplete coordinate pair')
        number(row['x_ft'],minimum=-100,maximum=100,nullable=True)
        number(row['y_ft'],minimum=-42.5,maximum=42.5,nullable=True)
        if row['x_ft'] is not None:
            from .shot_origins import in_rink
            require(in_rink(row['x_ft'],row['y_ft']), 'located source event outside physical rink')
        require(row['location_kind'] in ('reported_event','block_contact','unavailable') and ((row['x_ft'] is None) == (row['location_kind'] == 'unavailable')) and (row['location_kind'] != 'block_contact' or row['outcome'] == 'block') and (row['outcome'] != 'block' or row['location_kind'] != 'reported_event'), 'invalid recorded location')
        for field in ('recorded_stop','recorded_reattempt'):
            require(row[field] is None or type(row[field]) is bool, 'invalid recorded outcome label')
            require((row[field] is None) == (row[field+'_reason'] is not None), 'recorded label lacks reason')
            if row[field+'_reason'] is not None:
                text(row[field+'_reason'])
        reference(row['source'],catalogs)
        require(row['source']['kind'] == 'source', 'source attempt lacks source provenance')
    elif table == 'attempt_setter':
        fields(row,(*keys,'pre_outcome_weight','posterior_weight','recorded_assist_evidence'))
        text(row['candidate_id'])
        require(row['candidate_id'] in ('none','unknown') or (year,row['candidate_id']) in people, 'unknown setter')
        number(row['pre_outcome_weight'],minimum=0,maximum=1)
        number(row['posterior_weight'],minimum=0,maximum=1,nullable=True)
        require(type(row['recorded_assist_evidence']) is list, 'invalid assist evidence')
        for item in row['recorded_assist_evidence']:
            reference(item,catalogs)
    elif table == 'attempt_execution_share':
        fields(row,(*keys,'goals'))
        text(row['recipient_id'])
        require(row['group'] in ('shooter','setter','goalie','coach') and ((row['group'] == 'coach') == (row['recipient_id'] == 'coaching_context')), 'invalid share group')
        if row['group'] != 'coach':
            require(row['group'] == 'setter' and row['recipient_id'] in ('none','unknown') or
                    (year,row['recipient_id']) in people and (row['group'] != 'goalie' or people[(year,row['recipient_id'])]['kind'] == 'goalie'),
                    'invalid share recipient')
        number(row['goals'])
        if row['group'] == 'setter' and (row['recipient_id'] in ('none','unknown') or people[(year,row['recipient_id'])]['kind'] == 'goalie'):
            require(row['goals'] == 0, 'neutral setter recipient has nonzero share')
    elif table == 'dressed_game':
        fields(row,(*keys,'team_id','source'))
        reference(row['source'],catalogs)
        require(row['source']['kind'] == 'source', 'dressed game lacks source')
    elif table == 'context_coverage':
        fields(row,(*keys,'availability','explanation','known_excluded_seconds','unquantified_gap','reason_counts','source_ids','method_ids'))
        disposition({key:row[key] for key in ('availability','explanation')})
        number(row['known_excluded_seconds'],minimum=0,nullable=True)
        require(type(row['unquantified_gap']) is bool, 'invalid context gap')
        reason_counts(row['reason_counts'])
        if row['availability'] == 'not_computed':
            require(row['known_excluded_seconds'] is None and row['unquantified_gap'] and not row['reason_counts'], 'pending context claims measured coverage')
        for field,catalog in (('source_ids','source'),('method_ids','method')):
            strings(row[field],ordered=True)
            require(set(row[field]) <= set(catalogs[catalog]), 'unknown context coverage reference')
    elif table == 'interval_fact':
        fields(row,(*keys,'period_number','start_seconds','end_seconds','support_id','for_mass','against_mass','on_net_for','on_net_against','period_horizon_seconds'))
        number(row['period_number'],minimum=1,maximum=4,integer=True)
        number(row['start_seconds'],minimum=0)
        number(row['end_seconds'],minimum=0,maximum=300 if row['period_number'] == 4 else 1200)
        number(row['period_horizon_seconds'],minimum=0,maximum=300 if row['period_number'] == 4 else 1200)
        require(row['end_seconds'] > row['start_seconds'] and row['end_seconds'] <= row['period_horizon_seconds'], 'empty/reversed interval or bounds exceed known period horizon')
        text(row['support_id'])
        require(row['support_id'] in catalogs['support'] and catalogs['support'][row['support_id']]['season'] == year and catalogs['support'][row['support_id']]['population_id'] == row['population'], 'interval support differs')
        for field in ('for_mass','against_mass'):
            number(row[field],minimum=0,integer=row['population'] in ('recorded_all_attempts','recorded_goals','recorded_locatable_unblocked'))
        for field in ('on_net_for','on_net_against'):
            if row['population'] == 'recorded_goals':
                number(row[field],minimum=0,integer=True)
            else:
                require(row[field] is None, 'non-goal population has on-net count')
        if row['population'] == 'recorded_goals':
            require(row['for_mass'] <= row['on_net_for'] and row['against_mass'] <= row['on_net_against'], 'goals exceed on-net')
    elif table == 'interval_player':
        fields(row,keys)
        require(people[(year,row['player_id'])]['kind'] == 'skater', 'goalie in skater membership')
    elif table == 'interval_location':
        fields(row,(*keys,'for_mass','against_mass'))
        from .observed_spatial import cells
        number(row['cell_id'],minimum=0,maximum=679,integer=True)
        require(row['population'] in ('recorded_locatable_unblocked','neutral_locatable_unblocked_value') and row['cell_id'] in {item['cell_id'] for item in cells()}, 'invalid context location')
        for key in ('for_mass','against_mass'):
            number(row[key],minimum=0,integer=row['population'] == 'recorded_locatable_unblocked')


def disposition(value):
    require(value['availability'] in ('provided','not_computed'), 'invalid availability')
    if value['availability'] == 'provided':
        require(value['explanation'] is None, 'provided result has explanation')
    else:
        text(value['explanation'])


def validate_row(table, row, family, catalogs, people):
    require(type(row) is dict, 'expected row object')
    if table in FACT_TABLES:
        validate_fact(table,row,catalogs,people)
        _method_supports(row,row['season'],catalogs)
        return
    fields(row,(*KEYS[table],'result'))
    season(row['season'])
    identifier(row['player_id'])
    require((row['season'],row['player_id']) in people, 'unknown analytical person')
    kind = people[(row['season'],row['player_id'])]['kind']
    require((kind == 'goalie') == (family == 'goalie'), 'analytical row person kind differs')
    if 'strength' in row:
        allowed = (*GOALIE_STRENGTHS,'covered_all') if table in ('goalie_observed','goalie_evidence_map','goalie_danger') else GOALIE_STRENGTHS if family == 'goalie' else SPATIAL_STRENGTHS if family == 'spatial' else EXECUTION_STRENGTHS if family == 'execution' or table == 'skater_shootiness' else ('5v5',)
        require(row['strength'] in allowed, 'invalid analytical strength')
    if table == 'analysis_map':
        require((row['map_kind'],row['strength'],row['view']) in map_keys(family), 'invalid map selector')
    elif table in ('goalie_evidence_map','goalie_danger'):
        require(row['population'] in ('unblocked','on_net'), 'invalid goalie population')
        if table == 'goalie_evidence_map':
            require(row['type'] in ('all','wrist_snap','slap','tip','backhand','other'), 'invalid goalie evidence type')
    elif table == 'execution_breakdown':
        require(row['kind'] in ('shot_type','danger') and row['stratum'] in (('wrist','snap','slap','backhand','tip','other') if row['kind'] == 'shot_type' else ('<.05','[.05,.15)','>=.15')), 'invalid execution stratum')
    elif table == 'adjustment_decomposition':
        require((row['strength'],row['target']) in required_keys(table,family), 'invalid adjustment target')
    result = row['result']
    fields(result,('availability','explanation','data'))
    disposition(result)
    if result['availability'] == 'not_computed':
        require(result['data'] is None, 'pending result has data')
        return
    require(type(result['data']) is dict, 'provided row lacks payload')
    validate_payload(table,result['data'],row,catalogs,person_kind=kind)
    _method_supports(result['data'],row['season'],catalogs)
    method_id = result['data'].get('method_id')
    if method_id is not None:
        method = catalogs['method'][method_id]
        require(method['family'] == family, 'method family differs')
        if _has_available_estimate(result['data']) and not (table == 'execution_breakdown' and kind == 'skater' and result['data']['events'] == 0):
            require(method['design_sha256'] is not None and method['training_cutoff'] is not None, 'unavailable fit supports available estimate')


def _has_available_estimate(value):
    if type(value) is dict:
        return ('uncertainty' in value and value.get('value') is not None) or any(_has_available_estimate(item) for item in value.values())
    return type(value) is list and any(_has_available_estimate(item) for item in value)


def map_keys(family):
    if family == 'spatial':
        return tuple((kind,strength,view) for strength in SPATIAL_STRENGTHS for kind in ('offense_attempts','defense_attempts','offense_xg','defense_xg') if not (strength in ('5v4','5v3','4v3','pp') and kind.startswith('defense') or strength in ('4v5','3v5','3v4','pk') and kind.startswith('offense')) for view in ('effect','complete'))
    if family == 'execution':
        return tuple((kind,strength,'effect') for kind in ('finishing','setting') for strength in EXECUTION_STRENGTHS)
    if family == 'territory':
        return (('ice_won','5v5','effect'),('ice_lost','5v5','effect'))
    return tuple(('goalie_stopping',strength,'effect') for strength in GOALIE_STRENGTHS)


@dataclass(frozen=True)
class Results:
    directory: Path
    manifest: dict
    catalogs: dict
    people: dict

    def rows(self, member, table, family=None):
        previous = None
        path = member_path(self.directory,member)
        with path.open('rb') as source:
            digest_value = hashlib.sha256()
            count = 0
            for line in source:
                digest_value.update(line)
                require(line.endswith(b'\n') and line.strip(), f'{path}: incomplete/blank jsonl record')
                row = strict_json(line)
                if family is None:
                    validate_catalog(table,row,self.manifest['purpose'],self.catalogs,self.manifest['prepared_sha256'])
                else:
                    validate_row(table,row,family,self.catalogs,self.people)
                key = tuple(row[field] for field in KEYS[table])
                require(previous is None or previous < key, f'{table}: rows duplicate or not ordered by primary key')
                previous = key
                count += 1
                yield row
            require(count == member['rows'] and digest_value.hexdigest() == member['sha256'], f'{path}: member count/digest mismatch')


def member_path(directory, member):
    fields(member,('path','sha256','rows'))
    digest(member['sha256'])
    number(member['rows'],minimum=0,integer=True)
    require(type(member['path']) is str and member['path'] and not Path(member['path']).is_absolute() and all(part not in ('','..','.') for part in member['path'].split('/')), 'unsafe member path')
    path = directory / member['path']
    require(path.resolve(strict=True).is_relative_to(directory) and path.is_file(), 'member escapes results directory or is missing')
    return path


def read_results(directory: Path) -> Results:
    return _read_results(directory, 'manifest.json')


def _read_results(directory, manifest_name):
    directory = directory.resolve(strict=True)
    manifest = strict_json((directory/manifest_name).read_bytes())
    fields(manifest,('schema_version','kind','purpose','seasons','observed_bindings','prepared_sha256','producer','catalogs','families'))
    require(type(manifest['schema_version']) is int and manifest['schema_version'] == 2 and manifest['kind'] == 'player_analysis_results' and manifest['purpose'] in ('real','fixture'), 'invalid result manifest')
    strings(manifest['seasons'],ordered=True)
    require(manifest['seasons'] and set(manifest['seasons']) <= set(SEASONS) and (manifest['purpose'] != 'real' or manifest['seasons'] == list(SEASONS)), 'invalid display seasons')
    require(type(manifest['observed_bindings']) is list and len(manifest['observed_bindings']) == len(manifest['seasons']), 'missing observed bindings')
    for year,item in zip(manifest['seasons'],manifest['observed_bindings']):
        fields(item,('season','corpus_sha256'))
        require(item['season'] == year, 'observed binding season differs')
        digest(item['corpus_sha256'])
    fields(manifest['producer'],('git_commit','git_dirty','python_version'))
    commit = manifest['producer']['git_commit']
    require(commit is None or type(commit) is str and re.fullmatch('[0-9a-f]{40}',commit) is not None, 'invalid producer commit')
    require(manifest['producer']['git_dirty'] is None or type(manifest['producer']['git_dirty']) is bool, 'invalid producer dirty flag')
    text(manifest['producer']['python_version'])
    if manifest['prepared_sha256'] is not None:
        digest(manifest['prepared_sha256'])
    fields(manifest['catalogs'],('people','sources','methods','supports'))
    catalogs = {'source':{},'method':{},'support':{}}
    people = {}
    result = Results(directory,manifest,catalogs,people)
    paths = set()
    for table,key in (('sources','source'),('methods','method'),('supports','support'),('people',None)):
        member = manifest['catalogs'][table]
        path = member_path(directory,member)
        require(path not in paths, 'duplicate member path')
        paths.add(path)
        for row in result.rows(member,table):
            if key is None:
                require(row['season'] in manifest['seasons'], 'person outside publication')
                people[(row['season'],row['player_id'])] = row
            else:
                catalogs[key][row[KEYS[table][0]]] = row
    require(type(manifest['families']) is list, 'missing family dispositions')
    inventory = []
    for family in manifest['families']:
        fields(family,('season','family','availability','explanation','tables'))
        text(family['family'])
        require(family['season'] in manifest['seasons'] and family['family'] in FAMILY_TABLES, 'invalid family disposition')
        disposition(family)
        fields(family['tables'],FAMILY_TABLES[family['family']] if family['availability'] == 'provided' else ())
        require(family['availability'] != 'provided' or manifest['prepared_sha256'] is not None, 'provided family lacks prepared identity')
        inventory.append((family['season'],family['family']))
        for table,member in family['tables'].items():
            path = member_path(directory,member)
            require(path not in paths, 'member reused across tables')
            paths.add(path)
            for row in result.rows(member,table,family['family']):
                require(row['season'] == family['season'], 'row season differs from family')
            if table not in FACT_TABLES:
                people_count = sum(person['season'] == family['season'] and ((person['kind'] == 'goalie') == (family['family'] == 'goalie')) for person in people.values())
                require(member['rows'] == people_count * len(required_keys(table,family['family'])), f'{table}: missing promised person/selector rows')
    require(inventory == sorted(set(inventory)) and set(inventory) == {(year,family) for year in manifest['seasons'] for family in FAMILY_TABLES}, 'missing/duplicate/unordered family dispositions')
    return result


def write_results(selection, catalogs, family_rows, output: Path) -> dict:
    """serialize fixed producer rows; validation precedes the final manifest write."""
    fields(selection,('purpose','seasons','observed_bindings','prepared_sha256'))
    fields(catalogs,('people','sources','methods','supports'))
    require(not output.exists() and not output.is_symlink(), 'result output exists')
    output.mkdir()
    manifest = dict(schema_version=2,kind='player_analysis_results',**selection,producer=implementation_identity(),catalogs={},families=[])
    def write_row(destination, sha, table, row, previous):
        key = tuple(row[field] for field in KEYS[table])
        require(previous is None or previous < key, f'{table}: producer rows must be sorted and unique')
        data = json_bytes(row)+b'\n'
        destination.write(data)
        sha.update(data)
        return key
    def member(path, rows, table):
        count = 0
        previous = None
        with (output/path).open('xb') as destination:
            sha = hashlib.sha256()
            for row in rows:
                previous = write_row(destination, sha, table, row, previous)
                count += 1
        return dict(path=path,sha256=sha.hexdigest(),rows=count)
    for family in family_rows:
        streamed_evidence = family.get('family') == 'evidence' and 'game_rows' in family
        fields(family,('season','family','availability','explanation','tables','game_ids','game_rows') if streamed_evidence
               else ('season','family','availability','explanation','tables'))
        require(family['season'] in SEASONS and family['family'] in FAMILY_TABLES, 'invalid producer family selector')
        disposition(family)
        require(not streamed_evidence or family['availability'] == 'provided', 'streamed evidence must be provided')
        fields(family['tables'],('context_coverage',) if streamed_evidence else
               FAMILY_TABLES[family['family']] if family['availability'] == 'provided' else ())
        record = {key:family[key] for key in ('season','family','availability','explanation')}
        if streamed_evidence:
            game_ids = family['game_ids']
            require(type(game_ids) is list and bool(game_ids) and all(type(gid) is str for gid in game_ids)
                    and game_ids == sorted(set(game_ids)), 'evidence selected games must be sorted and unique')
            game_tables = ('attempt_fact','interval_fact','interval_player','interval_location')
            paths = {table:f"{family['season']}-evidence-{table}.jsonl" for table in game_tables}
            hashes = {table:hashlib.sha256() for table in game_tables}
            counts = {table:0 for table in game_tables}
            previous = {table:None for table in game_tables}
            dressed = []
            with ExitStack() as stack:
                destinations = {table:stack.enter_context((output/path).open('xb')) for table,path in paths.items()}
                for game_id,batch in zip(game_ids,family['game_rows'],strict=True):
                    fields(batch,('game_id',*game_tables,'dressed_game'))
                    require(batch['game_id'] == game_id, 'evidence batch differs from selected game')
                    for table in (*game_tables,'dressed_game'):
                        rows = batch[table]
                        require(type(rows) is list, f'{table}: evidence batch rows must be a list')
                        for row in rows:
                            require(row['game_id'] == game_id, f'{table}: evidence row game differs')
                            if table == 'dressed_game':
                                dressed.append(row)
                            else:
                                previous[table] = write_row(destinations[table], hashes[table], table, row, previous[table])
                                counts[table] += 1
            record['tables'] = {table:dict(path=paths[table],sha256=hashes[table].hexdigest(),rows=counts[table]) for table in game_tables}
            record['tables']['dressed_game'] = member(f"{family['season']}-evidence-dressed_game.jsonl",
                sorted(dressed,key=lambda row:tuple(row[key] for key in KEYS['dressed_game'])), 'dressed_game')
            record['tables']['context_coverage'] = member(f"{family['season']}-evidence-context_coverage.jsonl",
                family['tables']['context_coverage'], 'context_coverage')
        else:
            record['tables'] = {table:member(f"{family['season']}-{family['family']}-{table}.jsonl",rows,table) for table,rows in family['tables'].items()}
        manifest['families'].append(record)
    for table,rows in catalogs.items():
        manifest['catalogs'][table] = member(table+'.jsonl',rows,table)
    staging = output/'manifest.json.incomplete'
    write_json(staging,manifest)
    _read_results(output, 'manifest.json.incomplete')
    staging.rename(output/'manifest.json')
    return manifest


def grids():
    from .shot_origins import grid
    from .observed_spatial import cells
    return (
        dict(grid_id='native656',kind='native',cells=[dict(cell_id=index,x_ft=float(x),y_ft=float(y)) for index,(x,y) in enumerate(grid()[0])]),
        dict(grid_id='display668',kind='display',mapping='rect5_gaussian10_v1',cells=[{key:item[key] for key in ('cell_id','x_min','x_max','y_min','y_max','area_sqft')} for item in cells()]),
    )


def _insert(connection, table, row):
    columns = ','.join('"'+key+'"' for key in row)
    connection.execute(f'INSERT INTO "{table}" ({columns}) VALUES ({",".join("?" for _ in row)})', tuple(row.values()))


def store_person(person, attribution=None):
    row = {key:value for key,value in person.items() if key not in ('teams','source','sweater_numbers','identity_support')}
    for key in ('teams','source','sweater_numbers','identity_support'):
        row[key+'_json'] = json_bytes(person[key]).decode()
    row['name_source_json'] = None if attribution is None else attribution['name_source_json']
    row['position_source_json'] = None if attribution is None else attribution['position_source_json']
    return row


def insert_results(connection, results):
    """insert finalized facts and fixed payloads after observed season/person insertion."""
    catalogs = results.catalogs
    for catalog,table,key in (('source','analysis_source','source_id'),('method','analysis_method','method_id')):
        for row in catalogs[catalog].values():
            _insert(connection,table,{key:row[key],'payload_json':json_bytes({field:value for field,value in row.items() if field != key}).decode()})
    for row in catalogs['support'].values():
        columns = {key:row[key] for key in ('support_id','season','population_id','policy_id')}
        _insert(connection,'analysis_support',columns|{'payload_json':json_bytes({key:value for key,value in row.items() if key not in columns}).decode()})
    for row in grids():
        _insert(connection,'analysis_grid',{'grid_id':row['grid_id'],'payload_json':json_bytes({key:value for key,value in row.items() if key != 'grid_id'}).decode()})
    # source-only evidence is inserted first. numerical supplements never determine its row set.
    families = sorted(results.manifest['families'],key=lambda row:row['family'] != 'evidence')
    for family in families:
        _insert(connection,'analysis_family',{key:family[key] for key in ('season','family','availability','explanation')})
        for table,member in family['tables'].items():
            if table in ('attempt_value','attempt_setter','attempt_execution_share'):
                continue
            for row in results.rows(member,table,family['family']):
                if table not in FACT_TABLES:
                    result = row['result']
                    payload = result['data']
                    method_id = payload.get('method_id') if payload is not None else None
                    if payload is not None:
                        payload = {key:value for key,value in payload.items() if key != 'method_id'}
                    columns = {key:row[key] for key in KEYS[table]}
                    _insert(connection,table,columns|dict(method_id=method_id,availability=result['availability'],explanation=result['explanation'],payload_json=None if payload is None else json_bytes(payload).decode()))
                elif table == 'attempt_fact':
                    columns = {key:row[key] for key in (*KEYS[table],'shooter_id','goalie_id','outcome','shot_type','support_id')}
                    state = row['actual_state']
                    strength = f"{state['attacking_skaters']}v{state['defending_skaters']}" if state is not None and state['attacking_goalie_present'] and state['defending_goalie_present'] else None
                    payload = {key:value for key,value in row.items() if key not in columns}
                    for field in ESTIMATE_FIELDS['attempt_value']:
                        payload[field] = dict(value=None,unavailable_reason='not_computed',reason_detail=dict(explanation='not computed',evidence=[]),uncertainty=dict(kind='not_estimated'))
                    _insert(connection,table,columns|dict(strength=strength,method_id=None,payload_json=json_bytes(payload).decode()))
                elif table in ('interval_fact','interval_player','interval_location'):
                    _insert(connection,table,row)
                else:
                    columns = {key:row[key] for key in (*KEYS[table],*(('team_id',) if table == 'dressed_game' else ('availability',)))}
                    _insert(connection,table,columns|{'payload_json':json_bytes({key:value for key,value in row.items() if key not in columns}).decode()})
    for family in families:
        for table,member in family['tables'].items():
            if table not in ('attempt_value','attempt_setter','attempt_execution_share'):
                continue
            for row in results.rows(member,table,family['family']):
                key = tuple(row[field] for field in ('season','game_id','source_index'))
                source = connection.execute('SELECT support_id,payload_json,outcome FROM attempt_fact WHERE season=? AND game_id=? AND source_index=?',key).fetchone()
                require(source is not None, 'supplement without source attempt')
                if table == 'attempt_value':
                    _supplement_population(row,source[2])
                    require(source[0] == row['support_id'], 'supplement/source support differs')
                    payload = strict_json(source[1].encode())
                    payload.update({field:row[field] for field in ESTIMATE_FIELDS['attempt_value']})
                    connection.execute('UPDATE attempt_fact SET method_id=?,payload_json=? WHERE season=? AND game_id=? AND source_index=?',(row['method_id'],json_bytes(payload).decode(),*key))
                else:
                    columns = {field:row[field] for field in KEYS[table]}
                    _insert(connection,table,columns|{'payload_json':json_bytes({field:value for field,value in row.items() if field not in columns}).decode()})
    check_results(connection,results)


def stored_result(row):
    payload = strict_json(row['payload_json'].encode()) if row['payload_json'] is not None else None
    if payload is not None and row['method_id'] is not None:
        payload['method_id'] = row['method_id']
    return dict(availability=row['availability'],explanation=row['explanation'],data=payload)


def required_keys(table, family):
    if table == 'analysis_map':
        return map_keys(family)
    if table == 'execution_breakdown':
        strengths = GOALIE_STRENGTHS if family == 'goalie' else EXECUTION_STRENGTHS
        return tuple((strength,kind,stratum) for strength in strengths for kind,strata in (('shot_type',('wrist','snap','slap','backhand','tip','other')),('danger',('<.05','[.05,.15)','>=.15'))) for stratum in strata)
    if table == 'adjustment_decomposition':
        return tuple((strength,target) for strength in SPATIAL_STRENGTHS for target in ('for_attempts_per60','against_attempts_per60','for_xg_per60','against_xg_per60') if not (strength in ('5v4','5v3','4v3','pp') and target.startswith('against') or strength in ('4v5','3v5','3v4','pk') and target.startswith('for')))
    if table in ('goalie_evidence_map','goalie_danger'):
        return tuple((strength,population,*((kind,) if table == 'goalie_evidence_map' else ())) for strength in (*GOALIE_STRENGTHS,'covered_all') for population in ('unblocked','on_net') for kind in (('all','wrist_snap','slap','tip','backhand','other') if table == 'goalie_evidence_map' else ('all',)))
    if table in ('goalie_result','goalie_observed'):
        return tuple((strength,) for strength in ((*GOALIE_STRENGTHS,'covered_all') if table == 'goalie_observed' else GOALIE_STRENGTHS))
    if table in ('skater_spatial','skater_execution','skater_shootiness'):
        return tuple((strength,) for strength in (SPATIAL_STRENGTHS if table == 'skater_spatial' else EXECUTION_STRENGTHS))
    return ((),)


def check_results(connection, results):
    """read back every exchange row and independently check cross-record closure."""
    import sqlite3
    connection.row_factory = sqlite3.Row
    for table,expected in (('analysis_source',results.catalogs['source']),('analysis_method',results.catalogs['method'])):
        key = 'source_id' if table == 'analysis_source' else 'method_id'
        for row in connection.execute(f'SELECT * FROM {table}'):
            require({key:row[key],**strict_json(row['payload_json'].encode())} == expected[row[key]], 'catalog read-back differs')
    for person in results.people.values():
        actual = connection.execute('SELECT * FROM person WHERE season=? AND player_id=?',(person['season'],person['player_id'])).fetchone()
        require(actual is not None, 'person read-back missing')
        restored = {key:actual[key] for key in person if key not in ('teams','source','sweater_numbers','identity_support')}
        restored.update({key:strict_json(actual[key+'_json'].encode()) for key in ('teams','source','sweater_numbers','identity_support')})
        require(restored == person, 'person scalar read-back differs')
    for row in connection.execute('SELECT * FROM analysis_support'):
        restored = {key:row[key] for key in ('support_id','season','population_id','policy_id')}
        restored.update(strict_json(row['payload_json'].encode()))
        require(restored == results.catalogs['support'][row['support_id']], 'support read-back differs')
    for expected in grids():
        actual = connection.execute('SELECT payload_json FROM analysis_grid WHERE grid_id=?',(expected['grid_id'],)).fetchone()
        require(actual is not None and {'grid_id':expected['grid_id'],**strict_json(actual[0].encode())} == expected, 'grid read-back differs')
    for family in results.manifest['families']:
        actual = connection.execute('SELECT * FROM analysis_family WHERE season=? AND family=?',(family['season'],family['family'])).fetchone()
        require(actual is not None and dict(actual) == {key:family[key] for key in ('season','family','availability','explanation')}, 'family read-back differs')
        for table,member in family['tables'].items():
            if table in FACT_TABLES:
                for expected in results.rows(member,table,family['family']):
                    storage_table = 'attempt_fact' if table == 'attempt_value' else table
                    where = ' AND '.join('"'+key+'"=?' for key in KEYS[table])
                    actual = connection.execute(f'SELECT * FROM {storage_table} WHERE {where}',tuple(expected[key] for key in KEYS[table])).fetchone()
                    require(actual is not None, f'{table}: missing fact read-back')
                    actual = dict(actual)
                    if 'payload_json' in actual:
                        payload = strict_json(actual.pop('payload_json').encode())
                        require(not (set(payload) & set(actual)), 'fact payload duplicates relational field')
                        actual.update(payload)
                    if table in ('attempt_fact','attempt_value'):
                        actual.pop('strength',None)
                    require(all(key in actual and actual[key] == value for key,value in expected.items()), f'{table}: fact read-back differs')
                continue
            for expected in results.rows(member,table,family['family']):
                where = ' AND '.join('"'+key+'"=?' for key in KEYS[table])
                actual = connection.execute(f'SELECT * FROM {table} WHERE {where}',tuple(expected[key] for key in KEYS[table])).fetchone()
                require(actual is not None and stored_result(actual) == expected['result'], f'{table}: scalar read-back differs')
            expected_count = 0
            if family['availability'] == 'provided':
                for (year,player_id),person in results.people.items():
                    if year != family['season'] or (person['kind'] == 'goalie') != (family['family'] == 'goalie'):
                        continue
                    for extra in required_keys(table,family['family']):
                        columns = KEYS[table]
                        values = (year,player_id,*extra)
                        where = ' AND '.join('"'+key+'"=?' for key in columns)
                        require(connection.execute(f'SELECT 1 FROM {table} WHERE {where}',values).fetchone() is not None, f'{table}: missing promised person/selector row')
                        expected_count += 1
                # shared tables are partitioned by their owning map kind or person kind.
                if table not in ('analysis_map','execution_breakdown'):
                    require(connection.execute(f'SELECT count(*) FROM {table} WHERE season=?',(family['season'],)).fetchone()[0] == expected_count, f'{table}: unexpected rows')
    for family in results.manifest['families']:
        if family['family'] == 'evidence' and family['availability'] == 'provided':
            for (year,player_id),person in results.people.items():
                if year == family['season'] and person['kind'] == 'skater':
                    actual = [row[0] for row in connection.execute('SELECT population FROM context_coverage WHERE season=? AND player_id=? ORDER BY population',(year,player_id))]
                    require(actual == sorted(CONTEXT_POPULATIONS), 'missing context coverage')
    _check_intervals(connection)
    require(connection.execute("SELECT 1 FROM attempt_setter s JOIN attempt_fact a USING(season,game_id,source_index) WHERE a.outcome!='goal' AND json_array_length(json_extract(s.payload_json,'$.recorded_assist_evidence'))!=0 LIMIT 1").fetchone() is None,
            'non-goal setter claims recorded assist evidence')
    for row in connection.execute('SELECT season,game_id,source_index,sum(json_extract(payload_json,\'$.pre_outcome_weight\')) total,sum(json_extract(payload_json,\'$.posterior_weight\')) posterior,count(json_extract(payload_json,\'$.posterior_weight\')) posterior_count,count(*) n FROM attempt_setter GROUP BY season,game_id,source_index'):
        require(close(row['total'],1), 'setter weights do not sum to one')
        require(row['posterior_count'] == 0 or row['posterior_count'] == row['n'] and close(row['posterior'],1), 'posterior setter weights do not sum to one')
        candidates = {r['candidate_id']:strict_json(r['payload_json'].encode()) for r in connection.execute(
            'SELECT candidate_id,payload_json FROM attempt_setter WHERE season=? AND game_id=? AND source_index=?',
            (row['season'],row['game_id'],row['source_index']))}
        require('none' in candidates and close(candidates['none']['pre_outcome_weight'],.2), 'setter none/setup prior differs')
        require('unknown' not in candidates or set(candidates) == {'none','unknown'}, 'unknown setter mixed with known candidates')
    for row in connection.execute("SELECT season,game_id,source_index,payload_json FROM attempt_fact WHERE json_extract(payload_json,'$.actor_all_attempt_opportunity.value') IS NOT NULL"):
        args = (row['season'],row['game_id'],row['source_index'])
        require(connection.execute('SELECT 1 FROM attempt_setter WHERE season=? AND game_id=? AND source_index=?',args).fetchone() is not None,
                'completed source event lacks setter branches')
        require(connection.execute('SELECT count(DISTINCT "group") FROM attempt_execution_share WHERE season=? AND game_id=? AND source_index=?',args).fetchone()[0] == 4,
                'completed source event lacks execution groups')
    for row in connection.execute('SELECT a.season,a.game_id,a.source_index,a.payload_json,count(DISTINCT s."group") groups,sum(json_extract(s.payload_json,\'$.goals\')) goals FROM attempt_fact a JOIN attempt_execution_share s USING(season,game_id,source_index) GROUP BY a.season,a.game_id,a.source_index'):
        values = strict_json(row['payload_json'].encode())
        actor = values['actor_all_attempt_opportunity']['value']
        neutral = values['neutral_all_attempt_opportunity']['value']
        require(row['groups'] == 4 and actor is not None and neutral is not None and close(row['goals'],actor-neutral), 'execution shares do not close actor-minus-neutral')
    for row in connection.execute('SELECT s."group",s.recipient_id,a.shooter_id,a.goalie_id,json_extract(a.payload_json,\'$.team_id\') shooting_team,d.team_id recipient_team FROM attempt_execution_share s JOIN attempt_fact a USING(season,game_id,source_index) LEFT JOIN dressed_game d ON d.season=s.season AND d.game_id=s.game_id AND d.player_id=s.recipient_id WHERE s."group" IN (\'shooter\',\'goalie\')'):
        if row['group'] == 'goalie':
            require(row['recipient_team'] is not None and row['shooting_team'] is not None and row['recipient_team'] != row['shooting_team'], 'unreported source goalie lacks defending dressed identity')
            require(row['goalie_id'] is None or row['recipient_id'] == row['goalie_id'], 'execution goalie share conflicts with reported source goalie')
        else:
            require(row['recipient_id'] == row['shooter_id' if row['group'] == 'shooter' else 'goalie_id'], 'execution share differs from source actor')
    for row in connection.execute('SELECT s.candidate_id,json_extract(a.payload_json,\'$.team_id\') shooting_team,d.team_id candidate_team FROM attempt_setter s JOIN attempt_fact a USING(season,game_id,source_index) LEFT JOIN dressed_game d ON d.season=s.season AND d.game_id=s.game_id AND d.player_id=s.candidate_id WHERE s.candidate_id NOT IN (\'none\',\'unknown\')'):
        require(row['candidate_team'] is not None and row['candidate_team'] == row['shooting_team'], 'named setter lacks attacking dressed identity')
    _check_maps(connection)
    _check_execution_evidence(connection)
    _check_repeated_facts(connection)


def _check_execution_evidence(connection):
    for row in connection.execute("SELECT season,player_id,strength,payload_json FROM skater_execution WHERE availability='provided'"):
        payload = strict_json(row['payload_json'].encode())
        paired = payload['paired_evidence']
        attempts = connection.execute('SELECT outcome,payload_json FROM attempt_fact WHERE season=? AND shooter_id=? AND strength=?',
                                      (row['season'],row['player_id'],row['strength'])).fetchall()
        require(len(attempts) == paired['source_attempts'], 'paired source count differs from keyed source rows')
        keyed_totals = [0,0,0.,0.]
        for attempt in attempts:
            values = strict_json(attempt['payload_json'].encode())
            reference = values['neutral_all_attempt_opportunity']['value']
            actor = values['actor_all_attempt_opportunity']['value']
            if reference is not None and actor is not None:
                for index,amount in enumerate((1,int(attempt['outcome'] == 'goal'),reference,actor)):
                    keyed_totals[index] += amount
        totals = {kind:[0,0,0.,0.] for kind in ('shot_type','danger')}
        breakdowns = connection.execute('SELECT kind,availability,payload_json FROM execution_breakdown WHERE season=? AND player_id=? AND strength=?',
                                       (row['season'],row['player_id'],row['strength'])).fetchall()
        require(len(breakdowns) == 9, 'paired execution evidence lacks fixed strata')
        for breakdown in breakdowns:
            require(breakdown['availability'] == 'provided', 'provided execution lacks paired stratum evidence')
            data = strict_json(breakdown['payload_json'].encode())
            for index,amount in enumerate((data['events'],data['observed_goals'],data['reference']['expected_goals'],data['actor']['expected_goals'])):
                totals[breakdown['kind']][index] += amount
        omitted = paired['danger_unavailable']
        require(totals['shot_type'][0] == paired['paired_attempts'], 'paired execution count differs from type totals')
        require(all(close(a,b) for a,b in zip(totals['shot_type'],keyed_totals)), 'paired execution evidence differs from keyed source/model intersection')
        require(all(close(total,totals['danger'][i]+omitted[key]) for i,(total,key) in enumerate(zip(totals['shot_type'],
                    ('events','observed_goals','reference_expected_goals','actor_expected_goals')))), 'paired execution type/danger totals differ')


def _check_intervals(connection):
    require(connection.execute("""SELECT 1 FROM person p JOIN json_each(p.teams_json) t
        LEFT JOIN player_season s USING(season,player_id)
        WHERE NOT EXISTS(SELECT 1 FROM json_each(coalesce(s.teams_json,'[]')) old WHERE json_extract(old.value,'$.id')=json_extract(t.value,'$.id'))
        AND NOT EXISTS(SELECT 1 FROM dressed_game d JOIN game g USING(season,game_id)
            WHERE d.season=p.season AND d.player_id=p.player_id AND d.team_id=json_extract(t.value,'$.id')
            AND ((d.team_id=g.away_team_id AND (g.away_abbreviation IS NULL OR g.away_abbreviation IS json_extract(t.value,'$.abbreviation')))
                OR (d.team_id=g.home_team_id AND (g.home_abbreviation IS NULL OR g.home_abbreviation IS json_extract(t.value,'$.abbreviation'))))) LIMIT 1""").fetchone() is None,
        'person affiliation lacks matching dressed-game/game-team evidence')
    require(connection.execute('SELECT 1 FROM interval_fact GROUP BY season,game_id,interval_id HAVING min(period_number)!=max(period_number) OR min(start_seconds)!=max(start_seconds) OR min(end_seconds)!=max(end_seconds) LIMIT 1').fetchone() is None, 'interval id reuses different bounds')
    require(connection.execute('SELECT 1 FROM interval_fact GROUP BY season,game_id,period_number HAVING min(period_horizon_seconds)!=max(period_horizon_seconds) LIMIT 1').fetchone() is None, 'period horizon differs across source-supported intervals')
    previous_domain = None
    previous_end = 0
    for row in connection.execute('SELECT * FROM interval_fact ORDER BY season,game_id,team_id,population,period_number,start_seconds'):
        domain = tuple(row[key] for key in ('season','game_id','team_id','population','period_number'))
        require(domain != previous_domain or row['start_seconds'] >= previous_end, 'overlapping context intervals')
        previous_domain, previous_end = domain, row['end_seconds']
        teams = connection.execute('SELECT away_team_id,home_team_id FROM game WHERE season=? AND game_id=?',(row['season'],row['game_id'])).fetchone()
        require(row['team_id'] in tuple(teams), 'context team not in game')
        membership = list(connection.execute('SELECT team_id,player_id FROM interval_player WHERE season=? AND game_id=? AND interval_id=?',(row['season'],row['game_id'],row['interval_id'])))
        require(len(membership) == 10 and len({item['player_id'] for item in membership}) == 10
                and all(sum(item['team_id'] == team for item in membership) == 5 for team in teams), 'context requires known 5+5 physical skater membership')
        if row['population'] in ('recorded_locatable_unblocked','neutral_locatable_unblocked_value'):
            totals = connection.execute('SELECT coalesce(sum(for_mass),0),coalesce(sum(against_mass),0) FROM interval_location WHERE season=? AND game_id=? AND interval_id=? AND team_id=? AND population=?',tuple(row[key] for key in ('season','game_id','interval_id','team_id','population'))).fetchone()
            require(close(totals[0],row['for_mass']) and close(totals[1],row['against_mass']), 'context map/scalar differs')
    for row in connection.execute('SELECT * FROM interval_player'):
        require(connection.execute('SELECT 1 FROM interval_fact WHERE season=? AND game_id=? AND interval_id=? AND team_id=?',tuple(row[key] for key in ('season','game_id','interval_id','team_id'))).fetchone() is not None, 'orphan interval membership')
        dressed = connection.execute('SELECT team_id FROM dressed_game WHERE season=? AND game_id=? AND player_id=?',(row['season'],row['game_id'],row['player_id'])).fetchone()
        require(dressed is not None and dressed[0] == row['team_id'], 'membership conflicts with dressed team')
    for row in connection.execute('SELECT d.*,g.away_team_id,g.home_team_id,p.teams_json,pg.team_id observed_team FROM dressed_game d JOIN game g USING(season,game_id) JOIN person p USING(season,player_id) LEFT JOIN player_game pg USING(season,player_id,game_id)'):
        require(row['team_id'] in (row['away_team_id'],row['home_team_id']) and row['team_id'] in {team['id'] for team in strict_json(row['teams_json'].encode())}, 'dressed team not in game or person affiliation')
        require(row['observed_team'] is None or row['observed_team'] == row['team_id'], 'dressed team differs from observed player-game')
    for row in connection.execute('SELECT a.*,b.for_mass paired_for,b.against_mass paired_against,b.on_net_for paired_net_for,b.on_net_against paired_net_against FROM interval_fact a LEFT JOIN interval_fact b ON a.season=b.season AND a.game_id=b.game_id AND a.interval_id=b.interval_id AND a.population=b.population AND a.team_id!=b.team_id'):
        require(row['paired_for'] is not None and close(row['for_mass'],row['paired_against']) and close(row['against_mass'],row['paired_for']) and row['on_net_for'] == row['paired_net_against'] and row['on_net_against'] == row['paired_net_for'], 'paired team interval masses are not mirrored')


def _check_maps(connection):
    for row in connection.execute("SELECT * FROM analysis_map WHERE availability='provided'"):
        payload = strict_json(row['payload_json'].encode())
        if payload['integrated_value'] is None:
            continue
        if row['map_kind'] in ('offense_attempts','defense_attempts','offense_xg','defense_xg'):
            table = 'skater_spatial'
            field = row['map_kind']+'_per60'+('_complete' if row['view'] == 'complete' else '')
        elif row['map_kind'] in ('finishing','setting'):
            table = 'skater_execution'
            field = 'finishing_goals_per100_attempts' if row['map_kind'] == 'finishing' else 'setting_goals_per100_assisted_opportunities'
        elif row['map_kind'] in ('ice_won','ice_lost'):
            table = 'skater_territory'
            field = row['map_kind']+'_goals_per_basket'
        else:
            table = 'goalie_result'
            field = 'stopping_goals_per100_on_net'
        sql = f'SELECT payload_json,availability,method_id FROM {table} WHERE season=? AND player_id=?'
        args = (row['season'],row['player_id'])
        if table != 'skater_territory':
            sql += ' AND strength=?'
            args += (row['strength'],)
        scalar = connection.execute(sql,args).fetchone()
        require(scalar is not None and scalar['availability'] == 'provided', 'available map has no scalar')
        scalar_payload = strict_json(scalar['payload_json'].encode())
        require(scalar_payload[field]['value'] is not None and close(payload['integrated_value'],scalar_payload[field]['value']) and row['method_id'] == scalar['method_id'], 'map/scalar closure or method differs')


def _check_repeated_facts(connection):
    for row in connection.execute("SELECT m.season,m.player_id,m.payload_json,s.personal_goals,s.personal_primary_assists,s.personal_included_seconds,s.personal_goals_per60,s.personal_primary_assists_per60 FROM skater_microstats m JOIN player_season s USING(season,player_id) WHERE m.availability='provided'"):
        payload = strict_json(row['payload_json'].encode())
        for field,count,rate in (('goals_per60','personal_goals','personal_goals_per60'),('primary_assists_per60','personal_primary_assists','personal_primary_assists_per60')):
            value = payload[field]
            require(value['value'] == row[rate] and value['numerator'] == row[count] and value['denominator'] == row['personal_included_seconds'], 'repeated observed personal facts differ')
    for row in connection.execute("SELECT p.payload_json penalties,d.payload_json descriptive FROM skater_penalties p JOIN skater_descriptive d USING(season,player_id) WHERE p.availability='provided' AND d.availability='provided'"):
        penalties = strict_json(row['penalties'].encode())
        descriptive = strict_json(row['descriptive'].encode())['recorded_penalties']['focal']
        for key in ('drawn','taken','served'):
            require(penalties['recorded_'+key] == descriptive[key], 'repeated recorded penalty fields differ')
    for row in connection.execute("SELECT m.payload_json microstats,d.payload_json descriptive FROM skater_microstats m JOIN skater_descriptive d USING(season,player_id) WHERE m.availability='provided' AND d.availability='provided'"):
        microstats = strict_json(row['microstats'].encode())
        scoring = strict_json(row['descriptive'].encode())['scoring_by_strength']['five_on_five']
        for key,count in (('goals_per60','goals'),('primary_assists_per60','primary_assists')):
            require(microstats[key]['value'] == scoring[key]['value'] and microstats[key]['numerator'] == scoring[count] and microstats[key]['denominator'] == scoring['seconds'], 'repeated descriptive personal facts differ')
    for row in connection.execute("SELECT l.season,l.player_id,m.payload_json FROM value_ledger l JOIN analysis_method m USING(method_id) WHERE l.availability='provided'"):
        ledger = strict_json(row['payload_json'].encode())
        for table in ('skater_spatial','skater_execution','skater_penalties','skater_territory'):
            for method in connection.execute(f"SELECT m.payload_json FROM {table} r JOIN analysis_method m USING(method_id) WHERE r.season=? AND r.player_id=? AND r.availability='provided'",(row['season'],row['player_id'])):
                component = strict_json(method[0].encode())
                require(component['reference_id'] == ledger['reference_id'] and component['support_policy_id'] == ledger['support_policy_id'], 'ledger and component policies differ')


def _actual_selection(rows, strength):
    for row in rows:
        state = row['state']
        require(state['defending_goalie_present'], 'goalie evidence without defending goalie')
        if strength == 'covered_all':
            continue
        require(state['attacking_goalie_present'], 'extra-attacker state outside covered-all evidence')
        own_strength = f"{state['defending_skaters']}v{state['attacking_skaters']}"
        allowed = ('5v5','4v4','3v3') if strength == 'ev' else ('4v5','3v5','3v4') if strength == 'pk' else (strength,)
        require(own_strength in allowed, 'actual goalie state differs from own-team strength selector')


def _actual_masses(rows, totals):
    require(type(rows) is list, 'missing actual-state evidence')
    identities = []
    for row in rows:
        fields(row, ('state','goals','expected_goals','attempts','support'))
        actual_state(row['state'])
        identities.append(json_bytes(row['state']))
        _evidence_mass({key:row[key] for key in ('goals','expected_goals','attempts')})
        support(row['support'])
    require(len(identities) == len(set(identities)), 'duplicate actual goalie evidence state')
    require(all(close(sum(row[key] for row in rows),totals[key]) for key in ('goals','expected_goals','attempts')), 'actual-state evidence does not close to totals')


def _goalie_actual_states(value, catalogs):
    rows = value['actual_states']
    require(type(rows) is list, 'missing actual goalie states')
    identities = []
    for row in rows:
        fields(row, ('state','source_counts','on_net_evidence','unblocked_evidence','stage_evidence'))
        actual_state(row['state'])
        identities.append(json_bytes(row['state']))
        _source_counts(row['source_counts'],catalogs)
        _paired(row['on_net_evidence'],catalogs,on_net=True)
        _paired(row['unblocked_evidence'],catalogs)
        _goalie_stages(row['stage_evidence'])
    require(len(identities) == len(set(identities)), 'duplicate goalie summary actual state')
    for key in ('unblocked_attempts','misses','shots_on_goal','saves','goals_against'):
        values = [row['source_counts'][key] for row in rows]
        expected = sum(values) if all(item is not None for item in values) else None
        require(value['source_counts'][key] == expected, 'actual-state source counts do not close')
    for name in ('on_net_evidence','unblocked_evidence'):
        for key in ('attempts','goals','expected_goals'):
            require(close(value[name][key],sum(row[name][key] for row in rows)), 'actual-state paired evidence does not close')
    for name,row in value['stage_evidence'].items():
        numerator = 'fractional_response_sum' if name == 'next_attempt_danger' else 'success_count'
        for key in (numerator,'eligible_count','matched_expected_sum'):
            require(close(row[key],sum(state['stage_evidence'][name][key] for state in rows)), 'actual-state stage evidence does not close')


def source_reference(value, catalogs):
    reference(value,catalogs)
    require(value['kind'] == 'source', 'source-only fact has modeled provenance')


def _supplement_population(value, outcome):
    fields = ('actor_on_net_goal_probability','neutral_goalie_on_net_goal_probability') if outcome in ('block','miss') else ()
    if outcome == 'block':
        fields += ('actor_unblocked_goal_probability',)
    require(all(value[field]['value'] is None and value[field]['unavailable_reason'] == 'not_applicable' for field in fields), 'supplement value outside its source population')


def _method_supports(value, row_season, catalogs, method_id=None):
    if type(value) is list:
        for item in value:
            _method_supports(item,row_season,catalogs,method_id)
    elif type(value) is dict:
        method_id = value.get('method_id',method_id)
        reference = value.get('id') if value.get('kind') == 'method' else value.get('method_id')
        for reference in [*value.get('method_ids',[]),*([reference] if reference is not None else [])]:
            _method(reference,catalogs)
            method = catalogs['method'][reference]
            require(all(year <= row_season for year in method['fit_seasons']), 'method fit season is later than displayed season')
            require(method['training_cutoff'] is None or method['training_cutoff'] <= row_season[4:]+'-06-30', 'method training cutoff is later than displayed season')
        if 'prior_seasons' in value:
            priors = set(value['prior_seasons'])
            require(all(year < row_season for year in priors), 'support prior season is not strictly historical')
            if priors:
                _method(method_id,catalogs)
                method = catalogs['method'][method_id]
                input_seasons = {year for item in method['inputs'] for year in item['seasons']}
                require(priors <= set(method['fit_seasons']) and priors <= input_seasons, 'support prior seasons are not bound to method inputs and fit seasons')
        for item in value.values():
            _method_supports(item,row_season,catalogs,method_id)
