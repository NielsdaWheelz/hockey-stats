# pr04c — recover broad spatial shape

status: **full specification; execution unassigned.** the user selected broad patterns before cell precision, shape recovery before complete regional-rate recovery, and synthetic refit uncertainty with only a conditional real point-fit chain. [the plan](../plan.md) owns assignment. preserve [04b's mixed verdict](../research/attribution-04b/decision.md) and all earlier evidence. this document authorizes no execution by itself.

## question and boundary

does restricting relative player shape to broad rink patterns recover known spatial differences better than zero and the native 04b estimator, with intervals meeting the declared recovery floor?

one candidate: a fixed low-frequency graph basis for player **shape**, retaining separate volume, native context, five chronological seasons and age-neutral annual borrowing. diagnose saved 04b outputs first; run the candidate only if that diagnosis supports the mechanism. no alternate basis, cutoff tuning or second model follows a failure.

the primary estimand is the zero-sum allocation of recorded unblocked attempts, separate from how many attempts occur. complete rates and native cells remain visible secondary diagnostics. a successful result nominates a developmental shape representation under tested assumptions; it establishes neither complete player-map accuracy nor supported ability, defense-wide recovery, physical location accuracy or private hockeyviz parity.

non-goals: source changes/acquisition, chance fitting or valuation, age/deployment features, positivity links, alternative intervals, real historical bootstrap, website/publication, generic research infrastructure. the 5% meaningful **scalar** contrast remains unchanged; it supplies no spatial accuracy margin. [05a](05a-observed-website.md) remains independent.

## inputs and diagnosis before fitting

use [04b's result](../research/attribution-04b/result.json) to resolve its exact external artifacts under `/Volumes/Expansion/hockey-stats/runs/attribution-04b-20261015/`, including:

| input | sha256 |
|---|---|
| `prepared/prepared.json` | `fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b` |
| `fits/fits.json` | `356fe332cd0c8d3786140db41c99e739ba4a807c519ddb7c1ab6a876a7a580fc` |
| `simulation/simulation.json` | `6075a4de7ca5449a2e66e2b7b6bd7caca7d81e6c4dedc29a12d328f627250863` |
| `assessment-02/assessment.json` | `a2a3347f29d1c0cde218e4ddec2175946f45c71a4a7306d7b441966d48d6319b` |

follow bound manifests, never discover a convenient replacement run. preserve original model/reporting identities and the corrected 04a control. the hdd was detached during specification: external-array diagnosis is an execution prerequisite, not a result obtained here. no recapture/refit to bypass missing originals.

retain all five admitted seasons, 2021–22 through 2025–26, their 6,560-game inventory, matched spatial counts/time and zero-event exposure. unchanged annual `r,u`, first-season positive native shares `p`, player/stratum order, masks and source-population ids remain conditional references. the new model protocol has its own identity; do not restamp old preparation. only the existing unblocked spatial population is refitted; all-attempt states are read-only controls.

reconcile all saved 04b outer states and errors, then diagnose broad `3−4` and localized `18−19` in years 1 and 5. express a contrast map as `d=t*p+h`, `sum(h)=0`. in ordinary native squared error:

```text
||error||² = delta_t² * ||p||² + ||delta_h||² + 2*delta_t*p' delta_h
```

retain the cross term: zero-sum does not mean orthogonal to nonuniform `p`. report volume-only predictions using the SAME fitted volume, shape bias, sampling variation, mean-pattern attenuation, interval centering/width, entry/innovation scales and endpoint/inherited limitations. compare original point fits with saved weighted searches without treating different optima as proof of a bug.

fixed regional operator `W:(656,12)`: use the six existing `compound_regions(grid()[0])` regions, each split by negative/positive `y`; give centerline cells half to each. every row sums to one. this reveals left/right patterns the original six totals can cancel. use these same regions throughout 04c.

**diagnosis gate:** for each noise case, take all 200 saved final-year broad shape estimates, `a_i=W' h_i`, and actual truth `a`. compute `bias2=||mean(a_i)-a||²`, `variation=mean(||a_i-mean(a_i)||²)`, and verify their sum equals mean squared error. proceed only if `bias2>variation` in BOTH cases, after evidence/numerical reconciliation. otherwise record `mechanism_not_supported` and stop. this descriptive test identifies bias-dominated failure; it is not a new scientific success threshold or proof that the proposed basis repairs it. an evidence/implementation discrepancy gives incomplete execution and an issue, not permission to replace the control.

## one geometry-defined representation

use the existing 656-cell `shot_origins.grid()` and cardinal adjacency. with cell spacing 5 feet, let `L=(diag(degree)-adjacency)/25`. retain the positive eigenmodes with `lambda <= (2*pi/40)^2`; exclude the single constant mode. the current grid has **40 retained modes**: last retained eigenvalue about `.02386537`, next about `.02552307`, cutoff about `.02467401`. require the expected grid/rank and a separated cutoff; no rounding-based partial eigenspace selection.

this is a 40-foot **nominal wavelength for relative shape**, not demonstrated 40-foot accuracy, interpolation or mirror tying. geometry selects eigenvectors; the existing reference `p` defines centering/units. no synthetic truth or fitted response selects complexity. use existing numpy/scipy; save one basis and its identity for every year/refit rather than relying on repeat eigenvector signs.

```text
D = diag(p)
E = retained eigenvectors                         # 656 × q, q=40
F = E - 1*(p' E)
G G' = F' D F                                    # lower cholesky
B = F G^(-T)                                    # p'B=0; B'DB=I
R = D B                                         # 1'R=0; R'D^(-1)R=I
shape_mean = Theta R'                            # Theta: 2n × q
map_mean = m_t p' + Theta R'
shape_covariance = (R R') ⊗ V_h
```

store `B,p`; derive `R`. no `656×656` prior or player×cell kronecker allocation. smoothing `h/p` does not remove empirical texture in `p`. omitted directions have no conditional model variance; truth outside the basis must remain an explicit bias diagnostic, never a claim of certainty.

retain 04b's volume fit and independent full row covariances, annual entry/innovation, absence/return rules, exposure centering and context compensation. shape carries coefficient means `Theta` and full player covariance through the SAME fixed basis. scale units remain whitened shape variance; do not multiply by `655/40`. no later data revises an earlier annual point estimate.

fit the existing native shape likelihood with a restricted player prior. for 04b's residualized `H,T_h,shape_yy`, coefficient prior `Theta0,V0=L0 L0'`:

```text
T_B = T_h B
b = T_B - H Theta0
K = I + L0' H L0
V_h = L0 K^(-1) L0'
zz = shape_yy - 2*sum(Theta0*T_B) + sum(Theta0*(H Theta0))
objective = q*logdet(K) + zz - trace(V_h b b')
Theta = Theta0 + V_h b
```

`zz` includes native response energy outside the basis; it is constant during one variance search. the candidate searches using `q*logdet(K)-trace(V_h b b')` to avoid cancellation, and reports both that reduced objective and the full value. the named native-04b control preserves its original full-objective/selection arithmetic; shared refactoring cannot silently change it. never substitute the volume quadratic or combine native rank with projected contraction. reuse native grouped `Q_h`; no new count pass is needed for projected response energy.

context remains **unrestricted native shape**: `A_h=ybar_shape-xbar*Theta*R'`. projecting context into the basis would change a second mechanism. apply original player centering and compensate context exactly. complete rates remain additive and may be negative; never clip.

retain the variance search `[1e-8,1]`, 17 log-grid points and original bounded refinement (`xatol=1e-4,maxiter=40`). finite bound-selected fits remain in all denominators with their limitations. do not widen the range or suppress inherited flags.

for player contrast `c` and native weights `v`, the sole projection owner returns:

```text
mean = r * ((c'm_t)*(p'v) + c'Theta*(R'v))
variance = r² * ((c'V_t c)*(p'v)² + (c'V_h c)*||R'v||²)
```

`v=1` recovers volume exactly. use the existing constant-shift decomposition for stable zero-sum arithmetic. shape-only projections use `v-(p'v)*1`; no subtraction of two independently estimated intervals. covariance retains teammate/opponent/role dependence. working intervals remain conditional diagnostics, separate from empirical refit intervals.

## fixed synthetic population and responses

reuse `attribution_simulation.synthetic_designs()["paired"]` unchanged: five years, four teams of eight, 96 games/year, 50 stints/game, both directions, original scalar ticks, exposure, strata, entry/return and persistent co-deployment of 26/31. this preserves `PCG64(40400)` including the preceding mixed-design pass. keep known `r=40`, annual design `u` and corrected real `p`; no synthetic all-attempt chain or blocked-response component is needed.

define `h(g,a)=a*p*(g-p'g)/max(abs(g-p'g))`. assign these uncentered shape rows, zero elsewhere:

| pattern | `g` on native centers `(x,y)` | assignments |
|---|---|---|
| broad radial | original 04b rule: `+1` on nearest-to-`(89,0)` cells through cumulative `p>=.5`, `−1` elsewhere; native-index distance ties | offense 3 `+h(g,.10)`, 4 its negative |
| broad lateral | `I(x>25)*y/42.5` | offense 10 `+h(g,.10)`, 11 its negative |
| localized | `exp(-||(x,y)-(80,15)||²/200)-exp(-||(x,y)-(80,-15)||²/200)` | offense 18 `+h(g,.10)`, 19 its negative |
| rough | `I(x>25)*sin(2*pi*(x+100)/20)*cos(2*pi*y/20)` | offense 20 `+h(g,.05)`, 21 its negative |
| entry/return | radial / lateral as above | entrant 32 offense `+h(radial,.05)` from year 3; entrant 33 defense `+h(lateral,.05)` from year 3; returner 8 offense `+h(radial,.05)` from year 4 |
| exact-null difference | lateral | offense 26 `+h(lateral,.05)`, 31 its negative in every year |

center scalar and shape truths separately within offense/defense using that year's exact `u`, including single-player/paired-sum truths. let `M_truth=t_truth*p'+H_truth`; generating rates are `mu=40*(p+X*M_truth)`. validate finite strictly positive rates and truth sums BEFORE response generation. if invalid, stop for a specification correction; never clip, redraw or attenuate a pattern after outcomes. differing shape amplitudes are fixed controlled stresses, not claims about real-player magnitudes.

two noise cases, each **400 independent outer datasets**, with identical responses for candidate and fresh native-04b control:

- `gaussian`, case 0: independent count-unit normal draws, mean `e*mu`, variance `e*40*p`; signed/fractional values are deliberate synthetic responses.
- `game_pace`, case 1: one `Gamma(2,.5)` multiplier per game, shared across its rows/cells; independent poisson responses conditional on that multiplier, means `pace*e*mu`.

response seeds are `SeedSequence([40430,case_id,outer_id,year_index])`, using `PCG64` and sorted game/stint/direction/native-cell order. freeze exact generated truths, design order and per-year response digests; these are new response streams, not a replay of 04b outcomes. compare each estimate with **actual truth**, never projected truth. `h_projected=(h*B)*R'` is an oracle representability diagnostic only.

## staged assessment and stopping rules

### 1. means, before nested refits

fit five-year native-04b and candidate spatial chains on each of the 800 datasets. the native control is the current `fit_revision_year`, NOT `fit_shared_volume_control` (04a). common volume arithmetic may run once and be shared explicitly; both shape chains retain their own priors/scales. no reused old response fits. save point states, true/estimated native shape and complete maps, original-equation diagnostics and scale paths.

assessment shape is `h_est=r*c'Theta*R'`, in attempts/60 team minutes; generating `H_truth` is dimensionless, so `h_truth=r*c'H_truth`. apply that unit conversion once, including old saved arrays whose units differ. primary error is final-year `||W'*(h_est-h_truth)||²`, in squared attempts/60 team minutes. assess offense radial `3−4` and lateral `10−11` under both noise cases, against **zero shape** and **matched native-04b shape**: eight comparisons. a volume-only map has exactly zero shape, so it is not a third independent primary comparison.

for each comparison, bootstrap its 400 paired outer errors with 10,000 resamples, `SeedSequence([40432,case_id,contrast_id,baseline_id])`; ids follow the order above, baselines zero then 04b. use a two-sided percentile 95% interval for `baseline_error-candidate_error`: lower `>0` supports improvement; upper `<=0` fails; otherwise inconclusive. every outer dataset stays in its denominator. only **all eight supported** permit stage 2. any failure gives `mean_recovery_failed`; otherwise any overlap gives `mean_recovery_inconclusive`; stop without nested or real fits.

report absolute/normalized error, attenuation, bias and variation. normalization by zero truth energy is unavailable, never silently zero. positive gain is a directional developmental criterion, not an independently justified practical spatial-accuracy margin. complete-map comparisons with zero, same fitted volume-only and 04b remain secondary; they cannot become outcome-selected vetoes of this shape nomination.

### 2. uncertainty, conditional on stage 1

on those SAME 800 datasets, perform **200 candidate full historical spatial refits each**. draw one positive normalized exponential game multiplier per inventory game/year with `SeedSequence([40431,case_id,outer_id,draw_id,year_index])`. use `attribution_uncertainty.game_weights`; refit native context residualization, volume/shape scales, full covariance and chronological priors. hold original `r,u,p`, basis and topology fixed. no fixed-scale shortcut, new datasets, control bootstrap or failure replacement.

retain grouped sufficient statistics once per active outer dataset. between stages, deterministic response regeneration is allowed once per outer dataset: match saved response digests and unit-weight point statistics before refits. do not archive the entire synthetic response corpus or rescan/generate responses inside each inner draw. save requested joint projections, weights/seeds and scale/status receipts; no full inner covariance archive.

primary intervals are the existing pointwise basic intervals `2*point-quantile(draws,[.975,.025])`, linear quantiles. do not add working variance. primary functionals, always p-centered, are:

```text
v_radial = I(distance((x,y),(89,0)) <= 20) - its p-weighted mean
v_lateral = I(x>25)*sign(y) - its p-weighted mean     # sign(0)=0
```

four primary coverage cells: year-five radial `3−4` under `v_radial` and lateral `10−11` under `v_lateral`, each in both noise cases. coverage compares actual generating truth with each refit interval. a two-sided 95% wilson interval, denominator 400 outer datasets, supports the `.90` floor if its lower bound is `>=.90`, fails if its upper bound is `<.90`, otherwise is inconclusive. this is a **90% developmental floor for nominal 95% pointwise intervals**, not 95% calibration or simultaneous map coverage. requiring all comparisons to pass is an intersection decision; individual intervals remain pointwise.

record working and refit coverage, width, bias and wrong-sign zero exclusions for the following fixed diagnostics; the primary four alone enter nomination:

| diagnostic | years and functionals |
|---|---|
| four shape pairs `3−4,10−11,18−19,20−21` | years 1 and 5; all 12 shape-region totals, radial/lateral functionals and maximum-absolute-true-shape cell (native-index tie) |
| nonzero entry/return shapes | 32 offense and 33 defense in year 3, 8 offense in year 4; 12 shape regions and their assigned radial/lateral functional |
| inseparable 26/31 | individual players and difference in every year: `not_data_identified`, no empirical interval or directional/equivalence assertion; retain raw spread and working prior-conditioned diagnostics. sum in years 1 and 5: both broad functionals and 12 shape regions |
| matched volume | original spatial scalar pairs `2−5,6−2,7−2` in year 5 and the three original scalar transitions; report original exact scalar truths and 5% labels separately, without new scalar nomination |

regional coverage gets the same floor classification; failing/inconclusive transition/local/rough cells remain explicit limitations, not suppressed rows. exact-null abstention is a software requirement, not successful recovery of zero. do not infer individual identification from the sum or low false-claim rates from wide intervals. no meaningful 5% label is applied to shape.

maximum nested budget: **160,000 spatial histories, 1.6 million small annual volume/shape block fits**. this exceeds 04b's synthetic budget but removes its 200 expensive real histories. 400 outer datasets reduce monte carlo ambiguity in the four nominated coverage cells; they do not cure model bias. use at most four workers, one numerical thread per worker; record actual wall/process time and memory, without an eta promise. no extra draws to resolve an inconvenient overlap.

### 3. conditional real point fit and decision

only all eight mean comparisons and four primary coverage cells supported, with complete execution and numerical/null checks passed, yields `nominate_broad_shape`. then execute **one five-season real spatial point-fit chain**, replay spatial volume against saved 04b and retain the unchanged all-attempt control. no real bootstrap or new real-player refit intervals.

stream the original five annual ledgers once for scalar/map/context accounting and existing native negative-rate diagnostics: strict sign counts, exposure-weighted cell frequency, extrema/examples and negative mass. retain zero-event time and each control's frozen arithmetic, including exact zeros: native-04b uses its saved volume/shape composition; historical 04a uses its original flat `M,A`, never a rounded split/recombination. report complete-rate inadequacy without relabeling it as shape failure or an intensity model.

show final-year point maps for the four unchanged real examples from pairs `(8476460,8478398)` and `(8480336,8480800)`, both roles. no fitted-player selection, rankings, new meaningful labels or borrowing of 04b's real refit intervals. working intervals may appear only as explicitly conditional numerical diagnostics. real fit failure leaves that stage incomplete; it does not erase complete synthetic evidence or authorize a new model.

if stage 2 has a failed primary cell, recommend `uncertainty_failed`; if none fails but any is inconclusive, `uncertainty_inconclusive`. diagnosis rejection, mean stops and uncertainty stops are complete scientific answers when their assigned stages reconcile; future stages are `not_run` with the exact reason. numerical/resource/input failure is `incomplete`, never a scientific rejection. always `admission:not_admitted,handoff:null`. complete real-rate accuracy, real-player uncertainty, source/deployment robustness and supported chance valuation remain separate requirements.

## owners, contracts and files

`saved evidence → diagnosis → frozen basis/protocol → paired mean recovery → gated refit recovery → conditional real point fit → scoped report`.

| owner | boundary / required interface |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | existing grouped data, fixed references and weighted residualization. consume original preparation read-only; no new source interpretation or eligibility logic |
| `analysis/src/hockey_stats/attribution.py` | `build_shape_basis(grid,p)`, typed basis/state, explicit basis-aware annual fit and sole map/projection/complete-rate arithmetic. retain native-04b only as a named scientific control; share posterior, prior and scale mechanics |
| `analysis/src/hockey_stats/attribution_uncertainty.py` | common historical refit with explicit selected populations, per-season game weights and shape representation. move 04b-specific seeds/budgets/selections to its caller where necessary; no duplicated annual loop or plugin registry. generalize exact-duplicate checking only to the selected population set |
| `analysis/src/hockey_stats/attribution_simulation.py` | unchanged shared lineup/design generator; new study patterns/policies do not belong here |
| `analysis/research/attribution_recovery.py` | diagnosis, 04c truth definitions, phase commands, projection requests, criteria, costs and figures. no copied posterior or imports through historical study controllers |
| `docs/research/attribution-04c/` | implementation-time protocol, result, decision, verification and three figures; do not fabricate these evidence files during specification |

keep numerical primitives cohesive; introduce a private basis helper module only if it absorbs substantial complexity. adapt directly affected projection/valuation consumers to the explicit new state, with no new valuation campaign. the active state/reader separates `source_prepared` from `model_protocol`: existing population loaders carry the old source protocol, which must not masquerade as the new model protocol. hard-cut the active contract; old artifact readers retain their original checks solely as named read-only controls. no automatic fallback, silent schema conversion or historical artifact migration.

new artifact schema `3`, exact purpose `research|fixture_exercise`, finite json and non-pickle npz; reuse `artifacts.py`/`chance_cli` identity and exclusive-output primitives. every manifest binds implementation, consumed `{path,sha256}` identities and ordered array shapes. diagnosis binds the spec snapshot and old evidence; the subsequent frozen protocol binds diagnosis, and model-stage manifests bind that protocol. a diagnosis-only result binds diagnosis/spec with `model_protocol:null`. no circular hash. research requires a clean producer; fixture exercises record dirty producer state when necessary during red/green and cannot satisfy research acceptance. preserve separate model/reporting producers for a later reporting-only correction.

| artifact kind | required content |
|---|---|
| `attribution_recovery_protocol` | frozen spec and diagnosis, old evidence refs, grid/reference identity, basis rule, generators/seeds, stage budgets, requests/criteria, output root and producer; no self-hash |
| `attribution_recovery_diagnosis` | spec snapshot/producer/old evidence, reconciled artifacts/denominators, volume/shape/cross decomposition, broad bias/variation gate, scale/interval evidence and explicit stop/proceed reason; no model-protocol dependency |
| `attribution_recovery_prepared` | new protocol, original preparation/source ids, original annual references/ledger refs, bound basis `B:(656,40)`/eigenvalues/`p`, fixed `W`/functionals and synthetic design/truth identities; no copied raw data |
| `attribution_recovery_annual` | explicit `representation:graph_40ft|native_04b`, year/previous/source/model identities and ordered current/entrant/carried ids; unchanged volume; candidate shape `Theta:(2n,40)`/basis identity, native control shape `M:(2n,656)`; each has `V:(2n,2n),A:(s,656)`, matching prior mean/full prior covariance, independent entry/innovation/scale status and original `r,u,p`. no width-based inference or graph basis on native controls |
| `attribution_recovery_means` | all 800 unique `(case,outer)` records, response digests, point states/errors/baselines, eight gate intervals, completeness and reason; region/native/complete errors have distinct names |
| `attribution_recovery_intervals` | same 800 ids × 200 unique inner ids, fixed joint request identity, weights/seeds, scale outcomes and projection arrays; actual truths, numerators/denominators, working/basic kinds, four primary rules and all scoped diagnostics |
| `attribution_recovery_real` | five ordered annual refs, scalar/volume replay, point examples, single-pass native diagnostics, numerical probes; explicit `real_refit_intervals:null` |
| `attribution_recovery_result` | stage status/reason and evidence refs, named rule matrix, nomination and scope, costs/limitations, `admission:not_admitted,handoff:null` |

common projection record: `(case,outer,year,role,player_coefficients,functional_id,estimand)` where `estimand=shape|volume|complete_rate`; units, truth, point value, working interval, refit interval or unavailable reason. array order/request hashes must agree across draws; do not align by incidental list position. represent `not_data_identified`, `not_run` and `incomplete` distinctly from a finite zero. inner histories retain compact selected-scale/status receipts as in 04b's `_short_annual`; full search curves belong to point states/designated probes, not every inner fit. no full inner covariance archive or repeated native decoding in scale searches.

manual commands in the single study entry point:

```text
diagnose --baseline-result --out
prepare --baseline-prepared --diagnosis --protocol --out
pilot-means --prepared --out
pilot-intervals --prepared --means --out
fit-real --prepared --means --intervals --out
assess --diagnosis [--prepared --means --intervals --real] --out
```

arguments name manifest files, not guessed directories; validate prerequisite identities and pass status. `assess` accepts only the artifacts for reached stages, and explains omitted stages. all research outputs remain external-only under `/Volumes/Expansion/hockey-stats/runs/`; ordinary mount/path/i/o handling, manual reruns and preserved expensive outputs suffice. no drive safeguards, local fit mirror, vm, scheduler or checkpoint engine. incomplete ids are retained/reported; never reduce denominators or replace failed draws. bounded fixtures can run detached with the same code paths and explicit smaller fixture budgets.

## numerical verification, content and completion

non-overlapping delivery boundaries, with an independent adversarial reviewer before proceeding:

1. **evidence and geometry:** reconcile old saved summaries; temporary red → green checks for decomposition including the cross term, fixed twelve-region accounting, basis rank/orthogonality and rotation invariance. source/reference changes or missing originals stop execution. no unrelated source re-audit.
2. **model owner:** independently assemble a tiny joint gaussian system and compare coefficient/native means, covariances, context compensation, scale objective and projections. include corrected triangular-factor regression, unit-weight native control replay, shape orthogonality, volume conservation, absent/entrant/returning chronology and exact-null contrasts. hashes, orders, masks and original reference arrays require exact equality; numerical replay/equation comparisons use relative tolerance `1e-8`. report residuals, not optimizer success alone. forbid material negative variance; keep existing bounded-roundoff interval-sqrt handling distinct from prohibited rate clipping.
3. **study/uncertainty:** temporary end-to-end fixture red → green → refactor → green through diagnosis/stop, means/pass/fail, refit gate, real gate and reporting. independently recompute fixed truth, region errors, paired resamples, basic quantiles, wilson criteria and exact-null abstention. check changed request/basis identity, missing/duplicate/error draws and zero-truth-energy behavior. candidate/control responses must match; a simulated absent source cannot silently activate synthetic research input.
4. **bounded resolution:** for candidate first/final shape states of outer zero in both noise cases, plus conditional real first/final states, reevaluate saved winner and nearest finite grid neighbors; tighten an existing bracket once to `xatol=1e-6,maxiter=80`. no invented endpoint bracket, new restart or propagated refit campaign. hold incoming priors fixed, preserve original candidates. all requested/native current-player mean movements must be `<=1e-4` of the reference rate; report working-interval movement and scale status. failures withhold dependent progression and open an issue, rather than trigger repeated tuning. at most six annual probes; independent equation checks still apply to every state.
5. **execution and closure:** freeze protocol/clean producer before new responses; complete only reachable stages, reconcile all denominators, independently audit sources/numerics/statistics/content and record resource costs. **delete all temporary tests, controllers and test-only dependencies after verification**; retain fixtures, scientific assessment commands and evidence. no lasting checks are selected in this slice; [07](07-lightweight-testing.md) remains separate. update the plan and issue records without changing frozen studies.

the content designer defines these figure contracts before generation, then reviews labels, units and claim scope:

| figure | what good content establishes |
|---|---|
| diagnosis | actual truth, mean fitted shape and bias on shared scales; volume/shape/cross contributions, bias versus variation and scale behavior. distinguish an outer mean from one realized fit |
| recovery | eight shape-error comparisons and four primary coverage cells, denominators/monte carlo intervals, nominal `.95` versus developmental `.90`; separate transition/null/stress statuses. wider intervals alone are not success |
| representation limits | actual truth, geometric projection and fitted pattern for broad/local/rough cases; gaussian outer zero, year five, fixed shared scales. include conditional real examples only if run, labeled research point associations with no refit intervals |

figures follow reached stages: after an early stop, show later claims as `not_run` with their reason; do not fabricate candidate maps or require empty success-shaped panels. the report must answer what pattern was recovered, against which baseline, at what resolution and under which assumptions. it must expose poor complete rates or entrant/local performance even if the narrower primary rule passes. no native-cell certainty, causal isolation, attractive-player selection, supported-ability label or automatic next experiment.

completion means a verified answer, including a diagnosis stop, scientific failure or inconclusiveness—not a required nomination. acceptance requires exact source/control reuse, one fixed representation, correct full-history fitting/projections, complete reachable budgets, independent numerical/statistical/content audits, clear scoped decisions and cleanup. no code or fits belong to this specification task.

material prices: broad pooling discards fine structure and can bias local/rough signals; `p` can imprint native texture and remains estimated-but-conditioned-on. refits vary fitted histories/scales, not sources, reference estimation, topology or cross-game dependence. two primary offensive patterns do not validate every player, defense shape or transition. positive directional gains do not establish practical map accuracy; a basic refit procedure can still fail under shrinkage/boundary behavior. native additive context/rates remain unconstrained. avoiding real refits leaves real-player uncertainty pending. no scientific result is a publication handoff.

method references: [wood on reduced-rank smoothing](https://doi.org/10.1111/1467-9868.00374), [marra and wood on smoothing bias and interval coverage](https://purehost.bath.ac.uk/ws/files/249372/MarraWoodCI.pdf), and [scipy's symmetric eigensolver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigh.html) inform the design, not its validation. [magnus 9](https://hockeyviz.com/txt/magnus9EV) motivates interpretable spatial effects and annual borrowing; this is our stated approximation, not a claim about a private implementation.
