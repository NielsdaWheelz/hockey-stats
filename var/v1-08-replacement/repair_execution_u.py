"""one exact-u continuation on frozen inputs; assembly is a separate phase."""
import argparse
from hashlib import sha256
import inspect
import json
import resource
import sys
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
from scipy.optimize import _lbfgsb, _lbfgsb_py

from hockey_stats import chance, execution_fit, execution_trace
from hockey_stats.artifacts import json_values, ordered_array_digest, write_json
from hockey_stats.execution_design import DEFINITION, RECIPE
from hockey_stats.execution_inputs import load_u_bundle
from hockey_stats.execution_trace import (DiagnosticStop, Evaluations, NativeObserver,
                                          same_bits, save_json)


def endpoint_qualification(native, callbacks, accepted_native_iterations, initial,
                           completed, start_value, endpoint_value):
    """native motion precedes mean completion; improvement uses fresh evaluations."""
    checks=dict(
        native_success=bool(native.success and native.status==0),
        native_finite=bool(np.isfinite(native.fun) and np.isfinite(native.x).all()
                           and np.isfinite(native.jac).all()),
        native_iteration=bool(native.nit>0 and callbacks==native.nit
                              and accepted_native_iterations==native.nit),
        raw_movement=bool(not np.array_equal(native.x,initial)),
        fresh_values_finite=bool(np.isfinite(start_value) and np.isfinite(endpoint_value)),
        strict_fresh_improvement=bool(endpoint_value<start_value),
        completed_finite=bool(np.isfinite(completed).all()),
        completed_movement=bool(not np.array_equal(completed,initial)),
    )
    return dict(passed=all(checks.values()),checks=checks,
                fresh_start_objective=start_value,fresh_raw_endpoint_objective=endpoint_value,
                raw_coefficient_max_change=float(np.max(np.abs(native.x-initial))),
                completed_coefficient_max_change=float(np.max(np.abs(completed-initial))))


def repair(bundle_manifest, diagnosis_path, output, *, expected_diagnosis_sha256):
    """one native solve; no source rebuild, old probe solve or annual assembly."""
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    began=perf_counter()
    evaluations=observer=None
    solve_started=probability_started=fit_finished=None
    report=dict(status='started',eligible_endpoint=False,assembly_performed=False,
                added_global_evaluation_cap=None,added_native_evaluation_cap=None)
    try:
        diagnosis_path=Path(diagnosis_path)
        diagnosis_bytes=diagnosis_path.read_bytes()
        diagnosis_sha=sha256(diagnosis_bytes).hexdigest()
        if diagnosis_sha!=expected_diagnosis_sha256:
            raise DiagnosticStop('diagnosis_pin_mismatch')
        diagnosis=json.loads(diagnosis_bytes)
        if (diagnosis['status']!='arithmetic_repair_permitted' or
                not diagnosis['reproduced'] or
                not diagnosis['first_positive_witness']['positive_witness']):
            raise DiagnosticStop('arithmetic_repair_not_permitted')
        bundle_manifest=Path(bundle_manifest)
        bundle_sha=sha256(bundle_manifest.read_bytes()).hexdigest()
        if bundle_sha!=diagnosis['bundle_manifest_sha256']:
            raise DiagnosticStop('diagnosis_input_bundle_mismatch')
        report.update(diagnosis=dict(path=str(diagnosis_path),sha256=diagnosis_sha),
                      inputs=dict(path=str(bundle_manifest),sha256=bundle_sha),
                      execution_fit_sha256=sha256(Path(execution_fit.__file__).read_bytes()).hexdigest(),
                      trace_owner_path=str(Path(execution_trace.__file__)),
                      trace_owner_sha256=sha256(Path(execution_trace.__file__).read_bytes()).hexdigest(),
                      repair_source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
        save_json(output/'repair.json',report)
        reload_started=perf_counter()
        bundle=load_u_bundle(bundle_manifest)
        report['reload_wall_seconds']=perf_counter()-reload_started
        design,actors,initial=(bundle[k] for k in ('design','actors','initial'))
        if design['head']!='u' or bundle['metadata']['recipe']!=RECIPE:
            raise DiagnosticStop('repair_head_or_statistical_recipe_mismatch')
        ledger=bundle['metadata']['incoming_ledger']
        if json.dumps(execution_fit.annual_priors(design,ledger),sort_keys=True)!=json.dumps(actors,sort_keys=True):
            raise DiagnosticStop('reloaded_annual_prior_mismatch')
        anchor_dir=diagnosis_path.parent/'evaluation-000'
        anchor_gradient=np.load(anchor_dir/'gradient.npy',allow_pickle=False)
        anchor_addends=np.load(anchor_dir/'addends.npy',allow_pickle=False)
        anchor_x=np.load(anchor_dir/'x.npy',allow_pickle=False)
        if not same_bits(anchor_x,initial):
            raise DiagnosticStop('diagnosed_saved_start_mismatch')
        original=execution_fit.objective
        evaluations=Evaluations(output,original,limit=None,native_limit=None)
        evaluations.phase='repair_continuation'
        observer=NativeObserver(output,evaluations,initial)
        default_options=inspect.signature(_lbfgsb_py._minimize_lbfgsb).parameters
        report['native_limits']=dict(maxiter=DEFINITION['solver']['maxiter'],
            maxfun=default_options['maxfun'].default,maxls=default_options['maxls'].default,
            ftol=DEFINITION['solver']['continuation']['ftol'],
            gtol=DEFINITION['solver']['continuation']['gtol'])
        save_json(output/'repair.json',report)
        def traced_objective(x,head,current_actors,responsibilities=None):
            f,g=evaluations(x,head,current_actors,responsibilities)
            current=evaluations.calls[-1]
            if not same_bits(f,float(current['reference'])):
                raise DiagnosticStop('repaired_loss_not_exact_component_sum')
            if current['number']==0 and not (same_bits(current['x'],initial) and
                    same_bits(g,anchor_gradient) and same_bits(current['addends'],anchor_addends)):
                raise DiagnosticStop('repaired_anchor_gradient_or_addends_changed')
            return f,g
        solve_started=perf_counter()
        with patch.object(execution_fit,'objective',traced_objective), \
             patch.object(chance,'minimize',observer.minimize), \
             patch.object(_lbfgsb,'setulb',observer):
            result=execution_fit.continue_head(design,ledger,initial)
        report['continuation_wall_seconds']=perf_counter()-solve_started
        for name,endpoint in result['endpoints'].items():
            np.save(output/f'completed-{name}-endpoint.npy',endpoint,allow_pickle=False)
        summary={key:value for key,value in result.items() if key not in ('coefficients','endpoints')}
        save_json(output/'continuation-result.json',json_values(summary))
        raw=observer.result
        if raw is None:
            raise DiagnosticStop('repair_missing_native_result')
        report['native_evaluation_count_matches']=bool(evaluations.native_calls==raw.nfev)
        report['native_limit_overruns']=dict(
            iterations=max(0,int(raw.nit)-report['native_limits']['maxiter']),
            evaluations=max(0,int(raw.nfev)-report['native_limits']['maxfun']))
        if result['status']!='complete' or not raw.success:
            raise DiagnosticStop('repair_native_incomplete')
        if not report['native_evaluation_count_matches']:
            raise DiagnosticStop('repair_native_evaluation_count_mismatch')
        completed=result['coefficients']
        # fresh values from the same repaired evaluator, after the native return.
        evaluations.phase='qualification_fresh_saved_start'
        start_value,start_gradient=traced_objective(initial,design,actors)
        start_evaluation=evaluations.calls[-1]['number']
        evaluations.phase='qualification_fresh_raw_endpoint'
        endpoint_value,endpoint_gradient=traced_objective(raw.x,design,actors)
        endpoint_evaluation=evaluations.calls[-1]['number']
        accepted=sum(event.get('after_task',[None])[0]==1 for event in observer.events)
        basic=endpoint_qualification(raw,observer.callbacks,accepted,initial,completed,start_value,endpoint_value)
        basic.update(saved_start_evaluation=start_evaluation,raw_endpoint_evaluation=endpoint_evaluation,
                     raw_gradient_max=float(np.max(np.abs(endpoint_gradient))),
                     saved_start_gradient_max=float(np.max(np.abs(start_gradient))),
                     raw_gradient_max_change=float(np.max(np.abs(endpoint_gradient-start_gradient))))
        report['basic_qualification']=basic
        if not basic['passed']:
            save_json(output/'basic-qualification.json',basic)
            raise DiagnosticStop('repair_endpoint_qualification_failed')
        contract=dict(native_success=basic['checks']['native_success'],
            accepted_native_iterations=accepted,accepted_callbacks=observer.callbacks,
            raw_endpoint_moved=basic['checks']['raw_movement'],
            fresh_start_objective=start_value,fresh_raw_endpoint_objective=endpoint_value,
            completed_endpoint_moved=basic['checks']['completed_movement'],
            completed_coefficients_sha256=ordered_array_digest({'coefficients':completed}))
        basic['qualification']=contract
        write_json(output/'basic-qualification.json',json_values(basic))
        result['u_repair_qualification']=dict(contract,basic_receipt=dict(
            path=str(output/'basic-qualification.json'),
            sha256=sha256((output/'basic-qualification.json').read_bytes()).hexdigest()))
        report['basic_receipt']=result['u_repair_qualification']['basic_receipt']
        summary['u_repair_qualification']=result['u_repair_qualification']
        save_json(output/'continuation-result.json',json_values(summary))
        from hockey_stats.execution_u_repair import qualify_u_bundle
        fit_finished=perf_counter()
        probability_started=fit_finished
        qualification=qualify_u_bundle(bundle,result,output/'qualification')
        report['probability_qualification_wall_seconds']=perf_counter()-probability_started
        qualification_path=Path(qualification['receipt'])
        report['probability_qualification']=dict(path=str(qualification_path),
            sha256=sha256(qualification_path.read_bytes()).hexdigest())
        report['qualification_wall_seconds']=json.loads(qualification_path.read_bytes())['wall_seconds']
        if not qualification['probability_passed']:
            raise DiagnosticStop('repair_probability_qualification_failed')
        report.update(status='qualified',eligible_endpoint=True,
                      reason='native_motion_fresh_improvement_and_frozen_probability_check_passed')
    except BaseException as error:
        report.update(status='stopped',reason=str(error),exception=type(error).__name__)
        if not isinstance(error,DiagnosticStop):
            report['unexpected_error']=repr(error)
    finally:
        finished=perf_counter()
        report['resources']=dict(
            input_read_wall_seconds=(finished if solve_started is None else solve_started)-began,
            fit_wall_seconds=0. if solve_started is None else (finished if fit_finished is None else fit_finished)-solve_started,
            qualification_wall_seconds=report.get('qualification_wall_seconds',
                0. if probability_started is None else finished-probability_started),
            peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
            full_objective_calls=0 if evaluations is None else len(evaluations.calls))
        report.update(full_objective_calls=0 if evaluations is None else len(evaluations.calls),
                      native_objective_calls=0 if evaluations is None else evaluations.native_calls,
                      native_events=0 if observer is None else len(observer.events),
                      callbacks=0 if observer is None else observer.callbacks,
                      wall_seconds=perf_counter()-began,
                      trace_bytes_excluding_final_receipt=sum(p.stat().st_size for p in output.rglob('*')
                          if p.is_file() and p.name!='repair.json'))
        if 'basic_qualification' in report and not report['basic_qualification']['passed']:
            report['basic_qualification']=dict(passed=False,checks=report['basic_qualification']['checks'],
                diagnostic_receipt=dict(path=str(output/'basic-qualification.json'),
                    sha256=sha256((output/'basic-qualification.json').read_bytes()).hexdigest()))
        (output/'repair.json').write_text(json.dumps(json_values(report),indent=2,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--diagnosis',required=True,type=Path)
    parser.add_argument('--diagnosis-sha256',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    report=repair(args.bundle,args.diagnosis,args.output,expected_diagnosis_sha256=args.diagnosis_sha256)
    print(json.dumps(dict(status=report['status'],reason=report.get('reason'),
        full_objective_calls=report['full_objective_calls'],native_objective_calls=report['native_objective_calls'])))
    return 0 if report['status']=='qualified' else 1


if __name__=='__main__':
    raise SystemExit(main())
