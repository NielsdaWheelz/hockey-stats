# legacy raw provenance and invented handedness

status: confirmed archive defect; excluded from the chosen fresh-corpus path. retain this constraint until the replacement corpus is admitted and its source/missing-value checks are recorded. observed 2026-09-29 at legacy commit `1d45312ed4a2d797150e377c87ecdba231b5ebfc`.

## problem and impact

the predecessor transforms some upstream response bodies before raw storage. its roster augmentation also fills absent players with synthetic names and `shootsCatches: "L"`. this destroys the distinction between an observed left-handed player and unknown handedness. the [external audit](../research/external-corpus-audit.md) confirms all 20,956 stored boxscores have the projected player-list shape; 4,969 away-roster and 5,040 home-roster snapshots contain `Dressed`. matching stored hashes do not establish source originality.

## evidence and reproduction

- [live-projection.ts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/source-adapter/live-projection.ts#L149): `augmentRoster` supplies invented names and left-handedness.
- [port.ts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/source-adapter/port.ts#L133): fetch helpers apply projections before constructing landed bodies; roster calls use the augmentation at lines 508 and 518.
- inspect baseline fixture `packages/core/fixtures/corpus/2023020204/roster-home.json` and `roster-away.json`: respectively 10 and 5 rows have `firstName.default == "Dressed"`; all 15 set `shootsCatches == "L"`.
- [raw-snapshot-capture.ts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/per-game-ingest/raw-snapshot-capture.ts#L13) claims verbatim response preservation, but the upstream projection has already occurred.

## resolution evidence

before admitting old data, classify affected endpoints and determine whether untouched originals exist. preserve actual upstream response bodies before parsing or transformation in the replacement design. represent absent handedness explicitly; resolve it only from an attributed source. demonstrate a raw-response → derived-record case with missing roster fields, preserving original bytes and unknown values. any re-fetched replacement must retain its new capture date rather than impersonate the original snapshot.

the drive audit is complete for the reuse decision. the user chose fresh 2023–24 through 2025–26 captures; no legacy importer is planned. do not repair the archived code, invent capture receipts or rewrite historical evidence. retire this issue into the audit record after the replacement corpus demonstrates the stated admission contract.

replacement acquisition verified on 2026-09-29: [capture](../../app/src/operator/capture.ts) preserves bytes before parsing; temporary real-http checks passed for missing fields, unknown fields, invalid utf-8 and gzip decoding. [fresh fixtures](../../fixtures/README.md) replace the old baseline. the subsequent external audit resolves the reuse decision; fresh full-corpus admission remains to perform.
