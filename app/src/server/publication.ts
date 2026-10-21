import * as SqliteClient from "@effect/sql-sqlite-node/SqliteClient";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import type { SqlError } from "effect/sql/SqlError";
import {
  Count, Coverage, CoverageStatus, DateString, GameId, GitCommit, HockeyId, LeagueResponse, Metrics,
  PlayerGame, PlayerResponse, PlayerSummary, Publication as PublicationSchema, ReasonCodes,
} from "../shared/observed.js";

const Locator = Schema.Struct({ game_id: GameId, source_index: Count });
const Implementation = Schema.Struct({ git_commit: GitCommit, git_dirty: Schema.NullOr(Schema.Boolean), python_version: Schema.String });
const Producer = Schema.Struct({ ...Implementation.fields, sqlite_version: Schema.String, source_implementations: Schema.Array(Implementation) });
const { reason_codes, ...metricValues } = Metrics.fields;
const { git_commit, ...publicationFields } = PublicationSchema.fields;
const metricColumns = { ...metricValues, reason_codes_json: Schema.fromJsonString(reason_codes) };
const PublicationRow = Schema.Struct({
  id: Schema.Literal(1), schema_version: Schema.Literal(1),
  ...publicationFields,
  game_type: Schema.Literal(2), producer_json: Schema.fromJsonString(Producer), coverage_json: Schema.fromJsonString(Coverage),
});
const PlayerRow = Schema.Struct({
  player_id: HockeyId, display_name: Schema.NullOr(Schema.String), reported_position: PlayerSummary.fields.reported_position,
  name_source_json: Schema.NullOr(Schema.fromJsonString(Locator)), position_source_json: Schema.fromJsonString(Locator),
});
const GameRow = Schema.Struct({
  game_id: GameId, game_date: DateString, away_team_id: HockeyId, home_team_id: HockeyId,
  away_abbreviation: Schema.NullOr(Schema.String), home_abbreviation: Schema.NullOr(Schema.String),
  included_seconds: Count, known_excluded_seconds: Count, known_unresolved_seconds: Count,
  horizon_unavailable: Schema.Literals([0, 1]), away_attempts: Schema.NullOr(Count), home_attempts: Schema.NullOr(Count),
  coverage_status: CoverageStatus, reason_codes_json: Schema.fromJsonString(ReasonCodes),
}).check(Schema.makeFilter((game) => {
  if (game.away_team_id === game.home_team_id || game.coverage_status === "complete" && game.known_excluded_seconds !== 0) return false;
  if (game.included_seconds > 0) return game.away_attempts !== null && game.home_attempts !== null && (game.coverage_status === "complete" ? game.reason_codes_json.length === 0 : game.coverage_status === "partial" && game.reason_codes_json.length > 0 && !game.reason_codes_json.includes("no_5v5_exposure"));
  if (game.coverage_status === "complete") return game.away_attempts === 0 && game.home_attempts === 0 && game.reason_codes_json.length === 1 && game.reason_codes_json[0] === "no_5v5_exposure";
  return game.coverage_status === "unavailable" && game.away_attempts === null && game.home_attempts === null && game.reason_codes_json.length > 0 && !game.reason_codes_json.includes("no_5v5_exposure");
}));
const PlayerGameRow = Schema.Struct({ player_id: HockeyId, game_id: GameId, team_id: HockeyId, ...metricColumns });
const PlayerSeasonRow = Schema.Struct({
  player_id: HockeyId, teams_json: Schema.fromJsonString(PlayerSummary.fields.teams),
  listed_games: PlayerSummary.fields.listed_games, games_with_included_time: Count, partial_games: Count, unavailable_games: Count,
  ...metricColumns,
});
const strict = { onExcessProperty: "error" } as const;
const tables = {
  publication: PublicationRow, player: PlayerRow, game: GameRow, player_game: PlayerGameRow, player_season: PlayerSeasonRow,
};
const physicalColumns = {
  publication: ["id", "schema_version", "kind", "publication_id", "purpose", "season", "game_type", "generated_at", "source_requested_min", "source_requested_max", "undated_sources", "population_version", "corpus_sha256", "producer_json", "coverage_json"],
  player: ["player_id", "display_name", "reported_position", "name_source_json", "position_source_json"],
  game: Object.keys(GameRow.fields), player_game: Object.keys(PlayerGameRow.fields), player_season: Object.keys(PlayerSeasonRow.fields),
};
const integerColumns = new Set(["id", "schema_version", "game_type", "undated_sources", "included_seconds", "known_excluded_seconds", "known_unresolved_seconds", "horizon_unavailable", "away_attempts", "home_attempts", "listed_games", "games_with_included_time", "partial_games", "unavailable_games", "attempts_for", "attempts_against"]);
const nullableColumns = new Set(["id", "display_name", "name_source_json", "source_requested_min", "source_requested_max", "away_abbreviation", "home_abbreviation", "away_attempts", "home_attempts", "attempts_for", "attempts_against", "for_per60", "against_per60"]);
const primaryKeys = { publication: ["id"], player: ["player_id"], game: ["game_id"], player_game: ["player_id", "game_id"], player_season: ["player_id"] };
const foreignKeyDefinitions = { publication: [], player: [], game: [], player_game: ["game:game_id:game_id", "player:player_id:player_id"], player_season: ["player:player_id:player_id"] };

export interface PublicationReader {
  readonly metadata: PublicationSchema;
  readonly coverage: Coverage;
  readonly league: Effect.Effect<LeagueResponse, Error | SqlError>;
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
    if (JSON.stringify(version) !== '[{"user_version":1}]' || JSON.stringify(journal) !== '[{"journal_mode":"delete"}]') throw new Error("incompatible publication version or journal mode");
    const actual = tableList.filter((table) => !table.name.startsWith("sqlite_"));
    if (actual.length !== 5 || actual.some((table) => table.type !== "table" || table.strict !== 1 || !(table.name in tables))) throw new Error("publication requires exactly five strict tables");
  });
  for (const [table, schema] of Object.entries(tables)) {
    const columns = yield* sql.unsafe<{ name: string; type: string; notnull: number; pk: number; dflt_value: unknown }>(`PRAGMA table_info(${table})`);
    const foreignKeys = yield* sql.unsafe<{ seq: number; table: string; from: string; to: string; on_update: string; on_delete: string; match: string }>(`PRAGMA foreign_key_list(${table})`);
    const rows = yield* sql.unsafe(`SELECT * FROM ${table}`);
    yield* Effect.try(() => {
      if (JSON.stringify(columns.map((column) => column.name)) !== JSON.stringify(physicalColumns[table as keyof typeof tables])) throw new Error(`${table}: incompatible columns`);
      for (const column of columns) {
        const type = integerColumns.has(column.name) ? "INTEGER" : column.name === "for_per60" || column.name === "against_per60" ? "REAL" : "TEXT";
        const key = table as keyof typeof tables;
        if (column.type !== type || column.notnull !== (nullableColumns.has(column.name) ? 0 : 1) || column.pk !== primaryKeys[key].indexOf(column.name) + 1 || column.dflt_value !== null) throw new Error(`${table}.${column.name}: incompatible physical column`);
      }
      const key = table as keyof typeof tables;
      if (JSON.stringify(foreignKeys.map((key) => `${key.table}:${key.from}:${key.to}`).sort()) !== JSON.stringify(foreignKeyDefinitions[key]) || foreignKeys.some((key) => key.seq !== 0 || key.on_update !== "NO ACTION" || key.on_delete !== "NO ACTION" || key.match !== "NONE")) throw new Error(`${table}: incompatible foreign keys`);
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
    undated_sources: stored.undated_sources, population_version: stored.population_version, corpus_sha256: stored.corpus_sha256, git_commit: stored.producer_json.git_commit,
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
  const readPlayers = () => Effect.gen(function* () {
    const rows = yield* sql.unsafe("SELECT s.*, p.display_name, p.reported_position FROM player_season s JOIN player p USING(player_id) ORDER BY s.player_id");
    return yield* Effect.try(() => rows.map((input) => {
      const row = Schema.decodeUnknownSync(JoinedPlayer, strict)(input);
      return Schema.decodeUnknownSync(PlayerSummary, strict)({
        player_id: row.player_id, display_name: row.display_name, reported_position: row.reported_position,
        teams: row.teams_json, listed_games: row.listed_games, games_with_included_time: row.games_with_included_time,
        partial_games: row.partial_games, unavailable_games: row.unavailable_games, metrics: metrics(row),
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
        metrics: metrics(row),
      });
    }));
  });
  yield* readPlayers();
  yield* readGames();
  const missingSeasons = yield* sql.unsafe("SELECT player_id FROM player EXCEPT SELECT player_id FROM player_season");
  if (missingSeasons.length !== 0) return yield* Effect.fail(new Error("player missing season summary"));
  return {
    metadata, coverage,
    league: Effect.map(readPlayers(), (players) => ({ publication: metadata, coverage, players })),
    player: (playerId: string) => Effect.gen(function* () {
      const players = yield* readPlayers();
      if (!players.some((player) => player.player_id === playerId)) return undefined;
      const games = yield* readGames(playerId);
      return { publication: metadata, coverage, players, games };
    }),
  } satisfies PublicationReader;
})).pipe(Layer.provide(SqliteClient.layer({ filename, readonly: true, disableWAL: true })));
