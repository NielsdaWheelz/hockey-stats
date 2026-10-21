import { useId, useState } from "react";
import { Link } from "react-router";
import { parseMinutes, type PeerSettings } from "./explorer";
import {
  observedMetrics,
  metricDefinition,
  observedStanding,
  formatPercentile,
  peerGroupName,
  populationSupport,
  type ObservedComparison,
  type ObservedRateKey,
} from "./observed-comparison";
import { CoverageDetail, Minutes, Quantity, playerName } from "./presentation";

export function PeerControls({
  settings,
  onChange,
}: {
  readonly settings: PeerSettings;
  readonly onChange: (settings: Partial<PeerSettings>) => void;
}) {
  const id = useId();
  const [minute, setMinute] = useState({
    committed: settings.peerMin,
    draft: String(settings.peerMin),
    error: "",
  });
  if (minute.committed !== settings.peerMin)
    setMinute({
      committed: settings.peerMin,
      draft: String(settings.peerMin),
      error: "",
    });
  return (
    <div className="reference-controls">
      <div className="peer-controls">
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
        <form
          className="minute-control"
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            const value = parseMinutes(minute.draft);
            if (value === undefined) {
              setMinute({
                ...minute,
                error:
                  "enter nonnegative whole minutes without leading zeros; minutes × 60 must be a safe integer.",
              });
              return;
            }
            setMinute({ committed: value, draft: String(value), error: "" });
            onChange({ peerMin: value });
          }}
        >
          <label htmlFor={`${id}-minimum`}>
            minimum peer included 5v5 minutes
          </label>
          <div className="minute-input">
            <input
              id={`${id}-minimum`}
              inputMode="numeric"
              value={minute.draft}
              aria-invalid={Boolean(minute.error)}
              aria-describedby={minute.error ? `${id}-error` : undefined}
              onChange={(event) =>
                setMinute({
                  ...minute,
                  draft: event.currentTarget.value,
                  error: "",
                })
              }
            />
            <button type="submit">apply peer minimum</button>
          </div>
          {minute.error && (
            <p id={`${id}-error`} className="selection-error" role="alert">
              {minute.error}
            </p>
          )}
        </form>
        <button
          type="button"
          onClick={() => {
            setMinute({ committed: 300, draft: "300", error: "" });
            onChange({ peers: "position", peerMin: 300 });
          }}
        >
          reset peers
        </button>
      </div>
      <p className="control-note">
        the minimum applies separately to personal and on-ice included time.
        membership uses exact seconds; displayed minutes are rounded. it is a
        viewing rule, not a reliability threshold. reported groups do not verify
        deployment or equal exposure.
      </p>
    </div>
  );
}

export default function PeerDistributions({
  comparison,
  metric,
  onMetricChange,
  profileLink,
}: {
  readonly comparison: ObservedComparison;
  readonly metric: ObservedRateKey;
  readonly onMetricChange: (metric: ObservedRateKey) => void;
  readonly profileLink: (playerId: string) => {
    readonly to: string;
    readonly state: unknown;
  };
}) {
  const id = useId();
  const definition = metricDefinition(metric);
  const groups = comparison.groups[definition.population];
  let low = Infinity;
  let high = -Infinity;
  for (const group of groups) {
    for (const player of [
      ...group.members,
      ...group.selected.map((entry) => entry.player),
    ]) {
      const value = definition.rate(player);
      if (value !== null) {
        low = Math.min(low, value);
        high = Math.max(high, value);
      }
    }
  }
  // rates are nonnegative; expand constants while retaining finite bounds.
  if (low === high && Number.isFinite(low)) {
    const padding = Math.max(1, Math.abs(low) * 0.05);
    low = Math.max(0, low - padding);
    high = Number.isFinite(high + padding) ? high + padding : high;
  }
  const domain = Number.isFinite(low) ? ([low, high] as const) : undefined;
  const x = (value: number) => `${8 + 84 * ((value - low) / (high - low))}%`;
  const family = definition.population === "personal" ? "personal" : "on-ice";
  return (
    <section className="peer-context" aria-labelledby={`${id}-heading`}>
      <h3 id={`${id}-heading`}>observed raw-rate detail</h3>
      <div className="metric-control">
        <label htmlFor={`${id}-metric`}>detail metric</label>
        <select
          id={`${id}-metric`}
          value={metric}
          onChange={(event) =>
            onMetricChange(event.currentTarget.value as ObservedRateKey)
          }
        >
          {observedMetrics.map((entry) => (
            <option key={entry.key} value={entry.key}>
              {entry.label}
            </option>
          ))}
        </select>
      </div>
      <figure
        className="peer-figure"
        data-metric={metric}
        data-domain-min={domain?.[0]}
        data-domain-max={domain?.[1]}
        aria-labelledby={`${id}-title`}
        aria-describedby={`${id}-description`}
      >
        <h4 id={`${id}-title`}>{definition.label} per 60</h4>
        <p id={`${id}-description`} className="chart-description">
          {groups.map((group) => peerGroupName(group.key)).join("; ")} · per 60
          included {family} 5v5 minutes. each player has one mark; selected
          circles and diamonds annotate that distribution. exact numerical
          tables follow.{" "}
          {metric === "against60" && "higher = more opponent attempts."}
        </p>
        {!domain && (
          <p>
            no published rate values are available for this reference or
            selection.
          </p>
        )}
        {groups.map((group) => (
          <div className="peer-lane" key={group.key} data-group={group.key}>
            <h5>
              {peerGroupName(group.key)} · {family} reference
            </h5>
            <p className="reference-summary">
              at least {comparison.settings.peerMin} included 5v5 minutes · n ={" "}
              {group.members.length}; partial n = {group.partialCount}
            </p>
            {group.members.length === 0 && (
              <p className="control-note">no players meet this peer rule</p>
            )}
            {group.members.length === 1 && (
              <p className="control-note">
                one eligible player; no between-player comparison
              </p>
            )}
            {domain && (
              <svg
                className="peer-rug"
                width="100%"
                height="32"
                role="img"
                aria-label={`${peerGroupName(group.key)}: ${group.members.length} player marks; numeric values in the peer table`}
              >
                {group.members.map((player) => (
                  <line
                    key={player.player_id}
                    data-player-id={player.player_id}
                    data-value={definition.rate(player)!}
                    x1={x(definition.rate(player)!)}
                    x2={x(definition.rate(player)!)}
                    y1="8"
                    y2="26"
                    className="peer-mark"
                  />
                ))}
              </svg>
            )}
            {group.selected.map(({ player, slot }) => {
              const row = comparison.cards
                .find((card) => card.slot === slot)!
                .rows.find((row) => row.metric === metric)!;
              const support = populationSupport(player, definition.population);
              return (
                <div className="selected-band" key={player.player_id}>
                  <p>
                    {slot === 0 ? "circle" : "diamond"} ·{" "}
                    {comparison.cards.length === 1
                      ? "selected"
                      : slot === 0
                        ? "first"
                        : "second"}
                    : {playerName(player)} ·{" "}
                    <Quantity
                      value={row.rate}
                      metrics={support}
                      rate
                      precision={definition.precision}
                    />{" "}
                    per 60 ·{" "}
                    {row.standing.kind === "ranked"
                      ? `${formatPercentile(row.standing.percentile)} observed-rate percentile`
                      : row.standing.kind === "unavailable"
                        ? "rate unavailable"
                        : support.included_seconds <
                            comparison.settings.peerMin * 60
                          ? `outside reference: under ${comparison.settings.peerMin} ${family} minutes`
                          : "outside reference"}
                  </p>
                  {domain && row.rate !== null && (
                    <svg
                      width="100%"
                      height="24"
                      role="img"
                      aria-label={`${playerName(player)}: ${row.rate} per 60 included ${family} minutes`}
                    >
                      {slot === 0 ? (
                        <circle
                          className="selected-mark"
                          data-selected-slot={slot}
                          data-player-id={player.player_id}
                          data-value={row.rate}
                          cx={x(row.rate)}
                          cy="12"
                          r="5"
                        />
                      ) : (
                        <svg
                          x={x(row.rate)}
                          y="12"
                          overflow="visible"
                          width="1"
                          height="1"
                        >
                          <path
                            className="selected-mark"
                            data-selected-slot={slot}
                            data-player-id={player.player_id}
                            data-value={row.rate}
                            data-x={x(row.rate)}
                            d="M 0 -6 L 6 0 L 0 6 L -6 0 Z"
                          />
                        </svg>
                      )}
                    </svg>
                  )}
                </div>
              );
            })}
          </div>
        ))}
        {domain && (
          <>
            <svg
              className="peer-axis"
              width="100%"
              height="16"
              role="img"
              aria-label={`shared rate scale from ${domain[0]} to ${domain[1]}, increasing rightward`}
            >
              <line x1="8%" x2="92%" y1="6" y2="6" />
              {domain.map((value, index) => (
                <line key={index} x1={x(value)} x2={x(value)} y1="6" y2="12" />
              ))}
            </svg>
            <div className="axis-endpoints">
              <span>
                minimum <span>{domain[0]}</span>
              </span>
              <span>
                maximum <span>{domain[1]}</span>
              </span>
            </div>
          </>
        )}
        <figcaption>
          marks overlap; separate selection labels and numerical tables retain
          tied values. shared play makes these related observations. spread
          describes recorded results, not uncertainty about ability.
        </figcaption>
      </figure>
      {groups.map((group) => (
        <details className="peer-values" key={group.key}>
          <summary>
            {peerGroupName(group.key)} · numeric peer values (
            {group.members.length} players)
          </summary>
          <div
            className="table-scroll"
            tabIndex={0}
            aria-label={`${peerGroupName(group.key)} peer values table, scroll horizontally for all columns`}
          >
            <table className="peer-table">
              <caption>
                exactly one row per reference member, ordered by name and id.
                standing uses unrounded published rates; equal displayed rates
                can have different percentiles. ties count half.
              </caption>
              <thead>
                <tr>
                  <th scope="col">player</th>
                  <th scope="col">reported position</th>
                  <th scope="col" className="numeric">
                    count
                  </th>
                  <th scope="col" className="numeric">
                    {family} included min
                  </th>
                  <th scope="col" className="numeric">
                    rate per 60
                  </th>
                  <th scope="col" className="numeric">
                    observed-rate percentile
                  </th>
                  <th scope="col">coverage</th>
                </tr>
              </thead>
              <tbody>
                {group.members.map((player) => {
                  const support = populationSupport(
                    player,
                    definition.population,
                  );
                  const standing = observedStanding(
                    definition.rate(player),
                    player.player_id,
                    group,
                    metric,
                  );
                  const entry = group.selected.find(
                    (entry) => entry.player.player_id === player.player_id,
                  );
                  return (
                    <tr
                      key={player.player_id}
                      data-player-id={player.player_id}
                    >
                      <th scope="row">
                        <Link {...profileLink(player.player_id)}>
                          {playerName(player)}
                        </Link>
                        {entry && (
                          <span className="peer-selection-label">
                            {comparison.cards.length === 1
                              ? "selected"
                              : entry.slot === 0
                                ? "first"
                                : "second"}
                          </span>
                        )}
                      </th>
                      <td>{player.reported_position}</td>
                      <td className="numeric">
                        <Quantity
                          value={definition.count(player)}
                          metrics={support}
                        />
                      </td>
                      <td className="numeric">
                        <Minutes seconds={support.included_seconds} />
                      </td>
                      <td className="numeric">
                        <Quantity
                          value={definition.rate(player)}
                          metrics={support}
                          rate
                          precision={definition.precision}
                        />
                      </td>
                      <td className="numeric">
                        {standing.kind === "ranked"
                          ? formatPercentile(standing.percentile)
                          : "unavailable"}
                      </td>
                      <td>
                        <CoverageDetail metrics={support} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </details>
      ))}
    </section>
  );
}
