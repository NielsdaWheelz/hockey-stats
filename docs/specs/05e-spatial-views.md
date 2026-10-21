# pr05e — observed spatial views

status: **full specification; implementation and activation unassigned.** confirmed 2026-10-21: league differences by default, absolute rates available, fixed descriptive smoothing with unsmoothed evidence retained. [the plan](../plan.md) owns progression. extend [05d](05d-descriptive-cards.md) independently of 04m/model admission; unchanged observed/publication contracts still apply.

## target and boundary

show **where recorded unblocked attempts occurred during a player's included 2025–26 regular-season 5v5 time**: two for/against maps on the profile, four on comparison, matched minutes/coverage and inspectable season/game evidence. python supplies finalized quantities through the existing sqlite → effect → react path. the maps describe team results while a player was present, not that player's isolated contribution.

no fitting, acquisition, xg, blocked-origin imputation, ability/replacement-impact maps, personal-shot maps, rankings/percentiles, new peer cohorts, date filters, event explorer, adjustable smoothing, map export or public hosting. retain the existing descriptive card/png, on-ice/personal results and peer membership unchanged. a later supported ability view extends these owners; this slice does not admit a model.

an included-league reference shows where recorded play differs from the season's ordinary pattern. replacement needs a declared population and, for substitution/value claims, supported attribution. a fringe-player observed average also includes its deployment circumstances. replacement valuation remains in the [capability inventory](../product-inventory.md), not an interchangeable zero for these maps.

## source and matched spatial population

use the exact local real corpus/path/digest in 05a/05d; fixture purpose remains explicit. reuse verified corpus/native inputs, reconstruction and 05d credit reads. no replacement captures, native-schema rewrite or research-artifact dependency. record the newly consumed coordinate fields and implementation identity in the existing producer receipt.

`observed.py` owns segment admission, event assignment and all masks. derive a **third, independent spatial population** from its admitted/coalesced on-ice segments:

1. select existing included `goal|shot-on-goal|missed-shot` dispositions. keep their single segment assignment, team, genuine-5v5 and penalty-shot exclusions. blocks and failed attempts supply no spatial event. do not import chance-model eligibility: shot type, prior actions, fitted actors and personal-credit corroboration are not additional requirements.
2. verify each newly consumed native coordinate/status against `reconstruct.attacking_coordinates` using `defending_sides` and the interpreted event. that owner rotates both x/y, requires event-specific side evidence and rejects period-side conflicts. inconsistent derived fields fail the build; legitimate missing/conflicting source evidence remains coverage.
3. require finite normalized coordinates inside `shot_origins.in_rink`. no clipping, inferred side, nearest-valid relocation, absolute-y fold or dropped negative-x events. for **both** panels retain the shooting team's attacking frame, goal at `(89,0)`; do not rotate against events into the selected player's attacking frame.
4. a missing coordinate, unresolved frame or outside-rink location removes its **whole assigned segment** from spatial counts and time for both teams. union with inherited on-ice masks, including collateral valid events. keep zero-event segments. personal-credit masks have no effect here.

these are **recorded event locations**, not verified physical releases. retain source-credited own/awarded goals with usable locations. finite coordinates do not prove who physically shot from that spot; official-credit meaning matches 05d. examples and source locators belong in verification.

spatial seconds cannot exceed on-ice seconds. for every player/game and season:

`spatial.known_excluded_seconds = on_ice.known_excluded_seconds + on_ice.included_seconds − spatial.included_seconds`.

unknown-strength time supplies no known denominator. inherit relevant gap reasons and global unassigned-player limitations; add `spatial_coordinates_missing`, `spatial_frame_unresolved`, `spatial_location_outside_rink`. propagate game limitations conservatively as the existing owner does. global unassigned games prevent complete season coverage.

| spatial support | scalar counts/rates | map |
|---|---|---|
| positive time | integer for/against counts, `3600 × count / seconds`; complete without gaps, partial otherwise | every display cell present, including observed zeros |
| zero time, no gaps | counts zero, rates null; complete with `no_spatial_5v5_exposure` | null: no rate map |
| zero time with gaps | counts/rates null; unavailable with gap reasons | null: unavailable, never an all-zero map |

recompute the no-exposure reason at game/season projection. reduce available counts and seconds before projection, never average game rates. missingness can be selective: results describe **included spatial time**, not complete-season rates or a missing-at-random estimate. no peer-minute or reliability cutoff controls map availability.

## geometry, smoothing and reference

one new `observed_spatial.py` adjunct owns this display geometry/arithmetic. reuse rink admission/normalization owners; preserve the research grid unchanged. its native nearest-center regions are not ordinary square bins and must not be drawn as though they were.

**display partition:** x edges `−100:5:100`, y edges `−42.5:5:42.5`; `cell_id = 17*x_index + y_index`. retain the 668 rectangles with positive-area intersection with the rounded rink: length 200ft, width 85ft, corner radius 28ft. ids are ordered, not consecutive. assign admitted coordinates by floor indices; only exact positive outer endpoints select the last index. draw rectangles through the matching rounded-rink svg clip. this grid consumes recorded coordinates directly, not research cell ids.

calculate each clipped area's `area_sqft` and actual centroid `(center_x,center_y)` once. a bounded helper integrates the rink cross-section:

`b(x) = 42.5` for `|x|≤72`, otherwise `14.5 + sqrt(28² − (|x|−72)²)`.

within a rectangle let `lo=max(y_min,−b(x))`, `hi=min(y_max,b(x))`. integrate positive height, x times that height, and `(hi²−lo²)/2` where `hi>lo`; divide moments by area. use elementary circle primitives or existing scipy quadrature with independent verification, not a new geometry dependency. total area is `17000−4*28²+π*28²`; all retained centroids lie inside the rink. verify areas within `1e−8 ft²` and centroids within `1e−8 ft` of independent boundary examples. exclude truly empty cells, not positive slivers.

**fixed pooling:** freeze gaussian standard deviation `h=10ft`. with area `a_j` and centroid `c_j`:

```text
w[j,i] = a[j] * exp(-||c[j] - c[i]||² / (2 * h²))
k[j,i] = w[j,i] / sum_j w[j,i]
smoothed_counts = k @ recorded_counts
```

use the full finite matrix, one operator for both directions, all players and the league. columns sum to one. apply it to season aggregates, not repeatedly to games; materialize it only in python. area weighting avoids assigning equal mass to tiny corner pieces; centroids avoid representatives outside the rink.

this is **discrete pooling of five-foot bins**, not continuous event-level kde, a fitted probability surface or ten-foot statistical precision. it blurs evidence according to a fixed convention; near boundaries it need not preserve perfectly uniform density. no bandwidth search, browser blur, interpolation across unavailable maps or renormalization to equal player totals.

let `T` be retained physical spatial seconds, `C_j` retained events at cell j across both shooting teams, and `t_p,n_pj` a player's spatial seconds and counts in one direction:

```text
league_raw_rate[j] = 3600 * C[j] / (2 * T)
player_raw_rate[j] = 3600 * n[p,j] / t[p]
league_density[j] = 100 * (k @ league_raw_rate)[j] / area[j]
player_density[j] = 100 * (k @ player_raw_rate)[j] / area[j]
difference[j] = player_density[j] - league_density[j]
```

color units: **unblocked attempts per 60 minutes per 100 square feet**. panel totals remain ordinary attempts/60. retain integer recorded counts and unsmoothed bin rates in the numerical evidence; smoothed mass is never a recorded count. `sum(density[j]*area[j]/100)` reproduces total rate; integrated difference reproduces player minus league total rate.

count physical events once for the league and use **two team-directions per elapsed second**. do not average player rates, exclude the selected player, or let table/position/peer-minute controls change the baseline. both directions use the same league map and matched spatial population. zero league time gives null rates/maps; a positive-time player necessarily has a defined reference.

## publication and api

hard-cut to sqlite schema **3**, `PRAGMA user_version=3`; retain command interfaces, `kind:observed_5v5`, on-ice/personal versions and finalization/receipt sequence. add literals `spatial_population_version:matched_unblocked_locations_v1` and `spatial_display_version:rect5_gaussian10_v1`. no dual reader, in-place migration or fallback.

| storage owner | additions |
|---|---|
| `publication` | two spatial versions; typed `spatial_coverage_json` as defined below |
| `game` | physical `spatial_included_seconds`, `spatial_known_excluded_seconds`, nullable `spatial_away_unblocked`/`spatial_home_unblocked`, `spatial_coverage_status`, `spatial_reason_codes_json` |
| `player_game`, `player_season` | `spatial_`-prefixed scalar fields from `SpatialMetrics` below; keep every existing field unchanged |
| `spatial_cell` | one row per cell: id, bounds, centroid, area; `league_count`, `league_raw_per60`, `league_density` (nullable only under zero-time projection) |
| `player_game_spatial` | sparse `(player_id,game_id,cell_id,for_count,against_count)`; at least one count positive; primary key all three ids; composite foreign key to `player_game`, plus cell foreign key |
| `player_season_spatial` | dense cells for each positive-time player: `(player_id,cell_id,for_count,against_count,for_raw_per60,against_raw_per60,for_density,against_density,for_difference,against_difference)`; primary key both ids and corresponding foreign keys |

no fourth game-team cell table: receipts retain physical team-cell counts; player-game cells provide exact publication reconciliation. absent sparse cells mean zero **only within available support**. zero-time players have no season cell rows; positive-time players have all 668, even with no events.

`spatial_coverage_json` fields: `included_seconds`, `known_excluded_seconds` (both physical); `unblocked_attempts`, `unblocked_per60`; `coverage_status`, `reason_codes`; `inventory_games`, `games_with_included_time`, `partial_games`, `unavailable_games`; `reason_game_counts:[{code,games}]`. game counts/reasons use spatial status, not the existing all-attempt status. its total rate is `3600 * unblocked_attempts / (2 * included_seconds)`, equal to summed league raw cell rates; a player-denominator validator must not be reused here.

league projection: positive `T` gives integer counts and finite rates/densities; zero `T` without gaps gives zero counts and null rates/densities; zero `T` with gaps gives null counts/rates/densities. apply that rule to the league total and cells. geometry rows always remain present. global zero-time reason/status follow the spatial support table.

```ts
type SpatialMetrics = {
  included_seconds: number
  known_excluded_seconds: number
  unblocked_for: number | null
  unblocked_against: number | null
  for_per60: number | null
  against_per60: number | null
  coverage_status: "complete" | "partial" | "unavailable"
  reason_codes: readonly SpatialReasonCode[]
}
// SpatialReasonCode = inherited gap reasons (without no_5v5_exposure)
// + the three location reasons + no_spatial_5v5_exposure.
```

counts/seconds/ids retain existing safe-integer/id contracts. raw rates/densities are finite nonnegative numbers; differences finite signed numbers. geometry floats are finite with positive areas; reasons sorted/unique. enforce null/zero/support rules, exact rowsets and applicable constraints in python, strict sqlite and effect schemas. extend the reader's single-column foreign-key inspection to validate the new composite relation.

keep all-player summaries free of grid arrays and new spatial scalar groups. extend both responses with one required nullable field:

```text
spatial: null | {
  definition: {population_version, display_version, sigma_ft:10,
    rink:{length_ft:200,width_ft:85,corner_radius_ft:28,goal_x:89},
    units:"attempts_per60_per100sqft", orientation:"shooting_team_positive_x"},
  league_support: <spatial_coverage_json>,
  cells: [<spatial_cell fields, sorted by cell_id>],
  players: [{player_id, data:null | {
    metrics:<SpatialMetrics>, cells:null | [<player_season_spatial cell fields>]
  }}]
}
```

`data:null` means a requested valid id is absent; `cells:null` means a known player has zero spatial time. selected-player cells omit redundant player ids. geometry/reference appear once, and all identities/values belong to the response's publication.

- `GET /api/league`: no query gives `spatial:null`. optional **single** query `spatial=ID[,ID]` requests one or two distinct canonical `HockeyId`s. empty/malformed/repeated fields, duplicate ids or more than two ids return typed `InvalidSpatialSelection`/400. valid unknown ids get nullable entries in requested order.
- `GET /api/players/:playerId`: retain existing 400/404 behavior; always include exactly that player's spatial selection. add `spatial:SpatialMetrics` to existing game rows. no per-game map endpoint or bulk map download.
- comparison loader requests syntactically valid a/b ids, deduplicated; existing inline malformed/equal/unknown selection messages remain. revalidate on a/b changes; peers, `peerMin` and map-mode changes alone do not fetch. preserve abort handling: never pair new identities with prior response maps.

effect reads finalized values; it does not smooth or calculate hockey rates. startup verifies count/time arithmetic, geometry identity, exact rowsets, game→season reductions, difference identity and mass conservation, without reimplementing the gaussian kernel. use bounded validation reads rather than materializing every sparse/dense row as one object; record actual cost. a small typed reader adjunct is justified if it separates spatial validation from ordinary queries.

## views and content

content design owns definitions, hierarchy, numeric alternatives and missing states. reuse typography, spacing, focus and formatting; one `spatial-views.tsx`, no chart platform or new frontend dependency.

| surface | required behavior |
|---|---|
| profile | after observed summaries, `where unblocked attempts occurred`; paired `for — the player's team` / `against — opponents`; counts, total rates, spatial minutes/coverage, maps and expandable numerical evidence |
| comparison | same component for both players, four panels; each player's own spatial population/minutes; no common-games or isolated-effect claim |
| game evidence | spatial for/against counts, included minutes and coverage beside existing populations; season counts/time reconcile to these contributions |
| explanation | scored/saved/missed events, excluded blocks, recorded-location meaning, matched missing-location exclusions, league reference and fixed smoothing; reasons and global unassigned-game disclosure |

show a shared **included league reference** summary: team-direction minutes (`2*T/60`, explicitly labeled), supported/inventory games, coverage and exclusions/reasons. explain that both directions use this reference and peer controls do not change it. distinguish these team-direction minutes from physical time and player minutes; do not conceal the baseline's own selective coverage.

one shared mode: `difference from included league average` (default) / `absolute rate`. both show the same smoothed quantity. url `map=absolute` selects the alternative; absent means difference, invalid/repeated values normalize to default while preserving selections/peers. retain mode through profile↔comparison and history; no fetch. raw counts/rates remain in the table, without another map toggle.

draw the **full** rink, `+x` toward the top and `+y` toward the right. one attacking orientation for both directions; explain that opponents attack that goal in the against panel. preserve long/negative-x attempts and lateral signs. rink/goal landmarks must not obscure values. svg clipping draws curved support; no screenshot or approximate boundary polygon.

difference uses a perceptually ordered blue–neutral–red palette: fewer / same / more. red is not universally good or bad. absolute uses a nonnegative sequential palette. all available visible panels share one domain: `[-M,M]` from maximum absolute displayed difference, or `[0,M]` from maximum displayed absolute density. an unavailable player does not suppress another's maps/legend. no independent scales, hidden percentile clipping or outlier suppression. all-zero values get an explicit zero state with a fixed positive legend extent; no available data means no map/legend. say that the scale changes with selection: colors across unrelated pages require their legends. stack narrow-screen panels with player/direction headings and the same shared legend; no separate mobile scale.

visible copy: `recorded 2025–26 regular-season 5v5`; `unadjusted on-ice results`; `five-foot bins; fixed gaussian smoothing, 10-foot standard deviation`. spatial minutes may differ from other panels. no significance shading, reliability badge, winner label or precision claim. positive time and zero attempts is real zero density (and negative league difference); zero-time/missing maps receive reasons, not league-average white.

per-player expandable semantic table: cell id/bounds/area, recorded for/against counts, raw bin rates, displayed densities, league density and differences. label raw bin rates versus displayed density; round only for presentation, preserving sign/small-value information rather than calling a nonzero plotted value exact zero. summaries/captions explain without hover. no hundreds of keyboard stops; tables scroll within labeled containers. keyboard use, 320px reflow and actual native 200% zoom apply. 05d png facts/layout remain unchanged; maps stay browser-only.

references: [hockeyviz shot-map guide](https://hockeyviz.com/howto/shotMap) motivates unblocked patterns, same-season league context and exposure; its xg weighting is outside scope. [isolated impacts](https://hockeyviz.com/howto/isolate) describes a separate modeling claim. [replacement methodology](https://evolving-hockey.com/glossary/goals-above-replacement/) defines a separate value reference. [accessible complex images](https://www.w3.org/WAI/tutorials/images/complex/) supports captions and numeric evidence. no private-method or exact visual parity claim follows.

## owners and acceptance

| boundary | files / deliverable |
|---|---|
| facts/population/numerics | `analysis/src/hockey_stats/observed.py`, new `observed_spatial.py`; reuse normalization/rink primitives. masks, geometry, counts, pooling, reference, final rows and receipts |
| publication/transport | `analysis/src/hockey_stats/publication.py`; `app/src/shared/observed.ts`, `app/src/server/publication.ts`, `main.ts`, `app/src/web/client.ts`; schema-3 finalization, strict reader and selected-map composition |
| presentation/content | new `app/src/web/spatial-views.tsx`; existing `routes/player.tsx`, `routes/compare.tsx`, `presentation.tsx`, `styles.css`; shared modes/scales, coverage, definitions and numerical alternatives |
| evidence/handoff | `README.md`, `fixtures/README.md`, `docs/research/observed-05e/verification.md`; checked cases, candidate commands, costs and code-paired cutover/rollback |

agree fields first; dependency order is population/geometry → publication/api → views. parallel work stays within these owners. reuse concrete formatting, segments and validation; extract only shared or substantial incidental complexity. no research migration or generic plotting/metric framework. source/statistical, systems and content reviewers independently challenge each boundary and integrated result.

temporary integration/live **red → green → refactor → green**, independent reviews, then delete temporary tests/controllers/test-only dependencies. retain useful original fixtures, checked facts and receipts; no new lasting harness under [07](07-lightweight-testing.md). documentation changes need only link/consistency checks.

1. independently check rotations, both directions, side switches/conflicts, focal missing/outside-rink coordinates, negative-x attempts, own/awarded goals, penalty shots and unusable kinds. derived-coordinate drift fails; legitimate missingness stays visible; collateral masks remove counts/time together; zero-event time remains. reuse equivalent fixtures; preserve complete original bundles for new distinct defects.
2. independently verify cell assignment at interior/outer/rounded boundaries, all 668 areas/centroids, total area and symmetry. inspect central/corner impulses, uniform density and a sparse real map. verify finite nonnegative kernel columns sum to one, zero preservation, linearity and mass/difference conservation to `1e−10 + 1e−10*abs(expected)`; geometry uses its stated tolerances. uniform input need not stay uniform at boundaries.
3. reconcile per game/team/cell: player-for sums equal opponent player-against sums and are divisible by five; dividing recovers physical counts. cells match game team totals; player-game cells reduce exactly to season cells; league cells equal summed player-for cells/5; player seconds equal ten times physical seconds. retain independently counted physical team evidence in receipts. null/zero/support rules survive serialization.
4. build/check one real candidate from all 1,312 pinned inventory games, preserving all old on-ice/personal fields and input bytes. report spatial supported games/players/time/counts, extra losses/reasons, runtime, peak memory, candidate size, startup cost and selected-pair payload size. no invented coverage floor or full-season claim from fixtures; no fit or new hdd dependency.
5. verify sqlite→effect→browser agreement, selected-only payloads, malformed-candidate rejection, unknown/duplicate ids, zero/partial/unavailable maps, trades and unchanged peers/png. pinned typecheck/build pass. exercise compare changes/aborts, direct links, back/forward/reload and mode/peer state. check shared legends, orientation, clipping, raw-versus-smoothed evidence, keyboard, 320px reflow and native 200% zoom across profile/comparison/game evidence.
6. browse a separate-loopback candidate with raw inputs/python/network/hdd unavailable. preserve actual active/previous databases. verify schema-3 rejection of schema 1/2 and code-paired forward/rollback in a disposable directory. document explicit later stop/check/copy/restart with the actual active schema and compatible git revision; no archived build, release manager or compatibility reader.

completion is a checked candidate and useful observed maps, **not activation or admission**. costs: selective spatial support and a third minute total; five-foot quantization and fixed ten-foot blur; unadjusted league context rather than replacement value; a new display partition/area calculation; per-view color scales; stored season summaries for simple detached serving; schema rebuild/manual rollback; one selected-map request when comparison changes. none authorizes another modeling or smoothing campaign.
