# pr05a — private observed-results website

status: **stub; not ready for implementation.** the user approved this intermediate product alongside 04c. [the plan](../plan.md) owns assignment; no implementation or publication is assigned. this is the first vertical slice of the existing [05 publication](05-publication.md)/[06 website](06-website.md) responsibilities, not another application or a replacement for analytical v1.

## target and scope

browse the 2025–26 regular season privately: compact sortable league table and name search → player profile → complete-season observed summary and game evidence. show recorded genuine-5v5 attempts for/against, reconstructed exposure, matched rates and visible coverage. browsing and direct-route reload work without python or the external drive.

source-supported observed quantities do not require chance/attribution admission. they do require correct source selection, alignment and aggregation. reported event membership and reconstructed elapsed lineups are different evidence: define the matched population before dividing counts by time. preserve unavailable values and reasons; incomplete included-game subtotals must not appear as complete-season totals. game counts/exposure reconcile to the corresponding summary.

## one path and clear owners

- python reuses interpretation/reconstruction and population primitives, computes the observed summaries once and exports one finalized sqlite database. it owns units, selection, rates and reconciliation.
- effect owns validated read operations, view responses and explicit local publication. react/router owns presentation, urls and transient interaction. no hockey aggregation is reimplemented in sql or typescript.
- the publication needs source/population identity and cutoff, exact transformation/reconstruction revision, player identity, season summaries, game rows and coverage. exact schema/api fields belong in the full spec. no model identity or empty future ability tables are required for this observed-only slice.
- use the existing explicit stop/copy/restart procedure, one active database and one previous valid database. no automatic activation, new service, metric registry or compatibility framework. later 05–06 extend these same modules and views.
- content design owns concise metric labels, units, sorting meaning, missing/empty/error states and evidence hierarchy. the page must make recorded on-ice results distinguishable from individual ability without filling it with research placeholders.

## settle in the full specification

name the exact supported count/exposure population and missingness rules, source/summary producer, table columns/sort behavior, schema and whole-view responses, file owners and publication checks. verify independent observed facts, season/game reconciliation, detached reads, direct routes and manual activation/restore. source-driven fixtures verify boundaries; a declared real publication verifies the intended browsing path. selected lasting checks follow [07](07-lightweight-testing.md); exploratory/campaign checks remain temporary.

## exclusions and tradeoff

no xg, fitted attribution, adjusted maps, ability ranking, player comparisons, percentiles, arbitrary dates, public hosting, new acquisition or browser-triggered analysis. ability panels are absent; withheld 04b results do not enter under an observed label. observed shot maps can follow separately and do not delay this slice.

the accepted cost is some possible schema/view rework when supported ability arrives. the benefit is an independently useful website and design feedback while research continues. this intermediate does not fulfill the brief's chance-valued ability target or admit any model.
