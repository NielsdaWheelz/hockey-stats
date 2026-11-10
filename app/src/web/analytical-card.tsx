import { useId, useState } from "react";
import { Link } from "react-router";
import type {
  MapsResponse,
  Person,
  Support,
  SkaterSpatial,
} from "../shared/player-analysis";
import type { Publication, SeasonEvidence } from "../shared/observed";
import type { ProfileView } from "./client";
import type { PeerSettings } from "./explorer";
import {
  analysisMetric,
  selectHistoryValue,
  selectLeagueValues,
  type AnalysisMetricId,
} from "./analysis-values";
import {
  buildAnalysisCohort,
  rawOnlyStanding,
  type AnalysisPeerGroup,
} from "./analysis-cohorts";
import {
  analysisCsvHeaders,
  analysisCsvRow,
  displayNumber,
  displayValue,
  plotDomain,
  valueText,
  type AnalysisRow,
} from "./analysis-history";
import {
  AnalyticalMapDrawing,
  AnalyticalMapLegend,
  analyticalMapDrawingSvg,
  prepareAnalyticalMap,
  type AnalyticalMapModel,
} from "./analytical-map";
import { ledgerPresentation } from "./ledger-presentation";
import { csvText, downloadBlob, svgPng } from "./export";
import { playerName, seasonLabel, teamName } from "./presentation";

const mapSlots = [
  {
    slotId: "i01",
    label: "5v5 offense",
    strength: "5v5",
    role: "offense",
    attemptId: "spatial.5v5.offense_attempts_per60",
    xgId: "spatial.5v5.offense_xg_per60",
  },
  {
    slotId: "i02",
    label: "common pp offense",
    strength: "pp",
    role: "offense",
    attemptId: "spatial.pp.offense_attempts_per60",
    xgId: "spatial.pp.offense_xg_per60",
  },
  {
    slotId: "i03",
    label: "5v5 defense",
    strength: "5v5",
    role: "defense",
    attemptId: "spatial.5v5.defense_attempts_per60",
    xgId: "spatial.5v5.defense_xg_per60",
  },
  {
    slotId: "i04",
    label: "common pk defense",
    strength: "pk",
    role: "defense",
    attemptId: "spatial.pk.defense_attempts_per60",
    xgId: "spatial.pk.defense_xg_per60",
  },
] as const;
const distributionSlots = [
  ["i07", "finishing", "execution.5v5.finishing_goals_per100_attempts"],
  [
    "i08",
    "inferred setting",
    "execution.5v5.setting_goals_per100_assisted_opportunities",
  ],
  ["i09", "ordinary-minor drawing", "penalties.drawn_per60"],
  ["i10", "ordinary-minor taking", "penalties.taken_per60"],
] as const;

export const analyticalCardSlots: readonly {
  readonly section: string;
  readonly slotId: string;
  readonly metricId: AnalysisMetricId;
}[] = [
  ...mapSlots.flatMap((slot) =>
    [slot.attemptId, slot.xgId].map((metricId) => ({
      section: "spatial",
      slotId: slot.slotId,
      metricId,
    })),
  ),
  ...(["probability", "neutral_probability", "difference"] as const).map(
    (quantity) => ({
      section: "shootiness",
      slotId: "i06",
      metricId: `shootiness.5v5.${quantity}` as AnalysisMetricId,
    }),
  ),
  ...(
    [
      "finishing_goals_per100_attempts",
      "setting_goals_per100_assisted_opportunities",
      "avoid_block_probability",
      "on_net_probability",
      "recorded_stop_probability",
      "conversion_probability",
      "avoid_block_probability_difference",
      "on_net_probability_difference",
      "recorded_stop_probability_difference",
      "conversion_probability_difference",
    ] as const
  ).map((field, i) => ({
    section: "execution",
    slotId: i === 0 ? "i07" : i === 1 ? "i08" : "i22",
    metricId: `execution.5v5.${field}` as AnalysisMetricId,
  })),
  ...(
    [
      "drawn_per60",
      "taken_per60",
      "drawn_value_per60",
      "taken_value_per60",
    ] as const
  ).map((field) => ({
    section: "penalties",
    slotId: field.startsWith("drawn") ? "i09" : "i10",
    metricId: `penalties.${field}` as AnalysisMetricId,
  })),
  ...ledgerPresentation.flatMap(([, term], i) =>
    (["league", "replacement"] as const).map((reference) => ({
      section: "contributions",
      slotId: `i${i + 11}`,
      metricId: `ledger.${term}.${reference}_goals` as AnalysisMetricId,
    })),
  ),
  ...(["league", "replacement"] as const).map((reference) => ({
    section: "totals",
    slotId: "i21",
    metricId: `ledger.${reference}_total` as AnalysisMetricId,
  })),
  ...(
    [
      "ice_won_goals_per_basket",
      "ice_lost_goals_per_basket",
      "exit_offense.hazard_per_second",
      "entry_offense.hazard_per_second",
      "zone_retention.opponent_exit_hazard_per_second",
      "entry_prevention.opponent_entry_hazard_per_second",
      "exit_offense.one_second_probability",
      "entry_offense.one_second_probability",
      "zone_retention.one_second_probability",
      "entry_prevention.one_second_probability",
    ] as const
  ).map((field) => ({
    section: "territory",
    slotId: "i23",
    metricId: `territory.${field}` as AnalysisMetricId,
  })),
];

type CardField = {
  readonly section: string;
  readonly slotId: string;
  readonly row: AnalysisRow;
  readonly supportKeys: readonly string[];
};
type Distribution = {
  readonly slotId: string;
  readonly label: string;
  readonly row: AnalysisRow;
  readonly group: AnalysisPeerGroup;
  readonly domain: readonly [number, number] | null;
  readonly supportKeys: readonly string[];
};
export type AnalyticalCardModel = {
  readonly playerId: string;
  readonly person: Person | null;
  readonly historicalPerson: Person | null;
  readonly publication: Publication;
  readonly season: SeasonEvidence;
  readonly companion: string | null;
  readonly identity: readonly string[];
  readonly fields: readonly CardField[];
  readonly maps: readonly {
    readonly slotId: string;
    readonly label: string;
    readonly map: AnalyticalMapModel;
    readonly attempt: CardField;
    readonly xg: CardField;
    readonly supportKey: string | null;
    readonly stateWeights: (typeof SkaterSpatial.Type)["state_weights"];
  }[];
  readonly shootiness: readonly CardField[];
  readonly distributions: readonly Distribution[];
  readonly ledger: readonly {
    readonly term: string;
    readonly label: string;
    readonly field: CardField;
    readonly replacement: CardField;
  }[];
  readonly total: CardField;
  readonly replacement: CardField;
  readonly supports: readonly {
    readonly key: string;
    readonly population: string;
    readonly support: Support;
  }[];
  readonly methods: readonly {
    readonly key: string;
    readonly id: string;
    readonly reference: string;
  }[];
  readonly findings: readonly string[];
};

const disposition = ({ datum }: AnalysisRow) =>
  datum.value !== null
    ? valueText(datum)
    : datum.status === "absent"
      ? "absent season"
      : datum.status === "not_computed" ||
          datum.original?.unavailable_reason === "not_computed"
        ? "pending computation"
        : (datum.reason?.replaceAll("_", " ") ?? "unavailable");
const name = (model: AnalyticalCardModel) =>
  model.person
    ? playerName(model.person)
    : model.historicalPerson
      ? `${playerName(model.historicalPerson)} · historical identity`
      : `player ${model.playerId}`;
const supportText = (entry: AnalyticalCardModel["supports"][number]) =>
  `${entry.key} · ${entry.population} · included/excluded min ${entry.support.included_seconds === null ? "unknown" : displayNumber(entry.support.included_seconds / 60)}/${entry.support.known_excluded_seconds === null ? "unknown" : displayNumber(entry.support.known_excluded_seconds / 60)} · ${entry.support.prior_only ? "prior-only / hypothetical" : entry.support.current_season_information ? "some current focal information" : "no current focal information"}${entry.support.unquantified_gap ? "; unquantified gaps" : ""}`;

function supportPopulation(metric: AnalysisMetricId): string {
  const [family, strength, field] = metric.split(".");
  if (family === "spatial") return `${strength} spatial`;
  if (family === "shootiness") return "shootiness";
  if (family === "penalties") return "ordinary-minor penalties";
  if (family === "territory") return "inferred territory";
  if (family === "execution" && field === "finishing_goals_per100_attempts")
    return "finishing";
  if (
    family === "execution" &&
    field === "setting_goals_per100_assisted_opportunities"
  )
    return "inferred setting";
  throw new Error(`no analytical-sheet support population for ${metric}`);
}
const cautions = [
  "calibrated player uncertainty is unknown; empirical population spread is not uncertainty.",
  "reference execution: virtual neutral shooter, inferred setter and goalie. complete maps insert one focal player, not actual deployment.",
  "workload: 1,000 5v5 / 100 pp / 100 pk min. pp/pk use league-time mixtures; specialty time may be hypothetical or prior-only.",
  "attempt integrals differ from xg insets. positive against is more against; positive taking contrasts are more penalties.",
  "10ft pooling and contours do not establish fine-scale reliability. aggregate support need not inform every head.",
];

export function prepareAnalyticalCards(
  profiles: readonly ProfileView[],
  settings: PeerSettings,
  maps: readonly MapsResponse[],
): readonly AnalyticalCardModel[] {
  if (!profiles.length || profiles.length > 2)
    throw new Error("analytical cards require one or two selected skaters");
  const selected = profiles.map((profile) => {
    const year = profile.detail.history.find(
      (row) => row.season.season === profile.season.season,
    );
    const overview = profile.overviewCohorts.find(
      (row) => row.season.season === profile.season.season,
    );
    if (!year || !overview)
      throw new Error(
        "analytical card requires the selected annual identity and overview",
      );
    return { profile, year, overview };
  });
  const prepared = selected.map(({ profile, year, overview }) =>
    analyticalCardSlots.map((slot) => {
      const metric = analysisMetric(slot.metricId);
      if (!metric)
        throw new Error(
          `analytical card selector is missing: ${slot.metricId}`,
        );
      const datum = selectHistoryValue(
        year,
        overview,
        metric,
        profile.player_id,
      );
      return {
        ...slot,
        row: {
          datum,
          standing:
            metric.standingPolicy === "raw_only"
              ? rawOnlyStanding
              : {
                  kind: "unavailable",
                  reason: "card scalar; percentile not requested",
                  n: null,
                  peerGroup: null,
                  cutoffMinutes: null,
                },
          member: null,
          incompatiblePeerCount: null,
        } satisfies AnalysisRow,
      };
    }),
  );
  const distributions = distributionSlots.map(([slotId, label, metricId]) => {
    const metric = analysisMetric(metricId)!;
    const datums = prepared.map(
      (fields) =>
        fields.find((field) => field.metricId === metricId)!.row.datum,
    );
    const cohort = buildAnalysisCohort(
      selectLeagueValues(selected[0].overview, metric),
      datums,
      settings,
    );
    const values = cohort.groups
      .flatMap((group) => [
        ...group.members,
        ...group.selected.map((row) => row.datum),
      ])
      .map((datum) => displayValue(datum))
      .filter(
        (value): value is number => value !== null && Number.isFinite(value),
      );
    const domain = values.length ? plotDomain([0, ...values]) : null;
    return { slotId, label, metricId, cohort, domain };
  });
  return selected.map(({ profile, year, overview }, index) => {
    const supports: { key: string; population: string; support: Support }[] =
      [];
    const supportKeys = new Map<string, string>();
    const supportKey = (support: Support, metric: AnalysisMetricId) => {
      const population = supportPopulation(metric);
      const identity = JSON.stringify([population, support]);
      let key = supportKeys.get(identity);
      if (!key) {
        key = `s${supports.length + 1}`;
        supports.push({ key, population, support });
        supportKeys.set(identity, key);
      }
      return key;
    };
    const fields: CardField[] = prepared[index].map(
      ({ section, slotId, row, metricId }) => {
        const distribution = distributions.find(
          (distribution) => distribution.metricId === metricId,
        );
        const group = distribution?.cohort.groups.find((group) =>
          group.selected.some(
            (row) => row.datum.playerId === profile.player_id,
          ),
        );
        const rankedRow: AnalysisRow = group
          ? {
              ...row,
              standing: group.selected.find(
                (row) => row.datum.playerId === profile.player_id,
              )!.standing,
              member: group.members.some(
                (member) => member.playerId === profile.player_id,
              ),
              incompatiblePeerCount: group.incompatiblePeerCount,
            }
          : row;
        return {
          section,
          slotId,
          row: rankedRow,
          supportKeys:
            slotId === "i22" || slotId === "i23"
              ? []
              : [
                  ...new Set([
                    ...(row.datum.support
                      ? [supportKey(row.datum.support, metricId)]
                      : []),
                    ...Object.entries(row.datum.componentSupport).flatMap(
                      ([term, entry]) => {
                        if (!entry.support) return [];
                        const component = ledgerPresentation.find(
                          ([, name]) => name === term,
                        );
                        if (!component)
                          throw new Error(
                            `unknown analytical ledger support ${term}`,
                          );
                        return [supportKey(entry.support, component[2])];
                      },
                    ),
                  ]),
                ],
        };
      },
    );
    const field = (metricId: AnalysisMetricId) =>
      fields.find((field) => field.row.datum.metric.id === metricId)!;
    const core = mapSlots.map((slot) => {
      const response = maps.find(
        (response) =>
          response.family !== "observed" &&
          response.family !== "goalie_evidence" &&
          response.family === `${slot.role}_attempts` &&
          response.selection.strength === slot.strength &&
          response.selection.view === "effect",
      );
      if (!response)
        throw new Error(`analytical card is missing ${slot.label} attempt map`);
      const map = prepareAnalyticalMap(response, profile.player_id);
      const summary =
        !("availability" in year.families) &&
        year.families.kind === "skater" &&
        year.families.spatial.availability === "provided"
          ? year.families.spatial.data.find(
              (row) => row.strength === slot.strength,
            )?.result
          : null;
      return {
        slotId: slot.slotId,
        label: slot.label,
        map,
        attempt: field(slot.attemptId),
        xg: field(slot.xgId),
        supportKey: map.support
          ? supportKey(map.support, slot.attemptId)
          : null,
        stateWeights:
          summary?.availability === "provided"
            ? summary.data.state_weights
            : [],
      };
    });
    if (
      core[0].map.maximum !== core[2].map.maximum ||
      core[1].map.maximum !== core[3].map.maximum
    )
      throw new Error("corresponding analytical map scales disagree");
    const visibleFields = fields.filter(
      (field) => field.slotId !== "i22" && field.slotId !== "i23",
    );
    const constructionFields = ledgerPresentation.flatMap(([, term, detail]) =>
      field(`ledger.${term}.league_goals`).row.datum.value === null
        ? []
        : [field(detail)],
    );
    const methodFields = [...visibleFields, ...constructionFields];
    const methods = [
      ...new Map(
        methodFields
          .flatMap((field) => field.row.datum.methods)
          .map((method) => [method.method_id, method]),
      ).values(),
    ];
    const usage = overview.players.find(
      (row) => row.person.player_id === profile.player_id,
    )?.result;
    const reported =
      usage?.availability === "provided" ? usage.data.reported_usage : null;
    const identity = year.person
      ? [
          `${year.person.reported_position ?? "position unavailable"} · ${year.person.teams.map(teamName).join(" / ") || "teams unavailable"} · age ${displayNumber(year.person.age_years)} as of ${year.person.age_as_of}`,
          reported?.availability === "provided"
            ? `${reported.data.positive_toi_appearances} positive-toi appearances · ${displayNumber(reported.data.minutes_per_appearance.value)} reported min/appearance`
            : `reported workload: ${reported?.explanation ?? "unavailable"}`,
        ]
      : [
          "absent selected season; no values or identity borrowed from another year",
        ];
    return {
      playerId: profile.player_id,
      person: year.person,
      historicalPerson:
        profile.detail.history
          .toSorted((a, b) => a.season.season.localeCompare(b.season.season))
          .findLast((row) => row.person !== null)?.person ?? null,
      publication: profile.publication,
      season: profile.season,
      companion: profiles.length === 2 ? profiles[1 - index].player_id : null,
      identity,
      fields,
      maps: core,
      shootiness: [
        field("shootiness.5v5.probability"),
        field("shootiness.5v5.neutral_probability"),
        field("shootiness.5v5.difference"),
      ],
      distributions: distributions.map((distribution) => {
        const group = distribution.cohort.groups.find((group) =>
          group.selected.some(
            (row) => row.datum.playerId === profile.player_id,
          ),
        )!;
        const item = field(distribution.metricId);
        return {
          slotId: distribution.slotId,
          label: distribution.label,
          row: item.row,
          group,
          domain: distribution.domain,
          supportKeys: item.supportKeys,
        };
      }),
      ledger: ledgerPresentation.map(([label, term]) => ({
        term,
        label,
        field: field(`ledger.${term}.league_goals`),
        replacement: field(`ledger.${term}.replacement_goals`),
      })),
      total: field("ledger.league_total"),
      replacement: field("ledger.replacement_total"),
      supports,
      methods: methods.map((method, i) => ({
        key: `m${i + 1}`,
        id: method.method_id,
        reference: method.reference_id,
      })),
      findings: [
        ...new Set(
          methodFields.flatMap((field) =>
            field.row.datum.findings.map((finding) => finding.summary),
          ),
        ),
      ],
    };
  });
}

function EmpiricalDistribution({
  distribution,
}: {
  readonly distribution: Distribution;
}) {
  const { row, group, domain } = distribution;
  const x = (value: number) =>
    8 + (84 * (value - domain![0])) / (domain![1] - domain![0]);
  return (
    <figure
      className="analytical-distribution"
      data-metric={row.datum.metric.id}
      data-domain-min={domain?.[0]}
      data-domain-max={domain?.[1]}
    >
      <figcaption>{distribution.label}</figcaption>
      <p>
        <strong>{disposition(row)}</strong> {row.datum.metric.displayUnit} ·{" "}
        {distribution.supportKeys.join("/")}
      </p>
      {domain ? (
        <>
          <svg
            viewBox="0 0 500 54"
            role="img"
            aria-label={`${distribution.label}; empirical qualified peers, zero reference and selected marker`}
          >
            <line x1="8%" x2="92%" y1="38" y2="38" stroke="#7d898a" />
            <line
              x1={`${x(0)}%`}
              x2={`${x(0)}%`}
              y1="3"
              y2="49"
              stroke="#5b6468"
              strokeDasharray="3 3"
            />
            {group.members.map((datum) => (
              <line
                key={datum.playerId}
                x1={`${x(displayValue(datum)!)}%`}
                x2={`${x(displayValue(datum)!)}%`}
                y1="14"
                y2="37"
                stroke="#93a8aa"
              />
            ))}
            {row.datum.value !== null && (
              <circle
                cx={`${x(displayValue(row.datum)!)}%`}
                cy="26"
                r="7"
                fill="#193f47"
                stroke="#fbfaf6"
                strokeWidth="2"
              />
            )}
          </svg>
          <p className="analytical-distribution-domain">
            {displayNumber(domain[0])} … 0 effect … {displayNumber(domain[1])}
          </p>
        </>
      ) : (
        <p>no eligible peers or selected estimate; no invented distribution</p>
      )}
      <p>
        {group.peerGroup} · n={group.members.length} ·{" "}
        {group.cutoffMinutes ?? "unknown"} matched min cutoff
        {group.members.length === 0
          ? " · empty cohort"
          : group.members.length === 1
            ? " · singleton cohort"
            : ""}
        {row.datum.value !== null && !row.member ? " · selected outsider" : ""}
      </p>
      <p>
        population spread is not uncertainty
        {distribution.slotId === "i10"
          ? "; more taking is not a favorable contribution"
          : ""}
        .
      </p>
    </figure>
  );
}

export default function AnalyticalCard({
  model,
  detailLink,
}: {
  readonly model: AnalyticalCardModel;
  readonly detailLink?: (id: AnalysisMetricId) => {
    readonly to: string;
    readonly state?: unknown;
  };
}) {
  const id = useId();
  const [status, setStatus] = useState("");
  const label = (text: string, metricId: AnalysisMetricId) =>
    detailLink ? <Link {...detailLink(metricId)}>{text}</Link> : text;
  const mapPair = (panels: AnalyticalCardModel["maps"]) => (
    <div className="analytical-map-pair">
      {panels.map((panel) => (
        <figure
          className="analytical-core-map"
          key={panel.slotId}
          data-map-slot={panel.slotId}
        >
          <figcaption>
            {label(panel.label, panel.attempt.row.datum.metric.id)} · attempt
            effect
          </figcaption>
          <div className="analytical-core-map-body">
            {panel.map.integral === null ? (
              <div className="analytical-map-missing">
                {panel.map.availability}: {panel.map.reason}
              </div>
            ) : (
              <AnalyticalMapDrawing model={panel.map} />
            )}
            <div className="analytical-map-inset">
              <p>
                attempt integral
                <br />
                <strong>{displayNumber(panel.map.integral)}</strong>{" "}
                {panel.map.unitLabel}
              </p>
              <p>
                xg difference
                <br />
                <strong>{disposition(panel.xg.row)}</strong> xg/60
              </p>
              <p>
                xg neutral{" "}
                {displayNumber(
                  panel.xg.row.datum.spatial_detail?.neutral.value ?? null,
                )}{" "}
                xg/60
              </p>
              <p>
                xg relative{" "}
                {displayNumber(
                  panel.xg.row.datum.spatial_detail?.relative_percent.value ??
                    null,
                )}
                %
              </p>
              <p>xg is not the attempt-map integral.</p>
              <p>{panel.supportKey ?? "support unavailable"}</p>
              {panel.stateWeights.length > 0 && (
                <p>
                  standardized weights:{" "}
                  {panel.stateWeights
                    .map(
                      (row) => `${row.strength} ${displayNumber(row.weight)}`,
                    )
                    .join("; ")}
                </p>
              )}
              <AnalyticalMapLegend model={panel.map} />
            </div>
          </div>
          <p>{panel.map.orientation}</p>
          <p>
            {panel.map.integral === null
              ? "map unavailable; no neutral estimate drawn"
              : panel.map.maximum === 0
                ? "neutral fill; zero scale"
                : `neutral band |density| < ${displayNumber(panel.map.maximum / 4)}; paired sign intensities`}
            {panel.map.direction === "defense" &&
              "; positive means more against"}
            .
          </p>
        </figure>
      ))}
    </div>
  );
  return (
    <section className="analytical-card" aria-labelledby={id}>
      <header>
        <p className="analytical-kicker">
          {model.publication.purpose === "fixture"
            ? "synthetic fixture · "
            : ""}
          analytical skater sheet
        </p>
        <h3 id={id}>{name(model)}</h3>
        <p>
          {seasonLabel(model.season.season)} · experimental adjusted estimates
        </p>
        {model.identity.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </header>
      {mapPair(model.maps.slice(0, 2))}
      <section className="analytical-skill-belt">
        <h4>5v5 shootiness and empirical skills</h4>
        <div className="analytical-shootiness">
          {model.shootiness.map((field, i) => (
            <p key={field.row.datum.metric.id}>
              {label(
                [
                  "shootiness",
                  "supplied neutral probability",
                  "difference from neutral",
                ][i],
                field.row.datum.metric.id,
              )}
              : <strong>{disposition(field.row)}</strong>{" "}
              {field.row.datum.metric.displayUnit} ·{" "}
              {field.supportKeys.join("/")}
            </p>
          ))}
        </div>
        <div className="analytical-distributions">
          {model.distributions.map((distribution) => (
            <EmpiricalDistribution
              key={distribution.slotId}
              distribution={distribution}
            />
          ))}
        </div>
      </section>
      <section className="analytical-accounting">
        <h4>ten supplied contributions and league total</h4>
        <p>
          1,000 5v5 / 100 pp / 100 pk minutes · favorable goals per common
          workload. connecting lines mean addition.
        </p>
        <div className="analytical-ledger">
          {model.ledger.map((term) => (
            <div
              className="analytical-ledger-term"
              data-ledger-term={term.term}
              key={term.term}
            >
              <span>{label(term.label, term.field.row.datum.metric.id)}</span>
              <strong>{disposition(term.field.row)}</strong>
              <span>
                {term.field.supportKeys.join("/") ||
                  "component support unavailable"}
              </span>
            </div>
          ))}
        </div>
        <div className="analytical-totals">
          <p>
            league-relative total{" "}
            <strong>{disposition(model.total.row)}</strong>
          </p>
          <p>
            replacement-relative total{" "}
            <strong>{disposition(model.replacement.row)}</strong>
          </p>
        </div>
        <p>
          supplied totals only; a missing component withholds its total.
          replacement component values remain in detail/csv.
        </p>
      </section>
      {mapPair(model.maps.slice(2))}
      <footer>
        <h4>construction, support and limitations</h4>
        {cautions.map((line) => (
          <p key={line}>{line}</p>
        ))}
        {model.supports.map((entry) => (
          <p key={entry.key}>{supportText(entry)}</p>
        ))}
        {model.methods.map((method) => (
          <p key={method.id}>
            {method.key}: {method.id}; reference {method.reference}
          </p>
        ))}
        {model.findings.map((finding) => (
          <p className="analytical-warning" key={finding}>
            {finding}
          </p>
        ))}
        <p>
          publication {model.publication.publication_id} ·{" "}
          {model.publication.purpose}
          {model.companion &&
            ` · shared comparison scales with player ${model.companion}`}
        </p>
      </footer>
      <div className="card-actions">
        <button
          type="button"
          onClick={async () => {
            const snapshot = model;
            try {
              const blob = await svgPng(analyticalCardSvg(snapshot));
              downloadBlob(
                blob,
                `hockey-stats-${snapshot.season.season}-${snapshot.playerId}-analytical${snapshot.companion ? `-with-${snapshot.companion}` : ""}.png`,
              );
              setStatus("analytical sheet png prepared");
            } catch {
              setStatus("analytical sheet export failed; retry the download");
            }
          }}
        >
          download analytical sheet png
        </button>
        <button
          type="button"
          onClick={() =>
            downloadBlob(
              new Blob([analyticalCardCsv(model)], {
                type: "text/csv;charset=utf-8",
              }),
              `hockey-stats-${model.season.season}-${model.playerId}-analytical.csv`,
            )
          }
        >
          download analytical card csv
        </button>
        <p role="status">{status}</p>
      </div>
    </section>
  );
}

export function analyticalCardCsv(model: AnalyticalCardModel): string {
  return csvText(
    ["section", "slot_id", ...analysisCsvHeaders],
    model.fields.map((field) => [
      field.section,
      field.slotId,
      ...analysisCsvRow(model.publication, model.season, field.row),
    ]),
  );
}

export function analyticalCardSvg(model: AnalyticalCardModel): string {
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
    const max = Math.max(1, Math.floor(width / (size * 0.56)));
    const lines: string[] = [];
    let line = "";
    for (const word of value.split(/\s+/)) {
      if (line && line.length + word.length + 1 > max) {
        lines.push(line);
        line = "";
      }
      if (word.length > max) {
        if (line) {
          lines.push(line);
          line = "";
        }
        for (let i = 0; i < word.length; i += max)
          lines.push(word.slice(i, i + max));
      } else line += `${line ? " " : ""}${word}`;
    }
    if (line) lines.push(line);
    lines.forEach((line, i) => text(line, x, y + i * (size + 5), size, extra));
    return lines.length * (size + 5);
  };
  let y = 40;
  text(
    `${model.publication.purpose === "fixture" ? "synthetic fixture · " : ""}analytical skater sheet`,
    44,
    y,
    20,
    'fill="#145a66" font-weight="700"',
  );
  y += 45;
  y += wrap(name(model), 44, y, 1112, 34, 'font-weight="700"');
  y += wrap(
    `${seasonLabel(model.season.season)} · experimental adjusted estimates`,
    44,
    y,
    1112,
    22,
  );
  for (const line of model.identity) y += wrap(line, 44, y, 1112);
  y += 12;
  const mapPair = (panels: AnalyticalCardModel["maps"]) => {
    const top = y;
    let bottom = top;
    panels.forEach((panel, column) => {
      const x = 44 + column * 570;
      parts.push(`<g data-map-slot="${panel.slotId}">`);
      text(`${panel.label} · attempt effect`, x, top, 22, 'font-weight="700"');
      if (panel.map.integral !== null)
        parts.push(
          `<svg x="${x}" y="${top + 20}" width="204" height="480">${analyticalMapDrawingSvg(panel.map, `map-${panel.slotId}`)}</svg>`,
        );
      else
        wrap(
          `${panel.map.availability}: ${panel.map.reason ?? "map unavailable"}`,
          x,
          top + 70,
          204,
          20,
        );
      let inset = top + 52;
      const lines = [
        `attempt integral: ${displayNumber(panel.map.integral)} ${panel.map.unitLabel}`,
        `xg difference: ${disposition(panel.xg.row)} xg/60`,
        `xg neutral: ${displayNumber(panel.xg.row.datum.spatial_detail?.neutral.value ?? null)} xg/60`,
        `xg relative: ${displayNumber(panel.xg.row.datum.spatial_detail?.relative_percent.value ?? null)}%`,
        `role time: ${panel.map.support?.included_seconds === null || !panel.map.support ? "unavailable" : `${displayNumber(panel.map.support.included_seconds / 60)} min`} · ${panel.supportKey ?? "no support"}`,
        `density: ${panel.map.densityLabel}`,
        `levels (3 sig figs): ${panel.map.levels.map((value) => Number(value.toPrecision(3))).join(" ")}`,
      ];
      for (const line of lines) inset += wrap(line, x + 234, inset, 306) + 10;
      panel.map.legend.forEach((level, i) =>
        parts.push(
          `<rect x="${x + 234 + (i * 306) / panel.map.legend.length}" y="${inset}" width="${306 / panel.map.legend.length}" height="18" fill="${level.fill}"/>`,
        ),
      );
      const legendHeight = wrap(
        panel.map.integral === null
          ? "map unavailable; no neutral estimate drawn"
          : panel.map.maximum === 0
            ? "all-zero scale: neutral fill"
            : `neutral: magnitude < ${Number((panel.map.maximum / 4).toPrecision(3))}; not zero`,
        x + 234,
        inset + 48,
        306,
        20,
      );
      const orientationY = Math.max(top + 528, inset + 48 + legendHeight + 12);
      const orientationHeight = wrap(
        panel.map.direction === "offense"
          ? "+x up / +y right; attack above"
          : "+x down / +y left; defended goal below; positive is more against",
        x,
        orientationY,
        540,
        20,
      );
      bottom = Math.max(bottom, orientationY + orientationHeight + 24);
      parts.push("</g>");
    });
    y = bottom;
  };
  mapPair(model.maps.slice(0, 2));
  text("5v5 shootiness", 44, y, 24, 'font-weight="700"');
  y += 32;
  const shootiness = model.shootiness
    .map(
      (field, i) =>
        `${["probability", "supplied neutral", "difference"][i]} ${disposition(field.row)} ${field.row.datum.metric.displayUnit}${field.supportKeys.length ? ` (${field.supportKeys.join("/")})` : ""}`,
    )
    .join(" · ");
  y += wrap(shootiness, 44, y, 1112) + 15;
  const distributionTop = y;
  let distributionBottom = y;
  model.distributions.forEach((distribution, i) => {
    const x = 44 + i * 284;
    const { row, group, domain } = distribution;
    wrap(distribution.label, x, distributionTop, 260, 22, 'font-weight="700"');
    wrap(
      `${disposition(row)} ${row.datum.metric.displayUnit} · ${distribution.supportKeys.join("/")}`,
      x,
      distributionTop + 58,
      260,
    );
    const toX = (value: number) =>
      x + 20 + (220 * (value - domain![0])) / (domain![1] - domain![0]);
    const rugY = distributionTop + 130;
    if (domain) {
      parts.push(
        `<path d="M${x + 20} ${rugY + 15}h220" stroke="#7d898a"/><path d="M${toX(0)} ${rugY - 20}v48" stroke="#59676d" stroke-dasharray="3 3"/>`,
      );
      for (const peer of group.members)
        parts.push(
          `<path d="M${toX(displayValue(peer)!)} ${rugY - 12}v27" stroke="#93a8aa"/>`,
        );
      if (row.datum.value !== null)
        parts.push(
          `<circle cx="${toX(displayValue(row.datum)!)}" cy="${rugY}" r="7" fill="#193f47" stroke="#fbfaf6" stroke-width="2"/>`,
        );
      text(displayNumber(domain[0]), x + 20, rugY + 48, 20);
      text("0 effect", toX(0), rugY + 73, 20, 'text-anchor="middle"');
      text(
        displayNumber(domain[1]),
        x + 240,
        rugY + 48,
        20,
        'text-anchor="end"',
      );
    } else
      wrap(
        "no eligible peers or selected estimate; no invented distribution",
        x,
        distributionTop + 130,
        260,
      );
    let contextY = rugY + 102;
    contextY += wrap(group.peerGroup, x, contextY, 260);
    contextY += wrap(
      `n=${group.members.length}; ≥${group.cutoffMinutes ?? "?"} min`,
      x,
      contextY,
      260,
    );
    if (row.datum.value !== null && !row.member)
      contextY += wrap("selected outsider", x, contextY, 260);
    distributionBottom = Math.max(distributionBottom, contextY + 18);
  });
  y = distributionBottom;
  text(
    "ten supplied league-relative contributions",
    44,
    y,
    24,
    'font-weight="700"',
  );
  y += 29;
  y += wrap(
    "1,000 5v5 / 100 pp / 100 pk min · favorable goals; lines mean addition, not causal arrows",
    44,
    y,
    1112,
  );
  const ledgerTop = y + 14,
    totalY = ledgerTop + 115;
  model.ledger.forEach((term, i) => {
    const column = i < 5 ? 0 : 1,
      row = i % 5,
      x = 44 + column * 756,
      top = ledgerTop + row * 55;
    parts.push(
      `<path d="M${column === 0 ? x + 338 : x - 12} ${top + 8}L${column === 0 ? 480 : 720} ${totalY}" fill="none" stroke="#bdc8c5"/>`,
    );
    text(term.label, x, top, 20, 'font-weight="600"');
    text(
      `${disposition(term.field.row)} · ${term.field.supportKeys.join("/") || "support unavailable"}`,
      x,
      top + 25,
      20,
    );
  });
  parts.push(
    `<rect x="466" y="${totalY - 43}" width="268" height="115" rx="5" fill="#e7ede5"/>`,
  );
  text(
    "league total",
    600,
    totalY - 14,
    21,
    'text-anchor="middle" font-weight="650"',
  );
  wrap(
    disposition(model.total.row),
    600,
    totalY + 16,
    230,
    22,
    'text-anchor="middle" font-weight="650"',
  );
  y = ledgerTop + 295;
  y +=
    wrap(
      `replacement-relative total: ${disposition(model.replacement.row)} favorable goals per common workload; full replacement component column in detail/csv`,
      44,
      y,
      1112,
    ) + 14;
  mapPair(model.maps.slice(2));
  text("construction, support and limitations", 44, y, 22, 'font-weight="700"');
  y += 30;
  for (const line of cautions) y += wrap(line, 44, y, 1112, 18) + 1;
  for (const panel of model.maps.filter(
    (panel) => panel.map.strength === "pp" || panel.map.strength === "pk",
  ))
    y +=
      wrap(
        `${panel.label} standardized league-time mixture: ${panel.stateWeights.length ? panel.stateWeights.map((row) => `${row.strength} ${displayNumber(row.weight)}`).join("; ") : "not supplied; component pending"}`,
        44,
        y,
        1112,
        18,
      ) + 1;
  for (const entry of model.supports)
    y += wrap(supportText(entry), 44, y, 1112, 18) + 1;
  for (const method of model.methods)
    y +=
      wrap(
        `${method.key}: ${method.id}; reference ${method.reference}`,
        44,
        y,
        1112,
        18,
      ) + 1;
  for (const finding of model.findings) y += wrap(finding, 44, y, 1112, 18) + 1;
  y +=
    wrap(
      `publication ${model.publication.publication_id} · ${model.publication.purpose}${model.companion ? `; shared scales with comparison player ${model.companion}` : ""}`,
      44,
      y,
      1112,
      18,
    ) + 18;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="${y}" viewBox="0 0 1200 ${y}" font-family="system-ui,sans-serif" fill="#242b2d" role="img" aria-label="${xml(`${name(model)} analytical skater sheet`)}"><title>${xml(`${name(model)} · ${seasonLabel(model.season.season)} · experimental adjusted estimates`)}</title><rect width="1200" height="${y}" fill="#fbfaf6"/>${parts.join("")}</svg>`;
}
