# pr05a — private observed-results website

status: **full specification; ready for handoff, implementation and publication unassigned.** the user confirmed localhost-only access and the narrow effect-4 cutover. [the plan](../plan.md) owns assignment. this is the first vertical slice of [05](05-publication.md)/[06](06-website.md), independent of model admission and 04e execution.

## target and boundary

browse the **2025–26 regular season** on this mac: compact sortable league table/name search → player → included season results and listed-game evidence. show recorded on-ice attempts for/against, matched genuine-5v5 time, per-60 rates and visible gaps. browsing, direct links and reloads work with python, raw inputs, external network and the external drive unavailable; local loopback remains available.

one path: `validated native corpus → python observed quantities → finalized sqlite → effect reads → react views`. python owns hockey meaning and aggregation; effect owns application boundaries, reads and explicit file publication; react owns presentation. no browser analysis, source fetching, duplicated hockey formulas or model prerequisite.

non-goals: xg, ability/adjusted maps, individual scoring panels, player comparisons, percentiles, qualification filters, arbitrary dates, charts, headshots, public hosting, lan access, accounts, forecasts and a generic metric/card framework. missing model panels stay absent. this intermediate product does not fulfill the promised ability profile. richer observed maps/stats may follow separately.

## exact input and observed population

real acceptance uses the existing local corpus:

```text
/Users/nnandal/Documents/code/hockey-stats-local/03m-20261010/corpora/20252026/corpus.json
sha256: 1e4273d00107f8b7c04a49c70e4ac8a53153d46c493f2bf2bb2c4fd0e30ce034
```

its schema-2 manifest lists all 1,312 inventory games and ledger entries; that was checked during specification, not a new source/aggregation audit. explicit fixture corpora use `purpose:fixture`; their incomplete coverage cannot satisfy real-publication acceptance. no acquisition or five-season rerun. bind every consumed envelope and original source/producer identity. missing named inputs fail; no path discovery or substitute corpus.

reuse `corpus_inputs.load_corpus`, `validate_envelope`, native interpretation/reconstruction, and `artifacts` provenance primitives. validate newly consumed roster names, report timing/codes, player-exposure fields, interval bodies, reconstructed memberships and `shift_relation`: current envelope validation does not cover them all. positive intervals partition each supported period's `[0,end_seconds)` exactly, including explicit unresolved intervals; no gaps/overlap. unsupported horizons supply no invented duration. links agree with period, clock and full membership. malformed derived contracts fail; supported nulls retain their meaning.

the current attribution package consumes frozen row ledgers; its earlier source-population builder is no longer present. add the single current owner `observed.py`. historical 04a logic may inform review but is not imported or restored as a second pipeline. do not use chance eligibility, score chronology, fitted states or attribution sufficient statistics.

### matched counts and time

1. retain every inventory game in coverage. only admitted `reconstructed` envelopes supply metrics; absent/identity-mismatched games supply located unavailable rows, never invented player membership.
2. start from positive native elapsed intervals. genuine 5v5 requires five distinct skaters and one goalie per side, with disjoint opposing memberships and supported roster/team/role identities. every retained skater has exactly one `player_game` row. unavailable/ambiguous roster links remove affected counts/time together as `roster_identity_unresolved`; missing names do not. supported overtime is eligible; shootouts, penalty shots and known other strengths are excluded. coalesce contiguous intervals only within one period and identical FULL memberships, including goalies. retain valid zero-event time.
3. count exactly `goal|shot-on-goal|missed-shot|blocked-shot`. the exact `failed-shot-attempt` class is not an additional attempt. no coordinate, shot-type, bio, history or score-context requirement applies.
4. each count requires resolved shooting-team ownership, native corroborated event membership and one compatible positive coalesced segment through `interval_indices`/`shift_relation`. map native indices to coalesced segments; `before|after|both` can count once, never by a universal before-boundary rule. do not infer lineup, duration or ownership.
5. a potentially in-scope attempt that cannot be assigned removes ALL locally plausible containing/adjacent segments at its clock. unknown clock removes the named period; unknown timed period removes the game. known non-attempt/other-strength/shootout/penalty-shot evidence does not remove valid 5v5.
6. invalid api kind/code records can conceal attempts and receive the same located masks. account separately for unmatched report `GOAL|SHOT|MISS|BLOCK` rows: collect native `report_source_index` links, then mask unlinked rows at their reported clock. positively known shootouts/penalty shots remain excluded. no new matcher or synthetic count. conservatively do not infer report-only strength from `EV` or build another membership classifier; this may discard some extra valid time.
7. union masks before aggregation. remove affected counts AND time for both teams and every affected skater, including collateral otherwise valid attempts. retain each disposition/reason and reconcile unioned losses once. unknown membership/time is not known 5v5 time.

| source evidence | handling |
|---|---|
| absent api events or play-report collection (`null`, not a parsed empty array) | no matched game population; `required_source_unavailable` |
| `timed_goals` or `timed_shots` check with `status:mismatch` | whole-game matched exclusion, `count_accounting_conflict`; the aggregate cannot locate the discrepancy by time/strength |
| those checks `unavailable` | no extra exclusion alone; primary collections and located masks still apply. absent optional boxscore corroboration remains diagnostic |
| `player_toi` mismatch/native incomplete player exposure | preserve valid segments, retain that player's coverage limitation |
| `player_shift_count` mismatch | diagnostic; shift-row count is not elapsed time |
| unresolved shifts/horizons | retain native unknowns; use independently supported intervals where available |
| missing coordinates/types/bios/coach facts | no scalar exclusion |

reuse native timed-goal accounting, including its shootout handling. a matching source does not overrule a conflicting supplied total. no blanket rejection for any issue, and no 04a whole-game score-chronology gate: these results are unadjusted.

### identity, zeros and coverage

one player id survives trades. a player-game row requires a unique game roster id/team and skater position `C|L|R|D|F`; it means **listed**, not played or dressed. no DNP/scratch inference. season teams come from those game-time memberships, never a bio's `currentTeamAbbrev`. unknown whole-game or potentially skater roster associations contribute to a league-wide gap, not fabricated rows for every player.

display name is the latest chronological admitted roster observation containing BOTH first/last names, retaining its game/source-index locator. preserve source spelling; unavailable name stays null and renders `player <id>`. reported position uses the latest supported roster value with its own locator. game labels use game-time team ids/abbreviations; unknown abbreviation renders an explicitly identified team id. names/bios do not gate otherwise supported counts.

`included_seconds` is an exact nonnegative integer over the admitted set, never full official ice time. `known_excluded_seconds` counts native known-5v5 time removed by observed-population masks; it excludes unresolved-strength time. game coverage separately carries known unresolved-membership seconds and unavailable horizons. do not divide by an unknown full-5v5 denominator or display a coverage percentage.

| evidence | counts | rates | coverage |
|---|---|---|---|
| positive included time | nonnegative integers; zero is genuine | `3600*count/included_seconds` | `complete` or `partial` |
| zero included time, supported complete evidence of no 5v5 | zero | null, `no_5v5_exposure` | `complete` |
| zero included time with a relevant gap | null | null | `unavailable` |

`complete` means no known relevant coverage gap within the source-supported listed evidence, not independently verified physical truth. `partial` means usable time survives a gap. carry game-level potentially relevant gaps conservatively to listed players, plus native player-specific limitations. retain zero-time listed skaters in discovery.

season quantities reduce available game contributions before applying the same zero/null rule. season rates use summed counts/time, never an average of game rates. any listed unavailable/partial contribution prevents a complete season label. when any game has unassigned player associations, EVERY season summary carries `unassigned_player_games`: positive included time means `partial`; zero included time means `unavailable` with null counts/rates, even if known listed games establish zero. game rows retain their own statuses. arithmetic checks reconcile available contributions before this nullable season projection. disclose the global limitation beside each profile summary, with the located unassigned-game list in coverage details. all headline summaries say **included results**; a season title names the target period, not certified complete totals.

fixed presentation reasons:

```text
required_source_unavailable  count_accounting_conflict
event_evidence_unresolved   unpaired_report_attempt
elapsed_membership_unresolved  period_horizon_unavailable
player_toi_conflict  roster_identity_unresolved
unassigned_player_games  no_5v5_exposure
```

preserve detailed source codes/locators in the builder's receipt; these categories do not replace the source taxonomy. missingness is never silently converted to zero.

## publication schema and commands

python's standard `sqlite3` writes one new database, rollback journal `DELETE`, foreign keys enabled, one committed build. use `STRICT` tables, primary/foreign keys, nonnegative checks and explicit nullability. schema version is `1`, kind `observed_5v5`; no migrations, models, event warehouse, orm or generic metric table.

hockey ids are canonical decimal TEXT; season is eight digits, game ten digits. publication identity is a uuid. timestamps are utc iso strings; game dates are source calendar dates. numeric values must be finite; counts/seconds fit javascript safe integers. the following physical columns are required; `_json` fields have the explicitly named small object/array contract, not arbitrary blobs.

| table / key | fields |
|---|---|
| `publication`, `id=1` | `schema_version`, `kind`, `publication_id` (new uuid), `purpose:real|fixture`, `season`, `game_type=2`, `generated_at`, `source_requested_min/max` nullable, `undated_sources`, `population_version:matched_attempts_v1`, `corpus_sha256`, `producer_json`, `coverage_json` |
| `player`, `player_id` | `display_name` nullable, `reported_position`, `name_source_json` nullable, `position_source_json`; source objects identify game/roster index |
| `game`, `game_id` | `game_date`, `away_team_id`, `home_team_id`, nullable away/home abbreviations, `included_seconds`, `known_excluded_seconds`, `known_unresolved_seconds`, `horizon_unavailable` boolean-as-integer, nullable `away_attempts`, `home_attempts`, `coverage_status`, `reason_codes_json` |
| `player_game`, `(player_id,game_id)` | foreign keys, game-time `team_id`, shared metrics below |
| `player_season`, `player_id` | foreign key, `teams_json:[{id,abbreviation}]`, `listed_games`, `games_with_included_time`, `partial_games`, `unavailable_games`, shared metrics below |

shared metrics are explicit columns in both tables: `included_seconds`, `known_excluded_seconds`, nullable `attempts_for`, `attempts_against`, `for_per60`, `against_per60`, `coverage_status`, `reason_codes_json`. counts/rates obey the zero/null table. status is `complete|partial|unavailable`; code arrays are sorted unique fixed enums. `teams_json` is deduplicated by id; label each team from its latest admitted game observation. keys/order are deterministic, with ids as final tie-breakers.

`producer_json` reuses `implementation_identity()` fields `git_commit:string|null`, `git_dirty:boolean|null`, `python_version:string`, adding `sqlite_version:string` and `source_implementations:[{git_commit,git_dirty,python_version}]` with the same types. preserve distinct consumed native producer identities; exact consumed-file digests/locators remain in the receipt. name/position source objects are `{game_id,source_index}` with integer roster index. `coverage_json` contains integer `inventory_games`, `games_with_included_time`, `partial_games`, `unavailable_games`, `games_with_unassigned_player_associations`, `reason_game_counts:[{code,games}]` and `unassigned_games:[{game_id,date,away_team_id,home_team_id,reason_codes}]`. keep counts of games distinct from counts of issues. source dates describe retrieval, not a fabricated common observation instant.

python validates game-team membership and all reductions; effect only selects/joins/decodes published rows. reads may assemble nested view objects and choose home/away display labels, but must not derive counts, rates, eligibility or season aggregates. SQL checks and foreign keys support structure; they do not replace source reconciliation.

```text
hockey-stats-observed --corpus <corpus.json> --purpose real|fixture --out <new-directory>
```

add this entry point through the existing cli conventions (`Once`, explicit paths). no automatic source regeneration. write `observed.sqlite.incomplete`, close and independently read back/check. write `verification.json` with consumed file digests, source dispositions, aggregate identities, exact exclusions, the checked database digest and measured cost; only then rename to `observed.sqlite`. unexpected contract/i/o failures before this final rename produce no finalized candidate; ordinary known source gaps can produce a truthful partial publication. a real acceptance candidate needs some supported positive exposure, not a new coverage-percentage floor.

the database is self-contained for serving; the builder receipt/raw evidence may remain elsewhere. use `/Users/nnandal/Documents/code/hockey-stats-local/publication/` as the shared serving directory across worktrees, with `active.sqlite` and at most one `previous.sqlite`. these cheap serving artifacts do not constitute a fit mirror. candidate outputs use explicit separate paths; no automatic archive or cleanup service.

effect operator commands:

```text
npm run publication -- check --candidate <observed.sqlite>
npm run publication -- activate --candidate <observed.sqlite> --directory <serving-directory>
npm run publication -- restore --directory <serving-directory>
```

`check` opens an EXISTING file read-only, validates exact schema/kind, integrity/foreign keys and complete typed view rows; print purpose, season, publication id, coverage and path. it does not certify scientific admission. `activate` is explicit: operator stops serving first; copy candidate to a new `incoming.sqlite`, verify its digest and read contract, validate any existing active, then replace the previous file with the old active and incoming with active. first activation needs no previous. an invalid/incompatible active stops before rotation and requires manual repair; it must not overwrite the valid backup. failed copying cannot alter active/previous. an interrupted rename sequence is repaired manually from intact files. `restore` checks/copies previous before rotating, preserving a validated current active as the new previous; if active is absent, leave previous intact. no process detector, lock service, hot switching or backward reader. compatible code comes from git when needed. restart and reload after either action.

## application, api and browser contract

retain node `24.21.0`. confirmed cutover: `effect`, `@effect/platform-node`, `@effect/sql-sqlite-node` `4.0.5`, react/react-dom `19.3.1`, `react-router`, `@react-router/dev`, `@react-router/node` `8.4.0`, vite `8.3.4`; pin compatible supporting types and lockfile during implementation. migrate the five existing capture operator files to the same effect major, preserving command behavior/source bytes/receipts; remove obsolete `@effect/platform` imports/dependency. no dual-major compatibility layer or capture redesign.

official registry inspection supports these versions and node engines; install/build compatibility remains implementation verification. effect core is stable, but http/sql declarations remain unstable and this node version's `node:sqlite` is release-candidate. the engineering tradeoff is pinned, verified narrow boundaries plus a small capture migration, avoiding another major migration after the website grows. this is not a claim that every dependency api is stable.

one read-only sqlite connection scoped to the server lifetime, `readonly:true, disableWAL:true`, validated before listening. no create-on-missing, retries against another file, source-root lookup, python process or runtime writes. bind only `127.0.0.1`; default port 3000, explicit local port override. development uses the router/vite dev server, also bound to loopback, with `/api` proxy to effect; the built site uses one effect node process for api/assets. no public/lan host switch in this slice.

from `app/`, expose `npm run build`, `npm run serve -- --publication <active.sqlite> [--port <port>]`, and separate `npm run dev:api -- --publication <active.sqlite>` / `npm run dev:web` commands. development starts two terminals; no process supervisor. the production serve command requires its built assets; the development api command explicitly omits asset serving. the README records exact local urls and the proxy port.

shared effect schemas and `HttpApi` define exactly:

| endpoint | response |
|---|---|
| `GET /api/league` | `{publication, coverage, players:[PlayerSummary]}` |
| `GET /api/players/:playerId` | `{publication, coverage, player:PlayerSummary, games:[PlayerGame]}` |

`publication` exposes `publication_id`, `kind`, `purpose`, `season`, `generated_at`, `source_requested_min`, `source_requested_max`, `undated_sources`, `population_version`, `corpus_sha256` and exporter `git_commit`; no local filesystem paths. `coverage` is the published season coverage object. `PlayerSummary` contains `player_id`, `display_name`, `reported_position`, `teams`, `listed_games`, `games_with_included_time`, `partial_games`, `unavailable_games` and `metrics`. `PlayerGame` contains `game_id`, `game_date`, game-time `team`/`opponent` objects `{id,abbreviation}`, `venue:home|away` and `metrics`. `metrics` contains exactly the shared metric columns above, with decoded `reason_codes` instead of its sqlite JSON column name. all ids are strings; nullable values retain reasons. lists use stable ordering and full unrounded published numbers. no api-side search/rate calculation, pagination, projections, write endpoints or arbitrary SQL.

invalid player-id syntax → typed 400; valid absent id → typed 404; unexpected read failure → typed 500 with a short retryable presentation message and operator detail in stderr. unavailable metric data remains successful typed data, not an endpoint failure. incompatible/missing database fails startup. browser error bodies expose no paths or stacks. publication id is provenance, not a client pinning protocol.

api/html use `Cache-Control:no-store`; content-hashed assets may cache long term. api routing precedes static files and document fallback. unknown `/api/*` and missing assets return actual errors, never spa html. configure router framework mode with `ssr:false`, `appDirectory:src/web` and output under ignored `app/dist/`; its root shell still renders during build. document navigation loads the local shell and router; direct `/players/<id>` reload works. no remote fonts/assets/analytics. route `clientLoader` owns fetched data through the typed effect client, forwarding abort signals; no duplicate query cache/atom store. separate browser/server type-check boundaries so browser modules cannot import node/sqlite implementations.

browser routes are `/` and `/players/:playerId`. league URL owns `q`, `sort` and `dir`; invalid values normalize to defaults. supported sorts: `name|games|minutes|for60|against60`; `games` means `games_with_included_time`, default minutes descending, name/id ascending ties. suppress loader revalidation for changes confined to `q/sort/dir`; these use already loaded league rows without refetch. back navigation restores the meaningful selection. name search uses lowercase, unicode decomposition/removal of combining marks, whitespace-token AND substring matching; preserve original names for display. no search service.

## content and visual acceptance

the designer owns copy/formatting in the schemas above, reviewed before implementation and against real values afterward. use a restrained statistical sheet: pale background, dark readable text, one link/focus accent, tabular numerals and quiet table rules. one responsive stylesheet; system fonts; no design-system project or performance-grade colors.

| feature | required content and behavior |
|---|---|
| shared heading | `2025–26 · regular season · 5v5 recorded results`; concise definition: recorded while the player was on the ice, unadjusted for teammates/opponents/score/deployment |
| league table | player link, season team(s), reported position, games with included time, matched minutes, attempts for/60, attempts against/60, coverage. no rank number or implicit minimum-time cutoff |
| profile | identity → included minutes/counts/rates → coverage → listed-game evidence. one identity across trades; no ability placeholders |
| games | date ascending/id ties; player's team, `vs`/`at` opponent, matched minutes, for/against counts and coverage/reasons. roster listing is not an appearance claim |
| definitions | attempts include scored, saved, missed and blocked shots; matched means counts and time satisfy the same published population. inline explanation or native disclosure, not hover-only |
| coverage | label source-supported evidence `covered`, `partial` or `unavailable`; show known excluded minutes and relevant reasons. unassigned-game limitation sits beside the summary; its disclosure lists every located game by id/date/matchup/reasons. no unknown-denominator percentages |
| missing/zero | null renders an em dash with an accessible reason; observed zero renders `0`; no 5v5 time explains null rates. no complete-season claim from included subtotals |
| navigation/states | labeled search, result count, clear action, genuine links, selected sort direction; loading never shows a previous player's numbers under a new name. distinct empty search, missing player and failed-load states with retry/back |
| evidence disclosure | publication date/id, source retrieval interval, population meaning and concise coverage; detailed implementation paths remain in operator receipts |

format minutes/rates to one decimal and counts as integers; positive time below six seconds displays `<0.1` minutes with exact seconds accessible. sort by unrounded values with nulls last in both directions. UI time conversion/rounding is presentation only. use native table/caption/header markup, sortable-header buttons and `aria-sort`, visible keyboard focus, status text independent of color. mobile uses horizontal table scrolling with sticky player identity; retain time/coverage. verify keyboard use, a narrow viewport and 200% zoom. do not call raw rate ordering ability, creation/suppression ratings or distinguishable ranking.

## files and non-overlapping delivery

| owner / files | implementation boundary |
|---|---|
| python observed owner: `analysis/src/hockey_stats/observed.py`, narrow shared validation additions | matched population, masks, identity, coverage and game/season quantities; no sql/application code |
| python publication owner: `publication.py`, `cli.py`, `analysis/pyproject.toml` | explicit DDL/export/finalization/read-back; reuse authoritative observed results |
| app shared/server/operator: `app/src/shared/observed.ts`, `server/publication.ts`, `server/main.ts`, `operator/publication-cli.ts` | schemas, read-only queries, local http/assets, explicit check/activate/restore |
| browser/content: `app/src/web/` root/routes/client/styles; router/vite config, app scripts/types | typed route loading, table/search/profile/game views and content; no duplicate hockey calculation |
| integration/docs: lockfile, `README.md`, eventual `docs/research/observed-05a/verification.md` | exact commands, bounded fixture/real receipts and operator handoff; plan records completion |

share actual primitives; do not revive the removed study builder or create a metric registry. the effect cutover precedes app work; observed and app contracts can then be implemented independently against the same explicit fixture contract. each boundary gets an independent source/systems/content review before integration. cross-owner changes preserve one authoritative calculation.

## verification and completion

temporary end-to-end integration/live red → green → refactor → green, then independent adversarial review and deletion of temporary tests/controllers/test-only dependencies. retain source fixtures and the verification record; no new permanent harness is selected. preserve any newly demonstrated distinct broken game as its complete original available bundle under the existing fixture policy.

1. **source/aggregation:** independently checked real fixture boundaries exercise before/after/both once, zero-event time, unknown events/report-only attempts, collection absence, missing clocks/horizons, count conflicts, known out-of-scope events and collateral masks. synthetic mutations remain explicitly synthetic. missing locations/types/bios/names must not change counts. test trades, listed-only evidence, globally unassignable rosters, membership conservation and null/zero behavior.
2. **invariants:** every included attempt belongs to exactly one segment; masks remove counts/time together; player exposure sums to ten times physical admitted time; summed player for and against counts EACH equal five times admitted attempts. season counts/seconds equal game reductions; rates derive from those unrounded sums. verify source→sqlite→api values independently.
3. **application boundary:** incompatible/malformed/missing database rejection; source-supported nulls; exact route errors; unknown api/assets never html. verify capture byte/receipt/exit behavior through bounded controlled-http checks after the effect cutover. no new bulk network capture.
4. **usable browser:** real league search/sort → player → game evidence; direct route reload, back/search restoration, empty/error/loading states, missing data, keyboard/zoom/narrow layout. visually inspect actual rendered pages with real long names, traded players, zero and partial rows. no screenshot-only acceptance.
5. **operation:** build one real candidate from all 1,312 inventory games, report supported/excluded/unknown quantities and cost, without a completeness promise. explicitly check/activate it only when that execution/publication is assigned. verify browsing with raw roots/python/external network/external inputs unavailable; database bytes/mtime unchanged and no wal sidecar after reads. demonstrate activate/restore on small fixture copies, including a failed incoming copy or invalid active preserving the valid backup; no exhaustive crash simulator.

completion is a working private observed-results path with truthful coverage, preserved source evidence, independent reviews and documented commands. software success changes no model verdict. accepted costs: conservative exposure loss, source-selected subsets, a small dependency cutover, manual publication interruptions and possible later schema/view rework when supported ability arrives.

references: [sqlite strict tables](https://www.sqlite.org/stricttables.html), [read-only uri semantics](https://www.sqlite.org/uri.html), [effect 4 package](https://registry.npmjs.org/effect/4.0.5), [node sqlite](https://nodejs.org/dist/v24.21.0/docs/api/sqlite.html), [router spa mode](https://reactrouter.com/how-to/spa), [w3c sortable-table guidance](https://www.w3.org/WAI/ARIA/apg/patterns/table/examples/sortable-table/). public-product inspiration: [hockeyviz's separated descriptive panels](https://hockeyviz.com/howto/skaterCard), [money puck's table/profile navigation](https://moneypuck.com/stats.htm); neither supplies our eligibility or an ability claim.
