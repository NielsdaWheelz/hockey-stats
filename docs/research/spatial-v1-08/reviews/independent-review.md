# independent mathematical, source and systems review

date: 2026-10-31 utc. status: report through source `9fbcbd2`, with no open source or mathematical defect from this review. saved fixture composition and publication are clean. server, api, browser, detached runtime and every real result remain unreviewed. review remains open through final acceptance. strict-state, composition and application reading is partial; real fits, real publication and live checks have not been reviewed because they have not happened. this is not software acceptance, activation or scientific admission.

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

## saved fixture03 chain

final-recipe captured fixture, five annual states at source `838b058`, whose numerics equal `a4b07e0`. this was a replay of saved files with no new fit, probe or source pass, and it read raw json and arrays rather than the strict reader.

| year | directed rows | events | roster | neutral/focal map worst | brute allocation worst, three low-time skaters |
|---|---|---|---|---|---|
| `20212022` | 12,962 | 632 | 224 | `3.1e-15` | `2.6e-15` |
| `20222023` | 8,464 | 352 | 179 | `1.8e-15` | `2.8e-15` |
| `20232024` | 12,298 | 453 | 201 | `1.8e-15` | `1.3e-15` |
| `20242025` | 15,986 | 665 | 245 | `2.3e-15` | `4.4e-15` |
| `20252026` | 9,196 | 358 | 277 | `2.8e-15` | `2.7e-15` |

history: every manifest binds its predecessor's digest. for every actor, head and subblock, a ledger replayed from raw arrays matches the saved entry or carry kind, anchor, gap precision and mean; each carried mean is the last supported raw coefficient. prior-only coefficients sit at their conditional means within `1e-13`. saved objectives match an independent implementation, with stationarity at or below `3.2e-5` for every head and year.

probes: exactly three continuations exist, one per head, each with unchanged prior inputs and the prescribed stopping. baseline arrays still match the manifest. keys were written before the first continuation, at one-second file-time resolution. 256 frozen contexts are in key order. all 15 maxima recomputed from raw arrays with independent math agree with the saved comparisons, including worst volume coalition `5.66e-5` and standardized `5.93e-6` per hour. all pass. `trades` is truthfully absent: 0 of 144 final-year skaters have two teams, so no final-year probe exercises a traded player. this fixture says nothing about real-scale budgets.

## publication recipes

the composition and publication commands bind the accepted inputs. the fixture results carry the same preparation digest as all five states. each display year's published execution method binds that state's valued and coach identities, and the publish output name matches the server path. both interpreters report python 3.14.8, numpy 2.5.3 and scipy 1.18.1.

| id | finding | disposition |
|---|---|---|
| r1 | `app/dist` is older than the source: 0 of 38 files postdate the last `app/src` change, and the newest main bundle is from 00:25:54 while `5b183a1` and `3f9f90c` were committed later | open; rebuild at the final commit before any application check |
| r2 | `detached.sb` omits `raw`, `factual`, `references`, `chance`, `archive`, `runs/coaches-*` and `runs/execution-v1-05-*`, though the v1-06 precedent denied raw inputs and a detached result is only as strong as its deny list | open; extend before the detached run |
| r3 | `prepare-selection.py` pins two of five accepted digests | open; pin `d6b4661c`, `e6980f33` and `93bf863b` before writing the selection |

r1 is closed by `fixture03-app-build-bindings.json`: this review reproduced the build digest `2b84760d` and the source digest `359a32a0` over 38 and 52 files, all 52 blobs equal commit `8664fc8`, and the n3 sentence is present in the built client. the source digest needs `Path` ordering, not string ordering; the stated definition says only "ordered", which is harmless.

r2's deny list now covers every external root and sibling checkout. what stays readable under `fixture03` is logs, exit files, accounting and the candidate itself. all 27 paired one-byte controls in `fixture03-detached-controls.json` show outside exit 0 and sandbox `EPERM`, and the built-asset positive control passes. the profile file and the receipt's saved text both hash to `42c21d26`; root's receipts at `960e229` bind that digest, which resolves an earlier quoted `efd6c3e4`, and the candidate positive read passes before and after with the profile unchanged. that is one-byte access only: runtime detachment remains pending, so detached acceptance is not established. r3 could not be applied before summarize started: selection `134c4522` was already written. all five of its digests match the live manifests and this review's independent reads, and root keeps that consumed selection unchanged.

## saved composition

`fixture03/results` from summarize exit 0, 289.93 seconds, 741,621,760 bytes peak resident memory, 1.2 gb. replayed from raw member files.

- preservation: all 45 non-owned members, 789,233,295 bytes, are byte-identical to `fixture/current-02/results`, with unchanged family descriptors. people, sources, supports and all nine existing methods are exact. three methods are added, and every evidence uri resolves to its stated digest, including the coefficient-support receipt.
- identities: published and fitted skaters agree exactly in all three years, 201, 245 and 277, with no published-only or fitted-only person. the missing-projection branch is therefore not exercised on this data, only by the synthetic product check.
- scalars and support: all sixteen values and support records equal the saved projections, with absent intervals stated. other strengths stay `not_computed` for v1-09.
- maps: native cells equal the saved arrays exactly. an independent point-in-rectangle transport plus the declared pooling reproduces display mass exactly, native and display totals close within `2.84e-14`, and density is exact.
- decompositions: all seven saved adjustment fields are exact, closure is within `4.26e-14`, and 608 zero-time rows are unavailable.

### n3: no-history prior-only rows show the annual center

repaired in wording at `ddb7181`; no numerical change. the shared sentence in selected detail, csv and png states that raw zero can become nonzero after annual centering and that borrowed values can remain large without current matched exposure. both claims match the measured rows below. a skater with no current or earlier support has raw coefficient zero, so its contrast is the annual reporting center with its sign reversed, not a player estimate. every such skater in a season shows one identical value: `-0.264%` in `20242025` (12 skaters) and `-1.169%` in `20252026` (53 skaters), for offense attempts. this follows the specification and support marks them prior-only, but the number invites being read as a small negative estimate. carried prior-only rows range from `-24.3%` to `+28.8%` on these small fixture histories, with zero current time. percentiles are withheld for both; the magnitudes are shown.


## real first annual preflight

read-only review of `receipts/real-20212022-pin-preflight.json` and the literal command, sha-256 prefix `3df58081e4da8924`. no real game was read and nothing was launched.

cleared: `20212022` is the first prepared season and has no `--previous`, which the cli enforces. `fit_spatial` requires this start for real purpose and adds no probes in this year. the prepared, coach and score digests match the accepted inputs, with 1,312 unique games. analysis is unchanged from `838b058` to `8664fc8`, tree `a0a92672`. output is external, absent and exclusive. solver options are the prescribed `10000`, `1e-15`, `1e-6` and history `10`. the drive has 6.6 tb free. memory shape looks inside the envelope: about 3.0m directed rows across about 350 dense columns, or about 8.4 gb, doubled transiently, plus keys. that is arithmetic from two 2025-26 games, and no runtime forecast is made.

| id | finding | disposition |
|---|---|---|
| p1 | `_audit_shift_starts` raises on the first non-prior known shooter start. the fixture shows 0 such cases in 2,361 known shooter starts, which bounds the rate only below about `0.13%`; real `20212022` has 117,676 5v5 panel events, so a real case remains plausible. a stop is correct, but stopping at the first case costs the design pass and yields one key where the issue needs a census | recommended before release: collect all cases, then raise after the pass and before fitting. decision with root |
| p2 | the preflight's own `prerequisites` still list fixture publication and browser acceptance, which the proposed parallel release would not satisfy | amend the receipt to record root's decision. parallel running is acceptable in my reading: those stages consume states and do not feed fits, so the exposed cost is a state schema change, not a math change |
| p3 | the command has no `cd`, though `--project analysis` is relative. a wrong directory fails fast rather than silently, because the primary checkout rejects `--family spatial` | add an explicit `cd` |
| p4 | the command lacks the fixture recipes' occupied-output guard, so a relaunch overwrites the failed run's log and exit evidence. `--out` itself stays exclusive | add `set -C` or the guard |
| p5 | `implementation()` runs after the heads finish, hours after launch. later docs or app commits are harmless because the analysis tree matches, but any change under `analysis/`, including `analysis/research`, would misstate `git_commit` or `git_dirty` for code already loaded | launch condition: no edit under `analysis/` until exit, and record the launch head in the runtime receipt |

audit aggregation at `9fbcbd2`, resolving p1: the 14-line diff replaces the immediate refusal with per-game records and one refusal after the selected loop. that runs inside `prepare_spatial`, so `--out` stays absent. this review ran the temporary check and added two of its own: on `0e3e245` the same bad case stops after the first game, so the check's red is real, and the refusal parsed as json holds both located records, each with kind, keys, pointers and prepared source digest. no strict reader closes over the audit keys, so fixture03 states stay readable, and the cli prints the full message. the valid control uses a same-clock faceoff with a proved earlier anchor, so that branch is now exercised by a synthetic record. one limit: unresolved bindings still pass through as counts by design, so real annual `unresolved_shooter_binding_count` must be read at acceptance, because a nonzero value leaves the issue's resolution unmet.

## saved publication

read-only, immutable open of `fixture03/candidate/player-analysis.sqlite`, publication `e5118eea-1ccf-45e4-ba59-4ed8b5a906b5`, exit 0, 638.38 seconds, 230,195,200 bytes peak resident memory, 1,369,198,592 bytes.

the database digest `6c77ed60` matches `verification.json` before and after the read, with no sidecar created. quick check and foreign-key check pass, journal mode is delete, and 39 tables are present. all 112,788 envelope rows in composition members match the database on availability, explanation and payload: 49,887 spatial and 62,901 non-spatial. provided 5v5 spatial rows are 201, 245 and 277 per year, with maps at eight per skater and four decompositions per skater; other strengths remain `not_computed`. twelve methods are present, three of them spatial. `analysis_map` is shared by families, and its season totals equal the sum of the execution and spatial members.

not compared row by row: non-envelope fact tables, covered only by season row counts here and by the publisher's conservation checks, and `attempt_value`, which is declared by the publisher but has no table of its own in this database. those members are byte-identical to the accepted v1-06 input. server, api, browser and the candidate positive control are not reviewed, so detached and application acceptance are not established.

## first real annual release assessment

no source or mathematical reason to hold the first real annual was found at `9fbcbd2`, whose analysis tree is the frozen `4c83f23d`, conditional on these items:

1. the revised command and guard were not reviewed here. the launch record should show the absolute `cd`, the output guard, the launch head and analysis tree, and all of `analysis/` frozen until exit.
2. the real chain's source differs from fixture03's `838b058` by the audit aggregation; the runtime receipt should state that.
3. a nonzero `unresolved_shooter_binding_count` at first-annual acceptance is an acceptance issue, as root has decided.
4. a refusal listing non-prior shooter starts is a correct stop that needs an upstream decision, not a failed launch.
5. the volume probe risk stays open.

launch check: recipe `0a6a4c92` has the absolute `cd`, an occupied-path guard before any write, `set -C`, head, tree and analysis-status capture with a refusal on any analysis change, and preserved exit status. the launch receipt shows `960e229`, tree `4c83f23d`, clean analysis, one heavy fit and no forecast. p3, p4 and p5 are satisfied at launch; p5 holds only if `analysis/` stays untouched until exit, and p2 is recorded in `concurrency`.

fixture api: the six saved rows in the one- and two-player receipts match the candidate database exactly on offense xg, defense xg and support. that cross-checks saved values only, not the api checks themselves. the expanded target closes a real gap: the old check validated only the first selected player, and the new receipt records a mutated second-player integrated value being refused. the history-gap pair is confirmed against the database: skaters `8475726` and `8477504` have four present player-years, and the second has no person row in `20232024` or `20252026`, so those absences are genuine. `8475726` in `20252026` is a real zero-time prior-only case. no browser evidence exists.

rollback, receipts only: the operator sequence ran on disposable files under `fixture03/rollback-check`, with the strict reader validating each incoming database, no live serving mutation, and `previous.sqlite` carrying the candidate digest `6c77ed60`. this review did not rerun it.

## cost notes

- `validate_design` loops over every row in python and each annual fit reaches it about four times: before fitting, at write, at read-back and as the next year's predecessor. composition repeats it for five states. estimated tens of minutes per annual fit; measure on the first real year.
- the cli holds the predecessor's whole design through the fit, though only its ledger and basis are used. after the representation change this looks affordable; measure it too.
- `solve_logistic` retains the native `maxfun=15000`. v1-05 heads took 3,000 to 5,000 evaluations. a larger volume or spatial head exhausting it would report a failed solve after the full cost.

## not established

no real fit, probe, publication, api, browser or export result is reviewed here. the synthetic proof uses tiny designs and proves arithmetic, not estimator quality. shape and quality numerical sensitivity at real scale is unmeasured. causal interpretation, calibration and scientific support are outside this review.
