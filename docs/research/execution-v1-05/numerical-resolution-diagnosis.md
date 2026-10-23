# numerical resolution diagnosis

this records the original prescribed stopping tolerances and rejected conditioning diagnostics. the solver computes the exact objective and analytic gradient, but its original relative function-change termination could precede the required `1e-5` branch-probability stability. this is separate from declared optimizer or em completion.

the checked fixture chain `chain-04` used the then-current `fa794eee0098b53900fce6c5b7756019a9b196c466a5e4366ef858a6297cbf2d` source recipe, with shared missingness conditions repaired. all twenty heads completed. all final-year selector requirements were covered. its four mandatory tightened probes still failed:

| head | original raw maximum gradient | tightened raw maximum gradient | raw objective change | maximum probability change |
|---|---:|---:|---:|---:|
| `u` | `.0014993` | `.0004684` | `-4.005e-7` | `4.3213e-5` |
| `q` | `.0019360` | `.0016341` | `-1.227e-6` | `6.9102e-5` |
| `r` | `.0008786` | `.0001977` | `-2.246e-7` | `3.9928e-5` |
| `g` | `.0006753` | `.0001900` | `-2.237e-7` | `4.3020e-5` |

all original solver calls used the specified options. inner solves commonly ended with `RELATIVE REDUCTION OF F`, rather than satisfying the raw gradient tolerance. raw summed losses of roughly `200..568` make `ftol=1e-10` permit relative step reductions of order `2e-8..6e-8`; point probabilities can still change materially at objective differences this small. strict em responsibility and observed-objective stopping does not repair an inner optimizer's early relative-loss termination.

one bounded diagonal-conditioning diagnostic changed only private solver coordinates. the diagonal was the exact penalty diagonal plus the zero-logit complete-data fisher diagonal, including observed setter labels and the current mean coupling. raw likelihood, penalties, starts, options and reporting remained unchanged. independent finite differences matched that diagonal to `1.49e-10`, and the transformed gradient to `2.49e-10`.

diagonal conditioning reduced iteration counts substantially but did not close resolution: `u=4.944e-5,q=1.763e-5,r=2.061e-5,g=1.760e-5`. receipts: `/tmp/execution_v1_05_preconditioned_results.json` and `/tmp/execution_v1_05_preconditioned_probe.log`. it was not adopted in production.

the native smoothing penalty remains correlated after diagonal scaling. measured exact 348-orbit prior condition numbers were `123.75` for the base map and `31.86` for type maps. root therefore approved one final bounded diagnostic using six exact map-block cholesky transformations, with the same fixed diagonal for other coordinates. independent inverse-coordinate error was `1.11e-16`; transformed gradient errors were `4.59e-9` for `u` and `4.31e-9` for `g`; raw-objective agreement was within `7.11e-15`.

the first block diagnostic attempt stopped BEFORE fitting because a source recipe update correctly invalidated the old predecessor under the strict reader. root explicitly rejected bypassing that reader or interpreting old family bytes as a compatible current family.

the fresh final-source `chain-05` uses recipe `eba7057ff0314232b591aecc1af2b211ffaec269fa79638f6d3236f4f5e82304`. all twenty heads completed; the four mandatory continuation probability differences remain exactly those displayed for chain-04. current strict state/probe readers and selector coverage passed. only after this new family existed did the approved block diagnostic run through that same strict reader.

the sole block diagnostic FAILED. `u/q/r` completed in `64/68/62` iterations, with raw objective improvements under continuation of `1.373e-7/8.386e-8/2.981e-8`. `g` returned unavailable with `no_completed_start`: neither requested start completed. the temporary harness asserted on this result before writing full failed-start diagnostics or computing final probability comparisons. that is a receipt gap; the precise `g` termination is not established by the retained log, and no missing probability comparison is represented as passed. `/tmp/execution_v1_05_block_probe.log` retains the actual observed failure and the completed binary-head diagnostics.

the conditioning search stopped. neither diagonal nor block whitening was adopted. no threshold was relaxed and no tighter coefficients were promoted. this investigation alone did not establish the numerical handoff.

production numerical code stayed unchanged during those diagnostics. subsequently one prospective native-solver preview used baseline `ftol=1e-14` and continuation `1e-15`, preserving all other rules. [the preview](stopping-preview.json) passed all four unchanged margins; [independent review](stopping-amendment-review.md) confirmed its scope and old-predecessor limitation. the user approved this exact stopping amendment on 2026-10-22. [verification](verification.md) owns the fresh full-chain result; this historical diagnosis remains adverse evidence, not the current acceptance verdict.
