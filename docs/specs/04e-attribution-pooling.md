# pr04e — test two spatial pooling bands

status: **full specification; implementation and execution unassigned.** [the plan](../plan.md) owns assignment. the user selected two spatial bands, mean recovery/prediction before interval calibration, at least 25% lower regional squared error than zero, at least 99% prediction-gain retention, and mandatory null-population diagnostics without a null nomination gate. preserve every previous verdict, including [04c](../research/attribution-04c/decision.md) and [04d](../research/attribution-04d/decision.md).

## question and scope

does learning separate pooling strengths for broad spatial patterns and remaining detail recover useful player differences within the declared shape-prediction cost?

04d finds little broad geometric omission, limited precision and substantial suppression under the selected scales. a shared global criterion can rationally sacrifice sparse effects. that motivates this hypothesis; it does not prove its cause or select an oracle variance.

one candidate and one freshly fitted control, on new known-truth populations. keep the existing 40-dimensional representation, unrestricted native context, separate volume and five-year age-neutral borrowing. change only the partition of shape covariance/scale learning. this tests spatial exchangeability; players still share scales within each band. player-specific pooling is a different, unassigned hypothesis.

success nominates a **synthetic mean estimator under the tested conditions**, not player intervals, real-player ability, positive event intensities or model admission. no real fits, historical bootstrap, new data, chance valuation, age/deployment features, alternative cutoff, website, new dependencies or research framework. [05a](05a-observed-website.md) remains independent. the existing 5% scalar-effect threshold is unchanged.

## inputs and one candidate

resolve the saved 04c basis through its [protocol](../research/attribution-04c/protocol.json) and [result](../research/attribution-04c/result.json), under `/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/`. consume the original positive shares `p`, ordered native grid, eigenvalues and `B`; basis file sha256 `67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc`, semantic identity `649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51`. validate these once. no whole-corpus read or real-preparation rebuild. old evidence supplies geometry and a bounded replay, never this study's selection outcomes.

use the exact saved 656-cell graph construction: `D=diag(p)`, `p'B=0`, `B'DB=I`, `R=DB`. the control is `graph_40ft`: one full player covariance for all 40 coefficients. the candidate, `graph_two_band_80ft`, partitions those SAME columns:

- `low`: first 11 columns, corresponding to the nested graph eigenspace with `0<lambda<=(2*pi/80)^2` before whitening.
- `high`: remaining 29 columns, its `p`-orthogonal complement inside the retained span. these whitened columns are not individual pure frequencies.

verify the separated cutoff, ranks, saved ordering and nested-subspace identity. do not rebuild a different basis, select a partial tied eigenspace or try another cutoff. 80 feet is a fixed nominal geometric wavelength, not demonstrated map precision. no mirror tying. the full retained span and omitted directions are unchanged.

each band owns `Theta_b`, full row covariance `V_b`, proper incoming mean/covariance, entry/innovation scales and search receipts. reuse current annual chronology, absent/returning-player rules, reference centering and variance search. separate band covariance is a working gaussian assumption; it does not assert independence under game-pace noise.

```text
shape_mean = sum_b Theta_b R_b'
shape_covariance = sum_b (R_b R_b') ⊗ V_b
A_shape = ybar_shape - xbar * shape_mean        # ONE unrestricted native context
map_mean = m_volume p' + shape_mean
```

never store one `V` as though the candidate remained separable, or add context once per band. volume arithmetic is identical between arms; compute it once per dataset/year and share it explicitly. each arm/band retains its own shape history. save native response energy once in the combined objective.

for residualized information `H`, shape score `T_h`, and each proper prior `Theta0_b,V0_b=L0_b L0_b'`, reuse the authoritative update:

```text
T_b = T_h B_b
b_b = T_b - H Theta0_b
K_b = I + L0_b' H L0_b
V_b = L0_b K_b^(-1) L0_b'
Theta_b = Theta0_b + V_b b_b
reduced_objective_b = q_b*logdet(K_b) - trace(V_b b_b b_b')
```

apply existing exposure centering to each update, then compute the single final context from the centered combined shape. do not also compensate that recomputed context. report the full objective as native response energy plus each band's prior-mean quadratic/cross terms and reduced objective. the full response-energy constant is NOT repeated per band. select scales using reduced objectives; preserve the control's arithmetic. search the existing 17 log-grid points on `[1e-8,1]`, with original bounded refinement `xatol=1e-4,maxiter=40`. retain endpoints and inherited limitations; no expanded search to obtain a desired result.

the shared projection owner must support the candidate, including covariance propagation needed for subsequent annual priors:

```text
mean(c,v) = r*((c'm_volume)*(p'v) + sum_b c'Theta_b R_b'v)
variance(c,v) = r²*((c'V_volume c)*(p'v)²
                    + sum_b (c'V_b c)*||R_b'v||²)
```

use the existing stable constant-shift decomposition for shape-only projections. `v=1` recovers volume. these are working conditional moments, not validated player intervals; 04e issues no interval claims.

## prospective population and fixed budget

reuse the existing lineup mechanism, with explicit new random streams: four teams of eight slots, five seasons, 96 games/year, 50 stints/game, both directions, fixed durations/strata, entrants 32/33 from year 3 and returning player 8 from year 4. preserve exact co-deployment of 26/31. extract the reused mechanism without altering the original `synthetic_designs()` or 04c response streams.

freeze ONE training history with `PCG64(40600)` and ONE independent evaluation history with `PCG64(40601)`, each calling the paired-design kernel directly, WITHOUT consuming a preceding mixed-design pass. the original historical wrapper retains its mixed-then-paired order. rosters/schedule match; sampled lineups differ. hold these designs fixed across all datasets. `r=40`, saved `p`, and training exposure reference `u` remain fixed. no original scalar ticks: true player volume effects are zero. fitted volume remains unchanged and visible diagnostically.

three populations × two noise laws × **200 independent truth/response datasets** = **1,200 paired five-year datasets**, 2,400 fitted histories and 12,000 annual states. sharing volume leaves 6,000 volume updates and 18,000 shape-band updates. no nested refits, replacement draws, added populations or extension after an inconclusive result. record actual cost; this is a finite research budget, not an eta.

### new physical truths

pair slots `(0,1),(2,3),(4,5),(6,7)` within teams 0–2. in team 3 use `(0,1),(2,7),(3,4),(5,6)`; `(2,7)` holds inseparable players 26/31. pair order and offense/defense order are fixed.

for every `(outer,team,role,pair)`, draw two physical gaussian lobes using `PCG64(SeedSequence([40602,outer,team,role,pair]))`. in order, draw `x1,y1,w1,x2,y2,w2`, with `x~Uniform(0,80)`, `y~Uniform(-30,30)`, `w~Uniform(20,40)` feet. on native centers `s`:

```text
g0(s) = exp(-||s-(x1,y1)||²/(2*w1²)) - exp(-||s-(x2,y2)||²/(2*w2²))
g = (g0 - p'g0) / max(abs(g0 - p'g0))
raw_pair_maps = (+.10*p*g, -.10*p*g)
```

fields are independent of the fitted basis and persist across all five years. the same outer's fields are shared across populations/noise laws; each assessment cell still has 200 independent outer draws. role ids are offense 0, defense 1. select no truth by representability or apparent recovery.

| population id | activation |
|---|---|
| `sparse`, 0 | one pair per team/role, selected by the first `integers(0,4)` draw from `PCG64(SeedSequence([40603,outer,team,role]))` |
| `diffuse`, 1 | all four pairs per team/role |
| `null`, 2 | none |

slots retain their signs; player ids follow the roster. entrants inherit slot effects; returner 8 changes slot and can change sign. this is an explicit transition stress, not a claim of constant player truth. do not invent truths for absent carried rows.

truth, recovery and evaluation formulas use current-player offense/defense order. select those fitted rows by identity from the all-seen annual state before comparison with `X` or truth; embed contrasts with zero coefficients for carried-only rows when calling full-state projection/rank routines. zero contrast coefficients are not absent-player truth.

center raw maps separately by role using TRAINING `u`; compensate true native shape context by `5*(raw_offense_mean+raw_defense_mean)`. generating rates remain exactly `mu=r*(p+X*raw_shape)` on both designs. evaluation never recenters fitted maps or truth to evaluation exposure. with five of eight skaters, at most three uncancelled pair members remain per role: diffuse rates are at least `.4*r*p`, sparse at least `.8*r*p`, null `r*p`. verify positivity, finite normalization and zero shape sums before drawing responses. invalid construction is an implementation/specification problem, not permission to clip, redraw or attenuate.

### responses and fresh-deployment assessment

draw training responses with `PCG64(SeedSequence([40604,population,law,outer,year_index]))`; years are 0–4, rows retain game/stint/direction/native-cell order. both arms consume identical arrays and sufficient statistics.

- `gaussian`, law 0: independent normal count-unit responses with mean `e*mu`, variance `e*r*p`; signed/fractional values are deliberate.
- `game_pace`, law 1: one `Gamma(2,.5)` multiplier per game, then independent conditional poisson counts with mean `pace*e*mu`; multiplier shared by all game rows/cells.

reuse response-generation arithmetic with an explicit rng; preserve old named streams exactly. freeze design/truth identities, seed policy and per-year response digests. stream one dataset at a time; retain compact sufficient statistics and fitted states, not full response copies.

evaluate on the independent lineups using their **known conditional means**, with training-fitted context and unchanged player order/reference:

```text
eta_true = r * X_eval * raw_shape
eta_arm = r * (A_shape_train[stratum] + X_eval * shape_mean_train)
eta_zero = r * ybar_shape_train[stratum]
P_arm = sum_i e_i * ||eta_arm_i - eta_true_i||²_(D^-1) / sum_i e_i
```

`eta_zero` is the **training context mean**, not a league constant or oracle. no evaluation response draws, fitting or recentering. these mean-error differences equal expected fresh-response squared-score differences under either noise law; no poisson likelihood is claimed. this is within-season, fresh-deployment shape prediction, not next-season forecasting. fitted complete-rate negativity remains an explicit diagnostic, never clipped or silently interpreted as a valid intensity.

## recovery, comparison criteria and decision

use 04c's exact `W:(656,12)`: six `compound_regions`, split by negative/positive y, centerline half to each side, row sums one. year 5 is primary. score actual native truth, never basis-projected truth.

each team/role/slot-pair defines `c=first_player-second_player` for that year. verify estimability under the training likelihood using 04d's centered-functional/rank convention, including cutoff sensitivity. expect 32 contrasts, with two inseparable 26−31 role contrasts excluded: **30 primary contrasts**. unexpected rank/roster discrepancies stop execution; do not silently shrink the denominator. inseparable differences report `not_estimable` despite finite prior estimates.

```text
R_arm = (1/30) * sum_c || r*c'*(shape_mean_arm - true_shape)*W ||²
R_zero = (1/30) * sum_c || r*c'*true_shape*W ||²
```

ALL identifiable pairs count, including inactive pairs. their false maps consume the same error budget. active/inactive errors use the same denominator and add to total. lower error is averaged performance, not a guarantee for every pair. units are squared attempts per 60 team minutes; no division by 12. defense coefficients retain the allowed-attempt sign, not an unexplained suppression sign flip.

for each of the four non-null population/law cells, use all 200 paired outer records. bootstrap whole paired records 10,000 times with `PCG64(SeedSequence([40605,population,law]))`, sampling 200 indices with replacement per draw. reuse each draw across every criterion; use two-sided percentile 95% intervals with linear quantiles. aggregate risks first, never average per-history ratios. these are monte carlo intervals for mean risks over fresh truths/training responses, including fitting variation, conditional on fixed references and the two deployment designs. they do NOT calibrate individual-player uncertainty.

| required contrast | support | meaning |
|---|---|---|
| `.75*mean(R_zero)-mean(R_candidate)` | lower bound `>=0` | at least 25% lower mean regional error than zero |
| `mean(R_control)-mean(R_candidate)` | lower bound `>0` | supported improvement over unchanged pooling |
| `G=mean(P_zero)-mean(P_control)` | lower bound `>0` | positive control gain makes retention meaningful |
| `.01*G-(mean(P_candidate)-mean(P_control))` | lower bound `>=0` | retain at least 99% of control prediction gain |

all four criteria must support in ALL four non-null cells for `nominate_two_band`. for strict-positive criteria, upper `<=0` fails; for nonnegative criteria, upper `<0` fails; otherwise classify unsupported overlap as inconclusive. any failed criterion gives `criteria_failed`; absent failure, any inconclusive criterion gives `criteria_inconclusive`. these are one conjunctive research claim, not unadjusted claims that every subgroup or player succeeds. report intervals/absolute costs even if the gain ratio is unavailable. zero-crossing alone establishes neither equivalence nor noninferiority.

null-population error, inactive-pair error, scales and false-map magnitudes are mandatory adjacent diagnostics. null truth has `R_zero=0`; its noisy fitted context baseline can still have positive prediction error. use no null recovery/retention ratios or nomination gates: report absolute risks and differences. adverse null behavior must qualify the conclusion but cannot acquire a retrospective veto or disappear from the report.

secondary outputs: years 1–4; active/inactive and offense/defense partitions; entry/return errors; inseparable abstention; actual versus projected native/regional truth; scale/endpoint paths; native shape and complete-rate error/negativity. actual truth varies across outer draws: do not relabel cross-truth dispersion as fixed-truth bias/variance. no outcome-selected extra fit follows any diagnostic.

always return `admission:not_admitted,handoff:null`; nomination is `graph_two_band_80ft` only on full support, otherwise null. even success stops here. any later uncertainty, real deployment or alternative pooling study needs its own assignment.

## ownership, interfaces and artifacts

| owner / files | responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution.py` | finite two-band state; shared scale/update, centering/context, map/projection and complete-rate arithmetic; strict annual artifact reader/writer; bounded numerical check |
| `analysis/src/hockey_stats/attribution_data.py` | existing grouped/synthetic sufficient statistics and exact reference/order validation; no duplicate data path |
| `analysis/src/hockey_stats/attribution_uncertainty.py` | existing `fit_history` chronology/receipts, adapted for named band states and explicit shared volume; no new bootstrap engine |
| `analysis/src/hockey_stats/attribution_simulation.py` | reused lineup/noise kernels with explicit rng; preserve named historical streams |
| `analysis/research/attribution_pooling.py` | 04e truth construction, finite cases/seeds, pairing, criteria, summaries and figures; one small batch cli |
| `docs/research/attribution-04e/` | eventual frozen protocol, result, decision, verification and two reviewed figures |

add `ShapeBandState(Theta,V,prior_mean,prior_covariance,a,q,scale,diagnostics)` and `TwoBandShapeState(low,high,A)`; `A` is native context once. extend `AnnualState` and `fit_recovery_year` with the single named candidate representation. keep the full saved `ShapeBasis`; do not disguise a truncated matrix as a valid 40-column basis. common block algebra may accept the explicit selected columns/rank. native/one-band states remain named scientific controls, not fallback paths. remove replaced duplicate arithmetic, not frozen evidence or inactive supported features.

`fit_history` owns chronology; study code does not reimplement a yearly fitter. run the control first, then supply its explicit `(benchmark,year)` volume states to the candidate through the same owner. verify population, response, row/reference identity and previous-volume lineage; share the immutable volume block without recentering or solving again. no generalized cache or paired-experiment framework. state/receipt consumers must handle the discriminated band variant explicitly. `shape_mean`, `context_mean`, `project`, `project_native` and `complete_rates` remain the sole numerical owners. extract the reused 04d estimability calculation into its responsible numerical module rather than copying rank algebra. preserve its declared tolerance and identity checks.

new `write_pooling_annual` / `read_pooling_annual` use schema 4 for BOTH fresh arms. use strict tagged shape variants; validate shape/rank, full covariances, priors, ordering, finite values and chronology. existing schema-3 readers remain explicit frozen-evidence readers; no migration, autodetection fallback or restamping. reuse envelope/hash helpers with an explicit expected schema where needed. source refs bind 04e synthetic preparation, not a fake real corpus.

the small cli exposes `prepare --purpose research|fixture_exercise --output`, `fit --prepared --population --law --start --stop --output`, and `assess --prepared --fits ... --output`. preparation freezes the complete protocol before research response generation. fixture purpose explicitly permits a smaller named synthetic design and outer count, written into its protocol; it cannot satisfy research acceptance or substitute for missing research originals. no hidden fitting during assessment, service, scheduler, runner or checkpoint system.

new schema-4 kinds are `attribution_pooling_protocol`, `attribution_pooling_prepared`, `attribution_pooling_fit`, `attribution_pooling_annual`, `attribution_pooling_assessment`, `attribution_pooling_result`. every consuming document binds `{path,sha256}` parents, producer/spec identities, purpose, applicable representation/population/law/outer/year ids, array names/order/units and resources. the protocol does not hash itself. prepared outputs save both designs, reference/band identities, region operator and seed/truth rules. `attribution_pooling_fit` is one `fit.json` range manifest: explicit half-open `[start,stop)`, population/law, ordered per-outer records and annual artifact refs. those records save shared statistics, response digests, truth/activation identity, both annual histories, full band priors/covariances, scale receipts and completeness. assessment requires disjoint, exact coverage of `outer=0..199` in all six research cells. deterministic truth regeneration is checked by digest; retain compact arrays needed for independent assessment, not duplicate full histories per downstream step.

assessment contains per-outer losses, active/inactive components, paired interval rows, diagnostics and numerical receipts. result contains `execution_status`, per-criterion status/bounds, `study_status`, `nomination`, `admission`, `handoff`, consumed refs, limitations and artifact links. unavailable ratios are null with a reason; unexpected numerical/source failures give incomplete execution, never a scientific rejection or silently omitted draw. reject missing/duplicate ranges and mismatched protocol/basis/design identities.

expensive outputs use a new external directory under `/Volumes/Expansion/hockey-stats/runs/attribution-04e-<date>/`; never overwrite prior studies. store only compact review summaries/figures in git. ordinary i/o failure stops the command; manual repair/rerun is sufficient. no local expensive-output mirror or new drive safeguards. detached verification uses explicitly marked tiny synthetic cases and existing fixtures, not automatic input substitution.

## delivery, numerical check and content acceptance

implement in three reviewed boundaries, then execute only when assigned:

1. **numerical/state owner:** add the two-band variant and strict artifacts; verify existing control/stream preservation. independent small joint gaussian solves must match bandwise means/covariances, one context and one response constant. verify within-band rotation invariance, reduction to the one-band model under IDENTICAL prescribed scale paths/incoming priors, full covariance, centering, absence/return, exact-null contrasts and scalar/map conservation. independently learned band scales need not match the control. do not add a generic prior framework.
2. **population/assessment owner:** construct the frozen designs/truth/noise and paired loss contract. verify positivity/gauge compensation, all 30 estimable contrasts, actual versus projected truth, training-only reference/context and active+inactive accounting. independent arithmetic must reproduce all 16 primary criterion rows and the single joint decision.
3. **content/study owner:** complete one detached end-to-end fixture including malformed evidence, incomplete ranges, zero denominators and all decision states; then the declared research inventory, bounded probes and report. freeze content semantics before viewing results. no lasting suite is selected here: temporary integration/live red → green → refactor → green, adversarial review, delete temporary tests/controllers/test-only dependencies; retain scientific tools, fixtures and verification receipts.

bounded resolution: for outer 0 of every population/law, inspect year 1 and year 5 in both arms: 24 annual probes, 36 shape-block probes. reuse the existing selected point/two nearest coarse rechecks and one tighter search inside the original refinement bracket (`xatol=1e-6,maxiter=80`); fixed incoming priors, no propagated history rerun or widened grid. recombine candidate bands with one context. require maximum current-player native/regional mean movement divided by `r` no greater than `1e-4`; record primary-contrast and evaluation-loss movement too. additionally substitute the probed final-year outer-0 losses into the original records and recompute all criterion intervals with the SAME bootstrap indices: no criterion's support/fail/inconclusive class may change. this links the check to the 1% budget without further fits. unresolved numerical movement withholds nomination pending cause-specific repair; it does not authorize more model search. independently checked equations use relative tolerance `1e-8`; exact identities/order/digests remain exact. probes bound selected local numerical sensitivity, not global optimization error.

retain one exact original graph-stream/posterior replay at outer 0, gaussian, years 1–5, through named frozen readers, to check the changed shared boundary. no rereading all 800 historical archives or historical refitting campaign. preserve the triangular-factor regression in temporary verification. report all finite bound-selected results in their original denominators; no failed-fit replacement.

the content designer owns a short decision, one primary table and two figures: **recovery and prediction cost** shows all criteria/bounds plus adjacent inactive/null diagnostics; **spatial changes** compares actual truth/control/candidate on common scales, with compact regional plots for band contributions. examples are year 5, outer 0: sparse team-0 offense's first active and first inactive pair, diffuse team-0 defense's first pair, and diffuse team-3 offense's inseparable pair. select these identities from activation alone, before responses; show both noise laws. prior allocation for an inseparable difference is labeled unsupported evidence. native pixels do not imply native precision.

completion requires exact inventory, accountable costs, preserved controls, independent numerical/statistical/systems/content reviews and a truthful decision—even failure or inconclusion. tradeoffs remain explicit: one extra covariance/scale process; fixed deployment/reference scope; broad physical truth families; slot-based transitions; unvalidated player uncertainty; possible negative complete rates; and limited real-hockey identification. a better pooling rule cannot create information absent from co-deployment.

method context: [magnus 9](https://hockeyviz.com/txt/magnus9EV) distinguishes historical and structural pooling, but does not prescribe our two-band model or expose private equivalence. [smooth-term documentation](https://search.r-project.org/CRAN/refmans/mgcv/html/smooth.terms.html) illustrates separating representation from penalties; no r dependency is introduced. [bayesian workflow](https://arxiv.org/abs/2011.01808) motivates separate computation and model checks, not these project-specific numerical margins.
