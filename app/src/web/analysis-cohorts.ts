import type { AnalysisDatum } from "./analysis-values";
import type { PeerSettings } from "./explorer";

export type AnalysisStanding =
  | {
      readonly kind: "ranked";
      readonly percentile: number;
      readonly n: number;
      readonly peerGroup: string;
      readonly cutoffMinutes: number;
    }
  | {
      readonly kind: "outside";
      readonly reason: string;
      readonly n: number;
      readonly peerGroup: string;
      readonly cutoffMinutes: number;
    }
  | {
      readonly kind: "unavailable";
      readonly reason: string;
      readonly n: number | null;
      readonly peerGroup: string | null;
      readonly cutoffMinutes: number | null;
    };
type Selection = {
  readonly datum: AnalysisDatum;
  readonly slot: number;
  readonly standing: AnalysisStanding;
};

export type AnalysisPeerGroup = {
  readonly key: string;
  readonly peerGroup: string;
  readonly cutoffMinutes: number | null;
  readonly members: readonly AnalysisDatum[];
  readonly selected: readonly Selection[];
  readonly incompatiblePeerCount: number;
};

export type AnalysisCohort = { readonly groups: readonly AnalysisPeerGroup[] };

export const positionGroup = (position: string | null): "f" | "d" | null =>
  position === "D"
    ? "d"
    : position === "C" || position === "L" || position === "R" || position === "F"
      ? "f"
      : null;

export function midpointPercentile(
  value: number,
  values: readonly number[],
): number | null {
  if (!values.length || !Number.isFinite(value)) return null;
  let less = 0;
  let equal = 0;
  for (const peer of values) {
    if (peer < value) less++;
    if (peer === value) equal++;
  }
  return 100 * (less + equal / 2) / values.length;
}

function qualificationReason(
  datum: AnalysisDatum,
  cutoffMinutes: number,
): string | null {
  if (datum.status === "absent") return "absent season";
  if (datum.value === null || !Number.isFinite(datum.value))
    return datum.reason ?? "quantity unavailable";
  if (datum.metric.cutoff === "census") return "census_unverified";
  const seconds = datum.qualificationSeconds;
  if (seconds === null || !Number.isFinite(seconds)) return "qualification unavailable";
  if (seconds <= 0) return "no exposure";
  return seconds < cutoffMinutes * 60 ? "below cutoff" : null;
}

export function buildAnalysisCohort(
  datums: readonly AnalysisDatum[],
  selected: readonly AnalysisDatum[],
  settings: PeerSettings,
): AnalysisCohort {
  const groups: (Omit<AnalysisPeerGroup, "selected"> & { selected: Selection[] })[] = [];
  selected.forEach((datum, slot) => {
    if (datum.status === "absent") {
      groups.push({
        key: JSON.stringify(["absent", datum.playerId, datum.season]),
        peerGroup: "reference unavailable",
        cutoffMinutes: null,
        members: [],
        incompatiblePeerCount: 0,
        selected: [
          {
            datum,
            slot,
            standing: {
              kind: "unavailable",
              reason: "absent season",
              n: null,
              peerGroup: null,
              cutoffMinutes: null,
            },
          },
        ],
      });
      return;
    }
    const position = datum.metric.kind === "goalie"
      ? "g"
      : settings.peers === "all"
        ? "all"
        : positionGroup(datum.person?.reported_position ?? null);
    const peerGroup = position === "g"
      ? "goalies"
      : position === "all"
        ? "all skaters"
        : position === "f"
          ? "reported forwards"
          : position === "d"
            ? "reported defense"
            : "unknown position";
    const cutoff = datum.metric.cutoff === "specialty"
      ? settings.specialtyMin
      : settings.peerMin;
    const cutoffMinutes = datum.metric.cutoff === "census" ? null : cutoff;
    const key = JSON.stringify([position, datum.semanticKey]);
    const existing = groups.find(group => group.key === key);
    if (existing) {
      existing.selected.push({
        datum,
        slot,
        standing: standing(datum, existing, cutoff, position),
      });
      return;
    }
    const candidates = datums.filter(peer =>
      peer.season === datum.season &&
      peer.metric.kind === datum.metric.kind &&
      peer.metric.id === datum.metric.id &&
      (
        position === "g" ||
        position === "all" ||
        position !== null && positionGroup(peer.person?.reported_position ?? null) === position
      ),
    );
    if (!datum.semanticIdentityKnown && datum.value === null && position !== null) {
      const placeholder: typeof groups[number] = {
        key,
        peerGroup,
        cutoffMinutes,
        members: [],
        incompatiblePeerCount: 0,
        selected: [],
      };
      placeholder.selected.push({
        datum,
        slot,
        standing: standing(datum, placeholder, cutoff, position),
      });
      groups.push(placeholder);
      // no selected definition is known: retain every real peer partition separately.
      const meanings = new Set(
        candidates
          .filter(peer => peer.value !== null && peer.semanticIdentityKnown)
          .map(peer => peer.semanticKey),
      );
      for (const meaning of meanings) {
        const partitionKey = JSON.stringify([position, meaning]);
        if (groups.some(group => group.key === partitionKey)) continue;
        groups.push({
          key: partitionKey,
          peerGroup,
          cutoffMinutes,
          selected: [],
          members: candidates
            .filter(peer =>
              peer.semanticKey === meaning && qualificationReason(peer, cutoff) === null,
            )
            .sort(datumOrder),
          incompatiblePeerCount: candidates
            .filter(peer => peer.value !== null && peer.semanticKey !== meaning).length,
        });
      }
      return;
    }
    const group: typeof groups[number] = {
      key,
      peerGroup,
      cutoffMinutes,
      selected: [],
      members: candidates
        .filter(peer =>
          peer.semanticKey === datum.semanticKey && qualificationReason(peer, cutoff) === null,
        )
        .sort(datumOrder),
      incompatiblePeerCount: candidates
        .filter(peer => peer.value !== null && peer.semanticKey !== datum.semanticKey).length,
    };
    group.selected.push({
      datum,
      slot,
      standing: standing(datum, group, cutoff, position),
    });
    groups.push(group);
  });
  return { groups };
}

const datumOrder = (a: AnalysisDatum, b: AnalysisDatum) =>
  (a.person?.display_name ?? "").localeCompare(b.person?.display_name ?? "") ||
  a.playerId.localeCompare(b.playerId);

function standing(
  datum: AnalysisDatum,
  group: AnalysisPeerGroup,
  cutoff: number,
  position: string | null,
): AnalysisStanding {
  const common = {
    n: group.members.length,
    peerGroup: group.peerGroup,
    cutoffMinutes: group.cutoffMinutes,
  };
  const reason = qualificationReason(datum, cutoff);
  if (datum.status === "absent" || datum.metric.cutoff === "census")
    return {
      kind: "unavailable",
      reason: reason!,
      n: null,
      peerGroup: null,
      cutoffMinutes: null,
    };
  if (!datum.semanticIdentityKnown && datum.value === null)
    return {
      kind: "unavailable",
      reason: reason!,
      ...common,
      n: null,
      peerGroup: position === null ? null : group.peerGroup,
    };
  if (datum.value === null)
    return {
      kind: "unavailable",
      reason: reason!,
      ...common,
      peerGroup: position === null ? null : group.peerGroup,
    };
  if (position === null)
    return {
      kind: "unavailable",
      reason: "unknown position",
      n: null,
      peerGroup: null,
      cutoffMinutes: cutoff,
    };
  if (reason) {
    if (reason === "below cutoff" || reason === "no exposure")
      return { kind: "outside", reason, ...common, cutoffMinutes: cutoff };
    return { kind: "unavailable", reason, ...common };
  }
  if (!group.members.length) return { kind: "unavailable", reason: "empty cohort", ...common };
  if (!group.members.some(member => member.playerId === datum.playerId))
    return {
      kind: "outside",
      reason: "not a cohort member",
      ...common,
      cutoffMinutes: cutoff,
    };
  return {
    kind: "ranked",
    percentile: midpointPercentile(
      datum.value!,
      group.members.map(peer => peer.value!),
    )!,
    ...common,
    cutoffMinutes: cutoff,
  };
}
