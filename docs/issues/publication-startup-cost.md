# publication startup cost

problem: full semantic publication validation runs before the server binds. v1-12 measured 3,361 seconds for strict startup on its 32,039,075,840-byte candidate. staging a copy first does not remove this second scan at final restart.

impact: restarting or activating the complete product can interrupt localhost for roughly an hour. the existing validation is meaningful; skipping it without binding the accepted artifact would weaken correctness.

evidence: [v1-12 acceptance](../research/value-v1-12/verification.md#real-candidate-and-live-acceptance), [candidate receipt](../research/value-v1-12/receipts/real-candidate.json), and `publicationLayer` in `app/src/server/publication.ts` calling full physical, analysis and observed validation before the listener starts. no new startup was run for this record.

owner: [v1-20 admission/startup](../specs/v1-20-whole-card-closure.md#admission-and-startup-contract). the user selected this redesign on 2026-11-20: retain full explicit validation, bind its result to database and compiled-validator identities, then hash/read only required indexes at ordinary startup. acceptance, stage and activation remain separate commands. no receipt fallback, hot switching or authenticated trust service.

resolved when: unchanged invalid-publication cases still fail admission; invalid/mismatched receipts or bytes fail before listening; admitted and full-check readers agree; real startup demonstrably avoids semantic census and improves measured time. retain hash/initialization/downtime measurements, same-code rollback proof and cross-schema rollback's remaining cost. specification approval alone does not resolve this issue.
