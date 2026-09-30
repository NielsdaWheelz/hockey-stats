# implementation plan

status: 01 and [02a](specs/02-interpretation.md) are implemented, reviewed and merged. [02b](specs/02b-reconstruction.md) is specified; its implementation is not yet authorized. the user confirmed adding the official per-event on-ice report after the [boundary audit](issues/event-membership-evidence.md). later slices still require their specifications and the user's progression decision. [brief](brief.md) and [architecture](architecture.md) supply the settled product and operating constraints.

this plan builds the first useful product. the [product roadmap](roadmap.md) proposes v2+ capabilities and their ordering; its later milestones are not requirements for these slices.

## target

local commands acquire evidence and run python analysis. save expensive fits and export a completed sqlite publication. one effect application serves its league table, player profiles, maps, comparisons and game evidence. publication is an explicit stop/copy/restart operation; retain one previous database. source and model meaning remain visible. no job platform or release manager.

## slices and ownership

these are review boundaries, not a fixed number of large prs. specify only the next implementable slice in detail; split further when a change cannot be reviewed comfortably.

| slice | owns | input → output | depends on |
|---|---|---|---|
| [01 capture](specs/01-capture.md) | effect acquisition; small source corpus | explicit game id → unchanged responses and retrieval records | none |
| [02a interpretation / pr2](specs/02-interpretation.md) | python source semantics and reconciliation | one game's captures → attributed identities, events, reported locations and shift records | 01 |
| [02b reconstruction](specs/02b-reconstruction.md) | report capture/interpretation; python event membership, elapsed exposure, coordinates and coverage | five attributed sources → reported event players, supported intervals and genuine 5v5 exposure | 02a |
| 02c corpus and reference admission — planned | effect reference acquisition; python corpus selection and coverage audit | schedule, player bios and selected game captures → attributed game inventory, birth dates/handedness and reconstruction coverage | 02b; historical-data inspection when available |
| 03 chance valuation | python blocked-origin imputation and opportunity model | interpreted/reconstructed evidence → valued attempts, fitted artifacts and evaluation | 02c evidence; scientifically justified training/evaluation selection |
| 04 player attribution | python history-informed spatial effects | valued attempts and exposure → player surfaces, summaries and supported uncertainty | 03 |
| 05 publication | python export; effect read queries and file publication | declared analytical outputs → sqlite and complete view responses | agreed output contract; fixture outputs can precede 03–04 |
| 06 website | react/effect presentation | published view responses → league table, profiles, comparisons and game evidence | 05; real analytical release also needs 03–04 |
| 07 lightweight testing | a small lasting integration/live suite and necessary fixtures | stable capture-to-publication/read path → repeatable high-value checks | after a useful end-to-end path exists; before declaring the first product complete |

02a owns source interpretation; 02b extends it for the necessary on-ice report and owns reconstruction. 02c makes the previously implicit corpus dependency explicit: compare captures with a captured schedule inventory, admit player birth dates/handedness, and apply the existing interpretation/reconstruction to a declared selection. reuse acquisition mechanics while keeping schedule/player identities separate from the fixed game-capture contract. inspect the detached historical data when it returns; classify originals versus transformed exports. local examples can exercise these mechanisms without the drive, but cannot establish a training population. no scheduler, generic importer or reference-data service follows from this boundary.

02c establishes available evidence, not fitness for a particular model. 03–04 select the training horizon, evaluation splits, eligibility and required features; their specification need not wait for exhaustive historical recovery. 03 owns opportunity values and their pre-event features; 04 owns player effects and the decision to acquire game-specific roster-report coach evidence before evaluating coach context. spot-check roster-report availability during 02c so that decision starts with known limits. scratches remain a later availability/context input. the [source audit](research/source-audit.md) records these placements. event-summary and home/visitor-shift reports serve selected manual checks in 02b and corpus audits in 02c; duplicate production feeds need a demonstrated missing fact.

05 serializes results and queries them without a second scientific implementation. 06 renders them without refitting. 07 adds software verification, not application capabilities or model-validation ownership. 02c adds reference acquisition and corpus bookkeeping before fitting; the cost buys explicit populations and attributed age/handedness rather than leaving those tasks hidden inside model code. all later slices still require specification and the user's progression decision.

each detailed specification names its files, inputs/outputs, content rules and observable acceptance. the content reviewer owns command wording and fixture annotations in 01; later slices assign method explanations, units, missingness and view content to their designer. data and systems reviewers challenge semantics and unnecessary machinery before implementation. no separate design system or content framework follows from that review.

## working rules

- hard cutover: no legacy imports, compatibility adapters, fallback feeds or inherited expectations. retain the archive and historical documents as evidence.
- reuse existing application modules and effect/node/library primitives; extract shared application code only where actual repetition warrants it.
- initial slices use temporary end-to-end integration/live checks: establish red, implement, establish green, refactor, rerun, then delete all test code and test-only dependencies/scripts. retain a short verification record in the change description and useful source data/facts. production validation remains application behavior.
- the user explicitly chose deletion of all initial tests. cost: checks must be recreated for later changes until 07 defines the lasting suite. 07 should be extremely lightweight and integration/live-heavy; no matrix, orchestration service or continuous fitting obligation is implied.
- scientific evaluation routines and results in 03–04 are part of the analysis supporting fitted artifacts and published claims. retain those with the relevant work; they are not the temporary software tests deleted above, and their validity cannot wait for 07.
- preserve expensive work; rebuild cheap work. no application build archive, automatic stage cache, scheduled pipeline or hot publication protocol.

## first product acceptance

the fixed-season product answers the agreed 5v5 player question with coherent maps/scalars, observed game evidence, coverage and justified uncertainty. raw evidence remains attributable; unsupported quantities remain unavailable. a completed publication works without the hdd or python environment. publishing and restoring the previous database are ordinary operator actions. scientific evaluation must support the claims before real estimates replace development fixtures.

current-season operation, public hosting, fuller cards, distribution charts and further components follow later. exact models, thresholds and frontend endpoint/schema details belong to their slices; inventing them before their scientific inputs are known would add speculative work.
