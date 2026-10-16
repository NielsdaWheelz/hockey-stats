# attribution spatial signal recovery

status: open; post-04b descriptive review on 2026-10-16. owner: attribution estimator research. [04c](../specs/04c-attribution-recovery.md) specifies diagnosis and one conditional broad-shape pilot; [the plan](../plan.md) owns assignment. no 04c execution/evidence exists yet. this finding does not revise the frozen [04b verdict](../research/attribution-04b/decision.md).

problem: 04b's four native map-error improvements compare against 04a. they do not establish useful recovery beyond predicting no difference between the simulated players. shrinking a noisy estimate toward zero can improve that comparison while erasing signal.

evidence: [saved simulation summary](/Volumes/Expansion/hockey-stats/runs/attribution-04b-20261015/simulation/simulation.json), sha256 `6075a4de7ca5449a2e66e2b7b6bd7caca7d81e6c4dedc29a12d328f627250863`. filter `error_metrics` to `year=5`, `contrast` in `broad,local`; each row aggregates 200 independent outer replicates. divide `means.revision` by `means.truth_energy`, also saved as `means.revision_normalized`. the [metric implementation](../../analysis/research/attribution_revision_recovery.py) computes squared native contrast-map error; the zero prediction's error is exactly the truth energy.

| noise | broad normalized error | local normalized error |
|---|---:|---:|
| gaussian | 1.016515 | 1.146075 |
| game pace | 1.041137 | 2.217348 |

zero-difference error equals 1. these are descriptive means, not a newly frozen superiority test or evidence that all real player estimates are useless. the injected patterns have zero volume, but estimated volume error contributes to these complete-map errors; isolate it before attributing the discrepancy to shape shrinkage. the saved `descriptive-recovery.npz` bias arrays and outer artifacts permit mean-pattern and variation checks without refitting. truth energy was independently checked against `synthetic-design.npz` and its player-order manifest.

impact: improvement over the predecessor cannot alone support useful player maps. all 655 native shape directions share a scale process without geometric smoothing; inappropriate shrinkage is a plausible mechanism, not a demonstrated cause. the point/refit scale discrepancy in the [uncertainty issue](attribution-working-uncertainty.md) requires joint investigation. simply enlarging intervals, displaying wider regions or acquiring more games does not establish recovery.

resolution: prospectively compare useful signal recovery against zero, volume-only and established controls on identical populations; separate volume error, spatial bias and sampling variation. assess broad/local and deliberately poorly represented patterns with a representation chosen independently of those truths. obtain evidence supporting the declared resolution or explicitly narrow the claim. this issue owns mean/signal recovery; the uncertainty issue owns interval/claim behavior, and [complete-rate adequacy](attribution-negative-rates.md) remains separate. no automatic full refit campaign or new admission follows.
