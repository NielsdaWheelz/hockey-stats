# microstat reference-xg population metadata

problem: `execution_composition._method` supplies execution common-panel population/qualification/assessment wording to `reference-xg-v1-06-*` methods. the factual value actually uses personal ordinary5v5 attempts and matched `neutral_all_attempt_value` time. `analysis-values.ts` reads the method population into detail/exports, so the evidence currently describes a different population.

impact: reference-xg numbers/support need no refit, but a card-only label correction would leave misleading published provenance. existing `spatial_composition._accepted_source` also expects inherited method records byte-for-byte, so a corrected descendant needs an explicit narrow expectation amendment.

evidence: `analysis/src/hockey_stats/execution_composition.py:_method`; `analysis/src/hockey_stats/microstats.py:reduce_reference_xg,summarize_reference_xg`; `app/src/web/analysis-values.ts` method population selection. source inspection during the 2026-11-08 v1-17 specification review, not a numerical rerun. reproduce with an existing reference-xg method catalog row and the corresponding `FactValue` support; compare their population/qualification descriptions.

resolution: [v1-17's bounded correction](../specs/v1-17-microstat-cards.md#bounded-reference-xg-metadata-correction) fixes the producer, creates an attributed metadata-only successor and verifies exact unchanged numerical bodies/support/nonowned catalogs. both readers, field detail and exports must expose the correct personal population; spatial inheritance accepts only the expected attributed correction. preserve originals; no fit/rescore/preparation or direct database edits. delete this issue after real correction evidence passes; specification alone does not resolve it.
