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
  DatumEvidence,
  displayNumber,
  prepareHistory,
  standingText,
  valueText,
  type AnalysisRow,
  type HistoryPoint,
} from "./analysis-history";
import { downloadBlob, svgPng } from "./export";
import { playerName, seasonLabel, teamName } from "./presentation";

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
const comparativeLedgerTerms = [
  ["5v5 offense", "five_on_five_offense", "spatial.5v5.offense_xg_per60"],
  ["5v5 defense", "five_on_five_defense", "spatial.5v5.defense_xg_per60"],
  ["pp offense", "power_play_offense", "spatial.pp.offense_xg_per60"],
  ["pk defense", "penalty_kill_defense", "spatial.pk.defense_xg_per60"],
  ["finishing", "finishing", "execution.5v5.finishing_goals_per100_attempts"],
  [
    "setting",
    "setting",
    "execution.5v5.setting_goals_per100_assisted_opportunities",
  ],
  ["drawing", "penalties_drawn", "penalties.drawn_value_per60"],
  ["taking", "penalties_taken", "penalties.taken_value_per60"],
  ["ice won", "ice_won", "territory.ice_won_goals_per_basket"],
  ["ice lost", "ice_lost", "territory.ice_lost_goals_per_basket"],
] as const;

type CardField = {
  readonly label: string;
  readonly construction: string;
  readonly row: AnalysisRow;
};
type CardSeries = {
  readonly label: string;
  readonly color: string;
  readonly dash: string;
  readonly points: readonly HistoryPoint[];
};
type ComparativeCardModel = {
  readonly playerId: string;
  readonly person: Person | null;
  readonly historicalPerson: Person | null;
  readonly season: SeasonEvidence;
  readonly publication: Publication;
  readonly settings: PeerSettings;
  readonly usage:
    ProfileView["overviewCohorts"][number]["players"][number]["result"] | null;
  readonly headline: CardField;
  readonly replacement: CardField;
  readonly tiles: readonly CardField[];
  readonly headlineHistory: readonly CardSeries[];
  readonly componentHistory: readonly CardSeries[];
  readonly ledger: readonly {
    readonly label: string;
    readonly league: AnalysisRow;
    readonly replacement: AnalysisRow;
    readonly detail: string;
  }[];
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
    annual.map((year) => point(year, id));
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
        "roster-depth proxy outside each team's top 12 forwards / 6 defensemen by regular-season usage, pooled by position",
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
    ledger: comparativeLedgerTerms.map(([label, term, detail]) => ({
      label,
      detail,
      league: row(`ledger.${term}.league_goals`),
      replacement: row(`ledger.${term}.replacement_goals`),
    })),
  };
}

const peersText = ({ standing, datum }: AnalysisRow) =>
  `${standingText(standing)} · ${standing.peerGroup ?? "reference unavailable"} · n=${standing.n ?? "unavailable"} · cutoff ${standing.cutoffMinutes ?? "unavailable"} min · qualification ${datum.qualificationSeconds ?? "unavailable"} s (${datum.metric.qualificationLabel})`;
const magnitude = ({ datum }: AnalysisRow) =>
  `${valueText(datum)} ${datum.metric.displayUnit}`;
const supportText = ({ datum }: AnalysisRow) => {
  const support = datum.support ?? datum.observedSupport;
  const direct = support
    ? `${support.included_seconds ?? "unknown"} included seconds; ${support.known_excluded_seconds ?? "unknown"} excluded seconds; ${"prior_only" in support ? `prior-only ${support.prior_only}; gap ${support.unquantified_gap}` : `recorded coverage ${support.coverage_status}`}`
    : "no aggregate support supplied";
  const components = Object.entries(datum.componentSupport)
    .map(
      ([term, component]) =>
        `${term}: ${component.support ? `${component.support.included_seconds ?? "unknown"} included seconds; ${component.support.known_excluded_seconds ?? "unknown"} excluded seconds; prior-only ${component.support.prior_only}; gap ${component.support.unquantified_gap}; inferred ${component.support.inferred_inputs.join(", ") || "none"}; reasons ${JSON.stringify(component.support.reason_counts)}` : component.reason}`,
    )
    .join("; ");
  return `${direct}${components ? `; constituent support: ${components}` : ""}${datum.reason ? `; ${datum.reason}` : ""}`;
};
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
  const prepared = series.map((line) => ({
    ...line,
    prepared: prepareHistory(line.points, "percentile"),
  }));
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
        {years.map((point, i) => (
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
        {prepared.map((line) => (
          <g key={line.label} stroke={line.color} fill={line.color}>
            {line.prepared.map(({ point, value, breakBefore }, i) => (
              <g key={point.season.season}>
                {i > 0 &&
                  value !== null &&
                  line.prepared[i - 1].value !== null &&
                  !breakBefore && (
                    <line
                      x1={x(i - 1)}
                      x2={x(i)}
                      y1={y(line.prepared[i - 1].value!)}
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
              {prepared.flatMap((line) =>
                line.prepared.map(({ point, value, breakBefore }) => (
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
        common workload: 1,000 5v5 + 100 pp + 100 pk minutes · favorable goals;
        higher is more of the named quantity. specialty minutes are
        hypothetical.
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
          title="league-relative value history"
          series={model.headlineHistory}
          selectedSeason={model.season.season}
        />
        <EmbeddedHistory
          title="component history"
          series={model.componentHistory}
          selectedSeason={model.season.season}
        />
      </div>
      <details className="comparative-ledger">
        <summary>ten signed ledger terms, references and evidence</summary>
        <p>
          the ten visible tiles are not ten additive terms. penalties groups
          drawing and taking; the totals below are published, never recomputed
          here. no aggregate ledger exposure or prior-only flag is inferred.
          support and methods are specific to each term.
        </p>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="signed ledger detail"
        >
          <table>
            <thead>
              <tr>
                <th>term / standalone detail</th>
                <th>league goals / common workload</th>
                <th>replacement goals / common workload</th>
              </tr>
            </thead>
            <tbody>
              {model.ledger.map((term) => (
                <tr key={term.label}>
                  <th scope="row">
                    <Link {...detailLink(term.detail)}>{term.label}</Link>
                  </th>
                  <td>
                    {magnitude(term.league)}
                    <DatumEvidence datum={term.league.datum} />
                  </td>
                  <td>
                    {magnitude(term.replacement)}
                    <DatumEvidence datum={term.replacement.datum} />
                  </td>
                </tr>
              ))}
              <tr>
                <th scope="row">published total</th>
                <td>{magnitude(model.headline.row)}</td>
                <td>{magnitude(model.replacement.row)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
      <footer>
        <p>
          percentiles describe annual standing, not confidence or causal
          isolation. no forecast or calibrated interval is implied.
        </p>
        <p>
          publication {model.publication.publication_id} ·{" "}
          {model.publication.purpose}
        </p>
        <button
          type="button"
          disabled={status === "rendering"}
          onClick={async () => {
            if (busy.current) return;
            busy.current = true;
            setStatus("rendering");
            // capture this immutable prepared view before awaiting image rendering.
            const snapshot = model;
            try {
              const blob = await svgPng(comparativeCardSvg(snapshot));
              downloadBlob(
                blob,
                `hockey-stats-${snapshot.playerId}-${snapshot.season.season}-${snapshot.publication.publication_id}-comparative.png`,
              );
              setStatus("saved");
            } catch {
              setStatus("download failed; retry available");
            } finally {
              busy.current = false;
            }
          }}
        >
          {status === "rendering"
            ? "rendering png…"
            : "download complete comparative png"}
        </button>
        <p role="status">{status === "idle" ? "" : status}</p>
      </footer>
    </article>
  );
}

// complete svg composition; measured wrapping gives long evidence content its own height.
function comparativeCardSvg(model: ComparativeCardModel): string {
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
  const measurement = document.createElementNS(ns, "svg");
  measurement.style.position = "fixed";
  measurement.setAttribute("width", "0");
  measurement.setAttribute("height", "0");
  measurement.setAttribute("aria-hidden", "true");
  const probe = document.createElementNS(ns, "text");
  measurement.append(probe);
  document.body.append(measurement);
  const text = (
    value: string,
    x: number,
    top: number,
    width: number,
    size = 20,
    color = "#242b2d",
  ) => {
    probe.setAttribute("font-family", "system-ui, sans-serif");
    probe.setAttribute("font-size", String(size));
    const fits = (candidate: string) => {
      probe.textContent = candidate;
      return probe.getComputedTextLength() <= width;
    };
    const lines: string[] = [];
    for (const paragraph of value.split("\n")) {
      let line = "";
      for (const word of paragraph.split(/\s+/)) {
        const joined = line ? `${line} ${word}` : word;
        if (fits(joined)) {
          line = joined;
          continue;
        }
        if (line) lines.push(line);
        line = "";
        for (const char of word) {
          if (line && !fits(line + char)) {
            lines.push(line);
            line = "";
          }
          line += char;
        }
      }
      if (line) lines.push(line);
    }
    for (const line of lines) {
      const node = element("text", {
        x,
        y: top + size,
        "font-size": size,
        fill: color,
      });
      node.textContent = line;
      top += size * 1.4;
    }
    return top + 8;
  };
  let top = 38;
  const paragraph = (value: string, size = 20) => {
    top = text(value, 48, top, 1104, size);
  };
  const field = (
    item: CardField,
    x: number,
    y: number,
    width: number,
    dominant = false,
  ) => {
    let bottom = text(item.label, x, y, width, dominant ? 29 : 22);
    bottom = text(
      valueText(item.row.datum),
      x,
      bottom,
      width,
      dominant ? 54 : 36,
      "#17696b",
    );
    bottom = text(item.row.datum.metric.displayUnit, x, bottom, width, 18);
    bottom = text(peersText(item.row), x, bottom, width, 17);
    bottom = text(item.construction, x, bottom, width, 17);
    if (item.row.datum.reason)
      bottom = text(item.row.datum.reason, x, bottom, width, 17);
    return bottom;
  };
  const chart = (
    title: string,
    series: readonly CardSeries[],
    left: number,
    chartTop: number,
  ) => {
    let bottom = text(
      `${title} · annual percentile 0–100`,
      left,
      chartTop,
      526,
      23,
    );
    const base = bottom + 160,
      x = (i: number) => left + 54 + i * 198,
      y = (value: number) => base - value * 1.4;
    for (const value of [0, 50, 100]) {
      element("line", {
        x1: left + 54,
        x2: left + 450,
        y1: y(value),
        y2: y(value),
        stroke: "#cbd2ce",
      });
      text(String(value), left + 4, y(value) - 12, 46, 16);
    }
    series[0].points.forEach((point, index) => {
      if (point.season.season === model.season.season)
        element("rect", {
          x: x(index) - 8,
          y: base - 144,
          width: 16,
          height: 150,
          fill: "#d8e8e1",
        });
      text(seasonLabel(point.season.season), x(index) - 46, base + 12, 110, 18);
      if (point.season.season === model.season.season)
        text("selected", x(index) - 38, base + 38, 100, 16);
    });
    for (const line of series) {
      const prepared = prepareHistory(line.points, "percentile");
      prepared.forEach(({ value, breakBefore }, index) => {
        if (
          index > 0 &&
          value !== null &&
          prepared[index - 1].value !== null &&
          !breakBefore
        )
          element("line", {
            x1: x(index - 1),
            x2: x(index),
            y1: y(prepared[index - 1].value!),
            y2: y(value),
            stroke: line.color,
            "stroke-width": 3,
            "stroke-dasharray": line.dash,
          });
        if (value !== null)
          element("circle", {
            cx: x(index),
            cy: y(value),
            r: 5,
            fill: line.color,
          });
      });
    }
    bottom = base + 70;
    for (const line of series) {
      element("line", {
        x1: left,
        x2: left + 28,
        y1: bottom + 13,
        y2: bottom + 13,
        stroke: line.color,
        "stroke-width": 3,
        "stroke-dasharray": line.dash,
      });
      bottom = text(line.label, left + 38, bottom, 480, 18, line.color);
    }
    return bottom;
  };
  try {
    paragraph("experimental seasonal level · comparative skater", 23);
    if (model.publication.purpose === "fixture")
      paragraph("fixture publication · development evidence", 23);
    paragraph(
      model.person ? playerName(model.person) : `player ${model.playerId}`,
      40,
    );
    paragraph(
      `${seasonLabel(model.season.season)} · player ${model.playerId}`,
      24,
    );
    identityLines(model).forEach((line) => paragraph(line));
    paragraph(
      "common workload: 1,000 5v5 + 100 pp + 100 pk minutes · favorable goals; specialty minutes are hypothetical.",
      22,
    );
    top = Math.max(
      field(model.headline, 48, top, 536, true),
      field(model.replacement, 616, top, 536),
    );
    for (let start = 0; start < model.tiles.length; start += 5) {
      const bottoms = model.tiles
        .slice(start, start + 5)
        .map((item, index) => field(item, 48 + index * 225, top + 20, 204));
      top = Math.max(...bottoms) + 22;
    }
    top =
      Math.max(
        chart("league-relative value history", model.headlineHistory, 48, top),
        chart("component history", model.componentHistory, 626, top),
      ) + 20;
    // compact evidence keys are shared only for identical supplied content.
    const notes = new Map<string, { key: string; value: string }>();
    const key = (prefix: string, value: string) => {
      const identity = `${prefix}:${value}`;
      const existing = notes.get(identity);
      if (existing) return existing.key;
      const label = `${prefix}${notes.size + 1}`;
      notes.set(identity, { key: label, value });
      return label;
    };
    const quantityKey = ({ datum }: AnalysisRow) =>
      key(
        "q",
        `native value ${datum.value ?? "unavailable"} ${datum.metric.unit}; qualification basis ${datum.qualificationBasis}; status ${datum.status}; reason ${datum.reason ?? "none"}; uncertainty ${JSON.stringify(datum.original && "uncertainty" in datum.original ? datum.original.uncertainty : null)}; field detail ${JSON.stringify(datum.original?.reason_detail ?? null)}; workload ${JSON.stringify(datum.workload)}; original observed support ${JSON.stringify(datum.observedSupport)}; original fact ${datum.original && "denominator_kind" in datum.original ? JSON.stringify(datum.original) : "not applicable"}`,
      );
    const refs = (row: AnalysisRow) => {
      const datum = row.datum;
      return `${quantityKey(row)}; ${key("s", supportText(row))}; ${key("m", `construction ${datum.construction}; population ${datum.population}; numerical reference ${datum.numericReference}; reference ${datum.referenceId}; support policy ${datum.supportPolicyId}; methods ${datum.methods.map((method) => `${method.method_id}; recipe ${method.recipe_id}; reference ${method.reference_id}: ${method.reference}; support policy ${method.support_policy_id}; limitations ${method.limitations.join("; ") || "none supplied"}`).join(" / ") || "unlinked"}; sources ${datum.sources.map((source) => `${source.source_id}: ${source.definition}; limitations ${source.limitations.join("; ") || "none supplied"}`).join(" / ") || "unlinked"}; findings ${datum.findings.map((finding) => `${finding.population}: ${finding.summary}`).join(" / ") || "none supplied"}`)}`;
    };
    paragraph(
      "annual history evidence · raw values, annual peers and gap reasons",
      25,
    );
    for (const series of [
      ...model.headlineHistory,
      ...model.componentHistory,
    ]) {
      paragraph(series.label, 22);
      for (const { point, value, breakBefore } of prepareHistory(
        series.points,
        "percentile",
      )) {
        paragraph(
          `${seasonLabel(point.season.season)}${point.season.season === model.season.season ? " · selected" : ""}: ${magnitude(point)} · ${peersText(point)}`,
          18,
        );
        paragraph(
          `${point.datum.person ? `${playerName(point.datum.person)} · ${point.datum.person.reported_position ?? "position unavailable"} · ${point.datum.person.teams.map(teamName).join(" / ") || "teams unavailable"}` : "absent annual identity"} · evidence ${refs(point)}${value === null ? ` · plot gap: ${point.standing.kind === "ranked" ? "unavailable" : point.standing.reason}` : ""}${breakBefore ? ` · line break: ${breakBefore}` : ""}`,
          17,
        );
        paragraph(`corpus ${point.season.corpus_sha256}`, 15);
      }
    }
    paragraph(
      "ten signed ledger terms · league / replacement goals per common workload",
      25,
    );
    paragraph(
      "the ten tiles are not the ten additive terms. penalties groups drawing and taking. totals are supplied by the publisher.",
      18,
    );
    for (const term of model.ledger)
      paragraph(
        `${term.label}: ${magnitude(term.league)} / ${magnitude(term.replacement)} · league evidence ${refs(term.league)}; replacement evidence ${refs(term.replacement)} · standalone ${term.detail}`,
        18,
      );
    paragraph(
      `published totals: ${magnitude(model.headline.row)} league / ${magnitude(model.replacement.row)} replacement`,
      22,
    );
    paragraph("selected-year quantity evidence", 25);
    for (const item of [model.headline, model.replacement, ...model.tiles]) {
      const datum = item.row.datum;
      paragraph(
        `${item.label}: ${magnitude(item.row)} · status ${datum.status}; ${datum.reason ?? "published value available"} · evidence ${refs(item.row)}`,
        18,
      );
    }
    if (model.usage?.availability === "provided")
      key(
        "usage",
        `reported usage original envelope: ${JSON.stringify(model.usage.data.reported_usage)}`,
      );
    paragraph(
      "evidence key · exact matching support and method records share a key",
      25,
    );
    for (const note of notes.values())
      paragraph(`${note.key}: ${note.value}`, 16);
    paragraph(
      `peer viewing choices: ${model.settings.peers}; general ${model.settings.peerMin} min; specialty ${model.settings.specialtyMin} min. cohort n is field- and year-specific.`,
      19,
    );
    paragraph(
      "percentiles describe standing of the published quantity, not confidence or causal isolation. no forecast or calibrated interval is implied. unavailable uncertainty is not a zero-width interval.",
      19,
    );
    paragraph(
      `publication ${model.publication.publication_id} · ${model.publication.purpose} · generated ${model.publication.generated_at} · selected corpus ${model.season.corpus_sha256}`,
      18,
    );
    const height = Math.ceil(top + 40);
    svg.setAttribute("height", String(height));
    svg.setAttribute("viewBox", `0 0 1200 ${height}`);
    bg.setAttribute("height", String(height));
    return new XMLSerializer().serializeToString(svg);
  } finally {
    measurement.remove();
  }
}
