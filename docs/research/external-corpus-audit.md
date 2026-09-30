# external corpus audit

inspected 2026-09-29. purpose: decide whether the predecessor's data can supply pr03b. **decision: use fresh captures for 2023–24, 2024–25 and 2025–26**, confirmed by the user after these findings. retain the archive as historical evidence; no legacy reader or database enters the new analytical path.

## location and inspection boundary

the hockey data is on `/Volumes/Expansion`, an approximately 7.3-tib volume with 6.2 tib available at inspection. the current store is the `hockey` postgres database in container `hockey-stats-db-1`, volume `hockey-stats_hockey_pgdata`, inside colima profile `hockey`. its disk is `/Volumes/Expansion/colima/_lima/_disks/colima-hockey/datadisk`: 512 gib logical size, not a measure of allocated hockey data. postgres reports approximately 67 gb for the database.

the user explicitly authorized starting the stopped vm and database for read-only sql; startup itself writes runtime state. queries used `PGOPTIONS='-c default_transaction_read_only=on -c statement_timeout=60000'` and `BEGIN READ ONLY`. no legacy application, migrator, ingestion or model code was run. the container and vm were stopped after inspection. their old bind mount created empty `docker/initdb` directories in this checkout; those task-created directories were removed. no data was deleted or rewritten.

an older directory-format postgres backup is at `/Volumes/Expansion/backups/hockey_20260712.dump`: 84 files, 9,839,672,080 bytes, created july 12 by `pg_dump` 18.4 from postgres 16.13. its readable table-of-contents and selected gzip table records were inspected without restoring it. it has 20,011 game records; the newer database has 20,769. the old `Docker.raw` backups/rescue images and campaign logs were located but not exhaustively inspected. model metadata/artifact references are present; saved model files have not all been located or checked. this is not an archive-deletion inventory.

## observed database contents

20,769 distinct game ids span 2010-10-07 through 2026-06-14, including regular-season, playoff and some preseason records. each of the three proposed seasons has 1,312 regular-season ids. those counts agree with the directly queried official [2023–24](https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D20232024), [2024–25](https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D20242025) and [2025–26](https://api.nhle.com/stats/rest/en/season?cayenneExp=id%3D20252026) totals; equality of counts does not establish identical inventories or usable evidence.

`raw_snapshot` contains 172,666 rows. source captures range from july 5 to july 19, 2026. stored text and parse-error counts were checked across all endpoint groups: no null `raw_body_text`, no recorded parse errors. those are storage facts, not source-fidelity evidence.

| endpoint | snapshots | distinct scopes | implication |
|---|---:|---:|---|
| `PlayByPlay` | 20,956 | 20,769 | candidate retained source text; not admitted new-pipeline captures |
| `ShiftCharts` | 20,956 | 20,769 | candidate retained source text; pagination/completeness still require audit |
| `Boxscore` | 20,956 | 20,769 | every stored json body has the projected `players` list |
| `AwayRoster` / `HomeRoster`, each | 20,956 | 20,769 | projected rosters; synthetic entries are present |
| `HtmlRo` | 20,770 | 20,769 | playing-roster report, not per-event on-ice evidence |
| `HtmlTh` / `HtmlTv`, each | 572 | 571 | selected shift reports; not full corpus coverage |
| `PlayerLanding` | 1,311 | 1,311 | historical reference observations, not complete player coverage |
| `Schedule` | 2,749 | 1,726 | discovery records, not an admitted current season inventory |
| `SeasonReference` / `TeamReference`, each | 20,956 | 16 | projected, repeatedly landed reference collections |
| per-event `HtmlPl` / game summary | 0 | 0 | required new-pipeline reports must be captured |

regular-season play-by-play/shift/boxscore scope counts are 1,230 for 2010–11, 2011–12 and 2013–14 through 2016–17; 720 for 2012–13; 1,271 for 2017–18 and 2018–19; 1,082 for 2019–20; 868 for 2020–21; and 1,312 for each season from 2021–22 through 2025–26. these are database counts, not a new promise to analyze sixteen seasons.

## fidelity findings

- stored text hashes match recorded hashes for six endpoint families across games `2023020001`, `2024020001` and `2025020001`. the text in sampled boxscores is nevertheless a derived `{players: [{playerId, teamId, toi}, ...]}` object. a matching hash proves retained-text consistency, not originality.
- 4,969 away-roster and 5,040 home-roster snapshots contain the name `Dressed`. the [archived augmentation code](../../.reference/hockey-stats-legacy/packages/core/src/ingestion/source-adapter/live-projection.ts) manufactures missing names and `shootsCatches: "L"`. these counts identify affected snapshots, not unique players or an exact count of fabricated handedness fields.
- the [source adapter](../../.reference/hockey-stats-legacy/packages/core/src/ingestion/source-adapter/port.ts) applies boxscore, roster and reference projections before storage. play-by-play and shift fetches use its identity text path. historical text can be useful without being promoted to the new `http-client-body` byte/receipt contract; the database lacks the original request-url/header/byte receipt needed for that claim.
- the old per-event report landing rule requires `data-pl-row` in the html ([implementation](../../.reference/hockey-stats-legacy/packages/core/src/ingestion/source-adapter/legacy-html.ts)). no such reports were retained. this explains a plausible failure mechanism; the zero-row count is the direct evidence. the new pipeline's report parser and source-preserving capture replace that path.

representative locator: boxscore snapshot `019f38ff-c7b2-712a-97d6-452c836011c8`, `Game:2023020001`, captured `2026-07-06 19:55:18.657483+00`, has retained-text sha-256 `2707813c251495db118bf8da165aef9de9149eb0cd0639bf6f2f4ddd04a9eb74` and the projected `players` shape. inspect the actual body and adapter, not its `raw_snapshot` table name.

reproduce the essential checks with read-only queries over `raw_snapshot`: group `count(*)`, `count(distinct scope)`, `min/max(fetched_at)` by endpoint; compare `encode(sha256(convert_to(raw_body_text,'UTF8')),'hex')` with `content_hash` for the three sample scopes; count boxscores satisfying `json_body ? 'players'`; group regular game ids/scopes by their season-start prefix. the july backup's table-of-contents maps `game` to `4243.dat.gz` and `raw_snapshot` to `4250.dat.gz`; postgres copy escaping must be decoded before checking text hashes. no full backup checksum or complete historical source-to-model lineage audit was performed.

## chosen replacement and costs

fresh acquisition means approximately 19,680 game-source requests plus twelve season-reference requests for three 1,312-game seasons. final game ids come from newly admitted official inventories, not manufactured ranges or these old counts. all five game feeds are captured through the existing command; existing fixture bytes remain untouched.

the cost is another download and later retrieval dates. the benefit is one supported capture/reconstruction contract, complete source bodies, actual on-ice reports and no one-off importer with mixed provenance. old source text and expensive fits remain preserved, but are not scientific evidence for the new candidate merely because they exist. re-fetching historical games supports retrospective reanalysis, not an as-of-date forecast claim.

native effect/python commands can use `/Volumes/Expansion/hockey-stats/` directly. removable storage does not require colima. the legacy profile reserves 12 virtual cpus and is configured for 56 gib ram; it is unnecessary for the new file-based batch pipeline. detach the drive between runs; keep the eventual active/previous published sqlite databases locally as already agreed. deletion of old hockey data requires a separate, explicit scope after preservation needs are resolved.
