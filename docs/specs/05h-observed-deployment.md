# 05h — observed deployment context

full specification, 2026-10-21. [the plan](../plan.md) owns assignment. the user selected **shared minutes plus share of the selected player's included time**. specification approval does not assign implementation, acquisition or activation.

## target, prerequisites and limits

add two selected player-season tables: **teammates shared with** and **opponents faced**. show who shared the player's included 5v5 time, ordered by overlap, with same-season profile links. reuse all three published seasons, identities, coverage and navigation. this is recorded deployment context, not teammate quality, chemistry or an explanation of isolated ability.

implementation starts from [02d's](02d-source-exposure-consistency.md) reviewed observed-support implementation, frozen selected-corpus manifest and checked schema-5 candidate. bind that candidate/receipt and its input identities before rebuilding. do not substitute the older 05g population or duplicate 02d's recovery work. explicitly retained source gaps are valid. 02d's separate research-ledger audit and ongoing 04m do not supply a product dependency; report their status honestly without making an attribution result a prerequisite.

build one schema-6 candidate with identical pre-existing hockey facts and added deployment facts. localhost serving remains independent of raw data, python and the external drive. preserve the running site, active/previous databases, 02d baseline and research work. activation remains separately assigned.

exclude pair-game drill-down, team-tenure/date splits, together/apart outcomes, strength states beyond the existing 5v5 population, goalie relationships, quality ratings, line inference, maps, percentile ranks, filters/search/pagination within these tables, new endpoints, comparison/history/png expansion, acquisition and fitting. no fourth support denominator or eligibility threshold.

## factual contract

use **every final retained on-ice segment** from `observe_game`, including zero-event time. 02d's maximal constant-lineup segments and final on-ice mask are authoritative. personal-credit or spatial exclusions must not narrow deployment. do not reconstruct overlap from attempts, season team lists, reported total ice time or a second source sweep.

for a retained segment of duration `d`, with five away and five home skaters:

- add `d` to each unordered within-team pair: ten per side, twenty total;
- add `d` to each away/home pair: twenty-five total;
- exclude goalies and self; add nothing for masked/unresolved segments.

a pair is keyed by relation plus two player ids. canonicalize ids in numeric order, using `(digit length, binary digit string)` wherever ids are stored as strings; no floating-point id conversion. relation is `teammate|opponent`, determined by that segment's actual sides. accumulate repeated contributions across the selected season, including team changes. a pair can have both relations after a trade. do not split by current team or merge seasons.

retain exact positive integer `shared_seconds`. no zero rows, rounded minutes, percentages or reciprocal duplicates are stored. a missing pair means no overlap in **included evidence**, not proof that the players never shared the ice.

for physical included seconds `D`, selected-player seconds `T_i`, and pair overlap `S_ij`:

```text
sum(canonical teammate seconds) = 20 D
sum(canonical opponent seconds) = 25 D
sum(teammate seconds incident to i) = 4 T_i
sum(opponent seconds incident to i) = 5 T_i
S_ij,teammate + S_ij,opponent <= min(T_i, T_j)
share_ij = 100 * S_ij / T_i
```

check these identities per game and season. shared seconds are reciprocal; shares need not be. full unrounded shares sum to 400% and 500%, because each second has multiple counterparts. these are overlapping time shares, never a partition, percentile or reliability measure.

## analytical and storage ownership

keep the small pair counter in `analysis/src/hockey_stats/observed.py` beside its existing retained-segment accounting. use within-team combinations and the cross-team product once per segment. no graph framework or separate segment parser.

add this typed fact to each existing game receipt's `deployment_pairs`, then reduce the same rows to `ObservedResult.player_season_pairs`:

```text
PairSeconds = {
  player_a: canonical hockey id,
  relation: teammate | opponent,
  player_b: canonical hockey id,
  shared_seconds: positive safe integer
}
```

`player_a` is numerically smaller. the parent receipt owns game identity and binds native segment indices/masks; unavailable games have an empty pair list. preserve 02d's six-value `observe_game` return contract. source calculations have one owner; publication and browser never recompute memberships. season pairs equal exact per-game reductions, with identities referencing that season's skaters.

per-game pairs stay in the existing verification receipts; only seasonal pairs enter sqlite. this increases receipt size but preserves an inspectable game→season trail without another artifact lifecycle or serving table. process one season at a time and measure added bytes/time/memory; do not materialize a dense league-by-league matrix.

hard-cut `publication.py` and the effect reader to `PRAGMA user_version=6` and publication `schema_version=6`. retain 02d's three `v2` population identities and `rect5_gaussian10_v1`. add one strict table:

```sql
CREATE TABLE player_season_pair (
    season TEXT NOT NULL,
    player_a TEXT NOT NULL,
    relation TEXT NOT NULL CHECK(relation IN ('teammate','opponent')),
    player_b TEXT NOT NULL,
    shared_seconds INTEGER NOT NULL
      CHECK(shared_seconds BETWEEN 1 AND 9007199254740991),
    PRIMARY KEY(season,player_a,relation,player_b),
    FOREIGN KEY(season,player_a) REFERENCES player_season(season,player_id),
    FOREIGN KEY(season,player_b) REFERENCES player_season(season,player_id),
    CHECK(length(player_a)<length(player_b) OR
      (length(player_a)=length(player_b) AND player_a COLLATE BINARY < player_b))
) STRICT;
CREATE INDEX player_season_pair_b
    ON player_season_pair(season,player_b,relation,player_a);
```

existing foreign keys supply canonical season/player identities. update the exact table/column/key catalog: ten strict tables. producer insertion/read-back, `_check_season` and server startup validate positive integers, canonical distinct endpoints, both identities, combined pair bounds and every player's 4T/5T totals, including players with no rows. season/global pair totals alone cannot establish correct identities; source acceptance below is also required.

no compatibility reader, migration, extra metadata version family or automatic rebuild. use the existing `hockey-stats-observed --selection <02d-selected-selection.json> --out <fresh-directory>`. retain its source/receipt hashes, independent read-back and incomplete-output behavior. the final receipt binds the schema-5 baseline and exact preservation comparison. do not rerun source capture or native corpus preparation.

## typed api and composition

extend only `PlayerResponse` from `GET /api/players/:playerId?season=...`:

```ts
type DeploymentPeer = {
  player_id: HockeyId;
  shared_seconds: Count; // strictly positive
};
type Deployment = {
  teammates: DeploymentPeer[];
  opponents: DeploymentPeer[];
};
// existing fields remain; new field:
deployment: Deployment | null;
```

reuse selected-season names/positions from the response's existing `players` list; no duplicated identity fields or extra fetch. ordinary league and comparison responses carry no pair lists. profile history remains compact and unchanged. preserve current query parsing, season default/errors, player absence and error catalog.

read the canonical table with two indexed endpoint branches combined by `UNION ALL`: one where selected id is `player_a`, one where it is `player_b`. normalize to the other id and relation. return **all positive counterparts**, descending exact shared seconds, then ascending numeric counterpart id. do not depend on database row order or apply the card's peer filters. table expansion is entirely local presentation.

strict response validation requires:

- `deployment:null` iff the known player has no published record in the selected season;
- a present player has a deployment object; each peer belongs to the selected-season `players`, differs from self, has positive safe-integer seconds, and occurs at most once within each relation;
- ordered arrays satisfy the declared ties, combined counterpart bounds and 4T/5T totals against the published on-ice `metrics.included_seconds`;
- present zero-time/unavailable support has empty arrays; positive time requires both nonempty arrays. missing facts or violations are read failures, not empty successful results.

reuse the existing read-only handle and validate pairs one season at a time. startup scans each seasonal pair set once; profile requests use the endpoint indexes. do not load every season's pairs into every response, scan the full pair table per player or create an in-memory publication cache.

## profile and content contract

one `DeploymentTables` component sits **after peer distributions and before spatial views**. pass selected player, deployment, selected-season identities and the existing profile-link callback; keep query/navigation ownership in `routes/player.tsx`.

- heading: “5v5 deployment · <season>”. show the selected player's included on-ice minutes and existing `CoverageDetail` once above both tables; retain the page's `GlobalGap` notice.
- tables: “teammates shared with” and “opponents faced”. columns are linked name/reported position, “shared min”, and “share of included time”. reuse `playerName` and `Minutes`; omit counterpart team labels that could imply which stint supplied overlap.
- show ten rows per table initially, with independent “show all <n>” / “show fewer” buttons when needed. show the visible/total row count. return all rows in the api; no thresholds, extra requests, sort controls or new url parameters.
- calculate the percentage in one local presentation helper from shared seconds and **the selected player's** included seconds. display one decimal; a positive value below 0.1% is `<0.1%`. never divide by personal/spatial time, counterpart time or total pair-time. exact seconds determine order; display rounding does not.
- copy: “shared minutes use this player's included 5v5 time, including intervals with no recorded attempts. shares overlap: each included second counts for four teammates and five opponents.” add “a player can appear in both tables after a trade.” use neutral numbers, without higher-is-better colors, ranks or confidence styling.
- links preserve selected season and existing peer/metric/map settings through the established profile-link behavior. those settings do not change deployment rows. local expansion resets on player or season change, but not an unrelated view-setting change. reuse existing abort/loading handling; never show old-player rows beneath a new heading.

availability has explicit meanings:

| state | content |
|---|---|
| absent selected-season record | existing absence/history message; no deployment tables or invented zero |
| present, zero included time with unavailable coverage | “shared time is unavailable in the included evidence”; show existing reasons |
| present, supported zero included 5v5 time | “no included 5v5 time to report”; no percentages or “no teammates” claim |
| positive time with partial coverage | show retained overlaps and existing exclusions/gaps; no claim of complete physical deployment |

counterpart profile coverage can differ. do not infer pair-specific completeness or apply another mask. an omitted counterpart may have shared excluded/unavailable time. collapse the long tail for readability, not reliability. preserve native table semantics/captions, column scopes, keyboard links/buttons and focus on expansion controls. fit three columns at 320px and native 200% zoom; stack the tables when necessary, wrap names/headings and avoid page-wide overflow. no new UI library or export design.

## files, acceptance and delivery

| non-overlapping boundary | owner/files |
|---|---|
| authoritative pair facts and receipts | `analysis/src/hockey_stats/observed.py`; extend existing immutable result types and game/season checks |
| storage and candidate | `analysis/src/hockey_stats/publication.py`; schema 6, exact inserts/read-back and baseline preservation |
| transport | `app/src/shared/observed.ts`, `app/src/server/publication.ts`; strict pair/response schemas, startup checks and indexed profile query. a small `server/deployment-publication.ts` may contain these pair-specific reads/checks if needed to keep the existing reader cohesive; no generic relationship service |
| content and integration | `app/src/web/deployment-tables.tsx`, `routes/player.tsx`, `styles.css`; reuse `presentation.tsx`, existing links and view-state owners |
| retained evidence | extend the existing observed fixtures/readme; `docs/research/observed-05h/verification.md` records candidate refs, preservation, checks, costs and limits |

acceptance proceeds through temporary integration/live red → green → refactor → green checks, with independent source/statistical, systems and content review at each boundary:

1. **source and arithmetic:** hand-computed tiny intervals exercise positive zero-event time, repeated same-lineup segments, unequal exposure denominators, a teammate/opponent trade, goalies, 02d conflict exclusion, personal/spatial-only exclusions, unavailable games, nullable names and two seasons. independently check exact pair identities, seconds and source membership, not just conservation or calls back into the new counter.
2. **full candidate:** bind the reviewed 02d manifest/baseline; build all 3,936 inventory games. independently reconstruct pair reductions from retained native memberships and receipt masks, using a different counting method; compare every seasonal pair and 4T/5T total. exact per-game reduction verifies the full data, not a selection of famous players. all pre-existing table facts and source identities remain equal to the schema-5 baseline, except schema/publication id/time/producer and added receipt fields. count/reference/map/coverage/population meanings cannot drift.
3. **storage/api:** reject duplicate/reversed/self/unknown-season pairs, nonpositive/oversized seconds, incorrect bounds/totals and old schema. verify canonical symmetry, deterministic ties, trades in both lists, absent versus unavailable players, seasonal separation and existing errors. valid responses supply all peers and only selected-profile deployment. inspect query plans for both endpoint indexes; measure build size/time/memory, startup and representative profile payload/query cost. repair measured regressions; no new monitoring platform.
4. **browser/content:** verify top-ten/show-all/fewer, exact minutes/shares against known seconds, reciprocal unequal shares, missing/long names, trade crossover, partial/zero/absent states, keyboard operation, 320px/native 200% zoom and rapid player/season changes. links retain intended season/settings; peer changes leave deployment unchanged. confirm comparison, history, maps and one existing png retain their scope and values. the content reviewer checks the rendered denominator/overlap/gap wording.
5. **delivery:** detached browsing on a separate candidate listener; incompatible-schema rejection and code-paired manual rollback on disposable paths only. pinned typecheck/build pass. preserve the actual running site and databases. record candidate identity/hash, exact baseline comparison, independent checks, actual cost and any remaining source limits; no model admission or activation follows.

after final green, delete temporary tests/controllers and test-only dependencies; retain useful fixtures, checked facts and publication receipts. no permanent harness is assigned. if a distinct source failure appears, follow the existing complete-bundle fixture/issue policy; do not silently expand 05h into source recovery.

material tradeoffs: stored canonical pairs need two endpoint reads but avoid duplicate reciprocal facts; game receipts grow to preserve reconciliation without a game-pair api; seasonal aggregation hides stint detail; ten visible rows hide the tail until expansion; shares improve context but overlap and inherit missingness. no model result, additional service or broader feature compensates for these limits.
