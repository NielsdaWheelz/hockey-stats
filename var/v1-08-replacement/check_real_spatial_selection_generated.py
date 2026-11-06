"""generated-only selection identity and status controls."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile

spec=importlib.util.spec_from_file_location('selection',Path(__file__).with_name('write_real_spatial_selection.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as tmp:
    m.ROOT=Path(tmp);m.DESTINATION=m.ROOT/'states-selection.json';m.PINS={};previous=None
    for season in m.YEARS:
        path=m.ROOT/m.PATHS[season];path.mkdir(parents=True)
        members=[]
        if season==m.YEARS[-1]:
            for head in m.HEADS:
                status='failed' if head=='volume' else 'passed'
                data=json.dumps(dict(status=status,failures=[{'test':1}] if status=='failed' else [])).encode()
                target=path/'probes'/f'{head}-comparison.json';target.parent.mkdir(exist_ok=True);target.write_bytes(data)
                digest=hashlib.sha256(data).hexdigest();m.COMPARISONS[head]=(status,digest)
                members.append(dict(path=str(target.relative_to(path)),role='probe_comparison',sha256=digest))
        manifest=dict(kind='spatial_state',purpose='real',season=season,
            prepared=dict(purpose='real',path='/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json',sha256=m.PREPARED),
            coaches=dict(purpose='real',path='/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json',sha256=m.COACHES),
            valued=dict(purpose='real',season=season,path=str(m.ROOT/'scores'/season/'manifest.json'),sha256=m.SCORES[season]),
            heads=[dict(head=h,status='complete') for h in m.HEADS],recipe_id='experimental-v1',recipe={'test':1},basis_identity={'test':1},previous=previous,files=members)
        raw=json.dumps(manifest).encode();(path/'manifest.json').write_bytes(raw);digest=hashlib.sha256(raw).hexdigest();m.PINS[season]=digest
        previous=dict(season=season,path=str(path/'manifest.json'),sha256=digest,purpose='real',usage='annual')
        recipe=Path(str(m.ROOT/m.RUN_STEMS[season])+'-launch-spatial-recipe.txt');recipe.parent.mkdir(parents=True,exist_ok=True);recipe.write_text(m.RECIPE+'\n')
    with contextlib.redirect_stdout(io.StringIO()): assert m.main()==0
    result=json.loads(m.DESTINATION.read_text());assert result['schema_version']==1 and len(result['states'])==5
    try:
        with contextlib.redirect_stdout(io.StringIO()): m.main()
    except AssertionError: pass
    else: raise AssertionError('overwrite accepted')
    m.DESTINATION.unlink();status,digest=m.COMPARISONS['volume'];m.COMPARISONS['volume']=('passed',digest)
    try:
        with contextlib.redirect_stdout(io.StringIO()): m.main()
    except AssertionError: pass
    else: raise AssertionError('wrong frozen status accepted')
    assert not m.DESTINATION.exists()
    m.COMPARISONS['volume']=(status,'0'*64)
    try:
        with contextlib.redirect_stdout(io.StringIO()): m.main()
    except AssertionError: pass
    else: raise AssertionError('wrong comparison digest accepted')
    assert not m.DESTINATION.exists()
print('generated selector identity, status and exclusive-write controls passed')
