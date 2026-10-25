# v1-05 final-year numerical resolution

problem: final real `20252026` baseline-to-tighter probability changes exceed the fixed `1e-5` bound in `u/q`, despite completed native solves and complete selector coverage. the command correctly exits `1`; the independent report records `incomplete_failed_resolution`.

| head | maximum branch/terminal probability change | verdict |
|---|---:|---|
| `u` | `1.2808432675537329e-5` | failed |
| `q` | `1.4692029087437497e-5` | failed |
| `r` | `7.778643741906954e-6` | passed |
| `g` | `3.055071906565843e-8` | passed |

impact: all twenty real baseline heads are complete and the first sixteen have annual acceptance, but final-year acceptance and the full v1-05 handoff remain blocked. no tighter coefficients were promoted. scientific admission is not asserted; cleanup awaits final verification.

evidence: [operator failure](../research/execution-v1-05/real-final-year-resolution-failure.json), [independent diagnosis](../research/execution-v1-05/real-final-year-independent-failure.json) and [result](../research/execution-v1-05/real-final-year-result.json) bind manifest `f7ed612309a16bb0385694e27f8136f1eac8eab34c9eae2c3939605f43268e69` and baseline descriptor `06d2cc53b998afea4996f5886e408ae576f25b0b7bcdc2887c5ce314491cb5a8`. all 48 requirements are covered: 44 actual and four fixture; missing coverage is not the cause. the strict reader validates all eighteen members and four probe variants. baseline coefficients still match the frozen descriptor.

the approved native optimizer tolerances are baseline `ftol=1e-14`, continuation `1e-15`; they permit relative-objective termination without reaching raw `gtol`. both baseline and tighter `u/q` solves terminated on `ftol`, before iteration/evaluation caps. bounded independent review checked saved coefficient deltas, actor centering, prior-only means and unchanged design/origin/prior contracts, and inspected comparison inputs; it found no accounting defect. it did not independently replay the full probability comparison. the worst context is not saved and remains unknown without rebuilding the design. this is a failure of the declared probability-stability criterion, not evidence that a cap was exhausted or a particular arithmetic defect exists.

reproduce from retained outputs: strict-read `/Volumes/Expansion/hockey-stats/runs/execution-v1-05-20261025-01/20252026` with `read_execution_state(..., 'real')`, then read each tagged variant with `read_execution_probe`. compare the recorded maximum changes with `1e-5`; `u/q` fail. no raw-event replay or refit is needed to inspect the saved verdict.

next bounded work: a diagnostic preview is being prepared on the same final-year objective and accepted 2024 priors, starting from the saved `1e-15` `u/q` coefficients and requesting native `ftol=1e-16`, with the full frozen selector. roughly ninety minutes of preparation and uncertain solve time may be required. `1e-16` is near float64 relative precision (`2.220446049250313e-16`), so feasibility and numerical evidence precede any proposal. no stopping-policy amendment or new annual retry is approved; full handoff remains incomplete, scientific admission is not asserted, and cleanup awaits final verification. a successful preview would not by itself establish a qualified replacement chain.

resolved when: all four final probes pass the unchanged probability bound under an approved policy, with a compatible declared recipe and predecessor chain; any adopted stopping change receives explicit approval and its required fresh qualification. retain failed outputs and historical verdicts, then close [real acceptance](execution-v1-05-real-acceptance.md) separately after consolidated handoff checks.
