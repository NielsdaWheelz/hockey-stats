"""independent scratch-only substitution of native capture launcher effects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

work = Path.cwd()
source = work/'var/v1-08-replacement/real-u-capture-command.sh'
command = source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest() == '1e88d781780e16bf85d32d7d11060a2afaa6306eccbdd98e5c3ca3b2f1116c0a'
subprocess.run(['zsh', '-n', str(source)], check=True)
subprocess.run(['sh', '-n', str(source)], check=True)
scratch = Path(tempfile.mkdtemp(prefix='u-independent-shell-', dir=work/'var/v1-08-replacement'))
binpath = scratch/'bin'; binpath.mkdir()
def executable(name, text):
    path = binpath/name
    path.write_text(text)
    path.chmod(0o755)
    return path
executable('git', '''#!/bin/sh
case "$*" in
'rev-parse HEAD') echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
'rev-parse HEAD:analysis') echo 54e41d821b1cc12fb262be4c42d6898a610c37fe ;;
'status --porcelain --untracked-files=all -- analysis') : ;;
*) exit 81 ;;
esac
''')
executable('shasum', '''#!/bin/sh
shift
for name in "$@"; do
case "$name" in
var/v1-08-replacement/capture_execution_u.py) echo "e42f7be944a5350a9096b953559835cddbeb6f9a2081113f01eae32131951d5c  $name" ;;
var/v1-08-replacement/diagnose_execution_u.py) echo "2142a218e9759c9103db29e728605efaf7492363efd888cd2c019b956f51ec4d  $name" ;;
*) echo "scratch-stub-input-digest  $name" ;;
esac
done
''')
runner = executable('fake-capture', '''#!/bin/sh
printf 'scratch-only standin arguments: %s\\n' "$*"
exit "$U_INDEPENDENT_EXIT"
''')
realroot = '/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/u-repair-01'
assert command.count(realroot) == 1
original_runner = '/usr/bin/time -l env PYTHONPATH=analysis/src analysis/.venv/bin/python var/v1-08-replacement/capture_execution_u.py'
assert command.count(original_runner) == 1
results = []
for status in (0, 1, 7):
    root = scratch/f'status-{status}'
    script = scratch/f'status-{status}.sh'
    script.write_text(command.replace(realroot, str(root)).replace(original_runner, '/usr/bin/time -l '+str(runner)))
    environment = dict(os.environ, PATH=str(binpath)+':'+os.environ['PATH'], U_INDEPENDENT_EXIT=str(status))
    result = subprocess.run(['zsh', str(script)], env=environment, capture_output=True, text=True)
    assert result.returncode == status, (result, root)
    assert (Path(str(root)+'-exit.txt')).read_text().strip() == str(status)
    assert all(Path(str(root)+suffix).is_file() for suffix in ('.log', '-start.txt', '-finish.txt', '-shell.pid', '-launch-head.txt', '-launch-analysis-tree.txt', '-launch-capture-sha256.txt', '-launch-diagnosis-sha256.txt', '-launch-analysis-status.txt', '-launch-inputs-sha256.txt'))
    assert not root.exists()
    before = Path(str(root)+'.log').read_bytes()
    again = subprocess.run(['zsh', str(script)], env=environment, capture_output=True, text=True)
    assert again.returncode == 1 and 'occupied path:' in again.stderr
    assert Path(str(root)+'.log').read_bytes() == before
    results.append(dict(standin_status=status, shell_status=result.returncode, exact_status_receipt=True, occupied_path_refused=True, log_preserved=True))
print(json.dumps(dict(status='passed', command_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), scope='zsh shell with scratch output root and standin git/shasum/capture; no real capture or input read', results=results, scratch=str(scratch)), indent=2))
