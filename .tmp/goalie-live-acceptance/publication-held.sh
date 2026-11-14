#!/bin/zsh
# held source only; run once only after the separate accepted preflight/assignment.
(
set -C
cd /Users/nnandal/Documents/code/hockey-stats-v1-07 || exit 1
/usr/bin/time -l env \
  -u OPENBLAS_NUM_THREADS -u OMP_NUM_THREADS -u MKL_NUM_THREADS \
  -u VECLIB_MAXIMUM_THREADS -u NUMEXPR_NUM_THREADS -u BLIS_NUM_THREADS \
  PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-07/analysis/src \
  /Users/nnandal/Documents/code/hockey-stats-v1-07/analysis/.venv/bin/python -B \
  -m hockey_stats.analysis_cli publish \
  --observed /Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/observed-selection.json \
  --results /Volumes/Expansion/hockey-stats/runs/spatial-st-v1-09-20261112-03/real/results \
  --out /Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/candidate-final-g-st-01 \
  > /Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/logs/publication-final-g-st-01.log 2>&1
goalie_publication_exit=$?
printf '%s\n' "$goalie_publication_exit" > /Volumes/Expansion/hockey-stats/runs/goalies-v1-07-20261108-01/real/logs/publication-final-g-st-01.exit || exit 1
printf 'G_ST_PUBLICATION_EXIT=%s\n' "$goalie_publication_exit"
exit "$goalie_publication_exit"
)
