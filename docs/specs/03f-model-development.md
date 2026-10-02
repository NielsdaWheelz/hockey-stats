# pr03f — diagnose and screen chance-model revisions

status: **specification ready for handoff; no implementation or fitting performed in this documentation phase.** 03e merged in `a8b1de8`; its [withheld decision](../research/chance-03e/decision.md) remains unchanged. this is a new, bounded development round. [brief](../brief.md) · [plan](../plan.md) · [03g follow-up](03g-chance-assessment.md)

## target and boundary

explain where the current model overpredicts and measure whether richer recent context or a different history policy improves its observable components. finish with an attributable recommendation, including `no_revision_identified` when appropriate. do not require a winner to complete the pr.

03e trained on 1,912 games, 181,147 eligible attempts and 7,614 goals: approximately 1.46 seasons. shot type, short preceding-event context, game context, spatial maps and seasonal actors already enter. a small number of input concepts produces a substantial parameter count. neither additional seasons nor additional features is an established remedy.

the failed quantity integrates over origins without the focal location: `P(goal | recorded context, actors) = Σπur`. the product's opportunity value instead retains observed/imputed location and standardizes modeled execution. failure of the first warns about the shared model; it does not directly measure player-value bias. passing it would not establish physical-origin accuracy.

**included:** saved-model diagnosis; independent component fitting/prediction; a fixed twelve-cell experiment with ten new solves; a readable comparison and next-revision recommendation. **excluded:** joint em fits, new origin/avoidance laws, opportunity scoring, 04 handoffs, acquisition, older-corpus admission, new source parsers, coordinate correction, player attribution, publication, website work and a lasting test harness. [03g](03g-chance-assessment.md) owns the selected model revision and its assessment.

## evidence and chronology

use the shared local raw corpus `/Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930` and compatible admitted corpora/artifacts under `/Users/nnandal/Documents/code/hockey-stats-03e-runs`. no hdd is required. resolve models through `inputs/development-evidence.json` and linked assessment identities; do not guess artifact filenames. preserve all old bytes. new artifacts belong under `/Users/nnandal/Documents/code/hockey-stats-03f-runs`, outside git; research notes/figures belong in `docs/research/chance-03f/`.

write `protocol.md` before new scientific fits or prediction inspection. bind the specification/code revisions, actual selection/configuration digests, fixed matrix, feature order, comparisons and numerical limits. all seasons are already research-exposed; freezing this round is not fresh confirmation. diagnoses beyond the named groups remain explicitly exploratory. no adaptive additions or replacement recipes within this round.

| window | baseline/context training | history-ablation training | assessment |
|---|---|---|---|
| `development` | 2023–24 plus 2024–25 games before `2025-01-01` | the same pre-january 2024–25 games only | remaining 712 games of 2024–25 |
| `season_transfer` | complete 2023–24 and 2024–25 | complete 2024–25 only | complete 2025–26 |

reuse 03e's selections where identical; derive the two history selections from their game ids. use canonical dates and whole games, including zero-contribution games. assessment dates must follow training dates and ids must be disjoint. verify the expected 600/712 split and season inventories; do not force counts by dropping games. this new transfer screen is not execution of 03e's stopped transfer protocol.

## 1. diagnose the existing candidate

export keyed factual predictions once for the three saved 03e development models, including their direct benchmarks, on original training and assessment selections. training results are in-sample diagnostics. reuse `prepare`, `predict_attempt` and their numerical context; **do not call reference opportunity scoring**. saved opportunity streams are not the factual probabilities being tested.

reconcile assessment counts and probability/loss sums to saved schema-3 evaluations before interpretation. retain the independently selected stronger benchmarks from 03e for historical comparisons; do not silently substitute a flattering comparator. the experiment below independently fixes anchor as its baseline.

report pooled residuals and log loss by original/model type, recent versus no recent context, recent kind/team/delay, home/away, role, calendar month, and stage-specific actor support. show the three probability quantities separately. retain counts, observed/predicted positives, exclusions and missingness. no arbitrary multidimensional search.

use the **anchor-defined** `[0.10, 0.15)` goal-probability cohort for paired candidate/benchmark diagnosis, alongside each model's own fixed bins. an error on a cohort selected by another predictor is descriptive, not automatically that predictor's calibration failure. do not select all-attempt calibration cohorts on observed block/goal status. recorded-outcome breakdowns, if useful for accounting, must carry that distinction.

answer: is the excess concentrated in a context, time period or actor-support group; does the direct benchmark share it; is it already present in training? these comparisons locate associations, not a unique cause. revisit all-attempt, conversion and marginal-unblocked evidence together; multiplying aggregate errors cannot attribute the joint failure to a component.

## 2. fixed component experiments

fit two quantities separately:

- `unblocked_conversion`: the native spatial conversion stage `r`, using eligible unblocked goals/non-goals and recorded-proxy geometry.
- `all_attempt_recorded_context`: the native direct all-attempt goal benchmark, using all eligible attempts. no focal coordinates, block outcome, current posterior or subsequent events as predictors.

| recipe | context | training history |
|---|---|---|
| `baseline` | current additive terms | full training selection for the window |
| `context_interactions` | baseline plus the 36 columns below | identical to baseline |
| `recent_history` | current additive terms | history-ablation selection for the window |

run all three recipes for both quantities in both windows: **twelve cells, two saved baseline components reused, ten new optimizer solves**. the reused cells are the anchor's `r` and `benchmarks.all_attempt` for development. no context/history combination, penalty sweep, automatic retry search or joint fit. use the exact anchor configuration from 03e, including optimizer limits/tolerances and the applicable existing penalties. retain failed numerical results; no converged component means no scientific prediction for that cell.

`context_interactions` keeps all existing main terms and adds:

1. six indicators `recent_kind=k AND recent_team=same`, for every existing kind except the reference `faceoff`;
2. thirty indicators `recent_kind=k AND recent_delay=d`, for those same kinds and `d=1..5` seconds; delay zero is the reference.

order the six owner columns first, then kind-major/delay-minor columns, following native recent-kind order. all added columns are zero when no recent action exists. unsupported context remains unavailable under existing preparation; it never becomes no recent action. use `ridge_context` for added conversion coefficients and `ridge_benchmark` for the direct benchmark. these are context interactions, **not** sustained event chains, puck trajectories or observed possession. they test the current assumption that owner/delay effects apply identically across preceding-event kinds.

`recent_history` removes one prior season. it tests incremental historical evidence under the present annual-state/shrinkage policy, including its effect on actor support. it does not isolate sample size from pooling and cannot establish whether ten older seasons would help. preserve native season carry-forward and unseen-actor semantics; do not exclude entrants or use assessment observations to fit priors. eligibility and assessment keys must be identical across recipes within each quantity/window.

## 3. comparisons and recommendation

compare each changed recipe with its same-window baseline on identical keyed observations. primary comparison: pooled mean goal log loss, in nats per applicable attempt; `delta = changed − baseline`. also report brier, predicted-minus-observed rate in percentage points, twenty fixed probability bins, named diagnostic groups and actual runtime. never combine conversion and all-attempt losses into one score; their populations and conditioning differ.

reuse 03e's paired whole-game and seven/fourteen-calendar-day bootstrap arithmetic: 2,000 draws, `PCG64`, seed `3032026`, 95% linear-percentile intervals, pooled sums/counts, empty games/days and final partial blocks retained. undefined draws yield explicit null intervals without redraws. intervals condition on fitted models and omit model-selection/fit uncertainty; report contributing games/blocks and pointwise coverage limits. do not repeat expensive fits for bootstrap draws.

negative point log-loss differences in **both** windows support proposing that named component change for further research. mixed direction means temporal instability; no improvement means no revision identified by this screen. intervals and brier/calibration changes qualify that recommendation; adverse tradeoffs must be stated, not hidden behind average loss. interval overlap with zero neither proves equivalence nor prohibits a bounded follow-up. if both alternatives improve, report both separately; an untested combination is not a winner.

show 03e's calibration margins as historical reference lines, not a new automatic admission rule. do not erase its verdict or invent universal standards from those margins. a recommendation is not a validated model. improvement in the direct all-attempt benchmark does not demonstrate an improved latent-origin model; conversion improvement does not establish better blocked origins.

the final decision labels each `(changed recipe, quantity)`: either window unavailable/nonconverged → `incomplete`; both deltas negative → `consistent_direction`; neither negative → `no_improvement`; exactly one negative → `mixed_direction`. exact zero is not improvement; mixed direction need not mean a sign reversal. these describe point estimates, not demonstrated superiority. retain exact deltas, uncertainty, limitations and the next experiment justified. map each future check to its actual claim: recorded-outcome probabilities, physical origin assumptions, standardized opportunity stability or player attribution. any later admission rule must be justified before that assessment; no new thresholds are selected here to pass the observed results.

## architecture and capability contract

one manual research entrypoint, `analysis/research/chance_development.py`; no scheduler, feature store or model registry. reuse installed python dependencies and ordinary exclusive output directories.

| command | inputs → output / responsibility |
|---|---|
| `diagnose --evidence … --protocol … --out …` | existing schema-2 03e evidence plus bound protocol → factual prediction streams, reconciled diagnostic sums and completion record |
| `fit-component --selection … --config … --quantity … --features … --protocol … --out …` | existing selection/config; quantity above; features `additive` or `recent_interactions` → standalone component artifact and solve diagnostics; zero em calls |
| `evaluate-component --selection … --component … --out …` | later selection and saved component → keyed predictions, coverage and additive per-game metrics |
| `compare --evidence … --out …` | fixed-matrix evidence index → paired metrics, bounded figures and comparison completion record; no scientific verdict from the command |

invoke with the locked environment from `analysis/`: `.venv/bin/python research/chance_development.py …`. a saved baseline component may be extracted during diagnosis; this is exact reuse, not refitting. it must retain the original model/implementation identity plus the extraction revision.

| owner / file | non-overlapping responsibility |
|---|---|
| `chance_data.py` | sole owner of source admission, eligibility, attributed context and prepared selections; no new source features in this slice |
| `chance.py` | expose `extract_component(model, *, quantity)`, `fit_component(attempts, config, metadata, *, quantity, features)` and `predict_component(component, attempt)` from existing numerical work; native fitting delegates to shared primitives. keep one implementation of geometry, penalties, actor states and logits |
| `chance_evaluation.py` | reusable binary probability/loss sums and per-game accounting; accepts component predictions without fabricated joint outputs |
| `analysis/research/chance_review.py` | existing pooled uncertainty/calendar-block arithmetic reused or narrowly extracted; retain historical review behavior |
| `analysis/research/chance_development.py` | research cli, fixed component-artifact validation, evidence pairing and report assembly |
| `docs/research/chance-03f/{protocol,decision,verification}.md` | prospective study choices, scientific interpretation, commands/resources and software evidence |

`extract_component` returns the component artifact: conversion uses `model.stages.r` with `model.diagnostics.r`; direct all-attempt uses `model.benchmarks.all_attempt` and its embedded diagnostics. `fit_component` returns `(component_or_none, diagnostics)`; a nonconverged solve yields no model. `predict_component` returns `log_p`, `log_not_p`, `season_basis`, `state_season` and `actor_evidence` for an eligible applicable row; evaluation owns non-applicable/excluded rows.

component artifacts use a distinct `artifact_kind: chance_component`, `schema_version: 1`, `purpose: research|fixture_exercise`, quantity, `feature_set`, ordered feature layout/coefficients, conversion grid identity/centers, numerical diagnostics, season/actor evidence, training ids/dates, selection/config/protocol/source identities and implementation/dependency versions. `scientific_assessment` stays `not_performed`. save only the information required to reproduce predictions; no fake `π/u`, joint reference or completed chance model. native model readers must reject component artifacts.

prediction streams key every recognized attempt by `(game_id, source_index)`; retain `event_id`, date/season, status/reasons and source identity. include excluded rows with null predictions and a complete coverage ledger. eligible rows carry quantity-specific applicability, observed binary outcome, stable `log_p`/`log_not_p`, probability, component identity, actor-state basis and frozen diagnostic descriptors. blocked rows are not applicable to conversion; they are not missing conversion outcomes or zeros. predictions cannot contain source labels as leaked features. stable log probabilities own loss arithmetic; do not clip probabilities to conceal overflow.

the schema-1 screen evidence index binds the protocol, input identities and twelve cells `(window, recipe, quantity)`, each with training/assessment selections, component/evaluation references and `reused|fitted|failed` status. failed cells retain diagnostics with null unavailable artifact references. comparison records bind it and contain counts/sums, candidate-minus-baseline metrics/intervals, coverage and resource measurements. missing/duplicate/mismatched keys, labels or source identities fail pairing; do not silently intersect cohorts. a failed cell remains visible and yields incomplete evidence, not a substituted model.

exit `0` means the requested artifact completed, not scientific approval; numerical/input/output failure is nonzero. use existing argument/output/error conventions. write completion records last. interrupted cheap component solves may be rerun explicitly; no new recovery engine. preserve 03e's expensive fits/checkpoints. keep native chance-2 schemas and baseline prediction meaning intact; this is a distinct research capability, not a legacy compatibility dispatcher. any later joint-model cutover belongs to 03g.

## content, verification and completion

the scientific content designer owns a short decision page: the question; training/assessment populations; a twelve-cell results table; paired loss/calibration figures on common axes; and a plain-language recommendation with unresolved mechanisms. labels must identify observed outcomes versus predictions, in-sample versus later-game checks, percentage points versus percentages, and component improvement versus model admission. use at most three figures; numeric evidence remains authoritative. no player cards or maps suggesting physical-origin certainty.

temporary integration checks follow red → green → refactor → green, then delete all test code/test-only dependencies. retain analytical commands, fixtures and factual verification notes. verify these behaviors, not every helper:

1. extracting saved baseline components reproduces native eligible predictions within absolute `1e-12`: conversion matches `predict_attempt(...).candidate_r`; direct all-attempt matches `.benchmark_all`, not the composed `.candidate_all`. reconcile recorded counts/sums at the existing review tolerance; diagnosis uses factual probabilities, not opportunity values.
2. fixture component fit → reload → later-game prediction → comparison works without em/reference scoring; independent arithmetic verifies the 36 contrasts and meaningful objective/gradient cases.
3. future/overlapping training games, altered event identities, changed labels and cohort mismatch fail; unavailable/no-recent context and unseen actors retain their distinct meanings.
4. paired pooling matches hand calculations with unequal game counts, zero-contribution games, calendar boundaries and undefined draws; input bytes remain unchanged.
5. the local detached study accounts for all twelve cells, reports failures honestly, preserves 03b/03e decisions and produces no native handoff/publication.

run a fixture capacity check before full component solves; record wall time, peak memory and artifact size. these fits avoid em but are not promised instantaneous. run sequentially; report unexpectedly costly work instead of quietly increasing limits or launching parallel campaigns. independent statistical/systems review challenges the frozen matrix before fitting and the final interpretation afterward; content review checks that figures/text support the same claims. preserve newly discovered distinct broken-game evidence under the existing fixture policy.

## retained questions and material tradeoffs

| question / cost | owner and disposition |
|---|---|
| sustained sequences and shift age | 03f records source feasibility/missingness from existing reconstruction evidence; 03g selects them only if justified. membership at two events does not prove continuous presence between them |
| calendar rest, cumulative game workload, current shift age | distinct concepts; 04 retains deployment/rest ownership unless a revised chance hypothesis needs one earlier. no generic fatigue variable |
| older seasons or annual spatial/context evolution | 03f measures the bounded history ablation; 03g decides whether additional admission or a different pooling model is warranted. archive bytes remain unadmitted |
| handedness, rink effects, coaches, setters, tip/block geometry | retain [input-audit](../research/model-input-audit.md) and issue ownership; none is silently added or declared irrelevant |
| limited experiments | isolates two questions without an exhaustive search; no claim that rejected or omitted alternatives cannot work |
| screening before joint revision | adds a small research boundary while avoiding another speculative hours-long em campaign; component gains may not transfer to opportunity/player estimates |
| exposed seasons and uncertainty | supports retrospective development recommendations, not untouched confirmation or publication |

[hockeyviz xg8](https://hockeyviz.com/txt/xg8) motivates differentiated recent context, historical information and testing proposed terms; its seasonal fits/priors and shot-sequence definitions differ from ours. [magnus9](https://hockeyviz.com/txt/magnus9EV) places rest and shift-start effects in player shot-rate attribution. these references motivate hypotheses, not automatic feature inclusion or parity claims.
