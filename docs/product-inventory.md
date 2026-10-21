# product capability inventory

reviewed 2026-09-29. this is the checklist behind the [roadmap](roadmap.md), bounded by the public hockeyviz/jfresh references and useful evolving-hockey comparisons. the user selected complete player analysis as the parity scope, including dedicated goalie cards; whole-site parity is excluded. public evidence cannot establish exhaustive subscriber-product parity or decide every field. the [brief](brief.md) remains authoritative.

**status:** **first** = agreed first product; **later** = part of the agreed destination, implemented incrementally; **candidate** = reference detail worth considering, not yet selected; **optional** = enrichment outside the public-data core. a later family does not commit us to every competitor field or formula. nothing here expands the current slice or requires a universal card framework.

2026-10-16 amendment: [05a](specs/05a-observed-website.md) brings forward a private observed subset: league table/search, player identity, recorded 5v5 counts, matched reconstructed exposure/rates and reconciled game evidence with coverage. this does not promote the later descriptive-card family or fulfill the first analytical product. ability, xg, adjusted maps and comparisons remain outside that intermediate slice.

2026-10-17 amendment: [05b](specs/05b-observed-comparison.md) selects a separate two-player comparison of those existing observed quantities. reuse the same publication and api; no new metric, percentile cohort or ability claim. richer comparison/distribution/card capabilities below remain later.

2026-10-20 amendment: [05c's full player-explorer contract](specs/05c-player-explorer.md) adds table discovery, compact observed cards and raw-rate peer plots alongside 04l. the user chose reported forward/defense peers and an adjustable 300-included-minute default; table filtering remains separate. magnitude, included minutes and coverage stay visible; numeric percentiles and new facts are not bundled. [05d](specs/05d-descriptive-cards.md) records later richer descriptive/export work; [05e](specs/05e-spatial-views.md) records the separate spatial contract. these bring forward observed presentation capabilities without promoting unsupported skill components.

2026-10-21 amendment: [05d](specs/05d-descriptive-cards.md) specifies personal shots on goal, goals and primary assists, separate personal exposure/coverage, and a single-player png. existing on-ice distributions remain; new percentiles/personal distributions and usage enrichment remain later. [05e](specs/05e-spatial-views.md) next targets source-supported observed rink views independently of 04m. descriptive capabilities do not admit player ability.

2026-10-21 spatial contract: [05e](specs/05e-spatial-views.md) now specifies observed unblocked for/against maps on profiles/comparison, league differences plus absolute rates, fixed descriptive smoothing and inspectable raw evidence. its separate matched spatial support preserves existing populations; source locations are not verified releases. replacement valuation, personal-shot maps, adjusted effects and map downloads remain distinct later capabilities. this advances observed spatial explanation, not admitted skill or private-model parity.

2026-10-21 comparative-card contract: [05f](specs/05f-comparative-observed-cards.md) brings forward observed percentiles for the five existing rates, with raw magnitudes, separate personal/on-ice peer eligibility and one detail distribution. profile, comparison and one-player png share the same content. higher means higher recorded rate; outside-cohort selections retain raw values without percentile standing. this extends descriptive comparison without admitting an ability component.

2026-10-21 historical-observation contract: [05g](specs/05g-observed-history.md) specifies 2023–24 through 2025–26 across existing views, with a three-row raw-rate/minute/coverage history table and seasonal detail links. each year's identity, peers and spatial league reference remain distinct. history has no percentile or trajectory chart; absence is not zero. analytical history, longer careers, personal maps and deployment detail remain separate capabilities.

## analytical dependencies

the capability review, updated after 04b, separates available facts, implemented mechanisms and supported estimates. [the plan](plan.md) owns assignments/status and [the feature inventory](model-features.md) exact encoder use; these are dependencies of parity, not a mandatory bundle before the first useful profile.

| capability boundary | remaining work |
|---|---|
| chance measurement | supported recorded probabilities, block-origin/avoidance composition, tip sensitivity and reference-standardized opportunity; q × g alone supplies none of these admissions |
| temporal structure | 04a/04b implement five-season chronological age-neutral borrowing; useful recovery, justified aging/entrant priors, changeability and historical selection remain to assess |
| spatial player contribution | aligned stints, zero-event exposure, annual offense/defense and volume/shape mechanisms exist; useful recovery beyond trivial baselines, uncertainty, complete-rate adequacy and richer justified deployment adjustment remain |
| later skills | setting inference, validated freeze/rebound targets, dedicated goalie effects, special teams, penalties, shootiness, territory and nonoverlapping totals |
| player experience | 05a first delivers observed publication/table/search/profile/game evidence; supported ability maps/comparisons and later cards/history/distributions/downloads extend the same path |

attribution research can investigate recorded-rate associations and sensitivities before chance admission; [04c](research/attribution-04c/decision.md) records one completed recovery question. those provisional fitted outputs do not fulfill the promised chance-valued profile or belong in 05a's observed-only publication. a few useful components can justify a bounded predictive cost under a prospective claim-specific rule; identical private-model numbers remain outside acceptance.

public [xg8](https://hockeyviz.com/txt/xg8) supplies reference distinctions in outcome layers, symmetry/type geometry, tip treatment, setters, coaches and historical priors. precise current hockeyviz implementation remains unknown after its announced rewrite; the reference caveat below governs. available local proxies, unadmitted sources and unsupported physical tracking must remain distinct.

## skater components

the ten contribution rows below follow the public [isolated-impact guide](https://hockeyviz.com/howto/isolate). their meanings are reference descriptions, not adopted estimators. our temporal target remains underlying ability across the selected season.

| component | question | status |
|---|---|---|
| 5v5 offense | how does the player change spatial chance creation? | first |
| 5v5 defense | how does the player change spatial chance suppression? | first |
| power-play offense | how does the player improve chances with the extra skater? | later |
| penalty-kill defense | how does the player suppress chances while shorthanded? | later |
| finishing | how does conversion differ after accounting for supported shot context? | later |
| setting | what does the pass immediately before a shot contribute? | later |
| penalties drawn | how does the player affect the team's drawing of eligible penalties? | later |
| penalties taken | how does the player affect the team's taking of eligible penalties? | later |
| ice won | what offensive value does the player leave for subsequent shifts through territory? | later |
| ice lost | what defensive value does the player leave through territory? | later |

penalty effects attributed to on-ice players differ from personally recorded infractions and draws. keep those observations alongside, not interchangeable with, the modeled effects. [penalty methodology](https://hockeyviz.com/txt/magnus7P)

the following complete that component family without creating additional additive contributions:

| quantity | meaning / boundary | status |
|---|---|---|
| shootiness | modeled tendency to take the team's shot; effectiveness is a different question | later; [reference](https://hockeyviz.com/txt/shootiness) |
| four transition subskills | exit offense, entry offense, offensive-zone retention, defensive entry prevention; help explain ice won/lost | later; inferred puck movement is not tracked controlled entries/exits; [reference](https://hockeyviz.com/txt/bluelineTraversals) |
| finishing subskills | block avoidance, reaching the net, freeze outcome and conversion, conditional on earlier outcomes | later explanatory drill-down; exact supported quantities require validation; do not add conditional probabilities; [reference](https://hockeyviz.com/txt/xg8) |
| common-value summary | combine supported contributions under explicit accounting and a reference workload | later, conditional on valid composition; [synthetic-goals reference](https://hockeyviz.com/txt/sG) |

special-teams scope needs explicit manpower states. hockeyviz's published model covers 5v4, 5v3 and 4v3, but not power-play defense or shorthanded offense. additional states are candidates; those missing directions are not silently implied by a “complete” card. [special-teams methodology](https://hockeyviz.com/txt/magnus9ST)

evolving hockey offers a useful alternative accounting comparison: even-strength offense/defense, power-play offense, shorthanded defense, penalties drawn/taken; grouped offense/defense/penalty value; goals, wins and standings points above replacement. these are not extra independent skills. synthetic goals, goals above replacement and wins above replacement require different references and conversions; the inventory does not select a second model family. [glossary](https://evolving-hockey.com/glossary/goals-above-replacement/)

## goalie family — later

goalie profiles are confirmed; their precise estimands, fields and eligibility still require a separate specification. start with an intelligible stopping estimate and its evidence. stopping, evidence, spatial/type/danger detail, supported outcome subskills, workload and history are later family targets. exact start-quality/consistency fields and aggregate valuation remain candidates pending explicit definitions and validation; the entire table is not required for the first goalie release.

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
| isolated skater summary | coherent offense/defense maps and scalar effects; add validated components individually | first 5v5 subset; later full family |
| compact comparative skater card | component magnitudes and percentiles, clear cohort, identity, evidence and context; readable download | 05f supplies an observed five-rate subset; analytical components remain later |
| descriptive skater card | scoring, usage and on/off results; distinguish experience from estimated ability | 05d/05f cover personal scoring and on-ice summaries/comparison; richer usage and off-ice panels remain later |
| career and historical profiles | navigable season cards, maps, results, explanations and ability/subskill trajectories; common-value history where supported | 05g specifies a three-season observed subset and table-only history; longer careers and analytical trajectories remain later |
| detailed 5v5 view | inspect spatial differences hidden by the summary | first maps; richer drill-down later |
| finishing/setting detail | results, estimated subskills, shot-type/danger breakdowns and history | later; exact panel composition and bins specified with the models |
| goalie summary and detail | compact comparisons, stopping evidence, maps, subskills and history | later family; exact panels candidates |
| usage/context view | deployment distributions, teammates/opponents, role and workload | later beyond first exposure/context essentials |
| personal shot view | individual shot locations, rates and shot mix | later; observed/imputed locations distinguished |
| with/without view | together/apart results and maps, selected teammate/combination context, replacement comparisons | later; shared deployment prevents a causal-chemistry claim |
| adjustment explanation | relate observed on-ice results to isolated estimates through supported self/context terms and any defined residual | later; nonlinear effects need explicit composition, not invented additive attribution |
| tracking/microstat card | directly tracked actions and optional skating measures | optional |

public hockeyviz [career](https://hockeyviz.com/player/matthau97) and [season](https://hockeyviz.com/player/matthau97/TOR/2526) pages enumerate summary, detail, finishing, personal-shot and contextual panels. the [descriptive-card guide](https://hockeyviz.com/howto/skaterCard) and [with/without guide](https://hockeyviz.com/howto/wowy) explain distinct families. exact radar/spider layouts and separate replacement-comparison pages remain presentation choices; the contextual questions are later capabilities.

the context family includes supported teammate, opponent, coaching, score/deployment and other environmental contributions. [published model terms](https://hockeyviz.com/txt/magnus9EV) motivate those explanations; they do not guarantee a unique additive decomposition. a residual must retain its defined meaning rather than be relabeled luck. static published explanations can serve this purpose without an interactive refitter.

the [jfresh skater preview](https://hockeystats.com/cards/player-cards) supplies compact component comparison, context, history and download. evolving hockey's [official example](https://evolving-hockey.com/wp-content/uploads/2021/10/Player_card_2_ex-1536x1144.png), generated in 2021, pairs gar/xgar components with overall/group percentiles and deployment distributions. its [public card notes](https://evolving-hockey.com/stats/player_cards/) distinguish single-season totals from weighted three-season summaries. these preserve model and temporal distinctions; they do not establish current authenticated behavior or select another model for us.

## evidence and context checklist

these are panel candidates for the later descriptive/context families. v1 includes only the counts, exposure and coverage required by its own specification.

- **identity:** name, team(s), position, age, handedness where supported; trades must not silently fragment season totals.
- **individual results:** goals, primary/secondary assists and points; attempts, unblocked attempts, shots on goal and shooting percentage; counts and exposure-normalized rates. exact selections need a purpose, not every available column.
- **on-ice results:** attempts and goals for/against, rates and shares, on-ice shooting/save percentages; xg for/against clearly model-derived. individual results and on-ice results answer different questions.
- **deployment:** games, total and per-game ice time, strength-state workload, positional role; shift starts on the fly versus faceoffs and by zone; time leading/tied/trailing.
- **environment:** teammate/opponent context, including forward/defense groups; observed with/without results, team and league references. personally drawn/taken penalties remain recorded evidence.

the hockeyviz [descriptive guide](https://hockeyviz.com/howto/skaterCard) motivates the scoring, usage and on/off groups. do not promote those contextual associations into player skills. jfresh's current [explanation](https://hockeystats.com/about/player-cards) describes projected scoring rates, weighted multi-season inputs, position-specific cohorts and workload-based context. our observed-results panels must not borrow those numbers' labels while changing their meaning.

## comparison and application capabilities

| capability | status / contract |
|---|---|
| league table, name search, sorting and player navigation | first; unavailable estimates remain distinguishable from poor ones |
| compact player comparison | first; same state, units, baseline and comparable evidence |
| complete-season summary and game evidence | first; observed aggregates reconcile; game rows are not fitted ability contributions |
| distribution with selected player, percentile and rank | 05c supplies observed raw-unit distributions; 05f supplies numeric percentile standing for five rates with exact family cohorts and tie rules. ability distributions and other ranking contracts remain later; retain magnitude |
| richer comparisons and history | later; same-method comparisons or explicit method differences; no arbitrary date-window fitting |
| readable downloadable cards | 05d supplies one descriptive png; 05f supplies compact comparative content, preserving identity, raw rates, both supports, coverage and explicit cohort/percentile meaning. ability cards remain conditional on supported components |
| specialist component tables | later; reuse selected quantities, not independent recalculation |
| descriptive statistics workspace and downloads | later; individual/on-ice/workload tables, season rows, game evidence and useful count/rate views; publish supported derived outputs |
| inspectable definitions and evidence limits | first, expanded with each component; units, sign, baseline, time meaning, provenance, uncertainty and missingness |

our rule: a population distribution shows variation among players; an uncertainty interval describes uncertainty about an estimate. neither substitutes for the other. a rank is not an effect size. actual accumulated contribution, per-exposure rates and standardized-workload value are different views of defined quantities, not new skills.

historical cards are an explicit [jfresh offering](https://hockeystats.com/cards/historic-player-cards). public [player profiles](https://hockeystats.com/players/jackson-lacombe) expose descriptive table families and controls; the [line tool](https://hockeystats.com/stats/line-tool) exposes combination selection, whose results were not exercised. our historical profiles require analytical outputs for those seasons, not retained old publications.

later recorded-result coverage includes playoffs and additional strength states, separated from the fitted regular-season population. retain team-specific evidence for traded players without fragmenting their season-level ability estimate. hockeyviz's [appearance lists](https://hockeyviz.com/player/mcdavco97/EDM/2425) also include preseason; that remains a candidate, not an implied preseason model. historical range and state coverage must be established from admitted evidence, never inferred from a season selector.

## optional tracking enrichment

retain this checklist without making tracking an input to the public-data core:

- shooting and chance involvement, including rush versus established-zone offense;
- passes leading to shots/chances, dangerous passes and pass-origin context;
- carried/passed/dumped entries and exits, retention and success;
- defensive entry denials, controlled-entry prevention and rush-chance suppression;
- forecheck pressure, recoveries, defensive retrievals and retrieval success;
- possession decisions, turnover risk and workload;
- hits and skating speed/bursts where their distinct sources support them.

the [microstat-card guide](https://hockeystats.com/about/microstat-player-cards) draws on all three zones tracking and nhl edge skating data. samples, access, rights and definitions belong to that optional product. inferred transitions and imputed setters do not become tracked observations because they fill similar card slots.

## what this inventory does not commit us to

source capture, blocked-origin inference, chance-model stages, priors, aging and deployment adjustments support the estimates. they are not extra independent contributions to add to a card. statistical diagnostics belong to analytical work unless they answer a reader's concrete question.

team dashboards, coaches, prospects, fantasy, contract valuation, lineup simulators, game/playoff forecasts, accounts and payments are unselected neighboring products. salary/cap context and future-player forecasts are also unselected; appearing on a reference card does not make them essential here. arbitrary date-window fits remain excluded by the brief.

reference uncertainty is explicit: hockeyviz [announced rewritten models](https://hockeyviz.com/txt/preview2627) in september 2026 with methods forthcoming; public guides span different vintages. jfresh's current skater headline predicts future value, while our headline describes a selected season. [unresolved reference definitions](issues/card-reference-definitions.md) must be settled when their quantities become implementation targets. we can reproduce a capability using our own explicit, validated definition without claiming numerical equivalence.

the tradeoff is deliberate: preserve the full destination checklist, but specify only the next selected capability. this leaves future formulas and exact layouts open while preventing familiar omissions from disappearing between slices.
