# pr04n — complete recorded-rate adequacy

full specification, 2026-10-21; implementation and research execution require separate assignment. [the plan](../plan.md) owns progression. preserve [04m's frozen evidence](../research/attribution-04m/decision.md); this is a research report, not an ability handoff or website release.

## target and boundary

**does annual borrowing improve held-out complete regional unblocked-attempt rates, and where do volume, shape or their composition fail?**

| settled choice | consequence |
|---|---|
| corrected historical support; nine new fits | six scalar fits and three affected shape refits; three unaffected shape states reused after exact compatibility checks |
| retain 04m's 2025–26 partition, four prior seasons, forty-mode basis, covariates and annual borrowing | assesses the existing family; no new model-selection campaign or temporal replication |
| complete broad-regional paired loss is primary; volume, shape, interaction and native behavior remain visible | no absolute regional mse/rmse, latent-player recovery or calibrated player intervals |
| sign diagnostics replay held-out 2025–26 rows only | includes zero-event time; earlier negative-rate evidence remains historical, without a five-season sign audit |
| conditional diagnostic directions; no new gain/admission gate | adverse or unresolved results complete the assignment; no automatic successor or publishable estimator |

population: recorded, locatable unblocked attempts on matched reconstructed genuine-5v5 spatial support, including both team directions and zero-event exposure. this is joint lineup prediction of recorded results, not separate offensive/defensive ability, all-attempt opportunity value or a forecast available before the games. all seasons remain research-exposed. preserve the distinction between negative signed effects and physically negative complete rates.

non-goals: new features, priors, selectors, aging, chance weights, block-origin inference, acquisition, simulation campaigns, nested refits, player rankings/intervals, positive-link replacement, clipping, publication or frontend changes. richer deployment adjustment and uncertainty wait; the benefit is testing the assembled quantity before further component tuning. public [magnus 9](https://hockeyviz.com/txt/magnus9EV) motivates inspectable rate components; it supplies neither our acceptance criteria nor a private-model parity claim.

## inputs, correction and reuse

bind [04m's result](../research/attribution-04m/result.json), sha256 `3e17a6323c2ad67b40e65e2c9a5c4e290d896f640bbf95726b20dc558ff30b08`, and its named preparation, fit, assessment/probe, original row, basis and inventory references. reuse [04m's exact source/partition contract](04m-attribution-empirical.md#bound-inputs-and-partition): first-season `p,B`, `R=diag(p)B`, 656 native cells, 1,312 final inventory games, 1,051 training / 261 assessment, preceding seasons wholly training. freeze the same ids; never redraw. verify source hashes, axes, clean producer identities and train-only references. zero total retained assessment exposure stops explicitly; individual zero-time inventory games remain. a context absent from training fails only if it has positive assessment exposure.

execution additionally requires **02d's accepted final research-impact receipt**, consistent with the independent audit below: `kind:source_exposure_result,execution_status:complete,research_impact:verified,policy_id:strict_interior_other_strength_v1`. follow its hash-bound research-impact artifact; require the specified concordant exclusions and no recovery. an interim oracle or `candidate_status:ready` website candidate alone is insufficient. ordinary unavailable/changed inputs stop preparation; do not acquire replacements or expand the study. [02d](02d-source-exposure-consistency.md) owns the underlying source decision.

| frozen spatial-ledger exclusion | period / segment | interval, seconds | attacking teams |
|---|---|---|---|
| `2023020041` | 2 / 236 | `[1167,1200)` | 30, 8 |
| `2023020685` | 3 / 372 | `[939,992)` | 2, 52 |
| `2024020186` | 3 / 325 | `[657,703)` | 14, 52 |

these are six complete directed zero-count rows: 132 physical / 264 directed seconds, with no retained count loss or 2025–26 change. ledger segments are not native interval indices. match bound game, period, segment, endpoints, team, lineup, context and duration; independently verify zero retained spatial counts in the original rows. corroborating oracle: `/Users/nnandal/Documents/code/hockey-stats-local/source-02d-20261021/review/research-impact-oracle.json`, sha256 `cf5f1ab4f57d0c4d6232cc5dcce0a862894c0c8ed8ddd79f1296fc1dd726a3d8`. bind the accepted final receipt and these exact rows during preparation. a different correction requires a bounded spec amendment, not automatic extra fits.

subtract each excluded row's exposure/design contributions from its original raw grouped moments; preserve count moments and scalar response energy only after the zero-count check. recompute residualization, rate, exposure reference and likelihoods. store a finite correction receipt and corrected affected archives with new identities; never overwrite originals or regenerate the source corpus. no goal-boundary resegmentation or count prorating.

| component | borrowing chain | final independent |
|---|---|---|
| volume | five new chronological states, 2021–22 through 2025–26 | one new state |
| shape | reuse 2021–22/2022–23; refit 2023–24, 2024–25, 2025–26 | reuse 04m's exact state |

twelve selected states: nine new, three reused. prove reused annual likelihood arrays, ids, `u,r`, basis/reference and incoming-parent equality; retain their original identities within the new selection. this finite reuse costs explicit checks and avoids redundant fits; no generic cache or compatibility layer. source-only sensitivity compares corrected versus original final **borrowing shape** on unchanged assessment games. it measures the shape consequence of correction, not the uncomputed complete-rate effect of correcting volume.

## training and physical prediction

`e=seconds/3600` is directed exposure; `n` is the native count row; `X` has offense then defense player indicators; `Z` selects the existing context. for each training selection:

```text
A = sum(e X'X)                 C = sum(e Z'X)
E = sum(e Z)                   N = sum(Z'n)
K = sum(X'n)                   r = sum(N)/sum(E)
xbar = diag(1/E) C             nbar = diag(1/E) N
H = r (A − C' diag(1/E) C)      T = K − C' diag(1/E) N
scalar_score = T 1
scalar_energy = (sum(Q_t) − sum_s ((N_s 1)^2 / E_s)) / r
shape_score = (T − (T 1)p') B
```

read retained scalar `Q_t` through the owning archive decoder; 04m's shape-only loader intentionally omits it. missing energy is not zero. active players, positive contexts and normalized exposure `u` come from training games. keep `weighted_population`'s positive-weight contract; selected-game contraction owns partitioning. corrected zero-event rows change `A,C,E,H,T,r,u,xbar,nbar`, although `N,K,Q_t` are unchanged.

add `ScalarCoefficientLikelihood(season,player_ids,H,score,energy,u,r,source_identity)` and `ScalarCoefficientState` in the numerical owner. `fit_scalar_coefficients(likelihood, previous_or_none)` returns the state; its validator and bounded probe consume the same likelihood/parent contract. coefficients/score have shape `(2*n,1)`; full covariance has shape `(2*n,2*n)`. reuse `_ScaleProblem(..., p=None)`, annual alignment/prior construction, scale selection and coefficient updating; do not disguise volume as a one-mode shape or use all-attempt volume. retain `beta,uncentered_beta,V,centering_shift`, ids, current/entrant/carried flags, `u,r,a,q`, parents and complete scale/solve receipts; `V` is full centered covariance. derive each role’s shift from `u` and its uncentered coefficients; preserve the existing aggregate `centering_shift` meaning rather than treating it as either role’s shift.

preserve league-relative historical carry without rescaling by the old/new league rate. first/independent states select entry variance; later states retain that entry variance, add selected innovation to historical covariance, and preserve cross-player covariance and carried-only posterior updates. unchanged selector: `log10 variance −8..0 by 0.5`, one bounded refinement (`xatol=1e-4,maxiter=40`), endpoint flags. no population penalty, feature selection or optimizer sweep.

for each arm, form physical predictions from **uncentered** coefficients:

```text
m_v = r beta_raw                      f_v = nbar 1 − xbar m_v_current
M_h = r Theta_raw R'                  F_h = nbar − (nbar 1)p' − xbar M_h_current
M = m_v p' + M_h                      F = f_v p' + F_h
mu_i = Z_i F + X_i M = v_i p' + h_i
```

context-only has `M=0,F=nbar`. use the actual posterior for carried-only identities; wholly unseen identities receive zero raw prior means. centered unseen coefficients equal minus their own role's shift, not zero or the sum of shifts. verify raw/centered prediction equality, `h_i 1=0`, `mu_i 1=v_i`, and matching population/axes between components. context compensation uses training-current rows only. observed assessment volume never enters a prediction.

## assessment and rate diagnostics

retain 04m's twelve physical regions `W=shape_regions()`. primary contrast is borrowing minus independent; borrowing minus context and independent minus context are reference checks. for each game:

```text
G = [[diag(E), C], [C', A]]       S = stack(N,K)
L_a = stack(F_a,M_a)
D_ab = <(L_a−L_b)W, G((L_a+L_b)W)> − 2<S W,(L_a−L_b)W>
delta_ab = sum(D_ab) / (12 sum(directed_hours))
```

negative means lower error; units `(recorded unblocked attempts/60)^2`. use sparse grouped contractions. **complete loss uses raw `N,K`**: the existing shape-loss helper subtracts observed total times `p` and cannot be passed complete predictions unchanged. share one contraction kernel with explicit complete/shape response contracts; preserve 04m's values.

also score scalar volume, zero-sum shape, each region and native inverse-share error. with `y=n/e`, `t=y1`, `h=y−tp'`, `q=p'W`, regional paired numerators decompose into:

```text
D_complete = ||q||² D_volume + D_shape + D_interaction
D_interaction = 2 sum_i e_i [
  (v_a−t_i) <q,(h_a−h_i)W> − (v_b−t_i) <q,(h_b−h_i)W> ]
```

all three regional contribution terms divide by the same `12 × directed_hours`; standalone volume divides by directed hours. native inverse-share metric `diag(1/p)` has unit volume weight and zero interaction. independently verify both decompositions and `D_bi=D_bc−D_ic` per game, pooled and per draw. signed contributions are not percentages of blame. paired moments do not establish absolute regional mse/rmse.

reuse 04m's 2,000 draws each for games / seven-day / fourteen-day blocks, `PCG64(404130)`, shared draws across contrasts, components and source-only comparison. retain zero-time games, empty calendar blocks and unavailable zero-denominator draws; pool numerators/exposure, with linear 95% percentile intervals. all three valid intervals below zero → `supported_lower_loss`; all above → `supported_higher_loss`; otherwise `unresolved`. intervals condition on fitted models, selection, split and source population; no refitting, scheme selection, multiplicity control or new gain threshold. carry forward fixed month/support summaries as descriptive diagnostics, not subgroup accuracy claims.

stream the bound original final-season spatial ledger once, select held-out games, include zero-event rows and independently reconcile its `A,C,E,N,K` and exposure/counts to grouped assessment inputs. use bounded batches, not a dense row-by-cell archive. for the three primary arms and total / twelve-region / native complete predictions, record strict negative-entry counts, exposure-weighted negative-entry fraction, any-negative-row exposure fraction, negative mass, minimum and exact worst-row plus cell/region locator. probe variants use grouped rescoring, not additional native row campaigns. define:

- negative-entry fraction: `sum(e × number_negative) / (number_locations × sum(e))`;
- negative mass: `sum(e × sum(max(−prediction,0)))`, in predicted attempts; also divide by `training_r × assessment_directed_hours` for a common dimensionless reference;
- total prediction is one location; region/native counts use their own resolution. retain numerical tolerances separately from strict signs.

reuse or extract existing `negative_rate_summaries` once; preserve its historical negative-total-rate meaning and name any-negative-entry-row exposure separately. no clipping or zero-negative-cell pass gate. regional adequacy is primary; native limitations remain visible. signed effects may be negative; a negative complete prediction cannot be interpreted as an event intensity. report these facts even if paired loss improves.

## owners, interfaces and saved contract

| owner | responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | source validation, finite correction, selected training moments including scalar energy, exact reuse proof and held-out row reconciliation |
| `analysis/src/hockey_stats/attribution.py` | scalar coefficient likelihood/state/fit/validation/probe; existing shape and annual algebra remain authoritative |
| `analysis/src/hockey_stats/attribution_prediction.py` | physical component composition, explicit response-target loss contraction and rate-summary arithmetic |
| `analysis/src/hockey_stats/paired_evaluation.py` | existing shared paired ratio/calendar resampling; no study thresholds |
| `analysis/research/attribution_complete.py` | frozen policy, `prepare → fit → assess → report`, inventories and classifications |
| `analysis/research/attribution_complete_assessment.py`, `attribution_complete_report.py` | cohesive study assessment and saved-only rendering; no duplicate fitting/decoding |
| `fixtures/attribution/complete-rates.*`, fixture readme | compact synthetic counted histories and checked facts, reusing empirical-fixture construction |
| `docs/research/attribution-04n/` | decision, verification, small result/tables and one figure; expensive arrays stay external |

extract mature decoding/serialization from old study commands into the responsible package when reused; do not import another study's controller as a library. preserve frozen artifact readers and outputs; hard-cut any newly superseded duplicate mechanism, without an unrelated historical migration or framework.

```text
python analysis/research/attribution_complete.py prepare \
  --source-result docs/research/attribution-04m/result.json \
  --source-audit <accepted-02d-result.json> --output <new-dir>
python analysis/research/attribution_complete.py fit --prepared <prepared.json> --output <new-dir>
python analysis/research/attribution_complete.py assess --prepared <prepared.json> --fit <fit.json> --output <new-dir>
python analysis/research/attribution_complete.py report --assessment <assessment.json> --output <new-report-dir>
```

`--fixture <fixture.json>` replaces both source arguments. schema 1, `kind:attribution_complete_{protocol,prepared,fit,assessment,result}`, `purpose:research|fixture_exercise`, clean producer/dependency identities and existing `{path,sha256}` references. no path discovery, fallback, schema guessing or public api change.

- **protocol/prepared:** spec snapshot, accepted source correction/old and new identities, row locators, split, basis, training arrays, exact reused-state proofs, formulas, seed and finite inventory.
- **fit:** twelve named component/season/arm states, `new|reused`, exact likelihood/parent refs, complete covariance/raw and centered coefficients/references/scale diagnostics; write each new state before continuing.
- **assessment:** game loss numerators, float hours, normalizers/denominators, component closure, every interval scheme, fixed diagnostics, source-only comparison, rate summaries/locators, probe variants and costs.
- **result:** `execution_status:complete,numerical_status:verified|unresolved,study_status:diagnosed|numerically_unresolved,nomination:null,admission:not_admitted,handoff:null`; at most one next question or an explicit unresolved reason. fixture status is `fixture_verified|numerically_unresolved`, with no next question. missing required inputs/states cannot produce completion.

run sequentially under `/Volumes/Expansion/hockey-stats/runs/attribution-04n-<date>/`. preserve completed outputs; no runner, local mirror, automatic retry or checkpoint engine. missing-path/hash/i/o errors stop normally. record measured wall time, memory and bytes; 04m's six shape fits took 393 seconds, not a runtime promise for this study.

## numerical and implementation acceptance

nine new states receive existing bounded winner/two-nearest/coarse-bracket probes (`xatol=1e-6,maxiter=80`), conditional on incoming primary history. bind the three unchanged states' original probe receipts; reuse the final independent shape's saved alternative. require equation residuals ≤ `1e-8` and current-player physical movement ≤ `1e-4` of annual league rate. retain finite endpoint winners/inherited unresolved-scale flags as limitations; failed/nonfinite solves stop dependent work.

rescore all sixteen primary/probe combinations of the four final fitted components, recomputing context compensation with unchanged training moments and shared draws. separately bind the original 04m final borrowing shape and its saved probe; score all four corrected/original primary/probe shape combinations for source-only sensitivity. there are nine new probe receipts, three reused selected-state receipts and this additional frozen-control receipt. no further fitting or propagated probe histories. verify all three complete-regional aggregate directions and the source-only shape direction remain stable; otherwise numerical interpretation is unresolved. other diagnostic movements remain visible without extra vetoes. preserve primary results; never widen the search to obtain a preferred conclusion.

implement and adversarially review four non-overlapping boundaries:

1. **source/training:** accepted correction and zero counts; selected-moment subtraction versus independent tiny-row reconstruction; count preservation, changed exposure/residualization, first-two/final-independent reuse, unchanged held-out inputs. reject wrong locators/axes/parents, missing energy and unexpected corrections. held-out response/exposure perturbations cannot alter training references or fits.
2. **fitting/composition:** five tiny counted seasons with known zero-event exclusions, entrants, carried/unseen players and changing rates. independently solve scalar and shape posterior/prior/gauge equations; verify all twelve selected states, nine new fits, three reuses and source-only comparison. preserve affected 04m/shared-consumer outputs; no extra real control fits.
3. **assessment:** direct tiny-row residual squares equal grouped complete/shape/volume/interaction calculations, including nonzero regional interaction and zero native interaction. verify paired closure, float denominators, zero-time/calendar cases, conditional intervals, sixteen main/four source-only probe combinations and direct sign/mass oracles. reconcile the real held-out row stream and all required receipts after execution assignment.
4. **content/integration:** all four commands on the fixture; missing inputs fail visibly; saved-only report regeneration; independent source, numerical/statistical and rendered-content review. no website/browser checks belong to this research boundary.

temporary end-to-end checks follow red → green → refactor → green, then deletion with test-only dependencies/controllers. retain fixtures, checked expectations, assessment commands and verification receipts. no permanent harness is assigned; documentation work requires links/consistency only. software acceptance does not require a favorable scientific result.

## content contract

the content reviewer owns labels, hierarchy, units and unsupported-claim checks for every output:

| output | good content |
|---|---|
| `decision.md` | complete-rate question first; actual source correction, coverage and primary direction; volume/shape/interaction; negative-rate limits and source-only shape result; conditional uncertainty; one next question or unresolved |
| `comparison.csv` | `comparison,contrast,metric,region,component,loss_numerator,directed_hours,metric_normalizer,loss_denominator,estimate,scheme,lower,upper,undefined_draws,direction,reason`; `comparison` separates main/source-only |
| `game-scores.csv`, `diagnostics.csv` | bound game/date/partition, counts/time, paired contributions and fixed month/support/numerical summaries; unavailable values have reasons |
| `rate-diagnostics.csv` | arm/resolution, counts, all exposure and mass denominators, strict minima with row and cell/region locators; no inferred reliability label |
| one static figure | complete-regional contrasts, then borrowing−independent contributions: weighted volume `||q||² D_volume`, shape and interaction, all divided by `12 × hours`; consistent lower-is-better axis, zero lines, numeric companion and conditional interval caption |
| `verification.md`, `result.json` | identities/inventories, costs, independent checks, source/fit preservation, test deletion and limitations |

lead with complete recorded-rate evidence, not an attractive player map or a nominal pass. shape-only gains and native shortcomings remain legible beside the headline. useful prediction still does not resolve latent recovery, richer context, empirical player uncertainty or supported chance valuation; publication remains separate.
