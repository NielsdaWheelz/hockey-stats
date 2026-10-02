# project brief

status: product direction settled through discussion on 2026-09-29. this is the authoritative brief. explicit user choices and delegated implementation judgments are distinguished below. [capture](specs/01-capture.md), [interpretation](specs/02-interpretation.md), [reconstruction](specs/02b-reconstruction.md), [corpus/reference admission](specs/02c-corpus.md) and [chance-model workflow](specs/03a-chance-workflow.md) are reviewed and merged. 03b is complete and merged in `9132131`; its [scientific decision](research/chance-03b/decision.md) rejects the declared all-attempt use. 03e's completed [decision](research/chance-03e/decision.md) is `withheld`, with no surviving primary or handoff. 04 and publication remain unauthorized. the [external drive audit](research/external-corpus-audit.md) informed the corpus choice. the website remains unstarted; scientific support is not implied.

pr03c follow-up: [source revision](specs/03c-source-revision.md) and its offline-evidence amendment are reviewed and merged in `fa61454`. [the complete audit](research/chance-03c/decision.md) records report attributes, landing goal modifiers, bounded source repairs, expanded fixtures and all three local seasons. verified game-body equivalence supports the historical comparisons; fresh receipts retain actual dates. [03d](specs/03d-chance-revision.md) is reviewed and merged in `af95c88`, with [fixture verification](research/chance-03d/verification.md) complete. the user authorized [03e](specs/03e-training-assessment.md) implementation and real fitting on 2026-09-30; [software verification](research/chance-03e/verification.md) and the bounded study are complete under the unchanged [protocol](research/chance-03e/protocol.md). all three development recipes completed fitting, evaluation, scoring and comparison; each decisively failed declared all-attempt calibration. no primary survived, so dependent transfer, kernel variants and final fits were not run. the user has no full-game replay access. use public evidence without assuming a subscription or annotation campaign; imputed origins remain distinct from observed physical origins. no scientific criterion or 03b verdict is retroactively changed.

current next step: [03f](specs/03f-model-development.md) and its bounded study are reviewed and merged in `9c5f3dc`. [its decision](research/chance-03f/decision.md) recommends recent-context interactions for further research in each observable component and retains full training history; calibration limitations remain. the user authorized the entire [03g](specs/03g-chance-assessment.md) implementation/diagnostic on 2026-10-02; it is complete and independently verified. [its decision](research/chance-03g/decision.md) recommends `assess_integrated`: composed proper losses improve while calibration and observable spatial discrepancies remain. no fitting or handoff occurred. [03h](specs/03h-chance-revision.md) retains separately specified assessment as an unauthorized stub. this sequence does not change the product target, admit a model or rehabilitate 03e's candidate.

## purpose

answer: **how good is this player at creating and suppressing chances, where on the ice does that appear, and what evidence supports the estimate?**

the primary product estimates repeatable ability using prior seasons, with observed season results alongside. the user has specified its temporal meaning: the player's underlying level across the selected season, rather than their state at season's end. it is centered on interpretable player components and spatial explanation, following hockeyviz's approach. evolving hockey remains a useful comparator. learning happens through building; teaching features and a curriculum are not requirements.

the first useful version serves the user personally, with an eventual public website. its initial analytical scope is **5v5 skater chance creation and suppression in a completed regular season**. current-season operation follows through local runs initiated whenever the user wants an update.

the explicit long-term destination is to replicate the substantive player-card and component-analysis capabilities of hockeyviz and jfresh, delivered incrementally. this includes sortable ranking tables and distribution charts showing where a selected player sits among a declared comparison population. dedicated goalie cards are a confirmed later family with their own models and validation. this is a product goal, not merely visual inspiration. the initial target does not need to contain the full cards or distribution charts. [capability inventory](product-inventory.md) · [reference scope and evidence](research/player-card-references.md)

## choices confirmed by the user

| decision | settled direction | material consequence |
|---|---|---|
| product focus | player contribution through components | game and team views support this purpose; a game explorer alone does not fulfill the brief |
| modeling philosophy | hockeyviz-style interpretability and decomposition | model assumptions, context, and component meaning must be inspectable |
| chance-quality boundary, confirmed in 03d | retain location, shot type and supported preceding-play context; standardize modeled residual shooter/goalie execution | creating these circumstances counts toward opportunity; 04 must not automatically control the same mechanisms away; this is not causal isolation |
| long-term product | hockeyviz player cards/components and jfresh player cards | preserve the destination while delivering one defensible component at a time |
| parity boundary | complete player analysis: skater/goalie cards, components, context, history and comparisons | broader team/game products, forecasts, simulators and prospects are not implied; retain our declared statistical meaning |
| goalie profiles | include dedicated goalie cards later | a separate model and validation family; the first 5v5 skater target stays unchanged |
| primary statistical question | repeatable ability, informed by prior seasons | estimates can differ from current-season outcomes and can lag abrupt changes in ability |
| temporal meaning of ability | underlying level across the selected season | a late-season improvement remains blended with earlier play; no claim of season-end form |
| website interaction | explore published analyses; run new fits separately | interactive filters query available results; new adjusted estimates require a separate analytical run |
| first player discovery | compact league-wide table plus name search | publish a sortable player-summary index with links to profiles and comparisons |
| long-term comparison tools | tables for sorting and ranking; distribution charts locating a player | comparisons need explicit populations and uncertainty; an ordered table alone does not establish meaningful separation |
| publication history | serve the active publication; keep one previous valid publication for rollback | recover application code through git history; no archived builds or historical publication browser |
| publication intent | explicit publication of a validated candidate | successful computation does not replace active results; the operator takes a separate publish action |
| incomplete evidence | allow justified, visible coverage gaps | withhold unsupported estimates; label incomplete observed totals and assess selective missingness |
| serving independence | browse published results and develop without the external drive; eventual public production also serves independently | retain complete published outputs where they are served; rebuilding remains a separate operation |
| analytical execution | local batch processing and fitting on the user's machine and hdd indefinitely | no assumed migration to remote computation; fresh publications depend on local availability and successful runs |
| observed results | show alongside estimates | retain the distinction between what happened and what the model estimates |
| observed period | complete-season summary plus game-by-game breakdown; no window/date-range splits | no interactive aggregation over selected dates; the season summary and fitted estimate retain their declared periods |
| first evidence drill-down | game-by-game breakdown | publish recorded counts, reconstructed 5v5 exposure, and coverage; individual-event investigation remains in local analytical tools initially |
| first audience | the user, then a public audience | one operator; no first-release subscription, account, or multi-user administration system |
| first analytical scope | 5v5 skater chance creation/suppression | finishing, special teams, and dedicated goalie profiles follow separately; no claim of total player value |
| blocked attempts | include blocked shots by imputing their shooting origins | retain observed block locations separately; location inference adds assumptions, validation and uncertainty |
| first time horizon | completed season, then current season | establishes a fixed reference before ongoing updates and correction handling |
| freshness and cadence | conditional freshness; the user initiates local runs when wanted | results retain their actual evidence cutoff between runs; no update deadline or required nightly operation |
| source access | public-data core; optional paid enrichment later | paid tracking cannot become an undeclared dependency of core results |
| language responsibility | effect for application behavior; python for numerical work | two environments and an explicit exchange contract; one authoritative implementation per calculation |
| data fidelity | preserve truly raw responses and correct discovered defects | transformation cannot overwrite evidence or invent missing facts |
| verification workflow | temporary integration/live tests for initial red/green/refactor, deleted after verification; a later dedicated slice defines a tiny lasting suite | useful fixtures/facts remain; interim changes require recreating checks; scientific model evaluation remains part of the analysis |
| chance-model progression | implement the workflow in 03a, admit real training data and assess fitted models in separate 03b | fixture verification cannot establish scientific acceptance |
| revised-model evidence, confirmed during 03e | allow conditional progression using the existing, previously examined seasons | disclose research exposure; chronological assessment is not untouched confirmation. declared scientific checks still apply; this does not establish physical-origin accuracy or authorize publication |
| origin-assumption sensitivity, confirmed during 03e | carry scientifically admissible alternatives into 04 research even when opportunity maps differ materially | retain the family; 04 must test player magnitudes, signs and spatial conclusions across it before publication. calibration/source failures still block admission; do not assume map differences cancel |
| first training corpus | fresh captures of 2023–24 through 2025–26 through the existing pipeline | another download and later retrieval dates; no legacy importer or projected source inputs; acquisition/implementation separately authorized on 2026-09-30; this does not establish scientific support |

## initial product and scope

the following are engineering/product judgments within the confirmed direction, not additional answers attributed to the user:

- **league and season:** nhl, league-wide, initially the 2025–26 regular season. the official [season reference](https://api.nhle.com/stats/rest/en/season), checked on 2026-09-29, identifies this as a completed season. player estimates require league context; a favorite-team-only model would not suffice.
- **population:** skaters during genuine 5v5 play with both goalies present. other situations remain preserved in source captures but are outside this initial analysis. individual eligibility and insufficient-evidence behavior belong in the metric specification.
- **blocked attempts, confirmed during architecture:** include blocked shots using imputed origins in the intended all-attempt analysis. observed block coordinates remain intact and distinct from inferred shooting locations. the estimator and its validation remain scientific responsibilities; unblocked-only results may serve as a benchmark, not a silent replacement for this scope.
- **profile:** separate offensive chance creation and defensive chance suppression, with spatial maps, readable rates or component summaries, and observed results for the same declared selection. observed results mean recorded counts and exposure; an unadjusted on-ice xg total is still model-derived and must be labeled accordingly. use a league-average reference for the first estimates; replacement-level valuation is a different later question.
- **comparison:** support comparing players under the same population, baseline, and units. a compact comparison supports the core question; a generalized custom-report builder is not required.
- **discovery, confirmed during architecture:** a compact league-wide table plus name search. show separate offensive and defensive estimates, exposure, and uncertainty or unavailable status; support sorting and access to profiles and comparisons. broader ranking tools and distribution charts follow incrementally.
- **evidence:** display exposure, the observation cutoff, the selected season the estimate describes, model/data revision, and consequential uncertainty or limitations. keep that season-level target distinct from a season-end state estimate. a profile should distinguish a weak estimate from an estimate of weak performance.
- **game breakdown, confirmed during architecture:** the player profile includes a complete-season summary and game-by-game table of recorded counts, reconstructed 5v5 ice time, and inclusion/coverage information. its aggregates reconcile to the corresponding displayed season results. no window/date-range splits. the table does not decompose adjusted season-level ability into game contributions. identify prior-season evidence separately; these displayed games are not the complete evidence behind the model. individual-event browsing is deferred.
- **history:** earlier seasons supply priors, fitting, and validation as justified by evidence. one displayed season is not permission to fit on that season alone. the earliest usable season is determined by source coverage and model validation, not copied from the old repo.

current-season coverage comes after the completed-season result is credible. the user controls when updates run. this supersedes treating the earlier next-morning preference as an operating requirement. new publications must identify the games and evidence incorporated, rather than merely change a refresh timestamp. retrieval, scoring, player-estimate updating, and global model refitting may be separate operations; expose meaningful differences in their cutoffs. an older result remains a result for its stated evidence, and is not provisional merely because time has passed.

the website explores published analytical datasets. new model fits run separately through research/operator commands. player selection, sorting, and comparisons remain interactive, but cannot silently change the population or temporal meaning of an existing fitted estimate. observed summaries target the complete selected season, with game rows available for inspection; arbitrary window/date-range summaries are excluded. custom adjusted estimates require their own run and validation before publication.

the user permits publication with justified, visible coverage gaps. incomplete source evidence need not block the entire season when scientific checks support the remaining claims. withhold unsupported estimates, identify exclusions and their consequences, and label incomplete observed totals as covering the included evidence. season-level ability remains the target, but selective missingness can invalidate particular estimates or the whole fit. neither a high overall coverage percentage nor disclosure alone establishes validity. this relaxes absolute completeness, not the evidence required for a claim.

local browsing and the eventual public production website consume complete published outputs without depending on the external drive or fitting environment. retain the latest complete publication locally for real browsing and application development, alongside separate compact fixtures. the public serving environment holds its own complete publication. this separation permits interactive queries; it does not require static hosting. successful runs produce candidates; activation requires an explicit operator publish action after the required checks. between publications, continue serving the last valid results with their evidence cutoff visible.

retain the active publication and one previous valid publication for rollback. this limits revisions of published outputs, not the historical seasons needed for fitting. keep the source evidence, expensive fitted artifacts, configuration and git references needed for the retained results and current research. preservation follows replacement cost: fitting can take hours, while rebuilding the website takes minutes. recover application code through git and rebuild it; rerun cheap derived work. no archived application builds, per-step recovery system or automatic cleanup service. removing old research outputs is an ordinary operator task after checking what is still useful.

ingestion, analytical processing, and fitting run locally with the external hdd indefinitely. this is a settled operating constraint, not a temporary step toward cloud computation. preserve completed expensive work across interruptions; exact checkpoint boundaries and numerical continuation depend on the workload and fitter. if resources are unavailable, work waits until the user runs it again. automation may be added for demonstrated convenience; schedulers, freshness alerts, and availability commitments are not current requirements.

## what interpretability requires

the preference is substantive, not a demand for a particular regression package. a reader should be able to inspect the inputs, reference conditions, component definitions, and composition rules behind a result. preserve spatial differences that a scalar would erase. more coefficients or more panels do not necessarily provide more understanding.

components need valid accounting. a sum must reconcile to its total where the model defines addition; conditional probabilities may multiply, and interactions may prevent an additive interpretation. chance creation, finishing, and other mechanisms must not count the same value twice. do not manufacture a total merely to fill a player card.

the initial adjusted spatial maps and their offensive/defensive headline summaries must describe the same fitted quantity. a map of observed shots can supplement the evidence, but cannot by itself explain an adjusted player estimate. this is a scientific design consequence of the promised spatial explanation; exact response, population and accounting are tracked in the architecture.

interpretability governs model choice among empirically credible candidates; it does not excuse invalid probabilities, leakage, unstable attribution, or misleading uncertainty. simpler or more flexible models may be used as benchmarks. reproducing selected public methods is useful evidence, but matching hockeyviz's private production numbers is not the acceptance criterion.

the resulting quantities are context-adjusted estimates under stated assumptions. inspectable arithmetic does not establish causal identification. historical information stabilizes estimates but introduces assumptions about persistence and aging; sensitivity and validation must address them. [public magnus 9 methodology](https://hockeyviz.com/txt/magnus9EV)

inference is permitted when necessary and supported, with its provenance and assumptions visible. mccurdy's [shot-outcome description](https://hockeyviz.com/txt/xg8) illustrates both interpretable decomposition and imputed inputs. our model must distinguish observations from reconstructions and imputations. excluding incomplete records can also bias the sample, so neither automatic exclusion nor automatic filling is a universal policy.

## source and correction contract

retain original response bodies before parsing, filtering, normalization, or serialization into another shape, with enough source and retrieval metadata to identify the capture. retain full captured game responses even when the current analysis uses only a subset. the precise byte/encoding and storage contract belongs to architecture.

raw evidence may contain upstream mistakes. keep it unchanged; corrections, coordinate normalization, identity resolution, and imputation produce separately attributable derived records. unknown handedness remains unknown until an attributed source or explicitly labeled inference supports a value. corrected historical downloads are new captures, not replacements masquerading as earlier evidence.

every result identifies its input selection, transformation/model revision, and information cutoff. revised evidence must not silently coexist with stale dependent results. preserve enough information to reproduce and explain the active and rollback publications; deliberately discarded older revisions carry no indefinite reproducibility promise. a historical reanalysis must not be represented as a forecast that was available at that historical date.

ordinary development and tests work without the external drive or live upstream requests. the user approved two evidence tiers: compact committed fixtures spanning ordinary and broken games across supported seasons, and a larger raw local corpus outside git, targeting all three already-captured seasons subject to measured storage cost. 03c owns expansion and copying; subsequent slices preserve new distinct failure cases as encountered. copy original complete available response bundles, receipts and season references, with hand-checked facts; synthetic cases stay separate. copying evidence does not authorize fitting or supply scientific acceptance. 07 owns the lasting lightweight checks, not the start of fixture collection. [fixture policy](../fixtures/README.md#fixture-policy-and-local-corpus)

the [external audit](research/external-corpus-audit.md) found projected boxscores, synthetic roster fields and no per-event on-ice reports in the old database. the user chose fresh acquisition for pr03b; archive contents remain unadmitted. fresh full-corpus response/missing-value checks are now recorded in the audit and [03b verification](research/chance-03b/verification.md); [external-inventory](issues/external-data-inventory.md) tracks remaining preservation questions before any separately authorized cleanup. [fresh fixture admission](../fixtures/README.md) replaces the old fixture baseline without rehabilitating the archive. improve mechanisms at their responsible layer; do not silently alter old evidence.

publicly accessible inputs do not automatically permit unrestricted redistribution. the core must be rebuildable from identified accessible sources; publication of bundled source data requires source-specific review. optional paid inputs must identify their additional coverage and must not silently change the meaning of core metrics.

## success criteria for the first analytical product

1. selecting an eligible skater yields a defensible estimate of 5v5 offensive and defensive contribution, with useful spatial detail and an explicit reference population.
2. observed results and modeled ability remain distinguishable; maps, tables, and any exports describe the same declared selections. game-level counts and exposure reconcile to the corresponding season summary; unavailable evidence is not presented as zero.
3. comparison makes differences, evidence volume, and uncertainty intelligible without implying that every numerical difference is meaningful.
4. data reconstruction reconciles selected independent facts and handles supported boundary cases without invented observations or silent loss of coverage.
5. the statistical evaluation supports the promised interpretation against honest baselines and checks information leakage, calibration where relevant, stability, and shared-deployment sensitivity. the later model specification sets quantitative acceptance rules before evaluating candidate results.
6. a result can be traced and reproduced; a correction leads to a coherent revised publication or explicit unavailability, with rollback possible.
7. the bounded development dataset exercises real boundaries offline. a full-data run explicitly identifies its larger input and cannot silently substitute fixtures.

visual quality serves these criteria: consistent rink orientation and scales, legible units, deliberate information density, and progressive detail. no teaching workflow is required. the first product is complete when it answers the promised question reliably, not when it reaches a feature count.

## excluded from the first analytical product

finishing or setting skill profiles, special-teams valuation, dedicated goalie profiles, playoff analysis, prospect/other-league coverage, contracts, fantasy recommendations, game forecasts, lineup simulations, total gar/war-style ratings, and paid tracking integrations.

the fuller skater cards, their component families, comparison summaries, career context, broader ranking tools, and player distribution charts belong to the confirmed long-term destination. they are deferred from the first target, not discarded; the compact sortable discovery table is included initially. surrounding products such as fantasy, prospects, or roster simulation are not implied by the card goal. numerical agreement with a particular private model, exact component formulas, and the treatment of an overall total require their own evidence and specifications.

the cost of the initial scope is real: the profile does not explain a player's entire contribution. that limit must be visible. infrastructure/data slices may precede the usable profile, but they are dependencies rather than substitutes for it.

## remaining decisions and their owners

no further user preference is required to complete this brief. unresolved empirical questions are not decisions we can settle by preference.

| remaining matter | owner and timing | what settles it |
|---|---|---|
| concrete dependency pins and interface fields | engineering, relevant slice specification | selected architecture, current compatibility and the slice's actual inputs/outputs |
| model family, within-season evidence weighting, xg/shot definitions, priors, contexts, uncertainty method | statistical design, before the relevant implementation slice | the settled season-level estimand and explicit evidence requirements; benchmarked candidates |
| detailed card reference versions and component expansion order | product/statistical design, as later components are specified | pinned examples and method descriptions; the long-term destination itself is settled |
| trustworthy historical coverage and training horizon | data audit and statistical validation | actual source inventory, reconstruction checks, and held-out evidence |
| offline evidence and lasting verification | 03c expands fixtures/local raw corpus; each slice preserves distinct new failures; 07 defines lasting checks | attributable cases and checked expectations, measured storage, verified copies and explicit offline selections |
| input cutoffs, interruption recovery, update/refit commands | architecture and current-season specification | explicit operator actions, measured workload, reusable completed work, and accurate result provenance |
| hosting, public launch, source-code license, paid inputs | later publication/product decision | a useful personal product and concrete costs/rights; none is a prerequisite for first analysis |

this is a website run by one person. use ordinary local commands to acquire data and run python analysis, then explicitly publish a completed sqlite file. stopping the server, replacing that file, restarting and reloading the page is sufficient. save work when recreating it is expensive; rerun cheap steps. add automation or machinery only when it demonstrably reduces recurring work or serves an actual feature. the agreed hockey analysis can be ambitious without making website operation elaborate.

the brief and architecture direction are complete. [the first slice](specs/01-capture.md) is implemented with two admitted example games. later implementation follows specification review and the user's progression decision. outline dependencies without exhaustively specifying empirical research in advance. 03a produces explicitly labeled fixture fits and scored attempts; no scientifically accepted model or player analytical dataset has been produced yet.
