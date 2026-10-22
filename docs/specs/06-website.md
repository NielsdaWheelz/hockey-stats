# pr06 — complete player-analysis website

status: **scope index; the [experimental application appendix](experimental-application.md) and its [parent specification](experimental-player-analysis.md) define the initial implementation and remaining expanded-coverage contracts.** extend the existing 05a–05h application for the [complete experimental program](experimental-player-analysis.md), through [05](05-publication.md). [the plan](../plan.md) owns assignment; [the visual inventory](../product-inventory.md#visual-coverage-inventory--2026-10-22) is the view/control/export checklist. do not build another research dashboard or require global model admission before private modeled views.

## target behavior

browse complete selected skater and goalie analysis: tables/search, concise comparative cards, component details, spatial explanation, peer distributions, player comparisons, historical trajectories, recorded game evidence, deployment/with-without context, personal shooting and exports. keep real magnitudes and evidence beside ranks. 5v5/xg is the first working path, not the completed scope.

[v1](../product-inventory.md#v1-card-completion-boundary--2026-10-22) completes hockeyviz-style player cards/components and both jfresh skater formats, including supported microstats, embedded maps/distributions/history and card png. retain and extend the existing workspace around those outputs. the broader catalogue follows; standalone scatters, richer history bands, spider/reciprocal views and jfresh goalie extras are not all v1 gates. [eight sample images](../research/visual-references/README.md) and [presentation requirements](experimental-application.md#sample-driven-presentation-requirements) distinguish compact comparative, microstat and analytical-sheet compositions.

the headline remains underlying level across a season. distinguish observations, experimental modeled estimates and specific supported claims. show quantity/sign/units/reference, season/strength, coverage, model identity and consequential limitations. separate component rates, accumulated results and reference-workload value. no unsupported causal, forecast, replacement or calibrated-uncertainty language.

## structure and composition

reuse current react/router routes, shared client/effect operations and profile/table/comparison/distribution/map/history/png owners. typed responses supply finished hockey quantities; browser selectors choose available results rather than refit models. the application may compute declared display/cohort operations from published values, using the same owner across html and exports.

one content designer per feature family works with its numerical owner on actual labels, definitions, representative content, map scales and empty/error states. examples must include sparse evidence, missing inputs, experimental uncertainty and materially different players. labeled synthetic fixtures permit parallel interface work; real-output review is required before calling a family complete. no generic dashboard/card framework or ornamental placeholder wall.

scalar/map/explanation views must describe the same quantity. probability stages and explanatory subskills do not become extra additive value. incompatible comparisons need visible reasons; selected player/cohort/reference remain explicit. history uses declared output seasons and methods, not archived publications. table/card/map exports preserve identity, units, references and experimental meaning.

## boundaries and acceptance

retain localhost access until separately changed; detached browsing, direct links and ordinary reloads continue. no browser-triggered fits, arbitrary date windows, complete event explorer, accounts, public-hosting work or historical-release browser. missing in-scope reference panels remain open under [visual coverage](../issues/experimental-visual-coverage.md); unknown definitions require explicit independent contracts or a user scope decision, not indefinite optional status.

the application appendix owns files, routes/responses, layouts, cohorts, scales and export formats for assigned view batches. test actual table → profile → comparison → history/export journeys and reconcile v1 card fields first; later inventory rows remain tracked. document inaccessible evidence rather than inventing it, and distinguish it from an unwritten available field. verify keyboard use, narrow layouts/zoom, readable maps and invariant content across displays. keep verification proportionate to consequential changes.

temporary integration/live checks follow red → green → refactor → green, then deletion; fixtures and explicitly selected lasting checks follow [07](07-lightweight-testing.md). completion requires real family outputs and truthful content, not mature accuracy or a scientific-admission badge. software-invalid quantities stay unavailable with a reason; weak but defined estimates can be explored. implementation and activation remain separately assigned.
