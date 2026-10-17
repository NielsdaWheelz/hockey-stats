import { useEffect } from "react";
import {
  Link,
  useLoaderData,
  useLocation,
  useSearchParams,
  type ClientLoaderFunctionArgs,
  type ShouldRevalidateFunctionArgs,
} from "react-router";
import type { PlayerSummary } from "../../shared/observed";
import { loadLeague } from "../client";
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

type Sort = "name" | "games" | "minutes" | "for60" | "against60";
const sorts: readonly Sort[] = [
  "name",
  "games",
  "minutes",
  "for60",
  "against60",
];

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
    for (const key of ["q", "sort", "dir"]) {
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
  const q = search.get("q") ?? "";
  const rawSort = search.get("sort");
  const sort: Sort = sorts.includes(rawSort as Sort)
    ? (rawSort as Sort)
    : "minutes";
  const dir = search.get("dir") === "asc" ? "asc" : "desc";
  useEffect(() => {
    const next = new URLSearchParams(search);
    if (rawSort !== null && !sorts.includes(rawSort as Sort))
      next.delete("sort");
    if (search.has("dir") && !["asc", "desc"].includes(search.get("dir")!))
      next.delete("dir");
    if (next.toString() !== search.toString())
      setSearch(next, { replace: true, preventScrollReset: true });
  }, [search, rawSort, setSearch]);
  const normalized = (value: string) =>
    value.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");
  const tokens = normalized(q).trim().split(/\s+/).filter(Boolean);
  const players = data.players.filter((player) =>
    tokens.every((token) => normalized(playerName(player)).includes(token)),
  );
  const nameOrder = (a: PlayerSummary, b: PlayerSummary) =>
    playerName(a).localeCompare(playerName(b), "en") ||
    a.player_id.length - b.player_id.length ||
    a.player_id.localeCompare(b.player_id);
  const value = (player: PlayerSummary) =>
    sort === "games"
      ? player.games_with_included_time
      : sort === "minutes"
        ? player.metrics.included_seconds
        : sort === "for60"
          ? player.metrics.for_per60
          : player.metrics.against_per60;
  players.sort((a, b) => {
    if (sort === "name")
      return (
        (dir === "asc" ? 1 : -1) *
          playerName(a).localeCompare(playerName(b), "en") || nameOrder(a, b)
      );
    const left = value(a),
      right = value(b);
    if (left === null) return right === null ? nameOrder(a, b) : 1;
    if (right === null) return -1;
    return (dir === "asc" ? left - right : right - left) || nameOrder(a, b);
  });
  const updateQuery = (query: string) => {
    const next = new URLSearchParams(search);
    if (query) next.set("q", query);
    else next.delete("q");
    setSearch(next, { replace: true, preventScrollReset: true });
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
          setSearch(next, { preventScrollReset: true });
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
        <h2>included results</h2>
        <p>
          matched counts and time, with source coverage alongside. rate ordering
          describes recorded results.
        </p>
      </section>
      <GlobalGap coverage={data.coverage} />
      <div className="search-row">
        <div>
          <label htmlFor="player-search">search players</label>
          <input
            id="player-search"
            type="search"
            value={q}
            onChange={(event) => updateQuery(event.currentTarget.value)}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <button type="button" onClick={() => updateQuery("")} disabled={!q}>
          clear search
        </button>
        <p role="status">
          {players.length} {players.length === 1 ? "player" : "players"}
        </p>
      </div>
      {players.length === 0 ? (
        <p className="empty-search">no players match this search.</p>
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
