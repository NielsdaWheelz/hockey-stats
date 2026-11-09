import { useId, useRef, useState } from "react";
import { Link } from "react-router";
import type { AnalysisMetricId } from "./analysis-values";
import { analysisCsvHeaders, analysisCsvRow, DatumEvidence, displayNumber, standingText, valueText } from "./analysis-history";
import { csvText, downloadBlob, svgPng } from "./export";
import type { MicrostatCardModel } from "./microstat-values";
import { playerName, seasonLabel, teamName } from "./presentation";

type Field = MicrostatCardModel["groups"][number]["slots"][number]["fields"][number];
const identity = (model: MicrostatCardModel) => model.person ? playerName(model.person)
  : model.historicalPerson ? `${playerName(model.historicalPerson)} · historical identity` : `player ${model.playerId}`;
const layoutLabel = (model: MicrostatCardModel) => model.layout === "unknown"
  ? "position unavailable · all microstat fields" : `${model.layout} microstats`;
const marker = (field: Field) => [(field.fact?.construction ?? field.row.datum.status).replaceAll("_", " "), field.supportKey, ...field.evidenceKeys].filter(Boolean).join(" · ");
const dispositions = (model: MicrostatCardModel) => {
  const fields = model.groups.flatMap(group => group.slots.flatMap(slot => slot.fields));
  return [...new Set(fields.flatMap(field => field.state ? [field.state] : []))].join("; ");
};
const peerLabel = (model: MicrostatCardModel) => `${model.settings.peers === "all" ? "all skaters" : "same-year reported position"}; cutoff ${model.settings.peerMin} matched min`;
const supportText = (support: MicrostatCardModel["supports"][number]) => `${support.key}: ${support.population} · ${support.includedSeconds === null ? "unknown included minutes" : `${displayNumber(support.includedSeconds / 60)} included min`} · ${support.coverage}${support.opportunities === null ? "" : ` · denominator ${displayNumber(support.opportunities)} opponent attempts`}`;

export function microstatCsv(model: MicrostatCardModel): string {
  return csvText(["layout", "section", "slot_id", ...analysisCsvHeaders], [
    ...model.groups.flatMap(group => group.slots.flatMap(slot => slot.fields.map(field => [
      model.layout, group.label, slot.id, ...analysisCsvRow(model.publication, model.season, field.row),
    ]))),
    ...model.components.map(row => [model.layout, "modeled component context", row.datum.metric.id, ...analysisCsvRow(model.publication, model.season, row)]),
  ]);
}

const xml = (text: string | number) => String(text).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
function lines(text: string, length: number): string[] {
  const result: string[] = [];
  let line = "";
  for (const word of text.split(/\s+/)) {
    if (line && line.length + word.length + 1 > length) { result.push(line); line = ""; }
    if (word.length > length) {
      if (line) { result.push(line); line = ""; }
      for (let i = 0; i < word.length; i += length) result.push(word.slice(i, i + length));
    } else line += `${line ? " " : ""}${word}`;
  }
  if (line) result.push(line);
  return result;
}

export function microstatCardSvg(model: MicrostatCardModel): string {
  const parts: string[] = [];
  const text = (value: string | number, x: number, y: number, size = 20, extra = "") => parts.push(`<text x="${x}" y="${y}" font-size="${size}" ${extra}>${xml(value)}</text>`);
  const wrap = (value: string, x: number, y: number, length: number, size = 20, extra = "") => {
    const wrapped = lines(value, length);
    const leading = size >= 32 ? size + 10 : size + 5;
    wrapped.forEach((value, index) => text(value, x, y + index * leading, size, extra));
    return wrapped.length * leading;
  };
  const rule = (x: number, y: number, width: number) => parts.push(`<path d="M${x} ${y}h${width}" stroke="#d7dad5"/>`);
  let y = 36;
  text(model.publication.purpose === "fixture" ? "synthetic fixture · microstat card" : "season microstat card", 44, y, 20, 'fill="#145a66" font-weight="700"');
  y += 42;
  y += wrap(identity(model), 44, y, 55, 32, 'font-weight="700"');
  text(`${seasonLabel(model.season.season)} · ${model.person?.reported_position ?? "position unavailable"} · ${model.person ? model.person.teams.map(teamName).join(" / ") || "teams unavailable" : "absent selected season"}`, 44, y + 10);
  y += 38;
  text(layoutLabel(model), 44, y, 22, 'font-weight="600"');
  y += 28;
  text(peerLabel(model), 44, y);
  y += 34;
  for (let pair = 0; pair < model.groups.length; pair += 2) {
    let bottom = y;
    for (let column = 0; column < 2; column++) {
      const group = model.groups[pair + column];
      if (!group) continue;
      const x = 44 + column * 570;
      text(group.label, x, y, 25, 'font-weight="700"');
      text("raw quantity", x + 275, y, 20, 'fill="#566263"');
      text("percentile", x + 433, y, 20, 'fill="#566263"');
      rule(x, y + 16, 542);
      let rowY = y + 40;
      for (const slot of group.slots) {
        for (const field of slot.fields) {
          const { datum, standing } = field.row;
          const labelHeight = wrap(datum.metric.label, x, rowY, 23, 20, 'font-weight="600"');
          let contentHeight: number;
          if (datum.value !== null) {
            text(valueText(datum), x + 275, rowY, 24, 'font-weight="650"');
            contentHeight = 31 + wrap(datum.metric.displayUnit, x + 275, rowY + 28, 15);
            if (standing.kind === "ranked") {
              text(standingText(standing).replace(" percentile", ""), x + 433, rowY, 22, 'font-weight="650"');
              text(`n=${standing.n}`, x + 433, rowY + 27);
              parts.push(`<rect x="${x + 433}" y="${rowY + 36}" width="104" height="5" fill="#e5eeec"/><rect x="${x + 433}" y="${rowY + 36}" width="${104 * standing.percentile / 100}" height="5" fill="#4e817e"/>`);
              contentHeight = Math.max(contentHeight, 48);
            } else {
              contentHeight = Math.max(contentHeight, wrap(standingText(standing), x + 433, rowY, 12));
            }
          } else {
            contentHeight = wrap(field.state ?? "unavailable", x + 275, rowY, 26);
            contentHeight += wrap(datum.metric.displayUnit, x + 275, rowY + contentHeight + 2, 26);
          }
          const markerY = rowY + Math.max(labelHeight, contentHeight) + 4;
          const markerHeight = wrap(marker(field), x, markerY, 48, 20, 'fill="#566263"');
          rowY = markerY + markerHeight + 2;
        }
      }
      bottom = Math.max(bottom, rowY);
    }
    y = bottom + 24;
  }
  text("support keys", 44, y, 22, 'font-weight="700"');
  y += 30;
  if (!model.supports.length) { text("no available field support; reasons remain field-specific", 44, y); y += 29; }
  for (const support of model.supports) y += wrap(supportText(support), 44, y, 105, 20) + 3;
  if (model.evidence.length) {
    y += 8;
    y += wrap(model.evidence.map(entry => `${entry.key} ${entry.construction}: ${entry.id}`).join(" · "), 44, y, 113, 18) + 10;
  }
  rule(44, y, 1112);
  y += 28;
  const footer = [
    `${seasonLabel(model.season.season)}; supported 5v5 facts plus model-valued reference xg; field-specific units and matched support.`,
    "higher percentile means higher quantity, not better play. population spread is not uncertainty. reference xg is experimental, not a forecast.",
    dispositions(model),
    `publication ${model.publication.publication_id} · ${model.publication.purpose}; source/method keys above; full evidence in page/csv.`,
  ].filter(Boolean);
  for (const line of footer) y += wrap(line, 44, y, 113, 18) + 2;
  const height = y + 16;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${height}" viewBox="0 0 1200 ${height}" role="img" aria-label="${xml(`${identity(model)}: ${layoutLabel(model)}`)}" font-family="system-ui, sans-serif" fill="#242b2d" style="font-variant-numeric:tabular-nums"><title>${xml(`${identity(model)}: ${seasonLabel(model.season.season)} ${layoutLabel(model)}`)}</title><rect width="1200" height="${height}" fill="#fbfaf6"/>${parts.join("")}</svg>`;
}

export default function MicrostatCard({ model, detailLink }: {
  readonly model: MicrostatCardModel;
  readonly detailLink?: (id: AnalysisMetricId) => { readonly to: string; readonly state?: unknown };
}) {
  const heading = useId();
  const [download, setDownload] = useState<"idle" | "rendering" | "saved" | "failed">("idle");
  const rendering = useRef(false);
  return <section className="microstat-card" aria-labelledby={heading}>
    <header>
      <p className="microstat-kicker">{model.publication.purpose === "fixture" ? "synthetic fixture · microstat card" : "season microstat card"}</p>
      <h3 id={heading}>{identity(model)}</h3>
      <p>{seasonLabel(model.season.season)} · {model.person?.reported_position ?? "position unavailable"} · {model.person ? model.person.teams.map(teamName).join(" / ") || "teams unavailable" : "absent selected season"}</p>
      <p>{layoutLabel(model)} · {peerLabel(model)}</p>
    </header>
    <div className="microstat-groups">
      {model.groups.map(group => <section className="microstat-group" key={group.label}>
        <h4>{group.label}</h4>
        <div className="microstat-columns" aria-hidden="true"><span>quantity</span><span>raw value</span><span>standing</span></div>
        {group.slots.map(slot => <div className="microstat-slot" data-slot={slot.id} key={slot.id}>
          {slot.fields.map(field => {
            const { datum, standing } = field.row;
            return <div className="microstat-field" key={datum.metric.id} data-metric={datum.metric.id}>
              <div className="microstat-label">{detailLink ? <Link {...detailLink(datum.metric.id)}>{datum.metric.label}</Link> : datum.metric.label}</div>
              <div className="microstat-value">{datum.value === null ? <span className="microstat-unavailable">{field.state}</span> : <strong>{valueText(datum)}</strong>}<span className="microstat-unit">{datum.metric.displayUnit}</span></div>
              <div className="microstat-standing">{standing.kind === "ranked" ? <><strong>{standingText(standing)}</strong><span>n={standing.n}</span><meter min={0} max={100} value={standing.percentile} aria-label={`${datum.metric.label} percentile`}/></> : <span>{datum.value === null ? "no standing" : standingText(standing)}</span>}</div>
              <p className="microstat-marker">{marker(field)}{field.supportKey && ` · ${model.supports.find(support => support.key === field.supportKey)!.coverage}`}</p>
              {datum.value === null && datum.original?.reason_detail && <p className="microstat-reason">{datum.original.reason_detail.explanation}</p>}
              <div className="microstat-evidence"><DatumEvidence datum={datum}/></div>
            </div>;
          })}
        </div>)}
      </section>)}
    </div>
    <div className="microstat-supports">
      <h4>support and source keys</h4>
      {model.supports.map(support => <p key={support.key}>{supportText(support)}</p>)}
      {model.evidence.map(entry => <p key={entry.key}>{entry.key}: {entry.construction} · {entry.id}</p>)}
    </div>
    <footer>
      <p>{seasonLabel(model.season.season)}: supported 5v5 facts plus model-valued reference xg; field-specific units and matched support. higher percentile means higher quantity, not better play. population spread is not uncertainty.</p>
      <p>reference xg is experimental same-season model valuation, not a held-out forecast. calibration and attribution limitations remain in its field evidence.</p>
      {dispositions(model) && <p>{dispositions(model)}</p>}
      <p>publication {model.publication.publication_id} · {model.publication.purpose}</p>
    </footer>
    <div className="card-actions">
      <button type="button" disabled={download === "rendering"} onClick={async () => {
        if (rendering.current) return;
        rendering.current = true;
        setDownload("rendering");
        const snapshot = model;
        try {
          const blob = await svgPng(microstatCardSvg(snapshot));
          downloadBlob(blob, `hockey-stats-${snapshot.season.season}-${snapshot.playerId}-microstats.png`);
          setDownload("saved");
        } catch { setDownload("failed"); }
        finally { rendering.current = false; }
      }}>{download === "rendering" ? "rendering png…" : "download player png"}</button>
      <button type="button" onClick={() => {
        const snapshot = model;
        downloadBlob(new Blob([microstatCsv(snapshot)], { type: "text/csv;charset=utf-8" }), `hockey-stats-${snapshot.season.season}-${snapshot.playerId}-microstats.csv`);
      }}>download card data csv</button>
      <p role="status" aria-live="polite">{download === "rendering" ? "preparing the selected card…" : download === "saved" ? "png download prepared." : download === "failed" ? "png could not be created. try again." : "single-player card; component context and history remain separate."}</p>
    </div>
    <section className="microstat-components">
      <h4>modeled component context</h4>
      <p>league-relative goals per common workload: 1,000 minutes at 5v5; 100 power-play minutes; 100 penalty-kill minutes. finishing and penalties use the published common workload. these six terms are a subset, never a total.</p>
      <div className="microstat-component-grid">{model.components.map(row => <div key={row.datum.metric.id} className="microstat-component" data-metric={row.datum.metric.id}>
        <h5>{detailLink ? <Link {...detailLink(row.datum.metric.id)}>{row.datum.metric.label}</Link> : row.datum.metric.label}</h5>
        <p>{row.datum.value === null ? `${row.datum.status === "absent" ? "absent season" : row.datum.status === "not_computed" || row.datum.original?.unavailable_reason === "not_computed" ? "pending computation" : row.datum.reason?.replaceAll("_", " ") ?? "unavailable"} · ledger` : `${valueText(row.datum)} ${row.datum.metric.displayUnit}`}</p>
        <p>{standingText(row.standing)}{row.standing.kind === "ranked" && ` · n=${row.standing.n}`}</p>
        {Object.entries(row.datum.componentSupport).map(([role, component]) => <p key={role}>{role.replaceAll("_", " ")}: {component.support ? component.support.prior_only ? "prior-only role" : component.support.current_season_information ? "current-season information" : "no current-season information" : component.reason}</p>)}
        <DatumEvidence datum={row.datum}/>
      </div>)}</div>
    </section>
  </section>;
}
