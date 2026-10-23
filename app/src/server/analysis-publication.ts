import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Effect from "effect/Effect";
import * as Schema from "effect/Schema";
import { createHash } from "node:crypto";
import * as A from "../shared/player-analysis.js";
import { Season } from "../shared/observed.js";
import { forEachRow, strictJson } from "./sql-rows.js";
import { physicalSchema } from "./physical-schema.js";

export const decode = <S extends Schema.ConstraintDecoder<unknown, never>>(
  schema: S,
  input: unknown,
): S["Type"] => {
  if (input !== null && typeof input === "object")
    for (const [key, value] of Object.entries(input))
      if (key.endsWith("_json") && typeof value === "string") strictJson(value);
  return Schema.decodeUnknownSync(schema, A.strict)(input);
};
export const close = A.close;
export const per60 = A.per60;
export const provided = <T>(data: T) => ({
  availability: "provided" as const,
  explanation: null,
  data,
});
export const pending = (explanation: string) => ({
  availability: "not_computed" as const,
  explanation,
  data: null,
});
export const absent = (explanation: string) => ({
  availability: "absent" as const,
  explanation,
  data: null,
});
export const summarySchemas = {
  skater_descriptive: A.SkaterDescriptiveResult,
  skater_context: A.SkaterContextResult,
  skater_microstats: A.SkaterMicrostatsResult,
  skater_spatial: A.SkaterSpatialResult,
  skater_execution: A.SkaterExecutionResult,
  skater_shootiness: A.SkaterShootinessResult,
  skater_penalties: A.SkaterPenaltiesResult,
  skater_territory: A.SkaterTerritoryResult,
  goalie_result: A.GoalieResultEnvelope,
  goalie_observed: A.GoalieObservedResult,
  goalie_evidence_map: A.GoalieEvidenceMapResult,
  goalie_danger: A.GoalieDangerResult,
  value_ledger: A.ValueLedgerResult,
  analysis_map: A.AnalysisMapResult,
  execution_breakdown: A.ExecutionBreakdownResult,
  adjustment_decomposition: A.AdjustmentDecompositionResult,
};
export type SummaryTable = keyof typeof summarySchemas;
export const tableFamily = (
  table: SummaryTable,
  row: Record<string, unknown>,
  kind: string,
): A.Family => {
  if (table === "analysis_map")
    return row.map_kind === "goalie_stopping"
      ? "goalie"
      : ["finishing", "setting"].includes(String(row.map_kind))
        ? "execution"
        : ["ice_won", "ice_lost"].includes(String(row.map_kind))
          ? "territory"
          : "spatial";
  if (table === "execution_breakdown") return kind === "goalie" ? "goalie" : "execution";
  if (table === "adjustment_decomposition") return "spatial";
  if (table === "value_ledger") return "ledger";
  if (table.startsWith("goalie_")) return "goalie";
  if (table === "skater_context") return "descriptive";
  return table.slice(7) as A.Family;
};
export const parseObject = (value: unknown): Record<string, unknown> => {
  if (typeof value !== "string") throw new Error("stored JSON must be text");
  const parsed: unknown = strictJson(value);
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed))
    throw new Error("stored payload must be an object");
  return parsed as Record<string, unknown>;
};
export const resultFromRow = <T extends SummaryTable>(
  table: T,
  row: Record<string, unknown>,
): (typeof summarySchemas)[T]["Type"] => {
  let data: Record<string, unknown> | null = null;
  if (row.payload_json !== null) {
    data = parseObject(row.payload_json);
    if ("method_id" in data) throw new Error("method identity must have one stored owner");
    if (row.method_id !== null) data = { ...data, method_id: row.method_id };
  }
  return decode(summarySchemas[table], {
    availability: row.availability,
    explanation: row.explanation,
    data,
  });
};
export const factFromRow = (row: Record<string, unknown>) => {
  const { payload_json, ...columns } = row;
  const payload = parseObject(payload_json);
  if (Object.keys(payload).some((key) => key in columns))
    throw new Error("payload duplicates a physical field");
  return { ...columns, ...payload };
};
export const personFromRow = (row: Record<string, unknown>) =>
  decode(A.Person, {
    season: row.season,
    player_id: row.player_id,
    kind: row.kind,
    display_name: row.display_name,
    reported_position: row.reported_position,
    teams: strictJson(String(row.teams_json)),
    source: strictJson(String(row.source_json)),
    birth_date: row.birth_date,
    age_as_of: row.age_as_of,
    age_years: row.age_years,
    height_cm: row.height_cm,
    handedness: row.handedness,
    sweater_numbers: strictJson(String(row.sweater_numbers_json)),
    identity_support: strictJson(String(row.identity_support_json)),
  });

export const validatePhysical = (sql: SqliteClient) =>
  Effect.gen(function* () {
    const integrity = yield* sql.unsafe<Record<string, unknown>>("PRAGMA integrity_check"),
      foreign = yield* sql.unsafe<Record<string, unknown>>("PRAGMA foreign_key_check");
    const version = yield* sql.unsafe<Record<string, unknown>>("PRAGMA user_version"),
      journal = yield* sql.unsafe<Record<string, unknown>>("PRAGMA journal_mode");
    const tables = yield* sql.unsafe<{ name: string; type: string; strict: number; wr: number }>(
      "PRAGMA table_list",
    );
    yield* Effect.try(() => {
      if (JSON.stringify(integrity) !== '[{"integrity_check":"ok"}]' || foreign.length !== 0)
        throw new Error("publication integrity or foreign-key check failed");
      if (JSON.stringify(version) !== '[{"user_version":7}]')
        throw new Error("incompatible publication version; schema 7 is required");
      if (JSON.stringify(journal) !== '[{"journal_mode":"delete"}]')
        throw new Error("publication requires delete journal mode");
      const actual = tables.filter((table) => !table.name.startsWith("sqlite_"));
      if (
        actual.length !== Object.keys(physicalSchema).length ||
        actual.some(
          (table) =>
            table.type !== "table" ||
            table.strict !== 1 ||
            table.wr !== 0 ||
            !(table.name in physicalSchema),
        )
      )
        throw new Error("publication requires the fixed strict schema-7 tables");
    });
    for (const [table, expected] of Object.entries(physicalSchema)) {
      const columns = yield* sql.unsafe<{
        name: string;
        type: string;
        notnull: number;
        pk: number;
        dflt_value: unknown;
      }>(`PRAGMA table_info(${table})`);
      const foreign = yield* sql.unsafe<{
        id: number;
        seq: number;
        table: string;
        from: string;
        to: string;
        on_update: string;
        on_delete: string;
        match: string;
      }>(`PRAGMA foreign_key_list(${table})`);
      yield* Effect.try(() => {
        if (
          JSON.stringify(
            columns.map(({ name, type, notnull, pk }) => ({ name, type, notnull, pk })),
          ) !== JSON.stringify(expected.columns) ||
          columns.some((column) => column.dflt_value !== null)
        )
          throw new Error(`${table}: incompatible physical columns`);
        const groups = new Map<number, typeof foreign>();
        for (const key of foreign) groups.set(key.id, [...(groups.get(key.id) ?? []), key]);
        const definitions = [...groups.values()]
          .map(
            (rows) =>
              `${rows[0].table}:${[...rows]
                .sort((a, b) => a.seq - b.seq)
                .map((row) => `${row.from}:${row.to}`)
                .join(",")}`,
          )
          .sort();
        if (
          JSON.stringify(definitions) !== JSON.stringify(expected.foreignKeys) ||
          foreign.some(
            (key) =>
              key.on_update !== "NO ACTION" ||
              key.on_delete !== "NO ACTION" ||
              key.match !== "NONE",
          )
        )
          throw new Error(`${table}: incompatible foreign keys`);
      });
    }
    const indexes = yield* sql.unsafe<{
      name: string;
      unique: number;
      origin: string;
      partial: number;
    }>("PRAGMA index_list(player_season_pair)");
    const columns = yield* sql.unsafe<{ name: string; desc: number; coll: string; key: number }>(
      "PRAGMA index_xinfo(player_season_pair_b)",
    );
    yield* Effect.try(() => {
      const index = indexes.find((row) => row.name === "player_season_pair_b"),
        keys = columns.filter((row) => row.key === 1);
      if (
        index === undefined ||
        index.unique !== 0 ||
        index.origin !== "c" ||
        index.partial !== 0 ||
        JSON.stringify(keys.map((row) => row.name)) !==
          '["season","player_b","relation","player_a"]' ||
        keys.some((row) => row.desc !== 0 || row.coll !== "BINARY")
      )
        throw new Error("deployment counterpart index differs");
    });
  });

const canonical = (value: unknown): unknown =>
  Array.isArray(value)
    ? value.map(canonical)
    : value !== null && typeof value === "object"
      ? Object.fromEntries(
          Object.entries(value)
            .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
            .map(([key, value]) => [key, canonical(value)]),
        )
      : value;
export const readCatalogs = (
  sql: SqliteClient,
  purpose: "real" | "fixture",
  seasons: readonly Season[],
  prepared: string | null,
) =>
  Effect.gen(function* () {
    const sources: Record<string, A.Source> = Object.create(null),
      methods: Record<string, A.Method> = Object.create(null),
      supports: Record<string, A.SupportDefinition> = Object.create(null);
    const checkChronology = (method: A.Method, season: string) => {
      if (method.fit_seasons.some((fitSeason) => fitSeason > season))
        throw new Error("method fit seasons are later than the displayed season");
      if (method.training_cutoff !== null && method.training_cutoff > `${season.slice(4)}-06-30`)
        throw new Error("method training cutoff is later than the displayed season");
    };
    yield* forEachRow(sql, "analysis_source", (row) =>
      Effect.try(() => {
        const source = decode(A.Source, factFromRow(row));
        if (source.purpose !== purpose) throw new Error("source purpose differs from publication");
        sources[source.source_id] = source;
      }),
    );
    yield* forEachRow(sql, "analysis_method", (row) =>
      Effect.try(() => {
        const method = decode(A.Method, factFromRow(row));
        if (
          method.purpose !== purpose ||
          createHash("sha256")
            .update(JSON.stringify(canonical(method.inputs)))
            .digest("hex") !== method.input_sha256
        )
          throw new Error("method purpose or composite input identity differs");
        if (
          !method.inputs.some((input) => input.role === "prepared") ||
          method.inputs.some((input) => input.role === "prepared" && input.sha256 !== prepared)
        )
          throw new Error("method prepared identity differs from publication base");
        if (
          method.inputs.some(
            (input) =>
              (input.role === "annual_state" || input.role === "predecessor") &&
              input.seasons.some((season) => !method.fit_seasons.includes(season)),
          )
        )
          throw new Error("annual state or predecessor seasons are outside method fit seasons");
        methods[method.method_id] = method;
      }),
    );
    yield* forEachRow(sql, "analysis_support", (row) =>
      Effect.try(() => {
        const support = decode(A.SupportDefinition, factFromRow(row));
        if (
          !seasons.includes(support.season) ||
          support.source_ids.some((id) => sources[id] === undefined) ||
          support.method_ids.some((id) => methods[id] === undefined)
        )
          throw new Error("support metadata is dangling");
        for (const id of support.method_ids) checkChronology(methods[id], support.season);
        supports[support.support_id] = support;
      }),
    );
    const inputs = yield* sql.unsafe<Record<string, unknown>>(
      "SELECT * FROM analysis_family ORDER BY season,family",
    );
    const families = yield* Effect.try(() =>
      inputs.map((row) => decode(A.FamilyAvailability, row)),
    );
    yield* Effect.try(() => {
      if (prepared === null && families.some((row) => row.availability === "provided"))
        throw new Error("provided analytical families require prepared identity");
      if (
        families.length !== seasons.length * A.Family.literals.length ||
        seasons.some((season) =>
          A.Family.literals.some(
            (family) => !families.some((row) => row.season === season && row.family === family),
          ),
        )
      )
        throw new Error("family disposition inventory differs");
    });
    const checkReferences = (input: unknown, season?: string, inheritedMethod?: string | null) => {
      if (Array.isArray(input)) {
        for (const value of input) checkReferences(value, season, inheritedMethod);
        return;
      }
      if (input === null || typeof input !== "object") return;
      const value = input as Record<string, unknown>;
      const methodId = Object.hasOwn(value, "method_id") ? value.method_id : inheritedMethod;
      const referencedMethods = [
        methodId,
        ...(value.kind === "method" ? [value.id] : []),
        ...(Array.isArray(value.method_ids) ? value.method_ids : []),
      ];
      if (season !== undefined)
        for (const id of referencedMethods) {
          if (typeof id !== "string") continue;
          const method = methods[id];
          if (method === undefined) throw new Error("stored method does not resolve");
          checkChronology(method, season);
        }
      if (Array.isArray(value.prior_seasons)) {
        const priors = value.prior_seasons as string[];
        if (season === undefined || priors.some((prior) => prior >= season))
          throw new Error("support prior season is not strictly historical");
        if (priors.length > 0) {
          const method = typeof methodId === "string" ? methods[methodId] : undefined;
          if (method === undefined)
            throw new Error("support prior seasons lack a containing method");
          const inputSeasons = new Set(method.inputs.flatMap((input) => input.seasons));
          if (
            priors.some(
              (prior) =>
                !method.fit_seasons.includes(prior as Season) || !inputSeasons.has(prior as Season),
            )
          )
            throw new Error("support prior seasons are not bound to method inputs and fit seasons");
        }
      }
      if (
        (value.kind === "source" || value.kind === "method") &&
        typeof value.id === "string" &&
        (value.kind === "source" ? sources[value.id] : methods[value.id]) === undefined
      )
        throw new Error("stored reference does not resolve");
      if (typeof value.method_id === "string" && methods[value.method_id] === undefined)
        throw new Error("stored method does not resolve");
      if (typeof value.support_id === "string") {
        const support = supports[value.support_id];
        if (
          support === undefined ||
          (season !== undefined && support.season !== season) ||
          (typeof value.population === "string" && value.population !== support.population_id)
        )
          throw new Error("stored support does not match its season/population");
      }
      if (
        Array.isArray(value.source_ids) &&
        value.source_ids.some((id) => typeof id !== "string" || sources[id] === undefined)
      )
        throw new Error("source list does not resolve");
      if (
        Array.isArray(value.method_ids) &&
        value.method_ids.some((id) => typeof id !== "string" || methods[id] === undefined)
      )
        throw new Error("method list does not resolve");
      if (typeof value.method_id === "string") {
        const method = methods[value.method_id]!;
        const hasEstimate = (input: unknown): boolean =>
          Array.isArray(input)
            ? input.some(hasEstimate)
            : input !== null && typeof input === "object"
              ? ("uncertainty" in input &&
                  "value" in input &&
                  (input as { value: unknown }).value !== null) ||
                Object.values(input).some(hasEstimate)
              : false;
        const numericalMap =
          Array.isArray(value.cells) ||
          Array.isArray(value.native_cells) ||
          Array.isArray(value.attempt_counts);
        const paired =
          typeof value.attempts === "number" && typeof value.expected_goals === "number";
        if (paired && method.family !== "goalie")
          throw new Error("paired goalie evidence method family differs");
        if (
          (method.design_sha256 === null || method.training_cutoff === null) &&
          (hasEstimate(value) || numericalMap || (paired && Number(value.attempts) > 0))
        )
          throw new Error("available fitted output lacks design/cutoff identity");
      }
      for (const field of Object.values(value))
        checkReferences(field, season, methodId as string | null | undefined);
    };
    return { sources, methods, supports, families, checkReferences };
  });

const validateGoalieStates = (
  rows: readonly { state: typeof A.ActualState.Type }[],
  strength: string,
) => {
  // goalie selectors name the defending team; source attempts name the attacking team.
  for (const { state } of rows) {
    const ownStrength = `${state.defending_skaters}v${state.attacking_skaters}`;
    const allowed =
      strength === "ev"
        ? ["5v5", "4v4", "3v3"]
        : strength === "pk"
          ? ["4v5", "3v5", "3v4"]
          : [strength];
    if (
      !state.defending_goalie_present ||
      (strength !== "covered_all" &&
        (!state.attacking_goalie_present || !allowed.includes(ownStrength)))
    )
      throw new Error("goalie evidence actual state conflicts with selector");
  }
};

export const validateAnalysis = (
  sql: SqliteClient,
  catalogs: Effect.Success<ReturnType<typeof readCatalogs>>,
) =>
  Effect.gen(function* () {
    const people = new Map<string, A.Person>();
    yield* forEachRow(sql, "person", (row) =>
      Effect.try(() => {
        for (const field of ["name_source_json", "position_source_json"])
          if (row[field] !== null)
            decode(
              Schema.Struct({
                game_id: A.AttemptKey.fields.game_id,
                source_index: A.AttemptKey.fields.source_index,
              }),
              strictJson(String(row[field])),
            );
        const person = personFromRow(row);
        catalogs.checkReferences(person, person.season);
        people.set(`${person.season}:${person.player_id}`, person);
      }),
    );
    const present = (season: unknown, id: unknown, kind?: string) => {
      const person = people.get(`${season}:${id}`);
      if (person === undefined || (kind !== undefined && person.kind !== kind))
        throw new Error("analytical subject kind/identity differs");
      return person;
    };
    for (const table of Object.keys(summarySchemas) as SummaryTable[]) {
      yield* forEachRow(sql, table, (row) =>
        Effect.try(() => {
          decode(Season, row.season);
          decode(A.Id, row.player_id);
          const person = present(
            row.season,
            row.player_id,
            table.startsWith("skater_") ||
              table === "value_ledger" ||
              table === "adjustment_decomposition"
              ? "skater"
              : table.startsWith("goalie_")
                ? "goalie"
                : undefined,
          );
          const family = tableFamily(table, row, person.kind);
          if (
            !catalogs.families.some(
              (entry) =>
                entry.season === row.season &&
                entry.family === family &&
                entry.availability === "provided",
            )
          )
            throw new Error("row supplied for a pending family");
          if ("strength" in row)
            decode(
              table.startsWith("goalie_")
                ? table === "goalie_result"
                  ? A.GoalieStrength
                  : A.EvidenceStrength
                : table === "skater_spatial" || table === "adjustment_decomposition"
                  ? A.SpatialStrength
                  : table === "analysis_map"
                    ? Schema.Union([A.SpatialStrength, A.GoalieStrength])
                    : person.kind === "goalie"
                      ? A.GoalieStrength
                      : A.ExecutionStrength,
              row.strength,
            );
          if (table === "analysis_map") {
            decode(A.MapKind, row.map_kind);
            decode(A.MapView, row.view);
            if ((row.map_kind === "goalie_stopping") !== (person.kind === "goalie"))
              throw new Error("map person kind differs");
            const offense = ["offense_attempts", "offense_xg"].includes(String(row.map_kind)),
              defense = ["defense_attempts", "defense_xg"].includes(String(row.map_kind));
            if (
              (offense && ["4v5", "3v5", "3v4", "pk"].includes(String(row.strength))) ||
              (defense && ["5v4", "5v3", "4v3", "pp"].includes(String(row.strength))) ||
              (!offense && !defense && row.view !== "effect")
            )
              throw new Error("map role/view differs from its strength");
          }
          if (table === "goalie_evidence_map" || table === "goalie_danger")
            decode(A.EvidencePopulation, row.population);
          if (table === "goalie_evidence_map") decode(A.EvidenceType, row.type);
          if (table === "execution_breakdown") {
            if (row.kind === "shot_type") decode(A.ShotType, row.stratum);
            else if (row.kind === "danger")
              decode(Schema.Literals(["<.05", "[.05,.15)", ">=.15"]), row.stratum);
            else throw new Error("unknown breakdown kind");
          }
          if (table === "adjustment_decomposition") decode(A.AdjustmentTarget, row.target);
          const result = resultFromRow(table, row);
          if (table === "skater_spatial" && result.availability === "provided") {
            const value = result.data as typeof A.SkaterSpatial.Type;
            const expected =
              row.strength === "pp"
                ? ["5v4", "5v3", "4v3"]
                : row.strength === "pk"
                  ? ["4v5", "3v5", "3v4"]
                  : [String(row.strength)];
            if (
              JSON.stringify(value.state_weights.map((entry) => entry.strength).sort()) !==
              JSON.stringify(expected.sort())
            )
              throw new Error("spatial state-weight selectors differ");
          }
          if (
            result.availability === "provided" &&
            (table === "goalie_observed" ||
              table === "goalie_evidence_map" ||
              table === "goalie_danger")
          ) {
            const value = result.data as
              | typeof A.GoalieObserved.Type
              | typeof A.GoalieEvidenceMap.Type
              | typeof A.GoalieDanger.Type;
            validateGoalieStates(value.actual_states, String(row.strength));
            if (table === "goalie_observed")
              for (const game of (value as typeof A.GoalieObserved.Type).games)
                validateGoalieStates(game.actual_states, String(row.strength));
          }
          catalogs.checkReferences(result, String(row.season));
          if (
            result.availability === "provided" &&
            family !== "descriptive" &&
            family !== "microstats" &&
            table !== "goalie_observed" &&
            row.method_id === null
          )
            throw new Error("modeled result requires method identity");
          if (
            typeof row.method_id === "string" &&
            catalogs.methods[row.method_id].family !== family
          )
            throw new Error("row method family differs");
        }),
      );
    }
    for (const [table, schema] of Object.entries({
      attempt_setter: A.AttemptSetter,
      attempt_execution_share: A.AttemptExecutionShare,
      dressed_game: A.DressedGame,
      context_coverage: A.ContextCoverage,
    })) {
      yield* forEachRow(sql, table, (row) =>
        Effect.try(() => {
          const value = decode(schema, factFromRow(row));
          catalogs.checkReferences(value, String(row.season));
          const owner =
            table === "attempt_setter" || table === "attempt_execution_share"
              ? "execution"
              : "evidence";
          if (
            !catalogs.families.some(
              (entry) =>
                entry.season === row.season &&
                entry.family === owner &&
                entry.availability === "provided",
            )
          )
            throw new Error("fact supplied for pending family");
          if (table === "dressed_game") present(row.season, row.player_id);
          if (table === "context_coverage") present(row.season, row.player_id, "skater");
          if (
            table === "attempt_setter" &&
            row.candidate_id !== "none" &&
            row.candidate_id !== "unknown"
          )
            present(row.season, row.candidate_id, "skater");
          if (
            table === "attempt_execution_share" &&
            !["none", "unknown", "coaching_context"].includes(String(row.recipient_id))
          )
            present(row.season, row.recipient_id, row.group === "goalie" ? "goalie" : "skater");
        }),
      );
    }
    yield* forEachRow(sql, "attempt_fact", (row) =>
      Effect.try(() => {
        const { strength, ...fact } = factFromRow(row),
          value = decode(A.ValuedAttemptFact, fact);
        catalogs.checkReferences(value, value.season);
        if (
          !catalogs.families.some(
            (entry) =>
              entry.season === row.season &&
              entry.family === "evidence" &&
              entry.availability === "provided",
          )
        )
          throw new Error("source attempt supplied for pending evidence");
        if (catalogs.supports[value.support_id].population_id !== "source_supported_attempts")
          throw new Error("attempt support population differs");
        if (
          value.method_id === null &&
          [
            value.actor_all_attempt_opportunity,
            value.neutral_all_attempt_opportunity,
            value.actor_unblocked_goal_probability,
            value.actor_on_net_goal_probability,
            value.neutral_goalie_on_net_goal_probability,
          ].some((estimate) => estimate.value !== null)
        )
          throw new Error("available event model value lacks method identity");
        if (value.method_id !== null && catalogs.methods[value.method_id].family !== "execution")
          throw new Error("event model method family differs");
        if (value.shooter_id !== null) present(value.season, value.shooter_id);
        if (value.goalie_id !== null) present(value.season, value.goalie_id, "goalie");
        if (value.method_id !== null) {
          const inapplicable = (estimate: A.Estimate) =>
            estimate.value === null && estimate.unavailable_reason === "not_applicable";
          if (
            ((value.outcome === "miss" || value.outcome === "block") &&
              (!inapplicable(value.actor_on_net_goal_probability) ||
                !inapplicable(value.neutral_goalie_on_net_goal_probability))) ||
            (value.outcome === "block" && !inapplicable(value.actor_unblocked_goal_probability))
          )
            throw new Error("event values conflict with observed conditional-stage applicability");
        }
        const state = value.actual_state,
          expected =
            state !== null && state.attacking_goalie_present && state.defending_goalie_present
              ? `${state.attacking_skaters}v${state.defending_skaters}`
              : null;
        if (strength !== expected) throw new Error("attempt strength differs from actual state");
      }),
    );
    for (const [table, schema] of Object.entries({
      interval_fact: A.IntervalFact,
      interval_player: A.IntervalPlayer,
      interval_location: A.IntervalLocation,
    })) {
      yield* forEachRow(sql, table, (row) =>
        Effect.try(() => {
          const value = decode(schema, row);
          catalogs.checkReferences(value, String(row.season));
          if (
            !catalogs.families.some(
              (entry) =>
                entry.season === row.season &&
                entry.family === "evidence" &&
                entry.availability === "provided",
            )
          )
            throw new Error("interval supplied for pending evidence");
          if (table === "interval_player") present(row.season, row.player_id, "skater");
        }),
      );
    }
    const gridRows = yield* sql.unsafe<Record<string, unknown>>(
      "SELECT * FROM analysis_grid ORDER BY grid_id",
    );
    const grids = yield* Effect.try(() =>
      gridRows.map((row) => decode(A.AnalysisGrid, factFromRow(row))),
    );
    yield* Effect.try(() => {
      if (grids.length !== 2 || new Set(grids.map((row) => row.kind)).size !== 2)
        throw new Error("both fixed grids are required");
    });
    yield* validateRequiredRows(sql, people, catalogs.families);
    yield* validateCrossRecords(sql, grids);
    yield* validateRepeatedFacts(sql);
    return { people, grids };
  });

const mapKinds = (family: A.Family) =>
  family === "spatial"
    ? ["offense_attempts", "defense_attempts", "offense_xg", "defense_xg"]
    : family === "execution"
      ? ["finishing", "setting"]
      : family === "territory"
        ? ["ice_won", "ice_lost"]
        : family === "goalie"
          ? ["goalie_stopping"]
          : [];
const requiredSelectors = (
  table: SummaryTable,
  family: A.Family,
): readonly Record<string, string>[] => {
  if (table === "analysis_map") {
    const rows: Record<string, string>[] = [];
    for (const map_kind of mapKinds(family))
      for (const strength of family === "spatial"
        ? A.SpatialStrength.literals
        : family === "execution"
          ? A.ExecutionStrength.literals
          : family === "goalie"
            ? A.GoalieStrength.literals
            : ["5v5"]) {
        if (
          (map_kind.startsWith("offense_") && ["4v5", "3v5", "3v4", "pk"].includes(strength)) ||
          (map_kind.startsWith("defense_") && ["5v4", "5v3", "4v3", "pp"].includes(strength))
        )
          continue;
        for (const view of family === "spatial" ? ["effect", "complete"] : ["effect"])
          rows.push({ map_kind, strength, view });
      }
    return rows;
  }
  if (table === "execution_breakdown")
    return (family === "goalie" ? A.GoalieStrength.literals : A.ExecutionStrength.literals).flatMap(
      (strength) => [
        ...A.ShotType.literals.map((stratum) => ({ strength, kind: "shot_type", stratum })),
        ...["<.05", "[.05,.15)", ">=.15"].map((stratum) => ({ strength, kind: "danger", stratum })),
      ],
    );
  if (table === "adjustment_decomposition")
    return A.SpatialStrength.literals.flatMap((strength) =>
      A.AdjustmentTarget.literals
        .filter(
          (target) =>
            strength === "5v5" ||
            (["5v4", "5v3", "4v3", "pp"].includes(strength)
              ? target.startsWith("for_")
              : target.startsWith("against_")),
        )
        .map((target) => ({ strength, target })),
    );
  if (table === "goalie_evidence_map" || table === "goalie_danger")
    return A.EvidenceStrength.literals.flatMap((strength) =>
      A.EvidencePopulation.literals.flatMap((population) =>
        table === "goalie_evidence_map"
          ? A.EvidenceType.literals.map((type) => ({ strength, population, type }))
          : [{ strength, population }],
      ),
    );
  if (table === "skater_spatial")
    return A.SpatialStrength.literals.map((strength) => ({ strength }));
  if (table === "skater_execution" || table === "skater_shootiness")
    return A.ExecutionStrength.literals.map((strength) => ({ strength }));
  if (table === "goalie_result" || table === "goalie_observed")
    return (
      table === "goalie_result" ? A.GoalieStrength.literals : A.EvidenceStrength.literals
    ).map((strength) => ({ strength }));
  return [{}];
};
const familyTables: Readonly<Record<A.Family, readonly SummaryTable[]>> = {
  descriptive: ["skater_descriptive", "skater_context"],
  microstats: ["skater_microstats"],
  spatial: ["skater_spatial", "analysis_map", "adjustment_decomposition"],
  execution: ["skater_execution", "analysis_map", "execution_breakdown"],
  shootiness: ["skater_shootiness"],
  penalties: ["skater_penalties"],
  territory: ["skater_territory", "analysis_map"],
  goalie: [
    "goalie_result",
    "goalie_observed",
    "goalie_evidence_map",
    "goalie_danger",
    "analysis_map",
    "execution_breakdown",
  ],
  ledger: ["value_ledger"],
  evidence: [],
};
const selectorKey = (value: Readonly<Record<string, unknown>>, keys: readonly string[]) =>
  JSON.stringify(keys.map((key) => value[key]));
export const validateRequiredRows = (
  sql: SqliteClient,
  people: ReadonlyMap<string, A.Person>,
  families: readonly (typeof A.FamilyAvailability.Type)[],
) =>
  Effect.gen(function* () {
    for (const disposition of families) {
      if (disposition.availability !== "provided") continue;
      for (const person of people.values()) {
        if (
          person.season !== disposition.season ||
          (person.kind === "goalie") !== (disposition.family === "goalie")
        )
          continue;
        for (const table of familyTables[disposition.family]) {
          const expected = requiredSelectors(table, disposition.family),
            keys = Object.keys(expected[0]);
          const filter =
            table === "analysis_map"
              ? ` AND map_kind IN (${mapKinds(disposition.family)
                  .map(() => "?")
                  .join(",")})`
              : "";
          const rows = yield* sql.unsafe<Record<string, unknown>>(
            `SELECT ${keys.length === 0 ? "1 AS present" : keys.join(",")} FROM ${table} WHERE season=? AND player_id=?${filter}`,
            [
              person.season,
              person.player_id,
              ...(table === "analysis_map" ? mapKinds(disposition.family) : []),
            ],
          );
          yield* Effect.try(() => {
            const actual = new Set(rows.map((row) => selectorKey(row, keys)));
            if (
              rows.length !== expected.length ||
              expected.some((row) => !actual.has(selectorKey(row, keys)))
            )
              throw new Error(`${table}: missing or unexpected promised person/selector row`);
          });
        }
        if (disposition.family === "evidence") {
          const rows = yield* sql.unsafe<{ population: string }>(
            "SELECT population FROM context_coverage WHERE season=? AND player_id=?",
            [person.season, person.player_id],
          );
          yield* Effect.try(() => {
            if (
              JSON.stringify(rows.map((row) => row.population).sort()) !==
              JSON.stringify([...A.ContextPopulation.literals].sort())
            )
              throw new Error("missing context coverage population");
          });
        }
      }
    }
  });

const assertEmpty = (sql: SqliteClient, query: string, message: string) =>
  Effect.gen(function* () {
    const rows = yield* sql.unsafe(query);
    if (rows.length > 0) return yield* Effect.fail(new Error(message));
  });
export const validateCrossRecords = (
  sql: SqliteClient,
  grids: readonly (typeof A.AnalysisGrid.Type)[],
) =>
  Effect.gen(function* () {
    const identities = yield* sql.unsafe<{ person_teams: string; observed_teams: string }>(
      "SELECT p.teams_json person_teams,s.teams_json observed_teams FROM person p JOIN player_season s USING(season,player_id)",
    );
    yield* Effect.try(() => {
      for (const row of identities) {
        const teams = decode(A.Person.fields.teams, strictJson(row.person_teams));
        const observed = decode(A.Person.fields.teams, strictJson(row.observed_teams));
        if (!A.preservesObservedAffiliations(teams, observed))
          throw new Error("person loses or changes an observed affiliation");
      }
    });
    yield* assertEmpty(
      sql,
      `SELECT 1 FROM person p JOIN json_each(p.teams_json) t
       LEFT JOIN player_season s USING(season,player_id)
       WHERE NOT EXISTS(SELECT 1 FROM json_each(coalesce(s.teams_json,'[]')) old WHERE json_extract(old.value,'$.id')=json_extract(t.value,'$.id'))
       AND NOT EXISTS(SELECT 1 FROM dressed_game d JOIN game g USING(season,game_id)
         WHERE d.season=p.season AND d.player_id=p.player_id AND d.team_id=json_extract(t.value,'$.id')
         AND ((d.team_id=g.away_team_id AND (g.away_abbreviation IS NULL OR g.away_abbreviation IS json_extract(t.value,'$.abbreviation')))
           OR (d.team_id=g.home_team_id AND (g.home_abbreviation IS NULL OR g.home_abbreviation IS json_extract(t.value,'$.abbreviation'))))) LIMIT 1`,
      "person affiliation lacks matching dressed-game/game-team evidence",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact a JOIN interval_fact b ON a.season=b.season AND a.game_id=b.game_id AND a.team_id=b.team_id AND a.population=b.population AND a.period_number=b.period_number AND a.rowid<b.rowid WHERE a.start_seconds<b.end_seconds AND b.start_seconds<a.end_seconds LIMIT 1",
      "overlapping context partition",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact GROUP BY season,game_id,interval_id HAVING MIN(period_number)<>MAX(period_number) OR MIN(start_seconds)<>MAX(start_seconds) OR MIN(end_seconds)<>MAX(end_seconds) LIMIT 1",
      "interval identity reuses different bounds",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact f JOIN game g USING(season,game_id) WHERE f.team_id NOT IN (g.away_team_id,g.home_team_id) OR f.period_number>4 OR f.end_seconds>CASE WHEN f.period_number=4 THEN 300 ELSE 1200 END LIMIT 1",
      "context team or period horizon differs",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact GROUP BY season,game_id,period_number HAVING MIN(period_horizon_seconds)<>MAX(period_horizon_seconds) LIMIT 1",
      "context source period horizon differs",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_player GROUP BY season,game_id,interval_id,player_id HAVING COUNT(*)>1 LIMIT 1",
      "player appears on both physical sides",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_player p LEFT JOIN dressed_game d USING(season,game_id,player_id) WHERE d.team_id IS NULL OR p.team_id<>d.team_id OR NOT EXISTS(SELECT 1 FROM interval_fact f WHERE f.season=p.season AND f.game_id=p.game_id AND f.interval_id=p.interval_id AND f.team_id=p.team_id) LIMIT 1",
      "interval membership lacks matching dressed identity/fact",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM dressed_game d JOIN game g USING(season,game_id) WHERE d.team_id NOT IN(g.away_team_id,g.home_team_id) LIMIT 1",
      "dressed identity team is absent from game",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact f JOIN game g USING(season,game_id) WHERE (SELECT COUNT(*) FROM interval_player p WHERE p.season=f.season AND p.game_id=f.game_id AND p.interval_id=f.interval_id AND p.team_id=g.away_team_id)<>5 OR (SELECT COUNT(*) FROM interval_player p WHERE p.season=f.season AND p.game_id=f.game_id AND p.interval_id=f.interval_id AND p.team_id=g.home_team_id)<>5 LIMIT 1",
      "context needs full five-on-five membership",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact f WHERE NOT EXISTS(SELECT 1 FROM interval_player p WHERE p.season=f.season AND p.game_id=f.game_id AND p.interval_id=f.interval_id) LIMIT 1",
      "interval has no full membership",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_fact a JOIN interval_fact b ON a.season=b.season AND a.game_id=b.game_id AND a.interval_id=b.interval_id AND a.population=b.population AND a.team_id<>b.team_id WHERE ABS(a.for_mass-b.against_mass)>1e-9+1e-9*MAX(ABS(a.for_mass),ABS(b.against_mass)) OR ABS(a.against_mass-b.for_mass)>1e-9+1e-9*MAX(ABS(a.against_mass),ABS(b.for_mass)) OR a.on_net_for IS NOT b.on_net_against OR a.on_net_against IS NOT b.on_net_for LIMIT 1",
      "paired context team facts do not mirror",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM dressed_game d JOIN person p USING(season,player_id) WHERE NOT EXISTS(SELECT 1 FROM json_each(p.teams_json) t WHERE json_extract(t.value,'$.id')=d.team_id) LIMIT 1",
      "dressed team is absent from person identity",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM dressed_game d JOIN player_game p USING(season,player_id,game_id) WHERE d.team_id<>p.team_id LIMIT 1",
      "dressed team conflicts with observed player game",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM interval_location l LEFT JOIN spatial_cell c USING(season,cell_id) WHERE c.cell_id IS NULL LIMIT 1",
      "context location cell is absent from physical geometry",
    );
    const geometries = yield* sql.unsafe<{
      cell_id: number;
      center_x: number;
      center_y: number;
      x_min: number;
      x_max: number;
      y_min: number;
      y_max: number;
      area_sqft: number;
    }>(
      "SELECT cell_id,center_x,center_y,x_min,x_max,y_min,y_max,area_sqft FROM spatial_cell WHERE season=(SELECT MAX(season) FROM season) ORDER BY cell_id",
    );
    const native = grids.find((grid) => grid.kind === "native")!,
      display = grids.find((grid) => grid.kind === "display")!;
    yield* Effect.try(() => {
      if (native.kind !== "native" || display.kind !== "display")
        throw new Error("missing fixed map geometry");
      const expected: { cell_id: number; x_ft: number; y_ft: number }[] = [];
      for (let x = -97.5; x < 100; x += 5)
        for (let y = -40; y < 45; y += 5)
          if (Math.max(Math.abs(x) - 72, 0) ** 2 + Math.max(Math.abs(y) - 14.5, 0) ** 2 <= 28 ** 2)
            expected.push({ cell_id: expected.length, x_ft: x, y_ft: y });
      if (JSON.stringify(expected) !== JSON.stringify(native.cells))
        throw new Error("native geometry identity differs");
      if (
        display.cells.length !== geometries.length ||
        display.cells.some((cell, i) =>
          Object.entries(cell).some(
            ([key, value]) => value !== geometries[i][key as keyof (typeof geometries)[number]],
          ),
        )
      )
        throw new Error("display geometry differs from observed physical partition");
    });
    const indices = new Map(geometries.map((cell, index) => [cell.cell_id, index]));
    const nativeDisplay =
      native.kind === "native"
        ? native.cells.map(
            (cell) =>
              indices.get(
                17 * Math.floor((cell.x_ft + 100) / 5) + Math.floor((cell.y_ft + 42.5) / 5),
              )!,
          )
        : [];
    // fixed K*T validation; this is transport arithmetic, not another estimator.
    const kernel = geometries.map((source) => {
      const weights = geometries.map(
        (target) =>
          target.area_sqft *
          Math.exp(
            -((target.center_x - source.center_x) ** 2 + (target.center_y - source.center_y) ** 2) /
              200,
          ),
      );
      const sum = weights.reduce((a, b) => a + b, 0);
      return weights.map((weight) => weight / sum);
    });
    const transport = (masses: readonly number[]) => {
      const raw = new Float64Array(668),
        pooled = new Float64Array(668);
      for (let i = 0; i < masses.length; i++) raw[nativeDisplay[i]] += masses[i];
      for (let source = 0; source < 668; source++)
        if (raw[source] !== 0)
          for (let target = 0; target < 668; target++)
            pooled[target] += raw[source] * kernel[source][target];
      return pooled;
    };
    yield* forEachRow(sql, "analysis_map", (row) =>
      Effect.gen(function* () {
        const result = yield* Effect.try(() => resultFromRow("analysis_map", row));
        if (result.availability !== "provided") return;
        const value = result.data;
        const units: Readonly<Record<string, string>> = {
          offense_attempts: "attempts_per60",
          defense_attempts: "attempts_per60",
          offense_xg: "xg_per60",
          defense_xg: "xg_per60",
          finishing: "goals_per100_attempts",
          setting: "goals_per100_assisted_opportunities",
          ice_won: "goals_per_basket",
          ice_lost: "goals_per_basket",
          goalie_stopping: "goals_per100_on_net",
        };
        yield* Effect.try(() => {
          if (value.grid_id !== "native656" || value.unit !== units[String(row.map_kind)])
            throw new Error("map grid or unit differs");
        });
        if (value.cells === null) return;
        const pooled = transport(value.cells.map((cell) => cell.value));
        yield* Effect.try(() => {
          if (row.view === "complete" && value.cells!.some((cell) => cell.value < 0))
            throw new Error("negative complete map rate");
          if (
            value.display_cells!.some(
              (cell, i) =>
                cell.cell_id !== geometries[i].cell_id ||
                !close(cell.mass, pooled[i]) ||
                !close(cell.density_per100sqft, (100 * cell.mass) / geometries[i].area_sqft),
            )
          )
            throw new Error("map display transport differs");
        });
        const kind = String(row.map_kind),
          spatial = ["offense_attempts", "defense_attempts", "offense_xg", "defense_xg"].includes(
            kind,
          );
        const table: SummaryTable = spatial
          ? "skater_spatial"
          : kind === "finishing" || kind === "setting"
            ? "skater_execution"
            : kind === "ice_won" || kind === "ice_lost"
              ? "skater_territory"
              : "goalie_result";
        const field = spatial
          ? `${kind}_per60${row.view === "complete" ? "_complete" : ""}`
          : kind === "finishing"
            ? "finishing_goals_per100_attempts"
            : kind === "setting"
              ? "setting_goals_per100_assisted_opportunities"
              : kind === "ice_won" || kind === "ice_lost"
                ? `${kind}_goals_per_basket`
                : "stopping_goals_per100_on_net";
        const rows = yield* sql.unsafe<Record<string, unknown>>(
          `SELECT * FROM ${table} WHERE season=? AND player_id=?${table === "skater_territory" ? "" : " AND strength=?"}`,
          [
            String(row.season),
            String(row.player_id),
            ...(table === "skater_territory" ? [] : [String(row.strength)]),
          ],
        );
        yield* Effect.try(() => {
          if (
            rows.length !== 1 ||
            rows[0].availability !== "provided" ||
            rows[0].method_id !== row.method_id
          )
            throw new Error("available map lacks matching scalar/method");
          const scalar = parseObject(rows[0].payload_json)[field] as A.Estimate;
          if (scalar.value === null || !close(value.integrated_value!, scalar.value))
            throw new Error("map scalar closure differs");
        });
      }),
    );
    yield* forEachRow(sql, "goalie_evidence_map", (row) =>
      Effect.try(() => {
        const result = resultFromRow("goalie_evidence_map", row);
        if (result.availability !== "provided") return;
        const value = result.data,
          keys = ["goals", "expected_goals", "attempts"] as const,
          pooled = keys.map((key) => transport(value.native_cells.map((cell) => cell[key])));
        for (const key of keys)
          if (
            !close(
              value.native_cells.reduce((sum, cell) => sum + cell[key], 0) + value.unmapped[key],
              value.totals[key],
            )
          )
            throw new Error("goalie evidence total differs");
        for (const [i, cell] of value.display_cells.entries()) {
          if (
            cell.cell_id !== geometries[i].cell_id ||
            keys.some((key, k) => !close(cell[key], pooled[k][i]))
          )
            throw new Error("goalie evidence display transport differs");
          const ratio =
            cell.expected_goals > 0 && value.league_goals > 0 && value.league_expected_goals > 0
              ? 100 *
                (cell.goals /
                  cell.expected_goals /
                  (value.league_goals / value.league_expected_goals) -
                  1)
              : null;
          if (
            ratio === null
              ? cell.ratio !== null || cell.unavailable_reason !== "no_exposure"
              : cell.ratio === null || cell.unavailable_reason !== null || !close(ratio, cell.ratio)
          )
            throw new Error("goalie evidence pooled ratio differs");
        }
      }),
    );
    yield* forEachRow(sql, "interval_fact", (row) =>
      Effect.gen(function* () {
        if (
          row.population !== "recorded_locatable_unblocked" &&
          row.population !== "neutral_locatable_unblocked_value"
        )
          return;
        const totals = yield* sql.unsafe<{ for_mass: number; against_mass: number }>(
          "SELECT COALESCE(SUM(for_mass),0) AS for_mass,COALESCE(SUM(against_mass),0) AS against_mass FROM interval_location WHERE season=? AND game_id=? AND interval_id=? AND team_id=? AND population=?",
          [
            String(row.season),
            String(row.game_id),
            String(row.interval_id),
            String(row.team_id),
            String(row.population),
          ],
        );
        yield* Effect.try(() => {
          if (
            !close(totals[0].for_mass, Number(row.for_mass)) ||
            !close(totals[0].against_mass, Number(row.against_mass))
          )
            throw new Error("context location/scalar closure differs");
        });
      }),
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM attempt_setter GROUP BY season,game_id,source_index HAVING ABS(SUM(json_extract(payload_json,'$.pre_outcome_weight'))-1)>2e-9 LIMIT 1",
      "setter weights do not sum to one",
    );
    yield* assertEmpty(
      sql,
      "SELECT 1 FROM attempt_execution_share s JOIN attempt_fact a USING(season,game_id,source_index) GROUP BY s.season,s.game_id,s.source_index HAVING COUNT(DISTINCT s.\"group\")<>4 OR json_extract(a.payload_json,'$.actor_all_attempt_opportunity.value') IS NULL OR json_extract(a.payload_json,'$.neutral_all_attempt_opportunity.value') IS NULL OR ABS(SUM(json_extract(s.payload_json,'$.goals'))-(json_extract(a.payload_json,'$.actor_all_attempt_opportunity.value')-json_extract(a.payload_json,'$.neutral_all_attempt_opportunity.value')))>1e-9+1e-9*MAX(ABS(SUM(json_extract(s.payload_json,'$.goals'))),ABS(json_extract(a.payload_json,'$.actor_all_attempt_opportunity.value')-json_extract(a.payload_json,'$.neutral_all_attempt_opportunity.value'))) LIMIT 1",
      "four-group execution shares do not close",
    );
  });

const validateRepeatedFacts = (sql: SqliteClient) =>
  Effect.gen(function* () {
    yield* forEachRow(sql, "skater_microstats", (row) =>
      Effect.gen(function* () {
        const result = yield* Effect.try(() => resultFromRow("skater_microstats", row));
        if (result.availability !== "provided") return;
        const observed = yield* sql.unsafe<Record<string, unknown>>(
          "SELECT personal_goals,personal_primary_assists,personal_included_seconds,personal_goals_per60,personal_primary_assists_per60 FROM player_season WHERE season=? AND player_id=?",
          [String(row.season), String(row.player_id)],
        );
        yield* Effect.try(() => {
          if (observed.length === 0) return;
          for (const [field, count, rate] of [
            ["goals_per60", "personal_goals", "personal_goals_per60"],
            ["primary_assists_per60", "personal_primary_assists", "personal_primary_assists_per60"],
          ] as const) {
            const fact = result.data[field];
            if (
              fact.value !== observed[0][rate] ||
              fact.numerator !== observed[0][count] ||
              fact.denominator !== observed[0].personal_included_seconds
            )
              throw new Error("repeated observed personal facts differ");
          }
        });
        const descriptive = yield* sql.unsafe<Record<string, unknown>>(
          "SELECT * FROM skater_descriptive WHERE season=? AND player_id=? AND availability='provided'",
          [String(row.season), String(row.player_id)],
        );
        if (descriptive.length === 0) return;
        yield* Effect.try(() => {
          const summary = resultFromRow("skater_descriptive", descriptive[0]);
          if (summary.availability !== "provided")
            throw new Error("descriptive fact disposition differs");
          const scoring = summary.data.scoring_by_strength.five_on_five;
          for (const [field, count] of [
            ["goals_per60", "goals"],
            ["primary_assists_per60", "primary_assists"],
          ] as const) {
            const fact = result.data[field];
            if (
              fact.value !== scoring[field].value ||
              fact.numerator !== scoring[count] ||
              fact.denominator !== scoring.seconds
            )
              throw new Error("repeated descriptive personal facts differ");
          }
        });
      }),
    );
    yield* forEachRow(sql, "skater_penalties", (row) =>
      Effect.gen(function* () {
        const result = yield* Effect.try(() => resultFromRow("skater_penalties", row));
        if (result.availability !== "provided") return;
        const rows = yield* sql.unsafe<Record<string, unknown>>(
          "SELECT * FROM skater_descriptive WHERE season=? AND player_id=? AND availability='provided'",
          [String(row.season), String(row.player_id)],
        );
        if (rows.length === 0) return;
        yield* Effect.try(() => {
          const summary = resultFromRow("skater_descriptive", rows[0]);
          if (summary.availability !== "provided")
            throw new Error("descriptive fact disposition differs");
          for (const key of ["drawn", "taken", "served"] as const)
            if (
              JSON.stringify(canonical(result.data[`recorded_${key}`])) !==
              JSON.stringify(canonical(summary.data.recorded_penalties.focal[key]))
            )
              throw new Error("repeated recorded penalty fields differ");
        });
      }),
    );
    yield* forEachRow(sql, "value_ledger", (row) =>
      Effect.gen(function* () {
        if (row.availability !== "provided") return;
        const methods = yield* sql.unsafe<{ payload_json: string }>(
          "SELECT payload_json FROM analysis_method WHERE method_id=?",
          [String(row.method_id)],
        );
        if (methods.length !== 1) return yield* Effect.fail(new Error("ledger method is missing"));
        const ledger = yield* Effect.try(() => parseObject(methods[0].payload_json));
        for (const table of [
          "skater_spatial",
          "skater_execution",
          "skater_penalties",
          "skater_territory",
        ]) {
          const components = yield* sql.unsafe<{ payload_json: string }>(
            `SELECT m.payload_json FROM ${table} r JOIN analysis_method m USING(method_id) WHERE r.season=? AND r.player_id=? AND r.availability='provided'`,
            [String(row.season), String(row.player_id)],
          );
          yield* Effect.try(() => {
            for (const row of components) {
              const component = parseObject(row.payload_json);
              if (
                component.reference_id !== ledger.reference_id ||
                component.support_policy_id !== ledger.support_policy_id
              )
                throw new Error("ledger and component policies differ");
            }
          });
        }
      }),
    );
  });
