# 04h implementation verification

status: implementation and detached verification complete; **research execution blocked by selected external input reads**. this is not completion of the full [04h specification](../../specs/04h-attribution-resolution.md). [the plan](../../plan.md) owns progression; the [input issue](../../issues/04h-research-inputs.md) records the blocker and closure criteria. no research protocol/result, scientific decision, nomination, admission or handoff is issued.

## implementation and ownership

branch `codex/04h-attribution-resolution`, worktree `/Users/nnandal/Documents/code/hockey-stats-04h`. the primary checkout's ten draft documents were copied into the worktree and preserved in `f4ebb71`; the primary checkout was not edited. producer `fbdc47016478fdbed257ae43e43891743df37c47` implements the study with the existing locked python environment and no new dependencies. later changes remove two unused imports and document verification; numerical behavior is unchanged.

three native subagents implemented source/pooling, known-law algebra and study execution. the primary implemented reporting and independent acceptance checks. cross-owner reviewers checked each boundary; authors did not supply their own sole approval.

- `attribution_data` binds the six named 04g manifests, truth identities and assessment-only statistic/control chains. calibration records retain deterministic truth metadata. no complete 04f traversal, directory discovery or historical migration is used.
- the same owner aligns annual likelihoods by player identity, preserving entrants, absence, the changed returner and retired nuisance rows. context remains separate by season; final exposure weights own centering.
- `attribution` owns the finite marginal-likelihood selector and explicit reusable fixed-design factors. it reuses `fixed_shape_update`; exact zero is a separate model. the selector accepts training moments and no truth.
- `attribution_simulation` owns the extracted physical truths/regions and collapsed known-law score moments. `attribution_prediction` owns expected excess and signed context coupling. historical callers use these owners directly; their old streams and verdicts remain unchanged.
- the study owns fixed conditions, calibration/assessment separation, expected recovery, numerical probes, compact cell arrays and bootstrap summaries. the reporting module owns one complete csv, one limits/context table, one figure and a concise decision.

constant pooling changes persistence and selector assumptions; eleven modes also lose spatial detail. the fixed reference is selected with calibration truth and cannot be deployed. adaptive risks use realized saved-response errors, never fixed-variance formulas evaluated at a response-selected penalty. working covariance remains numerical evidence, not calibrated player uncertainty.

## red, green and adversarial review

temporary checks began red at the absent cli and absent moment/pooling interfaces. after implementation they passed, then passed again after refactoring and independent review. the final verification used the clean producer above.

| boundary | independent evidence | result |
|---|---|---|
| source/pooling | six selected fixture cells × two representations; direct stacked exposure rows, independent normal equations/objectives, reordered identities, separate annual contexts, unequal references, entry/absence/return and inseparable averages | passed |
| factor reuse and identity | seventeen nonzero factors reused across two response records; retired nuisance rows remain coupled; final-season gauge differs from a historical gauge | passed; maximum eigensolve objective difference `3.64e-12` |
| known-law moments | explicit tiny full recorded-count covariance under both laws; nonzero physical exposure means/coupling, shared game pace, independent copies, null equality and omitted detail | 121 comparisons passed; maximum absolute residual `2.84e-14` |
| complete risk curves | independent full-count covariance pushforward for both laws, two amplitudes, one/two game copies, two/one modes and all eighteen penalties including exact zero | 2,592 comparisons passed; maximum absolute residual `4.80e-14` |
| study mathematics | independent dense exposure-row contractions of all 684 fixture grid records and twelve adaptive fits; actual physical targets, functional operators, signed projection cross terms and calibration-only selection | passed at `atol=1e-10,rtol=1e-8` |
| saved-array assessment | complete diffuse/game-pace and observed-null/gaussian fixture cells; direct native exposure scoring, original physical truth bodies, mean/ratio/root units and nondegenerate 100-record bootstrap arithmetic | 2,421 comparisons passed at the same tolerances |
| detached integration | prepare → six fits → assess with external/network access forbidden, unselected manifests/chains/calibration statistics forbidden, response generation/annual fitting/scale selection forbidden, and assessment fitting forbidden | passed; six source statistic archives and thirty selected annual states |
| numerical probes | independent eigensolve enumeration of all eighteen penalties, centered means/covariances, contexts, physical predictions, objectives, expected risks and original equations | all twelve fixture probes passed |

review repaired reference/context field collisions, seconds-to-minutes conversion, missing explicit basis columns/source-score names, incomplete consumed-reference reconciliation, and selected-only posterior/prediction probes. prediction comparisons now use physical rates. source scale and inherited limitations remain in their denominators and visible in the limits table. context includes raw exposure/count fields, not old fitted interval claims.

the compact [known-law fixture](../../../fixtures/attribution/known-law-moments.json) retains the independently checked count-covariance inputs and expected moments; its 82-array archive is 30,305 bytes. extraction parity preserves 75 annual physical truths at outers 0/51/199, activation and region bytes on nonuniform synthetic shares. parity using the actual research shares still requires the unread external basis.

## bounded fixture execution

the explicitly named schema-5 fixture source was constructed temporarily through the existing 04e/04g fixture interfaces. it has six selected cells, outers 0/1, five years, the same player/native/basis dimensions, calibration `{0}` and assessment `{1}`. its uniform native reference and smaller deployment retain their own identities. source numerical limitations remain explicitly visible. no fixture output satisfies research acceptance.

| executed fixture work | count |
|---|---:|
| selected cells | 6 |
| non-null / analytic-null grid records | 576 / 108 |
| pooled point fits | 12 |
| source control histories / annual states | 6 / 30 |
| independent eigensolve probes | 12 |
| new research responses / annual fits | 0 / 0 |

the guarded final pipeline completed in about 3.49 seconds. fixture intervals have one assessment record and are degenerate; a separate 100-record arithmetic oracle checks nontrivial paired means, roots, ratios and linear-percentile interpolation. it creates no research responses, fit or scientific conclusion. the public command-line path and independently reconciled report are recorded in the [verification receipt](verification.json).

## research execution

the committed 04g result/protocol sha256 values are `84bb4d034bb2213ce8b1cf0cf91fe54713fa7ba797e684f329838b16d05266a6` and `9e8266d1b0f7883d284e677be1e607f3cd8593264c3a5e95e9909acbfb3b8ef2`; the 04a contextual result is `8b1f9bfd2ba48acf81f7c23db97d5e37c81bc2e17cec86666f0aece4551a49ac`. these local metadata digests pass. external basis/design/operators, six fit manifests, selected statistic/control originals and the assessment reference remain unverified in this execution. ordinary reads stalled and were interrupted. no source was modified and no research run directory was created. the final [research preflight](reviews/research-preflight.json) on clean merged branch `08c31b5` locates the block at opening the pinned 04g prepared metadata. the concurrent 05b specification is incorporated without changing the reviewed numerical code or closing the research assignment.

once those files are readable, invoke the existing cli from the repository root with the existing environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=analysis/src:analysis/research \
  /Users/nnandal/Documents/code/hockey-stats/analysis/.venv/bin/python \
  analysis/research/attribution_resolution.py prepare \
  --source-result docs/research/attribution-04g/result.json \
  --real-context docs/research/attribution-04a/result.json \
  --purpose research \
  --output /Volumes/Expansion/hockey-stats/runs/attribution-04h-20261017
```

run `fit` once for each explicit sparse/diffuse/null × gaussian/game-pace cell, with that `prepared.json` and a new output subdirectory. pass the six exact `fit.json` paths to `assess`. no controller, resume engine, new response generation or search expansion is needed. completion still requires the full 57,600/108 grid records, 1,200 pooled fits, 600 original histories/3,000 states, twelve research probes, independent full-cell assessments and reviewed research reports. acceptance does not follow from the fixture result.

temporary integration/live scripts, generated fixture trees and bytecode are removed after final review; compact receipts and useful checked fixtures remain. the verification receipt records cleanup and final document checks. current source evidence, expensive fits, published databases, frozen paths and the main environment remain untouched.
