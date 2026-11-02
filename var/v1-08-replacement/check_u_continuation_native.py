"""tiny raw OptimizeResult hook checks; the optimizer/objective are never run."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from time import perf_counter
from unittest.mock import patch

import numpy as np
from scipy.optimize import OptimizeResult
from hockey_stats import chance
from hockey_stats.captures import InputContractError

HERE=Path(__file__).parent


def main():
    began=perf_counter()
    observer_path=HERE/'consumed_start_check.py'
    spec=importlib.util.spec_from_file_location('native_observer',observer_path)
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    scratch=Path(tempfile.mkdtemp(prefix='u-native-controls-',dir=HERE))
    source=scratch/'source-check.json';source.write_text('{"kind":"synthetic-source-check","status":"passed"}\n')
    identity=dict(purpose='real',season='20252026',command=['fit','--family','execution','--season','20252026'],
        source_check_path=str(source),analysis_tree='59813412b3ef66bb66ae60f5daf930716d00073e')
    outcomes=[]
    for mode,fun,classification,raw_success in [('finite',1.25,'finite',False),('nan',np.nan,'nan',False),
            ('posinf',np.inf,'posinf',False),('neginf',-np.inf,'neginf',False),
            ('success_then_postcheck_failure',2.,'finite',True),('outer_raise',3.,'finite',False),
            ('native_options_mutation',4.,'finite',False)]:
        destination=scratch/(mode+'.json')
        initial=np.zeros(2);options=dict(maxiter=10000,ftol=1e-16,gtol=1e-7)
        supplied=dict(options)
        raw=OptimizeResult(success=raw_success,status=0 if raw_success else 2,message='synthetic native stop',nit=0,nfev=7,fun=fun,x=initial)
        fitted=dict(status='unavailable',starts=[dict(objective=99.,converged=False)])
        calls=[]
        def objective(*args):raise AssertionError('objective called')
        def native(original_objective,original_initial,**kwargs):
            assert original_objective is objective and original_initial is initial
            assert kwargs['method']=='L-BFGS-B' and kwargs['jac'] is True and kwargs['options'] is options
            calls.append('native')
            if mode=='native_options_mutation':options['ftol']=.5
            return raw
        def original(design,previous_ledger=None,*,tightened=False,initial=None):
            calls.append('fit')
            returned=chance.minimize(objective,initial,method='L-BFGS-B',jac=True,options=options)
            assert returned is raw and destination.exists()
            # the capture must precede this outer postcheck/row-builder outcome.
            report=json.loads(destination.read_text())
            assert report['native_result']['fun_classification']==classification
            assert report['native_result']['fun']==(fun if classification=='finite' else None)
            if mode=='outer_raise':raise RuntimeError('synthetic later row-builder failure')
            return fitted
        with patch.object(chance,'minimize',native):
            hook=observer.baseline_fit_hook(original,None,identity,native_destination=destination)
            try:returned=hook(dict(head='u',size=2),tightened=True,initial=initial)
            except RuntimeError as error:
                assert mode=='outer_raise' and str(error)=='synthetic later row-builder failure'
            else:assert returned is fitted
            assert chance.minimize is native
        assert calls==['fit','native'] and raw.fun is fun
        report=json.loads(destination.read_text())
        assert report['native_result']==dict(success=raw_success,status=raw.status,message=raw.message,nit=0,nfev=7,
            fun=fun if classification=='finite' else None,fun_classification=classification)
        assert report['requested_solver']==dict(method='L-BFGS-B',jac=True,options=supplied)
        assert report['source_check']==dict(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        assert report['analysis_tree']==identity['analysis_tree'] and 'x' not in report and 'coefficients' not in report
        assert options==(dict(supplied,ftol=.5) if mode=='native_options_mutation' else supplied)
        outcomes.append(dict(mode=mode,fun_classification=classification,raw_result_identity=True,
            fit_result_identity=mode!='outer_raise',native_calls=1,capture_before_postcheck=True))
    bypasses=[]
    for mode,head,tightened,initial,requested in [('non_u','q',True,np.zeros(2),True),('baseline','u',False,None,True),
            ('not_tightened','u',False,np.zeros(2),True),('unrequested','u',True,np.zeros(2),False)]:
        destination=scratch/(mode+'.json');fitted=object();calls=[]
        def original(design,previous_ledger=None,*,tightened=False,initial=None):calls.append(1);return fitted
        hook=observer.baseline_fit_hook(original,None,identity,native_destination=destination if requested else None)
        assert hook(dict(head=head,size=2),tightened=tightened,initial=initial) is fitted
        assert calls==[1] and not destination.exists()
        bypasses.append(mode)
    # an impossible/malformed raw result must fail visibly, not become unavailable.
    destination=scratch/'malformed.json'
    def original(design,previous_ledger=None,*,tightened=False,initial=None):
        return chance.minimize(lambda *args:None,initial,method='L-BFGS-B',jac=True,options={})
    with patch.object(chance,'minimize',lambda *a,**k:OptimizeResult(success=False,status=2,message='bad',nit=0,nfev=1,fun=None)):
        try:observer.baseline_fit_hook(original,None,identity,native_destination=destination)(dict(head='u',size=2),tightened=True,initial=np.zeros(2))
        except TypeError:pass
        else:raise AssertionError('malformed native fun accepted')
    assert not destination.exists()
    calls=[]
    def original(design,previous_ledger=None,*,tightened=False,initial=None):calls.append(1);return None
    wrong=observer.baseline_fit_hook(original,None,dict(identity,purpose='fixture'),native_destination=scratch/'wrong.json')
    try:wrong(dict(head='u',size=2),tightened=True,initial=np.zeros(2))
    except InputContractError:pass
    else:raise AssertionError('wrong purpose accepted')
    assert calls==[]
    early=[]
    occupied=scratch/'occupied.json';occupied.write_text('untouched')
    for mode,command,destination,extra in [('score',['score','--family','execution'],scratch/'score.json',[]),
            ('family',['fit','--family','spatial','--season','20252026'],scratch/'family.json',[]),
            ('season',['fit','--family','execution','--season','20242025'],scratch/'season.json',[]),
            ('occupied',['fit','--family','execution','--season','20252026'],occupied,[]),
            ('same_source',['fit','--family','execution','--season','20252026'],scratch/'unused-source.json',[]),
            ('same_gap',['fit','--family','execution','--season','20252026'],scratch/'same.json',['--u-baseline-start-gap',str(scratch/'same.json')])]:
        argv=['observer','--out-check',str(scratch/'unused-source.json'),'--u-continuation-native',str(destination),*extra,'--',*command,'--prepared','/unread']
        with patch.object(sys,'argv',argv),patch.object(Path,'read_text',side_effect=AssertionError('artifact read before refusal')):
            try:observer.main()
            except InputContractError:early.append(mode)
            else:raise AssertionError('invalid native request accepted: '+mode)
    assert occupied.read_text()=='untouched'
    result=dict(status='passed',observer_sha256=hashlib.sha256(observer_path.read_bytes()).hexdigest(),outcomes=outcomes,
        bypasses=bypasses,malformed_native_result_refused=True,purpose_refused_before_original=True,
        early_refusals=early,
        scope='raw OptimizeResult objects and stubbed original functions only; no optimizer, objective, source context, real payload or ordinary analysis_main invoked',
        scratch=str(scratch),wall_seconds=perf_counter()-began)
    with (HERE/'u-continuation-native-controls-03.json').open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
