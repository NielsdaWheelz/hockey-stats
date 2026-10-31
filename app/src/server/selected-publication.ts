import type { SqliteClient } from "@effect/sql-sqlite-node/SqliteClient";
import * as Effect from "effect/Effect";
import * as A from "../shared/player-analysis.js";
import type { Season, SpatialSelection } from "../shared/observed.js";
import {
  absent,
  decode,
  factFromRow,
  pending,
  per60,
  provided,
  resultFromRow,
  type SummaryTable,
  type summarySchemas,
} from "./analysis-publication.js";
type Queries = {
  envelope: (season: Season) => typeof A.Envelope.Type;
  person: (season: Season, id: string) => A.Person | null;
  known: (id: string) => A.Person;
  readSummary: (
    table: SummaryTable,
    season: Season,
    id: string,
    selectors?: Readonly<Record<string, string>>,
  ) => Effect.Effect<
    (typeof summarySchemas)[SummaryTable]["Type"],
    Error | import("effect/sql/SqlError").SqlError
  >;
};
const requireKind = (queries: Queries, id: string, kind: "skater" | "goalie") => {
  const person = queries.known(id);
  if (person.kind !== kind)
    throw new A.SelectionError(400, "person kind is incompatible with selection");
};
const attempt = (row: Record<string, unknown>) => {
  const { strength, ...value } = factFromRow(row);
  return decode(A.ValuedAttemptFact, value);
};
export const readMaps = (
  selection: A.MapSelection,
  queries: Queries & {
    grids: readonly (typeof A.AnalysisGrid.Type)[];
    readSpatial: (
      season: Season,
      ids: readonly string[],
    ) => Effect.Effect<SpatialSelection | null, Error | import("effect/sql/SqlError").SqlError>;
  },
) =>
  Effect.gen(function* () {
    const kind =
      selection.family === "goalie_evidence" || selection.family === "goalie_stopping"
        ? "goalie"
        : "skater";
    yield* Effect.try(() => {
      for (const id of selection.players) requireKind(queries, id, kind);
    });
    const base = yield* Effect.try(() => queries.envelope(selection.season));
    if (selection.family === "observed") {
      const spatial = yield* queries.readSpatial(selection.season, selection.players);
      if (spatial === null) return yield* Effect.fail(new Error("observed map selection missing"));
      const values = spatial.players.flatMap(
        (player) =>
          player.data?.cells?.flatMap((cell) =>
            selection.view === "effect"
              ? [cell.for_difference, cell.against_difference]
              : [cell.for_density, cell.against_density],
          ) ?? [],
      );
      const maximum = Math.max(0, ...values.map(Math.abs));
      return yield* Effect.try(() =>
        decode(A.MapsResponse, {
          ...base,
          family: "observed",
          selection: spatial,
          scale: {
            minimum: selection.view === "effect" ? -maximum : 0,
            maximum,
            unit: spatial.definition.units,
          },
        }),
      );
    }
    const players: unknown[] = [],
      values: number[] = [];
    const mapUnits: Readonly<Record<string, string>> = {
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
    const unit =
      selection.family === "goalie_evidence"
        ? selection.view === "evidence_ratio"
          ? "percent"
          : "goals"
        : `${mapUnits[selection.family]}_per100sqft`;
    for (const player_id of selection.players) {
      if (queries.person(selection.season, player_id) === null) {
        players.push({ player_id, result: absent("player is absent from selected season") });
        continue;
      }
      const result = yield* queries.readSummary(
        selection.family === "goalie_evidence" ? "goalie_evidence_map" : "analysis_map",
        selection.season,
        player_id,
        selection.family === "goalie_evidence"
          ? {
              strength: selection.strength,
              population: selection.population!,
              type: selection.type!,
            }
          : { map_kind: selection.family, strength: selection.strength, view: selection.view },
      );
      if (result.availability === "provided") {
        if (selection.family === "goalie_evidence") {
          const data = decode(A.GoalieEvidenceMap, result.data);
          for (const cell of data.display_cells)
            if (selection.view === "evidence_ratio" ? cell.ratio !== null : true)
              values.push(selection.view === "evidence_ratio" ? cell.ratio! : cell.mass_saved);
        } else {
          const data = decode(A.AnalysisMap, result.data);
          for (const cell of data.display_cells ?? []) values.push(cell.density_per100sqft);
        }
      }
      players.push({ player_id, result });
    }
    if (selection.family.startsWith("offense_") || selection.family.startsWith("defense_")) {
      const counterpart = selection.family.startsWith("offense_")
        ? selection.family.replace("offense_", "defense_")
        : selection.family.replace("defense_", "offense_");
      const reciprocal: Readonly<Record<string, string>> = {
        "5v5": "5v5",
        "5v4": "4v5",
        "5v3": "3v5",
        "4v3": "3v4",
        "4v5": "5v4",
        "3v5": "5v3",
        "3v4": "4v3",
        pp: "pk",
        pk: "pp",
      };
      for (const player_id of selection.players) {
        if (queries.person(selection.season, player_id) === null) continue;
        const result = yield* queries.readSummary("analysis_map", selection.season, player_id, {
          map_kind: counterpart,
          strength: reciprocal[selection.strength],
          view: selection.view,
        });
        if (result.availability === "provided")
          for (const cell of decode(A.AnalysisMap, result.data).display_cells ?? [])
            values.push(cell.density_per100sqft);
      }
    }
    const maximum = Math.max(0, ...values.map(Math.abs));
    const definition = {
      native_grid: queries.grids.find((grid) => grid.kind === "native"),
      display_grid: queries.grids.find((grid) => grid.kind === "display"),
      orientation: "shooting_team_positive_x",
    };
    return yield* Effect.try(() =>
      decode(A.MapsResponse, {
        ...base,
        family: selection.family,
        selection,
        definition,
        scale: {
          minimum:
            selection.view === "evidence_ratio"
              ? -25
              : selection.view === "complete"
                ? 0
                : -maximum,
          maximum: selection.view === "evidence_ratio" ? 25 : maximum,
          unit,
        },
        players,
      }),
    );
  });
export const readEvidence = (sql: SqliteClient, selection: A.EvidenceSelection, queries: Queries) =>
  Effect.gen(function* () {
    const { season, player_id, family, strength } = selection;
    yield* Effect.try(() =>
      requireKind(
        queries,
        player_id,
        family === "goalie" || family === "goalie_evidence" ? "goalie" : "skater",
      ),
    );
    const base = yield* Effect.try(() => queries.envelope(season));
    const missingPerson = queries.person(season, player_id) === null;
    if (missingPerson)
      return yield* Effect.try(() =>
        decode(A.EvidenceResponse, {
          ...base,
          family,
          selection,
          result: absent("player is absent from selected season"),
        }),
      );
    const disposition = base.publication.families.find(
      (row) =>
        row.season === season &&
        row.family ===
          (family === "personal_shots"
            ? "evidence"
            : family === "goalie_evidence"
              ? "goalie"
              : family),
    )!;
    if (disposition.availability === "not_computed")
      return yield* Effect.try(() =>
        decode(A.EvidenceResponse, {
          ...base,
          family,
          selection,
          result: pending(disposition.explanation!),
        }),
      );
    if (family === "penalties" || family === "territory" || family === "microstats") {
      const result = yield* queries.readSummary(
        `skater_${family}` as SummaryTable,
        season,
        player_id,
      );
      return yield* Effect.try(() =>
        decode(A.EvidenceResponse, { ...base, family, selection, result }),
      );
    }
    if (family === "goalie_evidence") {
      const observed = yield* queries.readSummary("goalie_observed", season, player_id, {
        strength: strength!,
      });
      const map = yield* queries.readSummary("goalie_evidence_map", season, player_id, {
        strength: strength!,
        population: selection.population!,
        type: selection.type!,
      });
      const danger = yield* queries.readSummary("goalie_danger", season, player_id, {
        strength: strength!,
        population: selection.population!,
      });
      return yield* Effect.try(() =>
        decode(A.EvidenceResponse, {
          ...base,
          family,
          selection,
          result: provided({ observed, map, danger }),
        }),
      );
    }
    if (family === "personal_shots") {
      if (selection.shot_type !== null) {
        const types = yield* sql.unsafe<Record<string, unknown>>(
          "SELECT 1 FROM attempt_fact WHERE season=? AND COALESCE(shot_type,'unknown')=? LIMIT 1",
          [season, selection.shot_type],
        );
        if (
          types.length === 0 &&
          !A.SourceShotType.literals.includes(selection.shot_type as typeof A.SourceShotType.Type)
        )
          return yield* Effect.fail(new A.SelectionError(400, "unknown source shot type"));
      }
      const rows = yield* sql.unsafe<Record<string, unknown>>(
        `SELECT * FROM attempt_fact WHERE season=? AND shooter_id=? AND strength='5v5'${selection.shot_type === null ? "" : " AND COALESCE(shot_type,'unknown')=?"} ORDER BY game_id,source_index`,
        selection.shot_type === null
          ? [season, player_id]
          : [season, player_id, selection.shot_type],
      );
      const attempts = yield* Effect.try(() =>
        rows
          .map(attempt)
          .filter((row) =>
            row.outcome === "block"
              ? selection.blocked_contacts
              : selection.outcome === "all_unblocked" ||
                (selection.outcome === "on_net" &&
                  (row.outcome === "goal" || row.outcome === "save")) ||
                row.outcome === selection.outcome,
          ),
      );
      return yield* Effect.try(() =>
        decode(A.EvidenceResponse, {
          ...base,
          family,
          selection,
          result: provided({
            attempts,
            unblocked_count: attempts.filter((row) => row.outcome !== "block").length,
            located_count: attempts.filter((row) => row.outcome !== "block" && row.x_ft !== null)
              .length,
            blocked_contact_count: attempts.filter((row) => row.outcome === "block").length,
            support_ids: [...new Set(attempts.map((row) => row.support_id))].sort(),
          }),
        }),
      );
    }
    const summary = yield* queries.readSummary(
      family === "goalie" ? "goalie_result" : "skater_execution",
      season,
      player_id,
      { strength: strength! },
    );
    const rawBreakdowns = yield* sql.unsafe<Record<string, unknown>>(
      "SELECT * FROM execution_breakdown WHERE season=? AND player_id=? AND strength=? ORDER BY CASE kind WHEN 'shot_type' THEN 0 ELSE 1 END,CASE stratum WHEN 'wrist' THEN 0 WHEN 'snap' THEN 1 WHEN 'slap' THEN 2 WHEN 'backhand' THEN 3 WHEN 'tip' THEN 4 WHEN 'other' THEN 5 WHEN '<.05' THEN 0 WHEN '[.05,.15)' THEN 1 WHEN '>=.15' THEN 2 END",
      [season, player_id, strength!],
    );
    const breakdowns = yield* Effect.try(() =>
      rawBreakdowns.map((row) => ({
        strength: row.strength,
        kind: row.kind,
        stratum: row.stratum,
        result: resultFromRow("execution_breakdown", row, queries.person(season, player_id)!.kind),
      })),
    );
    if (family === "goalie")
      return yield* Effect.try(() =>
        decode(A.EvidenceResponse, {
          ...base,
          family,
          selection,
          result: provided({ summary, breakdowns }),
        }),
      );
    const selectedEvents =
      "WITH selected AS (SELECT a.* FROM attempt_fact a WHERE a.season=? AND a.strength=? AND (a.shooter_id=? OR EXISTS(SELECT 1 FROM attempt_setter s WHERE s.season=a.season AND s.game_id=a.game_id AND s.source_index=a.source_index AND s.candidate_id=?) OR EXISTS(SELECT 1 FROM attempt_execution_share s WHERE s.season=a.season AND s.game_id=a.game_id AND s.source_index=a.source_index AND s.recipient_id=? AND s.\"group\" IN ('shooter','setter'))))";
    const parameters = [season, strength!, player_id, player_id, player_id];
    const rawAttempts = yield* sql.unsafe<Record<string, unknown>>(
      `${selectedEvents} SELECT * FROM selected ORDER BY game_id,source_index`,
      parameters,
    );
    const attempts = yield* Effect.try(() => rawAttempts.map(attempt));
    const setters = yield* sql.unsafe<Record<string, unknown>>(
      `${selectedEvents} SELECT s.* FROM attempt_setter s JOIN selected USING(season,game_id,source_index) ORDER BY s.game_id,s.source_index,s.candidate_id`,
      parameters,
    );
    const shares = yield* sql.unsafe<Record<string, unknown>>(
      `${selectedEvents} SELECT s.* FROM attempt_execution_share s JOIN selected USING(season,game_id,source_index) ORDER BY s.game_id,s.source_index,s.\"group\",s.recipient_id`,
      parameters,
    );
    return yield* Effect.try(() =>
      decode(A.EvidenceResponse, {
        ...base,
        family,
        selection,
        result: provided({
          summary,
          breakdowns,
          attempts,
          setters: setters.map((row) => decode(A.AttemptSetter, factFromRow(row))),
          shares: shares.map((row) => decode(A.AttemptExecutionShare, factFromRow(row))),
        }),
      }),
    );
  });
export const readContext = (sql: SqliteClient, selection: A.ContextSelection, queries: Queries) =>
  Effect.gen(function* () {
    const { season, player_id, mode, population, teammates } = selection,
      selected_players = [player_id, ...teammates];
    yield* Effect.try(() => {
      for (const id of selected_players) requireKind(queries, id, "skater");
    });
    const base = yield* Effect.try(() => queries.envelope(season));
    const locatable =
      population === "recorded_locatable_unblocked" ||
      population === "neutral_locatable_unblocked_value";
    const coverage: A.ContextResponse["coverage"][number][] = [];
    const disposition = base.publication.families.find(
      (row) => row.season === season && row.family === "evidence",
    )!;
    if (queries.person(season, player_id) === null || disposition.availability === "not_computed") {
      const missing = queries.person(season, player_id) === null;
      coverage.push({
        season,
        player_id,
        population,
        availability: missing ? "absent" : "not_computed",
        explanation: missing ? "player is absent from selected season" : disposition.explanation!,
        known_excluded_seconds: null,
        unquantified_gap: true,
        reason_counts: [],
        source_ids: [],
        method_ids: [],
      });
    } else {
      const rows = yield* sql.unsafe<Record<string, unknown>>(
        "SELECT * FROM context_coverage WHERE season=? AND player_id=? AND population=?",
        [season, player_id, population],
      );
      if (rows.length !== 1) return yield* Effect.fail(new Error("context coverage is missing"));
      coverage.push(yield* Effect.try(() => decode(A.ContextCoverage, factFromRow(rows[0]))));
    }
    const names = mode === "on_off" ? (["on", "off"] as const) : (["together", "apart"] as const);
    const groups: (typeof A.ContextGroup.Type)[] = names.map((group) => ({
      group,
      for_mass: 0,
      against_mass: 0,
      seconds: 0,
      for_per60: null,
      against_per60: null,
      on_net_for: population === "recorded_goals" ? 0 : null,
      on_net_against: population === "recorded_goals" ? 0 : null,
      locations: locatable ? [] : null,
      support_ids: [],
    }));
    if (coverage[0].availability !== "provided")
      return yield* Effect.try(() =>
        decode(A.ContextResponse, {
          ...base,
          mode,
          selected_players,
          population,
          groups: [],
          coverage,
        }),
      );
    const membership = (alias: string) =>
      `EXISTS(SELECT 1 FROM interval_player p WHERE p.season=f.season AND p.game_id=f.game_id AND p.interval_id=f.interval_id AND p.team_id=f.team_id AND p.player_id=${alias})`;
    const teammateTerms = teammates.map(
      () =>
        `${membership("?")} AND EXISTS(SELECT 1 FROM dressed_game t WHERE t.season=f.season AND t.game_id=f.game_id AND t.team_id=f.team_id AND t.player_id=?)`,
    );
    const together =
      teammateTerms.length === 0 ? "1" : teammateTerms.map((term) => `(${term})`).join(" AND ");
    const cte = `WITH eligible AS (SELECT f.*,${membership("?")} AS focal_present,${together} AS together FROM interval_fact f JOIN dressed_game d ON d.season=f.season AND d.game_id=f.game_id AND d.team_id=f.team_id AND d.player_id=? WHERE f.season=? AND f.population=?), selected AS (SELECT *,CASE WHEN ${mode === "on_off" ? "focal_present" : "together"} THEN ? ELSE ? END AS selected_group FROM eligible${mode === "with_without" ? " WHERE focal_present=1" : ""})`;
    const parameters = [
      player_id,
      ...teammates.flatMap((id) => [id, id]),
      player_id,
      season,
      population,
      ...names,
    ];
    const totals = yield* sql.unsafe<{
      selected_group: string;
      for_mass: number;
      against_mass: number;
      seconds: number;
      on_net_for: number | null;
      on_net_against: number | null;
      support_ids: string;
    }>(
      `${cte} SELECT selected_group,SUM(for_mass) AS for_mass,SUM(against_mass) AS against_mass,SUM(end_seconds-start_seconds) AS seconds,SUM(on_net_for) AS on_net_for,SUM(on_net_against) AS on_net_against,json_group_array(DISTINCT support_id) AS support_ids FROM selected GROUP BY selected_group`,
      parameters,
    );
    for (const total of totals) {
      const group = groups.find((row) => row.group === total.selected_group)!;
      Object.assign(group, {
        for_mass: total.for_mass,
        against_mass: total.against_mass,
        seconds: total.seconds,
        for_per60: per60(total.for_mass, total.seconds),
        against_per60: per60(total.against_mass, total.seconds),
        on_net_for: total.on_net_for,
        on_net_against: total.on_net_against,
        support_ids: (JSON.parse(total.support_ids) as string[]).sort(),
      });
    }
    if (locatable) {
      const locations = yield* sql.unsafe<{
        selected_group: string;
        cell_id: number;
        for_mass: number;
        against_mass: number;
      }>(
        `${cte} SELECT s.selected_group,l.cell_id,SUM(l.for_mass) AS for_mass,SUM(l.against_mass) AS against_mass FROM selected s JOIN interval_location l USING(season,game_id,interval_id,team_id,population) GROUP BY s.selected_group,l.cell_id ORDER BY s.selected_group,l.cell_id`,
        parameters,
      );
      for (const { selected_group, ...cell } of locations) {
        const group = groups.find((row) => row.group === selected_group)!;
        Object.assign(group, { locations: [...group.locations!, cell] });
      }
    }
    return yield* Effect.try(() =>
      decode(A.ContextResponse, { ...base, mode, selected_players, population, groups, coverage }),
    );
  });
