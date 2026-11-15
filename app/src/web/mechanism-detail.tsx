import type { PenaltyEvidence, ShootinessEvidence } from "../shared/player-analysis";

type Evidence = typeof PenaltyEvidence.Type | typeof ShootinessEvidence.Type;
const number = (value: number | null) => value === null ? "unavailable" : value.toLocaleString("en-US", {maximumFractionDigits: 6});

export function MechanismDetail({evidence}: {readonly evidence: Evidence}) {
  const coefficient = evidence.coefficient_support;
  return <div className="mechanism-detail">
    <p>coefficient {coefficient.status}; current-season information {coefficient.current_season_information ? "yes" : "no"}; prior-only {coefficient.prior_only ? "yes" : "no"}; prior {coefficient.prior_kind ?? "unavailable"}; anchor {coefficient.prior_anchor_season ?? "none"}; borrowed seasons {coefficient.prior_seasons.join(", ") || "none"}. calibrated uncertainty and optimizer accuracy are unknown.</p>
    {"valuation" in evidence ? <>
      <p>complete team-award rates: drawing {number(evidence.drawn_complete_per60)}, taking {number(evidence.taken_complete_per60)}; neutral {number(evidence.neutral_per60)} awards per60. drawing/taking differences subtract that neutral rate. positive taking difference means more team penalties.</p>
      <div className="table-scroll" role="region" tabIndex={0} aria-label="isolated ordinary-minor value reference, scroll horizontally">
        <table><caption>isolated two-minute opportunity reference</caption><thead><tr><th scope="col">quantity</th><th scope="col">value</th><th scope="col">unit</th></tr></thead>
          <tbody>{([
            ["a · neutral 5v4 offense", evidence.valuation.a, "xg/hour"], ["b · source-pooled 4v5 offense", evidence.valuation.b, "xg/hour"],
            ["e_f · neutral 5v5 offense", evidence.valuation.e_f, "xg/hour"], ["e_a · neutral 5v5 against", evidence.valuation.e_a, "xg/hour"],
            ["T · maximum opportunity", evidence.valuation.T_hours, "hours"], ["tau · expected opportunity", evidence.valuation.tau_hours, "hours"],
            ["V · signed isolated-minor value", evidence.valuation.V_goals, "goals"],
          ] as const).map(([label,value,unit]) => <tr key={label}><th scope="row">{label}</th><td className="numeric">{number(value)}</td><td>{unit}</td></tr>)}</tbody>
        </table>
      </div>
      <p>matched sh support: {number(evidence.valuation.sh_support.included_seconds / 60)} included minutes; {evidence.valuation.sh_support.attempts} attempts; {number(evidence.valuation.sh_support.neutral_goal_mass)} neutral goal mass; {number(evidence.valuation.sh_support.known_excluded_seconds / 60)} known excluded minutes; unquantified gap {evidence.valuation.sh_support.unquantified_gap ? "yes" : "no"}. {evidence.valuation.available ? "valuation available, including zero or negative value" : `valuation unavailable: ${evidence.valuation.reason?.replaceAll("_", " ")}`}.</p>
      <p>the isolated-minor approximation omits overlap, 5v3, regulation truncation and focal specialty skill. source-pooled sh circumstances differ from hypothetical ev/pp references. a pp goal ends the opportunity; a sh goal does not. taking value = −taking difference × V; V can be negative.</p>
    </> : <>
      <p>share of team attempts conditions on an attempt occurring. common unit: {evidence.reference_unit.forwards} forwards / {evidence.reference_unit.defenders} defenders; focal position {evidence.position_group}. pooled seven-state candidate information: {coefficient.likelihood_events} choices. neither the modeled probability nor its qualifying minutes is observed shot share or finishing.</p>
      <div className="table-scroll" role="region" tabIndex={0} aria-label="exact-state shootiness qualification and pooled candidate information, scroll horizontally">
        <table><caption>exact-state minutes qualify cohorts; pooled candidate choices inform one shared coefficient</caption>
          <thead><tr><th scope="col">strength</th><th scope="col">qualifying min</th><th scope="col">excluded min</th><th scope="col">gap</th><th scope="col">candidate choices</th><th scope="col">personal attempts</th><th scope="col">excluded possible choices</th></tr></thead>
          <tbody>{evidence.states.map(state => <tr key={state.strength}><th scope="row">{state.strength}</th><td>{number(state.included_seconds / 60)}</td><td>{number(state.known_excluded_seconds / 60)}</td><td>{state.unquantified_gap ? "yes" : "no"}</td><td>{state.team_choices}</td><td>{state.personal_attempts}</td><td>{state.excluded_possible_choices}</td></tr>)}</tbody>
        </table>
      </div>
    </>}
  </div>;
}
