# pr05b — two-player observed comparison

status: **direction stub; not ready for implementation.** [the plan](../plan.md) owns assignment. extend [05a](05a-observed-website.md)'s existing private website independently of 04h or model admission. [brief](../brief.md) · [architecture](../architecture.md)

## target and ownership

select two distinct skaters from the same active completed-season publication and compare their existing recorded on-ice 5v5 counts, rates, included minutes and coverage. matched counts and time belong to each player's own included evidence; the players need not share games, opponents, teammates or coverage. link each player to the existing profile/game evidence. these describe included observations, not adjusted contribution or repeatable ability.

reuse one existing `/api/league` response for both summaries and their publication identity. show publication evidence once, retaining the global unassigned-evidence notice and each player's coverage. python remains the owner of counts, matched exposure and rates; effect retains reads/validation; route and presentation modules under `app/src/web/` own selection and display. reuse the existing client and formatters. exclude new exporters, endpoints, database schemas and analytical quantities, including browser-derived differences, net rates or ratios.

localhost-only, detached browsing and the active-publication/one-backup policy stay unchanged. this slice needs no new acquisition, fit or publication. meaningful url selection should support direct links and reloads.

## full specification and completion

settle the concrete route, player selectors, duplicate/unknown/missing selections, loading/error behavior, navigation back from profiles and narrow table layout. use available publication examples; define exact labels and null behavior before implementation. selection changes the players displayed, not the season or analytical population. existing profile links provide game evidence; do not fetch or merge game rows into this view.

the content designer owns a compact accessible comparison: aligned units and precision, counts versus rates clearly distinguished, included time and coverage beside each player's numbers, and direct access to supporting evidence. display missing values with their existing reason; do not imply that a numerical difference establishes an ability difference.

completion requires rendered values and metadata to agree with the consumed league response, visible unequal or incomplete coverage, useful keyboard navigation, direct-route reloads and detached browsing. the full spec selects proportionate integration/browser checks under [07](07-lightweight-testing.md); source/export correctness does not need a new audit for this presentation change.

exclude percentiles, new comparison cohorts, distribution charts, adjusted maps, xg, ability rankings, arbitrary dates, public hosting and a generic comparison/card framework. these remain separate roadmap capabilities. the benefit is useful comparison now; the cost is limited descriptive interpretation and possible presentation changes when supported estimates arrive. this does not fulfill or narrow the analytical player-profile destination.
