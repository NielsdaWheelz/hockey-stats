# pr05b — two-player observed comparison

status: **full specification; ready for handoff.** independent statistical, systems and content reviews cleared. docs only; [the plan](../plan.md) owns implementation assignment. confirmed on 2026-10-17: a dedicated comparison page plus a profile shortcut, without league-row selection controls. independent of 04h and model admission. [brief](../brief.md) · [architecture](../architecture.md) · [05a contract](05a-observed-website.md)

## target and boundary

choose two distinct skaters from the active completed-season publication; inspect their existing recorded on-ice 5v5 counts, rates, matched minutes and coverage side by side; open either profile's game evidence and return to the pair.

both columns and publication evidence come from **one `LeagueResponse`**. each player's counts and time describe that player's own included evidence. common season/definitions/units do not imply common games, opponents, teammates or missingness. this is descriptive comparison, not an estimate of individual contribution.

no new metrics, browser-derived differences/ratios/net values, ranking/cohort filters, percentiles, distribution charts, xg, adjusted maps, date windows or common-game recomputation. no new endpoint, database schema, exporter, acquisition, fit, publication, retained dependency, cache/store, hosting or public/lan access. use the current local publication; the hdd and python are unnecessary. supported ability remains a separate destination.

## interaction and url contract

route: `/compare?a=<first-player-id>&b=<second-player-id>`. ids remain strings, checked with the existing `HockeyId` contract; preserve slot order. no automatic defaults or preselected prominent players.

- league heading: one `compare players` link to `/compare`, carrying existing `leagueSearch` history state.
- profile: `compare this player` links to `/compare?a=<id>`, carrying that same league return context.
- each slot has a labeled name search, selected identity, explicit `clear first player` / `clear second player`, and result buttons. a committed change updates only its own query key in one router navigation, pushes history and prevents scroll reset. explicitly carry `leagueSearch` state on every such navigation; router navigation otherwise drops it. if the resulting url is unchanged, do not navigate or refetch; this includes choosing the current id or clearing an absent slot. do not rewrite the other slot.
- search drafts stay local. typing never changes the selected player or url. clear drafts on committed pair changes, including back/forward; reload starts empty drafts with the committed ids restored.
- comparison has `back to players`, restoring `leagueSearch` when present. its profile links carry `comparisonSearch` and existing `leagueSearch`; the profile's `back to comparison` link carries `leagueSearch` onward again, alongside its existing `back to players`. history values are query strings only; build destinations on known local paths, not arbitrary return urls. absent context uses the unfiltered league page.
- direct comparison links/reloads preserve the pair. copied/new-tab profile links lack comparison return context and return to players; no profile-query expansion or persistent selection store.

parse each slot independently with `URLSearchParams.getAll`:

| input | visible state |
|---|---|
| key absent or one empty value | unselected; prompt to choose that slot |
| repeated key or noncanonical id | inline `invalid first/second player selection; choose a player below` |
| canonical id absent from loaded rows | inline `player <id> is not in this publication` |
| two valid identical ids | retain first slot; mark second `choose a different player` |
| two distinct present ids | render the comparison |

retain invalid query values until the user replaces/clears that slot; no silent coercion/substitution. ignore unknown query keys. render no metric table until both slots are valid and distinct; keep the valid identity and both pickers available for repair. a valid player with unavailable metrics remains selectable.

## picker and navigation behavior

reuse the league's lowercase/unicode-decomposition/accent-removal, whitespace-token AND substring name matching, including `playerName` fallback. extract the actual shared matching/name-order helpers; preserve existing league search/sort behavior. order results by display name, then the existing decimal-string id tie-breaker. exclude the other valid selected player; no position, exposure or coverage cutoff.

empty/whitespace search shows `search by player name`, not an arbitrary shortlist. show at most ten matches with their name/fallback, season teams, reported position and id; show total matching count, and `showing 10 of <n>; refine this name` when truncated. zero matches: `no other players match this name`. selection is explicit even for one result.

use a small `PlayerPicker` component with ordinary labeled search inputs, lists and buttons; no combobox/listbox roles or custom arrow-key protocol. tab, enter and space must work. each result's accessible name includes the player name, id and destination slot, disambiguating duplicate names. after selection/clear, keep focus at that slot's stable input and announce its committed choice through one polite status message; back/forward does not steal focus. selection/search/retry must not display old values under new player names.

the route owns committed ids and validation. the picker receives its slot, loaded players, selected identity/error, other valid id and choose/clear callbacks; it owns only draft search and local focus. URL changes remain in the route, with pair-change notification clearing drafts.

this trades up to ten button tab stops for visible, explicit choices and simple state. no new control library or general picker framework.

## data, composition and files

`routes/compare.tsx` owns `clientLoader -> loadLeague(request.signal)`, selection parsing and the page. one typed effect-client fetch on entry/reload/retry; no `loadPlayer` calls in this view. both headers, metric columns, shared heading and disclosures use that response. selecting/clearing/back-forward changes limited to `a/b` reuse loaded data through `shouldRevalidate`; explicit revalidation and normal route entry keep router defaults. draft typing performs no navigation or fetch.

the existing schemas remain authoritative: `LeagueResponse={publication,coverage,players:PlayerSummary[]}`; the comparison selects two rows, not a second derived transport model. python remains the sole owner of quantities; effect reads/validates; react selects and formats. do not recompute rates from counts/time or merge profile summaries across requests.

| owner / files | exact change |
|---|---|
| `app/src/web/routes/compare.tsx` — new | route loader/revalidation, slot states, page and explicit metric rows |
| `app/src/web/player-picker.tsx` — new | two instances of the bounded local name picker; no data fetching |
| `app/src/web/presentation.tsx`, `routes/league.tsx` | share matching/name-order helpers with preserved league behavior; reuse `Minutes`, `Quantity`, `CoverageDetail`, `Evidence`, `playerName`, `teamName`; make `GlobalGap` copy apply to every displayed player |
| `app/src/web/routes.ts`, `root.tsx` | register `compare`; include its loader in publication/season selection; before any response, omit the season instead of asserting the hard-coded 2025–26 |
| `app/src/web/routes/player.tsx`, `routes/league.tsx` | profile shortcut, single league link and narrow return navigation |
| `app/src/web/styles.css` | scoped picker/comparison styling within the existing statistical sheet |
| `app/src/server/main.ts` | explicitly serve the document for `/compare` (and trailing slash); preserve api/missing-asset errors, loopback and cache rules |
| `README.md`, eventual `docs/research/observed-05b/verification.md` | route/use instructions, checks, actual publication identity and limitations |

no changes to shared response schemas, sql reader, capture commands or analytical code are needed. remove only code made redundant by the shared-helper extraction; no unrelated cleanup. existing `LoadError` handles failed league reads with retry/back. query-selection problems are local page states, not a 400/404 fetch failure. an empty published player list is successful data: explain `no players are available in this publication` and retain evidence.

## content and visual contract

the content designer owns this exact hierarchy: shared season/population heading → `compare included results` and short explanation → two pickers → global gap when present → comparison → publication evidence.

copy: `each player's own included evidence and matched 5v5 time; these are unadjusted on-ice observations, not estimates of individual contribution.` explain that attempts “for” are by the player's team while on ice, not personal shots. attempts include scored, saved, missed and blocked shots; 04h's unblocked research population does not change this view.

one native table has three columns: metric / first player / second player. column headers link to the corresponding profiles and show season teams plus reported position. explicit row order/mapping:

| label | existing source |
|---|---|
| matched 5v5 minutes | `metrics.included_seconds` through `Minutes` |
| games with included time | `games_with_included_time` |
| on-ice attempts for/60 | `metrics.for_per60` |
| on-ice attempts against/60 | `metrics.against_per60` |
| on-ice attempts for | `metrics.attempts_for` |
| on-ice attempts against | `metrics.attempts_against` |
| coverage and reasons | `CoverageDetail(metrics)`, including visible known excluded minutes |
| listed games | `listed_games` |
| partial games with included time | `partial_games` |
| unavailable listed games | `unavailable_games` |

caption: `each player's counts and time come from their own included evidence; included games can differ.` beside coverage explain: partial games are a subset of games with included time; roster listing is not an appearance claim; known excluded time is not a complete missing-time denominator. never sum these overlapping game counts or calculate a coverage percentage.

reuse integer counts and one-decimal minutes/rates, including positive time below six seconds shown as `<0.1` with exact seconds accessible. zero is zero; null is an em dash with its existing reason and visible coverage explanation. covered zero exposure has count zero but null rates; unavailable zero exposure has null counts/rates. positive exposure can have real zero rates. known excluded minutes can be zero while coverage is partial.

show `GlobalGap` once with its complete unassigned-game disclosure: every summary carries this limitation; it need not be attributable to either selected player. use neutral shared copy: `included results may omit games for any player.` show `Evidence` once with publication identity/retrieval, overall coverage and the existing fixture-purpose marker when applicable. retain missing-name/team fallbacks and traded players' published team list. no winner colors, difference column, arrows, ranks or unsupported ability labels.

retain the restrained sheet, system fonts, tabular numerals, visible focus and link accent. use a caption, column headers and `scope="row"` metric headers ([table guidance](https://www.w3.org/WAI/tutorials/tables/two-headers/)). keep aligned comparison columns on narrow screens; wrap names/reasons, override inherited nonwrapping headers and the coverage minimum width within this view, and allow keyboard-accessible horizontal scrolling when needed. keep the metric column visible without consuming the viewport. no separate card dashboard, sticky-toolbar system or chart.

good content lets a reader identify the players, units, exposure and evidence limitations before interpreting a numerical contrast, and reach supporting game rows without losing the pair.

## delivery and acceptance

one cohesive implementation slice; avoid parallel writers or separate harnesses for the same route. non-overlapping responsibilities:

1. **implementation:** owns all listed application changes: route/picker/helper extraction, loader, navigation, document fallback, shared heading and styling. source/schema owners remain unchanged.
2. **content design:** owns the copy/row/layout contract above and rendered inspection of names, trades, unequal exposure, missingness and coverage. review this contract before coding and the integrated view afterward.
3. **independent verification:** owns the integration evidence and adversarial statistical/systems/content review after green, including one-publication meaning, url/history behavior, direct reload and accessibility. record results in the verification receipt. use existing commands; no runner or new framework.

temporary end-to-end/integration/live red → green → refactor → green checks; independent adversarial review; then delete temporary tests/controllers/test-only dependencies. retain useful checked fixtures/facts and the verification record. [07](07-lightweight-testing.md) owns separately selected lasting checks; this slice selects none.

- build/typecheck with existing pins. demonstrate the new production route returns the shell on direct reload, uses `no-store`, and preserves real errors for unknown api/assets.
- use the built app and current real publication: filtered/sorted league → comparison; profile shortcut → second selection; comparison → profile/game evidence → back; pair edits → return to the original filtered/sorted league; back/forward → direct reload. verify both displayed columns/metadata against the single decoded league response and each existing profile; no source/export re-audit.
- record request counts: one league request on entry; none for typing or pair-only changes; explicit retry/re-entry can fetch. exercise delayed/failed loading and a coherent replacement response where one selected id is absent, without activating/replacing the real database. no mixed-publication columns or stale data under changed names.
- use small explicitly synthetic typed league responses through the same browser/client boundary for missing/repeated/malformed/unknown/duplicate selections; empty player list; zero/null/tiny exposure; missing names; duplicate display names; trades; global gaps; partial coverage with zero known excluded time; and a non-2025–26 publication. preserve 05a's semantic invariants: a global unassigned gap propagates to player-season status/reasons. failed transport/decoding remains a load error, not “no players”.
- keyboard-only selection/repair/clear/return, visible focus, result announcements, narrow viewport and 200% zoom. inspect actual rendering and reconcile table rows; a screenshot alone is insufficient.
- browse with only built assets and the existing local publication, without external drive/raw inputs or upstream requests. no publication rebuild/rotation, capture regression suite or research campaign. record which checks used real versus synthetic evidence.

current read-only inspection found 940 published players: 880 partial and 60 covered, with 81 multi-team players; no zero-exposure season row or global unassigned gap. real-only checks cannot cover missingness. implementation records its actual publication identity rather than hard-coding these counts.

completion is a usable, truthful two-player observed comparison with preserved existing league/profile behavior. costs: more clicks than league-row selection, bounded button navigation, complete league-response loading on route entry, no common-game adjustment, and possible later presentation changes for supported estimates. independent historical scientific verdicts remain untouched.

routing choices follow the installed framework's [url-state](https://reactrouter.com/api/hooks/useSearchParams) and [route-module](https://reactrouter.com/start/framework/route-module) contracts; retain current pins, not a framework upgrade.
