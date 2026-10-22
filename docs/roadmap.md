# product roadmap

status: approved intermediate direction and proposed later milestones. version labels describe capabilities, not deadlines, giant releases or model/schema versions. the [brief](brief.md) fixes the destination; the [implementation plan](plan.md) owns current status, assignments and sequencing. the [capability inventory](product-inventory.md) lists components, cards and supporting views. this roadmap does not authorize execution or expand capture scope.

parity scope confirmed 2026-09-29: **complete player analysis**, covering hockeyviz/jfresh skater and goalie cards, components, context, history and comparisons. whole-site parity is not the destination. this means comparable analytical capabilities under our stated definitions, not identical private-model numbers.

## proposed progression

| milestone | what becomes useful | why here / what it needs |
|---|---|---|
| intermediate — private observed results | localhost completed-season table/search, player/game evidence and comparison; cohort-aware exploration, compact observed cards and distributions in actual units | [05a](specs/05a-observed-website.md)/[05b](specs/05b-observed-comparison.md)/[05c](specs/05c-player-explorer.md) supply this path independently of model admission. omit ability and xg; this does not replace v1 |
| v1 — explain a player's 5v5 contribution | completed-season offense/defense estimates and maps, recorded results, league table, name search, compact comparison and game evidence | establish the scientific and product foundation; this is the current plan, not merely the capture slice |
| v2 — compare and share supported estimates | declared-cohort ability distributions and percentiles, richer analytical comparisons, a compact downloadable 5v5 contribution card | reuse earlier observed exploration/card mechanisms when suitable; retain magnitude, units, uncertainty and component scope alongside ranks |
| v3 — follow the season | publish current-season estimates whenever the operator runs an update; show incorporated evidence and coverage | requires validated behavior with partial-season evidence, entrants and source corrections; rerunning the full-season recipe is not enough by itself |
| v4+ — broaden the component profile | penalties drawn/taken, power-play offense, penalty-kill defense and finishing, each added separately | each needs its own definition, reference, data support and evaluation; choose the next component from that evidence, not a mandatory bundle |

the supported analytical versions of v2 and v3 are independent after v1. observed distributions/cards can arrive earlier through the parallel product track below. the recommendation favors useful comparison tools first; current-season work can take priority if that is the more pressing use once v1 exists. the cost of the proposed order is delaying current-season analysis while improving the completed-season product. each milestone can ship through several small slices.

source capture, reconstruction and feature preparation support the first product; [the plan](plan.md) owns their current status and study results. [the feature inventory](model-features.md) distinguishes implemented encoders, inactive families and missing source/inference dependencies.

## scientific path to v1

the post-04b direction prioritizes useful spatial signal recovery and scoped uncertainty. [04c](specs/04c-attribution-recovery.md) tested one fixed geometric shape basis against zero and native 04b after diagnosing saved evidence. the user selected broad shape first: complete regional rates and fine cells remain secondary, and nomination would not establish complete player-map accuracy. improvement over 04a alone does not demonstrate recovery beyond zero; [the post-study finding](issues/attribution-spatial-recovery.md) leaves all frozen verdicts intact. numerical checks belong inside the work.

04c's representation traded fine spatial freedom for shared evidence across rink geometry. its known-truth assessment included broad/local and poorly represented patterns, annual transitions and inseparable linemates. its contingent refit-uncertainty and real-point-fit stages were not reached; they do not automatically transfer into later studies. native-grid rendering supplies no independent cell precision, and the 5% meaningful scalar contrast supplies no spatial error budget.

[04c's completed decision](research/attribution-04c/decision.md) fails the mean-recovery gate after all 800 paired datasets. gated uncertainty and real fitting are not reached. [04d's diagnosis](research/attribution-04d/decision.md) separates small broad geometric omission, limited precision and selected-scale suppression; annual carry supports its frozen targets. this motivates one pooling question, not an adopted model.

[04e](research/attribution-04e/decision.md) completes two spatial pooling bands within the same representation on all 1,200 new paired datasets. the decision is `criteria_failed`: no cell supports 25% lower regional error than zero, candidate fresh-deployment prediction worsens, and control gains over its training-context baseline are negative. three regional improvements over control do not satisfy the joint claim. larger null/inactive false maps remain visible diagnostics. all bounded numerical checks and independent reviews pass; calibrated player intervals, real-data evidence and complete rates remain unresolved. no real fit, nested fitting or next candidate follows. the private observed website remains independent.

[04f](research/attribution-04f/decision.md) completes the bounded saved-output diagnosis before another attribution revision. its exact accounting separates regional pair recovery, native spatial weighting, complete-lineup combinations and context interaction. 04e's verdict remains unchanged; the remedy remains unresolved and no successor is proposed. [the plan](plan.md) owns further assignment. no new fits or successor model are bundled into this diagnosis.

the subsequent [04g comparison](research/attribution-04g/decision.md) completes one separate population constraint while retaining annual borrowing and marginal-likelihood selection. it broadens physical truths beyond forced opposite pairs and scores all identifiable player combinations. prediction improves over the control in all eight non-null cells, but regional recovery worsens in six and every useful-recovery target fails. progress and nomination both fail; numerical checks pass. this preserves the old verdicts and admits no model. [the plan](plan.md) records closure; no real-player uncertainty campaign or successor is assigned.

the [04h diagnosis](research/attribution-04h/decision.md) connects regional recovery to physical units within a finite pooled family; its truth-selected reference is diagnostic. [04i's completed comparison](research/attribution-04i/decision.md) rejects its observable selector: sparse recovery and every prediction-retention criterion fail, while diffuse recovery is inconclusive. the control remains research evidence, not an admitted model.

[04j's completed real-deployment information diagnosis](research/attribution-04j/decision.md) closes selector findings from saved evidence, compares actual player separation with the simulations, and proposes the next empirical evaluation. the user selected working-noise information without empirical game-noise estimation. real design and temporal assumptions precede another candidate; no new algorithm or narrower product destination is selected. this costs real-artifact assembly and conditional matrix analysis, without establishing recovery or calibrated intervals. [the plan](plan.md) owns assignment; the completed information study does not assign its proposed empirical benchmark.

[04k's completed comparison](research/attribution-04k/decision.md) tests existing league-relative annual borrowing against a final-season-only fit, with known native physical effects on actual deployment. all 100 pairs and twelve probes pass independent review. aggregate/stable gains coexist with reversal, first-observation and null harm; half-amplitude prediction cost remains imprecise. the diagnostic has no scientific gate, nominee or real-player uncertainty claim. its single prior question is a proposal; [the plan](plan.md) owns progression.

[04l's completed accounting](research/attribution-04l/decision.md) locates stable gains/reversal harm mainly in retained means and entry harm mainly in current-signal weighting. interacting scales and covariance leave the remedy unresolved; no prior intervention is selected. exact conditional accounting is not a repaired model.

the [04m empirical benchmark](specs/04m-attribution-empirical.md) tests recorded whole-game-held-out spatial shape with unchanged annual borrowing, independent fitting and training context. its [result](research/attribution-04m/decision.md) supports lower broad-regional loss from borrowing; native improvement remains unresolved. retain borrowing as the developmental baseline. this shape comparison does not establish complete rates, latent recovery, player uncertainty or next-season forecasting; preserve the earlier synthetic verdicts.

[02d source/exposure consistency](specs/02d-source-exposure-consistency.md) separately addresses 05g's two source findings: strict-interior matched exclusions, three complete-bundle probes with conditional expansion across the 57 empty-shift games, and one corrected observed candidate. distinguish policy losses, recovery gains and frozen-ledger research consequences before proposing regeneration; do not modify 04m or assume a refit is necessary.

the approved [04n complete-rate direction](specs/04n-attribution-follow-up.md) assesses predicted matched unblocked volume plus spatial shape on held-out games before another prior, context or uncertainty campaign. compare complete regional rates and component interaction; inspect physical-rate limitations without clipping or inventing a native positivity gate. 02d determines whether a source-only sensitivity must come first; changed support requires matched shape and volume controls. the cost is fresh volume work and delayed context refinement; the benefit is testing the assembled quantity required by the player product. this remains an unblocked diagnostic, with the full spec and execution separately assigned. all-attempt valuation, player recovery and uncertainty remain later requirements.

the remaining analytical responsibilities are distinct; their concrete next studies depend on evidence rather than a mandatory bundle:

| responsibility | remaining claim / dependency |
|---|---|
| spatial attribution and complete rates | useful recovery, scoped uncertainty, joint map/scalar accounting and adequate complete-rate behavior; smoothing alone does not guarantee positive intensities |
| deployment adjustment | use justified shift-start/time, score/time, rest and penalty-aftermath facts across all supported exposure, including zero-event time; coach terms require admitted dated evidence |
| temporal ability | annual age-neutral borrowing already exists; assess age-related change, entrant/returner behavior and entry/exit selection against it. older history needs a named temporal consumer |
| chance valuation and downstream consequences | supported integrated opportunity values, block-origin/type/tip sensitivity and common-reference valuation; retain 03p's structural nomination without treating it as admission |
| real-player support | predictive/portability evidence, shared-deployment limitations and justified consequence budgets; synthetic recovery and provisional weights cannot supply these alone |

04a/04b's matched recorded-rate populations and provisional valuation remain research evidence. neither location-only stresses nor agreement between unadmitted weights bounds error against truth. the [04 supported-attribution contract](specs/04-player-attribution.md) preserves the all-attempt chance-valued destination. [model direction](research/model-direction.md) retains alternative chance structures and targeted inactive features; no blanket activation or new acquisition is implied.

[05a](specs/05a-observed-website.md) progresses independently from those model questions using observed evidence. [05](specs/05-publication.md) and [06](specs/06-website.md) later extend its publication/view owners with supported ability, maps and comparisons. selected lasting checks under [07](specs/07-lightweight-testing.md) arrive with their owning boundaries; the whole testing slice is not a prerequisite. [the plan](plan.md) owns assignments.

tradeoff: the intermediate website delivers earlier utility and feedback, with possible schema/view rework when supported estimates arrive. spatial pooling adds a testable smoothness assumption and may lose local detail. neither direction lowers the evidence required for ability publication or changes the first analytical product.

## milestones that need not wait

the analytical release path is supported outcome/opportunity measurement, including blocked-origin/type/location sensitivity → spatial stint attribution with exposure (including zero-shot time), teammate/opponent/deployment context and history → useful profiles/maps/observed game evidence → broader cards and component families. per-shot conversion is upstream valuation, not player creation/suppression. [magnus9](https://hockeyviz.com/txt/magnus9EV) motivates that distinction. richer historical claims need an explicitly admitted historical corpus; nineteen peer seasons are not a prerequisite for the first useful profile. research-only attribution feasibility can investigate the downstream model earlier, as described above.

05a/05b supply private observed results and comparison without a chance-model handoff. on 2026-10-20 the user approved the following product direction alongside 04l. tables support discovery, compact cards support comparison, and spatial views explain location. evolve one application and its publication owners; no generic card/dashboard system.

| slice | purpose / boundary | tradeoff |
|---|---|---|
| [05c player explorer](specs/05c-player-explorer.md) | discovery filters, compact observed summaries and raw-rate peer plots; reported forward/defense reference and 300-minute default, independently adjustable from table filtering | existing local publication suffices; no numeric percentiles or ability inference. low-minute selections remain visible, and mixed-position references remain distinct |
| [05d descriptive cards](specs/05d-descriptive-cards.md) | recorded personal shots/goals/primary assists across tables, profiles, comparisons and one png | separate personal support preserves on-ice results; source/publication work and manual schema cutover. percentiles/new peer plots deferred |
| [05e spatial views](specs/05e-spatial-views.md) | observed unblocked for/against rink views on profiles/comparison; league differences and absolute rates, fixed smoothing and numerical evidence | a third matched support, explicit display geometry and schema-3 rebuild. unadjusted league context is not replacement value or ability; no model-admission dependency |
| [05f comparative observed cards](specs/05f-comparative-observed-cards.md) | five existing personal/on-ice rates with observed percentiles; compact profile/comparison/png and one selected-metric detail | application-only reuse of published facts. personal/on-ice peer populations can differ; raw magnitudes stay visible; higher means more, and outside-cohort selections have no percentile |
| [05g historical observed profiles](specs/05g-observed-history.md) | 2023–24 through 2025–26 in the existing league/profile/same-season comparison; three-row raw-rate history with exposure/coverage and linked detail | third-season derived preparation, all-season verification and schema-4 rebuild. one active database holds all years; seasonal identity/peers/map references remain separate; no trajectory chart or ability claim |
| [05h observed deployment](specs/05h-observed-deployment.md) | two selected-season tables: teammate/opponent minutes and shares of selected-player included time | every retained on-ice interval, including zero-event time; canonical pair facts after 02d's observed boundary. overlapping shares, no peer cutoff, quality, chemistry or adjusted effects |

05f supplies comparative context and 05g historical observed profiles. 05h specifies deployment context independently of 04m, using 02d's reviewed observed contract and checked candidate as its preservation baseline. complete shift recovery and the separate frozen-research audit are not product prerequisites; retained gaps stay visible. after acceptance, the next proposed product action is explicit activation of the combined observed website, not another frontend slice merely to occupy research time. personal shot maps remain a distinct later capability. 04m's positive evidence supplies neither admission nor ability-release authority. analytical cards/maps can be designed with labeled synthetic examples when separately assigned; real ability release still requires supported analysis. withheld fitted effects cannot enter through an observed label. [the plan](plan.md) owns current status and progression.

replacement-based value remains a later player-analysis capability with an explicit reference population, components and supported attribution. league-relative observed maps and replacement valuation answer different questions; switching the map's subtraction cannot establish the latter. 05e uses included league context and preserves that distinction.

- **public website:** publish once the personal product is useful and ready to share. hosting and data-publication details get their own small specification then. full cards are not a prerequisite. fitting stays local; hosting does not create an update schedule.
- **historical player analysis:** publish prior-season profiles/cards, maps, component explanations, recorded results and trajectories when comparable outputs exist. define supported seasons and visible gaps through corpus admission. historical training data alone does not supply these outputs; historical season rows in the active publication do not require archived website builds or publication revisions.
- **goalie cards:** confirmed later as a separate analytical family. begin with stopping and its evidence, then add spatial/type/danger detail, supported subskills, workload and history. choose their place after v1 according to value and available evidence; they need their own validation, not completion of every skater component first.

## longer-term destination

the [card references](research/player-card-references.md) describe the intended combination: hockeyviz-style spatial explanation and inspectable components, with jfresh-style concise comparative cards, history and sharing. fuller cards add setting, shooting tendencies and transition contributions as their estimates become defensible. publicly available event data may support inferred components without supporting claims of directly tracked passing or entries; optional enrichment remains separate from the public-data core.

a common-value summary follows only if the components support coherent accounting and a declared reference. no sum of percentile ranks, double-counted contributions or premature total-player-value label. replicating capabilities is the destination; numerical parity with a private model is not an acceptance test.

## player-analysis completion checkpoints

these were missing or underspecified in the milestone outline. they are later capability targets, not one additional giant release. the inventory owns the detailed checklist.

| capability | completion means | dependency / cost |
|---|---|---|
| explain results versus ability | expose supported teammate, opponent, coaching/deployment and other context behind the adjustment; show a residual only where its meaning is defined | needs published explanatory model outputs; contributions add only where the model supplies valid accounting; residual is not a synonym for luck |
| descriptive statistics workspace | individual/on-ice/workload tables, season rows, game evidence, useful count/rate views and downloadable tables | reuses interpreted evidence and publications; selections must not silently change an estimate's fitted population |
| personal and contextual detail | personal shot maps; together/apart results and maps; replacement context; deployment and teammate/opponent comparisons | additional published summaries and exposure; shared deployment still prevents a causal-chemistry interpretation |
| full component detail | spatial special-teams effects, transition subskills, finishing/setting explanations and shooting/goalie outcome detail by supported type/danger | separate scientific validation; exact states, bins and field definitions belong to each slice |
| historical and broader recorded coverage | navigable historical profiles; traded-player team evidence alongside season estimates; later playoff and other strength-state results clearly separated | source admission and backfilled outputs; displaying playoff results does not authorize pooling them into regular-season ability fits |

these targets follow the public hockeyviz [career](https://hockeyviz.com/player/matthau97) and [season](https://hockeyviz.com/player/mcdavco97/EDM/2425) surfaces, jfresh's [historical-card offering](https://hockeystats.com/cards/historic-player-cards), and the current [player-statistics workspace](https://hockeystats.com/players/jackson-lacombe). historical archive access and full interactive workflows were not verified. exact earliest seasons remain evidence-dependent. preseason recorded views remain candidates; no preseason ability model is selected.

## deliberate differences and excluded site families

hockeyviz describes ability at a [particular instant](https://hockeyviz.com/howto/isolate); jfresh describes [predictive war and scoring](https://hockeystats.com/about/player-cards). our headline describes underlying level across a season. current-season updates do not change that estimand. forecast outputs or a point-in-time state estimate would require a separately selected target; matching layouts cannot establish scientific equivalence. similarly, a common-value summary does not establish replacement-based valuation until that reference is defined.

arbitrary date ranges remain excluded; tracked microstats remain optional; contract context remains unselected. these are explicit differences from parts of the references. the cost is narrower functionality in exchange for retaining the settled product meaning and public-data core.

whole-site exclusions include team/league dashboards, game/series reports, coach evaluations, game/playoff forecasts, scenario/roster builders, prospects, scouting and other leagues. these are substantial additional products, evidenced by hockeyviz's [team page](https://hockeyviz.com/team/TOR/2526) and [tool offerings](https://hockeyviz.com/subscribe), and hockey stats' [broader product](https://hockeystats.com/). their existence does not expand the selected player-analysis destination. operator-run publication also makes no promise of either site's live delivery cadence.

## scope discipline

retain the same operating model throughout: local batch analysis, saved expensive fits, sqlite publication and an ordinary website. add a feature's concrete contract and implementation slices when it becomes next. no future-proofing framework or full future backlog now.

prospects, fantasy tools, contracts, lineup simulation, arbitrary date-window fits and paid services are not implied by this roadmap. ordering and candidate details remain proposals; the confirmed skater/goalie destination and agreed v1 scope stay fixed.
