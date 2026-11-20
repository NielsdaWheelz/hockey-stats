# v1-12 value ledger verification

implemented on `implement/v1-12-value-ledger` in the isolated `~/Documents/code/.worktrees/hockey-stats/v1-12` checkout. real source-to-screen acceptance and temporary campaign cleanup are complete. the single schema 12 candidate is inactive. [the specification](../../specs/v1-12-value-ledger.md) controls the acceptance boundary. [the plan](../../plan.md#current-boundary) owns assignment and status.

## design and trade-offs

- dated boxscore time and roster reconciliation determine the annual depth group. excluding an entire unreliable team-position group discards otherwise usable minutes and changes the reference population. fixed depth weights preserve the population when a required estimate is unavailable and can withhold the entire position reference.
- finisher and setter contributions use the seven common reference states. enumerating the remaining neutral slots stays stable at rounded-one focal probability. the whole-team attempt rate, fixed lineup roles, omitted interactions and hypothetical specialty minutes limit the interpretation of the ten-term index.
- the score event stream is validated and hashed once. the shorthanded reducer retains strict prepared-game validation and saves enough segment and attempt evidence to validate reuse. the territory reader hashes each bound archive and decodes only its saved scalar array. these checks spend i/o to preserve accepted input identity.
- semantic comparison identity uses declared component definitions. an unavailable state keeps the same identity when the selected donor seasons agree on its definition. a changed definition still breaks the comparison.
- one annual reference holds rankings, weights and constants. overview and history carry compact coverage and the scalar ledger. selected detail pays one evidence read for the full construction and constituent support.
- the cutover uses one attributed exchange successor and the ordinary schema-paired publisher. checking the inherited members and building and starting a complete candidate cost time and disk space. operation stays on an inactive candidate with the existing local serving build and publication pair.

## temporary checks

- eleven source checks pass after refactoring. the original fixture corpus and old implementation agree exactly on accepted 4v5 receipts for five seasons and 36 games. the new fixture checks exercise retained zero-event time, whole-segment exclusions and bound source/score rejections.
- independent arithmetic fixtures pass sign and unit checks, reciprocal weights, direct slot enumeration at rounded-one neutral probability, zero workload versus unavailable positive workload, ties, trades and unavailable weighted members.
- a saved v1-11 donor row with synthetic depth evidence passes detached python and typescript validation. corrupted reference identity, source/support identity, state arithmetic, grouping and complete-vector total were rejected. the narrow territory test forbids opening panel/design arrays and calling full reprojection.
- schema 12 fixture publication and strict server startup passed with pending ledger/reference envelopes. a disposable copy missing the annual reference failed strict startup. the live fixture verified year selection, pending and absent results, and rejection of unrelated evidence selectors. [pending fixture](receipts/pending-fixture.json), [selector checks](receipts/pending-fixture-selectors.json).
- the attributed successor for the provided synthetic fixture preserves 50 inherited members and all 15 original method bodies. two supplied ledger rows were reconstructed from checked prerequisite formulas. missing terms withhold their totals. the compiled detached server and actual narrow browser passed, including scalar equality and real downloads. [provided fixture](receipts/provided-fixture.json), [browser download receipts](receipts/provided-fixture-browser.json).
- the schema-paired disposable rollback served both matched pairs and rejected both mismatched pairs. it restored the original fixture bytes. [rollback](receipts/disposable-rollback.json).
- synthetic browser fixtures passed narrow and native 200% inspection, seven-state construction, ten signed terms and all four construction csv row types.

## implementation review

the independent opus review and the native boundary reviewers inspected the source, arithmetic, detached readers and web handoffs. shared neutral rates now compare the published donors that actually supply them. saved empty panels retain their exact selected score and donor method identity. missing totals retain the first canonical missing estimate reason in both readers. fixture controls also caught a mismatch between concatenated and tuple sorting of team ids and a pending annual envelope being passed back into the current writer.

the saved final-year territory status supplies its inherited finding. the preparation selection confirms complete regular-season inventories for the three years. upstream execution validators already require unavailable per-100 skills on empty panels. native interpretation derives the boxscore team from the containing array. the reviewer's remaining source concerns produced a strict short-side ambiguity repair, explicit receipt construction identity and a test for unidentified zero-time players. [independent opus review](implementation-opus-review.md).

the application review followed the conversion, physical schema, lazy profile/detail linkage and export owners. the construction csv now supplies explicit exact-state values, units and unavailable reasons, plus rank and member dispositions. both zooms produced identical downloaded bytes in the synthetic control. the [v1-17 microstat export](../../specs/v1-17-microstat-cards.md#exports-and-operating-contract) keeps the compact png scoped to the statistical card. the six ledger strip rows are covered by card csv and selected detail/history exports. [application review](application-opus-review.md), [typed csv receipt](receipts/typed-construction.json).

the attribution audit binds the accepted donor, the one-time conversion receipt and the composed exchange. an annual method binds its immediate donor for detached arithmetic. the converter's exact member copies and current metadata/envelopes were checked before composition, and final strict readback checks the complete carried exchange. [conversion metadata proof](receipts/real-conversion-metadata.json).

one bounded dry run propagated all five pinned final-year variants for an actual donor focal row with synthetic shorthanded opportunities. it exercised native saved-state and scalar archive reads in 2.76 seconds. the real run below supplies the full annual check.

## real run

the accepted donor manifest and prepared manifest match `ec5349f1f019a9ccfbac908be26dd34b350f26085a890904b6048de0da1d2829` and `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c`. the run lives under `/Volumes/Expansion/hockey-stats/runs/value-v1-12-20261119-yVPgGFSw`. the attributed exchange conversion passed after 618.72 seconds and peaked at 36,306,944 resident bytes. the subsequent source reductions use the same native slot. [conversion receipt](receipts/real-conversion.json). fitting, rescoring, scientific admission and activation are outside this assignment.

the first 20232024 usage reduction agrees with 923 complete inherited usage records and qualifies 30 team groups at each position. the initial shorthanded pass was interrupted before any reduction receipt after review found a short-side boundary defect. the corrected serialized pass reuses the exact checked usage bytes. the strict prepared reader now releases each consumed game without waiting for cyclic collection.

| real season | source audit agreement | source reduction wall time and peak rss | 3v5 attempts / seconds | 3v4 attempts / seconds |
|---|---:|---|---:|---:|
| 20232024 | 923 complete player-season records | 5,151.65 s, 2,938,863,616 bytes | 14 / 10,695 | 19 / 9,209 |
| 20242025 | 920 complete player-season records | 5,240.68 s, 3,554,508,800 bytes | 8 / 10,510 | 8 / 6,467 |
| 20252026 | 940 complete player-season records | 5,359.25 s, 3,597,090,816 bytes | 9 / 11,601 | 17 / 8,973 |

20232024 retains an unquantified gap in both shorthanded references. the 3v4 reduction excluded 120 known seconds. [source receipt](receipts/real-source-20232024.json).

20242025 retains all 32 team-position groups in each position. its 3v5 and 3v4 reductions excluded 322 and 48 known seconds and retain unquantified gaps. [source receipt](receipts/real-source-20242025.json).

20252026 retains all 32 team-position groups in each position. its 3v5 and 3v4 reductions excluded 523 and 354 known seconds and retain unquantified gaps. [source receipt](receipts/real-source-20252026.json).

independent source checks passed for all three seasons in 74.36 seconds with 1,343,684,608 resident bytes at peak. the checker reopened original traded-player boxscores, matched their team totals to fixed weights, and checked exact short-state attempts and time against the bound prepared segments and saved event stream. the witness games include retained zero-event time and whole-segment exclusions. [native source witnesses](receipts/real-independent-source.json).

## real composition and prebuild

exchange 6 `6d05679d3fcfdb0eca3ba9cae414a12dcb2f4699d037719c953aa200c6896389` passed strict staged readback in 3,564.32 native seconds with 2,543,452,160 resident bytes at peak. the composition contains 32,827,369,104 bytes before its final receipt. the independent prebuild check took 4.14 seconds and checked exact method bodies, carried descriptors, complete player keys and the conversion attribution. the 90 carried members contain 38,080,022 rows and 32,684,886,370 bytes. the inherited member bytes were digest-checked during copying and strict exchange validation. the prebuild check compared their descriptors instead of rereading all 32.7 gb. [value results](receipts/real-value-results.json), [prebuild audit](receipts/real-prebuild.json).

| season | skater rows / league totals / replacement totals | forward depth members / seconds | defender depth members / seconds | compact overview addition | selected ledger detail range |
|---|---:|---:|---:|---:|---:|
| 20232024 | 924 / 923 / 923 | 229 / 2,633,623 | 132 / 2,318,947 | 3,553,972 bytes | 193,332–207,166 bytes |
| 20242025 | 920 / 920 / 920 | 256 / 2,942,925 | 146 / 2,595,904 | 3,537,954 bytes | 198,819–205,600 bytes |
| 20252026 | 940 / 940 / 940 | 261 / 3,238,496 | 152 / 2,460,494 | 3,614,559 bytes | 199,018–206,351 bytes |

all six position references have complete fixed member vectors. 20232024 excludes teams `1` and `21` at both positions. the two later years retain all 32 teams at both positions. player `8477073` has unavailable finishing and setting in 20232024. both totals remain unavailable and the other terms retain their own availability. all annual methods share the same semantic reference identity.

of the five final-year variants, the largest movement anywhere in the ledger is 0.000002330 goals, from shootiness. the maximum league-total movement is 0.000002252 goals and the maximum replacement-total movement is 0.000002204 goals. all movements remain below the 0.001-goal diagnostic budget. the saved territory hazards still exceed their own upstream budget. aggregate optimizer accuracy and uncertainty remain unassessed. earlier years have no corresponding diagnostic variants.

## publication interruption and safe eject

the ordinary publisher ran for 7,414.57 seconds and reached numerical result insertion. it peaked at 3,337,191,424 resident bytes. at the user's request, `SIGINT` ended the process with exit 130. sqlite closed, the journal disappeared, and the incomplete file was 622,530,560 bytes after close. the scheduled reader exited without starting. the completed exchange and reductions retain their checked identities. macos ejected the apfs container and its physical disk, and the volume and its visible file handles were absent afterward. [interruption receipt](receipts/publication-interruption.json).

the original active and previous database identifiers, sizes, inodes, modification times and header hashes match the storage delivery receipt. the compatible service is still on port 3000 under pid `91302`. the primary checkout is clean.

## real candidate and live acceptance

the remounted drive supplied the same checked exchange and observed selection. the ordinary publisher rebuilt in `candidate-02` and passed integrity, foreign keys, stored-result readback and three seasonal conservation checks. publication `35ce39e0-5a28-4582-8b98-e7973b0e8045` contains a 32,039,075,840-byte database. the publisher consumed 41,878,614,908 input bytes, took 18,011.25 native seconds and peaked at 3,328,000,000 resident bytes. the interrupted directory remains evidence of the earlier attempt. [real candidate receipt](receipts/real-candidate.json).

the compiled app became ready in 3,361 seconds on port 3133 with original data reads denied. the deny probe failed with an operating-system permission error while the original data remained mounted. peak server rss across startup and live checks was 3,018,899,456 bytes. acquisition, fitting and scoring were unnecessary because the checked inputs were reused.

all 24 selectors agree with the published row values and annual reference ids in all three years. overview, profile, history and selected evidence agree on each checked value. the real cases cover forwards, defenders, trades, specialty qualification and players below the general time cutoff. the raw overview responses include inherited families and were 44,480,005, 44,609,885 and 45,286,689 bytes by season, each about five seconds on the test host. the prebuild table above isolates the ledger addition. selected detail loads only when requested. [live selector and browser receipts](receipts/real-candidate.json).

chrome checked table-to-profile navigation, both comparative and analytical totals, the six microstat strip values, both execution-contribution links, the pooled f/d replacement standings, seven state rows, and the final-year sensitivity copy. all three normal-width journeys and the final-season 375 px and native 200% journeys passed. each downloaded three csvs and three pngs. the construction csv carries term, exact-state, team-rank and weighted-member rows plus dependency methods. the first browser assertion counted nested evidence headings. its corrected selector counted the actual pooled peer table.

the six narrow downloads match the normal downloads byte for byte. at native 200%, five match exactly. the history png has the same dimensions and differs at 1,104 of 6,526,800 pixels inside the plot. the chart raster varies with zoom and the evidence and quantities agree. the initial byte comparison and the localized difference are both recorded. [download identities and comparison receipt](receipts/real-candidate.json).

## cleanup and preservation

the temporary converter, campaign tests, runners and disposable worktree fixture copies were removed after verification. the checked source fixtures, durable receipts and external candidate remain. the two schema-matched fixture pairs and rejected crossed pairs are recorded in the rollback receipt. the live acceptance server was stopped and port 3133 closed. the 38 original serving-build files matched their recorded hashes, inodes, sizes and modification times. the active schema 8 and previous schema 7 databases matched their recorded identities, sizes, inodes, modification times and header hashes. the primary checkout and its service on port 3000 remained in use. [rollback proof](receipts/disposable-rollback.json), [preservation evidence](receipts/real-candidate.json).
