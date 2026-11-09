# repeated goalie scoring references

problem: actual evidence recomputes the same annual strength/state/type/population league totals for each goalie and each listed game, including detached validation. common-panel projection also repeats neutral branch reductions for every goalie.

impact: correct output with avoidable cpu cost. the first real score takes 13,179.20 seconds; evidence/projection writing takes 4,800.69 seconds and validation takes 3,601.95. these broad intervals do not isolate each repeated operation.

evidence: a one-second native sample at 2026-11-09 11:13:56 utc shows `math_fsum`, generator/string operations and tuple membership during evidence writing. source review traces annual `_totals` calls inside `_summary_evidence` for every game and in `_evidence_map`; independent review clears proposed explicit shared league references and one chunk-outer neutral reducer.

resolution: apply the reviewed private reductions; exact tiny old/new serialized evidence parity, exact chunk-boundary branch/raw/public parity and the required composition read of preserved real outputs must pass. retain the first completed score and all accepted fits. no sampling, schema change, target/solver change, cache framework or extra real rescore is required.
