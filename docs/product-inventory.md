# product capability inventory

reviewed 2026-09-29. this is the checklist behind the [roadmap](roadmap.md), bounded by the public hockeyviz/jfresh references and useful evolving-hockey comparisons. the user selected complete player analysis as the parity scope, including dedicated goalie cards; whole-site parity is excluded. public evidence cannot establish exhaustive subscriber-product parity or decide every field. the [brief](brief.md) remains authoritative.

**scope, amended 2026-10-22:** **core** = required in the complete private experimental destination, not automatically in v1; **candidate** = an unresolved definition/scope decision, not coverage closure; **optional** = explicitly excluded enrichment outside the public-data core. the v1 boundary below owns release scope. publicly documented player-analysis views inside the settled scope require implementation or an explicit disposition; unknown private formulas do not silently make their panels optional. core means implemented numerical capability and its views, not scientific certification. a synthetic panel or unavailable placeholder is not an implemented component. documented inaccessible evidence may limit reference parity without blocking an honest v1. [plan](plan.md) owns status and assignment.

05a–05h establish the observed foundation: table/search, profiles, personal/on-ice/game evidence, comparison, raw-rate distributions/percentiles, png, spatial views, three-season history and deployment. their narrower slice exclusions do not constrain the new experimental program. keep those facts and their coverage intact while extending the same publication/application. [program boundaries](specs/experimental-player-analysis.md)

[the implementation specification](specs/experimental-player-analysis.md) maps the initial core to explicit source/model/application owners, with [numerical value accounting](specs/experimental-attribution.md), [chance/goalie contracts](specs/experimental-chance.md) and [view/schema contracts](specs/experimental-application.md). implementing the first 5v5 path does not close the remaining families. the expanded visual requirement now includes resolving goalie start/consistency and aggregate-value presentations. their numerical definitions remain open; neither an invented formula nor the existing schema completes them.

## completeness and delivery evidence — 2026-10-22

product completeness has two checklists: this component/view inventory and the retained [input/feature repertoire](model-features.md). the latter includes required inactive alternatives; having real headline numbers does not establish input completeness. conversely, preparing inputs does not complete a component or its interface. the [coverage issue](issues/experimental-repertoire-coverage.md) owns unresolved contracts. candidate labels below are unresolved choices, not evidence that every documented public feature has been covered; the crosswalk must give them a concrete definition or explicit scope disposition.

the following is the specified delivery mapping, not an implementation receipt. every core row needs actual producer output, checked publication/api transport and representative rendered content; synthetic examples and unavailable placeholders do not close it. shared card/table/comparison/history/export owners consume the same published quantities, with units, reference, support and experimental meaning intact.

| component family | specified publication records | required experience |
|---|---|---|
| chance, finishing and setting | `attempt_fact`, `skater_execution`, `execution_breakdown`, `analysis_map` | personal-shot evidence, conditional stages, type/danger detail, finishing/setting maps, cards and history |
| spatial offense/defense, pp/pk | `skater_spatial`, `analysis_map` | attempt/xgf/xga magnitudes and maps at declared strengths, specialist tables, comparisons and history |
| shootiness | `skater_shootiness` | taking-shot tendency and its execution/accounting explanation; no extra additive contribution |
| penalties | `skater_penalties`, `value_ledger` | recorded infractions beside modeled drawn/taken effects and their common-workload value; ordinary-minor baseline scope visible |
| territory | `skater_territory`, `analysis_map`, `value_ledger` | four transition subskills, ice won/lost maps and value; inferred movement labeled |
| common value | `value_ledger` | ten-component card/table/history, league and depth-replacement references, magnitude and percentile; not exact private synthetic-goals/war replication |
| goalies | `goalie_result`, `goalie_observed`, `execution_breakdown`, `analysis_map` | stopping, observed/expected results, outcomes, spatial/type/danger detail, workload, cards and history |
| context and evidence | `adjustment_decomposition`, finalized interval/attempt facts | coaching/other-context explanations, on/off and with/without results, deployment and source coverage |

## v1 card completion boundary — 2026-10-22

the user clarified that v1 requires the full hockeyviz player-card experience and both jfresh skater-card formats, not the entire catalogue below. this is a release boundary within the same program, not a return to a 5v5-only preview. the [supplied samples](research/visual-references/README.md) establish visual targets; the source/reference crosswalk establishes meanings.

| v1 requirement | completion evidence / boundary |
|---|---|
| complete hockeyviz-style skater cards | isolated and descriptive compositions with every documented card section: 5v5 offense/defense, pp offense, pk defense, finishing, setting, penalties drawn/taken, ice won/lost, shootiness, transition/execution subskills, coherent total, xgf/xga and corresponding maps, distributions and contextual evidence. use our declared seasonal estimands; independently constructed common value is not private sG or war |
| hockeyviz-style goalie cards | stopping, results, isolated outcome subskills, maps/type/danger, workload and the history belonging to the card; dedicated goalies remain selected. reconcile the actual reference fields before implementation; jfresh-specific start/consistency extras are later |
| jfresh-style comparative card | s01's compact hierarchy, component/context percentile tiles, underlying magnitudes, headline and embedded value/component histories. retain league/replacement references and three displayed seasons; no projected-war or salary claim |
| jfresh-style microstat card | s02's grouped shooting, passing, transition and other-action format, populated with every supported field. twenty example fields have a [source/definition checklist](research/visual-references/README.md#microstat-field-coverage). unavailable observations retain explicit reasons; independently inferred counterparts are named separately |
| usable surrounding product | retain and extend existing discovery, metric tables, profile/comparison, peer distributions, season navigation, evidence and card png around those outputs. component detail needed to understand a card belongs in v1; no separate dashboard |

release mapping: v01–v03, the card sections of v04–v09, v14's hockeyviz card, embedded v16 histories, existing v17–v19 workflows extended to card quantities, and v21 are v1. v11/v12 provide the already-selected explanation and replacement summaries needed by those cards. full standalone context/reciprocal-wowy, replacement and spider views (v10–v13), jfresh-specific goalie extras (v15 and any additional v14 aggregate), extended history/reference-band explorer (v16) and many-player scatters (v20) follow. existing observed functionality stays intact. a section shown on a required reference card cannot be deferred merely because its broader family also has later standalone views.

each v1 field needs a line in its content/source crosswalk: reference, exact independent meaning, source or inference, producer/payload, display/export and status. preserve every computable required component even when scientifically weak. distinguish unavailable evidence from missing implementation, and publish the remaining source limitations; an unavailable field does not establish exact reference parity. private formulas permit explicit independent estimators, not invented observations. neither paid tracking nor every speculative/alternative encoder is a v1 prerequisite. remaining input and visual work stays on the destination checklist.

### v1 field crosswalk and card acceptance

finish the field-level crosswalk here under the v1 card families, linking exact formulas/source definitions to their existing owners rather than duplicating them. each row records:

| field contract | required content |
|---|---|
| identity and scope | card/section/field, dated reference or supplied sample, v1/later disposition |
| meaning and evidence | our exact quantity; observed/derived/inferred/modeled meaning; source locator or explicit evidence limitation |
| population and scale | season/strength, eligibility/missingness, numerator and denominator/exposure, units/sign, reference and peer cohort |
| implementation and content | authoritative producer, concrete payload, card/detail/history/export use, responsible numerical/source and content owners |
| independent status and proof | definition/contract readiness, implementation, fixture check and real-output/browser/export evidence separately; source availability and scientific support are separate from those states |

the microstat crosswalk includes all twenty supplied fields even when an observation is unavailable; the sample review is its starting field list, not a completed derivation contract. finish the goalie/descriptive-card field audit as well. an unknown private formula can receive an explicit independent definition; an inaccessible observation cannot receive a fabricated proxy under the same name. resolve only consequential product ambiguities with the user; technical owners settle routine implementation choices.

acceptance units are complete card compositions: hockeyviz-style isolated skater, descriptive skater and goalie cards, plus jfresh-style comparative and microstat cards. each needs its supported real quantities, all required embedded maps/distributions/component diagrams/histories, relevant navigation/controls and faithful export. receipt links connect the field rows to actual rendered examples and checked values. fixture-only panels, a merged producer or disconnected working charts do not close a card. unavailable observations may remain labeled; failed calculations and unimplemented available fields cannot be relabeled source gaps. later standalone views do not hold completed cards open.

**dated exhaustiveness:** start from the 2026-10-22 reference inventory and supplied samples; record the dates and access limits of the remaining required-card audit. once its v1 crosswalk is settled, later unrelated discoveries enter the destination queue by default. missing already-promised card fields and correctness defects still update the affected contract; new v1 breadth needs an explicit scope decision. completeness claims cite that dated boundary, not all future competitor features or every possible transformation. [the plan](plan.md#v1-delivery-sequence) owns sequencing and assignments.

## visual coverage inventory — 2026-10-22

this is the current reference-to-view checklist, not a completed exhaustive interface audit. [reference evidence](research/player-card-references.md#visual-reference-sweep--2026-10-22) and [eight inspected user images](research/visual-references/README.md) own dated examples and inspection limits; [the visual issue](issues/experimental-visual-coverage.md) tracks missing contracts. ids below are documentation locators, not a runtime registry. add distinct panels discovered in the bounded sweep; an omitted view cannot be inferred from another row's broad family name.

every row needs a reference/example, analytical question, exact published quantities/population, chart/table form, controls, export, numerical/publication/frontend owners and separate contract/fixture/real-data/browser verification states. completion receipts link to actual code and rendered examples. rows are destination coverage items; the v1 mapping above determines what must ship first. missing definitions and later work stay open without becoming release gates for unrelated cards.

| id / reference family | question and presentation | controls / export | owners and current contract gap |
|---|---|---|---|
| v01 compact skater card; jfresh preview / s01 | component magnitudes, percentile tiles, headline/reference context and two embedded history plots | season, peers, reference; complete card png | card/cohort + ledger/history; baseline quantities exist, sample composition and field reconciliation remain open |
| v02 isolated skater summary; hockeyviz isolate / s07 | four rink maps, shootiness, paired skill distributions, component-value diagram and total in one analytical sheet | strength, reference, metric detail; complete card/map png | spatial/execution/value + card/rink; rate, relative-percent and workload-value meanings remain distinct |
| v03 descriptive card; hockeyviz skater guide | scoring and usage bars, appearances and observed context | season/strength; card png and table csv | observed + card; all required scoring/workload populations must be specified |
| v04 on/off results; hockeyviz skater guide and season page | for-versus-against scatter panels and with/without maps, league reference and included time | quantity, supported strength, population; plot/map png and csv | finalized evidence + context; current contract is 5v5 and lacks a recorded-goal context population; pp/pk and adjustment meanings need contracts |
| v05 deployment; hockeyviz skater guide | shift-start/score-state distributions, workload and teammate/opponent role groups | season/strength and reference; plot png and csv | preparation + deployment; elapsed summaries, role definitions and missing-start handling need explicit payloads |
| v06 spatial detail; hockeyviz isolate/season / s04/s08 | rink-clipped contours, density legend, physical axes and matching exposure/value/rate inset; distinct on-ice and isolated maps | supported strength, quantity, baseline; map png | spatial/finalized evidence + rink; authoritative cell mass, area conversion, interpolation and shared-scale rules |
| v07 personal shots; hockeyviz season | recorded locations and shot-mix detail | outcome/type/strength, distinct blocked-contact layer; map png and evidence csv | source evidence + personal geography; existing contract preserves source-supported shots outside fitting support |
| v08 finishing/setting; hockeyviz career and type/danger links | observed/expected outcome comparisons, subskills and inferred setting | season/strength, type/danger; plot png and csv | execution + details; choose exact panels/scales from referenced examples |
| v09 penalties/territory; hockeyviz isolate | component distributions, recorded evidence, transition subskills and ice won/lost | season, metric/reference; plot/map png and csv | mechanisms + details; meanings and nonadditive subskills stay explicit |
| v10 with/without; hockeyviz wowy/season | together and both players' apart rates in linked scatter/table views, with matched maps | counterpart/group and minimum shared exposure; plot/map png and csv | interval facts + context; current focal/group sums do not define reciprocal counterpart-away populations |
| v11 adjustment explanation; hockeyviz career breakdown links | baseline, self and contextual contributions to the displayed result | target/strength; plot png and csv | attribution decomposition + details; reuse declared nonlinear accounting, never call unexplained residue luck |
| v12 replacement; hockeyviz season | player versus explicit replacement reference, with magnitudes and reference composition | season/quantity/reference; plot png and csv | value + comparison; ledger exists; inspect the reference panel and define any further quantity/map before adding it |
| v13 spider/radar; hockeyviz season | multiaxis profile of declared comparable quantities | cohort/reference and player; plot png, values csv | cohort + comparison; pin axes/normalization and accessible values; polygon area is not total value |
| v14 goalie card/detail; jfresh goalie and hockeyviz goalie | stopping, observed/expected saving, type/danger, outcome subskills and workload | season/strength/stratum/peers; card/map/plot png and csv | goalie + card/details; baseline quantities exist in spec, aggregate headline needs an independent definition |
| v15 goalie start/consistency panels; jfresh goalie | game-quality frequencies and temporal variability | declared eligible games/seasons; plot png and csv | goalie evidence + details; thresholds, denominators, temporal meaning and eligible populations remain open |
| v16 analytical history; both career/card families / s01/s03 | embedded card histories first; later player trajectory over annual population bands with age/team strip | published season, quantity, method; embedded card/plot png and csv | annual summaries + history/cohort; explicit annual band construction, counts and gaps; population bands are not uncertainty; three seasons initially |
| v17 tables/workspace; public player profiles and project brief | searchable sortable descriptive/component tables with quantities, support and definitions | player kind, season, family, strength, peers; visible table csv | publication + explorer; reconcile exact public column/control coverage; no second metric calculation |
| v18 comparison/distributions; cards and project brief | raw-unit peer distributions, highlighted players and aligned component comparisons | same-kind players, metric, cohort/reference; plot png and csv | cohort + comparison; use identical quantity/reference rules and visible mixed-position cohorts |
| v19 appearances/game evidence; hockeyviz season | player game rows, workload and links to eligible evidence | published season; table csv | observed/goalie evidence + profile; no new whole-game report or event explorer implied |
| v20 many-player scatter; hockeyviz s05/s06 | labeled offense-versus-defense and finishing-versus-setting comparisons, zero reference and inspectable quadrants | season, strength, team, peers, fixed preset; plot png and values csv | published scalars/cohort + explorer; later view, explicit units/reference conversion and label-collision/omission rules |
| v21 microstat card; jfresh s02 | grouped shooting, passing, transition and other-action magnitudes/percentiles | season, peers, field detail; card png and values csv | source/numerical + card/publication; v1 supported fields, [missing input/meaning contracts](issues/microstat-inputs.md); no substitution of inferred setting for tracked passing |

cross-cutting completion includes discovery → profile → comparison → history/detail navigation, direct-link/back behavior, definitions, unavailable/partial/prior-dominated states, keyboard access, narrow/zoom layouts and faithful saved outputs. a reference control may require a new producer or api contract; assigning it to frontend does not make its quantities exist. record card metadata such as usage labels and headshots with its source/scope disposition. salary/cap remains explicitly unselected below; do not infer a new feed or silently reopen that boundary from its presence on a reference card.

inspect distinct analytical and visual forms, not every cosmetic revision or player. representative skater/goalie, season/career, thin-support and traded-player examples bound the audit. preserve the selected seasonal meaning and public-data constraints; differences from predictive private cards remain visible. real component output plus the full view/interaction contract closes a row; screenshots or a rendered synthetic card alone do not.

## analytical dependencies

| capability boundary | remaining experimental work / later evidence |
|---|---|
| chance measurement | compose conditional outcomes, origin inference and reference-standardized opportunity; inspect calibration and origin sensitivity without requiring prior admission to display experimental values |
| temporal structure | use explicit annual history, entry and age assumptions; preserve known persistence/change failures and assess revised choices through product consequences |
| spatial player contribution | reuse aligned stints, zero-event exposure and rate/history mechanisms; implement chance-valued responses, coherent complete rates and context explanations; recovery and calibrated uncertainty remain evidence questions |
| component breadth | actual setting, freeze/rebound, goalie, special-teams, penalty, shootiness and territorial estimators, with nonoverlapping accounting |
| player experience | extend observed owners with every core card/map/table/comparison/history/export family; label experimental outputs and expose their evidence |

historical scientific verdicts remain unchanged. [03p](research/chance-03p/decision.md) and [04n](research/attribution-04n/decision.md) supply useful starting mechanisms, not automatic artifact promotion or supported ability. the [feature inventory](model-features.md) separates prepared facts, encoders and fitted use. missing input preparation and explicit inference remain implementation work; every feature need not first win an isolated experiment.

public [xg8](https://hockeyviz.com/txt/xg8) supplies reference distinctions in outcome layers, symmetry/type geometry, tip treatment, setters, coaches and historical priors. precise current hockeyviz implementation remains unknown after its announced rewrite; the reference caveat below governs. available local proxies, unadmitted sources and unsupported physical tracking must remain distinct.

## skater components

the ten contribution rows below follow the public [isolated-impact guide](https://hockeyviz.com/howto/isolate). their meanings are reference descriptions, not adopted estimators. our temporal target remains underlying ability across the selected season.

| component | question | status |
|---|---|---|
| 5v5 offense | how does the player change spatial chance creation? | core |
| 5v5 defense | how does the player change spatial chance suppression? | core |
| power-play offense | how does the player improve chances with the extra skater? | core |
| penalty-kill defense | how does the player suppress chances while shorthanded? | core |
| finishing | how does conversion differ after accounting for supported shot context? | core |
| setting | what does the pass immediately before a shot contribute? | core |
| penalties drawn | how does the player affect the team's drawing of eligible penalties? | core |
| penalties taken | how does the player affect the team's taking of eligible penalties? | core |
| ice won | what offensive value does the player leave for subsequent shifts through territory? | core |
| ice lost | what defensive value does the player leave through territory? | core |

penalty effects attributed to on-ice players differ from personally recorded infractions and draws. keep those observations alongside, not interchangeable with, the modeled effects. [penalty methodology](https://hockeyviz.com/txt/magnus7P)

the following complete that component family without creating additional additive contributions:

| quantity | meaning / boundary | status |
|---|---|---|
| shootiness | modeled tendency to take the team's shot; effectiveness is a different question | core; [reference](https://hockeyviz.com/txt/shootiness) |
| four transition subskills | exit offense, entry offense, offensive-zone retention, defensive entry prevention; help explain ice won/lost | core; inferred puck movement is not tracked controlled entries/exits; [reference](https://hockeyviz.com/txt/bluelineTraversals) |
| finishing subskills | block avoidance, reaching the net, freeze outcome and conversion, conditional on earlier outcomes | core explanatory drill-down; define conditional targets and assess their limitations; do not add conditional probabilities; [reference](https://hockeyviz.com/txt/xg8) |
| common-value summary | combine defined experimental contributions under explicit accounting and a reference workload | core, conditional on valid composition; [synthetic-goals reference](https://hockeyviz.com/txt/sG) |

the core special-teams contract covers 5v4, 5v3 and 4v3 power-play offense and reciprocal penalty-kill defense, following the published scope. power-play defense, shorthanded offense and additional states are candidates; those missing directions are not silently implied by a “complete” card. [special-teams methodology](https://hockeyviz.com/txt/magnus9ST)

evolving hockey offers a useful alternative accounting comparison: even-strength offense/defense, power-play offense, shorthanded defense, penalties drawn/taken; grouped offense/defense/penalty value; goals, wins and standings points above replacement. these are not extra independent skills. synthetic goals, goals above replacement and wins above replacement require different references and conversions; the inventory does not select a second model family. [glossary](https://evolving-hockey.com/glossary/goals-above-replacement/)

## goalie family

goalie profiles are core experimental capability: stopping, evidence, spatial/type/danger detail, outcome subskills, workload and history. start-quality/consistency and aggregate-value presentations are required coverage items with open definitions under v14/v15, not optional forever. specify independent quantities/eligibility where private formulas are unknown; do not relabel seasonal estimates as projected war. scientific quality can remain provisional without deferring the whole family.

| group | reference quantities to consider | distinction to preserve |
|---|---|---|
| stopping | even-strength and penalty-kill ability; workload-adjusted comparison | our season-level ability target versus a forecast or observed season result |
| evidence | shots faced, saves, goals allowed, exposure, save percentage, expected save percentage, goals saved above expected | counts and save percentage versus model-derived expectation and residuals |
| shot context | stopping by danger tier and shot type; spatial saving maps | conditional results versus independently estimated repeatable skills |
| outcome subskills | effects on misses, freezing the puck, goals versus rebounds | freezing ends play; rebound behavior and subsequent rebound danger are separate questions |
| start patterns and stability | quality/excellent/bad starts; consistency | historical consistency describes between-season variation; start categories describe games; neither alone establishes a stable talent |
| workload and history | appearances, starts, minutes, share of team games, role; stopping and result trajectories | workload is context, not automatically quality |
| overall value | common-value or replacement-based summary, if justified | declare units, reference and rate versus accumulated contribution |

the current [jfresh goalie preview](https://hockeystats.com/cards/goalie-cards) visibly includes danger tiers, start categories, rebound control, consistency, workload, percentile history and save-percentage comparison. its headline is projected value. historical [2022 definitions](https://jfresh.substack.com/p/2022-nhl-player-cards-explainer) do not establish today's thresholds or regression rules.

hockeyviz's [goalie page](https://hockeyviz.com/player/helleco93) separates results, isolated subskills, type/danger breakdowns and history. its public [saving map](https://hockeyviz.com/fixedImg/savingTeamSingle/2526/WPG/helleco93) and [type panels](https://hockeyviz.com/fixedImg/savingTeam/2526/WPG/helleco93) compare observed goals with expected goals; they are not automatically adjusted goalie-ability maps. the [published subskill example](https://hockeyviz.com/static/txt/magnus/fabric/history-goalie_lundqhe82-8g.png) distinguishes misses, freezes and conversion outcomes. magnus 9 [removed goalie rebound terms](https://hockeyviz.com/txt/magnus9EV) from its even-strength shot-rate model: do not resurrect an obsolete term as a documented current skill.

## cards and supporting views

a card presents quantities; it is not a new statistical model. several rows can be sections of one profile rather than separate pages.

| family | contents / purpose | status |
|---|---|---|
| isolated skater summary | coherent offense/defense maps and scalar effects across the component family | core; experimental estimates with evidence, stronger claims assessed separately |
| compact comparative skater card | component magnitudes and percentiles, clear cohort, identity, evidence and context; readable download | core; extend the observed subset with experimental component magnitudes and explicit reference cohorts |
| descriptive skater card | scoring, usage and on/off results; distinguish experience from estimated ability | core; reuse personal/on-ice summaries and add declared usage/off-ice evidence |
| career and historical profiles | navigable season cards, maps, results, explanations and ability/subskill trajectories; common-value history where supported | core analytical history and trajectories on declared output seasons; corpus expansion remains separate |
| detailed 5v5 view | inspect spatial differences hidden by the summary | core; observed and modeled detail remain distinct |
| finishing/setting detail | results, estimated subskills, shot-type/danger breakdowns and history | core; exact panel composition and bins specified with the baseline models |
| goalie summary and detail | compact comparisons, stopping evidence, maps, subskills and history | core; v14/v15 include required presentations with unresolved numerical definitions |
| usage/context view | deployment distributions, teammates/opponents, role and workload | core; reuse shared minutes/time shares, add declared roles/workload and experimental context estimates |
| personal shot view | individual shot locations, rates and shot mix | core; [05i](specs/05i-personal-shot-views.md) is folded into the program. define event population, shot mix, rates and coverage; blocked contacts are not release locations |
| with/without view | together/apart results and maps, selected teammate/combination context, replacement comparisons | core; shared deployment prevents a causal-chemistry claim |
| adjustment explanation | relate observed on-ice results to isolated estimates through defined self/context terms and any defined residual | core; nonlinear effects need explicit composition, not invented additive attribution |
| tracking/microstat card | supported event facts, independently named expected quantities and available tracked/skating measurements | v1 card with explicit field-level gaps; paid/private tracking remains optional input enrichment |

public hockeyviz [career](https://hockeyviz.com/player/matthau97) and [season](https://hockeyviz.com/player/matthau97/TOR/2526) pages enumerate summary, detail, finishing, personal-shot and contextual panels. the [descriptive-card guide](https://hockeyviz.com/howto/skaterCard) and [with/without guide](https://hockeyviz.com/howto/wowy) explain distinct families. spider and replacement presentations have explicit coverage rows above; their route placement may vary, but omitting the distinct views requires an explicit scope decision.

the context family includes explicitly estimated teammate, opponent, coaching, score/deployment and other environmental contributions, with experimental limitations visible. [published model terms](https://hockeyviz.com/txt/magnus9EV) motivate those explanations; they do not guarantee a unique additive decomposition. a residual must retain its defined meaning rather than be relabeled luck. static published explanations can serve this purpose without an interactive refitter.

the [jfresh skater preview](https://hockeystats.com/cards/player-cards) supplies compact component comparison, context, history and download. evolving hockey's [official example](https://evolving-hockey.com/wp-content/uploads/2021/10/Player_card_2_ex-1536x1144.png), generated in 2021, pairs gar/xgar components with overall/group percentiles and deployment distributions. its [public card notes](https://evolving-hockey.com/stats/player_cards/) distinguish single-season totals from weighted three-season summaries. these preserve model and temporal distinctions; they do not establish current authenticated behavior or select another model for us.

## evidence and context checklist

these evidence/context families support the core product. choose purposeful concrete fields with the component/view specification; no need to display every source column. keep descriptive context distinct from a modeled skill.

- **identity:** name, team(s), position, age, handedness where supported; trades must not silently fragment season totals.
- **individual results:** goals, primary/secondary assists and points; attempts, unblocked attempts, shots on goal and shooting percentage; counts and exposure-normalized rates. exact selections need a purpose, not every available column.
- **on-ice results:** attempts and goals for/against, rates and shares, on-ice shooting/save percentages; xg for/against clearly model-derived. individual results and on-ice results answer different questions.
- **deployment:** games, total and per-game ice time, strength-state workload, positional role; shift starts on the fly versus faceoffs and by zone; time leading/tied/trailing.
- **environment:** teammate/opponent context, including forward/defense groups; observed with/without results, team and league references. personally drawn/taken penalties remain recorded evidence.

the hockeyviz [descriptive guide](https://hockeyviz.com/howto/skaterCard) motivates the scoring, usage and on/off groups. do not promote those contextual associations into player skills. jfresh's current [explanation](https://hockeystats.com/about/player-cards) describes projected scoring rates, weighted multi-season inputs, position-specific cohorts and workload-based context. our observed-results panels must not borrow those numbers' labels while changing their meaning.

## comparison and application capabilities

| capability | status / contract |
|---|---|
| league table, name search, sorting and player navigation | core; unavailable estimates remain distinguishable from poor ones |
| compact player comparison | core; same state, units, baseline and comparable evidence |
| complete-season summary and game evidence | core; observed aggregates reconcile; game rows are not fitted ability contributions |
| distribution with selected player, percentile and rank | 05c supplies observed raw-unit distributions; 05f supplies numeric percentile standing for five rates with exact family cohorts and tie rules. experimental component distributions use their own declared cohorts; retain magnitude and uncertainty limits |
| richer comparisons and history | core; same-method comparisons or explicit method differences; no arbitrary date-window fitting |
| readable downloadable cards | 05d supplies one descriptive png; 05f supplies compact comparative content, preserving identity, raw rates, both supports, coverage and explicit cohort/percentile meaning. experimental cards carry the model meaning and limitations; stronger claims need relevant evidence |
| specialist component tables | core; reuse selected quantities, not independent recalculation |
| descriptive statistics workspace and downloads | core; individual/on-ice/workload tables, season rows, game evidence and useful count/rate views; publish supported derived outputs |
| inspectable definitions and evidence limits | core, expanded with each component; units, sign, baseline, time meaning, provenance, uncertainty and missingness |

our rule: a population distribution shows variation among players; an uncertainty interval describes uncertainty about an estimate. neither substitutes for the other. a rank is not an effect size. actual accumulated contribution, per-exposure rates and standardized-workload value are different views of defined quantities, not new skills.

historical cards are an explicit [jfresh offering](https://hockeystats.com/cards/historic-player-cards). public [player profiles](https://hockeystats.com/players/jackson-lacombe) expose descriptive table families and controls; the [line tool](https://hockeystats.com/stats/line-tool) exposes combination selection, whose results were not exercised. our historical profiles require analytical outputs for those seasons, not retained old publications.

later recorded-result coverage includes playoffs and additional strength states, separated from the fitted regular-season population. retain team-specific evidence for traded players without fragmenting their season-level ability estimate. hockeyviz's [appearance lists](https://hockeyviz.com/player/mcdavco97/EDM/2425) also include preseason; that remains a candidate, not an implied preseason model. historical range and state coverage must be established from admitted evidence, never inferred from a season selector.

## microstat source coverage and optional enrichment

v1 requires the microstat card and every honestly constructible field, not access to unavailable private tracking. [the twenty-field sample crosswalk](research/visual-references/README.md#microstat-field-coverage) and [input issue](issues/microstat-inputs.md) own the immediate source work. retain this broader checklist without making paid tracking a dependency of the public-data core:

- shooting and chance involvement, including rush versus established-zone offense;
- passes leading to shots/chances, dangerous passes and pass-origin context;
- carried/passed/dumped entries and exits, retention and success;
- defensive entry denials, controlled-entry prevention and rush-chance suppression;
- forecheck pressure, recoveries, defensive retrievals and retrieval success;
- possession decisions, turnover risk and workload;
- hits and skating speed/bursts where their distinct sources support them.

the [microstat-card guide](https://hockeystats.com/about/microstat-player-cards) draws on all three zones tracking and nhl edge skating data. establish field definitions, access and seasonal coverage before selecting an input. supported public fields are not excluded merely because the original card also uses private tracking. inferred transitions and imputed setters do not become tracked observations because they fill similar card slots. source limitations may remain in v1; do not label the resulting card complete private-data parity.

## what this inventory does not commit us to

source capture, blocked-origin inference, chance-model stages, priors, aging and deployment adjustments support the estimates. they are not extra independent contributions to add to a card. statistical diagnostics belong to analytical work unless they answer a reader's concrete question. dated coach effects and age/history context are required model capabilities; standalone coach products are not.

team dashboards, standalone coach evaluations, prospects, fantasy, contract valuation, lineup simulators, game/playoff forecasts, accounts and payments are unselected neighboring products. salary/cap context and future-player forecasts are also unselected; appearing on a reference card does not make them essential here. arbitrary date-window fits remain excluded by the brief.

reference uncertainty is explicit: hockeyviz [announced rewritten models](https://hockeyviz.com/txt/preview2627) in september 2026 with methods forthcoming; public guides span different vintages. jfresh's current skater headline predicts future value, while our headline describes a selected season. [unresolved reference definitions](issues/card-reference-definitions.md) must be settled when their quantities become implementation targets. we can reproduce a capability using our own explicit, checked experimental definition without claiming numerical equivalence or mature scientific support.

the tradeoff is deliberate: specify coherent batches against the full experimental checklist, build them in parallel where possible, and use the resulting product to refine estimates. exact baseline formulas and layouts belong to the full program specification; scientifically weak output remains labeled rather than quietly replaced or certified. explicit optional boundaries remain; the approved visual amendment supersedes earlier candidate labels for in-scope required presentations. missing definitions stay open until specified or explicitly rescoped.
