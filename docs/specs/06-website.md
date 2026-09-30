# pr06 — website

status: **stub; not ready for implementation.** expand against the [05 publication contract](05-publication.md) and the settled [brief](../brief.md). labeled fixtures can exercise the interface; a real analytical release additionally requires supported 03–04 results. [plan](../plan.md)

## purpose and ownership

support the published question: who creates or suppresses genuine 5v5 opportunities, where, and with what evidence? inputs are complete published view responses. outputs are a compact sortable league table with name search, player profiles and adjusted maps, selected-player comparisons, complete-season observed summaries and game-by-game evidence.

use the selected react/router frontend and effect operations within `app/src/`. route/browser modules own presentation and meaningful url selections; effect owns response validation and application effects. server queries remain in 05. defer concrete files and interfaces; preserve one state owner.

## settled behavior and exclusions

present offense and defense separately. distinguish estimated ability from observed counts, reconstructed exposure and inferred locations. game rows explain observed season totals; they do not decompose adjusted season effects. show units, baseline, uncertainty meaning, evidence coverage and publication identity. unavailable values need reasons, not zeros.

support local/private browsing, direct links and reloads. no browser-triggered fits, arbitrary date windows, full event explorer or historical-release browser. public hosting, richer cards, percentile/distribution charts and new analytical components have separate consumers in the roadmap.

## full specification and completion

content design owns labels, definitions, empty/error states, visual hierarchy and accessible explanations. analytical owners supply metric semantics. specify sorting, comparison compatibility, map scales/orientation and insufficient-evidence states using real output examples. display admitted population/reference metadata; do not confuse the model baseline with a percentile cohort. any later cohort needs its definition when that feature first consumes it.

completion means the agreed views work coherently from one publication, including detached operation, direct-route reload and honest fixture/missingness labels. verify the useful browsing path and chart readability; no design-system project.
