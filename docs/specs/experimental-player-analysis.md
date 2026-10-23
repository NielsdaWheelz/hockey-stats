# complete experimental player analysis

full implementation contract. [the plan](../plan.md) owns assignment; this specification assigns no execution. read the four normative appendices with this page: [chance/execution and goalies](experimental-chance.md), [spatial attribution and value accounting](experimental-attribution.md), [publication and application](experimental-application.md), [card facts and source contracts](experimental-card-facts.md). together they replace the coordinating stub and the implementation-detail placeholders in 05/06. frozen protocols and verdicts remain unchanged.

coverage amendment, 2026-10-22: the reviewed appendices define the initial baseline, not exhaustive feature coverage. the requirement below broadens preparation and retained alternatives; their remaining later-destination contracts are recorded in [the coverage issue](../issues/experimental-repertoire-coverage.md). the earlier specification review does not certify those additions. the baseline remains usable as an integration increment while the expanded program stays incomplete.

the subsequent frontend clarification also requires the [visual inventory](../product-inventory.md#visual-coverage-inventory--2026-10-22): distinct panels, chart forms, controls and exports must be traced individually. [visual gaps](../issues/experimental-visual-coverage.md) include actual missing numerical/publication contracts, not merely styling. the dated v1 crosswalk and amended appendices now define the required additions; later destination forms remain open. these add factual/scoring/display work without new fit heads. integrate the independent paths in parallel when assigned.

**release clarification:** v1 is the [complete card boundary](../product-inventory.md#v1-card-completion-boundary--2026-10-22): hockeyviz-style player cards with all component/subskill bodies, and the two jfresh-style skater cards with every honestly constructible field. required card maps, distributions, histories and export belong in v1; the full surrounding visual catalogue and retained alternative encoders need not all finish first. inaccessible evidence remains an explicit field-level limitation. the following comprehensive requirements describe the whole program; they do not reinstate a global v1 coverage gate. [sample-driven content contract](experimental-application.md#sample-driven-presentation-requirements)

the v1 field/source/owner crosswalk and additional numerical/schema/content contracts are now complete. the [delivery sequence](../plan.md#v1-delivery-sequence) defines twenty bounded implementation handoffs; actual assignment remains separate. the [crosswalk and complete-card acceptance rule](../product-inventory.md#v1-field-crosswalk-and-card-acceptance) bounds the dated release. unaffected contracts may proceed when assigned; new additions require their own review and cost disclosure. no whole-destination audit or best-model requirement precedes v1.

## target and limits

deliver the complete selected [player-analysis inventory](../product-inventory.md) with real, coherent, explicitly experimental estimates. extend one application: source → local python → sqlite → effect → react. integrate useful families continuously; a missing family leaves the program incomplete, not the website unusable. weak scientific performance directs iteration. incorrect calculations, failed solves and invented evidence are not estimates.

the headline describes underlying level across a regular season. fit **2021–22 through 2025–26** chronologically; publish the last three annual states beside existing observed results. earlier displayed states cannot consume later responses. these seasons are research-exposed; in-sample displays and retrospective checks are not forecasts or untouched validation.

## input and feature completeness

complete both the [feature inventory](../model-features.md) and the [component/view inventory](../product-inventory.md). every identified, analytically meaningful public input, documented peer family and agreed candidate needs a retained implementation or a specific evidence limitation. an unwritten available family cannot be closed as unnecessary to the first recipe or unlikely to improve prediction. public methods and our proposed alternatives retain separate provenance; no private-recipe or unlimited transformation claim follows.

preparation preserves all supported recorded event kinds and their ordered histories, exact locators, timestamps/clock uncertainty, participant and on-ice identities, episode/reset boundaries and missingness. summary features are consumers of this history, not its replacement. a predictor selects only a declared pre-event prefix; later assists, outcomes and reconstruction evidence cannot enter it unnoticed. incomplete recording stays explicit; a full recorded history is not complete tracked possession.

retain the existing recent/sequence/window encoders and add concrete selectable time-decay and bounded learned-attention alternatives. attention learns weights from training data; it is not another source field or automatically a transformer. each owns its objective, prefix/reset scope, parameters, masks, population, reference, numerical checks and measured cost. cap/truncation decisions must be explicit. no hidden last-event substitute, outcome-conditioned weighting or fit on assessment data. the owning chance appendix must settle the actual alternative before implementation.

the coverage work also owns named tip/rink corrections, finer elapsed context and age/entry/transition-variance alternatives, plus dispositions for other meaningful available source fields. derived corrections never overwrite source observations; inability to establish their accuracy is distinct from inability to implement an honest alternative. additional public sources need concrete capture/admission contracts, not a generic importer.

every required alternative must eventually be prepared, selectable and exercised through a bounded real-data fit/score path where applicable. this proves implementation behavior, not value. v1 needs the inputs/encoders of its coherent card-producing recipes; remaining alternatives stay named later work, with correct existing implementations retained. no whole-corpus campaign or search over combinations is implied. variants reuse existing command/artifact owners and declare their own identities; `experimental-v1` below identifies the frozen initial recipe, not an assertion that all product requirements are already specified. no new runtime registry or runner follows.

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

the ten-term total is a defined component index, not war, a forecast or credit for actual goals. the expanded visual destination includes additional goalie aggregate and quality-start/consistency presentations, with independent definitions still open. later jfresh-specific extras do not postpone the v1 hockeyviz-style goalie card; any field on that required card still needs an explicit contract. no causal isolation or exact private-model parity claim.

## a. evidence and preparation

use the five admitted selections and corrected 02d support. preserve raw bytes, existing observed meanings and frozen research ledgers. product artifacts use a new strict contract; reuse native facts instead of reimplementing interpretation per model. [v1-01](v1-01-shared-evidence.md) specifies base preparation, including separate event-supported and matched-elapsed populations; missing elapsed support does not erase otherwise usable execution evidence.

| input | initial implementation / authoritative owner |
|---|---|
| geometry, type, blocks | existing normalized frames/types/grid; chance owner supplies inferred-origin mass. block contacts never become observed releases |
| event chain | reuse `game_chronology.py`, `feature_data.py`, predecessor eligibility, resets and continuity; later outcomes never become predictors |
| strength | reconstruction owns actual skater/goalie membership. extend preparation beyond its present 5v5 filter; unit summaries use the actual opposing set rather than a hardcoded five |
| elapsed context | reconstruction owns segments/conflicts; preparation evaluates the modeled context over all retained time, including zero-event time. event-only features cannot supply rate denominators |
| shift/rest/workload | reuse prefix/lookback facts; add elapsed evaluation at the same owner. retain partial counters and unknown starts; no same-clock faceoff does not prove an on-the-fly start |
| people/history | dated identities, handedness, age and affiliation. absent birth date gives a declared age-neutral transition; retrospective handedness retains its assumption. annual effects and lagged counts are separate |
| coaches | [v1-02](v1-02-dated-coaches.md) extends capture `--source` with `right-rail`: `/v1/gamecenter/{gameId}/right-rail`. fresh supplemental directories, one initial request per missing game, at most 6,560, after the bounded access probe. preserve the six-source core contract. interpret `/gameInfo/{homeTeam,awayTeam}/headCoach/default` through one attributed identity table |
| coach binding/absence | receipt binds requested game; check available context, including absent corroborators. reported game head coach is not verified bench attendance or appointment history. missing/conflicting identity stays unknown; no present-day backfill or silent alternate feed. v1-02 records source access and real acquisition separately from software completion |
| penalties/territory | located events, participants, severity, reason, zone and resets supply the exact targets in the attribution appendix. inferred movement is not tracked possession |
| factual card/source additions | [card-facts appendix](experimental-card-facts.md): all-strength usage/primary scoring, goal/on-net context, personal unblocked/hit/blocker counts, shifts/score/shared usage and honest microstat/skating dispositions; no parallel parser or fake pass evidence |
| personal/goalie outcomes | reuse `scoring_credits.py`, reports and boxscore/bio identities. assists are outcome evidence, not predictors for goals alone. explicitly construct recorded stop/continuation and reattempt labels |

right-rail is the currently specified new bulk feed, not a claim that all relevant public inputs have been covered. the inventory must record other identified available inputs and finish their contracts before separately assigned acquisition. use sequential existing effect capture, ordinary errors and manual retry; no acquisition framework. original receipt binding, explicit selection and broken-game preservation follow existing policy. roster reports may corroborate a recorded manual identity investigation, not act as an automatic fallback.

the admitted corpus does not establish complete passes/screens, tracked entries/exits, puck trajectories or representative video-verified block origins. setters, territorial movement and releases are inferred. inspect identified public measurements/aggregates before declaring them unavailable; aggregates do not become event-level tracking. learned event attention is a required retained candidate in this program, with its concrete contract still open, rather than an unspecified post-product possibility.

optional circumstances use training-only centering and explicit missing indicators/categories. source zero, structural absence, partial observation and unavailable remain distinct. essential identity, membership, outcome or frame instead follows the family's matched-support exclusion. report support by year, family, outcome and missing reason; never intersect unrelated family populations merely for convenience. observed personal/on-ice/spatial supports remain intact.

### internal capability contract

preparation produces identified `attempt`, `exposure`, `penalty`, `transition`, `person-season` and `game-context` records: game/event/interval locators, half-open time bounds, actual membership/strength, applicability, observed/inferred meaning and source identity. interfaces are ordinary functions, not plugins:

```
prepare_analysis(corpus_selection, output) -> prepared_manifest
fit_chance(prepared, coaches, annual_recipe, previous_state, output) -> chance_state
score_chance(prepared, coaches, chance_state, reference) -> valued_attempts
fit_spatial(prepared, coaches, valued_attempts, annual_recipe, previous_state, output) -> spatial_state
fit_mechanisms(prepared, coaches, spatial_state, chance_state, previous_states, output) -> mechanism_states
summarize_players(states, valued_attempts, reference, output) -> family_results
build_publication(observed_seasons, family_results, output) -> checked_candidate
```

these name responsibility, not mandatory files. saved states bind implementation, selection, response/support, ordered feature/identity axes, recipe/reference, predecessor and solver result. reuse exclusive finite-JSON/array artifact helpers. fixed output payloads are defined in the application appendix; the publisher must not infer provenance from filenames.

base preparation and coach evidence have separate identities. [v1-02](v1-02-dated-coaches.md#output-and-downstream-composition) binds dated coach records/explicit absence to selected inventory games in `coaches.json`; fitting/scoring join by exact corpus, season, game, date and team identities. `--coaches FILE` binds that artifact's hash. later state consumers follow the exact bound selection, never a newly discovered feed. this permits independent preparation/acquisition and avoids rebuilding base facts when coaching evidence changes; it adds one explicit input at numerical execution. no unknown-coach fallback feed or silent change to a fitted state's input follows.

### operator interface and artifact schema

add one ordinary `hockey-stats-analysis` entry point in `analysis_cli.py`, registered in `analysis/pyproject.toml`. explicit subcommands call the owners above; they do not schedule work:

| subcommand | required selections and result |
|---|---|
| `prepare --selection FILE --out DIR` | identified five-corpus selection → prepared manifest and game/season facts, under v1-01; no coach dependency |
| `python -m hockey_stats.coaches --selection FILE --identities FILE --out DIR` | separate v1-02 offline module command → checked `coaches.json`; no preparation/publication command registration or network access |
| `fit --family execution\|spatial\|mechanisms --prepared DIR --coaches FILE --season ID --out DIR` | one annual family state; `--previous DIR` required for a returning annual chain; spatial also requires `--valued DIR`; mechanisms require `--execution DIR --spatial DIR` |
| `score --prepared DIR --coaches FILE --execution DIR --season ID --out DIR` | frozen chance state and its bound coach selection → valued attempts and common opportunity panel |
| `summarize --prepared DIR --models FILE --out DIR` | explicit compatible annual state/panel selection → three-season family results, references and evidence |
| `publish --observed FILE --results DIR --out DIR` | existing observed selections plus [v1-13's strict family results](v1-13-typed-publication.md#exchange-and-command) → one candidate and receipts, through the existing publication builder |

base `selection.json` follows [v1-01's strict schema 1](v1-01-shared-evidence.md#selection-artifacts-and-operation), separate from the v1-02 coach capture/binding selection. the fixed `recipe_id='experimental-v1'` and three display seasons belong to later model/result identities, not factual preparation. files use explicit paths; validate internal receipt/source hashes through existing readers. `models.json` lists `{family,season,state_manifest,sha256}` and valued-panel manifests; no globbing for the newest result. reject omitted prerequisites, ignored flags, duplicate years and incompatible identities. the first annual state has no predecessor; later states cannot silently restart from zero.

prepared/numerical output directories contain `manifest.json` with `schema_version=1`, `kind`, input identities and `{path,sha256}` members; numerical artifacts additionally bind recipe, ordered axes and numerical status. v1-01 fixes its factual manifest; the compact v1-02 source binder instead writes the complete `coaches.json` contract, and publication follows v1-13's candidate layout. use existing JSON/array writers: JSON for finite typed facts/metadata, numpy archives for numerical arrays; partition large facts by game/year. completed annual families are the numerical reuse unit. no automatic old-artifact migration, new storage service or serialized python objects. dry command examples in the verification receipt identify the actual chosen paths; no costly job starts merely by importing a module. add subcommands with their owning prs; v1-01 implements only `prepare`.

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
| coverage/contracts | source/method and player-card reference research, feature/visual inventories and owning appendices | explicit input and panel/control crosswalks, concrete missing contracts and costs; no new prerequisite study |
| evidence | existing `app/src/operator/{capture,cli,capture-report}.ts`; `analysis/src/hockey_stats/{captures,interpret,references,reconstruct,corpus_inputs,feature_data,feature_history}.py`; cohesive new `analysis_data.py` | common prepared facts/selection and fixture witnesses; sole owner of shared source changes |
| chance/execution/goalies | compatible `chance*`/`shot_origins.py`; cohesive `execution.py`, called by the single `analysis_cli.py`; source preparation stays with evidence owner | annual states, valued attempts, execution/goalie results; retained sequence/decay/attention and correction alternatives with checked exercise paths |
| spatial/mechanisms/value | reuse `attribution_data.py`/`attribution.py` basis/identity helpers; `spatial_rates.py`, `player_mechanisms.py`, `player_value.py` | positive annual rates, mechanism states, reference ledger; finer elapsed/temporal alternatives under their own contracts |
| publication/readers | existing `publication.py`, new `analysis_publication.py`; existing effect owners plus `shared/player-analysis.ts`, `server/analysis-publication.ts` | one strict schema-7 candidate, typed reads, cross-family validation |
| application/content | existing routes/pickers/distributions/rink/export owners; cohesive analysis card/details/history/context modules | v1 card crosswalk and supporting journeys first; later catalogue rows remain tracked. fixtures unblock work; actual outputs and exports complete it |
| integration | manifests, receipts, docs and real journeys; no runner | checked family paths in one candidate; activation separately assigned |

these are ownership packages, each deliverable across multiple prs under the plan's proposed boundaries. preparation and application/publication proceed in parallel once their contracts are settled; chance supplies valued responses; spatial rates supply mechanism valuation. integrate actual families as they arrive, then accept complete card compositions. 5v5 alone, fixtures alone or unexplained prior zeros do not complete v1. 05i personal geography belongs here rather than in another prerequisite slice. partial-family development must preserve explicit unfinished status and the current active publication.

[v1-13](v1-13-typed-publication.md) implements the fixed exchange/storage/read boundary with detached fixtures; later producers serialize real rows through it. it does not consume incomplete fit internals or require v1-01's corpus run. only the shared `analysis_cli.py`/entry-point edits need coordination. whole pending families have explicit availability envelopes; source gaps and failed computations remain separately attributable. existing observed views adapt to schema7; analytical card rendering and activation remain later assignments.

[v1-14](v1-14-history-cohorts-exports.md) consumes that boundary without another schema change: fixed field/cohort selectors, three annual peer populations, shared history and exports through the existing routes. detached fixtures establish these mechanisms; each later card still owes its complete composition and real producer-to-export evidence. it can proceed independently of factual/numerical producers once assigned, coordinating shared frontend files with other view owners.

[v1-15](v1-15-comparative-card-discovery.md) supplies the complete comparative skater composition and surrounding discovery/comparison against those shared mechanisms. it can be implemented detached alongside source work; actual v1-03/06/12 outputs close its real card and exports. finite tables and the two embedded histories reuse published values; no new numerical, source or publication contract follows.

## d. operation and acceptance

run one declared baseline per family and five chronological annual states, plus the bounded numerical checks in the appendices: thirty execution/goalie, thirty spatial and twenty mechanism head-states, with sixteen final-head continuations. initializations and setter-em inner solves add actual computation; eighty states is not eighty optimizer calls. no grid search, automatic feature search, bootstrap-refit campaign or extra seasons. begin with fixtures and representative real preparation, solve and common-panel projection to measure dimensions, time and memory. measurements determine chunk sizes and honest cost estimates, not a new scientific gate. do not silently reduce forty modes, populations or references to meet an invented deadline.

that count covers the initial recipe only. required alternative implementations add bounded preparation/fit/score exercise costs, to be fixed in their contracts before execution. retain correct code even when the baseline leaves it inactive. full-corpus comparative campaigns remain separately selected; implementation completeness does not mean an exhaustive empirical search.

64 gb is the memory envelope. one heavy fit at a time; chunk dense work rather than materialize whole-corpus native-cell tensors. preserve expensive annual outputs externally and reuse completed compatible states explicitly. no checkpoint engine, local fit mirror, colima/docker or distributed infrastructure. failed writes may require manual rerun. complete fitting needs external originals; detached development uses the existing local corpus. no new dependency without a concrete unmet requirement in numpy/scipy/effect/react/sqlite.

use temporary integration/live red → green → refactor → green checks, then delete campaign-only tests/controllers and unused dependencies. retain fixtures, checked facts and scientific diagnostic commands. only explicitly selected stable regressions under [07](07-lightweight-testing.md) survive; no general harness is added.

1. **source:** independent witnesses cover new targets/strengths, coach binding, same-clock ambiguity, leakage, missing/partial inputs, origins/setters, zero-event time and corrected exclusions. old source/observed facts stay exact unless an independently demonstrated correction is recorded separately.
2. **numerics:** independently check small objectives/gradients, constrained coordinates, chronology, probability/mass closure, positive complete rates, references and ten-term accounting. tighten solver tolerances tenfold for one bounded final-state continuation per distinct fitted head; compare reference-panel probabilities (`1e-5` absolute), per-hour scalar effects (`1e-4` absolute) and resulting basket terms (`1e-3` goals). these are numerical resolution tolerances, not accuracy claims. any exceeded bound is an unresolved numerical result requiring a responsible repair or explicit incomplete delivery, not another automatic campaign. failed solves stay unavailable; diagnostic endpoints are not completed estimates.
3. **real completion:** every selected family produces actual annual results on its declared population, with coverage, costs and known limitations. include simple in-sample fit/calibration/residual diagnostics, labeled as such. poor quality alone does not block an honestly computed experimental output.
4. **publication:** source/result → sqlite → typed response → profile/table/map/comparison/history/export reconciles. cover a goalie, sparse specialist, traded skater, incomplete game, changed history and synthetic fixture. verify on/off and three-person intersections independently of pair totals.
5. **content/operation:** reviewer checks real values, units/reference, support, uncertainty absence, color/sign, 320px layout, keyboard access, native 200% zoom and actual exports. detached browsing and disposable-file schema-paired rollback pass before assigned activation. preserve current serving files during development.
6. **coverage:** v1 reconciles every required card component/field and its input path to real producer, publication, rendered behavior and export. distinguish documented inaccessible evidence from available but unwritten work; the latter remains incomplete. track the broader source/method/feature and visual inventories separately, including later alternatives and standalone views. their open rows prevent claiming the entire destination complete, but do not block the specified v1. recipe activation and scientific assessment remain separate from implementation evidence.

adversarial review covers each changed source, numerical, transport and content boundary. stop further checks once required behavior passes and concrete concerns are resolved. this contract establishes software and experimental use, not supported ability.

then inspect the assembled product, rank defects by consequences, save the baseline and improve one consequential mechanism or coherent feature group. compare actual cards/maps and relevant empirical evidence. calibrated uncertainty, better aging/origin/attribution and public launch remain follow-ups; they must not postpone the complete experimental product again.
