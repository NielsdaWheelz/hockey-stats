# pr04h — recoverable spatial signal and penalty selection

status: **full specification; ready for handoff.** independent statistical, systems/source and content reviews cleared. specification only; [the plan](../plan.md) owns implementation/execution assignment. confirmed on 2026-10-17: both gaussian and game-pace laws; diagnostic curves without a new absolute accuracy gate; reuse existing histories and transitions. preserve frozen verdicts and research exposure. always return `nomination:null,admission:not_admitted,handoff:null`.

## question and scope

how much regional recovery is available within one finite pooled-history family, and how much does training-selected regularization obtain? extend [04d](../research/attribution-04d/decision.md) to five years and [04g](../research/attribution-04g/decision.md)'s full identifiable target. compare one constant-player pooled benchmark with saved annual borrowing; this changes temporal assumptions, not just computation. positive evidence selects a subsequent question, not a deployable ability estimator.

no new research responses, annual fits, real fits, acquisition, nested uncertainty, age/context features, website work or broad cleanup. [05b](05b-observed-comparison.md) is independent. native processing and external-only outputs remain. the drive is required for research execution, not specification; missing research originals cannot be replaced with the uniform-reference graph fixture.

## inputs and finite work

pin committed [04g result](../research/attribution-04g/result.json), sha256 `84bb4d034bb2213ce8b1cf0cf91fe54713fa7ba797e684f329838b16d05266a6`, and [protocol](../research/attribution-04g/protocol.json), sha256 `9e8266d1b0f7883d284e677be1e607f3cd8593264c3a5e95e9909acbfb3b8ef2`. their named references identify the basis, designs, operators, prepared metadata and fit manifests. preserve `r=40`, positive native shares `p`, 656 cells, `B' diag(p) B=I`, `p'B=0`, and `R=diag(p)B`. basis semantic identity stays `649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51`.

select **independent sparse/diffuse** and the single **paired null**, each under both laws. paired non-null cases remain historical context. retain outer ids 0–199 and five seasons 2021–22 through 2025–26. outers 0–99 select a common truth-informed reference; 100–199 assess it and the data-selected fits. these cases were previously examined: the split separates the new selection calculation, not an untouched confirmation set.

| condition | truth multiplier `alpha` | independent game copies `k` | saved basis columns `d` | work |
|---|---:|---:|---:|---|
| `base` | 1 | 1 | 40 | fixed-penalty curves; saved-response pooled fits |
| `half_effect` | .5 | 1 | 40 | fixed-penalty curves only |
| `double_games` | 1 | 2 | 40 | fixed-penalty curves only |
| `broad` | 1 | 1 | 11 | fixed-penalty curves; saved-response pooled fits |

use the first eleven saved modes, the existing nested nominal 80-foot space; verify its identity through `validate_pooling_basis`. keep the same twelve-region operator `W` and actual native truth. half-strength preserves positivity. `k=2` means independent copies of every complete game, with independent pace draws, not longer exposure under the original pace. no full factorial, stronger-amplitude search or expanded grid follows a result.

fixed prior variances are `{0} ∪ {10^x: x=-8,-7.5,…,0}`: eighteen settings. non-null curves contain `2 populations × 2 laws × 4 conditions × 200 truths × 18 = 57,600` grid records, each containing three recovery targets and prediction once. null has three distinct conditions per law, with `half_effect` aliasing `base`: 108 grid records, without fictitious outer replication. keep observed null samples separate by law. assessment requires **1,200 pooled point fits** (`6 cells × 100 histories × 2 representations`) and **600 saved annual-control histories/3,000 annual states**. calibration needs truths, not response files. record time/memory/output costs; stream histories and retain compact per-cell archives, not directories per grid setting.

prepare a finite source inventory from the six named fit manifests. open statistics and `history` control chains only for assessment ids 100–199; calibration 0–99 uses deterministic truth identities from manifests. also bind the result's named `assessment` reference by digest; select its 600 final-year records by `(family,population,law,outer,year)` for saved `R_control,R_zero,P_control,P_zero`. decode each selected five-year chain under its strict source contract. bind historical metadata by digest and selected fields without recursively traversing unrelated `consumed` references. avoid 04g's convenience `read_prepared` path through the complete 04f inventory. checking saved posterior/objective equations is permitted validation, not a new annual fit or search. no corpus scan, directory discovery, source mutation or compatibility fallback. missing inputs stop with located reasons.

## pooled estimator and temporal meaning

reuse annual residualized information `H_y`, native shape score `T_y`, context mean `ybar_y` and design mean `xbar_y`. let `S_y` select current offense/defense rows from the ordered union of seen identities. retain separate context for every season, even when labels repeat:

```text
H* = sum_y S_y' H_y S_y
Q* = sum_y S_y' T_y B_d
K_a = (H* + a^-1 I)^-1
beta_a = K_a Q*
L(a) = d logdet(I + a H*) - trace(Q*' K_a Q*)
```

use factorization/solves, reusing fixed-design factorizations across records; omitted native response energy is constant across the grid. `a=0` is the exact zero-map model with `beta=0,K=0,L=0`, handled explicitly, not by an epsilon prior. choose smallest finite `L`, ties to smaller `a`; no continuous refinement. the same gaussian working marginal-likelihood selector is used under game pace. it receives training moments only, never truths, oracle choices or assessment results. endpoints are range limitations, not optimizer failures.

report coefficients centered with final-season exposure weights padded with zero for absent identities. saved moments contain the full response: reuse shape residualization `T_h=T-T.sum(axis=1,keepdims=True)*p` and `ybar_h=ybar-ybar.sum(axis=1,keepdims=True)*p`, then final context `A_h5=ybar_h5-xbar5*S5*centered_beta*R_d'`. `T_h B_d=T B_d` because `p'B_d=0`; use the explicit residualized form consistently with existing fitting. never pool context across years or fit assessment context. retain uncentered algebra for risk calculations. entrants 32/33 receive only their own observations; retired players remain nuisance rows. player 8 returns into a different slot and can have a changed true field: retain its identity/history and expose this persistence misspecification. do not average annually centered maps or transfer predecessor observations to an entrant.

reuse the unchanged forty-mode annual `history` control, including its original scale-selection method, for both pooled representations. the eleven-mode comparison changes representation as well as temporal estimation; even the forty-mode benchmark changes the scale-selection procedure. these are benchmark contrasts, not isolated causal tests of pooling. 04g's population-shrinkage result is historical evidence, not an additional arm. score all current identifiable combinations, including transition effects; never silently drop the changed returner.

## exact fixed-family risk

these are expected risks under known simulated laws, conditional on designs and physical truths, not calibrated player intervals or lower bounds for other estimators. implement small contractions, not a covariance over every recorded count.

write unscaled physical shape as `M_y=truth['raw']`, row mean `mu_i=e_i*r*(p+alpha*x_i*M_y)`, and embedded residualized design vector `v_i=S_y'*(x_i-xbar_y[stratum])'`. do not substitute `truth['centered']`: its compensating context would also be needed, and omitting it changes the game-pace noise law. centering belongs to output/scoring. each game includes both directional rows under the same pace:

```text
gaussian:  Cov(N_i) = e_i*r*diag(p); independent rows
game_pace: Cov(vec N_g) = diag(vec mu_g) + .5 vec(mu_g) vec(mu_g)'
m = E Q* = sum_y S_y' H_y (alpha*M_y B_d)
q_g = sum_(i in game g) v_i (mu_i B_d)
```

`m` uses each year's actual truth, not `H*` times final truth. for native scoring operator `V` (regions or a named functional), set `D=R_d' V`:

```text
C_V = sum_i v_i v_i' sum_j mu_ij ||(B_d D)[j,:]||²
      + .5 sum_g (q_g D)(q_g D)'                  # game pace
C_V = ||D||_F² H*                                # gaussian
F = J5 S5
E recovery(V,a) = r²/64 * (
  ||F K_a m D - J5(alpha*M5)V||_F²
  + trace(F K_a C_V K_a F'))
```

`J5` is 04g's final identifiable/exposure-centered operator; require rank 60 and its existing cutoff sensitivity. the inseparable 26/31 average retains weight two; their individual difference stays `not_estimable`; the denominator remains 64. report bias and variance. keep physical truth in the target: spatial projection and estimation errors can have a regional cross term and must not be added as orthogonal squared errors.

full-lineup **spatial** prediction uses final evaluation rows `z_i=x_eval_i-xbar_train5[stratum]`, weights `w_i=e_i/sum(e)`, `G=sum_i w_i z_i'z_i` and native inverse-share metric. it does not assess fitted volume or complete-intensity validity. form `C_P=E[(Q*-m)(Q*-m)']` by the game-pace contraction above with `D=I_d`; gaussian gives `d H*`. retain the final-context cross-score vector:

```text
f_s = (sum_(i in final stratum s) v_i sum_j mu_ij ||B_d[j,:]||²
       + .5 sum_(g in final year) q_g (sum_(i in g,s) mu_i B_d)') / (r E_s)
```

`E_s` is final training context exposure in hours. gaussian gives `f_s=0`; game pace generally does not. with `zbar_s=sum_(eval i in s) w_i z_i`, expected excess over the noisy no-player training-context predictor is:

```text
bias_map = S5 K_a m R_d' - alpha*M5
player_error = r² * (sum_i w_i ||z_i bias_map||²_(diag(p)^-1)
                     + trace(S5' G S5 K_a C_P K_a))
signal = r² * sum_i w_i ||z_i(alpha*M5)||²_(diag(p)^-1)
coupling = 2 r² * sum_s zbar_s S5 K_a f_s
expected_excess = player_error - signal + coupling
prediction_gain = -expected_excess
```

for `k` independent game copies multiply `H*,m,C_V,C_P` and final context exposure by `k`; `f_s` stays unchanged. evaluation weights/references stay fixed. preserve signed coupling. at exact null, projected game means vanish, so fixed-family curves must agree between laws; adaptive fits can differ.

select **one variance per population/law/condition** minimizing mean exact twelve-region risk across calibration truths 0–99; ties to smaller variance. reuse that choice for the explanatory functionals, without separate tuning. the single analytic null selects `a=0` without fictitious calibration truths. freeze before assessment on truths 100–199. never choose hindsight optima separately for noisy assessment records. show complete grid curves without reselecting from assessment minima. the reference uses known truth, cannot be deployed and need not outperform every adaptive rule.

**adaptive risks use realized errors from saved-response fits.** evaluating fixed-variance formulas at response-selected variances does not account for selection and is prohibited. exact formulas apply only to fixed-grid curves and the independently chosen common reference. `half_effect`/`double_games` have no adaptive/annual assessment: mark `not_run` rather than extrapolate.

## assessment and content

primary recovery stays `R=r²/64*||J5*(shape_hat-alpha*M5)*W||²_F`, in squared attempts per 60 team minutes. report `R`, zero risk, their ratio where defined, and `sqrt(mean(R)/12)` as rms error per region/player-role. `sqrt(mean(R))` is a regional-vector norm, not per-region error. average before roots/ratios. null ratios are unavailable; show absolute false-map risk.

two explanatory functionals reuse `W`: sum both sides of `in_zone_0_10` and `in_zone_10_20`; and half the positive-y minus negative-y mass across all regions. label them **within 20 ft, in front of goal** and **lateral redistribution**. single-functional rms is `sqrt(mean(risk))`, without division by twelve. they describe redistributed recorded unblocked attempts/60, with unchanged total rate; neither is xg, total offense, high danger or handedness. show offense and attempts allowed separately. retain actual truth and omitted-detail evidence for eleven modes.

at base/broad, pair annual-versus-pooled realized recovery/prediction errors on identical saved responses. compare adaptive realized recovery with the independently selected fixed-reference expected recovery, naming the different calculations. retain `.75*mean(R_zero)-mean(R)` as a labeled historical reference, **not a new nomination or absolute-accuracy gate**. show selected variances/endpoints. intervals crossing zero establish neither equivalence nor noninferiority.

bootstrap the 100 assessment records 10,000 times with `PCG64(SeedSequence([40901,population_id,law_id]))`; sparse/diffuse/null ids 0/1/2, gaussian/game-pace ids 0/1. reuse indices across conditions/metrics/arms; use linear 2.5/97.5 percentiles. recompute averages/roots/ratios in each draw; hold calibration-selected variances fixed. these describe mean experimental risk conditional on designs, calibration set and selected reference; reference-selection uncertainty and individual-player precision are not covered. analytic null has no outer sampling interval; observed null fits retain their intervals. comparisons are descriptive, without a conjunctive pass/fail gate.

partition full centered errors afterward for offense/defense, physically active/inactive rows, entrants 32/33 and returner 8; retain full-target denominators and signed accounting. year five is the target; no new annual trajectory gallery. source-selected control limitations remain visible and cannot justify dropped records.

bind [04a result](../research/attribution-04a/result.json), sha256 `8b1f9bfd2ba48acf81f7c23db97d5e37c81bc2e17cec86666f0aece4551a49ac`, as contextual metadata only. use `population.annual` and `resolution.exposure_quartiles` for unblocked data: final median exposure about 734.2 minutes versus synthetic mean 742.5; annual rates about 40.98–42.17 versus synthetic 40. equal minutes do not imply equal lineup information. omit the scalar-population shared-pair fact; a real spatial deployment spectrum is unavailable. no substitute 05a population or new scan.

content design delivers one concise `decision.md`, one complete comparison table, one limits/context table and one figure. fixed curves use assessment truths 100–199 and mark the calibration-selected variance. adaptive aggregate errors occupy a separate categorical panel, never a point at the mean/median selected variance. show every condition and contrary result. labels: “annual borrowing, 40 spatial modes”, “pooled history, training-selected” with its mode count, “fixed penalty selected with calibration truth — diagnostic”; identify its twelve-region selection loss. repeat the unchanged annual baseline explicitly when comparing eleven modes. label prediction as spatial/inverse-share-weighted; distinguish spatial modes from the rank-60 player target. axes state physical units, averaging, exposure and law; mean-risk intervals cannot look like player uncertainty. the limits table names four teams/eight slots, randomized deployment, inseparable pair, changed returner and unavailable real deployment spectrum.

the decision recommends at most one subsequent question: temporal estimation/selection if the learnable benchmark helps; selector/prior assumptions if the fixed reference shows unused potential; or resolution/evidence if improvement needs broader/stronger-information conditions. `unresolved` is valid. cite recovery and prediction evidence; no automatic causal diagnosis, narrower product claim, successor campaign or admission follows.

## owners, api and artifacts

| owner | bounded responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | selected-source decoding and identity-aligned pooling; reuse reference/centering/rank checks |
| `analysis/src/hockey_stats/attribution.py` | pooled finite-grid marginal selection and fixed solves through `fixed_shape_update`; no duplicate posterior or fictional annual state |
| `analysis/src/hockey_stats/attribution_simulation.py` | shared deterministic truths and known noise-moment contractions; preserve old streams/laws |
| `analysis/src/hockey_stats/attribution_prediction.py` | shared prediction/excess and expected-coupling arithmetic |
| `analysis/research/attribution_resolution.py` | conditions, splits, expected recovery, diagnostic comparisons, cli and reports |
| `docs/research/attribution-04h/` | eventual protocol/result, decision, verification, tables and figure |

extract reused truths/region construction from study-local functions when needed and update callers, preserving checked outputs. no historical reruns, generic framework, public api or unrelated migration.

paired-null controls use schema-4 `read_pooling_annual` with the explicit `PoolingSource`; independent controls use schema-5 `read_regularization_annual`. reuse loaded statistics and explicit chronological predecessors. these are named source contracts, never automatic fallback or migration.

`read_regularization_source_slice(result_ref, cells, assessment_ids)` returns the bound basis/design/operators, truth metadata, selected statistics/control references and saved assessment scores under the explicit 04g source contract. the study owns the six-cell/id selection; the decoder never opens unselected chains. `pool_shape_likelihood(populations, basis, columns, target_season)` returns union/current identities, common `r/p`, pooled `H/score`, target context/reference and source identity. `fit_pooled_shape(pooled, variances)` returns selected variance, grid objectives, centered `Theta/V`, target context and diagnostics. `V` is the working conditional covariance for numerical verification, not validated uncertainty. the selector accepts no truth. expected-risk operations take known-law moments and a fixed variance separately. pooled results record basis columns explicitly; eleven-mode results cannot masquerade as `AnnualState`/`graph_40ft`.

```text
prepare --source-result <04g-result.json> --real-context <04a-result.json>
        --purpose research|fixture_exercise --output <new-directory>
fit --prepared <prepared.json> --population sparse|diffuse|null
    --law gaussian|game_pace --output <new-directory>
assess --prepared <prepared.json> --fits <six-explicit-fit.json-paths> --output <new-directory>
```

`prepare` freezes the spec/protocol, identities, inventory, ordering and budgets. each `fit` creates fixed-risk curves, calibration choices and assessment pooled fits, without research response generation. `assess` reads outputs, reconciles, bootstraps and reports; no fitting or selection there. no controller, search expansion, resume system or new dependencies.

use existing finite-json/exclusive-write/array-reference primitives, new `attribution_resolution_{protocol,prepared,fit,assessment,result}` kinds and schema version 5. references are `{path,sha256}`; identify executing and source producers separately. one compact archive per cell plus manifest; declared axes, names, dtypes and shapes are verified, not inferred from filenames.

- **prepared:** six cells; split/conditions/grid; native/basis/region/entity digests; selected statistic/control references; real-context fields; purpose/counts. reject wrong laws, references, source swaps or duplicate/missing outer ids.
- **fit:** fixed curves indexed by `(outer,condition,prior_variance)`, with a three-target axis for `risk,bias_squared,sampling_variance,zero_risk`, and `prediction_excess,coupling` once per grid record; null aliases; calibration selections; assessment `selected_a/objectives/Theta/V/context`, source-control scores, functionals/transitions and costs. target order is twelve-region vector, within-20-ft, lateral. per non-null cell, recovery arrays are `(200,4,18,3)` and prediction `(200,4,18)`; analytic null omits outer replication: `(3,18,3)` and `(3,18)`. condition/grid ordering follows the tables above. outer ids 100–199 index adaptive results; rank-specific coefficient arrays have shapes `(100,68,40)` and `(100,68,11)`, covariance `(100,68,68)` per rank, context `(100,6,656)`, objectives `(100,18)`. full-grid records preserve original region units. no opaque estimator or player intervals.
- **assessment:** exact completeness, paired summaries/intervals, historical-reference margins, report refs and limits. unavailable ratios/absent calculations carry reasons, never nonfinite placeholders.
- **result:** `execution_status:complete`, `numerical_status:verified|unresolved`, `study_status:diagnosed|numerically_unresolved`, `next_question:temporal_selection|penalty_selection|resolution_evidence|unresolved`, and null nomination/handoff with `admission:not_admitted`. input/incomplete execution writes no completed result. numerical failure preserves evidence and permits only an unresolved next question.

research requires a clean identified producer and verified selected external inputs. new outputs use `/Volumes/Expansion/hockey-stats/runs/attribution-04h-<date>/`; compact reviewed reports go in git. preserve original evidence. ordinary i/o failure stops; manual rerun suffices.

`fixture_exercise` accepts an explicitly identified schema-5 04g fixture source: six selected cells, outers 0/1, five years and the same player/native/basis dimensions. use calibration `{0}`, assessment `{1}`, the same grid/conditions and the source's declared stable identification rank. this gives 576 non-null/108 null grid records, twelve pooled fits, six control histories/thirty states; replace adaptive array leading dimension 100 with 1. probe id 1 at both representations. the smaller design and fixture basis retain their own identities; temporary fixture generation is verification only. no fixture interval or conclusion satisfies research acceptance, and no permanent fixture runner is added.

## delivery and acceptance

non-overlapping boundaries, each with independent adversarial review:

1. **source/pooling:** temporary red → green → refactor → green integration checks bind selected inputs and compare moments/coefficients with direct stacked rows and separate annual context. include reordered identities, entry/absence/changed returner, unequal references and inseparable averages. preserve historical decoder behavior and the no-truth selector interface.
2. **risk algebra:** independently construct tiny full count covariance under both laws and compare with collapsed recovery/prediction/coupling formulas. include nonzero physical exposure means, nonzero game-pace coupling, null law equality, independent-game doubling versus shared-pace duration, and actual-truth coarse bias. compare empirical scores with direct exposure rows. no monte carlo convergence campaign is required for covariance verification.
3. **bounded execution:** six cells, 57,600 non-null/108 null grid records and 1,200 pooled fits reconcile; all 600 source control histories replay their final scores. every solve `A X=B` satisfies `||A X-B||_F/max(1,||B||_F)<=1e-8`. independently enumerate the same grid with an eigensolve at outer 100/base and 199/broad in each cell: twelve probes. posterior/objective/risk agreement uses `atol=1e-10,rtol=1e-8`; a changed winner must also agree in objective and predictions within those tolerances, otherwise numerical status is unresolved. no enlarged search or replacement samples.
4. **assessment/content:** independently recompute one full non-null cell and one observed-null cell from saved arrays, including paired intervals, reference-selection separation, roots/units and counts. inspect the figure and reconcile every shown point to its table. distinguish analytic conditional risk, adaptive realized risk, simulation evidence and real-context summaries.

remove temporary integration/live checks, controllers, bytecode and test-only dependencies after verification, as requested. retain fixtures, scientific tools and useful receipts. no lasting harness is assigned; [07](07-lightweight-testing.md) owns separately selected checks. preserve a newly encountered distinct real-source reproducer under the existing fixture policy if applicable.

completion is a reconciled bounded diagnosis, including an unresolved substantive finding. tradeoffs: constant pooling can bias changing players; eleven modes lose detail; finite settings and conditional intervals limit claims; two-law moments add algebra but avoid new simulations; exposed cases supply no fresh confirmation. real-player recovery, complete-rate adequacy, calibrated uncertainty and supported chance valuation remain open.
