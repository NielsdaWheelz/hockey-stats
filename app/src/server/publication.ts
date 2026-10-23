import * as SqliteClient from "@effect/sql-sqlite-node/SqliteClient";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import type { SqlError } from "effect/sql/SqlError";
import * as A from "../shared/player-analysis.js";
import {
  Count,
  Coverage,
  GitCommit,
  Season,
  SeasonEvidence,
  SpatialCoverage,
  type PlayerSummary,
} from "../shared/observed.js";
import { validateObserved } from "./observed-publication.js";
import { readSpatial } from "./spatial-publication.js";
import {
  absent,
  decode,
  pending,
  provided,
  readCatalogs,
  resultFromRow,
  validateAnalysis,
  validatePhysical,
  tableFamily,
  type SummaryTable,
} from "./analysis-publication.js";
import { readEvidence, readContext, readMaps } from "./selected-publication.js";
const Implementation = Schema.Struct({
  git_commit: GitCommit,
  git_dirty: Schema.NullOr(Schema.Boolean),
  python_version: A.Text,
});
const Producer = Schema.Struct({
  ...Implementation.fields,
  sqlite_version: Schema.String,
  spatial_consumed_fields: Schema.Tuple([
    Schema.Literal("interpreted.events.reported_x"),
    Schema.Literal("interpreted.events.reported_y"),
    Schema.Literal("interpreted.events.home_team_defending_side"),
    Schema.Literal("reconstruction.events.attacking_x"),
    Schema.Literal("reconstruction.events.attacking_y"),
    Schema.Literal("reconstruction.events.coordinate_status"),
  ]),
});
const PublicationRow = Schema.Struct({
  prepared_sha256: Schema.NullOr(A.Digest),
  id: Schema.Literal(1),
  schema_version: Schema.Literal(7),
  kind: Schema.Literal("player_analysis"),
  publication_id: A.Publication.fields.publication_id,
  purpose: A.Purpose,
  game_type: Schema.Literal(2),
  generated_at: A.Publication.fields.generated_at,
  population_version: A.Publication.fields.population_version,
  personal_population_version: A.Publication.fields.personal_population_version,
  spatial_population_version: A.Publication.fields.spatial_population_version,
  spatial_display_version: A.Publication.fields.spatial_display_version,
  producer_json: Schema.fromJsonString(Producer),
});
const SeasonRow = Schema.Struct({
  season: Season,
  corpus_sha256: SeasonEvidence.fields.corpus_sha256,
  source_requested_min: SeasonEvidence.fields.source_requested_min,
  source_requested_max: SeasonEvidence.fields.source_requested_max,
  undated_sources: Count,
  coverage_json: Schema.fromJsonString(Coverage),
  source_implementations_json: Schema.fromJsonString(Schema.Array(Implementation)),
  spatial_coverage_json: Schema.fromJsonString(SpatialCoverage),
});
type Failure = Error | SqlError;
export interface PublicationReader {
  readonly metadata: A.Publication;
  readonly seasons: readonly SeasonEvidence[];
  readonly league: (selection: A.LeagueSelection) => Effect.Effect<A.LeagueResponse, Failure>;
  readonly player: (
    season: Season,
    id: string,
  ) => Effect.Effect<A.PlayerResponse | undefined, Failure>;
  readonly maps: (selection: A.MapSelection) => Effect.Effect<A.MapsResponse, Failure>;
  readonly evidence: (selection: A.EvidenceSelection) => Effect.Effect<A.EvidenceResponse, Failure>;
  readonly context: (selection: A.ContextSelection) => Effect.Effect<A.ContextResponse, Failure>;
}
export const Publication = Context.Service<PublicationReader>("hockey-stats/Publication");
export const publicationLayer = (filename: string) =>
  Layer.effect(
    Publication,
    Effect.gen(function* () {
      const sql = yield* SqliteClient.SqliteClient;
      yield* validatePhysical(sql);
      const metadataRows = yield* sql.unsafe<Record<string, unknown>>("SELECT * FROM publication");
      const stored = yield* Effect.try(() => {
        if (metadataRows.length !== 1) throw new Error("publication requires one metadata row");
        return decode(PublicationRow, metadataRows[0]);
      });
      const inputs = yield* sql.unsafe<Record<string, unknown>>(
        "SELECT * FROM season ORDER BY season DESC",
      );
      const seasons = yield* Effect.try(() =>
        inputs.map((input) => {
          const row = decode(SeasonRow, input);
          if (stored.purpose === "real" && row.source_implementations_json.length === 0)
            throw new Error("real season requires source implementation evidence");
          return decode(SeasonEvidence, {
            season: row.season,
            corpus_sha256: row.corpus_sha256,
            source_requested_min: row.source_requested_min,
            source_requested_max: row.source_requested_max,
            undated_sources: row.undated_sources,
            coverage: row.coverage_json,
            spatial_coverage: row.spatial_coverage_json,
          });
        }),
      );
      const available_seasons = seasons.map((row) => row.season);
      yield* Effect.try(() => {
        const declared = ["20252026", "20242025", "20232024"];
        if (
          seasons.length === 0 ||
          available_seasons.some((season) => !declared.includes(season)) ||
          (stored.purpose === "real" &&
            JSON.stringify(available_seasons) !== JSON.stringify(declared))
        )
          throw new Error("publication season catalog differs from its purpose");
      });
      const catalogs = yield* readCatalogs(
        sql,
        stored.purpose,
        available_seasons,
        stored.prepared_sha256,
      );
      const metadata = yield* Effect.try(() =>
        decode(A.Publication, {
          publication_id: stored.publication_id,
          schema_version: 7,
          kind: stored.kind,
          purpose: stored.purpose,
          generated_at: stored.generated_at,
          population_version: stored.population_version,
          personal_population_version: stored.personal_population_version,
          spatial_population_version: stored.spatial_population_version,
          spatial_display_version: stored.spatial_display_version,
          git_commit: stored.producer_json.git_commit,
          families: catalogs.families,
        }),
      );
      const analysis = yield* validateAnalysis(sql, catalogs);
      const observed = yield* validateObserved(sql, seasons, stored.purpose);
      const envelope = (season: Season) => {
        const evidence = seasons.find((row) => row.season === season);
        if (evidence === undefined)
          throw {
            _tag: "SeasonNotFound",
            message: `season ${season} is not published`,
            available_seasons,
          } satisfies A.ApiError;
        return {
          publication: metadata,
          available_seasons,
          season: evidence,
          sources: catalogs.sources,
          methods: catalogs.methods,
          supports: catalogs.supports,
        };
      };
      const person = (season: Season, id: string) => analysis.people.get(`${season}:${id}`) ?? null;
      const known = (id: string) => {
        const identity = [...analysis.people.values()].find((row) => row.player_id === id);
        if (identity === undefined)
          throw {
            _tag: "PlayerNotFound",
            message: "player not found in this publication",
          } satisfies A.ApiError;
        return identity;
      };
      const readSummary = (
        table: SummaryTable,
        season: Season,
        id: string,
        selectors: Readonly<Record<string, string>> = {},
      ) =>
        Effect.gen(function* () {
          if (person(season, id) === null) throw new Error("readSummary requires a present person");
          const family = tableFamily(table, selectors, person(season, id)!.kind);
          const disposition = catalogs.families.find(
            (row) => row.season === season && row.family === family,
          );
          if (disposition?.availability === "not_computed")
            return pending(disposition.explanation!);
          const entries = Object.entries(selectors);
          const rows = yield* sql.unsafe<Record<string, unknown>>(
            `SELECT * FROM ${table} WHERE season=? AND player_id=?${entries.map(([key]) => ` AND ${key}=?`).join("")}`,
            [season, id, ...entries.map(([, value]) => value)],
          );
          if (rows.length !== 1)
            return yield* Effect.fail(
              new Error(`${table}: required selected row missing or ambiguous`),
            );
          return yield* Effect.try(() => resultFromRow(table, rows[0]));
        });
      const families = (
        season: Season,
        id: string,
        kind: "skater" | "goalie",
        observedRows?: readonly PlayerSummary[],
      ) =>
        Effect.gen(function* () {
          if (person(season, id) === null)
            return { kind, ...absent("player is absent from selected season") };
          const collection = (table: SummaryTable, strengths: readonly string[]) =>
            Effect.gen(function* () {
              if (person(season, id) === null)
                throw new Error("family collection requires a present person");
              const family = table.startsWith("goalie_") ? "goalie" : table.slice(7),
                disposition = catalogs.families.find(
                  (row) => row.season === season && row.family === family,
                )!;
              if (disposition.availability === "not_computed")
                return pending(disposition.explanation!);
              const rows = [];
              for (const strength of strengths) {
                let result = yield* readSummary(table, season, id, { strength });
                if (table === "goalie_observed" && result.availability === "provided") {
                  const full = decode(A.GoalieObserved, result.data),
                    { games, ...summary } = full;
                  result = provided(summary) as typeof result;
                }
                rows.push({ strength, result });
              }
              return provided(rows);
            });
          if (kind === "goalie") {
            const goalie = yield* collection("goalie_result", A.GoalieStrength.literals),
              goalie_observed = yield* collection("goalie_observed", A.EvidenceStrength.literals);
            return yield* Effect.try(() =>
              decode(A.GoalieFamilies, { kind, goalie, goalie_observed }),
            );
          }
          const current = (observedRows ?? (yield* observed.readPlayers(season, id))).find(
            (row) => row.player_id === id,
          );
          const data = {
            kind,
            observed:
              current === undefined
                ? pending("no selected-season observed skater record")
                : provided(current),
            descriptive: yield* readSummary("skater_descriptive", season, id),
            context: yield* readSummary("skater_context", season, id),
            microstats: yield* readSummary("skater_microstats", season, id),
            spatial: yield* collection("skater_spatial", A.SpatialStrength.literals),
            execution: yield* collection("skater_execution", A.ExecutionStrength.literals),
            shootiness: yield* collection("skater_shootiness", A.ExecutionStrength.literals),
            penalties: yield* readSummary("skater_penalties", season, id),
            territory: yield* readSummary("skater_territory", season, id),
            ledger: yield* readSummary("value_ledger", season, id),
          };
          return yield* Effect.try(() => decode(A.PlayerFamilies, data));
        });
      const overview = (value: A.PlayerFamilies) => {
        if ("availability" in value)
          throw new Error("league overview requires selected-season identity");
        if (value.kind === "goalie") {
          const select = (collection: typeof value.goalie, strength: string) =>
            collection.availability === "not_computed"
              ? collection
              : collection.data.find((row) => row.strength === strength)!.result;
          const ev =
            value.goalie_observed.availability === "provided"
              ? value.goalie_observed.data.find((row) => row.strength === "ev")!.result
              : value.goalie_observed;
          return provided({
            reported_usage: ev.availability === "provided" ? provided(ev.data.reported_usage) : ev,
            goalie: { ev: select(value.goalie, "ev"), pk: select(value.goalie, "pk") },
            observed: {
              ev,
              pk:
                value.goalie_observed.availability === "provided"
                  ? value.goalie_observed.data.find((row) => row.strength === "pk")!.result
                  : value.goalie_observed,
            },
          });
        }
        const select = (
          collection: typeof value.spatial | typeof value.execution | typeof value.shootiness,
          strength: string,
        ) =>
          collection.availability === "not_computed"
            ? collection
            : collection.data.find((row) => row.strength === strength)!.result;
        return provided({
          reported_usage:
            value.descriptive.availability === "provided"
              ? provided(value.descriptive.data.reported_usage)
              : value.descriptive,
          ledger: value.ledger,
          spatial: {
            five_on_five: select(value.spatial, "5v5"),
            pp: select(value.spatial, "pp"),
            pk: select(value.spatial, "pk"),
          },
          execution: select(value.execution, "5v5"),
          shootiness: select(value.shootiness, "5v5"),
          penalties: value.penalties,
          territory: value.territory,
          observed: value.observed,
          context: value.context,
        });
      };
      const league = (selection: A.LeagueSelection) =>
        Effect.gen(function* () {
          const { season, kind, family, strength } = selection;
          const base = yield* Effect.try(() => envelope(season));
          const observedRows =
            family === "observed" || family === "overview"
              ? yield* observed.readPlayers(season)
              : [];
          const players: unknown[] = [];
          for (const identity of analysis.people.values()) {
            if (
              identity.season !== season ||
              identity.kind !== kind ||
              (family === "observed" &&
                !observedRows.some((row) => row.player_id === identity.player_id))
            )
              continue;
            const result =
              family === "overview"
                ? overview(yield* families(season, identity.player_id, kind, observedRows))
                : family === "observed"
                  ? provided(observedRows.find((row) => row.player_id === identity.player_id)!)
                  : yield* readSummary(
                      family === "goalie" ? "goalie_result" : (`skater_${family}` as SummaryTable),
                      season,
                      identity.player_id,
                      strength === null ? {} : { strength },
                    );
            players.push({ person: identity, result });
          }
          return yield* Effect.try(() =>
            decode(A.LeagueResponse, { ...base, family, kind, strength, players }),
          );
        });
      return {
        metadata,
        seasons,
        league,
        player: (season: Season, id: string) =>
          Effect.gen(function* () {
            const base = yield* Effect.try(() => envelope(season));
            const identity = [...analysis.people.values()].find((row) => row.player_id === id);
            if (identity === undefined) return undefined;
            const selected = person(season, id),
              history: A.PlayerResponse["history"][number][] = [];
            for (const evidence of [...seasons].reverse())
              history.push({
                season: evidence,
                person: person(evidence.season, id),
                families: yield* families(evidence.season, id, identity.kind),
              });
            const selectedFamilies = history.find((row) => row.season.season === season)!.families;
            const hasObserved =
              !("availability" in selectedFamilies) &&
              selectedFamilies.kind === "skater" &&
              selectedFamilies.observed.availability === "provided";
            const observed_games = hasObserved ? yield* observed.readGames(season, id) : [];
            const deployment = hasObserved ? yield* observed.readDeployment(season, id) : null;
            return yield* Effect.try(() =>
              decode(A.PlayerResponse, {
                ...base,
                player_id: id,
                kind: identity.kind,
                person: selected,
                families: selectedFamilies,
                observed_games,
                deployment,
                history,
              }),
            );
          }),
        maps: (selection: A.MapSelection) =>
          readMaps(selection, {
            envelope,
            person,
            known,
            readSummary,
            grids: analysis.grids,
            readSpatial: (season: Season, ids: readonly string[]) =>
              readSpatial(sql, season, envelope(season).season.spatial_coverage, ids),
          }),
        evidence: (selection: A.EvidenceSelection) =>
          readEvidence(sql, selection, { envelope, person, known, readSummary }),
        context: (selection: A.ContextSelection) =>
          readContext(sql, selection, { envelope, person, known, readSummary }),
      } satisfies PublicationReader;
    }),
  ).pipe(Layer.provide(SqliteClient.layer({ filename, readonly: true, disableWAL: true })));
