# overlapping shift evidence

problem: the admitted `2025021094` shift response repeats two positive-length intervals for the same player. elapsed membership cannot be supported during either overlap without repairing source evidence.

impact: 118 seconds remain unresolved. supported intervals and reported event memberships survive; neither deduplicating rows nor unioning their durations establishes a justified full-game denominator. later population admission must assess this missingness.

evidence: `fixtures/captures/2025021094/shifts/body.bin`, `data[151..152]`: player `8476873`, team `12`, period 2 `18:28–19:20` (52 seconds); `data[156..157]`: the same player/team, period 3 `13:50–14:56` (66 seconds). the captured collection advertises and contains 735 rows. all original rows and their capture digest remain preserved. [fixture facts](../../fixtures/README.md) record the disjoint reconstruction and evidence limits.

reproduction: run the installed reconstruction command on this capture; inspect `overlapping_player_shifts` issues and the affected intervals. the reconstructed partition includes 118 unresolved seconds. the paired rows have different record ids and shift numbers, so identity uniqueness alone does not detect these overlaps.

resolution: admit a separately identified corrected source capture and verify unique, coherent intervals against the reported player toi and selected shift-report facts; or establish an explicitly attributed, independently supported correction in a later authorized evidence slice. keep the original response. removing the rows solely to obtain a complete denominator does not resolve this issue.
