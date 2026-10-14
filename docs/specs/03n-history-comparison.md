# pr03n — short versus expanded training history

status: **specified; implementation and real fitting await separate assignment.** 03m is reviewed and merged in `8cb0ff1`; [its audit](../research/corpus-03m/decision.md) supplies five inventories, not model admission. user choice, 2026-10-13: external-only outputs, manual rerun risk accepted; no further drive investigation or special recovery machinery. [brief](../brief.md) · [direction](../research/model-direction.md)

## question and boundary

does adding the complete 2021–22/2022–23 observations improve later **recorded goal probabilities on eligible unblocked 5v5 attempts**, under our current direct-conversion estimator?

deliver four fresh native fits, exact common assessment streams, paired comparisons and a developmental horizon recommendation. a negative or inconclusive result completes the study. no acquisition, new features, sequence filter, recency weighting, penalty sweep, historical-family activation, outcome decomposition, joint em, origin fit, player estimate, model admission, 04 handoff or publication. retain supported inactive code. [03o](03o-outcome-decomposition.md) remains separately specified/assigned after reviewing this result.

this is a **native estimator-horizon package**. geometry/type/context are shared across years; annual shooter/goalie states are jointly fitted. longer history changes actor support/state dimensions, earliest seasonal reference, borrowing and likelihood-to-penalty balance. it neither isolates sample size nor implements hockeyviz's single-season prior propagation. [published xg8](https://hockeyviz.com/txt/xg8) passes preceding-season player estimates/evidence into annual fits; that redesign is separate.

## fixed evidence and populations

canonical manifests:

- `/Volumes/Expansion/hockey-stats/corpora/03m-20261010-02/20212022/corpus.json`, sha256 `30eb12b290ccd9af9eae7ade8c7dcd5f285129b52b646eec3fced3e2628badc8`.
- `/Volumes/Expansion/hockey-stats/corpora/03m-20261010/{20222023,20232024,20242025,20252026}/corpus.json`.
- 03m selection `/Volumes/Expansion/hockey-stats/runs/03m-20261010-03/inputs/selection.json`, sha256 `2e924d8ca08c4bd1191d4b3f9bfccbd4f795f8bc6283d39b5aed3c81c579bdac`; final audit sha256 `78d4034971e8d781ceb5dfa6af56b64ffb423e368027dc9c08a6701a4540b6d6` at its sibling `audit/admission-audit.json`.

these are committed evidence references, not a fresh external-byte verification during specification. before execution, verify the bound selection/audit and obtain all five actual manifest identities from their input records. freeze consumed envelope/selection/preparation identities with native readers; no re-admission campaign, stale-path substitution or invented hashes. preserve all existing raw/evidence/study paths.

selection stays schema 2, with explicit `corpora:[{path,game_ids}]`, `purpose='research'` and `history_corpora=[]`. older observations enter `corpora`, hence the likelihood, not merely historical feature facts. choose dates from admitted inventory. within each corpus order game ids by `(game_date,game_id)`; concatenate corpora in season order. use the identical assessment selection/order/cohort across arms.

| window / partition | short training | expanded training | common later assessment |
|---|---|---|---|
| development | all 2023–24 plus 2024–25 before `2025-01-01`; 1,912 games; 128,679 applicable / 7,614 goals | add all 2021–22/2022–23; 4,536 games; 306,041 / 18,471 | remaining 2024–25; 712 games; 49,014 / 2,804 |
| season_transfer | all 2023–24/2024–25; 2,624 games; 177,693 / 10,418 | add all 2021–22/2022–23; 5,248 games; 355,055 / 21,275 | all 2025–26; 1,312 games; 87,018 / 5,291 |

research checks require exact inventory sets/dates, these game/row/goal totals, disjoint training/assessment keys and every assessment date after all training dates. every selected game stays, including zero-contribution games. both binary training outcomes must exist. the five distinct seasons reconcile to 442,073 applicable / 26,566 goals; never sum overlapping windows. existing assessments are research-exposed; development assessment becomes transfer training. the windows are chronological checks, not independent confirmation.

all six cohort files (four training, two shared assessment) use schema 1 and `quantity='unblocked_conversion'`, `definition={mode:'all_source_eligible',required_families:[]}`. preserve every recognized source key/status/reason and study disposition in order. labels stay in prepared source/prediction rows and reconcile through `outcome_audit.json`, not added to cohort membership. eligible unblocked rows are included; eligible blocks are not applicable; source `out_of_scope|unavailable` remains source-excluded. zero feature omissions. failed active encoding is a located contract failure, never an additional selection rule. no intersection of mismatched streams or 03l sequence-selected control.

03m's unresolved membership, coordinate frames, 2,601 unavailable recognized rows and one unknown overtime horizon retain native dispositions. conversion loss has no elapsed-time denominator; do not require complete full-game exposure or invent it. references are retrieval-dated; no new bio/affiliation covariates. malformed inputs, identity disagreement, changed digests and missing promised files stop execution; valid unavailable evidence stays unavailable.

## identical recipe, native numerical meaning

one schema-3 config serves all four cells. `trait_assumptions=[]`; `r` families exactly `game_additive,recent_additive,recent_interactions` in canonical order. inactive `origin,u,unblocked,all_attempt` declare `game_additive,recent_additive`; those declarations confer no fitting permission. all native geometry, six model types, circumstance transforms and actor treatment stay unchanged.

| exact config fields | values |
|---|---|
| `kernel_distance_ft,kernel_direction_strength` | `20,4` |
| `ridge_origin_base,ridge_cell,ridge_benchmark` | `.25,.25,.25` |
| `ridge_origin_factor,ridge_type_cell` | `1,1` |
| `smooth_origin,smooth_cell,ridge_context` | `4,4,4` |
| `ridge_shooter,change_shooter,ridge_goalie,change_goalie` | `4,16,16,64` |
| `optimizer_max_iterations,optimizer_ftol,optimizer_gtol` | `2000,1e-10,1e-6` |
| `em_max_iterations,em_relative_tolerance,em_posterior_tolerance,objective_decrease_tolerance` | `2000,1e-8,1e-6,1e-10` |

fit ALL native `r` coefficients afresh, zero initialization except each cohort's empirical goal log-odds intercept. different goal rates legitimately give different initial intercepts. no saved coefficients, warm starts, offsets, old loss as control or fifth fit.

native objective is summed binary negative log likelihood plus unchanged penalties: unpenalized intercept; `ridge_context=4` on nonreference season/context terms; existing base/type spatial ridge and neighbor smoothness; shooter/goalie level penalties and adjacent-year first differences over all selected annual states. earliest selected season is the seasonal-offset reference; expanded likelihood is not normalized to preserve an effective penalty strength. changed reference/shrinkage/support belongs in the interpretation.

all selected years define the season domain, even an empty year. prediction in 2025–26 carries the latest fitted season/actor state from 2024–25; it does not fit a future state. unseen actors contribute zero residual; older-only actors can have a latest state inferred through penalties. retain native `season_basis,state_season,actor_evidence` and counts rather than calling all of these observed support.

preserve native `L-BFGS-B` success plus finite coefficients/objective. relative objective reduction can terminate before the gradient tolerance; [scipy's documented stopping rules](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html) explain the distinction. no silent iteration/tolerance changes, tighter post-result fits or extra starts. numerical success and predictive benefit remain separate.

## composition, owners and capability contracts

`explicit selections → core evidence → all-source cohorts → native setup/capacity → four fits/evaluations → strict paired report`.

| owner / files | responsibility |
|---|---|
| `analysis/src/hockey_stats/chance_data.py` | add `prepare_core(selection_path)`, sharing current selection/source traversal/order/coverage assembly with full `prepare`. reuse `prepare_game_attempts`; omit only feature/history materialization. reject nonempty `history_corpora`; retain full preparation and all supported families |
| `chance.py` | share `compile_component_design(attempts,config,*,quantity,seasons)` with native layout/season construction. factor `prepare_component_fit(...)` from current component validation/membership/encoding, returning `(layout,data,centers,edges,initial)`; preserve unsupported-binary failure diagnostics with null data/initial. one native initializer/objective dispatch serves capacity, fitting and verification; no second numerical implementation |
| `chance_cohort.py,chance_features.py,chance_evaluation.py` | existing membership, 65 selected columns, binary summaries and descriptors; no new eligibility/encoder or generic feature platform |
| `analysis/research/chance_development.py` | factor shared `fit_prepared(args,prepared)` / `evaluate_prepared(args,prepared)` artifact operations. current commands still call full `prepare`; 03n calls `prepare_core`. extend cli, evaluation and `validate_evaluation` together for `short` / `expanded` arms restricted to full-source conversion; preserve supported `baseline` / `sequence` behavior |
| new `analysis/research/chance_history.py` | thin manual selection/window/recipe validation, cohort/capacity commands, four-cell orchestration by explicit operator invocation and report/content. reuse `implementation,resources,validate_evaluation,paired_rows,compare_pair,calendar_blocks,ratio_interval` and figure primitives |
| `docs/research/chance-03n/`, fixtures/issues | statistician owns protocol/decision; content designer owns population/capacity labels and comparison/figure; data owner preserves distinct evidence; independent reviewers challenge each boundary |

core preparation returns all recognized attempts and every game with identical model-consumed core fields, input identities/order, dates and nullable source coverage. per-game `feature_games`/`feature_player_games` joins remain complete dictionaries with explicitly inactive empty values. the study accepts only the three core families/no trait assumptions; selecting other families through this path fails explicitly. no duplicate selection/coverage reader, fake feature values, automatic core/full fallback or changed `PREPARATION_IDENTITY` for a projection.

full preparation's inactive sequence diagnostics are outside the projection equivalence claim. retain native evaluation's `sequence_index=null` bookkeeping bucket for schema/summary reconciliation, but omit it from displayed/report comparison groups and label it `not_prepared` in `diagnostic_scope`; never call it observed absence. retain full sequence extraction for its actual consumers. all other promised source/type/recent/role/month/support descriptors and predictions must agree with full preparation.

native component/fit/evaluation/completion/prediction schemas stay 3; config 3, cohort 1, selection 2. adding named full-source arms is a current capability extension, not a compatibility reader or reason to rebuild old artifacts. source/prediction binding and omitted-row semantics remain strict; `short|expanded` reject any selected-family cohort or omission. do not use `chance_sequence.py`'s equal-training-cohort, sequence recipe or fixed-short-window validators for this experiment.

## manual commands, capacity and files

all commands run from `analysis/` as `.venv/bin/python research/chance_history.py <command> ...`. required paths are located, nonrepeated/nonabbreviated; help exits 0, syntax 2, input/numerical/resource/i/o failure 1. outputs are new exclusive directories outside every input root. fixture exercises use explicit bounded chronological selections and `purpose='fixture_exercise'`, without research counts/nominations.

| command | required flags / result |
|---|---|
| `cohort` | `--selection --protocol --out`; existing `cohort.json` and `outcome_audit.json` for each of six partitions |
| `capacity` | `--selection --cohort --config --protocol --out`; largest expanded-transfer native setup, one initial objective/gradient, `capacity.json`; NO optimizer |
| `fit` | `--selection --cohort --config --protocol --window --arm --out`; native fit/component/completion |
| `evaluate` | `--selection --cohort --component --protocol --window --arm --out`; complete recognized `attempts.jsonl`, native evaluation/completion |
| `report` | `--inputs --protocol --out`; validated paired `result.json`, figure and completion |

`window=development|season_transfer`, `arm=short|expanded`, quantity fixed to `unblocked_conversion`. validate supplied preparation against actual selection identity before shared artifact operations. complete evaluations require one identical assessment cohort identity per window; training cohorts differ by exact horizon. successful completions are written last; failed fits retain diagnostics and no successful component/completion.

capacity preflight uses the complete 5,248-game expanded-transfer selection, its exact cohort and production setup. `capacity.json`, schema 1 / `artifact_kind='chance_history_capacity'`, has `purpose,selection,cohort,config,protocol,implementation,preparation_identity,setup_status,counts,design,dimensions,array_bytes,initial,resources_before_serialization`. `setup_status='valid'` requires all reconciliation checks and finite native arithmetic. counts are native source/cohort totals; dimensions include the 65-column scalar shape and season/actor/core coefficient counts; initial has empirical intercept, objective and gradient maximum; resources are measured wall seconds/rss bytes BEFORE writing the artifact. validate saved config/cohort/capacity serialization by rereading them; do not serialize prepared matrices or invent a successful component.

run the capacity command under `/usr/bin/time -l`, retaining its exact timing/stderr log. after exit, the operator writes a small exclusive `capacity-measurement.json`, schema 1: `capacity,timing_log,argv,exit_code,wall_seconds,peak_rss_bytes,peak_footprint_bytes`; the first two are `{path,sha256}` references. require exit 0 and both final peaks ≤ **48 gib** (`48*2**30` bytes) BEFORE the first fit. the report rebinds both artifacts/log and independently extracts the log's final rss/footprint fields. setup validity alone is not a resource pass; the command cannot know a post-exit footprint. this operating envelope leaves 16 gib on the 64-gib host. record starting host conditions and separately estimate parameter-sized optimizer workspace, naming assumptions; preflight does not measure a full optimized fit or promise its peak. no dense attempts × all-coefficients matrix.

if capacity fails, record the cause and stop expensive work; repair demonstrated unused/duplicate materialization at its owner and remeasure with exact numerical equivalence. never shrink selections, alter penalties/convergence or silently switch hardware. no memory supervisor, auto tuning, lazy feature platform or new storage format.

all real inputs/outputs are external under a fresh explicit `/Volumes/Expansion/hockey-stats/runs/chance-03n-<run-id>/`: `inputs/` holds protocol/config, six selections and report inputs; sibling `cohorts/<partition>/`, `capacity/`, `fits/<window>/<arm>/`, `evaluations/<window>/<arm>/`, `report/` and factual receipts. this sibling layout respects selection-parent/output restrictions. do not relocate frozen studies. fixtures use local outside-input outputs and need no hdd.

check actual mount/expected inputs/output parent before each manual batch; missing volume/i/o stops the command, no substitute root. user accepts external-only result writing and manual rerun risk. completed fits remain intact; an interrupted cell restarts into a fresh explicit directory after ordinary input revalidation. no local fit copy, physical-cause gate, deliberate drive interruption, checkpoint engine, retries or runner. code must fail normally; no special drive-defense system.

## paired assessment and developmental decision

primary: expanded minus short mean goal log loss, **nats per eligible unblocked assessment attempt**; negative favors expanded. secondaries: brier, observed/predicted goals, signed pooled residual in percentage points and change in absolute pooled residual. use stable native log probabilities, no clipping. retain twenty own-arm half-open bins (last includes 1), and paired bins defined by SHORT probabilities. changed bin membership is not paired calibration improvement.

fixed separate report groups: `recent_context,model_type,calendar_month,role,actor_support:shooter,actor_support:goalie`. short defines paired actor-support memberships; expanded-own support summaries remain separate. additionally retain per-actor 3×3 support transitions (`observed_in_state,other_seasons_only,unseen`) with applicable count/goals, descriptive only. no subgroup nomination, cross-product search, causal support claim or new admission gate.

per window: 2,000 paired whole-game draws and 2,000 each nonoverlapping 7-/14-calendar-day block draws; `PCG64`, seed `3032026`, 95% linear-percentile intervals. reuse identical sampled units across arms/metrics, pool sums/counts, never game means. blocks start at earliest assessment date and retain empty games/days/intervening blocks/final partial block. undefined draws produce null intervals without redraw; report contributing units. intervals condition on the four fitted models and omit fitting/selection/source uncertainty. twelve thousand draws, ZERO bootstrap fits.

freeze arithmetic deadband `d=1e-10` nats/attempt; verify exact identity and both signed near-identity directions independently using [03l's arithmetic evidence](../research/chance-03l/verification.md). it is not a hockey-effect threshold, solver-error bound or useful-effect guarantee. show unrounded deltas/intervals, relative loss change, magnitude, contrary brier/calibration and numerical limitations. never tighten fitting or change gates after seeing results.

| both-window condition | `direction` |
|---|---|
| missing, nonconverged, unreconciled cell or undefined primary point | `incomplete` |
| both primary point deltas `< -d` | `expanded_direction` |
| both `> d` | `short_direction` |
| both within `[-d,d]` | `within_arithmetic_deadband` |
| otherwise | `mixed_direction` |

nominate `expanded` only for expanded direction, both game upper bounds `< -d`, all three interval methods defined in both windows, and no calendar lower bound `> d`. symmetrically nominate `short` only for short direction, both game lower bounds `> d`, all methods defined, and no calendar upper bound `< -d`. otherwise `nominated_horizon=null,recommendation='no_supported_horizon'`; supported cases use `recommendation='supported_horizon'`. research results use `scientific_assessment='not_admitted'`. fixture exercises give `direction='not_assessed',recommendation='fixture_only',nominated_horizon=null,scientific_assessment='not_performed'`; native fit/evaluation records also retain `not_performed`. nomination is conditional research evidence, not automatic horizon adoption, final model acceptance or 03o execution. an inconclusive result proves neither horizon sufficient.

## schemas, content and execution acceptance

new report-input schema 1: `schema_version,purpose,capacity,windows,resampling`. capacity has `status,setup,measurement,failure,stop_reason`; `complete` requires both bound preflight artifacts and the operating pass, otherwise `failed|not_run` locates the failure/reason with unfinished references null. windows have exactly the two names and `short,expanded` cells. each cell has `status,config,training_cohort,assessment_cohort,fit,evaluation,failure,stop_reason`; artifact references use `{path,sha256}`. `fit,evaluation` explicitly reference their native `completion.json` files, whose bound component/diagnostics/evaluation/stream references are followed and validated. `complete` requires both successful completions and no failure; `failed|not_run` retain null unfinished artifacts and located reason/diagnostics, including failed fit diagnostics through `failure`. each assessment pair references one cohort; training identities follow exact horizon selections. source/numerical/resource failure stops later expensive cells. scientific direction does not stop the second window.

new `result.json`, schema 1 / `artifact_kind='chance_history_result'`: `purpose,inputs,protocol,implementation,quantity,population,diagnostic_scope,direction,recommendation,nominated_horizon,scientific_assessment,execution_status,coverage,cells,comparisons,resampling,arithmetic_deadband_nats_per_attempt,limitations,resources,figure`. coverage has native source/study/applicability counts by partition/season/outcome with no duplicated-window league total. cells bind component/design/native diagnostics and resources. comparisons use existing paired results with `baseline=short,changed=expanded`, explicit role mapping, own-arm bins, short-owned groups and support transitions. all component/protocol/config/selection/cohort chains and full ordered streams must reconcile; never accept equal counts as equal membership.

reload each completed fit and recompute its saved native objective once through shared setup/objective. use existing `agrees` (`rel_tol=1e-10,abs_tol=1e-10`). write a per-cell bound verification receipt under the report output: schema 1, `purpose,component,selection,cohort,config,protocol,implementation,saved_objective,replayed_objective,difference,gradient_max_abs,agrees`; cells reference it as `verification`. keep these facts outside the compact component schema. this is verification, not another solve or gradient gate. reuse live preparation where practical; release arrays between cells. disagreement prevents a successful report; a valid report of declared incomplete execution is evidence, not study completion.

content designer's committed `docs/research/chance-03n/`:

| artifact | what good content must show |
|---|---|
| `protocol.md` | frozen question, exact six selections/five manifests, config/code/lock/preparation identities, native horizon/reference semantics, counts, capacity budget and prospective numerical/assessment/stop rules; freeze before fitting |
| `result.json` | complete bound result projection, unrounded values, denominators/units, explicit nulls/reasons and resource costs; no raw/prediction stream or full coefficient duplication |
| `decision.md` | population table, absolute/paired losses and conditional intervals, contrary calibration/brier, support changes, nomination/limits and what remains for 03o; no player/card/xg-parity claim |
| `figures/history.png` | two rows, one per window: paired log-loss delta with all three intervals and zero line; short-defined bin residuals with shared axes and nonempty counts. legible units/denominators; own bins stay separate machine tables |
| `verification.md` | exact commands/resources/input hashes, core/full/numerical equivalence, independent reviews, interruptions if any and temporary-code deletion |

execution after separate assignment: temporary fixture red → implement → green → refactor → green; independent systems/statistical/content prefit review; freeze clean code/config/input identities and protocol; complete full capacity preflight; run development short → expanded → transfer short → expanded, each followed by its evaluation; paired report; independent numerical/source/content review; delete all temporary tests/controllers/bytecode/test-only dependencies. retain supported code, original fixtures, useful scientific commands and expensive fits. new distinct failures follow the existing [fixture policy](../../fixtures/README.md); no new permanent test harness before 07.

software acceptance: independent core/full projection, input-order/nullable-coverage/cohort equality; all 65 active encodings and complete native designs/actor counts equal WITHIN each identical selection, not across horizons; controlled short/expanded likelihood+penalty and gradient checks; per-cohort intercept, carry-forward/unseen behavior, native fixture fit/prediction equivalence; changed-digest/foreign-key/truncated/reordered/mislabeled-stream rejection; symmetric decision boundaries, zero/undefined units and independent paired bins/intervals; capacity setup/post-exit receipt reconciliation, exclusive paths, ordinary missing-input failures and detached fixtures. no changed source bytes or historical scientific results.

real study completion requires successful capacity, all four converged fits/evaluations, exact full-population reconciliation and independently verified report. gain/admission is NOT required. an input/resource/numerical stop produces explicit `incomplete`, not empirical rejection or a fabricated completion. retain measured costs and concrete blockers in issues; do not keep expanding verification after required checks pass.

tradeoffs: fresh controls cost recomputation; more history changes support/borrowing/shrinkage and may amplify drift; fixed penalties are not fixed effective regularization; conditional intervals omit refitting uncertainty; core projection adds one explicit capability while keeping inactive extraction; 48-gib headroom can require owner-level memory repair; external-only writes can lose an interrupted solve, with rerun accepted. reviewing these costs/benefits chooses 03o's horizon later; no additional acquisition or automatic campaign.
