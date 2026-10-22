# 05g — historical observed profiles

full specification, 2026-10-21. [the plan](../plan.md) owns assignment. the user chose **2023–24 through 2025–26** and **history table only**. specification approval does not assign implementation, source preparation or activation. independent 04m research supplies no dependency or admitted model.

## target and limits

browse each of the three completed regular seasons through the existing league, player and same-season comparison pages. a player profile adds three linked history rows: five existing raw rates, seasonal identity, included minutes and coverage. selected-season cards, percentiles, distributions, maps, game evidence and the single-player png retain their current meanings.

one new immutable sqlite publication contains all three seasons. historical observations are data in the active publication, not archived publication revisions. preserve the existing 2025–26 facts exactly; add independently verified older observations. the website remains localhost-only and works without raw data, python or the external drive.

exclude career totals, pooled seasons, history percentiles, trajectory charts, fitted trends, aging/ability claims, cross-season player comparisons, date windows, new metrics, personal shot maps, deployment panels, global player search, acquisition, fitting, hosting and a publication manager. retain all three existing support populations and the 05f percentile convention. this does not expand the analytical target or admit any withheld model.

## source selection and preparation

metadata inspection found local raw/reference bundles for all three years, with 1,312 capture-directory names per year. this is readiness evidence, not current source-integrity or observed-publication acceptance.

| season | native input / required preparation |
|---|---|
| `20232024` | build a fresh corpus from the local originals using the existing native command below; freeze its resulting digest before publication |
| `20242025` | `/Users/nnandal/Documents/code/hockey-stats-local/03m-20261010/corpora/20242025/corpus.json`; sha256 `7e2ee518dd4dc961f0c7835572561f7463f431eac680487ab035ed84cebe21d3` |
| `20252026` | `/Users/nnandal/Documents/code/hockey-stats-local/03m-20261010/corpora/20252026/corpus.json`; sha256 `1e4273d00107f8b7c04a49c70e4ac8a53153d46c493f2bf2bb2c4fd0e30ce034` |

from `analysis/`, with the output parent created and a fresh destination:

```sh
.venv/bin/hockey-stats-corpus \
  --reference /Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930/references/20232024 \
  --games /Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930/captures \
  --out /Users/nnandal/Documents/code/hockey-stats-local/observed-05g-inputs-01/corpora/20232024
```

if occupied, choose another explicit fresh directory. do not use `fresh-20260930/derived`: it points to the external archive. the retained third local raw season is the existing exception, not permission for a growing mirror. no new feed or capture is necessary for the planned inputs. missing originals, contract failures and new distinct broken games require explicit evidence/fixtures under existing policy; never substitute a corrected download or pretend a missing season passed.

hard-cut the observed command to:

```sh
.venv/bin/hockey-stats-observed --selection /absolute/selection.json --out /absolute/fresh-candidate-directory
```

the selection is a small observed-publication contract, separate from research selections:

```ts
type ObservedSelection = {
  schema_version: 1;
  purpose: "real" | "fixture";
  corpora: { season: string; path: string; sha256: string }[];
}
```

require exactly these keys, absolute existing corpus paths, lowercase 64-hex digests, canonical consecutive-year season ids, ascending unique seasons and distinct resolved paths. `real` requires exactly the three declared seasons, the two pinned existing corpus identities and a frozen fresh 2023–24 identity; each full native inventory has 1,312 regular-season games. fixtures contain one to three explicitly fixture corpora from these seasons and never become real. no game-subset selector, implicit directory discovery or purpose override. remove `--corpus/--purpose` and `_REAL_CORPUS/_REAL_DIGEST`; no compatibility wrapper. retain the existing strict json, native corpus and consumed-source validation owners.

`build_publication(selection_path, output)` validates the selection; `aggregate(corpus_path, purpose, expected_season, expected_sha256)` checks its bound input and returns the existing single-season `ObservedResult`. remove the hardcoded single-season admission gate without weakening source validation. each aggregation owns its own identities, counts, masks, physical references and reductions. never concatenate three seasons before calculating quantities.

produce one season at a time, insert/read back its rows and write `seasons/<season>/verification.json`, then release its heavy results. one top-level `verification.json` binds selection bytes/digest, publication id, producer, database digest, each season receipt path/digest, compact coverage/checks and measured total cost. keep complete consumed-source receipts per season. finalize `observed.sqlite` only after every selected season and full database pass; failure leaves an incomplete candidate and does not touch active/previous files. retain existing output-outside-input and fresh-directory rules. no resume engine or cache layer.

## factual invariants

reuse `observed.py`, `scoring_credits.py` and `observed_spatial.py` unchanged in statistical meaning. on-ice attempts, personal scoring and locatable unblocked maps have separate matched counts/time, reasons and league coverage. retain raw versus derived provenance, unresolved source gaps, zero-time positive assists and null-rate semantics. source locations remain reported locations, not proven releases.

seasonal roster evidence owns each year's name, reported position and teams. use the existing within-season selection rule; do not overwrite old identity with latest bios or map relocated franchises into a modern label. a player id links seasons, but a player-season row owns its attributes. no published row means **no published player record**, not zero production, retirement or proof that the player did not play. a present row with unavailable support remains a present row with its existing reasons.

peers use only the selected year's player summaries, seasonal positions, family-specific minutes and declared cutoff. maps use only that year's physical included league reference. full season inventories and unassigned associations remain visible separately from player-linked games. different coverage between years is expected and disclosed; identical definitions do not make missingness ignorable.

## sqlite schema 4

hard-cut writer/reader to `PRAGMA user_version=4` and metadata `schema_version=4`. nine strict tables; retain existing column types, finite/null/rate checks, geometry and population versions except the changes below. move fields rather than retaining obsolete single-season copies.

| table | key / ownership |
|---|---|
| `publication` | singleton `id=1`; global schema/kind/purpose/publication id, `game_type=2`, generation time, four existing population/display versions and `producer_json` |
| `season` — new | `season` primary key; `corpus_sha256`, source-request min/max, undated count, `coverage_json`, `spatial_coverage_json`, `source_implementations_json` |
| `player` | primary key `(season,player_id)`; existing seasonal identity and source locators; season foreign key |
| `game` | primary key `(season,game_id)`; existing physical evidence; season foreign key; game id's season/type agrees with its parent |
| `player_game` | primary key `(season,player_id,game_id)`; foreign keys to the matching seasonal player and game |
| `player_season` | primary key `(season,player_id)`; foreign key to seasonal player; existing summary/teams and three supports |
| `spatial_cell` | primary key `(season,cell_id)`; season foreign key; existing geometry and this season's league cell facts |
| `player_game_spatial` | primary key `(season,player_id,game_id,cell_id)`; foreign keys to matching `player_game` and `spatial_cell` |
| `player_season_spatial` | primary key `(season,player_id,cell_id)`; foreign keys to matching `player_season` and `spatial_cell` |

every season key is nonnull. repeat the 668 valid cell geometries per season: negligible duplication avoids a separate geometry lifecycle and preserves the existing reference owner. ids remain the current ids, not renumbered across years. prefix existing game-oriented indexes with season, including sparse-map `(season,game_id)` access. [composite foreign keys](https://www.sqlite.org/foreignkeys.html#fk_composite) enforce same-season relationships; also validate game-id/year agreement and semantic conservation.

enable foreign keys when writing, retain rollback-journal finalization, integrity/read-back and strict structure checks. validate global structure once, then each season's scalar rows and bounded per-game/per-player spatial reductions. prove player/physical exposure and counts, game-to-season reductions, personal credit, sparse/dense map conservation, reasons, finite rates and reference normalization independently within each season. do not replace these with an all-season sum that permits compensating errors. require at least one supported physical interval in every real season; justified partial/unavailable games are retained.

serve through one read-only handle. every query/join/reduction names its season; global membership checks deliberately span seasons only to distinguish known players. avoid loading three dense spatial datasets or retaining three aggregation receipts in memory. no validation cache, orm, migration service or schema-3 fallback. measure actual build size/time/peak memory and server startup; repair demonstrated regressions without inventing a new performance platform.

## typed api and composition

retain the two endpoints, adding `season`:

| request | behavior |
|---|---|
| `GET /api/league?season=20242025` | selected-season full summary list; no map arrays |
| `GET /api/league?season=20242025&spatial=a,b` | same response plus existing one/two selected maps, with this season's league reference |
| `GET /api/players/:playerId?season=20242025` | selected-season league list, selected games/map and compact three-season player history |

omitted `season` means newest published season. explicit empty, repeated or malformed values return `InvalidSeasonSelection` (400); well-formed but unpublished returns `SeasonNotFound` (404). both errors carry ordered `available_seasons` for recovery links. preserve repeated values with `getAll` until validation; retain the typed error catalog through the client into `LoadError`. never silently replace an explicit season. existing player/spatial errors remain; update strict query parsing to accept only each endpoint's owned keys. invalid player syntax remains 400; globally unknown profile id remains 404.

reuse current scalar/spatial schemas. split the old mixed metadata object explicitly:

```ts
type SeasonEvidence = {
  season: Season;
  corpus_sha256: string;
  source_requested_min: string | null;
  source_requested_max: string | null;
  undated_sources: number;
  coverage: Coverage;
  spatial_coverage: SpatialCoverage;
}
type LeagueResponse = {
  publication: Publication; // global identity, definitions, generation time, git producer
  available_seasons: Season[]; // descending, unique, nonempty
  season: SeasonEvidence;
  players: PlayerSummary[]; // this season only
  spatial: SpatialSelection | null;
}
type PlayerResponse = LeagueResponse & {
  player_id: string;
  games: PlayerGame[];
  history: { season: SeasonEvidence; player: PlayerSummary | null }[];
}
```

`Publication` removes old season/source-cutoff/corpus fields; retain its other current wire fields. full source implementation identities stay in stored evidence/receipts. use existing timestamp/count/hash schemas, not unrestricted numbers/strings implied by this shorthand. `history` has exactly one row per available season, newest first, including absent records. selected history evidence/summary equals the selected response evidence/summary exactly. all nonnull history rows and game/map selections belong to `player_id`. history contains no other-season league lists, games or grids. no additional endpoint/fetch is needed.

known player absent from the selected season returns 200: selected league data and evidence, `games:[]`, its selected spatial entry with `data:null`, and nonempty history containing at least one real summary. present-but-unavailable follows existing support semantics. comparison remains season-scoped; an absent requested map id retains `data:null` and no fabricated summary. the comparison can link that id's profile/history without fetching a global directory.

the reader exposes global metadata/catalog and `league(season, spatialIds?)` / `player(season, playerId)`; season resolution belongs to the shared api boundary before those methods. handlers, typed client and operator `check` use the new contract together. all response content comes from the same handle. hard-cut existing consumers; do not reconstruct the former mixed metadata as a compatibility adapter.

## navigation and content

keep current paths; add `season` to their query. generated league/profile/comparison/history links write the actual selected season, including the newest. omitted direct links resolve once to the newest; canonicalize with idle history replacement after the coherent response, without a redundant fetch. never infer season from wall-clock time. api/browser errors show supported-season links with unrelated settings preserved.

one labeled native season selector serves all three routes from response metadata. a meaningful selection pushes one history entry, composes with `viewSearch(location,navigation.location)`, preserves committed discovery/peer/metric/map settings and selected player ids, and refetches. `season` must never enter the presentation-only `shouldRevalidate` allowlist. permit only the no-fetch canonicalization from omitted season to the same latest season already resolved in this response; actual changes always reload. retain absent team filters as visible filters with zero results and reset available; do not silently broaden them. search/pickers stay explicitly scoped to the selected season.

pending season changes show a loading state for the whole data view; no old card, header, map or export action appears under a new year. errors never leave stale-season facts as the result. superseded loads abort normally. preserve rapid query edits, existing return destinations, back/forward/reload and keyboard focus. selected-season profile→compare links keep season; back restores a genuinely recorded destination's season. without recorded return state, `back to players` and the site-home link use the selected season's league, not the newest default.

| surface | content designer's acceptance contract |
|---|---|
| league | current discovery/table, explicit selected season and its gap notice; filters never select another year's peers |
| profile | selected-season identity/card → three-row history → existing peer detail/maps/game evidence; all selected-season evidence stays coherent |
| history | newest first; season link, teams/reported position, three personal rates, two on-ice rates; grouped personal/on-ice included minutes and coverage. no ranks, percentiles, differences, arrows or trend labels |
| absent season | `no published player record for <season>`; history and available-season links remain; no selected-season card, maps, games or png. heading uses player id, with any name from history explicitly labeled by its source season |
| comparison | one shared season; preserve ids and explain each absent selection; suppress pair card, distributions and maps until both seasonal summaries exist. profile/history links remain available |
| png | existing single-player five-rate card for selected season; season in filename/image, selected cohort and selected-season source/coverage context; no history export |

history is a semantic table with two labeled metric groups and existing rate precision. use existing definitions and formatting. every absent season keeps its row and explicit message; do not fill numeric cells with zero. present rows with unavailable rates retain reasons. selected row uses text and `aria-current`, not color alone. partial coverage remains visible beside its family; details/known exclusions are accessible through the season link. keep each season's global unassigned-game gap visible in the row context. spatial minutes/coverage remain in that season's map, not another history denominator without a metric.

allow a labeled keyboard-scrollable history table at 320 css pixels and native 200% zoom; wrap identities and keep season links readable. selected-season percentiles still use 05f's exact family-specific cohort, tie convention and neutral direction. same units allow descriptive comparison, not adjustment for annual league environment, missingness or changing deployment. say `recorded results across published seasons`, not `career ability` or `improvement`.

png captures global publication, selected-season evidence, player and peer settings synchronously at click. an in-progress export retains that snapshot if navigation follows. preserve the current renderer and cleanup. update `Evidence`, `GlobalGap`, root headings, spatial copy and export consumers for explicit metadata ownership; no fact should inherit the newest year's context accidentally.

public references motivate navigation: [hockeyviz's career page](https://hockeyviz.com/player/matthau97) links seasonal detail, while [hockeystats' player page](https://hockeystats.com/players/jackson-lacombe) separates season tables and game logs. our inference is to connect compact history to complete seasonal evidence. their analytical claims, career aggregations and broader controls are not imported.

## owners and delivery boundaries

| boundary / files | assigned responsibility |
|---|---|
| source/publication: `analysis/src/hockey_stats/observed.py`, `publication.py`, `cli.py` | explicit selection, fresh third-season native preparation through existing `corpus.py`, independent aggregation, schema-4 writing/read-back and receipts. reuse source/spatial owners; no duplicate eligibility or new native format |
| transport: `app/src/shared/observed.ts`, `server/publication.ts`, `server/spatial-publication.ts`, `server/main.ts`, `operator/publication-cli.ts`, `web/client.ts` | exact schemas/errors, scoped validation/queries, history response, typed requests and season-aware operator checks |
| presentation: `app/src/web/` — `root.tsx`, `routes/league.tsx`, `routes/player.tsx`, `routes/compare.tsx`, `explorer.ts`, `player-picker.tsx`, `presentation.tsx`, `descriptive-card.tsx`, `spatial-views.tsx`, `styles.css` | one season-query/selector implementation, coherent navigation, history table, evidence/export metadata. reuse `observed-comparison.ts`; no second percentile/cohort implementation |
| handoff: `README.md`, `docs/research/observed-05g/verification.md` | actual commands, source selection/receipts, checks, costs, gaps, candidate and matching code identities; create during implementation |

agree boundary types before parallel work and give each file one owner. keep the small selection decoder with publication, history query with the reader, query handling with explorer and history table with the player route; extract only substantial or reused complexity. a content designer defines/reviews each surface above. independent source/statistical, systems and rendered-content reviewers challenge each boundary and the integrated result. no unrelated cleanup, scientific migration, dependency upgrade or generic season framework.

## acceptance and handoff

temporary integration/live red → green → refactor → green checks precede independent review and deletion of tests/controllers/test-only dependencies. retain checked fixtures/facts and receipts. this slice selects no permanent suite; [07](07-lightweight-testing.md) owns that separate policy. use isolated candidate/output/build/listener; preserve the active site/build, active/previous databases, raw originals, expensive fits and independent 04m work.

1. **source and preservation:** verify all 3,936 inventory entries through existing native/observed checks, per-season consumed source identities and independently reconciled supports/counts. each inventory includes unavailable games explicitly. check distinct older-season gaps instead of assuming 2025 coverage. independently compare every 2025 identity, game/summary value, coverage/reason and map/reference value against active schema 3; only publication/schema/producer-generation metadata may differ. unexplained changes fail acceptance; record any genuine newly demonstrated source defect and resolve its scope before changing established meanings. preserve new distinct complete raw fixtures under project policy.
2. **storage isolation:** real and deliberately unequal multi-season fixture outputs read back exactly. fixture cases reuse ids across seasons with different names/positions/teams/rates, include absent and unavailable records, changed league references and unequal support populations. reject wrong digests/seasons/purpose, duplicates, malformed metadata, cross-season relationships, missing season rows, game-id mismatch and corrupted reductions. a failed season never finalizes a partial publication. schema-3 files fail clearly under the new reader. measure size, build/startup time and peak memory.
3. **api arithmetic/coherence:** default and each explicit season, profile history, selected spatial requests and typed errors. independently enumerate selected-year peers/percentiles and map references; history equals its linked season response. no other-year games/grids or three league lists leak into a profile. verify unknown-global versus known-absent versus present-unavailable distinctions; all three coverage contexts remain correctly labeled. real candidate operator check passes.
4. **browser/content:** league → historical profile → same-season comparison → back; direct historical links without return state, site home, history links, all three seasons, reload/back/forward, invalid/duplicate/unpublished season, absent selections and retained filters. test delayed/aborted loads and rapid season/picker/peer/metric/map edits; no cross-season stale values or extra presentation-only/canonicalization requests. render real plus boundary-case history tables, keyboard navigation, 320px reflow and native 200% zoom. open actual pngs for all three years and a navigation-during-export case; image/name/rates/cohorts/source context equal the click snapshot.
5. **cutover and detached use:** pinned typecheck/build; browse every season/history/comparison/map and export with no raw/python/hdd/network reads. exercise schema-3↔4 code-paired stop/copy/restart rollback only in disposable publication directories with isolated builds. current operator rotation validates active and incoming with one reader, so cross-version activation needs the existing manual procedure, not a compatibility reader. preserve one previous database; reconstruct matching old code from git. actual activation remains separately assigned.

the receipt separates real/synthetic/manual evidence, original-source validation, preserved current-season equality and source limitations; records final independent reviews, actual costs, candidate hash and matching code; and identifies concrete unresolved issues under `docs/issues/`. deleting temporary checks follows final green, not unresolved acceptance.

material costs: third-season preparation and all-season verification; a larger rebuilt database; manual incompatible-schema rollback; season-scoped discovery instead of global search; no percentile/trend summary across years; visible absence and differing coverage; historical raw-rate changes can reflect deployment or league environment. the benefit is a complete, inspectable historical observed capability without extending the research claim.
