"""execution objective observations and transparent pinned native solver traces."""
from fractions import Fraction
from hashlib import sha256
import inspect
import json
import math
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy
from scipy.optimize import _lbfgsb, _lbfgsb_py

from . import chance
from .execution_design import DEFINITION

SOURCE_COMMIT = 'e4e854eaa8f18d807cd3496028e257e36caa93cc'


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


class DiagnosticStop(RuntimeError):
    pass


class Evaluations:
    """the single full-objective boundary and ordinary partial-trace owner."""
    def __init__(self, output, objective, *, limit, native_limit):
        self.output, self.objective, self.limit = output, objective, limit
        self.native_limit = native_limit
        self.calls = []
        self.phase = 'anchor'
        self.native_calls = 0
        self.native = False
        self.observer = None
        self.identical_inputs = {}

    def __call__(self, x, design, actors, responsibilities=None):
        if ((self.limit is not None and len(self.calls)>=self.limit) or
                (self.native and self.native_limit is not None and self.native_calls>=self.native_limit)):
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
                partial=np.asarray(terms,dtype=np.float64)
                record.update(status='failed' if np.isfinite(partial).all() else 'nonfinite_partial_addends',
                              error=repr(error),seconds=perf_counter()-began)
                np.save(folder/'partial-addends.npy',partial,allow_pickle=False)
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
