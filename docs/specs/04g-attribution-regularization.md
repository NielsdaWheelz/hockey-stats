# pr04g — separate population shrinkage from annual borrowing

status: full specification requested; **documentation only, execution unassigned**. [the plan](../plan.md) owns progression. preserve the frozen [04e failure](../research/attribution-04e/decision.md) and [04f accounting](../research/attribution-04f/decision.md). the user approved one population constraint, broader physical truths, separate progress/nomination criteria, and recovery across all identifiable player combinations. this is a synthetic mean-estimator comparison, not model admission.

## question and boundary

does a separately learned population constraint improve regional recovery and fresh-deployment prediction while annual borrowing remains available?

04f locates most prediction deterioration outside its thirty tested pair differences; it does not identify a remedy. moreover, 04e's equal-and-opposite truth construction puts no predictive signal in that complementary span. 04g therefore changes one prior and broadens the assessment. it must not penalize the truth-defined pair complement or assume real players obey those pairs.

keep the one-band `graph_40ft` geometry, native context, likelihood, volume model, training references and five annual age-neutral updates. retain marginal-likelihood selection; no cross-validation selector, two-band candidate, player-specific scales, age terms, extra features, new real data, real fits, nested refits, uncertainty calibration or website changes. success nominates only a synthetic mean estimator under the declared conditions. [05a](05a-observed-website.md) remains independent.

## sources and finite work

consume 04e's original result (sha256 `b2b1b2225221bc3297556229ca6fb548c78494f7cc843ba90cb3e3f28e006c32`), preparation, saved designs, sufficient statistics and `graph_40ft` annual controls under `/Volumes/Expansion/hockey-stats/runs/attribution-04e-20261016/`. use existing strict readers and source inventory; do not restamp old artifacts or rerun the two-band arm. 04f's result (sha256 `a22161d74224c71b2f58bbfa1b39b661291bb341b6e23e5c2ae35297ada41a49`) supplies rationale, not model-selection inputs.

reuse the exact saved 656-cell grid, positive `p`, 40-column `B`, `R=diag(p)B`, `p'B=0`, `B'diag(p)B=I`; basis semantic identity `649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51`. use 04e's five training/evaluation designs and 04c's twelve-region operator `W`. no basis rebuild or source-corpus scan.

| cases | data and control | new work |
|---|---|---|
| original `paired` sparse/diffuse/null × gaussian/game pace × 200 | read all 1,200 saved datasets and controls | candidate histories only |
| new `independent` sparse/diffuse × gaussian/game pace × 200 | generate 800 datasets; fresh unchanged controls | both histories |

the original 400 null datasets serve both families; do not duplicate identical nulls. total: 2,000 paired datasets, ten cells, 2,800 new five-year history records/14,000 annual records. reuse candidate year-one shape from its same-data control, leaving **12,000 fresh shape selections and 4,000 fresh volume selections**. preserve 6,000 original control states by reference. no added draws, alternative candidates or extension after an inconclusive result. record measured time/memory/output size; the two-dimensional search increases cost, without an eta or runner.

## one normalized prior

add named policy `population_history` beside the unchanged scientific control `history`; both use `graph_40ft`. initial/entry variance `a`, annual innovation `q`, and structural precision `lambda` have distinct meanings.

- year one: use the existing one-scale zero-centered fit exactly; `a` is its selected variance. `lambda=0`, `population_precision_status:not_estimated_initial_year`; preserve the original `shape.scale.status` and its limitations separately. do not estimate two redundant zero-centered variances.
- later years: construct historical mean `M_h` and proper covariance `C_h(q)` using the existing `_prior` rule **from this arm's preceding state**. seen players retain full previous covariance plus `q` on its existing innovation indices; entrants retain zero mean and fixed initial `a`. absent rows remain in the history with zero current exposure. no age adjustment or silently reset history.
- apply one common population precision to all offense/defense rows and all forty coefficients, including entrants and carried rows. use the normalized product of the historical gaussian and the zero-centered population factor:

```text
C = (C_h(q)^(-1) + lambda*I)^(-1)
M = (I + lambda*C_h(q))^(-1) M_h
```

this also shrinks inherited means; merely reducing `q` does not. entrants receive both the fixed entry prior and the population constraint. absent-player means can contract without new observations. these are explicit assumptions, not extra evidence. `lambda=0` must return the historical prior exactly; a whole zero-lambda path reproduces the control. a zero-lambda year after earlier nonzero shrinkage need not reproduce the control's different history.

let `T=T_h B`, `H` be the existing residualized information, and `d=40`. for every candidate `(q,lambda)`:

```text
C = L L'
K = I + L' H L
V = L K^(-1) L'
b = T - H M
Theta = M + V b
objective = d*logdet(K) - 2*<M,T> + <M,H M> - trace(V b b')
full_objective = saved_native_shape_energy + objective
```

use factorizations/solves, not explicit matrix inverses. this is the normalized effective-prior marginal objective. do not add a product-of-priors agreement penalty. unlike the existing fixed-mean scale search, `M` changes with both parameters: its cross/quadratic terms and `b` cannot be cached as constants or dropped. native response energy appears once. reuse the posterior and exposure-centering owners; compute native context once as `ybar_shape - xbar*shape_mean`. retain full centered covariance for subsequent years, map/projection arithmetic and diagnostics. these working moments are not calibrated player intervals.

### bounded selection and numerical resolution

year one and the control retain the original 17-point variance grid and bounded refinement. later candidate years search `x=log10(q)` on `[-8,0]` and `t=log10(1+lambda)` on `[0,8]`, with spacing `.5`: 289 coarse points, including exact `lambda=0`. these are numerical values in the existing coefficient units. select the smallest objective; ties prefer smaller `lambda`, then smaller `q`.

also run the original one-dimensional selector on the zero-lambda boundary using this candidate's incoming history. translate every boundary evaluation to the displayed common objective before comparison: the old selector omits the fixed prior-mean energy. preserve its original search arithmetic. refine once inside the clipped half-step box around the best coarse point with bounded Powell (`xtol=1e-4,ftol=1e-10,maxfev=160`); select the best finite evaluated point across the grid, boundary and refinement. record every evaluated pair, full objective, residual, phase and search receipt. no search expansion or outcome-based tuning. preserve `scale_unresolved` for failed/nonfinite refinement, finite upper/lower search endpoints and inherited limitations; zero lambda is a legitimate boundary, not itself an unresolved scale. these flags remain diagnostics, not an additional nomination veto; all selected states must be valid and the bounded checks below must pass. never silently omit a flagged history.

freeze a numerical probe at outer 0, years 2 and 5, in all ten cells: **twenty candidate states**. independently recheck the winner, original best coarse point and its eight grid neighbors that lie within bounds. add quarter-step points within the original refinement box and rerun that box at `xtol=1e-6,ftol=1e-12,maxfev=320`. select the best original/probe evaluation under the same objective/tie rule. use unchanged incoming history, then the authoritative fixed-prior update. retain original states; probes do not launch new histories or replace selection outcomes. require equation residuals `<=1e-8` and maximum current native/region map movement divided by `r` `<=1e-4`. recompute primary summaries with the ten final-year probe substitutions and identical bootstrap indices; every primary classification must remain unchanged. a failed numerical check gives `numerically_unresolved`, not scientific failure or permission for a larger campaign. this checks bounded local resolution, not global optimality or downstream propagation of changed earlier states.

## physical truth and responses

the `paired` family is exactly 04e's frozen truth, activation, response and reference construction. regenerate only deterministic truth and verify its digest; reuse saved response statistics. mark these cases research-exposed.

the `independent` family uses the same roster, stints, train/evaluation deployment, entry/absence/return pattern and `r=40`. for each `(outer,team,role,slot)` draw physical lobes with `PCG64(SeedSequence([40802,outer,team,role,slot]))`: in order `x1,y1,w1,x2,y2,w2`, with `x~Uniform(0,80)`, `y~Uniform(-30,30)`, `w~Uniform(20,40)` feet. roles are offense 0/defense 1, slots 0–7. define on native cell centers:

```text
g0(s) = exp(-||s-(x1,y1)||²/(2*w1²)) - exp(-||s-(x2,y2)||²/(2*w2²))
g = (g0-p'g0) / max(abs(g0-p'g0))
raw_slot_shape = .09*p*g
```

no opposite partner, fitted-basis projection or fitted-outcome selection. sparse activation selects two distinct slots per team/role with `choice(8,2,replace=False)` from `PCG64(SeedSequence([40803,outer,team,role]))`; sort selected indices for storage. diffuse activates all eight. fields/activation persist across seasons by slot, with the existing entrant/returner identity transitions; share fields across activation/noise cells for the same outer. generate no truth for absent carried-only players.

center truth separately by role using training `u`, compensating native context exactly as in 04e. the generating complete rates remain `r*(p+X*raw_shape)` on both designs. diffuse rates are at least `.10*r*p`, sparse at least `.64*r*p`; verify positivity, normalization, compensation and finite fields before responses. `.09` sacrifices direct amplitude equality with the paired family's `.10` to guarantee positive rates without pair cancellation. compare arms within each family; do not compare families as a causal decomposition. invalid construction stops; no clipping, attenuation, redraw or rejection sampling.

before responses, verify nonzero evaluation-deployment truth energy outside 04f's thirty-pair span in every new non-null case; save total/complement energy and its fraction. use this only as a construction check, never to select truths, strengths or fitting directions. tiny signal remains tiny; no favorable-signal quota.

new response streams are `PCG64(SeedSequence([40804,population,law,outer,year_index]))`, with sparse/diffuse ids 0/1, gaussian/game-pace ids 0/1, years 0–4. reuse the existing explicit-rng kernels, original row order, gaussian variance and per-game `Gamma(2,.5)` pace law. both arms see identical arrays. stream one dataset; save compact sufficient statistics and exact response/truth/activation digests, not full response copies. evaluation uses known means, not new responses or fitted evaluation context.

## recovery, prediction and decisions

year five is primary. select current-player rows by identity from all-seen states. use actual physical native truth, never its projection into the fitted spatial basis.

let `E_H` be the orthoprojector onto the positive-eigenvalue span of the training `H`, using `likelihood_spectrum` and its `.1/1/10` cutoff sensitivity. let `P` be the existing role-wise training-exposure centering matrix and `J=P E_H`. the primary recovery score is:

```text
R_arm = r²/64 * || J*(shape_arm - true_shape)*W ||_F²
R_zero = r²/64 * || J*true_shape*W ||_F²
```

this scores the complete identifiable, reference-centered player space equally per represented player-role; average improvement does not guarantee recovery of every contrast. in the frozen final design, `rank(H)=60`. an equivalent interpretable operator has thirty singleton players and the identifiable average of inseparable players `{26,31}` per role: subtract the role's exposure reference, give each singleton weight 1 and each pair-average weight 2, then divide by 64. verify equivalence, rank stability, null annihilation and span before responses. **neither individual inseparable effect is claimed identified.** keep their difference explicitly `not_estimable`. do not silently drop an unexpected target or change the denominator. this new score and its 25% target apply prospectively to 04g; 04e's thirty-contrast score/verdict is unchanged and reported secondarily.

prediction uses the existing `attribution_prediction.py` owner, all native cells and both complete lineups:

```text
eta_true = r*X_eval*raw_shape
eta_arm = r*(A_shape_train[stratum] + X_eval*shape_arm)
eta_zero = r*ybar_shape_train[stratum]
P_arm = sum_i e_i*||eta_arm_i-eta_true_i||²_(diag(p)^(-1)) / sum_i e_i
```

the no-player predictor is the noisy training context, not oracle truth or a league constant. no evaluation refit/recentering. signed excess arithmetic must reconcile to error minus available signal plus context coupling as in 04f. all risk units are squared attempts per 60 team minutes; no division by twelve regions. this is within-season fresh-deployment prediction, not future-season forecasting.

each of eight non-null family/population/law cells has 200 paired outer records. bootstrap whole records 10,000 times with `PCG64(SeedSequence([40805,family,population,law]))`, family paired/independent 0/1. reuse sampled indices across all metrics; average risks before forming contrasts. use linear two-sided percentile 95% intervals. these intervals include fitting/selection variation across generated datasets, conditional on fixed designs/references and the frozen fitting rule; they are not calibrated individual-player intervals. reused cases remain research-exposed.

the two shared null cells use the same bootstrap with `family=0,population=2` and their original law ids; report absolute-risk/difference intervals only. reject duplicate `independent/null` ranges.

| criterion | supported when |
|---|---|
| recovery progress: `mean(R_control)-mean(R_candidate)` | lower bound `>0` |
| prediction progress: `mean(P_control)-mean(P_candidate)` | lower bound `>0` |
| useful recovery: `.75*mean(R_zero)-mean(R_candidate)` | lower bound `>=0` |
| useful prediction: `mean(P_zero)-mean(P_candidate)` | lower bound `>0` |

for strict-positive criteria, upper `<=0` fails; for nonnegative criteria, upper `<0` fails; remaining overlap is inconclusive. report each cell separately. `progress` requires both progress criteria supported in ALL eight non-null cells. `nomination` requires all four criteria supported in ALL eight. otherwise record failed if any required criterion fails, inconclusive if none fails but support is incomplete. progress can exist without nomination. this is a conjunctive population-level research claim, not simultaneous precision for every player or diagnostic.

the old 99% retention ratio is not reused: the control had no supported positive gain. a candidate merely approaching zero maps cannot satisfy useful recovery and positive own prediction gain. null absolute risks/false maps, inactive errors and comparisons with control remain mandatory diagnostics, without a null nomination veto or undefined zero-denominator ratios.

secondary outputs: original thirty-pair recovery; years 1–4; role, active/inactive and entry/return components; identifiable pair-average versus nonestimable difference; scales/boundaries, actual versus spatially projected truth, native and complete-rate error/negativity. retain signed cross terms in any partition. for active/inactive recovery, apply the full `J` error operator first, then partition rows by physical activation with the unchanged denominator 64; repeated pair-average rows follow their members' activation. reference centering can give physically inactive players nonzero relative truth. no selected map gallery or additional fit follows a diagnostic.

always write `admission:not_admitted,handoff:null`. nomination is `population_history` only on complete scientific and numerical support; otherwise null. successful software execution, developmental progress and nomination are separate fields.

## owners, interfaces and artifacts

| owner | change |
|---|---|
| `analysis/src/hockey_stats/attribution.py` | explicit prior policy, normalized combination/objective/selector, shared posterior/centering/projection; strict new annual codec and bounded probe |
| `analysis/src/hockey_stats/attribution_data.py` | authoritative saved-statistic decoding and identifiable recovery operator; preserve reference/order/rank contracts |
| `analysis/src/hockey_stats/attribution_uncertainty.py` | one chronology owner for both grouped inputs and already prepared annual populations; explicit shared control volume |
| `analysis/src/hockey_stats/attribution_simulation.py` | existing explicit-rng response/deployment kernels; preserve historical streams |
| `analysis/src/hockey_stats/attribution_prediction.py` | existing current-player selection and prediction/excess arithmetic |
| `analysis/research/attribution_regularization.py` | fixed cases, truth, seeds, finite cli, comparisons and report; no second fitter |
| `docs/research/attribution-04g/` | eventual protocol/result, decision, verification, tables and one figure |

reuse `GraphShapeState`, retaining `a`, `q`, full effective `prior_mean/prior_covariance`, `Theta`, `V`, context and receipts. add explicit policy identity to the model/state contract; `shape.scale` records selected `lambda`, both coordinates, all evaluations, limits and initial-year status. preserve historical and effective prior identities separately. no universal prior interface or model registry.

extract `fit_population_history(...)` within the existing chronology module; it accepts the ordered annual `RevisionPopulation` selection, explicit source/model identities, prior policy and optional named control-volume mapping. existing `fit_history` remains the grouped-input adapter and delegates after its normal weighted preparation. saved 04e sufficient statistics use the same chronology, without fabricated game rows. expose the policy through `fit_recovery_year`; all old callers explicitly select `history`. repeated algebra belongs to the package, not copied study controllers.

for `population_history`, require the matching immutable control volume for every year, with exact source/population/statistic/order/reference and previous-volume lineage. model-protocol identities intentionally differ between reused controls and the candidate; verify their evidence equality without requiring or inventing equal model identities. reuse initial shape numbers without refitting, recording their control parent. later candidate shape history uses only preceding candidate states. independent controls use the unchanged history rule. existing source/state readers remain explicit frozen-evidence readers, not compatibility fallbacks.

new schema `5`, kinds `attribution_regularization_protocol|prepared|fit|annual|assessment|result`. reuse artifact/hash helpers; no automatic schema dispatch, migration or rewriting old outputs.

- **protocol/prepared:** exact spec/producer/source refs; designs, geometry, regions/recovery operators; source-versus-fresh inventory, truth/noise/search/bootstrap/numerical rules; purpose, units, seeds and budget frozen before new responses.
- **fit:** half-open outer range, exact family/population/law, ordered per-outer truth/response/statistic refs and both annual histories. original control refs retain schema 4; fresh states use the strict schema-5 codec. record `computed|reused_control` and source refs explicitly, never pretend reused work is a new solve.
- **annual:** source/model/policy/basis/season/player identities; previous same-arm annual and shared-control refs; native/context arrays, full working covariance, historical/effective priors, `a/q/lambda`, complete search and numerical receipts. reconstruct and check chronology/prior identities on read. no scalar covariance substitutes.
- **assessment:** all 2,000 paired records, denominators, primary/secondary risks, signed excess reconciliation, eight non-null interval tables, two null tables, numerical substitutions and costs. assessment reads states; it performs no fit or parameter search.
- **result:** consumed refs; exact completeness; `execution_status`, `numerical_status`, per-criterion classes, separate `progress_status`/`nomination_status`, `nomination`, `admission`, `handoff`, limits and report refs. unexpected input/numerical failures remain incomplete/unresolved, never omitted datasets or scientific rejection.

all references are `{path,sha256}`; arrays have exact names/order/dtypes and finite-value checks. bind current inputs separately from frozen producers. reject overlapping/missing ranges, changed responses, wrong histories, control/candidate swaps and mismatched references. use exclusive new directories under `/Volumes/Expansion/hockey-stats/runs/attribution-04g-<date>/`; keep compact reviewed evidence in git. ordinary i/o failure stops; manual rerun suffices.

manual cli: `prepare --source-result --purpose research|fixture_exercise --output`; `fit --prepared --family --population --law --start --stop --output`; `assess --prepared --fits ... --output`. research requires a clean identified producer and exact complete inventory. explicit tiny fixtures cannot satisfy research acceptance. no scheduler, resume engine, local expensive-output mirror or automatic source substitution.

## delivery and acceptance

non-overlapping boundaries; independent adversarial review before moving on:

1. **numerical/state:** temporary red → green → refactor → green integration checks. independent dense gaussian calculation verifies normalized prior, full marginal objective and posterior across nonzero means/correlated covariances. check zero-lambda reduction, basis-rotation invariance, centering/context conservation, entrants, carried returns and inseparable directions. preserve the control and old decoder behavior; no copied optimizer/chronology.
2. **population/assessment:** independently verify physical positivity, role gauge, new complementary signal, rank/span/entity metric and both risk formulas from direct rows. reconcile all original thirty-pair control risks before adding the new target. audit new and reused source paths, no evaluation leakage, exact ranges and bootstrap pairing. detached fixture integration exercises both paths and malformed-evidence rejection.
3. **assigned execution/content:** only after implementation is assigned, run the finite inventory and twenty numerical probes; recompute direct-row scores for outer 0 and 199 in all ten cells and bootstrap one paired, one independent and one null cell independently. use `abs(actual-expected)<=1e-8*(1+abs(expected))`; signed excess checks use the small excess as reference. the fit command produces probes; assessment only validates/substitutes their saved outputs. do not silently alter scientific criteria or replace failed histories.
4. **closure:** exact counts, finite reconciled evidence, measured costs, independent numerical/statistical/systems/content review, rendered figure inspection and truthful decision. delete temporary tests/controllers/test-only dependencies after verification; keep fixtures, checked facts, assessment tools and receipts. update plan/issues; preserve previous evidence. no permanent test suite is assigned here.

the content designer owns `decision.md` (≤500 words), `comparison-table.md`, `diagnostics-table.md` and `recovery-prediction.png`. every number derives from assessment. show four aligned interval panels for the four criteria, all eight non-null cells, explicit zero lines/units; place null, scale and transition diagnostics adjacent in tables. distinguish named identifiable averages from unsupported individual effects. headline progress and nomination separately, give contrary evidence, then at most one next question. no “criteria passed” scoreboard, risk percentages against the large common context-noise term, or ability claim.

tradeoffs: continued population shrinkage can erase persistent truth as well as false maps; retaining marginal likelihood isolates the prior change but leaves that selector's suitability open. a broader recovery target gives up direct primary-score comparability with 04e. independent physical truths cost new fits and differ in amplitude; fixed deployments, gaussian working moments, slot transitions and synthetic laws still limit transport. bounded search leaves global optimization uncertainty. no success establishes player intervals, valid positive fitted intensities, chance valuation or real-hockey ability.

method context: the published [magnus 9](https://hockeyviz.com/txt/magnus9EV) distinguishes historical and structural constraints. it motivates separating those responsibilities; it does not prescribe this scalar player penalty, its selection rule or an exact private-model replication.
