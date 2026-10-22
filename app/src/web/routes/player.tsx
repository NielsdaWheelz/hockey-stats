import { useMemo } from "react";
import {
  Link,
  useLoaderData,
  useLocation,
  useNavigation,
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
  seasonSearch,
  shouldRevalidateView,
  useCanonicalSearch,
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
  seasonLabel,
} from "../presentation";

export const clientLoader = ({ params, request }: ClientLoaderFunctionArgs) =>
  loadPlayer(params.playerId!, request.signal, new URL(request.url).searchParams);
export const ErrorBoundary = LoadError;
export const shouldRevalidate = (args: ShouldRevalidateFunctionArgs) =>
  shouldRevalidateView(args, ["peers", "peerMin", "map", "metric"]);

export default function Player() {
  const data = useLoaderData<typeof clientLoader>();
  const { publication, season, players, games, spatial, history } = data;
  const player = players.find((row) => row.player_id === data.player_id);
  const historicalIdentity = history.find((row) => row.player !== null);
  const location = useLocation();
  const navigation = useNavigation();
  const [search, setSearch] = useSearchParams();
  const { settings, search: peerNormalized } = readPeerSettings(search);
  const { mode, search: mapNormalized } = readMapMode(peerNormalized);
  const { metric, search: normalized } = readRateMetric(mapNormalized);
  useCanonicalSearch(season.season, normalized);
  const leagueSearch =
    historySearch(location.state?.leagueSearch) ||
    `?${seasonSearch("", season.season)}`;
  const comparisonSearch = historySearch(location.state?.comparisonSearch);
  const viewQuery = seasonSearch("", season.season);
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
  const comparison = useMemo(
    () =>
      player ? buildObservedComparison(players, [player], settings) : undefined,
    [players, player, settings.peers, settings.peerMin],
  );
  const comparisonQuery = new URLSearchParams(viewQuery);
  comparisonQuery.set("a", data.player_id);
  return (
    <>
      <nav className="back-link">
        <Link to={`/${leagueSearch}`}>back to players</Link>
        {comparisonSearch && (
          <Link to={`/compare${comparisonSearch}`} state={{ leagueSearch }}>
            back to comparison
          </Link>
        )}
        <Link to={`/compare?${comparisonQuery}`} state={{ leagueSearch }}>
          compare this player
        </Link>
      </nav>
      <section className="player-heading">
        <h2>{player ? playerName(player) : `player ${data.player_id}`}</h2>
        {player ? (
          <p>
            {player.teams.map(teamName).join(" / ")} · reported position{" "}
            {player.reported_position} · player {player.player_id}
          </p>
        ) : (
          <>
            <p>no published player record for {seasonLabel(season.season)}.</p>
            {historicalIdentity?.player && (
              <p>
                {playerName(historicalIdentity.player)} · name from{" "}
                {seasonLabel(historicalIdentity.season.season)}.
              </p>
            )}
            <p>
              absence is not zero production or evidence that the player did not
              play. choose a history season below.
            </p>
          </>
        )}
      </section>
      {comparison && (
        <DescriptiveCard
          comparison={comparison}
          publication={publication}
          season={season}
          controls={<PeerControls settings={settings} onChange={changePeers} />}
        />
      )}
      <section className="player-history" aria-labelledby="history-heading">
        <h3 id="history-heading">recorded results across published seasons</h3>
        <p className="control-note">
          each season retains its own identity, matched time and coverage. raw
          rates are unadjusted for league environment, missingness or deployment.
        </p>
        <div
          className="table-scroll history-scroll"
          tabIndex={0}
          role="region"
          aria-label="player history table, scroll horizontally for all columns"
        >
          <table
            className="history-table"
            aria-label="recorded results across published seasons"
          >
            <caption>
              personal and on-ice rates use separate included 5v5 minutes.
              follow a season for its complete evidence and known exclusions.
            </caption>
            <colgroup span={2} />
            <colgroup span={5} />
            <colgroup span={4} />
            <thead>
              <tr>
                <th scope="col" rowSpan={2} className="identity">
                  season
                </th>
                <th scope="col" rowSpan={2}>
                  season identity / teams / reported position
                </th>
                <th scope="colgroup" colSpan={5}>
                  personal production
                </th>
                <th scope="colgroup" colSpan={4}>
                  team attempts while on ice
                </th>
              </tr>
              <tr>
                <th scope="col" className="numeric">shots on goal/60</th>
                <th scope="col" className="numeric">goals/60</th>
                <th scope="col" className="numeric">primary assists/60</th>
                <th scope="col" className="numeric">included min</th>
                <th scope="col">coverage</th>
                <th scope="col" className="numeric">for/60</th>
                <th scope="col" className="numeric">against/60</th>
                <th scope="col" className="numeric">included min</th>
                <th scope="col">coverage</th>
              </tr>
            </thead>
            <tbody>
              {history.map(({ season: evidence, player: row }) => (
                <tr key={evidence.season}>
                  <th scope="row" className="identity">
                    <Link
                      to={`${location.pathname}?${seasonSearch(search, evidence.season)}`}
                      state={location.state}
                      aria-current={
                        evidence.season === season.season ? "page" : undefined
                      }
                    >
                      {seasonLabel(evidence.season)}
                    </Link>
                    {evidence.season === season.season && (
                      <span className="history-context">selected season</span>
                    )}
                    {evidence.coverage.games_with_unassigned_player_associations > 0 && (
                      <span className="history-context">
                        global gap: {evidence.coverage.games_with_unassigned_player_associations}{" "}
                        unassigned inventory games; player totals may omit games.
                      </span>
                    )}
                  </th>
                  {row ? (
                    <>
                      <td className="history-identity">
                        <span className="history-name">{playerName(row)}</span>
                        {row.teams.map(teamName).join(" / ")} · {row.reported_position}
                      </td>
                      <td className="numeric">
                        <Quantity value={row.personal.shots_on_goal_per60} metrics={row.personal} rate precision={2} />
                      </td>
                      <td className="numeric">
                        <Quantity value={row.personal.goals_per60} metrics={row.personal} rate precision={2} />
                      </td>
                      <td className="numeric">
                        <Quantity value={row.personal.primary_assists_per60} metrics={row.personal} rate precision={2} />
                      </td>
                      <td className="numeric">
                        <Minutes seconds={row.personal.included_seconds} />
                      </td>
                      <td><CoverageDetail metrics={row.personal} /></td>
                      <td className="numeric">
                        <Quantity value={row.metrics.for_per60} metrics={row.metrics} rate />
                      </td>
                      <td className="numeric">
                        <Quantity value={row.metrics.against_per60} metrics={row.metrics} rate />
                      </td>
                      <td className="numeric">
                        <Minutes seconds={row.metrics.included_seconds} />
                      </td>
                      <td><CoverageDetail metrics={row.metrics} /></td>
                    </>
                  ) : (
                    <td colSpan={10}>
                      no published player record for {seasonLabel(evidence.season)}.
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <GlobalGap season={season} />
      {player && comparison && (
        <>
          <PeerDistributions
            comparison={comparison}
            metric={metric}
            onMetricChange={changeMetric}
            profileLink={(playerId) => ({
              to: `/players/${playerId}?${viewQuery}`,
              state: { leagueSearch, comparisonSearch },
            })}
          />
          <SpatialViews
            spatial={spatial}
            players={[player]}
            season={season.season}
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
        </>
      )}
      <Evidence publication={publication} season={season} />
    </>
  );
}
