import type {
  Estimate,
  FactValue,
  Support,
  Person,
  Source,
  Method,
  LeagueResponse,
  PlayerResponse,
  PlayerFamilies,
  LeagueSelection,
  SkaterSpatial,
  SkaterExecution,
  SkaterShootiness,
  SkaterPenalties,
  SkaterTerritory,
  ValueLedger,
  GoalieResult,
  SkaterContext,
  SkaterDescriptive,
  ReportedUsage,
  SkaterMicrostats,
  QuantityPath,
} from "../shared/player-analysis";
import { preservesObservedAffiliations } from "../shared/player-analysis";
import type { Family, Publication } from "../shared/publication";
import type { PlayerSummary } from "../shared/observed";
import { observedMetrics, type ObservedRateKey } from "./observed-comparison";

type Spatial = typeof SkaterSpatial.Type;
type Execution = typeof SkaterExecution.Type;
type Shootiness = typeof SkaterShootiness.Type;
type Penalties = typeof SkaterPenalties.Type;
type Territory = typeof SkaterTerritory.Type;
type Ledger = typeof ValueLedger.Type;
type Goalie = typeof GoalieResult.Type;
type Result<T> =
  | {
      readonly availability: "provided";
      readonly data: T;
      readonly explanation: null;
    }
  | {
      readonly availability: "not_computed" | "absent";
      readonly data: null;
      readonly explanation: string;
    };

export type AnalysisCatalogs = {
  readonly publication: Publication;
  readonly sources: Readonly<Record<string, Source>>;
  readonly methods: Readonly<Record<string, Method>>;
};

export type ComponentSupport = Readonly<Record<
  string,
  | { readonly support: Support; readonly reason: null }
  | { readonly support: null; readonly reason: string }
>>;

export type AnalysisMetricId = ObservedRateKey
  | `ledger.${"league" | "replacement"}_total`
  | `ledger.${LedgerTerm | "penalties_combined"}.${"league" | "replacement"}_goals`
  | `spatial.5v5.${"offense" | "defense"}_${"attempts_per60" | "xg_per60" | "attempts_relative_percent" | "xg_relative_percent"}`
  | `spatial.pp.offense_${"attempts_per60" | "xg_per60" | "attempts_relative_percent" | "xg_relative_percent"}`
  | `spatial.pk.defense_${"attempts_per60" | "xg_per60" | "attempts_relative_percent" | "xg_relative_percent"}`
  | `execution.${typeof strengths[number]}.${typeof executionFields[number]}`
  | `shootiness.${typeof strengths[number]}.${"probability" | "difference"}`
  | `penalties.${"drawn_per60" | "taken_per60" | "drawn_value_per60" | "taken_value_per60"}`
  | `territory.${"ice_won_goals_per_basket" | "ice_lost_goals_per_basket"}`
  | `territory.${"exit_offense" | "entry_offense" | "zone_retention" | "entry_prevention"}.one_second_probability`
  | `context.${"teammates" | "opponents"}.usage_minutes_per_appearance`
  | "descriptive.usage.minutes_per_appearance"
  | `descriptive.scoring.${"ev" | "pp"}.primary_points_per60`
  | `microstats.${keyof SkaterMicrostats}`
  | `goalie.${"ev" | "pk"}.${typeof goalieFields[number]}`;

// one fixed card/table order; these are existing selectors, never additive terms.
export const comparativeTileIds = [
  "ledger.five_on_five_offense.league_goals",
  "ledger.five_on_five_defense.league_goals",
  "ledger.power_play_offense.league_goals",
  "ledger.penalty_kill_defense.league_goals",
  "ledger.finishing.league_goals",
  "goals60",
  "primaryAssists60",
  "ledger.penalties_combined.league_goals",
  "context.opponents.usage_minutes_per_appearance",
  "context.teammates.usage_minutes_per_appearance",
] as const satisfies readonly AnalysisMetricId[];

export type AnalysisMetric = {
  readonly id: AnalysisMetricId;
  readonly kind: Person["kind"];
  readonly family: LeagueSelection["family"];
  readonly publicationFamily: Family | "observed";
  readonly strength: LeagueSelection["strength"];
  readonly group: string;
  readonly label: string;
  readonly unit: string;
  readonly displayUnit: string;
  readonly displayScale: number;
  readonly population: string;
  readonly construction: string;
  readonly numericReference: string;
  readonly rankDirection: "increasing";
  readonly standingPolicy: "percentile" | "raw_only";
  readonly cutoff: "general" | "specialty" | "census";
  readonly qualificationLabel: string;
  readonly observedPopulation?: "personal" | "onIce";
  readonly quantityPath?: typeof QuantityPath.Type;
  readonly selectionStrength?: typeof import("../shared/player-analysis").ExecutionStrength.Type;
  readonly select: (inputs: ValueInputs) => SelectedValue;
};

export type AnalysisDatum = {
  readonly person: Person | null;
  readonly playerId: string;
  readonly season: string;
  readonly metric: AnalysisMetric;
  readonly value: number | null;
  readonly status: "provided" | "not_computed" | "absent" | "unavailable";
  readonly reason: string | null;
  readonly original: Estimate | FactValue | null;
  readonly support: Support | null;
  readonly componentSupport: ComponentSupport;
  readonly reference_panel: Execution["reference_panel"] | null;
  readonly coefficient_support: Execution["coefficient_support"] | null;
  readonly paired_evidence: Execution["paired_evidence"] | null;
  readonly qualificationSeconds: number | null;
  readonly qualificationBasis: string;
  readonly methods: readonly Method[];
  readonly sources: readonly Source[];
  readonly semanticKey: string;
  readonly guideSemanticKey: string;
  readonly semanticIdentityKnown: boolean;
  readonly supportPolicyId: string;
  readonly referenceId: string;
  readonly construction: string;
  readonly population: string;
  readonly numericReference: string;
  readonly findings: readonly Method["assessment"]["findings"][number][];
  readonly workload: unknown;
  readonly reasonCodes: readonly string[];
  readonly observedSupport: PlayerSummary["personal"] | PlayerSummary["metrics"] | null;
};

// these are typed result envelopes, not a second publication schema.
type ValueInputs = {
  observed: Result<PlayerSummary>;
  spatial: (strength: "5v5" | "pp" | "pk") => Result<Spatial>;
  execution: Result<Execution>;
  shootiness: Result<Shootiness>;
  penalties: Result<Penalties>;
  territory: Result<Territory>;
  ledger: Result<Ledger>;
  context: Result<SkaterContext>;
  descriptive: Result<SkaterDescriptive>;
  reportedUsage: Result<typeof ReportedUsage.Type>;
  microstats: Result<SkaterMicrostats>;
  goalie: (strength: "ev" | "pk") => Result<Goalie>;
};

type SelectedValue = {
  readonly original: Estimate | FactValue | null;
  readonly value: number | null;
  readonly status: AnalysisDatum["status"];
  readonly reason: string | null;
  readonly support: Support | null;
  readonly componentSupport?: ComponentSupport;
  readonly reference_panel?: Execution["reference_panel"];
  readonly coefficient_support?: Execution["coefficient_support"];
  readonly paired_evidence?: Execution["paired_evidence"];
  readonly qualificationSeconds: number | null;
  readonly qualificationBasis: string;
  readonly methodId?: string;
  readonly sourceId?: string;
  readonly construction?: string;
  readonly workload?: unknown;
  readonly observedSupport?: PlayerSummary["personal"] | PlayerSummary["metrics"];
};

const pending = (explanation = "family is not computed"): Result<never> => ({
  availability: "not_computed",
  explanation,
  data: null
});

function fromResult<T>(result: Result<T>, read: (data: T) => SelectedValue): SelectedValue {
  if (result.availability === "provided") return read(result.data);
  return {
    original: null,
    value: null,
    status: result.availability,
    reason: result.explanation,
    support: null,
    qualificationSeconds: null,
    qualificationBasis: "unavailable"
  };
}

const estimate = (
  value: Estimate,
  support: Support,
  methodId: string,
  qualificationBasis: string,
): SelectedValue => ({
  original: value,
  value: value.value,
  status: value.value === null ? "unavailable" : "provided",
  reason: value.unavailable_reason,
  support,
  qualificationSeconds: support.included_seconds,
  qualificationBasis,
  methodId
});

const definition = (
  metric: Omit<AnalysisMetric, "rankDirection" | "displayScale" | "displayUnit" | "standingPolicy"> & Partial<Pick<AnalysisMetric, "standingPolicy">>,
): AnalysisMetric => ({
  ...metric,
  rankDirection: "increasing",
  standingPolicy: metric.standingPolicy ?? "percentile",
  displayScale: metric.unit === "fraction" ? 100 : 1,
  displayUnit: metric.unit === "fraction"
    ? metric.id.endsWith("difference") ? "percentage points" : "%"
    : metric.unit === "goals_per_reference_basket" ? "goals per common workload"
    : metric.unit === "goals_per100_attempts" ? "goals per 100 attempts"
    : metric.unit === "goals_per100_assisted_opportunities" ? "goals per 100 setup opportunities"
    : metric.unit === "minutes_per_appearance" ? "min per appearance"
    : metric.unit === "per60" ? "per 60 min"
    : metric.unit
});

const title = (field: string) => field.replaceAll("_", " ");

const base = {
  kind: "skater",
  family: "overview",
  strength: null,
  construction: "modeled",
  numericReference: "published model reference",
  cutoff: "general",
  qualificationLabel: "modeled family support"
} as const;

const observed = observedMetrics.map(metric => definition({
  ...base,
  publicationFamily: "observed",
  id: metric.key,
  observedPopulation: metric.population,
  family: "observed",
  strength: "5v5",
  group: "observed 5v5",
  label: metric.label,
  unit: "per60",
  population: metric.population === "personal"
    ? "matched personal 5v5 credits"
    : "matched on-ice 5v5 attempts",
  construction: "recorded",
  numericReference: "observed rate",
  qualificationLabel: metric.population === "personal"
    ? "matched personal 5v5 credits"
    : "matched on-ice 5v5 attempts",
  select: inputs => fromResult(inputs.observed, player => {
    const support = metric.population === "personal" ? player.personal : player.metrics;
    const value = metric.rate(player);
    return {
      original: null,
      value,
      status: value === null ? "unavailable" : "provided",
      reason: value === null ? support.reason_codes.join(", ") || "quantity unavailable" : null,
      support: null,
      observedSupport: support,
      qualificationSeconds: support.included_seconds,
      qualificationBasis: `${metric.population === "personal" ? "personal" : "metrics"}.included_seconds`
    };
  })
}));

const spatialRoles = [
  ["5v5", ["offense", "defense"]],
  ["pp", ["offense"]],
  ["pk", ["defense"]],
] as const;

const spatial = spatialRoles.flatMap(([strength, roles]) =>
  roles.flatMap(role =>
    ([
      "attempts_per60",
      "xg_per60",
      "attempts_relative_percent",
      "xg_relative_percent",
    ] as const).map(quantity => {
      const field = `${role}_${quantity}` as const;
      return definition({
        ...base,
        publicationFamily: "spatial",
        id: `spatial.${strength}.${field}` as AnalysisMetricId,
        quantityPath: `skater_spatial.${field}`,
        group: `spatial ${strength}`,
        label: title(field),
        unit: quantity.endsWith("relative_percent")
          ? "%"
          : quantity === "attempts_per60"
            ? "attempts_per60"
            : "xg_per60",
        population: `${strength} ${role}`,
        qualificationLabel: `${strength} spatial support`,
        numericReference: "published neutral spatial forecast",
        cutoff: strength === "5v5" ? "general" : "specialty",
        select: inputs => fromResult(
          inputs.spatial(strength),
          data => estimate(
            data[field],
            data.support,
            data.method_id,
            `spatial.${strength}.support.included_seconds`
          )
        )
      });
    }),
  ),
);

const executionFields = [
  "finishing_goals_per100_attempts",
  "setting_goals_per100_assisted_opportunities",
  "avoid_block_probability",
  "on_net_probability",
  "recorded_stop_probability",
  "conversion_probability",
  "avoid_block_probability_difference",
  "on_net_probability_difference",
  "recorded_stop_probability_difference",
  "conversion_probability_difference",
] as const;

const strengths = ["5v5", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4"] as const;

const execution = strengths.flatMap(strength =>
  executionFields.map(field => definition({
    ...base,
    publicationFamily: "execution",
    id: `execution.${strength}.${field}`,
    quantityPath: `skater_execution.${field}`,
    selectionStrength: strength,
    family: strength === "5v5" ? "overview" : "execution",
    strength: strength === "5v5" ? null : strength,
    group: `execution ${strength}`,
    label: field === "setting_goals_per100_assisted_opportunities"
      ? "setting goals per 100 setup opportunities"
      : field === "finishing_goals_per100_attempts"
        ? "finishing goals per 100 attempts"
        : title(field),
    unit: field.includes("probability")
      ? "fraction"
      : field === "finishing_goals_per100_attempts"
        ? "goals_per100_attempts"
        : "goals_per100_assisted_opportunities",
    population: `${strength} ${field.startsWith("setting") ? "inferred setup opportunities" : "attempt stages"}`,
    qualificationLabel: `${strength} current-season exact-strength on-ice participation`,
    numericReference: field.includes("probability") && !field.endsWith("difference")
      ? "conditional probability"
      : "reference-execution opportunity; fitted seasonal common panel",
    cutoff: strength === "5v5" ? "general" : "specialty",
    select: inputs => fromResult(
      inputs.execution,
      data => ({
        ...estimate(data[field], data.support[field], data.method_id,
          `${strength} current-season exact-strength focal on-ice participation with both goalies; cohort qualification, not panel or likelihood exposure`),
        reference_panel: data.reference_panel,
        coefficient_support: data.coefficient_support,
        paired_evidence: data.paired_evidence,
      })
    )
  })),
);

const shootiness = strengths.flatMap(strength =>
  (["probability", "difference"] as const).map(field => definition({
    ...base,
    publicationFamily: "shootiness",
    id: `shootiness.${strength}.${field}`,
    quantityPath: `skater_shootiness.${field}`,
    selectionStrength: strength,
    family: strength === "5v5" ? "overview" : "shootiness",
    strength: strength === "5v5" ? null : strength,
    group: `shootiness ${strength}`,
    label: `shootiness ${title(field)}`,
    unit: "fraction",
    population: `${strength} shooting opportunities`,
    qualificationLabel: `${strength} shootiness support`,
    numericReference: field === "probability"
      ? "conditional probability"
      : "published neutral shootiness forecast",
    cutoff: strength === "5v5" ? "general" : "specialty",
    select: inputs => fromResult(
      inputs.shootiness,
      data => estimate(
        data[field],
        data.support,
        data.method_id,
        `shootiness.${strength}.support.included_seconds`
      )
    )
  })),
);

const penalties = ([
  "drawn_per60",
  "taken_per60",
  "drawn_value_per60",
  "taken_value_per60",
] as const).map(field => definition({
  ...base,
  publicationFamily: "penalties",
  id: `penalties.${field}`,
  quantityPath: `skater_penalties.${field}`,
  group: "modeled penalties",
  label: `penalties ${title(field)}`,
  unit: field.includes("value") ? "goals_per60" : "penalties_per60",
  population: "modeled penalty opportunities",
  qualificationLabel: "modeled penalty support",
  select: inputs => fromResult(
    inputs.penalties,
    data => estimate(
      data[field],
      data.support,
      data.method_id,
      "penalties.support.included_seconds"
    )
  )
}));

const territory = [
  ...(["ice_won_goals_per_basket", "ice_lost_goals_per_basket"] as const).map(field => definition({
    ...base,
    publicationFamily: "territory",
    id: `territory.${field}`,
    quantityPath: `skater_territory.${field}`,
    group: "territory",
    label: title(field),
    unit: "goals_per_basket",
    population: "territory opportunities",
    qualificationLabel: "territory support",
    select: inputs => fromResult(
      inputs.territory,
      data => estimate(
        data[field],
        data.support,
        data.method_id,
        "territory.support.included_seconds"
      )
    )
  })),
  ...(["exit_offense", "entry_offense", "zone_retention", "entry_prevention"] as const).map(field => definition({
    ...base,
    publicationFamily: "territory",
    id: `territory.${field}.one_second_probability`,
    quantityPath: `skater_territory.${field}.one_second_probability`,
    group: "territory",
    label: `${title(field)} one second probability`,
    unit: "fraction",
    population: `territory ${title(field)} opportunities`,
    qualificationLabel: `territory ${title(field)} support`,
    numericReference: "one second transition probability",
    select: inputs => fromResult(
      inputs.territory,
      data => estimate(
        data[field].one_second_probability,
        data[field].support,
        data.method_id,
        `territory.${field}.support.included_seconds`
      )
    )
  })),
];

const context = (["teammates", "opponents"] as const).map(field => definition({
  ...base,
  publicationFamily: "descriptive",
  id: `context.${field}.usage_minutes_per_appearance`,
  group: "counterpart usage",
  label: `${field} usage per appearance`,
  unit: "minutes_per_appearance",
  population: `known-weight ${field} usage`,
  qualificationLabel: `${field} known-weight focal elapsed coverage`,
  construction: "reconstructed",
  numericReference: "published counterpart usage",
  select: inputs => fromResult(inputs.context, data => {
    const selected = data[field];
    const value = estimate(
      selected.usage_minutes_per_appearance,
      selected.coverage,
      "",
      `context.${field}.coverage.included_seconds`,
    );
    return {
      ...value,
      methodId: undefined,
      sourceId: data.provenance.id,
      workload: {
        known_slot_seconds: selected.known_slot_seconds,
        all_slot_seconds: selected.all_slot_seconds,
        unique_counterparts: selected.unique_counterparts
      },
      qualificationSeconds: selected.known_slot_seconds > 0 ? selected.coverage.included_seconds : null
    };
  })
}));

export const descriptiveMetricIds = [
  "descriptive.usage.minutes_per_appearance",
  "descriptive.scoring.ev.primary_points_per60",
  "descriptive.scoring.pp.primary_points_per60",
] as const satisfies readonly AnalysisMetricId[];

const descriptive = descriptiveMetricIds.map(id => {
  const strength = id === descriptiveMetricIds[1] ? "ev" : "pp";
  const usage = id === descriptiveMetricIds[0];
  return definition({
    ...base,
    id,
    family: "descriptive",
    publicationFamily: "descriptive",
    standingPolicy: "raw_only",
    group: "recorded descriptive",
    label: usage ? "reported minutes per appearance" : `${strength} primary points per 60`,
    unit: usage ? "minutes_per_appearance" : "per60",
    population: usage ? "reported all-strength positive-toi appearances" : `${strength} matched personal scoring`,
    qualificationLabel: usage ? "observed on-ice 5v5 included seconds (viewing population)" : `${strength} scoring seconds`,
    construction: "recorded",
    numericReference: "published recorded value",
    cutoff: usage || strength === "ev" ? "general" : "specialty",
    select: inputs => usage
      ? fromResult(inputs.reportedUsage, data => ({
          ...estimate(data.minutes_per_appearance, data.support, "", "overview.observed.metrics.included_seconds"),
          methodId: undefined,
          sourceId: data.provenance.id,
          qualificationSeconds: inputs.observed.data?.metrics.included_seconds ?? null,
        }))
      : fromResult(inputs.descriptive, data => {
      const group = data.scoring_by_strength[strength];
      const value = group.primary_points_per60;
      return {
        ...estimate(value, group.support, "", `descriptive.scoring_by_strength.${strength}.seconds`),
        methodId: undefined,
        sourceId: data.provenance.id,
        qualificationSeconds: group.seconds,
      };
    }),
  });
});

const microstatFields = [
  "goals_per60",
  "primary_assists_per60",
  "unblocked_attempts_per60",
  "hits_per60",
  "reference_xg_per60",
  "blocked_attempt_share",
  "primary_pass_xg_per60",
  "primary_shot_assists_per60",
  "in_zone_attempts_per60",
  "rush_attempts_per60",
  "high_danger_pass_attempts_per60",
  "in_zone_shot_assists_per60",
  "rush_shot_assists_per60",
  "high_danger_passes_per60",
  "zone_entries_per60",
  "possession_entries_per60",
  "zone_exits_per60",
  "possession_exits_per60",
  "forecheck_involvements_per60",
  "defensive_zone_touches_per60",
  "pass_exits_per60",
  "carry_exits_per60",
  "defensive_zone_retrievals_per60",
  "successful_retrievals_per60",
  "shot_assisting_passes_per60",
  "puck_management_xga_saved_per100_plays",
  "entry_denial_fraction",
  "possession_entry_denial_fraction",
  "skating_max_speed_mph",
  "skating_bursts_over20_count",
] as const satisfies readonly (keyof SkaterMicrostats)[];

const microstats = microstatFields.map(field => definition({
  ...base,
  publicationFamily: "microstats",
  id: `microstats.${field}`,
  quantityPath: field === "reference_xg_per60" ||
    field === "primary_pass_xg_per60" ||
    field === "puck_management_xga_saved_per100_plays"
    ? `skater_microstats.${field}`
    : undefined,
  family: "microstats",
  group: "microstats",
  label: title(field),
  unit: field === "skating_max_speed_mph"
    ? "mph"
    : field === "skating_bursts_over20_count"
      ? "count"
      : field === "puck_management_xga_saved_per100_plays"
        ? "xga_saved_per100_plays"
        : field === "blocked_attempt_share" || field.endsWith("fraction")
          ? "fraction"
          : "per60",
  population: `published ${field} window`,
  qualificationLabel: `${title(field)} own source window`,
  construction: "source-backed",
  numericReference: "published source window",
  cutoff: field.startsWith("skating_") ? "census" : "general",
  select: inputs => fromResult(inputs.microstats, data => {
    const fact = data[field];
    return {
      ...estimate(fact, fact.support, "", `microstats.${field}.support.included_seconds`),
      methodId: fact.provenance.kind === "method" ? fact.provenance.id : undefined,
      sourceId: fact.provenance.kind === "source" ? fact.provenance.id : undefined,
      construction: fact.construction
    };
  })
}));

const goalieFields = [
  "stopping_goals_per100_on_net",
  "miss_probability",
  "recorded_stop_probability",
  "conversion_probability",
  "recorded_reattempt_probability",
  "reattempt_neutral_goal_probability",
  "followup_danger",
  "miss_probability_difference",
  "recorded_stop_probability_difference",
  "conversion_probability_difference",
  "recorded_reattempt_probability_difference",
  "reattempt_neutral_goal_probability_difference",
  "followup_danger_difference",
] as const;

const goalie = (["ev", "pk"] as const).flatMap(strength =>
  goalieFields.map(field => definition({
    ...base,
    publicationFamily: "goalie",
    id: `goalie.${strength}.${field}`,
    quantityPath: `goalie_result.${field}`,
    kind: "goalie",
    group: `goalie ${strength}`,
    label: title(field),
    unit: field === "stopping_goals_per100_on_net" ? "goals_per100_on_net" : "fraction",
    population: `goalie ${strength} conditional opportunities`,
    qualificationLabel: `goalie ${strength} ${title(field)} support`,
    numericReference: field.endsWith("difference") || field === "stopping_goals_per100_on_net"
      ? "published neutral goalie forecast"
      : "conditional probability",
    cutoff: strength === "ev" ? "general" : "specialty",
    select: inputs => fromResult(
      inputs.goalie(strength),
      data => estimate(
        data[field],
        data.support[field],
        data.method_id,
        `goalie.${strength}.support.${field}.included_seconds`
      )
    )
  })),
);

const ledgerTerms = [
  "five_on_five_offense",
  "five_on_five_defense",
  "power_play_offense",
  "penalty_kill_defense",
  "finishing",
  "setting",
  "penalties_drawn",
  "penalties_taken",
  "ice_won",
  "ice_lost",
] as const;
type LedgerTerm = typeof ledgerTerms[number];

function ledgerSupport(inputs: ValueInputs, term: LedgerTerm): {
  support: Support | null;
  reason: string | null;
} {
  let result: Result<unknown>;
  let support: Support | null = null;
  switch (term) {
    case "five_on_five_offense":
    case "five_on_five_defense": {
      const value = inputs.spatial("5v5");
      result = value;
      if (value.availability === "provided") support = value.data.support;
      break;
    }
    case "power_play_offense": {
      const value = inputs.spatial("pp");
      result = value;
      if (value.availability === "provided") support = value.data.support;
      break;
    }
    case "penalty_kill_defense": {
      const value = inputs.spatial("pk");
      result = value;
      if (value.availability === "provided") support = value.data.support;
      break;
    }
    case "finishing":
    case "setting":
      result = inputs.execution;
      if (inputs.execution.availability === "provided")
        support = inputs.execution.data.support[
          term === "finishing"
            ? "finishing_goals_per100_attempts"
            : "setting_goals_per100_assisted_opportunities"
        ];
      break;
    case "penalties_drawn":
    case "penalties_taken":
      result = inputs.penalties;
      if (inputs.penalties.availability === "provided") support = inputs.penalties.data.support;
      break;
    case "ice_won":
    case "ice_lost":
      result = inputs.territory;
      if (inputs.territory.availability === "provided") support = inputs.territory.data.support;
      break;
  }
  return support
    ? {
        support,
        reason: null
      }
    : {
        support: null,
        reason: result.explanation ?? "support unavailable"
      };
}

const ledger = (["league", "replacement"] as const).flatMap(reference =>
  (["total", ...ledgerTerms, "penalties_combined"] as const).map(term => definition({
    ...base,
    publicationFamily: "ledger",
    id: term === "total" ? `ledger.${reference}_total` : `ledger.${term}.${reference}_goals`,
    quantityPath: term === "total"
      ? `value_ledger.${reference}_total`
      : term === "penalties_combined"
        ? `value_ledger.penalties_combined.${reference}_goals`
        : `value_ledger.components.${term}.${reference}_goals`,
    group: `ledger ${reference}`,
    label: `${reference} ${title(term)}`,
    unit: "goals_per_reference_basket",
    population: "published standardized workload basket",
    qualificationLabel: term === "total" || term === "finishing"
      ? "matched on-ice 5v5 attempts"
      : term === "five_on_five_offense" || term === "five_on_five_defense"
        ? "5v5 spatial support"
        : term === "power_play_offense"
          ? "pp spatial support"
          : term === "penalty_kill_defense"
            ? "pk spatial support"
            : term === "setting"
              ? "5v5 setting assisted-opportunity support"
              : term === "ice_won" || term === "ice_lost"
                ? "territory support"
                : "modeled penalty support",
    construction: "model_valued",
    numericReference: reference === "league" ? "published league reference" : "published replacement reference",
    cutoff: term === "power_play_offense" || term === "penalty_kill_defense" ? "specialty" : "general",
    select: inputs => fromResult(inputs.ledger, data => {
      const value = term === "total"
        ? data[`${reference}_total`]
        : term === "penalties_combined"
          ? data.penalties_combined[`${reference}_goals`]
          : data.components[term][`${reference}_goals`];
      const terms = term === "total"
        ? ledgerTerms
        : term === "penalties_combined"
          ? ["penalties_drawn", "penalties_taken"] as const
          : [term];
      const componentSupport: Record<string, {
        support: Support;
        reason: null;
      } | {
        support: null;
        reason: string;
      }> = {};
      for (const component of terms) {
        const selected = ledgerSupport(inputs, component);
        componentSupport[component] = selected.support
          ? {
              support: selected.support,
              reason: null
            }
          : {
              support: null,
              reason: selected.reason!
            };
      }
      const headline = term === "total" || term === "finishing";
      const support = term === "penalties_combined"
        ? ledgerSupport(inputs, "penalties_drawn").support
        : term === "total"
          ? null
          : ledgerSupport(inputs, term).support;
      return {
        original: value,
        value: value.value,
        status: value.value === null ? "unavailable" : "provided",
        reason: value.unavailable_reason,
        support: null,
        componentSupport,
        methodId: data.method_id,
        qualificationSeconds: headline
          ? inputs.observed.data?.metrics.included_seconds ?? null
          : support?.included_seconds ?? null,
        qualificationBasis: headline
          ? "overview.observed.metrics.included_seconds"
          : term === "five_on_five_offense" || term === "five_on_five_defense"
            ? "spatial.5v5.support.included_seconds"
            : term === "power_play_offense"
              ? "spatial.pp.support.included_seconds"
              : term === "penalty_kill_defense"
                ? "spatial.pk.support.included_seconds"
                : term === "setting"
                  ? "execution.5v5.support.setting_goals_per100_assisted_opportunities.included_seconds"
                  : term === "ice_won" || term === "ice_lost"
                    ? "territory.support.included_seconds"
                    : "penalties.support.included_seconds",
        workload: data.reference_minutes
      };
    })
  })),
);

export const analysisMetrics: readonly AnalysisMetric[] = [
  ...observed,
  ...ledger,
  ...spatial,
  ...execution,
  ...shootiness,
  ...penalties,
  ...territory,
  ...context,
  ...descriptive,
  ...microstats,
  ...goalie,
];

export const analysisMetric = (id: string): AnalysisMetric | undefined =>
  analysisMetrics.find(metric => metric.id === id);

export const defaultAnalysisMetric = (kind: Person["kind"]): AnalysisMetric =>
  kind === "goalie" ? goalie[0] : observed[0];

function emptyInputs(explanation?: string): ValueInputs {
  const unavailable = pending(explanation);
  return {
    observed: unavailable,
    spatial: () => unavailable,
    execution: unavailable,
    shootiness: unavailable,
    penalties: unavailable,
    territory: unavailable,
    ledger: unavailable,
    context: unavailable,
    descriptive: unavailable,
    reportedUsage: unavailable,
    microstats: unavailable,
    goalie: () => unavailable
  };
}

function historyInputs(families: PlayerFamilies, metric: AnalysisMetric): ValueInputs {
  if ("availability" in families) {
    const absent = {
      availability: "absent",
      data: null,
      explanation: families.explanation
    } as const;
    return {
      ...emptyInputs(),
      observed: absent,
      spatial: () => absent,
      execution: absent,
      shootiness: absent,
      penalties: absent,
      territory: absent,
      ledger: absent,
      context: absent,
      descriptive: absent,
      reportedUsage: absent,
      microstats: absent,
      goalie: () => absent
    };
  }
  if (families.kind === "goalie") return {
    ...emptyInputs(),
    goalie: strength => families.goalie.availability === "provided"
      ? families.goalie.data.find(row => row.strength === strength)?.result ?? pending("strength is not computed")
      : families.goalie
  };
  return {
    observed: families.observed,
    spatial: strength => families.spatial.availability === "provided"
      ? families.spatial.data.find(row => row.strength === strength)?.result ?? pending("strength is not computed")
      : families.spatial,
    execution: families.execution.availability === "provided"
      ? families.execution.data.find(
          row => row.strength === (metric.selectionStrength ?? "5v5"),
        )?.result ?? pending("strength is not computed")
      : families.execution,
    shootiness: families.shootiness.availability === "provided"
      ? families.shootiness.data.find(
          row => row.strength === (metric.selectionStrength ?? "5v5"),
        )?.result ?? pending("strength is not computed")
      : families.shootiness,
    penalties: families.penalties,
    territory: families.territory,
    ledger: families.ledger,
    context: families.context,
    descriptive: families.descriptive,
    reportedUsage: families.descriptive.availability === "provided"
      ? { availability: "provided", data: families.descriptive.data.reported_usage, explanation: null }
      : families.descriptive,
    microstats: families.microstats,
    goalie: () => pending("not applicable to skaters")
  };
}

function datum(
  person: Person | null,
  playerId: string,
  season: string,
  catalogs: AnalysisCatalogs,
  metric: AnalysisMetric,
  inputs: ValueInputs,
): AnalysisDatum {
  const selected = metric.select(inputs);
  const methods: Method[] = [];
  const sources: Source[] = [];
  if (selected.methodId) {
    const method = catalogs.methods[selected.methodId];
    if (!method) throw new Error(`unresolved method ${selected.methodId}`);
    methods.push(method);
  }
  if (selected.sourceId) {
    const source = catalogs.sources[selected.sourceId];
    if (!source) throw new Error(`unresolved source ${selected.sourceId}`);
    sources.push(source);
  }
  const method = methods[0];
  const source = sources[0];
  const supportPolicyId = metric.observedPopulation === "personal"
    ? catalogs.publication.personal_population_version
    : metric.observedPopulation === "onIce"
      ? catalogs.publication.population_version
      : method?.support_policy_id ?? `selected_field.${metric.id}.published_support.v1`;
  const referenceId = method?.reference_id ?? "";
  const construction = selected.construction ?? source?.construction ?? metric.construction;
  const population = source?.population ?? method?.population ?? metric.population;
  const numericReference = method?.reference ?? metric.numericReference;
  const semanticKey = JSON.stringify([
    metric.id,
    metric.unit,
    metric.population,
    construction,
    metric.numericReference,
    ...(method ? [[method.recipe_id, method.reference_id, method.support_policy_id]] : []),
    ...(source ? [[source.construction, source.population, source.definition, supportPolicyId]] : []),
    ...(metric.observedPopulation ? [supportPolicyId] : []),
  ]);
  for (const reference of selected.original?.reason_detail?.evidence ?? []) {
    if (reference.kind === "method" && !methods.some(entry => entry.method_id === reference.id)) {
      const evidence = catalogs.methods[reference.id];
      if (!evidence) throw new Error(`unresolved method ${reference.id}`);
      methods.push(evidence);
    }
    if (reference.kind === "source" && !sources.some(entry => entry.source_id === reference.id)) {
      const evidence = catalogs.sources[reference.id];
      if (!evidence) throw new Error(`unresolved source ${reference.id}`);
      sources.push(evidence);
    }
  }
  const quantityPath = metric.quantityPath;
  const findings = quantityPath
    ? methods.flatMap(entry =>
        entry.assessment.findings.filter(finding => finding.quantities.includes(quantityPath)),
      )
    : [];
  return {
    person,
    playerId,
    season,
    metric,
    value: selected.value,
    status: selected.status,
    reason: selected.reason,
    original: selected.original,
    support: selected.support,
    componentSupport: selected.componentSupport ?? {},
    reference_panel: selected.reference_panel ?? null,
    coefficient_support: selected.coefficient_support ?? null,
    paired_evidence: selected.paired_evidence ?? null,
    qualificationSeconds: selected.qualificationSeconds,
    qualificationBasis: selected.qualificationBasis,
    methods,
    sources,
    semanticKey,
    guideSemanticKey: metric.id === descriptiveMetricIds[0]
      ? JSON.stringify([semanticKey, "overview.observed.metrics.included_seconds", catalogs.publication.population_version])
      : semanticKey,
    semanticIdentityKnown: Boolean(method || source || metric.observedPopulation),
    supportPolicyId,
    referenceId,
    construction,
    population,
    numericReference,
    findings,
    workload: selected.workload ?? null,
    reasonCodes: selected.observedSupport?.reason_codes ?? [],
    observedSupport: selected.observedSupport ?? null
  };
}

export function selectHistoryValue(
  row: PlayerResponse["history"][number],
  catalogs: AnalysisCatalogs,
  metric: AnalysisMetric,
  playerId: string,
): AnalysisDatum {
  if (row.families.kind !== metric.kind) throw new Error("selected quantity has the wrong person kind");
  return datum(row.person, playerId, row.season.season, catalogs, metric, historyInputs(row.families, metric));
}

// overview carries the observed summary unchanged; its identity must agree
// before a recorded value or its exposure can be attributed to this person.
export function checkObservedIdentity(person: Person, summary: PlayerSummary): void {
  if (
    person.player_id !== summary.player_id ||
    person.display_name !== summary.display_name ||
    person.reported_position !== summary.reported_position ||
    !preservesObservedAffiliations(person.teams, summary.teams)
  )
    throw new Error(`player ${person.player_id}: observed summary identity differs from its overview person`);
}

export function selectLeagueValues(
  response: LeagueResponse,
  metric: AnalysisMetric,
  overview?: Extract<LeagueResponse, { kind: "skater"; family: "overview" }>,
): AnalysisDatum[] {
  // the overview already contains the exact recorded 5v5 envelope. keep the
  // metric and its observed population semantics unchanged while selecting it.
  const usageOverview = response.kind === "skater" && response.family === "overview" && response.strength === null && metric.id === descriptiveMetricIds[0];
  const observedOverview = response.kind === "skater" && response.family === "overview" &&
    response.strength === null && metric.kind === "skater" &&
    metric.family === "observed" && metric.strength === "5v5" &&
    observed.some(field => field.id === metric.id);
  if (
    response.kind !== metric.kind ||
    !observedOverview && !usageOverview && (response.family !== metric.family || response.strength !== metric.strength)
  )
    throw new Error("league response does not match the selected quantity request");
  const make = (person: Person, inputs: ValueInputs) => {
    if (inputs.observed.availability === "provided")
      checkObservedIdentity(person, inputs.observed.data);
    return datum(person, person.player_id, response.season.season, response, metric, inputs);
  };
  switch (response.family) {
    case "overview":
      if (response.kind === "goalie") return response.players.map(row => {
        if (row.result.availability !== "provided") return make(row.person, emptyInputs(row.result.explanation));
        const data = row.result.data;
        return make(row.person, {
          ...emptyInputs(),
          goalie: strength => data.goalie[strength]
        });
      });
      return response.players.map(row => {
        if (row.result.availability !== "provided") return make(row.person, emptyInputs(row.result.explanation));
        const data = row.result.data;
        return make(row.person, {
          observed: data.observed,
          spatial: strength => data.spatial[strength === "5v5" ? "five_on_five" : strength],
          execution: data.execution,
          shootiness: data.shootiness,
          penalties: data.penalties,
          territory: data.territory,
          ledger: data.ledger,
          context: data.context,
          descriptive: pending(),
          reportedUsage: data.reported_usage,
          microstats: pending(),
          goalie: () => pending()
        });
      });
    case "descriptive":
      return response.players.map(row => {
        const member = overview?.players.find(member => member.person.player_id === row.person.player_id);
        return make(row.person, {
          ...emptyInputs(),
          descriptive: row.result,
          reportedUsage: row.result.availability === "provided"
            ? { availability: "provided", data: row.result.data.reported_usage, explanation: null }
            : row.result,
          observed: member?.result.availability === "provided" ? member.result.data.observed : pending(),
        });
      });
    case "observed":
      return response.players.map(row => make(row.person, {
        ...emptyInputs(),
        observed: row.result
      }));
    case "execution":
      return response.players.map(row => make(row.person, {
        ...emptyInputs(),
        execution: row.result
      }));
    case "shootiness":
      return response.players.map(row => make(row.person, {
        ...emptyInputs(),
        shootiness: row.result
      }));
    case "microstats":
      return response.players.map(row => make(row.person, {
        ...emptyInputs(),
        microstats: row.result
      }));
    default:
      throw new Error("selected quantity does not use this endpoint");
  }
}

// a left join preserves overview identity when a requested scalar family has no
// row. this is an unavailable view datum, never a fabricated exchange result.
export function selectMissingLeagueValue(response: LeagueResponse, metric: AnalysisMetric, person: Person): AnalysisDatum {
  if (person.kind !== response.kind || person.season !== response.season.season ||
    response.kind !== metric.kind || response.family !== metric.family || response.strength !== metric.strength)
    throw new Error("missing family row does not match the selected quantity request");
  return datum(person, person.player_id, response.season.season, response, metric,
    emptyInputs("no published family row for this player-season"));
}
