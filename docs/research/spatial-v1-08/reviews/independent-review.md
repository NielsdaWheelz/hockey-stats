# independent mathematical, source and systems review

date: 2026-10-31 utc. status: report against analysis commit `0e3e245` plus the failure branch at `a4b07e0`, with no open source or mathematical defect from this review. review remains open through final acceptance. strict-state, composition and application reading is partial; real fits, real publication and live checks have not been reviewed because they have not happened. this is not software acceptance, activation or scientific admission.

read `AGENTS.md`, the brief, council, the complete [v1-08 specification](../../../specs/v1-08-positive-attribution.md) and the [attribution appendix](../../../specs/experimental-attribution.md). reviewed `spatial_design.py`, `spatial_rates.py`, `spatial_state.py`, `spatial_composition.py`, `coalitions.py`, `iter_neutral_origins`, `read_panel` and the owners they consume: `analysis_support.py`, chunk construction in `analysis_context.py`, `execution_scores.py`, `execution_design.py`, `build_shape_basis`, publication validators and the spatial wire schema. real input reads were limited to two prepared games, the five score manifests and saved execution head metadata. no prepared-season pass, fit or serving file was touched.

## findings

| id | finding | disposition |
|---|---|---|
| d1 | a recorded goalie attempt failed the skater-only shooter check, so an identified shooter was labeled unresolved and removed its whole two-direction segment | accepted; repaired; `spatial_design.py` tests skaters and goalies |
| d2 | aggregate support omitted `historical_borrowing` on carried terms and `setter` on chance targets carrying the pre-outcome mixture | accepted; repaired in `_projection_support` |
| d3 | centered context is fully dense, so csr storage and full-row grouping keys threatened the 64 gb envelope. two real games have 1,076 and 1,197 5v5 chunks, about 3.0m directed rows a season across 354 context columns | accepted; design now holds sparse actors and dense context, with digest grouping and exact representative comparison |
| a1 | per-role transition columns exactly duplicated each other and widened the effective prior by a factor of `sqrt(2)` | accepted; spec amended to one attacking-frame block in `4ec546d` |
| a2 | "all-missing" was ambiguous between an indicator and a member fraction | accepted; `missing_fraction=1` is the declared reading |
| t1 | exposure-weighted means of a constant column round away from the constant, giving a noise scale near `1e-16` and a false `±1` column: 1,095 of 2,000 random constant cases on the reviewed code | found independently by the authors; repaired in `d14266a`; 0 of 2,000 at `3cb6701` |

root and other reviewers found and repaired further defects during this review: the tautological time identity, support pointer indexing, optional neutral-mass reconciliation, per-column support scans, physical-state discrepancy handling, seasonwide gap attribution, unbound head arrays and the actual-context baseline binding. this review did not independently re-derive those repairs beyond the proof below.

## open items

### volume probe may fail its fixed budget at real scale

simulation evidence only. this is not a real-fit result and proposes no change to any margin, gate or probe.

the simulation matches real scale in objective magnitude and information, not in design: 121,254 attempts over 2,280 directed hours, 640 skaters on persistent lines and pairs, 60 correlated context columns, 60,000 rows, volume only, one seed, scipy L-BFGS-B at the prescribed controls. |f| is 3.67e5 and the hessian condition is 5.7e4.

| quantity, attempts per hour | value | fixed budget |
|---|---|---|
| continuation movement of focal rate, the quantity the fixed probe records | `2.7e-4` | `1e-4` |
| baseline distance to an exact newton optimum | `5.5e-4` | none; not a contract quantity |
| continuation distance to that optimum | `4.3e-4` | none; not a contract quantity |

the first row is the relevant one: it concerns the contract's own measurement, separately from optimum distance. if real behavior resembles this, the volume probe fails after all five annual chains are spent. real designs are larger and may behave differently; the saved v1-05 heads supply no direct answer: they are binary logistic objectives near `7e4`, and every one stopped on `ftol` with gradient maxima of `1e-3` to `1e-2`.

mechanism: `ftol` is relative to `|f|`, and most of `|f|` here is the constant `sum(y)*log(r)`. the stopping threshold therefore moves with the choice of rate units, although the minimizer does not. dropping that constant and evaluating `expm1` preserves the minimizer. in the same simulation it gives probe movement `1.9e-5`, baseline distance `2.1e-5` and continuation distance `1.4e-5`, at 819 rather than 550 iterations. root left this proposal unselected: fixed loss and solver controls stay, with no margin relaxation. shape and quality were not simulated.

resolved by: real final-year probe results, either way. a volume pass closes this item; a failure is handled under the existing [numerical contract](../../../specs/v1-08-positive-attribution.md#numerical-resolution-and-measured-cost).

### n2: reset clocks give fresher chunk-left prefixes

limitation, documented by root as conditional on the piecewise elapsed partition; no code gate. chunk cuts at resets mean an event at a reset clock sits at a chunk's left edge and sees a fresher workload prefix than a mid-chunk event: 71 of 207 real events. the difference is bounded by one chunk, estimated at seconds of ice time against a standard deviation of hundreds, and lies inside the accepted piecewise-constant approximation.

### closed: reset at the event clock reached the event design

goals and stoppages cut chunks, and an internal-boundary event uses the following child, whose elapsed transition follows same-clock resets. root chose the stronger invariant in `9278552`; `037a676` and `1e1b51a` implement it. `_strength_transitions` records the focal row before applying that event's own reset, so `event.context.strength_transition` is genuinely pre-event. the faceoff gate requires an anchor strictly earlier in saved chronology and preserves physical age. 207 real event rows rebuild independently with zero mismatches, and elapsed rows keep the chunk state.

### closed: `on_the_fly` proved on the focal clock

`analysis_context.py:516` proves `on_the_fly` only when a live episode strictly contains the shift start, so with a member's shift starting on the focal clock, a reset on that clock, possibly the focal goal or whistle itself, turned the start `unknown`. on event rows that level therefore depended on the outcome. evidence was 5 of 2,070 member slots across the two real games, all `on_the_fly`, none the shooter; the contrasting reset case was never observed, so the dependence came from the code rather than an observed pair.

root repaired it in `0e3e245`, more narrowly than this review proposed: an event `on_the_fly` start needs a coherent shift start strictly before the focal clock, while a same-clock faceoff stays known when its anchor is proved earlier in saved chronology. the narrower rule is better, because that faceoff is real pre-event information. physical age and elapsed rows are unchanged. all five real witnesses now read `unknown` with age preserved. neither game contains a same-clock faceoff with an earlier anchor, so that branch rests on root's controlled check, not on this review. the upstream audit now covers `on_the_fly`: 121 known shooter starts across the two games, all proved earlier, 0 unresolved.

## proofs

all math in the proof below was written from the specification, not from the modules. it reuses only fixed axes, column helpers and the transform under test.

three-year synthetic chain at `0e3e245`, through `fit_spatial`, strict state write/read and the final-year probes: 20 skaters, 3 coaches, 300 directed rows and about 250 events a year, including a zero-time actor, unknown coach and score, blocked fractional origins and zero chance targets. it passes:

- objective and gradient for all three heads against an independent dense implementation with entry, carry, gap, age drift and prior-only profiling, at the solution and at a random point. agreement is within `1e-8`.
- final gradients below `1e-2` against that implementation. this also exercises the solver's grouped volume path, which the direct comparison does not.
- neutral, focal and difference native maps, scalars and relative percent against direct definitions, with the reference taken as the exposure mean of the elapsed linear predictor.
- exact actual-context allocation against all 24 orders over every directed row and focal player, averaged after evaluation by focal time. worst native-cell difference `1.89e-15`. a zero-time actor reports `no_exposure`.
- history: a gap-two returner carries from `20232024` at precision `50` with age drift; an absent-then-entering actor enters and then carries.
- all three final probes pass on this tiny design. largest native-map movement is `5.51e-5` per hour, on volume coalitions. this is not evidence about real scale.

real-source reconciliation at `0e3e245`, games `2025020701` and `2025020101`. elapsed context in `2025020701` was rebuilt from primary records: 2,394 directed rows show zero mismatches across score margin from a source-order goal replay, home/period, ten-minute band, members, start × age from shifts, rest, all twenty workload counters on complete and partial-known means and complete fractions, and transition. 207 event rows across both games rebuild with zero mismatches on pre-event margin, chunk clock, attacking side, pre-event transition and gated start × age under the final rule. the retained-target audit does real work: 86 known shooter faceoff starts and 121 known `on_the_fly` starts, all proved earlier, 0 unresolved, and exactly the 5 known spatial unknown starts. execution rows were stubbed, so this exercises source extraction, not scoring. two games are not a corpus check.

failure branch at `a4b07e0`, the only analysis change after `0e3e245`. three injected post-solve failures in a carry year cover volume, shape and quality, using `InputContractError`, `FloatingPointError` and `ValueError` at both diagnostics and centering. all pass: the failed head retains exactly its 60-row incoming ledger, with no centers, reference predictor, diagnostics, `prior_mean` values or coefficient file, and it keeps its solver and objective evidence. the other two heads stay complete. the state strict-reads, all projections and adjustments are unavailable with zeroed arrays, no probes run, and the next year refuses it as a predecessor. the strict validator refuses a failed state with retained centers. one limit remains: an exception inside the solve itself leaves `solver` null, losing the partial trace, while its reason and resources survive. that record is truthful, so no change is requested.

real binding: all five accepted score manifests equal the `prepared` and `coaches` references `prepare_spatial` requires. their 5v5 panels hold 117,676 to 125,351 events and 18.9m to 23.9m origin rows, about 160 to 190 per event.

read and cleared, not separately executed: elapsed-only moments and absent-mean zeroing, team-relative start zones, on-the-fly versus unknown, age-bin edges, rest ordering, ten-minute bands, coach gate signs on pre-event margin, goal chunk cuts, probe budget arithmetic against the specification and the detached reader's locator-only provenance.

## cost notes

- `validate_design` loops over every row in python and each annual fit reaches it about four times: before fitting, at write, at read-back and as the next year's predecessor. composition repeats it for five states. estimated tens of minutes per annual fit; measure on the first real year.
- the cli holds the predecessor's whole design through the fit, though only its ledger and basis are used. after the representation change this looks affordable; measure it too.
- `solve_logistic` retains the native `maxfun=15000`. v1-05 heads took 3,000 to 5,000 evaluations. a larger volume or spatial head exhausting it would report a failed solve after the full cost.

## not established

no real fit, probe, publication, api, browser or export result is reviewed here. the synthetic proof uses tiny designs and proves arithmetic, not estimator quality. shape and quality numerical sensitivity at real scale is unmeasured. causal interpretation, calibration and scientific support are outside this review.
