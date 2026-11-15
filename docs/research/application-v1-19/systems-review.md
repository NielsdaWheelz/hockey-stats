# independent systems and export review

scope: native navigation agent reviewed the card, detail, map adapter and export owners independently of their implementation. this review covers software behavior and the fixture publication. real candidate integration remains a separate acceptance obligation.

## findings and repairs

- unavailable map, danger, stage and game csv paths supplied one detail cell beneath a wider closed header. the shared `goalieCsv` owner now writes the complete declared width with blank inapplicable cells. inner pending availability/reasons also survive the common envelope. the independent eleven-case [export contract check](receipts/systems-export-contract-green.json) verifies unavailable and provided row widths, unique headers, exact-state raw-only metadata and required-map failures. the repair is at [the finite csv encoder](../../../app/src/web/goalie-evidence.tsx#L246), rather than four separate padding implementations.
- while a new population request was pending, the displayed old card and selected plots still offered downloads. the delayed-fetch [red receipt](receipts/pending-export-red.json) records six held actual-map reads and enabled old-selection buttons. profiles/comparison now disable the existing goalie card/detail fieldset and shared distribution/history download buttons while their loader is pending, with an explicit visible reason. selection controls remain usable. owners: [profile](../../../app/src/web/routes/player.tsx#L354), [comparison](../../../app/src/web/routes/compare.tsx#L424), [distribution](../../../app/src/web/peer-distributions.tsx#L691), [history](../../../app/src/web/analysis-history.tsx#L1028). node24 typechecking passes. live green verification awaits the root-owned rebuild; the red deployment is not claimed fixed by a source check alone.

## checked behavior

an already-started png export has a different contract from initiating an export while new data are pending. the native [snapshot check](receipts/started-export-snapshot-green.json) held png completion, changed population, mode, cohort cutoff and season, then released it. the downloaded 1200×6062 png retained the original 20232024 ev/unblocked additive selection and its original filename. it was an actual png download; no screenshot substituted for export.

card preparation rejects missing overview or fixed type maps. preparing another season/population/cohort leaves an existing render model byte-identical when serialized to svg. the eleven-case contract check also verifies thirteen exact-state scalar rows plus three raw history rows; percentile, peer group, cutoff, cohort size and membership cells remain blank. goalie-card scalar rows reuse the shared envelope, including exact `goalie_detail`; `evidence_population` remains distinct from the shared scalar `population` column.

map preparation retains the published one/two-player scale. exports consume the same render model and physical geometry helper as inspection/drawing; actual ratio cells retain their undefined mask and sign. no browser refit, source read, rebinning or probability composition was found. source proofs remain supplied publication data. model and actual references retain separate selectors.

## proportionality

`GoalieDetails` currently prepares the same card model again to reuse complete type accounting. this repeats finite client rendering work but introduces no second analytical implementation, request or divergent arithmetic. it is not a correctness blocker. no extra lifecycle/cache mechanism is recommended.

no additional concrete systems finding remains beyond the pending live verification of the export guard. this scoped review does not certify scientific quality, real source coverage or full-spec completion.
