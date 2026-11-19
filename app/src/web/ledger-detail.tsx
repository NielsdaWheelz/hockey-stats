import { useId, useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router";
import type { Estimate, LedgerReference, Method, ValueLedger } from "../shared/player-analysis";
import { displayNumber } from "./analysis-history";
import type { ProfileView, LedgerEvidence } from "./client";
import { downloadCsv, type CsvCell } from "./export";
import { ledgerInteractions, ledgerLimits, ledgerPresentation, ledgerWorkload } from "./ledger-presentation";
import { playerName, seasonLabel } from "./presentation";

const csvHeaders = [
  "row_type", "publication_id", "season", "subject_player_id", "annual_reference_id",
  "term", "strength", "depth_group", "team_id", "member_player_id", "rank",
  "seconds", "unit", "league_value", "depth_mean", "replacement_value",
  "league_reason", "replacement_reason",
  "execution_use", "unit_position", "workload_hours", "mixture_weight_fraction",
  "neutral_team_attempts_per_hour", "attempt_rate_unavailable_reason",
  "panel_id", "panel_opportunities_count", "panel_unavailable_reason",
  "focal_shooter_probability_fraction", "focal_shooter_probability_unavailable_reason",
  "setter_share_fraction", "setter_share_unavailable_reason",
  "finishing_goals_per_100_attempts", "finishing_rate_unavailable_reason",
  "setting_goals_per_100_setup_opportunities", "setting_rate_unavailable_reason",
  "finishing_goals_per_reference_basket", "finishing_value_unavailable_reason",
  "setting_goals_per_reference_basket", "setting_value_unavailable_reason",
  "team_group_status", "team_group_exclusion_reasons", "rank_status",
  "rank_member_complete", "rank_member_depth", "depth_reference_status",
  "depth_reference_unavailable_reason", "member_vector_status", "member_missing_terms",
  "evidence",
] as const;

type ConstructionRow = {
  readonly row_type: "term" | "execution_state" | "team_rank" | "weighted_member";
} & Partial<Record<typeof csvHeaders[number], CsvCell>>;

const constructionRows = (
  response: LedgerEvidence,
  ledger: ValueLedger,
  reference: LedgerReference,
  methods: readonly Method[],
): readonly (readonly CsvCell[])[] => {
  const { evidence } = ledger;
  const group = evidence.depth_position.group;
  const identity = {
    publication_id: response.publication.publication_id, season: response.season.season,
    subject_player_id: response.selection.player_id, annual_reference_id: reference.reference_id,
  };
  const means = group === "unknown" ? null : reference.positions[group].components;
  const rows: readonly ConstructionRow[] = [
    ...ledgerPresentation.map(([, term]): ConstructionRow => {
      const { league_goals: league, replacement_goals: replacement } = ledger.components[term];
      return {
        row_type: "term", term, depth_group: group, unit: "goals_per_reference_basket",
        league_value: league.value, depth_mean: means?.[term], replacement_value: replacement.value,
        league_reason: league.unavailable_reason, replacement_reason: replacement.unavailable_reason,
        evidence: JSON.stringify({ league, replacement }),
      };
    }),
    ...([
      ["total", ledger.league_total, ledger.replacement_total],
      ["penalties_combined", ledger.penalties_combined.league_goals, ledger.penalties_combined.replacement_goals],
    ] as const).map(([term, league, replacement]): ConstructionRow => ({
      row_type: "term", term, depth_group: group, unit: "goals_per_reference_basket",
      league_value: league.value, replacement_value: replacement.value,
      league_reason: league.unavailable_reason, replacement_reason: replacement.unavailable_reason,
      evidence: JSON.stringify(term === "total" ? {
        league, replacement, workload: ledger.reference_minutes, depth_position: evidence.depth_position,
        unit_position: evidence.unit_position, inputs: evidence.inputs,
        support: evidence.dependency_support, annual_inputs: reference.inputs,
        references: { F: reference.positions.F.reason, D: reference.positions.D.reason },
        methods, sources: response.sources, uncertainty: "not_estimated",
        conventions: [ledgerInteractions, ledgerLimits, termScaling, ...executionNotes],
      } : { league, replacement }),
    })),
    ...evidence.execution_states.map((state, index): ConstructionRow => {
      const common = reference.state_references[index];
      const panel = common.execution_panel;
      return {
        row_type: "execution_state", strength: state.strength, depth_group: group,
        execution_use: state.use, unit_position: evidence.unit_position,
        workload_hours: common.hours, mixture_weight_fraction: common.mixture_weight,
        neutral_team_attempts_per_hour: common.attempts_per_hour.value,
        attempt_rate_unavailable_reason: common.attempts_per_hour.unavailable_reason,
        panel_id: panel?.panel_id, panel_opportunities_count: panel?.opportunities,
        panel_unavailable_reason: panel === null ? evidence.inputs.execution[index].explanation : null,
        focal_shooter_probability_fraction: state.shooter_probability.value,
        focal_shooter_probability_unavailable_reason: state.shooter_probability.unavailable_reason,
        setter_share_fraction: state.setter_share.value,
        setter_share_unavailable_reason: state.setter_share.unavailable_reason,
        finishing_goals_per_100_attempts: state.finishing_per100.value,
        finishing_rate_unavailable_reason: state.finishing_per100.unavailable_reason,
        setting_goals_per_100_setup_opportunities: state.setting_per100.value,
        setting_rate_unavailable_reason: state.setting_per100.unavailable_reason,
        finishing_goals_per_reference_basket: state.finishing_goals.value,
        finishing_value_unavailable_reason: state.finishing_goals.unavailable_reason,
        setting_goals_per_reference_basket: state.setting_goals.value,
        setting_value_unavailable_reason: state.setting_goals.unavailable_reason,
        evidence: JSON.stringify({ state, common_reference: common,
          execution: evidence.dependency_support.execution[index],
          shootiness: evidence.dependency_support.shootiness[index] }),
      };
    }),
    ...reference.groups.flatMap(({ members, ...team }) => (
      members.length ? members : [null]
    ).map((member): ConstructionRow => ({
      row_type: "team_rank", depth_group: team.position, team_id: team.team_id, member_player_id: member?.player_id,
      rank: member?.rank, seconds: member?.known_team_seconds ?? team.known_seconds, unit: "reported_seconds",
      team_group_status: team.status, team_group_exclusion_reasons: team.reasons.join("|"),
      rank_status: team.status === "excluded" ? "group_excluded" : member === null ? "no_member" : "ranked",
      rank_member_complete: member?.complete, rank_member_depth: member?.depth,
      evidence: JSON.stringify({ team, member }),
    }))),
    ...(["F", "D"] as const).flatMap(position => {
      const depth = reference.positions[position];
      const missing = new Map(depth.missing_vectors.map(member => [member.player_id, member.terms]));
      return depth.members.map((member): ConstructionRow => {
        const terms = missing.get(member.player_id);
        return {
          row_type: "weighted_member", depth_group: position, member_player_id: member.player_id,
          seconds: member.seconds, unit: "reported_seconds",
          depth_reference_status: depth.available ? "available" : "unavailable",
          depth_reference_unavailable_reason: depth.reason,
          member_vector_status: terms === undefined ? "complete" : "missing_terms",
          member_missing_terms: terms?.join("|"),
          evidence: JSON.stringify({ teams: member.teams, reference_seconds: depth.total_seconds,
            missing_terms: terms ?? [] }),
        };
      });
    }),
  ];
  return rows.map(row => {
    const record = { ...identity, ...row };
    return csvHeaders.map(field => record[field]);
  });
};

const estimateText = (estimate: Estimate): string => estimate.value === null
  ? estimate.unavailable_reason?.replaceAll("_", " ") ?? "unavailable"
  : displayNumber(estimate.value);

const termScaling = "5v5 spatial and penalty rates use 1,000 minutes. pp and pk rates use 100. defense and ice lost reverse the upstream against sign. taking keeps its signed value. territory values already use the 1,000-minute reference.";

const executionNotes = [
  "for each exact strength, finishing uses hours × neutral team attempts/hour × focal shooter share × finishing goals per 100 attempts / 100. setting substitutes the modeled setter share and setting goals per 100 setup opportunities.",
  "setter share is 0.8 × (1 − focal shooter share) × K. K averages over remaining neutral skaters. the team attempt rate may include ordinary goalie attempts and is allocated to skater slots.",
  "pp and reciprocal pk use league physical-time weights. zero-weight states contribute zero. active states need their own panel and inputs even when their attempt rate is zero.",
] as const;

function EvidenceTable({ columns, children, label }: {
  readonly columns: readonly string[];
  readonly children: ReactNode;
  readonly label: string;
}) {
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label={label}>
      <table>
        <thead><tr>{columns.map(column => <th scope="col" key={column}>{column}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export default function LedgerDetail({ profile, exportPending }: {
  readonly profile: ProfileView;
  readonly exportPending: boolean;
}) {
  const title = useId();
  const [status, setStatus] = useState("");
  const [groupsOpen, setGroupsOpen] = useState(false);
  const location = useLocation();
  const response = profile.ledgerEvidence;
  if (!response) return null;
  const { result } = response;
  const ledger = result.data?.ledger;
  const reference = result.data?.reference;
  const header = (
    <>
      <h3 id={title}>value ledger construction</h3>
      <p>{profile.person ? playerName(profile.person) : `player ${profile.player_id}`} · {seasonLabel(profile.season.season)}</p>
    </>
  );
  if (result.availability !== "provided" || ledger?.availability !== "provided" || reference?.availability !== "provided")
    return <section aria-labelledby={title}>{header}<p>{result.explanation ?? ledger?.explanation ?? reference?.explanation}</p></section>;

  const data = ledger.data;
  const annual = reference.data;
  const { depth_position: depth, unit_position: unit, execution_states: states, inputs, dependency_support: support } = data.evidence;
  const focal = depth.group === "unknown" ? null : annual.positions[depth.group];
  const methodIds = new Set([
    data.method_id, annual.method_id,
    ...[...inputs.spatial, ...inputs.execution, ...inputs.shootiness, inputs.penalties, inputs.territory]
      .flatMap(input => input.method_id === null ? [] : [input.method_id]),
  ]);
  const citedMethods = Object.values(response.methods).filter(method => methodIds.has(method.method_id));
  const method = response.methods[data.method_id];
  const selectedQuantity = profile.selectedMetric.quantityPath;
  const findings = method?.assessment.findings.filter(finding => selectedQuantity && finding.quantities.includes(selectedQuantity)) ?? [];
  return (
    <section aria-labelledby={title} className="ledger-detail" data-player-id={profile.player_id}>
      {header}
      <p>{ledgerWorkload}. {ledgerLimits}</p>
      <p>viewing cutoffs use 300 minutes for general quantities and 50 for pp and pk by default. each field has its own qualification time.</p>
      <p>{ledgerInteractions}</p>
      <p>{termScaling}</p>
      {findings.map((finding, i) => <p key={i}>{finding.summary}</p>)}
      <EvidenceTable label="signed terms and depth subtraction" columns={[
        "component", "league goals", "depth mean", "replacement goals", "source quantity",
      ]}>
        {ledgerPresentation.map(([label, term, metric]) => {
          const values = data.components[term];
          const next = new URLSearchParams(location.search);
          next.set("view", "analytical");
          next.set("metric", metric);
          const sourceLabel = term === "finishing" || term === "setting"
            ? `standalone 5v5 ${term} skill` : `${label} source quantity`;
          return <tr data-ledger-term={term} key={term}>
            <th scope="row">{label}</th>
            <td>{estimateText(values.league_goals)}</td>
            <td>{displayNumber(focal?.components?.[term] ?? null)}</td>
            <td>{estimateText(values.replacement_goals)}</td>
            <td><Link to={`${location.pathname}?${next}`} state={location.state}>{sourceLabel}</Link></td>
          </tr>;
        })}
        <tr><th scope="row">combined penalties</th><td>{estimateText(data.penalties_combined.league_goals)}</td><td>—</td><td>{estimateText(data.penalties_combined.replacement_goals)}</td><td>drawing + taking</td></tr>
        <tr><th scope="row">total</th><td>{estimateText(data.league_total)}</td><td>—</td><td>{estimateText(data.replacement_total)}</td><td>ten terms</td></tr>
      </EvidenceTable>

      <h4>finishing and inferred setting by exact strength</h4>
      <p>shootiness unit position: {unit === "unknown" ? "unresolved" : unit}.</p>
      {executionNotes.map(note => <p key={note}>{note}</p>)}
      <EvidenceTable label="seven-state execution construction" columns={[
        "strength", "workload hours", "neutral team attempts/hour", "panel opportunities",
        "focal shooter share", "setter share", "finishing / 100 attempts",
        "setting / 100 setups", "finishing goals", "setting goals",
      ]}>
        {states.map((state, i) => {
          const common = annual.state_references[i];
          return <tr data-ledger-state={state.strength} key={state.strength}>
            <th scope="row">{state.strength}{state.use === "omitted_zero_weight" ? " · omitted" : ""}</th>
            <td>{displayNumber(common.hours)}</td>
            <td>{estimateText(common.attempts_per_hour)}</td>
            <td>{displayNumber(common.execution_panel?.opportunities ?? null)}</td>
            <td>{estimateText(state.shooter_probability)}</td>
            <td>{estimateText(state.setter_share)}</td>
            <td>{estimateText(state.finishing_per100)}</td>
            <td>{estimateText(state.setting_per100)}</td>
            <td>{estimateText(state.finishing_goals)}</td>
            <td>{estimateText(state.setting_goals)}</td>
          </tr>;
        })}
      </EvidenceTable>
      <details>
        <summary>exact-state dependencies and model support</summary>
        {states.map((state, i) => {
          const common = annual.state_references[i];
          const skill = support.execution[i];
          const usage = support.shootiness[i];
          const source = common.attempt_reference;
          return <section key={state.strength}>
            <h5>{state.strength}</h5>
            <p>{common.unit.forwards} forwards / {common.unit.defenders} defenders · time weight {displayNumber(common.mixture_weight)} · K (F) {estimateText(common.setting_K.F)} · K (D) {estimateText(common.setting_K.D)}.</p>
            <p>{source.kind === "source_pool"
              ? `matched source pool · ${source.attempts} attempts / ${source.included_seconds} seconds · known excluded seconds ${source.known_excluded_seconds}${source.unquantified_gap ? " · additional unquantified gaps" : ""}`
              : `neutral spatial team rate · ${source.method_id ?? "source unavailable"}`}.</p>
            <ul>
              {([["finishing", skill.finishing], ["setting", skill.setting], ["shootiness", usage.support]] as const).map(([label, row]) =>
                <li key={label}>{label} · {row
                  ? `${row.included_seconds ?? "unknown"} included seconds · ${row.prior_only ? "prior-only hypothetical role" : row.current_season_information ? "current-season information" : "no current-season information"}`
                  : "source/model support unavailable"}</li>)}
            </ul>
            <pre>{JSON.stringify({
              reference: common, execution: inputs.execution[i], shootiness: inputs.shootiness[i],
              support: { execution: skill, shootiness: usage },
              estimates: state,
            }, null, 2)}</pre>
          </section>;
        })}
        <h5>spatial, penalty and territory dependencies</h5>
        <pre>{JSON.stringify({
          spatial: inputs.spatial, penalties: inputs.penalties, territory: inputs.territory,
          support: { spatial: support.spatial, penalties: support.penalties, territory: support.territory },
        }, null, 2)}</pre>
        <h5>bound model methods and sources</h5>
        {citedMethods.map(body => <details key={body.method_id}>
          <summary>{body.method_id}</summary><pre>{JSON.stringify(body, null, 2)}</pre>
        </details>)}
        {Object.values(response.sources).map(body => <details key={body.source_id}>
          <summary>{body.source_id}</summary><pre>{JSON.stringify(body, null, 2)}</pre>
        </details>)}
        <pre>{JSON.stringify(annual.inputs, null, 2)}</pre>
      </details>

      <h4>reported-usage depth reference</h4>
      <p>profile position {profile.person?.reported_position ?? "unavailable"} · annual depth position {depth.group} · shootiness unit position {unit}.</p>
      <p>reported seconds by role: {depth.forward_seconds} forward / {depth.defense_seconds} defense / {depth.unknown_seconds} unresolved · {depth.missing_time_records} missing time records{depth.mixed ? " · mixed roles" : ""}.</p>
      <p>complete team-position groups supply forwards ranked below the top 12 and defense below the top 6. cutoff ties stay regular. each player subtracts their own F/D depth mean. means pool regularized estimates, so thin members and cross-position gaps inherit shrinkage assumptions.</p>
      <EvidenceTable label="depth reference coverage" columns={[
        "position", "complete groups", "excluded groups", "weighted skaters", "reported minutes", "reference",
      ]}>
        {(["F", "D"] as const).map(group => {
          const groups = annual.groups.filter(entry => entry.position === group);
          const complete = groups.filter(entry => entry.status === "complete").length;
          const baseline = annual.positions[group];
          return <tr key={group}>
            <th scope="row">{group}</th><td>{complete}</td><td>{groups.length - complete}</td>
            <td>{baseline.member_count}</td><td>{displayNumber(baseline.total_seconds / 60)}</td>
            <td>{baseline.available ? "available" : baseline.reason}</td>
          </tr>;
        })}
      </EvidenceTable>
      <details onToggle={event => setGroupsOpen(event.currentTarget.open)}>
        <summary>team ranks, exclusions and weighted members</summary>
        {groupsOpen && <>
          <EvidenceTable label="team-position groups and ranks" columns={[
            "team / position", "status", "supported / scheduled games", "known seconds / cutoff seconds", "excluded evidence", "player ranks",
          ]}>
            {annual.groups.map(group => <tr key={`${group.team_id}-${group.position}`}>
              <th scope="row">{group.team_id} / {group.position}</th>
              <td>{group.status}</td><td>{group.supported_games} / {group.inventory_games}</td>
              <td>{group.known_seconds} / {group.cutoff_seconds ?? "none"}</td>
              <td>{group.reasons.join(", ") || "none"} · {group.missing_time_records} missing time records
                {group.unquantified_gap && " · unquantified gap"}
                {group.affected_games.length > 0 && <p>games {group.affected_games.join(", ")}</p>}
                {group.affected_players.length > 0 && <p>players {group.affected_players.join(", ")}</p>}
              </td>
              <td>{group.members.length ? <ul>{group.members.map(member => <li key={member.player_id}>
                {member.player_id} · {member.known_team_seconds}s · {member.rank === null ? "rank unavailable" : `rank ${member.rank}`}
                {member.depth && " · depth"}{!member.complete && " · incomplete"}
              </li>)}</ul> : "none"}</td>
            </tr>)}
          </EvidenceTable>
          {(["F", "D"] as const).map(group => {
            const position = annual.positions[group];
            const missing = new Map(position.missing_vectors.map(member => [member.player_id, member.terms]));
            return <section key={group}>
              <h5>{group} weighted depth skaters</h5>
              <EvidenceTable label={`${group} weighted skaters and team contributions`} columns={[
                "player", "seconds", "team contributions (seconds)", "unavailable terms",
              ]}>
                {position.members.map(member => <tr key={member.player_id}>
                  <th scope="row">{member.player_id}</th><td>{member.seconds}</td>
                  <td>{member.teams.map(team => `${team.team_id} (${team.seconds})`).join(" · ")}</td>
                  <td>{missing.get(member.player_id)?.join(", ") ?? "none"}</td>
                </tr>)}
              </EvidenceTable>
            </section>;
          })}
        </>}
      </details>
      <button type="button" disabled={exportPending} onClick={() => {
        try {
          downloadCsv(csvHeaders, constructionRows(response, data, annual, citedMethods),
            `hockey-stats-${annual.season}-${profile.player_id}-ledger-construction.csv`);
          setStatus("ledger construction csv prepared");
        } catch {
          setStatus("ledger construction csv failed. retry the download.");
        }
      }}>download ledger construction csv</button>
      <p role="status">{status}</p>
    </section>
  );
}
