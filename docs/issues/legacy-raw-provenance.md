# legacy raw provenance and invented handedness

status: open salvage constraint. fresh capture now preserves unchanged client-body bytes; external-corpus provenance and derived missing-value handling remain unresolved. observed 2026-09-29 at legacy commit `1d45312ed4a2d797150e377c87ecdba231b5ebfc`.

## problem and impact

the predecessor transforms some upstream response bodies before raw storage. its roster augmentation also fills absent players with synthetic names and `shootsCatches: "L"`. this destroys the distinction between an observed left-handed player and unknown handedness. an external-drive dataset produced through this path may contain altered records even when labeled raw. the drive has not been inspected, so affected extent is unknown.

## evidence and reproduction

- [live-projection.ts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/source-adapter/live-projection.ts#L149): `augmentRoster` supplies invented names and left-handedness.
- [port.ts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/source-adapter/port.ts#L133): fetch helpers apply projections before constructing landed bodies; roster calls use the augmentation at lines 508 and 518.
- inspect baseline fixture `packages/core/fixtures/corpus/2023020204/roster-home.json` and `roster-away.json`: respectively 10 and 5 rows have `firstName.default == "Dressed"`; all 15 set `shootsCatches == "L"`.
- [raw-snapshot-capture.ts](https://github.com/NielsdaWheelz/hockey-stats-legacy/blob/1d45312ed4a2d797150e377c87ecdba231b5ebfc/packages/core/src/ingestion/per-game-ingest/raw-snapshot-capture.ts#L13) claims verbatim response preservation, but the upstream projection has already occurred.

## resolution evidence

before admitting old data, classify affected endpoints and determine whether untouched originals exist. preserve actual upstream response bodies before parsing or transformation in the replacement design. represent absent handedness explicitly; resolve it only from an attributed source. demonstrate a raw-response → derived-record case with missing roster fields, preserving original bytes and unknown values. any re-fetched replacement must retain its new capture date rather than impersonate the original snapshot.

blocker for corpus audit: external drive detached. do not repair the archived code or rewrite historical evidence as part of documentation work.

replacement acquisition verified on 2026-09-29: [capture](../../app/src/operator/capture.ts) preserves bytes before parsing; temporary real-http checks passed for missing fields, unknown fields, invalid utf-8 and gzip decoding. [two fresh games](../../fixtures/README.md) replace the old fixture baseline. this resolves new acquisition fidelity, not the detached corpus audit or the later derived-record demonstration.
