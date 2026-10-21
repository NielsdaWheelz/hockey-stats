# 05c player explorer verification

status: complete; all seven acceptance boundaries and independent reviews pass. temporary integration/live tests and native-zoom controls are deleted after final green. [the plan](../../plan.md) owns progression. these are observed results and software checks, not model admission.

## delivery and ownership

the user assigned the entire [05c specification](../../specs/05c-player-explorer.md) on 2026-10-20 in branch `codex/05c-player-explorer`, worktree `/Users/nnandal/Documents/code/hockey-stats-05c`. base: `88e3e7f`. input commit `9004cad` preserves the primary checkout's current documentation drafts separately from implementation. application producer: `05e7dc4631c5a4e7ec481afba7d3e27a7c9065f4`.

three non-astra native subagents own transport/selection logic, interface implementation and independent temporary integration/live verification. content hierarchy is reviewed before implementation and after rendering. the primary agent integrates the work, challenges each boundary, verifies native zoom and preservation, and records acceptance. implementation owners cross-review one another's contracts; the verifier makes no production edits.

`observed.ts` and the existing readonly reader own the hard-cut profile response: league fields plus selected-player games. `explorer.ts` owns explicit query parsing, discovery selection, reported-position peer membership and season-team options. routes own urls, history and one loaded response. `PeerDistributions` owns local reference drafts, shared geometry, figures and numeric alternatives; it owns no fetching or navigation. existing formatting, coverage, evidence and picker primitives remain authoritative.

python, sqlite tables, publication commands, dependencies and lockfile are unchanged. there is no singular-profile compatibility path. obsolete filtered-player reading, profile markup/styles and duplicate peer sorting are removed. the application formats published hockey values without deriving new rates or analytical eligibility.

## publication and evidence

evidence root: `/Users/nnandal/Documents/code/hockey-stats-local/05c-verification/`. `before.json` and `preservation.json` identify the protected publication and actual surrounding repository state.

the active file is `/Users/nnandal/Documents/code/hockey-stats-local/publication/active.sqlite`, publication `ae011202-6e2f-41d6-9528-ef02d73b477e`, season `20252026`. it contains 940 published players. size: 5,873,664 bytes; sha-256: `d49d2b8f3342c03d8ce4430330e9df2a9368671b6eefab399f40a7a02946ecb0`; nanosecond mtime: `1792216826902185233`. bytes, mtime and the directory's sole `active.sqlite` entry remain unchanged after checks and cleanup.

real transport checks compare the checked profile’s entire summary list with the league response, verify unique player ids and preserve all 82 baseline game rows for `8470613`. the real browser journey uses traded player `8470621`, preserving both `TBL`/`LAK` and all whole-season values while filtering by one season team; its profile has 72 listed game rows. an independent enumeration matches all 438 default forward peers. `transport.json` and `real.json` retain these results.

synthetic edge populations enter through the same typed browser client boundary. they never replace the real database. `synthetic-facts.json` retains the explicitly synthetic response, checked member ids, partial counts and boundary facts without executable tests. cases include 17,999/18,000/18,001 seconds, all five reported position codes, zero and unavailable exposure, partial records with zero known exclusions, tiny exposure, mixed slots, empty/single/constant populations, tied highlights and rates through `Number.MAX_VALUE`. the largest accepted minute input is `150119987579016`; the next integer is rejected because its seconds are unsafe.

## acceptance

node `24.21.0` runs both type checks, the production build and live servers. `pinned-typecheck.log` and `pinned-build.log` pass. final checks use the committed application producer above. `browser.json` records eleven passing browser groups; `journey.json`, `real.json`, `transport.json`, `helper-final.log` and `native-zoom.json` cover the remaining boundaries. `adversarial-final.json`, `contracts-review.json` and `interface-content-review.json` clear statistical meaning, systems behavior, source contracts and rendered usability with no remaining blocker.

| spec boundary | final evidence |
|---|---|
| 1 — transport/build | full profile list exactly equals league values and coverage; selected games unchanged; old singular field absent; real 400/404 and no-store preserved; pinned typecheck/build pass |
| 2 — complete journey | real and synthetic league filters/sort → profile → comparison → either profile/game evidence → recorded return destination; peer-table context, copied/direct queries, reload, back/forward, clear/reset and keyboard selection pass |
| 3 — membership | independently checked ids/counts at exact-second thresholds; discovery zero floor retains unavailable rows, peer zero floor requires positive exposure; selected eligible rows counted once; original mixed-pair slots, partial membership, empty/single groups and outside selections preserved |
| 4 — geometry/meaning | both figures and all lanes share one declared finite domain; mark coordinates reconcile to unrounded supplied rates; tables use the same ids/values; null has no mark, zero stays zero; global gaps, fixture markers and coverage remain visible |
| 5 — loading | one request per entered view, no second league request on profiles; no requests for typing, discovery/reference edits or pair-only changes; delayed/successive synthetic responses preserve whole-response identity; retry and absent-selected load error pass |
| 6 — access/rendering | keyboard-only filters/apply/reset/pickers/profile/evidence/back, actual destination focus, labeled local table scrolling, long/duplicate/missing names, tied marker labels and 320-pixel reflow pass; native 200% zoom passes separately |
| 7 — detached/review | built routes use the existing local publication; observed browser requests remain on loopback; no acquisition, raw processing, fitting or publication replacement; independent final source/content/statistical/system reviews clear before test deletion |

read-error/retry checks use an explicitly synthetic `ReadFailure` 500 response. no real database i/o fault is induced. direct production documents preserve peer queries; missing assets and unknown api routes retain 404 behavior. browser checks use cached chromium; no cross-browser claim is made.

native zoom uses a temporary browser extension calling `chrome.tabs.setZoom(2)` and verifying `getZoom() === 2`. measured `innerWidth` is 640/320 against `outerWidth` 1280/640, with device-pixel ratio 2. all three routes pass at both widths without page-wide overflow. final compositor viewport captures show actual plots, markers, captions and numeric endpoints. blank initial playwright clips were rejected; final images use `Page.captureScreenshot` after native scrolling and paint. this is browser zoom, separate from synthetic 320-pixel viewport checks.

## adversarial findings and refactor

initial red checks fail on the old singular response, absent discovery controls and absent card/figures. independent review then repairs concrete defects at their owners:

- native game-evidence and skip links discarded router return state. local focus/scroll now preserves the url, history and return context, and moves keyboard focus to the actual target.
- applying unchanged explicit defaults created history entries. routes compare effective committed values before navigation; clear/reset still clear their own drafts/errors at defaults.
- close unequal rates produced identical rounded axis labels; exact floating endpoint labels then wrapped poorly at narrow native zoom. the shared domain rounds its bounds outward to whole units after finite constant-domain expansion. observations and their linear coordinates remain unrounded; close observations receive less visual magnification.
- rug accessible text claimed exact values in one-decimal peer tables. it now promises numeric values.

post-green review removes duplicate sorting and obsolete css, preserves picker spacing, and formats the explicit rendering code. final green covers the complete refactored source. exploratory logs preserve their failures; premature post-navigation assertions and a wrongly scoped temporary selector were verification mistakes, corrected without production changes. only final passing receipts establish acceptance.

## cleanup and limits

`test-deletion.json` records removal of `/tmp/hockey-stats-05c-verification-20261020/` and shutdown of task servers on 3058/3059. `zoom-deletion.json` records removal of `/tmp/hockey-stats-05c-zoom/`, including its test controllers, temporary extension and browser profiles, while preserving native-zoom evidence. no test-only application dependency or lasting regression check is added. checked facts, images, logs and reviews remain; no temporary test/controller is retained.

at implementation handoff, the worktree, branch and built application remained for review/use through the [readme](../../../README.md#private-observed-results). the implementation and acceptance work made no writes to the primary checkout. the concurrent 04l integration independently advances main to `f172d8e`; preservation records that change rather than asserting the primary checkout stayed byte-identical. no merge, hosting or later slice was assigned at that point. the user subsequently assigned the integration and cleanup below.

accepted costs remain explicit: profiles carry a whole league list (533,405 bytes for the checked 82-game profile; league 502,311 bytes), discovery and reference controls are independent, mixed-position pairs have distinct named populations, related/partial observations receive equal marks, low exposure receives no noise correction, marks can overlap, and extremes or outward whole-unit bounds can compress visible differences. numeric tables preserve access to the supplied values at the established display precision. return destinations depend on browser history state; copied links keep their own reference query and use the default league return. later supported-ability views may require presentation changes. these limitations establish neither player ability nor a reliability threshold.

## source integration and task cleanup

the user subsequently assigned pr, merge and task cleanup. integration preserves application producer `05e7dc4` in merge ancestry and current main’s completed 04l source, fixtures, frozen evidence and scientific verdict verbatim. all eleven current primary drafts are saved under the external verification root before reconciliation: eight remain byte-identical; plan, council and 05c status combine the preserved content with completed work. the reviewed application tree remains identical to the verified producer.

the final receipt is `/Users/nnandal/Documents/code/hockey-stats-local/05c-verification/pr-merge-cleanup.json`; independent delivery review is `pr-delivery-review.json` beside it. these record the actual pr/checks/merge identity, reviewed-versus-merged tree equality, primary typecheck/build and live read, publication preservation, exact removed task resources and retained evidence. the primary checkout rebuilds and serves the existing local publication; this updates application code without rebuilding or replacing the database.

05c paths in earlier receipts name historical verification provenance; no reusable fit or source input depends on that worktree, so no alias is needed after removal. source evidence, expensive fits, the previous publication if present, existing research aliases and the main environment remain protected. no historical scientific campaign is rerun.
