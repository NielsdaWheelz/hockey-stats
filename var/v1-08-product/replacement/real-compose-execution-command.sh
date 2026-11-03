#!/bin/zsh
# held until the accepted-score receipt and actually written selection hash are pinned.
# root releases composition separately, after the current heavy job leaves the resource lane.
set -eu
expected_final_score_sha256=40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc
expected_selection_sha256=''
accepted_score_receipt=/Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/receipts/real-final-score-completion.json
accepted_score_receipt_sha256=8f9163b53c07c264ef59d651bf4860b04333b70a61ec4a19abc7bd4fecfa1953
case "$expected_final_score_sha256$expected_selection_sha256$accepted_score_receipt_sha256" in *[!0-9a-f]*) exit 1 ;; esac
[ "${#expected_final_score_sha256}" -eq 64 ] && [ "${#expected_selection_sha256}" -eq 64 ] && [ "${#accepted_score_receipt_sha256}" -eq 64 ] && [ -n "$accepted_score_receipt" ] || exit 1
compose_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
compose_head=$(git rev-parse HEAD)
compose_tree=fc716257eb118d1a091472cde4b214e8bca1f753
compose_checker_sha=bbf7c5f2cf751f8103103c3ab0337c4de0844b48ffaa57321fd871ebbfd23c60
compose_selector_sha=376cbefc521cb8c67318841166c29f8ddb35121bdc4ccb1c725dbcec1bc41ac4
compose_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real
compose_output=$compose_root/execution-results
for compose_path in "$compose_output" "$compose_root/compose-execution.log" "$compose_root/compose-execution.exit" "$compose_root/compose-execution-start.txt" "$compose_root/compose-execution-finish.txt" "$compose_root/compose-execution-shell.pid" "$compose_root/compose-execution-launch-head.txt" "$compose_root/compose-execution-launch-analysis-tree.txt" "$compose_root/compose-execution-launch-analysis-status.txt" "$compose_root/compose-execution-launch-observer-sha256.txt" "$compose_root/compose-execution-launch-checker-sha256.txt" "$compose_root/compose-execution-launch-selector-sha256.txt" "$compose_root/compose-execution-launch-command-sha256.txt" "$compose_root/compose-execution-launch-acceptance-sha256.txt" "$compose_root/compose-execution-expected-recipe-sha256.txt" "$compose_root/compose-execution-scores-selection-sha256.txt" "$compose_root/compose-execution-facts-manifest-sha256.txt" "$compose_root/compose-execution-prepared-manifest-sha256.txt" "$compose_root/compose-execution-observed-selection-sha256.txt"; do
  if [ -e "$compose_path" ]; then
    print -u2 "occupied path: $compose_path; command not launched"
    exit 1
  fi
done
[ "$(git rev-parse HEAD:analysis)" = "$compose_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
compose_pin() {
  if [ "$(shasum -a256 "$1" | cut -d' ' -f1)" != "$2" ]; then
    print -u2 "pin mismatch: $1; command not launched"
    exit 1
  fi
}
compose_pin "$compose_root/scores/20252026/manifest.json" "$expected_final_score_sha256"
compose_pin "$compose_root/scores-selection.json" "$expected_selection_sha256"
compose_pin "$accepted_score_receipt" "$accepted_score_receipt_sha256"
compose_pin var/v1-08-product/replacement/verify-real-execution-compose.py "$compose_checker_sha"
compose_pin var/v1-08-product/replacement/prepare-real-score-selection.py "$compose_selector_sha"
compose_pin var/v1-08-replacement/consumed_start_check.py ef4995e579855950cab475cc2ac237f6ce22538429cc1f04d675b48838a6fca4
compose_pin /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/facts-04/manifest.json 786b2899b72347e2cbbdb89d24d01e174abf8923fc07e07649fc2bcfdf1967eb
compose_pin /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
compose_pin /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/observed-selection.json 5b6e3f0b8ae736260070549677a59bbf648ebab9a916729333eeb577611331e9
[ "$(git rev-parse HEAD)" = "$compose_head" ]
set -C
print -r -- $$ > "$compose_root/compose-execution-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$compose_root/compose-execution-start.txt"
print -r -- "$compose_head" > "$compose_root/compose-execution-launch-head.txt"
git rev-parse HEAD:analysis > "$compose_root/compose-execution-launch-analysis-tree.txt"
git status --porcelain --untracked-files=all -- analysis > "$compose_root/compose-execution-launch-analysis-status.txt"
# the observer is recorded as upstream score provenance; summarize does not invoke it.
shasum -a256 var/v1-08-replacement/consumed_start_check.py > "$compose_root/compose-execution-launch-observer-sha256.txt"
shasum -a256 var/v1-08-product/replacement/verify-real-execution-compose.py > "$compose_root/compose-execution-launch-checker-sha256.txt"
shasum -a256 var/v1-08-product/replacement/prepare-real-score-selection.py > "$compose_root/compose-execution-launch-selector-sha256.txt"
shasum -a256 "$compose_command_path" > "$compose_root/compose-execution-launch-command-sha256.txt"
shasum -a256 "$accepted_score_receipt" > "$compose_root/compose-execution-launch-acceptance-sha256.txt"
print -r -- 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$compose_root/compose-execution-expected-recipe-sha256.txt"
shasum -a256 "$compose_root/scores-selection.json" > "$compose_root/compose-execution-scores-selection-sha256.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/facts-04/manifest.json > "$compose_root/compose-execution-facts-manifest-sha256.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json > "$compose_root/compose-execution-prepared-manifest-sha256.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/observed-selection.json > "$compose_root/compose-execution-observed-selection-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python -m hockey_stats.analysis_cli summarize --family execution --prepared /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02 --facts /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/facts-04 --scores "$compose_root/scores-selection.json" --out "$compose_output" > "$compose_root/compose-execution.log" 2>&1
compose_status=$?
set -e
print -r -- "$compose_status" > "$compose_root/compose-execution.exit"
date -u +%Y-%m-%dT%H:%M:%SZ > "$compose_root/compose-execution-finish.txt"
exit "$compose_status"
