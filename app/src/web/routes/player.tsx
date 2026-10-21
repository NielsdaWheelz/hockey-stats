import { useEffect, useMemo } from "react";
import {
  Link,
  useLoaderData,
  useLocation,
  useNavigation,
  useParams,
  useSearchParams,
  type ClientLoaderFunctionArgs,
  type ShouldRevalidateFunctionArgs,
} from "react-router";
import { loadPlayer } from "../client";
import {
  readMapMode,
  readPeerSettings,
  readRateMetric,
  viewSearch,
  type PeerSettings,
} from "../explorer";
import SpatialViews from "../spatial-views";
import PeerDistributions, { PeerControls } from "../peer-distributions";
import DescriptiveCard from "../descriptive-card";
import {
  buildObservedComparison,
  type ObservedRateKey,
} from "../observed-comparison";
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

export const clientLoader = async ({
  params,
  request,
}: ClientLoaderFunctionArgs) => {
  const data = await loadPlayer(params.playerId!, request.signal);
  if (!data.players.some((player) => player.player_id === params.playerId))
    throw new Response("selected player is absent from the response", {
      status: 500,
    });
  return data;
};
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
    for (const key of ["peers", "peerMin", "map", "metric"]) {
      current.delete(key);
      next.delete(key);
    }
    if (current.toString() === next.toString()) return false;
  }
  return defaultShouldRevalidate;
}

export default function Player() {
  const { publication, coverage, players, games, spatial } =
    useLoaderData<typeof clientLoader>();
  const params = useParams();
  const player = players.find((row) => row.player_id === params.playerId)!;
  const location = useLocation();
  const navigation = useNavigation();
  const [search, setSearch] = useSearchParams();
  const { settings, search: peerNormalized } = readPeerSettings(search);
  const { mode, search: mapNormalized } = readMapMode(peerNormalized);
  const { metric, search: normalized } = readRateMetric(mapNormalized);
  useEffect(() => {
    if (
      navigation.state === "idle" &&
      normalized.toString() !== search.toString()
    )
      setSearch(normalized, {
        replace: true,
        preventScrollReset: true,
        state: location.state,
      });
  }, [
    normalized.toString(),
    search,
    setSearch,
    location.state,
    navigation.state,
  ]);
  const leagueSearch = historySearch(location.state?.leagueSearch);
  const comparisonSearch = historySearch(location.state?.comparisonSearch);
  const viewQuery = new URLSearchParams();
  if (metric !== "sog60") viewQuery.set("metric", metric);
  if (mode === "absolute") viewQuery.set("map", "absolute");
  if (settings.peers !== "position") viewQuery.set("peers", settings.peers);
  if (settings.peerMin !== 300)
    viewQuery.set("peerMin", String(settings.peerMin));
  const changePeers = (nextSettings: Partial<PeerSettings>) => {
    const next = viewSearch(location, navigation.location);
    const previous = next.toString();
    if (nextSettings.peers !== undefined) {
      if (nextSettings.peers === "position") next.delete("peers");
      else next.set("peers", nextSettings.peers);
    }
    if (nextSettings.peerMin !== undefined) {
      if (nextSettings.peerMin === 300) next.delete("peerMin");
      else next.set("peerMin", String(nextSettings.peerMin));
    }
    if (next.toString() !== previous)
      setSearch(next, {
        preventScrollReset: true,
        state: location.state,
        flushSync: true,
      });
  };
  const changeMetric = (nextMetric: ObservedRateKey) => {
    const next = viewSearch(location, navigation.location);
    if (nextMetric === readRateMetric(next).metric) return;
    if (nextMetric === "sog60") next.delete("metric");
    else next.set("metric", nextMetric);
    setSearch(next, {
      preventScrollReset: true,
      state: location.state,
      flushSync: true,
    });
  };
  const changeMode = (nextMode: "difference" | "absolute") => {
    const next = viewSearch(location, navigation.location);
    if (nextMode === readMapMode(next).mode) return;
    if (nextMode === "absolute") next.set("map", "absolute");
    else next.delete("map");
    setSearch(next, {
      preventScrollReset: true,
      state: location.state,
      flushSync: true,
    });
  };
  const returnComparison = new URLSearchParams(comparisonSearch);
  if (mode === "absolute") returnComparison.set("map", "absolute");
  else returnComparison.delete("map");
  const comparison = useMemo(
    () => buildObservedComparison(players, [player], settings),
    [players, player, settings.peers, settings.peerMin],
  );
  const comparisonQuery = new URLSearchParams(viewQuery);
  comparisonQuery.set("a", player.player_id);
  return (
    <>
      <nav className="back-link">
        <Link to={`/${leagueSearch}`}>back to players</Link>
        {comparisonSearch && (
          <Link to={`/compare?${returnComparison}`} state={{ leagueSearch }}>
            back to comparison
          </Link>
        )}
        <Link to={`/compare?${comparisonQuery}`} state={{ leagueSearch }}>
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
      <DescriptiveCard
        comparison={comparison}
        publication={publication}
        coverage={coverage}
        controls={<PeerControls settings={settings} onChange={changePeers} />}
      />
      <GlobalGap coverage={coverage} />
      <PeerDistributions
        comparison={comparison}
        metric={metric}
        onMetricChange={changeMetric}
        profileLink={(playerId) => ({
          to: `/players/${playerId}${viewQuery.size ? `?${viewQuery}` : ""}`,
          state: { leagueSearch, comparisonSearch },
        })}
      />
      <SpatialViews
        spatial={spatial}
        players={[player]}
        season={publication.season}
        mode={mode}
        onModeChange={changeMode}
      />
      <section aria-labelledby="games-heading">
        <h3 id="games-heading" tabIndex={-1}>
          listed-game evidence
        </h3>
        <div
          className="table-scroll"
          tabIndex={0}
          aria-label="listed-game evidence table, scroll horizontally for all columns"
        >
          <table className="game-table">
            <caption>
              date order · personal, on-ice and spatial counts have their own
              matched minutes and coverage; spatial season counts and time
              reduce from these rows
            </caption>
            <thead>
              <tr>
                <th scope="col" className="identity">
                  date / game
                </th>
                <th scope="col">player's team</th>
                <th scope="col">opponent</th>
                <th scope="col" className="numeric">
                  on-ice min
                </th>
                <th scope="col" className="numeric">
                  on-ice for
                </th>
                <th scope="col" className="numeric">
                  on-ice against
                </th>
                <th scope="col">on-ice coverage / reasons</th>
                <th scope="col" className="numeric">
                  shots on goal
                </th>
                <th scope="col" className="numeric">
                  goals
                </th>
                <th scope="col" className="numeric">
                  primary assists
                </th>
                <th scope="col" className="numeric">
                  personal min
                </th>
                <th scope="col">personal coverage / reasons</th>
                <th scope="col" className="numeric">
                  spatial unblocked for
                </th>
                <th scope="col" className="numeric">
                  spatial unblocked against
                </th>
                <th scope="col" className="numeric">
                  spatial min
                </th>
                <th scope="col">spatial coverage / reasons</th>
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
                  <td className="numeric">
                    <Quantity
                      value={game.personal.shots_on_goal}
                      metrics={game.personal}
                    />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={game.personal.goals}
                      metrics={game.personal}
                    />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={game.personal.primary_assists}
                      metrics={game.personal}
                    />
                  </td>
                  <td className="numeric">
                    <Minutes seconds={game.personal.included_seconds} />
                  </td>
                  <td>
                    <CoverageDetail metrics={game.personal} />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={game.spatial.unblocked_for}
                      metrics={game.spatial}
                    />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={game.spatial.unblocked_against}
                      metrics={game.spatial}
                    />
                  </td>
                  <td className="numeric">
                    <Minutes seconds={game.spatial.included_seconds} />
                  </td>
                  <td>
                    <CoverageDetail metrics={game.spatial} />
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
