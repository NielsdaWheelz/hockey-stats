# pr03g — conversion integration and observable geometry

status: **specification ready for handoff; docs only so far. implementation/diagnostic execution require separate assignment.** [03f](../research/chance-03f/decision.md) merged in `9c5f3dc`; context interactions improve component losses without resolving calibration. [03e remains withheld](../research/chance-03e/decision.md). [brief](../brief.md) · [plan](../plan.md) · [03h follow-up](03h-chance-revision.md)

## target and scope

answer three questions: what does the saved conversion improvement change in composed probabilities; where do observable spatial predictions disagree with recorded evidence; how much does standardized opportunity change? produce a bounded diagnosis and one justified next recommendation, possibly none. diagnostic completion does not admit a model or supply a 04 handoff.

include one composition, one original development assessment, existing scalar benchmarks and at most three figures. exclude all fitting/em, kernel variants, acquisition, changed eligibility/coordinates, transfer/final fits, player attribution, publication, effect changes and a lasting test harness. the shared local corpus and saved runs suffice; no hdd is required.

## frozen inputs

use `/Users/nnandal/Documents/code/hockey-stats-03e-runs` and `/Users/nnandal/Documents/code/hockey-stats-03f-runs` read-only. create new outputs under `/Users/nnandal/Documents/code/hockey-stats-03g-runs`, shared outside git and worktrees. resolve parents through these indexes, not filenames guessed from branch names:

| index | sha256 | selects |
|---|---|---|
| `03e-runs/inputs/development-evidence.json` | `cdaa37d12e8cbfa1d48d86871eb3ab77a49b9d0d8997ef99794151f40261f0e9` | original `anchor` assessment/model/score; frozen `stronger` direct comparators |
| `03f-runs/inputs/screen-evidence.json` | `59f6dd8011d496a9ed3ba9783059c8b333a3eadbbc354721a492a64dad4a462c` | `development/context_interactions/unblocked_conversion` and improved direct `all_attempt_recorded_context`; linked study inputs/selections |

the selected anchor model digest is `fff2c86b743fcbcae3a44848e9ae084341bcec00ecbd77797b0060c276a1549e`; replacement conversion digest is `590e411694e52dacb42d9f57cd8935e3988a049fa5436da8314e31f28d5faf98`. retain their original protocol/implementation identities alongside this slice's execution identity.

training: 1,912 games through `2024-12-31`, 181,147 eligible attempts; conversion uses 128,679 unblocked attempts. assessment: the original 712 later 2024–25 games, 85,317 recognized attempts: 68,775 eligible, 16,270 outside scope, 272 unavailable; eligible outcomes are 49,014 unblocked, 19,761 blocked and 2,804 goals. training/assessment ids are disjoint and assessment dates strictly later. no 2025–26 component substitution: its later training cutoff would contaminate this comparison.

before diagnostic execution, save `inputs/protocol.md` and `inputs/evidence.json`. the latter has `schema_version: 1`, `artifact_kind: chance_conversion_integration`, `purpose: research`, and `{path, sha256}` references `protocol`, `source_evidence`, `component_screen`. the loader resolves and records the selected parents, selections, original assessments/scores and saved component evaluations; require the screen's linked study inputs to bind the same original evidence/parents/selections. fixture verification uses the same shape with `purpose: fixture_exercise`; it cannot be relabeled research. no general experiment matrix or user-configurable region search.

## composition contract

baseline is the saved anchor. revision retains anchor's origin `π`, avoidance `u`, forward kernel and joint shooter–goalie reference; replace only conversion with the complete saved interaction `r`, including its refitted spatial, scalar and actor coefficients. additive terms can change even on no-recent rows.

`prediction_context(model, *, conversion=None)` owns validated layouts and coefficients per stage. native prediction remains the existing capability; the supplied conversion must pass `validate_component` and match training identities/selection/dates/counts, config, seasons/grid, category orders and actor identities/support against the anchor's extracted conversion. the numerical capability accepts existing `additive` or `recent_interactions` components; real 03g evidence must select the declared interaction component. additive extraction is the exact-reuse control, not a second research recipe. use the selected stage's actor evidence and seasonal-state semantics.

reuse `predict_attempt`, `reference_probabilities` and `score_attempt`; narrowly extract their shared cell-level terms for region sums. never fabricate an unblocked observation to call `predict_component` on candidate origins. reference scoring must encode scalar features separately for `u` and `r`; its current single additive vector cannot represent revised conversion. isolate baseline/revision reference caches.

for cell `h`, standardized opportunity is `v(h) = Σ_(s,g) ρ_anchor(s,g) u(h;s,target) r(h;s,g,target)`, holding recorded type/context fixed. attempt value is `V = Σ_h q_anchor(h)v(h)`. average pairwise probability PRODUCTS, not products of marginal averages; retain anchor's `20242025` reference weights and target state. unblocked `q` is the recorded-proxy point mass; blocked `q` retains its original conditional inference.

do not mutate the anchor into a newly fitted model or copy its em diagnostics onto the composition. native model/checkpoint schemas remain unchanged; they reject composition manifests. existing native and component formats are current inputs, not legacy compatibility paths.

## diagnostics

**factual probabilities:** separately report observed-cell unblocked conversion, all-attempt composed goal probability and unchanged marginal-unblocked probability. use existing binary metrics, twenty own fixed bins and source-defined type/context/month/role/home-away groups. paired actor-support groups use anchor-defined memberships; retain revised support separately. report the anchor-defined `[0.10,0.15)` all-attempt cohort on identical rows, separately from own-bin calibration. historical `stronger` remains the direct comparator for both goal quantities; the saved improved direct component is an additional all-attempt scalar comparator. neither gets spatial or opportunity maps. these are retrospective recorded-context probabilities, not demonstrated pre-release forecasts.

**observable spatial outcomes:** partition native cell centers, in this precedence:

1. `behind_goal`: `x > 89`.
2. `outside_attacking_zone`: `x <= 25`.
3. remaining cells: distance to `(89,0)` in feet in `[0,10)`, `[10,20)`, `[20,40)`, `[40,∞)`, named `in_zone_0_10`, `in_zone_10_20`, `in_zone_20_40`, `in_zone_40_plus`.

use native `cell_id` for observed unblocked proxies; never use raw-coordinate regions against quantized probability sums. for every eligible attempt, `A_R = Σ_R πu` predicts “unblocked and proxy cell in R”; `G_R = Σ_R πur` predicts “goal and proxy cell in R”. blocked compound labels are zero without assigning a shooting origin or zero opportunity. contexts are exactly `all`, `none`, `recent`, from supported preceding-action presence. every denominator is ALL eligible attempts in that context. regions partition outcomes/probability mass; `none + recent = all`. never compare unconditional `π` directly with selected unblocked locations. regional discrepancies cannot uniquely identify the faulty component or prove blocked-origin accuracy.

**opportunity changes:** retain baseline/revision totals and cell-mass arrays separately for blocked/unblocked attempts; report signed total change, mean absolute and maximum absolute event-value change, plus regional mass differences. arrays sum to event values and retain native orientation/units. opportunity has no observed calibration target in this slice. do not independently normalize maps or interpret their changes as player effects.

reuse paired whole-game and 7/14-calendar-day bootstrap arithmetic for pooled goal log-loss, brier and calibration deltas: 2,000 `PCG64` draws, seed `3032026`, pointwise 95% linear percentiles, pooled additive sums/counts. retain empty units and final partial blocks; undefined draws produce null intervals without redraws. regional residual intervals use whole-game resampling only, with counts/contributing-game support visible; constant-label regions carry that limitation. no subgroup admission thresholds or opportunity error bars. intervals condition on fitted models and omit fitting, selection and origin-law uncertainty. historical margins are reference lines, not newly selected gates. these exposed seasons remain development evidence.

## command, artifacts and owners

from the repo root, after the locked environment is prepared:

```sh
uv run --project analysis python analysis/research/chance_integration.py --evidence /Users/nnandal/Documents/code/hockey-stats-03g-runs/inputs/evidence.json --out /Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis
```

one command; no fitter, resume or automatic next stage. reuse `Once`, strict json, `linked_path`, `identity`, `output_path`, `write_json` and implementation identity. require a new output directory outside inputs. input/numerical/pairing failure exits nonzero and leaves no completion; `0` means diagnostic completion, never admission. interrupted cheap work is rerun explicitly. preserve original fits/captures.

| output | contract |
|---|---|
| `composition.json` | schema 1, `artifact_kind: chance_conversion_composition`; resolved parent/index/protocol/selection identities, compatibility facts and executing implementation; `scientific_assessment: not_performed`; no duplicate coefficient arrays or fitted-model status |
| `attempts.jsonl` | every recognized attempt once, keyed `(game_id, source_index)`; source/event/date/season, prepared status/reasons/labels and diagnostic descriptors; eligible rows contain baseline/revision and scalar-comparator factual log probabilities, fixed-region `A_R/G_R` arrays, proxy cell only when unblocked, and two opportunity scalars. inapplicable predictions are null. retain stage evidence; bind composition identity once in the enclosing summary |
| `comparison.json` | schema 1, `artifact_kind: chance_conversion_diagnosis`; binds composition and keyed stream; coverage/game dates, resolved benchmark identities, probability summaries/own bins/paired groups/cohort, per-game additive sums, regional definitions/context summaries, opportunity totals/cell arrays, invariant maxima and measured resources |
| `completion.json` | schema 1; identities of composition, stream, comparison and generated figures; written last after reconciliation/rendering |

binary/region records reuse `count`, `observed_positive_count`, `predicted_probability_sum`, `log_loss_sum`, `brier_score_sum`; derive residual percentage points as `100*(predicted−observed)/count`. region records also identify quantity/region/context and per-game sums; zero counts yield null rates. opportunity arrays use grid order, expected-goal units and separate blocked/unblocked counts. all numeric outputs are finite or explicit nulls. pair complete recognized streams, labels, statuses, sources and dates with saved evidence; no silent intersections. record actual file identities, not just parent directory names.

pair semantic dispositions explicitly: native score `valued` means prepared `eligible`; component `predicted` means eligible/applicable; conversion `not_applicable` means eligible/blocked. `unavailable` and `out_of_scope` retain their meanings. reject any other disagreement; do not require literal status-name equality across these current formats.

| owner/file | responsibility |
|---|---|
| `analysis/src/hockey_stats/chance.py` | strict conversion composition; shared per-cell prediction/reference and selected actor semantics |
| `analysis/src/hockey_stats/chance_evaluation.py` | reuse binary aggregation; fixed compound regional labels/sums |
| new `analysis/research/chance_integration.py` | evidence resolution, one-pass diagnosis/output assembly and figures |
| existing `analysis/research/chance_development.py`, `chance_review.py` | reuse row pairing, diagnostics and pooled/calendar arithmetic; extract narrowly if this removes duplication |
| `docs/research/chance-03g/` | short protocol, verification, decision and at most three figures; issues retain unresolved scientific problems |

no changes to capture/reconstruction/preparation, effect, dependencies or publication. if a distinct source defect is discovered, preserve its original bundle under the fixture policy and record the blocker; no source-repair detour.

## content and verification

content owner defines three figures: own-bin conversion/all-attempt residual panels on shared axes with counts and differing-membership warning; regional residuals in a two-quantity × three-context panel layout, six region labels per panel, per 100 eligible attempts, showing unchanged `A_R` once; blocked/unblocked signed opportunity-change maps on one symmetric expected-goal-per-cell scale. no unsupported confidence shading. captions name population/cutoff, grid, units/sign, reference where relevant, proxy meaning and uncertainty limits. tables retain absolute counts/totals and adverse groups; no interactive report or player cards.

temporary integration/live red → green → refactor → green uses committed raw fixtures and reusable saved 03f fixture parameters: `03f-runs/verification/fixture-native-reference/model.json` and `03f-runs/verification/capacity-compact/conversion/component.json` match inputs/selection/config/grid/training dates. [03f verification](../research/chance-03f/verification.md) retains their provenance. cover the complete command, reload/pairing and the following independent checks; then delete ALL test code/test-only dependencies, retaining useful facts/artifacts:

- additive extracted conversion reproduces native anchor probabilities/reference values within absolute `1e-12`; existing native prediction meaning remains unchanged.
- revised observed-cell conversion matches saved 03f predictions; nonzero interaction, spatial and actor terms plus brute-force joint reference arithmetic verify stage-specific encoding and complete replacement.
- `π/u`, blocked `q`, marginal-unblocked and every `A_R` remain unchanged within `1e-12`; per-region probabilities sum to their overall probabilities, and origin/opportunity mass conserves.
- baseline factual sums reconcile to saved schema-3 assessment; baseline values/posteriors reconcile to original anchor score rows. use existing `agrees` (`1e-10` relative/absolute) for aggregate roundoff; compare individual values within `1e-12`.
- complete keys, source identities, labels/statuses and populations match; reject missing/duplicate rows, incompatible parents, wrong component kind, future/overlapping assessments and unavailable context recoded as none. region-boundary labels use native cells.
- pooled unequal-game/empty-block/undefined arithmetic agrees with independent examples; fitting/em entrypoints are guarded against execution. inputs remain unchanged.

before the full diagnostic, freeze protocol/implementation identities and measure a small fixed assessment prefix against the verified baseline. record wall time, memory and output bytes; use bounded existing caches and streaming. no approximate pair averaging, cell pruning or accidental full posterior export. compare the measured budget with saved 03e scoring costs; an unexpected hours-long diagnosis requires a measured explanation/repair, not more fits. full execution makes one bounded paired pass over the 712 games; no repeated training or entire three-season source audit.

acceptance: those reconciliations pass; all declared evidence and at most three legible figures exist; independent numerical/systems and content review finds no unresolved correctness error; tests are deleted. update existing issues with evidence without changing historical verdicts. `decision.md` answers the three target questions, preserves contrary groups/measurement limits and recommends `assess_integrated` (prospective assessment in 03h, no admission), one named structural hypothesis, or `no_supported_hypothesis`. **no numerical success threshold or handoff is required.**

tradeoffs: saved-fit reuse isolates conversion changes without another expensive em campaign; it does not prove revised player attribution. compact rows/cell summaries avoid duplicating full posterior streams; originals remain attributable and richer later outputs get their own contract. coarse fixed regions and conditional bootstrap intervals provide bounded diagnosis, not physical-origin validation or exhaustive spatial inference. origin-law sensitivity remains required for affected later claims even if these checks look good.
