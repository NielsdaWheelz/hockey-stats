# descriptive minimal refactor

2026-10-22. removed the unused `SEASONS` import, inlined the one-use player-game dictionary constructor, and removed unused source-id parameters/paths. strength cardinalities, goalie presence and conversion counts now have explicit role/unit names. no population, formula, support rule or specified public boundary changed.

[exact before/after evidence](../receipts/descriptive-refactor-equivalence.json) covers all 24 actual displayed fixture games and 723 skaters across three seasons. it compares fixed per-game evidence, complete descriptive/microstat game reductions, people and both season summaries. recursive canonical values preserve dictionary/container classes, `Counter`, `defaultdict` factories, dataclass classes/fields, sequence classes, scalar types and key types. all three canonical values and hashes match exactly.

[the current consumer check](../receipts/refactor-consumer-green.txt) sends actual before/after producer contexts through the existing typed overview, value selectors and cohort owner. all 245 teammate and opponent datums, 77-member defender cohorts and selected standings match exactly. root's already-running full candidate run remains valid for this inert refactor; no additional six-pass facts run was started. the real run uses the refactored source.

before source sha256: `16622c087542f967f63a54c2a7016e28f0f0886673383c4d4debf7999053228a`. after source sha256: `191b33425ebd5f833ec9c42a4bfd89376c2c7e53f5ba4805b5f7ff3a581431de`.

independent publication review cleared the source diff and canonical comparisons. root authorized cleanup after final green; owned disposable controllers and large canonical snapshots were deleted; the compact receipt retains exact inputs, counts, hashes, comparison scope and consumer outcomes.
