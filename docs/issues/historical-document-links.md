# historical document links

problem: two frozen 03e documents link to the deleted `docs/issues/historical-bio-dating.md`: [decision](../research/chance-03e/decision.md) and [protocol](../research/chance-03e/protocol.md). both links predate the 04n specification.

impact: readers cannot follow the original bio-dating evidence; no numerical input or scientific result changes.

evidence: `git grep -n historical-bio-dating HEAD -- docs/research/chance-03e` finds both references; the target is absent. the 2026-10-21 documentation check preserved the frozen files.

resolved when both references have a durable historical evidence destination without changing the frozen scientific account or reopening a resolved source issue.
