# typed publication verification

implementation and detached acceptance of [v1-13](../../specs/v1-13-typed-publication.md), assigned 2026-10-22. branch `implement/v1-13-typed-publication`; worktree `/Users/nnandal/Documents/code/hockey-stats-v1-13`. the starting snapshot preserves the user's supplied documentation changes in `c80aa0a`. live activation, real family production and new analytical cards remain separate assignments.

## evidence and independence

the [frozen exchange](../../../fixtures/publication-v1-13/results/manifest.json) and [independent expected facts](../../../fixtures/publication-v1-13/checked-facts.json) cover all fixed tables and family/selector matrices over three display years. six existing complete captured-game bundles supply the observed baseline. synthetic analytical records have separate attributed identities and fixture purpose. no acquisition, fit or historical scientific verdict changed.

three native non-astra agents implemented exchange/storage, shared contracts and reader/operator boundaries. a separate non-astra session implemented the current web adaptation. root inspected their contracts and source-to-screen behavior; an independent read-only session ran adversarial storage and operator probes, and the shared-contract owner independently audited content. temporary integration checks were written red, passed after implementation, rerun after refactoring and removed after review. checked facts and receipts remain; no persistent harness or dependency was added.

## checked behavior

| boundary | result |
|---|---|
| exchange and candidate | strict manifest/jsonl parsing, exact keys and primary-key ordering, digest/count/path checks, purpose isolation, complete family dispositions and required rows; exclusive output, incomplete failure and final rename verified |
| storage and identity | literal strict schema7 declarations, foreign keys, integrity, single method storage, source/method/support resolution, identity-kind agreement and exact read-back verified |
| independent arithmetic | ten components total 55 league-relative and 110 replacement-relative; four native/display map transports integrate to 3; goalie mapped saving differs from whole-population saving, and covered-all ratio 100% remains beyond the fixed ±25% legend |
| conditional evidence | exact fixed danger bins including probability one; separate execution denominators; 23 source rows in each provided evidence year retain duplicate/null event ids; only the first year's source index zero has a fitted supplement |
| context | independent interval-set intersections for all attempts, goals and locatable unblocked attempts; two-teammate conjunction, zero-event time, trade, absent teammate and pending valued populations verified |
| observed preservation | every original row/column exact in season, game, player game/season, spatial game/season/cells and pair tables; 216 player-game and 216 player-season rows, 144,288 player-season spatial rows; identity changes only from `player` to `person` |
| api and composition | all five typed endpoints, selector/kind/strength errors, explicit absent vs pending states, resolving offline metadata, cancellation and mixed publication/year/corpus rejection verified |
| operator | disposable activation preserves opaque schema6 predecessor bytes; compatible schema7 restore works; cross-schema restore refuses with matching-build manual instructions; invalid/occupied incoming refuses before rotation |
| standalone reads | operating-system sandbox denies original/worktree fixture and generated-input directories plus the external drive; an actual input read fails while database-only check and all five endpoints succeed |
| ordinary read failure | a disposable database corrupted after startup produces 500 with existing retry copy and local technical detail; no unavailable estimate is fabricated |

adversarial checks cover malformed/extra/duplicate fields, promised-member and disposition omissions, unsafe/nonfinite values, dangling/wrong-kind references, failed-fit evidence, wrong units/strengths, invalid probabilities, finite-leaf arithmetic overflow, map/ledger/scalar disagreement, conditional event applicability, physical rounded-rink coordinates, interval overlap/horizon/membership/mirroring, dressed-team conflicts, repeated facts and identity/count parity. rejection receipts assert the intended error rather than merely a nonzero exit.

review repaired source-only lineage, absent-season typing, actual goalie strata, source-unclassified/block evidence, distinct context populations, failed-solve and unavailable-source copy, synthetic historical input binding and per-row method chronology. earlier seals missed the historical binding and later-season method metadata; final evidence supersedes those seals. annual methods now respect the row season through june 30; carried state inputs and season-scoped support methods obey the same chronology, while the common prepared artifact may retain multiple seasons. review also withdrew an incorrect proposed prohibition on overtime 5v5: the official [2025–26 rulebook](https://media.nhl.com/site/asset/public/ext/2025-26/2025-26Rules.pdf), table 15, allows it after penalty expirations. the declared physical membership and bounded known period horizon remain authoritative.

## browser checks

root used native computer-use controls against an isolated compiled fixture server on port 41914. firefox verified league search/sort/filter reset, discovery → profile → return with query preserved, profile cards/peer controls/deployment/games/history, missing-year navigation, server-scaled map mode, ordered comparison deep link → profile → comparison, fixture labeling and a completed `hockey-stats-20252026-8480860-5v5.png` download. goalie identity/history, absent goalie and a present skater without observed results never render invented skater values.

targeted 375×820 and native 200% checks cover changed identity/absence states. browser review found and repaired a new goalie-history table overflow by reusing the existing keyboard-scrollable table region. it also found that generic season 404s rendered player-not-found copy; the existing specific season/player error contracts now retain their distinctions. chrome's native window became stale; firefox rendered the identical responses, and bounded real-response decoding/rendering found no product loop. no browser-driving framework was added.

## costs and limits

| measurement | fixture result |
|---|---:|
| database bytes | 20,299,776 |
| build wall time / peak resident bytes | 8.536 s / 185,991,168 |
| compiled check wall time / peak resident bytes | 1.22 s / 292,274,176 |
| compiled startup to first response | 1.474 s |
| observed cohort / selected profile / selected maps bytes | 324,894 / 739,522 / 506,317 |
| node shared decode: cohort / profile / maps | 7 / 8 / 7 ms |
| full profile load / static render | 33 / 162 ms |
| client javascript change | 54,529 bytes raw, 9.16%; no new dependency |

these measurements describe the checked compact fixture and pinned node `24.21.0`, not full-season capacity. season coverage inventories account for much of the current response size. map toggles revalidate their coherent route requests; no cache is introduced. startup uses bounded 128-row keyset batches because the pinned sqlite adapter has no streaming cursor; catalogs and required scalar closure totals remain in memory, while a selected response intentionally carries its complete fixed payload. [real map-volume measurement](../../issues/publication-map-volume.md) remains a producer-integration follow-up, not evidence that full-size operation was verified. fixtures establish transport and current-view continuity, not scientific admission, real analytical delivery or complete cards.

## final identity and cleanup

the final candidate is `var/v1-13/candidate-chronology/player-analysis.sqlite`, publication `cfed52ea-954b-4d6d-87e6-dc5d8d118476`, sha-256 `9ba58c11a8c430098b74eff35b47bbe797f8d345c8911fbc71ae5f432a85c10c`. the retained result manifest's sha-256 is `f768b285ea529a07f9a683e54878d8f9ec42c758f899cfefcec3018c59c66078`; prepared/design fixture identity is the actual checked-facts sha-256 `6e50f4a432b56a3643450874e885ab993026eca6d299c080e1496bb21dd38cee`. the [chronology rejection receipt](receipts/python-chronology.json) and [quantity equivalence](receipts/chronology-equivalence.json) supersede earlier metadata identities without changing their numerical evidence. candidate producer metadata truthfully identifies the dirty implementation snapshot based on `c80aa0a`; later git commit identity does not rewrite a frozen database.

[content review](content-review.md), [independent storage/interface review](independent-review.md), [python receipts](receipts/python-integration.json), [independent numerical oracle](receipts/independent-numerics.json), [exact observed preservation](receipts/observed-preservation.json), [final quantity equivalence](receipts/chronology-equivalence.json), [reader/operator receipt](receipts/reader/reader-final-receipt.json), [web green results](receipts/web-green.txt) and [browser/build receipt](receipts/browser-and-build.json) record the final boundaries. `npm run typecheck`, `npm run build`, installed `hockey-stats-analysis publish --help` and whitespace checks pass after temporary application-test deletion. relative documentation links are checked; historical absolute external receipt locators remain preserved.

[protected-state evidence](receipts/protected-state.json) confirms all 30 original build/database files retain exact bytes, sizes and modification times, and the primary listener retains pid `70045`, start time and command. the reviewed database retains its exact digest after reads with no wal/shm. the database is a disposable worktree output; no sqlite file is committed. no live activation occurred.

the python, shared-contract, reader, web, independent-review and root temporary controllers/generators were removed after their final green checks. compact cleanup inventories accompany their receipts; retained source-backed fixtures and expected facts remain data, not a test runner. no test-only dependency or persistent acceptance framework remains.
