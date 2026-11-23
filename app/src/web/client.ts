import * as Effect from "effect/Effect";
import * as Result from "effect/Result";
import * as FetchHttpClient from "effect/http/FetchHttpClient";
import * as HttpApiClient from "effect/http-api/HttpApiClient";
import * as Schema from "effect/Schema";
import { HockeyId } from "../shared/observed";
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
  close,
  ExecutionSummaryResult,
  GoalieSummaryResult,
  PenaltySummaryResult,
  ShootinessSummaryResult,
  TerritorySummaryResult,
  projectOverviewResult,
  PlayerAnalysisApi,
  type LeagueResponse,
  type EvidenceResponse,
  type MapsResponse,
  type Person,
  type PlayerFamilies,
  type PlayerResponse,
} from "../shared/player-analysis";
import {
  readKind,
  readGoalieSelection,
  readMapMode,
  readMetric,
  readTableSelection,
  readView,
  analyticalMapSelection,
  type AnalysisView,
  type GoalieSelection,
} from "./explorer";
import {
  checkObservedIdentity,
  analysisMetric,
  overviewEvidenceSelection,
  scalarDatum,
  type AnalysisDatum,
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
export type GoalieOverview = Extract<LeagueResponse, { kind: "goalie"; family: "overview" }>;
export type Overview = SkaterOverview | GoalieOverview;
export type GoalieEvidence = Extract<EvidenceResponse, { family: "goalie_evidence" }>;
export type GoalieDetail = Extract<EvidenceResponse, { family: "goalie" }>;
export type LeagueView = Release & {
  readonly players: readonly PlayerSummary[];
  readonly selectedCohort: LeagueResponse;
} & (
  | { readonly kind: "skater"; readonly overview: SkaterOverview }
  | { readonly kind: "goalie"; readonly overview: GoalieOverview }
);
export type ObservedMaps = {
  readonly selection: SpatialSelection;
  readonly scale: Extract<MapsResponse, { family: "observed" }>["scale"];
};
export type ExecutionEvidence = Extract<EvidenceResponse, { family: "execution" }>;
export type SpatialEvidence = Extract<EvidenceResponse, { family: "spatial" }>;
export type LedgerEvidence = Extract<EvidenceResponse, { family: "ledger" }>;
export type MicrostatsEvidence = Extract<EvidenceResponse, { family: "microstats" }>;
export type MicrostatsCohort = Extract<LeagueResponse, { family: "microstats" }>;
export type ProfileView = Release & {
  readonly goalieOverviewCohorts: readonly GoalieOverview[];
  readonly goalieSelection: GoalieSelection | null;
  readonly goalieEvidence: GoalieEvidence | null;
  readonly goalieDetail: GoalieDetail | null;
  readonly goalieMaps: readonly MapsResponse[];
  readonly executionEvidence: ExecutionEvidence | null;
  readonly spatialEvidence: SpatialEvidence | null;
  readonly coreMaps: readonly MapsResponse[];
  readonly selectedMap: MapsResponse | null;
  readonly ledgerEvidence: LedgerEvidence | null;
  readonly microstatsEvidence: MicrostatsEvidence | null;
  readonly microstatsCohort: MicrostatsCohort | null;
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
  readonly coreMaps: readonly MapsResponse[];
  readonly selectedMetric: AnalysisMetric;
  readonly scalarCohort: LeagueResponse;
  readonly persons: readonly Person[];
  readonly pair: readonly [Person, Person] | null;
  readonly profiles: readonly [ProfileView, ProfileView] | null;
  readonly overviewCohorts: readonly SkaterOverview[];
  readonly maps: ObservedMaps | null;
  readonly selectionError: string | null;
};

const client = HttpApiClient.make(PlayerAnalysisApi).pipe(
  Effect.provide(FetchHttpClient.layer),
);
const headers = { "content-type": "application/json" };

async function read<A, E>(
  effect: Effect.Effect<A, E>,
  signal?: AbortSignal,
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

export type EvidenceRelease = Release & Envelope;

// hydrate only the requested rows and preserve their click-time order. the
// originating scalar is the contract even when running after navigation.
export function loadLeagueEvidence(release: EvidenceRelease, datums: readonly AnalysisDatum[]) {
  const requests = new Map<string, ScalarRequest>();
  const metricRequests = new Map<AnalysisMetric, string>();
  for (const datum of datums) {
    if (datum.evidence.state === "loaded") continue;
    const selection = overviewEvidenceSelection(datum.metric);
    if (!selection || datum.season !== release.season.season)
      throw new Error("overview evidence differs from the requested season or quantity");
    const request = { ...selection, season: datum.season };
    const key = requestKey(request);
    requests.set(key, request);
    metricRequests.set(datum.metric, key);
  }
  if (requests.size === 0) return Promise.resolve(datums);

  return read(Effect.gen(function* () {
    const api = yield* client;
    const responses = yield* Effect.forEach(requests, ([key, request]) =>
      api.analysis.league({ query: scalarQuery(request) }).pipe(
        Effect.map(response => [key, response] as const),
      ), { concurrency: "unbounded" });
    return yield* compose(() => {
      const byRequest = new Map(responses);
      for (const [key, response] of responses) {
        sameRelease(release, response);
        checkRequest(response, requests.get(key)!);
      }
      catalogs([release, ...byRequest.values()]);
      const lookup = new Map([...metricRequests].map(([metric, key]) => [
        metric,
        new Map(selectLeagueValues(byRequest.get(key)!, metric).map(datum => [datum.playerId, datum])),
      ]));
      return datums.map(datum => {
        if (datum.evidence.state === "loaded") return datum;
        const full = lookup.get(datum.metric)?.get(datum.playerId);
        if (!full || full.evidence.state !== "loaded" || !equal(scalarDatum(datum), scalarDatum(full)))
          throw new Error(`player ${datum.playerId}: full family evidence differs from its overview quantity`);
        return { ...datum, evidence: full.evidence };
      });
    });
  }));
}

const overviewRequest = (season: string, kind: "skater" | "goalie" = "skater"): ScalarRequest => ({
  season,
  kind,
  family: "overview",
  strength: null,
});
const descriptiveRequest = (season: string): ScalarRequest => ({
  season, kind: "skater", family: "descriptive", strength: null,
});
const rawObserved = (metric: AnalysisMetric, view: AnalysisView) =>
  view === "observed" && metric.standingPolicy === "raw_only";
const needsOverview = (season: string, selectedSeason: string, metric: AnalysisMetric, view: AnalysisView) =>
  season === selectedSeason || (view === "microstats" ? metric.family === "overview" : !rawObserved(metric, view));
const microstatsRequest = (season: string): ScalarRequest => ({
  season, kind: "skater", family: "microstats", strength: null,
});

// only these five selectors can use observed values already carried by overview.
const metricRequest = (season: string, metric: AnalysisMetric): ScalarRequest =>
  metric.kind === "skater" && metric.family === "observed" && metric.strength === "5v5"
    ? overviewRequest(season)
    : scalarRequest(season, metric);

function requireSkaterOverview(response: LeagueResponse): SkaterOverview {
  if (
    response.kind !== "skater" ||
    response.family !== "overview" ||
    response.strength !== null
  )
    throw new Error("expected the selected skater overview");
  return response;
}

function requireOverview(response: LeagueResponse): Overview {
  if (response.family !== "overview" || response.strength !== null)
    throw new Error("expected the selected player-kind overview");
  return response;
}

function composeLeague(
  overview: Overview,
  selectedCohort: LeagueResponse = overview,
): LeagueView {
  sameRelease(overview, selectedCohort);
  for (const row of selectedCohort.players) {
    const member = overview.players.find(
      ({ person }) => person.player_id === row.person.player_id,
    );
    if (!member || !equal(member.person, row.person))
      throw new Error(`player ${row.person.player_id}: family identity differs from its overview row`);
    if (selectedCohort.family === "descriptive" && overview.kind === "skater") {
      const descriptive = selectedCohort.players.find(candidate => candidate.person.player_id === row.person.player_id)!;
      const usage = descriptive.result.availability === "provided"
        ? { availability: "provided", data: descriptive.result.data.reported_usage, explanation: null }
        : descriptive.result;
      const overviewUsage = member.result.availability === "provided" ? member.result.data.reported_usage : member.result;
      if (!equal(overviewUsage, usage))
        throw new Error(`player ${row.person.player_id}: reported usage differs between overview and descriptive`);
    }
  }
  if (selectedCohort.family === "descriptive" && overview.kind === "skater") {
    for (const member of overview.players) {
      if (member.result.availability === "provided" &&
          member.result.data.reported_usage.availability === "provided" &&
          !selectedCohort.players.some(row => row.person.player_id === member.person.player_id))
        throw new Error(`player ${member.person.player_id}: available reported usage has no descriptive cohort row`);
    }
  }
  const league = {
    publication: overview.publication,
    available_seasons: overview.available_seasons,
    season: overview.season,
    selectedCohort,
    players: overview.kind === "goalie" ? [] : overview.players.flatMap(({ person, result }) => {
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
  return overview.kind === "goalie"
    ? { ...league, kind: "goalie", overview }
    : { ...league, kind: "skater", overview };
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
  if (!member) return;
  const families = row.families;
  if (member.result.availability !== "provided" || "availability" in families || families.kind !== "skater")
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
  ) => {
    if (collection.availability !== "provided") return collection;
    const value = collection.data.find(value => value.strength === strength);
    if (!value) throw new Error(`player ${playerId}: annual family lacks strength ${strength}`);
    return value.result;
  };
  const checks = [
    [data.observed, families.observed],
    [data.ledger, families.ledger],
    [data.penalties, projectOverviewResult(PenaltySummaryResult, families.penalties)],
    [data.territory, projectOverviewResult(TerritorySummaryResult, families.territory)],
    [data.context, families.context],
    [data.execution, projectOverviewResult(ExecutionSummaryResult, strengthResult(families.execution, "5v5"))],
    [data.shootiness, projectOverviewResult(ShootinessSummaryResult, strengthResult(families.shootiness, "5v5"))],
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

function checkMicrostats(row: AnnualRow, cohort: LeagueResponse, playerId: string): MicrostatsCohort {
  if (cohort.family !== "microstats" || cohort.kind !== "skater" || cohort.strength !== null)
    throw new Error("expected a microstats cohort");
  if (!equal(row.season, cohort.season))
    throw new Error("microstats cohort differs from its annual season evidence");
  const member = cohort.players.find(({ person }) => person.player_id === playerId);
  const families = row.families;
  if ("availability" in families) {
    if (member) throw new Error("absent season has a microstats cohort row");
    return cohort;
  }
  if (families.kind !== "skater")
    throw new Error("microstats cohort requires annual skater families");
  if (!member || !equal(row.person, member.person) || !equal(families.microstats, member.result))
    throw new Error(`player ${playerId}: complete microstats identity, body, status or support differs from its cohort row`);
  return cohort;
}

function withMicrostatsEvidence(profile: ProfileView, evidence: EvidenceResponse): ProfileView {
  sameRelease(profile.detail, evidence);
  if (evidence.family !== "microstats" ||
      evidence.selection.player_id !== profile.player_id ||
      evidence.selection.season !== profile.season.season ||
      evidence.selection.strength !== null || evidence.selection.population !== null ||
      evidence.selection.type !== null || evidence.selection.outcome !== null ||
      evidence.selection.shot_type !== null || evidence.selection.blocked_contacts)
    throw new Error("microstats evidence differs from the selected player, season or population");
  catalogs([profile.detail, evidence]);
  const families = profile.detail.families;
  if (!("availability" in families) && families.kind !== "skater")
    throw new Error("microstats evidence requires skater families");
  const expected = "availability" in families
    ? { availability: families.availability, data: families.data, explanation: families.explanation }
    : families.microstats;
  if (!equal(expected, evidence.result))
    throw new Error("microstats evidence body, status or support differs from player detail");
  return { ...profile, microstatsEvidence: evidence };
}

function withLedgerEvidence(profile: ProfileView, evidence: EvidenceResponse): ProfileView {
  sameRelease(profile.detail, evidence);
  if (evidence.family !== "ledger" ||
      evidence.selection.player_id !== profile.player_id ||
      evidence.selection.season !== profile.season.season ||
      evidence.selection.strength !== null || evidence.selection.population !== null ||
      evidence.selection.type !== null || evidence.selection.outcome !== null ||
      evidence.selection.shot_type !== null || evidence.selection.blocked_contacts)
    throw new Error("ledger evidence differs from the selected player or season");
  catalogs([profile.detail, evidence]);
  const families = profile.detail.families;
  if (!("availability" in families) && families.kind !== "skater")
    throw new Error("ledger evidence requires skater families");
  const expected = "availability" in families ? families : families.ledger;
  const ledger = evidence.result.availability === "provided" ? evidence.result.data.ledger : evidence.result;
  if (ledger.availability !== expected.availability || ledger.explanation !== expected.explanation)
    throw new Error("ledger evidence status differs from its annual summary");
  if (ledger.availability === "provided" && expected.availability === "provided") {
    if (evidence.result.availability !== "provided" || evidence.result.data.reference.availability !== "provided")
      throw new Error("provided ledger evidence requires its annual reference");
    const reference = evidence.result.data.reference.data;
    const { evidence: detail, ...scalars } = ledger.data;
    const { depth_reference_coverage: coverage, depth_position_group: group,
      annual_reference_id: referenceId, ...expectedScalars } = expected.data;
    const position = group === "unknown" ? null : reference.positions[group];
    const groups = reference.groups.filter(entry => entry.position === group);
    const completeGroups = groups.filter(entry => entry.status === "complete").length;
    const detailCoverage = position === null ? null : {
      available: position.available, complete_groups: completeGroups,
      excluded_groups: groups.length - completeGroups,
      member_count: position.member_count, total_seconds: position.total_seconds,
    };
    if (referenceId !== detail.annual_reference_id || referenceId !== reference.reference_id ||
        group !== detail.depth_position.group || !equal(coverage, detailCoverage) ||
        !equal(expectedScalars, scalars))
      throw new Error("ledger evidence scalars or reference identity differ from its annual summary");
  }
  return { ...profile, ledgerEvidence: evidence };
}

const selectedLedgerDetail = (query: URLSearchParams, metric: AnalysisMetric) =>
  metric.publicationFamily === "ledger" && query.getAll("metric").length === 1 &&
  query.get("metric") === metric.id;

function withExecutionEvidence(profile: ProfileView, evidence: EvidenceResponse): ProfileView {
  sameRelease(profile.detail, evidence);
  const strength = profile.selectedMetric.selectionStrength!;
  if (evidence.family !== "execution" || evidence.selection.player_id !== profile.player_id ||
      evidence.selection.season !== profile.season.season || evidence.selection.strength !== strength)
    throw new Error("execution evidence differs from the selected player, season or strength");
  catalogs([profile.detail, evidence]);
  const families = profile.detail.families;
  const expected = "availability" in families ? families
    : families.kind === "skater" && families.execution.availability === "provided"
      ? families.execution.data.find(row => row.strength === strength)?.result : families.kind === "skater" ? families.execution : null;
  const availability = "availability" in families ? families.availability
    : families.kind === "skater" ? families.execution.availability : null;
  if (evidence.result.availability !== availability ||
      evidence.result.availability === "provided" && !equal(evidence.result.data.summary, expected))
    throw new Error("execution evidence summary differs from its selected annual result");
  return { ...profile, executionEvidence: evidence };
}

const coreMapSelections = [
  { family: "offense_attempts", strength: "5v5" },
  { family: "offense_attempts", strength: "pp" },
  { family: "defense_attempts", strength: "5v5" },
  { family: "defense_attempts", strength: "pk" },
] as const;

function loadAnalytical(profiles: readonly ProfileView[], query: URLSearchParams) {
  return Effect.gen(function* () {
    const api = yield* client;
    const first = profiles[0];
    const players = profiles.map(profile => profile.player_id);
    const season = first.season.season;
    const selected = analyticalMapSelection(first.selectedMetric);
    const selectedView = first.selectedMetric.publicationFamily === "spatial" ? mapView(query) : "effect";
    const requests = coreMapSelections.map(selection => ({ ...selection, view: "effect" as "effect" | "complete" }));
    const selectedIndex = selected ? requests.findIndex(request => equal(request, { ...selected, view: selectedView })) : -1;
    const mapRequests = selected && selectedIndex === -1 ? [...requests, { ...selected, view: selectedView }] : requests;
    const maps = yield* Effect.all(mapRequests.map(selection => api.analysis.maps({
      query: { season, players: players.join(","), ...selection },
    })), { concurrency: "unbounded" });
    const spatial = first.selectedMetric.publicationFamily === "spatial";
    const strength = spatial ? first.selectedMetric.strength : null;
    const evidence = spatial ? yield* Effect.all(profiles.map(profile => api.analysis.evidence({
      params: { playerId: profile.player_id }, query: { season, family: "spatial", strength: strength! },
    })), { concurrency: "unbounded" }) : [];
    return yield* compose(() => {
      const resolved = catalogs([...profiles.map(profile => profile.detail), ...maps, ...evidence]);
      maps.forEach((response, index) => {
        const request = mapRequests[index];
        sameRelease(first.detail, response);
        if (response.family !== request.family || !equal(response.selection.players, players) ||
            response.selection.strength !== request.strength || response.selection.view !== request.view)
          throw new Error("analytical map response differs from its requested selection");
        const metricId = response.family.startsWith("offense_") || response.family.startsWith("defense_")
          ? `spatial.${request.strength}.${response.family}_per60`
          : response.family === "finishing" ? `execution.${request.strength}.finishing_goals_per100_attempts`
          : response.family === "setting" ? `execution.${request.strength}.setting_goals_per100_assisted_opportunities`
          : `territory.${response.family}_goals_per_basket`;
        const metric = analysisMetric(metricId);
        if (!metric) throw new Error("analytical map has no matching finite scalar");
        if (response.scale.maximum < 0 ||
            response.scale.minimum !== (request.view === "complete" ? 0 : -response.scale.maximum) ||
            response.scale.unit !== `${metric.unit}_per100sqft`)
          throw new Error("analytical map scale differs from its selected view or dimensional density");
        response.players.forEach((row, playerIndex) => {
          const profile = profiles[playerIndex];
          if ((row.result.availability === "absent") !== (profile.person === null))
            throw new Error("analytical map availability differs from its selected annual identity");
          if (row.result.availability !== "provided" || row.result.data.integrated_value === null) return;
          const annual = profile.detail.history.find(row => row.season.season === season)!;
          const datum = selectHistoryValue(annual, profile.detail, metric, profile.player_id);
          const value = request.view === "complete" ? datum.spatial_detail?.complete.value : datum.value;
          if (value === null || value === undefined || !close(row.result.data.integrated_value, value) ||
              row.result.data.method_id !== datum.methods[0]?.method_id || !equal(row.result.data.support, datum.support))
            throw new Error("analytical map integral, method or support differs from its selected annual scalar");
        });
      });
      if (maps[0].scale.maximum !== maps[2].scale.maximum || maps[1].scale.maximum !== maps[3].scale.maximum)
        throw new Error("paired analytical core maps must share their published extent");
      const coreMaps = maps.slice(0, 4).map(response => ({ ...response, ...resolved }));
      return profiles.map((profile, index): ProfileView => {
        const spatialEvidence = evidence[index] ?? null;
        if (spatialEvidence) {
          sameRelease(profile.detail, spatialEvidence);
          if (spatialEvidence.family !== "spatial" || spatialEvidence.selection.player_id !== profile.player_id ||
              spatialEvidence.selection.strength !== strength)
            throw new Error("spatial evidence differs from its selected player or strength");
          const families = profile.detail.families;
          const summary = "availability" in families ? families
            : families.kind === "skater" && families.spatial.availability === "provided"
              ? families.spatial.data.find(row => row.strength === strength)?.result : families.kind === "skater" ? families.spatial : null;
          const availability = "availability" in families ? families.availability
            : families.kind === "skater" ? families.spatial.availability : null;
          if (spatialEvidence.result.availability !== availability ||
              spatialEvidence.result.availability === "provided" && !equal(summary, spatialEvidence.result.data.summary))
            throw new Error("spatial evidence summary differs from its selected annual result");
        }
        return {
          ...profile,
          detail: { ...profile.detail, ...resolved },
          coreMaps,
          selectedMap: selected ? { ...maps[selectedIndex === -1 ? 4 : selectedIndex], ...resolved } : null,
          spatialEvidence: spatialEvidence?.family === "spatial" ? { ...spatialEvidence, ...resolved } : null,
        };
      });
    });
  });
}

function loadGoalie(profiles: readonly ProfileView[], query: URLSearchParams) {
  return Effect.gen(function* () {
    const api = yield* client;
    const first = profiles[0];
    const season = first.season.season;
    const players = profiles.map(profile => profile.player_id);
    const selection = readGoalieSelection(query).selection;
    const { coreStrength, evidenceStrength, population, evidenceView } = selection;
    const mapRequests = [
      { family: "goalie_stopping", strength: coreStrength, view: "effect" },
      ...(["all", "wrist_snap", "slap", "tip", "backhand", "other"] as const).map(type => ({
        family: "goalie_evidence", strength: evidenceStrength,
        view: evidenceView === "mass" ? "evidence_mass" : "evidence_ratio", population, type,
      })),
      ...(evidenceStrength !== "covered_all" && evidenceStrength !== coreStrength
        ? [{ family: "goalie_stopping", strength: evidenceStrength, view: "effect" }] : []),
    ];
    const maps = yield* Effect.all(mapRequests.map(request => api.analysis.maps({
      query: { season, players: players.join(","), ...request },
    })), { concurrency: "unbounded" });
    const actual = yield* Effect.all(profiles.map(profile => api.analysis.evidence({
      params: { playerId: profile.player_id },
      query: { season, family: "goalie_evidence", strength: evidenceStrength, population, type: "all" },
    })), { concurrency: "unbounded" });
    const modeled = evidenceStrength === "covered_all" ? [] : yield* Effect.all(profiles.map(profile => api.analysis.evidence({
      params: { playerId: profile.player_id },
      query: { season, family: "goalie", strength: evidenceStrength },
    })), { concurrency: "unbounded" });
    return yield* compose(() => {
      const resolved = catalogs([...profiles.map(profile => profile.detail), ...maps, ...actual, ...modeled]);
      maps.forEach((response, index) => {
        sameRelease(first.detail, response);
        const request = mapRequests[index];
        if (response.family === "observed" || response.family !== request.family ||
            !equal(response.selection.players, players) || response.selection.strength !== request.strength ||
            response.selection.view !== request.view ||
            response.selection.population !== ("population" in request ? request.population : null) ||
            response.selection.type !== ("type" in request ? request.type : null))
          throw new Error("goalie map differs from its requested identity or selection");
        const unit = response.family === "goalie_stopping" ? "goals_per100_on_net_per100sqft"
          : evidenceView === "mass" ? "goals_per100sqft" : "percent";
        if (response.scale.unit !== unit || response.scale.minimum !== -response.scale.maximum)
          throw new Error("goalie map scale differs from its selected units");
        response.players.forEach((row, playerIndex) => {
          const profile = profiles[playerIndex];
          if ((row.result.availability === "absent") !== (profile.person === null))
            throw new Error("goalie map availability differs from annual identity");
        });
        if (response.family !== "goalie_stopping") return;
        response.players.forEach((row, playerIndex) => {
          const profile = profiles[playerIndex];
          if (row.result.availability !== "provided") return;
          const annual = profile.detail.history.find(row => row.season.season === season)!;
          const families = annual.families;
          const result = !("availability" in families) && families.kind === "goalie" && families.goalie.availability === "provided"
            ? families.goalie.data.find(row => row.strength === request.strength)?.result : null;
          if (result?.availability !== "provided")
            throw new Error("goalie stopping map has no matching annual estimate");
          const map = row.result.data;
          const estimate = result.data.stopping_goals_per100_on_net;
          const agrees = map.integrated_value === null || estimate.value === null
            ? map.integrated_value === estimate.value : close(map.integrated_value, estimate.value);
          if (!agrees || map.method_id !== result.data.method_id ||
              !equal(map.support, result.data.support.stopping_goals_per100_on_net) ||
              map.unavailable_reason !== estimate.unavailable_reason || !equal(map.reason_detail, estimate.reason_detail))
            throw new Error("goalie stopping map value, missingness or support differs from its annual estimate");
        });
      });
      return profiles.map((profile, index): ProfileView => {
        const evidence = actual[index];
        sameRelease(profile.detail, evidence);
        if (evidence.family !== "goalie_evidence" || evidence.selection.player_id !== profile.player_id ||
            evidence.selection.strength !== evidenceStrength || evidence.selection.population !== population || evidence.selection.type !== "all")
          throw new Error("goalie evidence differs from its selected identity or population");
        const families = profile.detail.families;
        const expectedObserved = "availability" in families ? families
          : families.kind === "goalie" && families.goalie_observed.availability === "provided"
            ? families.goalie_observed.data.find(row => row.strength === evidenceStrength)?.result
            : families.kind === "goalie" ? families.goalie_observed : null;
        if (evidence.result.availability === "provided") {
          const observed = evidence.result.data.observed;
          if (observed.availability === "provided") {
            const { games: _games, ...summary } = observed.data;
            if (expectedObserved?.availability !== "provided" || !equal(summary, expectedObserved.data))
              throw new Error("goalie recorded detail differs from its annual source/paired summary");
          } else if (expectedObserved?.availability === "provided") {
            throw new Error("goalie recorded detail withholds a provided annual summary");
          }
          const allMap = maps.find(map => map.family === "goalie_evidence" && map.selection.type === "all");
          const selectedMap = allMap?.family === "goalie_evidence" ? allMap.players.find(row => row.player_id === profile.player_id)?.result : null;
          if (!equal(selectedMap, evidence.result.data.map))
            throw new Error("goalie actual map differs between the selected map and evidence endpoints");
        } else if ((evidence.result.availability === "absent") !== (profile.person === null)) {
          throw new Error("goalie actual evidence availability differs from annual identity");
        }
        const detail = modeled[index] ?? null;
        if (detail) {
          sameRelease(profile.detail, detail);
          if (detail.family !== "goalie" || detail.selection.player_id !== profile.player_id || detail.selection.strength !== evidenceStrength)
            throw new Error("goalie model detail differs from its selected identity or strength");
          const families = profile.detail.families;
          const expected = "availability" in families ? families
            : families.kind === "goalie" && families.goalie.availability === "provided"
              ? families.goalie.data.find(row => row.strength === evidenceStrength)?.result : families.kind === "goalie" ? families.goalie : null;
          if (detail.result.availability === "provided" && !equal(detail.result.data.summary, expected))
            throw new Error("goalie model detail differs from its annual estimate or support");
        }
        return {
          ...profile, detail: { ...profile.detail, ...resolved }, goalieSelection: selection,
          goalieMaps: maps.map(map => ({ ...map, ...resolved })),
          goalieEvidence: { ...evidence, ...resolved },
          goalieDetail: detail?.family === "goalie" ? { ...detail, ...resolved } : null,
        };
      });
    });
  });
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
    if (metric.family === "microstats") checkMicrostats(row, cohort, detail.player_id);
    const member = cohort.players.find(({ person }) => person.player_id === detail.player_id);
    const selected = selectHistoryValue(row, cohort, metric, detail.player_id);
    if (member) {
      if (!equal(row.person, member.person))
        throw new Error(`player ${detail.player_id}: annual identity differs from its cohort row`);
      const peer = selectLeagueValues(cohort, metric).find(value => value.playerId === detail.player_id);
      // an absent strength can have a family-envelope explanation instead of a
      // strength-envelope explanation; original per-field reasons remain exact.
      const summary = selected.evidence.state === "not_loaded" || peer?.evidence.state === "not_loaded";
      const focal = summary ? scalarDatum(selected) : selected;
      const ranked = summary && peer ? scalarDatum(peer) : peer;
      const agrees = focal.status === "not_computed" && ranked?.status === "not_computed"
        ? equal({ ...focal, reason: null }, { ...ranked, reason: null })
        : equal(focal, ranked);
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
  const goalieOverviewCohorts = detail.kind === "goalie" ? detail.available_seasons.map(season => {
    const cohort = cohorts.get(requestKey(overviewRequest(season, "goalie")));
    if (!cohort || cohort.family !== "overview" || cohort.kind !== "goalie") throw new Error("goalie profile is missing an annual overview cohort");
    return cohort;
  }) : [];
  for (const cohort of goalieOverviewCohorts) {
    const row = detail.history.find(row => row.season.season === cohort.season.season)!;
    sameRelease({ ...detail, season: row.season }, cohort);
    const member = cohort.players.find(member => member.person.player_id === detail.player_id);
    if (!equal(row.person, member?.person ?? null)) throw new Error("goalie annual identity differs from its cohort row");
    if (member) {
      const families = row.families;
      if (member.result.availability !== "provided" || "availability" in families || families.kind !== "goalie")
        throw new Error("goalie overview has no annual goalie families");
      for (const strength of ["ev", "pk"] as const) {
        const modeled = families.goalie.availability === "provided" ? families.goalie.data.find(row => row.strength === strength)?.result : families.goalie;
        const observed = families.goalie_observed.availability === "provided" ? families.goalie_observed.data.find(row => row.strength === strength)?.result : families.goalie_observed;
        if (!equal(projectOverviewResult(GoalieSummaryResult, modeled), member.result.data.goalie[strength]) ||
            !equal(observed, member.result.data.observed[strength]))
          throw new Error("goalie annual estimate, status or support differs from its overview");
      }
    }
  }
  const overviewCohorts = detail.kind === "goalie" ? [] : detail.available_seasons.flatMap(season => {
    const cohort = cohorts.get(requestKey(overviewRequest(season)));
    return cohort ? [requireSkaterOverview(cohort)] : [];
  });
  const requiredOverviews = detail.kind === "skater"
    ? detail.available_seasons.filter(season => needsOverview(season, detail.season.season, selectedMetric, view))
    : [];
  if (requiredOverviews.some(season => !overviewCohorts.some(cohort => cohort.season.season === season)))
    throw new Error("profile is missing a required annual overview cohort");
  const selectedAnnual = detail.history.find(row => row.season.season === detail.season.season)!;
  const microstats = cohorts.get(requestKey(microstatsRequest(detail.season.season)));
  const microstatsCohort = microstats ? checkMicrostats(selectedAnnual, microstats, detail.player_id) : null;
  if (view === "microstats" && !microstatsCohort)
    throw new Error("microstats view is missing its selected-year microstats cohort");
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
    goalieOverviewCohorts,
    goalieSelection: null,
    goalieEvidence: null,
    goalieDetail: null,
    goalieMaps: [],
    executionEvidence: null,
    spatialEvidence: null,
    coreMaps: [],
    selectedMap: null,
    ledgerEvidence: null,
    microstatsEvidence: null,
    microstatsCohort,
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
      query: { season: seasonQuery(query), kind: readKind(query).kind, family: "overview" },
    });
    const { table, strength } = readTableSelection(query).selection;
    const extra = table === "descriptive" ? descriptiveRequest(overview.season.season)
      : (table === "execution" || table === "shootiness") && strength !== "5v5" || table === "spatial"
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
      checkRequest(overview, overviewRequest(overview.season.season, overview.kind));
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
    const view = readView(query, detail.kind).view;
    const metric = readMetric(query, detail.kind, view).metric;
    const requests = [...new Map(
      [
        ...detail.available_seasons.flatMap(season => [
          ...((detail.kind === "goalie" || needsOverview(season, detail.season.season, metric, view)) ? [overviewRequest(season, detail.kind)] : []),
          ...(metric.standingPolicy === "raw_only" ? [] : [metricRequest(season, metric)]),
        ]),
        ...(detail.kind === "skater" && (view === "observed" || metric.standingPolicy === "raw_only") ? [descriptiveRequest(detail.season.season)] : []),
        ...(view === "microstats" ? [microstatsRequest(detail.season.season)] : []),
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
    if (view === "microstats" && metric.family === "microstats") {
      const evidence = yield* api.analysis.evidence({
        params: { playerId },
        query: { season: profile.season.season, family: "microstats" },
      });
      profile = yield* compose(() => withMicrostatsEvidence(profile, evidence));
    }
    if (metric.publicationFamily === "execution") {
      const evidence = yield* api.analysis.evidence({
        params: { playerId },
        query: {
          season: profile.season.season,
          family: "execution",
          strength: metric.selectionStrength!,
        },
      });
      profile = yield* compose(() => withExecutionEvidence(profile, evidence));
    }
    if (selectedLedgerDetail(query, metric)) {
      const evidence = yield* api.analysis.evidence({
        params: { playerId },
        query: { season: profile.season.season, family: "ledger" },
      });
      profile = yield* compose(() => withLedgerEvidence(profile, evidence));
    }
    if (view === "goalie") return (yield* loadGoalie([profile], query))[0];
    if (view === "analytical") return (yield* loadAnalytical([profile], query))[0];
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

// selected-year identities lead the picker; known identities survive absent years.
// paired profiles share one set of exact annual cohort reads.
export const loadComparison = (signal: AbortSignal, query: URLSearchParams) =>
  read(Effect.gen(function* () {
    const api = yield* client;
    const initial = yield* api.analysis.league({
      query: { season: seasonQuery(query), kind: readKind(query).kind, family: "overview" },
    });
    const overview = yield* compose(() => {
      checkSelectedSeason(initial, query);
      return requireOverview(initial);
    });
    const kind = overview.kind;
    const view = readView(query, kind).view;
    const metric = readMetric(query, kind, view).metric;
    const persons = overview.players.map(row => row.person);
    const selectedIds = ["a", "b"].map(key => {
      const values = query.getAll(key);
      return values.length === 1 && Schema.is(HockeyId)(values[0]) ? values[0] : null;
    });
    const [first, second] = selectedIds.map(id => persons.find(row => row.player_id === id));
    const pair = first && second && first.player_id !== second.player_id
      ? [first, second] as const
      : null;
    const requestedIds = selectedIds[0] !== null && selectedIds[1] !== null && selectedIds[0] !== selectedIds[1]
      ? [selectedIds[0], selectedIds[1]] as const : null;
    const details = requestedIds ? yield* Effect.all(
      requestedIds.map(playerId => api.analysis.player({
        params: { playerId },
        query: { season: overview.season.season },
      }).pipe(Effect.catch(error => Schema.is(ApiError)(error) && error._tag === "PlayerNotFound"
        ? Effect.succeed(null) : Effect.fail(error)))),
      { concurrency: "unbounded" },
    ) : [];
    const profileDetails = details[0]?.kind === kind && details[1]?.kind === kind
      ? [details[0], details[1]] as const : null;
    const requests = [...new Map(
      [
        ...(profileDetails
          ? overview.available_seasons.flatMap(season => [
              ...((kind === "goalie" || needsOverview(season, overview.season.season, metric, view)) ? [overviewRequest(season, kind)] : []),
              ...(metric.standingPolicy === "raw_only" ? [] : [metricRequest(season, metric)]),
            ])
          : [metricRequest(overview.season.season, metric)]),
        ...(kind === "skater" && (view === "observed" || metric.standingPolicy === "raw_only") ? [descriptiveRequest(overview.season.season)] : []),
        ...(view === "microstats" ? [microstatsRequest(overview.season.season)] : []),
      ].map(request => [requestKey(request), request]),
    ).values()].filter(
      request => requestKey(request) !== requestKey(overviewRequest(overview.season.season, kind)),
    );
    const responses = yield* Effect.all(
      requests.map(request => api.analysis.league({ query: scalarQuery(request) })),
      { concurrency: "unbounded" },
    );
    let comparison = yield* compose((): ComparisonView => {
      checkRequest(overview, overviewRequest(overview.season.season, kind));
      details.forEach((detail, index) => {
        if (!detail) return;
        sameRelease(overview, detail);
        const person = persons.find(candidate => candidate.player_id === requestedIds![index]);
        if (detail.player_id !== requestedIds![index] ||
            (detail.kind === kind && !equal(detail.person, person ?? null)))
          throw new Error("comparison detail does not match its selected annual identity");
      });
      responses.forEach((response, index) => {
        samePublication(overview, response);
        checkRequest(response, requests[index]);
      });
      const resolved = catalogs([overview, ...details.filter(detail => detail !== null), ...responses]);
      const cohorts = new Map([
        [
          requestKey(overviewRequest(overview.season.season, kind)),
          { ...overview, ...resolved },
        ] as const,
        ...responses.map((response, index) => [
          requestKey(requests[index]), { ...response, ...resolved },
        ] as const),
      ]);
      const selectedOverview = requireOverview(
        cohorts.get(requestKey(overviewRequest(overview.season.season, kind)))!,
      );
      const scalarCohort = cohorts.get(requestKey(metricRequest(overview.season.season, metric)))!;
      const league = composeLeague(selectedOverview, scalarCohort);
      const profiles: ComparisonView["profiles"] = profileDetails ? [
        composeProfile({ ...profileDetails[0], ...resolved }, metric, cohorts, view),
        composeProfile({ ...profileDetails[1], ...resolved }, metric, cohorts, view),
      ] : null;
      const known = details.flatMap(detail => {
        if (!detail || detail.kind !== kind) return [];
        const identity = detail.person ?? detail.history.find(row => row.person !== null)?.person;
        return identity ? [identity] : [];
      });
      const knownPair = profiles && known[0] && known[1] ? [known[0], known[1]] as const : pair;
      return {
        ...league,
        persons: [...persons, ...known.filter(person => !persons.some(row => row.player_id === person.player_id))],
        selectedMetric: metric,
        scalarCohort,
        pair: knownPair,
        profiles,
        overviewCohorts: kind === "goalie" ? [] : profileDetails ? overview.available_seasons.flatMap(season => {
          const cohort = cohorts.get(requestKey(overviewRequest(season)));
          return cohort ? [requireSkaterOverview(cohort)] : [];
        }) : [requireSkaterOverview(selectedOverview)],
        maps: null,
        coreMaps: [],
        selectionError: details.some(detail => detail !== null && detail.kind !== kind)
          ? `mixed skater/goalie comparison is invalid; choose two distinct ${kind === "goalie" ? "goalies" : "skaters"}` : null,
      };
    });
    if (comparison.profiles && view === "goalie") {
      const profiles = yield* loadGoalie(comparison.profiles, query);
      return { ...comparison, profiles: [profiles[0], profiles[1]] as const };
    }
    if (comparison.profiles && metric.publicationFamily === "execution") {
      const profiles = comparison.profiles;
      const evidence = yield* Effect.all(profiles.map(profile => api.analysis.evidence({
        params: { playerId: profile.player_id },
        query: { season: comparison.season.season, family: "execution", strength: metric.selectionStrength! },
      })), { concurrency: "unbounded" });
      comparison = yield* compose((): ComparisonView => {
        catalogs([comparison.overview, ...evidence]);
        return { ...comparison, profiles: [withExecutionEvidence(profiles[0], evidence[0]), withExecutionEvidence(profiles[1], evidence[1])] };
      });
    }
    if (comparison.profiles && selectedLedgerDetail(query, metric)) {
      const profiles = comparison.profiles;
      const evidence = yield* Effect.all(profiles.map(profile => api.analysis.evidence({
        params: { playerId: profile.player_id },
        query: { season: comparison.season.season, family: "ledger" },
      })), { concurrency: "unbounded" });
      comparison = yield* compose((): ComparisonView => {
        catalogs([comparison.overview, ...evidence]);
        return { ...comparison, profiles: [withLedgerEvidence(profiles[0], evidence[0]), withLedgerEvidence(profiles[1], evidence[1])] };
      });
    }
    if (comparison.profiles && view === "analytical") {
      const profiles = yield* loadAnalytical(comparison.profiles, query);
      return { ...comparison, profiles: [profiles[0], profiles[1]] as const, coreMaps: profiles[0].coreMaps };
    }
    if (comparison.profiles && view === "microstats" && metric.family === "microstats") {
      const profiles = comparison.profiles;
      const evidence = yield* Effect.all(profiles.map(profile => api.analysis.evidence({
        params: { playerId: profile.player_id },
        query: { season: comparison.season.season, family: "microstats" },
      })), { concurrency: "unbounded" });
      comparison = yield* compose((): ComparisonView => {
        catalogs([comparison.overview, ...evidence]);
        return {
          ...comparison,
          profiles: [
            withMicrostatsEvidence(profiles[0], evidence[0]),
            withMicrostatsEvidence(profiles[1], evidence[1]),
          ],
        };
      });
    }
    if (!pair || view !== "observed") return comparison;
    const mapMode = mapView(query);
    const ids = pair.map(person => person.player_id);
    const maps = yield* api.analysis.maps({
      query: mapsQuery(overview.season.season, ids, mapMode),
    });
    return yield* compose((): ComparisonView => {
      catalogs([overview, ...details.filter(detail => detail !== null), ...responses, maps]);
      return { ...comparison, maps: observedMaps(maps, comparison, ids, mapMode) };
    });
  }), signal);
