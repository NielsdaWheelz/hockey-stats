"""tiny injected hook checks; no model, source context or native solver call."""
from copy import deepcopy
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
from types import CodeType
from unittest.mock import patch

import numpy as np
from hockey_stats.captures import InputContractError

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
OBSERVER=WORK/'var/v1-08-replacement/consumed_start_check.py'


def main():
    began=perf_counter()
    original_source=(OBSERVER.parent/'consumed_start_check-286.py').read_bytes()
    assert hashlib.sha256(original_source).hexdigest()=='286b34dd95ae9cf60a562ad9ec6426000d04a9e658ee3977b7b88080099fedaf'
    def code_signature(code):
        return (code.co_code,tuple(code_signature(value) if isinstance(value,CodeType) else value for value in code.co_consts),
                code.co_names,code.co_varnames,code.co_freevars,code.co_cellvars,code.co_argcount,code.co_posonlyargcount,
                code.co_kwonlyargcount,code.co_flags,code.co_exceptiontable)
    def code_objects(code):
        result={code.co_qualname:code}
        for value in code.co_consts:
            if isinstance(value,CodeType):result.update(code_objects(value))
        return result
    before=code_objects(compile(original_source,str(OBSERVER),'exec'))
    after=code_objects(compile(OBSERVER.read_bytes(),str(OBSERVER),'exec'))
    preserved=['encoded','responses','main.<locals>.option','main.<locals>.save',
               'main.<locals>.context','main.<locals>.head','main.<locals>.prepare']
    preserved += [name for name in before if name.startswith('StartCheck.')]
    assert all(code_signature(before[name])==code_signature(after[name]) for name in preserved)
    original_class=next(node for node in ast.parse(original_source).body if isinstance(node,ast.ClassDef) and node.name=='StartCheck')
    current_class=next(node for node in ast.parse(OBSERVER.read_bytes()).body if isinstance(node,ast.ClassDef) and node.name=='StartCheck')
    assert ast.dump(original_class)==ast.dump(current_class)
    spec=importlib.util.spec_from_file_location('gap_observer',OBSERVER)
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    scratch=Path(tempfile.mkdtemp(prefix='u-gap-controls-',dir=OBSERVER.parent))
    source=scratch/'source-check.json';source.write_text('{"kind":"synthetic-source-check","status":"passed"}\n')
    identity=dict(purpose='real',season='20252026',command=['fit','--family','execution','--season','20252026'],
                  source_check_path=str(source),analysis_tree='59813412b3ef66bb66ae60f5daf930716d00073e')
    base=dict(status='complete',requested_starts=['zero','prior_mean'],selected_start='zero',
              starts=[dict(name=name,converged=True,deduplicated_to=None,objective=10.+i) for i,name in enumerate(('zero','prior_mean'))],
              endpoints=dict(zero=np.zeros(2),prior_mean=np.array([3.,4.])))
    def snapshot(value):
        if isinstance(value,np.ndarray):return (value.dtype.str,value.shape,value.tobytes())
        if isinstance(value,dict):return {key:snapshot(item) for key,item in value.items()}
        if isinstance(value,list):return [snapshot(item) for item in value]
        return value
    results=[]
    for mode in ('complete','zero_gap','incomplete','deduplicated','missing_deduplication','duplicate_start','missing_endpoint','nonfinite_endpoint','wrong_dimension','overflow'):
        result=deepcopy(base)
        if mode=='incomplete':result['starts'][1]['converged']=False
        if mode=='deduplicated':result['starts'][1]=dict(name='prior_mean',deduplicated_to='zero')
        if mode=='missing_deduplication':result['starts'][1].pop('deduplicated_to')
        if mode=='duplicate_start':result['starts'].append(deepcopy(result['starts'][1]))
        if mode=='zero_gap':result['endpoints']['prior_mean']=np.zeros(2)
        if mode=='missing_endpoint':result['endpoints'].pop('prior_mean')
        if mode=='nonfinite_endpoint':result['endpoints']['prior_mean'][0]=np.nan
        if mode=='wrong_dimension':result['endpoints']['prior_mean']=np.zeros(3)
        if mode=='overflow':result['endpoints']['prior_mean']=np.array([1e308,0.])
        calls=[];prior=snapshot(result)
        def original(design,previous_ledger=None,*,tightened=False,initial=None):
            calls.append((design,previous_ledger,tightened,initial));return result
        destination=scratch/(mode+'.json')
        hook=observer.baseline_fit_hook(original,destination,identity)
        assert hook(dict(head='u',size=2)) is result and len(calls)==1 and snapshot(result)==prior
        report=json.loads(destination.read_text())
        assert report['source_check']==dict(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        assert report['analysis_tree']==identity['analysis_tree'] and 'endpoints' not in report
        if mode=='complete':
            assert report['availability']=='available' and report['coefficient_max_change']==4. and report['coefficient_l2_change']==5.
        elif mode=='zero_gap':
            assert report['availability']=='available' and report['coefficient_max_change']==report['coefficient_l2_change']==0.
        elif mode=='overflow':
            assert report['availability']=='unavailable' and report['coefficient_max_change']==1e308 and report['coefficient_l2_change'] is None
        else:
            assert report['availability']=='unavailable' and report['coefficient_max_change'] is report['coefficient_l2_change'] is None
        results.append(dict(mode=mode,availability=report['availability'],reason=report['reason'],original_calls=len(calls)))
    bypasses=[]
    for mode,head,tightened,initial,requested in [('non_u','q',False,None,True),('continuation','u',True,np.zeros(2),True),
            ('tightened','u',True,None,True),('unrequested','u',False,None,False)]:
        calls=[]
        def original(design,previous_ledger=None,*,tightened=False,initial=None):calls.append(1);return base
        destination=scratch/(mode+'.json')
        hook=observer.baseline_fit_hook(original,destination if requested else None,identity)
        assert hook(dict(head=head,size=2),tightened=tightened,initial=initial) is base
        assert calls==[1] and not destination.exists()
        bypasses.append(mode)
    from hockey_stats import execution_fit
    previous=execution_fit.fit_head
    with patch.object(execution_fit,'fit_head',observer.baseline_fit_hook(lambda *a,**k:base,None,identity)):
        from hockey_stats.execution_fit import fit_head as captured_alias
        assert captured_alias(dict(head='u',size=2)) is base
    assert execution_fit.fit_head is previous
    calls=[]
    def original(design,previous_ledger=None,*,tightened=False,initial=None):calls.append(1);return base
    wrong=observer.baseline_fit_hook(original,scratch/'wrong-purpose.json',dict(identity,purpose='fixture'))
    try:wrong(dict(head='u',size=2))
    except InputContractError:pass
    else:raise AssertionError('wrong purpose accepted')
    assert calls==[]
    # only argument guards run; any attempted prepared/header read is an error.
    refused=[]
    occupied=scratch/'occupied.json';occupied.write_text('untouched')
    for mode,command,destination in [('score',['score','--family','execution'],scratch/'score.json'),
            ('family',['fit','--family','spatial','--season','20252026'],scratch/'family.json'),
            ('season',['fit','--family','execution','--season','20242025'],scratch/'season.json'),
            ('occupied',['fit','--family','execution','--season','20252026'],occupied)]:
        argv=['observer','--out-check',str(scratch/'unused-source.json'),'--u-baseline-start-gap',str(destination),'--',*command,'--prepared','/unread']
        with patch.object(sys,'argv',argv),patch.object(Path,'read_text',side_effect=AssertionError('artifact read before refusal')):
            try:observer.main()
            except InputContractError:refused.append(mode)
            else:raise AssertionError('invalid request accepted: '+mode)
    assert occupied.read_text()=='untouched'
    output=dict(status='passed',observer_sha256=hashlib.sha256(OBSERVER.read_bytes()).hexdigest(),
        original_observer_sha256=hashlib.sha256(original_source).hexdigest(),oracle_bytecode_unchanged=preserved,
        source_report_fields_unchanged=True,hook_modes=results,bypasses=bypasses,original_result_identity_and_contents_preserved=True,
        alias_capture_and_restore=True,early_refusals=refused+['wrong_purpose_before_original'],
        scratch=str(scratch),scope='tiny injected results and hook/argument guards only; no analysis_main/model/native solver/source context or real payload invoked',
        wall_seconds=perf_counter()-began)
    destination=OBSERVER.parent/'u-baseline-start-gap-controls-03.json'
    with destination.open('x') as stream:json.dump(output,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
