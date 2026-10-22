# 05h — observed deployment context

approved direction stub, 2026-10-21. [the plan](../plan.md) owns assignment. specification can proceed alongside 04m; implementation requires a settled [02d exposure contract](02d-source-exposure-consistency.md), including any gaps explicitly retained. no implementation or publication is assigned here.

## target

add two tables to the selected player-season profile: **teammates shared with** and **opponents faced**, ordered by included 5v5 minutes, with links to existing profiles. use the three-season navigation and seasonal identities already supplied by 05g. these explain the deployment behind the observed card/maps without claiming teammate quality, chemistry or isolated ability.

aggregate overlap from all admitted on-ice intervals, including zero-event time. preserve the selected player's matched on-ice support and coverage; do not derive minutes from shot-event co-occurrence or intersect them with personal/spatial eligibility. include skaters only, exclude self, and retain player ids across team changes. seconds are the authoritative quantity; minutes are display units. over complete admitted five-skater intervals, teammate overlap sums to four times the player's included seconds and opponent overlap to five times; these are accounting checks, not independent observations.

python owns aggregation; the existing sqlite publication, effect reader/api and profile own storage, transport and display. no browser source reconstruction or new service. the full spec will settle exact rows/keys, API shape, table size/presentation, tie order, coverage copy, absent/unavailable states and independent acceptance checks. a content designer must make shared minutes, selected season and coverage intelligible beside linked identities.

exclude together/apart outcome rates, chemistry, quality-of-teammate/opponent scores, inferred line tiers, adjusted effects, new maps, percentile ranks and comparison/export expansion. personal-shot maps remain a distinct later capability. the cost is one new factual aggregation and publication rebuild; the benefit is context for existing results without awaiting an ability model. 04m supplies no data dependency or admission authority.
