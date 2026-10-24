import * as Schema from "effect/Schema";
import { useEffect } from "react";
import {
  useLocation,
  useNavigation,
  useSearchParams,
  type ShouldRevalidateFunctionArgs,
} from "react-router";
import { HockeyId, type Team } from "../shared/observed";
import {
  analysisMetric,
  defaultAnalysisMetric,
  type AnalysisMetric,
  type AnalysisMetricId,
} from "./analysis-values";
import { teamName, type PlayerIdentity } from "./presentation";

export type Sort =
  | AnalysisMetricId
  | "name"
  | "games"
  | "minutes"
  | "personalMinutes"
  | "reportedAppearances"
  | "reportedMinutes"
  | "evScoringMinutes"
  | "ppScoringMinutes";
export type AnalysisView = "comparative" | "observed";
export type DiscoveryTable =
  | "overview"
  | "observed"
  | "descriptive"
  | "spatial"
  | "execution"
  | "shootiness"
  | "penalties"
  | "territory";
export type TableSelection = {
  readonly table: DiscoveryTable;
  readonly strength:
    | "5v5"
    | "pp"
    | "pk"
    | "5v4"
    | "5v3"
    | "4v3"
    | "4v5"
    | "3v5"
    | "3v4"
    | null;
};

export function readView(search: URLSearchParams): {
  readonly view: AnalysisView;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const values = search.getAll("view");
  const selected = values.length === 1 ? values[0] : undefined;
  if (values.length && selected !== "comparative" && selected !== "observed")
    next.delete("view");
  return { view: selected === "observed" ? "observed" : "comparative", search: next };
}

export function readTableSelection(search: URLSearchParams): {
  readonly selection: TableSelection;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const tables: readonly DiscoveryTable[] = [
    "overview", "observed", "descriptive", "spatial", "execution", "shootiness", "penalties", "territory",
  ];
  const values = search.getAll("table");
  const selected = values.length === 1 ? values[0] : undefined;
  const table = tables.find(value => value === selected) ?? "overview";
  if (values.length && selected !== table) next.delete("table");
  const strengths = search.getAll("strength");
  const rawStrength = strengths.length === 1 ? strengths[0] : undefined;
  const choices = table === "spatial"
    ? ["5v5", "pp", "pk"] as const
    : table === "execution" || table === "shootiness"
      ? ["5v5", "5v4", "5v3", "4v3", "4v5", "3v5", "3v4"] as const
      : [];
  const strength = choices.find(value => value === rawStrength) ?? choices[0] ?? null;
  if (strengths.length && rawStrength !== strength) next.delete("strength");
  return { selection: { table, strength }, search: next };
}

export type Discovery = {
  readonly q: string;
  readonly sort: Sort;
  readonly dir: "asc" | "desc";
  readonly position: "all" | "f" | "d";
  readonly team: string | null;
  readonly min: number;
};
export type PeerSettings = {
  readonly peers: "position" | "all";
  readonly peerMin: number;
  readonly specialtyMin: number;
};

export function parseMinutes(value: string): number | undefined {
  if (!/^(0|[1-9]\d*)$/.test(value)) return undefined;
  const minutes = Number(value);
  return Number.isSafeInteger(minutes * 60) ? minutes : undefined;
}

export function readDiscovery(
  search: URLSearchParams,
  allowedSorts: readonly Sort[],
  defaultSort: Sort,
): {
  readonly discovery: Discovery;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const sortValues = search.getAll("sort");
  const rawSort = sortValues.length === 1 ? sortValues[0] : undefined;
  const sort = allowedSorts.find(value => value === rawSort) ?? defaultSort;
  if (sortValues.length && rawSort !== sort) next.delete("sort");
  const directions = search.getAll("dir");
  const rawDirection = directions.length === 1 ? directions[0] : undefined;
  const invalidSort = sortValues.length > 0 && rawSort !== sort;
  const dir = !invalidSort && rawDirection === "asc" ? "asc" : "desc";
  if (invalidSort) next.delete("dir");
  if (directions.length && rawDirection !== "asc" && rawDirection !== "desc")
    next.delete("dir");
  const positions = search.getAll("position");
  const rawPosition = positions.length === 1 ? positions[0] : undefined;
  const position =
    rawPosition === "f" || rawPosition === "d" ? rawPosition : "all";
  if (
    positions.length &&
    rawPosition !== "all" &&
    rawPosition !== "f" &&
    rawPosition !== "d"
  )
    next.delete("position");
  const teams = search.getAll("team");
  const team =
    teams.length === 1 && Schema.is(HockeyId)(teams[0]) ? teams[0] : null;
  if (teams.length && team === null) next.delete("team");
  const minimums = search.getAll("min");
  const minimum = minimums.length === 1 ? parseMinutes(minimums[0]) : undefined;
  if (minimums.length && minimum === undefined) next.delete("min");
  return {
    discovery: {
      q: search.get("q") ?? "",
      sort,
      dir,
      position,
      team,
      min: minimum ?? 0,
    },
    search: next,
  };
}

export function readPeerSettings(search: URLSearchParams): {
  readonly settings: PeerSettings;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const modes = search.getAll("peers");
  const rawMode = modes.length === 1 ? modes[0] : undefined;
  const peers = rawMode === "all" ? "all" : "position";
  if (modes.length && rawMode !== "position" && rawMode !== "all")
    next.delete("peers");
  const minimums = search.getAll("peerMin");
  const minimum = minimums.length === 1 ? parseMinutes(minimums[0]) : undefined;
  if (minimums.length && minimum === undefined) next.delete("peerMin");
  const specialties = search.getAll("specialtyMin");
  const specialty = specialties.length === 1 ? parseMinutes(specialties[0]) : undefined;
  if (specialties.length && specialty === undefined) next.delete("specialtyMin");
  return {
    settings: { peers, peerMin: minimum ?? 300, specialtyMin: specialty ?? 50 },
    search: next,
  };
}

export function readMetric(
  search: URLSearchParams,
  kind: "skater" | "goalie",
  view = readView(search).view,
): {
  readonly metric: AnalysisMetric;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const values = search.getAll("metric");
  const selected = values.length === 1 ? analysisMetric(values[0]) : undefined;
  const metric = selected?.kind === kind ? selected : undefined;
  if (values.length && metric === undefined) next.delete("metric");
  return {
    metric: metric ?? (kind === "skater" && view === "comparative"
      ? analysisMetric("ledger.league_total")!
      : defaultAnalysisMetric(kind)),
    search: next,
  };
}

export function readHistoryScale(search: URLSearchParams, metric = analysisMetric(search.get("metric") ?? "")): {
  readonly scale: "raw" | "percentile";
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const values = search.getAll("history");
  const selected = values.length === 1 ? values[0] : undefined;
  const scale = metric?.standingPolicy !== "raw_only" && selected === "percentile" ? "percentile" : "raw";
  if (metric?.standingPolicy === "raw_only" && selected === "percentile") next.set("history", "raw");
  if (values.length && selected !== "raw" && selected !== "percentile")
    next.delete("history");
  return { scale, search: next };
}

export function teamOptions(
  players: readonly Pick<PlayerIdentity, "teams">[],
): Team[] {
  const names = new Map<string, Set<string>>();
  for (const player of players) {
    for (const team of player.teams) {
      let labels = names.get(team.id);
      if (!labels) {
        labels = new Set<string>();
        names.set(team.id, labels);
      }
      if (team.abbreviation !== null) labels.add(team.abbreviation);
    }
  }
  return [...names]
    .map(([id, labels]) => ({
      id,
      abbreviation: labels.size === 1 ? [...labels][0] : null,
    }))
    .sort(
      (a, b) =>
        teamName(a).localeCompare(teamName(b), "en") ||
        a.id.length - b.id.length ||
        a.id.localeCompare(b.id),
    );
}

export type MapMode = "difference" | "absolute";

export function readMapMode(search: URLSearchParams): {
  readonly mode: MapMode;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const values = search.getAll("map");
  const mode =
    values.length === 1 && values[0] === "absolute" ? "absolute" : "difference";
  if (values.length && mode === "difference") next.delete("map");
  return { mode, search: next };
}

// compose another edit with an in-flight same-page selection, not its old view.
export function viewSearch(
  current: { readonly pathname: string; readonly search: string },
  pending?: { readonly pathname: string; readonly search: string },
): URLSearchParams {
  return new URLSearchParams(
    pending?.pathname === current.pathname ? pending.search : current.search,
  );
}

export function seasonSearch(search: URLSearchParams | string, season: string) {
  const next = new URLSearchParams(search);
  next.set("season", season);
  return next;
}

// only the idle normalization below may skip an omitted-season reload.
let canonicalization: { readonly from: string; readonly to: string } | undefined;

export function useCanonicalSearch(
  season: string,
  normalized: URLSearchParams,
) {
  const location = useLocation();
  const navigation = useNavigation();
  const [search, setSearch] = useSearchParams();
  const next = new URLSearchParams(normalized);
  if (!search.has("season")) next.set("season", season);
  useEffect(() => {
    if (navigation.state !== "idle") return;
    canonicalization = undefined;
    if (next.toString() === search.toString()) return;
    if (!search.has("season"))
      canonicalization = {
        from: location.pathname + location.search,
        to: `${location.pathname}?${next}`,
      };
    setSearch(next, {
      replace: true,
      preventScrollReset: true,
      state: location.state,
    });
  }, [next.toString(), search.toString(), navigation.state, location]);
}

export function shouldRevalidateView(
  { currentUrl, nextUrl, defaultShouldRevalidate }: ShouldRevalidateFunctionArgs,
  presentationKeys: readonly string[],
) {
  if (
    canonicalization?.from === currentUrl.pathname + currentUrl.search &&
    canonicalization.to === nextUrl.pathname + nextUrl.search
  ) {
    // the router can ask twice for one navigation; keep the answer stable
    // until the idle hook sees the committed location.
    return false;
  }
  if (pendingSeasonChange(currentUrl, nextUrl)) return true;
  if (
    currentUrl.pathname === nextUrl.pathname &&
    currentUrl.search !== nextUrl.search
  ) {
    const current = new URLSearchParams(currentUrl.search);
    const next = new URLSearchParams(nextUrl.search);
    for (const key of presentationKeys) {
      current.delete(key);
      next.delete(key);
    }
    if (current.toString() === next.toString()) return false;
  }
  return defaultShouldRevalidate;
}

export function pendingSeasonChange(
  current: { readonly search: string },
  pending?: { readonly search: string },
) {
  return (
    pending !== undefined &&
    JSON.stringify(new URLSearchParams(current.search).getAll("season")) !==
      JSON.stringify(new URLSearchParams(pending.search).getAll("season"))
  );
}
