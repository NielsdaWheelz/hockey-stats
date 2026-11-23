import * as Schema from "effect/Schema";
import * as Struct from "effect/Struct";
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
export const preservesObservedAffiliations = (
  teams: readonly Team[],
  observed: readonly Team[],
): boolean =>
  observed.every((old) =>
    teams.some((team) => team.id === old.id && team.abbreviation === old.abbreviation),
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
  "reported_shifts_unavailable",
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
      !value.prior_only || !value.current_season_information,
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
  "execution_breakdown.reference.expected_goals",
  "execution_breakdown.reference.mean_opportunity",
  "execution_breakdown.reference.observed_minus_expected_goals",
  "execution_breakdown.actor.expected_goals",
  "execution_breakdown.actor.mean_opportunity",
  "execution_breakdown.actor.observed_minus_expected_goals",
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
        "ev_state",
        "derivation",
        "successor_panel",
        "territory_reference",
        "execution_score",
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
      ((value.design_sha256 !== null && value.training_cutoff !== null) ||
        (value.evidence.length > 0 && value.assessment.findings.length > 0)) &&
      (value.family !== "execution" ||
        !value.assessment.findings.some((finding) =>
          finding.quantities.some((quantity) =>
            [
              "execution_breakdown.probability",
              "execution_breakdown.effect",
              "execution_breakdown.expected_successes",
            ].includes(quantity),
          ),
        )),
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
}).check(
  Schema.makeFilter((value) => {
    const starts = Object.values(value.shift_starts);
    const startTotal = starts.every((bin) => bin.count !== null)
      ? starts.reduce((sum, bin) => sum + (bin.count ?? 0), 0)
      : null;
    if (starts.some((bin) => bin.share.value !== null &&
      (bin.count === null || startTotal === null || startTotal <= 0 ||
        !close(bin.share.value, bin.count / startTotal)))) return false;
    const known = [value.score.leading, value.score.tied, value.score.trailing];
    const knownTotal = known.every((bin) => bin.seconds !== null)
      ? known.reduce((sum, bin) => sum + (bin.seconds ?? 0), 0)
      : null;
    const unknown = value.score.unknown;
    const allTotal = knownTotal !== null && unknown.seconds !== null
      ? knownTotal + unknown.seconds : null;
    return known.every((bin) => bin.share.value === null ||
      (bin.seconds !== null && knownTotal !== null && knownTotal > 0 &&
        close(bin.share.value, bin.seconds / knownTotal))) &&
      (unknown.share.value === null || (unknown.seconds !== null && allTotal !== null &&
        allTotal > 0 && close(unknown.share.value, unknown.seconds / allTotal)));
  }),
);
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
const spatialState = Schema.Literals(["5v5", "5v4", "5v3", "4v3"]);
const headStateSupport = Schema.Struct({
  state: spatialState,
  included_seconds: Rate,
  likelihood_events: Count,
  eligible_origin_weight: Rate,
});
const spatialHeadSupport = Schema.Struct({
  available: Schema.Boolean,
  included_seconds: Schema.NullOr(Rate),
  likelihood_events: Schema.NullOr(Count),
  eligible_origin_weight: Schema.NullOr(Rate),
  current_season_information: Schema.NullOr(Schema.Boolean),
  prior_only: Schema.NullOr(Schema.Boolean),
  prior_kind: Schema.NullOr(Schema.Literals(["entry", "carry"])),
  prior_anchor_season: Schema.NullOr(Season),
  prior_seasons: Schema.Array(Season).check(Schema.makeFilter(sortedStrings)),
  state_support: Schema.NullOr(Schema.Array(headStateSupport)),
  reason: Schema.NullOr(Text),
}).check(Schema.makeFilter((value) => {
  const counts = [value.included_seconds, value.likelihood_events, value.eligible_origin_weight];
  if (!value.available)
    return counts.every((count) => count === null) && value.current_season_information === null &&
      value.prior_only === null && value.prior_kind === null && value.prior_anchor_season === null &&
      value.prior_seasons.length === 0 && value.state_support === null && value.reason !== null;
  if (counts.some((count) => count === null) || value.reason !== null || value.state_support === null ||
      value.current_season_information === null || value.prior_only !== !value.current_season_information)
    return false;
  return (value.prior_kind === "entry"
    ? value.prior_anchor_season === null && value.prior_seasons.length === 0
    : value.prior_kind === "carry" && value.prior_seasons.length > 0 &&
      value.prior_anchor_season === value.prior_seasons.at(-1)) &&
    value.state_support.reduce((sum, row) => sum + row.likelihood_events, 0) === value.likelihood_events &&
    close(value.state_support.reduce((sum, row) => sum + row.included_seconds, 0), value.included_seconds!) &&
    close(value.state_support.reduce((sum, row) => sum + row.eligible_origin_weight, 0), value.eligible_origin_weight!);
}));
const spatialActualContext = Schema.Struct({
  available: Schema.Boolean,
  included_seconds: Schema.NullOr(Rate),
  states: Schema.NullOr(Schema.Array(Schema.Struct({state: spatialState, seconds: Rate, weight: Probability}))),
  reason: Schema.NullOr(Text),
}).check(Schema.makeFilter((value) => {
  if (!value.available)
    return value.reason !== null && value.states === null &&
      (value.reason === "no_exposure" ? value.included_seconds === 0 : value.included_seconds === null);
  return value.reason === null && value.included_seconds !== null && value.included_seconds > 0 &&
    value.states !== null && value.states.length > 0 &&
    close(value.states.reduce((sum, row) => sum + row.seconds, 0), value.included_seconds) &&
    close(value.states.reduce((sum, row) => sum + row.weight, 0), 1) &&
    value.states.every((row) => close(row.weight, row.seconds / value.included_seconds!));
}));
export const SpatialEvidence = Schema.Struct({
  fit_family: Schema.Literals(["ev", "st"]),
  annual_state: Receipt,
  reference_sha256: Digest,
  state_support: Schema.Array(Schema.Struct({
    state: spatialState,
    physical_seconds: Rate,
    directed_seconds: Rate,
    attempts: Count,
    origin_weight: Rate,
    baseline_current_information: Schema.Struct({volume: Schema.Boolean, shape: Schema.Boolean, quality: Schema.Boolean}),
  })),
  roles: Schema.Array(Schema.Struct({
    role: Schema.Literals(["offense", "defense"]),
    coefficient_support: Schema.Struct({volume: spatialHeadSupport, shape: spatialHeadSupport, quality: spatialHeadSupport}),
    actual_context: spatialActualContext,
  })),
  method_id: Text,
}).check(Schema.makeFilter((value) => {
  const fittedStates = value.fit_family === "ev" ? ["5v5"] : ["5v4", "5v3", "4v3"];
  const selectedStates = value.state_support.map((row) => row.state);
  if (selectedStates.length === 0 || !unique(selectedStates) ||
      selectedStates.some((state, index) => !fittedStates.includes(state) ||
        (index > 0 && fittedStates.indexOf(selectedStates[index - 1]) >= fittedStates.indexOf(state))))
    return false;
  if (value.fit_family === "ev"
    ? value.roles.length !== 2 || value.roles[0].role !== "offense" || value.roles[1].role !== "defense"
    : value.roles.length !== 1)
    return false;
  for (const row of value.state_support) {
    if (!close(row.directed_seconds, row.physical_seconds * (value.fit_family === "ev" ? 2 : 1)) ||
        row.baseline_current_information.volume !== (row.directed_seconds > 0 || row.attempts > 0) ||
        row.baseline_current_information.shape !== (row.origin_weight > 0) ||
        row.baseline_current_information.quality !== (row.origin_weight > 0))
      return false;
  }
  for (const role of value.roles) {
    const heads = Object.values(role.coefficient_support);
    if (role.actual_context.available && heads.some((head) => !head.available)) return false;
    for (const kind of ["volume", "shape", "quality"] as const) {
      const head = role.coefficient_support[kind];
      if (!head.available) continue;
      if (JSON.stringify(head.state_support!.map((row) => row.state)) !== JSON.stringify(fittedStates) ||
          head.current_season_information !== (kind === "volume"
            ? head.included_seconds! > 0 || head.likelihood_events! > 0
            : head.eligible_origin_weight! > 0))
        return false;
    }
    if (role.actual_context.available && JSON.stringify(role.actual_context.states!.map((row) => row.state)) !== JSON.stringify(selectedStates))
      return false;
    if (role.actual_context.available)
      for (const state of role.actual_context.states!)
        for (const head of heads)
          if (head.available && !close(head.state_support!.find((row) => row.state === state.state)!.included_seconds, state.seconds))
            return false;
    if (role.actual_context.reason === "no_exposure")
      for (const head of heads)
        if (head.available && !close(head.state_support!.filter((row) => selectedStates.includes(row.state))
          .reduce((sum, row) => sum + row.included_seconds, 0), 0))
          return false;
  }
  return true;
}));
export type SpatialEvidence = typeof SpatialEvidence.Type;
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
const executionMasses = { u: Rate, uq: Rate, uqr: Rate, uqrg: Rate };
const focalMasses = {
  u: Schema.NullOr(Rate),
  uq: Schema.NullOr(Rate),
  uqr: Schema.NullOr(Rate),
  uqrg: Schema.NullOr(Rate),
};
export const ExecutionReferencePanel = Schema.Struct({
  panel_id: Text,
  opportunities: Count,
  setup_weight: Rate,
  neutral: Schema.Struct(executionMasses),
  focal_shooter: Schema.Struct(focalMasses),
  setting_setup: Schema.Struct({
    neutral_goal_mass: Rate,
    focal_goal_mass: Schema.NullOr(Rate),
  }),
}).check(
  Schema.makeFilter((value) => {
    for (const masses of [value.neutral, value.focal_shooter]) {
      let previous: number | null = value.opportunities;
      for (const field of ["u", "uq", "uqr", "uqrg"] as const) {
        const mass = masses[field];
        if (mass !== null && (previous === null || mass > previous))
          return false;
        previous = mass;
      }
    }
    return (
      close(value.setup_weight, 0.8 * value.opportunities) &&
      value.setting_setup.neutral_goal_mass <= value.setup_weight &&
      value.setting_setup.neutral_goal_mass <= value.neutral.uqrg &&
      (value.setting_setup.focal_goal_mass === null ||
        value.setting_setup.focal_goal_mass <= value.setup_weight)
    );
  }),
);
const coefficientFields = {
  available: Schema.Boolean,
  likelihood_events: Schema.NullOr(Count),
  prior_only: Schema.NullOr(Schema.Boolean),
  prior_seasons: Schema.Array(Season).check(Schema.makeFilter(sortedStrings)),
  reason: Schema.NullOr(Text),
};
const validCoefficient = (value: {
  available: boolean;
  likelihood_events: number | null;
  prior_only: boolean | null;
  prior_seasons: readonly string[];
  reason: string | null;
}) =>
  value.available
    ? value.prior_only !== null &&
      (value.likelihood_events !== null || value.reason !== null)
    : value.likelihood_events === null &&
      value.prior_only === null &&
      value.prior_seasons.length === 0 &&
      value.reason !== null;
const executionCoefficient = Schema.Struct(coefficientFields).check(
  Schema.makeFilter(validCoefficient),
);
export const ExecutionCoefficientSupport = Schema.Struct({
  shooter: Schema.Struct({
    u: executionCoefficient,
    q: executionCoefficient,
    r: executionCoefficient,
    g: executionCoefficient,
  }),
  setter: Schema.Struct({
    g: Schema.Struct({
      ...coefficientFields,
      candidate_events: Schema.NullOr(Count),
      mean_coupled_events: Schema.NullOr(Count),
    }).check(
      Schema.makeFilter(
        (value) =>
          validCoefficient(value) &&
          (value.available ||
            (value.candidate_events === null &&
              value.mean_coupled_events === null)) &&
          (value.likelihood_events === null ||
            ((value.candidate_events === null ||
              value.candidate_events <= value.likelihood_events) &&
              (value.mean_coupled_events === null ||
                value.mean_coupled_events <= value.likelihood_events))),
      ),
    ),
  }),
});
export const ExecutionPairedEvidence = Schema.Struct({
  source_attempts: Count,
  paired_attempts: Count,
  unvalued_source_attempts: Count,
  danger_unavailable: Schema.Struct({
    events: Count,
    observed_goals: Count,
    reference_expected_goals: Rate,
    actor_expected_goals: Rate,
  }),
}).check(
  Schema.makeFilter(
    (value) =>
      value.source_attempts ===
        value.paired_attempts + value.unvalued_source_attempts &&
      value.danger_unavailable.events <= value.paired_attempts &&
      value.danger_unavailable.observed_goals <=
        value.danger_unavailable.events &&
      value.danger_unavailable.reference_expected_goals <=
        value.danger_unavailable.events &&
      value.danger_unavailable.actor_expected_goals <=
        value.danger_unavailable.events,
  ),
);
export const SkaterExecution = Schema.Struct({
  ...executionFields,
  reference_panel: ExecutionReferencePanel,
  coefficient_support: ExecutionCoefficientSupport,
  paired_evidence: ExecutionPairedEvidence,
  support: executionSupport,
  method_id: Text,
}).check(
  Schema.makeFilter((value) => {
    const panel = value.reference_panel;
    const neutral = panel.neutral;
    const focal = panel.focal_shooter;
    const coefficients = value.coefficient_support.shooter;
    let available = true;
    for (const head of ["u", "q", "r", "g"] as const) {
      available = available && coefficients[head].available;
      const prefix = { u: "u", q: "uq", r: "uqr", g: "uqrg" } as const;
      if ((focal[prefix[head]] !== null) !== available) return false;
    }
    if (
      (panel.setting_setup.focal_goal_mass !== null) !==
      value.coefficient_support.setter.g.available
    )
      return false;
    const ratio = (numerator: number | null, denominator: number | null) =>
      numerator === null || denominator === null || denominator === 0
        ? null
        : numerator / denominator;
    const stages = [
      [
        "avoid_block_probability",
        ratio(focal.u, panel.opportunities),
        ratio(neutral.u, panel.opportunities),
      ],
      [
        "on_net_probability",
        ratio(focal.uq, focal.u),
        ratio(neutral.uq, neutral.u),
      ],
      [
        "recorded_stop_probability",
        ratio(focal.uqr, focal.uq),
        ratio(neutral.uqr, neutral.uq),
      ],
      [
        "conversion_probability",
        ratio(focal.uqrg, focal.uqr),
        ratio(neutral.uqrg, neutral.uqr),
      ],
    ] as const;
    for (const [field, focalRatio, neutralRatio] of stages) {
      const level =
        focalRatio === null
          ? null
          : field === "recorded_stop_probability"
            ? 1 - focalRatio
            : focalRatio;
      const baseline =
        neutralRatio === null
          ? null
          : field === "recorded_stop_probability"
            ? 1 - neutralRatio
            : neutralRatio;
      const published = value[field].value;
      const difference = value[`${field}_difference`].value;
      if (difference !== null && (difference < -1 || difference > 1)) return false;
      const denominator =
        field === "on_net_probability"
          ? "u"
          : field === "recorded_stop_probability"
            ? "uq"
            : field === "conversion_probability"
              ? "uqr"
              : null;
      const numerator =
        field === "avoid_block_probability"
          ? "u"
          : field === "on_net_probability"
            ? "uq"
            : field === "recorded_stop_probability"
              ? "uqr"
              : "uqrg";
      const focalAvailable = focal[numerator] !== null;
      const focalUnderflow =
        panel.opportunities > 0 &&
        focalAvailable &&
        denominator !== null &&
        focal[denominator] === 0;
      const neutralUnderflow =
        panel.opportunities > 0 &&
        denominator !== null &&
        neutral[denominator] === 0;
      if (focalUnderflow && published === null) return false;
      if (
        (focalUnderflow || neutralUnderflow) &&
        focalAvailable &&
        difference === null
      )
        return false;
      if (
        !focalUnderflow &&
        (level === null
          ? published !== null
          : published === null || !close(published, level))
      )
        return false;
      if (
        !focalUnderflow &&
        !neutralUnderflow &&
        (level === null || baseline === null
          ? difference !== null
          : difference === null || !close(difference, level - baseline))
      )
        return false;
    }
    for (const [field, numerator, denominator] of [
      [
        "finishing_goals_per100_attempts",
        focal.uqrg === null ? null : 100 * (focal.uqrg - neutral.uqrg),
        panel.opportunities,
      ],
      [
        "setting_goals_per100_assisted_opportunities",
        panel.setting_setup.focal_goal_mass === null
          ? null
          : 100 *
            (panel.setting_setup.focal_goal_mass -
              panel.setting_setup.neutral_goal_mass),
        panel.setup_weight,
      ],
    ] as const) {
      const expected = ratio(numerator, denominator);
      const actual = value[field].value;
      if (
        expected === null
          ? actual !== null
          : actual === null || !close(actual, expected)
      )
        return false;
    }
    const qualification = value.support.finishing_goals_per100_attempts;
    for (const field of Object.keys(executionSupport.fields) as (keyof typeof executionFields)[]) {
      const support = value.support[field];
      if (support.eligible_weight !== null ||
          support.included_seconds !== qualification.included_seconds ||
          support.known_excluded_seconds !== qualification.known_excluded_seconds ||
          support.unquantified_gap !== qualification.unquantified_gap ||
          JSON.stringify(support.reason_counts) !== JSON.stringify(qualification.reason_counts)) return false;
      const heads = field.startsWith("avoid_block") ? ["u"] as const
        : field.startsWith("on_net") ? ["u", "q"] as const
        : field.startsWith("recorded_stop") ? ["u", "q", "r"] as const
        : ["u", "q", "r", "g"] as const;
      const terms = field.startsWith("setting") ? [value.coefficient_support.setter.g]
        : heads.map(head => value.coefficient_support.shooter[head]);
      const complete = terms.every(term => term.available);
      if (support.prior_only !== (complete && terms.every(term => term.prior_only)) ||
          JSON.stringify(support.prior_seasons) !== JSON.stringify([...new Set(terms.flatMap(term => term.prior_seasons))].sort())) return false;
      if (!complete || terms.some(term => term.likelihood_events === null)) {
        if (support.events !== null || (!complete && support.current_season_information)) return false;
      } else {
        const counts = terms.map(term => term.likelihood_events!);
        if (support.events === null || support.events < Math.max(...counts) ||
            support.events > counts.reduce((total, count) => total + count, 0) ||
            support.current_season_information !== (support.events > 0)) return false;
      }
    }
    return true;
  }),
);
const mechanismCoefficientSupport = Schema.Struct({
  status: Schema.Literals(["complete", "failed", "unavailable"]),
  current_season_information: Schema.Boolean,
  prior_only: Schema.Boolean,
  prior_kind: Schema.NullOr(Schema.Literals(["entry", "carry"])),
  prior_anchor_season: Schema.NullOr(Season),
  prior_seasons: Schema.Array(Season),
  likelihood_events: Count,
  information_weight: Rate,
}).check(Schema.makeFilter((value) =>
  sortedStrings(value.prior_seasons) && value.current_season_information === (value.information_weight > 0) &&
  (value.status === "complete"
    ? value.prior_only === !value.current_season_information && (value.prior_kind === "entry"
      ? value.prior_anchor_season === null && value.prior_seasons.length === 0
      : value.prior_kind === "carry" && value.prior_seasons.length > 0 && value.prior_anchor_season === value.prior_seasons.at(-1))
    : !value.prior_only && value.prior_kind === null && value.prior_anchor_season === null && value.prior_seasons.length === 0)));
const minorValuation = Schema.Struct({
  available: Schema.Boolean, reason: Schema.NullOr(Text),
  a: Schema.NullOr(Rate), b: Schema.NullOr(Rate), e_f: Schema.NullOr(Rate), e_a: Schema.NullOr(Rate),
  T_hours: Schema.Literal(2 / 60), tau_hours: Schema.NullOr(Rate), V_goals: Schema.NullOr(Schema.Finite),
  sh_support: Schema.Struct({included_seconds: Rate, attempts: Count, neutral_goal_mass: Rate,
    known_excluded_seconds: Rate, unquantified_gap: Schema.Boolean}),
  inputs: Schema.Struct({ev_state: Receipt, st_state: Receipt, execution_score: Receipt, reduction: Receipt}),
}).check(Schema.makeFilter((value) => {
  const sh = value.sh_support;
  if (sh.neutral_goal_mass > sh.attempts || (value.b !== null &&
      (sh.included_seconds <= 0 || !close(value.b, sh.neutral_goal_mass / (sh.included_seconds / 3600))))) return false;
  const tau = value.a === null ? null : value.a === 0 ? 2 / 60 : -Math.expm1(-value.a * 2 / 60) / value.a;
  if (tau === null ? value.tau_hours !== null : value.tau_hours === null || !close(tau, value.tau_hours)) return false;
  return value.available
    ? value.reason === null && value.a !== null && value.b !== null && value.e_f !== null && value.e_a !== null &&
      tau !== null && value.V_goals !== null && close(value.V_goals, (value.a - value.e_f - value.b + value.e_a) * tau)
    : value.reason !== null && value.V_goals === null;
}));
export const PenaltyEvidence = Schema.Struct({
  annual_state: Receipt, coefficient_support: mechanismCoefficientSupport, reference_id: Digest,
  neutral_per60: Schema.NullOr(Rate.check(Schema.isGreaterThan(0))),
  drawn_complete_per60: Schema.NullOr(Rate.check(Schema.isGreaterThan(0))),
  taken_complete_per60: Schema.NullOr(Rate.check(Schema.isGreaterThan(0))), valuation: minorValuation,
});
const mechanismStateSupport = Schema.Struct({
  strength: ExecutionStrength, included_seconds: Rate, known_excluded_seconds: Rate, unquantified_gap: Schema.Boolean,
  team_choices: Count, personal_attempts: Count, excluded_possible_choices: Count,
}).check(Schema.makeFilter((value) => value.personal_attempts <= value.team_choices));
export const ShootinessEvidence = Schema.Struct({
  annual_state: Receipt, coefficient_support: mechanismCoefficientSupport, reference_id: Digest,
  position_group: Schema.Literals(["F", "D", "unknown"]),
  reference_unit: Schema.Struct({forwards: Count.check(Schema.isGreaterThan(0)), defenders: Count.check(Schema.isGreaterThan(0))}),
  states: Schema.Array(mechanismStateSupport),
}).check(Schema.makeFilter((value) =>
  JSON.stringify(value.states.map((state) => state.strength)) === JSON.stringify(ExecutionStrength.literals) &&
  value.states.reduce((sum, state) => sum + state.team_choices, 0) === value.coefficient_support.likelihood_events &&
  value.coefficient_support.likelihood_events === value.coefficient_support.information_weight));
const mechanismSupportMatches = (support: typeof Support.Type, coefficient: typeof mechanismCoefficientSupport.Type) =>
  support.current_season_information === coefficient.current_season_information && support.prior_only === coefficient.prior_only &&
  JSON.stringify(support.prior_seasons) === JSON.stringify(coefficient.prior_seasons) &&
  support.events === coefficient.likelihood_events && support.eligible_weight === coefficient.information_weight;
const mechanismEstimateMatches = (estimate: Estimate, available: boolean, status: typeof mechanismCoefficientSupport.Type.status) =>
  estimate.uncertainty.kind === "not_estimated" && (estimate.value !== null) === available &&
  (status === "failed" ? estimate.unavailable_reason === "failed_fit"
    : status === "unavailable" ? estimate.unavailable_reason === "no_exposure" : true);
export const SkaterShootiness = Schema.Struct({
  probability: ProbabilityEstimate, neutral_probability: ProbabilityEstimate, difference: Estimate,
  support: Support, method_id: Text, evidence: ShootinessEvidence,
}).check(Schema.makeFilter((value) => {
  const coefficient = value.evidence.coefficient_support;
  const available = coefficient.status === "complete" && value.evidence.position_group !== "unknown";
  return mechanismSupportMatches(value.support, coefficient) &&
    [value.probability, value.neutral_probability, value.difference].every((estimate) =>
      mechanismEstimateMatches(estimate, available, coefficient.status) &&
      (coefficient.status === "complete" && value.evidence.position_group === "unknown" ? estimate.unavailable_reason === "missing_source" : true)) &&
    (!available || close(value.difference.value!, value.probability.value! - value.neutral_probability.value!));
}));
export const SkaterPenalties = Schema.Struct({
  drawn_per60: Estimate, taken_per60: Estimate, drawn_value_per60: Estimate, taken_value_per60: Estimate,
  recorded_drawn: penaltyRecord, recorded_taken: penaltyRecord, recorded_served: penaltyRecord,
  support: Support, method_id: Text, evidence: PenaltyEvidence,
}).check(Schema.makeFilter((value) => {
  const evidence = value.evidence, coefficient = evidence.coefficient_support, complete = coefficient.status === "complete";
  if (!mechanismSupportMatches(value.support, coefficient) || value.support.included_seconds === null ||
      !close(value.support.included_seconds, coefficient.information_weight * 3600) ||
      [evidence.neutral_per60, evidence.drawn_complete_per60, evidence.taken_complete_per60].some((rate) => (rate !== null) !== complete)) return false;
  for (const [rate, level, valuation, sign] of [
    [value.drawn_per60, evidence.drawn_complete_per60, value.drawn_value_per60, 1],
    [value.taken_per60, evidence.taken_complete_per60, value.taken_value_per60, -1],
  ] as const) {
    if (!mechanismEstimateMatches(rate, complete, coefficient.status) ||
        !mechanismEstimateMatches(valuation, complete && evidence.valuation.available, coefficient.status) ||
        (complete && !close(rate.value!, level! - evidence.neutral_per60!)) ||
        (complete && evidence.valuation.available && !close(valuation.value!, sign * rate.value! * evidence.valuation.V_goals!)) ||
        (complete && !evidence.valuation.available && (!["failed_fit", "no_exposure", "missing_source"].includes(evidence.valuation.reason!) ||
          valuation.unavailable_reason !== evidence.valuation.reason))) return false;
  }
  return true;
}));
export const validateMechanismSelection = (value: {
  readonly season: string; readonly strength: string | null;
  readonly data: typeof SkaterShootiness.Type | typeof SkaterPenalties.Type;
  readonly methods: Readonly<Record<string, Method>>;
}): boolean => {
  const data = value.data, evidence = data.evidence, coefficient = evidence.coefficient_support, method = value.methods[data.method_id];
  const penalty = "drawn_per60" in data;
  if (method === undefined || method.family !== (penalty ? "penalties" : "shootiness") ||
      !method.evidence.some((binding) => binding.uri === evidence.annual_state.uri && binding.sha256 === evidence.annual_state.sha256) ||
      !method.inputs.some((input) => input.role === "annual_state" && input.sha256 === evidence.annual_state.sha256 &&
        input.seasons.length === 1 && input.seasons[0] === value.season) ||
      coefficient.prior_seasons.some((year) => year >= value.season || !method.fit_seasons.includes(year))) return false;
  if ("position_group" in evidence) {
    const index = ExecutionStrength.literals.indexOf(value.strength as typeof ExecutionStrength.Type);
    const units = [[3,2],[4,1],[4,1],[3,1],[2,2],[1,2],[1,2]] as const;
    if (index < 0 || evidence.reference_unit.forwards !== units[index][0] || evidence.reference_unit.defenders !== units[index][1]) return false;
    const state = evidence.states[index];
    if (data.support.included_seconds !== state.included_seconds || data.support.known_excluded_seconds !== state.known_excluded_seconds ||
        data.support.unquantified_gap !== state.unquantified_gap) return false;
  }
  return true;
};
export const stableSum = (values: readonly number[]): number => {
  let sum = 0,
    correction = 0;
  for (const value of values) {
    const next = sum + value;
    correction +=
      Math.abs(sum) >= Math.abs(value)
        ? sum - next + value
        : value - next + sum;
    sum = next;
  }
  return sum + correction;
};
const mapMassCloses = (
  native: readonly { readonly value: number }[],
  display: readonly { readonly mass: number }[],
  total: number,
  territory: boolean,
): boolean => {
  if (!territory)
    return (
      close(
        native.reduce((sum, row) => sum + row.value, 0),
        total,
      ) &&
      close(
        display.reduce((sum, row) => sum + row.mass, 0),
        total,
      )
    );
  const allowance =
    64 * 2 ** -52 * stableSum(native.map((row) => Math.abs(row.value)));
  return [
    stableSum(native.map((row) => row.value)),
    stableSum(display.map((row) => row.mass)),
  ].every(
    (sum) =>
      Number.isFinite(sum) &&
      Math.abs(sum - total) <=
        1e-9 + 1e-9 * Math.max(Math.abs(sum), Math.abs(total)) + allowance,
  );
};
export const territoryRoles = [
  "exit_offense",
  "entry_offense",
  "zone_retention",
  "entry_prevention",
] as const;
const territoryZones = ["D", "N", "O"] as const;
const territoryAges = [0, 10, 20, 40, 60, 90] as const;
const finiteVector = (length: number) =>
  Schema.Array(Schema.Finite).check(
    Schema.makeFilter((v) => v.length === length),
  );
const nonnegativeVector = (length: number) =>
  Schema.Array(Rate).check(Schema.makeFilter((v) => v.length === length));
const probabilityVector = (length: number) =>
  Schema.Array(Probability).check(
    Schema.makeFilter(
      (v) =>
        v.length === length &&
        close(
          v.reduce((a, b) => a + b, 0),
          1,
        ),
    ),
  );
const countVector = (length: number) =>
  Schema.Array(Count).check(Schema.makeFilter((v) => v.length === length));
const territoryReason = Schema.Literals([
  "event_kind_unresolved",
  "source_order_unresolved",
  "clock_unresolved",
  "orientation_unresolved",
  "conflicting_anchors",
  "report_barrier_unresolved",
  "membership_or_horizon_unavailable",
  "identity_conflict",
  "strength_conflict",
  "outside_five_on_five",
  "period_or_game_end",
  "restart_unproved",
  "restart_clock_mismatch",
  "shift_endpoint_unresolved",
  "shift_age_unavailable",
  "zone_unavailable",
]);
const territoryRoleEvidence = Schema.Struct({
  coefficient_support: mechanismCoefficientSupport,
  neutral_hazard_per_second: Schema.NullOr(Rate.check(Schema.isGreaterThan(0))),
  neutral_one_second_probability: Schema.NullOr(Probability),
});
export const TerritoryEvidence = Schema.Struct({
  annual_state: Receipt,
  prepared: Receipt,
  reference_id: Digest,
  qualification_seconds: Rate,
  roles: Schema.Struct({
    exit_offense: territoryRoleEvidence,
    entry_offense: territoryRoleEvidence,
    zone_retention: territoryRoleEvidence,
    entry_prevention: territoryRoleEvidence,
  }),
  nuisance_coverage: Schema.Struct({
    path_slot_seconds: Rate,
    terminal_carry_slot_seconds: Rate,
    whistle_risk_slot_seconds: Rate,
    whistle_incidences: Count,
    live_end_risk_slot_seconds: Rate,
    live_end_incidences: Count,
    decidable_whistle_trials: Count,
    ended_whistle_trials: Count,
    restart_pairs: Count,
    start_counts: countVector(4),
    on_the_fly_zone_counts: countVector(3),
    terminal_tails: Count,
    terminal_lag_seconds: Schema.NullOr(
      Schema.Struct({ p50: Rate, p90: Rate, p99: Rate, max: Rate }),
    ),
    censored_endpoints: Schema.Array(
      Schema.Struct({ reason: territoryReason, count: Count }),
    ),
    prior_only_cells: Schema.Array(
      Schema.Struct({
        process: Schema.Literals(["w", "d", "h"]),
        zone: Schema.Literals(territoryZones),
        age_lower: Schema.Literals(territoryAges),
      }),
    ),
    prior_only_restart_rows: Schema.Array(Schema.Literals(territoryZones)),
  }),
  shift_reference: Schema.Struct({
    available: Schema.Boolean,
    reason: Schema.NullOr(Text),
    receipt: Receipt,
    data: Schema.NullOr(
      Schema.Struct({
        initial_start_probabilities: probabilityVector(4),
        initial_on_the_fly_zone_probabilities: Schema.NullOr(
          probabilityVector(3),
        ),
        neutral_end_probabilities: probabilityVector(4),
        focal_end_probabilities: probabilityVector(4),
        end_difference: finiteVector(4),
        neutral_occupancy_seconds: nonnegativeVector(6),
        mean_shift_seconds: Rate.check(Schema.isGreaterThan(0)),
        shifts_per_1000_minutes: Rate.check(Schema.isGreaterThan(0)),
        survival_at_90: Probability,
        tail_time_fraction: Probability,
      }),
    ),
  }),
  successor_reference: Schema.Struct({
    available: Schema.Boolean,
    reason: Schema.NullOr(Text),
    ev_state: Receipt,
    panel: Schema.NullOr(Receipt),
    data: Schema.NullOr(
      Schema.Struct({
        for_goals_per_shift: finiteVector(4),
        against_goals_per_shift: finiteVector(4),
        for_absolute_terms_goals_per_shift: nonnegativeVector(4),
        against_absolute_terms_goals_per_shift: nonnegativeVector(4),
      }),
    ),
  }),
}).check(
  Schema.makeFilter((e) => {
    const c = e.nuisance_coverage,
      shift = e.shift_reference,
      s = e.shift_reference.data,
      successor = e.successor_reference,
      g = successor.data;
    if (
      [
        c.terminal_carry_slot_seconds,
        c.whistle_risk_slot_seconds,
        c.live_end_risk_slot_seconds,
      ].some(
        (x) => x > c.path_slot_seconds && !close(x, c.path_slot_seconds),
      ) ||
      c.ended_whistle_trials > c.decidable_whistle_trials ||
      c.decidable_whistle_trials > c.whistle_incidences ||
      c.on_the_fly_zone_counts.reduce((a, b) => a + b, 0) !==
        c.start_counts[3] ||
      (c.terminal_lag_seconds === null) !== (c.terminal_tails === 0)
    )
      return false;
    const lag = c.terminal_lag_seconds;
    if (
      lag !== null &&
      !(lag.p50 <= lag.p90 && lag.p90 <= lag.p99 && lag.p99 <= lag.max)
    )
      return false;
    const reasons = c.censored_endpoints.map((x) => x.reason);
    if (!sortedStrings(reasons)) return false;
    const cells = c.prior_only_cells.map(
      (x) =>
        ["w", "d", "h"].indexOf(x.process) * 18 +
        territoryZones.indexOf(x.zone) * 6 +
        territoryAges.indexOf(x.age_lower),
    );
    if (
      cells.some((x, i) => i > 0 && x <= cells[i - 1]) ||
      JSON.stringify(c.prior_only_restart_rows) !==
        JSON.stringify(
          territoryZones.filter((z) => c.prior_only_restart_rows.includes(z)),
        )
    )
      return false;
    for (const ref of [shift, successor])
      if (
        ref.available
          ? ref.data === null || ref.reason !== null
          : ref.data !== null || ref.reason === null
      )
        return false;
    if (
      shift.available &&
      (!territoryRoles.every(
        (role) => e.roles[role].coefficient_support.status === "complete",
      ) ||
        Math.min(
          c.whistle_risk_slot_seconds,
          c.live_end_risk_slot_seconds,
          c.decidable_whistle_trials,
          c.restart_pairs,
          c.start_counts.reduce((a, b) => a + b, 0),
        ) <= 0)
    )
      return false;
    if (successor.available && (!shift.available || successor.panel === null))
      return false;
    if (s !== null) {
      const total = c.start_counts.reduce((a, b) => a + b, 0),
        mean = s.mean_shift_seconds;
      if (
        !s.initial_start_probabilities.every((p, i) =>
          close(p, c.start_counts[i] / total),
        ) ||
        (s.initial_on_the_fly_zone_probabilities === null) !==
          (c.start_counts[3] === 0) ||
        (s.initial_on_the_fly_zone_probabilities !== null &&
          !s.initial_on_the_fly_zone_probabilities.every((p, i) =>
            close(p, c.on_the_fly_zone_counts[i] / c.start_counts[3]),
          )) ||
        !close(
          s.end_difference.reduce((a, b) => a + b, 0),
          0,
        ) ||
        !s.end_difference.every((d, i) =>
          close(
            d,
            s.focal_end_probabilities[i] - s.neutral_end_probabilities[i],
          ),
        ) ||
        s.neutral_occupancy_seconds
          .slice(0, 5)
          .some(
            (x, i) =>
              x >
              [10, 10, 20, 20, 30][i] + 1e-9 + 1e-9 * [10, 10, 20, 20, 30][i],
          ) ||
        !close(
          s.neutral_occupancy_seconds.reduce((a, b) => a + b, 0),
          mean,
        ) ||
        !close(s.shifts_per_1000_minutes, 60000 / mean) ||
        !close(s.tail_time_fraction, s.neutral_occupancy_seconds[5] / mean)
      )
        return false;
    }
    if (
      g !== null &&
      ![g.for_goals_per_shift, g.against_goals_per_shift].every((v, side) =>
        v.every(
          (x, i) =>
            Math.abs(x) <=
            [
              g.for_absolute_terms_goals_per_shift,
              g.against_absolute_terms_goals_per_shift,
            ][side][i],
        ),
      )
    )
      return false;
    return true;
  }),
);
export type TerritoryEvidence = typeof TerritoryEvidence.Type;
export const territoryReferenceBody = (
  e: TerritoryEvidence,
  season: string,
  purpose: string,
  recipe_id: string,
) => {
  const shift = e.shift_reference.data;
  const common =
    shift === null
      ? null
      : Object.fromEntries(
          Object.entries(shift).filter(
            ([key]) =>
              !["focal_end_probabilities", "end_difference"].includes(key),
          ),
        );
  return {
    schema_tag: "territory-evidence-v1-11-1",
    season,
    purpose,
    recipe_id,
    annual_state: e.annual_state,
    prepared: e.prepared,
    ev_state: e.successor_reference.ev_state,
    panel: e.successor_reference.panel,
    neutral_role_levels: Object.fromEntries(
      territoryRoles.map((role) => [
        role,
        {
          neutral_hazard_per_second: e.roles[role].neutral_hazard_per_second,
          neutral_one_second_probability:
            e.roles[role].neutral_one_second_probability,
        },
      ]),
    ),
    nuisance_coverage: e.nuisance_coverage,
    common_shift_data: common,
    successor_data: e.successor_reference.data,
  };
};
export const binary64DigestRepresentation = (value: unknown): unknown => {
  if (typeof value === "number") {
    if (!Number.isFinite(value))
      throw new Error("nonfinite reference digest input");
    const bytes = new Uint8Array(8);
    new DataView(bytes.buffer).setFloat64(0, value === 0 ? 0 : value, false);
    return [
      "f64",
      Array.from(bytes, (x) => x.toString(16).padStart(2, "0")).join(""),
    ];
  }
  if (Array.isArray(value)) return value.map(binary64DigestRepresentation);
  if (value !== null && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([key, item]) => [key, binary64DigestRepresentation(item)]),
    );
  return value;
};

const transition = Schema.Struct({
  hazard_per_second: NonnegativeEstimate,
  one_second_probability: ProbabilityEstimate,
  support: Support,
}).check(
  Schema.makeFilter(
    (value) =>
      value.one_second_probability.value === null ||
      (value.hazard_per_second.value !== null &&
        close(
          value.one_second_probability.value,
          -Math.expm1(-value.hazard_per_second.value),
        )),
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
  evidence: TerritoryEvidence,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter((data) => {
    const e = data.evidence,
      s = data.support,
      coefficients = territoryRoles.map(
        (role) => e.roles[role].coefficient_support,
      );
    if (
      !s.inferred_inputs.includes("territory") ||
      s.included_seconds !== e.qualification_seconds ||
      s.eligible_weight !== e.qualification_seconds ||
      s.current_season_information !==
        coefficients.every((c) => c.current_season_information) ||
      s.prior_only !==
        coefficients.every((c) => c.status === "complete" && c.prior_only) ||
      JSON.stringify(s.prior_seasons) !==
        JSON.stringify(
          [...new Set(coefficients.flatMap((c) => c.prior_seasons))].sort(),
        ) ||
      s.events === null ||
      s.events < Math.max(...coefficients.map((c) => c.likelihood_events)) ||
      s.events > coefficients.reduce((n, c) => n + c.likelihood_events, 0)
    )
      return false;
    for (const role of territoryRoles) {
      const row = data[role],
        neutral = e.roles[role],
        c = neutral.coefficient_support;
      const hazard =
        "hazard_per_second" in row
          ? row.hazard_per_second
          : "opponent_exit_hazard_per_second" in row
            ? row.opponent_exit_hazard_per_second
            : row.opponent_entry_hazard_per_second;
      const complete = c.status === "complete",
        avoidance = role === "zone_retention" || role === "entry_prevention";
      if (
        !row.support.inferred_inputs.includes("territory") ||
        !mechanismSupportMatches(row.support, c) ||
        row.support.included_seconds !== e.qualification_seconds ||
        !mechanismEstimateMatches(hazard, complete, c.status) ||
        !mechanismEstimateMatches(
          row.one_second_probability,
          complete,
          c.status,
        ) ||
        (neutral.neutral_hazard_per_second !== null) !== complete ||
        (neutral.neutral_one_second_probability !== null) !== complete
      )
        return false;
      if (
        complete &&
        (!(hazard.value! > 0) ||
          !close(
            row.one_second_probability.value!,
            avoidance ? Math.exp(-hazard.value!) : -Math.expm1(-hazard.value!),
          ) ||
          !close(
            neutral.neutral_one_second_probability!,
            avoidance
              ? Math.exp(-neutral.neutral_hazard_per_second!)
              : -Math.expm1(-neutral.neutral_hazard_per_second!),
          ))
      )
        return false;
    }
    if (
      e.roles.exit_offense.neutral_hazard_per_second !==
        e.roles.zone_retention.neutral_hazard_per_second ||
      e.roles.entry_offense.neutral_hazard_per_second !==
        e.roles.entry_prevention.neutral_hazard_per_second
    )
      return false;
    for (const [side, estimate] of [
      ["for", data.ice_won_goals_per_basket],
      ["against", data.ice_lost_goals_per_basket],
    ] as const) {
      if (
        estimate.uncertainty.kind !== "not_estimated" ||
        (estimate.value !== null) !== e.successor_reference.available
      )
        return false;
      const shift = e.shift_reference.data,
        g = e.successor_reference.data;
      if (shift !== null && g !== null) {
        const values =
          side === "for" ? g.for_goals_per_shift : g.against_goals_per_shift;
        const scales =
          side === "for"
            ? g.for_absolute_terms_goals_per_shift
            : g.against_absolute_terms_goals_per_shift;
        const expected =
          shift.shifts_per_1000_minutes *
          stableSum(
            shift.end_difference.map((d, i) => (d === 0 ? 0 : d * values[i])),
          );
        const allowance =
          64 *
          2 ** -52 *
          shift.shifts_per_1000_minutes *
          stableSum(
            shift.end_difference.map((d, i) => Math.abs(d) * scales[i]),
          );
        if (
          !Number.isFinite(expected) ||
          !Number.isFinite(allowance) ||
          Math.abs(estimate.value! - expected) >
            1e-9 +
              1e-9 * Math.max(Math.abs(estimate.value!), Math.abs(expected)) +
              allowance
        )
          return false;
        let pivot = -1;
        for (let index = 0; index < shift.end_difference.length; index++) {
          const weight = shift.end_difference[index];
          if (
            weight !== 0 &&
            (pivot === -1 || Math.abs(weight) > Math.abs(shift.end_difference[pivot]))
          )
            pivot = index;
        }
        const centeredTerms: number[] = [];
        for (let index = 0; index < shift.end_difference.length; index++) {
          const weight = shift.end_difference[index];
          if (weight !== 0 && index !== pivot)
            centeredTerms.push(weight * (values[index] - values[pivot]));
        }
        const centeredExpected =
          pivot === -1 ? 0 : shift.shifts_per_1000_minutes * stableSum(centeredTerms);
        if (
          !Number.isFinite(centeredExpected) ||
          Math.abs(estimate.value! - centeredExpected) >
            1e-9 +
              1e-9 * Math.max(Math.abs(estimate.value!), Math.abs(centeredExpected)) +
              allowance
        )
          return false;
      } else {
        const reason = coefficients.some((c) => c.status === "failed")
          ? "failed_fit"
          : coefficients.some((c) => c.status === "unavailable")
            ? "no_exposure"
            : "missing_source";
        if (estimate.unavailable_reason !== reason) return false;
      }
    }
    return true;
  }),
);
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
const goalieMassRecord = (size: number) => Schema.Struct({
  masses: Schema.Array(Schema.NullOr(Rate)),
  log_masses: Schema.Array(Schema.NullOr(Schema.Finite)),
}).check(Schema.makeFilter(record => {
  if (record.masses.length !== size || record.log_masses.length !== size) return false;
  for (let i = 0; i < size; i++) {
    const mass = record.masses[i], log = record.log_masses[i];
    if (mass === null ? log !== null : log === null ? mass !== 0 :
        Math.abs(mass - Math.exp(log)) > 1e-12 * Math.max(mass, Math.exp(log)) || !Number.isFinite(Math.exp(log)))
      return false;
    if (i > 0 && mass !== null && (record.masses[i - 1] === null ||
        (log !== null && (record.log_masses[i - 1] === null || log > record.log_masses[i - 1]!))))
      return false;
  }
  return true;
}));
const goalieHeadSupport = Schema.Struct({
  available: Schema.Boolean,
  likelihood_events: Count,
  prior_only: Schema.Boolean,
  prior_seasons: Schema.Array(Season).check(Schema.makeFilter(sortedStrings)),
  reason: Schema.NullOr(Schema.Literals(["head_incomplete", "actor_coefficient_unavailable"])),
}).check(Schema.makeFilter(head => head.available === (head.reason === null) &&
  (head.available || head.likelihood_events === 0) &&
  head.prior_only === (head.available && head.likelihood_events === 0)));
export const GoalieEvidence = Schema.Struct({
  neutral_values: Schema.Struct({
    miss_probability: Schema.NullOr(Probability),
    recorded_stop_probability: Schema.NullOr(Probability),
    conversion_probability: Schema.NullOr(Probability),
    recorded_reattempt_probability: Schema.NullOr(Probability),
    reattempt_neutral_goal_probability: Schema.NullOr(Probability),
    followup_danger: Schema.NullOr(Probability),
  }),
  masses: Schema.Struct({
    prefixes: Schema.Struct({ neutral: goalieMassRecord(4), focal: goalieMassRecord(4) }),
    continuation: Schema.Struct({ neutral: goalieMassRecord(3), focal: goalieMassRecord(3) }),
  }),
  coefficient_support: Schema.Struct({
    q: goalieHeadSupport, r: goalieHeadSupport, g: goalieHeadSupport,
    h: goalieHeadSupport, d: goalieHeadSupport,
  }),
  panels: Schema.Array(Schema.Struct({
    panel_id: Text,
    physical_state: Schema.Array(Count).check(Schema.makeFilter(state =>
      state.length === 4 && state[2] === 1 && state[3] === 1)),
    events: Count,
    origins: Count,
    events_sha256: Digest,
    arrays_sha256: Digest,
  })).check(Schema.makeFilter(panels => panels.length === 1 || panels.length === 3)),
});
const goalieDependencies = {
  stopping_goals_per100_on_net: ["r", "g"],
  miss_probability: ["q"],
  recorded_stop_probability: ["q", "r"],
  conversion_probability: ["q", "r", "g"],
  recorded_reattempt_probability: ["h"],
  reattempt_neutral_goal_probability: ["h", "d"],
  followup_danger: ["h", "d"],
} as const;
const goalieResultShape = Schema.Struct({
  ...goalieFields,
  support: goalieSupport,
  method_id: Text,
  evidence: GoalieEvidence,
});
export const GoalieResult = goalieResultShape.check(Schema.makeFilter(value => {
  const { masses, coefficient_support: heads, neutral_values } = value.evidence;
  const { prefixes, continuation } = masses;
  if (prefixes.neutral.masses.some(mass => mass === null) || prefixes.focal.masses[0] === null ||
      continuation.neutral.masses[0] === null || continuation.focal.masses[0] === null ||
      continuation.neutral.masses[0] !== continuation.focal.masses[0] ||
      continuation.neutral.log_masses[0] !== continuation.focal.log_masses[0]) return false;
  for (const [index, dependencies] of [[1, ["q"]], [2, ["q", "r"]], [3, ["q", "r", "g"]]] as const)
    if ((prefixes.focal.masses[index] !== null) !== dependencies.every(head => heads[head].available))
      return false;
  for (const reference of ["neutral", "focal"] as const)
    for (const [index, dependencies] of [[1, ["h"]], [2, ["h", "d"]]] as const)
      if ((continuation[reference].masses[index] !== null) !== dependencies.every(head =>
        reference === "neutral" ? heads[head].reason !== "head_incomplete" : heads[head].available))
        return false;
  const same = (actual: number | null, expected: number | null) =>
    actual === null || expected === null ? actual === expected :
      Math.abs(actual - expected) <= Math.max(1e-15, 1e-12 * Math.max(Math.abs(actual), Math.abs(expected)));
  for (const [field, group, numerator, denominator, complement] of [
    ["miss_probability", "prefixes", 1, 0, true],
    ["recorded_stop_probability", "prefixes", 2, 1, true],
    ["conversion_probability", "prefixes", 3, 2, false],
    ["recorded_reattempt_probability", "continuation", 1, 0, false],
    ["reattempt_neutral_goal_probability", "continuation", 2, 1, false],
    ["followup_danger", "continuation", 2, 0, false],
  ] as const) {
    const dependencies = goalieDependencies[field];
    for (const reference of ["neutral", "focal"] as const) {
      const logs = masses[group][reference].log_masses;
      const available = dependencies.every(head => reference === "neutral"
        ? heads[head].reason !== "head_incomplete" : heads[head].available);
      const delta = logs[numerator] === null ? -Infinity : logs[numerator]! - logs[denominator]!;
      const expected = !available || logs[denominator] === null ? null :
        complement ? -Math.expm1(delta) : Math.exp(delta);
      if (!same(reference === "neutral" ? neutral_values[field] : value[field].value, expected)) return false;
    }
    const focal = value[field].value, neutral = neutral_values[field];
    if (!same(value[`${field}_difference`].value,
        focal === null || neutral === null ? null : focal - neutral)) return false;
  }
  const denominators = {
    stopping_goals_per100_on_net: prefixes.neutral.masses[1],
    miss_probability: prefixes.neutral.masses[0],
    recorded_stop_probability: prefixes.neutral.masses[1],
    conversion_probability: prefixes.neutral.masses[2],
    recorded_reattempt_probability: continuation.neutral.masses[0],
    reattempt_neutral_goal_probability: continuation.neutral.masses[1],
    followup_danger: continuation.neutral.masses[0],
  };
  for (const field of Object.keys(goalieFields) as (keyof typeof goalieFields)[]) {
    const base = field.replace(/_difference$/, "") as keyof typeof goalieDependencies;
    const dependencies = goalieDependencies[base].map(head => heads[head]);
    const available = dependencies.every(head => head.available);
    const support = value.support[field];
    const priorSeasons = [...new Set(dependencies.flatMap(head => head.prior_seasons))].sort();
    if (support.eligible_weight !== denominators[base] || (value[field].value !== null && !available) ||
        support.current_season_information !== (available && dependencies.every(head => head.likelihood_events > 0)) ||
        support.prior_only !== (available && dependencies.every(head => head.prior_only)) ||
        JSON.stringify(support.prior_seasons) !== JSON.stringify(priorSeasons)) return false;
  }
  return true;
}));
export function validGoalieProjectionBinding(value: typeof GoalieResult.Type, season: string, strength: string) {
  const states = strength === "ev" ? ["5v5", "4v4", "3v3"] : strength === "pk" ? ["4v5", "3v5", "3v4"] : [strength];
  return value.evidence.panels.length === states.length && value.evidence.panels.every((panel, i) => {
    const [defending, attacking] = states[i].split("v").map(Number);
    return panel.physical_state[0] === attacking && panel.physical_state[1] === defending &&
      panel.panel_id === `execution-v1-06-1:${season}:${attacking},${defending},1`;
  }) && Object.values(value.evidence.coefficient_support).every(head => head.prior_seasons.every(year => year < season));
}
const sourceCountShape = Schema.Struct({
  provenance: SourceReference,
  unblocked_attempts: Schema.NullOr(Count),
  misses: Schema.NullOr(Count),
  shots_on_goal: Schema.NullOr(Count),
  saves: Schema.NullOr(Count),
  goals_against: Schema.NullOr(Count),
  save_percentage: ProbabilityEstimate,
  support: Support,
});
const validSourceCountTotals = (value: typeof sourceCountShape.Type) =>
  (value.misses === null || value.shots_on_goal === null ||
    value.unblocked_attempts === value.misses + value.shots_on_goal) &&
  (value.saves === null || value.goals_against === null ||
    value.shots_on_goal === value.saves + value.goals_against);
const validSaveFraction = (value: typeof sourceCountShape.Type) =>
  value.save_percentage.value === null ||
  (value.saves !== null && value.shots_on_goal !== null && value.shots_on_goal > 0 &&
    close(value.save_percentage.value, value.saves / value.shots_on_goal));
const sourceCounts = sourceCountShape.check(
  Schema.makeFilter((value) => validSourceCountTotals(value) && validSaveFraction(value)),
);
const reportedSourceCounts = sourceCountShape.check(
  Schema.makeFilter((value) =>
    (validSourceCountTotals(value) ||
      (value.support.unquantified_gap && value.support.reason_counts.some(row => row.code === "source_unavailable"))) &&
    validSaveFraction(value)),
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
  const countFields = ["unblocked_attempts", "misses", "shots_on_goal", "saves", "goals_against"] as const;
  const missingCollection = value.actual_states.length === 0 &&
    countFields.every(field => value.source_counts[field] === null) &&
    value.source_counts.support.unquantified_gap &&
    value.source_counts.support.reason_counts.some(row => row.code === "source_unavailable");
  for (const field of countFields) {
    const total = value.source_counts[field];
    const expected = missingCollection || value.actual_states.some(row => row.source_counts[field] === null)
      ? null
      : value.actual_states.reduce((sum, row) => sum + row.source_counts[field]!, 0);
    if (expected === null ? total !== null : total === null || !close(total, expected))
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
  reported_boxscore_counts: reportedSourceCounts,
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
const ledgerFields = {
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
};
export const LedgerTerm = Schema.Literals(Object.keys(ledgerFields.components.fields) as (keyof typeof ledgerFields.components.fields)[]);
const ledgerEstimate = Estimate.check(Schema.makeFilter((value) => value.uncertainty.kind === "not_estimated"));
export const ledgerClose = (value: number, terms: readonly number[]) => {
  const expected = stableSum(terms);
  return Number.isFinite(value) && Number.isFinite(expected) &&
    Math.abs(value - expected) <= 1e-9 + 1e-9 * Math.max(Math.abs(value), Math.abs(expected)) +
      64 * 2 ** -52 * stableSum(terms.map(Math.abs));
};
const ledgerTotal = (value: Estimate, terms: readonly Estimate[]) => {
  const missing = terms.find((term) => term.value === null);
  if (missing)
    return value.value === null && value.unavailable_reason === missing.unavailable_reason &&
      JSON.stringify(value.reason_detail) === JSON.stringify(missing.reason_detail);
  return value.value !== null && ledgerClose(value.value, terms.map((term) => term.value!));
};
const validLedgerTotals = (value: Pick<ValueLedgerSummary, "components" | "league_total" | "replacement_total" | "penalties_combined">) =>
  (["league", "replacement"] as const).every((reference) => {
    const term = `${reference}_goals` as const;
    return ledgerTotal(value[`${reference}_total`], LedgerTerm.literals.map((key) => value.components[key][term])) &&
      ledgerTotal(value.penalties_combined[term], [
        value.components.penalties_drawn[term], value.components.penalties_taken[term],
      ]);
  });
const depthGroup = Schema.Literals(["F", "D"]);
const depthPosition = Schema.Literals(["F", "D", "unknown"]);
const inputRef = Schema.Struct({
  strength: Schema.NullOr(SpatialStrength),
  availability: Schema.Literals(["provided", "not_computed"]),
  explanation: Schema.NullOr(Text),
  method_id: Schema.NullOr(Text),
  reference_id: Schema.NullOr(Text),
  support_policy_id: Schema.NullOr(Text),
}).check(Schema.makeFilter((value) =>
  value.availability === "provided"
    ? value.explanation === null && value.method_id !== null && value.reference_id !== null && value.support_policy_id !== null
    : value.explanation !== null && value.method_id === null && value.reference_id === null && value.support_policy_id === null));
const executionState = Schema.Struct({
  strength: ExecutionStrength,
  use: Schema.Literals(["active", "omitted_zero_weight"]),
  shooter_probability: ledgerEstimate,
  setter_share: ledgerEstimate,
  finishing_per100: ledgerEstimate,
  setting_per100: ledgerEstimate,
  finishing_goals: ledgerEstimate,
  setting_goals: ledgerEstimate,
});
const ledgerEvidence = Schema.Struct({
  annual_reference_id: Digest,
  depth_position: Schema.Struct({
    group: depthPosition, mixed: Schema.Boolean, forward_seconds: Count,
    defense_seconds: Count, unknown_seconds: Count, missing_time_records: Count,
  }),
  unit_position: depthPosition,
  inputs: Schema.Struct({
    spatial: Schema.Array(inputRef),
    execution: Schema.Array(inputRef),
    shootiness: Schema.Array(inputRef),
    penalties: inputRef,
    territory: inputRef,
  }),
  execution_states: Schema.Array(executionState),
  dependency_support: Schema.Struct({
    spatial: Schema.Array(Schema.Struct({
      strength: SpatialStrength, support: Schema.NullOr(Support),
      roles: Schema.NullOr(Schema.Array(Schema.Struct({
        role: Schema.Literals(["offense", "defense"]),
        coefficient_support: Schema.Struct({volume: spatialHeadSupport, shape: spatialHeadSupport, quality: spatialHeadSupport}),
      }))),
    })),
    execution: Schema.Array(Schema.Struct({
      strength: ExecutionStrength, finishing: Schema.NullOr(Support), setting: Schema.NullOr(Support),
      coefficient_support: Schema.NullOr(ExecutionCoefficientSupport), panel_id: Schema.NullOr(Text),
    })),
    shootiness: Schema.Array(Schema.Struct({
      strength: ExecutionStrength, support: Schema.NullOr(Support),
      coefficient_support: Schema.NullOr(mechanismCoefficientSupport),
    })),
    penalties: Schema.NullOr(Schema.Struct({ support: Support, coefficient_support: mechanismCoefficientSupport })),
    territory: Schema.NullOr(Schema.Struct({ support: Support, roles: TerritoryEvidence.fields.roles })),
  }),
});
const validLedgerEstimates = (value: { readonly components: typeof ledgerFields.components.Type;
  readonly league_total: Estimate; readonly replacement_total: Estimate; readonly penalties_combined: typeof component.Type;
}) => [value.league_total, value.replacement_total, ...Object.values(value.components).flatMap(Object.values),
  ...Object.values(value.penalties_combined)].every((estimate) => estimate.uncertainty.kind === "not_estimated");

export const ValueLedgerSummary = Schema.Struct({
  ...ledgerFields,
  annual_reference_id: Digest,
  depth_position_group: depthPosition,
  depth_reference_coverage: Schema.NullOr(Schema.Struct({
    available: Schema.Boolean, complete_groups: Count, excluded_groups: Count, member_count: Count, total_seconds: Count,
  })),
});
export const ValueLedger = Schema.Struct({ ...ledgerFields, evidence: ledgerEvidence });
export type ValueLedger = typeof ValueLedger.Type;
export type ValueLedgerSummary = typeof ValueLedgerSummary.Type;
const depthReference = Schema.Struct({
  available: Schema.Boolean,
  reason: Schema.NullOr(Text),
  members: Schema.Array(Schema.Struct({
    player_id: Id, seconds: Count, teams: Schema.Array(Schema.Struct({ team_id: Id, seconds: Count })),
  })),
  total_seconds: Count, member_count: Count,
  components: Schema.NullOr(Schema.Record(LedgerTerm, Schema.Finite)),
  missing_vectors: Schema.Array(Schema.Struct({ player_id: Id, terms: Schema.Array(LedgerTerm) })),
});
export const LedgerReference = Schema.Struct({
  season: Season, method_id: Text, reference_id: Digest,
  inputs: Schema.Struct({prepared: Receipt, source_results: Receipt, usage_reduction: Receipt,
    shorthanded_reduction: Receipt, shootiness_state: Receipt}),
  state_references: Schema.Array(Schema.Struct({
    strength: ExecutionStrength, hours: Rate, mixture_weight: Rate, attempts_per_hour: ledgerEstimate,
    attempt_reference: Schema.Union([
      Schema.Struct({ kind: Schema.Literal("spatial"), strength: ExecutionStrength,
        method_id: Schema.NullOr(Text), quantity: Schema.Literal("offense_attempts_per60_neutral") }),
      Schema.Struct({ kind: Schema.Literal("source_pool"), strength: ExecutionStrength, reduction: Receipt,
        attempts: Count, included_seconds: Rate, neutral_goal_mass: Rate, known_excluded_seconds: Rate,
        unquantified_gap: Schema.Boolean }),
    ]),
    unit: Schema.Struct({ forwards: Count, defenders: Count }),
    neutral_slot_logits: Schema.NullOr(Schema.Struct({ F: Schema.Finite, D: Schema.Finite })),
    setting_K: Schema.Struct({ F: ledgerEstimate, D: ledgerEstimate }),
    shootiness_reference_id: Schema.NullOr(Digest),
    execution_panel: Schema.NullOr(Schema.Struct({ panel_id: Text, opportunities: Count, setup_weight: Rate })),
  })),
  groups: Schema.Array(Schema.Struct({
    team_id: Id, position: depthGroup, status: Schema.Literals(["complete", "excluded"]),
    reasons: Schema.Array(Schema.Literals(["schedule_unavailable", "team_boxscore_unavailable",
      "player_enumeration_unresolved", "identity_conflict", "missing_toi", "position_conflict",
      "position_unavailable", "annual_position_tie", "annual_position_incomplete"])),
    inventory_games: Count, supported_games: Count, known_seconds: Count, missing_time_records: Count,
    unquantified_gap: Schema.Boolean, affected_games: Schema.Array(Id), affected_players: Schema.Array(Id),
    cutoff_seconds: Schema.NullOr(Count),
    members: Schema.Array(Schema.Struct({ player_id: Id, known_team_seconds: Count, complete: Schema.Boolean,
      rank: Schema.NullOr(Count), depth: Schema.NullOr(Schema.Boolean) })),
  })),
  positions: Schema.Struct({ F: depthReference, D: depthReference }),
});
export type LedgerReference = typeof LedgerReference.Type;
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
        mapMassCloses(
          value.cells,
          value.display_cells,
          value.integrated_value,
          value.unit === "goals_per_basket",
        ),
  ),
);
export const GoalieExecutionBreakdown = Schema.Struct({
  events: Count,
  eligible_weight: Rate,
  observed_successes: Count,
  expected_successes: Rate,
  probability: ProbabilityEstimate,
  effect: Estimate,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter(
    (value) =>
      value.eligible_weight === value.events &&
      value.observed_successes <= value.eligible_weight &&
      value.expected_successes <= value.eligible_weight &&
      value.support.events === value.events &&
      value.support.eligible_weight === value.events &&
      value.support.included_seconds === null &&
      (value.events === 0
        ? value.probability.value === null && value.effect.value === null
        : value.probability.value !== null &&
          value.effect.value !== null &&
          close(value.probability.value, value.expected_successes / value.events) &&
          close(value.effect.value, (value.expected_successes - value.observed_successes) / value.events)),
  ),
);
const skaterExpectation = Schema.Struct({
  expected_goals: Rate,
  mean_opportunity: ProbabilityEstimate,
  observed_minus_expected_goals: Estimate,
});
export const SkaterExecutionBreakdown = Schema.Struct({
  events: Count,
  observed_goals: Count,
  reference: skaterExpectation,
  actor: skaterExpectation,
  support: Support,
  method_id: Text,
}).check(
  Schema.makeFilter(
    (value) =>
      value.observed_goals <= value.events &&
      value.support.included_seconds === null &&
      [value.reference, value.actor].every(
        (expectation) =>
          expectation.expected_goals <= value.events &&
          (value.events === 0
            ? expectation.mean_opportunity.value === null &&
              (expectation.mean_opportunity.unavailable_reason === "no_exposure" ||
                (expectation.mean_opportunity.unavailable_reason === "missing_source" &&
                  value.support.unquantified_gap &&
                  value.support.reason_counts.some((reason) => reason.code === "source_unavailable")))
            : expectation.mean_opportunity.value !== null &&
              close(
                expectation.mean_opportunity.value,
                expectation.expected_goals / value.events,
              )) &&
          expectation.observed_minus_expected_goals.value !== null &&
          close(
            expectation.observed_minus_expected_goals.value,
            value.observed_goals - expectation.expected_goals,
          ),
      ),
  ),
);
export const ExecutionBreakdown = Schema.Union([
  SkaterExecutionBreakdown,
  GoalieExecutionBreakdown,
]);
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
    const estimates = [
      value.baseline,
      value.self,
      value.teammates,
      value.opponents,
      value.coaching_other_context,
      value.numerical_residual,
      value.factual_prediction,
    ];
    const missing = estimates.filter((estimate) => estimate.value === null);
    if (missing.length > 0)
      return missing.every((estimate) => estimate.unavailable_reason === missing[0].unavailable_reason);
    const terms = estimates.slice(0, 5).map((estimate) => estimate.value!);
    const factual = value.factual_prediction.value!, residual = value.numerical_residual.value!;
    const tolerance = 1e-10 * (1 + Math.abs(factual) + terms.reduce((sum, term) => sum + Math.abs(term), 0));
    const unadjusted = terms.reduce((sum, term) => sum + term, 0);
    return Number.isFinite(tolerance) && Number.isFinite(unadjusted) &&
      Math.abs(unadjusted + residual - factual) <= tolerance &&
      Math.abs(residual - (factual - unadjusted)) <= tolerance && Math.abs(residual) <= tolerance;
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
export const ReportedUsageResult = result(ReportedUsage);
export const SkaterDescriptiveResult = result(SkaterDescriptive);
export const SkaterContextResult = result(SkaterContext);
export const SkaterMicrostatsResult = result(SkaterMicrostats);
export const SkaterSpatialResult = result(SkaterSpatial);
export const SpatialEvidenceResult = result(SpatialEvidence);
export const SkaterExecutionResult = result(SkaterExecution);
export const SkaterShootinessResult = result(SkaterShootiness);
export const SkaterPenaltiesResult = result(SkaterPenalties);
export const SkaterTerritoryResult = result(SkaterTerritory);
export const GoalieResultEnvelope = result(GoalieResult);
export const GoalieObservedResult = result(GoalieObserved);
export const GoalieObservedSummaryResult = result(GoalieObservedSummary);
export const ValueLedgerResult = result(ValueLedger.check(Schema.makeFilter(
  (value) => validLedgerEstimates(value) && validLedgerTotals(value),
)));
export const ValueLedgerSummaryResult = result(ValueLedgerSummary.check(Schema.makeFilter(
  (value) => validLedgerEstimates(value) && validLedgerTotals(value) &&
    (value.depth_position_group === "unknown") === (value.depth_reference_coverage === null),
)));
export const LedgerReferenceResult = result(LedgerReference);
export const LedgerEvidenceData = Schema.Struct({ ledger: ValueLedgerResult, reference: LedgerReferenceResult });
export const AnalysisMapResult = result(AnalysisMap);
export const SkaterExecutionBreakdownResult = result(SkaterExecutionBreakdown);
export const GoalieExecutionBreakdownResult = result(GoalieExecutionBreakdown);
export const ExecutionBreakdownResult = result(ExecutionBreakdown);
export const AdjustmentDecompositionResult = result(AdjustmentDecomposition);
export const GoalieEvidenceMapResult = result(GoalieEvidenceMap);
export const GoalieDangerResult = result(GoalieDanger);
export const SpatialAdjustment = Schema.Struct({target: AdjustmentTarget, result: AdjustmentDecompositionResult});
export const SpatialEvidenceData = Schema.Struct({
  summary: SkaterSpatialResult,
  evidence: SpatialEvidenceResult,
  adjustments: Schema.Array(SpatialAdjustment),
});
export const validateSpatialEvidenceSelection = (value: {
  readonly season: string;
  readonly strength: string;
  readonly summary: typeof SkaterSpatialResult.Type;
  readonly evidence: typeof SpatialEvidenceResult.Type;
  readonly adjustments: readonly (typeof SpatialAdjustment.Type)[];
  readonly methods: Readonly<Record<string, Method>>;
}): boolean => {
  const offense = ["5v4", "5v3", "4v3", "pp"].includes(value.strength);
  const roles = value.strength === "5v5" ? ["offense", "defense"] : [offense ? "offense" : "defense"];
  const selectedStates = value.strength === "pp" || value.strength === "pk"
    ? ["5v4", "5v3", "4v3"]
    : [{"4v5":"5v4", "3v5":"5v3", "3v4":"4v3"}[value.strength] ?? value.strength];
  const targets = AdjustmentTarget.literals.filter((target) => value.strength === "5v5" ||
    (offense ? target.startsWith("for_") : target.startsWith("against_")));
  if (!SpatialStrength.literals.includes(value.strength as typeof SpatialStrength.Type) ||
      JSON.stringify(value.adjustments.map((row) => row.target)) !== JSON.stringify(targets) ||
      value.summary.availability !== value.evidence.availability)
    return false;
  if (value.evidence.availability !== "provided")
    return value.adjustments.every((row) => row.result.availability === "not_computed");
  if (value.summary.availability !== "provided") return false;
  const evidence = value.evidence.data, summary = value.summary.data;
  const method = value.methods[evidence.method_id];
  const summaryStates = value.strength === "pp" ? ["5v4", "5v3", "4v3"]
    : value.strength === "pk" ? ["4v5", "3v5", "3v4"] : [value.strength];
  if (summary.method_id !== evidence.method_id || method === undefined || method.family !== "spatial" ||
      !method.fit_seasons.includes(value.season as Season) ||
      !method.evidence.some((receipt) => receipt.uri === evidence.annual_state.uri && receipt.sha256 === evidence.annual_state.sha256) ||
      !method.inputs.some((input) => input.role === "annual_state" && input.sha256 === evidence.annual_state.sha256 &&
        input.seasons.length === 1 && input.seasons[0] === value.season) ||
      evidence.fit_family !== (value.strength === "5v5" ? "ev" : "st") ||
      JSON.stringify(summary.state_weights.map((row) => row.strength).sort()) !== JSON.stringify(summaryStates.sort()) ||
      JSON.stringify(evidence.state_support.map((row) => row.state)) !== JSON.stringify(selectedStates) ||
      JSON.stringify(evidence.roles.map((row) => row.role)) !== JSON.stringify(roles))
    return false;
  for (const role of evidence.roles) {
    const heads = Object.values(role.coefficient_support);
    const numericRole = (["attempts", "xg"] as const).some((quantity) =>
      (["per60", "per60_complete", "relative_percent"] as const)
        .some((suffix) => summary[`${role.role}_${quantity}_${suffix}`].value !== null));
    if (numericRole && heads.some((head) => !head.available)) return false;
    for (const head of heads)
      if (head.prior_seasons.some((year) => year >= value.season || !method.fit_seasons.includes(year) ||
          !method.inputs.some((input) => input.role === "annual_state" && input.seasons.includes(year))))
        return false;
    const context = role.actual_context;
    if (context.included_seconds !== null && summary.support.included_seconds !== null &&
        !close(context.included_seconds, summary.support.included_seconds))
      return false;
    for (const row of value.adjustments.filter((row) => role.role === "offense" ? row.target.startsWith("for_") : row.target.startsWith("against_"))) {
      if (row.result.availability !== "provided" || row.result.data.method_id !== evidence.method_id)
        return false;
      const adjustment = row.result.data;
      const estimates = [adjustment.baseline, adjustment.self, adjustment.teammates, adjustment.opponents,
        adjustment.coaching_other_context, adjustment.numerical_residual, adjustment.factual_prediction];
      const reasons = context.reason === "no_exposure" ? ["no_exposure"]
        : context.reason === "incomplete_annual_family" ? ["failed_fit"]
        : context.reason === "not_evaluated" ? ["missing_source", "not_computed"] : ["missing_source"];
      if (context.available ? estimates.some((estimate) => estimate.value === null)
        : estimates.some((estimate) => estimate.value !== null || !reasons.includes(estimate.unavailable_reason!)))
        return false;
    }
  }
  return true;
};
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
    (value) => (value.group === "coach") === (value.recipient_id === "coaching_context") &&
      (value.group === "setter" || !["none", "unknown"].includes(value.recipient_id)),
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
  Schema.Array(Schema.Struct({ strength: SpatialStrength, result: SkaterSpatialResult })).check(
    Schema.makeFilter(rows => rows.length === SpatialStrength.literals.length && unique(rows.map(row => row.strength))),
  ),
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
  ledger: ValueLedgerSummaryResult,
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
// the overview carries the same estimates and support as full results, with
// evidence-bearing bodies available through their named family endpoints.
export const ExecutionSummary = Schema.Struct({
  ...executionFields,
  support: SkaterExecution.fields.support,
  method_id: SkaterExecution.fields.method_id,
});
export const ShootinessSummary = SkaterShootiness.mapFields(Struct.pick([
  "probability", "neutral_probability", "difference", "support", "method_id",
]));
export const PenaltySummary = SkaterPenalties.mapFields(Struct.pick([
  "drawn_per60", "taken_per60", "drawn_value_per60", "taken_value_per60", "support", "method_id",
]));
export const TerritorySummary = SkaterTerritory.mapFields(Struct.pick([
  "ice_won_goals_per_basket", "ice_lost_goals_per_basket", "exit_offense", "entry_offense",
  "zone_retention", "entry_prevention", "support", "method_id",
]));
export const GoalieSummary = Schema.Struct({
  ...goalieFields,
  support: GoalieResult.fields.support,
  method_id: GoalieResult.fields.method_id,
});
export const ExecutionSummaryResult = result(ExecutionSummary);
export const ShootinessSummaryResult = result(ShootinessSummary);
export const PenaltySummaryResult = result(PenaltySummary);
export const TerritorySummaryResult = result(TerritorySummary);
export const GoalieSummaryResult = result(GoalieSummary);

// project already decoded full results. the summary decoder selects only the
// declared fields and retains the original availability envelope.
export const projectOverviewResult = <S extends Schema.ConstraintDecoder<unknown, never>>(
  schema: S, full: unknown,
): S["Type"] => Schema.decodeUnknownSync(schema)(full);

const skaterOverview = Schema.Struct({
  reported_usage: ReportedUsageResult,
  ledger: ValueLedgerSummaryResult,
  spatial: Schema.Struct({
    five_on_five: SkaterSpatialResult,
    pp: SkaterSpatialResult,
    pk: SkaterSpatialResult,
  }),
  execution: ExecutionSummaryResult,
  shootiness: ShootinessSummaryResult,
  penalties: PenaltySummaryResult,
  territory: TerritorySummaryResult,
  observed: ObservedResult,
  context: SkaterContextResult,
});
const goalieOverview = Schema.Struct({
  reported_usage: ReportedUsageResult,
  goalie: Schema.Struct({ ev: GoalieSummaryResult, pk: GoalieSummaryResult }),
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
          preservesObservedAffiliations(row.person.teams, data.teams)
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
    "spatial",
    "goalie",
    "goalie_evidence",
    "penalties",
    "territory",
    "microstats",
    "ledger",
  ]),
  strength: Schema.NullOr(Schema.Union([EvidenceStrength, SpatialStrength])),
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
const breakdownRow = <S extends Schema.Top>(schema: S) => Schema.Struct({
  strength: Schema.Union([ExecutionStrength, GoalieStrength]),
  kind: Schema.Literals(["shot_type", "danger"]),
  stratum: Schema.Union([ShotType, Schema.Literals(["<.05", "[.05,.15)", ">=.15"])]),
  result: schema,
});
export const EvidenceResponse = Schema.Union([
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("ledger"),
    selection: EvidenceSelection,
    result: ApiResult(LedgerEvidenceData),
  }),
  Schema.Struct({
    ...Envelope.fields,
    family: Schema.Literal("spatial"),
    selection: EvidenceSelection,
    result: ApiResult(SpatialEvidenceData),
  }),
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
        breakdowns: Schema.Array(breakdownRow(SkaterExecutionBreakdownResult)),
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
      Schema.Struct({ summary: GoalieResultEnvelope, breakdowns: Schema.Array(breakdownRow(GoalieExecutionBreakdownResult)) }),
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
      response.selection.season === response.season.season &&
      (response.family !== "spatial" || response.result.availability !== "provided" ||
        validateSpatialEvidenceSelection({...response.result.data, season: response.season.season,
          strength: response.selection.strength!, methods: response.methods})),
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
