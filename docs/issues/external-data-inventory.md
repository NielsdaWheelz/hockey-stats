# external data inventory

status: blocked on the user's detached drive; does not block research or architecture discussion.

## problem and impact

the user reports a substantial downloaded dataset on an external drive. this session has neither mounted nor inspected it. source coverage, storage layout, original responses, derived tables, model artifacts, and reproducibility are unknown. assuming the old documentation describes the stored data accurately would risk importing corrupted or irreproducible evidence.

## evidence

user report on 2026-09-29; [verified raw-provenance defect](legacy-raw-provenance.md) in the predecessor; full archived source available locally at `.reference/hockey-stats-legacy/`.

## resolution evidence

on reconnection, inspect read-only first: record mount/storage layout, size and formats, game/season/feed coverage, manifests and hashes, capture dates, raw versus transformed records, and available database/export schema versions. inspect a few representative games through source → canonical → model lineage. identify recoverable originals and record gaps.

choose a bounded offline fixture set only after that inventory, or capture fresh responses independently sooner if needed. keep training data external and development fixtures local; lack of the drive must produce an explicit unavailable training input, not a silent change of dataset. the fixture size budget and exact game list belong to the next specification, not an arbitrary corpus copy.
