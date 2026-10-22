# complete experimental player analysis

full implementation contract. [the plan](../plan.md) owns assignment; this specification assigns no execution. read the three normative appendices with this page: [chance/execution and goalies](experimental-chance.md), [spatial attribution and value accounting](experimental-attribution.md), [publication and application](experimental-application.md). together they replace the coordinating stub and the implementation-detail placeholders in 05/06. frozen protocols and verdicts remain unchanged.

## target and limits

deliver the complete selected [player-analysis inventory](../product-inventory.md) with real, coherent, explicitly experimental estimates. extend one application: source → local python → sqlite → effect → react. integrate useful families continuously; a missing family leaves the program incomplete, not the website unusable. weak scientific performance directs iteration. incorrect calculations, failed solves and invented evidence are not estimates.

the headline describes underlying level across a regular season. fit **2021–22 through 2025–26** chronologically; publish the last three annual states beside existing observed results. earlier displayed states cannot consume later responses. these seasons are research-exposed; in-sample displays and retrospective checks are not forecasts or untouched validation.

## settled choices

| choice | contract and cost |
|---|---|
| headline | league-relative component value, replacement-relative value alongside |
| replacement | roster-depth proxy outside each team's top twelve forwards/six defensemen by regular-season usage; exact pooling in the attribution appendix. injuries, trades and deployment contaminate it; this is not available replacement labor |
| reference xg | virtual shooter/setter/goalie with zero residual execution terms; retain circumstances and inferred setup state. exact and cheap, but **not** average probability across actual players. supersedes the older empirical matchup reference only for this product |
| spatial basis | forty retained graph modes on the existing native grid, positive complete rates. finer patterns cost more nonlinear fitting and are not automatically well resolved |
| headline workload | 1,000 minutes 5v5 + 100 pp + 100 pk for every skater. show opportunity and prior dominance; hypothetical specialty minutes are not accumulated season value |
| uncertainty | point estimates; `not_estimated` means no interval, zero-width band or reliability badge. no nested-refit campaign |
| breadth | compatible groups fitted jointly; fixed initial priors and explicit inference buy complete behavior before optimal calibration. retain correct inactive encoders |
| interface | same-kind comparisons; three-season trajectories; no interactive refits, arbitrary date-window estimates, paid feeds, playoffs or additional historical acquisition |

the ten-term total is a defined component index, not war, a forecast or credit for actual goals. goalie aggregate/replacement value and exact quality-start/consistency fields remain unselected candidates. no causal isolation or exact private-model parity claim.

## a. evidence and preparation

use the five admitted selections and corrected 02d support. preserve raw bytes, existing observed meanings and frozen research ledgers. product artifacts use a new strict contract; reuse native facts instead of reimplementing interpretation per model.

| input | initial implementation / authoritative owner |
|---|---|
| geometry, type, blocks | existing normalized frames/types/grid; chance owner supplies inferred-origin mass. block contacts never become observed releases |
| event chain | reuse `game_chronology.py`, `feature_data.py`, predecessor eligibility, resets and continuity; later outcomes never become predictors |
| strength | reconstruction owns actual skater/goalie membership. extend preparation beyond its present 5v5 filter; unit summaries use the actual opposing set rather than a hardcoded five |
| elapsed context | reconstruction owns segments/conflicts; preparation evaluates the modeled context over all retained time, including zero-event time. event-only features cannot supply rate denominators |
| shift/rest/workload | reuse prefix/lookback facts; add elapsed evaluation at the same owner. retain partial counters and unknown starts; no same-clock faceoff does not prove an on-the-fly start |
| people/history | dated identities, handedness, age and affiliation. absent birth date gives a declared age-neutral transition; retrospective handedness retains its assumption. annual effects and lagged counts are separate |
| coaches | extend capture `--source` with `right-rail`: `/v1/gamecenter/{gameId}/right-rail`, at most one initial request for each of 6,560 games still missing it. add exclusive source leaves/receipts; do not recapture six unchanged core sources. interpret `/gameInfo/{homeTeam,awayTeam}/headCoach/default` through one attributed name-to-id table |
| coach binding/absence | receipt binds requested game; verify available team/date context. response may omit game id. missing/conflicting identity stays unknown; no present-day backfill or silent alternate feed |
| penalties/territory | located events, participants, severity, reason, zone and resets supply the exact targets in the attribution appendix. inferred movement is not tracked possession |
| personal/goalie outcomes | reuse `scoring_credits.py`, reports and boxscore/bio identities. assists are outcome evidence, not predictors for goals alone. explicitly construct recorded stop/continuation and reattempt labels |

right-rail is the only new bulk feed. use sequential existing effect capture, ordinary errors and manual retry; no acquisition framework. original receipt binding, explicit selection and broken-game preservation follow existing policy. roster reports may corroborate a recorded manual identity investigation, not act as an automatic fallback.

complete passes/screens, tracked entries/exits, puck trajectories and representative video-verified block origins remain unavailable. setters, territorial movement and releases are inferred. event-chain attention is a possible later estimator over retained sequences, not another feed or a required neural network.

optional circumstances use training-only centering and explicit missing indicators/categories. source zero, structural absence, partial observation and unavailable remain distinct. essential identity, membership, outcome or frame instead follows the family's matched-support exclusion. report support by year, family, outcome and missing reason; never intersect unrelated family populations merely for convenience. observed personal/on-ice/spatial supports remain intact.

### internal capability contract

preparation produces identified `attempt`, `exposure`, `penalty`, `transition`, `person-season` and `game-context` records: game/event/interval locators, half-open time bounds, actual membership/strength, applicability, observed/inferred meaning and source identity. interfaces are ordinary functions, not plugins:

```
prepare_analysis(corpus_selection, coach_selection, output) -> prepared_manifest
fit_chance(prepared, annual_recipe, previous_state, output) -> chance_state
score_chance(prepared, chance_state, reference) -> valued_attempts
fit_spatial(prepared, valued_attempts, annual_recipe, previous_state, output) -> spatial_state
fit_mechanisms(prepared, spatial_state, chance_state, previous_states, output) -> mechanism_states
summarize_players(states, valued_attempts, reference, output) -> family_results
build_publication(observed_seasons, family_results, output) -> checked_candidate
```

these name responsibility, not mandatory files. saved states bind implementation, selection, response/support, ordered feature/identity axes, recipe/reference, predecessor and solver result. reuse exclusive finite-JSON/array artifact helpers. fixed output payloads are defined in the application appendix; the publisher must not infer provenance from filenames.

### operator interface and artifact schema

add one ordinary `hockey-stats-analysis` entry point in `analysis_cli.py`, registered in `analysis/pyproject.toml`. explicit subcommands call the owners above; they do not schedule work:

| subcommand | required selections and result |
|---|---|
| `prepare --selection FILE --out DIR` | identified five-corpus/coach selection → prepared manifest and per-season facts/arrays |
| `fit --family execution|spatial|mechanisms --prepared DIR --season ID --out DIR` | one annual family state; `--previous DIR` required for a returning annual chain; spatial also requires `--valued DIR`; mechanisms require `--execution DIR --spatial DIR` |
| `score --prepared DIR --execution DIR --season ID --out DIR` | frozen chance state → valued attempts and common opportunity panel |
| `summarize --prepared DIR --models FILE --out DIR` | explicit compatible annual state/panel selection → three-season family results, references and evidence |
| `publish --observed FILE --results DIR --out FILE` | existing observed selections plus analytical results → one candidate, through the existing publication builder |

`selection.json` is schema 1: `purpose`, ordered `seasons[{season,corpus_manifest,sha256}]`, `coach_captures[{game_id,receipt,sha256}]`, `display_seasons`, and fixed `recipe_id='experimental-v1'`. files use explicit paths; validate internal receipt/source hashes through existing readers. `models.json` lists `{family,season,state_manifest,sha256}` and valued-panel manifests; no globbing for the newest result. reject omitted prerequisites, ignored flags, duplicate years and incompatible identities. the first annual state has no predecessor; later states cannot silently restart from zero.

each output directory contains `manifest.json` with `schema_version=1`, `kind`, input/recipe identities, ordered axes, numerical status and `{path,sha256}` members. use existing JSON/array writers: JSON for finite typed facts/metadata, numpy archives for numerical arrays; partition large facts by game/year. completed annual families are the reuse unit. no automatic old-artifact migration, new storage service or serialized python objects. dry command examples in the verification receipt identify the actual chosen paths; no costly job starts merely by importing a module.

## b. baseline and accounting

the appendices freeze estimators, actor/reference operations, units, signs and accounting. do not clip old additive complete-rate predictions into a new model. positive likelihoods reuse bases/chronology/sparse mechanisms; old quadratic coefficients are not compatible fitted artifacts.

| producer | required actual outputs |
|---|---|
| chance/execution | four outcomes; factual/neutral values; fractional origins; finishing/setting; type/danger and personal-shot evidence |
| spatial skaters | 5v5 offense/defense; 5v4, 5v3, 4v3 pp offense and reciprocal pk defense; attempt/chance maps and scalars; reference/actual-context predictions |
| penalties/territory/shootiness | drawn/taken rates/value; ice won/lost and four explanatory subskills; share of team attempts |
| goalies | stopping, observed/expected evidence, ev/pk and location/type/danger detail, recorded outcome/reattempt behavior, workload/history |
| accounting | exactly ten additive skater terms; common workload, league/depth references; nonlinear interaction treatment, context explanation and map/scalar closure |

the chance recipe selects `game_additive,recent_additive,recent_interactions,recent_geometry,off_wing,sequence,shift_age,shift_start,workload,calendar_rest,strength_transition`, plus actual strength, coach and annual age. `game_detail,recent_detail,action_windows,zone_run,historical` remain implemented and initially inactive: overlapping encodings are not extra evidence. attribution uses its elapsed design, not the event design transplanted onto stints. 04o's smooth score/time family remains an alternative, neither discarded nor automatically adopted.

joint selection does not require each family's historical study to have succeeded. inspect assembled behavior. later ablations require refitting; zeroing a fitted term is a conditional perturbation only.

## c. non-overlapping batches

each batch pairs its domain/numerical owner with a content reviewer. labels, denominators, real representative content and unavailable states are part of its contract. coordinate shared-file edits rather than duplicate owners.

| batch | owned files/boundaries | handoff |
|---|---|---|
| evidence | existing `app/src/operator/{capture,cli,capture-report}.ts`; `analysis/src/hockey_stats/{captures,interpret,references,reconstruct,corpus_inputs,feature_data,feature_history}.py`; cohesive new `analysis_data.py` | common prepared facts/selection and fixture witnesses; sole owner of shared source changes |
| chance/execution/goalies | compatible `chance*`/`shot_origins.py`; cohesive `execution.py`, called by the single `analysis_cli.py` | annual states, valued attempts, execution/goalie results |
| spatial/mechanisms/value | reuse `attribution_data.py`/`attribution.py` basis/identity helpers; `spatial_rates.py`, `player_mechanisms.py`, `player_value.py` | positive annual rates, mechanism states, reference ledger |
| publication/readers | existing `publication.py`, new `analysis_publication.py`; existing effect owners plus `shared/player-analysis.ts`, `server/analysis-publication.ts` | one strict schema-7 candidate, typed reads, cross-family validation |
| application/content | existing routes/pickers/distributions/rink/export owners; cohesive analysis card/details/history/context modules | all journeys, fixture-first where useful, actual-output review |
| integration | manifests, receipts, docs and real journeys; no runner | checked family paths in one candidate; activation separately assigned |

these are work packages, not mandatory serial prs. preparation and application/publication proceed in parallel; chance supplies valued responses; spatial rates supply mechanism valuation. integrate actual families as they arrive. 5v5 alone, fixtures alone or unexplained prior zeros do not complete the program. 05i personal geography belongs here rather than in another prerequisite slice.

## d. operation and acceptance

run one declared baseline per family and five chronological annual states, plus the bounded numerical checks in the appendices: thirty execution/goalie, thirty spatial and twenty mechanism head-states, with sixteen final-head continuations. initializations and setter-em inner solves add actual computation; eighty states is not eighty optimizer calls. no grid search, automatic feature search, bootstrap-refit campaign or extra seasons. begin with fixtures and representative real preparation, solve and common-panel projection to measure dimensions, time and memory. measurements determine chunk sizes and honest cost estimates, not a new scientific gate. do not silently reduce forty modes, populations or references to meet an invented deadline.

64 gb is the memory envelope. one heavy fit at a time; chunk dense work rather than materialize whole-corpus native-cell tensors. preserve expensive annual outputs externally and reuse completed compatible states explicitly. no checkpoint engine, local fit mirror, colima/docker or distributed infrastructure. failed writes may require manual rerun. complete fitting needs external originals; detached development uses the existing local corpus. no new dependency without a concrete unmet requirement in numpy/scipy/effect/react/sqlite.

use temporary integration/live red → green → refactor → green checks, then delete campaign-only tests/controllers and unused dependencies. retain fixtures, checked facts and scientific diagnostic commands. only explicitly selected stable regressions under [07](07-lightweight-testing.md) survive; no general harness is added.

1. **source:** independent witnesses cover new targets/strengths, coach binding, same-clock ambiguity, leakage, missing/partial inputs, origins/setters, zero-event time and corrected exclusions. old source/observed facts stay exact unless an independently demonstrated correction is recorded separately.
2. **numerics:** independently check small objectives/gradients, constrained coordinates, chronology, probability/mass closure, positive complete rates, references and ten-term accounting. tighten solver tolerances tenfold for one bounded final-state continuation per distinct fitted head; compare reference-panel probabilities (`1e-5` absolute), per-hour scalar effects (`1e-4` absolute) and resulting basket terms (`1e-3` goals). these are numerical resolution tolerances, not accuracy claims. any exceeded bound is an unresolved numerical result requiring a responsible repair or explicit incomplete delivery, not another automatic campaign. failed solves stay unavailable; diagnostic endpoints are not completed estimates.
3. **real completion:** every selected family produces actual annual results on its declared population, with coverage, costs and known limitations. include simple in-sample fit/calibration/residual diagnostics, labeled as such. poor quality alone does not block an honestly computed experimental output.
4. **publication:** source/result → sqlite → typed response → profile/table/map/comparison/history/export reconciles. cover a goalie, sparse specialist, traded skater, incomplete game, changed history and synthetic fixture. verify on/off and three-person intersections independently of pair totals.
5. **content/operation:** reviewer checks real values, units/reference, support, uncertainty absence, color/sign, 320px layout, keyboard access, native 200% zoom and actual exports. detached browsing and disposable-file schema-paired rollback pass before assigned activation. preserve current serving files during development.

adversarial review covers each changed source, numerical, transport and content boundary. stop further checks once required behavior passes and concrete concerns are resolved. this contract establishes software and experimental use, not supported ability.

then inspect the assembled product, rank defects by consequences, save the baseline and improve one consequential mechanism or coherent feature group. compare actual cards/maps and relevant empirical evidence. calibrated uncertainty, better aging/origin/attribution and public launch remain follow-ups; they must not postpone the complete experimental product again.
