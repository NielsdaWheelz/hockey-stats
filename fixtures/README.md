# offline capture corpus

eight fresh nhl responses, captured on 2026-09-29 with the production command on node `24.21.0`. all returned http `200`; their bodies total 993,223 bytes. exact request urls, retrieval times, selected response headers, saved lengths and sha-256 digests are in each `capture.json`. all eight responses advertised gzip; `body.bin` preserves the decompressed http-client bytes before text decoding or parsing. no source body was modified. `.gitattributes` treats these bodies as binary artifacts, preserving the reports' original crlf bytes and disabling textual diffs/merges; inspect the files directly.

purpose: bounded offline examples for later interpretation and application development. these are neither a training population nor a complete boundary suite. no legacy fixtures were imported; the archived projected and synthetic fixtures remain excluded from the source-evidence baseline.

## identity and admission

the following values were directly inspected in both `play-by-play/body.bin` and `boxscore/body.bin`. the corresponding saved report's `Visitor`, `Home` and `GameInfo` tables were manually inspected to corroborate date, teams, game number and final score.

| game directory | `id`; `season`; `gameType`; `gameDate` | `awayTeam.id` / `abbrev`; `homeTeam.id` / `abbrev` | report locator and checked identity |
|---|---|---|---|
| [2025020001](captures/2025020001/) | `2025020001`; `20252026`; `2`; `2025-10-07` | `16` / `CHI`; `13` / `FLA` | [report](captures/2025020001/game-summary/body.bin), `GameInfo`: `Tuesday, October 7, 2025`, `Game 0001`; `Visitor` chicago, `Home` florida |
| [2025020006](captures/2025020006/) | `2025020006`; `20252026`; `2`; `2025-10-08` | `20` / `CGY`; `22` / `EDM` | [report](captures/2025020006/game-summary/body.bin), `GameInfo`: `Wednesday, October 8, 2025`, `Game 0006`; `Visitor` calgary, `Home` edmonton |

purpose and limit: this establishes that the admitted bodies identify the requested examples, rather than trusting the request id. report paths identify the season/type; report text does not repeat the api's full ten-digit id. agreement between nhl exports is corroboration, not an independent measurement of the game.

every `shifts/body.bin` record's `data[*].gameId` matches its directory's game id. each body's saved length and digest were recomputed from local bytes and matched its record. purpose and limit: check identity, collection completeness and storage integrity; a matching digest does not prove correct hockey facts. all files were also read and inspected in a process with network access disabled and without the hdd.

## inspected facts

all array indices below are zero-based. source counts are read from the saved responses, not generated regression snapshots. report sections were checked manually; no report parser is part of the application.

| purpose | exact source or report locator | checked result | limit |
|---|---|---|---|
| regulation result and corroboration | `2025020001`, both json sources: `awayTeam.score`, `homeTeam.score`, `awayTeam.sog`, `homeTeam.sog`, `gameOutcome.lastPeriodType`; report `Visitor`, `Home`, `BY PERIOD` → left/right `TOT` rows, `Goals` / `Shots` columns | final `2–3`, shots `19–37`, outcome `REG`; report agrees | official recorded totals; no adjusted ability or genuine-5v5 restriction |
| shootout accounting and corroboration | `2025020006`, same fields and report sections; report `SCORING SUMMARY` final row: `Per = SO`, `Team = CGY` | final `4–3`, shots `22–35`, outcome `SO`; report `BY PERIOD` has timed goals `3–3` and shots `22–35` | the winning shootout decision changes the final score; it is not another timed-play goal or shot |
| complete play examples | `play-by-play`, `plays.length` | `361` for `2025020001`; `374` for `2025020006` | response record counts, not independently verified event completeness |
| shift collection admission | `shifts`, `data.length`, `total`, every `data[*].gameId`, counts by `data[*].typeCode`; requests use `limit=-1` | `2025020001`: `856 = 856`, `851` type-`517` and `5` type-`505`; `2025020006`: `826 = 826`, `817` type-`517` and `9` type-`505` | complete relative to the feed's advertised total; not every record is a shift, and no exposure is reconstructed |
| preserve block evidence | `2025020001` play-by-play `plays[2]`: `eventId`, `typeDescKey`, `details.eventOwnerTeamId`, `details.xCoord`, `details.yCoord`, `details.blockingPlayerId`, `details.shootingPlayerId` | event `101`, `blocked-shot`, owner `13`, coordinates `(-61, 3)`, players `8482807` / `8473419`; fields retained unchanged | recorded block coordinates do not establish shooting origin; no ownership correction or coordinate inference here |
| preserve same-time order and missingness | `2025020001` play-by-play `plays[0..1]`: `eventId`, `timeInPeriod`, `sortOrder`, `details` | events `52`, `51`, both `00:00`, sort orders `8`, `11`; first event has no `details` key | source order and absence are preserved; no inferred chronology or filled object |
| expose misleading strength labels | `2025020001` report `EVEN STRENGTH` → `5v5` cells; chicago goalie table → `KNIGHT, SPENCER`, `EMPTY NET`, `TEAM TOTALS`, `EV` / `TOT` time columns; play-by-play `plays[356].situationCode` | report `5v5 = 2-6/50:18`; knight `EV = 49:22`, `TOT = 59:04`; empty net `EV = TOT = 00:56`; team `EV = 50:18`; event `1266` has code `0651` | the report's `5v5` total includes empty-net time and cannot certify both goalies present; no genuine-5v5 exposure claim |
| preserve overtime/shootout boundary | `2025020006` play-by-play `plays[*].periodDescriptor`; `typeDescKey = goal`, `details.eventOwnerTeamId`, excluding `periodType = SO` | periods `1–3 REG`, `4 OT`, `5 SO`; six timed goals, three per team; three further `goal` records in `SO` | counting every goal record would misstate timed scoring; this inspection is not a reconstruction implementation |
| preserve non-shift nulls | `2025020001` shifts `data[134]`: `typeCode`, `duration`, `eventNumber`; `2025020006` shifts `data[73]`: same fields plus `eventDescription` | first: `505`, `null`, `630`; second: `505`, `null`, `823`, `Shootout` | null is missing duration, not zero exposure; these records cannot be treated as ordinary shifts |

the fixture values match the specification's 2026-09-29 survey. later upstream corrections require a new capture with its own retrieval time, not edits to these bodies. roster membership does not establish participation or handedness. a captured response remains evidence to interpret, not a validated game or analysis.

## source interpretation audit

additional read-only checks on 2026-09-29 informed the pr2 specification. these are inspected source facts and cross-export reconciliations, not evidence of a completed interpreter or validated on-ice reconstruction.

| purpose | source locators and check | result / limit |
|---|---|---|
| block ownership and zone semantics | both play-by-play bodies: `plays[*]` with `typeDescKey = blocked-shot`; compare `details.eventOwnerTeamId` with the `rosterSpots[*].teamId` of `shootingPlayerId`; inspect `blockingPlayerId`, `reason`, `zoneCode` | all 77 owners match shooting teams. 66 opposing-player blocks have zone `D`; 11 `teammate-blocked` records have zone `O` and matching shooter/blocker teams. neither blanket ownership reversal nor a universal owner-relative zone interpretation is valid |
| reported interval arithmetic | both shifts bodies: type-517 rows' `startTime`, `endTime`, `duration`, `period`; group by `playerId` and compare with boxscore `playerByGameStats` → each side/group → `toi`, `shifts` where present | all 851/817 intervals have positive duration equal to end minus start within period bounds. duration sums and record counts match every supplied player toi/shift count. this is source reconciliation, not proof of genuine-5v5 exposure |
| roster versus recorded use | `rosterSpots`; distinct `playerId` among type-517 shift rows; boxscore goalie `toi` and `savePctg` | each roster has 40 players; 38 have intervals. unused goalies have reported zero toi and absent save percentage; absence is not a zero percentage |
| identity versus order | both play-by-play bodies: `plays[*].eventId`, `sortOrder`, `periodDescriptor`, `timeInPeriod` | event ids are unique but not chronological; sort order strictly increases. calgary/edmonton has 20 shootout-period records, all at `00:00`; those clocks cannot describe timed exposure |
| penalty roles and score snapshots | calgary/edmonton play-by-play: events `477`, `480`; all `goal` records' `details.awayScore/homeScore` | event 477 distinguishes committed-by from served-by; event 480 is a same-time misconduct. timed goal snapshots include the goal; all three shootout goal snapshots remain `3–3`. these fields are not pre-event score context |

additional source inspection during interpretation implementation pinned these acceptance facts directly from the captured bodies, independently of interpreter output:

| purpose | exact source locators | checked result / limit |
|---|---|---|
| distinguish listed goalies from recorded use | `2025020001` play-by-play `rosterSpots[26]`, `[34]`; boxscore `playerByGameStats.homeTeam.goalies[0]`, `.awayTeam.goalies[1]`; all type-517 shifts | players `8480193` (team `13`) and `8482821` (team `16`) are listed goalies with `toi = 00:00`, no supplied `shifts` field and no type-517 intervals. roster membership remains distinct from participation |
| same distinction in the shootout game | `2025020006` play-by-play `rosterSpots[4]`, `[33]`; boxscore `playerByGameStats.homeTeam.goalies[0]`, `.awayTeam.goalies[0]`; all type-517 shifts | players `8475717` (team `22`) and `8482445` (team `20`) have the same zero-toi, absent-count and absent-interval observations. a missing count remains missing |
| retain separate penalty participants | `2025020006` play-by-play `plays[342].details`, event `477`; `plays[343].details`, event `480` | event 477 reports committed-by `8477346`, drawn-by `8478402`, served-by `8482679`, duration `2`, type `MIN`. event 480 reports committed-by `8477346`, duration `10`, type `MIS`. these are reported roles and minutes, not inferred manpower |
