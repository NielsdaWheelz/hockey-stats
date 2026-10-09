# chance-2 fixture exercise

these selections exercise software, not an admitted scientific training population. all artifacts retain `purpose: fixture_exercise` and `scientific_assessment: not_performed`. the schema-3 configuration retains the exact 03d numerical settings, with `[game_additive,recent_additive]` explicitly selected in all five stages and no trait assumptions: all penalties are one, distance is 20 feet and direction strength is four. none was selected for attractive fixture predictions.

## preparation and commands

from the repository root, use an external run directory with sibling inputs, corpora and reports. rebuild all twenty-one committed capture bundles against their three season references. the numerical selections retain the original eighteen-game exercise; the three later source-boundary games are admitted only as history evidence:

```sh
fixture_repo="$PWD"
fixture_run=/absolute/fixture-run
mkdir -p "$fixture_run/inputs" "$fixture_run/corpora" "$fixture_run/reports"
cd analysis
uv sync --locked
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20232024 --games ../fixtures/captures --out "$fixture_run/corpora/20232024"
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20242025 --games ../fixtures/captures --out "$fixture_run/corpora/20242025"
.venv/bin/hockey-stats-corpus --reference ../fixtures/references/20252026 --games ../fixtures/captures --out "$fixture_run/corpora/20252026"
.venv/bin/python - "$fixture_repo" "$fixture_run" <<'PY'
import json
from pathlib import Path
import sys

repo, run = map(Path, sys.argv[1:])
histories = [str(run / "corpora" / f"{year}{year + 1}" / "corpus.json")
             for year in (2023, 2024, 2025)]
for name in ("train", "assessment", "scoring"):
    selection = json.loads((repo / "fixtures/chance" / (name + ".json")).read_text())
    for entry in selection["corpora"]:
        year = int(entry["game_ids"][0][:4])
        entry["path"] = str(run / "corpora" / f"{year}{year + 1}" / "corpus.json")
    selection["history_corpora"] = histories
    (run / "inputs" / (name + ".json")).write_text(json.dumps(selection, indent=2) + "\n")
PY
.venv/bin/hockey-stats-features --selection "$fixture_run/inputs/scoring.json" --config ../fixtures/chance/candidate.json --out "$fixture_run/reports/features"
.venv/bin/hockey-stats-chance fit --selection "$fixture_run/inputs/train.json" --config ../fixtures/chance/candidate.json --out "$fixture_run/reports/fit"
.venv/bin/hockey-stats-chance evaluate --selection "$fixture_run/inputs/assessment.json" --model "$fixture_run/reports/fit/model.json" --out "$fixture_run/reports/assessment.json"
.venv/bin/hockey-stats-chance score --selection "$fixture_run/inputs/scoring.json" --model "$fixture_run/reports/fit/model.json" --out "$fixture_run/reports/scored"
```

outputs must be new, with existing parents. selection paths resolve relative to their json files. training uses `2023020001`, `2024020001` and `2025020001`, with 276 eligible attempts across the admitted seasons. the target reference is the latest training season, `20252026`; its 98 eligible attempts supply joint shooter–goalie pair frequencies. the three explicit history inventories supply strictly earlier-date facts, never additional target rows or reference members. most inventory games have no fixture capture, so historical totals correctly remain unavailable. those inactive requirements do not affect this unchanged additive exercise. assessment uses `2025021094`, dated `2026-03-20`, strictly later and disjoint, with 91 eligible attempts. scoring deliberately includes all eighteen development fixtures, including training games. assessment never changes the fit or reference.

interpretation/reconstruction envelopes use schema 4; interpreted reference and corpus reports and selections use schema 2. regenerate them from unchanged original captures. old affected contracts fail explicitly. preserve expensive historical artifacts at their historical git revisions; the mathematical family remains `chance-2`, with no scientific admission.

configs, fit/model/checkpoint artifacts, score rows and score completion use schema 3; evaluations use schema 4; components use schema 2. numerical artifacts bind current preparation and exact stage designs, including fixed transforms and penalties. evaluate writes a new json file; fit and score create new directories. none overwrites an existing output or writes within an input directory. [research composition](../../README.md#chance-research-review) uses sibling input/output directories and an explicit schema-2 evidence manifest; that reviewer rejects these fixture artifacts.

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

all committed season inventories contain 1,312 expected games. six/seven/eight captures are present, leaving 1,306/1,305/1,304 absent. the original numerical selections target six/four/eight games; the additional three captures are source boundaries, not extra training rows. this deliberately small selection establishes neither full-season coverage nor scientific independence: all three seasons have already been examined.

## feature inspection

`features.json` schema 1 reports field/design availability with exact denominators, source locators naming their supported field, selected designs and resources; `completion.json` is its final success marker. zero/false are values. null fields retain unavailable/conflict/not-applicable reasons. partial `known_*` sums do not become complete totals. valid source gaps succeed; malformed contracts fail. no fit or scientific assessment is performed.

to activate another family, copy the config to the external inputs directory and change the appropriate canonical stage list. missing selected requirements fail with a keyed error; rows are never silently dropped. `recent_geometry` and `off_wing` are restricted to `u,r,unblocked`; off-wing requires the saved `reported_hand_stable_trait` assumption and a supported hand even on the centerline. outcomes, postgame totals and direct bio/coach/venue effects remain excluded from focal predictors. [03k's ledger](../../docs/research/features-03k/ledger.md) owns exact names/order/scales and limits.

## quantities and recovery

unblocked locations remain quantized recorded origin/contact proxies, including tips without relocation. each block retains its observed contact coordinate and receives a conditional origin distribution. posterior mass is not independent physical release evidence. `weight` is origin probability mass; `opportunity_mass` is its expected-goal contribution. sum contributions to get `reference_opportunity_value`; do not multiply them by weights again.

reference opportunity averages each target-season shooter–goalie pair's PRODUCT of unblocked and conditional-goal probabilities, freezing original selected circumstances and shooter hand, then swapping only residual execution coefficients. a block can retain positive standardized opportunity despite an observed zero goal. this is retrospective opportunity valuation, not total defensive value, a causal decomposition or a demonstrated pre-release forecast.

schema-4 assessment retains overall probability bins per game and adds additive subgroup sums with the same category/value descriptors as the global groups. zero-count groups remain present in every selected game; per-game subgroup bins are absent. metrics identify `goal` or `unblocked` outcomes through `outcome` and `observed_positive_count`. period and minute-band groups support residual diagnostics without recomputing predictions.

`tip_distance` bands are `0_10`, `10_20`, `20_40` and `40_plus`, left-closed and right-open in feet. distance is `hypot(89−attacking_x, attacking_y)` before quantization; `tip_below_goal_line` is `attacking_x > 89`. both groups contain only eligible unblocked original `tip-in`/`deflected` events, and only candidate/benchmark `unblocked_conversion` metrics. their counts partition that tip subset. blocked tips retain block-contact evidence and are excluded from these location diagnostics. the fixture assessment has seven such unblocked tips, with distance-band counts `2, 2, 2, 1` and none below the goal line; these facts establish software behavior, not tip-location accuracy.

full block distributions retain every grid cell and cost disk. exact joint reference products use existing bounded numerical batches without a context cache; repeated computation keeps newly selected circumstance identity correct. no pruning or pair subsampling is used. preserve completed fits; regenerate cheap derivatives outside the worktree. scoring requires the model and an explicit selection to prepare shared game/player facts. `score.json` is written last and binds the complete scored stream. a missing completion artifact means interrupted work.

`--resume` requires the same exact inputs/configuration and clean implementation identity. it resumes accepted numerical state into a new output directory. before-earliest seasonal scoring remains unavailable; intermediate states and later carried-forward states are labeled. stage evidence distinguishes observations in the applied state, observations only in other seasons, and unseen zero prior modes; none identifies rookie status.

[03d verification](../../docs/research/chance-03d/verification.md) records historical numerical/resource checks; [03k verification](../../docs/research/features-03k/verification.md) records current preparation, baseline reproduction, live commands and full-corpus review. these establish software behavior only. 03b remains scientifically rejected. 03e completed its fixed [protocol](../../docs/research/chance-03e/protocol.md) with [withholding](../../docs/research/chance-03e/decision.md); [03j](../../docs/research/chance-03j/decision.md) remains inconclusive. dated studies execute historical git; 03k authorizes no new research campaign. 04 still requires supported values, compatible event/exposure selections and player robustness across the admitted family.
