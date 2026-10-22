# v1-01 — shared card and model evidence

full implementation handoff, 2026-10-22. [the plan](../plan.md) owns assignment; this document assigns no execution. read the [program](experimental-player-analysis.md), [card facts](experimental-card-facts.md), [execution](experimental-chance.md) and [elapsed-model contract](experimental-attribution.md#elapsed-design). this slice prepares their shared evidence; it does not compute the cards or fit their models.

## outcome and boundary

one offline command turns explicitly selected native corpora into reusable, identified game facts: every recorded event, actual all-strength skater/goalie membership, zero-event elapsed time, chronology, identity, source credits, immediate outcome labels and pre-event/elapsed context. subsequent consumers select their own populations without reparsing sources or substituting observations for unknowns. the existing observed 5v5 results remain exact.

real acceptance covers the admitted five regular seasons, `20212022..20252026`, 6,560 inventory games. detached fixture development is sufficient to implement the interface, not to claim that acceptance. use the exact corpus paths/hashes in the [03n input table](../research/chance-03n/protocol.md); 02d corrected support policy, not those captured originals. no new acquisition, corpus recovery, native schema revision, model design matrix, fit, xg/origin inference, territory inference, factual season-rate reduction, sqlite/application change or activation. coaches are a separate v1-02 input; tracking/skating and later encoder alternatives remain their assigned boundaries.

accepted costs: wider prepared facts and a complete five-season verification pass; conservative loss of elapsed support where source lineups conflict; piecewise-constant elapsed workload; explicit unknown identity/history. these buy consistent consumers without claiming more complete hockey observations. unknown height units withhold optional normalized height, not other identity fields. no model-quality gate applies.

## owners and composition

| owner / files under `analysis/src/hockey_stats/` | owned change and boundary |
|---|---|
| `reconstruct.py` | shared maximal membership segments and event/segment conflict evidence; native report matching, horizons and interval links remain authoritative |
| `game_chronology.py` | single verified event order/score authority; expose elapsed score changes without another goal accumulator |
| `feature_data.py`, `feature_history.py` | event/elapsed facts, coalesced player participation, live starts, actual-unit summaries, prefix/history and immediate outcome evidence |
| `chance_data.py`, `scoring_credits.py`, `references.py` | extract reusable factual operations where needed; preserve existing research eligibility and source-bound credit/identity meanings |
| new `analysis_data.py` | typed product selection/records, composition, finite artifact reader/writer and game-at-a-time preparation; no raw parser or fitted calculation |
| new `analysis_cli.py`; `analysis/pyproject.toml` | `hockey-stats-analysis prepare` only; thin argument handling and entry point |
| implementation receipt/content owner | `docs/research/evidence-v1-01/verification.md`, compact coverage receipts and fixture expectations; truthful support vocabulary |

reuse `corpus_inputs`, `captures` and low-level `artifacts` helpers for native validation, hashes, implementation identity and exclusive finite JSON. existing research artifact envelopes are not the new product schema. `corpus_inputs.object_fields` permits extra keys: new product readers must explicitly reject them. keep ordinary functions/typed records; no feature registry, service, runner, checkpoint system or generic ingestion framework.

existing reconstruction already retains other strengths. add a common `membership_segments(intervals)` coalescer and make `five_on_five_segments` its exact filtered projection. lift shared factual operations at their current owner; do not copy the whole research preparer and remove its 5v5 checks. old research APIs and observed populations are still distinct supported consumers, not compatibility fallbacks. new product readers accept only this contract.

```text
prepare_analysis(selection_path, output) -> manifest
prepare_game(envelope, inventory_entry, references, input_ref) -> game_facts
read_prepared(path, expected_purpose) -> validated_manifest
read_prepared_game(manifest, season, game_id) -> game_facts
read_prepared_people(manifest, season) -> season_people
read_prepared_coverage(manifest) -> coverage
```

these functions compose existing owners. history joins occur after their compact prerequisites are available. v1-02 supplies a separately bound coach selection to later family fits; it neither blocks this preparation nor causes a base-evidence rebuild.

## selection, artifacts and operation

```text
hockey-stats-analysis prepare --selection FILE --out DIR

selection = {
  schema_version: 1,
  purpose: "real" | "fixture",
  seasons: [{season, corpus_manifest, sha256, game_ids}]
}
```

all keys required; reject unknown keys, duplicate flags/years/games, invalid types and mismatched season/receipt/hash identities. season/game ids use the native eight-/ten-digit strings; player/team ids and source indexes retain native integer types. paths are explicit and resolved relative to the selection file; output is a new directory outside inputs. `real` requires the five ordered seasons and `game_ids:null` (all inventory games). `fixture` allows an ordered subset of these seasons with explicit nonempty inventory game-id lists. full inventories still supply schedule context; never open omitted game envelopes or count their missing summaries as failed captures. fixture purpose cannot be relabeled real. no newest-file discovery or hdd/local fallback. real output uses ordinary external files; fixtures may be local. no five-season local mirror.

process selected games in source game-date/id order. retain only compact per-game/person history summaries across games; reread selected envelopes for final game facts if needed. later records may supply descriptive season identity, never an earlier game's predictor prefix. history uses strictly earlier dates under the existing rule; first selected game is not necessarily first career appearance. expose incomplete lookbacks rather than zero-filling omitted games. parameterize the existing history source locator instead of fabricating `/history_corpora` in this selection.

copy exact selection bytes to `selection.json`; write `games/<season>/<game_id>.json`, `people/<season>.json`, `coverage.json`, then `manifest.json` last. every selected inventory game gets a record, including unavailable source cases. a missing/corrupt promised file or invalid schema is an error; an admitted ledger/source's explicit missing/empty/failed/unresolved disposition is data. output has no completion manifest after failure; correct the cause and use a fresh directory. no resume state machine. reuse exclusive writers and `allow_nan=False`; no pickle or corpus-sized event/cell arrays.

the exact manifest keys are `schema_version:1`, `kind:"prepared-analysis"`, `purpose`, `preparation_id:"experimental-evidence-v1"`, `implementation`, `selection:{path:"selection.json",sha256}`, `inputs`, `seasons`, `files`, `resources`. `inputs` binds consumed corpus/envelope/reference/source identities using existing input-reference records, with their original resolved paths. `seasons` lists `{season,inventory_games,selected_game_ids}`. `files` contains `{kind:"game"|"people"|"coverage",season,game_id,path,sha256}`; inapplicable ids are null. require exactly one game member per selected key, one people member per selected season and one coverage member; unique contained relative member paths and matching internal schema/year/game ids. reject extra, missing and cross-wired members.

`resources` is `{wall_seconds,peak_memory_bytes,output_bytes}` with nonnegative finite values; bytes exclude the final manifest. prepared readers check exact keys, identities and finite values, loading/hashing members as consumed. they do not reopen original corpora/captures; preparation validates those inputs, whose identities remain provenance. source verification can be repeated explicitly during acceptance. implementation records distinguish source code, preparation policy and inputs; hash identity is not scientific support.

game files have exactly `schema_version,season,game_id,game,events,associations,segments,chunks,player_shifts,episodes,people,attempts,credits,ordinary_attempt_support,issues`. season person files contain `schema_version,season,people`. use the typed fields below and existing `{values,problems,evidence}` convention for nullable facts. evidence includes immutable input identity and source pointer. nulls require located missing/conflict/not-applicable reasons; partial known sums retain completeness separately. raw source fields stay source fields. no universal `eligible` boolean or free-form metric bag.

## record contract

| record | required contents and meaning |
|---|---|
| `game` | inventory date/teams/type; source and collection dispositions; supported period horizons; order, score and frame validity separately; actual terminal evidence. no fabricated five-minute overtime or timed shootout |
| `events` | one row per original interpreted `Event`, keyed by `(season,game_id,source_index)`; retain every existing event field, original id/order, kind validity, roles, penalty fields and source observations. add verified order/predecessor/successor links, pre-score, report membership, normalized frame/location with meaning, episode/reset links and exact pre-event context. invalid/unrecognized rows remain evidence and cannot be skipped to manufacture continuity |
| `associations` | per event: native `interval_indices`, `shift_relation`, report match, touching/matching segment ids, boundary/interior position and conflict reasons. preserve unsupported/unmatched report attempts as located issues with touching spans, not invented api events |
| `segments` | maximal positive half-open same-period runs with identical full membership and consecutive native indices; `segment_index,native_interval_indices,period,start_seconds,end_seconds`, four skater/goalie lists, exact state, source status and located attempt-support conflicts. unknown native spans remain identified gaps |
| `chunks` | disjoint children of supported segments: `chunk_index,segment_index,period,start_seconds,end_seconds`, elapsed score, per-member shift/context links, unit context and applicability. retain unsupported context as nulls/reasons; membership and time do not disappear because a predictor is missing |
| `player_shifts` | player/team/period, coalesced participation start/end, original shift/interval links, membership continuity, start kind and own-team zone, elapsed age, rest and source reasons. both skaters and goalies; no team-average invented shift |
| `episodes` | anchored recorded live spans: index, period, start/end clocks and source indexes, `faceoff` or `first_live_action` start, left-censored start flag and reset/terminal/unknown end reason. a left-censored episode cannot establish the complete earlier participant universe for setting |
| game `people` | dated roster/boxscore identity and affiliation, sweater/position/role observations, bio references, separately named reported totals, prefix/history facts and coverage. source totals are not reconstructed minutes |
| `attempts` | one link per recognized attempt event; outcome/type/modifier, credited versus physical shooter, shooting side/opposing goalie, ordinary-play disposition, reported/normalized location meaning, factual feature groups, immediate-stop and reattempt evidence. keep block contacts as contacts and unavailable physical action separate from recorded goal credit |
| `credits` | event link, scorer/shooter, primary assister, raw-bound credit status/reasons; preserve secondary evidence without inventing a new points metric. no duplicate assist parser or on-ice requirement for a legitimate off-ice assister |
| season `people` | person id/name, dated team/position/sweater observations, resolved F/D/G group or conflict, birth/hand evidence, february-1 reference date and integer age-days. preserve uncertain chronology; the numerical encoder later converts age to years |

indexes are local to the bound input/preparation, not stable across recaptures. nullable/duplicated event ids are evidence, not primary keys. store home/away membership once; consumer team-relative views invert deliberately. known goalie absence is `[]`; unknown is null. exact states retain all four list sizes. with both goalies, descriptive ev is 5v5/4v4/3v3, pp is 5v4/5v3/4v3 and pk reciprocal; extra-attacker/other supported states remain `other`, unknown stays unknown. attribution's narrower groups remain downstream selections.

penalty/territory source rows are typed views of `events`, not duplicated ledgers. qualification of ordinary-minor awards, inferred zone movement, setter candidates/weights, origins, neutral probabilities and card-rate denominators belong to their later producers. source roles, dated teams and membership are prepared here; v1-03 owns additional hitter/blocker attribution checks and the affected family's masks. reported all-strength totals never fill an unknown reconstructed denominator.

### closed record shapes

implement explicit product typed records and validators. `Event,Game,Input,Result,Check,ReportRow,RosterRecord,BoxscorePlayer,SourceObservation,ScoreCounts,Issue` reuse `interpret.py`; `InventoryGame` reuses `references.py`; `Period,Interval,Membership,ReconstructedEvent` reuse `reconstruct.py`. `Fact<T>` is the existing located `{values:T,problems,evidence}` convention with a fixed named `T`; its evidence is `feature_data`'s input/source/pointer reference. reuse the exact retained field sets/units in the [03k ledger](../research/features-03k/ledger.md#exact-shared-fields-and-history-windows); there are no existing feature TypedDict validators to assume. add the explicit new shapes below; `?` means nullable, every displayed key is required. scalar values inside `Fact` may be null with a field problem; absence is not an omitted key.

```text
game = {inventory: InventoryGame, ledger: {status,reason},
        identity: Game?, inputs: Input[], reported_results: Result[],
        checks: Check[], periods: Period[]?, native_intervals: Interval[]?,
        report_rows: ReportRow[]?, recording_observations: SourceObservation[],
        source_issues: Issue[], native_issues: Issue[]}
event = {source: Event, pre_score: Fact<ScoreCounts>,
         geometry: Fact<{x_ft,y_ft,frame,location_kind}>,
         chronology: Fact<{order_index,predecessor_source_index,
           successor_source_index,episode_index,reset_source_index}>,
         context: EventContext}
association = {source_index, native: ReconstructedEvent?,
               touching_segment_indices, matching_segment_indices,
               temporal_case: interior|boundary|unavailable, issue_indices}
segment = {segment_index,native_interval_indices,period_number,
           start_seconds,end_seconds,membership: Membership,issue_indices}
chunk = {chunk_index,segment_index,start_seconds,end_seconds,
         score: Fact<ScoreCounts>, strength_transition: TransitionFacts,
         member_contexts: [{player_id,
           player_shift_index,shift_age_seconds: Fact<{value}>,
           elapsed_prefix: PrefixFacts}], away_unit: UnitFacts,
         home_unit: UnitFacts,issue_indices}
player_shift = {player_shift_index,player_id,team_id,period_number,
                start_seconds,end_seconds,native_shift_indices,
                native_interval_indices,start: Fact<{kind,zone,
                  event_source_index,episode_index,rest_seconds}>,issue_indices}
episode = {episode_index,period_number,start_seconds,end_seconds?,
           start_source_index,end_source_index?,
           start_kind: faceoff|first_live_action,left_censored: bool,
           end_reason: reset|faceoff|terminal|unknown,issue_indices}
attempt = {source_index,details: Fact<{outcome,physical_status,
             credited_shooter_id,physical_shooter_id,shooting_team_id,
             opposing_goalie_id,location_kind}>,
           feature_facts: RetainedAttemptFacts,immediate_outcomes: Fact<{
             recorded_goalie_stop,reattempt_within_5s,reattempt_source_index,
             next_event_source_index,next_event_delay_seconds}>}
```

all indexes/counters are nonnegative integers; ids retain native types, seconds are finite nonnegative numbers, score counts are nonnegative integers. nullable context fields have explicit problems. `start.kind=faceoff|on_the_fly|unknown`, `zone=offensive|neutral|defensive|null`; unknown start has an issue. `outcome=block|miss|save|goal|null`, `physical_status=ordinary|outside_population|unresolved`, `location_kind=reported_attempt|block_contact|unavailable`. links must target their named collection and agree with the event/game. collection null means unavailable with a located issue; `[]` means a checked empty collection. event availability cannot depend on interval availability.

`RetainedAttemptFacts` has exactly `geometry,state,preceding,sequence,deployment,current_workload,outcome`, with existing named constructor shapes except these unit replacements. `EventContext={prefix_by_player,live_episode_index,strength_transition:TransitionFacts}` gives source-supported participants' prefixes, never invented membership. `PrefixFacts` preserves existing fields/known sums and adds `on_net_faced,known_on_net_faced`, not applicable to skaters. `UnitFacts=Fact<{member_count,known_count,known_toi_all_sum_seconds,toi_all_mean_seconds,toi_all_max_seconds}>` describes skaters. product `current_workload=Fact<{players,opposing_unit}>` uses it; member links also live in `chunk.member_contexts`. product deployment replaces `attacking_five/opposing_five` with `attacking_unit/opposing_unit`, each `Fact<{member_count,known_count,known_age_sum_seconds,age_min_seconds,age_mean_seconds,age_max_seconds}>`. complete aggregates require all actual members known. known unit sums/counts include only members with a complete field value; individual partial lower bounds remain in their member facts. preserve the old five-member fields/behavior only in research projections. no new coalesced shift-count predictor.

`TransitionFacts=Fact<{exists,prior_shorthanded_side,return_seconds,age_seconds}>`, with boolean `exists`, side `home|away|null`, and period-local return clock. reuse the existing unequal-strength→5v5 transition and its reset/applicability rule, evaluated at each chunk-left boundary and exact event position. do not infer penalty expiry; do not build elapsed transition facts from occasional attempt snapshots. elapsed resets at a clock apply to following elapsed play; source-ordered event snapshots retain the pre-event rule.

event geometry uses the existing coordinate/frame owner for every located event, not only attempts: finite feet in the `home_attack` frame, with `location_kind=reported_event|block_contact|unavailable`. other team frames are exact rotations, not new source observations. unresolved frame or out-of-rink evidence stays unavailable with original coordinates preserved in `Event`; block contacts never become releases. this supplies faceoff/hit/turnover anchors for later consumers without a second location calculator.

game `people` maps decimal player ids to the existing `player_game_facts` shape plus `roster: RosterRecord[]`, `boxscore: BoxscorePlayer[]` and dated sweater evidence; retained history/rest shapes follow their named ledger contracts. season `people` is an array of `Fact<{player_id,name,team_ids,reported_positions,position_group,sweaters,birth_date,shoots_catches,age_reference_date,age_days,height_cm}>`; teams/positions are unique sorted source values, sweaters retain `{team_id,game_id,number}` observations, dates are iso dates, group is `F|D|G|null`. field provenance supplies dates/source identity. credits retain the exact `scoring_credits` result fields keyed by source index, without post-hoc stronger eligibility; absent collections remain null. game `issues` uses located `Issue` plus evidence references, separate from retained native issue indexes.

`ordinary_attempt_support` has exactly `segments,events,report_only,reasons`. segment rows are `{segment_index,disposition:included|excluded,reason_indices}`; event rows `{source_index,disposition:included|excluded|not_applicable|unresolved,segment_index?,chunk_index?,reason_indices}`; report-only rows `{report_source_index,affected_segment_indices,reason_indices}`. require one row per prepared segment/source event, and one per unlinked potential report attempt. these collections follow their respective source availability, not a universal null. reasons are `{code,scope:segment|period|game,period_number?,event_source_indices,report_source_indices,affected_segment_indices,evidence}`. codes are `source_unavailable,count_accounting_conflict,membership_unavailable,identity_conflict,strength_conflict,ambiguous_assignment,event_evidence_unresolved,unmatched_report_attempt,clock_unavailable,horizon_unavailable`. included events require exactly one included segment and child; excluded events retain any known assignment. exclusion is the union of saved reasons, checked against the source/chunk links.

`coverage.json` has `{schema_version:1,seasons:[...]}`. each season contains `season,inventory_games,selected_games,game_status_counts,game_sources,events,report_only_attempts,time,unknown_horizon_games,unresolved_known_seconds,completeness`. status counts use the native `CorpusGame` enum; source rows are `{source,available_games,unavailable_games}`. event rows are `{kind,outcome,count}`, retaining unknown kinds separately. time rows are `{away_skaters,home_skaters,away_goalies,home_goalies,physical_seconds,included_seconds,excluded_seconds,team_seconds,skater_slot_seconds,goalie_slot_seconds}` on resolved membership, using the saved base mask; unknown horizons do not become zero missing time. `completeness` has `order,score,frame,identity,history,event_context,elapsed_context,immediate_stop,reattempt`, each `{available,partial,unavailable,not_applicable}`: game denominator for order/score/frame, season-person for identity, person-game for history, event for event context, chunk for elapsed context, attempt for labels. available means all applicable fields supported, partial some, unavailable none, not-applicable no applicable fields. retain per-reason masks for interpreting these summaries.

## support and chronology invariants

**event evidence and elapsed support are independent.** valid report-supported attempts in an empty-shift game remain available to event-based execution, with unknown shift context. they cannot establish a rate denominator. new rate consumers use the matched links/masks below; existing observed on-ice/personal/spatial/deployment results continue through their current authoritative owners, unchanged.

1. coalesce native runs before locating exclusions; a redundant native split cannot shorten a contradiction. goalie changes break a full-membership run. retain actual overtime horizons, unresolved intervals and otherwise valid zero-event time.
2. honor native event links and `before|after|both|neither|unavailable`. at an endpoint, a unique native-supported matching run assigns the event; `both` within one maximal run is one assignment. do not infer support from one matching side when another required adjacent interval is unknown. at internal chunk boundaries choose the following child in the assigned run, or its final child if the event is at the run's end.
3. shared new ordinary-attempt rate support excludes a whole maximal run when a corroborated recorded ordinary-play attempt contradicts its full membership strictly inside it. here corroborated means a valid timed `goal|shot-on-goal|missed-shot|blocked-shot`, unique matched report with `penalty_shot:false`, no supported landing penalty-shot, and valid full reported membership. physical-shooter, location/type and assist failures do not suppress contradiction evidence; own/awarded goal observations remain source evidence. retain strength-versus-identity conflict reasons. a boundary attempt with no unique match affects touching runs of its exact state; other-state neighbors remain diagnostics. unknown state affects all touching applicable runs; missing timing widens only to the identified period/game. union overlapping masks once; remove counts and time together. never fabricate replacement lineups.
4. this new all-strength support does not rewrite 02d. preserve the exact `outside_attempt_conflicts` predicate and old observed masking. malformed credit, location or physical-action evidence must not erase unrelated observations. preserve event-supported records even when their rate support is excluded; expose each restriction and its owner.
5. source kind/order/clock uncertainty breaks affected event chains. all recorded events remain; no event-id sorting or silent skipping to the next convenient live action. use the existing verified source ordering and all-strength timed-goal corroboration, excluding shootout decisions from elapsed score.
6. split chunks at membership/strength, score changes, supported resets, regulation ten-minute boundaries and every present member's shift-age boundaries `0,10,20,40,60,90` seconds. preserve genuine overtime and its separate context. chunks partition their parent's physical time exactly; no one-second expansion.
7. events retain the authoritative pre-event score; elapsed time after a goal uses the updated score. a valid incoming-lineup goal may use that lineup and pre-goal score even when no positive-time chunk has both. do not import the old research score-context exclusion into this product. this is the event/elapsed exception already specified by the positive likelihood, not a repair to frozen studies.

the fixed new rate-support failure matrix completes rule 3. absent required event/report collections or a native timed-goal/shot accounting `mismatch` exclude all reconstructed segments for this matched rate; missing accounting corroboration remains separately visible, not automatically a contradiction. unresolved potential attempts without a valid assignment mask touching relevant runs, or the identified period/game if unlocatable. unmatched report attempts use checked roster-resolved full membership if independently available, otherwise unknown state; raw `EV/PP` text never supplies that state. missing segment-member identity masks that segment. known penalty shots/untimed shootout events are outside this population. stored masks include excluded counts and time, while underlying native segments and usable event evidence survive. v1-03/08 read these decisions and add only their own field restrictions; they do not reconstruct the same masks independently.

## context and labels

reuse the existing reviewed feature families and their evidence. current five-player-only unit means become shared actual-unit calculations: complete means divide by the actual supported member count; partial sums/counts stay separately named. preserve existing research projections exactly. no feature is activated, centered, standardized or ablated here.

coalesce contiguous participation for the individual before classifying starts; a teammate change or stoppage alone does not start a new shift. a corroborated faceoff gives its supported membership and own-team zone. otherwise prove a start strictly inside known live play for `on_the_fly`; a tied clock without that evidence stays unknown. an episode starts at a corroborated faceoff or conservatively at a supported timed ordinary save/miss/block, hit, giveaway or takeaway. `feature_data.RESETS` supplies the fixed reset set: goal, stoppage, penalty, period-start, period-end, game-end, shootout-complete; a new faceoff also closes/restarts an episode. delayed penalties/failed attempts are retained but not new live anchors. first-action starts are left-censored; unknown order/kind/timing ends continuity. later anchors can start another censored span. no invented maximum gap between recorded actions.

retain two workload snapshots. event prefixes include only verified earlier records, including earlier same-clock records, excluding the focal event. elapsed prefixes integrate participation over preceding half-open time and count events strictly before the chunk-left clock, excluding all same-clock events; hold them constant for that chunk. future spatial events use that chunk context with the declared pre-score/membership exceptions. execution uses its exact event prefix. this intentionally coarse elapsed approximation prevents same-clock leakage without adding a cut per shot.

retain the existing native-row `shifts_begun/completed` basis; coalesced participation does not silently change those counters. new coalesced counts, if consumed, have separately named fields. at an elapsed boundary, native starts/ends at that clock belong to following elapsed play. event-time tied endpoints follow the existing supported before/after membership rule; ambiguous endpoints remain unknown. elapsed shift age/start refers to the coalesced participation span.

add `on_net_faced` to the goalie prefix owner: all timed source-supported on-net actions faced by the identified goalie, including penalty shots, excluding shootouts/known empty nets. ordinary physical and penalty-shot goals count; unresolved physical-action/goalie identity leaves the affected total incomplete with its known sum. no coordinate/type/execution-eligibility restriction. this event-prefix basis is separately identified from prior-game boxscore `shotsAgainst`; never use the current game's final total as a predictor. retain current player attempt/goal/shift/time prefixes, previous-night/second-previous-night participation, preceding 7/14-day counters and earlier-season facts under existing applicability rules. only prior dates enter game history; same-date summaries remain excluded. a strength change is not proof of penalty expiry. retain unused families without expanding the recipe.

`immediate_outcomes` is a separately named fact group, not a redefinition of the old longer-span `_outcomes` fields:

- `recorded_goalie_stop: bool|null`: after a supported saved shot, the immediately next recorded event must be a supported stoppage with reason `goalie-stopped-after-sog` and delay `0..2` seconds. another supported next event or a validated terminal gives false; an ordinary goal gives false; non-on-net is not applicable. unknown ordering/timing remains unknown; do not skip an intervening row.
- `reattempt_within_5s: bool|null`, `reattempt_source_index`, next-event index/delay and evidence: after a supported save, the immediately next recorded event is an ordinary same-team attempt within `0..5` seconds in the same period, before any reset. supported nonqualifying next events/terminals give false; unproved terminal/order/team/physical-action evidence gives unknown. occurrence does not require the next attempt's geometry or eventual neutral value. v1-07 owns the danger target; v1-05 maps these factual labels into its outcome heads.

require only facts necessary to decide each label: a known non-attempt next row needs no team/geometry to establish a negative reattempt label. false links are null/not-applicable; undecidable links are null/unavailable. no requirement for future membership or shot type unless necessary to establish that action's physical/team disposition. these future labels never enter predictor records.

use dated roster/boxscore teams, not present-day bio affiliation. season display name is the latest supported dated game identity under the existing observed name resolution; it is descriptive, never a historical predictor. map `C/L/R/F→F`, `D→D`, `G→G`; conflicting supported groups yield null with observations retained. birth/hand conflicts yield null; missing bio `effective_at` cannot become known-as-of evidence. retrospective hand retains its assumption. expose optional `height_cm` only with verified units; retain raw height and the [unit limitation](../issues/bio-height-units.md). age-days needs birth date, not resolved role; the later age-curve transition requires both and otherwise uses its explicit age-neutral rule.

## acceptance, content and handoffs

the evidence content reviewer defines a useful receipt: what was selected, what each source supports, what remains unknown, how much time each restriction removes and which consumers may use it. `coverage.json` and the verification document report per-season inventory/selected/source-available games; events by source kind/outcome; report-only records; exact-state physical seconds; directed team-seconds; player/goalie slot-seconds; conflicts/exclusions/unknown spans; context/label/identity completeness. source availability, matched elapsed support and model applicability are separate columns. never call reconstruction ground truth or the new records calibrated ability. no card/UI design is implemented here.

| boundary / independent review | required evidence before completion |
|---|---|
| input and artifact | temporary end-to-end red→green→refactor→green from an explicit fixture selection through `prepare` and the public reader; reject malformed/extra fields, hash/identity mismatch, duplicate selection and occupied output. incomplete output is unreadable; explicit source gaps survive. no network/fitting/publication import side effects |
| source association | independently inspect existing fixtures for exact strength/goalies, endpoints, unknown adjacent shifts, shortened overtime, report-only/unmatched events and overlapping masks. verify source rows are neither dropped nor multiplied; count/time exclusions have witnesses |
| context/identity | check source-ordered same-clock prefixes, score before/after a goal, zero-event chunk partition, coalesced starts, actual-unit means, goalie prefixes, terminal/reattempt labels, dated trade/sweater/bio observations and missing history. change later values/labels while preserving chronology/accounting validation premises: earlier predictor facts remain identical; corrupting whole-game source validation may legitimately withhold them |
| preserved consumers | before/after comparison on all three displayed seasons through existing observed reducers: exact hockey facts, supported/excluded time, counts, personal/spatial/deployment values and reasons. existing feature/research fixture projections remain exact; implementation hashes/receipts need not match. no application rebuild or historical fitting required |
| real handoff | prepare all 6,560 selected inventory games, validate every partition and reconcile coverage. independently recalculate representative facts against originals. account for every selected game and original event; measure time/peak memory/output bytes. unavailable games remain unavailable, not silently omitted |
| downstream readiness | a small reader exercise selects execution event facts, all-strength descriptive facts and elapsed-model chunks without parsing sources or fitting. a complete-row mock may prove schemas; actual selected facts prove this producer's delivery |

use existing cases, especially `2025020001/0006` (empty nets/strengths/boundaries), `2025021094` (penalty shot/short overtime), `2024021235` (event evidence without shifts), `2022020822` (incoming goal/pre-score) and `2024020186` (interior conflict). use compact labeled synthetic cases for missing boundary combinations, actual 3/4/5/6-member arithmetic, equal-clock ordering and exact stop/reattempt cutoffs. check physical time once, team-time twice, and slot-time using actual membership, never an unconditional factor five or ten. 02d's already-excluded 132 seconds are a baseline fact, not an additional subtraction.

implement in four reviewable internal boundaries: (1) segments/associations and preserved source projections; (2) context/identity/labels at existing owners; (3) strict preparation artifacts/command; (4) full-corpus reconciliation and consumer/content review. source, systems and hockey/content reviewers challenge each boundary independently; root resolves cross-boundary meaning. retain originals and new distinct broken-game fixtures under existing policy. delete temporary campaign tests/controllers/test-only dependencies after final checks; retain compact checked facts and receipts. no new persistent test harness is assigned.

v1-03 owns rate/scoring/microstat reductions and their additional matched masks; v1-05/07 own outcome/design/latent targets; v1-08 owns numerical elapsed design and value-dependent support; v1-10/11 own qualified penalties and inferred movement. v1-13 can develop schema/application contracts independently. all later fits join v1-02's separately identified coaching evidence. expensive fitting, source acquisition and site activation require their own assignments. success here means usable, honest common evidence—not finished cards or scientific admission.
