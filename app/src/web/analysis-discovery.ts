import type {
  Estimate,
  LeagueResponse,
  Person,
  Source,
  Support,
} from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import {
  analysisMetric,
  analysisMetrics,
  comparativeTileIds,
  selectLeagueValues,
  selectMissingLeagueValue,
  type AnalysisMetricId,
} from "./analysis-values";
import { buildAnalysisCohort } from "./analysis-cohorts";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  type AnalysisRow,
} from "./analysis-history";
import { matchingPlayers, nameOrder, playerName } from "./presentation";
import type {
  Discovery,
  DiscoveryTable,
  PeerSettings,
  Sort,
} from "./explorer";
import type { CsvCell } from "./export";

type Overview = Extract<LeagueResponse, { kind: "skater"; family: "overview" }>;
export type MetadataId =
  | "minutes"
  | "reportedAppearances"
  | "reportedMinutes"
  | "games"
  | "personalMinutes";
export type DiscoveryColumn = {
  readonly id: AnalysisMetricId | MetadataId;
  readonly label: string;
};
export type MetadataValue = {
  readonly value: number | null;
  readonly unit: string;
  readonly displayScale: number;
  readonly displayUnit: string;
  readonly status: string;
  readonly reason: string | null;
  readonly support: Support | null;
  readonly observedSupport: unknown;
  readonly source: Source | null;
  readonly original: Estimate | null;
  readonly evidence: unknown;
  readonly semanticKey: string;
  readonly semanticIdentityKnown: boolean;
  readonly definition: string;
};
export type DiscoveryCell =
  | {
      readonly kind: "metric";
      readonly row: AnalysisRow;
      readonly value: number | null;
      readonly semanticKey: string;
      readonly semanticIdentityKnown: boolean;
      readonly definition: string;
    }
  | ({ readonly kind: "metadata" } & MetadataValue);
export type DiscoveryRow = {
  readonly person: Person;
  readonly cells: Readonly<Record<string, DiscoveryCell>>;
};
export const discoveryTables: readonly DiscoveryTable[] = [
  "overview",
  "observed",
  "spatial",
  "execution",
  "shootiness",
  "penalties",
  "territory",
];
const metadataLabels: Record<MetadataId, string> = {
  minutes: "included observed 5v5 min",
  reportedAppearances: "reported appearances",
  reportedMinutes: "reported min / appearance",
  games: "included on-ice games",
  personalMinutes: "personal included 5v5 min",
};

export function discoveryPreset(table: DiscoveryTable, strength: string | null) {
  let ids: readonly (AnalysisMetricId | MetadataId)[];
  let defaultSort: AnalysisMetricId | MetadataId;
  switch (table) {
    case "overview":
      ids = [
        "minutes",
        "reportedAppearances",
        "reportedMinutes",
        "ledger.league_total",
        "ledger.replacement_total",
        ...comparativeTileIds,
      ];
      defaultSort = "ledger.league_total";
      break;
    case "observed":
      ids = [
        "minutes",
        "games",
        "personalMinutes",
        "for60",
        "against60",
        "sog60",
        "goals60",
        "primaryAssists60",
      ];
      defaultSort = "minutes";
      break;
    case "spatial": {
      const selected = strength ?? "5v5";
      ids = [
        "minutes",
        ...analysisMetrics
          .filter(metric => metric.id.startsWith(`spatial.${selected}.`))
          .map(metric => metric.id),
      ];
      defaultSort =
        `spatial.${selected}.${selected === "pk" ? "defense" : "offense"}_xg_per60` as AnalysisMetricId;
      break;
    }
    case "execution":
    case "shootiness": {
      const selected = strength ?? "5v5";
      ids = [
        "minutes",
        ...analysisMetrics
          .filter(metric => metric.id.startsWith(`${table}.${selected}.`))
          .map(metric => metric.id),
      ];
      defaultSort = table === "execution"
        ? `execution.${selected}.finishing_goals_per100_attempts` as AnalysisMetricId
        : `shootiness.${selected}.difference` as AnalysisMetricId;
      break;
    }
    case "penalties":
      ids = [
        "minutes",
        "penalties.drawn_per60",
        "penalties.taken_per60",
        "penalties.drawn_value_per60",
        "penalties.taken_value_per60",
      ];
      defaultSort = "penalties.drawn_value_per60";
      break;
    case "territory":
      ids = [
        "minutes",
        "territory.exit_offense.one_second_probability",
        "territory.entry_offense.one_second_probability",
        "territory.zone_retention.one_second_probability",
        "territory.entry_prevention.one_second_probability",
        "territory.ice_won_goals_per_basket",
        "territory.ice_lost_goals_per_basket",
      ];
      defaultSort = "territory.ice_won_goals_per_basket";
  }
  return {
    table,
    strength,
    defaultSort,
    columns: ids.map(id => ({
      id,
      label: analysisMetric(id)?.label ?? metadataLabels[id as MetadataId],
    })),
  };
}

function metadataValue(
  overview: Overview,
  row: Overview["players"][number],
  id: MetadataId,
): MetadataValue {
  const usageField = id === "reportedAppearances" || id === "reportedMinutes";
  const envelope = row.result.availability === "provided"
    ? usageField ? row.result.data.reported_usage : row.result.data.observed
    : row.result;
  const common = {
    unit: id === "minutes" || id === "personalMinutes"
      ? "seconds"
      : id === "reportedMinutes"
        ? "minutes_per_appearance"
        : id === "games" ? "games" : "appearances",
    displayScale: id === "minutes" || id === "personalMinutes" ? 1 / 60 : 1,
    displayUnit: id === "minutes" || id === "personalMinutes"
      ? "minutes"
      : id === "reportedMinutes"
        ? "minutes per appearance"
        : id === "games" ? "games" : "appearances",
  };
  const definition = metadataLabels[id];
  if (envelope.availability !== "provided") return {
    ...common,
    value: null,
    status: envelope.availability,
    reason: envelope.explanation,
    support: null,
    source: null,
    original: null,
    observedSupport: null,
    evidence: envelope,
    semanticKey: JSON.stringify([id, "unknown"]),
    semanticIdentityKnown: false,
    definition,
  };
  if (
    usageField &&
    row.result.availability === "provided" &&
    row.result.data.reported_usage.availability === "provided"
  ) {
    const usage = row.result.data.reported_usage.data;
    const source = overview.sources[usage.provenance.id];
    if (!source) throw new Error(`unresolved source ${usage.provenance.id}`);
    const original = id === "reportedMinutes" ? usage.minutes_per_appearance : null;
    return {
      ...common,
      value: id === "reportedAppearances"
        ? usage.positive_toi_appearances
        : usage.minutes_per_appearance.value,
      status: original?.value === null ? "unavailable" : "provided",
      reason: original?.value === null
        ? original.reason_detail?.explanation ?? original.unavailable_reason
        : null,
      support: usage.support,
      source,
      original,
      observedSupport: null,
      evidence: { reported_usage: usage, source },
      semanticKey: JSON.stringify([
        id, common.unit, source.construction, source.population, source.definition,
      ]),
      semanticIdentityKnown: true,
      definition: `${definition}; ${source.construction}; ${source.population}; ${source.definition}`,
    };
  }
  if (
    row.result.availability !== "provided" ||
    row.result.data.observed.availability !== "provided"
  ) throw new Error("unresolved observed metadata envelope");
  const observed = row.result.data.observed.data;
  const support = id === "personalMinutes" ? observed.personal : observed.metrics;
  const populationVersion = id === "personalMinutes"
    ? overview.publication.personal_population_version
    : overview.publication.population_version;
  return {
    ...common,
    value: id === "games" ? observed.games_with_included_time : support.included_seconds,
    status: "provided",
    reason: null,
    support: null,
    source: null,
    original: null,
    observedSupport: support,
    evidence: { observed_support: support, population_version: populationVersion },
    semanticKey: JSON.stringify([id, common.unit, populationVersion]),
    semanticIdentityKnown: true,
    definition: `${definition}; observed population ${populationVersion}`,
  };
}

export function composeDiscoveryRows(
  overview: Overview,
  selectedCohort: LeagueResponse,
  columns: readonly DiscoveryColumn[],
  settings: PeerSettings,
): DiscoveryRow[] {
  const rows = overview.players.map(row => ({
    person: row.person,
    cells: {} as Record<string, DiscoveryCell>,
  }));
  for (const column of columns) {
    const metric = analysisMetric(column.id);
    if (!metric) {
      overview.players.forEach((row, index) => {
        rows[index]!.cells[column.id] = {
          kind: "metadata",
          ...metadataValue(overview, row, column.id as MetadataId),
        };
      });
      continue;
    }
    const response = metric.family === "overview" || metric.family === "observed"
      ? overview : selectedCohort;
    const datums = selectLeagueValues(response, metric);
    const present = new Set(datums.map(datum => datum.playerId));
    for (const row of rows) {
      if (!present.has(row.person.player_id))
        datums.push(selectMissingLeagueValue(response, metric, row.person));
    }
    const cohort = buildAnalysisCohort(datums, datums, settings);
    const byId = new Map(cohort.groups.flatMap(group =>
      group.selected.map(selection => [
        selection.datum.playerId,
        {
          datum: selection.datum,
          standing: selection.standing,
          member: group.members.some(member => member.playerId === selection.datum.playerId),
          incompatiblePeerCount: group.incompatiblePeerCount,
        },
      ] as const),
    ));
    for (const row of rows) {
      const analysis = byId.get(row.person.player_id);
      if (!analysis) throw new Error(`missing discovery scalar for ${row.person.player_id}`);
      const { datum } = analysis;
      row.cells[column.id] = {
        kind: "metric",
        row: analysis,
        value: datum.value,
        semanticKey: datum.semanticKey,
        semanticIdentityKnown: datum.semanticIdentityKnown,
        definition: [
          datum.numericReference,
          datum.construction,
          datum.population,
          ...datum.methods.map(method =>
            `recipe ${method.recipe_id}, reference ${method.reference_id}, support ${method.support_policy_id}`,
          ),
          ...datum.sources.map(source =>
            `source definition ${source.definition}; ${source.construction}; ${source.population}`,
          ),
          `support policy ${datum.supportPolicyId}`,
        ].join("; "),
      };
    }
  }
  return rows;
}

export function sortDiscoveryRows(
  rows: readonly DiscoveryRow[],
  sort: Sort,
  dir: "asc" | "desc",
): DiscoveryRow[] {
  return [...rows].sort((a, b) => {
    if (sort === "name") return (
      (dir === "asc" ? 1 : -1) * playerName(a.person).localeCompare(playerName(b.person), "en") ||
      nameOrder(a.person, b.person)
    );
    const left = a.cells[sort]!, right = b.cells[sort]!;
    if (left.semanticIdentityKnown !== right.semanticIdentityKnown)
      return left.semanticIdentityKnown ? -1 : 1;
    const group = left.semanticKey.localeCompare(right.semanticKey, "en");
    if (group) return group;
    if (left.value === null) return right.value === null ? nameOrder(a.person, b.person) : 1;
    if (right.value === null) return -1;
    return (
      (dir === "asc" ? left.value - right.value : right.value - left.value) ||
      nameOrder(a.person, b.person)
    );
  });
}

export function filterDiscoveryRows(
  rows: readonly DiscoveryRow[],
  discovery: Discovery,
): { rows: DiscoveryRow[]; unknownTimeExcluded: number } {
  const matches = new Set(
    matchingPlayers(rows.map(row => row.person), discovery.q)
      .map(person => person.player_id),
  );
  const identities = rows.filter(row =>
    matches.has(row.person.player_id) &&
    (discovery.position === "all" || (discovery.position === "d"
      ? row.person.reported_position === "D"
      : ["C", "L", "R", "F"].includes(row.person.reported_position ?? ""))) &&
    (discovery.team === null || row.person.teams.some(team => team.id === discovery.team)),
  );
  return {
    rows: identities.filter(row =>
      discovery.min === 0 ||
      row.cells.minutes!.value !== null && row.cells.minutes!.value! >= discovery.min * 60,
    ),
    unknownTimeExcluded: discovery.min > 0
      ? identities.filter(row => row.cells.minutes!.value === null).length : 0,
  };
}

export const discoveryCsvHeaders = [
  ...analysisCsvHeaders,
  "table",
  "strength",
  "row_order",
  "column_order",
  "column_id",
  "metadata_evidence",
] as const;

function metadataCsvRow(
  publication: Publication,
  season: SeasonEvidence,
  person: Person,
  cell: MetadataValue,
): readonly CsvCell[] {
  const fields: Partial<Record<typeof analysisCsvHeaders[number], CsvCell>> = {
    publication_id: publication.publication_id,
    purpose: publication.purpose,
    season: season.season,
    corpus_sha256: season.corpus_sha256,
    player_id: person.player_id,
    player_kind: person.kind,
    display_name: person.display_name,
    position: person.reported_position,
    unit: cell.unit,
    display_unit: cell.displayUnit,
    value: cell.value,
    display_value: cell.value === null ? null : cell.value * cell.displayScale,
    value_status: cell.status,
    value_reason: cell.reason,
    population: cell.source?.population ?? null,
    construction: cell.source?.construction ?? "recorded",
    numeric_reference: cell.definition,
    included_seconds: cell.support?.included_seconds ??
      (cell.observedSupport as { included_seconds?: number } | null)?.included_seconds ?? null,
    known_excluded_seconds: cell.support?.known_excluded_seconds ??
      (cell.observedSupport as { known_excluded_seconds?: number } | null)?.known_excluded_seconds ?? null,
    unquantified_gap: cell.support?.unquantified_gap ?? null,
    source_ids: cell.source ? JSON.stringify([cell.source.source_id]) : null,
    teams: JSON.stringify(person.teams),
    observed_support: cell.observedSupport ? JSON.stringify(cell.observedSupport) : null,
    support_reason_counts: cell.support ? JSON.stringify(cell.support.reason_counts) : null,
    semantic_identity: cell.semanticKey,
    uncertainty_status: cell.original?.uncertainty.kind ?? null,
    uncertainty: cell.original ? JSON.stringify(cell.original.uncertainty) : null,
    value_reason_detail: cell.original?.reason_detail ? JSON.stringify(cell.original.reason_detail) : null,
    prior_only: cell.support?.prior_only ?? null,
    inferred_inputs: cell.support ? JSON.stringify(cell.support.inferred_inputs) : null,
    current_season_information: cell.support?.current_season_information ?? null,
    prior_seasons: cell.support ? JSON.stringify(cell.support.prior_seasons) : null,
    source_definitions: cell.source ? JSON.stringify([cell.source.definition]) : null,
    source_limitations: cell.source ? JSON.stringify(cell.source.limitations) : null,
  };
  return analysisCsvHeaders.map(header => fields[header] ?? null);
}

export function discoveryCsvRows(
  publication: Publication,
  season: SeasonEvidence,
  rows: readonly DiscoveryRow[],
  preset: ReturnType<typeof discoveryPreset>,
): readonly (readonly CsvCell[])[] {
  return rows.flatMap((row, rowIndex) => preset.columns.map((column, columnIndex) => {
    const cell = row.cells[column.id]!;
    return [
      ...(cell.kind === "metric"
        ? analysisCsvRow(publication, season, cell.row)
        : metadataCsvRow(publication, season, row.person, cell)),
      preset.table,
      preset.strength,
      rowIndex + 1,
      columnIndex + 1,
      column.id,
      cell.kind === "metric" ? "" : JSON.stringify(cell.evidence),
    ];
  }));
}
