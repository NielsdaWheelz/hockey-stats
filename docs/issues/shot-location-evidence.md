# shot-location evidence

status: open; source semantics and imputation validation. identified 2026-09-29. inclusion through blocked-origin imputation is now settled by the user.

problem: a coordinate attached to an event is not necessarily the shot's origin. the intended all-attempt analysis includes blocked shots, but has not yet established the supported source semantics, origin estimator or its accuracy and downstream sensitivity.

evidence: hockeyviz's [xg 8 description](https://hockeyviz.com/txt/xg8) distinguishes block locations from shot origins and describes imputation for blocked shots and some tip locations. its [magnus 9 description](https://hockeyviz.com/txt/magnus9EV) uses inferred blocked-shot origins. these published observations motivate an audit; they do not independently verify the semantics or error rates of our future captures.

pr2 inspection, 2026-09-29: the two [admitted captures](../../fixtures/README.md) contain 77 blocks whose owners agree with roster-resolved shooting teams. 66 opposing-player blocks have reported zone `D`; 11 explicitly teammate-blocked attempts have zone `O`. a generic zone-to-owner interpretation or blanket ownership reversal would be wrong for these inputs. preserve recorded coordinates, zone and defending-side evidence in pr2; establish the analytical frame in reconstruction and shooting origins in chance valuation. these checks do not validate spatial accuracy or origin inference.

impact: treating a block coordinate as a shooting coordinate can misplace chance quality and player effects. excluding blocked attempts instead changes the modeled opportunity population; it is not a semantically neutral cleanup. neither silent relocation nor silently declaring the source coordinate correct is acceptable.

resolution: inspect attributed captures for each supported event/source version; document coordinate meanings and hand-check selected examples against independent evidence where available. specify the origin estimator and handling of missing, ambiguous, blocked, and tipped locations. retain observed fields, attributed inference rules, and evidence about reconstruction error or its limits. verify normalized origin weights, conserved event contributions, source/cutoff provenance, and downstream sensitivity of chance values, maps and player estimates. distinguish fixed-imputer results from uncertainty propagated through imputation. evaluate the same population contract throughout the pipeline. an unblocked-only benchmark does not resolve the selected blocked-origin requirement.

blockers: the external corpus remains uninspected; the [inventory](external-data-inventory.md) and initial source-contract specification precede admission. published methodology alone does not admit the legacy data.
