"""one bounded diagnosis over frozen u inputs; never produces a fitted head.

reference sums measure outer accumulation only. the native observer targets the
pinned scipy 1.18.1 c implementation, including its zero-based workspace offsets.
"""
import argparse
from fractions import Fraction
from hashlib import sha256
import inspect
import json
import math
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
import scipy
from scipy.optimize import _lbfgsb, _lbfgsb_py

from hockey_stats import chance, execution_fit
from hockey_stats.execution_design import DEFINITION

STEPS = (1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7)
DIRECTION_NAMES = ('gradient', 'largest_gradient_coordinate', 'intercept',
                   'base_maps', 'type_maps', 'circumstances',
                   'supported_shooter_actors', 'attacking_coaches',
                   'defending_coaches', 'ages', 'supported_actor_age',
                   'prior_only', 'all')
SOURCE_COMMIT = 'e4e854eaa8f18d807cd3496028e257e36caa93cc'
ANCHOR_LOSS = 69668.42305740231
ANCHOR_GMAX = 0.002770559377087478


def encoded(value):
    if isinstance(value, Fraction):
        return dict(numerator=str(value.numerator), denominator=str(value.denominator),
                    rounded=float(value).hex())
    if isinstance(value, np.generic):
        return encoded(value.item())
    if isinstance(value, float):
        return dict(hex=value.hex(), classification='finite' if math.isfinite(value)
                    else 'nan' if math.isnan(value) else 'posinf' if value > 0 else 'neginf')
    if isinstance(value, dict):
        return {str(k): encoded(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encoded(v) for v in value]
    return value


def save_json(path, value):
    path.write_text(json.dumps(encoded(value), indent=2, allow_nan=False)+'\n')


def reference(addends):
    return sum((Fraction.from_float(float(term)) for term in addends), Fraction())


def same_bits(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()


def direction_evidence(points, analytic):
    """all comparisons use exact represented arithmetic; no certified bounds."""
    analytic = Fraction.from_float(float(analytic))
    scales = []
    for i in range(1, 6):
        p = points[i]
        noise = abs(p['D']-p['R'])
        truncation = max(abs(p['R']-points[i-1]['R']), abs(p['R']-points[i+1]['R']))
        budget = noise+truncation
        discrepancy = analytic-p['R']
        scales.append(dict(index=i, h=STEPS[i], ordinary=p['D'], reference=p['R'],
                           signed_discrepancy=discrepancy, outer_error=noise,
                           truncation_trend=truncation, empirical_budget=budget,
                           outside=abs(discrepancy)>budget,
                           contains_analytic=abs(discrepancy)<=budget,
                           excludes_zero=abs(p['R'])>budget))
    unresolved = resolved = None
    for left, right in zip(scales, scales[1:]):
        if (unresolved is None and left['outside'] and right['outside'] and
                left['signed_discrepancy']*right['signed_discrepancy']>0):
            unresolved = [left['index'], right['index']]
        if (resolved is None and left['contains_analytic'] and right['contains_analytic'] and
                left['excludes_zero'] and right['excludes_zero']):
            resolved = [left['index'], right['index']]
    return dict(scales=scales, unresolved_window=unresolved, resolved_window=resolved)


def trial_evidence(start_loss, start_reference, trial_loss, trial_reference,
                   step, gdold, gd, displaced, associated):
    """strict same-trial reversal across native separate/fma threshold forms."""
    values = (start_loss, trial_loss, step, gdold, gd)
    if not all(math.isfinite(float(x)) for x in values):
        return dict(positive_witness=False, reason='nonfinite_trial')
    # gtest rounds first; reassociating 1e-3, step and gdold changes the contract.
    gtest = float(1e-3*gdold)
    separate = float(start_loss+float(step*gtest))
    fused = math.fma(step, gtest, start_loss)
    reference_start = float(start_reference)
    reference_trial = float(trial_reference)
    reference_separate = float(reference_start+float(step*gtest))
    reference_fused = math.fma(step, gtest, reference_start)
    exact_decrease = trial_reference-start_reference
    exact_limit = Fraction.from_float(step)*Fraction.from_float(gtest)
    original_margins = [trial_loss-separate, trial_loss-fused]
    rounded_margins = [reference_trial-reference_separate, reference_trial-reference_fused]
    curvature_margin = float(.9*(-gdold))-abs(gd)
    witness = bool(associated and displaced and step>0 and gdold<0 and
                   all(margin>0 for margin in original_margins) and
                   all(margin<0 for margin in rounded_margins) and
                   exact_decrease<exact_limit and curvature_margin>0)
    return dict(positive_witness=witness, associated=associated, displaced=displaced,
                step=step, gdold=gdold, gd=gd, gtest=gtest,
                original_thresholds=[separate, fused],
                rounded_reference_thresholds=[reference_separate, reference_fused],
                original_margins=original_margins, rounded_margins=rounded_margins,
                exact_decrease=exact_decrease, exact_limit=exact_limit,
                exact_margin=exact_decrease-exact_limit, curvature_margin=curvature_margin,
                signed_accumulation_discrepancy=Fraction.from_float(trial_loss)-trial_reference,
                start_accumulation_discrepancy=Fraction.from_float(start_loss)-start_reference)


def directions(design, actors, gradient):
    """frozen names, eligibility, index tie breaking and sha256 sign rule."""
    names = design['design']['coefficient_names']
    maps = np.asarray(design['map_indices'], dtype=np.int64)
    supported = [a['index'] for a in actors if a['likelihood_support']]
    groups = dict(base_maps=maps[0], type_maps=maps[1:].ravel(),
                  circumstances=design['circumstance_indices'], ages=design['age_indices'],
                  supported_actor_age=supported+list(design['age_indices']),
                  prior_only=[a['index'] for a in actors if not a['likelihood_support']],
                  all=range(len(names)))
    for name, block in [('supported_shooter_actors','shooter'),
                         ('attacking_coaches','attacking_coach'),
                         ('defending_coaches','defending_coach')]:
        groups[name] = [a['index'] for a in actors if a['block']==block and a['likelihood_support']]
    result = {}
    for name in DIRECTION_NAMES:
        vector = np.zeros(len(names), dtype=np.float64)
        if name == 'gradient':
            vector[:] = gradient
        elif name == 'largest_gradient_coordinate':
            vector[int(np.argmax(np.abs(gradient)))] = 1.
        elif name == 'intercept':
            vector[names.index('intercept')] = 1.
        else:
            indices = np.unique(np.asarray(list(groups[name]), dtype=np.int64))
            for index in indices:
                sign = sha256((name+'\0'+names[index]).encode('utf-8')).digest()[0] & 1
                vector[index] = 1. if sign == 0 else -1.
        norm = np.linalg.norm(vector)
        result[name] = None if norm == 0 else vector/norm
    return result


def gradient_direction_evidence(state, initial, gradient, direction):
    """verify the pinned first-cauchy floating realization, without a tolerance.

    first col=0/theta=1 gives f2=-f1 and dtm=-f1/f2=1. unbounded
    cauchy uses daxpy(1,-g,x), then mainlb subtracts x. both possible
    scalar f1 expression forms must remain finite/nonzero; neither is
    an objective/gradient error bound or a changed comparison threshold.
    """
    separate = fused = 0.
    for value in gradient:
        negative = float(-value)
        separate = float(separate-float(negative*negative))
        fused = math.fma(-negative,negative,fused)
    dtm_forms = []
    for f1 in (separate,fused):
        f2 = float(-1.*f1)
        dtm_forms.append(None if not math.isfinite(f1) or f1==0. else float(-f1/f2))
    guards = dict(iteration_zero=int(state['isave'][29])==0,
                  no_corrections=int(state['isave'][27])==0 and int(state['isave'][30])==0,
                  theta_one=same_bits(float(state['dsave'][0]),1.),
                  no_bounds=bool(np.all(state['nbd']==0) and state['lsave'][1]==0),
                  cauchy_unit_step=dtm_forms==[1.,1.])
    expected = np.subtract(np.subtract(initial,gradient),initial)
    residual = direction+gradient
    record = dict(guards=guards,construction='fl64(fl64(x_start-g_start)-x_start)',
                  exact_construction=same_bits(direction,expected),
                  f1_separate=separate,f1_fma=fused,dtm_forms=dtm_forms,
                  different_from_ideal_coordinates=int(np.count_nonzero(direction!=-gradient)),
                  relative_ideal_residual=float(np.linalg.norm(residual)/np.linalg.norm(gradient)),
                  analytic_gradient_dot_native_direction=float(np.dot(gradient,direction)),
                  ideal_negative_gradient_squared_norm=float(-np.dot(gradient,gradient)))
    record['resolved']=bool(all(guards.values()) and record['exact_construction'])
    return record


class DiagnosticStop(RuntimeError):
    pass


class Evaluations:
    """the single full-objective boundary and ordinary partial-trace owner."""
    def __init__(self, output, objective, limit=256):
        self.output, self.objective, self.limit = output, objective, limit
        self.calls = []
        self.phase = 'anchor'
        self.native_calls = 0
        self.native = False
        self.observer = None
        self.identical_inputs = {}

    def __call__(self, x, design, actors, responsibilities=None):
        if len(self.calls)>=self.limit or (self.native and self.native_calls>=64):
            raise DiagnosticStop('full_objective_cap')
        number = len(self.calls)
        folder = self.output/f'evaluation-{number:03d}'
        folder.mkdir()
        np.save(folder/'x.npy', x, allow_pickle=False)
        record = dict(number=number, phase=self.phase, status='started', path=folder.name)
        self.calls.append(record)
        save_json(folder/'record.json', record)
        if self.native:
            self.native_calls += 1
        terms = []
        began = perf_counter()
        try:
            f, g = self.objective(x, design, actors, responsibilities, addends=terms)
            terms = np.asarray(terms, dtype=np.float64)
            np.save(folder/'gradient.npy', g, allow_pickle=False)
            np.save(folder/'addends.npy', terms, allow_pickle=False)
            finite = bool(math.isfinite(f) and np.isfinite(g).all() and np.isfinite(terms).all())
            r = reference(terms) if finite else None
            record.update(status='finite' if finite else 'nonfinite', loss=f,
                          reference=r, seconds=perf_counter()-began,
                          signed_accumulation_discrepancy=Fraction.from_float(f)-r if finite else None)
            save_json(folder/'record.json', record)
            record.update(x=np.array(x, copy=True), gradient=np.array(g, copy=True),
                          addends=terms, loss=f, reference=r)
            if not finite:
                raise DiagnosticStop('nonfinite_objective_trace')
            identity=sha256(record['x'].tobytes()).digest()
            earlier=self.identical_inputs.get(identity)
            if earlier is not None:
                assert_repeat(earlier,record)
            else:
                self.identical_inputs[identity]=record
            if self.observer is not None:
                self.observer.evaluated(record)
            return f, g
        except BaseException as error:
            if record['status']=='started':
                record.update(status='failed', error=repr(error), seconds=perf_counter()-began)
                np.save(folder/'partial-addends.npy', np.asarray(terms,dtype=np.float64), allow_pickle=False)
                save_json(folder/'record.json', record)
            raise

    def evaluate(self, x, design, actors, phase):
        self.phase = phase
        self(x, design, actors)
        return self.calls[-1]


def assert_repeat(left, right):
    if not all(same_bits(left[key],right[key]) for key in ('x','gradient','addends','loss')):
        raise DiagnosticStop('nonrepeatable_objective_gradient_or_addends')


class NativeObserver:
    """transparent original setulb calls with exact request/response pairing.

    source setulb stores direction's zero-based start in isave[12] and
    line-search starting x in isave[13]. mainlb receives &isave[21], while
    dsave is unshifted: fold[1], gd[10], step[13], gdold[14]. dcsrch receives
    &dsave[16], whose gtest is offset 1 and finit offset 4.
    """
    def __init__(self, output, evaluations, initial):
        if scipy.__version__!='1.18.1' or np.__version__!='2.5.3':
            raise DiagnosticStop('unpinned_native_environment')
        wrapper_hash=sha256(inspect.getsource(_lbfgsb_py._minimize_lbfgsb).encode()).hexdigest()
        if wrapper_hash!='e2ee79963e9c64c5119845a1f5db3e39acbd1799571b4b02d74e608bd2863b95':
            raise DiagnosticStop('unpinned_native_python_wrapper')
        self.output, self.evaluations, self.initial = output, evaluations, initial
        self.original = _lbfgsb.setulb
        self.pending = None
        self.events, self.trials = [], []
        self.callbacks = 0
        self.result = None
        self.options = None
        self.first_direction = None
        self.first_start = None
        self.first_state = None
        self.evaluations.observer = self
        save_json(output/'native-identity.json',dict(scipy=scipy.__version__,numpy=np.__version__,
            source_commit=SOURCE_COMMIT,
            native_module_sha256=sha256(Path(_lbfgsb.__file__).read_bytes()).hexdigest(),
            python_wrapper_sha256=sha256(inspect.getsource(_lbfgsb_py._minimize_lbfgsb).encode()).hexdigest()))

    def evaluated(self, record):
        if self.pending is not None:
            if not same_bits(self.pending['x'],record['x']):
                raise DiagnosticStop('native_request_objective_x_mismatch')

    def snapshot(self, args, destination):
        # all array arguments, including complete workspace and controls, survive.
        arrays = {name:np.asarray(value).copy() for name,value in zip(
            ('m','x','lower','upper','nbd','f','gradient','factr','pgtol','wa','iwa',
             'task','lsave','isave','dsave','maxls','ln_task'),args)}
        np.savez(destination, **arrays)
        return arrays

    def __call__(self, *args):
        number = len(self.events)
        before = self.snapshot(args,self.output/f'native-{number:03d}-before.npz')
        record = dict(number=number, status='started')
        self.events.append(record)
        save_json(self.output/f'native-{number:03d}.json',record)
        consumed = None
        if tuple(before['task']) in ((3,301),(3,302)):
            if self.pending is None or not same_bits(before['x'],self.pending['x']):
                raise DiagnosticStop('unresolved_native_request_association')
            # scipy may serve cached initial/repeated x without a full call.
            response = next((r for r in reversed(self.evaluations.calls)
                if 'gradient' in r and same_bits(r['x'],before['x']) and
                same_bits(r['loss'],before['f']) and same_bits(r['gradient'],before['gradient'])),None)
            if response is None:
                raise DiagnosticStop('unresolved_native_response_association')
            consumed = dict(self.pending, response=response['number'])
            self.pending = None
        try:
            returned = self.original(*args)  # exactly one unchanged native invocation.
        except BaseException as error:
            record.update(status='failed', error=repr(error))
            save_json(self.output/f'native-{number:03d}.json',record)
            raise
        after = self.snapshot(args,self.output/f'native-{number:03d}-after.npz')
        record.update(status='complete',before_task=before['task'].tolist(),after_task=after['task'].tolist())
        if consumed is not None:
            record['consumed_evaluation']=consumed['response']
            if consumed['task']==[3,302]:
                # gd survives the native local-state save even when x is restored.
                consumed.update(gd=float(after['dsave'][10]), consumption_event=number,
                                after_task=after['task'].tolist())
                self.trials.append(consumed)
        if tuple(after['task']) in ((3,301),(3,302)):
            self.pending = dict(event=number,task=after['task'].tolist(),x=after['x'].copy())
            if tuple(after['task'])==(3,302):
                n=len(after['x']); offset=int(after['isave'][12]); start=int(after['isave'][13])
                direction=after['wa'][offset:offset+n].copy()
                search_start=after['wa'][start:start+n].copy()
                if len(direction)!=n or len(search_start)!=n:
                    raise DiagnosticStop('invalid_native_workspace_offsets')
                np.save(self.output/f'native-{number:03d}-direction.npy',direction,allow_pickle=False)
                np.save(self.output/f'native-{number:03d}-start.npy',search_start,allow_pickle=False)
                ds=after['dsave']
                self.pending.update(direction=direction,search_start=search_start,
                                    step=float(ds[13]),gdold=float(ds[14]),fold=float(ds[1]),
                                    native_gtest=float(ds[17]),native_finit=float(ds[20]))
                if self.first_direction is None:
                    self.first_direction,self.first_start=direction.copy(),search_start.copy()
                    self.first_state=after
        save_json(self.output/f'native-{number:03d}.json',record)
        return returned

    def callback(self, x):
        np.save(self.output/f'callback-{self.callbacks:03d}.npy',x,allow_pickle=False)
        self.callbacks += 1

    def minimize(self, objective, initial, **kwargs):
        expected=dict(maxiter=DEFINITION['solver']['maxiter'],
                      ftol=DEFINITION['solver']['continuation']['ftol'],
                      gtol=DEFINITION['solver']['continuation']['gtol'])
        if kwargs!=dict(method='L-BFGS-B',jac=True,options=expected):
            raise DiagnosticStop('changed_original_solver_options')
        self.options=dict(expected)
        save_json(self.output/'native-options.json',dict(kwargs,initial_bits=sha256(np.asarray(initial).tobytes()).hexdigest()))
        self.evaluations.native=True
        try:
            result=chance_minimize(objective,initial,callback=self.callback,**kwargs)
            self.result=result
            np.save(self.output/'raw-native-endpoint.npy',result.x,allow_pickle=False)
            np.save(self.output/'raw-native-gradient.npy',result.jac,allow_pickle=False)
            save_json(self.output/'raw-native-result.json',dict(success=bool(result.success),
                status=int(result.status),message=str(result.message),nit=int(result.nit),
                nfev=int(result.nfev),njev=int(result.njev),fun=float(result.fun),
                endpoint_sha256=sha256(result.x.tobytes()).hexdigest(),
                raw_displacement_max=float(np.max(np.abs(result.x-self.initial)))))
            return result  # original OptimizeResult identity, before production postchecks.
        finally:
            self.evaluations.native=False


chance_minimize = chance.minimize


def summarize_trials(observer, anchor, initial, evaluations, output):
    trials=[]
    for trial in observer.trials:
        response=evaluations.calls[trial['response']]
        start=next((r for r in reversed(evaluations.calls[:trial['response']+1])
            if 'reference' in r and same_bits(r['x'],trial['search_start']) and
            same_bits(r['loss'],trial['fold'])),None)
        if start is None:
            item=dict(positive_witness=False,associated=False,
                      reason='unresolved_native_start_reference',step=trial['step'],
                      gdold=trial['gdold'],gd=trial['gd'],
                      signed_accumulation_discrepancy=Fraction.from_float(response['loss'])-response['reference'])
        else:
            associated=bool(same_bits(start['x'],initial) and
                same_bits(start['loss'],anchor['loss']) and
                same_bits(trial['native_finit'],start['loss']) and
                same_bits(trial['native_gtest'],float(1e-3*trial['gdold'])) and
                same_bits(trial['direction'],observer.first_direction) and same_bits(trial['x'],response['x']))
            item=trial_evidence(start['loss'],start['reference'],response['loss'],response['reference'],
                trial['step'],trial['gdold'],trial['gd'],not np.array_equal(trial['x'],start['x']),associated)
            item['search_start_evaluation']=start['number']
        item.update(request_event=trial['event'],consumption_event=trial['consumption_event'],
                    response_evaluation=trial['response'])
        trials.append(item)
    save_json(output/'trial-evidence.json',trials)
    return trials


def diagnose(bundle_path, output):
    """loads checked inputs; every full evaluation belongs to the same cap."""
    from hockey_stats.execution_inputs import load_u_bundle
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    began=perf_counter()
    report=dict(status='started',eligible_endpoint=False,
                arithmetic_scope='outer scalar accumulation only; inner errors unbounded',
                direction_names=DIRECTION_NAMES,steps=STEPS,full_objective_cap=256,native_evaluation_cap=64)
    evaluations=observer=anchor=None
    try:
        bundle_path=Path(bundle_path)
        manifest_path=bundle_path/'manifest.json' if bundle_path.is_dir() else bundle_path
        bundle=load_u_bundle(manifest_path)
        design,actors,initial=(bundle[k] for k in ('design','actors','initial'))
        if design['head']!='u' or not np.isfinite(initial).all():
            raise DiagnosticStop('invalid_captured_u_inputs')
        report['bundle_manifest_sha256']=sha256(manifest_path.read_bytes()).hexdigest()
        save_json(output/'diagnosis.json',report)
        original_objective=execution_fit.objective
        evaluations=Evaluations(output,original_objective)
        anchor=evaluations.evaluate(initial,design,actors,'reloaded_anchor')
        if not same_bits(anchor['loss'],ANCHOR_LOSS) or not same_bits(float(np.max(np.abs(anchor['gradient']))),ANCHOR_GMAX):
            raise DiagnosticStop('reloaded_anchor_mismatch')
        report['capture_validation']=dict(status='checked_reloaded_anchors',
            bundle_manifest_sha256=report['bundle_manifest_sha256'],
            objective=anchor['loss'],gradient_max=float(np.max(np.abs(anchor['gradient']))),
            objective_bits=np.float64(anchor['loss']).tobytes().hex(),
            gradient_max_bits=np.float64(np.max(np.abs(anchor['gradient']))).tobytes().hex())
        save_json(output/'diagnosis.json',report)
        for i in range(2):
            repeated=evaluations.evaluate(initial,design,actors,f'baseline_repeat_{i+1}')
            assert_repeat(anchor,repeated)
        frozen=directions(design,actors,anchor['gradient'])
        evidence={}
        for name,vector in frozen.items():
            if vector is None:
                evidence[name]=dict(status='unavailable_empty_group')
                continue
            np.save(output/f'direction-{name}.npy',vector,allow_pickle=False)
            points=[]
            for h in STEPS:
                endpoints=[]
                for sign in (1.,-1.):
                    x=initial+(sign*h)*vector
                    point=evaluations.evaluate(x,design,actors,f'{name}:h={h}:sign={sign}')
                    endpoints.append(point)
                    if name=='gradient' and h==1e-3:
                        repeated=evaluations.evaluate(x,design,actors,f'{name}:h={h}:sign={sign}:repeat')
                        assert_repeat(point,repeated)
                plus,minus=endpoints
                denominator=Fraction.from_float(float(2*h))
                ordinary=float((plus['loss']-minus['loss'])/(2*h))
                points.append(dict(h=h,plus=plus['number'],minus=minus['number'],
                    D=Fraction.from_float(ordinary),R=(plus['reference']-minus['reference'])/denominator))
            evidence[name]=dict(status='measured',analytic=float(np.dot(anchor['gradient'],vector)),
                                points=points,**direction_evidence(points,np.dot(anchor['gradient'],vector)))
        save_json(output/'direction-evidence.json',evidence)
        report['directions']=evidence
        # original continuation only; diagnosis never qualifies its returned endpoint.
        ledger=bundle['metadata']['incoming_ledger']
        recomputed=execution_fit.annual_priors(design,ledger)
        if json.dumps(recomputed,sort_keys=True)!=json.dumps(actors,sort_keys=True):
            raise DiagnosticStop('reloaded_annual_prior_mismatch')
        observer=NativeObserver(output,evaluations,initial)
        evaluations.phase='original_continuation'
        with patch.object(execution_fit,'objective',evaluations), \
             patch.object(chance,'minimize',observer.minimize), \
             patch.object(_lbfgsb,'setulb',observer):
            continuation=execution_fit.continue_head(design,ledger,initial)
        np.save(output/'completed-diagnostic-endpoint.npy',continuation['endpoints']['continuation'],allow_pickle=False)
        trials=summarize_trials(observer,anchor,initial,evaluations,output)
        raw=observer.result
        reproduced=bool(raw is not None and not raw.success and raw.status==2 and raw.nit==0 and
            raw.nfev==19 and evaluations.native_calls==raw.nfev and
            same_bits(float(raw.fun),ANCHOR_LOSS) and same_bits(raw.x,initial))
        report['reproduced']=reproduced
        if not reproduced:
            raise DiagnosticStop('original_failure_unreproduced')
        bad=[name for name,e in evidence.items() if e.get('unresolved_window') is not None]
        if bad:
            report['unresolved_derivative_directions']=bad
            raise DiagnosticStop('unresolved_derivative_discrepancy')
        gradient_window=evidence['gradient'].get('resolved_window')
        direction=observer.first_direction
        direction_record = None if direction is None else gradient_direction_evidence(
            observer.first_state,initial,anchor['gradient'],direction)
        direction_resolved=bool(direction_record is not None and direction_record['resolved'] and
                                same_bits(observer.first_start,initial))
        if direction_record is not None:
            np.save(output/'native-first-direction-ideal-residual.npy',direction+anchor['gradient'],allow_pickle=False)
            save_json(output/'native-first-direction-evidence.json',direction_record)
        report['native_first_direction']=direction_record
        report['native_first_direction_resolved']=direction_resolved
        if gradient_window is None or not direction_resolved:
            raise DiagnosticStop('unresolved_descent_direction_window')
        witness=next((t for t in trials if t['positive_witness']),None)
        report['first_positive_witness']=witness
        report['status']='arithmetic_repair_permitted' if witness else 'inconclusive'
        report['reason']='positive_same_trial_outer_arithmetic_witness' if witness else 'no_complete_positive_witness'
        report['native_events']=len(observer.events)
        report['callbacks']=observer.callbacks
    except BaseException as error:
        report.update(status='stopped',reason=str(error),exception=type(error).__name__)
        if not isinstance(error,DiagnosticStop):
            report['unexpected_error']=repr(error)
    finally:
        if observer is not None and anchor is not None and not (output/'trial-evidence.json').exists():
            try:
                summarize_trials(observer,anchor,initial,evaluations,output)
            except Exception as error:
                report['partial_trial_finalization_error']=repr(error)
        report.update(full_objective_calls=0 if evaluations is None else len(evaluations.calls),
                      native_objective_calls=0 if evaluations is None else evaluations.native_calls,
                      wall_seconds=perf_counter()-began,
                      trace_bytes_excluding_final_receipt=sum(p.stat().st_size for p in output.rglob('*')
                          if p.is_file() and p.name!='diagnosis.json'))
        save_json(output/'diagnosis.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=diagnose(args.bundle,args.output)
    print(json.dumps(dict(status=result['status'],reason=result.get('reason'),
                          full_objective_calls=result['full_objective_calls'])))
    return 0 if result['status']=='arithmetic_repair_permitted' else 1


if __name__=='__main__':
    raise SystemExit(main())
