"""tiny source-backed repair-to-probability integration; synthetic authorization only."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
from repair_execution_u import repair

here=Path(__file__).parent
manifest=here/'u-capture-fixture-i9lihlc7/inputs/manifest.json'
scratch=Path(tempfile.mkdtemp(prefix='u-repair-fixture-',dir=here))
# these old fixture anchor vectors establish the unchanged contract. this
# synthetic authorization exercises controller behavior, never a real verdict.
source=here/'u-source-diagnosis-nzfk7p53/diagnosis/evaluation-000'
anchor=scratch/'evaluation-000';anchor.mkdir()
for name in ('x.npy','gradient.npy','addends.npy'):shutil.copyfile(source/name,anchor/name)
diagnosis=scratch/'synthetic-diagnosis.json'
diagnosis.write_text(json.dumps(dict(kind='synthetic-controller-fixture-only',
    status='arithmetic_repair_permitted',reproduced=True,
    first_positive_witness=dict(positive_witness=True),
    bundle_manifest_sha256=sha256(manifest.read_bytes()).hexdigest()))+'\n')
report=repair(manifest,diagnosis,scratch/'repair',expected_diagnosis_sha256=sha256(diagnosis.read_bytes()).hexdigest())
assert report['status']=='qualified',report
assert report['eligible_endpoint'] and not report['assembly_performed']
assert report['basic_qualification']['passed']
assert report['native_evaluation_count_matches']
assert report['resources']['full_objective_calls']==report['full_objective_calls']
assert report['resources']['fit_wall_seconds']>0 and report['resources']['qualification_wall_seconds']>0
assert (scratch/'repair/qualification/heads/u.npz').is_file()
assert not (scratch/'repair/manifest.json').exists()
print(json.dumps(dict(status='passed',source_backed_fixture=True,synthetic_authorization=True,
    full_calls=report['full_objective_calls'],native_calls=report['native_objective_calls'],
    callbacks=report['callbacks'],raw_strict_improvement=True,
    actual_probability_qualification=True,assembly_performed=False,scratch=str(scratch))))
final=json.loads((scratch/'repair/repair.json').read_text())
assert isinstance(final['resources']['fit_wall_seconds'],float)
assert isinstance(final['resources']['qualification_wall_seconds'],float)
assert final['basic_receipt']['sha256']==sha256(Path(final['basic_receipt']['path']).read_bytes()).hexdigest()
assert final['probability_qualification']['sha256']==sha256(Path(final['probability_qualification']['path']).read_bytes()).hexdigest()
print('passed: ordinary numeric final phase resources and exact basic/probability receipt bindings')
