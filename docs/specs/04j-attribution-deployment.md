# pr04j — real-deployment attribution benchmark

status: full specification; implementation and execution require assignment in [the plan](../plan.md). [rationale](../research/model-direction.md#approved-real-deployment-direction--2026-10-17) · [council](../research/council.md#04j-specification-review--2026-10-17) · [recovery issue](../issues/attribution-spatial-recovery.md).

## target and boundary

determine which player contrasts actual five-season deployment distinguishes under the existing context and working-noise model; compare that information with the simulations and recommend one subsequent empirical benchmark. close the selector question from saved evidence. no new estimator is selected.

the user selected **deployment information only**, without estimating noise from games. outputs are conditional sampling standard deviations for unbiased linear contrasts under the declared reference model, not calibrated player uncertainty, observed ability or universal limits on estimation. retain the season-level ability destination, annual borrowing and historical verdicts. constant physical effects across five seasons are a diagnostic assumption only.

use matched `unblocked_spatial` populations, native zero-sum shape and unchanged unknown context means, residualized separately each season. keep source exclusions, zero-event exposure and identities. no scalar/complete-rate analysis, new masks, reconstruction, acquisition, responses, ability fits, selector/grid search, empirical covariance, bootstrap, chance valuation, admission, publication or website changes. frozen league-rate/spatial-reference summaries remain inputs; individual outcomes cannot choose contrasts. no eleven-/forty-mode comparison.

## frozen evidence and work

| evidence | binding and selected content |
|---|---|
| corrected real design | [04b result](../research/attribution-04b/result.json), sha256 `d0c0f6a7af3888cd0d0920d152f322447a984cbc20edac596aa70f60dbb0f2de`; its `/Volumes/Expansion/hockey-stats/runs/attribution-04b-20261015/prepared/prepared.json`, sha256 `fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b`, binds corrected 04a |
| synthetic design | [04h result](../research/attribution-04h/result.json), sha256 `c962c9d4c38c86150fceff15036c1f19bc5bfea897127b7fd08d4f929cdcdbb7`; its explicit 04g source binds `/Volumes/Expansion/hockey-stats/runs/attribution-04e-20261016/prepared.json`, sha256 `986ddf180bce3606a264595afbf1d8635ef9f9ae21c4af8f186daea69c35eb1f`, and the original designs/basis archives |
| selector closure | bound 04h comparison and [04i result](../research/attribution-04i/result.json), sha256 `c32ac2c9b03584c0435e9be2a23d621ec80b1bb15ef748f64e1b4146584dfd19`; its comparison/diagnostic reports only |

follow exact child references/hashes; exclude invalid original 04a output, fitted/refit chains and synthetic responses/truths. verify only the selected chain: no directory scan, newest-file selection, unrelated fitted-control validation or fallback. missing originals stop execution; fixtures cannot replace them. preserve bound references across canonical path resolution.

select `20212022..20252026`. real annual players: `1003,951,924,910,940`, union `1477`; directed rows: `698940,881742,864050,857462,881612`. each has 42 contexts: attacking home/away × period 1–3 × clipped score differential −3..3. synthetic **training deployment** has 32 current players, 96 games, 9,600 directed rows and six contexts per season, union 34. its one design is shared across populations/noise laws; 600 repeated responses are not independent deployment evidence. the context difference prevents interpreting this as a pure teammate-mixing comparison.

real selected arrays: `H,xbar,stratum_weight` from annual statistics; `u,player_exposure,p` from references; players, strata, `r`, masks/coverage and row counts from manifests. do not decode `T,yy,shape_yy,ybar` or game responses. synthetic: `train_{0..4}_{offense,defense,seconds,si,u,player_exposure,row_game_ids}`, `centers,W`, and basis `p`; no evaluation arrays. verify full archive hashes while decoding only selected members. retain the recorded full-design identity and compute a distinct selected-training digest; do not claim to recompute the old training-plus-evaluation digest.

require exact equality of all annual real and synthetic `p` arrays to the frozen first-real-season reference. producer ancestry is insufficient; no substitution if equality fails. small preparation manifests were inspected while specifying; bulk arrays remain to verify.

budget: ten annual spectra plus two final-target historical spectra; apply three cutoff masks to each, not three decompositions. real player/reference contrasts: 9,456 annual plus 1,880 historical; synthetic: 320 annual plus 64 historical. with twelve real/eight synthetic case labels below, total 11,740 labeled contrast rows. preparation records distinct calculation count and absent cases separately. batch contrasts against each spectrum, never refactor per player or region. research needs the external originals.

## exposure, history and targets

recover raw overlap from saved residualized statistics:

```text
G_raw = (H + xbar' diag(stratum_weight) xbar) / r
together_seconds(i,j) = 3600 * G_raw[off_i,off_j]
i_without_j = player_exposure[i] - together_seconds(i,j)
opponent_seconds(i,j) = 3600 * G_raw[off_i,def_j]
```

the producer admits both attacking directions for each retained interval. source durations are integral seconds in both designs. require reconstructed overlap seconds within `1e-6` of nearest integers; use checked integers for overlap accounting/ranking/ties, preserving `H` and the reconstruction residual receipt. check equal same-role blocks, symmetric opponent block with zero diagonal, and `3600*diag(G_raw)` against saved exposure in both roles. do not halve pair minutes. `sum(player_exposure)=5*directed_team_seconds`; physical elapsed time is half that directed total. preserve coverage; player presence does not establish complete-season time.

for every current player/year retain exposure, observed seasons, first-observed/return-after-absence flags and strongest same-team partner: exclude self, maximize shared time, break ties by ascending id. “first observed” means this corpus, not nhl debut; absence is not retirement. retain history-only identities as nuisance columns. no low-minute cutoff.

annual contrasts compare each player with that year's exposure-weighted reference, separately for `offense` and `defense` (display **attempts allowed**). final annual/history comparisons use **identical final-current players and final exposure weights**, not the union average.

final cases, both roles and both assumptions:

- real `(8476460,8478398)` and `(8480336,8480800)`, first id minus second: historical scalar-selected shared/no-shared cases; recompute spatial overlap, without calling them spatial extrema.
- real pair with greatest final spatial same-team shared time; sorted ids, lexicographic tie break. freeze during preparation. preserve duplicate selection labels without duplicate calculation.
- synthetic `(26,31)` difference and equally weighted mean relative to the final exposure reference. the mean cannot make either inseparable individual available or enter individual-player distributions.

absent case members give `not_in_target_population`, never replacements. overlap is descriptive, not the estimability test.

## information and units

let `e=seconds/3600`, `z=x−xbar[stratum]`, `p` be the common 656-cell reference and `C=diag(p)−pp'`. under the existing independent-row working model, normalized counts have covariance `diag(p)/(e*r)`. removing their total in proportions `p`, then multiplying by `r`, gives physical shape covariance `r*C/e`. hence:

```text
H_y = r_y Σ e_i z_i z_i'
L_y = H_y / r_y²                         # physical shape information
L_history = Σ S_y' L_y S_y               # S_y selects current identities from union
P_y = exposure_centering(u_y)
d_annual = P_y' c
d_history = S_5' P_5' c                  # final target, not union reference
```

`c` is a player unit vector, same-role difference or declared pair average. `S_y` preserves both role blocks/order. annual context means remain separate unknown nuisance parameters. constant history assumes the same **physical** player effect; summing `H_y` and scaling by final `r` changes that meaning. `pool_shape_likelihood` requires equal rates and is not this operation. real rates vary around 41–42; synthetic `r=40`. keep their exact values and shared `p`, without another standardized-noise arm.

reuse `likelihood_spectrum` and `centered_estimability` semantics: `tau=100*dimension*eps*lambda_max`; positive eigenvalues at `.1,1,10*tau`; relative null projection tolerance `1e-8`. compute `||d−V+(V+'d)||/||d||` directly, never by subtracting squared norms near the threshold; preserve the zero-vector convention. a materially negative eigenvalue fails. rank or status disagreement across cutoffs gives `numerically_unresolved`, never a tuned cutoff. real rank is measured, not assumed to be dimension minus two. role-constant gauges are null directions, not prior observations.

only for an estimable contrast:

```text
q = d' L+ d
regional_covariance = q W' C W
regional_rms_sd = sqrt(q trace(W' C W) / 12)
functional_sd(v) = sqrt(q v' C v)
```

`W` is the existing 656 × 12 partition from `shape_regions()`. reuse within-20-ft/in-front-of-goal and lateral operators: lateral region weights `+0.5` on positive y, `−0.5` on negative y, with original center-line half allocation. units: **redistributed recorded unblocked attempts/60**. retain covariance; adding marginal variances gives wrong functional precision. total-shape variance is zero by construction, not known volume.

annual eigensystems may be rescaled from `H`: `lambda_L=lambda_H/r²`, `tau_L=tau_H/r²`, unchanged eigenvectors/masks and `q=r²*q_H`. never pass an unscaled `H` spectrum with `L`. record `geometry_inverse=q/r` as an annual geometry factor independent of the rate multiplier; no analogous pooled rescaling. projecting an unavailable contrast into an estimable space changes its meaning and is forbidden. statuses are `available|not_estimable|numerically_unresolved|zero_functional|not_in_target_population`; unavailable `q`/sd stays null with reason. the row-space condition follows [standard estimability theory](https://support.sas.com/documentation/cdl/en/statug/65328/HTML/default/statug_introglmest_sect002.htm); independently verify the physical transformation.

## selector closure and content

extract only the inspected eleven-mode settings from 04h: sparse `3.1622776601683795e-05`, diffuse `0.0001`, each law. select `condition=broad,target=twelve_region_vector,spatial_modes=11`, `record_type=fixed_curve` versus `record_type=comparison,arm=adaptive`; metrics `risk,rms,prediction_excess`. show expected fixed-setting versus realized adaptive values; prediction excess must not be mixed with absolute prediction error. add all six 04i cells' `diagnostic_selected_score` rows for `score,realized_error_minus_zero,post_selection_optimism`, plus null `record_type=diagnostic_target,partition=all,target=twelve_region_vector` rows for `candidate_risk,control_risk`, both laws. these are 46 saved summary rows. retain reported intervals; do not invent paired intervals between calculations, optimize another grid or call truth-inspected settings deployable winners.

the content designer fixes labels/layout before implementation and reviews rendered output. outputs:

| artifact | required content |
|---|---|
| `designs.csv` | ten annual/two historical designs; source ids, contexts, current/union players, exposure, rate/reference, entries/returns, rank/nullity, cutoff results and costs |
| `contrasts.csv` | all selected player/cases, season/assumption/role, reference/coefficients, minutes/history/partner overlap, status/reason/null projection, `q`, annual geometry factor, twelve regional sds, two functional sds and regional rms sd |
| `summary.csv` | final population overall and minutes `[0,300),[300,600),[600,1000),[1000,infinity)`, by role/design/assumption; counts/unavailable reasons; available-only median/10th/90th percentiles using linear quantiles; historical/annual sd ratios on matched available contrasts and newly estimable counts |
| `selector-closure.csv` | source-row selectors, saved means/intervals/units and expected-versus-realized labels |
| `information.npz` | ordered spectra, cutoff/null diagnostics, common `p,W,C`/functional covariance and contrast axes/values; store finite available values with explicit row indices, not object arrays or missing-as-zero sentinels; no source-array/eigenvector copies required |
| `decision.md`, figure, `verification.md` | checks/costs, limits and one next-benchmark proposal or explicit unresolved diagnosis |

one four-panel exposure-versus-within-20-ft-sd figure: columns offense/attempts allowed; rows final annual/constant history. real points and distinct synthetic markers, shared axes, unavailable counts, exact rate/reference labels and **42 real / 6 synthetic contexts**. no ability ranks, confidence intervals, favorable-result line or estimated effects. summaries retain all-player denominators; finite-sd distributions condition on availability. store covariance once and `q` per contrast rather than duplicate 12 × 12 matrices.

the decision answers which contrasts are unavailable, where working precision is weak, how persistence changes it, and how synthetic design differs. no new absolute accuracy/progress gate. the subsequent benchmark proposal must name actual design/coverage; contrast/exposure/overlap groups; proposed broad physical magnitudes justified independently of desired success; stable/entry/change scenarios; noise assumptions; and one estimator question. these are next-specification proposals, not assignment. design alone cannot reveal actual effects or choose the required accuracy.

## owners, interfaces and execution

| owner | bounded responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | selected design readers; existing centering/spectrum/estimability; batched contrast arithmetic and identity-aligned physical information |
| `analysis/src/hockey_stats/attribution_simulation.py` | existing regions; centralize near/lateral construction from `analysis/research/attribution_resolution.py` and `attribution_selection.py`, updating both consumers with preserved behavior |
| `analysis/research/attribution_deployment.py` | frozen sources/selections, commands and reports; separate report module only if presentation complexity warrants it |
| `docs/research/attribution-04j/` | compact reports, figure, result and verification; larger arrays remain external |
| `fixtures/attribution/deployment-information.{json,npz}` and `fixtures/attribution/README.md` | compact synthetic design, independently checked expectations and provenance; no old-campaign fixture tree |

the reader returns `DeploymentDesign(season,player_ids,strata,H,xbar,stratum_weight,player_exposure,u,p,r,source_refs)`, float64 arrays, ordered ids/axes. real shapes: `(2n,2n),(42,2n),(42,),(n,),(n,),(656,)`; synthetic contexts number six. reuse selected decoding primitives; do not call `load_revision_population` or broad 04h/04g readers that load responses/unrelated controls. no generic source adapter or historical migration.

pure contracts: `physical_history_information(designs)` returns union ids, `S_y` and `L_history`; `contrast_information(L,D,spectrum)` accepts columns of **already centered/aligned** contrasts and returns cutoff statuses/null residuals/`q`. one arithmetic owner serves batched and existing scalar semantics; preserve the scalar interface/results for current consumers. no fit machinery or selector framework.

```text
prepare --real-result <04b-result.json> --synthetic-result <04h-result.json>
        --selection-result <04i-result.json> --purpose research --output <new-directory>
prepare --fixture-designs <fixture.json> --purpose fixture_exercise --output <new-directory>
analyze --prepared <prepared.json> --output <new-directory>
report --analysis <analysis.json> --output <new-directory>
```

`prepare` verifies selected sources, identity/coverage/exposure and freezes cases; no eigensolves or response scoring. `analyze` follows the prepared inventory: twelve research or eight fixture spectra, contrasts and applicable probes. `report` summarizes saved analysis/closure and renders content; no numerical rerun or source reselection.

new `attribution_deployment_{protocol,prepared,analysis,result}` artifacts use schema version 1, explicit purpose/producer/source identities and existing finite-json, exclusive-write, `{path,sha256}` and array-reference primitives. protocol binds spec/rules/operators/cutoffs; prepared binds sources, inventory, axes/cases/references/budget; analysis binds all contrasts/spectra/probes/costs and extracted selector-closure rows/labels. result records report refs, `execution_status:complete`, `numerical_status:verified|unresolved` and `nomination:null,admission:not_admitted,handoff:null`. research additionally requires `study_status:diagnosed|numerically_unresolved` and a structured next-benchmark proposal or unresolved reason. incomplete execution writes no completed result. structural nonestimability is valid, not a software failure.

research uses a clean producer, existing locked dependencies and `/Volumes/Expansion/hockey-stats/runs/attribution-04j-<date>/`. process annual matrices sequentially, accumulating one union matrix. record wall/process time, peak memory and bytes. ordinary i/o/manual rerun suffices; no runner, checkpoints, fit mirror or release machinery. preserve originals/fits.

fixture input is mutually exclusive with research parents. `fixture.json` has `kind:attribution_deployment_fixture,schema_version:1,purpose:fixture_exercise`, three ordered seasons, two named design lists (`real`,`synthetic`), explicit case coefficients and independently checked expected inventory. both designs are synthetic and every report says so. each annual entry supplies `DeploymentDesign` metadata and bound array references plus explicit rows for verification. use twelve current players/year, identity entry/absence/return and union fourteen in each design: eight spectra, 144 annual and 48 historical player contrasts across both designs, plus declared cases. retain 656-cell geometry/nonuniform `p`; own contexts/rates/cases replace research constants. no upstream campaign-tree fixtures or closure substitutes: closure is `not_applicable,fixture_exercise`. shared numerical/reporting owners run locally; fixture result is `study_status:fixture_verified|numerically_unresolved,next_benchmark:null`, never `diagnosed`, with the same execution/numerical/report-reference fields.

## delivery and acceptance

independent adversarial review at each non-overlapping boundary, with temporary red → green → refactor → green integration checks:

1. **source/accounting:** reconcile selected hashes, ten annual populations, ids/masks, common `p`, current/union counts and exposure identities. independently reconstruct five synthetic `H`/context summaries from saved training rows. fixtures exercise wrong sources/axes, missing inputs, duplicate ids, asymmetric pairing and absent cases. no unselected-response decoding or silent rebuilding.
2. **mathematics:** tiny explicit-row three-season fixture with unequal rates/exposures, nonuniform `p`, separate contexts, entry/absence/return, duplicate players and role gauges. independently compare pooling, centering, covariance and nonestimability with direct generalized least squares on the two physical functionals (`atol=1e-10,rtol=1e-8`). verify batched/scalar agreement, zero functionals and cutoff-sensitive cases. rate changes must not change persistence meaning.
3. **research/numerics:** reconcile twelve spectra, declared counts and cases. require `||LV−VΛ||F/max(1,||L||F)<=1e-10`, and for unit-norm role gauges `g`, `||Lg||₂/max(1,||L||F)<=1e-10`; available-contrast solve residual `||Lx−d||₂/max(1,||d||₂)<=1e-8`. independent reduced-known-gauge svd with **the same absolute cutoffs** for final real annual/history matrices: highest-/lowest-exposure player/reference and maximum-overlap pair, both roles, twelve probes; exposure ties use ascending id. statuses agree, null projections at absolute `1e-8`, available `q` at `atol=1e-10,rtol=1e-6`. annual availability must survive constant history and `q_history−q_annual<=1e-10+1e-6*abs(q_annual)`. disagreement is unresolved; no jitter, priors or adjusted thresholds.
4. **content/result:** independently reproduce group denominators/quantiles, closure rows, covariance-to-sd units and plotted values; inspect rendered figure. distinguish nonestimability, numerical uncertainty, weak conditional precision and unsupported real-noise claims. completion requires the diagnosis and proposal or justified unresolved conclusion, not favorable precision.

delete temporary tests/controllers, bytecode and unused test-only dependencies after verification; retain fixtures, independent expectations, scientific tools and receipts. no permanent suite is assigned; [07](07-lightweight-testing.md) owns selected retained checks. concrete unresolved issues belong in `docs/issues/`; do not invent another campaign.

tradeoffs: all-player tables retain awkward cases at modest matrix/reporting cost; native shape avoids assuming eleven-mode truth but cannot demonstrate smooth-model performance. unchanged contexts/reference noise bound the work while leaving omitted context/game dependence unresolved. constant history can supply precision through a false persistence assumption. recovery, complete rates, calibrated uncertainty and supported chance valuation remain separate requirements; the observed website is unaffected.
