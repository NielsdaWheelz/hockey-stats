# pr05f comparative observed cards

status: **implemented and verified, 2026-10-21; [acceptance and independent review](../research/observed-05f/verification.md) complete.** confirmed: raw rates plus observed percentiles; higher percentile means higher rate for every row; withhold percentiles outside the reference cohort. [the plan](../plan.md) owns assignment. implementation and verification complete; activation remains separate. independent of 04m and model admission. extend [05c](05c-player-explorer.md), [05d](05d-descriptive-cards.md) and [05e](05e-spatial-views.md); preserve their contracts except the presentation changes named here.

## target and boundary

understand a player's **recorded 2025–26 regular-season 5v5 production and position among declared peers** at a glance. five compact rows combine raw rates with observed percentiles on the profile, comparison and single-player png. one selected-metric distribution supplies detail. all values come from one existing publication response.

this is application work over published facts: no acquisition, fitting, new hockey quantities, database rebuild/schema change, new api, dependency upgrade or model admission. no ability/overall score, reversed defense rating, xg, map percentile, replacement value, historical selector, league percentile columns, csv, comparison/map download, public hosting or generic card framework. league discovery, spatial populations/references and game evidence retain their meanings. no work on 04m's files or results.

## quantities and reference populations

use the five rows in this order. paths are relative to `PlayerSummary`; rates remain the producer's unrounded values. counts remain accessible supporting evidence. all rates are per 60 included 5v5 minutes of their named population.

| metric key | visible label | published count / rate | population | rate decimals |
|---|---|---|---|---|
| `sog60` | shots on goal | `personal.shots_on_goal` / `personal.shots_on_goal_per60` | `personal` | 2 |
| `goals60` | goals | `personal.goals` / `personal.goals_per60` | `personal` | 2 |
| `primaryAssists60` | primary assists | `personal.primary_assists` / `personal.primary_assists_per60` | `personal` | 2 |
| `for60` | on-ice attempts for | `metrics.attempts_for` / `metrics.for_per60` | `onIce` | 1 |
| `against60` | on-ice attempts against | `metrics.attempts_against` / `metrics.against_per60` | `onIce` | 1 |

retain `PeerSettings = { peers: "position" | "all", peerMin: number }`, default `position/300`. `personal` uses `personal.included_seconds` and personal coverage; `onIce` uses `metrics.included_seconds` and on-ice coverage. apply the same minute setting separately. the three personal rates share one cohort; the two on-ice rates share another. current equality of their minutes is not a shared-population contract.

reuse 05c membership: reported `C/L/R/F` are forwards, `D` defense; unsupported positions remain invalid under the existing schema. require positive family seconds, exact `seconds >= 60 * peerMin` and available family rates. eligible partial records remain included. one equally weighted observation per player, with an eligible selected player present exactly once. no time weighting, complete-only restriction or leave-one-out rank. discovery filters do not select peers.

same-position pairs share their family cohorts; mixed pairs in position mode use separately named forward/defense cohorts. all mode supplies one cohort per family. retain original first/second slots. each cohort states its population, group, minimum, member count and partial-member count. selections remain searchable and visible regardless of peer eligibility. changing peers never changes counts, raw rates, exposure, map baseline or game rows.

## percentile contract

for a selected **member**, let `n` be cohort size, `L` the number with a strictly lower published rate and `E` the number with an exactly equal rate:

`percentile = 100 * (L + E / 2) / n`

this is the midpoint of strict and inclusive empirical positions, not a fitted distribution. `[1, 2, 3, 3, 4]` gives `60` for either `3`; five equal values give `50` each. it corresponds to [scipy's `kind="mean"`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.percentileofscore.html), not its default `rank`; implement the small arithmetic locally without a statistical dependency. never recalculate hockey rates, use rounded labels to form ties, add an epsilon or force extrema to 0/100.

| case | card standing / detail |
|---|---|
| eligible member | numeric percentile and marker; the member remains in the reference once |
| finite rate below the floor | `outside reference: under <m> <population> minutes`; no percentile/percentile marker; retain raw rate and raw-distribution highlight |
| null rate, including positive assists with zero personal time | `rate unavailable`; retain count and existing reason; neither percentile nor raw-rate marker; never substitute zero |
| empty cohort | `no players meet this peer rule`; no percentile; retain any finite selected raw marker |
| one member | percentile `50`; explicitly `one eligible player; no between-player comparison` |
| all ties | all members `50`; raw plot retains overlapping marks and the actual common rate |

zero is a valid rate. compare exact published finite numbers; schema errors remain errors. format percentiles to one decimal, without a bare percent sign; use `<0.1` or `>99.9` if rounding would invent a 0/100 endpoint. marker placement uses the unrounded percentile. equal rounded rate labels can have different standings; explain that calculations use unrounded values in the definitions.

**higher means more of the recorded rate throughout.** the against row says `higher = more opponent attempts`. scales/marks are neutral, without favorable colors, stars, tiers, winner labels or arithmetic combining percentiles. the label is `observed-rate percentile`; describe ties as half counted. do not say the value is the exact percentage strictly below, a confidence level, ability or reliability. shared play also makes these correlated observations; the distribution is descriptive spread, not uncertainty.

## application composition and urls

the existing `GET /api/league` and `GET /api/players/:playerId`, typed responses and selected-map queries remain unchanged. profile uses its coherent `players/games/spatial/publication/coverage` response; comparison uses its existing selected-map league response. one pure application owner derives membership, row values and percentiles from that list. python still owns source eligibility, counts, hockey rates and spatial numerical work; ordinal summaries of a user-selected displayed cohort belong to the application. do not introduce persistence, a new schema or a second fetch for rankings.

add one presentation query to profile/comparison: `metric=sog60|goals60|primaryAssists60|for60|against60`, default `sog60`. it selects the detail only; all five overview rows stay visible. use one labeled native select shared by the pair. parse with `getAll`; absent uses default; repeated/empty/invalid values normalize only this key to default with history replacement. preserve unknown and unrelated keys.

reuse the existing route behavior: meaningful committed edits push one entry without scrolling; unchanged edits do nothing; normalizing waits for idle; metric/peer edits do not fetch or clear picker drafts. extend both `shouldRevalidate` allowlists. compose edits with `viewSearch(location, navigation.location)` so overlapping picker/map/peer changes retain pending selections. `reset peers` resets only `peers/peerMin`, preserving `metric/map` and selected ids.

forward profile → new comparison, comparison → profile and peer-table links carry committed `metric/peers/peerMin/map`. back links restore the recorded destination metric/peers and existing return state; preserve 05e's map-mode behavior. league entry starts at default metric. invalid/incomplete/duplicate pairs retain existing picker/errors and show no comparison card or peer detail. ordinary player/pair changes retain current coherent loading, cancellation, retry and selected-map requests. no old name/new value mixture.

## presentation and export

the content designer owns hierarchy, labels and edge-state copy for every surface, and reviews a real plus boundary-case rendering before acceptance. use existing system fonts, tabular numbers, restrained sheet, link/focus styles and semantic html. one concrete five-row content model feeds html and png; their layout mechanisms may differ, their facts and meanings may not.

| surface | required hierarchy / good content |
|---|---|
| profile | identity/season/teams/reported position → `recorded 5v5 results` and `regular season · unadjusted observations` → reference controls → five rows in personal/on-ice groups → grouped included minutes and visible coverage → one raw-rate detail → existing spatial views and game evidence |
| comparison | existing pickers/global gap → shared reference controls → aligned five rows, first/second player columns → each player's two support summaries → one detail with both selections → existing maps/evidence. replace duplicate rate summaries; preserve counts, games and full coverage in concise supporting evidence |
| each overview row | label → raw rate and units → neutral 0–100 position strip with 0/50/100 labels and numeric percentile, or explicit unavailability. enough text to read without hover; counts may be subordinate but remain available |
| reference/support | named group and family, minimum, `n` and partial `n`; selected included/known-excluded minutes, coverage and outside-reference status. name both supports even when numerically equal; no fabricated coverage percentage |
| detail | metric select → named cohort(s) and raw-unit rug → selected values/markers → expandable numeric peer table per group. one metric at a time; count, family minutes, rate, percentile and coverage columns plus linked identity |
| png | one player, all five rows and both support/reference summaries; same declared cohort and standing as the screen; concise definitions and evidence footer; useful independently of the website |

raw detail reuses 05c's neutral rugs, first/second circle/diamond markers, accessible tables and finite-domain handling. one shared increasing raw-rate axis across the selected metric's groups/selections, including against; different metrics need not share a domain. include all finite extremes without clipping; constant domains expand finitely. missing rates have no mark, outside-reference selections retain separate highlights, ties overlap with separate labels. selected markers annotate rather than duplicate members. numeric tables contain exactly the displayed cohort, deterministic name/id order; no hundreds of focusable marks. group counts/coverage use the metric's family. provide a short chart description and linked/expandable numerical alternative following [w3c guidance](https://www.w3.org/WAI/tutorials/images/complex/).

keep five rows readable at 320 css pixels and native 200% zoom. labels wrap; comparison tables may scroll in the existing labeled, keyboard-accessible container. no clipped names/numbers, hover-only meaning, percentile gradients or motion implying trends. the minute cutoff remains a viewing rule. partial records and global unassigned-game gaps remain visible; detailed reasons, full definitions and game evidence remain reachable through existing owners. explain repeated outside-reference/coverage conditions once per family with short, unambiguous row placeholders. no separate full comparison table repeating the same five rates.

retain the existing single-player export entry on the profile. capture player, publication, coverage, committed peer settings and the derived card rows synchronously at click, before asynchronous png rendering. a later control/player change cannot alter that snapshot. use the existing svg → canvas → png path, safe text nodes, measured wrapping and object-url cleanup. no external fonts/images or new renderer. width remains 1200 pixels; height grows for genuine content rather than clipping or shrinking text into illegibility. normal cards must remain a compact five-row summary, not the former full definitions/reasons transcript.

the png carries full name/player id, season/state, reported position/team list; count and rate for each row; both included/known-excluded minutes and coverage; actual family cohort/group/minimum/member/partial counts; withheld-standing notices; `higher percentile = higher recorded rate` with the against clarification; concise tied-rank and observed-not-ability meaning; publication id and generated time labeled as publication time; fixture marker when applicable. include a compact global-gap statement when present. full reason lists, source hashes and longer definitions stay in the profile. do not print a localhost address as though it were a public evidence link. no map or selected-detail graphic is added to the png.

the references motivate comparative hierarchy, not borrowed statistical claims: [hockeyviz descriptive cards](https://hockeyviz.com/howto/skaterCard) put production in context; [jfresh's guide](https://hockeystats.com/about/player-cards) describes predictive quantities and position-relative percentiles. our rows remain recorded single-season rates.

## files and capability contracts

| owner / files | responsibility |
|---|---|
| `app/src/web/observed-comparison.ts` — new | concrete five-metric definitions, existing peer selection moved here and extended with required population, pure percentile/standing and shared card view data. one owner for all html/png arithmetic |
| `app/src/web/explorer.ts` | discovery remains; retain `PeerSettings`/query helpers; add metric parsing; remove moved peer implementation/types and update consumers, without legacy wrappers |
| `app/src/web/peer-distributions.tsx` | export one concrete `PeerControls` preserving minute draft/apply/reset state, rendered once above the overview; separate detail replaces two always-visible figures with one selected-metric rug/table and consumes prepared cohorts; owns no fetching or url state |
| `app/src/web/descriptive-card.tsx` | export a concrete `ObservedRateValue` for raw rate/standing presentation, reused in profile/comparison rows; keep profile-only download/game links separate. single-player svg/png consumes the same card facts; remove superseded text-dump layout |
| `app/src/web/routes/player.tsx`, `routes/compare.tsx` | derive comparison once per response/settings; compose existing surfaces; own committed query/history, controls and navigation |
| `app/src/web/presentation.tsx`, `styles.css` | shared value/coverage formatting and concise copy only where reused; responsive rows/scales; preserve `Quantity`, `Minutes`, `CoverageDetail`, `GlobalGap`, `Evidence` and definition owners |
| `README.md`, `docs/research/observed-05f/verification.md` | actual user-facing behavior/commands and reviewed verification receipt, created during implementation |

the internal contract is concrete, not a wire schema or plugin registry:

```ts
type ObservedRateKey = "sog60" | "goals60" | "primaryAssists60" | "for60" | "against60"
type PeerPopulation = "personal" | "onIce"
type Standing =
  | { kind: "ranked"; percentile: number }
  | { kind: "outside" }
  | { kind: "unavailable" }
```

`readRateMetric(search)` returns `{ metric, search }`, normalizing its owned key only. moved `selectPeerGroups(players, selected, settings, population)` returns the existing group shape (`key`, `members`, `selected` with original `slot`). population is required; never silently default a personal row to on-ice minutes. `buildObservedComparison(players, selected, settings)` returns `{ settings, groups: { personal, onIce }, cards }`; each card binds its original player/slot and five ordered `{ metric, population, count, rate, standing, groupKey }` rows. derive unavailable/outside text from that row and its family support; a finite below-floor rate is outside, a null rate unavailable. the caller supplies the selected rows from this response. each row resolves to exactly one family/group; the model retains exact numbers and source player records. both overview and detail use this result rather than recalculating cohorts separately. fixed metric labels/field selection/precision have one owner.

`PeerControls` receives `settings/onChange`; detail receives the prepared comparison, `metric/onMetricChange` and route-built `profileLink`. `ObservedRateValue` consumes one prepared row and its family/group context, with no navigation, downloads or fixed element ids. routes compose labels/rows using that display; comparison retains native table semantics. profile-only anchors/actions stay in the profile composition. do not duplicate controls or carry a nonexistent game anchor into comparison.

delivery boundaries are **comparison logic**, **content/rendering/export**, and **route integration**. agree these types first; give each file one implementation owner. a content designer defines/reviews each surface above; independent statistical, systems and content reviewers challenge the contracts and final integrated behavior. no parallel edits to shared files, unrelated historical migration, generic experiment framework or new dependency.

## acceptance and handoff

implement temporary integration/live red → green → refactor → green checks at these boundaries, independently review, then delete tests/controllers and test-only dependencies. retain useful checked fixtures/facts and the receipt. this slice selects no lasting suite; [07](07-lightweight-testing.md) retains its separate scope. use current pins and a separate build/listener with the existing read-only local publication; preserve the running site, its assets and active/previous database. no database rotation, raw-source audit or fitting is necessary.

1. **independent arithmetic:** hand-enumerated typed-response cases verify exact memberships and all five standings, including `[1,2,3,3,4]→60`, all ties/singleton→50, zero/null, empty cohorts, `(60*m)-1`, `60*m`, `(60*m)+1` seconds, zero minimum with zero time, all position codes, selected members once, same/mixed groups and all-skater mode. distinguish rounded-equal but unequal raw values. deliberately differ personal/on-ice support and coverage; retain zero-time positive assists without a rate. below-floor selections have raw markers but no percentile.
2. **real integrated values:** use the active local publication on an isolated listener. independently enumerate cohort ids/counts/partial counts and standings for selected high/low-minute profiles and same/mixed pairs. profile, comparison, selected detail, numerical tables and png agree. published counts/rates/game/maps and source/publication identities remain unchanged; no hard-coded assumption that every player is eligible or every support matches.
3. **journeys and requests:** table → profile → comparison → peer profile → back; direct query/reload/back/forward; metric changes, minute drafts/apply/reset, invalid/repeated keys, empty groups and invalid pairs. record request counts: no metric/peer request; player/pair changes retain existing selected-map behavior. delayed/aborted requests plus rapid picker/map/metric/peer edits preserve pending ids, committed settings and coherent values; no picker draft loss.
4. **export and accessibility:** open actual downloaded pngs, not just svg strings; independently compare all five rates/standings, supports and reference metadata to the click snapshot, including a control change during export. exercise unavailable/outside/empty/singleton/partial/fixture/global-gap cases, long/missing/duplicate names, export failure/retry and object-url cleanup. keyboard controls, numeric alternatives, 320px reflow and native 200% zoom pass; record native zoom separately from viewport approximations. designer verifies hierarchy and against direction on screen and image.
5. **delivery:** pinned `npm run typecheck` and `npm run build`; detached browsing from the local database without python/raw/hdd/network dependence; unchanged api/schema and database bytes. independent review after green, repair at the responsible owner and rerun affected checks. remove temporary checks/dependencies after final green. receipt distinguishes real/synthetic/manual evidence, tradeoffs and unresolved issues; record concrete issues under `docs/issues/`. this completes implementation verification, not activation or scientific admission.

accepted costs: percentile compression and sensitivity to cohort choice; different personal/on-ice populations; withheld standing for excluded selections; neutral against direction requiring explicit reading; one detail metric at a time; compact exports carry essential context while full evidence stays on the page. raw units, declared populations and preserved evidence make those costs inspectable.
