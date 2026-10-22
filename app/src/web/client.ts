import * as Effect from "effect/Effect";
import * as Result from "effect/Result";
import * as FetchHttpClient from "effect/http/FetchHttpClient";
import * as HttpApiClient from "effect/http-api/HttpApiClient";
import * as Schema from "effect/Schema";
import type {
  Deployment,
  PlayerGame,
  PlayerSummary,
  Publication,
  SeasonEvidence,
  SpatialSelection,
} from "../shared/observed";
import {
  ApiError,
  PlayerAnalysisApi,
  type LeagueResponse,
  type MapsResponse,
  type Person,
  type PlayerFamilies,
  type PlayerResponse,
} from "../shared/player-analysis";
import { readMapMode } from "./explorer";

// current views: the observed skater cohort and observed maps, joined into one view model per route.
type Release = {
  readonly publication: Publication;
  readonly available_seasons: readonly string[];
  readonly season: SeasonEvidence;
};
export type LeagueView = Release & { readonly players: readonly PlayerSummary[] };
export type ObservedMaps = {
  readonly selection: SpatialSelection;
  readonly scale: Extract<MapsResponse, { family: "observed" }>["scale"];
};
export type ProfileView = Release & {
  readonly player_id: string;
  readonly kind: PlayerResponse["kind"];
  readonly person: Person | null;
  readonly player: PlayerSummary | undefined;
  readonly observedExplanation: string | null;
  readonly players: readonly PlayerSummary[];
  readonly games: readonly PlayerGame[];
  readonly deployment: Deployment | null;
  readonly maps: ObservedMaps | null;
  readonly history: readonly {
    readonly season: SeasonEvidence;
    readonly person: Person | null;
    readonly player: PlayerSummary | null;
  }[];
};
export type ComparisonView = LeagueView & {
  readonly pair: readonly [PlayerSummary, PlayerSummary] | null;
  readonly maps: ObservedMaps | null;
};

const client = HttpApiClient.make(PlayerAnalysisApi).pipe(
  Effect.provide(FetchHttpClient.layer),
);
const headers = { "content-type": "application/json" };

async function read<A, E>(
  effect: Effect.Effect<A, E>,
  signal: AbortSignal,
): Promise<A> {
  const result = await Effect.runPromise(Effect.result(effect), { signal });
  if (Result.isSuccess(result)) return result.success;
  const error = result.failure;
  if (Schema.is(ApiError)(error)) {
    const status =
      error._tag === "PlayerNotFound" || error._tag === "SeasonNotFound" || error._tag === "NotFound"
        ? 404
        : error._tag === "ReadFailure"
          ? 500
          : 400;
    throw new Response(JSON.stringify(error), { status, headers });
  }
  console.error("publication response could not be used", error);
  throw new Response(JSON.stringify({ _tag: "ReadFailure", message: "results could not be loaded. please try again." }), {
    status: 500,
    headers,
  });
}

const compose = <A>(join: () => A) => Effect.try({ try: join, catch: (error) => error });

const seasonQuery = (query: URLSearchParams) => {
  const values = query.getAll("season");
  return values.length === 0 ? undefined : values.length === 1 ? values[0] : values;
};
const cohortQuery = (query: URLSearchParams) => ({
  season: seasonQuery(query),
  kind: "skater",
  family: "observed",
  strength: "5v5",
});
const mapView = (query: URLSearchParams) =>
  readMapMode(query).mode === "absolute" ? "complete" : "effect";

// a season is identified by its corpus evidence, not only its year.
function sameRelease(a: Release, b: Release) {
  const identity = (release: Release) =>
    `${release.publication.publication_id}/${release.season.season}/${release.season.corpus_sha256}`;
  if (identity(a) !== identity(b))
    throw new Error(`responses describe different publications or seasons: ${identity(a)} and ${identity(b)}`);
}

function composeLeague(response: LeagueResponse): LeagueView {
  if (response.family !== "observed") throw new Error(`expected the observed cohort, got ${response.family}`);
  return {
    publication: response.publication,
    available_seasons: response.available_seasons,
    season: response.season,
    players: response.players.map(({ result }) => {
      if (result.availability !== "provided") throw new Error("observed cohort rows must be provided summaries");
      return result.data;
    }),
  };
}

// absent seasons and goalies carry no observed skater envelope.
const observedOf = (families: PlayerFamilies) =>
  "availability" in families || families.kind !== "skater" ? null : families.observed;

function composeProfile(detail: PlayerResponse, league: LeagueView): ProfileView {
  sameRelease(detail, league);
  const observed = observedOf(detail.families);
  const player = league.players.find((row) => row.player_id === detail.player_id);
  const summary = observed?.availability === "provided" ? observed.data : undefined;
  if (JSON.stringify(player) !== JSON.stringify(summary))
    throw new Error(`player ${detail.player_id}: selected observed summary differs from its cohort row`);
  if (player) {
    const cohort = new Set(league.players.map((row) => row.player_id));
    const peers = detail.deployment ? [...detail.deployment.teammates, ...detail.deployment.opponents] : [];
    if (detail.deployment === null || peers.some((peer) => !cohort.has(peer.player_id)))
      throw new Error(`player ${detail.player_id}: deployment peers must resolve in the observed cohort`);
  }
  return {
    ...league,
    player_id: detail.player_id,
    kind: detail.kind,
    person: detail.person,
    player,
    observedExplanation: observed?.availability === "not_computed" ? observed.explanation : null,
    games: detail.observed_games,
    deployment: detail.deployment,
    maps: null,
    history: detail.history.toReversed().map((row) => {
      const observed = observedOf(row.families);
      return {
        season: row.season,
        person: row.person,
        player: observed?.availability === "provided" ? observed.data : null,
      };
    }),
  };
}

function observedMaps(
  response: MapsResponse,
  release: Release,
  players: readonly string[],
  view: "effect" | "complete",
): ObservedMaps {
  if (response.family !== "observed") throw new Error(`expected observed maps, got ${response.family}`);
  sameRelease(response, release);
  const selected = response.selection.players.map((row) => row.player_id);
  if (JSON.stringify(selected) !== JSON.stringify(players))
    throw new Error(`map players ${selected} do not match requested ${players}`);
  if (view === "effect" ? response.scale.minimum !== -response.scale.maximum : response.scale.minimum !== 0)
    throw new Error(`map scale ${response.scale.minimum}..${response.scale.maximum} does not fit the ${view} view`);
  return { selection: response.selection, scale: response.scale };
}

const mapsQuery = (season: string, players: readonly string[], view: "effect" | "complete") => ({
  season,
  players: players.join(","),
  family: "observed",
  strength: "5v5",
  view,
});

export const loadLeague = (signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.gen(function* () {
      const api = yield* client;
      const cohort = yield* api.analysis.league({ query: cohortQuery(query) });
      return yield* compose(() => composeLeague(cohort));
    }),
    signal,
  );

// the detail decides whether an observed map exists; goalies have no skater map.
export const loadProfile = (playerId: string, signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.gen(function* () {
      const api = yield* client;
      const [detail, cohort] = yield* Effect.all(
        [
          api.analysis.player({ params: { playerId }, query: { season: seasonQuery(query) } }),
          api.analysis.league({ query: cohortQuery(query) }),
        ],
        { concurrency: "unbounded" },
      );
      const profile = yield* compose(() => composeProfile(detail, composeLeague(cohort)));
      if (!profile.player) return profile;
      const view = mapView(query);
      const maps = yield* api.analysis.maps({ query: mapsQuery(profile.season.season, [playerId], view) });
      return yield* compose((): ProfileView => ({ ...profile, maps: observedMaps(maps, profile, [playerId], view) }));
    }),
    signal,
  );

// maps wait for the cohort: only a distinct pair of published skaters has an ordered map.
export const loadComparison = (signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.gen(function* () {
      const api = yield* client;
      const cohort = yield* api.analysis.league({ query: cohortQuery(query) });
      const league = yield* compose(() => composeLeague(cohort));
      const [first, second] = ["a", "b"].map((key) => {
        const values = query.getAll(key);
        return values.length === 1 ? league.players.find((row) => row.player_id === values[0]) : undefined;
      });
      if (!first || !second || first.player_id === second.player_id)
        return { ...league, pair: null, maps: null } satisfies ComparisonView;
      const ids = [first.player_id, second.player_id];
      const view = mapView(query);
      const maps = yield* api.analysis.maps({ query: mapsQuery(league.season.season, ids, view) });
      return yield* compose((): ComparisonView => ({
        ...league,
        pair: [first, second],
        maps: observedMaps(maps, league, ids, view),
      }));
    }),
    signal,
  );
