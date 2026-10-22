# 04o verification

status: implementation and assigned research execution verified. the result is `execution_status:complete,numerical_status:verified,study_status:diagnosed,nomination:null,admission:not_admitted,handoff:null`. adoption remains undecided. [decision](decision.md) answers prediction and player sensitivity separately; [the specification](../../specs/04o-attribution-context.md) remains the acceptance contract.

the user assigned the whole specification in branch `implement/04o-attribution-context`, worktree `/Users/nnandal/Documents/code/hockey-stats-04o`. input snapshot `b6295d0` preserves the supplied specification and concurrent drafts. primary source and the observed website remain outside implementation. expensive outputs and receipts live under `/Volumes/Expansion/hockey-stats/runs/attribution-04o-20261021/`; the directory date records assignment, while execution completed on 2026-10-22.

three non-astra agents implemented source/design, numerical fitting/commands, and prediction/assessment/reporting. root cross-reviewed their boundaries; an independent claude session challenged source, mathematical, statistical and rendered-content claims through skid. final content review and temporary-check disposal are recorded below.

## identities and population

all supplied 04n bindings verify exactly. paths in this table are relative to `/Volumes/Expansion/hockey-stats/runs/attribution-04n-20261021/`, except the repository result.

| input | sha256 |
|---|---|
| `docs/research/attribution-04n/result.json` | `7245ab4873945ebaa0b58d0cd46a11ab9087e1196b4c1258770b304a7664ae6f` |
| `prepared/prepared.json` | `26ecaa961af968e936067ff31002283150bc7278adba7b7121e52c936358c902` |
| `prepared/protocol.json` | `1dae2c1f696b14c3af7456b25534d3c0f6fdb30775788ca4599dc0eeee17121a` |
| `prepared/correction.json` | `41fd7c3a5b79dee24e91335ca2eda0132feffa0120b5266f0e0c386037daad27` |
| `fit/fit.json` | `154f6e6324e3144eb6aa74aebcaabc2b6a860e123faca4b297328a087329bbcb` |
| `assessment/assessment.json` | `748b3634ce966e607fbd1d3e9bbd29c9f0ce2c84d662b797f23228725d48d558` |

clean analytical producer `b59ce06c57bcc0783e11892d9e104f9e0ddae579` completes preparation, fitting and assessment. its prepared artifact retains the original specification snapshot, sha256 `1cefbc43102b34a7822aebb52574c6eb8f5c4123c15c8e1866a2e2c48cda7ff4`. the final report uses clean producer `2fac80e51f8fffe658390718e661bbbd7f8e7fbc`; later changes remove fixture setup residue and refine report labels/layout/cost measurement. no completed preparation, fit or assessment is replaced.

| output under the new external root | sha256 |
|---|---|
| `prepared/prepared.json` | `6cf727418b005641519f3c9f4765a0ffd29c3b22f592de369f3e804837954d4d` |
| `fit/fit.json` | `5a1f6edb7bc3cbd5ed09119b01cacafd42931b03d00b441f63b7261fded71a05` |
| `assessment/assessment.json` | `52960f8ac704e0ce45d86ec12625b3b3c2306bfa03900ceb8abaf24a183485c6` |
| `report-final-05/result.json` | `a71fb0d8d01aaefd802fb1cfcc2dfc2ce22c55e4243b59faf4ecd0ddfa9e2309` |

all 6,560 inventory games, 4,183,800 corrected directed rows and 432,136 retained events reconcile. the accepted six zero-count exclusions remove 132 physical / 264 directed seconds without losing events. all nine frozen coarse arrays per year, seven grouped moments, support and ten control parent inputs match exactly. final training remains 1,051 games / 68,906 counts / 1,682.973333 directed hours; assessment remains 261 games / 17,331 counts / 421.448333 directed hours. zero-time inventory games `2025020544` and `2025020565` remain included. all five seasons remain research-exposed.

## source/design acceptance

[`attribution_context.py`](../../../analysis/src/hockey_stats/attribution_context.py) owns the eighteen-column basis, exact exposure/event moments, centering and residualization; [`attribution_data.py`](../../../analysis/src/hockey_stats/attribution_data.py) owns frozen source bindings and state codecs. no study controller becomes a library.

- the counted five-season fixture exercises all eighteen columns, zero-event time, a goal, simultaneous events, inclusive endpoints, clipping saturation, regulation `1200` and coarse overtime. independent quadrature/event calculations check 65 games and five annual raw joint-design projections. training-isolation perturbations, typed codec roundtrips and wrong assignment/context/correction/rank failures pass.
- every real annual design has rank 18; diagonal-scaled correlation conditions range from 10.57 to 12.30. the independent raw joint `[z,h0]` audit reproduces candidate information and scores within `2.28e-13`, with solve residuals below `1.66e-16`.
- the independent reviewer integrates the first 60 real source-order games directly from original ledgers, including the rescheduled game below: 26,886 directed rows and 3,851 events. saved per-game raw moments agree within `6.7e-16`. structural zeros, exposure bounds and training-only centering are checked over all 6,560 games. this bounded oracle is distinct from the full production reconciliation.

first preparation at `c205891` stops before any prepared output or fit: the new cursor assumes lexicographically sorted ledgers. frozen coverage instead follows original producer traversal, placing `2021020015` before `2021020007`. the latter has 428 directed rows, 5,238 directed seconds and 60 counts, so treating it as empty is wrong.

repair `b59ce06` consumes the hash-bound frozen coverage order once, joins one game at a time and writes moments into canonical sorted axes. duplicate, noncontiguous and outside-inventory groups fail; missing groups still require zero frozen moments. the non-monotonic fixture preserves canonical arrays exactly. assessment stays in sorted order for frozen bootstrap indices; sign replay stays in source order for control witness ties. ledger order is never used to reconstruct pre-score. `reviews/prepare-01.log`, `prepare-01-stop.json` and subsequent green receipts preserve the failure and repair; no raw evidence, population or tolerance changes.

## fit/composition acceptance

[`attribution.py`](../../../analysis/src/hockey_stats/attribution.py) adds the typed score-only scalar API over the existing annual numerical machinery. the old energy-bearing API stays strict for its retained consumers. shared prediction/composition and general-Gram contractions belong to [`attribution_prediction.py`](../../../analysis/src/hockey_stats/attribution_prediction.py). the study owns only fixed policy, classifications and commands.

independent tiny-matrix proper-prior precision solves verify entrants, carried-only innovation, changing annual rates, unchanged league-relative carry, both role gauges and full centered covariance. an analytic variance optimum of `0.15` exercises interior selection, refinement and the bounded probe. saved scalar controls reproduce the full/score objective constant offset without optimizer reselection or rewritten curves; maximum omitted-constant discrepancy is `1.1642e-10`.

the real fit contains twenty selected states: ten new candidate states and ten exact control reuses. every scale search is resolved without endpoint or inherited flags. `execution` names this study's new/reused status; retained control `origin` names historical 04n/04m provenance. every original parent, likelihood, axis and reference is checked.

`reviews/independent-fit-audit.json` independently solves all twenty primary posteriors and twenty fixed-history probes without production fitting/optimizer calls. maximum raw/centered coefficient discrepancy is `4.74e-15`, full gauged covariance discrepancy `1.74e-16` and primary equation residual `5.19e-15`. probe residuals remain below `5.60e-15`; maximum league-relative current-player movement is `2.420e-6`, below `1e-4`. `independent-probe-bindings.json` verifies all twenty alternative parents, likelihoods, sources, axes, references and original scales. alternatives do not replace primaries or propagate histories.

## assessment acceptance

independent direct exposure/event arithmetic verifies all 21 loss quantities, nonzero regional interaction, zero native interaction, common physical units and complete/volume/shape identities. constant, linear, repeated-root, boundary and near-tangent cases verify strict negative intervals, mass and one-sided extrema. a 10,000-case exact-decimal discriminant oracle checks compensated arithmetic; numerical tolerances never clip physical rates.

the real held-out replay reconciles all 177,098 directed rows and 17,331 events. shape sums and complete-minus-volume sums are below `2.85e-14`. zero-temporal embedding reproduces frozen 04n controls: 16,443 metric-game contractions, 189 interval comparisons and all three constant-control sign diagnostics, with exact integer counts and witness identity.

`reviews/independent-assessment-audit.json` uses raw uncentered moments and independent augmented arithmetic, without production imports. it verifies all 87,696 game × variant × metric numerators (maximum discrepancy `2.79e-12`), all 1,008 interval rows (endpoint discrepancy `5.33e-14`), 1,880 primary player rows, 360,960 variant regional changes, 192 support rows and all six physical minimum witnesses (`2.67e-15`). independent calendar/PCG64 draws, pooled ratios, directions, minutes and player summaries agree. a separate claude bootstrap recomputation also reproduces every interval and direction. neither audit reruns a native sign campaign.

all sixteen final-component variants preserve the primary `unresolved` regional direction. candidate-minus-control complete regional loss is `+0.00665404`; all three intervals cross zero. native complete loss is higher (`+18.5442`), driven by shape, while volume remains unresolved. one region has supported higher loss, labeled an unadjusted descriptive comparison. regional negative frequency and mass increase; native frequency slightly falls while mass and worst magnitude increase. these adverse findings remain beside the primary result.

player sensitivity uses 940 ordered final source-reference players: 935 current, four carried-only and one unseen, separately for both roles. prior-only training minutes are zero; held-out minutes are separately labeled. current-player scalar rms changes are `0.05404` offense / `0.05153` defense attempts/60; regional change-size rms is `0.006259` / `0.005999`. the common gauge and practical scalar band establish no calibrated uncertainty or recovery.

## integration, content and temporary checks

all four commands pass on the portable fixture with 43 copied dependencies and twenty states. malformed assignment/context/correction/hash/rank inputs stop explicitly without changing originals. saved-only reports pass with source/prepared/fit reads, fitting, composition, scoring and resampling denied, permitting only the assessment's bound archive. real reports are regenerated from the unchanged assessment. runtime/provenance/output paths can differ; scientific rows remain equal.

root and independent content reviewers inspect both real figures and reconcile claims against saved tables. the final prediction legend sits outside data; player figures distinguish both roles and evidence groups, and label the scalar 5% yardstick as practical. player csv regional headers identify their named regions. native interaction is reported as zero by construction with roundoff; individual supported-region diagnostics use a direction-neutral rule. the decision explicitly names locatable attempts, matched genuine-5v5/zero-event exposure and exposed seasons. no absolute mse, equivalence, causal isolation, improved recovery, rank or admission claim is made.

the final portable four-command receipt binds `a4f7e38`; report-only changes finish at `2fac80e`. final fixture and real denied-dependency reporting checks pass at that producer. `reviews/report-final-03-csv-verification.json` independently verifies all 67,680 named regional values, 1,008 comparison rows and 48 native-zero labels without changing numerical values. final report artifacts retain those scientific values; the last report change measures output bytes and writes the manifest after both markdown files. independent final review clears the producer diff, exact scientific-field equality, both figures and measured output size.

red → green → refactor → green is complete, followed by scoped deletion:

| owner | removed temporary material | retained external receipts under `reviews/temporary-checks/` |
|---|---|---|
| source | five scripts and one transient snapshot; six files / 869,070 bytes | `source/deletion-inventory.json`, `source/deletion-verification.json`, eight red/green/fact receipts and snapshot digests |
| numerical | eight controllers and 24 owned run roots; 1,158 files / 178,829,432 bytes | `numerical/deletion-inventory.json`, `numerical/deletion-receipt.json`, 32 red/green/final receipts |
| prediction/content | fourteen scripts, bytecode, preview and copied receipt; seventeen files / 227,167 bytes | `prediction/inventory-before-deletion.json`, `prediction/deletion-receipt.json` and three checked-fact receipts |
| independent claude review | 195 scratch files / 54,254,371 bytes, 26 directories, including fixture and saved-only rerenders | `independent-review/review.md`, `independent-review/scratch-inventory-before-deletion.json`, `independent-review/scratch-deletion-receipt.json` |

no temporary test/controller or test-only dependency remains. literal fixtures, independently checked facts, all four scientific commands, expensive outputs and receipts remain. `reviews/documentation-checks.json` records resolved local links and twelve exact report copies. the whole-branch `git -c core.whitespace=cr-at-eol diff --check b6295d0 HEAD` and the post-cleanup four-command entry point pass. csv exports retain standard carriage-return/line-feed endings; a final source-only eof cleanup is independently checked as ast-identical to the assessed producer. these are documentation/entry checks, without application tests or scientific reruns.

## measured costs and preservation

| command | wall seconds | peak resident bytes | output bytes before final manifest |
|---|---:|---:|---:|
| prepare | 265.16 | 1,230,782,464 | 730,197,889 |
| fit | 226.28 | 3,684,597,760 | 515,383,023 |
| assess, including probes | 371.75 | 4,739,072,000 | 523,140,790 |
| final saved-only report | 0.87 | 202,309,632 | 6,897,266 |

the baseline and final `reviews/preservation-before.json` / `preservation-after.json` verify all 224 protected files, 2,772,773,057 bytes, with exact hashes, sizes and nanosecond mtimes. old source/result/fit evidence, serving build and both publication databases remain intact. listener pid `70045`, its start time and serving command remain unchanged. all eleven original input blobs remain preserved in `b6295d0`. `reviews/primary-draft-preservation.json` records concurrent edits to five primary documents and additional primary-only drafts; these are left untouched for later integration. this work neither writes primary source nor rebuilds the site.

costs accepted by the specification remain: ten fresh component fits and an original-event/exposure pass; restricted quadratic temporal curves and forty-mode temporal shape; external-only expensive artifacts with manual rerun risk; conditional prediction intervals and point-only player sensitivity. no new dependency, runner, checkpoint engine, fit mirror, positivity rewrite or publication machinery is added. the implemented family remains available without scientific adoption. chance valuation, recovery, uncertainty and explicit publication remain separate requirements; [negative-rate limitations](../../issues/attribution-negative-rates.md) stay open. no unique next revision is identified.

## source integration and task cleanup

on 2026-10-22 the user assigned pr, merge and cleanup. [pr #47](https://github.com/NielsdaWheelz/hockey-stats/pull/47) merges as `3e8f9026ac176fb78e1a3686b1ae9d16748d9a0c` after `GitGuardian Security Checks` passes. its tree `3f9eb7a580de14b67a0a39c86cfadf4ca8200917` equals independently reviewed head `be2383da6492bf18f7e5a7670c03cdaaa3240edd` exactly. all scientific producer commits and the exact eleven-blob input snapshot remain ancestors; no squash, source regeneration, refitting, scoring or report rerender occurs during delivery.

integration preserves main's `7c63bfb` complete experimental-product direction. the brief, agents, full inventory, coordinated-program stub and 04/05/06/05i scope contracts retain its bytes exactly. living documents add completed 04o evidence without restoring a serial scientific-admission gate. the original specification body, numerical code, fixtures, decision, result, csv tables and figures remain unchanged. the original implementation record above is historical; the current experimental-product policy governs separately assigned future use.

primary fast-forwards cleanly. changed analytical/study imports and the four-command entry point pass in the primary environment. pinned node `24.21.0` typechecking passes on the byte-identical application tree. serving assets are neither rebuilt nor restarted. [independent integration review](/Volumes/Expansion/hockey-stats/runs/attribution-04o-20261021/reviews/delivery/integration-review.json) and [hosted review](/Volumes/Expansion/hockey-stats/runs/attribution-04o-20261021/reviews/delivery/hosted-independent-review.json) bind the reviewed tree, source preservation, checks and merge.

the registered task worktree, distinct environment, local/remote branch, 26 scratch files / 153,273 bytes, temporary pr body and empty owned claude scratch are removed. every removed receipt has a hash-identical retained external copy. `/Users/nnandal/Documents/code/hockey-stats-04o` remains a symlink to the primary checkout: the frozen preparation's hash-bound 04n result locator still uses that path. [reference audit](/Volumes/Expansion/hockey-stats/runs/attribution-04o-20261021/reviews/delivery/reference-audit.json) verifies 35 repository references and all four task-root references, including three historical fixture locators. no duplicate checkout/environment, new scientific copy or rewritten frozen reference is needed. the external specification snapshot stays unchanged.

independent final preservation verifies all 434 protected files, 4,609,577,545 bytes, retain exact hashes, sizes and nanosecond mtimes. this includes the prior 224 files, all new 04o outputs and receipts, source evidence, expensive states/probes, serving build and both publication databases. listener pid `70045`, its start time and command remain unchanged. [final preservation](/Volumes/Expansion/hockey-stats/runs/attribution-04o-20261021/reviews/delivery/final-preservation.json) and the [cleanup receipt](post-merge-cleanup.json) record these checks. only documentation and the delivery receipt change after the reviewed merge; no activation, new fit, model admission or automatic successor follows.
