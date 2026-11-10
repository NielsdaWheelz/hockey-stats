import { contours } from "d3-contour";
import { useId, useState } from "react";
import type {
  MapsResponse,
  Support,
  MapUnit,
  QuantityPath,
} from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import { csvText, downloadBlob, svgPng } from "./export";
import { displayNumber } from "./analysis-history";
import Rink from "./rink";

type ModelResponse = Exclude<
  MapsResponse,
  { readonly family: "observed" | "goalie_evidence" }
>;
export type AnalyticalMapModel = {
  readonly playerId: string;
  readonly companion: string | null;
  readonly publication: Publication;
  readonly season: SeasonEvidence;
  readonly family: ModelResponse["family"];
  readonly strength: ModelResponse["selection"]["strength"];
  readonly view: ModelResponse["selection"]["view"];
  readonly title: string;
  readonly direction: "offense" | "defense";
  readonly orientation: string;
  readonly availability: "provided" | "not_computed" | "absent" | "unavailable";
  readonly reason: string | null;
  readonly reference: string | null;
  readonly support: Support | null;
  readonly methodId: string | null;
  readonly warnings: readonly string[];
  readonly unit: string;
  readonly unitLabel: string;
  readonly densityUnit: string;
  readonly densityLabel: string;
  readonly integral: number | null;
  readonly maximum: number;
  readonly minimum: number;
  readonly levels: readonly number[];
  readonly legend: readonly { readonly value: number; readonly fill: string }[];
  readonly nativeCells: readonly {
    readonly cell_id: number;
    readonly x_ft: number;
    readonly y_ft: number;
    readonly value: number;
  }[];
  readonly rectangles: readonly {
    readonly cellId: number;
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
    readonly fill: string;
    readonly density: number;
    readonly mass: number;
    readonly bounds: ModelResponse["definition"]["display_grid"]["cells"][number];
  }[];
  readonly contours: readonly {
    readonly level: number;
    readonly path: string;
    readonly fill: string;
  }[];
};

const neutral = "#f7f7f2";
const positive = ["#f3c7cb", "#dc8c95", "#c64d5f", "#b2182b"];
const negative = ["#c7d9e7", "#91b5d1", "#5891bc", "#2166ac"];
const complete = [
  "#e3edf5",
  "#c7d9e7",
  "#abc5dc",
  "#91b5d1",
  "#74a3c6",
  "#5891bc",
  "#3c7bb4",
  "#2166ac",
];
const unitLabels: Readonly<Record<typeof MapUnit.Type, string>> = {
  attempts_per60: "attempts/60 min",
  xg_per60: "xg/60 min",
  goals_per100_attempts: "goals/100 attempts",
  goals_per100_assisted_opportunities: "goals/100 setup opportunities",
  goals_per_basket: "goals/declared basket",
  goals_per100_on_net: "goals/100 on-net attempts",
};
const mapUnits: Readonly<Record<ModelResponse["family"], typeof MapUnit.Type>> =
  {
    offense_attempts: "attempts_per60",
    defense_attempts: "attempts_per60",
    offense_xg: "xg_per60",
    defense_xg: "xg_per60",
    finishing: "goals_per100_attempts",
    setting: "goals_per100_assisted_opportunities",
    ice_won: "goals_per_basket",
    ice_lost: "goals_per_basket",
    goalie_stopping: "goals_per100_on_net",
  };
const color = (value: number, maximum: number, absolute: boolean): string => {
  if (maximum === 0 || value === 0) return neutral;
  const palette = absolute ? complete : value < 0 ? negative : positive;
  const level = palette.reduce(
    (count, _, index) =>
      count +
      (Math.abs(value) >= maximum * ((index + 1) / palette.length) ? 1 : 0),
    0,
  );
  return level === 0 ? neutral : palette[level - 1];
};

export function prepareAnalyticalMap(
  response: MapsResponse,
  playerId: string,
): AnalyticalMapModel {
  if (response.family === "observed" || response.family === "goalie_evidence")
    throw new Error("analytical maps require a published model map");
  const selected = response.players.find((row) => row.player_id === playerId);
  if (!selected)
    throw new Error("analytical map is missing its selected player");
  const result = selected.result;
  const data = result.availability === "provided" ? result.data : null;
  const direction =
    response.family.startsWith("defense_") || response.family === "ice_lost"
      ? "defense"
      : "offense";
  const absolute = response.selection.view === "complete";
  const maximum = response.scale.maximum;
  const magnitudes =
    maximum === 0
      ? []
      : Array.from(
          { length: absolute ? 8 : 4 },
          (_, i) => maximum * ((i + 1) / (absolute ? 8 : 4)),
        );
  const levels =
    maximum === 0
      ? [0]
      : absolute
        ? [0, ...magnitudes]
        : [...magnitudes.map((level) => -level).reverse(), 0, ...magnitudes];
  const display = new Map(
    response.definition.display_grid.cells.map((cell) => [cell.cell_id, cell]),
  );
  const rectangles = (data?.display_cells ?? []).map((cell) => {
    const bounds = display.get(cell.cell_id);
    if (!bounds) throw new Error("analytical map display geometry is missing");
    return {
      cellId: cell.cell_id,
      x: direction === "offense" ? 42.5 + bounds.y_min : 42.5 - bounds.y_max,
      y: direction === "offense" ? 100 - bounds.x_max : 100 + bounds.x_min,
      width: bounds.y_max - bounds.y_min,
      height: bounds.x_max - bounds.x_min,
      fill: color(cell.density_per100sqft, maximum, absolute),
      density: cell.density_per100sqft,
      mass: cell.mass,
      bounds,
    };
  });
  const raster = new Array<number>(40 * 17).fill(0);
  for (const cell of data?.display_cells ?? []) {
    const xi = Math.floor(cell.cell_id / 17),
      yi = cell.cell_id % 17;
    raster[xi + 40 * yi] = cell.density_per100sqft;
  }
  const geometry = contours()
    .size([40, 17])
    .thresholds(magnitudes)
    .smooth(true);
  const polygons =
    data?.display_cells && maximum > 0
      ? [
          ...geometry(raster).map((polygon) => ({ polygon, sign: 1 })),
          ...(absolute
            ? []
            : geometry(raster.map((value) => -value)).map((polygon) => ({
                polygon,
                sign: -1,
              }))),
        ]
      : [];
  const paths = polygons.map(({ polygon, sign }) => ({
    level: sign * polygon.value,
    fill: color(sign * polygon.value, maximum, absolute),
    path: polygon.coordinates
      .flatMap((shape) =>
        shape.map(
          (ring) =>
            ring
              .map(([u, v], i) => {
                const x = -100 + 5 * u,
                  y = -42.5 + 5 * v;
                return `${i === 0 ? "M" : "L"}${direction === "offense" ? 42.5 + y : 42.5 - y},${direction === "offense" ? 100 - x : 100 + x}`;
              })
              .join("") + "Z",
        ),
      )
      .join(""),
  }));
  const native = new Map(
    response.definition.native_grid.cells.map((cell) => [cell.cell_id, cell]),
  );
  const method = data ? response.methods[data.method_id] : null;
  const quantity: Readonly<
    Record<ModelResponse["family"], typeof QuantityPath.Type>
  > = {
    offense_attempts: "skater_spatial.offense_attempts_per60",
    defense_attempts: "skater_spatial.defense_attempts_per60",
    offense_xg: "skater_spatial.offense_xg_per60",
    defense_xg: "skater_spatial.defense_xg_per60",
    finishing: "skater_execution.finishing_goals_per100_attempts",
    setting: "skater_execution.setting_goals_per100_assisted_opportunities",
    ice_won: "skater_territory.ice_won_goals_per_basket",
    ice_lost: "skater_territory.ice_lost_goals_per_basket",
    goalie_stopping: "goalie_result.stopping_goals_per100_on_net",
  };
  const unit = data?.unit ?? mapUnits[response.family];
  return {
    playerId,
    companion: response.selection.players.find((id) => id !== playerId) ?? null,
    publication: response.publication,
    season: response.season,
    family: response.family,
    strength: response.selection.strength,
    view: response.selection.view,
    title: `${response.selection.strength} ${response.family.replaceAll("_", " ")} · ${absolute ? "complete focal rate" : "effect"}`,
    direction,
    orientation:
      direction === "offense"
        ? "full rink: attacking goal above; +x up, +y right"
        : "full rink: defended goal below; +x down, +y left; both axes rotated 180°",
    availability: data
      ? data.cells
        ? "provided"
        : "unavailable"
      : result.availability,
    reason: data
      ? (data.reason_detail?.explanation ?? data.unavailable_reason)
      : result.explanation,
    reference: data?.reference ?? null,
    support: data?.support ?? null,
    methodId: data?.method_id ?? null,
    warnings:
      method?.assessment.findings
        .filter((finding) =>
          finding.quantities.includes(quantity[response.family]),
        )
        .map((finding) => finding.summary) ?? [],
    unit,
    unitLabel: unitLabels[unit],
    densityUnit: response.scale.unit,
    densityLabel: `${unitLabels[unit]}/100 sqft`,
    integral: data?.integrated_value ?? null,
    maximum,
    minimum: response.scale.minimum,
    levels,
    legend: levels.map((value) => ({
      value,
      fill: color(value, maximum, absolute),
    })),
    nativeCells: (data?.cells ?? []).map((cell) => {
      const point = native.get(cell.cell_id);
      if (!point) throw new Error("analytical map native geometry is missing");
      return { ...point, value: cell.value };
    }),
    rectangles,
    contours: paths,
  };
}

export const analyticalMapSupport = (model: AnalyticalMapModel): string =>
  model.support
    ? `${model.support.included_seconds === null ? "unknown" : displayNumber(model.support.included_seconds / 60)} included min; ${model.support.prior_only ? "prior-only hypothetical estimate" : model.support.current_season_information ? "some current focal information" : "no current focal information"}; ${model.support.known_excluded_seconds === null ? "unknown" : displayNumber(model.support.known_excluded_seconds / 60)} excluded min; ${model.support.unquantified_gap ? "unquantified gaps" : "declared included population"}`
    : (model.reason ?? "map support unavailable");

export function AnalyticalMapDrawing({
  model,
  render = "contours",
}: {
  readonly model: AnalyticalMapModel;
  readonly render?: "contours" | "rectangles";
}) {
  return (
    <Rink
      className="analytical-rink"
      label={model.title}
      description={`${model.orientation}; ${model.densityUnit}; 10ft display pooling, contour interpolation is not measured subcell precision`}
    >
      <rect x="0" y="0" width="85" height="200" fill={neutral} />
      {render === "rectangles"
        ? model.rectangles.map((cell) => (
            <rect
              key={cell.cellId}
              x={cell.x}
              y={cell.y}
              width={cell.width}
              height={cell.height}
              fill={cell.fill}
            >
              <title>{`cell ${cell.cellId}; density ${cell.density}; display mass ${cell.mass}; raw x ${cell.bounds.x_min}…${cell.bounds.x_max}, y ${cell.bounds.y_min}…${cell.bounds.y_max} ft`}</title>
            </rect>
          ))
        : model.contours.map((contour) => (
            <path
              key={contour.level}
              d={contour.path}
              fill={contour.fill}
              fillRule="evenodd"
            />
          ))}
    </Rink>
  );
}

export function AnalyticalMapLegend({
  model,
}: {
  readonly model: AnalyticalMapModel;
}) {
  return (
    <div
      className="analytical-density-legend"
      role="group"
      aria-label={`${model.title}; density color legend`}
    >
      {model.legend.map((level) => (
        <span key={level.value}>
          <i aria-hidden="true" style={{ backgroundColor: level.fill }} />
          {displayNumber(level.value)}
        </span>
      ))}
      <p>
        {model.densityLabel};{" "}
        {model.integral === null
          ? "map unavailable"
          : model.maximum === 0
            ? "all-zero map"
            : model.view === "complete"
              ? "complete nonnegative density"
              : `central neutral band: |density| < ${displayNumber(model.maximum / 4)}, not exact zero`}
      </p>
    </div>
  );
}

export function AnalyticalMapFigure({
  model,
  render = "contours",
  tables = true,
  downloads = true,
}: {
  readonly model: AnalyticalMapModel;
  readonly render?: "contours" | "rectangles";
  readonly tables?: boolean;
  readonly downloads?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState("");
  const id = useId();
  return (
    <figure className="analytical-map" aria-labelledby={id}>
      <figcaption id={id}>{model.title}</figcaption>
      {model.integral === null ? (
        <p>
          {model.availability}: {model.reason}
        </p>
      ) : (
        <AnalyticalMapDrawing model={model} render={render} />
      )}
      <p>{model.orientation}</p>
      <p>
        integral {displayNumber(model.integral)} {model.unitLabel} · density{" "}
        {model.densityLabel}
      </p>
      <AnalyticalMapLegend model={model} />
      <p className="analytical-map-levels">
        legend levels: {model.levels.map(displayNumber).join(" · ")}
        {model.integral === null
          ? " · map unavailable"
          : model.maximum === 0
            ? " · all-zero map: neutral fill"
            : model.view === "effect"
              ? `; neutral band: magnitude below ${displayNumber(model.maximum / 4)}, not exact zero`
              : ""}
      </p>
      <p>
        reference: {model.reference ?? "unavailable"}.{" "}
        {analyticalMapSupport(model)}.
      </p>
      <p>
        experimental adjusted estimate; calibrated player uncertainty is
        unknown. published native mass and display density; 10ft gaussian
        pooling, then linear contour interpolation. no measured subcell
        precision.{" "}
        {model.view === "complete" &&
          "one focal player in the virtual reference; not recorded on-ice results or actual deployment."}
        {model.direction === "defense" &&
          " positive differences mean more against."}
      </p>
      {model.warnings.map((warning) => (
        <p className="analytical-warning" key={warning}>
          {warning}
        </p>
      ))}
      {tables && (
        <details onToggle={(event) => setOpen(event.currentTarget.open)}>
          <summary>native and display numerical evidence</summary>
          {open && (
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="native and display map values; scroll horizontally"
            >
              <table>
                <caption>
                  native centers have no rectangular footprint; mass uses{" "}
                  {model.unit}
                </caption>
                <thead>
                  <tr>
                    <th>native cell</th>
                    <th>x ft</th>
                    <th>y ft</th>
                    <th>native mass</th>
                  </tr>
                </thead>
                <tbody>
                  {model.nativeCells.map((cell) => (
                    <tr key={cell.cell_id}>
                      <th>{cell.cell_id}</th>
                      <td>{cell.x_ft}</td>
                      <td>{cell.y_ft}</td>
                      <td>{cell.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <table>
                <caption>
                  display rectangles clipped to the physical rink; raw
                  coordinates retain stored orientation
                </caption>
                <thead>
                  <tr>
                    <th>display cell</th>
                    <th>x bounds ft</th>
                    <th>y bounds ft</th>
                    <th>area sqft</th>
                    <th>display mass</th>
                    <th>density per100sqft</th>
                  </tr>
                </thead>
                <tbody>
                  {model.rectangles.map((cell) => (
                    <tr key={cell.cellId}>
                      <th>{cell.cellId}</th>
                      <td>
                        {cell.bounds.x_min}…{cell.bounds.x_max}
                      </td>
                      <td>
                        {cell.bounds.y_min}…{cell.bounds.y_max}
                      </td>
                      <td>{cell.bounds.area_sqft}</td>
                      <td>{cell.mass}</td>
                      <td>{cell.density}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </details>
      )}
      {downloads && (
        <div className="card-actions">
          <button
            type="button"
            onClick={async () => {
              const snapshot = { model, render };
              try {
                const blob = await svgPng(
                  analyticalMapSvg(snapshot.model, snapshot.render),
                );
                downloadBlob(
                  blob,
                  `hockey-stats-${snapshot.model.season.season}-${snapshot.model.playerId}-${snapshot.model.family}-${snapshot.model.strength}-${snapshot.model.view}${snapshot.model.companion ? `-with-${snapshot.model.companion}` : ""}-map.png`,
                );
                setStatus("map png prepared");
              } catch {
                setStatus("map export failed; retry the download");
              }
            }}
          >
            download selected map png
          </button>
          <button
            type="button"
            onClick={() =>
              downloadBlob(
                new Blob([analyticalMapCsv(model)], {
                  type: "text/csv;charset=utf-8",
                }),
                `hockey-stats-${model.season.season}-${model.playerId}-${model.family}-${model.strength}-${model.view}${model.companion ? `-with-${model.companion}` : ""}-map.csv`,
              )
            }
          >
            download selected map csv
          </button>
          <p role="status">{status}</p>
        </div>
      )}
    </figure>
  );
}

const xml = (value: string | number) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
export function analyticalMapDrawingSvg(
  model: AnalyticalMapModel,
  id: string,
  render: "contours" | "rectangles" = "contours",
): string {
  return `<svg viewBox="-1 -1 87 202" width="100%" height="100%"><title>${xml(model.title)}</title><desc>${xml(model.orientation)}</desc><defs><clipPath id="${id}"><rect width="85" height="200" rx="28"/></clipPath></defs><g clip-path="url(#${id})"><rect width="85" height="200" fill="${neutral}"/>${render === "rectangles" ? model.rectangles.map((cell) => `<rect x="${cell.x}" y="${cell.y}" width="${cell.width}" height="${cell.height}" fill="${cell.fill}"/>`).join("") : model.contours.map((contour) => `<path d="${contour.path}" fill="${contour.fill}" fill-rule="evenodd"/>`).join("")}<g fill="none" stroke="#64767b" stroke-width="0.3"><path d="M0 75H85M0 125H85M0 100H85"/><circle cx="42.5" cy="100" r="15"/><path d="M39.5 11H45.5M39.5 189H45.5"/></g></g><rect width="85" height="200" rx="28" fill="none" stroke="#59676d" stroke-width="0.6"/></svg>`;
}

export function analyticalMapSvg(
  model: AnalyticalMapModel,
  render: "contours" | "rectangles" = "contours",
): string {
  const parts: string[] = [];
  let y = 44;
  const text = (value: string) => {
    const words = value.split(/\s+/);
    let line = "";
    for (const word of words) {
      if (line.length + word.length > 91) {
        parts.push(`<text x="44" y="${y}" font-size="20">${xml(line)}</text>`);
        y += 27;
        line = "";
      }
      line += `${line ? " " : ""}${word}`;
    }
    if (line) {
      parts.push(`<text x="44" y="${y}" font-size="20">${xml(line)}</text>`);
      y += 27;
    }
  };
  text(
    `${model.publication.purpose === "fixture" ? "synthetic fixture · " : ""}${model.season.season} · player ${model.playerId} · ${model.title}`,
  );
  if (model.integral !== null)
    parts.push(
      `<svg x="335" y="${y}" width="530" height="1260">${analyticalMapDrawingSvg(model, "selected-map", render)}</svg>`,
    );
  y += model.integral !== null ? 1300 : 25;
  model.legend.forEach((level, index) =>
    parts.push(
      `<rect x="${44 + (index * 1112) / model.legend.length}" y="${y}" width="${1112 / model.legend.length}" height="22" fill="${level.fill}"/>`,
    ),
  );
  y += 48;
  for (const line of [
    model.orientation,
    `integral ${displayNumber(model.integral)} ${model.unitLabel}; density ${model.densityLabel}`,
    `shared legend levels: ${model.levels.map(displayNumber).join(" · ")}; ${model.integral === null ? "map unavailable" : model.maximum === 0 ? "all-zero map" : "neutral band below first signed threshold"}`,
    ...(model.companion
      ? [
          `shared comparison scale with player ${model.companion}; selected player ${model.playerId}`,
        ]
      : []),
    `reference: ${model.reference ?? "unavailable"}`,
    analyticalMapSupport(model),
    `${model.availability}: ${model.reason ?? "published output"}; native/display data in csv; 10ft pooling and linear contour interpolation imply no measured subcell precision.`,
    "experimental estimate; calibrated player uncertainty is unknown.",
    ...(model.view === "complete"
      ? [
          "one focal player in the virtual reference; not actual deployment or recorded results",
        ]
      : []),
    ...model.warnings,
    `publication ${model.publication.publication_id}; method ${model.methodId ?? "unavailable"}`,
  ])
    text(line);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${y + 30}" viewBox="0 0 1200 ${y + 30}" font-family="system-ui,sans-serif" fill="#242b2d"><rect width="1200" height="${y + 30}" fill="#fbfaf6"/>${parts.join("")}</svg>`;
}

export function analyticalMapCsv(model: AnalyticalMapModel): string {
  const context = [
    model.publication.publication_id,
    model.publication.purpose,
    model.season.season,
    model.playerId,
    model.family,
    model.strength,
    model.view,
    model.availability,
    model.reason,
    model.unit,
    model.densityUnit,
    model.integral,
    model.reference,
    model.methodId,
    JSON.stringify(model.support),
    JSON.stringify(model.warnings),
    model.minimum,
    model.maximum,
    JSON.stringify(model.levels),
    model.companion,
  ];
  return csvText(
    [
      "record_kind",
      "grid_id",
      "cell_id",
      "x_ft",
      "y_ft",
      "x_min_ft",
      "x_max_ft",
      "y_min_ft",
      "y_max_ft",
      "area_sqft",
      "native_mass",
      "display_mass",
      "display_density_per100sqft",
      "publication_id",
      "purpose",
      "season",
      "player_id",
      "map_kind",
      "strength",
      "view",
      "availability",
      "reason",
      "integral_unit",
      "density_unit",
      "integral",
      "reference",
      "method_id",
      "support",
      "limitations",
      "scale_minimum",
      "scale_maximum",
      "legend_levels",
      "comparison_companion",
    ],
    [
      [
        "metadata",
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        ...context,
      ],
      ...model.nativeCells.map((cell) => [
        "native",
        "native656",
        cell.cell_id,
        cell.x_ft,
        cell.y_ft,
        null,
        null,
        null,
        null,
        null,
        cell.value,
        null,
        null,
        ...context,
      ]),
      ...model.rectangles.map((cell) => [
        "display",
        "display668",
        cell.cellId,
        null,
        null,
        cell.bounds.x_min,
        cell.bounds.x_max,
        cell.bounds.y_min,
        cell.bounds.y_max,
        cell.bounds.area_sqft,
        null,
        cell.mass,
        cell.density,
        ...context,
      ]),
    ],
  );
}
