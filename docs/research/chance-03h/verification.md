# 03h software and saved-evidence verification

status: implementation and real assessment complete; independent statistical, systems and content reviews passed; all temporary test code deleted. decision: `withheld`. [specification](../../specs/03h-chance-revision.md) · [protocol](protocol.md) · [decision](decision.md)

implementation: `752b69dda7eb47dd39ea69e80186826e351d9c7c`, clean analysis tree; `analysis/research/chance_assessment.py` sha256 `ee7d7e24e047a55b8054663875b1c2745c68e9870afa6e611326bd2e5176489a`. no shared primitive, dependency, interpreter pin or historical script changed. the command owns saved-evidence validation/reconstruction/classification/output; native binary/bin arithmetic and pooled/calendar intervals keep their existing owners.

execution uses available python `3.14.8`, numpy `2.5.3` and scipy `1.18.1` under the unchanged lock, sha256 `bae38095f3dea6bdb860501eca311b1c33390c7a1e8b7aae76966572f118acdd`. the repository's `3.14.7` pin remains intact; the explicit override follows 03g's patch substitution. original 03g/parent execution identities remain separately recorded, rather than being relabeled as this assessment.

evidence root: `/Users/nnandal/Documents/code/hockey-stats-03h-runs`. immutable `inputs/protocol.md`, sha256 `75b152c2cd90180ae5d190cc227ac45226dbee94b11e3ccf7ef42d26d11c0bdf`, and `inputs/execution-freeze.json`, sha256 `b8ef3171f9fbbbe169374775f7c65cffeebe34674a20cda9b3bf8e2c2d749f84`, were saved before real interval arithmetic. the freeze binds the clean executing revision, reviewed source/dependency bytes, software/statistical reviews and exact four input identities. `inputs/specification.md` preserves executing-specification bytes, sha256 `b08016dc757d54bacc74634322d4d272b392e0da6ab660916b846c8b86b002c6`; later status updates do not alter its requirements. the real stream was not prehashed for this freeze.

## temporary red → green → refactor → green

the first complete saved-fixture command was red before production code existed: missing `chance_assessment.py`, exit `2`, retained in `verification/fixture-command-red.log`. the first expanded green passed the preserved fixture, seven synthetic command cases, 33 rejection cases and four independent numerical groups. adversarial refactoring added exact research pins, native probability validation, stronger coverage/excluded-goal reconciliation and canonical training dates; removed duplicated bin validation; retained compact per-game bin triples and corrected generic fixture wording. no scientific rule changed.

final held source passes 70 subprocess cases: one complete preserved 03g fixture command, ten explicitly synthetic valid commands and 59 malformed-evidence/output rejection cases. the commands and four independent numerical groups verify unequal-game pooled sums, empty/final calendar blocks, undefined draws, all bin boundaries and finite log-space zero/one endpoints, exact margin/5% boundaries, constant labels/low support, historical failure-before-support order, nonrequired failures and conflicting methods. both allowed dispositions are exercised, including no admission after no failure.

the subprocess guard forbids preparation, prediction, scoring, fitting/em and fitted-parent/raw reopening; every valid command's audit records exactly one stream open. rejection cases cover schema/purpose/identity/cross-link mismatch, coherent fixture relabeling, missing/duplicate/unordered keys, source/event/date/season/label/disposition errors, null/applicable probabilities, nonfinite/complement errors, full/game/bin/coverage disagreement and existing/inside-input outputs. invalid cases exit nonzero without completion; substantiated fixture withholding exits zero. native current classifications include `other`, not the initial synthetic fixture's invented `other_situation`; the fixture generator was corrected before final green. an earlier test protocol shared its output parent and correctly hit exclusivity; the test was moved into its own input directory.

`verification/software-verification.json`, sha256 `608376f268dff3089574fb70aa2ee2f137273dbf34adbe718a7bce2ee41d0b5a`, binds final source/tests/logs/receipts, unchanged saved fixture hashes and the locked environment. final integration took 41.97 seconds with 291,880,960 peak rss bytes; numerical checks took 0.66 seconds with 111,738,880 bytes. logs are `final-integration-green.log` and `final-numerical-green.log` under `verification/`. explicitly synthetic saved streams remain fixture evidence outside git; their parameters and labels are not raw observations or research evidence.

## real operation and independent review

from the isolated worktree, with external timing and output captured in `verification/research-command.log`:

```sh
UV_PYTHON=3.14.8 uv run --locked --project analysis python analysis/research/chance_assessment.py --completion /Users/nnandal/Documents/code/hockey-stats-03g-runs/diagnosis/completion.json --protocol /Users/nnandal/Documents/code/hockey-stats-03h-runs/inputs/protocol.md --out /Users/nnandal/Documents/code/hockey-stats-03h-runs/assessment
```

| measured operation | value |
|---|---:|
| full external wall time | 5.95 seconds |
| completion internal wall time | 5.159959 seconds |
| sole stream pass | 4.619840 seconds |
| peak resident memory | 312,164,352 bytes |
| saved stream bytes read/hashed in that pass | 567,119,704 bytes |
| unique logical input artifact bytes, including protocol | 620,548,427 bytes |
| assessment bytes before completion | 21,891,385 bytes |
| inclusive two-file output | 21,893,479 bytes |

the successful command exits `0` with `withheld`. it reconciles all 712 games and 85,317 recognized rows, including 272 unavailable rows and their null predictions. full binary/game sums, twenty own bins for all three quantities, dispositions, reasons, goal counts and excluded-goal reasons match saved revised summaries at native `1e-10` relative/absolute tolerance. complete original source coverage is preserved; source/report metadata and genuinely timed 5v5 counts absent from the saved row contract remain bound historical evidence, not newly reconstructed observations.

all 42,720 game-bin records remain, including 28,942 zero contributions. per-game bins carry ordered count/observed-positive/predicted-sum triples; global records own native bounds and rates. all 63 criteria and 189 method records survive. calendar intervals include the empty seven-day block and final partial blocks. the two required blockers are conversion bin 3 under games/seven days and all-attempt bin 2 under every method. the nonrequired marginal bin 8 fourteen-day failure remains descriptive.

`review-notes/statistical-refactor-review.json` clears final source and historical-rule fidelity. `review-notes/independent-statistical-output-review.json` checks every criterion/classification/verdict and independently recomputes 24 intervals across eight prospectively selected representative criteria from saved per-game sums; maximum difference is `1.39e-17`. no original stream, fitted parent or raw capture is reread for review. `review-notes/systems-output-review.json` verifies strict finite schema-1 artifacts, actual output hashes/cross-links, executing/original provenance, freeze/source/dependency preservation, complete populations, records and byte accounting. the output directory contains only `assessment.json` and completion-last `completion.json`.

final artifact sha256: `assessment.json` is `9f226f0934244a22ff3fb8212bac271c3bfb589d63516c5664a31c79d085b889`; `completion.json` is `d1ec15ffb51748049efc79d847f0a454cfae5a8a90072880d276487e9d8dca2f`.

## review and deletion closure

independent statistical content clearance is recorded in `review-notes/statistical-content-clearance.json` and its final `statistical-content-delta-clearance.json`. the independent claude-code review, coordinated through `skid`, is retained in `verification/review-systems-initial.md` and `review-content-final.md`. all correctness findings are resolved. content review tightened attribution to retained origin/avoidance mass, disclosed prior inspection of both failed point residuals, counted all 19 required criteria, and limited the proposed diagnostic's interpretation. no source or numerical result changed after the frozen real execution.

after those reviews, all five temporary test sources (53,904 bytes) and both cached bytecode files were deleted with the entire worktree `.tmp-03h/` directory. no test code remains in the external evidence root; fixture data, logs and receipts remain. no test-only dependency was added. `verification/test-deletion.json`, sha256 `e039b15391e1f01f7aedefd4c732e05cad9c075579354bcb41591faf8f9b4a02`, records deletion and unchanged identities for all nine frozen source/dependency files. the immutable preexecution software receipt's pending-deletion statement remains historical; this separate receipt closes it. project status pages now record completed 03h and the withheld disposition; 03i, 04 and publication require separate authorization.

material tradeoffs: this necessary-condition screen can settle withholding but cannot establish admission; broader obligations stay separately selected. preserving complete coverage adds a historical source/issue ledger to the output, while compact per-game bins avoid repeating derivable descriptors. the command accepts the native saved key order and checks monotonic keys with constant-size state; it adds no reorder/legacy path. one cheap command can be rerun after interruption, so no checkpoint, runner or raw-corpus audit is introduced. 03b/03e verdicts, expensive fits, original saved streams and existing 03g figures remain preserved.
