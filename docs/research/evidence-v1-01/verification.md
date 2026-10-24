# v1-01 shared-evidence verification

status: complete, 2026-10-24. all 6,560 selected games and 2,060,996 original events pass full source/public-reader reconciliation, partition and coverage checks. original-source samples, guarded downstream reads and the reason-time supplement pass. [independent final review](real-acceptance-independent-review.json) clears the receipt chain; [temporary tests/controllers are deleted](test-deletion-real.json). the [requested pause](pause-2026-10-23.json) remains historical.

implementation: branch `v1-01-shared-evidence`, worktree `/Users/nnandal/Documents/code/hockey-stats-v1-01`. three non-astra implementers covered source/support, factual context and artifacts; root, peer reviewers and a separate claude session challenged the boundaries. the primary checkout and serving files were not modified by this work.

## delivered contract

`analysis_data` owns `prepare_analysis`, `prepare_game`, `read_prepared`, `read_prepared_game`, `read_prepared_people` and `read_prepared_coverage`. its public readers consume the prepared artifact without opening original sources. source support, context construction and closed record validation remain package internals. existing native, observed and research owners retain their separate supported populations.

`hockey-stats-analysis prepare --selection FILE --out DIR` requires both flags exactly once. selection identities, corpus/capture receipts, member hashes, fixed records, links, units, source availability and count/time support are checked explicitly. output must be new; the manifest is written last. no retry engine, compatibility schema, acquisition, fit, season-rate reducer, database or application change was introduced.

all-strength membership coalescing is shared with the exact old 5v5 projection. event evidence survives missing elapsed membership. the new ordinary-attempt mask owns matched count/time exclusions; consumers add only their own restrictions. chunks partition retained physical segments. event prefixes are source-ordered and pre-event; elapsed prefixes use preceding half-open time and exclude same-clock actions.

the closed segment schema represents exact state through the four membership cardinalities; source status remains in `game.ledger`, `game.inputs` and linked `native_intervals`, while matched-rate disposition remains in `ordinary_attempt_support`. retained `identity_observations` remains conditional under the [03k contract](../features-03k/ledger.md#exact-shared-fields-and-history-windows); the validator checks both its required presence on unresolved joins and equality to the retained original arrays.

## selected evidence and resources

[fixture selection](selection-fixture.json), [fixture manifest](fixture-manifest.json), [coverage](coverage.json), [source freeze](source-freeze.json) and [independent facts](independent-facts.json) identify the final artifact. its local path is `/Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6`. source captures are the existing committed originals. no new broken-game download or replacement fixture was needed.

| season | inventory | selected / all six sources parsed | original events | attempt facts | resolved physical seconds | included seconds | excluded seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| `20212022` | 1,312 | 7 | 2,192 | 824 | 25,619 | 25,399 | 220 |
| `20222023` | 1,312 | 5 | 1,497 | 596 | 18,595 | 14,984 | 3,611 |
| `20232024` | 1,312 | 6 | 1,948 | 715 | 21,887 | 21,887 | 0 |
| `20242025` | 1,312 | 9 | 3,044 | 1,092 | 29,275 | 27,966 | 1,309 |
| `20252026` | 1,312 | 9 | 2,978 | 1,101 | 25,663 | 14,597 | 11,066 |
| total | 6,560 | 36 | 11,659 | 4,328 | 121,039 | 104,833 | 16,206 |

these are selected-fixture facts, not full-season coverage. parsed source availability does not establish complete records, matched elapsed support or model applicability. coverage separately records 11,949 unresolved known seconds and one game with unknown horizon; an unknown duration is not zero missing time. exact-state physical time, directed team time, actual skater/goalie slot time, source kinds/outcomes, report-only records and every completeness denominator remain in the coverage receipt.

final preparation measured 152.38 seconds wall time, 1,038,254,080 peak resident bytes and 1,939,136,248 output bytes excluding the manifest. python was `3.14.8`; source content hash is `b2ac65f8e6dd7c1faec2bade6a4dc446646c322ca17a0e5182d3d80d5a92379f`; policy hash is `28624b42c78254a0000c97205b73a5ff5ff59fbc237264c77d4cd4e339178795`. the manifest records the input-contract snapshot commit and a dirty working tree; content hashes identify the verified implementation precisely. fixture costs do not establish real runtime, peak memory or drive capacity.

## checks and adversarial repairs

| boundary | evidence |
|---|---|
| input and artifact | temporary cli-to-public-reader test was red before implementation, then green through refactors. strict command/selection, malformed member, refreshed-hash semantic corruption, missing/incomplete output and occupied-output cases are in [checks](checks.json). original-source reads and socket connections were denied during detached reader checks |
| source and support | all 37 existing capture fixtures preserve native reconstruction, old 5v5 segments and old conflict predicates exactly; [source fixtures](source-fixtures.json), [peer review](source-review.json). all 36 selected games retain every original event exactly by source index and every native interval/report row; partitions and independent score/unit arithmetic are checked in the final facts receipt |
| context and labels | synthetic actual 3/4/5/6-member arithmetic and partial sums, source-ordered same-clock/goalie prefixes, no skipped successor, stop cutoffs 0/2/3 seconds, reattempt cutoffs 0/5/6 seconds, unresolved kinds, first-action censoring, closing goals, valid terminals versus bare eof and direct missing-history locators passed. [future invariance](future-invariance.json) records byte-identical earlier predictor facts after later trusted-input mutations; raw admission is a separate checked boundary |
| dated identity | [seven actual multi-team people](people-facts.json) match original dated teams/sweaters, latest supported roster names, positions and named bio observations; february-1 age references and unknown effective times/height units are explicit. conditional conflicting-join evidence and malformed date/age/sweater links are checked |
| preserved consumers | [full canonical before/after results](preserved-consumers.json) match exactly through existing observed reducers on all three displayed 1,312-game seasons: hockey facts, support, personal/spatial/deployment quantities and reasons. [36 research/core fixture projections](research-projections.json) also match exactly after the final repair; no historical fit or application rebuild was required |
| downstream readiness | [actual reader exercise](downstream-readers.json) selects ordinary execution event facts, all-strength descriptive states and matched elapsed chunks in `2025020001` and `2025021094`, with original sources/network denied. it neither fits nor establishes a downstream recipe's eligibility |
| real handoff | [real artifact](real-artifact.json), [29 original-source samples](real-content.json), [guarded reader exercise](real-systems.json), [all 6,560 public-game/source checks](real-source-reconciliation.json), [saved-reason coverage](real-reason-coverage.json) and [independent final review](real-acceptance-independent-review.json) pass; [temporary tests/controllers are deleted](test-deletion-real.json) |

independent review repaired outcome-dependent episode availability at the focal row; uncertain participation fabricated across source gaps; incomplete physical-action label semantics; goalie workload taint from known empty nets/own goals; unresolved support mislabeled ambiguity; unassigned interior attempts left in included runs; abbreviated season identities; missing raw block coordinates; and strict source/member consistency gaps. [final independent review](independent-review.md) separates computational findings from operating costs and scientific claims.

representative checked cases:

- `2022020822`: the incoming-lineup goal at `/plays/93`, period 2 clock 116, retains pre-score 0–1; assigned following elapsed play has score 1–1.
- `2024021235`: 292 events and 110 attempts survive absent shift membership; zero resolved segments and 110 `membership_unavailable` reasons. event evidence supplies no denominator.
- `2024020186`: union exclusion is 49 seconds for this new all-strength mask: the old 46-second 5v5 conflict plus a distinct 3-second 6v5 run. the old 02d predicate and exclusions are unchanged; there is no second subtraction of its baseline 132 seconds.
- `2025021094`: the penalty shot at `/plays/164` is outside ordinary matched support; the final ordinary goal at `/plays/304` is retained in actual overtime `[40,41)`, with no invented full overtime.
- `2025020565`: distinct overlapping own rows for `8482684` cannot establish a known physical union. [original locators and expected behavior](../../../fixtures/README.md#v1-01-individual-participation-overlap-check--2026-10-22) retain all rows; 27 clean spans supply 1,564 known seconds, with complete time/start/age/rest withheld. known 5v5 time intersects clean participation and never exceeds known total time. exact duplicates and endpoint adjacency remain valid controls.

## real-corpus resumption

all five original corpus identities match the [real selection](selection-real.json). the first preparation reached `2021020093`, where two other-state boundary neighbors produced the same empty-affected strength diagnostic twice. the strict validator correctly rejected it. [the repair receipt](boundary-2021020093.json) records red, green, refactor, source/consumer parity and independent public readback. the producer now emits that diagnostic once, preserving each same-state identity mask, every source row and all support decisions. the complete original capture bundle is retained under `fixtures/captures/2021020093/`; no corrected download replaced it.

the [resumed implementation freeze](real-source-freeze.json) identifies commit `5503c7b` by source content. the [native-only regression](real-native-support.json) checks all 6,560 envelopes, 2,060,996 original events, 2,082,038 report rows and 2,444,136 maximal segments: source cardinality, unique witnesses, native partitions and exclusion unions pass. it measured 281.561 seconds and 203,063,296 peak resident bytes. this bounded check preceded the complete prepared-artifact acceptance recorded below.

the [real artifact receipt](real-artifact.json) identifies `/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json`, sha256 `63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c`. all five seasons have 1,312 game members, plus five people members and coverage. preparation measured 33,732.702 seconds (9.37 hours), 5,420,793,856 peak resident bytes and 397,784,660,779 output bytes excluding the manifest. independent checks match the exact 6,568-file set, output bytes, selection bytes, package source hash and policy hash. the recorded analysis tree was clean at `5503c7b`; documentation status is separate.

[content verification](real-content.json) independently checks 29 games against original bodies: 9,451 events/pre-scores, 13,343 roles, 7,759 geometries, 108,554 known prefix times and 6,960 dated history windows. all 29 samples and five season people files pass public readback. [systems verification](real-systems.json) checks all five people files/coverage and three actual downstream selections with original sources, network, fitting and publication access denied. its 5,369 person-season records remain explicitly partial; the three views preserve usable event facts when elapsed membership is absent. neither bounded review substitutes for full source reconciliation.

the [full source reconciliation](real-source-reconciliation.json) (sha256 `7419ba23f1050d3abd0a11467a223253c922135e10250a4ace378d117185f210`) checks each of the 6,560 selected games once through the public reader, conserves all 2,060,996 original events and matches each season's saved coverage, including support time, exact-state accounting and completeness. five disjoint season receipts share the same manifest, checker and identity-count bindings. their measured wall seconds are 6,979.512, 8,552.734, 15,198.696, 15,563.685 and 16,175.081 in season order; peak resident bytes are respectively 1,874,542,592, 2,217,361,408, 1,745,928,192, 1,574,764,544 and 1,674,559,488. these per-shard measurements include concurrent work and one bounded operating-system scheduling probe; they are not additive elapsed runtime. the compact merge made no additional public-game reads.

## real coverage

the exact [real coverage member](real-coverage.json) is copied byte for byte from the completed artifact (sha256 `fb9e5c5207375747caf00d45d49a5264ccd9b86bf0e6f22c34b21bd0bdf9fc49`). the public coverage reader and all five season people readers passed the guarded systems check; all five independent source seasons reconcile to this coverage. these are recorded source and support facts, not model eligibility or scientific quality.

all six named source bodies are available for every selected game in each season: play-by-play, boxscore, shifts, game-summary, play-report and landing. availability means the source parsed; it does not imply every field, event context or elapsed rate denominator is supported. matched elapsed support is the included physical time below. model applicability is **not assessed here** and belongs to each downstream consumer and its additional restrictions.

| season | inventory / selected games | six-source available games | original events | report-only attempts | matched included seconds | excluded seconds | unresolved known seconds | unknown-horizon games |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `20212022` | 1,312 / 1,312 | 1,312 | 404,656 | 909 | 4,611,732 | 97,019 | 69,299 | 1 |
| `20222023` | 1,312 / 1,312 | 1,312 | 408,732 | 825 | 4,670,390 | 83,153 | 27,075 | 0 |
| `20232024` | 1,312 / 1,312 | 1,312 | 413,676 | 836 | 4,587,763 | 58,105 | 128,655 | 0 |
| `20242025` | 1,312 / 1,312 | 1,312 | 420,073 | 736 | 4,420,410 | 92,692 | 260,095 | 0 |
| `20252026` | 1,312 / 1,312 | 1,312 | 413,859 | 983 | 4,617,973 | 113,817 | 57,215 | 0 |

`real-coverage.json` retains 131 season/state rows keyed by away/home skater and goalie counts. each row records physical, included, excluded, directed team, skater-slot and goalie-slot seconds. the table sums those exact-state rows by season; team time counts both directions, while slot time uses actual membership. physical seconds are counted once and equal included plus excluded seconds.

| season | exact-state rows | resolved physical seconds | directed team-seconds | skater-slot-seconds | goalie-slot-seconds |
|---|---:|---:|---:|---:|---:|
| `20212022` | 32 | 4,708,751 | 9,223,464 | 45,142,287 | 9,134,599 |
| `20222023` | 29 | 4,753,543 | 9,340,780 | 45,675,870 | 9,254,830 |
| `20232024` | 24 | 4,645,868 | 9,175,526 | 44,908,206 | 9,091,413 |
| `20242025` | 24 | 4,513,102 | 8,840,820 | 43,360,702 | 8,744,366 |
| `20252026` | 22 | 4,731,790 | 9,235,946 | 45,203,897 | 9,140,442 |

excluded seconds are the union of saved matched-support masks. the manifest-bound [reason coverage supplement](real-reason-coverage.json) (sha256 `1304e54fa489c4b8c6f2f276dddf721d726c43dce13ceee0178f8ca419791fef`) counts saved reason witnesses and event dispositions without rederiving support policy or changing the closed artifact. it reads the 1,345 games with positive known resolved exclusion after their full source proof, not another 6,560-game pass. the 2,060,996 source-event support dispositions are:

| included | excluded | unresolved | not applicable |
|---:|---:|---:|---:|
| 735,216 | 16,685 | 17,861 | 1,291,234 |

each reason witness is a saved reason row. per-code excluded segments and seconds are unions within that code; they overlap other codes and must not be added. the overall saved mask excludes 44,725 segments and 444,786 known resolved physical seconds once. 12,195 seconds carry multiple distinct reason codes.

| saved reason code | witnesses | excluded segments | known resolved excluded seconds |
|---|---:|---:|---:|
| `count_accounting_conflict` | 218 | 41,739 | 392,921 |
| `event_evidence_unresolved` | 889 | 431 | 11,940 |
| `horizon_unavailable` | 16 | 0 | 0 |
| `identity_conflict` | 1,321 | 1,309 | 21,730 |
| `membership_unavailable` | 17,969 | 294 | 5,920 |
| `strength_conflict` | 457 | 167 | 3,935 |
| `unmatched_report_attempt` | 923 | 1,250 | 20,849 |

the five hash-bound season reason receipts named by the merged supplement give the following detail. zero in the witness table means no saved reason row; zero in the time table means no known resolved exclusion, even when witnesses exist.

| season | included events | excluded events | unresolved events | not-applicable events |
|---|---:|---:|---:|---:|
| `20212022` | 142,727 | 3,698 | 2,206 | 256,025 |
| `20222023` | 148,628 | 3,126 | 899 | 256,079 |
| `20232024` | 152,632 | 2,422 | 4,416 | 254,206 |
| `20242025` | 144,278 | 3,372 | 8,434 | 263,989 |
| `20252026` | 146,951 | 4,067 | 1,906 | 260,935 |

reason witnesses by season:

| reason code | `20212022` | `20222023` | `20232024` | `20242025` | `20252026` |
|---|---:|---:|---:|---:|---:|
| `count_accounting_conflict` | 40 | 42 | 28 | 48 | 60 |
| `event_evidence_unresolved` | 164 | 154 | 224 | 172 | 175 |
| `horizon_unavailable` | 16 | 0 | 0 | 0 | 0 |
| `identity_conflict` | 654 | 237 | 165 | 135 | 130 |
| `membership_unavailable` | 2,172 | 933 | 4,483 | 8,444 | 1,937 |
| `strength_conflict` | 266 | 69 | 62 | 35 | 25 |
| `unmatched_report_attempt` | 162 | 153 | 216 | 221 | 171 |

per-code known resolved excluded seconds by season; reason-code rows cannot be added within a season because one segment may carry multiple codes:

| reason code | `20212022` | `20222023` | `20232024` | `20242025` | `20252026` |
|---|---:|---:|---:|---:|---:|
| `count_accounting_conflict` | 74,310 | 75,757 | 50,348 | 82,697 | 109,809 |
| `event_evidence_unresolved` | 2,310 | 2,075 | 2,946 | 2,384 | 2,225 |
| `horizon_unavailable` | 0 | 0 | 0 | 0 | 0 |
| `identity_conflict` | 13,368 | 3,776 | 2,440 | 1,206 | 940 |
| `membership_unavailable` | 931 | 987 | 2,250 | 859 | 893 |
| `strength_conflict` | 2,953 | 653 | 196 | 88 | 45 |
| `unmatched_report_attempt` | 5,675 | 2,114 | 2,969 | 7,870 | 2,221 |

among 5,215 games with zero known resolved excluded seconds, 877 still have reason witnesses. a zero here states only the absence of a resolved segment exclusion: the coverage separately records 542,339 unresolved known seconds and one game with unknown horizon, whose missing duration is not assigned zero. source events remain available independently of excluded rate time; downstream consumers own any further model-applicability restrictions.

source event counts by kind and outcome (`null` is the recorded absent outcome; a zero means that kind/outcome pair has no row in that season):

| kind | outcome | `20212022` | `20222023` | `20232024` | `20242025` | `20252026` |
|---|---|---:|---:|---:|---:|---:|
| `blocked-shot` | `block` | 35,375 | 38,615 | 44,677 | 43,877 | 40,866 |
| `delayed-penalty` | `null` | 1,752 | 2,185 | 3,376 | 3,210 | 3,384 |
| `faceoff` | `null` | 74,251 | 74,659 | 74,188 | 74,296 | 73,496 |
| `failed-shot-attempt` | `null` | 0 | 27 | 13 | 7 | 15 |
| `game-end` | `null` | 1,312 | 1,312 | 1,312 | 1,312 | 1,312 |
| `giveaway` | `null` | 23,513 | 22,656 | 20,233 | 39,364 | 40,366 |
| `goal` | `null` | 717 | 681 | 640 | 713 | 796 |
| `goal` | `goal` | 7,657 | 7,793 | 7,628 | 7,357 | 7,554 |
| `hit` | `null` | 60,186 | 59,077 | 59,648 | 56,293 | 53,658 |
| `missed-shot` | `null` | 138 | 97 | 109 | 83 | 139 |
| `missed-shot` | `miss` | 30,286 | 32,098 | 35,354 | 38,021 | 39,029 |
| `penalty` | `null` | 9,696 | 10,063 | 10,008 | 9,011 | 9,692 |
| `period-end` | `null` | 4,326 | 4,333 | 4,290 | 4,284 | 4,381 |
| `period-start` | `null` | 4,334 | 4,334 | 4,290 | 4,285 | 4,381 |
| `shootout-complete` | `null` | 103 | 95 | 82 | 77 | 119 |
| `shot-on-goal` | `null` | 385 | 322 | 316 | 256 | 394 |
| `shot-on-goal` | `save` | 74,854 | 73,742 | 71,399 | 66,315 | 64,976 |
| `stoppage` | `null` | 57,199 | 57,260 | 57,734 | 58,684 | 57,202 |
| `takeaway` | `null` | 18,572 | 19,383 | 18,379 | 12,628 | 12,099 |

completeness cells are `available / partial / unavailable / not applicable`, using the coverage member’s own denominator: game for order/score/frame, season-person for identity, person-game for history, event for event context, chunk for elapsed context and attempt for immediate stop/reattempt. a partial record retains supported subfields and does not become a complete observed fact.

| field / denominator | `20212022` | `20222023` | `20232024` | `20242025` | `20252026` |
|---|---:|---:|---:|---:|---:|
| `order` | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 |
| `score` | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 | 1,312 / 0 / 0 / 0 |
| `frame` | 1,185 / 127 / 0 / 0 | 1,205 / 107 / 0 / 0 | 1,172 / 139 / 1 / 0 | 1,301 / 11 / 0 / 0 | 1,306 / 6 / 0 / 0 |
| `identity` | 0 / 1,147 / 0 / 0 | 0 / 1,077 / 0 / 0 | 0 / 1,041 / 0 / 0 | 0 / 1,041 / 0 / 0 | 0 / 1,063 / 0 / 0 |
| `history` | 0 / 52,460 / 0 / 0 | 0 / 52,460 / 0 / 0 | 294 / 52,174 / 0 / 0 | 313 / 52,160 / 0 / 0 | 435 / 52,043 / 0 / 0 |
| `event_context` | 307,677 / 96,515 / 464 / 0 | 349,212 / 59,111 / 409 / 0 | 260,113 / 153,107 / 456 / 0 | 316,465 / 103,090 / 518 / 0 | 328,833 / 84,515 / 511 / 0 |
| `elapsed_context` | 1,147,643 / 278,678 / 0 / 0 | 1,548,919 / 209,103 / 0 / 0 | 1,131,820 / 568,841 / 0 / 0 | 1,364,325 / 315,243 / 0 / 0 | 1,445,746 / 302,335 / 0 / 0 |
| `immediate_stop` | 82,481 / 0 / 476 / 66,455 | 81,493 / 0 / 438 / 71,417 | 78,983 / 0 / 447 / 80,693 | 73,646 / 0 / 524 / 82,452 | 72,501 / 0 / 508 / 80,745 |
| `reattempt` | 74,832 / 0 / 476 / 74,104 | 73,715 / 0 / 438 / 79,195 | 71,371 / 0 / 447 / 88,305 | 66,296 / 0 / 524 / 89,802 | 64,953 / 0 / 508 / 88,293 |

## costs and consumer limits

the closed direct-fact json schema repeats located evidence and missing reasons. real preparation occupies 397.8 gb and takes 9.37 hours. the five full-reader measurements above resolve the recorded storage-cost issue; this delivery retains the specified representation. a normalized store requires a separate storage-contract change behind the same factual reader meanings. [two bounded optimization candidates](operating-review.json) showed modest or negligible measured benefit and were rejected without changing production.

conservative run exclusions and conflicting individual-component omissions lose usable time rather than invent exact participation. elapsed workload is intentionally piecewise constant. missing history and optional normalized height remain missing. two game-at-a-time passes retain compact prior-game summaries rather than every event in memory. these choices preserve the selected meanings at the cost of support, disk, source rereads and downstream decoding time.

consumer contracts must keep `feature_facts.outcome` and `immediate_outcomes` out of predictors and select named predictor groups explicitly. the reused `prior_shorthanded_side` means the prior side with fewer skaters, including extra-attacker states; it does not prove penalty expiry. verified source order can place review goals after a same-clock stoppage; [episode source-order issue](../../issues/episode-source-order.md) requires an explicit execution-consumer decision about outcome-dependent availability. no causal, calibration, ability or scientific admission claim follows from this implementation.

at the detached v1-01 boundary, `analysis_cli.main(argv=None) -> int` exposed only `prepare`: required `command` subparser, no flag abbreviation, existing `cli.Once`, `prepare_analysis(selection, out)`, absolute manifest path on success/0, contract/io/value errors on stderr/1 and argparse errors/2. that two-way handoff with v1-13 was historical. the integrated command now exposes v1-01 `prepare`, v1-13 `publish` and v1-03 `facts`; their preparation, publication and factual-reduction owners remain separate. neither detached fixture set depended on execution of the other.

the completed detached phase's [test deletion receipt](test-deletion.json) retains its identities and outcomes. after real acceptance and independent final review passed, the remaining temporary tests/controllers, probes, shadows and cheap failed/profiling outputs were deleted; [the real deletion receipt](test-deletion-real.json) records 183 files, 4,026,247,695 bytes and exact hashes. original fixtures, checked facts, completed external proofs and both final artifacts remain. no persistent harness or dependency was added.

the [real selection](selection-real.json) fixes all five 03n paths/hashes. the completed preparation used this command once and wrote the frozen external artifact:

```sh
uv run --project analysis hockey-stats-analysis prepare \
  --selection docs/research/evidence-v1-01/selection-real.json \
  --out /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02
```

the [checkpoint](pause-2026-10-23.json) retains the historical two passing receipts and three partial source streams from the requested pause. the later [source](real-source-reconciliation.json) and [reason](real-reason-coverage.json) merges supersede those partial streams. the [plan](../../plan.md#current-boundary) records completion and owns further progression.
