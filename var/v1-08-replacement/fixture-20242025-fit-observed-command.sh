cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution
  for fit_path in "$fit_run_root/20242025" "$fit_run_root/20242025.log" "$fit_run_root/20242025-start.txt" "$fit_run_root/20242025-finish.txt" "$fit_run_root/20242025-exit.txt" "$fit_run_root/20242025-shell.pid" "$fit_run_root/20242025-launch-head.txt" "$fit_run_root/20242025-launch-analysis-tree.txt" "$fit_run_root/20242025-launch-analysis-status.txt" "$fit_run_root/20242025-launch-observer-sha256.txt" "$fit_run_root/20242025-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20242025-source-check.json "$fit_run_root/20242025-launch-previous-sha256.txt"; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20242025-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20242025-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20242025-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20242025-launch-analysis-tree.txt" &&
  [ "$(cat "$fit_run_root/20242025-launch-analysis-tree.txt")" = c2412ac713b8c60e808dd71771f0812224b94439 ] &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20242025-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20242025-launch-analysis-status.txt" ] &&
  shasum -a 256 var/v1-08-replacement/consumed_start_check.py > "$fit_run_root/20242025-launch-observer-sha256.txt" &&
  [ "$(cat "$fit_run_root/20242025-launch-observer-sha256.txt")" = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf  var/v1-08-replacement/consumed_start_check.py' ] &&
  printf '%s\n' 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$fit_run_root/20242025-expected-recipe-sha256.txt" &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20232024/manifest.json > "$fit_run_root/20242025-launch-previous-sha256.txt" &&
  [ "$(cat "$fit_run_root/20242025-launch-previous-sha256.txt")" = '85438d8488de33d2c31a7a2a200ca0efdf6c9011d0edc9ffb34018445fd8894b  /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20232024/manifest.json' ] &&
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20242025-source-check.json -- fit --family execution --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20242025 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20232024 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20242025 > "$fit_run_root/20242025.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20242025-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20242025-finish.txt"
  exit "$fit_run_status"
)
