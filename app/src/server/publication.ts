import * as SqliteClient from "@effect/sql-sqlite-node/SqliteClient";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import type { SqlError } from "effect/sql/SqlError";
import {
  Count, Coverage, CoverageStatus, DateString, GameId, GitCommit, HockeyId, LeagueResponse, Metrics,
  PersonalMetrics, PersonalReasonCodes, PlayerGame, PlayerResponse, PlayerSummary, Publication as PublicationSchema, ReasonCodes, Season, SeasonEvidence, SpatialCoverage,
} from "../shared/observed.js";

import { spatialColumns, spatialGameColumns, spatialTables, spatialIntegerColumns, spatialNullableColumns, spatialRealColumns, spatialMetrics, readSpatial, validateSpatial } from "./spatial-publication.js";

const Locator = Schema.Struct({ game_id: GameId, source_index: Count });
const Implementation = Schema.Struct({ git_commit: GitCommit, git_dirty: Schema.NullOr(Schema.Boolean), python_version: Schema.String.check(Schema.isNonEmpty()) });
const Producer = Schema.Struct({ ...Implementation.fields, sqlite_version: Schema.String, spatial_consumed_fields: Schema.Tuple([
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
  id: Schema.Literal(1), schema_version: Schema.Literal(4),
  ...publicationFields,
  game_type: Schema.Literal(2), producer_json: Schema.fromJsonString(Producer),
});
const SeasonRow = Schema.Struct({
  season: Season, corpus_sha256: SeasonEvidence.fields.corpus_sha256,
  source_requested_min: SeasonEvidence.fields.source_requested_min, source_requested_max: SeasonEvidence.fields.source_requested_max,
  undated_sources: Count, coverage_json: Schema.fromJsonString(Coverage), source_implementations_json: Schema.fromJsonString(Schema.Array(Implementation).check(Schema.makeFilter((identities) => new Set(identities.map((identity) => JSON.stringify(identity))).size === identities.length))),
  spatial_coverage_json: Schema.fromJsonString(SpatialCoverage),
});
const PlayerRow = Schema.Struct({
  season: Season, player_id: HockeyId, display_name: Schema.NullOr(Schema.String), reported_position: PlayerSummary.fields.reported_position,
  name_source_json: Schema.NullOr(Schema.fromJsonString(Locator)), position_source_json: Schema.fromJsonString(Locator),
});
const GameRow = Schema.Struct({
  season: Season, game_id: GameId, game_date: DateString, away_team_id: HockeyId, home_team_id: HockeyId,
  away_abbreviation: Schema.NullOr(Schema.String), home_abbreviation: Schema.NullOr(Schema.String),
  included_seconds: Count, known_excluded_seconds: Count,
  personal_included_seconds: Count, personal_known_excluded_seconds: Count, known_unresolved_seconds: Count,
  horizon_unavailable: Schema.Literals([0, 1]), away_attempts: Schema.NullOr(Count), home_attempts: Schema.NullOr(Count),
  coverage_status: CoverageStatus, reason_codes_json: Schema.fromJsonString(ReasonCodes), ...spatialGameColumns,
}).check(Schema.makeFilter((game) => {
  if (game.game_id.slice(0, 4) !== game.season.slice(0, 4) || game.game_id.slice(4, 6) !== "02") return false;
  if (game.personal_included_seconds > game.included_seconds || game.personal_known_excluded_seconds - game.known_excluded_seconds !== game.included_seconds - game.personal_included_seconds || game.away_team_id === game.home_team_id || game.coverage_status === "complete" && game.known_excluded_seconds !== 0) return false;
  if (game.included_seconds > 0) return game.away_attempts !== null && game.home_attempts !== null && (game.coverage_status === "complete" ? game.reason_codes_json.length === 0 : game.coverage_status === "partial" && game.reason_codes_json.length > 0 && !game.reason_codes_json.includes("no_5v5_exposure"));
  if (game.coverage_status === "complete") return game.away_attempts === 0 && game.home_attempts === 0 && game.reason_codes_json.length === 1 && game.reason_codes_json[0] === "no_5v5_exposure";
  return game.coverage_status === "unavailable" && game.away_attempts === null && game.home_attempts === null && game.reason_codes_json.length > 0 && !game.reason_codes_json.includes("no_5v5_exposure");
}));
const PlayerGameRow = Schema.Struct({ season: Season, player_id: HockeyId, game_id: GameId, team_id: HockeyId, ...metricColumns, ...personalColumns, ...spatialColumns });
const PlayerSeasonRow = Schema.Struct({
  season: Season, player_id: HockeyId, teams_json: Schema.fromJsonString(PlayerSummary.fields.teams),
  listed_games: PlayerSummary.fields.listed_games, games_with_included_time: Count, partial_games: Count, unavailable_games: Count,
  ...metricColumns, ...personalColumns, ...spatialColumns,
});
const strict = { onExcessProperty: "error" } as const;
const tables = {
  publication: PublicationRow, season: SeasonRow, player: PlayerRow, game: GameRow, player_game: PlayerGameRow, player_season: PlayerSeasonRow, ...spatialTables,
};
const physicalColumns = {
  publication: ["id", "schema_version", "kind", "publication_id", "purpose", "game_type", "generated_at", "population_version", "personal_population_version", "producer_json", "spatial_population_version", "spatial_display_version"],
  season: Object.keys(SeasonRow.fields), player: Object.keys(PlayerRow.fields),
  game: Object.keys(GameRow.fields), player_game: Object.keys(PlayerGameRow.fields), player_season: Object.keys(PlayerSeasonRow.fields),
  spatial_cell: Object.keys(spatialTables.spatial_cell.fields), player_game_spatial: Object.keys(spatialTables.player_game_spatial.fields), player_season_spatial: Object.keys(spatialTables.player_season_spatial.fields),
};
const integerColumns = new Set([...spatialIntegerColumns, "id", "schema_version", "game_type", "undated_sources", "included_seconds", "known_excluded_seconds", "known_unresolved_seconds", "horizon_unavailable", "away_attempts", "home_attempts", "listed_games", "games_with_included_time", "partial_games", "unavailable_games", "attempts_for", "attempts_against", "personal_included_seconds", "personal_known_excluded_seconds", "personal_shots_on_goal", "personal_goals", "personal_primary_assists"]);
const nullableColumns = new Set([...spatialNullableColumns, "id", "display_name", "name_source_json", "source_requested_min", "source_requested_max", "away_abbreviation", "home_abbreviation", "away_attempts", "home_attempts", "attempts_for", "attempts_against", "for_per60", "against_per60", "personal_shots_on_goal", "personal_goals", "personal_primary_assists", "personal_shots_on_goal_per60", "personal_goals_per60", "personal_primary_assists_per60"]);
const primaryKeys = { publication: ["id"], season: ["season"], player: ["season", "player_id"], game: ["season", "game_id"], player_game: ["season", "player_id", "game_id"], player_season: ["season", "player_id"], spatial_cell: ["season", "cell_id"], player_game_spatial: ["season", "player_id","game_id","cell_id"], player_season_spatial:["season", "player_id","cell_id"] };
const foreignKeyDefinitions = { publication: [], season: [], player: ["season:season:season"], game: ["season:season:season"], player_game: ["game:season:season,game_id:game_id", "player:season:season,player_id:player_id"], player_season: ["player:season:season,player_id:player_id"], spatial_cell: ["season:season:season"], player_game_spatial: ["player_game:season:season,player_id:player_id,game_id:game_id", "spatial_cell:season:season,cell_id:cell_id"], player_season_spatial: ["player_season:season:season,player_id:player_id", "spatial_cell:season:season,cell_id:cell_id"] };

export interface PublicationReader {
  readonly metadata: PublicationSchema;
  readonly seasons: readonly SeasonEvidence[];
  readonly league: (season: Season, spatialIds?: readonly string[]) => Effect.Effect<LeagueResponse, Error | SqlError>;
  readonly player: (season: Season, playerId: string) => Effect.Effect<PlayerResponse | undefined, Error | SqlError>;
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
    if (JSON.stringify(version) !== '[{"user_version":4}]' || JSON.stringify(journal) !== '[{"journal_mode":"delete"}]') throw new Error("incompatible publication version or journal mode");
    const actual = tableList.filter((table) => !table.name.startsWith("sqlite_"));
    if (actual.length !== 9 || actual.some((table) => table.type !== "table" || table.strict !== 1 || !(table.name in tables))) throw new Error("publication requires exactly nine strict tables");
  });
  for (const table of Object.keys(tables)) {
    const columns = yield* sql.unsafe<{ name: string; type: string; notnull: number; pk: number; dflt_value: unknown }>(`PRAGMA table_info(${table})`);
    const foreignKeys = yield* sql.unsafe<{ id: number; seq: number; table: string; from: string; to: string; on_update: string; on_delete: string; match: string }>(`PRAGMA foreign_key_list(${table})`);
    yield* Effect.try(() => {
      if (JSON.stringify(columns.map((column) => column.name)) !== JSON.stringify(physicalColumns[table as keyof typeof tables])) throw new Error(`${table}: incompatible columns`);
      for (const column of columns) {
        const type = integerColumns.has(column.name) ? "INTEGER" : column.name === "for_per60" || column.name === "against_per60" || column.name.endsWith("_per60") || spatialRealColumns.includes(column.name) ? "REAL" : "TEXT";
        const key = table as keyof typeof tables;
        if (column.type !== type || column.notnull !== (nullableColumns.has(column.name) ? 0 : 1) || column.pk !== primaryKeys[key].indexOf(column.name) + 1 || column.dflt_value !== null) throw new Error(`${table}.${column.name}: incompatible physical column`);
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
    });
  }
  const metadataRows = yield* sql.unsafe("SELECT * FROM publication");
  const stored = yield* Effect.try(() => {
    if (metadataRows.length !== 1) throw new Error("publication requires one metadata row");
    return Schema.decodeUnknownSync(PublicationRow, strict)(metadataRows[0]);
  });
  const metadata = yield* Effect.try(() => Schema.decodeUnknownSync(PublicationSchema, strict)({
    publication_id: stored.publication_id, kind: stored.kind, purpose: stored.purpose,
    generated_at: stored.generated_at, population_version: stored.population_version, personal_population_version: stored.personal_population_version,
    spatial_population_version: stored.spatial_population_version, spatial_display_version: stored.spatial_display_version, git_commit: stored.producer_json.git_commit,
  }));
  const seasonInputs = yield* sql.unsafe("SELECT * FROM season ORDER BY season DESC");
  const seasons = yield* Effect.try(() => {
    if (seasonInputs.length === 0) throw new Error("publication requires a nonempty season catalog");
    return seasonInputs.map((input) => {
      const row = Schema.decodeUnknownSync(SeasonRow, strict)(input);
      if (metadata.purpose === "real" && row.source_implementations_json.length === 0) throw new Error("real season requires source implementation evidence");
      return Schema.decodeUnknownSync(SeasonEvidence, strict)({
        season: row.season, corpus_sha256: row.corpus_sha256, source_requested_min: row.source_requested_min,
        source_requested_max: row.source_requested_max, undated_sources: row.undated_sources, coverage: row.coverage_json, spatial_coverage: row.spatial_coverage_json,
      });
    });
  });
  const available_seasons = seasons.map((evidence) => evidence.season);
  yield* Effect.try(() => {
    const declared = ["20252026", "20242025", "20232024"];
    if (available_seasons.some((season) => !declared.includes(season)) || (metadata.purpose === "real" && JSON.stringify(available_seasons) !== JSON.stringify(declared))) throw new Error("publication season catalog differs from its purpose");
  });
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
  const readPlayers = (season: Season, playerId?: string) => Effect.gen(function* () {
    const rows = yield* sql.unsafe(`SELECT s.*, p.display_name, p.reported_position FROM player_season s JOIN player p USING(season,player_id) WHERE s.season=?${playerId === undefined ? "" : " AND s.player_id=?"} ORDER BY s.player_id`, playerId === undefined ? [season] : [season, playerId]);
    return yield* Effect.try(() => rows.map((input) => {
      const row = Schema.decodeUnknownSync(JoinedPlayer, strict)(input);
      return Schema.decodeUnknownSync(PlayerSummary, strict)({
        player_id: row.player_id, display_name: row.display_name, reported_position: row.reported_position,
        teams: row.teams_json, listed_games: row.listed_games, games_with_included_time: row.games_with_included_time,
        partial_games: row.partial_games, unavailable_games: row.unavailable_games, metrics: metrics(row), personal: personal(row),
      });
    }));
  });
  const readGames = (season: Season, playerId?: string) => Effect.gen(function* () {
    const rows = yield* sql.unsafe(`SELECT p.*, g.game_date, g.away_team_id, g.home_team_id, g.away_abbreviation, g.home_abbreviation FROM player_game p JOIN game g USING(season,game_id) WHERE p.season=?${playerId === undefined ? "" : " AND p.player_id=?"} ORDER BY g.game_date, g.game_id, p.player_id`, playerId === undefined ? [season] : [season, playerId]);
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
  for (const evidence of seasons) {
    const season = evidence.season, coverage = evidence.coverage;
    for (const [table, schema] of Object.entries({player: PlayerRow, game: GameRow, player_game: PlayerGameRow, player_season: PlayerSeasonRow})) {
      const rows = yield* sql.unsafe(`SELECT * FROM ${table} WHERE season=?`, [season]);
      yield* Effect.try(() => {
        for (const row of rows) {
          Schema.decodeUnknownSync(schema, strict)(row);
          if (table === "player") {
            const player = Schema.decodeUnknownSync(PlayerRow, strict)(row);
            for (const locator of [player.name_source_json, player.position_source_json]) {
              if (locator !== null && (locator.game_id.slice(0, 4) !== season.slice(0, 4) || locator.game_id.slice(4, 6) !== "02")) throw new Error("seasonal player source locator differs from its season");
            }
          }
        }
      });
    }
    const players = yield* readPlayers(season);
    yield* readGames(season);
    const gameInputs = yield* sql.unsafe("SELECT * FROM game WHERE season=?", [season]);
    const playerGameInputs = yield* sql.unsafe("SELECT * FROM player_game WHERE season=?", [season]);
    yield* Effect.try(() => {
      const games = gameInputs.map((row) => Schema.decodeUnknownSync(GameRow, strict)(row));
      const playerGames = playerGameInputs.map((row) => Schema.decodeUnknownSync(PlayerGameRow, strict)(row));
      if (coverage.inventory_games !== games.length || coverage.games_with_included_time !== games.filter((game) => game.included_seconds > 0).length ||
        coverage.partial_games !== games.filter((game) => game.coverage_status === "partial").length || coverage.unavailable_games !== games.filter((game) => game.coverage_status === "unavailable").length ||
        metadata.purpose === "real" && (games.length !== 1312 || !games.some((game) => game.included_seconds > 0))) throw new Error("season coverage differs from its physical games");
      const reasonCounts = new Map<string, number>();
      for (const game of games) for (const reason of game.reason_codes_json) reasonCounts.set(reason, (reasonCounts.get(reason) ?? 0) + 1);
      if (JSON.stringify(coverage.reason_game_counts) !== JSON.stringify([...reasonCounts].sort(([a],[b]) => a.localeCompare(b)).map(([code,games]) => ({code,games})))) throw new Error("season coverage reasons differ from physical games");
      for (const gap of coverage.unassigned_games) {
        const game = games.find((game) => game.game_id === gap.game_id);
        if (game === undefined || gap.date !== game.game_date || gap.away_team_id !== game.away_team_id || gap.home_team_id !== game.home_team_id ||
          game.reason_codes_json.some((reason) => !gap.reason_codes.includes(reason)) || gap.reason_codes.some((reason) => reason !== "roster_identity_unresolved" && !game.reason_codes_json.includes(reason))) throw new Error("unassigned game evidence differs from its physical game");
      }
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
    const missingSeasons = yield* sql.unsafe("SELECT player_id FROM player WHERE season=? EXCEPT SELECT player_id FROM player_season WHERE season=?", [season, season]);
    if (missingSeasons.length !== 0) return yield* Effect.fail(new Error("player missing season summary"));
    yield* validateSpatial(sql, season, evidence.spatial_coverage, coverage.games_with_unassigned_player_associations);
  }
  const league = (season: Season, ids?: readonly string[]) => Effect.gen(function* () {
    const evidence = seasons.find((evidence) => evidence.season === season);
    if (evidence === undefined) return yield* Effect.fail(new Error("reader requires a published season"));
    const players = yield* readPlayers(season);
    const spatial = yield* readSpatial(sql, season, evidence.spatial_coverage, ids);
    return yield* Effect.try(() => Schema.decodeUnknownSync(LeagueResponse, strict)({publication:metadata,available_seasons,season:evidence,players,spatial}));
  });
  return {
    metadata, seasons, league,
    player: (season: Season, playerId: string) => Effect.gen(function* () {
      const known = yield* sql.unsafe("SELECT 1 FROM player WHERE player_id=? LIMIT 1", [playerId]);
      if (known.length === 0) return undefined;
      const selected = yield* league(season, [playerId]);
      const games = yield* readGames(season, playerId);
      const history: Array<PlayerResponse["history"][number]> = [];
      for (const evidence of seasons) {
        const rows = evidence.season === season ? selected.players.filter((player) => player.player_id === playerId) : yield* readPlayers(evidence.season, playerId);
        history.push({season:evidence,player:rows[0] ?? null});
      }
      return yield* Effect.try(() => Schema.decodeUnknownSync(PlayerResponse, strict)({...selected,player_id:playerId,games,history}));
    }),
  } satisfies PublicationReader;
})).pipe(Layer.provide(SqliteClient.layer({ filename, readonly: true, disableWAL: true })));
