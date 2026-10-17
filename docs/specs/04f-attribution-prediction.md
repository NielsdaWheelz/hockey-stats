# pr04f — explain attribution prediction failure

status: **assigned for implementation and bounded execution on 2026-10-16.** [the plan](../plan.md) owns assignment. preserve [04e's failed verdict](../research/attribution-04e/decision.md), criteria and artifacts. this diagnostic cannot nominate, admit or publish a model.

## target and boundary

explain why the candidate improves regional recovery over the control in some cells while both full predictors lose to the noisy training-context baseline. deliver exact accounting, one readable explanation and at most one proposed next question. an unresolved explanation is a valid completion.

recovery scored thirty player-pair differences across twelve regions; prediction scored whole lineups across 656 cells with inverse-reference-share weights. a common false effect can cancel in a pair difference but affect a lineup. fitted context also changes with estimated player maps. neither observation establishes the cause before accounting.

scope: saved year-five shape predictions, both original arms, sparse/diffuse/null populations and gaussian/game-pace laws. no new research data, responses, fits, scale searches, numerical probes, feature activation, reference/grid changes, real-player claims or retrospective success thresholds. complete-rate positivity, player intervals and chance valuation remain separate. [05a](05a-observed-website.md) remains independent.

## evidence and finite work

start from the committed [04e result](../research/attribution-04e/result.json), sha256 `b2b1b2225221bc3297556229ca6fb548c78494f7cc843ba90cb3e3f28e006c32`. require its original complete execution, verified numerics, `criteria_failed` and `not_admitted`. follow exact bound references, including inherited 04c basis/protocol/result parents. 04e outputs are rooted at `/Volumes/Expansion/hockey-stats/runs/attribution-04e-20261016/`; no latest-run discovery or replacement capture.

- six cells × 200 paired datasets: 1,200 records and 2,400 final fitted states. require every original record, including nulls and boundary-selected fits; no replacements or reduced denominators.
- validate the 12,000 annual states chronologically through existing strict readers, supplying validated source/statistics, preceding state and shared control volume. preceding years establish lineage only; compute no new historical risks. fixed selected-objective checks inside these readers are validation, not optimization.
- decode each statistic archive once per dataset; retain only the preceding states. existing reader rehashing is allowed; no new cache or validator. hash the bound original assessment without parsing its 290-mb historical diagnostic tree. seven fit manifests supply original final losses; the compact result supplies aggregate checks.
- reconstruct the EXACT frozen designs, physical truths and activation from existing 04e functions/seeds; verify saved digests. truth arrays were not saved separately. this reconstructs existing evidence, not a new random sample. do not regenerate responses.

the originals are mounted and available at specification. missing inputs stop execution; detached algebra checks do not substitute for research evidence. ordinary serial execution with one numerical thread suffices. record wall/cpu time, peak memory and consumed inventory. preserve all source files; no output mirror, runner, new dependency or recovery engine.

## mathematical contract

reuse native shares `p`, `D=diag(p)`, basis `B`, `R=D B`, region operator `W`, annual rate `r=40`, and original training reference. select current offense/defense rows by player identity before any design multiplication: final states include 34 all-seen players but only 32 current players. carried-only rows have no current truth. units are squared attempts per 60 team minutes.

let `M*` and `M` be true/fitted current shape maps; `A*` true context; `s_i` the evaluation stratum; `w_i` elapsed exposure. construct the source shape mean `ybar_h = ybar - rowsum(ybar)*p`. retain training `xbar`; never recenter under evaluation deployment.

```text
z_i = X_eval_i - xbar_train[s_i]
b_i = ybar_h[s_i] - A*[s_i] - xbar_train[s_i] M*
t = z M*;  v = z M;  h = v - t
<a,c> = r² / sum(w) * sum_i w_i * sum_j a_ij c_ij / p_j

noise = <b,b>;  signal = <t,t>;  error = <h,h>
coupling = 2<b,v>
P_zero = noise + signal - 2<b,t>
P_arm  = noise + error + 2<b,h>
delta  = P_arm - P_zero = error - signal + coupling
```

assert the saved context identity `A_hat = ybar_h - xbar_train M`. reproduce `P_zero/P_control/P_candidate` directly from original context/maps as well as this identity. these are errors against known mean responses, not new noisy observations. positive `delta` means worse prediction. label `signal` **known deployment-signal energy**, not achievable headroom. large common `noise` alone explains no paired difference; signed coupling is not causal blame.

### one joint partition

spatial row-map projections are `F_low=B[:,:11] R[:,:11]'`, `F_high=B[:,11:40] R[:,11:40]'`, and `F_omitted=I-1p'-F_low-F_high`. ranks on the zero-sum shape space are 11/29/615. use matrix contractions, not repeated dense 656-square projectors. verify zero-sum shapes, projection identities and orthogonality in `D^-1`; euclidean `B B'` is wrong.

construct `C:(30,64)` from the exact thirty disjoint scored pair differences, excluding the two inseparable `26−31` role contrasts. `C C'=2I`; set `J_test=.5 C'C`, `J_rest=I-J_test`. verify `C J_test=C` and `C J_rest=0`. the complement includes common effects, untested combinations and unsupported directions; it is NOT synonymous with unidentifiable effects. these projectors are euclidean-orthogonal, not deployment-orthogonal.

for each spatial band `k` and player partition `a∈{test,rest}`:

```text
v_ka = z J_a M F_k;  t_ka = z J_a M* F_k
h_ka = v_ka - t_ka;  b_k = b F_k
E_ka = <h_ka,h_ka>;  S_ka = <t_ka,t_ka>;  I_ka = 2<b_k,v_ka>
E_cross_k = 2<h_k_test,h_k_rest>
S_cross_k = 2<t_k_test,t_k_rest>
delta_k = sum_a(E_ka-S_ka+I_ka) + E_cross_k-S_cross_k
delta = sum_k delta_k
```

retain signed player cross terms. spatial cross terms vanish only under the checked metric. omitted fitted correction is zero: omitted error equals signal, coupling is zero, and its excess contribution must cancel. omitted context can still dominate absolute error. use the frozen training gauge; verify same-role reference-shift invariance and zero evaluated contribution from the known inseparable differences.

reproduce all original `R_zero/R_control/R_candidate` and active/inactive regional partitions with denominator thirty. add exactly one score bridge using the SAME pair contrasts but prediction's spatial metric:

```text
R_native_pair_arm = r²/30 * sum((C(M-M*))² / p)
R_native_pair_zero = r²/30 * sum((C M*)² / p)
```

this separates regional aggregation/weighting from additional lineup combinations. it is a diagnostic, not a preferred replacement loss or new recovery gate. do not expand to another score grid.

## summaries and uncertainty

design recommendation: paired aggregate intervals from saved datasets; no refits. use 10,000 resamples of 200 whole records, `PCG64(SeedSequence([40605,population_id,law_id]))`, original ordered populations/laws, and linear `.025/.975` quantiles. reuse indices across both arms and every component within a cell. the null cell extends this recipe; it had no historical criterion intervals.

summarize original risks, aggregate error/signal/coupling/delta, joint contributions and the score bridge. retain means and paired candidate-minus-control differences. resample records and form each complete signed contrast before quantiles; interval endpoints do not add. no ratios, percentage-of-blame charts, cross-cell significance comparisons or mechanism-selection thresholds.

these are post-study monte carlo intervals for mean behavior over truth/training-response draws, conditional on fixed deployments, references and synthetic families. they are not simultaneous bounds, calibrated player intervals, confirmation of a discovered cause or new hockey evidence. numerical reconciliation has tolerances, never statistical intervals.

## owners, api and composition

| file | responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution_prediction.py` | shared current-row selection, exposure-weighted deployment gram, signed inner/quadratic loss and excess-risk arithmetic |
| `analysis/research/attribution_pooling.py` | replace its three duplicated selection/gram/loss helpers with shared imports; preserve original arithmetic, truth/protocol policy and outputs |
| `analysis/research/attribution_prediction.py` | 04f source traversal, exact partitions, paired summaries, cli and report |
| existing `attribution.py`, `attribution_data.py`, `artifacts.py` | retain strict annual/statistic/source decoding, shape projection, identities and exclusive finite-json writing |
| `docs/research/attribution-04f/` | eventual compact protocol/result, decision, verification, tables and figure; create no fabricated evidence during specification |

shared function contracts:

```text
current_player_rows(state, players) -> ordered current offense/defense indices
deployment_gram(X, stratum_indices, exposure, n_strata) -> weighted Gram([Z,X])
prediction_inner(gram, left, right, *, p, rate) -> signed scalar
prediction_loss(gram, context, maps, *, p, rate) -> squared risk
excess_prediction_terms(gram, xbar, noise_context, true_maps, fitted_maps,
                        *, p, rate) -> {error, signal, coupling, delta}
```

`left/right` stack stratum context then current player maps; the gram divides by total exposure. `p=None` preserves the existing unweighted diagnostic path. loss delegates to the same bilinear arithmetic and preserves existing roundoff treatment; never clamp signed coupling/cross terms. excess arithmetic uses `noise_context=ybar_h-A*-xbar M*` and context-adjusted map corrections `[-xbar M; M]`. exact signatures may use existing typed states; no second implementation of these equations.

reuse 04e's `read_prepared`, `fit_inventory`, `physical_truths` and digest functions as frozen source-policy owners. do not call its top-level `assess`, which requires the original producer and reruns unrelated diagnostics. do not call its full `annual_losses` merely to reproduce six totals. no second annual decoder, fitter, schema migration or generic experiment framework; remove the replaced helper bodies, not supported inactive features.

one manual command, from `analysis/`:

```text
uv run python research/attribution_prediction.py assess \
  --source-result ../docs/research/attribution-04e/result.json \
  --output /Volumes/Expansion/hockey-stats/runs/attribution-04f-<date>
```

the command validates its source, freezes the exact spec snapshot/protocol before diagnosis, computes, and renders the report. research requires an identified clean producer. output is a new exclusive directory outside every input root. no prepare/fit/resume service or automatic source fallback. malformed evidence or arithmetic failure exits nonzero; partial files cannot carry complete status. a new diagnostic bug is repaired here; a demonstrated upstream defect stops interpretation, records the affected boundary and does not silently revise/refit 04e.

schema `4`, new kinds `attribution_prediction_protocol|attribution_prediction_assessment|attribution_prediction_result`, using existing artifact helpers:

| artifact | required payload |
|---|---|
| protocol | new producer and original producer; source-result/spec refs; scope/order, units, projections, bootstrap recipe, numerical tolerances and fixed verification inventory |
| assessment | 1,200 ordered `(population,law,outer,season)` paired records; original/reproduced six risks; score bridge; arm→band→player-partition `E,S,I,delta` and signed cross terms; aggregate terms, residuals, summaries and costs |
| result | protocol/assessment refs; source and new producer; exact counts; `execution_status:complete,reconciliation:verified,nomination:null,admission:not_admitted,handoff:null`; compact summaries, limitations and report refs |

each record binds original statistics, both final annual refs, truth/activation digests and exact arm names `graph_40ft|graph_two_band_80ft`. all refs use `{path,sha256}`; finite values and named arrays only. retain compact new diagnostics, not copied posterior histories or raw responses. preserve original input state tags unchanged. no completed result is written until reconciliation and report generation succeed.

## content and acceptance

the content designer owns `decision.md` (≤500 words), `accounting-table.md`, `partition-table.md` and `prediction-accounting.png`, all numbers derived from the assessment. tables cover all six cells and both arms: original/direct/reconstructed risks, error minus signal plus coupling, residuals, the low/high test/rest/cross partition, omitted cancellation and the score bridge. show nulls and inactive error adjacent to other results. use one figure with readable signed contributions, zero line, explicit units and direct totals; detailed reconciliation stays in tables. no decorative rink maps, component percentages, pass/fail colors or clipping inconvenient values.

the decision distinguishes exact accounting from inferred explanations. report the strongest relevant pattern, contrary evidence and limits. propose at most one next question with its discriminating comparison and cost, or say unresolved. a positive term is no proof that changing that component would help. proposing a narrower claim must name the capability delayed and evidence still needed. never rescue 04e's verdict or announce an automatic successor.

non-overlapping delivery boundaries; independent adversarial review before proceeding:

1. **evidence/shared-metric owner:** extract the three reused helpers, bind exact source inventory and traverse strict states. verify preserved 04e metric behavior and current/carried ordering. missing files, changed digests, wrong references, duplicate/incomplete ranges and mismatched arm/statistic/response lineage reject.
2. **diagnostic/statistical owner:** implement the equations and fixed partitions. independent direct-row arithmetic checks outer `0` and `199` in all six cells (24 final states), including all signed terms. verify all 1,200 six-risk records and existing compact means/active-inactive totals. use `abs(actual-expected) <= 1e-8*(1+abs(expected))`; excess-error checks use the small signed contrast as reference, not the large common absolute risk. exact ids/order/hashes remain exact. check projection identities and omitted cancellation at the same tolerance.
3. **study/content owner:** temporary red → green → refactor → green integration checks. detached deterministic algebra fixtures cover nonuniform shares, zero fitted correction, truth insertion, pair-common error, nonzero player cross terms, outside-basis truth and inseparable contrasts. no miniature fitting campaign. the assigned full read-only command supplies source-to-report integration; sentinel failures prove fitting, scale search and response generation are never called. independently reproduce bootstrap summaries for one non-null and one null cell. render/inspect the figure and review the decision against the tables.
4. **closure:** exact inventory, finite reconciled outputs, actual costs, independent source/numerical/statistical/content review and truthful conclusions. delete temporary tests/controllers/test-only dependencies after verification; retain useful fixtures, receipts and scientific assessment tools. no permanent suite is selected here. update plan/issues; preserve completed study evidence.

stop after the fixed accounting and report. no extra years, partitions, draws or fits because the explanation is unsatisfying. tradeoffs: lineage validation costs reading/fixed-state arithmetic but avoids a second decoder; paired intervals add modest work but only conditional synthetic evidence; the two simple partitions leave signed interactions rather than manufacturing clean blame; saved-state diagnosis can narrow a next experiment but cannot prove its remedy or establish real-hockey identification.

method context: [magnus 9](https://hockeyviz.com/txt/magnus9EV) makes linear-map components inspectable; it does not prescribe this diagnostic or reveal private equivalence. [ridge-regression notes](https://arxiv.org/abs/1509.09169) distinguish parameter estimation and prediction. the exact identities and budgets here follow this repository's frozen experiment.
