# microstat source availability and delivery

status, 2026-10-22: the [v1 field crosswalk](../product-inventory.md#microstat-skater--s02-and-documented-fd-variants) and [canonical contracts](../specs/experimental-card-facts.md#microstat-quantities-and-populations) are complete. the twenty-field forward and defense variants contain twenty-nine distinct fields. implementation and source acquisition remain separate; [the plan](../plan.md#proposed-pr-boundaries-and-dependencies) owns assignments.

## problem and impact

six fields are constructible from admitted event facts plus the specified execution model: goals, primary assists, personal unblocked attempts, hits, blocker share and reference xg. only the first two already have the required published personal-rate owner. missing code for the other four is required v1 work, not inaccessible evidence. source validity/matched exposure still needs verification in the new reducers.

twenty-two fields need observations absent from the admitted corpus: observed pass links/play categories, controlled crossings, pressure/retrieval/touch evidence and targeted entry defense. source-valued puck management additionally needs its model/reference and eligible-play denominator. inferred setting/territory do not establish these measurements. required cells can remain explicitly unavailable; no source percentile becomes invented raw data.

skating is a separate public-measurement family. maximum mph and 20+ mph burst count have honest independent definitions; historical payload/schema/census is not yet verified. no private composite is promised. access failure is neither a zero nor proof that acquisition is impossible.

## checked evidence and bounded follow-up

- the [official guide](https://hockeystats.com/about/microstat-player-cards) defines F/D fields; the [provider glossary](https://www.allthreezones.com/player-cardsfaq.html) qualifies credited actions and tracked windows. [current workbook](https://www.allthreezones.com/tableau-workbook-2021-present.html) and [data links](https://www.allthreezones.com/a3z-data-links.html) redirected to member login on 2026-10-22. no paid access or representative open historical tracking corpus was admitted.
- [official NHL documentation](https://www.nhl.com/news/nhl-edge-launches-website-for-puck-and-player-tracking-data) establishes public skating aggregates. the official player page exposed no measurements in the server-readable response. ordinary requests to `https://api-web.nhle.com/v1/edge/skater-skating-speed-detail/8478402/{season}/2` for `20232024`, `20242025`, `20252026` returned 403. no access bypass or bulk capture occurred; endpoint names alone are not an exercised primary schema.
- local fixture games `2023020001`, `2024020001`, `2025020001` and current source code establish usable role fields, not season-wide completeness. existing `observed.py`/`scoring_credits.py` own goals/a1; new factual reductions reuse reconstruction and validate actor/team roles.

resolution: v1-03/06/17 implement and verify the constructible fields and complete card; v1-04 performs the bounded primary skating feasibility/admission handoff. if tracking later becomes accessible, a source-specific adapter must first pin the actual protocol/schema, ids, observed windows, numerator/denominator and rights evidence described in the factual appendix. no general importer or acquisition campaign is authorized here. retain explicit source limitations and replace this issue only when attainable-field delivery receipts and any remaining source-specific blockers are recorded; neither unavailable tracking nor a blocked skating probe delays unrelated cards.
