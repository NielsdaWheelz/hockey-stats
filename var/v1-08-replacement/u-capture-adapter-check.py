"""temporary transparent source observer and frozen-selector controls."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from hockey_stats import execution_design as ed
from hockey_stats.captures import InputContractError

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('u_capture',HERE/'capture_execution_u.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
# no source or objective called: capture observer closes before the sole u builder.
observer=module.observer
calls=[]
context=dict(features={name:dict(value=None,status='unavailable') for name in observer.NAMES},strength=(5,5,1))
context['features'][observer.FLAG]=dict(value=1.,status='available')
context['features']['shooter_age_seconds/60']=dict(value=0.,status='available')
attempt=dict(source_index=7,details={},immediate_outcomes={},feature_facts=dict(state={'values':{}},deployment={'values':{'players':{'1':{'values':dict(start_type='on_the_fly',start_seconds=10,age_seconds=0)}}}}))
game=dict(game_id='tiny')
history={'cutoff':{'elapsed_seconds':10,'source_order':7}}
labels=[dict(u=1.,q=1.,r=1.,g=1.)]
predictors=[SimpleNamespace(key='tiny:7')]
expected=observer.StartCheck();expected.observe(context,attempt,game,1,history);expected.close()
for name in ed.HEADS:expected.head(dict(head=name,rows=[0],keys=['tiny:7']))
expected.head_admission={name:{'included':1} for name in ed.HEADS}
expected_report=expected.report()
prepared=SimpleNamespace()
def builder(name,*args,**kwargs):
    calls.append(name);return dict(head=name,rows=[0],keys=['tiny:7'])
def prepare(*args,**kwargs):
    assert kwargs['training_heads']==('u',)
    ed._feature_context(attempt,game,1,None,(5,5,1),{},{},history)
    ed._head_design('u',predictors,labels,{})
    return SimpleNamespace(coverage={'heads':expected.head_admission})
with patch.object(ed,'_feature_context',return_value=context),patch.object(ed,'_head_design',builder),patch.object(ed,'prepare_execution',prepare):
    result,report=module.source_design(prepared,'unused',expected_report)
assert calls==['u'] and report['source_context_sha256']==expected_report['source_context_sha256']
assert report['head_populations']==expected_report['head_populations']
bad=dict(expected_report,source_context_sha256='wrong')
calls.clear()
with patch.object(ed,'_feature_context',return_value=context),patch.object(ed,'_head_design',builder),patch.object(ed,'prepare_execution',prepare):
    try:module.source_design(prepared,'unused',bad)
    except InputContractError:pass
    else:raise AssertionError('source mismatch accepted')
assert calls==[], 'bad source reached numerical head construction'
# direct frozen key restoration never calls the selector owner or builds training heads.
p=SimpleNamespace(key='tiny:7');fixture=SimpleNamespace(key='synthetic-resolution:tiny:7:shooter:9')
selector=dict(keys=['tiny:7'],requirements=[dict(requirement='sparse:q:shooter:9',key=fixture.key,disposition='fixture')],
    fixture_witnesses=[dict(key=fixture.key,attribution=dict(source_key='tiny:7',actor={'id':'9'}))])
design=ed.ExecutionDesign('fixture','20252026',{}, {},None,(p,),{'u':{}},{},(),ed.RECIPE)
donor=SimpleNamespace(heads={name:dict(actors=[dict(id='9',block='shooter')]) for name in ed.HEADS})
def witness(view,name,block,actor):
    assert list(view.heads)==list(ed.HEADS) and view.heads['q'] is donor.heads['q']
    assert name=='sparse:q:shooter:9' and block=='shooter' and actor=='9'
    return fixture,dict(source_key='tiny:7',actor={'id':'9'})
with patch.object(ed,'build_resolution_witness',witness):
    assert module.frozen_probes(design,donor,selector)==(p,fixture)
with patch.object(ed,'build_resolution_witness',return_value=(fixture,{'wrong':'witness'})):
    try:module.frozen_probes(design,donor,selector)
    except InputContractError:pass
    else:raise AssertionError('changed witness accepted')
print(json.dumps(dict(status='passed',scope='tiny transparent source observer and donor-metadata witness injection; no source, fit or objective',
    u_only_builder=True,all_head_population_fingerprints=True,source_mismatch_before_matrix=True,frozen_selector_restoration=True,witness_mismatch_refused=True),indent=2))
