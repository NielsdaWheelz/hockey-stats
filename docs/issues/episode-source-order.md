# reviewed source order and execution predictors

problem: verified source order can place an awarded goal after the same-clock review stoppage that closed its live episode. v1-01 correctly preserves that order; episode-context availability can therefore carry outcome information.

impact: a later execution head must not treat episode presence as an innocuous predictor or infer release-time ordering from event ids. this does not invalidate retained source facts or change frozen research.

evidence: detached fixture review found `2021020942 /plays/300→301`, `2022020001 /plays/138→139`, `2024020022 /plays/235→236` and `2025020006 /plays/182→183`: stoppage followed by goal at the same clock. the goal has the lower event id but later verified sort order. four of 195 ordinary fixture goals have this pattern; those counts do not estimate five-season prevalence. [v1-01 verification](../research/evidence-v1-01/verification.md) retains the independent review.

resolution: v1-05/v1-07 must explicitly select predictor families and decide whether episode presence is excluded or a separately justified event-time rule is required. assess outcome-dependent availability before fitting. keep future `feature_facts.outcome` and `immediate_outcomes` out of predictors; do not repair source order implicitly in the producer. close this issue when the consumer contract and its verification enforce that decision.

## v1-05 real preflight — 2026-10-24

independent review reproduced the defect through the accepted real prepared reader at `2025020006:183`. the video-review stoppage at `/plays/182` closes episode `28`; the ordinary goal at the same period/clock then has no episode. the current execution consumer consequently changes recent context to `none` and substitutes `.2 none/.8 unknown` for the named setter universe. the original earlier block at `/plays/181` is two seconds earlier. this is a consumer defect, not invalid prepared evidence, and real fitting has not started.

removing an episode-presence column is insufficient: selected recent families, reset-dependent strength-transition context and setter branch construction consume that history implicitly. shift-continuity defender sequence is independent of this reset and must not be discarded merely by association. the user approved the [uniform prior-clock amendment](../research/execution-v1-05/timing-amendment.md): require both supported earlier source order and a strictly earlier clock, retain current membership and declare lost within-clock precision. implementation, bounded controls over all four original witnesses and one independent mathematical/source-history review pass. this issue remains open until the fresh complete fixture chain and remaining independent acceptance checks enforce the new recipe; no real fit has begun.
