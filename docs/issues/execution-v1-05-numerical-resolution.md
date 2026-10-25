# v1-05 final-year numerical resolution

problem: the historical `59509c18` chain's final real `20252026` baseline-to-tighter probability changes exceed the fixed `1e-5` bound in `u/q`, despite completed native solves and complete selector coverage. the command correctly exits `1`; the independent report records `incomplete_failed_resolution`.

| head | maximum branch/terminal probability change | verdict |
|---|---:|---|
| `u` | `1.2808432675537329e-5` | failed |
| `q` | `1.4692029087437497e-5` | failed |
| `r` | `7.778643741906954e-6` | passed |
| `g` | `3.055071906565843e-8` | passed |

impact: all twenty real baseline heads are complete and the first sixteen have annual acceptance, but final-year acceptance and the full v1-05 handoff remain blocked. no tighter coefficients were promoted. scientific admission is not asserted; cleanup awaits final verification.

evidence: [operator failure](../research/execution-v1-05/real-final-year-resolution-failure.json), [independent diagnosis](../research/execution-v1-05/real-final-year-independent-failure.json) and [result](../research/execution-v1-05/real-final-year-result.json) bind manifest `f7ed612309a16bb0385694e27f8136f1eac8eab34c9eae2c3939605f43268e69` and baseline descriptor `06d2cc53b998afea4996f5886e408ae576f25b0b7bcdc2887c5ce314491cb5a8`. all 48 requirements are covered: 44 actual and four fixture; missing coverage is not the cause. the strict reader validates all eighteen members and four probe variants. baseline coefficients still match the frozen descriptor.

the failed chain used the then-approved native optimizer tolerances, baseline `ftol=1e-14`, continuation `1e-15`; they permit relative-objective termination without reaching raw `gtol`. both baseline and tighter `u/q` solves terminated on `ftol`, before iteration/evaluation caps. bounded independent review checked saved coefficient deltas, actor centering, prior-only means and unchanged design/origin/prior contracts, and inspected comparison inputs; it found no accounting defect. it did not independently replay the full probability comparison. the worst context is not identified by the retained failure or preview reports. this is a failure of the declared probability-stability criterion, not evidence that a cap was exhausted or a particular arithmetic defect exists.

reproduce with historical producer `e2f98d5` from retained outputs: strict-read `/Volumes/Expansion/hockey-stats/runs/execution-v1-05-20261025-01/20252026` with `read_execution_state(..., 'real')`, then read each tagged variant with `read_execution_probe`. compare the recorded maximum changes with `1e-5`; `u/q` fail. no raw-event replay or refit is needed to inspect the saved verdict.

completed diagnostic: the [preview](../research/execution-v1-05/real-stopping-preview.json) rebuilds the same final-year design with old accepted 2024 priors and the full frozen selector, exactly replays the original failed comparisons, then continues saved `1e-15` `u/q` coefficients once at native `ftol=1e-16`. incremental changes `3.889186265260136e-7` / `2.2608070832097482e-6` meet `1e-5`; both still terminate on `ftol`, not raw `gtol`. [independent review](../research/execution-v1-05/real-stopping-preview-review.md) checked arrays, metrics and 97/107 prior-only formulas; it did not independently rerun the full probabilities. all 99 protected paths remain unchanged. this old-prior evidence neither repairs the saved failure nor qualifies a replacement chain. the user [approved uniform baseline `ftol=1e-15` / continuation `1e-16` and a full rerun](../research/execution-v1-05/real-stopping-amendment-2026-10-25.md) on 2026-10-25. implementation and independent review precede fresh five-year fixture then real chains under a new recipe, with no old-recipe predecessor or preview promotion. it retains the `1e-5` bound; numerical floor/cap and runtime risks remain. full handoff is incomplete, scientific admission is not asserted, and cleanup awaits final verification.

resolved when: all four final probes pass the unchanged probability bound under an approved policy, with a compatible declared recipe and predecessor chain; any adopted stopping change receives explicit approval and its required fresh qualification. retain failed outputs and historical verdicts, then close [real acceptance](execution-v1-05-real-acceptance.md) separately after consolidated handoff checks.

current replacement status: the approved stricter `14267557` recipe passes all four probes in a fresh five-year fixture chain, with independent review. this fixture result does not resolve the failed real comparison; all five newly propagated real years and four final real probes remain required.
