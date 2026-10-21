# pr05d — richer descriptive cards

status: **later stub; not ready for implementation.** [the plan](../plan.md) owns sequencing/assignment. extend the [05c explorer](05c-player-explorer.md) toward readable, downloadable descriptive player cards; do not preassign every field found on a reference site.

## intended capability

select a small useful set of personal scoring/shot and usage facts, publish them under explicit definitions, then compose a compact card with existing on-ice results and peer context. personal shots, goals and primary assists are candidate fields, subject to their actual source/reconstruction support; they are not already present in the website contract. preserve completed-season 5v5 scope unless the user separately changes it.

the downloaded card must retain player, season, strength state, units, exposure, coverage, cohort when used and publication/definition context. its values must reconcile to the same table/profile; exporting an attractive image cannot discard consequential limitations.

## ownership and dependencies

python owns new fact derivation, population matching and published aggregates. extend the existing observed sqlite/export contract and effect schemas/readers when needed; no second exporter or client-side hockey calculation. reuse the current card/table presentation. any republication is explicit; no new acquisition is implied.

numeric percentiles are a later candidate here, not automatic scope: first define peer eligibility, treatment of ties/missingness, metric direction and authoritative ownership. keep original magnitudes beside ranks. no combined percentile score, predictive war label or relabeling observed rates as offensive/defensive ability.

## settle before a full specification

- exact fields, source provenance, numerator/denominator and missingness; audit retained facts before proposing new capture.
- whether the useful field set and export fit one cohesive slice; split derivation from presentation if their independent contracts warrant it.
- cohort/percentile policy if selected; export format and layout; concise definitions and coverage text.
- independent source-to-publication reconciliation and rendered/live card checks, including missing values and traded players.

tradeoff: closer to the descriptive parts of hockeyviz/jfresh cards, with genuine producer/publication work beyond frontend changes. this supplies no supported ability, special-teams model, historical trajectory or forecast. [05e](05e-spatial-views.md) records the distinct spatial dependency.
