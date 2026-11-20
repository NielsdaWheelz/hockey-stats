import { createHash } from "node:crypto";
import { isDeepStrictEqual as same } from "node:util";
import * as A from "../shared/player-analysis.js";

type Result<S extends { readonly Type: unknown }> = {
  readonly availability: "provided" | "not_computed";
  readonly explanation: string | null;
  readonly data: S["Type"] | null;
};
export type LedgerSources = {
  spatial: ReadonlyMap<string, Result<typeof A.SkaterSpatial>>;
  spatialEvidence: ReadonlyMap<string, Result<typeof A.SpatialEvidence>>;
  execution: ReadonlyMap<string, Result<typeof A.SkaterExecution>>;
  shootiness: ReadonlyMap<string, Result<typeof A.SkaterShootiness>>;
  penalties: ReadonlyMap<string, Result<typeof A.SkaterPenalties>>;
  territory: ReadonlyMap<string, Result<typeof A.SkaterTerritory>>;
};
type Reference = A.LedgerReference;
type Method = typeof A.Method.Type;
type Group = "F" | "D";
type Term = typeof A.LedgerTerm.Type;
type State = Reference["state_references"][number];
const groups = ["F", "D"] as const;
const states = A.ExecutionStrength.literals;
const units = [[3,2], [4,1], [4,1], [3,1], [2,2], [1,2], [1,2]] as const;
const terms = A.LedgerTerm.literals;
const stable = A.stableSum;
const check: (condition: unknown, message: string) => asserts condition = (condition, message) => {
  if (!condition) throw new Error(`ledger: ${message}`);
};
const ordered = (keys: readonly string[]) => keys.every((key, i) => i === 0 || keys[i - 1] < key);
const near = (value: number | null, contributions: readonly (number | null)[]) =>
  contributions.every((term): term is number => term !== null)
    ? value !== null && A.ledgerClose(value, contributions)
    : value === null;

const slotConstants = (reference: State, role: Group) => {
  const logits = reference.neutral_slot_logits!;
  const slots: Group[] = [
    ...Array<Group>(reference.unit.forwards).fill("F"), ...Array<Group>(reference.unit.defenders).fill("D"),
  ];
  const focal = slots.indexOf(role);
  const remaining = slots.map((_, i) => i).filter(i => i !== focal);
  const normalized = (indices: readonly number[]) => {
    const center = Math.max(...indices.map(i => logits[slots[i]]));
    const weights = indices.map(i => Math.exp(logits[slots[i]] - center));
    const total = stable(weights);
    return weights.map(weight => weight / total);
  };
  const remainingWeights = normalized(remaining);
  return {
    p0: normalized(slots.map((_, i) => i))[focal],
    k: stable(remaining.map((shooter, index) => {
      const weight = (setter: Group) => setter === "D" ? 1 : slots[shooter] === "F" ? 2 : 3;
      return remainingWeights[index] * weight(role) /
        stable(slots.filter((_, index) => index !== shooter).map(weight));
    })),
  };
};

export const validateLedgerYear = (
  reference: Reference,
  ledgers: ReadonlyMap<string, A.ValueLedger>,
  source: LedgerSources,
  methods: Readonly<Record<string, Method>>,
  inventory: ReadonlyMap<string, ReadonlySet<string>>,
  preparation: string | null,
) => {
  const { reference_id, ...body } = reference;
  check(createHash("sha256").update(JSON.stringify(A.binary64DigestRepresentation(body))).digest("hex") === reference_id,
    "reference digest differs");
  const method = methods[reference.method_id];
  const roles = { prepared: "prepared", source_results: "source_results",
    usage_reduction: "derivation", shorthanded_reduction: "derivation", shootiness_state: "annual_state" } as const;
  check(method?.family === "ledger" && reference.inputs.prepared.sha256 === preparation &&
    method.inputs.some(input => input.role === "derivation" && input.sha256 === reference_id &&
      input.seasons.includes(reference.season)) &&
    method.evidence.some(receipt => receipt.sha256 === reference_id) &&
    (Object.keys(roles) as (keyof typeof roles)[]).every(key => {
      const binding = reference.inputs[key];
      return method.evidence.some(receipt => same(binding, receipt)) &&
        method.inputs.some(input => input.role === roles[key] && input.sha256 === binding.sha256 &&
          input.seasons.includes(reference.season));
    }), "annual method and selected input bindings differ");

  const scores = method.inputs.filter(input => input.role === "execution_score");
  const selectedScore = scores[0];
  check(scores.length <= 1 && (!selectedScore || (same(selectedScore.seasons, [reference.season]) &&
    method.evidence.some(receipt => receipt.sha256 === selectedScore.sha256))), "invalid selected execution score binding");
  const references = reference.state_references;
  check(same(references.map(ref => ref.strength), states), "annual state axes differ");
  const firstState = references[0];
  check(references.every(ref => ref.shootiness_reference_id === firstState.shootiness_reference_id &&
    (ref.neutral_slot_logits !== null) === (firstState.neutral_slot_logits !== null)),
    "shared shootiness identity or availability differs by strength");
  const pp = references.slice(1, 4).map(state => state.mixture_weight);
  check(A.ledgerClose(1, pp), "pp mixture does not close");
  const weights = [1, ...pp, ...pp];
  const constants = references.map((ref, index) => {
    const weight = weights[index];
    check(weight <= 1 && A.ledgerClose(ref.mixture_weight, [weight]) &&
      (ref.hours === 0) === (weight === 0) && (ref.mixture_weight === 0) === (weight === 0) &&
      A.ledgerClose(ref.hours, [(index === 0 ? 1000 : 100) / 60 * weight]) &&
      (ref.attempts_per_hour.value === null || ref.attempts_per_hour.value >= 0) &&
      same([ref.unit.forwards, ref.unit.defenders], units[index]) &&
      ref.attempt_reference.strength === ref.strength, "state mixture, workload or unit differs");
    const attempts = ref.attempt_reference;
    if (attempts.kind === "source_pool") {
      check(index >= 4 && attempts.neutral_goal_mass <= attempts.attempts &&
        (index === 4 || same(attempts.reduction, reference.inputs.shorthanded_reduction)) &&
        (attempts.included_seconds > 0
          ? attempts.attempts === 0 ? ref.attempts_per_hour.value === 0
            : near(ref.attempts_per_hour.value, [3600 * attempts.attempts / attempts.included_seconds])
          : ref.attempts_per_hour.value === null && attempts.attempts === 0 &&
            ["no_exposure", "missing_source"].includes(ref.attempts_per_hour.unavailable_reason!)),
        "source-pooled attempt reference differs");
    } else check(index < 4, "attempt reference family differs");
    if (ref.execution_panel)
      check(A.ledgerClose(ref.execution_panel.setup_weight, [.8 * ref.execution_panel.opportunities]),
        "execution panel setup mass differs");
    if (ref.neutral_slot_logits === null) {
      check(ref.setting_K.F.value === null && same(ref.setting_K.F, firstState.setting_K.F) &&
        same(ref.setting_K.F, ref.setting_K.D), "K lacks a common unavailability reason");
      return null;
    }
    check(ref.shootiness_reference_id !== null && Math.max(ref.neutral_slot_logits.F, ref.neutral_slot_logits.D) === 0,
      "neutral logits lack their source identity or centering");
    const neutral = { F: slotConstants(ref, "F"), D: slotConstants(ref, "D") };
    for (const role of groups) {
      const value = ref.setting_K[role].value;
      check(value !== null && value >= 0 && value <= 1 && near(value, [neutral[role].k]), "remaining-slot K differs");
    }
    return neutral;
  });
  check(reference.groups.length === 2 * inventory.size &&
    reference.groups.every((group, index) => {
      if (index === 0) return true;
      const previous = reference.groups[index - 1];
      return previous.team_id < group.team_id ||
        (previous.team_id === group.team_id && previous.position < group.position);
    }),
    "annual team/group axes differ");
  const fixed = { F: new Map<string, { team_id: string; seconds: number }[]>(),
    D: new Map<string, { team_id: string; seconds: number }[]>() };
  const groupSeconds = new Map<string, number>();
  for (const group of reference.groups) {
    const games = inventory.get(group.team_id);
    check(games && group.inventory_games === games.size && group.supported_games <= games.size &&
      ordered(group.reasons) && ordered(group.affected_games) && ordered(group.affected_players) &&
      group.affected_games.every(id => games.has(id)) &&
      ordered(group.members.map(member => member.player_id)), "invalid team-game/group inventory");
    if (group.status === "excluded") {
      check(group.reasons.length > 0 && group.cutoff_seconds === null &&
        group.members.every(member => member.rank === null && member.depth === null), "excluded group is ranked");
      continue;
    }
    const cutoff = group.position === "F" ? 12 : 6;
    const times = group.members.map(member => member.known_team_seconds).sort((a,b) => b-a);
    check(group.reasons.length === 0 && group.supported_games === group.inventory_games &&
      group.missing_time_records === 0 && !group.unquantified_gap &&
      group.affected_games.length === 0 && group.affected_players.length === 0 &&
      group.known_seconds === times.reduce((sum, seconds) => sum + seconds, 0) &&
      group.cutoff_seconds === (times[cutoff - 1] ?? null), "complete team-group coverage or cutoff differs");
    for (const member of group.members) {
      const rank = times.indexOf(member.known_team_seconds) + 1;
      check(member.complete && member.known_team_seconds > 0 && member.rank === rank &&
        member.depth === (rank > cutoff) &&
        ledgers.get(member.player_id)?.evidence.depth_position.group === group.position,
        "complete team rank or annual position differs");
      groupSeconds.set(member.player_id, (groupSeconds.get(member.player_id) ?? 0) + member.known_team_seconds);
      if (member.depth) {
        const members = fixed[group.position];
        const teams = members.get(member.player_id) ?? [];
        teams.push({team_id: group.team_id, seconds: member.known_team_seconds});
        members.set(member.player_id, teams);
      }
    }
  }
  for (const role of groups) {
    const position = reference.positions[role];
    const members = [...fixed[role]].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([player_id, teams]) =>
      ({ player_id, teams, seconds: teams.reduce((sum, team) => sum + team.seconds, 0) }));
    const total = members.reduce((sum, member) => sum + member.seconds, 0);
    check(same(position.members, members) && position.member_count === members.length && position.total_seconds === total,
      "fixed depth member and team-time weights differ");
    const missing = members.flatMap(({player_id}) => {
      const row = ledgers.get(player_id);
      check(row, "weighted depth member lacks a ledger row");
      const absent = terms.filter(term => row.components[term].league_goals.value === null);
      return absent.length ? [{ player_id, terms: absent }] : [];
    });
    const available = total > 0 && missing.length === 0;
    check(same(position.missing_vectors, missing) && position.available === available &&
      position.reason === (available ? null : total === 0 ? "no_exposure" : "missing_member_vectors") &&
      (position.components !== null) === available, "depth vector availability differs");
    if (position.components)
      for (const term of terms)
        check(near(position.components[term], members.map(member =>
          (member.seconds / total) * ledgers.get(member.player_id)!.components[term].league_goals.value!)),
          "common-weight depth vector differs");
  }

  const unavailable = (reason: NonNullable<A.Estimate["unavailable_reason"]>, explanation: string): A.Estimate => ({
    value: null, unavailable_reason: reason, reason_detail: { explanation, evidence: [] },
    uncertainty: { kind: "not_estimated" },
  });
  const unestimated = (estimate: A.Estimate | undefined, explanation: string | null): A.Estimate =>
    estimate ? { ...estimate, uncertainty: { kind: "not_estimated" } } : unavailable("not_computed", explanation!);
  const binding = (strength: string | null, entry: Result<{Type: {method_id: string}}>) => {
    const method_id = entry.data?.method_id ?? null;
    const method = method_id === null ? null : methods[method_id];
    return { strength, availability: entry.availability, explanation: entry.explanation, method_id,
      reference_id: method?.reference_id ?? null, support_policy_id: method?.support_policy_id ?? null };
  };
  const estimateMatches = (actual: A.Estimate, expected: A.Estimate, factor = 1) =>
    expected.value === null ? same(actual, expected) : near(actual.value, [expected.value * factor]);
  const matchingTermSum = (actual: A.Estimate, estimates: readonly A.Estimate[]) => {
    const missing = estimates.find(estimate => estimate.value === null);
    return missing ? same(actual, missing) : near(actual.value, estimates.map(estimate => estimate.value));
  };
  const evidenceByMethod = new Set<string>();
  const stateRows = <T>(rows: ReadonlyMap<string, T>, strength: string) => {
    const suffix = `:${strength}`;
    return [...rows].flatMap(([key, row]) =>
      key.endsWith(suffix) ? [[key.slice(0, -suffix.length), row] as const] : [])
      .sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0)
      .map(([, row]) => row);
  };

  for (const [strength, indices] of [["pp", [1,2,3]], ["pk", [4,5,6]]] as const) {
    for (const { data } of stateRows(source.spatial, strength))
      if (data)
        check(indices.every(i => data.state_weights.some(weight => weight.strength === states[i] &&
          A.ledgerClose(weight.weight, [weights[i]]))), "shared spatial state weights differ");
  }
  let shootinessStatus: "complete" | "failed" | "unavailable" | undefined;
  for (const [index, ref] of references.entries()) {
    const attempts = ref.attempt_reference;
    if (attempts.kind === "spatial") {
      const rows = stateRows(source.spatial, ref.strength);
      const donors = rows.flatMap(row => row.data ? [row.data] : []);
      if (!donors.length) {
        check(rows[0] && attempts.method_id === null &&
          same(ref.attempts_per_hour, unavailable("not_computed", rows[0].explanation!)),
          "shared spatial attempts lack their pending source");
      }
      for (const donor of donors) {
        check(attempts.method_id === donor.method_id &&
          estimateMatches(ref.attempts_per_hour, unestimated(donor.offense_attempts_per60_neutral, null)),
          "shared spatial attempts differ");
        evidenceByMethod.add(donor.method_id);
      }
    }
    const panels = stateRows(source.execution, ref.strength).flatMap(row => row.data ? [row.data] : []);
    check((ref.execution_panel !== null) === (selectedScore !== undefined || panels.length > 0), "shared execution panel lacks its source");
    for (const data of panels) {
      const panel = data.reference_panel;
      check(!selectedScore || methods[data.method_id]?.evidence.some(receipt => receipt.sha256 === selectedScore.sha256),
        "selected score differs from execution donor lineage");
      check(ref.execution_panel !== null && panel.panel_id === ref.execution_panel.panel_id &&
        panel.opportunities === ref.execution_panel.opportunities &&
        A.ledgerClose(panel.setup_weight, [ref.execution_panel.setup_weight]), "shared common panel differs");
      evidenceByMethod.add(data.method_id);
    }
    for (const {data} of stateRows(source.shootiness, ref.strength)) {
      if (data === null) continue;
      const { position_group: role, coefficient_support: {status} } = data.evidence;
      check(shootinessStatus === undefined || shootinessStatus === status,
        "shared shootiness reference fit status differs");
      shootinessStatus = status;
      const expected = role === "unknown" ? null : constants[index]?.[role].p0 ?? null;
      check(same(ref.unit, data.evidence.reference_unit) &&
        ref.shootiness_reference_id === data.evidence.reference_id &&
        same(reference.inputs.shootiness_state, data.evidence.annual_state) &&
        near(data.neutral_probability.value, [expected]), "shared shootiness reference differs");
      evidenceByMethod.add(data.method_id);
    }
  }
  check((firstState.shootiness_reference_id !== null) === (shootinessStatus !== undefined) &&
    (firstState.neutral_slot_logits !== null) === (shootinessStatus === "complete"),
    "shared shootiness reference differs from its source");
  if (shootinessStatus !== "complete")
    check(firstState.setting_K.F.unavailable_reason === (shootinessStatus === "failed" ? "failed_fit" :
      shootinessStatus === "unavailable" ? "no_exposure" : "not_computed"), "shared K unavailability reason differs");
  const minor = references[4].attempt_reference;
  const penaltyDonors = [...source.penalties.values()].flatMap(row => row.data ? [row.data] : []);
  check(minor.kind === "source_pool" && (penaltyDonors.length > 0 || minor.included_seconds === 0),
    "4v5 opportunity lacks its saved minor reference");
  const { strength: _strength, kind: _kind, reduction, ...minorSupport } = minor;
  for (const donor of penaltyDonors) {
    const valuation = donor.evidence.valuation;
    check(!selectedScore || valuation.inputs.execution_score.sha256 === selectedScore.sha256,
      "selected score differs from minor reference lineage");
    check(same(minorSupport, valuation.sh_support) && same(reduction, valuation.inputs.reduction),
      "saved 4v5 minor support differs");
    evidenceByMethod.add(donor.method_id);
  }

  for (const [player, row] of ledgers) {
    const e = row.evidence;
    const position = e.depth_position;
    check(row.method_id === reference.method_id && e.annual_reference_id === reference_id,
      "player ledger and annual identity differ");
    const {forward_seconds: forward, defense_seconds: defense, unknown_seconds: unknown,
      missing_time_records: missingTime, mixed} = position;
    check((groupSeconds.get(player) ?? 0) <= forward + defense &&
      (!(forward > 0 && defense > 0) || mixed), "complete group time or mixed role differs from annual usage");
    if (position.group !== "unknown") {
      const [own, other] = position.group === "F" ? [forward, defense] : [defense, forward];
      check(unknown === 0 && (own > 0 || missingTime > 0) &&
        (mixed ? own > other && missingTime === 0 : other === 0), "recorded time and annual position differ");
    }
    const spatial = (state: string) => source.spatial.get(`${player}:${state}`)!;
    const execution = (state: string) => source.execution.get(`${player}:${state}`)!;
    const shootiness = (state: string) => source.shootiness.get(`${player}:${state}`)!;
    const penalties = source.penalties.get(player)!;
    const territory = source.territory.get(player)!;
    const inputs = {
      spatial: A.SpatialStrength.literals.map(state => binding(state, spatial(state))),
      execution: states.map(state => binding(state, execution(state))),
      shootiness: states.map(state => binding(state, shootiness(state))),
      penalties: binding(null, penalties),
      territory: binding(null, territory),
    };
    check(same(inputs, e.inputs), "copied input identities differ");
    for (const entry of [...inputs.spatial, ...inputs.execution, ...inputs.shootiness, inputs.penalties, inputs.territory])
      if (entry.method_id !== null) evidenceByMethod.add(entry.method_id);
    const support = {
      spatial: A.SpatialStrength.literals.map(strength => ({
        strength, support: spatial(strength).data?.support ?? null,
        roles: source.spatialEvidence.get(`${player}:${strength}`)!.data?.roles.map(
          ({role, coefficient_support}) => ({role, coefficient_support})) ?? null,
      })),
      execution: states.map(strength => {
        const data = execution(strength).data;
        return { strength, finishing: data?.support.finishing_goals_per100_attempts ?? null,
          setting: data?.support.setting_goals_per100_assisted_opportunities ?? null,
          coefficient_support: data?.coefficient_support ?? null, panel_id: data?.reference_panel.panel_id ?? null };
      }),
      shootiness: states.map(strength => ({
        strength, support: shootiness(strength).data?.support ?? null,
        coefficient_support: shootiness(strength).data?.evidence.coefficient_support ?? null,
      })),
      penalties: penalties.data && { support: penalties.data.support, coefficient_support: penalties.data.evidence.coefficient_support },
      territory: territory.data && { support: territory.data.support, roles: territory.data.evidence.roles },
    };
    check(same(e.dependency_support, support), "copied upstream support differs");
    const roles = new Set(states.flatMap(state => {
      const data = shootiness(state).data;
      return data ? [data.evidence.position_group] : [];
    }));
    check(roles.size <= 1 && e.unit_position === ([...roles][0] ?? "unknown") &&
      same(e.execution_states.map(state => state.strength), states), "annual shooter role or state axis differs");
    for (const [index, ref] of references.entries()) {
      const state = e.execution_states[index], skill = execution(ref.strength), shot = shootiness(ref.strength);
      const p = unestimated(shot.data?.probability, shot.explanation);
      const finishing = unestimated(skill.data?.finishing_goals_per100_attempts, skill.explanation);
      const setting = unestimated(skill.data?.setting_goals_per100_assisted_opportunities, skill.explanation);
      check(same(state.shooter_probability, p) && same(state.finishing_per100, finishing) &&
        same(state.setting_per100, setting), "copied execution skill or shooter probability differs");
      check(state.setter_share.value === null || (state.setter_share.value >= 0 && state.setter_share.value <= 1),
        "setter share is outside [0,1]");
      const k = e.unit_position === "unknown" ? p : ref.setting_K[e.unit_position];
      const missingShare = [p, k].find(estimate => estimate.value === null);
      const setterShare = missingShare ? null : .8 * stable([1, -p.value!]) * k.value!;
      check(missingShare
        ? same(state.setter_share, missingShare)
        : e.unit_position !== "unknown" && near(state.setter_share.value, [setterShare]),
        "setter share differs");
      const active = ref.hours > 0;
      check(state.use === (active ? "active" : "omitted_zero_weight"), "state workload disposition differs");
      for (const [result, share, value] of [
        [state.finishing_goals, p, finishing],
        [state.setting_goals, { ...state.setter_share, value: setterShare }, setting],
      ] as const) {
        if (!active) {
          check(result.value === 0, "omitted state is not exact zero");
          continue;
        }
        const rate = ref.attempts_per_hour;
        const missing = [rate, share, value].find(estimate => estimate.value === null);
        if (missing) {
          check(same(result, missing), "state execution contribution differs");
        } else {
          check(ref.execution_panel && ref.execution_panel.opportunities > 0,
            "available execution inputs require a supported common panel");
          const term = ref.hours * rate.value! * share.value! * value.value! / 100;
          check(rate.value === 0 ? result.value === 0 : near(result.value, [term]), "state execution contribution differs");
        }
      }
    }
    const modeled = [
      ["five_on_five_offense", spatial("5v5").data?.offense_xg_per60, spatial("5v5").explanation, 1000/60],
      ["five_on_five_defense", spatial("5v5").data?.defense_xg_per60, spatial("5v5").explanation, -1000/60],
      ["power_play_offense", spatial("pp").data?.offense_xg_per60, spatial("pp").explanation, 100/60],
      ["penalty_kill_defense", spatial("pk").data?.defense_xg_per60, spatial("pk").explanation, -100/60],
      ["penalties_drawn", penalties.data?.drawn_value_per60, penalties.explanation, 1000/60],
      ["penalties_taken", penalties.data?.taken_value_per60, penalties.explanation, 1000/60],
      ["ice_won", territory.data?.ice_won_goals_per_basket, territory.explanation, 1],
      ["ice_lost", territory.data?.ice_lost_goals_per_basket, territory.explanation, -1],
    ] as const;
    for (const [term, estimate, explanation, multiplier] of modeled)
      check(estimateMatches(row.components[term].league_goals, unestimated(estimate, explanation), multiplier),
        `${term} source value or multiplier differs`);
    for (const term of ["finishing","setting"] as const)
      check(matchingTermSum(row.components[term].league_goals, e.execution_states.map(state => state[`${term}_goals`])),
        "execution term does not close");
    const depth = position.group === "unknown" ? null : reference.positions[position.group];
    let depthProblem: A.Estimate | null = null;
    if (depth === null) {
      depthProblem = unavailable("not_applicable", "no resolved annual depth position");
    } else if (!depth.available) {
      const member = depth.missing_vectors[0];
      if (member) {
        const estimate = ledgers.get(member.player_id)!.components[member.terms[0]].league_goals;
        const detail = estimate.reason_detail!;
        depthProblem = {
          ...estimate,
          reason_detail: { ...detail, explanation: `the depth reference requires a member value that is unavailable. ${detail.explanation}` },
        };
      } else {
        depthProblem = unavailable("no_exposure", "no eligible depth time");
      }
    }
    for (const term of terms) {
      const { league_goals: league, replacement_goals: replacement } = row.components[term];
      const missing = league.value === null ? league : depthProblem;
      check(missing ? same(replacement, missing) : near(replacement.value, [league.value, -depth!.components![term]]),
        "depth subtraction differs");
    }
  }
  for (const id of evidenceByMethod) {
    const upstream = methods[id];
    check(upstream && upstream.purpose === method.purpose &&
      upstream.fit_seasons.every(year => method.fit_seasons.includes(year)) &&
      (upstream.training_cutoff === null || method.training_cutoff !== null && upstream.training_cutoff <= method.training_cutoff),
      "ledger method drops upstream fitting history");
  }
  const coverage = (role: Group) => {
    const {available, member_count, total_seconds} = reference.positions[role];
    const selected = reference.groups.filter(group => group.position === role);
    const complete_groups = selected.filter(group => group.status === "complete").length;
    return {available, member_count, total_seconds, complete_groups, excluded_groups: selected.length - complete_groups};
  };
  return {F: coverage("F"), D: coverage("D")};
};
