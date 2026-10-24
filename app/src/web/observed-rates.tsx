import type { PlayerSummary } from "../shared/observed";
import type { PeerSettings } from "./explorer";
import {
  formatPercentile,
  metricDefinition,
  peerGroupName,
  populationSupport,
  type ObservedCard,
  type ObservedComparison,
  type ObservedRateRow,
  type PeerGroup,
} from "./observed-comparison";
import { CoverageDetail, Minutes, Quantity } from "./presentation";

const familyName = (population: ObservedRateRow["population"]) =>
  population === "personal" ? "personal" : "on-ice";

function referenceText(group: PeerGroup, settings: PeerSettings) {
  return `${peerGroupName(group.key)} · ${familyName(group.population)} reference · at least ${settings.peerMin} included 5v5 minutes · n = ${group.members.length}; partial n = ${group.partialCount}`;
}

function referenceLimit(group: PeerGroup) {
  return group.members.length === 0
    ? "no players meet this peer rule"
    : group.members.length === 1
      ? "one eligible player; no between-player comparison"
      : null;
}

function outsideText(
  card: ObservedCard,
  population: ObservedRateRow["population"],
  settings: PeerSettings,
) {
  if (
    !card.rows.some(
      (row) => row.population === population && row.standing.kind === "outside",
    )
  )
    return null;
  const support = populationSupport(card.player, population);
  return support.included_seconds < settings.peerMin * 60
    ? `outside reference: under ${settings.peerMin} ${familyName(population)} minutes`
    : `outside reference: no eligible ${familyName(population)} exposure`;
}

export function ObservedRateValue({
  row,
  group,
  player,
}: {
  readonly row: ObservedRateRow;
  readonly group: PeerGroup;
  readonly player: PlayerSummary;
}) {
  const definition = metricDefinition(row.metric);
  const support = populationSupport(player, row.population);
  const standing = row.standing;
  return (
    <div
      className="observed-rate-value"
      data-metric={row.metric}
      data-standing={standing.kind}
    >
      <p className="rate-primary">
        <strong>
          <Quantity
            value={row.rate}
            metrics={support}
            rate
            precision={definition.precision}
          />
        </strong>{" "}
        <span>per 60 {familyName(row.population)} min</span>
      </p>
      <p className="rate-count">
        <Quantity value={row.count} metrics={support} /> recorded
        {support.coverage_status !== "complete"
          ? ` · ${support.coverage_status} coverage`
          : ""}
      </p>
      {standing.kind === "ranked" ? (
        <>
          <p className="standing-label">
            <strong>{formatPercentile(standing.percentile)}</strong>{" "}
            observed-rate percentile
          </p>
          <div
            className="percentile-strip"
            role="img"
            aria-label={`observed-rate percentile ${formatPercentile(standing.percentile)} on a 0 to 100 scale`}
          >
            <span className="percentile-track" />
            <span
              className="percentile-marker"
              style={{ left: `${standing.percentile}%` }}
              data-percentile={standing.percentile}
            />
            <span className="percentile-ticks">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </span>
          </div>
        </>
      ) : (
        <p className="standing-unavailable">
          {standing.kind === "unavailable"
            ? "rate unavailable"
            : group.members.length === 0
              ? "no reference players"
              : "outside reference"}
        </p>
      )}
      {row.metric === "against60" && (
        <p className="rate-direction">higher = more opponent attempts</p>
      )}
    </div>
  );
}

export function ObservedSupport({
  card,
  comparison,
}: {
  readonly card: ObservedCard;
  readonly comparison: ObservedComparison;
}) {
  const { player } = card;
  return (
    <div className="observed-support">
      <div className="population-coverage">
        {(["personal", "onIce"] as const).map((population) => {
          const support = populationSupport(player, population);
          const row = card.rows.find(
            (entry) => entry.population === population,
          )!;
          const group = comparison.groups[population].find(
            (entry) => entry.key === row.groupKey,
          )!;
          const limit = referenceLimit(group);
          const outside = outsideText(card, population, comparison.settings);
          return (
            <div key={population} data-population={population}>
              <h4>{familyName(population)} support and reference</h4>
              <p>
                <Minutes seconds={support.included_seconds} /> included minutes
              </p>
              <CoverageDetail metrics={support} />
              <p className="reference-summary">
                {referenceText(group, comparison.settings)}
              </p>
              {limit && <p className="outside-reference">{limit}</p>}
              {outside && <p className="outside-reference">{outside}</p>}
              {card.rows.some(
                (entry) =>
                  entry.population === population &&
                  entry.standing.kind === "unavailable",
              ) && (
                <p className="outside-reference">
                  rate unavailable; retained counts and coverage reasons remain
                  evidence.
                </p>
              )}
            </div>
          );
        })}
      </div>
      <p className="control-note">
        {player.games_with_included_time} games with on-ice included time;{" "}
        {player.listed_games} listed games, {player.partial_games} on-ice
        partial, {player.unavailable_games} on-ice unavailable. roster listing
        is not an appearance claim; included minutes are not full official ice
        time.
      </p>
    </div>
  );
}
