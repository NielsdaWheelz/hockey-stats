import { useEffect, useState } from "react";
import {
  Link,
  useLoaderData,
  useLocation,
  useSearchParams,
  type ClientLoaderFunctionArgs,
  type ShouldRevalidateFunctionArgs,
} from "react-router";
import { loadLeague } from "../client";
import {
  parseMinutes,
  readDiscovery,
  selectDiscovery,
  teamOptions,
  type Sort,
} from "../explorer";
import {
  CoverageDetail,
  Evidence,
  GlobalGap,
  LoadError,
  Minutes,
  Quantity,
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
    for (const key of ["q", "sort", "dir", "position", "team", "min"]) {
      current.delete(key);
      next.delete(key);
    }
    if (current.toString() === next.toString()) return false;
  }
  return defaultShouldRevalidate;
}

export default function League() {
  const data = useLoaderData<typeof clientLoader>();
  const location = useLocation();
  const [search, setSearch] = useSearchParams();
  const { discovery, search: normalized } = readDiscovery(search);
  const { q, sort, dir, position, team, min } = discovery;
  const [minute, setMinute] = useState({
    committed: min,
    draft: String(min),
    error: "",
  });
  if (minute.committed !== min)
    setMinute({ committed: min, draft: String(min), error: "" });
  useEffect(() => {
    if (normalized.toString() !== search.toString())
      setSearch(normalized, {
        replace: true,
        preventScrollReset: true,
        state: location.state,
      });
  }, [normalized.toString(), search, setSearch, location.state]);
  const players = selectDiscovery(data.players, discovery);
  const teams = teamOptions(data.players);
  const commit = (next: URLSearchParams, replace = false) => {
    if (next.toString() !== search.toString())
      setSearch(next, {
        replace,
        preventScrollReset: true,
        state: location.state,
      });
  };
  const clear = () => {
    setMinute({ committed: 0, draft: "0", error: "" });
    if (q === "" && position === "all" && team === null && min === 0) return;
    const next = new URLSearchParams(search);
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
          const next = new URLSearchParams(search);
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
        <h2>explore included results</h2>
        <p>
          matched counts and time, with source coverage alongside. rate ordering
          describes recorded results.
        </p>
        <Link to="/compare" state={{ leagueSearch: location.search }}>
          compare players
        </Link>
      </section>
      <GlobalGap coverage={data.coverage} />
      <div className="discovery-controls">
        <div className="search-control">
          <label htmlFor="player-search">search players</label>
          <input
            id="player-search"
            type="search"
            value={q}
            onChange={(event) => {
              const next = new URLSearchParams(search);
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
              const next = new URLSearchParams(search);
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
              const next = new URLSearchParams(search);
              if (event.currentTarget.value)
                next.set("team", event.currentTarget.value);
              else next.delete("team");
              commit(next);
            }}
          >
            <option value="">all season teams</option>
            {team && !teams.some((row) => row.id === team) && (
              <option value={team}>
                team {team} — not in this publication
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
            const next = new URLSearchParams(search);
            if (value === 0) next.delete("min");
            else next.set("min", String(value));
            commit(next);
          }}
        >
          <label htmlFor="discovery-min">minimum included 5v5 minutes</label>
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
        games.
      </p>
      <p role="status" className="result-count">
        {players.length} of {data.players.length} published players
      </p>
      {players.length === 0 ? (
        <p className="empty-search">
          no players match the active filters: name {q ? `“${q}”` : "any"};
          position{" "}
          {position === "all"
            ? "all skaters"
            : position === "f"
              ? "reported forwards"
              : "reported defense"}
          ; team {team ?? "all"}; at least {min} included minutes.{" "}
          <button type="button" onClick={clear}>
            clear filters
          </button>
        </p>
      ) : (
        <div
          className="table-scroll"
          tabIndex={0}
          aria-label="player results table, scroll horizontally for all columns"
        >
          <table className="league-table">
            <caption>
              included season results · games means games with included time;
              minutes are matched 5v5 exposure
            </caption>
            <thead>
              <tr>
                {header("name", "player", "player name")}
                <th scope="col">season teams</th>
                <th scope="col">position</th>
                {header("games", "games", "games with included time")}
                {header("minutes", "matched min", "matched minutes")}
                {header("for60", "for/60", "attempts for/60")}
                {header("against60", "against/60", "attempts against/60")}
                <th scope="col">coverage</th>
              </tr>
            </thead>
            <tbody>
              {players.map((player) => (
                <tr key={player.player_id}>
                  <th scope="row" className="identity">
                    <Link
                      to={`/players/${player.player_id}`}
                      state={{ leagueSearch: location.search }}
                    >
                      {playerName(player)}
                    </Link>
                  </th>
                  <td>{player.teams.map(teamName).join(" / ")}</td>
                  <td>{player.reported_position}</td>
                  <td className="numeric">{player.games_with_included_time}</td>
                  <td className="numeric">
                    <Minutes seconds={player.metrics.included_seconds} />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={player.metrics.for_per60}
                      metrics={player.metrics}
                      rate
                    />
                  </td>
                  <td className="numeric">
                    <Quantity
                      value={player.metrics.against_per60}
                      metrics={player.metrics}
                      rate
                    />
                  </td>
                  <td>
                    <CoverageDetail metrics={player.metrics} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Evidence publication={data.publication} coverage={data.coverage} />
    </>
  );
}
