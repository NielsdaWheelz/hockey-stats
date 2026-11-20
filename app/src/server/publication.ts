import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
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
} from "../shared/observed.js";
import { readObserved } from "./observed-publication.js";
import { ledgerReferenceCoverage } from "./ledger-publication.js";
import { readSpatial } from "./spatial-publication.js";
import {
  absent,
  decode,
  pending,
  parseObject,
  payloadFromRow,
  provided,
  readCatalogs,
  resultFromRow,
  type AnalysisIndexes,
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
  schema_version: Schema.Literal(12),
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
export const readPublicationMetadata = (sql: SqliteClient) =>
  Effect.gen(function* () {
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
        schema_version: 12,
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
    return { metadata, seasons, available_seasons, catalogs, prepared: stored.prepared_sha256 };
  });

export const makePublication = (
  sql: SqliteClient,
  { metadata, seasons, available_seasons, catalogs }: Effect.Success<ReturnType<typeof readPublicationMetadata>>,
  indexes: AnalysisIndexes,
): PublicationReader => {
  const analysis = {
    people: indexes.people,
    grids: indexes.grids,
    ledgerReferences: new Map(
      [...indexes.ledgerReferences].flatMap(([season, reference]) =>
        reference.availability === "provided" ? [[season, ledgerReferenceCoverage(reference.data)]] : []),
    ),
  };
  const observed = readObserved(sql);
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
  const pendingFamily = (season: Season, family: A.Family) => {
    const disposition = catalogs.families.find(row => row.season === season && row.family === family);
    if (!disposition) throw new Error(`${family}: required seasonal catalog entry missing`);
    return disposition.availability === "not_computed" ? pending(disposition.explanation!) : null;
  };
  const readSummary = (
    table: SummaryTable,
    season: Season,
    id: string,
    selectors: Readonly<Record<string, string>> = {},
  ) =>
    Effect.gen(function* () {
      const identity = person(season, id);
      if (!identity) throw new Error("readSummary requires a present person");
      const unavailable = pendingFamily(season, tableFamily(table, selectors, identity.kind));
      if (unavailable) return unavailable;
      const entries = Object.entries(selectors);
      const rows = yield* sql.unsafe<Record<string, unknown>>(
        `SELECT * FROM ${table} WHERE season=? AND player_id=?${entries.map(([key]) => ` AND ${key}=?`).join("")}`,
        [season, id, ...entries.map(([, value]) => value)],
      );
      if (rows.length !== 1)
        return yield* Effect.fail(
          new Error(`${table}: required selected row missing or ambiguous`),
        );
      return yield* Effect.try(() => resultFromRow(table, rows[0], identity.kind));
    });
  const ledgerPayload = `json_remove(payload_json,'$.evidence') AS payload_json,
    json_extract(payload_json,'$.evidence.annual_reference_id') AS annual_reference_id,
    json_extract(payload_json,'$.evidence.depth_position.group') AS depth_position_group`;
  const ledgerFromRow = (season: Season, row: Record<string, unknown>) => {
    const { method_id, availability, explanation, payload_json, annual_reference_id, depth_position_group } = row;
    if (availability === "not_computed")
      return decode(A.ValueLedgerSummaryResult, { availability, explanation, data: null });
    const reference = analysis.ledgerReferences.get(season);
    if (!reference) throw new Error("ledger annual coverage required");
    return decode(A.ValueLedgerSummaryResult, provided({
      ...parseObject(payload_json),
      method_id,
      annual_reference_id,
      depth_position_group,
      depth_reference_coverage: depth_position_group === "F" || depth_position_group === "D"
        ? reference[depth_position_group] : null,
    }));
  };
  const readLedgerSummary = (season: Season, id: string) =>
    Effect.gen(function* () {
      const unavailable = pendingFamily(season, "ledger");
      if (unavailable) return unavailable;
      const rows = yield* sql.unsafe<Record<string, unknown>>(`
        SELECT method_id, availability, explanation, ${ledgerPayload}
          FROM value_ledger WHERE season=? AND player_id=?`, [season,id]);
      if (rows.length !== 1)
        return yield* Effect.fail(new Error("ledger summary required"));
      return yield* Effect.try(() => ledgerFromRow(season, rows[0]));
    });
  const families = (
    season: Season,
    id: string,
    kind: "skater" | "goalie",
  ) =>
    Effect.gen(function* () {
      if (person(season, id) === null)
        return { kind, ...absent("player is absent from selected season") };
      const collection = (table: SummaryTable, strengths: readonly string[]) =>
        Effect.gen(function* () {
          const unavailable = pendingFamily(season, tableFamily(table, {}, kind));
          if (unavailable) return unavailable;
          const rows = [];
          for (const strength of strengths) {
            const result = yield* readSummary(table, season, id, { strength });
            rows.push({ strength, result: table === "goalie_observed"
              ? A.projectOverviewResult(A.GoalieObservedSummaryResult, result) : result });
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
      const current = (yield* observed.readPlayers(season, id)).find(
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
        ledger: yield* readLedgerSummary(season, id),
      };
      return yield* Effect.try(() => decode(A.PlayerFamilies, data));
    });
  // all expressions and strength sets below come from declared overview fields.
  // sqlite discards large evidence before any JSON reaches the application.
  const overviewPayload = (fields: Readonly<Record<string, unknown>>) =>
    `CASE WHEN payload_json IS NOT NULL THEN json_object(${Object.keys(fields)
      .filter(key => key !== "method_id")
      .map(key => `'${key}',json_extract(payload_json,'$.${key}')`).join(",")})
      END AS payload_json`;
  const readOverviewRows = <T>(
    season: Season,
    table: SummaryTable,
    kind: A.Person["kind"],
    decodeRow: (row: Record<string, unknown>) => T,
    projection = "payload_json",
    strengths: readonly string[] = [],
  ) =>
    Effect.gen(function* () {
      const unavailable = pendingFamily(season, tableFamily(table, {}, kind));
      if (unavailable) return () => unavailable;
      const rows = yield* sql.unsafe<Record<string, unknown>>(`
        SELECT player_id, ${strengths.length ? "strength" : "'' AS strength"},
               method_id, availability, explanation, ${projection}
          FROM ${table} WHERE season=?${strengths.length
            ? ` AND strength IN (${strengths.map(() => "?").join(",")})` : ""}`,
        [season, ...strengths]);
      return yield* Effect.try(() => {
        const byIdentity = new Map<string, T>();
        for (const row of rows) {
          const key = `${row.player_id}:${row.strength}`;
          if (byIdentity.has(key)) throw new Error(`${table}: duplicate overview row for ${key}`);
          byIdentity.set(key, decodeRow(row));
        }
        return (id: string, strength = "") => {
          const result = byIdentity.get(`${id}:${strength}`);
          if (result === undefined)
            throw new Error(`${table}: required overview row missing for ${id} ${strength}`);
          return result;
        };
      });
    });

  const readSkaterOverview = (season: Season, people: readonly A.Person[]) =>
    Effect.gen(function* () {
      const observedRows = new Map((yield* observed.readPlayers(season)).map(row => [row.player_id, row]));
      const usage = yield* readOverviewRows(season, "skater_descriptive", "skater",
        row => payloadFromRow(A.ReportedUsageResult, row),
        "json_extract(payload_json,'$.reported_usage') AS payload_json");
      const ledger = yield* readOverviewRows(season, "value_ledger", "skater",
        row => ledgerFromRow(season, row), ledgerPayload);
      const spatial = yield* readOverviewRows(season, "skater_spatial", "skater",
        row => resultFromRow("skater_spatial", row), "payload_json", ["5v5", "pp", "pk"]);
      const execution = yield* readOverviewRows(season, "skater_execution", "skater",
        row => payloadFromRow(A.ExecutionSummaryResult, row), overviewPayload(A.ExecutionSummary.fields), ["5v5"]);
      const shootiness = yield* readOverviewRows(season, "skater_shootiness", "skater",
        row => payloadFromRow(A.ShootinessSummaryResult, row), overviewPayload(A.ShootinessSummary.fields), ["5v5"]);
      const penalties = yield* readOverviewRows(season, "skater_penalties", "skater",
        row => payloadFromRow(A.PenaltySummaryResult, row), overviewPayload(A.PenaltySummary.fields));
      const territory = yield* readOverviewRows(season, "skater_territory", "skater",
        row => payloadFromRow(A.TerritorySummaryResult, row), overviewPayload(A.TerritorySummary.fields));
      const context = yield* readOverviewRows(season, "skater_context", "skater",
        row => resultFromRow("skater_context", row));
      return yield* Effect.try(() => people.map(person => {
        const id = person.player_id, summary = observedRows.get(id);
        return { person, result: provided({
          reported_usage: usage(id),
          ledger: ledger(id),
          spatial: { five_on_five: spatial(id, "5v5"), pp: spatial(id, "pp"), pk: spatial(id, "pk") },
          execution: execution(id, "5v5"),
          shootiness: shootiness(id, "5v5"),
          penalties: penalties(id),
          territory: territory(id),
          observed: summary ? provided(summary) : pending("no selected-season observed skater record"),
          context: context(id),
        }) };
      }));
    });

  const readGoalieOverview = (season: Season, people: readonly A.Person[]) =>
    Effect.gen(function* () {
      const model = yield* readOverviewRows(season, "goalie_result", "goalie",
        row => payloadFromRow(A.GoalieSummaryResult, row),
        overviewPayload(A.GoalieSummary.fields), ["ev", "pk"]);
      const actual = yield* readOverviewRows(season, "goalie_observed", "goalie",
        row => payloadFromRow(A.GoalieObservedSummaryResult, row),
        overviewPayload(A.GoalieObservedSummary.fields), ["ev", "pk"]);
      return yield* Effect.try(() => people.map(person => {
        const id = person.player_id, ev = actual(id, "ev");
        return { person, result: provided({
          reported_usage: ev.availability === "provided" ? provided(ev.data.reported_usage) : ev,
          goalie: { ev: model(id, "ev"), pk: model(id, "pk") },
          observed: { ev, pk: actual(id, "pk") },
        }) };
      }));
    });

  const league = (selection: A.LeagueSelection) =>
    Effect.gen(function* () {
      const { season, kind, family, strength } = selection;
      const base = yield* Effect.try(() => envelope(season));
      const people = [...analysis.people.values()].filter(person => person.season === season && person.kind === kind);
      let players: unknown;
      if (family === "overview") {
        players = kind === "goalie" ? yield* readGoalieOverview(season, people) : yield* readSkaterOverview(season, people);
      } else if (family === "observed") {
        const observedRows = new Map((yield* observed.readPlayers(season)).map(row => [row.player_id, row]));
        players = people.flatMap(person => {
          const result = observedRows.get(person.player_id);
          return result ? [{ person, result: provided(result) }] : [];
        });
      } else {
        const rows = [];
        for (const person of people) {
          const result = yield* readSummary(
            family === "goalie" ? "goalie_result" : (`skater_${family}` as SummaryTable),
            season,
            person.player_id,
            strength === null ? {} : { strength },
          );
          rows.push({ person, result });
        }
        players = rows;
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
  };
};
