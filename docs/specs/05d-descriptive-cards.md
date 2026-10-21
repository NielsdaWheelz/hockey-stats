# pr05d — richer descriptive cards

status: **full specification; implemented and verified 2026-10-21. [acceptance](../research/observed-05d/verification.md) records the real candidate and independent reviews; separately authorized schema-2 activation is complete on 2026-10-21.** confirmed 2026-10-21: one single-player png download; a separate personal population preserves existing on-ice results. [the plan](../plan.md) owns progression. independent of 04m and model admission. extend [05a's publication](05a-observed-website.md) and [05c's explorer](05c-player-explorer.md); their unchanged contracts still apply.

## target and scope

browse, sort, compare and download **recorded 2025–26 regular-season 5v5 results**: personal shots on goal, goals and primary assists, beside existing on-ice attempts. every new season quantity has inspectable game contributions, matched personal exposure and visible coverage. one python producer, one sqlite publication, the existing effect api and three existing routes.

no fitting, acquisition, ability/xg/adjusted maps, percentiles, new peer plots, points/net scores/shooting percentage, special teams, date windows, historical selector, portraits/logos, public hosting or card framework. existing peer plots retain their on-ice meaning and 05c rules. [05e](05e-spatial-views.md) owns subsequent observed maps. neither study completion nor descriptive publication admits a model.

## source and credit contract

use the exact real corpus/path/digest specified in 05a; explicit fixture corpora remain separate. additionally consume the play-by-play and landing captures named by each reconstructed envelope's `interpreted.inputs`. derive `read_capture`'s game-root argument from the bound `.../<source>/capture.json` path. use that reader/strict decoding; verify recorded game identity, request time, http status and body hash against the frozen input. record every consumed receipt/body. promised missing files fail even when the capture reader returns unavailable; changed bytes or contradictory derived locators also fail. originally unavailable sources or unresolved credits produce located coverage. no replacement capture or source regeneration.

bounded specification inspection found 192 timed fixture goals with agreeing ordered assist lists, including 14 explicit unassisted goals. one selected real envelope's two original captures are locally readable with matching hashes. this does not establish full-season coverage. native artifacts omit landing assists: read new fields in one `scoring_credits.py` adjunct without rewriting corpora or changing frozen native schemas.

| quantity | exact credited events |
|---|---|
| `shots_on_goal` | one credit per retained `shot-on-goal` to `roles.shooter`, and per retained `goal` to `roles.scorer` |
| `goals` | one credit to the retained goal's scorer; a subset of shots on goal |
| `primary_assists` | one credit to the corroborated first assister of a retained goal, or none for an explicitly unassisted goal |

these are credited statistics, not verified physical actions: own/awarded goals retain their source meaning. misses, blocks and failed attempts contribute none. reuse existing supported event strength, penalty-shot exclusion, shooting team, scorer/shooter and lineup checks. scorer/shooter can be a goalie; preserve goalie credits in reconciliation without making skater rows.

for each otherwise included goal:

1. uniquely match landing and play-by-play by event id, corroborating period/type, clock, scoring team and scorer. reuse/extract existing goal-identity corroboration in `reconstruct.py`, preserving historical modifier/native outputs. a saved source path alone is not proof. extract identity-field checks separately if needed; retain the old modifier wrapper's broader checks. modifier presence is not an assist requirement. keep new credit issues out of reconstruction's document/issues.
2. inspect raw play assist-key presence and the matched landing `assists` array. require zero to two valid positive player ids, valid order, no duplicates/scorer-as-assister and unique same-team game-roster identities. goalies are valid assisters. absent both play assist keys plus explicit landing `[]` establishes no assist. present null/invalid keys, `assist2` without `assist1`, or absent/null/malformed landing arrays do not establish zero.
3. require agreement on first assister or no assist. secondary-only identity disagreement between otherwise valid lists is diagnostic; malformed lists or conflicting primary credit remain unresolved.
4. an assister need not be on ice at the goal. credit its same-team roster identity even after a line change; its own included time supplies the rate denominator.

the adjunct returns one located record per otherwise included scored/saved event: `{source_index, status: credited|unresolved, scorer_or_shooter_id, primary_assister_id, evidence_refs, reason}`. `observed.py` joins `source_index` to its authoritative segment assignment for masks/receipts. a credited saved shot has no assist; a credited goal's null assister means corroborated none. each reference identifies capture/hash and raw field path. decode each selected body once. frozen roles/goal identity must agree with bound raw fields: source conflicts are coverage; altered derivations are contract errors. no adjunct artifact pipeline, cli, fallback interpreter or second general parser.

## two matched populations

`observed.py` remains the mask/segment/aggregation/receipt owner. factor its existing accepted-event result only enough to share it; no copied reconstruction. existing on-ice counts, seconds, coverage, identities and peer membership remain identical.

personal support starts from those included coalesced segments. unresolved personal credit removes its entire segment from **all three personal counts** and the time of its on-ice skaters, for both teams. union additional masks, including collateral valid events. unavailable landing credit evidence affects included goal segments, not unrelated goal-free time. retain located exclusions and losses; all original observed exclusions still apply.

count each accepted event once at its existing segment assignment. the goal's strength and retained segment select an assist even if its recipient is off ice; never invent an assister interval. this is event-strength scoring divided by retained personal time, not a count of assists made while present.

`personal.included_seconds` is player time in retained personal segments. `personal.known_excluded_seconds` unions original known exclusions and additional personal-mask time; unresolved-strength time supplies no known denominator. personal seconds cannot exceed on-ice seconds. carry inherited game/player/global limitations and additional `personal_credit_unresolved` conservatively to listed skaters. source-selected play may be atypical.

| personal evidence | counts | rates / coverage |
|---|---|---|
| positive included time | three nonnegative integers | `3600 * count / personal.included_seconds`; complete unless relevant gaps, otherwise partial |
| zero time but retained positive assist | integer counts, including that assist; shots/goals zero | all rates null; complete/partial from gaps; add `no_personal_5v5_exposure` |
| zero time, no credits, complete evidence | three zeros | null rates; complete; `no_personal_5v5_exposure` |
| zero time, no credits, relevant gaps | all counts/rates null | unavailable |

`no_personal_5v5_exposure` explains an undefined rate, not an evidence gap. recompute it for each final game/season row; a zero-time game cannot carry it into a positive-time season. do not reuse the old zero-time⇒zero-count invariant. reduce available game counts/time before the same season projection; never average game rates. any unavailable/partial contribution and `unassigned_player_games` prevent complete season coverage. all counts share availability; all rates share denominator/availability. `goals <= shots_on_goal`; assists need not be below the player's goals. retain available reductions before nullable projection in the receipt.

independently reconcile per game/season: skater time equals ten times physical personal time; skater plus goalie credits equal retained event credits; goals contribute once to both goal and shot counts; at most one primary credit per goal; player-game sums reproduce seasons. goalie credits remain receipt-only. the fivefold on-ice count multiplier does not apply to personal credit.

## publication and api

hard-cut sqlite to schema **2**, including `PRAGMA user_version=2`; keep `kind:observed_5v5` and on-ice `population_version:matched_attempts_v1`. add `personal_population_version:matched_personal_credits_v1`. retain the five strict tables, finalization/receipt sequence and command interfaces. no in-place migration, dual reader or generic metric table.

| table | additions |
|---|---|
| `publication` | required literal `personal_population_version` |
| `player_game`, `player_season` | personal-prefixed columns for included/known-excluded seconds, three counts, three rates, coverage status and reason-code json |
| `game` | `personal_included_seconds`, `personal_known_excluded_seconds` for physical conservation; credit totals/dispositions remain in the receipt |

both existing api responses add required `personal` to each player summary and player-game row:

```ts
type PersonalMetrics = {
  included_seconds: number
  known_excluded_seconds: number
  shots_on_goal: number | null
  goals: number | null
  primary_assists: number | null
  shots_on_goal_per60: number | null
  goals_per60: number | null
  primary_assists_per60: number | null
  coverage_status: "complete" | "partial" | "unavailable"
  reason_codes: readonly PersonalReasonCode[]
}
// PersonalReasonCode: inherited gap reasons, excluding no_5v5_exposure,
// plus personal_credit_unresolved and no_personal_5v5_exposure.
```

sqlite uses these exact names prefixed `personal_`, with `personal_reason_codes_json`; metadata's new literal reaches the api. counts/seconds are safe nonnegative integers, rates finite nonnegative reals or null. enforce the null/zero table, valid status/reason combinations and sorted unique reasons in python, applicable sqlite checks and effect schemas. extend complete typed read-back and game→season checks. wrong versions/missing fields fail.

`GET /api/league` and `GET /api/players/:playerId` keep 05c's coherent composition, errors and read-only/no-store behavior. effect selects published values; browser formats/sorts without calculating hockey rates or credit. `Metrics` stays the unchanged on-ice type; add distinct `PersonalMetrics`, sharing only actual common formatting/coverage fields.

build/check one real candidate from the pinned local corpus and browse it on a separate loopback port for acceptance. preserve active/previous bytes; this specification assigns no activation.

**cross-version cutover, when separately assigned:** stop serving; validate old active with its old git revision and candidate with schema-2 code; verify an incoming copy; move old active to previous, incoming to active; restart compatible code. the existing operator rejects incompatible active files, so document explicit manual steps rather than weaken validation. rollback restores old database and compatible git revision. same-version rotation keeps existing commands. verify both transitions in a disposable directory. no archived builds, compatibility reader or release manager.

## views and content

content design owns definitions, labels, coverage and rendered hierarchy on every surface. say **recorded 5v5 results**, with separate `personal production` and `team attempts while on ice`. no ability labels or winner colors.

| surface | required behavior |
|---|---|
| league | sortable personal `shots on goal/60`, `goals/60`, `primary assists/60`, personal included minutes and personal coverage beside existing columns. label both minute populations. totals stay on profile/comparison to bound width |
| profile | identity/season → personal count/rate rows and existing on-ice values → each population's minutes/coverage → existing on-ice peers → game evidence. visible download action and definitions |
| comparison | extend existing aligned table with personal counts/rates/minutes/coverage; each player retains its own population. no matched-game/rank/winner claim |
| game evidence | add three personal counts, personal minutes and coverage; preserve game labels/links and on-ice evidence |
| png | one player; name/id, all season teams, reported position, season/regular-season/5v5 scope, personal and on-ice counts/rates, both minute/coverage summaries, publication date/id and both definition versions |

add sort keys `sog60`, `goals60`, `primaryAssists60`, `personalMinutes`; preserve default sort, nulls-last in either direction, exact-number order and name/id ties. discovery minimum, games and peer rules continue using **on-ice** time; clarify labels. no new filter or reliability threshold. preserve existing route queries/history/loading/pickers and separate peer controls.

personal rates display two decimals; existing on-ice rates/minutes keep one-decimal conventions, including `<0.1` minutes. integer counts; exact values for sorting. share formatting across views/export. zero is `0`; null is an explained dash; counts can remain visible with undefined zero-time rates. coverage never implies official complete totals or a fabricated percentage.

definitions: shots on goal include scored/saved shots, excluding misses/blocks; goals are already included in shots; primary assists are first credited assists, not all assists or measured passing. goal strength determines credit even after an assister changes off. personal support can be smaller than on-ice support. existing peers describe only on-ice rates. preserve global unassigned-game disclosure.

## single-player png

download from the profile's loaded response without requests/reaggregation. omit peer plots and cohort claims; interactive peers remain on-page. no comparison export, svg download, format/template choices or service. use one small browser-native self-contained svg→canvas→`toBlob("image/png")` renderer, shared content/formatting, system fonts, escaped text nodes and no external assets or `foreignObject`. no screenshot dependency.

width: 1200 pixels; height follows content. text must remain readable at 600-pixel display width; body/footer at least 24 native pixels. wrap long names/teams/reasons and grow height instead of clipping or shrinking below that minimum. use existing restrained colors, tabular numerals, spacing and section labels.

retain human-readable coverage reasons, global missing-association count when relevant, `included results; unadjusted observations, not ability`, and concise quantity definitions. publication time is not a source observation time. omit cohort metadata because no exported value depends on a cohort.

snapshot the selected response at click; disable duplicate export while rendering. accessible progress/error state, recoverable download action and object-url cleanup. filename `hockey-stats-<season>-<playerId>-5v5.png`. image supplements semantic html; every exported fact remains available as text. keyboard controls, visible focus, 320-css-pixel reflow and native 200% zoom apply. wide tables scroll inside labeled keyboard-accessible containers, not the page.

references: [descriptive card hierarchy](https://hockeyviz.com/howto/skaterCard), [accessible complex-image alternatives](https://www.w3.org/WAI/tutorials/images/complex/), [browser png export](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob). these support presentation, not private-model parity.

## implementation owners

| boundary | files / responsibility |
|---|---|
| source/data | new `analysis/src/hockey_stats/scoring_credits.py`; `observed.py`; narrowly extract goal-identity corroboration in `reconstruct.py` if needed. credit facts, personal masks, reductions and receipts; no frozen-schema change |
| publication/transport | `analysis/src/hockey_stats/publication.py`; `app/src/shared/observed.ts`, `app/src/server/publication.ts`. schema-2 columns/invariants and both response groups; existing cli shape unchanged |
| presentation | `app/src/web/explorer.ts`, `presentation.tsx`, three route files, `styles.css`; new `descriptive-card.tsx` for concrete card content/download. retain peer/picker behavior |
| content/verification | `README.md`, `fixtures/README.md`, `docs/research/observed-05d/verification.md`; definitions, checked cases, candidate commands, manual cutover/rollback and actual results |

one slice, dependency order: credits/personal contract → publication/api → views/export. agree fields before parallel work; one owner per file. reuse concrete segment, formatting and coverage mechanisms; remove redundant derivations, not supported inactive features. no research migration, generic export framework or unrelated capture refactor. source/statistical, systems and content reviewers independently challenge each boundary and the integrated result.

## acceptance

temporary integration/live red → green → refactor → green checks, independent reviews, then delete temporary tests/controllers/test-only dependencies. retain checked facts, source fixtures and receipts. no lasting harness selected under [07](07-lightweight-testing.md). documentation-only work runs no application campaign.

1. independently check raw scored/saved, explicit unassisted and goalie-credit examples. synthetic boundaries cover missing/null/malformed/conflicting primary credit, secondary-only disagreement, off-ice/zero-time assists, duplicate identity, collateral masks, own-goal credit and valid goal-free time. preserve any new distinct broken original bundle.
2. reconcile credit dispositions, unioned masks, physical/player/goalie identities and game→season reductions. no double-counted goal, invented zero or unmatched denominator. source/derived drift fails before finalization. native outputs and all prior on-ice quantities/coverage remain identical for the same corpus.
3. build a real candidate covering all 1,312 inventory games; report supported personal games/time/credits, additional losses and unresolved reasons. no assumed coverage floor or full-season validity claim from fixtures. verify aggregate identities and preservation; record runtime, peak memory and candidate size.
4. verify strict sqlite→effect→browser agreement, malformed candidates, nulls/zeros, trades and unchanged on-ice peer membership. pinned typecheck/build pass. disposable-directory old/new code-and-database cutover/rollback succeeds; schema-2 code rejects schema 1.
5. exercise table sort/filter → profile → compare → game evidence, back/forward/reload and peers. check two-decimal formatting, exact sorting, long/missing identities, differing personal/on-ice coverage and zero-time positive assists. no extra fetching or stale identity/value pairing.
6. save/inspect actual png files for ordinary, long-name/traded and partial/unavailable cases; reconcile every exported fact to the response. check failure and keyboard behavior, 600px image readability, native 200% zoom and 320px html reflow. browsing/export works without raw inputs, python, external network or hdd.

completion means a verified candidate and coherent views/export, not activation or admission. costs: narrower personal support, occasional distinct minutes, collateral exclusions, new source reads, schema rebuild/manual cross-version rollback, wider tables and a noneditable png. personal distributions, percentiles, usage enrichment and spatial views remain separately scoped.
