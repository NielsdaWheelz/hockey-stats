# skating source inspection — 2026-10-22

documentation-stage inspection, not source admission or execution of [v1-04](../../specs/v1-04-skating-source-feasibility.md). three independent source, systems and quantity/content reviewers inspected the existing contracts and source candidates; root checked the shared capture/read and publication owners. no production capture receipts were created.

## observations

- the [official glossary](https://www.nhl.com/nhl-edge/glossary) defines sustained maximum speed and disjoint burst-speed categories. the source reviewer received a web-reader extraction; root's subsequent open timed out. this is definition evidence, not an exercised raw acquisition path.
- the [official launch account](https://www.nhl.com/news/nhl-edge-launches-website-for-puck-and-player-tracking-data) describes historical comparisons and curated rankings. those do not establish a complete player census.
- ordinary requests to `https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/8478402/{season}/2` for `20232024`, `20242025` and `20252026` each returned 403, `text/plain; charset=UTF-8`, 17 bytes, `error code: 1010` followed by a newline. one official listing probe at `https://www.nhl.com/nhl-edge/skaters/20252026/2/skating-speed/all` also returned 403; other listing seasons were not probed. this repeats the earlier access finding; it does not prove missing historical data or permanent impossibility.
- indexed official pages sometimes contain measurements while opening the same url yields only a shell or denial. the [fabbro/nikishin comparison](https://www.nhl.com/nhl-edge/comparisons/skaters/dante-fabbro-8479371/alexander-nikishin-8482100/20252026/2) requested 2025–26 but its indexed left-player selection showed 2023–24 playoffs. url parameters alone cannot validate returned seasonal facts. search snippets are not captured measurement evidence.
- no primary historical json body, literal measurement paths, full enumeration protocol or complete seasonal player universe was observed. community endpoint descriptions are discovery hints, not exercised primary schemas.

## consequence

the user selected bounded feasibility and a costed acquisition handoff, not conditional collection of all three seasons. use the ordinary production capture client for three initial historical probes; the full specification caps conditional inspection at twelve requests. preserve original receipts/bodies when execution is assigned. if blocked, stop with access evidence and an unobserved adapter. if readable, bind identity/year/scope, inspect literal fields and separately establish enumeration feasibility before proposing acquisition.

raw-value feasibility, full population coverage and eventual percentile eligibility are different results. existing schema7 transports `skating_max_speed_mph` and `skating_bursts_over20_count`; it has no structured census. v1-04 owns the source handoff; v1-17 owns publication/cohort integration. neither the audit nor a successful software fixture admits a real skating feed.
