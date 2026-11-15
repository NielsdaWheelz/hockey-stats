# mechanism fixture valuation

problem: the existing synthetic penalty example predates v1-10's strict shared valuation evidence. player `9000001` in `fixtures/publication-v1-13/results/20232024-penalties-skater_penalties.jsonl` has drawn rate/value `(3,3)` and taken rate/value `(-3,-3)`. no common `V` satisfies both `draw_value=draw_rate*V` and `take_value=-take_rate*V`.

impact: evidence cannot simply be attached during exchange4/schema10 conversion. this is a synthetic fixture contract gap, not evidence that real penalty estimates are wrong; those are not yet fitted. prior acceptance records retain their original scope.

resolution: [v1-10](../specs/v1-10-penalties-shootiness.md#publication-and-application) creates an attributed synthetic successor with independently recomputed consistent values, complete/neutral rates, support and valuation. preserve the original fixture byte-for-byte; require both strict readers and source-to-export checks. real pending rows remain null until their producer completes. remove this issue after the accepted successor/receipt proves resolution.
