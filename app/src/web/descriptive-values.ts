import type {
  Estimate,
  Person,
  PlayerResponse,
  SkaterDescriptive,
  SkaterContext,
  Support,
  Source,
  Method,
} from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import type { ProfileView } from "./client";
import type { PeerSettings } from "./explorer";
import {
  analysisMetric,
  descriptiveMetricIds,
  selectHistoryValue,
  selectLeagueValues,
  type AnalysisDatum,
} from "./analysis-values";
import {
  buildDescriptiveGuide,
  type DescriptiveGuide,
} from "./analysis-cohorts";
import { csvText, type CsvCell } from "./export";

type Result<T> =
  | {
      readonly availability: "provided";
      readonly data: T;
      readonly explanation: null;
    }
  | {
      readonly availability: "absent" | "not_computed";
      readonly data: null;
      readonly explanation: string;
    };
type DescriptiveAnnual = {
  readonly season: SeasonEvidence;
  readonly person: Person | null;
  readonly descriptive: Result<SkaterDescriptive>;
  readonly context: Result<SkaterContext>;
};
type DescriptiveGuideRow = {
  readonly datum: AnalysisDatum;
  readonly guide: DescriptiveGuide;
};
export type DescriptiveCardModel = {
  readonly publication: Publication;
  readonly season: SeasonEvidence;
  readonly playerId: string;
  readonly person: Person | null;
  readonly descriptive: Result<SkaterDescriptive>;
  readonly context: Result<SkaterContext>;
  readonly settings: PeerSettings;
  readonly sources: Readonly<Record<string, Source>>;
  readonly methods: Readonly<Record<string, Method>>;
  readonly guides: readonly DescriptiveGuideRow[];
  readonly annual: readonly DescriptiveAnnual[];
};

function annual(row: PlayerResponse["history"][number]): DescriptiveAnnual {
  const families = row.families;
  if ("availability" in families)
    return {
      season: row.season,
      person: row.person,
      descriptive: families,
      context: families,
    };
  if (families.kind !== "skater")
    throw new Error("descriptive card requires a skater");
  return {
    season: row.season,
    person: row.person,
    descriptive: families.descriptive,
    context: families.context,
  };
}

export function buildDescriptiveCard(
  view: ProfileView,
  playerId: string,
  settings: PeerSettings,
): DescriptiveCardModel {
  if (view.player_id !== playerId)
    throw new Error("descriptive card player identity differs");
  const rows = view.detail.history
    .map(annual)
    .sort((a, b) => a.season.season.localeCompare(b.season.season));
  const selected = rows.find((row) => row.season.season === view.season.season);
  const history = view.detail.history.find(
    (row) => row.season.season === view.season.season,
  );
  if (!selected || !history)
    throw new Error("descriptive card selected annual record missing");
  const guides = descriptiveMetricIds.map((id) => {
    const metric = analysisMetric(id)!;
    const datum = selectHistoryValue(history, view.detail, metric, playerId);
    const peers = view.descriptiveCohort
      ? selectLeagueValues(
          view.descriptiveCohort,
          metric,
          view.overviewCohorts.find(
            (row) => row.season.season === view.season.season,
          ),
        )
      : [];
    return { datum, guide: buildDescriptiveGuide(peers, datum, settings) };
  });
  return {
    ...selected,
    publication: view.publication,
    playerId,
    settings,
    sources: view.detail.sources,
    methods: view.detail.methods,
    guides,
    annual: rows,
  };
}

const descriptiveCsvHeaders = [
  "publication_id",
  "purpose",
  "season",
  "corpus_sha256",
  "player_id",
  "display_name",
  "position",
  "teams",
  "peer_setting",
  "peer_min_minutes",
  "specialty_min_minutes",
  "panel_id",
  "scope",
  "field_path",
  "category",
  "source_paths",
  "population",
  "value",
  "unit",
  "value_status",
  "value_reason",
  "numerator",
  "denominator",
  "denominator_kind",
  "support_json",
  "source_ids",
  "method_ids",
  "source_definitions",
  "source_limitations",
  "method_limitations",
  "semantic_identity",
  "guide_n",
  "guide_peer_group",
  "guide_cutoff_minutes",
  "guide_qualification",
] as const;
type DescriptiveScope =
  | "focal"
  | "on"
  | "off"
  | "team"
  | "league"
  | "teammates"
  | "opponents"
  | "guide";
type DescriptiveField = {
  readonly panel: string;
  readonly scope: DescriptiveScope;
  readonly path: string;
  readonly category: string;
  readonly sourcePaths: readonly string[];
  readonly value: number | string | boolean | null;
  readonly unit: string;
  readonly status: string;
  readonly reason: string | null;
  readonly support: Support | null;
  readonly sourceIds: readonly string[];
  readonly methodIds: readonly string[];
  readonly numerator: number | null;
  readonly denominator: number | null;
  readonly denominatorKind: string | null;
  readonly guide: DescriptiveGuideRow | null;
};

// finite panel roots define the export, including exact-state and category evidence.
// estimates retain their own null/reason; support is inherited only within its body.
export function descriptiveFields(
  model: DescriptiveCardModel,
): readonly DescriptiveField[] {
  const fields: DescriptiveField[] = [];
  const visit = (
    panel: string,
    scope: DescriptiveScope,
    path: string,
    value: unknown,
    inherited: Support | null,
    sourceIds: readonly string[],
    category = "",
    parent: Record<string, unknown> = {},
  ): void => {
    const base = {
      panel,
      scope,
      path,
      category,
      sourcePaths: [path],
      support: inherited,
      sourceIds,
      methodIds: [] as readonly string[],
      numerator: null,
      denominator: null,
      denominatorKind: null,
      guide: null,
    };
    if (value === null || typeof value !== "object") {
      if (typeof value === "number" && !Number.isFinite(value))
        throw new Error("descriptive values must be finite");
      const leaf = path.split(".").at(-1)!;
      const unit = leaf.includes("seconds")
        ? "seconds"
        : leaf === "height_cm"
          ? "cm"
          : leaf === "age_years"
            ? "years"
            : leaf === "band"
              ? "usage_band"
              : typeof value === "number"
                ? "count"
                : "text";
      fields.push({
        ...base,
        value: value as string | number | boolean | null,
        unit,
        status: value === null ? "unavailable" : "provided",
        reason: value === null ? "published value unavailable" : null,
      });
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((entry, index) => {
        const label =
          entry && typeof entry === "object"
            ? String(
                "code" in entry
                  ? entry.code
                  : "band" in entry
                    ? entry.band
                    : index,
              )
            : String(index);
        visit(
          panel,
          scope,
          path,
          entry,
          inherited,
          sourceIds,
          category ? `${category}:${label}` : label,
          parent,
        );
      });
      return;
    }
    const record = value as Record<string, unknown>;
    if ("value" in record && "unavailable_reason" in record) {
      const estimate = value as Estimate;
      const leaf = path.split(".").at(-1)!;
      const unit =
        leaf === "share_minus_half"
          ? "percentage_points"
          : leaf.includes("per60")
            ? "per60"
            : leaf === "per1000minutes"
              ? "per1000minutes"
              : leaf.includes("minutes_per_appearance")
                ? "minutes_per_appearance"
                : leaf === "mean_band_index"
                  ? "usage_band"
                  : "fraction";
      let numerator: number | null = null,
        denominator: number | null = null,
        denominatorKind: string | null = null;
      if (leaf.endsWith("_per60")) {
        const countKey =
          leaf === "for_per60"
            ? "for_count"
            : leaf === "against_per60"
              ? "against_count"
              : leaf.slice(0, -6);
        numerator =
          typeof parent[countKey] === "number"
            ? (parent[countKey] as number)
            : null;
        denominator =
          typeof parent.seconds === "number" ? parent.seconds : null;
        denominatorKind = "included_seconds";
      } else if (leaf === "per1000minutes") {
        numerator = typeof parent.count === "number" ? parent.count : null;
        denominator =
          typeof parent.reported_seconds === "number"
            ? parent.reported_seconds
            : null;
        denominatorKind = "matched_reported_seconds";
      } else if (leaf === "shooting_for" || leaf === "shooting_against") {
        numerator = parent[
          leaf === "shooting_for" ? "goals_for" : "goals_against"
        ] as number | null;
        denominator = parent[
          leaf === "shooting_for" ? "on_net_for" : "on_net_against"
        ] as number | null;
        denominatorKind = "on_net";
      } else if (leaf === "share" && path.includes(".shift_starts.")) {
        numerator = typeof parent.count === "number" ? parent.count : null;
        denominatorKind = "all_shift_starts";
      } else if (leaf === "share" && path.includes(".score.")) {
        numerator = typeof parent.seconds === "number" ? parent.seconds : null;
        denominatorKind =
          category === "unknown" ? "all_score_seconds" : "known_score_seconds";
      } else if (leaf === "save_fraction") {
        denominator =
          typeof parent.on_net_against === "number"
            ? parent.on_net_against
            : null;
        denominatorKind = "on_net_against";
      } else if (leaf === "minutes_per_appearance") {
        numerator =
          typeof parent.reported_seconds === "number"
            ? parent.reported_seconds / 60
            : typeof parent.seconds === "number"
              ? parent.seconds / 60
              : null;
        denominator =
          typeof parent.positive_toi_appearances === "number"
            ? parent.positive_toi_appearances
            : typeof parent.appearances === "number"
              ? parent.appearances
              : null;
        denominatorKind =
          typeof parent.positive_toi_appearances === "number"
            ? "positive_toi_appearances"
            : "role_conditional_appearances";
      }
      const references = estimate.reason_detail?.evidence ?? [];
      fields.push({
        ...base,
        value: estimate.value,
        unit,
        status: estimate.value === null ? "unavailable" : "provided",
        reason:
          estimate.unavailable_reason === null
            ? null
            : `${estimate.unavailable_reason}${estimate.reason_detail ? `: ${estimate.reason_detail.explanation}` : ""}`,
        sourceIds: [
          ...new Set([
            ...sourceIds,
            ...references
              .filter((ref) => ref.kind === "source")
              .map((ref) => ref.id),
          ]),
        ],
        methodIds: references
          .filter((ref) => ref.kind === "method")
          .map((ref) => ref.id),
        numerator,
        denominator,
        denominatorKind,
      });
      return;
    }
    const support = (record.support ??
      record.coverage ??
      inherited) as Support | null;
    const localSourceIds =
      record.provenance &&
      typeof record.provenance === "object" &&
      "id" in record.provenance
        ? [String(record.provenance.id)]
        : sourceIds;
    for (const [key, child] of Object.entries(record)) {
      if (key === "support" || key === "coverage" || key === "provenance")
        continue;
      visit(
        panel,
        scope,
        `${path}.${key}`,
        child,
        support,
        localSourceIds,
        path.endsWith(".shift_starts") || path.endsWith(".score")
          ? key
          : category,
        record,
      );
    }
  };
  if (model.person) {
    for (const key of [
      "display_name",
      "reported_position",
      "age_years",
      "age_as_of",
      "height_cm",
      "birth_date",
      "handedness",
    ] as const)
      visit(
        "d01",
        "focal",
        `person.${key}`,
        model.person[key],
        null,
        model.person.source
          .filter((ref) => ref.kind === "source")
          .map((ref) => ref.id),
      );
    model.person.teams.forEach((team) =>
      visit(
        "d01",
        "focal",
        "person.teams",
        team,
        null,
        model
          .person!.source.filter((ref) => ref.kind === "source")
          .map((ref) => ref.id),
        team.id,
      ),
    );
  } else {
    visit("d01", "focal", "person", null, null, []);
  }
  const d = model.descriptive;
  const sourceIds = d.availability === "provided" ? [d.data.provenance.id] : [];
  const body = d.availability === "provided" ? d.data : null;
  const roots = [
    ["d01", "reported_usage"],
    ["d02", "strength_usage"],
    ["d03", "scoring_by_strength.ev"],
    ["d04", "scoring_by_strength.pp"],
  ] as const;
  for (const [panel, path] of roots) {
    const value = path
      .split(".")
      .reduce<unknown>(
        (current, key) =>
          current && typeof current === "object"
            ? (current as Record<string, unknown>)[key]
            : null,
        body,
      );
    visit(panel, "focal", `descriptive.${path}`, value, null, sourceIds);
  }
  // non-plotted strengths and unclassified credits remain accessible in detail/csv.
  for (const key of [
    "pk",
    "other",
    "five_on_five",
    "states",
    "unclassified",
  ] as const)
    visit(
      "d03",
      "focal",
      `descriptive.scoring_by_strength.${key}`,
      body?.scoring_by_strength[key] ?? null,
      null,
      sourceIds,
    );
  for (const [panel, key, scopes] of [
    ["d06", "on_off_attempts", ["on", "off", "league"]],
    ["d07", "on_off_goals", ["on", "off", "league"]],
    ["d08", "on_ice_conversion", ["focal", "team", "league"]],
    ["d09", "recorded_penalties", ["focal", "team", "league"]],
    ["d10", "deployment", ["focal", "team", "league"]],
  ] as const) {
    for (const scope of scopes) {
      const group = body?.[key][scope as never] as unknown;
      if (key === "deployment") {
        const deployment =
          body?.deployment[scope as "focal" | "team" | "league"];
        visit(
          "d10",
          scope,
          `descriptive.deployment.${scope}.shift_starts`,
          deployment?.shift_starts ?? null,
          deployment?.support ?? null,
          sourceIds,
        );
        visit(
          "d11",
          scope,
          `descriptive.deployment.${scope}.score`,
          deployment?.score ?? null,
          deployment?.support ?? null,
          sourceIds,
        );
      } else
        visit(
          panel,
          scope,
          `descriptive.${key}.${scope}`,
          group ?? null,
          null,
          sourceIds,
        );
    }
  }
  for (const scope of ["teammates", "opponents"] as const)
    visit(
      "d12",
      scope,
      `context.${scope}`,
      model.context.availability === "provided"
        ? model.context.data[scope]
        : null,
      null,
      model.context.availability === "provided"
        ? [model.context.data.provenance.id]
        : [],
    );
  const strengths = ["ev", "pp", "pk", "other"] as const;
  const known = strengths.map(
    (key) => body?.strength_usage[key].seconds ?? null,
  );
  fields.push({
    panel: "d02",
    scope: "focal",
    path: "display.usage.known_seconds",
    category: "",
    sourcePaths: strengths.map(
      (key) => `descriptive.strength_usage.${key}.seconds`,
    ),
    value: known.some((value) => value !== null)
      ? known.reduce<number>((sum, value) => sum + (value ?? 0), 0)
      : null,
    unit: "seconds",
    status: known.every((value) => value !== null) ? "provided" : "partial",
    reason: known.every((value) => value !== null)
      ? null
      : `missing categories: ${strengths.filter((_, index) => known[index] === null).join(", ")}`,
    support: null,
    sourceIds,
    methodIds: [],
    numerator: null,
    denominator: null,
    denominatorKind: null,
    guide: null,
  });
  for (const row of model.guides) {
    for (const leaf of ["q25", "q50", "q75", "n"] as const) {
      fields.push({
        panel: "d05",
        scope: "guide",
        path: `guide.${row.datum.metric.id}.${leaf}`,
        category: "",
        sourcePaths: [
          row.datum.metric.id,
          ...(row.datum.metric.id.includes(".usage.")
            ? [
                "descriptive.reported_usage.minutes_per_appearance",
                "overview.observed.metrics.included_seconds",
              ]
            : [
                `descriptive.scoring_by_strength.${row.datum.metric.id.includes(".ev.") ? "ev" : "pp"}.primary_points_per60`,
              ]),
        ],
        value: row.guide[leaf],
        unit: leaf === "n" ? "count" : row.datum.metric.unit,
        status: row.guide[leaf] === null ? "unavailable" : "provided",
        reason:
          row.guide[leaf] !== null && row.guide.reason
            ? `focal outside guide: ${row.guide.reason}`
            : row.guide.reason,
        support: null,
        sourceIds: row.guide.sourceIds,
        methodIds: row.guide.methodIds,
        numerator: null,
        denominator: null,
        denominatorKind: null,
        guide: row,
      });
    }
  }
  for (const field of fields) {
    if (field.path.startsWith("person.") && field.value === null) {
      const key = field.path.slice("person.".length);
      const problems =
        model.person?.identity_support.problems.filter(
          (problem) => problem.field === key,
        ) ?? [];
      Object.assign(field, {
        status: model.person ? "unavailable" : "absent",
        reason: problems.length
          ? problems
              .map((problem) => `${problem.code}: ${problem.explanation}`)
              .join("; ")
          : "selected annual identity absent",
      });
      continue;
    }
    if (
      field.value !== null ||
      field.status === "provided" ||
      field.panel === "d05"
    )
      continue;
    const family = field.panel === "d12" ? model.context : model.descriptive;
    if (family.availability !== "provided")
      Object.assign(field, {
        status: family.availability,
        reason: family.explanation,
      });
  }
  const keys = fields.map((field) =>
    JSON.stringify([field.panel, field.scope, field.path, field.category]),
  );
  if (new Set(keys).size !== keys.length)
    throw new Error("duplicate descriptive card field");
  return fields;
}

function descriptiveCsvRows(
  model: DescriptiveCardModel,
): readonly (readonly CsvCell[])[] {
  return descriptiveFields(model).map((field) => {
    const sources = field.sourceIds.map((id) => model.sources[id]);
    const methods = field.methodIds.map((id) => model.methods[id]);
    const guide = field.guide;
    return [
      model.publication.publication_id,
      model.publication.purpose,
      model.season.season,
      model.season.corpus_sha256,
      model.playerId,
      model.person?.display_name,
      model.person?.reported_position,
      JSON.stringify(model.person?.teams ?? []),
      model.settings.peers,
      model.settings.peerMin,
      model.settings.specialtyMin,
      field.panel,
      field.scope,
      field.path,
      field.category,
      JSON.stringify(field.sourcePaths),
      guide
        ? `${guide.guide.peerGroup}; ${guide.guide.qualification}`
        : sources.map((source) => source.population).join("; "),
      field.value,
      field.unit,
      field.status,
      field.reason,
      field.numerator,
      field.denominator,
      field.denominatorKind,
      JSON.stringify(field.support),
      JSON.stringify(field.sourceIds),
      JSON.stringify(field.methodIds),
      JSON.stringify(sources.map((source) => source.definition)),
      JSON.stringify(sources.flatMap((source) => source.limitations)),
      JSON.stringify(methods.flatMap((method) => method.limitations)),
      guide?.datum.guideSemanticKey ??
        JSON.stringify(
          sources.map((source) => [source.source_id, source.definition]),
        ),
      guide?.guide.n,
      guide?.guide.peerGroup,
      guide?.guide.cutoffMinutes,
      guide?.guide.qualification,
    ];
  });
}
export const descriptiveCsv = (model: DescriptiveCardModel): string =>
  csvText(descriptiveCsvHeaders, descriptiveCsvRows(model));
