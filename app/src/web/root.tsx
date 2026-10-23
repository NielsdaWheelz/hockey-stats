import { useEffect, useRef, type ReactNode } from "react";
import type { ComparisonView, LeagueView, ProfileView } from "./client";
import {
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLocation,
  useNavigation,
  useRouteLoaderData,
  useSearchParams,
} from "react-router";
import stylesheet from "./styles.css?url";
import { LoadError, seasonLabel } from "./presentation";
import { pendingSeasonChange, seasonSearch, viewSearch } from "./explorer";

export const links = () => [{ rel: "stylesheet", href: stylesheet }];
export const meta = () => [
  { title: "hockey statistics · published player analysis" },
  {
    name: "description",
    content:
      "published observations, experimental estimates and their evidence",
  },
];

export function Layout({ children }: { readonly children: ReactNode }) {
  const league = useRouteLoaderData<LeagueView>("routes/league");
  const player = useRouteLoaderData<ProfileView>("routes/player");
  const comparison = useRouteLoaderData<ComparisonView>("routes/compare");
  const data = player ?? league ?? comparison;
  const season = data?.season.season;
  const location = useLocation();
  const navigation = useNavigation();
  const [, setSearch] = useSearchParams();
  const pending = viewSearch(location, navigation.location).getAll("season");
  const selected =
    pending.length === 1 && data?.available_seasons.includes(pending[0]!)
      ? pending[0]!
      : season;
  const changingSeason =
    navigation.state !== "idle" &&
    pendingSeasonChange(location, navigation.location);
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <a
          className="skip-link"
          href="#main"
          onClick={(event) => {
            event.preventDefault();
            document.getElementById("main")?.focus();
          }}
        >
          skip to results
        </a>
        <div className="sheet">
          {data?.publication.purpose === "fixture" && (
            <p className="fixture-banner" role="note">
              fixture publication · development evidence, not real results
            </p>
          )}
          <header className="site-heading">
            <p className="eyebrow">
              <Link to={season ? `/?${seasonSearch("", season)}` : "/"}>
                hockey statistics / player analysis
              </Link>
            </p>
            <h1>
              {season && !changingSeason && `${seasonLabel(season)} · `}regular
              season · published player analysis
            </h1>
            <p>
              recorded results and experimental estimates retain their own
              populations, numerical references and support.
            </p>
            {data && (
              <div className="season-control">
                <label htmlFor="season-selection">season</label>
                <select
                  id="season-selection"
                  value={selected}
                  onChange={(event) => {
                    const next = viewSearch(location, navigation.location);
                    if (
                      next.getAll("season").length === 1 &&
                      next.get("season") === event.currentTarget.value
                    )
                      return;
                    next.set("season", event.currentTarget.value);
                    setSearch(next, {
                      preventScrollReset: true,
                      state: location.state,
                      flushSync: true,
                    });
                  }}
                >
                  {data.available_seasons.map((value) => (
                    <option key={value} value={value}>
                      {seasonLabel(value)}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </header>
          {children}
          <footer>
            observations and experimental estimates · limitations belong to each
            quantity
          </footer>
        </div>
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export function HydrateFallback() {
  return (
    <main id="main">
      <p role="status">loading published results…</p>
    </main>
  );
}

export default function App() {
  const navigation = useNavigation();
  const location = useLocation();
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    main.current?.focus({ preventScroll: true });
  }, [location.pathname]);
  const changingPage =
    navigation.state !== "idle" &&
    (navigation.location?.pathname !== location.pathname ||
      pendingSeasonChange(location, navigation.location));
  return (
    <main id="main" ref={main} tabIndex={-1}>
      {changingPage ? (
        <p role="status">loading published results…</p>
      ) : (
        <Outlet />
      )}
    </main>
  );
}

export const ErrorBoundary = LoadError;
