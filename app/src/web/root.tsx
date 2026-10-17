import { useEffect, useRef, type ReactNode } from "react";
import type { LeagueResponse, PlayerResponse } from "../shared/observed";
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
} from "react-router";
import stylesheet from "./styles.css?url";
import { LoadError } from "./presentation";

export const links = () => [{ rel: "stylesheet", href: stylesheet }];
export const meta = () => [
  { title: "hockey statistics · recorded results" },
  {
    name: "description",
    content: "included 5v5 recorded results and source coverage",
  },
];

export function Layout({ children }: { readonly children: ReactNode }) {
  const league = useRouteLoaderData<LeagueResponse>("routes/league");
  const player = useRouteLoaderData<PlayerResponse>("routes/player");
  const comparison = useRouteLoaderData<LeagueResponse>("routes/compare");
  const season = (player ?? league ?? comparison)?.publication.season;
  const seasonLabel = season ? `${season.slice(0, 4)}–${season.slice(6)}` : "";
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <a className="skip-link" href="#main">
          skip to results
        </a>
        <div className="sheet">
          <header className="site-heading">
            <p className="eyebrow">
              <Link to="/">hockey statistics / included results</Link>
            </p>
            <h1>
              {seasonLabel && `${seasonLabel} · `}regular season · 5v5 recorded
              results
            </h1>
            <p>
              recorded while each player was on the ice; unadjusted for
              teammates, opponents, score or deployment.
            </p>
          </header>
          {children}
          <footer>
            source-supported observations · no estimate of player ability
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
      <p role="status">loading recorded results…</p>
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
    navigation.location?.pathname !== location.pathname;
  return (
    <main id="main" ref={main} tabIndex={-1}>
      {changingPage ? (
        <p role="status">loading recorded results…</p>
      ) : (
        <Outlet />
      )}
    </main>
  );
}

export const ErrorBoundary = LoadError;
