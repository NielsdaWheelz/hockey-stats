# 04j verification

04j completes its assigned information diagnosis: `execution_status:complete,numerical_status:verified,study_status:diagnosed,nomination:null,admission:not_admitted,handoff:null`. [decision](decision.md) · [result](result.json) · [frozen protocol](protocol.json) · [execution checks](execution-verification.md). the next benchmark is a structured proposal, not an assigned campaign.

## implementation and source boundary

clean producer `f7e36a9321aca75d92f6bdb01784d914f9312b8f` ran preparation, analysis and reporting with the existing locked environment: python 3.14.8, numpy 2.5.3, scipy 1.18.1, lock sha256 `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`. branch `codex/04j-attribution-deployment`; worktree `/Users/nnandal/Documents/code/hockey-stats-04j`. the original checkout and its pending documentation remain untouched.

native subagents implemented the selected readers/shared mathematics, study commands and fixture/reporting boundary. independent cross-review and root review checked each boundary. the shared implementation owns physical information and scalar/batched estimability; both historical consumers now use the same near/lateral operators. their original arrays match exactly, and 113 historical scalar cases differ by at most `8.9e-16`.

all ten original designs reconcile. exact native-reference equality holds across real and synthetic seasons. only 68 selected archive members were decoded; no responses, truths, evaluation arrays or fitted controls were decoded. five real statistic digests match independently read originals exactly; reconstructed synthetic information differs from independent direct rows by at most `4.76e-11`. integer overlap reconstruction differs by at most `4.14e-9` seconds, below the unchanged `1e-6` limit. masks, zero-event exposure and annual coverage remain bound to their sources.

## bounded research execution

external root: `/Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/`.

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats/analysis/.venv/bin/python analysis/research/attribution_deployment.py prepare --real-result docs/research/attribution-04b/result.json --synthetic-result docs/research/attribution-04h/result.json --selection-result docs/research/attribution-04i/result.json --purpose research --output /Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/prepared
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats/analysis/.venv/bin/python analysis/research/attribution_deployment.py analyze --prepared /Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/prepared/prepared.json --output /Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/prepared/analysis
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats/analysis/.venv/bin/python analysis/research/attribution_deployment.py report --analysis /Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/prepared/analysis/analysis.json --output /Volumes/Expansion/hockey-stats/runs/attribution-04j-20261017/prepared/report
```

these record the executed commands, not overwrite instructions: every output path is exclusive. ordinary reruns need new output directories. no runner, checkpoint engine, source-array mirror, new dependency, fit, response generation or publication was introduced.

| accounting | verified total |
|---|---:|
| annual spectra / final-history spectra | 10 / 2 |
| annual player/reference contrasts, real / synthetic | 9,456 / 320 |
| historical player/reference contrasts, real / synthetic | 1,880 / 64 |
| case labels / all labeled rows / distinct calculations | 20 / 11,740 / 11,736 |
| absent research cases | 0 |
| available / nonestimable rows | 11,712 / 28 |
| saved selector-closure rows | 46 |
| independent reduced-gauge svd decompositions / probes | 2 / 12 |
| equation/gauge/solve checks / persistence comparisons | 36 / 1,948 |

all three cutoff masks agree. real annual ranks are `2004,1900,1846,1818,1878`; historical rank is `2952`, each with measured nullity two. synthetic annual rank is 60 and history rank 64, each with nullity four. largest eigen, role-gauge and available-solve residuals are `4.58e-15`, `1.94e-14` and `3.61e-11`, respectively. svd probes use the same absolute cutoffs; all statuses, null projections and available q values agree at the specified tolerances. every available final annual contrast remains available under constant physical history with nonincreasing q.

all 940 real final players are conditionally estimable in both roles. synthetic players 26/31 and their difference remain nonestimable; their relative pair mean is available. real final within-20-ft, in-front-of-goal median sd is `1.56539` annually and `0.509134` under constant physical history, versus `1.16241` and `0.519054` in the synthetic deployment. the 264 real players below 300 included minutes have the largest group medians, `3.25549` and `1.48637`. these are sampling sds under fixed working assumptions, not actual effects or calibrated player uncertainty.

equal offense/attempts-allowed precision follows paired deployment and matched role/context symmetry, with the same reference and working noise. it does not imply equal player effects or equal empirical noise. constant history changes the temporal assumption; lower sd cannot establish that players remained unchanged. the 42-versus-six context difference prevents a pure teammate-mixing interpretation.

## independent acceptance and temporary verification

- [source/accounting](reviews/root-source-accounting.json), [live selected readers](reviews/data-math-live-sources.json), [shared historical parity](reviews/root-shared-parity.json), [shared red/green/refactor](reviews/data-math-integration.json).
- [study integration and negative inputs](reviews/study-cli-integration.json), [independent cli mathematics](reviews/data-math-cli-review.json), [root implementation review](reviews/root-integration-review.json).
- [fixture/content/source review](reviews/content-fixture-source-review.json): 216 direct full-nuisance gls expectations, 40 independently computed summary groups, wrong-source/axis/hash/input/pairing rejection, explicit absent cases and detached saved-only reporting. the compact fixture has eight spectra, 144 annual and 48 historical individual contrasts, plus declared cases; both design labels are synthetic.
- [research numerical review](reviews/research-numerical-review.json), [research content review](reviews/research-content-review.json), [root units/result review](reviews/root-research-result.json), [independent saved closure selection](reviews/root-closure-selection.json).

all 40 report groups, their denominators, unavailable reasons, linear quantiles and matched ratios reconcile independently. all 11,740 exported contrasts and 11,712 indexed finite array rows reconcile. covariance contractions, physical units and all 46 exact saved means/intervals match. all eight actual scatter series match saved values, and an independent saved-only rerender is byte-identical; root and content reviewers inspected the rendered four-panel figure.

temporary tests were written before implementation, failed at the missing target boundary, passed after implementation, then passed after refactoring. source failures and independent fixture algebra exposed and corrected real implementation errors; no source fallback or adjusted numerical cutoff was added. temporary tests/controllers and bytecode were deleted after independent review. no permanent suite or test-only dependency remains. [cleanup receipt](reviews/cleanup.json).

## costs and tradeoffs

- prepare: 0.847 wall seconds, 0.793 process seconds, peak memory 573,423,616 bytes; output-tree bytes before its manifest 533,427.
- analyze: 9.648 wall seconds, 9.574 process seconds, peak memory 2,602,303,488 bytes; output-tree bytes before its manifest 5,676,732.
- report: 0.865 wall seconds, 0.813 process seconds, peak memory 257,458,176 bytes; output-tree bytes before its manifest 10,466,524.

preparation binds 255,462,700 unique selected-source bytes, including full archive hashes. analysis retains numerical arrays externally; repository reports include the complete 9.6 mb contrast csv for direct inspection. preparation avoids a redundant matrix copy by reopening and verifying frozen originals during analysis. explicit dense identity selections use memory to keep the physical alignment contract inspectable; indexed accumulation avoids cubic embedding. aggregate floating exposure checks use the existing relative equality, while overlap rounding and integer totals retain their strict contracts.

all-player native-shape information preserves awkward cases and avoids assuming eleven-mode truth. its cost is matrix/table work without a smooth-model performance claim. unchanged contexts and reference noise leave omitted context and game dependence unresolved. false physical persistence can produce misleading apparent precision. the proposed broad transfers are counting-scale scenarios selected independently of observed sds, not inferred real magnitudes or a new accuracy gate.

source captures, expensive fits, prior publications and historical scientific verdicts remain intact. useful recovery, complete rates, empirical player uncertainty and supported chance valuation remain separate requirements. 04j resolves its assigned information question; the existing recovery issue remains open.

csv reports retain their standard crlf record endings. the final git whitespace check enables `cr-at-eol` to preserve exact frozen bytes; it passes with the other whitespace checks enabled. production code and fixtures remain byte-identical to the clean research producer, and the worktree is clean.

## post-merge integration and cleanup

[pr #33](https://github.com/NielsdaWheelz/hockey-stats/pull/33) merged in `ea23777` after its security check passed. the merge tree equals reviewed head `942d881`; the assignment snapshot and clean research producer remain in ancestry. primary-checkout imports and the saved preparation preserve all three parent-result identities through the retained `hockey-stats-04j` symlink. this checked saved evidence and source lookup, with no new spectra, fits, assessments or responses.

the eight already-incorporated primary drafts were independently verified, temporarily stashed for the fast-forward and reconciled with the completed documents. the owned redundant stash, task local/remote branches, registered worktree and temporary pr body are removed. no second environment was created. source evidence, expensive fits, all frozen research outputs, publications, the primary environment, archived reference, desktop docker and older aliases remain intact. [post-merge cleanup receipt](post-merge-cleanup.json).
