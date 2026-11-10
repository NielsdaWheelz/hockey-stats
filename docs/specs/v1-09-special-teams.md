# v1-09 — special teams and common projections

full implementation handoff; [the plan](../plan.md#current-boundary) owns assignment. extends the shared positive spatial owner from [v1-08](v1-08-positive-attribution.md), using the [attribution equations](experimental-attribution.md#positive-volume-and-forty-mode-shape), [application contract](experimental-application.md) and [isolated-card crosswalk](../product-inventory.md#v1-field-crosswalk-and-card-acceptance). specification only: no implementation, fit, acquisition or activation is assigned here.

## outcome and boundary

deliver pp offense and pk defense for five chronological seasons `20212022`–`20252026`; publish the last three through the existing application. one special-teams family shares player/context coefficients across `5v4`, `5v3`, `4v3`, with separate state baselines. each physical interval supplies one advantaged-side observation. reciprocal `4v5`, `3v5`, `3v4` outputs describe the defending players in that same model, not three more fits.

scope: **fifteen fresh heads — volume, shape and quality × five seasons — and at most three final-season diagnostic continuations**, followed by exact-state/common-mixture projections, actual-context allocations, one combined exchange and an inactive candidate. a continuation is attempted once for each completed final baseline; absent/failed baselines receive a located `not_run` reason. no multistart, alternative recipe, bootstrap, execution refit/rescore, preparation rerun, download or new season. evaluating saved neutral origin values is permitted; rebuilding execution scores/panels is not. preserve accepted 5v5 values and their original limitations exactly.

**user decisions, 2026-11-09:** use general attacking/defending coach effects and seven clipped score main effects plus unknown; omit coach-by-score/shell and score-by-clock interactions from this recipe. retain those encoders for other recipes. new-head sensitivity is a disclosed diagnostic: a mathematically checked, solver-completed baseline may publish experimentally despite excessive or unassessed movement. incomplete baselines, invalid arithmetic, leakage, wrong populations and broken accounting still block affected output. this prospective policy changes no earlier verdict or v1-08 admission record.

the simpler context follows the published [magnus special-teams structure](https://hockeyviz.com/txt/magnus9ST). our positive likelihoods, forty-mode representation, annual priors and reference are independent choices. thinner specialty data justify shared effects; this may miss state-specific skill and late-game/coaching interactions. estimates describe underlying level across a season, not held-out forecasts, causal isolation or private-model parity.

v1-10 owns penalties/shootiness, v1-11 territory, v1-12 the common-workload ledger, v1-18 the complete analytical sheet. no shorthanded-offense or pp-defense attribution, 4v4/3v3, empty-net attribution, replacement total, calibrated interval or new dashboard. current scalar/detail/history/comparison/export journeys and all new map payloads belong here; full map-sheet rendering and structured head/adjustment detail remain v1-18.

## inputs and operating contract

real execution needs the hdd. detached documentation, source work and labeled fixtures do not. new expensive outputs use fresh directories under `/Volumes/Expansion/hockey-stats/runs/spatial-st-v1-09-<run>/`. preserve source evidence, expensive fits, failed records, the live build, port 3000 and active/previous databases. no colima/docker, fit mirror, runner, checkpoint engine or release manager.

pin these locators under `/Volumes/Expansion/hockey-stats`; the repository receipts establish their identities, not a new external validation in this specification:

| input | relative locator | sha256 |
|---|---|---|
| preparation | `prepared/evidence-v1-01-02/manifest.json` | `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c` |
| reported head coaches | `runs/coaches-v1-02-20261022-01/coaches-01/coaches.json` | `102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0` |
| corrected execution scores | `runs/execution-spatial-replacement-20261031-01/real/scores-selection.json` | `588376316a8b4d5311a1677bb3f1419f3754854f25dd2a28e09e3e8c000f9450` |
| accepted 5v5 state selection / basis lineage | `runs/execution-spatial-replacement-20261031-01/real/states-selection.json` | `7ac43cfa0bcf72b449bc9267b19f16eb5ac7d7bf396fd08d9a98200d94549f1c` |
| combined donor with corrected reference-xg prose | `runs/application-v1-17-20261108-01/results/manifest.json` | `38c1d8e105e244c5e45cf071b18bb98be10c78268ab2688a40f5bc3dca84c9b8` |

the [spatial composition receipt](../research/spatial-v1-08/receipts/real-spatial-composition-completion.json) binds the accepted states. the first ev basis donor is `real/spatial/20212022/manifest.json` in that replacement run, digest `3b7b51339b5ebb00a340a3f593347adf3a72ee137ad24739abd582b8290a5509`. its `basis_identity.array_sha256` is `4fa1d565e939dae706a7f3fa0d060b06b647602ba32d2850174b80c6267fa42b`. the [v1-17 correction receipt](../research/application-v1-17/receipts/real-metadata-correction.json) binds the combined successor and its correction evidence `a732f9885dab11c902f08bedf35366c01eb6b22150b9e64fe6f347c0df6d1bf4`. never regress to the old execution-only donor or undo corrected personal-reference-xg support wording. an explicitly selected compatible descendant, including v1-07 goalie output, is permitted only after exact inherited-family/identity checks. no newest-directory discovery.

the corrected score artifacts already contain all three exact physical panels. read them through the execution owner; do not infer missing analytical capability from its former 5v5-only accessor. v1-07 owns the shared exact-state/cached-panel repair. coordinate that small change before merging shared files; no dependency on successful goalie fits. one heavy fit at a time; coordinate large drive passes with its current owner. fixtures can progress independently once assigned.

## responsibilities and interfaces

| package/file owner | owned change; content counterpart |
|---|---|
| `spatial_design.py` | finite `ev`/`st` designs, one-direction masks, actual unit sizes, explicit state axes/offsets and compact designs; source designer owns role/support vocabulary |
| `spatial_rates.py` | shared positive objectives, priors, fitting, reference and projection/accounting algebra; numerical designer defines quantities, sign and interpretation |
| `spatial_state.py` | strict distinct st state/probe contracts, basis-only import and detached reads; no generic model registry |
| `execution_scores.py`, execution evaluator | existing saved exact-panel access and joint neutral origin values; coordinate v1-07's change, preserve old numerical output |
| `spatial_composition.py` | replace only pending specialty rows, preserve 5v5/non-spatial data; publication designer owns evidence, availability and reference copy |
| `analysis_cli.py` | thin closed-family dispatch and argument validation; no numerical logic |
| `analysis_publication.py`, `publication.py`, shared effect schemas/readers | v1-18’s exchange3/schema9 checks and existing mass transport; no second fitting/reference implementation |
| `app/src/web/{analysis-values,analysis-discovery,analysis-history,analysis-cohorts,client,explorer}.ts[x]`, routes and export owner | exact-state selection, shared detail/cohorts/history and exports; interaction designer owns clear state/role/mixture distinctions |

root integrates shared files; source, numerical and application owners have non-overlapping boundaries. independent reviewers challenge each boundary before real execution and final acceptance. share the existing objective, centering, sparse reduction, sixteen-subset allocation and native/display transport primitives. eliminate hardcoded five-player arithmetic where this family needs actual counts; do not fork a second spatial engine or change active ev semantics.

```text
hockey-stats-analysis fit --family spatial-st --prepared DIR --coaches FILE
  --valued ANNUAL_SCORE --season ID [--previous ST_STATE | --basis EV_STATE]
  --out NEWDIR
hockey-stats-analysis summarize --family spatial-st --results COMBINED_RESULTS
  --states ST_SELECTION --out NEWDIR
hockey-stats-analysis publish --observed FILE --results DIR --out NEWDIR

prepare_spatial(prepared, coaches, valued, season, *, family)
  -> SpatialDesign | SpecialTeamsDesign
fit_spatial(design, previous_state, output, *, basis_source=None, final_year=False)
  -> SpatialState
read_spatial_basis(accepted_ev_state) -> checked basis, identity
read_spatial_state(path, expected_purpose, *, expected_family) -> SpatialState
project_spatial(state, design) -> SpatialProjections
compose_special_teams(existing_results, state_selection, output)
  -> complete player_analysis_results exchange
```

preserve active ev commands and artifact identities. first st year requires `--basis` selecting the first accepted ev state from the pinned selection; later years require the immediately preceding completed st family and forbid another basis input. copy only its checked native basis, not ev coefficients/priors/targets. fixtures bind their own accepted basis and explicit consecutive annual subset. `--valued` binds exactly one annual score. selection is closed `{schema_version:1,purpose,prepared_sha256,states:[{season,path,sha256}]}`, five ordered years for real composition. reject duplicate/irrelevant flags, wrong family/year/purpose/bindings, future states and occupied destinations. `--product-admission` belongs to the historical ev contract and is rejected here; st diagnostic-use policy is already frozen prospectively.

the st `fit` command sets `final_year` for `20252026` in real preparation, and for the last declared fixture-preparation season in fixtures. that ordinary command attempts each completed final head's prescribed continuation once; it must not copy the current ev dispatch's fixture-only probe behavior. completed, checked baselines with exceeded/unassessed diagnostics yield a completed st artifact and successful command exit, accepted by st composition with disclosures. baseline/contract failure remains incomplete/nonzero. preserve ev dispatch and its historical admission semantics.

composition requires a null first predecessor and each later `previous` path/digest to equal the preceding selected state, not merely consecutive year labels. all selected states share purpose, preparation, coaching, st recipe and basis. each annual `valued` digest must equal that year's pinned corrected score selection and agree with inherited execution-method evidence. mixed valid chains/targets fail. the canonical v1-13 fixture already contains a computed synthetic 5v4 row: use an attributed fixture donor staged with pending specialty rows and preserve that original fixture; never weaken the real conflicting-result rejection to accommodate it.

## matched population and elapsed design

start with v1-01's `ordinary_attempt_support`; retain its exclusions unchanged. within retained maximal membership segments, require both goalies, supported ordinary play and exact physical strength `5v4|5v3|4v3`. identify the advantaged team once. keep every eligible zero-attempt child interval once, including genuine supported overtime. neither double time into reciprocal views nor halve time because only one direction is fitted.

classify an event's side before requesting a valued target. a proved shorthanded attempt is outside this response and does not create an added exclusion merely because its execution value is absent. an ambiguous side that could be advantaged, or an advantaged attempt missing essential identity/outcome/shooter/team/membership/origin/neutral value, excludes its assigned maximal segment's modeled counts and all child time. preserve base versus added exclusion unions. v1-01 may already have excluded a segment for a source contradiction involving either side; this consumer never restores it.

use the saved corroborated event assignment at boundaries, authoritative pre-event score/strength transition and amended start-eligibility rule. the score panel's attacking-oriented physical state must equal the assigned event's state. wrong score key/state/outcome bindings are contract failures, not ordinary missing-data exclusions. never borrow the following lineup, reset a boundary event early or require the event design to equal the elapsed design. retain excluded source locators, known lost seconds, advantaged attempts, ignored shorthanded attempts and unquantified gaps separately. inferred block origins remain mass distributions, never observed release points.

reuse [v1-08's fixed elapsed design](v1-08-positive-attribution.md#fixed-elapsed-design), with only these declared changes:

| feature | st contract |
|---|---|
| state | fixed order `5v4,5v3,4v3`; integer `state_time` / `state_event` arrays select offsets and state intercepts |
| players | shared attacking pp / defending pk coefficient axes; every identified seasonal roster skater has both roles; counts are `(5,4),(5,3),(4,3)` |
| coaches | one reported-head-coach base block per role plus existing missing-coach context; no score/shell blocks; attendance remains unproved |
| score | eight centered columns: clipped `-3..3` and unknown; no clock interaction or standalone ten-minute clock columns |
| retained context | home×period; per-member shift-start×age, rest, complete/partial workload means and fractions, supported strength transition; exact existing facts and missingness semantics |
| normalization | unit fractions divide by actual role size; complete/partial means divide by contributing members. no `.2`, five-player validator or hidden fifth neutral player |
| transforms | pooled matched physical st time, once; continuous available-member moments and disjoint missingness follow v1-08. no state-specific restandardization |

the existing ten-minute chunk boundaries may remain even though score×clock is inactive. exact duplicate volume designs may be collapsed by state plus all predictor values and summed hours. never invent event chains/shot types on zero-event time. raw complete/partial/unknown status survives transformed zeros. identity, ordering, side counts and state support are explicit design invariants.

## positive heads and annual history

use the canonical [three losses and positive offsets](experimental-attribution.md#positive-volume-and-forty-mode-shape) unchanged, evaluated with each row's state. fit one shared coefficient vector/matrix per head plus **three penalized state intercept blocks**, not a shared intercept plus a redundant full set. state block widths are `1`, `40`, `41` for volume, shape and quality; actor/context widths remain those same head widths. quality separates its scalar and forty spatial terms. penalties apply once to each shared coefficient, not once per state.

freeze offsets from this year's pooled st data and each state's retained counts/time, exactly as the appendix defines. save the 656-cell, forty-mode basis from the accepted ev artifact, verifying cell order, uniform orthonormality and digest. keep its exact arrays for every st year. the basis carries geometry only; no ev or research coefficients transfer. each head minimizes its summed likelihood plus proper prior with analytic gradients; targets/offsets/transforms remain fixed during a solve.

retain the declared entry **or** carry priors: scalar player sd `.25` / `.10*sqrt(gap)`, coach `.10` / `.05*sqrt(gap)`; vector precision multiplies the corresponding scalar precision by 40. context scalar precision 1 / shape 160; state scalar-intercept precision `.25` / shape 40. quality uses separate scalar/vector penalties. raw pp and pk history stays separate, head/subblock-specific and st-only. carry the last likelihood-supported raw coefficient, never the reporting center or a prior-only year. volume support is positive elapsed or event incidence; shape/quality support is positive origin weight, even for a zero quality target.

volume alone retains joint pp/pk×F/D age drift with ridge64 and dated `z(age)` from the existing owner. missing/changed position or age yields an explicit age-neutral transition. unsupported actors are profiled to their conditional means and contribute no invented age evidence. shape, quality and coach history remain age-neutral. conditional history ignores uncertainty in prior years and may lag a changing specialty role.

zero exposure in a state requires zero retained attempts there; orphan events cannot supply a denominator. that state's intercepts are at their zero prior means, offsets remain defined by the pooled smoothing rule, and its projection is marked state-extrapolated. positive state exposure with no attempts informs its volume intercept, while its shape/quality intercepts retain static zero means. shared player effects can still have current evidence from other st states. state intercepts have fresh static priors each year, not carried state effects. zero pooled exposure makes the family unavailable. positive pooled exposure with zero attempts permits volume only; shape/quality remain unavailable. constant quality targets are valid under proper penalties. a missing/failed required head withholds joint projections; preserve completed artifacts, report incomplete and stop the dependent annual chain without fallback carry or automatic rerun.

all complete native rates must be finite and strictly positive; `lambda_X<=lambda_A`, allowing finite sigmoid upper rounding. negative contrasts are valid. no clipping, replacement by absolute values or diagnostic endpoint promoted to baseline. retain objective components, iterations/evaluations, termination and gradient norms; solver success alone does not establish the requested gradient accuracy.

## references, mixtures and accounting

one annual common reference serves every player. compute each role's raw actor center with pooled **slot exposure**, `m_r=sum_i(seconds_i,r*beta_i,r)/sum_i(seconds_i,r)`. center coach roles by known-coach elapsed time; if none exists, use zero center and zero applicability, explicitly. these are reporting transforms only. each exact-state reference has centered context zero, neutral player/coach residuals zero, actual counts `n_att(s),n_def(s)` and the same pooled known-coach applicability per role. transfer player centers as `n_att(s)*m_att+n_def(s)*m_def`; transfer coach centers through their applicability, not an unconditional coefficient. apply this separately in every head/subblock and prove actual predictions unchanged.

this is a hypothetical centered **linear-predictor** reference, not the mean nonlinear prediction or each state's empirical context. shared context/coach applicability isolates state baseline/count differences and permits explicit extrapolation into a zero-time state. save all state reference vectors and their identity. insert one focal player in pp attack or pk defense jointly through volume, shape and quality; produce neutral/focal native rates, their signed difference, scalar sums and `100*difference/neutral`. pk positives mean more against; only v1-12 reverses the ledger sign.

with `H_s` retained physical hours, define `w_s=H_s/sum H`. use these identical weights for every player's pp projection and reciprocal pk projection. mix **native neutral/focal rates first**, then differences, sums and relative percentages; never average percentages, use role-slot hours or substitute a player's own usage. save all three weights, including zeros. a zero-time state's prior-based exact projection stays visible; missing required estimates never become zeros or cause silent renormalization. the eventual pp/pk contribution is `+(100/60)*delta_xg` / `-(100/60)*delta_xg`; this slice checks that consequence but does not populate the ledger.

actual-context explanation remains separate. per retained focal chunk, use its state reference, offsets and counts; partition deviations into self, `n_focal-1` teammates, `n_other` opponents and coaching/other context. evaluate all sixteen subsets jointly through the three heads, then average rates/allocations over focal elapsed time. common pp/pk **actual-context** summaries use that player's actual role-state hours, including the corresponding mixture of state-neutral baselines. they must not reuse the league-weighted reference baseline. zero focal role/state time gives `no_exposure` for this explanation even when a standardized estimate exists.

baseline + four allocations + floating residual = factual prediction per native cell and scalar, tolerance `1e-10*(1+abs(factual)+sum(abs(terms)))`; residual is never credit. report the largest absolute terms, cancellation and probe movement as diagnostic values. exact closure does not make extreme cancelling terms reliable attribution. store the actual-state weights beside these artifact summaries; public standardized `state_weights` retain their different league-reference meaning.

## artifacts and strict composition

keep the active ev recipe/kind/schema exact. add a finite st definition/recipe identity and schema1 `kind=spatial_st_state` in the existing artifact owner; strict kind dispatch is not an old-format fallback. use a separate `SpecialTeamsDesign` record for state-axis additions: the current ev reader derives its closed fields from `SpatialDesign`, so widening that record would invalidate saved evidence. share validation/math without relaxing old invariants. no historical migration.

| artifact | required additions to the existing spatial contract |
|---|---|
| manifest | `family=st`, purpose/year, exact recipe/design/implementation, prepared/coaches/annual-score/prior/basis bindings; all three head statuses; ordered contained member identities/resources |
| design + arrays | three-state axis, `state_time/state_event` integer indexes, actual role counts, one-direction time/event keys, existing sparse actors/dense contexts, ragged origins/targets; per-state offsets and pooled transforms; definition/digest |
| coverage | year/game/state physical hours, role-slot hours, attempts/origin/neutral mass, base/added masks and reason unions, ignored sh events, gaps, missing context and zero-state evidence |
| heads / coefficient support | raw coefficients, shared axes, three intercept blocks, priors/ledgers/age, centers/applicability, objectives/solver costs; existing head/role support rows plus exact-state time/event/origin breakdown whose sums reconcile pooled support |
| reference / projections | state reference vectors, annual league `state_weights`, all roster roles/exact/common neutral/focal/difference arrays and scalar closures; actual-context weights/support separately; unavailable estimates with reasons, never NaN |
| probes | baseline identities, frozen context keys, three single-head continuations and joint saved-variant comparison; status `within_budget|exceeded|unassessed`, located maxima and reasons, no history promotion |

v1-18 fixes the saved support fields through the [spatial-evidence contract](experimental-application.md#spatial-evidence-projection): `coverage.state_support` holds all three attacker-oriented states with physical/directed seconds, attempts, origin weight and baseline information; every available head/role support row has a three-state `state_support` breakdown; unavailable heads retain null; every available actual-context adjustment has `states:[{state,seconds,weight}]`. retain zero shares and distinguish pooled coefficient support from selected-state time. these records supply both final schema9 evidence and detached inspections; they require no additional fit.

reuse finite json, non-object numpy arrays, exclusive writers and hash helpers. validate contained shapes/order/uniqueness, state/membership/exposure identity, probabilities, raw-history chronology and projection/accounting closure. detached state reads use only contained members; provenance paths do not require reopening source/predecessors. first-year basis import checks the pinned manifest and lazily reads only `design.npz`'s `basis`: float64 `(656,40)`, finite, correct cell order/orthonormality and exact `ordered_array_digest({'basis':B})`. preserve the full saved basis identity; its other digest also binds original eigenvalue/grid construction and is not recomputed from B alone. record the archive's declared digest as provenance, without claiming a fresh whole-archive hash. this avoids reading the roughly 8 gb archive and 1.4 gb design json merely to use its small basis. no repeated full preparation scans inside optimizer/projection loops.

publication coordination: v1-18 owns the shared schema9/exchange3 cutover and one temporary conversion of the pinned combined schema2 donor. this slice can develop/fill numerical artifacts independently, then compose against the explicitly accepted compatible schema3 successor. preserve its evidence/method correction and any compatible goalie descendant; do not implement a competing converter, dual-version reader or automatic latest-artifact selection. if shared delivery order changes, the integrator reconciles these same contracts before final composition; no refit follows.

composition changes only st-owned keys. preserve every 5v5 scalar/map/adjustment row, method id and original warning exactly; do not reload ev states to recalculate them. preserve every non-spatial member byte-for-byte where unchanged and all inherited catalogs/identities, including corrected reference-xg and any accepted goalie output. replace only currently pending st rows; reject a precomputed conflicting specialty result. mixed spatial files are streamed rowwise. add new methods/references and verify no non-owned semantic difference. v1-08's post-result use decision remains attached to its own rows; it grants nothing to st.

for every published skater-season, fill the existing pending specialty keys:

- **8 scalar rows:** pp, pk and six exact states. retain all sixteen schema8 fields; the eight role-applicable values are computed, the opposite role's fields are `not_applicable`.
- **32 maps:** eight selectors × applicable role × attempts/xg × complete/effect. retain 656 native and existing 668 display-cell meanings and mass transport. neutral native arrays remain in the state; api scalar neutral rates close to them.
- **16 adjustment rows:** the applicable role × attempts/xg for each selector, with the existing seven accounting quantities. no-role/time rows have their explicit reasons.

with preserved 5v5 rows, the totals are 9 scalar, 40 map and 20 adjustment keys per published skater-season. this is the existing matrix, not a schema expansion.

exact-state rows use their one state with weight 1; pp/pk rows use the three reciprocal league weights. scalar/map readers independently reject wrong roles, negative/duplicate weights or weights whose sum differs from one, mismatched reciprocal weights, missing required states and common-versus-exact weighted-sum failures. ratio fields close after mixing; do not apply an additive-map sum to a percent. target v1-18’s exchange3/schema9, retaining existing scalar/map bodies and endpoints; populate its finite spatial-evidence table from the already-required saved records. v1-18 owns the shared exact-state selectors/client/history plumbing before this final integration; this slice supplies and verifies their real specialty quantities.

## support and application content

public `Support.included_seconds` is actual retained focal time in the selected role/state; pp/pk use that role's union across three states. `events` counts distinct advantaged attempts while the focal player is on ice in that population, not shorthanded shots or a weighted synthetic count. `eligible_weight` is null. excluded known seconds are the matching physical-time union; reason counts retain their declared game/event meaning, never summed overlapping losses.

`current_season_information` means any contributing focal role/head has likelihood information **anywhere in this shared st family**, never in the opposite role; `prior_only` means none has it. actual state participation and pooled coefficient information are different. a zero-minute 5v3 specialist projection may use current 5v4 evidence; a zero-time pp role may be purely prior-based. save exact-state/head information and anchor years in bound strict evidence. pooled actor information also does not establish support for a rare state's baseline; retain annual state-level time/event/mass counts and extrapolation flags. aggregate summary support does not claim every term is currently informed; schema9’s separate evidence retains the full role/head/state distinctions. reconcile prepared versus published roster identities explicitly; required published people get a checked projection or a specific unavailable reason.

`prior_seasons` is the union from contributing heads of this same focal role; `historical_borrowing` in `inferred_inputs` follows that role's actual carry, never the opposite role's history. exact-state methods identify any zero-exposure state in their existing findings/limitations; selected detail and exports display that extrapolation caveat. v1-18’s finite evidence payload carries these records; an artifact-only warning is insufficient.

| surface / content owner | definition of good |
|---|---|
| selection/discovery | reuse v1-18’s shared spatial-table/client/history extension to all nine strengths and its 24 exact-state role-valid difference/relative-percent selectors; no invented pk offense. use `family=spatial&strength=...`, not a larger overview payload. default defensive sorting for all reciprocal pk states |
| selected detail | say “experimental pp offense” / “pk defense” / exact state; show difference, complete, neutral, relative percent, league state weights, actual qualifying minutes, pooled-information caveat and linked evidence. no hardcoded 5v5 support text |
| cohorts | same F/D defaults; 50 actual included minutes in the selected st role/state, adjustable viewing rule, not reliability. positive qualifying time remains required even at cutoff 0. raw estimates remain below cutoff; numeric percentile withheld. higher against percentile means more against, never silently better |
| history/comparison | each year's own state weights, role support, method and limitations; no line across missing estimates, no mixing publication identities. both selected players use the same annual reference; their qualifying evidence remains distinct |
| maps/api | reciprocal pk uses the existing conceded-attempt attacking frame, not a second reflection or favorable-sign inversion. every native/display integral closes to its own quantity. paired requests checked; no new full-sheet renderer |
| exports | extend the ui-only spatial detail with existing `state_weights` and reference identity; detail/csv preserve exact weights, four values, reasons, support and evidence. selected-field png carries state, role, raw sign, reference-mixture meaning and experimental/optimizer caveat; full receipt lists remain in csv/detail |

use `analysis-values.ts` as the sole selector owner, including the missing spatial-family league branch and exact-state input type. coordinate `client.ts` family requests, `explorer.ts` URL parsing, league controls/revalidation, shared history/export and strength-aware copy. complete/neutral guides are not additional ranked skills. retain comparative/value defaults and observed views; the full card's pending common-workload components stay pending. no second percentile, quantity derivation or generic chart/metric framework.

## diagnostic resolution and measured cost

baseline [L-BFGS-B](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html): one conditional-prior start, history 10, `maxiter=10000,ftol=1e-15,gtol=1e-6`; retain native line-search/function limits and report them. after freezing all baseline history, continue each completed final head once with `ftol=1e-16,gtol=1e-7`, otherwise identical objective/offsets/transforms/prior. save separate-head and joint-three-head projection comparisons; joint comparison uses saved probes, not another fit. failed/missing continuation gives `unassessed`, not zero movement or passed precision. if one probe is unavailable, the joint variant is unassessed; retain valid single-head comparisons without silently substituting a baseline into the joint variant.

recompute conditional prior-only values and reporting centers for each variant. compare every final-roster exact/common neutral/focal/contrast scalar and native map; flag exact-state shape `p_c` / quality `Q_c` movement above `1e-5`, scalar movement above `1e-4` per hour, native-map L1 movement above `1e-4` per hour, or either prospective 100-minute pp/pk term movement above `1e-3` goals. probability checks cover neutral/focal and frozen coalition contexts; common-mixture comparisons concern rates/maps, not an invented time-weighted mean of `p_c` or `Q_c`. these are diagnostic flags, not calibrated accuracy or publication gates. original 5v5 budgets/verdicts stay unchanged. per-state and mixed results both matter; averaging cannot hide sensitivity.

before continuations, freeze at most 256 actual contexts: first key for each physical state×focal role, then supported boundary goal, missing optional context, entrant, returner, traded player and sparse role; union and fill lexicographically by `(game_id,segment_index,chunk_index,event_source_index,role,player_id)`, null before integers. inspect priors by `(role,player_id)`, including defense, not only the attacking role. record absent categories. compare all sixteen coalition rates/allocations on this fixed set. whole-roster standardized projections are not sampled. method/detail/export must say whether sensitivity was within flags, exceeded or unassessed, and that remaining optimizer accuracy is unknown. earlier annual states say their sensitivity was not assessed; final-year results are not retrospective passes. scientific calibration, prior sensitivity and generated-target uncertainty remain separate limitations.

retain in-sample state-stratified volume residuals, location residuals/cross-entropy, neutral-quality calibration, role/prior-only counts, extreme projections and allocation cancellation. no new scientific threshold. measure the first complete annual triple before estimating remaining cost. compress only identical volume rows; event batches ≤4096 form batch×40 and batch×656 arrays, never event×cell×feature. stream exact all-player coalitions; no dropping modes/players/time to meet a guessed deadline. 64 gb operating envelope, one heavy solve, external-only expensive output.

record design/read bytes, state dimensions, each solve/probe, projection/coalition costs, peak memory, exchange/candidate size, build/strict-reader time and selected api/browser latency. the accepted v1-17 candidate is about 13.36 gb; build 6,555 seconds and strict startup 474 seconds are historical costs, not st forecasts. extra state maps materially increase storage and strict validation work. fix measured bottlenecks at their owning layer; no schema/cache/service redesign is assigned merely by those costs.

## acceptance and final handoff

write temporary source-to-api/live checks for target behavior, demonstrate red, implement, get green, refactor shared owners, rerun affected checks, then delete campaign-only tests/controllers/dependencies. retain useful source fixtures, checked expected facts and compact receipts. no new permanent test suite is selected here. newly distinct broken original games follow the existing complete-bundle fixture policy.

| boundary | required independent evidence |
|---|---|
| support | all three strengths, home/away advantage, zero-event time, sh event ignored versus ambiguous pp exclusion, both-goalie rule, source/boundary assignment, whole-segment masks; slot-hours close to `5H54+5H53+4H43` attacking and `4H54+3H53+3H43` defending; 4v3 fractions sum to one per actual unit |
| mathematics | hand-computed small losses/gradients for each state/head, positive smoothed empty state, proper priors, no duplicated penalties, all-zero/all-one quality; forty-mode basis identity and no ev coefficient import |
| history/reference | consecutive years, entry/carry/absence/role/age cases, prior-only anchors unchanged, raw-versus-centered equivalence, actual count transfers and unknown coach applicability; independently check neutral/focal three-head substitution |
| projection | exact/shared weights, reciprocal mapping, ratio-after-mix, zero-weight state, rare/no-role time, all native/scalar/display sums; independently enumerate 24 group orders against sixteen-subset accounting and verify focal-time mixture baselines |
| preservation/composition | all old 5v5 rows/methods and non-owned facts/outputs exact; v1-17 metadata correction and any compatible goalie family survive; all required keys/invalid roles/weights and corrupted identities rejected by python and effect readers |
| real execution | all 15 baseline heads complete, three diagnostics attempted/reasoned and all variant disclosures truthful; five-year state selection and three-year real exchange/candidate reconcile. a failed required baseline leaves real scope incomplete, never a synthetic substitute |
| application | enumerate 40 finite scalar selectors (32 specialty, 8 preserved 5v5) through accessor/transport checks, separately from 40 map combinations. real new pp/pk and exact-state discovery/profile/detail/cohort/history/comparison, sparse/prior-only/traded/absent-year cases, new maps/paired api, actual csv/png downloads and narrow/native 200% layouts; offline candidate browsing and isolated rollback. preserved 5v5 live checks receive only their explicitly recorded scope |
| content/resources | each content owner checks unit/sign/reference/support and receipts against artifacts; source, math, systems and content reviewers resolve findings. record actual costs and protected serving/input identities; no activation |

fixture acceptance establishes software behavior, not real source coverage, capacity or completed capability. v1-08's deferred real browser checks remain deferred unless explicitly exercised and recorded here; a new st check does not inherit or silently close them. browser access failure leaves those checks incomplete, not passed by api/export-source inspection.

write `docs/research/spatial-st-v1-09/verification.md` with exact inputs/code/recipes/references, commands, support reconciliation, fifteen heads, diagnostic outcomes, preservation, independent findings, costs and cleanup. record computational completion, experimental integration, activation and scientific support separately. concrete unresolved defects belong in `docs/issues/`; v1-10/11/12/18 retain their planned work. final state is usable specialty estimates and reference fields through the current app, with honest limitations, no silent total-value substitution and no claimed complete-card or scientific admission.
