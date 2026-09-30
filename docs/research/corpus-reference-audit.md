# corpus and reference source audit

date: 2026-09-29, local time. read-only investigation for [pr2c](../specs/02c-corpus.md). the user confirmed local captures now and the drive later. scratch downloads are research evidence, not admitted fixtures or a historical corpus.

## source choice

use four fixed official season responses. the earlier weekly-schedule/player-landing proposal supplied the right facts through unnecessarily many requests. direct season inventory and bulk bios provide a smaller acquisition boundary.

| source, inspected request | observed facts | limits |
|---|---|---|
| [season metadata](https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D20252026&limit=-1) | one matching row; `totalRegularSeasonGames = 1312`; `numberOfGames = 82` | nominal games per team is not a population denominator; dates have no timezone offset |
| [regular-season games](https://api.nhle.com/stats/rest/en/game?cayenneExp=season%3D20252026%20and%20gameType%3D2&limit=-1) | 1,312 unique ids, matching advertised total and season count; 32 teams each appear 82 times; dates 2025-10-07 through 2026-04-16 | source agreement supports a captured inventory, not an independent historical census; preserve corrections as new captures |
| [skater bios](https://api.nhle.com/stats/rest/en/skater/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D20252026%20and%20gameTypeId%3D2&limit=-1) | 940 rows and unique player ids; birth date and shoots/catches | omitting the game-type filter returned 1,182 rows but only 940 unique players; rows do not echo season/type |
| [goalie bios](https://api.nhle.com/stats/rest/en/goalie/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D20252026%20and%20gameTypeId%3D2&limit=-1) | 98 rows and unique ids, none overlapping the skater ids | report membership does not establish a game's roster or participation; current affiliation is not historical affiliation |

the two bio reports cover all 120 distinct roster ids in our three admitted games, including six unused backup goalies. that checks these examples; it does not establish coverage of every roster-only player. preserve each report's exact filtered request as population provenance. do not manufacture a season field attributed to its rows.

## consequential checks

- skater `/data/837`, player `8486169`, has `birthDate: "2004-05-06"` and `shootsCatches: null`. the [player landing response](https://api-web.nhle.com/v1/player/8486169/landing) also lacks handedness. missing remains missing; another request is not a justified default value.
- goalie `/data/86`, player `8475683`, reports birth date `1988-09-20`, catches `L`, and current team `TOR`; the admitted 2025 florida game lists him on team `13`. admit the biographical fields without importing current team, position or performance as historical context. fixture row indices must be rechecked at admission.
- every target-season inventory row reports `gameStateId: 7` and `gameScheduleStateId: 1`. gamecenter independently supplies `OFF` for the three fixtures. a complete numeric-state vocabulary was not established; preserve numeric states rather than invent an enum or use scores to certify completion. existing game interpretation owns completed-game admission.
- the season's regular-season end boundary is 2026-04-17, but the last inventoried game date is april 16. boundaries do not imply games on every date. keep offset-free source times as source text; the corpus does not need invented utc instants.
- [2019–20 metadata](https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D20192020&limit=-1) retains nominal `numberOfGames: 82` but reports 1,082 regular-season games; its [game inventory](https://api.nhle.com/stats/rest/en/game?cayenneExp=season%3D20192020%20and%20gameType%3D2&limit=-1) also contains 1,082. no hardcoded 82-game or 1,312-game rule.

the [weekly schedule](https://api-web.nhle.com/v1/schedule/2025-10-07) agrees for its 48 games. [toronto's season schedule](https://api-web.nhle.com/v1/club-schedule-season/TOR/20252026) contains 88 games including six preseason games; the 82 regular-season rows agree with the inventory on ids, dates, teams and scores. these were selected cross-export checks, not new production dependencies.

## consequence and cost

pr2c captures these four responses, then audits the complete inventoried regular-season population against explicitly selected local capture roots. missing local games remain rows in that audit. reference availability cannot certify scientific eligibility; 03–04 still own historical horizon, features and validation.

bulk bios avoid per-player requests but can omit players without report rows. keep those references unavailable. player landing remains a documented direct source for a demonstrated future need, not an automatic fallback or another pr2c command. existing game captures and raw bodies remain unchanged. historical layouts, completeness and provenance remain unverified until the external-data audit.

## production admission follow-up

pr2c captured and admitted the four sources with the production command. [fixture admission](../../fixtures/README.md#season-reference-admission) records actual retrieval times, byte checks and rechecked facts. counts remain 1,312 inventory games and 940/98 bio observations covering all 120 fixture roster ids. the admitted goalie locator for player `8475683` is `/data/40`, superseding the scratch locator `/data/86` for this retrieval. player `8486169` remains `/data/837` with null handedness and is outside these fixture rosters. the earlier scratch download is not the admitted evidence.
