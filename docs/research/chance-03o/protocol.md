# 03o observable-conversion decomposition protocol

date: 2026-10-13. status: frozen prospectively after software and independent target/source acceptance, before formal control reuse or research fitting. the user assigned complete implementation and execution of [03o](../../specs/03o-outcome-decomposition.md). the immutable execution copy is `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/inputs/protocol.md`. software exercises use `fixture_exercise`; this bounded study uses `research`.

## question and estimand

does separately modeling recorded net-hitting and scoring improve later recorded-goal probabilities on source-eligible unblocked 5v5 attempts under the selected short history?

`q(x)=p(on_net|unblocked,x)`; `g(x)=p(goal|on_net,x)`; `p(goal|unblocked,x)=q(x)*g(x)`. goal implies recorded on-net, so this identity requires no independence assumption. both native stages predict EVERY eligible unblocked assessment attempt, including observed misses. actual on-net status determines training and diagnostic target applicability; it never replaces a probability, gates either prediction or enters a predictor.

`x` retains recorded location, six model shot types, native circumstances, shooters and goalies. this is a retrospective probability check on recorded attempts, without physical-origin accuracy, causal isolation or a live pre-release forecasting claim. retain existing tip/deflection attribution, geometry and annual borrowing. tip-shooter masking, mirror pooling and further layers remain separate experiments. a negative, mixed or inconclusive finding completes this developmental study without admitting a model.

## immutable evidence and fixed masks

use only the four original schema-2 03n short selections below, at their original paths, with `purpose='research'` and `history_corpora=[]`. no observations enter, no source is recaptured, and no historical path or verdict changes. corpus-season order and native within-corpus game/source order remain exact. all selected games remain in the date ledger, including zero-contribution games. within each window, training and assessment games are disjoint and every assessment date follows every training date.

original selection root: `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/`.

| selection | actual sha256 |
|---|---|
| `development-short-training.json` | `c4b8918f44a88a0bdbc53ed9bfd37f196850cf18823a44e6dbe752118532de5a` |
| `development-assessment.json` | `30a6e0ae1338e2b68a8d89101d8e0b5e537ee6c4357f78ca5f7a5974aea32791` |
| `season_transfer-short-training.json` | `7b78ea4aaa7bbf0afa7c9f94bd8f54ffeabca51b45a079fe44e293b0a1627db9` |
| `season_transfer-assessment.json` | `c99b1e8e43b6d807f3ea326cd87b0e3843fe11ff8da7d601c14a31cc91965905` |

training development uses all 2023–24 plus 2024–25 games before `2025-01-01`; assessment uses the rest of 2024–25. transfer trains on all 2023–24/2024–25 and assesses all 2025–26. both windows are research-exposed; they overlap in training and development assessment later enters transfer training. they do not provide independent confirmation.

selected manifests are `/Volumes/Expansion/hockey-stats/corpora/03m-20261010/<season>/corpus.json`. admitted 03m provenance remains unchanged. target cohorts bind actual selection, manifests and game-envelope bytes. research evidence stays at those original paths.

| season | actual manifest sha256 |
|---|---|
| `20232024` | `92392c80b145d72c3be759a94b8113db04a7e8d26a4404e1e15a40119db6a414` |
| `20242025` | `46208ef0830949de4faf1e6695f052c9fdbc23bca5b86fa045c3552d3d467639` |
| `20252026` | `8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43` |

source `out_of_scope|unavailable` stays excluded regardless of event class. eligible unsupported classes or disagreements among `source_event.type_key,blocked,goal` cause a located failure, never a new omission. retain unavailable coverage as null; zero represented attempts do not assert complete source coverage. unresolved source membership, coordinate frames, shot-type recording and unavailable observations remain limitations. no sequence-completeness filter, elapsed-time requirement, new feature, longer horizon, recency weighting or source re-admission applies.

## literal targets and measured denominators

let `U` denote source-eligible unblocked attempts, `O` recorded on-net attempts and `G` goals. saved means the recorded non-goal `shot-on-goal` class; it does not distinguish frozen, rebound or in-play outcomes.

| literal source class | recorded `on_net` | q target: `unblocked_on_net` | g target: `on_net_conversion` |
|---|---|---|---|
| `missed-shot` | false | false | not applicable |
| `shot-on-goal` | true | true | false |
| `goal` | true | true | true |
| `blocked-shot` | null | not applicable | not applicable |

full original-fixture `feature_facts.outcome.values.on_net` independently agrees with this literal mapping. research uses `prepare_core` and does not materialize full or future-event feature facts. source `goal` and native goal audits remain unchanged; numerical setup keeps source `data.goal` and an explicit float64 `data.target`. no temporary goal relabeling or synthetic observation enters any source artifact.

| partition | games | U | O | miss | saved | G |
|---|---:|---:|---:|---:|---:|---:|
| development short training | 1,912 | 128,679 | 87,618 | 41,061 | 80,004 | 7,614 |
| development assessment | 712 | 49,014 | 31,658 | 17,356 | 28,854 | 2,804 |
| season-transfer short training | 2,624 | 177,693 | 119,276 | 58,417 | 108,858 | 10,418 |
| season-transfer assessment | 1,312 | 87,018 | 56,111 | 30,907 | 50,820 | 5,291 |

before this freeze, original source event classes were joined independently to immutable 03n source dispositions, without new target or prediction code. receipt: `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/receipts/independent-source-counts.json`, sha256 `3d8bde05819c05c562c05b02485b41decc5c8f4404a2258e62bef89db847a6d0`. it retains exact per-game and per-season class/source counts and zero-contribution games. each partition satisfies `U=miss+saved+G` and `O=saved+G`.

independent season reconciliation: 2023–24 contributes `O=61,143,G=5,266`; 2024–25 contributes `O=58,133,G=5,152`, split into training `O=26,475,G=2,348` and assessment `O=31,658,G=2,804`; 2025–26 contributes `O=56,111,G=5,291`. transfer O therefore equals `61,143+58,133=119,276` training and `56,111` assessment, agreeing with 03m's source-eligible `goal|shot-on-goal` season counts. overlapping partitions are not summed as a league total.

eight schema-1 target cohorts use `definition={mode:'all_source_eligible',required_families:[]}`. q includes U. g includes O and marks eligible misses and blocks `not_applicable`. all recognized keys and source dispositions survive in native order; there are no feature omissions. this membership is target-applicability based, not universally outcome-blind, and no prediction or model output selects it. q positive keys must exactly equal g included keys; both target outcomes must exist in each stage's training window. schema-1 target audits bind actual source counts and selection/cohort identities, rather than merely matching one another's summaries.

## frozen stage-cohort identities

all paths below are relative to `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/`. every stage row binds the actual `cohorts/<partition>/<quantity>/{cohort,outcome_audit,target_audit}.json` bytes.

| partition / quantity | cohort sha256 | source-goal outcome audit sha256 | target audit sha256 |
|---|---|---|---|
| `development-training/unblocked_on_net` | `f3593763bd13b92cc7e6fdd003cf65dcf1521263817b61d1ce67dae50aea5d71` | `3841bc62a6377c1d7100ff57ee3e582212336ebfbfec70e3fab69c4a8f3a4405` | `b2de4ae090b21839e5b668acb4a69a12217fc622a1483c177ebfda4a1746b89b` |
| `development-training/on_net_conversion` | `14e9898b0c00f9f8dd8f5c4578617ac345860e0c8bedba98b2460611b96edb1d` | `775f81235dfc1439303ee1ff4fb26bdc4f05ee04f7e7042320a3293051eaac64` | `c0d506bf7279c17996a000cb5843f060367c26a0560bb83b9dd38bb46527a4a1` |
| `development-assessment/unblocked_on_net` | `24190db5e5223851ab3e46c43bef37bba6157732aea7fa3ff9a4a1a5202e882b` | `97983dd3b9a5729cd5c741f04258c6a5407adcc50533d9e75d262490dcdc796f` | `de7990504aaeeabdb7498573c862dc744978098a45bceed779c23e56bc31425c` |
| `development-assessment/on_net_conversion` | `d8f6ac70d53dcc5389c4b330767294cb7d38fdb3dcc109c5afd0055228194fd5` | `12004db20e629c376658c09d684ef89928b95e5502a5315ac5738895fa251244` | `44014b4d8073998b605c1e70b706af6febef8da64393c69691e43525fae12222` |
| `season_transfer-training/unblocked_on_net` | `f4e73e380cf21d08ca45028f5a7675b75825ee034d9d2226e36d22bc5c761f30` | `9d0d1e715c20e2dcd99f8a595c65953d1718e1b808f0be25f426e00614b5f013` | `d854e61ae45d2b178ab3595ca8bd0c0950e6f6f9a433467818906f6dcd1f06c0` |
| `season_transfer-training/on_net_conversion` | `5e9faf89b627b048c27c918412569b732744858b52fc56cbe4a5dad26cdb9d2d` | `c29887afe31ee578d8d96483da24534b07709e7a5d6117b4b169c7949492428a` | `7a04b6f3dcd7f75a6843ea2478023ab52ea0639bbbad039e7c26640fd7d02009` |
| `season_transfer-assessment/unblocked_on_net` | `9f361067cbc725bbb8b276ebbc75ec8186cf0d8bcbd049ebcc3988cb53352573` | `011372a1c1f0078876ae8a18d0215472e33c3cb518b2fa519252500ab695601c` | `f27a44a6bea60f5abf68959cd1554a7092984d148bd4e09eb9beef1df1b6dcb3` |
| `season_transfer-assessment/on_net_conversion` | `362497d8afe3aaee405a6c2c2a11d1ee6a7dd3b5cd58444afb8a87c5064e70fb` | `d2172126082463561f929c8659a360407be30d738eee7b34befdbd04e508900a` | `f0afefc1aa816ff42ce483a162650b256a54c0c52b507aa44142c0d550fdca0c` |

| protocol-free cohort completion | actual sha256 | actual clean preparation implementation |
|---|---|---|
| `cohorts/development-training/completion.json` | `72650467e70f22cf4469a2cc7468e42bb645d3c6f6759e8faa8b29ba92f39c69` | `e3ebb5df7ec9e025475d5b956bc6505b4957b88c` |
| `cohorts/development-assessment/completion.json` | `aabb8effba18ecd7b7bf32c9d8c40bd11eededa379060484450a5f40be59c4dd` | `e3ebb5df7ec9e025475d5b956bc6505b4957b88c` |
| `cohorts/season_transfer-training/completion.json` | `2ce4f9f47fdc04099e980824a86b2df69afbaf23d6c112f42b15ad3210a3a5a1` | `e3ebb5df7ec9e025475d5b956bc6505b4957b88c` |
| `cohorts/season_transfer-assessment/completion.json` | `d4415e184f9e3d247667317eb117e676304ee5fa0cef4cbd5b656becf00d7b59` | `cdd46f9b1bd894298d4057969948973176dc0ea6` |

the first three partition completions retain their actual clean `e3ebb5df7ec9e025475d5b956bc6505b4957b88c` preparation provenance; transfer assessment retains `cdd46f9b1bd894298d4057969948973176dc0ea6`. native source/target/cohort owners and their byte hashes are identical across these commits. the later prospective change only repairs product-complement arithmetic and clarifies the assigned specification; it changes no target, selection, membership, source outcome, fit objective or decision rule. completed source artifacts are not restamped.

prefit reconciliation receipt: `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/receipts/target-prefit-reconciliation.json`, sha256 `0c4dce59af69359e58f04e8ea42b8f5186c4c976ff16c3f1e45a9f1e1a31163f`. status is `pass`. it binds the independent original-source receipt and all eight actual target audits, reconciling per-game/season class counts, original dispositions, U/O/G, included target positives/negatives and source goal counts. this is target/source acceptance before any fitting, without empirical gain or admission.

## immutable direct controls and reuse inputs

reuse BOTH 03n `short` cells; do not select winners or subgroups. original source result: `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/report/result.json`, sha256 `7f846890843811a10386f5da40818ac0e914ac27436d8e29678f3a91e3cfc123`.

this protocol freezes `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/inputs/reuse.json`, sha256 `8220448b5c05e90239ffed073c13c4c74679d28f75c927cf29db723679a03333`. that schema-1 INPUT binds the original result, unchanged config, both original fit/evaluation completions and all four original selections/cohorts. the later reuse receipt binds this protocol; the protocol does not bind that future receipt, avoiding a cycle.

controls retain their original protocol `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/protocol.md`, sha256 `83473150503f9ed70af5e9fb711b21cdb198d4733acade4efa6a124aebbd0a06`; original implementation `21744af5c5bc33f7341d2e15d54145540416f687`, `git_dirty=false`; python `3.14.8`, numpy `2.5.3`, scipy `1.18.1`; original lockfile sha256 `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`. do not restamp original artifacts as 03o.

all paths in the following table are relative to `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/`.

| original direct binding | development actual sha256 | season-transfer actual sha256 |
|---|---|---|
| `fits/<window>/short/completion.json` | `f22920e2112b414ffb423521910a729f6ff2412f6f9494e4e472d5725f5f6032` | `87a0f4744dcf1756916464eafe55d2c7a1bfc15e49b46d4968800f7b0a9fbf8d` |
| `fits/<window>/short/fit.json` | `19e0a9432d6ec153d7d56ba68a048eeb5aacc316f9ee4958cf428aca5af4d1f2` | `4d3dae411ab0389499e2390c6e05de73ac9c0c3a92ccf0d380fe5470b6acb249` |
| `fits/<window>/short/component.json` | `30bebc464a4aa20a65a3da96eb83adb8c2bafe60f4956303d04e69bb487d0506` | `7065a95db4d562fa1518392e3f396c12d081a03389a458cfa1692ed430a234a9` |
| `evaluations/<window>/short/completion.json` | `5be46eed91a043abf078a61d35251db8c109833aed230880f1fbb9966c44bb83` | `fa5adaa3b92aefbbdc74b7fd2eae7934408d4c9c9995a19326715c402193aa5b` |
| `evaluations/<window>/short/evaluation.json` | `772d19469fe46273626f726e9a31266daeaea1833bfada7e9d72ee5c5d878a57` | `f7f8d8a98dc8a9f20086ad8152c993a2d7e2ea95ee740782a874eb3841e97b81` |
| `evaluations/<window>/short/attempts.jsonl` | `2fdb9cc113d00989a39fb27fd9da90781044b5827c7af35a7611b1cbf4c4e8fd` | `619bbe570c588dd4ca855c7d5a72435bcdc57a49699dabf1c8ec88cad20c15c4` |
| `cohorts/<window>-short-training/cohort.json` | `5dca3168cd63206190e1d04c15ce7478243d25e7ea2de86db035e3d78b35a6b2` | `d9c182341308e74c0fb726c1561765c4ae5356920bf84247f9c0f2e9cdcb1dcc` |
| `cohorts/<window>-assessment/cohort.json` | `f5366725f8e0ee8d5703d479444b94f0cc09a34a5762cd13b2d239bf2ab4a0c6` | `c2b09c06f5379b6aaa16ec5821f2a52046a7463494a195a37d6862a236f36ebf` |
| `report/verification-<window>-short.json` | `69638b433054b2c971d334316e87eec99d03317cbccb02b382e5ba583c3cf68a` | `0434a8de12337413e69d51d009d1cd8759d30238520a4747a2e58d435d9afcba` |

formal prefit reuse validates the original binding chains, exact selection/source/order/labels/cohort/design/numerical-contract equivalence under extended code, q/direct layout and actor-count agreement, and source-goal preservation. replay each saved direct objective ONCE through shared native setup with `agrees(rel_tol=1e-10,abs_tol=1e-10)`, then reproduce saved direct predictions within native row tolerances. exact keys, dispositions, source descriptors, annual basis, actor support and aggregate sums must agree. verification receipts remain separate from compact components. missing or mismatched evidence stops with a concrete issue; there is no try-reuse-else-refit path. new direct controls require a revised protocol and assignment.

## clean software and unchanged recipe

frozen production commit: `cdd46f9b1bd894298d4057969948973176dc0ea6`, with clean analysis implementation. no production change or commit occurs between protocol freeze and the completed report. runtime: python `3.14.8`, numpy `2.5.3`, scipy `1.18.1`, matplotlib `3.11.2`, beautifulsoup4 `4.14.3`. `analysis/uv.lock` remains sha256 `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`; no test-only dependency is introduced.

| production file | actual sha256 |
|---|---|
| `analysis/pyproject.toml` | `69ecf922d418e5e8f4734f74f8f46a0a55e07dde9e5de5a09b3d9fcb47493dd8` |
| `analysis/src/hockey_stats/chance_targets.py` | `21a27fd66acea333ae78ac3c4d70e30748f4e3de5a106ad919f0f101af7bdc51` |
| `analysis/src/hockey_stats/chance_cohort.py` | `41cc70a76fc6de5495c56b99e1919936acb55c3e38e7a734fb78e3208ff91059` |
| `analysis/src/hockey_stats/chance.py` | `6a28019b903615bdfc97e82980e835a5437eeaa2e896eb288644239e5bfd4042` |
| `analysis/src/hockey_stats/chance_data.py` | `dfc0d3cf85a327c48259b7fb2bf1573b5385eed3786527550b0e1c70c0b37cc6` |
| `analysis/src/hockey_stats/chance_evaluation.py` | `bfdbb4422b2e2a6c59459a89ea111b62b45f347c624781b41aac442cb7d53bd0` |
| `analysis/research/chance_development.py` | `a191d1dc51680e2f0285b5907706edb499e82aceb9ce6783c3ebd86756d2c651` |
| `analysis/research/chance_history.py` | `3d81596a8c7cffd6adf0c95ab8cd3aa7169a0f0a3327a6722dbb7d74f9f4009a` |
| `analysis/research/chance_decomposition.py` | `897240ed817266cc021c84f554efbc0d63e1ffcddf50e3fe6fdf621ca37bd4c5` |
| `analysis/uv.lock` | `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd` |
| `docs/specs/03o-outcome-decomposition.md` | `9d478287ab822b35ddd0cfc50ed83d7f4aa0135e74a8417eec4abf18693f91a3` |

unchanged `PREPARATION_IDENTITY` is `{version:'features-03k-1',selection_schema:2,corpus_schema:2,reference_schema:2,interpretation_schema:4}`. core preparation preserves the same source projection and identity, omitting inactive feature/history materialization. full preparation and every supported inactive extraction remain available. cohorts remain schema 1; native config/component/fit/completion artifacts remain schema 3 and selections schema 2. new study completions use schema 1. new component quantities are active standalone targets, not joint-em layers or compatibility artifacts. illicit extraction/integration of these layers through a joint model fails.

one byte-unchanged schema-3 config serves all four fresh cells: `/Volumes/Expansion/hockey-stats/runs/chance-03n-20261013/inputs/config.json`, sha256 `1a52e1bbb5d9ef736b6781c18cfa66bf3c869817c6da8b6e9d9c741b417c1bf2`. q and g both use native layout `r`, exactly `game_additive,recent_additive,recent_interactions` in canonical order, all 65 circumstances and `trait_assumptions=[]`. inactive `origin,u,unblocked,all_attempt` declarations remain `game_additive,recent_additive`; they do not authorize fitting. absent sequence facts stay `not_prepared`; no sequence subgroup diagnosis follows.

| exact config fields | values |
|---|---|
| `kernel_distance_ft,kernel_direction_strength` | `20,4` |
| `ridge_origin_base,ridge_cell,ridge_benchmark` | `.25,.25,.25` |
| `ridge_origin_factor,ridge_type_cell` | `1,1` |
| `smooth_origin,smooth_cell,ridge_context` | `4,4,4` |
| `ridge_shooter,change_shooter,ridge_goalie,change_goalie` | `4,16,16,64` |
| `optimizer_max_iterations,optimizer_ftol,optimizer_gtol` | `2000,1e-10,1e-6` |
| `em_max_iterations,em_relative_tolerance,em_posterior_tolerance,objective_decrease_tolerance` | `2000,1e-8,1e-6,1e-10` |

## four native fits and their meaning

fresh cells are `development/unblocked_on_net`, `development/on_net_conversion`, `season_transfer/unblocked_on_net`, `season_transfer/on_net_conversion`. each gets a separate coefficient set, actor counts and solve. each solve uses its own empirical-intercept initialization, without shared coefficients or a warm start. no extra initialization, saved offset or post-result fit is permitted. all coefficients start zero except each included population's empirical positive-target log-odds intercept: q uses `log(O/(U-O))`; g uses `log(G/(O-G))`.

both layouts preserve the native 656-cell grid, native type-cell maps, geometry/context transforms, shooters/goalies and complete selected annual state domain `20232024,20242025`. earliest selected season `20232024` is the offset reference even if an annual state has no applicable evidence. q and direct counts/layouts agree; g's counts reflect only O. development assessment uses fitted 2024–25 states; transfer 2025–26 carries latest fitted 2024–25 season/actor states. unseen actor residuals are zero; observed-only-in-other-seasons actors may have applied states inferred through annual penalties. preserve `season_basis,state_season,actor_evidence` and each stage's own support counts. nuisance actor logits are not player ability cards.

use summed binary negative log likelihood and unchanged penalties: unpenalized intercept; cell ridge `.25`, type-cell ridge `1`, neighbor smoothness `4`, context/season ridge `4`; shooter level/change `4/16`; goalie level/change `16/64`. one shared spatial-binomial objective receives the explicit response. original direct and benchmark objectives retain their unchanged source-goal responses. no likelihood normalization, new penalty, recency transform or gradient gate is introduced.

native `L-BFGS-B` success, finite coefficients and finite objective are required, with maximum 2,000 iterations, `ftol=1e-10`, `gtol=1e-6`. relative-objective stopping may occur before gradient tolerance. disclose actual termination and maximum absolute gradient; no tighter restart or extra solve follows. replay each NEW saved fit objective ONCE during report verification through the same setup/target/objective using `agrees(rel_tol=1e-10,abs_tol=1e-10)`. bind source, design, component, saved/replayed objective, difference and gradient maximum in receipts outside compact components.

q and g optimize separate binary likelihoods on richer miss/saved/goal classifications. their summed training losses do not compete with direct binary goal loss. two coefficient sets and g's smaller fitting population change effective shrinkage under fixed penalties; this compares an estimator package, without causal isolation of factorization.

## complete prediction and scoring domains

write both numerical stage predictions on every U row, including misses. stage g has `metric_applicable=false,observed=null` on a miss while retaining its prediction, annual basis and own actor evidence. eligible blocks have `status='not_applicable'`; source exclusions retain `out_of_scope|unavailable`. outside U, stage observations/numerical/basis fields and composed goal are null. source `goal` and literal raw `on_net` remain source facts. source-only descriptors use native `diagnostic_groups(attempt,game_date,{})`; do not invent combined actor support.

compose `log_p=log_q+log_g`. for `log_p<=-log(2)`, evaluate its complement with `log_not_p=log1p(-exp(log_p))`; otherwise use `log_not_p=logaddexp(log_not_q,log_q+log_not_g)`. these are exact binary identities with deterministic numerical regions: the lower-half form keeps extremely small products' complement logs nonpositive; the stage-complement form preserves finite near-certainty tails even when the product probability rounds to one. this prospective arithmetic repair was independently checked before any research fit; masks, objectives, solvers and decision rules remain unchanged. no rounded probability-product/complement arithmetic, clipping, failed-call fallback, division of direct probabilities to invent g or actual-outcome substitution applies.

three explicit metrics use populations U/O/U: q-on-U is `on_net`; g-on-O is `goal_given_on_net`; the product on U is `composed_goal`. q and g losses, own bins and own actor-support groups are descriptive on their own target populations. composed-own groups omit actor support. no stage score ranking, stage-loss comparison with direct or new calibration-admission gate follows.

report validation rejoins actual source bytes, full ordered keys, individual raw labels/dispositions/descriptors and saved stage coefficients/basis/support before reconciling every metric/group/game sum. mutually matching but false prediction streams must fail. pairing requires exact entire U order and coverage; do not intersect surviving rows or compare O against U.

## paired arithmetic and prospective decision

primary: decomposed minus direct mean GOAL log loss, nats per eligible unblocked assessment attempt; negative favors decomposition. secondaries: brier, observed/predicted goals, signed pooled predicted-minus-observed residual in percentage points and change in absolute pooled residual. retain full precision, magnitude, denominators and contrary secondary evidence.

retain twenty own-arm goal probability bins and twenty paired bins defined by DIRECT probabilities; bins are left-closed/right-open except the final bin includes one. direct defines paired groups `recent_context,model_type,calendar_month,role,actor_support:shooter,actor_support:goalie`. each stage retains its own target-population bin/support summaries separately. no subgroup gates, support-transition search or added diagnosis campaign applies. sequence diagnostics remain `not_prepared`.

per window, draw 2,000 paired whole-game samples and 2,000 samples for each nonoverlapping seven-/fourteen-calendar-day block method. use `PCG64`, seed `3032026`, linear 95% percentiles. identical sampled units feed both arms and all metrics. use pooled sums/counts, retaining empty games, intervening empty blocks and the final partial block from the earliest assessment date. undefined draws produce null intervals without redraw. there are 12,000 draws and ZERO bootstrap fits. intervals condition on the two reused direct controls and four fresh stage fits; they omit fitting, selection and source uncertainty.

arithmetic deadband: `d=1e-10` nats/attempt. this is neither solver uncertainty, a hockey-effect threshold nor a useful-effect guarantee. symmetric, undefined and near-identity software checks establish the arithmetic before fitting and do not license changed gates afterward.

| both-window primary condition | direction |
|---|---|
| missing/nonconverged/unreconciled cell or undefined primary point | `incomplete` |
| both deltas `< -d` | `decomposed_direction` |
| both deltas `> d` | `direct_direction` |
| both deltas within `[-d,d]` | `within_arithmetic_deadband` |
| otherwise | `mixed_direction` |

nominate decomposed only for `decomposed_direction`, with both whole-game upper bounds `< -d`, all three interval methods are defined in both windows and no calendar lower bound is `> d`. symmetrically nominate direct only for `direct_direction`, with both whole-game lower bounds `> d`, all methods are defined and no calendar upper bound is `< -d`. supported cases say `supported_representation`; otherwise `no_supported_representation` with null nomination. all research results remain `not_admitted`; native artifacts say `scientific_assessment='not_performed'`. fixtures always say `not_assessed,fixture_only,null,not_performed` and need neither the hdd nor research counts/nomination.

no gain or accepted final model is required. incomplete execution is not a negative scientific result or a completed study. no automatic representation adoption, native integration, blocked-origin model, joint em, final fit, player estimate, 04 handoff, publication or peer-model-parity claim follows. later opportunity reference standardization must average the PRODUCT over one shared joint actor reference; multiplying separately averaged layers is generally wrong. record that contract now and implement it only under later assignment.

## manual operation, stop order and closure

run explicit manual commands from `analysis/` with `.venv/bin/python research/chance_decomposition.py`. flags require exact paths, no repeats or abbreviations; outputs are new exclusive directories outside input parents. syntax failures return 2, input/numerical/i/o failures 1, help/success 0. successful completion files are written last; failed native fits retain diagnostics without a successful component/completion.

canonical order after the frozen protocol: formal reuse proof; development q fit → g fit → assessment; season-transfer q fit → g fit → assessment; report, including one objective replay per NEW saved fit. any source, numerical or i/o failure stops later expensive cells in this order. scientific direction does not stop the second window. a declared incomplete report is valid operational evidence, without an empirical rejection or completion claim. no replacement controls or extra cells are scheduled.

all real outputs are external-only under `/Volumes/Expansion/hockey-stats/runs/chance-03o-20261013/`, with sibling `inputs/`, `cohorts/<partition>/<quantity>/`, `reuse/`, `fits/<window>/<quantity>/`, `assessments/<window>/`, `report/`, `receipts/`. preserve frozen paths and expensive completed fits. ordinary mount/path/expected-input/i/o checks suffice. the user accepts manual rerun risk after interruption; an interrupted cell restarts manually into a fresh explicit output directory after ordinary input validation. no local fit copy, special drive safeguard, physical-cause gate, acquisition, vm, retry/checkpoint engine or runner applies.

03n already measured a larger 5,248-game native setup. this study has at most 2,624 training games/177,693 U rows with the same compact basis. do not repeat that capacity campaign without newly demonstrated materialization. measure each command/fit's final wall time, peak rss and footprint. process windows/stages sequentially and release preparation/arrays between them; no dense attempts × all-coefficients matrix or new cache/storage framework is permitted.

before fitting: temporary original-fixture red → green → refactor → green; independent source/full-fact target agreement, preserved direct objective/predictions, q/direct design/counts, g target/intercept/counts, gradients, complete grids/annual support, miss prediction/no outcome leakage, illicit joint extraction, extreme-log arithmetic, full ordered source/label/digest/basis reconstruction, U/O/U scores, paired bins/all interval methods and symmetric/undefined decisions. adversarial source/numerical/content review supports the clean code/input/config/cohort/protocol freeze; the narrow prospective complement repair and its independent closure must pass before expensive fits. formal control reuse precedes every new fit. after fitting: independently reconcile the complete source, saved objectives, full-population arithmetic, figures/content and decision, then delete temporary tests/controllers/bytecode/test-only dependencies. retain useful scientific commands, factual receipts, unchanged original fixtures and expensive outputs. concrete unresolved issues belong in `docs/issues/`.

tradeoffs: richer labels buy two maps/coefficient sets and smaller g support with changed effective shrinkage; g extrapolates to actual misses under recorded input limitations; exact reuse saves two expensive fits while depending on original hdd artifacts and strict compatibility; conditional intervals omit refitting/selection/source uncertainty; current tip treatment isolates this comparison while deferring a published refinement; external-only writes accept lost interrupted work. none changes the prospective acceptance or decision rules.
