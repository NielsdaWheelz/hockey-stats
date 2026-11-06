"""held saved-only real composition preservation, scalar/context and bounded map check."""
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import resource
import sys
import time

ROOT=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
SOURCE=ROOT/'execution-results'
OUTPUT=ROOT/'results'
SELECTION=ROOT/'states-selection.json'
ADMISSION=ROOT/'spatial-product-admission-02.json'
DESTINATION=ROOT/'compose-spatial-saved-check-01.json'
BASE_SHA='3441f784c11eb6a8eda38800806b8e4dc68e06e8587c91db24c5dffaadae4347'
COMBINED_SHA='a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5'
SELECTION_SHA='7ac43cfa0bcf72b449bc9267b19f16eb5ac7d7bf396fd08d9a98200d94549f1c'
ADMISSION_SHA='f07d5a6ab23ec8234818958050223177e6b19cb56136972af83ad448faab6b80'
DONOR_SHA='f5c467767a45d0b9152a0308e1fc7e407da0d5b465ffdd743baae10918c44521'
YEARS=('20212022','20222023','20232024','20242025','20252026')
DISPLAY=YEARS[2:]
PATHS=dict(zip(YEARS,('spatial/20212022','spatial/20222023-complete-01','spatial/20232024','spatial/20242025','spatial/20252026')))
PREPARED='63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
COACHES='102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
UNKNOWN_SUPPORT=dict(included_seconds=None,events=None,eligible_weight=None,known_excluded_seconds=None,unquantified_gap=True,reason_counts=[],inferred_inputs=[],current_season_information=False,prior_only=False,prior_seasons=[])
PENDING=dict(availability='not_computed',explanation='special-team spatial estimation awaits v1-09',data=None)
SCALAR_KINDS=(('difference','per60'),('complete','per60_complete'),('neutral','per60_neutral'),('relative_percent','relative_percent'))
TERMS=dict(baseline='baseline',self='self',teammates='teammates',opponents='opponents',coaching_other_context='coaching_other_context',numerical_residual='residual',factual_prediction='factual')
HASHED={}


def identity(path):
    path=Path(path);assert path.suffix not in ('.npz','.npy'), 'full array hashing is outside this checker'
    if path not in HASHED:
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        HASHED[path]=dict(path=str(path),bytes=path.stat().st_size,sha256=digest)
    return HASHED[path]


def bound_json(path,expected):
    assert path.suffix not in ('.npz','.npy'), 'array payload is outside JSON checks'
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected, str(path)
    HASHED[path]=dict(path=str(path),bytes=len(raw),sha256=expected)
    return json.loads(raw)


def rows(path,member=None):
    assert path.suffix not in ('.npz','.npy'), 'array payload is outside row checks'
    digest=hashlib.sha256();count=0
    with path.open('rb') as stream:
        for line in stream:
            digest.update(line);count+=1;yield json.loads(line)
    actual=digest.hexdigest()
    if member is not None:
        assert actual==member['sha256'],str(path)
        if 'rows' in member:assert count==member['rows'],str(path)
    HASHED[path]=dict(path=str(path),bytes=path.stat().st_size,sha256=actual)


def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10),(a,b)


def selected_states(selection):
    assert set(selection)=={'schema_version','purpose','prepared_sha256','states'} and type(selection['schema_version']) is int and selection['schema_version']==1
    assert selection['purpose']=='real' and selection['prepared_sha256']==PREPARED
    assert type(selection['states']) is list and [row['season'] for row in selection['states']]==list(YEARS)
    for row in selection['states']:
        assert set(row)=={'season','path','sha256'} and row['path']==str(ROOT/PATHS[row['season']]/'manifest.json')
        assert type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256'])
    assert selection['states'][0]['sha256']=='3b7b51339b5ebb00a340a3f593347adf3a72ee137ad24739abd582b8290a5509'
    return {row['season']:row for row in selection['states']}


def check_estimate(actual,value,reason,method,person):
    why='failed_fit' if reason=='incomplete_annual_family' else 'no_exposure' if reason=='no_exposure' else 'missing_source'
    detail=None if value is not None else dict(explanation=reason or 'saved spatial projection unavailable for this published skater',evidence=[dict(kind='method',id=method),*person['source']])
    assert actual==dict(value=value,unavailable_reason=None if value is not None else why,reason_detail=detail,uncertainty=dict(kind='not_estimated'))


def check_scalar(data,projection,method,person):
    expected_fields={f'{role}_{quantity}_{suffix}' for role in ('offense','defense') for quantity in ('attempts','xg') for _,suffix in SCALAR_KINDS}
    assert set(data)==expected_fields|{'state_weights','support','method_id'}
    assert data['method_id']==method and data['state_weights']==[dict(strength='5v5',weight=1.)]
    assert data['support']==(projection['support'] if projection is not None else UNKNOWN_SUPPORT)
    reason=projection['reason'] if projection is not None else 'published skater has no saved prepared-roster coefficient; no neutral substitution'
    numeric=0
    for role in ('offense','defense'):
        for quantity in ('attempts','xg'):
            for kind,suffix in SCALAR_KINDS:
                value=None if projection is None else projection['values'][role][quantity][kind]
                check_estimate(data[f'{role}_{quantity}_{suffix}'],value,reason,method,person);numeric+=value is not None
    return numeric


def check_context(data,adjustment,quantity,method,person):
    assert set(data)==set(TERMS)|{'method_id'} and data['method_id']==method
    saved=adjustment[quantity] if adjustment is not None else {}
    reason=adjustment['reason'] if adjustment is not None else 'published skater has no saved actual-context projection'
    for name,source in TERMS.items():check_estimate(data[name],saved.get(source),reason,method,person)
    if data['factual_prediction']['value'] is not None:close(sum(data[name]['value'] for name in list(TERMS)[:-1]),data['factual_prediction']['value'])
    return data['factual_prediction']['value'] is None


def check_map_header(row,projection,public):
    assert row['result']['availability']=='provided' and row['view'] in ('complete','effect')
    data=row['result']['data'];field=row['map_kind']+'_per60'+('_complete' if row['view']=='complete' else '')
    estimate=public[field];quantity=row['map_kind'].split('_')[1]
    assert data['grid_id']=='native656' and data['unit']==('attempts_per60' if quantity=='attempts' else 'xg_per60') and data['reference']=='spatial-league-centered-virtual-v1'
    assert data['method_id']==public['method_id'] and data['support']==public['support']
    assert data['integrated_value']==estimate['value'] and data['unavailable_reason']==estimate['unavailable_reason'] and data['reason_detail']==estimate['reason_detail']
    available=projection is not None and projection['available']
    assert available==(estimate['value'] is not None) and (data['cells'] is not None)==available and (data['display_cells'] is not None)==available


def population_receipt(year,published,fitted,state):
    return dict(season=year,source_results=dict(path=str(SOURCE/'manifest.json'),sha256=BASE_SHA),state=state,
        intersection=sorted(published&fitted),published_only=sorted(published-fitted),fitted_only=sorted(fitted-published),
        missing_projection='every required published skater is emitted; absence retains a located unavailable reason, never a neutral player')


def native_sample(path,member,projections,sample,public):
    # Only rates.npy is decompressed; the archive and adjustments.npy are not hashed/read.
    import numpy as np
    player=sample['player_id'];index=next(i for i,row in enumerate(projections) if row['player_id']==player)
    with np.load(path/member['path'],allow_pickle=False) as saved:
        rates=saved['rates'];raw=rates[index,0,0,2].copy();shape=list(rates.shape);loaded_bytes=int(rates.nbytes)
    data=sample['result']['data'];assert [cell['cell_id'] for cell in data['cells']]==list(range(656))
    assert np.array_equal(np.asarray([cell['value'] for cell in data['cells']]),raw)
    assert data['integrated_value']==public[player]['offense_attempts_per60']['value']
    close(math.fsum(raw),data['integrated_value']);close(math.fsum(cell['mass'] for cell in data['display_cells']),data['integrated_value'])
    return dict(player_id=player,map_kind='offense_attempts',view='effect',source_projection_array=member,source_rates_shape=shape,rates_member_array_bytes_loaded=loaded_bytes,native_cells_exact=656,integrated_value=data['integrated_value'],native_sum=math.fsum(raw),display_mass_sum=math.fsum(cell['mass'] for cell in data['display_cells']),archive_integrity='already accepted canonical producer; no full archive rehash',scope='one saved native map plus native/display sums; not all maps, display cells, densities or transport')


def main():
    if not all(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) for value in (BASE_SHA,COMBINED_SHA,SELECTION_SHA,ADMISSION_SHA)):
        raise SystemExit('combined manifest/selection/admission pins withheld; no input/output access')
    started=time.perf_counter();assert not DESTINATION.exists();HASHED.clear()
    assert int((ROOT/'compose-spatial-exit.txt').read_text())==1
    assert int((ROOT/'compose-spatial-complete-01-exit.txt').read_text())==0
    manifest=bound_json(OUTPUT/'manifest.json',COMBINED_SHA);base=bound_json(SOURCE/'manifest.json',BASE_SHA)
    donor=bound_json(OUTPUT/'manifest.json.incomplete',DONOR_SHA)
    assert {k:v for k,v in manifest.items() if k not in ('producer','catalogs')}=={k:v for k,v in donor.items() if k not in ('producer','catalogs')}
    assert {k:v for k,v in manifest['catalogs'].items() if k!='methods'}=={k:v for k,v in donor['catalogs'].items() if k!='methods'}
    assert manifest['catalogs']['methods']['path']=='methods-complete-01.jsonl'
    donor_members=[*donor['catalogs'].values(),*(member for family in donor['families'] for member in family['tables'].values())]
    assert len({m['path'] for m in donor_members})==len(donor_members)
    for member in donor_members: assert identity(OUTPUT/member['path'])['sha256']==member['sha256']
    selection=bound_json(SELECTION,SELECTION_SHA);pinned=selected_states(selection)
    admission=bound_json(ADMISSION,ADMISSION_SHA)
    assert admission['season']==YEARS[-1] and admission['purpose']=='real' and admission['decision']=='admit_saved_baseline'
    assert admission['selection']==dict(path=str(SELECTION),sha256=SELECTION_SHA)
    assert admission['optimizer_accuracy']=='unknown' and admission['original_precision']['status']=='failed'
    precision=admission['original_precision']['comparisons']
    assert {head:precision[head]['status'] for head in ('volume','shape','quality')}==dict(volume='failed',shape='passed',quality='passed')
    assert admission['schema_version']==2
    warning=admission['content_warning'];assert type(warning) is str and warning
    context_warnings=admission['actual_context_warnings'];assert set(context_warnings)=={'20242025','20252026'}
    context_evidence=[dict(uri=str(ADMISSION),sha256=ADMISSION_SHA),dict(uri=admission['actual_context_review']['path'],sha256=admission['actual_context_review']['sha256'])]
    references=[admission[name] for name in ('selection','baseline','policy','consequence_result','consequence_review')]+[precision[head] for head in ('volume','shape','quality')]
    admission_evidence=[dict(uri=str(ADMISSION),sha256=ADMISSION_SHA)]+[dict(uri=row['path'],sha256=row['sha256']) for row in references]
    assert manifest['purpose']==base['purpose']=='real' and manifest['seasons']==base['seasons']==list(DISPLAY)
    for key in ('observed_bindings','prepared_sha256'):assert manifest[key]==base[key]
    assert manifest['prepared_sha256']==PREPARED
    annuals={};previous=None
    for year,item in pinned.items():
        state=bound_json(Path(item['path']),item['sha256']);assert state['purpose']=='real' and state['season']==year
        assert state['prepared']['sha256']==PREPARED and state['coaches']['sha256']==COACHES
        assert state['previous']==(None if previous is None else dict(previous,purpose='real',usage='annual'))
        if year==YEARS[-1]:
            members_by_path={r['path']:r for r in state['files']};parent=Path(item['path']).parent
            baseline=members_by_path['probes/baseline.json']
            assert admission['baseline']==dict(path=str(parent/baseline['path']),sha256=baseline['sha256'])
            for head in ('volume','shape','quality'):
                member=members_by_path[f'probes/{head}-comparison.json']
                assert precision[head]==dict(path=str(parent/member['path']),sha256=member['sha256'],status=precision[head]['status'])
        annuals[year]=state;previous=item
    before={(r['season'],r['family']):r for r in base['families']};after={(r['season'],r['family']):r for r in manifest['families']};assert set(before)==set(after)
    inherited=[]
    for key,family in before.items():
        if family['family']=='spatial':continue
        assert after[key]==family
        for member in family['tables'].values():
            checked=identity(OUTPUT/member['path']);assert checked['sha256']==member['sha256'];inherited.append(checked)
    for name in ('people','sources','supports'):
        assert manifest['catalogs'][name]==base['catalogs'][name]
        if name!='people':assert identity(OUTPUT/manifest['catalogs'][name]['path'])['sha256']==base['catalogs'][name]['sha256']
    people_member=manifest['catalogs']['people'];people={(r['season'],r['player_id']):r for r in rows(OUTPUT/people_member['path'],people_member)}
    old_member=base['catalogs']['methods'];old_methods={r['method_id']:r for r in rows(SOURCE/old_member['path'],old_member)}
    new_member=manifest['catalogs']['methods'];methods={r['method_id']:r for r in rows(OUTPUT/new_member['path'],new_member)}
    donor_method_member=donor['catalogs']['methods'];donor_methods={r['method_id']:r for r in rows(OUTPUT/donor_method_member['path'],donor_method_member)}
    with (OUTPUT/donor_method_member['path']).open('rb') as old, (OUTPUT/new_member['path']).open('rb') as new:
        for a,b in zip(old,new,strict=True):
            if not json.loads(a)['method_id'].startswith('spatial-v1-08-'): assert a==b
    assert all(methods[k]==v for k,v in old_methods.items()) and set(methods)-set(old_methods)=={f'spatial-v1-08-{year}' for year in DISPLAY}
    years=[];samples=[];method_evidence=[]
    for year in DISPLAY:
        state=annuals[year];path=Path(pinned[year]['path']).parent;members={r['role']:r for r in state['files']}
        projections=list(rows(path/members['projections']['path'],members['projections']));by_player={r['player_id']:r for r in projections};assert len(by_player)==len(projections)
        adjustment_rows=list(rows(path/members['adjustments']['path'],members['adjustments']));adjustments={(r['player_id'],r['role']):r for r in adjustment_rows};assert len(adjustments)==len(adjustment_rows)
        published={player for (season,player),person in people.items() if season==year and person['kind']=='skater'};fitted=set(by_player)
        population=population_receipt(year,published,fitted,dict(path=pinned[year]['path'],sha256=pinned[year]['sha256']))
        receipt_path=OUTPUT/f'{year}-spatial-composition.json';method=methods[f'spatial-v1-08-{year}'];method_id=method['method_id'];fit_years=[y for y in YEARS if y<=year]
        assert method['recipe_id']==state['recipe_id']+':'+state['recipe']['version'] and method['design_sha256']==state['design_identity'] and method['fit_seasons']==fit_years and method['training_cutoff']==state['training_cutoff']
        inputs=[dict(role='prepared',sha256=PREPARED,seasons=fit_years),dict(role='coaches',sha256=COACHES,seasons=fit_years),dict(role='opportunity_panel',sha256=state['valued']['sha256'],seasons=[year]),dict(role='source_results',sha256=BASE_SHA,seasons=[year]),*[dict(role='annual_state',sha256=pinned[y]['sha256'],seasons=[y]) for y in fit_years]]
        assert method['inputs']==inputs and method['input_sha256']==hashlib.sha256(json.dumps(inputs,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert any(r['sha256']==state['valued']['sha256'] for r in old_methods[f'execution-v1-06-{year}']['evidence'])
        old_method=donor_methods[method_id]
        assert {k:v for k,v in method.items() if k not in ('limitations','evidence','assessment')}=={k:v for k,v in old_method.items() if k not in ('limitations','evidence','assessment')}
        evidence=method['evidence'];assert len(evidence)=={'20232024':3,'20242025':5,'20252026':13}[year] and evidence[0]==dict(uri=pinned[year]['path'],sha256=pinned[year]['sha256'])
        support=members['coefficient_support'];assert evidence[1]==dict(uri=str(path/support['path']),sha256=support['sha256'])
        assert identity(path/support['path'])['sha256']==support['sha256']
        assert evidence[2]['uri']==str(receipt_path) and bound_json(receipt_path,evidence[2]['sha256'])==population
        original_limitations=old_method['limitations'][:6]
        expected_warnings=([warning] if year==YEARS[-1] else [])+([context_warnings[year]] if year in context_warnings else [])
        assert method['limitations']==original_limitations+expected_warnings
        if year=='20232024': assert method==old_method
        findings=method['assessment']['findings'];assert len(findings)==(2 if year in context_warnings else 1)
        if year==YEARS[-1]:
            assert evidence[3:]==admission_evidence+[context_evidence[1]]
            assert method['limitations'].count(warning)==1
            assert findings[0]['evidence']==evidence[:-1] and findings[0]['summary'].endswith('; '+warning)
        else:
            assert findings[0]['evidence']==evidence[:3]
            if year in context_warnings: assert evidence[3:]==context_evidence
        if year in context_warnings:
            assert method['limitations'].count(context_warnings[year])==1
            assert findings[1]['summary']==context_warnings[year] and findings[1]['evidence']==context_evidence
            assert findings[1]['quantities']==[f'adjustment_decomposition.{x}' for x in ('baseline','self','teammates','opponents','coaching_other_context','numerical_residual','factual_prediction')]
        for row in evidence:
            checked=identity(Path(row['uri']));assert checked['sha256']==row['sha256']
            method_evidence.append(checked)
        family=after[year,'spatial'];assert family['availability']=='provided';public={};pending=numeric=0
        scalar_member=family['tables']['skater_spatial']
        for row in rows(OUTPUT/scalar_member['path'],scalar_member):
            assert row['season']==year
            if row['strength']!='5v5':assert row['result']==PENDING;pending+=1;continue
            player=row['player_id'];assert player in published and player not in public and row['result']['availability']=='provided'
            numeric+=check_scalar(row['result']['data'],by_player.get(player),method_id,people[year,player]);public[player]=row['result']['data']
        assert set(public)==published
        context_member=family['tables']['adjustment_decomposition'];context_keys=set();unavailable=0
        for row in rows(OUTPUT/context_member['path'],context_member):
            assert row['season']==year
            if row['strength']!='5v5':assert row['result']==PENDING;continue
            player=row['player_id'];key=(player,row['target']);assert player in published and key not in context_keys;context_keys.add(key)
            direction,quantity,_=row['target'].split('_',2);assert row['result']['availability']=='provided'
            unavailable+=check_context(row['result']['data'],adjustments.get((player,'offense' if direction=='for' else 'defense')),quantity,method_id,people[year,player])
        assert context_keys=={(p,f'{direction}_{quantity}_per60') for p in published for direction in ('for','against') for quantity in ('attempts','xg')}
        map_member=family['tables']['analysis_map'];sample=None;map_headers=0
        for row in rows(OUTPUT/map_member['path']):
            assert row['season']==year
            if row['strength']!='5v5':assert row['result']==PENDING;continue
            player=row['player_id'];assert player in published
            check_map_header(row,by_player.get(player),public[player]);map_headers+=1
            if row['map_kind']=='offense_attempts' and row['view']=='effect' and row['result']['data']['cells'] is not None:sample=row;break
        samples.append(dict(season=year,status='no_available_saved_map') if sample is None else dict(season=year,status='sample_checked',**native_sample(path,members['projection_arrays'],projections,sample,public)))
        years.append(dict(season=year,identity_reconciliation=population,published_5v5_players=len(public),scalar_fields_exact=16*len(public),numeric_scalar_values=numeric,unavailable_scalar_fields=16*len(public)-numeric,pending_strength_rows=pending,actual_context_fields_exact=7*len(context_keys),unavailable_actual_context_rows=unavailable,map_header_prefix_rows_checked=map_headers,fitted_prior_only_zero_time_players=sum(r['support']['prior_only'] and r['support']['included_seconds']==0 for r in projections)))
    producer_resources=bound_json(OUTPUT/'completion-resources-01.json',identity(OUTPUT/'completion-resources-01.json')['sha256'])
    assert producer_resources['state_selection']==dict(path=str(SELECTION),sha256=SELECTION_SHA)
    assert producer_resources['donor_manifest']==dict(path=str(OUTPUT/'manifest.json.incomplete'),sha256=DONOR_SHA)
    assert producer_resources['product_admission']==dict(path=str(ADMISSION),sha256=ADMISSION_SHA)
    assert producer_resources['methods']==dict(path=str(OUTPUT/new_member['path']),sha256=new_member['sha256'])
    assert producer_resources['manifest']==dict(path=str(OUTPUT/'manifest.json'),sha256=COMBINED_SHA)
    def command_cost(stem):
        log=ROOT/(stem+'.log');text=log.read_text()
        timing=re.findall(r'([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys',text)
        rss=re.findall(r'(\d+)\s+maximum resident set size',text);footprint=re.findall(r'(\d+)\s+peak memory footprint',text)
        return dict(timing=None if not timing else dict(zip(('wall_seconds','user_seconds','system_seconds'),map(float,timing[-1]))),
                    maximum_resident_bytes=None if not rss else int(rss[-1]),peak_memory_footprint_bytes=None if not footprint else int(footprint[-1]),log=identity(log))
    result=dict(kind='real-combined-spatial-saved-composition-check',status='scoped_saved_checks_passed_pending_independent_and_runtime_acceptance',recorded_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),manifest=identity(OUTPUT/'manifest.json'),execution_base=identity(SOURCE/'manifest.json'),states_selection=identity(SELECTION),product_admission=identity(ADMISSION),purpose='real',displayed_seasons=list(DISPLAY),producer=manifest['producer'],exit=0,
        cost=dict(completion_resources=producer_resources,failed_composition=command_cost('compose-spatial'),additive_completion=command_cost('compose-spatial-complete-01')),
        preservation=dict(original_member_bytes_verified=len(donor_members),donor_manifest=identity(OUTPUT/'manifest.json.incomplete'),nonowned_family_rows_exact=sum(k[1]!='spatial' for k in before),table_members_byte_exact=len(inherited),inherited_table_bytes=sum(row['bytes'] for row in inherited),people_sources_supports_descriptor_and_actual_hash_exact=True,retained_methods=len(old_methods),added_methods=len(methods)-len(old_methods)),saved_scalar_and_context_checks=years,native_source_samples=samples,method_evidence_actual_hashes=method_evidence,fully_hashed_files=list(HASHED.values()),
        verification_cost=dict(wall_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)),checker=identity(Path(__file__).resolve()),publication_launched=False,
        scope='saved preservation hashes/catalog retention, all 16 published scalar/support and seven actual-context fields, exact identity intersection/differences and added method/admission disclosure bindings; JSON/JSONL evidence may be large and is counted above; only one native rates map per display year, no full NPZ hash or adjustments/design/head array read, source/model/compose/full strict reader. inherited method evidence payloads are not reopened. full native/display transport proof remains the fixture algorithm proof; real independent/runtime/product acceptance remains separate')
    with DESTINATION.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],receipt=str(DESTINATION),inherited_members=len(inherited),display_years=len(years))))
    return 0


if __name__=='__main__':raise SystemExit(main())
