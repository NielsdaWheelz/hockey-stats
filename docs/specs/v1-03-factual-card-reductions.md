# v1-03 — factual card reductions

full handoff under [the program](experimental-player-analysis.md). [card facts](experimental-card-facts.md) owns quantity definitions; [v1-13](v1-13-typed-publication.md) owns the fixed exchange/schema7; [the crosswalk](../product-inventory.md#v1-field-crosswalk-and-card-acceptance) owns card completeness; [the plan](../plan.md#proposed-pr-boundaries-and-dependencies) owns assignment. writing this specification assigns no implementation, acquisition, fitting or activation. no new product preference is required.

## outcome and boundary

produce actual three-season descriptive, microstat and source-evidence rows from checked preparation, preserving every existing observed result. build a candidate through the existing publisher and verify those facts through the typed api and existing comparative/discovery views. v1-16/17 still own complete descriptive/microstat card presentation; real factual delivery does not complete their compositions or the modeled comparative tiles.

real execution follows verified [v1-01](v1-01-shared-evidence.md) integration. it selects `20232024,20242025,20252026` from that five-season preparation and the same three native corpora used by observed aggregation: 3,936 inventory games, including unavailable games. specification and bounded fixture work need no hdd; real acceptance needs the explicitly selected preparation and native inputs, wherever retained. do not copy a new full local mirror. the completed candidate must browse detached.

no coach dependency, new acquisition, fitting, model admission, skating admission, tracking inference, new frontend composition, schema version, endpoint, migration/importer, service or runner. preserve primary `app/dist`, active/previous databases and port 3000. numerical producers may proceed independently after their own prerequisites; this slice does not serialize them behind a factual research gate.

accepted costs: additional source reductions and evidence storage; separate populations and coverage rather than one convenient denominator; conservative exclusions for contradictory attribution; another invocation of the existing observed reducer during candidate assembly. reported penalty credits measure what the sources attribute, not every infraction actually caused. goalie identities/evidence are included, but goalie headers/results remain pending v1-07. no new abstraction or dependency is justified by these costs.

## responsibilities and composition

| owner | concrete change; boundary |
|---|---|
| `analysis_data.py`, prepared readers | consume verified v1-01 facts; no raw parsing or fresh reconstruction in reducers. a demonstrated missing prepared fact is repaired at its existing owner, with affected-boundary checks |
| `observed.py` | existing `aggregate`/`observe_game` own all old populations, credits, spatial cells and shared seconds. expose/reuse their receipts; never copy their eligibility rules |
| new `descriptive.py` | identity enrichment; reported/strength usage; primary scoring; recorded goal context; penalties; starts/score/counterpart usage; fixed per-game evidence projection and factual result composition |
| new `microstats.py` | the fixed thirty-key record: five factual measurements, one pending reference-xg field and precise unavailable-source dispositions. consume shared prepared/observed facts; no parser, probability or duplicate scoring owner |
| `scoring_credits.py`, existing support/chronology owners | reuse credit/team checks; narrowly share pure actor checks for missed shots/hits/blocks where necessary. all new masks stay at their factual population owner, not in rendering |
| `analysis_publication.py`, `publication.py` | existing serializer, catalogs, inserts and candidate verification. repair score shares and the source-backed affiliation invariant below; add the fixed `reported_shifts_unavailable` support reason. no new exchange format or factual calculations in sqlite assembly |
| `analysis_cli.py` | add `facts`; preserve merged `prepare` and `publish`. v1-01 and v1-13 edited this file independently; integrate all three explicitly |
| `app/src/shared/player-analysis.ts` | mirror score shares/support reason; one shared observed-affiliation preservation predicate for typed responses and current consumers |
| `app/src/server/{observed-publication,analysis-publication}.ts`, `app/src/web/analysis-values.ts` | replace the corresponding exact team-list identity checks with that preservation rule; server also checks added affiliations against dressed-game/game-team evidence. current observed/overview reads must accept supported additions and reject lost/conflicting affiliations. no alternate api/calculator or view redesign |
| evidence/content | `fixtures/README.md`, attributed fixtures, `docs/research/facts-v1-03/verification.md`; preserve reproductions and measured acceptance, not temporary controllers |

agree these internal boundaries before parallel implementation:

```text
descriptive.recorded_evidence(prepared_game, observed_game_receipt,
                             source_ids, support_ids) -> fixed per-game evidence
descriptive.reduce_game(prepared_game, observed_game, recorded_evidence) -> game reductions
descriptive.summarize_season(people, game reductions, observed_result) -> person/descriptive/context rows
microstats.reduce_game(prepared_game, observed_game_receipt) -> fixed p/u/h/b reductions
microstats.summarize_season(people, game reductions, observed_result,
                           source_ids, pending_method_id) -> skater_microstats rows
descriptive.build_factual_results(prepared: Path, observed: Path, output: Path) -> result manifest
```

these are ordinary typed functions over explicit named records, not a generic reducer/plugin protocol or new serialized intermediate product. game reductions retain count, seconds, support/dispositions and source locators needed for checks. one projection supplies both descriptive context summaries and emitted interval facts. process one season at a time; stream evidence in each table's declared tuple-key order (`game_id,source_index` for events, not calendar order). history facts are already prepared. do not materialize a season×player×event×cell array. compact season accumulators and a reread suffice; no new cache/spool framework.

## command, inputs and exchange

```text
hockey-stats-analysis facts --prepared DIRECTORY --observed FILE --out NEW_DIRECTORY
hockey-stats-analysis publish --observed FILE --results DIRECTORY --out NEW_DIRECTORY
```

`facts` is offline. use `analysis_data.read_prepared/read_prepared_game/read_prepared_people`, `publication.read_selection`, `observed.aggregate` and `analysis_publication.write_results`. reject repeated/unknown flags, incomplete artifacts, purpose/year/game mismatches and digest drift. each displayed native corpus digest must equal its corresponding prepared selection binding; check game identity, original source indexes and source receipts when joining. fixture selections have explicitly matching bounded game sets and remain `purpose=fixture`; no relabeling a captured fixture as real.

the observed owner may reopen its existing bound native/source inputs. new reducers use prepared facts and observed receipts only. call the observed owner once per displayed season here; the publisher invokes it normally again. no use of the live sqlite database as a source, latest-directory lookup or alternate-path fallback.

write the existing `player_analysis_results` manifest and sorted/hash-bound jsonl members, manifest last into a fresh directory. bind `purpose`, exact `prepared_sha256`, the three ordered display seasons and their `observed_bindings`. keep all fixed source/method/support catalogs and family dispositions:

| disposition | tables/results |
|---|---|
| provided `descriptive` | one `skater_descriptive` and `skater_context` row per resolved season skater |
| provided `microstats` | one complete thirty-key `skater_microstats` row per resolved season skater; unavailable fields stay typed |
| provided `evidence` | actual `attempt_fact`, `dressed_game`, `interval_fact`, `interval_player`, `interval_location`; complete `context_coverage` dispositions |
| not computed | `spatial`, `execution`, `shootiness`, `penalties`, `territory`, `goalie`, `ledger`; explicit explanations and no manufactured rows |

provided factual payloads may have missing measurements, but available input plus an unwritten reducer is not acceptance. publication source records bind actual prepared/native receipt hashes and exact definitions; public urls alone do not establish admission. use fixed source/support policy identifiers for the populations below. record exclusions and source conflicts with located reasons. no prior-only or model-uncertainty claim for factual counts.

## populations and reduction rules

counts are integers; elapsed seconds remain source units until `3600*n/seconds`. zero supported events can be zero. zero denominator gives an unavailable rate; absent evidence is not zero. retain zero-event time. union overlapping exclusions before summing duration. different family masks do not propagate into each other.

event joins use `(season,game_id,source_index)`; nullable/duplicated native event ids cannot be keys. **old observed segment indexes and prepared all-strength segment indexes are different axes.** join/verify their native interval identities, period, bounds and full membership; never match by list position. source-supported boundary events use the existing before/after association. no nearest-clock assignment or splitting a count fractionally between intervals.

| quantity/population | base, additional checks and exact output |
|---|---|
| reported usage | dated boxscore player-games, once per player/game/team. `supported_games/missing_games` refer to known toi; appearances require positive toi. known seconds and appearances share support. shifts have independent missingness: publish total only when complete over listed games, otherwise null plus `reported_shifts_unavailable` count. unknown unassignable games stay season coverage, not invented player appearances |
| strength usage | supported elapsed membership, independent of ordinary-attempt/actor completeness. ev/pp/pk/other and exact states follow card facts; group appearances count games with positive group time. a missing shot location/credit cannot erase usage |
| primary scoring | `five_on_five` **and its exact-state row** copy the old personal goals/a1/count/time/coverage. other states use saved ordinary-attempt support plus reconciled goal/on-net credit masks. ev sums that preserved 5v5 component and matched 4v4/3v3 components; other groups sum their disjoint states. compute rates from summed counts/time, never average rates |
| primary-assist recipients | keep legitimate off-ice first assistants, using the event's state and the recipient's own matching time. a supported credit can have zero personal seconds and a null rate. missing secondary credit cannot tighten goals/a1. unsupported strength stays unclassified, not forced into ev |
| recorded all attempts | exact old observed mask/dispositions, with each physical team side counted once |
| recorded goals/on-net | old all-attempt support, with any additional goal/on-net accounting conflict removing that interval's paired counts/time. do not require personal scorer/assist identity or chance-model physical eligibility. recorded own/awarded goals remain recorded outcomes where team accounting is supported; `goals <= on_net` on identical support |
| recorded locatable unblocked | exact old spatial masks/cells. no new smoothing, rebinning, origin imputation or dropped zero-event time |
| `u`: personal unblocked | saved ordinary 5v5 support; goal+save+miss, corroborated recorded shooter/scorer and team. extend shared prepared actor checking to misses; prepared goal/save `credits` alone are insufficient. no geometry, shot-type or probability prerequisite |
| `h`: personal hits | valid 5v5 membership/time and usable play-by-play/report collections; reconcile every api hit and report `HIT` through existing native associations, then check hitter's team and opposing hittee. unmatched/report-only/ambiguous hits mask affected time; do not invent an api event. absent collections mask the game; invalid-kind rows cannot silently establish zero hits. no unrelated ordinary-shot/assist restrictions |
| `b`: credited blocking | saved ordinary 5v5 support; valid opposing shooter/blocker identities and membership. numerator own credited blocks; denominator opponent ordinary attempts while present, on that same support. assert numerator ≤ denominator; no block-coordinate requirement |

for new `u/h/b` actor/association conflicts, exclude the affected family for **both team sides of the affected segment**, not merely its event. this deliberately gives up some otherwise usable observations for auditable matched populations. a unique supported assignment selects its segment; unresolved known-clock assignment implicates every touching eligible segment, never a convenient one. missing clock widens to the identified period, or game when period is unknown. report-only hits use their retained period/clock under the same rule. apply only the family's supported 5v5 spans; no fabricated excluded duration for wholly unknown time. retain issue scope and original event. new all-strength credit conflicts use the same located principle outside the frozen 5v5 personal component. explicit penalty shots/shootouts do not enter ordinary opportunity rates.

for all state/group totals, distinguish checked empty support from unknown support. unclassified means unknown strength; a known-strength credit without matched elapsed support instead retains that state in the receipt outside rate counts. group/state sums reconcile to the retained supported subset, not necessarily official all-strength totals. an absent old personal row alone does not prove zero exposure; preserve its unavailable status and source reason rather than inventing a replacement observed row.

### references, deployment and penalties

on/off uses the same provided interval rows as the api: on is focal present; off is focal absent within that player's source-supported **dressed team-games**. trades retain dated team identity. the conversion `team` reference pools that team's physical sides once over those dressed games; league pools each physical side once. `shooting_for`, `shooting_against`, `save_fraction` and share-minus-half follow card facts. a known zero numerator over positive support is zero; zero attempts/time gives null as applicable.

recorded penalty targets are **source-attributed infraction credits**. each source penalty event counts once, including a double minor; distinct same-clock events remain distinct. no inference of advantage awards, coincidence, expiry or misconduct causation. retain original type/description/duration and role dispositions:

- `attributed`: valid taker/drawer/server id with compatible dated team; off-ice attribution is permitted.
- `not_recorded`: optional drawn/served key absent; or source-explicit bench infraction with no individual taker. zero attributed credit, not proof nobody actually drew/served the penalty. retain that limitation and count.
- `unresolved`: supplied null/malformed/conflicting id, missing taker for an individual infraction, or a located contradictory structured identity/team observation. never fill from an assumed player or equate served with taken.

“complete ledger” means a structurally usable api recorded-event collection and supplied role ids checked against dated identity/team evidence, not independent proof of every real infraction. missing/invalid event collections cannot prove zero. prepared report descriptions do not contain structured penalty-role ids: report-role comparison is a named manual source sample in acceptance, not claimed automatic reconciliation. no free-text penalty parser is assigned. preserve any demonstrated contradiction as an attributed unresolved case at the responsible owner. unusable collection excludes that game's affected role counts and player-minutes. unresolved taking/serving excludes the offending team's player-games for that role; unresolved drawing excludes the opposing team's. unknown offending team implicates both. a valid taken role survives an unrelated drawn/served gap.

rates use positive known **reported** player seconds in those same eligible player-games: `60000*count/reported_seconds`. focal, dressed-team and league references pool matching player-game counts/minutes, never physical team-time. source-type categories are mutually exclusive and sum to the attributed total; bench/unattributed/conflicting and any separately supported coincidence evidence remain receipt dispositions, not overlapping category totals. zero-toi credits stay source evidence outside the rate. disclose the recorded-credit interpretation beside every reference.

count coalesced player shift starts only when the actual start has supported 5v5 state. a midshift transition into 5v5 is not a new start. use prepared faceoff/zone/on-the-fly/unknown facts; all five categories share the all-start denominator.

score seconds use supported 5v5 elapsed chunks, split at verified score changes. let `K=leading+tied+trailing`, `U=unknown`. known-state shares are their seconds divided by `K`; `unknown.share=U/(K+U)` is separately labeled coverage. zero denominators give null. **repair python and typescript validation accordingly**; the current python check incorrectly puts unknown seconds in every denominator. team/league deployment guides pool the same player-start/player-second units over their corresponding dressed-team/league player-games, not physical team-time.

counterpart means use exact old shared 5v5 seconds and the one reported-usage reducer: `sum(shared_seconds * counterpart_minutes_per_appearance) / known_slot_seconds`. retain known/all slot seconds and distinct counterparts. all teammate slots reconcile to `4*focal_seconds`; opponents to `5*focal_seconds`. F/D usage bands and their weighted indices follow the fixed card-facts ranks; unknown position/usage cannot become zero or an inferred role. these are usage proxies, not teammate quality or stable line assignments.

## identity, missing fields and source evidence

retain exact observed skater display name and reported position in `person`; preserve every old team entry, including its abbreviation. add only independently supported dated season affiliations from preparation, with their source identities. this may reveal a team in a game the old observed reducer could not use. repair exact team-list equality in the publisher, effect startup reader, typed observed league response and `analysis-values.checkObservedIdentity`; require every old entry unchanged, rather than equal list length/order. use one shared typescript predicate, retaining strict id/name/position checks. old observed `player_season` teams/metrics stay exact. check additions against prepared evidence during production and resolving dressed-game/game-team evidence during publication/server reads. no present-day roster inference or arbitrary superset.

enrich only supported age/hand/sweater/height; retain conflicts in identity support. new resolved skaters/goalies use prepared dated evidence. unknown F/D/G classification stays an attributed preparation/receipt gap, not a guessed kind. no fabricated skater metrics for goalies. the existing goalie family requires model-valued sections; leave it pending v1-07 rather than filling expected totals/methods with zeros. broader person affiliation improves identity coverage without changing old observed team-split facts.

microstats use the fixed [field crosswalk](experimental-card-facts.md#microstat-quantities-and-populations), not a new field registry:

- exact old `goals_per60` and `primary_assists_per60`; computed `unblocked_attempts_per60`, `hits_per60`, `blocked_attempt_share`. counts, own denominator, support, construction and source reference travel together.
- `reference_xg_per60`: null, `not_computed`, model-valued; v1-06 owns it. declare an honest pending method with bound prepared identity, null design/cutoff, no fitted seasons/state and explicit non-computation evidence. this satisfies existing typed provenance without inventing a model.
- twenty-two tracking-dependent measurements: `missing_source`, with their specific absent observations. `primary_pass_xg_per60` remains model-valued with pending method and missing pass-source evidence; source-modeled puck management keeps source provenance. no inferred setting/territory substitutes.
- both skating measurements: no admitted player-season context/census under [v1-04's receipt](../research/skating-v1-04/verification.md). use that specific limitation, not the obsolete assertion that every request returns 403. no reuse of an unverified detail number.

`recorded_evidence` returns the fixed per-game rows and coverage inputs consumed by summary reducers and the serializer:

| table | producer obligation |
|---|---|
| `attempt_fact` | source-supported timed attempt evidence, keyed by original source index; nullable actors/state/type/coordinates stay unavailable. preserve recorded coordinate meaning, block contacts and recorded-stop/reattempt reasons. no fitted values, setters or execution shares |
| `dressed_game` | exactly supported dated player/team/game affiliation; no appearance inferred from a current roster or merely from a nonzero stat |
| `interval_fact` | old observed positive disjoint 5v5 segments with directed team sides, known period horizon and the three recorded populations' matching masses/time; shared interval id/bounds across populations |
| `interval_player` | exact supported five skaters per side, once regardless of how many populations use the interval; no orphan membership or goalie |
| `interval_location` | sparse existing display-cell integer masses on recorded-locatable support, closing to its interval and player summaries |
| `context_coverage` | every skater × all five populations. three recorded populations provided with measured exclusions/gaps; both neutral-valued populations explicitly not computed, with no invented measured coverage |

source events can survive absent elapsed exposure or unresolved physical action. map the valid source event kind to `goal|save|miss|block`; prepared physical `outcome` may be null for an own/awarded goal. `shooter_id` is the supported physical shooter, never a copied credited scorer; retain null when unresolved. personal geography requires that supported shooter and event state. a recorded goal row does not prove a release, and its existence cannot determine a later fit's eligibility.

omit explicit penalty shots/shootouts and invalid timed-kind rows from this fixed personal-event view, recording their dispositions; do not exclude every `physical_status=outside_population`, which also contains recorded own/awarded goals. credited scorer and physical-action status remain in prepared evidence. probability fields stay pending through the existing source-row insertion. recorded-stop/reattempt labels copy supported facts/reasons, never automatic false. use existing geometry/frame transforms once; shooting-team display orientation does not change the original observation. rows inherit exact source/support catalog identities; no invented physical release or silently discarded original evidence.

## content and acceptance ownership

assign a content reviewer to each parallel feature boundary; this is review of real definitions/payloads/current consumers, not a new design system:

| content owner | good content and required example |
|---|---|
| identity/usage/scoring | reported versus included minutes, ev union, own counts/time and partial coverage; trade, zero-toi and off-ice assist examples |
| descriptive/context | both on/off populations, physical versus player reference denominators, recorded conversion, penalty-credit limits and usage-proxy labels; unknown score/start and thin counterpart support |
| microstats | “shots” explicitly means unblocked attempts, not shots on goal; fractions have their own units; each pending/missing field explains why. no ability/uncertainty claim from factual standing |
| evidence/publication | original source keys, coordinate meanings, supported-zero versus unknown, recorded versus pending model values; existing comparative header/goals/a1/context and csv/png retain season, population and coverage |

implement/review in four non-overlapping work packages: (1) shared identity/support projection and descriptive reductions; (2) microstats over that agreed projection; (3) catalog/result/cli and invariant repair; (4) independent source/arithmetic/content integration. packages 1/2 may proceed together after the internal record boundary is agreed; one owner edits shared publication/cli files. v1-16 may implement its view against settled typed fixtures independently. do not expand this assignment into that view or the [comparative export-density follow-up](../issues/comparative-export-density.md).

## verification and final state

temporary end-to-end red → green → refactor → green checks exercise the command → real fixed results → candidate sqlite → typed api/current views. delete temporary tests/controllers/test-only dependencies afterward; retain attributed fixture bundles, checked expectations and the verification receipt. no new retained harness is assigned. documentation preparation itself needs only link/consistency/whitespace checks.

| boundary | acceptance evidence |
|---|---|
| inputs/failure | explicit fixtures; absent/changed member, wrong purpose/corpus/year, malformed role and partial output rejected or attributed at the correct boundary. no manifest accepted after failed serialization; no raw writes |
| population arithmetic | zero-event time; overlapping masks once; family-local exclusions; boundary/unavailable events; goal with unresolved personal credit; miss with missing shooter; blocker on wrong team; missing hittee; unknown location does not erase a count. independently sum selected cases and all game→season/group closures |
| scoring/penalties/usage | exact old 5v5 state and ev rollup; off-ice a1, zero denominator and secondary-only disagreement; bench/explicit server/absent optional role/unresolved identity/double minor/distinct same-clock rows; reported shift missingness, trade, source-supported additional person/team outside observed rows and unknown counterpart position. penalty source witnesses include `2025020006:342–343`, `2024020022:163`, `2025021094:106`, `2025020001:113–114`; inspect existing api/report originals |
| references/evidence | on/off partition dressed support; physical league versus penalty/deployment player units; five/four slot closure; goal/on-net and sparse-cell closure; shared interval/membership identity; all thirty microstat keys and all five coverage dispositions |
| real reductions | all 3,936 inventory games accounted for across three seasons, including unavailable games. all supplied skaters have complete factual payloads. actual new source facts traverse publisher/readers; no fixture masquerades as real. reconcile previous observed counts/rates/denominators/coverage/identities/spatial/pairs exactly against the same pinned inputs |
| application | isolated candidate/listener: descriptive/microstat league and player reads, personal-shot evidence and on/off/with-without recorded context agree with independent sums. inspect real comparative usage/goals/a1/context plus history/export propagation; pending model tiles remain pending. detached candidate reads require no preparation, raw or fit paths |
| handoff | record input/result/candidate hashes, per-season support/exclusion totals, source samples, defects/limits, wall time/peak memory/output bytes and exact commands. independent source/arithmetic, systems and content reviews clear concrete findings. protected serving files/database/listener remain unchanged |

stop at verified factual delivery. no scientific success criterion or optional research rerun. newly exposed distinct source failures get complete original fixture bundles under the existing policy and an issue with evidence/resolution criteria. a genuine source gap may remain visible; missing implemented reductions, mismatched exposure, incorrect arithmetic or fabricated provenance may not. v1-05 numerical work and v1-16/17 card completion remain separately assigned successors.
