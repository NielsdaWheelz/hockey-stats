# v1-07 — goalie continuation and results

full implementation handoff; [the plan](../plan.md#current-boundary) owns assignment. builds on [execution base](v1-05-execution-base.md), [scoring](v1-06-execution-scoring.md), [chance/goalie definitions](experimental-chance.md#goalie-card-evidence-and-conditional-summaries), [application](experimental-application.md) and [g01–g14](../product-inventory.md#goalie--public-savingtypedanger-examples-and-documented-subskills). specification only: no implementation, acquisition, fit or activation is assigned by this document.

## outcome and boundary

deliver real goalie estimates and evidence for five chronological seasons `20212022`–`20252026`, publishing the last three. add two continuation heads per year, then complete stopping, six subskills, actual results, type/danger/location evidence and annual summaries. use the existing private application's direct goalie profiles, selectors, cohorts, history and exports. seasonal estimates describe underlying level across the selected season; they are not held-out forecasts or causal isolation.

scope: **ten new annual head-states, at most two final-year tighter continuations, five annual goalie score artifacts and one combined three-season exchange/candidate.** one continuation is attempted for each completed final-year baseline; a missing/failed baseline records `not_run` with reason. starts and diagnostic evaluations add actual computation; ten states is not ten optimizer calls. the corrected four-head execution chain is an immutable input. no base refit, base score-artifact regeneration, spatial fit, source preparation/download, new seasons, alternative recipe search or calibrated-uncertainty campaign. evaluating required base conditionals through the existing pure evaluator is permitted; rebuilding its event/coalition/reference artifacts is not.

**user boundary choice, 2026-11-08:** v1-19 owns goalie discovery, browser two-goalie comparison, the complete goalie sheet, assembled type/danger/map panels and full-card png. those discovery/comparison paths are currently skater-only; they are not existing goalie functionality. v1-07 verifies direct goalie-profile stopping/subskill selection, detail, cohorts, history and selected-field exports; all new map/evidence payloads and paired map requests receive api acceptance. this does not close v1-19's visual obligations. no goalie war, replacement total, generic rebound-value component or contribution to the skater ledger. v1-17 may proceed independently, with coordinated shared-file edits.

**user decision, 2026-11-08:** new-head optimizer sensitivity is a disclosed diagnostic, not a publication gate. one tighter solve per head; flag changes above `1e-4` probability, or `0.01` percentage point, in the summaries below. completed, mathematically checked baseline estimates may be published experimentally when sensitivity exceeds that threshold or is unassessed. no automatic retry campaign. incomplete baseline solves, leakage, invalid probabilities, wrong units/joins and broken accounting still withhold affected output. this prospective exception applies only to v1-07; earlier verdicts and other family protocols remain unchanged.

## inputs and operating contract

real execution needs the hdd; docs, source work and attributed fixture development do not. all new expensive outputs use fresh directories under `/Volumes/Expansion/hockey-stats/runs/goalies-v1-07-<run>/`. no colima/docker dependency, local fit mirror, checkpoint engine or release manager. retain original evidence, expensive states and failed diagnostic records. never touch the serving build, port3000, active/previous databases or source captures.

pin these inputs under `/Volumes/Expansion/hockey-stats`:

| role | relative locator | sha256 |
|---|---|---|
| preparation | `prepared/evidence-v1-01-02/manifest.json` | `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c` |
| reported coaches | `runs/coaches-v1-02-20261022-01/coaches-01/coaches.json` | `102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0` |
| corrected base scores | `runs/execution-spatial-replacement-20261031-01/real/scores-selection.json` | `588376316a8b4d5311a1677bb3f1419f3754854f25dd2a28e09e3e8c000f9450` |
| combined composition input | `runs/execution-spatial-replacement-20261031-01/real/results/manifest.json` | `a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5` |

each selected score binds its exact annual base state, preparation, coaching and panel members. copy those identities into the new target/score manifests; no latest-file discovery, old execution selection or probe promotion. the corrected final base state is `real/u-repair-01/assembled-01/20252026/manifest.json` under that replacement run, digest `59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276`. [accepted score identities](../research/spatial-v1-08/receipts/real-final-score-completion.json), [selection](../research/spatial-v1-08/receipts/real-execution-composition-completion.json) and [combined exchange](../research/spatial-v1-08/receipts/real-spatial-composition-completion.json) are the binding evidence. inspect small manifests first; perform necessary full input validation once at the owning command, not repeated independent whole-corpus scans.

compose onto the combined exchange, **not** execution-only `3441f784`: dropping the spatial family is a defect. an explicitly selected compatible descendant is allowed only if preparation, source facts and corrected execution identities agree and non-goalie families are preserved. fixture selections have their own `purpose=fixture`, consecutive annual subset and matching complete source/score/result identities; never use synthetic examples as real acceptance.

## responsibilities and interfaces

| owner | responsibility |
|---|---|
| `analysis_context.py`, `execution_history.py`, `execution_design.py` | existing labels, chronology, source-only identity resolution and shared predictor construction; no second source parser |
| new `goalie.py` | public two-head preparation/fit/evaluation; q/r-form design, fractional response, priors and new-head diagnostics using existing numerical primitives |
| new `goalie_state.py` | strict two-head state/probe/target artifacts; reuse finite-json, array and raw-history helpers without widening the immutable four-head contract |
| `execution.py`, `execution_scores.py` | authoritative base probabilities and saved panels; generalize the existing checked panel accessor to declared exact states |
| new `goalie_scores.py` | focal/reference projections, new-head event values, saved panel/support evidence, annual score artifacts and detached validation |
| `descriptive.py`, new `goalie_composition.py` | authoritative source-only goalie reductions, matched numerical evidence and complete-exchange composition; no model success requirement for source counts |
| `analysis_publication.py`, `publication.py`, existing effect schemas/readers | schema8 invariants, required keys, shared native/display transport and typed reads; no fitting or coefficient interpretation |
| `analysis_cli.py` | thin family dispatch; preserve existing commands and reject unrelated flags |
| existing `analysis-values.ts`, cohort/history/export owners and player route | explicit conditional labels, support/limitations and actual existing-route integration; no second dashboard |
| content/review | one designer for modeled skills/maps, one for actual evidence, one for history/cohort/export fidelity; independent source, numerical and systems/content review |

shared refactors must preserve old execution predictions/recipe identity. extract its source-row/predictor construction rather than cloning it or preparing a fake q/r fit. `read_panel` currently restricts callers to physical 5v5 although all states are saved; support the declared exact-state enum and verify a cached panel matches the requested state. never return a cached 5v5 panel for pk. remove duplicate derivations and obsolete placeholder behavior, preserving correctly implemented inactive features and historical scientific tools.

```text
hockey-stats-analysis fit --family goalie --prepared DIR --coaches FILE
  --valued ANNUAL_EXECUTION_SCORES --season YYYYZZZZ [--previous GOALIE_STATE]
  --out NEWDIR
hockey-stats-analysis score --family goalie --prepared DIR --coaches FILE
  --state GOALIE_STATE --valued ANNUAL_EXECUTION_SCORES --out NEWDIR
hockey-stats-analysis summarize --family goalie --prepared DIR
  --results COMBINED_RESULTS --scores GOALIE_SELECTION --out NEWDIR
hockey-stats-analysis publish --observed FILE --results DIR --out NEWDIR

prepare_goalie(prepared, coaches, annual_execution_scores, season) -> GoalieDesign
fit_goalie_year(design, previous, output) -> GoalieState
read_goalie_state(path, expected_purpose) -> GoalieState
goalie_probabilities(state, focal_predictors, origin_cells, neutralize) -> (h,d)
score_goalie(state, prepared, coaches, annual_execution_scores, output) -> GoalieScores
read_goalie_scores(path, expected_purpose) -> GoalieScores
compose_goalie(prepared, combined_results, annual_goalie_scores, output)
  -> complete player_analysis_results exchange
```

`--valued` identifies one checked annual score artifact; its base-state reference is read explicitly at fit/score time. `--previous` is required after the first selected year and rejected for the first. require consecutive years, identical prepared/coach/recipe definitions and current-year target bindings; no future-year state enters an earlier fit. `--scores` is strict `{schema_version:1,purpose,prepared_sha256,scores:[{season,path,sha256}]}`, five ordered goalie-score manifests for real composition. reject repeated/unknown flags, mixed purposes, wrong identity/year and occupied destinations. preserve old family-specific flag rejection. no command acquires or activates data.

## source labels and separate populations

use `attempt.immediate_outcomes` from `analysis_context.py`; the older longer-span `feature_facts.outcome` fields are different quantities.

| head | included focal events | target |
|---|---|---|
| `h` — recorded reattempt | ordinary saved attempt, source-resolved defending goalie, valid focal predictor core, known immediate reattempt label | binary `reattempt_within_5s` |
| `d` — next-attempt neutral danger | same focal population, `h=1`, exact linked successor has a complete compatible execution score | successor's saved fully neutral all-attempt opportunity `prefixes.neutral.uqrg` |

occurrence examines **only the immediately next recorded event**, in verified source order. same-team ordinary attempt, same period and elapsed delay `0..5` seconds gives true. supported non-attempt, opponent attempt, known terminal, outside-population action or delay above five gives false under the existing source rules. unknown order/clock/terminal/physical/team evidence remains unknown. never skip an intervening event or search a longer sequence. a supported non-attempt needs neither geometry nor team to establish that it is not an immediate attempt.

`h` does not require known recorded-stop status or a valued successor. `h=1,d=unavailable` stays a positive occurrence observation with a separate danger exclusion. zero danger is a valid target, not missing. a blocked successor uses its saved imputed-origin opportunity; no contact-as-release, on-net conditional probability, realized goal or neutral-goalie-only value may replace it. bind `(season,game_id,source_index)` of focal and successor and the exact target-score identity. future identity, type, location, strength, goalie or outcome supplies label/target evidence only; predictors describe the focal shot before its outcome.

keep the source definition when strength or goalie changes after the save: it is a recorded follow-up, not proved physical rebound control. no hidden unchanged-lineup restriction. missing valued successors select the conditional-danger sample; report known positives, valued positives and exclusion reasons by year/state/goalie. fitted danger extrapolates from that subset and omits uncertainty in its base-model target.

## two-head mathematics and history

reuse the q/r **encoding formula**, not their fitted matrices: mirrored 656-cell/type geometry, same fixed context families and goalie workload/rest, tip-masked original shooter, focal defending goalie and separate attacking/defending reported coaches. no setter coefficient. these are execution mirror cells, **not** the forty spatial-attribution modes. predictors come from the original save. optional missing facts retain the existing indicator/imputation policy; recompute column means, scales, active columns, actor centers and supports independently on each head's own eligible rows.

use the execution penalties and raw head-specific last-supported ledgers: spatial base/type `.25/1`, neighbor4, context4, shooter entry/carry4/16, goalie16/64, coach256/1024, applicable age-curve ridge64. intercept unpenalized. returners receive carry **instead of** another zero-centered level penalty; coaches have no age drift. retain dated absence, role/age-neutral transitions and exact prior-only completion. no coefficients or age curves transfer between h/d or from q/r. reporting centers never become the next prior mean.

with `p=sigmoid(eta)`, use the proper fractional cross-entropy for d:

```text
loss = sum_i [-y_i*log_sigmoid(eta_i) -(1-y_i)*log_sigmoid(-eta_i)]
       + declared half-quadratic penalties
residual = p_i-y_i
```

use stable logs and summation. the existing binary expression `-log_sigmoid((2*y-1)*eta)` is WRONG for fractional y; do not pass d through it. retain floating response sums in diagnostics. constant fractional `0<y<1` has a finite intercept and is valid; empty support or all-zero/all-one responses do not yield a finite unpenalized learned intercept. preserve the old binary objective/gradient path and accepted coefficient predictions exactly while sharing genuinely common matrix/prior mechanisms.

use the existing solver, zero and current-coordinate prior-mean starts, deduplicated when equal; select the lower completed objective. no em is needed for these two heads. baseline `maxiter=10000,ftol=1e-15,gtol=1e-6`, native `maxfun=15000`; record actual termination, gradients, evaluations and costs. failed/nonfinite baseline heads have unavailable dependent estimates, not finite diagnostic endpoints presented as completed fits. preserve a completed independent head; failure does not invalidate unrelated stopping/source outputs or trigger a base rerun. a consecutive annual container remains a valid predecessor when one head is unavailable: only completed, likelihood-supported heads update their raw ledgers; an unavailable head retains its incoming last-supported ledger unchanged, with the missing-year reason. later years may fit from that last supported state. no diagnostic endpoint or incoming prior is presented as that year's fitted result. record unresolved numerical components as incomplete actual capability, even when unaffected outputs and software are deliverable.

## reference panels, stopping and six subskills

reuse exact annual execution panel membership, order, native origin weights and pre-outcome setup weights. saved panels lack h/d predictors: replay supplied prepared facts once to construct their focal contexts, assert key/state agreement, then evaluate the new heads. this is not re-preparation or base rescoring. saved base logits and applicable actor residuals supply standardized stopping. use the shared evaluator only for required actual-event stage conditionals not already saved stably; do not recompute base allocations, setter responsibilities or skater projections.

let `E` below mean the unnormalized sum over the same origin × setup branches; each physical attempt contributes total branch weight one. all normalization is explicit in the ratios. `E_W` alone denotes a normalized W-weighted average. neutral execution removes shooter, setter, goalie and both coach residuals. focal goalie evaluation restores only that goalie's applicable residuals. exact state is always stored in attacking orientation; public goalie strength is defending-team orientation. e.g. goalie `4v5` uses attacking `5v4`. both goalies must be present for the nine exact public strengths. ev pools `5v5/4v4/3v3`; pk pools defending `4v5/3v5/3v4`. pool constituent panel masses **before** normalizing; actual goalie usage never chooses common-panel weights.

```text
A=E[u]; B=E[u*q]; C=E[u*q*r]; D=E[u*q*r*g]
Q=B/A; R=C/B; G=D/C
stopping = 100 * E[u0*q0*(r0*g0-rG*gG)] / E[u0*q0]
W(branch) = origin_weight * setup_weight * u0*q0*(1-r0*g0)
```

`0` denotes all residuals neutral, `G` the focal goalie. the stopping contrast deliberately excludes q's focal miss effect. use the same global denominator for its native map; cell masses sum to the scalar. map texture reflects shot-context weighting and the shared model, not independently fitted goalie-specific location coefficients.

| published level, plus focal-minus-neutral difference | quantity / conditioning |
|---|---|
| `miss_probability` | `1-Q`, given unblocked opportunity |
| `recorded_stop_probability` | `1-R`, given on-net opportunity; immediate recorded stopped-save proxy, not ordinary save percentage |
| `conversion_probability` | `G`, given on-net and no recorded stop |
| `recorded_reattempt_probability` | `E_W[h]`, given a neutral saved-shot reference opportunity |
| `reattempt_neutral_goal_probability` | `E_W[h*d]/E_W[h]`, conditional on recorded reattempt |
| `followup_danger` | `E_W[h*d]`, per neutral saved-shot reference opportunity |

use fixed neutral W for both neutral and focal h/d. multiply inside the expectation; never multiply independently averaged heads. compute conditional ratios/weights in log space when necessary: rounded-zero mass does not imply an undefined ratio. truly empty panels or unsupported coefficients produce located unavailable fields. an h=0 mathematical denominator makes conditional d unavailable while joint danger is zero; floating underflow must be distinguished. no calibrated intervals are invented.

retain neutral/focal unnormalized prefix masses, saved-shot/h/hd masses, panel ids, both conditional denominators and per-head actor evidence in strict saved projections. missing focal coefficients affect only dependent fields: miss needs q; recorded-stop q/r; conversion q/r/g; stopping r/g; reattempt h; conditional/joint danger h/d. cross-strength coefficient information is distinct from actual role exposure. a prior-only coefficient may remain evaluable.

## actual goalie evidence

three references stay distinct: common-panel modeled contrasts; actual-offense/neutral-goalie paired expectations; fully neutral next-attempt targets. no generic xg label may conflate them.

reuse and extract the existing source-only goalie resolver from `execution_design.py`: opposing event membership, dated team and credited/native conflict checks. do not require a complete model score to count source events. retain resolved-versus-reported attribution provenance; never overwrite old `attempt_fact` rows. unresolved identity/state remains excluded/unattributed with evidence. source counts need ordinary action, identifiable goalie and supported physical state, not modeled type/location. supported event-only rows survive missing elapsed time.

reduce `source_counts` with `unblocked=misses+saves+goals`, `on_net=saves+goals`, and saves/on-net when positive. use prepared boxscore/start/usage records: supported starter=true gives start; starter=false plus positive supported participation gives relief; proved zero participation gives did_not_play only without contradictory event/interval evidence; otherwise unknown with a located reason. missing toi alone does not erase explicit starter evidence. do not infer a starter from the first shot. sum independently supported reported fields with field-specific coverage, never invent a missing count from an unrelated total. reported official ev/pp/pk and all-situations counts remain separately labeled corroboration; they do not prove exact-state or both-goalie totals. unsupported reported splits stay unavailable. preserve all selected-year goalie identities, including unused backups, with honest zero versus unknown support.

pair source and numerical events by exact season/game/source index and compatible goalie/state/outcome. for on-net evidence use saved neutral-goalie `E[uqrg]/E[uq]`; for unblocked use `E[uqrg]/E[u]`. actual offense/coaches remain. remove unvalued rows from **both** paired expected and observed totals, preserving broader raw counts. reconcile paired, source-only and numerical-only keys separately. keep the saved stable conditional values; do not divide rounded prefix zeros.

for each pair population publish `N,goals,sum(p)`, saved-above-expected `sum(p)-goals`, goals per100 expected `100*goals/sum(p)`, mean danger `sum(p)/N`, matched league mean and relative percent `100*(own_mean/league_mean-1)`. on-net alone adds expected save fraction `1-sum(p)/N`. zero denominators yield unavailable ratios, not pseudocounts. the league reference includes each eligible physical attempt exactly once on the same year/strength/population/type; do not double-count aggregate rows. actual `covered_all` retains separate exact physical-state contributions, including supported extra-attacker/own-pp evidence; it is not ev+pk or a claim of complete coverage.

stage evidence intersects known label/target with an available compatible conditional prediction. keep label-only exclusions, including failed-fit reasons, in saved coverage. an empty matched population has zero matched counts/mass and explicit support; it does not assert zero raw observations or zero event probabilities. the matched stage numerator/denominator/expected sum uses: miss on unblocked; recorded stop on net with known stop label; conversion on net with known not-stopped label; h on saves with known occurrence; d on positive valued successors. expected stages retain actual offense with neutral goalie; d responses retain fully neutral successor targets. actual matched d evidence requires a completed d prediction, not a completed h fit: observed h=1 supplies its condition. standardized conditional d still needs both h and d. preserve broader label/target exclusions separately in saved coverage. game rows use the same definitions; do not invent per-game fitted talent or replace game evidence with season values.

## maps, strata and strict public payloads

retain exchange2/schema8 and existing typed goalie tables. fill the fixed required matrix for each published goalie-season; individually unavailable results remain explicit, not silently omitted:

| table | required keys per goalie-season |
|---|---|
| `goalie_result` | eleven `GoalieStrength` values: nine exact both-goalie states plus ev/pk; thirteen estimate/support fields each |
| `analysis_map` | eleven `goalie_stopping` effect maps |
| `goalie_observed` | twelve strengths including `covered_all`, with game records |
| `execution_breakdown` | eleven strengths × six underlying types/three danger tiers =99 |
| `goalie_evidence_map` | twelve strengths × unblocked/on_net × all/wrist_snap/slap/tip/backhand/other =144 |
| `goalie_danger` | twelve strengths × two populations =24 |

reuse the shared native→display transport and fixed 10 ft blur. model stopping maps are additive goals per100 common on-net opportunities. paired evidence maps deposit `p-goal` at supported unblocked origins, retaining attempts/goals/expected masses and unmapped totals. pool goal and expected masses separately before the existing league-relative ratio `100*((pooled_goals/pooled_expected)/(league_goals/league_expected)-1)`. positive ratio means more goals allowed per expected goal than the reference; it is not favorable stopping. ratios do not sum and zero expected/nonpositive league reference gives unavailable. type-specific references match the same type/population.

existing goalie `execution_breakdown` has one population: paired **unblocked** attempts. define `events=eligible_weight=N`, `observed_successes=goals`, `expected_successes=sum(p)`, `probability=sum(p)/N`, `effect=(sum(p)-goals)/N`. label that last quantity recorded goals saved per unblocked attempt, not isolated effect. zero N keeps zero counts/masses and unavailable probability/effect. support events/weight equal N; seconds are null. enforce these equations in python and effect, replacing the current bound-only validation. six underlying model types partition matched counts/masses; grouped two-population type evidence comes from `goalie_evidence_map`, not another breakdown schema.

three danger tiers use the event's fully neutral **on-net** probability `<.05`, `[.05,.15)`, `>=.15`. the separate 100-bin danger histogram uses the selected paired population's **neutral-goalie** p and edges `0,.01,...,1`, last bin includes1. count/mass every paired event once and enforce total closure. complete base-score rows already require a finite neutral-on-net probability and modeled type: reject inconsistent saved records; source rows without those prerequisites are excluded before pairing with explicit saved coverage. do not add an unclassified histogram/danger bin to schema8 or drop paired mass. densities divide mass by one probability percentage point; their integrals recover goal/expected totals. do not copy an unknown private signed-density or centering formula. source-unclassified types remain visible exclusions, not silently mapped to other.

for modeled scalar support, `events` is the distinct current likelihood-key union for that field's contributing focal heads; `prior_only/current_season_information/prior_seasons` use the same dependency set. a partial prior dependency is not all-head current evidence. `eligible_weight` is the **neutral unnormalized reference denominator**: A for miss, B for stop/stopping, C for conversion, total W for h/joint danger, and neutral `sum(W*h)` for conditional danger. it is neither a count nor the focal denominator; strict projection evidence retains both. `included_seconds` is current-year supported goalie-perspective both-goalie elapsed membership for the selected exact/aggregate strength, solely for cohorts. evidence rows instead use their paired N and null seconds. unknown/partial exposure remains visible; no borrowed boxscore or unrelated-state time.

existing per-field support and method references suffice; no new public payload field or schema bump. each method binds the strict projection/head evidence, recipe, base targets and reference/support policy. inline method/selector/export explanations must disclose conditioning, partial priors and numerical status even with the hdd detached. a detailed structured coefficient drill-down remains v1-19, not implied by a link to an external artifact.

## artifacts and composition

use separate two-head annual states; never append h/d to expensive four-head files or reinterpret old state versions. manifests use strict finite json, contained named arrays, unique fixed roles and manifest-last completion. reusable artifact helpers enforce locators/digests/axes; no pickle, generic model registry or arbitrary metadata bag.

| artifact | required closed content |
|---|---|
| annual state | `schema_version=1,kind=goalie-continuation,purpose,season,recipe,implementation,prepared,coaches,base_state,base_scores,previous,training_cutoff,heads,files,resources`; heads exactly h/d; reuse explicit design/actors/priors/centers/ledger/starts/selected-start/diagnostics/status records, with binary/fractional target kind and floating target mass |
| target/coverage members | focal key/outcome/goalie/physical state; source h label/reason; successor key; d target or located exclusion; target-score identity; h/d eligibility and exclusion reasons. counts by head/year/state/goalie; no synthetic zero for missing target |
| numerical members | baseline descriptor frozen before probes; h-tight/d-tight arrays when available, completion/termination/gradients/objectives, exact design/target/prior hashes and comparison status. a missing/failed baseline has `not_run`/reason and no probe array; a failed continuation has no usable endpoint, retaining only diagnostics. final manifest binds descriptor and members without a hash cycle |
| annual scores | `schema_version=1,kind=goalie-scores,purpose,season,recipe,implementation,prepared,coaches,state,base_state,base_scores,training_cutoff,files,coverage,resources,numerical_sensitivity`; five ordered years |
| score members | keyed h/d actor/neutral-goalie values and eligibility; source reduction/disposition rows; goalie/strength projections with all neutral/focal masses and head support; modeled native maps; source/paired/stage/game/type/danger/evidence-map rows; panel identities and numerical comparisons. use the fixed schema8 payload shapes where they already apply |

state readers validate their own saved design/target/array/ledger relations without reopening provenance paths. score readers likewise read detached from preparation/fits. implementation must finish explicit field/axis schemas before its first fit; unknown fields, malformed arrays, duplicate keys, wrong roles, inconsistent masses/priors and mismatched chronology fail. provenance is evidence, not an instruction for an http reader to traverse external files.

`compose_goalie` consumes supplied preparation plus checked annual goalie scores and a compatible combined exchange. replace only goalie-owned tables/rows/catalog entries; map kind and checked person.kind determine shared-table ownership. preserve all skater/observed/interval/attempt/valuation members and existing source/method records exactly. append only nonconflicting source/method definitions; conflicting reused ids fail. record input/output family/member digests. reusing the original skater evidence is mandatory; no factual rebuild, probability reinterpretation or new model service.

measure the first annual preparation/fit/projection and actual publication size, wall time, peak memory, strict startup, selected read and export costs. one heavy command at a time within the existing 64 gb envelope. stream physical rows, panels, players and cells; do not retain player×attempt×origin tensors or repeatedly reopen all scores per goalie. exact duplicate neutral branches may be collapsed; sampling, fewer origins/strengths/players or relaxed arithmetic are not performance repairs. costs are unmeasured until execution, not promised from old fixture timings.

## bounded numerical sensitivity

retain mandatory objective/gradient, source, unit, prior, positive-probability and accounting checks. attempt exactly one final-year continuation for each new head with a completed selected baseline, holding targets, design, priors and objective fixed. use `ftol=1e-16,gtol=1e-7,maxiter=10000` and unchanged maxfun. this is a sensitivity experiment, not an accuracy certificate; ftol can still stop before gtol. failed/abnormal zero-movement probes are **unassessed**, never passed. earlier years record `not_assessed_for_annual_state`; final-year findings must not become retrospective annual passes.

before probes freeze up to 256 valid keyed focal/panel contexts covering states, types, missingness, tips, low support and both h labels/d extremes, selected in deterministic source-key order. evaluate all origins for a selected panel row. report pointwise h/d/joint changes and the inherited 1e-5 threshold diagnostically; no new population search or retry follows.

compare baseline with h-tight, d-tight and combined h+d-tight without additional solves. for **every final-season goalie and all eleven model strengths**, compare neutral/focal continuation levels and focal-minus-neutral differences; additionally compare normalized actual paired h/d predicted means for each nonempty published evidence summary. flag maximum absolute change above 1e-4 probability. retain counts, denominator movement, total expected-mass consequences and which quantities remain unassessed if one head fails. stopping/base-stage fields must remain exactly unchanged. map integration and evidence closure remain computational checks, not tolerance tradeoffs.

publish the original completed baseline, never a tighter endpoint under its identity. if sensitivity fails or cannot be assessed, methods and exports say so and show measured consequences/unknown remaining optimizer accuracy. poor calibration, target-model uncertainty and conditional prior assumptions remain visible separately. no arbitrary post-result threshold change, silent claim of convergence accuracy, extra continuation or separate prerequisite campaign. the final receipt distinguishes completed baseline, assessed/unassessed sensitivity, scientific quality, software acceptance and activation.

## content contract and acceptance

modeled content designer: explicit labels for all six conditionings; stopping favorable-positive, raw probabilities consistently increasing with the named event, differences stored as fractions and rendered as `100*difference` percentage points. replace the current generated labels and “published neutral goalie forecast” in `analysis-values.ts`. identify ev/pk state mixtures, neutral/focal references and prior/extrapolated support. no all-subskill higher-is-better score or total.

evidence designer: raw source counts, neutral-goalie paired results and standardized skills remain separate. label goals allowed rather than the generic transport name “successes”; distinguish probability from saved goals and additive map mass from ratio. “next recorded same-team attempt within five seconds” is a proxy, not tracking, pass evidence or proven goalie control. never describe covered-all as gap-free all-situations.

history/export designer: reuse current selectors and cohort rules (300 included ev minutes; 50 selected-specialty minutes, adjustable viewing rules). all eleven api strengths remain available even where the current browser exposes ev/pk selectors only. magnitude survives below-cutoff; numeric percentile does not. each historical point uses its own season cohort/reference. include raw units, season/strength, conditioning, support, method and unresolved sensitivity in selected-field png/csv. no invented intervals; a source link cannot be the sole explanation of a misleading number.

| acceptance boundary | required proof |
|---|---|
| source → targets | independent selected original-event checks for immediate next versus later attempt, same-clock order, exact 5s cutoff, intervening invalid event, known non-attempt with missing team, terminal unknown/known, goalie/strength change and h-positive/d-unavailable; complete real inventories and exclusion totals reconcile |
| mathematics/history | independent tiny binary/fractional objective and gradient; constant fractional response, endpoints/empty support, tip mask, mirror expansion, input imputation, entry/carry/age/absence/prior-only and center preservation; existing base-head probabilities unchanged |
| references/evidence | direct branch enumeration verifies all conditionals, fixed saved-shot weighting and joint h*d; both paired populations, stage denominators, defending-strength orientation, exact-state/aggregate/game/type/bin totals, map/density/scalar and ratio arithmetic; underflow/zero denominators correct |
| real computation | five chronological h/d states and scores, ten baseline dispositions, up to two bounded final probes and all three assessed/unassessed sensitivity variants; failed head only withholds dependent fields, never triggers a base campaign. real required coefficients absent because code is unwritten do not count as legitimate unavailable evidence |
| strict artifact/publication | malformed/extra/missing/duplicate/identity/version/population negatives; save/read equality; full required selector matrix; non-goalie exchange members exact; inactive candidate and normal strict reader work without original inputs |
| api | all three seasons, every goalie/required key through existing typed endpoints; representative complete, traded, relief, sparse/prior-only, no-current-minutes and unavailable cases; api scalars/maps/evidence match saved rows |
| current browser/export | direct real goalie profiles, ev/pk stopping and all six skills/differences, cohort cutoff and annual history; normal/narrow/native 200% layouts; real png/csv downloads checked for values, labels and caveats; selected endpoint/map evidence is not full v1-19 visual acceptance |
| review/preservation | independent source, mathematical and systems/content reviewers close findings at each changed boundary; preserved source/fit/serving identities; measured costs and open issues; no scientific admission or activation inferred |

use a small meaningful temporary red→green→refactor→green source-to-api/live chain. do not write hundreds of implementation-mirroring tests. exercise failures before expensive runs, then verify the actual outputs; repeat only for new changes or concrete concerns. new broken source cases retain complete available original captures under the existing fixture policy. useful fixtures, checked expected facts, scientific assessment tools and compact receipts remain. delete temporary tests/controllers/test-only dependencies after the assigned acceptance is complete; historical deletion records stay historical. no new retained harness is selected here. retain the existing waiver of a separate accessibility/voiceover audit; required layout/export checks still need actual evidence.

if browser access is unavailable, record deferred checks and the exact candidate/build; do not claim full acceptance from api checks or silently inherit v1-08's deferral. no numerical rerun is justified by a browser limitation. existing manual inactive-candidate/rollback procedures suffice; do not exercise rollback against the live publication.

## delivery and explicit tradeoffs

write `docs/research/goalies-v1-07/verification.md` with exact inputs/recipe/source identities, commands, baseline/probe/score outcomes, source/target exclusions, row/mass closure, real content examples, costs, independent findings, preservation and cleanup. record software integration, experimental-use sensitivity and scientific claims separately. concrete unresolved defects belong in `docs/issues/`; assigned v1-19 composition remains in the plan, not a fabricated source gap.

accepted costs: ten additional fits and exact common-panel scoring; a recorded-event rebound proxy that misses physical continuations; conditional-danger selection and generated-target uncertainty; fixed shrinkage/point-history assumptions; no calibrated intervals; common usage rather than a goalie's actual mix for modeled skills; extra per-population evidence and larger publication; direct profile access until v1-19 adds goalie discovery/comparison; aggregate schema8 support with saved detailed evidence rather than a new public drill-down; potentially optimizer-sensitive baselines under the explicit diagnostic policy. the benefit is a complete, inspectable goalie numerical family available for the existing product and v1-19, without another admission campaign.

public [hockeyviz xg8](https://hockeyviz.com/txt/xg8) motivates layered outcomes and actor/context adjustment. its [goalie career surface](https://hockeyviz.com/player/helleco93) distinguishes results, subskills and type/danger histories; the retained [reference audit](../research/player-card-references.md#v1-field-audit--2026-10-22) records inspection limits. our recorded-stop/reattempt proxies, neutral reference and stopping headline are independently defined. no private formula, full physical rebound observation or micah-model parity is claimed.
