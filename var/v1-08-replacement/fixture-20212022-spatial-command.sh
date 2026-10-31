cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20212022" "$fit_run_root/20212022.log" "$fit_run_root/20212022-start.txt" "$fit_run_root/20212022-finish.txt" "$fit_run_root/20212022-exit.txt" "$fit_run_root/20212022-shell.pid" "$fit_run_root/20212022-launch-head.txt" "$fit_run_root/20212022-launch-analysis-tree.txt" "$fit_run_root/20212022-launch-analysis-status.txt" "$fit_run_root/20212022-launch-valued-sha256.txt" "$fit_run_root/20212022-expected-design-recipe-sha256.txt"; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20212022-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20212022-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20212022-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20212022-launch-analysis-tree.txt" &&
  [ "$(cat "$fit_run_root/20212022-launch-analysis-tree.txt")" = c2412ac713b8c60e808dd71771f0812224b94439 ] &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20212022-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20212022-launch-analysis-status.txt" ] &&
  printf '%s\n' 04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b > "$fit_run_root/20212022-expected-design-recipe-sha256.txt" &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20212022/manifest.json > "$fit_run_root/20212022-launch-valued-sha256.txt" &&
  [ "$(cat "$fit_run_root/20212022-launch-valued-sha256.txt")" = '78e029e06cfb50ebdc247117faeb3849459e291be2267c250a9c15858dac7d60  /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20212022/manifest.json' ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20212022 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20212022 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022 > "$fit_run_root/20212022.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20212022-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20212022-finish.txt"
  exit "$fit_run_status"
)
