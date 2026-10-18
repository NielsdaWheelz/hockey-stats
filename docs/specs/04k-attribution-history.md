# pr04k — annual borrowing on real deployment

status: **implementation and bounded research execution assigned**. the user approved the three choices below and assigned the entire specification on 2026-10-17. [the plan](../plan.md) owns progression; [04j](../research/attribution-04j/decision.md) supplies the completed information diagnosis. no model is admitted.

## question and boundary

does the existing annual borrowing rule recover known spatial effects better than a final-season-only fit on actual deployment, and what does it cost when effects change? evaluate generated effects on the admitted five-season design, not observed player ability.

| approved choice | consequence |
|---|---|
| retain existing league-relative carry | isolates the present rule; physically stable effects need not be constant in its normalized coordinates |
| diagnostic comparison; no new gate | show recovery, prediction cost and contrary cases; no winner, nomination, admission or player-uncertainty claim |
| gaussian plus game-shared gaussian sensitivity | selected saved design summaries suffice; omits count-dependent shot noise and is not the earlier gamma-poisson generator |

retain the existing forty-mode, age-neutral annual shape estimator and its marginal-likelihood selector. no new prior, representation, covariate, scale grid, empirical noise estimator, historical acquisition, recorded-response fit, volume model, bootstrap, chance valuation, website or publication change. real deployment does not make the simulated effects empirical. observed coverage and the season-level ability destination remain unchanged.

## inputs and finite inventory

verify only the selected source chain; preserve its bound paths and hashes. no newest-file selection, broad campaign reader or substitute source.

| input | binding / selected content |
|---|---|
| 04j | [result](../research/attribution-04j/result.json), sha256 `c59f54cdc9256e5dcb198b916f175d90a45b59944dbd2ef3c67abb524c397e3e`; its prepared manifest sha256 `94247ec3244c0fd35b886bfaae041cd01491af908752756a833805b970b7b91c` at `/Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/prepared/prepared.json` |
| real annual design | select that preparation's `sources.real_result`, then use `read_real_deployment_designs`; corrected 04b prepared sha256 `fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b` binds the five spatial populations and grouped archives |
| grouped design | each selected annual manifest supplies ordered game ids and binds `unblocked_spatial-<season>-grouped.npz`; decode sparse `H_e`, sparse `stratum_x`, `stratum_e` only; verify full archive hashes without decoding recorded response members |
| spatial basis | `/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/prepared/basis.npz`, sha256 `67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc`; semantic identity `649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51` |

select `20212022..20252026`, `unblocked_spatial`, all admitted zero-event exposure and matched spatial exclusions. current players are `1003,951,924,910,940`, union `1477`; directed row counts are `698940,881742,864050,857462,881612`. each season has 1,312 games and 42 contexts: attacking home/away × period 1–3 × clipped score −3..3. retain exact annual `r`, exposure weights `u`, ids, coverage and common positive 656-cell `p`. basis and annual `p` must be exactly equal. do not decode `T,yy,shape_yy,ybar,T_raw,stratum_n,Q_t,Q_h`, previous fitted player effects or old synthetic truths.

| cell id | noise law | physical transfer amplitude |
|---|---|---:|
| `gaussian_half` | working gaussian | 0.5 |
| `gaussian_base` | working gaussian | 1 |
| `gaussian_double` | working gaussian | 2 |
| `gaussian_null` | working gaussian | 0 |
| `game_shared_base` | working gaussian plus shared mean perturbation | 1 |

twenty noise records `0..19` per cell. each record fits five chronological borrowing states and one independent final-season state: **100 pairs, 500 generated annual scores, 600 selected states**. no unused independent earlier-season fits, factorial expansion or adaptive increase of repetitions. the same twenty gaussian histories are shared across cells; the 100 cell records are not mutually independent. the null cell costs 120 states and diagnoses false maps; a second null game-shared cell would be identical under this law.

## native truth and temporal meaning

generate one outcome-blind population, fixed across noise records and cells. truth is native physical redistribution, never generated in the fitted basis. with native centers `(x,y)` and reference `p`, form two hard partitions:

1. radial: sort cells by distance to `(89,0)`, then `x,y`.
2. lateral: sort by `y`, then `x`.

for each ordering, select the nonempty proper prefix whose cumulative `p` is closest to `0.5`; ties choose the shorter prefix. for prefix `A`, define `f = p*1_A/p(A) − p*1_notA/(1−p(A))`. thus `sum(f)=0` and `sum(abs(f))/2=1`: amplitude one transfers exactly one recorded unblocked attempt/60 between the two halves. these are broad reference-mass partitions, not the within-20-ft region or a smooth ground-truth hockey surface. retain their actual boundaries and forty-mode projection discrepancy; that discrepancy is not a regional error floor.

the pinned basis was read while specifying: masses are approximately `0.5003431395` and `0.4913300087`. implementation independently verifies them and `min(r) − 10*2*max(abs(f/p)) > 0` over both templates. this bounds the unperturbed native mean `r*p + X*F` above zero for every ten-skater lineup, including double amplitude. no clipping, attenuation, redrawing or favorable truth replacement. signed gaussian realizations remain permitted; this is not a count generator.

use `Generator(PCG64(SeedSequence(...)))`, namespace `404110`:

- for each role `0=offense,1=defense`, permute sorted union ids with seed `[404110,0,role]`; assign the repeating pattern `radial+,radial−,lateral+,lateral−` in that order.
- within final-current ids with any earlier admitted appearance, independently permute sorted ids with `[404110,3,role]`. let `k=floor(n/6)`: first `k` are injected reversal, next `k` injected onset, remaining players stable. history-only identities are stable. final-current players with no prior appearance retain their assigned field and the separate label `no_prior_observation`.
- raw physical field `F_y` is `a*sign*f` throughout stable histories; reversal changes its sign at the **start of the final season**; onset is zero before that season and `a*sign*f` throughout it. absent identities contribute no rows but keep their history. at amplitude zero all fields are zero; trajectory assignments are bookkeeping, not actual changes.

score final-current truth `P_5 F_5`, where `P_y=exposure_centering(u_y)`. raw physical persistence need not imply a constant exposure-relative field as the reference changes. injected onset/reversal likewise need not mean exact zero/negation after centering. actual corpus entry and return-after-absence are independent flags, not nhl debut or evidence of a real ability change. report exact cohort/template/sign counts and all 940 players in both roles; no minute cutoff or outcome-based selection.

## generated likelihood, without recorded responses

let `e=seconds/3600`, `z=X−xbar[stratum]`, `H=r*sum(e*z*z')`, `B` be the saved 656 × 40 basis, and `R=diag(p)B`; `p'B=0`, `B'diag(p)B=I`. `F_y` is the current-player raw physical truth, ordered offense then defense. generate the projected score directly:

```text
Q_y = (H_y/r_y) F_y B + S_y Z_y
S_y S_y' = H_y;  Z_y entries iid N(0,1)
```

factor each annual `H` once, using the existing spectrum/gauge contract. research must verify the 04j ranks `2004,1900,1846,1818,1878`, covariance reconstruction relative residual ≤ `1e-10`, and that discarded directions are only the two role-constant gauges; the fixture preserves its separately declared extra nulls. no jitter or new cutoff that removes weak information. seed `Z_y` with `[404110,1,record,year_index]`, with research year index `0..4` and fixed saved factor axes. independent and borrowing arms receive identical final `Q`.

for `game_shared_base`, also draw `xi_g ~ N(0,0.5)` independently by inventory game, using `[404110,2,record,year_index]`; `0.5` is the variance. use the same draw for both directions and every cell. with `A_g=sum_game e*X*X'` and `X_g=sum_game e*stratum_indicator*X'`, add:

```text
Q_game = sum_g xi_g (A_g − xbar' X_g) F_y B
```

this is the shape-score projection of a game-shared perturbation to the generated mean, alongside unchanged working gaussian noise. generating context shape is zero; retain **raw** `F_y` here, since centering it without context compensation changes the law. the reference `r*p` vanishes under `B`. no simulated context response is needed for the comparison below.

contract `xi @ H_e` and `xi @ stratum_x` in their flattened sparse form before reshaping/multiplying. never materialize one dense global matrix per game. reconcile grouped totals with annual `H,xbar,stratum_weight` first. do not use `weighted_population`: pace changes the response law, not exposure, `H`, `u`, `p`, `r` or fit weights. the stress omits mean-dependent shot noise, permits signed mean perturbations and is not calibrated to actual game variability.

## paired estimator contract

both arms use the unchanged `graph_40ft` shape likelihood and selector. the independent arm has no predecessor at its **actual final season**. borrowing has one state per admitted season, with identity-aligned union columns and zero current exposure for history-only players.

retain current prior semantics: first state has zero mean and selected variance `a`; later states embed the preceding centered mean/covariance unchanged in relative-rate units, add selected innovation variance `q` to previously seen identities, and give new identities zero mean with inherited entry variance `a`. keep absent players as correlated nuisance rows. do not multiply carry by `r_previous/r_current`. an entrant can be affected by inherited population shrinkage and teammate estimates despite having no personal past.

reuse the existing coarse log10 variance grid `−8..0` by `0.5`, one bounded refinement around the best interior grid point (`xatol=1e-4,maxiter=40`), finite-winner tie rule and full centered row covariance. no population constraint from 04g or pooled selector from 04i. the projected-score objective omits response energy, an additive constant independent of the selected scale; absent energy/full objective must remain absent, never fabricated as zero.

extract the coefficient-only update at its existing numerical owner. preserve posterior, centering, alignment and selector arithmetic for affected current callers. full-state callers retain their existing context calculation order and artifact shapes; no historical artifact rewrite or second implementation. this does not authorize generic compatibility adapters. new callers use the explicit new contract only.

## recovery and prediction

extract current rows and final exposure centering from each fitted state. let `M_arm=r_5*Theta_arm*R'`, `T=P_5 F_5`, and `W` be the existing 656 × 12 partition. for a declared set of player-role rows `C`:

```text
regional_mse_arm(C) = sum(((M_arm−T) W)[C]^2) / (12*len(C))
zero_mse(C)         = sum((T W)[C]^2) / (12*len(C))
recovery_benefit    = regional_mse_independent − regional_mse_borrowing
```

primary summaries are separate offense and attempts-allowed populations, each `n=940`; positive defensive values mean more attempts allowed. report `sqrt(mean(regional_mse))`, not mean per-record rms, and both arms versus the zero-player baseline. score full native truth; no projection of truth into the estimator's span. repeat the existing within-20-ft and lateral functionals as diagnostics with their actual physical targets, not the transfer amplitude substituted as their truth; each functional's mse divides summed squared errors by `len(C)`, without the regional factor twelve.

mandatory cohort summaries: injected stable/reversal/onset/no-prior groups; actual returners; minutes `[0,300),[300,600),[600,1000),[1000,infinity)`; and each template. use each group's own denominator, report counts, and state overlapping flags cannot be summed. retain per-player/region monte carlo mean error and squared error. for directional shrinkage, report the cohort mean of `mean_error_i dot t_i / norm(t_i)` for regional truth `t_i`, with exact zero targets omitted and counted; do not average signed fields and call cancellation absence of bias. null reporting uses absolute false-map error, not a zero-denominator ratio.

spatial prediction is known-mean error **in excess of the same fitted-context, zero-player predictor**, on the identical final deployment. define `total_hours=sum(stratum_weight)/r_5=sum(e)` using directed exposure, not half that physical elapsed time; `G=H_5/(r_5*total_hours)`. use current coefficients:

```text
prediction_excess_arm = r_5² trace(Theta_arm' G Theta_arm)
                      − 2*r_5 trace(Theta_arm' G F_5 B)
prediction_cost       = prediction_excess_borrowing − prediction_excess_independent
```

context error cancels exactly because each stratum's exposure-weighted residualized design sums to zero. this remains true with game-shared noise; both arms and the zero-player baseline use the same stratum means. verify against explicit-row calculations with arbitrary context noise in fixtures. no native context draws, response-energy fields or absolute prediction loss are needed. this is independent replication on fixed covariates, not new-lineup or future-season validation. retain negative excess and positive cost; no sign clipping or gain-retention ratio.

for each paired benefit/cost and arm mean, report mean, sample sd, monte carlo se `sd/sqrt(20)` and approximate 95% t interval with 19 degrees of freedom. rms intervals, if displayed, transform the mean-mse endpoints by `sqrt(max(0,endpoint))`; never calculate them from per-record rms. records, not players/games/regions, are the independent simulation units. all intervals condition on one fixed truth/deployment population and these laws; they are neither player intervals nor uncertainty over plausible populations. do not bootstrap or silently pool cells. twenty repetitions may leave comparisons imprecise; no outcome-dependent extension. this follows the requirement to expose finite-simulation error in [Morris, White and Crowther](https://arxiv.org/html/1712.03198v3).

there is **no pass/fail scientific gate, nominee or rescued historical verdict**. report direction and uncertainty without calling a crossing-zero interval equivalence. the old 25% recovery rule, 99% prediction-gain rule and 5% scalar contrast do not become criteria here. conclusions must name stable/change/null harms and this fixed mixture, not require borrowing to win under deliberately adverse persistence.

## owners and public capability

| owner | responsibility / new boundary |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | reuse `DeploymentDesign` and selected readers; add a narrow game-design reader and validation for `game_ids,H_e,stratum_x,stratum_e`; source/identity/accounting only |
| `analysis/src/hockey_stats/attribution.py` | one coefficient-only annual shape entry around existing prior, scale, posterior and centering mechanisms; shared state validation and bounded conditional probe arithmetic |
| `analysis/src/hockey_stats/attribution_simulation.py` | native transfer truth and exact projected-score generation; no study thresholds or source selection |
| `analysis/src/hockey_stats/attribution_prediction.py` | explicit-denominator regional errors and same-deployment prediction excess; reuse signed quadratic arithmetic, preserve the existing historical denominator where requested |
| `analysis/research/attribution_history.py` | frozen sources, cohort/cell/seed inventory, ordinary commands, assessment, decision and reports; separate presentation module only if needed |
| `docs/research/attribution-04k/` | compact result, decision, tables, figure and verification; expensive arrays external |
| `fixtures/attribution/history-comparison.{json,npz}` and `fixtures/attribution/README.md` | compact synthetic geometry, generated-score checks and independently checked expectations; reuse existing deployment/basis fixtures by reference |

numeric-only API: `fit_shape_coefficients(likelihood, previous=None)` consumes actual season, current ids, `H,Q,u,r`, basis identity and source identity. it returns all-seen/current ids, centered `Theta,V`, entry/innovation scales, centering shift, search receipt and diagnostics. fitting never receives truth, noise-law labels, assessment values or trajectory labels. predecessor state owns its season/ids/scales; missing predecessor is explicit, not fake season zero. align/embed current information once. retain the small uncentered mean/shift needed by existing context wrappers, not a dummy volume/context state.

`generate_shape_score(design, score_factor, physical_truth, basis, gaussian_draw, grouped_design=None, game_draw=None)` returns `Q` and generation diagnostics; game moments/draw must be supplied together. inputs are already validated numeric data, with no hidden source reads. `shape_recovery(...)` takes explicit selected rows/operator/denominator. `same_deployment_excess(H,r,total_hours,Theta,F,B)` owns the displayed formula. use float64, finite arrays, sorted identities and named axes. do not instantiate `RevisionPopulation` with invented response fields.

```text
prepare --deployment-result <04j-result.json> --purpose research --output <new-directory>
prepare --fixture <fixture.json> --purpose fixture_exercise --output <new-directory>
fit --prepared <prepared.json> --cell <id> --record <id> --output-root <fits-directory>
assess --prepared <prepared.json> --fits <fits-directory> --output <new-directory>
report --assessment <assessment.json> --output <new-directory>
```

`prepare` verifies selected originals, freezes truth/cohorts/operators and inventory, and saves five research score factors; no fitting. `fit` writes one pair exclusively at `<cell>/<record>/fit.json` relative to the supplied fits root, with six selected states and five scores for research. `assess` addresses every expected pair explicitly from the prepared inventory, never scanning for available substitutes; missing/invalid pairs prevent a completed assessment. `report` reads saved assessment only. the fixture's three years/four states/two records and interval degrees of freedom below override research counts throughout these shared commands. simple operator loops suffice; no scheduler, runner, checkpoint engine or automatic retry. ordinary i/o failure stops; completed expensive outputs remain intact.

artifacts use schema version 1 and `kind:attribution_history_{protocol,prepared,fit,assessment,result}`. all carry explicit purpose, clean producer identity, locked dependency identity and `{path,sha256}` references using existing artifact primitives. protocol binds spec choices, formulas, grid, seed algorithms, counts and probe policy. prepared binds selected source chain, ordered array axes, truth/cohort/reference digests, factors and expected pair paths. fit binds cell/record, five generated scores, six ordered states, exact parents, diagnostics and costs. selected-state arrays are `Theta,V` plus small centering data; reconstruct prior matrices from retained predecessor/scales, without storing candidate covariance grids, gain matrices or factorizations. assessment binds the complete inventory, metric rows, probes, omissions/reasons and resources. result binds reports with `execution_status:complete,numerical_status:verified|unresolved,study_status:diagnosed|numerically_unresolved,nomination:null,admission:not_admitted,handoff:null` and one `next_question` or explicit unresolved reason. fixture results instead use `study_status:fixture_verified|numerically_unresolved,next_question:null`. no completed result from partial execution.

research runs sequentially under `/Volumes/Expansion/hockey-stats/runs/attribution-04k-<date>/`. record first `gaussian_base/0` time, peak memory and bytes as a cost preflight; retain it as record zero, not an extra pilot. the fixed budget is at most 34,200 scale-objective evaluations plus selected posterior updates and probes below. six selected covariances per record total about **28.14 gb** across 100 records, plus **0.46 gb** of means and **0.30 gb** of scores, before shared factors/metadata; retain them externally for replay. no local mirror or special drive machinery. timing is measured, not promised; resource/i/o failure leaves an explicit incomplete inventory, not a downsized scientific result.

detached fixture contract: `kind:attribution_history_fixture,schema_version:1,purpose:fixture_exercise` binds the existing deployment fixture's `real_0..2` explicit rows only (both old design labels are synthetic). use its three season labels, contexts and durations, but replace final-season id `13` with new id `15`, including row membership; ids `11,12` return and `10,13,14` are history-only. twelve current players/year, union fifteen. this new fixture owns rates `50,60,70` and uniform `p`/forty-mode basis from `graph-40ft.json`; recompute design/game moments from rows, never relabel the old nonuniform statistics. preserve both source fixtures and honor their existing exact fixture contracts, including historical producer metadata. expected annual ranks are `18,20,20`; additional null directions are intentional, unlike research's two gauges. independently verify the pair `(1,2)` remains inseparable. use all five cells and two records: ten pairs, thirty scores, forty selected states and ten probes. generic interval aggregation uses its actual `N=2`, never research's `N=20`; every output is a fixture exercise. no fabricated research parent tree.

## numerical checks and delivery

reuse existing numerical residual tolerances, covariance/centering checks and clean-producer verification. preserve finite endpoint winners and inherited `scale_unresolved` flags as bounded-search limitations; the null cell may legitimately hit the lower bound. nonfinite/failed solves are different and cannot be silently dropped or redrawn.

perform twelve fixed conditional probes: record zero, all six `gaussian_base` states; final borrowing and independent states for `gaussian_double`, `gaussian_null`, `game_shared_base`. independently recompute the saved winner and two nearest coarse candidates, then tighten the saved interior bracket once **when one exists** (`xatol=1e-6,maxiter=80`). no new bracket/grid or repeated tuning; a missing bracket retains its bounded-search limitation. incoming priors stay fixed, so this is not a propagated-history or global-optimization bound. require equation residuals ≤ `1e-8` and maximum absolute change in physical native-cell/regional current-player maps ≤ `1e-4` of that season's `r`. for final probes also substitute the alternative into the saved paired record and report movement of recovery/prediction summaries beside their monte carlo se; no substantive interpretation may rest on an unresolved numerical movement. do not replace the primary fits with probe winners. a consequential failure yields `numerically_unresolved`, not another campaign.

non-overlapping delivery boundaries, each with independent adversarial review and temporary red → green → refactor → green integration verification:

1. **source and generation:** selected hashes/member allowlist, annual/group reconciliation, exact identities/rates/centering, frozen positive native truths, gaussian score covariance and shared-game contractions. independent tiny explicit rows must reproduce score means, covariance and prediction cancellation; prove recorded responses are not decoded.
2. **shared fitting:** refactor at numerical owners; preserve affected current consumers, actual-season independent fitting, entry/absence/return alignment, full covariance and original context arithmetic order. capture an existing affected entry point's valid synthetic fixture output before refactoring and reproduce it afterward; independently verify the coefficient objective and changing-rate carry. this does not reopen prior research fits or fabricate response fields. no obsolete duplicate update path remains.
3. **paired assessment:** the detached fixture exercises all five cells, both arms, null ratios, group denominators, missing pair, changed parent, nonfinite score, gauge invariance and the inseparable synthetic pair. a finite prior cannot turn that pair into data identification. fixture probes use its base four states plus the six final-state probes, ten total.
4. **bounded research and content:** after separate execution assignment, reconcile 100 pairs/500 scores/600 states and twelve probes, all expected metric/cohort rows, complete costs and unchanged originals. an independent reviewer recomputes per-record final metrics from retained fits/scores/truth and audits interval aggregation. render and inspect the report/figure. preserve fixtures, expected facts, scientific commands and receipts; delete temporary tests/controllers/test-only dependencies after verification. no lasting test harness is selected in 04k; [07](07-lightweight-testing.md) retains its separate policy.

## report and acceptance

the content designer fixes labels/layout before implementation and independently reviews rendered output. every surface says **simulated effects on observed deployment — not player ability estimates**. use physical units, matched axes, visible counts and limits; no real-player rankings, confidence-colored ability maps or success badges.

| report | required content |
|---|---|
| `design.csv`, `truth.csv` | annual source/coverage/rates/context/exposure; cohort/template/sign/entry/return assignments; raw and centered target magnitudes; exact partitions and representation discrepancy |
| `metrics.csv` | all record/arm/role/cohort/operator values, explicit denominators and units, null/empty reasons; no missing-as-zero |
| `comparison.csv`, `diagnostics.csv` | both-role regional rms for borrowing/independent/zero, paired mse benefit and intervals; five same-deployment prediction-excess comparisons; near/lateral, change/entry/return/minute/template harm and bounded-scale/numerical limits |
| `players.csv` | all final player-role ids, simulated targets, monte carlo mean errors/squared errors, history/overlap/minutes and cohort flags; a research audit table, not estimated real ability |
| `comparison.png` | columns offense recovery, attempts-allowed recovery, prediction cost; five labeled cells with zero reference and monte carlo intervals; base-law changed-player harm displayed adjacent, not hidden behind an aggregate |
| `decision.md`, `result.json`, `verification.md` | one diagnostic answer and next question or unresolved reason; exact inventory/provenance/costs, checks and limitations, no admission/handoff |

acceptance means the assigned comparison executes and reports honestly, including harm or imprecision. complete only when independent source, numerical, statistical and content reviews reconcile its declared inventory; unexpected omissions cannot be renamed scientific inconclusion. successful fixtures establish software behavior only.

material costs/limits: real-sized histories replace cheap toy fits; fixed truth and twenty repetitions constrain generality/precision; forty modes discard detail; relative carry approximates physical persistence; a mixed stable/change population has arbitrary proportions; the gaussian game stress is not a validated count/noise law; same-deployment prediction says nothing about unseen lineups. those limits are the design, not undisclosed exceptions. [magnus 9](https://hockeyviz.com/txt/magnus9EV) motivates inspecting historical borrowing and annual behavior, not copying private constants or claiming parity. age-informed borrowing, empirical noise, complete-rate adequacy, calibrated uncertainty and supported chance valuation remain separately specified work.
