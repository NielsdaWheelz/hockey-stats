import { decode, per60 } from "./analysis-publication.js";
import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Effect from "effect/Effect";
import * as Schema from "effect/Schema";
import {
  Count,
  CoverageStatus,
  DateString,
  GameId,
  HockeyId,
  Metrics,
  PersonalMetrics,
  PersonalReasonCodes,
  PlayerGame,
  PlayerSummary,
  ReasonCodes,
  Season,
  SeasonEvidence,
} from "../shared/observed.js";
import { readDeployment, validateDeployment } from "./deployment-publication.js";
import {
  spatialColumns,
  spatialGameColumns,
  spatialMetrics,
  validateSpatial,
} from "./spatial-publication.js";
import { preservesObservedAffiliations } from "../shared/player-analysis.js";
const strict = { onExcessProperty: "error" } as const;
const Locator = Schema.Struct({ game_id: GameId, source_index: Count });
const { reason_codes, ...metricValues } = Metrics.fields;
const metricColumns = { ...metricValues, reason_codes_json: Schema.fromJsonString(reason_codes) };
const personalColumns = {
  personal_included_seconds: Count,
  personal_known_excluded_seconds: Count,
  personal_shots_on_goal: Schema.NullOr(Count),
  personal_goals: Schema.NullOr(Count),
  personal_primary_assists: Schema.NullOr(Count),
  personal_shots_on_goal_per60: PersonalMetrics.fields.shots_on_goal_per60,
  personal_goals_per60: PersonalMetrics.fields.goals_per60,
  personal_primary_assists_per60: PersonalMetrics.fields.primary_assists_per60,
  personal_coverage_status: CoverageStatus,
  personal_reason_codes_json: Schema.fromJsonString(PersonalReasonCodes),
};
const PlayerRow = Schema.Struct({
  season: Season,
  player_id: HockeyId,
  display_name: Schema.NullOr(Schema.String),
  reported_position: PlayerSummary.fields.reported_position,
  name_source_json: Schema.NullOr(Schema.fromJsonString(Locator)),
  position_source_json: Schema.fromJsonString(Locator),
  teams_json: Schema.fromJsonString(PlayerSummary.fields.teams),
});
const GameRow = Schema.Struct({
  season: Season,
  game_id: GameId,
  game_date: DateString,
  away_team_id: HockeyId,
  home_team_id: HockeyId,
  away_abbreviation: Schema.NullOr(Schema.String),
  home_abbreviation: Schema.NullOr(Schema.String),
  included_seconds: Count,
  known_excluded_seconds: Count,
  personal_included_seconds: Count,
  personal_known_excluded_seconds: Count,
  known_unresolved_seconds: Count,
  horizon_unavailable: Schema.Literals([0, 1]),
  away_attempts: Schema.NullOr(Count),
  home_attempts: Schema.NullOr(Count),
  coverage_status: CoverageStatus,
  reason_codes_json: Schema.fromJsonString(ReasonCodes),
  ...spatialGameColumns,
}).check(
  Schema.makeFilter((game) => {
    if (game.game_id.slice(0, 4) !== game.season.slice(0, 4) || game.game_id.slice(4, 6) !== "02")
      return false;
    if (
      game.personal_included_seconds > game.included_seconds ||
      game.personal_known_excluded_seconds - game.known_excluded_seconds !==
        game.included_seconds - game.personal_included_seconds ||
      game.away_team_id === game.home_team_id ||
      (game.coverage_status === "complete" && game.known_excluded_seconds !== 0)
    )
      return false;
    if (game.included_seconds > 0)
      return (
        game.away_attempts !== null &&
        game.home_attempts !== null &&
        (game.coverage_status === "complete"
          ? game.reason_codes_json.length === 0
          : game.coverage_status === "partial" &&
            game.reason_codes_json.length > 0 &&
            !game.reason_codes_json.includes("no_5v5_exposure"))
      );
    if (game.coverage_status === "complete")
      return (
        game.away_attempts === 0 &&
        game.home_attempts === 0 &&
        game.reason_codes_json.length === 1 &&
        game.reason_codes_json[0] === "no_5v5_exposure"
      );
    return (
      game.coverage_status === "unavailable" &&
      game.away_attempts === null &&
      game.home_attempts === null &&
      game.reason_codes_json.length > 0 &&
      !game.reason_codes_json.includes("no_5v5_exposure")
    );
  }),
);
const PlayerGameRow = Schema.Struct({
  season: Season,
  player_id: HockeyId,
  game_id: GameId,
  team_id: HockeyId,
  ...metricColumns,
  ...personalColumns,
  ...spatialColumns,
});
const PlayerSeasonRow = Schema.Struct({
  season: Season,
  player_id: HockeyId,
  teams_json: Schema.fromJsonString(PlayerSummary.fields.teams),
  listed_games: PlayerSummary.fields.listed_games,
  games_with_included_time: Count,
  partial_games: Count,
  unavailable_games: Count,
  ...metricColumns,
  ...personalColumns,
  ...spatialColumns,
});

export const validateObserved = (
  sql: SqliteClient,
  seasons: readonly SeasonEvidence[],
  purpose: "real" | "fixture",
) =>
  Effect.gen(function* () {
    const JoinedPlayer = Schema.Struct({
      ...PlayerSeasonRow.fields,
      display_name: PlayerRow.fields.display_name,
      reported_position: PlayerRow.fields.reported_position,
    });
    const JoinedGame = Schema.Struct({
      ...PlayerGameRow.fields,
      game_date: DateString,
      away_team_id: HockeyId,
      home_team_id: HockeyId,
      away_abbreviation: Schema.NullOr(Schema.String),
      home_abbreviation: Schema.NullOr(Schema.String),
    });
    const metrics = (row: typeof PlayerGameRow.Type | typeof PlayerSeasonRow.Type): Metrics => ({
      included_seconds: row.included_seconds,
      known_excluded_seconds: row.known_excluded_seconds,
      attempts_for: row.attempts_for,
      attempts_against: row.attempts_against,
      for_per60: row.for_per60,
      against_per60: row.against_per60,
      coverage_status: row.coverage_status,
      reason_codes: row.reason_codes_json,
    });
    const personal = (
      row: typeof PlayerGameRow.Type | typeof PlayerSeasonRow.Type,
    ): PersonalMetrics => ({
      included_seconds: row.personal_included_seconds,
      known_excluded_seconds: row.personal_known_excluded_seconds,
      shots_on_goal: row.personal_shots_on_goal,
      goals: row.personal_goals,
      primary_assists: row.personal_primary_assists,
      shots_on_goal_per60: row.personal_shots_on_goal_per60,
      goals_per60: row.personal_goals_per60,
      primary_assists_per60: row.personal_primary_assists_per60,
      coverage_status: row.personal_coverage_status,
      reason_codes: row.personal_reason_codes_json,
    });
    const readPlayers = (season: Season, playerId?: string) =>
      Effect.gen(function* () {
        const rows = yield* sql.unsafe(
          `SELECT s.*, p.display_name, p.reported_position FROM player_season s JOIN person p USING(season,player_id) WHERE s.season=?${playerId === undefined ? "" : " AND s.player_id=?"} ORDER BY s.player_id`,
          playerId === undefined ? [season] : [season, playerId],
        );
        return yield* Effect.try(() =>
          rows.map((input) => {
            const row = decode(JoinedPlayer, input);
            return Schema.decodeUnknownSync(
              PlayerSummary,
              strict,
            )({
              player_id: row.player_id,
              display_name: row.display_name,
              reported_position: row.reported_position,
              teams: row.teams_json,
              listed_games: row.listed_games,
              games_with_included_time: row.games_with_included_time,
              partial_games: row.partial_games,
              unavailable_games: row.unavailable_games,
              metrics: metrics(row),
              personal: personal(row),
            });
          }),
        );
      });
    const readGames = (season: Season, playerId?: string) =>
      Effect.gen(function* () {
        const rows = yield* sql.unsafe(
          `SELECT p.*, g.game_date, g.away_team_id, g.home_team_id, g.away_abbreviation, g.home_abbreviation FROM player_game p JOIN game g USING(season,game_id) WHERE p.season=?${playerId === undefined ? "" : " AND p.player_id=?"} ORDER BY g.game_date, g.game_id, p.player_id`,
          playerId === undefined ? [season] : [season, playerId],
        );
        return yield* Effect.try(() =>
          rows.map((input) => {
            const row = decode(JoinedGame, input);
            if (row.team_id !== row.home_team_id && row.team_id !== row.away_team_id)
              throw new Error("player game team absent from matchup");
            const home = row.team_id === row.home_team_id;
            return Schema.decodeUnknownSync(
              PlayerGame,
              strict,
            )({
              game_id: row.game_id,
              game_date: row.game_date,
              venue: home ? "home" : "away",
              team: {
                id: row.team_id,
                abbreviation: home ? row.home_abbreviation : row.away_abbreviation,
              },
              opponent: {
                id: home ? row.away_team_id : row.home_team_id,
                abbreviation: home ? row.away_abbreviation : row.home_abbreviation,
              },
              metrics: metrics(row),
              personal: personal(row),
              spatial: spatialMetrics(row),
            });
          }),
        );
      });
    for (const evidence of seasons) {
      const season = evidence.season,
        coverage = evidence.coverage;
      const identityInputs = yield* sql.unsafe(
        `SELECT p.season,p.player_id,p.display_name,p.reported_position,p.name_source_json,p.position_source_json,p.teams_json FROM person p JOIN player_season s USING(season,player_id) WHERE p.season=? AND p.kind='skater'`,
        [season],
      );
      const players = yield* readPlayers(season);
      yield* readGames(season);
      const gameInputs = yield* sql.unsafe("SELECT * FROM game WHERE season=?", [season]);
      const playerGameInputs = yield* sql.unsafe("SELECT * FROM player_game WHERE season=?", [
        season,
      ]);
      const physicalSeconds = yield* Effect.try(() => {
        const games = gameInputs.map((row) => decode(GameRow, row));
        const playerGames = playerGameInputs.map((row) => decode(PlayerGameRow, row));
        if (
          coverage.inventory_games !== games.length ||
          coverage.games_with_included_time !==
            games.filter((game) => game.included_seconds > 0).length ||
          coverage.partial_games !==
            games.filter((game) => game.coverage_status === "partial").length ||
          coverage.unavailable_games !==
            games.filter((game) => game.coverage_status === "unavailable").length ||
          (purpose === "real" &&
            (games.length !== 1312 || !games.some((game) => game.included_seconds > 0)))
        )
          throw new Error("season coverage differs from its physical games");
        const reasonCounts = new Map<string, number>();
        for (const game of games)
          for (const reason of game.reason_codes_json)
            reasonCounts.set(reason, (reasonCounts.get(reason) ?? 0) + 1);
        if (
          JSON.stringify(coverage.reason_game_counts) !==
          JSON.stringify(
            [...reasonCounts]
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([code, games]) => ({ code, games })),
          )
        )
          throw new Error("season coverage reasons differ from physical games");
        for (const gap of coverage.unassigned_games) {
          const game = games.find((game) => game.game_id === gap.game_id);
          if (
            game === undefined ||
            gap.date !== game.game_date ||
            gap.away_team_id !== game.away_team_id ||
            gap.home_team_id !== game.home_team_id ||
            game.reason_codes_json.some((reason) => !gap.reason_codes.includes(reason)) ||
            gap.reason_codes.some(
              (reason) =>
                reason !== "roster_identity_unresolved" && !game.reason_codes_json.includes(reason),
            )
          )
            throw new Error("unassigned game evidence differs from its physical game");
        }
        const gameById = new Map(games.map((game) => [game.game_id, game]));
        const identities = identityInputs.map((row) => decode(PlayerRow, row));
        const byGame = new Map<string, typeof playerGames>();
        const byPlayer = new Map<string, typeof playerGames>();
        const checkRates = (value: Metrics | PersonalMetrics) => {
          if (value.included_seconds === 0) return;
          const pairs =
            "shots_on_goal" in value
              ? [
                  [value.shots_on_goal, value.shots_on_goal_per60],
                  [value.goals, value.goals_per60],
                  [value.primary_assists, value.primary_assists_per60],
                ]
              : [
                  [value.attempts_for, value.for_per60],
                  [value.attempts_against, value.against_per60],
                ];
          for (const [count, rate] of pairs) {
            if (count === null || rate === null)
              throw new Error("stored rate lacks its matched count/time");
            // python rounds the integer product at division; javascript rounds it before division.
            const expected = per60(count, value.included_seconds)!;
            if (Math.abs(rate - expected) > 4 * Number.EPSILON * Math.max(rate, expected))
              throw new Error("stored rate differs from its matched count/time");
          }
        };
        for (const row of playerGames) {
          const gameRows = byGame.get(row.game_id) ?? [];
          gameRows.push(row);
          byGame.set(row.game_id, gameRows);
          const playerRows = byPlayer.get(row.player_id) ?? [];
          playerRows.push(row);
          byPlayer.set(row.player_id, playerRows);
          checkRates(metrics(row));
          checkRates(personal(row));
        }
        for (const player of identities) {
          const games = new Set((byPlayer.get(player.player_id) ?? []).map((row) => row.game_id));
          for (const locator of [player.name_source_json, player.position_source_json]) {
            if (locator !== null && !games.has(locator.game_id))
              throw new Error("seasonal player source locator is absent from their listed games");
          }
        }
        for (const game of games) {
          const rows = byGame.get(game.game_id) ?? [];
          const seconds = rows.reduce((sum, row) => sum + row.included_seconds, 0);
          const personalSeconds = rows.reduce((sum, row) => sum + row.personal_included_seconds, 0);
          const attemptsFor = rows.reduce((sum, row) => sum + (row.attempts_for ?? 0), 0);
          const attemptsAgainst = rows.reduce((sum, row) => sum + (row.attempts_against ?? 0), 0);
          const attempts = (game.away_attempts ?? 0) + (game.home_attempts ?? 0);
          if (
            seconds !== 10 * game.included_seconds ||
            personalSeconds !== 10 * game.personal_included_seconds ||
            attemptsFor !== 5 * attempts ||
            attemptsAgainst !== 5 * attempts
          )
            throw new Error(`${game.game_id}: stored game conservation failed`);
        }
        for (const player of players) {
          const identity = identities.find((row) => row.player_id === player.player_id);
          if (
            identity === undefined ||
            !preservesObservedAffiliations(identity.teams_json, player.teams)
          )
            throw new Error("observed person teams differ from its summary");
          const rows = byPlayer.get(player.player_id) ?? [];
          if (
            rows.length !== player.listed_games ||
            rows.filter((row) => row.included_seconds > 0).length !==
              player.games_with_included_time ||
            rows.filter((row) => row.coverage_status === "partial").length !==
              player.partial_games ||
            rows.filter((row) => row.coverage_status === "unavailable").length !==
              player.unavailable_games
          )
            throw new Error(`${player.player_id}: stored season frequencies differ`);
          const teams = new Map<string, PlayerSummary["teams"][number]>();
          for (const row of [...rows].sort((a, b) => {
            const left = gameById.get(a.game_id)!,
              right = gameById.get(b.game_id)!;
            return (
              left.game_date.localeCompare(right.game_date) ||
              left.game_id.localeCompare(right.game_id)
            );
          })) {
            const game = gameById.get(row.game_id)!;
            teams.set(row.team_id, {
              id: row.team_id,
              abbreviation:
                row.team_id === game.away_team_id ? game.away_abbreviation : game.home_abbreviation,
            });
          }
          const expectedTeams = [...teams.values()].sort(
            (a, b) => a.id.length - b.id.length || a.id.localeCompare(b.id),
          );
          if (JSON.stringify(player.teams) !== JSON.stringify(expectedTeams))
            throw new Error(`${player.player_id}: seasonal teams differ from their listed games`);
          const values = rows.map((row) => ({ metrics: metrics(row), personal: personal(row) }));
          for (const group of ["metrics", "personal"] as const) {
            const season = player[group];
            const contributions = values.map((value) => value[group]);
            const quantities = (value: Metrics | PersonalMetrics) =>
              "shots_on_goal" in value
                ? [
                    value.included_seconds,
                    value.known_excluded_seconds,
                    value.shots_on_goal,
                    value.goals,
                    value.primary_assists,
                  ]
                : [
                    value.included_seconds,
                    value.known_excluded_seconds,
                    value.attempts_for,
                    value.attempts_against,
                  ];
            const reductions = contributions.map(quantities);
            for (const [index, stored] of quantities(season).entries()) {
              const reduced = reductions.reduce((sum, row) => sum + (row[index] ?? 0), 0);
              if (stored !== null && stored !== reduced)
                throw new Error(`${player.player_id}: stored ${group} season reduction failed`);
            }
            const zeroReason =
              group === "personal" ? "no_personal_5v5_exposure" : "no_5v5_exposure";
            const reasons = new Set<string>(
              contributions
                .flatMap((value) => value.reason_codes)
                .filter((code) => code !== zeroReason),
            );
            if (coverage.games_with_unassigned_player_associations > 0)
              reasons.add("unassigned_player_games");
            if (
              season.included_seconds === 0 &&
              (group === "personal" || season.coverage_status === "complete")
            )
              reasons.add(zeroReason);
            if (JSON.stringify([...reasons].sort()) !== JSON.stringify(season.reason_codes))
              throw new Error(`${player.player_id}: stored ${group} season reasons differ`);
            checkRates(season);
          }
        }
        return games.reduce((sum, game) => sum + BigInt(game.included_seconds), 0n);
      });
      const mismatched = yield* sql.unsafe(
        "SELECT 1 FROM player_season s JOIN person p USING(season,player_id) WHERE s.season=? AND p.kind<>'skater' LIMIT 1",
        [season],
      );
      if (mismatched.length > 0)
        return yield* Effect.fail(
          new Error("observed person kind/teams differ from its season summary"),
        );
      yield* validateDeployment(sql, season, players, physicalSeconds);
      yield* validateSpatial(
        sql,
        season,
        evidence.spatial_coverage,
        coverage.games_with_unassigned_player_associations,
      );
    }
    return {
      readPlayers,
      readGames,
      readDeployment: (season: Season, id: string) => readDeployment(sql, season, id),
    };
  });
