import * as Schema from "effect/Schema";
import {
  Link,
  useLoaderData,
  useLocation,
  useSearchParams,
  type ClientLoaderFunctionArgs,
  type ShouldRevalidateFunctionArgs,
} from "react-router";
import { HockeyId, type PlayerSummary } from "../../shared/observed";
import { loadLeague } from "../client";
import PlayerPicker from "../player-picker";
import {
  CoverageDetail,
  Evidence,
  GlobalGap,
  LoadError,
  Minutes,
  Quantity,
  historySearch,
  playerName,
  teamName,
} from "../presentation";

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) =>
  loadLeague(request.signal);
export const ErrorBoundary = LoadError;

export function shouldRevalidate({
  currentUrl,
  nextUrl,
  defaultShouldRevalidate,
}: ShouldRevalidateFunctionArgs) {
  if (
    currentUrl.pathname === nextUrl.pathname &&
    currentUrl.search !== nextUrl.search
  ) {
    const current = new URLSearchParams(currentUrl.search);
    const next = new URLSearchParams(nextUrl.search);
    for (const key of ["a", "b"]) {
      current.delete(key);
      next.delete(key);
    }
    if (current.toString() === next.toString()) return false;
  }
  return defaultShouldRevalidate;
}

function selection(
  values: string[],
  slot: "first" | "second",
  players: readonly PlayerSummary[],
): { readonly player?: PlayerSummary; readonly error?: string } {
  if (values.length === 0 || (values.length === 1 && values[0] === "")) return {};
  if (values.length !== 1 || !Schema.is(HockeyId)(values[0]))
    return { error: `invalid ${slot} player selection; choose a player below` };
  const player = players.find((row) => row.player_id === values[0]);
  return player
    ? { player }
    : { error: `player ${values[0]} is not in this publication` };
}

export default function Compare() {
  const data = useLoaderData<typeof clientLoader>();
  const location = useLocation();
  const [search, setSearch] = useSearchParams();
  const leagueSearch = historySearch(location.state?.leagueSearch);
  const first = selection(search.getAll("a"), "first", data.players);
  const second = selection(search.getAll("b"), "second", data.players);
  const secondError =
    first.player && first.player.player_id === second.player?.player_id
      ? "choose a different player"
      : second.error;
  const committedPair = JSON.stringify([search.getAll("a"), search.getAll("b")]);
  const commit = (slot: "first" | "second", player?: PlayerSummary) => {
    const next = new URLSearchParams(search);
    const key = slot === "first" ? "a" : "b";
    if (player) next.set(key, player.player_id);
    else next.delete(key);
    if (next.toString() !== search.toString())
      setSearch(next, { preventScrollReset: true, state: { leagueSearch } });
  };
  const pair =
    first.player && second.player && !secondError
      ? [first.player, second.player]
      : undefined;
  return (
    <>
      <nav className="back-link">
        <Link to={`/${leagueSearch}`}>back to players</Link>
      </nav>
      <section className="comparison-heading">
        <h2>compare included results</h2>
        <p>
          each player's own included evidence and matched 5v5 time; these are
          unadjusted on-ice observations, not estimates of individual contribution.
        </p>
        <p>
          attempts “for” are by the player's team while on ice, not personal shots.
          attempts include scored, saved, missed and blocked shots.
        </p>
      </section>
      {data.players.length === 0 && (
        <p className="empty-search">no players are available in this publication</p>
      )}
      <div className="comparison-pickers">
        <PlayerPicker
          slot="first"
          players={data.players}
          selected={first.player}
          error={first.error}
          otherId={secondError ? undefined : second.player?.player_id}
          committedPair={committedPair}
          onChoose={(player) => commit("first", player)}
          onClear={() => commit("first")}
        />
        <PlayerPicker
          slot="second"
          players={data.players}
          selected={second.player}
          error={secondError}
          otherId={first.player?.player_id}
          committedPair={committedPair}
          onChoose={(player) => commit("second", player)}
          onClear={() => commit("second")}
        />
      </div>
      <p role="status" className="visually-hidden">
        first player:{" "}
        {first.error ??
          (first.player
            ? `${playerName(first.player)}, player ${first.player.player_id}`
            : "unselected")}
        . second player:{" "}
        {secondError ??
          (second.player
            ? `${playerName(second.player)}, player ${second.player.player_id}`
            : "unselected")}
        .
      </p>
      <GlobalGap coverage={data.coverage} />
      {pair && (
        <section aria-label="included player comparison">
          <div
            className="table-scroll comparison-scroll"
            tabIndex={0}
            aria-label="player comparison table, scroll horizontally for both players"
          >
            <table className="comparison-table">
              <caption>
                each player's counts and time come from their own included
                evidence; included games can differ.
              </caption>
              <thead>
                <tr>
                  <th scope="col" className="identity">
                    metric
                  </th>
                  {pair.map((player, index) => (
                    <th scope="col" key={player.player_id}>
                      <span>{index === 0 ? "first player" : "second player"}</span>
                      <Link
                        to={`/players/${player.player_id}`}
                        state={{
                          comparisonSearch: location.search,
                          leagueSearch,
                        }}
                      >
                        {playerName(player)}
                      </Link>
                      <span>
                        {player.teams.map(teamName).join(" / ")} · reported
                        position {player.reported_position}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row" className="identity">
                    matched 5v5 minutes
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      <Minutes seconds={player.metrics.included_seconds} />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    games with included time
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      {player.games_with_included_time}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    on-ice attempts for/60
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      <Quantity
                        value={player.metrics.for_per60}
                        metrics={player.metrics}
                        rate
                      />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    on-ice attempts against/60
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      <Quantity
                        value={player.metrics.against_per60}
                        metrics={player.metrics}
                        rate
                      />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    on-ice attempts for
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      <Quantity
                        value={player.metrics.attempts_for}
                        metrics={player.metrics}
                      />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    on-ice attempts against
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      <Quantity
                        value={player.metrics.attempts_against}
                        metrics={player.metrics}
                      />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    coverage and reasons
                  </th>
                  {pair.map((player) => (
                    <td key={player.player_id}>
                      <CoverageDetail metrics={player.metrics} />
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    listed games
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      {player.listed_games}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    partial games with included time
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      {player.partial_games}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row" className="identity">
                    unavailable listed games
                  </th>
                  {pair.map((player) => (
                    <td className="numeric" key={player.player_id}>
                      {player.unavailable_games}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
          <p className="comparison-note">
            partial games are a subset of games with included time; roster listing
            is not an appearance claim; known excluded time is not a complete
            missing-time denominator.
          </p>
        </section>
      )}
      <Evidence publication={data.publication} coverage={data.coverage} />
    </>
  );
}
