# pr03p — mirror pooling within the outcome decomposition

status: **complete on 2026-10-14.** [the decision](../research/chance-03p/decision.md) is `within_budget,nominate_mirror,mirror_y,not_admitted`; both windows pass the bounded numerical check. [verification](../research/chance-03p/verification.md) records full software/research acceptance. the user selected mirror pooling and at least 99% predictive-gain retention, then assigned complete implementation and bounded execution, on 2026-10-14. the prospective specification copy and exact code/artifact identities remain frozen in the execution [protocol](../research/chance-03p/protocol.md). [plan](../plan.md) owns progression. [03o](../research/chance-03o/decision.md) remains `no_supported_representation,not_admitted`; [04a](04a-attribution-feasibility.md) is independent.

## question and boundary

can corresponding left/right cells share spatial coefficients within each shot type while retaining at least 99% of the untied model's recorded-goal predictive gain over a training-rate constant forecast?

keep `q=p(on_net|unblocked,x)`, `g=p(goal|on_net,x)` and `p=q*g`. compare four fresh mirrored components with the four saved untied 03o components, across the same two windows. both arms already have q/g; the benefit under test is fewer independent spatial coefficients. [hockeyviz's published xg8](https://hockeyviz.com/txt/xg8) motivates stronger spatial support through symmetry while sacrificing possible league-level left/right differences. our grid, penalty and comparison policy remain our own.

deliver reusable constrained fitting, exact control reproduction, two matched assessments, a bounded numerical sensitivity check and one developmental recommendation. negative, inconclusive and numerically unresolved results can complete this study. no type pooling, tip-shooter masking, new features/sources, longer history, penalty search, origin fitting, all-attempt integration, attribution, model admission or publication. retain correct inactive features. direct conversion is historical context only; do not reopen direct-versus-decomposed selection or re-score direct controls.

## evidence and populations

reuse the original selections/config from `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/` and original q/g cohorts, target audits, fits and composed assessments from `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/`. [03o protocol](../research/chance-03o/protocol.md) binds selections, config and cohorts. its [result](../research/chance-03o/result.json), sha256 `77ebbcdf7b35101848d15415151a18bab3bdf40c36726d864e9ad616a2280848`, binds completed controls. freeze all four controls and both assessment streams; no winner selection, fallback refit, artifact migration or restamping.

| window | training | assessment | training games / U / O / G | assessment games / U / O / G |
|---|---|---|---|---|
| `development` | 2023–24 plus 2024–25 before `2025-01-01` | remaining 2024–25 | 1,912 / 128,679 / 87,618 / 7,614 | 712 / 49,014 / 31,658 / 2,804 |
| `season_transfer` | 2023–24 and 2024–25 | 2025–26 | 2,624 / 177,693 / 119,276 / 10,418 | 1,312 / 87,018 / 56,111 / 5,291 |

`U` means source-eligible unblocked 5v5 attempts; `O` means recorded on-net; `G` means goals. q fits/scores on U with target O; g fits/scores on O with target G; the product scores goals on U. both stages predict EVERY U row, including actual misses. retain `missed-shot/shot-on-goal/goal` target mapping, source goals, original keys/order, gaps, actor support and zero-contribution games. source exclusions stay excluded; contradictions fail at their source owner, never become a new filter. no sequence-completeness mask or preparation change.

use `prepare_core` and the existing all-source-eligible target cohorts. verify original per-game/season counts and source bindings; do not build a new cohort campaign. windows are chronological but research-exposed and overlap in training; they are not independent confirmation.

## the one structural change

retain the native 656-cell grid and `cell_id`. reflect a cell centre `(x,y)` to `(x,-y)`. number orbits by the first native cell index encountered. there are 40 centreline cells and 308 pairs: 348 orbits. tie the base map and each of its five type-offset maps separately, preserving all six type meanings. intercept, annual, actor and circumstance coefficients remain untied and are refitted; their design and penalty definitions are unchanged.

construct an integer `full_to_free` vector in native coefficient order: tied coefficients share one free index; every other coefficient has its own. with expansion `beta = theta[full_to_free]`, evaluate the EXISTING full objective `f(beta)` and sum its gradient by free index. this implements `f(P theta)` and `P^T grad(f)`, including the existing `P^T K P` penalty. never average gradients, halve penalties, normalize the likelihood, rebuild an unweighted half-rink penalty or materialize dense P/design matrices.

| independent coefficients per stage | untied | mirrored |
|---|---:|---:|
| spatial maps only | 3,936 | 2,088 |
| development q / g, including other terms | 6,159 / 6,147 | 4,311 / 4,299 |
| transfer q / g, including other terms | 6,335 / 6,317 | 4,487 / 4,469 |

derive/check these counts before fitting. the full grid has 1,255 edges; projection has 647 distinct edges, with 608 double and 39 single contributions. full-objective evaluation preserves these multiplicities automatically. counts describe free parameters, not effective degrees of freedom or guaranteed time/storage savings.

symmetry is a coefficient constraint at corresponding grid cells. preserve nearest-cell tie behavior: for example, `(82.5,2.5)` selects `(82.5,0)` while `(82.5,-2.5)` selects `(82.5,-5)`. do not promise reflection equality for every raw coordinate or complete prediction. actors/context can differ; future signed predictors may also distinguish sides. do not mirror source observations, player shot-generation maps or origin distributions.

the byte-bound schema-3 config remains sha256 `1a52e1bbb5d9ef736b6781c18cfa66bf3c869817c6da8b6e9d9c741b417c1bf2`: `game_additive,recent_additive,recent_interactions`, all 65 circumstances, no trait assumptions; cell/type ridge `.25/1`, spatial smoothing `4`, context/season ridge `4`, shooter level/change `4/16`, goalie `16/64`. retain the native annual domain, earliest reference, carry-forward and unseen-actor rules. q/g keep their own actor counts and coefficient sets.

primary fits use the existing empirical-target-log-odds intercept and zeros elsewhere, no control warm start. unchanged `L-BFGS-B`: `maxiter=2000,ftol=1e-10,gtol=1e-6`; native success plus finite objective/coefficients. replay each new saved objective once with existing relative/absolute `1e-10` agreement. report the FREE-coordinate gradient, rather than mistaking nonzero full gradients at a constrained optimum for failure. replay validates arithmetic, not optimization accuracy.

## selected comparison policy

for each window, set `p0=training_G/training_U` before assessment. score its binary goal forecast on the same U rows as both arms. no assessment-fitted intercept or recalibration. with mean goal log losses in nats/U:

```text
D = L_constant - L_untied                  # control predictive gain
A = 0.01 * D                               # allowed cost
delta = L_mirror - L_untied
c = delta - A = L_mirror - .99*L_untied - .01*L_constant
```

the primary estimand is c; lower favors staying within the selected allowance. mirror loss may increase: superiority is NOT required. 99% concerns gain over this constant forecast, not accuracy, absolute loss retention, stage calibration or player-effect resolution. this is a prospective development policy, not a threshold chosen from mirror results. no later relaxation to 95%.

accumulate per-game U counts and additive losses for all three forecasts. for each window, use 2,000 whole-game, 2,000 nonoverlapping seven-day and 2,000 fourteen-day draws; `PCG64`, seed `3032026`, linear 2.5/97.5 percentiles. blocks start at the earliest selected assessment date; retain intervening empty blocks, zero-contribution games and final partial blocks. draw exactly the selected number of units with replacement. identical draws serve all arms, contrasts and numerical comparisons. compute pooled sums/counts, not averages of game means.

resample the complete paired c and D, including the constant's assessment losses; its training probability stays fixed. never freeze a full-sample random allowance inside the bootstrap. undefined draws give a null interval and explicit count/reason, with no dropping/redrawing. 12,000 draws total; ZERO bootstrap fits. intervals condition on the fitted models, training reference and selected design; they omit fitting, source and selection uncertainty.

classify each window from all three interval methods:

- `reference_unusable` if a required interval is undefined, point D is not strictly positive or any D lower bound is not strictly positive. retain absolute losses/deltas; no gain-retention claim.
- otherwise `within_budget` if point c and every c upper bound are at most zero; `exceeds_budget` if point c and every c lower bound are strictly positive; otherwise `inconclusive`. percentile intervals need not contain their point estimate, so check both.

combined-status precedence: incomplete primary work → `incomplete`; otherwise any usable window `exceeds_budget` → `exceeds_budget`; otherwise any `reference_unusable` → `reference_unusable`; otherwise both `within_budget` → `within_budget`; otherwise `inconclusive`. retain both window statuses. this deliberately conservative agreement requirement is a chosen policy, not six independent confirmations. nomination requires BOTH windows `within_budget` and the numerical check below `stable_within_probe`. otherwise nominate nothing. no requirement that raw `delta<0`, and no new stage-calibration or subgroup gate.

secondaries: brier, predicted/observed goals, signed residual in percentage points, twenty own-arm and untied-defined paired goal bins. q/g diagnostics retain U/O denominators, own actor support and untied-defined paired bins; groups are the existing `recent_context,model_type,calendar_month,role,actor_support:shooter,actor_support:goalie`, with stage-specific actor groups only. product groups do not invent combined actor support. retain contrary calibration evidence. no post-result bin search, additional resampling campaign or claim that q/g losses rank the stages.

## bounded numerical sensitivity

after both primary assessments, run ONE diagnostic continuation for every primary/control component: two arms × q/g × two windows = eight probes. same data, target, objective and parameterization; start at that artifact's saved coefficients. use `L-BFGS-B,maxiter=100,maxfun=400,maxls=20,ftol=1e-12,gtol=1e-8`. no additional start, second continuation, optimizer search or retry on a scientific outcome. record actual iterations/evaluations and termination, including the solver's terminal line-search behavior under its evaluation cap. [scipy documents these stopping controls](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html).

store endpoints as diagnostic states, never replacement fits or fabricated converged schema-3 components. original 03o controls and new primary models remain immutable. score both stages on U, their product on U and g diagnostics on O. store mean/p99/max absolute q/g/product probability changes; original/probe objective, free-gradient maximum and loss changes. these are deterministic local sensitivity measurements, separate from sampling intervals.

for each window, let `lm0,lc0` be original per-row product goal losses and `lm1,lc1` the corresponding probed-arm losses. use original `A` above and compute:

```text
B = mean(abs(lm1-lm0)) + .99*mean(abs(lc1-lc0))
numerical allowance = .10*A
```

evaluate all four arm combinations `(m0,c0),(m1,c0),(m0,c1),(m1,c1)` with the SAME draws and fixed constant. `stable_within_probe` requires valid endpoints, positive usable original reference, `B <= .10*A`, ABSOLUTE movement of the c point and both endpoints of each interval from the original pair `<= .10*A`, and unchanged reference-usability/budget classification for every combination. this prevents cancellation between arms and detects decision sensitivity. probability maxima are descriptive; do not demand each rare row satisfy an aggregate-loss allowance.

a finite endpoint with nonincreasing training objective within existing `1e-10` replay tolerance is valid when it stops normally or at the declared iteration/evaluation cap. cap termination alone is not a new convergence gate. abnormal/nonfinite/increasing-objective probes or failed movement/classification checks yield `resolution_unestablished`; unusable reference yields `reference_unusable`. neither triggers more fitting. preserve all available evidence; source/i/o failures remain execution failures.

the probe budget and 10%-of-allowance rule are engineering choices. passing establishes stability under this specified continuation, NOT a certified bound on distance to the optimum, residual optimization error, fitting uncertainty or player effects. any later stronger claim requires different evidence.

## owners and interfaces

`original sources/cohorts/controls → reuse receipt → four constrained fits → two assessments → eight diagnostic probes → paired report`.

| owner / files | contract and boundary |
|---|---|
| `analysis/src/hockey_stats/chance.py` | owns deterministic parameterization, constrained objective/solve and expansion. expose `spatial_parameterization(layout,centers,constraint)` for `untied` or `mirror_y`; `fit_component` accepts the explicit constraint, existing callers select `untied`. reuse `prepare_component_fit,component_objective,fit_logistic` and prediction. mirror supports only the two assigned spatial quantities. preserve native component fields and four-field diagnostics |
| new `analysis/src/hockey_stats/chance_components.py` | move mature shared component setup/fit execution/source bindings from `research/chance_development.py`; return native components/diagnostics without study decisions. one authoritative setup, artifact validation and objective-replay path; 03p adds its constraint envelope. no campaign matrix or generic engine |
| `chance_evaluation.py` | own shared stable `compose_logs`, composed-row/metric views and paired additive evaluation needed from 03o/development. preserve extreme-log composition, U/O/U semantics, source rejoin and own/paired bin meaning. move the used calendar/ratio primitives here; study-specific 99% policy stays outside |
| `artifacts.py` and existing boundary helpers | reuse exact identity, finite-json, exclusive-path and completion behavior. promote only helpers otherwise imported through historical research scripts; no second validator stack or general artifact framework |
| new `analysis/research/chance_mirror.py` | fixed commands, original control selection, new schema validation, numerical budget, paired contrast, decision and figures. imports numerical/shared mechanisms from the package, not a chain of historical campaign scripts |
| `docs/research/chance-03p/` | statistician owns protocol/decision; content designer owns names, units, tables/figures/nulls; independent numerical/source/systems reviewers challenge the boundaries. fixtures/issues preserve newly demonstrated failures |

one solver primitive in `chance.py` owns the scipy call and returns coefficients plus termination/status, iterations/evaluations and objective. native `fit_logistic` adapts this to its unchanged four-field diagnostics; the probe supplies explicit cap/tolerance settings and retains the richer diagnostics. no script-side duplicate solver. add `component_probe_context(component,coefficients,parameterization,...)` to validate the source component, finite expanded shape and constraint, then use the SAME prediction arithmetic with an explicit audit role. never mutate the component or fabricate a successful one.

update prior command imports only as extraction requires; verify their affected behavior without migrating studies or rewriting frozen results. keep native prediction designs/arrays expanded: their columns describe prediction, while the parameterization separately describes free fitting coordinates. ordinary native prediction remains schema 3. 03p consumers require the fit envelope and regenerate/validate its map and coefficient equality; equality alone does not prove how a model was trained. no native schema migration or old/new fallback reader.

04a owns attribution, annual priors, count-rate uncertainty and provisional valuation; it does not edit this fitting path. share only explicit existing source/prediction contracts. neither track depends on the other's result. no effect/frontend change.

## manual commands and artifacts

from `analysis/`: `.venv/bin/python research/chance_mirror.py <command> ...`. fixed windows `development|season_transfer`, quantities `unblocked_on_net|on_net_conversion`. require explicit paths, no repeated/abbreviated flags; help 0, syntax 2, contract/numerical/i/o failure 1. successful diagnostic or scientific non-support is exit 0. outputs are new exclusive directories outside input parents; completion written last.

| command | required flags / output |
|---|---|
| `reuse` | `--inputs --protocol --out`; validate all four original components/cohorts, replay each control objective once, reproduce both full composed streams, bind source and numerical agreement in `reuse.json,completion.json` |
| `fit` | `--reuse --protocol --window --quantity --out`; reuse selects exact training/config/cohort. one primary mirrored solve; `parameterization.json,fit.json,component.json,completion.json` |
| `evaluate` | `--reuse --protocol --window --on-net-fit --conversion-fit --out`; consume fit COMPLETIONS, validate their constraint/targets; `attempts.jsonl,assessment.json,completion.json` |
| `numerics` | `--inputs --protocol --out`; inputs bind the completed primary matrix and reuse; eight fixed probes, diagnostic states, two movement streams and `numerics.json,completion.json` |
| `report` | `--inputs --protocol --out`; same matrix plus numerical completion; validate, compare and write `result.json`, two figures and completion; no solve |

`reuse` preserves original protocol/implementation identities, validates actual source labels/dispositions/cohorts/targets, annual support, config/design and exact ordered keys. compare numeric replay under existing native tolerances (`1e-10` objective relative/absolute, `1e-12` prediction absolute); nonnumeric identities agree exactly. mismatches fail, with no intersection of streams, silent repair or control refit. retain one source/objective/prediction receipt per validated boundary and reuse it; no repeated corpus audit merely to write the report.

new study DOCUMENTS use closed schema 1 with `schema_version,artifact_kind,purpose,implementation,protocol`; input manifests instead contain `schema_version,purpose` plus their listed fields, and streams keep the row contracts below. references are `{path,sha256}`. `purpose` is `research|fixture_exercise`; implementation binds clean analysis code/runtime/lock. native config/component remain 3, selection 2, cohort 1. study kinds are `chance_mirror_reuse,fit,parameterization,probe_state,numerics,result` with the `chance_mirror_` prefix on each; assessment/completion kinds are specified separately. contracts add:

| artifact | required content |
|---|---|
| reuse input | `source_result,config,windows`; each window has `training_selection,assessment_selection,training,assessment,control_fits,control_assessment`. training/assessment map q/g quantities to `{cohort,outcome_audit,target_audit}` refs; control_fits maps q/g to native fit-completion refs (four total); control_assessment binds its composed completion. bind hashes before protocol freeze; protocol binds this INPUT, later receipt binds protocol, avoiding a cycle |
| `reuse.json` | `source_result,config,windows,checks,resources`; original binding chains, verified counts, four objective/two stream receipts and identity-parameterization refs for the four untied controls. no copied coefficients or replacement identities |
| `parameterization.json` | `constraint,quantity,grid_sha256,design_sha256,full_to_free,full_count,free_count,full_spatial_count,free_spatial_count,orbit_count,centreline_count,penalty='restricted_full_objective',cell_assignment='native_nearest_first'`. primary constraint is `mirror_y`; control probe constraint is `untied` with identity map/full free count. orbit count describes the selected grouping (348/656). hash canonical native grid/design values using existing digest rules; indices contiguous in first-occurrence order. no component reference cycle |
| `fit.json` | `window,quantity,selection,config,cohort,target_audit,parameterization,solver,start_policy='empirical_intercept',role='primary',status,diagnostics,objective_replay,resources`. native diagnostics unchanged; receipt separately records projected gradient/dimensions. failed fit has located diagnostics and no successful component/completion |
| `assessment.json,attempts.jsonl` | retain the exact 03o composed assessment/row vocabulary, source identities and U/O/U semantics; new assessment kind `chance_mirror_assessment`, with additional `fits` and `parameterizations` maps and a `source_replay` receipt. the assessment completion binds the same receipt: selection/cohorts/components/parameterizations/stream identities, ordered source/prediction replay counts and tolerance. this implements the required reusable validation boundary without another corpus audit. both stages present on all U, g observed null on misses, numeric fields null outside U. do not fake native schema-3 evaluations |
| matrix input | `reuse,windows`; reuse and each window's `unblocked_on_net,on_net_conversion,assessment` cells are `{status,completion,failure,stop_reason}`, status `complete`, `failed` or `not_run`. completed cells bind completion and have null failure/reason; unfinished refs null with located failure/reason. numerics requires a complete matrix. report input adds `numerics` in the same cell form and supports incomplete cells. canonical order is explicit, not json member order |
| diagnostic state | kind `chance_mirror_probe_state`, `role='numerical_probe',window,arm,quantity,source_fit,source_component,parameterization,solver,termination,iterations,evaluations,coefficients,objective,free_gradient_max,valid,missing_reason`. coefficients are expanded, finite or null on failure; cannot be supplied as a primary fit/completion |
| `numerics.json` | `inputs,probes,windows,resources`; each probe binds source, state and replay checks; each window binds movement stream and original/probed metrics, B/A, all four combination classifications/interval shifts and numerical status/reasons. record unresolved cases without inventing probabilities |
| movement stream | original U key/source identity plus `window,goal` and original/probed q/g/product log probabilities for both arms. invalid probes have explicit nulls/reasons. no synthetic native component or hidden replacement stream |
| `result.json` | `inputs,reuse,constraint,windows,numerics,comparison_result,recommendation,nominated_structure,scientific_assessment,execution_status,resampling,limitations,resources,figures`. windows contain populations/coverage, fixed p0, three absolute losses, D/A/delta/c and all paired intervals, reference/budget status, secondary/own/paired stage diagnostics and numerical status. preserve full precision and explicit null reasons |

completion kinds are `chance_mirror_{reuse,fit,assessment,numerics,report}_completion`; common fields above plus refs to exactly their promised artifacts, selection/window/quantity where applicable and `scientific_assessment='not_performed'`. fit completion binds native component AND parameterization AND fit record; report completion binds result/figures. no successful completion for partial writes. ordinary local path/i/o checks suffice.

the primary/report validators rejoin source labels, dispositions, ordered keys and numerical coefficients, not just self-consistent summary counts. composed probabilities use the existing stable log-space complement branch from 03o; no clipping, output rounding or actual-outcome gating. diagnostic states use the same low-level prediction math with explicit audit role, never bypass native primary validation.

for detached `fixture_exercise`, temporary setup creates bounded untied q/g controls with native fitting on the same captured fixture selections and a distinct fixture protocol. `source_result` is null only for this purpose; all control/assessment window bindings remain required. do not fabricate a 03o result or run a direct-control campaign for the fixture. the same commands validate those artifacts without research-specific paths/counts/hashes; `research` stays pinned to 03o. this is an explicit exercise purpose, never a reuse fallback or substitute scientific study.

`recommendation='nominate_mirror'` and `nominated_structure='mirror_y'` only when both windows meet budget and numerical conditions; otherwise `no_supported_structure,null`. `comparison_result` reports `within_budget|exceeds_budget|inconclusive|reference_unusable|incomplete` from primary evidence, separately from numerical status. `execution_status='complete'` permits a valid non-supporting/unresolved result; missing or failed primary work/source reconciliation is `incomplete`. `scientific_assessment='not_admitted'` always. fixtures instead report `not_assessed,fixture_only,null,not_performed` and cannot nominate.

## content and operation

the content designer defines and reviews these outputs before execution:

| committed `docs/research/chance-03p/` | what good content shows |
|---|---|
| `protocol.md` | exact original input/control hashes, clean code/lock/runtime, four cells, constraint, solver/probe policies, counts, uncertainty/decision rules; frozen before real fitting |
| `result.json` | byte-exact completed result copied from the external run; attributable numbers/units/nulls, no source or coefficient duplication |
| `decision.md` | plain answer, population table, coefficient reduction, absolute losses and c intervals, reference/numerical outcome, contrary diagnostics and limits; research nomination distinguished from admission |
| `figures/comparison.png` | one row per window; c with game/7-day/14-day intervals against zero labeled “99% gain-retention boundary”; U/G, control gain and allowance alongside. negative supports staying within budget; no “99% accuracy” or equivalence wording |
| `figures/stages.png` | q-on-U and g-on-O by window; common untied-defined bins, both arms, counts and predicted-minus-observed pp on comparable column axes. descriptive; own-bin tables separately available |
| `verification.md` | exact commands/identities, independent checks, original/probe objective/prediction/loss movement and termination table, wall/rss/output costs, reviews, temporary-test deletion and remaining limits |

no dashboard, rink-map atlas or content system. captions state that intervals condition on fitted models and the probe is not an optimization-error certificate. fewer coefficients are not extra components, effective degrees of freedom or evidence of player accuracy.

real outputs use a fresh `/Volumes/Expansion/hockey-stats/runs/chance-03p-<run-id>/` with `inputs/,reuse/,fits/<window>/<quantity>/,assessments/<window>/,numerics/,report/,receipts/`. all expensive outputs external-only; preserve original paths/fits. process one stage/window at a time; no dense design or new cache, job runner, vm, local fit mirror or checkpoint system. ordinary mount/i/o handling and accepted manual reruns remain sufficient. detached fixture exercises need no hdd or research counts and follow the same semantic boundaries.

03o's four fitting commands totaled about 524 seconds; its full run took about 47 minutes and peaked near 5 gib rss. these are evidence of scale, not an eta. 03p adds eight capped probes and source reuse/assessment overhead; record actual whole-command costs. no separate capacity campaign absent demonstrated new materialization.

## delivery, review and acceptance

after assignment, split along the owner table: numerical parameterization; shared execution/artifact boundary; paired assessment/report; content/evidence. review each contract before implementation and review the integrated seams before fitting. do not let separate workers implement duplicate target, penalty, source-validation or resampling logic.

1. temporary detached integration red → green → refactor → green. exercise captured fixtures and separately labeled synthetic numerical cases. independently check all mirror pairs/centreline, full-versus-reduced objective and finite-difference gradients, unchanged untied behavior, penalty multiplicities, source-cell ties, q/g miss predictions and extreme log composition.
2. verify end-to-end binding/roles, strict mismatch failures, original ordered streams, zero-contribution games, complete paired c/D arithmetic, calendar draws/undefined cases, numerical caps/endpoints and all decision boundaries. validate original/probed mixed combinations; a deliberately asymmetric coefficient mutation must fail constraint validation. no fitting campaign is a routine test.
3. independent source/numerical/systems/content prefit review; freeze clean code, input manifest and protocol; formal reuse before any new primary fit. order: development q → g → assessment; transfer q → g → assessment; eight probes in window, untied/mirror, q/g order; report. no early stop for an unfavorable direction. source/i/o or primary-fit failure stops dependent work; diagnostic non-support does not authorize retry.
4. independently reconcile final losses, paired intervals, parameter counts, bounded movement and decision; inspect both figures. preserve useful scientific commands, receipts, original fixtures and expensive fits. per this assignment, delete ALL temporary test code/controllers/bytecode/test-only dependencies after verification; no lasting 03p suite is selected. [07](07-lightweight-testing.md) remains separate.

software acceptance requires the contracts above and preserved affected untied behavior. research completion requires four valid reused controls, four native-success mirror fits, both complete matched assessments, all eight bounded probe outcomes and a reconciled report; predictive gain, numerical support and admission are NOT completion requirements. failures are located, never disguised as empirical rejection. record distinct source failures under the existing [fixture policy](../../fixtures/README.md); unresolved defects go in `docs/issues/`.

material tradeoffs: hard symmetry loses true left/right spatial differences for stronger pooling; restricting the original penalty isolates that constraint but is not a new penalty optimum. expanded native arrays avoid schema churn without promising storage savings. exact reuse saves refits but requires original hdd artifacts. conditional intervals omit model-fitting uncertainty; agreement across three resampling methods is conservative. the small continuation budget tests local numerical stability and can remain unresolved. all existing calibration/source/origin limitations survive; no additional experiment or adoption happens automatically.
