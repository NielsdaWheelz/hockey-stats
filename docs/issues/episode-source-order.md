# reviewed source order and execution predictors

problem: verified source order can place an awarded goal after the same-clock review stoppage that closed its live episode. v1-01 correctly preserves that order; episode-context availability can therefore carry outcome information.

impact: a later execution head must not treat episode presence as an innocuous predictor or infer release-time ordering from event ids. this does not invalidate retained source facts or change frozen research.

evidence: detached fixture review found `2021020942 /plays/300→301`, `2022020001 /plays/138→139`, `2024020022 /plays/235→236` and `2025020006 /plays/182→183`: stoppage followed by goal at the same clock. the goal has the lower event id but later verified sort order. four of 195 ordinary fixture goals have this pattern; those counts do not estimate five-season prevalence. [v1-01 verification](../research/evidence-v1-01/verification.md) retains the independent review.

resolution: v1-05/v1-07 must explicitly select predictor families and decide whether episode presence is excluded or a separately justified event-time rule is required. assess outcome-dependent availability before fitting. keep future `feature_facts.outcome` and `immediate_outcomes` out of predictors; do not repair source order implicitly in the producer. close this issue when the consumer contract and its verification enforce that decision.
