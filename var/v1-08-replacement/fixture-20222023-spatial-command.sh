cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20222023" "$fit_run_root/20222023.log" "$fit_run_root/20222023-start.txt" "$fit_run_root/20222023-finish.txt" "$fit_run_root/20222023-exit.txt" "$fit_run_root/20222023-shell.pid" "$fit_run_root/20222023-launch-head.txt" "$fit_run_root/20222023-launch-analysis-tree.txt" "$fit_run_root/20222023-launch-analysis-status.txt" "$fit_run_root/20222023-launch-valued-sha256.txt" "$fit_run_root/20222023-launch-previous-sha256.txt" "$fit_run_root/20222023-expected-design-recipe-sha256.txt"; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20222023-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20222023-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20222023-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20222023-launch-analysis-tree.txt" &&
  [ "$(cat "$fit_run_root/20222023-launch-analysis-tree.txt")" = c2412ac713b8c60e808dd71771f0812224b94439 ] &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20222023-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20222023-launch-analysis-status.txt" ] &&
  printf '%s\n' 04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b > "$fit_run_root/20222023-expected-design-recipe-sha256.txt" &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022/manifest.json > "$fit_run_root/20222023-launch-previous-sha256.txt" &&
  [ "$(cat "$fit_run_root/20222023-launch-previous-sha256.txt")" = '91ccca92782e4c156cb6ebe55952b6ded7c20d865ce4efcc323267b674d11465  /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022/manifest.json' ] &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20222023/manifest.json > "$fit_run_root/20222023-launch-valued-sha256.txt" &&
  [ "$(cat "$fit_run_root/20222023-launch-valued-sha256.txt")" = '69bf4a4dede3a7ca3f0c0cca9897caaadd2330d40a2a2acbd5c902cf6484bdad  /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20222023/manifest.json' ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20222023 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20222023 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20222023 > "$fit_run_root/20222023.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20222023-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20222023-finish.txt"
  exit "$fit_run_status"
)
