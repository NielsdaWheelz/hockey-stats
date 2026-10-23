# v1-15 — comparative card and discovery

full implementation handoff under [the application contract](experimental-application.md), [comparative field crosswalk](../product-inventory.md#comparative-skater--s01-and-public-player-card-guide) and merged [v1-14 mechanisms](v1-14-history-cohorts-exports.md). [the plan](../plan.md#proposed-pr-boundaries-and-dependencies) owns assignment. the user selected comparative cards and the value table as the new entry points; recorded results remain one click away. this specification assigns no implementation, acquisition, fitting or activation.

## outcome and boundary

extend the existing website with the complete compact comparative skater card: identity/usage, league-relative headline, replacement companion, ten tiles, two embedded histories and a faithful single-player png. discovery supplies finite family tables; the existing two-player comparison presents two complete cards and shared selected-field detail. every quantity comes from schema7, using the existing selectors, cohorts, history and exports.

all published skaters remain discoverable even without an observed 5v5 summary. unfinished families remain visible; there is no automatic observed substitute. use the existing routes and effect client. no new wire schema, endpoint, database, dependency, fitting, generic card/chart framework, service or persistent cache.

software acceptance can finish detached against attributed v1-13/14 fixtures while v1-01/02 run. actual comparative-card delivery still requires v1-03 factual/context outputs, v1-06 execution and v1-12 ledger with their upstream producers. weak science does not block a correctly transported experimental estimate; fixtures do not establish real card completion. preserve the live build, active/previous databases, listener, source captures and fits.

accepted costs: a denser card and wider tables, several annual scalar reads, explicit per-field support, and more visible pending estimates before producers finish. these buy the intended complete composition without another research prerequisite. estimates remain seasonal levels, not forecasts, private war/sG or causal effects. other card compositions, modeled maps, many-player scatters, new source feeds, public hosting and combined-pair pngs are outside this slice.

## owners and implementation boundaries

| boundary / files | responsibility |
|---|---|
| `app/src/web/analysis-values.ts`, `analysis-cohorts.ts` | existing typed selectors, per-field support and midpoint ranks; one finite observed-in-overview adapter, no new hockey arithmetic |
| `client.ts`, `explorer.ts`, `presentation.tsx`, `player-picker.tsx` | coherent reads, finite route state, identity-based discovery/search; preserve cancellation and publication checks |
| new `analysis-discovery.ts`, existing `routes/league.tsx` | explicit table presets/columns, filter/sort/export selection; no configurable column language |
| new `comparative-card.tsx`, existing `analysis-history.tsx` | fixed card view model, html/png composition, shared history points/segments; ledger detail stays here unless its rendering warrants one cohesive module |
| existing `routes/player.tsx`, `routes/compare.tsx`, `root.tsx`, `styles.css` | comparative/observed navigation, two-card comparison, existing distributions/evidence and responsive presentation |
| existing `export.ts` and history csv helpers | shared download plumbing and metadata serialization; each renderer owns its composition |
| `fixtures/publication-v1-15/README.md`, `docs/research/application-v1-15/verification.md` | only new small attributed cases, checked expectations and acceptance receipts |

implement data composition, discovery, card/history and integration/export as non-overlapping internal boundaries. give each a content designer; domain and systems reviewers independently inspect meaning and ownership. coordinate shared frontend files with subsequent card owners. no edits to numerical producers, shared wire types or publication storage are expected.

## fixed card contract

use the inspected [s01 composition](../research/visual-references/README.md#inspected-examples) as layout evidence, not as numerical evidence or application assets. preserve its hierarchy: identity and dominant headline, two rows of five tiles, two small history plots. use the existing paper/teal/slate typography and neutral percentile marks; do not acquire logos, headshots, salary or line-role labels.

header: selected annual `Person` name/id, position, all reported teams, supported age with `age_as_of`, season; `reported_usage` positive-toi appearances and reported minutes/appearance with coverage. show included observed 5v5 minutes separately. absent identity fields retain reasons; historical identity may identify an absent-season page only when labeled with its actual year. never manufacture a current record.

the following are exact existing `AnalysisMetricId` values, not new payload fields. `ledger.<term>.league_goals` is abbreviated below. the first five tiles form row one; the remaining five form row two.

| display | authoritative selector | meaning / qualification |
|---|---|---|
| headline | `ledger.league_total` | published favorable goals per common workload; magnitude and percentile; general observed on-ice 5v5 eligibility |
| replacement companion | `ledger.replacement_total` | same workload; magnitude alongside, explicit roster-depth reference |
| 5v5 offense | `ledger.five_on_five_offense.league_goals` | modeled favorable contribution; corresponding spatial support |
| 5v5 defense | `ledger.five_on_five_defense.league_goals` | modeled favorable contribution; corresponding spatial support |
| power play | `ledger.power_play_offense.league_goals` | modeled favorable contribution; pp support |
| penalty kill | `ledger.penalty_kill_defense.league_goals` | modeled favorable contribution; pk support |
| finishing | `ledger.finishing.league_goals` | full-workload contribution, not standalone per100 skill; general observed on-ice 5v5 eligibility |
| goals | `goals60` | recorded personal 5v5 goals/60; matching personal exposure |
| primary assists | `primaryAssists60` | recorded personal 5v5 primary assists/60; matching personal exposure |
| penalties | `ledger.penalties_combined.league_goals` | published drawn+taken contribution; shared modeled penalty support |
| opponent usage | `context.opponents.usage_minutes_per_appearance` | counterpart all-strength usage weighted by shared 5v5 time; focal coverage and known slot weight |
| teammate usage | `context.teammates.usage_minutes_per_appearance` | same construction for teammates; not shared minutes or teammate skill |

common workload is exactly 1,000 5v5, 100 pp and 100 pk minutes. every tile carries magnitude/unit, standing or its reason, construction and a route to its evidence/distribution. label modeled contributions, recorded rates and usage proxies distinctly. neutral percentile encoding means higher named value; defense and penalty signs already come from the ledger and are not inverted again. goals/a1 are neither projections nor the later descriptive ev fields.

reuse `AnalysisDatum`, `AnalysisRow`, `HistoryPoint` and `AnalysisStanding`. a card view model contains selected annual identity/usage, the fixed headline/companion/ten rows, two named history series sets, ledger detail and publication/settings. it is renderer input, not a second exchange schema. no browser summing partial components, deriving replacement, estimating uncertainty or inventing unavailable support.

all ten tiles stay present when pending. retain a usable magnitude when its percentile is withheld. `not_computed`, absent season, source/fit-unavailable and outside-cohort are distinct states. one unavailable tile never removes another tile's peers. original uncertainty/findings remain inspectable; unavailable uncertainty is not a zero-width interval.

ledger detail shows the publisher's ten signed terms in fixed order: 5v5 offense, 5v5 defense, pp offense, pk defense, finishing, setting, drawing, taking, ice won, ice lost; league/replacement columns and supplied totals. combined penalties is a grouping of two terms, never an eleventh addend. **ten visible tiles are not ten additive ledger terms.** link the standalone skill/strength selectors from this detail; do not substitute their per60/per100 units into the card. preserve each constituent's support, hypothetical specialty workload, prior-only state, reference/method and limitations. there is no aggregate ledger exposure or inferred aggregate prior-only flag.

## cohorts and embedded histories

reuse [v1-14's cohort and semantic rules](v1-14-history-cohorts-exports.md#cohort-calculation) unchanged: default annual F/D peers; unknown position stays unknown; general 300 and specialty 50 included minutes; exact midpoint ties on unrounded values; independent per-field eligibility. `peers=all`, `peerMin` and `specialtyMin` remain explicit adjustable viewing choices. display n/peer group and the applicable qualification per tile, with compact shared keys only where they are actually equal. a qualified headline does not certify specialty experience.

both embedded plots cover the three displayed years, oldest first, using that year's person, quantity and cohort:

- headline plot: `ledger.league_total` percentile;
- component plot: 5v5 offense, 5v5 defense and finishing **ledger** percentiles.

axes are fixed 0–100; selected year is marked; component lines have distinct labels, colors and dashes. raw annual magnitudes/units, n, cutoffs, support and gap reasons remain in an adjacent expandable table. no trailing-average claim, forecast, interpolated gap, fitted density or uncertainty band. preserve magnitude access for unranked years.

extract the currently private point/segment break preparation in `analysis-history.tsx` at this second consumer. both its existing single-field history and the card's one-/three-series plots use it. missing ranks break percentile lines; changed semantic definition/reference breaks both modes; an annual F↔D peer change breaks percentile continuity. a new annual method id alone does not. embedded plots stay fixed percentiles; the existing selected-field detail retains its independent `history=raw|percentile` control.

## discovery, routes and comparison

retain `/`, `/players/:id`, `/compare?a=&b=`. root defaults to the comparative/value table; skater profile and comparison default to comparative cards. named observed navigation preserves current facts, cards, maps, games, deployment and downloads. current goalie profile behavior remains unchanged; new goalie discovery/cards belong to v1-19. no alternate legacy route or silent fallback.

| route state | finite contract |
|---|---|
| root `table` | `overview` default; `observed,spatial,execution,shootiness,penalties,territory` |
| root `strength` | spatial: `5v5` default or `pp,pk`; execution/shootiness: `5v5` default or `5v4,5v3,4v3,4v5,3v5,3v4`; omitted for other tables |
| profile/comparison `view` | `comparative` default or `observed`; applies to skaters |
| existing `metric` | finite selected-detail id, includes its strength; default `ledger.league_total` for comparative skaters, existing `sog60` for observed; valid explicit selections persist |
| existing controls | preserve `season,q,position,team,min,sort,dir,peers,peerMin,specialtyMin,history,map` where applicable; map affects only observed map views |

`table/strength` choose root columns, not selected-detail semantics or cohorts. use current canonical-search rules for malformed/duplicate/unknown values. changing table/strength resets invalid sort to that table's default; valid unavailable fields remain selected. view/metric changes load what they require; peer settings/filter/sort/history scale remain local when inputs already cover them. links preserve relevant season/settings, league return state and comparison state; pending navigation cannot mix old data with new labels. no backward-compatibility alias layer.

discover and pick from schema7 overview `Person`, not `PlayerSummary`. generalize the existing name/search/team helpers only to the identity fields they need. do not synthesize an observed summary for an overview-only skater. search/name/position/team filters select visible rows; never change percentile cohorts. default discovery `min=0` includes missing/zero observed time; a positive minimum explicitly filters on available **included observed 5v5 time**, excluding unknowns with an explanatory count. this is separate from general/specialty peer cutoffs and never changes basis with the table. unknown position remains in all-skater discovery, not forwards by default.

fixed table presets; identity and included observed 5v5 time accompany every table. each analytical cell has raw magnitude/unit, standing/status and selected-field detail access; reported usage/counts/time do not acquire new percentiles.

| table | ordered quantity columns / default numeric sort |
|---|---|
| overview | reported appearances, reported minutes/appearance; league/replacement totals; the ten tiles above in card order / `ledger.league_total` descending |
| observed | existing included-game count, personal time and five rates, preserving on-ice/personal coverage / included on-ice time descending |
| spatial | valid roles only: 5v5 offense then defense, pp offense, pk defense; each role's attempts/60, xg/60 and two relative percentages / first valid role's xg/60 effect descending |
| execution | finishing, setting, avoid-block, on-net, recorded-stop, conversion probabilities, then their four published differences / finishing descending |
| shootiness | probability, difference / difference descending |
| penalties | drawn/60, taken/60, drawn value/60, taken value/60 / drawn value descending |
| territory | exit offense, entry offense, zone retention, entry prevention one-second probabilities; ice won/lost goals per basket / ice won descending |

the five unranked columns are fixed, reuse existing sort ids where present, and are not added to `AnalysisMetricId`. paths below begin inside the provided overview's `reported_usage` or `observed` data; unresolved envelopes retain their actual reasons.

| column/sort id | authoritative value / native unit | placement |
|---|---|---|
| `minutes` | `observed.metrics.included_seconds` / seconds, displayed as minutes | every table |
| `reportedAppearances` | `reported_usage.positive_toi_appearances` / appearances | overview |
| `reportedMinutes` | `reported_usage.minutes_per_appearance.value` / minutes per appearance | overview |
| `games` | `observed.games_with_included_time` / games | observed |
| `personalMinutes` | `observed.personal.included_seconds` / seconds, displayed as minutes | observed |

ranked column/sort ids are the exact existing metric ids. `name` remains the identity sort. use the field sets already enumerated in `analysis-values.ts`; execution/shootiness use exact strengths, not aggregate pp/pk. descriptive/microstat/goalie table expansion belongs to v1-16/17/19. sort unrounded raw values, missing last in both directions, deterministic name/id ties. mixed F/D percentiles are never a universal rank column.

if the active numeric sort column has incompatible meanings, group by that column's `semanticKey` and sort within each group, missing values last. group order is deterministic by semantic key, unknown meaning last; label each group with its differing reference/definition. name sorting needs no semantic grouping. unranked columns use their fixed definition plus the owning source's construction/population/definition, or the applicable observed publication population version. ordinary annual provenance changes do not create groups. filters select rows after identifying these groups; they do not redefine the peer reference. wide tables may scroll horizontally; no paging/virtualization/new table library absent a demonstrated need.

the existing comparison picker accepts any selected-season published skater. invalid, duplicate and absent selections keep explicit errors; direct profile links can retain an absent current year and its actual historical rows. two comparative cards align side by side when readable and stack when narrow. reuse selected-field distributions/raw detail with each player's actual peer group and semantic identity; incompatible meanings stay separate. comparison settings apply to both; neither player substitutes the other's position/support. observed mode retains an overview-only skater's unavailable observed card/map side while the other remains usable; the existing map api already represents missing data as `data:null`. each card has its own png; existing plotted-values csv remains. no pair total, inferred winner or automatic quality verdict.

## read and composition contract

reuse existing `GET /api/league` and player detail endpoints, their typed envelopes/catalogs and `client.ts` request checks. no browser reads from raw files or fit artifacts.

1. a root table reads selected-season skater overview for identities/common fields; most presets use that one response. non-5v5 execution/shootiness additionally read their exact family/strength. left-join on published person id; verify agreeing identities, preserve missing family states, reject contradictory rows. observed values may be selected directly from overview's existing observed envelope.
2. comparative profile reads one player detail plus the three annual skater overview cohorts. comparison shares those three cohorts between two player details. one request per exact `(season,kind,family,strength)` per loader, never per tile/player. selected-field detail adds only its own family history/cohort requests when not already supplied; no speculative reads for all 197 fields.
3. the finite overview adapter in `analysis-values.ts` permits the existing five observed/5v5 selectors against the actual skater overview envelope. reuse their exact accessor, support and publication-population semantic keys. keep actual response identity and all other family/strength checks strict. independently prove parity against observed endpoint rows; overview-only identities yield explicit unavailable observed data, not invented counterparts. this small adapter avoids a redundant request without another rate implementation.
4. compose by publication identity/purpose/displayed seasons and each year's own `SeasonEvidence`/corpus. provided annual person, scalar, status/support and provenance must agree between detail/cohort where represented. absence and pending are legitimate states; inconsistent provided records/catalog ids are errors. retain `samePublication`, `sameRelease`, catalog-conflict handling and cancellation. never combine a stale response after navigation/restart.
5. observed view retains its existing evidence/map requests. comparative mode needs no map request; selected scalar histories do not fetch map/event arrays. preserve current goalie loading. request-local reuse suffices; no cache, polling or release manager.

the comparative renderer consumes a prepared fixed model of these values, standings and histories. html, png, table cells and detail share selectors/formatting. extracting history segments and identity helpers is required reuse; copying rank, source support or download arithmetic is not.

## content and export acceptance

| feature / content owner | what good means |
|---|---|
| compact card designer | recognizable single comparative composition; legible identity/headline/ten tiles/two histories; quantity class, scale, season and workload survive saving |
| discovery designer | explicit family/strength and units; all identities reachable; raw sort direction, empty/pending states and filters understandable; support is field-specific |
| history designer | annual populations and gaps visible; no invented continuity; all original values/reasons accessible; small plots remain legible in the complete card |
| ledger/evidence designer | every term/reference inspectable; total is not the tile sum; experimental construction, support and scientific limitations are separate |

prominent experimental status and a separate synthetic-fixture banner suffice; do not repeat a warning paragraph beneath every cell. every png includes identity/year, numerical reference, exact workload, raw magnitudes/units, annual peer settings/n and reasons for each of the four history series, key coverage/prior-only limitations, publication/method identity and experimental/fixture meaning. use compact keys and an expanding footer; never one false card-wide denominator or cohort n.

deliver a complete single-player comparative png, including both histories, through existing `svgPng`/`downloadBlob`. use 1200px width and content-driven height; long identity/limitations wrap, never truncate. local typography/assets only. reuse the card view model and shared plot preparation, with renderer-owned svg geometry; no html screenshot service or new image library. existing observed/history pngs remain working. snapshot player, season, settings, publication and values once per click; navigation cannot relabel an in-flight download. errors leave browsing usable and retry available.

add visible-table csv using existing `analysisCsvHeaders`/`analysisCsvRow` and `downloadCsv`: long form, one row per visible player and displayed quantity, in exact table row then column order; identity is repeated, not a separate metric row. preserve the shared analysis columns and append fixed `table,strength,row_order,column_order,column_id,metadata_evidence` columns. for genuine metrics, reuse `analysisCsvRow`, `column_id=metric_id` and empty `metadata_evidence`.

the five unranked columns use one narrow fixed metadata-row encoder over the same headers: `metric_id` empty, `column_id` from the table above, exact native/display value/unit/status, actual person/publication/source/support, and empty ranking/qualification/method fields where inapplicable. never forge an `AnalysisMetric` to call the ranked serializer. `metadata_evidence` preserves reported usage's listed/supported/missing game counts, provenance and support, or the applicable original observed support and population version. an unavailable value has its envelope/field reason; factual zero is not absence. add no new percentile contract. shared csv serialization still owns quoting and textual formula escaping.

totals/units/uncertainty/support/provenance remain exact unrounded published values. filename names table, strength if any, season and publication. existing history/distribution csvs retain their meanings; this is the visible selection, not every hidden player or family.

## implementation and verification

1. **red / contract:** reuse [v1-13](../../fixtures/publication-v1-13/README.md) and [v1-14](../../fixtures/publication-v1-14/README.md); add only missing attributed cases/checked expectations. trace the exact card/preset fields, qualifiers and producer references. prepare one hand-checked complete three-year card and one intentionally partial card. existing five observed rates and exports are preservation controls.
2. **data/discovery green:** verify overview-only skater discovery/picker, pending families, unknown position/name/team, no observed time with `min=0`, positive display cutoff, invalid/duplicate comparison selections and absent-year profile. verify overview/observed parity, finite family/strength routing, null-last sorting/ties, semantic grouping and visible-table csv order. filters cannot change cohorts. count requests and reject mixed publication/year/catalog/contradictory provided values.
3. **card/history green:** independently reconcile every tile/headline/ledger row with the fixture. include signed defense/taking, distinct finishing per100 versus basket values, one unranked tile, qualified headline with prior-only specialty, zero/negative values, differing general/specialty cutoffs and F/D peers. check all three annual cohorts, missing middle year, changed position, same-policy new method id and actual semantic change. two-player cards share reads without sharing the wrong cohort. publisher checks own ledger closure; the browser cannot repair invalid data.
4. **render/export green:** inspect actual wide/narrow 320px and native 200% browser layouts, semantic controls/keyboard flow, scrollable tables, long labels, empty states and both complete/partial cards. read native saved png/csv; both embedded plots, all ten tiles and essential meanings must survive. verify export retry and navigation during rendering; existing observed/map/deployment/history flows, direct links/back/season changes and detached operation still work. report any dedicated accessibility/assistive-technology checks actually run; v1-14's waiver is historical, not evidence of verification here.
5. **refactor/review:** remove superseded observed-only identity coupling and duplicate presentation/download/history mechanisms; retain current observed mode as useful behavior. independent domain, systems and rendered-content reviewers clear findings. rerun only affected boundary checks and pinned typecheck/build in the isolated task worktree. no unrelated producer/schema migration or dependency upgrade.
6. **handoff:** delete temporary tests/controllers and test-only dependencies after final green; retain attributed fixtures/checked facts. receipt records code/input identities, field/table/card coverage, request counts/bytes, representative read/render/export costs, observed preservation, native output evidence and limitations. keep full-season map-capacity work with its owning integration. update the plan with actual status; no primary serving build, database rotation, activation or admission.

done here means complete comparative composition, discovery, comparison and exports work against the real typed API on checked fixtures, with no unexplained field/owner and exact observed preservation. the receipt separately records **software complete** versus **real card integration pending/complete**. real v1-03/06/12 outputs later close the same card/exports progressively; they do not trigger another wholesale frontend rewrite or speculative fitting campaign.
