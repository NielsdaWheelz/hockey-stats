# pr04o — score and game-time attribution context

full specification, 2026-10-21. [the plan](../plan.md) owns assignment; implementation, research execution and publication remain unassigned. [model direction](../research/model-direction.md#04o--test-context-and-player-consequences) owns rationale. preserve [04n's evidence](../research/attribution-04n/decision.md), expensive fits and the active website.

## target and decisions

**does richer score × game-time adjustment improve held-out complete regional prediction, and how much does it change offensive/defensive player effects?**

| settled choice | consequence |
|---|---|
| fixed smooth curves within each regulation period | a small quadratic basis, with no smoothing-selection campaign; may miss abrupt late-game behavior |
| diagnostic comparison; decide adoption afterward | supported predictive gain does not automatically nominate the family or establish better player recovery |
| player changes are point sensitivities; ten new fits | five scalar and five shape states; prediction intervals condition on fits. no claim that a player's movement exceeds fitting uncertainty |

retain 04n's corrected spatial support, split, forty-mode player shape and age-neutral annual borrowing. one unchanged control and one candidate. the target is recorded, locatable unblocked attempts on matched genuine-5v5 exposure, including zero-event time; all five seasons remain research-exposed. player effects describe associations at comparable recorded circumstances. score is partly player-created: adjusting for it does not estimate the player's total causal contribution through earlier scoring or tactics.

non-goals: independent-season or source-only refits, new cohorts, acquisition, shift starts/rest/coaches/age, chance weights, origin imputation, positivity rewrite, clipping, latent-recovery simulations, calibrated player intervals/rankings, admission, handoff or website changes. the tradeoff is one contextual comparison before player-uncertainty work. public [magnus 9](https://hockeyviz.com/txt/magnus9EV) motivates contextual components; our small fixed basis is not its minute-by-minute method or private-model parity.

## bound inputs and population

bind [04n's result](../research/attribution-04n/result.json), sha256 `7245ab4873945ebaa0b58d0cd46a11ab9087e1196b4c1258770b304a7664ae6f`, and follow its checked preparation, accepted 02d correction, fit, assessment/probe and original-ledger references. expected external root: `/Volumes/Expansion/hockey-stats/runs/attribution-04n-20261021`. require these identities:

| artifact under that root | sha256 |
|---|---|
| `prepared/prepared.json` | `26ecaa961af968e936067ff31002283150bc7278adba7b7121e52c936358c902` |
| `prepared/protocol.json` | `1dae2c1f696b14c3af7456b25534d3c0f6fdb30775788ca4599dc0eeee17121a` |
| `prepared/correction.json` | `41fd7c3a5b79dee24e91335ca2eda0132feffa0120b5266f0e0c386037daad27` |
| `fit/fit.json` | `154f6e6324e3144eb6aa74aebcaabc2b6a860e123faca4b297328a087329bbcb` |
| `assessment/assessment.json` | `748b3634ce966e607fbd1d3e9bbd29c9f0ce2c84d662b797f23228725d48d558` |

the original 04a preparation supplies `segments.jsonl`, `events.jsonl`, coverage and annual spatial-row archives through those references. verify their hashes at execution; no current reconstruction may replace the frozen population. apply exactly 04n's six zero-count row exclusions: 132 physical / 264 directed seconds, no lost counts or final-season change. retain 6,560 inventory games, the same first-season `p,B,R=diag(p)B`, 656 cells, twelve `shape_regions()`, and annual `r,u` references. final 2025–26 has 1,051 training / 261 assessment games; earlier seasons are wholly training. preserve zero-time inventory games and missing coverage.

for retained spatial events, join `(game_id,assigned_segment,side)` to the frozen directed row `(game_id,segment_index,stratum[0])`. require exactly one retained directed row per retained spatial event, consume its count once, and exhaust every retained row's per-cell counts exactly. reconcile player membership, attacking team, period, clipped pre-score and source locators. preserve inclusive endpoint assignment: an event at a segment endpoint can belong to the preceding segment. do not impose a new half-open event join, split counts proportionally or substitute a midpoint. source clocks have integer-second precision, not tracking precision.

elapsed time uses the applicable score; each goal uses its own pre-event score, and following elapsed time uses the post-goal score. consume each frozen event's pre-score and accepted assignment, including same-clock events. the ledger lacks `sort_order`; never reconstruct score from ledger order, `source_index` or post-event score. an endpoint event adds no exposure or positive-duration intermediate state. preserve current-period `1200` endpoints. use the frozen clipped-score stratum, corroborated by chronology: a coalesced segment's unclipped score need not describe every event after changes outside the clipped range. unresolved joins, changed support or absent positive-time assessment context stop preparation; no silent event dropping or narrower successful-row population.

## one fixed design

retain all coarse context indicators `z`: home/away × period × attacking score difference clipped to `s∈[-3,3]`. add eighteen raw columns, in the following fixed order:

```text
period k = 1,2,3
score factor b = 1, max(s,0), max(-s,0)
time power j = 1,2
tau = (period_seconds - 600)/600
h0[k,b,j] = 1(period=k) * b * tau^j
```

the curves share home/away slopes while retaining separate coarse intercepts. lead/trail magnitude is linear within sign; time is quadratic within each period, without continuity imposed across intermissions. added terms are zero outside regulation; preserve any existing coarse overtime support, without clipping an overtime clock into regulation. the bound real corpus has regulation contexts only.

scalar volume gets these eighteen nuisance coefficients. new temporal **shape** uses only the existing forty spatial modes; old coarse context keeps its unrestricted native-cell map. thus the candidate adds eighteen volume and `18×40` shape coefficients, not `18×656` free map coefficients. fixed temporal/spatial rank supplies the smoothing assumption; no new selected penalty. player representation and historical prior are unchanged.

center the added basis within old strata using training exposure only. keep per-game raw moments so assessment uses the corresponding training centering, never its own means. the resulting training `D` below must have full rank and finite, verified solves. check rank on its diagonal-scaled correlation matrix using `lambda_min > 18 * eps_float64 * lambda_max`; record the spectrum, condition and solve residuals. unsupported rank stops explicitly, without adaptive column removal, ridge rescue or a pseudoinverse. a fixture must exercise the whole design, not evade rank checks.

## exact exposure and fitting contract

`dt` is directed hours, `X` has offense then defense indicators, and `n_j` is the native one-hot vector for event `j`. integrate polynomials analytically on retained intervals, including those with no events. products have degree at most four. evaluate event terms at their actual source times/pre-scores.

```text
E = integral z'1 dt                  J = integral z'h0 dt
M = diag(1/E) J                     h(t) = h0(t) - z(t) M
A = integral X'X dt                 C0 = integral z'X dt
Ch = integral h'X dt                D = integral h'h dt
N0 = sum_j z(t_j)' n_j              Nh = sum_j h(t_j)' n_j
K = sum_j X(t_j)' n_j
H = r [A - C0' diag(1/E) C0 - Ch' solve(D,Ch)]
T = K - C0' diag(1/E) N0 - Ch' solve(D,Nh)
scalar_score = T 1                  shape_score = T B
```

`p'B=0`; training `integral z'h dt=0`. verify those identities and both role gauges. no matrix inverse in implementation. coarse projections must reproduce 04n's corrected `A,C,E,N,K,r,u` and old likelihoods before fitting. temporal nuisance effects are estimated anew each year; only the existing player state borrows across years.

time-varying predictions require the continuous working least-squares contrast

```text
integral ||mu(t) W||² dt - 2 sum_j <n_j W, mu(t_j) W>
```

its prediction-dependent terms reduce exactly to 04n for piecewise-constant predictions. this is not an assertion of an unchanged finite-stint gaussian response, an absolute mse, a poisson likelihood or calibrated noise. old scalar response energy `Q_t` cannot be copied into the candidate or invented as zero.

add typed `ScalarScoreLikelihood(season,player_ids,H,score,u,r,source_identity)` with matching fit, validation and bounded-probe entry points. reuse `ScalarCoefficientState`, annual alignment, `_coefficient_inputs`, `_coefficient_update` and `_ScaleProblem(response_rank=1,yy=None)`. preserve the old energy-bearing `ScalarCoefficientLikelihood` and its validation. do not make energy optional, disguise scalar volume as a shape mode or introduce a fallback reader.

with fixed incoming mean `m0`, prior covariance `V_lambda` and `b=score-H m0`, the variance-dependent objective is

```text
logdet(I + V_lambda H) - b' solve(H + V_lambda^-1, b)
```

use the existing stable factored algebra, not explicit inverses. the omitted full-objective term is `energy - 2 m0' score + m0'Hm0`, constant **within** that annual variance search. record objective identity `gaussian_score_scale_contrast_v1`; values are not comparable to old full-objective levels or across years. verify constant-offset and posterior equivalence on saved controls without rewriting their objective curves or demanding bit-identical optimizer reselection. floating selection differences are bounded by the probes below.

fit five chronological candidate volume and five candidate shape states, 2021–22 through 2025–26. reuse all ten corresponding 04n borrowing states exactly, after likelihood/axis/parent/reference validation. preserve league-relative carry without old/new-rate rescaling, entry variance, innovation selection, full covariance, entrants and carried-only updates. retain the existing `log10 variance −8..0 by 0.5` grid and one bounded refinement (`xatol=1e-4,maxiter=40`). no control-chain rerun or selector search.

## physical predictions and player sensitivities

using current-training **uncentered** player coefficients:

```text
mv = r beta_raw                     Mh = r Theta_raw R'
fv = diag(1/E)(N0 1 - C0 mv)
Fh = diag(1/E)[N0 - (N0 1)p' - C0 Mh]
bv = solve(D, Nh 1 - Ch mv)
Bh = solve(D, Nh B - Ch r Theta_raw) R'
v(t) = z fv + h bv + X mv
shape(t) = z Fh + h Bh + X Mh
mu(t) = v(t)p' + shape(t)
```

the control embeds its saved coarse prediction with zero temporal coefficients. annual references are common between arms because source counts/time are unchanged. context compensation uses training-current players only; actual posterior values apply to carried-only players. a wholly unseen player has zero raw prior mean and minus its own role's shift when centered. verify raw/centered prediction equality, zero-sum shape and complete-rate sum equal to volume; do not confuse aggregate centering shift with a role's shift.

bind the sensitivity population to 04n's ordered final-season source-reference `player_ids`, excluding historical-only state ids. report both arms and candidate-minus-control changes for each, separately for offense and defense, using their common final-training `u,r,p,B` reference:

```text
scalar effect = r beta_centered
regional complete effect = (r beta_centered p' + r Theta_centered R') W
regional change size = sqrt(sum_regions(change²)/12)
```

save signed scalar and twelve regional changes, id, training included minutes and `current|carried_only|unseen` evidence status. carried-only/unseen training minutes are zero; any held-out minutes are separately labeled. within current players, summarize `abs(scalar_change)` and `regional_change_size` separately: exposure-weighted rms and unweighted median/p90/maximum. use the same normalized training exposure weights in both arms; show carried-only/unseen rows separately. the existing `±0.05r` scalar band is a descriptive practical yardstick, not a significance/adoption rule or spatial threshold. positive defense means more attempts allowed. common-gauge changes in prior-only rows are not new player evidence. no player intervals, rank claims or bootstrap of player coefficients from assessment games.

## paired assessment and signs

for each held-out game retain full joint moments of `Z=[z,h]`, including its generally nonzero coarse/time cross-block, and `X`:

```text
Gg = integral [Z,X]'[Z,X] dt         Sg = sum_j [Z(t_j),X(t_j)]' n_j
La = stack(context_native_a, player_native_a)
Dg = <(Lc-Lb)W, Gg((Lc+Lb)W)> - 2<Sg W,(Lc-Lb)W>
delta = sum(Dg)/(12 sum(directed_hours))
```

`c` is candidate, `b` the reused control; negative means lower complete regional error, in `(recorded unblocked attempts/60)^2`. no response self-energy is needed. `Gg` is mathematical notation: retain existing sparse player `A/C/K` blocks, a small dense context Gram and bounded per-game contractions; do not materialize dense player-square matrices per game or all-game-by-cell tensors. use one shared contraction kernel with explicit complete/shape target and general context Gram; the old diagonal-context shortcut is invalid here. independently reproduce the frozen 04n control comparisons by zero-temporal embedding as a compatibility receipt, not new study arms or fits.

also report scalar volume, zero-sum shape, each region, native inverse-share error and the regional volume/shape/interaction accounting from [04n](04n-attribution-follow-up.md#assessment-and-rate-diagnostics), using the exact integrated/event terms. native interaction remains zero. preserve fixed month/support summaries; do not label them subgroup accuracy tests.

reuse 2,000 draws each for games / seven-day / fourteen-day blocks, `PCG64(404130)`, the frozen calendar/block rules and common draws across all components/variants. retain zero-time games, empty blocks and unavailable zero-denominator draws. pool numerators/exposure, with linear 95% percentile intervals. all three valid intervals below zero → `supported_lower_loss`; all above → `supported_higher_loss`; otherwise `unresolved`. these intervals condition on fits, selection, split, source population and working criterion. no new gain gate, scheme selection, equivalence claim or automatic adoption.

stream the corrected held-out original rows in bounded batches for sign diagnostics. candidate rates within a row are quadratic, so static midpoint signs/masses are invalid. for total / twelve regions / native cells, solve interval roots, integrate strictly negative portions and find minima at endpoints/interior vertices. handle constant, linear, repeated-root and boundary cases explicitly; isolated zeros have zero duration. report for each arm:

- negative interval/location pairs: a pair counts only with positive-duration negative prediction; this differs from a sampled point count;
- negative location-time fraction: negative location-hours divided by `number_locations × directed_hours`;
- any-negative exposure fraction: union of negative time intervals across locations, divided by directed hours;
- negative mass: `integral sum(max(-mu,0)) dt`, in predicted attempts, also divided by `training_r × directed_hours`;
- minimum or boundary infimum and exact game/segment/side/time/location witness, labeled `attained|left_limit|right_limit`. a context/lineup jump does not give the adjoining row the same value; numerical tolerances remain separate from strict signs.

the embedded constant control must reproduce 04n's static rate diagnostics. no dense row-by-cell archive, clipping or new positivity veto. report negative physical rates beside any prediction gain; a signed player effect is a different quantity. probe variants use grouped rescoring, not sixteen native sign campaigns.

## owners, commands and saved contracts

| owner | responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | bound input/state codecs, corrected source selection and exact control reuse; retain existing readers |
| new `analysis/src/hockey_stats/attribution_context.py` | fixed exposure basis, event joins, polynomial moments, training centering/residualization and their typed arrays; one cohesive owner for the new data mathematics |
| `analysis/src/hockey_stats/attribution.py` | score-only scalar fit/validation/probe over shared annual numerical machinery |
| `analysis/src/hockey_stats/attribution_prediction.py` | general-Gram loss, physical composition and integrated sign arithmetic; preserve existing consumers |
| `analysis/src/hockey_stats/paired_evaluation.py` | existing shared ratio/calendar resampling |
| new `analysis/research/attribution_context.py`, optional cohesive report module | frozen study policy, four commands, inventory, classifications and saved-only figures |
| `fixtures/attribution/context.*`, fixture readme | compact counted five-season histories, checked timing/polynomial expectations and malformed-input cases |
| `docs/research/attribution-04o/` | decision, verification, small result/tables and two figures; expensive arrays remain external |

reuse chronology, source locators, basis, state serialization and finite correction contracts; do not import another study controller as a library. extend the shared predictor's concrete context contract, not a generic experiment framework. remove superseded duplicate derivations at the changed boundary while preserving frozen readers/evidence. no unrelated migration, public api or effect/frontend change.

```text
python analysis/research/attribution_context.py prepare \
  --source-result docs/research/attribution-04n/result.json --output <new-dir>
python analysis/research/attribution_context.py fit --prepared <prepared.json> --output <new-dir>
python analysis/research/attribution_context.py assess --prepared <prepared.json> --fit <fit.json> --output <new-dir>
python analysis/research/attribution_context.py report --assessment <assessment.json> --output <new-report-dir>
```

`--fixture <fixture.json>` replaces `--source-result`. schema 1; `kind:attribution_context_{protocol,prepared,fit,assessment,result}`, `purpose:research|fixture_exercise`; clean producer/dependency identities and existing `{path,sha256}` references. finite, ordered axes are explicit: seasons, inventory/partition games, contexts, eighteen basis columns, offense/defense players, native cells and regions. reject mismatches/nonfinite arrays, unavailable references and unexpected corrections. no path discovery, fallback or schema guessing.

- **protocol/prepared:** this spec snapshot; source/partition identities; event/exposure reconciliation; fixed basis ordering; per-game raw Gram/response archives; annual training centering, `H,score,r,u,p,B`; ranks/solve checks and control-equivalence receipts. assessment is transformed with saved training centering.
- **fit:** twenty selected component/season/arm records, ten `new`, ten `reused`; likelihood/objective identities, parents, complete raw/centered coefficients/covariance and scale/solve receipts. write each new completed state before continuing.
- **assessment:** per-game loss numerators/hours, component accounting, all interval schemes, player sensitivities/evidence groups, time-integrated signs/witnesses, bounded probes, compatibility checks and measured costs.
- **result:** `execution_status:complete,numerical_status:verified|unresolved,study_status:diagnosed|numerically_unresolved,nomination:null,admission:not_admitted,handoff:null`; diagnostic directions plus at most one justified next question, or an unresolved reason. fixture status is `fixture_verified|numerically_unresolved`, without a research recommendation. missing required evidence cannot produce completion.

run sequentially under `/Volumes/Expansion/hockey-stats/runs/attribution-04o-<date>/`; ordinary missing-path/hash/i/o failures stop. preserve completed expensive outputs. no local fit mirror, runner, automatic retries or checkpoint engine. measure elapsed time, peak memory and bytes. ten fresh states plus source-event integration cost more than simply toggling a prepared feature; 04n's timings are not a promise for this task.

## numerical and implementation acceptance

each of ten new states receives the existing fixed-history winner/two-nearest/coarse-bracket probe (`xatol=1e-6,maxiter=80`). bind the ten control states' original probe receipts and final alternatives. verify equation residuals ≤ `1e-8` and current-player physical movement ≤ `1e-4` of annual league rate. retain endpoint/inherited unresolved flags as limitations. no propagated probe histories or widened search.

rescore all sixteen primary/probe combinations of the four final components, recomputing context compensation and using shared draws. the primary complete-regional direction must remain stable; otherwise numerical interpretation is unresolved. report sensitivity of the player point changes and other diagnostic directions without new scientific vetoes. preserve primary results. algebraic reconciliation uses `rtol=1e-8,atol=1e-10` with units recorded; exact integer counts and artifact identities remain exact.

implement and independently review four non-overlapping boundaries:

1. **source/design:** counted five-season fixture with full-rank eighteen-column exposure, zero-event intervals, a goal, simultaneous events, inclusive endpoints, clipping saturation, period end and coarse overtime. reconcile original corrected counts/time; analytically verify moments against an independent quadrature/event oracle; reject wrong assignment, rank, context or correction. held-out perturbations cannot change training preparation. real coarse projections reproduce every annual 04n moment/reference.
2. **fit/composition:** independent tiny-matrix prior/posterior/gauge solves, score/full objective constant offset and probes; entrants, carried/unseen ids, changing rates and temporal shapes. ten fresh states/ten exact reuses; old energy-bearing validators stay strict. recover old predictions with zero temporal terms and validate complete/volume/shape identities.
3. **assessment:** direct integrated squared-prediction/event calculations equal grouped paired losses, including regional interaction and zero native interaction. independently verify the root/minimum/negative-mass cases, shared draws, empty-block/zero-time handling, all sixteen variants and player reference/evidence groups. reconcile the real held-out ledger and frozen control receipts after execution assignment.
4. **content/integration:** all four commands on the fixture; errors are explicit; saved-only reporting works without source ledgers/fitting calls. source, statistical/numerical and content reviewers inspect their boundaries and every material adverse result. render the two figures for legibility and verify claims against saved tables.

temporary integration/live checks follow red → green → refactor → green, then deletion with test-only dependencies/controllers. retain fixtures, checked facts, reusable assessment tools and receipts. no new permanent harness or application tests. software completion does not require a favorable scientific direction; documentation-only verification is links/consistency.

## content and final state

the content reviewer owns labels, hierarchy, units and unsupported-claim checks for every feature:

| output | good content |
|---|---|
| `decision.md` | answers prediction and player sensitivity separately; explains the actual curve restriction, fixed support, conditional uncertainty, negative-rate evidence and adoption still undecided; no improved-recovery claim from coefficient movement |
| `comparison.csv`, prediction figure | complete regional result first, volume/shape/interaction and native diagnostics alongside; all three interval schemes, units and lower-is-better direction; no absolute mse or selective favorable interval |
| `player-changes.csv`, sensitivity figure | both roles, raw signed changes and regional change size versus included training minutes; separate current/prior-only evidence; scalar 5% reference labeled as practical context, never significance or a regional threshold |
| `rate-diagnostics.csv` | resolution-specific duration, negative mass, minimum and witness; distinguishes signed effects from impossible complete rates |
| `verification.md`, `result.json` | exact input/output/control identities, counts, twenty states/probes, independent checks, costs, limitations and temporary-test deletion; no implied publication |

final state: one inspectable, reproducible research comparison with preserved controls and explicit player consequences. a favorable result informs a separate adoption/recovery/uncertainty decision; an adverse or unresolved result is complete evidence. no fitted value enters the observed website.
