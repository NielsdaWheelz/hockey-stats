# v1-15 implementation and verification

status: **software complete; real card integration pending.** the assigned [specification](../../specs/v1-15-comparative-card-discovery.md) works through the actual typed schema7 api against checked fixtures. synthetic numbers establish application behavior, not real player estimates or scientific support. actual v1-03/06/12 outputs and their upstream producers close real comparative-card delivery. no source acquisition, fit, primary serving build, publication rotation, activation or admission was performed.

## source and input identities

worktree: `/Users/nnandal/Documents/code/hockey-stats-v1-15`; branch: `implement/v1-15-comparative-card-discovery`. base: `1753e8efcab7a77b25cc67ec468e82c24b8c5294`. context-only commit `ec95981` preserves the seven supplied specification/context documents copied from the main checkout; main originals were not edited. the implementation commit containing this receipt owns the final changes. [code/input identity receipt](receipts/identities.json) records exact source and fixture hashes.

node `24.21.0` and existing locked dependencies were used. no dependency or wire/storage/numerical-producer change. the fixture candidate is publication `67029d34-5ba1-4549-956c-48918b7c886a`, purpose `fixture`, database sha256 `5b726441170ca2ecbb10837b4f2ce509140b650daa82586aaa0fcca82aee91f7`, 20,299,776 bytes. [candidate receipt](receipts/candidate.json) retains corpus/manifest/member identities, original observation checks and read-back evidence. assembly/read-back took 3.72 seconds, process high-water rss 220,872,704 bytes; neither is a full-season capacity measurement.

reuse [v1-13 originals](../../../fixtures/publication-v1-13/README.md) and [v1-14 cases](../../../fixtures/publication-v1-14/README.md). all original captures and analytical member bytes are preserved. rebuilding the six captured games at this worktree changed only the copied manifest's declared corpus hashes. [v1-15 checked facts](../../../fixtures/publication-v1-15/checked-facts.json) specify the additional response transformations and independently calculated expectations. detail/history/cohort projections receive the same declared synthetic transformation before ordinary typed decoding. no synthetic record is attributed to a captured player.

## implemented contracts

one fixed prepared card supplies html and png: annual identity/usage, supplied league/replacement totals, ten ordered tiles, two embedded percentile histories and ten independently inspectable signed ledger terms. the full-workload ledger contribution remains distinct from standalone finishing per100, recorded goals/a1 rates and counterpart usage. there is no browser ledger reconstruction. each field retains its own qualification, uncertainty, support, prior-only state, source and reference. missing ranks preserve usable magnitudes. annual cohorts and shared history preparation preserve gaps, semantic changes and F/D reference changes; ordinary annual method ids do not create false breaks.

identity-based discovery and comparison include all 84 published skaters, including 12 without observed summaries. `min=0` retains unknown time; positive display minimum excludes it with an explicit count. filters never redefine percentile cohorts. all seven presets and 21 valid family/strength combinations were exercised. exact-family reads left-join by checked identity; missing rows remain missing. numeric sorts use unrounded values, nulls last, deterministic ties and visibly labeled semantic partitions. finite route state preserves explicit valid metrics, observed navigation and local peer/filter/history controls.

visible-table csv shares the existing analysis serializer and a narrow metadata encoder. its 64 columns retain exact native values, display units, status/support and original metadata evidence; unranked quantities have no forged metric or percentile. two visible synthetic players produce 30 overview rows, in exact player/column order. each comparison card exports separately. existing observed cards, selected-field history/distributions, maps, deployment, games and exports remain available; one unavailable observed side does not remove the other. existing goalie behavior remains separate.

## red, green and adversarial review

[root red receipt](receipts/root-red.txt) records the original failure to discover all overview identities. implementing agents independently owned data composition, discovery/content and card/history; root reviewed their boundaries and live integration. an independent reviewer inspected the full change and constructed schema-valid counterexamples. [independent review](independent-review.md) records the two findings and their independent clearance: embedded observed identity mismatch and indistinguishable semantic-partition labels.

additional review repairs covered absent exact-family comparison rows, unnecessary comparative map revalidation, unavailable usage/time reasons, original workload/known-slot evidence, independent replacement-column uncertainty, duplicate peer controls and svg title warnings. internal renderer helpers/types became private after reviewing actual consumers. no unresolved implementation finding remains.

| affected boundary | final evidence |
|---|---|
| typed loaders and requests | [23 live checks](receipts/root-green.txt), [request/byte receipt](receipts/root-live.json); invalid/duplicate/absent selections, absent current year, mixed publication/catalog/value contradictions and shared annual reads |
| observed adapter | five selectors × 72 captured rows × three seasons: exact endpoint parity; [17 identity/support contracts](receipts/identity-green.txt), including schema-valid id/name/position/team contradictions that must reject |
| discovery | [all 21 combinations](receipts/discovery-green.txt), null-last ties/semantic groups, exact-family left joins, filters and ordered csv; [independent checks](receipts/independent-review.txt) |
| card/history | [render contracts](receipts/render-green.txt): ten tiles, ten ledger terms, four annual series, exact signed values, specialty prior-only/independent qualification, gaps and changed meanings/positions |
| browser integration | [23 live browser assertions](receipts/browser-tests.json), zero errors: complete/partial cards, two-card comparison, preserved observed/goalie paths, local cutoffs/reset, png failure/retry, navigation during encoding and 320px layout |
| native navigation/export cost | [season link, browser back/forward and png sample](receipts/interaction-cost.json) |
| detached serving | [all five api endpoints return 200](receipts/detached.json) while source directories and the external drive are denied by an operating-system sandbox; [denied read control](receipts/detached-source-denied.txt) |
| final compile | [pinned typecheck](receipts/typecheck-green.txt), [isolated build](receipts/build-green.txt) after temporary-test deletion; whitespace and documentation links checked |

## native rendering and saved outputs

[native check record](receipts/native-checks.json) distinguishes actual visual, accessibility-tree and keyboard checks from unperformed audits. wide layouts, a 320px application viewport and native 200% browser zoom were inspected. long names wrap. both peer cutoffs have labeled inputs and explicit apply buttons; native Return submission changed the general cutoff and standing. history images have names and adjacent exact-value tables. no VoiceOver session or comprehensive accessibility audit was run or claimed; no historical waiver is reused.

[native output receipt](receipts/native-exports.json) records saved file hashes and dimensions. the complete comparative png is 1200 × 8623; the partial card is 1200 × 7009. both retain all ten tiles, both plots, numerical reference/workload, annual raw values/n/cutoffs/reasons, signed ledger values and exact support/provenance. saved observed and history png controls are 1200 × 1695 and 1200 × 2172. retry and navigation-during-encoding pngs are byte-identical to the original complete export: new-season content rendered before the delayed callback, while the saved image retained the original snapshot. the independently parsed csv retains seconds natively and minutes for display, with empty inapplicable rank fields and correct textual formula escaping.

accepted presentation cost: exact per-field and annual evidence makes the saved png substantially taller than the reference image. the leading comparative composition stays compact; a content-sized footer preserves the essential meanings instead of truncating them. tables scroll locally at 320px; document width remains exactly 320px. plots stay fixed percentiles, with original magnitudes available in their evidence tables.

## bounded costs and limitations

| fixture journey | api reads | uncompressed response bytes |
|---|---:|---:|
| default discovery | 1 | 441,795 |
| comparative profile / observed selected metric | 4 | 2,215,475 |
| profile with exact 5v4 execution detail | 7 | 3,086,238 |
| exact-strength discovery | 2 | 729,944 |
| comparative pair | 5 | 2,965,657 |
| partial observed pair, including map | 6 | 3,345,027 |
| complete synthetic card | 4 | 2,477,787 |

[measured read samples](receipts/root-live.json) report each request's elapsed time and size. overview reads are reused within one loader, with no persistent cache; comparative routes request no maps. own annual corpora and catalog/value consistency remain checked. this accepts a few megabytes of bounded scalar reads to preserve the existing typed api and avoid another service/cache contract.

[one local render sample](receipts/render-cost.json) records model preparation, static html rendering and byte size. [the native export sample](receipts/interaction-cost.json) took approximately 1.01 seconds from click through png encoding and local artifact save, including test polling; it is not an isolated codec benchmark. the complete saved png is 3,236,925 bytes. browser settling samples include polling/waits, rendering and API work and must not be read as isolated render timings. no full-season performance claim follows; [map-volume measurement](../../issues/publication-map-volume.md) stays with its owning real integration.

real producer integration remains pending and must check actual complete card/export values through these same owners. fixtures do not supply calibration, recovery, causal isolation, private-model parity, forecasts or calibrated uncertainty. existing historical scientific verdicts remain unchanged.

## cleanup and preservation

[cleanup receipt](receipts/cleanup.json) inventories temporary tests/controllers before deletion and verifies their absence after final green. no test-only dependency or public test interface remains. attributed fixtures, checked expectations and compact evidence receipts are retained. only owned task listeners/downloads/scratch were removed; the isolated worktree and branch remain for review. the final compile runs after deletion, without regenerating tests.

[protected-state receipt](receipts/protected-state.json) compares all 30 protected primary-build/database files by hash, size and nanosecond modification time, plus the original port-3000 process identity. the main build, active/previous databases and listener remain unchanged. no original source capture or expensive fit was modified. no pr, merge or activation was performed.
