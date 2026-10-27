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
import { HockeyId } from "../../shared/observed";
import type { Person } from "../../shared/player-analysis";
import { loadComparison } from "../client";
import PlayerPicker from "../player-picker";
import {
  readMapMode,
  readView,
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
import ComparativeCard, { prepareComparativeCard } from "../comparative-card";
import DescriptiveCard, { descriptiveScales } from "../descriptive-card";
import { buildDescriptiveCard } from "../descriptive-values";
import PeerDistributions, { PeerControls } from "../peer-distributions";
import {
  selectLeagueValues,
  type AnalysisMetric,
} from "../analysis-values";
import { buildAnalysisCohort } from "../analysis-cohorts";
import AnalysisHistory, { prepareHistoryPoint, type HistoryScale } from "../analysis-history";
import { ObservedRateValue, ObservedSupport } from "../observed-rates";
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
  shouldRevalidateView(args, [
    "peers",
    "peerMin",
    "specialtyMin",
    "history",
    ...(readView(args.nextUrl.searchParams).view === "comparative"
      ? ["map"]
      : []),
  ]);

function selection(
  values: string[],
  slot: "first" | "second",
  players: readonly Person[],
  season: string,
): {
  readonly player?: Person;
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
  const { view, search: viewNormalized } = readView(search);
  const { settings, search: peerNormalized } = readPeerSettings(viewNormalized);
  const { mode, search: mapNormalized } = readMapMode(peerNormalized);
  const { metric, search: metricNormalized } = readMetric(
    mapNormalized,
    "skater",
  );
  const { scale, search: normalized } = readHistoryScale(metricNormalized, metric);
  useCanonicalSearch(data.season.season, normalized);
  const viewQuery = seasonSearch("", data.season.season);
  if (view === "observed") viewQuery.set("view", "observed");
  viewQuery.set("metric", metric.id);
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
    next.set("metric", nextMetric.id);
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
  const changeScale = (nextScale: HistoryScale) => {
    const next = viewSearch(location, navigation.location);
    if (nextScale === "raw") next.delete("history");
    else next.set("history", nextScale);
    setSearch(next, { preventScrollReset: true, state: location.state, flushSync: true });
  };
  const first = selection(
    search.getAll("a"),
    "first",
    data.persons,
    data.season.season,
  );
  const second = selection(
    search.getAll("b"),
    "second",
    data.persons,
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
  const commit = (slot: "first" | "second", player?: Person) => {
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
  const comparison = useMemo(() => {
    const firstObserved = data.players.find(
      (player) => player.player_id === pair?.[0].player_id,
    );
    const secondObserved = data.players.find(
      (player) => player.player_id === pair?.[1].player_id,
    );
    return firstObserved && secondObserved
      ? buildObservedComparison(
          data.players,
          [firstObserved, secondObserved],
          settings,
        )
      : undefined;
  }, [data.players, pair, settings.peers, settings.peerMin]);
  const cards = useMemo(
    () =>
      view === "comparative" && data.profiles
        ? data.profiles.map((profile) =>
            prepareComparativeCard(profile, settings),
          )
        : null,
    [
      data.profiles,
      view,
      settings.peers,
      settings.peerMin,
      settings.specialtyMin,
    ],
  );
  const descriptiveCards = useMemo(
    () => view === "observed" && data.profiles
      ? data.profiles.map(profile => buildDescriptiveCard(profile, profile.player_id, settings))
      : null,
    [data.profiles, view, settings.peers, settings.peerMin, settings.specialtyMin],
  );
  const descriptiveSharedScales = descriptiveCards ? descriptiveScales(descriptiveCards) : undefined;
  const scalarHistories = useMemo(
    () => data.profiles?.map(profile => ({
      playerId: profile.player_id,
      person: profile.person,
      views: profile.scalarHistory.map(row =>
        prepareHistoryPoint(row, profile.detail, metric, profile.player_id, settings),
      ),
    })) ?? [],
    [data.profiles, metric, settings.peers, settings.peerMin, settings.specialtyMin],
  );
  const scalarComparison = useMemo(() => {
    if (!pair) return null;
    const values = data.scalarCohort ? selectLeagueValues(data.scalarCohort, metric) : [];
    const selected = scalarHistories.map(history => history.views.find(
      ({ point }) => point.season.season === data.season.season,
    )!.point.datum);
    return buildAnalysisCohort(values, selected, settings);
  }, [
    data.scalarCohort,
    data.profiles,
    scalarHistories,
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
        {view === "observed" && (
          <p>
            the recorded 5v5 comparison below uses each player's own included
            evidence and matched 5v5 time; these are unadjusted observations,
            not ability. personal production and team attempts while on ice use
            separate matched populations.
          </p>
        )}
        {view === "observed" && (
          <p>
            attempts “for” are by the player's team while on ice, not personal
            shots. attempts include scored, saved, missed and blocked shots.
          </p>
        )}
        <p>both player searches use this season's published records.</p>
      </section>
      <nav className="comparative-view-nav" aria-label="comparison view">
        {(["comparative", "observed"] as const).map((choice) => {
          const next = seasonSearch(search, data.season.season);
          if (choice === "observed") next.set("view", "observed");
          else next.delete("view");
          return (
            <Link
              key={choice}
              to={`${location.pathname}?${next}`}
              state={location.state}
              aria-current={choice === view ? "page" : undefined}
            >
              {choice === "comparative"
                ? "comparative cards"
                : "observed results"}
            </Link>
          );
        })}
      </nav>
      {data.persons.length === 0 && (
        <p className="empty-search">no players are available in this season</p>
      )}
      <div className="comparison-pickers">
        <PlayerPicker
          slot="first"
          players={data.persons}
          selected={first.player}
          error={first.error}
          otherId={secondError ? undefined : second.player?.player_id}
          committedPair={committedPair}
          onChoose={(player) => commit("first", player)}
          onClear={() => commit("first")}
        />
        <PlayerPicker
          slot="second"
          players={data.persons}
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
      {view === "observed" && <GlobalGap season={data.season} />}
      {cards && (
        <section
          className="comparative-controls"
          aria-label="comparative card peer settings"
        >
          <PeerControls settings={settings} onChange={changePeers} allCutoffs />
        </section>
      )}
      {cards && (
        <div className="comparative-pair">
          {cards.map((card) => (
            <ComparativeCard
              key={card.playerId}
              model={card}
              detailLink={(id) => {
                const next = seasonSearch(search, data.season.season);
                next.set("metric", id);
                return {
                  to: `${location.pathname}?${next}`,
                  state: location.state,
                };
              }}
            />
          ))}
        </div>
      )}
      {descriptiveCards && (
        <section aria-label="complete recorded card comparison">
          <PeerControls settings={settings} onChange={changePeers} allCutoffs />
          <div className="descriptive-pair">
            {descriptiveCards.map(model => (
              <DescriptiveCard
                key={model.playerId}
                model={model}
                scales={descriptiveSharedScales}
                detailLink={id => {
                  const next = seasonSearch(search, data.season.season);
                  next.set("metric", id);
                  next.delete("history");
                  return { to: `${location.pathname}?${next}`, state: location.state };
                }}
              />
            ))}
          </div>
        </section>
      )}
      {view === "observed" && comparison && (
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
          showPeerControls={view === "observed" && metric.standingPolicy !== "raw_only"}
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
      {scalarHistories.map(history => (
        <section key={history.playerId} aria-label={`selected quantity history for ${history.person ? playerName(history.person) : `player ${history.playerId}`}`}>
          <h3>{history.person ? playerName(history.person) : `player ${history.playerId}`} · selected quantity history</h3>
          <AnalysisHistory
            view={{ publication: data.publication, metric, selectedSeason: data.season.season,
              scale, points: history.views.map(({ point }) => point) }}
            onScaleChange={changeScale}
            seasonLink={year => ({
              to: `${location.pathname}?${seasonSearch(search, year)}`, state: location.state,
            })}
          />
        </section>
      ))}
      {view === "observed" && pair && (
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
