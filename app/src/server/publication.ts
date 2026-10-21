import * as SqliteClient from "@effect/sql-sqlite-node/SqliteClient";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import type { SqlError } from "effect/sql/SqlError";
import {
  Count, Coverage, CoverageStatus, DateString, GameId, GitCommit, HockeyId, LeagueResponse, Metrics,
  PersonalMetrics, PersonalReasonCodes, PlayerGame, PlayerResponse, PlayerSummary, Publication as PublicationSchema, ReasonCodes, SpatialCoverage,
} from "../shared/observed.js";

import { spatialColumns, spatialGameColumns, spatialTables, spatialIntegerColumns, spatialNullableColumns, spatialRealColumns, spatialMetrics, readSpatial } from "./spatial-publication.js";

const Locator = Schema.Struct({ game_id: GameId, source_index: Count });
const Implementation = Schema.Struct({ git_commit: GitCommit, git_dirty: Schema.NullOr(Schema.Boolean), python_version: Schema.String });
const Producer = Schema.Struct({ ...Implementation.fields, sqlite_version: Schema.String, source_implementations: Schema.Array(Implementation), spatial_consumed_fields: Schema.Tuple([
  Schema.Literal("interpreted.events.reported_x"), Schema.Literal("interpreted.events.reported_y"), Schema.Literal("interpreted.events.home_team_defending_side"),
  Schema.Literal("reconstruction.events.attacking_x"), Schema.Literal("reconstruction.events.attacking_y"), Schema.Literal("reconstruction.events.coordinate_status"),
]) });
const { reason_codes, ...metricValues } = Metrics.fields;
const { git_commit, ...publicationFields } = PublicationSchema.fields;
const metricColumns = { ...metricValues, reason_codes_json: Schema.fromJsonString(reason_codes) };
const personalColumns = {
  personal_included_seconds: Count, personal_known_excluded_seconds: Count,
  personal_shots_on_goal: Schema.NullOr(Count), personal_goals: Schema.NullOr(Count), personal_primary_assists: Schema.NullOr(Count),
  personal_shots_on_goal_per60: PersonalMetrics.fields.shots_on_goal_per60,
  personal_goals_per60: PersonalMetrics.fields.goals_per60,
  personal_primary_assists_per60: PersonalMetrics.fields.primary_assists_per60,
  personal_coverage_status: CoverageStatus, personal_reason_codes_json: Schema.fromJsonString(PersonalReasonCodes),
};
const PublicationRow = Schema.Struct({
  id: Schema.Literal(1), schema_version: Schema.Literal(3),
  ...publicationFields,
  game_type: Schema.Literal(2), producer_json: Schema.fromJsonString(Producer), coverage_json: Schema.fromJsonString(Coverage), spatial_coverage_json: Schema.fromJsonString(SpatialCoverage),
});
const PlayerRow = Schema.Struct({
  player_id: HockeyId, display_name: Schema.NullOr(Schema.String), reported_position: PlayerSummary.fields.reported_position,
  name_source_json: Schema.NullOr(Schema.fromJsonString(Locator)), position_source_json: Schema.fromJsonString(Locator),
});
const GameRow = Schema.Struct({
  game_id: GameId, game_date: DateString, away_team_id: HockeyId, home_team_id: HockeyId,
  away_abbreviation: Schema.NullOr(Schema.String), home_abbreviation: Schema.NullOr(Schema.String),
  included_seconds: Count, known_excluded_seconds: Count,
  personal_included_seconds: Count, personal_known_excluded_seconds: Count, known_unresolved_seconds: Count,
  horizon_unavailable: Schema.Literals([0, 1]), away_attempts: Schema.NullOr(Count), home_attempts: Schema.NullOr(Count),
  coverage_status: CoverageStatus, reason_codes_json: Schema.fromJsonString(ReasonCodes), ...spatialGameColumns,
}).check(Schema.makeFilter((game) => {
  if (game.personal_included_seconds > game.included_seconds || game.personal_known_excluded_seconds - game.known_excluded_seconds !== game.included_seconds - game.personal_included_seconds || game.away_team_id === game.home_team_id || game.coverage_status === "complete" && game.known_excluded_seconds !== 0) return false;
  if (game.included_seconds > 0) return game.away_attempts !== null && game.home_attempts !== null && (game.coverage_status === "complete" ? game.reason_codes_json.length === 0 : game.coverage_status === "partial" && game.reason_codes_json.length > 0 && !game.reason_codes_json.includes("no_5v5_exposure"));
  if (game.coverage_status === "complete") return game.away_attempts === 0 && game.home_attempts === 0 && game.reason_codes_json.length === 1 && game.reason_codes_json[0] === "no_5v5_exposure";
  return game.coverage_status === "unavailable" && game.away_attempts === null && game.home_attempts === null && game.reason_codes_json.length > 0 && !game.reason_codes_json.includes("no_5v5_exposure");
}));
const PlayerGameRow = Schema.Struct({ player_id: HockeyId, game_id: GameId, team_id: HockeyId, ...metricColumns, ...personalColumns, ...spatialColumns });
const PlayerSeasonRow = Schema.Struct({
  player_id: HockeyId, teams_json: Schema.fromJsonString(PlayerSummary.fields.teams),
  listed_games: PlayerSummary.fields.listed_games, games_with_included_time: Count, partial_games: Count, unavailable_games: Count,
  ...metricColumns, ...personalColumns, ...spatialColumns,
});
const strict = { onExcessProperty: "error" } as const;
const tables = {
  publication: PublicationRow, player: PlayerRow, game: GameRow, player_game: PlayerGameRow, player_season: PlayerSeasonRow, ...spatialTables,
};
const physicalColumns = {
  publication: ["id", "schema_version", "kind", "publication_id", "purpose", "season", "game_type", "generated_at", "source_requested_min", "source_requested_max", "undated_sources", "population_version", "personal_population_version", "corpus_sha256", "producer_json", "coverage_json", "spatial_population_version", "spatial_display_version", "spatial_coverage_json"],
  player: ["player_id", "display_name", "reported_position", "name_source_json", "position_source_json"],
  game: Object.keys(GameRow.fields), player_game: Object.keys(PlayerGameRow.fields), player_season: Object.keys(PlayerSeasonRow.fields),
  spatial_cell: Object.keys(spatialTables.spatial_cell.fields), player_game_spatial: Object.keys(spatialTables.player_game_spatial.fields), player_season_spatial: Object.keys(spatialTables.player_season_spatial.fields),
};
const integerColumns = new Set([...spatialIntegerColumns, "id", "schema_version", "game_type", "undated_sources", "included_seconds", "known_excluded_seconds", "known_unresolved_seconds", "horizon_unavailable", "away_attempts", "home_attempts", "listed_games", "games_with_included_time", "partial_games", "unavailable_games", "attempts_for", "attempts_against", "personal_included_seconds", "personal_known_excluded_seconds", "personal_shots_on_goal", "personal_goals", "personal_primary_assists"]);
const nullableColumns = new Set([...spatialNullableColumns, "id", "display_name", "name_source_json", "source_requested_min", "source_requested_max", "away_abbreviation", "home_abbreviation", "away_attempts", "home_attempts", "attempts_for", "attempts_against", "for_per60", "against_per60", "personal_shots_on_goal", "personal_goals", "personal_primary_assists", "personal_shots_on_goal_per60", "personal_goals_per60", "personal_primary_assists_per60"]);
const primaryKeys = { publication: ["id"], player: ["player_id"], game: ["game_id"], player_game: ["player_id", "game_id"], player_season: ["player_id"], spatial_cell: ["cell_id"], player_game_spatial: ["player_id","game_id","cell_id"], player_season_spatial:["player_id","cell_id"] };
const foreignKeyDefinitions = { publication: [], player: [], game: [], player_game: ["game:game_id:game_id", "player:player_id:player_id"], player_season: ["player:player_id:player_id"], spatial_cell: [], player_game_spatial: ["player_game:player_id:player_id,game_id:game_id", "spatial_cell:cell_id:cell_id"], player_season_spatial: ["player_season:player_id:player_id", "spatial_cell:cell_id:cell_id"] };

export interface PublicationReader {
  readonly metadata: PublicationSchema;
  readonly coverage: Coverage;
  readonly league: (spatialIds?: readonly string[]) => Effect.Effect<LeagueResponse, Error | SqlError>;
  readonly player: (playerId: string) => Effect.Effect<PlayerResponse | undefined, Error | SqlError>;
}
export const Publication = Context.Service<PublicationReader>("hockey-stats/Publication");

export const publicationLayer = (filename: string) => Layer.effect(Publication, Effect.gen(function* () {
  const sql = yield* SqliteClient.SqliteClient;
  const integrity = yield* sql.unsafe("PRAGMA integrity_check");
  const foreignKeys = yield* sql.unsafe("PRAGMA foreign_key_check");
  const version = yield* sql.unsafe("PRAGMA user_version");
  const journal = yield* sql.unsafe("PRAGMA journal_mode");
  const tableList = yield* sql.unsafe<{ name: string; type: string; strict: number }>("PRAGMA table_list");
  yield* Effect.try(() => {
    if (JSON.stringify(integrity) !== '[{"integrity_check":"ok"}]' || foreignKeys.length !== 0) throw new Error("publication integrity or foreign-key check failed");
    if (JSON.stringify(version) !== '[{"user_version":3}]' || JSON.stringify(journal) !== '[{"journal_mode":"delete"}]') throw new Error("incompatible publication version or journal mode");
    const actual = tableList.filter((table) => !table.name.startsWith("sqlite_"));
    if (actual.length !== 8 || actual.some((table) => table.type !== "table" || table.strict !== 1 || !(table.name in tables))) throw new Error("publication requires exactly eight strict tables");
  });
  for (const [table, schema] of Object.entries(tables)) {
    const columns = yield* sql.unsafe<{ name: string; type: string; notnull: number; pk: number; dflt_value: unknown }>(`PRAGMA table_info(${table})`);
    const foreignKeys = yield* sql.unsafe<{ id: number; seq: number; table: string; from: string; to: string; on_update: string; on_delete: string; match: string }>(`PRAGMA foreign_key_list(${table})`);
    const rows = table in spatialTables ? [] : yield* sql.unsafe(`SELECT * FROM ${table}`);
    yield* Effect.try(() => {
      if (JSON.stringify(columns.map((column) => column.name)) !== JSON.stringify(physicalColumns[table as keyof typeof tables])) throw new Error(`${table}: incompatible columns`);
      for (const column of columns) {
        const type = integerColumns.has(column.name) ? "INTEGER" : column.name === "for_per60" || column.name === "against_per60" || column.name.endsWith("_per60") || spatialRealColumns.includes(column.name) ? "REAL" : "TEXT";
        const key = table as keyof typeof tables;
        if (column.type !== type || column.notnull !== (nullableColumns.has(column.name) || table === "spatial_cell" && column.name === "cell_id" ? 0 : 1) || column.pk !== primaryKeys[key].indexOf(column.name) + 1 || column.dflt_value !== null) throw new Error(`${table}.${column.name}: incompatible physical column`);
      }
      const key = table as keyof typeof tables;
      const relations = new Map<number, typeof foreignKeys[number][]>();
      for (const relation of foreignKeys) relations.set(relation.id, [...(relations.get(relation.id) ?? []), relation]);
      const definitions = [...relations.values()].map((parts) => {
        parts.sort((a,b) => a.seq-b.seq);
        if (parts.some((part,index) => part.seq !== index || part.table !== parts[0].table)) throw new Error(`${table}: invalid composite relation`);
        return `${parts[0].table}:${parts.map((part) => `${part.from}:${part.to}`).join(",")}`;
      }).sort();
      if (JSON.stringify(definitions) !== JSON.stringify(foreignKeyDefinitions[key]) || foreignKeys.some((key) => key.on_update !== "NO ACTION" || key.on_delete !== "NO ACTION" || key.match !== "NONE")) throw new Error(`${table}: incompatible foreign keys`);
      for (const row of rows) Schema.decodeUnknownSync(schema, strict)(row);
    });
  }
  const metadataRows = yield* sql.unsafe("SELECT * FROM publication");
  const stored = yield* Effect.try(() => {
    if (metadataRows.length !== 1) throw new Error("publication requires one metadata row");
    return Schema.decodeUnknownSync(PublicationRow, strict)(metadataRows[0]);
  });
  const metadata = yield* Effect.try(() => Schema.decodeUnknownSync(PublicationSchema, strict)({
    publication_id: stored.publication_id, kind: stored.kind, purpose: stored.purpose, season: stored.season,
    generated_at: stored.generated_at, source_requested_min: stored.source_requested_min, source_requested_max: stored.source_requested_max,
    undated_sources: stored.undated_sources, population_version: stored.population_version, personal_population_version: stored.personal_population_version, spatial_population_version: stored.spatial_population_version, spatial_display_version: stored.spatial_display_version, corpus_sha256: stored.corpus_sha256, git_commit: stored.producer_json.git_commit,
  }));
  const coverage = stored.coverage_json;
  const JoinedPlayer = Schema.Struct({ ...PlayerSeasonRow.fields, display_name: PlayerRow.fields.display_name, reported_position: PlayerRow.fields.reported_position });
  const JoinedGame = Schema.Struct({
    ...PlayerGameRow.fields, game_date: DateString, away_team_id: HockeyId, home_team_id: HockeyId,
    away_abbreviation: Schema.NullOr(Schema.String), home_abbreviation: Schema.NullOr(Schema.String),
  });
  const metrics = (row: typeof PlayerGameRow.Type | typeof PlayerSeasonRow.Type): Metrics => ({
    included_seconds: row.included_seconds, known_excluded_seconds: row.known_excluded_seconds,
    attempts_for: row.attempts_for, attempts_against: row.attempts_against, for_per60: row.for_per60,
    against_per60: row.against_per60, coverage_status: row.coverage_status, reason_codes: row.reason_codes_json,
  });
  const personal = (row: typeof PlayerGameRow.Type | typeof PlayerSeasonRow.Type): PersonalMetrics => ({
    included_seconds: row.personal_included_seconds, known_excluded_seconds: row.personal_known_excluded_seconds,
    shots_on_goal: row.personal_shots_on_goal, goals: row.personal_goals, primary_assists: row.personal_primary_assists,
    shots_on_goal_per60: row.personal_shots_on_goal_per60, goals_per60: row.personal_goals_per60,
    primary_assists_per60: row.personal_primary_assists_per60, coverage_status: row.personal_coverage_status,
    reason_codes: row.personal_reason_codes_json,
  });
  const readPlayers = () => Effect.gen(function* () {
    const rows = yield* sql.unsafe("SELECT s.*, p.display_name, p.reported_position FROM player_season s JOIN player p USING(player_id) ORDER BY s.player_id");
    return yield* Effect.try(() => rows.map((input) => {
      const row = Schema.decodeUnknownSync(JoinedPlayer, strict)(input);
      return Schema.decodeUnknownSync(PlayerSummary, strict)({
        player_id: row.player_id, display_name: row.display_name, reported_position: row.reported_position,
        teams: row.teams_json, listed_games: row.listed_games, games_with_included_time: row.games_with_included_time,
        partial_games: row.partial_games, unavailable_games: row.unavailable_games, metrics: metrics(row), personal: personal(row),
      });
    }));
  });
  const readGames = (playerId?: string) => Effect.gen(function* () {
    const rows = yield* sql.unsafe(`SELECT p.*, g.game_date, g.away_team_id, g.home_team_id, g.away_abbreviation, g.home_abbreviation FROM player_game p JOIN game g USING(game_id)${playerId === undefined ? "" : " WHERE p.player_id = ?"} ORDER BY g.game_date, g.game_id, p.player_id`, playerId === undefined ? [] : [playerId]);
    return yield* Effect.try(() => rows.map((input) => {
      const row = Schema.decodeUnknownSync(JoinedGame, strict)(input);
      if (row.team_id !== row.home_team_id && row.team_id !== row.away_team_id) throw new Error("player game team absent from matchup");
      const home = row.team_id === row.home_team_id;
      return Schema.decodeUnknownSync(PlayerGame, strict)({
        game_id: row.game_id, game_date: row.game_date, venue: home ? "home" : "away",
        team: { id: row.team_id, abbreviation: home ? row.home_abbreviation : row.away_abbreviation },
        opponent: { id: home ? row.away_team_id : row.home_team_id, abbreviation: home ? row.away_abbreviation : row.home_abbreviation },
        metrics: metrics(row), personal: personal(row), spatial: spatialMetrics(row),
      });
    }));
  });
  const players = yield* readPlayers();
  yield* readGames();
  const gameInputs = yield* sql.unsafe("SELECT * FROM game");
  const playerGameInputs = yield* sql.unsafe("SELECT * FROM player_game");
  yield* Effect.try(() => {
    const games = gameInputs.map((row) => Schema.decodeUnknownSync(GameRow, strict)(row));
    const playerGames = playerGameInputs.map((row) => Schema.decodeUnknownSync(PlayerGameRow, strict)(row));
    const byGame = new Map<string, typeof playerGames>();
    const byPlayer = new Map<string, typeof playerGames>();
    const checkRates = (value: Metrics | PersonalMetrics) => {
      if (value.included_seconds === 0) return;
      const pairs = "shots_on_goal" in value
        ? [[value.shots_on_goal, value.shots_on_goal_per60], [value.goals, value.goals_per60], [value.primary_assists, value.primary_assists_per60]]
        : [[value.attempts_for, value.for_per60], [value.attempts_against, value.against_per60]];
      for (const [count, rate] of pairs) {
        if (count === null || rate === null) throw new Error("stored rate lacks its matched count/time");
        // python rounds the integer product at division; javascript rounds it before division.
        const expected = 3600 * count / value.included_seconds;
        if (Math.abs(rate - expected) > 4 * Number.EPSILON * Math.max(rate, expected)) throw new Error("stored rate differs from its matched count/time");
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
    for (const game of games) {
      const rows = byGame.get(game.game_id) ?? [];
      const seconds = rows.reduce((sum, row) => sum + row.included_seconds, 0);
      const personalSeconds = rows.reduce((sum, row) => sum + row.personal_included_seconds, 0);
      const attemptsFor = rows.reduce((sum, row) => sum + (row.attempts_for ?? 0), 0);
      const attemptsAgainst = rows.reduce((sum, row) => sum + (row.attempts_against ?? 0), 0);
      const attempts = (game.away_attempts ?? 0) + (game.home_attempts ?? 0);
      if (seconds !== 10 * game.included_seconds || personalSeconds !== 10 * game.personal_included_seconds || attemptsFor !== 5 * attempts || attemptsAgainst !== 5 * attempts) throw new Error(`${game.game_id}: stored game conservation failed`);
    }
    for (const player of players) {
      const rows = byPlayer.get(player.player_id) ?? [];
      if (rows.length !== player.listed_games || rows.filter((row) => row.included_seconds > 0).length !== player.games_with_included_time || rows.filter((row) => row.coverage_status === "partial").length !== player.partial_games || rows.filter((row) => row.coverage_status === "unavailable").length !== player.unavailable_games) throw new Error(`${player.player_id}: stored season frequencies differ`);
      const values = rows.map((row) => ({ metrics: metrics(row), personal: personal(row) }));
      for (const group of ["metrics", "personal"] as const) {
        const season = player[group];
        const contributions = values.map((value) => value[group]);
        const quantities = (value: Metrics | PersonalMetrics) => "shots_on_goal" in value
          ? [value.included_seconds, value.known_excluded_seconds, value.shots_on_goal, value.goals, value.primary_assists]
          : [value.included_seconds, value.known_excluded_seconds, value.attempts_for, value.attempts_against];
        const reductions = contributions.map(quantities);
        for (const [index, stored] of quantities(season).entries()) {
          const reduced = reductions.reduce((sum, row) => sum + (row[index] ?? 0), 0);
          if (stored !== null && stored !== reduced) throw new Error(`${player.player_id}: stored ${group} season reduction failed`);
        }
        const zeroReason = group === "personal" ? "no_personal_5v5_exposure" : "no_5v5_exposure";
        const reasons = new Set<string>(contributions.flatMap((value) => value.reason_codes).filter((code) => code !== zeroReason));
        if (coverage.games_with_unassigned_player_associations > 0) reasons.add("unassigned_player_games");
        if (season.included_seconds === 0 && (group === "personal" || season.coverage_status === "complete")) reasons.add(zeroReason);
        if (JSON.stringify([...reasons].sort()) !== JSON.stringify(season.reason_codes)) throw new Error(`${player.player_id}: stored ${group} season reasons differ`);
        checkRates(season);
      }
    }
  });
  const missingSeasons = yield* sql.unsafe("SELECT player_id FROM player EXCEPT SELECT player_id FROM player_season");
  if (missingSeasons.length !== 0) return yield* Effect.fail(new Error("player missing season summary"));
  const spatial = yield* readSpatial(sql, stored.spatial_coverage_json, coverage.games_with_unassigned_player_associations);
  return {
    metadata, coverage,
    league: (ids?: readonly string[]) => Effect.gen(function* () {
      const players = yield* readPlayers();
      return { publication: metadata, coverage, players, spatial: yield* spatial(ids) };
    }),
    player: (playerId: string) => Effect.gen(function* () {
      const players = yield* readPlayers();
      if (!players.some((player) => player.player_id === playerId)) return undefined;
      const games = yield* readGames(playerId);
      return { publication: metadata, coverage, players, games, spatial: yield* spatial([playerId]) };
    }),
  } satisfies PublicationReader;
})).pipe(Layer.provide(SqliteClient.layer({ filename, readonly: true, disableWAL: true })));
