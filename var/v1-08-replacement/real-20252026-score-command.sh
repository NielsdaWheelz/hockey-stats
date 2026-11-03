#!/bin/zsh
# final score from the accepted assembled family; supersedes the old held final-year command.
# root releases this command separately. keep HEAD, analysis and helpers fixed until exit.
set -eu
score_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
score_head=$(git rev-parse HEAD)
score_tree=fc716257eb118d1a091472cde4b214e8bca1f753
score_observer_sha=ef4995e579855950cab475cc2ac237f6ce22538429cc1f04d675b48838a6fca4
score_checker_sha=53fa5baf871a8e133ef446d8d41e4602bc371388cd607be3bd746ff2b1970d0f
score_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real
score_output=$score_root/scores/20252026
score_state=$score_root/u-repair-01/assembled-01/20252026
score_state_sha=59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276
for score_path in "$score_output" "$score_root/score-20252026.log" "$score_root/score-20252026.exit" "$score_root/score-20252026-source-check.json" "$score_root/score-20252026-start.txt" "$score_root/score-20252026-finish.txt" "$score_root/score-20252026-shell.pid" "$score_root/score-20252026-launch-head.txt" "$score_root/score-20252026-launch-analysis-tree.txt" "$score_root/score-20252026-launch-analysis-status.txt" "$score_root/score-20252026-launch-observer-sha256.txt" "$score_root/score-20252026-launch-checker-sha256.txt" "$score_root/score-20252026-launch-command-sha256.txt" "$score_root/score-20252026-launch-prepared-sha256.txt" "$score_root/score-20252026-launch-coaches-sha256.txt" "$score_root/score-20252026-launch-state-sha256.txt" "$score_root/score-20252026-launch-fit-source-sha256.txt" "$score_root/score-20252026-launch-original-sha256.txt" "$score_root/score-20252026-launch-acceptance-sha256.txt" "$score_root/score-20252026-expected-recipe-sha256.txt"; do
  if [ -e "$score_path" ]; then
    print -u2 "occupied path: $score_path; command not launched"
    exit 1
  fi
done
[ "$(git rev-parse HEAD:analysis)" = "$score_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
score_pin() {
  if [ "$(shasum -a256 "$1" | cut -d' ' -f1)" != "$2" ]; then
    print -u2 "pin mismatch: $1; command not launched"
    exit 1
  fi
}
score_pin var/v1-08-replacement/consumed_start_check.py "$score_observer_sha"
score_pin var/v1-08-replacement/accept_real_score_20252026.py "$score_checker_sha"
score_pin "$score_state/manifest.json" "$score_state_sha"
score_pin /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
score_pin /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json 102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0
score_pin "$score_root/fit-20252026-final-02-source-check.json" 59f4b00827ea736f0a374ba6f32a1ce7003f5f9ab7a131b84d5e4971f0624e9d
score_pin /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-04/scores/20252026/manifest.json 580f85fb2844fabf1d05d26e707438600e9e504fe005410406dd790c2e2ba56c
score_pin docs/research/spatial-v1-08/reviews/u-assembled-family-saved-review.md 23b8fe830ae17c72bcf9360ce6e98d5601f0c2ca9e0f8dbd1f77c47dee0d697a
[ "$(git rev-parse HEAD)" = "$score_head" ]
set -C
print -r -- $$ > "$score_root/score-20252026-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$score_root/score-20252026-start.txt"
print -r -- "$score_head" > "$score_root/score-20252026-launch-head.txt"
git rev-parse HEAD:analysis > "$score_root/score-20252026-launch-analysis-tree.txt"
git status --porcelain --untracked-files=all -- analysis > "$score_root/score-20252026-launch-analysis-status.txt"
shasum -a256 var/v1-08-replacement/consumed_start_check.py > "$score_root/score-20252026-launch-observer-sha256.txt"
shasum -a256 var/v1-08-replacement/accept_real_score_20252026.py > "$score_root/score-20252026-launch-checker-sha256.txt"
shasum -a256 "$score_command_path" > "$score_root/score-20252026-launch-command-sha256.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json > "$score_root/score-20252026-launch-prepared-sha256.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json > "$score_root/score-20252026-launch-coaches-sha256.txt"
shasum -a256 "$score_state/manifest.json" > "$score_root/score-20252026-launch-state-sha256.txt"
shasum -a256 "$score_root/fit-20252026-final-02-source-check.json" > "$score_root/score-20252026-launch-fit-source-sha256.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-04/scores/20252026/manifest.json > "$score_root/score-20252026-launch-original-sha256.txt"
shasum -a256 docs/research/spatial-v1-08/reviews/u-assembled-family-saved-review.md > "$score_root/score-20252026-launch-acceptance-sha256.txt"
print -r -- 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$score_root/score-20252026-expected-recipe-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python var/v1-08-replacement/consumed_start_check.py --out-check "$score_root/score-20252026-source-check.json" -- score --family execution --prepared /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02 --coaches /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json --state "$score_state" --out "$score_output" > "$score_root/score-20252026.log" 2>&1
score_status=$?
set -e
print -r -- "$score_status" > "$score_root/score-20252026.exit"
date -u +%Y-%m-%dT%H:%M:%SZ > "$score_root/score-20252026-finish.txt"
exit "$score_status"
