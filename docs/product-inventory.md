# product capability inventory

this page owns the five v1 card field crosswalks and the wider catalogue of player-analysis views. the [brief](brief.md) owns product choices. the [feature repertoire](model-features.md) covers inputs and encoders. the [plan](plan.md) owns assignments.

## v1 card completion boundary — 2026-10-22

v1 delivered the complete private experimental card compositions for 2023–24, 2024–25 and 2025–26. the installed schema 12 publication closed 104 obligations as follows. counts refer to contract rows. a row can include several quantities or a whole view. [whole-card verification](research/application-v1-20/verification.md) · [row-level proof](/Users/nnandal/Documents/hockey-stats/local/application-v1-20-20261122/card-closure.json)

| card | checked on the real publication | evidenced source gap | user-deferred | composition and producer evidence |
|---|---:|---:|---:|---|
| analytical skater | 24 | 0 | 0 | [four maps, skills and ledger](research/application-v1-18/verification.md) · [real value accounting](research/value-v1-12/verification.md#real-candidate-and-live-acceptance) |
| descriptive skater | 13 | 0 | 0 | [recorded facts](research/facts-v1-03/real/verification.md) · [scoring, workload and context sheet](research/application-v1-16/verification.md) |
| goalie | 14 | 0 | 0 | [stopping and conditional subskills](research/goalies-v1-07/verification.md) · [goalie sheet and discovery](research/application-v1-19/coverage.md) |
| comparative skater | 18 | 0 | 0 | [comparative card and discovery](research/application-v1-15/verification.md) · [release csv and png](research/application-v1-20/verification.md) |
| microstat skater | 12 | 22 | 1 | [available metrics and exports](research/application-v1-17/verification.md) · [source dispositions](issues/microstat-inputs.md) |
| **total** | **81** | **22** | **1** | [final activated publication](research/application-v1-20/verification.md#final-activation-and-live-verification) |

the release closes the five compositions on their stated populations. two conditions explain the missing microstat numbers. required tracked observations are absent from the admitted public corpus. skating acquisition and integration were explicitly deferred despite a promising public source. estimated ability, uncertainty calibration and numerical equivalence to peer products require separate evidence. [reference scope](research/player-card-references.md#v1-field-audit--2026-10-22) · [release review](research/v1-review.md)

### v1 field crosswalk and card acceptance

read each row as the contract for its field, population, data owner and presentation. the original source codes date to the 2026-10-22 audit. **e** was an existing observed quantity, **p** an admitted fact requiring a reduction, **m** an experimental estimate, **t** a field requiring absent tracking and **s** a documented public skating field subsequently deferred. use the closure table above for delivered status.

common to all cards are selected season and identity, workload and its coverage, units, reference, cohorts and their size, method and publication identity, missing or prior-only states and access to field evidence. the page and csv carry the detailed provenance. pngs retain the context needed to interpret the image. annual gaps remain visible and source changes have traceable identities. [factual definitions](specs/experimental-card-facts.md#source-boundary-and-shared-ownership) · [identity and usage](specs/experimental-card-facts.md#identity-and-reported-usage) · [execution accounting](specs/experimental-chance.md#execution-accounting-and-goalie-views) · [shared presentation and payloads](specs/experimental-application.md#card-compositions-and-shared-display-rules)

#### isolated skater — s07 and public isolated-impact guide

| id / required slot | canonical quantity, payload and owner | readiness / content acceptance |
|---|---|---|
| i01–i04 four maps | `analysis_map(offense_attempts,5v5)`, `(offense_attempts,pp)`, `(defense_attempts,5v5)`, `(defense_attempts,pk)`; `spatial_rates.project_spatial` | m; attempted-shot density, shared scales, against sign preserved; exact-state detail and declared pp/pk mixture |
| i05 four xg insets | matching `skater_spatial.*_xg_per60`, `*_neutral`, `*_relative_percent`; [card projections](specs/experimental-attribution.md#card-projections-and-shared-quantities) | m; inset xg is separate from attempt-map mass; own complete and neutral rates accessible |
| i06 shootiness | `skater_shootiness(5v5).probability,neutral_probability,difference`; [v1-10](specs/v1-10-penalties-shootiness.md) | m; probability/percentage-point difference, common unit, exact-state qualification and pooled coefficient support; no additional value addend |
| i07 finishing distribution | `skater_execution(5v5).finishing_goals_per100_attempts`; execution | m; raw-unit empirical peer distribution/marker, neutral zero; no uncertainty claim |
| i08 setting distribution | `setting_goals_per100_assisted_opportunities`; same execution owner | m; inferred setting, distinct denominator; never observed shot assists |
| i09–i10 drawn/taken distributions | `skater_penalties.drawn_per60,taken_per60`; [v1-10](specs/v1-10-penalties-shootiness.md) and [ordinary-minor model](specs/experimental-attribution.md#penalties) | m; signed 5v5 team-award contrasts; taking positive means more penalties. typed complete/neutral/valuation evidence; common-workload contributions remain v1-12 |
| i11–i20 ten connected contribution labels | `value_ledger.components`: `five_on_five_offense`, `five_on_five_defense`, `power_play_offense`, `penalty_kill_defense`, `finishing`, `setting`, `penalties_drawn`, `penalties_taken`, `ice_won`, `ice_lost`; [v1-12](specs/v1-12-value-ledger.md), `player_value` [accounting](specs/experimental-attribution.md#ten-term-ledger-and-depth-reference) | m; each league/replacement goals per common 1,000/100/100-minute workload; full seven-state execution construction and component-specific support in detail; no percentile/subskill double count |
| i21 headline totals and reference explanation | `value_ledger.league_total,replacement_total,reference_minutes`; same owner; [annual reference and row evidence](specs/experimental-application.md#value-ledger-evidence) | m; exact unrounded sum iff all ten terms exist; league headline/depth reference alongside. complete team-position groups, fixed common member weights and exclusions are inspectable; not private sG or war |
| i22 four execution subskills | `skater_execution` block avoidance, on-net, recorded-stop, conversion levels/differences, fixed panel/coefficient support; `execution_breakdown`; [conditioning](specs/experimental-chance.md#execution-accounting-and-goalie-views) | m; standardized season/exact-strength skills with each denominator; separate type/danger paired recorded goals and neutral/actual-actor expectations. no skill×stratum expansion or observed-pass claim |
| i23 four territory subskills/maps | `skater_territory.exit_offense,entry_offense,zone_retention,entry_prevention`; `analysis_map(ice_won/ice_lost)`; [v1-11](specs/v1-11-territory-successor-value.md), [finite evidence](specs/experimental-application.md#territory-evidence-projection) | m; hazard/probability and successor-value maps stay distinct, not tracked entries/exits. known-path qualification versus zone risk, terminal proxy, starts and per 1,000-minute accounting remain inspectable; ledger contributions belong to v1-12 |
| i24 history/explanation | three annual rows of i05–i23; `adjustment_decomposition`; shared history/detail | m; raw component/subskill trajectories and declared baseline/self/context breakdown; no interpolated gaps or new fit |

one full-rink sheet combines four maps, four skill distributions and ten signed component values. support for each head/state and the diagnostic actual-context breakdown belong in detail. [sheet contract](specs/v1-18-analytical-skater-sheet.md)

#### descriptive skater — public full skater card

| id / required slot | canonical quantity, payload and owner | readiness / content acceptance |
|---|---|---|
| d01 identity/appearances | `person` and `skater_descriptive.reported_usage`; factual identity/usage owner | e/p; dated age/height where known, season teams and supported/listed appearances |
| d02 usage stack | `reported_usage` plus `strength_usage(ev,pp,pk,other)`; [usage](specs/experimental-card-facts.md#identity-and-reported-usage) | p; all-strength reported minutes/appearance, included strength minutes, explicit gap and denominators |
| d03–d04 ev/pp scoring bars | `scoring_by_strength` goals, primary assists and primary-point rates; [scoring](specs/experimental-card-facts.md#scoring-and-recorded-goal-context) | e for current 5v5 components; p for ev/pp; goals+primary assists reconcile; published matched counts/other states in detail. official/secondary/full-point totals remain upstream source evidence, not invented card values |
| d05 workload/scoring guides | same reported usage and scoring in declared F/D peers | p; empirical guides, no invented first-line skill threshold |
| d06 attempt on/off scatter | `on_off_attempts.on,off,league`: for/against rates, share-minus-half, counts/time | e/p; existing matched attempts, dressed-game off and physical team-time league reference; inverted y is visual only |
| d07 goal on/off scatter | `on_off_goals`, `recorded_goals` context population | p; recorded goals, no shooter-credit requirement or covert xg substitution |
| d08 shooting/saving bars | `on_ice_conversion`: for/against shooting fractions and save fraction, team/league references | p; on-net denominator, separate recorded proportions, not finishing/goalie ability |
| d09 recorded penalty bars | `recorded_penalties.drawn,taken,served`, classes and matched reported time; [penalties](specs/experimental-card-facts.md#recorded-penalties-and-deployment) | p; all-strength infraction rates per 1,000 reported minutes, distinct from i09/i10 |
| d10 shift-start composition | `deployment.focal/team/league.shift_starts` counts/shares O/N/D, proven on-the-fly and unknown | p; same start denominator, no missing-faceoff→on-the-fly inference |
| d11 score deployment | `deployment.score` leading/tied/trailing seconds/shares and unknown support | p; elapsed pre-score integration, not event frequency |
| d12 teammate/opponent context scatter | `skater_context` F/D usage-band coordinates, raw weighted usage and coverage | e/p; pair seconds already exist; reported counterpart usage/ranks are new factual reduction, not fitted quality |
| d13 history/evidence/footer | annual factual rows and game records, source/coverage/unit/reference keys | e/p; three-season table/selected-field history, required method/support text in png |

scoring and usage bars sit beside two on/off scatter panels, deployment and teammate/opponent context. game counts, elapsed support and availability reconcile to their season totals. [factual reductions](specs/v1-03-factual-card-reductions.md) · [sheet and export](specs/v1-16-descriptive-card-context.md)

#### goalie — public saving/type/danger examples and documented subskills

| id / required slot | canonical quantity, payload and owner | readiness / content acceptance |
|---|---|---|
| g01 identity/appearances/workload | `person`, `goalie_observed` reported usage, starts, relief/unknown start status, games | p; recorded time versus modeled/evidence support distinct |
| g02 stopping headline/distribution/map | `goalie_result.stopping_goals_per100_on_net`, modeled `analysis_map(goalie_stopping)` | m; common-panel ev/pk, favorable prevention sign; no invented overall goalie sG/war |
| g03 recorded outcomes | `source_counts.unblocked_attempts,misses,shots_on_goal,saves,goals_against,save_percentage` | p; misses+saves+goals and saves+goals identities, reported totals separately identified |
| g04 paired expected results | `on_net_evidence` and `unblocked_evidence` expected goals, observed goals, saved-above-expected, goals per100 expected; [conditional evidence](specs/experimental-chance.md#goalie-card-evidence-and-conditional-summaries) | m; two different questions/supports, never interchangeable xga; expected save fraction only on-net |
| g05 difficulty inset | mean neutral-goalie probability, matched league mean and relative percent | m; own actual opportunity mix, not stopping ability |
| g06 evidence map/legend | `goalie_evidence_map` goal/expected masses, mass-difference and league-relative ratio display | m; additive saving mass closes; ratio does not sum; underlying masses/support inspectable |
| g07 type panels | wrist+snap, slap, tip/deflection, backhand plus other/detail; matching attempts, goals, expected goals/maps | p/m; no lost other/unclassified counts; unblocked default and explicit on-net option |
| g08 danger comparison | `goalie_danger` fixed-bin actual/expected goal densities and totals; three danger tiers separately | m; independent nonnegative density definition, no copied unknown signed-centering formula |
| g09–g11 outcome subskills | `goalie_result.miss_probability,recorded_stop_probability,conversion_probability` with differences/support | m; conditional complements/prefix weights, probability/percentage-point units; no goalie block-avoidance effect |
| g12 continuation subskills | `recorded_reattempt_probability,reattempt_neutral_goal_probability,followup_danger` with differences/support | m; same saved-shot reference, joint `E[h*d]`, recorded continuation proxy rather than physical rebound assertion |
| g13 observed stages/workload evidence | `stage_evidence` labeled successes, denominators, expected sums; per-game counterparts | p/m; source unknown terminal spans remain unknown; real workload and conditional evidence |
| g14 history/selection/explanation | three annual stopping/observed/subskill rows and cohorts, exact strength/population/reference/method keys | m/p; embedded stopping history, subskill trajectories in detail, same-kind comparison and coherent card/plot pngs |

even-strength stopping leads, with penalty-kill stopping available. saving evidence defaults to the unblocked population in the selected state group. the full-rink additive saving map leads, with a ratio toggle. the sheet embeds four shot-type panels, difficulty/danger, raw stopping history and six subskill distributions. exact-state, stage, game and prior details support inspection. [goalie numerical contract](specs/v1-07-goalie-continuation.md) · [complete sheet and detail](specs/v1-19-goalie-card-discovery.md#complete-sheet-and-detail)

#### comparative skater — s01 and public player-card guide

| required slot | canonical quantity / owner | readiness / presentation |
|---|---|---|
| identity/usage header | same `person`/reported usage as d01/d02 | e/p; no forecast/cap/first-line rating |
| headline and replacement | same i21 ledger totals; same-position cohort | m; common-workload magnitude plus percentile, replacement magnitude alongside |
| 5v5 offense / defense / pp / pk / finishing tiles | same five named i11–i20 ledger contributions | m; favorable goal-contribution percentile; raw rate/skill and support in detail |
| goals / primary-assists tiles | existing `PersonalMetrics.goals_per60,primary_assists_per60` | e; recorded 5v5, own personal support; never projections or latent setting |
| penalties tile | `value_ledger.penalties_combined` | m; drawn+taken once, split visible |
| competition / teammates tiles | `skater_context.opponents,teammates.usage_minutes_per_appearance` | p; source usage proxy weighted by shared 5v5 seconds, not skill or shared minutes alone |
| embedded headline history | three annual league-total percentiles/magnitudes | m; each year's peer population/cutoff |
| embedded component history | three annual 5v5 offense/defense/finishing percentiles/magnitudes | m; same ledger values, no three-year forecast/trailing average |
| footer/detail/export | common metadata, explicit observed/model tiles, n/cutoff, workload/prior-only roles and scoped numerical findings; all ten components in detail | m/e/p; compact png includes both histories; v1-20 adds 27-row whole-card csv with full field/annual evidence |

the ten tiles use the same recorded facts, usage and ledger values as the other cards. two embedded histories and a compact interpretation footer accompany the png. the csv has 27 current/annual rows with full evidence. both totals are available for 2,783 of 2,784 skater-seasons. the remaining row lacks supported finishing and setting. [comparative card](specs/v1-15-comparative-card-discovery.md) · [final export contract](specs/v1-20-whole-card-closure.md#comparative-card-and-downloads)

#### microstat skater — s02 and documented F/D variants

`skater_microstats` exposes thirty scalar keys across twenty-nine reference slots. skating contains two keys. the factual producer owns the reductions, execution owns reference xg and the source owner admits tracking/skating observations.

| field / payload key | card | readiness |
|---|---|---|
| goals / `goals_per60` | f,d | e |
| reference xg / `reference_xg_per60` | f,d | m |
| unblocked attempts / `unblocked_attempts_per60` | f,d | p |
| primary assists / `primary_assists_per60` | f,d | e |
| hits / `hits_per60` | f,d | p |
| reference expected assists / `primary_pass_xg_per60` | f,d | t |
| primary shot assists / `primary_shot_assists_per60` | f,d | t |
| entries / `zone_entries_per60` | f,d | t |
| possession entries / `possession_entries_per60` | f,d | t |
| exits / `zone_exits_per60` | f,d | t |
| possession exits / `possession_exits_per60` | f,d | t |
| in-zone attempts / `in_zone_attempts_per60` | f | t |
| rush attempts / `rush_attempts_per60` | f | t |
| attempts off dangerous passes / `high_danger_pass_attempts_per60` | f | t |
| in-zone shot assists / `in_zone_shot_assists_per60` | f | t |
| rush shot assists / `rush_shot_assists_per60` | f | t |
| high-danger passes / `high_danger_passes_per60` | f | t |
| skating / `skating_max_speed_mph`, `skating_bursts_over20_count` | f; one slot, two honest measures | s; user-deferred, explicitly unfinished |
| forecheck involvement / `forecheck_involvements_per60` | f | t |
| defensive-zone touches / `defensive_zone_touches_per60` | f | t |
| pass exits / `pass_exits_per60` | d | t |
| carry exits / `carry_exits_per60` | d | t |
| defensive-zone retrievals / `defensive_zone_retrievals_per60` | d | t |
| successful retrievals / `successful_retrievals_per60` | d | t |
| shot-assisting passes / `shot_assisting_passes_per60` | d | t |
| source puck management / `puck_management_xga_saved_per100_plays` | d | t; source-modeled, outside our ledger |
| entry denial / `entry_denial_fraction` | d | t |
| possession-entry denial / `possession_entry_denial_fraction` | d | t |
| blocking share / `blocked_attempt_share` | d | p |

each position shows twenty slots. forward has five measured or derived fields, fourteen tracking gaps and one deferred skating slot. defense has six measured or derived fields and fourteen tracking gaps. unknown position has a labeled 29-slot union. the six checked union fields and the six ledger rows in detail yield the twelve checked obligations. the modeled strip and annual detail are outside the default twenty-slot png. each field uses its own units, exposure and eligibility. missing fields receive an explanation and no numeric rank. [card and grouping contract](specs/v1-17-microstat-cards.md) · [field definitions](specs/experimental-card-facts.md#microstat-quantities-and-populations) · [evidence and resumption](issues/microstat-inputs.md#checked-evidence-and-bounded-follow-up)

#### complete-card acceptance and bounded exhaustiveness

the final matrix binds every slot to its contract, producer, publication, selected surface and retained evidence. it reconciles repeated values across the card, tables, history and export. actual profiles and same-kind comparisons cover ordinary and incomplete support, narrow layouts, native 200% zoom and downloaded files. the selected checks and missing dispositions are visible per row. [closure contract](specs/v1-20-whole-card-closure.md#five-card-capability-contract) · [real verification](research/application-v1-20/verification.md)

## v2 current-season views

2026–27 opens on recorded results in discovery and on the player profile by default. an explicit link to a modeled field opens that field with its availability. the first release has current facts alongside the three modeled seasons from 2023–24 through 2025–26. it can show a call-up from his first supported appearance.

| surface | what the reader gets |
|---|---|
| player and game log | for skaters, games, minutes, shots on goal, goals and supported personal and on-ice 5v5 rates with their own included time. for goalies, supported boxscore minutes, shots faced, saves and goals allowed with their stated strength and coverage. expected goals, goals saved above expected and modeled stopping require a numerical producer. |
| discovery, comparison and history | use the selected season's roster and peers. one player-season spans a trade and each game names the club actually represented. show qualifying peer count. a below-cutoff player keeps a supported magnitude and a reason for the missing percentile. retain the existing general and specialty minute rules on their declared populations. |
| page, csv and png | show “games through” with the cutoff. league coverage reports games supporting the measure out of verified completed games, with unresolved statuses separate. the card shows the player's supported games and minutes. disclose gaps in roster evidence at the level they can be assigned. show “not yet fitted” for an unfitted field. beside an estimate show “model fitted through” and use its fit snapshot for modeled peer standing. keep dates and coverage legible in the png. evidence and csv identify the publication, any fit, the source revisions and when game statuses were observed. |

reconcile a newly finished game's rows and the season totals on the card and export. check a debut, a traded player, an empty eligible cohort and a goalie with partial source coverage. dated historical estimates keep their original season and fit identity. [snapshot proof](issues/current-season-snapshot.md#two-cutoff-acceptance) · [cohort rules](specs/v1-14-history-cohorts-exports.md#cohort-calculation) · [goalie facts](../analysis/src/hockey_stats/descriptive.py#L263)

## v2 microstat page

on the player profile and on each side of a comparison, use the selected skater, season and publication for two additions outside the reference slots.

| group | what the reader gets | authoritative quantity |
|---|---|---|
| passing | an **inferred 5v5 setting** readout beside the passing fields. give the signed change in expected goals per 100 modeled setup opportunities versus a neutral setter on the same shot panel. show support, including prior-only status where applicable, or the reason a value is missing. | reuse `execution.5v5.setting_goals_per100_assisted_opportunities` from the analytical sheet. recorded primary goal assists and tracked primary shot assists each use their own covered minutes. [setting calculation](specs/v1-06-execution-scoring.md#common-panels-skills-and-support) |
| transition | a **modeled 5v5 zone movement** link to this skater’s entry offense, exit offense, zone retention and entry prevention. at the destination show focal and neutral one-second probabilities and supported time at risk in the relevant zone for each role. quiet seconds count toward avoiding an opponent exit or entry. | reuse the four territory projections and their evidence. the lineup model uses crossings inferred between recorded puck locations. a carry, pass or dump can connect the same locations. personally controlled crossings, retrievals and defended entry attempts require action credits. [movement evidence](specs/v1-11-territory-successor-value.md#movement-observations) · [role probabilities](specs/experimental-attribution.md#inferred-territory-and-post-shift-value) |

the page additions use existing analytical detail and exports. the reference png keeps its twenty slots per known position, and the microstat csv keeps its reference fields and six ledger rows. verify a forward, a defender, a mixed-position comparison and an unavailable setting value. magnitudes and support must agree with the analytical source for the same player and season. each missing tracking field keeps its reason and empty rank. [shipped export contract](specs/v1-17-microstat-cards.md#exports-and-operating-contract) · [real example](research/v1-review.md#what-the-microstat-gaps-mean)

## v2 goalie card

lead the profile, each side of a goalie comparison and its single-player png with two adjacent readings. place them consecutively at narrow widths.

| reader question | quantity and label |
|---|---|
| how would this goalie do on the same shots as a neutral goalie? | **modeled stopping** in goals prevented per 100 common on-net opportunities. show the selected model strength (even strength or penalty kill), support and any prior dependence. positive means fewer goals allowed. |
| how did the goalie fare on the shots actually faced? | **goals saved above expected** in total goals. show two labeled rows, on-net and unblocked including misses, each with its own eligible count, observed goals, neutral-goalie expected goals and difference. print the actual-evidence strength beside these rows. |

both rows use the existing paired evidence. the actual map opens on unblocked attempts with additive saving first. changing the map population leaves the two row identities intact. keep a missing value and its reason visible. use literal event names for the conditional subskills and label the modeled map as a distribution over shot origins. percentile standing describes the fitted estimates in the cohort. [numerical definitions](research/model-direction.md#reading-goalie-estimates) · [saros example](research/v1-review.md#one-goalie-three-questions)

first correct the csv population column. verify both toggle positions at the same strength, including a goalie whose two saving totals have opposite signs. the page, comparison, png and filtered csv should agree on the eligible counts, signs and corresponding values at their displayed precision. keep exact values in csv. [export reproducer and acceptance](issues/goalie-export-population.md)

## v2 reciprocal teammate view

**how did this team play with the two skaters together and with each apart, in games both dressed for the club?** open one pair from the teammate list, ordered by shared minutes. select one club and published regular season, through its stated cutoff for a season in progress. “both dressed” requires a dated roster or boxscore record that identifies that club unambiguously for each skater in the same game. interval membership supplies actual ice time. this selection excludes games with missing or conflicting affiliations, games apart after a trade and games on opposing sides. [dressed-game rule](../analysis/src/hockey_stats/descriptive.py#L159) · [deployment list](../app/src/web/deployment-tables.tsx#L64)

| measure | numerator and exposure |
|---|---|
| recorded attempts for and against · default | count goals, saved shots, misses and blocks from the club's perspective, each with weight one. use the retained genuine 5v5 time for `recorded_all_attempts`, including intervals with zero events. |
| reference expected goals for and against · experimental | sum the published fully neutral all-attempt values. use the retained seconds for `neutral_all_attempt_value`. label this option unavailable when the selected season lacks scored intervals. [value and support](specs/v1-06-execution-scoring.md#matched-values-and-publication) |

within those games, partition each measure's team intervals once. show **both**, **a only**, **b only**, using names on screen. retain **neither** for reconciliation. each rate is `3600 × summed count or expected goals / summed seconds`. positive time with zero events gives 0. zero time gives an unavailable rate. show together and apart even when one has few minutes. differences describe deployment, including the other skaters, opponents, shift starts and score. a causal chemistry or lineup recommendation would need additional evidence.

plot the three states on common for/against axes for the selected measure. label each axis and plot only states with a defined rate. the table keeps all three rows, with contributing games, minutes, for/against totals and both rates per 60. the page and csv show jointly dressed games, games with usable intervals and any unresolved coverage. the csv includes exact seconds and totals, rates, player/club/season identities, cutoff, population and publication. plot, table and export read one selected-pair result. [edmonton example](research/v1-review.md#one-pair-two-game-selections)

accept on a real pair and cases with a trade, a missing game or interval, zero-event time and no apart time. swapping players exchanges only the two exclusive rows. all four cells must sum to the club's eligible time and both totals on the same games for each measure. the existing exclusion totals cover whole player-seasons. assign excluded time to a row only when the game, interval and both players' membership are known. flag unassigned losses as unknown. measure one selected request and verify that simply opening the list issues zero pair requests. [context reader](../app/src/server/selected-publication.ts#L451)

## v2 many-player scatters

**which skaters reach a similar result in different ways, and which estimates deserve a closer look?** add two fixed presets to skater discovery. one point represents one skater's experimental level across one published regular season. use the three modeled seasons in v1. a season with only recorded results shows the modeled fields' availability. [worked examples](research/v1-review.md#what-two-axes-reveal)

| 5v5 preset | horizontal axis | vertical axis |
|---|---|---|
| chance creation and suppression · default | change in expected goals for per 60, `spatial.5v5.offense_xg_per60` | change in expected goals against per 60, `spatial.5v5.defense_xg_per60`. fewer against plots higher. keep the published sign in labels, table and csv. both axes use the same frozen virtual lineup. [spatial projection](specs/v1-08-positive-attribution.md#reference-and-exact-decomposition) |
| finishing and inferred setting | goals added per 100 modeled setup opportunities, `execution.5v5.setting_goals_per100_assisted_opportunities` | goals added per 100 physical attempts, `execution.5v5.finishing_goals_per100_attempts`. each replaces one neutral actor on the common panel. read them separately. combining these rates into a goal total would require an explicit workload for each role. [execution definitions](specs/v1-06-execution-scoring.md#common-panels-skills-and-support) |

show the model's zero lines. club and position filter the points while keeping coordinates and references fixed. a traded skater has one season-wide estimate under each listed club. check each axis's definition and reference across players within the publication and season. use one scatter minutes control, the existing general cutoff (`peerMin`, default 300). both values must be defined and each must meet the cutoff on its own positive qualifying seconds. spatial uses retained 5v5 time. execution uses each field's 5v5 participation for eligibility and its common-panel opportunities for the rate. the league table's separate minutes filter applies only to the league table. [cohort rules](specs/v1-14-history-cohorts-exports.md#cohort-calculation) · [existing table filters](../app/src/web/analysis-discovery.ts#L489)

keep zero, near-neutral and extreme points. label selected players, move overlapping labels and keep points at their exact coordinates. make every skater searchable. show listed, qualified and excluded counts with reasons. mark a searched below-cutoff skater with two values as outside the cohort. a missing coordinate stays empty with its reason and produces no point. open one skater's evidence or select two into the existing comparison at the same season. the cloud shows fitted differences. individual resolution requires separate evidence.

the plot, searchable table and csv share one selection. export the player, season, clubs, publication, preset, axis units and references, signed unrounded values, qualification seconds and eligibility/availability. flag any selected outsider separately. display and export prior-only status at its published scope. spatial shares one aggregate flag across roles and heads. execution supplies support for each field. [spatial support](specs/v1-08-positive-attribution.md#publication-and-content) · [execution support](specs/v1-06-execution-scoring.md#common-panels-skills-and-support)

reconcile both presets with the individual sheets, including opposite defensive signs, a trade, a missing coordinate, a cutoff that splits the presets and the inspected extreme. measure response size and time to a usable plot using the compact annual read. [acceptance cases](research/v1-review.md#what-two-axes-reveal) · [discovery cost](issues/profile-history-payload-cost.md)

## v2 annual peer context

**did the player's value move, did his standing among peers move, or did both move?** extend the existing skater profile history across the three published regular seasons, 2023–24 through 2025–26. keep the compact card's two percentile plots and open the richer reading in profile detail. start with two fields.

| selected field | value on the vertical axis | qualifying time for that season |
|---|---|---|
| `ledger.league_total` | experimental goals relative to the league reference over 1,000 5v5, 100 pp and 100 pk minutes. label model zero separately from the peer median. | included **on-ice** 5v5 minutes. actual specialty exposure and prior dependence remain visible in component evidence. |
| `sog60` | recorded personal 5v5 shots on goal per 60 **personal included minutes** | those same personal included minutes |

on one raw-unit scale per field, draw a player dot, a median tick and a bar spanning the 25th to 75th percentiles at each season. label the three marks. use that season's reported position group by default, with the existing all-skater option and adjustable 300-minute default. apply the field's eligibility and definition to the whole season roster. each qualified skater contributes once regardless of minutes or presence in another year. use exact values for midrank standing and the existing nearest-rank quartiles. the bar describes the spread among eligible peers. calibrated uncertainty about the player would need separate evidence. [cohort rules](specs/v1-14-history-cohorts-exports.md#cohort-calculation) · [existing quartile calculation](../app/src/web/analysis-cohorts.ts#L325)

label the dates covered, cohort size, qualifying minutes, age as of february 1 and every club represented that season. retain unknown ages. a trade gets one annual point. show a below-cutoff player's available magnitude beside the eligible peers and explain the withheld rank. an empty cohort has no quartiles. a missing annual identity or unknown position leaves the default position band unavailable. mark peer-group changes, gaps in player values and breaks in quantity definitions.

each season links to its evidence. chart, table, csv and png share the selection. csv retains unrounded values, quartiles, qualification seconds, peer settings and publication identity. [season identity](specs/v1-03-factual-card-reductions.md#identity-missing-fields-and-source-evidence) · [history and downloads](specs/v1-14-history-cohorts-exports.md#presentation-and-exports)

reconcile both fields against the checked matthews and carlo histories. exercise a trade, a below-cutoff value, a missing season and an empty cohort. measure the three-season read and time to a usable chart on the installed publication. the first view needs only these published scalars and the compact annual reader. [worked examples](research/v1-review.md#when-value-and-standing-diverge) · [read cost](issues/profile-history-payload-cost.md)

## visual coverage inventory — 2026-10-22

these twenty-one families describe the dated destination. a v1 receipt covers a specific card section and its shipped selectors. a later standalone view needs its own population, units, reference, interaction and evidence. the eight supplied images and public guides establish the compositions and record access limits. [reviewed images](research/visual-references/README.md) · [reference audit](research/player-card-references.md#visual-reference-sweep--2026-10-22) · [open visual contracts](issues/experimental-visual-coverage.md)

| id / family | quantity and reading | selected controls, output and ownership |
|---|---|---|
| v01 compact comparative skater | headline, component/context tiles, two annual histories, magnitude and percentile | card/cohort and ledger/history. select season, peers and reference. whole-card png and csv. |
| v02 analytical skater | four full-rink maps with matching xg insets, shootiness, distributions and component ledger | spatial/execution/value producers and sheet/rink. inspect state, reference and metric detail. whole-card and plot exports. |
| v03 descriptive skater | scoring/workload bars, appearances, recorded context | facts and descriptive card. season, strength, card png and game/table csv. |
| v04 on/off results | for/against rates, shares and included time for focal-on, dressed-game off and league populations | interval facts and descriptive sheet. attempts and goals under matched exposure. expanded reciprocal views require v10. |
| v05 deployment | shift starts, score state, usage and counterpart role groups | prepared intervals and context. season, strength, reference, plot/table exports. broader combinations require their own groups. |
| v06 spatial detail | observed on-ice and experimental full-rink maps with physical area, units, reference and inset | facts/spatial projection and rink. strength, quantity, display reference and map export. color thresholds use the selected scale. |
| v07 personal shots | recorded personal locations and shot mix, including a separate block-contact layer | factual evidence and personal-location view. season/outcome/type filters and point counts with coverage. [geography contract](specs/05i-personal-shot-views.md) |
| v08 finishing/setting | standardized levels, component maps, histories and outcomes by type/danger alongside reference- and actor-conditioned expectations | execution and detail. fixed strata select actual evidence. season/strength and plot/data exports share the projection. [execution evidence](research/execution-v1-06/verification.md) |
| v09 penalties/territory | drawn/taken effects and recorded infractions, four transition subskills and ice won/lost maps/value | mechanism producers and detail. metric/reference, export and sampled evidence disclose event support, zone proxy and units. |
| v10 reciprocal with/without | together and each playing without the other in games both dressed for one club | selected pair first. the context reader supplies recorded attempts and supported reference xg to the plot, table and csv. later maps need their own matched locatable-unblocked population. [reader contract](#v2-reciprocal-teammate-view) |
| v11 adjustment explanation | experimental baseline, self and context terms for the selected actual lineup | attribution projection and detail. actual-context terms remain diagnostic where counterfactuals extrapolate. broader context explorer needs support/magnitude explanations. [documented extremes](issues/spatial-actual-context-extremes.md) |
| v12 replacement | value relative to the position-specific roster-depth group | ledger and comparison. membership, workload and exclusions support the shipped scalar. later replacement views need a defined quantity/map and pinned example. |
| v13 teammate-combination spider | each point represents an overlapping lineup subset. edges join subsets that differ by one required skater. hockeyviz examples use either adjusted attempts or xg per 60, with the against axis inverted. | later. interval facts and comparison. specify the measure, membership, shared exposure, adjustment, display cutoff and exported values. [dated chart evidence](research/player-card-references.md#reciprocal-and-combination-charts) |
| v14 goalie sheet | stopping, saving, matched on-net/unblocked evidence, six conditional skills, type/danger, workload and stopping history | goalie producers, full sheet and detail. select population, ev/pk, peers and stratum. card/map/plot png and csv. private overall-value formula unknown. |
| v15 goalie start patterns | start-quality categories, consistency and proposed overall-value displays | later. goalie evidence and details. define thresholds, eligible games/seasons, temporal target, reference and export. [peer preview](https://hockeystats.com/cards/goalie-cards) |
| v16 history | v1 shows three seasons of magnitudes and peer standing. v2 adds annual quartiles, age, clubs and qualifying minutes for skater value and recorded shooting. | profile history and cohorts own the chart, table and exports. longer coverage and a smoothed game log have separate evidence needs. [annual peer context](#v2-annual-peer-context) · [historical depth](issues/experimental-visual-coverage.md#earlier-season-coverage) |
| v17 discovery/tables | sortable and searchable value, component and recorded-stat tables | publication and explorer. player kind, season, family and peers. csv follows selection. extended peer table controls require their own evidence. |
| v18 comparison and distributions | raw-unit peer populations, selected player markers and two like-kind players | cohort/comparison. preserve distinct positional cohorts, signs, sorting and references in plots and exports. |
| v19 appearances and games | actual workload, inclusion and observations by game | observed facts, goalie evidence and profile. season selection and game rows. counts and exposure reconcile to season facts. |
| v20 many-player scatters | 5v5 xg creation and suppression, finishing and inferred setting, each on its own published scale | selected for v2 discovery. two presets share the compact annual reader, filters, searchable table, csv and player navigation. [reader contract](#v2-many-player-scatters) · [peer examples](research/player-card-references.md#many-player-scatterplots) |
| v21 grouped microstats | four groups spanning shooting, passing, transition and other actions, with raw values, standings and explicit source gaps | factual/execution/skating source owners and card. profiles, comparisons, field-level histories, png and csv. [microstat evidence](issues/microstat-inputs.md) |

## cards and supporting views

the ledger assigns goals to 5v5 offense and defense, pp offense, pk defense, finishing, setting, penalties drawn and taken, and ice won and lost. the first four describe chance creation/suppression at their assigned strengths. special teams combine 5v4, 5v3 and 4v3 pp and reciprocal pk using declared league-time weights. shootiness describes who takes the shot. modeled penalties concern the on-ice team's award risk. zone transitions explain successor value. subskills stay in detail so the same goals enter a total once. [component contracts](specs/experimental-attribution.md) · [special teams](specs/v1-09-special-teams.md) · [ledger and depth reference](specs/v1-12-value-ledger.md)

the delivered headline estimates underlying level across a season on common minutes, with actual results separately available. v2 adds a historical ability view. select a date on the player's curve and read the estimate, how much evidence supports it and how far beyond that date the fit could see. comparisons use a shared target date, evidence cutoff and reference. the dated skill and season summary keep distinct labels on the card and downloads. [ability contract](research/model-direction.md#retrospective-player-ability)

hockeyviz describes isolated impact at an instant. jfresh's comparative skater card leads with projected war and includes projected scoring rates. our comparative card shows seasonal goal impact at common minutes, its positional standing and recorded scoring rates. where a power-play or penalty-kill term drives the result, show the player's included minutes in that role and any documented prior-only status. [historical re-estimation](research/player-card-references.md#historical-ability-estimates) · [comparative card definitions](https://hockeystats.com/about/player-cards) · [comparison protocol](research/model-direction.md#comparing-skater-rankings)

goalie evidence maps and type/danger panels compare actual goals conceded with expected goals over matched opportunities. standardized stopping uses the model reference. the six conditional subskills include recorded continuation and danger proxies. the public sources do not establish the current private overall goalie formula. event-based territory and setting likewise answer different questions from tracked entries/exits or shot assists. [goalie definitions](specs/experimental-chance.md#goalie-card-evidence-and-conditional-summaries) · [later card definitions](issues/card-reference-definitions.md)

the screen, comparison and export must preserve raw magnitude, cohort definition, units, signs and material limits for the selected season. each year in a recorded history needs admitted observations. a modeled history also needs the fitted result and its cutoff for that year. broader recorded game states and playoffs require their own exposure and source contracts. retrospective season-level models, career records and future forecasts have different targets. [history and cohort contract](specs/v1-14-history-cohorts-exports.md)

the [open source issue](issues/microstat-inputs.md) distinguishes missing tracking, inaccessible provider measurements and deferred public skating work. broader paid enrichment, standalone team/coach evaluations, contracts/cap, prospects, fantasy, simulators and game forecasts have their own product decisions. the [roadmap](roadmap.md) describes v2 tracks and the [plan](plan.md) owns sequencing.
