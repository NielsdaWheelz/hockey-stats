# pr03d — revised chance model

status: **reviewed and merged in `af95c88`; implemented and fixture-verified.** scientific assessment remains separate; real fitting requires 03e authorization. [software verification](../research/chance-03d/verification.md) · [source evidence](../research/chance-03c/decision.md) · [input audit](../research/model-input-audit.md) · [03e assessment](03e-training-assessment.md)

## target and boundary

replace `chance-1` with one interpretable `chance-2` candidate in the existing local python fit/evaluate/score workflow. value genuine 5v5 attempts, including blocked attempts through conditional origin distributions. the user confirmed that location, shot type and supported preceding-play context belong to created opportunity; standardize modeled residual shooter/goalie execution. 04 must not automatically adjust these mechanisms away again.

an observed block can retain positive reference opportunity. the first defensive component concerns reducing attempt volume/danger, not a separate reward for the realized block. later blocking/finishing components require explicit accounting before addition to a total. this is not total defensive value, a causal decomposition or a live forecast.

03b remains rejected. this slice establishes software behavior, not scientific acceptance. real fitting, recipe selection, assumption sensitivity and the support/rejection decision belong to 03e; player attribution to 04. no website, publication, acquisition campaign, tracking dependency, model-selection platform or permanent test harness. the shared three-season local corpus exists; use compact committed fixtures for numerical verification here.

## design basis and departures

the reference is the published [xg8](https://hockeyviz.com/txt/xg8), not undisclosed production code. its type-dependent geometry, recent-event context and historical regularization inform this design. its [2026–27 preview](https://hockeyviz.com/txt/preview2627) announces replacement methods still to be described. source descriptions guide hypotheses; they do not validate our candidate.

| decision | reason / material cost |
|---|---|
| two stages: unblocked, then goal given unblocked | serves current opportunity valuation; no separate miss/freeze subskills. three directly recorded stages remain a possible later revision, not another mandatory candidate |
| joint forward origin/observation model | one observed-data likelihood; unlike a fixed inverse imputer, outcomes inform origins. assumed geometry can still change blocked AND unblocked values |
| shared/type-specific spatial maps and bounded context | addresses demonstrated omissions; increases computation and reliance on recording conventions |
| actor-season effects with shrinkage | permits changing execution effects; three seasons do not establish a physical aging law |
| target-season joint matchup reference | history affects estimates, not reference membership. replaces chance-1's pooled-window reference |
| retained tip-coordinate proxies, no automatic relocation | avoids inventing contact locations; consequential tip sensitivity remains a required 03e question, not resolved by a warning or calibration |

the coupling is substantive: unblocked data inform `a(h)=π(h)u(h)`; block data inform `K d`, where `d(h)=π(h)(1−u(h))`. changing assumed `K` changes inferred `d`, hence `u=a/(a+d)` and reference `u*r`. replacing `u*r` with `r` would change the estimand. adding type does not remove this dependency. neither a coherent likelihood nor a concentrated posterior identifies real block-to-release geometry.

## source and population contract

retain 03c integrity, genuine-5v5/both-goalie eligibility, score accounting and located gaps. read corpus/selection schema 1 and interpreted schema 3. reconstruction envelope becomes schema 3 for type admission below; regenerate cheap derived records from unchanged captures. no old-envelope/model/checkpoint readers. preserve expensive historical artifacts; reproduce them with their historical git revision.

extend only reconstruction's exact type vocabulary with `between-legs` / `Between Legs` and `cradle` / `Cradle`. preserve eleven canonical types, originals, reconciliation status and locators. do not case-fold unknown strings or prefer one conflicting feed. preparation owns six fixed modeling groups:

| group | canonical types |
|---|---|
| `wrist`, `snap`, `slap`, `backhand` | respective same-named type |
| `tip` | `tip-in`, `deflected` |
| `other` | `wrap-around`, `poke`, `bat`, `between-legs`, `cradle` |

missing/conflicting/unsupported type yields `type_unavailable`, not wrist or a missingness predictor. retain original-type diagnostics: acceptable pooled `other` results do not certify each constituent.

ordinary goals require corroborated modifier `none`; own/awarded goals or unresolved modifier evidence yield `physical_attempt_unresolved`. retain credited scorer separately; analytical shooter is unavailable when the physical action is unresolved. this does not prove there was no attempt. do not transfer a goal to a preceding attempt, infer a defender or duplicate a goal. every source goal still participates in score accounting and observed totals. positive penalty-shot evidence remains outside scope. existing frame/identity checks continue.

unblocked coordinates remain recorded origin/contact proxies; tips retain a separate diagnostic. blocks retain observed contact coordinates plus inferred release mass. no tip relocation, missing-location imputation or source overwrite. disclose these measurement conventions.

keep one row per recognized attempt and all applicable reasons. add `type_unavailable`, `physical_attempt_unresolved`, `context_unavailable`; precedence remains known outside scope → unavailable → eligible. report recognized attempts, reconstructed genuine-5v5 attempts and chance-2 eligible attempts as separate counts, including excluded goals by reason. these reuse reconstruction classifications, not a second source-eligibility algorithm. selective exclusion can improve apparent calibration; it is not evidence of repair. missing interval linkage does not itself prevent event valuation or establish usable player-rate exposure.

## selected features and preceding context

use the complete game's unique `sort_order` records before filtering attempts; reuse score/order validation. the immediately preceding record owns context. never skip an excluded or non-5v5 record to find a preferred predecessor.

1. require supported focal period/clock and the existing valid source ordering. no predecessor, a supported period transition, or a valid preceding kind/code pair for `goal`, `stoppage`, `penalty`, `period-start`, `period-end`, `game-end`, `shootout-complete` resets context to no recent action. these are recording boundaries, not inferred possession; text alone does not validate a reset.
2. otherwise require the same supported timed period and known nondecreasing clocks. a gap greater than five seconds gives no recent action BEFORE requiring predecessor type, identity or coordinates. unknown timing remains unavailable. zero means source order within one recorded second, not zero physical flight time.
3. at gap `0..5`, require a valid supported action: `faceoff`, `hit`, `giveaway`, `takeaway`, `shot-on-goal`, `missed-shot`, `blocked-shot`. invalid/unsupported actions make context unavailable. do not call `delayed-penalty` a whistle or every `failed-shot-attempt` a penalty shot.
4. a recent action requires its owner team and in-rink coordinate in the CURRENT shooting team's frame. reuse/extract reconstruction's explicit event defending-side rotation and period-conflict rule; never infer a side from coordinates. prior block coordinates remain block evidence. `x > 25` feet is the current team's attacking zone; other locations are outside it. neither category certifies a rush or possession.
5. for a preceding recognized non-goal attempt, require a unique roster-resolved reported shooter consistent with its shooting team; encode same/different shooter. do not require preceding 5v5 eligibility, interval linkage or report matching. other kinds are not applicable; unavailable identity is not different shooter.

store `previous_event={status: recent|none|unavailable, source_index, event_id, kind, time_gap_seconds, owner_team_relation, current_attack_x, current_attack_y, location_basis, same_shooter, reason}`. unused fields are null; retain available evidence even when unavailable. team relation means recorded ownership, not possession. recent kind has seven levels; other factors are same/opponent team, delay `0..5`, attacking/other zone and same/different shooter. no-recent/not-applicable is the zero reference, never an outcome-dependent unknown category.

the fixed scalar design `x` contains: score margin bucket `≤−2, −1, 0, +1, ≥+2`; period `1,2,3,OT`; home/away; within-period first/middle/last minute; recent factors above. margin is shooting-team minus opponent goals BEFORE the event. minute bands use scheduled length (`1200` regulation, `300` regular-season overtime), never a realized sudden-death endpoint: first `<60`, last `≥length−60`, middle otherwise. references: tied, period 1, away, middle, no recent action. one-hot contrasts; no fitted scaling or configurable feature expressions.

save a prepared `context` object in that field order: `score_bucket`, `period`, `home_away`, `minute_band`, `recent_kind`, `recent_team`, `recent_delay`, `recent_zone`, `recent_shooter`. score codes are `trailing_2_plus|trailing_1|tied|leading_1|leading_2_plus`; period is `1|2|3|OT`; minute band `first|middle|last`; recent fields use the categories above, with null for no recent/not-applicable. keep `pre_event_score`; remove the superseded three-category analytical `score` field. emit contrasts in listed order with reference omitted; type order is wrist/snap/slap/backhand/tip/other, role order F/D/unknown, seasons ascending and actor ids numerically ascending. save ordered feature names in every fitted layout.

| other audited family | disposition and owner |
|---|---|
| prior displacement, angle change, apparent speed, lateral crossing | omit this candidate: contact/proxy coordinates and integer clocks do not track puck movement; a future extension must evaluate focal geometry at each latent origin, not the block coordinate |
| sustained-shot sequences, shift age/fatigue | assess in 03e's omission review; require supported continuity/exposure definitions before addition |
| handedness/off-wing, age | omit here; 03e reviews residual geometry/history limitations; 04 owns selected age treatment. frozen bio equality remains unproved; current identified references exist |
| rink/recording effects, detailed score × time | 03e assesses season/type/geometry drift and home/away residuals; no automatic correction or post hoc short-miss deletion |
| coaches/right-rail, deployment/rest, post-penalty context | 04 is first consumer unless a reviewed chance revision establishes a need |
| setter/assist, on-net/freeze/rebound execution, penalty actors | later components; goal-only assists and later stoppages are not focal predictors |
| own/awarded/penalty modifiers; focal outcomes/blocker/reasons | eligibility, labels or diagnostics only |
| pl printed distance; turnover actor identity | source corroboration/later components; current geometry uses attributed coordinates and recent context needs kind/team, not turnover-player effects. no duplicate distance predictor or actor parser |
| bios/display/rosters, boxscore totals, gs summaries, root clocks/control flags | existing identity/accounting/later display owners; no postgame counts or undocumented flags as predictors |
| passing/tracking/entries/exits, replay/edge | absent core inputs; no new dependency or implied reconstruction accuracy |

“assess” requires an explicit 03e judgment with evidence or a limitation, not implementation of every listed feature.

## numerical contract

reuse the finite 5-foot rink grid, nearest-cell rule, adjacency and goal `(89,0)` feet. retain signed cells; no symmetry assumption or display smoothing. let `h` be origin cell, `b` block cell, `t` model type, `y` season, `s/g` actors and `z` goal label. observations have unit weight; history acts through penalties.

**origin law:** `π_i(h)=softmax_h[a_h + A_(t,h) + R_(role,h) + Y_(y,h) + Σ_j C_(j,h)*x_ij]`. role is `F/D/unknown`, used only in origins. type/role references are wrist/F; seasonal reference is the first fitted season. each nonreference contrast owns a spatial map. no actor identity, focal outcome/location or posterior enters this prior. additive maps share evidence across sparse combinations instead of independent distributions for every crossed stratum.

**outcomes**, with separate stage coefficients:

```text
logit u_i(h) = μ_u + τ_u[y] + f_u[h] + δ_u[t,h] + β_u·x_i + α_u[s,y]
logit r_i(h) = μ_r + τ_r[y] + f_r[h] + δ_r[t,h] + β_r·x_i + α_r[s,y] + γ_r[g,y]
```

`u` is unblocked probability; `r` is goal probability conditional on unblocked. wrist type deviation and first-season intercept offset are zero. no redundant type intercepts. spatial surfaces are shared across seasons. initially retain shooter terms for tips too; 03e assesses their pooling, without publishing finishing components.

**observation law:** retain `K(b|h) ∝ exp(−distance(b,h)/kernel_distance_ft − kernel_direction_strength*(1−cos θ))`, normalized over block cells for EACH origin. `θ` compares origin→block with origin→goal; retain the current same-cell convention. kernel is type-shared, fixed within a fit and computed in log space. soft support can admit implausible paths; this assumed law requires sensitivity.

```text
unblocked likelihood: π_i(h) * u_i(h) * r_i(h)^z * (1-r_i(h))^(1-z)
blocked likelihood:   Σ_h π_i(h) * (1-u_i(h)) * K(b_i|h)
blocked posterior q:  normalize_h[π_i(h) * (1-u_i(h)) * K(b_i|h)]
```

sum over origins BEFORE taking the observed log likelihood. unblocked `q` is point mass at its recorded-proxy cell. posterior mass is not independent release evidence.

**penalties:** summed negative log likelihood plus `λ/2 * sum(coeff²)` per named group and `λ_smooth/2 * sum_neighbor(map[h]−map[k])²` per spatial map. ONLY global `μ_u/μ_r` are unpenalized; seasonal offsets and other nonactor scalars use `ridge_context`. origin base/factor maps have separate ridge strengths; outcome base/type maps have separate ridge strengths. each family has one neighbor-smoothing strength. ridge fixes softmax-map shifts; no additional centering machinery or pseudocount prior.

actor trajectories add `λ_level/2 * Σ_actor,year effect² + λ_change/2 * Σ_actor,adjacent_year (effect_y−effect_(y−1))²`, separately for each shooter stage and the conversion goalie. save one contiguous season order from earliest through latest selection for actors, origin season maps and outcome offsets, including zero-observation intermediate years. each stage-observed actor has every state. first appearance in this corpus is not rookie status. stage-unseen actors use the zero prior mode, explicitly labeled—not an average probability.

**fitting:** fit `r` once. fit `π/u` by em: freeze old posterior weights; update `u` with weighted logistic likelihood and `π` with weighted multinomial likelihood, including the penalties above. reuse scipy `L-BFGS-B`, analytic gradients, warm starts, stable `log_expit/logsumexp` and accepted-step checkpoints. two starts: uniform/zero origin coefficients; penalized multinomial fit to unblocked origins. the latter is an initializer, not evidence of representative blocked origins. initialize `u/r` intercepts with observed class log odds; other outcome coefficients zero.

require blocks, unblocked goals/non-goals and converged finite conversion/benchmark solves. failure of the unblocked-origin initializer invalidates only its start. a failed/nonfinite avoidance OR multinomial inner solve invalidates that em start; retain its preceding fully accepted checkpoint. accept an iteration only after both solves and observed-objective checks succeed. relative objective change divides by `max(1,abs(previous_objective))`; allowable decrease uses the same scale. stop only when relative objective AND maximum event-posterior total variation meet tolerance. select greatest converged penalized objective; ties retain first start. no converged start means failed fit. checkpoint origin/avoidance coefficients; reject mismatched data/config/code/state.

## reference, predictions and benchmarks

target/reference season is the latest selected training season and must supply eligible attempts. save empirical JOINT shooter–goalie frequencies `ρ(s,g)` from those attempts, each block counted once. history informs coefficients only. factual scoring uses saved contiguous states: `season_basis: fitted` when that season supplies eligible training rows, `unobserved` for an intermediate state without such rows, `carried_forward` for dates in later seasons using latest fitted states. record `state_season`. `score` emits unavailable rows with `season_unsupported` before the earliest state; `evaluate` retains its stricter date check below.

actor evidence is per stage: save total training count, count in the applied state season and `basis: observed_in_state|other_seasons_only|unseen`. count zero in that season with positive total means other-seasons-only, not rookie or unseen; those seasons can be later when scoring historical records within a retrospective fit. coefficient basis is fitted seasonal state or zero penalty prior mode, with carry-forward separately recorded. a shooter seen only in blocks has avoidance evidence but no conversion evidence.

```text
v_i(h) = Σ_(s,g) ρ(s,g) * u(h,x_i;s,target_season) * r(h,x_i;s,g,target_season)
opportunity_mass_i(h) = q_i(h) * v_i(h)
reference_opportunity_value_i = Σ_h opportunity_mass_i(h)
```

hold observed type/context fixed. reference environment/actors use target-season states; factual origins use the event's season basis. use one reference across players/directions. average pairwise probability PRODUCTS, not separate stage averages or logits. held-out data never changes the reference. history may change estimates, not reference-season membership. spatial expected-goal mass sums to the scalar; origin mass sums to one.

factual outputs are distinct: unblocked `r(h)`; recorded-context goals `Σ_h π_i(h)u_i(h)r_i(h)`; recorded-context unblocked `Σ_h π_i(h)u_i(h)`. the latter two omit focal location, outcome and posterior. reconciled type/eligibility are retrospective, potentially outcome-influenced measurements: these are NOT demonstrated pre-release forecasts. positive standardized block values are not calibrated against observed blocked zeros.

fit two benchmarks through the same logistic primitive/penalties and eligible rows:

- unblocked conversion: `η=μ+τ[y]+κ[t]+Σ_(j=1..5) w[t,j]*G_j+β·x+α[s,y]+γ[g,y]`, with `G=[d,a,d²,d*a,a²]`, `d=distance_to_goal/100`, `a=atan2(abs(y),89−x)/π` at the same quantized cell. six independent geometry vectors, not a shared vector plus deviations. wrist type intercept is zero.
- all-attempt goals: `η=μ+τ[y]+κ[t]+ζ[role]+β·x+α[s,y]+γ[g,y]`; wrist/F contrasts zero; no focal geometry/origins.

benchmark global intercept alone is unpenalized; ALL nonactor slopes/offsets use `ridge_benchmark`, without neighbor smoothing. actor level/change penalties match the candidate's corresponding actor family. order coefficients as displayed: intercept, nonreference seasons, type contrasts, type-major geometry (unblocked) or role contrasts (all-attempt), fixed scalar design order, shooter-major seasonal states, goalie-major states. save that order; use it identically for fit and prediction.

reuse stable log loss, brier, fixed calibration bins and per-game sums. additionally calibrate marginal unblocked probability against observed unblocked labels; no third benchmark. shared probability summaries name `outcome: goal|unblocked`; use `observed_positive_count` in totals/bins rather than labeling unblocked counts as goals. summarize by season, score bucket, role, home/away, canonical type AND model group, recent/none context and stage actor/season basis. remove the old unblocked-only type filter. empty groups retain null rates. observed-record likelihood comparisons require matching quantization/population/observation definitions.

`evaluate` retains disjoint, strictly later game/date checks for chronological transfer. held out from this fit does not mean untouched research confirmation: all three seasons have been examined. 03e must specify any different assessment design before changing this command contract.

## api, artifacts and resource bounds

retain `hockey-stats-chance fit --selection --config --out [--resume]`, `evaluate --selection --model --out`, `score --selection --model --out`. retain `prepare`, `fit_model`, `prediction_context`, `predict_attempt` ownership. change `reference_probabilities(model, attempt, cell_ids, context)` to return values in requested cell order for that attempt's type/scalar context. `score_attempt(model, attempt, context)` requests all cells for a block or its one proxy cell otherwise; remove the old cli-wide score×cell matrix. `prediction_context(model)` owns bounded in-memory exact reference reuse keyed by type/scalar context and cell, plus existing numerical state; no persisted cache artifact.

config schema 2 is exact: `schema_version` and these numerical keys. features/groupings/grid/season rules are fixed by `chance-2`.

```text
kernel_distance_ft, kernel_direction_strength
ridge_origin_base, ridge_origin_factor, smooth_origin
ridge_cell, ridge_type_cell, smooth_cell, ridge_context, ridge_benchmark
ridge_shooter, change_shooter, ridge_goalie, change_goalie
optimizer_max_iterations, optimizer_ftol, optimizer_gtol
em_max_iterations, em_relative_tolerance, em_posterior_tolerance
objective_decrease_tolerance
```

finite numbers; reject booleans. positive except smoothing/direction/change strengths may be zero; iteration limits positive integers. fixture config: distance `20`, direction `4`, all penalties `1`, optimizer limit `1000`, `ftol=1e-10`, `gtol=1e-6`, em limit `500`, relative tolerance `1e-8`, posterior tolerance `1e-6`, decrease tolerance `1e-10`. these exercise software, not a real recipe. explain numerical adjustments without selecting attractive fixture predictions.

| artifact | change; retain provenance/completion behavior |
|---|---|
| `fit.json`, `model.json` | schema 2, `model_kind: chance-2`; ordered features/categories, seasons, origin/stage/benchmark coefficients/penalties, actor counts by stage/season, target reference ids/counts/weights and diagnostics. model alone suffices to score |
| `checkpoint.json` and numerical state | schema 2; existing exact input/config/implementation binding and accepted origin/outcome state |
| evaluation json | schema 2; `all_attempt_recorded_context` replaces `all_attempt_outcome_blind`; add marginal unblocked calibration, conditioning, source/model inclusion and goal counts; no scientific pass/fail |
| `attempts.jsonl` | schema 2; existing identity/source/interval fields plus `credited_scorer_id`, `model_shot_type`, `previous_event`, `context`, `season_basis`, `state_season`, stage-specific actor evidence and new reasons; `shot_type` remains canonical; nullable origins/values for unavailable rows |
| `score.json` | schema 2; exact quantity/reference/conditioning, identities and reconciled per-game coverage; written last |

retain `purpose: fixture_exercise|research` and `scientific_assessment: not_performed`. fixture models cannot become research. reject malformed/unknown schemas/configs/partial artifacts; retain finite json, exclusive outputs and existing exits. remove superseded chance-1 layouts/strata/metric paths from the active workflow. historical 03b assessment is not rerun through the new model; 03e adapts retained scientific comparisons under its own protocol.

aggregate sufficient counts over actual categorical combinations; bound cell/event/actor-pair batches. never materialize attempt×cell×feature or event×cell×reference-pair tensors. compute exact reference values only for needed context/cell combinations with bounded reuse. full block posteriors retain all cells. no pruning, pair subsampling or undocumented interpolation. richer context may make exact scoring expensive; measure runtime/memory/artifact size. 03e owns full-corpus cost and any separately reviewed approximation.

## implementation ownership and content

| owner / files | non-overlapping responsibility |
|---|---|
| evidence: `reconstruct.py`, envelope writers `cli.py` / `corpus.py` | exact type additions; extract frame rule; envelope 3 cutover. no new feed/matcher/exposure algorithm |
| preparation: `chance_data.py` | physical/type/context rules, coverage, ordered feature evidence and reasons |
| numerical: `shot_origins.py`, `chance.py` | origin maps/penalties, stages/em, benchmarks, reference, validation; reuse grid/kernel/optimizer; remove old strata |
| workflow: `chance_evaluation.py`, `chance_cli.py` | artifacts/checkpoints, labeled diagnostics, bounded scoring; no scientific decision service |
| content/verification: `fixtures/chance/README.md`, fixture selection/config json, `README.md`, `docs/research/chance-03d/verification.md` | exact usage, source facts, measured checks and labels; update fixture type facts after implementation, preserve raw bytes |

content design owns field explanations and command/report text; numerical owners own their truth. good content names outcome, conditioning, units, selection, reference and denominator; distinguishes recorded proxies/inferred distributions and numerical completion/scientific support. examples: `fit complete: candidate saved; scientific assessment not performed.` and `scoring complete: <n> valued; <n> outside scope; <n> unavailable.` say “recorded preceding-play context” and “conditional origin distribution,” not observed passes/rushes or recovered locations.

## acceptance and handoff

1. temporary installed-command integration checks: red → green → refactor → green. rebuild all 18 fixture games detached from network/hdd/shared raw; verify source/type/context/coverage facts. fit a bounded selection spanning admitted seasons, evaluate disjoint later fixtures and score the saved model. metrics are not scientific acceptance.
2. independently check reset barriers, excluded predecessors, irrelevant predecessors older than five seconds, same-clock order, nominal period ends, both-team rotations/side conflicts; own/awarded/penalty goals; missing/conflicting/new/unknown types. model-excluded goals still update scores; no fabricated actor/open-play context.
3. tiny independently enumerated synthetic calculations verify likelihood-before-log, multinomial normalization, analytic gradients, penalties/history, frozen em weights, objective accounting and joint reference averaging. assessment outcomes cannot alter saved fit/reference. for the same focal block with fixed model and otherwise unchanged admissible context, changing its coordinate may change its posterior but not its recorded-context probability; the next event's preceding-zone feature may legitimately change.
4. verify save/load and accepted-state resume equivalence, zero-observation seasons, observed/other-seasons-only/unseen actors, failed starts, invalid inputs/old versions. finite normalized masses; probability complements and `sum(opportunity_mass)==reference_opportunity_value` within absolute `1e-10`.
5. explain fixture eligibility deltas from 03c facts, with exhaustive dispositions and nonexclusive reason counts; check unchanged raw hashes. record runtime/peak memory/scored size and actual failures/resolutions; retain useful facts, delete temporary tests/dependencies.

completion permits progression to 03e assessment. its protocol must examine type/context residuals, excluded-goal selectivity, seasonal transfer, tip measurement and kernel/origin/refit sensitivity on compatible populations/fixed references. separate conditional parameter uncertainty, assumption sensitivity and independent physical-origin accuracy. 04 still needs supported values, compatible event/exposure selections and player-map sensitivity. real fitting requires separate 03e authorization.
