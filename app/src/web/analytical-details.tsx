import { useId, useState } from "react";
import type { Estimate, SkaterPenalties } from "../shared/player-analysis";
import type { ProfileView, SpatialEvidence } from "./client";
import {
  analysisMetric,
  analysisMetrics,
  selectHistoryValue,
  type AnalysisMetric,
} from "./analysis-values";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  displayNumber,
  valueText,
  type AnalysisRow,
} from "./analysis-history";
import { rawOnlyStanding } from "./analysis-cohorts";
import { analyticalCardSlots } from "./analytical-card";
import { AnalyticalMapFigure, prepareAnalyticalMap } from "./analytical-map";
import { downloadCsv, type CsvCell } from "./export";
import { seasonLabel } from "./presentation";

const adjustmentQuantities = [
  "baseline",
  "self",
  "teammates",
  "opponents",
  "coaching_other_context",
  "numerical_residual",
  "factual_prediction",
] as const;
const estimateText = (value: Estimate) =>
  value.value === null
    ? `unavailable: ${value.reason_detail?.explanation ?? value.unavailable_reason?.replaceAll("_", " ")}`
    : displayNumber(value.value);
const diagnosticMeaning =
  "actual-context diagnostics can contain extreme, opposing allocations under cancellation. factual prediction is a model prediction over actual included elapsed context, not recorded results. self is a context-dependent allocation, not a standardized player effect or ledger contribution. these allocations do not support a player-credit waterfall or ranking.";
type PenaltyRecords = Record<
  "drawn" | "taken" | "served",
  (typeof SkaterPenalties.Type)["recorded_drawn"]
>;

function RecordedPenaltyTable({
  records,
  label,
}: {
  readonly records: PenaltyRecords;
  readonly label: string;
}) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      role="region"
      aria-label={`${label}, scroll horizontally`}
    >
      <table>
        <caption>{label}</caption>
        <thead>
          <tr>
            <th scope="col">recorded role</th>
            <th scope="col">count</th>
            <th scope="col">reported seconds</th>
            <th scope="col">per 1,000 minutes</th>
            <th scope="col">categories</th>
            <th scope="col">included / excluded seconds</th>
          </tr>
        </thead>
        <tbody>
          {(["drawn", "taken", "served"] as const).map((role) => (
            <tr key={role}>
              <th scope="row">recorded {role}</th>
              <td>{records[role].count ?? "unavailable"}</td>
              <td>{displayNumber(records[role].reported_seconds)}</td>
              <td>{estimateText(records[role].per1000minutes)}</td>
              <td>
                {records[role].categories
                  .map((category) => `${category.code}: ${category.count}`)
                  .join("; ") || "none supplied"}
              </td>
              <td>
                {displayNumber(records[role].support.included_seconds)} /{" "}
                {displayNumber(records[role].support.known_excluded_seconds)}
                {records[role].support.unquantified_gap
                  ? "; unquantified gaps"
                  : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const spatialEvidenceCsvHeaders = [
  "publication_id",
  "purpose",
  "season",
  "corpus_sha256",
  "player_id",
  "strength",
  "section",
  "role",
  "head",
  "state",
  "target",
  "quantity",
  "value",
  "unit",
  "availability",
  "reason",
  "included_seconds",
  "physical_seconds",
  "directed_seconds",
  "likelihood_events",
  "eligible_origin_weight",
  "current_season_information",
  "prior_only",
  "prior_kind",
  "prior_anchor_season",
  "prior_seasons",
  "baseline_current_information",
  "standardized_weights",
  "actual_state_weights",
  "annual_state",
  "reference_sha256",
  "support",
  "method_id",
  "method",
  "limitations",
  "estimate",
] as const;

function spatialEvidenceCsvRows(
  response: SpatialEvidence,
): readonly (readonly CsvCell[])[] {
  const joined =
    response.result.availability === "provided" ? response.result.data : null;
  const evidence =
    joined?.evidence.availability === "provided" ? joined.evidence.data : null;
  const summary =
    joined?.summary.availability === "provided" ? joined.summary.data : null;
  const base: Partial<
    Record<(typeof spatialEvidenceCsvHeaders)[number], CsvCell>
  > = {
    publication_id: response.publication.publication_id,
    purpose: response.publication.purpose,
    season: response.season.season,
    corpus_sha256: response.season.corpus_sha256,
    player_id: response.selection.player_id,
    strength: response.selection.strength,
    annual_state: JSON.stringify(evidence?.annual_state ?? null),
    reference_sha256: evidence?.reference_sha256,
    standardized_weights: JSON.stringify(summary?.state_weights ?? null),
    support: JSON.stringify(summary?.support ?? null),
    method_id: evidence?.method_id ?? summary?.method_id,
    method: JSON.stringify(
      response.methods[evidence?.method_id ?? summary?.method_id ?? ""] ?? null,
    ),
  };
  const rows: CsvCell[][] = [];
  const append = (
    values: Partial<
      Record<(typeof spatialEvidenceCsvHeaders)[number], CsvCell>
    >,
  ) => {
    const row = { ...base, ...values };
    rows.push(spatialEvidenceCsvHeaders.map((header) => row[header]));
  };
  append({
    section: "reference",
    quantity: "numerical_reference_sha256",
    value: evidence?.reference_sha256,
    availability: joined?.evidence.availability ?? response.result.availability,
    reason: joined?.evidence.explanation ?? response.result.explanation,
  });
  for (const state of evidence?.state_support ?? [])
    append({
      section: "state",
      state: state.state,
      quantity: "baseline_support",
      value: state.attempts,
      unit: "attempts",
      physical_seconds: state.physical_seconds,
      directed_seconds: state.directed_seconds,
      eligible_origin_weight: state.origin_weight,
      baseline_current_information: JSON.stringify(
        state.baseline_current_information,
      ),
      availability: "provided",
    });
  for (const role of evidence?.roles ?? []) {
    for (const head of ["volume", "shape", "quality"] as const) {
      const support = role.coefficient_support[head];
      const common = {
        role: role.role,
        head,
        availability: support.available ? "provided" : "unavailable",
        reason: support.reason,
        current_season_information: support.current_season_information,
        prior_only: support.prior_only,
        prior_kind: support.prior_kind,
        prior_anchor_season: support.prior_anchor_season,
        prior_seasons: JSON.stringify(support.prior_seasons),
      };
      append({
        ...common,
        section: "head",
        quantity: "likelihood_support",
        included_seconds: support.included_seconds,
        likelihood_events: support.likelihood_events,
        eligible_origin_weight: support.eligible_origin_weight,
      });
      for (const state of support.state_support ?? [])
        append({
          ...common,
          section: "head_state",
          state: state.state,
          quantity: "likelihood_support",
          included_seconds: state.included_seconds,
          likelihood_events: state.likelihood_events,
          eligible_origin_weight: state.eligible_origin_weight,
        });
    }
    append({
      section: "actual_context",
      role: role.role,
      quantity: "included_seconds",
      value: role.actual_context.included_seconds,
      unit: "seconds",
      availability: role.actual_context.available ? "provided" : "unavailable",
      reason: role.actual_context.reason,
      actual_state_weights: JSON.stringify(role.actual_context.states),
    });
    for (const state of role.actual_context.states ?? [])
      append({
        section: "actual_state",
        role: role.role,
        state: state.state,
        quantity: "included_seconds",
        value: state.seconds,
        unit: "seconds",
        actual_state_weights: JSON.stringify(role.actual_context.states),
        availability: "provided",
      });
  }
  for (const target of joined?.adjustments ?? []) {
    const data =
      target.result.availability === "provided" ? target.result.data : null;
    const role = target.target.startsWith("for_") ? "offense" : "defense";
    const context = evidence?.roles.find(
      (item) => item.role === role,
    )?.actual_context;
    const method = data ? response.methods[data.method_id] : null;
    const warnings =
      method?.assessment.findings.filter((finding) =>
        finding.quantities.some((quantity) =>
          quantity.startsWith("adjustment_decomposition."),
        ),
      ) ?? [];
    for (const quantity of adjustmentQuantities) {
      const estimate = data?.[quantity];
      append({
        section: "adjustment",
        role,
        target: target.target,
        quantity,
        value: estimate?.value,
        unit: target.target.includes("attempts")
          ? "attempts_per60"
          : "xg_per60",
        availability: estimate
          ? estimate.value === null
            ? "unavailable"
            : "provided"
          : target.result.availability,
        reason:
          estimate?.reason_detail?.explanation ?? target.result.explanation,
        included_seconds: context?.included_seconds,
        actual_state_weights: JSON.stringify(context?.states ?? null),
        method_id: data?.method_id,
        method: JSON.stringify(method ?? null),
        estimate: JSON.stringify(estimate ?? null),
        limitations: JSON.stringify({
          meaning: diagnosticMeaning,
          findings: warnings,
        }),
      });
    }
  }
  return rows;
}

const analyticalAnnualCsvHeaders = [
  "section",
  "slot_id",
  ...analysisCsvHeaders,
] as const;
function analyticalAnnualRows(profile: ProfileView) {
  return profile.detail.history.map((year) => ({
    year,
    fields: analyticalCardSlots.map((slot) => {
      const metric = analysisMetric(slot.metricId);
      if (!metric)
        throw new Error(`analytical annual selector missing: ${slot.metricId}`);
      const datum = selectHistoryValue(
        year,
        profile.detail,
        metric,
        profile.player_id,
      );
      const row: AnalysisRow = {
        datum,
        standing:
          metric.standingPolicy === "raw_only"
            ? rawOnlyStanding
            : {
                kind: "unavailable",
                reason: "raw annual detail; percentile not requested",
                n: null,
                peerGroup: null,
                cutoffMinutes: null,
              },
        member: null,
        incompatiblePeerCount: null,
      };
      return { ...slot, row };
    }),
  }));
}
function analyticalAnnualCsvRows(
  profile: ProfileView,
): readonly (readonly CsvCell[])[] {
  return analyticalAnnualRows(profile).flatMap(({ year, fields }) =>
    fields.map((field) => [
      field.section,
      field.slotId,
      ...analysisCsvRow(profile.publication, year.season, field.row),
    ]),
  );
}

const penaltyEvidenceCsvHeaders = [
  "publication_id",
  "purpose",
  "season",
  "corpus_sha256",
  "player_id",
  "construction",
  "population",
  "record_owner",
  "role",
  "count",
  "reported_seconds",
  "per1000minutes",
  "estimate",
  "categories",
  "support",
  "provenance",
  "method",
  "availability",
  "reason",
] as const;
function penaltyEvidenceCsvRows(
  profile: ProfileView,
  owner: "descriptive" | "penalties",
): readonly (readonly CsvCell[])[] {
  const families = profile.detail.families;
  if ("availability" in families || families.kind !== "skater")
    return [
      [
        profile.publication.publication_id,
        profile.publication.purpose,
        profile.season.season,
        profile.season.corpus_sha256,
        profile.player_id,
        "recorded",
        "all strengths",
        owner,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        "absent",
        "availability" in families
          ? families.explanation
          : "not applicable to goalies",
      ],
    ];
  const descriptive =
    families.descriptive.availability === "provided"
      ? families.descriptive.data
      : null;
  const penalties =
    families.penalties.availability === "provided"
      ? families.penalties.data
      : null;
  const records =
    owner === "descriptive"
      ? descriptive?.recorded_penalties.focal
      : penalties
        ? {
            drawn: penalties.recorded_drawn,
            taken: penalties.recorded_taken,
            served: penalties.recorded_served,
          }
        : null;
  return (["drawn", "taken", "served"] as const).map((role) => [
    profile.publication.publication_id,
    profile.publication.purpose,
    profile.season.season,
    profile.season.corpus_sha256,
    profile.player_id,
    "recorded",
    "all strengths",
    owner,
    `recorded_${role}`,
    records?.[role].count,
    records?.[role].reported_seconds,
    records?.[role].per1000minutes.value,
    JSON.stringify(records?.[role].per1000minutes ?? null),
    JSON.stringify(records?.[role].categories ?? null),
    JSON.stringify(records?.[role].support ?? null),
    JSON.stringify(
      owner === "descriptive" ? (descriptive?.provenance ?? null) : null,
    ),
    JSON.stringify(
      owner === "penalties" && penalties
        ? profile.detail.methods[penalties.method_id]
        : null,
    ),
    records ? "provided" : families[owner].availability,
    records?.[role].per1000minutes.reason_detail?.explanation ??
      families[owner].explanation,
  ]);
}

function SpatialEvidenceDetail({
  response,
}: {
  readonly response: SpatialEvidence;
}) {
  const [status, setStatus] = useState("");
  const joined =
    response.result.availability === "provided" ? response.result.data : null;
  const evidence =
    joined?.evidence.availability === "provided" ? joined.evidence.data : null;
  const summary =
    joined?.summary.availability === "provided" ? joined.summary.data : null;
  const findings = evidence
    ? (response.methods[evidence.method_id]?.assessment.findings.filter(
        (finding) =>
          finding.quantities.some((quantity) =>
            quantity.startsWith("adjustment_decomposition."),
          ),
      ) ?? [])
    : [];
  return (
    <section className="analytical-spatial-evidence">
      <h3>saved spatial evidence · {response.selection.strength}</h3>
      {!evidence ? (
        <p>{joined?.evidence.explanation ?? response.result.explanation}</p>
      ) : (
        <>
          <p>
            numerical reference digest: <code>{evidence.reference_sha256}</code>
            . annual state: <code>{evidence.annual_state.uri}</code> · sha256{" "}
            <code>{evidence.annual_state.sha256}</code>.
          </p>
          <p>
            aggregate qualification is actual included time; information below
            belongs to each role and head. current information for one head does
            not establish information for the other heads, precision or solver
            accuracy. zero exact-state minutes can coexist with informed pooled
            specialty coefficients. prior-only estimates remain hypothetical.
          </p>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="annual state baseline evidence, scroll horizontally"
          >
            <table>
              <caption>
                annual baseline support, not the focal player's time
              </caption>
              <thead>
                <tr>
                  <th scope="col">attacker-oriented state</th>
                  <th scope="col">physical seconds</th>
                  <th scope="col">directed seconds</th>
                  <th scope="col">attempts</th>
                  <th scope="col">origin weight</th>
                  <th scope="col">volume / shape / quality information</th>
                </tr>
              </thead>
              <tbody>
                {evidence.state_support.map((state) => (
                  <tr key={state.state}>
                    <th scope="row">{state.state}</th>
                    <td>{displayNumber(state.physical_seconds)}</td>
                    <td>{displayNumber(state.directed_seconds)}</td>
                    <td>{state.attempts}</td>
                    <td>{displayNumber(state.origin_weight)}</td>
                    <td>
                      {Object.values(state.baseline_current_information)
                        .map((flag) => (flag ? "yes" : "no; extrapolated"))
                        .join(" / ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label="spatial coefficient head support and priors, scroll horizontally"
          >
            <table>
              <caption>
                focal coefficient support across the full fitted family
              </caption>
              <thead>
                <tr>
                  <th scope="col">role / head</th>
                  <th scope="col">included seconds</th>
                  <th scope="col">likelihood events</th>
                  <th scope="col">origin weight</th>
                  <th scope="col">current information</th>
                  <th scope="col">prior only</th>
                  <th scope="col">entry / carry</th>
                  <th scope="col">anchor / prior years</th>
                  <th scope="col">state breakdown / reason</th>
                </tr>
              </thead>
              <tbody>
                {evidence.roles.flatMap((role) =>
                  (["volume", "shape", "quality"] as const).map((head) => {
                    const support = role.coefficient_support[head];
                    return (
                      <tr key={`${role.role}-${head}`}>
                        <th scope="row">
                          {role.role} / {head}
                        </th>
                        <td>{displayNumber(support.included_seconds)}</td>
                        <td>{support.likelihood_events ?? "unavailable"}</td>
                        <td>{displayNumber(support.eligible_origin_weight)}</td>
                        <td>
                          {support.current_season_information === null
                            ? "unavailable"
                            : String(support.current_season_information)}
                        </td>
                        <td>
                          {support.prior_only === null
                            ? "unavailable"
                            : String(support.prior_only)}
                        </td>
                        <td>{support.prior_kind ?? "unavailable"}</td>
                        <td>
                          {support.prior_anchor_season ?? "none"} /{" "}
                          {support.prior_seasons.join(", ") || "none"}
                        </td>
                        <td>
                          {support.available
                            ? support.state_support
                                ?.map(
                                  (state) =>
                                    `${state.state}: ${displayNumber(state.included_seconds)} s, ${state.likelihood_events} events, ${displayNumber(state.eligible_origin_weight)} origin weight`,
                                )
                                .join("; ")
                            : support.reason}
                        </td>
                      </tr>
                    );
                  }),
                )}
              </tbody>
            </table>
          </div>
          <p>
            standardized reference weights:{" "}
            {JSON.stringify(summary?.state_weights ?? null)}. these are the
            published common basket or exact-state weights, not actual
            deployment weights.
          </p>
          {evidence.roles.map((role) => (
            <p key={role.role}>
              actual {role.role} context:{" "}
              {displayNumber(role.actual_context.included_seconds)} included
              seconds;{" "}
              {role.actual_context.available
                ? role.actual_context.states
                    ?.map(
                      (state) =>
                        `${state.state}: ${displayNumber(state.seconds)} s, weight ${displayNumber(state.weight)}`,
                    )
                    .join("; ")
                : role.actual_context.reason}
              .
            </p>
          ))}
        </>
      )}
      <h4>actual-context adjustments · diagnostic allocations</h4>
      <p className="analytical-warning">{diagnosticMeaning}</p>
      {findings.map((finding, index) => (
        <p className="analytical-warning" key={index}>
          {finding.summary}
        </p>
      ))}
      {joined && (
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="all seven actual-context adjustment quantities, scroll horizontally"
        >
          <table>
            <caption>
              supplied actual-context values; no favorable-sign reversal or
              clipping
            </caption>
            <thead>
              <tr>
                <th scope="col">target</th>
                <th scope="col">quantity</th>
                <th scope="col">value</th>
                <th scope="col">unit</th>
                <th scope="col">reason</th>
              </tr>
            </thead>
            <tbody>
              {joined.adjustments.flatMap((target) =>
                adjustmentQuantities.map((quantity) => {
                  const estimate =
                    target.result.availability === "provided"
                      ? target.result.data[quantity]
                      : null;
                  return (
                    <tr key={`${target.target}-${quantity}`}>
                      <th scope="row">{target.target.replaceAll("_", " ")}</th>
                      <td>{quantity.replaceAll("_", " ")}</td>
                      <td>
                        {estimate ? displayNumber(estimate.value) : "pending"}
                      </td>
                      <td>
                        {target.target.includes("attempts")
                          ? "attempts per 60 min"
                          : "xg per 60 min"}
                      </td>
                      <td>
                        {estimate?.reason_detail?.explanation ??
                          target.result.explanation ??
                          "available; calibrated uncertainty not estimated"}
                      </td>
                    </tr>
                  );
                }),
              )}
            </tbody>
          </table>
        </div>
      )}
      <button
        type="button"
        onClick={() => {
          try {
            downloadCsv(
              spatialEvidenceCsvHeaders,
              spatialEvidenceCsvRows(response),
              `hockey-stats-${response.season.season}-${response.selection.player_id}-${response.selection.strength}-spatial-evidence.csv`,
            );
            setStatus("spatial evidence csv prepared");
          } catch {
            setStatus("spatial evidence export failed; retry the download");
          }
        }}
      >
        download spatial evidence csv
      </button>
      <p role="status">{status}</p>
    </section>
  );
}

function AnnualComponents({ profile }: { readonly profile: ProfileView }) {
  const [annualOpen, setAnnualOpen] = useState(false);
  const [status, setStatus] = useState("");
  const annual = annualOpen ? analyticalAnnualRows(profile) : [];
  return (
    <section>
      <details onToggle={(event) => setAnnualOpen(event.currentTarget.open)}>
        <summary>
          three-season raw components and subskills · 57 fields per year
        </summary>
        <p>
          each year retains its own identity, population, reference, recipe and
          support. these raw tables request no additional cohorts, interpolate
          no missing values and create no trajectory across a semantic break.
        </p>
        {annual.map(({ year, fields }) => (
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label={`${seasonLabel(year.season.season)} raw analytical components, scroll horizontally`}
            key={year.season.season}
          >
            <table>
              <caption>
                {seasonLabel(year.season.season)} ·{" "}
                {year.person?.display_name ??
                  "selected person absent this year"}
              </caption>
              <thead>
                <tr>
                  <th scope="col">slot / quantity</th>
                  <th scope="col">supplied value</th>
                  <th scope="col">unit</th>
                  <th scope="col">population</th>
                  <th scope="col">reference / recipe</th>
                  <th scope="col">included seconds / disposition</th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field) => (
                  <tr key={field.row.datum.metric.id}>
                    <th scope="row">
                      {field.slotId} / {field.row.datum.metric.label}
                    </th>
                    <td>
                      {field.row.datum.value === null
                        ? "unavailable"
                        : valueText(field.row.datum)}
                    </td>
                    <td>{field.row.datum.metric.displayUnit}</td>
                    <td>{field.row.datum.population}</td>
                    <td>
                      {field.row.datum.numericReference};{" "}
                      {field.row.datum.methods
                        .map((method) => method.recipe_id)
                        .join(", ") || "not supplied"}
                    </td>
                    <td>
                      {displayNumber(field.row.datum.qualificationSeconds)};{" "}
                      {field.row.datum.reason ??
                        (field.row.datum.support?.prior_only
                          ? "prior-only / hypothetical"
                          : field.row.datum.status)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
        <button
          type="button"
          onClick={() => {
            try {
              downloadCsv(
                analyticalAnnualCsvHeaders,
                analyticalAnnualCsvRows(profile),
                `hockey-stats-${profile.season.season}-${profile.player_id}-analytical-annual.csv`,
              );
              setStatus("annual analytical csv prepared");
            } catch {
              setStatus("annual export failed; retry the download");
            }
          }}
        >
          download all annual components csv
        </button>
      </details>
      <p role="status">{status}</p>
    </section>
  );
}

export default function AnalyticalDetails({
  profile,
  metric,
  render,
  onRenderChange,
  onModeChange,
  onMetricChange,
  mode,
}: {
  readonly profile: ProfileView;
  readonly metric: AnalysisMetric;
  readonly render: "contours" | "rectangles";
  readonly onRenderChange: (value: "contours" | "rectangles") => void;
  readonly onModeChange: (value: "difference" | "absolute") => void;
  readonly onMetricChange: (value: AnalysisMetric) => void;
  readonly mode: "difference" | "absolute";
}) {
  const id = useId();
  const [status, setStatus] = useState("");
  const families = profile.detail.families;
  if ("availability" in families || families.kind !== "skater")
    return (
      <section>
        <h3>analytical detail</h3>
        <p>
          {"availability" in families
            ? families.explanation
            : "skater analytical detail is not applicable to goalies"}
        </p>
        {families.kind === "skater" && <AnnualComponents profile={profile} />}
      </section>
    );
  const spatial = metric.publicationFamily === "spatial";
  const executionStrength =
    metric.publicationFamily === "execution"
      ? (metric.selectionStrength ?? "5v5")
      : "5v5";
  const execution =
    families.execution.availability === "provided"
      ? families.execution.data.find(
          (row) => row.strength === executionStrength,
        )?.result
      : families.execution;
  const executionData =
    execution?.availability === "provided" ? execution.data : null;
  const penalties =
    families.penalties.availability === "provided"
      ? families.penalties.data
      : null;
  const recorded =
    families.descriptive.availability === "provided"
      ? families.descriptive.data.recorded_penalties.focal
      : null;
  const territory =
    families.territory.availability === "provided"
      ? families.territory.data
      : null;
  const selectedMap = profile.selectedMap
    ? prepareAnalyticalMap(profile.selectedMap, profile.player_id)
    : null;
  return (
    <section className="analytical-details">
      <h2>analytical detail · {metric.label}</h2>
      {(spatial || metric.publicationFamily === "execution") && (
        <div className="analysis-controls">
          <div>
            <label htmlFor={`${id}-strength`}>detail strength</label>
            <select
              id={`${id}-strength`}
              value={metric.id}
              onChange={(event) =>
                onMetricChange(analysisMetric(event.target.value)!)
              }
            >
              {analysisMetrics
                .filter(
                  (candidate) =>
                    candidate.publicationFamily === metric.publicationFamily &&
                    candidate.id.split(".").slice(2).join(".") ===
                      metric.id.split(".").slice(2).join("."),
                )
                .map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.id.split(".")[1]}
                  </option>
                ))}
            </select>
          </div>
          {spatial && (
            <div>
              <label htmlFor={`${id}-quantity`}>spatial quantity</label>
              <select
                id={`${id}-quantity`}
                value={metric.id}
                onChange={(event) =>
                  onMetricChange(analysisMetric(event.target.value)!)
                }
              >
                {analysisMetrics
                  .filter(
                    (candidate) =>
                      candidate.publicationFamily === "spatial" &&
                      candidate.id.split(".")[1] === metric.id.split(".")[1] &&
                      candidate.id.includes(
                        metric.id.includes(".defense_")
                          ? ".defense_"
                          : ".offense_",
                      ),
                  )
                  .map((candidate) => (
                    <option key={candidate.id} value={candidate.id}>
                      {candidate.label}
                    </option>
                  ))}
              </select>
            </div>
          )}
        </div>
      )}
      {selectedMap && (
        <>
          <div className="analysis-controls">
            {spatial && (
              <div>
                <label htmlFor={`${id}-map-view`}>selected map values</label>
                <select
                  id={`${id}-map-view`}
                  value={mode}
                  onChange={(event) =>
                    onModeChange(
                      event.target.value as "difference" | "absolute",
                    )
                  }
                >
                  <option value="difference">effect difference</option>
                  <option value="absolute">complete focal rate</option>
                </select>
              </div>
            )}
            <div>
              <label htmlFor={`${id}-render`}>map rendering</label>
              <select
                id={`${id}-render`}
                value={render}
                onChange={(event) =>
                  onRenderChange(
                    event.target.value as "contours" | "rectangles",
                  )
                }
              >
                <option value="contours">contours</option>
                <option value="rectangles">raw rectangles</option>
              </select>
            </div>
          </div>
          <AnalyticalMapFigure model={selectedMap} render={render} />
        </>
      )}
      {spatial && profile.spatialEvidence && (
        <SpatialEvidenceDetail response={profile.spatialEvidence} />
      )}
      <section>
        <h3>execution subskills · {executionStrength}</h3>
        <p>
          conditional focal stage probabilities and supplied focal-minus-neutral
          differences use the common reference panel. neutral prefix masses and
          denominators remain visible; the panel and focal qualifying minutes
          are different populations. selected finishing or setting skill is not
          a skill-by-stratum estimate.
        </p>
        {!executionData ? (
          <p>
            {execution?.explanation ??
              "execution strength is pending computation"}
          </p>
        ) : (
          <>
            <p>
              panel: {executionData.reference_panel.opportunities} physical
              opportunities; inferred setup weight{" "}
              {displayNumber(executionData.reference_panel.setup_weight)}.
            </p>
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="execution conditional stages and panel denominators, scroll horizontally"
            >
              <table>
                <thead>
                  <tr>
                    <th scope="col">conditional stage</th>
                    <th scope="col">focal probability</th>
                    <th scope="col">focal − neutral</th>
                    <th scope="col">neutral prefix numerator / denominator</th>
                    <th scope="col">qualifying seconds</th>
                  </tr>
                </thead>
                <tbody>
                  {(
                    [
                      ["avoid block", "avoid_block_probability", "u", null],
                      [
                        "on net given unblocked",
                        "on_net_probability",
                        "uq",
                        "u",
                      ],
                      [
                        "recorded stop given on net",
                        "recorded_stop_probability",
                        "uqr",
                        "uq",
                      ],
                      [
                        "conversion given no recorded stop",
                        "conversion_probability",
                        "uqrg",
                        "uqr",
                      ],
                    ] as const
                  ).map(([label, field, numerator, denominator]) => (
                    <tr key={field}>
                      <th scope="row">{label}</th>
                      <td>{estimateText(executionData[field])}</td>
                      <td>
                        {estimateText(executionData[`${field}_difference`])}
                      </td>
                      <td>
                        {field === "recorded_stop_probability" &&
                          "no-recorded-stop continuation: "}
                        {displayNumber(
                          executionData.reference_panel.neutral[numerator],
                        )}{" "}
                        /{" "}
                        {displayNumber(
                          denominator
                            ? executionData.reference_panel.neutral[denominator]
                            : executionData.reference_panel.opportunities,
                        )}
                      </td>
                      <td>
                        {displayNumber(
                          executionData.support[field].included_seconds,
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="execution coefficient information, scroll horizontally"
            >
              <table>
                <caption>
                  conditional coefficient evidence; information is not
                  calibrated uncertainty
                </caption>
                <thead>
                  <tr>
                    <th scope="col">coefficient</th>
                    <th scope="col">likelihood events</th>
                    <th scope="col">prior only / prior years</th>
                    <th scope="col">reason</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ...(["u", "q", "r", "g"] as const).map((head) => ({
                      label: `shooter ${head}`,
                      support: executionData.coefficient_support.shooter[head],
                    })),
                    {
                      label: "inferred setter g",
                      support: executionData.coefficient_support.setter.g,
                    },
                  ].map(({ label, support }) => (
                    <tr key={label}>
                      <th scope="row">{label}</th>
                      <td>{support.likelihood_events ?? "unavailable"}</td>
                      <td>
                        {support.prior_only === null
                          ? "unavailable"
                          : String(support.prior_only)}{" "}
                        / {support.prior_seasons.join(", ") || "none"}
                      </td>
                      <td>{support.reason ?? "available"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p>
              inferred setter candidate events:{" "}
              {executionData.coefficient_support.setter.g.candidate_events ??
                "unavailable"}
              ; mean-coupled events:{" "}
              {executionData.coefficient_support.setter.g.mean_coupled_events ??
                "unavailable"}
              . finishing denominator:{" "}
              {executionData.reference_panel.opportunities} attempts; setting
              denominator:{" "}
              {displayNumber(executionData.reference_panel.setup_weight)}{" "}
              inferred assisted opportunities.
            </p>
          </>
        )}
      </section>
      <section>
        <h3>
          penalties · recorded all-strength evidence and modeled 5v5 awards
        </h3>
        <p>
          recorded drawn, taken and served penalties describe the supplied
          all-strength factual population. ordinary-minor modeled contrasts
          describe 5v5 team awards. a positive taking contrast means more taken;
          it is not a favorable contribution.
        </p>
        {!recorded ? (
          <p>
            {families.descriptive.explanation ??
              "recorded penalty evidence unavailable"}
          </p>
        ) : (
          <RecordedPenaltyTable
            records={recorded}
            label="descriptive facts · recorded all-strength penalty evidence"
          />
        )}
        {penalties && (
          <RecordedPenaltyTable
            records={{
              drawn: penalties.recorded_drawn,
              taken: penalties.recorded_taken,
              served: penalties.recorded_served,
            }}
            label="penalty-family supplied records · recorded all-strength penalty evidence"
          />
        )}

        {penalties ? (
          <>
            <p>
              modeled ordinary-minor contrasts: drawn{" "}
              {estimateText(penalties.drawn_per60)}; taken{" "}
              {estimateText(penalties.taken_per60)} awards per 60 min. supplied
              drawn value {estimateText(penalties.drawn_value_per60)}; taken
              value {estimateText(penalties.taken_value_per60)} goals per 60
              min.
            </p>
            <p>
              model included seconds{" "}
              {displayNumber(penalties.support.included_seconds)}; known
              excluded seconds{" "}
              {displayNumber(penalties.support.known_excluded_seconds)};
              unquantified gap {String(penalties.support.unquantified_gap)}.
              exclusions: {JSON.stringify(penalties.support.reason_counts)}.
            </p>
          </>
        ) : (
          <p>modeled penalties: {families.penalties.explanation}</p>
        )}
        {(["descriptive", "penalties"] as const).map((owner) => (
          <button
            type="button"
            key={owner}
            onClick={() => {
              try {
                downloadCsv(
                  penaltyEvidenceCsvHeaders,
                  penaltyEvidenceCsvRows(profile, owner),
                  `hockey-stats-${profile.season.season}-${profile.player_id}-${owner}-recorded-penalties.csv`,
                );
                setStatus(`${owner} recorded penalty evidence csv prepared`);
              } catch {
                setStatus(
                  "recorded penalty evidence export failed; retry the download",
                );
              }
            }}
          >
            {owner === "descriptive"
              ? "download recorded penalty evidence csv"
              : "download supplied penalty evidence csv"}
          </button>
        ))}
      </section>
      <section>
        <h3>inferred territory subskills</h3>
        <p>
          inferred territory is not tracked entries or exits. transition
          probability differs from opponent-transition avoidance; hazards stay
          in per-second units. ice-won / ice-lost map values use their declared
          basket; ledger contributions have separate workload and units.
        </p>
        {!territory ? (
          <p>{families.territory.explanation}</p>
        ) : (
          <>
            <p>
              ice won {estimateText(territory.ice_won_goals_per_basket)}; ice
              lost {estimateText(territory.ice_lost_goals_per_basket)} goals per
              declared basket.
            </p>
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="territory hazards and one-second probabilities, scroll horizontally"
            >
              <table>
                <thead>
                  <tr>
                    <th scope="col">subskill</th>
                    <th scope="col">supplied hazard per second</th>
                    <th scope="col">one-second probability</th>
                    <th scope="col">probability meaning</th>
                    <th scope="col">included / excluded seconds</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      label: "exit offense",
                      hazard: territory.exit_offense.hazard_per_second,
                      probability:
                        territory.exit_offense.one_second_probability,
                      support: territory.exit_offense.support,
                      meaning: "transition",
                    },
                    {
                      label: "entry offense",
                      hazard: territory.entry_offense.hazard_per_second,
                      probability:
                        territory.entry_offense.one_second_probability,
                      support: territory.entry_offense.support,
                      meaning: "transition",
                    },
                    {
                      label: "zone retention",
                      hazard:
                        territory.zone_retention
                          .opponent_exit_hazard_per_second,
                      probability:
                        territory.zone_retention.one_second_probability,
                      support: territory.zone_retention.support,
                      meaning: "avoid opponent exit",
                    },
                    {
                      label: "entry prevention",
                      hazard:
                        territory.entry_prevention
                          .opponent_entry_hazard_per_second,
                      probability:
                        territory.entry_prevention.one_second_probability,
                      support: territory.entry_prevention.support,
                      meaning: "avoid opponent entry",
                    },
                  ].map((row) => (
                    <tr key={row.label}>
                      <th scope="row">{row.label}</th>
                      <td>{estimateText(row.hazard)}</td>
                      <td>{estimateText(row.probability)}</td>
                      <td>{row.meaning}</td>
                      <td>
                        {displayNumber(row.support.included_seconds)} /{" "}
                        {displayNumber(row.support.known_excluded_seconds)}
                        {row.support.unquantified_gap
                          ? "; unquantified gaps"
                          : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
      <AnnualComponents profile={profile} />
      <p role="status">{status}</p>
    </section>
  );
}
