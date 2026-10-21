import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Effect from "effect/Effect";
import * as Schema from "effect/Schema";
import { createHash } from "node:crypto";
import {
  Count, CoverageStatus, GameId, HockeyId, Season, PlayerSpatialCell, SpatialCell, SpatialCoverage,
  SpatialMetrics, SpatialReasonCodes, SpatialSelection,
} from "../shared/observed.js";

export const spatialColumns = {
  spatial_included_seconds: Count, spatial_known_excluded_seconds: Count,
  spatial_unblocked_for: Schema.NullOr(Count), spatial_unblocked_against: Schema.NullOr(Count),
  spatial_for_per60: SpatialMetrics.fields.for_per60, spatial_against_per60: SpatialMetrics.fields.against_per60,
  spatial_coverage_status: CoverageStatus, spatial_reason_codes_json: Schema.fromJsonString(SpatialReasonCodes),
};
export const spatialGameColumns = {
  spatial_included_seconds: Count, spatial_known_excluded_seconds: Count,
  spatial_away_unblocked: Schema.NullOr(Count), spatial_home_unblocked: Schema.NullOr(Count),
  spatial_coverage_status: CoverageStatus, spatial_reason_codes_json: Schema.fromJsonString(SpatialReasonCodes),
};
export const PlayerGameSpatialRow = Schema.Struct({
  season: Season, player_id: HockeyId, game_id: GameId, cell_id: Count, for_count: Count, against_count: Count,
}).check(Schema.makeFilter((row) => row.for_count + row.against_count > 0));
export const PlayerSeasonSpatialRow = Schema.Struct({ season: Season, player_id: HockeyId, ...PlayerSpatialCell.fields });
export const spatialTables = { spatial_cell: Schema.Struct({season: Season, ...SpatialCell.fields}), player_game_spatial: PlayerGameSpatialRow, player_season_spatial: PlayerSeasonSpatialRow };
export const spatialIntegerColumns = ["cell_id", "league_count", "for_count", "against_count", "spatial_included_seconds", "spatial_known_excluded_seconds", "spatial_unblocked_for", "spatial_unblocked_against", "spatial_away_unblocked", "spatial_home_unblocked"];
export const spatialNullableColumns = ["league_count", "league_raw_per60", "league_density", "spatial_unblocked_for", "spatial_unblocked_against", "spatial_for_per60", "spatial_against_per60", "spatial_away_unblocked", "spatial_home_unblocked"];
export const spatialRealColumns = ["x_min", "x_max", "y_min", "y_max", "center_x", "center_y", "area_sqft", "league_density", "for_density", "against_density", "for_difference", "against_difference"];
const strict = { onExcessProperty: "error" } as const;
type SpatialRow = { [K in keyof typeof spatialColumns]: typeof spatialColumns[K]["Type"] };
export const spatialMetrics = (row: SpatialRow): SpatialMetrics => ({
  included_seconds: row.spatial_included_seconds, known_excluded_seconds: row.spatial_known_excluded_seconds,
  unblocked_for: row.spatial_unblocked_for, unblocked_against: row.spatial_unblocked_against,
  for_per60: row.spatial_for_per60, against_per60: row.spatial_against_per60,
  coverage_status: row.spatial_coverage_status, reason_codes: row.spatial_reason_codes_json,
});
const close = (actual: number, expected: number, label: string) => {
  if (Math.abs(actual - expected) > 1e-10 + 1e-10 * Math.abs(expected)) throw new Error(`${label}: spatial arithmetic differs`);
};
const support = (row: SpatialRow & { included_seconds: number; known_excluded_seconds: number; reason_codes_json: readonly string[] }) => {
  const value = Schema.decodeUnknownSync(SpatialMetrics, strict)(spatialMetrics(row));
  if (value.included_seconds > row.included_seconds || value.known_excluded_seconds !== row.known_excluded_seconds + row.included_seconds - value.included_seconds || row.reason_codes_json.some((code) => code !== "no_5v5_exposure" && !value.reason_codes.includes(code as typeof value.reason_codes[number]))) throw new Error("spatial support differs from matched on-ice support");
  if (value.included_seconds > 0) {
    close(value.for_per60!, 3600 * value.unblocked_for! / value.included_seconds, "for rate");
    close(value.against_per60!, 3600 * value.unblocked_against! / value.included_seconds, "against rate");
  }
  return value;
};
const ScalarRow = Schema.Struct({
  included_seconds: Count, known_excluded_seconds: Count, reason_codes_json: Schema.fromJsonString(Schema.Array(Schema.String)), ...spatialColumns,
});
const SeasonRow = Schema.Struct({ player_id: HockeyId, ...ScalarRow.fields });
const GameRow = Schema.Struct({
  game_id: GameId, away_team_id: HockeyId, home_team_id: HockeyId,
  included_seconds: Count, known_excluded_seconds: Count, reason_codes_json: Schema.fromJsonString(Schema.Array(Schema.String)), ...spatialGameColumns,
});
const PlayerGameRow = Schema.Struct({ player_id: HockeyId, team_id: HockeyId, ...ScalarRow.fields });
const selectScalars = Object.keys(ScalarRow.fields).join(",");

export const validateSpatial = (sql: SqliteClient, selectedSeason: Season, leagueSupport: SpatialCoverage, unassignedGames: number) => Effect.gen(function* () {
  const cellInputs = yield* sql.unsafe(`SELECT ${Object.keys(SpatialCell.fields).join(",")} FROM spatial_cell WHERE season=? ORDER BY cell_id`, [selectedSeason]);
  const cells = yield* Effect.try(() => cellInputs.map((row) => Schema.decodeUnknownSync(SpatialCell, strict)(row)));
  yield* Effect.try(() => {
    if (cells.length !== 668) throw new Error("spatial geometry requires 668 cells");
    const geometry = cells.map(({league_count, league_raw_per60, league_density, ...cell}) => Object.values(cell).map((value) => value.toFixed(8)).join(",")).join("\n");
    // frozen geometry identity for rect5_gaussian10_v1; numerical generation stays in python.
    if (createHash("sha256").update(geometry).digest("hex") !== "f92426d41ebfb482313c31c758871fd4f4ac3fca008ee097ae8bed6f8129207c") throw new Error("spatial geometry differs from its display version");
    const total = cells.reduce((sum, cell) => sum + (cell.league_count ?? 0), 0);
    if (leagueSupport.unblocked_attempts !== null && total !== leagueSupport.unblocked_attempts) throw new Error("spatial league counts differ");
    for (const cell of cells) {
      if (leagueSupport.included_seconds > 0) {
        if (cell.league_count === null || cell.league_raw_per60 === null || cell.league_density === null) throw new Error("positive league time requires every cell");
        close(cell.league_raw_per60, 3600 * cell.league_count / (2 * leagueSupport.included_seconds), "league cell rate");
      } else if (cell.league_count !== (leagueSupport.coverage_status === "complete" ? 0 : null) || cell.league_raw_per60 !== null || cell.league_density !== null) throw new Error("zero league time requires null rates/maps");
    }
    if (leagueSupport.included_seconds > 0) {
      close(leagueSupport.unblocked_per60!, 3600 * leagueSupport.unblocked_attempts! / (2 * leagueSupport.included_seconds), "league total rate");
      close(cells.reduce((sum, cell) => sum + cell.league_density! * cell.area_sqft / 100, 0), leagueSupport.unblocked_per60!, "league density mass");
    }
  });
  const gameInputs = yield* sql.unsafe(`SELECT ${Object.keys(GameRow.fields).join(",")} FROM game WHERE season=? ORDER BY game_id`, [selectedSeason]);
  const games = yield* Effect.try(() => gameInputs.map((row) => Schema.decodeUnknownSync(GameRow, strict)(row)));
  const leagueCounts = new Map<number, number>();
  const gameReasons = new Map<string, number>();
  let totalSeconds = 0, totalExcluded = 0, totalAttempts = 0;
  for (const game of games) {
    const playerInputs = yield* sql.unsafe(`SELECT player_id,team_id,${selectScalars} FROM player_game WHERE season=? AND game_id=? ORDER BY player_id`, [selectedSeason, game.game_id]);
    const sparseInputs = yield* sql.unsafe("SELECT * FROM player_game_spatial WHERE season=? AND game_id=? ORDER BY player_id,cell_id", [selectedSeason, game.game_id]);
    yield* Effect.try(() => {
      const metrics = support({...game, spatial_unblocked_for: game.spatial_away_unblocked, spatial_unblocked_against: game.spatial_home_unblocked,
        spatial_for_per60: game.spatial_included_seconds > 0 ? 3600 * game.spatial_away_unblocked! / game.spatial_included_seconds : null,
        spatial_against_per60: game.spatial_included_seconds > 0 ? 3600 * game.spatial_home_unblocked! / game.spatial_included_seconds : null});
      const players = playerInputs.map((row) => Schema.decodeUnknownSync(PlayerGameRow, strict)(row));
      const sparse = sparseInputs.map((row) => Schema.decodeUnknownSync(PlayerGameSpatialRow, strict)(row));
      const counts = new Map<string, [number, number]>();
      const teams = new Map(players.map((row) => [row.player_id, row.team_id]));
      const teamCells = new Map<string, [number, number]>();
      for (const row of sparse) {
        if (row.season !== selectedSeason || row.game_id !== game.game_id || !teams.has(row.player_id)) throw new Error("spatial sparse identity differs");
        const count = counts.get(row.player_id) ?? [0, 0];
        count[0] += row.for_count; count[1] += row.against_count; counts.set(row.player_id, count);
        const key = `${teams.get(row.player_id)}:${row.cell_id}`;
        const team = teamCells.get(key) ?? [0, 0];
        team[0] += row.for_count; team[1] += row.against_count; teamCells.set(key, team);
      }
      let seconds = 0;
      for (const player of players) {
        const value = support(player);
        const count = counts.get(player.player_id) ?? [0, 0];
        if (count[0] !== (value.unblocked_for ?? 0) || count[1] !== (value.unblocked_against ?? 0)) throw new Error("spatial game cells differ from scalar counts");
        seconds += value.included_seconds;
      }
      if (seconds !== 10 * metrics.included_seconds) throw new Error("spatial player seconds differ from physical time");
      let away = 0, home = 0;
      for (const cell of cells) {
        const a = teamCells.get(`${game.away_team_id}:${cell.cell_id}`) ?? [0, 0];
        const h = teamCells.get(`${game.home_team_id}:${cell.cell_id}`) ?? [0, 0];
        if (a[0] !== h[1] || h[0] !== a[1] || a[0] % 5 !== 0 || h[0] % 5 !== 0) throw new Error("spatial team/cell conservation failed");
        away += a[0] / 5; home += h[0] / 5;
        leagueCounts.set(cell.cell_id, (leagueCounts.get(cell.cell_id) ?? 0) + (a[0] + h[0]) / 5);
      }
      if (away !== (game.spatial_away_unblocked ?? 0) || home !== (game.spatial_home_unblocked ?? 0)) throw new Error("spatial physical team counts differ");
      totalSeconds += metrics.included_seconds; totalExcluded += metrics.known_excluded_seconds; totalAttempts += away + home;
      for (const reason of metrics.reason_codes) gameReasons.set(reason, (gameReasons.get(reason) ?? 0) + 1);
    });
  }
  yield* Effect.try(() => {
    const reasons = [...gameReasons.keys()].filter((code) => code !== "no_spatial_5v5_exposure");
    if (totalSeconds === 0 && reasons.length === 0) reasons.push("no_spatial_5v5_exposure");
    if (leagueSupport.included_seconds !== totalSeconds || leagueSupport.known_excluded_seconds !== totalExcluded || leagueSupport.unblocked_attempts !== (totalSeconds > 0 || leagueSupport.coverage_status === "complete" ? totalAttempts : null) ||
      leagueSupport.inventory_games !== games.length || leagueSupport.games_with_included_time !== games.filter((g) => g.spatial_included_seconds > 0).length ||
      leagueSupport.partial_games !== games.filter((g) => g.spatial_coverage_status === "partial").length || leagueSupport.unavailable_games !== games.filter((g) => g.spatial_coverage_status === "unavailable").length ||
      JSON.stringify(leagueSupport.reason_codes) !== JSON.stringify(reasons.sort()) || JSON.stringify(leagueSupport.reason_game_counts) !== JSON.stringify([...gameReasons].sort(([a],[b]) => a.localeCompare(b)).map(([code,games]) => ({code,games})))) throw new Error("spatial league coverage differs from games");
    for (const cell of cells) if (cell.league_count !== null && cell.league_count !== (leagueCounts.get(cell.cell_id) ?? 0)) throw new Error("spatial league cell differs from player counts");
  });
  const seasonInputs = yield* sql.unsafe(`SELECT player_id,${selectScalars} FROM player_season WHERE season=? ORDER BY player_id`, [selectedSeason]);
  const seasons = yield* Effect.try(() => seasonInputs.map((row) => Schema.decodeUnknownSync(SeasonRow, strict)(row)));
  for (const season of seasons) {
    const denseInputs = yield* sql.unsafe("SELECT * FROM player_season_spatial WHERE season=? AND player_id=? ORDER BY cell_id", [selectedSeason, season.player_id]);
    const reduced = yield* sql.unsafe<{cell_id:number; for_count:number; against_count:number}>("SELECT cell_id,SUM(for_count) AS for_count,SUM(against_count) AS against_count FROM player_game_spatial WHERE season=? AND player_id=? GROUP BY cell_id ORDER BY cell_id", [selectedSeason, season.player_id]);
    const contributions = yield* sql.unsafe(`SELECT ${selectScalars} FROM player_game WHERE season=? AND player_id=?`, [selectedSeason, season.player_id]);
    yield* Effect.try(() => {
      const metrics = support(season);
      const rows = denseInputs.map((row) => Schema.decodeUnknownSync(PlayerSeasonSpatialRow, strict)(row));
      const sparse = new Map(reduced.map((row) => [row.cell_id, row]));
      const values = contributions.map((row) => support(Schema.decodeUnknownSync(ScalarRow, strict)(row)));
      for (const key of ["included_seconds", "known_excluded_seconds", "unblocked_for", "unblocked_against"] as const) {
        if (metrics[key] !== null && metrics[key] !== values.reduce((sum, value) => sum + (value[key] ?? 0), 0)) throw new Error("spatial season scalar reduction failed");
      }
      const reasons = new Set<SpatialMetrics["reason_codes"][number]>(values.flatMap((row) => row.reason_codes).filter((code) => code !== "no_spatial_5v5_exposure"));
      if (unassignedGames > 0) reasons.add("unassigned_player_games");
      if (metrics.included_seconds === 0 && reasons.size === 0) reasons.add("no_spatial_5v5_exposure");
      if (JSON.stringify([...reasons].sort()) !== JSON.stringify(metrics.reason_codes)) throw new Error("spatial season reasons differ");
      if (metrics.included_seconds === 0) {
        if (rows.length !== 0 || reduced.length !== 0) throw new Error("zero-time player has spatial cells");
        return;
      }
      if (rows.length !== cells.length) throw new Error("positive-time player requires exact dense cell set");
      let forCount = 0, againstCount = 0, forMass = 0, againstMass = 0, forDifference = 0, againstDifference = 0;
      for (const [index,row] of rows.entries()) {
        const cell = cells[index], count = sparse.get(row.cell_id);
        if (row.season !== selectedSeason || row.player_id !== season.player_id || row.cell_id !== cell.cell_id || row.for_count !== (count?.for_count ?? 0) || row.against_count !== (count?.against_count ?? 0)) throw new Error("spatial dense identity/count reduction differs");
        if (cell.league_density === null) throw new Error("player map requires positive league reference");
        close(row.for_raw_per60, 3600 * row.for_count / metrics.included_seconds, "raw for");
        close(row.against_raw_per60, 3600 * row.against_count / metrics.included_seconds, "raw against");
        close(row.for_difference, row.for_density - cell.league_density, "for difference");
        close(row.against_difference, row.against_density - cell.league_density, "against difference");
        forCount += row.for_count; againstCount += row.against_count;
        forMass += row.for_density * cell.area_sqft / 100; againstMass += row.against_density * cell.area_sqft / 100;
        forDifference += row.for_difference * cell.area_sqft / 100; againstDifference += row.against_difference * cell.area_sqft / 100;
      }
      if (forCount !== metrics.unblocked_for || againstCount !== metrics.unblocked_against) throw new Error("spatial dense totals differ");
      close(forMass, metrics.for_per60!, "for density mass"); close(againstMass, metrics.against_per60!, "against density mass");
      close(forDifference, metrics.for_per60! - leagueSupport.unblocked_per60!, "for difference mass"); close(againstDifference, metrics.against_per60! - leagueSupport.unblocked_per60!, "against difference mass");
    });
  }
});

const definition: SpatialSelection["definition"] = { population_version: "matched_unblocked_locations_v1", display_version: "rect5_gaussian10_v1", sigma_ft: 10,
  rink: {length_ft:200,width_ft:85,corner_radius_ft:28,goal_x:89}, units:"attempts_per60_per100sqft",orientation:"shooting_team_positive_x" };
export const readSpatial = (sql: SqliteClient, season: Season, leagueSupport: SpatialCoverage, ids?: readonly string[]) => Effect.gen(function* () {
  if (ids === undefined) return null;
  const cellInputs = yield* sql.unsafe(`SELECT ${Object.keys(SpatialCell.fields).join(",")} FROM spatial_cell WHERE season=? ORDER BY cell_id`, [season]);
  const cells = yield* Effect.try(() => cellInputs.map((row) => Schema.decodeUnknownSync(SpatialCell, strict)(row)));
  const players: Array<SpatialSelection["players"][number]> = [];
  for (const player_id of ids) {
    const scalarInputs = yield* sql.unsafe(`SELECT ${selectScalars} FROM player_season WHERE season=? AND player_id=?`, [season, player_id]);
    if (scalarInputs.length === 0) { players.push({player_id,data:null}); continue; }
    const metrics = yield* Effect.try(() => spatialMetrics(Schema.decodeUnknownSync(ScalarRow, strict)(scalarInputs[0])));
    const inputs = metrics.included_seconds > 0 ? yield* sql.unsafe(`SELECT ${Object.keys(PlayerSpatialCell.fields).join(",")} FROM player_season_spatial WHERE season=? AND player_id=? ORDER BY cell_id`, [season, player_id]) : null;
    const selected = yield* Effect.try(() => inputs === null ? null : inputs.map((row) => Schema.decodeUnknownSync(PlayerSpatialCell, strict)(row)));
    players.push({player_id,data:{metrics,cells:selected}});
  }
  return yield* Effect.try(() => Schema.decodeUnknownSync(SpatialSelection, strict)({definition,league_support:leagueSupport,cells,players}));
});
