# independent adversarial review — v1-06 real acceptance

status: interim, 2026-10-27. integration contracts reviewed read-only; no blocker found. real annual scores, the composed exchange and the candidate do not exist yet, and external drive reads are paused while the root restores ordinary access. nothing here claims real delivery, scientific admission or activation.

scope: the merge of main `8163545` (accepted real v1-03/v1-16, as `4e840ea`) and the staged merge of v1-05 `e7bcfa2` (recipe `14267557016abe9c08a6c863fe03151edca0be0fac889321e758f764af36eae5`, twenty real heads, four passed probes) into `implement/v1-06-execution-scoring`. the reviewer edits no production file, starts no fit, score, composition or publication, and changes no permission on any path.

temporary reviewer material, to be deleted after final green: `var/v1-06-real-checks/independent/` (`evaluator_parity.py`, `v105_execution.py`, `score_check.py`) and the working status file `/tmp/v106-real-review-status.md`.

## integration contracts

| contract | evidence | result |
|---|---|---|
| v1-05 design identity | every module feeding `prepare_execution` (`analysis_data`, `chance_features`, `feature_history`, `execution_history`, `feature_data`, `shot_origins`, `coaches`) is byte-identical to the v1-05 producer `7f6edf1`; `execution_design.py` differs only by the additive `scoring_facts`/`observed_setters` fields. `DEFINITION`/`RECIPE` are unchanged | pass. scoring binds recipe, prepared and coach identities at runtime but does not compare re-derived coverage with the saved state coverage; the real check below closes that by data |
| evaluator parity | frozen v1-05 `execution_branch_probabilities` reproduces all fourteen saved actual/neutral signatures in `fixtures/execution-v1-05/predictors.json` against its stable `14267557` state; the merged log-domain evaluator differs by at most `2.8e-16` on every array, so those sha signatures are no longer bit-reproducible under merged code | pass. the signatures remain v1-05-arithmetic historical evidence, not a current-code check |
| unknown/goalie setter branch | v1-05 couples unknown/goalie branches to the candidate-weighted skater mean; v1-06 uses zero setter deviation. design weights make that mean the same weighted average as the setter center; in all five real `g` heads they agree to `1.7e-16` | pass. the actor probability is the fitted one |
| frozen real selector | 48 requirements: 44 actual (`incomplete_setter` is actual `2025020010:66`), four fixture rows sharing one sparse shooter witness `synthetic-resolution:2025020038:6:shooter:8471734`; the staged `_resolve` rebuilds it through the sparse branch, and the reader's `context_key == keys[0]` and complete-key preconditions hold by construction | pass. the separately reported fixture `incomplete_setter` synthetic dispatch is owned by the native writer and is not a real-chain failure |
| participation | the staged `execution_participation` rule equals the factual `elapsed_available` rule; an all-invalid-segment game is unknown, not zero, and the season gap propagates | pass. annual scores must come from the clean commit containing it, because projection `support` changes |
| composition | the staged per-game `physical_statuses` change preserves the source/score binding and fallback exactly while dropping full prepared-attempt retention; compose removes only the `-opportunity` pending method, and the retained primary pending method is still referenced by `primary_pass_xg_per60` | pass |
| exchange2/schema8 and the two-pass serializer | the factual builder streams evidence per game through `write_results`; composition uses the generic path and the final strict read-back. app server/web typecheck passes on `4e840ea` plus the current index, and the eight files both sides changed merged without combined hunks | pass |

## historical versus current evidence

current-source receipts, rechecked against worktree hashes on 2026-10-27:
- [numerical integration](../numerical-integration-20261026.json) binds the current `execution.py`, `execution_design.py`, `execution_fit.py`, `execution_state.py`, `execution_history.py` and `feature_data.py`. it is fixture qualification under `14267557`, not real acceptance.
- the [merge boundary](../real/merge-boundary-2026-10-26.json) binds the current `analysis_publication.py`, `descriptive.py` and `microstats.py`.
- the [composition lifetime check](../real/composition-memory-boundary-2026-10-26.json) binds the current `execution_composition.py`. its retained-capture byte differential is not completed.

historical, not current acceptance:
- the accepted-01 fixture scores, results and candidate `d553ffb2…`. they were made under recipe `cfbda18b`, which the current score reader rejects.
- the v1-05 predictor sha signatures, which are v1-05 arithmetic.
- the 2026-10-23 [independent review](independent-claude-review.md).
- any check that reads accepted-01 members, which counts as lifetime or shape evidence only.

open before acceptance, none of them blockers:
- the composer byte differential.
- a receipt binding the staged `execution_scores.py` `_resolve` dispatch. only a temporary script covers it now.
- the stale `49956bf`/`cfbda18b` integration sentence in [verification](../verification.md).
- a preflight that the real coach artifact contains the `identities.json` that `write_execution_scores` reads.

## cost observations

these are measured-cost items, not correctness findings. scoring calls the accepted v1-05 `prepare_execution`, which now eagerly materializes all four heads' fit batches that scoring never consumes. real v1-05 receipts show 5.6–6.9 ks of design time and fit peaks of 17–21 gb. composition still holds a full season of `interval_fact`/`interval_player` rows (about 2.5m/4.3m on real 2023–24) plus valued rows in memory. the campaign should record actual peaks rather than infer them from fixture capacity.

## real acceptance checks pending

when drive access returns and the root names the canonical paths, the reviewer will run bounded checks:

- events versus the bound v1-05 `coverage.json`: equal keys, head dispositions and `complete` exactly where `full_probability_context` holds;
- `score_check.py` per year: stratified events plus all 256 final-year probe keys, with sixteen coalitions, explicit 24-permutation shares, posteriors, prefixes and conditionals recomputed from saved panel logits plus state residuals in plain arithmetic, plus sampled and frozen projection pairs, maps, and shooter/setter likelihood counts rebuilt from saved event and candidate sets;
- composition: source/paired/unvalued partition, type and danger totals, attempt-value key joins, reference-xg mass/seconds closure and exact preservation of factual rows;
- candidate: `mode=ro&immutable=1` read, schema 8, stored execution rows equal to the results and no wal/shm.
