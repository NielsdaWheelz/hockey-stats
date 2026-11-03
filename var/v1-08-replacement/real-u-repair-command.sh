#!/bin/zsh
# fixed reviewed analysis/helpers and accepted saved diagnosis; root releases this command separately.
# record actual launch head: command/docs commits may advance while the analysis tree stays exact.
# keep analysis and helpers unchanged until the numerical process exits. this command never assembles.
set -eu
repair_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
repair_head=$(git rev-parse HEAD)
repair_tree=fc716257eb118d1a091472cde4b214e8bca1f753
repair_helper_sha=9ddb1425196328fff332f5ba1da91a231d77fce233fe48565e883b9e594d9c69
repair_trace_sha=89af29e14de76a3a8f332b3753c5640d9b6c825f493719163dd687b7b824bc13
repair_diagnostic_helper_sha=031f30d640c0d526e35d8d862803718c1f565ee99ca2ef5638b9e36df3f25ca1
repair_diagnosis_sha=115da4fe4c18912b74b1970f1825a4338f0f54c6ccd9f0cfb3f7e10dfa026af1
repair_capture=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01
repair_root=$repair_capture/repair-01
for repair_path in "$repair_root" "$repair_root.log" "$repair_root-start.txt" "$repair_root-finish.txt" "$repair_root-exit.txt" "$repair_root-shell.pid" "$repair_root-launch-head.txt" "$repair_root-launch-analysis-tree.txt" "$repair_root-launch-helper-sha256.txt" "$repair_root-launch-trace-sha256.txt" "$repair_root-launch-diagnostic-helper-sha256.txt" "$repair_root-launch-command-sha256.txt" "$repair_root-launch-analysis-status.txt" "$repair_root-launch-inputs-sha256.txt" "$repair_root-launch-acceptance-sha256.txt"; do
  if [ -e "$repair_path" ]; then
    print -u2 "occupied path: $repair_path; command not launched"
    exit 1
  fi
done
[ "$(git rev-parse HEAD:analysis)" = "$repair_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
repair_pin() {
  if [ "$(shasum -a256 "$1" | cut -d' ' -f1)" != "$2" ]; then
    print -u2 "pin mismatch: $1; command not launched"
    exit 1
  fi
}
repair_pin var/v1-08-replacement/repair_execution_u.py "$repair_helper_sha"
repair_pin analysis/src/hockey_stats/execution_trace.py "$repair_trace_sha"
repair_pin var/v1-08-replacement/diagnose_execution_u.py "$repair_diagnostic_helper_sha"
repair_pin "$repair_capture/inputs/manifest.json" 031975b95114fbe62c0e468ebdf16d6170c27f15407b7df71ff0b08e18517a6c
repair_pin "$repair_capture/diagnosis/diagnosis.json" "$repair_diagnosis_sha"
repair_pin "$repair_capture/source-check.json" 9f1351a2cf619e32a7ebeb487a4dda4b3892dcb005b7f2ded917a71354509aa7
repair_pin "$repair_capture/capture-reloaded.json" a10365297148c215f764bb2cde5178602a5eda13563fca36f6345bfd4f7fb9f6
repair_pin /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
repair_pin /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json 102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0
repair_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20242025/manifest.json 1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe
repair_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-final-02/20252026/manifest.json cb075d5e59aea61589411e4573db7192c45fddd8265a807c2c39c2084b504e22
repair_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/fit-20252026-final-02-source-check.json 59f4b00827ea736f0a374ba6f32a1ce7003f5f9ab7a131b84d5e4971f0624e9d
repair_pin docs/research/spatial-v1-08/reviews/u-diagnosis-saved-review.md 2e04c4a6331c2a36f176e0e307b0f520a5255d19cb23513935f13da9b80ecdbd
repair_pin docs/research/spatial-v1-08/receipts/u-capture-diagnosis-completion.json 6950fed6a7593168e9554515387debcc9e0d02b091d71995f57a00272da623d9
repair_pin docs/research/spatial-v1-08/execution-u-exact-sum-repair.md 6beb304528f63ecb335ddab57e9baa9eb31be5099471cb5033d5810e0515abb7
repair_pin var/v1-08-replacement/u-independent-saved-audit.py da9b2122f6c7a726338dbc7714c800d16f2d48be3e388f847fb3471c65645369
repair_pin var/v1-08-replacement/u-independent-saved-audit.log 0d186ace4a57d3235e6c6f9f69c8ea0077d91c098fe539eddcbb24d3ebae7593
[ "$(git rev-parse HEAD)" = "$repair_head" ]
set -C
print -r -- $$ > "$repair_root-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$repair_root-start.txt"
print -r -- "$repair_head" > "$repair_root-launch-head.txt"
git rev-parse HEAD:analysis > "$repair_root-launch-analysis-tree.txt"
shasum -a256 var/v1-08-replacement/repair_execution_u.py > "$repair_root-launch-helper-sha256.txt"
shasum -a256 analysis/src/hockey_stats/execution_trace.py > "$repair_root-launch-trace-sha256.txt"
shasum -a256 var/v1-08-replacement/diagnose_execution_u.py > "$repair_root-launch-diagnostic-helper-sha256.txt"
shasum -a256 "$repair_command_path" > "$repair_root-launch-command-sha256.txt"
git status --porcelain --untracked-files=all -- analysis > "$repair_root-launch-analysis-status.txt"
shasum -a256 "$repair_capture/inputs/manifest.json" "$repair_capture/diagnosis/diagnosis.json" "$repair_capture/source-check.json" "$repair_capture/capture-reloaded.json" /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20242025/manifest.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-final-02/20252026/manifest.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/fit-20252026-final-02-source-check.json > "$repair_root-launch-inputs-sha256.txt"
shasum -a256 docs/research/spatial-v1-08/reviews/u-diagnosis-saved-review.md docs/research/spatial-v1-08/receipts/u-capture-diagnosis-completion.json docs/research/spatial-v1-08/execution-u-exact-sum-repair.md var/v1-08-replacement/u-independent-saved-audit.py var/v1-08-replacement/u-independent-saved-audit.log > "$repair_root-launch-acceptance-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python var/v1-08-replacement/repair_execution_u.py --bundle "$repair_capture/inputs/manifest.json" --diagnosis "$repair_capture/diagnosis/diagnosis.json" --diagnosis-sha256 "$repair_diagnosis_sha" --output "$repair_root" > "$repair_root.log" 2>&1
repair_status=$?
set -e
print -r -- "$repair_status" > "$repair_root-exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$repair_root-finish.txt"
exit "$repair_status"
