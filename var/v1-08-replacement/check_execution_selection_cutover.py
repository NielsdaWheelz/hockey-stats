"""temporary selection writer pin/parser controls on tiny manifest scaffolding."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
path=HERE.parents[0]/'v1-08-product/replacement/prepare-real-score-selection.py'
spec=importlib.util.spec_from_file_location('real_execution_selection',path)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
FINAL='40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc'
assert h.EXPECTED['20252026']==FINAL and h.STATES['20252026']=='59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276'
assert str(h.FINAL_STATE).endswith('/u-repair-01/assembled-01/20252026/manifest.json')
assert not hasattr(h,'SELECTION_SHA256')
assert h.FINAL_ACCEPTANCE['sha256']=='8f9163b53c07c264ef59d651bf4860b04333b70a61ec4a19abc7bd4fecfa1953'
# missing acceptance refuses before all input/output reads, including exists().
with patch.object(h,'FINAL_ACCEPTANCE',None),patch.object(Path,'read_bytes',side_effect=AssertionError('file read before acceptance gate')), \
     patch.object(Path,'exists',side_effect=AssertionError('filesystem query before acceptance gate')):
    try:h.main()
    except AssertionError as error:assert str(error)=='accepted final score evidence remains pending'
    else:raise AssertionError('pending final acceptance entered writer')
scratch=Path(tempfile.mkdtemp(prefix='execution-selection-controls-',dir=HERE))
root=scratch/'accepted-inputs';root.mkdir();expected={};previous=None
for season in h.EXPECTED:
    local=root/'scores'/season;local.mkdir(parents=True)
    state=dict(path=str(h.FINAL_STATE if season=='20252026' else root/'execution'/season/'manifest.json'),sha256=h.STATES[season])
    manifest=dict(purpose='real',season=season,prepared=dict(sha256=h.PREPARED,path='/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json'),
        coaches=dict(sha256=h.COACHES,path='/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json'),
        state=dict(state,previous=previous),recipe=dict(sha256=h.RECIPE,name='experimental-v1',version='execution-v1-05-2'),scoring_version='execution-v1-06-1',
        numerical_resolution={'status':'passed' if season=='20252026' else 'not_applicable'})
    data=(json.dumps(manifest)+'\n').encode();(local/'manifest.json').write_bytes(data)
    expected[season]=hashlib.sha256(data).hexdigest();previous=state
accept=scratch/'accepted-review.json';accept.write_text('{"kind":"synthetic-accepted-input-control"}\n')
acceptance=dict(path=str(accept),sha256=hashlib.sha256(accept.read_bytes()).hexdigest())
stream=io.StringIO()
with patch.object(h,'ROOT',root),patch.object(h,'EXPECTED',expected),patch.object(h,'FINAL_ACCEPTANCE',acceptance),redirect_stdout(stream):h.main()
selection=root/'scores-selection.json';data=selection.read_bytes();report=json.loads(stream.getvalue())
assert report==dict(path=str(selection),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
selected=json.loads(data);assert [row['season'] for row in selected['scores']]==list(h.EXPECTED)
assert [row['sha256'] for row in selected['scores']]==list(expected.values())
# same exact manifests must not overwrite an existing exclusive selection.
with patch.object(h,'ROOT',root),patch.object(h,'EXPECTED',expected),patch.object(h,'FINAL_ACCEPTANCE',acceptance):
    try:h.main()
    except AssertionError:pass
    else:raise AssertionError('existing selection overwritten')
selection.unlink()
# a manifest digest that is rebound to a wrong final state still cannot select it.
p=root/'scores/20252026/manifest.json';changed=json.loads(p.read_text());changed['state']['path']=str(root/'execution/20252026/manifest.json')
p.write_text(json.dumps(changed));wrong=dict(expected);wrong['20252026']=hashlib.sha256(p.read_bytes()).hexdigest()
with patch.object(h,'ROOT',root),patch.object(h,'EXPECTED',wrong),patch.object(h,'FINAL_ACCEPTANCE',acceptance):
    try:h.main()
    except AssertionError:pass
    else:raise AssertionError('old final state path accepted')
assert not selection.exists()
print(json.dumps(dict(status='passed',scope='tiny synthetic score manifests and exclusive selection only; no real selection, source, score, strict reader, arrays or composition',
    held_before_io=True,actual_payload_hash_emitted_after_write=True,ordered_five_score_selection=True,old_final_path_and_overwrite_refused=True,scratch=str(scratch)),indent=2))
