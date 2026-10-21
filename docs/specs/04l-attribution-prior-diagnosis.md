# pr04l — account for annual-prior gains and harm

status: **specified; saved-fit scope confirmed 2026-10-19**. the user selected diagnosis only, without an entry-prior intervention. [the plan](../plan.md) owns assignment. the user assigned full implementation, bounded saved-fit execution and verification on 2026-10-20. any successor experiment remains unassigned.

## question and scope

which realized terms account for 04k's stable-player gains and reversal, first-observation and null harm: changed weighting of current evidence, or retained historical means? distinguish exposure-reference changes from historical transmission onto players with no personal past.

04k already established those subgroup differences. repeating them is insufficient; the deliverable is an exact, independently checked account that can motivate **at most one** subsequent prior hypothesis, or explicitly leave the remedy unresolved. keep its forty-mode estimator, full native truth, populations, scales, relative-rate carry and scientific verdict frozen.

| choice | consequence |
|---|---|
| diagnose saved final fits; no new research fits | exact realized accounting, without a candidate's performance or an independently identified cause |
| condition on selected covariances and scales | response-dependent selection remains inside the terms; this is not a classical bias–variance decomposition |
| retain all five cells and twenty paired records | preserves stable/change/null counterevidence; still only one fixed truth population and twenty shared histories |
| no new scientific gate | a completed diagnosis may remain unresolved; no nomination, admission, player intervals or publication |

out of scope: changing entry variance or historical means, local parameter-sensitivity experiments, reselecting scales, generating research responses, historical replay, empirical noise estimation, aging/context/feature changes, chance valuation, volume/complete-rate fitting, new data and website changes. the observed website and full season-level ability destination remain unchanged. a diagnostic conditional on frozen selections cannot establish that resetting inherited entry variance would help.

## inputs and bounded work

for research, pin [04k's result](../research/attribution-04k/result.json), sha256 `88404a3f624f741e316f251f9fa0b928f6850c2460044f66e2ae3322a32d95fa`. require its `complete,verified,diagnosed` status. follow its named references only:

| source | sha256 / selection |
|---|---|
| prepared | `9878ef0d199997976327ad5c9ec1e615a956b4bc84458431cc0c85fc57e943cd`; `/Volumes/Expansion/hockey-stats/runs/attribution-04k-20261017/prepared/prepared.json` |
| protocol | `6f72e59b9d8d8e1899b7e1632f09d7c3795e8365b97baffe4070fd2dd6cff5d9`; selected by the result/preparation |
| assessment | `1275fc420b2eb80dfa936a8f2e95ce3329724598aab5fb6a3f98fa2cb619e96e`; its `consumed.fit_*` references bind all 100 pairs |
| geometry | prepared archive; decode `B,p,eigenvalues,W,near,lateral` and final-year `H,u,p,truth,centered_truth,stratum_weight,player_exposure` only |
| paired fits | five cells `gaussian_half,gaussian_base,gaussian_double,gaussian_null,game_shared_base`, records `0..19`; final borrowing and independent states, immediate predecessor's `Theta`, and final `Q` |

resolve final/previous indices from the declared chronology, not filenames alone: research borrowing/previous/independent indices are `4/3/5`; existing fixture indices are `2/1/3`. read each selected final state's `Theta,V,uncentered_Theta,centering_shift,u`; retain ids, source identity, `a,q`, scale receipts and parent metadata. read all six states' scale metadata, but no earlier covariance or score arrays. the current research population is 940 players per role; the final borrowing state also contains previously seen, currently absent identities.

the finite inventory is **100 pairs, 100 existing final scores, 200 final-state decompositions, 100 incoming mean reconstructions and 600 metadata-only scale rows**. preserve all source cohorts and amplitudes; do not redraw truth, drop records, select favorable players or treat the five cells as independent populations. recorded responses, grouped game archives, old generators and 04k numerical-probe alternatives are not inputs.

the detached 04k fixture uses its own bound `complete,verified,fixture_verified` result, five cells × records `0,1`, three seasons, ten pairs/scores, twenty final decompositions, ten preceding means and forty scale rows. retain its extra null directions, changing rates and empty cohorts. fixture provenance is checked against its declared parents, not the research hashes; it supplies software evidence only.

verify each selected manifest/archive hash once per command and stream pairs sequentially. whole-archive verification reads about 29.4 gb across the fits; selective decoding reads roughly 10.3 gb cumulatively. it does not retain that volume in memory or replay 600 states. bind the predecessor's declared compound digest through its verified archive and parent metadata; do not claim to recompute that digest from `Theta` alone. preserve originals and expensive outputs. execution needs the drive; it is absent during specification, so external availability and bulk contents were not reverified here.

## exact final-state accounting

all matrices below use final-current offense then defense rows and forty coefficient columns. `H,Q` are the final current-player likelihood. take the current principal block `V` from each saved centered covariance, preserving every cross-player/role entry. `P` exposure-centers each role using final-current `u`. selection is by identity, never positional coincidence; verify final annual `p` equals the basis reference exactly.

reconstruct borrowing `m0` by aligning the immediate predecessor's **centered relative-rate** `Theta` to final-current identities; new identities have zero uncentered prior mean. independent `m0=0`. do not multiply carry by a league-rate ratio. history-only identities have zero final information columns and exposure weight, so their own mean contributes zero to current estimates. their earlier information remains inside the saved covariance/selection; selecting its current principal block does not refit or discard that information. `V` is not the proper incoming covariance.

with final raw physical truth `F` multiplied by the cell amplitude, and the saved basis `B,R=diag(p)B`:

```text
Qbar = H (F B / r)                  # current-player axes
S    = V Qbar                      # transmitted current signal
N    = V (Q − Qbar)                 # transmitted realized score noise
Cref = P m0                        # exposure-reference carry
Cupd = −V (H m0)                   # historical-mean transmission through update
C    = Cref + Cupd
Theta = S + N + C
```

this identity follows because `H,Q,Qbar` annihilate both role-constant gauges: centering the posterior covariance does not change its action on these scores. verify those gauge conditions and the identity against saved `Theta`, plus saved uncentered-to-centered means/compensation. never invert centered `V`, reconstruct a posterior or silently substitute a new solve.

multiply `V @ score` and `V @ (H @ m0)`; do not form a dense gain `V@H` or union-sized information matrix. for any coefficient component `Z`, its regional map is `r*(P Z)*R'*W`; target `T=(P F)*W` remains the **full native truth**, not its forty-mode projection. use the same transformation with `near` and `lateral` for those existing diagnostics. an npz member still requires full decoding before taking its current principal block; do not promise partial row reads.

an entrant's uncentered personal `m0` is zero. its `Cref` need not be: the reference subtracts other players' exposure-weighted mean. its `Cupd` can also be nonzero through coupled player estimates. show these noncausal channels separately under the frozen prior/reference convention. both annihilate a global role-constant shift of current `m0`; changing only old means while retaining zero entrant means changes the prior, not merely its gauge. masked-source allocations remain convention-dependent.

## scores, interactions and uncertainty

for receiver set `A` define `<x,y>_A=sum(x[A]*y[A])/(12*len(A))` for regional vectors. let physical components be `s,n,c`, error `e=s+n+c−T`, with subscripts `b,i` for borrowing/independent. independent carry is exactly zero.

```text
loss_change = <e_b,e_b> − <e_i,e_i>       # positive is harm from borrowing
d_signal    = <s_b−s_i, e_b+e_i>
d_noise     = <n_b−n_i, e_b+e_i>
d_carry     = <c_b,     e_b+e_i>
loss_change = d_signal + d_noise + d_carry
```

this is an explicit symmetric allocation of an exact paired difference, not unique causal attribution or percentages of blame. additionally retain each arm's six quadratic terms for `a=s−T,n,c`: three squared norms and `2<a,n>,2<a,c>,2<n,c>`. they must sum to its mse; keep negative cross terms. `a` includes omitted native detail, shrinkage and cross-player mixing. `V` was selected from responses, so `N` is not independent of `S,C`, need not average to zero, and its squared norm is not sampling variance.

receiver sets: all players; frozen stable/reversal/onset/no-prior groups; actual returners; the four existing minute bands; both template groups. retain exact own-group denominators and overlapping flags. primary explanation uses base and null cases, both roles; show all other cells as sensitivities. null trajectory names are bookkeeping, not actual changes. repeat direct recovery reconciliation for the existing near/lateral functionals with denominator `len(A)` and their actual targets.

partition incoming history into eight disjoint source masks: final stable/reversal/onset/history-only × source role. final no-prior source means are exactly zero and audited. compute each source's `C` by the same identity; history-only source terms are analytically zero on current receivers and checked against the union-axis fixture calculation. allocate regional signed contributions using the **same** `e_b+e_i`; the eight values sum to `d_carry`. report all receiving cohorts; do not build an eight-by-eight interaction experiment. for no-prior receivers additionally allocate `Cref` and `Cupd` separately. these trace saved input rows, not the ultimate historical origin or causal influence of a named teammate.

reconcile 04k's per-record recovery quantities and same-deployment prediction excess using `shape_recovery` and `same_deployment_excess`, preserving their exact context baseline and directed-hour denominator. no new prediction estimand or prediction-cost threshold. preserve original units: maps in recorded unblocked attempts/60, losses and allocations in their squares; positive defense is more attempts allowed.

summarize per-record paired quantities with the existing mean, sample sd, monte carlo se and two-sided 95% `t_(N−1)` interval: research `N=20,df=19`; fixture `N=2,df=1`. never treat players/regions as independent repetitions. these intervals measure monte carlo error for a response-dependent statistic under fixed truth/design/noise; scales and covariances vary across records. they do not condition on the realized fitted states and are not player intervals. show null absolute error; never divide by zero gain or call crossing zero equivalence. report each arm's rms as `sqrt(mean(mse))`, not mean per-record rms. empty fixture cohorts are explicitly unavailable with counts/reasons.

## ownership and commands

| file / owner | contract |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | `read_history_source_slice(result_ref)` returns verified final geometry, protocol/population axes and the finite bound inventory; `read_history_final_record(source, cell, record)` returns the two final states, final score and an explicit preceding-mean record. reuse `_read_selected_artifact` and existing selected-array validation; no fake full predecessor or general campaign reader |
| `analysis/src/hockey_stats/attribution.py` | `decompose_shape_history(H,Q,Qbar,m0,V,u,Theta)` accepts aligned current arrays and returns coefficient `signal,noise,carry_reference,carry_update` plus closure residuals. it and source-mask calls share `shape_history_carry(H,V,u,m0)`, which returns reference/update terms without checking the full saved mean. reuse centering semantics; validate dimensions, finite values and gauge conditions. no optimizer, solver, truth/cohort selector or writer |
| `analysis/src/hockey_stats/attribution_prediction.py` | reuse `shape_recovery,same_deployment_excess`; place genuinely shared signed-quadratic arithmetic here if needed. preserve existing callers' numbers |
| `analysis/research/attribution_priors.py` | frozen source/cell/cohort selections, `Qbar`, masks, uncertainty, diagnostic conclusions and CLI; cannot call a fitter/generator or acquire inputs |
| `analysis/research/attribution_priors_report.py` | render only saved diagnosis rows into checked prose/tables/figure; never read original arrays or recompute scientific scores |
| `docs/research/attribution-04l/` | small result, decision, verification, tables and one figure; source/fits stay external |

source wrappers may share a narrow decoder with 04k when it removes actual duplication; do not migrate old studies or change their schema/producer receipts. scientific constants/seeds/cohorts remain study policy. no new dependency, compatibility fallback, runner, cache service or artifact framework.

```text
python analysis/research/attribution_priors.py diagnose \
  --history-result docs/research/attribution-04k/result.json --output <new-dir>
python analysis/research/attribution_priors.py report \
  --diagnosis <new-dir>/diagnosis.json --output <new-report-dir>
```

derive purpose from the exact input contract. research requires the pinned result and ordinary external output under `/Volumes/Expansion/hockey-stats/runs/attribution-04l-*`; `fixture_exercise` accepts the existing 04k fixture result shape with its own declared inventory. no automatic substitute when the drive is absent. use exclusive output creation and ordinary i/o errors. write protocol/spec snapshot before analysis; write a complete result only after every required record/check reconciles. reporting consumes saved compact outputs and must work without source arrays.

## artifacts and content

use schema version `1`, existing producer/source hashes, units, finite numeric validation and explicit missing reasons. avoid copying native maps, covariances or source truth inventories.

- `protocol.json`: spec identity, parent result/prepared/protocol/assessment identities, selected pair/archive identities, member allowlist, cells/records, receiver/source masks, axes/units, equations and interval convention. artifact kind `attribution_prior_protocol`.
- `diagnosis.json`: kind `attribution_prior_diagnosis`; consumed protocol, inventory/read accounting, numerical closure receipts, record/summary tables, scale rows, limitations and resource cost. record keys: `cell,record,role,receiver,operator,arm,metric,source_group,source_role`; add `n_players,denominator,omitted_zero_targets,value,units,reason`. nonapplicable axes are explicit nulls; key uniqueness is mandatory. summaries replace `record` with `n_records,mean,sd,mc_se,ci_low,ci_high`; keep denominator/omission information. scale rows: `cell,record,state_index,season,arm,a,q,selected_exponent,status,own_reasons,inherited_limitation`.
- `result.json`: kind `attribution_prior_result`; after full reconciliation, `execution_status:complete,numerical_status:verified,study_status:diagnosed`, evidence refs, `next_hypothesis` or null and `unresolved_reason`; always `nomination:null,admission:not_admitted,handoff:null`. fixture output instead uses `study_status:fixture_verified,next_hypothesis:null` and cannot recommend scientific work. no scientific pass/fail fabricated from accounting closure; failed checks prevent a completed result.
- `comparison.csv,accounting.csv,scales.csv`: saved rows and summaries, standalone units/signs/counts; no recomputation in rendering. comparison preserves the frozen control results; accounting includes three paired allocations, six quadratic terms, source allocations and entrant reference/update terms.
- `decision.md`, `verification.md`, one figure: answer, contrary evidence, scope, costs, remaining ambiguity and next-hypothesis rationale. a content designer owns wording/figure review before implementation and after rendering.

use these finite row identifiers; additional exploratory metrics require a separately justified scope change:

| rows | identifiers / denominator |
|---|---|
| frozen comparisons | operators `twelve_region_vector,within_20_ft,lateral_redistribution,same_deployment`; metrics `regional_mse,within_20_ft_mse,lateral_redistribution_mse,recovery_benefit,directional_bias,prediction_excess,prediction_cost`; arms `borrowing,independent,zero,paired_benefit,paired_cost` only where present in 04k. retain its cohort/denominator and zero-target rules; map its `cohort` field to `receiver` |
| regional accounting | operator `twelve_region_vector`; paired arm `paired_change`: `loss_change,signal_allocation,noise_allocation,carry_allocation,source_carry_allocation,reference_carry_allocation,update_carry_allocation`. squared/cross terms use arm `borrowing` or `independent`: `signal_error_square,noise_square,carry_square,signal_noise_cross,signal_carry_cross,noise_carry_cross`. denominator `12*n_players`; reference/update allocations only for no-prior receivers |
| axes and summaries | roles `offense,attempts_allowed`; `both` only for the original joint prediction rows. frozen receiver ids come from 04k; source groups `stable,reversal,onset,history_only`, source role `offense,attempts_allowed`. summary-only `regional_rms` derives from arm mse; its sd/se belong to source mse and remain separately labeled |

good content makes stable gains and reversal/entry/null harm equally legible. use a paired `loss_change` interval panel beside a signed-term matrix, both **positive means harm from borrowing**. original benefit values remain unchanged in the comparison table. show all five cells in compact sensitivity panels/tables. keep cross-term cancellation visible. no waterfall, percentages of blame, player ranking, illustrative ability map or unlabeled apparent player confidence band.

the diagnostic decision may propose **one next hypothesis**, not one exclusive mechanism. its object contains `question,channel,receiver,evidence_keys,proposed_observable_rule,contrary_evidence_keys,tradeoff,falsifying_result`, with evidence keys resolving to saved summary rows. identify stable-player and prediction costs. truth-defined reversal/onset labels are assessment-only, never proposed fitting inputs. current-score weighting changes do not identify inherited `a` separately from carried covariance, selected `q` and coupling; differing scale receipts are supporting context only. if the link to an actionable hypothesis remains ambiguous, use `next_hypothesis:null,unresolved_reason:mechanism_interaction_unresolved` and stop. no automatic extra diagnosis, experiment, threshold change or campaign follows.

## delivery and acceptance

implement along three boundaries in order; review each independently before proceeding:

1. **source reader and algebra.** statistical reviewer checks centered-covariance identity, absent rows, reference shifts and conditional-selection claims; systems reviewer checks selected reads, hashes and owners. temporary red/green checks exercise missing/wrong/altered sources, schema/purpose/axis/order errors and detached behavior. source mismatch stops explicitly; no source repair or substitute within this slice.
2. **finite diagnosis.** exercise the existing three-year 04k fixture, with fixture parents produced locally by its existing commands if needed; this is temporary verification, not research fitting inside 04l. independent tiny analytic cases cover nonuniform exposure, a new entrant, history-only rows, cross-role coupling, exact-zero carry and negative cross terms. verify the derivative-free decomposition against a direct small proper-prior update; retain useful checked facts/fixtures.
3. **research execution and content**, only when separately assigned. reconcile all 100 pairs, 200 decompositions, 100 previous means and 600 scale rows. numeric mean/score/centering/region identities and every original per-record recovery/prediction quantity must agree at `rtol=1e-8,atol=1e-10`; also require `norm(A−B)/max(1,norm(A),norm(B)) ≤ 1e-8` for each asserted identity, using the frobenius norm for arrays and absolute value for scalars. normalize gauge residuals by `max(1,norm(original matrix))`. source identities/hashes and discrete axes must match exactly. check each current player/coefficient before averaging. independently recompute signed/quadratic/source sums and saved summaries; do not certify only the rendered means. failures retain evidence and stop completion; no threshold relaxation.

record a bounded read/compute preflight on base record zero as part of the same inventory, then complete the remainder without duplicating fits or adding repetitions. report bytes read/decoded, peak memory, wall time and zero research solves/scale evaluations. an independent reviewer verifies numerical identities using a separately derived tiny reference, plus all saved record-level closure/summary receipts; content review checks the rendered figure and exact table claims. saved-only report rerender must reproduce its numeric tables without original arrays.

follow temporary end-to-end red → green → refactor → green. after acceptance and adversarial review, delete temporary tests/controllers/test-only dependencies; retain fixtures, checked expected facts, scientific tools and verification receipts. no permanent harness is assigned. update the plan and recovery issue with the actual outcome; leave all completed study protocols, verdicts, originals, fits and publications intact.

## rationale

[hockeyviz's published Magnus 9 account](https://hockeyviz.com/txt/magnus9EV) makes component inspection and explicit historical/entrant priors central. that supports inspecting our own prior behavior; it does not validate our gaussian law, imply access to private methods or justify copying its constants. [simulation-study guidance](https://arxiv.org/html/1712.03198v3) supports explicit targets, data-generating assumptions and monte carlo uncertainty. the algebra here follows our retained estimator; its interpretation stays narrower than an empirical prior recommendation.
