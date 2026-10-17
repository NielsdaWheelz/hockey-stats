import {
  Link,
  isRouteErrorResponse,
  useRevalidator,
  useRouteError,
} from "react-router";
import type {
  Coverage,
  Metrics,
  PlayerSummary,
  Publication,
  ReasonCode,
  Team,
} from "../shared/observed";

const reasons: Record<ReasonCode, string> = {
  required_source_unavailable:
    "required event or report evidence is unavailable",
  count_accounting_conflict:
    "recorded attempts conflict with a supplied game total",
  event_evidence_unresolved:
    "an event could not be assigned to supported 5v5 membership and time",
  unpaired_report_attempt: "a report attempt has no native event match",
  elapsed_membership_unresolved: "some elapsed membership is unresolved",
  period_horizon_unavailable: "a period's elapsed horizon is unavailable",
  player_toi_conflict:
    "reported player ice time conflicts with reconstructed exposure",
  roster_identity_unresolved:
    "some roster identities or team associations are unresolved",
  unassigned_player_games:
    "some inventory games have unassigned player associations",
  no_5v5_exposure: "no 5v5 exposure in the supported listed evidence",
};

export const playerName = (player: PlayerSummary) =>
  player.display_name ?? `player ${player.player_id}`;
export const teamName = (team: Team) => team.abbreviation ?? `team ${team.id}`;

const normalizedName = (value: string) =>
  value.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");

export function matchingPlayers(players: readonly PlayerSummary[], query: string) {
  const tokens = normalizedName(query).trim().split(/\s+/).filter(Boolean);
  return players.filter((player) =>
    tokens.every((token) => normalizedName(playerName(player)).includes(token)),
  );
}

export const nameOrder = (a: PlayerSummary, b: PlayerSummary) =>
  playerName(a).localeCompare(playerName(b), "en") ||
  a.player_id.length - b.player_id.length ||
  a.player_id.localeCompare(b.player_id);

export const historySearch = (value: unknown) =>
  typeof value === "string" && value.startsWith("?") ? value : "";

export function Minutes({ seconds }: { readonly seconds: number }) {
  return (
    <span>
      {seconds > 0 && seconds < 6 ? "<0.1" : (seconds / 60).toFixed(1)}
      <span className="visually-hidden"> minutes ({seconds} seconds)</span>
    </span>
  );
}

export function Quantity({
  value,
  metrics,
  rate = false,
}: {
  readonly value: number | null;
  readonly metrics: Metrics;
  readonly rate?: boolean;
}) {
  if (value === null)
    return (
      <span className="missing">
        —
        <span className="visually-hidden">
          {" "}
          {metrics.reason_codes.map((code) => reasons[code]).join("; ")}
        </span>
      </span>
    );
  return <>{rate ? value.toFixed(1) : value}</>;
}

export function CoverageDetail({ metrics }: { readonly metrics: Metrics }) {
  return (
    <details className="metric-coverage">
      <summary>
        {metrics.coverage_status === "complete"
          ? "covered"
          : metrics.coverage_status}
        <span className="excluded">
          <Minutes seconds={metrics.known_excluded_seconds} /> known min
          excluded
        </span>
      </summary>
      {metrics.reason_codes.length ? (
        <ul>
          {metrics.reason_codes.map((code) => (
            <li key={code}>{reasons[code]}</li>
          ))}
        </ul>
      ) : (
        <p>no known relevant gap within listed source evidence.</p>
      )}
    </details>
  );
}

export function GlobalGap({ coverage }: { readonly coverage: Coverage }) {
  if (coverage.games_with_unassigned_player_associations === 0) return null;
  return (
    <aside className="global-gap" aria-label="unassigned player evidence">
      <p>
        player associations are unresolved in{" "}
        {coverage.games_with_unassigned_player_associations} inventory{" "}
        {coverage.games_with_unassigned_player_associations === 1
          ? "game"
          : "games"}
        . every season summary carries this gap; included results may omit games
        for any player.
      </p>
      <details>
        <summary>view every unassigned game</summary>
        <ul>
          {coverage.unassigned_games.map((game) => (
            <li key={game.game_id}>
              <time dateTime={game.date}>{game.date}</time> · {game.game_id} ·
              team {game.away_team_id} at team {game.home_team_id}:{" "}
              {game.reason_codes.map((code) => reasons[code]).join("; ")}
            </li>
          ))}
        </ul>
      </details>
    </aside>
  );
}

export function Evidence({
  publication,
  coverage,
}: {
  readonly publication: Publication;
  readonly coverage: Coverage;
}) {
  return (
    <details className="evidence">
      <summary>publication and coverage evidence</summary>
      <dl className="evidence-facts">
        <dt>published</dt>
        <dd>
          <time dateTime={publication.generated_at}>
            {publication.generated_at}
          </time>
        </dd>
        <dt>publication id</dt>
        <dd className="identifier">{publication.publication_id}</dd>
        <dt>source retrieval</dt>
        <dd>
          {publication.source_requested_min !== null &&
          publication.source_requested_max !== null ? (
            <>
              {publication.source_requested_min} to{" "}
              {publication.source_requested_max}
            </>
          ) : (
            "dated source retrieval interval unavailable"
          )}
          {publication.undated_sources > 0 && (
            <>
              ; {publication.undated_sources} undated source{" "}
              {publication.undated_sources === 1 ? "receipt" : "receipts"}
            </>
          )}
        </dd>
        <dt>inventory coverage</dt>
        <dd>
          {coverage.games_with_included_time} games with included time of{" "}
          {coverage.inventory_games} inventory games; {coverage.partial_games}{" "}
          partial, {coverage.unavailable_games} unavailable
        </dd>
        <dt>population</dt>
        <dd>
          matched recorded attempts and genuine 5v5 elapsed time. counts and
          time satisfy the same published population.
        </dd>
      </dl>
      {coverage.reason_game_counts.length > 0 && (
        <ul>
          {coverage.reason_game_counts.map(({ code, games }) => (
            <li key={code}>
              {reasons[code]}: {games} {games === 1 ? "game" : "games"}
            </li>
          ))}
        </ul>
      )}
      <p>
        covered means no known relevant gap within listed source evidence.
        included results are admitted subtotals, not certified complete-season
        totals.
      </p>
      <p>attempts include scored, saved, missed and blocked shots.</p>
      {publication.purpose === "fixture" && (
        <p className="fixture-notice">
          fixture publication · development evidence
        </p>
      )}
    </details>
  );
}

export function LoadError() {
  const error = useRouteError();
  const revalidator = useRevalidator();
  const status = isRouteErrorResponse(error) ? error.status : 500;
  return (
    <section className="load-error">
      <h2>
        {status === 404
          ? "player not found"
          : status === 400
            ? "invalid player id"
            : "results could not be loaded"}
      </h2>
      <p>
        {status === 404
          ? "this player is absent from this publication."
          : status === 400
            ? "the player id must be a canonical decimal number."
            : "please try again. if the problem persists, check the local server."}
      </p>
      <div className="actions">
        {status >= 500 && (
          <button
            type="button"
            onClick={() => revalidator.revalidate()}
            disabled={revalidator.state !== "idle"}
          >
            {revalidator.state === "idle" ? "try again" : "retrying…"}
          </button>
        )}
        <Link to="/">back to players</Link>
      </div>
    </section>
  );
}
