#!/bin/zsh
# one reviewed head-preserving completion; no fit/probe/retry and no writes to the original partial.
set -eu
spatial_tree=38ec706cb505ea3d9936518dd119869e7695200b
completion_adapter_sha=e821fa49ae46ebb678985ce8cc6d221f90f198065293ab1e20bd7c8723b4741c
case "$spatial_tree" in *[!0-9a-f]*) print -u2 'completion source review pending; command not launched'; exit 1 ;; esac
case "$completion_adapter_sha" in *[!0-9a-f]*) print -u2 'completion adapter review pending; command not launched'; exit 1 ;; esac
[ "${#spatial_tree}" -eq 40 ]
[ "${#completion_adapter_sha}" -eq 64 ]
completion_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
completion_head=$(git rev-parse HEAD)
completion_adapter=/Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/complete_real_spatial_20222023.py
spatial_campaign=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01
spatial_prepared=/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02
spatial_coaches=/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json
spatial_valued=$spatial_campaign/real/scores/20222023
spatial_previous=$spatial_campaign/real/spatial/20212022
spatial_root=$spatial_campaign/real/spatial/20222023-complete-01
spatial_run=$spatial_root
for spatial_path in "$spatial_root" "$spatial_run.log" "$spatial_run-start.txt" "$spatial_run-finish.txt" "$spatial_run-exit.txt" "$spatial_run-shell.pid" "$spatial_run-launch-head.txt" "$spatial_run-launch-analysis-tree.txt" "$spatial_run-launch-analysis-status.txt" "$spatial_run-launch-command-sha256.txt" "$spatial_run-launch-inputs-sha256.txt" "$spatial_run-launch-acceptance-sha256.txt" "$spatial_run-launch-spatial-recipe.txt" "$spatial_run-saved-metadata-acceptance.json" "$spatial_run-completion-preflight.json"; do
  if [ -e "$spatial_path" ]; then print -u2 "occupied path: $spatial_path; command not launched"; exit 1; fi
done
[ "$(git rev-parse HEAD:analysis)" = "$spatial_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
spatial_pin() {
  if [ "$(shasum -a256 "$1" | cut -d' ' -f1)" != "$2" ]; then print -u2 "pin mismatch: $1; command not launched"; exit 1; fi
}
spatial_pin "$completion_adapter" "$completion_adapter_sha"
spatial_pin "$spatial_prepared/manifest.json" 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
spatial_pin "$spatial_coaches" 102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0
spatial_pin "$spatial_valued/manifest.json" 296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20
spatial_pin "$spatial_campaign/real/execution/20222023/manifest.json" eb52909e32d051b205e9cd6ccdcb8227371202d469a52357cfb926c94cff599c
spatial_pin "$spatial_previous/manifest.json" 3b7b51339b5ebb00a340a3f593347adf3a72ee137ad24739abd582b8290a5509
spatial_pin docs/research/spatial-v1-08/receipts/real-second-spatial-interruption.json 0bc1f5cb3b09ed326b8176ad35b41d51d868ab1ac72ebef1bad52dd35692c684
spatial_pin docs/research/spatial-v1-08/receipts/real-second-spatial-reconnection-preflight.json e9515116b27d2f68cb5fdfc4f571bb21039c2879c7d0613f734a38691b106b53
spatial_pin docs/research/spatial-v1-08/receipts/real-first-spatial-completion.json 54ca302a29bff57fd1dba7cea8dd2cfd89e869a97eba00d2ad0a4a6af5809ed7
[ "$(git rev-parse HEAD)" = "$completion_head" ]
mkdir -p "$spatial_campaign/real/spatial"
set -C
print -r -- $$ > "$spatial_run-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$spatial_run-start.txt"
print -r -- "$completion_head" > "$spatial_run-launch-head.txt"
git rev-parse HEAD:analysis > "$spatial_run-launch-analysis-tree.txt"
git status --porcelain --untracked-files=all -- analysis > "$spatial_run-launch-analysis-status.txt"
shasum -a256 "$completion_command_path" > "$spatial_run-launch-command-sha256.txt"
print -r -- 04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b > "$spatial_run-launch-spatial-recipe.txt"
shasum -a256 "$spatial_prepared/manifest.json" "$spatial_coaches" "$spatial_valued/manifest.json" "$spatial_campaign/real/execution/20222023/manifest.json" "$spatial_previous/manifest.json" > "$spatial_run-launch-inputs-sha256.txt"
shasum -a256 docs/research/spatial-v1-08/receipts/real-second-spatial-interruption.json docs/research/spatial-v1-08/receipts/real-second-spatial-reconnection-preflight.json docs/research/spatial-v1-08/receipts/real-first-spatial-completion.json > "$spatial_run-launch-acceptance-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python "$completion_adapter" --expected-head "$completion_head" --expected-analysis-tree "$spatial_tree" --expected-reconnection-sha256 e9515116b27d2f68cb5fdfc4f571bb21039c2879c7d0613f734a38691b106b53 > "$spatial_run.log" 2>&1
completion_status=$?
set -e
print -r -- "$completion_status" > "$spatial_run-exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$spatial_run-finish.txt"
exit "$completion_status"
