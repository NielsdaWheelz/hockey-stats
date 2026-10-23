# approved stopping amendment

user approval was relayed by root on 2026-10-22. commit `841be03` makes the four owned-file changes: baseline solver `ftol=1e-14`, continuation comparison `ftol=1e-15`, the literal recipe definition, and both authoritative specification owners. the dated specification note explains the relative-loss failure, unchanged `1e-5` probability margin, preserved failed evidence and fresh-chain requirement.

new recipe hash: `cfbda18bf84d3ad211d97d621b56f8346c223c14553aa6cb661ee4be3d64be09`.

the old recipe `eba7057ff0314232b591aecc1af2b211ffaec269fa79638f6d3236f4f5e82304` is reproduced exactly by changing only the new literal solver definition's `ftol` back to `1e-10`. current strict reading rejects chain05 with `execution recipe definition differs`; no reinterpretation or promotion occurred.

actual red: before the production edit, the existing independent temporary numerical check was changed to require continuation metadata `optimizer_ftol==1e-15`. running it failed at that contract assertion (`/tmp/execution_v1_05_numerical_checks.py`, line 169). after the minimal edit the same complete check passed, including all original finite differences, native mirror penalties, exact em identity, hand intercept, history, unavailable failures, diagnostic counting and continuation invariants.

a native-solver spy then observed exactly:

```text
baseline:     maxiter=2000, ftol=1e-14, gtol=1e-6
continuation: maxiter=2000, ftol=1e-15, gtol=1e-7
```

this exercised the actual production path, not a constant-only source assertion. the recipe reconstruction and historical-family rejection also passed. both specification notes and their existing amendment-review link were checked; `git diff --check` passed. the diff contains only the three solver/recipe literal changes and the two specification updates. the distinct `1e-10*(1+abs(old))` observed-mixture increase allowance is unchanged.

the artifact owner separately owns strict probe metadata validation at `1e-15` and the new complete five-year fixture chain. that chain remains required; the already frozen `/tmp/execution_v1_05_stopping_preview_results.json` remains historical proposal evidence under its original recipe and predecessor. no real fit was run by this numerical amendment task. temporary mathematics/source checks are retained pending final acceptance.


cleanup after green — 2026-10-22: root accepted the local numerical boundary after fixture chain06 completed twenty heads and passed four probes, with independent mathematics and option checks green. the seven temporary controllers and three owned bytecode files were deleted; their paths above are historical references. all result/receipt/proposal/log files and fitted fixture states remain retained. exact deletion and retained-file existence checks are recorded in `/tmp/execution_v1_05_cleanup_manifest.json`. full real acceptance remains open.
