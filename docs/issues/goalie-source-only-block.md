# locate the single source-only block exclusion

the accepted `20222023` goalie score has one source-included key without a complete immutable base score: `2022020554:252`. source/numerical counts and withheld fields reconcile; this is not evidence of a computational defect. its base exclusion reason has not yet been inspected.

one bounded coverage read identifies the key (2,124,608 bytes; sha256 `6a02178fda84775ffe35f50315c27a547dc94fc9721c71fdc776b9c8dbf0d551`). producer rules and the exhaustive saved partitions identify it as a block: 151,541 included source rows minus 113,179 paired unblocked rows equals 38,362 `blocked_outside_paired_unblocked` rows. that explains the paired-population exclusion, not why the base score is incomplete. no matching retained fixture or issue was found in the local index.

resolve with a bounded inspection of this exact key’s saved base disposition, then its one prepared/original event only if necessary. document the checked expected gap or repair any newly found computational defect at its owner. if it exposes a distinct broken capture case, preserve the complete original available bundle/receipts and season references under the fixture policy. no full annual event/body scan, input rerun or numerical retry is justified. body inspection is pending while the sibling owns the heavy window; no new source failure is claimed.
