#!/bin/zsh
# third real spatial annual draft with accepted fresh completion predecessor; held until year two is accepted and root releases it.
# retain the same recipe/native controls; this year has a spatial predecessor and no probes.
set -eu
spatial_previous_sha=bdc5c2d4ed8645f5b1aa825abe06397b333ed399c2a4399eff6106dd6b98bd17
case "$spatial_previous_sha" in *[!0-9a-f]*) print -u2 'accepted year-two spatial pin withheld; command not launched'; exit 1 ;; esac
[ "${#spatial_previous_sha}" -eq 64 ] || exit 1
spatial_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
spatial_head=$(git rev-parse HEAD)
spatial_tree=38ec706cb505ea3d9936518dd119869e7695200b
spatial_recipe=04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b
spatial_prepared=/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02
spatial_coaches=/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json
spatial_campaign=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01
spatial_valued=$spatial_campaign/real/scores/20232024
spatial_root=$spatial_campaign/real/spatial/20232024
spatial_run=$spatial_root
spatial_previous=$spatial_campaign/real/spatial/20222023-complete-01
for spatial_path in "$spatial_root" "$spatial_run.log" "$spatial_run-start.txt" "$spatial_run-finish.txt" "$spatial_run-exit.txt" "$spatial_run-shell.pid" "$spatial_run-launch-head.txt" "$spatial_run-launch-analysis-tree.txt" "$spatial_run-launch-analysis-status.txt" "$spatial_run-launch-command-sha256.txt" "$spatial_run-launch-inputs-sha256.txt" "$spatial_run-launch-acceptance-sha256.txt" "$spatial_run-launch-spatial-recipe.txt" "$spatial_run-saved-metadata-acceptance.json"; do
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
spatial_pin "$spatial_previous/manifest.json" "$spatial_previous_sha"
spatial_pin "$spatial_prepared/manifest.json" 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
spatial_pin "$spatial_coaches" 102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0
spatial_pin "$spatial_valued/manifest.json" f13a1136c3df857a83d9f37aa10b919b64934e240515c3a8d5e2c556a778b238
spatial_pin "$spatial_campaign/real/execution/20232024/manifest.json" dd8b638dd8eb3e8af25722f53f633202b5fa28ef3ce81ec45bb9a180d9f09bfa
spatial_pin docs/research/spatial-v1-08/receipts/replacement-real-score-20232024-completion.json 86fef0c0fb2ab08940a95a004c8ebf507d37387ca50a78f234fadc8b6e16c2c6
spatial_pin docs/research/spatial-v1-08/fixture-source-to-screen-final.md b4f09fc85231c42c96d4e7417091b9ff01c27046aa297bce09599b0a69d1e1f1
[ "$(git rev-parse HEAD)" = "$spatial_head" ]
mkdir -p "$spatial_campaign/real/spatial"
set -C
print -r -- $$ > "$spatial_run-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$spatial_run-start.txt"
print -r -- "$spatial_head" > "$spatial_run-launch-head.txt"
git rev-parse HEAD:analysis > "$spatial_run-launch-analysis-tree.txt"
git status --porcelain --untracked-files=all -- analysis > "$spatial_run-launch-analysis-status.txt"
shasum -a256 "$spatial_command_path" > "$spatial_run-launch-command-sha256.txt"
print -r -- "$spatial_recipe" > "$spatial_run-launch-spatial-recipe.txt"
shasum -a256 "$spatial_prepared/manifest.json" "$spatial_coaches" "$spatial_valued/manifest.json" "$spatial_campaign/real/execution/20232024/manifest.json" "$spatial_previous/manifest.json" > "$spatial_run-launch-inputs-sha256.txt"
shasum -a256 docs/research/spatial-v1-08/receipts/replacement-real-score-20232024-completion.json docs/research/spatial-v1-08/fixture-source-to-screen-final.md > "$spatial_run-launch-acceptance-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python -m hockey_stats.analysis_cli fit --family spatial --prepared "$spatial_prepared" --coaches "$spatial_coaches" --valued "$spatial_valued" --season 20232024 --previous "$spatial_previous" --out "$spatial_root" > "$spatial_run.log" 2>&1
spatial_status=$?
set -e
print -r -- "$spatial_status" > "$spatial_run-exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$spatial_run-finish.txt"
exit "$spatial_status"
