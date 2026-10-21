import { useRef, useState, type ReactNode } from "react";
import type { Coverage, PlayerSummary, Publication } from "../shared/observed";
import type { PeerSettings } from "./explorer";
import {
  formatPercentile,
  metricDefinition,
  peerGroupName,
  populationSupport,
  type ObservedCard,
  type ObservedComparison,
  type ObservedRateRow,
  type PeerGroup,
} from "./observed-comparison";
import {
  CoverageDetail,
  Definitions,
  Minutes,
  Quantity,
  formatMinutes,
  formatQuantity,
  playerName,
  reasons,
  teamName,
} from "./presentation";

type Card = {
  readonly comparison: ObservedComparison;
  readonly publication: Publication;
  readonly coverage: Coverage;
};

const familyName = (population: ObservedRateRow["population"]) =>
  population === "personal" ? "personal" : "on-ice";

function referenceText(group: PeerGroup, settings: PeerSettings) {
  return `${peerGroupName(group.key)} · ${familyName(group.population)} reference · at least ${settings.peerMin} included 5v5 minutes · n = ${group.members.length}; partial n = ${group.partialCount}`;
}

function referenceLimit(group: PeerGroup) {
  return group.members.length === 0
    ? "no players meet this peer rule"
    : group.members.length === 1
      ? "one eligible player; no between-player comparison"
      : null;
}

function outsideText(
  card: ObservedCard,
  population: ObservedRateRow["population"],
  settings: PeerSettings,
) {
  if (
    !card.rows.some(
      (row) => row.population === population && row.standing.kind === "outside",
    )
  )
    return null;
  const support = populationSupport(card.player, population);
  return support.included_seconds < settings.peerMin * 60
    ? `outside reference: under ${settings.peerMin} ${familyName(population)} minutes`
    : `outside reference: no eligible ${familyName(population)} exposure`;
}

export function ObservedRateValue({
  row,
  group,
  player,
}: {
  readonly row: ObservedRateRow;
  readonly group: PeerGroup;
  readonly player: PlayerSummary;
}) {
  const definition = metricDefinition(row.metric);
  const support = populationSupport(player, row.population);
  const standing = row.standing;
  return (
    <div
      className="observed-rate-value"
      data-metric={row.metric}
      data-standing={standing.kind}
    >
      <p className="rate-primary">
        <strong>
          <Quantity
            value={row.rate}
            metrics={support}
            rate
            precision={definition.precision}
          />
        </strong>{" "}
        <span>per 60 {familyName(row.population)} min</span>
      </p>
      <p className="rate-count">
        <Quantity value={row.count} metrics={support} /> recorded
        {support.coverage_status !== "complete"
          ? ` · ${support.coverage_status} coverage`
          : ""}
      </p>
      {standing.kind === "ranked" ? (
        <>
          <p className="standing-label">
            <strong>{formatPercentile(standing.percentile)}</strong>{" "}
            observed-rate percentile
          </p>
          <div
            className="percentile-strip"
            role="img"
            aria-label={`observed-rate percentile ${formatPercentile(standing.percentile)} on a 0 to 100 scale`}
          >
            <span className="percentile-track" />
            <span
              className="percentile-marker"
              style={{ left: `${standing.percentile}%` }}
              data-percentile={standing.percentile}
            />
            <span className="percentile-ticks">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </span>
          </div>
        </>
      ) : (
        <p className="standing-unavailable">
          {standing.kind === "unavailable"
            ? "rate unavailable"
            : group.members.length === 0
              ? "no reference players"
              : "outside reference"}
        </p>
      )}
      {row.metric === "against60" && (
        <p className="rate-direction">higher = more opponent attempts</p>
      )}
    </div>
  );
}

export function ObservedSupport({
  card,
  comparison,
}: {
  readonly card: ObservedCard;
  readonly comparison: ObservedComparison;
}) {
  const { player } = card;
  return (
    <div className="observed-support">
      <div className="population-coverage">
        {(["personal", "onIce"] as const).map((population) => {
          const support = populationSupport(player, population);
          const row = card.rows.find(
            (entry) => entry.population === population,
          )!;
          const group = comparison.groups[population].find(
            (entry) => entry.key === row.groupKey,
          )!;
          const limit = referenceLimit(group);
          const outside = outsideText(card, population, comparison.settings);
          return (
            <div key={population} data-population={population}>
              <h4>{familyName(population)} support and reference</h4>
              <p>
                <Minutes seconds={support.included_seconds} /> included minutes
              </p>
              <CoverageDetail metrics={support} />
              <p className="reference-summary">
                {referenceText(group, comparison.settings)}
              </p>
              {limit && <p className="outside-reference">{limit}</p>}
              {outside && <p className="outside-reference">{outside}</p>}
              {card.rows.some(
                (entry) =>
                  entry.population === population &&
                  entry.standing.kind === "unavailable",
              ) && (
                <p className="outside-reference">
                  rate unavailable; retained counts and coverage reasons remain
                  evidence.
                </p>
              )}
            </div>
          );
        })}
      </div>
      <p className="control-note">
        {player.games_with_included_time} games with on-ice included time;{" "}
        {player.listed_games} listed games, {player.partial_games} on-ice
        partial, {player.unavailable_games} on-ice unavailable. roster listing
        is not an appearance claim; included minutes are not full official ice
        time.
      </p>
    </div>
  );
}

// measured text nodes preserve source names safely and let genuine content grow.
export function cardSvg({ comparison, publication, coverage }: Card): string {
  const card = comparison.cards[0]!;
  const player = card.player;
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg");
  svg.setAttribute("width", "1200");
  svg.setAttribute("font-family", "system-ui, sans-serif");
  svg.setAttribute("fill", "#242b2d");
  svg.setAttribute("style", "font-variant-numeric:tabular-nums");
  const element = (
    tag: string,
    attributes: Record<string, string | number>,
  ) => {
    const node = document.createElementNS(namespace, tag);
    for (const [key, value] of Object.entries(attributes))
      node.setAttribute(key, String(value));
    svg.append(node);
    return node;
  };
  const background = element("rect", { width: 1200, fill: "#fbfaf6" });
  const measurement = svg.cloneNode(false) as SVGSVGElement;
  measurement.setAttribute("width", "0");
  measurement.setAttribute("height", "0");
  measurement.setAttribute("aria-hidden", "true");
  measurement.style.position = "fixed";
  const probe = document.createElementNS(namespace, "text");
  measurement.append(probe);
  document.body.append(measurement);
  try {
    const text = (
      value: string,
      x: number,
      top: number,
      maxWidth: number,
      size = 24,
      weight = "400",
    ) => {
      probe.setAttribute("font-size", String(size));
      probe.setAttribute("font-weight", weight);
      const width = (value: string) => {
        probe.textContent = value;
        return probe.getComputedTextLength();
      };
      const lines: string[] = [];
      let line = "";
      for (const word of value.split(/\s+/)) {
        const joined = line ? `${line} ${word}` : word;
        if (width(joined) <= maxWidth) {
          line = joined;
          continue;
        }
        if (line) lines.push(line);
        line = "";
        for (const character of word) {
          if (line && width(line + character) > maxWidth) {
            lines.push(line);
            line = "";
          }
          line += character;
        }
      }
      if (line) lines.push(line);
      for (const [index, line] of lines.entries()) {
        const node = element("text", {
          x,
          y: top + size + index * size * 1.35,
          "font-size": size,
          "font-weight": weight,
        });
        node.textContent = line;
      }
      return lines.length * size * 1.35;
    };
    let y = 48;
    const paragraph = (value: string, size = 23, weight = "400") => {
      y += text(value, 64, y, 1072, size, weight) + 10;
    };
    paragraph(playerName(player), 42, "650");
    paragraph(
      `${publication.season.slice(0, 4)}–${publication.season.slice(4)} regular season · player ${player.player_id} · reported position ${player.reported_position}`,
    );
    paragraph(`season teams: ${player.teams.map(teamName).join(" / ")}`);
    y += 10;
    paragraph("recorded 5v5 results", 30, "650");
    paragraph("regular season · unadjusted observations");
    for (const population of ["personal", "onIce"] as const) {
      y += 12;
      paragraph(
        population === "personal"
          ? "personal production"
          : "team attempts while on ice",
        25,
        "650",
      );
      for (const row of card.rows.filter(
        (entry) => entry.population === population,
      )) {
        const definition = metricDefinition(row.metric);
        const group = comparison.groups[population].find(
          (entry) => entry.key === row.groupKey,
        )!;
        element("line", { x1: 64, x2: 1136, y1: y, y2: y, stroke: "#d7dad5" });
        y += 12;
        let labelHeight = text(definition.label, 64, y, 358, 25, "600");
        if (row.metric === "against60")
          labelHeight +=
            text(
              "higher = more opponent attempts",
              64,
              y + labelHeight + 3,
              358,
              20,
            ) + 3;
        const rawHeight = text(
          `${formatQuantity(row.rate, definition.precision)} per 60 ${familyName(population)} min`,
          450,
          y,
          320,
          23,
          "600",
        );
        const countHeight = text(
          `${formatQuantity(row.count)} recorded`,
          450,
          y + rawHeight + 2,
          320,
          21,
        );
        let standingHeight: number;
        if (row.standing.kind === "ranked") {
          standingHeight = text(
            `${formatPercentile(row.standing.percentile)} observed-rate percentile`,
            808,
            y,
            328,
            21,
          );
          const lineY = y + standingHeight + 16;
          element("line", {
            x1: 816,
            x2: 1128,
            y1: lineY,
            y2: lineY,
            stroke: "#677575",
            "stroke-width": 2,
          });
          element("circle", {
            cx: 816 + (312 * row.standing.percentile) / 100,
            cy: lineY,
            r: 5,
            fill: "#242b2d",
          });
          for (const [offset, label] of [
            [0, "0"],
            [156, "50"],
            [312, "100"],
          ] as const) {
            const node = element("text", {
              x: 816 + offset,
              y: lineY + 26,
              "font-size": 18,
              "text-anchor":
                offset === 0 ? "start" : offset === 312 ? "end" : "middle",
            });
            node.textContent = label;
          }
          standingHeight += 50;
        } else {
          standingHeight = text(
            row.standing.kind === "unavailable"
              ? "rate unavailable"
              : group.members.length === 0
                ? "no reference players"
                : "outside reference",
            808,
            y,
            328,
            21,
          );
        }
        y +=
          Math.max(labelHeight, rawHeight + countHeight + 2, standingHeight) +
          14;
      }
    }
    y += 12;
    for (const population of ["personal", "onIce"] as const) {
      const support = populationSupport(player, population);
      const row = card.rows.find((entry) => entry.population === population)!;
      const group = comparison.groups[population].find(
        (entry) => entry.key === row.groupKey,
      )!;
      paragraph(`${familyName(population)} support and reference`, 24, "650");
      paragraph(
        `${formatMinutes(support.included_seconds)} included min · ${formatMinutes(support.known_excluded_seconds)} known min excluded · coverage: ${support.coverage_status === "complete" ? "covered" : support.coverage_status}`,
        21,
      );
      paragraph(referenceText(group, comparison.settings), 21);
      const limit = referenceLimit(group);
      if (limit) paragraph(limit, 21);
      const outside = outsideText(card, population, comparison.settings);
      if (outside) paragraph(outside, 21);
      const noExposureReason =
        population === "personal"
          ? "no_personal_5v5_exposure"
          : "no_5v5_exposure";
      if (support.reason_codes.some((code) => code === noExposureReason))
        paragraph(reasons[noExposureReason], 21);
    }
    y += 10;
    paragraph(
      "higher percentile = higher recorded rate; against: higher = more opponent attempts.",
      22,
      "600",
    );
    paragraph(
      "observed-rate percentile counts lower rates plus half of exact ties, using unrounded published rates. descriptive spread, not ability, uncertainty or reliability; shared play relates these observations.",
      21,
    );
    paragraph(
      "each rate uses its own population’s included 5v5 time. membership uses exact seconds; displayed minutes are rounded. covered means no known relevant gap in listed evidence; included results are not certified complete-season totals. known excluded time is not all missing time.",
      21,
    );
    if (coverage.games_with_unassigned_player_associations > 0)
      paragraph(
        `global gap: player associations unresolved in ${coverage.games_with_unassigned_player_associations} inventory games; any player may have omitted games.`,
        21,
      );
    paragraph(`publication time: ${publication.generated_at}`, 20);
    paragraph(`publication id: ${publication.publication_id}`, 20);
    if (publication.purpose === "fixture")
      paragraph("fixture publication · development evidence", 22, "650");
    const height = Math.ceil(y + 38);
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
  comparison,
  publication,
  coverage,
  controls,
}: Card & { readonly controls?: ReactNode }) {
  const [state, setState] = useState<"idle" | "rendering" | "saved" | "failed">(
    "idle",
  );
  const rendering = useRef(false);
  const card = comparison.cards[0]!;
  return (
    <section className="observed-card" aria-labelledby="included-heading">
      <h3 id="included-heading">recorded 5v5 results</h3>
      <p className="control-note">regular season · unadjusted observations</p>
      {controls}
      {(["personal", "onIce"] as const).map((population) => (
        <div className="observed-rate-group" key={population}>
          <h4>
            {population === "personal"
              ? "personal production"
              : "team attempts while on ice"}
          </h4>
          <dl className="observed-overview">
            {card.rows
              .filter((row) => row.population === population)
              .map((row) => (
                <div key={row.metric}>
                  <dt>{metricDefinition(row.metric).label}</dt>
                  <dd>
                    <ObservedRateValue
                      row={row}
                      group={
                        comparison.groups[population].find(
                          (group) => group.key === row.groupKey,
                        )!
                      }
                      player={card.player}
                    />
                  </dd>
                </div>
              ))}
          </dl>
        </div>
      ))}
      <ObservedSupport card={card} comparison={comparison} />
      <p className="control-note">
        higher percentile = higher recorded rate, including against. percentiles
        count lower rates plus half of exact ties; they describe observations,
        not ability or uncertainty. the minimum is a viewing rule.
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
              const snapshot = { comparison, publication, coverage };
              const blob = await cardPng(snapshot);
              const url = URL.createObjectURL(blob);
              try {
                const link = document.createElement("a");
                link.href = url;
                link.download = `hockey-stats-${snapshot.publication.season}-${snapshot.comparison.cards[0]!.player.player_id}-5v5.png`;
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
                : "one player; five rates, observed percentiles and declared references."}
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
