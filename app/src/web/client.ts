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
import { readMapMode, readMetric } from "./explorer";
import { selectHistoryValue, selectLeagueValues, type AnalysisMetric } from "./analysis-values";

// each route composes its bounded publication reads before rendering.
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
  readonly selectedMetric: AnalysisMetric;
  readonly scalarHistory: readonly ScalarHistoryRow[];
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
export type ScalarHistoryRow = PlayerResponse["history"][number] & {
  readonly cohort: LeagueResponse;
};
export type ComparisonView = LeagueView & {
  readonly selectedMetric: AnalysisMetric;
  readonly scalarCohort: LeagueResponse;
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

// publication metadata and displayed years are one snapshot, across all annual corpora.
function samePublication(a: Release, b: Release) {
  if (!equal(a.publication, b.publication) || !equal(a.available_seasons, b.available_seasons))
    throw new Error("responses describe different publications or displayed seasons");
}

function sameRelease(a: Release, b: Release) {
  samePublication(a, b);
  if (!equal(a.season, b.season))
    throw new Error(`responses describe different season evidence: ${a.season.season} and ${b.season.season}`);
}

function equal(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== "object" || a === null || typeof b !== "object" || b === null) return false;
  const left = Object.entries(a), right = Object.entries(b);
  return left.length === right.length && left.every(([key, value]) =>
    Object.hasOwn(b, key) && equal(value, (b as Record<string, unknown>)[key]));
}

type Envelope = Pick<PlayerResponse, "sources" | "methods" | "supports">;
function catalogs(inputs: readonly Envelope[]): Envelope {
  const merged: Envelope = { sources: {}, methods: {}, supports: {} };
  for (const input of inputs) {
    for (const name of ["sources", "methods", "supports"] as const) {
      const target = merged[name] as Record<string, unknown>;
      for (const [id, value] of Object.entries(input[name])) {
        if (Object.hasOwn(target, id) && !equal(target[id], value))
          throw new Error(`conflicting ${name} catalog entry: ${id}`);
        target[id] = value;
      }
    }
  }
  return merged;
}

type ScalarRequest = Pick<LeagueResponse, "kind" | "family" | "strength"> & { readonly season: string };
const requestKey = (request: ScalarRequest) => JSON.stringify([
  request.season, request.kind, request.family, request.strength,
]);
const scalarRequest = (season: string, metric: AnalysisMetric): ScalarRequest => ({
  season, kind: metric.kind, family: metric.family, strength: metric.strength,
});
const scalarQuery = ({ strength, ...request }: ScalarRequest) => ({
  ...request, ...(strength === null ? {} : { strength }),
});
function checkRequest(response: LeagueResponse, request: ScalarRequest) {
  if (requestKey({ ...response, season: response.season.season }) !== requestKey(request))
    throw new Error("league response does not match its requested field population");
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

function composeProfile(detail: PlayerResponse, league: LeagueView, selectedMetric: AnalysisMetric, scalarHistory: readonly ScalarHistoryRow[]): ProfileView {
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
    selectedMetric,
    scalarHistory,
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

// the player response owns annual identity, absence and displayed-season evidence.
export const loadProfile = (playerId: string, signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.gen(function* () {
      const api = yield* client;
      const detail = yield* api.analysis.player({ params: { playerId }, query: { season: seasonQuery(query) } });
      const metric = readMetric(query, detail.kind).metric;
      const observedRequest: ScalarRequest | null = detail.kind === "skater"
        ? { season: detail.season.season, kind: "skater", family: "observed", strength: "5v5" }
        : null;
      const requests = [...new Map([
        ...(observedRequest === null ? [] : [observedRequest]),
        ...detail.available_seasons.map((season) => scalarRequest(season, metric)),
      ].map((request) => [requestKey(request), request])).values()];
      const responses = yield* Effect.all(
        requests.map((request) => api.analysis.league({ query: scalarQuery(request) })),
        { concurrency: "unbounded" },
      );
      const profile = yield* compose(() => {
        responses.forEach((response, index) => {
          samePublication(detail, response);
          checkRequest(response, requests[index]);
        });
        const resolved = catalogs([detail, ...responses]);
        const cohorts = new Map(responses.map((response, index) => [requestKey(requests[index]), { ...response, ...resolved }]));
        const scalarHistory = detail.history.map((row): ScalarHistoryRow => {
          const cohort = cohorts.get(requestKey(scalarRequest(row.season.season, metric)))!;
          sameRelease({ ...detail, season: row.season }, cohort);
          const member = cohort.players.find(({ person }) => person.player_id === detail.player_id);
          const selected = selectHistoryValue(row, cohort, metric, playerId);
          if (member) {
            if (!equal(row.person, member.person))
              throw new Error(`player ${playerId}: annual identity differs from its cohort row`);
            const peer = selectLeagueValues(cohort, metric).find((value) => value.playerId === playerId);
            // family-envelope copy may differ; original field reasons and evidence remain exact.
            const agrees = selected.status === "not_computed" && peer?.status === "not_computed"
              ? equal({ ...selected, reason: null }, { ...peer, reason: null })
              : equal(selected, peer);
            if (!agrees)
              throw new Error(`player ${playerId}: selected scalar or support differs from its annual cohort row`);
          } else if (selected.value !== null) {
            throw new Error(`player ${playerId}: available scalar has no annual cohort row`);
          }
          return { ...row, cohort };
        });
        const league: LeagueView = detail.kind === "goalie"
          ? { publication: detail.publication, available_seasons: detail.available_seasons, season: detail.season, players: [] }
          : composeLeague(cohorts.get(requestKey(observedRequest!))!);
        return composeProfile(detail, league, metric, scalarHistory);
      });
      if (!profile.player) return profile;
      const view = mapView(query);
      const maps = yield* api.analysis.maps({ query: mapsQuery(profile.season.season, [playerId], view) });
      return yield* compose((): ProfileView => {
        catalogs([detail, ...responses, maps]);
        return { ...profile, maps: observedMaps(maps, profile, [playerId], view) };
      });
    }),
    signal,
  );

// the observed picker stays bounded; the selected field retains its complete cohort.
export const loadComparison = (signal: AbortSignal, query: URLSearchParams) =>
  read(
    Effect.gen(function* () {
      const api = yield* client;
      const observed = yield* api.analysis.league({ query: cohortQuery(query) });
      const league = yield* compose(() => composeLeague(observed));
      const metric = readMetric(query, "skater").metric;
      const request = scalarRequest(league.season.season, metric);
      const scalar = requestKey(request) === requestKey({ ...observed, season: observed.season.season })
        ? observed
        : yield* api.analysis.league({ query: scalarQuery(request) });
      const scalarCohort = yield* compose(() => {
        sameRelease(observed, scalar);
        checkRequest(scalar, request);
        return { ...scalar, ...catalogs([observed, scalar]) };
      });
      const [first, second] = ["a", "b"].map((key) => {
        const values = query.getAll(key);
        return values.length === 1 ? league.players.find((row) => row.player_id === values[0]) : undefined;
      });
      if (!first || !second || first.player_id === second.player_id)
        return { ...league, selectedMetric: metric, scalarCohort, pair: null, maps: null } satisfies ComparisonView;
      yield* compose(() => {
        for (const player of [first, second]) {
          const identity = observed.players.find((row) => row.person.player_id === player.player_id)!.person;
          const member = scalarCohort.players.find((row) => row.person.player_id === player.player_id);
          if (!member || !equal(identity, member.person))
            throw new Error(`player ${player.player_id}: comparison identity differs from its selected-field cohort row`);
        }
      });
      const ids = [first.player_id, second.player_id];
      const view = mapView(query);
      const maps = yield* api.analysis.maps({ query: mapsQuery(league.season.season, ids, view) });
      return yield* compose((): ComparisonView => {
        catalogs([observed, scalar, maps]);
        return {
          ...league, selectedMetric: metric, scalarCohort, pair: [first, second],
          maps: observedMaps(maps, league, ids, view),
        };
      });
    }),
    signal,
  );
