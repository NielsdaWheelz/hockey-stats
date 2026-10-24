# transition availability must own one indicator

problem: the prior-clock transition owner makes existence, side and age jointly available, structurally absent or unavailable. the encoder nevertheless emitted both `unavailable:strength_transition` and `unavailable:strength_transition_age`. they are identical for every valid owner output, not merely correlated in a sample.

impact: two identical columns with ridge precision `4` give their common effect effective precision `2`, contradicting the specified one-indicator contract. recipe `0cbf1872` and its fixture fits are diagnostic history rather than qualification of the corrected design. the first real command was stopped during preparation; no output directory, fitted head or coefficient array was produced. factual processing under its separate owner was untouched.

evidence: known transitions have known side and age; known absence marks age structurally absent and fires neither indicator; unknown transitions fire both. [the interruption receipt](../research/execution-v1-05/real-first-year-interruption.json) records the exact stopped command, costs and retained logs. this defect was introduced by the new all-or-nothing transition contract; independently partial workload fields must not be merged by analogy.

resolution: use one shared transition availability condition, bind it in a new recipe, verify all three states and the effective precision, and pass a fresh complete five-year fixture chain with four final numerical probes. retain the old diagnosis and independent review, then remove this issue. restart real fitting only from that clean source freeze in a new external run directory.
