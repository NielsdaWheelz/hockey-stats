# 03j decision

**`inconclusive`; `no_supported_intervention`.** the frozen rule does not prioritize conversion scale. nominate no next fit from this benchmark: failure to establish benefit neither identifies a structural cause nor selects the queued avoidance experiment. model admission is `not_assessed`; historical 03b rejection and 03e/03h withholding stand. [complete tables](/Users/nnandal/Documents/code/hockey-stats-03j-runs/benchmark/benchmark.json) · [figure](figures/conversion-scale.png) · [protocol](protocol.md) · [verification](verification.md).

march 1–april 17 assessment contains all 25,027 eligible unblocked attempts, 1,472 goals and 366 games. unchanged/adjusted log loss is `0.1920362282 → 0.1921775682`: paired difference **`+0.0001413400` nats per attempt**, with positive meaning worse. all three pointwise 95% adjustment-refit intervals cross zero:

| resampling | paired log-loss interval, nats/attempt |
|---|---|
| whole game | `[−0.0000780699, +0.0006040719]` |
| seven day | `[−0.0001964435, +0.0006242884]` |
| fourteen day | `[−0.0002820543, +0.0005816425]` |

brier difference is `+0.0000619821`; its three intervals also cross zero. predicted goals fall `1,488.478 → 1,398.220` against 1,472 observed; pooled predicted-minus-observed residual moves `+0.065841 → −0.294801` percentage points. nominal deterioration is not established harm, equivalence or evidence for a different mechanism.

the fitted equation is `adjusted logit = −0.16287686 + 0.96033249 × saved logit`. `a` is the joint intercept, not calibration-in-the-large; the slope slightly compresses logit differences. aggregate mass falls, although very small probabilities can rise. january–february apparent loss improves `0.1865840707 → 0.1864185303` on 23,987 attempts/1,332 goals; that in-sample improvement did not establish later benefit.

descriptive heterogeneity remains: no-recent residual worsens `−0.248133 → −0.577792` pp while recent improves `+0.781187 → +0.349953` pp. wrist/slap/backhand underprediction worsens; tip/other overprediction improves. unchanged own bin `[0.15,0.20)` has 1,213 attempts at `+3.078575` pp; adjusted own membership has 1,063 at `+0.437428` pp. on the identical 1,213-row cohort, adjustment leaves `+1.696099` pp. bin migration is not a paired calibration effect; sparse tails, descriptive groups and these bins supply no new admission test.

both windows were research-exposed, and adjustment received newer labels than the saved model. january–february versus march–april environments, drift, shrinkage, missing mechanisms and measurement error remain competing explanations. intervals include adjustment fitting and selected-window sampling conditional on the saved model; they omit base fitting, selection, origin assumptions and cross-window dependence. only five/four fortnightly units limit that sensitivity. origin, all-attempt, spatial and player obligations remain open.

all 6,000 draws were defined and converged, with at most nine iterations and maximum final scaled-gradient norm `2.735e-9`. nominal fitting took seven iterations with scaled-gradient norm `1.301e-10` and positive hessian. the single-pass command completed in 145.12 seconds at 346,292,224 bytes peak rss, within the frozen 900-second/2-gib limits. independent arithmetic and rendered-figure reviews passed; no follow-on fit or handoff occurred.
