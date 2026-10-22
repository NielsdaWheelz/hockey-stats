import * as Schema from "effect/Schema";
import * as HttpApi from "effect/http-api/HttpApi";
import * as HttpApiEndpoint from "effect/http-api/HttpApiEndpoint";
import * as HttpApiGroup from "effect/http-api/HttpApiGroup";
import * as HttpApiSchema from "effect/http-api/HttpApiSchema";
import {
  HockeyId,
  GameId,
  Season,
  Count,
  Rate,
  DateString,
  Timestamp,
  GitCommit,
  Team,
  AvailableSeasons,
  SeasonEvidence,
  PlayerSummary,
  PlayerGame,
  Deployment,
  SpatialSelection,
  InvalidPlayerId,
  PlayerNotFound,
  InvalidSeasonSelection,
  SeasonNotFound,
  ReadFailure,
} from "./observed.js";
import {
  parseLeagueSelection as parseLeague,
  parseMapSelection as parseMap,
  parseEvidenceSelection as parseEvidence,
} from "./player-analysis-selections.js";

import {
  Text,
  Digest,
  Id,
  Purpose,
  Family,
  FamilyAvailability,
  Publication,
} from "./publication.js";
export {
  Text,
  Digest,
  Id,
  Purpose,
  Family,
  FamilyAvailability,
  Publication,
} from "./publication.js";

export const strict = { onExcessProperty: "error" } as const;
export const PersonKind = Schema.Literals(["skater", "goalie"]);
export const Construction = Schema.Literals([
  "recorded",
  "reconstructed",
  "inferred",
  "model_valued",
  "modeled",
  "source_modeled",
]);
export const ExecutionStrength = Schema.Literals(["5v5", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4"]);
export const SpatialStrength = Schema.Literals([
  "5v5",
  "5v4",
  "5v3",
  "4v3",
  "4v5",
  "3v5",
  "3v4",
  "pp",
  "pk",
]);
export const GoalieStrength = Schema.Literals([
  "5v5",
  "4v4",
  "3v3",
  "5v4",
  "5v3",
  "4v3",
  "4v5",
  "3v5",
  "3v4",
  "ev",
  "pk",
]);
export const EvidenceStrength = Schema.Literals([
  "5v5",
  "4v4",
  "3v3",
  "5v4",
  "5v3",
  "4v3",
  "4v5",
  "3v5",
  "3v4",
  "ev",
  "pk",
  "covered_all",
]);
export const ContextPopulation = Schema.Literals([
  "recorded_all_attempts",
  "recorded_goals",
  "recorded_locatable_unblocked",
  "neutral_locatable_unblocked_value",
  "neutral_all_attempt_value",
]);
export const SupportPopulation = Schema.Literals([
  "source_supported_attempts",
  ...ContextPopulation.literals,
]);
export const ShotType = Schema.Literals(["wrist", "snap", "slap", "backhand", "tip", "other"]);
export const SourceShotType = Schema.Literals([
  "backhand",
  "bat",
  "between-legs",
  "cradle",
  "deflected",
  "poke",
  "slap",
  "snap",
  "tip-in",
  "wrap-around",
  "wrist",
  "unknown",
]);
export const EvidenceType = Schema.Literals([
  "all",
  "wrist_snap",
  "slap",
  "tip",
  "backhand",
  "other",
]);
export const EvidencePopulation = Schema.Literals(["unblocked", "on_net"]);
export const MapKind = Schema.Literals([
  "offense_attempts",
  "defense_attempts",
  "offense_xg",
  "defense_xg",
  "finishing",
  "setting",
  "ice_won",
  "ice_lost",
  "goalie_stopping",
]);
export const MapView = Schema.Literals(["effect", "complete"]);
export const Probability = Rate.check(Schema.isLessThanOrEqualTo(1));
const sortedStrings = (values: readonly string[]) =>
  values.every((value, index) => index === 0 || values[index - 1] < value);
const unique = (values: readonly unknown[]) => new Set(values).size === values.length;
export const SourceReference = Schema.Struct({ kind: Schema.Literal("source"), id: Text });
export const Reference = Schema.Struct({ kind: Schema.Literals(["source", "method"]), id: Text });
export const ReasonDetail = Schema.Struct({ explanation: Text, evidence: Schema.Array(Reference) });
export const UnavailableReason = Schema.Literals([
  "not_applicable",
  "no_exposure",
  "missing_source",
  "failed_fit",
  "not_computed",
]);
export const Uncertainty = Schema.Union([
  Schema.Struct({ kind: Schema.Literal("not_estimated") }),
  Schema.Struct({
    kind: Schema.Literal("interval"),
    lower: Schema.Finite,
    upper: Schema.Finite,
    level: Probability.check(Schema.isGreaterThan(0), Schema.isLessThan(1)),
    method: Text,
    conditional_on: Schema.Array(Text).check(Schema.isMinLength(1)),
  }).check(Schema.makeFilter((value) => value.lower <= value.upper)),
]);
const estimateFields = {
  value: Schema.NullOr(Schema.Finite),
  unavailable_reason: Schema.NullOr(UnavailableReason),
  reason_detail: Schema.NullOr(ReasonDetail),
  uncertainty: Uncertainty,
};
const validEstimate = (value: {
  value: number | null;
  unavailable_reason: typeof UnavailableReason.Type | null;
  reason_detail: typeof ReasonDetail.Type | null;
  uncertainty: typeof Uncertainty.Type;
}) =>
  value.value !== null
    ? value.unavailable_reason === null && value.reason_detail === null
    : value.unavailable_reason !== null &&
      value.reason_detail !== null &&
      value.uncertainty.kind === "not_estimated" &&
      (value.reason_detail.evidence.length > 0 ||
        ["not_computed", "not_applicable", "no_exposure"].includes(value.unavailable_reason)) &&
      (value.unavailable_reason !== "failed_fit" ||
        value.reason_detail.evidence.some((reference) => reference.kind === "method")) &&
      (value.unavailable_reason !== "missing_source" ||
        value.reason_detail.evidence.some((reference) => reference.kind === "source"));
export const Estimate = Schema.Struct(estimateFields).check(Schema.makeFilter(validEstimate));
export type Estimate = typeof Estimate.Type;
export const ProbabilityEstimate = Estimate.check(
  Schema.makeFilter((value) => value.value === null || (value.value >= 0 && value.value <= 1)),
);
export const NonnegativeEstimate = Estimate.check(
  Schema.makeFilter((value) => value.value === null || value.value >= 0),
);
export const SupportReasonCode = Schema.Literals([
  "required_source_unavailable",
  "count_accounting_conflict",
  "event_evidence_unresolved",
  "unpaired_report_attempt",
  "elapsed_membership_unresolved",
  "period_horizon_unavailable",
  "player_toi_conflict",
  "roster_identity_unresolved",
  "unassigned_player_games",
  "event_exposure_conflict",
  "shift_source_empty",
  "no_5v5_exposure",
  "no_personal_5v5_exposure",
  "personal_credit_unresolved",
  "spatial_coordinates_missing",
  "spatial_frame_unresolved",
  "spatial_location_outside_rink",
  "no_spatial_5v5_exposure",
  "source_unavailable",
  "membership_unavailable",
  "identity_conflict",
  "strength_conflict",
  "ambiguous_assignment",
  "unmatched_report_attempt",
  "clock_unavailable",
  "horizon_unavailable",
  "not_computed",
  "not_applicable",
  "no_exposure",
  "missing_source",
  "failed_fit",
  "type_unavailable",
  "context_unavailable",
  "elapsed_unavailable",
  "value_unavailable",
]);
export const ReasonCounts = Schema.Array(
  Schema.Struct({ code: SupportReasonCode, count: Count.check(Schema.isGreaterThan(0)) }),
).check(Schema.makeFilter((rows) => sortedStrings(rows.map((row) => row.code))));
export const Support = Schema.Struct({
  included_seconds: Schema.NullOr(Rate),
  events: Schema.NullOr(Count),
  eligible_weight: Schema.NullOr(Rate),
  known_excluded_seconds: Schema.NullOr(Rate),
  unquantified_gap: Schema.Boolean,
  reason_counts: ReasonCounts,
  inferred_inputs: Schema.Array(
    Schema.Literals(["blocked_origin", "setter", "territory", "historical_borrowing"]),
  ).check(Schema.makeFilter(sortedStrings)),
  current_season_information: Schema.Boolean,
  prior_only: Schema.Boolean,
  prior_seasons: Schema.Array(Season).check(Schema.makeFilter(sortedStrings)),
}).check(
  Schema.makeFilter(
    (value) =>
      !value.prior_only || (!value.current_season_information && value.prior_seasons.length > 0),
  ),
);
export type Support = typeof Support.Type;
export const Receipt = Schema.Struct({ uri: Text, sha256: Digest });
export const Source = Schema.Struct({
  source_id: Text,
  label: Text,
  purpose: Purpose,
  origin: Schema.Literals(["source_capture", "synthetic"]),
  acquisition: Schema.Literals(["admitted", "not_acquired", "access_unverified"]),
  construction: Construction,
  population: Text,
  definition: Text,
  receipts: Schema.Array(Receipt),
  limitations: Schema.Array(Text),
}).check(
  Schema.makeFilter(
    (value) =>
      (value.origin !== "synthetic" || value.purpose === "fixture") &&
      (value.acquisition === "admitted" ? value.receipts.length > 0 : value.limitations.length > 0),
  ),
);
export type Source = typeof Source.Type;
export const QuantityPath = Schema.Literals([
  "skater_spatial.offense_attempts_per60",
  "skater_spatial.defense_attempts_per60",
  "skater_spatial.offense_xg_per60",
  "skater_spatial.defense_xg_per60",
  "skater_spatial.offense_attempts_per60_complete",
  "skater_spatial.defense_attempts_per60_complete",
  "skater_spatial.offense_xg_per60_complete",
  "skater_spatial.defense_xg_per60_complete",
  "skater_spatial.offense_attempts_per60_neutral",
  "skater_spatial.defense_attempts_per60_neutral",
  "skater_spatial.offense_xg_per60_neutral",
  "skater_spatial.defense_xg_per60_neutral",
  "skater_spatial.offense_attempts_relative_percent",
  "skater_spatial.defense_attempts_relative_percent",
  "skater_spatial.offense_xg_relative_percent",
  "skater_spatial.defense_xg_relative_percent",
  "skater_execution.finishing_goals_per100_attempts",
  "skater_execution.setting_goals_per100_assisted_opportunities",
  "skater_execution.avoid_block_probability",
  "skater_execution.on_net_probability",
  "skater_execution.recorded_stop_probability",
  "skater_execution.conversion_probability",
  "skater_execution.avoid_block_probability_difference",
  "skater_execution.on_net_probability_difference",
  "skater_execution.recorded_stop_probability_difference",
  "skater_execution.conversion_probability_difference",
  "skater_shootiness.probability",
  "skater_shootiness.neutral_probability",
  "skater_shootiness.difference",
  "skater_penalties.drawn_per60",
  "skater_penalties.taken_per60",
  "skater_penalties.drawn_value_per60",
  "skater_penalties.taken_value_per60",
  "skater_territory.ice_won_goals_per_basket",
  "skater_territory.ice_lost_goals_per_basket",
  "skater_territory.exit_offense.hazard_per_second",
  "skater_territory.exit_offense.one_second_probability",
  "skater_territory.entry_offense.hazard_per_second",
  "skater_territory.entry_offense.one_second_probability",
  "skater_territory.zone_retention.opponent_exit_hazard_per_second",
  "skater_territory.zone_retention.one_second_probability",
  "skater_territory.entry_prevention.opponent_entry_hazard_per_second",
  "skater_territory.entry_prevention.one_second_probability",
  "goalie_result.stopping_goals_per100_on_net",
  "goalie_result.miss_probability",
  "goalie_result.recorded_stop_probability",
  "goalie_result.conversion_probability",
  "goalie_result.recorded_reattempt_probability",
  "goalie_result.reattempt_neutral_goal_probability",
  "goalie_result.followup_danger",
  "goalie_result.miss_probability_difference",
  "goalie_result.recorded_stop_probability_difference",
  "goalie_result.conversion_probability_difference",
  "goalie_result.recorded_reattempt_probability_difference",
  "goalie_result.reattempt_neutral_goal_probability_difference",
  "goalie_result.followup_danger_difference",
  "goalie_observed.on_net_evidence.expected_goals",
  "goalie_observed.on_net_evidence.goals_saved_above_expected",
  "goalie_observed.on_net_evidence.goals_per100_expected",
  "goalie_observed.on_net_evidence.mean_goal_probability",
  "goalie_observed.on_net_evidence.league_mean_goal_probability",
  "goalie_observed.on_net_evidence.difficulty_relative_percent",
  "goalie_observed.on_net_evidence.expected_save_fraction",
  "goalie_observed.unblocked_evidence.expected_goals",
  "goalie_observed.unblocked_evidence.goals_saved_above_expected",
  "goalie_observed.unblocked_evidence.goals_per100_expected",
  "goalie_observed.unblocked_evidence.mean_goal_probability",
  "goalie_observed.unblocked_evidence.league_mean_goal_probability",
  "goalie_observed.unblocked_evidence.difficulty_relative_percent",
  "goalie_observed.stage_evidence.miss",
  "goalie_observed.stage_evidence.recorded_stop",
  "goalie_observed.stage_evidence.conversion",
  "goalie_observed.stage_evidence.reattempt",
  "goalie_observed.stage_evidence.next_attempt_danger",
  "analysis_map.integrated_value",
  "analysis_map.cells",
  "analysis_map.display_cells.mass",
  "analysis_map.display_cells.density_per100sqft",
  "execution_breakdown.probability",
  "execution_breakdown.effect",
  "execution_breakdown.expected_successes",
  "adjustment_decomposition.baseline",
  "adjustment_decomposition.self",
  "adjustment_decomposition.teammates",
  "adjustment_decomposition.opponents",
  "adjustment_decomposition.coaching_other_context",
  "adjustment_decomposition.numerical_residual",
  "adjustment_decomposition.factual_prediction",
  "goalie_evidence_map.totals.expected_goals",
  "goalie_evidence_map.native_cells.expected_goals",
  "goalie_evidence_map.unmapped.expected_goals",
  "goalie_evidence_map.display_cells.mass_saved",
  "goalie_evidence_map.display_cells.ratio",
  "goalie_danger.expected_goal_mass",
  "goalie_danger.totals.expected_goals",
  "attempt_value.actor_all_attempt_opportunity",
  "attempt_value.neutral_all_attempt_opportunity",
  "attempt_value.actor_unblocked_goal_probability",
  "attempt_value.actor_on_net_goal_probability",
  "attempt_value.neutral_goalie_on_net_goal_probability",
  "skater_microstats.reference_xg_per60",
  "skater_microstats.primary_pass_xg_per60",
  "skater_microstats.puck_management_xga_saved_per100_plays",
  "value_ledger.league_total",
  "value_ledger.replacement_total",
  "value_ledger.penalties_combined.league_goals",
  "value_ledger.penalties_combined.replacement_goals",
  "value_ledger.components.five_on_five_offense.league_goals",
  "value_ledger.components.five_on_five_offense.replacement_goals",
  "value_ledger.components.five_on_five_defense.league_goals",
  "value_ledger.components.five_on_five_defense.replacement_goals",
  "value_ledger.components.power_play_offense.league_goals",
  "value_ledger.components.power_play_offense.replacement_goals",
  "value_ledger.components.penalty_kill_defense.league_goals",
  "value_ledger.components.penalty_kill_defense.replacement_goals",
  "value_ledger.components.finishing.league_goals",
  "value_ledger.components.finishing.replacement_goals",
  "value_ledger.components.setting.league_goals",
  "value_ledger.components.setting.replacement_goals",
  "value_ledger.components.penalties_drawn.league_goals",
  "value_ledger.components.penalties_drawn.replacement_goals",
  "value_ledger.components.penalties_taken.league_goals",
  "value_ledger.components.penalties_taken.replacement_goals",
  "value_ledger.components.ice_won.league_goals",
  "value_ledger.components.ice_won.replacement_goals",
  "value_ledger.components.ice_lost.league_goals",
  "value_ledger.components.ice_lost.replacement_goals",
]);
export const Method = Schema.Struct({
  method_id: Text,
  family: Family,
  purpose: Purpose,
  recipe_id: Text,
  design_sha256: Schema.NullOr(Digest),
  input_sha256: Digest,
  fit_seasons: Schema.Array(Season).check(Schema.makeFilter(sortedStrings)),
  training_cutoff: Schema.NullOr(DateString),
  target: Text,
  population: Text,
  reference: Text,
  limitations: Schema.Array(Text),
  evidence: Schema.Array(Receipt),
  inputs: Schema.Array(
    Schema.Struct({
      role: Schema.Literals([
        "prepared",
        "coaches",
        "annual_state",
        "opportunity_panel",
        "source_results",
        "predecessor",
      ]),
      sha256: Digest,
      seasons: Schema.Array(Season).check(Schema.makeFilter(sortedStrings)),
    }),
  ),
  reference_id: Text,
  support_policy_id: Text,
  assessment: Schema.Struct({
    status: Schema.Literal("experimental"),
    findings: Schema.Array(
      Schema.Struct({
        quantities: Schema.Array(QuantityPath).check(
          Schema.isMinLength(1),
          Schema.makeFilter(unique),
        ),
        population: Text,
        summary: Text,
        evidence: Schema.Array(Schema.Struct({ uri: Text, sha256: Schema.NullOr(Digest) })),
      }),
    ),
  }),
}).check(
  Schema.makeFilter(
    (value) =>
      (value.design_sha256 !== null && value.training_cutoff !== null) ||
      (value.evidence.length > 0 && value.assessment.findings.length > 0),
  ),
);
export type Method = typeof Method.Type;
export const SupportDefinition = Schema.Struct({
  support_id: Text,
  season: Season,
  population_id: SupportPopulation,
  policy_id: Text,
  definition: Text,
  source_ids: Schema.Array(Text).check(Schema.makeFilter(sortedStrings)),
  method_ids: Schema.Array(Text).check(Schema.makeFilter(sortedStrings)),
});
export type SupportDefinition = typeof SupportDefinition.Type;
export const IdentityField = Schema.Literals([
  "display_name",
  "reported_position",
  "teams",
  "birth_date",
  "age_as_of",
  "age_years",
  "height_cm",
  "handedness",
  "sweater_numbers",
]);
export const Person = Schema.Struct({
  season: Season,
  player_id: Id,
  kind: PersonKind,
  display_name: Schema.NullOr(Text),
  reported_position: Schema.NullOr(Schema.Literals(["C", "L", "R", "F", "D", "G"])),
  teams: Schema.Array(Team).check(Schema.makeFilter((rows) => unique(rows.map((row) => row.id)))),
  source: Schema.Array(Reference),
  birth_date: Schema.NullOr(DateString),
  age_as_of: DateString,
  age_years: Schema.NullOr(Rate),
  height_cm: Schema.NullOr(Rate.check(Schema.isGreaterThan(0))),
  handedness: Schema.NullOr(Schema.Literals(["L", "R"])),
  sweater_numbers: Schema.Array(
    Schema.Struct({
      team_id: Id,
      game_id: GameId,
      number: Schema.String.check(Schema.isPattern(/^[0-9]{1,2}$/)),
    }),
  ),
  identity_support: Schema.Struct({
    problems: Schema.Array(Schema.Struct({ field: IdentityField, code: Text, explanation: Text })),
    evidence: Schema.Array(Reference),
  }),
}).check(
  Schema.makeFilter(
    (value) =>
      (value.reported_position === null ||
        (value.kind === "goalie") === (value.reported_position === "G")) &&
      value.age_as_of === `${value.season.slice(4)}-02-01` &&
      (value.birth_date === null
        ? value.age_years === null
        : Date.parse(value.birth_date) <= Date.parse(value.age_as_of) &&
          (value.age_years === null ||
            close(
              value.age_years,
              (Date.parse(value.age_as_of) - Date.parse(value.birth_date)) / 86400000 / 365.25,
            ))) &&
      unique(value.sweater_numbers.map((row) => `${row.team_id}:${row.game_id}:${row.number}`)) &&
      (value.teams.length > 0 ||
        value.identity_support.problems.some((problem) => problem.field === "teams")) &&
      (
        [
          "display_name",
          "reported_position",
          "birth_date",
          "age_years",
          "height_cm",
          "handedness",
        ] as const
      ).every(
        (field) =>
          value[field] !== null ||
          value.identity_support.problems.some((problem) => problem.field === field),
      ),
  ),
);
export type Person = typeof Person.Type;
const factFields = {
  ...estimateFields,
  support: Support,
  unit: Text,
  numerator: Schema.NullOr(Rate),
  denominator: Schema.NullOr(Rate),
  denominator_kind: Schema.Literals([
    "included_seconds",
    "opponent_attempts",
    "tracked_plays",
    "none",
  ]),
  construction: Construction,
  provenance: Reference,
};
export const FactValue = Schema.Struct(factFields).check(
  Schema.makeFilter(
    (value) =>
      validEstimate(value) &&
      !value.support.prior_only &&
      value.support.prior_seasons.length === 0 &&
      (value.construction === "recorded" ||
      value.construction === "reconstructed" ||
      value.construction === "source_modeled"
        ? value.provenance.kind === "source"
        : value.provenance.kind === "method"),
  ),
);
export type FactValue = typeof FactValue.Type;
const fact = (
  unit: string,
  denominator: typeof factFields.denominator_kind.Type,
  fraction = false,
) =>
  FactValue.check(
    Schema.makeFilter((value) => {
      if (value.unit !== unit || value.denominator_kind !== denominator) return false;
      if (value.value === null) return true;
      if (unit !== "xga_saved_per100_plays" && value.value < 0) return false;
      if (fraction && value.value > 1) return false;
      if (denominator === "none")
        return unit === "mph"
          ? value.numerator === null && value.denominator === null
          : value.denominator === null &&
              value.numerator !== null &&
              Number.isSafeInteger(value.numerator) &&
              Number.isSafeInteger(value.value) &&
              value.value === value.numerator;
      if (value.denominator === null || value.denominator <= 0) return false;
      if (unit === "xga_saved_per100_plays")
        return value.numerator === null && value.construction === "source_modeled";
      if (value.numerator === null) return false;
      if (
        denominator === "included_seconds" &&
        value.support.included_seconds !== value.denominator
      )
        return false;
      return close(
        value.value,
        unit === "per60"
          ? per60(value.numerator, value.denominator)!
          : value.numerator / value.denominator,
      );
    }),
  );
const per60Fact = fact("per60", "included_seconds");
const fractionFact = fact("fraction", "opponent_attempts", true);
const trackingFraction = fact("fraction", "tracked_plays", true);
export const SkaterMicrostats = Schema.Struct({
  goals_per60: per60Fact,
  primary_assists_per60: per60Fact,
  unblocked_attempts_per60: per60Fact,
  hits_per60: per60Fact,
  reference_xg_per60: per60Fact,
  blocked_attempt_share: fractionFact,
  primary_pass_xg_per60: per60Fact,
  primary_shot_assists_per60: per60Fact,
  in_zone_attempts_per60: per60Fact,
  rush_attempts_per60: per60Fact,
  high_danger_pass_attempts_per60: per60Fact,
  in_zone_shot_assists_per60: per60Fact,
  rush_shot_assists_per60: per60Fact,
  high_danger_passes_per60: per60Fact,
  zone_entries_per60: per60Fact,
  possession_entries_per60: per60Fact,
  zone_exits_per60: per60Fact,
  possession_exits_per60: per60Fact,
  forecheck_involvements_per60: per60Fact,
  defensive_zone_touches_per60: per60Fact,
  pass_exits_per60: per60Fact,
  carry_exits_per60: per60Fact,
  defensive_zone_retrievals_per60: per60Fact,
  successful_retrievals_per60: per60Fact,
  shot_assisting_passes_per60: per60Fact,
  puck_management_xga_saved_per100_plays: fact("xga_saved_per100_plays", "tracked_plays"),
  entry_denial_fraction: trackingFraction,
  possession_entry_denial_fraction: trackingFraction,
  skating_max_speed_mph: fact("mph", "none"),
  skating_bursts_over20_count: fact("count", "none"),
});
export type SkaterMicrostats = typeof SkaterMicrostats.Type;
const reportedUsageFields = {
  positive_toi_appearances: Count,
  reported_seconds: Schema.NullOr(Rate),
  minutes_per_appearance: NonnegativeEstimate,
  reported_shifts: Schema.NullOr(Count),
  listed_games: Count,
  supported_games: Count,
  missing_games: Count,
  support: Support,
};
export const ReportedUsage = Schema.Struct({
  provenance: SourceReference,
  ...reportedUsageFields,
  teams: Schema.Array(Schema.Struct({ team_id: Id, ...reportedUsageFields })).check(
    Schema.makeFilter((rows) => unique(rows.map((row) => row.team_id))),
  ),
}).check(
  Schema.makeFilter(
    (value) =>
      value.supported_games + value.missing_games === value.listed_games &&
      value.positive_toi_appearances <= value.supported_games &&
      (value.minutes_per_appearance.value === null ||
        (value.reported_seconds !== null &&
          value.positive_toi_appearances > 0 &&
          close(
            value.minutes_per_appearance.value,
            value.reported_seconds / (60 * value.positive_toi_appearances),
          ))),
  ),
);
export const ActualState = Schema.Struct({
  attacking_skaters: Count.check(Schema.isLessThanOrEqualTo(6)),
  defending_skaters: Count.check(Schema.isLessThanOrEqualTo(6)),
  attacking_goalie_present: Schema.Boolean,
  defending_goalie_present: Schema.Boolean,
});
const validUsage = (value: {
  seconds: number | null;
  appearances: number;
  minutes_per_appearance: Estimate;
}) =>
  value.minutes_per_appearance.value === null ||
  (value.seconds !== null &&
    value.appearances > 0 &&
    close(value.minutes_per_appearance.value, value.seconds / (60 * value.appearances)));
const usageGroup = Schema.Struct({
  seconds: Schema.NullOr(Rate),
  appearances: Count,
  minutes_per_appearance: NonnegativeEstimate,
  support: Support,
}).check(Schema.makeFilter(validUsage));
const strengthGroups = {
  ev: usageGroup,
  pp: usageGroup,
  pk: usageGroup,
  other: usageGroup,
  five_on_five: usageGroup,
};
export const StrengthUsage = Schema.Struct({
  ...strengthGroups,
  states: Schema.Array(
    Schema.Struct({ state: ActualState, ...usageGroup.fields }).check(
      Schema.makeFilter(validUsage),
    ),
  ).check(Schema.makeFilter((rows) => unique(rows.map((row) => JSON.stringify(row.state))))),
});
const validScoring = (value: {
  goals: number | null;
  primary_assists: number | null;
  primary_points: number | null;
  seconds: number | null;
  goals_per60: Estimate;
  primary_assists_per60: Estimate;
  primary_points_per60: Estimate;
}) =>
  (value.goals === null ||
    value.primary_assists === null ||
    value.primary_points === value.goals + value.primary_assists) &&
  (
    [
      [value.goals_per60, value.goals],
      [value.primary_assists_per60, value.primary_assists],
      [value.primary_points_per60, value.primary_points],
    ] as const
  ).every(
    ([estimate, count]) =>
      estimate.value === null ||
      (count !== null &&
        value.seconds !== null &&
        value.seconds > 0 &&
        close(estimate.value, per60(count, value.seconds)!)),
  );
const scoringGroup = Schema.Struct({
  goals: Schema.NullOr(Count),
  primary_assists: Schema.NullOr(Count),
  primary_points: Schema.NullOr(Count),
  seconds: Schema.NullOr(Rate),
  goals_per60: NonnegativeEstimate,
  primary_assists_per60: NonnegativeEstimate,
  primary_points_per60: NonnegativeEstimate,
  support: Support,
}).check(Schema.makeFilter(validScoring));
export const ScoringByStrength = Schema.Struct({
  ev: scoringGroup,
  pp: scoringGroup,
  pk: scoringGroup,
  other: scoringGroup,
  five_on_five: scoringGroup,
  states: Schema.Array(
    Schema.Struct({ state: ActualState, ...scoringGroup.fields }).check(
      Schema.makeFilter(validScoring),
    ),
  ),
  unclassified: Schema.Struct({
    goals: Schema.NullOr(Count),
    primary_assists: Schema.NullOr(Count),
    primary_points: Schema.NullOr(Count),
    support: Support,
  }),
});
const validOnOff = (value: {
  for_count: number | null;
  against_count: number | null;
  seconds: number | null;
  for_per60: Estimate;
  against_per60: Estimate;
  share_minus_half: Estimate;
}) => {
  const rates = [
    [value.for_per60, value.for_count],
    [value.against_per60, value.against_count],
  ] as const;
  return (
    rates.every(
      ([estimate, count]) =>
        estimate.value === null ||
        (count !== null &&
          value.seconds !== null &&
          value.seconds > 0 &&
          close(estimate.value, per60(count, value.seconds)!)),
    ) &&
    (value.share_minus_half.value === null ||
      (value.for_count !== null &&
        value.against_count !== null &&
        value.for_count + value.against_count > 0 &&
        close(
          value.share_minus_half.value,
          100 * (value.for_count / (value.for_count + value.against_count) - 0.5),
        )))
  );
};
export const OnOffGroup = Schema.Struct({
  for_count: Schema.NullOr(Count),
  against_count: Schema.NullOr(Count),
  seconds: Schema.NullOr(Rate),
  for_per60: NonnegativeEstimate,
  against_per60: NonnegativeEstimate,
  share_minus_half: Estimate,
  support: Support,
}).check(Schema.makeFilter(validOnOff));
const onOff = Schema.Struct({ on: OnOffGroup, off: OnOffGroup, league: OnOffGroup });
const goalOnOffGroup = Schema.Struct({
  ...OnOffGroup.fields,
  on_net_for: Schema.NullOr(Count),
  on_net_against: Schema.NullOr(Count),
}).check(
  Schema.makeFilter(
    (value) =>
      validOnOff(value) &&
      (value.for_count === null ||
        value.on_net_for === null ||
        value.for_count <= value.on_net_for) &&
      (value.against_count === null ||
        value.on_net_against === null ||
        value.against_count <= value.on_net_against),
  ),
);
const goalOnOff = Schema.Struct({
  on: goalOnOffGroup,
  off: goalOnOffGroup,
  league: goalOnOffGroup,
});
const conversion = Schema.Struct({
  goals_for: Schema.NullOr(Count),
  goals_against: Schema.NullOr(Count),
  on_net_for: Schema.NullOr(Count),
  on_net_against: Schema.NullOr(Count),
  shooting_for: ProbabilityEstimate,
  shooting_against: ProbabilityEstimate,
  save_fraction: ProbabilityEstimate,
  support: Support,
}).check(
  Schema.makeFilter((value) => {
    const ratios = [
      [value.shooting_for, value.goals_for, value.on_net_for, false],
      [value.shooting_against, value.goals_against, value.on_net_against, false],
      [value.save_fraction, value.goals_against, value.on_net_against, true],
    ] as const;
    return ratios.every(
      ([estimate, numerator, denominator, complement]) =>
        estimate.value === null ||
        (numerator !== null &&
          denominator !== null &&
          denominator > 0 &&
          numerator <= denominator &&
          close(
            estimate.value,
            complement ? 1 - numerator / denominator : numerator / denominator,
          )),
    );
  }),
);
const penaltyRecord = Schema.Struct({
  count: Schema.NullOr(Count),
  reported_seconds: Schema.NullOr(Rate),
  per1000minutes: NonnegativeEstimate,
  categories: Schema.Array(Schema.Struct({ code: Text, count: Count })).check(
    Schema.makeFilter((rows) => sortedStrings(rows.map((row) => row.code))),
  ),
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      (value.count === null ||
        value.categories.reduce((sum, row) => sum + row.count, 0) === value.count) &&
      (value.per1000minutes.value === null ||
        (value.reported_seconds !== null &&
          value.reported_seconds > 0 &&
          value.count !== null &&
          close(value.per1000minutes.value, (60000 * value.count) / value.reported_seconds))),
  ),
);
const penaltySet = Schema.Struct({
  drawn: penaltyRecord,
  taken: penaltyRecord,
  served: penaltyRecord,
});
const startBin = Schema.Struct({ count: Schema.NullOr(Count), share: ProbabilityEstimate });
const scoreBin = Schema.Struct({ seconds: Schema.NullOr(Rate), share: ProbabilityEstimate });
const deploymentRecord = Schema.Struct({
  shift_starts: Schema.Struct({
    offensive: startBin,
    neutral: startBin,
    defensive: startBin,
    on_the_fly: startBin,
    unknown: startBin,
  }),
  score: Schema.Struct({
    leading: scoreBin,
    tied: scoreBin,
    trailing: scoreBin,
    unknown: scoreBin,
  }),
  support: Support,
});
export const SkaterDescriptive = Schema.Struct({
  provenance: SourceReference,
  reported_usage: ReportedUsage,
  strength_usage: StrengthUsage,
  scoring_by_strength: ScoringByStrength,
  on_off_attempts: onOff,
  on_off_goals: goalOnOff,
  on_ice_conversion: Schema.Struct({ focal: conversion, team: conversion, league: conversion }),
  recorded_penalties: Schema.Struct({ focal: penaltySet, team: penaltySet, league: penaltySet }),
  deployment: Schema.Struct({
    focal: deploymentRecord,
    team: deploymentRecord,
    league: deploymentRecord,
  }),
});
export type SkaterDescriptive = typeof SkaterDescriptive.Type;
const band = Schema.Struct({
  band: Count.check(Schema.isGreaterThan(0)),
  counterparts: Count,
  slot_seconds: Rate,
});
const counterpart = (bands: number) =>
  Schema.Struct({
    usage_minutes_per_appearance: NonnegativeEstimate,
    mean_band_index: NonnegativeEstimate,
    known_slot_seconds: Rate,
    all_slot_seconds: Rate,
    unique_counterparts: Count,
    bands: Schema.Array(band).check(
      Schema.makeFilter(
        (rows) => rows.length === bands && rows.every((row, index) => row.band === index + 1),
      ),
    ),
    coverage: Support,
  }).check(
    Schema.makeFilter(
      (value) =>
        value.known_slot_seconds <= value.all_slot_seconds &&
        (value.usage_minutes_per_appearance.value === null || value.known_slot_seconds > 0),
    ),
  );
const counterpartUsage = Schema.Struct({
  usage_minutes_per_appearance: NonnegativeEstimate,
  known_slot_seconds: Rate,
  all_slot_seconds: Rate,
  unique_counterparts: Count,
  forward: counterpart(4),
  defense: counterpart(3),
  coverage: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      value.known_slot_seconds <= value.all_slot_seconds &&
      (value.usage_minutes_per_appearance.value === null || value.known_slot_seconds > 0),
  ),
);
export const SkaterContext = Schema.Struct({
  provenance: SourceReference,
  teammates: counterpartUsage,
  opponents: counterpartUsage,
});
export type SkaterContext = typeof SkaterContext.Type;
const stateWeights = Schema.Array(
  Schema.Struct({ strength: ExecutionStrength, weight: Probability }),
).check(
  Schema.makeFilter(
    (rows) =>
      unique(rows.map((row) => row.strength)) &&
      rows.length > 0 &&
      Math.abs(rows.reduce((sum, row) => sum + row.weight, 0) - 1) <= 1e-9,
  ),
);
export const SkaterSpatial = Schema.Struct({
  offense_attempts_per60: Estimate,
  defense_attempts_per60: Estimate,
  offense_xg_per60: Estimate,
  defense_xg_per60: Estimate,
  offense_attempts_per60_complete: NonnegativeEstimate,
  defense_attempts_per60_complete: NonnegativeEstimate,
  offense_xg_per60_complete: NonnegativeEstimate,
  defense_xg_per60_complete: NonnegativeEstimate,
  offense_attempts_per60_neutral: NonnegativeEstimate,
  defense_attempts_per60_neutral: NonnegativeEstimate,
  offense_xg_per60_neutral: NonnegativeEstimate,
  defense_xg_per60_neutral: NonnegativeEstimate,
  offense_attempts_relative_percent: Estimate,
  defense_attempts_relative_percent: Estimate,
  offense_xg_relative_percent: Estimate,
  defense_xg_relative_percent: Estimate,
  state_weights: stateWeights,
  support: Support,
  method_id: Text,
})
  .check(
    Schema.makeFilter((value) =>
      (["offense", "defense"] as const).every((role) =>
        (["complete", "neutral"] as const).every((reference) => {
          const attempts = value[`${role}_attempts_per60_${reference}`].value;
          const xg = value[`${role}_xg_per60_${reference}`].value;
          return attempts === null || xg === null || (xg > 0 && xg <= attempts);
        }),
      ),
    ),
  )
  .check(
    Schema.makeFilter((value) =>
      (["offense", "defense"] as const).every((role) =>
        (["attempts", "xg"] as const).every((quantity) => {
          const effect = value[`${role}_${quantity}_per60`].value;
          const complete = value[`${role}_${quantity}_per60_complete`].value;
          const neutral = value[`${role}_${quantity}_per60_neutral`].value;
          const percent = value[`${role}_${quantity}_relative_percent`].value;
          return (
            (effect === null ||
              (complete !== null && neutral !== null && close(effect, complete - neutral))) &&
            (percent === null ||
              (effect !== null &&
                neutral !== null &&
                neutral > 0 &&
                close(percent, (100 * effect) / neutral)))
          );
        }),
      ),
    ),
  );
const executionStages = {
  avoid_block_probability: ProbabilityEstimate,
  on_net_probability: ProbabilityEstimate,
  recorded_stop_probability: ProbabilityEstimate,
  conversion_probability: ProbabilityEstimate,
};
const executionFields = {
  finishing_goals_per100_attempts: Estimate,
  setting_goals_per100_assisted_opportunities: Estimate,
  ...executionStages,
  avoid_block_probability_difference: Estimate,
  on_net_probability_difference: Estimate,
  recorded_stop_probability_difference: Estimate,
  conversion_probability_difference: Estimate,
};
const executionSupport = Schema.Struct({
  finishing_goals_per100_attempts: Support,
  setting_goals_per100_assisted_opportunities: Support,
  avoid_block_probability: Support,
  on_net_probability: Support,
  recorded_stop_probability: Support,
  conversion_probability: Support,
  avoid_block_probability_difference: Support,
  on_net_probability_difference: Support,
  recorded_stop_probability_difference: Support,
  conversion_probability_difference: Support,
});
export const SkaterExecution = Schema.Struct({
  ...executionFields,
  support: executionSupport,
  method_id: Text,
});
export const SkaterShootiness = Schema.Struct({
  probability: ProbabilityEstimate,
  neutral_probability: ProbabilityEstimate,
  difference: Estimate,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter(
    (value) =>
      value.difference.value === null ||
      (value.probability.value !== null &&
        value.neutral_probability.value !== null &&
        close(value.difference.value, value.probability.value - value.neutral_probability.value)),
  ),
);
export const SkaterPenalties = Schema.Struct({
  drawn_per60: Estimate,
  taken_per60: Estimate,
  drawn_value_per60: Estimate,
  taken_value_per60: Estimate,
  recorded_drawn: penaltyRecord,
  recorded_taken: penaltyRecord,
  recorded_served: penaltyRecord,
  support: Support,
  method_id: Text,
});
const transition = Schema.Struct({
  hazard_per_second: NonnegativeEstimate,
  one_second_probability: ProbabilityEstimate,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      value.one_second_probability.value === null ||
      (value.hazard_per_second.value !== null &&
        close(value.one_second_probability.value, 1 - Math.exp(-value.hazard_per_second.value))),
  ),
);
const exitAvoidance = Schema.Struct({
  opponent_exit_hazard_per_second: NonnegativeEstimate,
  one_second_probability: ProbabilityEstimate,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      value.one_second_probability.value === null ||
      (value.opponent_exit_hazard_per_second.value !== null &&
        close(
          value.one_second_probability.value,
          Math.exp(-value.opponent_exit_hazard_per_second.value),
        )),
  ),
);
const entryAvoidance = Schema.Struct({
  opponent_entry_hazard_per_second: NonnegativeEstimate,
  one_second_probability: ProbabilityEstimate,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      value.one_second_probability.value === null ||
      (value.opponent_entry_hazard_per_second.value !== null &&
        close(
          value.one_second_probability.value,
          Math.exp(-value.opponent_entry_hazard_per_second.value),
        )),
  ),
);
export const SkaterTerritory = Schema.Struct({
  ice_won_goals_per_basket: Estimate,
  ice_lost_goals_per_basket: Estimate,
  exit_offense: transition,
  entry_offense: transition,
  zone_retention: exitAvoidance,
  entry_prevention: entryAvoidance,
  support: Support,
  method_id: Text,
});
const goalieFields = {
  stopping_goals_per100_on_net: Estimate,
  miss_probability: ProbabilityEstimate,
  recorded_stop_probability: ProbabilityEstimate,
  conversion_probability: ProbabilityEstimate,
  recorded_reattempt_probability: ProbabilityEstimate,
  reattempt_neutral_goal_probability: ProbabilityEstimate,
  followup_danger: ProbabilityEstimate,
  miss_probability_difference: Estimate,
  recorded_stop_probability_difference: Estimate,
  conversion_probability_difference: Estimate,
  recorded_reattempt_probability_difference: Estimate,
  reattempt_neutral_goal_probability_difference: Estimate,
  followup_danger_difference: Estimate,
};
const goalieSupport = Schema.Struct({
  stopping_goals_per100_on_net: Support,
  miss_probability: Support,
  recorded_stop_probability: Support,
  conversion_probability: Support,
  recorded_reattempt_probability: Support,
  reattempt_neutral_goal_probability: Support,
  followup_danger: Support,
  miss_probability_difference: Support,
  recorded_stop_probability_difference: Support,
  conversion_probability_difference: Support,
  recorded_reattempt_probability_difference: Support,
  reattempt_neutral_goal_probability_difference: Support,
  followup_danger_difference: Support,
});
export const GoalieResult = Schema.Struct({
  ...goalieFields,
  support: goalieSupport,
  method_id: Text,
});
const sourceCounts = Schema.Struct({
  provenance: SourceReference,
  unblocked_attempts: Schema.NullOr(Count),
  misses: Schema.NullOr(Count),
  shots_on_goal: Schema.NullOr(Count),
  saves: Schema.NullOr(Count),
  goals_against: Schema.NullOr(Count),
  save_percentage: ProbabilityEstimate,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      (value.unblocked_attempts === null ||
        value.misses === null ||
        value.shots_on_goal === null ||
        value.unblocked_attempts === value.misses + value.shots_on_goal) &&
      (value.shots_on_goal === null ||
        value.saves === null ||
        value.goals_against === null ||
        value.shots_on_goal === value.saves + value.goals_against) &&
      (value.save_percentage.value === null ||
        (value.saves !== null &&
          value.shots_on_goal !== null &&
          value.shots_on_goal > 0 &&
          close(value.save_percentage.value, value.saves / value.shots_on_goal))),
  ),
);
const pairedFields = {
  attempts: Count,
  goals: Count,
  expected_goals: Rate,
  goals_saved_above_expected: Estimate,
  goals_per100_expected: NonnegativeEstimate,
  mean_goal_probability: ProbabilityEstimate,
  league_mean_goal_probability: ProbabilityEstimate,
  difficulty_relative_percent: Estimate,
  support: Support,
  method_id: Text,
};
const paired = Schema.Struct(pairedFields).check(
  Schema.makeFilter(
    (value) => value.goals <= value.attempts && value.expected_goals <= value.attempts,
  ),
);
const pairedOnNet = Schema.Struct({
  ...pairedFields,
  expected_save_fraction: ProbabilityEstimate,
}).check(
  Schema.makeFilter(
    (value) => value.goals <= value.attempts && value.expected_goals <= value.attempts,
  ),
);
const stageEvidence = Schema.Struct({
  success_count: Count,
  eligible_count: Count,
  matched_expected_sum: Rate,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      value.success_count <= value.eligible_count &&
      value.matched_expected_sum <= value.eligible_count,
  ),
);
const goalieStages = Schema.Struct({
  miss: stageEvidence,
  recorded_stop: stageEvidence,
  conversion: stageEvidence,
  reattempt: stageEvidence,
  next_attempt_danger: Schema.Struct({
    fractional_response_sum: Rate,
    eligible_count: Count,
    matched_expected_sum: Rate,
    support: Support,
  }),
});
export const GoalieState = ActualState.check(
  Schema.makeFilter((state) => state.defending_goalie_present),
);
const stateKey = (state: typeof ActualState.Type) =>
  [
    state.attacking_skaters,
    state.defending_skaters,
    state.attacking_goalie_present,
    state.defending_goalie_present,
  ].join(":");
export const GoalieActualState = Schema.Struct({
  state: GoalieState,
  source_counts: sourceCounts,
  on_net_evidence: pairedOnNet,
  unblocked_evidence: paired,
  stage_evidence: goalieStages,
});
const goalieActualStates = Schema.Array(GoalieActualState).check(
  Schema.makeFilter((rows) => unique(rows.map((row) => stateKey(row.state)))),
);
const validGoalieStates = (value: {
  source_counts: typeof sourceCounts.Type;
  on_net_evidence: typeof pairedOnNet.Type;
  unblocked_evidence: typeof paired.Type;
  stage_evidence: typeof goalieStages.Type;
  actual_states: readonly (typeof GoalieActualState.Type)[];
}) => {
  for (const field of [
    "unblocked_attempts",
    "misses",
    "shots_on_goal",
    "saves",
    "goals_against",
  ] as const) {
    const total = value.source_counts[field];
    if (
      total !== null &&
      (value.actual_states.some((row) => row.source_counts[field] === null) ||
        !close(
          total,
          value.actual_states.reduce((sum, row) => sum + (row.source_counts[field] ?? 0), 0),
        ))
    )
      return false;
  }
  for (const population of ["on_net_evidence", "unblocked_evidence"] as const)
    for (const field of ["attempts", "goals", "expected_goals"] as const)
      if (
        !close(
          value[population][field],
          value.actual_states.reduce((sum, row) => sum + row[population][field], 0),
        )
      )
        return false;
  for (const stage of ["miss", "recorded_stop", "conversion", "reattempt"] as const)
    for (const field of ["success_count", "eligible_count", "matched_expected_sum"] as const)
      if (
        !close(
          value.stage_evidence[stage][field],
          value.actual_states.reduce((sum, row) => sum + row.stage_evidence[stage][field], 0),
        )
      )
        return false;
  for (const field of [
    "fractional_response_sum",
    "eligible_count",
    "matched_expected_sum",
  ] as const)
    if (
      !close(
        value.stage_evidence.next_attempt_danger[field],
        value.actual_states.reduce(
          (sum, row) => sum + row.stage_evidence.next_attempt_danger[field],
          0,
        ),
      )
    )
      return false;
  return true;
};
const goalieSummaryFields = {
  source_counts: sourceCounts,
  reported_boxscore_counts: sourceCounts,
  on_net_evidence: pairedOnNet,
  unblocked_evidence: paired,
  stage_evidence: goalieStages,
  actual_states: goalieActualStates,
};
export const GoalieGame = Schema.Struct({
  provenance: SourceReference,
  game_id: GameId,
  date: DateString,
  team: Team,
  opponent: Team,
  start_status: Schema.Literals(["start", "relief", "did_not_play", "unknown"]),
  reported_seconds: Schema.NullOr(Rate),
  ...goalieSummaryFields,
}).check(Schema.makeFilter(validGoalieStates));
export const GoalieObservedSummary = Schema.Struct({
  provenance: SourceReference,
  ...goalieSummaryFields,
  starts: Count,
  relief_appearances: Count,
  unknown_start_status: Count,
  reported_usage: ReportedUsage,
  coverage: Support,
}).check(Schema.makeFilter(validGoalieStates));
export const GoalieObserved = Schema.Struct({
  ...GoalieObservedSummary.fields,
  games: Schema.Array(GoalieGame).check(
    Schema.makeFilter((rows) => unique(rows.map((row) => row.game_id))),
  ),
}).check(Schema.makeFilter(validGoalieStates));
const component = Schema.Struct({ league_goals: Estimate, replacement_goals: Estimate });
export const ValueLedger = Schema.Struct({
  reference_minutes: Schema.Struct({
    five_on_five: Schema.Literal(1000),
    power_play: Schema.Literal(100),
    penalty_kill: Schema.Literal(100),
  }),
  components: Schema.Struct({
    five_on_five_offense: component,
    five_on_five_defense: component,
    power_play_offense: component,
    penalty_kill_defense: component,
    finishing: component,
    setting: component,
    penalties_drawn: component,
    penalties_taken: component,
    ice_won: component,
    ice_lost: component,
  }),
  league_total: Estimate,
  replacement_total: Estimate,
  penalties_combined: component,
  method_id: Text,
}).check(
  Schema.makeFilter((value) =>
    (["league", "replacement"] as const).every((reference) => {
      const components = Object.values(value.components).map(
        (component) => component[`${reference}_goals`].value,
      );
      const total = value[`${reference}_total`].value;
      const drawn = value.components.penalties_drawn[`${reference}_goals`].value;
      const taken = value.components.penalties_taken[`${reference}_goals`].value;
      const combined = value.penalties_combined[`${reference}_goals`].value;
      return (
        (total === null ||
          (components.every((component) => component !== null) &&
            close(
              total,
              components.reduce<number>((sum, component) => sum + (component ?? 0), 0),
            ))) &&
        (combined === null || (drawn !== null && taken !== null && close(combined, drawn + taken)))
      );
    }),
  ),
);
export const per60 = (mass: number, seconds: number): number | null =>
  seconds === 0 ? null : (3600 * mass) / seconds;
export const close = (a: number, b: number) =>
  Number.isFinite(a) &&
  Number.isFinite(b) &&
  Math.abs(a - b) <= 1e-9 + 1e-9 * Math.max(Math.abs(a), Math.abs(b));
const massCells = Schema.Array(Schema.Struct({ cell_id: Count, value: Schema.Finite })).check(
  Schema.makeFilter(
    (rows) => rows.length === 656 && rows.every((row, index) => row.cell_id === index),
  ),
);
const displayCells = Schema.Array(
  Schema.Struct({ cell_id: Count, mass: Schema.Finite, density_per100sqft: Schema.Finite }),
).check(
  Schema.makeFilter(
    (rows) =>
      rows.length === 668 &&
      rows.every((row, index) => index === 0 || rows[index - 1].cell_id < row.cell_id),
  ),
);
export const MapUnit = Schema.Literals([
  "attempts_per60",
  "xg_per60",
  "goals_per100_attempts",
  "goals_per100_assisted_opportunities",
  "goals_per_basket",
  "goals_per100_on_net",
]);
export const AnalysisMap = Schema.Struct({
  grid_id: Text,
  unit: MapUnit,
  reference: Text,
  cells: Schema.NullOr(massCells),
  display_cells: Schema.NullOr(displayCells),
  integrated_value: Schema.NullOr(Schema.Finite),
  unavailable_reason: Schema.NullOr(UnavailableReason),
  reason_detail: Schema.NullOr(ReasonDetail),
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter((value) =>
    value.cells === null
      ? value.display_cells === null &&
        value.integrated_value === null &&
        value.unavailable_reason !== null &&
        value.reason_detail !== null &&
        validEstimate({
          value: null,
          unavailable_reason: value.unavailable_reason,
          reason_detail: value.reason_detail,
          uncertainty: { kind: "not_estimated" },
        })
      : value.display_cells !== null &&
        value.integrated_value !== null &&
        value.unavailable_reason === null &&
        value.reason_detail === null &&
        close(
          value.cells.reduce((sum, row) => sum + row.value, 0),
          value.integrated_value,
        ) &&
        close(
          value.display_cells.reduce((sum, row) => sum + row.mass, 0),
          value.integrated_value,
        ),
  ),
);
export const ExecutionBreakdown = Schema.Struct({
  events: Count,
  eligible_weight: Rate,
  observed_successes: Rate,
  expected_successes: Rate,
  probability: ProbabilityEstimate,
  effect: Estimate,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter(
    (value) =>
      value.observed_successes <= value.eligible_weight &&
      value.expected_successes <= value.eligible_weight,
  ),
);
export const AdjustmentTarget = Schema.Literals([
  "for_attempts_per60",
  "against_attempts_per60",
  "for_xg_per60",
  "against_xg_per60",
]);
export const AdjustmentDecomposition = Schema.Struct({
  baseline: Estimate,
  self: Estimate,
  teammates: Estimate,
  opponents: Estimate,
  coaching_other_context: Estimate,
  numerical_residual: Estimate,
  factual_prediction: Estimate,
  method_id: Text,
}).check(
  Schema.makeFilter((value) => {
    const terms = [
      value.baseline,
      value.self,
      value.teammates,
      value.opponents,
      value.coaching_other_context,
      value.numerical_residual,
    ].map((estimate) => estimate.value);
    return (
      value.factual_prediction.value === null ||
      (terms.every((term) => term !== null) &&
        close(
          value.factual_prediction.value,
          terms.reduce<number>((sum, term) => sum + (term ?? 0), 0),
        ))
    );
  }),
);
const evidenceMass = Schema.Struct({ goals: Count, expected_goals: Rate, attempts: Count }).check(
  Schema.makeFilter(
    (value) => value.goals <= value.attempts && value.expected_goals <= value.attempts,
  ),
);
export const GoalieEvidenceState = Schema.Struct({
  state: GoalieState,
  ...evidenceMass.fields,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) => value.goals <= value.attempts && value.expected_goals <= value.attempts,
  ),
);
const evidenceStates = Schema.Array(GoalieEvidenceState).check(
  Schema.makeFilter((rows) => unique(rows.map((row) => stateKey(row.state)))),
);
const nativeEvidenceMass = Schema.Struct({
  goals: Rate,
  expected_goals: Rate,
  attempts: Rate,
}).check(
  Schema.makeFilter(
    (value) => value.goals <= value.attempts && value.expected_goals <= value.attempts,
  ),
);
const evidenceDisplay = Schema.Struct({
  cell_id: Count,
  goals: Rate,
  expected_goals: Rate,
  attempts: Rate,
  mass_saved: Schema.Finite,
  ratio: Schema.NullOr(Schema.Finite),
  unavailable_reason: Schema.NullOr(UnavailableReason),
}).check(
  Schema.makeFilter(
    (value) =>
      value.goals <= value.attempts &&
      value.expected_goals <= value.attempts &&
      close(value.mass_saved, value.expected_goals - value.goals) &&
      (value.ratio === null) === (value.unavailable_reason !== null),
  ),
);
export const GoalieEvidenceMap = Schema.Struct({
  actual_states: evidenceStates,
  native_cells: Schema.Array(Schema.Struct({ cell_id: Count, ...nativeEvidenceMass.fields })).check(
    Schema.makeFilter(
      (rows) =>
        rows.length === 656 &&
        rows.every(
          (row, index) =>
            row.cell_id === index &&
            row.goals <= row.attempts &&
            row.expected_goals <= row.attempts,
        ),
    ),
  ),
  unmapped: evidenceMass,
  totals: evidenceMass,
  league_goals: Count,
  league_expected_goals: Rate,
  display_cells: Schema.Array(evidenceDisplay).check(
    Schema.makeFilter(
      (rows) =>
        rows.length === 668 &&
        rows.every((row, index) => index === 0 || rows[index - 1].cell_id < row.cell_id),
    ),
  ),
  reference: Text,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter((value) =>
    (["goals", "expected_goals", "attempts"] as const).every(
      (field) =>
        close(
          value.actual_states.reduce((sum, row) => sum + row[field], 0),
          value.totals[field],
        ) &&
        close(
          value.native_cells.reduce((sum, row) => sum + row[field], 0) + value.unmapped[field],
          value.totals[field],
        ) &&
        close(
          value.display_cells.reduce((sum, row) => sum + row[field], 0) + value.unmapped[field],
          value.totals[field],
        ),
    ),
  ),
);
export const GoalieDanger = Schema.Struct({
  actual_states: evidenceStates,
  edges: Schema.Array(Probability).check(
    Schema.makeFilter(
      (rows) => rows.length === 101 && rows.every((value, index) => value === index / 100),
    ),
  ),
  attempt_counts: Schema.Array(Count).check(Schema.makeFilter((rows) => rows.length === 100)),
  goal_mass: Schema.Array(Rate).check(Schema.makeFilter((rows) => rows.length === 100)),
  expected_goal_mass: Schema.Array(Rate).check(Schema.makeFilter((rows) => rows.length === 100)),
  totals: evidenceMass,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter(
    (value) =>
      (["goals", "expected_goals", "attempts"] as const).every((field) =>
        close(
          value.actual_states.reduce((sum, row) => sum + row[field], 0),
          value.totals[field],
        ),
      ) &&
      value.attempt_counts.every((count, index) => {
        const expected = value.expected_goal_mass[index];
        const goals = value.goal_mass[index];
        if (count === 0) return expected === 0 && goals === 0;
        const lower = value.edges[index] * count;
        const upper = value.edges[index + 1] * count;
        return (
          (expected >= lower || close(expected, lower)) &&
          (expected <= upper || close(expected, upper)) &&
          (goals <= count || close(goals, count))
        );
      }) &&
      close(
        value.attempt_counts.reduce((sum, count) => sum + count, 0),
        value.totals.attempts,
      ) &&
      close(
        value.goal_mass.reduce((sum, mass) => sum + mass, 0),
        value.totals.goals,
      ) &&
      close(
        value.expected_goal_mass.reduce((sum, mass) => sum + mass, 0),
        value.totals.expected_goals,
      ),
  ),
);
export const result = <S extends Schema.Top>(data: S) =>
  Schema.Union([
    Schema.Struct({ availability: Schema.Literal("provided"), explanation: Schema.Null, data }),
    Schema.Struct({
      availability: Schema.Literal("not_computed"),
      explanation: Text,
      data: Schema.Null,
    }),
  ]);
export const AbsentResult = Schema.Struct({
  availability: Schema.Literal("absent"),
  explanation: Text,
  data: Schema.Null,
});
export const ApiResult = <S extends Schema.Top>(data: S) =>
  Schema.Union([result(data), AbsentResult]);
export const ObservedResult = result(PlayerSummary);
export const SkaterDescriptiveResult = result(SkaterDescriptive);
export const SkaterContextResult = result(SkaterContext);
export const SkaterMicrostatsResult = result(SkaterMicrostats);
export const SkaterSpatialResult = result(SkaterSpatial);
export const SkaterExecutionResult = result(SkaterExecution);
export const SkaterShootinessResult = result(SkaterShootiness);
export const SkaterPenaltiesResult = result(SkaterPenalties);
export const SkaterTerritoryResult = result(SkaterTerritory);
export const GoalieResultEnvelope = result(GoalieResult);
export const GoalieObservedResult = result(GoalieObserved);
export const GoalieObservedSummaryResult = result(GoalieObservedSummary);
export const ValueLedgerResult = result(ValueLedger);
export const AnalysisMapResult = result(AnalysisMap);
export const ExecutionBreakdownResult = result(ExecutionBreakdown);
export const AdjustmentDecompositionResult = result(AdjustmentDecomposition);
export const GoalieEvidenceMapResult = result(GoalieEvidenceMap);
export const GoalieDangerResult = result(GoalieDanger);
export const SupportDescriptor = SupportDefinition;
export const FamilyDisposition = FamilyAvailability;
export const AttemptKey = Schema.Struct({ season: Season, game_id: GameId, source_index: Count });
const validAttemptGeometry = (value: {
  x_ft: number | null;
  y_ft: number | null;
  location_kind: "reported_event" | "block_contact" | "unavailable";
  outcome: "goal" | "save" | "miss" | "block";
}) =>
  (value.x_ft === null) === (value.y_ft === null) &&
  (value.location_kind === "unavailable"
    ? value.x_ft === null
    : value.x_ft !== null &&
      Math.abs(value.x_ft) <= 100 &&
      value.y_ft !== null &&
      Math.abs(value.y_ft) <= 42.5 &&
      Math.max(Math.abs(value.x_ft) - 72, 0) ** 2 + Math.max(Math.abs(value.y_ft) - 14.5, 0) ** 2 <=
        28 ** 2) &&
  (value.location_kind === "unavailable" ||
    (value.location_kind === "block_contact") === (value.outcome === "block"));
export const AttemptFact = Schema.Struct({
  ...AttemptKey.fields,
  event_id: Schema.NullOr(Count),
  period_number: Count.check(Schema.isGreaterThan(0)),
  time_seconds: Rate,
  team_id: Schema.NullOr(Id),
  shooter_id: Schema.NullOr(Id),
  goalie_id: Schema.NullOr(Id),
  actual_state: Schema.NullOr(ActualState),
  outcome: Schema.Literals(["goal", "save", "miss", "block"]),
  shot_type: Schema.NullOr(Text),
  x_ft: Schema.NullOr(Schema.Finite),
  y_ft: Schema.NullOr(Schema.Finite),
  location_kind: Schema.Literals(["reported_event", "block_contact", "unavailable"]),
  recorded_stop: Schema.NullOr(Schema.Boolean),
  recorded_stop_reason: Schema.NullOr(Text),
  recorded_reattempt: Schema.NullOr(Schema.Boolean),
  recorded_reattempt_reason: Schema.NullOr(Text),
  support_id: Text,
  source: SourceReference,
}).check(Schema.makeFilter(validAttemptGeometry));
export const AttemptValue = Schema.Struct({
  ...AttemptKey.fields,
  actor_all_attempt_opportunity: ProbabilityEstimate,
  neutral_all_attempt_opportunity: ProbabilityEstimate,
  actor_unblocked_goal_probability: ProbabilityEstimate,
  actor_on_net_goal_probability: ProbabilityEstimate,
  neutral_goalie_on_net_goal_probability: ProbabilityEstimate,
  method_id: Text,
  support_id: Text,
});
export const ValuedAttemptFact = Schema.Struct({
  ...AttemptFact.fields,
  actor_all_attempt_opportunity: ProbabilityEstimate,
  neutral_all_attempt_opportunity: ProbabilityEstimate,
  actor_unblocked_goal_probability: ProbabilityEstimate,
  actor_on_net_goal_probability: ProbabilityEstimate,
  neutral_goalie_on_net_goal_probability: ProbabilityEstimate,
  method_id: Schema.NullOr(Text),
}).check(Schema.makeFilter(validAttemptGeometry));
export const Recipient = Schema.Union([Id, Schema.Literals(["none", "unknown"])]);
export const AttemptSetter = Schema.Struct({
  ...AttemptKey.fields,
  candidate_id: Recipient,
  pre_outcome_weight: Probability,
  posterior_weight: Schema.NullOr(Probability),
  recorded_assist_evidence: Schema.Array(Reference),
});
export const AttemptExecutionShare = Schema.Struct({
  ...AttemptKey.fields,
  group: Schema.Literals(["shooter", "setter", "goalie", "coach"]),
  recipient_id: Schema.Union([Recipient, Schema.Literal("coaching_context")]),
  goals: Schema.Finite,
}).check(
  Schema.makeFilter(
    (value) => (value.group === "coach") === (value.recipient_id === "coaching_context"),
  ),
);
export const DressedGame = Schema.Struct({
  season: Season,
  player_id: Id,
  game_id: GameId,
  team_id: Id,
  source: SourceReference,
});
export const IntervalFact = Schema.Struct({
  season: Season,
  game_id: GameId,
  interval_id: Text,
  team_id: Id,
  population: ContextPopulation,
  period_number: Count.check(Schema.isGreaterThan(0), Schema.isLessThanOrEqualTo(4)),
  period_horizon_seconds: Rate.check(Schema.isGreaterThan(0)),
  start_seconds: Rate,
  end_seconds: Rate,
  support_id: Text,
  for_mass: Rate,
  against_mass: Rate,
  on_net_for: Schema.NullOr(Count),
  on_net_against: Schema.NullOr(Count),
}).check(
  Schema.makeFilter(
    (value) =>
      (["recorded_all_attempts", "recorded_goals", "recorded_locatable_unblocked"].includes(
        value.population,
      )
        ? Number.isSafeInteger(value.for_mass) && Number.isSafeInteger(value.against_mass)
        : true) &&
      value.end_seconds > value.start_seconds &&
      value.end_seconds <= value.period_horizon_seconds &&
      value.period_horizon_seconds <= (value.period_number <= 3 ? 1200 : 300) &&
      (value.population === "recorded_goals"
        ? value.on_net_for !== null &&
          value.on_net_against !== null &&
          Number.isSafeInteger(value.for_mass) &&
          Number.isSafeInteger(value.against_mass) &&
          value.for_mass <= value.on_net_for &&
          value.against_mass <= value.on_net_against
        : value.on_net_for === null && value.on_net_against === null),
  ),
);
export const IntervalPlayer = Schema.Struct({
  season: Season,
  game_id: GameId,
  interval_id: Text,
  team_id: Id,
  player_id: Id,
});
export const IntervalLocation = Schema.Struct({
  season: Season,
  game_id: GameId,
  interval_id: Text,
  team_id: Id,
  population: Schema.Literals([
    "recorded_locatable_unblocked",
    "neutral_locatable_unblocked_value",
  ]),
  cell_id: Count,
  for_mass: Rate,
  against_mass: Rate,
}).check(
  Schema.makeFilter(
    (value) =>
      value.population !== "recorded_locatable_unblocked" ||
      (Number.isSafeInteger(value.for_mass) && Number.isSafeInteger(value.against_mass)),
  ),
);
export const ContextCoverage = Schema.Struct({
  season: Season,
  player_id: Id,
  population: ContextPopulation,
  availability: Schema.Literals(["provided", "not_computed"]),
  explanation: Schema.NullOr(Text),
  known_excluded_seconds: Schema.NullOr(Rate),
  unquantified_gap: Schema.Boolean,
  reason_counts: ReasonCounts,
  source_ids: Schema.Array(Text).check(Schema.makeFilter(sortedStrings)),
  method_ids: Schema.Array(Text).check(Schema.makeFilter(sortedStrings)),
}).check(
  Schema.makeFilter(
    (value) => (value.availability === "not_computed") === (value.explanation !== null),
  ),
);
export const NativeGrid = Schema.Struct({
  grid_id: Schema.Literal("native656"),
  kind: Schema.Literal("native"),
  cells: Schema.Array(
    Schema.Struct({ cell_id: Count, x_ft: Schema.Finite, y_ft: Schema.Finite }),
  ).check(
    Schema.makeFilter(
      (rows) => rows.length === 656 && rows.every((row, index) => row.cell_id === index),
    ),
  ),
});
export const DisplayGrid = Schema.Struct({
  grid_id: Schema.Literal("display668"),
  kind: Schema.Literal("display"),
  mapping: Schema.Literal("rect5_gaussian10_v1"),
  cells: Schema.Array(
    Schema.Struct({
      cell_id: Count,
      x_min: Schema.Finite,
      x_max: Schema.Finite,
      y_min: Schema.Finite,
      y_max: Schema.Finite,
      area_sqft: Rate.check(Schema.isGreaterThan(0)),
    }),
  ).check(
    Schema.makeFilter(
      (rows) =>
        rows.length === 668 &&
        rows.every(
          (row, index) =>
            row.x_min < row.x_max &&
            row.y_min < row.y_max &&
            (index === 0 || rows[index - 1].cell_id < row.cell_id),
        ),
    ),
  ),
});
export const AnalysisGrid = Schema.Union([NativeGrid, DisplayGrid]);
const keyedSources = Schema.Record(Text, Source).check(
  Schema.makeFilter((rows) => Object.entries(rows).every(([id, value]) => id === value.source_id)),
);
const keyedMethods = Schema.Record(Text, Method).check(
  Schema.makeFilter((rows) => Object.entries(rows).every(([id, value]) => id === value.method_id)),
);
const keyedSupports = Schema.Record(Text, SupportDefinition).check(
  Schema.makeFilter((rows) => Object.entries(rows).every(([id, value]) => id === value.support_id)),
);
export const Envelope = Schema.Struct({
  publication: Publication,
  available_seasons: AvailableSeasons,
  season: SeasonEvidence,
  sources: keyedSources,
  methods: keyedMethods,
  supports: keyedSupports,
});
const spatialSummaries = result(
  Schema.Array(Schema.Struct({ strength: SpatialStrength, result: SkaterSpatialResult })),
);
const executionSummaries = result(
  Schema.Array(Schema.Struct({ strength: ExecutionStrength, result: SkaterExecutionResult })),
);
const shootinessSummaries = result(
  Schema.Array(Schema.Struct({ strength: ExecutionStrength, result: SkaterShootinessResult })),
);
const goalieSummaries = result(
  Schema.Array(Schema.Struct({ strength: GoalieStrength, result: GoalieResultEnvelope })),
);
const goalieObservedSummaries = result(
  Schema.Array(Schema.Struct({ strength: EvidenceStrength, result: GoalieObservedSummaryResult })),
);
export const SkaterFamilies = Schema.Struct({
  kind: Schema.Literal("skater"),
  observed: ObservedResult,
  descriptive: SkaterDescriptiveResult,
  context: SkaterContextResult,
  microstats: SkaterMicrostatsResult,
  spatial: spatialSummaries,
  execution: executionSummaries,
  shootiness: shootinessSummaries,
  penalties: SkaterPenaltiesResult,
  territory: SkaterTerritoryResult,
  ledger: ValueLedgerResult,
});
export const GoalieFamilies = Schema.Struct({
  kind: Schema.Literal("goalie"),
  goalie: goalieSummaries,
  goalie_observed: goalieObservedSummaries,
});
export const AbsentFamilies = Schema.Struct({
  kind: PersonKind,
  availability: Schema.Literal("absent"),
  explanation: Text,
  data: Schema.Null,
});
export const PlayerFamilies = Schema.Union([SkaterFamilies, GoalieFamilies, AbsentFamilies]);
export type PlayerFamilies = typeof PlayerFamilies.Type;
const skaterOverview = Schema.Struct({
  reported_usage: result(ReportedUsage),
  ledger: ValueLedgerResult,
  spatial: Schema.Struct({
    five_on_five: SkaterSpatialResult,
    pp: SkaterSpatialResult,
    pk: SkaterSpatialResult,
  }),
  execution: SkaterExecutionResult,
  shootiness: SkaterShootinessResult,
  penalties: SkaterPenaltiesResult,
  territory: SkaterTerritoryResult,
  observed: ObservedResult,
  context: SkaterContextResult,
});
const goalieOverview = Schema.Struct({
  reported_usage: result(ReportedUsage),
  goalie: Schema.Struct({ ev: GoalieResultEnvelope, pk: GoalieResultEnvelope }),
  observed: Schema.Struct({ ev: GoalieObservedSummaryResult, pk: GoalieObservedSummaryResult }),
});
export const SkaterOverviewResult = result(skaterOverview);
export const GoalieOverviewResult = result(goalieOverview);
const leagueRows = <S extends Schema.Top>(schema: S) =>
  Schema.Array(Schema.Struct({ person: Person, result: schema }));
const leagueBody = Schema.Union([
  Schema.Struct({
    family: Schema.Literal("observed"),
    kind: Schema.Literal("skater"),
    strength: Schema.Literal("5v5"),
    players: leagueRows(ObservedResult),
  }),
  Schema.Struct({
    family: Schema.Literal("overview"),
    kind: Schema.Literal("skater"),
    strength: Schema.Null,
    players: leagueRows(SkaterOverviewResult),
  }),
  Schema.Struct({
    family: Schema.Literal("overview"),
    kind: Schema.Literal("goalie"),
    strength: Schema.Null,
    players: leagueRows(GoalieOverviewResult),
  }),
  Schema.Struct({
    family: Schema.Literal("spatial"),
    kind: Schema.Literal("skater"),
    strength: SpatialStrength,
    players: leagueRows(SkaterSpatialResult),
  }),
  Schema.Struct({
    family: Schema.Literal("execution"),
    kind: Schema.Literal("skater"),
    strength: ExecutionStrength,
    players: leagueRows(SkaterExecutionResult),
  }),
  Schema.Struct({
    family: Schema.Literal("shootiness"),
    kind: Schema.Literal("skater"),
    strength: ExecutionStrength,
    players: leagueRows(SkaterShootinessResult),
  }),
  Schema.Struct({
    family: Schema.Literal("penalties"),
    kind: Schema.Literal("skater"),
    strength: Schema.Null,
    players: leagueRows(SkaterPenaltiesResult),
  }),
  Schema.Struct({
    family: Schema.Literal("territory"),
    kind: Schema.Literal("skater"),
    strength: Schema.Null,
    players: leagueRows(SkaterTerritoryResult),
  }),
  Schema.Struct({
    family: Schema.Literal("descriptive"),
    kind: Schema.Literal("skater"),
    strength: Schema.Null,
    players: leagueRows(SkaterDescriptiveResult),
  }),
  Schema.Struct({
    family: Schema.Literal("microstats"),
    kind: Schema.Literal("skater"),
    strength: Schema.Null,
    players: leagueRows(SkaterMicrostatsResult),
  }),
  Schema.Struct({
    family: Schema.Literal("goalie"),
    kind: Schema.Literal("goalie"),
    strength: GoalieStrength,
    players: leagueRows(GoalieResultEnvelope),
  }),
]);
export const LeagueSelection = Schema.Struct({
  season: Season,
  kind: PersonKind,
  family: Schema.Literals([
    "overview",
    "observed",
    "spatial",
    "execution",
    "shootiness",
    "penalties",
    "territory",
    "descriptive",
    "microstats",
    "goalie",
  ]),
  strength: Schema.NullOr(Schema.Union([SpatialStrength, GoalieStrength])),
}).check(
  Schema.makeFilter((value) => {
    const query = new URLSearchParams({
      season: value.season,
      kind: value.kind,
      family: value.family,
    });
    if (value.strength !== null) query.set("strength", value.strength);
    try {
      parseLeague(query, [value.season]);
      return true;
    } catch {
      return false;
    }
  }),
);
export type LeagueSelection = typeof LeagueSelection.Type;
export const LeagueResponse = Schema.Union(
  leagueBody.members.map((body) => Schema.Struct({ ...Envelope.fields, ...body.fields })),
).check(
  Schema.makeFilter(
    (response) =>
      response.available_seasons.includes(response.season.season) &&
      unique(response.players.map((row) => row.person.player_id)) &&
      response.players.every((row) => {
        if (row.person.kind !== response.kind || row.person.season !== response.season.season)
          return false;
        if (response.family !== "observed") return true;
        if (row.result.availability !== "provided") return false;
        const data = row.result.data as typeof PlayerSummary.Type;
        return (
          row.person.player_id === data.player_id &&
          row.person.display_name === data.display_name &&
          row.person.reported_position === data.reported_position &&
          JSON.stringify(row.person.teams) === JSON.stringify(data.teams)
        );
      }),
  ),
);
export type LeagueResponse = typeof LeagueResponse.Type;
export const PlayerResponse = Schema.Struct({
  ...Envelope.fields,
  player_id: Id,
  kind: PersonKind,
  person: Schema.NullOr(Person),
  families: PlayerFamilies,
  observed_games: Schema.Array(PlayerGame),
  deployment: Schema.NullOr(Deployment),
  history: Schema.Array(
    Schema.Struct({
      season: SeasonEvidence,
      person: Schema.NullOr(Person),
      families: PlayerFamilies,
    }),
  ),
}).check(
  Schema.makeFilter((response) => {
    if (
      (response.person === null) !==
      ("availability" in response.families && response.families.availability === "absent")
    )
      return false;
    if (
      response.families.kind !== response.kind ||
      (response.person !== null &&
        (response.person.player_id !== response.player_id ||
          response.person.kind !== response.kind ||
          response.person.season !== response.season.season))
    )
      return false;
    const years = [...response.available_seasons].reverse();
    if (
      response.history.length !== years.length ||
      !response.history.some((row) => row.person !== null)
    )
      return false;
    if (
      !response.history.every(
        (row, index) =>
          row.season.season === years[index] &&
          row.families.kind === response.kind &&
          (row.person === null) ===
            ("availability" in row.families && row.families.availability === "absent") &&
          (row.person === null ||
            (row.person.player_id === response.player_id &&
              row.person.kind === response.kind &&
              row.person.season === row.season.season)),
      )
    )
      return false;
    const selected = response.history.find((row) => row.season.season === response.season.season);
    if (
      !selected ||
      JSON.stringify(selected.season) !== JSON.stringify(response.season) ||
      JSON.stringify(selected.person) !== JSON.stringify(response.person) ||
      JSON.stringify(selected.families) !== JSON.stringify(response.families)
    )
      return false;
    if (
      response.kind === "goalie" ||
      response.person === null ||
      (response.families.kind === "skater" &&
        !("availability" in response.families) &&
        response.families.observed.availability !== "provided")
    )
      return response.observed_games.length === 0 && response.deployment === null;
    return (
      unique(response.observed_games.map((row) => row.game_id)) &&
      response.observed_games.every(
        (row) => row.game_id.slice(0, 4) === response.season.season.slice(0, 4),
      )
    );
  }),
);
export type PlayerResponse = typeof PlayerResponse.Type;
export const MapSelection = Schema.Struct({
  season: Season,
  players: Schema.Array(Id).check(
    Schema.makeFilter((ids) => ids.length > 0 && ids.length <= 2 && unique(ids)),
  ),
  family: Schema.Union([Schema.Literal("observed"), MapKind, Schema.Literal("goalie_evidence")]),
  strength: Schema.Union([EvidenceStrength, Schema.Literal("pp")]),
  view: Schema.Literals(["effect", "complete", "evidence_mass", "evidence_ratio"]),
  population: Schema.NullOr(EvidencePopulation),
  type: Schema.NullOr(EvidenceType),
}).check(
  Schema.makeFilter((value) => {
    const query = new URLSearchParams({
      season: value.season,
      players: value.players.join(","),
      family: value.family,
      strength: value.strength,
      view: value.view,
    });
    if (value.population !== null) query.set("population", value.population);
    if (value.type !== null) query.set("type", value.type);
    try {
      parseMap(query, [value.season]);
      return true;
    } catch {
      return false;
    }
  }),
);
const scale = Schema.Struct({ minimum: Schema.Finite, maximum: Schema.Finite, unit: Text }).check(
  Schema.makeFilter((value) => value.minimum <= value.maximum),
);
export const MapsResponse = Schema.Union([
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("observed"),
    selection: SpatialSelection,
    scale,
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: MapKind,
    selection: MapSelection,
    definition: Schema.Struct({
      native_grid: NativeGrid,
      display_grid: DisplayGrid,
      orientation: Schema.Literal("shooting_team_positive_x"),
    }),
    scale,
    players: Schema.Array(Schema.Struct({ player_id: Id, result: ApiResult(AnalysisMap) })),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("goalie_evidence"),
    selection: MapSelection,
    definition: Schema.Struct({
      native_grid: NativeGrid,
      display_grid: DisplayGrid,
      orientation: Schema.Literal("shooting_team_positive_x"),
    }),
    scale,
    players: Schema.Array(Schema.Struct({ player_id: Id, result: ApiResult(GoalieEvidenceMap) })),
  }),
]).check(
  Schema.makeFilter(
    (response) =>
      response.family === "observed" ||
      (response.family === response.selection.family &&
        response.selection.season === response.season.season &&
        response.players.length === response.selection.players.length &&
        response.players.every(
          (row, index) => row.player_id === response.selection.players[index],
        )),
  ),
);
export type MapsResponse = typeof MapsResponse.Type;
export const EvidenceSelection = Schema.Struct({
  season: Season,
  player_id: Id,
  family: Schema.Literals([
    "personal_shots",
    "execution",
    "goalie",
    "goalie_evidence",
    "penalties",
    "territory",
    "microstats",
  ]),
  strength: Schema.NullOr(EvidenceStrength),
  population: Schema.NullOr(EvidencePopulation),
  type: Schema.NullOr(EvidenceType),
  outcome: Schema.NullOr(Schema.Literals(["all_unblocked", "on_net", "goal", "save", "miss"])),
  shot_type: Schema.NullOr(Text),
  blocked_contacts: Schema.Boolean,
}).check(
  Schema.makeFilter((value) => {
    const query = new URLSearchParams({ season: value.season, family: value.family });
    if (value.strength !== null) query.set("strength", value.strength);
    if (value.population !== null) query.set("population", value.population);
    if (value.type !== null) query.set("type", value.type);
    if (value.outcome !== null) query.set("outcome", value.outcome);
    if (value.shot_type !== null) query.set("shot_type", value.shot_type);
    if (value.family === "personal_shots")
      query.set("blocked_contacts", String(value.blocked_contacts));
    else if (value.blocked_contacts) return false;
    try {
      parseEvidence(query, [value.season], value.player_id);
      return true;
    } catch {
      return false;
    }
  }),
);
const breakdownRow = Schema.Struct({
  strength: Schema.Union([ExecutionStrength, GoalieStrength]),
  kind: Schema.Literals(["shot_type", "danger"]),
  stratum: Schema.Union([ShotType, Schema.Literals(["<.05", "[.05,.15)", ">=.15"])]),
  result: ExecutionBreakdownResult,
});
export const EvidenceResponse = Schema.Union([
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("personal_shots"),
    selection: EvidenceSelection,
    result: ApiResult(
      Schema.Struct({
        attempts: Schema.Array(ValuedAttemptFact),
        unblocked_count: Count,
        located_count: Count,
        blocked_contact_count: Count,
        support_ids: Schema.Array(Text),
      }),
    ),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("execution"),
    selection: EvidenceSelection,
    result: ApiResult(
      Schema.Struct({
        summary: SkaterExecutionResult,
        breakdowns: Schema.Array(breakdownRow),
        attempts: Schema.Array(ValuedAttemptFact),
        setters: Schema.Array(AttemptSetter),
        shares: Schema.Array(AttemptExecutionShare),
      }),
    ),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("goalie"),
    selection: EvidenceSelection,
    result: ApiResult(
      Schema.Struct({ summary: GoalieResultEnvelope, breakdowns: Schema.Array(breakdownRow) }),
    ),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("goalie_evidence"),
    selection: EvidenceSelection,
    result: ApiResult(
      Schema.Struct({
        observed: GoalieObservedResult,
        map: GoalieEvidenceMapResult,
        danger: GoalieDangerResult,
      }),
    ),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("penalties"),
    selection: EvidenceSelection,
    result: ApiResult(SkaterPenalties),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("territory"),
    selection: EvidenceSelection,
    result: ApiResult(SkaterTerritory),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("microstats"),
    selection: EvidenceSelection,
    result: ApiResult(SkaterMicrostats),
  }),
]).check(
  Schema.makeFilter(
    (response) =>
      response.family === response.selection.family &&
      response.selection.season === response.season.season,
  ),
);
export type EvidenceResponse = typeof EvidenceResponse.Type;
export const ContextSelection = Schema.Struct({
  season: Season,
  player_id: Id,
  mode: Schema.Literals(["on_off", "with_without"]),
  population: ContextPopulation,
  teammates: Schema.Array(Id).check(Schema.makeFilter((ids) => ids.length <= 2 && unique(ids))),
}).check(
  Schema.makeFilter(
    (value) =>
      !value.teammates.includes(value.player_id) &&
      (value.mode === "on_off" ? value.teammates.length === 0 : value.teammates.length > 0),
  ),
);
export const ContextGroup = Schema.Struct({
  group: Schema.Literals(["on", "off", "together", "apart"]),
  for_mass: Rate,
  against_mass: Rate,
  seconds: Rate,
  for_per60: Schema.NullOr(Rate),
  against_per60: Schema.NullOr(Rate),
  on_net_for: Schema.NullOr(Count),
  on_net_against: Schema.NullOr(Count),
  locations: Schema.NullOr(
    Schema.Array(Schema.Struct({ cell_id: Count, for_mass: Rate, against_mass: Rate })),
  ),
  support_ids: Schema.Array(Text),
}).check(
  Schema.makeFilter((value) =>
    value.seconds === 0
      ? value.for_per60 === null && value.against_per60 === null
      : value.for_per60 !== null &&
        value.against_per60 !== null &&
        close(value.for_per60, per60(value.for_mass, value.seconds)!) &&
        close(value.against_per60, per60(value.against_mass, value.seconds)!),
  ),
);
export const AbsentContextCoverage = Schema.Struct({
  season: Season,
  player_id: Id,
  population: ContextPopulation,
  availability: Schema.Literal("absent"),
  explanation: Text,
  known_excluded_seconds: Schema.Null,
  unquantified_gap: Schema.Literal(true),
  reason_counts: Schema.Array(Schema.Never),
  source_ids: Schema.Array(Schema.Never),
  method_ids: Schema.Array(Schema.Never),
});
export const ApiContextCoverage = Schema.Union([ContextCoverage, AbsentContextCoverage]);
export const ContextResponse = Schema.Struct({
  ...Envelope.fields,
  mode: Schema.Literals(["on_off", "with_without"]),
  selected_players: Schema.Array(Id),
  population: ContextPopulation,
  groups: Schema.Array(ContextGroup),
  coverage: Schema.Array(ApiContextCoverage),
}).check(
  Schema.makeFilter((value) => {
    if (
      ["recorded_all_attempts", "recorded_goals", "recorded_locatable_unblocked"].includes(
        value.population,
      ) &&
      value.groups.some(
        (group) =>
          !Number.isSafeInteger(group.for_mass) ||
          !Number.isSafeInteger(group.against_mass) ||
          (group.locations !== null &&
            group.locations.some(
              (row) =>
                !Number.isSafeInteger(row.for_mass) || !Number.isSafeInteger(row.against_mass),
            )),
      )
    )
      return false;
    if (
      !unique(value.selected_players) ||
      value.selected_players.length < 1 ||
      value.selected_players.length > 3 ||
      (value.mode === "on_off" && value.selected_players.length !== 1)
    )
      return false;
    if (
      !value.coverage.every(
        (row) => row.season === value.season.season && row.population === value.population,
      )
    )
      return false;
    if (value.coverage.some((row) => row.availability !== "provided"))
      return value.groups.length === 0;
    const labels = value.mode === "on_off" ? ["on", "off"] : ["together", "apart"];
    return (
      value.coverage.length > 0 &&
      value.groups.length === 2 &&
      value.groups.every(
        (group, index) =>
          group.group === labels[index] &&
          (value.population === "recorded_goals"
            ? group.on_net_for !== null && group.on_net_against !== null
            : group.on_net_for === null && group.on_net_against === null) &&
          (["recorded_locatable_unblocked", "neutral_locatable_unblocked_value"].includes(
            value.population,
          )
            ? group.locations !== null
            : group.locations === null),
      )
    );
  }),
);
export type ContextResponse = typeof ContextResponse.Type;
export const InvalidSelection = Schema.Struct({
  _tag: Schema.Literal("InvalidSelection"),
  message: Text,
}).pipe(HttpApiSchema.status(400));
export const NotFound = Schema.Struct({ _tag: Schema.Literal("NotFound"), message: Text }).pipe(
  HttpApiSchema.status(404),
);
export const ApiError = Schema.Union([
  InvalidSelection,
  NotFound,
  InvalidPlayerId,
  PlayerNotFound,
  InvalidSeasonSelection,
  SeasonNotFound,
  ReadFailure,
]);
export type ApiError = typeof ApiError.Type;
const QueryValue = Schema.optional(Schema.Union([Schema.String, Schema.Array(Schema.String)]));
const errors = [
  InvalidSelection,
  NotFound,
  InvalidPlayerId,
  PlayerNotFound,
  InvalidSeasonSelection,
  SeasonNotFound,
  ReadFailure,
] as const;
export const PlayerAnalysisApi = HttpApi.make("player-analysis").add(
  HttpApiGroup.make("analysis").add(
    HttpApiEndpoint.get("league", "/api/league", {
      query: { season: QueryValue, kind: QueryValue, family: QueryValue, strength: QueryValue },
      success: LeagueResponse,
      error: errors,
    }),
    HttpApiEndpoint.get("player", "/api/players/:playerId", {
      params: { playerId: Schema.String },
      query: { season: QueryValue },
      success: PlayerResponse,
      error: errors,
    }),
    HttpApiEndpoint.get("maps", "/api/maps", {
      query: {
        season: QueryValue,
        players: QueryValue,
        family: QueryValue,
        strength: QueryValue,
        view: QueryValue,
        population: QueryValue,
        type: QueryValue,
      },
      success: MapsResponse,
      error: errors,
    }),
    HttpApiEndpoint.get("evidence", "/api/players/:playerId/evidence", {
      params: { playerId: Schema.String },
      query: {
        season: QueryValue,
        family: QueryValue,
        strength: QueryValue,
        population: QueryValue,
        type: QueryValue,
        outcome: QueryValue,
        shot_type: QueryValue,
        blocked_contacts: QueryValue,
      },
      success: EvidenceResponse,
      error: errors,
    }),
    HttpApiEndpoint.get("context", "/api/players/:playerId/context", {
      params: { playerId: Schema.String },
      query: {
        season: QueryValue,
        mode: QueryValue,
        population: QueryValue,
        teammates: QueryValue,
      },
      success: ContextResponse,
      error: errors,
    }),
  ),
);
export {
  parseLeagueSelection,
  parseMapSelection,
  parsePlayerSelection,
  parseEvidenceSelection,
  parseContextSelection,
  selectSeason,
  SelectionError,
} from "./player-analysis-selections.js";
export type MapSelection = typeof MapSelection.Type;
export type EvidenceSelection = typeof EvidenceSelection.Type;
export type ContextSelection = typeof ContextSelection.Type;
export const fieldLabels = {
  not_computed: "not computed",
  missing_tracking: "tracked primary-pass observations are not available",
  skating_access: "historical skating source access is unverified",
  failed_fit: "fit failed",
  no_exposure: "no eligible exposure",
  uncertainty: "uncertainty not estimated",
  prior_only: "hypothetical; prior-only estimate",
} as const;
