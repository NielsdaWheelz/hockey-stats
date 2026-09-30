# chance fit cost

status: open; measured prerequisite repair for 03b.

problem: the fitter repeats coordinate quantization and frozen blocked posterior calculations inside every inner optimizer call. the repeated work does not change an e-step's sufficient statistics.

evidence: the deterministic eight-game fresh selection at `/Volumes/Expansion/hockey-stats/chance/03b-20260930/inputs/profile-training.json` has 751 eligible attempts. the profiled baseline fit took 47.81 seconds, with 146,718,720 bytes peak resident memory. `baseline-fit.pstats` attributes 33.62 seconds to `_stage_objective`, 22.565 seconds to 362,128 `posterior` calls and 13.754 seconds to 1,139,501 `cell_id` calls. profiled timings include profiler overhead and do not establish full-season capacity.

impact: expensive repeated work delays real scientific development without improving the estimator. premature full-window runs could waste substantial computation.

resolution: compute scalar indices once and aggregate frozen blocked sufficient mass by shared predictor context at the responsible numerical layer. preserve the likelihood, penalties, fixed grid, posterior update and convergence conditions. do not retain a season-sized event-by-cell posterior matrix. differential objective/gradient and full installed-fit checks must establish mathematical equivalence; rerun the same bounded workload and measure ordinary full-window capacity before deciding whether completed-em-boundary recovery is needed.
