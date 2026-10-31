cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution
  for fit_path in "$fit_run_root/20212022" "$fit_run_root/20212022.log" "$fit_run_root/20212022-start.txt" "$fit_run_root/20212022-finish.txt" "$fit_run_root/20212022-exit.txt" "$fit_run_root/20212022-shell.pid" "$fit_run_root/20212022-launch-head.txt" "$fit_run_root/20212022-launch-analysis-tree.txt" "$fit_run_root/20212022-launch-analysis-status.txt" "$fit_run_root/20212022-launch-observer-sha256.txt" "$fit_run_root/20212022-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/fit-20212022-source-check.json "$fit_run_root/20212022-launch-prepared-sha256.txt" "$fit_run_root/20212022-launch-coaches-sha256.txt" "$fit_run_root/20212022-launch-known-census-sha256.txt"; do
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
  shasum -a 256 var/v1-08-replacement/consumed_start_check.py > "$fit_run_root/20212022-launch-observer-sha256.txt" &&
  [ "$(cat "$fit_run_root/20212022-launch-observer-sha256.txt")" = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf  var/v1-08-replacement/consumed_start_check.py' ] &&
  printf '%s\n' 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$fit_run_root/20212022-expected-recipe-sha256.txt" &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json > "$fit_run_root/20212022-launch-prepared-sha256.txt" &&
  [ "$(cat "$fit_run_root/20212022-launch-prepared-sha256.txt")" = '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c  /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json' ] &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json > "$fit_run_root/20212022-launch-coaches-sha256.txt" &&
  [ "$(cat "$fit_run_root/20212022-launch-coaches-sha256.txt")" = '102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0  /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json' ] &&
  shasum -a 256 /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/20212022-non-prior-starts.json > "$fit_run_root/20212022-launch-known-census-sha256.txt" &&
  [ "$(cat "$fit_run_root/20212022-launch-known-census-sha256.txt")" = '6fd06ffbd3143379849fd82b4598c85d4f178b14c3c9eed4b28e003f30207a96  /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/20212022-non-prior-starts.json' ] &&
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/fit-20212022-source-check.json --known-census /Volumes/Expansion/hockey-stats/runs/spatial-v1-08-20261031-01/real/20212022-non-prior-starts.json -- fit --family execution --prepared /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02 --coaches /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json --season 20212022 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20212022 > "$fit_run_root/20212022.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20212022-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20212022-finish.txt"
  exit "$fit_run_status"
)
