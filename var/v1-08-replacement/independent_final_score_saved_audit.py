"""independent saved final score audit; no project readers, source or evaluators."""
from collections import Counter,defaultdict
import hashlib
from itertools import groupby,permutations,zip_longest
import json
from math import fsum,isfinite
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter
import numpy as np

WORK=Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
C=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
NEW=C/'scores/20252026'
OLD=Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/current-04/scores/20252026')
HEADS=['u','q','r','g'];PREFIXES=['u','uq','uqr','uqrg'];REFS=['actor','neutral','neutral_goalie'];GROUPS=['shooter','setter','goalie','coach']
STRENGTHS=['5v5','5v4','5v3','4v3','4v5','3v5','3v4']
STAGES=['avoid_block_probability','on_net_probability','recorded_stop_probability','conversion_probability']
FIELDS=['finishing_goals_per100_attempts','setting_goals_per100_assisted_opportunities',*STAGES,*[x+'_difference' for x in STAGES]]
STATE_FIELDS=['attacking_skaters','defending_skaters','attacking_goalies','defending_goalies']
BUDGETS=dict(probability=1e-5,per100=1e-3,map_l1=1e-3)
started=perf_counter();checked={};manifests={}
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def remember(root,name,digest,size):
    expected=next(x['sha256'] for x in manifests[root]['files'] if x['path']==name)
    assert digest==expected,(root,name);checked[root,name]=dict(path=name,sha256=digest,bytes=size)
def jsonl(root,name):
    h=hashlib.sha256();size=0
    with (root/name).open('rb') as f:
        for line in f:
            h.update(line);size+=len(line);yield json.loads(line)
    remember(root,name,h.hexdigest(),size)
def bindjson(root,name):
    p=root/name;data=p.read_bytes();remember(root,name,hashlib.sha256(data).hexdigest(),len(data));return json.loads(data)
def pairs(a,b):
    missing=object()
    for x,y in zip_longest(a,b,fillvalue=missing):assert x is not missing and y is not missing;yield x,y

a=read(C/'score-20252026-saved-acceptance.json');assert sha(C/'score-20252026-saved-acceptance.json')=='bc20e0f9558b0513aabd806498a74ea3decb0997bf1b3383bec87d96003b6e16'
assert a['strict_read']['invocations_here']==1 and a['strict_read']['status']=='passed'
assert sha(NEW/'manifest.json')=='40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc'
assert sha(OLD/'manifest.json')=='580f85fb2844fabf1d05d26e707438600e9e504fe005410406dd790c2e2ba56c'
for root in (NEW,OLD):
    m=read(root/'manifest.json');manifests[root]=m
    assert len(m['files'])==73 and len({r['path'] for r in m['files']})==73
    assert all((root/r['path']).resolve().is_relative_to(root.resolve()) for r in m['files'])
n,o=manifests[NEW],manifests[OLD]
for k in ['purpose','season','prepared','coaches','training_cutoff','panels','scoring_version']:assert n[k]==o[k],k
assert n['season']=='20252026' and n['purpose']=='real' and n['recipe']['sha256']=='47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674'
assert n['state']['sha256']=='59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276' and sha(n['state']['path'])==n['state']['sha256']
assert n['numerical_resolution']==dict(status='passed',path='resolution.json')
coverage=bindjson(NEW,'coverage.json');assert coverage==bindjson(OLD,'coverage.json')
resolution=bindjson(NEW,'resolution.json');old_resolution=bindjson(OLD,'resolution.json')
assert resolution['status']=='passed' and resolution['tolerances']==BUDGETS
annual_root=Path(n['state']['path']).parent;annual=read(n['state']['path'])
annual_members={x['path']:x['sha256'] for x in annual['files']}
def annual_json(name):assert sha(annual_root/name)==annual_members[name];return read(annual_root/name)
heads={h:annual_json('heads/'+h+'.json') for h in HEADS};baseline_ref=heads['u']['resolution']['baseline'];baseline=annual_json(baseline_ref['path'])
assert sha(annual_root/baseline_ref['path'])==baseline_ref['sha256']
assert resolution['baseline']==dict(baseline_ref,annual_manifest_sha256=n['state']['sha256'])
assert all(annual[k]==n[k] for k in ['purpose','season','prepared','coaches','recipe','training_cutoff'])
assert annual['previous']['sha256']=='1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe'
for h in HEADS:
    r=heads[h]['resolution'];p=annual_json(r['probe']['path'])
    assert heads[h]['status']=='complete' and r['status']=='passed' and r['baseline']==baseline_ref
    assert r['probe']['sha256']==annual_members[r['probe']['path']]
    assert p['head']==h and p['usage']=='numerical_probe' and p['baseline']==baseline_ref and p['comparison']==r['comparison']
    assert p['arrays']['sha256']==annual_members[p['arrays']['path']]
selector=baseline['selector'];ep=resolution['event_probes'];geometry=selector['synthetic_geometry']
assert ep==dict(actual_keys=selector['keys'],fixture_witnesses=[x['key'] for x in selector['fixture_witnesses']],synthetic_geometry=dict(context_key=geometry['context_key'],types=geometry['types'],cells=656))
assert len(ep['actual_keys'])==256 and len(set(ep['actual_keys']))==256 and geometry['cells']==list(range(656)) and geometry['execution']==['actual','neutral']
assert len(selector['requirements'])==48 and all(r['disposition'] in ['actual','fixture'] for r in selector['requirements'])
assert resolution['selector']==a['final_propagation']['focal_selector']
assert a['final_propagation']['event_selector']['annual_requirements']==selector['requirements']
source_ref=a['source_parity']['score_report'];fit_ref=a['source_parity']['fit_report']
assert source_ref['sha256']=='b7deeb18afc0eac4bbdebdf252e02c8aa5eec7182d9ab72ba54ce21aed119e8b'
for ref in [source_ref,fit_ref]:assert sha(ref['path'])==ref['sha256']
source,fit=read(source_ref['path']),read(fit_ref['path'])
assert {k:v for k,v in source.items() if k not in ['command','observer_seconds']}=={k:v for k,v in fit.items() if k not in ['command','observer_seconds']}
assert source['source_contexts']==151381 and source['source_context_sha256']=='f96ee4a0eadeb2f5caa44db999c71b9ad0e6a178b8a3812f9895019dcdb065a3' and source['source_response_sha256']=='63e224a6d8ac06729882bd05b1dcd817df49d39000fb8559817e0e1d01feef04'
print('manifest/annual/probe/selector/source receipt bindings pass',file=sys.stderr,flush=True)

panel_data={p['panel_id']:dict(rows=0,keys=[],old=defaultdict(list),new=defaultdict(list)) for p in n['panels']}
by_state={tuple(p['state'][k] for k in STATE_FIELDS):p['panel_id'] for p in n['panels']}
assert len(panel_data)==32
named={r['key'] for r in source['first_witnesses'] if all(r['consumed'][k]['status']=='unavailable' for k in ['shooter_start_zone:offensive','shooter_start_zone:neutral','shooter_start_zone:defensive'])}
actual={};complete_rows={};heads_count={h:Counter() for h in HEADS};recognized=complete=setter_count=share_count=0
closure=permutation_error=0.;orders=list(permutations(range(4)))
streams={name:[iter(groupby(jsonl(root,name),key=lambda r:(r['game_id'],r['source_index']))) for root in (OLD,NEW)] for name in ['setters.jsonl','shares.jsonl']}
# one compact reducer for descriptive old/new movement; propagation budgets stay separate.
def movement():return dict(event_maxima=[],numeric_cells=0,null_cells=0,absolute=None,relative=None,zero_baseline_to_nonzero=0,zero_example=None)
stats={s:{g:movement() for g in [*REFS,'coalition','all']} for s in ['all_complete','located_unavailable_witnesses','remainder_excluding_named_witnesses']};strata=Counter()
def offer(r,where,x,y):
    d=y-x;loc=dict(where,old=x,new=y,signed_change=d);ab=abs(d)
    if r['absolute'] is None or ab>r['absolute']['absolute_change']:r['absolute']=dict(loc,absolute_change=ab)
    if x==0 and y!=0:
        r['zero_baseline_to_nonzero']+=1
        if r['zero_example'] is None:r['zero_example']=loc
    else:
        rel=ab/abs(x) if x else 0.
        if r['relative'] is None or rel>r['relative']['relative_change']:r['relative']=dict(loc,relative_change=rel)
    r['numeric_cells']+=1;return ab
def flatten(e):
    result={}
    for ref in REFS:
        p=e['prefixes'][ref]
        for name in PREFIXES:result[ref+'.prefix.'+name]=p[name]
        for name,v in zip(['one_minus_u','u_minus_uq','uq_minus_uqr','uqr_minus_uqrg','uqrg'],[1-p['u'],p['u']-p['uq'],p['uq']-p['uqr'],p['uqr']-p['uqrg'],p['uqrg']]):result[ref+'.terminal.'+name]=v
    for name,v in e['conditional_probabilities'].items():
        ref='neutral_goalie' if name.startswith('neutral_goalie_') else 'neutral' if name.startswith('neutral_') else 'actor';result[ref+'.conditional.'+name]=v
    for i,v in enumerate(e['coalition_goal_mass']):result['coalition.'+str(i)]=v
    return result
identity_keys=['season','game_id','source_index','key','shooter_id','goalie_id','attacking_coach_id','defending_coach_id','physical_state','shot_type','outcome','heads','status','reasons']
for old,new in pairs(jsonl(OLD,'events.jsonl'),jsonl(NEW,'events.jsonl')):
    recognized+=1;assert all(old[k]==new[k] for k in identity_keys),new['key']
    for h,v in new['heads'].items():
        heads_count[h]['included' if v['included'] else 'excluded']+=1
        if v['included']:heads_count[h]['class:'+str(int(v['target']))]+=1
    if new['status']!='complete':assert old==new;continue
    complete+=1;key=new['key'];order=(new['game_id'],new['source_index']);state=tuple(new['physical_state']);pid=by_state[state];panel=panel_data[pid];panel['rows']+=1;panel['keys'].append(key)
    complete_rows[key]=(pid,new['shot_type'])
    if key in ep['actual_keys']:actual[key]=new
    for label,e in [('old',old),('new',new)]:
        for prefix in PREFIXES:panel[label]['neutral.'+prefix].append(e['prefixes']['neutral'][prefix])
        for ref in ['actor','neutral_goalie']:panel[label][ref+'.uqrg'].append(e['prefixes'][ref]['uqrg'])
    selected=['all_complete','located_unavailable_witnesses' if key in named else 'remainder_excluding_named_witnesses']
    for s in selected:strata[s]+=1
    before,after=flatten(old),flatten(new);assert before.keys()==after.keys();event_max=dict.fromkeys([*REFS,'coalition','all'],0.)
    for field,x in before.items():
        y=after[field];assert (x is None)==(y is None);group=field.split('.')[0]
        if x is None:
            for s in selected:
                for g in [group,'all']:stats[s][g]['null_cells']+=1
        else:
            assert isfinite(x) and isfinite(y)
            for s in selected:
                for g in [group,'all']:offer(stats[s][g],dict(key=key,physical_state=new['physical_state'],field=field),x,y)
            event_max[group]=max(event_max[group],abs(y-x));event_max['all']=max(event_max['all'],abs(y-x))
    for s in selected:
        for g,v in event_max.items():stats[s][g]['event_maxima'].append(v)
    sets=[];shares=[]
    for name,destination in [('setters.jsonl',sets),('shares.jsonl',shares)]:
        for iterator in streams[name]:
            parent,records=next(iterator);assert parent==order;destination.append(list(records))
    for x,y in pairs(*sets):assert {k:v for k,v in x.items() if k!='posterior_weight'}=={k:v for k,v in y.items() if k!='posterior_weight'} and (x['posterior_weight'] is None)==(y['posterior_weight'] is None)
    setter_count+=len(sets[1]);share_count+=len(shares[1]);assert [(x['group'],x['recipient_id']) for x in shares[0]]==[(x['group'],x['recipient_id']) for x in shares[1]]
    for e,allocation in zip([old,new],shares):
        closure=max(closure,abs(fsum(x['goals'] for x in allocation)-(e['prefixes']['actor']['uqrg']-e['prefixes']['neutral']['uqrg'])))
        contributions=[[] for _ in range(4)];masses=e['coalition_goal_mass']
        for ordering in orders:
            subset=0
            for g in ordering:
                following=subset|(1<<g);contributions[g].append(masses[following]-masses[subset]);subset=following
        for i,g in enumerate(GROUPS):permutation_error=max(permutation_error,abs(fsum(contributions[i])/24-fsum(x['goals'] for x in allocation if x['group']==g)))
    if recognized%30000==0:print('saved events/accounting checked:',recognized,file=sys.stderr,flush=True)
assert recognized==153754 and complete==151381 and recognized-complete==2373 and setter_count==1371413 and share_count==1825556
assert closure<=3e-14 and permutation_error<=3e-14
assert all(next(it,None) is None for name in streams.values() for it in name)
for h,counts in heads_count.items():assert all(source['head_admission'][h][k]==v for k,v in counts.items())
for s,groups in stats.items():
    assert strata[s]==a['probability_movement'][s]['rows']
    for g,r in groups.items():
        maxima=r.pop('event_maxima');r.update(events=len(maxima),event_maximum_absolute_quantiles=dict(zip(['p50','p90','p99','max'],map(float,np.quantile(maxima,[.5,.9,.99,1.])))) if maxima else None)
        assert r==a['probability_movement'][s]['groups'][g],(s,g)
for panel in panel_data.values():
    for label in ['old','new']:panel[label]={k:fsum(v) for k,v in panel[label].items()}
assert len(actual)==256 and named<=complete_rows.keys()
print('all saved event identities, setter/share rows, 24-order allocations and descriptive maxima/quantiles pass',file=sys.stderr,flush=True)

# panel membership is checked independently; arrays are hashed, never evaluated.
for p in n['panels']:
    panel=panel_data[p['panel_id']];keys=[]
    for x,y in pairs(jsonl(OLD,p['events_path']),jsonl(NEW,p['events_path'])):
        assert x==y and complete_rows[y['key']]==(p['panel_id'],y['shot_type']);keys.append(y['key'])
    assert keys==panel['keys'] and len(keys)==panel['rows']==p['events']
projection_values={};old_values={};projection_count=0;scalar={f:movement() for f in FIELDS}
for old,new in pairs(jsonl(OLD,'projections.jsonl'),jsonl(NEW,'projections.jsonl')):
    projection_count+=1;pair=(new['player_id'],new['strength'])
    for k in ['season','player_id','strength','unavailable','coefficient_support','support']:assert old[k]==new[k]
    for label,e in [('old',old),('new',new)]:
        ref=e['reference_panel'];panel=panel_data[ref['panel_id']];assert ref['opportunities']==panel['rows']
        for prefix in PREFIXES:assert abs(ref['neutral'][prefix]-panel[label].get('neutral.'+prefix,0.))<=max(1e-10,32*np.finfo(float).eps*max(1,next(p['origins'] for p in n['panels'] if p['panel_id']==ref['panel_id'])))
    for f in FIELDS:
        x,y=old['values'][f],new['values'][f];assert (x is None)==(y is None)
        if x is None:scalar[f]['null_cells']+=1
        else:scalar[f]['event_maxima'].append(offer(scalar[f],dict(player_id=new['player_id'],strength=new['strength'],field=f),x,y))
    assert pair not in projection_values;projection_values[pair]=new['values'];old_values[pair]=old['values']
assert projection_count==6580
for f,r in scalar.items():
    vals=r.pop('event_maxima');r.update(available_projection_pairs=len(vals),scalar_absolute_change_quantiles=dict(zip(['p50','p90','p99','max'],map(float,np.quantile(vals,[.5,.9,.99,1.])))) if vals else None)
    assert r==a['standardized_scalar_movement'][f],f
maps=0;mapstats={k:dict(available_pairs=0,unavailable_pairs=0,values=[],maximum=None) for k in ['finishing','setting']}
for old,new in pairs(jsonl(OLD,'maps.jsonl'),jsonl(NEW,'maps.jsonl')):
    maps+=1
    for k in ['season','player_id','strength','map_kind','panel_id']:assert old[k]==new[k]
    assert (old['cells'] is None)==(new['cells'] is None);r=mapstats[new['map_kind']]
    if new['cells'] is None:r['unavailable_pairs']+=1;continue
    field=FIELDS[0] if new['map_kind']=='finishing' else FIELDS[1];pair=(new['player_id'],new['strength'])
    assert fsum(old['cells'])==old['integrated_value']==old_values[pair][field]
    assert fsum(new['cells'])==new['integrated_value']==projection_values[pair][field]
    dif=[y-x for x,y in zip(old['cells'],new['cells'],strict=True)];l1=fsum(map(abs,dif));r['available_pairs']+=1;r['values'].append(l1)
    if r['maximum'] is None or l1>r['maximum']['native_map_l1']:
        cell=max(range(len(dif)),key=lambda i:abs(dif[i]));r['maximum']=dict(player_id=pair[0],strength=pair[1],map_kind=new['map_kind'],native_map_l1=l1,old_integrated=old['integrated_value'],new_integrated=new['integrated_value'],largest_cell=cell,old_cell=old['cells'][cell],new_cell=new['cells'][cell])
assert maps==13160
for kind,r in mapstats.items():
    vals=r.pop('values');r['quantiles']=dict(zip(['p50','p90','p99','max'],map(float,np.quantile(vals,[.5,.9,.99,1.])))) if vals else None
    assert r==a['native_map_l1_movement'][kind],kind
print('all 32 panel memberships/sums, projections and native map closures/movement pass',file=sys.stderr,flush=True)

focal=resolution['selector'];focal_pairs=[tuple(p) for p in focal['pairs']]
names=[f'{label}:{strength}:{side}' for strength in STRENGTHS for label in ['finishing','setting'] for side in ['min','max']]+[f'{role}:{block}:{kind}' for role in ['F','D'] for block in ['shooter','setter'] for kind in ['smallest_positive_support','first_prior_only']]+[f+':'+side for f in STAGES for side in ['min','max']]+['largest_tip_supported_fraction']
assert [r['requirement'] for r in focal['requirements']]==names and len(names)==45
assert len(focal_pairs)==43 and len(set(focal_pairs))==43 and focal_pairs==sorted(focal_pairs,key=lambda p:(STRENGTHS.index(p[1]),p[0]))
assert set(focal_pairs)<=(projection_values.keys()) and {tuple(r['pair']) for r in focal['requirements'] if r['pair'] is not None}==set(focal_pairs)
for r in focal['requirements']:assert r['disposition'] in ['selected','unavailable'] and (r['pair'] is None)==(r['disposition']=='unavailable')
public={f"{p['state']['attacking_skaters']}v{p['state']['defending_skaters']}":p['panel_id'] for p in n['panels'] if p['state']['attacking_goalies']==1}
actual_sums={ref:fsum(actual[k]['prefixes'][ref]['uqrg'] for k in ep['actual_keys']) for ref in REFS};danger=Counter()
for e in actual.values():
    d=e['conditional_probabilities']['neutral_on_net_goal_probability'];danger['<.05' if d<.05 else '[.05,.15)' if d<.15 else '>=.15']+=1
propagation={}
assert [p['head'] for p in resolution['probes']]==HEADS
for p in resolution['probes']:
    h=p['head'];assert p['status']=='passed' and p['probe']==heads[h]['resolution']['probe']
    ak=p['actual_keys'];assert ak['population']['keys']==256 and ak['baseline_danger']==dict(danger) and 0<=ak['danger_crossings']<=256
    for ref,s in ak['expected_sums'].items():assert s['baseline']==actual_sums[ref] and isfinite(s['variant']) and 0<=s['variant']<=256 and s['change']==s['variant']-s['baseline']
    assert [x['panel_id'] for x in p['neutral_panels']]==list(panel_data)
    changes={};max_panel=None
    for saved,panel_record in zip(p['neutral_panels'],n['panels'],strict=True):
        panel=panel_data[saved['panel_id']];assert saved['events']==panel['rows']==panel_record['events']
        assert set(saved['baseline'])==set(saved['variant'])==set(PREFIXES)
        for prefix in PREFIXES:
            baseline_sum=panel['new'].get('neutral.'+prefix,0.)
            assert abs(saved['baseline'][prefix]-baseline_sum)<=max(1e-10,32*np.finfo(float).eps*max(1,panel_record['origins']))
            assert isfinite(saved['variant'][prefix]) and 0<=saved['variant'][prefix]<=saved['events']
        delta=saved['variant']['uqrg']-saved['baseline']['uqrg'];assert delta==saved['uqrg_change'];changes[saved['panel_id']]=delta
        if max_panel is None or abs(delta)>abs(max_panel['signed_goal_change']):max_panel=dict(panel_id=saved['panel_id'],events=saved['events'],signed_goal_change=delta)
    assert [tuple(r['pair']) for r in p['pairs']]==focal_pairs
    maxima=dict(stage=0.,per100=0.,map_l1=0.);locators={}
    for r,pair in zip(p['pairs'],focal_pairs,strict=True):
        assert r['status']=='passed' and set(r['scalar_absolute_changes'])==set(FIELDS)
        for f,v in r['scalar_absolute_changes'].items():
            assert (v is None)==(projection_values[pair][f] is None)
            if v is None:continue
            kind='per100' if f in FIELDS[:2] else 'stage';assert isfinite(v) and 0<=v<=BUDGETS['per100' if kind=='per100' else 'probability']
            if kind not in locators or v>maxima[kind]:locators[kind]=dict(pair=list(pair),field=f,change=v)
            maxima[kind]=max(maxima[kind],v)
        for kind,f in zip(['finishing','setting'],FIELDS[:2]):
            v=r['native_map_l1_changes'][kind];assert (v is None)==(projection_values[pair][f] is None)
            if v is None:continue
            assert isfinite(v) and 0<=v<=BUDGETS['map_l1']
            if 'map_l1' not in locators or v>maxima['map_l1']:locators['map_l1']=dict(pair=list(pair),map_kind=kind,change=v)
            maxima['map_l1']=max(maxima['map_l1'],v)
        assert r['neutral_panel_goal_mass_change']==changes[public[pair[1]]]
    for kind,v in maxima.items():assert v==p['maximum_changes'][kind]
    for kind in ['actual_probability','synthetic_probability']:assert isfinite(p['maximum_changes'][kind]) and 0<=p['maximum_changes'][kind]<=BUDGETS['probability']
    assert p['maximum_changes']['posterior_diagnostic'] is None or 0<=p['maximum_changes']['posterior_diagnostic']<=1
    assert a['final_propagation']['heads'][h]['producer_saved_maximum_changes']==p['maximum_changes'] and a['final_propagation']['heads'][h]['independently_reaggregated_pair_maxima']==maxima
    propagation[h]=dict(saved_probability_evidence=p['maximum_changes'],reaggregated_pair_maxima=maxima,pair_maximum_locators=locators,largest_panel_sum_movement=max_panel,actual_key_expected_sums=ak['expected_sums'],danger_crossings_saved=ak['danger_crossings'])
print('four saved propagations, frozen selections, all panel sums/budgets and maximum locators pass',file=sys.stderr,flush=True)

# finish independent member hashing without reopening any JSONL already consumed.
for root,m in manifests.items():
    for ref in m['files']:
        name=ref['path']
        if (root,name) not in checked:
            p=root/name;remember(root,name,sha(p),p.stat().st_size)
    assert len([k for k in checked if k[0]==root])==73
    assert sum(v['bytes'] for k,v in checked.items() if k[0]==root)==m['resources']['output_bytes']
for name in ['people.jsonl','coach_ids.jsonl']:assert checked[NEW,name]['sha256']==checked[OLD,name]['sha256']
identical=[r['path'] for r in n['files'] if checked[NEW,r['path']]['sha256']==checked[OLD,r['path']]['sha256']]
changed=[r['path'] for r in n['files'] if r['path'] not in identical]
assert n['resources']['recognized_events']==recognized and n['resources']['complete_events']==complete and n['resources']['setter_branches']==setter_count and n['resources']['projections']==projection_count
assert n['resources']['projected_skaters']==940 and n['resources']['origin_rows']==sum(p['origins'] for p in n['panels'])
assert sha(WORK/'var/v1-08-replacement/accept_real_score_20252026.py')=='53fa5baf871a8e133ef446d8d41e4602bc371388cd607be3bd746ff2b1970d0f'
launch=(C/'score-20252026-launch-head.txt').read_text().strip();assert launch==n['implementation']['git_commit']=='58ca52df2d9409d1e788b07a916f8b51b9826187' and not n['implementation']['git_dirty']
for ref in [launch,'HEAD']:assert subprocess.check_output(['git','rev-parse',ref+':analysis'],cwd=WORK,text=True).strip()=='fc716257eb118d1a091472cde4b214e8bca1f753'
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','analysis'],cwd=WORK,text=True).strip()
assert (C/'score-20252026.exit').read_text().strip()=='0'
log=(C/'score-20252026.log').read_text();timing=re.search(r'(\d+\.\d+) real\s+(\d+\.\d+) user\s+(\d+\.\d+) sys',log);assert timing
facts=dict(status='passed',kind='independent-saved-final-execution-score-audit',manifest_sha256=sha(NEW/'manifest.json'),canonical_acceptance_sha256=sha(C/'score-20252026-saved-acceptance.json'),original_manifest_sha256=sha(OLD/'manifest.json'),annual_manifest_sha256=n['state']['sha256'],source_report_sha256=source_ref['sha256'],helper_sha256=sha(WORK/'var/v1-08-replacement/accept_real_score_20252026.py'),analysis_tree='fc716257eb118d1a091472cde4b214e8bca1f753',launch_head=launch,members_checked_each=73,member_identities={label:[checked[root,r['path']] for r in manifests[root]['files']] for label,root in [('new',NEW),('old',OLD)]},identical_members=identical,changed_members=changed,population=dict(recognized=recognized,complete=complete,excluded=recognized-complete,setter_rows=setter_count,share_rows=share_count,projections=projection_count,maps=maps,heads={h:dict(v) for h,v in heads_count.items()}),accounting=dict(share_closure_max=closure,independent24order_direct_group_error=permutation_error,all_map_scalar_closures_exact=True,all32panel_memberships_and_sums=True),annual_event_selector=dict(actual_keys=256,fixture_witnesses=ep['fixture_witnesses'],requirements=selector['requirements']),focal_selector=focal,propagation=propagation,panel_goal_sums=[dict(panel_id=pid,events=p['rows'],old=p['old'],new=p['new'],signed_goal_change={r:p['new'].get(r+'.uqrg',0.)-p['old'].get(r+'.uqrg',0.) for r in REFS}) for pid,p in panel_data.items()],probability_movement=stats,standardized_scalar_movement=scalar,native_map_l1_movement=mapstats,resources=dict(new_member_bytes=n['resources']['output_bytes'],old_member_bytes=o['resources']['output_bytes'],producer=n['resources'],whole_command_wall_seconds=float(timing[1]),audit_wall_seconds=perf_counter()-started),scope=dict(recomputed='manifest-bound saved row identities/nullability, scalar/map/share arithmetic, direct24-order allocation, event baseline/danger sums, all32 neutral baseline sums, signed saved variant-minus-baseline, saved pair maxima/locators and verdict budgets',bound_producer_evidence='unsaved variant actual/synthetic probability maxima, posterior diagnostics, variant sums, pair deltas/map-l1 and danger crossings; these are bound and internally checked, not independently predicted',prohibited_calls_performed=False,strict_reader_invocations=0,source_game_reads=0,no_seasonwide_actor_per_event_or_all_player_bound=True))
print(json.dumps(facts,indent=2,allow_nan=False))
