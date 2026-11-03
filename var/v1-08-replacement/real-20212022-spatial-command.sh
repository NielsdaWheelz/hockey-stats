#!/bin/zsh
# first replacement real spatial annual only; root releases this standalone command.
# preserve the original spatial objective/controls. no predecessor or final probes in 20212022.
# run serially after the final execution score exits; measure this complete annual before successors.
set -eu
spatial_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
spatial_head=$(git rev-parse HEAD)
spatial_tree=fc716257eb118d1a091472cde4b214e8bca1f753
spatial_recipe=04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b
spatial_prepared=/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02
spatial_coaches=/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json
spatial_campaign=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01
spatial_valued=$spatial_campaign/real/scores/20212022
spatial_root=$spatial_campaign/real/spatial/20212022
for spatial_path in "$spatial_root" "$spatial_root.log" "$spatial_root-start.txt" "$spatial_root-finish.txt" "$spatial_root-exit.txt" "$spatial_root-shell.pid" "$spatial_root-launch-head.txt" "$spatial_root-launch-analysis-tree.txt" "$spatial_root-launch-analysis-status.txt" "$spatial_root-launch-command-sha256.txt" "$spatial_root-launch-inputs-sha256.txt" "$spatial_root-launch-acceptance-sha256.txt" "$spatial_root-launch-spatial-recipe.txt"; do
  if [ -e "$spatial_path" ]; then
    print -u2 "occupied path: $spatial_path; command not launched"
    exit 1
  fi
done
[ "$(git rev-parse HEAD:analysis)" = "$spatial_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
spatial_pin() {
  if [ "$(shasum -a256 "$1" | cut -d' ' -f1)" != "$2" ]; then
    print -u2 "pin mismatch: $1; command not launched"
    exit 1
  fi
}
spatial_pin "$spatial_prepared/manifest.json" 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
spatial_pin "$spatial_coaches" 102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0
spatial_pin "$spatial_valued/manifest.json" 37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d
spatial_pin "$spatial_campaign/real/execution/20212022/manifest.json" 7c740083469c9a16edf6d73552ea18b89425a52b2ea7f4deeea41f79a5043e61
spatial_pin docs/research/spatial-v1-08/receipts/replacement-real-score-20212022-completion.json 7dbd5500d0565f622d53eeed4aac0859e6e69e03348e1af6fff08d4161105294
spatial_pin docs/research/spatial-v1-08/fixture-source-to-screen-final.md b4f09fc85231c42c96d4e7417091b9ff01c27046aa297bce09599b0a69d1e1f1
[ "$(git rev-parse HEAD)" = "$spatial_head" ]
mkdir -p "$spatial_campaign/real/spatial"
set -C
print -r -- $$ > "$spatial_root-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$spatial_root-start.txt"
print -r -- "$spatial_head" > "$spatial_root-launch-head.txt"
git rev-parse HEAD:analysis > "$spatial_root-launch-analysis-tree.txt"
git status --porcelain --untracked-files=all -- analysis > "$spatial_root-launch-analysis-status.txt"
shasum -a256 "$spatial_command_path" > "$spatial_root-launch-command-sha256.txt"
print -r -- "$spatial_recipe" > "$spatial_root-launch-spatial-recipe.txt"
shasum -a256 "$spatial_prepared/manifest.json" "$spatial_coaches" "$spatial_valued/manifest.json" "$spatial_campaign/real/execution/20212022/manifest.json" > "$spatial_root-launch-inputs-sha256.txt"
shasum -a256 docs/research/spatial-v1-08/receipts/replacement-real-score-20212022-completion.json docs/research/spatial-v1-08/fixture-source-to-screen-final.md > "$spatial_root-launch-acceptance-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python -m hockey_stats.analysis_cli fit --family spatial --prepared "$spatial_prepared" --coaches "$spatial_coaches" --valued "$spatial_valued" --season 20212022 --out "$spatial_root" > "$spatial_root.log" 2>&1
spatial_status=$?
set -e
print -r -- "$spatial_status" > "$spatial_root-exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$spatial_root-finish.txt"
exit "$spatial_status"
