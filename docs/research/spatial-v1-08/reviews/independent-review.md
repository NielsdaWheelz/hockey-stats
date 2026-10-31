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

so the mask is decided by records before the attempt plus the saved shift start clock. two small dependencies remain, and both can only withhold a start, never admit one. `len(matching) == 1` and `tied_unknown` can see a later same-clock record, so a later faceoff can withhold a start anchored earlier. `order_supported` and an unknown episode end are game-level. no source change follows, and [the final review](#final-source-review) settles that no count is needed.

mask size: age-known start-unknown rows in `u` were 10, 5, 15, 14 and 5 across the five years. the `20212022` 5v5 census alone adds 54, so at least 84% of that group becomes newly masked rows. `unavailable:shooter_shift_start` therefore becomes a near-dedicated level for same-clock starts, not the general unknown level, which stays on the roughly 2,000 to 10,000 unbound rows. mechanically this is sound, and the neutral reference does not read it. it means the repaired coefficient will be estimated mostly from these rows, so a large change in it is expected and is not evidence of a defect.

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

## cost notes

- `validate_design` loops over every row in python and each annual fit reaches it about four times: before fitting, at write, at read-back and as the next year's predecessor. composition repeats it for five states. estimated tens of minutes per annual fit; measure on the first real year.
- the cli holds the predecessor's whole design through the fit, though only its ledger and basis are used. after the representation change this looks affordable; measure it too.
- `solve_logistic` retains the native `maxfun=15000`. v1-05 heads took 3,000 to 5,000 evaluations. a larger volume or spatial head exhausting it would report a failed solve after the full cost.

## not established

no real fit, probe, publication, api, browser or export result is reviewed here. the synthetic proof uses tiny designs and proves arithmetic, not estimator quality. shape and quality numerical sensitivity at real scale is unmeasured. causal interpretation, calibration and scientific support are outside this review.
