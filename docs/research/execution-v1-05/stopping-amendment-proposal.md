# proposed stopping amendment — review only

status: the user approved this exact amendment on 2026-10-22 after the preview and independent read-only mathematics review. the following proposal is retained as the pre-adoption record. the preview used the old predecessor; only a fresh full chain can qualify the amended recipe.

subsequent verification: the new full fixture chain completed twenty heads and passed all four probes; [verification](verification.md) owns its identities and limits. the numerical campaign controllers were deleted after this green boundary; [cleanup](numerical-cleanup.json) retains exact paths and absence checks. the preview and failed chains remain historical evidence.

proposal: change the baseline native optimizer's `ftol` from `1e-10` to `1e-14`; the required tenfold-tighter continuation consequently uses `1e-15`. retain `chance.solve_logistic`, the original summed penalized objective and gradients, all coefficient coordinates, `maxiter=2000`, baseline `gtol=1e-6`, continuation `gtol=1e-7`, both starts, every em rule and the `1e-5` probability margin.

this is tighter stopping, with additional computation. it adds no conditioning, algorithm, restart, population change or new recipe family. the production source, recipe and specifications have NOT changed. user approval is required before changing that fixed specification and computing a new annual chain.

why: the original relative function-change threshold admitted completed endpoints whose point probabilities moved by `4.0e-5..6.9e-5` in the mandatory continuation. the independently checked likelihoods and gradients were correct. diagonal and block conditioning did not resolve the delivery boundary and were not adopted. a single, prospective stopping preview selected the same `1e-14/1e-15` values for every head before fitting, near the strict relative precision available in float64; there was no per-head search.

the preview bound the final source recipe `eba7057ff0314232b591aecc1af2b211ffaec269fa79638f6d3236f4f5e82304`, requested-year design, coaching source and exact 20242025 predecessor ledger through the current strict readers. it used the same frozen final-year selector: 256 keyed actual attempts, all 40 requirements covered, the existing attributed synthetic witness, and all prescribed native-cell/type/actual/neutral probes. only the `ftol` keyword was changed in a temporary wrapper around the native solver. all other solver options and em rules were checked and retained.

| head | baseline status | continuation status | maximum probability change | raw objective change | maximum coefficient change |
|---|---|---|---:|---:|---:|
| `u` | complete | complete | `5.750508e-7` | `-1.034550e-10` | `1.716726e-6` |
| `q` | complete | complete | `2.948081e-7` | `-3.535661e-11` | `6.331226e-7` |
| `r` | complete | complete | `2.786669e-7` | `-1.901412e-11` | `5.279830e-7` |
| `g` | complete | complete | `3.449346e-7` | `-1.392664e-11` | `2.788602e-6` |

all four preview probes pass the UNCHANGED `1e-5` margin. the worst difference is about seventeen times below it. both `g` starts completed five em updates; continuation completed one. every inner solve completed and no observed-objective increase occurred. selected `g` responsibility changes were `5.791611e-7` and `6.077964e-8`; relative observed-objective changes were `8.395661e-13` and `6.729713e-14`, satisfying the original baseline and tighter em rules.

raw gradients remain explicit; tighter `ftol` does not make a claim that the alternative gradient stopping condition was reached:

| head | baseline raw maximum gradient | continuation raw maximum gradient | selected iterations, baseline/continuation |
|---|---:|---:|---:|
| `u` | `1.295461e-5` | `1.577522e-5` | `337/37` |
| `q` | `9.970524e-6` | `5.224114e-5` | `336/22` |
| `r` | `1.241858e-5` | `3.080303e-6` | `342/30` |
| `g` | `2.089612e-5` | `7.255374e-6` | `729/28` |

the selected iteration total for `g` sums its inner solves. actual calls included both starts: three calls per binary head, eleven for `g` across its baseline starts and continuation. measured baseline/continuation fit time was about `41` seconds combined on this fixture; source preparation is separate. no real-data cost or stability claim follows.

after approval, the concrete changes are:

1. change baseline `ftol` in `docs/specs/v1-05-execution-base.md` and the canonical `docs/specs/experimental-chance.md` from `1e-10` to `1e-14`; explicitly retain the tenfold tighter continuation and original observed-objective increase allowance.
2. change the literal solver definition in `execution_design.py` to bind the newly approved value in the recipe hash.
3. change `_solve_start`'s baseline constant in `execution_fit.py` to `1e-14`, its continuation comparison metadata to `1e-15`, and `execution_state.py`'s strict probe validation to the same approved tighter constant.
4. rerun the complete five-year fixture chain under the new recipe, preserving the old diagnostic families as historical evidence. inspect all twenty heads and all four final probes. the preview uses the existing predecessor ledger and does not establish this new full chain.

the `1e-10*(1+abs(old))` observed-mixture objective increase allowance is a DIFFERENT contract and stays unchanged. do not replace every textual occurrence of `1e-10`.

full evidence: `/tmp/execution_v1_05_stopping_preview_results.json`; native call log/status summary: `/tmp/execution_v1_05_stopping_preview.log`; temporary controller: `/tmp/execution_v1_05_stopping_preview.py`. all head statuses, exact solver calls, start/inner terminations, objectives, raw gradients, probability comparisons, source identities and selector records were retained. these are proposal receipts, not accepted annual artifacts. no real fit, source admission or completed numerical handoff is established.
