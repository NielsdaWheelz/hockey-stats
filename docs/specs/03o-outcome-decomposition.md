# pr03o — observable conversion decomposition

status: **assigned for complete implementation and real execution, 2026-10-13.** [03n](../research/chance-03n/decision.md) is reviewed and merged in `fa3c0e1`; its conditional short nomination informs this study, without model admission. user choice, 2026-10-13: decomposition only, current actor treatment, tip-shooter masking deferred. use two saved short direct controls and four fresh stage fits. [brief](../brief.md) · [direction](../research/model-direction.md)

## question and boundary

does modeling recorded net-hitting and scoring separately improve later recorded-goal probabilities on source-eligible unblocked 5v5 attempts?

`q(x)=p(on_net|unblocked,x)`; `g(x)=p(goal|on_net,x)`; `p(goal|unblocked,x)=q(x)*g(x)`.

goal implies on-net, so this identity needs no independence assumption. both stages predict EVERY eligible unblocked assessment row, including actual misses. actual on-net status selects training/diagnostic labels, never the product or its predictors. `x` retains our recorded location/type/context and actors; this is neither live pre-release forecasting nor physical/causal validation.

[published xg8](https://hockeyviz.com/txt/xg8) motivates conditional layers and includes goalie effects on net-hitting. it also omits tip/deflection shooter identity and separates frozen/in-play outcomes; our native model does neither. retain native shooters/goalies, tip treatment, geometry, six types and annual borrowing here. tip-shooter masking, mirror pooling and further layers remain separate experiments.

deliver target contracts/audits, four fresh native fits, two complete composed assessments, paired comparison and a developmental representation recommendation. negative/mixed/inconclusive evidence completes the study. no acquisition, new feature family, sequence filter, longer horizon, recency/penalty/geometry campaign, freeze/setter inference, blocked-origin integration, joint em, final fit, player estimate, admission, 04 handoff or publication. retain all supported inactive extraction.

## evidence, targets and fixed populations

use the exact four 03n short training/assessment selections at their original paths under `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/`: `development-short-training.json`, `development-assessment.json`, `season_transfer-short-training.json`, `season_transfer-assessment.json`. keep schema 2, `purpose='research'`, `history_corpora=[]`, original hashes/order and admitted manifests. [03n protocol](../research/chance-03n/protocol.md) binds those identities. new observations do not enter. all assessment dates follow disjoint training dates; selected empty games remain. windows are research-exposed and overlap in training, not independent confirmation.

| window | short training: games / unblocked / goals | common assessment: games / unblocked / goals |
|---|---|---|
| `development` | all 2023–24 plus 2024–25 before `2025-01-01`; 1,912 / 128,679 / 7,614 | remaining 2024–25; 712 / 49,014 / 2,804 |
| `season_transfer` | all 2023–24/2024–25; 2,624 / 177,693 / 10,418 | all 2025–26; 1,312 / 87,018 / 5,291 |

let `U` be eligible unblocked, `O` recorded on-net, `G` goals. interpret `source_event.type_key` literally:

| source class | `on_net` | `unblocked_on_net` training target | `on_net_conversion` training/diagnostic target |
|---|---|---|---|
| `missed-shot` | false | false | not applicable |
| `shot-on-goal` | true | true | false |
| `goal` | true | true | true |
| `blocked-shot` | null | not applicable | not applicable |

source `out_of_scope|unavailable` remains excluded regardless of class. assert source class/`blocked`/`goal` agreement; an unsupported or contradictory eligible class is a located failure, never a new omission. `shot-on-goal` is the recorded non-goal on-net class, called saved here; it does not distinguish freezes/rebounds. verify this mapping against full `feature_facts.outcome.values.on_net` on original fixtures; research uses `prepare_core`, without full/future-event feature materialization.

eight schema-1 cohorts (two quantities × four partitions) use `definition={mode:'all_source_eligible',required_families:[]}`. all recognized keys/source dispositions survive in native order. q includes U; g includes O and marks eligible misses/blocks `not_applicable`. no feature omissions. membership is target-applicability based, not universally outcome-blind; no prediction/model output selects it. raw `goal` and source goal audits stay unchanged.

audit/freeze before fitting: `U=miss+saved+G`, `O=saved+G`; q positive keys exactly equal g included keys; both training outcomes exist for every stage/window. transfer O is 119,276 training / 56,111 assessment, with the table's G counts. [03m summary](../research/corpus-03m/summary.json), `seasons/<season>/counts/attempt_counts` with status `eligible` and kind `goal|shot-on-goal`, gives 61,143 + 58,133 training / 56,111 assessment. development-split O is not yet separately measured; derive and independently reconcile exact counts before the frozen protocol, rather than inventing them. retain per-game/season counts and zero-contribution games; nullable source coverage stays missing. unchanged coordinate/membership/type-recording/source gaps remain limits, not new filters or elapsed-time requirements.

## recipe and immutable controls

one unchanged schema-3 config serves both new quantities: original `inputs/config.json`, sha256 `1a52e1bbb5d9ef736b6781c18cfa66bf3c869817c6da8b6e9d9c741b417c1bf2`. both use numerical layout `r`, explicitly selected `game_additive,recent_additive,recent_interactions`, all 65 circumstances and `trait_assumptions=[]`. existing inactive stage declarations remain; adding component quantities does not add joint-em stages or an automatic campaign.

preserve the native 656-cell grid/type maps, shared geometry/context, complete selected annual domain, earliest-season reference and latest-state carry-forward into 2025–26. each stage has its own shooter/goalie counts, annual coefficients and empirical positive-target log-odds intercept; all remaining coefficients start zero. q/direct layouts and actor counts agree; g counts reflect O. unseen residuals are zero; unobserved annual states retain native penalty-inferred meaning. no shared coefficient set or warm start.

summed binary likelihood plus unchanged penalties: cell ridge `.25`, type-cell ridge `1`, neighbor smoothness `4`, context/season ridge `4`, shooter level/change `4/16`, goalie `16/64`; intercept unpenalized. all other config fields remain byte-bound above. `L-BFGS-B`: 2,000 iterations, `ftol=1e-10,gtol=1e-6`, native success and finite coefficients/objective. relative-objective stopping may precede gradient tolerance; disclose termination/gradient. no new gradient gate, additional start, tighter post-result fit or altered likelihood normalization. two coefficient sets and g's smaller population change effective shrinkage; this tests an estimator package, not isolated causal factorization.

freeze reuse of the two 03n `short` cells from [its result](../research/chance-03n/result.json), sha256 `7f846890843811a10386f5da40818ac0e914ac27436d8e29678f3a91e3cfc123`. controls retain original 03n protocol, implementation, config and completion/component/evaluation/stream identities; never restamp them as 03o. a prefit reuse receipt must verify original binding chains plus exact selection/source/order/labels/cohort/design/numerical-contract equivalence under extended code. replay each saved direct objective once with existing `agrees(1e-10 relative/absolute)` and reproduce its predictions under native row tolerances; preserve exact keys/dispositions/support and aggregate reconciliation. missing/mismatched evidence stops with a concrete issue. NO try-reuse-else-refit fallback; fresh controls require an explicitly revised protocol/assignment.

## owners and capability contracts

`source selections → target cohorts/audits → protocol/control-reuse freeze → four fits → two composed streams → paired report`.

| owner / files | responsibility |
|---|---|
| new `analysis/src/hockey_stats/chance_targets.py` | four literal quantities: existing direct/all-attempt plus `unblocked_on_net,on_net_conversion`; `component_target(row,quantity)->bool` or null, `component_prediction_applicable(row,quantity)->bool`, `recorded_on_net(row)` and `component_kind(quantity)`. prediction scope for both new quantities is U; no registry/plugin engine |
| `chance_cohort.py` | reuse recognized-row membership/coverage; extend quantity-specific applicability and separate target audit. keep cohort schema 1 and source outcome-audit meaning; remove obsolete blanket outcome-blind claims |
| `chance.py` | new quantities reuse `r`. standalone setup retains source `data.goal` and adds explicit float64 `data.target`; initialize from target positives. ONE shared spatial-binomial function receives the response: joint conversion passes source goals, components pass target; benchmark components likewise receive their explicit unchanged goal target. preserve existing objectives/coefficients/predictions. failure messages name binary target outcomes. grid follows spatial layout; `extract_component` rejects new targets because joint models contain neither layer |
| `chance_development.py,chance_evaluation.py,chance_history.py` | share quantity-explicit native setup, `fit_prepared`, source binding and `compare_paired_records(baseline,changed,pairs)` statistical core. existing `compare_pair` delegates with its validated native pairs. preserve 03n schema/results and supported direct/sequence consumers. native schema-3 evaluator remains limited to its existing scoring contract |
| new `analysis/research/chance_decomposition.py` | thin fixed-study commands, control compatibility, two-stage prediction/scoring distinction, strict ordered pairing, product/comparative report and figures; reuse native binary summaries, resampling and artifact primitives |
| `docs/research/chance-03o/`, fixtures/issues | statistician owns frozen protocol/decision; content designer owns target/population vocabulary, tables/figures and null/error labels; data owner preserves new distinct failures; independent reviewers challenge source, numerical and composition boundaries |

config/component/fit/completion stay schema 3; selection 2; cohort 1. new quantity enums extend an active standalone capability; no old-artifact migration/compatibility reader. preserve actual source goals, `PREPARATION_IDENTITY`, full preparation and inactive families. new components cannot masquerade as direct conversion or be passed to joint-model integration. quantity/target semantics belong to the native owner, not wrapper copies or temporary source relabeling.

## manual commands and schemas

from `analysis/`: `.venv/bin/python research/chance_decomposition.py <command> ...`. fixed windows `development|season_transfer`; fit quantity is one of the two new literals. paths are required, nonrepeated/nonabbreviated; help 0, syntax 2, input/numerical/i/o failure 1. outputs are new exclusive directories outside input parents. `fixture_exercise` permits bounded native direct controls and same-shaped reuse inputs under distinct fixture protocols, with strict purpose/source/quantity checks. research reuse stays pinned to 03n, never falls back to fixtures. fixtures need no hdd or research counts/nomination.

| command | required flags / result |
|---|---|
| `cohort` | `--selection --out`; one traversal produces `out/<quantity>/{cohort,outcome_audit,target_audit}.json` for both quantities and one protocol-free top completion |
| `reuse` | `--inputs --protocol --out`; bound old controls, source/design/objective/prediction checks and `reuse.json,completion.json`; no fit |
| `fit` | `--selection --cohort --config --protocol --reuse --window --quantity --out`; validates bound reuse completion and sibling target audit before native `fit.json,component.json,completion.json` |
| `evaluate` | `--selection --cohort-on-net --cohort-conversion --on-net-component --conversion-component --protocol --window --out`; full composed `attempts.jsonl,assessment.json,completion.json` |
| `report` | `--inputs --protocol --out`; validated `result.json`, two figures and completion |

artifact references are `{path,sha256}`; successful completion is written last. failed native fits retain diagnostics without a successful component/completion. declared incomplete execution can produce a valid incomplete report, not an empirical rejection or completed study. source/numerical/i/o failure stops later expensive cells in explicit canonical order; scientific direction does not stop the second window.

new schema-1 contracts, closed fields:

- `target_audit.json`, kind `chance_component_target_audit`: `schema_version,artifact_kind,purpose,quantity,selection,cohort,inputs,preparation_identity,counts,per_game,per_season`; selection/cohort are identity refs, inputs retain native identities. counts: `recognized_count,source_eligible_count,source_statuses,study_inclusions,source_applicable_count,included_count,excluded_count,unblocked,on_net,missed,saved,goals,target_positive,target_negative`. class counts are source-eligible; target counts are included rows. per-game `{game_id,game_date,season,counts}`, per-season `{season,games,counts}`; zero represented rows do not assert complete source coverage.
- reuse input: `schema_version,purpose,source_result,config,windows`; each window binds original `fit,evaluation,training_selection,assessment_selection,training_cohort,assessment_cohort`. `reuse.json`, kind `chance_decomposition_control_reuse`, has `schema_version,artifact_kind,purpose,source_result,config,windows,protocol,implementation,source_protocol,source_implementation,checks,verification,resources`. verification refs hold native objective/prediction agreement. require both declared controls, not chosen winners/subgroups. protocol freezes reuse INPUTS; the later receipt binds that protocol, avoiding a cycle.
- composed row: `schema_version,game_id,source_index,event_id,game_date,season,source_identity,source_status,source_reasons,study_inclusion,study_reasons,status,blocked,goal,on_net,diagnostic_groups,stages,composed_goal`. `source_identity={kind:'game',path,sha256}` is the exact original game-envelope identity. status is `predicted` iff U, `not_applicable` for eligible blocks, otherwise the source `out_of_scope|unavailable`. source-only groups are native `diagnostic_groups(attempt,game_date,{})`: `original_type,model_type,recent_context,recent_kind,recent_team,recent_delay,home_away,role,calendar_month,sequence_index`.
- `stages` has exact keys `unblocked_on_net,on_net_conversion`; each holds `metric_applicable,observed,log_p,log_not_p,season_basis,state_season,actor_evidence`. both predictions exist on ALL U; g's observed is null and metric applicability false on misses. outside U, stage observations/numerical/basis fields and composed goal are null, metric applicability false. `composed_goal={log_p,log_not_p}` on U; source goal never changes. no combined actor-support fiction.
- `assessment.json`, kind `chance_decomposition_assessment`: `schema_version,artifact_kind,purpose,protocol,implementation,selection,inputs,preparation_identity,game_dates,coverage,cohorts,components,target_audits,attempts,metrics,groups,per_game,resources,scientific_assessment`. cohort/component/audit maps have both exact quantity keys; refs bind actual files. metrics/groups/per-game maps use `on_net,goal_given_on_net,composed_goal` with U/O/U denominators and native metric shapes. stage groups use their own actor support; composed-own groups omit it. `scientific_assessment='not_performed'`.
- report input: `schema_version,purpose,reuse,config,windows,resampling`. reuse is `{status,completion,failure,stop_reason}`, with completion naming `reuse/completion.json`. each window has exact keys `unblocked_on_net,on_net_conversion,assessment`; fit cells are `{status,cohort,target_audit,fit,failure,stop_reason}`, assessment is `{status,completion,failure,stop_reason}`. statuses `complete|failed|not_run`; fit/completion refs name actual completion files. complete requires all promised artifacts and no failure/reason; incomplete locates failure/reason and leaves unfinished refs null. validated reuse precedes fitting; canonical stop order ignores json member order.
- `result.json`, kind `chance_decomposition_result`: `schema_version,artifact_kind,purpose,inputs,protocol,implementation,reuse,horizon,population,diagnostic_scope,direction,recommendation,nominated_representation,scientific_assessment,execution_status,coverage,cells,comparisons,stage_diagnostics,resampling,arithmetic_deadband_nats_per_attempt,limitations,resources,figures`. retain full-precision native counts/metrics/bins and binding chains, not coefficients/raw/prediction duplication. cells reference objective replay receipts outside compact components.

new completions share `schema_version,artifact_kind,purpose,implementation,scientific_assessment='not_performed'`; kinds are `chance_decomposition_{cohort,reuse,assessment,report}_completion`. cohort adds `selection,cohorts,outcome_audits,target_audits`, with no protocol. reuse adds `protocol,reuse`; assessment adds `protocol,selection,components,cohorts,target_audits,assessment,attempts`; report adds `protocol,inputs,result,figures`. quantity maps use the two fixed keys. validate target audits against actual source, not merely mutually matching counts.

explicit numerical views may reuse native `summarize_component`/paired statistics; never serialize fake schema-3 evaluations or reinterpret saved raw rows. report validation rejoins actual source labels/dispositions/descriptors and saved stage coefficients; mutually consistent but false streams must fail, as in 03n. replay each new fit objective once with `agrees(1e-10 relative/absolute)`; bind input/design/component, saved/replayed objective/difference and gradient maximum in verification receipts, outside compact components. reuse receipts already bind old-control replay; no duplicate solve or new gradient gate.

## composition, assessment and decision

compute in log space: `log_p=log_q+log_g`; `log_not_p=logaddexp(log_not_q,log_q+log_not_g)`. no rounded multiplication/complement subtraction, clipping, division of direct probabilities to invent a conditional comparator, or actual-outcome substitution. separate stage binomial likelihoods use richer miss/saved/goal labels; their summed training loss is not comparable to direct binary goal loss.

prospective numerical clarification, 2026-10-13, before fitting: evaluate this same complement identity as `log1p(-exp(log_p))` when `log_p <= -log(2)` and with the displayed stage-complement sum otherwise. direct floating-point evaluation of the displayed sum can round just above zero for a tiny valid product; the first region avoids that cancellation. the second retains finite failure tails when near-certain stage probabilities have rounded log probabilities to zero. this deterministic range choice changes no probability model, fitting objective, population or decision rule and performs no clipping.

primary: **decomposed minus direct mean GOAL log loss, nats per eligible unblocked assessment attempt**; negative favors decomposition. score exact full U keys/order, never intersect or compare O with U. secondaries: brier, observed/predicted goals, signed pooled residual in percentage points and absolute-residual change. stage proper losses/calibration use their actual U/O target populations, descriptive only; stage losses are not competing scores.

reuse 03n's fixed game/calendar arithmetic: per window 2,000 paired game draws and 2,000 each nonoverlapping 7-/14-day block draws, `PCG64`, seed `3032026`, linear 95% intervals; pooled sums/counts, identical sampled units across arms/metrics, empty/intervening/final-partial units retained. undefined draws yield null intervals without redraw. 12,000 draws, ZERO bootstrap fits. condition on two reused direct models and four stage fits; omit fitting/selection/source uncertainty.

retain twenty own-arm goal bins and twenty paired bins defined by DIRECT probabilities; last bin includes one. direct support owns paired groups: `recent_context,model_type,calendar_month,role,actor_support:shooter,actor_support:goalie`. keep each stage's own support/bin summaries separate. absent sequence diagnostics stay `not_prepared`; no subgroup gates, support-transition search or added diagnosis campaign.

freeze `d=1e-10` nats/attempt. direction: incomplete for missing/nonconverged/unreconciled cells or undefined primary point; `decomposed_direction` if both deltas `<-d`; `direct_direction` if both `>d`; `within_arithmetic_deadband` if both inside `[-d,d]`; otherwise `mixed_direction`. nominate decomposed only if both game upper bounds `<-d`, all three interval methods defined in both windows and no calendar lower bound `>d`; direct symmetrically requires both game lower bounds `>d` and no calendar upper bound `<-d`. supported cases say `supported_representation`; otherwise `no_supported_representation` with null nomination. research remains `not_admitted`; fixtures always `not_assessed,fixture_only,null,not_performed`. disclose contrary secondaries; no automatic integration or new calibration-admission gates. deadband is not solver uncertainty or a useful-effect guarantee.

## content, operation and acceptance

designer-owned committed `docs/research/chance-03o/`:

| artifact | what good content shows |
|---|---|
| `protocol.md` | exact masks/measured counts; immutable control-input/config/code/lock/cohort identities; four cells, penalties/support/reference meaning and prospective decision/stop rules, frozen before fitting. later reuse receipts reference it |
| `result.json` | byte-exact bound report projection; unrounded values, units/denominators, null reasons, provenance and measured costs |
| `decision.md` | games/U/O/miss/saved/G table; absolute and paired goal scores/intervals; stage diagnostics/support on their own populations; nomination, contrary evidence and limits. nuisance actor logits are not player cards/ability |
| `figures/comparison.png` | one row per window: goal-loss delta with three intervals/zero; direct-defined goal-bin residuals, common axes and counts. distinguish own-bin tables |
| `figures/stages.png` | rows are windows; columns q-on-U and g-on-O own bins. x: mean bin prediction; y: predicted-minus-observed residual, pp. shared column axes/counts/zero; descriptive points, no implied interval/admission or stage score ranking |
| `verification.md` | exact commands/input hashes, reuse/target/source/objective/interval checks, whole-command costs, independent reviews and test deletion |

real outputs are external-only in a fresh `/Volumes/Expansion/hockey-stats/runs/chance-03o-<run-id>/`, with sibling `inputs/`, `cohorts/<partition>/<quantity>/`, `reuse/`, `fits/<window>/<quantity>/`, `assessments/<window>/`, `report/`, `receipts/`. retain all frozen paths/fits. ordinary mount/path/i/o checks and manual reruns; no local fit mirror, vm, drive investigation, runner/checkpoint/retry engine. detached software fixtures use local exclusive outputs.

03n already measured a larger 5,248-game setup; chosen training has at most 2,624 games/177,693 U rows with the same compact basis. measure each command/fit's final wall/rss/footprint; do not repeat the capacity campaign absent new demonstrated materialization. process stages/windows sequentially and release preparation/arrays between them. no dense attempts × all-coefficients matrix or new storage/cache framework.

after separate assignment: temporary original-fixture red → green → refactor → green; independent source/numerical/content prefit review; generate target cohorts/count audits, freeze clean code/input/config/protocol; prove old-control reuse before fitting; development q fit → g fit → assessment, then transfer q → g → assessment; report and one saved-objective replay per NEW fit; independent final arithmetic/source/content review; delete all temporary tests/controllers/bytecode/test-only dependencies. retain useful scientific commands/factual receipts/original fixtures/expensive fits. preserve newly distinct source failures under the existing [fixture policy](../../fixtures/README.md).

software acceptance: independent original-fixture source/full-fact target equivalence; source labels/coverage unchanged; q/direct layouts/actor counts and old control objective/predictions preserved; g subset/targets/intercept/counts correct; no outcome leakage or miss prediction gating; new spatial grids present and illicit joint extraction rejected; extreme-log product arithmetic independently checked; full ordered source/label/digest/basis reconciliation; independent U/O/U metrics and paired bins/all resampling; symmetric/undefined/near-identity decisions; strict bindings/exclusive paths and detached end-to-end fixtures. no code/data mutation masquerading as original evidence.

research completion: two valid reused controls, four converged new fits, both exact complete assessments and independently reconciled report; gain/admission NOT required. failures yield located `incomplete`, not unsupported scientific verdicts. further fitting/measurement/integration is separately assigned. later opportunity/04 reference standardization must average the PRODUCT over the same joint actor reference; multiplying separately averaged layers is generally wrong. record that contract now, implement it later.

tradeoffs: richer outcome labels buy two maps/coefficient sets, smaller g support and changed effective shrinkage; conditional intervals omit refitting uncertainty; exact control reuse saves work but needs strict compatibility and the original hdd artifacts; recorded-on-net classification/conditional extrapolation carry measurement limits; preserving current tip treatment isolates this comparison while deferring a published refinement. no additional feature/source campaign or peer-parity claim follows.
