cd /Users/nnandal/Documents/code/hockey-stats-v1-08 || exit 1
# held preparation; replace the pending state digest only after root accepts the annual.
score_state_sha256=eb52909e32d051b205e9cd6ccdcb8227371202d469a52357cfb926c94cff599c
if [ "${#score_state_sha256}" -ne 64 ]; then
  printf '%s\n' 'accepted 20222023 state digest pending; command not launched' >&2
  exit 1
fi
for score_path in /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/scores/20222023 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023.log /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023.exit /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-source-check.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-head.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-analysis-tree.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-analysis-status.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-observer-sha256.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-expected-recipe-sha256.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-start.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-finish.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-shell.pid /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-prepared-sha256.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-coaches-sha256.txt /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-state-sha256.txt; do
  if [ -e "$score_path" ]; then
    printf '%s\n' "occupied path: $score_path; command not launched" >&2
    exit 1
  fi
done
if [ ! -f /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20222023/manifest.json ]; then
  printf '%s\n' 'accepted state manifest not yet available; command not launched' >&2
  exit 1
fi
set -C
printf '%s\n' $$ > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-shell.pid &&
date -u +%Y-%m-%dT%H:%M:%SZ > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-start.txt &&
git rev-parse HEAD > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-head.txt &&
git rev-parse HEAD:analysis > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-analysis-tree.txt &&
[ "$(cat /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-analysis-tree.txt)" = c2412ac713b8c60e808dd71771f0812224b94439 ] &&
git status --porcelain --untracked-files=all -- analysis > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-analysis-status.txt &&
[ ! -s /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-analysis-status.txt ] &&
shasum -a 256 var/v1-08-replacement/consumed_start_check.py > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-observer-sha256.txt &&
[ "$(cat /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-observer-sha256.txt)" = '286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf  var/v1-08-replacement/consumed_start_check.py' ] &&
printf '%s\n' 47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674 > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-expected-recipe-sha256.txt &&
shasum -a 256 /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-prepared-sha256.txt &&
[ "$(cat /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-prepared-sha256.txt)" = '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c  /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json' ] &&
shasum -a 256 /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-coaches-sha256.txt &&
[ "$(cat /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-coaches-sha256.txt)" = '102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0  /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json' ] &&
shasum -a 256 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20222023/manifest.json > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-state-sha256.txt &&
[ "$(cat /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-launch-state-sha256.txt)" = "$score_state_sha256  /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20222023/manifest.json" ] &&
/usr/bin/time -l env PYTHONPATH=/Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/.venv/bin/python /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/consumed_start_check.py --out-check /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-source-check.json -- score --family execution --prepared /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02 --coaches /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json --state /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20222023 --out /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/scores/20222023 > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023.log 2>&1
replacement_status=$?
printf '%s\n' "$replacement_status" > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023.exit
date -u +%Y-%m-%dT%H:%M:%SZ > /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/score-20222023-finish.txt
exit "$replacement_status"
