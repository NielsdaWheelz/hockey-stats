# fresh v1-11 contract review

scope: read-only review of the implementation against the full handoff and canonical numerical appendix. local bounded controls only; no hdd reads, real fits, publication or startup. the real execution and final acceptance remain root-owned.

## source blocker found and repaired

the original `territory_design.py` grouped conflicting anchors by period and elapsed clock, crossing corroborated live-span boundaries. an ordinary located goal and following center faceoff normally share the same elapsed clock and have different locations. this falsely marked both as conflicting, deleting the valid bridge into the goal and the valid bridge after the faceoff. it also prevented the located terminal anchor from owning the nuisance endpoint.

the independent temporary control `.territory-independent/final-reset-conflict.py` was red: hit at `10s/x0` → ordinary goal at `20s/x80`, followed by faceoff at `20s/x0` → hit at `30s/x40`, produced zero path seconds and crossings. the declared continuous-span construction requires twenty seconds and crossings at `13.125/26.25s`.

the repair at `analysis/src/hockey_stats/territory_design.py:169` scopes conflict groups to the same period, clock and episode, separates goal/faceoff resets and intervening source/report barriers, and updates the recipe description/hash. independent green checks establish twenty physical seconds, two crossings, two hundred nuisance slot-seconds, ten whistle incidences and two mirrored restart pairs. a located goal supplies the endpoint without terminal carry. the original named nonbridge exclusion remains recorded, while known resets and zero-duration nonbridges no longer invent a `clock_unresolved` failure.

bounded existing captures confirm material impact:

| capture | old path seconds / crossings | repaired path seconds / crossings | repaired conflict handling |
|---|---:|---:|---|
| `2025020001` | `2273 / 116` | `2406 / 122` | five ordinary goal/faceoff pairs stop being false conflicts; genuine same-span `320/321` remains excluded |
| `2024020001` | `2109 / 86` | `2215 / 90` | four ordinary goal/faceoff pairs stop being false conflicts; genuine same-span contacts, including `332/333`, remain excluded |

[exact checked facts](final-contract-source-facts.json) bind both input copies, the frozen old source, repaired source and control. the old unqualified real attempt cannot supply acceptance for the repaired source. the corrected normal-cli regeneration was independently reread: `e2e-v3` contains both completed baseline heads, 66 entry plus 56 exit crossings, and 36 scalar/72 map rows for complete and deliberately missing-panel composition. both retain valid shift references; only the complete panel supplies successor values. the old `e2e-v2` state now rejects with `territory recipe differs`.

## other reviewed boundaries

the two-head scalar likelihood uses seconds and event multiplicities correctly. raw role-specific entry/carry priors and reporting centers remain separate; unknown positions retain fitted coordinates. finite-age block exponentials and the analytic tail retain same-zone self-restarts; one-slot spatial changes use all start/age columns, include unknown means and avoid a second defensive reflection. normalized occupancy/pivot contraction and unrebased absolute term scales preserve their declared accounting meanings.

saved state and reference readers retain explicit purposes, annual identities, source bindings, per-head statuses and diagnostic outcomes. current composition operates annually without holding five full designs, preserves copied inherited members and leaves ledger completion to v1-12. finite detached evidence preserves valid movement/shift references when successor input is absent. the ordinary readers now enforce both territory map presentations against the scalar/support/method owner.

the new panel cost fields separately name metadata read time, logical bound bytes, panel projection time, panel array bytes and process memory high-water. they do not claim physical i/o measurement or incremental peak allocation. the fitting instrumentation separately times validation, compression, complete head fitting, nested native solver calls, hazard projection and writing. cumulative peak scope explicitly excludes later write/readback peaks; whole-command measurement remains with the native command. the bounded `resources.py` control was independently rerun and confirms exact numerical equality with the prior implementation for coefficients, probes, priors, ledgers, centering, objectives, diagnostics, projections, support and recipe. no numerical change or generic lifecycle machinery follows from this instrumentation.

the compositor now requires each published year to have one matching accepted ev method whose declared annual-state inputs cover the entire selected ev prefix, including the two undisplayed years. it does not combine incompatible methods. [the bounded metadata admission review](final-ev-prefix-review.json) proves exact-prefix admission and rejection of either wrong old ancestor and a mixed-method prefix. the earlier compositor failed those old-ancestor controls. this check reuses validated method inputs and adds no external reads. these metadata-boundary controls use explicit i/o stubs and do not substitute for source/numerical integration or real input verification. execution review must still bind the exact five selected states to the accepted receipt pins; this review has not read those external states or certified real annual completion.

no other concrete first-fit correctness blocker was established by this review. the corrected source and its normal-cli integration are cleared for a fresh frozen first annual. this is bounded source/code clearance, not real numerical, publication, browser or scientific acceptance.
