# 04c decision

status: **complete** on 2026-10-16. `mean_recovery_failed,nomination:null,admission:not_admitted,handoff:null`.

the fixed graph candidate improves broad regional shape error over zero under both generators, but fails the prospective requirement to improve over native 04b in every comparison. game-pace radial recovery versus native 04b is inconclusive; lateral recovery fails. nested refits and real fitting are `not_run` with reason `mean_recovery_failed`. this scientific stop completes the assigned question.

the [protocol](protocol.json) was frozen before new responses at clean implementation `481a9e36138e0d143efe4009d2733c53a941a35b`. [the result](result.json) binds the original sources, diagnosis, preparation, all 800 paired datasets and figures. [verification](verification.md) records independent reviews and temporary-test deletion. the [specification](../../specs/04c-attribution-recovery.md) and earlier studies remain unchanged.

## diagnosis and mean recovery

all 400 saved 04b outer datasets reconcile. final broad regional shape error is bias dominated in both cases:

| original noise | squared bias | sampling variation |
|---|---:|---:|
| gaussian | 6.098232 | 0.000363 |
| game pace | 5.134426 | 0.073981 |

the diagnosis preserves volume, shape and their signed cross term. it supports testing the proposed mechanism; it does not prove that pooling repairs it.

all 400 new datasets per case complete, with five-year candidate and fresh native-04b chains on identical responses. positive gain below means lower candidate error. every interval uses the declared 10,000 paired resamples; units are squared attempts/60 team minutes.

| noise | offense contrast | baseline | mean gain | percentile 95% interval | decision |
|---|---|---|---:|---|---|
| gaussian | radial `3−4` | zero shape | 0.416581 | [0.387692, 0.445835] | supported |
| gaussian | radial `3−4` | native 04b | 0.325627 | [0.298734, 0.352786] | supported |
| gaussian | lateral `10−11` | zero shape | 0.118078 | [0.107675, 0.128754] | supported |
| gaussian | lateral `10−11` | native 04b | 0.091203 | [0.081700, 0.101335] | supported |
| game pace | radial `3−4` | zero shape | 0.989914 | [0.911424, 1.070042] | supported |
| game pace | radial `3−4` | native 04b | -0.038974 | [-0.104998, 0.027490] | inconclusive |
| game pace | lateral `10−11` | zero shape | 0.250547 | [0.225340, 0.275931] | supported |
| game pace | lateral `10−11` | native 04b | -0.018741 | [-0.037223, -0.000917] | failed |

all eight had to support progression. six supported, one was inconclusive and one failed. no extra datasets, alternative cutoff, widened scale range or replacement model followed.

substantial bias remains despite improvement over zero. normalized regional error divides by actual truth energy: zero prediction equals one, perfect recovery equals zero. attenuation is the outer mean's projection onto the actual regional truth pattern, divided by truth energy.

| noise | offense contrast | normalized regional shape error | mean-pattern attenuation |
|---|---|---:|---:|
| gaussian | radial `3−4` | 0.932677 | 0.034835 |
| gaussian | lateral `10−11` | 0.933728 | 0.035060 |
| game pace | radial `3−4` | 0.840022 | 0.088433 |
| game pace | lateral `10−11` | 0.859379 | 0.083693 |

secondary evidence remains adverse: rough regional shape error is 1.178614 and 2.434202 times zero-prediction error under gaussian and game-pace noise. six of eight final candidate complete-map errors exceed their zero baselines. all 32 broad/local/rough pattern summaries and 90 entry/return or matched-volume summaries remain in the result. these diagnostics describe limitations; they do not supply new vetoes or substitute thresholds.

## scope and costs

the candidate has 40 geometry-selected modes with a 40-foot nominal wavelength for relative shape. that is a representation rule, not demonstrated spatial accuracy. actual truth remains the assessment target; geometric projection is only an oracle representability diagnostic. native shares are estimated but conditioned on. volume and unrestricted native context retain their original contracts.

no empirical candidate interval calibration or new real-player evidence was reached. the four primary coverage cells, secondary refit diagnostics and conditional real chain remain untested. exact-null individual contrasts abstain; that does not identify their effects as zero. complete additive rates remain unconstrained. no result establishes supported ability, causal isolation, defense-wide recovery, chance valuation or publication readiness. the [recovery](../../issues/attribution-spatial-recovery.md), [uncertainty](../../issues/attribution-working-uncertainty.md) and [complete-rate](../../issues/attribution-negative-rates.md) issues remain open. no next campaign is assigned.

| command | wall seconds | parent process seconds | worker process seconds | recorded peak process bytes |
|---|---:|---:|---:|---:|
| diagnosis | 122.33 | 30.02 | — | 349,863,936 |
| preparation | 1.07 | 0.85 | — | 488,325,120 |
| paired means | 557.94 | 10.76 | 1,917.48 | 2,153,742,336 |
| assessment | 122.32 | 17.87 | — | 896,188,416 |

the study uses at most four workers with one numerical thread each. memory values are recorded per-process peaks, not simultaneous aggregate memory. all expensive outputs and review receipts remain under `/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/`; no local fit mirror or new dependency was added.

figures: [saved-evidence diagnosis](diagnosis.png), [eight mean comparisons and the uncertainty stop](recovery.png), [actual, projected and fitted patterns](representation-limits.png).
