# pr05c — observed player explorer

status: **full specification; implementation unassigned.** user choices confirmed 2026-10-20: reported forward/defense peers by default, including separate groups for a mixed-position pair; adjustable peer minimum of 300 included minutes. [the plan](../plan.md) owns progression. independent of 04l and model admission. [brief](../brief.md) · [architecture](../architecture.md) · [05b contract](05b-observed-comparison.md)

## target and boundary

discover a player in the existing league table, inspect a compact observed profile with raw-rate peer context, compare two players, and reach their game evidence without losing navigation context. the final state is three improved existing routes, one coherent publication per view, and two directly inspectable distributions: **on-ice attempts for/60 and against/60**.

these are unadjusted recorded results while a player was on the ice, not personal shot totals or estimates of contribution. attempts include scored, saved, missed and blocked shots. differing teammates, opponents, deployment, included games and coverage remain part of the comparison. preserve completed-season genuine 5v5, localhost-only operation and detached browsing.

no new hockey metrics, percentiles/ranks, differences/net scores, uncertainty bands, adjusted values, xg, spatial maps, personal scoring, export, date windows or historical season selector. no acquisition, fitting, python change, database rebuild/rotation, hosting, account, cache/store, chart dependency or component framework. [05d](05d-descriptive-cards.md)/[05e](05e-spatial-views.md) retain later capabilities. no fictional skill placeholders on real profiles.

## discovery versus reference

these are distinct controls on different pages; table filtering never silently changes a chart's reference.

| surface | controls / defaults | effect |
|---|---|---|
| league `/` | existing name search/sort; `position=all`, all season teams, minimum included minutes `0` | filter displayed rows only; no chart on this page |
| profile `/players/:playerId` and `/compare` | `peers=position`, `peerMin=300`; explicit `all` alternative | choose chart background only; never change selected identities, their quantities or game evidence |

league filters intersect. group forwards as reported `C/L/R/F`, defense as `D`; preserve original reported position in identity text. minute filtering compares exact `included_seconds >= 60 * min`, before rounding. zero minimum retains zero-exposure/unavailable players. name matching, sort directions, nulls-last ordering and name/id tie-breaking reuse existing behavior. no automatic rate sort or inferred winner.

season-team options come from the complete response's `teams[]`, keyed by team id and deterministically ordered by label/id. use existing missing-abbreviation fallback; if one id has conflicting non-null labels, show `team <id>` rather than choose arbitrarily. selecting a team matches membership in the published season list; retain the player's entire team list and whole-season values. copy: `matches listed season teams; results still cover all included season games.` no team-only aggregation. show visible count against all published players; zero matches identifies active filters and offers clear filters. clear filters resets `q/position/team/min`, preserving sort.

comparison pickers continue searching all published players under 05b, independently of either filter set. league discovery starts without a cutoff, so low-minute names remain discoverable by default. deliberate table filters can hide them; never override filters because a search happens to match.

## peer contract

`position` means the selected player's reported forward/defense group, not exact center/wing matching or verified deployment. `all` explicitly uses all skaters. use one common `peerMin` for both selections. same-group pairs share one background; mixed pairs in position mode have separately labeled forward and defense backgrounds. all mode always has one background. no automatic population switch on an existing explicit all-mode choice.

membership is the chosen group, exact `included_seconds >= 60 * peerMin`, positive included seconds and available published rates. current `Metrics` invariants make both rates available together: both figures use the same members. each player contributes one equally weighted observation, including eligible partial records. an eligible selected player is already a member; highlighting never appends or counts it twice. no time weighting, complete-only restriction or inferred coverage fraction.

each background states its group, minimum, member count and partial-member count: e.g. `reported forwards · at least 300 included 5v5 minutes · <n> players, <p> partial`. include `one mark per player; shared play means these are related observations. the cutoff is a viewing rule, not a reliability threshold.` known global gaps remain visible through `GlobalGap`; covered still means no known relevant gap within listed evidence.

- a below-floor selection retains its card and finite highlighted rates, labeled `outside reference: under <m> included minutes`; it contributes nothing to member count.
- null rates have no mark: show the existing unavailable value/reason, never zero. zero rates remain at their actual coordinate. zero included exposure is outside the reference even when the floor is zero.
- an empty background says `no players meet this peer rule`; retain finite selected highlights, clearly without peers. one member is valid. if no background or selected value is available, show text instead of an invented axis.
- neither reference membership nor position matching implies equal exposure, independent samples, precise separation or ability ranking.

## urls, navigation and loading

| route | owned query keys |
|---|---|
| league | existing `q/sort/dir`; `position=all\|f\|d`, `team=<HockeyId>` or absent, `min=<minutes>` |
| profile | `peers=position\|all`, `peerMin=<minutes>` |
| comparison | existing `a/b`; `peers/peerMin` |

use ordinary labeled selects for group/team and a nonnegative whole-minute input with an explicit apply action for each minute setting. drafts stay local until enter/apply; invalid drafts show an inline error and leave committed results unchanged. accept canonical decimal integers whose product with 60 is a safe integer, including zero; no arbitrary hockey-specific upper limit. new select/applied-minute changes push one history entry and prevent scroll reset; unchanged values do nothing. existing league search typing still replaces history; preserve existing sort and 05b pair-selection semantics. peer edits must not clear picker drafts; pair changes still do.

`reset peers` restores `position/300`, preserving selected ids; `clear filters` restores discovery defaults while preserving sort. both reset their own minute draft/error even when committed defaults already hold, and navigate only if owned query values change. when a committed minimum changes through back/forward, normalization or apply, replace its draft and clear its validation error. unrelated filter changes do not discard a pending minute draft. every query mutation/normalization preserves the route's existing `leagueSearch`/`comparisonSearch` return state explicitly.

parse new controls with `getAll`. absent keys use declared defaults; repeated, empty or invalid presentation values normalize only their own key to default via history replacement. a well-formed team id absent from the publication remains selected as `team <id> — not in this publication`, yielding no rows until cleared; do not substitute another team. unknown keys are ignored/preserved. retain 05b's visible invalid/repeated/unknown/duplicate `a/b` handling without normalization. default-valued keys may be omitted; control labels always show the effective values.

league links start profiles/comparison with peer defaults and preserve the complete league query in existing `leagueSearch` history state. profile → new comparison carries the profile's `peers/peerMin` in the destination query, plus its id as `a`; comparison → profile and peer-table → profile carry current peer settings in the actual query. selected profile links from comparison also retain its full `comparisonSearch` and `leagueSearch`. back links restore the recorded destination context, not settings changed later on another page. peer-table links preserve any existing return context; they do not invent a previous comparison. direct links/reload retain their own query settings; absent return history means the default league page. build known local paths using query strings, preserving the existing `historySearch` boundary.

same-path changes limited to a route's presentation keys reuse loaded data through `shouldRevalidate`. profile id changes, normal route entry, reload and explicit retry retain normal fetching. no request for typing, filter/peer edits or pair-only changes. use one client-loader request per entered view; avoid additional effects/refetches. preserve loading/error/retry behavior and never render old values under a new player name. an incomplete/invalid pair keeps pickers and errors but renders neither comparison results nor peer figures; selecting the pair reveals its current peer controls.

## coherent transport and ownership

hard-cut the existing profile response; no new endpoint or compatibility branch:

`GET /api/league` retains `{ publication, coverage, players: PlayerSummary[] }`. `GET /api/players/:playerId` replaces the singular `player` field:

```ts
type PlayerResponse = LeagueResponse & { readonly games: readonly PlayerGame[] }
```

compose `PlayerResponse` from `LeagueResponse.fields` plus `games` in the existing effect schema. `PublicationReader.player(id)` reads the full player list once, returns absent if the id is missing, then reads only that id's games from the same existing readonly publication handle. every player id appears once, as required by the existing database keys/join. `loadPlayer(id, signal)` keeps its interface; the route derives its selected row from this returned list. unexpected absence in a successful response is a load error, not empty peer data. existing 400/404/500 behavior, no-store responses and manual stop/replace/restart publication remain.

the card, peer groups, global coverage, season header, games and evidence all use this one response. league/comparison still use one `LeagueResponse`. no independent profile-plus-league requests, client revision handshake, hot switching or cached cross-route merge. the profile payload grows by one league list; this is acceptable for the existing single-season population and eliminates ambiguous response composition. sqlite and python contracts remain unchanged. remove the now-unused filtered `readPlayers(id)` branch rather than retain a legacy path; keep the game reader's existing uses.

python remains authoritative for counts, rates, exposure and analytical eligibility. the application only selects published rows, groups their reported positions, lays out their supplied values and formats them. never recalculate rates from counts/time. peer size and chart geometry are presentation, not new hockey quantities.

| files / owner | bounded responsibility |
|---|---|
| `app/src/shared/observed.ts`, `app/src/server/publication.ts` | profile transport cutover and composition; no new sql tables or publication lifecycle |
| `app/src/web/explorer.ts` — new | explicit discovery/peer query parsing and pure membership selections; reuse `matchingPlayers`/`nameOrder`; no generic filter registry |
| `app/src/web/peer-distributions.tsx` — new | shared peer controls, two svg figures and accessible peer-values tables; receives players, selections, settings and change callback; owns no url or fetch |
| `app/src/web/routes/league.tsx` | discovery controls, query/history and existing table |
| `app/src/web/routes/player.tsx` | coherent loader selection, compact observed profile, peer section, preserved game evidence/navigation |
| `app/src/web/routes/compare.tsx` | preserve pickers/aligned metric table; add shared peer section and peer query propagation |
| `app/src/web/presentation.tsx`, `root.tsx`, `styles.css` | reuse names/units/coverage/evidence; update profile loader type where necessary; scoped integrated typography/layout |
| `README.md`, `docs/research/observed-05c/verification.md` | brief use instructions and actual acceptance/evidence receipt |

the two small presentation interfaces are concrete: `readDiscovery(search)` returns discovery values and normalized search parameters; `readPeerSettings(search)` does the same for `peers/peerMin`. each normalizes only its owned keys. `selectDiscovery(players, discovery)` returns filtered/sorted published rows; `selectPeerGroups(players, selected, settings)` returns `{ key: "all" | "f" | "d", members: readonly PlayerSummary[], selected: readonly { player: PlayerSummary, slot: 0 | 1 }[] }[]`. preserve original selection slots for markers; group order is forwards then defense when split. `PeerDistributions` receives `players`, one/two valid `selected` rows, `settings`, `onChange(nextSettings)` and route-built `profileLink(playerId) -> { to, state }` carrying return context. its reset clears its local draft/error and calls `onChange` with defaults; the route alone decides whether to navigate. these are presentation values, not new wire schemas.

keep the route's url ownership explicit. share concrete cohort arithmetic, formatting and figure rendering; do not force the profile's definition list and comparison's native table through a universal card configuration. existing `client.ts`, picker, route registration, server handlers, dependencies and capture commands need no behavioral change. remove only derivations/markup made redundant by this slice.

## content and visual contract

the content designer reviews each surface before implementation and its rendered result afterward:

| feature | required hierarchy / good content |
|---|---|
| discovery | compact purpose heading → clearly labeled filters → visible/all count → sortable table → evidence. controls wrap; identity and rates remain scannable. no per-row comparison-selection state |
| observed profile | player identity/teams/reported position → `observed on-ice results` card with prominent for/60 and against/60 → matched minutes, counts and games with included time → visible coverage summary → peer context → listed-game evidence. keep the existing full coverage/reason details and publication evidence; `view game evidence` anchors to the existing table |
| comparison | existing heading/pickers/global gap → existing aligned quantities and coverage → peer controls and figures → publication evidence. no duplicate pair of full cards or winner column; both profile links retain the evidence journey |
| peer context | explicit reference controls/counts → two rate figures → selected numeric values and outside-reference notices → expandable numeric peer tables. a reader can identify population, units, exposure and limitations without hovering |

use the existing restrained sheet, system fonts, tabular numbers, focus styles and link accent. organize the card with typographic hierarchy and spacing, not ornamental panels. preserve original names and identifiers; new explanatory prose is lowercase. reuse `Minutes`, `Quantity`, `CoverageDetail`, `GlobalGap`, `Evidence`, `playerName` and `teamName`. integer counts and one-decimal display remain; membership, ordering and positions use unrounded values. preserve `<0.1` minutes with accessible exact seconds, covered zero versus unavailable zero, and partial coverage with zero known excluded time. do not manufacture a coverage percentage or sum overlapping game counts.

figures are **horizontal rug plots**: one short neutral mark at each member's exact rate coordinate, equal treatment per player, no vertical data dimension. overlap is permitted and stated; no random jitter, density fit, clipping or aggregation that changes a value. draw selected markers in a separate labeled band within their own group's lane; use circle/diamond plus name/value to distinguish slots, not color alone. mixed-pair highlights appear only with their respective group, never duplicated across both backgrounds. tied selections retain separate label rows at the same x-coordinate. selected eligible members remain in the rug exactly once; the highlight is an annotation.

render two figures, `on-ice attempts for/60` and `on-ice attempts against/60`. each has one lane, or named forward/defense lanes for a mixed pair. use one shared linear domain/ticks across both figures and all lanes on that page, covering every finite peer and selected value. the domain may start above zero because these are point locations, not bar lengths; show its numeric endpoints, use readable ticks, provide space at extremes and expand a constant domain finitely. every axis increases rightward, including against; no good/bad colors or rank alignment. extreme valid values remain visible even if they compress the rest. plots can rescale when peer membership or selections change; never animate data into an apparent trend.

each figure has a visible title/caption and accessible short description including group/units and where numeric values are available. provide one expandable native peer table per distinct group, generated from the same membership list: linked name, reported position, included minutes, for/60, against/60 and coverage. deterministic name/id ordering; selected rows have visible `selected` or `first/second` text, without adding outside-reference rows. selected values/reasons are already visible outside these tables. individual svg marks are not controls or hundreds of tab stops; no hover-only evidence. captions say `marks overlap; values are available below` and `spread describes observed player results, not uncertainty about ability`.

controls, captions and names reflow at 320 css pixels; tables may scroll within labeled keyboard-accessible containers. charts fit the content width with readable labels/ticks; no page-wide overflow, sticky layout system or horizontally compressed text. maintain keyboard input/apply/reset, focus and polite result-count announcements. references: [tables](https://hockeystats.com/stats/skaters), [jfresh card preview](https://hockeystats.com/cards/player-cards), [hockeyviz descriptive card](https://hockeyviz.com/howto/skaterCard); borrow comparative hierarchy, not their different statistical meanings. [accessible chart alternatives](https://www.w3.org/WAI/tutorials/images/complex/) · [reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

## delivery and acceptance

one cohesive slice, with non-overlapping implementation owners: **transport** owns schema/reader; **presentation logic** owns query/membership helpers; **interface** owns route integration/figures/styles. agree the two small presentation contracts before parallel work; one owner edits each file. **content design** owns the hierarchy/labels above for all three surfaces; independent review checks statistical meaning, systems behavior and rendered usability. no separate campaign controller or design framework.

use temporary end-to-end/integration/live red → green → refactor → green checks, adversarial review, then delete temporary tests/controllers/test-only dependencies. retain useful checked fixture facts and the receipt. [07](07-lightweight-testing.md) owns separately selected lasting checks; this slice selects none. no source re-audit or unrelated historical migration.

1. build/typecheck with current pins. verify the real profile endpoint returns the coherent new shape, with the selected row and every peer value equal to the existing league response from that publication; game rows retain their existing values. the old singular-player contract is removed everywhere. ordinary profile 400/404 and read failures remain errors.
2. built app/current local publication: league search + position/team/minute filters + sort → profile → comparison → either profile/game evidence → back. verify direct reload, copied profile/compare queries, back/forward, clear filters and peer reset. filters preserve exact whole-season quantities, including trades. log actual publication identity/counts; do not hard-code 940 or assume every player has data.
3. independently enumerate membership ids, partial counts, values and highlight membership. cover exact `60*m-1`, `60*m`, `60*m+1` seconds; all four forward codes and defense; min zero; eligible selection counted once; below-floor/outside selection; null versus zero/tiny exposure; mixed groups; all-skater mode; all-equal rates; empty/single-member groups; tied highlights and extreme rates. use small explicitly synthetic typed responses through the same client/browser boundary where real data lacks these cases.
4. reconcile rendered coordinates against supplied unrounded rates and the declared shared domain; numeric tables have exactly the same member ids/values as their rugs. unavailable values make no marks. changing name/team discovery never changes reference settings; changing peer settings never changes player metrics/games. partial coverage, global unassigned gaps and fixture markers remain visible. no inferred ability or reliability language.
5. record request counts: one profile request, no second league fetch; one league request on league/comparison entry; none for typing or presentation-only changes. use delayed/failed and successive synthetic publication responses to verify one-response coherence, retry, absent selections and no stale name/value combination. normal route changes may load a newer publication as a whole; do not activate/replace the real database for this check.
6. keyboard-only filter/apply/reset/picker/profile/back flows; native browser 200% zoom, 320px viewport, long/duplicate/missing names and coincident labels. inspect actual chart/table rendering and numeric accessibility; record native zoom separately from viewport approximations. no requirement for each mark to be focusable. current production routes still reload directly and retain existing api/asset error behavior.
7. browse built assets with only the current local publication: no external-drive/raw/upstream requests and no republication. independently review the integrated content and contracts after green; repair concrete defects at their owning layer, rerun affected checks, then remove temporary verification code. receipt distinguishes real/synthetic/manual checks, remaining limitations and accepted costs.

completion is useful discovery and truthful peer context from existing evidence. accepted costs: larger profile responses, independent table/reference controls, no noise correction for low exposure, overlap in compact plots, separate peer populations for mixed positions, possible axis compression by extremes and later presentation changes for supported ability. no model admission follows.
