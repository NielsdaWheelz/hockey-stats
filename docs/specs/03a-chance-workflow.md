# pr03a — chance-model workflow

status: specification, 2026-09-29; no implementation authorized in this phase. 02c is reviewed and merged. the user chose local evidence now, historical admission later, and a separate **03b for real training and scientific acceptance**. [brief](../brief.md) · [architecture](../architecture.md) · [03b boundary](03b-training-acceptance.md)

## target and limits

one offline python entry point provides fit, evaluate and score for a specified all-attempt chance-model candidate. it includes blocked attempts through distributions of inferred origins. three admitted games exercise the software; they cannot establish credible chance values. no website, publication, player attribution, historical importer, automatic model selection or acceptance service.

the candidate has two conditional stages: avoiding a block, then scoring given an unblocked attempt. nuisance shooter/goalie terms support a common conversion reference; they are not new player-card components. this is our candidate, not a reproduction of hockeyviz's private model. scientific limitations and source evidence are recorded in [statistical methods](../research/statistical-methods.md#pr03-candidate-and-information-boundaries).

03a delivers the complete numerical recipe below, two small benchmarks, reusable evaluation, attributed artifacts and meaningful temporary verification. 03b may reject or revise this candidate. no scientific acceptance follows from convergence or green software checks.

## command and input contract

one entry point, `hockey-stats-chance`, with three subcommands:

```sh
hockey-stats-chance fit --selection train.json --config candidate.json --out fit-directory
hockey-stats-chance evaluate --selection assessment.json --model fit-directory/model.json --out assessment-output.json
hockey-stats-chance score --selection scoring.json --model fit-directory/model.json --out scored-directory
```

`fit` trains the candidate and both benchmarks on its selection only. `evaluate` and `score` load the saved fit; neither refits, recalibrates nor retunes anything. scoring may include training games for retrospective analysis. assessment requires disjoint game ids and game dates strictly after the latest training date; keep whole dates together because the admitted inventory supplies dates, not a reliable within-day chronology.

selection schema: `{schema_version: 1, purpose: fixture_exercise|research, corpora: [{path, game_ids}]}`. `path` identifies an existing 02c `corpus.json`, relative to the selection file or absolute; `game_ids` is a nonempty explicit list of inventoried ten-digit string ids. reject duplicate ids across the entire selection, unknown ids and incompatible schemas. missing selected captures remain missing evidence. no directory discovery, date-query language or silent fixture substitution. retain selected, unselected, missing, excluded and usable game/attempt counts separately; a selection of three games is not a full-season corpus.

read corpus schema 1 and its referenced reconstruction envelopes (schema 1, interpreted schema 2), one game at a time. only `reconstructed` rows supply analytical records. selected `missing_capture` and `identity_unavailable` rows remain distinct evidence gaps; selected `input_error` or `identity_mismatch` rows stop the command with exit 1 and their located reason. do not import such failures as missing captures. bind envelope identities to the inventory row; require a unique reconstruction row for each interpreted event used. malformed files, broken references or identity contradictions are input errors, not ordinary missingness. hash the actual selection, config, corpus and consumed game files; retain their paths and digests. use the embedded source provenance without reopening raw captures or requiring their original drive paths. no changes to 02c's schema or reimplementation of interpretation/reconstruction.

all flags occur once; reject unknown/abbreviated arguments. outputs must be new, with existing parents, outside input directories. reuse strict finite-json reading, existing identity reporting and exclusive writing. syntax/help exits 2/0; local input, numerical or filesystem failure exits 1. programming errors surface. ordinary evidence gaps permit exit 0 when the requested artifact is complete; numerical failure never produces a usable model. no-overwrite applies to every command.

## source-derived preparation

join by `(game_id, source_index)`, not a guessed timestamp. retain event id, report row, interval indices and source issue links. a recognized attempt has `kind_valid: true` and `type_key` in `blocked-shot/missed-shot/shot-on-goal/goal`. emit one output row per recognized attempt, including exclusions; unclassifiable source records are counted separately, never assumed to be non-attempts. ordinary reason codes are `outside_5v5`, `membership_unresolved`, `actor_unavailable`, `location_unavailable`, `score_unavailable`; preserve all applicable reasons and their source details, rather than returning only the first missing field.

| requirement | treatment |
|---|---|
| population | completed regular-season game; supported timed `five_on_five` event with both reported goalies. known other situations/penalty shots/shootouts are `out_of_scope`; unresolved membership is `unavailable` |
| actors | shooting team established; unique roster-resolved shooter (`scorer` for goals, `shooter` otherwise) belongs to that team; opposing reported on-ice goalie supplies goalie identity. conflicts or missing required identity are unavailable |
| role | game-roster `C/L/R/F` → `F`, `D` → `D`; unsupported/missing position → `unknown`. current bios do not establish historical role |
| locations | normalized attacking frame, goal at `(89, 0)` feet. preserve reported and normalized coordinates; recorded unblocked locations are origin proxies, blocked locations are block evidence. missing/frame-ambiguous/out-of-rink locations are unavailable; no clipping or invented coordinates |
| score | goals already completed before the attempt, from the shooting team's perspective: trailing/tied/leading. begin 0–0; count valid timed goals at every strength, excluding shootouts. process unique `sort_order`, requiring coherent period/elapsed-time order; read the score BEFORE applying the current goal |
| score support | require fully classifiable goal accounting and existing play-by-play and boxscore `timed_goals` checks both with status `match`. missing/conflicting goal ownership, clocks or ordering withhold this covariate for the game; attempts requiring it are unavailable. never substitute tied or use a goal's post-event score as its predictor |
| interval linkage | preserve it, but do not require it to value an otherwise supported event. 04 must reconcile event and exposure populations before estimating rates |

source accounting checks use later game evidence to establish retrospective completeness; they do not introduce future goal counts into predictors. assess the selectivity of this eligibility rule in 03b. missing role has an explicit origin stratum; missing score or coordinates does not. tips/deflections retain their recorded proxy with a diagnostic tag, not an unvalidated relocation.

omit shot type from both stages initially: in these captures its absence identifies a blocked outcome. also omit current block reason, assists, outcome/missingness flags and post-goal score as predictors. observed block status/location belong only to the observation likelihood and retrospective origin inference. previous-event context, handedness, age, rink effects and coach terms are not required by this first candidate; 03b must examine consequential omissions before acceptance. retain their source evidence for later work.

## numerical contract

the following fixes the implementation; scientific tuning remains 03b's work. use float64 arrays and library optimizers, not a new modeling framework.

**geometry.** use a 5-foot square grid over a 200-by-85-foot rink with 28-foot rounded corners. candidate centers are `x = -97.5 + 5i`, `i=0..39`, and `y = -40 + 5j`, `j=0..16`. retain centers satisfying `max(abs(x)-72,0)^2 + max(abs(y)-14.5,0)^2 <= 28^2`, within the rectangle. order by increasing x then y; zero-based index is `cell_id`. map an in-rink point to the nearest retained center, breaking ties by id. this is quantization of a recorded proxy, not sub-cell accuracy. cardinal neighbors are retained centers exactly 5 feet apart. no left/right folding.

let `h` be an origin cell, `b` a block cell, `c` the pre-event score category, `s` the shooter and `g` the goalie. `z=(role,c)` has nine strata. `π_z(h)` is the origin distribution before the outcome. `u` and `r` are logistic probabilities:

```text
logit u(h,c,s)   = intercept_u + cell_u[h] + score_u[c] + shooter_u[s]
logit r(h,c,s,g) = intercept_r + cell_r[h] + score_r[c] + shooter_r[s] + goalie_r[g]
```

tied is the score reference (coefficient zero). every cell, actor and other score coefficient has positive ridge penalty; intercepts are unpenalized. add squared neighbor differences for cell smoothness. all effects are plug-in estimates. an actor absent from a stage's evidence receives coefficient zero, the penalty prior mode, explicitly flagged; this is **not** a league-average probability. retain stage-specific counts, including shooters seen only in blocked attempts. no coefficient gets a published skill interpretation here.

**block observation law.** fix each candidate kernel before fitting:

```text
log w(b,h) = -distance(h,b)/kernel_distance_ft
             - kernel_direction_strength * (1 - cos(theta))
K(b|h) = w(b,h) / sum_over_block_cells w(b,h)
```

`theta` is the angle between origin→block and origin→goal. for the same cell, set its angular penalty to zero. compute normalization in log space. `kernel_distance_ft` must be positive, direction strength nonnegative. this forward law normalizes over possible block locations for each origin; reversing the normalization creates a different model. its soft directional preference avoids brittle trajectory exclusions, at the cost of admitting some implausible paths. kernel parameters are not jointly learned with the latent origin law.

**observed likelihood.** an unblocked attempt has recorded origin cell `h` and goal label `y∈{0,1}`; a blocked attempt has observed block cell `b` and unknown origin:

```text
unblocked: π_z(h) * u(h,c,s) * r(h,c,s,g)^y * (1-r(h,c,s,g))^(1-y)
blocked:   sum_h π_z(h) * (1-u(h,c,s)) * K(b|h)
```

sum over latent origins BEFORE taking the log. do not fit a regression to one guessed block origin or substitute a posterior-weighted average of log likelihoods for the observed likelihood. conditional independence of block location from actors/context given origin and the fixed kernel is a substantive assumption, not a source fact.

maximize the summed observed log likelihood, minus `0.5 * ridge * sum(coefficients^2)` for each coefficient group, minus `0.5 * smooth * sum_neighbor_pairs(cell[h]-cell[k])^2`, plus `origin_pseudocount * sum_z,h m(h)*log π_z(h)`, where `m` is uniform over retained cells. penalty scales refer to the summed objective, not a silently averaged loss.

1. fit `r` once on unblocked records. it does not enter blocked likelihoods.
2. fit `π/u` by em. unblocked origins have point mass at their recorded cell. for a block, `q_h ∝ π_z(h)*(1-u(h,c,s))*K(b|h)`; normalize with log-sum-exp.
3. update `π_z(h)=(expected_count_z,h + origin_pseudocount*m(h))/(count_z + origin_pseudocount)`. this is the map update under `Dirichlet(1 + origin_pseudocount*m)`. an empty stratum remains uniform. update `u` by penalized weighted logistic regression. a block's fractional rows have total weight one. every inner objective/gradient call uses the SAME preceding e-step weights; batched recomputation uses frozen old parameters, never the optimizer's trial coefficients.
4. use two deterministic starts: uniform `π`, and stratum-specific unblocked cell frequencies shrunk by the same pseudocount. initialize outcome intercepts from training proportions and other coefficients at zero. retain both starts' diagnostics; choose the converged fit with highest penalized observed objective, tie favoring uniform. no claim of a global optimum.

use scipy `minimize(method="L-BFGS-B")` with analytic gradients and stable `log_expit`/`logsumexp`. successful inner optimization and finite parameters/objectives are required. em must not decrease the same penalized observed objective beyond its numerical tolerance; require relative objective change and maximum posterior-weight change below the configured tolerances. reaching the iteration limit is failure, not convergence. require training evidence of blocks, unblocked attempts, unblocked goals and unblocked non-goals. do not change labels or invent pseudo-observations to satisfy this requirement.

**two benchmarks, trained and saved in `fit`.** both use the same source eligibility and ridge-penalized logistic fitting primitive. the unblocked benchmark predicts goals from intercept, distance-to-goal/100 and `atan2(abs(y),89-x)/π`, using the same quantized origin as `r`. the all-attempt benchmark uses intercept, score (tied reference) and role (`F` reference). benchmark slopes have positive ridge; they are factual prediction checks, not alternate published opportunity values.

## reference opportunity and evaluation

save `ρ(s,g)`, the empirical joint shooter–goalie pair distribution weighted by eligible training attempts, counting each block once. use this same fixed reference for every player and both directions. pooling seasons weights their included attempts equally; it assumes comparable conversion conditions and is subject to 03b's horizon/reference assessment. do not silently recalculate the reference when scoring a new selection.

```text
p_reference(h,c) = sum_(s,g) ρ(s,g) * u(h,c,s) * r(h,c,s,g)
value_cell[h]    = q_h * p_reference(h,c)
reference_opportunity_value = sum_h value_cell[h]
```

origin weights have units of attempt mass and sum to one. `opportunity_mass` and `reference_opportunity_value` have units of expected goals for this attempt; cell contributions sum to its value. for unblocked attempts `q` is the recorded proxy's point mass; for blocks it is the fitted factual posterior above. average the PRODUCT for each pair, not separately averaged stage probabilities or logits. do not score the mean origin or multiply every origin weight by the already-averaged event value. this standardizes conversion terms while leaving supported event context and reconstruction evidence explicit; it does not establish causal isolation.

the value reconstructs a reference opportunity after observing the attempt. it can be positive for an actual block, whose factual probability of having scored after the block is known is zero. do not call this reconstructed value a forecast or test it against blocked zeros as if it were one.

`evaluate` reports three distinct quantities, always naming the population and information:

| quantity | comparison / metrics |
|---|---|
| factual `r` on unblocked attempts | distance/angle benchmark; per-attempt log loss, brier score and calibration |
| factual all-attempt `sum_h π_z(h)*u*r` | score/role benchmark; same metrics. both exclude current location, block outcome and inferred origins; this checks an outcome-blind marginal probability, not location reconstruction |
| observed-record likelihood above | mean negative log likelihood for the fixed observation grid/law; report blocked/unblocked counts and contributions separately. likelihoods under different quantizations are not directly comparable |

compute log loss and marginal likelihood directly from stable log-domain predictions, not `log` of rounded probabilities or arbitrary clipping. calibration bins are fixed `[0,.05), [.05,.10), …, [.95,1]`; report count, summed predicted probability and goals, with null rates for empty groups. retain per-game metric sums/counts for later game-clustered comparisons. summarize by season, score, role, home/away, actor evidence (seen/unseen per stage), and recorded unblocked shot type; sparse/empty groups remain visible. no auc requirement, bootstrap engine or automatic statistical pass/fail. inputs, exclusions and conditioning must match between candidate and benchmark. selection/input failures produce no successful assessment; an empty eligible population produces explicit `insufficient_evidence` and null metrics, not zeros.

03a provides conditional point estimates and origin mass, not fitted-parameter confidence intervals or total uncertainty. 03b owns meaningful calibration tolerances, kernel/prior sensitivity, source-semantic spot checks, selective-missingness assessment and the decision whether these values support 04. those are retained scientific work, not disposable software tests.

## configuration, artifacts and composition

`candidate.json` contains `schema_version: 1` and only these numerical fields: `kernel_distance_ft`, `kernel_direction_strength`, `origin_pseudocount`; `ridge_cell`, `ridge_score`, `ridge_actor`, `smooth_cell`, `ridge_benchmark`; `optimizer_max_iterations`, `optimizer_ftol`, `optimizer_gtol`, `em_max_iterations`, `em_relative_tolerance`, `em_posterior_tolerance`, `objective_decrease_tolerance`. iteration limits must be positive integers; booleans are not numbers; all numbers finite; ridge/pseudocount/distance/tolerances positive, smoothness/direction nonnegative. use the same configured penalties for both stages. reject extra/missing keys rather than invent defaults. the 5-foot grid and feature definitions are fixed model version `chance-1`, not a plugin configuration language.

include one explicitly labeled fixture configuration: distance 20 feet, direction 4, pseudocount 10, ridge cell/score/benchmark 1, ridge actor 10, smoothness 10; optimizer limit 1000, `ftol=1e-10`, `gtol=1e-6`; em limit 500, relative tolerance `1e-8`, posterior tolerance `1e-6`, relative objective-decrease tolerance `1e-10` against `max(1,abs(previous_objective))`. these are numerical exercise choices, not accepted scientific defaults. changes needed for numerical verification must be explained in its record; do not tune fixture metrics to look credible.

| output | contract |
|---|---|
| `fit-directory/fit.json` | schema 1; implementation, input/config identities, resolved game selection/dates, preparation coverage, stage-specific actor counts, per-start convergence/termination/objective history, chosen start or null, `status: fitted|failed`, `scientific_assessment: not_performed` |
| `fit-directory/model.json` | written last, only after the candidate and both benchmarks pass numerical checks; schema 1, `model_kind: chance-1`, purpose, implementation (including numpy/scipy versions and lockfile digest), exact config/input identities/training ids/dates, grid centers/order/neighbors, feature/category/actor order and stage-specific evidence counts, both stages' coefficients, nine origin probability arrays, kernel parameters, joint reference ids/weights, both benchmarks' coefficients and numerical diagnostics. sufficient to score without training inputs or `fit.json` |
| assessment output | schema 1; model digest, assessment input identities/selection, purpose, prediction definitions, coverage/exclusions, metrics and per-game sums, `status: evaluated|insufficient_evidence`, `scientific_assessment: not_performed`. evaluation measures behavior; 03b's written scientific judgment is separate |
| `scored-directory/attempts.jsonl` | schema 1 per row; `(game_id, source_index)`, nullable event/report ids, interval indices, shooting team/shooter/goalie, pre-event score and role, source issue links, recorded/normalized coordinates and location kind, `status: valued|out_of_scope|unavailable`, stable reason codes, actor evidence counts/basis, nullable `origin_basis: recorded_proxy|inferred_block`, nullable `origin_distribution: [{cell_id, weight, opportunity_mass}]`, nullable `reference_opportunity_value`. `opportunity_mass` is `weight * p_reference(cell,score)`, not a probability to weight again |
| `scored-directory/score.json` | written last; schema 1, model digest, purpose, input identities/resolved selection, same geometry/reference definitions, counts by status/reason/origin basis and per-game coverage, attempts filename and digest, `scientific_assessment: not_performed` |

undefined values are null, never zero; explanations accompany reason codes. unavailable event rows do not erase the inventory or missing-game ledger. counts partition known attempts, separately from unclassifiable source rows. model fields have explicit array dimensions/orders; validate finite numbers, normalization, identity uniqueness and dimension agreement on load. read supported schema/model versions only; no pickle, migration or fallback reader. artifact purpose `fixture_exercise` cannot be relabeled `research` by a scoring/assessment selection.

use ordinary finite json for the modest fitted arrays. jsonl bounds scored-output writing; dense origin distributions cost disk, deliberately retaining mass rather than truncating to top cells. compute em responsibilities in bounded attempt batches, aggregate sufficient counts/gradients and recompute when needed. never materialize attempt×cell×coefficient or attempt×cell×reference-pair tensors. precompute the exact reference probabilities over cells and score states with bounded pair batches. no arbitrary mass pruning or second scientific implementation in effect.

`fit.json` is diagnostic; the last-written, fully decodable `model.json` is the fit's success artifact. score completion requires the last-written `score.json` and its matching attempts digest. a failed numerical run saves diagnostics without a model; interrupted partial artifacts are not successful outputs. manually remove cheap partial work and rerun into a new directory. subsequent evaluation failure cannot destroy a completed fit. no iteration checkpoint/resume system in 03a; 03b measures fit cost before deciding whether interrupted-fit recovery warrants a small checkpoint. completed fits are preserved because recreating them may be expensive.

## files and review boundaries

| files | sole responsibility |
|---|---|
| `analysis/src/hockey_stats/chance_data.py` | selected corpus/envelope reading, identity/digests, eligibility, pre-event context and coverage; no numerical fitting |
| `analysis/src/hockey_stats/shot_origins.py` | grid, fixed forward kernel, origin probabilities/posteriors and normalized mass; no acquisition or application state |
| `analysis/src/hockey_stats/chance.py` | shared penalized logistic primitive, candidate/benchmark fitting, saved model validation, reference averaging and attempt scoring |
| `analysis/src/hockey_stats/chance_evaluation.py` | retained probability scores, calibration and grouped scientific summaries using the same fitted predictors |
| `analysis/src/hockey_stats/chance_cli.py`, `analysis/pyproject.toml`, `analysis/uv.lock` | thin subcommand composition and exact numerical dependency pins; reuse `cli.Once`, `captures.strict_json`, `InputContractError`, `artifacts.implementation_identity` and `write_json` |
| `fixtures/chance/README.md`, `fixtures/chance/*.json`, `README.md` | bounded selections/configuration, hand-checked facts and actual invocation. derived outputs stay under ignored `var/`; existing capture bytes remain unchanged |

use numpy `2.5.3` and scipy `1.18.1`, subject to locked installation verification on the existing python 3.14/mac arm64 environment. these [numpy](https://pypi.org/project/numpy/2.5.3/) and [scipy](https://pypi.org/project/scipy/1.18.1/) releases provide matching wheels. no scipy-version compatibility layer, stan runtime, scikit-learn dependency or handwritten optimizer is needed. scipy supplies the [optimizer](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html); our code owns the likelihood, not the optimization algorithm.

the content designer owns command summaries, output field descriptions and fixture annotations. good content names the quantity and population, distinguishes recorded proxies from inferred origins, reports actual convergence/gaps and points to detailed evidence. it never announces “validated model,” “software verified,” or causal player skill because one command completed. examples for the three separate invocations:

```text
fit: fixture exercise; converged; saved to <path>
training: <n> games; <n> eligible attempts; <n> unavailable
scientific assessment: not performed

assessment: fixture exercise; <n> held-out games
unblocked conversion: <n> attempts; <metrics>
all-attempt outcome-blind prediction: <n> attempts; <metrics>
scientific assessment: not performed

score: fixture exercise; saved to <path>
values: <n> supported; <n> unavailable; <n> outside scope
origins: <n> recorded proxies; <n> inferred distributions
scientific assessment: not performed
```

## acceptance and adversarial checks

1. temporary installed-command integration checks establish red → green → refactor → green. derive a corpus from the existing three captures, fit the two october games, evaluate the march game and score all three offline without the hdd. fixture purposes and missing-season coverage remain visible. no fit/metric threshold is evidence of scientific acceptance.
2. independently check selected pre-goal scores (including non-5v5 goals), shooter/goalie identities, block ownership and origin-proxy distinctions. fixtures contain 362 timed attempts, including 273 classified 5v5 before additional model eligibility; never assert that all 362 are fit rows. retain the known unresolved reconstruction evidence.
3. small hand-calculated synthetic examples verify the marginal likelihood, posterior normalization, em objective accounting, fractional count conservation, exact joint reference average and `sum(opportunity_mass)==reference_opportunity_value`. check analytic gradients against finite differences at a few nonsingular points. these verify our implementation, not nhl origin accuracy.
4. verify train/save/load/score equivalence, no refitting or changed bytes during assessment/scoring, unchanged raw fixtures, and assessment overlap/date rejection. demonstrate that modifying held-out outcomes cannot alter saved coefficients/reference/kernel, while changing observed block evidence may change retrospective origin weights.
5. exercise missing locations/score/actors, unknown role, unseen stage actors, missing selected games, all-one-class training, one failed em start, all starts failed, malformed artifacts, existing outputs and interrupted writes. failures/gaps must follow the stated contract without default tied scores, fabricated locations, partial usable models or silent population changes.
6. numerical invariants: finite parameters and metrics; probabilities in `[0,1]`; normalized kernel/origin/reference weights; event/spatial value conservation within absolute `1e-10`. inspect local runtime/peak memory and recorded termination before calling the workflow usable. real-corpus resource and scientific sufficiency remain 03b's responsibility.
7. after verification, delete all temporary tests/scripts/test-only dependencies. retain fixture facts, concise verification evidence, production input/numerical validation and the scientific evaluation implementation. review mathematical validity, artifact reproducibility and operator wording separately; do not leave competing numerical paths or generic scaffolding.

material costs are explicit: a joint latent model is more work than plugging guessed origins into regression, but makes the outcome-dependent observation process inspectable. a coarse grid and two stages limit resolution and mechanism detail. omitted context and prior-mode unseen actors may impair calibration; reference averaging does not remove every skill proxy. kernel/regularization choices can change spatial conclusions despite similar observed-data fit. jsonl costs space; restarting an interrupted fit costs time. 03b must measure these limitations and can reject the candidate. none authorizes a larger operating platform or an unsupported player claim.
