# chance-2 fixture exercise

these selections exercise software, not an admitted scientific training population. all artifacts retain `purpose: fixture_exercise` and `scientific_assessment: not_performed`. the schema-2 configuration is the exact 03d numerical exercise: all penalties are one, distance is 20 feet and direction strength is four. none was selected for attractive fixture predictions.

## preparation and commands

from the repository root, prepare the locked environment and rebuild the committed captures against their three season references. the chance selections below retain the original eighteen-game exercise; the two later source-boundary fixtures are outside those selections:

```sh
mkdir -p var
cd analysis
uv sync --locked
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20232024 --games ../fixtures/captures --out ../var/chance-corpus-20232024
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20242025 --games ../fixtures/captures --out ../var/chance-corpus-20242025
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20252026 --games ../fixtures/captures --out ../var/chance-corpus-20252026
.venv/bin/hockey-stats-chance fit --selection ../fixtures/chance/train.json --config ../fixtures/chance/candidate.json --out ../var/chance-fit
.venv/bin/hockey-stats-chance evaluate --selection ../fixtures/chance/assessment.json --model ../var/chance-fit/model.json --out ../var/chance-assessment.json
.venv/bin/hockey-stats-chance score --selection ../fixtures/chance/scoring.json --model ../var/chance-fit/model.json --out ../var/chance-scored
```

outputs must be new, with existing parents. selection paths resolve relative to their json files. training uses `2023020001`, `2024020001` and `2025020001`, with 276 eligible attempts across the admitted seasons. the target reference is the latest training season, `20252026`; its 98 eligible attempts supply joint shooter–goalie pair frequencies. history informs estimates without entering reference membership. assessment uses `2025021094`, dated `2026-03-20`, strictly later and disjoint, with 91 eligible attempts. scoring deliberately includes all eighteen development fixtures, including training games. assessment never changes the fit or reference.

schema-3 reconstruction envelopes are regenerated from unchanged original captures. old envelopes, candidate configs, models and checkpoints fail explicitly. preserve expensive historical artifacts with their historical git revision; do not relabel them chance-2.

only evaluation changes to schema 3. configurations, fit/model/checkpoint artifacts, score rows and score completion remain schema 2. evaluate writes a new json file; fit and score create new directories. none overwrites an existing output or writes within an input directory. [research composition](../../README.md#chance-research-review) uses sibling input/output directories and an explicit schema-2 evidence manifest; that reviewer rejects these fixture artifacts.

## source facts and denominators

[the original capture facts](../README.md) retain exact source locators, receipts and evidence limitations. source indices refer to interpreted play-by-play order.

| evidence | consequence |
|---|---|
| `2025020001 / 2`, reported block `(-61,3)` rotates to `(61,-3)` for shooter `8473419`, team `13` | coordinates remain block contact evidence; the release distribution is inferred |
| `2025020001 / 66,73,90,136`; `2025020006 / 44,73` | all timed source goals update the score before later attempts, including goals outside genuine 5v5 |
| `2025021094 / 164,173` | the positively corroborated penalty-shot goal is outside scope but establishes the later `1–2` pre-event score |
| `2023020237 / 131,182` | exact `between-legs` / `Between Legs` and `cradle` / `Cradle` reconcile; both belong to model group `other` |
| `2024020340 / 342` | conflicting `snap` / `Wrist` stays unavailable; no preferred-feed replacement |
| `2025020184 / 158`; `2025020282 / 282`; `2025020307 / 14` | awarded/own goals retain credited scorers and observed goals, with unavailable analytical physical shooter and opportunity value |
| `2025020001 / 180`; `2025020184 / 157`; `2025020282 / 36,200` | immediately preceding `delayed-penalty` records are unsupported recent actions; no invented whistle reset or skipped predecessor |
| `2023020078`, all periods | contradictory defending sides retain unavailable frames and locations |
| `2025020544`, `2025020565` | elapsed exposure is unavailable; independent reported event membership still permits supported event valuation |

all eighteen games contain 2,210 recognized attempts, 1,623 reconstructed genuine-5v5 attempts and 1,530 chance-2 eligible attempts. those are different denominators. dispositions are 1,530 eligible, 585 outside scope and 95 unavailable. 119 recognized goals comprise 54 eligible, 57 outside scope and eight unavailable. applicable reasons are nonexclusive; an outside-scope goal can also have unresolved physical action. 03c had 1,537 eligible attempts: four recent-action failures and three unresolved awarded/own goals now become unavailable. the complete disposition and reason accounting is in [03d verification](../../docs/research/chance-03d/verification.md).

all committed season inventories contain 1,312 expected games. six/four/eight captures are present, leaving 1,306/1,308/1,304 absent. this deliberately small selection establishes neither full-season coverage nor scientific independence: all three seasons have already been examined.

## quantities and recovery

unblocked locations remain quantized recorded origin/contact proxies, including tips without relocation. each block retains its observed contact coordinate and receives a conditional origin distribution. posterior mass is not independent physical release evidence. `weight` is origin probability mass; `opportunity_mass` is its expected-goal contribution. sum contributions to get `reference_opportunity_value`; do not multiply them by weights again.

reference opportunity averages each target-season shooter–goalie pair's PRODUCT of unblocked and conditional-goal probabilities, holding recorded type/context fixed. a block can retain positive standardized opportunity despite an observed zero goal. this is retrospective opportunity valuation, not total defensive value, a causal decomposition or a demonstrated pre-release forecast.

schema-3 assessment retains overall probability bins per game and adds additive subgroup sums with the same category/value descriptors as the global groups. zero-count groups remain present in every selected game; per-game subgroup bins are absent. metrics identify `goal` or `unblocked` outcomes through `outcome` and `observed_positive_count`. period and minute-band groups support residual diagnostics without recomputing predictions.

`tip_distance` bands are `0_10`, `10_20`, `20_40` and `40_plus`, left-closed and right-open in feet. distance is `hypot(89−attacking_x, attacking_y)` before quantization; `tip_below_goal_line` is `attacking_x > 89`. both groups contain only eligible unblocked original `tip-in`/`deflected` events, and only candidate/benchmark `unblocked_conversion` metrics. their counts partition that tip subset. blocked tips retain block-contact evidence and are excluded from these location diagnostics. the fixture assessment has seven such unblocked tips, with distance-band counts `2, 2, 2, 1` and none below the goal line; these facts establish software behavior, not tip-location accuracy.

full block distributions retain every grid cell and cost disk. exact reference reuse is bounded in memory and requests only needed type/context/cell combinations. no pruning or pair subsampling is used. preserve completed fits; regenerate cheap corpora and scores into new paths. `model.json` alone suffices to score. `score.json` is written last and binds the complete scored stream. a missing completion artifact means interrupted work.

`--resume` requires the same exact inputs/configuration and clean implementation identity. it resumes accepted numerical state into a new output directory. before-earliest seasonal scoring remains unavailable; intermediate states and later carried-forward states are labeled. stage evidence distinguishes observations in the applied state, observations only in other seasons, and unseen zero prior modes; none identifies rookie status.

[03d verification](../../docs/research/chance-03d/verification.md) records historical numerical and resource checks. these establish software behavior only. 03b remains scientifically rejected. authorized 03e real fitting, assumption sensitivity and scientific assessment follow the [protocol](../../docs/research/chance-03e/protocol.md); [the decision](../../docs/research/chance-03e/decision.md) owns the conditional handoff or withholding. 04 still requires supported values, compatible event/exposure selections and player robustness across the admitted family.
