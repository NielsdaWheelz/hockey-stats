"""temporary strict-state/history/reference integration checks."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np
from scipy.sparse import csr_matrix

from hockey_stats.artifacts import ordered_array_digest
from hockey_stats.captures import InputContractError
from hockey_stats.spatial_design import SpatialDesign, RECIPE, CONTEXT_AXES, _actor_columns, _basis
from hockey_stats.spatial_rates import fit_spatial, annual_priors, HEADS, centered_reference, _unpack, head_objective, project_spatial, _linear
from hockey_stats.spatial_state import read_spatial_state, validate_design


def design():
    players=tuple(str(i) for i in range(11));players=tuple(sorted(players))
    a=['0','1','2','3','4'];b=['5','6','7','8','9']
    columns=tuple(_actor_columns(players,('coach',))+[dict(kind='context',name=a['name']) for a in CONTEXT_AXES])
    matrix=np.zeros((2,len(columns)))
    for row,(att,defend) in enumerate(((a,b),(b,a))):
        matrix[row,0]=1
        for i,c in enumerate(columns):
            if c.get('block')=='attacking_player' and c['id'] in att:matrix[row,i]=1
            if c.get('block')=='defending_player' and c['id'] in defend:matrix[row,i]=1
            if c.get('block')=='attacking_coach' and c['subblock'] in ('base','score:0'):matrix[row,i]=1
    keys=tuple(dict(game_id='fixture',segment_index=0,chunk_index=0,source_index=None,attacking_side=side,
                    attacking_players=att,defending_players=defend,optional_missing=True,
                    attacking_team_id='h' if row==0 else 'a',defending_team_id='a' if row==0 else 'h')
               for row,(side,att,defend) in enumerate((('home',a,b),('away',b,a))))
    event_keys=tuple(dict(key,source_index=i,boundary_goal=(i==0),inferred_origin=(i==0)) for i,key in enumerate(keys))
    basis,basis_id=_basis();basis_id=dict(basis_id,array_sha256=ordered_array_digest({'basis':basis}))
    exposure=np.array([1/6,1/6],dtype=float)
    cells=np.array([2,17,300],dtype=np.int64);weights=np.array([.25,.75,1.]);q=np.array([.04,.2,.06]);n=2;hours=float(exposure.sum())
    mass=np.bincount(cells,weights=weights,minlength=656);neutral=np.bincount(cells,weights=weights*q,minlength=656)
    pi=(mass+10*(mass+1/656)/(n+1))/(n+10);r=(n+(n+1)/(hours+1))/(hours+1)
    qmean=(neutral.sum()+10*(neutral.sum()+.5)/(n+1))/(n+10);qbar=(neutral+10*pi*qmean)/(mass+10*pi)
    transforms={'axes':[dict(axis,location=0.,scale=1.,available_hours=hours,missing_hours=0.) for axis in CONTEXT_AXES]}
    transforms['design_sha256']=hashlib.sha256(json.dumps(dict(recipe=RECIPE['sha256'],columns=columns,transforms=transforms),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    coverage=dict(purpose='fixture',season='20212022',attempts=2,origin_mass=2.,physical_included_hours=hours/2,directed_included_hours=hours,
                  neutral_chance_mass=float(neutral.sum()),games=[],players={p:dict(included_seconds=0. if p=='10' else 600.,events=0 if p=='10' else 2,
                    known_excluded_seconds=0.,unquantified_gap=False,reason_counts={},inferred_inputs=['blocked_origin']) for p in players})
    binding=dict(path='/missing/input/manifest.json',sha256='0'*64,purpose='fixture')
    return SpatialDesign('fixture','20212022',binding,binding,dict(binding,season='20212022'),'2022-01-01',players,
         {p:dict(position_group='F',age_days=26*365.2425) for p in players},('coach',),columns,csr_matrix(matrix[:,:len(_actor_columns(players,('coach',)))]),csr_matrix(matrix[:,:len(_actor_columns(players,('coach',)))]),matrix[:,len(_actor_columns(players,('coach',))):].copy(),matrix[:,len(_actor_columns(players,('coach',))):].copy(),exposure,
         keys,event_keys,np.array([0,2,3],dtype=np.int64),cells,weights,q,transforms,coverage,RECIPE,{},basis,basis_id,dict(r=r,pi=pi.tolist(),qbar=qbar.tolist()))


def main():
    d=design();validate_design(d)
    with tempfile.TemporaryDirectory(prefix='spatial-v1-08-') as path:
        state=fit_spatial(d,None,Path(path)/'annual',final_year=True)
        assert all(state.heads[h]['status']=='complete' for h in HEADS),state.heads
        assert state.probes['status']=='passed',state.probes
        absent=[r for r in state.coefficient_support if r['player_id']=='10']
        assert len(absent)==6 and all(r['prior_only'] and r['included_seconds']==0 for r in absent)
        assert all(not r['available'] and r['reason']=='no_exposure' for r in state.adjustments if r['player_id']=='10')
        rates=state.projection_arrays['rates']
        assert np.all(rates[:,:,:,0:2]>0) and np.all(rates[:,:,1,0:2]<=rates[:,:,0,0:2])
        for head in HEADS:
            beta,age=_unpack(state.head_arrays[head]['coefficients'],d,head)
            centers,reference,vector=centered_reference(d,head,beta)
            # verify transfer for every physical row, including unknown coach/gate.
            centered=beta.copy();offset=np.zeros_like(_linear(d,beta,'time'))
            for c in centers:
                centered[c['indices']]-=np.asarray(c['mean'])
                applicability=np.asarray(d.X_time[:,c['indices']].sum(axis=1)).ravel()
                offset+=applicability[:,None]*np.asarray(c['mean'])
            assert np.allclose(_linear(d,beta,'time'),_linear(d,centered,'time')+offset,atol=1e-13,rtol=0)
        # a two-year gap carries raw supported coordinates, not the annual center.
        later=replace(d,season='20232024',player_facts={p:dict(position_group='F',age_days=28*365.2425) for p in d.players})
        prior=next(r for r in annual_priors(later,'volume',state.heads['volume']['ledger']) if r['block']=='attacking_player' and r['id']=='0')
        assert prior['precision']==[50.] and prior['prior_anchor_season']=='20212022' and np.allclose(prior['age_delta'],[.2,0.],atol=1e-14,rtol=0)
        # prior-only players have no entry in supported history.
        assert not any(r['id']=='10' and r['block'].endswith('_player') for r in state.heads['volume']['ledger'])
        # detached strict read succeeds although source/predecessor locators do not exist.
        read_spatial_state(state.path,'fixture')
        original=state.path/'projections.jsonl';data=[json.loads(line) for line in original.read_text().splitlines()]
        data[0]['values']['offense']['xg']['difference']+=1.
        original.write_text(''.join(json.dumps(r)+'\n' for r in data))
        manifest_path=state.path/'manifest.json';manifest=json.loads(manifest_path.read_text())
        for member in manifest['files']:
            if member['path']=='projections.jsonl':member['sha256']=hashlib.sha256(original.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        try:read_spatial_state(state.path,'fixture')
        except InputContractError:pass
        else:raise AssertionError('strict reader accepted a rehashed wrong contrast')
    print('tiny full triple, probes, prior-only/history, gate centering and strict detached semantic rejection: green')

if __name__=='__main__':main()
