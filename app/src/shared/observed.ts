import * as Schema from "effect/Schema";
import * as HttpApi from "effect/http-api/HttpApi";
import * as HttpApiEndpoint from "effect/http-api/HttpApiEndpoint";
import * as HttpApiGroup from "effect/http-api/HttpApiGroup";
import * as HttpApiSchema from "effect/http-api/HttpApiSchema";

export const HockeyId = Schema.String.check(Schema.isPattern(/^[1-9]\d*$/));
export const GameId = Schema.String.check(Schema.isPattern(/^[1-9]\d{9}$/));
export const Season = Schema.String.check(Schema.isPattern(/^\d{8}$/), Schema.makeFilter((value) => Number(value.slice(4)) === Number(value.slice(0, 4)) + 1));
export const Count = Schema.Finite.check(Schema.isInt(), Schema.isGreaterThanOrEqualTo(0), Schema.isLessThanOrEqualTo(Number.MAX_SAFE_INTEGER));
export const Rate = Schema.Finite.check(Schema.isGreaterThanOrEqualTo(0));
export const DateString = Schema.String.check(Schema.isPattern(/^\d{4}-\d{2}-\d{2}$/), Schema.makeFilter((value) => !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value));
export const Timestamp = Schema.String.check(Schema.isPattern(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/), Schema.makeFilter((value) => !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 19) === value.slice(0, 19)));
export const GitCommit = Schema.NullOr(Schema.String.check(Schema.isPattern(/^[a-f0-9]{40}$/)));
export const ReasonCode = Schema.Literals([
  "required_source_unavailable", "count_accounting_conflict", "event_evidence_unresolved",
  "unpaired_report_attempt", "elapsed_membership_unresolved", "period_horizon_unavailable",
  "player_toi_conflict", "roster_identity_unresolved", "unassigned_player_games", "no_5v5_exposure",
]);
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

export const Publication = Schema.Struct({
  publication_id: Schema.String.check(Schema.isUUID()),
  kind: Schema.Literal("observed_5v5"),
  purpose: Schema.Literals(["real", "fixture"]),
  season: Season,
  generated_at: Timestamp,
  source_requested_min: Schema.NullOr(Timestamp),
  source_requested_max: Schema.NullOr(Timestamp),
  undated_sources: Count,
  population_version: Schema.Literal("matched_attempts_v1"),
  corpus_sha256: Schema.String.check(Schema.isPattern(/^[a-f0-9]{64}$/)),
  git_commit: GitCommit,
}).check(Schema.makeFilter((publication) => (publication.source_requested_min === null) === (publication.source_requested_max === null) && (publication.source_requested_min === null || publication.source_requested_max === null || Date.parse(publication.source_requested_min) <= Date.parse(publication.source_requested_max))));
export type Publication = typeof Publication.Type;

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
}).check(Schema.makeFilter((player) => player.partial_games <= player.games_with_included_time && player.games_with_included_time + player.unavailable_games <= player.listed_games));
export type PlayerSummary = typeof PlayerSummary.Type;

export const PlayerGame = Schema.Struct({
  game_id: GameId,
  game_date: DateString,
  team: Team,
  opponent: Team,
  venue: Schema.Literals(["home", "away"]),
  metrics: Metrics,
});
export type PlayerGame = typeof PlayerGame.Type;

export const LeagueResponse = Schema.Struct({ publication: Publication, coverage: Coverage, players: Schema.Array(PlayerSummary) });
export type LeagueResponse = typeof LeagueResponse.Type;
export const PlayerResponse = Schema.Struct({ publication: Publication, coverage: Coverage, player: PlayerSummary, games: Schema.Array(PlayerGame) });
export type PlayerResponse = typeof PlayerResponse.Type;

export const InvalidPlayerId = Schema.Struct({ _tag: Schema.Literal("InvalidPlayerId"), message: Schema.String }).pipe(HttpApiSchema.status(400));
export const PlayerNotFound = Schema.Struct({ _tag: Schema.Literal("PlayerNotFound"), message: Schema.String }).pipe(HttpApiSchema.status(404));
export const ReadFailure = Schema.Struct({ _tag: Schema.Literal("ReadFailure"), message: Schema.String }).pipe(HttpApiSchema.status(500));

export const ObservedApi = HttpApi.make("observed").add(HttpApiGroup.make("observed").add(
  HttpApiEndpoint.get("league", "/api/league", { success: LeagueResponse, error: ReadFailure }),
  HttpApiEndpoint.get("player", "/api/players/:playerId", {
    params: { playerId: Schema.String }, success: PlayerResponse, error: [InvalidPlayerId, PlayerNotFound, ReadFailure],
  }),
));
