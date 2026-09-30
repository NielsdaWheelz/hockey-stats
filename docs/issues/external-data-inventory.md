# external data inventory

status: blocked on the user's detached drive. during pr2c specification the user again confirmed local captures now, drive later; this does not block pr2c's bounded implementation and verification.

## problem and impact

the user reports a substantial downloaded dataset on an external drive. this session has neither mounted nor inspected it. source coverage, storage layout, original responses, derived tables, model artifacts, and reproducibility are unknown. assuming the old documentation describes the stored data accurately would risk importing corrupted or irreproducible evidence.

## evidence

user report on 2026-09-29; [verified raw-provenance defect](legacy-raw-provenance.md) in the predecessor; full archived source available locally at `.reference/hockey-stats-legacy/`.

## resolution evidence

on reconnection, inspect read-only first: record mount/storage layout, size and formats, game/season/feed coverage, manifests and hashes, capture dates, raw versus transformed records, and available database/export schema versions. inspect a few representative games through source → canonical → model lineage. identify recoverable originals and record gaps.

fresh [offline fixtures](../../fixtures/README.md) have since been admitted independently; [pr2b](../specs/02b-reconstruction.md) specifies their bounded extension. keep training data external and development fixtures local; lack of the drive must produce an explicit unavailable training input, not a silent change of dataset.

[02c](../specs/02c-corpus.md) implements verified season inventory, bulk bios and deterministic local corpus accounting for bounded local fixtures. it supplies reusable checks for this later audit, not an importer for an unseen historical layout. compare captured games with an attributed inventory, establish play-report coverage for event membership, and preserve reference provenance. reference acquisition and bounded local exercises need not wait for the drive; historical-data admission does. a directory containing downloaded games does not establish the expected population or reference-field provenance. 03–04 still decide scientific eligibility and training horizons. the [source audit](../research/source-audit.md) assigns coach evidence to 04's context decision and scratch interpretation to later availability work.
