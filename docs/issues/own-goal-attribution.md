# credited scorer versus physical shooting event

status: open; [03c](../specs/03c-source-revision.md) owns modifier admission; [03d](../specs/03d-chance-revision.md) owns physical-attempt and actor semantics. admitting the modifier alone does not resolve this issue.

problem: `chance_data.prepare` uses a goal's credited scorer as `shooter_id`. an own goal can separate statistical credit from the physical actor/location that a shot-quality model purports to describe. pl own-goal wording is preserved but unstructured.

evidence: [03b's decision](../research/chance-03b/decision.md) records own-goal wording at game `2025020282`, source index `282`, and game `2025020307`, index `14`; game `2025020184`, index `158`, lacks that descriptor despite missing type. reproduce by comparing those attributed api/report cases with scorer selection in [preparation](../../analysis/src/hockey_stats/chance_data.py). these are selected examples; missing type alone does not identify an own goal.

impact: adding shot type or assuming every goal coordinate is the credited player's release could misstate the measurement. existing records do not establish the physical shooter automatically.

live source follow-up: [landing goal modifiers](../research/source-audit.md#additional-source-evidence-without-the-drive) label the first two cited cases `own-goal` and the third `awarded`. the latter still has coordinates and apparent 5v5 membership in play-by-play/report evidence. preserve this additional observation; neither ordinary report wording nor an awarded modifier settles the physical attempt by itself. `none` also occurs on a fixture shootout winner, so the modifier cannot replace period/penalty-shot classification.

resolution: admit and reconcile landing modifier evidence, retain attributable cases and distinguish recorded credit from physical-action evidence; specify treatment in the revised model's population, actor and coordinate contracts, including any linkage to preceding attempts without double counting. quantify affected/unknown cases and test the chosen behavior. no automatic exclusion, inferred defender identity or relabeling of recorded coordinates without support. original captures/full-population inspection require the drive.
