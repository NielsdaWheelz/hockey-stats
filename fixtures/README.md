# offline capture corpus

the initial eight fresh nhl responses were captured on 2026-09-29 with the production command on node `24.21.0`. all returned http `200`; their bodies total 993,223 bytes. exact request urls, retrieval times, selected response headers, saved lengths and sha-256 digests are in each `capture.json`. all initial eight responses advertised gzip; `body.bin` preserves the decompressed http-client bytes before text decoding or parsing. no source body was modified. `.gitattributes` treats these bodies as binary artifacts, preserving the reports' original crlf bytes and disabling textual diffs/merges; inspect the files directly.

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

all array indices below are zero-based. source counts are read from the saved responses, not generated regression snapshots. report sections were checked manually during initial admission; the later play-report parser is described below.

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

## reconstruction source admission

pr2b adds seven production-captured responses: the play report for each existing game, and all five sources for `2025021094`. the corpus now contains fifteen responses totaling 5,402,645 body bytes. all returned http `200`, captured with node `24.21.0`. each new length and digest was recomputed before admission. no original fixture body or metadata changed. fresh acquisition used new ignored directories; all eight freshly fetched counterparts of the old sources were byte-identical to the existing bodies, so only the two new source pairs were copied into their game directories.

the two added reports have later retrieval times than their four companion sources: `2025020001` at `2026-09-30T02:27:12.006Z` and `2025020006` at `2026-09-30T02:27:41.483Z`. third-game report retrieval was `2026-09-30T02:27:43.232Z`; its companion request times remain in their own capture records. these are utc times on september 30 and local september 29. report bytes retain their original crlf encoding. the first two report digests agree with the earlier research copies, but their admitted metadata comes from the production capture command.

before copying, both core bodies agreed on numeric game identity, date, season and teams. every repeated play-report `GameInfo` header contained the matching date, game number and `Final`; every repeated on-ice column header agreed with the away/home abbreviations. all reported player jerseys mapped uniquely through each game's `(teamId, sweaterNumber)` roster. report row numbers, api event ids and api sort orders remain separate identifiers.

| checked evidence | exact source locators | result and limit |
|---|---|---|
| first-game report admission | `2025020001/play-report/body.bin`: repeated `GameInfo`, on-ice headers and `tr[id^="PL-"]` | `Tuesday, October 7, 2025`, `Game 0001`, `Final`, `CHI On Ice`, `FLA On Ice`; 364 report rows. 119 timed attempts and 70 faceoffs each have one unique period/clock/kind match to the api. extra report rows are retained, not zipped to api positions |
| second-game report admission | `2025020006/play-report/body.bin`: same locators | `Wednesday, October 8, 2025`, `Game 0006`, `Final`, `CGY On Ice`, `EDM On Ice`; 378 report rows. 123 timed attempts and 58 faceoffs each uniquely match; shootout remains untimed |
| shortened-overtime game identity | `2025021094`: both core bodies and summary/report `GameInfo`, `Visitor`, `Home`, on-ice headers | `2025021094`, `20252026`, regular season `2`, `2026-03-20`; away `12/CAR`, home `10/TOR`, final `4–3`, outcome `OT`. reports identify `Friday, March 20, 2026`, `Game 1094`, `Final`; 307 api events and 310 report rows; shifts `735 = total 735` |
| checked coordinate rotations | first-game api event `101`, recorded blocked-shot `(-61,3)`; goal `258`, recorded `(66,-1)`; goal `630`, recorded `(-63,-15)`; each event's reported defending side | normalized coordinates are `(61,-3)`, `(66,-1)`, `(63,15)` respectively. rotation uses the event's team and reported frame; the first remains a block location, not an inferred shooting origin |
| explicit penalty-shot goal | third-game api `plays[164]`, event `153`; report physical row index `167`, `PL-168` | period 2 `12:35`, `GOAL`, `CAR #50 ROBINSON(12), Penalty Shot`; report lists shooter `50/L` → `8480762` and opposing goalie `60/G` → `8479361`, situation `0101`. `EV` does not make this genuine 5v5. recorded coordinates `(-78,2)` normalize to `(78,-2)` from reported home defending `left` |
| overtime endpoint | third-game api `plays[304..306]`, events `1133`, `476`, `480`; report `PL-308`, `PL-309`, `PL-310` | goal, period-end and game-end all at period 4 `00:41`, remaining `04:19`. the winning goal retains the outgoing three-skater-plus-goalie sets. overtime exposure ends at 41 seconds; the remaining 259 nominal seconds do not exist as game exposure |
| actual elapsed gap | third-game shifts `data[151..152]`, `data[156..157]`, player `8476873`, team `12` | repeated type-517 intervals period 2 `18:28–19:20` (52 seconds) and period 3 `13:50–14:56` (66 seconds) make 118 seconds unresolved. these rows remain evidence; overlapping intervals are not unioned. reconstruction retains 2739 seconds 5v5 and 784 other, totaling 3641 seconds with the unresolved spans |
| actual ambiguous join | third-game api `plays[168..169]`, events `252/253`; report period 2 `13:23` `SHOT` rows | two api attempts and two report rows share the same join key. both attempts remain ambiguous; source order cannot resolve membership. their recorded locations remain independently available |

## manually corroborated exposure and boundary facts

selected official event-summary and home/visitor-shift reports were inspected separately during verification. these overlapping nhl exports corroborate source facts; they are neither independent measurements nor extra production inputs. retrieval evidence remains in ignored local research files. the following public report locators make the checks repeatable.

| checked fact | manually inspected locator | consequence |
|---|---|---|
| attempt and faceoff denominators | [ES020001.HTM](https://www.nhl.com/scores/htmlreports/20252026/ES020001.HTM), team `S`, `A/B`, `MS`, `FW`; [ES020006.HTM](https://www.nhl.com/scores/htmlreports/20252026/ES020006.HTM), same columns | first game chicago `19+18+13=50`, florida `37+19+13=69`: 119 attempts; second calgary `22+21+14=57`, edmonton `35+19+12=66`: 123. blocked attempts total `37+40=77`; faceoff wins total `70+58=128`. all 11 teammate blocks survive with shooting-team ownership |
| first game's goalie-presence correction | saved game summary `EVEN STRENGTH`, reported 5v5 `50:18`; [TV020001.HTM](https://www.nhl.com/scores/htmlreports/20252026/TV020001.HTM), knight `#30`, shift 3, period 3 ending `19:04`; [TH020001.HTM](https://www.nhl.com/scores/htmlreports/20252026/TH020001.HTM), bobrovsky `#72`, three full-period shifts | `3018−56=2962` seconds of genuine 5v5. the summary's label includes 56 seconds without chicago's goalie; period endpoint/goalie checks support this correction |
| second game's goalie gaps | saved summary reported 5v5 `49:20`; [TV020006.HTM](https://www.nhl.com/scores/htmlreports/20252026/TV020006.HTM), wolf `#32`, shifts 1/2 and 4/5 | goalie gaps period 1 `10:47–11:04` (17 seconds) and period 3 `04:29–04:47` (18 seconds), both inside the reported 5v5 intervals: `2960−17−18=2925` genuine-5v5 seconds |
| outgoing shot-boundary counterexamples | second-game api `plays[108]`, event `568`, report `PL-112`, period 2 `01:51`; api `plays[195]`, event `776`, report `PL-199`, period 2 `17:14`; visitor shift report weegar `#52` shift 15 and bahl `#7` shift 20 versus bean `#24` shifts 7/13 | report retains weegar rather than incoming bean at `01:51`, and bahl rather than incoming bean at `17:14`. named actor and situation checks alone fit both candidate lineups; exact report membership supports `before` links |
| goal/faceoff boundary distinction | first two play-report goals and faceoffs, corresponding shift endpoints | all 11 timed goals match outgoing membership; all 128 faceoffs match incoming membership. no universal incoming-lineup boundary rule is valid |
| third game's shortened overtime | [TH021094.HTM](https://www.nhl.com/scores/htmlreports/20252026/TH021094.HTM), woll `#60` shift 4; nylander `#88` shift 19 and tavares `#91` shift 19 | all run period 4 `00:00–00:41`, corroborating the endpoint; the winning goal remains attributable before the horizon ends |

reconstructed time partitions are disjoint and cover the supported horizons. first-two-game genuine-5v5 skater sums reconcile independently for each team to five times the supported seconds. the third game deliberately retains actual source gaps and ambiguous events; adding it does not certify complete reconstruction. source locations and elapsed lineups have separate coverage, and no shooting origins or model eligibility follow from these checks.

## season reference admission

pr2c adds four production captures for the 2025–26 regular season under [references/20252026](references/20252026/), retrieved on local 2026-09-29 (utc 2026-09-30) using node `24.21.0`. all returned http `200`. their client-delivered bodies total 832,140 bytes. every saved length and sha-256 digest was independently recomputed before copying, and every admitted file was compared byte-for-byte with the production output. `.gitattributes` applied binary handling before admission. all fifteen existing game receipts and bodies remain unchanged.

| source | request time, utc | checked received/advertised rows | body bytes |
|---|---|---|---|
| `season-summary` | `2026-09-30T04:12:21.559Z` | `1 / 1` | `634` |
| `season-games` | `2026-09-30T04:12:21.812Z` | `1312 / 1312` | `327491` |
| `skater-bios` | `2026-09-30T04:12:22.016Z` | `940 / 940` | `459134` |
| `goalie-bios` | `2026-09-30T04:12:22.276Z` | `98 / 98` | `44881` |

checked directly from admitted bodies, independently of interpretation:

- summary `/data/0/id = 20252026`; `/data/0/totalRegularSeasonGames = 1312`. inventory contains 1,312 distinct ten-digit ids, with matching explicit season/type and distinct positive teams. all rows report numeric states `7 / 1`; these do not establish gamecenter completion.
- the three fixture ids agree with inventory on date, season, regular-season type and home/away team ids. their identities remain in the admission tables above.
- summary `/data/0/startDate = "2025-10-07T17:00:00"`; `/data/0/regularSeasonEndDate = "2026-04-17T00:00:00"`. retain this offset-free text; the last inventory date is april 16.
- skater `/data/837`, player `8486169`, has birth date `2004-05-06` and explicit null `shootsCatches`. this player is outside the three games' roster population; the reference observation retains its null reason.
- goalie `/data/40`, player `8475683`, has birth date `1988-09-20`, catches `L`, and current team `TOR`; the first game's roster places him on team `13` (florida). the fresh locator is **40**, whereas the earlier scratch research reported 86. neither row order nor current team establishes historical affiliation.
- each bio report contains distinct player ids; the reports have no overlapping ids. together they cover all 120 distinct ids in the three available rosters, each with a birth date and shoots/catches value. this includes unused goalies `8480193`, `8482821`, `8475717`, `8482445`, `8475883`, `8476932`; roster membership is not participation.

the offline audit reports 1,312 expected games, 3 reconstructed and 1,309 missing captures. the three available games contribute 8,626 supported 5v5 seconds, 118 unresolved seconds and their separately scoped attempt/location totals. missing games have no invented exposure. all 120 roster ids have references in these examples; unavailable rosters for the other 1,309 games prevent league-wide completeness claims. historical admission and model eligibility remain unassessed.

roster-report availability was spot-checked at [RO020001.HTM](https://www.nhl.com/scores/htmlreports/20252026/RO020001.HTM), [RO020006.HTM](https://www.nhl.com/scores/htmlreports/20252026/RO020006.HTM), and [RO021094.HTM](https://www.nhl.com/scores/htmlreports/20252026/RO021094.HTM). each identifies the matching date, game and teams and includes playing rosters, scratches and head coaches. these remain manual evidence, not new production inputs or an assessment of historical availability. selected event-summary and shift-report facts already documented above supply the reconstruction corroboration; no duplicate parsers were added.
