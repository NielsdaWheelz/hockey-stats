import { useId, useState } from "react";
import { Link } from "react-router";
import { parseMinutes, type PeerSettings } from "./explorer";
import type { Publication, SeasonEvidence } from "../shared/observed";
import {
  analysisMetrics,
  type AnalysisDatum,
  type AnalysisMetric,
} from "./analysis-values";
import {
  midpointPercentile,
  type AnalysisCohort,
  type AnalysisPeerGroup,
} from "./analysis-cohorts";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  DatumEvidence,
  datumName,
  displayValue,
  displayNumber,
  valueText,
  plotDomain,
  standingText,
  type AnalysisRow,
} from "./analysis-history";
import { downloadCsv } from "./export";
import { fixtureNotice } from "./presentation";

export function PeerControls({
  settings,
  onChange,
  metric,
  allCutoffs = false,
}: {
  readonly settings: PeerSettings;
  readonly onChange: (settings: Partial<PeerSettings>) => void;
  readonly metric?: AnalysisMetric;
  readonly allCutoffs?: boolean;
}) {
  const id = useId();
  type Cutoff = "general" | "specialty";
  const committed = {
    general: settings.peerMin,
    specialty: settings.specialtyMin,
  };
  const [minutes, setMinutes] = useState({
    general: {
      committed: settings.peerMin,
      draft: String(settings.peerMin),
      error: "",
    },
    specialty: {
      committed: settings.specialtyMin,
      draft: String(settings.specialtyMin),
      error: "",
    },
  });
  if (
    minutes.general.committed !== committed.general ||
    minutes.specialty.committed !== committed.specialty
  ) {
    setMinutes({
      general:
        minutes.general.committed === committed.general
          ? minutes.general
          : {
              committed: committed.general,
              draft: String(committed.general),
              error: "",
            },
      specialty:
        minutes.specialty.committed === committed.specialty
          ? minutes.specialty
          : {
              committed: committed.specialty,
              draft: String(committed.specialty),
              error: "",
            },
    });
  }
  if (metric?.cutoff === "census" && !allCutoffs)
    return (
      <div className="reference-controls">
        <p>
          skating values are raw-only: census_unverified. a checked
          source-cohort contract is required before percentile ranks are
          available.
        </p>
      </div>
    );
  const cutoffs: readonly Cutoff[] = allCutoffs
    ? ["general", "specialty"]
    : [metric?.cutoff === "specialty" ? "specialty" : "general"];
  return (
    <div className="reference-controls">
      <div className="peer-controls">
        {metric?.kind !== "goalie" && (
          <div>
            <label htmlFor={`${id}-group`}>reference group</label>
            <select
              id={`${id}-group`}
              value={settings.peers}
              onChange={(event) =>
                onChange({
                  peers: event.currentTarget.value as PeerSettings["peers"],
                })
              }
            >
              <option value="position">reported position group</option>
              <option value="all">all skaters</option>
            </select>
          </div>
        )}
        {cutoffs.map((cutoff) => {
          const minute = minutes[cutoff];
          return (
            <form
              key={cutoff}
              className="minute-control"
              noValidate
              onSubmit={(event) => {
                event.preventDefault();
                const value = parseMinutes(minute.draft);
                if (value === undefined) {
                  setMinutes((previous) => ({
                    ...previous,
                    [cutoff]: {
                      ...previous[cutoff],
                      error:
                        "enter nonnegative whole minutes without leading zeros; minutes × 60 must be a safe integer.",
                    },
                  }));
                  return;
                }
                setMinutes((previous) => ({
                  ...previous,
                  [cutoff]: {
                    committed: value,
                    draft: String(value),
                    error: "",
                  },
                }));
                onChange(
                  cutoff === "specialty"
                    ? { specialtyMin: value }
                    : { peerMin: value },
                );
              }}
            >
              <label htmlFor={`${id}-${cutoff}-minimum`}>
                {cutoff} minimum peer included minutes ·{" "}
                {allCutoffs
                  ? cutoff === "specialty"
                    ? "pp and pk support, separately"
                    : "each field's matched general support"
                  : (metric?.qualificationLabel ??
                    "observed personal and on-ice 5v5, separately")}
              </label>
              <div className="minute-input">
                <input
                  id={`${id}-${cutoff}-minimum`}
                  inputMode="numeric"
                  value={minute.draft}
                  aria-invalid={Boolean(minute.error)}
                  aria-describedby={
                    minute.error ? `${id}-${cutoff}-error` : undefined
                  }
                  onChange={(event) => {
                    const draft = event.currentTarget.value;
                    setMinutes((previous) => ({
                      ...previous,
                      [cutoff]: { ...previous[cutoff], draft, error: "" },
                    }));
                  }}
                />
                <button type="submit">
                  apply {allCutoffs ? `${cutoff} ` : ""}peer minimum
                </button>
              </div>
              {minute.error && (
                <p
                  id={`${id}-${cutoff}-error`}
                  className="selection-error"
                  role="alert"
                >
                  {minute.error}
                </p>
              )}
            </form>
          );
        })}
        <button
          type="button"
          onClick={() => {
            setMinutes({
              general: { committed: 300, draft: "300", error: "" },
              specialty: { committed: 50, draft: "50", error: "" },
            });
            onChange({ peers: "position", peerMin: 300, specialtyMin: 50 });
          }}
        >
          reset peers
        </button>
      </div>
      <p className="control-note">
        membership uses exact matching seconds; zero cutoff still requires
        positive support. this viewing choice changes relative standing, not
        published values, model references or scientific support.
      </p>
    </div>
  );
}

function distributionRows(group: AnalysisPeerGroup): readonly AnalysisRow[] {
  const members = group.members.map((datum): AnalysisRow => ({
    datum,
    member: true,
    incompatiblePeerCount: group.incompatiblePeerCount,
    standing: {
      kind: "ranked",
      percentile: midpointPercentile(
        datum.value!,
        group.members.map((member) => member.value!),
      )!,
      n: group.members.length,
      peerGroup: group.peerGroup,
      cutoffMinutes: group.cutoffMinutes!,
    },
  }));
  const outsiders = group.selected
    .filter(
      ({ datum }) =>
        !group.members.some((member) => member.playerId === datum.playerId),
    )
    .map(({ datum, standing }): AnalysisRow => ({
      datum,
      standing,
      member: false,
      incompatiblePeerCount: group.incompatiblePeerCount,
    }));
  return [...members, ...outsiders];
}

export default function PeerDistributions({
  cohort,
  metric,
  onMetricChange,
  settings,
  onPeerChange,
  publication,
  season,
  profileLink,
  exportValues = false,
  showPeerControls = true,
}: {
  readonly cohort: AnalysisCohort;
  readonly metric: AnalysisMetric;
  readonly onMetricChange: (metric: AnalysisMetric) => void;
  readonly settings: PeerSettings;
  readonly onPeerChange: (settings: Partial<PeerSettings>) => void;
  readonly publication: Publication;
  readonly season: SeasonEvidence;
  readonly profileLink: (playerId: string) => {
    readonly to: string;
    readonly state: unknown;
  };
  readonly exportValues?: boolean;
  readonly showPeerControls?: boolean;
}) {
  const id = useId();
  const [status, setStatus] = useState("");
  const selected = cohort.groups.flatMap((group) => group.selected);
  const meanings = new Set(
    cohort.groups.flatMap((group) => [
      ...group.members.map((datum) => datum.semanticKey),
      ...group.selected
        .filter(({ datum }) => datum.value !== null)
        .map(({ datum }) => datum.semanticKey),
    ]),
  );
  const mismatch = meanings.size > 1;
  const selectedFamily = publication.families.find(
    (family) =>
      family.season === season.season &&
      family.family === metric.publicationFamily,
  );
  const rawOnly = metric.standingPolicy === "raw_only";
  const allRows = rawOnly ? [] : cohort.groups.flatMap(distributionRows);
  const domain = plotDomain(
    allRows
      .map(({ datum }) => displayValue(datum))
      .filter((value): value is number => value !== null),
  );
  const x = (value: number) =>
    `${8 + (84 * (value - domain![0])) / (domain![1] - domain![0])}%`;
  const grouped = new Map<string, AnalysisMetric[]>();
  for (const item of analysisMetrics.filter(
    (item) => item.kind === metric.kind,
  )) {
    const items = grouped.get(item.group) ?? [];
    items.push(item);
    grouped.set(item.group, items);
  }
  return (
    <section
      className="peer-context analysis-detail"
      aria-labelledby={`${id}-heading`}
    >
      <h3 id={`${id}-heading`}>selected published quantity</h3>
      <div className="metric-control">
        <label htmlFor={`${id}-metric`}>detail quantity</label>
        <select
          id={`${id}-metric`}
          value={metric.id}
          onChange={(event) =>
            onMetricChange(
              analysisMetrics.find(
                (item) => item.id === event.currentTarget.value,
              )!,
            )
          }
        >
          {[...grouped].map(([group, items]) => (
            <optgroup key={group} label={group}>
              {items.map((item) => {
                const family = publication.families.find(
                  (family) =>
                    family.season === season.season &&
                    family.family === item.publicationFamily,
                );
                return (
                  <option key={item.id} value={item.id}>
                    {item.label}
                    {family?.availability === "not_computed"
                      ? " · pending"
                      : ""}
                  </option>
                );
              })}
            </optgroup>
          ))}
        </select>
      </div>
      {selectedFamily?.availability === "not_computed" && (
        <p>pending family: {selectedFamily.explanation}</p>
      )}
      <p>
        <strong>{metric.label}</strong> · {metric.group} · {metric.displayUnit}
      </p>
      <p>
        numerical reference and population are resolved separately for each
        supplied value below. higher means more of this named quantity; it is
        not a universal quality score.
      </p>
      {publication.purpose === "fixture" && (
        <p className="fixture-notice">
          {fixtureNotice}
        </p>
      )}
      {showPeerControls && !rawOnly && (
        <PeerControls
          key={metric.cutoff}
          settings={settings}
          onChange={onPeerChange}
          metric={metric}
        />
      )}
      {mismatch && (
        <p className="selection-error">
          the displayed values have incompatible quantity definitions or
          numerical references. raw values and their separate references remain
          below; no joint plot or common rank comparison is shown.
        </p>
      )}
      <div className="analysis-selected-values">
        {selected.map(({ datum, slot, standing }) => (
          <article
            key={`${slot}-${datum.playerId}`}
            className="analysis-selected-value"
          >
            <h4>
              {selected.length > 1
                ? `${slot === 0 ? "first" : "second"}: `
                : ""}
              {datumName(datum)}
            </h4>
            <p className="rate-primary">
              <strong>{valueText(datum)}</strong> {metric.displayUnit}
            </p>
            <p>
              {rawOnly ? "no percentile defined" : <>{standingText(standing)} ·{" "}
              {standing.peerGroup ?? "reference unavailable"} · n=
              {standing.n ?? "unavailable"} · cutoff{" "}
              {standing.cutoffMinutes ?? "unavailable"} min</>}
            </p>
            <p>
              {datum.construction} · {datum.population} ·{" "}
              {datum.numericReference}
            </p>
            <p>
              qualification: {datum.qualificationSeconds ?? "unavailable"}{" "}
              matching seconds · {datum.qualificationBasis}
            </p>
            {datum.reason && <p>{datum.reason}</p>}
            <DatumEvidence datum={datum} />
          </article>
        ))}
      </div>
      {!mismatch && !rawOnly && (
        <figure
          className="peer-figure"
          data-metric={metric.id}
          data-domain-min={domain?.[0]}
          data-domain-max={domain?.[1]}
        >
          <h4>{metric.label} · empirical distribution</h4>
          <p>
            shared raw-unit scale in {metric.displayUnit}; every eligible peer
            contributes one mark. selected markers include out-of-cohort values.
            overlapping marks retain exact ties in the table. display labels use
            six significant digits; native table values and csv values remain
            exact.
          </p>
          {!domain && <p>no available value in this selection or reference.</p>}
          {cohort.groups.map((group) => (
            <div className="peer-lane" key={group.key}>
              <h5>{group.peerGroup}</h5>
              <p>
                {group.cutoffMinutes === null
                  ? "raw-only source population"
                  : `at least ${group.cutoffMinutes} matching included minutes`}{" "}
                · n={group.members.length} · {group.incompatiblePeerCount}{" "}
                incompatible peers excluded
              </p>
              {group.members.length === 0 && (
                <p>no eligible reference players</p>
              )}
              {group.members.length === 1 && (
                <p>one eligible reference player; midpoint rank is 50</p>
              )}
              {domain && (
                <svg
                  className="peer-rug"
                  width="100%"
                  height="36"
                  role="img"
                  aria-label={`${group.peerGroup}: ${group.members.length} empirical peer marks; exact values follow`}
                >
                  {group.members.map((datum) => (
                    <line
                      key={datum.playerId}
                      data-player-id={datum.playerId}
                      data-value={datum.value!}
                      x1={x(displayValue(datum)!)}
                      x2={x(displayValue(datum)!)}
                      y1="8"
                      y2="28"
                      className="peer-mark"
                    />
                  ))}
                </svg>
              )}
              {group.selected.map(({ datum, slot, standing }) => (
                <div className="selected-band" key={datum.playerId}>
                  <p>
                    {slot === 0 ? "circle" : "diamond"}: {datumName(datum)} ·{" "}
                    {valueText(datum)} {metric.displayUnit} ·{" "}
                    {standingText(standing)}
                  </p>
                  {domain && datum.value !== null && (
                    <svg
                      width="100%"
                      height="28"
                      role="img"
                      aria-label={`${datumName(datum)}: ${valueText(datum)} ${metric.displayUnit}`}
                    >
                      <g transform={`translate(0 14)`}>
                        {slot === 0 ? (
                          <circle
                            className="selected-mark"
                            cx={x(displayValue(datum)!)}
                            cy="0"
                            r="6"
                            data-player-id={datum.playerId}
                            data-value={datum.value}
                          />
                        ) : (
                          <svg
                            x={x(displayValue(datum)!)}
                            overflow="visible"
                            width="1"
                            height="1"
                          >
                            <path
                              className="selected-mark"
                              d="M 0 -7 L 7 0 L 0 7 L -7 0 Z"
                              data-player-id={datum.playerId}
                              data-value={datum.value}
                            />
                          </svg>
                        )}
                      </g>
                    </svg>
                  )}
                </div>
              ))}
            </div>
          ))}
          {domain && (
            <>
              <svg
                className="peer-axis"
                width="100%"
                height="18"
                role="img"
                aria-label={`shared scale ${displayNumber(domain[0])} to ${displayNumber(domain[1])} ${metric.displayUnit}`}
              >
                <line x1="8%" x2="92%" y1="5" y2="5" />
                {domain.map((value) => (
                  <line
                    key={value}
                    x1={x(value)}
                    x2={x(value)}
                    y1="5"
                    y2="13"
                  />
                ))}
              </svg>
              <div className="axis-endpoints">
                <span>minimum {displayNumber(domain[0])}</span>
                <span>maximum {displayNumber(domain[1])}</span>
              </div>
            </>
          )}
          <figcaption>
            empirical spread is not an uncertainty interval. ranks use exact
            native values and count half of exact ties. partial support may
            qualify; missing qualification cannot manufacture a rank.
          </figcaption>
        </figure>
      )}
      {!rawOnly && cohort.groups.map((group) => (
        <details className="peer-values" key={group.key}>
          <summary>
            {group.peerGroup}: numeric values ({distributionRows(group).length}{" "}
            rows)
          </summary>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label={`${group.peerGroup} selected quantity table, scroll horizontally for all columns`}
          >
            <table className="peer-table">
              <caption>
                reference members in name/id order, followed by selected
                outsiders once; exact native units remain visible.{" "}
                {group.incompatiblePeerCount} incompatible peers are excluded.
                {group.members[0] &&
                  ` population: ${group.members[0].population}; numerical reference: ${group.members[0].numericReference}.`}
              </caption>
              <thead>
                <tr>
                  <th scope="col">player / position</th>
                  <th scope="col">value / native unit</th>
                  <th scope="col">reference member</th>
                  <th scope="col">standing</th>
                  <th scope="col">support / evidence</th>
                </tr>
              </thead>
              <tbody>
                {distributionRows(group).map((row) => (
                  <tr
                    key={row.datum.playerId}
                    data-player-id={row.datum.playerId}
                  >
                    <th scope="row">
                      <Link {...profileLink(row.datum.playerId)}>
                        {datumName(row.datum)}
                      </Link>
                      <span className="history-context">
                        {row.datum.person?.reported_position ??
                          "position unavailable"}
                        {group.selected.some(
                          ({ datum }) => datum.playerId === row.datum.playerId,
                        )
                          ? " · selected"
                          : ""}
                      </span>
                    </th>
                    <td>
                      {row.datum.value ?? "unavailable"}{" "}
                      {metric.unit.startsWith("goals_per100_") ? metric.displayUnit : metric.unit}
                      {metric.displayScale !== 1 && (
                        <span className="history-context">
                          {valueText(row.datum)} {metric.displayUnit}
                        </span>
                      )}
                      <p>{row.datum.reason}</p>
                      <p>{row.datum.numericReference}</p>
                    </td>
                    <td>{row.member ? "yes" : "no · selected outsider"}</td>
                    <td>
                      {standingText(row.standing)}
                      <br />
                      n={row.standing.n ?? "unavailable"} · cutoff{" "}
                      {row.standing.cutoffMinutes ?? "unavailable"} min
                    </td>
                    <td>
                      <DatumEvidence datum={row.datum} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ))}
      {exportValues && !rawOnly && (
        <div className="card-actions">
          <button
            type="button"
            onClick={() => {
              const snapshot = { publication, season, metric, rows: allRows };
              try {
                downloadCsv(
                  analysisCsvHeaders,
                  snapshot.rows.map((row) =>
                    analysisCsvRow(snapshot.publication, snapshot.season, row),
                  ),
                  `hockey-stats-${selected.map(({ datum }) => datum.playerId).join("-")}-${snapshot.metric.id}-${snapshot.season.season}-distribution.csv`,
                );
                setStatus("distribution csv prepared");
              } catch {
                setStatus("export failed; retry the download.");
              }
            }}
          >
            download distribution csv
          </button>
          <p role="status">{status}</p>
          <p className="control-note">
            csv exports only these named peer groups and selected outsiders, in
            table order. native numeric units stay exact; textual formula
            prefixes receive a leading apostrophe.
          </p>
        </div>
      )}
    </section>
  );
}
