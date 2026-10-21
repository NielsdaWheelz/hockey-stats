import { useRef, useState } from "react";
import type { Coverage, PlayerSummary, Publication } from "../shared/observed";
import {
  CoverageDetail,
  Definitions,
  Minutes,
  Quantity,
  formatMinutes,
  formatQuantity,
  playerName,
  quantityDefinitions,
  reasons,
  teamName,
} from "./presentation";

type Card = {
  readonly player: PlayerSummary;
  readonly publication: Publication;
  readonly coverage: Coverage;
};

// text nodes keep source names and reasons out of svg markup. measure with the
// same system font used by the image; long tokens wrap rather than shrink.
export function cardSvg({ player, publication, coverage }: Card): string {
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg");
  svg.setAttribute("width", "1200");
  svg.setAttribute("font-family", "system-ui, sans-serif");
  svg.setAttribute("fill", "#242b2d");
  svg.setAttribute("style", "font-variant-numeric:tabular-nums");
  const background = document.createElementNS(namespace, "rect");
  background.setAttribute("width", "1200");
  background.setAttribute("fill", "#fbfaf6");
  svg.append(background);
  const measurement = svg.cloneNode(false) as SVGSVGElement;
  measurement.setAttribute("width", "0");
  measurement.setAttribute("height", "0");
  measurement.setAttribute("aria-hidden", "true");
  measurement.style.position = "fixed";
  const probe = document.createElementNS(namespace, "text");
  measurement.append(probe);
  document.body.append(measurement);
  try {
    const width = (value: string) => {
      probe.textContent = value;
      return probe.getComputedTextLength();
    };
    let y = 64;
    const text = (value: string, size = 26, weight = "400") => {
      probe.setAttribute("font-size", String(size));
      probe.setAttribute("font-weight", weight);
      const lines: string[] = [];
      let line = "";
      for (const word of value.split(/\s+/)) {
        const joined = line ? `${line} ${word}` : word;
        if (width(joined) <= 1072) {
          line = joined;
          continue;
        }
        if (line) lines.push(line);
        line = "";
        for (const character of word) {
          if (line && width(line + character) > 1072) {
            lines.push(line);
            line = "";
          }
          line += character;
        }
      }
      if (line) lines.push(line);
      for (const line of lines) {
        const node = document.createElementNS(namespace, "text");
        node.setAttribute("x", "64");
        node.setAttribute("y", String(y + size));
        node.setAttribute("font-size", String(size));
        node.setAttribute("font-weight", weight);
        node.textContent = line;
        svg.append(node);
        y += Math.ceil(size * 1.45);
      }
      y += 12;
    };
    const section = (label: string) => {
      y += 20;
      text(label, 34, "650");
    };
    const season = `${publication.season.slice(0, 4)}–${publication.season.slice(4)}`;
    text("recorded 5v5 results", 28, "650");
    text(playerName(player), 48, "650");
    text(
      `${season} regular season · player ${player.player_id} · reported position ${player.reported_position}`,
    );
    text(`season teams: ${player.teams.map(teamName).join(" / ")}`);
    section("personal production");
    const personal = player.personal;
    text(
      `shots on goal: ${formatQuantity(personal.shots_on_goal)} · per 60: ${formatQuantity(personal.shots_on_goal_per60, 2)}`,
    );
    text(
      `goals: ${formatQuantity(personal.goals)} · per 60: ${formatQuantity(personal.goals_per60, 2)}`,
    );
    text(
      `primary assists: ${formatQuantity(personal.primary_assists)} · per 60: ${formatQuantity(personal.primary_assists_per60, 2)}`,
    );
    text(
      `personal included minutes: ${formatMinutes(personal.included_seconds)}`,
    );
    text(
      `personal coverage: ${personal.coverage_status === "complete" ? "covered" : personal.coverage_status}; known excluded minutes: ${formatMinutes(personal.known_excluded_seconds)}`,
    );
    for (const code of personal.reason_codes) text(reasons[code]);
    section("team attempts while on ice");
    const metrics = player.metrics;
    text(
      `attempts for: ${formatQuantity(metrics.attempts_for)} · per 60: ${formatQuantity(metrics.for_per60, 1)}`,
    );
    text(
      `attempts against: ${formatQuantity(metrics.attempts_against)} · per 60: ${formatQuantity(metrics.against_per60, 1)}`,
    );
    text(`on-ice included minutes: ${formatMinutes(metrics.included_seconds)}`);
    text(
      `on-ice coverage: ${metrics.coverage_status === "complete" ? "covered" : metrics.coverage_status}; known excluded minutes: ${formatMinutes(metrics.known_excluded_seconds)}`,
    );
    for (const code of metrics.reason_codes) text(reasons[code]);
    text(
      `${player.games_with_included_time} games with on-ice included time; ${player.listed_games} listed games; ${player.partial_games} on-ice partial; ${player.unavailable_games} on-ice unavailable.`,
    );
    if (coverage.games_with_unassigned_player_associations > 0)
      text(
        `player associations are unresolved in ${coverage.games_with_unassigned_player_associations} inventory games; included results may omit games for any player.`,
      );
    section("definitions and evidence");
    text("included results; unadjusted observations, not ability", 28, "650");
    for (const definition of quantityDefinitions) text(definition);
    text(
      "— means unavailable or an undefined rate; the population’s coverage reasons explain why.",
    );
    text(
      `published: ${publication.generated_at} (publication time, not a source observation time)`,
    );
    text(`publication id: ${publication.publication_id}`);
    text(`on-ice definition: ${publication.population_version}`);
    text(`personal definition: ${publication.personal_population_version}`);
    if (publication.purpose === "fixture")
      text("fixture publication · development evidence");
    const height = y + 52;
    svg.setAttribute("height", String(height));
    svg.setAttribute("viewBox", `0 0 1200 ${height}`);
    background.setAttribute("height", String(height));
    return new XMLSerializer().serializeToString(svg);
  } finally {
    measurement.remove();
  }
}

export async function cardPng(card: Card): Promise<Blob> {
  const svg = cardSvg(card);
  const source = URL.createObjectURL(
    new Blob([svg], { type: "image/svg+xml;charset=utf-8" }),
  );
  try {
    const image = new Image();
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () =>
        reject(new Error("the card image could not be rendered"));
      image.src = source;
    });
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("image rendering is unavailable");
    context.drawImage(image, 0, 0);
    return await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(
        (blob) =>
          blob
            ? resolve(blob)
            : reject(new Error("the png could not be created")),
        "image/png",
      ),
    );
  } finally {
    URL.revokeObjectURL(source);
  }
}

export default function DescriptiveCard({
  player,
  publication,
  coverage,
}: Card) {
  const [state, setState] = useState<"idle" | "rendering" | "saved" | "failed">(
    "idle",
  );
  const rendering = useRef(false);
  const personal = player.personal;
  const metrics = player.metrics;
  return (
    <section className="observed-card" aria-labelledby="included-heading">
      <h3 id="included-heading">recorded 5v5 results</h3>
      <p className="control-note">
        included results; unadjusted observations, not ability
      </p>
      <h4>personal production</h4>
      <div
        className="table-scroll"
        tabIndex={0}
        aria-label="personal production table, scroll horizontally for all columns"
      >
        <table className="personal-table">
          <thead>
            <tr>
              <th scope="col">quantity</th>
              <th scope="col" className="numeric">
                count
              </th>
              <th scope="col" className="numeric">
                per 60 personal minutes
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">shots on goal</th>
              <td className="numeric">
                <Quantity value={personal.shots_on_goal} metrics={personal} />
              </td>
              <td className="numeric">
                <Quantity
                  value={personal.shots_on_goal_per60}
                  metrics={personal}
                  rate
                  precision={2}
                />
              </td>
            </tr>
            <tr>
              <th scope="row">goals</th>
              <td className="numeric">
                <Quantity value={personal.goals} metrics={personal} />
              </td>
              <td className="numeric">
                <Quantity
                  value={personal.goals_per60}
                  metrics={personal}
                  rate
                  precision={2}
                />
              </td>
            </tr>
            <tr>
              <th scope="row">primary assists</th>
              <td className="numeric">
                <Quantity value={personal.primary_assists} metrics={personal} />
              </td>
              <td className="numeric">
                <Quantity
                  value={personal.primary_assists_per60}
                  metrics={personal}
                  rate
                  precision={2}
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <h4>team attempts while on ice</h4>
      <dl className="observed-rates">
        <div>
          <dt>on-ice attempts for/60</dt>
          <dd>
            <Quantity value={metrics.for_per60} metrics={metrics} rate />
          </dd>
        </div>
        <div>
          <dt>on-ice attempts against/60</dt>
          <dd>
            <Quantity value={metrics.against_per60} metrics={metrics} rate />
          </dd>
        </div>
      </dl>
      <dl className="observed-facts">
        <div>
          <dt>on-ice attempts for</dt>
          <dd>
            <Quantity value={metrics.attempts_for} metrics={metrics} />
          </dd>
        </div>
        <div>
          <dt>on-ice attempts against</dt>
          <dd>
            <Quantity value={metrics.attempts_against} metrics={metrics} />
          </dd>
        </div>
        <div>
          <dt>games with on-ice included time</dt>
          <dd>{player.games_with_included_time}</dd>
        </div>
      </dl>
      <div className="population-coverage">
        <div>
          <h4>personal support</h4>
          <p>
            <Minutes seconds={personal.included_seconds} /> included minutes
          </p>
          <CoverageDetail metrics={personal} />
        </div>
        <div>
          <h4>on-ice support</h4>
          <p>
            <Minutes seconds={metrics.included_seconds} /> included minutes
          </p>
          <CoverageDetail metrics={metrics} />
        </div>
      </div>
      <p className="control-note">
        {player.listed_games} listed games; {player.partial_games} on-ice
        partial and {player.unavailable_games} on-ice unavailable. roster
        listing is not an appearance claim; included minutes are not full
        official ice time.
      </p>
      <Definitions />
      <div className="card-actions">
        <button
          type="button"
          disabled={state === "rendering"}
          onClick={async () => {
            if (rendering.current) return;
            rendering.current = true;
            setState("rendering");
            try {
              const snapshot = structuredClone({
                player,
                publication,
                coverage,
              });
              const blob = await cardPng(snapshot);
              const url = URL.createObjectURL(blob);
              try {
                const link = document.createElement("a");
                link.href = url;
                link.download = `hockey-stats-${snapshot.publication.season}-${snapshot.player.player_id}-5v5.png`;
                document.body.append(link);
                try {
                  link.click();
                } finally {
                  link.remove();
                }
              } finally {
                window.setTimeout(() => URL.revokeObjectURL(url), 1000);
              }
              setState("saved");
            } catch {
              setState("failed");
            } finally {
              rendering.current = false;
            }
          }}
        >
          {state === "rendering" ? "rendering png…" : "download player png"}
        </button>
        <p role="status" aria-live="polite">
          {state === "rendering"
            ? "preparing this player’s recorded results…"
            : state === "saved"
              ? "png download prepared."
              : state === "failed"
                ? "png could not be created. try downloading again."
                : "one player; season results and coverage, without peer plots."}
        </p>
      </div>
      <a
        href="#games-heading"
        onClick={(event) => {
          event.preventDefault();
          const heading = document.getElementById("games-heading");
          heading?.focus();
          heading?.scrollIntoView();
        }}
      >
        view game evidence
      </a>
    </section>
  );
}
