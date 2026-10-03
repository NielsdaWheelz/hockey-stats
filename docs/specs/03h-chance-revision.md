# pr03h — saved-candidate eligibility assessment

status: **specification ready for handoff; docs only. implementation/assessment require separate assignment.** 03g is reviewed and merged in `42e1ef7`; [its decision](../research/chance-03g/decision.md) recommends `assess_integrated`. 03b remains rejected and 03e withheld. [brief](../brief.md) · [plan](../plan.md) · [03i follow-up](03i-chance-revision.md)

## target and boundary

decide whether a calibration condition necessary under the retained project admission rule already disqualifies the saved composition from the unchanged all-attempt spatial-opportunity research use. apply the inherited 03e rule to overall probabilities and each predictor's own bins, using saved predictions. a decisive failure justifies `withheld`; otherwise report `further_assessment_required`. neither outcome admits a model or supplies a 04 handoff.

this is retrospective reassessment of an inspected candidate on research-exposed seasons. freeze the execution protocol before new interval arithmetic; do not call it untouched confirmation or pretend criteria were selected before seeing 03g. inherited margins are project tolerances, not universal scientific standards or bounds on player-value error.

include one saved candidate, three probability quantities and one stream pass. exclude preparation, prediction, scoring, fitting/em, calibration correction, acquisition, structural changes, sensitivity/transfer/final campaigns, player attribution, publication and new figures. [03i](03i-chance-revision.md) retains later selected work. conditional research permission does not waive a decisive probability failure.

## inputs and reconstruction

read `/Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json`, sha256 `8f4e098acb1b9b8ece3a989beb5e6a6d631d8ac32e3f7402923b59425d78080b`. its linked comparison is `e2d825297f5dd5a02871595a101d4a458a1c0546742f1acb9c8068a9f51e5e3c`, composition `d9c5f3773dfcb803cc7bcd3d41fd0c90025282247bfd3ffcc698eed13040a6d9`, and attempt stream `2830f700f4304c24da332cc34467670b9970f66f7d18de6791d8ca74754daca9`. validate actual hashes, current schema-1 artifact kinds/purpose and cross-links; preserve original execution/parent identities separately from this assessment. use these completed outputs without reopening fitted parents or a raw-corpus audit.

`purpose` is `research` or `fixture_exercise`, must agree across completion/comparison/composition, and propagates unchanged into outputs. fixture or synthetic evidence cannot become research evidence by relabeling.

the composition retains training through `2024-12-31` and the original 712 later 2024–25 assessment games: 85,317 recognized rows; 68,775 eligible, 16,270 outside scope, 272 unavailable. eligible outcomes are 49,014 unblocked, 19,761 blocked and 2,804 goals. use the comparison's recorded per-game order and dates consistently. all selected games remain, including zero-contribution games for a bin.

03g retains aggregate own bins but deliberately omits their per-game bins. recover those with one read of `attempts.jsonl`; do not average aggregate bins or rerun the model. stream these saved fields:

| quantity | prediction under `predictions.revision` | applicable / positive |
|---|---|---|
| `unblocked_conversion` | `candidate_r` | eligible and unblocked / `goal` |
| `all_attempt_recorded_context` | `candidate_all` | every eligible attempt / `goal` |
| `marginal_unblocked` | `candidate_unblocked` | every eligible attempt / `not blocked` |

validate recognized `(game_id, source_index)` keys, dates/source/event identities and status/label consistency. inapplicable predictions stay null. initialize every game; reuse `binary_record`, `binary_metrics`, `add_binary` and native twenty fixed bins: `[j/20,(j+1)/20)`, last upper endpoint inclusive. use complementary log probabilities without clipping. retain per-game counts, observed positives and predicted sums; reconcile full binary sums, every aggregate bin, game sums, coverage and exclusions to the saved revised summaries with existing `agrees` (`1e-10` relative/absolute). reject malformed/incomplete streams; never silently intersect populations. no copied prediction stream or posterior export.

## inherited rule and verdict

assess overall plus all twenty bins for each quantity; only overall and consequential represented bins are required. consequential means attempt share **OR** predicted-positive-mass share ≥5% of that quantity's whole applicable population. never trigger on observed positive counts. represented nonrequired bins retain descriptive classifications, including `failure`, but cannot cause withholding. keep empty bins visible without making them blockers. the anchor-defined cohort remains linked diagnostic evidence; it cannot replace revised own-bin calibration.

| quantity | overall rate margin | required own-bin rate margin |
|---|---:|---:|
| either goal quantity | ±0.0025 | ±0.01 |
| marginal unblocked | ±0.01 | ±0.03 |

residual is predicted minus observed rate. these are proportions: multiply by 100 only for displayed percentage points. reuse `ratio_interval` and `calendar_blocks`: 2,000 `PCG64` draws, seed `3032026`, pointwise 95% linear percentiles, pooled sums/counts. retain whole-game, seven-calendar-day and fourteen-calendar-day results; blocks start at the first selected date and retain empty blocks/final partial blocks. any undefined draw makes that interval null, without redraws. report contributing games/blocks separately; intervals omit fitting, selection and origin-law uncertainty.

for each required criterion/method, retain the exact historical order:

1. missing interval → `insufficient` with reason.
2. lower endpoint > positive margin or upper endpoint < negative margin → `failure`, even with fewer than 100 contributing games or constant labels.
3. interval extending beyond a margin while intersecting it → `insufficient`.
4. otherwise, constant labels or fewer than 100 contributing games → `insufficient`; whole interval inside the margin with adequate support → `support`.

any required failure under ANY declared resampling method yields `withheld`; retain every failed criterion and all methods. otherwise yield `further_assessment_required`, even if every assessed criterion has support. do not select a favorable blocking scheme, widen margins, omit troublesome context, substitute unblocked-only analysis or filter attempts using their fitted probability. known all-attempt own bin `[0.10,0.15)` has 1,999 attempts, 192 goals and +2.507250 pp residual; this is a warning, not the missing interval result.

this limited screen does not cover all inherited named subgroups/tip evidence, comparator-inferiority checks, spatial adequacy, origin/execution sensitivity or later-season support. these obligations are `not_assessed_by_this_slice`; a failure stops dependent work, not preservation of those obligations. cite 03g's lower proper losses and opposing spatial residuals without declaring either irrelevant. no fresh spatial threshold or claim that factual-probability failure proves opportunity bias/physical-origin error.

## command, artifacts and owners

new outputs live under `/Users/nnandal/Documents/code/hockey-stats-03h-runs`, shared outside git/worktrees. before execution save a short immutable `inputs/protocol.md`, binding this specification, input identities, unchanged rules and executing revision. from the repo root:

```sh
UV_PYTHON=3.14.8 uv run --project analysis python analysis/research/chance_assessment.py --completion /Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json --protocol /Users/nnandal/Documents/code/hockey-stats-03h-runs/inputs/protocol.md --out /Users/nnandal/Documents/code/hockey-stats-03h-runs/assessment
```

use the locked environment and available interpreter patch with its actual identity recorded, as in [03g verification](../research/chance-03g/verification.md). no dependency or interpreter-pin changes are implied. one command; require a new output outside inputs. invalid evidence/numerics returns nonzero without completion; a substantiated scientific withholding completes with exit `0`.

| file/output | owner and explicit contract |
|---|---|
| new `analysis/research/chance_assessment.py` | saved-evidence loading, bin reconstruction, narrow criterion classification and output; reuse strict json, identities/output helpers and binary/bootstrap primitives. do not call `chance_review.assessment_review`: it expects native evaluation schema 3, not a composition diagnosis |
| existing `chance_evaluation.py`, `analysis/research/chance_review.py` | authoritative binary/bin arithmetic and pooled/calendar intervals. reuse rather than copy; no unrelated refactor |
| `assessment.json` | schema 1, `artifact_kind: chance_necessary_calibration_assessment`, purpose, protocol/completion/composition/stream/comparison/implementation identities; population/coverage; quantity `overall` and twenty own-bin records; per-game additive sums; criterion ids, counts/shares/required reason, margin, all three intervals/support facts/classifications; `decision`, `blocking_criteria`, `remaining_obligations`, measured resources |
| `completion.json` | schema 1, `artifact_kind: chance_necessary_calibration_assessment_completion`; input/protocol/output identities and resources; written last after reconciliation |
| `docs/research/chance-03h/` | short protocol, verification and decision; existing 03g figures suffice. existing issues retain scientific limitations |

criterion ids are `<quantity>/overall` and `<quantity>/bin/<0–19>`; each method record retains estimate, interval, observed-positive count, contributing games/blocks, undefined draws and classification/reason. empty-bin rates/intervals are null; shares are zero when whole-quantity denominators are positive, and null only when that share's denominator is zero. `decision` is exactly `withheld` or `further_assessment_required`; no admitted status or handoff field. port only the small historical `calibration_fact` logic from `03e-runs/inputs/study-criteria.py` into maintained research code, preserving the original file; no runtime import from an external operator script or general approval framework.

## content, verification and completion

the content owner produces one short decision page: exact declared use and disposition, a compact decisive-evidence table with margins/counts/all methods, and a claim-status table separating factual probabilities, observable spatial outcomes, standardized opportunity and physical origins. distinguish `failure`, `insufficient` and unassessed obligations. link 03g's gains/maps; no new plots or dashboard. name one next hypothesis, if justified, with observation, mechanism, competing explanation and smallest discriminating experiment for 03i. do not prewrite a verdict or declare seasonal pooling the demonstrated cause.

temporary integration/live red → green → refactor → green covers one complete saved-evidence command and independent unequal-game/empty-block arithmetic, boundaries/OR trigger, constant labels/low support, null intervals, nonrequired failures and both dispositions. use explicitly synthetic saved-stream cases alongside preserved 03g fixture artifacts; never label synthetic parameters or labels raw. guard preparation/prediction/scoring/fitting entrypoints against use. mismatched identities, missing/duplicate keys, wrong labels/dispositions and aggregate disagreement reject. after verification delete ALL test code/test-only dependencies; retain useful facts and fixtures.

the real execution reads the saved stream once, hashes during that pass and reconstructs only small per-game/bin accumulators. record actual time/memory/bytes. no original capture copying/rehashing, full posterior duplication or hour-long scoring replay is warranted. an interruption reruns this cheap command; no runner/checkpoint machinery.

completion requires reconciled evidence, unchanged rule classification, all declared methods, correct limited verdict, independent statistical/systems/content review, updated existing issue facts and deleted temporary tests. lower loss remains a real improvement even if this use is withheld. no decisive failure completes with an explicit remaining-assessment list, not positive admission. no 04 implementation/publication or 03i work follows automatically.

tradeoff: this necessary-condition assessment can settle withholding cheaply but cannot establish a complete handoff. remaining validation and structural work move to a separately selected 03i specification instead of a contingent fitting campaign hidden here. the product target and historical verdicts remain unchanged.
