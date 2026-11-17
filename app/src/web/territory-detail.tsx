import type { SkaterTerritory } from "../shared/player-analysis";
import type { CsvCell } from "./export";

type Evidence = (typeof SkaterTerritory.Type)["evidence"];
const starts = ["DZ", "NZ", "OZ", "on_the_fly"] as const;
const ages = [0, 10, 20, 40, 60, 90] as const;
const roles = [
  "exit_offense",
  "entry_offense",
  "zone_retention",
  "entry_prevention",
] as const;
const number = (value: number | null) =>
  value === null
    ? "unavailable"
    : value.toLocaleString("en-US", { maximumFractionDigits: 6 });

export function territoryNotes(evidence: Evidence): readonly string[] {
  const coverage = evidence.nuisance_coverage;
  const shift = evidence.shift_reference.data;
  return [
    "inferred territory; interpolated movement and a terminal-zone proxy, not tracked entries, possession or actual post-shift goals.",
    "successor value uses goals per 1,000 5v5 minutes. positive ice lost means more against; the later ledger negates it once. four subskills are not additional contributions.",
    `neutral unit: five neutral skaters per side, neutral residual coaches and zero centered context; one focal slot. known-path qualification ${number(evidence.qualification_seconds / 60)} min is distinct from role-specific risk.`,
    `terminal-zone carry ${number(coverage.terminal_carry_slot_seconds)} / ${number(coverage.path_slot_seconds)} path slot-seconds; fraction ${number(coverage.path_slot_seconds > 0 ? coverage.terminal_carry_slot_seconds / coverage.path_slot_seconds : null)}; ${coverage.terminal_tails} physical tails. last location may mislocate the puck.`,
    shift
      ? `common neutral survival: mean ${number(shift.mean_shift_seconds)} seconds; ${number(shift.shifts_per_1000_minutes)} shifts per 1,000 minutes; survival at 90 seconds ${number(shift.survival_at_90)}; tail-time fraction ${number(shift.tail_time_fraction)}.`
      : `shift reference unavailable: ${evidence.shift_reference.reason}.`,
    "fixed substitution, common survival, inferred paths and carried point priors are assumptions. uncertainty is not estimated; optimizer accuracy is unknown.",
  ];
}

export const territoryEvidenceCsvHeaders = [
  "row_type",
  "quantity",
  "start",
  "side",
  "age_lower",
  "value",
  "unit",
  "initial_probability",
  "neutral_end_probability",
  "focal_end_probability",
  "end_difference",
  "reference_id",
  "support",
  "unavailable_reason",
] as const;

export function territoryEvidenceCsvRows(
  evidence: Evidence,
): readonly (readonly CsvCell[])[] {
  const rows: CsvCell[][] = [];
  const shift = evidence.shift_reference.data;
  const successor = evidence.successor_reference.data;
  for (const [i, start] of starts.entries()) {
    rows.push([
      "successor_start",
      "start_distribution",
      start,
      null,
      null,
      null,
      "probability",
      shift?.initial_start_probabilities[i] ?? null,
      shift?.neutral_end_probabilities[i] ?? null,
      shift?.focal_end_probabilities[i] ?? null,
      shift?.end_difference[i] ?? null,
      evidence.reference_id,
      JSON.stringify(evidence.nuisance_coverage.start_counts),
      evidence.shift_reference.reason,
    ]);
    for (const side of ["for", "against"] as const)
      rows.push([
        "successor_value",
        "start_contrast",
        start,
        side,
        null,
        (side === "for"
          ? successor?.for_goals_per_shift
          : successor?.against_goals_per_shift)?.[i] ?? null,
        "goals_per_shift",
        null,
        null,
        null,
        null,
        evidence.reference_id,
        JSON.stringify(
          side === "for"
            ? successor?.for_absolute_terms_goals_per_shift
            : successor?.against_absolute_terms_goals_per_shift,
        ),
        evidence.successor_reference.reason,
      ]);
  }
  for (const [i, age] of ages.entries())
    rows.push([
      "survival_occupancy",
      "neutral_occupancy",
      null,
      null,
      age,
      shift?.neutral_occupancy_seconds[i] ?? null,
      "seconds",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      null,
      evidence.shift_reference.reason,
    ]);
  const coverage = evidence.nuisance_coverage;
  for (const field of [
    "path_slot_seconds",
    "terminal_carry_slot_seconds",
    "whistle_risk_slot_seconds",
    "whistle_incidences",
    "live_end_risk_slot_seconds",
    "live_end_incidences",
    "decidable_whistle_trials",
    "ended_whistle_trials",
    "restart_pairs",
    "terminal_tails",
  ] as const)
    rows.push([
      "nuisance_coverage",
      field,
      null,
      null,
      null,
      coverage[field],
      field.endsWith("seconds") ? "slot_seconds" : "count",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      null,
      null,
    ]);
  for (const [i, start] of starts.entries())
    rows.push([
      "nuisance_coverage",
      "start_count",
      start,
      null,
      null,
      coverage.start_counts[i],
      "count",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      "new supported coalesced shifts",
      null,
    ]);
  for (const [i, zone] of ["D", "N", "O"].entries())
    rows.push([
      "nuisance_coverage",
      "on_the_fly_zone_count",
      zone,
      null,
      null,
      coverage.on_the_fly_zone_counts[i],
      "count",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      "same supported on-the-fly starts",
      null,
    ]);
  for (const quantile of ["p50", "p90", "p99", "max"] as const)
    rows.push([
      "nuisance_coverage",
      `terminal_lag_${quantile}`,
      null,
      null,
      null,
      coverage.terminal_lag_seconds?.[quantile] ?? null,
      "seconds",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      "per physical carried tail; nearest-rank quantiles",
      coverage.terminal_lag_seconds === null ? "no carried tails" : null,
    ]);
  for (const cell of coverage.prior_only_cells)
    rows.push([
      "prior_only_cell",
      cell.process,
      cell.zone,
      null,
      cell.age_lower,
      null,
      "prior_only",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      "zero observed denominator",
      null,
    ]);
  for (const zone of coverage.prior_only_restart_rows)
    rows.push([
      "prior_only_restart_row",
      "R",
      zone,
      null,
      null,
      null,
      "prior_only",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      "zero observed restart pairs",
      null,
    ]);
  for (const endpoint of coverage.censored_endpoints)
    rows.push([
      "censored_endpoint",
      endpoint.reason,
      null,
      null,
      null,
      endpoint.count,
      "count",
      null,
      null,
      null,
      null,
      evidence.reference_id,
      "reasons may overlap",
      null,
    ]);
  return rows;
}

export function TerritoryDetail({ evidence }: { readonly evidence: Evidence }) {
  const shift = evidence.shift_reference.data;
  const successor = evidence.successor_reference.data;
  const coverage = evidence.nuisance_coverage;
  return (
    <div className="territory-detail">
      <div
        className="table-scroll"
        role="region"
        tabIndex={0}
        aria-label="territory successor starts and value, scroll horizontally"
      >
        <table>
          <caption>
            successor starts and neutral-slot value; starts use the successor's
            own-team frame
          </caption>
          <thead>
            <tr>
              <th scope="col">start</th>
              <th scope="col">initial frequency</th>
              <th scope="col">neutral end</th>
              <th scope="col">focal end</th>
              <th scope="col">focal − neutral</th>
              <th scope="col">for goals/shift</th>
              <th scope="col">against goals/shift</th>
            </tr>
          </thead>
          <tbody>
            {starts.map((start, i) => (
              <tr key={start}>
                <th scope="row">{start.replaceAll("_", " ")}</th>
                <td>{number(shift?.initial_start_probabilities[i] ?? null)}</td>
                <td>{number(shift?.neutral_end_probabilities[i] ?? null)}</td>
                <td>{number(shift?.focal_end_probabilities[i] ?? null)}</td>
                <td>{number(shift?.end_difference[i] ?? null)}</td>
                <td>{number(successor?.for_goals_per_shift[i] ?? null)}</td>
                <td>{number(successor?.against_goals_per_shift[i] ?? null)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!successor && (
        <p>
          successor value unavailable: {evidence.successor_reference.reason}.
        </p>
      )}
      {territoryNotes(evidence).map((note) => (
        <p key={note}>{note}</p>
      ))}
      <p>
        on-the-fly starting-zone mixture D/N/O:{" "}
        {shift?.initial_on_the_fly_zone_probabilities
          ?.map(number)
          .join(" / ") ?? "unavailable or no on-the-fly starts"}
        ; counts {coverage.on_the_fly_zone_counts.join(" / ")}. it initializes
        live starts; the spatial successor uses its own on-the-fly category.
      </p>
      <div
        className="table-scroll"
        role="region"
        tabIndex={0}
        aria-label="neutral survival occupancy by shift age, scroll horizontally"
      >
        <table>
          <caption>common neutral survival occupancy</caption>
          <thead>
            <tr>
              <th scope="col">shift age, seconds</th>
              <th scope="col">occupancy, seconds</th>
            </tr>
          </thead>
          <tbody>
            {ages.map((age, i) => (
              <tr key={age}>
                <th scope="row">
                  {age}
                  {i === 5 ? "+" : `–${ages[i + 1]}`}
                </th>
                <td>{number(shift?.neutral_occupancy_seconds[i] ?? null)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div
        className="table-scroll"
        role="region"
        tabIndex={0}
        aria-label="territory role information and priors, scroll horizontally"
      >
        <table>
          <caption>
            role-specific information; qualifying minutes do not establish
            reliable estimates
          </caption>
          <thead>
            <tr>
              <th scope="col">role</th>
              <th scope="col">neutral hazard/s</th>
              <th scope="col">neutral 1s probability</th>
              <th scope="col">risk seconds</th>
              <th scope="col">crossings</th>
              <th scope="col">status / prior</th>
              <th scope="col">anchor / borrowed seasons</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((role) => {
              const row = evidence.roles[role],
                coefficient = row.coefficient_support;
              return (
                <tr key={role}>
                  <th scope="row">{role.replaceAll("_", " ")}</th>
                  <td>{number(row.neutral_hazard_per_second)}</td>
                  <td>{number(row.neutral_one_second_probability)}</td>
                  <td>{number(coefficient.information_weight)}</td>
                  <td>{coefficient.likelihood_events}</td>
                  <td>
                    {coefficient.status};{" "}
                    {coefficient.prior_kind ?? "unavailable"};{" "}
                    {coefficient.prior_only
                      ? "prior-only"
                      : coefficient.current_season_information
                        ? "current information"
                        : "no current information"}
                  </td>
                  <td>
                    {coefficient.prior_anchor_season ?? "none"};{" "}
                    {coefficient.prior_seasons.join(", ") || "none"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p>
        whistle risk {number(coverage.whistle_risk_slot_seconds)} slot-seconds /{" "}
        {coverage.whistle_incidences} incidences; live-ending risk{" "}
        {number(coverage.live_end_risk_slot_seconds)} slot-seconds /{" "}
        {coverage.live_end_incidences} endings. decidable whistle trials{" "}
        {coverage.decidable_whistle_trials}; ended{" "}
        {coverage.ended_whistle_trials}; team-oriented restart pairs{" "}
        {coverage.restart_pairs}. these denominators differ.
      </p>
      <p>
        terminal lag, seconds:{" "}
        {coverage.terminal_lag_seconds
          ? `p50 ${number(coverage.terminal_lag_seconds.p50)}, p90 ${number(coverage.terminal_lag_seconds.p90)}, p99 ${number(coverage.terminal_lag_seconds.p99)}, max ${number(coverage.terminal_lag_seconds.max)}`
          : "no carried tails"}
        . prior-only cells:{" "}
        {coverage.prior_only_cells
          .map((row) => `${row.process}/${row.zone}/${row.age_lower}+`)
          .join(", ") || "none"}
        ; prior-only restart rows:{" "}
        {coverage.prior_only_restart_rows.join(", ") || "none"}.
      </p>
      <p>
        censored endpoints:{" "}
        {coverage.censored_endpoints
          .map((row) => `${row.reason.replaceAll("_", " ")}: ${row.count}`)
          .join("; ") || "none"}
        ; reasons may overlap. conditional 5v5 projection assumes censoring is
        ignorable. reference <code>{evidence.reference_id}</code>.
      </p>
    </div>
  );
}
