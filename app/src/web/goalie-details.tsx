import { useState } from "react";
import type { GoalieObserved, Support } from "../shared/player-analysis";
import type { ProfileView } from "./client";
import type { PeerSettings } from "./explorer";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  displayNumber,
  HistoryPlot,
  prepareHistoryPoint,
  DatumEvidence,
} from "./analysis-history";
import { goalieDetailMetric, selectHistoryValue } from "./analysis-values";
import { rawOnlyStanding } from "./analysis-cohorts";
import { goalieFields, goalieSkills, prepareGoalieCard } from "./goalie-card";
import {
  GoalieEvidenceMapFigure,
  goalieCsv,
  goalieDangerCsv,
  goalieSupportText,
  prepareGoalieEvidenceMap,
  type GoalieCsvContext,
} from "./goalie-evidence";
import { AnalyticalMapFigure, prepareAnalyticalMap } from "./analytical-map";
import { csvText, downloadBlob, type CsvCell } from "./export";
import { seasonLabel, teamName } from "./presentation";

type Observed = typeof GoalieObserved.Type;
const stages = [
  "miss",
  "recorded_stop",
  "conversion",
  "reattempt",
  "next_attempt_danger",
] as const;
function observedEvidence(profile: ProfileView) {
  const result = profile.goalieEvidence?.result;
  const data = result?.availability === "provided" ? result.data : null;
  const observed =
    data?.observed.availability === "provided" ? data.observed.data : null;
  return {
    data,
    observed,
    reason:
      data?.observed.explanation ??
      result?.explanation ??
      "goalie evidence unavailable",
  };
}
function exportContext(profile: ProfileView): GoalieCsvContext {
  const selection = profile.goalieSelection!;
  const { data, observed, reason } = observedEvidence(profile);
  return {
    publication: profile.publication,
    season: profile.season,
    playerId: profile.player_id,
    coreStrength: selection.coreStrength,
    strength: selection.evidenceStrength,
    population: selection.population,
    type: null,
    methodId:
      observed?.[
        selection.population === "on_net"
          ? "on_net_evidence"
          : "unblocked_evidence"
      ].method_id ?? null,
    reference:
      "matched actual-opportunity evidence; selected strength, all types",
    support: observed?.coverage ?? null,
    availability: observed
      ? "provided"
      : (data?.observed.availability ??
        profile.goalieEvidence?.result.availability ??
        "not_computed"),
    reason: observed ? null : reason,
    companion:
      profile.goalieMaps
        .find((map) => map.family !== "observed")
        ?.selection.players.find((id) => id !== profile.player_id) ?? null,
  };
}

type StageRow = {
  readonly scope: "summary" | "actual_state" | "game" | "game_state";
  readonly gameId: string | null;
  readonly actualState: string | null;
  readonly stage: (typeof stages)[number];
  readonly successCount: number | null;
  readonly fractionalResponseSum: number | null;
  readonly eligibleCount: number;
  readonly matchedExpectedSum: number;
  readonly support: Support;
};
export function goalieStageRows(observed: Observed): readonly StageRow[] {
  const rows: StageRow[] = [];
  const add = (
    scope: StageRow["scope"],
    gameId: string | null,
    actualState: string | null,
    evidence: Observed["stage_evidence"],
  ) => {
    for (const stage of stages) {
      const value = evidence[stage];
      rows.push({
        scope,
        gameId,
        actualState,
        stage,
        successCount: "success_count" in value ? value.success_count : null,
        fractionalResponseSum:
          "fractional_response_sum" in value
            ? value.fractional_response_sum
            : null,
        eligibleCount: value.eligible_count,
        matchedExpectedSum: value.matched_expected_sum,
        support: value.support,
      });
    }
  };
  add("summary", null, null, observed.stage_evidence);
  for (const state of observed.actual_states)
    add(
      "actual_state",
      null,
      JSON.stringify(state.state),
      state.stage_evidence,
    );
  for (const game of observed.games) {
    add("game", game.game_id, null, game.stage_evidence);
    for (const state of game.actual_states)
      add(
        "game_state",
        game.game_id,
        JSON.stringify(state.state),
        state.stage_evidence,
      );
  }
  return rows;
}
export function goalieStagesCsv(profile: ProfileView): string {
  const context = { ...exportContext(profile), population: null },
    { observed } = observedEvidence(profile);
  return goalieCsv(
    context,
    [
      "scope",
      "game_id",
      "actual_state",
      "stage",
      "success_count",
      "fractional_response_sum",
      "eligible_count",
      "matched_expected_sum",
      "support",
    ],
    observed
      ? goalieStageRows(observed).map((row) => [
          row.scope,
          row.gameId,
          row.actualState,
          row.stage,
          row.successCount,
          row.fractionalResponseSum,
          row.eligibleCount,
          row.matchedExpectedSum,
          JSON.stringify(row.support),
        ])
      : [[]],
  );
}
export function goalieGamesCsv(profile: ProfileView): string {
  const context = { ...exportContext(profile), population: null },
    { observed } = observedEvidence(profile);
  return goalieCsv(
    context,
    [
      "game_id",
      "date",
      "team",
      "opponent",
      "start_status",
      "reported_seconds",
      "provenance",
      "source_counts",
      "reported_boxscore_counts",
      "on_net_evidence",
      "unblocked_evidence",
      "actual_states",
    ],
    observed
      ? observed.games.map((game) => [
          game.game_id,
          game.date,
          JSON.stringify(game.team),
          JSON.stringify(game.opponent),
          game.start_status,
          game.reported_seconds,
          JSON.stringify(game.provenance),
          JSON.stringify(game.source_counts),
          JSON.stringify(game.reported_boxscore_counts),
          JSON.stringify(game.on_net_evidence),
          JSON.stringify(game.unblocked_evidence),
          JSON.stringify(game.actual_states),
        ])
      : [[]],
  );
}
export function goalieTiersCsv(profile: ProfileView): string {
  const context = exportContext(profile);
  const result = profile.goalieDetail?.result;
  const rows =
    result?.availability === "provided"
      ? result.data.breakdowns.filter((row) => row.kind === "danger")
      : [];
  const columns = [
    "stratum",
    "events",
    "eligible_weight",
    "observed_successes",
    "expected_successes",
    "probability",
    "effect",
    "support",
    "field_availability",
    "field_reason",
    "tier_population",
    "tier_definition",
  ];
  const selected = {
    ...context,
    population: "unblocked",
    reference:
      "fully neutral on-net probability tiers; paired unblocked responses",
  };
  if (context.strength === "covered_all")
    return goalieCsv(
      {
        ...selected,
        availability: "not_defined",
        reason: "covered_all has no modeled strength or danger tiers",
      },
      columns,
      [
        [
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          "not_defined",
          "covered_all danger tiers not defined",
          "unblocked",
          "<.05; [.05,.15); >=.15",
        ],
      ],
    );
  return goalieCsv(
    selected,
    columns,
    ["<.05", "[.05,.15)", ">=.15"].map((stratum) => {
      const row = rows.find((row) => row.stratum === stratum)?.result;
      const data = row?.availability === "provided" ? row.data : null;
      return [
        stratum,
        data?.events,
        data?.eligible_weight,
        data?.observed_successes,
        data?.expected_successes,
        data?.probability.value,
        data?.effect.value,
        data ? JSON.stringify(data.support) : null,
        row?.availability ?? result?.availability ?? "not_computed",
        row?.explanation ?? result?.explanation,
        "unblocked",
        "fully neutral on-net probability",
      ];
    }),
  );
}

export function goalieDangerDetailCsv(profile: ProfileView): string {
  const { data } = observedEvidence(profile);
  const result = data?.danger;
  const danger = result?.availability === "provided" ? result.data : null;
  return goalieDangerCsv(
    {
      ...exportContext(profile),
      type: "all",
      availability:
        result?.availability ??
        profile.goalieEvidence?.result.availability ??
        "not_computed",
      reason: danger
        ? null
        : (result?.explanation ??
          profile.goalieEvidence?.result.explanation ??
          "danger evidence unavailable"),
      methodId: danger?.method_id ?? null,
      support: danger?.support ?? null,
    },
    danger,
  );
}

export function goalieExactCsv(profile: ProfileView): string {
  const selection = profile.goalieSelection!;
  const headers = ["section", "actual_strength", ...analysisCsvHeaders];
  if (selection.evidenceStrength === "covered_all") {
    const values: Partial<
      Record<(typeof analysisCsvHeaders)[number], CsvCell>
    > = {
      publication_id: profile.publication.publication_id,
      purpose: profile.publication.purpose,
      season: profile.season.season,
      corpus_sha256: profile.season.corpus_sha256,
      player_id: profile.player_id,
      player_kind: "goalie",
      value_status: "not_defined",
      value_reason: "covered_all has no modeled exact-state values or history",
    };
    return csvText(headers, [
      [
        "reason",
        "covered_all",
        ...analysisCsvHeaders.map((header) => values[header] ?? null),
      ],
    ]);
  }
  const strength = selection.evidenceStrength;
  const selectedYear = profile.detail.history.find(
    (year) => year.season.season === profile.season.season,
  )!;
  const selectedField =
    goalieFields.find((field) =>
      profile.selectedMetric.id.endsWith(`.${field}`),
    ) ?? "stopping_goals_per100_on_net";
  const rows: CsvCell[][] = [];
  for (const [section, year, fields] of [
    ["scalar", selectedYear, goalieFields],
    ...profile.detail.history.map(
      (year) => ["history", year, [selectedField]] as const,
    ),
  ] as const)
    for (const field of fields) {
      const datum = selectHistoryValue(
        year,
        profile.detail,
        goalieDetailMetric(strength, field),
        profile.player_id,
      );
      rows.push([
        section,
        strength,
        ...analysisCsvRow(profile.publication, year.season, {
          datum,
          standing: rawOnlyStanding,
          member: null,
          incompatiblePeerCount: null,
        }),
      ]);
    }
  return csvText(headers, rows);
}

function StageTable({ rows }: { readonly rows: readonly StageRow[] }) {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table>
        <caption>
          matched stage responses and expected sums; scopes overlap and must not
          be added
        </caption>
        <thead>
          <tr>
            <th>scope / game / state</th>
            <th>stage</th>
            <th>binary successes</th>
            <th>fractional response sum</th>
            <th>eligible count</th>
            <th>matched expected sum</th>
            <th>support</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              <th>
                {row.scope} {row.gameId} {row.actualState}
              </th>
              <td>{row.stage}</td>
              <td>{row.successCount ?? "not applicable"}</td>
              <td>
                {row.fractionalResponseSum === null
                  ? "not applicable"
                  : displayNumber(row.fractionalResponseSum)}
              </td>
              <td>{row.eligibleCount}</td>
              <td>{displayNumber(row.matchedExpectedSum)}</td>
              <td>{goalieSupportText(row.support)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function GoalieDetails({
  profile,
  settings,
  render = "contours",
}: {
  readonly profile: ProfileView;
  readonly settings: PeerSettings;
  readonly render?: "contours" | "rectangles";
}) {
  const [allStages, setAllStages] = useState(false);
  const [receipts, setReceipts] = useState(false);
  const selection = profile.goalieSelection;
  if (!selection) return null;
  const { data, observed, reason } = observedEvidence(profile);
  const core = prepareGoalieCard(profile, settings, { render });
  const selectedResponse = profile.goalieMaps.find(
    (map) =>
      map.family === "goalie_evidence" &&
      map.selection.type === selection.type &&
      map.selection.strength === selection.evidenceStrength &&
      map.selection.population === selection.population,
  );
  const exactResponse = profile.goalieMaps.find(
    (map) =>
      map.family === "goalie_stopping" &&
      map.selection.strength === selection.evidenceStrength,
  );
  const selectedMap = selectedResponse
    ? prepareGoalieEvidenceMap(selectedResponse, profile.player_id)
    : null;
  const otherResponse = profile.goalieMaps.find(
    (map) =>
      map.family === "goalie_evidence" &&
      map.selection.type === "other" &&
      map.selection.strength === selection.evidenceStrength &&
      map.selection.population === selection.population,
  );
  const exact = profile.goalieDetail?.result;
  const exactData = exact?.availability === "provided" ? exact.data : null;
  const summary =
    exactData?.summary.availability === "provided"
      ? exactData.summary.data
      : null;
  const tiers =
    exactData?.breakdowns.filter((row) => row.kind === "danger") ?? [];
  const download = (text: string, filename: string) =>
    downloadBlob(
      new Blob([text], { type: "text/csv;charset=utf-8" }),
      `hockey-stats-${profile.season.season}-${profile.player_id}-${filename}`,
    );
  const evidence = summary?.evidence;
  const selectedField =
    goalieFields.find((field) =>
      profile.selectedMetric.id.endsWith(`.${field}`),
    ) ?? "stopping_goals_per100_on_net";
  const exactMetric =
    selection.evidenceStrength === "covered_all"
      ? null
      : goalieDetailMetric(selection.evidenceStrength, selectedField);
  const exactHistory = exactMetric
    ? profile.detail.history.map(
        (year) =>
          prepareHistoryPoint(
            { ...year, cohort: null },
            profile.detail,
            exactMetric,
            profile.player_id,
            settings,
          ).point,
      )
    : [];
  return (
    <section
      className="goalie-details"
      aria-label="goalie numerical and source detail"
    >
      <h3>goalie evidence and numerical detail</h3>
      <p>
        actual {selection.evidenceStrength} / {selection.population}; detail
        type {selection.type}. selected type changes its map, never the all-type
        summary, stages, games or histogram. core stopping stays{" "}
        {selection.coreStrength}.
      </p>
      {selectedMap ? (
        <GoalieEvidenceMapFigure model={selectedMap} render={render} />
      ) : (
        <p>selected actual map unavailable; no substituted type or strength.</p>
      )}
      {selection.type !== "other" && otherResponse && (
        <details>
          <summary>other recorded shot-type map</summary>
          <GoalieEvidenceMapFigure
            model={prepareGoalieEvidenceMap(otherResponse, profile.player_id)}
            render={render}
          />
        </details>
      )}
      <section>
        <h4>complete recorded type accounting</h4>
        <div className="table-scroll" tabIndex={0}>
          <table>
            <caption>
              matched selected actual population; known-type rows do not certify
              the absence of unknown labels
            </caption>
            <thead>
              <tr>
                <th>recorded type</th>
                <th>attempts</th>
                <th>goals</th>
                <th>expected goals</th>
                <th>saved</th>
                <th>unmapped attempts</th>
                <th>reference / support</th>
              </tr>
            </thead>
            <tbody>
              {[
                ...core.typeMaps,
                ...(core.otherMap
                  ? [{ type: "other", label: "other", map: core.otherMap }]
                  : []),
                { type: "all", label: "all types", map: core.actualMap },
              ].map((panel) => (
                <tr key={panel.type}>
                  <th>{panel.label}</th>
                  <td>{panel.map.data?.totals.attempts ?? panel.map.reason}</td>
                  <td>{panel.map.data?.totals.goals ?? "unavailable"}</td>
                  <td>
                    {displayNumber(
                      panel.map.data?.totals.expected_goals ?? null,
                    )}
                  </td>
                  <td>{displayNumber(panel.map.integral)}</td>
                  <td>{panel.map.data?.unmapped.attempts ?? "unavailable"}</td>
                  <td>
                    {panel.map.reference};{" "}
                    {goalieSupportText(panel.map.support)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          unknown and inapplicable recorded labels are excluded according to the
          saved method. the producer supplies no per-goalie unknown-label count.
          aggregate label_unavailable also includes inapplicable stages and is
          not that count.
        </p>
      </section>
      <section>
        <h4>three danger tiers · paired unblocked responses</h4>
        <p>
          tiers use fully neutral on-net probabilities &lt;.05, [.05,.15), ≥.15.
          the paired responses remain UNBLOCKED when the histogram population
          changes.
        </p>
        {selection.evidenceStrength === "covered_all" ? (
          <p>
            not defined: covered_all is actual supported coverage, with no
            modeled coefficient, cohort or danger tiers.
          </p>
        ) : (
          <div className="table-scroll" tabIndex={0}>
            <table>
              <thead>
                <tr>
                  <th>tier</th>
                  <th>events / eligible weight</th>
                  <th>actual goals</th>
                  <th>expected successes</th>
                  <th>expected probability</th>
                  <th>saved / unblocked attempt</th>
                  <th>support</th>
                </tr>
              </thead>
              <tbody>
                {["<.05", "[.05,.15)", ">=.15"].map((stratum) => {
                  const row = tiers.find(
                    (row) => row.stratum === stratum,
                  )?.result;
                  const value =
                    row?.availability === "provided" ? row.data : null;
                  return (
                    <tr key={stratum}>
                      <th>{stratum}</th>
                      <td>
                        {value
                          ? `${value.events} / ${value.eligible_weight}`
                          : (row?.explanation ??
                            exact?.explanation ??
                            "unavailable")}
                      </td>
                      <td>{value?.observed_successes ?? "unavailable"}</td>
                      <td>
                        {displayNumber(value?.expected_successes ?? null)}
                      </td>
                      <td>{displayNumber(value?.probability.value ?? null)}</td>
                      <td>{displayNumber(value?.effect.value ?? null)}</td>
                      <td>{goalieSupportText(value?.support ?? null)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <button
          type="button"
          onClick={() => download(goalieTiersCsv(profile), "goalie-tiers.csv")}
        >
          download goalie-tiers.csv
        </button>
      </section>
      <section data-goalie-slot="g13">
        <h4>matched stage responses</h4>
        {observed ? (
          <>
            <StageTable
              rows={goalieStageRows(observed).filter(
                (row) => row.scope === "summary",
              )}
            />
            <details
              onToggle={(event) => setAllStages(event.currentTarget.open)}
            >
              <summary>
                actual-state, game and game-state stage evidence
              </summary>
              {allStages && (
                <StageTable
                  rows={goalieStageRows(observed).filter(
                    (row) => row.scope !== "summary",
                  )}
                />
              )}
            </details>
          </>
        ) : (
          <p>{reason}</p>
        )}
        <p>
          miss / recorded stop / conversion / reattempt are binary stage
          successes. next-attempt danger is a fractional response sum. unknown
          terminal sequences stay unknown; no invented unknown-label count.
        </p>
        <button
          type="button"
          onClick={() =>
            download(goalieStagesCsv(profile), "goalie-stages.csv")
          }
        >
          download goalie-stages.csv
        </button>
      </section>
      <section>
        <h4>per-game workload and source evidence</h4>
        {observed ? (
          <div className="table-scroll" tabIndex={0}>
            <table>
              <caption>
                recorded game results, reported usage and source coverage; no
                game-level talent estimate
              </caption>
              <thead>
                <tr>
                  <th>game / date</th>
                  <th>team / opponent</th>
                  <th>start status</th>
                  <th>reported min</th>
                  <th>source unblocked / on-net / saves / goals</th>
                  <th>unblocked paired attempts / goals / expected</th>
                  <th>on-net paired attempts / goals / expected</th>
                  <th>provenance / coverage</th>
                </tr>
              </thead>
              <tbody>
                {observed.games.map((game) => (
                  <tr key={game.game_id}>
                    <th>
                      {game.game_id}
                      <br />
                      {game.date}
                    </th>
                    <td>
                      {teamName(game.team)} / {teamName(game.opponent)}
                    </td>
                    <td>{game.start_status}</td>
                    <td>
                      {displayNumber(
                        game.reported_seconds === null
                          ? null
                          : game.reported_seconds / 60,
                      )}
                    </td>
                    <td>
                      {game.source_counts.unblocked_attempts ?? "unavailable"} /{" "}
                      {game.source_counts.shots_on_goal ?? "unavailable"} /{" "}
                      {game.source_counts.saves ?? "unavailable"} /{" "}
                      {game.source_counts.goals_against ?? "unavailable"}
                    </td>
                    <td>
                      {game.unblocked_evidence.attempts} /{" "}
                      {game.unblocked_evidence.goals} /{" "}
                      {displayNumber(game.unblocked_evidence.expected_goals)}
                    </td>
                    <td>
                      {game.on_net_evidence.attempts} /{" "}
                      {game.on_net_evidence.goals} /{" "}
                      {displayNumber(game.on_net_evidence.expected_goals)}
                    </td>
                    <td>
                      <details>
                        <summary>source and state evidence</summary>
                        <pre>
                          {JSON.stringify(
                            {
                              provenance: game.provenance,
                              reported_boxscore_counts:
                                game.reported_boxscore_counts,
                              actual_states: game.actual_states,
                            },
                            null,
                            2,
                          )}
                        </pre>
                      </details>
                      {goalieSupportText(game.source_counts.support)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>{reason}</p>
        )}
        <button
          type="button"
          onClick={() => download(goalieGamesCsv(profile), "goalie-games.csv")}
        >
          download goalie-games.csv
        </button>
      </section>
      <section>
        <h4>
          {selection.evidenceStrength} exact modeled values and raw three-season
          history
        </h4>
        <button
          type="button"
          onClick={() =>
            download(goalieExactCsv(profile), "goalie-exact-history.csv")
          }
        >
          download exact-state scalars and history csv
        </button>
        {selection.evidenceStrength === "covered_all" ? (
          <p>not defined for covered_all. no ev or pk values substituted.</p>
        ) : (
          <>
            <p>
              all thirteen supplied fields; fractions display once as
              percentages or percentage points. exact states have no league
              ranking.
            </p>
            {exactMetric && (
              <>
                <h5>{exactMetric.label}: exact-state raw trajectory</h5>
                <HistoryPlot
                  view={{
                    publication: profile.publication,
                    metric: exactMetric,
                    selectedSeason: profile.season.season,
                    scale: "raw",
                    points: exactHistory,
                  }}
                />
                <details>
                  <summary>
                    selected exact-state history support and references
                  </summary>
                  {exactHistory.map((point) => (
                    <section key={point.season.season}>
                      <h5>{seasonLabel(point.season.season)}</h5>
                      <DatumEvidence datum={point.datum} />
                    </section>
                  ))}
                </details>
              </>
            )}
            <div className="table-scroll" tabIndex={0}>
              <table>
                <thead>
                  <tr>
                    <th>field</th>
                    {profile.detail.history.map((year) => (
                      <th key={year.season.season}>
                        {seasonLabel(year.season.season)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {goalieFields.map((field) => (
                    <tr key={field}>
                      <th>{field.replaceAll("_", " ")}</th>
                      {profile.detail.history.map((year) => {
                        const families = year.families;
                        const result =
                          "availability" in families
                            ? null
                            : families.kind === "goalie" &&
                                families.goalie.availability === "provided"
                              ? families.goalie.data.find(
                                  (row) =>
                                    row.strength === selection.evidenceStrength,
                                )?.result
                              : null;
                        const value =
                          result?.availability === "provided"
                            ? result.data[field]
                            : null;
                        return (
                          <td key={year.season.season}>
                            {value?.value === null || !value
                              ? (value?.reason_detail?.explanation ??
                                value?.unavailable_reason ??
                                result?.explanation ??
                                ("availability" in families
                                  ? families.explanation
                                  : "unavailable"))
                              : `${displayNumber(value.value * (field === "stopping_goals_per100_on_net" ? 1 : 100))} ${field === "stopping_goals_per100_on_net" ? "goals/100 on-net" : field.endsWith("_difference") ? "pp" : "%"}`}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {exactResponse &&
              selection.evidenceStrength !== selection.coreStrength && (
                <AnalyticalMapFigure
                  model={prepareAnalyticalMap(exactResponse, profile.player_id)}
                  render={render}
                />
              )}
          </>
        )}
      </section>
      <section>
        <h4>head-specific prior and reference evidence</h4>
        {evidence ? (
          <>
            <details>
              <summary>per-field aggregate support</summary>
              <div className="table-scroll" tabIndex={0}>
                <table>
                  <thead>
                    <tr>
                      <th>field</th>
                      <th>likelihood union</th>
                      <th>eligible reference weight</th>
                      <th>support and exclusion reasons</th>
                    </tr>
                  </thead>
                  <tbody>
                    {goalieFields.map((field) => (
                      <tr key={field}>
                        <th>{field}</th>
                        <td>
                          {summary!.support[field].events ?? "unavailable"}
                        </td>
                        <td>
                          {summary!.support[field].eligible_weight ??
                            "unavailable"}
                        </td>
                        <td>
                          {goalieSupportText(summary!.support[field])};{" "}
                          {JSON.stringify(
                            summary!.support[field].reason_counts,
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
            <div className="table-scroll" tabIndex={0}>
              <table>
                <caption>
                  saved head flags; likelihood keys may overlap and counts are
                  not an event union
                </caption>
                <thead>
                  <tr>
                    <th>head</th>
                    <th>available / reason</th>
                    <th>likelihood events</th>
                    <th>prior only</th>
                    <th>carried seasons</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(evidence.coefficient_support).map(
                    ([head, value]) => (
                      <tr key={head}>
                        <th>{head}</th>
                        <td>
                          {String(value.available)} / {value.reason ?? "none"}
                        </td>
                        <td>{value.likelihood_events}</td>
                        <td>{String(value.prior_only)}</td>
                        <td>{value.prior_seasons.join(", ") || "none"}</td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
            <div className="table-scroll" tabIndex={0}>
              <table>
                <caption>
                  reference masses with bound log masses; null/null unavailable,
                  zero/null mathematical zero, zero/finite log positive
                  underflow
                </caption>
                <thead>
                  <tr>
                    <th>family / reference / axis</th>
                    <th>mass</th>
                    <th>log mass</th>
                  </tr>
                </thead>
                <tbody>
                  {(["prefixes", "continuation"] as const).flatMap((family) =>
                    (["neutral", "focal"] as const).flatMap((reference) =>
                      evidence.masses[family][reference].masses.map(
                        (mass, index) => (
                          <tr key={`${family}-${reference}-${index}`}>
                            <th>
                              {family} / {reference} /{" "}
                              {
                                (family === "prefixes"
                                  ? [
                                      "A=sum(u)",
                                      "B=sum(uq)",
                                      "C=sum(uqr)",
                                      "D=sum(uqrg)",
                                    ]
                                  : ["W", "Wh", "Whd"])[index]
                              }
                            </th>
                            <td>{mass ?? "unavailable"}</td>
                            <td>
                              {evidence.masses[family][reference].log_masses[
                                index
                              ] ?? "none"}
                            </td>
                          </tr>
                        ),
                      ),
                    ),
                  )}
                </tbody>
              </table>
            </div>
            <p>
              both continuation references use the same neutral saved-shot
              weights. conditional danger = Whd/Wh; joint danger = Whd/W.
              stopping is separately standardized with neutral q and cannot be
              reconstructed from focal prefix D.
            </p>
            <div className="table-scroll" tabIndex={0}>
              <table>
                <caption>
                  supplied fully neutral conditional levels; never fill missing
                  focal estimates
                </caption>
                <thead>
                  <tr>
                    <th>conditional field</th>
                    <th>neutral level %</th>
                  </tr>
                </thead>
                <tbody>
                  {goalieSkills.map((skill) => (
                    <tr key={skill.field}>
                      <th>{skill.label}</th>
                      <td>
                        {displayNumber(
                          evidence.neutral_values[skill.field] === null
                            ? null
                            : 100 * evidence.neutral_values[skill.field]!,
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <details
              onToggle={(event) => setReceipts(event.currentTarget.open)}
            >
              <summary>
                bound panel references, methods and numerical receipts
              </summary>
              {receipts && (
                <pre>
                  {JSON.stringify(
                    {
                      panels: evidence.panels,
                      method_id: summary?.method_id,
                      method: summary
                        ? profile.detail.methods[summary.method_id]
                        : null,
                      publication: profile.publication,
                    },
                    null,
                    2,
                  )}
                </pre>
              )}
            </details>
          </>
        ) : (
          <p>
            {selection.evidenceStrength === "covered_all"
              ? "not defined: actual covered_all has no common-panel coefficient evidence"
              : (exactData?.summary.explanation ??
                exact?.explanation ??
                "saved coefficient/reference evidence unavailable")}
          </p>
        )}
      </section>
      <div className="card-actions">
        <button
          type="button"
          onClick={() =>
            download(goalieDangerDetailCsv(profile), "goalie-danger.csv")
          }
        >
          download goalie-danger.csv
        </button>
      </div>
    </section>
  );
}
