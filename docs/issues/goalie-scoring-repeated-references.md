# repeated goalie scoring references

problem: actual evidence recomputes the same annual strength/state/type/population league totals for each goalie and each listed game, including detached validation. common-panel projection also repeats neutral branch reductions for every goalie.

impact: correct output with avoidable cpu cost. the first real score takes 13,179.20 seconds; evidence/projection writing takes 4,800.69 seconds and validation takes 3,601.95. these broad intervals do not isolate each repeated operation.

evidence: a one-second native sample at 2026-11-09 11:13:56 utc shows `math_fsum`, generator/string operations and tuple membership during evidence writing. source review traces annual `_totals` calls inside `_summary_evidence` for every game and in `_evidence_map`; independent review clears proposed explicit shared league references and one chunk-outer neutral reducer.

resolution: apply the reviewed private reductions; exact tiny old/new serialized evidence parity, exact chunk-boundary branch/raw/public parity and the required composition read of preserved real outputs must pass. retain the first completed score and all accepted fits. no sampling, schema change, target/solver change, cache framework or extra real rescore is required.

progress: both private reductions are applied. exact parity passes for 582 serialized evidence rows and eight branch/raw/public cases. no arithmetic mismatch occurred; the first temporary evidence-loader failure was repaired and preserved. the required composition read of the old first-real score through the new implementation remains pending. no speedup or full-real new-producer byte comparison is claimed.

resume finding: the user-interrupted second score takes 4,962.03 seconds before interruption in source preparation (peak resident memory 21,018,574,848 bytes). source review confirms both `prepare_execution_sources` and `reduce_goalie_game` repeatedly call default `cell_id`, which rebuilds the same centers, lookup and edges for each located attempt. the responsible callers can pass one local grid through the existing argument. the interrupted stack does not isolate this operation’s share of total runtime. exact bounded source-output/exception parity and independent review are required before the next real launch; no global cache or accepted-fit rerun is proposed.

source-grid progress: both owner-local changes pass exact serialized original/fixture source parity and all 16 coordinate outcomes; each owner constructs one grid. independent proof adjudication passes. the already required old-score composition read remains pending.
