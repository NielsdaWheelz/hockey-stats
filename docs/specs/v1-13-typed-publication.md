# v1-13 — typed publication foundation

full implementation handoff under [the program](experimental-player-analysis.md); [the plan](../plan.md#proposed-pr-boundaries-and-dependencies) owns assignment. [the application appendix](experimental-application.md) owns hockey quantities, card requirements and references; this document closes their exchange, storage and read contracts. no new product preference is required. implementation, acquisition, fitting and activation are not assigned by writing this specification.

prospective producer refinement: [v1-03](v1-03-factual-card-reductions.md) corrects score-share arithmetic, adds the fixed shift-coverage reason and permits evidenced person affiliations beyond old observed support while preserving every old observed fact. those narrow invariant changes supersede the corresponding checks below; they do not alter v1-13's completed acceptance record, fixed table shapes or schema version.

## outcome and boundary

one checked result bundle plus the existing observed selections produces a standalone schema-7 sqlite publication. one effect reader serves its typed contents, including explicit unfinished families, to the existing website. small fixtures exercise every analytical family before its real producer exists. observed facts and existing observed journeys retain their meanings.

all implementation and acceptance here can run detached. no v1-01 output, external originals, full-season rebuild, scientific fit or new source is required. fixtures establish this transport boundary, not real analytical delivery or complete cards. real serializers join through their owning producer prs; v1-14 onward owns new cards, cohorts, historical percentiles, contours and exports. no active/previous database, port 3000, primary build or running listener changes.

accepted costs: complete finite schemas now; a coordinated API cutover and small route-loader changes; explicit source/method/partial-state metadata; cross-language validation. these let source, numerical and interface work proceed independently. no orm, schema generator, generic metric registry, plugin system, job runner, additional service or dependency is needed.

## owners and implementation boundaries

| boundary | responsible files and change |
|---|---|
| result exchange and analytical storage | new `analysis/src/hockey_stats/analysis_publication.py`: strict result readers/writers, fixed family row schemas, inserts and cross-record checks; ordinary functions, no fit-artifact interpretation |
| candidate assembly | existing `publication.py`: observed aggregation/insertion/read-back, complete schema, finalization and receipts; `observed.py` remains the only existing observed reducer |
| command | `analysis_cli.py` and `analysis/pyproject.toml`: add only `publish`; coordinate this small shared edit with v1-01's `prepare`; remove the superseded observed-publication entry point in `cli.py` |
| shared boundary | new `app/src/shared/player-analysis.ts`; retain observed metrics/coverage primitives in `shared/observed.ts`. put shared identity/publication types in one small neutral module if needed to avoid circular imports; no duplicated definitions |
| read service | existing `server/publication.ts`, new `server/analysis-publication.ts`; preserve observed/spatial/deployment checks and SQL owners; one `Publication` service and connection lifetime |
| HTTP and client | existing `server/main.ts`, `web/client.ts`; one typed API, exact query unions, cancellation and existing errors |
| current views | the existing league/profile/comparison route loaders and a small shared composition function; adapt current observed presentation, do not build analytical cards |
| operator and evidence | existing `operator/publication-cli.ts`; fixture README and `docs/research/publication-v1-13/verification.md`; storage, interface and content reviewers own independent checks |

implement in that order, with review at each boundary. later producer prs translate their own outputs into these canonical rows; the publisher never reaches into unfinished fit internals. keep source, eligibility, fitted arithmetic and family reduction at their existing owners. do not copy reconstruction or research pipelines.

## exchange and command

```text
hockey-stats-analysis publish --observed FILE --results DIR --out DIR
build_publication(observed_selection: Path, results: Path, output: Path) -> verification
read_results(directory: Path) -> validated manifest and streamed fixed rows
write_results(selection, catalogs, family_rows, output: Path) -> manifest
```

`--observed` retains `publication.read_selection`'s explicit schema-1 corpus selection. `--results` selects the following completed bundle; `--out` is a fresh directory, preserving the mature writer's receipts/final-rename flow. no optional results argument, glob/latest discovery, old-format importer or ignored command flags. add no placeholder `fit`, `score` or `summarize` commands. `write_results` is the shared serializer later producers call, not a command for generating fake real results.

```text
manifest.json = {
  schema_version: 1, kind: "player_analysis_results", purpose: "real"|"fixture",
  seasons: [season],
  observed_bindings: [{season, corpus_sha256}],
  prepared_sha256: null|lowercase-64-hex,
  producer: {git_commit, git_dirty, python_version},
  catalogs: {people: member, sources: member, methods: member, supports: member},
  families: [{season, family, availability: "provided"|"not_computed",
              explanation: string|null, tables: {fixed_table_name: member}}]
}
member = {path: relative-path, sha256: lowercase-64-hex, rows: nonnegative-integer}
```

all keys required; unknown keys/types, duplicate JSON object keys, duplicate rows/years/families, unsafe integer IDs, invalid dates, nonfinite values and unmatched digests fail. use existing `captures.strict_json`, `artifacts` exclusive finite writers and digest/path helpers. catalog/table members are newline-delimited strict JSON, sorted by their declared primary key; validate by streaming. `tables` admits only the concrete names in the family table below, never supplied SQL, field lists or arbitrary metric names. empty supplied tables still have hashed zero-row files. write members before the manifest; a missing manifest or promised file is incomplete/error, not a coverage gap.

real bundles use the three ordered display seasons `20232024,20242025,20252026`; fixture bundles may use a nonempty ordered subset. the observed selection's purpose, seasons and corpus digests must agree. members inherit bundle purpose; source/method purpose must agree with it. every fixture bundle/candidate/response remains `fixture`, including fixtures derived from actual captured games. synthetic source origin requires fixture purpose. these checks reject declared mixtures; hashes establish identity, not the honesty of a fabricated provenance claim. source identifiers grant no permission to reopen raw inputs during reads. fitted methods may bind five historical seasons; those do not become display seasons.

`prepared_sha256` identifies the common base preparation consumed by supplied new facts/models, null only when all dependent families are pending. relevant method `inputs` must include this exact base identity; derived execution/design inputs retain their separate hashes. fixtures bind their small synthetic evidence identity, not a nonexistent real v1-01 run. the publisher validates recorded identities/member contents, without reopening or rehashing an external preparation or fit tree.

the complete catalog of families is fixed. include one disposition per displayed season/family:

| family | fixed tables owned by its result producer |
|---|---|
| `descriptive` | `skater_descriptive`, `skater_context` |
| `microstats` | `skater_microstats` |
| `spatial` | `skater_spatial`, spatial `analysis_map`, `adjustment_decomposition` |
| `execution` | `skater_execution`, execution `analysis_map`, `execution_breakdown`, `attempt_value`, `attempt_setter`, `attempt_execution_share` |
| `shootiness` | `skater_shootiness` |
| `penalties` | `skater_penalties` |
| `territory` | `skater_territory`, territory `analysis_map` |
| `goalie` | `goalie_result`, `goalie_observed`, `goalie_evidence_map`, `goalie_danger`, goalie `analysis_map` and `execution_breakdown` |
| `ledger` | `value_ledger` |
| `evidence` | source-only `attempt_fact`, `dressed_game`, `interval_fact`, `interval_player`, `interval_location`, `context_coverage` |

table ownership is disjoint even where the name is shared: map kind and the breakdown's referenced `person.kind` determine its owner; no additional subject-kind key. `attempt_value` is an exchange-only keyed supplement; the publisher left-joins it into source `attempt_fact`. absent execution never deletes source-supported shots. supplied supplement keys without a source event fail. base evidence exports belong to v1-03; valued evidence and execution supplements join with v1-06. unfinished valued context populations are explicit in `context_coverage`, not inferred from empty rows.

`not_computed` requires a specific explanation and an empty `tables` object. `provided` requires exactly its table set, even if some records/fields remain unavailable. for player summary/map/breakdown tables, include every applicable person/strength/key from the fixed matrix below; no omitted required key. a whole pending row uses `result={availability:"not_computed",explanation,data:null}`. a supplied row uses `result={availability:"provided",explanation:null,data:<strict family payload>}` and all required fields, including individually unavailable values. a pending family need not manufacture thousands of rows: the reader returns the same explicit family envelope. fixed card slots later render that state; they do not vanish. event/interval tables instead enumerate actual finalized evidence; coverage records distinguish a verified empty set from unfinished work.

summary/map/breakdown exchange rows are exactly `{<fixed table key fields>,result}`; `result.data` contains the appendix's fixed payload, including its method ID where defined. storage extracts that method ID into its nullable foreign-key column and removes the duplicate from payload JSON; reads restore it. pending rows require that column null; provided modeled rows require a resolving method, including a failed-fit record when appropriate. source-only families instead carry their tagged provenance. evidence rows use their explicit fact fields, not a fabricated estimate envelope.

partial candidates are valid. provided means a payload was supplied, not that every component is implemented or scientifically supported. no automatic `v1_complete` or `admitted` flag. a missing disposition/required row is corruption; explicitly unfinished work remains unfinished.

## metadata and value contracts

use the appendix's fixed `estimate`, `support`, `fact_value` and family fields, with these concrete refinements. scalars use JSON numbers; counts are safe nonnegative integers; player/team IDs cross this publication boundary as canonical decimal strings. strings for seasons/game IDs retain existing schemas. no lossy integer coercion, string-to-number guessing or default zero.

- `estimate` keeps `value`, `unavailable_reason`, `uncertainty` and adds `reason_detail:null|{explanation,evidence:[reference]}`. available values have null reason/detail. unavailable values require a reason/detail and `uncertainty.kind=not_estimated`; the explanation names the missing observation or unfinished computation. intervals require available values, finite ordered endpoints, `0<level<1`, nonempty method and conditional assumptions. do not clamp probabilities, intervals or signed effects to pass validation.
- `reference={kind:"source"|"method",id}` replaces ambiguous `source_or_method_id`; `fact_value.provenance` uses this tagged reference. a method-based value cannot impersonate a recorded source. no dangling IDs. `reason_detail.evidence` may be empty only for explicit `not_computed`, `not_applicable` or algebraically established `no_exposure`; a missing source/failed fit needs its actual source/method record.
- `support.reason_counts` is sorted `[{code,count}]`, with positive integer counts and no duplicate code; codes come from the producing population's declared reason vocabulary. `inferred_inputs` is a sorted subset of `blocked_origin|setter|territory|historical_borrowing`; `prior_seasons` is a sorted distinct season list. actual support may be null/zero for a modeled reference-panel estimate, with `prior_only` and current-season information truthful. observed count/time rates need positive matched time. these rules do not collapse conditional-stage denominators into one support object.
- source catalog rows: `{source_id,label,purpose:"real"|"fixture",origin:"source_capture"|"synthetic",acquisition:"admitted"|"not_acquired"|"access_unverified",construction,population,definition,receipts:[{uri,sha256}],limitations:[string]}`. `construction` uses the appendix's finite enum; population/definition are nonempty human-readable descriptions tied to the field's fixed contract. admitted sources need receipt identities; unavailable sources need a specific limitation. a public URL alone is not a receipt. synthetic receipts identify fixture artifacts; captured fixtures preserve their source receipts under fixture purpose. receipts are explanatory identities, not server filesystem/network capabilities.
- method rows extend the appendix's fields with `purpose`, `inputs:[{role,sha256,seasons}]`, `reference_id`, `support_policy_id`, `assessment`. roles are `prepared|coaches|annual_state|opportunity_panel|source_results|predecessor`; retain all applicable inputs. `assessment={status:"experimental",findings:[{quantities:[fixed field path],population,summary,evidence:[{uri,sha256:null|hex}]}]}`. `family,recipe_id,design_sha256,input_sha256,fit_seasons,training_cutoff,target,population,reference,limitations,evidence` remain required; descriptive text is nonempty, digests are hex, evidence uses the same receipt shape. the composite input digest hashes the exact ordered input list. unavailable fit states may have null design/cutoff only with failed/not-computed evidence; they cannot support available fitted values. no new supported-ability claim is introduced here.

compatibility means agreement on the relevant source seasons, purpose, reference and quantity definition, not equality of all input hashes: families intentionally use different supports. ledger inputs must name the same workload/reference policy as their component rows. a source correction or reference-panel change cannot be hidden behind an unchanged label. method and source descriptions are returned once per response, keyed by id; history includes the IDs needed for every displayed year. database reads require no external receipt files.

each modeled row's referenced methods must declare fitting seasons no later than that row's season, with any nonnull training cutoff no later than june 30 of the row's ending year. season-scoped support descriptors obey the same method bound. annual-state/predecessor input seasons must belong to the method's fitting seasons. these check the parent's chronological annual-state contract at publication; the numerical producer still owns the exact response/cutoff audit. a shared multi-season prepared artifact may include later years without claiming they entered an earlier fit. prior support must be strictly historical and bound by the containing method's fitting and input seasons; prior-only support requires a nonempty prior-season list.

the method assessment applies to modeled/model-valued quantities. recorded/reconstructed reductions retain their source provenance and producer identity; they do not acquire an experimental-model label because they share a database. `skater_descriptive`, `skater_context`, `goalie_observed` and its game records have a required source-tagged `provenance`; each goalie `source_counts`/`reported_boxscore_counts` record has its own source reference. `reported_usage.provenance` travels with that directly reused scalar projection. nested factual records inherit their containing source reference; paired/model-valued sections retain their method IDs. source-unclassified attempts remain visible in personal evidence/counts even when excluded from valued type breakdowns. recorded block coordinates have `location_kind=block_contact|unavailable`, never a release-location label.

shared physical values have one origin: overview/history/detail are projections, never independently fitted or reduced copies. enforce equality for repeated observed goals/a1 and recorded penalty fields. unblocked attempts, shots on goal, primary goal assists, tracked shot assists and inferred setting retain separate fields.

## storage and complete row shapes

replace the schema-6 identity table `player` with `person`; preserve observed game/season/pair/spatial tables and their factual columns, changing only foreign keys formerly targeting `player`. preserve foreign keys to game/player-game/player-season. validate skater kind on observed rows. no competing identity store and no goalie row with invented skater metrics. keep existing name/source values exact; optional new identity can remain unavailable. selected-season person absence is different from an unknown person.

`person` has the appendix's explicit identity fields plus `source_json`/`identity_support`; use the v1-01 identity schema for dates, hand, sweater-by-team and reasons. `age_years` is the exact date-day difference from birth date to the february-1 reference divided by `365.25`; missing birth date leaves age unavailable. unknown normalized height stays null under [the unit issue](../issues/bio-height-units.md). fixture identity supplies the same shape without requiring v1-01 execution. every observed skater must occur in the selected-season catalog with exact existing name/position/teams; conflicting duplicate identity fails.

the publication row retains nullable `prepared_sha256` from the result manifest. provided dependent families require it; relevant methods bind this same identity. retaining it inside sqlite lets standalone readers check the base/supplement binding without reopening the result or preparation directories.

schema 7 contains the preserved tables, fixed analytical tables from the appendix, plus:

| table / primary key | content |
|---|---|
| `analysis_source(source_id)` | strict source descriptor JSON |
| `analysis_support(support_id)` | `{season,population_id,policy_id,definition,source_ids,method_ids}`; finite evidence-population definitions, no exposure totals or arbitrary metric registry |
| `analysis_family(season,family)` | availability/explanation; exact season×family inventory |
| `analysis_grid(grid_id)` | fixed native/display geometry below |
| `dressed_game(season,player_id,game_id)` | actual team id and source reference, including supported roster games without included elapsed time |
| `context_coverage(season,player_id,population)` | availability, known excluded seconds, unquantified gap, reason counts and source/method references for that population's dressed-game support |

use explicit relational primary/foreign keys for season/person/game/method references and query selectors; strict JSON only for each finite nested payload. avoid duplicate `method_id` in column and payload: reconstruct the API payload from the one stored value. physical column/key/type/nullability definitions must be literal checked declarations, extending current readers. every table exists even when a family is pending; no arbitrary extension tables or silent extras. [strict tables](https://www.sqlite.org/stricttables.html) do not replace JSON/domain validation; [foreign keys](https://www.sqlite.org/foreignkeys.html) must be enabled explicitly.

support IDs resolve within `analysis_support`, whose population is `source_supported_attempts` or one of the five context populations. the definition describes eligibility and evidence; actual counts/time stay in facts/coverage. source/method lists resolve, season agrees with the fact and its population selector agrees with the descriptor. request metadata includes referenced support definitions once, alongside sources/methods.

the [application family tables](experimental-application.md#schema-7) and [v1 additions](experimental-application.md#v1-payload-additions) fix named leaves. make prose-only nested facts executable with the following common record shapes; equations/populations stay in [card facts](experimental-card-facts.md):

| nested record | required structure |
|---|---|
| reported usage | `positive_toi_appearances,reported_seconds,minutes_per_appearance,reported_shifts,listed_games,supported_games,missing_games,teams,support`; teams repeat the same fields keyed by team id, no recursive teams |
| strength usage | exact-state records plus fixed `ev,pp,pk,other,five_on_five`; each `seconds,appearances,minutes_per_appearance,support`; extra-attacker states retain explicit counts/goalie presence, not an invented standard strength |
| scoring by strength | same fixed groups plus exact states: `goals,primary_assists,primary_points,seconds,goals_per60,primary_assists_per60,primary_points_per60,support`; `unclassified` has only three counts/support, no invented strength time or rates; all-strength official evidence remains separate |
| on/off | fixed `on,off,league`, each `{for_count,against_count,seconds,for_per60,against_per60,share_minus_half,support}`; paired on-net counts accompany recorded goals |
| conversion | focal/team/league records of for/against goals, on-net counts, shooting/save fractions and support, with every ratio's own known denominator |
| recorded penalties | fixed drawn/taken/served records: count, reported seconds, per1000minutes, category counts and support; categories follow source interpretation, include unknown, and reconcile to counts; team/league share the shape |
| deployment | shift-start counts/shares for `offensive,neutral,defensive,on_the_fly,unknown`; score seconds/shares for `leading,tied,trailing,unknown`; team/league records share these shapes and support |
| counterpart usage | overall plus F/D records from the appendix; F has four band counts/weights, D three; histogram stores slot-seconds, not rounded percentages; zero known weight gives unavailable mean |
| microstats | every named key from the factual table, including both skating measures, as `fact_value`; no variable key dictionary or tracked proxy substitution |
| goalie summaries/games | source/paired/stage records exactly as the appendix; game rows additionally `game_id,date,team,opponent,start_status,reported_seconds`. start status is `start|relief|did_not_play|unknown`; listed/appearance coverage stays explicit |

counts/seconds with incomplete evidence are nullable where specified; derived numeric facts use `estimate`/support and fixed units, never a naked null without its containing coverage. all records have fixed field sets; array elements have explicit IDs and uniqueness. strength states are typed records, not caller-defined names. retain source-category codes as source evidence; fixed card groupings must exhaustively include unknown/other rather than discard new categories.

`analysis_map` adds `unavailable_reason,reason_detail` for null cells and `display_cells[{cell_id,mass,density_per100sqft}]`. its native `cells` are 656 ordered masses, not densities; `integrated_value` equals their sum. an unavailable map has both arrays and integrated value null with its reason; an available map has both complete arrays and null reason. supplied display rows use the appendix's `K*T` rule and 668 physical cells. store two fixed grid descriptors: native centers from `shot_origins.grid()`; display rectangles/areas from `observed_spatial.cells()`, mapping identity and `rect5_gaussian10_v1`. no native-area invention. publisher validation may check this fixed linear transport through existing geometry/pooling; producers own numerical mass. no browser smoothing or contour dependency here.

goalie evidence retains goals/expected/attempt masses and unmapped totals separately. display pooling precedes the ratio, with null ratios at undefined denominators and no pseudocount. transport includes `mass_saved`, constituent display masses, ratio and unavailability reason; only additive masses close to totals. danger arrays have 101 fixed edges from 0 to 1 by .01 and 100 bins; exactly-one probabilities enter the final bin. bin expected masses respect their probability bounds and counts. goalie evidence groups use `wrist_snap|slap|tip|backhand|other`; execution breakdowns retain six underlying types `wrist|snap|slap|backhand|tip|other`. source-unclassified types remain outside valued support, not mapped to other without evidence.

`goalie_observed` and each of its game records carry `actual_states:[{state,source_counts,on_net_evidence,unblocked_evidence,stage_evidence}]`, using the same fixed nested evidence records. `goalie_evidence_map` and `goalie_danger` carry `actual_states:[{state,goals,expected_goals,attempts,support}]` for their particular population. states are unique typed skater-count/goalie-presence records; additive quantities reconcile to the containing aggregate while ratios keep their own denominators. goalie strength uses its own team's perspective, `defending_skaters` versus `attacking_skaters`; exact/ev/pk selectors admit their corresponding both-goalie states. `covered_all` retains extra-attacker states, including an absent attacking goalie; the named defending goalie must be present. these are finalized observed/paired strata, not an additional aggregate model.

source `attempt_fact` is keyed by `(season,game_id,source_index)` from the bound v1-01 input. keep nullable/duplicated native `event_id` as evidence, NEVER as its primary/join key. `attempt_value`, setter and share keys use that same source index; reject supplements bound to another prepared input even if game IDs coincide. source facts carry recorded roles/outcome/type/coordinates/strength/support even without numerical output. exchange-only `attempt_value` contains exactly the five estimate fields `actor_all_attempt_opportunity,neutral_all_attempt_opportunity,actor_unblocked_goal_probability,actor_on_net_goal_probability,neutral_goalie_on_net_goal_probability`, plus method/support identity. all inapplicable/uncomputed fields remain typed unavailable. observed stop/reattempt labels stay in source facts. goalie_evidence returns finalized paired summaries/maps/histograms/game records, not an undefined per-event probability stream; actor-conditioned unblocked probability cannot substitute for neutral-goalie unblocked probability. execution owns that paired reduction.

`attempt_setter` and execution shares retain explicit `none`/`unknown` recipients. shooter/setter/goalie person recipients resolve to the person catalog. the single joint coaching share uses `recipient_id="coaching_context"`, with both dated coach inputs retained in method provenance; it is not two individually attributed coach effects. four-group shares sum to actor minus neutral opportunity, not to a player's ledger.

context facts retain the appendix's keys and population enum; replace ambiguous start/end with `period_number,start_seconds,end_seconds`, using period-local elapsed seconds and positive half-open bounds. each `interval_fact` additionally carries required `period_horizon_seconds`, the producer's finalized known horizon: `end_seconds<=period_horizon_seconds`, bounded by 1,200 regulation seconds or 300 regular-season overtime seconds. all records for a game/period agree on that horizon. this field closes an implementation-discovered gap: a scheduled maximum alone does not identify the actual known horizon. the publisher validates the declared source fact without reopening preparation. `interval_id` is a nonempty game-local string chosen by the producer: wherever reused it denotes identical bounds/full membership. each team/population has nonoverlapping rows; membership has five unique skaters on each physical side, and opposing fact rows mirror for/against masses and on-net counts. the publisher validates, never reconstructs, the partition. `dressed_game` fixes the focal team's per-game identity, agrees with season teams and any existing observed player-game. `context_coverage` exists for every skater/population, including pending valued populations. pending coverage has null excluded time, empty measured reason counts and an unquantified gap; references may identify known dependencies. no population silently borrows another's time. unresolved membership makes paired coverage explicitly unquantified; do not assign unknown excluded time to a guessed side. rates sum eligible facts over each group's time, preserving zero-event rows.

## reader and API contract

retain one process-lifetime read-only connection (`readonly:true,disableWAL:true`); its sqlite file is self-contained. startup/check validates physical schema, catalogs, every typed row and required closure using streamed queries; it does not load all event/map arrays into memory. use SQL parameters and fixed query branches. reuse observed season/spatial/deployment checks. ordinary read failures remain errors, not unavailable estimates.

`Publication` exposes `league(selection)`, `player(season,id)`, `maps(selection)`, `evidence(selection)` and `context(selection)`. all return one envelope `{publication,available_seasons,season,sources,methods,supports,...}`. `publication` retains current observed population/version metadata, changes kind to `player_analysis`, adds schema version 7 and family availability. `season` remains identified season evidence, not a bare inferred year. league includes selected-season people only; historical-only identities remain reachable through the player endpoint.

| endpoint | exact selection and response body beyond envelope |
|---|---|
| `/api/league` | optional season/kind/family; defaults newest published/skater/overview. strength as below. `family,kind,strength:null|value,players:[{person,result}]`; no maps/events. overview is the appendix's fixed scalar projection with explicit family envelopes |
| `/api/players/:id` | optional season only. `player_id,kind,person:null|selected identity,families,observed_games,deployment,history`. three ordered publication-year rows `{season,person:null|identity,families}`; compact scalar summaries only. no full league/maps/events |
| `/api/maps` | required season, one/two distinct same-kind comma-separated players, family, strength and view; additional goalie selectors only below. observed response is `{family:"observed",selection:SpatialSelection,scale}` plus envelope; analytical response is `{family,selection,definition,scale,players:[{player_id,result}]}` plus envelope, geometry/catalog once |
| `/api/players/:id/evidence` | required season/family; strength/population/type/filter rules below. returns exact selection and fixed family payload; no silent cap, arbitrary query language or fit execution |
| `/api/players/:id/context` | required season/mode/population; teammates required only for with_without, one/two distinct IDs excluding focal. `mode,selected_players,population,groups,coverage`; each group counts/mass/time/rates and locatable maps where that population permits |

only league/profile default season; explicit unknown season is 404, never another season. invalid/unknown/duplicate selectors or incompatible kind/strength/view are typed 400. unknown person is 404. known person missing this season returns 200 with null selected identity, explicit absent-season result and real history; never substitute another year's name/team as a selected appearance. selected API results use `{availability:"absent",explanation,data:null}` for this case, distinct from stored `provided|not_computed` rows. profile/history `families` adds the known `kind` to that absent envelope; context has an absent coverage record with null excluded time, an unquantified gap and empty reasons/references. the special observed-map response retains its existing null selected data. unavailable/pending families return 200. failed read or malformed stored response is 500 with existing retry copy and local technical logging.

fixed league matrix:

| kind/family | strength |
|---|---|
| skater `observed` | require `5v5` |
| skater `spatial` | require `5v5|5v4|5v3|4v3|4v5|3v5|3v4|pp|pk`; offense/defense only where defined |
| skater `execution|shootiness` | require `5v5|5v4|5v3|4v3|4v5|3v5|3v4` |
| skater `overview|penalties|territory|descriptive|microstats` | omit strength |
| goalie `goalie` | require `5v5|4v4|3v3|5v4|5v3|4v3|4v5|3v5|3v4|ev|pk` |
| goalie `overview` | omit strength |

map `family` is `observed`, one exact `map_kind` from the appendix, or `goalie_evidence`. observed uses 5v5 and `effect|complete`, with its strict observed variant above. spatial map kinds follow their applicable strengths and both views; finishing/setting use execution strengths and effect only; territory uses 5v5/effect; goalie stopping uses modeled goalie strengths/effect. goalie evidence instead requires `population=unblocked|on_net,type=all|wrist_snap|slap|tip|backhand|other,view=evidence_mass|evidence_ratio`. its strength selector is exactly the nine both-goalie states plus `ev|pk|covered_all`; `covered_all` retains separate actual-state records `{attacking_skaters,defending_skaters,attacking_goalie_present,defending_goalie_present}` for extra-attacker evidence, without arbitrary strength strings or a new aggregate model. reject unrelated selectors and incompatible person kinds. known season-absent selections remain explicitly unavailable. additive scale follows the appendix's rule over published display values; ratio uses fixed ±25% without clipping stored values.

evidence families are `personal_shots|execution|goalie|goalie_evidence|penalties|territory|microstats`. personal shots require `strength=5v5` under the appendix's initial geography scope and `outcome=all_unblocked|on_net|goal|save|miss`, optional exact source `shot_type` including unknown, and `blocked_contacts=true|false` default false; return unlocated counts/table rows as well as points. execution requires an execution strength and returns fixed shot-type/danger strata and event values. goalie model detail uses modeled strength; goalie_evidence uses actual strength/population/type. penalties/territory/microstats omit strength and use their fixed factual/modeled definitions. request arrays remain bounded to one player's season; measure actual payload before adding pagination.

context is 5v5 and `mode=on_off|with_without`; use the five named populations from the appendix. focal and selected teammates must be skaters; reject incompatible kind with 400. intersect actual interval memberships, never multiply pair totals. teammates must have contemporaneous same-team dressed evidence for a nonempty together group; known but season-absent/nonoverlapping skaters produce zero supported together time and unavailable rates, not invented teamwork. on/off is restricted to actual dressed team-games. one shared `per60(mass,seconds)` helper returns null at zero time; do not duplicate eligibility or fitted hockey calculations in typescript. selected groups' counts and time reconcile to the eligible focal/game domain. source gaps remain disclosed beside comparisons.

## current application, content and cutover

new code writes/reads schema7 only. remove schema6 branches, `observed_5v5` publication kind, the old API's `spatial=` query and full-league-in-player response. preserve supported observed definitions/reducers; they are current facts, not legacy fallbacks. the observed-only publication command is replaced by `publish --observed --results`; a caller wishing to publish only current facts supplies explicit pending-family dispositions.

current routes request `kind=skater&family=observed&strength=5v5`. profile loads one detail, one league cohort and selected maps; comparison shares one cohort and one ordered map request. a shared client composition function joins these fixed responses for existing components and checks publication/season identity before rendering. it is a current view-model projection, not an old-response decoder. preserve abort signals, deep links, query state, search/sort, peer controls, history, personal cards, maps, deployment and current downloads. no new analytical homepage or chart framework. a direct goalie profile may show identity/history and “goalie analysis presentation is not implemented yet”; it must not render skater values. analytical API fixtures remain inspectable through checks, not a second dashboard.

content reviewer approves these exact distinctions in fixtures: “not computed” for an unwritten family; “tracked primary-pass observations are not available” for shot assists; “historical skating source access is unverified” for skating; “fit failed” for a recorded failed solve; “no eligible exposure” for an undefined rate; “uncertainty not estimated”; and available prior-only specialties labeled hypothetical. show `fixture` prominently throughout current pages. method findings retain weak/rejected evidence without turning it into admission. reusable field labels/reference explanations belong to the shared contract, not arbitrary renderer strings or repeated warning paragraphs.

extend existing operator `check` to validate all schema7 families, including deferred states. preserve incoming exclusive copy/digest checks. activation's incoming candidate uses the new reader; an existing active database is preserved as opaque bytes, not passed through an incompatible reader. this changes predecessor validation, so report its byte identity and leave cross-schema validation to its matching git build. `restore` supports schema7 with its reader; cross-schema restore remains explicit stop/manual copy/rebuild from matching git/restart, not a compatibility reader. use disposable directories for verification. live activation remains a separate assignment and retains one previous database.

candidate building uses `player-analysis.sqlite.incomplete`, strict tables, explicit foreign keys and delete-journal mode. retain existing independent read-back, integrity/foreign-key checks, per-season reconciliation and exact input copies/receipts; write verification before final rename to `player-analysis.sqlite`. failed work leaves no final candidate; refuse existing output. [read-only sqlite](https://www.sqlite.org/uri.html) serves the completed file without source access. do not introduce hot switching, old build archives or crash orchestration.

serialized scalar read-back, integer counts, IDs and support membership remain exact. floating derived closure uses `abs(a-b)<=1e-9+1e-9*max(abs(a),abs(b))` for ledger/map/projection sums and fixed ratios, with no data modification on failure. this is arithmetic comparison tolerance, not scientific adequacy or permission to clip invalid probabilities. retain existing observed checks' stricter applicable invariants.

## acceptance and handoff

temporary end-to-end red → green → refactor → green checks; independent storage, interface and content review; then delete temporary tests/controllers/test-only dependencies. retain compact attributed fixtures, checked expected facts and the verification receipt. no persistent harness is assigned.

| boundary | sufficient evidence |
|---|---|
| exchange → storage → HTTP | compact three-season fixture with each fixed table/family, valid modeled strengths, skaters/goalies, trade, absent selected year, pending family, field-level gaps and prior-only specialty. compare canonical values/units/support/reference through python, sqlite and decoded responses; mixed real/fixture purpose fails |
| closure and independent facts | nontrivial ten-term league/replacement sums; paired map/scalar/native/display closure; goalie evidence mass vs nonadditive ratio; distinct execution denominators; event left join preserves a shot missing fitted values; on/off and two-teammate intersection with zero-event time. calculate expected answers independently of production reducers |
| rejection | malformed/extra fields, duplicate keys/rows, hash mismatch, missing promised member/disposition, dangling metadata, invalid IDs/kind/strength, unsafe/nonfinite numbers, wrong units, negative complete rates, out-of-range probability, map/ledger mismatch and fabricated source admission. corrupt input rejects; never repair by zero fill or relabeling as unavailable |
| observed preservation | existing captured-game fixtures through the same observed reducer before/after: exact counts, time, rates, reasons, personal/spatial facts, pairs and history. changed metadata/schema is expected. no full-corpus rerun merely to verify transport |
| API/content | all five endpoints, duplicate/incompatible/unknown queries, 200 partial vs 400/404/500, absent season without substitution, synthetic banner, cancellation and mixed-publication rejection. all method/source references resolve offline |
| browser | disposable fixture server in an isolated worktree/unused port: existing table/profile/comparison, deep-link/back, filters, error states, current png and selected missing-season/goalie states. targeted narrow/native 200% check for changed states; no final analytical-card/export claim |
| operation | candidate/check succeed after input directories become inaccessible; database hash unchanged and no wal/shm. bad candidate/occupied destination refuse; disposable activation preserves predecessor bytes, compatible restore works and cross-schema restore instructions identify the matching build. primary files/listener unchanged |

record database size, build/check/startup time, peak memory and representative response bytes; stream facts instead of materializing corpus arrays. fix measured problems at their owner; no speculative cache/pagination/service. useful evidence is a small source-to-read receipt, not an acceptance platform.

handoff: v1-03/06–12 implement real family serialization through `write_results`; v1-14 consumes the fixed scalar/history/support contracts; v1-15–19 implement actual card compositions; v1-20 closes remaining real paths and separately assigned delivery. coordinate only shared CLI/entry-point edits with v1-01. publish no assertion that fixtures, software completion or a partial candidate complete the five-card product.
