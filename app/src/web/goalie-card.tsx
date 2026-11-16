import { useState } from "react";
import { Link } from "react-router";
import type {
  GoalieDanger,
  GoalieObserved,
  GoalieObservedSummary,
  Method,
  Person,
  MapsResponse,
} from "../shared/player-analysis";
import type { ProfileView } from "./client";
import type { PeerSettings } from "./explorer";
import {
  analysisMetric,
  goalieFields,
  selectHistoryValue,
  selectLeagueValues,
  type AnalysisMetricId,
} from "./analysis-values";
import {
  buildAnalysisCohort,
  type AnalysisPeerGroup,
} from "./analysis-cohorts";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  displayNumber,
  displayValue,
  plotDomain,
  prepareHistory,
  prepareHistoryPoint,
  standingText,
  valueText,
  HistoryPlot,
  type AnalysisRow,
  type HistoryPoint,
} from "./analysis-history";
import {
  AnalyticalMapDrawing,
  AnalyticalMapLegend,
  analyticalMapDrawingSvg,
  prepareAnalyticalMap,
  type AnalyticalMapModel,
} from "./analytical-map";
import {
  GoalieMapDrawing,
  GoalieMapLegend,
  GoalieDangerPlot,
  goalieDangerDrawingSvg,
  goalieSupportText,
  goalieRatioScaleText,
  prepareGoalieEvidenceMap,
  type GoalieEvidenceMapModel,
} from "./goalie-evidence";
import { csvText, downloadBlob, svgPng, type CsvCell } from "./export";
import { playerName, seasonLabel, teamName } from "./presentation";

export const goalieSkills = [
  {
    field: "miss_probability",
    label: "miss",
    condition: "given an unblocked opportunity",
    slot: "g09",
  },
  {
    field: "recorded_stop_probability",
    label: "recorded stop",
    condition: "given on-net; recorded stopped-save proxy, not save percentage",
    slot: "g10",
  },
  {
    field: "conversion_probability",
    label: "conversion after no recorded stop",
    condition: "given on-net with no recorded stop; higher allows more goals",
    slot: "g11",
  },
  {
    field: "recorded_reattempt_probability",
    label: "recorded reattempt",
    condition:
      "neutral saved-shot weighting; immediately next same-team ordinary attempt, same period, 0–5 seconds",
    slot: "g12",
  },
  {
    field: "reattempt_neutral_goal_probability",
    label: "conditional successor danger",
    condition: "given recorded reattempt; fully neutral successor probability",
    slot: "g12",
  },
  {
    field: "followup_danger",
    label: "joint follow-up danger",
    condition:
      "per neutral saved-shot opportunity; E[h*d], not product of separate means",
    slot: "g12",
  },
] as const;
export { goalieFields };
export const goalieTypes = [
  { type: "wrist_snap", label: "wrist + snap" },
  { type: "slap", label: "slap" },
  { type: "tip", label: "tip / deflection" },
  { type: "backhand", label: "backhand" },
] as const;
type Field = {
  readonly field: (typeof goalieFields)[number];
  readonly slot: string;
  readonly row: AnalysisRow;
  readonly group: AnalysisPeerGroup;
  readonly domain: readonly [number, number] | null;
};
export type GoalieRawFact = {
  readonly section: string;
  readonly slot: string;
  readonly path: string;
  readonly value: CsvCell;
  readonly unit: string;
  readonly support: unknown;
  readonly reason: string | null;
  readonly methodId: string | null;
  readonly reference: string | null;
  readonly sourceId: string | null;
};
export type GoalieCardModel = {
  readonly profile: ProfileView;
  readonly playerId: string;
  readonly render: "contours" | "rectangles";
  readonly name: string;
  readonly companion: string | null;
  readonly fields: readonly Field[];
  readonly history: readonly HistoryPoint[];
  readonly modeledMap: AnalyticalMapModel;
  readonly actualMap: GoalieEvidenceMapModel;
  readonly typeMaps: readonly {
    readonly type: string;
    readonly label: string;
    readonly map: GoalieEvidenceMapModel;
  }[];
  readonly otherMap: GoalieEvidenceMapModel | null;
  readonly observed: typeof GoalieObserved.Type | null;
  readonly observedReason: string | null;
  readonly danger: typeof GoalieDanger.Type | null;
  readonly dangerReason: string | null;
  readonly rawFacts: readonly GoalieRawFact[];
  readonly footer: readonly string[];
};

export function goalieObservedFacts(
  observed: typeof GoalieObservedSummary.Type,
  methods: Readonly<Record<string, typeof Method.Type>>,
): readonly GoalieRawFact[] {
  const rawFacts: GoalieRawFact[] = [];
  const add = (
    section: string,
    slot: string,
    path: string,
    value: CsvCell,
    unit: string,
    support: unknown,
    reason: string | null = null,
    methodId: string | null = null,
    reference: string | null = null,
    sourceId: string | null = null,
  ) =>
    rawFacts.push({
      section,
      slot,
      path,
      value,
      unit,
      support,
      reason: value === null ? (reason ?? "source field unavailable") : null,
      methodId,
      reference,
      sourceId,
    });
  for (const source of ["source_counts", "reported_boxscore_counts"] as const) {
    const counts = observed[source];
    for (const field of [
      "unblocked_attempts",
      "misses",
      "shots_on_goal",
      "saves",
      "goals_against",
    ] as const)
      add(
        "source",
        "g03",
        `goalie_observed.${source}.${field}`,
        counts[field],
        "count",
        counts.support,
        "source count unavailable",
        null,
        source === "source_counts"
          ? "recorded event source"
          : "separately reported official totals",
        counts.provenance.id,
      );
    add(
      "source",
      "g03",
      `goalie_observed.${source}.save_percentage.value`,
      counts.save_percentage.value,
      "fraction",
      counts.support,
      counts.save_percentage.reason_detail?.explanation ??
        counts.save_percentage.unavailable_reason,
      null,
      "recorded saves / on-net source count",
      counts.provenance.id,
    );
    add(
      "source",
      "g03",
      `goalie_observed.${source}.provenance`,
      JSON.stringify(counts.provenance),
      "source reference",
      counts.support,
      null,
      null,
      null,
      counts.provenance.id,
    );
  }
  for (const population of ["unblocked", "on_net"] as const) {
    const key =
        population === "unblocked" ? "unblocked_evidence" : "on_net_evidence",
      row = observed[key];
    const reference = methods[row.method_id]?.reference ?? null;
    for (const field of ["attempts", "goals", "expected_goals"] as const)
      add(
        "paired",
        "g04",
        `goalie_observed.${key}.${field}`,
        row[field],
        field === "attempts" ? "attempts" : "goals",
        row.support,
        null,
        row.method_id,
        reference,
      );
    for (const field of [
      "goals_saved_above_expected",
      "goals_per100_expected",
      "mean_goal_probability",
      "league_mean_goal_probability",
      "difficulty_relative_percent",
    ] as const)
      add(
        field.includes("probability") || field === "difficulty_relative_percent"
          ? "difficulty"
          : "paired",
        field.includes("probability") || field === "difficulty_relative_percent"
          ? "g05"
          : "g04",
        `goalie_observed.${key}.${field}.value`,
        row[field].value,
        field.includes("probability")
          ? "fraction"
          : field === "goals_saved_above_expected"
            ? "goals"
            : field === "goals_per100_expected"
              ? "goals per100 expected"
              : "percent",
        row.support,
        row[field].reason_detail?.explanation ?? row[field].unavailable_reason,
        row.method_id,
        reference,
      );
  }
  const onNet = observed.on_net_evidence;
  add(
    "paired",
    "g04",
    "goalie_observed.on_net_evidence.expected_save_fraction.value",
    onNet.expected_save_fraction.value,
    "fraction",
    onNet.support,
    onNet.expected_save_fraction.reason_detail?.explanation ??
      onNet.expected_save_fraction.unavailable_reason,
    onNet.method_id,
    methods[onNet.method_id]?.reference ?? null,
  );
  for (const field of [
    "starts",
    "relief_appearances",
    "unknown_start_status",
  ] as const)
    add(
      "workload",
      "g01",
      `goalie_observed.${field}`,
      observed[field],
      "appearances",
      observed.coverage,
      null,
      null,
      "reported workload",
      observed.provenance.id,
    );
  for (const field of [
    "positive_toi_appearances",
    "reported_seconds",
    "listed_games",
    "supported_games",
    "missing_games",
  ] as const)
    add(
      "workload",
      "g01",
      `goalie_observed.reported_usage.${field}`,
      observed.reported_usage[field],
      field === "reported_seconds" ? "seconds" : "count",
      observed.reported_usage.support,
      "reported workload field unavailable",
      null,
      "reported workload",
      observed.reported_usage.provenance.id,
    );
  add(
    "workload",
    "g01",
    "goalie_observed.reported_usage.minutes_per_appearance.value",
    observed.reported_usage.minutes_per_appearance.value,
    "minutes per appearance",
    observed.reported_usage.support,
    observed.reported_usage.minutes_per_appearance.reason_detail?.explanation ??
      observed.reported_usage.minutes_per_appearance.unavailable_reason,
    null,
    "reported workload",
    observed.reported_usage.provenance.id,
  );
  return rawFacts;
}

export function prepareGoalieCard(
  profile: ProfileView,
  settings: PeerSettings,
  options: {
    readonly render?: "contours" | "rectangles";
    readonly companion?: Person;
  } = {},
): GoalieCardModel {
  const selection = profile.goalieSelection;
  if (profile.kind !== "goalie" || !selection)
    throw new Error(
      "goalie card requires the publication's goalie identity and selection",
    );
  const year = profile.detail.history.find(
    (row) => row.season.season === profile.season.season,
  );
  const overview = profile.goalieOverviewCohorts.find(
    (row) => row.season.season === profile.season.season,
  );
  if (!year || !overview)
    throw new Error(
      "goalie card is missing its selected annual identity or cohort",
    );
  const fields = goalieFields.map((field) => {
    const metric = analysisMetric(`goalie.${selection.coreStrength}.${field}`)!;
    const datum = selectHistoryValue(year, overview, metric, profile.player_id);
    const group = buildAnalysisCohort(
      selectLeagueValues(overview, metric),
      [datum],
      settings,
    ).groups[0];
    const selected = group.selected[0];
    const row: AnalysisRow = {
      datum,
      standing: selected.standing,
      member: group.members.some((peer) => peer.playerId === profile.player_id),
      incompatiblePeerCount: group.incompatiblePeerCount,
    };
    const values = [...group.members, datum]
      .map(displayValue)
      .filter((value): value is number => value !== null);
    const domain = values.length
      ? plotDomain(
          field.endsWith("_difference") ||
            field === "stopping_goals_per100_on_net"
            ? [0, ...values]
            : values,
        )
      : null;
    return {
      field,
      slot:
        field === "stopping_goals_per100_on_net"
          ? "g02"
          : goalieSkills.find((skill) => field.startsWith(skill.field))!.slot,
      row,
      group,
      domain,
    };
  });
  const stoppingMetric = analysisMetric(
    `goalie.${selection.coreStrength}.stopping_goals_per100_on_net`,
  )!;
  const history = profile.detail.history.map((annual) => {
    const cohort = profile.goalieOverviewCohorts.find(
      (row) => row.season.season === annual.season.season,
    );
    if (!cohort)
      throw new Error("goalie card is missing an annual stopping cohort");
    return prepareHistoryPoint(
      { ...annual, cohort },
      profile.detail,
      stoppingMetric,
      profile.player_id,
      settings,
    ).point;
  });
  const modeled = profile.goalieMaps.find(
    (response) =>
      response.family === "goalie_stopping" &&
      response.selection.strength === selection.coreStrength,
  );
  const actual = (type: string) =>
    profile.goalieMaps.find(
      (response) =>
        response.family === "goalie_evidence" &&
        response.selection.strength === selection.evidenceStrength &&
        response.selection.population === selection.population &&
        response.selection.type === type,
    );
  const main = actual("all");
  if (!modeled || !main)
    throw new Error(
      "goalie card is missing a required overview map; refusing an incomplete export",
    );
  const typeMaps = goalieTypes.map(({ type, label }) => {
    const response = actual(type);
    if (!response)
      throw new Error(`goalie card is missing its required ${type} map`);
    return {
      type,
      label,
      map: prepareGoalieEvidenceMap(response, profile.player_id),
    };
  });
  if (!profile.goalieEvidence)
    throw new Error(
      "goalie card is missing its selected actual evidence response",
    );
  const payload = profile.goalieEvidence.result;
  const data = payload?.availability === "provided" ? payload.data : null;
  const observed =
    data?.observed.availability === "provided" ? data.observed.data : null;
  const danger =
    data?.danger.availability === "provided" ? data.danger.data : null;
  const modeledMap = prepareAnalyticalMap(modeled, profile.player_id);
  const actualMap = prepareGoalieEvidenceMap(main, profile.player_id);
  const other = actual("other");
  if (!other)
    throw new Error(
      "goalie card is missing its required other-type evidence response",
    );
  const otherMap = prepareGoalieEvidenceMap(other, profile.player_id);
  const rawFacts: GoalieRawFact[] = observed
    ? [...goalieObservedFacts(observed, profile.detail.methods)]
    : [];
  const add = (
    section: string,
    slot: string,
    path: string,
    value: CsvCell,
    unit: string,
    support: unknown,
    reason: string | null = null,
    methodId: string | null = null,
    reference: string | null = null,
    sourceId: string | null = null,
  ) =>
    rawFacts.push({
      section,
      slot,
      path,
      value,
      unit,
      support,
      reason: value === null ? (reason ?? "source field unavailable") : null,
      methodId,
      reference,
      sourceId,
    });
  for (const { type, map } of [
    { type: "all", map: actualMap },
    ...typeMaps,
    ...(otherMap ? [{ type: "other", map: otherMap }] : []),
  ])
    if (map.data)
      for (const source of ["totals", "unmapped"] as const)
        for (const field of ["attempts", "goals", "expected_goals"] as const)
          add(
            "type",
            type === "all" ? "g06" : "g07",
            `goalie_evidence_map[type=${type}].${source}.${field}`,
            map.data[source][field],
            field === "attempts" ? "attempts" : "goals",
            map.data.support,
            null,
            map.data.method_id,
            map.data.reference,
          );
  if (danger)
    for (const field of ["attempts", "goals", "expected_goals"] as const)
      add(
        "danger_totals",
        "g08",
        `goalie_danger.totals.${field}`,
        danger.totals[field],
        field === "attempts" ? "attempts" : "goals",
        danger.support,
        null,
        danger.method_id,
        profile.detail.methods[danger.method_id]?.reference ?? null,
      );
  const methods = [
    ...new Set(
      fields.flatMap((field) =>
        field.row.datum.methods.map((method) => method.method_id),
      ),
    ),
  ];
  const footer = [
    `modeled ${selection.coreStrength}; actual ${selection.evidenceStrength} / ${selection.population}; ${selection.evidenceView === "mass" ? "additive saving density" : "league-relative ratio"}; detail type ${selection.type}.`,
    "experimental season-level stopping, not overall goalie value. stopping uses neutral miss weights and excludes focal miss effects. subskills do not add to stopping.",
    "recorded stop and immediate-next-event reattempt are source proxies, not ordinary save percentage or demonstrated physical rebound control. never skip an intervening event.",
    "calibrated player uncertainty is unavailable. population distributions show raw peer spread, not confidence intervals; higher conditional values are not automatically favorable.",
    "current supported elapsed minutes qualify peers independently of likelihood/reference masses. no carried seasons means an entry prior; carried seasons record borrowing; mixed and fully current head support remain in detail.",
    "10ft descriptive pooling precedes drawing; map texture does not imply independently fitted goalie spatial coefficients. ratio cells are masked when undefined and volatile at small expected mass.",
    `methods: ${methods.join("; ") || "not available"}.`,
    ...new Set(
      fields.flatMap((field) =>
        field.row.datum.findings.map((finding) => finding.summary),
      ),
    ),
    `publication ${profile.publication.publication_id} · ${profile.publication.purpose}${actualMap.companion ? `; shared corresponding map scales with player ${actualMap.companion}` : ""}.`,
  ];
  const identity =
    profile.person ??
    profile.detail.history.find((row) => row.person !== null)?.person;
  if (options.companion)
    footer.push(
      `comparison companion ${playerName(options.companion)} (player ${options.companion.player_id}); corresponding maps retain shared scales.`,
    );
  return {
    profile,
    playerId: profile.player_id,
    render: options.render ?? "contours",
    name: identity ? playerName(identity) : `player ${profile.player_id}`,
    companion: actualMap.companion,
    fields,
    history,
    modeledMap,
    actualMap,
    typeMaps,
    otherMap,
    observed,
    observedReason: observed
      ? null
      : (data?.observed.explanation ??
        payload?.explanation ??
        "goalie evidence is unavailable"),
    danger,
    dangerReason: danger
      ? null
      : (data?.danger.explanation ??
        payload?.explanation ??
        "danger evidence is unavailable"),
    rawFacts,
    footer,
  };
}

const disposition = (row: AnalysisRow) =>
  row.datum.value !== null
    ? valueText(row.datum)
    : (row.datum.reason ?? row.datum.status);
export function GoalieDistribution({ field }: { readonly field: Field }) {
  const { row, group, domain } = field;
  const x = (value: number) =>
    20 + (260 * (value - domain![0])) / (domain![1] - domain![0]);
  return (
    <div className="goalie-distribution">
      {domain ? (
        <svg
          viewBox="0 0 300 82"
          role="img"
          aria-label={`raw ${row.datum.metric.label} peer distribution`}
        >
          <path d="M20 34H280" stroke="#64767b" />
          {domain[0] <= 0 && domain[1] >= 0 && (
            <path d={`M${x(0)} 10V51`} stroke="#64767b" strokeDasharray="3 3" />
          )}
          {group.members.map((peer) => (
            <path
              key={peer.playerId}
              d={`M${x(displayValue(peer)!)} 20V48`}
              stroke="#9eaeae"
            >
              <title>{`${peer.person?.display_name ?? peer.playerId}: ${valueText(peer)}`}</title>
            </path>
          ))}
          {row.datum.value !== null && (
            <circle
              cx={x(displayValue(row.datum)!)}
              cy="34"
              r="6"
              fill="#145a66"
              stroke="#fbfaf6"
              strokeWidth="1.5"
            >
              <title>{`${row.member ? "selected cohort member" : "selected outsider"}: ${valueText(row.datum)}`}</title>
            </circle>
          )}
          <text x="20" y="72" fontSize="12">
            {displayNumber(domain[0])}
          </text>
          <text x="280" y="72" fontSize="12" textAnchor="end">
            {displayNumber(domain[1])}
          </text>
        </svg>
      ) : (
        <p>no finite peer or selected value; distribution unavailable</p>
      )}
      <p>
        {group.peerGroup}; n={group.members.length}; ≥
        {group.cutoffMinutes ?? "unknown"} supported min ·{" "}
        {standingText(row.standing)}
        {row.member === false ? "; selected outsider" : ""}.
      </p>
    </div>
  );
}

const unmappedText = (model: GoalieEvidenceMapModel): string =>
  model.data
    ? `unmapped ${model.data.unmapped.attempts} attempts; ${displayNumber(model.data.unmapped.expected_goals - model.data.unmapped.goals)} goals saved.`
    : "unmapped evidence unavailable";

export default function GoalieCard({
  model,
  detailLink,
}: {
  readonly model: GoalieCardModel;
  readonly detailLink?: (id: AnalysisMetricId) => {
    readonly to: string;
    readonly state?: unknown;
  };
}) {
  const [status, setStatus] = useState("");
  const { profile, observed } = model;
  const selection = profile.goalieSelection!;
  const stopping = model.fields[0];
  const fieldLabel = (field: Field, label: string) =>
    detailLink ? (
      <Link {...detailLink(field.row.datum.metric.id)}>{label}</Link>
    ) : (
      label
    );
  return (
    <section
      className="goalie-card"
      aria-label={`${model.name} complete goalie sheet`}
    >
      <header data-goalie-slot="g01">
        <p className="analytical-kicker">
          {profile.publication.purpose === "fixture" && "synthetic fixture · "}
          experimental goalie sheet
        </p>
        <h3>{model.name}</h3>
        <p>
          {seasonLabel(profile.season.season)} ·{" "}
          {profile.person?.teams.map(teamName).join(" / ") ||
            "selected-season teams unavailable"}
        </p>
        {observed ? (
          <p>
            {observed.reported_usage.positive_toi_appearances} reported
            appearances · {observed.starts} starts /{" "}
            {observed.relief_appearances} relief /{" "}
            {observed.unknown_start_status} unknown start status ·{" "}
            {observed.reported_usage.reported_seconds === null
              ? "unavailable"
              : displayNumber(
                  observed.reported_usage.reported_seconds / 60,
                )}{" "}
            reported min ·{" "}
            {displayNumber(
              observed.reported_usage.minutes_per_appearance.value,
            )}{" "}
            min/appearance
          </p>
        ) : (
          <p>{model.observedReason}</p>
        )}
        <p>
          selected {selection.coreStrength} supported minutes:{" "}
          {stopping.row.datum.qualificationSeconds === null
            ? "unavailable"
            : displayNumber(stopping.row.datum.qualificationSeconds / 60)}
          ; qualification is not likelihood exposure.
        </p>
      </header>
      <div className="goalie-stopping-belt" data-goalie-slot="g02">
        <section>
          <h4>
            {fieldLabel(
              stopping,
              `${selection.coreStrength} common-reference stopping`,
            )}
          </h4>
          <p className="goalie-headline">
            {disposition(stopping.row)}{" "}
            <span>
              goals prevented / 100 common-reference on-net opportunities
            </span>
          </p>
          <GoalieDistribution field={stopping} />
          <p>{goalieSupportText(stopping.row.datum.support)}</p>
          <p>
            positive means favorable stopping; calibrated player uncertainty
            unavailable.
          </p>
        </section>
        <section data-goalie-slot="g14">
          <h4>three-season raw stopping</h4>
          <HistoryPlot
            view={{
              publication: profile.publication,
              metric: stopping.row.datum.metric,
              selectedSeason: profile.season.season,
              scale: "raw",
              points: model.history,
            }}
          />
          <p>
            this fixed raw stopping plot keeps the core ev/pk strength when
            detail changes.
          </p>
        </section>
      </div>
      <section className="goalie-skill-section">
        <h4>
          six conditional subskills · level and focal-minus-neutral difference
        </h4>
        <div className="goalie-skills">
          {goalieSkills.map((skill) => {
            const level = model.fields.find(
              (field) => field.field === skill.field,
            )!;
            const difference = model.fields.find(
              (field) => field.field === `${skill.field}_difference`,
            )!;
            return (
              <section key={skill.field} data-goalie-slot={skill.slot}>
                <h5>{fieldLabel(difference, skill.label)}</h5>
                <p>
                  <strong>
                    {disposition(level.row)}
                    {level.row.datum.value !== null ? "%" : ""}
                  </strong>{" "}
                  level ·{" "}
                  <strong>
                    {disposition(difference.row)}
                    {difference.row.datum.value !== null ? " pp" : ""}
                  </strong>{" "}
                  difference
                </p>
                <GoalieDistribution field={difference} />
                <p>{skill.condition}.</p>
                <p>{goalieSupportText(level.row.datum.support)}</p>
              </section>
            );
          })}
        </div>
        <p>
          difference distributions increase with the supplied quantity; no
          universal favorable direction. level distributions remain selectable
          in detail.
        </p>
      </section>
      <section data-goalie-slot="g03">
        <h4>recorded source outcomes</h4>
        {observed ? (
          <div className="table-scroll" tabIndex={0}>
            <table>
              <caption>
                source events and separately reported boxscore totals; reported
                strength labels are not proof of exact physical strength
              </caption>
              <thead>
                <tr>
                  <th>source</th>
                  <th>unblocked</th>
                  <th>misses</th>
                  <th>on-net</th>
                  <th>saves</th>
                  <th>goals against</th>
                  <th>save %</th>
                </tr>
              </thead>
              <tbody>
                {(["source_counts", "reported_boxscore_counts"] as const).map(
                  (key) => (
                    <tr key={key}>
                      <th>
                        {key === "source_counts"
                          ? "recorded events"
                          : "reported official totals"}
                      </th>
                      <td>
                        {observed[key].unblocked_attempts ?? "unavailable"}
                      </td>
                      <td>{observed[key].misses ?? "unavailable"}</td>
                      <td>{observed[key].shots_on_goal ?? "unavailable"}</td>
                      <td>{observed[key].saves ?? "unavailable"}</td>
                      <td>{observed[key].goals_against ?? "unavailable"}</td>
                      <td>
                        {displayNumber(
                          observed[key].save_percentage.value === null
                            ? null
                            : 100 * observed[key].save_percentage.value,
                        )}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <p>{model.observedReason}</p>
        )}
      </section>
      <section data-goalie-slot="g04">
        <h4>matched actual-opportunity saving</h4>
        {observed ? (
          <div className="table-scroll" tabIndex={0}>
            <table>
              <caption>
                each row has its own eligible population; source counts can
                exceed matched eligibility
              </caption>
              <thead>
                <tr>
                  <th>population</th>
                  <th>eligible attempts</th>
                  <th>actual goals</th>
                  <th>expected goals</th>
                  <th>saved above expected</th>
                  <th>goals /100 expected</th>
                  <th>expected save %</th>
                </tr>
              </thead>
              <tbody>
                {(["unblocked", "on_net"] as const).map((population) => {
                  const row =
                    observed[
                      population === "on_net"
                        ? "on_net_evidence"
                        : "unblocked_evidence"
                    ];
                  return (
                    <tr key={population}>
                      <th>{population}</th>
                      <td>{row.attempts}</td>
                      <td>{row.goals}</td>
                      <td>{displayNumber(row.expected_goals)}</td>
                      <td>
                        {displayNumber(row.goals_saved_above_expected.value)}
                      </td>
                      <td>{displayNumber(row.goals_per100_expected.value)}</td>
                      <td>
                        {population === "on_net"
                          ? displayNumber(
                              observed.on_net_evidence.expected_save_fraction
                                .value === null
                                ? null
                                : 100 *
                                    observed.on_net_evidence
                                      .expected_save_fraction.value,
                            )
                          : "not defined"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p>{model.observedReason}</p>
        )}
      </section>
      <div className="goalie-map-grid">
        <figure data-goalie-slot="g02">
          <figcaption>
            {selection.coreStrength} modeled stopping · common reference
          </figcaption>
          {model.modeledMap.integral === null ? (
            <p>
              {model.modeledMap.availability}: {model.modeledMap.reason}
            </p>
          ) : (
            <AnalyticalMapDrawing
              model={model.modeledMap}
              render={model.render}
            />
          )}
          <p>
            native sum {displayNumber(model.modeledMap.integral)} goals
            prevented /100 on-net; positive is favorable.
          </p>
          <AnalyticalMapLegend model={model.modeledMap} />
          <p>
            {model.modeledMap.orientation};{" "}
            {goalieSupportText(model.modeledMap.support)}
          </p>
        </figure>
        <figure data-goalie-slot="g06">
          <figcaption>
            {selection.evidenceStrength} actual saving · {selection.population}
          </figcaption>
          {model.actualMap.data ? (
            <GoalieMapDrawing model={model.actualMap} render={model.render} />
          ) : (
            <p>
              {model.actualMap.availability}: {model.actualMap.reason}
            </p>
          )}
          <GoalieMapLegend model={model.actualMap} />
          <p>
            selected paired saving {displayNumber(model.actualMap.integral)}{" "}
            goals; mapped{" "}
            {displayNumber(
              model.actualMap.data
                ? model.actualMap.rectangles.reduce(
                    (sum, row) => sum + row.mass,
                    0,
                  )
                : null,
            )}
            ; unmapped{" "}
            {model.actualMap.data
              ? displayNumber(
                  model.actualMap.data.unmapped.expected_goals -
                    model.actualMap.data.unmapped.goals,
                )
              : "unavailable"}
            .
          </p>
          <p data-goalie-slot="g05">
            own mean probability (fraction){" "}
            {displayNumber(
              observed?.[
                selection.population === "on_net"
                  ? "on_net_evidence"
                  : "unblocked_evidence"
              ].mean_goal_probability.value ?? null,
            )}
            ; matched league probability (fraction){" "}
            {displayNumber(
              observed?.[
                selection.population === "on_net"
                  ? "on_net_evidence"
                  : "unblocked_evidence"
              ].league_mean_goal_probability.value ?? null,
            )}
            ; relative{" "}
            {displayNumber(
              observed?.[
                selection.population === "on_net"
                  ? "on_net_evidence"
                  : "unblocked_evidence"
              ].difficulty_relative_percent.value ?? null,
            )}
            %. actual opportunity mix, not ability.
          </p>
          <p>{goalieSupportText(model.actualMap.support)}</p>
        </figure>
      </div>
      <section data-goalie-slot="g07">
        <h4>
          saving by recorded shot type · {selection.evidenceStrength} /{" "}
          {selection.population}
        </h4>
        <div className="goalie-map-grid">
          {model.typeMaps.map((panel) => (
            <figure key={panel.type}>
              <figcaption>
                {panel.label} ·{" "}
                {panel.map.data?.totals.attempts ?? "unavailable"} attempts
              </figcaption>
              {panel.map.data ? (
                <GoalieMapDrawing model={panel.map} render={model.render} />
              ) : (
                <p>{panel.map.reason}</p>
              )}
              <TypeBars model={panel.map} />
              <p>{unmappedText(panel.map)}</p>
              <GoalieMapLegend model={panel.map} />
              <p>
                own matched reference {panel.map.reference ?? "unavailable"};{" "}
                {goalieSupportText(panel.map.support)}
              </p>
            </figure>
          ))}
        </div>
        <p>
          other recorded types:{" "}
          {model.otherMap?.data
            ? `${model.otherMap.data.totals.attempts} attempts; ${model.otherMap.data.totals.goals} goals; ${displayNumber(model.otherMap.data.totals.expected_goals)} expected`
            : (model.otherMap?.reason ?? "unavailable")}
          .
        </p>
        <p>
          other recorded types remain in full accounting/detail. unknown type
          labels are excluded from known-type panels; no per-goalie
          unknown-label count is supplied. all-type totals stay authoritative.
        </p>
      </section>
      <section data-goalie-slot="g08">
        <h4>actual versus expected goal danger</h4>
        {model.danger ? (
          <>
            <GoalieDangerPlot danger={model.danger} />
            <p>
              actual goals {model.danger.totals.goals} (red), expected{" "}
              {displayNumber(model.danger.totals.expected_goals)} (black),{" "}
              {model.danger.totals.attempts} attempts; 100 fixed
              one-percentage-point bins, last includes 1; nonnegative goal
              density, no extra smoothing.
            </p>
          </>
        ) : (
          <p>{model.dangerReason}</p>
        )}
      </section>
      <footer>
        {model.footer.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </footer>
      <div className="card-actions">
        <button
          type="button"
          onClick={async () => {
            const snapshot = model;
            try {
              downloadBlob(
                await svgPng(goalieCardSvg(snapshot)),
                `hockey-stats-${profile.season.season}-${profile.player_id}-goalie-card${model.companion ? `-with-${model.companion}` : ""}.png`,
              );
              setStatus("goalie sheet png prepared");
            } catch {
              setStatus(
                "goalie sheet export failed; no older selection was exported",
              );
            }
          }}
        >
          download complete goalie sheet png
        </button>
        <button
          type="button"
          onClick={() =>
            downloadBlob(
              new Blob([goalieCardCsv(model)], {
                type: "text/csv;charset=utf-8",
              }),
              `hockey-stats-${profile.season.season}-${profile.player_id}-goalie-card.csv`,
            )
          }
        >
          download goalie-card.csv
        </button>
        <p role="status">{status}</p>
      </div>
    </section>
  );
}

function TypeBars({ model }: { readonly model: GoalieEvidenceMapModel }) {
  if (!model.data) return <p>{model.reason}</p>;
  const { goals, expected_goals } = model.data.totals;
  const maximum = Math.max(goals, expected_goals);
  return (
    <div className="goalie-type-bars">
      <p>
        <span
          style={{
            width: `${maximum ? (100 * goals) / maximum : 0}%`,
            backgroundColor: "#b2182b",
          }}
        />
        actual {goals} goals
      </p>
      <p>
        <span
          style={{
            width: `${maximum ? (100 * expected_goals) / maximum : 0}%`,
            backgroundColor: "#5a567b",
          }}
        />
        expected {displayNumber(expected_goals)} goals
      </p>
    </div>
  );
}

export function goalieCardCsv(model: GoalieCardModel): string {
  const { profile } = model,
    selection = profile.goalieSelection!;
  const suffix = [
    "source_path",
    "raw_number",
    "raw_text",
    "raw_unit",
    "raw_support",
  ];
  const rows: CsvCell[][] = model.fields.map((field) => [
    "modeled",
    field.slot,
    selection.evidenceStrength,
    selection.population,
    ...analysisCsvRow(profile.publication, profile.season, field.row),
    null,
    null,
    null,
    null,
    null,
  ]);
  const rawRow = (fact: GoalieRawFact) => {
    const values: Partial<
      Record<(typeof analysisCsvHeaders)[number], CsvCell>
    > = {
      publication_id: profile.publication.publication_id,
      purpose: profile.publication.purpose,
      season: profile.season.season,
      corpus_sha256: profile.season.corpus_sha256,
      player_id: profile.player_id,
      player_kind: "goalie",
      display_name: model.name,
      value_status:
        profile.person === null
          ? "absent"
          : fact.value === null
            ? "unavailable"
            : "provided",
      value_reason: fact.reason,
      method_ids: fact.methodId ? JSON.stringify([fact.methodId]) : null,
      numeric_reference: fact.reference,
      source_ids: fact.sourceId ? JSON.stringify([fact.sourceId]) : null,
    };
    return [
      fact.section,
      fact.slot,
      selection.evidenceStrength,
      selection.population,
      ...analysisCsvHeaders.map((header) => values[header] ?? null),
      fact.path,
      typeof fact.value === "number" ? fact.value : null,
      typeof fact.value === "string" ? fact.value : null,
      fact.unit,
      fact.support ? JSON.stringify(fact.support) : null,
    ];
  };
  for (const fact of model.rawFacts) rows.push(rawRow(fact));
  if (!model.observed)
    rows.push(
      rawRow({
        section: "source",
        slot: "g03",
        path: "goalie_observed",
        value: null,
        unit: "",
        support: null,
        reason: model.observedReason,
        methodId: null,
        reference: null,
        sourceId: null,
      }),
    );
  return csvText(
    [
      "section",
      "slot_id",
      "evidence_strength",
      "evidence_population",
      ...analysisCsvHeaders,
      ...suffix,
    ],
    rows,
  );
}

export function goalieCardSvg(model: GoalieCardModel): string {
  const parts: string[] = [];
  const xml = (value: string | number) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  const text = (
    value: string | number,
    x: number,
    y: number,
    size = 20,
    extra = "",
  ) =>
    parts.push(
      `<text x="${x}" y="${y}" font-size="${size}" ${extra}>${xml(value)}</text>`,
    );
  const wrap = (
    value: string,
    x: number,
    y: number,
    width: number,
    size = 20,
    extra = "",
  ) => {
    const limit = Math.max(1, Math.floor(width / (size * 0.6)));
    const lines: string[] = [];
    let line = "";
    for (const word of value.split(/\s+/)) {
      if (line.length + word.length + 1 > limit && line) {
        lines.push(line);
        line = "";
      }
      if (word.length > limit) {
        if (line) {
          lines.push(line);
          line = "";
        }
        for (let i = 0; i < word.length; i += limit)
          lines.push(word.slice(i, i + limit));
      } else line += `${line ? " " : ""}${word}`;
    }
    if (line) lines.push(line);
    lines.forEach((line, i) => text(line, x, y + i * (size + 7), size, extra));
    return lines.length * (size + 7);
  };
  let y = 42;
  const full = (value: string, size = 20) => {
    y += wrap(value, 44, y, 1112, size);
  };
  const title = (value: string) => {
    y += 18;
    full(value, 24);
    y += 8;
  };
  full(
    `${model.profile.publication.purpose === "fixture" ? "synthetic fixture · " : ""}experimental goalie sheet`,
  );
  full(model.name, 34);
  full(
    `${seasonLabel(model.profile.season.season)} · ${model.profile.person?.teams.map(teamName).join(" / ") || "selected-season identity absent"}`,
  );
  const selection = model.profile.goalieSelection!,
    observed = model.observed,
    stopping = model.fields[0];
  if (observed)
    full(
      `${observed.reported_usage.positive_toi_appearances} reported appearances; ${observed.starts} starts / ${observed.relief_appearances} relief / ${observed.unknown_start_status} unknown; ${displayNumber(observed.reported_usage.reported_seconds === null ? null : observed.reported_usage.reported_seconds / 60)} reported min; ${displayNumber(observed.reported_usage.minutes_per_appearance.value)} min/appearance.`,
    );
  else full(model.observedReason!);
  title(
    `${selection.coreStrength} common-reference stopping: ${disposition(stopping.row)} goals prevented /100 on-net`,
  );
  full(
    `qualifying selected-state minutes ${displayNumber(stopping.row.datum.qualificationSeconds === null ? null : stopping.row.datum.qualificationSeconds / 60)}; ${goalieSupportText(stopping.row.datum.support)}.`,
  );
  const distribution = (
    field: Field,
    x: number,
    top: number,
    width: number,
  ) => {
    const { domain, row, group } = field;
    let bottom = top;
    if (domain) {
      const scale = (value: number) =>
        x + 20 + ((width - 40) * (value - domain[0])) / (domain[1] - domain[0]);
      parts.push(
        `<path d="M${x + 20} ${top + 26}h${width - 40}" stroke="#64767b"/>`,
      );
      if (domain[0] <= 0 && domain[1] >= 0)
        parts.push(
          `<path d="M${scale(0)} ${top}v53" stroke="#64767b" stroke-dasharray="3 3"/>`,
        );
      for (const peer of group.members)
        parts.push(
          `<path d="M${scale(displayValue(peer)!)} ${top + 12}v28" stroke="#9eaeae"/>`,
        );
      if (row.datum.value !== null)
        parts.push(
          `<circle cx="${scale(displayValue(row.datum)!)}" cy="${top + 26}" r="7" fill="#145a66" stroke="#fbfaf6" stroke-width="2"/>`,
        );
      text(displayNumber(domain[0]), x + 20, top + 76);
      text(
        displayNumber(domain[1]),
        x + width - 20,
        top + 76,
        20,
        'text-anchor="end"',
      );
      bottom = top + 105;
    } else bottom = top + 30 + wrap("no finite distribution", x, top + 30, width);
    bottom += wrap(
      `${group.peerGroup}; n=${group.members.length}; ≥${group.cutoffMinutes ?? "?"} supported min; ${standingText(row.standing)}${row.member === false ? "; selected outsider" : ""}`,
      x,
      bottom,
      width,
    );
    return bottom;
  };
  y = distribution(stopping, 44, y, 1112) + 14;
  title("three-season raw stopping · core strength unchanged by detail");
  const trajectory = prepareHistory(model.history, "raw");
  const domain = plotDomain(
    trajectory.flatMap((point) => (point.value === null ? [] : [point.value])),
  );
  if (domain) {
    const x = (i: number) => 200 + i * 440,
      sy = (value: number) =>
        y + 150 - (140 * (value - domain[0])) / (domain[1] - domain[0]);
    parts.push(`<path d="M200 ${y + 160}h900" stroke="#64767b"/>`);
    for (let i = 0; i < trajectory.length; i++) {
      const point = trajectory[i];
      if (
        i &&
        point.value !== null &&
        trajectory[i - 1].value !== null &&
        !point.breakBefore
      )
        parts.push(
          `<path d="M${x(i - 1)} ${sy(trajectory[i - 1].value!)}L${x(i)} ${sy(point.value)}" fill="none" stroke="#145a66" stroke-width="3"/>`,
        );
      if (point.value !== null)
        parts.push(
          `<circle cx="${x(i)}" cy="${sy(point.value)}" r="7" fill="#145a66"/>`,
        );
      text(
        seasonLabel(point.point.season.season),
        x(i),
        y + 194,
        20,
        'text-anchor="middle"',
      );
      text(
        point.value === null ? "unavailable" : displayNumber(point.value),
        x(i),
        y + 224,
        20,
        'text-anchor="middle"',
      );
    }
    text(displayNumber(domain[0]), 170, y + 158, 20, 'text-anchor="end"');
    text(displayNumber(domain[1]), 170, y + 16, 20, 'text-anchor="end"');
    y += 255;
  } else full("stopping history unavailable; no line drawn.");
  title(
    "six conditional subskills · level; focal-minus-neutral difference (pp)",
  );
  for (let rowIndex = 0; rowIndex < 3; rowIndex++) {
    let bottom = y;
    goalieSkills
      .slice(rowIndex * 2, rowIndex * 2 + 2)
      .forEach((skill, column) => {
        const x = 44 + column * 570;
        let top = y;
        const level = model.fields.find(
            (field) => field.field === skill.field,
          )!,
          difference = model.fields.find(
            (field) => field.field === `${skill.field}_difference`,
          )!;
        top += wrap(skill.label, x, top, 542, 22, 'font-weight="700"');
        top += wrap(
          `${disposition(level.row)}${level.row.datum.value !== null ? "%" : ""} level; ${disposition(difference.row)}${difference.row.datum.value !== null ? " pp" : ""} difference`,
          x,
          top,
          542,
        );
        top = distribution(difference, x, top + 5, 542);
        top += wrap(skill.condition, x, top + 8, 542);
        top += wrap(
          goalieSupportText(level.row.datum.support),
          x,
          top + 8,
          542,
        );
        bottom = Math.max(bottom, top + 28);
      });
    y = bottom;
  }
  title("recorded source outcomes · actual evidence");
  if (observed) {
    for (const key of ["source_counts", "reported_boxscore_counts"] as const) {
      const row = observed[key];
      full(
        `${key === "source_counts" ? "recorded events" : "reported official totals"}: unblocked ${row.unblocked_attempts ?? "unavailable"}; misses ${row.misses ?? "unavailable"}; on-net ${row.shots_on_goal ?? "unavailable"}; saves ${row.saves ?? "unavailable"}; goals against ${row.goals_against ?? "unavailable"}; save ${displayNumber(row.save_percentage.value === null ? null : 100 * row.save_percentage.value)}%.`,
      );
    }
    full(
      "unblocked = misses + saves + goals; on-net = saves + goals. reported labels do not certify exact strength.",
    );
    title(
      "matched actual-opportunity saving · two distinct paired populations",
    );
    for (const population of ["unblocked", "on_net"] as const) {
      const row =
        observed[
          population === "unblocked" ? "unblocked_evidence" : "on_net_evidence"
        ];
      full(
        `${population}: ${row.attempts} eligible attempts; ${row.goals} actual goals; ${displayNumber(row.expected_goals)} expected; ${displayNumber(row.goals_saved_above_expected.value)} goals saved; ${displayNumber(row.goals_per100_expected.value)} goals /100 expected${population === "on_net" ? `; expected save ${displayNumber(observed.on_net_evidence.expected_save_fraction.value === null ? null : 100 * observed.on_net_evidence.expected_save_fraction.value)}%` : "; expected save fraction not defined"}.`,
      );
    }
  }
  const mapPair = (
    panels: readonly {
      label: string;
      map: AnalyticalMapModel | GoalieEvidenceMapModel;
      type?: boolean;
    }[],
  ) => {
    let bottom = y;
    panels.forEach((panel, column) => {
      const x = 44 + column * 570;
      let top = y;
      top += wrap(panel.label, x, top, 542, 22, 'font-weight="700"');
      const drawingTop = top + 4;
      const present =
        "data" in panel.map
          ? panel.map.data !== null
          : panel.map.integral !== null;
      if (present)
        parts.push(
          `<svg x="${x}" y="${drawingTop}" width="542" height="231">${analyticalMapDrawingSvg(panel.map, `goalie-${y}-${column}`, "ratio" in panel.map && panel.map.ratio ? "rectangles" : model.render)}</svg>`,
        );
      else
        wrap(
          `${panel.map.availability}: ${panel.map.reason}`,
          x,
          drawingTop + 35,
          542,
        );
      top = drawingTop + 260;
      if ("data" in panel.map && panel.map.data) {
        const data = panel.map.data;
        top += wrap(
          `${data.totals.attempts} attempts; ${data.totals.goals} actual; ${displayNumber(data.totals.expected_goals)} expected; ${displayNumber(panel.map.integral)} saved.`,
          x,
          top,
          542,
        );
        if (panel.type) {
          const max = Math.max(data.totals.goals, data.totals.expected_goals);
          parts.push(
            `<rect x="${x}" y="${top}" width="${max ? (400 * data.totals.goals) / max : 0}" height="12" fill="#b2182b"/><rect x="${x}" y="${top + 20}" width="${max ? (400 * data.totals.expected_goals) / max : 0}" height="12" fill="#5a567b"/>`,
          );
          top += 62;
          top += wrap(
            "actual goals (red); expected goals (purple)",
            x,
            top,
            542,
          );
          top += wrap(unmappedText(panel.map), x, top + 8, 542);
        } else
          top += wrap(
            `mapped saving ${displayNumber(panel.map.rectangles.reduce((sum, row) => sum + row.mass, 0))}; unmapped ${displayNumber(data.unmapped.expected_goals - data.unmapped.goals)}.`,
            x,
            top,
            542,
          );
      } else if (!("data" in panel.map))
        top += wrap(
          `native sum ${displayNumber(panel.map.integral)} goals prevented /100 common-reference on-net; positive favorable.`,
          x,
          top,
          542,
        );
      const densityLabel = panel.map.densityLabel;
      top += wrap(densityLabel, x, top + 8, 542);
      panel.map.legend.forEach((level, i) =>
        parts.push(
          `<rect x="${x + (i * 542) / panel.map.legend.length}" y="${top}" width="${542 / panel.map.legend.length}" height="18" fill="${level.fill}"/>`,
        ),
      );
      top += 50;
      top += wrap(
        `levels: ${panel.map.levels.map((v) => Number(v.toPrecision(3))).join("; ")}`,
        x,
        top,
        542,
      );
      top += wrap(
        "ratio" in panel.map && panel.map.ratio
          ? `${goalieRatioScaleText(panel.map)}; nonadditive and volatile at small expected mass`
          : "positive favorable; central band below first nonzero density level; zero scale neutral",
        x,
        top + 7,
        542,
      );
      top += wrap(goalieSupportText(panel.map.support), x, top + 7, 542);
      top += wrap(
        `reference ${panel.map.reference ?? "unavailable"}; defended goal left; +x left / +y down; 10ft pooling.`,
        x,
        top + 7,
        542,
      );
      bottom = Math.max(bottom, top + 30);
    });
    y = bottom;
  };
  title("modeled stopping and actual saving · full rink");
  mapPair([
    {
      label: `${selection.coreStrength} modeled stopping`,
      map: model.modeledMap,
    },
    {
      label: `${selection.evidenceStrength} actual ${selection.population} saving`,
      map: model.actualMap,
    },
  ]);
  if (observed) {
    const paired =
      observed[
        selection.population === "on_net"
          ? "on_net_evidence"
          : "unblocked_evidence"
      ];
    full(
      `actual difficulty: own mean probability ${displayNumber(paired.mean_goal_probability.value)}; matched league mean probability ${displayNumber(paired.league_mean_goal_probability.value)} (fractions); relative ${displayNumber(paired.difficulty_relative_percent.value)}%. opportunity mix, not ability.`,
    );
  }
  title(
    `saving by recorded type · ${selection.evidenceStrength} / ${selection.population}`,
  );
  mapPair(
    model.typeMaps
      .slice(0, 2)
      .map((panel) => ({ label: panel.label, map: panel.map, type: true })),
  );
  mapPair(
    model.typeMaps
      .slice(2)
      .map((panel) => ({ label: panel.label, map: panel.map, type: true })),
  );
  if (model.otherMap?.data)
    full(
      `other recorded types: ${model.otherMap.data.totals.attempts} attempts; ${model.otherMap.data.totals.goals} goals; ${displayNumber(model.otherMap.data.totals.expected_goals)} expected.`,
    );
  full(
    "other known-type totals remain in detail; unknown-type exclusions are not a supplied per-goalie count. no known-type sum is substituted for all-type evidence.",
  );
  title("actual versus expected danger · nonnegative fixed-bin densities");
  if (model.danger) {
    parts.push(
      `<svg x="44" y="${y}" width="1112" height="300">${goalieDangerDrawingSvg(model.danger)}</svg>`,
    );
    y += 335;
    full(
      `${model.danger.totals.attempts} attempts; ${model.danger.totals.goals} actual goals (red); ${displayNumber(model.danger.totals.expected_goals)} expected goals (black). 100 bins; final upper endpoint includes 1. no extra smoothing.`,
    );
  } else full(model.dangerReason!);
  title("construction, support and limitations");
  for (const line of model.footer) {
    y += wrap(line, 44, y, 1112, 18) + 5;
  }
  y += 30;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${Math.ceil(y)}" viewBox="0 0 1200 ${Math.ceil(y)}" font-family="ui-monospace,Menlo,monospace" fill="#242b2d" role="img" aria-label="${xml(`${model.name} complete experimental goalie sheet`)}"><title>${xml(`${model.name} · ${model.profile.season.season} · ${selection.coreStrength} modeled / ${selection.evidenceStrength} ${selection.population} actual`)}</title><rect width="1200" height="${Math.ceil(y)}" fill="#fbfaf6"/>${parts.join("")}</svg>`;
}
