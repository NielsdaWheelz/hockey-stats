# pr2b — reported event membership and reconstructed exposure

status: implemented and [verified](02b-verification.md) on `implement/02b-reconstruction`, not yet merged. implementation was authorized on 2026-09-29; pr2a is merged. the user confirmed adding the official per-event on-ice report. [brief](../brief.md), [architecture](../architecture.md), [source audit](../research/source-audit.md) and [boundary evidence](../../fixtures/README.md#manually-corroborated-exposure-and-boundary-facts) supply the decisions and rationale.

## target and boundary

one offline command reads a game's captures and produces attributable event membership, elapsed lineups, genuine 5v5 exposure, normalized recorded attempt locations and separate coverage counts. **reported event membership and reconstructed elapsed membership are different evidence.** neither source repairs the other silently.

support completed regular-season games in the current source layouts, including regulation, shortened overtime, shootouts, empty nets and identified penalty shots. preserve unsupported evidence with a located consequence. no historical importer, model/features, blocked-origin imputer, database, website, stage runner, alternate feeds or compatibility layer. the external corpus remains separate; two or three fixtures do not establish historical coverage.

## composition and commands

extend the existing effect capture command with a fifth fixed source, `play-report`:

`https://www.nhl.com/scores/htmlreports/{season}/PL{gameSuffix}.HTM`

reuse its body/metadata writer, named user-agent, sequential requests, no-overwrite and failure behavior. capture metadata stays version 1; exit 0 now requires five complete 2xx responses. no source-selection flag or supplemental downloader. the summary report remains manually checked reference evidence.

from the prepared `analysis/` environment:

```sh
.venv/bin/hockey-stats-reconstruct --capture ../fixtures/captures/2025020001 --out ../var/reconstructed/2025020001.json
```

reuse existing argument/path checks, exclusive finite-json writing and implementation identity. both options occur exactly once; output is new, outside the capture directory, with an existing parent. no network or hdd discovery. `interpret_game(directory)` performs source interpretation; pure `reconstruct_game(document)` calculates the records below. do not load a serialized interpreted file or introduce a second source reader. retain the useful interpretation command.

write one envelope: `{schema_version: 1, implementation, interpreted, reconstruction}`. `implementation` uses the existing git/dirty/python fields once; `interpreted` is the current `GameDocument` without duplicate invocation identity. interpretation advances to schema version 2 for the changes below; rerun cheap old outputs, with no version-1 reader or migration.

help/syntax exits remain 0/2. input-contract, filesystem and programming errors remain errors. after a successful write, reconstruction exits 0 when there is an admitted game and at least one interval or timed event classified `five_on_five` or `other`; otherwise it writes the available diagnostic and exits 1. zero genuine-5v5 seconds can be a supported result. exit 0 does not certify completeness or model eligibility.

## interpretation changes at the responsible layer

read all five fixed capture records using `read_capture`; absent report metadata means unavailable event evidence, not permission to infer a replacement lineup. preserve the existing integrity and cross-game admission rules.

add `away_team_abbrev` and `home_team_abbrev` to `game`, and `sweater_number` to each roster row from `rosterSpots[*].sweaterNumber`. compare existing numeric/date/season identity before merging nullable labels: use the sole known or agreeing abbreviation; conflicting supplied abbreviations become null with an issue and prevent report admission, without erasing numeric identity. sweater mapping is strictly within this game and team; duplicate/ambiguous mappings are unresolved, never name-matched. add event `kind_valid`, using the existing kind/code validation once; downstream code must consume that result.

preserve independently valid shift endpoints when duration is missing or disagrees. `start_seconds` and `end_seconds` still require coherent ordered bounds within the supported period; a bad pair remains null. `duration_seconds` is the parsed reported duration, null when absent/invalid. add `interval_status: coherent | inconsistent | unavailable | not_shift`: coherent requires bounds and reported duration to agree; inconsistent means usable bounds but disagreeing duration; unavailable includes missing duration/bounds and unknown kinds; `not_shift` means a recognized non-shift record, currently type 505. missing duration can leave usable bounds for localizing the gap. existing player-toi reconciliation is unavailable when any contributing interval is not coherent. never parse issue prose or repeat clock interpretation downstream.

use one focused `play_report.py` parser with `beautifulsoup4` and the explicitly selected stdlib `html.parser`; lock the dependency. no hand-built html state machine, lxml dependency or generic report framework. HTML extraction belongs here; source clock/identity interpretation remains in `interpret.py`. share existing clock primitives when actually reused.

admit a report only when its `GameInfo` date/game number, final status and away/home on-ice column abbreviations agree with the admitted game. check repeated page headers for contradictions; a missing/mismatched identity makes the report unavailable while other source facts survive. do not rely on the requested filename alone. unsupported structure is named unavailability; an unexpected parser/programming defect is an error.

add `report_rows: list | null` to interpretation. select event rows `tr[id^="PL-"]` in document order and their **eight direct cells**: number, period, strength, clock, token, description, away members, home members. the clock cell's fragments are elapsed first, remaining second. avoid nested player-table cells. preserve every selected row; wrong cell counts retain locators with unavailable extracted fields. fields:

| field | meaning |
|---|---|
| `source_index`, `row_id`, `event_number` | zero-based index among selected `PL-` rows, html id and first-cell number; retain duplicates with an issue |
| `period_number`, `time_in_period`, `time_remaining`, `elapsed_seconds` | period and both reported clocks; normalize timed periods under the existing clock rules; shootout remains untimed |
| `event_code`, `reported_strength`, `description` | reported strings, whitespace normalized only in derived output |
| `away_members`, `home_members` | reported member arrays, each `{sweater_number, reported_position, player_id}`; game/team sweater mapping supplies the id |
| `penalty_shot` | true for an attempt description explicitly containing `Penalty Shot`, false for a parsed attempt without that marker; otherwise null |

extract each member's jersey and short position code together from its nested player table's first/second rows, not the descriptive name tooltip. never treat every number in the cell as a jersey. an unavailable/malformed member list is null; keep invalid individual slots with null fields and issues. a blank on-ice cell is null, not proof of an empty side. report locators include physical index and row id, so duplicate ids remain distinguishable. captured bytes stay unchanged.

## elapsed membership

1. establish expected timed periods: regulation 1–3 and overtime 4 when admitted outcome/event evidence establishes overtime. conflicting core `last_period_type` observations make the overtime horizon unavailable; supported regulation survives. completed regular-season regulation establishes 1,200 seconds per period; an agreed shootout outcome establishes 300 seconds of overtime. an overtime-ending game's horizon requires a unique valid api period-4 `period-end` time. compare supplied api/report terminal records by period and kind BEFORE comparing clocks, including final `game-end`; conflicting terminal evidence or a later timed event makes the affected horizon unavailable. missing overtime termination cannot become 300 seconds or the last shot time. shootout has no elapsed exposure.
2. inside each supported horizon, partition at all coherent or bounded-defective shift endpoints and period boundaries. retain positive-length, disjoint `[start,end)` intervals. a shift extending beyond the actual horizon contradicts that period's reconstruction: preserve the row, mark that period's elapsed membership unresolved and create no postgame intervals. do not clip a shift into a valid one. coherent zero-duration shifts contribute no time. only type 517 supplies shifts; known goal-marker rows do not.
3. derive membership from covering coherent shifts and unique roster identities/positions. classify `G` as goalie and `C/L/R/D/F` as skater. unknown categories stay unknown. no shift truncation, overlap union, guessed goalie or synthetic extra attacker. sorted ids provide deterministic output, not a repair of duplicate source rows.
4. overlapping/repeated shifts for a player make the overlapping span unresolved. a defective row with usable bounds affects those bounds; unusable bounds affect its identified period; an unlocatable potential shift affects the game. missing/incomplete shift collections make elapsed membership unavailable throughout supported horizons. unknown shift kinds cannot silently be assumed harmless. unaffected periods/spans survive.
5. plausible elapsed lineups have 3–6 skaters and at most one goalie per team, no more than six total players per side, unique identities and no player on both teams. unsupported counts/identity evidence produce `unresolved`, not `other`. five identified skaters and exactly one goalie on each side produce `five_on_five`; other supported configurations produce `other`.

reported player toi discrepancies remain explicit checks, not permission to force agreement. mark the affected player's full-game exposure completeness unresolved; inspect the located shift evidence to determine which lineup spans can still be supported. a report's even-strength label or a point-in-time situation code never fills a duration gap.

## event membership and its relationship to exposure

map api kinds to report codes: `period-start:PSTR`, `faceoff:FAC`, `hit:HIT`, `giveaway:GIVE`, `goal:GOAL`, `shot-on-goal:SHOT`, `missed-shot:MISS`, `blocked-shot:BLOCK`, `penalty:PENL`, `stoppage:STOP`, `period-end:PEND`, `game-end:GEND`, `takeaway:TAKE`, `delayed-penalty:DELPEN`, `shootout-complete:SOC`. unrecognized codes stay unmatched; no fuzzy mapping.

match timed records by `(period_number, elapsed_seconds, mapped kind)` only when **exactly one record on each side** has that key, with usable identities. api records require `kind_valid`, valid timing, and present unique event ids/sort orders; otherwise membership remains unavailable. multiple candidates are ambiguous; zero candidates are unmatched. never zip competing rows, choose the closest clock, or equate report numbers with api event ids/sort order. this deliberately leaves rare duplicate-clock/type cases unresolved.

resolve reported jerseys to player ids; retain the observed lists even if another check disagrees. missing/duplicate identities, conflicting goalie/skater categories, or incompatible named participants prevent supported event classification. for attempts check the scorer/shooter and any supplied blocker or opposing goalie; a blocker may be a teammate. goalie presence comes from the report lists; absence of `goalieInNetId` does not imply an empty net or reject a block. for faceoffs check both participants. **assists need not still be on the ice at the goal** and are not membership constraints. check the report's leading team abbreviation where the description names an event team; block perspective/zone labels must not reverse the shooting team.

decode valid four-digit timed situation codes as away-goalie, away-skaters, home-skaters, home-goalie. they are corroboration, not identity or a duration schedule. a supplied valid code conflicting with the report counts makes event strength unresolved; absent/invalid codes leave their own check unavailable rather than inventing a code. `EV` alone never establishes genuine 5v5.

identified penalty-shot attempts are `other` for this population regardless of their report strength label; preserve their goal/shot facts. shootout records are `untimed`. ordinary event lineups use the same plausible counts/genuine-5v5 condition as elapsed lineups. an unresolved report match never falls back to shift membership.

compare a supported event's exact player sets with the adjacent supported intervals: immediately before (`start < t <= end`) and after (`start <= t < end`). report `before`, `after`, `both`, `neither` or `unavailable`, and matching interval indices. these are candidate exposure links, not permission to count an event twice. a reported lineup can differ during stopped-clock substitutions; preserve the observation without changing shift endpoints. unsupported linkage is visible, and later models must select a coherent event/exposure population rather than silently use every event with whatever denominator survives.

## coordinates

normalize the four timed attempt kinds independently of membership. require a resolved shooting team, both finite recorded coordinates and `home_team_defending_side` of `left` or `right`. home defending left means home attacks positive x; the away direction is opposite. keep `(x,y)` when already attacking positive x; otherwise rotate to `(-x,-y)`. retain the event's direction evidence. conflicting reported sides within a period make that period's frame unresolved; a missing per-event side remains missing. no shot-majority, period-parity or zone fallback; no clipping or folding to a half-rink.

coordinates remain recorded event locations in feet, centered at center ice. rotated block locations are still block locations. shooting origins and chance values remain uncomputed; coordinate availability is not a spatial-accuracy claim.

## reconstruction schema and content

`reconstruction` contains these exact collections. unavailable scalars/collections are null; supported empty arrays and zero totals retain their ordinary meaning. issues use `{code, source, path, message}`; output rows may refer to indices in this issue list with `issue_indices`. source indices refer to the embedded interpreted collections and hence their capture digests.

| collection | row fields |
|---|---|
| `periods` | `period_number`, `end_seconds`, `end_event_source_index` (null when the completed-game/outcome rule establishes the horizon), `status` (`supported/unavailable`), `issue_indices` |
| `intervals` | `period_number`, `start_seconds`, `end_seconds`, `away_skaters`, `home_skaters`, `away_goalies`, `home_goalies` (id arrays or null), `shift_source_indices`, `classification` (`five_on_five/other/unresolved`), `issue_indices` |
| `events` | one row per api event: `source_index`, `report_source_index` or null, `match_status` (`matched/unmatched/ambiguous/unavailable/untimed`), membership arrays as above, `classification` (`five_on_five/other/unresolved/untimed`), `shift_relation`, `interval_indices`, `attacking_x`, `attacking_y`, `coordinate_status` (`normalized/missing_coordinates/unresolved_frame/not_applicable`), `issue_indices` |
| `player_exposure` | one row per uniquely identified roster skater: `player_id`, `team_id`, `supported_5v5_seconds`, `complete` (boolean), `issue_indices`; partial supported sums must not be labeled complete game toi |

`events` is null without the api collection; `player_exposure` is null without the roster. `periods`/`intervals` are null without an admitted game; a known horizon with missing shifts has unresolved intervals. `issues` is always a list. event membership arrays retain resolvable reported membership even when classification is unresolved. null interval arrays mean membership cannot be supported; source rows remain inspectable. `shift_relation` is unavailable unless the necessary adjacent exposure can be checked. `interval_indices` is empty when no supported link exists. `supported_5v5_seconds` is null when no elapsed classification is available, otherwise the sum over supported 5v5 intervals containing that skater. completeness requires supported horizons and no unresolved span in which that player might participate; a known conflicting player-toi check also prevents completeness. unused roster skaters can have supported zero, not fabricated participation.

`coverage` is another top-level reconstruction field with three objects:

- `time`: `expected_periods` and `supported_periods` (arrays of period numbers), `known_seconds`, `five_on_five_seconds`, `other_seconds`, `unresolved_seconds`. the last three partition known supported horizons; seconds are null if none is available. `known_seconds` is not a full-game denominator while any expected horizon is unavailable; expected periods are null if no game is admitted.
- `attempts`: `known_timed_attempts` counts rows with `kind_valid`, one of the four attempt kinds and `timed_period: true`, including bad-clock attempts whose membership is unresolved. `five_on_five`, `other`, `unresolved` partition these rows; `linked_five_on_five` is the subset having a supported exposure link. `unclassified_events` counts rows whose kind or timed/untimed period cannot be established. all counts are null without the api collection; unknown records prevent complete-attempt claims.
- `locations`: `known_timed_attempts`, `normalized`, `missing_coordinates`, `unresolved_frame`; a disjoint partition, checking coordinates before the shooting team/direction needed for the frame. issues identify the missing/conflicting fact. membership availability does not alter this denominator.

do not publish rates, per-player attempt totals, pre-event score features or model eligibility in this slice. preserve their source evidence. the content designer owns concise command summaries and located explanations: what failed, where, and which quantity is lost. example structure, using actual values:

```text
reconstructed game <id>
time: <n>/<n> period horizons; <n>s 5v5; <n>s other; <n>s unresolved
timed attempts: <n> 5v5; <n> other; <n> unresolved
5v5 attempts linked to exposure: <n>/<n>
recorded locations: <n> normalized; <n> missing; <n> frame unresolved
shooting origins: not computed
output: <path>
```

show nonzero `unclassified_events` explicitly; render unavailable counts/denominators as `unavailable`, never `0/0`. no “valid game,” blanket quality percentage, silent exclusion or raw payload dump. detailed reasons live in the document. the embedded interpretation's `uncomputed` list describes that source stage alone.

## files and implementation boundaries

| files | owner |
|---|---|
| `app/src/operator/capture.ts` | fifth fixed request; existing acquisition behavior |
| `analysis/src/hockey_stats/captures.py` | fifth source's exact capture identity |
| `analysis/src/hockey_stats/play_report.py`, `interpret.py` | focused html extraction; reported identities, clocks, members and structured shift support |
| `analysis/src/hockey_stats/reconstruct.py` | pure intervals, event matching/checks, coordinates, exposure and coverage; explicit typed records |
| `analysis/src/hockey_stats/cli.py`, `pyproject.toml`, `uv.lock` | thin second entry point and shared existing invocation mechanics; parser dependency |
| root `README.md`, `fixtures/README.md`, `fixtures/captures/` | actual commands, admitted source bytes and independently checked facts |

implement source interpretation, elapsed reconstruction, then event/location composition across these boundaries. each owns one meaning. no legacy imports, duplicate hockey calculations in effect, generalized decoder/report registry or persistent test harness. small helpers are justified by actual shared semantics, not hypothetical producers.

## acceptance and verification

1. temporary end-to-end checks establish red through installed commands, then green, refactor and rerun. capture the fifth source live using the production command; interpretation/reconstruction subsequently work offline without `/Volumes`. all existing capture bytes remain unchanged. check effect types and python installation/entry points.
2. admit the two reports alongside the existing fixture captures with their own exact request metadata. acquisition goes into new directories; manually copy only the new source pairs after cross-source inspection. differing retrieval times are explicit. if new reports contradict old captures, retain a separately identified fresh set rather than edit evidence. no fixture-admission framework.
3. add one small real five-source game, `2025021094`, after inspecting its actual captures: penalty-shot goal event `153`, period 2 `12:35`, report `PL-168`; overtime finishes at `00:41`, not five minutes. research found those facts; the implementation must verify its admitted retrieval, not assume unchanged upstream bodies. this third game covers two consequential gaps in the first two examples.
4. verify the documented goals/faceoffs and both boundary counterexamples. all 242 timed attempts and 128 faceoffs in the first two games had unique matches in the research copies. before admission, recheck report rows and roster identities. retain all 77 blocked attempts, including teammate blocks. explicit penalty shots and shootouts never enter genuine5v5; winning overtime goals remain attributable at the endpoint.
5. reconcile disjoint elapsed partitions and per-team skater sums (`5 × supported 5v5 seconds`). research produced provisional game totals of 2,962 and 2,925 seconds for the first two games; independently check selected boundaries and goalie presence before freezing those expectations. use selected event-summary and home/visitor-shift report rows for manual corroboration, recording source locators and checked facts; these overlapping exports are not independent measurements or new production inputs. report summaries alone are not an oracle. no extra 259 seconds after the third game's overtime winner.
6. temporary synthetic copies exercise: missing/mismatched report; duplicated match key; conflicting api kind/code; unresolved sweater; report/situation disagreement; malformed/overlapping/overrunning shift; incomplete shift collection; missing or disagreeing overtime termination; missing/conflicting frame evidence. require local gaps, surviving unrelated quantities, distinct null/zero and conserved coverage. annotate synthetic provenance and recompute digests when testing semantics. include new-field missingness without erasing old facts and unchanged interpretation-command guarantees.
7. delete all temporary test code, scripts and test-only dependencies after verification. retain fixture bytes and hand-checked facts, a short verification record, and production checks. delete the event-membership issue only after its resolution criteria pass. slice 07 still owns the lasting lightweight suite.

tradeoffs: one extra source and parser replace unsupported event inference. exact conservative joins sacrifice some coverage; no generalized reconciliation machinery is justified yet. one in-memory game document favors inspection over bulk storage. manual source admission and reruns are sufficient recovery. future modeling must evaluate selective missingness and scientific validity; this slice establishes evidence contracts, not a publishable ability estimate.
