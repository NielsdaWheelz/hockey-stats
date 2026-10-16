# pr04b — separate spatial shape and assess refit uncertainty

status: **complete and verified on 2026-10-16.** the [decision](../research/attribution-04b/decision.md) records the mixed scientific result; [verification](../research/attribution-04b/verification.md) records the full numerical budget and independent reviews. the user selected an additive shape revision and full historical refits. [the plan](../plan.md) owns progression. [04a](../research/attribution-04a/decision.md) remains the corrected historical benchmark; no admission or publication follows from this study.

## question, target and boundary

does allowing spatial shape to select its own annual borrowing improve native-grid recovery, and which player contrasts have usable uncertainty after refitting whole historical chains?

one revision package: retain the additive mean, separate spatial **volume** from **zero-sum shape**, and assess game-reweighted refit intervals beside conditional working intervals. keep all 656 native cells, the two matched populations, five seasons, context design and age-neutral annual transitions. no spatial truncation, neighbor smoothing, positivity link, new predictors or extra recipe. the all-attempt scalar and matched unblocked volume are unchanged controls.

the claim remains **recorded-rate association**, conditional on admitted evidence and stated references. [magnus 9](https://hockeyviz.com/txt/magnus9EV) motivates additive spatial effects and annual borrowing; it does not validate this covariance, uncertainty procedure or current private-model parity. negative signed effects are legitimate; negative complete rates remain an intensity limitation. no clipping, discarded zero-event exposure or rebranding as supported ability.

non-goals: source acquisition/reconstruction, chance fitting/admission, repeated valuation/location stresses, aging, coaches, richer deployment, cards, publication, causal isolation or a general model/experiment framework. keep correct inactive features. positive intensity, spatial smoothing and richer historical/context models remain alternatives requiring their own evidence, not automatic follow-ons.

## fixed inputs and references

read the corrected external root `/Volumes/Expansion/hockey-stats/runs/attribution-04a-20261014-02/`:

- `prepared/prepared.json`, sha256 `b771cdc1784a72cf0db6be47b9eb0f597af542bb9cace1f339ba40002265cd8a`, and every artifact it binds;
- the ten corrected annual states and completed assessment bound by [04a's result](../research/attribution-04a/result.json); reject the invalid original run;
- exact annual row ledgers, native grid, masks, population ids, rates, ordered players/strata and outcome-blind pairs. preserve the two original pairs `(8476460,8478398)` and `(8480336,8480800)`; unavailable remains unavailable.

reuse 2021–22 through 2025–26 and all 6,560 inventory games. population coverage is the existing matched ledger, not a claim that every game/second is admitted. scalar and spatial counts/time remain separate; no new eligibility filter. preserve source exclusion evidence and counts byte-for-byte. 04a's `population_id` includes its old protocol: retain it as **source-population identity**, separate from the new model-protocol hash. do not restamp old preparation.

freeze each population's original annual team rate `r`, exposure-centering vector `u`, player universe and context columns. spatial `p` is exactly the positive first-season native share vector used by corrected 04a; `D=diag(p)`. keep `p` fixed across years and refits. these reference choices deliberately remain conditional, not estimated anew by the bootstrap.

## one estimator, three annual blocks

reuse 04a's `e=seconds/3600`, `w=e*r`, `Y=N/(e*r)`, skater design `X` and flat context design `Z`. scalar population has its existing single block. for the spatial population:

```text
t = Y 1                         # volume, one response
C = Y - t p'                    # zero-sum shape, C 1 = 0
S_h = D - p p'                  # rank 655; never invert it
B_map = m_t p' + M_h            # M_h 1 = 0
A_map = a_t p' + A_h            # same decomposition for context
Cov(vec B_map) = (p p') ⊗ V_t + S_h ⊗ V_h
```

fit volume and shape with independent working priors, full cross-player/offense-defense row covariance in each block, and their **own** entry variance and annual innovation. shape uses all 655 zero-sum directions; no basis truncation or per-cell variance search. this replaces scalar-selected shape shrinkage; it does not smooth neighboring cells or make complete rates nonnegative.

reuse the corrected cholesky posterior, chronological carry, entrants, absent-year innovation, centering and context compensation. each block carries its own previous mean/covariance; first-year means are zero, entrants receive that block's first-year entry variance, and existing states receive its current innovation. all rows, including absent players, undergo the same original `u` centering. never invert a centered covariance. no later evidence revises an earlier saved point fit.

volume scale selection is unchanged. for shape, residualize within `Z` using current weights, set `H=Xr'Xr`, `T_h=Xr'Cr`, `V0=L L'`, `K=I+L'HL`, `b=T_h-H M0`, and use:

```text
zsz = sum_j ||Cr[:,j] - Xr M0[:,j]||² / p_j
objective_h = 655*logdet(K) + zsz - sum_j b[:,j]' V b[:,j] / p_j
V = L K^-1 L'
M = M0 + V b
```

this is the shape restricted marginal likelihood on the zero-sum subspace. summing shape responses before scale selection is INCORRECT: their sum is zero. obtain `zsz` from shape response cross-products; old `AnnualPopulation.yy` contains only the volume quadratic and is insufficient. form `b D^-1 b'` once per annual scale search, then contract it with each candidate `V`; solve the full response mean only at the selected scale. no singular inverse or player×cell kronecker allocation.

keep 04a's variance range `[1e-8,1]`, 17 log-grid points and one bounded refinement (`xatol=1e-4,maxiter=40`), smaller-variance tie rule and `scale_unresolved` handling. each block has its own scale curve/status. no expanded bounds, extra starts or outcome-driven tuning. missing finite states stop dependent work; endpoint winners remain explicit scientific limitations.

point-fit budget: five new shape fits, with the ten original scalar/volume states replayed through the shared arithmetic as controls. means, covariances, contexts and annual transitions require `max(abs(new-old))/(1+max(abs(old)))<=1e-8` per array. compare scalar/volume state, not a combined map whose shape intentionally changes. do not rerun unrelated 04a source preparation or chance scoring.

for player contrast `c` and response functional `v`, the single projection owner computes:

```text
mean = r * c' (m_t p' + M_h) v
working_variance = r² * [(c'V_t c)*(p'v)² + (c'V_h c)*(v'S_h v)]
```

`v=1` is exactly volume; regional functionals use existing `REGION_NAMES`. scalar population uses its one block. any fixed transport/projector must act on both response covariance terms. actual game fluctuations can couple volume and shape: refit intervals project each JOINT replicate, never add separate interval widths or standard errors. defense is opponent creation internally; negate once for displayed suppression.

## full historical refit uncertainty

use **200** complete weighted historical trajectories. draw independent `Exp(1)` weights for sorted inventory game ids in each season, normalize their sum to that season's game count, and apply the same game weight to every row/direction/cell and both populations. include games with no admitted rows in the common inventory. positive weights retain the observed player/context topology. independent seasons, fixed `PCG64` seed contract below; no resampling stints as independent observations.

each trajectory starts from zero prior and refits all three blocks across five years, including every scale search and complete covariance carry. multiply original row weight `w` by the game multiplier. recompute weighted context means and residualized statistics: reweighting already residualized global `H,T` is invalid. keep original `r,u,p`, player ordering and references throughout the trajectory. this includes fitting, scale-selection and propagated historical variation; it excludes reference uncertainty, unseen players, cross-game dependence, source error and model misspecification.

group unresidualized moments by game, stratum and local player ids. with multiplier `a_i`, preserve `E_s=sum(a_i*e_i)`, `X_s=sum(a_i*e_i*x_i)`, `N_s=sum(a_i*n_i)`, `H_e=sum(a_i*e_i*x_i*x_i')`, `T_raw=sum(a_i*x_i*n_i')`, `Q_t=sum(a_i*(sum(n_i))²/e_i)` and `Q_h=sum(a_i*(sum(n_ij²/p_j)-(sum(n_i))²)/e_i)`. then `H=r*(H_e-sum_s X_s*X_s'/E_s)`, `T=T_raw-sum_s X_s*N_s'/E_s`; residualize both quadratics analogously and divide by `r`. `T_h=T-(T*1)*p'`. weight each raw contribution once; never square the game multiplier. retain sparse/game-local moments, not one global dense Hessian per game.

report 95% **basic game-refit intervals**: `[2*estimate-q97.5, 2*estimate-q2.5]`, with `numpy.quantile(method="linear")`. retain 95% gaussian working intervals separately. neither is total ability uncertainty; never add their variances or call the refit distribution a posterior. normalized exponential weights have a [published bootstrap precedent](https://people.eecs.berkeley.edu/~jordan/sail/readings/rubin.pdf); validity for this regularized temporal estimator is the question tested here, not an inherited theorem.

no failed-draw replacement or reduced denominator. numerical failure makes the affected assessment incomplete; a finite bound-selected state remains in the distribution with its status. retain the fraction of unresolved scale searches and inherited limitations. no favorable-model selection within draws.

an exact persistent co-deployment null direction cannot become identified through reweighting. detect identical same-role membership histories over the observed prefix, including absence/entry, and independently verify likelihood-null differences. any contrast with unequal coefficients within such a group has a null-direction component: this includes either individual player, not just their difference. set its empirical interval and meaningful claim to null with `not_data_identified`; retain the point estimate, raw replicate spread and prior-conditioned working interval as diagnostics. do not label a collapsed bootstrap difference equivalent to zero. equally weighted group sums remain assessable. this guard covers exact persistent duplicates, not all possible near-confounding or temporary shared deployment; no generic identifiability certificate.

save refit projections for final-season current-player scalars and regions, and native cells for the four frozen real example players and their two pair contrasts. use the same replicate ids across projections. preserve base annual states, replicate projections, weights/seeds, selected scales and numerical statuses; do not archive every replicate's full covariance matrix. completed projections survive later failure; explicit manual replicate ranges may resume missing work without a runner or checkpoint engine.

## native-grid recovery and prospective criteria

freeze the generator, contrast list and rules before evaluating the candidate. reuse 04a's four-team/eight-skater, 96-game, 50-stint, five-season design and entry/return schedule. use its **paired** design in both cases: team four's players 26/31 always share deployment; other teams mix. retain scalar truths, entrant 32/33 and returner 8, and the year-four player-1 change. synthetic inputs remain labeled matrices, never raw captures.

replace the four-cell response with the native 656 cells and frozen real `p`. simulation references are known `r_U=40,r_all=55`, native `p`, and design exposure `u`; this tests the declared reference-conditional procedure. it does not validate estimation of these references. pass references explicitly to the numerical fitter; never fabricate `response_counts` to obtain them. scalar effects multiply `p`; replace the old four-cell shape truths with opposite zero-sum effects on offense players 3/4 (broad) and 18/19 (localized):

```text
h(g)_j = .10*p_j*(g_j - sum(p*g)) / max(abs(g - sum(p*g)))
broad g: +1 on nearest-net cells reaching half of p mass, -1 elsewhere
local g: exp(-||center-(80,15)||²/200) - exp(-||center-(80,-15)||²/200)
```

order broad cells by distance to `(89,0)`, then native index; include the threshold-crossing cell. assign `+h/-h` respectively. center generating offense, defense and shape by each year's fixed design exposure BEFORE generating counts, so 40/55 remain expected league team rates. map sums remain the centered scalar truths; shape effects are NOT a per-cell 5% contrast. compute all true responses and check every generating rate is positive before execution; no clipping or redrawing.

two cases × **200 independent outer replicates**:

- `gaussian`: independent count-unit normal responses with unblocked means `e*40*(p+X*B_truth)` and variances `e*40*p`; blocked mean `e*15*(1+X*b_truth)` and variance `e*15`. signed/noninteger draws are deliberate synthetic matrices.
- `game_pace`: poisson counts at those means times one `Gamma(shape=2,scale=.5)` multiplier per game, shared across stints, directions and cells. expected rates and known effects stay the same.

within EACH outer replicate, fit the shared-volume 04a control and revised base chains, then run the same 200-refit revised interval procedure. reuse actual shared fitting/scale mechanisms; no second numerical implementation in the simulator. control and revision see identical responses. this is **400 outer replicates and 80,000 inner historical trajectories (1.2 million small annual block fits)**, not a cheap four-cell smoke test. retain per-game sufficient statistics once; never regenerate responses in inner refits.

freeze design `PCG64(40400)` through the existing paired-design construction; response streams use `SeedSequence([40420,case_id,outer_id,year_index])`; inner weights use `[40421,case_id,outer_id,draw_id,year_index]`; real weights use `[40422,draw_id,year_index]`. zero-based case/replicate/draw ids; sorted game, stint, direction and native-cell order. separate streams prevent parallel scheduling from changing results.

assessed contrast cells are fixed, not chosen from plots:

| claim | projections / years |
|---|---|
| native shape | offense `3−4` and `18−19`; map error in years 1 and 5, final-year comparison primary. coverage at each map's maximum absolute true-effect cell (native-index tie), and all six fixed regional totals, in years 1 and 5 |
| volume and meaningful labels | offense pairs `2−5`, `6−2`, `7−2` in year 5, both scalar populations: true differences `0,.05,.10` of the known reference; no shape assigned to these players |
| annual transition | entrant 32 offense and entrant 33 defense in first observed year 3; returner 8 offense in year 4; both scalar populations |
| inseparable players | offense `26+31` and `26−31`, years 1 and 5, both scalar populations; only sum has empirical recovery claims |

truth undergoes the same known centering as the estimate. pair differences cancel the center; single players and paired sums do not. preserve exact scalar truth ticks/algebra for `0,.05,.10` boundary decisions, not subtraction of rounded centered maps or sums of 656 floating values. report all other player/year/region results descriptively. the independent coverage/error unit is the outer replicate, never cells or correlated players.

freeze **12 nomination coverage cells**, avoiding an accidental all-diagnostics gate: final-year broad/local peak cells in both noise cases (4); entrant 32 offense/entrant 33 defense at entry and returner 8 offense on return, all spatial-volume (3); final-year all-attempt scalar pairs `2−5,6−2,7−2` (3); final-year spatial-volume `7−2` and paired sum `26+31` (2). **all eight scalar cells use `game_pace`**, and the false-claim criteria apply to these eight. other assessed cells retain the same support classification and every failure, but cannot enlarge a nominated claim. no simultaneous or universal calibration claim follows from this finite set.

prospective developmental rules:

1. **shape improvement:** for each broad/local contrast and each noise case, compute the paired reduction in final-year native integrated squared map error `sum_j(error_j²)` from control to revision. use a 10,000-resample paired outer-replicate bootstrap, `SeedSequence([40423,case_id,contrast_id])`, percentile 95% interval. lower bound `>0` supports that specific gain; upper bound `<=0` fails it; otherwise inconclusive. report normalized error, bias, all-player map error and pure-volume controls too. no claim of universal superiority.
2. **interval recovery:** a two-sided 95% wilson interval for truth coverage entirely above/equal `.90` supports the declared coverage floor; entirely below fails; overlap is monte carlo inconclusive. **game-refit intervals are primary**; working intervals are diagnostics. this is a **90% developmental floor for nominal 95% intervals**, not a certificate of calibrated 95% coverage. report both procedures for every assessed cell; only the frozen 12 enter nomination.
3. **false claims:** use the original strict 5% meaningful-band rules for scalars only. for truth `theta`, wrong assertions are: positive zero-exclusion with `theta<=0`; negative zero-exclusion with `theta>=0`; `meaningful_positive` with `theta<=.05`; `meaningful_negative` with `theta>=-.05`; or `within_meaningful_band` with `abs(theta)>.05`. count one `any_false_claim` boolean per replicate, denominator **all 200**, even if no assertion is made; show components separately. a wilson upper bound `<=.10` supports this developmental false-claim ceiling; lower bound `>.10` fails; otherwise inconclusive. true 5% is a boundary: asserting strictly more than 5% is an error, not detection power. no 5% threshold on cells/regions or chance values.
4. **null handling:** no empirical directional/equivalence assertion for `26−31`, player 26 or player 31 individually in any replicate, or analogous real contrasts with a persistent duplicate-group null component. diagnose the raw collapsed spread and prior dependence, and assess the sum separately. more draws cannot identify the difference.
5. **usefulness:** report widths, zero-exclusion at true 5%, meaningful separation at true 10%, and near-zero resolution at true zero. no universal power gate or requirement that every real pair resolves. wide intervals may pass recovery while providing little useful resolution.

criteria apply claim by claim; no pooled average can erase an entrant, local-shape or null failure. present a named support matrix and `supported|failed|inconclusive` for each rule. the joint nomination is conservative and can remain inconclusive despite good individual cells; no multiplicity-adjusted or simultaneous-map claim. a limited supported claim cannot become blanket model acceptance. do not rerun until monte carlo intervals land on a preferred side.

## native real behavior and decision

one streamed real assessment must reconcile the same ledgers and verify map sums, centering and scalar controls across all five years. preserve 04a's negative complete scalar/total/cell diagnostics, including row×cell exposure-weighted frequency, minimum and located example. additionally report negative mass `sum_i e_i*sum_j max(-mu_ij,0)/(r*sum_i e_i)`; distinguish it from frequency. compare all metrics to the unchanged control, using identical exposure. zero-event rows remain. even nonnegative predictions on inspected rows do not make this unconstrained additive family a nonnegative intensity model; the user chose signed additive research.

decision fields separate numerical completion, native shape gain, interval recovery, null handling and meaningful resolution. `nominate_revision` requires all four primary shape gains, the 12 refit coverage cells and eight false-claim cells supported, plus correct null handling. otherwise use `mixed` if some claim groups are fully supported; `withheld` if none is supported and any nomination rule fails; `inconclusive` otherwise. groups are native shape (broad/local separately), volume, annual transition and paired sum; each requires its nomination cells, while other findings constrain the reported scope. exact-null correctness is a software requirement. incomplete numerical execution has no scientific verdict. unresolved scale searches accompany affected claims; finite bound-selected states are not discarded. no new fit follows automatically. always `admission:not_admitted,handoff:null`; [uncertainty](../issues/attribution-working-uncertainty.md), [complete-rate](../issues/attribution-negative-rates.md) and supported [04](04-player-attribution.md) contracts remain distinct.

## owners, interfaces and artifacts

`immutable 04a rows → grouped sufficient statistics → separate annual blocks → joint refit projections / recovery → research decision`.

| owner | exact responsibility |
|---|---|
| `attribution_data.py` | `prepare_revision(prepared,protocol,out)` validates old evidence and derives shape/grouped statistics; `weighted_population(grouped,game_weights,references)` recalculates context residualization. no raw parser, new masks or fitted policy |
| `attribution.py` | shared posterior/scale/transition arithmetic; explicit scalar and volume/shape annual states; `fit_revision_year(population,previous)` and `project(state,c,v)`. shared-volume composition survives only as the named scientific control, not a fallback |
| `attribution_uncertainty.py` | narrow `refit_history(prepared,protocol,draw_id,projection_requests)` returning requested `(year,population,contrast,functional)` joint projections plus scale/numerical evidence; synthetic requests include earlier years, real requests only the final year. exact-duplicate history diagnostic; no generic scheduler or model registry |
| `attribution_valuation.py` | adapt existing linear transport/projection consumers to the two covariance terms where affected; no new reference scoring or repeated valuation campaign |
| `analysis/research/attribution_revision.py` | frozen generator/cases/contrasts, manual commands, comparison rules and figures. extract only actually reused simulation mechanics from `attribution_feasibility.py`; no imports through historical controllers |
| `docs/research/attribution-04b/` | protocol, result, decision/figures and verification; statistician owns claims, systems reviewer identity/numerics, content designer labels and graphics |

reuse `artifacts.py`, native grid/regions, exclusive outputs, finite json, sha256 refs and non-pickle npz. typed contracts, no new numerical/storage dependency. hard-cut current attribution consumers to the new state; old schema-1 artifacts have one explicit read-only control reader, never automatic conversion/fallback. do not migrate historical evidence or reproduce posterior/projection arithmetic in a controller.

the control reader validates old protocol/prepared/previous links and reconstructs prior covariance through its preceding state, as the current reader does; that covariance is not an old npz field. interpret its spatial control as `m_t=M*1`, `M_h=M-m_t*p'`, `V_t=V_h=V`, which exactly recovers `D⊗V`. this is a named comparison, not a second production path.

new manifests use `schema_version:2`, exact kinds below, `purpose:research|fixture_exercise`, implementation identity, protocol hash and consumed `{path,sha256}` refs. protocol has no self-hash. research requires the exact corrected inputs and full budgets above. fixture purpose permits explicitly synthetic/compact native-grid inputs and smaller declared counts through the same paths, without claiming research completion. arrays/ledgers carry manifest-bound shapes/order rather than repeated headers:

the protocol freezes the model producer for preparation, fits, refits and recovery. assessment/result artifacts additionally bind that `model_implementation` and their own clean reporting `implementation`; a reporting repair consumes the unchanged frozen evidence and writes a fresh output. it does not authorize different upstream producers, new draws, modified thresholds or overwritten results. the named historical control retains its original `M,A` for complete-rate sign diagnostics: decomposing and recombining exact zeros is insufficient for a strict-sign count.

| artifact / kind | required contract |
|---|---|
| `protocol.json` / `attribution_revision_protocol` | spec snapshot, corrected evidence refs, exact block/scale/reference/seed/interval/generator/criteria rules, real/synthetic budgets and output root |
| `prepared.json` / `attribution_revision_prepared` | immutable source-population ids and old manifest hash; separate new protocol id; grid, annual references, players/strata/game order, original ledgers, shape quadratics and grouped-stat refs |
| `annual.json` / `attribution_revision_annual` | benchmark/year/previous hash; current/entrant/carried ids; `r,u,p`; volume block and shape block/null. each block stores centered mean, full row covariance, context means, prior mean/covariance, entry/innovation and scale status. map covariance is derived from these terms, never one fabricated `S⊗V` |
| `fits.json` / `attribution_revision_fits` | completed ordered manifest binding exactly two populations × five annual states, original control identities and common source/protocol refs; `--fits` consumes this file, never inferred directory contents |
| `refit-<id>.json` / `attribution_refit` | draw/seed, source/model identity, five-year block statuses and scales, reference bindings, joint arrays keyed by year/population/contrast/functional; complete/error status. no full per-draw covariance archive |
| `refits.json` / `attribution_refit_range` | explicit requested half-open range, unique draw artifact refs and missing/error ids, source/model/request bindings; a fresh directory per manual range |
| `simulation.json` / `attribution_revision_recovery` | generator identity, completed outer ids, exact truths, paired errors, coverage/false-claim counts and denominators, wilson/monte-carlo intervals, declared-rule classification and unavailable reasons |
| `assessment.json` / `attribution_revision_assessment` | reconciled annual controls/native diagnostics, base and refit projections, separate interval kinds, exact-null status, coverage/scale limitations, recovery support matrix |
| `result.json` / `attribution_revision_result` | evidence refs, completion, scoped scientific verdicts, cost/limitations, one recommendation, `admission:not_admitted,handoff:null` |

for `n` all-seen skaters and `s` observed strata, volume arrays have `M:(2n,1),V:(2n,2n),A:(s,1)`; shape has `M:(2n,656),V:(2n,2n),A:(s,656)` with zero row sums. priors match these shapes, `u:(n,)`, spatial `p:(656,)`; scalar `p` and shape are null. shared arrays/order have one owner, not independently reordered copies.

manual commands: `prepare --baseline-prepared --protocol --out`; `fit --prepared --out`; `refit --prepared --fits --draw-start --draw-stop --out`; `simulate --prepared --out`; `assess --prepared --fits --refits --simulation --out`. `--refits` repeats for explicit range manifests; stop is exclusive and research ids are `0..199`. require matching identities and no duplicate ids across ranges. incomplete/error sets remain reportable but receive no refit interval/scientific verdict; never drop failures to reduce the denominator. existing exclusive-output rules require new directories for resumed ranges. fixture exercises cannot satisfy research acceptance. fitting writes only its explicit output root; no capture or publication side effect.

## content, verification and completion

three static scientific figures, with a content designer defining and reviewing each schema before generation:

1. recovery: control/revision error and working/refit coverage, with truth, monte carlo intervals, entry/return and paired sum/difference visibly distinguished;
2. native maps: broad/local synthetic truth, estimates and errors; frozen real example maps on common axes/scales, matched scalar alongside. state that native cells are parameters, not proven five-foot physical accuracy; pointwise bands are not simultaneous certainty;
3. resolution: the same real pairs and scalar exposure summaries, 5% band, interval kind, units, evidence scope and null reason. no attractive-player selection, rankings or supported-ability labels.

non-overlapping delivery boundaries; independent adversarial review before proceeding:

1. **evidence/statistics:** temporary integration red → green for old-row reuse, grouped weight identity and recomputed context statistics. unit game weights recover original `H,T` and references; independently recompute native shape quadratics and selected full games. no source re-audit unless a new discrepancy requires it.
2. **model/projection:** compare small nonseparable volume/shape results against an independently assembled joint gaussian system. verify original normal equations, `L L'=V0`, covariance symmetry/positive semidefiniteness, centering/prediction invariance, map/scalar/region and transport accounting, entrant/returner chronology, no future leakage and exact nulls. corrected triangular-factor failure receives a specific reproducer.
3. **refits/recovery:** verify weighted contexts, fixed references, three independently carried blocks, no frozen scales/prior shortcut, paired game weights, interval quantiles, seeds, incomplete draws and null-claim suppression. independent checker recomputes selected joint projections and known truths. refactor → green before expensive execution.
4. **bounded numerical/real check:** reproduce all scalar/volume controls. for first- and final-year real shape fits, independently reevaluate the saved winner and its two nearest distinct finite grid points. where an original refinement bracket exists, tighten it once to `xatol=1e-6,maxiter=80`; otherwise retain the endpoint/grid result without inventing a bracket. hold incoming priors fixed and retain original candidates when choosing the lowest objective. maximum movement in league-relative current-player cells, scalars and regions must be `<=1e-4`; report directly recomputed working-label changes too. this is a conditional per-fit check, not a propagated-history/coverage bound or substantive cell-error budget. larger movement withholds affected claims and records an issue; no automatic campaign. check original-equation residuals at `<=1e-8`, covariance symmetry and finite arrays. materially negative variance fails; retain existing bounded-roundoff reporting, including raw variance and tolerance, with zero used only for an interval square root within that tolerance. never clip complete rates.
5. **closure:** execute only the frozen budget, reconcile complete draw/replicate denominators, obtain statistical/numerical/content reviews, record decision/costs, then **delete all temporary tests, controllers and test-only dependencies**. retain the scientific simulator/refit commands, useful fixtures and evidence. [07](07-lightweight-testing.md) stays separate; documentation work now needs no application tests.

freeze the protocol/spec snapshot before execution. measure one real and one nested synthetic trajectory as part of their assigned counts, then record the projected cost without changing the design. 200 real refits alone would cost roughly 14 process-hours at 04a's old two-block speed; the new shape block and 1.2 million small recovery fits add work. this is an hours-to-days study, not an eta. if resources are insufficient, stop and report incomplete; do not silently substitute fixed-scale intervals or fewer draws.

use per-game sparse/local sufficient statistics, bounded working memory and trace contractions; no dense per-game global player Hessians or repeatedly scanning millions of rows for every scale candidate. ordinary native batch commands and external-only outputs suffice. the user accepts manual rerun risk; no drive investigation, vm, local fit mirror or infrastructure project.

completion means a verified, interpretable answer within this budget, including failure or inconclusiveness. explicit prices: full native shape retains variance/noise and permits negative complete rates; separate borrowing increases parameters; bootstrap adds substantial computation and remains conditional; exact-null protection restricts individual claims; unchanged selective coverage/context and age-neutral history limit generalization. none supplies admitted ability or a website handoff.
