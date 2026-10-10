# 03l defending-sequence conversion protocol

date: 2026-10-09. assignment: implement and execute the complete [specified study](../../specs/03l-conversion-sequence.md). this protocol is prospective. its immutable execution copy and byte identities are retained outside git under `/Users/nnandal/Documents/code/hockey-stats-runs/chance-03l-20261009/`. software exercises are `fixture_exercise`; the four full cells are `research`. the scientific result cannot change this protocol.

## question and population

does verified defending shift-row persistence improve later recorded goal conversion on eligible unblocked attempts beyond the immediate-context model? the alternative explanation is that geometry, immediate context and existing actor/season terms already contain its useful information. this tests a four-term package: sequence-index contrasts and elapsed sequence age. it does not isolate possession, pressure, fatigue or a causal mechanism.

the source population is the existing recorded-unblocked population. the additional, goal- and prediction-blind rule is source `eligible`, unblocked, and both existing sequence requirements encodable. only a located `FeatureUnavailableError` permits exclusion; malformed facts, unsupported vocabulary, broken joins and baseline-family failures stop the command. missing sequence is neither index one nor age zero. original recognized order, source eligibility, reasons, labels, coverage and every selected game remain intact.

both arms fit on exactly the same included source keys. validate full-source coverage before filtering; compile final designs and actor counts after filtering, retaining seasons from every selected game. the saved 03k availability receipt reports 256,248 included of 264,711 eligible unblocked attempts, and 15,113 included of 15,709 goals across three distinct seasons. the omitted 8,463 attempts include 596 goals. preflight must independently reconcile these totals and partition/season/outcome/reason counts; overlapping windows must not inflate the all-season denominator. omission-reason tables group disjoint joint patterns of missing field, status and reason; exact evidence locators remain in membership rows. representativeness is unproved.

## recipes and numerical limits

quantity: `unblocked_conversion`. baseline `r` families: `game_additive,recent_additive,recent_interactions`. sequence `r` families: `game_additive,recent_additive,recent_interactions,sequence`. inactive `origin,u,unblocked,all_attempt` each declare `game_additive,recent_additive`; `trait_assumptions=[]`. config schema is 3. the two configs differ only in the `r` list.

all native conversion coefficients are freshly fitted. initialization is zero except the empirical training-goal log-odds intercept, identical across matched arms. spatial/type/shooter/goalie/season structure and borrowing remain native. the existing encoder supplies `index==2,index==3,index>=4,age_seconds/60`, with index one as reference and the existing context penalty. no saved coefficient, offset, fifth fit or second numerical implementation is permitted.

| fields | literal values |
|---|---|
| `kernel_distance_ft,kernel_direction_strength` | `20,4` |
| `ridge_origin_base,ridge_cell,ridge_benchmark` | `.25,.25,.25` |
| `ridge_origin_factor,ridge_type_cell` | `1,1` |
| `smooth_origin,smooth_cell,ridge_context` | `4,4,4` |
| `ridge_shooter,change_shooter,ridge_goalie,change_goalie` | `4,16,16,64` |
| `optimizer_max_iterations,optimizer_ftol,optimizer_gtol` | `2000,1e-10,1e-6` |
| `em_max_iterations,em_relative_tolerance,em_posterior_tolerance,objective_decrease_tolerance` | `2000,1e-8,1e-6,1e-10` |

the unused joint fields grant no permission for joint fitting. numerical-source evidence is `/Users/nnandal/Documents/code/hockey-stats-03e-runs/inputs/anchor.json`, sha256 `7889ec3a142e6f131ffa013df07f7399c15ba3e749b996c0d51abc8e1727676c`. it is historical evidence, not an input to a compatibility reader. the 03k availability receipt is `/Users/nnandal/Documents/code/hockey-stats-runs/features-03k-20261009/reports/full-final3-family-availability.json`, sha256 `3c675330e3818550b978af4a5b89b9386509d12c4b3cee7782d0d8033ec93537`.

## windows and input identities

dates come from admitted inventory. source selection schema 2 records explicit ids and `history_corpora=[]`; selected requirements need per-game facts. seasonal actor borrowing remains intact. training and assessment keys are disjoint; every assessment date follows every training date; both binary outcomes must occur in each training cohort.

| window | training | later assessment |
|---|---|---|
| `development` | all 1,312 games in 2023–24 and 600 games in 2024–25 before `2025-01-01`; 1,912 games | remaining 712 games in 2024–25 |
| `season_transfer` | all 2,624 games in 2023–24 and 2024–25 | all 1,312 games in 2025–26 |

all seasons are research-exposed. chronology is not untouched confirmation. current corpus manifests live under `/Users/nnandal/Documents/code/hockey-stats-runs/features-03k-20261009/corpora/final2/`:

| season / manifest | sha256 |
|---|---|
| `20232024/corpus.json` | `53bc6d0db228a366ab797e135e708b310c869e16cea6f96bfc2b0c22f920a16a` |
| `20242025/corpus.json` | `9c8061e15fc7991a07db3b041915b13d0bcfdf6f5f1429ae1e076120d8d29c3a` |
| `20252026/corpus.json` | `6a8ba483744061951e33164e5b7f5a05de82886cea37fba25d80f67b3b7666ae` |

originals remain under `/Users/nnandal/Documents/code/hockey-stats-raw/fresh-20260930`. no acquisition or original rewrite is authorized. execution receipts bind actual consumed game/manifest/selection bytes, current preparation identity, clean implementation, lockfile, both fresh configs, four external cohorts and this immutable protocol. `verification/prefit-freeze.json` is written after software checks and independent prefit reviews and before the first research fit. cohort membership hashes use canonical finite-json serialization of the complete recognized row ledger, as specified; external file identities bind that ledger to components and evaluations.

## predictions and assessment

save full recognized prediction streams. both arms predict included rows. the common-trained baseline also predicts every omitted eligible unblocked assessment row; the candidate preserves those rows with null predictions and exact study reasons. source-excluded and eligible blocked rows retain null predictions and their distinct dispositions. main losses, groups and per-game summaries use included rows only. separate baseline included/omitted losses, goal rates and predicted goal mass describe selection; they do not restore representativeness.

primary: paired sequence-minus-baseline mean goal log loss, in nats per included attempt; lower is better. use stable native log probabilities, without clipping. secondaries: brier score, observed and predicted goals, signed predicted-minus-observed calibration residual in percentage points, and change in absolute pooled residual. preserve unrounded values and relative loss change.

show all twenty half-open own-probability bins, with the last including one, for each arm. paired calibration uses baseline-bin membership for both arms. bin migration is not paired improvement. fixed descriptive groups are recent/none, model type, sequence index `1,2,3,4+`, calendar month, role and baseline-defined shooter/goalie support. no cross-product, subgroup search or nomination. empty groups have null metrics.

per window: 2,000 paired whole-game draws and 2,000 paired draws each over nonoverlapping seven- and fourteen-calendar-day blocks; `PCG64`, seed `3032026`, 95% linear-percentile intervals. identical sampled units are used across arms and metrics. pool additive sums and counts, never game means. blocks begin on the earliest selected assessment date and retain empty games, intervening empty days/blocks and the final partial block. any undefined draw makes that interval null; do not redraw. retain contributing game/block counts. these intervals are **conditional on fitted models** and omit fitting, selection and origin uncertainty. descriptive group/bin tables are not simultaneous tests. there is no bootstrap refitting.

## decision and stopping

the prospective arithmetic deadband is `1e-10` nats per row. independently check identical and nearly identical loss arithmetic. this is not a hockey-effect threshold and does not relax optimizer convergence; there is no post-result epsilon.

| condition across both windows | direction |
|---|---|
| any missing, nonconverged or unreconciled cell | `incomplete` |
| both primary point deltas `< -1e-10` | `consistent_direction` |
| neither primary point delta `< -1e-10` | `no_improvement` |
| otherwise | `mixed_direction` |

recommend `research_integration` only for consistent direction, both whole-game upper limits `< -1e-10`, all three interval methods defined in both windows, and neither calendar interval establishing harm (`lower > 1e-10`). otherwise recommend `no_supported_next_fit`. report adverse brier/calibration plainly; they are not retroactive gates. research results are `not_admitted`. fixtures always say `direction:not_assessed,recommendation:fixture_only,scientific_assessment:not_performed` and use explicit bounded chronological selections, not the full scientific count requirements.

after fixture red/green/refactor/green and independent statistical, systems and content review, freeze inputs and run four cells sequentially: development baseline, development sequence, season-transfer baseline, season-transfer sequence. complete both windows regardless of the first scientific direction. numerical/source/resource failure stops remaining expensive work and produces an explicit bounded `incomplete` decision with located failure evidence and stopped-cell reasons. no altered setting, replacement data, recovery engine or silent limit increase. write successful completions last; failed fits retain diagnostics without a successful component or completion.

measure fixture preparation, fit, reload, comparison, peak resident memory and artifact bytes before full fits; retain full costs and completed expensive components. run one preparation/fit process at a time, release arrays between cells, and use exclusive directories outside git/worktrees. final review independently challenges arithmetic, identities, accounting, interpretation and labels. delete all temporary tests and test-only dependencies after verification; preserve useful fixtures, facts and receipts.

## scope and tradeoffs

matching sacrifices coverage and unproved representativeness for an exact feature comparison. four fresh solves cost more than reusing historically different baselines. conditional intervals omit fitting/selection/origin uncertainty and account for neither repeated-season exposure nor all earlier research choices. the four-term package cannot separate index from age. strict changed schemas require fresh components and recorded revisions for historical consumers. correct inactive families remain implemented and incur maintenance without entering these recipes.

no origin/avoidance/direct all-attempt fit, joint em, probability patch, new feature/source, penalty sweep, automatic campaign, player estimate, admission, 04 handoff or publication follows. recorded coordinates and continuity proxies are not verified physical release truth. a negative or uncertain result completes the study; a separately chosen follow-up remains possible.
