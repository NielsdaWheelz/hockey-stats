# pr03j — conversion-scale benchmark

status: **full specification for handoff; implementation and real execution require separate assignment.** direction approved 2026-10-08 after merged 03i; the user confirmed adjustment-fitting uncertainty. historical 03b/03e/03h verdicts stand. [brief](../brief.md) · [direction](../research/model-direction.md) · [03k feature preparation](03k-feature-repertoire.md)

## target and scope

test whether a two-parameter adjustment to saved factual unblocked conversion predictions improves prediction in a later window. produce one attributable research-priority decision, complete numerical evidence and one readable figure. a useful adjustment nominates native conversion research; it is not a deployable model, opportunity correction or admission.

one saved revision, one chronological split, one unpenalized model, three paired bootstrap methods. no acquisition/hdd dependency, source preparation, base-model fitting/prediction, new features, avoidance/origin changes, all-attempt composition, actor-reference valuation, transfer/final campaign, 04 or publication. 03k remains independent. no intercept-only/spline/isotonic control, parameter grid, subgroup correction or automatic next experiment.

## frozen evidence and population

start at `/Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json`. reuse `chance_assessment.load_evidence` and `FROZEN_DIGESTS`: completion `8f4e098acb1b9b8ece3a989beb5e6a6d631d8ac32e3f7402923b59425d78080b`; linked comparison `e2d825297f5dd5a02871595a101d4a458a1c0546742f1acb9c8068a9f51e5e3c`, composition `d9c5f3773dfcb803cc7bcd3d41fd0c90025282247bfd3ffcc698eed13040a6d9`, stream `2830f700f4304c24da332cc34467670b9970f66f7d18de6791d8ca74754daca9`. preserve executing and parent identities separately. 03h/03i are cited context, not additional runtime inputs.

run `chance_assessment.reconstruct(loaded, diagnostic=collector)` once. hash/validate the whole stream and reconcile all revised quantities, native bins, games and coverage before fitting. retain 85,317 recognized rows: 68,775 eligible, 16,270 outside scope, 272 unavailable; eligible outcomes are 49,014 unblocked, 19,761 blocks and 2,804 goals. no population intersection, source reopening or re-scoring.

base-model training ends `2024-12-31`. use ALL eligible unblocked rows and exact `predictions.revision.candidate_r`:

| window, inclusive | selected games | unblocked attempts | goals |
|---|---:|---:|---:|
| adjustment fit: 2025-01-01–2025-02-28 | 346 | 23,987 | 1,332 |
| assessment: 2025-03-01–2025-04-17 | 366 | 25,027 | 1,472 |

these pinned counts apply to research. synthetic `fixture_exercise` bundles reconcile their own populations under the same fixed dates/eligibility rules; they need not contain the research counts.

retain ordered game/date ledgers and zero-contribution games. blocked/excluded rows remain in coverage, never the fit. collect compact float64 logits, binary labels, game indices and checked none/recent/model-type descriptors; no copied prediction/key/posterior stream. derive recentness from `previous_event.status`, not retained older metadata. validate descriptor/type cross-fields using a narrow extraction of existing `ResidualAccumulator.consume` checks, not a spatial accumulator or duplicate validator family. applicable contexts are `none,recent`; types are `wrist,snap,slap,backhand,tip,other`.

both windows are research-exposed. newer adjustment labels also give it more recent information than the unchanged model. chronology does not distinguish drift, shrinkage, missing mechanisms or measurement error, and supplies no untouched confirmation.

## numerical contract

let `x = log_p - log_not_p`, `y = goal`, `eta = a + b*x`, with adjusted logs `log_expit(eta)` and `log_expit(-eta)`. use saved complementary logs, never `logit(exp(log_p))`, clipping or probability floors. rounded boundary probabilities are permissible when logs/logits remain finite. identity `(a,b)=(0,1)` must reproduce unchanged row probabilities/losses within `1e-12` and aggregates under native `agrees` (`1e-10` relative/absolute).

fit the unpenalized weighted mean Bernoulli negative log likelihood:

`L = -sum(w * [y*log_expit(eta) + (1-y)*log_expit(-eta)]) / sum(w)`.

nominal weights are one. center/scale x using ONLY nominal fit-window mean `m` and population standard deviation `s`; both stay fixed in bootstrap. solve on `[1,(x-m)/s]`, starting at `[m,s]`; convert back to `b=theta_1/s`, `a=theta_0-b*m`. allow any finite slope: nonpositive b is adverse diagnostic evidence, not a reassuring clamp. joint a is an intercept, not calibration-in-the-large when b varies.

reuse `chance.fit_logistic` with analytic gradient; no penalty, model layout or alternate solver. exact settings: `optimizer_max_iterations=200`, `optimizer_ftol=1e-14`, `optimizer_gtol=1e-10`. independently reevaluate final objective/gradient/Hessian: finite coefficients/logs, reported convergence, scaled-gradient infinity norm ≤ `1e-8`, positive-definite analytic 2×2 Hessian, and objective no worse than identity under `agrees`. compute complementary sigmoid terms stably in derivatives.

require positive total fit weight, both labels, rank-two weighted design and no complete/quasi separation. in this one-dimensional predictor, either class-range ordering/touching identifies separation; check positive-weight observations. no ridge rescue, coefficient cap, constant fit, silent retry or dropped observations. invalid nominal support/numerical execution exits nonzero without completion.

## paired assessment and reliability

primary: assessment mean log-loss difference `adjusted - unchanged`, nats per eligible unblocked attempt; negative favors adjustment. brier difference and signed residual `(predicted goals - observed goals)/N` are secondary. nominal summaries use native binary helpers; bootstrap uses vectorized weighted sums of the SAME saved-log loss/brier/residual definitions, not python row loops. pooled ratios weight attempts, not games equally.

report fit metrics as apparent/in-sample. assessment contains unchanged/adjusted pooled metrics and paired differences; descriptive partitions are March/April, none/recent and all six fixed model types. retain counts, goals, predicted sums, residual rates and contributing games, including zero groups. no subgroup interval search or additional thresholds.

retain all twenty native reliability bins, `[i/20,(i+1)/20)`, last including one:

- own bins for each predictor, recomputed from its probabilities; their memberships differ and their residual differences are not paired effects.
- matched cohorts defined once by UNCHANGED probabilities; report both predictors on those identical rows. this separates movement between bins from within-cohort changes.

retain empty bins with zero counts and null rates; these tables are descriptive, with no bin intervals, admission margins or new calibration gate. nominal per-game binary sums reconcile to pooled sums; each partition/bin family reconciles separately.

## adjustment-refit uncertainty

2,000 draws EACH for whole-game, seven-day and fourteen-day methods; `PCG64`, seed `3032026`, pointwise 95% linear-percentile intervals. each method initializes its generator once, then generates its fit-window sample matrix followed by its assessment-window matrix. independently resample the two windows' units, preserve sample row pairing, and reuse the same assessment multiplicities for both predictors.

whole-game units include all selected games (346/366 for research). calendar units are anchored separately at each window's first selected date, including empty blocks/final partial blocks: research fit/assessment have 9/7 weekly and 5/4 fortnightly units; fixtures use their own ledgers. reuse native `calendar_blocks`; sample each window's original unit count with replacement. convert multiplicities to game/row weights without duplicating rows.

refit the same two parameters for each draw, with original m/s and identity initialization. evaluate both predictors on that draw's weighted assessment population. save `[a,b,delta_log_loss,delta_brier,unchanged_residual,adjusted_residual]`; use proportions for residuals, display percentage points. nominal estimates remain from the original windows.

zero fit/evaluation mass, one-label/rank-deficient/separated fit samples are explicitly undefined. retain their null affected statistics and reason counts; no redraws or discarded draws. any undefined draw makes that statistic's interval null. unchanged assessment residual can remain defined when a fit is unsupported. an optimizer/arithmetic failure on otherwise supported data is an execution error, not statistical missingness.

intervals include adjustment-estimation and selected fit/assessment sampling uncertainty conditional on the saved base model. they omit base-model fitting, adaptive selection, origin assumptions and dependence between windows. report contributing/selected games/blocks and undefined reasons; four/five fortnightly units limit the sensitivity. no fixed-coefficient uncertainty fallback.

## frozen research-priority rule

apply this order to nominal b and paired log-loss intervals: upper `<0` supports benefit, lower `>0` supports harm; equality to zero supports neither strict condition for that method. calendar methods check adverse sensitivity, not independent proof of benefit.

| recommendation | rule |
|---|---|
| `conflicting_or_adverse` | b ≤ 0, OR any defined method has lower endpoint > 0 |
| `scale_priority` | b > 0, whole-game upper endpoint < 0, both calendar intervals defined, and neither calendar lower endpoint > 0 |
| `inconclusive` | otherwise, including missing sensitivity/primary evidence without the adverse condition |

this chooses a research priority, not probability admission or a universal useful-effect margin. secondary brier/reliability/group outcomes constrain the written hypothesis; they never secretly change this rule. `scale_priority` nominates ONE native scale/shrinkage/temporal experiment. other outcomes may nominate ONE structural challenger or `no_supported_intervention`; lack of benefit does not prove a structural cause. no dependent fit is automatic.

historical withholding and origin/opportunity/player obligations remain open. neither coefficient equality, lower loss nor improved descriptive bins establishes complete calibration. [calibration distinctions](https://link.springer.com/article/10.1186/s12916-019-1466-7)

## command, boundaries and artifacts

from repo root, with unchanged lock/dependencies/interpreter pins:

```sh
UV_PYTHON=3.14.8 uv run --locked --project analysis python analysis/research/chance_conversion_scale.py --completion /Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json --protocol /Users/nnandal/Documents/code/hockey-stats-03j-runs/inputs/protocol.md --out /Users/nnandal/Documents/code/hockey-stats-03j-runs/benchmark
```

| owner/file | non-overlapping responsibility |
|---|---|
| new `analysis/research/chance_conversion_scale.py` | compact checked collector, objective/weighted solve, refit bootstrap, matched summaries, one figure and command; no base-model execution |
| `chance_assessment.py` | existing evidence loading/reconciliation; narrowly shared saved-descriptor check if extraction is needed; preserve 03h behavior/schema |
| `chance_residual_diagnosis.py` | reuse extracted descriptor check; no changed 03i result or spatial computation |
| `chance.py`, `chance_evaluation.py`, `chance_review.py` | existing optimizer, binary/bin arithmetic, validation/calendar primitives; no unrelated refactor or new model contract |
| `chance_cli.py`, `artifacts.py`, existing research identity/resource helpers | exclusive output, finite json, input/execution identities and measured resources |
| `docs/research/chance-03j/` | protocol, terse decision/verification, copy of the one figure; update existing issues with new evidence |

CLI has exactly three required single-use arguments above, `allow_abbrev=False`; no date/feature/recipe/sampling grid. research requires the exact frozen inputs; synthetic saved bundles keep `fixture_exercise`. freeze the external protocol after verified implementation and BEFORE any real adjustment fit; bind this spec, input identities, clean executing revision, dates, objective/settings, draws/rule and resource limits. no fitted-parent/raw access.

new shared outputs live outside git/worktrees. `benchmark.json` has schema 1, `artifact_kind: chance_conversion_scale_benchmark`, purpose, `model_admission: not_assessed`, `historical_admission_status: withheld` for research (`not_applicable` for fixtures), and these sections. preserve 03g's original `scientific_assessment: not_performed` separately; 03h/03i supplied the historical withholding, not the runtime 03g parent.

| section | capability contract |
|---|---|
| `inputs`, `protocol`, `implementation`, `parent_implementations` | existing `{path,sha256}` links and distinct execution identities; exact source stream identity binds rows |
| `population` | ordered fit/assessment game/date ledgers, complete source coverage and split applicable counts/goals |
| `fit` | raw a/b, m/s, no penalty/constraints, settings, support and independently checked numerical diagnostics |
| `metrics` | fit/apparent and assessment/unchanged-adjusted native binary sums/rates; paired assessment differences |
| `groups`, `own_bins`, `matched_bins`, `per_game` | fixed ordered domains, complete counts/goals/predicted sums/losses/rates/support; per-game predictor sums without duplicate per-row predictions |
| `uncertainty` | settings, selected/contributing units, ordered six-field draw records with per-statistic nulls/reasons, nominal estimates/intervals and excluded uncertainty sources |
| `recommendation`, `resources` | exact rule/classification with reasons; actual time/peak rss/bytes and measured throughput/projection |

metrics use existing `PROBABILITY_SUMS`; per-game records add game id/date/window. group/bin records identify predictor and cohort membership. null denominators yield null rates, never zero. each interval record retains `estimate`, `interval` ([lower,upper] or null), `undefined_draws`, `missing_reason` and selected/contributing unit counts. draw value arrays have the fixed six-column order above; retain per-draw missing reasons and per-statistic reason counts. finite json only.

write `conversion-scale.png`, `benchmark.json`, then `completion.json` (schema 1, `artifact_kind: chance_conversion_scale_benchmark_completion`) last, binding inputs/protocol/benchmark/figure/current execution and resources. the completion is the only success signal; malformed evidence/numerics/budget breach leaves none. valid inconclusive/adverse study exits 0. use a new output outside inputs; interruption reruns this cheap command, no checkpoint/runner. native model loaders must reject the benchmark kind; no `model.json`, handoff or adjusted probability stream.

## compute and content

one nominal solve plus 6,000 resampled solves, each max 200 iterations. freeze an engineering ceiling of 900 seconds wall time and 2 gib peak rss. inside the same execution, time the first 20 predetermined draws of each method (counted toward 2,000). project total time as `elapsed_now + sum((2000-20)*prefix_draw_seconds[method]/20)`. check projection/memory before continuing, actual resources between phases/solves and before completion. record projections/actuals; exceeding projected/actual ceiling stops without completion. resource repair may revise the ceiling in a new protocol before rerunning, never sampling/convergence/scientific criteria after observing results. no separate pilot stream pass or process supervisor.

content owner produces one figure: unchanged/adjusted columns; own-bin residual panels above count panels, all twenty midpoints retained. shared symmetric-log residual axes: linear within ±5 pp, logarithmic tails through ±100 pp, explicitly labeled; count axes share a linear 0–1 core and logarithmic tails. empty bins have no residual marker and visible zero counts. no cropped tails, admission-margin shading, bin whiskers, opportunity maps or dashboard. exact values remain in tables; nonlinear tail distances are the explicit readability tradeoff.

caption names denominators/sign, different own-bin membership, dates and research exposure. bins are descriptive; reported intervals concern pooled metrics and refit the adjustment conditional on the saved base model. this is retrospective observed-cell conversion, not a live pre-release forecast or standardized opportunity. reserve annotation space; inspect rendered output for clipping/overlap and identical scales.

`decision.md` leads with rule result and ONE next hypothesis or insufficiency, then matched overall loss/uncertainty, residuals, descriptive calibration/context/type limitations and numerical/resources facts. keep it one short page, link complete machine tables. explain coefficients literally and improvement without causal or admission language. apparent fit performance stays subordinate to assessment. newer-label information and Jan–Feb/Mar–Apr environment differences remain competing explanations.

## implementation and acceptance

1. temporary end-to-end red checks: full synthetic saved-bundle command, identity reproduction, independently solved two-risk-level MLE and weighted objective/gradient, date/exclusion/descriptor accounting, unequal-game paired resampling and fit-refitting effect. cover extreme finite logs, own versus matched bins, zero groups, undefined/separated draws versus numerical errors, evidence mismatch and incomplete output. guard raw/model execution. reuse existing fixtures; synthetic cases stay separate from raw captures.
2. implement the one command from shared primitives, green, refactor, green. retained features and legitimate historical research commands stay; remove only introduced duplication/dead paths. no compatibility reader or numerical fallback.
3. after explicit assignment, run the single frozen real benchmark. independently reconcile split/nominal/per-game/group/bin arithmetic and all percentile/decision calculations. temporary in-process verification on collected arrays checks representative weighted fits/draws across all methods; retain numerical receipts, not another stream or permanent audit hook. statistical, systems and content reviewers verify interpretation, correct objective, source preservation and rendered figure.
4. record protocol, decision, verification and unresolved issue facts; preserve expensive parents. delete ALL temporary tests/control code/bytecode/test-only dependencies; keep useful fixture data, documented facts and scientific artifacts. 07 still owns the lasting suite.

completion means reconciled inputs, supported nominal solve, every fixed summary, honest refit intervals/missingness, frozen rule result, one reviewed figure/report and test deletion. software completion does not require favorable research evidence or an admitted model. documentation authoring performs no fit.

tradeoffs: two parameters cheaply test scale but cannot locate a mechanism; recent labels confer additional information. 6,000 small refits cost more than fixed-correction intervals and still omit expensive base-fit/selection/origin uncertainty. conservative missing-draw handling can leave a completed study inconclusive. broad feature preparation and player robustness remain separate dependencies.

## queued avoidance experiment

retain [03i's 36-term proposal](../research/chance-03i/decision.md) for separate specification/assignment: fixed old u offset, exact origin/kernel/improved conversion, zero-coefficient reproduction, separate origin/avoidance designs and updated blocked weights. it cannot change no-recent predictions or conversion. retain the six-region composite score; prospectively add the seven-category blocking-level/conditional-allocation decomposition and a local reachability preflight. consider exact restricted marginal optimization only with native objective/gradient agreement and measured convergence. [the direction record](../research/model-direction.md) owns the other challengers. no next fit follows automatically.
