"""generated tiny controls only; no saved fixture/real input or numerical fitting."""
from copy import deepcopy
import json
import numpy as np
import independent_final_spatial_probe_audit as audit
from independent_first_spatial_audit import WIDTHS

players=['1','2'];basis=np.zeros((656,40));basis[:,0]=np.linspace(-1,1,656)
offsets=dict(r=2.,pi=(np.ones(656)/656).tolist(),qbar=(np.ones(656)*.2).tolist())
refs={h:np.zeros(WIDTHS[h]) for h in audit.HEADS}
betas={h:np.zeros((5,WIDTHS[h])) for h in audit.HEADS}
heads={h:dict(priors=[dict(block=block,id=p,subblock='base',index=i) for i,(block,p) in enumerate([(b,p) for b in ('attacking_player','defending_player') for p in players],1)],centers=[dict(block=b,subblock='base',mean=np.zeros(WIDTHS[h]).tolist()) for b in ('attacking_player','defending_player')]) for h in audit.HEADS}
base=audit.probabilities(players,heads,betas,refs,offsets,basis)
changed=deepcopy(betas);changed['quality'][1,0]=1e-6;changed['shape'][1,0]=2e-6
prob=audit.probabilities(players,heads,changed,refs,offsets,basis)
assert np.max(abs(prob['standardized_quality_probability']-base['standardized_quality_probability']))>0
assert np.max(abs(prob['standardized_shape_probability']-base['standardized_shape_probability']))>0
altered=deepcopy(offsets);altered['qbar']=(np.ones(656)*.4).tolist()
assert not np.array_equal(audit.probabilities(players,heads,betas,refs,altered,basis)['neutral_quality_probability'],base['neutral_quality_probability'])
rates=np.ones((2,2,2,3,656));variant=rates.copy();variant[0,0,1,2,0]+=2**-20;variant[0,0,1,2,1]-=2**-20
values=audit.movements(rates,variant,base,prob);maxima=audit.reduce_maxima(players,values)
assert maxima['standardized_scalar_per_hour']['value']==0.
assert maxima['standardized_native_map_l1']['value']>1.9e-6
assert maxima['standardized_native_map_l1']['locator']==dict(player_id='1',role='offense',quantity='xg',kind='difference')
assert maxima['neutral_shape_probability']['locator']==dict(kind='neutral',cell=0)
row=dict(kind='time',index=0,key=dict(game_id='2025020001',segment_index=0,chunk_index=0,source_index=None,attacking_players=['1'],defending_players=['2']),role='offense',player_id='1',requirements=['entries'])
requirements=[dict(requirement=name,disposition='actual' if name=='entries' else 'no_matching_context',key=row['key'] if name=='entries' else None) for name in audit.REQUIREMENTS]
audit.check_selection([row],requirements,players)
comparison=dict(status='passed',reason=None,maxima=deepcopy(maxima),failures=[])
for name in audit.CONTEXT_SHAPES:comparison['maxima'][name]=dict(value=0.,limit=audit.LIMITS[name],locator=dict(kind=row['kind'],key=row['key'],player_id='1',role='offense',coordinate=[0,0]))
result=audit.check_comparison(comparison,players,[row],values,maxima);assert result['budgets_passed'] is True
refused=[]
for name in ('shape','inventory','nonfinite','locator','coordinate','row_identity','row_order','requirement','limit','failure_status','signed_l1_confusion','zero_first_location'):
    c=deepcopy(comparison);rows=[deepcopy(row)];req=deepcopy(requirements);v={k:x.copy() for k,x in values.items()}
    try:
        if name=='shape':audit.movements(rates[:1],variant,base,prob)
        elif name=='row_identity':rows[0]['player_id']='2';audit.check_selection(rows,req,players)
        elif name=='row_order':rows=rows*2;audit.check_selection(rows,req,players)
        elif name=='requirement':req[0]['disposition']='actual';audit.check_selection(rows,req,players)
        else:
            if name=='inventory':c['maxima'].pop('shape_probability')
            elif name=='nonfinite':c['maxima']['shape_probability']['value']=float('nan')
            elif name=='locator':c['maxima']['standardized_scalar_per_hour']['locator']['player_id']='unknown'
            elif name=='coordinate':c['maxima']['shape_probability']['locator']['coordinate']=[16,0]
            elif name=='limit':c['maxima']['shape_probability']['limit']=1e-4
            elif name=='failure_status':c['status']='failed'
            elif name=='signed_l1_confusion':c['maxima']['standardized_native_map_l1']['value']=0.
            elif name=='zero_first_location':c['maxima']['neutral_shape_probability']['locator']['cell']=1
            audit.check_comparison(c,players,rows,v,maxima)
    except (AssertionError,KeyError,ValueError):refused.append(name)
    else:raise AssertionError('accepted '+name)
# Either independent or saved threshold crossing refuses; no equality tolerance rescues it.
for owner in ('independent','saved'):
    c=deepcopy(comparison);v={k:x.copy() for k,x in values.items()};m=deepcopy(maxima)
    if owner=='independent':v['standardized_quality_probability'][0,0,0]=np.nextafter(1e-5,np.inf);m=audit.reduce_maxima(players,v)
    else:
        item=c['maxima']['quality_probability'];item['value']=float(np.nextafter(1e-5,np.inf));c['status']='failed';c['reason']='numerical_movement_exceeds_budget';c['failures']=[dict(quantity='quality_probability',**item)]
    assert audit.check_comparison(c,players,[row],v,m)['budgets_passed'] is False
# Generated head/descriptor identities, conditional completion and held CLI admission.
from unittest.mock import patch
volume=deepcopy(heads['volume']);volume.update(head='volume',status='complete',reasons=[],ledger=[],reference_predictor=[0.],age_curves=dict(reference_age=27.,scale_years=10.,ridge_precision=64.,curves=[dict(role=r,position_group=p,coefficients=[0.,0.]) for r,p in (('offense','F'),('offense','D'),('defense','F'),('defense','D'))]),objective=dict(likelihood=0.,penalty=0.,total=0.),solver=dict(converged=True,options=audit.SOLVER,maxfun=15000,maxls=20,iterations=0,evaluations=1,raw_gradient_inf_norm=0.),diagnostics={},resources={})
for prior in volume['priors']:
    prior.update(mean=[0.],prior_mean=[0.],age_indices=[],age_delta=[],prior_only=prior['index']==4,current_season_information=prior['index']!=4,last_supported=None,position_group='F',age=27.,prior_seasons=[])
    if not prior['prior_only']:volume['ledger'].append(dict(block=prior['block'],id=prior['id'],subblock='base',coefficient=[0.],season='20252026',position_group='F',age=27.,support_seasons=['20252026']))
flat=np.zeros(13);audit.check_head(volume,flat,'volume','20252026',audit.SOLVER)
continuation=deepcopy(volume);continuation['solver']['options']=audit.CONTINUATION
audit.check_head(continuation,flat,'volume','20252026',audit.CONTINUATION,volume)
for name in ('head_identity','prior_input','conditional_profile','age_packing','solver_control','objective_closure'):
    bad=deepcopy(continuation);coefficients=flat.copy()
    if name=='head_identity':bad['head']='shape'
    elif name=='prior_input':bad['priors'][0]['mean']=[1.]
    elif name=='conditional_profile':coefficients[4]=1.
    elif name=='age_packing':bad['age_curves']['curves'][0]['coefficients'][0]=1.
    elif name=='solver_control':bad['solver']['options']=audit.SOLVER
    else:bad['objective']['total']=1.
    try:audit.check_head(bad,coefficients,'volume','20252026',audit.CONTINUATION,volume)
    except AssertionError:refused.append(name)
    else:raise AssertionError('accepted '+name)
manifest=dict(purpose='real',season='20252026',recipe={},prepared={},coaches={},valued={},previous={},design_identity='a',basis_identity={},files=[dict(path='head',sha256='a')],resources={})
annual=deepcopy(manifest);descriptor={k:manifest[k] for k in ('purpose','season','recipe','prepared','coaches','valued','previous','design_identity','basis_identity')}
flat_heads={h:np.zeros(1) for h in audit.HEADS};descriptor.update(schema_version=1,heads={h:dict(metadata_sha256=audit.canonical_digest(heads[h]),arrays_sha256=audit.digest_arrays({'coefficients':flat_heads[h]})) for h in audit.HEADS})
audit.check_baseline(manifest,annual,descriptor,heads,flat_heads)
for name in ('baseline_input','baseline_member','baseline_metadata_digest','baseline_coefficients_digest'):
    m=deepcopy(manifest);d=deepcopy(descriptor)
    if name=='baseline_input':m['prepared']={'changed':True}
    elif name=='baseline_member':m['files']=[]
    elif name=='baseline_metadata_digest':d['heads']['shape']['metadata_sha256']='changed'
    else:d['heads']['volume']['arrays_sha256']='changed'
    try:audit.check_baseline(m,annual,d,heads,flat_heads)
    except AssertionError:refused.append(name)
    else:raise AssertionError('accepted '+name)
with patch.object(audit.sys,'argv',['check','--expected-manifest-sha256','WITHHELD','--out','/unused']),patch.object(audit,'sha',side_effect=AssertionError('unexpected input read')),patch.object(audit.Path,'resolve',side_effect=AssertionError('unexpected path access')),patch.object(audit.np,'load',side_effect=AssertionError('unexpected array read')):
    try:audit.main()
    except AssertionError as error:assert 'pin withheld' in str(error)
    else:raise AssertionError('held command admitted')
print(json.dumps(dict(status='passed',generated_only=True,arithmetic='signed cancellation vs l1, qbar/intercept/shape discrimination, c-order zero tie',refused=refused,threshold_owners=['saved','independent'],actual_reads_or_model_calls=0),indent=2))
