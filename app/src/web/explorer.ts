import * as Schema from "effect/Schema";
import { HockeyId, type PlayerSummary, type Team } from "../shared/observed";
import { observedMetrics, type ObservedRateKey } from "./observed-comparison";
import {
  matchingPlayers,
  nameOrder,
  playerName,
  teamName,
} from "./presentation";

export type Sort =
  | "name"
  | "games"
  | "minutes"
  | "for60"
  | "against60"
  | "sog60"
  | "goals60"
  | "primaryAssists60"
  | "personalMinutes";
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
};

export function parseMinutes(value: string): number | undefined {
  if (!/^(0|[1-9]\d*)$/.test(value)) return undefined;
  const minutes = Number(value);
  return Number.isSafeInteger(minutes * 60) ? minutes : undefined;
}

export function readDiscovery(search: URLSearchParams): {
  readonly discovery: Discovery;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const sortValues = search.getAll("sort");
  const rawSort = sortValues.length === 1 ? sortValues[0] : undefined;
  const sort: Sort =
    rawSort === "name" ||
    rawSort === "games" ||
    rawSort === "minutes" ||
    rawSort === "for60" ||
    rawSort === "against60" ||
    rawSort === "sog60" ||
    rawSort === "goals60" ||
    rawSort === "primaryAssists60" ||
    rawSort === "personalMinutes"
      ? rawSort
      : "minutes";
  if (sortValues.length && rawSort !== sort) next.delete("sort");
  const directions = search.getAll("dir");
  const rawDirection = directions.length === 1 ? directions[0] : undefined;
  const dir = rawDirection === "asc" ? "asc" : "desc";
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
  return { settings: { peers, peerMin: minimum ?? 300 }, search: next };
}

export function readRateMetric(search: URLSearchParams): {
  readonly metric: ObservedRateKey;
  readonly search: URLSearchParams;
} {
  const next = new URLSearchParams(search);
  const values = search.getAll("metric");
  const metric =
    values.length === 1
      ? observedMetrics.find((definition) => definition.key === values[0])?.key
      : undefined;
  if (values.length && metric === undefined) next.delete("metric");
  return { metric: metric ?? "sog60", search: next };
}

export function selectDiscovery(
  players: readonly PlayerSummary[],
  discovery: Discovery,
): PlayerSummary[] {
  const selected = matchingPlayers(players, discovery.q).filter(
    (player) =>
      (discovery.position === "all" ||
        (player.reported_position === "D" ? "d" : "f") ===
          discovery.position) &&
      (discovery.team === null ||
        player.teams.some((team) => team.id === discovery.team)) &&
      player.metrics.included_seconds >= discovery.min * 60,
  );
  const value = (player: PlayerSummary) =>
    discovery.sort === "games"
      ? player.games_with_included_time
      : discovery.sort === "minutes"
        ? player.metrics.included_seconds
        : discovery.sort === "for60"
          ? player.metrics.for_per60
          : discovery.sort === "against60"
            ? player.metrics.against_per60
            : discovery.sort === "sog60"
              ? player.personal.shots_on_goal_per60
              : discovery.sort === "goals60"
                ? player.personal.goals_per60
                : discovery.sort === "primaryAssists60"
                  ? player.personal.primary_assists_per60
                  : player.personal.included_seconds;
  return selected.sort((a, b) => {
    if (discovery.sort === "name")
      return (
        (discovery.dir === "asc" ? 1 : -1) *
          playerName(a).localeCompare(playerName(b), "en") || nameOrder(a, b)
      );
    const left = value(a),
      right = value(b);
    if (left === null) return right === null ? nameOrder(a, b) : 1;
    if (right === null) return -1;
    return (
      (discovery.dir === "asc" ? left - right : right - left) || nameOrder(a, b)
    );
  });
}

export function teamOptions(players: readonly PlayerSummary[]): Team[] {
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
