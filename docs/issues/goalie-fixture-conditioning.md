# synthetic goalie conditioning

problem: the provided synthetic goalie `9000004`, `20232024`, `5v5` in [the foundation fixture](../../fixtures/publication-v1-13/results/20232024-goalie-goalie_result.jsonl) has reattempt probability `.2`, conditional successor danger `.2` and joint danger `.2`. its three differences are `.1`, implying neutral levels `.1,.1,.1`. under one saved-shot reference, the first two imply focal joint `.04` and neutral joint `.01`. no coherent prefix/continuation evidence can preserve all these synthetic values.

impact: the old fixture establishes its historical transport contract, not the newly explicit conditional algebra. v1-19's strict evidence extension cannot upgrade this row unchanged. real v1-07 projections are a separate accepted source; this finding does not establish a real-model defect.

evidence/reproduction: read the single provided row at the key above and compare `followup_danger.value` with `recorded_reattempt_probability.value * reattempt_neutral_goal_probability.value`; repeat on levels minus their corresponding differences. code/source inspection and independent systems review found the conflict on 2026-11-14. other fixture goalie rows are pending.

resolution: [v1-19](../specs/v1-19-goalie-card-discovery.md) and the shared exchange4/schema10 foundation create an attributed synthetic successor with independently checked masses, levels/differences, supports, maps and method evidence. add coherent ev/pk examples for the primary card paths. preserve the original fixture bytes/receipts; enumerate every corrected synthetic field in the conversion receipt. no real scalar/map may change and no fit/rescore is authorized. the issue closes when strict publication plus card/evidence checks demonstrate those identities and preservation.
