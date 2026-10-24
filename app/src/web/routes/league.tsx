import { Fragment, useMemo, useState } from "react";
import {
  Link,
  useLoaderData,
  useLocation,
  useNavigation,
  useSearchParams,
  type ClientLoaderFunctionArgs,
  type ShouldRevalidateFunctionArgs,
} from "react-router";
import { loadLeague } from "../client";
import {
  parseMinutes,
  readDiscovery,
  readTableSelection,
  readPeerSettings,
  teamOptions,
  seasonSearch,
  shouldRevalidateView,
  useCanonicalSearch,
  viewSearch,
  type Sort,
  type PeerSettings,
} from "../explorer";
import {
  CoverageDetail,
  Evidence,
  GlobalGap,
  LoadError,
  playerName,
  teamName,
} from "../presentation";
import {
  composeDiscoveryRows,
  discoveryPreset,
  discoveryTables,
  filterDiscoveryRows,
  sortDiscoveryRows,
  discoveryCsvHeaders,
  discoveryCsvRows,
} from "../analysis-discovery";
import {
  DatumEvidence,
  displayNumber,
  standingText,
  valueText,
} from "../analysis-history";
import { PeerControls } from "../peer-distributions";
import { downloadCsv } from "../export";
import { analysisMetric } from "../analysis-values";

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) =>
  loadLeague(request.signal, new URL(request.url).searchParams);
export const ErrorBoundary = LoadError;

export const shouldRevalidate = (args: ShouldRevalidateFunctionArgs) => {
  const selections = [args.currentUrl, args.nextUrl].map(url => readTableSelection(url.searchParams).selection);
  const needsExactFamily =
    selections.some(selection => selection.table === "descriptive" ||
      (selection.table === "execution" || selection.table === "shootiness") &&
      selection.strength !== "5v5");
  return shouldRevalidateView(args, [
    "q", "sort", "dir", "position", "team", "min",
    "peers", "peerMin", "specialtyMin", "history",
    ...(!needsExactFamily ? ["table", "strength"] : []),
  ]);
};

export default function League() {
  const data = useLoaderData<typeof clientLoader>();
  const location = useLocation();
  const navigation = useNavigation();
  const [search, setSearch] = useSearchParams();
  const { selection, search: tableNormalized } = readTableSelection(search);
  const preset = discoveryPreset(selection.table, selection.strength);
  const { settings, search: peersNormalized } = readPeerSettings(tableNormalized);
  const { discovery, search: normalized } = readDiscovery(
    peersNormalized,
    ["name", ...preset.columns.map(column => column.id)],
    preset.defaultSort,
  );
  const { q, sort, dir, position, team, min } = discovery;
  const [minute, setMinute] = useState({
    committed: min,
    draft: String(min),
    error: "",
  });
  if (minute.committed !== min)
    setMinute({ committed: min, draft: String(min), error: "" });
  useCanonicalSearch(data.season.season, normalized);
  const rows = useMemo(
    () => composeDiscoveryRows(data.overview, data.selectedCohort, preset.columns, settings),
    [
      data.overview, data.selectedCohort, selection.table, selection.strength,
      settings.peers, settings.peerMin, settings.specialtyMin,
    ],
  );
  const { rows: filtered, unknownTimeExcluded } = filterDiscoveryRows(
    rows,
    discovery,
  );
  const players = sortDiscoveryRows(filtered, sort, dir);
  const teams = teamOptions(data.overview.players.map(row => row.person));
  const sortGroupCount = sort === "name"
    ? 0 : new Set(rows.map(row => row.cells[sort]!.semanticKey)).size;
  const [exportError, setExportError] = useState("");
  const commit = (next: URLSearchParams, replace = false) => {
    if (next.toString() !== viewSearch(location, navigation.location).toString())
      setSearch(next, {
        replace,
        preventScrollReset: true,
        state: location.state,
        flushSync: true,
      });
  };
  const changePeers = (values: Partial<PeerSettings>) => {
    const next = viewSearch(location, navigation.location);
    for (const [key, value] of Object.entries(values)) next.set(key, String(value));
    commit(next);
  };
  const profileSearch = (metric?: string) => {
    const next = seasonSearch("", data.season.season);
    for (const key of ["peers", "peerMin", "specialtyMin", "history"])
      if (search.has(key)) next.set(key, search.get(key)!);
    if (selection.table === "observed" || selection.table === "descriptive") next.set("view", "observed");
    const selectedMetric = metric ?? search.get("metric");
    if (selectedMetric && analysisMetric(selectedMetric)?.kind === "skater")
      next.set("metric", selectedMetric);
    return next;
  };
  const clear = () => {
    setMinute({ committed: 0, draft: "0", error: "" });
    if (q === "" && position === "all" && team === null && min === 0) return;
    const next = viewSearch(location, navigation.location);
    for (const key of ["q", "position", "team", "min"]) next.delete(key);
    commit(next);
  };
  const header = (key: Sort, label: string, accessible: string) => (
    <th
      scope="col"
      aria-sort={
        sort === key ? (dir === "asc" ? "ascending" : "descending") : "none"
      }
      className={key === "name" ? "identity" : "numeric"}
    >
      <button
        type="button"
        aria-label={`sort by ${accessible}`}
        onClick={() => {
          const next = viewSearch(location, navigation.location);
          next.set("sort", key);
          next.set(
            "dir",
            sort === key
              ? dir === "asc"
                ? "desc"
                : "asc"
              : key === "name"
                ? "asc"
                : "desc",
          );
          commit(next);
        }}
      >
        {label}
        {sort === key && (
          <span className="sort-direction">
            {" "}
            {dir === "asc" ? "asc." : "desc."}
          </span>
        )}
      </button>
    </th>
  );
  return (
    <>
      <section className="league-heading">
        <h2>player discovery</h2>
        <p>
          experimental seasonal estimates and recorded results. sort raw values;
          each field retains its own support and annual comparison population.
        </p>
        <Link
          to={`/compare?${profileSearch()}`}
          state={{ leagueSearch: `?${seasonSearch(search, data.season.season)}` }}
        >
          compare players
        </Link>
      </section>
      <p className="experimental-status">
        experimental estimates · seasonal levels, not forecasts or causal effects
      </p>
      <nav className="discovery-presets" aria-label="analytical table">
        {discoveryTables.map(table => (
          <button
            key={table}
            type="button"
            aria-pressed={table === selection.table}
            onClick={() => {
              const next = viewSearch(location, navigation.location);
              if (table === "overview") next.delete("table");
              else next.set("table", table);
              next.delete("strength");
              const target = discoveryPreset(
                table,
                table === "spatial" || table === "execution" || table === "shootiness"
                  ? "5v5" : null,
              );
              if (!["name", ...target.columns.map(column => column.id)]
                .includes(next.get("sort") ?? target.defaultSort)) {
                next.delete("sort");
                next.delete("dir");
              }
              commit(next);
            }}
          >
            {table === "overview" ? "value overview"
              : table === "observed" ? "recorded 5v5"
              : table === "descriptive" ? "recorded card facts" : table}
          </button>
        ))}
      </nav>
      {selection.strength !== null && (
        <div className="strength-control">
          <label htmlFor="table-strength">exact table strength</label>
          <select
            id="table-strength"
            value={selection.strength}
            onChange={event => {
              const next = viewSearch(location, navigation.location);
              next.set("strength", event.currentTarget.value);
              const target = discoveryPreset(selection.table, event.currentTarget.value);
              if (!["name", ...target.columns.map(column => column.id)]
                .includes(next.get("sort") ?? target.defaultSort)) {
                next.delete("sort");
                next.delete("dir");
              }
              commit(next);
            }}
          >
            {(selection.table === "spatial"
              ? ["5v5", "pp", "pk"]
              : ["5v5", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4"]
            ).map(strength => <option key={strength}>{strength}</option>)}
          </select>
        </div>
      )}
      {selection.table !== "descriptive" && (
        <PeerControls settings={settings} onChange={changePeers} allCutoffs />
      )}
      <GlobalGap season={data.season} />
      <div className="discovery-controls">
        <div className="search-control">
          <label htmlFor="player-search">search players</label>
          <input
            id="player-search"
            type="search"
            value={q}
            onChange={(event) => {
              const next = viewSearch(location, navigation.location);
              if (event.currentTarget.value)
                next.set("q", event.currentTarget.value);
              else next.delete("q");
              commit(next, true);
            }}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <div>
          <label htmlFor="discovery-position">reported position group</label>
          <select
            id="discovery-position"
            value={position}
            onChange={(event) => {
              const next = viewSearch(location, navigation.location);
              if (event.currentTarget.value === "all") next.delete("position");
              else next.set("position", event.currentTarget.value);
              commit(next);
            }}
          >
            <option value="all">all skaters</option>
            <option value="f">reported forwards</option>
            <option value="d">reported defense</option>
          </select>
        </div>
        <div>
          <label htmlFor="discovery-team">listed season team</label>
          <select
            id="discovery-team"
            value={team ?? ""}
            onChange={(event) => {
              const next = viewSearch(location, navigation.location);
              if (event.currentTarget.value)
                next.set("team", event.currentTarget.value);
              else next.delete("team");
              commit(next);
            }}
          >
            <option value="">all season teams</option>
            {team && !teams.some((row) => row.id === team) && (
              <option value={team}>
                team {team} — not in this season
              </option>
            )}
            {teams.map((row) => (
              <option key={row.id} value={row.id}>
                {teamName(row)}
              </option>
            ))}
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
            if (value === min) return;
            const next = viewSearch(location, navigation.location);
            if (value === 0) next.delete("min");
            else next.set("min", String(value));
            commit(next);
          }}
        >
          <label htmlFor="discovery-min">
            minimum on-ice included 5v5 minutes
          </label>
          <div className="minute-input">
            <input
              id="discovery-min"
              inputMode="numeric"
              value={minute.draft}
              aria-invalid={Boolean(minute.error)}
              aria-describedby={
                minute.error ? "discovery-min-error" : undefined
              }
              onChange={(event) =>
                setMinute({
                  ...minute,
                  draft: event.currentTarget.value,
                  error: "",
                })
              }
            />
            <button type="submit">apply minimum</button>
          </div>
          {minute.error && (
            <p
              id="discovery-min-error"
              className="selection-error"
              role="alert"
            >
              {minute.error}
            </p>
          )}
        </form>
        <button type="button" onClick={clear}>
          clear filters
        </button>
      </div>
      <p className="control-note">
        matches listed season teams; results still cover all included season
        games. display filters never change peer populations. a zero minimum includes
        missing or zero observed time; a positive minimum uses available included observed 5v5 time in every table.
        {min > 0 && ` ${unknownTimeExcluded} otherwise matching skaters excluded because observed time is unavailable.`}
      </p>
      <p role="status" className="result-count">
        {players.length} of {data.overview.players.length} published skaters
      </p>
      <button
        type="button"
        disabled={!players.length}
        onClick={() => {
          setExportError("");
          try {
            downloadCsv(
              discoveryCsvHeaders,
              discoveryCsvRows(data.publication, data.season, players, preset),
              `${preset.table}${preset.strength ? `-${preset.strength}` : ""}-${data.season.season}-${data.publication.publication_id}.csv`,
            );
          } catch {
            setExportError("table export failed; retry the download.");
          }
        }}
      >
        download visible table csv
      </button>
      {exportError && <p role="alert">{exportError}</p>}
      {players.length === 0 ? (
        <p className="empty-search">
          no skaters match these filters.{" "}
          <button type="button" onClick={clear}>clear filters</button>
        </p>
      ) : (
        <div
          className="table-scroll"
          tabIndex={0}
          aria-label="player analysis table, scroll horizontally for all columns"
        >
          <table className="league-table discovery-table">
            <caption>
              {selection.table} {selection.strength ?? ""} · {selection.table === "descriptive"
                ? "unadjusted recorded values; no percentile defined. ev and pp use their own scoring minutes."
                : "raw values and neutral standings; higher percentile means higher named value."}
              {" "}included observed time is 5v5. reported usage/count/time columns have no percentile.
            </caption>
            <thead>
              <tr>
                {header("name", "player", "player name")}
                <th scope="col">season teams</th>
                <th scope="col">position</th>
                {preset.columns.map(column => (
                  <Fragment key={column.id}>
                    {header(column.id, column.label, column.label)}
                  </Fragment>
                ))}
              </tr>
            </thead>
            <tbody>
              {players.map((row, index) => {
                const active = sort === "name" ? null : row.cells[sort]!;
                const previous = index ? players[index - 1]!.cells[sort] : null;
                return (
                  <Fragment key={row.person.player_id}>
                    {active && sortGroupCount > 1 &&
                      (!previous || previous.semanticKey !== active.semanticKey) && (
                        <tr className="semantic-group">
                          <th colSpan={preset.columns.length + 3} scope="rowgroup">
                            sort definition: {active.semanticIdentityKnown
                              ? active.definition : "meaning unavailable"}
                          </th>
                        </tr>
                      )}
                    <tr>
                      <th scope="row" className="identity">
                        <Link
                          to={`/players/${row.person.player_id}?${profileSearch()}`}
                          state={{ leagueSearch: `?${seasonSearch(search, data.season.season)}` }}
                        >
                          {playerName(row.person)}
                        </Link>
                      </th>
                      <td>{row.person.teams.map(teamName).join(" / ") || "unavailable"}</td>
                      <td>{row.person.reported_position ?? "unknown"}</td>
                      {preset.columns.map(column => {
                        const cell = row.cells[column.id]!;
                        return (
                          <td key={column.id} className="numeric analysis-cell">
                            {cell.kind === "metric" ? (
                              <>
                                <Link
                                  to={`/players/${row.person.player_id}?${profileSearch(column.id)}`}
                                  state={{ leagueSearch: `?${seasonSearch(search, data.season.season)}` }}
                                >
                                  {valueText(cell.row.datum)} {cell.row.datum.metric.displayUnit}
                                </Link>
                                {cell.row.datum.metric.standingPolicy !== "raw_only" && <span className="cell-standing">
                                  {standingText(cell.row.standing)}
                                  {cell.row.standing.peerGroup && ` · ${cell.row.standing.peerGroup}`}
                                  {cell.row.standing.n !== null && ` · n=${cell.row.standing.n}`}
                                  {cell.row.standing.cutoffMinutes !== null && ` · ≥${cell.row.standing.cutoffMinutes} min`}
                                </span>}
                                <details>
                                  <summary>field evidence</summary>
                                  <DatumEvidence datum={cell.row.datum} />
                                </details>
                              </>
                            ) : (
                              <>
                                <span>{cell.value === null
                                  ? cell.reason ?? cell.status
                                  : `${displayNumber(cell.value * cell.displayScale)} ${cell.displayUnit}`}</span>
                                <details>
                                  <summary>source / coverage</summary>
                                  {cell.source && (
                                    <p>
                                      {cell.source.construction} · {cell.source.population} · {cell.source.definition}
                                    </p>
                                  )}
                                  {cell.observedSupport ? (
                                    <CoverageDetail
                                      metrics={cell.observedSupport as Parameters<typeof CoverageDetail>[0]["metrics"]}
                                    />
                                  ) : <pre>{JSON.stringify(cell.evidence, null, 2)}</pre>}
                                </details>
                              </>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Evidence publication={data.publication} season={data.season} />
    </>
  );
}
