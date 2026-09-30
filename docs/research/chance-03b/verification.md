# chance-03b software verification

verified 2026-09-30. these are software and bounded resource facts, not scientific acceptance. the [protocol](protocol.md) and scientific decision own that judgment.

## changes and independent checks

`75e7057` moves the existing executing implementation identity into the common fit/evaluate/score envelope. installed fixture commands first demonstrated its absence, then passed after repair. an independently loaded historical model retained its exact bytes, digest, evaluation metrics and scored stream. model fitting identity and later executing identity remain distinct. the resolved attribution issue was deleted.

`36d186c` repairs a measured fitter hot path. coordinates and scalar actor/score indices are prepared once. conversion and benchmark objectives use vector arithmetic; the block objective uses frozen success/failure sufficient statistics per score/shooter context. e-step event posteriors remain bounded to 64 rows. no likelihood, feature, grid, penalty, initialization or convergence contract changed; the old repeated training paths were removed.

independent differential checks compared original and revised objectives/gradients at perturbed parameters, including finite differences, posterior refresh, expected-count conservation and observed likelihood. full fresh eight-game fits retained both starts' 75/81 iterations. final objective differences were below `1.2e-10`; factual probability and reference-value differences were below `5e-10`, and maximum blocked cell-weight difference was `1.18e-8`. saved-model prediction arithmetic stayed identical. floating accumulation order changes can affect numerical trajectories or near-tied start selection; byte equality is not the fitter contract.

`720361a` adds the saved-evidence comparison script and pinned matplotlib `3.11.2`. temporary installed subprocess checks first failed on the missing script. green/refactor checks covered:

- hand-pooled log loss, brier score and calibration from games with one versus nine attempts; averaging game means gives a different, incorrect answer.
- independently computed 2,000-draw `PCG64` percentile intervals, repeatability and exact undefined-draw counts; one undefined draw makes the interval null.
- fixture, dirty/unidentified revision, consumed-input, coverage, prediction-definition and population mismatch rejection.
- linked score hashes, lockstep keys/statuses, null event ids, reordered streams, origin-count manifests and mass/value conservation.
- absent scored populations remain null with reasons; existing output paths fail; injected figure failure leaves no final `comparison.json`.
- a 100,000-attempt exact-bin-boundary case using production arithmetic; rounding in saved sums does not falsely reject a valid fixed bin.

an independent sol adversary reran the principal checks and inspected rendered figures. figures show factual calibration with counts, absolute spatial mass and signed differences on common scales, and event-value change summaries in expected goals. empty spatial evidence is visibly unavailable. event summaries use signed mean, mean absolute, root mean square and maximum absolute changes; coarse histograms were removed because they concealed small changes. no threshold selection or automatic verdict exists.

temporary test code, copied baseline code, caches and the temporary formatter environment were deleted after verification. no test-only dependency was added. `uv sync --locked` passed; application type checking also passed under pinned node `24.21.0`.

## measured bounded work

external root: `/Volumes/Expansion/hockey-stats/chance/03b-20260930/`. selections come from fresh official inventories, not fabricated ids. all measurements below are local observations on the user's machine; none establishes season capacity by extrapolation.

| workload | eligible attempts | wall seconds | peak resident bytes | qualification |
|---|---:|---:|---:|---|
| first eight training games, preparation | 751 | 0.459 | 82,264,064 | ordinary execution |
| first eight training games, baseline fit | 751 | 47.81 | 146,718,720 | profiled; profiler overhead included |
| first eight training games, optimized fit | 751 | 5.98 | 146,587,648 | ordinary execution; not a direct speed ratio with the profiled baseline |
| eight later games, baseline assessment | 714 | 1.04 | 137,789,440 | exploratory model, not seasonal acceptance |
| first eight training games, baseline scoring | 751 | 0.86 | 156,336,128 | 13.5 mib output; full origins retained |
| first 128 training games, optimized fit | 11,581 | 51.36 | 278,102,016 | clean analysis revision `720361a`; both starts converged |
| eight games after that training cutoff, comparison | 812 | 1.17 | 148,324,352 | clean saved-artifact command path; no seasonal claim |

the 128-game selection has 15,663 recognized attempts: 11,581 eligible, 3,921 outside scope and 161 unavailable. its 3,322 eligible blocks share 1,841 score/shooter contexts across 660 shooters. grouped statistics grow with observed contexts; posterior storage does not grow as events times cells. preparation measurements of 3.53 and 9.24 seconds illustrate filesystem/cache variability.

the clean capacity model is at `fits/capacity-anchor/model.json`, sha-256 `9936fd052869beef28b0ff0bf78d3f5beed2fbe05e2a8b38eb92c6669259f3e6`, 2,549,602 bytes. costs, selections, input identities, profile and logs remain under `inputs/`; `review/capacity/comparison.json` records its consumed assessment/model/protocol digests. these bounded measurements justified proceeding without checkpoint machinery. full-window costs and scientific results remain to be measured separately.
