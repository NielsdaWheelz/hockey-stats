"""temporary fresh fixture assembly and strict retained-component checks."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from hockey_stats.artifacts import write_json
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity
from hockey_stats.execution_state import read_execution_state
from hockey_stats.execution_u_repair import assemble_u_repair

HERE=Path(__file__).parent
scratch=Path(tempfile.mkdtemp(prefix='u-assembly-controls-',dir=HERE))
repair=HERE/'u-repair-fixture-bhvyu4q8/repair/repair.json'
report=json.loads(repair.read_text())
qualification=json.loads(Path(report['probability_qualification']['path']).read_text())
donor=read_execution_state(qualification['donor']['path'],'fixture')
# assembly must consume saved qualification without recomputation or source/numerical calls.
with patch('hockey_stats.execution_u_repair._probability_comparison',side_effect=AssertionError('probability recomputation during assembly')), \
     patch('hockey_stats.execution_fit.objective',side_effect=AssertionError('full objective during assembly')):
    assembled=assemble_u_repair(repair,scratch/'annual')
assert assembled.usage=='annual' and all(head['resolution']['status']=='passed' for head in assembled.heads.values())
for head in ('u','q','r','g'):
    assert identity(assembled.path.parent/f'heads/{head}.npz')['sha256']==identity(donor.path.parent/f'heads/{head}.npz')['sha256']
    assert {key:value for key,value in assembled.heads[head].items() if key!='resolution'}=={key:value for key,value in donor.heads[head].items() if key!='resolution'}
for head in ('q','r','g'):
    assert identity(assembled.path.parent/f'resolution/{head}.npz')['sha256']==identity(donor.path.parent/f'resolution/{head}.npz')['sha256']
    before=json.loads((donor.path.parent/f'resolution/{head}.json').read_text())
    after=json.loads((assembled.path.parent/f'resolution/{head}.json').read_text())
    assert {key:value for key,value in before.items() if key!='baseline'}=={key:value for key,value in after.items() if key!='baseline'}
    assert before['baseline']!=after['baseline']
a=json.loads((assembled.path.parent/'resolution/baseline.json').read_text())
b=json.loads((donor.path.parent/'resolution/baseline.json').read_text())
assert a['selector']==b['selector'] and a['heads']==b['heads']
assert assembled.manifest['previous']==donor.manifest['previous']
assert assembled.manifest['u_repair']['donor_resources']==donor.manifest['resources']
assert assembled.manifest['u_repair']['performed_resolution_solve_counts']==dict(u=1,q=0,r=0,g=0)
resources=assembled.manifest['resources'];costs=report['resources']
assert resources['fit_wall_seconds']==costs['fit_wall_seconds']
assert resources['qualification_wall_seconds']==costs['qualification_wall_seconds']
assert resources['assembly_wall_seconds']>0 and resources['design_wall_seconds']==0
assert resources['wall_seconds']==sum(resources[name] for name in ('input_read_wall_seconds','design_wall_seconds','fit_wall_seconds','qualification_wall_seconds','assembly_wall_seconds'))
assert assembled.heads['u']['resolution']['comparison']==qualification['comparison']
# no overwrite, orphan trace allowance, changed retained member or unqualified entry.
try:assemble_u_repair(repair,scratch/'annual')
except FileExistsError:pass
else:raise AssertionError('existing assembly overwritten')
(assembled.path.parent/'orphan-trace.json').write_text('{}')
try:read_execution_state(assembled.path,'fixture')
except InputContractError:pass
else:raise AssertionError('orphan diagnostic member accepted')
(assembled.path.parent/'orphan-trace.json').unlink()
manifest=json.loads(assembled.path.read_text());manifest['u_repair']['retained_members'][0]['sha256']='0'*64
assembled.path.write_text(json.dumps(manifest))
try:read_execution_state(assembled.path,'fixture')
except InputContractError:pass
else:raise AssertionError('changed retained-byte binding accepted')
failed=deepcopy(report);failed['status']='stopped';write_json(scratch/'failed-repair.json',failed)
try:assemble_u_repair(scratch/'failed-repair.json',scratch/'forbidden')
except InputContractError:pass
else:raise AssertionError('unqualified repair assembled')
assert not (scratch/'forbidden').exists()
print(json.dumps(dict(status='passed',scope='saved checked fixture repaired endpoint/qualification and canonical assembly/readers only; no source, solve, objective or probability recomputation',
    retained_npz_members=7,baseline_metadata_outside_resolution_exact=True,qrg_probe_metadata_and_comparisons_exact=True,
    selector_and_baseline_definition_hashes_exact=True,truthful_new_phase_costs=True,freshpath_orphan_retained_binding_and_unqualified_refusals=True,
    scratch=str(scratch)),indent=2))
