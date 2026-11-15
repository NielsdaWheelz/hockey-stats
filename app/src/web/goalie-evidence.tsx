import { useState } from "react";
import type {
  GoalieDanger,
  GoalieEvidenceMap,
  MapsResponse,
  Support,
} from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import {
  goalieEvidenceDisplayCells,
  goaliePhysicalPoint,
} from "../shared/map-geometry";
import {
  AnalyticalMapDrawing,
  analyticalMapDrawingSvg,
  prepareMapDrawing,
  type AnalyticalMapModel,
} from "./analytical-map";
import { csvText, downloadBlob, svgPng, type CsvCell } from "./export";
import { displayNumber } from "./analysis-history";

type Response = Extract<MapsResponse, { family: "goalie_evidence" }>;
export type GoalieEvidenceMapModel = Pick<
  AnalyticalMapModel,
  | "playerId"
  | "companion"
  | "publication"
  | "season"
  | "title"
  | "orientation"
  | "availability"
  | "reason"
  | "reference"
  | "support"
  | "methodId"
  | "maximum"
  | "minimum"
  | "levels"
  | "legend"
  | "rectangles"
  | "contours"
  | "integral"
  | "warnings"
> & {
  readonly direction: "goalie";
  readonly densityUnit: "percent" | "goals_per100sqft";
  readonly densityLabel: string;
  readonly response: Response;
  readonly data: typeof GoalieEvidenceMap.Type | null;
  readonly ratio: boolean;
};

export function prepareGoalieEvidenceMap(
  response: MapsResponse,
  playerId: string,
): GoalieEvidenceMapModel {
  if (response.family !== "goalie_evidence")
    throw new Error("goalie evidence requires its published map family");
  const selected = response.players.find((row) => row.player_id === playerId);
  if (!selected) throw new Error("goalie map is missing its selected player");
  const data =
    selected.result.availability === "provided" ? selected.result.data : null;
  const ratio = response.selection.view === "evidence_ratio";
  const cells = data
    ? goalieEvidenceDisplayCells(
        response.definition.display_grid,
        data.display_cells,
      )
    : [];
  const drawing = prepareMapDrawing(
    cells.map((cell) => ({
      ...cell,
      mass: cell.mass_saved,
      density_per100sqft: ratio ? cell.ratio : cell.density_per100sqft,
    })),
    "goalie",
    response.scale.maximum,
    false,
    !ratio,
    ratio,
  );
  const method = data ? response.methods[data.method_id] : null;
  return {
    ...drawing,
    response,
    data,
    playerId,
    ratio,
    companion: response.selection.players.find((id) => id !== playerId) ?? null,
    publication: response.publication,
    season: response.season,
    title: `${response.selection.strength} ${response.selection.population} ${response.selection.type} · ${ratio ? "goals per expected relative to league" : "goals saved above expected"}`,
    direction: "goalie",
    orientation:
      "full rink: defended goal left; stored +x points left, +y down",
    availability: selected.result.availability,
    reason: selected.result.explanation,
    reference: data?.reference ?? null,
    support: data?.support ?? null,
    methodId: data?.method_id ?? null,
    maximum: response.scale.maximum,
    minimum: response.scale.minimum,
    integral: data ? data.totals.expected_goals - data.totals.goals : null,
    densityUnit: ratio ? "percent" : "goals_per100sqft",
    densityLabel: ratio
      ? "% relative to matched league goals per expected"
      : "goals saved / 100 sqft",
    warnings: method?.limitations ?? [],
  };
}

export function GoalieMapDrawing({
  model,
  render = "contours",
}: {
  readonly model: GoalieEvidenceMapModel;
  readonly render?: "contours" | "rectangles";
}) {
  const [inspection, setInspection] = useState<string | null>(null);
  return (
    <div className="goalie-map-drawing">
      <AnalyticalMapDrawing
        model={model}
        render={model.ratio ? "rectangles" : render}
        onPoint={(x, y) => {
          const point = goaliePhysicalPoint(x, y);
          const cell = model.rectangles.find(
            (row) =>
              point.x >= row.bounds.x_min &&
              point.x < row.bounds.x_max &&
              point.y >= row.bounds.y_min &&
              point.y < row.bounds.y_max,
          );
          setInspection(
            cell
              ? `stored x ${displayNumber(point.x)}, y ${displayNumber(point.y)} ft · cell ${cell.cellId} · ${cell.density === null ? "undefined ratio" : `${displayNumber(cell.density)} ${model.densityUnit}`} · saving mass ${displayNumber(cell.mass)}`
              : "outside the published display cells",
          );
        }}
      />
      {inspection && (
        <p className="goalie-map-inspection" role="status">
          {inspection}
        </p>
      )}
    </div>
  );
}

export function goalieRatioScaleText(model: GoalieEvidenceMapModel): string {
  if (!model.data)
    return "ratio-cell accounting unavailable; no published cell body";
  const defined = model.rectangles.flatMap((cell) =>
    cell.density === null ? [] : [Math.abs(cell.density)],
  );
  return `positive unfavorable; fixed ±25% saturation; ${defined.filter((value) => value > 25).length} overflow cells; largest |ratio| ${defined.length ? displayNumber(Math.max(...defined)) : "unavailable"}%; ${model.rectangles.length - defined.length} undefined cells hatched; no pseudocount`;
}

export function GoalieMapLegend({
  model,
}: {
  readonly model: GoalieEvidenceMapModel;
}) {
  return (
    <div
      className="analytical-density-legend goalie-density-legend"
      role="group"
      aria-label={`${model.title} legend`}
    >
      {model.legend.map((level) => (
        <span key={level.value}>
          <i aria-hidden="true" style={{ backgroundColor: level.fill }} />
          {displayNumber(level.value)}
        </span>
      ))}
      <p>
        {model.densityLabel};{" "}
        {model.ratio
          ? goalieRatioScaleText(model)
          : `positive is favorable; central band |density| < ${displayNumber(model.maximum / 4)}; zero scale is neutral`}
        .
      </p>
    </div>
  );
}

export const goalieSupportText = (support: Support | null) =>
  support
    ? `${support.included_seconds === null ? "unknown" : displayNumber(support.included_seconds / 60)} supported min; ${support.known_excluded_seconds === null ? "unknown" : displayNumber(support.known_excluded_seconds / 60)} known excluded min; ${support.prior_only ? "prior-only" : support.current_season_information ? "current information" : "mixed or no current information"}; carried seasons ${support.prior_seasons.join(", ") || "none"}${support.unquantified_gap ? "; unquantified gaps" : ""}`
    : "support unavailable";

export type GoalieCsvContext = {
  readonly publication: Publication;
  readonly season: SeasonEvidence;
  readonly playerId: string;
  readonly coreStrength: string | null;
  readonly strength: string;
  readonly population: string | null;
  readonly type: string | null;
  readonly methodId: string | null;
  readonly reference: string | null;
  readonly support: Support | null;
  readonly availability: string;
  readonly reason: string | null;
  readonly companion?: string | null;
};
export function goalieCsv(
  context: GoalieCsvContext,
  columns: readonly string[],
  rows: readonly (readonly CsvCell[])[],
): string {
  const headers = [
    "publication_id",
    "purpose",
    "season",
    "corpus_sha256",
    "player_id",
    "modeled_strength",
    "actual_strength",
    "population",
    "type",
    "method_id",
    "numeric_reference",
    "availability",
    "reason",
    "selection_support",
    "comparison_companion",
  ];
  const values: readonly CsvCell[] = [
    context.publication.publication_id,
    context.publication.purpose,
    context.season.season,
    context.season.corpus_sha256,
    context.playerId,
    context.coreStrength,
    context.strength,
    context.population,
    context.type,
    context.methodId,
    context.reference,
    context.availability,
    context.reason,
    context.support ? JSON.stringify(context.support) : null,
    context.companion,
  ];
  if (rows.some((row) => row.length > columns.length))
    throw new Error("goalie csv row exceeds its closed column contract");
  return csvText(
    [...headers, ...columns],
    rows.map((row) => [
      ...values,
      ...columns.map((_, index) => row[index] ?? null),
    ]),
  );
}
const mapContext = (model: GoalieEvidenceMapModel): GoalieCsvContext => ({
  publication: model.publication,
  season: model.season,
  playerId: model.playerId,
  coreStrength: null,
  strength: model.response.selection.strength,
  population: model.response.selection.population,
  type: model.response.selection.type,
  methodId: model.methodId,
  reference: model.reference,
  support: model.support,
  availability: model.availability,
  reason: model.reason,
  companion: model.companion,
});

export function goalieMapCsv(model: GoalieEvidenceMapModel): string {
  const columns = [
    "record_kind",
    "cell_id",
    "x_ft",
    "y_ft",
    "x_min",
    "x_max",
    "y_min",
    "y_max",
    "area_sqft",
    "goals",
    "expected_goals",
    "attempts",
    "mass_saved",
    "density_per100sqft",
    "ratio",
    "ratio_unavailable_reason",
    "league_goals",
    "league_expected_goals",
    "display_mode",
    "scale_minimum",
    "scale_maximum",
    "unit",
  ];
  const data = model.data;
  if (!data) return goalieCsv(mapContext(model), columns, [[]]);
  const native = new Map(
    model.response.definition.native_grid.cells.map((cell) => [
      cell.cell_id,
      cell,
    ]),
  );
  const common: readonly CsvCell[] = [
    data.league_goals,
    data.league_expected_goals,
    model.ratio ? "ratio" : "mass",
    model.minimum,
    model.maximum,
    model.densityUnit,
  ];
  const rows: CsvCell[][] = data.native_cells.map((cell) => {
    const point = native.get(cell.cell_id);
    if (!point) throw new Error("goalie native map geometry is missing");
    return [
      "native",
      cell.cell_id,
      point.x_ft,
      point.y_ft,
      null,
      null,
      null,
      null,
      null,
      cell.goals,
      cell.expected_goals,
      cell.attempts,
      cell.expected_goals - cell.goals,
      null,
      null,
      null,
      ...common,
    ];
  });
  for (const cell of goalieEvidenceDisplayCells(
    model.response.definition.display_grid,
    data.display_cells,
  ))
    rows.push([
      "display",
      cell.cell_id,
      null,
      null,
      cell.bounds.x_min,
      cell.bounds.x_max,
      cell.bounds.y_min,
      cell.bounds.y_max,
      cell.bounds.area_sqft,
      cell.goals,
      cell.expected_goals,
      cell.attempts,
      cell.mass_saved,
      cell.density_per100sqft,
      cell.ratio,
      cell.unavailable_reason,
      ...common,
    ]);
  for (const kind of ["unmapped", "total"] as const) {
    const value = kind === "total" ? data.totals : data.unmapped;
    rows.push([
      kind,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      null,
      value.goals,
      value.expected_goals,
      value.attempts,
      value.expected_goals - value.goals,
      null,
      null,
      null,
      ...common,
    ]);
  }
  return goalieCsv(mapContext(model), columns, rows);
}

export function goalieDangerCsv(
  context: GoalieCsvContext,
  danger: typeof GoalieDanger.Type | null,
): string {
  const columns = [
    "bin",
    "lower",
    "upper",
    "upper_inclusive",
    "attempts",
    "actual_goal_mass",
    "expected_goal_mass",
    "actual_density_per_probability_percentage_point",
    "expected_density_per_probability_percentage_point",
    "total_attempts",
    "total_goals",
    "total_expected_goals",
    "unit",
  ];
  return goalieCsv(
    context,
    columns,
    danger
      ? danger.attempt_counts.map((attempts, i) => [
          i,
          danger.edges[i],
          danger.edges[i + 1],
          i === 99,
          attempts,
          danger.goal_mass[i],
          danger.expected_goal_mass[i],
          danger.goal_mass[i],
          danger.expected_goal_mass[i],
          danger.totals.attempts,
          danger.totals.goals,
          danger.totals.expected_goals,
          "goals per probability percentage point",
        ])
      : [[]],
  );
}

export function GoalieDangerPlot({
  danger,
}: {
  readonly danger: typeof GoalieDanger.Type;
}) {
  const maximum = Math.max(
    0,
    ...danger.goal_mass,
    ...danger.expected_goal_mass,
  );
  const y = (value: number) => 160 - (maximum ? (145 * value) / maximum : 0);
  const path = (values: readonly number[]) =>
    values
      .map(
        (value, i) =>
          `${i ? "L" : "M"}${65 + i * 4.2},${y(value)}H${65 + (i + 1) * 4.2}`,
      )
      .join("");
  return (
    <svg
      className="goalie-danger-plot"
      viewBox="0 0 520 205"
      role="img"
      aria-label="actual and expected goal mass per probability percentage point"
    >
      <path d="M65 10V160H485" fill="none" stroke="#64767b" />
      <path
        d={path(danger.expected_goal_mass)}
        stroke="#242b2d"
        strokeWidth="2"
        fill="none"
      />
      <path
        d={path(danger.goal_mass)}
        stroke="#b2182b"
        strokeWidth="2"
        fill="none"
      />
      <text x="2" y="18" fontSize="12">
        {displayNumber(maximum)}
      </text>
      <text x="12" y="163" fontSize="12">
        0
      </text>
      {[0, 25, 50, 75, 100].map((p) => (
        <text
          key={p}
          x={65 + 4.2 * p}
          y="180"
          fontSize="12"
          textAnchor="middle"
        >
          {p}%
        </text>
      ))}
      <text x="260" y="201" fontSize="12" textAnchor="middle">
        selected-population neutral-goalie probability
      </text>
    </svg>
  );
}

export function goalieDangerDrawingSvg(
  danger: typeof GoalieDanger.Type,
): string {
  const maximum = Math.max(
    0,
    ...danger.goal_mass,
    ...danger.expected_goal_mass,
  );
  const path = (values: readonly number[]) =>
    values
      .map(
        (value, i) =>
          `${i ? "L" : "M"}${90 + i * 10},${240 - (maximum ? (210 * value) / maximum : 0)}H${90 + (i + 1) * 10}`,
      )
      .join("");
  return `<svg viewBox="0 0 1112 300"><text x="3" y="30" font-size="20">${Number(maximum.toPrecision(4))}</text><text x="3" y="241" font-size="20">0</text><path d="M90 20V240H1090" stroke="#64767b" fill="none"/><path d="${path(danger.expected_goal_mass)}" stroke="#242b2d" stroke-width="3" fill="none"/><path d="${path(danger.goal_mass)}" stroke="#b2182b" stroke-width="3" fill="none"/>${[0, 25, 50, 75, 100].map((p) => `<text x="${90 + 10 * p}" y="270" font-size="20" text-anchor="middle">${p}%</text>`).join("")}<text x="556" y="298" font-size="20" text-anchor="middle">selected-population neutral-goalie probability; goals per one percentage point</text></svg>`;
}

export function goalieEvidenceMapSvg(
  model: GoalieEvidenceMapModel,
  render: "contours" | "rectangles" = "contours",
): string {
  const escape = (value: string) =>
    value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll('"', "&quot;");
  const parts: string[] = [];
  let y = 40;
  const line = (value: string, size = 20) => {
    const limit = Math.floor(1112 / (size * 0.6));
    let current = "";
    for (const word of value.split(/\s+/)) {
      if (current && current.length + word.length + 1 > limit) {
        parts.push(
          `<text x="44" y="${y}" font-size="${size}">${escape(current)}</text>`,
        );
        y += size + 8;
        current = "";
      }
      for (let i = 0; i < word.length; i += limit) {
        const chunk = word.slice(i, i + limit);
        if (i + limit < word.length) {
          if (current) {
            parts.push(
              `<text x="44" y="${y}" font-size="${size}">${escape(current)}</text>`,
            );
            y += size + 8;
            current = "";
          }
          parts.push(
            `<text x="44" y="${y}" font-size="${size}">${escape(chunk)}</text>`,
          );
          y += size + 8;
        } else current += `${current ? " " : ""}${chunk}`;
      }
    }
    if (current) {
      parts.push(
        `<text x="44" y="${y}" font-size="${size}">${escape(current)}</text>`,
      );
      y += size + 8;
    }
  };
  line(
    `${model.publication.purpose === "fixture" ? "synthetic fixture · " : ""}player ${model.playerId} · ${model.season.season}`,
  );
  line(model.title, 24);
  y += 10;
  if (model.data)
    parts.push(
      `<svg x="44" y="${y}" width="1112" height="474">${analyticalMapDrawingSvg(model, "selected-goalie", model.ratio ? "rectangles" : render)}</svg>`,
    );
  else line(`${model.availability}: ${model.reason}`);
  y += 510;
  for (const [index, level] of model.legend.entries()) {
    const x = 44 + (index * 1112) / model.legend.length;
    parts.push(
      `<rect x="${x}" y="${y}" width="${1112 / model.legend.length}" height="20" fill="${level.fill}"/><text x="${x + 5}" y="${y + 48}" font-size="20">${Number(level.value.toPrecision(3))}</text>`,
    );
  }
  y += 90;
  line(model.densityLabel);
  line(
    !model.data
      ? "map unavailable; no cell values or neutral fill supplied"
      : model.ratio
        ? `${goalieRatioScaleText(model)}. ratios are nonadditive and volatile at small expected mass.`
        : `positive favorable; central band |density| < ${displayNumber(model.maximum / 4)}; zero scale is neutral. mapped saving ${displayNumber(model.rectangles.reduce((sum, cell) => sum + cell.mass, 0))}; unmapped ${model.data ? displayNumber(model.data.unmapped.expected_goals - model.data.unmapped.goals) : "unavailable"}; total ${displayNumber(model.integral)} goals.`,
  );
  line(
    `${model.orientation}; published 10ft pooling, ${model.ratio ? "masked display cells" : render === "contours" ? "linear contour interpolation" : "display rectangles"}; no measured subcell precision.`,
  );
  line(
    `reference ${model.reference ?? "unavailable"}; method ${model.methodId ?? "unavailable"}.`,
  );
  line(goalieSupportText(model.support));
  for (const warning of model.warnings) line(warning);
  line(
    `publication ${model.publication.publication_id}${model.companion ? `; shared corresponding scales with player ${model.companion}` : ""}.`,
  );
  y += 20;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${y}" viewBox="0 0 1200 ${y}" font-family="ui-monospace,Menlo,monospace" fill="#242b2d"><rect width="1200" height="${y}" fill="#fbfaf6"/>${parts.join("")}</svg>`;
}

export function GoalieEvidenceMapFigure({
  model,
  render = "contours",
}: {
  readonly model: GoalieEvidenceMapModel;
  readonly render?: "contours" | "rectangles";
}) {
  const [status, setStatus] = useState("");
  const [cells, setCells] = useState(false);
  return (
    <figure className="goalie-evidence-map">
      <figcaption>{model.title}</figcaption>
      {model.data ? (
        <GoalieMapDrawing model={model} render={render} />
      ) : (
        <p>
          {model.availability}: {model.reason}
        </p>
      )}
      <GoalieMapLegend model={model} />
      <p>
        {model.orientation}; 10ft published pooling; contour interpolation adds
        no measured precision.
      </p>
      <p>
        {model.data
          ? `total saving ${displayNumber(model.integral)} goals; mapped ${displayNumber(model.rectangles.reduce((sum, cell) => sum + cell.mass, 0))}, unmapped ${displayNumber(model.data.unmapped.expected_goals - model.data.unmapped.goals)}. native and display representations must not be added.`
          : "no invented neutral map"}
      </p>
      <p>
        reference {model.reference ?? "unavailable"};{" "}
        {goalieSupportText(model.support)}. ratios are nonadditive and volatile
        at small expected mass.
      </p>
      <details onToggle={(event) => setCells(event.currentTarget.open)}>
        <summary>native/display cells and unmapped evidence</summary>
        {cells && (
          <div className="table-scroll" tabIndex={0}>
            <table>
              <caption>
                stored coordinates; native and display are alternative
                representations
              </caption>
              <thead>
                <tr>
                  <th>record</th>
                  <th>cell</th>
                  <th>goals</th>
                  <th>expected</th>
                  <th>attempts</th>
                  <th>mass saved</th>
                  <th>density /100sqft</th>
                  <th>ratio</th>
                </tr>
              </thead>
              <tbody>
                {model.data?.native_cells.map((row) => (
                  <tr key={`native-${row.cell_id}`}>
                    <th>native</th>
                    <td>{row.cell_id}</td>
                    <td>{row.goals}</td>
                    <td>{row.expected_goals}</td>
                    <td>{row.attempts}</td>
                    <td>{row.expected_goals - row.goals}</td>
                    <td></td>
                    <td></td>
                  </tr>
                ))}
                {model.data &&
                  goalieEvidenceDisplayCells(
                    model.response.definition.display_grid,
                    model.data.display_cells,
                  ).map((row) => (
                    <tr key={`display-${row.cell_id}`}>
                      <th>display</th>
                      <td>{row.cell_id}</td>
                      <td>{row.goals}</td>
                      <td>{row.expected_goals}</td>
                      <td>{row.attempts}</td>
                      <td>{row.mass_saved}</td>
                      <td>{row.density_per100sqft}</td>
                      <td>{row.ratio ?? row.unavailable_reason}</td>
                    </tr>
                  ))}
                {model.data &&
                  (["unmapped", "totals"] as const).map((kind) => (
                    <tr key={kind}>
                      <th>{kind}</th>
                      <td></td>
                      <td>{model.data![kind].goals}</td>
                      <td>{model.data![kind].expected_goals}</td>
                      <td>{model.data![kind].attempts}</td>
                      <td>
                        {model.data![kind].expected_goals -
                          model.data![kind].goals}
                      </td>
                      <td></td>
                      <td></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </details>
      <div className="card-actions">
        <button
          type="button"
          onClick={async () => {
            const snapshot = { model, render };
            try {
              const svg = goalieEvidenceMapSvg(snapshot.model, snapshot.render);
              downloadBlob(
                await svgPng(svg),
                `hockey-stats-${model.season.season}-${model.playerId}-goalie-map.png`,
              );
              setStatus("map png prepared");
            } catch {
              setStatus("map export failed; retry the download");
            }
          }}
        >
          download selected goalie map png
        </button>
        <button
          type="button"
          onClick={() =>
            downloadBlob(
              new Blob([goalieMapCsv(model)], {
                type: "text/csv;charset=utf-8",
              }),
              `hockey-stats-${model.season.season}-${model.playerId}-goalie-map.csv`,
            )
          }
        >
          download goalie-map.csv
        </button>
        <p role="status">{status}</p>
      </div>
    </figure>
  );
}
