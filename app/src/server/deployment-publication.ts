import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Effect from "effect/Effect";
import * as Schema from "effect/Schema";
import { Deployment, DeploymentPeer, HockeyId, Season, type PlayerSummary } from "../shared/observed.js";

export const PlayerSeasonPair = Schema.Struct({
  season: Season, player_a: HockeyId, relation: Schema.Literals(["teammate", "opponent"]),
  player_b: HockeyId, shared_seconds: DeploymentPeer.fields.shared_seconds,
}).check(Schema.makeFilter((row) => row.player_a.length < row.player_b.length || row.player_a.length === row.player_b.length && row.player_a < row.player_b));
const strict = { onExcessProperty: "error" } as const;
const PeerRow = Schema.Struct({relation:PlayerSeasonPair.fields.relation,...DeploymentPeer.fields});

export const validateDeployment = (sql: SqliteClient, season: Season, players: readonly PlayerSummary[], physicalSeconds: bigint) => Effect.gen(function* () {
  const inputs = yield* sql.unsafe("SELECT * FROM player_season_pair WHERE season=?", [season]);
  yield* Effect.try(() => {
    const seconds = new Map(players.map((player) => [player.player_id, BigInt(player.metrics.included_seconds)]));
    const totals = new Map(players.map((player) => [player.player_id, {teammate:0n,opponent:0n}]));
    const combined = new Map<string, bigint>();
    const physicalTotals = {teammate:0n,opponent:0n};
    for (const input of inputs) {
      const row = Schema.decodeUnknownSync(PlayerSeasonPair, strict)(input);
      const a = totals.get(row.player_a), b = totals.get(row.player_b);
      if (row.season !== season || a === undefined || b === undefined) throw new Error("deployment pair identity is absent from its season");
      const shared = BigInt(row.shared_seconds);
      const key = `${row.player_a}:${row.player_b}`;
      const overlap = (combined.get(key) ?? 0n) + shared;
      if (overlap > seconds.get(row.player_a)! || overlap > seconds.get(row.player_b)!) throw new Error("combined deployment overlap exceeds included player time");
      combined.set(key, overlap);
      a[row.relation] += shared;
      b[row.relation] += shared;
      physicalTotals[row.relation] += shared;
    }
    if (physicalTotals.teammate !== 20n * physicalSeconds || physicalTotals.opponent !== 25n * physicalSeconds) throw new Error("deployment totals differ from physical included time");
    for (const [id, total] of totals) {
      if (total.teammate !== 4n * seconds.get(id)! || total.opponent !== 5n * seconds.get(id)!) throw new Error(`${id}: deployment totals differ from included player time`);
    }
  });
});

export const readDeployment = (sql: SqliteClient, season: Season, playerId: string) => Effect.gen(function* () {
  const inputs = yield* sql.unsafe(`SELECT relation, player_id, shared_seconds FROM (
    SELECT relation, player_b AS player_id, shared_seconds FROM player_season_pair WHERE season=? AND player_a=?
    UNION ALL
    SELECT relation, player_a AS player_id, shared_seconds FROM player_season_pair WHERE season=? AND player_b=?
  ) ORDER BY shared_seconds DESC, length(player_id), player_id COLLATE BINARY`, [season, playerId, season, playerId]);
  return yield* Effect.try(() => {
    const deployment: {teammates: DeploymentPeer[]; opponents: DeploymentPeer[]} = {teammates:[],opponents:[]};
    for (const input of inputs) {
      const {relation,...peer} = Schema.decodeUnknownSync(PeerRow, strict)(input);
      deployment[relation === "teammate" ? "teammates" : "opponents"].push(peer);
    }
    return Schema.decodeUnknownSync(Deployment, strict)(deployment);
  });
});
