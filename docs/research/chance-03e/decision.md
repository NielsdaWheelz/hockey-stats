# chance-2 scientific decision

status: **in progress; no scientific verdict or admission decision.** the user authorized 03e implementation and real fitting on 2026-09-30. [software verification](verification.md) is complete; the bounded study continues under the unchanged [specification](../../specs/03e-training-assessment.md) and [protocol](protocol.md).

the first complete development anchor fit exited successfully under clean `e20adb20e784e811c7031294ddd2b96c7f9f4c19`. both starts converged after 1,853/1,751 accepted updates; strict native objective comparison selected `uniform`. `review-notes/development-anchor-complete-fit.json` and `review-notes/adversarial-verification.md` under the [run root](protocol.md#evidence-and-execution) retain the independent verification. inner native solves stopped on `ftol`; this does not establish unreported `gtol` attainment.

the complete fit took 40,332.64 seconds with peak rss 2,125,856,768 bytes. held-out native evaluation completed under clean `5bb2897` for 712 games, 68,775 eligible attempts and 49,014 unblocked attempts; [verification](verification.md#first-complete-development-fit) records its resources and linked artifacts. the saved numerical candidate has no scientific eligibility or primary-selection decision.

weaker completed native fit artifacts under clean `5bb2897`; both starts converged after 1,431/1,556 updates and strict objective comparison selected `unblocked_multinomial`. its original fit-process exit status was not observed after the terminal session was lost; completed model-last artifacts, completion log/resource footer and absent matching process establish native completion. its common-revision held-out evaluation completed with observed exit 0. [verification](verification.md#remaining-development-recipes) links these facts and resources.

stronger's uniform start exhausted the unchanged 2,000-update ceiling without meeting posterior tolerance; its second start remains live. this is a start-level nonconvergence, not a whole-recipe failure or probability rejection. stronger's whole-fit disposition, scientific comparisons, recipe/benchmark selection, protocol freeze and dependent transfer/final stages remain outstanding.

this page records current status until the actual report can state `conditional_research_handoff` or `withheld`, with attributable evidence and family dispositions. no handoff is issued. 03b's rejection remains unchanged; 04 and publication are not authorized, and physical-origin accuracy remains unestablished.
