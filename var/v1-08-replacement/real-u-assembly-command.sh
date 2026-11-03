#!/bin/zsh
# saved assembly only. root must accept the saved repair and release this exact command.
# record the runtime launch head after any command/docs commits; fixed tree/helper pins bind code.
# keep the whole head, analysis and helper fixed from launch until this command exits.
set -eu
assembly_command_path=${0:A}
cd /Users/nnandal/Documents/code/hockey-stats-v1-08
assembly_head=$(git rev-parse HEAD)
assembly_tree=fc716257eb118d1a091472cde4b214e8bca1f753
assembly_helper_sha=d0b17338fc4b6b657b3152a4b657dd25c7385d84869b8710bb625510458b576b
assembly_acceptance=/Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/reviews/u-exact-repair-saved-review.md
assembly_acceptance_sha=836e772305415496e437c4319a8ae04fae46970d0b431e38a542ad1d5d7ffbdf
assembly_root=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/assembled-01
assembly_repair=/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/repair.json
for assembly_path in "$assembly_root" "$assembly_root.log" "$assembly_root-start.txt" "$assembly_root-finish.txt" "$assembly_root-exit.txt" "$assembly_root-shell.pid" "$assembly_root-launch-head.txt" "$assembly_root-launch-analysis-tree.txt" "$assembly_root-launch-helper-sha256.txt" "$assembly_root-launch-command-sha256.txt" "$assembly_root-launch-analysis-status.txt" "$assembly_root-launch-inputs-sha256.txt" "$assembly_root-launch-acceptance-sha256.txt"; do
  if [ -e "$assembly_path" ]; then
    print -u2 "occupied path: $assembly_path; command not launched"
    exit 1
  fi
done
[ "$(git rev-parse HEAD:analysis)" = "$assembly_tree" ]
[ -z "$(git status --porcelain --untracked-files=all -- analysis)" ]
assembly_pin() {
  if [ "$(shasum -a256 "$1" | cut -d' ' -f1)" != "$2" ]; then
    print -u2 "pin mismatch: $1; command not launched"
    exit 1
  fi
}
assembly_pin var/v1-08-replacement/assemble_execution_u.py "$assembly_helper_sha"
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/repair.json 28c6d3b9a3f1261191085dd52831e7572103d46f62c2a667fcbbd1ecb53abdf1
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/qualification/qualification.json 2514390196a9e827caaecd67ece0b28cdb069fa5efb7bd339a93970ffd4f9aec
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/basic-qualification.json 02cd47ca8a11217a7fac05e6af8121b356831e78a06beeb1ceed42eeb9956aab
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/inputs/manifest.json 031975b95114fbe62c0e468ebdf16d6170c27f15407b7df71ff0b08e18517a6c
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/diagnosis/diagnosis.json 115da4fe4c18912b74b1970f1825a4338f0f54c6ccd9f0cfb3f7e10dfa026af1
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/source-check.json 9f1351a2cf619e32a7ebeb487a4dda4b3892dcb005b7f2ded917a71354509aa7
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/capture-reloaded.json a10365297148c215f764bb2cde5178602a5eda13563fca36f6345bfd4f7fb9f6
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-final-02/20252026/manifest.json cb075d5e59aea61589411e4573db7192c45fddd8265a807c2c39c2084b504e22
assembly_pin /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20242025/manifest.json 1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe
assembly_pin /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json 63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c
assembly_pin /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json 102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src/hockey_stats/execution_u_repair.py 4c7dfb499cccca81735594389a510850dba68aad700776059500fb7a05cb6522
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src/hockey_stats/execution_state.py 2f65ae947777eefee441af15e7609d3cae2edb5375bc9f99a85a4cf82e57cf14
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/repair_execution_u.py 9ddb1425196328fff332f5ba1da91a231d77fce233fe48565e883b9e594d9c69
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src/hockey_stats/execution_trace.py 89af29e14de76a3a8f332b3753c5640d9b6c825f493719163dd687b7b824bc13
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/diagnose_execution_u.py 031f30d640c0d526e35d8d862803718c1f565ee99ca2ef5638b9e36df3f25ca1
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/reviews/u-diagnosis-saved-review.md 2e04c4a6331c2a36f176e0e307b0f520a5255d19cb23513935f13da9b80ecdbd
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/receipts/u-capture-diagnosis-completion.json 6950fed6a7593168e9554515387debcc9e0d02b091d71995f57a00272da623d9
assembly_pin /Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/execution-u-exact-sum-repair.md 6beb304528f63ecb335ddab57e9baa9eb31be5099471cb5033d5810e0515abb7
assembly_pin "$assembly_acceptance" "$assembly_acceptance_sha"
[ "$(git rev-parse HEAD)" = "$assembly_head" ]
set -C
print -r -- $$ > "$assembly_root-shell.pid"
date -u +%Y-%m-%dT%H:%M:%SZ > "$assembly_root-start.txt"
print -r -- "$assembly_head" > "$assembly_root-launch-head.txt"
git rev-parse HEAD:analysis > "$assembly_root-launch-analysis-tree.txt"
shasum -a256 var/v1-08-replacement/assemble_execution_u.py > "$assembly_root-launch-helper-sha256.txt"
shasum -a256 "$assembly_command_path" > "$assembly_root-launch-command-sha256.txt"
git status --porcelain --untracked-files=all -- analysis > "$assembly_root-launch-analysis-status.txt"
shasum -a256 /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/repair.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/qualification/qualification.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/repair-01/basic-qualification.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/inputs/manifest.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/diagnosis/diagnosis.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/source-check.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01/capture-reloaded.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-final-02/20252026/manifest.json /Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution/20242025/manifest.json /Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json /Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src/hockey_stats/execution_u_repair.py /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src/hockey_stats/execution_state.py /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/repair_execution_u.py /Users/nnandal/Documents/code/hockey-stats-v1-08/analysis/src/hockey_stats/execution_trace.py /Users/nnandal/Documents/code/hockey-stats-v1-08/var/v1-08-replacement/diagnose_execution_u.py /Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/reviews/u-diagnosis-saved-review.md /Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/receipts/u-capture-diagnosis-completion.json /Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/execution-u-exact-sum-repair.md > "$assembly_root-launch-inputs-sha256.txt"
shasum -a256 "$assembly_acceptance" > "$assembly_root-launch-acceptance-sha256.txt"
set +e
/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python var/v1-08-replacement/assemble_execution_u.py --repair "$assembly_repair" --output "$assembly_root/20252026" --expected-launch-head "$assembly_head" --expected-helper-sha256 "$assembly_helper_sha" --acceptance "$assembly_acceptance" --acceptance-sha256 "$assembly_acceptance_sha" > "$assembly_root.log" 2>&1
assembly_status=$?
set -e
print -r -- "$assembly_status" > "$assembly_root-exit.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$assembly_root-finish.txt"
exit "$assembly_status"
