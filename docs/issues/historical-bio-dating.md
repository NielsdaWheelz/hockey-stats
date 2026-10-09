# historical biography dating

status: open source-time limitation. owner: 03k trait preparation/off-wing use; 04 historical-use cutoffs and attribution. the full 03k spec preserves retrieval dating and requires an explicit retrospective trait-stability assumption for off-wing selection. implementation is not yet assigned; historical source availability remains unproved.

problem: season-filtered biography reports captured on 2026-09-30 do not establish when admitted `shootsCatches` values were effective or available during historical games. agreement across these fresh reports is not agreement across historical snapshots.

evidence: `reviews/omission-source-notes.json` under the [03e run root](../research/chance-03e/protocol.md#evidence-and-execution) retains original reference receipts, source locators and the admitted field contract. shooting/catching hands are available for 1,022/1,041, 1,023/1,041 and 1,037/1,063 roster ids across the three seasons; 19/18/26 remain missing. these are roster counts, not eligible-event coverage. no per-observation effective/history timestamp is admitted for this field. the 2025–26 skater-bio row `/data/830/shootsCatches`, player `8486169`, is explicitly null.

impact: later source knowledge could be presented as historically available information, or used in off-wing geometry without a stated stability assumption. current chance-2 omits handedness; this evidence neither requires adding it nor identifies an existing fitted-feature error.

resolution: before affected 03k/04 use, implement effective-time/known-as-of metadata and the permitted retrospective interpretation; verify null/conflict and explicit-assumption behavior. support historical claims with attributable dated evidence or restrict the claim/use explicitly; retain missing values and disclose any trait-stability assumption. close when the chosen historical-use contract and its verification prevent unsupported dating. no new collection or feature is required if the affected use is declined.
