import { useId } from "react";
import type {
  PlayerSpatialCell,
  PlayerSummary,
  SpatialSelection,
} from "../shared/observed";
import type { MapMode } from "./explorer";
import {
  CoverageDetail,
  Minutes,
  Quantity,
  playerName,
  reasons,
} from "./presentation";

// keep nonzero tail values and their signs visible, including after rounding.
function spatialNumber(value: number | null): string {
  if (value === null) return "—";
  if (value === 0) return "0";
  if (Math.abs(value) < 0.001) return value.toExponential(2);
  return value.toLocaleString("en", { maximumSignificantDigits: 4 });
}

function Rink({
  geometry,
  cells,
  direction,
  mode,
  extent,
  label,
}: {
  readonly geometry: SpatialSelection["cells"];
  readonly cells: readonly PlayerSpatialCell[];
  readonly direction: "for" | "against";
  readonly mode: MapMode;
  readonly extent: number;
  readonly label: string;
}) {
  const id = useId();
  return (
    <svg
      className="spatial-rink"
      viewBox="-1 -1 87 202"
      role="img"
      aria-labelledby={`${id}-title`}
      aria-describedby={`${id}-description`}
    >
      <title id={`${id}-title`}>{label}</title>
      <desc id={`${id}-description`}>
        full rink; positive x points up, positive y points right. the shooting
        team attacks the top goal in both directions. colors use the shared
        legend; recorded counts and every displayed value follow in the
        numerical table.
      </desc>
      <defs>
        <clipPath id={`${id}-clip`}>
          <rect x="0" y="0" width="85" height="200" rx="28" />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id}-clip)`}>
        {cells.map((cell, index) => {
          const bounds = geometry[index]!;
          const value =
            cell[
              `${direction}_${mode === "absolute" ? "density" : "difference"}`
            ];
          const amount = (100 * Math.abs(value)) / extent;
          const endpoint =
            mode === "absolute" ? "#084594" : value < 0 ? "#2166ac" : "#b2182b";
          return (
            <rect
              key={cell.cell_id}
              x={bounds.y_min + 42.5}
              y={100 - bounds.x_max}
              width={bounds.y_max - bounds.y_min}
              height={bounds.x_max - bounds.x_min}
              fill={`color-mix(in oklab, ${endpoint} ${amount}%, #f7f7f2)`}
            />
          );
        })}
        <g className="spatial-landmarks" fill="none">
          <path d="M0 75H85M0 125H85M0 100H85" />
          <circle cx="42.5" cy="100" r="15" />
          <path d="M39.5 11H45.5M39.5 189H45.5" />
        </g>
      </g>
      <rect
        className="spatial-outline"
        x="0"
        y="0"
        width="85"
        height="200"
        rx="28"
        fill="none"
      />
    </svg>
  );
}

export default function SpatialViews({
  spatial,
  players,
  season,
  mode,
  onModeChange,
}: {
  readonly spatial: SpatialSelection | null;
  readonly players: readonly PlayerSummary[];
  readonly season: string;
  readonly mode: MapMode;
  readonly onModeChange: (mode: MapMode) => void;
}) {
  const id = useId();
  const selected = players.map((player) => ({
    player,
    data:
      spatial?.players.find((row) => row.player_id === player.player_id)
        ?.data ?? null,
  }));
  let maximum = 0;
  let available = false;
  for (const { data } of selected) {
    if (!data?.cells) continue;
    available = true;
    for (const cell of data.cells)
      for (const direction of ["for", "against"] as const)
        maximum = Math.max(
          maximum,
          Math.abs(
            cell[
              `${direction}_${mode === "absolute" ? "density" : "difference"}`
            ],
          ),
        );
  }
  const extent = maximum || 1;
  const support = spatial?.league_support;
  return (
    <section className="spatial-views" aria-labelledby={`${id}-heading`}>
      <h3 id={`${id}-heading`}>where unblocked attempts occurred</h3>
      <p>
        recorded {season.slice(0, 4)}–{season.slice(6)} regular-season 5v5 ·
        unadjusted on-ice results
      </p>
      <p className="spatial-introduction">
        scored, saved and missed attempts at their recorded locations; blocks
        are excluded. these team patterns include deployment effects and do not
        isolate the player.
      </p>
      <fieldset className="spatial-mode">
        <legend>map display</legend>
        <label>
          <input
            type="radio"
            name={`${id}-mode`}
            value="difference"
            checked={mode === "difference"}
            onChange={() => onModeChange("difference")}
          />{" "}
          difference from included league average
        </label>
        <label>
          <input
            type="radio"
            name={`${id}-mode`}
            value="absolute"
            checked={mode === "absolute"}
            onChange={() => onModeChange("absolute")}
          />{" "}
          absolute rate
        </label>
      </fieldset>
      {support && (
        <aside
          className="spatial-reference"
          aria-label="included league reference"
        >
          <h4>included league reference</h4>
          <p>
            <Minutes seconds={2 * support.included_seconds} /> team-direction
            minutes ({<Minutes seconds={support.included_seconds} />} physical
            minutes × two team-directions); {support.games_with_included_time}{" "}
            supported games / {support.inventory_games} inventory games;{" "}
            {support.partial_games} partial, {support.unavailable_games}{" "}
            unavailable.
          </p>
          <p>
            <Quantity value={support.unblocked_attempts} metrics={support} />{" "}
            recorded unblocked attempts;{" "}
            {spatialNumber(support.unblocked_per60)} attempts per 60
            team-direction minutes.
          </p>
          <p>coverage exclusions below use physical minutes.</p>
          <CoverageDetail metrics={support} />
          {support.reason_game_counts.length > 0 && (
            <details className="spatial-reference-reasons">
              <summary>league exclusion reasons by game</summary>
              <ul>
                {support.reason_game_counts.map(({ code, games }) => (
                  <li key={code}>
                    {reasons[code]}: {games} {games === 1 ? "game" : "games"}
                  </li>
                ))}
              </ul>
            </details>
          )}
          <p>
            both directions use this reference, including the selected players;
            peer controls do not change it. coverage can be selective.
          </p>
        </aside>
      )}
      <p className="spatial-method">
        five-foot bins; fixed gaussian smoothing, 10-foot standard deviation.
        both modes show descriptive smoothed density, not statistical precision.
        map units: unblocked attempts per 60 minutes per 100 square feet; panel
        totals: attempts per 60 spatial minutes.
      </p>
      {available && (
        <div className="spatial-legend" role="group" aria-label="shared map legend">
          <p>
            {mode === "difference"
              ? "difference from included league average"
              : "absolute rate"}{" "}
            · one scale for all available panels
          </p>
          <div className={`spatial-color-bar ${mode}`} aria-hidden="true" />
          <div className="spatial-legend-labels">
            <span>
              {spatialNumber(mode === "difference" ? -extent : 0)}
              <span>{mode === "difference" ? "fewer" : "zero"}</span>
            </span>
            {mode === "difference" && (
              <span>
                0<span>same</span>
              </span>
            )}
            <span>
              {spatialNumber(extent)}
              <span>more</span>
            </span>
          </div>
          {maximum === 0 && (
            <p>
              all displayed values are zero; the legend uses a fixed extent of
              1.
            </p>
          )}
          <p>
            the scale changes with the selected players and mode; compare colors
            across pages using their legends.
            {mode === "difference" &&
              " red means more attempts, not universally better or worse."}
          </p>
        </div>
      )}
      <p className="spatial-orientation">
        full rink: +x toward the top goal, +y toward the right. the shooting
        team attacks the top goal, including opponents in the against panel.
      </p>
      <div className="spatial-player-grid">
        {selected.map(({ player, data }) => (
          <section
            className="spatial-player"
            key={player.player_id}
            aria-label={`${playerName(player)} spatial evidence`}
          >
            <h4>{playerName(player)}</h4>
            {data ? (
              <>
                <p>
                  <Minutes seconds={data.metrics.included_seconds} /> included
                  spatial minutes. spatial minutes may differ from on-ice and
                  personal minutes.
                </p>
                <CoverageDetail metrics={data.metrics} />
                <div className="spatial-panels">
                  {(["for", "against"] as const).map((direction) => (
                    <figure className="spatial-panel" key={direction}>
                      <h5>
                        {direction === "for"
                          ? "for — the player's team"
                          : "against — opponents"}
                      </h5>
                      <p>
                        <Quantity
                          value={
                            data.metrics[
                              direction === "for"
                                ? "unblocked_for"
                                : "unblocked_against"
                            ]
                          }
                          metrics={data.metrics}
                        />{" "}
                        recorded unblocked attempts ·{" "}
                        {spatialNumber(data.metrics[`${direction}_per60`])}{" "}
                        attempts/60
                      </p>
                      {data.cells && spatial ? (
                        <>
                          <span className="spatial-goal-label">
                            attacking goal · +x
                          </span>
                          <Rink
                            geometry={spatial.cells}
                            cells={data.cells}
                            direction={direction}
                            mode={mode}
                            extent={extent}
                            label={`${playerName(player)}; ${direction}; ${mode === "difference" ? "difference from included league average" : "absolute rate"}`}
                          />
                          <figcaption>
                            left: −y · right: +y · bottom: −x
                          </figcaption>
                        </>
                      ) : (
                        <p className="spatial-unavailable">
                          {data.metrics.coverage_status === "unavailable"
                            ? "map unavailable"
                            : "no spatial 5v5 exposure; no rate map"}
                          .{" "}
                          {data.metrics.reason_codes
                            .map((code) => reasons[code])
                            .join("; ")}
                        </p>
                      )}
                    </figure>
                  ))}
                </div>
                {data.cells && spatial && (
                  <details className="spatial-values">
                    <summary>
                      numerical spatial evidence — {playerName(player)}
                    </summary>
                    <div
                      className="table-scroll"
                      tabIndex={0}
                      role="region"
                      aria-label={`${playerName(player)} numerical spatial evidence table; scroll horizontally for all columns`}
                    >
                      <table className="spatial-table">
                        <caption>
                          recorded counts and raw bin rates are unsmoothed.
                          displayed densities and signed differences use fixed
                          pooling; density units are attempts/60/100 square
                          feet. raw bin rates use attempts/60. all cells,
                          including zeros, are shown; bounds are rectangular bin
                          limits; area is clipped to the rink. values are
                          rounded for display; scientific notation preserves
                          small nonzero signs.
                        </caption>
                        <thead>
                          <tr>
                            <th scope="col">cell id</th>
                            <th scope="col">x bounds (ft)</th>
                            <th scope="col">y bounds (ft)</th>
                            <th scope="col">area (sq ft)</th>
                            <th scope="col">recorded for</th>
                            <th scope="col">recorded against</th>
                            <th scope="col">raw bin for/60</th>
                            <th scope="col">raw bin against/60</th>
                            <th scope="col">displayed for density</th>
                            <th scope="col">displayed against density</th>
                            <th scope="col">league density</th>
                            <th scope="col">for difference</th>
                            <th scope="col">against difference</th>
                          </tr>
                        </thead>
                        <tbody>
                          {data.cells.map((cell, index) => {
                            const geometry = spatial.cells[index]!;
                            return (
                              <tr key={cell.cell_id}>
                                <th scope="row">{cell.cell_id}</th>
                                <td>
                                  {geometry.x_min} to {geometry.x_max}
                                </td>
                                <td>
                                  {geometry.y_min} to {geometry.y_max}
                                </td>
                                <td className="numeric">
                                  {spatialNumber(geometry.area_sqft)}
                                </td>
                                {[
                                  cell.for_count,
                                  cell.against_count,
                                  cell.for_raw_per60,
                                  cell.against_raw_per60,
                                  cell.for_density,
                                  cell.against_density,
                                  geometry.league_density,
                                  cell.for_difference,
                                  cell.against_difference,
                                ].map((value, i) => (
                                  <td className="numeric" key={i}>
                                    {i < 2
                                      ? String(value)
                                      : spatialNumber(value)}
                                  </td>
                                ))}
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </details>
                )}
              </>
            ) : (
              <p className="spatial-unavailable">
                no spatial evidence for this player in this response.
              </p>
            )}
          </section>
        ))}
      </div>
      <details className="quantity-definitions">
        <summary>spatial population and display limits</summary>
        <p>
          locations are source-credited event locations, not verified physical
          releases. own or awarded goals retain their source-credit meaning.
          long attempts from negative x and lateral signs are retained.
        </p>
        <p>
          spatial counts and time come from their own matched population. a
          missing coordinate, unresolved attacking frame or outside-rink
          location removes the whole assigned segment's counts and time for both
          teams. valid attempts in that segment are excluded too. zero-event
          segments remain; personal-credit exclusions do not control spatial
          support.
        </p>
        <p>
          positive time with zero attempts is real zero absolute density; its
          league difference can be negative. zero time has no rate map, even
          with no known gaps. unavailable evidence is never shown as
          league-average white.
        </p>
        <p>
          counts and time reduce from the listed-game evidence. each player has
          their own included games and spatial minutes; a comparison is not
          restricted to common games. missingness can be selective: these are
          included subtotals, not complete-season or missing-at-random
          estimates. known excluded minutes do not measure all missing time.
          global unassigned-game limitations shown above apply here too.
        </p>
        <p>
          five-foot recorded bins are pooled using one fixed area-weighted
          gaussian rule. smoothed mass is not a recorded count; no browser
          smoothing, adjustable bandwidth, significance or ability estimate is
          implied. maps stay in the browser; the player png retains its existing
          facts.
        </p>
      </details>
    </section>
  );
}
