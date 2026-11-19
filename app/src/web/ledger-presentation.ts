import type { AnalysisDatum, AnalysisMetric } from "./analysis-values";

export const ledgerPresentation = [
  ["5v5 offense", "five_on_five_offense", "spatial.5v5.offense_xg_per60"],
  ["5v5 defense", "five_on_five_defense", "spatial.5v5.defense_xg_per60"],
  ["pp offense", "power_play_offense", "spatial.pp.offense_xg_per60"],
  ["pk defense", "penalty_kill_defense", "spatial.pk.defense_xg_per60"],
  ["finishing", "finishing", "execution.5v5.finishing_goals_per100_attempts"],
  [
    "inferred setting",
    "setting",
    "execution.5v5.setting_goals_per100_assisted_opportunities",
  ],
  ["drawing", "penalties_drawn", "penalties.drawn_value_per60"],
  ["taking", "penalties_taken", "penalties.taken_value_per60"],
  ["ice won", "ice_won", "territory.ice_won_goals_per_basket"],
  ["ice lost", "ice_lost", "territory.ice_lost_goals_per_basket"],
] as const;

export const ledgerWorkload = "common workload · 1,000 5v5 + 100 pp + 100 pk minutes";
export const ledgerLimits = "experimental index of favorable goals. specialty minutes may be hypothetical. uncertainty is unestimated.";
export const ledgerInteractions = "the index omits creation × own execution and penalty-created minutes × own specialty skill. a supplied total requires all ten terms. combined penalties groups drawing and taking.";

export const isReplacementLedger = (metric: AnalysisMetric) =>
  metric.id === "ledger.replacement_total" ||
  (metric.publicationFamily === "ledger" && metric.id.endsWith(".replacement_goals"));

export function ledgerCoverage(datum: AnalysisDatum): string | null {
  const detail = datum.ledger_detail;
  if (!detail) return null;
  if (detail.depth_position_group === "unknown")
    return "annual depth position unresolved";
  const coverage = detail.depth_reference_coverage!;
  return `depth reference ${detail.depth_position_group} · ${coverage.complete_groups} complete team-position groups · ${coverage.excluded_groups} excluded · ${coverage.member_count} weighted skaters${coverage.available ? "" : " · reference unavailable"}`;
}
