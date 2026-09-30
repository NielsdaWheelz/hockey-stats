# offline source corpus

owner: [03c offline-evidence amendment](../specs/03c-source-revision.md#offline-evidence-amendment). status: pending copying and verification, not a completed dataset.

problem and impact: the committed raw corpus has only three 2025–26 games and one season-reference bundle. known cross-season failures and the complete source corpus remain on the external drive, limiting detached verification.

evidence: on 2026-09-30, `du -sh fixtures` reports 6.1 mib; [fixture facts](../../fixtures/README.md) identify the three games. the [03b verification](../research/chance-03b/verification.md) distinguishes the local review mirror from original source captures; extracts are not complete input bundles.

resolution: preserve the specified ordinary/failure cases with originals, references and checked facts; measure raw corpus storage and copy the chosen larger population outside git. verify byte identity, inventory/source dispositions, explicit omissions and native detached processing. record results in the fixture index and 03c decision; a reduced local selection does not replace 03c's full audit. delete this issue and its live links when resolved.

blocker: original captures must be accessible for copying; no further re-download can recreate their historical byte identity. fixture preservation and manual copying do not wait for the pr07 harness.
