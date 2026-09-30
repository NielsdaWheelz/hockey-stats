# chance evaluation and scoring attribution

status: open; identified during pr03b specification. repair before using real-corpus assessments as scientific evidence.

problem: the merged chance command records executing code/python/numerical-library/lockfile identity only for `fit`. `evaluate` and `score` record the fitted model digest but omit the evaluator/scorer's executing implementation. a model's fitting revision cannot identify later changes to preparation, evaluation or scoring.

evidence: `analysis/src/hockey_stats/chance_cli.py` builds `common` without implementation identity and adds it only to fitting `metadata`. reproduce by inspecting the top-level fields in fixture model, assessment and score artifacts. no full retraining is needed to demonstrate the omission.

impact: saved assessment/scoring results cannot be fully attributed to the code that produced them. this does not imply that their computed values are wrong.

resolution: construct the existing implementation/dependency identity once for every subcommand and include it in each output artifact. retain the separate fitted-model digest. verify installed evaluation/scoring commands preserve the model bytes and report their own executing revision; use a temporary integration check, then delete it under the initial-slice policy. regenerate cheap assessment/scoring artifacts; no compatibility reader, registry or new provenance service. [owner: pr03b](../specs/03b-training-acceptance.md).
