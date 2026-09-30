# chance-2 software verification

date: 2026-09-30. scope: compact committed fixtures only; scientific assessment not performed. 03b remains rejected. no real fitting, recipe selection or player attribution occurred.

## unchanged evidence and reconstruction

all eighteen original capture bundles and three season-reference bundles were rebuilt offline with the installed corpus command. all 240 original files (120 bodies and 120 receipts), 35,066,471 bytes total, retain their preimplementation hashes after final verification. no fixture evidence was corrected or replaced.

the three inventories each contain 1,312 games. six/four/eight original captures are admitted, with 1,306/1,308/1,304 missing. all eighteen selected games retain source identity and reconstruction gaps. the initial rebuild took 10.271 seconds wall and 144,293,888 bytes peak child rss on mac arm64.

## exhaustive eligibility change from 03c

the baseline uses unchanged captures and preparation at the isolated preimplementation revision `ec343c1`. all 2,210 `(game_id, source_index)` attempt keys are identical. recognized attempts remain 2,210; reconstructed genuine-5v5 attempts remain 1,623. the complete transition matrix is:

| 03c disposition | chance-2 eligible | outside scope | unavailable |
|---|---:|---:|---:|
| eligible | 1530 | 0 | 7 |
| outside scope | 0 | 585 | 0 |
| unavailable | 0 | 0 | 88 |

new classifications total 1,530 eligible, 585 outside scope and 95 unavailable. all seven changed rows are listed below; every other row retains its disposition.

| game / source index / event id | new applicable reasons |
|---|---|
| `2025020001 / 180 / 721` | `context_unavailable` |
| `2025020184 / 157 / 103` | `context_unavailable` |
| `2025020184 / 158 / 104` | `type_unavailable`, `physical_attempt_unresolved`, `context_unavailable` |
| `2025020282 / 36 / 139` | `context_unavailable` |
| `2025020282 / 200 / 763` | `context_unavailable` |
| `2025020282 / 282 / 162` | `type_unavailable`, `physical_attempt_unresolved` |
| `2025020307 / 14 / 74` | `type_unavailable`, `physical_attempt_unresolved`, `context_unavailable` |

four ordinary attempts immediately follow unsupported recent `delayed-penalty` records. the other three are one awarded and two own goals with unresolved physical actions. all three goals remain in observed totals and pre-event score accounting; no preceding attempt inherits the goal and no physical shooter is fabricated. admitting the two new exact type pairs creates no additional eligible rows because those rows were already eligible under chance-1, which ignored type.

reason counts below include every applicable reason across all recognized attempts; they are NONEXCLUSIVE and must not be summed as exclusions.

| reason | 03c | chance-2 |
|---|---:|---:|
| `outside_5v5` | 585 | 585 |
| `membership_unresolved` | 2 | 2 |
| `actor_unavailable` | 54 | 54 |
| `location_unavailable` | 139 | 139 |
| `score_unavailable` | 0 | 0 |
| `type_unavailable` | 0 | 47 |
| `physical_attempt_unresolved` | 0 | 18 |
| `context_unavailable` | 0 | 75 |

all 119 recognized goals remain: 54 eligible, 57 outside scope and eight unavailable. excluded-goal reason counts are outside-5v5 57, membership 0, actor 19, location 19, score 0, type 18, physical action 18 and context 18; overlaps include untimed shootout records. selective exclusion is a population change, not proof of improved calibration.

| game | recognized | 03c eligible | chance-2 eligible | outside scope | unavailable |
|---|---:|---:|---:|---:|---:|
| `2023020001` | 126 | 79 | 79 | 47 | 0 |
| `2023020012` | 126 | 90 | 90 | 36 | 0 |
| `2023020013` | 123 | 96 | 96 | 27 | 0 |
| `2023020078` | 98 | 0 | 0 | 12 | 86 |
| `2023020237` | 109 | 89 | 89 | 20 | 0 |
| `2023020955` | 133 | 99 | 99 | 34 | 0 |
| `2024020001` | 125 | 99 | 99 | 24 | 2 |
| `2024020102` | 140 | 86 | 86 | 54 | 0 |
| `2024020340` | 121 | 78 | 78 | 43 | 0 |
| `2024020364` | 117 | 80 | 80 | 37 | 0 |
| `2025020001` | 119 | 99 | 98 | 20 | 1 |
| `2025020006` | 139 | 85 | 85 | 54 | 0 |
| `2025020184` | 119 | 98 | 96 | 21 | 2 |
| `2025020282` | 118 | 84 | 81 | 34 | 3 |
| `2025020307` | 118 | 87 | 86 | 31 | 1 |
| `2025020544` | 140 | 95 | 95 | 45 | 0 |
| `2025020565` | 119 | 102 | 102 | 17 | 0 |
| `2025021094` | 120 | 91 | 91 | 29 | 0 |

## independent context evidence

an independent temporary check read original play-by-play sort orders and coordinates rather than calling the preparation context implementation. all eighteen games passed: 627 recent records, including 28 within one recorded second and 152 opponent-owned predecessors; 1,504 irrelevant predecessors older than five seconds; four valid reset barriers; six unsupported recent actions; three identity failures; 41 unsupported focal-clock records; 24 owner/frame failures; and one timing failure. these dispositions cover every recognized attempt; their detailed failure reasons can overlap.

the check independently verified immediate-predecessor ownership, current-team rotation, source-side conflicts, clock boundaries and no skipping of excluded records. preparation checks additionally inject valid and invalid kind/code reset pairs, supported period transitions, missing identity/type, scheduled first/middle/last minute boundaries, contradictory/missing sides, own/awarded/penalty goals and unknown exact type spellings.

## numerical and installed-command verification

temporary installed-command checks were written before workflow implementation. the original installed workflow rejected the target schema-2 configuration with `candidate configuration keys do not match schema 1`. the new fit/evaluate/score workflow passed, then passed again after artifact composition was repaired. no configuration values were changed.

| bounded exercise | result |
|---|---|
| training | three season openers; 276 eligible attempts; target-season reference has 98 attempts across 36 joint pairs |
| starts | uniform converged in 26 updates; unblocked-multinomial start converged in 23 |
| selected | uniform; penalized observed objective `-1650.971365386996`; maximum posterior total variation `3.187223309235719e-7` |
| assessment | one strictly later game; 91 eligible attempts, including 62 unblocked |
| scoring | 2,210 recognized rows; 1,530 valued, 585 outside scope, 95 unavailable |
| origin basis | 1,087 recorded proxies; 443 complete conditional block distributions |
| installed resources, frozen revision | fit 3.688 seconds; evaluation 0.368 seconds; score 3.584 seconds; peak child rss 212,729,856 bytes (202.9 mib) |
| artifacts, frozen revision | standalone model 2,372,364 bytes; complete scored directory 33,217,332 bytes |

finite schema-2 artifacts, saved model/reference immutability during assessment, stream digest, all per-game row counts, full origin normalization and spatial-value conservation within absolute `1e-10` passed. an independent arithmetic check recomputed candidate and benchmark log loss, brier score, probability sums, twenty calibration bins, all strata and per-game summaries from saved predictions. empty strata retain null rates. every probability summary names `goal` or `unblocked` and uses `observed_positive_count`; canonical-type strata include blocks.

adversarial artifact review found a real composition error: overlaying diagnostic fields on model fields replaced benchmark coefficients in `fit.json`. successful fit reports now retain the complete model with nested diagnostics; a dedicated installed check verifies all benchmark coefficients, origin coefficients and diagnostics match `model.json`. a separate review found an omitted explicit reference season in score/evaluation summaries; both now save `reference_season` alongside joint-pair weights. these fixes concern artifact meaning and preservation, without changing fitted probabilities.

successful `fit.json` intentionally repeats complete coefficient/layout evidence while `model.json` remains sufficient for scoring. this small disk duplication satisfies the explicit artifact contract. complete block distributions cost about 32 mib for this compact selection; bounded exact reference reuse avoids a global context-by-cell-by-pair tensor. the three-season fixture fit exercises seasonal state and history software without scientific power or a recipe choice.

independently enumerated numerical checks passed analytic gradients for origin maps, avoidance, conversion, both benchmarks and every penalty/history family; likelihood sums before logs; softmax and forward-kernel normalization; fixed e-step weights; complete penalized-objective accounting; exact target-season joint probability products; coordinate-invariant recorded-context probabilities; and origin/opportunity conservation. changing a focal block coordinate changes its conditional posterior while leaving recorded-context marginal probabilities fixed when admissible context is held fixed.

numerical interruption during the second start resumed from its preceding accepted state and reproduced coefficients, reference and diagnostics EXACTLY. failed inner solves retained the preceding accepted origin/avoidance coefficients; failed origin initialization invalidated only its start. malformed states, changed objective histories, unsupported seasons and malformed model/reference evidence were rejected. contiguous zero-observation intermediate seasons, stage-specific observed/other-seasons-only/unseen actors and unseen zero prior modes passed.

source/preparation red → green → refactor → green checks passed independently. all eighteen exposure, membership, frame and score facts survived the hard schema cutover. each owner and the root reviewer checked the other modules' public contracts. original fixture bytes were never edited. temporary test code, the frozen baseline code copy and sandbox profiles were deleted after final green. useful derived facts and artifacts remain under ignored `var/`; no test-only project dependency was introduced.

## frozen installed recovery and detached operation

final installed verification used clean code revision `12436fe1898493ef157a5d355c1e1622dc54edd5`, python `3.14.7`, numpy `2.5.3`, scipy `1.18.1` and lock digest `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`. a temporary macos sandbox denied all network access, reads under `/Volumes`, and reads under `/Users/nnandal/Documents/code/hockey-stats-raw`. all eighteen games were rebuilt from committed captures/references within that sandbox. per-season corpus wall times were 3.252, 2.387 and 4.490 seconds. commands used the documented corpus/fit/evaluate/score interfaces, with regenerated explicit selections under `var/03d-final/inputs/` and artifacts under `var/03d-final/results/`.

the scoring sandbox additionally denied the frozen training corpus directories, training selection and `fit.json`. scoring all eighteen games through the separately rebuilt fixture corpus still succeeded using `model.json` alone. all 2,210 rows, per-game counts, stream digest, complete block distributions, reference-season labels, finite probabilities, origin normalization and expected-goal conservation passed. assessment and scoring left model bytes and reference membership unchanged.

an actual installed fit process was terminated after accepted em iteration two. its checkpoint resumed into a new directory in 3.205 seconds; a completed checkpoint resumed in 0.425 seconds. both reproduced origin/stage/benchmark coefficients, joint reference and all numerical diagnostics EXACTLY. altered accepted coefficients, mismatched implementation binding, old model versions, missing model evidence, overlapping games and occupied outputs failed with exit one. help/syntax returned zero/two. malformed reference goalie ids and incomplete provenance were actual review findings; the owning model decoder now rejects them and reconciles reference/actor evidence by stage and season.

a second bounded fixture fit began in `20242025`. scoring earlier fixtures yielded 453 additional unavailable rows with `season_unsupported`, null values and no fabricated state. totals reconciled to 1,077 valued, 585 outside scope and 548 unavailable. a disjoint earlier assessment and fixture-to-research relabeling were rejected. an actual score process was terminated after writing a partial stream; `score.json` remained absent, reuse was rejected and the fitted model remained intact.

source-order review also repaired two evidence boundaries: unique source order retains predecessor identities even when known clocks contradict chronology; an unknown goal clock invalidates score support without preventing a valid kind/code reset. unavailable context remains unavailable when chronology is contradictory. these changes preserve evidence without inventing timing or selecting a preferred predecessor.

the resolved credited-scorer and type-admission issue records were removed. physical actions for own/awarded or unresolved goals remain unknown and withheld; contradictory types retain their original evidence and explicit `type_unavailable`. the fixtures and this record preserve those facts. physical-origin accuracy, excluded-goal selectivity, calibration, seasonal transfer and kernel/origin sensitivity remain scientific responsibilities in 03e; the existing scientific issue records remain open. 04 remains withheld.
