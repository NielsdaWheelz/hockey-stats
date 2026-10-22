import * as Schema from "effect/Schema";
import * as HttpApiSchema from "effect/http-api/HttpApiSchema";

import { HockeyId, GameId, Season, Count, Rate, DateString, Timestamp, GitCommit, Publication } from "./publication.js";
export { HockeyId, GameId, Season, Count, Rate, DateString, Timestamp, GitCommit, Publication } from "./publication.js";
const inheritedReasonCodes = [
  "required_source_unavailable", "count_accounting_conflict", "event_evidence_unresolved",
  "unpaired_report_attempt", "elapsed_membership_unresolved", "period_horizon_unavailable",
  "player_toi_conflict", "roster_identity_unresolved", "unassigned_player_games",
  "event_exposure_conflict", "shift_source_empty",
] as const;
export const ReasonCode = Schema.Literals([...inheritedReasonCodes, "no_5v5_exposure"]);
export type ReasonCode = typeof ReasonCode.Type;
export const ReasonCodes = Schema.Array(ReasonCode).check(Schema.makeFilter((codes) => codes.every((code, index) => index === 0 || codes[index - 1] < code)));
export const CoverageStatus = Schema.Literals(["complete", "partial", "unavailable"]);
export const Team = Schema.Struct({ id: HockeyId, abbreviation: Schema.NullOr(Schema.String) });
export type Team = typeof Team.Type;

export const Metrics = Schema.Struct({
  included_seconds: Count,
  known_excluded_seconds: Count,
  attempts_for: Schema.NullOr(Count),
  attempts_against: Schema.NullOr(Count),
  for_per60: Schema.NullOr(Rate),
  against_per60: Schema.NullOr(Rate),
  coverage_status: CoverageStatus,
  reason_codes: ReasonCodes,
}).check(Schema.makeFilter((metrics) => {
  if (metrics.coverage_status === "complete" && metrics.known_excluded_seconds !== 0) return false;
  if (metrics.included_seconds > 0) return metrics.attempts_for !== null && metrics.attempts_against !== null && metrics.for_per60 !== null && metrics.against_per60 !== null && (metrics.coverage_status === "complete" ? metrics.reason_codes.length === 0 : metrics.coverage_status === "partial" && metrics.reason_codes.length > 0 && !metrics.reason_codes.includes("no_5v5_exposure"));
  if (metrics.coverage_status === "complete") return metrics.attempts_for === 0 && metrics.attempts_against === 0 && metrics.for_per60 === null && metrics.against_per60 === null && metrics.reason_codes.length === 1 && metrics.reason_codes[0] === "no_5v5_exposure";
  return metrics.coverage_status === "unavailable" && metrics.attempts_for === null && metrics.attempts_against === null && metrics.for_per60 === null && metrics.against_per60 === null && metrics.reason_codes.length > 0 && !metrics.reason_codes.includes("no_5v5_exposure");
}));
export type Metrics = typeof Metrics.Type;

export const PersonalReasonCode = Schema.Literals([
  ...inheritedReasonCodes,
  "personal_credit_unresolved", "no_personal_5v5_exposure",
]);
export type PersonalReasonCode = typeof PersonalReasonCode.Type;
export const PersonalReasonCodes = Schema.Array(PersonalReasonCode).check(Schema.makeFilter((codes) => codes.every((code, index) => index === 0 || codes[index - 1] < code)));
export const PersonalMetrics = Schema.Struct({
  included_seconds: Count,
  known_excluded_seconds: Count,
  shots_on_goal: Schema.NullOr(Count),
  goals: Schema.NullOr(Count),
  primary_assists: Schema.NullOr(Count),
  shots_on_goal_per60: Schema.NullOr(Rate),
  goals_per60: Schema.NullOr(Rate),
  primary_assists_per60: Schema.NullOr(Rate),
  coverage_status: CoverageStatus,
  reason_codes: PersonalReasonCodes,
}).check(Schema.makeFilter((metrics) => {
  const counts = [metrics.shots_on_goal, metrics.goals, metrics.primary_assists];
  const rates = [metrics.shots_on_goal_per60, metrics.goals_per60, metrics.primary_assists_per60];
  const noExposure = metrics.reason_codes.includes("no_personal_5v5_exposure");
  const gaps = metrics.reason_codes.some((code) => code !== "no_personal_5v5_exposure");
  if (metrics.coverage_status === "complete" && metrics.known_excluded_seconds !== 0) return false;
  if (metrics.goals !== null && metrics.shots_on_goal !== null && metrics.goals > metrics.shots_on_goal) return false;
  if (metrics.included_seconds > 0) return counts.every((value) => value !== null) && rates.every((value) => value !== null) && !noExposure && metrics.coverage_status === (gaps ? "partial" : "complete");
  if (counts.every((value) => value === null)) return rates.every((value) => value === null) && metrics.coverage_status === "unavailable" && gaps && noExposure;
  return metrics.shots_on_goal === 0 && metrics.goals === 0 && metrics.primary_assists !== null && (metrics.primary_assists > 0 || !gaps) && rates.every((value) => value === null) && noExposure && metrics.coverage_status === (gaps ? "partial" : "complete");
}));
export type PersonalMetrics = typeof PersonalMetrics.Type;

export const SpatialReasonCode = Schema.Literals([
  ...inheritedReasonCodes,
  "spatial_coordinates_missing", "spatial_frame_unresolved", "spatial_location_outside_rink", "no_spatial_5v5_exposure",
]);
export type SpatialReasonCode = typeof SpatialReasonCode.Type;
export const SpatialReasonCodes = Schema.Array(SpatialReasonCode).check(Schema.makeFilter((codes) => codes.every((code, index) => index === 0 || codes[index - 1] < code)));
const spatialSupport = (value: { included_seconds: number; known_excluded_seconds: number; coverage_status: typeof CoverageStatus.Type; reason_codes: readonly SpatialReasonCode[] }, counts: readonly (number | null)[], rates: readonly (number | null)[]) => {
  if (value.coverage_status === "complete" && value.known_excluded_seconds !== 0) return false;
  const noExposure = value.reason_codes.includes("no_spatial_5v5_exposure");
  if (value.included_seconds > 0) return counts.every((v) => v !== null) && rates.every((v) => v !== null) && !noExposure && value.coverage_status === (value.reason_codes.length ? "partial" : "complete");
  if (value.coverage_status === "complete") return counts.every((v) => v === 0) && rates.every((v) => v === null) && value.reason_codes.length === 1 && noExposure;
  return value.coverage_status === "unavailable" && counts.every((v) => v === null) && rates.every((v) => v === null) && value.reason_codes.length > 0 && !noExposure;
};
export const SpatialMetrics = Schema.Struct({
  included_seconds: Count, known_excluded_seconds: Count,
  unblocked_for: Schema.NullOr(Count), unblocked_against: Schema.NullOr(Count),
  for_per60: Schema.NullOr(Rate), against_per60: Schema.NullOr(Rate),
  coverage_status: CoverageStatus, reason_codes: SpatialReasonCodes,
}).check(Schema.makeFilter((value) => spatialSupport(value, [value.unblocked_for, value.unblocked_against], [value.for_per60, value.against_per60])));
export type SpatialMetrics = typeof SpatialMetrics.Type;
export const SpatialCoverage = Schema.Struct({
  included_seconds: Count, known_excluded_seconds: Count,
  unblocked_attempts: Schema.NullOr(Count), unblocked_per60: Schema.NullOr(Rate),
  coverage_status: CoverageStatus, reason_codes: SpatialReasonCodes,
  inventory_games: Count, games_with_included_time: Count, partial_games: Count, unavailable_games: Count,
  reason_game_counts: Schema.Array(Schema.Struct({ code: SpatialReasonCode, games: Count })),
}).check(Schema.makeFilter((value) => spatialSupport(value, [value.unblocked_attempts], [value.unblocked_per60]) &&
  value.partial_games <= value.games_with_included_time && value.games_with_included_time + value.unavailable_games <= value.inventory_games &&
  value.reason_game_counts.every((reason, index) => reason.games > 0 && reason.games <= value.inventory_games && (index === 0 || value.reason_game_counts[index - 1].code < reason.code))));
export type SpatialCoverage = typeof SpatialCoverage.Type;
export const SpatialCell = Schema.Struct({
  cell_id: Count, x_min: Schema.Finite, x_max: Schema.Finite, y_min: Schema.Finite, y_max: Schema.Finite,
  center_x: Schema.Finite, center_y: Schema.Finite, area_sqft: Rate.check(Schema.isGreaterThan(0)),
  league_count: Schema.NullOr(Count), league_raw_per60: Schema.NullOr(Rate), league_density: Schema.NullOr(Rate),
});
export type SpatialCell = typeof SpatialCell.Type;
export const PlayerSpatialCell = Schema.Struct({
  cell_id: Count, for_count: Count, against_count: Count,
  for_raw_per60: Rate, against_raw_per60: Rate, for_density: Rate, against_density: Rate,
  for_difference: Schema.Finite, against_difference: Schema.Finite,
});
export type PlayerSpatialCell = typeof PlayerSpatialCell.Type;
export const SpatialSelection = Schema.Struct({
  definition: Schema.Struct({
    population_version: Schema.Literal("matched_unblocked_locations_v2"), display_version: Schema.Literal("rect5_gaussian10_v1"), sigma_ft: Schema.Literal(10),
    rink: Schema.Struct({length_ft: Schema.Literal(200), width_ft: Schema.Literal(85), corner_radius_ft: Schema.Literal(28), goal_x: Schema.Literal(89)}),
    units: Schema.Literal("attempts_per60_per100sqft"), orientation: Schema.Literal("shooting_team_positive_x"),
  }),
  league_support: SpatialCoverage, cells: Schema.Array(SpatialCell).check(Schema.makeFilter((cells) => cells.length === 668 && cells.every((cell, index) => index === 0 || cells[index - 1].cell_id < cell.cell_id))),
  players: Schema.Array(Schema.Struct({player_id: HockeyId, data: Schema.NullOr(Schema.Struct({metrics: SpatialMetrics, cells: Schema.NullOr(Schema.Array(PlayerSpatialCell))}))})),
}).check(Schema.makeFilter((selection) => selection.players.length > 0 && selection.players.length <= 2 &&
  new Set(selection.players.map((player) => player.player_id)).size === selection.players.length &&
  selection.cells.every((cell) => selection.league_support.included_seconds > 0
    ? cell.league_count !== null && cell.league_raw_per60 !== null && cell.league_density !== null
    : cell.league_count === (selection.league_support.coverage_status === "complete" ? 0 : null) && cell.league_raw_per60 === null && cell.league_density === null) &&
  selection.players.every(({data}) => data === null || (data.metrics.included_seconds === 0 ? data.cells === null :
    selection.league_support.included_seconds > 0 && data.cells !== null && data.cells.length === selection.cells.length && data.cells.every((cell,index) => cell.cell_id === selection.cells[index].cell_id)))));
export type SpatialSelection = typeof SpatialSelection.Type;

const matchedPersonalSupport = ({ metrics, personal }: { metrics: Metrics; personal: PersonalMetrics }) =>
  personal.included_seconds <= metrics.included_seconds &&
  personal.known_excluded_seconds - metrics.known_excluded_seconds === metrics.included_seconds - personal.included_seconds &&
  metrics.reason_codes.every((code) => code === "no_5v5_exposure" || personal.reason_codes.includes(code));


export const Coverage = Schema.Struct({
  inventory_games: Count,
  games_with_included_time: Count,
  partial_games: Count,
  unavailable_games: Count,
  games_with_unassigned_player_associations: Count,
  reason_game_counts: Schema.Array(Schema.Struct({ code: ReasonCode, games: Count })),
  unassigned_games: Schema.Array(Schema.Struct({
    game_id: GameId, date: DateString, away_team_id: HockeyId, home_team_id: HockeyId, reason_codes: ReasonCodes,
  })),
}).check(Schema.makeFilter((coverage) =>
  coverage.partial_games <= coverage.games_with_included_time && coverage.games_with_included_time + coverage.unavailable_games <= coverage.inventory_games &&
  coverage.games_with_unassigned_player_associations === coverage.unassigned_games.length && coverage.games_with_unassigned_player_associations <= coverage.inventory_games &&
  coverage.reason_game_counts.every((reason, index) => reason.games > 0 && reason.games <= coverage.inventory_games && (index === 0 || coverage.reason_game_counts[index - 1].code < reason.code)) &&
  new Set(coverage.unassigned_games.map((game) => game.game_id)).size === coverage.unassigned_games.length,
));
export type Coverage = typeof Coverage.Type;

export const PlayerSummary = Schema.Struct({
  player_id: HockeyId,
  display_name: Schema.NullOr(Schema.String),
  reported_position: Schema.Literals(["C", "L", "R", "D", "F"]),
  teams: Schema.Array(Team).check(Schema.makeFilter((teams) => teams.length > 0 && new Set(teams.map((team) => team.id)).size === teams.length)),
  listed_games: Count.check(Schema.isGreaterThan(0)),
  games_with_included_time: Count,
  partial_games: Count,
  unavailable_games: Count,
  metrics: Metrics,
  personal: PersonalMetrics,
}).check(Schema.makeFilter((player) => player.partial_games <= player.games_with_included_time && player.games_with_included_time + player.unavailable_games <= player.listed_games && matchedPersonalSupport(player)));
export type PlayerSummary = typeof PlayerSummary.Type;

export const PlayerGame = Schema.Struct({
  game_id: GameId,
  game_date: DateString,
  team: Team,
  opponent: Team,
  venue: Schema.Literals(["home", "away"]),
  metrics: Metrics,
  personal: PersonalMetrics,
  spatial: SpatialMetrics,
}).check(Schema.makeFilter((game) => matchedPersonalSupport(game) &&
  game.spatial.included_seconds <= game.metrics.included_seconds &&
  game.spatial.known_excluded_seconds === game.metrics.known_excluded_seconds + game.metrics.included_seconds - game.spatial.included_seconds &&
  game.metrics.reason_codes.every((code) => code === "no_5v5_exposure" || game.spatial.reason_codes.includes(code))));
export type PlayerGame = typeof PlayerGame.Type;

export const AvailableSeasons = Schema.Array(Season).check(Schema.makeFilter((seasons) => seasons.length > 0 && seasons.every((season, index) => index === 0 || seasons[index - 1] > season)));
export const SeasonEvidence = Schema.Struct({
  season: Season,
  corpus_sha256: Schema.String.check(Schema.isPattern(/^[a-f0-9]{64}$/)),
  source_requested_min: Schema.NullOr(Timestamp), source_requested_max: Schema.NullOr(Timestamp), undated_sources: Count,
  coverage: Coverage, spatial_coverage: SpatialCoverage,
}).check(Schema.makeFilter((evidence) =>
  (evidence.source_requested_min === null) === (evidence.source_requested_max === null) &&
  (evidence.source_requested_min === null || evidence.source_requested_max === null || Date.parse(evidence.source_requested_min) <= Date.parse(evidence.source_requested_max)) &&
  evidence.coverage.unassigned_games.every((game) => game.game_id.slice(0, 4) === evidence.season.slice(0, 4) && game.game_id.slice(4, 6) === "02")));
export type SeasonEvidence = typeof SeasonEvidence.Type;

export const DeploymentPeer = Schema.Struct({ player_id: HockeyId, shared_seconds: Count.check(Schema.isGreaterThan(0)) });
export type DeploymentPeer = typeof DeploymentPeer.Type;
export const Deployment = Schema.Struct({ teammates: Schema.Array(DeploymentPeer), opponents: Schema.Array(DeploymentPeer) });
export type Deployment = typeof Deployment.Type;
export const InvalidPlayerId = Schema.Struct({ _tag: Schema.Literal("InvalidPlayerId"), message: Schema.String }).pipe(HttpApiSchema.status(400));
export const PlayerNotFound = Schema.Struct({ _tag: Schema.Literal("PlayerNotFound"), message: Schema.String }).pipe(HttpApiSchema.status(404));
export const InvalidSeasonSelection = Schema.Struct({ _tag: Schema.Literal("InvalidSeasonSelection"), message: Schema.String, available_seasons: AvailableSeasons }).pipe(HttpApiSchema.status(400));
export const SeasonNotFound = Schema.Struct({ _tag: Schema.Literal("SeasonNotFound"), message: Schema.String, available_seasons: AvailableSeasons }).pipe(HttpApiSchema.status(404));
export const ReadFailure = Schema.Struct({ _tag: Schema.Literal("ReadFailure"), message: Schema.String }).pipe(HttpApiSchema.status(500));
