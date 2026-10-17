# pr04i — observable regional penalty selection

status: **full specification; ready for handoff.** independent statistical, systems/source and content reviews cleared. docs only; [the plan](../plan.md) owns assignment. [04h](../research/attribution-04h/decision.md) is complete; its truth-informed reference exposed regional recovery at a prediction cost, not a deployable selector. this experiment changes only selection within its eleven-mode pooled family. [brief](../brief.md) · [architecture](../architecture.md)

## question and fixed boundary

can a penalty rule using observed training information improve final-season twelve-region recovery over the same pooled marginal-likelihood selector while retaining at least 99% of its spatial prediction gain?

confirmed by the user on 2026-10-17: eleven modes in both arms; saved annual summaries and one gaussian working-noise assumption, tested under both source laws; developmental improvement without a new absolute recovery gate; 99% prediction-gain retention; mandatory null/lateral/entrant/returner diagnostics without additional vetoes. even supported progress gives `nomination:null,admission:not_admitted,handoff:null`.

retain five-season constant player effects, separate annual contexts, final-season target/reference, columns `0..10` of the saved basis, the original eighteen-variance grid, full native physical truth and the complete identifiable player target. these are distinct: eleven fitted spatial modes, twelve scored regions, rank-60 player information. preserve entrants 32/33, retired nuisance identities, changed returner 8 and the inseparable 26/31 average with weight two. their individual difference remains unavailable.

no new responses, game-response reconstruction, annual/real fits, noise estimation, calibration-truth tuning, forty-mode arm, changed basis/prior, expanded grid, origin/chance work, player intervals, publication or website changes. no prediction-constrained selector, interpolation with control, post-result rescue or fallback to another rule. the prediction budget assesses the selected rule; it does not secretly modify it.

## evidence and bounded work

bind the committed [04h result](../research/attribution-04h/result.json), sha256 `c962c9d4c38c86150fceff15036c1f19bc5bfea897127b7fd08d4f929cdcdbb7`, and its explicit six control manifests. its prepared/protocol identities are `d20303ab13bc2d4282f4498756bcf48d83a2326f9adc4a8d49f2b23b274b5f85` / `a09a39d789274c0c4e3abb2814ce2ae67569c4da15839b2d54db74811c2f6fb1`. follow its bound 04g source, basis, original statistic references and final training/evaluation designs. verify purpose, identities, dimensions and ordered axes; filenames do not define populations. this is previously exposed research evidence.

| population / law | selected evidence | work |
|---|---|---|
| independent sparse/diffuse × gaussian/game pace | original outer ids `100..199`, five annual summaries each | 400 candidate selections and matched control replays |
| paired null × gaussian/game pace | same ids and chronology | 200 candidate selections and matched control replays; diagnostic only |

total: six cells, 600 statistic histories / 3,000 decoded annual likelihoods, 10,800 candidate grid evaluations, 600 selected candidate fits, 600 saved-control replays and twelve numerical probes. no predecessor annual fitted-state replay or 04h fixed-risk campaign. do not open calibration statistic/annual-state archives `0..99` or unselected chains, or use calibration truths/forty-mode controls in calculations. shared manifests and compressed archives contain unselected metadata/arrays; decoding them is not permission to use them.

the sources retain annual `H,T,xbar,ybar,u,p,r` and related summaries, not per-game responses or empirical clustered covariance. during `fit`, replay the unchanged eleven-mode selector against 04h's `objectives_11`, `selected_a_11`, `Theta_11`, `V_11`, `context_11` for all 600 records. during `assess`, rescore saved states against checked truth and reconcile matched recovery/prediction/coupling. no truth scoring enters fit and assessment never refits. preserve originals rather than duplicating controls into the new run.

## observable selector

reuse `pool_shape_likelihood`: identity-aligned pooled information `H*` and score `Q*`, final selection `S` (64 × 68), final annual `H5,T5`, fixed `p`, `B=B11`, `R=diag(p)B`, region operator `W` (656 × 12), and `r=40`. keep native shape residualization `T_h5=T5-T5.sum(axis=1,keepdims=True)*p`.

use `likelihood_spectrum(H5)` and its existing cutoff `tau=100*64*eps*lambda_max`, checked at factors `.1,1,10`; research rank must remain 60. construct `H5+` from the same positive eigenspace. with role-wise final exposure centering `P` and information projector `E`, retain **`J=P E`**, not `E P`. verify `J H5+ H5=J`, existing entity weights/null directions and final-versus-union alignment. no default pseudoinverse cutoff.

```text
variances = [0] + 10**[-8, -7.5, ..., 0]
D = R' W
U = J H5+ T_h5 W                         # noisy final-season native regional reference
K_a = (H* + I/a)^-1                      # a>0; use existing factors/solves
A_a = J S K_a Q* D
c_a = ||D||_F² trace(J S K_a S' J')
score(a) = r²/64 * (||A_a||_F² - 2 <A_a,U>_F + 2 c_a)
```

`a=0` is exact: `K=0,A=0,score=0`; no epsilon prior. select the smallest finite score, ties to smaller variance. keep signed terms; negative scores are valid. no clipping or extra penalty on selection. reuse fixed-design factors across records.

for each **fixed** candidate under the gaussian source covariance, `E[score(a)]=E[regional squared error(a)]-zero-map error`. the final-year reference targets physical native regions even when history changes or the basis omits detail. replacing it with pooled least squares or a basis-projected reference changes that target. the shared-noise correction uses `B' diag(p) W=D` and `J H5+ H5=J`.

the minimum score is not unbiased risk of the selected estimator; all scientific comparisons use its realized error against known truth afterward. under non-null game pace, the working covariance is generally misspecified. at exact null the shape covariance agrees with gaussian, so the fixed-candidate identity also holds; different higher moments can still change selection. neither law names, population labels, truths, activation, known-law moments, reference penalties nor assessment losses enter selection. inputs are explicit numeric arrays/operators; keep provenance outside that interface. the existing `PooledShapeLikelihood` carries source labels and is therefore not the new selector's argument.

background: [generalized risk estimation](https://arxiv.org/abs/0804.3010) and [projected risk estimation](https://arxiv.org/abs/1003.3985). the final-season/native-region covariance-penalty formula above is this study's derivation, requiring independent verification. neither reference establishes its validity under game pace or describes hockeyviz's private selector.

materialize the winning fit through the same fixed-grid solve, union centering and final context as the control: `Theta=P_union K_a Q*`, `maps=S Theta R'`, `context=ybar_h5-xbar5*maps`. returned covariance is numerical working covariance, not calibrated player uncertainty. verify that scoring centered maps agrees with `A_a`; never exchange projection/centering order silently.

## paired assessment and prospective criteria

score both arms on the same physical final truth, evaluation design and training context. shared prediction arithmetic retains signed context coupling. define per record:

```text
R = r²/64 * ||J (maps - M5_raw) W||_F²
P = full-lineup spatial prediction error, inverse-share weighted
P0 = error of the same no-player-shape training-context forecast
G = P0 - P
B = R_control - R_candidate
M = G_candidate - .99 G_control
```

primary benefit is `mean(B)>0`; prediction requires positive `mean(G_control)` and nonnegative retention margin `mean(M)`. show prediction cost `mean(P_candidate-P_control)` and allowance `.01*mean(G_control)` in their actual units. this is 1% of predictive **gain**, not total error. never form a noisy per-record gain ratio or substitute the weak annual predecessor as control.

for each cell resample the 100 complete outer records 10,000 times using `PCG64(SeedSequence([41001,population_id,law_id]))`, population ids sparse/diffuse/null=`0/1/2`, laws gaussian/game pace=`0/1`. reuse indices across arms/metrics; linear 2.5/97.5 percentiles. compute means before ratios/roots. whole records include their truth, response, noisy regional reference and data-selected fits: intervals describe mean experimental performance across that variation, conditional on the fixed designs/references and exposed truth population. no bootstrap refits are needed. these are neither individual-player intervals nor simultaneous bands or untouched confirmation.

in the **four non-null cells only**, classify each of `B,G_control,M`: `supported` if lower bound `>0`, `failed` if upper bound `<0`, otherwise `inconclusive` (including exact zero). a cell supports progress only when all three support it. overall `progress_status` is `supported` when all twelve non-null criteria support; `failed` if any of those twelve fails; otherwise `inconclusive`. null criterion/progress entries are `not_applicable` with reason `diagnostic_only`, while descriptive paired intervals remain. retain cell results and partial improvements. numerical uncertainty overrides overall status to `numerically_unresolved`. crossing zero proves neither equivalence nor acceptable prediction cost. no added records or relaxed margin after assessment.

report risk/zero risk and the old `.75*mean(R_zero)-mean(R)` as historical context, not gates. regional rms is `sqrt(mean(R)/12)` in redistributed recorded unblocked attempts/60 per player-role/region. use the same within-20-ft and lateral operators as 04h, with single-functional rms `sqrt(mean(R))`. null ratios are unavailable; show absolute false-map risk and paired changes.

mandatory adjacent diagnostics: both functionals, omitted physical detail, offense/attempts allowed, active/inactive rows, entrants and changed returner, selected variances/zero/upper endpoints, and selected score versus `R_candidate-R_zero` (its matching baseline), with post-selection optimism explicit. preserve full-target denominators and signed accounting; no per-partition tuning. diagnostics are not vetoes, but every deterioration qualifies the written conclusion. constant pooling can misrepresent changing players; broad regional improvement is not uniform map recovery.

## owners, composition and artifacts

| owner | bounded change |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | expose the existing annual-statistic decoder as `read_regularization_source_populations`; add strict selected 04h control reading; reuse identity/pooling/spectrum/region contracts |
| `analysis/src/hockey_stats/attribution.py` | factor fixed-index state construction out of `fit_pooled_shape`; preserve its marginal selector; add the explicit numeric regional selector using the existing grid/solve |
| `analysis/src/hockey_stats/attribution_prediction.py` | move reused realized map/context scoring here from 04h's study helper; use it in both studies with preserved results |
| `analysis/src/hockey_stats/attribution_simulation.py` | reuse physical truths/regions for assessment only; no response/noise generator changes |
| `analysis/research/attribution_selection.py` | six-cell rules, source binding, commands, criteria and compact reports; split a reporting file only if it absorbs substantial complexity |
| `docs/research/attribution-04i/` | eventual decision, comparison csv, diagnostic table, figure and verification |

`regional_penalty_scores(H5,T_h5,S,J,p,B,W,Q,grid,r)` returns eighteen scores and signed terms; `grid.H` is `H*`. it accepts no source/state object or truth. explicit flow: numeric scorer → deterministic argmin → `pooled_shape_at(pooled,grid,index)`, which constructs coefficients/covariance/context/diagnostics without a criterion. the existing marginal selector uses the same materializer and retains its meaningful `objectives`; do not invent a placeholder objective on the fixed-state return. archive scaled contributions `norm_term=r²||A||²/64`, `cross_term=-2r²<A,U>/64`, `correction_term=2r²c/64`, summing to `scores`. no generic criterion callback, study framework, compatibility adapter or duplicate posterior. named old research readers remain because they own still-consumed evidence, not as fallbacks.

extract only the named eleven-mode schema checks for control reading. do not call 04h's `_read_fits` wholesale: it also validates forty-mode controls and calibration-risk calculations outside this study.

```text
prepare --source-result <04h-result.json> --purpose research|fixture_exercise --output <new-directory>
fit --prepared <prepared.json> --population sparse|diffuse|null --law gaussian|game_pace --output <new-directory>
assess --prepared <prepared.json> --fits <six-explicit-fit.json-paths> --output <new-directory>
```

`prepare` binds the frozen spec, rules, six explicit controls and selected statistics; no fitting. `fit` selects candidate states and replays controls from training summaries; no truth-based selection. `assess` reconstructs checked physical truths and scores saved states, bootstraps and writes reports; no fitting, reselection or new response. unselected arrays and metadata may not influence a candidate.

use existing finite-json, exclusive-write and `{path,sha256}` / array-reference primitives. new `attribution_selection_{protocol,prepared,fit,assessment,result}` artifacts use schema version 5; no changes to historical artifact kinds. one compact array archive per cell, declared names/axes/dtypes and `outer_ids`; verify completeness before reporting.

- **prepared:** parent result/prepared/protocol/control/statistic references, source/executing producers, geometry/grid/rule digests, ordered cells/ids, purpose and budget. reference inherited inventories; do not copy 04h's large protocol or expensive outputs.
- **fit:** scores and each scaled signed term `(100,18)`; index/variance `(100,)`; candidate `Theta (100,68,11)`, `V (100,68,68)`, context `(100,6,656)`; replay maxima, rank/equation/probe receipts and costs. controls remain referenced. numeric arrays float64; indices/ids int64. expose endpoints without silently widening the grid.
- **assessment:** paired regional/functionals errors, prediction/coupling, zero risk, partitions, bootstrap summaries and classifications; source refs and reasons for unavailable values. primary regional error arrays `(100,64,12)` per arm; functional errors `(100,64,2)`.
- **result:** `execution_status:complete`, `numerical_status:verified|unresolved`, `progress_status:supported|failed|inconclusive|numerically_unresolved`, all cell criteria and report refs; `nomination:null,admission:not_admitted,handoff:null`. incomplete execution writes no completed result; failures retain evidence and cannot select another method automatically.

research uses a clean identified producer and verified external originals. write new outputs only under `/Volumes/Expansion/hockey-stats/runs/attribution-04i-<date>/`; ordinary i/o stops and manual reruns suffice. stream one history, reuse factors, report wall/process time, peak memory and bytes. no runner, checkpoint engine, local mirror or new dependency.

`fixture_exercise` binds an explicitly labeled compatible 04h fixture with all six cells and assessment id `{1}`. preserve its own geometry, rank and source identities, with identical native/basis/player dimensions and this rule/grid. six candidate fits, six control replays, 108 grid scores and one probe per cell; leading archive dimension is 1. fixture intervals cannot support research progress. synthetic verification inputs can exercise algebra; none replace research originals.

## content, delivery and acceptance

one concise decision, complete paired csv, diagnostic table and one figure. the content designer fixes labels/copy before implementation and reviews actual rendered output afterward. arm labels: `pooled history, regional-score selection, 11 spatial modes` and `pooled history, marginal-likelihood selection, 11 spatial modes`. the main table has one row per population/law: candidate/control rms, regional benefit interval, error/zero ratio, positive control gain and its interval, prediction cost/allowance/margin interval and criterion status. null uses absolute risks. the figure aligns recovery-benefit and retention-margin intervals with zero reference lines across all four non-null cells; label units and mean-experiment uncertainty. diagnostics sit beside the conclusion, including contrary results. selection scores are not player precision, prediction risk or post-selection unbiased error. no ability-card, rank or xg language.

non-overlapping delivery boundaries, independently reviewed after red → green → refactor → green:

1. **source/shared execution:** selected-statistic/control readers, fixed-index solve extraction and pure selector. verify reordered identities, separate contexts, entry/absence/return, final-reference alignment and no truth/law dependence. replay every saved eleven-mode control; extract only reused mechanisms, preserving historical behavior.
2. **mathematics/numerics:** independent tiny explicit-row covariance verifies every score term and the fixed-candidate gaussian risk-difference identity, including temporal changes, omitted native modes, nonuniform shares, inseparability and exact-null agreement between noise laws. verify exact zero, ties, endpoints, rank/cutoff sensitivity and centered/native agreement. changing assessment truths or law labels with identical numerical training inputs cannot change selection. no monte carlo campaign needed for this algebra.
3. **bounded research:** reconcile all six cells, 600 candidate/control pairs and 10,800 scores. every positive-variance solve satisfies `||AX-B||_F/max(1,||B||_F)<=1e-8`. independently enumerate the same grid by eigensolve at ids 100/199 in every cell: twelve probes of all scores, coefficients, covariance, contexts and physical predictions at `atol=1e-10,rtol=1e-8`. a changed winning index must agree in winning score and resulting predictions within those tolerances; otherwise numerical status is unresolved. no extra search.
4. **assessment/content:** independently rescore one full non-null/game-pace cell and one null cell, including native truth, paired intervals/margins, partitions and units. reconcile every plotted value to tables. bounded synthetic boundary checks verify all decision states and missing/duplicate/invalid artifacts; no new research responses. inspect source/data/report limits and preserved originals.

delete temporary integration/live checks, controllers, bytecode and test-only dependencies after verification; retain useful fixtures, independent expectations, scientific tools and receipts. no lasting suite is selected here; [07](07-lightweight-testing.md) owns that work. documentation preparation runs none of these campaigns.

completion is the reconciled comparison, including scientific failure or inconclusion. costs remain explicit: gaussian working noise can fail under game dependence; unregularized regional references can be noisy; constant history and eleven modes retain their biases; the strict 99% policy may be unresolved with 100 records; diagnostics may deteriorate despite primary progress. real-player recovery, complete-rate validity, calibrated uncertainty and supported chance valuation remain separate.
