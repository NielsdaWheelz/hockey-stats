import type { PlayerSummary } from "../shared/observed";
import type { PeerSettings } from "./explorer";
import { nameOrder } from "./presentation";

export type ObservedRateKey =
  | "sog60"
  | "goals60"
  | "primaryAssists60"
  | "for60"
  | "against60";
export type PeerPopulation = "personal" | "onIce";
export type Standing =
  | { readonly kind: "ranked"; readonly percentile: number }
  | { readonly kind: "outside" }
  | { readonly kind: "unavailable" };
export type PeerGroup = {
  readonly key: "all" | "f" | "d";
  readonly population: PeerPopulation;
  readonly members: readonly PlayerSummary[];
  readonly selected: readonly {
    readonly player: PlayerSummary;
    readonly slot: 0 | 1;
  }[];
  readonly partialCount: number;
};
export type ObservedRateRow = {
  readonly metric: ObservedRateKey;
  readonly population: PeerPopulation;
  readonly count: number | null;
  readonly rate: number | null;
  readonly standing: Standing;
  readonly groupKey: PeerGroup["key"];
};
export type ObservedCard = {
  readonly player: PlayerSummary;
  readonly slot: 0 | 1;
  readonly rows: readonly ObservedRateRow[];
};
export type ObservedComparison = {
  readonly settings: PeerSettings;
  readonly groups: {
    readonly personal: readonly PeerGroup[];
    readonly onIce: readonly PeerGroup[];
  };
  readonly cards: readonly ObservedCard[];
};

export const observedMetrics = [
  {
    key: "sog60",
    label: "shots on goal",
    population: "personal",
    precision: 2,
    count: (player: PlayerSummary) => player.personal.shots_on_goal,
    rate: (player: PlayerSummary) => player.personal.shots_on_goal_per60,
  },
  {
    key: "goals60",
    label: "goals",
    population: "personal",
    precision: 2,
    count: (player: PlayerSummary) => player.personal.goals,
    rate: (player: PlayerSummary) => player.personal.goals_per60,
  },
  {
    key: "primaryAssists60",
    label: "primary assists",
    population: "personal",
    precision: 2,
    count: (player: PlayerSummary) => player.personal.primary_assists,
    rate: (player: PlayerSummary) => player.personal.primary_assists_per60,
  },
  {
    key: "for60",
    label: "on-ice attempts for",
    population: "onIce",
    precision: 1,
    count: (player: PlayerSummary) => player.metrics.attempts_for,
    rate: (player: PlayerSummary) => player.metrics.for_per60,
  },
  {
    key: "against60",
    label: "on-ice attempts against",
    population: "onIce",
    precision: 1,
    count: (player: PlayerSummary) => player.metrics.attempts_against,
    rate: (player: PlayerSummary) => player.metrics.against_per60,
  },
] as const;

export const metricDefinition = (key: ObservedRateKey) =>
  observedMetrics.find((metric) => metric.key === key)!;

export const populationSupport = (
  player: PlayerSummary,
  population: PeerPopulation,
) => (population === "personal" ? player.personal : player.metrics);

export const peerGroupName = (key: PeerGroup["key"]) =>
  key === "all"
    ? "all skaters"
    : key === "f"
      ? "reported forwards"
      : "reported defense";

export function selectPeerGroups(
  players: readonly PlayerSummary[],
  selected: readonly PlayerSummary[],
  settings: PeerSettings,
  population: PeerPopulation,
): PeerGroup[] {
  const selections = ([0, 1] as const).flatMap((slot) =>
    selected[slot] ? [{ player: selected[slot], slot }] : [],
  );
  const keys: PeerGroup["key"][] =
    settings.peers === "all"
      ? ["all"]
      : (["f", "d"] as const).filter((key) =>
          selections.some(
            ({ player }) =>
              (player.reported_position === "D" ? "d" : "f") === key,
          ),
        );
  const metrics = observedMetrics.filter(
    (metric) => metric.population === population,
  );
  return keys.map((key) => {
    const members = players
      .filter((player) => {
        const support = populationSupport(player, population);
        return (
          (key === "all" ||
            (player.reported_position === "D" ? "d" : "f") === key) &&
          support.included_seconds > 0 &&
          support.included_seconds >= settings.peerMin * 60 &&
          metrics.every((metric) => metric.rate(player) !== null)
        );
      })
      .sort(nameOrder);
    return {
      key,
      population,
      members,
      partialCount: members.filter(
        (player) =>
          populationSupport(player, population).coverage_status === "partial",
      ).length,
      selected: selections.filter(
        ({ player }) =>
          key === "all" ||
          (player.reported_position === "D" ? "d" : "f") === key,
      ),
    };
  });
}

export function observedStanding(
  rate: number | null,
  playerId: string,
  group: PeerGroup,
  metric: ObservedRateKey,
): Standing {
  if (rate === null) return { kind: "unavailable" };
  if (!group.members.some((player) => player.player_id === playerId))
    return { kind: "outside" };
  const definition = metricDefinition(metric);
  let lower = 0;
  let equal = 0;
  for (const player of group.members) {
    const value = definition.rate(player)!;
    if (value < rate) lower += 1;
    if (value === rate) equal += 1;
  }
  return {
    kind: "ranked",
    percentile: (100 * (lower + equal / 2)) / group.members.length,
  };
}

export function formatPercentile(percentile: number): string {
  const label = percentile.toFixed(1);
  return label === "0.0" ? "<0.1" : label === "100.0" ? ">99.9" : label;
}

export function buildObservedComparison(
  players: readonly PlayerSummary[],
  selected: readonly PlayerSummary[],
  settings: PeerSettings,
): ObservedComparison {
  const groups = {
    personal: selectPeerGroups(players, selected, settings, "personal"),
    onIce: selectPeerGroups(players, selected, settings, "onIce"),
  };
  const cards = ([0, 1] as const).flatMap((slot) => {
    const player = selected[slot];
    if (!player) return [];
    return [
      {
        player,
        slot,
        rows: observedMetrics.map((definition) => {
          const group = groups[definition.population].find((candidate) =>
            candidate.selected.some((selection) => selection.slot === slot),
          )!;
          const rate = definition.rate(player);
          return {
            metric: definition.key,
            population: definition.population,
            count: definition.count(player),
            rate,
            standing: observedStanding(
              rate,
              player.player_id,
              group,
              definition.key,
            ),
            groupKey: group.key,
          };
        }),
      },
    ];
  });
  return { settings, groups, cards };
}
