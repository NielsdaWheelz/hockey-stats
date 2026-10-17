# 05b observed comparison verification

status: complete; all acceptance checks and independent reviews pass, and temporary tests/controllers are deleted. [the plan](../../plan.md) owns assignment and completion. this record concerns recorded evidence and application behavior, not scientific support.

## scope and ownership

the user assigned the entire [05b specification](../../specs/05b-observed-comparison.md) in branch `codex/05b-observed-comparison`, worktree `/Users/nnandal/Documents/code/hockey-stats-05b`, based on `0548c0f811cf662aba087846e8d47f2f3a206c6f`. one native subagent owns application implementation, one owns the temporary live checks and one independently reviews statistical, systems, content and accessibility boundaries. the primary agent owns integration, operational isolation and this receipt.

the existing python → sqlite → effect → react contract is unchanged. comparison selects two existing `PlayerSummary` rows from one typed `LeagueResponse`; it formats the supplied quantities without calculating new rates, differences or derived hockey facts. the route owns committed ids and validation. each picker owns only draft search and local focus. shared presentation helpers own the existing name matching and name/id order. no endpoint, schema, exporter, acquisition, fit, publication operation or retained dependency is added.

evidence root: `/Users/nnandal/Documents/code/hockey-stats-local/05b-verification/`. temporary controllers used `/tmp/hockey-stats-05b-checks.JA4G3Y/` and were removed after reviewed final green. the primary checkout, unrelated worktree, raw evidence, fits and publication remain outside this task's mutations.

## publication and isolation

the existing serving file is `/Users/nnandal/Documents/code/hockey-stats-local/publication/active.sqlite`, publication `ae011202-6e2f-41d6-9528-ef02d73b477e`, season `20252026`, generated `2026-10-17T05:59:42.040778Z`. its sha-256 is `d49d2b8f3342c03d8ce4430330e9df2a9368671b6eefab399f40a7a02946ecb0`, size 5,873,664 bytes and initial nanosecond mtime `1792216826902185233`. the initial directory contains only `active.sqlite`. `before.json` records protected state.

fresh typed-api inspection finds 940 players: 880 partial and 60 covered; 81 have multiple season teams. there are no zero-exposure season rows or global unassigned-player gaps. overall coverage is 1,312 inventory games, 1,280 with included time, 381 partial and 32 unavailable. these facts describe included source evidence; they do not establish player ability.

the built production server ran on `127.0.0.1:3057` with a temporary operating-system profile denying the raw corpus, analysis and fixture roots, the external drive, python execution and upstream sockets. `detached-controls.json` records direct `EPERM` denial controls and successful loopback access. no drive, host-network or existing service configuration was changed. the browser checks additionally rejected requests outside loopback. the task server is stopped after verification.

## red, green and review

`baseline-red.json` records three target failures before application changes: `/compare` returns 404, the league comparison link is absent and the profile shortcut is absent. the baseline uses the built server and current publication rather than a mocked application.

initial implementation passes typecheck and build under the shell's node `26.12.0`; those intermediate builds do not establish the pinned-runtime gate. baseline setup and every production serving process use node `24.21.0`. final pinned typecheck/build and a complete browser repeat are recorded below. independent pre-code review confirms the content/owner contract; source review checks slot parsing, pair-only revalidation, narrow query history, exact metric mapping, helper extraction, response-derived season and document fallback. review finds a stale event announcement after history or response replacement. the refactor derives one polite status from the current committed selection; no-op selection/absent clear creates no new commitment, navigation or fetch.

`initial-green.json` and `refactor-green.json` retain exploratory run names, including failed checks; neither is a passing acceptance receipt. the early checks read the url before the corresponding router render completed. observable committed-identity assertions replace those premature reads. independent review also identifies a genuine draft-reset design hazard: a passive effect permits a new pair to render with old drafts before a deferred clear. the picker now resets its single contextual draft state during render, without remounting inputs or adding a lifecycle controller. the early failures did not independently establish post-settled input loss. `journey-investigation.json` then passes the actual real league → pair → both profiles/game evidence → pair → original league journey, including shortcut, clear/reselection and reload.

rendered keyboard inspection then finds a focused profile name hidden behind the sticky metric column at an effective 195-pixel viewport. scoped css gives the metric width and native scroll padding one owner, sizes profile links to their text and bounds table width so each player column fits the uncovered scrollport. ordinary and extreme narrow layouts retain aligned rows and native scrolling; the extreme layout gains wrapping and taller rows.

## final acceptance

application producer: `b5843371058aaf9696cce283f24303c6c46bf5d6`. `pinned-static.log` records node `24.21.0`, npm `11.19.0`, `npm run typecheck` and `npm run build`, all successful. the production server and final checks use that pinned build. shared response schemas, sql reader, analytical files, package manifest and lockfile are unchanged.

the authoritative run is `final-reviewed.json`, with `final-reviewed.log` and `final-reviewed-browser-events.json`: **25 passed, zero failed**, at `2026-10-17T19:53:59.923Z`. twenty-three isolated browser contexts make 53 league and four profile requests; none attempts a non-loopback request or reports an uncaught application error. earlier run receipts retain their failures and fixture refinements; they are not the final acceptance record. synthetic player-summary reasons include their listed unavailable-game reason, preserving 05a's aggregation meaning.

| boundary | verified evidence |
|---|---|
| production documents | direct `/compare` and trailing-slash get/head return the shell with `no-store`; unknown api, asset, path and unsupported-method requests retain errors; hashed assets retain immutable caching |
| url and picker | sixteen absent/empty/repeated/malformed/unknown/duplicate selection cases; independent repair preserving the other slot and unknown keys; fallback/accent/token matching, decimal id ties, ten-result bound, explicit choices and no arbitrary shortlist |
| committed interaction | one history entry per changed slot; no navigation/refetch for current-id selection or absent clear; no fetch while typing or for pair-only changes; ordinary unknown-query revalidation; clear/back/forward/reload drafts, stable focus, preserved scroll for stable-layout commits and immediate next-slot typing |
| replacement and failures | delayed loading omits guessed season and old metrics; transport, decoding and server failures show retryable load errors; successful mounted revalidation updates season, names, metrics and evidence together, then withholds the table when one selected id disappears |
| exact presentation | all ten rows and both columns equal the single decoded response, including identity/team/position, coverage and excluded minutes; synthetic zero/null/tiny exposure, real zero rates, duplicate/missing names, trades, empty publication, fixture marker, global gap and non-2025 season retain their meanings |
| real journey | filtered/sorted league → pair → either profile and listed games → pair → original league; profile shortcut, clear/reselection, direct reload and copied/direct profile return; comparison makes no profile requests |
| access and rendering | native tab/enter/space selection, repair, clear and return; one current-data polite status; visible focus, aligned native table, accessible horizontal scrolling and readable focused names at narrow widths and 200% equivalent layouts |

`real-league-response.json` and `real-profile-responses.json` retain the actual decoded evidence. the checked pair is corey perry `8470621` and justin dowling `8475413`: 738.6 versus 14.4 matched minutes; 57.1/56.9 versus 37.5/75.1 attempts for/against per 60. these are each player's own included results. both full profile summaries match their selected league rows, and both game tables are reached and reconciled to their responses. synthetic inputs are explicitly marked ordinary json responses supplied at `/api/league`; no synthetic database is activated.

rendering checks inspect actual geometry, text ranges and keyboard scrolling as well as desktop, narrow and focused-table images. 200% checks use css layout/painting zoom and halved effective css viewports with device-pixel ratio two: 640 pixels for desktop and 195 pixels for the combined narrow case. native browser-chrome zoom controls are `not_run` because headless shortcuts have no effect; the layout and media-query conditions are exercised directly. in the final 195-pixel case, the scrollport is 163 pixels and table 271; both focused name lines fit inside the uncovered range. no injected css is present in final acceptance.

`preservation.json` verifies unchanged active-database bytes, nanosecond mtime and sidecar state, and the unchanged primary checkout. the separate 04h worktree is concurrently active and changes independently; this task makes no writes there. source re-auditing, capture regression, research execution and publication rebuild/rotation are outside this slice and were not run.

## deletion and handoff

`adversarial-final.json` records independent review of each boundary and the four closed findings, with no open application finding. after that clearance, `test-deletion.json` records removal of the sole browser controller, temporary sandbox profile and two copied baseline setup logs, and confirms the entire temporary directory is absent. the task server is stopped and port 3057 has no listener. all 66 retained evidence-file hashes remain unchanged through deletion, as do active publication bytes/mtime and the clean primary checkout. the concurrently active 04h worktree is observed without writes.

no test-only dependency was installed; the existing cached browser tools remain. no lasting check or harness is retained. at implementation handoff, the assigned branch/worktree and built app were retained, with operation documented in the [readme](../../../README.md#private-observed-results). the user subsequently assigned the source integration and cleanup below. the current publication has not been rebuilt or replaced.

## source integration and task cleanup

the user assigned pr, merge and task cleanup after implementation acceptance. delivery uses a merge commit preserving `b584337` and verifies the reviewed tree against the merged tree before removing the 05b worktree and local/remote task refs. the primary checkout rebuilds the merged application and serves the existing read-only publication. this changes application code, not the database or scientific claims.

the final receipt is `/Users/nnandal/Documents/code/hockey-stats-local/05b-verification/pr-merge-cleanup.json`; independent delivery review is `pr-delivery-review.json` beside it. they record the actual pr/checks/merge identity, primary build and localhost verification, exact removed resources and preserved evidence/publication. the unrelated, concurrently active 04h worktree and its staged work are outside this cleanup. source locators in earlier receipts remain historical verification provenance; no expensive output requires a 05b worktree alias.

## limits and costs

each player retains their own included games, exposure and missingness. comparison is descriptive, without common-game adjustment or an individual-contribution claim. the page loads the full league response on entry, uses up to ten result-button tab stops per slot and takes more clicks than league-row selection. aligned narrow-screen columns can require horizontal scrolling, with taller wrapped rows at extreme widths. return context is browser-history state, so copied/new-tab profile links return to players. explicit metric jsx is longer than a row registry but keeps each required mapping inspectable. possible later presentation changes for supported ability remain accepted. no historical scientific verdict is revised.
