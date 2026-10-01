# chance-2 training and assessment protocol

status: implementation and fitting authorized by the user on 2026-09-30. this protocol precedes development fitting. pilot measurements and development selections will be appended before its external byte freeze; transfer assessment must not precede that freeze. no scientific result is asserted here.

authority: [03e specification](../../specs/03e-training-assessment.md), revision `b27df7b3a691889d0000a1f1f72d655b27cdb516`; `inputs/study-setup.json` records the specification's exact sha256. [the brief](../../brief.md) fixes the quantity and conditional research boundary. 03b's rejection remains unchanged. implementation authorization supersedes the specification's earlier authorization status, not its requirements.

## evidence and execution

external run root: `/Users/nnandal/Documents/code/hockey-stats-03e-runs`. `inputs/` owns explicit selections, configurations, frozen protocol copies and execution evidence; `corpora/`, `fits/`, `assessments/`, `scores/`, `reviews/` are sibling outputs. `logs/` preserves command output and resource measurements. fits run sequentially. no source payloads are overwritten, transformed records labeled raw, or excluded games silently removed.

raw root: `/Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930`. all six game sources and four season references remain identified by their original receipts. each season contains 1,312 inventoried regular-season games. the full older corpus envelopes are schema 2 and incompatible with native chance-2 preparation. the partial `flub-corrected` corpora are case studies, not substitutes for full-season admission. rebuild every full inventory through `hockey-stats-corpus` using unchanged clean `b27df7b` source interpretation/reconstruction, outside raw directories. its corpus implementation identity and actual game dispositions remain evidence. models, evaluations and reviews separately identify their executing implementation.

all three seasons were previously examined, including scientific work on chance-1. chronological disjointness prevents direct fitting leakage; it does not undo research exposure or model-selection bias. these are retrospective fit-held-out checks, never untouched confirmation. the [selection-bias analysis](https://www.jmlr.org/papers/v11/cawley10a.html) explains why selection uncertainty remains outside these intervals.

| selection file under inputs | seasons / games | dates | responsibility |
|---|---|---|---|
| `pilot-train.json` | eight earliest games in each development-training season; 16 total | 2023-10-10 through 2024-10-09 | capacity only |
| `pilot-assess.json` | first eight development-assessment games | 2025-01-01 through 2025-01-02 | capacity and positive research review verification |
| `development-train.json` | all 1,312 in 2023–24; 600 in 2024–25 | 2023-10-10 through 2024-12-31 | three bounded recipes |
| `development-assess.json` | remaining 712 in 2024–25 | 2025-01-01 through 2025-04-17 | recipe and benchmark selection |
| `transfer-train.json` | both complete earlier seasons; 2,624 | 2023-10-10 through 2025-04-17 | frozen family |
| `transfer-assess.json` | all 1,312 in 2025–26 | 2025-10-07 through 2026-04-16 | retrospective seasonal transfer |
| `final-train.json` | all three seasons; 3,936 | 2023-10-10 through 2026-04-16 | admitted members only |
| `final-score.json` | all 1,312 in 2025–26 | 2025-10-07 through 2026-04-16 | matched 2025–26 reference opportunity |

canonical date, then game-id ordering; whole games stay together. the native evaluator additionally requires disjoint ids and assessment dates strictly later than training. pilot scoring uses its assessment selection, retaining the pilot model's 2024–25 joint matchup reference. pilot scoring is capacity evidence, not a final opportunity artifact. the three old fixture exclusions are not applied.

before any fit, reconcile recognized attempts, reconstructed genuine-5v5 attempts, chance-2 eligibility, disposition-partitioned goals, nonexclusive reasons, original/model types, prior-context failures, source drift, unlinked eligible events and unresolved elapsed time. source/identity errors stop admission; ordinary located source gaps remain visible. attribution requires compatible exposure and is owned by 04. no excluded-population claim follows from included-population calibration.

## bounded choices

`anchor.json`, `weaker.json` and `stronger.json` contain the specification's exact schema-2 numerical settings. weaker/stronger multiply every ridge, smoothing and annual-change penalty by 0.5/2; no kernel or numerical tolerance changes. native starts and accepted-state recovery remain intact. an unconverged fit supplies diagnostics, not a model candidate.

primary selection uses minimum pooled held-out observed-record negative log likelihood among converged development recipes without decisive applicable calibration failure. exact ties prefer anchor, stronger, weaker. insufficient precision in small development groups does not manufacture decisive failure. no survivor stops the study. select each goal benchmark independently by its own development log loss with the same tie order. freeze both benchmark labels and use their saved benchmark sums for every subsequent paired comparison. the marginal-unblocked outcome has no comparator. record recipe and comparator identities separately.

the transfer family is the three penalty recipes plus four one-parameter changes to the selected primary: distance 10/40 at direction 4; direction 2/8 at distance 20. no cartesian search, alternative replacement or post-transfer primary substitution. penalty changes confound their bundled mechanisms; likelihood comparisons do not validate latent origins.

`inputs/kernel-implications.json` evaluates the actual 656-cell finite-rink forward law before fitting. uniform grid-origin weighting is a diagnostic convention, not the observed origin population. its average conditional displacement is 16.12/31.21/46.74 feet for distance scales 10/20/40 at direction 4; means vary substantially with origin and rink truncation. at distance 20, expected goalward cosine is 0.767/0.892/0.947 for direction 2/4/8. the distance parameter is not mean displacement. the native law normalizes over possible block-contact cells for each origin.

judgment: this range is plausible as a declared stress experiment for an unverified contact/displacement law: short and long movement and weaker/stronger goalward alignment expose consequential assumptions while retaining finite-rink support. it is not a measured release-to-block distribution, confidence region, or validated physical bound. broad support may accommodate rebounds, tips, recording proxies or deviations from a straight path; their actual mechanisms are not identified by the kernel. representative independent geometry remains absent. [xG 8](https://hockeyviz.com/txt/xg8) motivates differentiated geometry/context/execution regularization; neither its parameterization nor its priors validate ours.

## criteria and uncertainty

the specification's margins, quantities, group families, contributing-game minimum and conservative proper-loss rule remain unchanged. use twenty fixed native probability bins and native additive game/group summaries; never replay predictions in the reviewer. tip distance/below-goal-line groups assess unblocked conversion only. threshold each group against the entire relevant probability population: at least 5% of eligible attempts or predicted positive mass. overlapping group families are not independent replications.

freeze development-triggered ids per candidate and quantity; retain benchmark diagnostic groups without turning a comparator into the admission target. the same trigger applies in transfer. represented season/basis categories are stage-dependent. empty prediction bins and actor categories make no claim. a vanished hockey/source group first requires explicit coverage reconciliation. observed positive count never selects or excludes a group.

goal calibration: overall ±0.0025 and consequential groups/bins ±0.01. marginal-unblocked calibration: overall ±0.01 and consequential groups/bins ±0.03. support requires the whole interval inside the margin and at least 100 contributing games. all-one-label populations cannot establish support from a degenerate empirical bootstrap. an interval wholly outside a margin rejects even without 100 games; overlap is insufficient. inspect seven- and fourteen-calendar-day sensitivities under the same criteria; neither adverse intervals nor lost support may be discarded.

candidate-minus-frozen-benchmark log-loss and brier differences are pooled over counts. an interval wholly above zero rejects. an upper bound at/below zero supports no excess; overlap is unresolved. admission requires positive calibration support and no decisive proper-loss inferiority; it does not require proved comparator equivalence. the cost is conservative: a useful model may be withheld by a small decisive loss without an independently justified degradation allowance. neither better loss nor map stability waives calibration failure. [probability-calibration documentation](https://scikit-learn.org/stable/modules/calibration.html) distinguishes probability reliability from proper-loss improvement.

resampling: 2,000 paired draws, `PCG64`, seed `3032026`, linear 95% percentile intervals. retain selected zero-contribution games, pool sums over counts on each draw, and never average game means. any zero-denominator draw makes the interval null with count/reason; no redraw or deletion. dependence blocks are nonoverlapping seven/fourteen calendar days anchored at the assessment's first date, including empty days and the final partial block; sample the original block count. report contributing games and blocks separately. these horizons are sensitivities, not certified independence. monthly discrepancies are descriptive. pointwise intervals exclude simultaneous, fitting, selection and origin-law uncertainty.

before transfer, append development counts and compatible supported exposure to translate the calibration budgets. unlinked events receive no invented exposure. conversion-weighted illustrations of marginal-unblocked error are illustrations, not propagated-error bounds. unacceptable practical consequences require a new disclosed protocol round; thresholds cannot change in this campaign.

## interpretation and stopping

matched comparisons require identical selected evidence, event/status streams, geometry, training populations, reference season and joint matchup counts/weights. final three-season versus transfer two-season results have different references and are descriptive. stream complete blocked/unblocked mass, original-type/role strata, posterior variation and attributable extremes. conserve event and spatial mass; null ratios retain absolute changes.

the sensitivity triggers are obligations for 04, not automatic probability rejection: mean absolute event change >0.0025, absolute total change >5%, or absolute spatial-mass change >10% of primary mass. preserve every admissible member, including map-changing members. do not average the family into a validated surface or call its range a confidence interval. decisive probability rejection may remove a member; numerical failure, nonexecution or insufficient required calibration support leave the planned family unresolved and withhold handoff.

tips retain original `tip-in`/`deflected` counts, goals, opportunity and spatial mass by season and blocked status. unblocked distance uses original attacking coordinates before quantization; below-goal-line means `x > 89`. block coordinates never become release proxies. kernel stability cannot establish tip-location robustness. consequential unresolved tip geometry travels to 04 as a publication constraint; 04 must justify sensitivity or withhold affected player conclusions.

omission review uses source evidence and available residuals, without adding features: source/season/type geometry drift; home/away and score/time residuals; prior-action proxy semantics; sequence/shift-age feasibility; fresh-reference handedness and temporal pooling. report absent evidence explicitly with owners. source ordering and integer-second clocks do not establish possession or puck trajectories; unresolved elapsed exposure prevents unsupported shift-age claims. selected-season average ability and historical player priors remain 04 responsibilities.

success is attributable evidence and either `conditional_research_handoff` or `withheld`. a stopped capacity or development stage is not a transfer probability rejection. mark dependent stages not run, preserve logs/checkpoints and report the actual blocker. no handoff index on withholding. a handoff requires primary admission, complete admitted final models/scores, matched final sensitivity, a written decision and the exact schema-1 external index linking their digests. no publication is authorized.

## measurements and freeze

pending execution. append actual pilot preparation/fit/evaluate/exact-score wall times, peak memory, bytes, origin/avoidance context-group counts and reference-pair counts; then first complete development-fit cost. fixture timings cannot establish season cost. preserve accepted numerical checkpoints. the development appendix must identify the selected primary, independently selected benchmarks, consequential ids, source/omission judgments and practical budgets before copying these bytes and their sha256 externally for transfer.
