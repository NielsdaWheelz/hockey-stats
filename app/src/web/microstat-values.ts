import type { FactValue, Person } from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import { positionGroup } from "./analysis-cohorts";
import { prepareHistoryPoint, type AnalysisRow } from "./analysis-history";
import { analysisMetric, microstatComponentIds, type AnalysisMetricId } from "./analysis-values";
import type { ProfileView } from "./client";
import type { PeerSettings } from "./explorer";

// layout owns order only. quantity meaning and formatting belong to the catalogue.
type MicrostatId = Extract<AnalysisMetricId, `microstats.${string}`>;
type SlotDefinition = MicrostatId | readonly [MicrostatId, MicrostatId];
const shooting = [
  "microstats.goals_per60", "microstats.reference_xg_per60", "microstats.unblocked_attempts_per60",
  "microstats.in_zone_attempts_per60", "microstats.rush_attempts_per60", "microstats.high_danger_pass_attempts_per60",
] as const satisfies readonly SlotDefinition[];
const passing = [
  "microstats.primary_assists_per60", "microstats.primary_pass_xg_per60", "microstats.primary_shot_assists_per60",
  "microstats.in_zone_shot_assists_per60", "microstats.rush_shot_assists_per60", "microstats.high_danger_passes_per60",
] as const satisfies readonly SlotDefinition[];
const transition = [
  "microstats.zone_entries_per60", "microstats.possession_entries_per60", "microstats.zone_exits_per60", "microstats.possession_exits_per60",
] as const satisfies readonly SlotDefinition[];
const other = [
  ["microstats.skating_max_speed_mph", "microstats.skating_bursts_over20_count"],
  "microstats.forecheck_involvements_per60", "microstats.hits_per60", "microstats.defensive_zone_touches_per60",
] as const satisfies readonly SlotDefinition[];
const defenseTransition = [...transition, "microstats.pass_exits_per60", "microstats.carry_exits_per60"] as const;
const defenseActions = [
  "microstats.defensive_zone_retrievals_per60", "microstats.successful_retrievals_per60",
  "microstats.puck_management_xga_saved_per100_plays", "microstats.entry_denial_fraction",
  "microstats.possession_entry_denial_fraction", "microstats.hits_per60", "microstats.blocked_attempt_share",
] as const satisfies readonly SlotDefinition[];

type MicrostatField = {
  readonly row: AnalysisRow;
  readonly fact: FactValue | null;
  readonly supportKey: string | null;
  readonly evidenceKeys: readonly string[];
  readonly state: string | null;
};
export type MicrostatCardModel = {
  readonly playerId: string;
  readonly person: Person | null;
  readonly historicalPerson: Person | null;
  readonly publication: Publication;
  readonly season: SeasonEvidence;
  readonly settings: PeerSettings;
  readonly layout: "forward" | "defense" | "unknown";
  readonly groups: readonly {
    readonly label: string;
    readonly slots: readonly { readonly id: string; readonly fields: readonly MicrostatField[] }[];
  }[];
  readonly components: readonly AnalysisRow[];
  readonly supports: readonly {
    readonly key: string;
    readonly population: string;
    readonly includedSeconds: number | null;
    readonly coverage: string;
    readonly opportunities: number | null;
  }[];
  readonly evidence: readonly { readonly key: string; readonly id: string; readonly construction: string }[];
};

export function prepareMicrostatCard(profile: ProfileView, settings: PeerSettings): MicrostatCardModel {
  const selected = profile.detail.history.find(year => year.season.season === profile.season.season);
  const microstats = profile.microstatsCohort;
  const overview = profile.overviewCohorts.find(cohort => cohort.season.season === profile.season.season);
  if (!selected || !microstats || !overview) throw new Error("microstat card requires selected-year identity, microstats and overview cohorts");
  const role = positionGroup(selected.person?.reported_position ?? null);
  const layout = role === "f" ? "forward" : role === "d" ? "defense" : "unknown";
  const groups: readonly (readonly [string, readonly SlotDefinition[]])[] = layout === "forward"
    ? [["shooting", shooting], ["passing", passing], ["transition", transition], ["other actions", other]]
    : layout === "defense"
      ? [["shooting", shooting.slice(0, 3)], ["passing", [...passing.slice(0, 3), "microstats.shot_assisting_passes_per60"]], ["transition", defenseTransition], ["defensive actions", defenseActions]]
      : [["shooting", shooting], ["passing", [...passing, "microstats.shot_assisting_passes_per60"]], ["transition", defenseTransition], ["other / actions", [...other, ...defenseActions.filter(id => id !== "microstats.hits_per60")]]];
  const supports: MicrostatCardModel["supports"][number][] = [];
  const supportIdentities: string[] = [];
  const evidence: MicrostatCardModel["evidence"][number][] = [];
  const evidenceIdentities: string[] = [];
  const field = (id: AnalysisMetricId): MicrostatField => {
    const metric = analysisMetric(id)!;
    const row = prepareHistoryPoint({ ...selected, cohort: microstats }, microstats, metric, profile.player_id, settings).point;
    const { datum } = row;
    const fact = datum.original && "denominator_kind" in datum.original ? datum.original : null;
    const evidenceKeys = [
      ...datum.sources.map(source => ({ id: source.source_id, construction: source.construction })),
      ...datum.methods.map(method => ({ id: method.method_id, construction: "model-valued" })),
    ].map(entry => {
      const identity = JSON.stringify(entry);
      let index = evidenceIdentities.indexOf(identity);
      if (index < 0) {
        index = evidence.length;
        evidenceIdentities.push(identity);
        evidence.push({ key: `e${index + 1}`, ...entry });
      }
      return evidence[index].key;
    });
    let supportKey: string | null = null;
    if (datum.value !== null && datum.support) {
      const support = datum.support;
      const coverage = support.unquantified_gap || support.included_seconds === null || support.known_excluded_seconds === null
        ? "partial / unknown coverage"
        : support.known_excluded_seconds > 0 || support.reason_counts.length > 0 ? "partial support" : "included support";
      const entry = {
        population: metric.population,
        includedSeconds: support.included_seconds,
        coverage,
        opportunities: fact?.denominator_kind === "opponent_attempts" ? fact.denominator : null,
      };
      // equal seconds alone do not make two physical populations identical.
      const identity = JSON.stringify([entry, datum.population, support]);
      let index = supportIdentities.indexOf(identity);
      if (index < 0) {
        index = supports.length;
        supportIdentities.push(identity);
        supports.push({ key: `s${index + 1}`, ...entry });
      }
      supportKey = supports[index].key;
    }
    const explanation = fact?.reason_detail?.explanation ?? datum.reason;
    const trackingEvidence = datum.sources.some(source => /track|puck.management/i.test(`${source.label} ${source.definition} ${explanation ?? ""}`));
    let state: string | null = null;
    if (datum.value === null) {
      if (datum.status === "absent") state = "absent season";
      else if (datum.status === "not_computed" || fact?.unavailable_reason === "not_computed") state = `pending computation · ${metric.publicationFamily}`;
      else if (explanation?.includes("skating acquisition deferred; no admitted measurements")) state = "skating deferred";
      else if (fact?.unavailable_reason === "missing_source" && trackingEvidence) state = "tracking unavailable";
      else state = datum.reason?.replaceAll("_", " ") ?? "quantity unavailable";
    }
    return { row, fact, supportKey, evidenceKeys, state };
  };
  return {
    playerId: profile.player_id,
    person: selected.person,
    historicalPerson: profile.detail.history.toSorted((a, b) => a.season.season.localeCompare(b.season.season)).findLast(year => year.person !== null)?.person ?? null,
    publication: profile.publication,
    season: profile.season,
    settings: { ...settings },
    layout,
    groups: groups.map(([label, slots]) => ({ label, slots: slots.map(slot => ({
      id: typeof slot === "string" ? slot.slice("microstats.".length) : "skating",
      fields: (typeof slot === "string" ? [slot] : slot).map(field),
    })) })),
    components: microstatComponentIds.map(id => prepareHistoryPoint({ ...selected, cohort: overview }, overview, analysisMetric(id)!, profile.player_id, settings).point),
    supports,
    evidence,
  };
}
