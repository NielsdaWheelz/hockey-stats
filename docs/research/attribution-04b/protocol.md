# 04b frozen study

the assigned [specification](../../specs/04b-attribution-revision.md) owns the estimator, references, generator, seed streams, fixed budgets and prospective claim rules. its pre-execution snapshot is `/Volumes/Expansion/hockey-stats/runs/attribution-04b-20261015/inputs/spec-snapshot.md`, sha256 `1ef3d7393b368f3d98ad06ccbfa97fabfbbd76bea6b4327baa001a1a6b494fca`. the machine-readable protocol binds that snapshot, the corrected 04a evidence and the reviewed implementation before research execution. it has no self-hash.

the [machine-readable protocol](protocol.json) and external `inputs/protocol.json` are identical, sha256 `32c4edf30c7cc8d5f1c844c7ee048991465d9066019e434ddefc0746ccedc7d6`. the model implementation is frozen at `d465795030c66c13d5b5c789c2c1879e1ef7a78b`; its exact python, numpy, scipy and lockfile identities are recorded in the protocol. preparation, fitting and every assigned real/synthetic trajectory used that commit throughout. command receipts record thread settings and process timing.

after numerical completion, source review found that the first assessment recomposed original control maps before counting strict negative signs, introducing tiny negatives in originally exact-zero columns. the reporting repair in `d3ef9b5` retains original control `M,A` and their original arithmetic; it changes no fitted states, trajectories, numerical thresholds or recovery rules. the original `assessment/` remains preserved with invalid control sign diagnostics. corrected reporting uses a fresh `assessment-02/`, binds its own clean `implementation`, and separately binds the frozen `model_implementation`; all upstream producers still require the exact frozen model identity. [verification](verification.md) records the failing original-game check, independent repair review and both reporting costs.

the claims concern recorded-rate associations conditional on the original references and admitted population. separate shape borrowing retains all 656 cells and may produce negative complete rates. historical game refits vary fits, scale selection and covariance carry; they do not vary references or establish total ability uncertainty. exact persistent co-deployment limits individual claims even when the empirical spread collapses.

the real budget is five new shape fits, ten replayed scalar/volume controls and 200 complete three-block historical refits. recovery uses two noise cases, 200 independent outer replicates per case and 200 historical refits within each outer replicate. no failed-draw replacement or outcome-driven additional execution is permitted. fixture exercises use the same mechanisms with explicit smaller counts and do not complete this study.

## figure schemas fixed before results

all figures use lowercase labels, physical units, explicit noise case and interval procedure. unavailable results retain their reason. no player selection depends on estimates. axes and color limits are shared where visual comparisons imply comparability. the figure review checks the actual rendered images as well as their data contracts.

1. `recovery.png`: paired native map error reductions for broad/local contrasts in each noise case with the outer-replicate monte carlo intervals; working/refit coverage for the frozen nomination cells beside the nominal .95 and developmental .90 references. transitions and paired sum are named separately. exact paired differences are shown as unidentified diagnostics, never zero-effect successes. denominators remain visible.
2. `native-maps.png`: broad/local synthetic truth, control, revision and revision error on native rink axes, using gaussian outer replicate zero in year five as the fixed illustration, followed by the four frozen real player examples in both roles. truth, estimates and errors share symmetric color limits within each comparison; all real examples share one scale. every synthetic and real map names its matched volume and evidence scope. native cells are model parameters, not demonstrated five-foot physical accuracy; pointwise intervals imply no simultaneous map certainty.
3. `resolution.png`: both frozen real pairs, both populations and offense/displayed suppression, with distinct working and basic game-refit intervals in league-relative units. the strict 5% meaningful band is scalar only. adjacent exposure summaries show original admitted annual seconds against interval width divided by the original annual rate, separately by population and role, using every current player. working and refit series are distinct, points are unconnected, and unavailable/unidentified counts remain visible. label the evidence scope and exact null reason; no rankings or supported-ability labels.

## execution and review

the [verification record](verification.md) records temporary red/green checks, independent numerical/source/statistical/content reviews, measured costs, completed denominators and deletion accounting. the [plan](../../plan.md) owns current status. a numerical interruption is incomplete execution, not a scientific verdict. this study always retains `admission:not_admitted,handoff:null`.

the first assigned gaussian outer replicate executes once before the four bounded synthetic workers begin. seed streams fix each remaining outer/inner trajectory independently of scheduling; a temporary check reproduced every selected parallel array bit for bit through the serial path. completed outer artifacts are written before results return to the parent. failed work is never replaced.

manual entry points run from the repository root with the locked environment already prepared:

```sh
analysis/.venv/bin/python analysis/research/attribution_revision.py prepare --baseline-prepared /absolute/corrected/prepared.json --protocol /absolute/inputs/protocol.json --out /absolute/new/prepared
analysis/.venv/bin/python analysis/research/attribution_revision.py fit --prepared /absolute/new/prepared/prepared.json --out /absolute/new/fits
analysis/.venv/bin/python analysis/research/attribution_revision.py refit --prepared /absolute/new/prepared/prepared.json --fits /absolute/new/fits/fits.json --draw-start 0 --draw-stop 1 --out /absolute/new/refits-000-001
analysis/.venv/bin/python analysis/research/attribution_revision.py simulate --prepared /absolute/new/prepared/prepared.json --out /absolute/new/simulation
analysis/.venv/bin/python analysis/research/attribution_revision.py assess --prepared /absolute/new/prepared/prepared.json --fits /absolute/new/fits/fits.json --refits /absolute/new/refits-000-001/refits.json --refits /absolute/new/another-range/refits.json --simulation /absolute/new/simulation/simulation.json --out /absolute/new/assessment
```

the actual protocol requires its exact corrected baseline and external output root. paths above illustrate argument boundaries, not alternate admissible research inputs. `--refits` repeats for explicit range manifests; ranges must have unique ids and cover all 200 assigned draws before empirical intervals exist. `--fits` always consumes its manifest. every output directory is new; no command discovers a completed run from directory contents. partial numerical execution remains reportable and supplies no scientific verdict.
