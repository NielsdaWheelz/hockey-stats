import { useId, useRef, useState } from "react";
import { Link } from "react-router";
import type { Person } from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import type { ProfileView } from "./client";
import type { PeerSettings } from "./explorer";
import {
  analysisMetric,
  comparativeTileIds,
  selectHistoryValue,
  selectLeagueValues,
  type AnalysisMetricId,
} from "./analysis-values";
import { buildAnalysisCohort } from "./analysis-cohorts";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  DatumEvidence,
  displayNumber,
  prepareHistory,
  standingText,
  valueText,
  type AnalysisRow,
  type HistoryPoint,
} from "./analysis-history";
import { csvText, downloadBlob, svgPng } from "./export";
import { playerName, seasonLabel, teamName } from "./presentation";
import { ledgerCoverage, ledgerLimits, ledgerWorkload } from "./ledger-presentation";

const tilePresentation = {
  "ledger.five_on_five_offense.league_goals": [
    "5v5 offense",
    "modeled contribution",
  ],
  "ledger.five_on_five_defense.league_goals": [
    "5v5 defense",
    "modeled contribution",
  ],
  "ledger.power_play_offense.league_goals": [
    "power play",
    "modeled contribution · hypothetical 100 min",
  ],
  "ledger.penalty_kill_defense.league_goals": [
    "penalty kill",
    "modeled contribution · hypothetical 100 min",
  ],
  "ledger.finishing.league_goals": [
    "finishing",
    "modeled full-workload contribution",
  ],
  goals60: ["goals", "recorded personal 5v5 rate"],
  primaryAssists60: ["primary assists", "recorded personal 5v5 rate"],
  "ledger.penalties_combined.league_goals": [
    "penalties",
    "modeled drawing + taking contribution",
  ],
  "context.opponents.usage_minutes_per_appearance": [
    "opponent usage",
    "shared-5v5 weighted all-strength usage proxy",
  ],
  "context.teammates.usage_minutes_per_appearance": [
    "teammate usage",
    "shared-5v5 weighted all-strength usage proxy",
  ],
} as const satisfies Record<
  (typeof comparativeTileIds)[number],
  readonly [string, string]
>;
const comparativeTiles = comparativeTileIds.map(
  (id) => [tilePresentation[id][0], id, tilePresentation[id][1]] as const,
);

type CardField = {
  readonly label: string;
  readonly construction: string;
  readonly row: AnalysisRow;
};
type CardSeries = {
  readonly label: string;
  readonly color: string;
  readonly dash: string;
  readonly points: ReturnType<typeof prepareHistory>;
};
type ComparativeCardModel = {
  readonly playerId: string;
  readonly person: Person | null;
  readonly historicalPerson: Person | null;
  readonly season: SeasonEvidence;
  readonly publication: Publication;
  readonly settings: PeerSettings;
  readonly usage:
    | ProfileView["overviewCohorts"][number]["players"][number]["result"]
    | null;
  readonly headline: CardField;
  readonly replacement: CardField;
  readonly tiles: readonly CardField[];
  readonly headlineHistory: readonly CardSeries[];
  readonly componentHistory: readonly CardSeries[];
};

export function prepareComparativeCard(
  profile: ProfileView,
  settings: PeerSettings,
): ComparativeCardModel {
  const annual = profile.detail.history.toSorted((a, b) =>
    a.season.season.localeCompare(b.season.season),
  );
  const selected = annual.find(
    (year) => year.season.season === profile.season.season,
  )!;
  const prepared = new Map<string, HistoryPoint>();
  const point = (
    year: (typeof annual)[number],
    id: AnalysisMetricId,
  ): HistoryPoint => {
    const key = `${year.season.season}:${id}`;
    const existing = prepared.get(key);
    if (existing) return existing;
    const metric = analysisMetric(id)!;
    const overview = profile.overviewCohorts.find(
      (cohort) => cohort.season.season === year.season.season,
    );
    if (!overview)
      throw new Error("comparative card is missing an annual overview cohort");
    const datum = selectHistoryValue(year, overview, metric, profile.player_id);
    const cohort = buildAnalysisCohort(
      selectLeagueValues(overview, metric),
      [datum],
      settings,
    );
    const group = cohort.groups.find((group) => group.selected.length > 0)!;
    const result = {
      datum,
      standing: group.selected[0].standing,
      member: group.members.some(
        (member) => member.playerId === profile.player_id,
      ),
      incompatiblePeerCount: group.incompatiblePeerCount,
      season: year.season,
    };
    prepared.set(key, result);
    return result;
  };
  const row = (id: AnalysisMetricId) => point(selected, id);
  const history = (id: AnalysisMetricId) =>
    prepareHistory(annual.map((year) => point(year, id)), "percentile");
  return {
    playerId: profile.player_id,
    person: selected.person,
    historicalPerson:
      annual.findLast((year) => year.person !== null)?.person ?? null,
    season: profile.season,
    publication: profile.publication,
    settings,
    usage:
      profile.overviewCohorts
        .find((cohort) => cohort.season.season === profile.season.season)
        ?.players.find((row) => row.person.player_id === profile.player_id)
        ?.result ?? null,
    headline: {
      label: "league-relative value",
      construction: "experimental favorable goals per common workload",
      row: row("ledger.league_total"),
    },
    replacement: {
      label: "replacement-relative value",
      construction:
        ledgerCoverage(row("ledger.replacement_total").datum) ?? "reported-usage depth reference",
      row: row("ledger.replacement_total"),
    },
    tiles: comparativeTiles.map(([label, id, construction]) => ({
      label,
      construction,
      row: row(id),
    })),
    headlineHistory: [
      {
        label: "league-relative value",
        color: "#17696b",
        dash: "",
        points: history("ledger.league_total"),
      },
      {
        label: "depth-replacement value",
        color: "#6e4e8b",
        dash: "7 4",
        points: history("ledger.replacement_total"),
      },
    ],
    componentHistory: [
      {
        label: "5v5 offense",
        color: "#17696b",
        dash: "",
        points: history("ledger.five_on_five_offense.league_goals"),
      },
      {
        label: "5v5 defense",
        color: "#6e4e8b",
        dash: "7 4",
        points: history("ledger.five_on_five_defense.league_goals"),
      },
      {
        label: "finishing",
        color: "#a0522d",
        dash: "2 4",
        points: history("ledger.finishing.league_goals"),
      },
    ],
  };
}

const peersText = ({ standing, datum }: AnalysisRow) =>
  `${standingText(standing)} · ${standing.peerGroup ?? "reference unavailable"} · n=${standing.n ?? "unavailable"} · cutoff ${standing.cutoffMinutes ?? "unavailable"} min · qualification ${datum.qualificationSeconds ?? "unavailable"} s (${datum.metric.qualificationLabel})`;
const magnitude = ({ datum }: AnalysisRow) =>
  `${valueText(datum)} ${datum.metric.displayUnit}`;
function identityLines(model: ComparativeCardModel): readonly string[] {
  const person = model.person;
  if (!person)
    return [
      `no published player record for ${seasonLabel(model.season.season)}; absence is not zero`,
      ...(model.historicalPerson
        ? [
            `historical identity: ${playerName(model.historicalPerson)} (${seasonLabel(model.historicalPerson.season)})`,
          ]
        : []),
    ];
  const families = model.usage;
  const lines = [
    `${person.reported_position ?? "position unavailable"} · ${person.teams.map(teamName).join(" / ") || "teams unavailable"} · age ${displayNumber(person.age_years)} as of ${person.age_as_of}`,
  ];
  if (families?.availability === "provided") {
    const usage = families.data.reported_usage;
    lines.push(
      usage.availability === "provided"
        ? `${usage.data.positive_toi_appearances} positive-toi appearances · ${displayNumber(usage.data.minutes_per_appearance.value)} reported min/appearance · usage support ${usage.data.supported_games}/${usage.data.listed_games} listed games; ${usage.data.missing_games} missing${usage.data.minutes_per_appearance.value === null ? `; ${usage.data.minutes_per_appearance.unavailable_reason}; ${usage.data.minutes_per_appearance.reason_detail?.explanation ?? ""}` : ""}`
        : `reported usage: ${usage.explanation}`,
    );
    const observed = families.data.observed;
    lines.push(
      observed.availability === "provided"
        ? `included observed 5v5 time: ${displayNumber(observed.data.metrics.included_seconds / 60)} min · ${observed.data.metrics.coverage_status}`
        : `included observed 5v5 time unavailable: ${observed.explanation}`,
    );
  } else
    lines.push(
      `reported usage unavailable: ${families?.explanation ?? "no annual overview row"}`,
      `included observed 5v5 time unavailable: ${families?.explanation ?? "no annual overview row"}`,
    );
  const headerFields = {
    display_name: "name",
    reported_position: "position",
    teams: "teams",
    age_years: "age",
    age_as_of: "age reference date",
  };
  lines.push(
    ...person.identity_support.problems
      .filter((problem) => problem.field in headerFields)
      .map(
        (problem) =>
          `${headerFields[problem.field as keyof typeof headerFields]}: ${problem.explanation}`,
      ),
  );
  return lines;
}

function EmbeddedHistory({
  title,
  series,
  selectedSeason,
}: {
  readonly title: string;
  readonly series: readonly CardSeries[];
  readonly selectedSeason: string;
}) {
  const years = series[0].points;
  const x = (i: number) => 52 + i * 176;
  const y = (value: number) => 164 - value * 1.36;
  return (
    <figure className="comparative-history">
      <figcaption>{title} · annual percentile, 0–100</figcaption>
      <svg
        viewBox="0 0 456 212"
        role="img"
        aria-label={`${title}; annual raw values, peers and gaps follow in the expandable table`}
      >
        {[0, 50, 100].map((value) => (
          <g key={value}>
            <line
              x1="52"
              x2="404"
              y1={y(value)}
              y2={y(value)}
              stroke="#cbd2ce"
            />
            <text x="42" y={y(value) + 4} textAnchor="end">
              {value}
            </text>
          </g>
        ))}
        {years.map(({ point }, i) => (
          <g key={point.season.season}>
            {point.season.season === selectedSeason && (
              <rect
                x={x(i) - 10}
                y="22"
                width="20"
                height="148"
                fill="#d8e8e1"
              />
            )}
            <text x={x(i)} y="190" textAnchor="middle">
              {seasonLabel(point.season.season)}
            </text>
            {point.season.season === selectedSeason && (
              <text x={x(i)} y="207" textAnchor="middle">
                selected
              </text>
            )}
          </g>
        ))}
        {series.map((line) => (
          <g key={line.label} stroke={line.color} fill={line.color}>
            {line.points.map(({ point, value, breakBefore }, i) => (
              <g key={point.season.season}>
                {i > 0 &&
                  value !== null &&
                  line.points[i - 1].value !== null &&
                  !breakBefore && (
                    <line
                      x1={x(i - 1)}
                      x2={x(i)}
                      y1={y(line.points[i - 1].value!)}
                      y2={y(value)}
                      strokeWidth="2.5"
                      strokeDasharray={line.dash}
                    />
                  )}
                {value !== null && (
                  <circle cx={x(i)} cy={y(value)} r="4">
                    <title>{`${line.label}: ${value} percentile · ${magnitude(point)}`}</title>
                  </circle>
                )}
              </g>
            ))}
          </g>
        ))}
      </svg>
      <div className="comparative-history-legend">
        {series.map((line) => (
          <span key={line.label} style={{ color: line.color }}>
            <svg width="28" height="10" aria-hidden="true">
              <line
                x1="0"
                x2="28"
                y1="5"
                y2="5"
                stroke={line.color}
                strokeWidth="2"
                strokeDasharray={line.dash}
              />
            </svg>
            {line.label}
          </span>
        ))}
      </div>
      <details>
        <summary>annual values, peers, support and gaps</summary>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label={`${title} annual evidence table`}
        >
          <table>
            <thead>
              <tr>
                <th>quantity / season</th>
                <th>raw magnitude / standing</th>
                <th>identity / support / breaks</th>
              </tr>
            </thead>
            <tbody>
              {series.flatMap((line) =>
                line.points.map(({ point, value, breakBefore }) => (
                  <tr key={`${line.label}-${point.season.season}`}>
                    <th scope="row">
                      {line.label}
                      <br />
                      {seasonLabel(point.season.season)}
                    </th>
                    <td>
                      {magnitude(point)}
                      <p>{peersText(point)}</p>
                      {value === null && (
                        <p>
                          plot gap:{" "}
                          {point.standing.kind === "ranked"
                            ? "unavailable"
                            : point.standing.reason}
                        </p>
                      )}
                    </td>
                    <td>
                      {point.datum.person
                        ? `${playerName(point.datum.person)} · ${point.datum.person.reported_position ?? "position unavailable"} · ${point.datum.person.teams.map(teamName).join(" / ") || "teams unavailable"}`
                        : "absent annual identity"}
                      <p>{breakBefore && `line break: ${breakBefore}`}</p>
                      <DatumEvidence datum={point.datum} />
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

function Field({
  field,
  detailLink,
  headline = false,
}: {
  readonly field: CardField;
  readonly detailLink: (id: string) => { to: string; state: unknown };
  readonly headline?: boolean;
}) {
  return (
    <section
      className={headline ? "comparative-headline" : "comparative-tile"}
      aria-label={field.label}
    >
      <h4>
        <Link {...detailLink(field.row.datum.metric.id)}>{field.label}</Link>
      </h4>
      <p className="comparative-magnitude">{valueText(field.row.datum)}</p>
      <p className="comparative-unit">{field.row.datum.metric.displayUnit}</p>
      {field.row.standing.kind === "ranked" && (
        <meter
          min="0"
          max="100"
          value={field.row.standing.percentile}
          aria-label={`${field.label} percentile`}
        >
          {field.row.standing.percentile}
        </meter>
      )}
      <p>{peersText(field.row)}</p>
      <p className="comparative-construction">{field.construction}</p>
      <DatumEvidence datum={field.row.datum} />
    </section>
  );
}

export default function ComparativeCard({
  model,
  detailLink,
}: {
  readonly model: ComparativeCardModel;
  readonly detailLink: (id: string) => { to: string; state: unknown };
}) {
  const id = useId();
  const busy = useRef(false);
  const [status, setStatus] = useState("idle");
  const save = async (format: "png" | "csv") => {
    if (busy.current) return;
    busy.current = true;
    const snapshot = model;
    setStatus("preparing download");
    try {
      const blob = format === "png"
        ? await svgPng(comparativeCardSvg(
            snapshot,
            new URL(detailLink("ledger.league_total").to, window.location.href).href,
          ))
        : new Blob([comparativeCardCsv(snapshot)], { type: "text/csv;charset=utf-8" });
      downloadBlob(
        blob,
        `hockey-stats-${snapshot.playerId}-${snapshot.season.season}-${snapshot.publication.publication_id}-comparative.${format}`,
      );
      setStatus("saved");
    } catch {
      setStatus("download failed; retry available");
    } finally {
      busy.current = false;
    }
  };
  return (
    <article className="comparative-card" aria-labelledby={`${id}-title`}>
      <header>
        <p className="comparative-kicker">
          experimental seasonal level · comparative skater
        </p>
        {model.publication.purpose === "fixture" && (
          <p className="fixture-banner">
            fixture publication · development evidence
          </p>
        )}
        <h3 id={`${id}-title`}>
          {model.person ? playerName(model.person) : `player ${model.playerId}`}
        </h3>
        <p>
          {seasonLabel(model.season.season)} · player {model.playerId}
        </p>
        {identityLines(model).map((line, index) => (
          <p key={index}>{line}</p>
        ))}
        {model.person && (
          <details>
            <summary>identity sources and support</summary>
            <pre>
              {JSON.stringify(
                {
                  source: model.person.source,
                  identity_support: model.person.identity_support,
                },
                null,
                2,
              )}
            </pre>
          </details>
        )}
        {model.usage?.availability === "provided" && (
          <details>
            <summary>reported usage source, support and original value</summary>
            <pre>
              {JSON.stringify(model.usage.data.reported_usage, null, 2)}
            </pre>
          </details>
        )}
      </header>
      <p className="comparative-workload">
        {ledgerWorkload}. {ledgerLimits}
      </p>
      <div className="comparative-totals">
        <Field field={model.headline} detailLink={detailLink} headline />
        <Field field={model.replacement} detailLink={detailLink} />
      </div>
      <div className="comparative-tiles">
        {model.tiles.map((field) => (
          <Field
            key={field.row.datum.metric.id}
            field={field}
            detailLink={detailLink}
          />
        ))}
      </div>
      <div className="comparative-histories">
        <EmbeddedHistory
          title="league and replacement value history"
          series={model.headlineHistory}
          selectedSeason={model.season.season}
        />
        <EmbeddedHistory
          title="component history"
          series={model.componentHistory}
          selectedSeason={model.season.season}
        />
      </div>
      <p className="comparative-ledger">
        <Link {...detailLink("ledger.league_total")}>ten signed ledger terms and evidence</Link>
      </p>
      <footer>
        <p>
          percentiles describe annual standing, not confidence or causal
          isolation. no forecast or calibrated interval is implied.
        </p>
        <p>
          publication {model.publication.publication_id} ·{" "}
          {model.publication.purpose}
        </p>
        <div className="card-actions">
          {(["png", "csv"] as const).map((format) => (
            <button
              key={format}
              type="button"
              disabled={status === "preparing download"}
              onClick={() => void save(format)}
            >
              download comparative {format}
            </button>
          ))}
          <p role="status">{status === "idle" ? "" : status}</p>
        </div>
      </footer>
    </article>
  );
}

function comparativeCardCsv(model: ComparativeCardModel): string {
  return csvText(["card_section", "series", ...analysisCsvHeaders], [
    ...[model.headline, model.replacement, ...model.tiles].map(({ row }) => [
      "current", row.datum.metric.id,
      ...analysisCsvRow(model.publication, model.season, row),
    ]),
    ...[...model.headlineHistory, ...model.componentHistory].flatMap((series) =>
      series.points.map(({ point, breakBefore }) => [
        "history", point.datum.metric.id,
        ...analysisCsvRow(model.publication, point.season, point, breakBefore),
      ]),
    ),
  ]);
}

function comparativeCardSvg(model: ComparativeCardModel, detailLocation: string): string {
  const ns = "http://www.w3.org/2000/svg";
  const font = "system-ui, sans-serif";
  const graphemes = new Intl.Segmenter(undefined, { granularity: "grapheme" });
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("width", "1200");
  svg.setAttribute("font-family", font);
  svg.setAttribute("fill", "#242b2d");
  const element = (tag: string, attrs: Record<string, string | number>) => {
    const node = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs))
      node.setAttribute(key, String(value));
    svg.append(node);
    return node;
  };
  const background = element("rect", { width: 1200, fill: "#fbfaf6" });
  const measurement = document.createElementNS(ns, "svg");
  measurement.style.position = "fixed";
  measurement.setAttribute("width", "0");
  measurement.setAttribute("height", "0");
  measurement.setAttribute("aria-hidden", "true");
  const probe = document.createElementNS(ns, "text");
  probe.setAttribute("font-family", font);
  measurement.append(probe);
  document.body.append(measurement);
  const text = (
    value: string,
    x: number,
    top: number,
    width: number,
    size = 18,
    color = "#242b2d",
  ) => {
    probe.setAttribute("font-size", String(size));
    const fits = (candidate: string) => {
      probe.textContent = candidate;
      return probe.getComputedTextLength() <= width;
    };
    for (const paragraph of value.split("\n")) {
      const lines: string[] = [];
      let line = "";
      for (const word of paragraph.split(/\s+/)) {
        const joined = line ? `${line} ${word}` : word;
        if (fits(joined)) {
          line = joined;
          continue;
        }
        if (line) lines.push(line);
        line = "";
        for (const { segment } of graphemes.segment(word)) {
          if (line && !fits(line + segment)) {
            lines.push(line);
            line = "";
          }
          line += segment;
        }
      }
      if (line) lines.push(line);
      for (const content of lines) {
        const node = element("text", { x, y: top + size, "font-size": size, fill: color });
        node.textContent = content;
        top += size * 1.28;
      }
    }
    return top;
  };
  let top = 30;
  const ink = "#17696b";
  const muted = "#4f605b";
  const paragraph = (value: string, size = 18, color?: string) => {
    top = text(value, 42, top, 1116, size, color) + 3;
  };
  const rule = () => {
    top += 7;
    element("line", { x1: 42, x2: 1158, y1: top, y2: top, stroke: "#aebcb5" });
    top += 10;
  };
  const cohort = ({ standing }: AnalysisRow) => {
    const group = standing.peerGroup === "reported forwards" ? "F"
      : standing.peerGroup === "reported defense" ? "D"
      : standing.peerGroup === "all skaters" ? "all"
      : standing.peerGroup ?? "—";
    return `${group} n=${standing.n ?? "—"}`;
  };
  const field = (item: CardField, x: number, y: number, width: number, size = 34) => {
    const { datum, standing } = item.row;
    const isLedger = datum.metric.publicationFamily === "ledger";
    const label = standingText(standing);
    const standingLabel = label === datum.original?.unavailable_reason ? label.replaceAll("_", " ") : label;
    let bottom = text(item.label, x, y, width, 22);
    bottom = text(valueText(datum), x, bottom, width, size, ink);
    bottom = text(isLedger ? "goals / workload" : datum.metric.displayUnit, x, bottom, width);
    bottom = text(`${standingLabel} · ${cohort(item.row)}`, x, bottom, width);
    const seconds = datum.qualificationSeconds;
    bottom = text(
      `q ${seconds === null ? "—" : `${seconds} s`} · ${standing.cutoffMinutes === null ? "cutoff —" : `≥${standing.cutoffMinutes} min`}`,
      x, bottom, width, 18, muted,
    );
    return item === model.replacement ? text(item.construction, x, bottom, width, 18, muted) : bottom;
  };
  const chart = (title: string, series: readonly CardSeries[], left: number, chartTop: number) => {
    const axisTop = text(title, left, chartTop, 534, 22) + 3;
    const base = axisTop + 107;
    const x = (index: number) => left + 63 + index * 201;
    const y = (value: number) => base - value;
    series[0].points.forEach(({ point }, index) => {
      if (point.season.season === model.season.season) {
        element("rect", {
          x: x(index) - 17, y: axisTop, width: 34, height: 113, fill: "#d8e8e1",
        });
      }
    });
    for (const value of [0, 50, 100]) {
      element("line", {
        x1: left + 47, x2: left + 489, y1: y(value), y2: y(value), stroke: "#cbd2ce",
      });
      text(String(value), left, y(value) - 12, 45, 18, muted);
    }
    series[0].points.forEach(({ point }, index) => {
      text(seasonLabel(point.season.season), x(index) - 33, base + 7, 108);
      text(
        point.datum.person ? point.datum.person.reported_position ?? "position —" : "absent",
        x(index) - 7, base + 30, 108, 18, muted,
      );
    });
    let bottom = base + 55;
    for (const [seriesIndex, line] of series.entries()) {
      // Keep tied dots visible within the same annual tick.
      const px = (index: number) => x(index) + (seriesIndex - (series.length - 1) / 2) * 10;
      line.points.forEach(({ value, breakBefore }, index) => {
        if (value === null) return;
        const previous = line.points[index - 1]?.value;
        if (previous != null && !breakBefore)
          element("line", {
            x1: px(index - 1), x2: px(index), y1: y(previous), y2: y(value),
            stroke: line.color, "stroke-width": 3, "stroke-dasharray": line.dash,
          });
        element("circle", { cx: px(index), cy: y(value), r: 4.5, fill: line.color });
      });
      element("line", {
        x1: left, x2: left + 24, y1: bottom + 13, y2: bottom + 13,
        stroke: line.color, "stroke-width": 3, "stroke-dasharray": line.dash,
      });
      bottom = text(
        `${line.label} · ${line.points.map(({ point }) => cohort(point)).join(" / ")}`,
        left + 33, bottom, 501, 18, line.color,
      );
    }
    return bottom;
  };
  try {
    paragraph("experimental seasonal level · comparative skater", 22, ink);
    if (model.publication.purpose === "fixture")
      paragraph("fixture publication · development evidence", 18, muted);
    paragraph(model.person ? playerName(model.person) : `player ${model.playerId}`, 44);
    const identity = identityLines(model);
    paragraph(
      `${seasonLabel(model.season.season)} · player ${model.playerId}${model.person ? ` · ${identity[0]}` : ""}`,
      22,
    );
    identity.slice(model.person ? 1 : 0).forEach((line) => paragraph(line));

    rule();
    top = Math.max(
      field(model.headline, 42, top, 537, 54),
      field(model.replacement, 618, top, 540),
    );
    rule();
    for (let start = 0; start < model.tiles.length; start += 5) {
      top = Math.max(...model.tiles.slice(start, start + 5).map(
        (item, index) => field(item, 42 + index * 225, top, 216),
      )) + 10;
    }

    rule();
    top = Math.max(
      chart("league and depth-replacement history", model.headlineHistory, 42, top),
      chart("component history", model.componentHistory, 618, top),
    );
    rule();
    paragraph("annual percentile · 0–100 · shaded year selected · gaps or changes in reference or definition break lines");
    paragraph(`annual peers · ${model.settings.peers === "position" ? "by reported position" : "all skaters"} · F = reported forwards · D = reported defense · n = field cohort size`);
    paragraph(`${ledgerWorkload}. ${ledgerLimits}`);
    paragraph("goals and primary assists are recorded personal 5v5 rates. usage weights all-strength minutes per appearance by shared 5v5 time.");
    paragraph("the depth baseline is an annual weighted mean for each skater's own F/D group, using complete team-position groups.");

    const fields = [model.headline, model.replacement, ...model.tiles];
    const labelsByQualification = new Map<string, string[]>();
    for (const { row, label } of fields) {
      const basis = row.datum.metric.qualificationLabel;
      const scopes = labelsByQualification.get(basis) ?? [];
      scopes.push(label);
      labelsByQualification.set(basis, scopes);
    }
    paragraph(`qualifying exposure (q) · ${[...labelsByQualification].map(
      ([basis, scopes]) => `${basis} (${scopes.join(", ")})`,
    ).join(" · ")}`, 18, muted);
    const labels = new Map(fields.map(({ row, label }) => [row.datum.metric.id, label]));
    const annual = [...model.headlineHistory, ...model.componentHistory].flatMap(
      ({ points }) => points.map(({ point }) => ({
        row: point,
        year: seasonLabel(point.season.season),
      })),
    );
    const selectedYear = seasonLabel(model.season.season);
    const entries = [...fields.map(({ row }) => ({ row, year: selectedYear })), ...annual];
    type Scopes = Map<string, Set<string>>;
    const findings = new Map<string, Scopes>();
    const warnings = new Map<string, Scopes>();
    const modeled = new Map<string, Set<string>>();
    const methodYears = new Map<string, Set<string>>();
    const record = (notes: Map<string, Scopes>, summary: string, label: string, year: string) => {
      const scopes = notes.get(summary) ?? new Map<string, Set<string>>();
      const fields = scopes.get(year) ?? new Set<string>();
      fields.add(label);
      scopes.set(year, fields);
      notes.set(summary, scopes);
    };
    for (const { row: { datum }, year } of entries) {
      const label = labels.get(datum.metric.id)!;
      if (datum.metric.publicationFamily === "ledger") {
        const yearFields = modeled.get(year) ?? new Set<string>();
        yearFields.add(label);
        modeled.set(year, yearFields);
      }
      for (const method of datum.methods) {
        const years = methodYears.get(method.method_id) ?? new Set<string>();
        years.add(year);
        methodYears.set(method.method_id, years);
      }
      for (const { summary } of datum.findings) record(findings, summary, label, year);
      for (const [term, { support }] of Object.entries(datum.componentSupport)) {
        const name = term.replaceAll("_", " ");
        if (support?.prior_only) record(warnings, "prior-only ledger constituents", name, year);
        if (support?.unquantified_gap || (support?.known_excluded_seconds ?? 0) > 0)
          record(warnings, "ledger constituents with excluded or unquantified coverage", name, year);
      }
      if (datum.support?.unquantified_gap || (datum.support?.known_excluded_seconds ?? 0) > 0)
        record(warnings, "excluded or unquantified coverage", label, year);
      if (datum.observedSupport?.coverage_status === "partial")
        record(warnings, "partial recorded coverage", label, year);
      if (year === selectedYear && datum.original?.reason_detail)
        record(warnings, datum.original.reason_detail.explanation, label, year);
    }

    const scopeText = (scopes: Scopes) => {
      const yearsByFields = new Map<string, string[]>();
      const totals = [model.headline.label, model.replacement.label];
      for (const [year, fields] of scopes) {
        const ledgerFields = modeled.get(year);
        const allModeled = ledgerFields?.size === fields.size && [...fields].every((field) => ledgerFields.has(field));
        const scope = allModeled ? "all modeled values shown"
          : (totals.every((label) => fields.has(label))
              ? ["both totals", ...[...fields].filter((label) => !totals.includes(label))]
              : [...fields]).join(", ");
        const years = yearsByFields.get(scope) ?? [];
        years.push(year);
        yearsByFields.set(scope, years);
      }
      return [...yearsByFields].map(([scope, years]) => `${scope} (${years.sort().join(", ")})`).join(" · ");
    };
    for (const [warning, scope] of warnings)
      paragraph(`${warning} · ${scopeText(scope)}`);
    if (findings.size) {
      paragraph("modeled value: construction and numerical limits", 22, ink);
      for (const [summary, scopes] of findings) paragraph(`${summary} [${scopeText(scopes)}]`);
    }
    if (methodYears.size)
      paragraph(`methods · ${[...methodYears].map(([id, years]) => `${id} (${[...years].sort().join(", ")})`).join(" · ")}`, 18, muted);
    paragraph(`publication ${model.publication.publication_id} · ${model.publication.purpose}`, 18, muted);
    paragraph(`current localhost detail · ${detailLocation}`, 18, muted);

    const height = Math.ceil(top + 27);
    svg.setAttribute("height", String(height));
    svg.setAttribute("viewBox", `0 0 1200 ${height}`);
    background.setAttribute("height", String(height));
    return new XMLSerializer().serializeToString(svg);
  } finally {
    measurement.remove();
  }
}
