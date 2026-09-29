# project brief

status: product direction settled through discussion on 2026-09-29. this is the authoritative brief. explicit user choices and delegated implementation judgments are distinguished below. architecture and implementation remain unstarted.

## purpose

answer: **how good is this player at creating and suppressing chances, where on the ice does that appear, and what evidence supports the estimate?**

the primary product estimates repeatable ability using prior seasons, with observed season results alongside. it is centered on interpretable player components and spatial explanation, following hockeyviz's approach. evolving hockey remains a useful comparator. learning happens through building; teaching features and a curriculum are not requirements.

the first useful version serves the user personally, with an eventual public website. its initial analytical scope is **5v5 skater chance creation and suppression in a completed regular season**. current-season operation follows, with next-morning updates.

the explicit long-term destination is to replicate the substantive player-card and component-analysis capabilities of hockeyviz and jfresh, delivered incrementally. this is a product goal, not merely visual inspiration. the initial target does not need to contain the full cards. [reference scope and evidence](research/player-card-references.md)

## choices confirmed by the user

| decision | settled direction | material consequence |
|---|---|---|
| product focus | player contribution through components | game and team views support this purpose; a game explorer alone does not fulfill the brief |
| modeling philosophy | hockeyviz-style interpretability and decomposition | model assumptions, context, and component meaning must be inspectable |
| long-term product | hockeyviz player cards/components and jfresh player cards | preserve the destination while delivering one defensible component at a time |
| primary statistical question | repeatable ability, informed by prior seasons | estimates can differ from current-season outcomes and can lag abrupt changes in ability |
| observed results | show alongside estimates | retain the distinction between what happened and what the model estimates |
| first audience | the user, then a public audience | one operator; no first-release subscription, account, or multi-user administration system |
| first analytical scope | 5v5 skater chance creation/suppression | finishing, special teams, and dedicated goalie profiles follow separately; no claim of total player value |
| first time horizon | completed season, then current season | establishes a fixed reference before ongoing updates and correction handling |
| eventual freshness | updated by the next morning | no live game service required |
| source access | public-data core; optional paid enrichment later | paid tracking cannot become an undeclared dependency of core results |
| language responsibility | effect for application behavior; python for numerical work | two environments and an explicit exchange contract; one authoritative implementation per calculation |
| data fidelity | preserve truly raw responses and correct discovered defects | transformation cannot overwrite evidence or invent missing facts |

## initial product and scope

the following are engineering/product judgments within the confirmed direction, not additional answers attributed to the user:

- **league and season:** nhl, league-wide, initially the 2025–26 regular season. the official [season reference](https://api.nhle.com/stats/rest/en/season), checked on 2026-09-29, identifies this as a completed season. player estimates require league context; a favorite-team-only model would not suffice.
- **population:** skaters during genuine 5v5 play with both goalies present. other situations remain preserved in source captures but are outside this initial analysis. individual eligibility and insufficient-evidence behavior belong in the metric specification.
- **profile:** separate offensive chance creation and defensive chance suppression, with spatial maps, readable rates or component summaries, and observed results for the same declared selection. observed results mean recorded counts and exposure; an unadjusted on-ice xg total is still model-derived and must be labeled accordingly. use a league-average reference for the first estimates; replacement-level valuation is a different later question.
- **comparison:** support comparing players under the same population, baseline, and units. a compact comparison supports the core question; a generalized custom-report builder is not required.
- **evidence:** display exposure, the observation cutoff, the period the estimate describes, model/data revision, and consequential uncertainty or limitations. the metric specification must distinguish average ability during a season from estimated ability at its end. a profile should distinguish a weak estimate from an estimate of weak performance.
- **history:** earlier seasons supply priors, fitting, and validation as justified by evidence. one displayed season is not permission to fit on that season alone. the earliest usable season is determined by source coverage and model validation, not copied from the old repo.

current-season coverage comes after the completed-season result is credible. eventual next-morning operation means newly admitted games inform the analysis, not merely that a refresh timestamp changes. retrieval, scoring, player-estimate updating, and global model refitting need not share a schedule. architecture must make their cutoffs visible; if an estimate has not incorporated recent games, it is labeled stale or provisional rather than presented as current.

## what interpretability requires

the preference is substantive, not a demand for a particular regression package. a reader should be able to inspect the inputs, reference conditions, component definitions, and composition rules behind a result. preserve spatial differences that a scalar would erase. more coefficients or more panels do not necessarily provide more understanding.

components need valid accounting. a sum must reconcile to its total where the model defines addition; conditional probabilities may multiply, and interactions may prevent an additive interpretation. chance creation, finishing, and other mechanisms must not count the same value twice. do not manufacture a total merely to fill a player card.

interpretability governs model choice among empirically credible candidates; it does not excuse invalid probabilities, leakage, unstable attribution, or misleading uncertainty. simpler or more flexible models may be used as benchmarks. reproducing selected public methods is useful evidence, but matching hockeyviz's private production numbers is not the acceptance criterion.

the resulting quantities are context-adjusted estimates under stated assumptions. inspectable arithmetic does not establish causal identification. historical information stabilizes estimates but introduces assumptions about persistence and aging; sensitivity and validation must address them. [public magnus 9 methodology](https://hockeyviz.com/txt/magnus9EV)

inference is permitted when necessary and supported, with its provenance and assumptions visible. mccurdy's [shot-outcome description](https://hockeyviz.com/txt/xg8) illustrates both interpretable decomposition and imputed inputs. our model must distinguish observations from reconstructions and imputations. excluding incomplete records can also bias the sample, so neither automatic exclusion nor automatic filling is a universal policy.

## source and correction contract

retain original response bodies before parsing, filtering, normalization, or serialization into another shape, with enough source and retrieval metadata to identify the capture. retain full captured game responses even when the current analysis uses only a subset. the precise byte/encoding and storage contract belongs to architecture.

raw evidence may contain upstream mistakes. keep it unchanged; corrections, coordinate normalization, identity resolution, and imputation produce separately attributable derived records. unknown handedness remains unknown until an attributed source or explicitly labeled inference supports a value. corrected historical downloads are new captures, not replacements masquerading as earlier evidence.

every result identifies its input selection, transformation/model revision, and information cutoff. revised evidence must not silently coexist with stale dependent results. preserve enough information to reproduce and explain prior publications. a historical reanalysis must not be represented as a forecast that was available at that historical date.

ordinary development and tests work without the external drive or live upstream requests. maintain a bounded offline fixture corpus of actual captured payloads and explicitly labeled synthetic cases, plus a compact derived dataset for exercising the product. hand-checked facts supplement implementation-generated regression snapshots. none of this substitutes for a training or statistical-evaluation corpus.

the detached dataset and predecessor pipeline remain untrusted until inspected. use [raw-provenance](issues/legacy-raw-provenance.md), [fixture-fidelity](issues/legacy-fixture-fidelity.md), and [external-inventory](issues/external-data-inventory.md) records as admission requirements. improve or replace mechanisms at their responsible layer; do not paper over defects or silently alter the archive.

publicly accessible inputs do not automatically permit unrestricted redistribution. the core must be rebuildable from identified accessible sources; publication of bundled source data requires source-specific review. optional paid inputs must identify their additional coverage and must not silently change the meaning of core metrics.

## success criteria for the first analytical product

1. selecting an eligible skater yields a defensible estimate of 5v5 offensive and defensive contribution, with useful spatial detail and an explicit reference population.
2. observed results and modeled ability remain distinguishable; maps, tables, and any exports describe the same declared selections.
3. comparison makes differences, evidence volume, and uncertainty intelligible without implying that every numerical difference is meaningful.
4. data reconstruction reconciles selected independent facts and handles supported boundary cases without invented observations or silent loss of coverage.
5. the statistical evaluation supports the promised interpretation against honest baselines and checks information leakage, calibration where relevant, stability, and shared-deployment sensitivity. the later model specification sets quantitative acceptance rules before evaluating candidate results.
6. a result can be traced and reproduced; a correction leads to a coherent revised publication or explicit unavailability, with rollback possible.
7. the bounded development dataset exercises real boundaries offline. a full-data run explicitly identifies its larger input and cannot silently substitute fixtures.

visual quality serves these criteria: consistent rink orientation and scales, legible units, deliberate information density, and progressive detail. no teaching workflow is required. the first product is complete when it answers the promised question reliably, not when it reaches a feature count.

## excluded from the first analytical product

finishing or setting skill profiles, special-teams valuation, dedicated goalie profiles, playoff analysis, prospect/other-league coverage, contracts, fantasy recommendations, game forecasts, lineup simulations, total gar/war-style ratings, and paid tracking integrations.

the fuller skater cards, their component families, comparison summaries, and career context belong to the confirmed long-term destination. they are deferred from the first target, not discarded. surrounding products such as fantasy, prospects, or roster simulation are not implied by the card goal. numerical agreement with a particular private model, exact component formulas, and the treatment of an overall total require their own evidence and specifications.

the cost of the initial scope is real: the profile does not explain a player's entire contribution. that limit must be visible. infrastructure/data slices may precede the usable profile, but they are dependencies rather than substitutes for it.

## remaining decisions and their owners

no further user preference is required to complete this brief. unresolved empirical questions are not decisions we can settle by preference.

| remaining matter | owner and timing | what settles it |
|---|---|---|
| effect version, ui framework, storage, artifact/process boundary | engineering, architecture phase | explicit ownership, required queries, reproducibility, local operation, measured workload |
| model family, temporal target, xg/shot definitions, priors, contexts, uncertainty method | statistical design, before the relevant implementation slice | explicit estimand and evidence requirements; benchmarked candidates |
| detailed card reference versions and component expansion order | product/statistical design, as later components are specified | pinned examples and method descriptions; the long-term destination itself is settled |
| trustworthy historical coverage and training horizon | data audit and statistical validation | actual source inventory, reconstruction checks, and held-out evidence |
| exact fixture games and size | first data-contract specification | minimal sufficient real and synthetic case coverage |
| next-morning cutoff, retries, refit/update cadence | architecture and current-season specification | stated freshness contract that the chosen computations can meet |
| hosting, public launch, source-code license, paid inputs | later publication/product decision | a useful personal product and concrete costs/rights; none is a prerequisite for first analysis |

operate for one user with immediate rollback and live repair. do not add generalized workflow infrastructure, a model platform, or distributed services without a requirement they uniquely satisfy. the numerical environment, data exchange, preserved captures, and validation all have real costs; these are accepted for correctness, not excuses to widen the system.

this phase ends with the brief. the next authorized phase must design the architecture and systems; slice specifications follow that, and implementation follows specifications. outline dependencies without exhaustively specifying empirical research in advance. no application code, trained model, or admitted dataset has been produced in this phase.
