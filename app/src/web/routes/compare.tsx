import * as Schema from "effect/Schema";
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
import { HockeyId, type PlayerSummary } from "../../shared/observed";
import { loadComparison } from "../client";
import PlayerPicker from "../player-picker";
import {
  readMapMode,
  readPeerSettings,
  readMetric,
  readHistoryScale,
  viewSearch,
  seasonSearch,
  shouldRevalidateView,
  useCanonicalSearch,
  type PeerSettings,
} from "../explorer";
import SpatialViews from "../spatial-views";
import PeerDistributions, { PeerControls } from "../peer-distributions";
import { selectLeagueValues, type AnalysisMetric } from "../analysis-values";
import { buildAnalysisCohort } from "../analysis-cohorts";
import { ObservedRateValue, ObservedSupport } from "../descriptive-card";
import {
  buildObservedComparison,
  observedMetrics,
} from "../observed-comparison";
import {
  Evidence,
  GlobalGap,
  LoadError,
  historySearch,
  playerName,
  teamName,
  seasonLabel,
} from "../presentation";

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) =>
  loadComparison(request.signal, new URL(request.url).searchParams);
export const ErrorBoundary = LoadError;

// map mode selects the requested map view, so it reloads.
export const shouldRevalidate = (args: ShouldRevalidateFunctionArgs) =>
  shouldRevalidateView(args, ["peers", "peerMin", "specialtyMin", "history"]);

function selection(
  values: string[],
  slot: "first" | "second",
  players: readonly PlayerSummary[],
  season: string,
): {
  readonly player?: PlayerSummary;
  readonly error?: string;
  readonly absentId?: string;
} {
  if (values.length === 0 || (values.length === 1 && values[0] === ""))
    return {};
  if (values.length !== 1 || !Schema.is(HockeyId)(values[0]))
    return { error: `invalid ${slot} player selection; choose a player below` };
  const player = players.find((row) => row.player_id === values[0]);
  return player
    ? { player }
    : {
        error: `no published skater record for player ${values[0]} in ${seasonLabel(season)}`,
        absentId: values[0],
      };
}

export default function Compare() {
  const data = useLoaderData<typeof clientLoader>();
  const location = useLocation();
  const navigation = useNavigation();
  const [search, setSearch] = useSearchParams();
  const leagueSearch =
    historySearch(location.state?.leagueSearch) ||
    `?${seasonSearch("", data.season.season)}`;
  const { settings, search: peerNormalized } = readPeerSettings(search);
  const { mode, search: mapNormalized } = readMapMode(peerNormalized);
  const { metric, search: metricNormalized } = readMetric(
    mapNormalized,
    "skater",
  );
  const { scale, search: normalized } = readHistoryScale(metricNormalized);
  useCanonicalSearch(data.season.season, normalized);
  const viewQuery = seasonSearch("", data.season.season);
  if (metric.id !== "sog60") viewQuery.set("metric", metric.id);
  if (scale !== "raw") viewQuery.set("history", scale);
  if (settings.specialtyMin !== 50)
    viewQuery.set("specialtyMin", String(settings.specialtyMin));
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
    if (nextSettings.specialtyMin !== undefined) {
      if (nextSettings.specialtyMin === 50) next.delete("specialtyMin");
      else next.set("specialtyMin", String(nextSettings.specialtyMin));
    }
    if (next.toString() !== previous)
      setSearch(next, {
        preventScrollReset: true,
        state: location.state,
        flushSync: true,
      });
  };
  const changeMetric = (nextMetric: AnalysisMetric) => {
    const next = viewSearch(location, navigation.location);
    if (nextMetric.id === readMetric(next, "skater").metric.id) return;
    if (nextMetric.id === "sog60") next.delete("metric");
    else next.set("metric", nextMetric.id);
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
  const first = selection(
    search.getAll("a"),
    "first",
    data.players,
    data.season.season,
  );
  const second = selection(
    search.getAll("b"),
    "second",
    data.players,
    data.season.season,
  );
  const secondError =
    first.player && first.player.player_id === second.player?.player_id
      ? "choose a different player"
      : second.error;
  const committedPair = JSON.stringify([
    data.season.season,
    search.getAll("a"),
    search.getAll("b"),
  ]);
  // expose the pending target before another control can compose its url edit.
  const commit = (slot: "first" | "second", player?: PlayerSummary) => {
    const next = viewSearch(location, navigation.location);
    const previous = next.toString();
    const key = slot === "first" ? "a" : "b";
    if (player) next.set(key, player.player_id);
    else next.delete(key);
    if (next.toString() !== previous)
      setSearch(next, {
        preventScrollReset: true,
        state: location.state,
        flushSync: true,
      });
  };
  const pair = data.pair;
  const comparison = useMemo(
    () =>
      pair ? buildObservedComparison(data.players, pair, settings) : undefined,
    [data.players, pair, settings.peers, settings.peerMin],
  );
  const scalarComparison = useMemo(() => {
    if (!pair) return null;
    const values = selectLeagueValues(data.scalarCohort, metric);
    const selected = pair.map(
      (player) => values.find((datum) => datum.playerId === player.player_id)!,
    );
    return buildAnalysisCohort(values, selected, settings);
  }, [
    data.scalarCohort,
    pair,
    metric,
    settings.peers,
    settings.peerMin,
    settings.specialtyMin,
  ]);
  const profileLink = (playerId: string) => ({
    to: `/players/${playerId}?${viewQuery}`,
    state: {
      leagueSearch,
      comparisonSearch: `?${seasonSearch(search, data.season.season)}`,
    },
  });
  return (
    <>
      <nav className="back-link">
        <Link to={`/${leagueSearch}`}>back to players</Link>
      </nav>
      <section className="comparison-heading">
        <h2>compare published player quantities</h2>
        <p>
          the recorded 5v5 comparison below uses each player's own included
          evidence and matched 5v5 time; these are unadjusted observations, not
          ability. personal production and team attempts while on ice use
          separate matched populations.
        </p>
        <p>
          attempts “for” are by the player's team while on ice, not personal
          shots. attempts include scored, saved, missed and blocked shots.
        </p>
        <p>both player searches use this season's published records.</p>
      </section>
      {data.players.length === 0 && (
        <p className="empty-search">no players are available in this season</p>
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
      {(first.absentId || second.absentId) && (
        <nav className="back-link" aria-label="absent player histories">
          {[first.absentId, second.absentId]
            .filter((id): id is string => id !== undefined)
            .map((id, index) => (
              <Link key={`${index}-${id}`} {...profileLink(id)}>
                player {id}: profile and published history
              </Link>
            ))}
        </nav>
      )}
      <GlobalGap season={data.season} />
      {comparison && (
        <section aria-label="included player comparison">
          <h3>recorded 5v5 comparison · observed reference</h3>
          <PeerControls settings={settings} onChange={changePeers} />
          <div
            className="table-scroll comparison-scroll"
            tabIndex={0}
            aria-label="player comparison table, scroll horizontally for both players"
          >
            <table className="comparison-table">
              <caption>
                regular season · unadjusted observations. higher observed-rate
                percentile means more of the recorded rate, including against.
                each player's counts and time use their own included evidence.
              </caption>
              <thead>
                <tr>
                  <th scope="col" className="identity">
                    metric
                  </th>
                  {comparison.cards.map(({ player, slot }) => (
                    <th scope="col" key={player.player_id}>
                      <span>
                        {slot === 0 ? "first player" : "second player"}
                      </span>
                      <Link {...profileLink(player.player_id)}>
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
              {(["personal", "onIce"] as const).map((population) => (
                <tbody key={population}>
                  <tr>
                    <th scope="rowgroup" colSpan={3}>
                      {population === "personal"
                        ? "personal production"
                        : "team attempts while on ice"}
                    </th>
                  </tr>
                  {observedMetrics
                    .filter(
                      (definition) => definition.population === population,
                    )
                    .map((definition) => (
                      <tr key={definition.key}>
                        <th scope="row" className="identity">
                          {definition.label}
                        </th>
                        {comparison.cards.map((card) => {
                          const row = card.rows.find(
                            (entry) => entry.metric === definition.key,
                          )!;
                          const group = comparison.groups[row.population].find(
                            (entry) => entry.key === row.groupKey,
                          )!;
                          return (
                            <td key={card.player.player_id}>
                              <ObservedRateValue
                                row={row}
                                group={group}
                                player={card.player}
                              />
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                </tbody>
              ))}
            </table>
          </div>
          <div className="comparison-support">
            {comparison.cards.map((card) => (
              <section
                key={card.player.player_id}
                aria-label={`${playerName(card.player)} support`}
              >
                <h3>
                  {card.slot === 0 ? "first" : "second"}:{" "}
                  {playerName(card.player)}
                </h3>
                <ObservedSupport card={card} comparison={comparison} />
              </section>
            ))}
          </div>
        </section>
      )}
      {scalarComparison && (
        <PeerDistributions
          cohort={scalarComparison}
          metric={metric}
          onMetricChange={changeMetric}
          settings={settings}
          onPeerChange={changePeers}
          publication={data.publication}
          season={data.season}
          profileLink={profileLink}
          exportValues
        />
      )}
      {comparison && pair && (
        <SpatialViews
          maps={data.maps}
          players={pair}
          season={data.season.season}
          mode={mode}
          onModeChange={changeMode}
        />
      )}
      <Evidence publication={data.publication} season={data.season} />
    </>
  );
}
