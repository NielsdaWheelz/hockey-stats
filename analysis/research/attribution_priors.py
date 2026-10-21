"""04l's finite accounting of saved annual-prior fits; no refitting."""

import argparse
import json
import os
from pathlib import Path
import sys
import time

for _thread in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[_thread] = '1'

import numpy as np
from scipy.stats import t

from hockey_stats.artifacts import artifact, json_values, require, resources, write_json
from hockey_stats.attribution import decompose_shape_history, shape_history_carry, validate_shape_history_identity
from hockey_stats.attribution_data import exposure_centering, read_history_source_slice, read_history_final_record
from hockey_stats.attribution_prediction import shape_recovery, same_deployment_excess
from hockey_stats.captures import InputContractError
from hockey_stats.chance_cli import identity, output_path

SPEC = Path(__file__).resolve().parents[2] / 'docs/specs/04l-attribution-prior-diagnosis.md'
RESEARCH_ROOT = Path('/Volumes/Expansion/hockey-stats/runs')
CELLS = ('gaussian_half', 'gaussian_base', 'gaussian_double', 'gaussian_null', 'game_shared_base')
AMPLITUDES = dict(zip(CELLS, (.5, 1., 2., 0., 1.), strict=True))
ROLES = ('offense', 'attempts_allowed')
RECEIVERS = ('all', 'stable', 'reversal', 'onset', 'no_prior_observation', 'actual_returner',
    'minutes_0_300', 'minutes_300_600', 'minutes_600_1000', 'minutes_1000_plus', 'template_radial', 'template_lateral')
SOURCES = ('stable', 'reversal', 'onset', 'history_only')
KEYS = ('cell', 'record', 'role', 'receiver', 'operator', 'arm', 'metric', 'source_group', 'source_role')
UNITS = '(recorded unblocked attempts/60)^2'
LIMITATIONS = [
    'exact realized accounting conditional on selected covariances and scales; no causal attribution or classical bias–variance decomposition',
    'response-dependent noise transmission is neither independent of signal and carry nor a sampling variance',
    'one fixed native truth population and shared histories; five cells are not independent populations',
    'monte carlo intervals describe response-dependent statistics under fixed truth/design/noise; they are not player intervals',
    'source allocations depend on the frozen prior/reference convention and trace saved rows, not ultimate historical origins',
    'current-score weighting cannot identify inherited a separately from covariance, selected q and coupling',
    'same-deployment prediction retains the original fitted-context baseline and directed-hour denominator',
    'no intervention, fitted candidate, nomination, model admission or publication; entry-prior resetting remains untested',
]


def _check(checks, name, left, right):
    receipt = validate_shape_history_identity(np.asarray(left),np.asarray(right),name)
    checks.append(dict(identity=name,normalized_residual=receipt['relative_residual'],
        maximum_absolute_residual=receipt['maximum_absolute_residual'],status='verified'))


def _cohorts(source, role):
    ids = source.final_year['player_ids']
    assignments = {row['player_id']: row for row in source.prepared['assignments']
        if row['role'] == ('defense' if role == 'attempts_allowed' else role)}
    labels = {name: [] for name in RECEIVERS}
    for index, player in enumerate(ids):
        row = assignments[player]
        labels['all'].append(index)
        labels[row['trajectory']].append(index)
        if row['return_after_absence']:
            labels['actual_returner'].append(index)
        labels['template_'+row['template']].append(index)
        minutes = source.final_arrays['player_exposure'][index]/60
        bucket = ('minutes_0_300' if minutes < 300 else 'minutes_300_600' if minutes < 600 else
            'minutes_600_1000' if minutes < 1000 else 'minutes_1000_plus')
        labels[bucket].append(index)
    offset = 0 if role == 'offense' else len(ids)
    return {key: np.asarray(value, dtype=np.int64)+offset for key, value in labels.items()}


def _row(cell, record, role, receiver, arm, metric, n, value, *, operator='twelve_region_vector',
         denominator=None, source_group=None, source_role=None, units=UNITS, omitted=0, reason=None):
    require(value is None or np.isfinite(value), 'nonfinite diagnostic value')
    return dict(cell=cell, record=record, role=role, receiver=receiver, operator=operator, arm=arm,
        metric=metric, source_group=source_group, source_role=source_role, n_players=n,
        denominator=12*n if denominator is None else denominator, omitted_zero_targets=omitted,
        value=None if value is None else float(value), units=units,
        reason=reason or ('empty cohort' if not n else None))


def _record(source, cell, record, saved, checks):
    g, year = source.final_arrays, source.final_year
    H, u, rate = g['H'], g['u'], year['r']
    P, B, R = exposure_centering(u), source.basis.B, source.basis.R
    raw = AMPLITUDES[cell]*g['truth']
    truth = AMPLITUDES[cell]*g['centered_truth']
    _check(checks, f'{cell}/{record}/native_truth_centering', P@raw, truth)
    Qbar = H@(raw@B/rate)
    parts, theta, native, fitted_maps = {}, {}, {}, {}
    for arm in ('borrowing', 'independent'):
        state, indices = saved[arm], saved['current_indices'][arm]
        theta[arm] = state.Theta[indices]
        fitted_maps[arm] = rate*theta[arm]@R.T
        V = state.V[np.ix_(indices, indices)]
        union_n = len(state.player_ids)
        off = state.u@state.uncentered_Theta[:union_n]
        defense = state.u@state.uncentered_Theta[union_n:]
        _check(checks,f'{cell}/{record}/{arm}/saved_centering',
            np.vstack((state.uncentered_Theta[:union_n]-off,state.uncentered_Theta[union_n:]-defense)),state.Theta)
        _check(checks,f'{cell}/{record}/{arm}/saved_compensation',off+defense,state.centering_shift)
        m0 = saved['m0'] if arm == 'borrowing' else np.zeros_like(saved['m0'])
        parts[arm] = decompose_shape_history(H, saved['Q'], Qbar, m0, V, u, theta[arm])
        for key, value in parts[arm]['closure'].items():
            if isinstance(value, dict):
                require(all(np.isfinite(item) for item in value.values())
                    and value['relative_residual'] <= 1e-8, 'decomposition closure failed: '+key)
            else:
                require(np.isfinite(value) and value <= 1e-8, 'decomposition closure failed: '+key)
        checks.append(dict(identity=f'{cell}/{record}/{arm}/coefficient_decomposition',
            status='verified', residuals=parts[arm]['closure']))
        _check(checks, f'{cell}/{record}/{arm}/current_centering', P@theta[arm], theta[arm])
        native[arm] = {key: rate*(P@parts[arm][key])@R.T for key in
            ('signal', 'noise', 'carry_reference', 'carry_update')}
        native[arm]['carry'] = native[arm]['carry_reference']+native[arm]['carry_update']
        _check(checks, f'{cell}/{record}/{arm}/native_component_sum',
            native[arm]['signal']+native[arm]['noise']+native[arm]['carry'], fitted_maps[arm])
    _check(checks, f'{cell}/{record}/independent_zero_carry', native['independent']['carry'],
        np.zeros_like(native['independent']['carry']))
    # source means are masked before applying the same fixed selected update.
    assignments = {(row['role'], row['player_id']): row for row in source.prepared['assignments']}
    source_terms, covered = {}, np.zeros(len(saved['m0']), dtype=bool)
    n = len(year['player_ids'])
    V = saved['borrowing'].V[np.ix_(saved['current_indices']['borrowing'], saved['current_indices']['borrowing'])]
    for role_index, source_role in enumerate(ROLES):
        source_name = 'offense' if role_index == 0 else 'defense'
        no_prior = np.asarray([i+role_index*n for i, player in enumerate(year['player_ids'])
            if assignments[(source_name, player)]['trajectory'] == 'no_prior_observation'], dtype=np.int64)
        require(np.array_equal(saved['m0'][no_prior], np.zeros_like(saved['m0'][no_prior])), 'entrant personal prior mean is nonzero')
        covered[no_prior] = True
        for group in SOURCES:
            indices = np.asarray([i+role_index*n for i, player in enumerate(year['player_ids'])
                if assignments[(source_name, player)]['trajectory'] == group], dtype=np.int64)
            covered[indices] = True
            mean = np.zeros_like(saved['m0'])
            mean[indices] = saved['m0'][indices]
            carry = shape_history_carry(H, V, u, mean)
            reference = rate*(P@carry['reference'])@R.T
            update = rate*(P@carry['update'])@R.T
            source_terms[(group, source_role)] = (reference, update)
    require(covered.all(), 'source masks do not partition incoming current history')
    _check(checks, f'{cell}/{record}/source_native_sum',
        sum(a+b for a,b in source_terms.values()), native['borrowing']['carry'])
    # history-only columns of the likelihood and reference are exactly zero. the
    # fixture additionally checks this on saved union axes, without a union H.
    if source.result['purpose'] == 'fixture_exercise':
        state, previous = saved['borrowing'], saved['previous']
        current = saved['current_indices']['borrowing']
        union_n = len(state.player_ids)
        positions = {player:i for i,player in enumerate(previous.player_ids)}
        absent = set(state.player_ids)-set(year['player_ids'])
        for role_index, source_role in enumerate(ROLES):
            mean = np.zeros_like(state.Theta)
            for i, player in enumerate(state.player_ids):
                if player in absent and player in positions:
                    mean[role_index*union_n+i] = previous.Theta[role_index*len(previous.player_ids)+positions[player]]
            selected = mean[current]
            reference = (exposure_centering(state.u)@mean)[current]
            update = -state.V[np.ix_(current,current)]@(H@selected)
            _check(checks, f'{cell}/{record}/{source_role}/history_only_union', reference+update,
                np.zeros_like(reference))
    rows = []
    operators = dict(twelve_region_vector=source.geometry['W'], within_20_ft=source.geometry['near'],
        lateral_redistribution=source.geometry['lateral'])
    frozen = {(row['role'],row['cohort'],row['operator'],row['arm'],row['metric']):row
        for row in source.assessment['metric_rows'] if row['cell']==cell and row['record']==record}
    for role in ROLES:
        for receiver, selected in _cohorts(source, role).items():
            count = len(selected)
            for operator, W in operators.items():
                denominator = count*(12 if operator=='twelve_region_vector' else 1)
                recoveries = {arm:shape_recovery(fitted_maps[arm], truth, selected, W, denominator)
                    for arm in ('borrowing', 'independent')}
                values = {arm:value['mse'] for arm,value in recoveries.items()}
                values['zero'] = recoveries['borrowing']['zero_mse']
                values['paired_benefit'] = None if not count else values['independent']-values['borrowing']
                for arm,value in values.items():
                    metric = 'recovery_benefit' if arm=='paired_benefit' else operator.replace('twelve_region_vector','regional')+'_mse'
                    rows.append(_row(cell,record,role,receiver,arm,metric,count,value,operator=operator,denominator=denominator))
                if operator != 'twelve_region_vector':
                    continue
                target = (truth@W)[selected]
                norm = np.linalg.norm(target,axis=1)
                nonzero = norm>0
                for arm in ('borrowing', 'independent'):
                    value = None if not nonzero.any() else float(np.mean(np.sum(
                        recoveries[arm]['error'][nonzero]*target[nonzero],axis=1)/norm[nonzero]))
                    rows.append(_row(cell,record,role,receiver,arm,'directional_bias',count,value,
                        denominator=int(nonzero.sum()),omitted=int((~nonzero).sum()),units='recorded unblocked attempts/60',
                        reason='empty cohort' if not count else ('all regional targets exactly zero' if value is None else None)))
                region = {arm:{key:(value@W)[selected] for key,value in components.items()}
                    for arm,components in native.items()}
                errors = {arm:recoveries[arm]['error'] for arm in region}
                def inner(left,right):
                    return None if not count else float(np.sum(left*right)/denominator)
                error_sum = errors['borrowing']+errors['independent']
                changes = dict(loss_change=None if not count else values['borrowing']-values['independent'],
                    signal_allocation=inner(region['borrowing']['signal']-region['independent']['signal'],error_sum),
                    noise_allocation=inner(region['borrowing']['noise']-region['independent']['noise'],error_sum),
                    carry_allocation=inner(region['borrowing']['carry'],error_sum))
                if count:
                    _check(checks,f'{cell}/{record}/{role}/{receiver}/signed_sum',changes['loss_change'],
                        sum(changes[name] for name in ('signal_allocation','noise_allocation','carry_allocation')))
                for metric,value in changes.items():
                    rows.append(_row(cell,record,role,receiver,'paired_change',metric,count,value))
                if receiver=='no_prior_observation':
                    entrant_channels = {}
                    for metric,component in (('reference_carry_allocation','carry_reference'),('update_carry_allocation','carry_update')):
                        entrant_channels[metric] = inner(region['borrowing'][component],error_sum)
                        rows.append(_row(cell,record,role,receiver,'paired_change',metric,count,entrant_channels[metric]))
                    if count:
                        _check(checks,f'{cell}/{record}/{role}/entrant_channel_sum',
                            sum(entrant_channels.values()),changes['carry_allocation'])
                for arm in region:
                    a,noise,carry = region[arm]['signal']-target,region[arm]['noise'],region[arm]['carry']
                    quadratic = dict(signal_error_square=inner(a,a),noise_square=inner(noise,noise),carry_square=inner(carry,carry),
                        signal_noise_cross=None if not count else 2*inner(a,noise),
                        signal_carry_cross=None if not count else 2*inner(a,carry),
                        noise_carry_cross=None if not count else 2*inner(noise,carry))
                    if count:
                        _check(checks,f'{cell}/{record}/{role}/{receiver}/{arm}/quadratic_sum',sum(quadratic.values()),values[arm])
                    for metric,value in quadratic.items():
                        rows.append(_row(cell,record,role,receiver,arm,metric,count,value))
                allocations = []
                for (group,source_role),(reference,update) in source_terms.items():
                    value = inner(((reference+update)@W)[selected],error_sum)
                    allocations.append(value)
                    rows.append(_row(cell,record,role,receiver,'paired_change','source_carry_allocation',count,value,
                        source_group=group,source_role=source_role))
                    if receiver=='no_prior_observation':
                        split = []
                        for metric,component in (('reference_carry_allocation',reference),('update_carry_allocation',update)):
                            channel_value = inner((component@W)[selected],error_sum)
                            split.append(channel_value)
                            rows.append(_row(cell,record,role,receiver,'paired_change',metric,count,
                                channel_value,source_group=group,source_role=source_role))
                        if count:
                            _check(checks,f'{cell}/{record}/{role}/{group}/{source_role}/entrant_source_channel_sum',sum(split),value)
                if count:
                    _check(checks,f'{cell}/{record}/{role}/{receiver}/source_signed_sum',sum(allocations),changes['carry_allocation'])
    hours = float(g['stratum_weight'].sum()/rate)
    prediction = {arm:same_deployment_excess(H,rate,hours,theta[arm],raw,B) for arm in theta}
    prediction.update(zero=0.,paired_cost=prediction['borrowing']-prediction['independent'])
    for arm,value in prediction.items():
        rows.append(_row(cell,record,'both','all',arm,'prediction_cost' if arm=='paired_cost' else 'prediction_excess',
            2*n,value,operator='same_deployment',denominator=hours))
    compared = 0
    for row in rows:
        key = tuple(row[name] for name in ('role','receiver','operator','arm','metric'))
        if key not in frozen:
            continue
        original = frozen[key]
        require(all(row[name]==original[name] for name in ('n_players','denominator','units','reason'))
            and row['omitted_zero_targets']==original.get('omitted_zero_targets',0), 'frozen recovery metadata differs')
        if row['value'] is None:
            require(original['value'] is None,'frozen unavailable value differs')
        else:
            _check(checks,f'{cell}/{record}/frozen/{"/".join(key)}',row['value'],original['value'])
        compared += 1
    require(compared==len(frozen),'frozen recovery/prediction inventory differs')
    return rows


def _summaries(rows, records):
    groups = {}
    for row in rows:
        key = tuple(row[name] for name in KEYS if name!='record')
        groups.setdefault(key,[]).append(row)
    result = []
    for key, values in groups.items():
        require(sorted(row['record'] for row in values)==list(records), 'summary record inventory differs')
        require(all(all(row[name]==values[0][name] for name in
            ('n_players','denominator','omitted_zero_targets','units','reason')) for row in values), 'fixed denominator/availability differs')
        common = {name:values[0][name] for name in values[0] if name not in ('record','value')}
        common.update(n_records=len(records),summary_key=json.dumps(key,separators=(',',':')))
        numbers = [row['value'] for row in values]
        if numbers[0] is None:
            require(all(value is None for value in numbers),'partial missing summary')
            result.append(dict(common,mean=None,sd=None,mc_se=None,ci_low=None,ci_high=None))
            continue
        require(all(value is not None and np.isfinite(value) for value in numbers),'nonfinite summary inputs')
        mean = float(np.mean(numbers))
        sd = float(np.std(numbers,ddof=1))
        se = sd/np.sqrt(len(records))
        margin = float(t.ppf(.975,len(records)-1)*se)
        result.append(dict(common,mean=mean,sd=sd,mc_se=se,ci_low=mean-margin,ci_high=mean+margin))
    # rms is a transform of the mean mse; its dispersion remains explicitly mse dispersion.
    for row in list(result):
        if row['metric']=='regional_mse':
            rms = dict(row,metric='regional_rms',units='recorded unblocked attempts/60',sd=None,mc_se=None,
                source_mse_sd=row['sd'],source_mse_mc_se=row['mc_se'],
                reason=row['reason'] or 'rms is sqrt(mean mse); sd and mc_se belong to the source mse')
            for name in ('mean','ci_low','ci_high'):
                rms[name] = None if row[name] is None else float(np.sqrt(max(0.,row[name])))
            rms['summary_key'] = json.dumps(tuple(rms[name] for name in KEYS if name!='record'),separators=(',',':'))
            result.append(rms)
    return result


def _validate_saved(rows, summaries, records, checks):
    require(len({tuple(row[name] for name in KEYS) for row in rows})==len(rows),'duplicate record key')
    require(len({row['summary_key'] for row in summaries})==len(summaries),'duplicate summary key')
    regional = {}
    for row in rows:
        if row['operator']=='twelve_region_vector':
            regional.setdefault(tuple(row[name] for name in ('cell','record','role','receiver')),[]).append(row)
    for group, values in regional.items():
        index = {(row['arm'],row['metric'],row['source_group'],row['source_role']):row['value'] for row in values}
        if not values[0]['n_players']:
            require(all(row['value'] is None for row in values),'empty receiver has saved numeric value')
            continue
        def value(arm,metric,source_group=None,source_role=None):
            return index[(arm,metric,source_group,source_role)]
        prefix = 'saved/'+str(group)
        loss = value('paired_change','loss_change')
        _check(checks,prefix+'/loss',loss,value('borrowing','regional_mse')-value('independent','regional_mse'))
        _check(checks,prefix+'/signed',loss,sum(value('paired_change',metric) for metric in
            ('signal_allocation','noise_allocation','carry_allocation')))
        for arm in ('borrowing','independent'):
            _check(checks,prefix+'/'+arm+'/quadratic',value(arm,'regional_mse'),sum(value(arm,metric) for metric in
                ('signal_error_square','noise_square','carry_square','signal_noise_cross','signal_carry_cross','noise_carry_cross')))
        _check(checks,prefix+'/source',value('paired_change','carry_allocation'),sum(
            value('paired_change','source_carry_allocation',source_group,source_role)
            for source_group in SOURCES for source_role in ROLES))
        if group[-1]=='no_prior_observation':
            channels = ('reference_carry_allocation','update_carry_allocation')
            _check(checks,prefix+'/entry',value('paired_change','carry_allocation'),sum(value('paired_change',metric) for metric in channels))
            for metric in channels:
                _check(checks,prefix+'/'+metric,value('paired_change',metric),sum(
                    value('paired_change',metric,source_group,source_role) for source_group in SOURCES for source_role in ROLES))
            for source_group in SOURCES:
                for source_role in ROLES:
                    _check(checks,prefix+'/'+source_group+'/'+source_role+'/entry',
                        value('paired_change','source_carry_allocation',source_group,source_role),
                        sum(value('paired_change',metric,source_group,source_role) for metric in channels))
    grouped = {}
    for row in rows:
        grouped.setdefault(tuple(row[name] for name in KEYS if name!='record'),[]).append(row)
    summary_index = {tuple(row[name] for name in KEYS if name!='record'):row for row in summaries}
    for summary in summaries:
        if summary['metric']=='regional_rms':
            source_key = tuple('regional_mse' if name=='metric' else summary[name] for name in KEYS if name!='record')
            mse = summary_index[source_key]
            require(summary['sd'] is None and summary['mc_se'] is None,'rms dispersion must stay labeled as mse')
            for name in ('mean','ci_low','ci_high'):
                if mse[name] is None:
                    require(summary[name] is None,'missing rms summary differs')
                else:
                    _check(checks,'rms/'+summary['summary_key']+'/'+name,summary[name],max(0.,mse[name])**.5)
            for name,source_name in (('source_mse_sd','sd'),('source_mse_mc_se','mc_se')):
                if mse[source_name] is None:
                    require(summary[name] is None,'missing rms mse dispersion differs')
                else:
                    _check(checks,'rms/'+summary['summary_key']+'/'+name,summary[name],mse[source_name])
            continue
        selected = grouped[tuple(summary[name] for name in KEYS if name!='record')]
        require(len(selected)==len(records),'saved summary inventory differs')
        if summary['mean'] is None:
            require(all(row['value'] is None for row in selected),'saved missing summary differs')
            continue
        numbers = [row['value'] for row in selected]
        mean = sum(numbers)/len(numbers)
        sd = (sum((value-mean)**2 for value in numbers)/(len(numbers)-1))**.5
        se = sd/len(numbers)**.5
        margin = float(t.ppf(.975,len(numbers)-1))*se
        _check(checks,'summary/'+summary['summary_key'],
            [summary[name] for name in ('mean','sd','mc_se','ci_low','ci_high')], [mean,sd,se,mean-margin,mean+margin])



def _answer(summaries, purpose):
    if purpose=='fixture_exercise':
        return 'the detached fixture verifies software accounting only; it supplies no scientific diagnosis or next hypothesis'
    index = {tuple(row[name] for name in ('cell','role','receiver','arm','metric')):row for row in summaries
        if row['operator']=='twelve_region_vector' and row['source_group'] is None and row['source_role'] is None}
    clauses = [
        'under the frozen symmetric allocation, base stable-player gains and reversal harm accompany '
        'the largest absolute mean historical-carry terms in both roles. base first-observation harm '
        'instead accompanies changed current-signal weighting, offset by realized noise and with small net carry. '
        'under null truth, signal is exactly zero while mean noise and carry allocations are positive. '
        'these are signed realized allocations under the saved convention, not identified causes or evidence '
        'that resetting entry variance would help.'
    ]
    for role in ROLES:
        for cell, receiver in [('gaussian_base',name) for name in ('stable','reversal','onset','no_prior_observation')]+[('gaussian_null','all')]:
            values = [index[(cell,role,receiver,'paired_change',metric)]['mean'] for metric in
                ('loss_change','signal_allocation','noise_allocation','carry_allocation')]
            labels = ('signal','noise','carry')
            largest = labels[int(np.argmax(np.abs(values[1:])))]
            directions = ', '.join(label+(' toward harm' if value>0 else ' toward benefit' if value<0 else ' exactly zero')
                for label,value in zip(labels,values[1:],strict=True))
            clauses.append(f"{cell}, {role}, {receiver}: mean paired mse change {values[0]:.6g}; "
                f"symmetric signal/noise/carry allocations {values[1]:.6g}, {values[2]:.6g}, {values[3]:.6g}. "
                f"the largest absolute mean allocation is {largest}; {directions}.")
    clauses.append('positive means borrowing harm, in squared recorded unblocked attempts/60. '
        'signed terms interact and retain response-dependent selection; these exact realized accounts do not identify an intervention. '
        'the actionable remedy remains unresolved; no next hypothesis is assigned.')
    return '\n\n'.join(clauses)


def _closure_summary(checks):
    decompositions = [check['residuals'] for check in checks if 'residuals' in check]
    return dict(check_count=len(checks),coefficient_decompositions=len(decompositions),
        maximum_normalized_residual=max((check.get('normalized_residual',0.) for check in checks),default=0.),
        maximum_coefficient_mean_relative_residual=max((row['saved_mean']['relative_residual'] for row in decompositions),default=0.),
        maximum_coefficient_mean_absolute_residual=max((row['saved_mean']['maximum_absolute_residual'] for row in decompositions),default=0.),
        maximum_gauge_relative_residual=max((value for row in decompositions for key,value in row.items()
            if key.endswith('gauge_relative_residual')),default=0.),
        maximum_covariance_centering_relative_residual=max((row['covariance_centering_relative_residual'] for row in decompositions),default=0.),
        status='verified')


def diagnose(history_result, output):
    started, process_started = time.monotonic(), time.process_time()
    source = read_history_source_slice(Path(history_result).absolute())
    purpose = source.result['purpose']
    root = output_path(str(output),[str(Path(ref['path']).parent) for ref in source.consumed.values()])
    if purpose=='research':
        require(root.is_relative_to(RESEARCH_ROOT) and root.relative_to(RESEARCH_ROOT).parts[0].startswith('attribution-04l-'),
            'research requires a new external attribution-04l directory')
    require(tuple(source.cells)==CELLS,'diagnosis cell inventory differs')
    root.mkdir()
    with (root/'spec.md').open('xb') as destination:
        destination.write(SPEC.read_bytes())
    protocol = artifact('attribution_prior_protocol',purpose,source.consumed,schema_version=1,
        spec=identity(SPEC),spec_snapshot=identity(root/'spec.md'),cells=list(source.cells),records=list(source.records),
        selected_pairs=[dict(cell=cell,record=record,manifest=ref,archive=source.fit_metadata[(cell,record)]['arrays'])
            for (cell,record),ref in source.fits.items()],
        receiver_order=list(RECEIVERS),source_groups=list(SOURCES),source_roles=list(ROLES),
        receiver_masks={role:{name:indices.tolist() for name,indices in _cohorts(source,role).items()} for role in ROLES},
        axes=dict(roles=list(ROLES),player_ids=source.final_year['player_ids'],coefficient_columns=40,
            regional_columns=12,region_names=source.prepared['region_names'],season=source.final_year['season']),units=dict(maps='recorded unblocked attempts/60',loss=UNITS),
        member_allowlist=dict(geometry=['B','p','eigenvalues','W','near','lateral',
            'final:H,u,p,truth,centered_truth,stratum_weight,player_exposure'],
            final=['Theta','V','uncentered_Theta','centering_shift','u'],previous=['Theta'],score=['final:Q']),
        equations=dict(signal='V Qbar',noise='V (Q-Qbar)',reference='P m0',update='-V (H m0)',
            allocation='<component_b-component_i,e_b+e_i>',target='full native physical truth'),
        interval='mean +/- t_.975,N-1 * sample_sd/sqrt(N); records are independent units',
        centering='final-current exposure reference; relative-rate carry without rate rescaling',
        source_masks={role:{group:[row['player_id'] for row in source.prepared['assignments']
            if row['role']==('defense' if role=='attempts_allowed' else role) and
            ((not row['current']) if group=='history_only' else (row['current'] and row['trajectory']==group))]
            for group in SOURCES} for role in ROLES},
        no_prior_source_ids={role:[row['player_id'] for row in source.prepared['assignments']
            if row['role']==('defense' if role=='attempts_allowed' else role)
            and row['current'] and row['trajectory']=='no_prior_observation'] for role in ROLES},
        source_allocation='eight disjoint final stable/reversal/onset/history-only by role; no-prior personal mean zero')
    write_json(root/'protocol.json',json_values(protocol))
    protocol_ref = identity(root/'protocol.json')
    rows, scales, checks = [], [], []
    pairs = [('gaussian_base',0)]+[(cell,record) for cell in source.cells for record in source.records if (cell,record)!=('gaussian_base',0)]
    preflight = None
    for cell,record in pairs:
        pair_started = time.monotonic()
        before = json_values(source.read_accounting)
        saved = read_history_final_record(source,cell,record)
        rows.extend(_record(source,cell,record,saved,checks))
        scales.extend(saved['scales'])
        if (cell,record)==('gaussian_base',0):
            preflight = dict(**resources(pair_started),read_accounting_before=before,
                read_accounting_after=json_values(source.read_accounting),included_in_inventory=True)
        print(f'{cell}/{record}: verified saved-fit accounting',file=sys.stderr,flush=True)
        del saved
    expected_pairs = 100 if purpose=='research' else 10
    expected_scales = 600 if purpose=='research' else 40
    require(len(pairs)==expected_pairs and len(scales)==expected_scales,'finite diagnosis inventory differs')
    require(len({(row['cell'],row['record'],row['state_index']) for row in scales})==len(scales), 'duplicate scale receipt')
    summaries = _summaries(rows,source.records)
    _validate_saved(rows,summaries,source.records,checks)
    frozen_summaries = {(row['cell'],row['role'],row['cohort'],row['operator'],row['arm'],row['metric']):row
        for row in source.assessment['comparison_rows']}
    frozen_omissions = {}
    for original in source.assessment['metric_rows']:
        omitted_key = tuple(original[name] for name in ('cell','role','cohort','operator','arm','metric'))
        frozen_omissions.setdefault(omitted_key,set()).add(original.get('omitted_zero_targets',0))
    require(all(len(values)==1 for values in frozen_omissions.values()),'frozen zero-target omissions change across records')
    compared = 0
    for row in summaries:
        key = tuple(row[name] for name in ('cell','role','receiver','operator','arm','metric'))
        if key in frozen_summaries:
            old = frozen_summaries[key]
            require(all(row[name]==old[name] for name in ('n_records','n_players','denominator','units','reason'))
                and row['omitted_zero_targets'] in frozen_omissions[key[:-1]+('regional_mse',) if row['metric']=='regional_rms' else key],
                'frozen summary metadata differs')
            for name in ('mean','sd','mc_se','ci_low','ci_high') + (('source_mse_sd','source_mse_mc_se') if row['metric']=='regional_rms' else ()):
                if row[name] is None: require(old[name] is None,'frozen missing summary differs')
                else: _check(checks,'frozen_summary/'+row['summary_key']+'/'+name,row[name],old[name])
            compared += 1
    require(compared==len(frozen_summaries),'frozen summary inventory differs')
    decision = dict(next_hypothesis=None,unresolved_reason=None if purpose=='fixture_exercise' else 'mechanism_interaction_unresolved')
    inventory = dict(pairs=len(pairs),scores=len(pairs),decompositions=2*len(pairs),previous_means=len(pairs),
        scales=len(scales),record_rows=len(rows),summary_rows=len(summaries),frozen_comparisons=len(source.assessment['metric_rows']),
        frozen_summaries=compared)
    cost = dict(**resources(started),process_seconds=time.process_time()-process_started,
        research_solves=0,scale_evaluations=0,measurement_scope='source reads and numerical checks; before diagnosis serialization')
    diagnosis = artifact('attribution_prior_diagnosis',purpose,dict(protocol=protocol_ref),schema_version=1,
        execution_status='complete',numerical_status='verified',
        study_status='fixture_verified' if purpose=='fixture_exercise' else 'diagnosed',
        inventory=inventory,read_accounting=source.read_accounting,checks=checks,closure_summary=_closure_summary(checks),
        diagnostic_answer=_answer(summaries,purpose),record_rows=rows,summary_rows=summaries,
        scale_rows=scales,decision=decision,limitations=LIMITATIONS,preflight_resources=preflight,resources=cost)
    write_json(root/'diagnosis.json',json_values(diagnosis))
    result = artifact('attribution_prior_result',purpose,dict(protocol=protocol_ref,diagnosis=identity(root/'diagnosis.json')),
        schema_version=1,execution_status='complete',numerical_status='verified',
        study_status=diagnosis['study_status'],inventory=inventory,**decision,nomination=None,admission='not_admitted',
        handoff=None,resources=dict(cost,**resources(started),process_seconds=time.process_time()-process_started,measurement_scope='through diagnosis serialization; before result serialization'))
    write_json(root/'result.json',json_values(result))
    return identity(root/'result.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    diagnosis_parser = sub.add_parser('diagnose')
    diagnosis_parser.add_argument('--history-result',required=True)
    diagnosis_parser.add_argument('--output',required=True)
    report_parser = sub.add_parser('report')
    report_parser.add_argument('--diagnosis',required=True)
    report_parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    try:
        if args.command=='diagnose': result = diagnose(args.history_result,args.output)
        else:
            from attribution_priors_report import render
            result = render(Path(args.diagnosis),Path(args.output))
    except (InputContractError,OSError,ValueError,KeyError,TypeError) as error:
        print(str(error),file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
