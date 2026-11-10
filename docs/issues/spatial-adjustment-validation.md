# spatial adjustment validation parity

problem: python's publication validator checks the saved seven-field actual-context decomposition with term-scaled floating-point tolerance, finite intermediates and a bounded residual. `app/src/shared/player-analysis.ts` currently uses generic net-relative closure only. the two contracts disagree under cancellation; the typed check also lacks the independent residual bound.

impact: v1-18 will expose these already-stored quantities through selected evidence. copied valid output must pass the same rule at both boundaries, and an excessive compensating residual must not pass merely because the final sum closes. this is separate from the scientific problem of extreme actual-context allocations; it does not establish that current candidates are corrupt.

evidence: `analysis/src/hockey_stats/analysis_publication.py`, `adjustment_decomposition` branch; `AdjustmentDecomposition` in the typescript file above. compare a large cancelling set of first-five terms plus a small arithmetic residual; separately inject an excessive residual while preserving the net sum.

resolution: [v1-18](../specs/v1-18-analytical-skater-sheet.md#publication-and-evidence-api) applies the original python rule in the typed owner, independently checks finite arithmetic, closure and residual bounds, and preserves real saved values. delete this issue after verified parity; retain the [actual-context interpretation issue](spatial-actual-context-extremes.md) and original precision verdict.
