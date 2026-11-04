"""year-two saved-json history/control check; canonical writer owns numeric validation."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from time import perf_counter

from accept_real_spatial_20212022 import HEADS, SOLVER

CAMPAIGN=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
OUTPUT=CAMPAIGN/'real/spatial/20222023'
PREVIOUS=CAMPAIGN/'real/spatial/20212022'
PREVIOUS_SHA='PENDING_ACCEPTED_SPATIAL_20212022_MANIFEST_SHA256'
ANALYSIS='fc716257eb118d1a091472cde4b214e8bca1f753'


def _key(row):
    return row['block'],row['id'],row['subblock']


def _records(rows):
    result={_key(row):row for row in rows}
    assert len(result)==len(rows)
    return result


def _head(root,manifest,head):
    name=f'heads/{head}.json';raw=(root/name).read_bytes()
    assert sha256(raw).hexdigest()==next(row['sha256'] for row in manifest['files'] if row['path']==name)
    result=json.loads(raw);assert result['head']==head
    return result


def inspect_second_year(path,previous,*,purpose,previous_sha256,prepared_sha256,coaches_sha256,valued_sha256):
    path,previous=Path(path),Path(previous)
    old_raw=(previous/'manifest.json').read_bytes();old=json.loads(old_raw)
    raw=(path/'manifest.json').read_bytes();current=json.loads(raw)
    assert sha256(old_raw).hexdigest()==previous_sha256
    assert old['kind']==current['kind']=='spatial_state' and old['purpose']==current['purpose']==purpose
    assert old['season']=='20212022' and old['previous'] is None and current['season']=='20222023'
    assert current['previous']==dict(path=str(previous/'manifest.json'),sha256=previous_sha256,season='20212022',purpose=purpose,usage='annual')
    assert current['recipe']==old['recipe'] and current['recipe']['solver']==SOLVER
    assert current['recipe']['heads']==list(HEADS) and current['recipe']['modes']==40
    assert current['basis_identity']==old['basis_identity']
    assert current['prepared']['sha256']==old['prepared']['sha256']==prepared_sha256
    assert current['coaches']['sha256']==old['coaches']['sha256']==coaches_sha256
    assert all(current[name]['path']==old[name]['path'] for name in ('prepared','coaches'))
    assert current['valued']['sha256']==valued_sha256 and current['valued']['season']=='20222023'
    assert [row['head'] for row in old['heads']]==[row['head'] for row in current['heads']]==list(HEADS)
    assert all(row['status']=='complete' for row in old['heads'])
    assert not any(row['path'].startswith('probes/') for row in current['files']) and not (path/'probes').exists()
    heads={}
    for head in HEADS:
        prior_head=_head(previous,old,head);metadata=_head(path,current,head)
        assert prior_head['status']=='complete' and metadata['status']==next(row['status'] for row in current['heads'] if row['head']==head)
        width={'volume':1,'shape':40,'quality':41}[head]
        incoming=_records(prior_head['ledger']);priors=_records(metadata['priors']);ledger=_records(metadata['ledger'])
        assert all(row['season']=='20212022' and row['support_seasons']==['20212022'] for row in incoming.values())
        kinds=Counter();gaps=Counter();transitions=Counter()
        complete=metadata['status']=='complete'
        for key,prior in priors.items():
            last=incoming.get(key);player=prior['block'].endswith('_player')
            assert prior['last_supported']==last and prior['prior_only'] is (not prior['current_season_information'])
            expected_kind='entry' if last is None else 'carry';gap=None if last is None else 2022-int(last['season'][:4])
            assert prior['prior_kind']==expected_kind and prior['prior_anchor_season']==(None if last is None else last['season'])
            assert prior['prior_seasons']==([] if last is None else last['support_seasons'])
            assert prior['mean']==([0.]*width if last is None else last['coefficient'])
            precision=(16. if player else 100.) if last is None else (100. if player else 400.)/gap
            wanted=[precision*40.]*width
            if head!='shape':wanted[0]=precision
            assert prior['precision']==wanted
            reason='entry' if last is None else 'age_neutral';delta=[];indices=[]
            if head=='volume' and player and last is not None:
                if prior['position_group'] not in ('F','D') or prior['position_group']!=last['position_group']:reason='missing_or_changed_role'
                elif prior['age'] is None or last['age'] is None:reason='missing_age'
                else:
                    now,earlier=(prior['age']-27.)/10,(last['age']-27.)/10
                    delta=[now-earlier,now*now-earlier*earlier]
                    start=(0 if prior['block']=='attacking_player' else 4)+(0 if prior['position_group']=='F' else 2)
                    indices=[start,start+1];reason='age_carry'
            assert prior['transition_reason']==reason and prior['age_delta']==delta and prior['age_indices']==indices
            kinds[expected_kind]+=1;transitions[reason]+=1
            if gap is not None:assert gap==1;gaps[str(gap)]+=1
            if complete:
                mean=prior['prior_mean'];assert len(mean)==width and all(math.isfinite(value) for value in mean)
                if not indices:assert mean==prior['mean']
                if prior['prior_only']:assert ledger.get(key)==last
                else:
                    row=ledger[key]
                    assert row['season']=='20222023' and row['support_seasons']==prior['prior_seasons']+['20222023']
                    assert row['position_group']==prior['position_group'] and row['age']==prior['age']
                    assert len(row['coefficient'])==width and all(math.isfinite(value) for value in row['coefficient'])
        supported={key for key,row in priors.items() if row['current_season_information']}
        if complete:
            assert set(ledger)==set(incoming)|supported
            assert {key for key,row in ledger.items() if row['season']=='20222023'}==supported
            assert all(ledger[key]==row for key,row in incoming.items() if key not in supported)
            solver=metadata['solver'];assert solver['converged'] is True and solver['options']==SOLVER
            assert solver['maxfun']==15000 and solver['maxls']==20 and math.isfinite(solver['raw_gradient_inf_norm'])
            objective=metadata['objective'];assert all(math.isfinite(value) for value in objective.values())
            assert objective['total']==objective['likelihood']+objective['penalty'] and metadata['reasons']==[]
        else:assert ledger==incoming
        heads[head]=dict(status=metadata['status'],reasons=metadata['reasons'],solver=metadata['solver'],objective=metadata['objective'],
            history=dict(carry_rows=kinds['carry'],entry_rows=kinds['entry'],carry_gaps=dict(gaps),transitions=dict(transitions),
                prior_only_rows=sum(row['prior_only'] for row in priors.values()),
                absent_actors_retained=sum(key not in priors for key in incoming),supported_ledger_rows=sum(row['season']=='20222023' for row in ledger.values())),
            resources=metadata['resources'])
    complete=all(row['status']=='complete' for row in heads.values())
    return dict(kind='second-real-spatial-saved-json-history-check',status='metadata_passed_pending_root_acceptance' if complete else 'incomplete_annual',
        eligible_as_predecessor=complete,manifest=dict(path=str(path/'manifest.json'),sha256=sha256(raw).hexdigest()),
        previous=current['previous'],purpose=purpose,season='20222023',final_probes=0,heads=heads,producer_resources=current['resources'],
        basis_identity=current['basis_identity'],
        scope='bound current/previous saved json only; raw history anchors, entry/carry precision, age-transition metadata and ledger retention checked without source or numeric arrays',
        producer_owned='canonical writer owns fitted array/prior-mean equality, age-curve conditional means, centering, projections and its strict spatial read; no independent numerical claim here')


def main():
    assert re.fullmatch('[0-9a-f]{64}',PREVIOUS_SHA), 'accepted first spatial annual pin remains pending'
    began=perf_counter();stem=OUTPUT
    exit_code=int(Path(str(stem)+'-exit.txt').read_text())
    assert Path(str(stem)+'-launch-analysis-tree.txt').read_text().strip()==ANALYSIS
    assert Path(str(stem)+'-launch-analysis-status.txt').read_text()==''
    try:
        report=inspect_second_year(OUTPUT,PREVIOUS,purpose='real',previous_sha256=PREVIOUS_SHA,
            prepared_sha256='63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c',
            coaches_sha256='102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0',
            valued_sha256='296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20')
        assert (exit_code==0)==report['eligible_as_predecessor']
    except Exception as error:report=dict(kind='second-real-spatial-saved-json-history-check',status='not_accepted',eligible_as_predecessor=False,error=repr(error))
    log=Path(str(stem)+'.log').read_text();timing=re.findall(r'([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys',log)
    rss=re.findall(r'(\d+)\s+maximum resident set size',log)
    footprint=re.findall(r'(\d+)\s+peak memory footprint',log)
    report.update(recorded_utc=datetime.now(timezone.utc).isoformat(),launch=dict(exit=exit_code,
        start=Path(str(stem)+'-start.txt').read_text().strip(),finish=Path(str(stem)+'-finish.txt').read_text().strip(),
        head=Path(str(stem)+'-launch-head.txt').read_text().strip(),analysis_tree=ANALYSIS),
        whole_command=dict(timing=None if not timing else dict(zip(('wall_seconds','user_seconds','system_seconds'),map(float,timing[-1]))),
            maximum_resident_bytes=None if not rss else int(rss[-1]),peak_memory_footprint_bytes=None if not footprint else int(footprint[-1])),
        metadata_readback_wall_seconds=perf_counter()-began)
    destination=Path(str(stem)+'-saved-metadata-acceptance.json')
    with destination.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=report['status'],receipt=str(destination))))
    return 0 if report['eligible_as_predecessor'] else 1


if __name__=='__main__':raise SystemExit(main())
