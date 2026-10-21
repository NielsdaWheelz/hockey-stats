import { useId, useState } from "react";
import { Link } from "react-router";
import type { PlayerSummary } from "../shared/observed";
import {
  parseMinutes,
  selectPeerGroups,
  type PeerGroup,
  type PeerSettings,
} from "./explorer";
import { CoverageDetail, Minutes, Quantity, playerName } from "./presentation";

const groupName = (key: PeerGroup["key"]) =>
  key === "all"
    ? "all skaters"
    : key === "f"
      ? "reported forwards"
      : "reported defense";
type RateKey = "for_per60" | "against_per60";
type Domain = readonly [number, number];

function RateFigure({
  groups,
  metric,
  title,
  domain,
}: {
  readonly groups: readonly PeerGroup[];
  readonly metric: RateKey;
  readonly title: string;
  readonly domain: Domain | undefined;
}) {
  const id = useId();
  const x = (value: number) =>
    `${8 + 84 * ((value - domain![0]) / (domain![1] - domain![0]))}%`;
  return (
    <figure
      className="peer-figure"
      data-metric={metric}
      data-domain-min={domain?.[0]}
      data-domain-max={domain?.[1]}
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-description`}
    >
      <h4 id={`${id}-title`}>{title}</h4>
      <p id={`${id}-description`} className="chart-description">
        {groups.map((group) => groupName(group.key)).join("; ")} · attempts per
        60 included 5v5 minutes. numeric selected values and peer tables follow.
      </p>
      {!domain ? (
        <p>
          no published rate values are available for this reference or
          selection.
        </p>
      ) : (
        <>
          {groups.map((group) => (
            <div className="peer-lane" key={group.key} data-group={group.key}>
              <h5>{groupName(group.key)}</h5>
              {group.members.length === 0 && (
                <p className="control-note">no players meet this peer rule</p>
              )}
              <svg
                className="peer-rug"
                width="100%"
                height="32"
                role="img"
                aria-label={`${groupName(group.key)}: ${group.members.length} player marks; numeric values in the peer table`}
                data-domain-min={domain[0]}
                data-domain-max={domain[1]}
              >
                {group.members.map((player) => (
                  <line
                    key={player.player_id}
                    data-player-id={player.player_id}
                    data-value={player.metrics[metric]!}
                    x1={x(player.metrics[metric]!)}
                    x2={x(player.metrics[metric]!)}
                    y1="8"
                    y2="26"
                    className="peer-mark"
                  />
                ))}
              </svg>
              {group.selected.map(({ player, slot }) => (
                <div className="selected-band" key={player.player_id}>
                  <p>
                    {slot === 0 ? "circle" : "diamond"} ·{" "}
                    {group.selected.length === 1 && groups.length === 1
                      ? "selected"
                      : slot === 0
                        ? "first"
                        : "second"}
                    : {playerName(player)} ·{" "}
                    <Quantity
                      value={player.metrics[metric]}
                      metrics={player.metrics}
                      rate
                    />
                  </p>
                  {player.metrics[metric] !== null && (
                    <svg
                      width="100%"
                      height="24"
                      role="img"
                      aria-label={`${playerName(player)}: ${player.metrics[metric]} attempts per 60 included minutes`}
                      data-domain-min={domain[0]}
                      data-domain-max={domain[1]}
                    >
                      {slot === 0 ? (
                        <circle
                          className="selected-mark"
                          data-selected-slot={slot}
                          data-player-id={player.player_id}
                          data-value={player.metrics[metric]}
                          cx={x(player.metrics[metric])}
                          cy="12"
                          r="5"
                        />
                      ) : (
                        <svg
                          x={x(player.metrics[metric])}
                          y="12"
                          overflow="visible"
                          width="1"
                          height="1"
                        >
                          <path
                            className="selected-mark"
                            data-selected-slot={slot}
                            data-player-id={player.player_id}
                            data-value={player.metrics[metric]}
                            data-x={x(player.metrics[metric])}
                            d="M 0 -6 L 6 0 L 0 6 L -6 0 Z"
                          />
                        </svg>
                      )}
                    </svg>
                  )}
                </div>
              ))}
            </div>
          ))}
          <svg
            className="peer-axis"
            width="100%"
            height="16"
            role="img"
            aria-label={`shared rate scale from ${domain[0]} to ${domain[1]}, increasing rightward`}
            data-domain-min={domain[0]}
            data-domain-max={domain[1]}
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
        marks overlap; values are available below. spread describes observed
        player results, not uncertainty about ability.
      </figcaption>
    </figure>
  );
}

export default function PeerDistributions({
  players,
  selected,
  settings,
  onChange,
  profileLink,
}: {
  readonly players: readonly PlayerSummary[];
  readonly selected: readonly PlayerSummary[];
  readonly settings: PeerSettings;
  readonly onChange: (settings: PeerSettings) => void;
  readonly profileLink: (playerId: string) => {
    readonly to: string;
    readonly state: unknown;
  };
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
  const groups = selectPeerGroups(players, selected, settings);
  let low = Infinity;
  let high = -Infinity;
  for (const group of groups) {
    for (const player of [
      ...group.members,
      ...group.selected.map((entry) => entry.player),
    ]) {
      for (const value of [
        player.metrics.for_per60,
        player.metrics.against_per60,
      ]) {
        if (value !== null) {
          low = Math.min(low, value);
          high = Math.max(high, value);
        }
      }
    }
  }
  let domain: Domain | undefined;
  if (Number.isFinite(low)) {
    if (low === high) {
      const padding = Math.max(1, low * 0.05);
      const upper = high + padding;
      low = Math.max(0, low - padding);
      high = Number.isFinite(upper) ? upper : high;
    }
    domain = [Math.floor(low), Math.ceil(high)];
  }
  return (
    <section className="peer-context" aria-labelledby={`${id}-heading`}>
      <h3 id={`${id}-heading`}>observed peer context</h3>
      <div className="peer-controls">
        <div>
          <label htmlFor={`${id}-group`}>reference group</label>
          <select
            id={`${id}-group`}
            value={settings.peers}
            onChange={(event) =>
              onChange({
                ...settings,
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
            onChange({ ...settings, peerMin: value });
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
      <div className="peer-counts" role="status">
        {groups.map((group) => (
          <p key={group.key}>
            {groupName(group.key)} · at least {settings.peerMin} included 5v5
            minutes · {group.members.length} players,{" "}
            {
              group.members.filter(
                (player) => player.metrics.coverage_status === "partial",
              ).length
            }{" "}
            partial
            {group.members.length === 0 && (
              <> · no players meet this peer rule</>
            )}
          </p>
        ))}
      </div>
      <p className="control-note">
        one mark per player; shared play means these are related observations.
        the cutoff is a viewing rule, not a reliability threshold. reported
        position groups do not verify deployment or equal exposure.
      </p>
      <div className="peer-figures">
        <RateFigure
          groups={groups}
          metric="for_per60"
          title="on-ice attempts for/60"
          domain={domain}
        />
        <RateFigure
          groups={groups}
          metric="against_per60"
          title="on-ice attempts against/60"
          domain={domain}
        />
      </div>
      <div className="selected-peer-values" aria-label="selected player values">
        {selected.map((player, slot) => {
          const member = groups.some((group) =>
            group.members.some((row) => row.player_id === player.player_id),
          );
          return (
            <div key={player.player_id}>
              <h4>
                {selected.length === 1
                  ? "selected"
                  : slot === 0
                    ? "first"
                    : "second"}
                : {playerName(player)}
              </h4>
              <p>
                for/60:{" "}
                <Quantity
                  value={player.metrics.for_per60}
                  metrics={player.metrics}
                  rate
                />{" "}
                · against/60:{" "}
                <Quantity
                  value={player.metrics.against_per60}
                  metrics={player.metrics}
                  rate
                />{" "}
                · <Minutes seconds={player.metrics.included_seconds} /> included
                minutes
              </p>
              {!member && (
                <p className="outside-reference">
                  outside reference:{" "}
                  {player.metrics.included_seconds === 0
                    ? "no included exposure"
                    : player.metrics.included_seconds < settings.peerMin * 60
                      ? `under ${settings.peerMin} included minutes`
                      : "published rates unavailable"}
                </p>
              )}
              <CoverageDetail metrics={player.metrics} />
            </div>
          );
        })}
      </div>
      {groups.map((group) => (
        <details className="peer-values" key={group.key}>
          <summary>
            {groupName(group.key)} · numeric peer values ({group.members.length}{" "}
            players)
          </summary>
          <div
            className="table-scroll"
            tabIndex={0}
            aria-label={`${groupName(group.key)} peer values table, scroll horizontally for all columns`}
          >
            <table className="peer-table">
              <caption>
                one row per reference member; exact membership uses unrounded
                included seconds, displayed rates use one decimal.
              </caption>
              <thead>
                <tr>
                  <th scope="col">player</th>
                  <th scope="col">reported position</th>
                  <th scope="col" className="numeric">
                    included min
                  </th>
                  <th scope="col" className="numeric">
                    for/60
                  </th>
                  <th scope="col" className="numeric">
                    against/60
                  </th>
                  <th scope="col">coverage</th>
                </tr>
              </thead>
              <tbody>
                {group.members.map((player) => {
                  const entry = group.selected.find(
                    (row) => row.player.player_id === player.player_id,
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
                            {selected.length === 1
                              ? "selected"
                              : entry.slot === 0
                                ? "first"
                                : "second"}
                          </span>
                        )}
                      </th>
                      <td>{player.reported_position}</td>
                      <td className="numeric">
                        <Minutes seconds={player.metrics.included_seconds} />
                      </td>
                      <td className="numeric">
                        <Quantity
                          value={player.metrics.for_per60}
                          metrics={player.metrics}
                          rate
                        />
                      </td>
                      <td className="numeric">
                        <Quantity
                          value={player.metrics.against_per60}
                          metrics={player.metrics}
                          rate
                        />
                      </td>
                      <td>
                        <CoverageDetail metrics={player.metrics} />
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
