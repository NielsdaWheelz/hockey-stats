import { useState } from "react";
import type { ExecutionEvidence as Evidence } from "./client";
import type {
  Estimate,
  SkaterExecutionBreakdown,
} from "../shared/player-analysis";
import { downloadCsv, type CsvCell } from "./export";

type Breakdown = typeof SkaterExecutionBreakdown.Type;
const number = (value: number, places: number) =>
  value !== 0 && Math.abs(value) < 10 ** -places
    ? value.toExponential(2)
    : value.toLocaleString("en", { maximumFractionDigits: places, useGrouping: false });
const value = (estimate: Estimate, places: number) =>
  estimate.value === null
    ? estimate.unavailable_reason === "no_exposure"
      ? "unavailable: no paired attempts"
      : `unavailable: ${estimate.unavailable_reason}`
    : number(estimate.value, places);
export const executionEvidenceCsvHeaders = [
  "publication_id",
  "purpose",
  "season",
  "corpus_sha256",
  "player_id",
  "strength",
  "kind",
  "stratum",
  "availability",
  "explanation",
  "events",
  "observed_goals",
  "reference_expected_goals",
  "reference_mean_opportunity",
  "reference_observed_minus_expected_goals",
  "actor_expected_goals",
  "actor_mean_opportunity",
  "actor_observed_minus_expected_goals",
  "support",
  "reference_panel",
  "coefficient_support",
  "paired_evidence",
  "method",
  "sources",
  "estimates",
] as const;
export function executionEvidenceCsvRows(
  evidence: Evidence,
  playerId: string,
): readonly (readonly CsvCell[])[] {
  if (evidence.result.availability !== "provided") return [];
  const summary = evidence.result.data.summary.data;
  return evidence.result.data.breakdowns.map((row) => {
    const data = row.result.data;
    return [
      evidence.publication.publication_id,
      evidence.publication.purpose,
      evidence.season.season,
      evidence.season.corpus_sha256,
      playerId,
      row.strength,
      row.kind,
      row.stratum,
      row.result.availability,
      row.result.explanation,
      data?.events,
      data?.observed_goals,
      data?.reference.expected_goals,
      data?.reference.mean_opportunity.value,
      data?.reference.observed_minus_expected_goals.value,
      data?.actor.expected_goals,
      data?.actor.mean_opportunity.value,
      data?.actor.observed_minus_expected_goals.value,
      JSON.stringify(data?.support ?? null),
      JSON.stringify(summary?.reference_panel ?? null),
      JSON.stringify(summary?.coefficient_support ?? null),
      JSON.stringify(summary?.paired_evidence ?? null),
      JSON.stringify(data ? evidence.methods[data.method_id] : null),
      JSON.stringify(evidence.sources),
      JSON.stringify(
        data ? { reference: data.reference, actor: data.actor } : null,
      ),
    ];
  });
}
function Expectations({ data }: { readonly data: Breakdown }) {
  return (
    <>
      <td>{data.events}</td>
      <td>{data.observed_goals}</td>
      <td>{number(data.reference.expected_goals, 3)}</td>
      <td>{value(data.reference.mean_opportunity, 4)}</td>
      <td>{value(data.reference.observed_minus_expected_goals, 3)}</td>
      <td>{number(data.actor.expected_goals, 3)}</td>
      <td>{value(data.actor.mean_opportunity, 4)}</td>
      <td>{value(data.actor.observed_minus_expected_goals, 3)}</td>
    </>
  );
}
export default function ExecutionEvidence({
  evidence,
  playerId,
}: {
  readonly evidence: Evidence;
  readonly playerId: string;
}) {
  const [status, setStatus] = useState("");
  const result = evidence.result;
  if (result.availability !== "provided")
    return (
      <section className="execution-evidence">
        <h3>recorded attempts and model expectations</h3>
        <p>{result.explanation}</p>
      </section>
    );
  const data = result.data;
  const paired = data.summary.data?.paired_evidence;
  return (
    <section className="execution-evidence">
      <h3>recorded attempts and model expectations</h3>
      <p>
        personal shooting at {evidence.selection.strength}: recorded goals
        beside reference-execution and actual-actor expectations on the same
        paired ordinary attempts, including blocks. fitted seasonal
        opportunities, not held-out forecasts. the tables describe the realized
        mix; standardized finishing, setting and stages use the common panel.
      </p>
      <p>
        reference execution sets shooter, setter, goalie and coaching residuals
        to zero while retaining circumstances and inferred setup. recorded minus
        expected is a descriptive residual. it is not isolated ability or luck.
      </p>
      {paired && (
        <p>
          source attempts {paired.source_attempts}; paired{" "}
          {paired.paired_attempts}; unvalued source attempts{" "}
          {paired.unvalued_source_attempts}. danger unavailable:{" "}
          {paired.danger_unavailable.events} paired attempts,{" "}
          {paired.danger_unavailable.observed_goals} recorded goals, reference
          expectation {number(paired.danger_unavailable.reference_expected_goals, 3)},
          actor expectation {number(paired.danger_unavailable.actor_expected_goals, 3)}.
        </p>
      )}
      {(["shot_type", "danger"] as const).map((kind) => (
        <div
          key={kind}
          className="table-scroll"
          role="region"
          tabIndex={0}
          aria-label={`${kind === "shot_type" ? "shot type" : "danger"} execution evidence table, scroll horizontally for all columns`}
        >
          <table>
            <caption>
              {kind === "shot_type"
                ? "shot type"
                : "reference-execution danger"}{" "}
              · each table partitions the paired personal attempts
              independently; do not add their totals
            </caption>
            <thead>
              <tr>
                <th scope="col">
                  {kind === "shot_type" ? "shot type" : "danger"}
                </th>
                <th scope="col">attempts</th>
                <th scope="col">recorded goals</th>
                <th scope="col">reference expected goals</th>
                <th scope="col">reference mean opportunity</th>
                <th scope="col">recorded − reference</th>
                <th scope="col">actor expected goals</th>
                <th scope="col">actor mean opportunity</th>
                <th scope="col">recorded − actor</th>
              </tr>
            </thead>
            <tbody>
              {data.breakdowns
                .filter((row) => row.kind === kind)
                .map((row) => (
                  <tr key={row.stratum}>
                    <th scope="row">{row.stratum}</th>
                    {row.result.availability === "provided" ? (
                      <Expectations data={row.result.data} />
                    ) : (
                      <td colSpan={8}>{row.result.explanation}</td>
                    )}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      ))}
      <p>
        danger uses the reference integrated goal probability given on-net:
        below .05; .05 to below .15; .15 and above. empty paired evidence does
        not assert no recorded activity. omitted values and their reasons remain
        below.
      </p>
      <button
        type="button"
        onClick={() => {
          try {
            downloadCsv(
              executionEvidenceCsvHeaders,
              executionEvidenceCsvRows(evidence, playerId),
              `hockey-stats-${playerId}-${evidence.season.season}-${evidence.selection.strength}-execution-evidence.csv`,
            );
            setStatus("evidence csv prepared");
          } catch {
            setStatus(
              "export failed; browsing remains available. retry the download.",
            );
          }
        }}
      >
        download evidence csv
      </button>
      <p role="status">{status}</p>
      <details className="analysis-evidence">
        <summary>
          keyed source and model evidence, support and omitted-value reasons
        </summary>
        <p>
          events can appear because this player is the shooter, a pre-outcome
          setter candidate or an execution-share recipient. these role events
          are not the personal shooting-strata total. setter candidates include
          inferred setup, none, unknown and known goalies; candidate weight is
          not an observed pass.
        </p>
        <pre>
          {JSON.stringify(
            data.breakdowns.map((row) => ({
              kind: row.kind,
              stratum: row.stratum,
              result: row.result,
            })),
            null,
            2,
          )}
        </pre>
        {data.attempts.map((attempt) => {
          const matches = (row: {
            season: string;
            game_id: string;
            source_index: number;
          }) =>
            row.season === attempt.season &&
            row.game_id === attempt.game_id &&
            row.source_index === attempt.source_index;
          const setters = data.setters.filter(matches);
          const shares = data.shares.filter(matches);
          const roles = [
            attempt.shooter_id === playerId ? "personal shooter" : null,
            setters.some((row) => row.candidate_id === playerId)
              ? "pre-outcome setter candidate"
              : null,
            ...shares
              .filter((row) => row.recipient_id === playerId)
              .map((row) => `${row.group} share recipient`),
          ].filter(Boolean);
          return (
            <details key={`${attempt.game_id}:${attempt.source_index}`}>
              <summary>
                {attempt.game_id} / source {attempt.source_index} ·{" "}
                {roles.join("; ") || "related role event"}
              </summary>
              <pre>{JSON.stringify({ attempt, setters, shares }, null, 2)}</pre>
            </details>
          );
        })}
        <p>
          publication {evidence.publication.publication_id};{" "}
          {evidence.publication.purpose}; corpus {evidence.season.corpus_sha256}
        </p>
      </details>
    </section>
  );
}
