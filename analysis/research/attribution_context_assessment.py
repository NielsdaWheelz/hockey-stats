"""04o's fixed paired assessment, player sensitivity and saved evidence boundary."""

from itertools import product
from pathlib import Path
import time

import numpy as np

from hockey_stats.artifacts import artifact, json_values, linked_path, require, resources, write_arrays, write_json
from hockey_stats.attribution_prediction import (complete_paired_decomposition, complete_prediction,
    context_complete_prediction, embed_constant_prediction, continuous_rate_diagnostics,
    context_prediction_row_batches, empirical_residuals)
from hockey_stats.paired_evaluation import paired_samples, paired_ratio_intervals
from hockey_stats.chance_cli import identity

ARMS = ('candidate','control')
SCHEMES = ('games','calendar_7_day','calendar_14_day')
COMPONENTS = (('control','volume'),('control','shape'),('candidate','volume'),('candidate','shape'))
UNITS = '(recorded unblocked attempts/60)^2'


def direction(intervals):
    require(len(intervals) == 3, 'context direction requires three interval schemes')
    if all(v is not None and v[1] < 0 for v in intervals): return 'supported_lower_loss'
    if all(v is not None and v[0] > 0 for v in intervals): return 'supported_higher_loss'
    return 'unresolved'


def metric_axes(names):
    return ([('regional','all',v,12.) for v in ('complete','weighted_volume','shape','interaction')]
        + [('regional',name,'complete',1.) for name in names]
        + [('native_inverse_share','all',v,1.) for v in ('complete','weighted_volume','shape','interaction')]
        + [('volume','all','volume',1.)])


def _losses(game, predictions, regions):
    value = complete_paired_decomposition(game,predictions['candidate'],predictions['control'],regions)
    return np.r_[[value['regional'][k] for k in ('complete','weighted_volume','shape','interaction')],
        value['regional']['region_numerators'],
        [value['native_inverse_share'][k] for k in ('complete','weighted_volume','shape','interaction')],
        value['volume']]


def assess_games(games, alternatives, regions, names, *, support=None):
    """one sparse contraction per variant/game; every ratio uses common saved draws."""
    variants = ('primary',*(f'probe_{i:04b}' for i in range(1,16)))
    require(set(alternatives) == set(variants) and all(set(a) == set(ARMS) for a in alternatives.values())
            and regions.ndim == 2 and regions.shape[1] == len(names) == 12,
            'context assessment requires sixteen variants, both arms and twelve regions')
    metrics=metric_axes(names); values=[]; dates=[]; hours=[]; ledger=[]; ids=[]
    player_hours=None; seen=set(); month_rows=[]; player_residuals=None; mean_rows=[]
    for game in games:
        require(game['game_id'] not in seen and game['partition'] in ('training','assessment'),
                'context game inventory or partition differs')
        seen.add(game['game_id'])
        exposure=float(game['directed_hours']); counts=float(game['N'][:len(game['E'])].sum())
        require(np.isfinite(exposure) and exposure >= 0 and np.isfinite(counts) and counts >= 0,
                'context game counts or hours are invalid')
        row=dict(game_id=game['game_id'],game_date=game['date'],partition=game['partition'],
            directed_hours=exposure,retained_recorded_unblocked_attempts=counts,
            coverage=game['coverage'],source_identity=game['source_identity'],
            reason='training game; excluded from assessment' if game['partition']=='training' else
                   'zero retained directed exposure' if exposure == 0 else None)
        ledger.append(row)
        if game['partition']=='training': continue
        v=np.asarray([_losses(game,alternatives[variant],regions) for variant in variants])
        require(np.allclose(v[:,0],v[:,1:4].sum(axis=1),rtol=1e-8,atol=1e-10)
                and np.allclose(v[:,16],v[:,17:20].sum(axis=1),rtol=1e-8,atol=1e-10),
                'context component loss accounting differs')
        if exposure == 0:
            require(counts == 0 and not np.any(v), 'zero-time context game contains counts or loss')
        values.append(v);dates.append(game['date']);hours.append(exposure);ids.append(game['game_id'])
        if player_hours is None: player_hours=np.zeros(game['A'].shape[0])
        require(player_hours.shape == (game['A'].shape[0],), 'context player axes changed')
        player_hours+=game['A'].diagonal()
        if support is not None:
            require(set(support) == set(game['player_ids']), 'context support ids differ')
            if player_residuals is None:
                player_residuals=np.zeros((2,len(player_hours),12))
            for ai,arm in enumerate(ARMS):
                residual=empirical_residuals(game,alternatives['primary'][arm],response='complete',operator=regions)
                player_residuals[ai]+=residual['player_residual_sum']
                for ri,name in enumerate(names):
                    mean_rows.append(dict(record_type='game_mean_complete',game_id=game['game_id'],game_date=game['date'],
                        arm=arm,region=name,directed_hours=exposure,
                        observed=float(residual['observed_sum'][ri]/exposure) if exposure else None,
                        predicted=float(residual['predicted_sum'][ri]/exposure) if exposure else None,
                        signed_residual=float(residual['residual_sum'][ri]/exposure) if exposure else None,
                        reason=None if exposure else 'zero directed exposure'))
        for mi,(metric,region,component,_) in enumerate(metrics):
            row[f'{metric}:{region}:{component}:loss_numerator']=float(v[0,mi])
    require(bool(hours) and sum(hours)>0,'context assessment has no positive exposure')
    values=np.asarray(values); hours=np.asarray(hours); norms=np.asarray([m[3] for m in metrics])
    denominators=np.broadcast_to(hours[:,None,None]*norms,values.shape)
    samples=paired_samples(dates,404130)
    schemes=paired_ratio_intervals(values.reshape(len(hours),-1),denominators.reshape(len(hours),-1),
                                  dates,404130,samples=samples)
    comparisons=[]; directions={}; closure={}
    for vi,variant in enumerate(variants):
        for mi,(metric,region,component,normalizer) in enumerate(metrics):
            index=vi*len(metrics)+mi
            intervals=[schemes[s]['interval'][index] for s in SCHEMES]
            intervals=[v.tolist() if np.isfinite(v).all() else None for v in intervals]
            label=direction(intervals);directions[variant,metric,region,component]=label
            for scheme,interval in zip(SCHEMES,intervals,strict=True):
                comparisons.append(dict(variant=variant,contrast='candidate-control',metric=metric,region=region,
                    component=component,loss_numerator=float(values[:,vi,mi].sum()),directed_hours=float(hours.sum()),
                    metric_normalizer=normalizer,loss_denominator=float(normalizer*hours.sum()),
                    estimate=float(values[:,vi,mi].sum()/(normalizer*hours.sum())),scheme=scheme,
                    lower=None if interval is None else interval[0],upper=None if interval is None else interval[1],
                    undefined_draws=int(schemes[scheme]['undefined_draws'][index]),direction=label,
                    reason=schemes[scheme]['missing_reason'][index],units=UNITS))
    for scheme,result in schemes.items():
        draws=result['draws'].reshape(2000,16,len(metrics));valid=np.isfinite(draws).all(axis=(1,2))
        selected=draws[valid]
        regional=float(np.max(np.abs(selected[:,:,0]-selected[:,:,1:4].sum(axis=2)))) if valid.any() else None
        native=float(np.max(np.abs(selected[:,:,16]-selected[:,:,17:20].sum(axis=2)))) if valid.any() else None
        require(not valid.any() or (np.allclose(selected[:,:,0],selected[:,:,1:4].sum(axis=2),rtol=1e-8,atol=1e-10)
                and np.allclose(selected[:,:,16],selected[:,:,17:20].sum(axis=2),rtol=1e-8,atol=1e-10)),
                'shared context draw component accounting differs')
        closure[scheme]=dict(regional_max_absolute=regional,native_max_absolute=native,
            valid_draws=int(valid.sum()),selected_units=samples[scheme]['samples'].shape[1])
    for month in sorted({d[:7] for d in dates}):
        selected=np.array([d.startswith(month) for d in dates]);total=float(hours[selected].sum())
        for mi,(metric,region,component,normalizer) in enumerate(metrics):
            numerator=float(values[selected,0,mi].sum())
            month_rows.append(dict(record_type='calendar_month',month=month,metric=metric,region=region,
                component=component,game_count=int(selected.sum()),directed_hours=total,
                loss_numerator=numerator,metric_normalizer=normalizer,
                estimate=numerator/(normalizer*total) if total else None,
                reason=None if total else 'zero directed exposure',units=UNITS))
    support_rows=[]
    if support is not None:
        ids_axis=alternatives['primary']['candidate']['player_ids'];n=len(ids_axis)
        for role_index,role in enumerate(('offense','defense')):
            for group in ('current_training','carried_only','new_to_fit','first_in_corpus_final'):
                chosen=np.array([support[p]['first_in_corpus_final'] if group=='first_in_corpus_final'
                                 else support[p]['group']==group for p in ids_axis])
                indices=np.flatnonzero(chosen & (player_hours[role_index*n:(role_index+1)*n]>0))+role_index*n
                total=float(player_hours[indices].sum())
                for ai,arm in enumerate(ARMS):
                    for ri,name in enumerate(names):
                        numerator=float(player_residuals[ai,indices,ri].sum())
                        support_rows.append(dict(record_type='support_signed_residual',role=role,support_group=group,
                            arm=arm,region=name,member_count=len(indices),on_ice_hours=total,
                            signed_residual_sum=numerator,signed_residual_rate=numerator/total if total else None,
                            participation_overlaps=True,interpretation='descriptive on-ice association; not subgroup accuracy',
                            reason=None if total else 'zero on-ice hours'))
    primary=directions['primary','regional','all','complete']
    stable=all(directions[v,'regional','all','complete']==primary for v in variants)
    arrays=dict(game_ids=np.asarray(ids,dtype=np.int64),directed_hours=hours,loss_numerators=values)
    for scheme,unit in samples.items():
        arrays[scheme+'_samples']=unit['samples']
        if unit['blocks'] is not None: arrays[scheme+'_blocks']=unit['blocks']
    return dict(comparison_rows=comparisons,game_rows=ledger,month_rows=month_rows,support_rows=support_rows,mean_rows=mean_rows,
        primary_direction=primary,primary_direction_stable=stable,draw_closure=closure,
        metric_axes=[dict(metric=m,region=r,component=c,normalizer=n,units=UNITS) for m,r,c,n in metrics],
        variant_axes=list(variants),assessment_game_ids=ids,assessment_directed_hours=float(hours.sum()),
        conditional_uncertainty='fixed fits, selected scales, split, source population and working criterion'),arrays,player_hours


def player_sensitivities(training, states, reference_ids, regions, heldout_hours):
    """common-reference centered point changes; prior-only rows remain separate evidence."""
    ids=tuple(reference_ids); current=tuple(training.player_ids); n=len(ids)
    require(len(ids)==len(set(ids)) and set(current).issubset(ids) and heldout_hours.shape==(2*n,),
            'player sensitivity reference population differs')
    current_positions={p:i for i,p in enumerate(current)}
    outputs={}; groups={}
    for arm in ARMS:
        volume,shape=states[arm,'volume'],states[arm,'shape']
        require(volume.player_ids==shape.player_ids and volume.current_player_ids==shape.current_player_ids==current
                and np.array_equal(volume.u,shape.u) and volume.r==shape.r==training.r,
                'sensitivity state common reference differs')
        positions={p:i for i,p in enumerate(volume.player_ids)}; ns=len(positions)
        fields=[]
        for role in range(2):
            vshift=volume.u @ volume.uncentered_beta[role*ns:(role+1)*ns]
            hshift=shape.u @ shape.uncentered_Theta[role*ns:(role+1)*ns]
            v=np.asarray([volume.uncentered_beta[role*ns+positions[p]]-vshift if p in positions else -vshift for p in ids])
            h=np.asarray([shape.uncentered_Theta[role*ns+positions[p]]-hshift if p in positions else -hshift for p in ids])
            fields.append((training.r*v.ravel(),training.r*(v*training.p+h @ training.basis.R.T) @ regions))
        outputs[arm]=fields
        groups[arm]=['current' if p in current_positions else 'carried_only' if p in positions else 'unseen' for p in ids]
    require(groups['candidate']==groups['control'],'candidate/control evidence groups differ')
    rows=[]; summaries=[]
    for role_index,role in enumerate(('offense','defense')):
        scalar=outputs['candidate'][role_index][0]-outputs['control'][role_index][0]
        regional=outputs['candidate'][role_index][1]-outputs['control'][role_index][1]
        size=np.sqrt(np.mean(regional**2,axis=1))
        for i,p in enumerate(ids):
            minutes=float(training.player_exposure[current_positions[p]]/60) if p in current_positions else 0.
            row=dict(player_id=p,role=role,evidence_status=groups['candidate'][i],training_included_minutes=minutes,
                heldout_included_minutes=float(heldout_hours[role_index*n+i]*60),
                candidate_scalar=float(outputs['candidate'][role_index][0][i]),
                control_scalar=float(outputs['control'][role_index][0][i]),scalar_change=float(scalar[i]),
                regional_change_size=float(size[i]),scalar_practical_yardstick=.05*training.r,
                units='recorded unblocked attempts/60',positive_defense='more attempts allowed')
            for j in range(12):
                row[f'candidate_region_{j}']=float(outputs['candidate'][role_index][1][i,j])
                row[f'control_region_{j}']=float(outputs['control'][role_index][1][i,j])
                row[f'region_change_{j}']=float(regional[i,j])
            rows.append(row)
        chosen=np.asarray([ids.index(p) for p in current]);w=np.asarray(training.u)
        require(w.shape==(len(current),) and np.isclose(w.sum(),1.),'sensitivity training exposure weights differ')
        for name,values in (('absolute_scalar_change',np.abs(scalar[chosen])),('regional_change_size',size[chosen])):
            summaries.append(dict(role=role,metric=name,evidence_status='current',players=len(chosen),
                exposure_weighted_rms=float(np.sqrt(w @ values**2)),median=float(np.median(values)),
                p90=float(np.percentile(values,90,method='linear')),maximum=float(values.max()),
                units='recorded unblocked attempts/60'))
    return rows,summaries


def _control_compatibility(population, training, metadata, regions, names, shared_samples):
    """zero-temporal embedding reproduces the old three fixed comparisons."""
    from hockey_stats.attribution_context import TEMPORAL_IDS, context_game_moments
    from hockey_stats.attribution_data import decode_coefficient_state, empirical_game_moments

    ids=population.references.player_ids; fit=metadata['controls_fit']; frozen=metadata['controls_assessment']
    selected={(row['arm'],row['component']):decode_coefficient_state(row,row['component'])
              for row in fit['states'] if row['index'] in (4,5)}
    coarse={arm:complete_prediction(training.coarse_training,selected[arm,'volume'],selected[arm,'shape'],ids)
            for arm in ('borrowing','independent')}
    coarse['context']=complete_prediction(training.coarse_training,None,None,ids)
    embedded={arm:embed_constant_prediction(p,TEMPORAL_IDS) for arm,p in coarse.items()}
    saved={row['game_id']:row for row in frozen.get('game_rows',[]) if row['partition']=='assessment'}
    require(set(saved)==set(metadata['assessment_ids']) and bool(frozen.get('comparison_rows')),
            'control compatibility requires complete frozen game and interval anchors')
    maxima={}; entries=0; replay_values=[];dates=[];hours=[]
    for game_id in metadata['assessment_ids']:
        old=empirical_game_moments(population.grouped,population.references,game_id)
        new=context_game_moments(population,training,game_id)
        game_values=[]
        for left,right in (('borrowing','independent'),('borrowing','context'),('independent','context')):
            original=_losses(old,dict(candidate=coarse[left],control=coarse[right]),regions)
            actual=_losses(new,dict(candidate=embedded[left],control=embedded[right]),regions)
            require(np.allclose(actual,original,rtol=1e-8,atol=1e-10),
                    'zero-temporal control loss differs from old coarse prediction')
            maxima['coarse_embedding']=max(maxima.get('coarse_embedding',0.),float(np.max(np.abs(actual-original))))
            if saved:
                expected=np.asarray([saved[game_id][f'{left}-{right}:{m}:{r}:{c}:loss_numerator']
                                     for m,r,c,_ in metric_axes(names)])
                require(np.allclose(actual,expected,rtol=1e-8,atol=1e-10),
                        'embedded control comparison differs from frozen 04n ledger')
                maxima['frozen_04n_ledger']=max(maxima.get('frozen_04n_ledger',0.),float(np.max(np.abs(actual-expected))))
            game_values.append(actual);entries+=len(actual)
        replay_values.append(game_values);dates.append(saved[game_id]['game_date']);hours.append(new['directed_hours'])
    replay_values=np.asarray(replay_values);hours=np.asarray(hours)
    metrics=metric_axes(names);normalizers=np.asarray([m[3] for m in metrics])
    denominator=np.broadcast_to(hours[:,None,None]*normalizers,replay_values.shape)
    schemes=paired_ratio_intervals(replay_values.reshape(len(hours),-1),denominator.reshape(len(hours),-1),
        dates,404130,samples=shared_samples)
    anchors={(r['contrast'],r['metric'],r['region'],r['component'],r['scheme']):r
        for r in frozen['comparison_rows'] if r['comparison']=='main'}
    contrasts=('borrowing-independent','borrowing-context','independent-context')
    require(len(anchors)==3*len(metrics)*3,'frozen control interval anchor inventory differs')
    for ci,contrast in enumerate(contrasts):
        for mi,(metric,region,component,_) in enumerate(metrics):
            for scheme in SCHEMES:
                anchor=anchors[contrast,metric,region,component,scheme];index=ci*len(metrics)+mi
                result=schemes[scheme]
                require(int(result['undefined_draws'][index])==anchor['undefined_draws']
                    and np.isclose(result['estimate'][index],anchor['estimate'],rtol=1e-8,atol=1e-10),
                    'frozen control resampling estimate or unavailable draws differ')
                interval=result['interval'][index]
                if anchor['lower'] is None:
                    require(not np.isfinite(interval).any(),'frozen unavailable interval became available')
                else:
                    expected=np.asarray([anchor['lower'],anchor['upper']])
                    require(np.allclose(interval,expected,rtol=1e-8,atol=1e-10),'frozen control interval endpoints differ')
                    maxima['interval_endpoints']=max(maxima.get('interval_endpoints',0.),float(np.max(np.abs(interval-expected))))
    return dict(status='verified',comparisons=3,metric_game_contractions=entries,
        maximum_absolute_errors=maxima,frozen_saved_ledger=True,interval_comparisons=3*len(metrics)*3,
        shared_primary_draws=True,
        units='loss numerator: squared (recorded unblocked attempts/60) times directed hours',
        rtol=1e-8,atol=1e-10)


def _rate_compatibility(rate_rows, frozen):
    """the single embedded control sign campaign preserves static 04n quantities."""
    old={row['resolution']:row for row in frozen.get('rate_rows',[]) if row['arm']=='borrowing'}
    require(set(old)=={'total','regional','native'},'control rate compatibility requires all frozen static anchors')
    fields=dict(negative_interval_location_pairs='negative_entries',negative_location_hours='negative_entry_location_hours',
        any_negative_directed_hours='any_negative_entry_row_directed_hours',
        negative_location_time_fraction='negative_entry_exposure_fraction',
        any_negative_exposure_fraction='any_negative_entry_row_exposure_fraction',
        negative_mass_predicted_attempts='negative_mass_predicted_attempts',negative_mass_fraction='negative_mass_fraction',
        minimum='minimum',directed_hours='directed_hours')
    errors={}
    for row in rate_rows:
        if row['arm']!='control': continue
        reference=old[row['resolution']]
        for key,old_key in fields.items():
            if key=='negative_interval_location_pairs':
                require(type(row[key]) is int and type(reference[old_key]) is int and row[key]==reference[old_key],
                        'embedded control integer negative-pair count differs')
                continue
            require(np.isclose(row[key],reference[old_key],rtol=1e-8,atol=1e-10),
                    'embedded constant control signs differ from frozen 04n')
            errors[row['resolution']+':'+key]=abs(row[key]-reference[old_key])
        require(row['rows']==reference['rows'] and row['locations']==reference['locations'],
                'embedded control diagnostic row/location counts differ')
        witness=row['worst_location'];anchor=reference['worst_location'];original=anchor['row']
        require(witness['game_id']==original['game_id'] and witness['segment_index']==original['segment_index']
            and witness['period']==original['period'] and witness['side']==original['stratum'][0]
            and witness['attacking_team']==original['attacking_team']
            and witness['location_index']==anchor['location_index']
            and witness['location_label']==anchor['location_label']
            and witness['attainment']=='attained'
            and witness['time']==(original['start']+original['end'])/2,
            'embedded control minimum witness identity differs')
    return dict(status='verified',frozen_rows=len(old),maximum_absolute_errors=errors,rtol=1e-8,atol=1e-10)


def assess(prepared, fitted, output):
    """validate saved states, run fixed probes and assess the frozen held-out rows."""
    from attribution_context import read_prepared, read_fit, _output, _cost, SEASONS, STATE_ARRAYS, RULES, MAIN_COMPONENTS
    from hockey_stats.attribution import (bounded_scalar_score_coefficient_probe,bounded_shape_coefficient_probe,
        validate_shape_coefficient_probe,validate_scalar_coefficient_probe,validate_scalar_score_coefficient_probe)
    from hockey_stats.attribution_context import (TEMPORAL_IDS,context_game_moments,iter_context_rows)
    from hockey_stats.attribution_data import (decode_coefficient_state,coefficient_state_row,
        read_context_source,read_context_fixture)
    from hockey_stats.attribution_simulation import shape_regions

    started,process_started=time.monotonic(),time.process_time()
    source=read_prepared(prepared);document=source.document
    fit_ref,fit_document,states=read_fit(source,fitted)
    original,metadata=(read_context_fixture(linked_path(document['fixture'])) if document['fixture']
                       else read_context_source(document['source_result']))
    source_inventory=[dict(row,partition='assessment' if row['game_id'] in document['assessment_ids'] else 'training')
                      for row in metadata['inventory']]
    require(original.source_identity==document['sources'] and metadata['correction_reference']==document['correction']
            and source_inventory==document['inventory'] and tuple(metadata['assessment_ids'])==tuple(document['assessment_ids']),
            'assessment source, correction or fixed partition differs from preparation')
    root=_output(output,document['purpose']);probes=[];alternative_states={}
    frozen={(row['component'],row['season']):row for row in document['control_probes']}
    selected={(row['arm'],row['component'],row['season']):row for row in fit_document['states']}
    for arm in ('control','candidate'):
        for component in ('volume','shape'):
            for year,training in enumerate(source.trainings):
                state=states[arm,component,SEASONS[year]]
                previous=None if year==0 else states[arm,component,SEASONS[year-1]]
                if arm=='control':
                    saved=frozen[component,SEASONS[year]]
                    receipt=saved['receipt'];alt_row=saved['alternative'];alternative=decode_coefficient_state(alt_row,component)
                    likelihood=training.coarse_scalar_likelihood if component=='volume' else training.coarse_training.likelihood
                    validator=validate_scalar_coefficient_probe if component=='volume' else validate_shape_coefficient_probe
                    validator(likelihood,previous,state,receipt,alternative)
                else:
                    likelihood=training.scalar_likelihood if component=='volume' else training.likelihood
                    receipt,alternative=(bounded_scalar_score_coefficient_probe if component=='volume'
                                         else bounded_shape_coefficient_probe)(likelihood,previous,state)
                    data=write_arrays(root,f'{component}-probe-{year}.npz',
                                      {name:getattr(alternative,name) for name in STATE_ARRAYS[component]})
                    record=selected[arm,component,SEASONS[year]]
                    alt_row=coefficient_state_row(alternative,year,arm,record['parent'],record['likelihood'],data,component)
                    validator=validate_scalar_score_coefficient_probe if component=='volume' else validate_shape_coefficient_probe
                    validator(likelihood,previous,state,receipt,alternative)
                probes.append(dict(arm=arm,component=component,index=year,season=SEASONS[year],
                    origin='reused' if arm=='control' else 'new',verified=receipt['status']=='verified',
                    receipt=receipt,alternative=alt_row))
                if year==4: alternative_states[arm,component]=alternative
    require(len(probes)==20 and sum(p['origin']=='new' for p in probes)==10,
            'context assessment requires ten fresh and ten original conditional probes')
    final=source.trainings[-1];population=source.populations[-1];ids=population.references.player_ids
    variants={};variant_states={}
    for bits in product((False,True),repeat=4):
        name='primary' if not any(bits) else 'probe_'+''.join(str(int(v)) for v in bits)
        chosen={key:alternative_states[key] if bit else states[*key,SEASONS[-1]]
                for key,bit in zip(MAIN_COMPONENTS,bits,strict=True)}
        variants[name]=dict(candidate=context_complete_prediction(final,chosen['candidate','volume'],chosen['candidate','shape'],ids),
            control=embed_constant_prediction(complete_prediction(final.coarse_training,
                chosen['control','volume'],chosen['control','shape'],ids),TEMPORAL_IDS))
        variant_states[name]=chosen
    inventory={row['game_id']:row for row in document['inventory']}
    def games():
        for game_id in population.grouped.game_ids:
            yield dict(context_game_moments(population,final,game_id),**inventory[game_id],
                coverage=original.game_coverage[game_id],source_identity=original.source_identity)
    earlier=set().union(*(t.player_ids for t in source.trainings[:-1]));current=set(final.player_ids)
    support={p:dict(group='current_training' if p in current else 'carried_only' if p in earlier else 'new_to_fit',
                    first_in_corpus_final=p not in earlier) for p in ids}
    regions,names=shape_regions()
    payload,arrays,heldout_hours=assess_games(games(),variants,regions,names,support=support)
    player_rows,player_summaries=player_sensitivities(final,variant_states['primary'],ids,regions,heldout_hours)
    variant_player_summaries=[];scalar_changes=[];regional_changes=[]
    for name in payload['variant_axes']:
        rows,summaries=player_sensitivities(final,variant_states[name],ids,regions,heldout_hours)
        scalar=np.asarray([r['scalar_change'] for r in rows]);regional=np.asarray([[r[f'region_change_{j}'] for j in range(12)] for r in rows])
        scalar_changes.append(scalar.reshape(2,len(ids)));regional_changes.append(regional.reshape(2,len(ids),12))
        variant_player_summaries.extend(dict(variant=name,**row) for row in summaries)
    arrays.update(player_scalar_changes=np.asarray(scalar_changes),player_regional_changes=np.asarray(regional_changes),
        player_ids=np.asarray(ids,dtype=np.int64),heldout_player_hours=heldout_hours)
    shared_samples={scheme:dict(samples=arrays[scheme+'_samples'],blocks=arrays.get(scheme+'_blocks')) for scheme in SCHEMES}
    compatibility=_control_compatibility(population,final,metadata,regions,names,shared_samples)
    replay=dict(rows=0,directed_hours=0.,retained_events=0);game_hours={game:0. for game in document['assessment_ids']};game_counts=dict(game_hours)
    def rows():
        for row in iter_context_rows(original,metadata,SEASONS[-1],document['assessment_ids']):
            replay['rows']+=1;replay['directed_hours']+=row['seconds']/3600
            counts=sum(count for _,count in row['counts']);replay['retained_events']+=counts
            game_hours[row['game_id']]+=row['seconds']/3600;game_counts[row['game_id']]+=counts
            yield row
        for game in payload['game_rows']:
            if game['partition']=='assessment':
                require(np.isclose(game_hours[game['game_id']],game['directed_hours'],rtol=1e-8,atol=1e-10)
                    and game_counts[game['game_id']]==game['retained_recorded_unblocked_attempts'],
                    'streamed held-out counts or hours differ from grouped moments')
        replay['status']='verified'
    physical={}
    rates=continuous_rate_diagnostics(context_prediction_row_batches(rows(),variants['primary'],final,receipt=physical),
                                      regions,names,final.r)
    require(replay.get('status')=='verified' and physical.get('status')=='verified',
            'continuous sign source or composition stream did not finish')
    rate_compatibility=_rate_compatibility(rates,metadata['controls_assessment'])
    numerical=payload['primary_direction_stable'] and all(p['verified'] for p in probes)
    data=write_arrays(root,'assessment.npz',arrays)
    payload.update(numerical_status='verified' if numerical else 'unresolved',
        unresolved_reason=None if numerical else 'conditional probes or primary complete-regional direction remain unresolved',
        region_names=names,player_rows=player_rows,player_summary_rows=player_summaries,
        player_probe_summary_rows=variant_player_summaries,rate_rows=rates,probes=probes,
        prepared=source.reference,protocol=document['protocol'],fit=fit_ref,sources=document['sources'],
        control_references=document['controls'],correction=document['correction'],
        coverage=document['coverage'],years=document['years'],partition=document['inventory'],months=document['months'],
        inventory=dict(states=20,new_states=10,reused_states=10,probes=20,new_probes=10,reused_probes=10,
            variants=16,main_bit_order=RULES['main_bit_order'],players=len(ids),
            games=len(document['inventory']),assessment_games=len(document['assessment_ids'])),
        verification=dict(heldout_rows=replay,physical_prediction=physical,control_comparisons=compatibility,
            control_rate_diagnostics=rate_compatibility,rtol=1e-8,atol=1e-10,
            interval_endpoints='exposure-interior infima: start right_limit, end left_limit; isolated event endpoints separate',
            primary_fit_preserved=fit_ref,probe_scope='fixed incoming primary histories; sixteen final-component combinations'),
        array_axes=dict(loss_numerators=['assessment_games','variants','metrics'],
            player_scalar_changes=['variants','roles','source_reference_players'],
            player_regional_changes=['variants','roles','source_reference_players','regions']),
        preparation_resources=document['resources'],fit_resources=fit_document['resources'],
        limits=['working continuous least-squares contrast; not absolute mse or calibrated noise',
            'conditional intervals exclude refitting, scale-selection, source and model uncertainty',
            'common-gauge movement in prior-only rows is not new player evidence',
            'signed player effects differ from impossible negative complete physical rates',
            'no chance-model or player-ability admission; no fitted value is published'])
    result=artifact('attribution_context_assessment',document['purpose'],
        dict(prepared=source.reference,protocol=document['protocol'],fit=fit_ref),schema_version=1,
        execution_status='complete',**payload,**data,resources=_cost(started,process_started,root))
    write_json(root/'assessment.json',json_values(result))
    return identity(root/'assessment.json')
