# prepared evidence size

problem: the v1-01 closed json record contract repeats located prefix/context evidence and missing-field reasons for every player and chunk. compact serialization removes whitespace but cannot share those objects on disk.

impact: real five-season preparation occupies 397,784,660,779 bytes excluding the manifest and takes 33,732.702 seconds, with 5,420,793,856 peak resident bytes. repeated full reader passes also incur material json decoding and validation cost. this is an operating cost, not a computational or scientific failure.

evidence: the [real artifact receipt](../research/evidence-v1-01/real-artifact.json) independently matches the exact file set and byte total. the contract requires direct fact envelopes and closed game/member shapes; an interned evidence table would change that storage contract. the volume had room for this artifact. two full public-reader/source season checks pass; the other checks and final reader-cost measurement are paused at the user's request before drive disconnection.

resolution: record the remaining full-reader cost and retain the specified format for this delivery. a later storage revision needs an explicit contract preserving located reasons, identities, partitions and source-independent reads; no silent schema drift or source reparsing. delete this issue after the measured costs and this engineering disposition are recorded in [verification](../research/evidence-v1-01/verification.md). [the plan](../plan.md) owns progression.
