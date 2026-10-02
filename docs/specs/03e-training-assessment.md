# pr03e — revised training and assessment

status: **implementation and bounded real-data assessment complete; decision `withheld`.** the user authorized implementation and fitting on 2026-09-30. [software verification](../research/chance-03e/verification.md) is complete; all three development recipes completed fitting, evaluation, scoring and comparison, then decisively failed declared all-attempt calibration. the [decision](../research/chance-03e/decision.md) records no surviving primary or handoff; dependent transfer, kernel variants and final fits were not run. the [protocol](../research/chance-03e/protocol.md) retains specification revision `b27df7b3a691889d0000a1f1f72d655b27cdb516` and its original digest as study authority; the specification body, requirements and criteria are unchanged. [03d](03d-chance-revision.md) merged in `af95c88`; its [fixture checks](../research/chance-03d/verification.md) establish software behavior. 04 and publication remain unauthorized. [03b's rejection](../research/chance-03b/decision.md) remains unchanged. [brief](../brief.md) · [plan](../plan.md)

## target and limits

produce a reproducible decision: `conditional_research_handoff` or `withheld`. a handoff supplies retrospective 5v5 opportunity inputs for 04 research, conditional on a declared family of assumptions. it does not approve publication, player attribution, physical release locations or a live forecast.

the user confirmed both boundaries: use the existing, previously examined seasons; carry scientifically admissible alternatives into 04 even when their opportunity maps differ materially. 04 must test player magnitudes, signs and spatial conclusions across that family. different maps neither prove physical error nor establish that differences cancel.

retain the 03d quantity: location, type and supported preceding-play context belong to created opportunity; standardize modeled residual execution through the target-season joint matchup reference. positive block opportunity is not a factual goal probability conditional on a known block. no unblocked-only substitution.

scope: native preparation/fit/evaluate/score, bounded recipe selection, diagnostics, assumption comparisons and a written decision. no new estimator, coordinate correction, feature search, acquisition campaign, web service, job runner, public cards or lasting test harness. rejection or insufficient evidence completes the study; it does not authorize indefinite tuning.

## inputs and chronology

use `/Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930`: all 1,312 inventoried regular-season games in each of `20232024`, `20242025`, `20252026`, with six game sources and admitted references. reuse compatible corpus artifacts; regenerate older reconstruction envelopes through native admission, outside raw directories. no hdd or recapture is required. remove 03b's three fixture exclusions from this new study; they cannot create untouched data.

before fitting, reconcile inventory/dispositions, recognized versus reconstructed-5v5 versus chance-eligible attempts, goals/excluded goals, original types, context failures, season differences, unlinked events and unresolved elapsed seconds. reasons may overlap; dispositions must partition. investigate selective exclusions against 03c's attributable facts. source gaps remain located; input/identity errors cannot silently disappear from selections. no claims about excluded populations.

| stage | training / assessment | purpose |
|---|---|---|
| capacity pilot | first eight chronological development-training games from each represented season | measure preparation, fit, evaluation and exact reference scoring; no scientific claim |
| development | all 2023–24 plus 2024–25 games before `2025-01-01`; assess remaining 2024–25 games | exercise two-season penalties and within-season completion; three recipes |
| frozen transfer assessment | both complete earlier seasons; assess all 2025–26 | assess seasonal carry-forward; seven recipes maximum |
| conditional final fits | all three seasons; score 2025–26 | matched target-season reference artifacts for 04; seven fits maximum |

use canonical game dates, with game-id tie ordering; keep whole games together. pilot evaluation uses the first eight development-assessment games. native `evaluate` retains disjoint ids and dates strictly after training. all seasons are research-exposed: these are fit-held-out retrospective checks, NOT fresh confirmation. [selection-bias basis](https://www.jmlr.org/papers/v11/cawley10a.html)

write `docs/research/chance-03e/protocol.md` before development: identify this specification revision, actual selections/configs and pilot measurements. after development, append selected recipes, exact consequential groups, benchmark labels and source/omission judgments; freeze its bytes/digest externally before transfer assessment. criteria below do not change in response to failure. a substantive revision is a disclosed new round, outside this bounded campaign.

## recipes and selection

config schema 2; anchor kernel distance `20` feet, direction `4`. optimizer/em limits `2000`; `optimizer_ftol=1e-10`, `optimizer_gtol=1e-6`, `em_relative_tolerance=1e-8`, `em_posterior_tolerance=1e-6`, `objective_decrease_tolerance=1e-10`. retain native starts, convergence and accepted-state recovery. unconverged output is not a candidate; numerical repairs need evidence, not relaxed scientific requirements.

| anchor penalty parameters | value |
|---|---:|
| `ridge_origin_base`, `ridge_cell`, `ridge_benchmark` | `0.25` |
| `ridge_origin_factor`, `ridge_type_cell` | `1` |
| `smooth_origin`, `smooth_cell`, `ridge_context`, `ridge_shooter` | `4` |
| `change_shooter`, `ridge_goalie` | `16` |
| `change_goalie` | `64` |

these expert hypotheses permit broad geometry, smaller contextual/actor effects and slower annual changes. an isolated `λβ²/2` penalty corresponds to scale `1/√λ`; combined penalties do not have those exact marginal standard deviations. they are not hockeyviz constants or established priors. [published xg8](https://hockeyviz.com/txt/xg8) motivates differentiated spatial/human/history penalties and bounded neighboring comparisons; its parameterization differs.

development fits `anchor`, `weaker` (every penalty ×`0.5`) and `stronger` (×`2`); kernel/numerical settings stay fixed. among converged candidates without decisive development calibration failures, select smallest held-out mean observed-record negative log likelihood; exact ties prefer anchor, stronger, weaker. smaller development groups need not establish equivalence to permit the larger assessment. no surviving candidate means stop and report why.

select each benchmark independently from those three fits by its own development goal log loss, with the same tie order. freeze both labels: later candidates compare with those recipes, not whichever bundled comparator flatters them. joint record likelihood selects the observation model; it does not validate origins.

the frozen family contains the three regularization recipes and four changes to the selected primary: distance `10` or `40` with direction `4`; direction `2` or `8` with distance `20`. each changes one kernel parameter. regularization recipes change a bundle, so their differences cannot isolate a particular penalty. no cartesian search. the kernel range is a declared stress range, not a confidence region; describe its finite-rink displacement/direction consequences and plausibility before assessment. indefensible assumptions require revision, not a claim of validated physics.

## probability evidence and admission

assess three native quantities: unblocked conversion at a recorded proxy; recorded-context all-attempt goal probability; recorded-context marginal unblocked probability. the latter two integrate the origin prior without focal location/outcome/posterior. reconciled type and eligibility remain retrospective measurements. lower proper loss alone does not establish calibration. [calibration basis](https://scikit-learn.org/stable/modules/calibration.html)

use the existing twenty fixed probability bins and subgroup families: original/model type, score, role, home/away, recent context, season and stage-specific actor/season support. a bin/group is consequential if it carries at least 5% of its quantity's eligible attempts or predicted positive mass. freeze development-triggered ids; the same trigger additionally applies in assessment. apply requirements to represented groups: development season/basis categories absent by construction are not impossible assessment gates; absent prediction bins or actor-support categories have no claim. a vanished hockey/source group first requires coverage reconciliation, not an automatic exemption. no observed-goal-count exclusions. empty/rare groups remain visible limitations.

| criterion | prospective requirement / meaning |
|---|---|
| goal calibration, both quantities | predicted-minus-observed within `±0.0025` overall and `±0.01` per consequential bin/group |
| marginal unblocked calibration | within `±0.01` overall and `±0.03` per consequential bin/group |
| calibration support | whole 95% interval inside the margin and at least 100 contributing games; no arbitrary attempt-count floor. all-one-label groups cannot establish support through a degenerate nonparametric bootstrap; retain them as insufficient evidence |
| calibration failure | interval wholly beyond a margin rejects, regardless of support minima; boundary overlap is insufficient |
| comparative log loss and brier | candidate-minus-frozen-benchmark pooled differences; interval wholly above zero rejects admission. upper bound at/below zero supports no excess for that comparison; overlap remains unresolved |

the calibration budgets mean a quarter/one additional goal per hundred eligible attempts in the respective probability population, or one/three additional unblocked outcomes per hundred attempts. these are project judgments, not literature standards. before assessment, translate their scale using development counts and compatible exposure; conversion-weighted unblocked-error illustrations explain possible consequences, not error bounds. do not invent exposure for unlinked events. unacceptable practical consequences require explicit protocol revision before proceeding.

admission requires positive calibration support for applicable overall/consequential criteria and no decisive pooled proper-loss inferiority under either loss. unresolved superiority may accompany admission; it does NOT establish comparative equivalence. this differs from 03b's requirement to establish zero excess under every comparison. without an independently justified positive degradation allowance, even a small decisive loss can withhold a useful model; that conservative cost is explicit. fit completion, lower pooled loss or a favorable alternative cannot waive calibration failure.

retain 2,000 paired whole-game bootstrap draws, `PCG64`, seed `3032026`, 95% linear-percentile intervals. pool sums over counts on every draw; never average game means. keep selected zero-contribution games. any zero-denominator draw makes that interval null, with undefined count/reason; no redraw or silent removal. intervals condition on fitted models/resampling assumptions and exclude fitting, selection and origin-law uncertainty.

repeat consequential checks with nonoverlapping seven- and fourteen-calendar-day blocks anchored at the assessment's first date, including empty days and the final partial block. resample the original number of blocks with replacement and pool their sums/counts; retain contributing-game and contributing-block counts separately. these are dependence sensitivities, not certified horizons. an adverse result or loss of required calibration support prevents admission: record rejected or insufficient evidence; never choose the favorable blocking. monthly discrepancies are diagnostic. pointwise intervals do not establish simultaneous coverage.

the primary must meet admission criteria before final fits. apply the same rules to alternatives and record every disposition. decisive probability rejection excludes an alternative from admission, while retaining its diagnostic evidence. numerical failure, missing execution or insufficient calibration support for any required alternative leaves the planned family unresolved and withholds handoff; it cannot quietly disappear. do not substitute a new primary after seeing 2025–26, trim difficult events or drop map-changing members.

## spatial, measurement and omission evidence

matched sensitivity requires identical event keys/statuses, source/selection identities, grid, training population, reference season and joint matchup counts/weights. each fit supplies its own coefficients; exact reference averaging remains native. two-season versus final three-season comparisons have different references and are descriptive, not matched sensitivity.

stream blocked/unblocked rows separately. report mean/max absolute event-value changes, signed total change, `sum(abs(alternative cell mass − primary cell mass))`, normalized spatial shape change and blocked-posterior total variation. additionally aggregate by original type and role; retain attributable extremes. conserve event/spatial mass. ratios require nonzero denominators; absolute changes remain available.

mean absolute event change above `0.0025`, absolute total change above `5%`, or absolute spatial-mass change above `10%` of primary mass triggers explicit downstream robustness obligations, NOT automatic research rejection. these preserve useful 03b diagnostic scales without reusing its verdict. posterior movement and isolated maxima locate concerns, not physical error. retain all admissible members, including different maps. do not average alternatives into a supposedly validated surface or call their range a confidence interval.

tips need a separate measurement ledger: by original `tip-in`/`deflected`, season and blocked/unblocked status, report counts, goals, opportunity totals and spatial mass. eligible unblocked tips additionally define `tip_distance` bands `0_10`, `10_20`, `20_40`, `40_plus` (left-closed, right-open feet) and `tip_below_goal_line: false|true` (`x>89`). distance is `hypot(89−attacking_x, attacking_y)` before quantization; predictions retain native quantization. these groups assess ONLY `unblocked_conversion`, with candidate/benchmark metrics. they partition the unblocked tip subset, not all attempts; do not calibrate all-attempt or marginal-unblocked probabilities after selecting on the observed outcome. retain original-type breakdowns; any consequential tip group receives the conversion criterion. block coordinates are not tip-location proxies, and distant tips are not automatically errors. quantify dependence on proxies; kernel variants do not bracket tip-location error. consequential unresolved tip geometry travels to 04 as a publication constraint, not a caveat erased by pooled calibration.

04 must establish whether affected scalar/spatial player conclusions survive justified tip-location sensitivity or withhold those conclusions. the ledger identifies dependence, not robustness; kernel-family stability cannot discharge this obligation. no new tip-coordinate estimator is authorized here.

address the 03d omission list: source/season/type geometry drift, home/away and score/time residuals, prior-action proxies, sequence/shift-age feasibility, handedness and temporal pooling. use existing records, residuals and source evidence; do not implement every omitted feature. unresolved mechanisms need a limitation or issue with evidence/owner. physical-origin accuracy remains unestablished without representative independent geometry; no replay subscription or annotation campaign is assumed.

## architecture, interfaces and ownership

manual composition: `corpus → selection → fit → evaluate/score → comparison → decision`. use an external run directory with sibling `inputs/`, `corpora/`, `fits/`, `assessments/`, `scores/`, `reviews/`. selections/configs/protocol copies/evidence belong in `inputs/`, not the common parent. existing commands require output parents to exist and outputs outside input directories.

| interface | contract |
|---|---|
| `hockey-stats-corpus --reference … --games … --out …` | existing season admission; new directory |
| `hockey-stats-chance fit --selection … --config … --out … [--resume …]` | unchanged fit/checkpoint semantics; model written last |
| `hockey-stats-chance evaluate --selection … --model … --out …` | new json FILE; evaluation envelope becomes schema 3 |
| `hockey-stats-chance score --selection … --model … --out …` | new directory; existing schema-2 rows/score completion contract |
| `uv run python research/chance_review.py --evidence … --out …` | existing entry point; new directory; evidence/comparison schema 2 |

hard-cut the retained reviewer from chance-1 assumptions to `chance-2`: population names, `outcome`, `observed_positive_count`, actor/context groups and reference season. models/configs/checkpoints/score rows remain schema 2; only evaluation becomes schema 3 for added evidence. scientific runs require an identified clean implementation; regenerate cheap compared evaluations under one revision when needed. historical reports use historical git revisions. no compatibility layer or duplicate predictor.

native evaluation adds additive `per_game[].groups` using the global category/value structure: each applicable probability population/predictor supplies `outcome`, `count`, `observed_positive_count`, `predicted_probability_sum`, `log_loss_sum`, `brier_score_sum`. include zero-count groups for selected games; reconcile to global summaries. retain existing per-game overall calibration bins; no per-game subgroup bins. add the named tip groups globally/per game, with their restricted conversion population and subset reconciliation above. research consumes sums, without replaying predictions or preparation.

`evidence.json` schema 2 retains `purpose: research`, absolute `protocol`, `assessments: [{label,path}]`, optional `scores: [{label,path}]` with `reference_score`, and `resampling: {draws:2000,seed:3032026}`. add `benchmarks: {unblocked_conversion:label, all_attempt_recorded_context:label}` exactly when assessments are nonempty; labels identify supplied entries. use their saved benchmark sums for every paired comparison; marginal unblocked has no benchmark. allow one score for coverage/tip/absolute-mass summaries: it references itself, pairwise results are empty with reason `no compatible alternative supplied`, and comparison-only figures are omitted with that reason. pilot-only assessment review may use anchor for both benchmarks and omit scores. one review bundle per cohort; incompatible sources/coverage/order/geometry or references cannot become paired evidence.

`comparison.json` schema 2 retains evidence/protocol/artifact digests, separate executing/model identities, counts, intervals/missing reasons, figures and sensitivity. add selected benchmark identities, outcome-specific calibration, subgroup/dependence summaries and `reference_season`. native outputs retain `scientific_assessment: not_performed`; the written decision owns the verdict. malformed/old/nonfinite/incompatible inputs fail visibly. write comparison last after figures succeed; no automatic acceptance service.

| owner / files | responsibility |
|---|---|
| numerical: `analysis/src/hockey_stats/chance_evaluation.py` | shared grouping/sums; no second model |
| workflow: `analysis/src/hockey_stats/chance_cli.py` | evaluation schema-3 envelope; preserve commands/recovery |
| research: `analysis/research/chance_review.py` | schema cutover, fixed benchmarks, intervals, streamed sensitivity, figures |
| science/operator: `docs/research/chance-03e/protocol.md`, external inputs/fits/results | frozen study, source/recipe judgments, attributable execution/resources |
| science/content design: `docs/research/chance-03e/decision.md`, figures, `docs/issues/` | claim, family dispositions, limitations, evidence and follow-ups |
| documentation: `README.md`, affected fixture instructions | exact usage/output contracts and retained facts |

reuse current numpy/scipy/matplotlib, identity/validation helpers, predictor, reference averaging, bootstrap arithmetic and grid. change fitting/preparation only for a demonstrated defect or measured resource blocker; record the cause and verify affected behavior. no silent likelihood changes.

## verification and completion

the pilot records wall time, peak memory, artifact bytes, origin-context groups and reference-pair counts for fitting AND exact scoring. fixture timing cannot establish season-scale cost. run expensive fits sequentially; measure the first complete development fit before the remaining workload. preserve checkpoints/expensive fits; rerun cheap derivatives. resource blockers warrant a scoped repair or incomplete decision, not origin pruning, matchup subsampling or a scheduler. seventeen full fits is a ceiling, not a quota; failed/rejected stages stop dependent work.

temporary integration checks: red → green → refactor → green, then delete tests/test-only dependencies. exercise native fixture fit/evaluate/score; directly check review arithmetic using fixture/synthetic inputs and verify the review cli rejects fixture artifacts. the legitimate research pilot supplies positive end-to-end review verification; no relabeling or production bypass. independently verify group/subset reconciliation, fixed-benchmark pairing, outcome labels, pooled game/block resampling, undefined denominators, singleton score summaries, matched reference/stream rejection and completion behavior. reuse 03d numerical verification unless touched. verify unchanged source bytes; preserve distinct new broken-game reproducers under fixture policy. retain scientific tools, useful fixtures and verification facts.

the designer owns a short report: study/population table; claim/criterion/result/consequence table; family dispositions and sensitivity; three figure families (calibration with counts/intervals, common-scale spatial mass/change, event-value changes). captions state conditioning, reference, selection and uncertainty exclusions. no universal quality score or “model accepted” badge.

after admission, fit the admitted family on all three seasons and score 2025–26 under identical 2025–26 joint reference weights. repeat matched sensitivity and inspect convergence/coverage/extremes; scoring final training games adds no held-out probability evidence. preserve every admitted alternative. if only the primary survives scientific rejection of alternatives, report no admitted final pair rather than invent a comparison; retain every transfer-stage rejection/comparison. numerical defects, invalid spatial meaning or missing required evidence withhold the handoff; declared unresolved measurement accuracy and material map sensitivity instead impose the confirmed 04 obligations.

on handoff, write external `handoff.json`: schema 1, `purpose: attribution_research`, `decision: {path,sha256}`, `reference_member`, `members: [{label,model:{path,sha256},score:{path,sha256}}]`. require nonempty uniquely labeled members and an existing reference label; every score identifies its linked model. members must be complete and share scoring population/reference. configurations, inputs and cutoffs already belong to linked artifacts. the decision lists exclusions, rejected/unresolved alternatives, tip/source limits and required 04 checks. no handoff index on `withheld`.

04 owns compatible event/exposure populations, historical-use cutoffs, attribution and player robustness across the family; league-wide stability is insufficient. 03e supplies final 2025–26 scores and retained models, not approved historical player priors. publication requires supported player conclusions and explicit operator action. completion here means attributable evidence and a defensible decision, including withholding.
