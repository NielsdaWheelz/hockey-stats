"""temporary observer for one ordinary execution fit/score command; no retries or jobs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import subprocess
from time import perf_counter
from unittest.mock import patch

import numpy as np

from hockey_stats.artifacts import require
from hockey_stats.execution_history import _value
from hockey_stats import execution_design as design

NAMES=('shooter_start_zone:offensive','shooter_start_zone:neutral','shooter_start_zone:defensive')
FLAG='unavailable:shooter_shift_start'
COUNTERS=('masked_on_the_fly','masked_faceoff','unresolved_binding','admitted_same_clock_faceoff','withheld_earlier_anchor')

def encoded(value):return json.dumps(value,allow_nan=False,sort_keys=True,separators=(',',':')).encode()

def responses(attempt):
    state=attempt['feature_facts']['state']['values']
    return dict(details=attempt['details'],immediate_outcomes=attempt['immediate_outcomes'],
                membership={name:state.get(name) for name in ('home_skaters','away_skaters','home_goalies','away_goalies')})


def baseline_start_gap(result, dimension):
    """compare only two independently completed baseline endpoints."""
    starts={row['name']:row for row in result['starts']}
    summary=[{key:starts[name].get(key) for key in ('name','converged','deduplicated_to','objective')}
             for name in ('zero','prior_mean') if name in starts]
    gap=dict(availability='unavailable',reason='incomplete_or_deduplicated_start',starts=summary,
             coefficient_max_change=None,coefficient_l2_change=None)
    if result['status']!='complete' or result['requested_starts']!=['zero','prior_mean'] or len(result['starts'])!=2 or list(starts)!=['zero','prior_mean'] or any(
            name not in starts or starts[name].get('converged') is not True
            or 'deduplicated_to' not in starts[name] or starts[name]['deduplicated_to'] is not None for name in ('zero','prior_mean')):
        return gap
    endpoints=[result['endpoints'].get(name) for name in ('zero','prior_mean')]
    if dimension<=0 or any(not isinstance(value,np.ndarray) or value.shape!=(dimension,) or not np.isfinite(value).all() for value in endpoints):
        gap['reason']='missing_nonfinite_or_wrong_dimension_endpoint'
        return gap
    with np.errstate(over='ignore',invalid='ignore'):
        difference=endpoints[1]-endpoints[0]
        maximum=float(np.max(np.abs(difference)))
        norm=float(np.linalg.norm(difference))
    gap.update(coefficient_max_change=maximum if np.isfinite(maximum) else None,
               coefficient_l2_change=norm if np.isfinite(norm) else None)
    if np.isfinite(maximum) and np.isfinite(norm):
        gap.update(availability='available',reason=None)
    else:
        gap['reason']='nonfinite_gap'
    return gap


def baseline_fit_hook(original, destination, identity, *, native_destination=None):
    recipe_sha=design.RECIPE['sha256']
    def fit_head(design, previous_ledger=None, *, tightened=False, initial=None):
        active=destination is not None and design['head']=='u' and initial is None and not tightened
        native_active=native_destination is not None and design['head']=='u' and initial is not None and tightened
        if active or native_active:
            require(identity['purpose']=='real' and identity['season']=='20252026','u diagnostic requires real20252026')
        if native_active:
            from hockey_stats import chance
            original_minimize=chance.minimize
            def minimize(*args,**kwargs):
                requested=dict(method=kwargs['method'],jac=kwargs['jac'],options=dict(kwargs['options']))
                native=original_minimize(*args,**kwargs)
                fun=float(native.fun)
                classification='finite' if np.isfinite(fun) else 'nan' if np.isnan(fun) else 'posinf' if fun>0 else 'neginf'
                source=Path(identity['source_check_path'])
                with source.open('rb') as stream:source_sha=hashlib.file_digest(stream,'sha256').hexdigest()
                report=dict(kind='temporary-u-continuation-native-result',purpose=identity['purpose'],season=identity['season'],
                    head='u',recipe_sha256=recipe_sha,analysis_tree=identity['analysis_tree'],dimension=design['size'],command=identity['command'],
                    source_check=dict(path=str(source),sha256=source_sha),requested_solver=requested,
                    native_result=dict(success=bool(native.success),status=int(native.status),message=str(native.message),
                        nit=int(native.nit),nfev=int(native.nfev),fun=fun if classification=='finite' else None,fun_classification=classification),
                    scope='literal native OptimizeResult before production postchecks; finite fun does not establish all internal trials were finite; no endpoint array, failure-mechanism inference or numerical-resolution verdict')
                with native_destination.open('x') as stream:json.dump(report,stream,allow_nan=False,indent=2);stream.write('\n')
                return native
            with patch.object(chance,'minimize',minimize):
                result=original(design,previous_ledger,tightened=tightened,initial=initial)
        else:
            result=original(design,previous_ledger,tightened=tightened,initial=initial)
        if active:
            source=Path(identity['source_check_path'])
            with source.open('rb') as stream:source_sha=hashlib.file_digest(stream,'sha256').hexdigest()
            report=dict(kind='temporary-u-baseline-start-gap',purpose=identity['purpose'],season=identity['season'],
                        head='u',recipe_sha256=recipe_sha,analysis_tree=identity['analysis_tree'],dimension=design['size'],command=identity['command'],
                        source_check=dict(path=str(source),sha256=source_sha),
                        endpoint_order=['zero','prior_mean'],scope='two completed baseline starts on the same fit objective; diagnostic only, no threshold or resolution verdict',
                        **baseline_start_gap(result,design['size']))
            with destination.open('x') as stream:json.dump(report,stream,allow_nan=False,indent=2);stream.write('\n')
        return result
    return fit_head


class StartCheck:
    """temporary counts and selected source witnesses, never a model input."""
    def __init__(self,expected=()):
        self.expected=set(expected);self.seen=set();self.known={};self.witnesses={}
        self.counts=Counter();self.by_strength=Counter();self.signature=hashlib.sha256();self.source_signature=hashlib.sha256()
        self.eligibility=Counter({name:0 for name in COUNTERS})
        self.context_rows=[];self.head_populations={}
        self.closed=False;self.overhead_seconds=0.;self.head_admission=None

    def observe(self,output,attempt,game,shooter,history):
        started=perf_counter()
        before=tuple(self.eligibility[name] for name in COUNTERS)
        key=f"{game['game_id']}:{attempt['source_index']}"
        require(key not in self.seen,f'{key}: encoder source context repeated before head construction')
        self.seen.add(key)
        features=output['features'];records=[features[name] for name in NAMES]
        status=[row['status'] for row in records]
        raw=_value(attempt['feature_facts']['deployment'],'players') or {}
        raw=raw.get(str(shooter),{})
        kind,zone=_value(raw,'start_type'),_value(raw,'start_zone')
        available=all(s=='available' for s in status)
        unavailable=all(s=='unavailable' for s in status)
        require(available or unavailable,f'{key}: mixed start availability')
        require(features[FLAG]['value']==float(unavailable),f'{key}: start availability flag differs')
        shifts=[];anchor=None;anchor_order=None;earlier_anchors=[]
        if kind!='on_the_fly':
            shifts=[s for s in game.get('player_shifts') or [] if s['player_id']==shooter
                    and s['period_number']==_value(attempt['feature_facts']['state'],'period_number')
                    and s['start_seconds']==_value(raw,'start_seconds') and s['end_seconds']==_value(raw,'end_seconds')]
            events={r['source']['source_index']:r for r in game.get('events') or []}
            for s in shifts:
                a=events.get(_value(s['start'],'event_source_index'))
                order=_value(a['chronology'],'order_index') if a is not None else None
                focal=history['cutoff']['source_order']
                if _value(s['start'],'kind')=='faceoff' and order is not None and focal is not None and order<focal:
                    earlier_anchors.append(_value(s['start'],'event_source_index'))
        if unavailable and earlier_anchors:self.eligibility['withheld_earlier_anchor']+=1
        expected_available=False
        if kind=='faceoff':
            matched=len(shifts)==1 and _value(shifts[0]['start'],'kind')==kind and _value(shifts[0]['start'],'zone')==zone
            if matched:
                anchor=events.get(_value(shifts[0]['start'],'event_source_index'))
                anchor_order=_value(anchor['chronology'],'order_index') if anchor is not None else None
            if not matched or anchor_order is None or history['cutoff']['source_order'] is None:
                self.eligibility['unresolved_binding']+=1
            if unavailable:
                self.eligibility['masked_faceoff']+=1
            expected_available=(matched and zone in ('offensive','neutral','defensive') and anchor_order is not None
                                and history['cutoff']['source_order'] is not None and anchor_order<history['cutoff']['source_order'])
        elif kind=='on_the_fly':
            if unavailable:self.eligibility['masked_on_the_fly']+=1
            start=_value(raw,'start_seconds');focal=history['cutoff']['elapsed_seconds']
            expected_available=start is not None and focal is not None and start<focal
        require(available==expected_available,f'{key}: start availability differs from independent raw-rule expectation (expected {expected_available}, actual {available})')
        if available:
            if kind=='on_the_fly':
                start=_value(raw,'start_seconds');focal=history['cutoff']['elapsed_seconds']
                require(start is not None and focal is not None and start<focal,f'{key}: actual encoder admitted non-prior on-the-fly start')
                expected=[0.,0.,0.]
            else:
                require(kind=='faceoff' and zone in ('offensive','neutral','defensive'),f'{key}: actual encoder admitted unknown start')
                require(len(shifts)==1 and _value(shifts[0]['start'],'kind')==kind and _value(shifts[0]['start'],'zone')==zone,
                        f'{key}: actual encoder admitted unresolved faceoff binding')
                focal=history['cutoff']['source_order']
                require(anchor_order is not None and focal is not None and anchor_order<focal,f'{key}: actual encoder admitted unproved faceoff')
                self.eligibility['admitted_same_clock_faceoff']+=int(_value(raw,'start_seconds')==history['cutoff']['elapsed_seconds'])
                expected=[float(zone==level) for level in ('offensive','neutral','defensive')]
            require([r['value'] for r in records]==expected,f'{key}: admitted start contrast differs from source')
        age=_value(raw,'age_seconds')
        require(features['shooter_age_seconds/60']['value']==(age/60 if age is not None else None),f'{key}: source age changed')
        disposition=('eligible:' if available else 'unavailable:')+str(kind)
        strength=','.join(map(str,output['strength']))
        self.counts[disposition]+=1;self.by_strength[strength+'|'+disposition]+=1
        flags=sum((self.eligibility[name]-prior)<<i for i,(name,prior) in enumerate(zip(COUNTERS,before)))
        self.context_rows.append((key,disposition,strength,flags))
        witness=dict(key=key,shooter_id=str(shooter),strength=output['strength'],raw_kind=kind,raw_zone=zone,
                     raw_start_seconds=_value(raw,'start_seconds'),focal_clock=history['cutoff']['elapsed_seconds'],
                     focal_order=history['cutoff']['source_order'],anchor_order=anchor_order,matching_coherent_shifts=len(shifts),
                     withheld_earlier_anchor_source_indices=earlier_anchors if unavailable else [],
                     consumed={n:features[n] for n in (*NAMES,FLAG)},saved_age_seconds=age)
        self.witnesses.setdefault(strength+'|'+disposition,witness)
        if key in self.expected:
            require(unavailable,f'{key}: known real timing failure remains admitted')
            self.known[key]=witness
        self.signature.update(encoded(dict(key=key,shooter_id=str(shooter),context=output)))
        self.source_signature.update(encoded(dict(key=key,responses=responses(attempt))))
        self.overhead_seconds+=perf_counter()-started

    def close(self):
        require(self.expected<=self.known.keys(),'known timing witnesses missing before head construction: '+','.join(sorted(self.expected-self.known.keys())))
        self.closed=True

    def head(self,result):
        counts=Counter();strengths=Counter();eligibility=Counter({name:0 for name in COUNTERS})
        require(len(result['rows'])==len(result['keys']),'head inclusion rows/keys differ')
        for index,key in zip(result['rows'],result['keys']):
            observed,disposition,strength,flags=self.context_rows[index]
            require(observed==key,'head physical key differs from observed source row')
            counts[disposition]+=1;strengths[strength+'|'+disposition]+=1
            for i,name in enumerate(COUNTERS):eligibility[name]+=int(bool(flags&(1<<i)))
        self.head_populations[result['head']]=dict(physical_attempts=len(result['keys']),
            key_sha256=hashlib.sha256(encoded(result['keys'])).hexdigest(),
            dispositions=dict(sorted(counts.items())),all_strength_dispositions=dict(sorted(strengths.items())),
            eligibility_counts=dict(eligibility))

    def report(self,status='passed'):
        return dict(kind='temporary-execution-consumed-start-check',status=status,recipe_sha256=design.RECIPE['sha256'],
                    source_contexts=len(self.seen),known_expected=len(self.expected),known_checked=len(self.known),
                    dispositions=dict(sorted(self.counts.items())),all_strength_dispositions=dict(sorted(self.by_strength.items())),
                    eligibility_counts=dict(self.eligibility),
                    head_populations=self.head_populations,
                    count_contract='dispositions partition source contexts; eligibility counts overlap; withheld_earlier_anchor is residual withholding, not an admission requirement',
                    residual_scope='withheld non-on-the-fly record with a saved coherent faceoff start on the exact player/period/start/end binding and earlier saved anchor; cannot detect alternatives absent from coherent saved evidence',
                    source_context_sha256=self.signature.hexdigest(),source_response_sha256=self.source_signature.hexdigest(),
                    known_witnesses=[self.known[k] for k in sorted(self.known)],first_witnesses=list(self.witnesses.values()),
                    before_head_construction=self.closed,observer_seconds=self.overhead_seconds,head_admission=self.head_admission)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out-check',required=True)
    parser.add_argument('--known-census')
    parser.add_argument('--u-baseline-start-gap')
    parser.add_argument('--u-continuation-native')
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args();command=args.command[1:] if args.command[:1]==['--'] else args.command
    require(command and command[0] in ('fit','score'),'observer supports one ordinary execution fit or score')
    require(command[command.index('--family')+1]=='execution','observer only accepts execution family')
    def option(name):return command[command.index(name)+1]
    gap_destination=Path(args.u_baseline_start_gap) if args.u_baseline_start_gap else None
    native_destination=Path(args.u_continuation_native) if args.u_continuation_native else None
    diagnostic_destinations=[path for path in (gap_destination,native_destination) if path is not None]
    if diagnostic_destinations:
        require(command[0]=='fit' and option('--season')=='20252026','u diagnostics require final-year execution fit')
        require(len(set(diagnostic_destinations+[Path(args.out_check)]))==len(diagnostic_destinations)+1,'u diagnostic and source outputs must be distinct')
        for diagnostic_path in diagnostic_destinations:require(not diagnostic_path.exists(),'u diagnostic output already exists')
    prepared=Path(option('--prepared'));prepared=prepared/'manifest.json' if prepared.is_dir() else prepared
    purpose=json.loads(prepared.read_text())['purpose']
    if diagnostic_destinations:require(purpose=='real','u diagnostics require real purpose')
    if command[0]=='fit':season=option('--season')
    else:
        state=Path(option('--state'));state=state/'manifest.json' if state.is_dir() else state
        season=json.loads(state.read_text())['season']
    expected=[]
    if args.known_census:
        expected=[r['key'] for r in json.loads(Path(args.known_census).read_text())]
    require(purpose!='real' or season!='20212022' or len(set(expected))==54,'real20212022 observer requires its exact54-key --known-census')
    check=StartCheck(expected);destination=Path(args.out_check)
    require(not destination.exists(),'source check output already exists')
    original_context=design._feature_context;original_head=design._head_design;original_prepare=design.prepare_execution
    written=False
    def save(status):
        nonlocal written
        report=check.report(status);report.update(command=command,purpose=purpose,season=season)
        with destination.open('x') as stream:json.dump(report,stream,allow_nan=False,indent=2);stream.write('\n')
        written=True
    def context(attempt,game,shooter,goalie,strength,coaches,team_rest,history):
        before=encoded(responses(attempt)) if not check.closed else None
        output=original_context(attempt,game,shooter,goalie,strength,coaches,team_rest,history)
        if not check.closed:
            require(before==encoded(responses(attempt)),'source response/membership mutated by encoder')
            check.observe(output,attempt,game,shooter,history)
        return output
    def head(*values,**kwargs):
        if not check.closed:check.close()
        result=original_head(*values,**kwargs)
        check.head(result)
        return result
    def prepare(*values,**kwargs):
        result=original_prepare(*values,**kwargs)
        check.head_admission=result.coverage['heads']
        save('passed')
        return result
    from hockey_stats.analysis_cli import main as analysis_main
    from hockey_stats import execution_fit
    observed_fit=baseline_fit_hook(execution_fit.fit_head,gap_destination,
        dict(purpose=purpose,season=season,command=command,source_check_path=str(destination),
             analysis_tree=subprocess.check_output(['git','rev-parse','HEAD:analysis'],text=True).strip() if diagnostic_destinations else None),
        native_destination=native_destination)
    sys.argv=['hockey-stats-analysis',*command]
    with patch.object(design,'_feature_context',context),patch.object(design,'_head_design',head),patch.object(design,'prepare_execution',prepare),patch.object(execution_fit,'fit_head',observed_fit):
        try:return analysis_main()
        finally:
            if not written:save('source_construction_incomplete')

if __name__=='__main__':raise SystemExit(main())
