# v1-15 independent adversarial review

status: source review and bounded independent checks complete; both independent findings repaired and verified. no unresolved source finding. browser/native acceptance remains with the root reviewer. this review establishes neither real-output card integration nor scientific admission.

## scope and evidence

reviewed the full v1-15 specification and current changes against context-only commit `ec95981`, including the new discovery/card modules, loaders, routes, identity helpers, shared history preparation, peer controls, styles and exports. read the product brief, council and plan. reviewed existing acceptance receipts as reported evidence, without treating them as independent browser verification.

ran bounded assertions with node `24.21.0`, existing `tsx` and the actual schema7 fixture api at `127.0.0.1:41915`. no dependency, listener, browser or publication changes. [final independent receipt](receipts/independent-review.txt). temporary controller: `app/.temporary-v1-15/independent-review.ts`; delete after final green under the slice's temporary-check policy. expected rejection traces in the receipt establish failing closed on deliberately contradictory responses.

independently checked:

- literal execution column order; card and ledger selector order and signed unit meanings by source inspection;
- all local table presets after loading non-5v5 execution: composed rows exactly equal rows from a fresh overview-only input, so stale `selectedCohort` cannot supply local values;
- root revalidation: exact-strength changes and season changes reload; overview/5v5 switches reuse supplied overview;
- null-last sorting within semantic groups in both directions and visible csv row/column shape across the local presets;
- observed goals selector parity against actual observed endpoint rows, including native identity/support and population semantics;
- explicit metric retention across observed/comparative modes, invalid table-sort reset and contradictory exact-family identity rejection;
- source-definition sort partition labels, through an independent fixture-derived counterexample and subsequent repair.

source inspection also checked three annual overview reads, request-local tuple deduplication, shared comparison cohorts with each player's own identity/support, pending navigation using committed search/data, absent-year identity labeling, field-specific qualification, shared plot break preparation, no browser ledger summing and snapshot capture before png awaits. these are source conclusions, not claims of native interaction coverage.

## findings

### resolved — p1: embedded observed identity bypassed the observed endpoint invariant

`app/src/shared/player-analysis.ts:2088` validates person/summary identity only for the standalone observed response. the initial finite overview adapter consumed an embedded `PlayerSummary` through `app/src/web/analysis-values.ts`, while `composeLeague` in `app/src/web/client.ts` checked outer family identities without verifying that embedded summary's player id/name/position/teams agreed with its owning `Person`.

independent reproduction: intercept one actual overview response in the local controller, change one provided embedded observed `player_id` to `9999999`, and decode it with the actual `LeagueResponse` schema. decoding succeeds. `loadLeague` also succeeds; composing the observed discovery table attributes its rates to overview person `8473507`. no wire record is written or server state changed. the old observed endpoint rejects this identity mismatch; the adapter must preserve that guarantee.

repair: one `checkObservedIdentity` owner in `analysis-values.ts` now preserves the exact id, display-name, reported-position and ordered team id/abbreviation invariant. both selector preparation and league loader composition invoke it before attribution. independently reran schema-valid mutations for player id, name, position, team id and team abbreviation: each actual wire schema decode succeeded, then the loader rejected the contradiction. the same run retained actual observed parity, overview-only identities and all local preset compositions. closed; issue record deleted. no schema migration or invented observed counterpart.

### resolved — p2: semantic sort groups could carry identical explanatory labels

the context selector includes the primary source's definition in `semanticKey`; the initial discovery group label omitted source definitions. two records with the same source construction/population but different definitions formed different partitions with identical headings. this concealed the reason the values could not be sorted together.

independent reproduction cloned the provided fixture context into a second person and gave its source a distinct definition. before repair: semantic keys differed while `cell.definition` was equal. discovery owner added source definitions/construction/population and support policy to the existing label owner, without adding annual source ids to semantic grouping. independent rerun confirms labels differ and expose the changed definition. closed.

## crossreview and remaining acceptance

the root reviewer reported earlier repairs for a missing selected-family comparison row, map-only comparative reloads, hidden usage/null reasons, missing workload/known-slot detail and replacement-column png uncertainty/reasons. inspected the corresponding current ownership and rendering paths; root owns the final integrated reruns.

no additional blocker found in card order/units, field-specific cohorts, annual joins, partial observed comparison or shared history preparation. the newly shared two-cutoff controls retain the selected-field default and use one group/reset owner; native keyboard and narrow rendering remain root verification.

do not infer saved-png fidelity, native 200% layout, browser back behavior, assistive-technology coverage or final software completion from this source review. latest native outputs and updated receipt must be read by the root reviewer after the final content repairs. temporary controllers/dependencies must be removed after final green. real v1-03/06/12 integration remains separately pending unless supported by actual output evidence.

## finalization closure

final source/document review is clear. read the final [cleanup](receipts/cleanup.json), [documentation checks](receipts/documentation-checks.json), [typecheck](receipts/typecheck-green.txt) and [build](receipts/build-green.txt) receipts. independently confirmed all inventoried cleanup paths are absent, including 11 temporary tests, five controllers and 22 downloads; final code hashes still match the identity receipt. root records stopped task listeners and successful pinned compilation after deletion. documentation checks record 477 valid local link targets and valid json receipts. the earlier cleanup/final-verification conditions above are closed.

reviewed root's bounded [browser assertions](receipts/browser-tests.json), [native checks](receipts/native-checks.json), [saved outputs](receipts/native-exports.json) and [navigation/export-cost sample](receipts/interaction-cost.json). the final completion claims match that evidence and preserve its limits: native 320px/200% viewing, named controls and Return submission, back/forward coherence and saved-output checks; no VoiceOver session or comprehensive accessibility audit. these ui checks were performed by root, not independently rerun by this reviewer. software completion against fixtures is supported; real producer/card integration remains pending. no unresolved finding, source edit or commit follows from this closure.
