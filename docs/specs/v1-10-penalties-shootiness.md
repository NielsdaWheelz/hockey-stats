# v1-10 — penalties and shootiness

full implementation handoff; [the plan](../plan.md#current-boundary) owns assignment. implements the [penalty](experimental-attribution.md#penalties) and [shootiness](experimental-attribution.md#shootiness) estimands, through the existing [application](experimental-application.md) and [card inventory](../product-inventory.md#v1-field-crosswalk-and-card-acceptance). this specification assigns no execution or activation.

## outcome and boundary

deliver ordinary-minor drawing/taking rate differences and their neutral opportunity values, plus conditional share of team attempts in seven strengths. fit `20212022`–`20252026` chronologically; publish the last three seasons. **ten new annual heads: one penalty intensity and one shooter-choice head per year; two final-season diagnostic continuations.** reduction, projection and publication add work but no fitted head. retain actual results even when scientifically weak.

**user decision, 2026-11-14:** tighter solves are disclosed diagnostics. mathematically checked, solver-completed baselines may publish experimentally with excessive or unassessed sensitivity and unknown optimizer accuracy. failed baseline solves, invalid arithmetic, leakage, wrong exposure and broken accounting still withhold affected output. neither final-year checks nor software completion establish earlier-year accuracy, calibrated uncertainty or ability admission.

the penalty model concerns on-ice team responsibility for non-offsetting ordinary two-minute minors, not responsibility assigned entirely to the named offender. the [published penalty model](https://hockeyviz.com/txt/magnus7P) motivates that question and repeat/switch context; our positive likelihood, richer context and annual priors are independent. shootiness conditions on a team attempt already occurring. our seasonal multinomial differs from the published online method retained in the [source dossier](../legacy/sources/hockeyviz-shootiness.md). neither model claims causal isolation or private-model equivalence.

v1-11 owns territory; v1-12 owns the ten-term ledger, replacement and common-workload contributions. do not populate ledger rows, invent a shootiness addend, multiply minutes in react or count penalty-created specialty minutes twice. no preparation rerun, source acquisition, execution/spatial/goalie fit or rescore, new spatial map, recipe search, bootstrap, new card, calibrated interval or activation. v1-19 can develop independently against the shared current publication contract.

## inputs and cost

real execution needs the hdd; fixture development does not. use fresh ordinary directories under `/Volumes/Expansion/hockey-stats/runs/mechanisms-v1-10-<run>/`. preserve originals, expensive states, frozen paths, active/previous databases, primary build and port 3000. one heavy command at a time, including large reductions, publication and strict startup. measure first annual reduction/solve and incremental bytes/time/memory; no promised runtime or further numerical campaign. 64 gb remains the memory envelope.

pin these existing inputs; these are repository receipt bindings, not a fresh external byte audit:

| input | locator under `/Volumes/Expansion/hockey-stats` / binding |
|---|---|
| prepared evidence | `prepared/evidence-v1-01-02/manifest.json`, `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c` |
| reported head coaches | `runs/coaches-v1-02-20261022-01/coaches-01/coaches.json`, `102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0` |
| corrected execution score selection | `runs/execution-spatial-replacement-20261031-01/real/scores-selection.json`, `588376316a8b4d5311a1677bb3f1419f3754854f25dd2a28e09e3e8c000f9450` |
| complete g/ev/st donor | `runs/spatial-st-v1-09-20261112-03/real/results/manifest.json`, `21de98fb8538632296a00e0650c9005f4a267b6a75bd6e09d541864f6f3836c3` |
| donor composition receipt | same directory, `special-teams-composition.json`, `15d14d611289a36aecca4aea24d996876055577b6157c6d5ce0d39ea982a4654` |

the [accepted shared target](../research/goalies-v1-07/receipts/shared-final-g-st-live-target.json) and [st closeout](../research/spatial-st-v1-09/verification.md#delivery-closeout) bind all five saved ev/st states and references. resolve their exact locators/digests through those explicit selections/receipts; save them in one v1-10 input selection before execution. no newest-directory discovery. inspect saved scalar/reference members through a narrow checked reader; do not load full spatial designs or regenerate maps. compatible successors require explicit selection and exact inherited-body/lineage checks.

the latest accepted combined candidate was 31.26 gb; strict startup took about 39 minutes. these are inherited measurements, not this task's forecast. one new candidate and detached acceptance remain necessary; do not repeat completed upstream campaigns merely to populate two families. normal native commands, numpy/scipy/effect/react/sqlite and existing readers suffice; no runner, local fit mirror or new dependency.

## owners and interfaces

| boundary | files and responsibility; content counterpart |
|---|---|
| evidence/design | new `mechanism_design.py`; consume `analysis_data`, `analysis_context`, reconstruction and factual owners. one penalty-group qualification, separate masks and choice rows. source designer owns population/reason vocabulary |
| numerical | new `player_mechanisms.py`; two objectives, priors, annual history, projections, valuation and diagnostic comparison. numerical designer owns units, reference and interpretation |
| saved state | new `mechanism_state.py`; finite annual/selection/member contracts, narrow reads and receipts. no model registry |
| shared elapsed encoding | extract reused context/transform/actor encoding from `spatial_design.py` into `elapsed_design.py` only as needed; ev/st delegate to the same implementation and retain exact behavior. no dummy spatial design or duplicated chronology |
| composition/publication | new `mechanism_composition.py`, existing `analysis_publication.py`, publication/server/shared schema owners; replace only pending owned rows, preserve other families; evidence designer owns detached meanings |
| application | existing `analysis-values.ts`, `analytical-details.tsx`, `analytical-card.tsx`, history/csv/cohort owners; fill present panels, consolidate repeated facts, expose evidence. content designer owns labels and export fidelity |
| integration | `analysis_cli.py`, canonical fixtures/docs; one root owns shared-file merges, resource scheduling and final acceptance |

reuse `chance.solve_logistic`, sparse arithmetic, saved membership/chronology and narrow spatial readers. share a small positive-intensity primitive only where it removes actual duplicate algebra. do **not** call spatial `fit_head(volume)` with fake arrays: it fits age coordinates and requires unrelated spatial contracts. mechanisms are age-neutral. remove displaced duplicate helpers/calls; retain supported inactive encoders and historical research commands.

```text
fit --family penalties --prepared DIR --coaches FILE --season ID
    [--previous PENALTY_STATE] --out NEWDIR
fit --family shootiness --prepared DIR --season ID
    [--previous SHOOTINESS_STATE] --out NEWDIR
summarize --family mechanisms --results CURRENT_EXCHANGE
    --states INPUT_SELECTION --out NEWDIR
publish --observed FILE --results DIR --out NEWDIR

prepare_penalties(prepared, coaches, season) -> PenaltyDesign
prepare_shootiness(prepared, season) -> ShootinessDesign
fit_mechanism(design, previous, output, *, final_year) -> MechanismState
read_mechanism_state(path, purpose, family) -> checked state
reduce_minor_reference(prepared, execution_score, ev_saved, st_saved) -> MinorReference
compose_mechanisms(existing_results, selection, output) -> current exchange
```

extend the closed cli choices; reject irrelevant/duplicate flags. shootiness rejects coaches, valued scores and basis. penalty fitting rejects valued scores/basis. first year forbids a predecessor; later real years require the exact preceding same-family state. final-year dispatch attempts the sole tighter solve automatically, rather than requiring an undiscoverable separate command. two independent chains avoid making territory's later implementation rerun either head. each real family contains all five years; fixtures declare their own consecutive subset and final year. a failed head saves failure/incoming history and cannot produce an available baseline or silently reset the next year's prior.

## source qualification

### penalty awards and elapsed population

use saved maximal membership segments and elapsed chunks with genuine 5v5, both goalies and verified membership/horizon. retain zero-award time. each physical interval supplies **two directed** opportunities; a counted award belongs once to its drawing-team direction. player role-time is physical time, not doubled. do not inherit shot-coordinate, shot-type, shooter or execution-value exclusions. incomplete penalty observation or membership cannot establish zero awards.

classify each complete `(game,period,clock)` penalty group from source records, retaining api/report locators. ordinary candidates are exactly `MIN` duration 2 minutes and `BEN` duration 2. `MIS/GAM` companions may be ignored for manpower only when their typed classification is known; no description-substring inference. cancel opposing ordinary counts: with `m_home,m_away`, remove `min(m_home,m_away)` from both. residual multiplicity is a team count, never an arbitrarily chosen offender: two same-side residual minors count twice and receive `2*V` under the declared isolated-opportunity approximation, not a simulated 5v3 duration. a pure known nonordinary group is outside the target. an ordinary-containing group with major, double-minor, unknown or otherwise ambiguous compound disposition is unresolved. preserve all original facts, including committed/drawn/served identities.

separate `group_disposition` from `elapsed_assignment`. native reconstruction marks some multiple same-clock non-attempt matches ambiguous; that alone does not make source net counts unknowable. for assignment require equal api/report penalty-group cardinality and unique ordered source identities. take the first report penalty row's roster-checked full membership; require `membership_interval_link` to return `before|both` and exactly one matching maximal segment immediately before the clock. only-after, absent or contradictory pre-award evidence is unresolved assignment. later rows may reflect administration. use the first source-ordered api penalty's pre-event context for all group responses, never the following chunk; unavailable chronology leaves contextual fields unknown. retain a source-known group even when assignment fails, but exclude implicated model counts/time. unequal source group cardinality is an unresolved possible award, not a proved complete net count. do not require all same-clock api situation codes to agree or infer earlier 5v5 from a later reduced lineup. bench, goalie or off-ice named offenders need no invented on-ice offender; attribution is to the verified on-ice teams.

report-only `PENL`, missing collections, unknown possible penalty kinds, duplicate identities and malformed clocks receive explicit dispositions. unresolved groups exclude all potentially affected maximal segments, both directions and child chunks, once; unlocatable clock widens to the known period, or game if period is unknown. propagate a proved membership defect; do not propagate an unrelated shot defect. a known 6v5 delayed-penalty award stays outside the 5v5 response. save mutually exclusive group/event dispositions, union excluded seconds and unquantified gaps, reconciling counts and physical/directed exposure.

repeat/switch is relative to the **taking** team and the last source-qualified residual ordinary-minor group at **any strength**, independently of fit exclusion. source-known awards can update it despite unqualified exposure. all awards at one clock use the pre-group value; apply one post-group side update after cancellation. elapsed time starting at that clock uses the post-group value. split chunks at these updates. a canceled or known nonordinary group neither changes nor repairs history. an unresolved possible ordinary award makes history `unknown` until a later unambiguous residual; `none` means verified no previous award. period changes do not reset it. this is a declared officiating-sequence covariate, not inferred intent by referees.

### shooter choices and qualification time

use ordinary physical attempts, including blocks and tips, in `5v5,5v4,5v3,4v3,4v5,3v5,3v4`. require the actual attacking skater set, both-goalie physical strength, known team and source-checked physical shooter among those skaters. known goalie attempts are outside; own/awarded goals, penalty shots and shootouts are outside; unresolved attempts remain excluded with evidence. coordinates, shot type, inferred origin and execution availability are irrelevant. no outcome/future event is a predictor.

retain each valid choice independently. qualification seconds use supported native seven-state membership/horizon and dated member identities, subtracting corroborated membership-conflict unions only, **not a likelihood exposure or denominator for shootiness**. do not subtract the entire ordinary-attempt mask or its count/location/type/value-only failures. penalty exposure uses the corresponding independent membership rule plus its award-specific exclusions. incomplete choices are counted separately; do not delete other valid choices or turn missing choices into non-shooting observations. save exact-state seconds, included team choices, focal shooter counts and exclusions; pooled candidate incidence across seven states supplies coefficient information. minutes alone do not inform this conditional model.

use the prepared season's fixed `F/D/unknown` group consistently for fit/reference: `C/L/R/F` collapse to `F`; unresolved F/D identity remains unknown. do not substitute a forward, outcome-based position or later-season position. unknown-role candidates participate in actual choice sets; their standardized F/D-unit result is unavailable.

## fixed numerical contracts

### ordinary-minor intensity

```text
eta = log(r) + intercept + draw_players + take_players + coaches + context
lambda = exp(eta)                            # awards/hour
loss = sum_time E_hours*lambda - sum_groups residual_count*eta + prior
r = (qualified_awards + 1)/(directed_hours + 1)
```

use the full ev elapsed context/coach score-shell design from the attribution appendix, freshly centered/scaled by this penalty population, plus centered `none/repeat/switch/unknown`. drawing maps to attacking and taking to defending; event score is authoritative pre-event score, while subsequent time uses updated score. inherited counters remain frozen at their declared chunk boundary. unknown context remains explicit. one smoothed offset hour/award and richer context are initial assumptions; no selection campaign.

priors: players sd `.25` on entry, `.10*sqrt(year_gap)` on carry; coaches `.10` / `.05*sqrt(year_gap)`; context sd `1`, intercept sd `2`. one entry **or** carry penalty; no age coordinates. raw last-likelihood-supported actor/subblock coefficients carry, not changing annual report centers. positive elapsed or counted-event incidence establishes information, including zero-award actors; unsupported coach subblocks do not refresh. all identified annual skaters have coordinates; uninformed actors remain at their conditional prior mean with explicit prior-only status.

center player roles by retained role-slot time and coaches by applicable time, transferring constants/applicability exactly as the ev reference. shared centered context is zero. insert one focal player in the drawing or taking role of that virtual reference. publish `complete-neutral` awards/hour, not the coefficient or an observed personal penalty rate. both player roles use the same two-direction population and therefore the same information years/prior anchor; validate that invariant rather than hiding a support mismatch. positive taking means more team penalties.

### conditional shooter choice

```text
w(F,s)=(2/3)/n_F; w(D,s)=(1/3)/n_D; w(unknown,s)=1/unit_size
logit_i = log(w(role_i,s)) + role_offset[role_i,s] + b_i
p_i = softmax_unit(logits)_i
loss = sum_choices (logsumexp(logits)-logit_shooter) + prior
```

absent position groups create no candidates/division. fit two fixed role contrasts per state with `F,D,unknown` offsets summing to zero; use sd `1` on the reconstructed three offsets. the common shift cancels. player sd `.5` on entry / `.2*sqrt(year_gap)` on carry, age-neutral. candidate incidence, including never-shooting teammates, updates history. save raw coordinates; report-center by each role's pooled candidate incidence and transfer its mean into that role's reporting offset. absent-role center is zero. **do not reimpose the fitting zero-sum constraint after reporting transfer.** check actual probabilities invariant, including unknown-role candidates.

reference units are `3F/2D` at 5v5; `4F/1D` at 5v4 and 5v3; `3F/1D` at 4v3; `2F/2D` at 4v5; `1F/2D` at 3v5 and 3v4. all other player deviations are zero; insert the focal centered coefficient into one same-position slot. retain fitted reporting role offsets. normalize the entire unit, then publish focal `probability`, same-slot all-neutral `neutral_probability`, and `difference=p-p0` as fractions. presentation multiplies by 100 once for percentages/percentage points. unknown position leaves all three unavailable; zero selected-state time can coexist with a fitted shared coefficient and a hypothetical projection. there is no extra goal-value term.

### isolated-minor value

read `a` from saved neutral 5v4 xg/hour and `e_f,e_a` from saved neutral ev xg/hour. verify their reference identities and equality across repeated player projections. **v1-09 supplies no shorthanded offensive model**: reduce `b=sum(neutral uqrg)/matched 4v5 hours` from pinned scores and independently matched shorthanded support. count only proved 4v5 shooting-side responses; ignore proved advantaged attempts even if their score is absent. exclude all counts/time of maximal segments containing an ambiguous potentially shorthanded ordinary attempt or a shorthanded attempt without a usable neutral value; retain zero-event time. wrong score key/state/shooter/outcome lineage is a contract failure, not ordinary missingness. do not import v1-09's advantaged-response mask, reconstruct a probability or rescore. save numerator, attempt count, exposure, exclusions and source/score identities. `b=0` is valid with positive time and zero mass; zero exposure means unavailable valuation.

```text
T = 2/60 hours
tau = -expm1(-a*T)/a                 # tau=T at a=0
V = (a-e_f-b+e_a)*tau                # goals / isolated ordinary minor
drawn_value_per60 = drawn_per60*V
taken_value_per60 = -taken_per60*V
```

all complete reference rates are finite/nonnegative; never clip `V` to positive. a pp goal terminates the opportunity; a sh goal does not. the source-pooled sh rate averages actual retained circumstances, unlike the hypothetical ev/pp references. overlaps, 5v3, end-of-regulation truncation and focal specialty skill are omitted. expose this approximation and any negative `V`. unavailable valuation withholds only value fields; available penalty-rate contrasts survive. save all five annual references for v1-12, which alone applies `1000/60` hours and groups ledger contributions.

## artifacts, solver and diagnostics

finite annual manifest: `schema_version=1,kind=player_mechanism_state,purpose,family,season,recipe,design_identity,implementation,prepared,coaches|null,previous|null,training_cutoff,head,files,resources`. bind every consumed member by path/hash/bytes and exact array axes/shapes/dtypes. save compact design arrays, coefficients, source/group/choice/exposure dispositions, transforms, priors, last-supported ledger, centers, reference, projections, support, solver and probes. use existing artifact json/hash/array primitives; narrow projection reads need no design reconstruction or external source access. unknown fields, duplicate keys, stale/wrong years/family/recipe/purpose/lineage and malformed finite values fail.

freeze recipe ids `penalties-v1-10-1` and `shootiness-v1-10-1`, with the full equations/constants/design policy in their hashed recipe bodies. `head` has `status,reasons,priors,ledger,centers,reference,objective,solver,diagnostics`; failed/unavailable branches retain reasons and incoming ledger, with no completed coefficient array. `design.json` binds ordered players/coaches/context columns or roles/states, transforms, source row locators and `arrays.npz`. penalty arrays are sparse time/event designs, hours and residual counts; shooter arrays are choice offsets, candidate ids/roles/states, winner indices and multiplicities. offsets partition candidates exactly; winners index their own choice; ids/axes/dimensions and positive counts/hours reconcile to saved dispositions. no source response or design field is inferred from array position without a bound axis. save `support.jsonl`, `projections.jsonl`, `reference.json`, `coverage.json` and finite probe records through one strict reader; ordinary fit/reuse and narrow composition reads validate the members they consume.

input selection: `schema_version=1,purpose,prepared,coaches,source_results,execution_scores,years[]`; each ordered year binds `season,penalties,shootiness,execution_score,ev_state,st_state,minor_reference` by path/hash, with `minor_reference` required nullable. null means derive once; a binding means validate/reuse that completed compatible reduction. references agree with the donor's numerical lineage. chronology is exact predecessor equality, not merely sorted labels. write a separate source-reduction receipt containing sh numerator/count/time/exclusions and input identities; the numerical reference binds that receipt and the final manifest binds both. no file contains its own byte digest or discovers a predecessor by path guessing.

use analytic gradients and the current scipy wrapper: `maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10`; one continuation from the completed final baseline with `ftol=1e-16,gtol=1e-7`, other settings unchanged. stable logsumexp/expm1 and finite loss/gradient/probability checks are required; no clipping overflow or malformed probabilities into success. compress identical designs by summed exposure or choice/shooter counts without changing objective; batch at most 4096 choices. no multistart, solver sweep, repeated rescue or new numerical framework.

record native exit/message, iterations/evaluations, loss and gradient, requested versus achieved tolerances, wall time/memory and exact saved coefficients. zero-event penalty time is valid; a completely zero-exposure penalty or zero-choice shootiness family is unavailable rather than synthetic fitted evidence. `ftol` completion does not certify `gtol` or coefficient accuracy.

compare each final continuation with its baseline on **all** current skaters: penalty complete/neutral/difference/value rates (`1e-4/hour`) and prospective 1000-minute penalty values (`1e-3` goals); shootiness every available state/reference slot probability and difference (`1e-5` fraction). actual fitting-row probabilities/rates receive the same respective `1e-5`/`1e-4` limits; report maxima/worst rows separately and include them in the diagnostic verdict. propagate both separate variants through available references; no fabricated shootiness-to-goal sensitivity before v1-12 supplies its opportunities. findings are `within_budget|exceeded|unassessed`; a failed/nonfinite/absent probe is unassessed, never zero movement. earlier years state `not_assessed`. baseline outputs remain authoritative; probes never replace them. record in-sample expected/observed totals and state/role fit summaries, explicitly not held-out accuracy.

## publication and application

hard cut to **exchange4/schema10** with the finite [mechanism evidence contract](experimental-application.md#mechanism-evidence-projection) on the two existing payloads and v1-19's [saved goalie evidence](experimental-application.md#goalie-evidence-projection). reconcile that [shared foundation](experimental-application.md#shared-exchange4schema10-cutover) before either candidate assembly; no dependency on the other family's fits. keep routes, scalar selectors, cohorts and tables. one temporary attributed converter stages the pinned exchange3 donor, enriches provided goalie rows from saved proofs, preserves inherited real numerical bodies/catalogs and leaves pending mechanisms null. no provided old payload is silently upgraded without its required evidence. the [synthetic penalty correction](../research/mechanisms-v1-10/product/verification.md#fixture-valuation-resolution) and [coherent joint fixture](../../fixtures/goalie-card-v1-19/README.md) are attributed successors; preserve originals exactly. delete conversion tooling after verified use. permanent writers/readers accept only the current contract; frozen prior outputs/receipts remain intact.

composition fills one penalty row and seven shootiness rows per published skater-year, plus closed method/reference/support evidence. reject conflicting computed owned rows rather than overwriting them. preserve all inherited factual, execution, g, ev/st, microstat, ledger and warning content. copied `recorded_drawn/taken/served` equal `skater_descriptive.recorded_penalties.focal` exactly; those all-strength personal facts do not adopt the mechanism mask. no ledger or territory placeholder becomes computed here.

after conversion, `source_results` binds the exact current-schema donor and its conversion receipt binds the original pinned exchange3 manifest. this is an attributed structural successor, not different numerical evidence. a later compatible current-schema descendant can be selected explicitly; the last compositor preserves other accepted families rather than forking from a stale donor. no second legacy-format read path remains in normal composition.

existing league/profile/comparison/history and `/api/players/:id/evidence?family=penalties` serve results; shootiness uses its existing profile/history path. detail exposes both probabilities for every state, including raw-only neutral selectors without ranks. retain current F/D cohorts and per-state minute rules; qualification is not precision. maps reject these non-spatial families. current shared export owners include evidence in csv and essential meaning/limits in png; no browser model or valuation implementation.

content designer freezes copy and layout before coding:

- “ordinary-minor drawing/taking difference” means signed team awards per60; “ordinary-minor drawing/taking value” means signed goals per60 under the isolated-minor reference. distinguish named-person recorded counts. show positive taking as more penalties; high percentile always means a larger supplied quantity.
- “share of team attempts” shows focal probability, neutral probability, percentage-point difference and common unit. show exact-state qualifying minutes separately from pooled seven-state information; neither is observed shot share or finishing.
- show complete/neutral penalty rates, `a,b,e_f,e_a,tau,V`, matched sh support, annual carry, prior-only flags and numerical limitations in selected detail/history/evidence exports. no confidence band or causal credit. zero, unavailable and prior-only remain distinct.
- populate analytical i06/i09/i10 and detail using the existing composition. remove the duplicated recorded penalty table/export branch currently rendered from both descriptive and modeled payloads; keep the descriptive owner authoritative. comparative/microstat penalty ledger tiles remain pending v1-12.

good content permits identification of quantity, population, reference, units, source versus model and information limits without reading research files. complete this family on real profiles, comparison, histories, tables and actual downloads; whole-card completion still has later owners.

## execution and acceptance

implement independent source/design, numerical/state and publication/content boundaries in parallel; root integrates and independent reviewers challenge each boundary before expensive execution. fixture work precedes real annuals. run the two five-year chains and their two prescribed probes serially, then compose, publish once and verify the changed end-to-end paths. no automatic extra scientific campaign or approval ceremony between ordinary successful steps.

| boundary | independent acceptance |
|---|---|
| source | reconcile every group/choice disposition; physical time once, directed penalty time twice and actual player slot-time. check original bench, offsetting/multiple residual and double-minor examples; labeled synthetic controls cover unobserved unknown-clock/chain/candidate boundaries. no exhaustive original-witness hunt |
| mathematics | hand-recompute small objectives/gradients, zero-event intensity, full choice normalization, candidate-not-shooter information, chronology/entry-or-carry, raw/report invariance, virtual units, minor survival/value including `a≈0`, `V≤0`, missing sh support and signs |
| real state | all ten annual heads and two final diagnostic attempts accounted for; exact lineage/support/reference/projection checks, five-year in-sample diagnostics, costs and availability. a failed baseline is recorded incomplete, not rescued by a disclaimer |
| composition | three-season full key inventory; independent complete-minus-neutral, value and probability closure; exact repeated facts and unrelated-family equality, original and converted fixture preservation; no ledger completion claim |
| application | producer→sqlite→typed api→selectors/cohorts/history→analytical profile/comparison→actual csv/png equality. all seven strengths, both positions, traded/sparse/prior-only/zero-specialty-time cases; inspect exports, narrow layout and native 200% zoom. verify taking sign and single percent conversion |
| operation | detached candidate/browser without source paths, ordinary strict startup/cost measurement, isolated disposable schema-paired rollback and preservation of live app/databases/evidence. activation remains separate |

use ready local originals: `2024021177` plays256–258 (two minors against one), `2022020744` plays61–62 (opposing cancellation with changed api situation codes), `2024020022:163` (bench), `2025021094:106` (double minor), `2025020006:342–343` (minor/misconduct outside 5v5), `2024020186:221–224` (mixed major group). these are api inspection locators, not already proved model memberships. [factual witnesses](../research/facts-v1-03/real/penalty-source-witnesses.json) retain additional checked source/report links. reuse complete retained bundles; preserve distinct newly exposed defects under fixture policy.

temporary integration/live **red → green → refactor → green**, then delete campaign tests/controllers and unused test dependencies. retain source fixtures, checked expected facts, useful scientific diagnostics and receipts. no new permanent harness; explicitly selected stable regression ownership stays with [07](07-lightweight-testing.md). record verification, commands/costs, reviews and unresolved issues under `docs/research/mechanisms-v1-10/` and `docs/issues/`. reviewers must distinguish specification review, software acceptance, real integration, diagnostic status and scientific support.

accepted tradeoffs: conservative ordinary-minor scope and exclusions; richer but weakly constrained penalty context; shared cross-strength shooter skill; fixed position weights/units and priors; age-neutral point-history borrowing; isolated-minor valuation with mixed reference construction; unknown optimizer accuracy; one schema conversion/candidate build. these are finite baseline choices, not reasons to omit required available output or claim stronger evidence.
