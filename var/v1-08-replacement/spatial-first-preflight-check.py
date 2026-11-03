"""temporary first-year CLI dispatch and saved-fixture metadata checks only."""
from contextlib import redirect_stdout,redirect_stderr
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from hockey_stats import analysis_cli
from hockey_stats.artifacts import require

here=Path(__file__).parent
spec=importlib.util.spec_from_file_location('spatial_metadata_acceptance',here/'accept_real_spatial_20212022.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
fixture=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture/spatial/20212022')
kwargs=dict(purpose='fixture',prepared_sha256='603ee00dfe069c99eb5fda3bda9f5d60ea9969fa3820a1df3b5bfcf16cefb7df',
    coaches_sha256='d876634925f7abaabc5e1300efd3a7837511a74628dd98943ffc682b69d7602c',
    valued_sha256='78e029e06cfb50ebdc247117faeb3849459e291be2267c250a9c15858dac7d60')
read_paths=[];original_read=Path.read_bytes

def observed_read(path):
    read_paths.append(str(path));assert path.suffix=='.json','numeric array or source read'
    return original_read(path)
with patch.object(Path,'read_bytes',observed_read):checked=a.inspect_first_year(fixture,**kwargs)
assert checked['head_counts']=={'complete':3} and checked['eligible_as_predecessor']
for defect in ('solver','history','incomplete'):
    def changed(path):
        data=observed_read(path)
        if path.name=='volume.json':
            value=json.loads(data)
            if defect=='solver':value['solver']['options']['ftol']=1e-10
            elif defect=='history':value['priors'][0]['prior_kind']='carry'
            else:value['status']='failed';value['reasons']=['synthetic_optimizer_failure']
            return json.dumps(value).encode()
        if path.name=='manifest.json' and defect=='incomplete':
            value=json.loads(data);value['heads'][0]['status']='failed';return json.dumps(value).encode()
        return data
    with patch.object(Path,'read_bytes',changed):
        if defect=='incomplete':
            refused=a.inspect_first_year(fixture,**kwargs)
            assert not refused['eligible_as_predecessor'] and refused['head_counts']=={'failed':1,'complete':2}
            assert refused['heads']['volume']['reasons']==['synthetic_optimizer_failure']
        else:
            try:a.inspect_first_year(fixture,**kwargs)
            except AssertionError:pass
            else:raise AssertionError('bad '+defect+' accepted')
# CLI dependencies are tiny stubs; this never invokes a source/design/fit/reader.
scratch=Path(tempfile.mkdtemp(prefix='spatial-first-cli-',dir=here))
prepared=scratch/'prepared';prepared.mkdir();(prepared/'manifest.json').write_text('{"purpose":"real"}\n')
argv=['fit','--family','spatial','--prepared',str(prepared),'--coaches',str(scratch/'coaches.json'),
      '--valued',str(scratch/'valued'),'--season','20212022','--out',str(scratch/'out')]
results=[]
for mode in ('pass','head_failure','missing_valued','duplicate_season','first_has_previous','later_lacks_previous'):
    calls=[]
    def read(p,purpose):
        assert p==str(prepared) and purpose=='real';calls.append('prepared_stub')
        return {'seasons':[{'season':'20212022'},{'season':'20222023'}]}
    design=SimpleNamespace(resources={})
    def prepare(*args):calls.append('design_stub');assert args[-1]=='20212022';return design
    def fit(d,previous,out,*,final_year):
        calls.append('fit_stub');assert d is design and previous is None and final_year is False
        return SimpleNamespace(path=out,probes=None,heads={head:{'status':'failed' if mode=='head_failure' and head=='volume' else 'complete'} for head in a.HEADS})
    def no_previous(*args):raise AssertionError('first-year predecessor read')
    active=list(argv)
    if mode=='missing_valued':at=active.index('--valued');del active[at:at+2]
    if mode=='duplicate_season':active+=['--season','20212022']
    if mode=='first_has_previous':active+=['--previous',str(scratch/'old')]
    if mode=='later_lacks_previous':active[active.index('20212022')]='20222023'
    stubs={'hockey_stats.analysis_data':SimpleNamespace(read_prepared=read),
        'hockey_stats.spatial_design':SimpleNamespace(prepare_spatial=prepare),
        'hockey_stats.spatial_rates':SimpleNamespace(fit_spatial=fit),
        'hockey_stats.spatial_state':SimpleNamespace(read_spatial_state=no_previous)}
    with patch.dict(sys.modules,stubs),redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
        try:code=analysis_cli.main(active)
        except SystemExit as error:code=error.code
    expected=0 if mode=='pass' else 2 if mode in ('missing_valued','duplicate_season') else 1
    assert code==expected,(mode,code)
    assert calls==(['prepared_stub','design_stub','fit_stub'] if mode in ('pass','head_failure') else ['prepared_stub'] if mode in ('first_has_previous','later_lacks_previous') else []),(mode,calls)
    results.append(dict(mode=mode,exit=code,calls=calls))
print(json.dumps(dict(status='passed',fixture_metadata_only=True,json_reads=len(read_paths),
    array_source_evaluator_projection_calls=0,metadata_failure_controls=['solver','history','incomplete'],cli_controls=results,scratch=str(scratch)),indent=2))
