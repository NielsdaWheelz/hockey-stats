# pr03l — defending-sequence conversion screen

status: **implementation and real execution assigned on 2026-10-09; in progress.** 03k is reviewed and merged in `15647ff`; [its verification](../research/features-03k/verification.md) establishes preparation, not scientific support. user choices, 2026-10-09: test defending-skater continuity; use four fresh fits and conditional assessment intervals. [brief](../brief.md) · [direction](../research/model-direction.md) · [feature contract](03k-feature-repertoire.md)

## question and boundary

does verified defending shift-row persistence improve later **recorded goal conversion on eligible unblocked attempts**, beyond the improved immediate-context model? the competing explanation is that immediate context, geometry and existing actor/season terms already contain its useful information.

[hockeyviz xg8](https://hockeyviz.com/txt/xg8) motivates defending-skater sequences and reports earlier time-in-shift terms unhelpful. our existing `sequence` family adds elapsed sequence age as well as index contrasts: a related four-term package, not exact replication or direct measurement of possession, pressure or fatigue. do not reinterpret the four coefficients causally.

deliver a runnable bounded study, four native conversion components, reconciled comparisons and a developmental decision. a negative or uncertain result completes the study. no origin/avoidance/direct all-attempt fit, joint em, probability patch, new feature/source, penalty sweep, automatic campaign, player estimate, admission, 04 handoff or publication. retain every other correct feature implementation. historical verdicts and protocols stand.

## frozen recipes and evidence

| arm | `r` families, in canonical order |
|---|---|
| `baseline` | `game_additive,recent_additive,recent_interactions` |
| `sequence` | `game_additive,recent_additive,recent_interactions,sequence` |

use `quantity="unblocked_conversion"`. both arms refit ALL native conversion coefficients from existing native initialization: zero coefficients except the empirical training-goal log-odds intercept, identical across matched arms; no saved coefficients, fitted offsets or historical loss as control. keep spatial/type/shooter/goalie/season structure and borrowing unchanged. final actor layouts/counts use the common training cohort. sequence contributes `index==2,index==3,index>=4,age_seconds/60`, index 1 reference, existing `ridge_context` penalty. the existing preparation/encoder owns continuity, boundaries, evidence and units; no second sequence algorithm.

create fresh config schema 3 files. inactive `origin,u,unblocked,all_attempt` each declare `game_additive,recent_additive`; `trait_assumptions=[]`. the candidate differs only in its `r` family list. preserve these historical anchor numbers literally:

| fields | values |
|---|---|
| `kernel_distance_ft,kernel_direction_strength` | `20,4` |
| `ridge_origin_base,ridge_cell,ridge_benchmark` | `.25,.25,.25` |
| `ridge_origin_factor,ridge_type_cell` | `1,1` |
| `smooth_origin,smooth_cell,ridge_context` | `4,4,4` |
| `ridge_shooter,change_shooter,ridge_goalie,change_goalie` | `4,16,16,64` |
| `optimizer_max_iterations,optimizer_ftol,optimizer_gtol` | `2000,1e-10,1e-6` |
| `em_max_iterations,em_relative_tolerance,em_posterior_tolerance,objective_decrease_tolerance` | `2000,1e-8,1e-6,1e-10` |

unused joint settings confer no permission to run joint fitting. numerical-source evidence: `/Users/nnandal/Documents/code/hockey-stats-03e-runs/inputs/anchor.json`, sha256 `7889ec3a142e6f131ffa013df07f7399c15ba3e749b996c0d51abc8e1727676c`; old schema 2 is historical evidence, not an input to a compatibility reader.

current derived corpora: `/Users/nnandal/Documents/code/hockey-stats-runs/features-03k-20261009/corpora/final2/{20232024,20242025,20252026}/corpus.json`. bind actual manifest/consumed-byte identities and current preparation identity. the three seasons contain 3,936 games; originals remain under `/Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930`. no hdd or acquisition needed. regenerate derived inputs from originals with current commands only if needed; never modify originals or old fits.

| window | training selection | later assessment selection |
|---|---|---|
| `development` | complete 2023–24 plus 600 games in 2024–25 before `2025-01-01`; 1,912 games | remaining 712 games in 2024–25 |
| `season_transfer` | complete 2023–24 and 2024–25; 2,624 games | complete 2025–26; 1,312 games |

select dates from admitted inventory, not game-id arithmetic. selection schema 2 uses explicit target game ids and `history_corpora=[]`: selected families need per-game facts, not a historical-fact scan. this does not remove the model's seasonal actor borrowing. for research, require disjoint training/assessment keys, all assessment dates later than training, both binary outcomes in each training cohort and exact game counts. keep every selected game, including zero applicable/included attempts. all three seasons are research-exposed; `season_transfer` names chronology, not untouched confirmation.

## source eligibility and study inclusion

freeze the goal/prediction-blind additional inclusion rule, conditional on the fixed recorded-unblocked population: **source `eligible`, unblocked, and both existing sequence fields encodable**. only a located `FeatureUnavailableError` from those requirements permits exclusion; malformed input, unsupported vocabulary or a broken join contract fails. baseline family failures also fail. missing sequence is neither index 1 nor age zero. the rule cannot inspect focal goals, fitted coefficients or predictions.

both arms train and compare on EXACTLY these keys. preserve recognized source order, original eligibility/reasons/labels and the selected game ledger. missingness must not rewrite `coverage` or become a predictor. existing full-source coverage validation happens before fitting-cohort filtering; compile the final layouts/designs after filtering, with seasons from all selected games.

the saved [03k receipt](../research/features-03k/verification.md) supports `256,248/264,711` eligible unblocked attempts and `15,113/15,709` goals across all three seasons. omitted `8,463` attempts include `596` goals: omissions are selective; representativeness is unproved. source receipt is `reports/full-final3-family-availability.json` under the 03k run root, sha256 `3c675330e3818550b978af4a5b89b9386509d12c4b3cee7782d0d8033ec93537`. prospective preflight must reconcile those totals over distinct source keys (not sum overlapping windows) and report actual training/assessment counts by window, season, outcome and missingness reason. these all-season counts are not assessment denominators.

score the common-trained baseline on ALL eligible unblocked assessment rows. main metrics use included rows only; separately report included/omitted baseline losses, goal rates and predicted mass. candidate predictions on omitted rows are null with reasons. this selection audit needs no fifth fit and does not make the common cohort representative.

## contracts, composition and owners

`current prepared facts → explicit cohort → native component fit → full recognized prediction stream → included-only summaries / omission audit → paired report`.

| file/owner | responsibility and capability |
|---|---|
| new `analysis/src/hockey_stats/chance_cohort.py` | pure classification/validation and compact cohort summaries; reuse `chance_features` requirement encoding. one owner for membership, not an expression language or automatic filtering framework |
| `chance_data.py`, `chance_features.py` | existing preparation and exact bases; expose a narrow shared availability helper only if needed to avoid a duplicate encoder |
| `chance.py` | mandatory `training_cohort` argument to `fit_component`; validate original coverage, exact membership and included actor counts; native objective/gradient/penalty/prediction remain authoritative |
| `chance_evaluation.py` | `summarize_component` owns included-only metrics, separate source/study/prediction accounting and omitted-baseline summaries; preserve zero-contribution games |
| `analysis/research/chance_development.py`, `chance_review.py`, `chance_integration.py` | update affected component consumers; reuse identity/output helpers, `prediction_check,validate_evaluation,paired_rows,compare_pair,binary_record,calendar_blocks,ratio_interval`. the old twelve-cell `compare` is not this study |
| new `analysis/research/chance_sequence.py` | thin explicit manual `cohort,fit,evaluate,report` commands; four named cells, no scheduler, registry or second numerical implementation |
| `docs/research/chance-03l/`, `fixtures/README.md` | statistician owns protocol/interpretation; content designer owns labels/report/figure; data owner preserves distinct original failures; independent reviewers challenge boundaries |

proposed public calls: `component_cohort(prepared, *, quantity, required_families)` and `validate_cohort(cohort, prepared)` in `chance_cohort`; `fit_component(original_eligible_rows,config,metadata,*,quantity,design,training_cohort,feature_games,feature_player_games)`. use existing `stage_design,encode_stage_inputs,FeatureUnavailableError` and component prediction context. for this study requirements are exactly `['sequence']`; both arms consume the same cohort, although baseline does not use the family. membership checks bind identities/keys/dispositions; do not rely on equal row counts.

changed component/standalone fit/evaluation/prediction-stream schemas hard-cut to **3**. native full-model/config remain 3; native joint evaluation remains 4; source/selection schemas stay unchanged. update affected producers/readers together; old changed artifacts fail. historical commands run at their recorded git revision, without adapters. exact schemas:

- external `cohort.json`, schema 1: `schema_version,purpose,quantity,definition,selection,inputs,preparation_identity,game_dates,rows,counts,per_game,membership_sha256`. `definition={mode:'selected_family_complete',required_families:['sequence']}`. `rows` retains every recognized `(game_id,source_index)` plus `event_id,source_status,source_reasons,study_inclusion,study_reasons` in original order. inclusion is `included|feature_unavailable|not_applicable|source_excluded`; reasons retain exact missing field/evidence locators. counts/per-game reconcile source statuses, source-applicable/included/omitted totals. membership digest is sha256 of `json.dumps(rows,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')`; bind the file with existing path/sha256 identity. outcome counts belong in the audit, not membership selection.
- component 3 adds compact `training_cohort={definition,source_applicable_count,included_count,excluded_count,membership_identity}`. its original `training_eligible_attempts` stays the full source-eligible count. included count equals shooter AND goalie layout counts; source-applicable = included + excluded. the external identity binds the training cohort, never assessment membership; avoid embedding full rows/coverage in each component.
- `extract_component(model,quantity=...)` keeps its call contract, emits component 3 with explicit `all_source_eligible` mode, empty requirements, equal applicable/included native counts, zero exclusions and null membership identity. null is legal ONLY for that defined mode. full-model composition requires this mode plus existing exact source/actor/count matches; a complete-case 03l component cannot silently replace the old joint conversion stage.
- prediction row 3 keeps original keys/labels/provenance and adds `source_status,source_reasons,study_inclusion,study_reasons`; existing `status,reasons` describe prediction disposition. `applicable` describes source quantity applicability, independent of study inclusion. included rows in both arms are `predicted`; omitted baseline rows are `predicted`, omitted candidate rows `study_excluded` with `observed,log_p,log_not_p,probability=null`. source `out_of_scope|unavailable` retains that prediction disposition; eligible blocked rows are `not_applicable`; both have null predictions. raw `goal,blocked` remain intact. pairing compares exact keys, source identity/status/reasons, inclusion/reasons, raw `goal,blocked` and source-context groups. `observed` agrees on included rows; omitted baseline has `observed=goal`, candidate null. differing prediction disposition/observed is allowed ONLY for that declared omitted-row pair.
- standalone fit/evaluation completion 3 binds protocol, config, component, source selection/preparation, training/assessment cohort as appropriate and output identities; write completion last; failed fits emit diagnostics without a successful component/completion. evaluation adds `cohort` identity, included-only `metrics,groups,per_game`, separate accounting and `omitted_baseline` summaries. reject missing/duplicate/reordered rows, truncated streams, foreign identities and unreconciled sums; do not intersect streams or silently skip records.

new commands require located input paths: `cohort --selection --protocol --output`; `fit --selection --cohort --config --protocol --output`; `evaluate --selection --cohort --component --arm --protocol --output`; `report --inputs --protocol --output`. `--arm` is `baseline|sequence`. report input schema 1 contains exactly `schema_version,purpose,windows,resampling`: purpose `research|fixture_exercise`, matching every produced artifact; windows keyed `development,season_transfer`, each keyed `baseline,sequence`. each cell records `status,config,training_cohort,assessment_cohort,fit,evaluation,failure,stop_reason`, with status `complete|failed|not_run`. bind successful completions when produced; otherwise use null references, located failure diagnostics/logs and explicit stop reasons, never fabricated completions. `complete` requires both fit and evaluation. frozen resampling settings are exactly those below. fixture runs use explicit bounded chronological selections/counts and report `direction:'not_assessed',recommendation:'fixture_only',scientific_assessment:'not_performed'`; exact scientific game counts and research nomination apply only to research. validate the declared recipe; no discovery, implicit latest path, optional cohort fallback or network API.

## assessment and developmental decision

primary: paired candidate-minus-baseline mean goal log loss, nats per included attempt; lower is better. retain stable log probabilities, no clipping. secondaries: brier, observed/predicted goals, signed calibration residual in percentage points and change in absolute pooled residual. show twenty half-open probability bins (last includes 1) for each arm, and a separate paired calibration table using BASELINE bin membership. bin migration is not paired calibration improvement.

fixed separate descriptive groups: recent/none, model type, sequence index `1,2,3,4+`, calendar month, role and baseline-defined shooter/goalie support. reuse existing descriptors; no cross-product/search/subgroup nomination. record attempts/goals/predicted mass/losses/residuals, empty groups as null metrics. baseline owns paired groups even if actor-support presentation changes.

per window use 2,000 paired whole-game draws and 2,000 each nonoverlapping 7-/14-calendar-day block draws, `PCG64`, seed `3032026`, 95% linear-percentile intervals. use the same sampled units across arms/metrics; pool additive sums and counts, never average game means. blocks start at earliest selected assessment date; retain empty games/days/intervening blocks/final partial block. any undefined draw yields a null interval, without redraws. report contributing units. intervals for paired overall loss, brier and signed residual shift condition on the four fitted models; no bootstrap fitting. group/bin tables are descriptive, not simultaneous tests.

declare `1e-10` nats/row as a prospective arithmetic deadband; independently verify identity/near-identity loss arithmetic. it is neither a hockey-effect threshold nor permission to relax optimizer convergence. preserve unrounded estimates/intervals; no post-result epsilon. [03j roundoff](../issues/conversion-priority-roundoff.md) does not change 03j's verdict.

| condition across both windows | `direction` |
|---|---|
| any missing/nonconverged/unreconciled cell | `incomplete` |
| both primary point deltas `< -1e-10` | `consistent_direction` |
| neither point delta `< -1e-10` | `no_improvement` |
| otherwise | `mixed_direction` |

`recommendation=research_integration` only if direction is consistent, BOTH whole-game upper limits `< -1e-10`, all three interval methods are defined in both windows, and neither calendar method establishes harm (`lower > 1e-10`). otherwise `no_supported_next_fit`. this nominates separately specified research, not automatic execution. report adverse brier/calibration plainly; they are secondary evidence, not retroactively changed admission gates. no conversion-loss threshold can establish material player impact. show magnitude/relative loss change, predicted-goal mass and limitations; an inconclusive screen does not prohibit an explicitly chosen follow-up.

## execution and final artifacts

after separate implementation/execution assignment: temporary fixture checks → refactor/recheck → independent prefit statistical/systems/content review → freeze clean code, lock/config/input/cohort identities and immutable protocol → four sequential fits/evaluations → paired report → independent interpretation/integrity review. run development baseline/candidate, then season-transfer baseline/candidate; complete both windows irrespective of the first window's scientific direction. numerical/source/resource failure stops remaining expensive work with `incomplete`, not silently altered settings or replacement data.

use ordinary exclusive output directories outside git/worktrees, e.g. `/Users/nnandal/Documents/code/hockey-stats-runs/chance-03l-20261009/`. one preparation/fit process at a time; release arrays between cells. measure actual fixture preparation/fit/reload/comparison wall time, peak memory and artifact size before full fits, then record full costs. current preparation builds target facts; the 03k all-family audit's 42.8 gb peak is not a four-fit cost estimate. no new lazy/streaming framework without a demonstrated bottleneck. native component solves have no checkpoint; preserve completed components, rerun interrupted cells explicitly, without a recovery engine or silent limit increase.

outside git retain located selections/configs, immutable protocol, four cohort files (training/assessment per window), four fit directories, four evaluation streams/summaries/completions, report and factual verification/review receipts. cheap regeneration is allowed; old expensive fits stay intact. in `docs/research/chance-03l/` deliver:

| artifact / content owner | required content |
|---|---|
| `protocol.md` / statistician | frozen hypothesis, exact recipes/settings/windows/cohort, identities, numerical limits, intervals/decision/stop rules; no results chosen first |
| `result.json`, schema 1 / report owner | identities/artifact links; source/common/omitted coverage per partition/season/outcome/reason; four cell diagnostics/resources/metrics; two paired results/intervals; bin/group tables; `purpose,direction,recommendation,scientific_assessment,limitations`; research is `not_admitted`, fixtures `not_performed` |
| `decision.md` / content designer + statistician | one conclusion with two-window evidence, selective missingness, contrary secondaries and what the result permits; identify baseline omitted-row predictions as common-trained |
| `figures/sequence.png` / designer | one readable figure: two-window loss deltas and three interval methods against zero, plus paired baseline-bin residuals/counts; common axes/units; descriptive bin panels share membership within each window and show nonempty-bin n; retain all twenty bins in tables, with own bins separate |
| `verification.md` / systems reviewer | software acceptance separately from scientific result; exact commands/digests, independent calculations, resource measurements, reviews, integrity and temporary-test deletion |

good content explains the observable question before any coefficient, identifies each denominator, labels intervals **conditional on fitted models**, and makes null/omitted evidence visible. captions distinguish recorded coordinates/proxies from physical release truth. no maps/cards, total xg, standardized opportunity, causal interpretation or parity claim follows.

## software acceptance and costs

temporary integration/live red → green → refactor → green checks cover actual captures through cohort → fit → reload → later prediction → report. independently verify four sequence columns, objective/gradient and paired loss/bin/bootstrap arithmetic; unchanged raw/source eligibility and identical common-cohort actor counts across arms; real missing-sequence evidence; no-recent versus missing; zero-contribution games; unequal game sizes/undefined draws; identity/near-identity directions; forbidden labels/chronology; malformed/mismatched cohort and stream rejection; strict schema cutover and composition rejection. fixture fits are labeled software evidence. preserve a distinct new broken game's complete original bundle/receipts and checked reason under `fixtures/`, per its existing policy. delete all temporary tests/test-only dependencies after verification; keep analytical commands, fixtures and facts. no lasting harness before 07.

acceptance: all software checks/reviews pass; source integrity holds; four declared cells and both comparisons reconcile or an explicit bounded incomplete decision explains the blocker; content matches numeric evidence; temporary tests are deleted. scientific improvement is not required. record unresolved concrete defects individually in `docs/issues/`.

material tradeoffs: matching sacrifices coverage/representativeness for a fair feature comparison; four fresh solves cost more than reusing a historically different baseline; conditional intervals omit fitting/selection/origin uncertainty and repeated-season exposure; testing the four-term package cannot separate index from age. strict changed contracts require fresh components and old revisions for historical consumers. retained inactive families cost upkeep without entering this recipe. these are local research costs, not grounds for additional operational infrastructure.
