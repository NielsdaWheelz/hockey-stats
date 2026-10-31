# fixture replacement fits

unexecuted one-command blocks. root releases one annual at a time after its prerequisites pass. these blocks do not launch each other.

## execution 20212022

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution
  for fit_path in "$fit_run_root/20212022" "$fit_run_root/20212022.log" "$fit_run_root/20212022-start.txt" "$fit_run_root/20212022-finish.txt" "$fit_run_root/20212022-exit.txt" "$fit_run_root/20212022-shell.pid" "$fit_run_root/20212022-launch-head.txt" "$fit_run_root/20212022-launch-analysis-tree.txt" "$fit_run_root/20212022-launch-analysis-status.txt" "$fit_run_root/20212022-launch-observer-sha256.txt" "$fit_run_root/20212022-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20212022-source-check.json; do
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
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20212022-source-check.json -- fit --family execution --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20212022 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20212022 > "$fit_run_root/20212022.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20212022-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20212022-finish.txt"
  exit "$fit_run_status"
)
```

## execution 20222023

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution
  for fit_path in "$fit_run_root/20222023" "$fit_run_root/20222023.log" "$fit_run_root/20222023-start.txt" "$fit_run_root/20222023-finish.txt" "$fit_run_root/20222023-exit.txt" "$fit_run_root/20222023-shell.pid" "$fit_run_root/20222023-launch-head.txt" "$fit_run_root/20222023-launch-analysis-tree.txt" "$fit_run_root/20222023-launch-analysis-status.txt" "$fit_run_root/20222023-launch-observer-sha256.txt" "$fit_run_root/20222023-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20222023-source-check.json; do
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
  shasum -a 256 var/v1-08-replacement/consumed_start_check.py > "$fit_run_root/20222023-launch-observer-sha256.txt" &&
  [ "$(cat "$fit_run_root/20222023-launch-observer-sha256.txt")" = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf  var/v1-08-replacement/consumed_start_check.py' ] &&
  printf '%s\n' 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$fit_run_root/20222023-expected-recipe-sha256.txt" &&
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20222023-source-check.json -- fit --family execution --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20222023 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20212022 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20222023 > "$fit_run_root/20222023.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20222023-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20222023-finish.txt"
  exit "$fit_run_status"
)
```

## execution 20232024

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution
  for fit_path in "$fit_run_root/20232024" "$fit_run_root/20232024.log" "$fit_run_root/20232024-start.txt" "$fit_run_root/20232024-finish.txt" "$fit_run_root/20232024-exit.txt" "$fit_run_root/20232024-shell.pid" "$fit_run_root/20232024-launch-head.txt" "$fit_run_root/20232024-launch-analysis-tree.txt" "$fit_run_root/20232024-launch-analysis-status.txt" "$fit_run_root/20232024-launch-observer-sha256.txt" "$fit_run_root/20232024-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20232024-source-check.json; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20232024-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20232024-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20232024-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20232024-launch-analysis-tree.txt" &&
  [ "$(cat "$fit_run_root/20232024-launch-analysis-tree.txt")" = c2412ac713b8c60e808dd71771f0812224b94439 ] &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20232024-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20232024-launch-analysis-status.txt" ] &&
  shasum -a 256 var/v1-08-replacement/consumed_start_check.py > "$fit_run_root/20232024-launch-observer-sha256.txt" &&
  [ "$(cat "$fit_run_root/20232024-launch-observer-sha256.txt")" = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf  var/v1-08-replacement/consumed_start_check.py' ] &&
  printf '%s\n' 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$fit_run_root/20232024-expected-recipe-sha256.txt" &&
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20232024-source-check.json -- fit --family execution --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20232024 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20222023 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20232024 > "$fit_run_root/20232024.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20232024-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20232024-finish.txt"
  exit "$fit_run_status"
)
```

## execution 20242025

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution
  for fit_path in "$fit_run_root/20242025" "$fit_run_root/20242025.log" "$fit_run_root/20242025-start.txt" "$fit_run_root/20242025-finish.txt" "$fit_run_root/20242025-exit.txt" "$fit_run_root/20242025-shell.pid" "$fit_run_root/20242025-launch-head.txt" "$fit_run_root/20242025-launch-analysis-tree.txt" "$fit_run_root/20242025-launch-analysis-status.txt" "$fit_run_root/20242025-launch-observer-sha256.txt" "$fit_run_root/20242025-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20242025-source-check.json; do
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
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20242025-source-check.json -- fit --family execution --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20242025 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20232024 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20242025 > "$fit_run_root/20242025.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20242025-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20242025-finish.txt"
  exit "$fit_run_status"
)
```

## execution 20252026

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution
  for fit_path in "$fit_run_root/20252026" "$fit_run_root/20252026.log" "$fit_run_root/20252026-start.txt" "$fit_run_root/20252026-finish.txt" "$fit_run_root/20252026-exit.txt" "$fit_run_root/20252026-shell.pid" "$fit_run_root/20252026-launch-head.txt" "$fit_run_root/20252026-launch-analysis-tree.txt" "$fit_run_root/20252026-launch-analysis-status.txt" "$fit_run_root/20252026-launch-observer-sha256.txt" "$fit_run_root/20252026-expected-recipe-sha256.txt" /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20252026-source-check.json; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20252026-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20252026-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20252026-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20252026-launch-analysis-tree.txt" &&
  [ "$(cat "$fit_run_root/20252026-launch-analysis-tree.txt")" = c2412ac713b8c60e808dd71771f0812224b94439 ] &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20252026-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20252026-launch-analysis-status.txt" ] &&
  shasum -a 256 var/v1-08-replacement/consumed_start_check.py > "$fit_run_root/20252026-launch-observer-sha256.txt" &&
  [ "$(cat "$fit_run_root/20252026-launch-observer-sha256.txt")" = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf  var/v1-08-replacement/consumed_start_check.py' ] &&
  printf '%s\n' 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > "$fit_run_root/20252026-expected-recipe-sha256.txt" &&
  /usr/bin/time -l env PYTHONPATH=analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/fit-20252026-source-check.json -- fit --family execution --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20252026 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20242025 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/execution/20252026 > "$fit_run_root/20252026.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20252026-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20252026-finish.txt"
  exit "$fit_run_status"
)
```

## spatial 20212022

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20212022" "$fit_run_root/20212022.log" "$fit_run_root/20212022-start.txt" "$fit_run_root/20212022-finish.txt" "$fit_run_root/20212022-exit.txt" "$fit_run_root/20212022-shell.pid" "$fit_run_root/20212022-launch-head.txt" "$fit_run_root/20212022-launch-analysis-tree.txt" "$fit_run_root/20212022-launch-analysis-status.txt"; do
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
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20212022-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20212022-launch-analysis-status.txt" ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20212022 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20212022 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022 > "$fit_run_root/20212022.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20212022-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20212022-finish.txt"
  exit "$fit_run_status"
)
```

## spatial 20222023

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20222023" "$fit_run_root/20222023.log" "$fit_run_root/20222023-start.txt" "$fit_run_root/20222023-finish.txt" "$fit_run_root/20222023-exit.txt" "$fit_run_root/20222023-shell.pid" "$fit_run_root/20222023-launch-head.txt" "$fit_run_root/20222023-launch-analysis-tree.txt" "$fit_run_root/20222023-launch-analysis-status.txt"; do
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
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20222023-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20222023-launch-analysis-status.txt" ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20222023 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20222023 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20222023 > "$fit_run_root/20222023.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20222023-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20222023-finish.txt"
  exit "$fit_run_status"
)
```

## spatial 20232024

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20232024" "$fit_run_root/20232024.log" "$fit_run_root/20232024-start.txt" "$fit_run_root/20232024-finish.txt" "$fit_run_root/20232024-exit.txt" "$fit_run_root/20232024-shell.pid" "$fit_run_root/20232024-launch-head.txt" "$fit_run_root/20232024-launch-analysis-tree.txt" "$fit_run_root/20232024-launch-analysis-status.txt"; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20232024-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20232024-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20232024-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20232024-launch-analysis-tree.txt" &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20232024-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20232024-launch-analysis-status.txt" ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20232024 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20222023 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20232024 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20232024 > "$fit_run_root/20232024.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20232024-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20232024-finish.txt"
  exit "$fit_run_status"
)
```

## spatial 20242025

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20242025" "$fit_run_root/20242025.log" "$fit_run_root/20242025-start.txt" "$fit_run_root/20242025-finish.txt" "$fit_run_root/20242025-exit.txt" "$fit_run_root/20242025-shell.pid" "$fit_run_root/20242025-launch-head.txt" "$fit_run_root/20242025-launch-analysis-tree.txt" "$fit_run_root/20242025-launch-analysis-status.txt"; do
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
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20242025-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20242025-launch-analysis-status.txt" ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20242025 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20232024 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20242025 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20242025 > "$fit_run_root/20242025.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20242025-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20242025-finish.txt"
  exit "$fit_run_status"
)
```

## spatial 20252026

```sh
cd /Users/nnandal/Documents/code/hockey-stats-v1-08 &&
(
  fit_run_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial
  for fit_path in "$fit_run_root/20252026" "$fit_run_root/20252026.log" "$fit_run_root/20252026-start.txt" "$fit_run_root/20252026-finish.txt" "$fit_run_root/20252026-exit.txt" "$fit_run_root/20252026-shell.pid" "$fit_run_root/20252026-launch-head.txt" "$fit_run_root/20252026-launch-analysis-tree.txt" "$fit_run_root/20252026-launch-analysis-status.txt"; do
    if [ -e "$fit_path" ]; then
      printf '%s\n' "occupied path: $fit_path; command not launched" >&2
      exit 1
    fi
  done
  mkdir -p "$fit_run_root" || exit 1
  set -C
  printf '%s\n' $$ > "$fit_run_root/20252026-shell.pid" &&
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20252026-start.txt" &&
  git rev-parse HEAD > "$fit_run_root/20252026-launch-head.txt" &&
  git rev-parse HEAD:analysis > "$fit_run_root/20252026-launch-analysis-tree.txt" &&
  git status --porcelain --untracked-files=all -- analysis > "$fit_run_root/20252026-launch-analysis-status.txt" &&
  [ ! -s "$fit_run_root/20252026-launch-analysis-status.txt" ] &&
  /usr/bin/time -l uv run --project analysis hockey-stats-analysis fit --family spatial --prepared /Users/nnandal/Documents/code/hockey-stats-v1-01/var/v1-01-root/root-r6 --coaches /Users/nnandal/Documents/code/hockey-stats-v1-05/var/v1-05-checks/coaches/coaches.json --season 20252026 --previous /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20242025 --valued /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/scores/20252026 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20252026 > "$fit_run_root/20252026.log" 2>&1
  fit_run_status=$?
  printf '%s\n' "$fit_run_status" > "$fit_run_root/20252026-exit.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$fit_run_root/20252026-finish.txt"
  exit "$fit_run_status"
)
```
