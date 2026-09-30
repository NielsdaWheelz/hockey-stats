# shot types retained in reports but omitted from interpretation

status: open; source-admission responsibility in [03c](../specs/03c-source-revision.md).

problem: interpretation preserves play-report descriptions but omits their structured shooter/type attributes. the earlier model audit inferred a general lack of block types from api missingness alone.

evidence: all 111 blocks in the three current fixtures have an explicit report type; none has api `shotType`. on 249 matched unblocked attempts, report types agree with the api. [counts, hashes and reproduction](../research/chance-03c-source-audit.md). these are bounded source facts, not league-wide coverage or physical-origin truth.

impact: usable evidence is unavailable to matching and later models. this does not establish that adding type fixes conversion or origin estimation. unknown grammar, contradictory sources and outcome-dependent recording must still be assessed.

resolution: attribute report shooter/type fields, reconcile matched source values without overwriting either, preserve conflicts/missingness, and audit coverage/agreement by season/outcome on the admitted corpus. verify raw bytes unchanged and source joins independently. numerical type conditioning belongs to the subsequent model specification. the detached drive delays full-corpus verification, not specification.
