# pr2c — season corpus and player references

status: reviewed and merged in `90f5c1a`; [verification](02c-verification.md). the user confirmed local captures now, historical drive later. [brief](../brief.md), [plan](../plan.md) and [source audit](../research/corpus-reference-audit.md) supply scope and evidence. real chance-model training and scientific acceptance belong to separate 03b, following 03a's workflow implementation.

## target and boundary

capture a season's official game inventory and player bios. one offline command accounts for every inventoried regular-season game against an explicit local capture root, reuses reconstruction, and records player references and coverage. it establishes available evidence, not a training-ready dataset.

one season per invocation, initially 2025–26; later models may select several separately audited seasons. the inventory defines the population, not directory contents. with the three local fixtures, report 3 present and 1,309 missing captures among 1,312 expected games. no arbitrary subset/date selector, filesystem crawler or implicit newest-capture selection.

no historical importer, source repair, modeling/features, age calculation, database, website, automatic downloader, retry/resume engine or orchestration framework. no legacy adapters or automatic alternate sources. bulk historical admission remains blocked on inspecting the drive; this slice's local behavior does not wait for it.

## acquisition contract

add an effect command, run from `app/` after creating the output parent:

```sh
npm run capture-season -- --season 20252026 --out ../var/references/20252026
```

`--season` and `--out` occur once. season is eight digits describing consecutive years; output is a new directory with an existing parent. `--help` alone exits 0. invalid invocation exits 1, matching capture's existing failure convention. fetch these four fixed sources sequentially, using the existing client/body persistence behavior:

| source directory | exact url template |
|---|---|
| `season-summary` | `https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D{season}&limit=-1` |
| `season-games` | `https://api.nhle.com/stats/rest/en/game?cayenneExp=season%3D{season}%20and%20gameType%3D2&limit=-1` |
| `skater-bios` | `https://api.nhle.com/stats/rest/en/skater/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D{season}%20and%20gameTypeId%3D2&limit=-1` |
| `goalie-bios` | `https://api.nhle.com/stats/rest/en/goalie/bios?isAggregate=false&isGame=false&cayenneExp=seasonId%3D{season}%20and%20gameTypeId%3D2&limit=-1` |

each source retains `body.bin` and `capture.json`. reference metadata uses `schemaVersion: 1`, its fixed `source`, and an eight-digit string `seasonId` instead of `gameId`; other request/response/body/failure fields retain their existing meanings. game capture metadata stays unchanged. share one faithful response-capture implementation, with explicit game versus season identities and urls; no endpoint registry or user-supplied url.

preserve client-delivered bytes before decoding, selected headers, request time, length and digest. keep non-2xx bodies; transport/body/timeout failures do not prevent later requests. filesystem errors stop. retain the existing named user-agent, timeout, no redirects/retries and no-overwrite behavior. exit 0 requires four complete 2xx responses; this does not certify their contents.

## offline composition and failure behavior

from the prepared `analysis/` environment, after creating the output parent:

```sh
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20252026 --games ../fixtures/captures --out ../var/corpus-20252026
```

all options occur once; reject unknown/abbreviated arguments. input roots must exist. output must be new, with an existing parent, outside both input roots. metadata establishes the requested season; conflicting season identities are an input error. resolve paths explicitly, with no external-drive discovery.

1. `interpret_references(directory)` shares strict json and capture-integrity checks with existing capture reading. it owns season/reference semantics below.
2. for each admitted inventory game id in ascending order, look up exactly `<games-root>/<id>`. ignore unrelated directories; never discover the population by listing them.
3. invoke existing `interpret_game` and `reconstruct_game` directly, one game at a time. require `requested_game_id` to match the lookup id even when `game` is null; a wrong requested capture is an input error. compare admitted game id, season, type, game date and home/away ids with the inventory. retain original per-game meaning and detailed issues.
4. write existing reconstruction envelopes under `games/<id>.json`; write `corpus.json` last. share implementation identity and exclusive finite-json writing with existing commands. no serialized-interpreter input or alternate reconstruction algorithm.

absent game directories are missing captures, not zero-exposure games. a present non-directory, malformed local metadata, promised missing body, digest failure or conflicting capture identity is an input error; record the affected game and continue with other games. missing/upstream-unavailable sources remain ordinary evidence gaps under existing interpretation rules. mismatching inventory/game identity is recorded and excluded from corpus aggregates; retain its diagnostic output for inspection. an unidentifiable game also retains its diagnostic if interpretation can produce one.

syntax/help exits 2/0. exit 0 means an admitted inventory was fully accounted for and the report written; missing games, bios and reconstruction gaps can coexist with exit 0. inventory unavailability or any local input-contract error exits 1, preserving the available report. reference input-contract errors and filesystem failures stop immediately; programming errors must surface. output-write failure stops the run. without the final report, the directory is unfinished; remove cheap partial outputs manually and rerun into a new directory. no automatic resume or commit protocol.

## reference interpretation and schemas

reuse existing `Input` provenance and located `Issue` conventions. distinguish malformed local capture records from unavailable upstream evidence. retain source indices and locators for every interpreted row and field issue. no source-body mutation or invented capture metadata.

**season and inventory:** require season-summary `data.length == total == 1`, a matching row `id`, positive `totalRegularSeasonGames`, and an inventory `data` array whose length equals its advertised `total`, distinct game-id count and season-summary count. every inventory row must identify the requested season, game type 2, a valid calendar `gameDate`, a unique matching ten-digit game id, and distinct positive home/visiting ids. admit the inventory only when those checks pass; otherwise retain input/check facts and issues, set `inventory` null, and do not claim a game denominator or run corpus games. this deliberately favors an explicit unsupported inventory over silently dropping rows. do not hardcode a league count or nominal games per team.

upstream ids/counts must be integers, not booleans or numeric strings. derived season/game ids are strings; player/team ids stay integers, as in game interpretation. map summary `id`, `totalRegularSeasonGames`, `startDate`, `regularSeasonEndDate`; inventory `id`, `season`, `gameType`, `gameDate`, `visitingTeamId`, `homeTeamId` to their named output fields. require each game id's year/type to agree with its explicit season/type.

retain `gameStateId` and `gameScheduleStateId` as nullable reported integers, with issues for absent/malformed values; they do not decide completion. existing gamecenter interpretation must still establish a completed regular-season game. keep offset-free season dates as reported text; the audit has no need to convert them to utc or infer missed calendar days.

**bios:** parse skater/goalie collections separately; record received/advertised counts and whether they match. a count mismatch means incomplete collection, not permission to discard coherent rows or claim an absent player was never listed. require a positive integer `playerId`; malformed identities retain located issues and cannot establish references. retain duplicate observations and flag unexpected repeated ids within one report. the exact filtered request establishes report scope; its rows do not themselves report season/type.

`birthDate` must be an actual `YYYY-MM-DD` date; `shootsCatches` must be `L` or `R`. missing, explicit null and invalid fields stay null with distinct reasons; one bad field does not erase the other. use one field-wise rule within and across reports: one distinct known value supplies the joined field, none leaves it null, and conflicting known values leave it null with an issue. preserve every observation, locator and missing/invalid-field issue even when another observation supplies a value. never import current team/position, height/weight or accumulated results as historical covariates. do not calculate age or infer handedness. birth-date plausibility against game dates belongs to the analytical consumer, with the source observation preserved.

| record | required fields / meaning |
|---|---|
| `ReferenceDocument` | `schema_version: 1`, `requested_season`, `inputs`, `season`, `inventory`, `bio_collections`, `bio_observations`, `checks`, `issues` |
| `season` | nullable `{season, reported_regular_games, reported_start, reported_regular_end}`; boundaries are source text |
| inventory row | `source_index`, `game_id`, `season`, `game_type`, `game_date`, `away_team_id`, `home_team_id`, `reported_game_state`, `reported_schedule_state` |
| bio collection | `source`, `received_rows`, `reported_total`, `complete: bool`; counts nullable when unavailable |
| bio observation | `source`, `source_index`, nullable `player_id`, `birth_date`, `shoots_catches`, `issue_indices` into reference issues; source path plus input digest attributes the fields |

`inventory` is null when unsupported, otherwise an ordered array. unavailable bio collections have no observations and a located reason. known empty collections remain distinguishable through their counts. the source documents retain fields outside this projection for later, justified use.

`checks` reuse existing `Check` meanings: `season_summary_rows` and `season_summary_total` compare received and advertised counts respectively with 1; `inventory_rows` compares received and advertised counts; `inventory_unique_ids` compares distinct valid ids with received rows; `season_regular_games` compares inventory rows with the season's reported count. preserve observed/expected integers or null, source, status and reason. invalid individual identities also withhold inventory even when counts agree.

## corpus output contract

`corpus.json` contains `{schema_version: 1, implementation, reference, games_root, games, players, summary, missing_game_ids, issues}`. `reference` embeds the reference document once. paths are resolved local paths; per-game output links are relative to the corpus directory. json is the current inspection/interchange format, not the eventual sqlite publication.

| record | required fields / meaning |
|---|---|
| game row | `game_id`, `inventory_source_index`, `capture_path`, `status`, `reason`, `output_path`, `coverage` |
| game `status` | `missing_capture`, `input_error`, `identity_unavailable`, `identity_mismatch`, `reconstructed`; these partition inventoried games |
| game `coverage` | existing reconstruction `Coverage`, only for matching admitted games; otherwise null. `reconstructed` does not mean complete, useful 5v5, or scientifically eligible |
| player row | `player_id`, `game_ids`, `birth_date`, `shoots_catches`, `observation_indices`, `issues`; one row for every non-null player id in admitted matching game rosters, including unused goalies |
| `summary` | `expected_games`, `games_by_status`, `games_with_unavailable_rosters`, `players_seen`, `players_with_birth_date`, `players_with_shoots_catches`, `games_with_unavailable_horizons`, `coverage_totals` |

player rows do not establish participation, position or historical team; those remain game facts. retain players without bio observations, with null fields and a reason distinguishing no matching row from incomplete/unavailable reference collections. do not silently exclude their games. `games_with_unavailable_rosters` counts all inventoried games without an available roster from a matching admitted game, including absent captures and rejected identities. the player denominator is only players seen in available admitted rosters; unavailable rosters and missing games prevent league-wide reference-completeness claims.

for each scalar count/seconds field in existing coverage, `coverage_totals` carries `{value, contributing_games, unavailable_games}`. sum only non-null values from matching reconstructed games; use null when no game contributes. unavailable games include all inventoried games lacking that quantity, including absent captures. keep the time/attempt/location groups separate. do not sum period-number arrays: report the number of inventoried games with unavailable expected horizons or fewer supported than expected horizons separately. retain unclassified-event counts. neither known-horizon seconds nor known-attempt counts are a full-season denominator while their contributing population is incomplete.

without an admitted inventory, `games`, `players`, `summary` and `missing_game_ids` are null, not empty successful populations. `issues` is always a list. `missing_game_ids` lists only absent captures; input errors and identity conflicts remain separate actionable rows. each reconstruction output retains its existing provenance and envelope version; no migrations or historical readers.

## operator content and acceptance

the content designer owns command summaries, fixture annotations and examples. good content names the population, distinguishes missing evidence from failed integrity, states consequences and points to the affected source. no raw payload dump, blanket “valid corpus,” “training-ready,” or single quality percentage. illustrative wording, with actual values substituted:

```text
corpus audit written: 2025–26 regular season
inventory: 1312 games; source counts agree
captures: 3 present; 1309 missing
game identity: 3 admitted; 0 unavailable; 0 conflicting; 0 input errors
supported 5v5 seconds: <sum> from <n> games; unavailable for <n>
player references: 120 roster ids seen; <n> birth dates; <n> shoots/catches
model eligibility: not assessed
output: <path>/corpus.json
```

show nonzero unresolved time, unresolved/unclassified attempts, unavailable horizons and reference gaps. report detailed findings in json rather than printing 1,309 missing ids. acquisition summaries retain http/body/failure distinctions. document an ordinary sequential loop over `missing_game_ids` invoking the existing game capture command into `<games-root>/<id>`; no manual transcription, automatic acquisition inside analysis or new batch platform.

acceptance, through temporary installed-command integration/live checks:

1. establish red, implement, establish green, refactor and rerun. capture the four references live with the production command into a new directory; admit that bounded season fixture with exact bytes/metadata and manually checked facts. all existing fixture bytes remain unchanged.
2. verify 1,312 unique game ids and three fixture identities, the 940/98 bio collections and all 120 roster references. retain the real null-handedness fact for player `8486169` and the current-team/historical-team counterexample. recheck locators and counts against the actual admitted retrieval; do not freeze scratch responses as unquestioned truth.
3. with python networking disabled and no drive, audit the three game fixtures against the full inventory. expect 1,309 missing captures, preserved known exposure, third-game 118 unresolved seconds and ambiguous event matches. per-game reconstruction must match the existing command's substantive outputs; only paths/implementation provenance may differ. verify grouped sums and contributing-game counts, including no-contributor nulls.
4. temporary labeled synthetic copies cover incomplete/duplicated/wrong-season inventory; mismatching summary count; missing/invalid/conflicting bio fields; absent/incomplete bios; wrong requested capture identity; a corrupt game alongside valid games; unavailable roster; inventory/game date/team mismatch; existing output and interrupted output. test successful incomplete audits separately from exit-1 integrity failures. do not require a large case matrix or lasting harness.
5. check selected event-summary/shift-report facts and roster-report availability for the admitted games, reusing pr2b's documented evidence where it already answers the question. no duplicate production parsers. check effect types, locked python installation and command help/exit behavior.
6. delete all temporary test code, scripts and test-only dependencies after verification. keep fixture bytes/facts and a concise verification record. retain production validation. historical admission and scientific model assessment remain outstanding; do not close their issues based on these examples.

## files, ownership and tradeoffs

| files | responsibility |
|---|---|
| `app/src/operator/capture.ts` | share faithful single-response capture; preserve existing five-source game behavior |
| `app/src/operator/capture-season.ts`, `capture-season-cli.ts`, `app/package.json` | fixed four-source season acquisition and invocation; no new dependency |
| `analysis/src/hockey_stats/captures.py` | shared receipt/integrity checks; explicit game/reference identity validation |
| `analysis/src/hockey_stats/references.py` | reference schemas, interpretation and located source issues |
| `analysis/src/hockey_stats/corpus.py` | deterministic inventory traversal, per-game composition, reference joins and scoped coverage totals |
| `analysis/src/hockey_stats/cli.py`, `pyproject.toml` | corpus entry point; reuse/extract existing implementation identity and output writing only where repeated |
| `README.md`, `fixtures/README.md`, `fixtures/references/20252026/`, `.gitattributes` | actual workflow, four admitted captures and checked facts; apply binary handling to the new source-body paths before admission |

separate acquisition, reference interpretation and corpus composition along these contracts. reuse game interpretation/reconstruction without changing their scientific rules. no duplicate hockey implementation in effect. no legacy code is imported.

four season requests replace calendar stitching and individual profile retrieval; bulk bios may omit roster-only players, which remain visible gaps. deterministic roots avoid a manifest/discovery system but require one explicitly chosen capture directory per id. full-season accounting makes small local examples visibly incomplete. per-game json reuses the existing contract and bounds memory but costs more disk than columnar storage; change format only when actual analytical access or measurements justify it. rerunning cheap audits is simpler than checkpointing them. none of these choices authorizes dropping blocked attempts, repairing ambiguous shifts or claiming fitted-model validity.
