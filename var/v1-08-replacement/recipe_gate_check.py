"""temporary recipe-gate check; original member payloads are never opened."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

from hockey_stats import execution_scores, execution_state
from hockey_stats.captures import InputContractError
from hockey_stats.execution_design import RECIPE


class ArrayBoundaryReached(RuntimeError):
    pass


class UnexpectedPayloadRead(RuntimeError):
    pass


CASES = (
    ('execution_state', execution_state, execution_state.read_execution_state,
     Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-05-20261025-02/20212022/manifest.json'),
     '592dce62062443311ea504cd10c7304b73be10441b6d558e91ca635663940953'),
    ('execution_scores', execution_scores, execution_scores.read_execution_scores,
     Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-01/scores/20212022/manifest.json'),
     '6228d2d415f7f7d9fbf4a0f39ebeb197bd79e1baf8c1d2948f5ac91362d76d7e'),
)


def check(name, module, reader, manifest_path, expected_sha, *, current_control=False):
    payload = manifest_path.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    assert sha == expected_sha, (name, 'original manifest pin differs')
    manifest = json.loads(payload)
    if current_control:
        manifest['recipe'] = deepcopy(RECIPE)
        if name == 'execution_scores':
            manifest['state']['recipe_sha256'] = RECIPE['sha256']
    member_hashes = {row['path']: row['sha256'] for row in manifest['files']}
    members = []
    boundary = []

    def identity(member):
        relative = str(Path(member).relative_to(manifest_path.parent))
        members.append(relative)
        if Path(relative).suffix == '.npz':
            boundary.append(relative)
            raise ArrayBoundaryReached(relative)
        return {'path': str(member), 'sha256': member_hashes[relative]}

    def read_json(path):
        if Path(path) != manifest_path:
            raise UnexpectedPayloadRead(str(path))
        return deepcopy(manifest)

    def load_array(*args, **kwargs):
        raise UnexpectedPayloadRead('np.load called')

    result = dict(kind=name, variant='current_recipe_control' if current_control else 'original',
                  path=str(manifest_path), sha256=sha,
                  original_recipe_sha256=json.loads(payload)['recipe']['sha256'],
                  purpose=manifest['purpose'], season=manifest['season'])
    with patch.object(module, 'identity', identity), patch.object(module, 'read_json', read_json), \
            patch.object(module.np, 'load', load_array):
        try:
            reader(manifest_path, 'real')
        except ArrayBoundaryReached:
            result.update(status='recipe_gate_accepted', array_boundary=boundary[0])
        except InputContractError as error:
            result.update(status='recipe_rejected', reason=str(error))
            assert 'recipe' in str(error), result
            assert not members, 'old recipe rejected after touching members'
        else:
            raise AssertionError('reader returned despite array read spy')
    result.update(member_identity_spy_calls=len(members), actual_member_payload_reads=0,
                  actual_array_loads=0,
                  passes=result['status'] == ('recipe_gate_accepted' if current_control else 'recipe_rejected'))
    return result


parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
results = [check(*case, current_control=current) for case in CASES for current in (False, True)]
receipt = dict(scope='recipe gate only; non-array member identities are stubbed from pinned manifests; original arrays and member payloads are never opened; current-recipe positive controls replace only in-memory recipe/state-recipe fields and are not fitted artifacts',
               current_recipe={k: RECIPE[k] for k in ('name', 'version', 'sha256')},
               cases=results, passed=all(row['passes'] for row in results))
with args.out.open('x') as output:
    json.dump(receipt, output, indent=2)
    output.write('\n')
print(json.dumps(receipt, indent=2))
sys.exit(0 if receipt['passed'] else 1)
