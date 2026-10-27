import { useId, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router";
import type { AnalysisMetricId } from "./analysis-values";
import {
  descriptiveCsv,
  descriptiveFields,
  type DescriptiveCardModel,
} from "./descriptive-values";
import { downloadBlob, svgPng } from "./export";
import { teamName, seasonLabel } from "./presentation";

type DescriptiveScales = {
  readonly usage: number;
  readonly strengthMinutes: number;
  readonly ev: number;
  readonly pp: number;
  readonly attempts: number;
  readonly goals: number;
  readonly conversion: number;
  readonly penalties: number;
};
const maximum = (
  values: readonly (number | null | undefined)[],
  fallback = 1,
): number =>
  Math.max(
    fallback,
    ...values.filter(
      (value): value is number =>
        value !== null && value !== undefined && Number.isFinite(value),
    ),
  );
export function descriptiveScales(
  models: readonly DescriptiveCardModel[],
): DescriptiveScales {
  const bodies = models.flatMap((model) =>
    model.descriptive.availability === "provided"
      ? [model.descriptive.data]
      : [],
  );
  const extent = (
    values: readonly (number | null | undefined)[],
    fallback = 1,
  ) => maximum(values, fallback) * 1.08;
  return {
    usage: extent(
      models.flatMap((model) => [
        model.descriptive.data?.reported_usage.minutes_per_appearance.value,
        ...model.guides
          .filter((row) => row.datum.metric.id.includes(".usage."))
          .flatMap((row) => [row.guide.q25, row.guide.q50, row.guide.q75]),
      ]),
    ),
    strengthMinutes: extent(
      bodies.map((body) =>
        ["ev", "pp", "pk", "other"].reduce(
          (sum, key) =>
            sum + (body.strength_usage[key as "ev"].seconds ?? 0) / 60,
          0,
        ),
      ),
    ),
    ev: extent(
      models.flatMap((model) => [
        model.descriptive.data?.scoring_by_strength.ev.primary_points_per60
          .value,
        ...model.guides
          .filter((row) => row.datum.metric.id.includes(".ev."))
          .flatMap((row) => [row.guide.q25, row.guide.q50, row.guide.q75]),
      ]),
    ),
    pp: extent(
      models.flatMap((model) => [
        model.descriptive.data?.scoring_by_strength.pp.primary_points_per60
          .value,
        ...model.guides
          .filter((row) => row.datum.metric.id.includes(".pp."))
          .flatMap((row) => [row.guide.q25, row.guide.q50, row.guide.q75]),
      ]),
    ),
    attempts: extent(
      bodies.flatMap((body) =>
        Object.values(body.on_off_attempts).flatMap((group) => [
          group.for_per60.value,
          group.against_per60.value,
        ]),
      ),
    ),
    goals: extent(
      bodies.flatMap((body) =>
        Object.values(body.on_off_goals).flatMap((group) => [
          group.for_per60.value,
          group.against_per60.value,
        ]),
      ),
    ),
    conversion: extent(
      bodies.flatMap((body) =>
        Object.values(body.on_ice_conversion).flatMap((group) => [
          group.shooting_for.value,
          group.shooting_against.value,
        ]),
      ),
      0.01,
    ),
    penalties: extent(
      bodies.flatMap((body) =>
        Object.values(body.recorded_penalties).flatMap((group) => [
          group.drawn.per1000minutes.value,
          group.taken.per1000minutes.value,
        ]),
      ),
    ),
  };
}
const numberText = (value: number | null | undefined, digits = 2): string =>
  value === null || value === undefined
    ? "unavailable"
    : value.toLocaleString("en", {
        maximumFractionDigits: digits,
        useGrouping: false,
      });
const xml = (value: unknown): string =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
const words = (value: string, max: number): string[] => {
  const lines: string[] = [];
  let line = "";
  for (const word of value.split(/\s+/)) {
    if (line && `${line} ${word}`.length > max) {
      lines.push(line);
      line = "";
    }
    if (word.length > max) {
      if (line) {
        lines.push(line);
        line = "";
      }
      for (let index = 0; index < word.length; index += max)
        lines.push(word.slice(index, index + max));
    } else line = line ? `${line} ${word}` : word;
  }
  if (line) lines.push(line);
  return lines;
};
const supportMark = (
  support: import("../shared/player-analysis").Support | undefined,
): string =>
  !support
    ? "support unavailable"
    : support.unquantified_gap ||
        support.reason_counts.length ||
        (support.known_excluded_seconds ?? 0) > 0
      ? "partial support"
      : "supported window";

// this composition is both the inline sheet and the png source. full audit detail
// stays alongside it; published values never depend on plot coordinates.
function cardSvg(
  model: DescriptiveCardModel,
  scales = descriptiveScales([model]),
): string {
  const pieces: string[] = [];
  const node = (
    tag: string,
    attributes: Record<string, string | number>,
    content = "",
  ) =>
    pieces.push(
      `<${tag} ${Object.entries(attributes)
        .map(([key, value]) => `${key}="${xml(value)}"`)
        .join(" ")}>${content}</${tag}>`,
    );
  const text = (
    value: string,
    x: number,
    y: number,
    size = 20,
    extra: Record<string, string | number> = {},
  ) => node("text", { x, y, "font-size": size, ...extra }, xml(value));
  const wrap = (
    value: string,
    x: number,
    y: number,
    width: number,
    size = 20,
    extra: Record<string, string | number> = {},
  ) => {
    const lines = words(value, Math.max(1, Math.floor(width / (size * 0.61))));
    lines.forEach((line, index) =>
      text(line, x, y + index * size * 1.25, size, extra),
    );
    return lines.length * size * 1.25;
  };
  const line = (
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    stroke = "#c5ceca",
    extra: Record<string, string | number> = {},
  ) => node("line", { x1, y1, x2, y2, stroke, ...extra });
  const rect = (
    x: number,
    y: number,
    width: number,
    height: number,
    fill: string,
  ) => node("rect", { x, y, width: Math.max(0, width), height, fill });
  const missing = (value: string, x: number, y: number, width: number) =>
    wrap(value, x, y, width, 20, { fill: "#536667" });
  const panel = (
    label: string,
    x: number,
    y: number,
    width: number,
    key: string,
  ) => {
    line(x, y - 15, x + width, y - 15);
    text(label, x, y + 12, 24, { "font-weight": 650 });
    text(key, x + width, y + 12, 20, { "text-anchor": "end", fill: "#536667" });
  };
  const dot = (scope: string, x: number, y: number, color: string) => {
    if (scope === "off" || scope === "opponents")
      node("rect", {
        x: x - 10,
        y: y - 10,
        width: 20,
        height: 20,
        fill: "none",
        stroke: color,
        "stroke-width": 3,
      });
    else if (scope === "league")
      node("path", {
        d: `M ${x} ${y - 9} L ${x + 9} ${y + 8} L ${x - 9} ${y + 8} Z`,
        fill: color,
      });
    else node("circle", { cx: x, cy: y, r: 8, fill: color });
  };
  const d = model.descriptive.data,
    c = model.context.data;
  const familyReason =
    model.descriptive.availability === "provided"
      ? null
      : model.descriptive.availability;
  const name =
    model.person?.display_name ??
    (model.person
      ? `player ${model.playerId}`
      : `player ${model.playerId} · absent season`);
  const nameLines = words(name, 50);
  const extraHeader = Math.max(0, nameLines.length - 2) * 50;
  nameLines.forEach((value, index) =>
    text(value, 44, 64 + index * 50, 40, { "font-weight": 700 }),
  );
  const idY = 80 + nameLines.length * 50;
  text(
    `${seasonLabel(model.season.season)} regular season · position ${model.person?.reported_position ?? "unavailable"} · player ${model.playerId}`,
    44,
    idY,
    22,
  );
  const teams = model.person?.teams.map(teamName).join(" / ") || "unavailable";
  const teamLines = words(`season teams: ${teams}`, 93);
  const extraTeams = Math.max(0, teamLines.length - 1) * 25;
  teamLines.forEach((value, index) =>
    text(value, 44, idY + 30 + index * 25, 20),
  );
  text(
    `age ${numberText(model.person?.age_years, 1)} as of ${model.person?.age_as_of ?? "unavailable"} · ${typeof model.person?.height_cm === "number" ? `height ${numberText(model.person.height_cm, 1)} cm` : "height unavailable"}`,
    44,
    idY + 60 + extraTeams,
    20,
  );
  text(
    "unadjusted recorded results · separate populations and denominators",
    44,
    idY + 90 + extraTeams,
    22,
    { "font-weight": 600 },
  );
  // header expansions reflow all panel blocks rather than clipping identity.
  const shift = extraHeader + extraTeams;
  const Y = (y: number) =>
    y + shift * (1 - Math.max(0, Math.min(1, (y - 650) / 1510)));
  const guide = (
    index: number,
    x: number,
    y: number,
    width: number,
    extent: number,
  ) => {
    const row = model.guides[index];
    text(`empirical peer guide g${index + 1}`, x, y, 20, {
      "font-weight": 600,
    });
    if (!row || row.guide.q25 === null) {
      line(x + 10, y + 30, x + width - 10, y + 30, "#b8c7c2", {
        "stroke-width": 4,
      });
      if (row?.datum.value !== null && row?.datum.value !== undefined)
        dot(
          "on",
          x + 10 + ((width - 20) * row.datum.value) / extent,
          y + 30,
          "#087b73",
        );
      text(`n=${row?.guide.n ?? 0} · guide unavailable`, x, y + 65, 20);
      missing(
        row?.guide.reason ?? "no eligible guide population",
        x,
        y + 94,
        width,
      );
      return;
    }
    const g = row.guide;
    const px = (value: number) => x + 10 + ((width - 20) * value) / extent;
    line(x + 10, y + 30, x + width - 10, y + 30, "#b8c7c2", {
      "stroke-width": 4,
    });
    for (const value of [g.q25, g.q50, g.q75])
      if (value !== null)
        line(px(value), y + 21, px(value), y + 39, "#52686a", {
          "stroke-width": 2,
        });
    if (row.datum.value !== null)
      dot("on", px(row.datum.value), y + 30, "#087b73");
    for (const [i, key] of ["q25", "q50", "q75"].entries())
      text(
        `${key} ${numberText(g[key as "q25"])}`,
        x + (i * width) / 3,
        y + 65,
        20,
      );
    text(
      `n=${g.n}${g.n === 1 ? " · coincident" : ""} · ${g.member ? "in guide" : "outside guide"}`,
      x,
      y + 94,
      20,
    );
  };
  panel(
    `reported usage${supportMark(d?.reported_usage.support) === "partial support" ? "*" : ""}`,
    44,
    Y(290),
    346,
    "d01–02",
  );
  const usage = d?.reported_usage;
  text(
    `${numberText(usage?.minutes_per_appearance.value)} min / appearance`,
    44,
    Y(341),
    22,
    { "font-weight": 650 },
  );
  text(
    `${numberText(usage?.positive_toi_appearances, 0)} ${usage?.positive_toi_appearances === 1 ? "appearance" : "appearances"}`,
    44,
    Y(374),
    20,
  );
  text(
    usage
      ? `${numberText(usage.supported_games, 0)}/${numberText(usage.listed_games, 0)} games supported/listed`
      : "supported/listed games unavailable",
    44,
    Y(398),
    20,
  );
  guide(0, 44, Y(430), 346, scales.usage);
  const strengths = ["ev", "pp", "pk", "other"] as const;
  const colors = ["#087b73", "#566f8b", "#a18b4f", "#a7adaa"];
  const values = strengths.map((key) => d?.strength_usage[key].seconds ?? null);
  const known = values.reduce<number>((sum, value) => sum + (value ?? 0), 0);
  text(
    `included ${values.every((value) => value !== null) ? "total" : "known subtotal"}: ${numberText(values.some((value) => value !== null) ? known / 60 : null, 1)} min`,
    44,
    Y(558),
    20,
  );
  let sx = 44;
  strengths.forEach((key, index) => {
    const value = values[index];
    if (value !== null) {
      const width = (346 * (value / 60)) / scales.strengthMinutes;
      rect(sx, Y(578), width, 22, colors[index]!);
      sx += width;
    }
  });
  strengths.forEach((key, index) => {
    text(
      `${key} ${numberText(values[index] === null ? null : values[index]! / 60, 1)} min`,
      44 + (index % 2) * 173,
      Y(626 + Math.floor(index / 2) * 25),
      20,
    );
  });
  for (const [index, strength, x] of [
    [1, "ev", 427],
    [2, "pp", 810],
  ] as const) {
    panel(
      `${strength} primary scoring`,
      x,
      Y(290),
      346,
      strength === "ev" ? "d03" : "d04",
    );
    const row = d?.scoring_by_strength[strength];
    text(
      `${numberText(row?.primary_points_per60.value)} primary points / 60`,
      x,
      Y(341),
      20,
      { "font-weight": 650 },
    );
    const max = strength === "ev" ? scales.ev : scales.pp;
    const g = row?.goals_per60.value,
      a = row?.primary_assists_per60.value;
    if (g !== null && g !== undefined && a !== null && a !== undefined) {
      rect(x, Y(361), (346 * g) / max, 24, "#087b73");
      rect(x + (346 * g) / max, Y(361), (346 * a) / max, 24, "#8eaeab");
    } else missing(familyReason ?? "scoring rate unavailable", x, Y(381), 346);
    guide(index, x, Y(430), 346, max);
    text(`goals ${numberText(g)} + a1 ${numberText(a)} / 60`, x, Y(558), 20);
    text(
      `${numberText(row?.goals, 0)} goals · ${numberText(row?.primary_assists, 0)} a1`,
      x,
      Y(590),
      20,
    );
    wrap(
      `${numberText(row?.seconds === null || row?.seconds === undefined ? null : row.seconds / 60, 1)} scoring min · ${supportMark(row?.support)}`,
      x,
      Y(626),
      346,
      20,
    );
  }
  const scatter = (
    key: "on_off_attempts" | "on_off_goals",
    x: number,
    title: string,
    extent: number,
    panelKey: string,
  ) => {
    panel(title, x, Y(680), 535, panelKey);
    text("5v5 · recorded for / against per 60", x, Y(725), 20);
    const px = x + 70,
      py = Y(760),
      w = 250,
      h = 250;
    line(px, py + h, px + w, py + h, "#5a6a6b");
    line(px, py, px, py + h, "#5a6a6b");
    line(px, py + h, px + w, py, "#a8b7b0", { "stroke-dasharray": "6 5" });
    for (const t of [0, 0.5, 1]) {
      text(numberText(extent * t, 1), px + w * t, py + h + 29, 20, {
        "text-anchor": "middle",
      });
      text(numberText(extent * t, 1), px - 12, py + h - h * t + 7, 20, {
        "text-anchor": "end",
      });
    }
    text("against / 60 →", px + 150, py + h + 63, 20, {
      "text-anchor": "middle",
    });
    text("for / 60", x - 14, py + h / 2, 20, {
      transform: `rotate(-90 ${x - 14} ${py + h / 2})`,
      "text-anchor": "middle",
    });
    const data = d?.[key];
    for (const [index, scope] of ["on", "off", "league"].entries()) {
      const group = data?.[scope as "on"];
      const forRate = group?.for_per60.value,
        against = group?.against_per60.value;
      const color =
        index === 0 ? "#087b73" : index === 1 ? "#455c6f" : "#8a7549";
      const ly = py + index * 78;
      dot(scope, x + 407, ly - 5, color);
      text(
        `${scope}${supportMark(group?.support) === "partial support" ? "*" : ""}`,
        x + 427,
        ly + 2,
        20,
      );
      text(
        `${numberText(group?.share_minus_half.value, 2)} pp`,
        x + 397,
        ly + 29,
        20,
      );
      text("share − 50%", x + 397, ly + 53, 20);
      if (
        forRate !== null &&
        forRate !== undefined &&
        against !== null &&
        against !== undefined
      )
        dot(
          scope,
          px + (w * against) / extent,
          py + h - (h * forRate) / extent,
          color,
        );
      else
        text("point unavailable", px + 12, py + 28 + index * 28, 20, {
          fill: "#536667",
        });
    }
    wrap("dashed: for = against", x + 397, Y(1030), 138, 20);
  };
  scatter("on_off_attempts", 44, "recorded attempts", scales.attempts, "d06");
  scatter("on_off_goals", 621, "recorded goals", scales.goals, "d07");
  panel("on-ice conversion", 44, Y(1140), 346, "d08");
  panel("recorded penalties", 427, Y(1140), 346, "d09");
  panel("counterpart bands", 810, Y(1140), 346, "d12");
  text("shooting fractions · on-net", 44, Y(1185), 20);
  text("per 1,000 matched reported min", 427, Y(1185), 20);
  text("league usage bands", 810, Y(1185), 20);
  const scopes = ["focal", "team", "league"] as const;
  scopes.forEach((scope, index) => {
    const y = Y(1230 + index * 100);
    const conversion = d?.on_ice_conversion[scope];
    const penalty = d?.recorded_penalties[scope];
    text(
      `${scope}${supportMark(conversion?.support) === "partial support" ? "*" : ""}`,
      44,
      y,
      20,
      { "font-weight": 600 },
    );
    text(scope, 427, y, 20, { "font-weight": 600 });
    for (const [i, role] of ["shooting_for", "shooting_against"].entries()) {
      const value = conversion?.[role as "shooting_for"].value;
      const baseline = y + 31 + i * 29;
      text(i === 0 ? "for" : "against", 44, baseline, 20);
      if (value !== null && value !== undefined)
        rect(
          145,
          baseline - 17,
          (120 * value) / scales.conversion,
          17,
          i === 0 ? "#087b73" : "#566f8b",
        );
      text(
        value === null || value === undefined
          ? "unavailable"
          : `${numberText(value * 100)}%`,
        277,
        baseline,
        20,
      );
    }
    for (const [i, role] of ["drawn", "taken"].entries()) {
      const record = penalty?.[role as "drawn"];
      const value = record?.per1000minutes.value;
      const baseline = y + 31 + i * 29;
      text(
        `${role}${supportMark(record?.support) === "partial support" ? "*" : ""}`,
        427,
        baseline,
        20,
      );
      if (value !== null && value !== undefined)
        rect(
          528,
          baseline - 17,
          (120 * value) / scales.penalties,
          17,
          i === 0 ? "#087b73" : "#566f8b",
        );
      text(numberText(value), 660, baseline, 20);
    }
  });
  text("recorded conversion, not ability", 44, Y(1530), 20);
  text("positive recorded role rates", 427, Y(1530), 20);
  panel("shift starts", 44, Y(1590), 346, "d10");
  panel("score time", 427, Y(1590), 346, "d11");
  text("all starts · O / N / D / fly / unknown", 44, Y(1635), 20);
  text("known time · leading / tied / trailing", 427, Y(1635), 20);
  const starts = [
    "offensive",
    "neutral",
    "defensive",
    "on_the_fly",
    "unknown",
  ] as const;
  const score = ["leading", "tied", "trailing"] as const;
  const portions = ["#087b73", "#889b9f", "#566f8b", "#b29759", "#c9c3ba"];
  scopes.forEach((scope, index) => {
    const group = d?.deployment[scope];
    const y = Y(1690 + index * 120);
    const label = `${scope}${supportMark(group?.support) === "partial support" ? "*" : ""}`;
    text(label, 44, y, 20, { "font-weight": 600 });
    text(label, 427, y, 20, { "font-weight": 600 });
    const startValues = starts.map(
      (key) => group?.shift_starts[key].share.value ?? null,
    );
    const scoreValues = score.map(
      (key) => group?.score[key].share.value ?? null,
    );
    let startX = 44,
      scoreX = 427;
    if (startValues.every((value) => value !== null)) {
      starts.forEach((_, i) => {
        const width = 346 * startValues[i]!;
        rect(startX, y + 14, width, 22, portions[i]!);
        startX += width;
      });
    } else text(familyReason ?? "start total unavailable", 44, y + 35, 20);
    if (scoreValues.every((value) => value !== null)) {
      score.forEach((_, i) => {
        const width = 346 * scoreValues[i]!;
        rect(scoreX, y + 14, width, 22, portions[i]!);
        scoreX += width;
      });
    } else text(familyReason ?? "score total unavailable", 427, y + 35, 20);
    const startCaption = startValues.every((value) => value === null)
      ? "all category shares unavailable"
      : startValues
          .map((value) => numberText(value === null ? null : value * 100, 1))
          .join(" / ") + " %";
    wrap(startCaption, 44, y + 66, 346, 20);
    const unknown = group?.score.unknown.share.value;
    wrap(
      unknown === null || unknown === undefined
        ? "unknown-time fraction unavailable"
        : `unknown ${numberText(unknown * 100, 1)}% of all time`,
      427,
      y + 66,
      346,
      20,
    );
  });
  const cx = 870,
    cy = Y(1270),
    cw = 250,
    ch = 220;
  line(cx, cy, cx, cy + ch, "#5a6a6b");
  line(cx, cy + ch, cx + cw, cy + ch, "#5a6a6b");
  for (const band of [1, 2, 3, 4])
    text(`f${band}`, cx - 15, cy + (ch * (band - 1)) / 3 + 7, 20, {
      "text-anchor": "end",
    });
  for (const band of [3, 2, 1])
    text(`d${band}`, cx + (cw * (3 - band)) / 2, cy + ch + 30, 20, {
      "text-anchor": "middle",
    });
  text("defense usage band →", cx + cw / 2, cy + ch + 63, 20, {
    "text-anchor": "middle",
  });
  text("forward usage band ↓", 810, cy - 25, 20);
  for (const [index, scope] of ["teammates", "opponents"].entries()) {
    const group = c?.[scope as "teammates"];
    const forward = group?.forward.mean_band_index.value;
    const defense = group?.defense.mean_band_index.value;
    const forwardKnown = typeof forward === "number";
    const defenseKnown = typeof defense === "number";
    const color = index === 0 ? "#087b73" : "#455c6f";
    const y = Y(1670 + index * 170);
    dot(scope, 824, y - 7, color);
    text(
      `${scope}${supportMark(group?.coverage) === "partial support" ? "*" : ""}`,
      848,
      y,
      22,
    );
    text(
      `F ${numberText(forward)} · D ${numberText(defense)}`,
      810,
      y + 35,
      20,
    );
    if (forwardKnown && defenseKnown) {
      dot(
        scope,
        cx + (cw * (3 - defense)) / 2,
        cy + (ch * (forward - 1)) / 3,
        color,
      );
    } else
      wrap(
        !forwardKnown && !defenseKnown
          ? "both usage bands unavailable"
          : "point unavailable; known coordinate retained in detail",
        810,
        y + 70,
        346,
        20,
      );
  }
  wrap(
    "fractional source-defined usage bands; neither fitted quality nor actual lines. no league point.",
    810,
    Y(2040),
    346,
    20,
  );
  const footerY = Y(2160);
  line(44, footerY - 25, 1156, footerY - 25);
  text(
    "recorded observations, not adjusted impact or repeatable ability. guides are empirical quartiles, not uncertainty.",
    44,
    footerY,
    18,
  );
  text(
    `g1: ${model.guides[0]?.guide.peerGroup ?? "unavailable"}, ≥${model.settings.peerMin} observed 5v5 min; g2: ev ≥${model.settings.peerMin} scoring min; g3: pp ≥${model.settings.specialtyMin} scoring min.`,
    44,
    footerY + 27,
    18,
  );
  text(
    "d06/07: dressed-game off ice; physical team-time league. d08: on-net. d10/11: start / player-time references.",
    44,
    footerY + 54,
    18,
  );
  text(
    `descriptive ${model.descriptive.availability} · context ${model.context.availability} · * partial/gapped support; panel keys resolve details/csv.`,
    44,
    footerY + 81,
    18,
  );
  const sourceKeys =
    [
      ...new Set(
        [d?.provenance.id, c?.provenance.id]
          .filter((id): id is string => Boolean(id))
          .map((id) => (id.length > 44 ? `${id.slice(0, 41)}…` : id)),
      ),
    ].join(" / ") || "no provided source";
  const sourceLines = words(`source/method: ${sourceKeys}`, 112);
  sourceLines.forEach((value, index) =>
    text(value, 44, footerY + 108 + index * 24, 18),
  );
  const idFooter = footerY + 108 + sourceLines.length * 24;
  text(
    `publication ${model.publication.publication_id} · ${model.publication.purpose} · ${model.publication.generated_at}`,
    44,
    idFooter,
    18,
  );
  if (model.publication.purpose === "fixture")
    text(
      "fixture publication · development evidence",
      44,
      idFooter + 26,
      18,
      { "font-weight": 700 },
    );
  const height = Math.ceil(
    idFooter + (model.publication.purpose === "fixture" ? 56 : 32),
  );
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${height}" viewBox="0 0 1200 ${height}" role="img" aria-label="${xml(`${name}: ${seasonLabel(model.season.season)} descriptive skater sheet`)}" font-family="system-ui, sans-serif" fill="#242b2d" style="font-variant-numeric:tabular-nums"><title>${xml(`${name}: ${seasonLabel(model.season.season)} descriptive skater sheet; recorded observations with separate support and references`)}</title><rect width="1200" height="${height}" fill="#fbfaf6"/>${pieces.join("")}</svg>`;
}

export default function DescriptiveCard({
  model,
  scales,
  controls,
  detailLink,
}: {
  readonly model: DescriptiveCardModel;
  readonly scales?: DescriptiveScales;
  readonly controls?: ReactNode;
  readonly detailLink?: (id: AnalysisMetricId) => {
    readonly to: string;
    readonly state?: unknown;
  };
}) {
  const heading = useId();
  const [state, setState] = useState<"idle" | "rendering" | "saved" | "failed">(
    "idle",
  );
  const rendering = useRef(false);
  const fields = descriptiveFields(model);
  return (
    <section className="descriptive-sheet" aria-labelledby={heading}>
      <h3 id={heading}>recorded descriptive skater sheet</h3>
      {controls}
      <div
        className="descriptive-sheet-art"
        role="region"
        aria-label="recorded descriptive sheet, scroll horizontally to read all panels"
        tabIndex={0}
        dangerouslySetInnerHTML={{ __html: cardSvg(model, scales) }}
      />
      <div className="card-actions">
        <button
          type="button"
          disabled={state === "rendering"}
          onClick={async () => {
            if (rendering.current) return;
            rendering.current = true;
            setState("rendering");
            const snapshot = model,
              snapshotScales = scales ? { ...scales } : undefined;
            try {
              const blob = await svgPng(cardSvg(snapshot, snapshotScales));
              downloadBlob(
                blob,
                `hockey-stats-${snapshot.season.season}-${snapshot.playerId}-descriptive.png`,
              );
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
        <button
          type="button"
          onClick={() => {
            const snapshot = model;
            downloadBlob(
              new Blob([descriptiveCsv(snapshot)], {
                type: "text/csv;charset=utf-8",
              }),
              `hockey-stats-${snapshot.season.season}-${snapshot.playerId}-descriptive.csv`,
            );
          }}
        >
          download card data csv
        </button>
        <p role="status" aria-live="polite">
          {state === "rendering"
            ? "preparing this selected-season sheet…"
            : state === "saved"
              ? "png download prepared."
              : state === "failed"
                ? "png could not be created. try again."
                : "single-season recorded facts; annual evidence remains separate."}
        </p>
      </div>
      <div className="descriptive-history-links">
        <h4>raw usage and scoring history</h4>
        <p>
          no percentile defined; these guides describe a viewing population.
        </p>
        {model.guides.map((row) => (
          <p key={row.datum.metric.id}>
            {detailLink ? (
              <Link {...detailLink(row.datum.metric.id)}>
                {row.datum.metric.label}
              </Link>
            ) : (
              row.datum.metric.label
            )}
            : {numberText(row.datum.value)} {row.datum.metric.displayUnit} ·{" "}
            {row.datum.reason ?? supportMark(row.datum.support ?? undefined)} ·{" "}
            {row.guide.peerGroup} · n={row.guide.n} · cutoff{" "}
            {row.guide.cutoffMinutes} min · {row.guide.qualification} ·
            incompatible meanings {row.guide.incompatiblePeerCount}
          </p>
        ))}
      </div>
      <section className="descriptive-annual">
        <h4>annual factual records</h4>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>season</th>
                <th>appearances</th>
                <th>reported min / appearance</th>
                <th>included strength min (ev / pp / pk / other)</th>
                <th>ev primary points / 60</th>
                <th>pp primary points / 60</th>
                <th>support</th>
              </tr>
            </thead>
            <tbody>
              {model.annual.map((row) => {
                const d = row.descriptive.data;
                return (
                  <tr key={row.season.season}>
                    <th>
                      <Link
                        to={`/players/${model.playerId}?season=${row.season.season}&view=observed`}
                      >
                        {seasonLabel(row.season.season)}
                      </Link>
                    </th>
                    <td>
                      {numberText(
                        d?.reported_usage.positive_toi_appearances,
                        0,
                      )}
                    </td>
                    <td>
                      {numberText(
                        d?.reported_usage.minutes_per_appearance.value,
                      )}
                    </td>
                    <td>
                      {(["ev", "pp", "pk", "other"] as const)
                        .map((key) =>
                          numberText(
                            d?.strength_usage[key].seconds === null ||
                              d?.strength_usage[key].seconds === undefined
                              ? null
                              : d.strength_usage[key].seconds! / 60,
                            1,
                          ),
                        )
                        .join(" / ")}
                    </td>
                    <td>
                      {numberText(
                        d?.scoring_by_strength.ev.primary_points_per60.value,
                      )}{" "}
                      ·{" "}
                      {numberText(
                        d?.scoring_by_strength.ev.seconds === null ||
                          d?.scoring_by_strength.ev.seconds === undefined
                          ? null
                          : d.scoring_by_strength.ev.seconds! / 60,
                        1,
                      )}{" "}
                      scoring min
                    </td>
                    <td>
                      {numberText(
                        d?.scoring_by_strength.pp.primary_points_per60.value,
                      )}{" "}
                      ·{" "}
                      {numberText(
                        d?.scoring_by_strength.pp.seconds === null ||
                          d?.scoring_by_strength.pp.seconds === undefined
                          ? null
                          : d.scoring_by_strength.pp.seconds! / 60,
                        1,
                      )}{" "}
                      scoring min
                    </td>
                    <td>
                      {row.descriptive.availability === "provided"
                        ? `${supportMark(d?.reported_usage.support)}; ev ${supportMark(d?.scoring_by_strength.ev.support)}; pp ${supportMark(d?.scoring_by_strength.pp.support)}`
                        : `${row.descriptive.availability}: ${row.descriptive.explanation}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <details className="descriptive-detail">
        <summary>panel values, counts, denominators, sources and gaps</summary>
        <p>
          reported all-strength time differs from included elapsed strength
          time. ev includes supported 4v4 and 3v3. off ice covers dressed games.
          share minus half is in percentage points; conversion and deployment
          are fractions. unknown score share uses all known plus unknown time;
          leading/tied/trailing shares use known time.
        </p>
        <p>
          band weights use counterpart slots, not shared-minute table shares.
          references are published team/league populations. no browser exposure
          reconstruction or adjustment is applied.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>panel / scope / category</th>
                <th>published field</th>
                <th>value / native unit</th>
                <th>status / support</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((field) => (
                <tr
                  key={JSON.stringify([
                    field.panel,
                    field.scope,
                    field.path,
                    field.category,
                  ])}
                >
                  <td>
                    {field.panel} / {field.scope}
                    {field.category ? ` / ${field.category}` : ""}
                  </td>
                  <th>{field.path}</th>
                  <td>
                    {field.value === null ? "unavailable" : String(field.value)}{" "}
                    {field.unit}
                  </td>
                  <td>
                    {field.status}
                    {field.reason ? `: ${field.reason}` : ""}
                    <details>
                      <summary>support and source</summary>
                      <pre>
                        {JSON.stringify(
                          {
                            source_paths: field.sourcePaths,
                            numerator: field.numerator,
                            denominator: field.denominator,
                            denominator_kind: field.denominatorKind,
                            support: field.support,
                            sources: field.sourceIds.map(
                              (id) => model.sources[id],
                            ),
                            methods: field.methodIds.map(
                              (id) => model.methods[id],
                            ),
                            guide: field.guide?.guide,
                          },
                          null,
                          2,
                        )}
                      </pre>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {model.person && (
          <details>
            <summary>selected annual identity and missing fields</summary>
            <pre>{JSON.stringify(model.person, null, 2)}</pre>
          </details>
        )}
        <p>
          publication {model.publication.publication_id}; corpus sha-256{" "}
          {model.season.corpus_sha256}.
        </p>
      </details>
      <Link
        to={`/players/${model.playerId}?season=${model.season.season}&view=observed#games-heading`}
      >
        view selected-year game evidence
      </Link>
    </section>
  );
}
