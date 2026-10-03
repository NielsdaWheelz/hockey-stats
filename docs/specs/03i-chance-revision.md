# pr03i — conversion localization and spatial composition

status: **specification ready for handoff; docs only. implementation/diagnosis require separate assignment.** 03h is reviewed and merged in `d828085`; [its decision](../research/chance-03h/decision.md) is `withheld`. [brief](../brief.md) · [plan](../plan.md) · [03j follow-up](03j-chance-experiment.md)

## target and boundary

produce new evidence for two unresolved problems: where overprediction concentrates within the revised failing probability bins, and how much measured calendar/shot-type composition changes recent/no-recent spatial discrepancies. conclude with one bounded next experiment or `no_supported_intervention`. unique causal attribution is not required to propose an intervention test.

this is the last general saved-evidence localization slice before selecting an experiment or recording insufficiency. use one composition, the original 712 assessment games and one saved-stream pass. no fitting/em, preparation, prediction/scoring, acquisition, recalibration, new features, eligibility/coordinate changes, transfer/final campaigns, player attribution or publication. no admission screen or new thresholds. 03b/03e/03h verdicts remain unchanged; no 04 handoff. existing shared artifacts suffice without the hdd.

## frozen inputs and validation

start with `/Users/nnandal/Documents/code/hockey-stats-03h-runs/assessment/completion.json`, sha256 `d1ec15ffb51748049efc79d847f0a454cfae5a8a90072880d276487e9d8dca2f`; its assessment is `9f226f0934244a22ff3fb8212bac271c3bfb589d63516c5664a31c79d085b889`. resolve 03g's completion/comparison/composition/stream through the linked identities and existing `chance_assessment.FROZEN_DIGESTS`; preserve parent execution identities separately. validate actual hashes/schema-1 kinds/cross-links. research inputs require these pinned artifacts and the withheld parent; fixture inputs retain `purpose: fixture_exercise` throughout. no relabeling or reopening fitted parents/raw captures.

retain all 85,317 recognized rows: 68,775 eligible, 16,270 outside scope, 272 unavailable; 49,014 eligible unblocked, 19,761 blocked and 2,804 goals. training ends `2024-12-31`; assessment is `2025-01-01`–`2025-04-17`. reuse 03h's checked-row/native probability/coverage reconciliation in the same stream pass, including all game identities and exclusions. reconcile reconstructed revised overall/bins and the two focal per-game bin triples to 03g/03h. require native `agrees` tolerance (`1e-10` relative/absolute); never silently intersect populations.

before new diagnostic arithmetic, freeze `inputs/protocol.md` binding this spec, input identities, executing revision, partitions, weights and resampling. these inspected development data remain research-exposed. do not claim untouched confirmation.

## probability localization

freeze revised own-bin membership using native twenty-bin arithmetic:

| quantity / saved revised field | applicable population | focal cohort |
|---|---|---|
| `unblocked_conversion` / `candidate_r` | eligible unblocked attempts | `[0.15,0.20)`: 2,465 attempts, 356 goals |
| `all_attempt_recorded_context` / `candidate_all` | every eligible attempt | `[0.10,0.15)`: 1,999 attempts, 192 goals |

for each whole applicable population and focal cohort, produce four separate exhaustive partitions: calendar month; original shot type with its model-type mapping; preceding kind (`none`, or `recent/<kind>`); native observed-proxy region. preserve null original type as missing. `previous_event.status` determines recentness: a `none` record may retain older event metadata. all-attempt geometry has a seventh `blocked_origin_unobserved` category; never assign block contacts or inferred origins to observed shooting regions. use `comparison.regions.cell_regions[proxy_cell_id]`, not raw coordinate cuts.

on identical rows report revision, baseline and saved `historical_stronger` direct probabilities (`candidate_r/all` versus `benchmark_r/all`). retain count, observed goals, predicted sum, signed excess goals `P−O`, residual rate `(P−O)/N`, contributing games and per-game additive triples. zero counts give null rates. each partition reconciles to its population/cohort; different families overlap and cannot be added. controls are conditional comparisons on revised membership, not their own calibration bins. validate complementary log probabilities with existing binary primitives; no clipping.

group tables are descriptive: distinguish high error rates from where most excess predicted goals occurs. no cartesian search, significance ranking, newly selected cutoff or subgroup removal. reuse 03h's linked cohort intervals rather than recalculate its admission decision. this adds revised-bin localization beyond [03f's existing marginals](../research/chance-03f/diagnosis.md); it does not identify a causal defect.

## spatial composition

use every eligible attempt, including blocks. context `c` is supported `none` or `recent`. preserve all six 03g regions in their pinned order. per region, retain `A_R = P(unblocked and proxy in R)` and revised `G_R = P(goal and proxy in R)`, using actual saved `region_probabilities`. observed positives are unblocked proxies in R, additionally `goal` for G; every blocked label is zero, without an assigned origin. denominator is **all eligible attempts in context**, not regional or unblocked attempts.

require six finite probabilities in `[0,1]`; their sums match saved marginal-unblocked/all-goal probabilities. baseline/revision A vectors agree. unblocked proxy ids are valid; blocked proxies and inapplicable regional predictions remain null. date/month, original/model type and recent descriptors must agree with the saved row fields. reconcile baseline/revision regional global/context/per-game additive triples to 03g; do not reconstruct regional log losses from saved probabilities.

stratum `s = calendar_month × model_shot_type`: derive months from the selected date ledger (january–april 2025 for research) and use `wrist,snap,slap,backhand,tip,other`, at most 24 research cells. initialize zero-contribution selected games and cells. common support `C` requires `n_none,s > 0` AND `n_recent,s > 0`; no outcome, fitted-probability or minimum-count filter. declare fixed pooled weights:

`w_s = (n_none,s + n_recent,s) / Σ_C(n_none + n_recent)`.

for each context/quantity/region, retain three views, in order:

| view | residual rate |
|---|---|
| `full_raw` | `(Σ_all P − Σ_all O) / Σ_all n` |
| `common_raw` | `(Σ_C P − Σ_C O) / Σ_C n` |
| `standardized` | `Σ_C w_s (P_c,s − O_c,s) / n_c,s` |

report common and excluded attempts/positives/predicted mass for each context, strata with no shared support, counts and contributing games. keep all strata visible. empty C means standardized/common results are null with a reason; full raw remains available where supported.

for each SAME region/quantity, compute recent-minus-none contrast `D_view` and paired `adjustment_shift = D_standardized − D_common_raw`. never contrast one context's 10–20 ft region with the other's 20–40 ft region. distinguish full→common exclusion from common→standardized weighting. compare point magnitudes and context-specific errors: a changed contrast does not establish removal of either absolute error. A is unchanged by conversion replacement; G includes conversion. neither isolates origin versus avoidance or establishes physical origins/opportunity bias. month adjustment addresses assessment-population composition, not training-to-assessment drift.

## uncertainty

only spatial views/contrasts/shift need new intervals; localization groups remain descriptive. reuse paired whole-game, seven-day and fourteen-day sampling: 2,000 `PCG64` draws, seed `3032026`, pointwise 95% linear percentiles. generate one shared draw matrix per method, retaining every selected game/empty calendar block/final partial block. hold C and original weights fixed. resample additive sums jointly across contexts/regions, then recompute ratios; a weighted sum of stratum ratios is not a pooled ratio.

an absent positive-weight stratum in a required context makes that statistic's draw undefined; no redraw, stratum dropping or reweighting. any undefined draw gives a null interval and retained count/reason. preserve point estimates and contributing game/block counts. pooled helpers own raw ratios; a small explicit calculation owns standardized and paired statistics. store rates as proportions; display `100 × rate` as percentage points/per 100 eligible attempts. intervals condition on saved fits and empirical support/weights; fitting, selection and origin-law uncertainty are excluded. no new support/failure classification or favorable-method selection.

global calendar draws can omit an entire month, so standardized calendar intervals and dependent contrasts/shifts will usually be null under this rule. this is a resampling limitation, not inadequate source coverage. retain raw calendar intervals and the whole-game standardized comparison; do not silently switch to within-month sampling.

## command, files and ownership

new outputs live under `/Users/nnandal/Documents/code/hockey-stats-03i-runs`, shared outside git/worktrees. from repo root:

```sh
UV_PYTHON=3.14.8 uv run --locked --project analysis python analysis/research/chance_residual_diagnosis.py --completion /Users/nnandal/Documents/code/hockey-stats-03h-runs/assessment/completion.json --protocol /Users/nnandal/Documents/code/hockey-stats-03i-runs/inputs/protocol.md --out /Users/nnandal/Documents/code/hockey-stats-03i-runs/diagnosis
```

| owner/file | contract |
|---|---|
| new `analysis/research/chance_residual_diagnosis.py` | completed-evidence loading, scalar localization, spatial aggregation/standardization, paired intervals and figures; no model execution |
| `chance_assessment.py` | retain strict checked-row/native reconciliation; only a narrow extraction/in-pass consumer justified to share its single pass. no duplicate validator, second read, generic callback framework or changed 03h result/schema |
| `chance_evaluation.py`, `chance_review.py` | authoritative binary/bin arithmetic, native region definition, pooled/calendar resampling and existing artifact helpers; reuse without unrelated refactor |
| `diagnosis.json` | schema 1, `artifact_kind: chance_residual_diagnosis`; purpose; input/protocol/current and parent identities; inherited decision; population/coverage; `localization` quantity/population/cohort/partition records and per-game triples; `spatial` region/type/month/context domains, per-game stratum triples, C/weights/exclusions, all three views/contrasts/shift; resampling/support/missing reasons; measured resources |
| `completion.json` | schema 1, `artifact_kind: chance_residual_diagnosis_completion`; input/protocol/output/figure identities and resources; written last after reconciliation |
| `docs/research/chance-03i/` | short protocol, decision and verification; two figures under `figures/`; existing issues updated with new facts |

compact triples use `[count, observed_positive_count, predicted_probability_sum]`; bind one ordered game/date ledger and explicit quantity/population/cohort/partition/group or context/stratum/region/predictor keys. stratum keys are `[calendar_month, model_shot_type]`. interval records retain `estimate`, `interval`, `undefined_draws`, `missing_reason` and contributing/selected game/block counts; standardized records also retain per-stratum support. null rates/intervals remain null, never zero.

require a new output outside inputs. malformed evidence/numerics exits nonzero without completion; valid insufficient diagnostics exit `0`. hash the stream during its sole read; retain compact accumulators, not another prediction stream/grid/posterior. record actual time/memory/bytes. this is minutes-scale saved arithmetic, not an hour-long scoring replay. interruption reruns the cheap command; no runner/checkpoint machinery, new dependency or interpreter-pin change.

## content, verification and completion

the content owner makes two restrained figures: `localization.png`, four partitions × two focal cohorts with identical baseline/revision/control memberships, counts and clearly descriptive residuals; `spatial-composition.png`, both compound quantities/all regions with full/common/standardized paired context contrasts, shared units and separate method facets. show absent intervals explicitly; no nine-whisker overlays, opportunity maps or dashboards. accompanying tables retain context-specific absolute residuals, counts/sums/support; captions name denominators, proxy boundaries and conditional uncertainty.

`decision.md` states what is NEW, then evidence→mechanism→competing explanation→ONE smallest discriminating experiment, or `no_supported_intervention`. smaller point discrepancies after matching favor measured composition; wider intervals alone do not. persistence leaves predictor underfit and proxy measurement unresolved. any next intervention names its target component and baseline comparison, promises neither unique causation nor repair of both problems, and requires a separate 03j specification. no reflexive general-diagnosis sequel or automatic fit. candidate withholding and unassessed admission obligations remain explicit.

temporary integration/live red → green → refactor → green covers the complete saved-fixture command and independently worked unequal-game/composition examples: full/common/standardized separation, fixed weights, paired draws, no common support, disappearing bootstrap strata, zero cells, cohort boundaries, partition reconciliation and blocked geometry. check rejection of inconsistent descriptors/proxies/regional probabilities and guard preparation/prediction/scoring/fitting/raw-parent access. verify narrow reuse leaves 03h's fixture behavior unchanged. no repeated exhaustive generic rejection campaign. after statistical/systems/content review delete ALL test code/test-only dependencies; retain useful fixtures/facts.

completion requires one reconciled real pass, every declared partition/region/view, honest missingness/intervals, readable artifacts, one justified recommendation or insufficiency, updated issue facts and deleted temporary tests. no diagnosis or fitting occurs during specification authoring.

tradeoff: fixed pooled common-support weights yield an inspectable comparison but restrict the population and condition uncertainty on its estimated composition. one cheap, finite diagnosis delays a fit while reducing speculative repairs; it cannot uniquely establish the cause or rehabilitate the withheld candidate. [03j](03j-chance-experiment.md) retains the structural backlog and remaining admission work.
