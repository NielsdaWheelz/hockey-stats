# statistical methods and scientific contracts

reviewed: 2026-09-29. scope: primary public methodology, historical code, and implications for this project. this is an independent disciplinary review, not advice attributed to the named researchers. linked descriptions establish published methods; they do not establish what currently runs in production. recommendations below retain their research context; the subsequent [brief](../brief.md) settles product purpose and scope.

## the question precedes the number

the central design constraint is to distinguish recorded results, estimated ability, and forecasts. they answer different questions and require different evidence. treating them as interchangeable is a conceptual error that better modeling cannot repair.

| quantity | intended meaning | interpretive limit |
|---|---|---|
| counts, rates, shares | recorded outcomes within a population and exposure | does not isolate responsibility or repeatability |
| expected goals, xg | goal probability conditional on specified information and eligible attempts | does not describe everything that made a chance dangerous |
| regularized adjusted plus-minus, rapm | context-adjusted, regularized player association with on-ice outcomes | adjustment alone does not establish causation |
| goals/wins above replacement, gar/war | component contributions relative to a declared baseline | different baselines and attribution rules answer different questions |
| forecast | distribution of future outcomes given an information cutoff | cannot substitute for an account of realized contribution |

these are our interpretive contracts, informed by the sources below. every published quantity should name its unit, population, timeframe, denominator, baseline, and model version.

## verified differences between the exemplars

reference update checked 2026-09-29: hockeyviz's [2026–27 preview](https://hockeyviz.com/txt/preview2627), headed september 28, 2026, announces rewritten xg and shot-rate models whose methodological articles are still to follow. magnus 9 and xg 8 below are explicit published reference versions, not specifications of those newer models. the preview's update paragraph also contains an inconsistent original-publication year; use the visible heading and retrieval date without silently correcting the source. this does not require waiting for new articles before designing and evaluating our own models.

the younggrens' original war philosophy prioritizes descriptive contribution within a period, including newcomers without requiring their personal nhl history. predictiveness is not its objective. the article originated in january 2019 and was republished in 2021. [war philosophy](https://evolving-hockey.com/blog/wins-above-replacement-history-philosophy-and-objectives-part-1/)

mccurdy's magnus 9 even-strength description, dated august 27, 2025, estimates spatial shot-rate effects with historical priors and aging adjustments. it revised aging treatment, shortened zone effects, and removed goalie rebound terms. it also distinguishes the underlying hexagonal representation from its smoother displayed maps. this is the newer public specification reviewed here, not proof of the current deployed version. [magnus 9](https://hockeyviz.com/txt/magnus9EV)

the historical magnus 8 description, dated august 28, 2024, reports rejecting plausible modifications when they worsened subsequent-season prediction. preserve it for methodological history rather than treating it as the latest specification. [magnus 8](https://www.hockeyviz.com/txt/magnus8EV)

our inference: retrospective attribution and persistent-ability estimation are both legitimate, but their outputs must carry different labels. the first product slice should choose an explicit question; it need not commit the whole project to one philosophy.

## mechanisms worth borrowing

the [shot-map guide](https://hockeyviz.com/howto/shotMap) describes an older unblocked-shot population, while magnus 9 includes blocked attempts with inferred origins. do not combine these descriptions into an allegedly version-independent definition of hockeyviz's metric. the guide also illustrates how event-context-dependent danger can be represented spatially; spatial modeling need not be location-only modeling. our own population and map-to-summary accounting must be explicit. [shot-location evidence issue](../issues/shot-location-evidence.md)

blocked-origin appendix checked 2026-09-29: [xg 8](https://hockeyviz.com/txt/xg8) assigns probabilities across candidate origin hexes using proximity to the block and alignment toward the net. it does not simply relocate every block to one guessed point. this is a published geometric baseline, not independently verified origin recovery. the user has selected imputation; our estimator and sensitivity evidence remain to establish.

mccurdy's may 26, 2025 xg description separates four conditional shot outcomes: avoiding a block, reaching the net, avoiding a freeze, and scoring rather than producing a rebound. the product yields scoring probability. its framework excludes shots against an empty net and penalty/shootout attempts. the decomposition makes assumptions inspectable and admits that some prior choices are heuristic. [xg 8](https://hockeyviz.com/txt/xg8)

evolving hockey's published 2018 xg work uses boosted trees and separate strength situations. it reports cross-validation alongside an unseen subsequent season, using auc and log loss. these results illustrate why evaluation populations matter; a headline score without its sample definition is weak evidence. [historical xg method](https://evolving-hockey.com/blog/a-new-expected-goals-model-for-predicting-goals-in-the-nhl/)

its rapm glossary describes duration-weighted stint regressions. substitutions delimit stints; whistles need not. its charts omit defensive goals-against ratings because goalie effects compromise their interpretation. [rapm glossary](https://evolving-hockey.com/glossary/regularized-adjusted-plus-minus/)

the original gar pipeline uses long-term rapm as a target for a separate statistical plus-minus model. it is not merely single-season rapm multiplied by minutes. [war process](https://evolving-hockey.com/blog/wins-above-replacement-the-process-part-2/)

the original offensive components favor realized goals, while defensive components use expected goals against to reduce goalie contamination. that compromise exposes the tension between descriptive attribution and incomplete observation. [war decisions](https://evolving-hockey.com/blog/wins-above-replacement-replacement-level-decisions-results-and-final-remarks-part-3/)

replacement level and goals-to-wins conversion are additional declared constructions, not natural constants. keep them visible beneath any total. [gar glossary](https://evolving-hockey.com/glossary/goals-above-replacement/)

## foundations and limits

macdonald's 2012 paper develops ridge-adjusted player ratings using several outcome measures. gramacy, taddy, and jensen's 2015 paper supplies a logistic formulation. thomas, ventura, jensen, and ma's 2013 work instead models competing scoring processes, addressing hockey's rare goals and frequent substitutions directly. these are alternative formulations, not a mandatory stack. [ridge](https://arxiv.org/abs/1201.0317), [logistic](https://arxiv.org/abs/1510.02172), [competing processes](https://arxiv.org/abs/1208.0799)

our assessment: regularization stabilizes sparse, correlated evidence but cannot manufacture independent observations of players who nearly always play together. fitted effects also depend on omitted variables, selection, and the target chosen. coefficient uncertainty alone does not capture all those limitations.

measurement deserves equal attention. schuckers and macdonald's 2014 rink-effects research documents differences in event recording. novet's 2019 passing-data model investigates information missing from conventional play-by-play. these historical findings justify contemporary checks; they do not establish the quality of today's feeds. [rink effects](https://arxiv.org/abs/1412.1035), [pre-shot movement](https://hockey-graphs.com/2019/08/12/expected-goals-model-with-pre-shot-movement-part-1-the-model/)

## recommended contracts and validation

each metric should have one compact specification: question, estimand, population, unit, inputs, exclusions, adjustments, information cutoff, validation, known limitations, and version. each result should remain traceable to its source snapshot and transformation/model versions. begin with files and manifests; a distributed provenance service would be disproportionate.

validation must follow the claim:

- xg: compare with a simple distance/angle baseline; use chronological holdouts with games kept together; report log loss, brier score, calibration, and relevant subgroup behavior. auc tests ordering, not calibrated probabilities.
- player estimates: verify exposure and stint reconstruction; inspect sensitivity to regularization and shared deployment; compare with simple baselines. report model uncertainty where supportable without implying it covers every missing variable.
- descriptive totals: reconcile component arithmetic and selected observed totals; explain baseline choices and sensitivity. forecast accuracy alone cannot establish correct attribution.
- forecasts: freeze the information cutoff, retain distributions, and assess calibration and proper probability scores. mccurdy's 2025 prediction contest provides a concrete distribution-scoring example. [prediction contest](https://hockeyviz.com/txt/predictionContest2526)

the local fixture should contain a small set of complete games with source payloads and explicit expected results. choose cases that exercise strength changes, substitutions, overtime, corrections, and missing fields. a few synthetic cases can isolate boundaries. trade-off: the fixture verifies transformations and integration, not training quality or league-wide statistical validity. representative training data remains a separate requirement.

## pr03 candidate and information boundaries

follow-up, 2026-09-29: the user chose [03a workflow implementation](../specs/03a-chance-workflow.md), with real training and scientific acceptance in separate [03b](../specs/03b-training-acceptance.md). the drive was deferred at that stage. the specification fixes a candidate; it does not certify it.

direct read-only inspection of the three admitted `play-by-play/body.bin` files found 362 timed attempts outside shootouts: 111 blocks and 251 unblocked attempts. all 111 blocks lack `shotType` and `goalieInNetId`; all 251 unblocked attempts have both. all have x/y coordinates. these counts include other strengths, so they are not training-population counts. reproduction: filter each file's `plays` by `typeDescKey` in `blocked-shot/missed-shot/shot-on-goal/goal` and non-`SO` `periodDescriptor.periodType`; count field presence under `details`. opposing goalie identity instead comes from the already interpreted on-ice report.

consequence: a naive “missing shot type” feature identifies the block outcome in these examples. omit shot type from the first predictor set; do not replace it with a missingness dummy. observed block locations can support retrospective reconstruction, but cannot enter an allegedly outcome-blind prediction through an inferred origin. tip/deflection coordinates also remain proxies requiring audit, not automatic relocation. [open location evidence](../issues/shot-location-evidence.md)

the council recommends a small joint model: a categorical origin law, a fixed geometric observation law for block locations, and conditional probabilities of avoiding a block and scoring given an unblocked attempt. marginalize the unknown origin in the observed likelihood, then derive its posterior. this is our proposed forward observation model, not hockeyviz's published inverse imputer. the probability arithmetic follows ordinary [finite-mixture marginalization](https://mc-stan.org/docs/stan-users-guide/finite-mixtures.html). origin assumptions remain weakly constrained: equally plausible kernels/priors can yield similar observed fits and different reconstructed locations.

[xg 8](https://hockeyviz.com/txt/xg8) motivates interpretable conditional stages and origin distributions. our first candidate collapses later outcomes into one unblocked conversion stage, deferring goalie-freeze and other extra components. mccurdy's [september 2026 preview](https://hockeyviz.com/txt/preview2627) announces further model changes with methods to follow; an older public article is evidence, not a verified description of current production.

reference opportunity averages each training shooter–goalie pair's product of conditional probabilities, then averages over the reconstructed origin distribution. it is not a factual forecast conditional on a known block. evaluate factual unblocked conversion against a distance/angle benchmark and outcome-blind all-attempt predictions against a score/role benchmark. never use post-outcome imputed locations only on one side of a purported fair forecast comparison.

review conclusions: statistical review required a coherent observation likelihood and explicit missingness assumptions; systems review required a complete saved model with bounded numerical work, not an estimator framework; content review required distinct labels for predictions, reference values and software versus scientific evidence. all supported separate 03b. the remaining disagreement is empirical: whether the small candidate's omitted context and uncertain origins support useful player analysis. source audit, development and untouched confirmation must decide it. no user preference can settle that question.

## pr03b evidence protocol

follow-up, 2026-09-30: 03a is merged. the [external audit](external-corpus-audit.md) found projected boxscores/rosters and no per-event on-ice reports; the user chose fresh 2023–24 through 2025–26 acquisition. [03b](../specs/03b-training-acceptance.md) specifies development on 2024–25 after fitting 2023–24, confirmation on 2025–26 after the frozen two-season refit, and a separate final three-season retrospective fit. the three exposed fixtures are excluded from confirmation. native commands use the mounted drive directly; no bulk run has started.

the council agrees on paired game-level resampling of pooled losses, separate calibration checks, fixed sensitivity alternatives and one written scientific decision. proper scores combine calibration and resolution; improvement does not alone prove calibration ([official guidance](https://scikit-learn.org/stable/modules/calibration.html)). choosing thresholds or candidates repeatedly against confirmation creates selection bias ([cawley and talbot](https://www.jmlr.org/papers/v11/cawley10a.html)). practical tolerances therefore belong to development and must be frozen before confirmation, not guessed from fixtures.

review corrections: aggregate assessments need identical consumed inputs and preparation identity to establish matched populations; streaming score comparisons use `(game_id, source_index)` because source event ids can be null. undefined bootstrap denominators remain explicit. the fixed sensitivity set must also be checked on the target confirmation population; development-only robustness does not establish target-season support. neither robustness nor good factual predictions establishes origin accuracy. a supported recipe still needs a separately identified final fit, whose training mix defines its reference.

## public availability and remaining decisions

the [2026-09-30 field-to-feature audit](model-input-audit.md) explicitly compares versioned public methods with our implemented predictors and source omissions. neither public-data access nor a shared method family establishes equal information sets. use this comparison when specifying the next model; do not infer that the first candidate implemented the public reference recipes.

03c follow-up, 2026-09-30: the [source/scientific audit](chance-03c-source-audit.md) corrects the api-only type-availability assumption, isolates the saved model's kernel/block-avoidance coupling, and reviews which earlier gates address physical accuracy versus model-conditional usefulness. 03b's rejection is preserved. source revision comes first; a new model and claim-specific validation design require their own specification after the type/population audit. the exposed seasons cannot be relabeled untouched confirmation.

[evolvingwild/hockey-all](https://github.com/evolvingwild/hockey-all) contains historical xg and other research code. its existence does not establish a current production implementation or blanket reuse permission. evolving hockey's [about page](https://evolving-hockey.com/about/) lists versions dated 2019–2020; treat that as public documentation with its own vintage. a current public hockeyviz production repository was not verified.

evolving hockey's [terms](https://evolving-hockey.com/terms-of-use/) distinguish attributed statistical models created from its data from redistribution of the underlying data. its downloadable data therefore should not become our public fixture by assumption. record source-specific provenance and permissions before copying material into distributable artifacts.

the archived repository's source dossiers are historical leads. retain their dates and provenance, and recheck claims before promoting them into this knowledge base. avoid converting repeated citation into apparent verification.

the unresolved product decisions are the first supported question, its audience, eligible seasons and strength states, and whether initial displays use independently derived observations or licensed modeled outputs. the unresolved scientific decisions are the estimand, data sufficiency, and acceptance evidence. architecture should follow those answers; neither a preferred language nor an impressive model should decide them silently.
