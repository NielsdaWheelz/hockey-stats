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
  type EvidenceResponse,
  type MapsResponse,
  type Person,
  type PlayerFamilies,
  type PlayerResponse,
} from "../shared/player-analysis";
import {
  readMapMode,
  readMetric,
  readTableSelection,
  readView,
  type AnalysisView,
} from "./explorer";
import {
  checkObservedIdentity,
  selectHistoryValue,
  selectLeagueValues,
  type AnalysisMetric,
} from "./analysis-values";

// each route composes its bounded publication reads before rendering.
type Release = {
  readonly publication: Publication;
  readonly available_seasons: readonly string[];
  readonly season: SeasonEvidence;
};
export type SkaterOverview = Extract<
  LeagueResponse,
  { kind: "skater"; family: "overview" }
>;
export type LeagueView = Release & {
  readonly players: readonly PlayerSummary[];
  readonly overview: SkaterOverview;
  readonly selectedCohort: LeagueResponse;
};
export type ObservedMaps = {
  readonly selection: SpatialSelection;
  readonly scale: Extract<MapsResponse, { family: "observed" }>["scale"];
};
export type ExecutionEvidence = Extract<EvidenceResponse, { family: "execution" }>;
export type ProfileView = Release & {
  readonly executionEvidence: ExecutionEvidence | null;
  readonly detail: PlayerResponse;
  readonly overviewCohorts: readonly SkaterOverview[];
  readonly view: AnalysisView;
  readonly selectedMetric: AnalysisMetric;
  readonly descriptiveCohort: Extract<LeagueResponse, { family: "descriptive" }> | null;
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
  readonly cohort: LeagueResponse | null;
};
export type ComparisonView = LeagueView & {
  readonly selectedMetric: AnalysisMetric;
  readonly scalarCohort: LeagueResponse;
  readonly persons: readonly Person[];
  readonly pair: readonly [Person, Person] | null;
  readonly profiles: readonly [ProfileView, ProfileView] | null;
  readonly overviewCohorts: readonly SkaterOverview[];
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
      error._tag === "PlayerNotFound" ||
      error._tag === "SeasonNotFound" ||
      error._tag === "NotFound"
        ? 404
        : error._tag === "ReadFailure"
          ? 500
          : 400;
    throw new Response(JSON.stringify(error), { status, headers });
  }
  console.error("publication response could not be used", error);
  throw new Response(
    JSON.stringify({
      _tag: "ReadFailure",
      message: "results could not be loaded. please try again.",
    }),
    { status: 500, headers },
  );
}

const compose = <A>(join: () => A) =>
  Effect.try({ try: join, catch: (error) => error });

const seasonQuery = (query: URLSearchParams) => {
  const values = query.getAll("season");
  return values.length === 0 ? undefined : values.length === 1 ? values[0] : values;
};
const mapView = (query: URLSearchParams) =>
  readMapMode(query).mode === "absolute" ? "complete" : "effect";

// publication metadata and displayed years are one snapshot, across all annual corpora.
function samePublication(a: Release, b: Release) {
  if (
    !equal(a.publication, b.publication) ||
    !equal(a.available_seasons, b.available_seasons)
  )
    throw new Error("responses describe different publications or displayed seasons");
}

function checkSelectedSeason(response: Release, query: URLSearchParams) {
  const values = query.getAll("season");
  if (
    values.length > 1 ||
    values.length === 1 && values[0] !== response.season.season
  )
    throw new Error("response does not match its requested season");
}

function sameRelease(a: Release, b: Release) {
  samePublication(a, b);
  if (!equal(a.season, b.season))
    throw new Error(`responses describe different season evidence: ${a.season.season} and ${b.season.season}`);
}

function equal(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== "object" || a === null || typeof b !== "object" || b === null)
    return false;
  const left = Object.entries(a),
    right = Object.entries(b);
  return left.length === right.length && left.every(([key, value]) =>
    Object.hasOwn(b, key) && equal(value, (b as Record<string, unknown>)[key]),
  );
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

type ScalarRequest = Pick<LeagueResponse, "kind" | "family" | "strength"> & {
  readonly season: string;
};
const requestKey = (request: ScalarRequest) =>
  JSON.stringify([request.season, request.kind, request.family, request.strength]);
const scalarRequest = (season: string, metric: AnalysisMetric): ScalarRequest => ({
  season,
  kind: metric.kind,
  family: metric.family,
  strength: metric.strength,
});
const scalarQuery = ({ strength, ...request }: ScalarRequest) => ({
  ...request,
  ...(strength === null ? {} : { strength }),
});
function checkRequest(response: LeagueResponse, request: ScalarRequest) {
  if (
    requestKey({ ...response, season: response.season.season }) !== requestKey(request)
  )
    throw new Error("league response does not match its requested field population");
}

const overviewRequest = (season: string): ScalarRequest => ({
  season,
  kind: "skater",
  family: "overview",
  strength: null,
});
const descriptiveRequest = (season: string): ScalarRequest => ({
  season, kind: "skater", family: "descriptive", strength: null,
});
const rawObserved = (metric: AnalysisMetric, view: AnalysisView) =>
  view === "observed" && metric.standingPolicy === "raw_only";

// only these five selectors can use observed values already carried by overview.
const metricRequest = (season: string, metric: AnalysisMetric): ScalarRequest =>
  metric.kind === "skater" && metric.family === "observed" && metric.strength === "5v5"
    ? overviewRequest(season)
    : scalarRequest(season, metric);

function requireOverview(response: LeagueResponse): SkaterOverview {
  if (
    response.kind !== "skater" ||
    response.family !== "overview" ||
    response.strength !== null
  )
    throw new Error("expected the selected skater overview");
  return response;
}

function composeLeague(
  overview: SkaterOverview,
  selectedCohort: LeagueResponse = overview,
): LeagueView {
  sameRelease(overview, selectedCohort);
  for (const row of selectedCohort.players) {
    const member = overview.players.find(
      ({ person }) => person.player_id === row.person.player_id,
    );
    if (!member || !equal(member.person, row.person))
      throw new Error(`player ${row.person.player_id}: family identity differs from its overview row`);
    if (selectedCohort.family === "descriptive") {
      const descriptive = selectedCohort.players.find(candidate => candidate.person.player_id === row.person.player_id)!;
      const usage = descriptive.result.availability === "provided"
        ? { availability: "provided", data: descriptive.result.data.reported_usage, explanation: null }
        : descriptive.result;
      const overviewUsage = member.result.availability === "provided" ? member.result.data.reported_usage : member.result;
      if (!equal(overviewUsage, usage))
        throw new Error(`player ${row.person.player_id}: reported usage differs between overview and descriptive`);
    }
  }
  if (selectedCohort.family === "descriptive") {
    for (const member of overview.players) {
      if (member.result.availability === "provided" &&
          member.result.data.reported_usage.availability === "provided" &&
          !selectedCohort.players.some(row => row.person.player_id === member.person.player_id))
        throw new Error(`player ${member.person.player_id}: available reported usage has no descriptive cohort row`);
    }
  }
  return {
    publication: overview.publication,
    available_seasons: overview.available_seasons,
    season: overview.season,
    overview,
    selectedCohort,
    players: overview.players.flatMap(({ person, result }) => {
      if (
        result.availability !== "provided" ||
        result.data.observed.availability !== "provided"
      )
        return [];
      const summary = result.data.observed.data;
      checkObservedIdentity(person, summary);
      return [summary];
    }),
  };
}

// absent seasons and goalies carry no observed skater envelope.
const observedOf = (families: PlayerFamilies) =>
  "availability" in families || families.kind !== "skater" ? null : families.observed;

type AnnualRow = PlayerResponse["history"][number];
// check the actual fields represented by overview, including unranked identity/usage
// and original envelopes. this compares projections; it computes no hockey values.
function checkOverview(row: AnnualRow, cohort: SkaterOverview, playerId: string) {
  const member = cohort.players.find(({ person }) => person.player_id === playerId);
  if (!equal(row.person, member?.person ?? null))
    throw new Error(`player ${playerId}: annual identity differs from its overview row`);
  if (!member || member.result.availability !== "provided") return;
  const families = row.families;
  if ("availability" in families || families.kind !== "skater")
    throw new Error(`player ${playerId}: provided overview has no annual skater families`);
  const data = member.result.data;
  const strengthResult = <T>(
    collection:
      | {
          readonly availability: "provided";
          readonly data: readonly { readonly strength: string; readonly result: T }[];
        }
      | {
          readonly availability: "not_computed";
          readonly data: null;
          readonly explanation: string;
        },
    strength: string,
  ) => collection.availability === "provided"
    ? collection.data.find(value => value.strength === strength)?.result
    : collection;
  const checks = [
    [data.observed, families.observed],
    [data.ledger, families.ledger],
    [data.penalties, families.penalties],
    [data.territory, families.territory],
    [data.context, families.context],
    [data.execution, strengthResult(families.execution, "5v5")],
    [data.shootiness, strengthResult(families.shootiness, "5v5")],
    [data.spatial.five_on_five, strengthResult(families.spatial, "5v5")],
    [data.spatial.pp, strengthResult(families.spatial, "pp")],
    [data.spatial.pk, strengthResult(families.spatial, "pk")],
    [
      data.reported_usage,
      families.descriptive.availability === "provided"
        ? {
            availability: "provided",
            data: families.descriptive.data.reported_usage,
            explanation: null,
          }
        : families.descriptive,
    ],
  ];
  if (checks.some(([left, right]) => !equal(left, right)))
    throw new Error(`player ${playerId}: annual overview values, status or support differ from player detail`);
}

function checkDescriptive(detail: PlayerResponse, cohort: LeagueResponse) {
  if (cohort.family !== "descriptive" || cohort.kind !== "skater" || cohort.strength !== null)
    throw new Error("expected selected descriptive cohort");
  sameRelease(detail, cohort);
  const row = detail.history.find(row => row.season.season === detail.season.season)!;
  const member = cohort.players.find(row => row.person.player_id === detail.player_id);
  if (member && !equal(detail.person, member.person) || !equal(row.person, detail.person))
    throw new Error(`player ${detail.player_id}: descriptive identity differs from player detail`);
  const families = detail.families;
  const annual = row.families;
  if ("availability" in families) {
    if (member) throw new Error("absent selected season has a descriptive cohort row");
    return cohort;
  }
  if (families.kind !== "skater" || "availability" in annual || annual.kind !== "skater")
    throw new Error("descriptive cohort requires skater annual families");
  if (!equal(families.descriptive, annual.descriptive) || !equal(families.context, annual.context) ||
      member && !equal(families.descriptive, member.result) ||
      !member && families.descriptive.availability === "provided")
    throw new Error(`player ${detail.player_id}: descriptive values, status or support differ from player detail`);
  return cohort;
}

function scalarRows(
  detail: PlayerResponse,
  metric: AnalysisMetric,
  cohorts: ReadonlyMap<string, LeagueResponse>,
): ScalarHistoryRow[] {
  return detail.history.map((row): ScalarHistoryRow => {
    const cohort = metric.standingPolicy === "raw_only" ? null : cohorts.get(requestKey(metricRequest(row.season.season, metric)))!;
    if (cohort === null) return { ...row, cohort: null };
    sameRelease({ ...detail, season: row.season }, cohort);
    const member = cohort.players.find(({ person }) => person.player_id === detail.player_id);
    const selected = selectHistoryValue(row, cohort, metric, detail.player_id);
    if (member) {
      if (!equal(row.person, member.person))
        throw new Error(`player ${detail.player_id}: annual identity differs from its cohort row`);
      const peer = selectLeagueValues(cohort, metric).find(value => value.playerId === detail.player_id);
      // an absent strength can have a family-envelope explanation instead of a
      // strength-envelope explanation; original per-field reasons remain exact.
      const agrees = selected.status === "not_computed" && peer?.status === "not_computed"
        ? equal({ ...selected, reason: null }, { ...peer, reason: null })
        : equal(selected, peer);
      if (!agrees)
        throw new Error(`player ${detail.player_id}: selected scalar or support differs from its annual cohort row`);
    } else if (selected.value !== null) {
      throw new Error(`player ${detail.player_id}: available scalar has no annual cohort row`);
    }
    return { ...row, cohort };
  });
}

function composeProfile(
  detail: PlayerResponse,
  selectedMetric: AnalysisMetric,
  cohorts: ReadonlyMap<string, LeagueResponse>,
  view: AnalysisView,
): ProfileView {
  const overviewCohorts = detail.kind === "goalie" ? [] : detail.available_seasons.flatMap(season => {
    const cohort = cohorts.get(requestKey(overviewRequest(season)));
    return cohort ? [requireOverview(cohort)] : [];
  });
  if (detail.kind === "skater" && !rawObserved(selectedMetric, view) && overviewCohorts.length !== detail.available_seasons.length)
    throw new Error("profile is missing an annual overview cohort");
  const descriptive = cohorts.get(requestKey(descriptiveRequest(detail.season.season)));
  const descriptiveCohort = descriptive ? checkDescriptive(detail, descriptive) : null;
  for (const cohort of overviewCohorts) {
    const row = detail.history.find(row => row.season.season === cohort.season.season)!;
    sameRelease({ ...detail, season: row.season }, cohort);
    checkOverview(row, cohort, detail.player_id);
  }
  const selectedOverview = overviewCohorts.find(row => row.season.season === detail.season.season);
  if (selectedOverview && descriptiveCohort) composeLeague(selectedOverview, descriptiveCohort);
  const players = selectedOverview ? composeLeague(selectedOverview).players : [];
  const observed = observedOf(detail.families);
  const player = players.find(row => row.player_id === detail.player_id);
  const summary = observed?.availability === "provided" ? observed.data : undefined;
  if (!equal(player, summary))
    throw new Error(`player ${detail.player_id}: selected observed summary differs from its overview row`);
  if (player) {
    const cohort = new Set(players.map(row => row.player_id));
    const peers = detail.deployment ? [...detail.deployment.teammates, ...detail.deployment.opponents] : [];
    if (detail.deployment === null || peers.some(peer => !cohort.has(peer.player_id)))
      throw new Error(`player ${detail.player_id}: deployment peers must resolve in the observed cohort`);
  }
  return {
    publication: detail.publication,
    available_seasons: detail.available_seasons,
    season: detail.season,
    detail,
    executionEvidence: null,
    overviewCohorts,
    view,
    selectedMetric,
    descriptiveCohort,
    scalarHistory: scalarRows(detail, selectedMetric, cohorts),
    player_id: detail.player_id,
    kind: detail.kind,
    person: detail.person,
    player,
    players,
    observedExplanation: observed?.availability === "not_computed" ? observed.explanation : null,
    games: detail.observed_games,
    deployment: detail.deployment,
    maps: null,
    history: detail.history.toReversed().map(row => {
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

const mapsQuery = (
  season: string,
  players: readonly string[],
  view: "effect" | "complete",
) => ({
  season,
  players: players.join(","),
  family: "observed",
  strength: "5v5",
  view,
});

export const loadLeague = (signal: AbortSignal, query: URLSearchParams) =>
  read(Effect.gen(function* () {
    const api = yield* client;
    const overview = yield* api.analysis.league({
      query: { season: seasonQuery(query), kind: "skater", family: "overview" },
    });
    const { table, strength } = readTableSelection(query).selection;
    const extra = table === "descriptive" ? descriptiveRequest(overview.season.season)
      : (table === "execution" || table === "shootiness") && strength !== "5v5"
      ? {
          season: overview.season.season,
          kind: "skater",
          family: table,
          strength,
        } satisfies ScalarRequest
      : null;
    const family = extra
      ? yield* api.analysis.league({ query: scalarQuery(extra) })
      : overview;
    return yield* compose(() => {
      checkSelectedSeason(overview, query);
      checkRequest(overview, overviewRequest(overview.season.season));
      if (extra) checkRequest(family, extra);
      const resolved = catalogs([overview, family]);
      return composeLeague(
        { ...requireOverview(overview), ...resolved },
        { ...family, ...resolved },
      );
    });
  }), signal);

// one exact scalar population per year; observed selectors reuse the overview.
export const loadProfile = (
  playerId: string,
  signal: AbortSignal,
  query: URLSearchParams,
) =>
  read(Effect.gen(function* () {
    const api = yield* client;
    const detail = yield* api.analysis.player({
      params: { playerId },
      query: { season: seasonQuery(query) },
    });
    yield* compose(() => {
      checkSelectedSeason(detail, query);
      if (detail.player_id !== playerId)
        throw new Error("player detail does not match its requested player");
    });
    const view = detail.kind === "goalie" ? "observed" : readView(query).view;
    const metric = readMetric(query, detail.kind, view).metric;
    const requests = [...new Map(
      [
        ...detail.available_seasons.flatMap(season => [
          ...(detail.kind === "skater" && (!rawObserved(metric, view) || season === detail.season.season) ? [overviewRequest(season)] : []),
          ...(metric.standingPolicy === "raw_only" ? [] : [metricRequest(season, metric)]),
        ]),
        ...(detail.kind === "skater" && (view === "observed" || metric.standingPolicy === "raw_only") ? [descriptiveRequest(detail.season.season)] : []),
      ].map(request => [requestKey(request), request]),
    ).values()];
    const responses = yield* Effect.all(
      requests.map(request => api.analysis.league({ query: scalarQuery(request) })),
      { concurrency: "unbounded" },
    );
    let profile = yield* compose(() => {
      responses.forEach((response, index) => {
        samePublication(detail, response);
        checkRequest(response, requests[index]);
      });
      const resolved = catalogs([detail, ...responses]);
      const cohorts = new Map(responses.map((response, index) => [
        requestKey(requests[index]),
        { ...response, ...resolved },
      ]));
      return composeProfile({ ...detail, ...resolved }, metric, cohorts, view);
    });
      if (metric.publicationFamily === "execution") {
        const evidence = yield* api.analysis.evidence({
          params: { playerId },
          query: {
            season: profile.season.season,
            family: "execution",
            strength: metric.selectionStrength!,
          },
        });
        profile = yield* compose((): ProfileView => {
          sameRelease(detail, evidence);
          if (
            evidence.family !== "execution" ||
            evidence.selection.player_id !== playerId ||
            evidence.selection.season !== profile.season.season ||
            evidence.selection.strength !== metric.selectionStrength
          )
            throw new Error(
              "execution evidence differs from the selected player, season or strength",
            );
          catalogs([detail, ...responses, evidence]);
          return { ...profile, executionEvidence: evidence };
        });
      }
      if (view !== "observed" || !profile.player) return profile;
    const mapMode = mapView(query);
    const maps = yield* api.analysis.maps({
      query: mapsQuery(profile.season.season, [playerId], mapMode),
    });
    return yield* compose((): ProfileView => {
      catalogs([detail, ...responses, maps]);
      return { ...profile, maps: observedMaps(maps, profile, [playerId], mapMode) };
    });
  }), signal);

// the picker uses every selected-year identity. two valid selections share all
// three annual overview and selected-field reads, including request-local reuse.
export const loadComparison = (signal: AbortSignal, query: URLSearchParams) =>
  read(Effect.gen(function* () {
    const api = yield* client;
    const initial = yield* api.analysis.league({
      query: { season: seasonQuery(query), kind: "skater", family: "overview" },
    });
    const overview = yield* compose(() => {
      checkSelectedSeason(initial, query);
      return requireOverview(initial);
    });
    const view = readView(query).view;
    const metric = readMetric(query, "skater", view).metric;
    const persons = overview.players.map(row => row.person);
    const [first, second] = ["a", "b"].map(key => {
      const values = query.getAll(key);
      return values.length === 1
        ? persons.find(row => row.player_id === values[0])
        : undefined;
    });
    const pair = first && second && first.player_id !== second.player_id
      ? [first, second] as const
      : null;
    const details = pair ? yield* Effect.all(
      pair.map(person => api.analysis.player({
        params: { playerId: person.player_id },
        query: { season: overview.season.season },
      })),
      { concurrency: "unbounded" },
    ) : [];
    const requests = [...new Map(
      [
        ...(pair
          ? overview.available_seasons.flatMap(season => [
              ...(!rawObserved(metric, view) || season === overview.season.season ? [overviewRequest(season)] : []),
              ...(metric.standingPolicy === "raw_only" ? [] : [metricRequest(season, metric)]),
            ])
          : [metricRequest(overview.season.season, metric)]),
        ...(view === "observed" || metric.standingPolicy === "raw_only" ? [descriptiveRequest(overview.season.season)] : []),
      ].map(request => [requestKey(request), request]),
    ).values()].filter(
      request => requestKey(request) !== requestKey(overviewRequest(overview.season.season)),
    );
    const responses = yield* Effect.all(
      requests.map(request => api.analysis.league({ query: scalarQuery(request) })),
      { concurrency: "unbounded" },
    );
    const comparison = yield* compose((): ComparisonView => {
      checkRequest(overview, overviewRequest(overview.season.season));
      details.forEach((detail, index) => {
        sameRelease(overview, detail);
        if (
          detail.player_id !== pair![index].player_id ||
          detail.kind !== "skater" ||
          !equal(detail.person, pair![index])
        )
          throw new Error("comparison detail does not match its selected annual identity");
      });
      responses.forEach((response, index) => {
        samePublication(overview, response);
        checkRequest(response, requests[index]);
      });
      const resolved = catalogs([overview, ...details, ...responses]);
      const cohorts = new Map([
        [
          requestKey(overviewRequest(overview.season.season)),
          { ...overview, ...resolved },
        ] as const,
        ...responses.map((response, index) => [
          requestKey(requests[index]), { ...response, ...resolved },
        ] as const),
      ]);
      const selectedOverview = requireOverview(
        cohorts.get(requestKey(overviewRequest(overview.season.season)))!,
      );
      const scalarCohort = cohorts.get(requestKey(metricRequest(overview.season.season, metric)))!;
      const league = composeLeague(selectedOverview, scalarCohort);
      const profiles: ComparisonView["profiles"] = pair ? [
        composeProfile({ ...details[0], ...resolved }, metric, cohorts, view),
        composeProfile({ ...details[1], ...resolved }, metric, cohorts, view),
      ] : null;
      return {
        ...league,
        persons,
        selectedMetric: metric,
        scalarCohort,
        pair,
        profiles,
        overviewCohorts: pair ? overview.available_seasons.flatMap(season => {
          const cohort = cohorts.get(requestKey(overviewRequest(season)));
          return cohort ? [requireOverview(cohort)] : [];
        }) : [selectedOverview],
        maps: null,
      };
    });
    if (!pair || view !== "observed") return comparison;
    const mapMode = mapView(query);
    const ids = pair.map(person => person.player_id);
    const maps = yield* api.analysis.maps({
      query: mapsQuery(overview.season.season, ids, mapMode),
    });
    return yield* compose((): ComparisonView => {
      catalogs([overview, ...details, ...responses, maps]);
      return { ...comparison, maps: observedMaps(maps, comparison, ids, mapMode) };
    });
  }), signal);
