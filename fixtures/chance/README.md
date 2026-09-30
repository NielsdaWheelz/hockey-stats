# chance-workflow fixture exercise

these selections exercise `chance-1` software offline. they are not an admitted training population or scientific assessment. the configuration is the specification's numerical exercise, not a scientific default. all derived artifacts belong under ignored `var/`.

## preparation and commands

from the repository root:

```sh
mkdir -p var
cd analysis
uv sync --locked
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20252026 --games ../fixtures/captures --out ../var/chance-corpus
.venv/bin/hockey-stats-chance fit --selection ../fixtures/chance/train.json --config ../fixtures/chance/candidate.json --out ../var/chance-fit
.venv/bin/hockey-stats-chance evaluate --selection ../fixtures/chance/assessment.json --model ../var/chance-fit/model.json --out ../var/chance-assessment.json
.venv/bin/hockey-stats-chance score --selection ../fixtures/chance/scoring.json --model ../var/chance-fit/model.json --out ../var/chance-scored
```

all output paths must be new, with existing parents. the selection paths resolve relative to their json files. training uses the two october games; assessment uses the march game, strictly later and disjoint. scoring deliberately includes training games for retrospective analysis. neither assessment nor scoring changes the fitted model.

## hand-checked source facts

source indices below refer to interpreted play-by-play order; the embedded source identities locate the unchanged capture evidence. [existing fixture facts](../README.md) document source checks and reconstruction limits.

| game / source index | fact | consequence |
|---|---|---|
| `2025020001 / 2` | shooter `8473419`, team `13`; opposing reported goalie `8481519`; block coordinates `(-61,3)` normalize to `(61,-3)` | shooting ownership is retained; these coordinates are block evidence, not a shooting origin |
| `2025020001 / 66` | chicago's first goal occurs at 1/10:03 with score `0–0` beforehand | goal outcome cannot supply its own pre-event score |
| `2025020001 / 73` | florida scores at 1/11:06, previously trailing `0–1` | use trailing, not the tied post-goal snapshot |
| `2025020001 / 90,136` | florida's non-5v5 goal gives it a `2–1` lead; chicago's subsequent 5v5 goal begins trailing `1–2` | goals at other strengths contribute to score context |
| `2025020006 / 44,73` | edmonton's non-5v5 goal precedes its 5v5 goal; the latter begins leading `1–0` | scope exclusion does not remove a completed goal from score accounting |
| `2025020006 / 357,358,370` | three shootout goal records occur after timed play ends `3–3` | shootout outcomes do not increment timed scores |
| `2025021094 / 164,173` | carolina's penalty-shot goal creates a `2–1` lead; toronto's 5v5 goal begins trailing `1–2` | the penalty shot is outside scope but contributes to timed goal accounting |
| all three games | 362 timed attempts, including 273 reconstructed 5v5 before further eligibility; 111 timed blocks lack shot type and reported goalie id | 362 is not the fitting denominator; on-ice evidence supplies goalies; shot type cannot be a stage predictor |
| admitted season inventory | 1,312 expected games, three captures, 1,309 missing | explicit selection is not season coverage |

reconstruction retains 118 unresolved elapsed seconds in the march game. event membership and exposure are distinct; interval linkage is retained but does not establish rate compatibility. [shot-location evidence](../../docs/issues/shot-location-evidence.md) and [overlapping-shift evidence](../../docs/issues/overlapping-shift-evidence.md) remain open scientific responsibilities.

## quantities and costs

an unblocked recorded coordinate is a quantized origin proxy. a block receives a retrospective origin distribution conditioned on its observed block evidence. its reference opportunity can be positive although a known blocked attempt cannot score. this value is not a forecast, causal player contribution, or fitted-parameter uncertainty interval.

the common reference averages each training shooter–goalie pair's product of stage probabilities. `weight` is attempt mass; `opportunity_mass` is its contribution in expected goals. summing cell contributions gives `reference_opportunity_value`; do not multiply those contributions by the weights again.

full distributions cost disk. interrupted numerical work restarts into a new directory; completed fits remain reusable. the coarse grid, fixed kernel, regularization and unseen-actor prior modes require assessment in 03b. finite fits and software checks cannot establish origin accuracy or credible chance values.

## software verification record — 2026-09-29

four sol workers divided source preparation, numerical fitting, command/evaluation composition and independent adversarial checks. installed-command and preparation checks first failed on absent modules. implemented behavior passed; refactoring centralized geometry/feature order, reused the fixed prediction context, removed redundant prediction fields and retained exact numerical contracts. the final installed-command checks passed again. no configuration value was changed to obtain convergence.

| final fixture exercise | result |
|---|---|
| training | `2025020001` and `2025020006`; 184 eligible attempts |
| em starts | uniform: 83 iterations; unblocked-frequency: 84; both converged |
| selected start | `unblocked_frequency`; penalized observed objective `-1508.9121373428075` |
| assessment | `2025021094`; 89 eligible attempts, including 60 unblocked |
| scoring | 378 recognized attempts: 273 valued, 103 outside scope, two unavailable; 362 are timed |
| origin basis | 183 recorded proxies; 90 inferred block distributions |
| numerical checks | finite parameters/metrics; normalized kernel/origin/reference mass; spatial value conservation within absolute `1e-10` |
| local resources | final automated fit: 9.605 seconds wall; peak child rss 141,918,208 bytes (135.3 mib), python 3.14.7 / numpy 2.5.3 / scipy 1.18.1 on mac arm64 |

independent arithmetic checked pre-goal scores, actors/ownership, quantization, the forward kernel, marginal likelihood, posterior normalization, fractional count conservation, full penalized objective, analytic gradients against finite differences, frozen e-step weights and the exact joint reference product. saved-model evaluation was recomputed independently for candidate/benchmark log loss, brier score, probability sums, calibration and per-game conservation. train-return/save/load scoring agreed. seven fixture shooters seen only in blocks retained evidence in `u` and prior-mode status in `r`.

adversarial checks covered accumulated missing fields, unknown role, missing selected games, unavailable identity, input errors, owner conflicts and shootout chronology; malformed models/configuration/provenance; existing outputs; same-date/overlapping assessment and fixture-purpose relabeling. one injected failed em start retained the other; both failed starts and one-class training produced no usable model. changing a held-out outcome changed assessment without changing fitted coefficients/reference/kernel. changing block evidence changed its retrospective posterior while leaving outcome-blind prediction unchanged. scoring worked with inaccessible training envelopes and without `fit.json`. raw captures, references and consumed corpus bytes remained unchanged; repeated score rows were byte-identical.

an actual installed score process was terminated during jsonl writing: partial attempts remained without `score.json`, reuse was rejected, and the completed fit remained intact. temporary tests, scripts and the separate formatter environment were deleted after final verification; no test-only dependency was added to the project. production validation and scientific evaluation remain. future changes must recreate appropriate checks until the lasting verification slice.

these are software facts from small development exercises, not origin accuracy, calibrated hockey probabilities, uncertainty coverage, or permission to use these values for player attribution. 03b remains unperformed. the known 118-second reconstruction gap and unresolved location evidence remain open.
