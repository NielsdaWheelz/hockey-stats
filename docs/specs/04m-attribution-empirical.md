# pr04m — empirical attribution benchmark

status: **implemented and verified under the user’s 2026-10-21 assignment.** [decision](../research/attribution-04m/decision.md) · [verification](../research/attribution-04m/verification.md). the external protocol retains the exact prespecified snapshot. [the plan](../plan.md) owns progression. [model direction](../research/model-direction.md#04m--test-the-current-family-on-recorded-games) owns rationale; completed studies retain their verdicts. this is a research command and report, not a website release or ability handoff.

## target and settled choices

does existing annual borrowing reduce error for **recorded spatial shape in held-out 2025–26 games**, compared with an independent-season fit and training-fitted context alone?

| choice | consequence |
|---|---|
| 2025–26 assessment; preceding four seasons supply history | the intended first profile season, without replication across target seasons |
| one fixed, calendar-spanning approximately 80/20 game split | six fresh shape states; incomplete assessment coverage and uncertainty conditional on this split/fitting |
| diagnostic comparison, no new minimum-gain gate | supported lower/higher error or unresolved direction; no automatic nominee or next model |
| unchanged forty-mode construction, annual carry, covariates and selector | isolates the existing family; limited context and historical assumptions remain |
| saved game moments; paired loss differences | no original-stint replay, absolute regional rmse, stint-level negative-rate frequency or entrant-stint squared-error claim |

the population remains recorded, locatable unblocked attempts during reconstructed genuine 5v5, with matched spatial counts/time, paired team directions and zero-event exposure. this does not cover imputed block origins or establish chance-valued ability. the split matches the season-level product target; this study measures prediction of recorded responses, not underlying ability or a forecast available before those games. all five seasons are research-exposed; new fit-level holdouts are not untouched scientific confirmation.

non-goals: a new prior/selector, age or feature activation, acquisition, volume-model fitting, complete-player-rate validation, simulated recovery, player intervals, nested refits, additional splits, publication or frontend work. prediction cannot resolve prior recovery failures or identify the prior as the sole cause of failure. preserve expensive fits and raw evidence; native commands and external-only outputs suffice.

## bound inputs and partition

research reads the corrected [04b result](../research/attribution-04b/result.json), sha256 `d0c0f6a7af3888cd0d0920d152f322447a984cbc20edac596aa70f60dbb0f2de`, and its named source references only:

| input | identity / use |
|---|---|
| corrected preparation | `/Volumes/Expansion/hockey-stats/runs/attribution-04b-20261015/prepared/prepared.json`, sha256 `fbc40ab798493be6fcc7068ea52eb43831ad725fb89d7a4c87242f689cb7d17b`; five `unblocked_spatial` annual entries, their original reference and grouped-moment archives |
| original preparation | bound `baseline_prepared`, sha256 `b771cdc1784a72cf0db6be47b9eb0f597af542bb9cace1f339ba40002265cd8a`; population, source/coverage and first-season-reference lineage |
| spatial basis | `/Volumes/Expansion/hockey-stats/runs/attribution-04c-20261016/prepared/basis.npz`, file sha256 `67d7ee706f1d8d251cc68a0d22378e67e1961b2ac53fb764bfc0efdff11d43fc`, semantic sha256 `649a49ecba19de5df609d6980d9de76491afa13e9108df0d8e6500659886cc51` |
| game dates | `/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20252026/corpus.json`, sha256 `8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43`; admitted inventory `game_date`, linked by the frozen [04a protocol](../research/attribution-04a/protocol.md) to [03n's manifest](../research/chance-03n/protocol.md) |

verify clean source producers, unchanged paired/spatial masks, ordered ids/axes and every consumed archive hash once per command. reuse corpus validation for dates and selected-array readers. require exact equality of the final grouped inventory and the 1,312 admitted game ids, including zero-retained-time games. dates come from the bound inventory, not game-id arithmetic or the website database. 04k/04l's generated scores and old fitted states are not empirical inputs.

`p` and forty-mode `B` depend only on 2021–22, which is wholly training. prove that source chain and retain `R=diag(p)B`; do not recompute a final-season spatial reference. all earlier seasons are wholly training. final-season rate, exposure reference, active players, context means and penalties use training games only.

freeze the final partition before contracting assessment responses: within each admitted calendar month, sort inventory ids by `(sha256(utf8("hockey-stats:04m:split:v1:" + game_id)), game_id)` and reserve the first `floor(month_game_count/5)` for assessment. all remaining games train. whole games include both directions, every retained stint and zero-event time. publish exact ids and actual fraction; do not redraw for better results or subgroup balance. retain zero-time games in inventory/calendar accounting. zero assessment exposure or an assessment context absent from training stops the fixed protocol explicitly; no mean substitution or silent exclusion.

the external originals were not re-read during specification. preparation verifies availability and these contracts before fitting; ordinary missing-path/hash/i/o failures stop the command.

## training and prediction contract

use existing `ShapeCoefficientLikelihood`, `fit_shape_coefficients` and `validate_shape_coefficient_state`. fit **six** states: 2021–22 through 2024–25 once chronologically, then final training-game borrowing and independent fits. the contextual baseline needs no scale fit. share earlier states; never fit final assessment responses or pass probe alternatives into history. retain relative-rate carry, full covariance, coarse grid `log10 variance = −8..0 by 0.5`, bounded refinement and endpoint flags. no inherited 04g population constraint or 04i selector.

for directed hours `e=seconds/3600`, count row `n`, player indicators `X` ordered offense then defense, and existing context indicators `Z`, contract selected training games:

```text
A = sum(e X'X)                 C = sum(e Z'X)
E = sum(e Z)                   N = sum(Z'n)
K = sum(X'n)                   r = sum(N)/sum(E)
xbar = diag(1/E) C             nbar = diag(1/E) N
H = r (A − C' diag(1/E) C)
T = K − C' diag(1/E) N          Q = (T − (T 1) p') B
```

derive active ids from positive training exposure and `u` from their normalized player exposure, never full-season `u`. retain training-supported contexts. the score has forty columns; response energy is absent, not fabricated zero. `weighted_population` owns positive bootstrap weights with fixed references: do not weaken it to smuggle a zero-weight split through. a selected-game contraction owns the new references and delegates shared arithmetic where useful.

each arm estimates its own context compensation. use saved **uncentered** coefficients for prediction:

```text
M_a = r uncentered_Theta_a R'           # native physical player shape
F_a = nbar − (nbar 1) p' − xbar M_a    # training-context shape
prediction_i = Z_i F_a + X_i M_a
```

`xbar M_a` uses training-current identities. embed predictions into the source player universe by identity. borrowing uses the actual final posterior for carried-only identities, including covariance-mediated updates. an identity absent from that fitted union receives its declared zero **raw prior mean**; the independent arm likewise uses zero for every untrained identity. keep their assessment rows and report their exposure. this is a prior prediction, not missing-data zero fill. baseline `M=0,F=nbar−(nbar 1)p'`.

verify equivalence with centered coefficients and compensated context. a wholly unseen player's centered value is minus its role-specific shift, not zero; derive the two shifts from `u @ uncentered_Theta` in each role. do not substitute the stored sum of shifts for either role. preserve historical fitting semantics.

## paired empirical assessment

score the zero-sum recorded shape `h_i=n_i/e_i−(sum(n_i)/e_i)p`. the observed total defines the assessment target only; it never enters a prediction. this tests the **joint lineup prediction**, not separately validated offensive/defensive ability. reuse `shape_regions()`'s twelve physical regions `W`; retain their native definitions independently of the forty fitted modes.

for each held-out game, use raw grouped moments on identical full player/context axes:

```text
G_g = [[diag(E_g), C_g], [C_g', A_g]]
S_g = stack(N_g − (N_g 1)p', K_g − (K_g 1)p')
L_a = stack(F_a, M_a)
D_ab,g = <(L_a−L_b)W, G_g ((L_a+L_b)W)>
         − 2 <S_g W, (L_a−L_b)W>
delta_ab = sum_g D_ab,g / (12 sum_g sum(E_g))
```

`<,>` is the frobenius inner product. this paired form cancels observed-response self energy exactly; it is **not** absolute mse/rmse. negative means the first arm has lower error; units are `(recorded unblocked attempts/60)^2`. do not clip signed losses. contract sparse game moments directly, without a dense game-by-player-squared tensor.

report `borrowing−independent` as primary; `borrowing−context` and `independent−context` as reference checks. require per-game, pooled and bootstrap-draw closure `D_bi = D_bc − D_ic`. save `loss_numerator,directed_hours,metric_normalizer,loss_denominator`, with `loss_denominator=metric_normalizer*directed_hours`: normalizer twelve for the regional aggregate and one for a single region or native metric. estimates and resampling use this denominator. pooled ratios weight total directed exposure, not an unweighted average of game rates; both sides remain one sampling unit.

reuse paired resampling: 2,000 draws each for games, seven-day blocks and fourteen-day blocks, `PCG64(404130)`, one shared draw matrix per scheme across contrasts/regions. blocks start at the earliest held-out inventory date and retain empty intervening blocks. draw units with replacement and pool numerator/denominator; keep zero-time games and report any zero-denominator draw as unavailable, without replacement. two-sided 95% percentile intervals use linear quantiles. adapt shared arithmetic to float exposure denominators; do not reuse an integer attempt `count` or attempt-specific failure message.

per contrast: all three valid intervals strictly below zero → `supported_lower_loss`; all strictly above → `supported_higher_loss`; otherwise `unresolved`. these are conditional diagnostic directions, not multiplicity-controlled claims, equivalence, noninferiority or nomination. intervals omit fitting/selection, split and population uncertainty. report every scheme; no favorable scheme selection or new 99% gate.

bounded diagnostics: twelve regional paired differences; native inverse-share paired loss using metric `diag(1/p)` and denominator directed hours; per-game observed/predicted native mean shape and signed residuals; calendar-month summaries; exposure/support accounting. among assessment players, support groups are exclusive: `current_training` has positive final training exposure; `carried_only` has no final training exposure but earlier exposure; `new_to_fit` has neither. separately record the overlapping boolean `first_in_corpus_final` for no earlier exposure. this means first observed during 2025–26 here, not nhl debut or a known ability change.

role-specific on-ice signed residual associations use `K_g−(K_g1)p'−C_g'F_a−A_gM_a`; sum within each fixed support group and divide by its total on-ice hours. report member counts and hours, with overlapping participation disclosed. zero hours yields unavailable, not zero. these are neither individual accuracy nor independent samples; no cohort squared-loss claim, residual ranking or subgroup search.

native means retain coordinates and coverage, but are not player-effect maps. no absolute regional errors, negative-stint frequencies, entrant-stint loss subsets or complete-player-rate claims follow. complete-rate/uncertainty issues stay open.

## owners, interfaces and artifacts

| owner / file | responsibility |
|---|---|
| `analysis/src/hockey_stats/attribution_data.py` | `read_empirical_source(result_ref, basis_ref, corpus_ref)` validates the recorded chain; `empirical_training(grouped, references, train_ids, basis)` returns a `ShapeCoefficientLikelihood` plus training ids, contexts, `xbar,nbar`, exposures and source identities. reuse decoding; no acquisition or fitted substitutions |
| `analysis/src/hockey_stats/attribution.py` | unchanged coefficient fit, state validation and bounded probes; no study partitions or assessment policy |
| `analysis/src/hockey_stats/attribution_prediction.py` | `empirical_prediction(training, state_or_none, evaluation_ids)` returns aligned physical context/player matrices; `empirical_paired_loss(game_moments, left, right, metric)` returns signed numerator and float directed hours. own gauge compensation and residual arithmetic once |
| `analysis/src/hockey_stats/paired_evaluation.py` | extract the shared ratio/block kernel from `chance_evaluation.py`; `paired_ratio_intervals(numerators, denominators, dates, seed)` retains float denominators and unavailable draws. chance callers delegate to this one kernel while retaining their labels, counts and values; no experiment framework or historical migration |
| `analysis/research/attribution_empirical.py` | frozen source/partition/arm policy; `prepare → fit → assess → report`, finite inventory, classifications and receipts |
| `analysis/research/attribution_empirical_report.py` | render saved assessment into prose/tables/figure; no original arrays, fitting or duplicated scientific arithmetic |
| `fixtures/attribution/empirical-prediction.{json,npz}` | small explicitly synthetic counted-stint fixture, source bindings and checked expectations; extend the existing fixture readme |
| `docs/research/attribution-04m/` | small result, decision, verification, tables and one figure; expensive states stay external |

```text
python analysis/research/attribution_empirical.py prepare \
  --source-result docs/research/attribution-04b/result.json --output <new-dir>
python analysis/research/attribution_empirical.py fit --prepared <prepared.json> --output <new-dir>
python analysis/research/attribution_empirical.py assess --prepared <prepared.json> --fit <fit.json> --output <new-dir>
python analysis/research/attribution_empirical.py report --assessment <assessment.json> --output <new-report-dir>
```

fixture preparation substitutes `--fixture <fixture.json>` for `--source-result`, never combines them. schema version 1, `kind:attribution_empirical_{protocol,prepared,fit,assessment,result}`, explicit `purpose:research|fixture_exercise`, clean producer/dependency identities and existing `{path,sha256}` references. no schema guessing, substitute paths, directory discovery or compatibility adapter.

protocol binds the spec snapshot, source/axes, split algorithm and ids, arms, formulas, seed and probe policy. prepared binds inventory, training statistics, reference/basis digests, expected states/probes (research six each; fixture four each) and coverage; bind grouped archives rather than copying a corpus. fit binds each state's season, all-seen/current/entrant/carried-only ids, named predecessor/likelihood, basis/source identity, full scale/diagnostic receipts and `Theta,V,uncentered_Theta,centering_shift,u,r,a,q`; save completed states externally before the next state. assessment binds complete state/probe inventories, game numerators/denominators, point/interval/diagnostic rows and measured costs.

research result has `execution_status:complete,numerical_status:verified|unresolved,study_status:diagnosed|numerically_unresolved,nomination:null,admission:not_admitted,handoff:null`, plus at most one `next_question` or an explicit unresolved reason. fixture results instead use `study_status:fixture_verified|numerically_unresolved,next_question:null`. incomplete required inputs/states cannot yield a completed result.

research runs sequentially under `/Volumes/Expansion/hockey-stats/runs/attribution-04m-<date>/`; measure the first historical state within the six, not an extra pilot. no runner, automatic rerun, local mirror or recovery engine. source/partition hashes remain unchanged through completion.

## numerical and integration acceptance

retain finite endpoint winners and inherited `scale_unresolved` as bounded-search limitations; nonfinite or failed solves stop dependent fitting. validate every saved state against original posterior, gauge and parent equations. run one existing bounded probe per state: saved winner/two nearest coarse candidates, one tighter saved bracket where present (`xatol=1e-6,maxiter=80`), fixed incoming history. require equation residuals ≤ `1e-8` and current-player native/regional movement ≤ `1e-4` of annual league rate. these six probes are conditional checks, not propagated-history or global-optimization bounds.

rescore both final probe alternatives individually and together with the same assessment draws, recomputing their context compensation from alternative uncentered coefficients and unchanged training moments. report movement and direction stability for the three aggregate contrasts; a changed aggregate classification or failed probe makes numerical interpretation unresolved. regional/native movements remain diagnostics, not additional vetoes. retain primary fits; do not replace them, widen the grid or add campaigns until a preferred result appears.

implement/review four non-overlapping boundaries:

1. **source/training:** verify source, dates, split, coverage and train-only contraction. synthetic held-out-response perturbations cannot change training/reference/basis/fits; held-out exposure cannot change `u`. reconcile original inventory, including zero-time games. missing training contexts fail visibly.
2. **fitting/prediction:** fixture runs two historical states and two final states, three season labels and the same monthly split. reuse graph-fixture geometry; supply explicit nonnegative integer counts, not gaussian scores relabeled as recordings. include zero-event rows, entrants, carried-only identities, unavailable contexts in a separate failure case, changing rates and shared lineups. independently check raw/centered predictions, zero raw prior means and untouched shared consumers.
3. **assessment:** direct tiny-row residual-square differences must equal grouped contrasts, including negative differences and all closure identities. check fractional hours, shared game sides, zero denominators, empty calendar blocks and interval labels. direct solves/oracles independently check saved fits; no extra real fitting. fixture uses four probes, research six.
4. **research/report:** after separate execution assignment, reconcile six states, six probes, held-out ids and every score/diagnostic row against bound sources. independently reproduce contraction/interval calculations from saved moments/states. verify rendering and saved-only regeneration. adversarial source, numerical/statistical and content review at each boundary; repair responsible owners, not alternate paths.

temporary integration/live checks follow red → green → refactor → green, then deletion with test-only dependencies/controllers. retain fixtures, checked facts, scientific commands and receipts; no lasting harness is assigned. source bytes and historical fits/verdicts remain unchanged. software acceptance may yield imprecise or adverse scientific evidence.

## content contract

the content reviewer owns plain-language meaning, units and scope within these schemas:

| artifact | required content |
|---|---|
| `decision.md` | question; actual source/partition/game/time/attempt coverage; three conditional contrasts; support gaps and scale limits; one next question or unresolved; no ability admission |
| `comparison.csv` | `contrast,metric,region,loss_numerator,directed_hours,metric_normalizer,loss_denominator,estimate,scheme,lower,upper,undefined_draws,direction,reason`; intervals/reasons explicit for every scheme |
| `game-scores.csv` | game/date/partition, retained hours/counts/coverage, paired numerators and reference identities; both directions remain one game |
| `diagnostics.csv` | fixed regional/native/calendar/support summaries, observable group counts/hours, signed residuals and numerical movement; unavailable values carry reasons |
| one static figure | three aggregate interval comparisons plus twelve regional deltas, consistent sign, zero line, units, exact interval meaning and numeric companion table |
| `verification.md`, `result.json` | source/producer/output references, costs, inventories, independent checks, source preservation, temporary-check deletion and limits |

good content identifies withheld games, prediction gains and harm, conditional uncertainty and unsupported claims without opening code. headline lower error is joint recorded-shape prediction; no player rankings, attractive player-map gallery, known-effect recovery percentages or micah-parity claim. the accepted cost is a limited empirical comparison before another prior revision; synthetic recovery, empirical uncertainty, richer deployment/age adjustment, complete rates and supported chance valuation remain separate work.
