# implementation plan

status: slice specifications authorized after architecture commit `9ff024a`; the user subsequently authorized implementation of 01, now complete. later slices still require their specifications and the user's progression decision. [brief](brief.md) and [architecture](architecture.md) supply the settled product and operating constraints.

## target

local commands acquire evidence and run python analysis. save expensive fits and export a completed sqlite publication. one effect application serves its league table, player profiles, maps, comparisons and game evidence. publication is an explicit stop/copy/restart operation; retain one previous database. source and model meaning remain visible. no job platform or release manager.

## slices and ownership

these are boundaries, not seven large prs. specify only the next implementable slice in detail; split further when a change cannot be reviewed comfortably.

| slice | owns | input → output | depends on |
|---|---|---|---|
| [01 capture](specs/01-capture.md) | effect acquisition; small source corpus | explicit game id → unchanged responses and retrieval records | none |
| 02 interpretation | python hockey semantics and coverage | captures → attributed events, identities, coordinates and genuine 5v5 exposure | 01 |
| 03 chance valuation | python blocked-origin imputation and opportunity model | interpreted evidence → valued attempts, fitted artifacts and evaluation | 02 |
| 04 player attribution | python history-informed spatial effects | valued attempts and exposure → player surfaces, summaries and supported uncertainty | 03 |
| 05 publication | python export; effect read queries and file publication | declared analytical outputs → sqlite and complete view responses | agreed output contract; fixture outputs can precede 03–04 |
| 06 website | react/effect presentation | published view responses → league table, profiles, comparisons and game evidence | 05; real analytical release also needs 03–04 |
| 07 lightweight testing | a small lasting integration/live suite and necessary fixtures | stable capture-to-publication/read path → repeatable high-value checks | after a useful end-to-end path exists; before declaring the first product complete |

02 owns reconstruction and historical-corpus admission when the drive returns: classify original versus transformed inputs and establish usable coverage. 03 owns opportunity values; 04 owns player effects. 05 serializes results and queries them without a second scientific implementation. 06 renders them without refitting. 07 adds software verification, not application capabilities or model-validation ownership. the detached drive does not gate 01; two example games cannot establish a training population.

each detailed specification names its files, inputs/outputs, content rules and observable acceptance. the content reviewer owns command wording and fixture annotations in 01; later slices assign method explanations, units, missingness and view content to their designer. data and systems reviewers challenge semantics and unnecessary machinery before implementation. no separate design system or content framework follows from that review.

## working rules

- hard cutover: no legacy imports, compatibility adapters, fallback feeds or inherited expectations. retain the archive and historical documents as evidence.
- there is no current application code to consolidate. reuse effect/node/library primitives; extract shared application code only where actual repetition warrants it.
- initial slices use temporary end-to-end integration/live checks: establish red, implement, establish green, refactor, rerun, then delete all test code and test-only dependencies/scripts. retain a short verification record in the change description and useful source data/facts. production validation remains application behavior.
- the user explicitly chose deletion of all initial tests. cost: checks must be recreated for later changes until 07 defines the lasting suite. 07 should be extremely lightweight and integration/live-heavy; no matrix, orchestration service or continuous fitting obligation is implied.
- scientific evaluation routines and results in 03–04 are part of the analysis supporting fitted artifacts and published claims. retain those with the relevant work; they are not the temporary software tests deleted above, and their validity cannot wait for 07.
- preserve expensive work; rebuild cheap work. no application build archive, automatic stage cache, scheduled pipeline or hot publication protocol.

## first product acceptance

the fixed-season product answers the agreed 5v5 player question with coherent maps/scalars, observed game evidence, coverage and justified uncertainty. raw evidence remains attributable; unsupported quantities remain unavailable. a completed publication works without the hdd or python environment. publishing and restoring the previous database are ordinary operator actions. scientific evaluation must support the claims before real estimates replace development fixtures.

current-season operation, public hosting, fuller cards, distribution charts and further components follow later. exact models, thresholds and frontend endpoint/schema details belong to their slices; inventing them before their scientific inputs are known would add speculative work.
