# pr2 — interpret captured game records

status: specification, 2026-09-29; implementation not authorized. pr1 is merged. the user chose local captures now, the external corpus later, and separate prs for source interpretation and on-ice reconstruction. [brief](../brief.md) and [architecture](../architecture.md) remain authoritative.

## target and boundary

one direct python command reads one explicitly selected pr1 capture directory offline and writes an attributed game document. it establishes supported identities, source records, clocks and reconciliations. it preserves conflicting observations and missing values. capture success, parsing success and hockey validity remain different claims.

this is interpretation slice 02a. 02b owns on-ice reconstruction, genuine 5v5 exposure, event-to-interval assignment and the analytical coordinate frame. chance valuation owns imputed shooting origins. no fitting, historical-corpus importer, bulk acquisition, html parser, website, database, orchestration or legacy compatibility in pr2.

support the current captured json feed shapes for completed nhl regular-season games: `gameType = 2`, `gameState = "OFF"`. other types/states are explicitly unsupported here. support is not hardcoded to the two fixture ids or their player lists. untouched upstream fields remain accessible in the captures; do not copy an unrestricted source `details` object into a purported canonical schema.

## invocation and ownership

create one installable package under `analysis/`, using ordinary cpython 3.14 and uv. pin the available 3.14 patch and compatible `uv_build` version during implementation; commit `.python-version`, `pyproject.toml` and `uv.lock`. no runtime dependencies are needed. use stdlib json, pathlib, hashlib, argparse and explicit typed records; no generic decoder framework or generated cross-language schemas.

after environment preparation, from `analysis/`:

```sh
.venv/bin/hockey-stats-interpret --capture ../fixtures/captures/2025020001 --out ../var/interpreted/2025020001.json
```

both options occur exactly once; reject unknown/repeated options and disable argparse option abbreviation. `--help` exits `0`; invalid argument syntax exits `2` using argparse's normal convention. input must be an existing directory. output must be new, outside that capture directory, with an existing parent. reject an existing output before reading source bodies. do not discover games, fetch sources, follow alternate feeds or implicitly select fixtures.

`read_capture(directory, source)` owns the pr1 file contract and returns checked bytes/metadata or a named unavailable-source result. `interpret_game(directory)` owns the hockey meanings and returns the document, including any gaps. a thin cli adds invocation/provenance, writes the document and reports its outcome. no effect wrapper or typescript hockey calculations.

## capture admission and failures

read the four fixed source directories. consume [pr1 metadata](01-capture.md#files-and-record-schema) directly: `schemaVersion: 1`, requested game id, source, request identity/time, capture state/status, body path/representation/length/digest and failure. use `body.bin`, never a metadata-provided arbitrary filename. verify length and sha-256 before interpreting bytes. they are already decompressed; a retained gzip header must not trigger another decompression.

- absent `capture.json`, recorded request failures and complete non-2xx bodies are unavailable sources with their actual reasons. ignore a stray body without metadata. never parse an error body as hockey data.
- present malformed metadata, an unsupported metadata version, mismatched source identity, contradictory requested game ids, a missing body promised by a captured record, or digest/length mismatch are input-contract errors: exit `1`, no output document. report the affected path and repair action. judge the files present; do not infer whether interruption or corruption caused the defect.
- invalid source json or unsupported game identity/state makes that source unavailable. reject non-finite json numbers and duplicate object keys; ignore unselected fields after parsing.
- at least one valid capture record must establish the requested game id; otherwise exit `1` without a document. derive it from coherent metadata, not directory names. json body ids must match it; all shift rows must identify it. admitted play-by-play and boxscore must agree on season, game type, date and away/home team ids. a conflict in those shared identities is an error; do not choose a winner.
- a body identifying another game is unavailable, never merged. shifts have no single body-level game id: any row with a missing/invalid/different game id makes that source unavailable, with the offending row located. other admitted sources remain usable. after identity admission, malformed selected collections/fields produce explicit issues and unavailable quantities, not invented empty arrays or defaults.
- the html report is integrity-checked and identified as `reference_only`; its hockey content remains manually inspected evidence. its absence does not erase json facts.

the core sources are play-by-play and boxscore. after successful writing, exit `0` exactly when at least one passes the declared game identity/type/state checks. collection gaps or reconciliation mismatches remain explicit and do not change that exit rule. if neither passes but the requested id is known, write a diagnostic with `game: null` and exit `1`. input-contract and filesystem errors exit `1` without a successful document. unexpected programming failures are errors, never converted into tolerated missing data.

construct the cheap result in memory; serialize finite json and create the output exclusively. no overwrite, temporary-output protocol, fsync, cache or checkpoints. interrupted json is unusable and removable manually; saved input captures remain unchanged.

## document contract

one `schema_version: 1` object. names below are exact output identifiers. game ids are ten-digit strings and `season` an eight-digit string; other ids are positive source integers. seconds are nonnegative integers; coordinates are finite numbers. invalid selected values become `null` plus a located issue; absent optional values remain `null` without invented defaults. no boolean-as-integer coercion or string-to-number guessing. source pointers preserve absent versus explicit-null evidence. game teams must be distinct; player/owner team assignments must refer to them or remain unresolved with an issue.

| field | contents |
|---|---|
| `requested_game_id` | coherent requested id |
| `interpretation` | `git_commit`, `git_dirty`, `python_version`; dirty means changes under `analysis/`, including untracked source files; unavailable git identity is null. dirty/unidentified results are development outputs, not reproducible solely from the commit; no source/build archives |
| `inputs` | four entries: `source`, absolute `capture_path`, `requested_at`, `http_status`, `body_sha256`, `status` (`parsed`, `unavailable`, `reference_only`), `reason`; unknown metadata values remain null |
| `game` | agreed `game_id`, `season`, `game_type`, `game_date`, `away_team_id`, `home_team_id`; null only in a diagnostic with no usable core source |
| `reported_results` | one observation per admitted core source: `source`, `away_score`, `home_score`, `away_sog`, `home_sog`, `last_period_type`; preserve both sources' values |
| `roster_records` | `source_index`, `player_id`, `team_id`, `first_name`, `last_name`, `reported_position` from `rosterSpots`; names use each source `default` string, position uses `positionCode`; null when collection unavailable |
| `boxscore_players` | `source_path`, `player_id`, `team_id`, `name`, `reported_position`, reported `toi`, parsed `toi_seconds`, `shift_count`, `goals`, `assists`, `sog`, `blocked_shots`; mappings below; null when collection unavailable |
| `events` | event rows below, or null when collection unavailable |
| `shift_records` | shift-feed rows below, or null when collection unavailable |
| `checks` | named checks below: `name`, optional `source`/`team_id`/`player_id`, `status` (`match`, `mismatch`, `unavailable`), `observed`, `expected`, `reason`; no overall validity score |
| `issues` | `{ code, source, path, message }`; `path` is a json pointer or capture path; code identifies a specific defect, message its consequence |
| `uncomputed` | array of four strings: `on_ice_membership`, `genuine_5v5_exposure`, `attacking_coordinates`, `shooting_origins` |

flatten boxscore `playerByGameStats` in away/home order, then forwards/defense/goalies, retaining each array's order and json pointer. `team_id` comes from that side's admitted team identity; `name` from `name.default`, `reported_position` from `position`, `shift_count` from `shifts`, `blocked_shots` from `blockedShots`; remaining names match their source fields. preserve nulls where the field is absent, including a goalie's shift count. keep source-specific player observations separate rather than reconcile differently formatted names by guessing.

every row retains its source array index or exact source json pointer. together with `inputs`, this identifies its body digest. keep one output row per source item, in source order, even when malformed: retain its locator, null unsupported fields and explain the defect. an unavailable collection is null; a parsed empty collection is `[]`. do not deduplicate records by player, event or shift id; report repeated ids. source-listed identity is not proof of participation, and no handedness is inferred.

event fields:

| group | fields / interpretation |
|---|---|
| identity/order | `source_index`, `event_id`, `sort_order`, `type_code`, `type_key`; retain all three ordering/identity values; do not sort by event id |
| period/time | `period_number`, reported `period_type`, reported `time_in_period`/`time_remaining`, `elapsed_seconds`, `timed_period` |
| context | reported `situation_code`, `home_team_defending_side`, `zone_code`, `owner_team_id` |
| location | `reported_x`, `reported_y`; recorded event coordinates, not guaranteed shooting origins; no clipping, flipping, side inference or imputation |
| participants | `roles`, the explicit mapping below; `shooting_team_id` resolved from the shooter's/scorer's unique roster team, never a blind reversal of owner |
| other selected facts | `shot_type`, `reason`, `penalty_type`, `penalty_duration_minutes`, `away_score`, `home_score` from `details.shotType`, `reason`, penalty-only `typeCode`/`duration`, `awayScore`/`homeScore`; no manpower inference from minutes |

`roles` maps these keys to the corresponding `details` fields: `shooter` → `shootingPlayerId`, `scorer` → `scoringPlayerId`, `blocker` → `blockingPlayerId`, `goalie` → `goalieInNetId`, `assist1/assist2` → `assist1PlayerId/assist2PlayerId`, `faceoff_winner/faceoff_loser` → `winningPlayerId/losingPlayerId`, `hitter/hit_player` → `hittingPlayerId/hitteePlayerId`, `penalty_committed_by/penalty_drawn_by/penalty_served_by` → `committedByPlayerId/drawnByPlayerId/servedByPlayerId`. omit absent role keys; retain explicit source nulls. invalid ids become null with issues. preserve unresolved participant ids without inventing roster entries. missing `details` is legitimate for period markers.

the four attempt kinds are `goal`, `shot-on-goal`, `missed-shot`, `blocked-shot`. for goals resolve shooting team from `scorer`; for the other three, from `shooter`, including shootout attempts. other event kinds have no derived shooting team. missing/ambiguous roster membership leaves it null. retain owner independently and report disagreement. blocker and shooter may be teammates. `zone_code` remains source-relative: its meaning is not uniformly relative to event owner. event score fields are reported snapshots, not pre-event context: timed goal snapshots include that goal; these fixtures' shootout goal snapshots remain tied.

timed periods are `REG` 1–3 (1,200 seconds) and `OT` 4 (300 seconds). `SO` 5 is untimed: retain its recorded clock, set `timed_period: false` and `elapsed_seconds: null`. unknown/inconsistent period descriptors make these derived fields unavailable. parse minutes/seconds strictly, requiring seconds 0–59. elapsed time must fit its period; when remaining time is supplied, the two must sum to the period length. missing remaining time alone does not erase valid elapsed time. contradictory clocks retain their strings but yield null elapsed seconds and a located issue. never manufacture absolute game time for shootouts.

shift fields: `source_index`, `record_id`, `type_code`, `kind` (`shift` for 517, otherwise `other`), `player_id`, `team_id`, `period_number`, `shift_number`, reported `start_time`, `end_time`, `duration`, `event_number`, `event_description`; normalized `start_seconds`, `end_seconds`, `duration_seconds`. normalize only type-517 rows with supported timed periods and `0 <= start <= end <= period length`, whose duration equals end minus start. otherwise leave normalized fields null and explain invalid interval tuples; non-shift rows remain unnormalized. retain zero-length source intervals if coherent; do not merge, truncate or repair shifts. this is clock interpretation, not on-ice reconstruction.

## checks and content

perform these named checks; unavailable operands are null and `reason` identifies the missing support:

| `name` / identity | `observed` | `expected` / rule |
|---|---|---|
| `shift_collection` | received array length | advertised `total`; mismatch prevents complete-collection claims |
| `timed_goals`, per core source | `{ away, home }` timed goal-record counts by owner | that source's `{ away, home }` final score; ordinary finals match directly; shootouts require tied timed goals and exactly one extra final-score goal for the winner |
| `timed_shots`, per core source/team | timed `shot-on-goal` plus `goal` count by owner | reported team shots |
| `player_toi`, per boxscore player | sum of that player's valid shift durations, seconds | reported boxscore toi, parsed to seconds |
| `player_shift_count`, per boxscore player | count of that player's type-517 rows | supplied boxscore shift count |

goal/shot counts need classifiable event kinds, periods and owners across the relevant collection. absent coordinates or roster membership alone do not invalidate owner-based counts; an unclassifiable row cannot silently disappear from a complete total. shootout records remain separate from timed counts. preserve incomplete shift collections for inspection, but make both per-player checks unavailable. within a complete collection, a known shift's invalid duration invalidates its player's duration sum, not its identifiable record count. ambiguous/duplicate shift identities invalidate affected players' checks; if the player cannot be identified, all such checks are unavailable. missing boxscore shift count is unavailable, not zero.

mismatches retain both values and identify the affected claim; never edit rows to force agreement. reported finals are not rewritten from event counts. duration/record-count agreement is source reconciliation, not validated on-ice exposure.

the content designer owns concise, factual command output and issue explanations. each problem names source, locator, failed condition and lost capability. no “valid game,” generic quality percentage, raw payload dump or default traceback for expected input failures. the cli may count stored rows and their normalized `kind` for presentation; scoring comes from recorded checks. when sources disagree, name both rather than print a consensus. example with agreeing sources:

```text
interpreted game 2025020006 from local captures
play-by-play: 374 source records
scoring: 3–3 timed-play goals; 4–3 reported final after shootout
shifts: 826 records match advertised total; 9 non-shift records
5v5 exposure: not reconstructed in this slice
output: <path>
```

for a gap: `shifts incomplete: 5 records received; source advertises 856; duration reconciliation unavailable`. for no usable core source: `game interpretation unavailable; diagnostic saved to <path>`. show all failed/unavailable source-level checks concisely; field-level details remain in the document.

## implementation boundaries and acceptance

| files | responsibility |
|---|---|
| `analysis/pyproject.toml`, `analysis/uv.lock`, `analysis/.python-version`, `analysis/src/hockey_stats/__init__.py` | one installable python package and console entry point |
| `analysis/src/hockey_stats/captures.py` | pr1 metadata, body integrity and source availability |
| `analysis/src/hockey_stats/interpret.py` | explicit records, source interpretation and named reconciliations |
| `analysis/src/hockey_stats/cli.py` | arguments, implementation identity, output write, concise content and exits |
| `.gitignore`, root `README.md`, `fixtures/README.md` | ignore the python environment/build outputs; setup/invocation; retain new independently inspected fixture facts |

reuse the pr1 artifact contract and python primitives. no existing python implementation exists to consolidate; leave the effect capture code alone. extract helpers only for actual repeated semantics such as clock parsing. do not add a schema registry, provider interface, correction framework or operator platform.

temporary end-to-end checks invoke the installed command using real files and inspect its complete output:

- both admitted games work offline, without hdd or network, and leave every capture byte unchanged. expected plays: 361/374; rosters: 40 each; shifts: 851/817 type-517 plus 5/9 other records. all supplied boxscore toi/shift counts reconcile; unused roster goalies remain distinct from players with shifts.
- verify selected annotations in [the corpus](../../fixtures/README.md): timed/final scores and shots, event 101's blocked ownership/location, event ids 52/51 with source sort order, null marker durations and all 20 shootout-period records retaining untimed status.
- retain all 77 blocks, including 11 `teammate-blocked` records; no ownership reversal, opposing-blocker requirement or shooting-origin claim. compare the derived shooting team with independently inspected roster associations.
- synthetic temporary copies exercise one missing optional field, a malformed clock/interval, unknown fields, a failed/non-2xx capture, malformed body json, incomplete shift collection, identity conflict, body-integrity mismatch and existing output. recompute test-copy digests when testing interpretation rather than integrity; label these copies synthetic. verify useful partial output versus errors exactly as above.
- establish red, implement, establish green, refactor and rerun. smoke-check package installation/entry point. live acquisition is unnecessary for this offline consumer: the real fixtures are the live-captured integration inputs; never claim another live pass occurred.
- delete all temporary test code, test-only scripts/dependencies and generated outputs afterward. retain useful inspected facts in fixture annotations, not implementation-generated snapshots as their own oracle. no lasting harness before slice 07. summarize verification in the pr description.

tradeoffs: one fully loaded json document is simple to inspect and exchange for one game; it is verbose and not a bulk analytical storage decision. sqlite remains the website publication format. retaining source-specific records means disagreements stay visible. stdlib parsing requires a few explicit field/clock checks; it avoids a general validation dependency. exposure and normalized spatial analysis arrive in 02b; a compact, reviewable scientific boundary is the benefit.

evidence: the admitted captured bodies and their annotated locators are primary for these rules. [python json](https://docs.python.org/3/library/json.html) documents strictness hooks; [uv package layout](https://docs.astral.sh/uv/concepts/projects/layout/) and [build backend](https://docs.astral.sh/uv/configuration/build-backend/) support the selected package structure. archived implementations are investigation references, not source authority or code to import.
