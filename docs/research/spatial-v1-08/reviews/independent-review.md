# independent mathematical, source and systems review

date: 2026-10-31 utc. status: report through source `9fbcbd2`. the real first annual stopped correctly on a confirmed upstream predictor defect; repair assignment is pending with the user. saved fixture composition and publication are clean. server, browser, detached runtime and every real fitted result remain unreviewed. review remains open through final acceptance. strict-state, composition and application reading is partial; real fits, real publication and live checks have not been reviewed because they have not happened. this is not software acceptance, activation or scientific admission.

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

## real `20212022` refusal and upstream scope

read-only. no fit, rescore, source change or 54-game pass; two census games, saved logits, coefficients and metadata only.

census: verified. the saved file equals an independent parse of the log, whose digest is `1711e43a`. it holds 54 records in 54 games for 50 players, 50 `on_the_fly` and 4 `faceoff`. every `on_the_fly` case has shift start exactly on the focal clock. every faceoff anchor is two orders later. all 54 are in the 117,676-event 5v5 panel, a rate of `4.6e-4`. this covers retained 5v5 targets in one season only. the first annual stopped correctly: `--out` is absent, with 0 heads, 4,447 seconds and 11.18 gb peak.

representatives: in `2021020637`, the shot is order 210, stoppage 211 and faceoff 212, all at clock 1049. the shooter's `faceoff/offensive` start is anchored on 212, after the attempt in recorded order. [corrected below](#corrections-to-this-review): the records do not prove that this faceoff followed the shot. in `2021020002`, the shot is at 1066 and the stoppage at 1067, and the shooter's `on_the_fly` start at 1066 holds only because no reset fell on that clock. a whistle one second earlier would have made it `unknown`.

size, under current coefficients only: moving the 54 to `unknown` raises their summed neutral mass from 2.407 to 2.817. that is +0.410 of 5,271.81 at 5v5, `7.8e-5`, with a median per-event change of 19% and a maximum of 24%. this is not a repaired value, because a refit moves the coefficients. nor does it discount the cases: the affected rows trained all four heads. [the correction below](#corrections-to-this-review) withdraws this figure as a guide to size, and narrows what the `g` coefficient rests on.

### responsible layer

the repair belongs at the execution encoder, with no repreparation. the shift's `start` and the event's `deployment.players[*].start_type/start_zone` are correct retrospective facts about the shift covering the attempt. v1-01 places pre-event context under `EventContext`, and nothing there promises that `deployment` is pre-event. `AGENTS.md` makes each selected family own its timing, and the brief separates later component facts from eligible predictors. the defect is `execution_design.py:264-266` admitting a retrospective fact as a pre-event predictor. the only other consumers are the spatial audit and frozen `chance_features.py:429`, whose research verdicts stay as they are.

`_feature_context` already holds what the gate needs. `on_the_fly` needs only `start_seconds < elapsed`, which the fact carries. `faceoff` needs the anchor, available through `game['player_shifts']` by exact player, period, start and end, compared on `game['events'][*].chronology`. an ambiguous binding becomes unknown, never known. the spatial rule `_start_before_event` is the right policy and should have one owner. the gate reaches every strength automatically, which matters because 5v5 is the only audited population.

### exact replacement

| item | requirement |
|---|---|
| prepared, coach, factual and capture bytes | unchanged |
| encoder | one gate plus an explicit `DEFINITION` change, which is what produces the new recipe identity; `unavailable:shooter_shift_start` already exists, so no column changes |
| fits | all 20 heads and the 4 final probes |
| scores | all 5 annual artifacts and final-year propagation |
| exchange | execution composition for the three display years; factual inputs reused |
| fixture | fixture states and scores, then a fresh spatial fixture chain; fixture03 becomes development evidence |
| v1-08 | new pins in `spatial_composition.py`, `inputs.json` and the specification |
| audit | `_audit_shift_starts` reads the unchanged prepared fact, so it would still refuse after a correct repair. hard-cut it after the acceptance proof below; a recipe hash alone would not be that proof |

minimal boundary, read-only; no code is authorized. root's direction stands:

1. one policy in the existing context owner, `analysis_context.py`. it is a statement about shift facts against event chronology, and spatial should not depend on execution internals. `_feature_context` applies it once, for fit and score; spatial event members use it directly. an ambiguous binding is unknown, which the existing missing indicator already records. no new module, field or saved record; `iter_neutral_origins` and panels stay as they are.
2. delete the raw-fact audit once corrected inputs are accepted. the consumer then depends on execution's pre-outcome contract, with no per-event refusal list or coverage protocol.
3. acceptance proof, temporary and deleted afterwards: encoder red/green for one bad record of each kind and one valid same-clock faceoff with a proved earlier anchor; a bounded check that all 54 census keys, the two original representatives among them, read unknown from the real encoder over their 54 games; and, per head, unchanged attempt population with `feature_support.unavailable_attempts` no lower than accepted.

that proof plus strict bindings is sufficient on one condition. the execution recipe hash is computed from the `DEFINITION` dict at `execution_design.py:130-131`, not from code, so a gate added without changing `DEFINITION` leaves the hash identical. old states and scores would then pass `execution_state.py:87` and `execution_scores.py:540`, and with the audit gone spatial would consume uncorrected targets silently. the repair must therefore add the policy to `DEFINITION` with a version change, and acceptance needs one negative control: the accepted real state and score manifests are refused by the new readers. that is a manifest read only. spatial then inherits the rejection through `read_execution_scores` in `prepare_spatial`, and the deletion order stops mattering.

the count check is one-sided: the census covers only 5v5 `20212022`. exactness across strengths rests on the single admission point, which is sound because `execution_design.py:264` is the only execution consumer of these fields. the acceptance claim should read "no non-prior shooter start is admitted", not "execution has no future information": only this family was audited. the neighboring `last_faceoff_*` and pre-clock history were read and are ordered correctly.

an earlier draft here proposed a saved refusal list and a permanent equality check. that is unnecessary and withdrawn.

why all 20: all four heads have `shooter_start_zone:*` and `unavailable:shooter_shift_start` active in all five years, so every head trains on the changed rows. `r` and `g` carry the direct outcome path, while `u` and `q` change through the same rows and column means. `g` also depends through setter em, because its responsibilities use the same circumstance logits. the carry ledger then passes each year's actor coefficients into the next year's priors, so a partial chain is not coherent.

measured command time from the accepted artifacts, not a forecast: fits summed 15.8 hours, peak 21.6 gb; scoring summed 26.3 hours, peak 26.1 gb. one heavy job at a time. no real spatial state exists, so nothing real is lost.

correction: an earlier version of this review said execution values sat in the schema8 candidate only, not the active schema7 publication. that was stale. `execution-v1-06/activation.md` at primary `c288b4c` records schema8 publication `9a5b4061` as active, with schema7 as its rollback, through a separately authorized activation. the affected construction is therefore in actively served execution values, not just a candidate. this review makes no rotation or rollback recommendation, and none is assigned; the repair replaces artifacts only, with any later activation a separate decision.

rejected as not fully correct: rescoring with existing coefficients leaves heads trained on these rows. excluding the 54 segments inside v1-08 is cheap and keeps the pins, but it leaves execution's own family and every coefficient unchanged, and other years uncensused. that fallback would need an explicit user decision that those limits are accepted.

unknown: the other four seasons, and every non-5v5 population. the real `20212022` unresolved-binding count was not reported, because the refusal came before coverage was saved.

### judgment on the repair scope

this review concurs with `execution-start-repair-scope.md` on layer and scope: admission at the execution encoder, one eligibility policy in the context owner, preparation and factual bytes retained, the full five-year chain of 20 heads and four continuations, regenerated scores and descendants, and deletion of the raw-fact audit after proof. its statements on `u,q,r,g`, setter em and carried priors agree with this review's independent reading. there is no dissent on the responsible layer.

two items should be explicit before assignment:

1. the scope says the recipe must identify the changed construction, but it does not state the trap. the hash comes from `DEFINITION`, so `DEFINITION` must change, and acceptance should include the negative control that accepted real state and score manifests are refused. without that, deleting the audit can consume old targets silently.
2. the scope asks the source passes to retain counts and located witnesses, while no new persisted ledger is selected. both can hold only if that evidence lives in temporary acceptance output, not in artifact schema or strict readers. it should say so. it is also a better all-strength check than this review's one-sided count, so it replaces that check.

root has accepted both clarifications, and both are now read-clear in the working `execution-start-repair-scope.md`: an explicit `DEFINITION` policy and version change with manifest-only old-state and old-score refusals, and all-strength counts and witnesses in temporary acceptance output with no artifact field, refusal ledger or reader protocol.

three limits carry forward. the scope's "no fitted probability change has been measured" stands; this review's `7.8e-5` is under current coefficients and is not a repaired value. the claim is limited to shooter start admission. the volume probe risk is unaffected: the repair reruns execution, not spatial stopping, so a real final-year probe remains the open test.

## approved start-eligibility repair

status: final source and command reviews complete, [below](#final-source-review), with no blocker to the first fixture fit. the first pass covered the approved scope, both replacement recipe pages, the recipe-gate receipts at `af80dd7` and the working source diff. data read: two already-checked prepared games and saved head metadata and coefficients. no source pass, fit or score.

### corrections to this review

1. `2021020637:210` does not prove that the anchor followed the shot, and "encodes the attempt's own outcome" overclaimed. all ten skaters on the focal row have shifts starting at 1049, and ten other skaters have shifts ending at 1049. the shooter's previous shift ended at 891, 158 seconds earlier. recorded order (shot 210, stoppage 211, faceoff 212) and the shift chart therefore cannot both be right. either the shot followed the faceoff, so `faceoff/offensive` was true pre-event information and `recorded_goalie_stop=true` is wrong, or the shift boundary is wrong, so membership and ages are. idk which. masking is still correct: recorded chronology does not prove the start prior, and that is the selected rule. "non-prior" must keep meaning "not proved prior".
2. the `+0.410`, 19% median figure is withdrawn as a guide to size. `unavailable:shooter_shift_start` and `unavailable:shooter_age_seconds/60` differ on 2 to 15 rows per head-year out of 1,725 to 10,285, afaict all with age known and start unknown. their shared level is identified only as a sum, and each coefficient alone is a ridge split plus those few rows: `20212022` `q` is -0.074 and +0.196, `g` +0.212 and +0.147, summing to +0.359. the masked rows keep age, so they take the start coefficient alone, which had almost no support of its own. only the sum rests on thousands of rows.

### predictor timing

proved from the source, not from counts. take a shooter with a bound shift.

- start strictly before the focal clock: `on_the_fly` cannot flip on the future, because the episode holding the start ends at or after the focal clock, which exceeds the start. a `faceoff` anchor sits on the earlier start clock, so it is earlier in order.
- start on the focal clock: every case is unavailable except a faceoff proved earlier in order. the same-clock reset no longer separates `on_the_fly` from unknown, which was the old mechanism.

corrected after fixture `20232024`: this overclaimed that the mask is decided by records before the attempt. three dependencies on later records remain, and all can only withhold a start, never admit one. `len(matching) == 1` and `tied_unknown` can see a later same-clock record. `order_supported` and an unknown episode end are game-level. the one this review missed is the largest: `individual_participation` omits a whole conflicting component, so a later native row can remove the shift that covers the attempt. [the fixture annual](#masked-population-in-20232024) shows it firing 4 to 120 seconds ahead of the attempts. no source change follows.

mask size: age-known start-unknown rows in `u` were 10, 5, 15, 14 and 5 across the five years. the `20212022` 5v5 census alone adds 54, so at least 84% of that group becomes newly masked rows. `unavailable:shooter_shift_start` therefore becomes a near-dedicated level for its age-known rows, not the general unknown level, which stays on the roughly 2,000 to 10,000 unbound rows. this review first called that a same-clock level; `20232024` shows it also holds omitted-participation rows with ages of 26 to 142 seconds. mechanically this is sound, and the neutral reference does not read it. it means the repaired coefficient will be estimated mostly from these rows, so a large change in it is expected and is not evidence of a defect.

### findings

| id | severity | finding | disposition |
|---|---|---|---|
| s1 | low, cheap now | `execution_composition.py:87` hard-codes `recipe_id` as `experimental-v1:execution-v1-06-1`, and `method_id` keeps `execution-v1-06-<year>`. the replacement publishes the same two strings for a different construction, against the issue's "explicit new identities". `design_sha256` and `evidence` do differ, so this is a false label, not a binding hole. | fixed in `24dec47`: `recipe_id` is now the checked annual recipe name and version, `experimental-v1:execution-v1-05-2`, with a red and green receipt. local `method_id` stays, which is fine now that `recipe_id` differs. |
| s2 | limit | "physical age" overclaims on faceoff rows. on `2021020637:210`, `shooter_age`, all three `opposing_age_*` and the membership come from the same same-clock shifts that the mask distrusts. all 54 census rows have age 0. preserving them is the decided scope, and this review does not reopen that. | acceptance must claim "no unproved start type or zone is consumed", not "no post-event deployment fact". closed: `5153964` says saved shift age and not proved prior, and `dfc97ed` carries that into both hashed definitions. |
| s3 | low | `DEFINITION["history_cutoff"]["unchanged"]` still lists `shift start` and `deployment`, beside a new `shift_start_eligibility` block. it is true of that cutoff only, and the new recipe hash will carry it. | fixed in `dfc97ed`: the entry reads `deployment outside start-type/zone eligibility` and `saved shift age`. |

### final source review

reviewed `dfc97ed`, with production unchanged through `683fa4b` at analysis subtree `c2412ac`. observer `b3811c4b`, hook check `69f88c50`. both recipes reproduce from the commit: execution `47691110`, spatial `04a9c15d`.

verdict: **production source is clear**, and the one command-book blocker it found is closed. no fit or score ran before that closure.

| id | severity | finding | required |
|---|---|---|---|
| b1 | blocker before any execution fit | neither `real-fit-commands.md` nor `fixture-fit-commands.md` invokes `consumed_start_check.py`. all ten execution fit blocks still run plain `uv run ... hockey-stats-analysis fit`; `e6d64d7` wrapped only the ten score blocks. so the 54-key barrier does not exist at fit, the fit half of the comparison that `replacement-product-recipes.md` requires is never produced, and fit-side head populations do not exist. an unwrapped fit cannot recover them without the separate pass the scope forbids. | closed in `bd326af`, [verified below](#final-command-review). |
| o1 | recommended, not required | the oracle gates admission only. eligible rows wrongly masked pass silently. in a mutation on real rows, 69 masked eligible `on_the_fly` rows raised no error and appear only as `masked_on_the_fly`, inseparable from true masks. 43 masked eligible faceoffs raised no error but do show in `withheld_earlier_anchor`. production is correct here by reading and by the two-game run. | closed in `9bf7ad6`, observer `286b34dd`: availability now equals the oracle for both kinds. this review reran its own mutation on real rows, and all 69 `on_the_fly` and all 43 faceoff over-masks are now refused, while the corrected encoder passes the 208 attempts and the old encoder is refused on exactly the two originals. the hook check equals its saved green output. |

two originals, run independently. the actual `_feature_context` from `78a0727` and from `dfc97ed` ran on every attempt of both games, 208 in all. this review's oracle finds the shift by clock containment and the anchor by scanning same-clock faceoffs. it reads neither deployment start facts nor `event_source_index`, so it shares no binding code with production.

| oracle class | attempts | old | new |
|---|---|---|---|
| start before the clock | 194 | available | available |
| start before the clock | 12 | unavailable | unavailable |
| same clock, later faceoff (`2021020637:210`) | 1 | `[1,0,0]`, flag 0 | unavailable, flag 1 |
| same clock, no faceoff (`2021020002:196`) | 1 | `[0,0,0]`, flag 0 | unavailable, flag 1 |

exactly those two rows change. zero non-start features differ on any attempt, including age. old-encoder rows fed through the observer are refused on exactly those two keys, with the right messages, and new rows pass. a rerun of the hook check equals its saved green output.

production and its boundaries:

- the gate sits inside `_feature_context`, so `build_resolution_witness`, which swaps the shooter at `execution_design.py:1006`, passes through it.
- the anchor comes from `player_shifts` by exact player, period, start and end. deployment's `shift_source_index` could not have served: it is the native index, 215 against coalesced 210 here. mismatched kind or zone, a missing anchor, or no focal clock or order fails closed.
- the spatial call is equivalent to the removed `_start_before_event`, and no `analysis/src` reference to the audit survives. only superseded `var/` scripts mention it.
- removing the audit leaves no old path. `prepare_spatial` reads through `read_execution_scores`, `read_panel` demands a checked artifact, and composition uses the same reader. the recipe gate refuses old manifests there.
- `prepare_execution` runs once per command, from both fit and score, and the wrapper resolves it at call time with no process pool. so the observer's hooks reach both, and its exclusive write cannot fire twice.
- `_head_design` returns `head`, `rows` and `keys`, every context produces a predictor, and the observer's key equality would refuse any drift.
- `git_dirty` reads `analysis/` only, so uncommitted docs do not touch provenance. worktree and primary venvs agree: python 3.14.8, numpy 2.5.3, scipy 1.18.1.

observer limits, accepted:

- no shared predicate, as stated. it does share `history.cutoff` and a textual copy of the binding filter with production. this review's oracle tests the binding on two games only.
- contexts after the first head construction are not observed. the resolution witness is one of them, and it uses the same function.
- `masked_faceoff` and `withheld_earlier_anchor` both include zone-unavailable faceoffs, which were already unavailable. neither is a pure timing count. the exact count of newly masked rows per head is the rise in saved `unavailable_attempts` against the original head metadata. `unavailable:on_the_fly` is all newly masked, so the remainder is newly masked faceoffs.

broadening the withheld counter: **no. this review withdraws its request.** the broader population cannot be read from the current counter: when a later same-clock faceoff breaks `len(matching) == 1`, the shift saves no kind and no anchor, so zero does not size it. but that path can only withhold a start, the contract concerns admission, and no count could change a decision, because no threshold or production broadening is authorized. acceptance should state it as a limit: a later same-clock record can withhold an earlier-anchored start, unsized.

after each accepted annual, this review will diff the saved `design` blocks against the originals, with no new pass: `columns`, `means` and `active` must match, and every `feature_support` entry except the three start columns must be equal. that is the all-strength proof that nothing else moved.

not established: anything beyond two games. all-strength populations, the other four seasons, fit and score parity, and every numerical effect wait for the runs. this review did not rerun `var/v1-08-execution-start-checks.py`; its own run replaces that for the two originals only. the volume probe risk is unaffected.

### final command review

reviewed `bd326af`, with the analysis subtree still `c2412ac`. digests match root's: receipt `c38950f7`, fixture book `d66e4779`, real book `4b421777`, first command `717f7b28`, observer `286b34dd`. the campaign directory does not exist.

verdict at that point: **no blocker to the first fixture fit.** b1 is closed. one finding below had to close before the first score, and it has.

checked directly, not from `observed-fit-book-checks.json`:

- both books parse to ten blocks, and all twenty pass `/bin/sh -n`.
- all ten execution blocks run the observer with the pinned python. each has its own `fit-<season>-source-check.json`, listed in the occupied-path guard, and pins subtree `c2412ac` and observer `286b34dd` before launch.
- `--known-census` appears on real `20212022` only, and that census file digest is `6fd06ffb` as pinned. without it the observer refuses.
- all twenty ordinary tails equal the `argv` in the original `replacement-fit-preparation.json`.
- the ten spatial blocks are byte-identical to the retained historical books, whose digests match that receipt. they consume the new campaign's `scores/<season>`.
- each `--previous` is exactly the prior year's `--out` in its own family and purpose, and first years have none.
- a dry run through the real observer `main`, with the cli stubbed and output in scratch, parsed all ten execution commands, handed the exact tail to the cli, and resolved the right purpose, season and census size. nothing reached the campaign path.
- the check file's parent exists once the block's `mkdir -p` has run, so the exclusive write cannot fail after preparation.
- failure paths are sound. `analysis_cli` turns an observer refusal into exit 1, and the observer's `finally` writes `source_construction_incomplete`. `_head_design` is called only in `prepare_execution`, so no late head hook can fail after a solve. the resolution witness calls only `_feature_context`, which is a pass-through by then.
- under the block's runtime, `hockey_stats` resolves to this worktree with a relative `PYTHONPATH`, and both recipes reproduce. `implementation_identity` reports `bd326af` with `git_dirty` false, despite this uncommitted review.

| id | severity | finding | required |
|---|---|---|---|
| c1 | before the first score, not before any fit | the ten score blocks carry no observer pin and no subtree pin, unlike the fit blocks. the observer is untracked under `var/`, and its report does not record its own digest. three versions of it are on record today, so a stale copy at score would go unseen, and the fit and score reports would then compare different oracles. `implementation` does bind production in the score manifest, so this concerns the observer only. | closed in `08f2120`, [verified below](#first-fixture-annual-and-score-guards). |

not established: the real runtime path has not executed at all. these checks prove the commands are well formed, not that they succeed. the real wrapped path first runs in the fixture fit, and that first `fit-20212022-source-check.json` is the first population evidence.

### first fixture annual and score guards

reviewed `fixture/execution/20212022` and `fit-20212022-source-check.json`, launched at `d181fcd`, with score books fixture `e17826b4` and real `747ce2fa` at `08f2120`. saved artifacts only, with no source pass.

verdict: **the first annual passes this review, and c1 is closed.** nothing here stops the next fixture annual or the first score. release remains root's.

identity: exit 0, 22.31 seconds, 921,845,760 bytes peak rss. launch records show subtree `c2412ac`, an empty analysis status and observer `286b34dd`. the manifest states recipe `47691110` and commit `d181fcd`, clean. the strict reader accepts the state: four heads complete, resolution `not_applicable`. the same reader refuses the original fixture state, `execution recipe definition differs`.

source check: status `passed`, written after design construction and before the solve. 771 contexts: 275 eligible faceoff, 420 eligible `on_the_fly`, 23 `None` and 53 `unknown`. all five eligibility counters are zero in every head. head populations 771, 618, 439 and 335 match `head_admission`. the observer's unavailable rows, 76, 58, 44 and 33, equal saved `unavailable_attempts` in all four heads.

diff against the accepted original, `v1-05-stopping15-checks/chain-01/20212022`, digest `aeac9f05`:

| compared | result |
|---|---|
| `columns`, `means`, `active`, `size` | equal in all four heads |
| `feature_support` | no entry differs |
| `coverage.json` | no differences |
| coefficient arrays | **byte-identical** in all four heads |
| every other head field | equal, except `fixed_transforms/shift_start` text and `diagnostics/wall_seconds` |

the result is what the source implies. this annual has no masked row, so the objective is unchanged, and an identical objective with deterministic numerics gives identical bytes. it is a strong regression proof: the repair moved nothing on rows it should not touch, and the new recipe text is the only other change.

limit, and this matters for reading the fixture chain: **this annual does not exercise the mask.** zero masked and zero same-clock admitted rows means the changed path never ran at population scale. at the real census rate, 771 attempts expect about 0.35 masked rows, so zero is unsurprising and proves nothing about masking. if the other four fixture annuals are also zero, all twenty fixture heads are regression evidence only. real `20212022`, with its 54-key barrier, then becomes the first population test of the mask. its source check is written before the solve, so its counts are readable before the expensive part runs.

score guards: all sixteen blocks pass `/bin/sh -n`. all ten score blocks pin subtree `c2412ac`, clean analysis status, observer `286b34dd` and the expected recipe, and all five launch receipts and the check path sit in the occupied-path guard. each `--state` and `--out` is its own purpose and season in the new campaign, and `--known-census` stays on real `20212022` only. all sixteen tails equal the original `replacement-product-preparation.json` argv, including the six compose and publish blocks. their byte identity is not independently proved, because the old books are not retained. a dry run of `score-20212022` through the real observer `main`, with the cli stubbed and output in scratch, handed over the right tail and resolved season from the new state.

### fixture annual diffs

each row is a saved-artifact diff against the accepted original annual in `chain-01`, with no source pass. "byte-identical" covers every head's coefficient array. a row also means: `columns`, `means`, `active`, `size`, every `feature_support` entry, `coverage.json` and every other head field are equal, except the `shift_start` recipe text and `wall_seconds`. the strict reader accepts the new state and refuses the original, and observer unavailable rows equal saved `unavailable_attempts`.

| annual | original | new | attempts `u,q,r,g` | masked | coefficients | previous |
|---|---|---|---|---|---|---|
| `20212022` | `aeac9f05` | `93478145` | 771, 618, 439, 335 | 0 | byte-identical | none |
| `20222023` | `52a2b0fa` | `7ca3062b` | 585, 434, 321, 235 | 0 | byte-identical | exact: new `93478145` |

| `20232024` | `e2ad6fda` | `85438d84` | 605, 448, 312, 250 | 7, 6, 4, 3 | moved: max 0.040, 0.011, 0.053, 0.063 | exact: new `7ca3062b` |
| `20242025` | `1a69f2b4` | `d94dba43` | 1,062, 755, 494, 390 | 0 | moved through history: max 0.0032, 0.0047, 0.0049, 0.0033 | exact: new `85438d84` |
| `20252026` | `87124257` | `52239766` | 1,068, 761, 508, 401 | 0 | moved through history: max 0.0030, 0.0069, 0.0083, 0.0033 | exact: new `d94dba43` |

the first two rows have all five special counters at zero, across 1,356 attempts. `20232024` differs from the rule above as follows, and every other field in that rule still holds.

- `feature_support` changes only on the three start columns. `coverage.json` has exactly 24 differences: three columns, two fields, four heads.
- newly unavailable rows are 7, 6, 4 and 3, which equal the observer's `unavailable:faceoff` per head, against `48→55`, `36→42`, `26→30` and `20→23` in saved metadata.
- the largest coefficient moves are `unavailable:shooter_shift_start`, its near-collinear `unavailable:shooter_age_seconds/60`, and `shooter_start_zone:defensive`, as [the indicator correction](#corrections-to-this-review) predicts. all seven rows are defensive starts.
- objectives rise by 0.0030, 0.0062, 0.0481 and 0.0184, as expected when information is removed.
- history: ledger ids, roles, ages and seasons are equal, with median change 0 and maximum 0.0033, 0.0070, 0.0083 and 0.0033. later fixture annuals will no longer be byte-identical.
- `selected_start` flips in `u`, `r` and `g`, but both starts tie to four decimals in old and new fits, so the flip carries no signal.

`20242025` has all five counters at zero, and its design, `feature_support` and `coverage.json` equal the original, so every change comes through carried history. the largest coefficient moves are actors such as `8481559`, `8480002` and `8479407`, median change is about `1e-7`, and prior means differ by at most 0.0050. some ledger maxima equal `20232024`'s exactly, 0.0070 in `q` and 0.0083 in `r`, because actors absent this year keep their last value, as the history rule says. `selected_start` flips in `r` and `g`, as ties again.

`20252026` likewise has all five counters at zero and an equal design, `feature_support` and `coverage.json`. its largest moves are again actors, such as `8481559` and `8482684`, with median change near `1e-7`, and ledger ids are equal. `selected_start` flips again in three heads, which this review did not re-examine beyond the first start's objective.

### fixture continuations

the four continuations pass. fixture execution therefore has all twenty heads and all four continuations complete, with this review's findings on each year above.

recomputed from saved `heads/*.npz` and `resolution/*.npz`, with no solve:

| head | coefficient max | coefficient l2 | saved maximum probability change | original fixture |
|---|---|---|---|---|
| `u` | `5.63e-8` | `2.39e-7` | `4.10e-8` | `3.37e-8` |
| `q` | `7.29e-9` | `1.78e-8` | `1.59e-8` | `1.67e-7` |
| `r` | `4.05e-8` | `1.47e-7` | `2.46e-8` | `2.19e-7` |
| `g` | `4.42e-8` | `1.60e-7` | `7.76e-8` | `6.04e-8` |

coefficient maxima and l2 norms reproduce the saved comparisons to the printed digits. all four probability changes sit near 100 times inside the `1e-5` budget, and root's quoted figures match. baseline `3cad4a5c` and all four probe files match their saved digests. each probe used `ftol 1e-16`, `gtol 1e-7` and the literal em tolerances. the selector equals the original exactly: 256 probes and 40 requirements, 38 actual and 2 fixture, with none unavailable and no withheld contexts. evaluated origins are 117,118 and branches 900,394.

two limits. **probability changes were not recomputed here.** they need the predictors, so this review checks the coefficient arithmetic and the bindings, and reads the probability maxima from the saved comparison. and these are 256 selected probes, not every row. [the final score](#final-score-and-propagations) covers every panel row, but only as sums. the continuations also stop on `ftol`: tightened gradients stay between `1.6e-6` and `4.4e-6`, above `gtol`, and `r`'s rises slightly. that is the accepted policy, and it reports sensitivity, not distance to an optimum.

the fixture chain never exercised the timing mask. 4,091 attempts produced seven masks, all omitted participation. at the real census rate, about 1.9 timing rows would be expected, so zero is unsurprising and proves nothing.

### masked population in `20232024`

verdict: **the seven masks are correct, they are not timing failures, and production should stay as it is.** the third annual passes.

saved facts, from `fit-20232024-source-check.json` and one witness game. every masked row is at strength `6,5,0` in `2023020955`, period 3: source indices 318, 319, 325, 336, 337, 338 and 339, for shooters `8479407`, `8482684` and `8480002`, at clocks 1078 to 1194. all carry raw `faceoff/defensive`, start 1052, anchored on faceoff 317. the start is earlier than every attempt by clock and by order, so none is a timing case. `masked_faceoff` and `unresolved_binding` are both 7 and `masked_on_the_fly` is 0.

cause: six players in that period, five of the extra-attacker unit and one home skater, have a native row reaching 1200 (`[1052,1200]` for all three shooters) and a short `[1198,1200]` row. those overlap strictly, so `individual_participation` conflicts the component and preparation omits it, with `overlapping_individual_participation` in the game issues. no `player_shifts` row covers the attempts, `active` is empty, and deployment keeps the `_deployment` fallback fact. the conflict begins 4 to 120 seconds after the attempts.

why the mask stands:

1. it withholds and cannot admit, and the hashed rule says a missing binding is unavailable.
2. it agrees with the preparation owner. v1-01 finding r6 chose to omit the whole component, and its review accepted that this also drops spans the conflicting rows agree on. the old encoder was consuming a start that preparation disowns, through the fallback.
3. it agrees with spatial, whose member start reads the same `player_shifts` and would be unknown here, though these `6,5,0` rows are outside its 5v5 panel.
4. the alternative, admitting any faceoff whose start clock precedes the attempt, is simple and timing-safe. but it would re-admit starts from components whose conflict may overlap the start itself, and it would split execution from spatial on the same facts.

what must change is wording, not code. "masked" now has two classes: not proved prior, and omitted participation. no record should describe all newly unavailable rows as timing failures. `saved shift age` survives on these rows from the same disowned native row, within the s2 limit.

two limits on reading this:

- **the timing mask is still unexercised in any fit.** this annual is not regression-only, but all seven rows took the binding branch. real `20212022` remains the first population test of timing.
- **the real size of this class is unknown, and the fixture cannot estimate it.** fixture games include selected edge cases, so 7 of 605 is not a rate. no saved real count exists. a conflicted player loses `shooter_prefix_toi` for the game, and all seven rows do, so the class is bounded above by saved prefix-unavailable rows in real `u`: 3,502, 1,397, 6,084, 8,760 and 2,634 by year, up to 5.7%. that bound is loose, and it does not exclude the class exceeding the 54 timing rows. this review's recommendation holds at the bound. real `unresolved_binding` is written when design construction ends, so it should be read and reported when that file appears, with no threshold. the solve may already be running; [no pause is needed](#proposed---review-source-pause).

`withheld_earlier_anchor` is 0 here although a later record did withhold these starts. that confirms a zero there sizes nothing. `unresolved_binding` is the counter that sees this class.

### proposed `--review-source` pause

recommendation: **do not add it. this review withdraws its "before the solve" wording, which prompted the proposal.** the requirement is to read and report the count, not to gate on it.

a pause is a gate with no decision at it. no threshold is authorized, and this review's recommendation holds at the upper bound, so no reading would justify withholding the token. the automatic barrier that matters already exists: the 54 known keys are enforced before head construction.

what the pause would cost:

- it changes observer `286b34dd` at the most expensive command, so real would run a path no fixture year exercised, plus new pins and review.
- a mistyped token or lost stdin aborts after design construction, which took most of the 4,447 seconds of the refused real pass.

reading the file as it appears loses nothing. this review first said the solve runs for hours, which overstates the first annual: the original `20212022` took 6,915 seconds of design and 1,885 of solve, about 31 minutes. that is still ample time to read a report, and later years are longer. root can stop it at any time, at the cost of a new check path.

if root keeps the flag anyway, one constraint applies. root's timer claim is right for fit: `design_wall_seconds` and `fit_wall_seconds` are measured inside the hook, so they exclude the pause. it is false for score, where `execution_scores.py:366` times the whole `prepare_execution` call, so a pause would inflate `design_wall_seconds` and `wall_seconds`. the flag must be fit-only.

### first two scores

`20212022` and `20222023` pass. all eight fit and score parity fields match, at 771 and 585 contexts. against `current-02` originals, **72 of 73 members are byte-identical in both years**, including `events.jsonl`, `people.jsonl`, every panel and every array. the only difference is `shares.jsonl`.

| year | rows | differing | largest change | per-event closure drift | per-recipient total drift |
|---|---|---|---|---|---|
| `20212022` | 9,187 | 5,846 | `2.08e-17` | `3.1e-17` | `1.4e-16` |
| `20222023` | 7,090 | 4,452 | `2.08e-17` | `1.8e-17` | `1.0e-16` |

only `goals` differs. ulp and relative measures are meaningless here because some shares are near zero, so absolute size is what counts.

root's explanation holds, by elimination. `b723c28` replaced the loop over pairwise differences in `execution_shapley` with `four_group_allocation`, a weight matrix over the 16 values: the same algebra with different rounding. saved inputs are unchanged, because coefficients are byte-identical and all 16 `coalition_goal_mass` values are equal. nothing else in the path changed: the `execution.py` diff is that call plus `iter_neutral_origins`, and the `execution_scores.py` diff touches read paths only. replaying old, new and 24-order allocation on the saved masses gives gaps up to `3.5e-17`, the same scale. **this is not a byte proof.** saved masses are already integrated, and exact reproduction needs a rescore, which this review did not run and does not recommend. no decision depends on it.

consequence: old-against-new score comparisons must treat `shares.jsonl` by absolute size, and composed values may differ near `1e-16` from this alone.

### third score

`20232024` passes. it is the first score whose inputs differ from the original, so unlike the first two it is not a regression check.

identity: manifest `fb1d1ad1`, exit 0. it binds state `85438d84` and recipe `47691110`, launch records show subtree `c2412ac`, clean status and observer `286b34dd`, and the implementation is `41c018b2`, clean. the strict reader accepts it and refuses the original. all eight parity fields match across 605 contexts.

against the original `current-02/scores/20232024`:

- 59 of 73 members are byte-identical, including `coverage.json`, `people.jsonl`, `coach_ids.jsonl` and every panel `jsonl`. event identity, labels, status and reasons are equal on all 715 events, 605 complete and 110 excluded. the population has not moved.
- 14 members differ, all expected: `events`, `maps`, `projections`, `setters`, `shares` and the nine panel arrays that hold events. every empty panel is byte-identical.
- summed neutral mass moves 26.3104 to 26.3149, +0.017%, and actor mass 26.4037 to 26.4116, +0.030%.

| rows | count | neutral change |
|---|---|---|
| the seven masked rows | 7 | +3.1% to +7.6% |
| known defensive faceoff, `2023020955` | 13 | median +3.9%, range +2.2% to +4.9% |
| known neutral or offensive faceoff, `2023020955` | 36 | medians near 0, within 0.54% |
| `on_the_fly`, `2023020955` | 38 | median +0.01%, within 0.76% |
| unavailable start, `2023020955` | 39 | about -2.3% to -3.5% |

all rows, excluding the seven: median 0.32%, 99th percentile 4.2%, maximum 4.9%, on `2023020955:93`.

this review first guessed that the 4.9% row reflected the shared unavailable level. that was wrong: row 93 is a known defensive faceoff start at 5v5. its movement comes from `shooter_start_zone:defensive`, whose coefficient moved -0.023 in `u`, -0.040 in `r` and +0.057 in `g`, because all seven masked rows were defensive starts. the other two zone contrasts barely moved. unavailable rows move because the `S+A` sum moved +0.026, +0.006, +0.033 and -0.049.

reading: masking rows also moves every row that shares their contrast. seven rows did that here, in a 605-row sample with few defensive rows, so these percentages say nothing about real size. no fitted real change has been measured.

### fourth score

`20242025` passes. manifest `1f6ac613`, exit 0, binds state `d94dba43` and recipe `47691110`, launch records are clean, the strict reader accepts it and refuses the original, and all eight parity fields match across 1,062 contexts.

against the original `c4a0b4b2`, 61 of 73 members are byte-identical. the 12 that differ are `events`, `maps`, `projections`, `setters`, `shares` and the seven panel arrays that hold events, and every empty panel is identical. identity, labels, status and reasons are equal on all 1,092 events, 1,062 complete and 30 excluded.

this year has no masks, so the change is carried history only, and it is small: neutral mass +0.0010%, actor mass +0.0017%. per-event neutral change has median `3.8e-5`, 99th percentile `2.9e-4` and maximum `8.2e-4`. actor change reaches `2.8e-3` on `2024020001:25`.

### final score and propagations

`20252026` passes, and fixture execution is complete: twenty heads, four continuations, five scores and four propagations. nothing here stops execution composition or the first spatial fit. release remains root's.

identity: manifest `80f61f0d`, exit 0, binds state `52239766` and recipe `47691110`. launch records are clean, the implementation is clean, the strict reader accepts it with resolution `passed` and refuses the original, and all eight parity fields match across 1,068 contexts.

against the original `e039601e`, 57 of 73 members are byte-identical. the 16 that differ are `events`, `maps`, `projections`, `resolution.json`, `setters`, `shares` and the ten panel arrays that hold events. every one of the 22 empty panels is identical. identity, labels, status and reasons are equal on all 1,101 events, 1,068 complete and 33 excluded. change is history only: neutral mass +0.0001%, actor mass +0.0013%, per-event neutral maximum `4.1e-4`, actor maximum `2.1e-3`.

propagation, recomputed from saved rows:

| head | actual | synthetic | stage | per100 | map l1 | largest panel sum change |
|---|---|---|---|---|---|---|
| `u` | `3.87e-8` | `2.31e-8` | `6.65e-9` | `2.69e-8` | `2.69e-8` | `5.58e-8` |
| `q` | `1.14e-8` | `9.38e-9` | `1.19e-8` | `2.54e-8` | `2.54e-8` | `5.38e-7` |
| `r` | `1.16e-8` | `5.40e-9` | `6.23e-9` | `1.81e-8` | `1.81e-8` | `1.46e-8` |
| `g` | `6.40e-8` | `7.21e-9` | `5.59e-9` | `9.00e-8` | `9.39e-8` | `1.00e-6` |

- per100 and map l1 maxima recompute exactly from the 38 pair records in every head, and all 38 pairs pass. root's figures match. all are far inside `1e-5`, `.001` and `.001`.
- all 32 panels are present in every head, 10 with events, totalling 1,068. each saved baseline equals the sum of that panel's saved event masses, and each change equals variant minus baseline, with no mismatches.
- the 256 keys equal the fit's frozen selector. keys, witnesses, pairs and all 45 requirements, 40 selected and 5 unavailable, equal the original. the 40 selected rows name 38 distinct pairs. expected-sum baselines equal saved events, and there are no danger crossings.
- baseline, annual and all four probe digests match the fit.

a correction on coverage. this review called these propagations the all-event check, and root's note says all-event too. **that is true only as sums.** every panel row is re-evaluated, but what is saved is panel masses and the 38 focal pairs. per-event maxima cover the 256 keys and the synthetic rows, and the receipt itself says there is no seasonwide actor or all-player error bound. no per-event bound across all rows exists, and acceptance should not claim one.

a recompute of mine first showed 2 to 10 panel mismatches per head. that was my own error, comparing an absolute value with the signed `uqrg_change`. corrected, there are none.

none of this tests a real scale. the fixture's gradients and solver work are small, and [the volume risk](#volume-probe-may-fail-its-fixed-budget-at-real-scale) concerns spatial at real size.

### first fresh spatial annual

`fixture/spatial/20212022` passes. the next spatial year is clear from this review; release remains root's.

identity: manifest `91ccca92`, exit 0, no previous. launch records show subtree `c2412ac`, clean status, design recipe `04a9c15d`, and valued `78e029e0`, which is the accepted new score. the strict reader accepts the state, and refuses the fixture03 original with `spatial fixed design definition differs`.

against preserved `fixture03/20212022`:

| member | result |
|---|---|
| `design.npz`, all 16 arrays | byte-identical |
| `heads/volume.npz`, `shape.npz`, `quality.npz` | byte-identical |
| `projections.npz`, `projections.jsonl`, 224 rows | byte-identical |
| `adjustments.jsonl`, 448 rows | byte-identical |
| `coefficient-support.jsonl`, 1,344 rows | byte-identical |
| `reference.json` | byte-identical |
| `coverage.json` | differs only by the removed `event_shift_start_audit`, overall and in seven games |
| `design.json` | the same removal, plus `event_shift_start` text, recipe digest, derived `design_sha256`, and `valued` path and digest |
| `heads/*.json`, `diagnostics.json` | differ only in wall seconds and peak rss |
| `manifest.json` | differs in `design_identity`, commit, `valued`, member digests that follow from the above, and resources |

this is the sharp check root expected. the rate recipe, basis and fitted values are unchanged, so the audit removal and the shared predicate changed no number. the 5v5 panel is byte-identical to the original, and this year's only score difference is `shares.jsonl`, which spatial's byte-identical design confirms it does not consume here.

limit: like the first execution annuals, this is regression evidence only. `20232024` is the first spatial year whose targets differ.

### second fresh spatial annual

`fixture/spatial/20222023` passes, with the same byte-level result as the first. manifest `8444b539`, exit 0, valued `69bf4a4d`, previous exact `91ccca92`, launch records clean. the strict reader accepts it and refuses the fixture03 original.

against `fixture03/20222023`: `design.npz`, all three head arrays, `projections.npz`, `projections.jsonl` with 179 rows, `adjustments` with 358 rows, `coefficient-support` with 1,074 rows and `reference.json` are byte-identical. head metadata differs only in wall seconds and peak rss, so history, ledgers and priors are equal. `coverage.json` differs only by the removed audit, `design.json` by that removal plus the recipe text and digests and the `valued` binding, and `manifest.json` also by `previous`.

still regression evidence only. `20232024` is the first spatial year with changed targets, and the next comparison should expect differences there.

### third fresh spatial annual

`fixture/spatial/20232024` passes, and root's expectation holds exactly: volume and shape are invariant, and only quality moves. the next year is clear from this review; release remains root's.

identity: manifest `000b36e4`, exit 0, valued `fb1d1ad1`, previous exact `8444b539`, launch records clean, rate recipe and basis unchanged. the strict reader accepts it and refuses the fixture03 original.

| member | result against `fixture03/20232024` |
|---|---|
| `design.npz` | 15 of 16 arrays byte-identical. only `neutral_goal_probability` changes, maximum `0.0058` |
| annual offsets | `r` and `pi` equal. only `qbar` changes, at most 3.0% |
| `heads/volume`, `heads/shape` | arrays byte-identical. metadata differs only in wall seconds and peak rss |
| `heads/quality` | coefficients move at most `0.0040`, ledger ids equal |
| `projections.npz` | every `attempts` map byte-identical in value. `xg` rates move at most `5.7e-4`, adjustments `2.1e-3` |
| `projections.jsonl` | only the four `xg` fields for each role and `reference_id` change |
| `adjustments.jsonl` | `attempts` and all other fields identical. only `xg` changes |
| `coefficient-support.jsonl` | byte-identical |
| `coverage.json` | apart from the removed audit, only `neutral_chance_mass` changes |
| `reference.json` | only quality centers, `qbar`, quality predictor and the digest |

targets, recomputed from the accepted score. reading `fb1d1ad1` through the strict reader and `iter_neutral_origins`, all 453 events match `design.npz` byte for byte in probabilities, cells and weights.

accounting: neutral mass moves from 16.957893137 to 16.959320058, and that value equals both `coverage.json` and the composed `interval_fact` total reviewed above. spatial and composition therefore agree on the same targets. `xg` adjustments close on all 402 rows, with largest gap `8.9e-16` and largest residual `7.6e-17`.

the effect size again comes from the seven masked rows through the defensive contrast, in a 453-event sample, so it says nothing about real size. the quality objective rises from 69.4704 to 69.4732, and its final gradient is `1.7e-5`, up from `5.3e-6`. calibration bins barely move.

### fourth fresh spatial annual

`fixture/spatial/20242025` passes, and the final spatial fit is clear from this review. release remains root's.

identity: manifest `c9fe5fb2`, exit 0, valued `1f6ac613`, previous exact `000b36e4`, launch records clean. the strict reader accepts it and refuses the fixture03 original.

the pattern from `20232024` holds, at about a hundredth of the size, because this year has no masks and its targets move only through execution history.

- `design.npz`: 15 of 16 arrays byte-identical. `neutral_goal_probability` moves at most `3.3e-5`. `r` and `pi` are equal, and `qbar` moves at most 0.02%.
- volume and shape: arrays byte-identical, and metadata differs only in wall seconds and peak rss, so their priors and ledgers carry no change.
- quality: coefficients move at most `2.2e-4`, median `1.8e-9`, ledger ids equal. for the first time its priors differ, carrying `20232024`'s quality change forward.
- projections: zero change in every `attempts` map. `xg` rates move at most `3.4e-5` and adjustments `5.6e-5`. only the `xg` fields and `reference_id` change. `coefficient-support.jsonl` is byte-identical.
- `coverage.json` changes only in `neutral_chance_mass`, apart from the removed audit.

targets: through the strict reader, all 665 retained events match `design.npz` byte for byte. neutral mass moves from 29.637485997 to 29.637835476, equal to `coverage.json` and to the composed `interval_fact` total. `xg` adjustments close on all 452 available rows, with largest gap `1.8e-15`.

### final fresh spatial annual and probes

`fixture/spatial/20252026` and all three probes pass. the fresh fixture spatial chain is complete: fifteen heads, three continuations, five annuals. combined selection and composition are clear from this review; release remains root's.

identity: manifest `af7cf925`, exit 0, valued `80f61f0d`, previous exact `c9fe5fb2`, launch records clean. the strict reader accepts it and refuses the fixture03 original. probe digests match root's: baseline `521e21b6`, rows `050b4713`, requirements `15dc751f`.

annual: the same shape as `20242025`. 15 of 16 design arrays are byte-identical, and `neutral_goal_probability` moves at most `2.5e-5`. `r` and `pi` are equal. volume and shape head arrays are byte-identical. quality coefficients move at most `1.9e-4`. `attempts` maps have zero change, and only `xg` fields and `reference_id` change. all 358 retained events match `design.npz` byte for byte through the strict reader. neutral mass moves from 15.208292477 to 15.207888585, equal to `coverage.json` and the composed `interval_fact` total. `xg` adjustments close on all 288 available rows, with largest gap `1.3e-15`.

probes: frozen `rows.json` and `requirements.json` are byte-identical to fixture03, and so are the volume and shape probe coefficients. only the quality probe moves, as it should. all three comparisons report `passed`, with no failures.

replay from raw saved arrays, with this review's own math and no solve:

| head | standardized scalar | standardized map | 1000-minute goals | coalition scalar | coalition map |
|---|---|---|---|---|---|
| volume | `5.93e-6` | `5.93e-6` | `3.32e-6` | `5.66e-5` | `5.66e-5` |
| shape | `1.11e-8` | `2.69e-6` | `1.35e-7` | `1.04e-7` | `2.28e-5` |
| quality | `3.16e-7` | `3.40e-7` | `1.91e-6` | `2.04e-6` | `2.39e-6` |

all 15 agree with the saved maxima to the printed digits. quality probability replays to `8.628904e-8` at the saved location, subset 14 and cell 590 for `8476882`. a first replay gave `8.49e-8`, because it read only the complete predictor; the saved quantity covers all 16 coalition subsets. the other saved maxima, including allocation and shape probability, were read and not replayed. all are within limits.

volume coalition sits at 57% of its `1e-4` budget, unchanged from fixture03. that is a fixture result. [the real-scale risk](#volume-probe-may-fail-its-fixed-budget-at-real-scale) stays open until a real final-year probe.

### combined fixture composition

`fixture/results` passes. manifest `a8d2f4ba`, base `82f0b55f`, selection `bdee26d0` with all five accepted state digests, producer `cf136b7`, clean, three seasons and 30 family rows. publication is clear from this review; release remains root's.

this review reran its own composition replay from raw member files, against the new base and the accepted states.

- preservation: all 45 non-owned members, 789,227,228 bytes, and every non-spatial family descriptor are byte-identical to `execution-results`. `people`, `sources` and `supports` are identical. the nine base methods are identical, and three spatial methods are added.
- native values: every provided 5v5 cell equals the state's `projections.npz` exactly. scalars equal `projections.jsonl`.
- display transport: an independent mapping of native centers into their containing display cells, plus the declared pooling, reproduce every display mass, with error 0. display and native scalars agree within `2.8e-14`, and density is exact.
- adjustments: published values equal the saved decomposition, closing within `4.3e-14`.
- joins: `published_only` and `fitted_only` are empty in all three seasons, at 201, 245 and 277 skaters. every non-5v5 row stays `not_computed` with its `v1-09` explanation.
- evidence: each spatial method binds its state manifest, `coefficient-support.jsonl` and composition receipt, and all digests were recomputed from disk. `fit_seasons` are correct.

against fixture03's composition: row counts are equal, and only `xg` content changes. no `attempts` map or adjustment row changes at all. prior-only and zero-time rows are 152, and no-exposure adjustment rows 608, all unchanged in support.

the spatial `recipe_id` stays `experimental-v1:positive-spatial-v1-08-1`. unlike s1, this label is accurate: it names the rate recipe, which is unchanged. design and target changes are carried by `design_sha256`, `evidence` and `inputs`. fixture03 was served only as an isolated candidate, publication `e5118eea` on port 3398, and was never activated as the live publication. the identities above still separate the two.

### saved fixture publication

candidate `fixture/candidate/player-analysis.sqlite` passes, read immutably, with no source pass, fit or rescore. publication `e7428c18-c105-4a51-bc57-af8d47899aae`, digest `95ee3f1c`, recomputed from disk, 1,369,219,072 bytes. no sidecar was created and the digest is unchanged after reading. this covers the saved database only: server, api, browser and detached controls are separate evidence.

- structure: `quick_check` ok, no foreign key violations, journal `delete`, schema 8. all 80 schema objects are identical to the fixture03 candidate's, and all 39 tables have equal row counts.
- binding: `verification.json` binds result `a8d2f4ba` and observed `24cda3b5`. its integrity, foreign key, read-back and per-season conservation checks all report passed, and `scientific_admission` is `not_performed`.
- envelope replay against the accepted exchange: 112,788 rows, 49,887 spatial and 62,901 other, with no key, envelope or payload mismatches. provided 5v5 spatial rows are 201, 245 and 277.
- non-envelope tables, which that replay only counts: `attempt_setter`, `attempt_execution_share`, `context_coverage`, `dressed_game` and `interval_player` are content-equal to the exchange. `interval_fact` and `interval_location` have zero cell differences across all 63,066 rows, and these hold the changed neutral masses.
- `attempt_value` has no table of its own. its five fields sit in `attempt_fact`, and all 2,855 rows match with no mismatches.
- methods: all 12 ids match the exchange and all 12 payloads are equal. six rows carry `experimental-v1:execution-v1-05-2`, three carry the pending factual reference and three `experimental-v1:positive-spatial-v1-08-1`.

this review's first pass raised three flags, all its own. `analysis_map` counts look wrong because execution and spatial share that table: 2,814 + 8,040 = 10,854, and likewise for the other seasons. the two interval tables looked different only because its canonical json distinguished sqlite `3.0` from json `3`. a query also failed on the unquoted column `group`.

not established: anything about serving. the candidate is not activated, and nothing here tests the api, the browser or the real corpus.

### real `20212022` launch review

verdict: **clear to launch. no blocker.** this review ran no source, fit or game read. it reread metadata, recomputed digests from disk and dry-ran the observer's argument handling with the cli stubbed and output in scratch.

- script: digest `acdf0c01`, `/bin/sh -n` passes. a line diff against the reviewed book block `1961ab26` shows only additions: three digest guards with their receipts, and the three new paths in the occupied guard. nothing else changed.
- argv: the full argv equals the receipt, and the ordinary tail equals both the receipt and the original `replacement-fit-preparation.json` argv. there is no `--previous`, no `--valued` and no pause or review flag.
- pins, all recomputed now: prepared `63bd2861`, coaches `102bca4c`, census `6fd06ffb`, observer `286b34dd`, subtree `c2412ac` with a clean analysis status. the script enforces all of them before launch, plus recipe `47691110` recorded for comparison.
- fresh paths: `real/` does not exist. all 15 output, log, receipt and check paths are in the occupied guard, `set -C` is on, and `mkdir -p` creates the check file's parent, so the exclusive write cannot fail after design.
- barrier: the dry run resolved `real`, `20212022` and 54 expected keys, and earlier controls refused the same command without the census. the census holds 54 distinct keys, 50 `on_the_fly` and 4 faceoff, in the observer's key format. every `on_the_fly` start is at or after the focal clock and every faceoff anchor at or after focal order, so all 54 must be unavailable under the production rule. a false barrier abort is not possible from these rows.
- oracle: a false equality abort is not expected. production and oracle apply the same binding, `_zone` returns only the three zones, and all 4,091 fixture contexts passed.
- failure evidence: a refusal gives exit 1 and writes `source_construction_incomplete`, and the block records log, exit, finish and launch receipts either way. a barrier failure stops before any solve, costing design time only.
- machine: nothing heavy running, 64 gb of memory against 17.3 gb peak in the original annual, 6.6 tb free, and system sleep prevented by `caffeinate`, which must stay active.

the stale fields in the receipt, `status: HOLD` and `pending root acceptance`, describe its preparation time. they are not defects, but the release record should supersede them.

what to expect, from the original annual: about 6,915 seconds of design, so the source report appears near two hours, then about 31 minutes of solve. the report should show `known_checked` 54, `masked_on_the_fly` at least 50 and `masked_faceoff` at least 4. `unresolved_binding` is the first real measure of omitted participation. no figure here is a forecast.

root's decision to let real fits proceed alongside blocked browser work is sound on the dependency: app-only repairs do not feed fitting. browser acceptance stays pending, not waived.

### real `20212022` source report

verdict: **clear. no defect.** report `2a1e41e1`, recipe `47691110`, saved `18:19:28z`, 4,398 seconds after launch against 6,915 of design in the original. this review read the report, the census, original head metadata and the production code cited below. it read no prepared game or capture, ran no new source pass and touched no running state. the fit is still running, so nothing here covers the solve.

the observer's requirements held on all 147,510 contexts: consumed availability equals the independent oracle and admitted contrasts equal source. all 54 known keys are masked, and the barrier closed before head construction.

| head | attempts | original unavailable | report unavailable | rise | masked on-the-fly | masked faceoff |
|---|---|---|---|---|---|---|
| `u` | 147,510 | 5,850 | 5,914 | 64 | 58 | 6 |
| `q` | 112,345 | 4,491 | 4,535 | 44 | 39 | 5 |
| `r` | 82,328 | 3,370 | 3,405 | 35 | 31 | 4 |
| `g` | 62,505 | 2,503 | 2,530 | 27 | 25 | 2 |

the original column and the report come from separate passes. the rise equals the masks in every head, so raw `None`, `unknown` and `no_same_clock_faceoff` add nothing new, and no masked faceoff lacked a zone. attempts equal the original support totals, and included plus excluded is 149,412 in all four heads.

the 64 in `u` split three ways:

- 54 at `5,5,1`, 50 on-the-fly and 4 faceoff. their keys equal the census exactly, in 54 games and 50 shooters. those are all the `5,5,1` masks, so a separate pass confirms the census was complete for that strength.
- 8 on-the-fly elsewhere: 2 at `3,3,1`, 3 at `4,5,1`, 3 at `5,4,1`.
- 2 faceoffs at `6,5,0`. these are the two `unresolved_binding` rows, because all four known faceoffs bind one coherent shift and an anchor order.

so 62 are same-clock, not 64. the 54 witnesses all have age zero. the eight others follow by construction: raw `on_the_fly` comes only from the supported-span overlay (`analysis_context.py:1153`), which requires start at or before focal, and the rule masks only start at or after focal. the four faceoffs all have anchor order at focal plus two and offensive zone, and none reaches `g`. the report cannot say what the intervening record is.

the two unresolved rows are not timing failures on this evidence. witness `2021020674:269` has a faceoff start at 1043, focal clock 1061, age 18 and no exact coherent binding. the other has no witness. both reach `g`. the observer cannot separate omitted participation from any other overlay failure, so the accurate name is unresolved. `withheld_earlier_anchor` zero says neither has a coherent earlier alternative at its bounds.

this sizes the scope's unknown for one year. `_deployment` can only write `faceoff`, `no_same_clock_faceoff` or nothing (`feature_data.py:999-1006`), and the last two were already unavailable. with the rise closure, two of 147,510 is the exact count of rows this year that the rule newly withholds for a non-timing reason, against the loose bound of 3,502. rows of the wider class that were already unavailable stay unsized, and the four later years stay unmeasured.

the fallback question closes. `_deployment` never writes `on_the_fly`, so the on-the-fly rule needs no binding: no fallback row can be admitted through it. spatial reads starts only through `player_shift_index` (`spatial_design.py:152-154`), so it consumes no fallback at all.

both real rows sit at `6,5,0`, which holds 2,832 of 147,510 attempts, as did all seven selected fixture rows. this is not chance, afaict. the mechanism is unknown: this is an observation from report counts, and no prepared game or capture was read to explain it. later years are unmeasured. no `5,5,1` row changed through this class this year, though three `5,5,1` rows carry `no_same_clock_faceoff`, so overlay failure is not confined to `6,5,0`.

`admitted_same_clock_faceoff` is zero here and in every fixture report, and afaict all 141,596 admitted starts are strictly earlier on the clock. that is a measurement, not a dead counter: the synthetic control fires it, and the same clock fields produced the 58 equalities. no admitted row this year rests on subsecond order. the order comparison's only work was rejecting the four.

pins for the completed state: saved `unavailable_attempts` must be 5,914, 4,535, 3,405 and 2,530, with `available_weight` 141,596, 107,810, 78,923 and 59,975. the real score must reproduce `source_context_sha256` `a60c81d8` and `source_response_sha256` `537cbba2`.

focused receipt `d6eacdb5` agrees with this section. its digests for the report, the original manifest and all four original head files recompute, and its limits are stated correctly. it counts only the 54 as proved classes; the eight further same-clock rows above follow from code, not from a witness. one field needs care. `conditioning_and_type_strength_partitions_match` sits beside `counts_match_original`, but the inputs the receipt names hold no type or strength partition: no original head file contains those keys, and they live in `coverage.json`, which it did not read. afaict the field can only be internal. internally it holds: class, type and strength each sum to included, and `u` class 1 equals `q`, `q` class 1 equals `r`, `r` class 1 equals `g`. equality with the original is not established until the coverage diff on the completed state, which [closes it](#completed-real-20212022-annual).

### completed real `20212022` annual

verdict: **clear. no defect.** manifest `7c740083` against original `592dce62`. this review read saved manifests, head metadata, coefficient arrays, `coverage.json` and receipts. it read no prepared game or capture, ran no source pass, rescore or solve, and left the strict read to the numerical owner.

every pin from the source report holds: saved `unavailable_attempts` 5,914, 4,535, 3,405 and 2,530, and `available_weight` 141,596, 107,810, 78,923 and 59,975. exit is 0 and all four heads are complete. all nine manifest file digests recompute. prepared, coaches, cutoff, `previous` and head paths equal the original.

design: `size`, `columns`, `means` and `active` are equal in all heads. inside `design`, only the three start-zone `feature_support` rows and the `shift_start` text in `fixed_transforms` change. `target`, `actors`, `priors`, `origin`, `arrays` and `selected_start` are equal. `ledger` lengths are equal and only `coefficient` differs.

coverage: exactly 24 leaves differ, the two start-zone support fields for three columns in four heads. all 149,412 per-attempt records and the per-head partitions equal the original. that closes the `conditioning_and_type_strength_partitions_match` point, and it closes the receipt's limit on old/new event identity for the fields coverage holds: key, game, outcome and goalie identity.

matrix nonzeros close the other receipt limit, on flag flips, as a count. a masked on-the-fly row adds one nonzero, since it had no contrast and gains the flag. a masked faceoff swaps one for one. so `q`, `r` and `g` rise by exactly 39, 31 and 25. `u` rises by 12,503, which is 39 + 19 × 656: the 19 masked on-the-fly rows outside `q` are blocked, and a blocked row carries all 656 origin cells.

| head | objective | start flag | age flag | pair sum | age-known start-unknown rows | largest shooter move | largest start contrast move |
|---|---|---|---|---|---|---|---|
| `u` | 63,798.406 to 63,797.688 | -0.060 to -0.280 | +0.023 to +0.228 | -0.037 to -0.052 | 10 to 74 | 0.0095 | 0.0005 |
| `q` | 61,491.748 to 61,491.719 | -0.074 to +0.048 | +0.196 to +0.083 | +0.123 to +0.132 | 8 to 52 | 0.0047 | 0.0002 |
| `r` | 43,428.521 to 43,428.385 | +0.056 to +0.142 | -0.178 to -0.256 | -0.122 to -0.115 | 5 to 40 | 0.0047 | 0.0008 |
| `g` | 35,037.244 to 35,037.325 | +0.212 to -0.144 | +0.147 to +0.447 | +0.359 to +0.302 | 5 to 32 | 0.0069 | 0.0007 |

the two flags are the largest moves in every head, up to 0.356 in `g`. [predictor timing](#predictor-timing) predicted this: the pair was a ridge split on 5 to 10 rows and is now separated by 32 to 74. the flags swing opposite and mostly cancel. the rest of the flag block moves at most 0.047. base, type, non-flag circumstance, goalie and setter blocks move at most 0.0037, coaches at most 0.0002, and the median coefficient about 1e-5. in `u`, six of the eight largest shooter moves are shooters in the 54 witnesses. all heads converged with the same terminations, and `g` took nine em iterations in both fits. `q` `gradient_max` rose from 0.0027 to 0.0102, but no gate reads it and termination is on relative reduction. afaict non-flag moves near 0.001 cannot be separated from stopping noise.

this is not yet a probability result. two groups need the real score, because no row-level change has been measured:

- masked rows. a masked on-the-fly row swaps the reference for the flag coefficient: -0.28, +0.05, +0.14 and -0.14 by head. that is about 64 rows.
- rows unavailable on both flags. `g` pair sum falls 0.056 on about 2,500 rows, the largest move on ordinary rows, and other co-occurring flags offset some of it. idk how much.

the flag also carries the accepted limit from [predictor timing](#predictor-timing). the start value is gone, but its absence remains a predictor, and availability can depend on later records. the flag's separate estimate now rests mostly on these rows, including the four later-anchor faceoffs. that limit is now sized at 64 of 147,510 in `u`. no change follows.

provenance: `git_commit` `dcd9930` is `HEAD` when the manifest was written (`artifacts.py:21`), not launch head `c4ed1e3`. `analysis` is tree `c2412ac` at both, and `git_dirty` covers `analysis/` only. the strict reader asks only for an identified clean commit, and fixture annuals already carry different commits, so this is not a defect. receipts should cite launch head and tree, not the manifest commit, for what ran.

cost: wall 6,164 seconds against 8,801, design 4,396 against 6,915, fit 1,767 against 1,885, of which `u` is 1,381. peak 18.8 gb against 17.3. the observer and the overlapping rollback both sit inside these, so no figure is a clean baseline.

### replacement disposable rollback

verdict: **clear for what it claims.** completion `6f5fca51`, correction `6cd0bdd0`, commit `bb8b34d`. this review read saved receipts, json outputs, scripts, profiles and the operator source. it ran no operator, opened no publication, rehashed no database and made no http request.

- saved outputs: every saved json, cost, exit, timestamp and tmpdir file matches the receipt in digest, and final sizes and mtimes match. `incoming.sqlite` is absent and `sqlite-temp` is empty. timings sum to 116.93 seconds against 117 from the timestamps, and peak is step two's 818,511,872 bytes.
- identity: step two's predecessor `d7151077` appears in the baseline `verification.json` only, and step three's `95ee3f1c` in the candidate's only. operator `e655` and reader `957d` recompute, app tree is `248ed592`, and the app has no status.
- sequence: step one against step three differs only in `action` and `predecessor`. step one against step two differs in `predecessor`, `publication_id`, `git_commit`, `generated_at` and the three spatial family rows moving to `provided`. `seasons` and `available_seasons` are equal across all three, as expected: they hold coverage facts, which the replacement does not change.
- correction: script `243135f3` to `7784afbc` is a path substitution plus `mkdir sqlite-temp`, the `SQLITE_TMPDIR` export and its receipt. operator tails and completion assertions are otherwise unchanged. the two profiles are 178 bytes each and differ only in the path, so confinement is unchanged.
- failed `01`: 6410 is `10 | 25 << 8`, the output is empty and the exit is 1. the failure is inside `check(incoming)` at `publication-cli.ts:98`, before either rename at `:116-119`, so rotation cannot have begun. the fixture03 receipt records no write profile, which fits the same reader passing there.

limits, none a defect:

- the final `active` digest is inherited, not recomputed. completion copies it from step two's `predecessor`, and step three's own hash is computed at `publication-cli.ts:87-95` but not saved. the chain is continuous and id, size and metadata agree, and the receipt says no repeat hash ran. read `final_disposable_files.active.sha256` that way.
- empty `sqlite-temp` proves only no leftover. sqlite unlinks temp files at open, so there is no spill size, here or for the real publication. an unsandboxed operator would spill to ordinary temp, on the internal disk unless told otherwise. that matters only if activation is ever decided.
- the operator's `next` step, restarting the server and reloading, was not exercised. neither was http or the browser. the receipt says so.
- the real fit's solve overlapped both operator attempts on the same volume, so its wall time is not a clean baseline. the report's 4,398 seconds of design finished at `18:19:28z`, before either attempt.

### execution-base composition

`fixture/execution-results` passes. manifest `82f0b55f`, producer `ffe9597`, clean, three seasons, 30 family rows. the retained facts' `prepared` and observed bindings are unchanged.

preservation against original `current-02/results` and retained `facts`:

- `people`, `sources` and `supports` catalogs equal the original. only `methods` changes.
- `descriptive` and all `not_computed` family rows equal both the original and the facts. the `spatial` family stays `not_computed`.
- `evidence.attempt_fact`, `dressed_game`, `interval_player` and `context_coverage` are byte-identical to the original.
- `interval_fact` and `interval_location` keep every row, with zero non-mass cell differences. only `for_mass` and `against_mass` change, and only in the two neutral populations. recorded attempts and goals do not move.
- in `microstats`, only `reference_xg_per60` `value` and `numerator` change.
- every composition receipt equals the original except `scores_sha256`: `intersection`, `numerical_only`, `source_only`, `unvalued_source_attempts`, `valued_exclusions` and `setter_discrepancies` are all unchanged.

bindings, recomputed from saved scores:

| season | `attempt_value` joined, cell mismatches | 5v5 neutral kept, events | `interval_fact` neutral total |
|---|---|---|---|
| `20232024` | 605, 0 | 16.959320058 | 16.959320058 |
| `20242025` | 1,062, 0 | 29.637835476 | 29.637835476 |
| `20252026` | 1,068, 0 | 15.207888585 | 15.207888585 |

kept means 5v5 complete events outside `valued_exclusions`, which removes 0, 136 and 470 events. the five `attempt_value` fields match saved prefixes and conditionals exactly, and `shares` totals match.

methods: nine rows. the six execution and reference rows carry `experimental-v1:execution-v1-05-2`. each binds its new score manifest, the retained facts and its composition receipt, and all digests were recomputed from disk. `fit_seasons` and cutoffs are unchanged, and `inputs` and `assessment` point at the new states and scores. the three `factual-pending-reference` rows equal the original and the facts. `method_id` stays `execution-v1-06-<year>`, as accepted under s1.

this review's first bindings pass reported mismatches on every `attempt_value` row and interval totals far from neutral mass. both were its own errors: those cells are wrapped objects, and interval rows split by `population` and exclude valued-out attempts. neither reflects the artifact.

## cost notes

- `validate_design` loops over every row in python and each annual fit reaches it about four times: before fitting, at write, at read-back and as the next year's predecessor. composition repeats it for five states. estimated tens of minutes per annual fit; measure on the first real year.
- the cli holds the predecessor's whole design through the fit, though only its ledger and basis are used. after the representation change this looks affordable; measure it too.
- `solve_logistic` retains the native `maxfun=15000`. v1-05 heads took 3,000 to 5,000 evaluations. a larger volume or spatial head exhausting it would report a failed solve after the full cost.

## not established

one real annual fit, `20212022`, is reviewed here. no real score, probe, spatial fit, publication, api, browser or export result is. the synthetic proof uses tiny designs and proves arithmetic, not estimator quality. shape and quality numerical sensitivity at real scale is unmeasured. causal interpretation, calibration and scientific support are outside this review.
