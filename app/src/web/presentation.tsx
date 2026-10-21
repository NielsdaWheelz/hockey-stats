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
  PersonalMetrics,
  PersonalReasonCode,
  SpatialMetrics,
  SpatialReasonCode,
  Team,
} from "../shared/observed";

export const reasons: Record<
  ReasonCode | PersonalReasonCode | SpatialReasonCode,
  string
> = {
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
  personal_credit_unresolved:
    "some personal scoring credit is unresolved; its segment is excluded from personal counts and time",
  no_personal_5v5_exposure:
    "no personal 5v5 exposure; rates are undefined even when a credited assist remains",
  spatial_coordinates_missing:
    "recorded coordinates are missing; the assigned segment is excluded from spatial counts and time",
  spatial_frame_unresolved:
    "the shooting team's attacking frame is unresolved; its segment is excluded from spatial counts and time",
  spatial_location_outside_rink:
    "a recorded location lies outside the rink; its segment is excluded from spatial counts and time",
  no_spatial_5v5_exposure:
    "no spatial 5v5 exposure; rates and maps are undefined",
  no_5v5_exposure: "no 5v5 exposure in the supported listed evidence",
};

export const playerName = (player: PlayerSummary) =>
  player.display_name ?? `player ${player.player_id}`;
export const teamName = (team: Team) => team.abbreviation ?? `team ${team.id}`;

const normalizedName = (value: string) =>
  value.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");

export function matchingPlayers(
  players: readonly PlayerSummary[],
  query: string,
) {
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

export const formatMinutes = (seconds: number) =>
  seconds > 0 && seconds < 6 ? "<0.1" : (seconds / 60).toFixed(1);

export const formatQuantity = (value: number | null, decimals = 0) =>
  value === null
    ? "—"
    : value === 0
      ? "0"
      : decimals
        ? value.toFixed(decimals)
        : String(value);

type CoverageFields = Pick<
  Metrics | PersonalMetrics | SpatialMetrics,
  "coverage_status" | "known_excluded_seconds" | "reason_codes"
>;

export function Minutes({ seconds }: { readonly seconds: number }) {
  return (
    <span>
      {formatMinutes(seconds)}
      <span className="visually-hidden"> minutes ({seconds} seconds)</span>
    </span>
  );
}

export function Quantity({
  value,
  metrics,
  rate = false,
  precision = 1,
}: {
  readonly value: number | null;
  readonly metrics: CoverageFields;
  readonly rate?: boolean;
  readonly precision?: 1 | 2;
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
  return <>{formatQuantity(value, rate ? precision : 0)}</>;
}

export function CoverageDetail({
  metrics,
}: {
  readonly metrics: CoverageFields;
}) {
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
        <dt>on-ice definition</dt>
        <dd>{publication.population_version}</dd>
        <dt>personal definition</dt>
        <dd>{publication.personal_population_version}</dd>
        <dt>populations</dt>
        <dd>
          team attempts while on ice and personal production have separate
          matched counts and genuine 5v5 time. personal support can be smaller.
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
      <p>publication time is not a source observation time.</p>
      <Definitions />
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

export const quantityDefinitions = [
  "shots on goal include scored and saved shots, excluding misses and blocks; goals are already included in shots on goal.",
  "primary assists are first credited assists, not all assists or measured passing. goal strength determines credit even after an assister changes off.",
  "personal support can be smaller than on-ice support. each rate uses its own population’s included time.",
  "team attempts while on ice include scored, saved, missed and blocked shots.",
  "covered means no known relevant gap in listed evidence; included results are not certified complete-season totals. known excluded time is not a complete missing-time denominator.",
] as const;

export function Definitions() {
  return (
    <details className="quantity-definitions">
      <summary>quantity definitions and limits</summary>
      {quantityDefinitions.map((definition) => (
        <p key={definition}>{definition}</p>
      ))}
      <p>
        observed-rate percentiles count reference members with lower rates plus
        half of exact ties, divided by the number of members. calculations use
        unrounded published values; equal displayed rates can have different
        standings.
      </p>
      <p>
        higher percentile means higher recorded rate throughout; against: higher
        = more opponent attempts. these are descriptive, correlated
        observations, not ability, uncertainty or reliability. personal and
        on-ice references use their own included minutes; the cutoff is a
        viewing rule.
      </p>
    </details>
  );
}
