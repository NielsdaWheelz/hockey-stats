# experimental player analysis — publication and application

application appendix to the [program specification](experimental-player-analysis.md). [the plan](../plan.md) alone owns assignment and status. this specifies the complete interface, including partial integration; it authorizes no activation by itself. [chance/execution](experimental-chance.md) and [attribution](experimental-attribution.md) own equations, populations and accounting.

## boundary

extend python → sqlite → effect → react. publish 2023–24, 2024–25 and 2025–26; five fitting/history seasons do not imply five display seasons. retain observed facts and their separate on-ice, personal and spatial populations. one player profile supports skaters or goalies; comparisons require the same kind.

python supplies finalized quantities, maps, references and evidence. sqlite sums selected facts; effect validates/reads and computes `3600*mass/eligible_seconds` for dynamic context, returning null at zero time. reuse one helper for that existing arithmetic, including related validators. react selects peers, sorts and renders. no sql/typescript model estimation, model service, second dashboard, plugin registry or browser inference.

## schema 7

one strict sqlite schema; `publication.kind='player_analysis'`, `purpose='real'|'fixture'`. preserve observed tables and facts; separate shared identity from skater-only observed records so goalies acquire no invented skater metrics. `person(season,player_id,kind,display_name,reported_position,teams_json,source_json)` supports `kind='skater'|'goalie'`, including position `G`.

the following concrete tables use indexed primary keys below and a `payload_json` decoded against their fixed strict schema. this keeps uncertainty/missingness structured without an arbitrary metric/value registry. no unrecognized fields or free-form metric names. small shared metadata tables avoid repeating method descriptions in every cell.

| table / key | fixed payload fields |
|---|---|
| `analysis_method(method_id)` | `family`, `recipe_id`, `design_sha256`, `input_sha256`, `fit_seasons`, `training_cutoff`, `target`, `population`, `reference`, `limitations`, `evidence` |
| `skater_spatial(season,player_id,strength)` | `offense_attempts_per60`, `defense_attempts_per60`, `offense_xg_per60`, `defense_xg_per60`; corresponding `*_complete` fields for focal reference rates; `support`, `method_id` |
| `skater_execution(season,player_id,strength)` | `finishing_goals_per100_attempts`, `setting_goals_per100_assisted_opportunities`, `avoid_block_probability`, `on_net_probability`, `recorded_stop_probability`, `conversion_probability`, paired `*_difference` fields for those four stages, `support`, `method_id` |
| `skater_shootiness(season,player_id,strength)` | `probability`, `difference`, `support`, `method_id` |
| `skater_penalties(season,player_id)` | `drawn_per60`, `taken_per60` signed team-award contrasts; `drawn_value_per60`, `taken_value_per60`; separate `recorded_drawn`, `recorded_taken`, `recorded_served` counts/support; `support`, `method_id` |
| `skater_territory(season,player_id)` | `ice_won_goals_per_basket`, `ice_lost_goals_per_basket`; fixed `exit_offense`, `entry_offense`, `zone_retention`, `entry_prevention` records defined below; `support`, `method_id` |
| `goalie_result(season,player_id,strength)` | `stopping_goals_per100_on_net` (already a contrast); `miss_probability`, `recorded_stop_probability`, `conversion_probability`, `recorded_reattempt_probability`, `reattempt_neutral_goal_probability`, `followup_danger`, paired `*_difference` fields for those six levels only; `support`, `method_id` |
| `goalie_observed(season,player_id,strength)` | `included_seconds`, `shots_on_goal`, `goals_against`, `saves`, `save_percentage`, `expected_goals`, `goals_saved_above_expected`, `starts`, `relief_appearances`, `workload`, `coverage`, `games` |
| `value_ledger(season,player_id)` | `reference_minutes`, ten named `components`, `league_total`, `replacement_total`, `method_id` |
| `analysis_map(season,player_id,map_kind,strength,view)` | `grid_id`, `unit`, `reference`, `cells`, `integrated_value`, `support`, `method_id` |
| `execution_breakdown(season,player_id,strength,kind,stratum)` | `events`, `eligible_weight`, `observed_successes`, `expected_successes`, `probability`, `effect`, `support`, `method_id` |
| `adjustment_decomposition(season,player_id,strength,target)` | `baseline`, `self`, `teammates`, `opponents`, `coaching_other_context`, `numerical_residual`, `factual_prediction`, `method_id` |

skater spatial strengths are `5v5|5v4|5v3|4v3|4v5|3v5|3v4`: 5v5 has both roles, pp offense and pk defense only. goalies additionally retain `4v4|3v3`; producer-computed `ev` and `pk` summaries combine respectively `5v5/4v4/3v3` and `4v5/3v5/3v4`, with both goalies present. modeled goalie groups use common training-panel neutral-on-net weights; observed groups sum actual records. unsupported combinations fail. extra-attacker states remain separate observed evidence.

`map_kind` is exactly `offense_attempts|defense_attempts|offense_xg|defense_xg|finishing|setting|ice_won|ice_lost|goalie_stopping|goalie_saved_above_expected`. `kind` is `shot_type|danger`; retain the six shot types and fixed danger bins `<.05`, `[.05,.15)`, `>=.15` on the numerical appendix's neutral on-net goal probability, never browser quantiles.

the ledger's named components are `five_on_five_offense`, `five_on_five_defense`, `power_play_offense`, `penalty_kill_defense`, `finishing`, `setting`, `penalties_drawn`, `penalties_taken`, `ice_won`, `ice_lost`. each has `league_goals` and `replacement_goals`. use the approved 1,000-minute 5v5 + 100-minute pp + 100-minute pk workload and numerical state mixture. positive ledger values benefit the player's team. do not add shootiness, outcome stages or transition subskills again. totals reconcile under the numerical accounting rule; replacement is the declared team-depth reference, not the league baseline.

shared types:

```text
estimate = { value: finite-number|null,
  unavailable_reason: null|not_applicable|no_exposure|missing_source|failed_fit|not_computed,
  uncertainty: {kind:not_estimated} |
    {kind:interval,lower,upper,level,method,conditional_on} }
support = {included_seconds,events,eligible_weight,known_excluded_seconds,
  unquantified_gap:boolean,reason_counts,inferred_inputs,
  current_season_information:boolean,prior_only:boolean,prior_seasons}
cell = {cell_id,value:finite-number}
```

value and unavailable reason are exclusive; intervals are ordered and identify their method. shared estimate fields carry this type. probabilities lie in `[0,1]`; signed effects may be negative. `defense_*` means change in against rate, not a favorable-sign inversion. execution stage levels are ratios of integrated prefix products on the common training-only opportunity panel; `*_difference` is focal minus neutral. finishing/setting use the stated common-panel denominators. goalie stopping reverses allowed-goal direction; its positive contrast is neutral minus focal `r*g` per 100 on-net opportunities. actual neutral-goalie expected-minus-observed evidence remains separate. unavailable uncertainty is not zero width. a valid prior-only estimate remains available and explicitly hypothetical; zero observed support does not become invented evidence.

execution and goalie `support` are fixed records with one support value per named estimate, since conditional stages have different denominators. other families share support only where their numerical contract establishes a common population. no generic support inferred from a player's overall minutes.

territory exit/entry records contain `hazard_per_second`, `one_second_probability=1-exp(-q)` and support. retention/prevention instead contain `opponent_exit_hazard_per_second` / `opponent_entry_hazard_per_second` and `one_second_probability=exp(-q)`: conditional fixed-zone avoidance of that opponent transition. do not label the opponent's transition probability as the player's retention probability. whole-zone movement probabilities still use the numerical generator.

map grids have explicit geometry, orientation and cell area. stored cells are **mass**, summed directly: attempts/xg per 60 for spatial rates; goals per 100 attempts for finishing; goals per 100 assisted opportunities for setting; goals per basket for territory; goals per 100 on-net for modeled goalie stopping; goals for observed saved-above-expected. execution maps deposit the same normalized common-panel contributions into their origin cells. density rendering divides by area and labels that conversion. `view=effect|complete|evidence`: spatial effects and complete rates are separate rows; execution/territory/stopping use effect; saved-above-expected uses evidence. paired panels share a scale. unavailable maps have `cells=null`, never zero fill. preserve observed versus inferred origins. complete chance rates satisfy `0<xg<=attempts`; signed contrasts have no such order constraint.

adjustment `target` is `for_attempts_per60|against_attempts_per60|for_xg_per60|against_xg_per60`; exact four-group shapley allocations of the complete quantity plus baseline close to the factual prediction. chance allocations evaluate the joint count×quality model, not an independently averaged quality map. `numerical_residual` is tolerance only, not skater credit. omitted cross-component ledger interactions are a disclosed convention, not a residual to add.

## finalized evidence and with/without

`attempt_fact` is keyed by `(season,game_id,event_id)`: period/time, team, shooter/goalie ids, actual skater/goalie counts, outcome/type, recorded coordinates/meaning, `actor_all_attempt_opportunity`, `neutral_all_attempt_opportunity`, `actor_unblocked_goal_probability`, `actor_on_net_goal_probability`, `neutral_goalie_on_net_goal_probability`, nullable `recorded_stop`/`recorded_reattempt` labels with reasons, and support identity. conditional values require their applicable population; opportunity is not a factual blocked-shot forecast.

construct these rows from authoritative source facts, then left-join model results by the full event key. source-supported shooter/outcome/location facts survive unavailable type, context or fitting eligibility; each unavailable model field carries its reason. missing fitted output cannot delete a recorded shot.

`attempt_setter` adds `candidate_id` (`none|unknown|person id`), `pre_outcome_weight`, nullable `posterior_weight` and recorded assist evidence. `attempt_execution_share` adds `group`, `recipient_id` and signed `goals`; group is `shooter|setter|goalie|coach`, with unknown recipients explicit. all keys include season/game/event. probabilities, inferred retrospective credit and signed goal allocation are different fields; none becomes a recorded assist.

personal geography defaults to **all source-supported unblocked personal attempts** in the selected season/strength, initially 5v5: goals, saves and misses with corroborated shooter and event-strength evidence. elapsed exposure and chance-fit eligibility are not prerequisites. plot unsmoothed recorded points; unknown/conflicting locations remain in the counts and accessible event table, not on the rink. outcome filters are `all_unblocked|on_net|goal|save|miss`; the shot-type filter uses the authoritative source types plus unknown, without forcing them into the six model categories. a separate default-off blocked-contact layer reports its own counts/coverage and explicitly says “contact, not release.” no inferred release replaces these points.

show counts, shot mix and location coverage, e.g. “122 of 130 supported unblocked attempts located”; no personal-spatial per60 denominator or league-relative density is introduced. cards/tables/maps use the same filters and event keys. this event-supported population may exceed the existing stricter matched personal-credit population: name that distinction, preserve its existing rates, and never force the two totals to agree. unresolved shooter/strength associations remain unattributed with source-gap evidence, not assigned to this player. ordinary map exports retain this source/population meaning.

for 5v5 context, publish `interval_fact(season,game_id,interval_id,team_id,population,start,end,support_id,for_mass,against_mass)` keyed by its first five fields; `interval_player(season,game_id,interval_id,team_id,player_id)`; and sparse `interval_location` with the full fact key plus `cell_id,for_mass,against_mass`. `population` is exactly `recorded_all_attempts|recorded_locatable_unblocked|neutral_locatable_unblocked_value|neutral_all_attempt_value`. each owns matching eligible time/gaps; zero-event intervals survive. context maps exist only for the two locatable-unblocked populations, closing to their respective unblocked scalar. all-attempt counts/value remain separate scalar views; no block mass is silently dropped or expanded into a large context map store. full fitted player maps still include inferred origins. never join masses across populations. these are finalized facts, not a second reconstruction.

the focal skater may select one or two teammates. together means all selected teammates present; apart means focal player present with at least one selected teammate absent. intersect memberships, then sum the selected population's mass, seconds and available location rows. never multiply pair totals or subtract mismatched populations. selected players, gaps and denominators appear beside both panels. no causal chemistry claim. replacement comparison is a modeled reference, not an observed “apart” population.

also provide focal on/off results over the player's source-supported dressed team-games only. on is eligible team time with that skater present; off is eligible team time with that skater absent. resolve the player's team per game, including trades. use the same family support for counts, expected sums, locations and time; neither the rest of the league nor games the player did not dress enter “off.” zero off-time is unavailable, not a zero rate. both comparisons reuse these facts and readonly sums.

## effect api and routes

extend the existing `Publication` service and typed http api. every response includes publication/season identity; method descriptions are returned once by id. all model fields follow the concrete schemas above.

| request | response |
|---|---|
| `GET /api/league?season=&kind=&family=&strength=` | `publication,available_seasons,season,family,methods,players`; identity, observed support and selected fixed-family scalars; no maps |
| `GET /api/players/:id?season=` | selected identity/family scalars, observed games, deployment, three-season history, methods; no league-sized maps |
| `GET /api/maps?season=&players=&family=&strength=&view=` | one/two distinct same-kind players, definition/reference, shared scale, selected maps/support |
| `GET /api/players/:id/evidence?season=&family=` | selected player's finalized event/breakdown evidence and support |
| `GET /api/players/:id/context?season=&mode=&population=&teammates=` | `mode=on_off|with_without`; selected game/group population, paired facts/maps/support; teammates required only for with/without |

`kind=skater|goalie`; league `family=overview|spatial|execution|shootiness|penalties|territory|goalie|observed` is a typed union of those fixed row schemas, default overview. strength-specific families require strength; other families omit it. map family/view combinations follow their fixed meanings; evidence `family=personal_shots|execution|goalie|penalties|territory`. replacement is a ledger comparison, not an undefined map transform. context requests select one explicit population. invalid/duplicate selectors return typed 400; unknown season/person returns 404; failed reads return 500. a person known in another published season retains history with unavailable selected-season results, never a substituted season or invented appearance. unavailable estimates are not 404. preserve cancellation and readonly process-lifetime publication.

retain `/`, `/players/:id`, `/compare`. canonical query state selects season, family, strength, reference and peers; comparisons keep the existing two pickers and profile shortcut. do not add a separate goalie app. scalar league payloads support sorting/distributions; fetch selected maps/details separately.

profile/comparison loaders obtain one league scalar payload for the selected season/kind alongside selected-player detail. reuse that cohort across cards/distributions, not separate requests per metric. historical percentiles, when displayed, use that historical season's cohort; never apply today's distribution to an earlier estimate.

## content and interaction

| family/view | content that constitutes completion |
|---|---|
| overview | all ten contributions and reconciled total; league-relative headline, replacement alongside; hypothetical workload and observed actual usage both visible |
| spatial | offense/defense at 5v5 and declared pp/pk states; scalar above map, units/baseline/support; more/fewer legends without hidden defensive sign changes |
| execution | the personal source geography defined above; finishing/setting, shootiness and conditional stages with denominators/type/danger detail; inferred setting clearly named |
| territory/penalties | ice won/lost plus four explanatory subskills; ordinary-minor drawing/taking effects, separate recorded personal counts, model exposure/exclusions and value; no implication of all penalty minutes or duplicated credit |
| goalie | stopping and observed/expected goals/saves; ev/pk, location/type/danger, outcome subskills and workload; no invented overall goalie value |
| context | deployment, focal on/off, with/without, and player/context explanation with interaction/residual; exact dressed-game/group membership and support |
| history | three-season modeled trajectories beside observed history; visible definition changes and gaps, no interpolated missing seasons |
| tables/comparison | specialist family columns, raw magnitudes, percentiles, exposure and distributions; same-kind comparisons use identical units/reference |

same F/D peer groups remain default. viewing defaults: 300 included 5v5 minutes for general skater metrics; 50 relevant minutes for pp/pk; 300 included ev minutes for goalies. these are explicit product judgments, adjustable and not reliability thresholds. expose cutoffs and cohort sizes. qualify each metric using its own supported opportunity; below-cutoff values remain visible but numeric percentiles are withheld. mixed F/D comparisons retain separately labeled peer groups. prior-dominated specialties cannot borrow an unrelated minutes denominator to imply experience.

observed percentiles still increase with recorded rate, including against. modeled component percentiles use the displayed quantity's declared direction. estimated rank is not reliable separation. show experimental status once prominently, units/reference locally, and expandable method/evidence; avoid repeating warning paragraphs under every number. unknown uncertainty reads “not estimated.” synthetic fixtures are separately labeled and never mixed with real players.

export a single-player png card, selected map png and visible table csv from the same view model as html. include season/strength, units/reference, workload, model identity, coverage and experimental meaning. no export-only hockey calculations. csv uses a normal column header and explicit metadata columns, without comment lines; card text must survive saving without surrounding webpage context.

## owners, cutover and acceptance

- python: extend `publication.py` and its cli; `analysis_publication.py` owns substantial new family serialization/closure. numerical producers own values and source identities.
- effect: new `shared/player-analysis.ts`, `server/analysis-publication.ts`; extend `server/publication.ts`, `main.ts`, operator and `web/client.ts`. preserve existing observed/spatial/deployment owners.
- frontend/content: extend the three route files, `explorer.ts`, picker/distributions and `spatial-views.tsx`; add cohesive `analysis-card.tsx`, `analysis-details.tsx`, `analysis-history.tsx`, `with-without.tsx`. extract existing svg→png conversion only for its actual second consumer.

reader accepts schema7 only. operator validates incoming with that reader; preserve schema6 active bytes opaquely rather than reading them with the new schema before rotation. for a cross-schema restore, stop, validate `previous.sqlite` using its matching git build, manually copy it over active and restart that build; do not call an old rotate command that tries to validate the schema7 active file. retain one previous database, not archived builds or a multi-schema fallback. activation remains explicitly assigned.

verify real source/result → sqlite → effect → table/profile/map/comparison/history/export for every required family; fixtures alone do not complete it. cover source shots excluded from fitting, personal location gaps and filters, goalie identity, zero exposure, unavailable/failed results, uncertainty, inferred credits, dressed-game on/off and with/without intersections, ledger/map closure, three-season cutoffs, synthetic isolation and prior observed facts. check detached browsing, keyboard/narrow layouts/native 200% zoom, export text, candidate rejection and ordinary restore. validate changed numerical contracts at their owner; downstream checks establish faithful transport/content, not scientific admission. record database size, build time and representative read/render costs; fix demonstrated problems without adding a service/cache framework.

use assigned temporary integration/live red → green → refactor checks and adversarial source/numerical/content review; delete campaign-only checks afterward. retain fixtures and only separately selected stable regressions. no calibration/recovery campaign is an application acceptance prerequisite.
