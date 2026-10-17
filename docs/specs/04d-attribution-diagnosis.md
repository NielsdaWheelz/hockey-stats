# pr04d — diagnose attribution signal loss

status: **full specification; implementation and execution unassigned.** the user selected known-truth diagnosis only; real-deployment identification remains separate. [the plan](../plan.md) owns assignment. preserve [04c's `mean_recovery_failed`](../research/attribution-04c/decision.md), every frozen protocol and all original artifacts.

## question and boundary

why do injected broad player patterns remain strongly attenuated: unavailable deployment information, finite observation precision, shared scale selection, or annual inheritance?

deliver a reconciled explanation of the existing experiment and at most one recommended next research question. several mechanisms may coexist; an unresolved diagnosis is valid. no candidate selection, new fitted model, uncertainty campaign, real-player inference or publication follows.

fixed scope: 04c's five synthetic years, two noise cases, 400 saved outer histories per case, graph-40ft and native-04b representations, original truth, references, context and prior policy. retain broad shape as the primary question; volume, complete-rate positivity, source robustness and chance valuation remain separate. [05a](05a-observed-website.md) is independent.

non-goals: new draws, noiseless empirical-bayes fitting, variance optimization/refinement, a different grid/basis, prior replacement, feature activation, historical acquisition, real-data identification/fitting, bootstrap or model admission. all numerical work below is diagnostic evaluation at existing states or fixed values, not another fitting campaign.

## evidence and finite budget

start from the checked-in [04c result](../research/attribution-04c/result.json), sha256 `a87d04c30205eb707b9dbf6ee3fd83f44da73617e12d674a445c228d65c9e747`. follow its bound manifests under `/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/`:

| input | sha256 |
|---|---|
| `prepared/prepared.json` | `59261bd10f874bb0d19146e7f22948a9a6b2dac511e00d73d4842dca8529f724` |
| `means/means.json` | `88a8d36fc492a4c891c3c8471b83be62976245aac93cf82b128f392485d30f48` |
| `prepared/design.npz` | `d173ca19ee4b6aef94fd3f7b6397cd01028d979c731a368a399825515c7c4dcc` |
| `prepared/basis.npz` | `67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc` |

the drive/originals were available during specification. resolve exact identities, not a newer convenient run. no raw captures or real ledgers are needed. saved outer archives contain both annual chains, means, full covariances, priors, context and scale curves; responses and sufficient statistics were not saved. decode saved truth/design arrays rather than reconstructing a new truth definition.

budget:

- stream/hash each of the 800 outer manifests/archives once; reconcile all 8,000 annual states and 04c's primary reported summaries. no copied historical archives.
- reconstruct likelihood information once per annual design: five designs, before and after the existing context adjustment.
- trace both representations through all saved paths with their selected covariance histories held fixed.
- evaluate exactly the existing 17 first-year variance points in each representation: 34 analytic states, no minimization or refinement.
- regenerate only `(case,outer)=(gaussian,0),(game_pace,0)`, five years each, using their original seeds. this is response/statistic and fixed-state numerical replay, not new evidence or scale selection. maximum ten response arrays, processed one year at a time.

freeze the 04d protocol, selections and clean producer before executing these diagnostics. research outputs use one new external directory under `/Volumes/Expansion/hockey-stats/runs/`; ordinary i/o errors and manual reruns suffice. no local fit mirror, runner or checkpoint system. use one numerical thread; streaming serial execution is sufficient. record actual time, memory and bytes read; no runtime promise.

## requests and units

reuse the saved grid, positive native shares `p`, graph basis `B`, `R=diag(p)B`, twelve-region operator `W`, annual `r=40`, exposure centering and ordered player ids. geometry/reference identity is exact. distinguish current players from absent carried rows; do not invent absent-season truth.

freeze 04d request identities with the existing coefficient/functionals and saved annual truth arrays. 04c's primary requests cover years 1/5; the additional years below are new projections, not new truths or purported saved 04c requests:

| requests | years (one-based) |
|---|---|
| primary offense radial `3−4`, lateral `10−11` | 1–5 |
| offense local `18−19`, rough `20−21` stresses | 1, 5 |
| entrant 32 offense, entrant 33 defense | 3–5 |
| returner 8 offense | 2, 4, 5; mark year 3 absent |
| paired offense `26−31`, `26+31` | 1–5 |

individual/sum requests remain relative to the original exposure-weighted reference. outputs are native/12-region shape vectors and saved radial/lateral scalar functionals. retain per-path regional/scalar values and aggregate native maps; full native example maps use outer zero only. no duplicated full map history or 5% scalar meaningful-band classification for shape.

for any regional prediction `z` and actual truth `z*`, report squared error, normalized squared error `||z-z*||²/||z*||²`, and truth alignment `z'z*/||z*||²`. zero prediction has normalized error one. when truth energy is zero, retain absolute error and mark ratios unavailable. alignment may be negative or exceed one: never clip it or call it a fraction recovered. rates use attempts/60 team minutes; squared errors use their square.

## 1. representation and likelihood information

geometric oracle: for the actual native shape row `h`, compute `h_projected=(hB)R'`. compare actual and projected truth in native and regional coordinates. this projection uses the model's weighted geometry; it need not minimize regional error. it establishes representability only, not achieved recovery or estimability.

rebuild `X`, exposure `e=seconds/3600` and context stratum means from the saved rows. let `Xc` be the original exposure-residualized design:

```text
H_raw = r X' diag(e) X
H     = r Xc' diag(e) Xc
P     = blockdiag(I - 1u', I - 1u')
```

use existing grouped/reference residualization; independently reconcile the direct row calculation. embed current-player matrices in each saved all-seen order with zero rows/columns for absent players. `H_raw` treats context as known: it is an oracle comparison, not permission to remove context from the model.

report rank, null directions and contrast information separately from exposure-centering constraints. never invert the saved centered posterior to infer `H`. for request vector `c`, analyze `d=P'c`, not an uncentered individual coefficient. use a symmetric eigendecomposition, `tau=100*n*eps*lambda_max` (`n=H.shape[0]`), and the corresponding pseudoinverse `H+`. negative eigenvalues below `-tau` are numerical failures. report the null projection `||(I-H+H)d||/||d||`; a value above `1e-8` gives `not_estimable`. a zero functional is `zero_functional`, not an identified player. verify rank and request status at `tau/10` and `10*tau`; unstable cases are `numerically_unresolved`, not evidence about hockey.

for estimable requests only, give the fixed-design gaussian likelihood-only variance:

```text
S_native = diag(p) - p p'
S_graph  = R R'
variance(c,v) = r² (d' H+ d) (v' S_representation v)
regional_total_variance = r² (d' H+ d) trace(W' S_representation W)
```

these are precision diagnostics under the working gaussian observation law, not uncertainty for adaptive fits or the game-pace generator. graph precision concerns its represented component; omitted truth bias remains visible. report scale relative to actual truth without inventing an adequacy cutoff. no five-year sum of `H` that silently assumes constant player effects, no finite minimum-norm estimate for a nonestimable contrast, and no inference that a paired sum identifies either individual.

## 2. frozen-path signal transmission

for every saved state, recover the proper-prior update using the existing factorization, with `V0=shape.prior_covariance`:

```text
V = (V0^(-1) + H)^(-1)               # notation only; use existing cholesky solves
V_saved = P V P'
K = V_saved H
theta* = truth_shape B              # graph; native uses truth_shape
Q = H theta*
F_0 = 0
incoming_t = embed(F_(t-1))          # same entrant-zero / carried-row policy
carry_t = (P - K) incoming_t
current_t = V_saved Q
F_t = carry_t + current_t
```

construct `Q` on current rows as `H_current theta*_current`, then embed that score into all-seen order. zero padding is a computational embedding, never absent-season truth. the identity uses `H P=H` and `P'Q=Q`; verify them and the saved covariance. save compact request/vector projections, not another full covariance archive. graph outputs return to native units through `R'`; native outputs already have native width. show all five years, selected entry/innovation scales, endpoint/inherited flags, and `L0' H L0` eigenvalues with transfer values `lambda/(1+lambda)` for `L0 L0'=V0`. those modes are prior-standardized directions, not individual-player gains.

also compute the one-step mean-response value with the **actual saved incoming mean** in place of `incoming_t`. this distinguishes the saved incoming state from the recursively noise-removed path while holding its covariance/scale path fixed. report signed carry/current contributions, incoming-to-updated discrepancy, and actual fitted value minus `F_t`; reconcile the sum exactly on the selected replay cases. these are conditional computational contrasts, not independent sources of error or a percentage-of-blame waterfall.

the selected scales depend on the noisy responses. `F_t` is therefore a **frozen-path mean-response intervention**, NOT `E[estimate | selected scales]`, the average fitted estimator, or evidence that prior borrowing is wrong. the actual-minus-`F_t` remainder need not average to zero. retain empirical means and 5/50/95% quantiles across the original 400 paths per case, labeled distributions of diagnostics, not confidence intervals. never pool years/cases as independent replicates.

## 3. first-year scale pressure, without fitting

first-year incoming means are zero and `V0=aI`; this permits an exact gaussian expectation at each fixed variance. use only `a=10^k`, `k=-8,-7.5,...,0`, independently of observed winners. for graph `q=40`, native `q=655`:

```text
V_a = (a^(-1)I + H)^(-1)
S_signal = (H theta*)(H theta*)'                   # graph
S_signal = ((H truth_shape)/p)(H truth_shape)'     # native
J_expected(a) = q logdet(I+aH)
                - trace(V_a S_signal) - q trace(V_a H)
```

reuse the scale-objective owner, exposing its determinant, signal and noise contractions. the `qH` noise contribution is required: fitting deterministic mean responses would omit it and ask a different question. native response energy is an `a`-independent constant. compare **differences from `a=1e-8` within each representation** with paired differences in all 400 saved gaussian first-year coarse curves; graph/native objective levels are not comparable. report their empirical mean and monte carlo standard error; this is not an equivalence test. later priors are response-dependent, so do not apply this first-year expectation there. game-pace curves may be displayed separately as observations, never as matched gaussian expectations. this slice does not establish game-pace sampling precision or fully explain its comparative failure; retain that limitation if mechanisms remain unresolved.

on the SAME 34 states, compute primary first-year expected regional squared error under the gaussian generator:

```text
z_native(a) = r c' P V_a H truth_shape W
z_graph(a)  = r c' P V_a H (truth_shape B) R' W
z_true     = r c' truth_shape W
expected_error = ||z_representation(a) - z_true||² +
r² (d' V_a H V_a d) trace(W' S_representation W)
```

graph bias includes omitted shape. report both primary contrasts, the entire fixed curve and determinant/signal/noise parts. a truth-informed low-error variance is an oracle diagnostic, not a deployable choice. disagreement between global marginal-likelihood preference and contrast risk can motivate a pooling question; it does not prove a bug, identify the correct prior, or authorize selecting another variance. do not widen the grid, optimize risk or choose a preferred answer from a new threshold.

## owners, interfaces and artifacts

`frozen evidence → validated design/states → information and transmission → fixed-grid diagnostics → explanation`.

| owner / file | contract |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | load fixed synthetic design/reference arrays; reconstruct grouped information with existing residualization. preserve exact player, context, exposure and truth meanings |
| `analysis/src/hockey_stats/attribution.py` | named embedded schema-3 state decoder; shared fixed-prior update/centering and objective contractions. expose narrow diagnostic results from existing algebra; no second posterior, scale selector or automatic representation inference |
| `analysis/src/hockey_stats/attribution_simulation.py` | share the existing gaussian/game-pace response mechanism only as needed for exact selected replay; caller owns old seeds/design/truth. no new generator |
| `analysis/src/hockey_stats/artifacts.py` | reuse finite json, explicit references and exclusive output; move ordered-array digest here only if now reused |
| `analysis/research/attribution_information.py` | 04d requests, rank convention, finite budget, contrasts, report and figure policy |
| `docs/research/attribution-04d/` | implementation-time protocol/result/decision/verification and two figures; no fabricated evidence files during specification |

required numerical interface responsibilities: `fixed_shape_update(H, prior_mean, prior_covariance, score, u)` returns centered mean/covariance, gain and equation residuals; `shape_objective_terms(...)` exposes existing determinant/contraction arithmetic, including response rank/metric explicitly. exact signatures may use existing typed states, but the study cannot copy these equations into a parallel fitter. the embedded reader validates saved block shapes, representation, basis, source/model identity, prior chronology and row order. hash/load one outer once, decode ten states. synthetic embedded and recorded standalone artifacts remain explicitly named readers, with no fallback or migration.

use saved truth arrays. do not import historical study controllers; move only reused mechanisms to their existing package owner and adapt the affected old caller, verifying its preserved arithmetic. no unrelated cleanup, protocol migration, generic diagnostics platform or new dependency.

two manual commands suffice:

```text
diagnose --baseline-result <file> --protocol <file> --out <new-directory>
assess --diagnosis <file> --out <new-directory>
```

`diagnose` validates the frozen protocol and performs the complete finite budget, including selected replay. `assess` reads only its outputs; it never fits or regenerates data. freeze the protocol using a small study-local function, existing artifact helpers and an exact spec snapshot; no separate orchestration tool.

schema `3`, kinds `attribution_information_protocol|attribution_information_diagnosis|attribution_information_result`, explicit `purpose:research|fixture_exercise`. common fields: new diagnostic producer, original model producer, consumed `{path,sha256}` refs, spec identity, source kind, units, ordered array shapes and resources. downstream outputs bind the protocol; the protocol never hashes itself. old artifacts remain unchanged. research requires a clean identified producer; reduced detached fixtures must say `fixture_exercise` and cannot satisfy research acceptance.

protocol owns exact requests, representations, case/outer/year ids, grid, rank/tolerance policy and budget. diagnosis owns validated input references, completeness counts, geometry/information tables, compact frozen-path projections, scale/risk curves and reconciliation receipts. result owns:

```text
execution_status: complete | incomplete
findings: [{mechanism, evidence_refs, contrary_evidence, scope, limitations}]
unresolved: [...]
recommended_next_question: {question, evidence_refs, discriminating_check} | null
nomination: null
admission: not_admitted
handoff: null
```

each metric row identifies `(representation,case,outer,year,request,probe)` as applicable; units, supplied oracle information, fixed/changed quantities and reference/truth identity accompany its value. statuses distinguish `available`, `not_estimable`, `zero_functional`, `numerically_unresolved`, `not_assessed` and `incomplete`; no missing value becomes zero or nonfinite json. retain only compact new arrays/receipts, not duplicate source archives or full generated responses.

## decision, content and acceptance

freeze these interpretation rules; do not force a single culprit:

| evidence | permissible next question / limitation |
|---|---|
| geometric residual in the reported functional | quantify its size against actual truth and fitted error; projected truth cannot replace actual truth |
| null component or likelihood variance relative to truth | report nonidentification or the precision cost under the stated design/law; a stronger prior does not create observation evidence |
| estimable signal but weak frozen-path transmission | report suppression at the selected prior scales; neither this nor low variance alone establishes inappropriate shrinkage |
| global criterion and primary oracle risk prefer different parts of the existing grid | investigate pooling/objective alignment; no automatic new penalty, variance family or chosen grid point |
| signed annual carry impedes or supports the target | identify when/how under the frozen path; no blanket judgment on historical borrowing or unconditional temporal risk |
| incomplete reconciliation or numerical instability | stop affected interpretation, record the responsible issue; this is execution failure, not scientific rejection |

complete diagnosis may have mixed or unresolved findings. recommend at most one discriminating next question, with contrary evidence and what would distinguish alternatives. no automatic 04e or model adoption; the user controls progression.

the content designer defines and reviews two figures before generation: **representation/information** shows actual versus projected broad/local/rough truth with shared units/scales and contrast-specific identification/precision; **transmission/scale pressure** shows saved fits versus labeled frozen-path diagnostics through five years, transition/null controls and the first-year criterion/risk curves. selected single-path examples are always outer zero; aggregate panels use all 400 paths per case. never call a synthetic contrast an nhl player, a diagnostic quantile a confidence interval, or a prior-supplied allocation recovered evidence. the short decision explains what was established, what remains unknown and why its one next question is justified.

non-overlapping implementation boundaries, each independently reviewed before continuation:

1. **evidence owner:** strict embedded decoding and exact frozen design/response/statistic replay. missing/corrupt identities, duplicate outers or changed order fail explicitly. all 800 paths remain in accounting; no replacements or denominator reduction.
2. **numerical owner:** independently assembled small gaussian systems verify context residualization, centering, null handling, coefficient/native projections, fixed-path chronology and the three objective terms. check coupled player covariance, entrants, absence/return, exact duplicate difference/sum, zero-truth energy and outside-basis truth. reproduce every saved shape covariance and selected replay posterior/context; equation/replay relative tolerance `1e-8`, identities/array order exact. preserve the triangular-factor regression. use the existing variance grid/search records; no new resolution campaign.
3. **study/content owner:** temporary end-to-end red → green → refactor → green through detached fixture, source/numerical failure and complete diagnosis/report. independently recompute selected risk/geometry calculations and first-year objective differences using direct tiny-system gaussian moments; assess rank stability once as specified. verify 04c summaries without recomputing its bootstrap. render both figures and inspect labels, bounds, unavailable states and evidence links.
4. **closure:** execute the fixed research budget only after assignment; source, numerical, statistical and content reviewers reconcile receipts and conclusions. delete temporary tests/controllers/test-only dependencies after verification; retain useful fixtures and scientific assessment commands. no lasting regression suite is selected here. update plan/issues without editing completed studies.

completion requires the declared accounting, reconciled algebra, truthful report and independent review—not a recovered model. about 5.3 gib of original archives/manifests must be read; no expensive fits are replaced. accepted limits: known-truth results do not identify real players; gaussian precision/risk does not validate game-pace uncertainty; fixed-path interventions omit adaptive-selection uncertainty; global pooling may rationally sacrifice sparse contrasts; conditional reference shares and additive-rate limitations persist. numerical tolerances are not scientific accuracy margins.

method context: [magnus 9](https://hockeyviz.com/txt/magnus9EV) distinguishes current evidence, historical priors and structural pooling; it does not specify this diagnostic or reveal a private implementation. [bayesian workflow](https://arxiv.org/abs/2011.01808) motivates checking computation and model behavior separately. [symmetric pseudoinverse documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.pinvh.html) informs numerical rank handling, not scientific identifiability.
