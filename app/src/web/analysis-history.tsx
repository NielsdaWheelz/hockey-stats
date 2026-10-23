import { useId, useRef, useState } from "react";
import { Link } from "react-router";
import type { Publication, SeasonEvidence } from "../shared/observed";
import type { AnalysisDatum, AnalysisMetric } from "./analysis-values";
import { positionGroup, type AnalysisStanding } from "./analysis-cohorts";
import { formatPercentile } from "./observed-comparison";
import { downloadBlob, downloadCsv, svgPng, type CsvCell } from "./export";
import { playerName, seasonLabel, teamName } from "./presentation";

export type HistoryScale = "raw" | "percentile";
export type AnalysisRow = {
  readonly datum: AnalysisDatum;
  readonly standing: AnalysisStanding;
  readonly member: boolean;
  readonly incompatiblePeerCount: number;
};
export type HistoryPoint = AnalysisRow & { readonly season: SeasonEvidence };
type HistoryView = {
  readonly publication: Publication;
  readonly metric: AnalysisMetric;
  readonly selectedSeason: string;
  readonly scale: HistoryScale;
  readonly points: readonly HistoryPoint[];
};

export function plotDomain(
  values: readonly number[],
): readonly [number, number] | null {
  if (!values.length) return null;
  const low = Math.min(...values),
    high = Math.max(...values);
  if (low !== high) return [low, high];
  const padding = low === 0 ? 1 : Math.abs(low) * 0.05;
  return [low - padding, high + padding];
}

function historyBreak(
  previous: {
    readonly value: number | null;
    readonly semanticKey: string;
    readonly peerGroup: string | null;
  },
  current: {
    readonly value: number | null;
    readonly semanticKey: string;
    readonly peerGroup: string | null;
  },
  scale: HistoryScale,
): string | null {
  if (previous.value === null || current.value === null)
    return "value unavailable";
  if (previous.semanticKey !== current.semanticKey)
    return "quantity definition changed";
  if (scale === "percentile" && previous.peerGroup !== current.peerGroup)
    return "reference group changed";
  return null;
}

export const displayValue = (datum: AnalysisDatum): number | null =>
  datum.value === null ? null : datum.value * datum.metric.displayScale;
export const displayNumber = (value: number | null): string =>
  value === null
    ? "unavailable"
    : value.toLocaleString("en", {
        maximumSignificantDigits: 6,
        useGrouping: false,
      });
export const valueText = (datum: AnalysisDatum): string =>
  displayNumber(displayValue(datum));
export const standingText = (standing: AnalysisStanding): string =>
  standing.kind === "ranked"
    ? `${formatPercentile(standing.percentile)} percentile`
    : standing.reason;
export const datumName = (datum: AnalysisDatum): string =>
  datum.person ? playerName(datum.person) : `player ${datum.playerId}`;
const groupName = (group: string | null): string =>
  group ?? "reference unavailable";

export function DatumEvidence({ datum }: { readonly datum: AnalysisDatum }) {
  return (
    <details className="analysis-evidence">
      <summary>support, sources and method</summary>
      <p>
        {datum.reason ?? "published value available"} · qualification:{" "}
        {datum.qualificationSeconds === null
          ? "unavailable"
          : `${datum.qualificationSeconds} seconds`}{" "}
        · {datum.qualificationBasis}
      </p>
      {datum.original?.reason_detail && (
        <p>{datum.original.reason_detail.explanation}</p>
      )}
      <p>
        quantity support:{" "}
        {datum.support
          ? `${datum.support.included_seconds ?? "unknown"} included seconds; ${datum.support.known_excluded_seconds ?? "unknown"} known excluded seconds; unquantified gap: ${datum.support.unquantified_gap}; prior only: ${datum.support.prior_only}`
          : datum.observedSupport
            ? `${datum.observedSupport.included_seconds} included seconds; ${datum.observedSupport.known_excluded_seconds} known excluded seconds; recorded coverage: ${datum.observedSupport.coverage_status}`
            : "no aggregate support supplied"}
        .
      </p>
      {datum.support && (
        <p>
          inferred inputs: {datum.support.inferred_inputs.join(", ") || "none"};
          current-season information:{" "}
          {String(datum.support.current_season_information)}; prior seasons:{" "}
          {datum.support.prior_seasons.join(", ") || "none"}; support reasons:{" "}
          {JSON.stringify(datum.support.reason_counts)}.
        </p>
      )}
      {datum.original && "denominator_kind" in datum.original && (
        <p>
          published mathematical denominator:{" "}
          {datum.original.denominator ?? "unavailable"} ·{" "}
          {datum.original.denominator_kind}; numerator:{" "}
          {datum.original.numerator ?? "unavailable"}. these describe this
          field's own window.
        </p>
      )}
      {datum.reasonCodes.length > 0 && (
        <p>recorded coverage reasons: {datum.reasonCodes.join(", ")}</p>
      )}
      {Object.keys(datum.componentSupport).length > 0 && (
        <div>
          <p>constituent support (separate from qualification):</p>
          <pre>{JSON.stringify(datum.componentSupport, null, 2)}</pre>
        </div>
      )}
      {datum.methods.map((method) => (
        <div key={method.method_id}>
          <p>
            experimental method {method.method_id} · recipe {method.recipe_id} ·
            reference {method.reference_id}: {method.reference} · support policy{" "}
            {method.support_policy_id}
          </p>
          <p>
            target: {method.target}; population: {method.population}
          </p>
          {method.limitations.map((text) => (
            <p key={text}>{text}</p>
          ))}
        </div>
      ))}
      {datum.findings.map((finding, i) => (
        <p key={i}>
          {finding.population}: {finding.summary}
        </p>
      ))}
      {datum.sources.map((source) => (
        <div key={source.source_id}>
          <p>source {source.source_id}</p>
          <pre>{JSON.stringify(source, null, 2)}</pre>
        </div>
      ))}
      <p>
        uncertainty:{" "}
        {JSON.stringify(
          datum.original && "uncertainty" in datum.original
            ? datum.original.uncertainty
            : null,
        )}
        . percentile describes the published quantity, not confidence in an
        ability difference.
      </p>
    </details>
  );
}

export const analysisCsvHeaders = [
  "publication_id",
  "purpose",
  "season",
  "corpus_sha256",
  "player_id",
  "player_kind",
  "display_name",
  "position",
  "metric_id",
  "unit",
  "population",
  "construction",
  "numeric_reference",
  "value",
  "display_value",
  "display_unit",
  "value_status",
  "value_reason",
  "percentile",
  "standing_reason",
  "peer_group",
  "cutoff_minutes",
  "cohort_n",
  "incompatible_peer_count",
  "member",
  "included_seconds",
  "qualification_seconds",
  "qualification_basis",
  "known_excluded_seconds",
  "unquantified_gap",
  "prior_only",
  "component_support",
  "method_ids",
  "source_ids",
  "reference_id",
  "support_policy_id",
  "workload",
  "uncertainty_status",
  "uncertainty",
  "support_reason_counts",
  "method_limitations",
  "teams",
  "api_strength",
  "inferred_inputs",
  "current_season_information",
  "prior_seasons",
  "method_findings",
  "observed_reason_codes",
  "observed_support",
  "quantity_group",
  "value_reason_detail",
  "semantic_identity",
  "numerator",
  "denominator",
  "denominator_kind",
  "observed_coverage_status",
  "source_definitions",
  "source_limitations",
] as const;
export function analysisCsvRow(
  publication: Publication,
  season: SeasonEvidence,
  row: AnalysisRow,
): readonly CsvCell[] {
  const { datum, standing } = row;
  const uncertainty =
    datum.original && "uncertainty" in datum.original
      ? datum.original.uncertainty
      : null;
  return [
    publication.publication_id,
    publication.purpose,
    season.season,
    season.corpus_sha256,
    datum.playerId,
    datum.metric.kind,
    datum.person?.display_name ?? null,
    datum.person?.reported_position ?? null,
    datum.metric.id,
    datum.metric.unit,
    datum.population,
    datum.construction,
    datum.numericReference,
    datum.value,
    displayValue(datum),
    datum.metric.displayUnit,
    datum.status,
    datum.reason,
    standing.kind === "ranked" ? standing.percentile : null,
    standing.kind === "ranked" ? null : standing.reason,
    standing.peerGroup,
    standing.cutoffMinutes,
    standing.n,
    row.incompatiblePeerCount,
    row.member,
    datum.support?.included_seconds ??
      datum.observedSupport?.included_seconds ??
      null,
    datum.qualificationSeconds,
    datum.qualificationBasis,
    datum.support?.known_excluded_seconds ??
      datum.observedSupport?.known_excluded_seconds ??
      null,
    datum.support?.unquantified_gap ?? null,
    datum.support?.prior_only ?? null,
    JSON.stringify(datum.componentSupport),
    JSON.stringify(datum.methods.map((method) => method.method_id)),
    JSON.stringify(datum.sources.map((source) => source.source_id)),
    datum.referenceId,
    datum.supportPolicyId,
    JSON.stringify(datum.workload),
    uncertainty?.kind ?? null,
    JSON.stringify(uncertainty),
    JSON.stringify(datum.support?.reason_counts ?? null),
    JSON.stringify(datum.methods.flatMap((method) => method.limitations)),
    JSON.stringify(datum.person?.teams ?? []),
    datum.metric.strength,
    JSON.stringify(datum.support?.inferred_inputs ?? null),
    datum.support?.current_season_information ?? null,
    JSON.stringify(datum.support?.prior_seasons ?? null),
    JSON.stringify(datum.findings),
    JSON.stringify(datum.reasonCodes),
    JSON.stringify(datum.observedSupport),
    datum.metric.group,
    JSON.stringify(datum.original?.reason_detail ?? null),
    datum.semanticKey,
    datum.original && "numerator" in datum.original
      ? datum.original.numerator
      : null,
    datum.original && "denominator" in datum.original
      ? datum.original.denominator
      : null,
    datum.original && "denominator_kind" in datum.original
      ? datum.original.denominator_kind
      : null,
    datum.observedSupport?.coverage_status ?? null,
    JSON.stringify(datum.sources.map((source) => source.definition)),
    JSON.stringify(datum.sources.flatMap((source) => source.limitations)),
  ];
}

function plottedValue(point: HistoryPoint, scale: HistoryScale): number | null {
  return scale === "raw"
    ? displayValue(point.datum)
    : point.standing.kind === "ranked"
      ? point.standing.percentile
      : null;
}
function breakReason(
  previous: HistoryPoint,
  current: HistoryPoint,
  scale: HistoryScale,
) {
  if (previous.datum.value === null || current.datum.value === null)
    return "value unavailable";
  if (
    scale === "percentile" &&
    (previous.standing.kind !== "ranked" || current.standing.kind !== "ranked")
  )
    return "annual standing unavailable";
  return historyBreak(
    {
      value: plottedValue(previous, scale),
      semanticKey: previous.datum.semanticKey,
      peerGroup: previous.standing.peerGroup,
    },
    {
      value: plottedValue(current, scale),
      semanticKey: current.datum.semanticKey,
      peerGroup: current.standing.peerGroup,
    },
    scale,
  );
}
function referenceChanged(
  previous: HistoryPoint,
  current: HistoryPoint,
): boolean {
  return (
    previous.standing.peerGroup !== null &&
    current.standing.peerGroup !== null &&
    previous.standing.peerGroup !== current.standing.peerGroup
  );
}
function positionChange(
  points: readonly HistoryPoint[],
  index: number,
): string | null {
  const current = points[index];
  if (current.datum.person === null) return null;
  const previous = points
    .slice(0, index)
    .findLast((point) => point.datum.person !== null);
  if (!previous) return null;
  const before = positionGroup(previous.datum.person!.reported_position);
  const after = positionGroup(current.datum.person.reported_position);
  if (before === null || after === null || before === after) return null;
  return `reported position group changed since ${seasonLabel(previous.season.season)}: ${before === "f" ? "forwards" : "defense"} → ${after === "f" ? "forwards" : "defense"}`;
}
function geometry(view: HistoryView) {
  const values = view.points.map((point) => plottedValue(point, view.scale));
  const domain =
    view.scale === "percentile"
      ? ([0, 100] as const)
      : plotDomain(values.filter((value): value is number => value !== null));
  return {
    values,
    domain,
    x: (i: number) => 110 + (i * 980) / Math.max(1, view.points.length - 1),
    y: (value: number) =>
      domain
        ? 290 - ((value - domain[0]) / (domain[1] - domain[0])) * 220
        : 290,
  };
}

function HistoryPlot({ view }: { readonly view: HistoryView }) {
  const { values, domain, x, y } = geometry(view);
  const nativeX = (index: number) => `${x(index) / 12}%`;
  const nativeY = (value: number) => 30 + ((y(value) - 70) * 130) / 220;
  return (
    <figure>
      <svg
        className="analysis-history-plot"
        width="100%"
        height="240"
        role="img"
        aria-label={`${view.metric.label}: ${view.scale} history; all values and gaps are in the following table`}
      >
        <line x1="9.17%" x2="90.83%" y1="160" y2="160" stroke="currentColor" />
        {view.points.map((point, i) => (
          <g key={point.season.season}>
            {i > 0 &&
              values[i - 1] !== null &&
              values[i] !== null &&
              !breakReason(view.points[i - 1], point, view.scale) && (
                <line
                  x1={nativeX(i - 1)}
                  x2={nativeX(i)}
                  y1={nativeY(values[i - 1]!)}
                  y2={nativeY(values[i]!)}
                  stroke="currentColor"
                  strokeWidth="2"
                />
              )}
            {values[i] !== null ? (
              <circle
                data-season={point.season.season}
                data-value={values[i]}
                cx={nativeX(i)}
                cy={nativeY(values[i]!)}
                r="5"
                fill="currentColor"
              />
            ) : (
              <text
                x={nativeX(i)}
                y="100"
                textAnchor={
                  i === 0
                    ? "start"
                    : i === view.points.length - 1
                      ? "end"
                      : "middle"
                }
              >
                unavailable
              </text>
            )}
            <text x={nativeX(i)} y="198" textAnchor="middle">
              {seasonLabel(point.season.season)}
            </text>
            {point.season.season === view.selectedSeason && (
              <text x={nativeX(i)} y="224" textAnchor="middle">
                selected
              </text>
            )}
          </g>
        ))}
      </svg>
      {domain && (
        <div className="axis-endpoints">
          <span>minimum {displayNumber(domain[0])}</span>
          <span>maximum {displayNumber(domain[1])}</span>
        </div>
      )}
      <figcaption>
        {view.scale === "percentile"
          ? "annual percentile, 0–100"
          : view.metric.displayUnit}
        ; no line crosses a missing year or changed quantity definition.
      </figcaption>
    </figure>
  );
}

// renderer-owned geometry; text is inserted as DOM text nodes, never as markup.
function historySvg(view: HistoryView): string {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("width", "1200");
  svg.setAttribute("font-family", "system-ui, sans-serif");
  svg.setAttribute("fill", "#242b2d");
  const element = (tag: string, attrs: Record<string, string | number>) => {
    const node = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs))
      node.setAttribute(key, String(value));
    svg.append(node);
    return node;
  };
  const bg = element("rect", { width: 1200, fill: "#fbfaf6" });
  const measurement = svg.cloneNode(false) as SVGSVGElement;
  measurement.setAttribute("width", "0");
  measurement.setAttribute("height", "0");
  measurement.setAttribute("aria-hidden", "true");
  measurement.style.position = "fixed";
  const probe = document.createElementNS(ns, "text");
  measurement.append(probe);
  document.body.append(measurement);
  try {
    let top = 30;
    const text = (value: string, size = 23) => {
      probe.setAttribute("font-size", String(size));
      const width = (value: string) => {
        probe.textContent = value;
        return probe.getComputedTextLength();
      };
      const lines: string[] = [];
      for (const paragraph of value.split("\n")) {
        let line = "";
        for (const word of paragraph.split(/\s+/)) {
          const joined = line ? `${line} ${word}` : word;
          if (width(joined) <= 1072) {
            line = joined;
            continue;
          }
          if (line) lines.push(line);
          line = "";
          for (const character of word) {
            if (line && width(line + character) > 1072) {
              lines.push(line);
              line = "";
            }
            line += character;
          }
        }
        if (line) lines.push(line);
      }
      for (const line of lines) {
        const node = element("text", {
          x: 64,
          y: top + size,
          "font-size": size,
        });
        node.textContent = line;
        top += size * 1.4;
      }
      top += 10;
    };
    text(
      `${datumName(view.points.find((point) => point.datum.person)?.datum ?? view.points[0].datum)} · ${view.metric.label}`,
      32,
    );
    text(
      `${view.points.map((p) => seasonLabel(p.season.season)).join(" / ")} · ${view.scale} history · selected ${seasonLabel(view.selectedSeason)}`,
    );
    text(
      `player ${view.points[0].datum.playerId} · ${view.metric.kind} · quantity ${view.metric.id}`,
      20,
    );
    text(`${view.metric.label} · ${view.metric.group}`);
    text(
      `native unit: ${view.metric.unit}; display unit: ${view.metric.displayUnit}; display multiplier: ${view.metric.displayScale}`,
    );
    const chartTop = top;
    const { values, domain, x, y } = geometry(view);
    element("line", {
      x1: 110,
      x2: 1090,
      y1: chartTop + 290,
      y2: chartTop + 290,
      stroke: "#242b2d",
    });
    if (domain)
      for (const value of domain) {
        const node = element("text", {
          x: 100,
          y: chartTop + y(value),
          "text-anchor": "end",
          "font-size": 21,
        });
        node.textContent = displayNumber(value);
      }
    for (const [i, point] of view.points.entries()) {
      if (
        i > 0 &&
        values[i - 1] !== null &&
        values[i] !== null &&
        !breakReason(view.points[i - 1], point, view.scale)
      )
        element("line", {
          x1: x(i - 1),
          x2: x(i),
          y1: chartTop + y(values[i - 1]!),
          y2: chartTop + y(values[i]!),
          stroke: "#242b2d",
          "stroke-width": 3,
        });
      if (values[i] !== null)
        element("circle", {
          cx: x(i),
          cy: chartTop + y(values[i]!),
          r: 7,
          fill: "#242b2d",
        });
      if (values[i] === null) {
        const missing = element("text", {
          x: x(i),
          y: chartTop + 180,
          "text-anchor": "middle",
          "font-size": 21,
        });
        missing.textContent = "unavailable";
      }
      const node = element("text", {
        x: x(i),
        y: chartTop + 328,
        "text-anchor": "middle",
        "font-size": 22,
      });
      node.textContent = seasonLabel(point.season.season);
    }
    top += 370;
    for (const [i, point] of view.points.entries()) {
      const { datum, standing } = point;
      text(
        `${seasonLabel(point.season.season)}${point.season.season === view.selectedSeason ? " · selected" : ""}: ${valueText(datum)} ${view.metric.displayUnit}; ${standingText(standing)}`,
        25,
      );
      text(
        `${datumName(datum)} · ${datum.person?.reported_position ?? "position unavailable"} · ${datum.person?.teams.map(teamName).join(" / ") || "teams unavailable"}`,
      );
      text(
        `${groupName(standing.peerGroup)} · cutoff ${standing.cutoffMinutes ?? "unavailable"} min · n=${standing.n ?? "unavailable"} · incompatible peers ${point.incompatiblePeerCount}`,
      );
      text(
        `qualification: ${datum.qualificationSeconds ?? "unavailable"} seconds (${datum.qualificationBasis}); quantity support: ${datum.support?.included_seconds ?? datum.observedSupport?.included_seconds ?? "unavailable"} included seconds; known excluded seconds ${datum.support?.known_excluded_seconds ?? datum.observedSupport?.known_excluded_seconds ?? "unavailable"}; gap ${datum.support?.unquantified_gap ?? "unknown"}; prior-only ${datum.support?.prior_only ?? "unknown"}`,
      );
      if (datum.support)
        text(
          `inferred inputs: ${datum.support.inferred_inputs.join(", ") || "none"}; current-season information: ${datum.support.current_season_information}; prior seasons: ${datum.support.prior_seasons.join(", ") || "none"}`,
          20,
        );
      if (datum.workload !== null)
        text(`published workload: ${JSON.stringify(datum.workload)}`, 20);
      if (datum.observedSupport)
        text(`recorded coverage: ${datum.observedSupport.coverage_status}`, 20);
      if (datum.original && "denominator_kind" in datum.original)
        text(
          `published mathematical denominator: ${datum.original.denominator ?? "unavailable"} (${datum.original.denominator_kind}); numerator ${datum.original.numerator ?? "unavailable"}; field's own window`,
          20,
        );
      if (datum.reason) text(`value state: ${datum.reason}`);
      if (datum.original?.reason_detail)
        text(datum.original.reason_detail.explanation, 20);
      if (i > 0) {
        const reason = breakReason(view.points[i - 1], point, view.scale);
        if (reason) text(`line break: ${reason}`);
        if (referenceChanged(view.points[i - 1], point))
          text("annual reference group changed");
        const change = positionChange(view.points, i);
        if (change) text(change);
      }
      text(
        `support reasons: ${JSON.stringify(datum.support?.reason_counts ?? null)}; recorded reason codes: ${datum.reasonCodes.join(", ") || "none"}`,
        20,
      );
      for (const [term, component] of Object.entries(datum.componentSupport)) {
        const support = component.support;
        text(
          `${term.replaceAll("_", " ")}: ${support ? `${support.included_seconds ?? "unknown"} included seconds; ${support.known_excluded_seconds ?? "unknown"} excluded seconds; gap ${support.unquantified_gap}; prior-only ${support.prior_only}; inferred ${support.inferred_inputs.join(", ") || "none"}; reasons ${JSON.stringify(support.reason_counts)}` : component.reason}`,
          20,
        );
      }
      text(
        `construction: ${datum.construction}; population: ${datum.population}; numerical reference: ${datum.numericReference}`,
        20,
      );
      text(
        `methods: ${datum.methods.map((m) => m.method_id).join(", ") || "unlinked"}; sources: ${datum.sources.map((s) => s.source_id).join(", ") || "unlinked"}; reference ${datum.referenceId ?? "none"}; support policy ${datum.supportPolicyId}`,
        20,
      );
      text(
        `method limitations: ${JSON.stringify(datum.methods.flatMap((m) => m.limitations))}; findings: ${JSON.stringify(datum.findings.map((finding) => `${finding.population}: ${finding.summary}`))}; uncertainty: ${JSON.stringify(datum.original && "uncertainty" in datum.original ? datum.original.uncertainty : null)}`,
        20,
      );
      for (const source of datum.sources)
        text(
          `source ${source.label} (${source.origin}, ${source.acquisition}): ${source.definition}; limitations: ${source.limitations.join("; ") || "none supplied"}`,
          20,
        );
      text(`corpus sha-256: ${point.season.corpus_sha256}`, 18);
    }
    text(
      `publication ${view.publication.publication_id} · ${view.publication.purpose} · generated ${view.publication.generated_at}`,
      20,
    );
    text(
      "percentiles describe relative standing of the published quantity, not confidence or ability separation. missing years and changed definitions break lines. csv text cells use an apostrophe to escape spreadsheet formula prefixes.",
      20,
    );
    if (view.publication.purpose === "fixture")
      text(
        "fixture publication · analytical examples are synthetic development evidence",
        23,
      );
    const height = Math.ceil(top + 30);
    svg.setAttribute("height", String(height));
    svg.setAttribute("viewBox", `0 0 1200 ${height}`);
    bg.setAttribute("height", String(height));
    return new XMLSerializer().serializeToString(svg);
  } finally {
    measurement.remove();
  }
}

export default function AnalysisHistory({
  view,
  onScaleChange,
  seasonLink,
}: {
  readonly view: HistoryView;
  readonly onScaleChange: (scale: HistoryScale) => void;
  readonly seasonLink: (season: string) => { to: string; state: unknown };
}) {
  const id = useId();
  const [status, setStatus] = useState("idle");
  const busy = useRef(false);
  const filename = `hockey-stats-${view.points[0].datum.playerId}-${view.metric.id}-${view.points[0].season.season}-${view.points.at(-1)!.season.season}-history`;
  return (
    <section className="analysis-history" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`}>{view.metric.label}: published history</h3>
      <label htmlFor={`${id}-scale`}>history scale</label>
      <select
        id={`${id}-scale`}
        value={view.scale}
        onChange={(event) =>
          onScaleChange(event.currentTarget.value as HistoryScale)
        }
      >
        <option value="raw">raw magnitude</option>
        <option value="percentile">annual percentile</option>
      </select>
      <p>
        one slot per published season. each year uses its own person, support
        and reference cohort. zero is a value; absence is not zero.{" "}
        {view.scale === "percentile"
          ? "percentile scale: 0–100; raw values remain in the table."
          : `display unit: ${view.metric.displayUnit}.`}
      </p>
      <HistoryPlot view={view} />
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label="selected quantity history table, scroll horizontally for all columns"
      >
        <table className="analysis-history-table">
          <caption>
            exact published raw values and annual context; changes in
            definitions and reference groups are explicit.
          </caption>
          <thead>
            <tr>
              <th scope="col">season</th>
              <th scope="col">identity / teams / position</th>
              <th scope="col">raw value / unit</th>
              <th scope="col">standing / reference</th>
              <th scope="col">support / breaks</th>
            </tr>
          </thead>
          <tbody>
            {view.points.map((point, i) => (
              <tr key={point.season.season} data-season={point.season.season}>
                <th scope="row">
                  <Link
                    {...seasonLink(point.season.season)}
                    aria-current={
                      point.season.season === view.selectedSeason
                        ? "page"
                        : undefined
                    }
                  >
                    {seasonLabel(point.season.season)}
                  </Link>
                  {point.season.season === view.selectedSeason && (
                    <span className="history-context">selected season</span>
                  )}
                </th>
                <td>
                  {datumName(point.datum)}
                  <br />
                  {point.datum.person?.teams.map(teamName).join(" / ") ||
                    "teams unavailable"}
                  <br />
                  {point.datum.person?.reported_position ??
                    "position unavailable"}
                </td>
                <td>
                  {point.datum.value ?? "unavailable"} {view.metric.unit}
                  <br />
                  {view.metric.displayScale !== 1 &&
                    `${valueText(point.datum)} ${view.metric.displayUnit}`}
                  <p>{point.datum.reason}</p>
                  <p>{point.datum.numericReference}</p>
                </td>
                <td>
                  {standingText(point.standing)}
                  <br />
                  {groupName(point.standing.peerGroup)} · n=
                  {point.standing.n ?? "unavailable"} · cutoff{" "}
                  {point.standing.cutoffMinutes ?? "unavailable"} min
                  <br />
                  {point.incompatiblePeerCount} incompatible peers excluded
                </td>
                <td>
                  {i > 0 && (
                    <p>{breakReason(view.points[i - 1], point, view.scale)}</p>
                  )}
                  {i > 0 && referenceChanged(view.points[i - 1], point) && (
                    <p>annual reference group changed</p>
                  )}
                  {positionChange(view.points, i) && (
                    <p>{positionChange(view.points, i)}</p>
                  )}
                  <DatumEvidence datum={point.datum} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="card-actions">
        <button
          type="button"
          disabled={status === "rendering"}
          onClick={async () => {
            if (busy.current) return;
            busy.current = true;
            setStatus("rendering");
            const snapshot = view;
            const name = filename;
            try {
              downloadBlob(
                await svgPng(historySvg(snapshot)),
                `${name}-${snapshot.scale}.png`,
              );
              setStatus("saved");
            } catch {
              setStatus("failed");
            } finally {
              busy.current = false;
            }
          }}
        >
          {status === "rendering" ? "rendering png…" : "download history png"}
        </button>
        <button
          type="button"
          onClick={() => {
            const snapshot = view;
            try {
              downloadCsv(
                analysisCsvHeaders,
                snapshot.points.map((point) =>
                  analysisCsvRow(snapshot.publication, point.season, point),
                ),
                `${filename}.csv`,
              );
              setStatus("csv saved");
            } catch {
              setStatus("failed");
            }
          }}
        >
          download history csv
        </button>
        <p role="status">
          {status === "failed"
            ? "export failed; browsing remains available. retry the download."
            : status === "saved"
              ? "history png prepared"
              : status === "csv saved"
                ? "history csv prepared"
                : ""}
        </p>
      </div>
      <p className="control-note">
        csv retains exact native and scaled numeric values and complete supplied
        uncertainty. displayed labels use six significant digits. textual
        formula prefixes receive a leading apostrophe for spreadsheet safety.
      </p>
    </section>
  );
}
