# score-clock repair awaits scientific reassessment

status: software contract verified; the recorded scientific reassessment criterion remains open under [03e](../specs/03e-training-assessment.md). no further 03c repair or drive access is required.

problem: `2024020102` has an overtime `TAKEAWAY` at api `/plays/360`, event `1224`, with elapsed and remaining clocks both `00:00`. its unsupported elapsed time correctly stays null. the former preparation guard unnecessarily removed score support from every attempt.

impact: 03b retained 140 attempts: 88 unavailable and 52 outside 5v5. the narrow repair preserves the faulty clock and located issue while allowing independently supported timed goal accounting. unsupported goal clocks, unknown potentially scoring kinds and contradictory supported chronology still withhold scores.

evidence: [the complete native fixture](../../fixtures/captures/2024020102/) reproduces the body-equivalent historical case, including report `PL-384`. timed goals reconcile to 3–3; the final 3–4 includes a shootout. installed native preparation now supports scores; temporary contradictory/unknown-kind integration checks passed and were deleted. [the full comparison](../research/chance-03c/decision.md) explains population changes and unchanged elapsed coverage.

remaining resolution: repeat the originally required scientific assessment on a prospectively specified revised candidate with separately justified confirmation. 03d/03e own that work; no fitting is authorized here. source recovery alone cannot certify the old model or alter 03b's rejection. close this issue when the scientific criterion passes.
