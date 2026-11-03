#!/bin/zsh
# proposed only: root supplies three reviewed source pins and the release receipt.
# actual launch head may advance for command/docs commits; the release records the reviewed source commit.
# keep analysis, capture, diagnosis and source-observer code unchanged from launch until exit.
set -eu
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
capture_commit=$(git rev-parse HEAD)
capture_tree=PENDING_REVIEWED_ANALYSIS_TREE
capture_sha=PENDING_REVIEWED_CAPTURE_SHA256
capture_diagnosis_sha=PENDING_REVIEWED_DIAGNOSIS_SHA256
case "$capture_tree:$capture_sha:$capture_diagnosis_sha" in
  *PENDING*) print -u2 'unreviewed capture pins; command not launched'; exit 1 ;;
esac
capture_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01
for capture_path in "$capture_root" "$capture_root.log" "$capture_root-start.txt" "$capture_root-finish.txt" "$capture_root-exit.txt" "$capture_root-shell.pid" "$capture_root-launch-head.txt" "$capture_root-launch-analysis-tree.txt" "$capture_root-launch-capture-sha256.txt" "$capture_root-launch-diagnosis-sha256.txt" "$capture_root-launch-analysis-status.txt" "$capture_root-launch-inputs-sha256.txt"; do
  if [ -e "$capture_path" ]; then
    print -u2 "occupied path: $capture_path; command not launched"
    exit 1
  fi
done
[ "$(git rev-parse HEAD)" = "$capture_commit" ]
[ "$(git rev-parse HEAD:analysis)" = "$capture_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
[ "$(shasum -a256 var/v1-08-replacement/capture_execution_u.py | cut -d' ' -f1)" = "$capture_sha" ]
[ "$(shasum -a256 var/v1-08-replacement/diagnose_execution_u.py | cut -d' ' -f1)" = "$capture_diagnosis_sha" ]
set -C
print -r -- $$ > "$capture_root-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$capture_root-start.txt"
git rev-parse HEAD > "$capture_root-launch-head.txt"
git rev-parse HEAD:analysis > "$capture_root-launch-analysis-tree.txt"
shasum -a256 var/v1-08-replacement/capture_execution_u.py > "$capture_root-launch-capture-sha256.txt"
shasum -a256 var/v1-08-replacement/diagnose_execution_u.py > "$capture_root-launch-diagnosis-sha256.txt"
git status --porcelain --untracked-files=all -- analysis > "$capture_root-launch-analysis-status.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20242025/manifest.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-final-02/20252026/manifest.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/fit-20252026-final-02-source-check.json > "$capture_root-launch-inputs-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python var/v1-08-replacement/capture_execution_u.py --expected-commit "$capture_commit" --expected-analysis-tree "$capture_tree" --expected-capture-sha256 "$capture_sha" --expected-diagnosis-sha256 "$capture_diagnosis_sha" > "$capture_root.log" 2>&1
capture_status=$?
set -e
print -r -- "$capture_status" > "$capture_root-exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$capture_root-finish.txt"
exit "$capture_status"
