# 03n training-history comparison protocol

date: 2026-10-13. status: frozen after software and independent prefit review, before capacity or research fitting. the user assigned complete implementation and execution of [03n](../../specs/03n-history-comparison.md). the immutable execution copy lives under `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/protocol.md`. software exercises are `fixture_exercise`; the bounded scientific study is `research`.

## question and population

does adding complete 2021–22/2022–23 observations improve later recorded goal probabilities on source-eligible unblocked 5v5 attempts under the unchanged native direct-conversion estimator? this compares estimator horizons, not an isolated sample-size intervention. negative or inconclusive evidence completes the study without admitting a model.

all recognized source rows and every selected game survive, in explicit corpus-season order and `(game_date,game_id)` order within each corpus. source `out_of_scope|unavailable` stays source-excluded; eligible blocks are not applicable. all eligible unblocked rows are included. no sequence filter, feature omissions, elapsed-time denominator, recency weighting, new covariate or re-admission campaign applies. failed active encoding stops execution. source uncertainty and 03m's unresolved membership, frames, 2,601 unavailable recognized rows and one unknown overtime horizon remain.

| partition | games | applicable unblocked attempts | goals |
|---|---:|---:|---:|
| development short training | 1,912 | 128,679 | 7,614 |
| development expanded training | 4,536 | 306,041 | 18,471 |
| development common assessment | 712 | 49,014 | 2,804 |
| season-transfer short training | 2,624 | 177,693 | 10,418 |
| season-transfer expanded training | 5,248 | 355,055 | 21,275 |
| season-transfer common assessment | 1,312 | 87,018 | 5,291 |

short development trains on all 2023–24 and 2024–25 before `2025-01-01`; assessment uses the remainder of 2024–25. short transfer trains on all 2023–24/2024–25 and assesses all 2025–26. expanded training adds all 2021–22/2022–23 to each short window. selected training and assessment ids are disjoint and all assessment dates follow all training dates. every training cohort contains both outcomes. the five distinct seasons reconcile to 442,073 applicable attempts / 26,566 goals; overlapping windows do not form a league total. these are research-exposed chronological checks, with development assessment later becoming transfer training, not independent confirmation.

## evidence and immutable inputs

bound 03m selection: `/Volumes/Expansion/hockey-stats/runs/03m-20261010-03/inputs/selection.json`, sha256 `2e924d8ca08c4bd1191d4b3f9bfccbd4f795f8bc6283d39b5aed3c81c579bdac`. bound final audit: its sibling `audit/admission-audit.json`, sha256 `78d4034971e8d781ceb5dfa6af56b64ffb423e368027dc9c08a6701a4540b6d6`. actual bytes and all five manifest identities have been verified before input construction. native preparation will bind all consumed manifests, game envelopes and original source receipts/bodies. no original path or historical study changes.

2021–22 manifest: `/Volumes/Expansion/hockey-stats/corpora/03m-20261010-02/20212022/corpus.json`. the other four manifests: `/Volumes/Expansion/hockey-stats/corpora/03m-20261010/<season>/corpus.json`.

| season | actual manifest sha256 |
|---|---|
| `20212022` | `30eb12b290ccd9af9eae7ade8c7dcd5f285129b52b646eec3fced3e2628badc8` |
| `20222023` | `735c741115725e7c4fe8a28782f352c787895db5eea2123b2b7ec27b4db1e02a` |
| `20232024` | `92392c80b145d72c3be759a94b8113db04a7e8d26a4404e1e15a40119db6a414` |
| `20242025` | `46208ef0830949de4faf1e6695f052c9fdbc23bca5b86fa045c3552d3d467639` |
| `20252026` | `8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43` |

all six explicit schema-2 selections live under the execution root's `inputs/`, with `purpose='research'`, `history_corpora=[]` and older observations in likelihood `corpora`. all six schema-1 cohort files have `quantity='unblocked_conversion'` and `definition={mode:'all_source_eligible',required_families:[]}`. cohort rows carry keys/source/study disposition; labels remain in source/prediction rows and reconcile through separate `outcome_audit.json` files.

| input selection | sha256 |
|---|---|
| `development-short-training.json` | `c4b8918f44a88a0bdbc53ed9bfd37f196850cf18823a44e6dbe752118532de5a` |
| `development-expanded-training.json` | `f1b37a89d1908d56696cd172f86787fabaa98bad114bf0eaf42ada702088026b` |
| `development-assessment.json` | `30a6e0ae1338e2b68a8d89101d8e0b5e537ee6c4357f78ca5f7a5974aea32791` |
| `season_transfer-short-training.json` | `7b78ea4aaa7bbf0afa7c9f94bd8f54ffeabca51b45a079fe44e293b0a1627db9` |
| `season_transfer-expanded-training.json` | `2310b6d9901d748f53ffa9aff47c18c53355d4c526d4056dc37c2c83c2d60410` |
| `season_transfer-assessment.json` | `c99b1e8e43b6d807f3ea326cd87b0e3843fe11ff8da7d601c14a31cc91965905` |

## software and recipe freeze

clean implementation commit: `21744af5c5bc33f7341d2e15d54145540416f687`. python `3.14.8`, numpy `2.5.3`, scipy `1.18.1`. `receipts/prefit-freeze.json` binds all tracked analysis files, six selections, the same config, source bindings and independent reviews before any research fitting. no commit occurs between this freeze and the report.

| production file | sha256 |
|---|---|
| `analysis/pyproject.toml` | `69ecf922d418e5e8f4734f74f8f46a0a55e07dde9e5de5a09b3d9fcb47493dd8` |
| `analysis/research/chance_development.py` | `3351824eff2c9393cc22e657e4506c73104df67610fc3f99a7a6e941e01ed18e` |
| `analysis/research/chance_history.py` | `5f473b9e190ad5fe1a527e3e9b0515984c1f2061bba6982f1a6537f3157deae1` |
| `analysis/src/hockey_stats/chance.py` | `db1b4c3e62795890a34e255088b9e917f5341bc6a15788f95b25c36a7b13ac78` |
| `analysis/src/hockey_stats/chance_data.py` | `dfc0d3cf85a327c48259b7fb2bf1573b5385eed3786527550b0e1c70c0b37cc6` |
| `analysis/uv.lock` | `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd` |

execution config: `inputs/config.json`, sha256 `1a52e1bbb5d9ef736b6781c18cfa66bf3c869817c6da8b6e9d9c741b417c1bf2`. unchanged native preparation identity: `receipts/preparation-identity.json`, sha256 `66528246b6df7a6261d7affd68d74a609101dc5dfccfcdb5ba27ed53479619d1`. the exact immutable execution protocol's identity is bound by each artifact. acceptance and thresholds remain the assigned specification.

## numerical recipe and meaning

one schema-3 config serves all four cells. `trait_assumptions=[]`; `r` families are exactly `game_additive,recent_additive,recent_interactions`, in canonical order. inactive `origin,u,unblocked,all_attempt` declare `game_additive,recent_additive`, without fitting permission. no retained feature capability is removed. core preparation omits inactive feature/history materialization without changing `PREPARATION_IDENTITY`; full preparation remains available. `sequence_index=null` is retained solely as native reconciliation bookkeeping, with diagnostic scope `not_prepared` and no displayed sequence comparison.

| fields | values |
|---|---|
| `kernel_distance_ft,kernel_direction_strength` | `20,4` |
| `ridge_origin_base,ridge_cell,ridge_benchmark` | `.25,.25,.25` |
| `ridge_origin_factor,ridge_type_cell` | `1,1` |
| `smooth_origin,smooth_cell,ridge_context` | `4,4,4` |
| `ridge_shooter,change_shooter,ridge_goalie,change_goalie` | `4,16,16,64` |
| `optimizer_max_iterations,optimizer_ftol,optimizer_gtol` | `2000,1e-10,1e-6` |
| `em_max_iterations,em_relative_tolerance,em_posterior_tolerance,objective_decrease_tolerance` | `2000,1e-8,1e-6,1e-10` |

all native `r` coefficients are freshly initialized and fitted. all initial coefficients are zero except each training cohort's empirical goal-log-odds intercept. native summed binary negative log likelihood and unchanged penalties apply: unpenalized intercept; season/context ridge; spatial/type ridge and neighbor smoothness; shooter/goalie level penalties and adjacent-year first differences over the complete selected annual-state domain. earliest selected season is the offset reference, including selected years with zero applicable rows. no likelihood normalization preserves effective penalty strength across horizons.

expanded history changes actor support/state dimensions, reference season, borrowing and likelihood-to-penalty balance. it does not implement annual prior propagation or isolate hockey history's causal value. native geometry, six model types, circumstance transforms and actor treatment remain. 2025–26 prediction carries latest fitted 2024–25 season/actor states; unseen actors contribute zero residual, and older-only actors may have latest states inferred through penalties. preserve `season_basis,state_season,actor_evidence` and their count distinctions.

native `L-BFGS-B` success and finite coefficients/objective are required. [scipy's stopping rules](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html) permit relative objective reduction to stop before gradient tolerance. record the actual termination and gradient; no extra starts, tighter post-result solve, silent tolerance change, saved coefficients, offsets or fifth fit. replay each saved objective once through the shared native setup/objective with `agrees(rel_tol=1e-10,abs_tol=1e-10)`; replay is verification, not another solve or gradient gate.

## capacity and manual operation

the full expanded-transfer 5,248-game setup, exact cohort and production recipe run under `/usr/bin/time -l` before any research fit. native capacity performs validation, native layout/encoding/initialization and one objective/gradient evaluation, with no optimizer and no dense attempts × all-coefficients matrix. it writes setup dimensions, allocated-array bytes, empirical intercept, objective, gradient and pre-serialization resource snapshots. final saved bytes are reread.

post-exit `capacity-measurement.json` binds setup and exact timing log/argv/exit/wall/rss/footprint. require exit zero, valid setup and both final peaks ≤ `48*2**30` bytes. setup success alone is not a resource pass. the 48-gib process ceiling leaves a nominal 16-gib allocation margin on the 64-gib host, not a guarantee of free memory: existing docker/editor/browser workloads and compressed pages already occupy the machine. preserve their actual measured starting conditions; no workload is stopped or gate changed. starting host conditions are retained in `receipts/host-before-setup.log`; capacity does not measure full optimized-fit peak. separately estimate native parameter-sized `L-BFGS-B` workspace with stated float/int sizes and default ten correction pairs; do not claim an exact full-process bound.

capacity failure stops expensive work. repair only demonstrated unused/duplicate materialization at its owner, prove numerical equivalence and remeasure. no shrinking selections, altered penalties/convergence, silent hardware change, memory supervisor, auto tuning, cache/storage redesign or runner.

run explicit manual cells in order: development short fit/evaluate; development expanded fit/evaluate; season-transfer short fit/evaluate; season-transfer expanded fit/evaluate; report. source/numerical/resource/i/o failures stop later expensive cells. scientific direction does not stop transfer. successful completions are written last; failed fits retain diagnostics without a component or successful completion. incomplete execution is not empirical rejection or study completion.

all real inputs/outputs are external under the fresh execution root, with sibling `inputs/`, `cohorts/<partition>/`, `capacity/`, `fits/<window>/<arm>/`, `evaluations/<window>/<arm>/`, `report/` and factual `receipts/`. verify ordinary mount/path/expected inputs/output parent before each batch; missing volume or i/o fails normally with no substitute path. user accepts external-only writes and manual rerun risk. preserve completed expensive fits; an interrupted cell would restart into a fresh explicit directory after ordinary input revalidation. no local fit copies, physical-cause gate, drive-interruption exercise, retry/checkpoint engine or acquisition.

## assessment, arithmetic and decision

primary: expanded minus short mean goal log loss, in nats per eligible unblocked assessment attempt; negative favors expanded. use stable native log probabilities without clipping. secondaries: brier, observed/predicted goals, signed pooled predicted-minus-observed residual in percentage points and change in absolute pooled residual. show unrounded deltas/intervals, relative loss change, magnitude and contrary secondary evidence.

retain twenty own-arm half-open calibration bins, with the final bin including one. paired bins use short predictions for common membership. short defines paired actor-support groups; expanded-own groups remain separate. fixed comparison groups: `recent_context,model_type,calendar_month,role,actor_support:shooter,actor_support:goalie`. preserve all nine per-actor support transitions among `observed_in_state,other_seasons_only,unseen`, with applicable counts/goals, descriptively. no subgroup nomination, cross-product search, causal support claim or admission gate.

per window, draw 2,000 whole-game paired samples and 2,000 samples for each nonoverlapping seven-/fourteen-calendar-day block scheme using `PCG64`, seed `3032026`, linear 95% percentiles. use identical sampled units across arms and metrics; pool sums/counts rather than game means. retain empty games/days/intervening blocks and final partial blocks from earliest assessment date. undefined draws yield null intervals without redraw, with contributing-unit counts reported. total 12,000 draws, zero bootstrap fits. intervals condition on the four fitted models and omit fitting/selection/source uncertainty.

arithmetic deadband: `d=1e-10` nats/attempt. independent identity and both signed near-identity tests validate arithmetic before fitting, drawing on [03l's evidence](../chance-03l/verification.md). this is not a hockey-effect threshold, solver-error bound or useful-effect guarantee; it cannot justify new fitting or changed gates after results.

| both-window primary condition | direction |
|---|---|
| missing/nonconverged/unreconciled cell or undefined primary point | `incomplete` |
| both deltas `< -d` | `expanded_direction` |
| both deltas `> d` | `short_direction` |
| both deltas within `[-d,d]` | `within_arithmetic_deadband` |
| otherwise | `mixed_direction` |

nominate expanded only for expanded direction, both whole-game upper bounds `< -d`, all three interval methods defined in both windows and no calendar lower bound `> d`. symmetrically nominate short only for short direction, both game lower bounds `> d`, all methods defined and no calendar upper bound `< -d`. supported cases say `supported_horizon`; otherwise `no_supported_horizon` with null horizon. all research results say `not_admitted`. fixture exercises always say `not_assessed,fixture_only,null,not_performed`; native fit/evaluation artifacts retain `not_performed`.

nomination is conditional developmental evidence, without automatic horizon adoption, model acceptance or 03o execution. an inconclusive result proves neither horizon sufficient. no origin/avoidance/all-attempt fit, joint em, penalty campaign, player estimate, 04 handoff, publication or peer-model parity claim follows.

## review and closure

before fitting: detached original-fixture red/green/refactor/green, independent core/full source and 65-column numerical equivalence, native fixture fit/prediction equivalence, strict malformed/bound/order/label rejection, symmetric decision and independent paired bins/intervals, capacity receipt/exclusive-path failures, then independent systems/statistical/content prefit review and clean code/config/input/protocol freeze. after fitting: full-population and objective reconciliation, independent numerical/source/content review, original fixture integrity and temporary-code/test-dependency deletion. retain useful commands, attributed fixtures, factual receipts and expensive outputs. unresolved concrete issues belong in `docs/issues/`.

tradeoffs: fresh controls cost recomputation; more history changes support/borrowing/shrinkage and may amplify drift; fixed penalties do not fix effective regularization; conditional intervals omit refitting uncertainty; core projection adds one explicit capability without removing inactive features; capacity headroom can require owner-level memory repair; external-only writing can lose an interrupted solve. none changes the prospective rules.
