import {
  Link,
  useLoaderData,
  useLocation,
  type ClientLoaderFunctionArgs,
} from "react-router";
import { loadPlayer } from "../client";
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

export const clientLoader = ({ params, request }: ClientLoaderFunctionArgs) =>
  loadPlayer(params.playerId!, request.signal);
export const ErrorBoundary = LoadError;

export default function Player() {
  const { publication, coverage, player, games } =
    useLoaderData<typeof clientLoader>();
  const location = useLocation();
  const leagueSearch = historySearch(location.state?.leagueSearch);
  const comparisonSearch = historySearch(location.state?.comparisonSearch);
  const metrics = player.metrics;
  return (
    <>
      <nav className="back-link">
        <Link to={`/${leagueSearch}`}>back to players</Link>
        {comparisonSearch && (
          <Link to={`/compare${comparisonSearch}`} state={{ leagueSearch }}>
            back to comparison
          </Link>
        )}
        <Link to={`/compare?a=${player.player_id}`} state={{ leagueSearch }}>
          compare this player
        </Link>
      </nav>
      <section className="player-heading">
        <h2>{playerName(player)}</h2>
        <p>
          {player.teams.map(teamName).join(" / ")} · reported position{" "}
          {player.reported_position} · player {player.player_id}
        </p>
      </section>
      <section aria-labelledby="included-heading">
        <h3 id="included-heading">included results</h3>
        <dl className="metric-sheet">
          <div>
            <dt>matched minutes</dt>
            <dd>
              <Minutes seconds={metrics.included_seconds} />
            </dd>
          </div>
          <div>
            <dt>attempts for</dt>
            <dd>
              <Quantity value={metrics.attempts_for} metrics={metrics} />
            </dd>
          </div>
          <div>
            <dt>attempts against</dt>
            <dd>
              <Quantity value={metrics.attempts_against} metrics={metrics} />
            </dd>
          </div>
          <div>
            <dt>attempts for/60</dt>
            <dd>
              <Quantity value={metrics.for_per60} metrics={metrics} rate />
            </dd>
          </div>
          <div>
            <dt>attempts against/60</dt>
            <dd>
              <Quantity value={metrics.against_per60} metrics={metrics} rate />
            </dd>
          </div>
        </dl>
        <GlobalGap coverage={coverage} />
      </section>
      <section className="profile-coverage" aria-labelledby="coverage-heading">
        <h3 id="coverage-heading">coverage</h3>
        <p>
          {player.games_with_included_time} games with included time;{" "}
          {player.listed_games} listed games, {player.partial_games} partial and{" "}
          {player.unavailable_games} unavailable.
        </p>
        <CoverageDetail metrics={metrics} />
        <p>
          roster listing is not an appearance claim. included minutes are not
          full official ice time.
        </p>
      </section>
      <section aria-labelledby="games-heading">
        <h3 id="games-heading">listed-game evidence</h3>
        <div
          className="table-scroll"
          tabIndex={0}
          aria-label="listed-game evidence table, scroll horizontally for all columns"
        >
          <table className="game-table">
            <caption>
              date order · matched minutes and recorded attempts in the included
              population
            </caption>
            <thead>
              <tr>
                <th scope="col" className="identity">
                  date / game
                </th>
                <th scope="col">player's team</th>
                <th scope="col">opponent</th>
                <th scope="col" className="numeric">
                  matched min
                </th>
                <th scope="col" className="numeric">
                  for
                </th>
                <th scope="col" className="numeric">
                  against
                </th>
                <th scope="col">coverage / reasons</th>
              </tr>
            </thead>
            <tbody>
              {games.map((game) => (
                <tr key={game.game_id}>
                  <th scope="row" className="identity">
                    <time dateTime={game.game_date}>{game.game_date}</time>
                    <span className="game-id">{game.game_id}</span>
                  </th>
                  <td>{teamName(game.team)}</td>
                  <td>
                    {game.venue === "home" ? "vs" : "at"}{" "}
                    {teamName(game.opponent)}
                  </td>
                  <td className="numeric">
                    <Minutes seconds={game.metrics.included_seconds} />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={game.metrics.attempts_for}
                      metrics={game.metrics}
                    />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={game.metrics.attempts_against}
                      metrics={game.metrics}
                    />
                  </td>
                  <td>
                    <CoverageDetail metrics={game.metrics} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <Evidence publication={publication} coverage={coverage} />
    </>
  );
}
