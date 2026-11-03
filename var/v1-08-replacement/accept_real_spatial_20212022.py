"""one post-exit first-year saved-metadata read; no arrays or numerical calls."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from time import perf_counter

CAMPAIGN=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
OUTPUT=CAMPAIGN/'real/spatial/20212022'
ANALYSIS='fc716257eb118d1a091472cde4b214e8bca1f753'
SOLVER=dict(maxiter=10000,ftol=1e-15,gtol=1e-6,maxcor=10)
HEADS=('volume','shape','quality')


def inspect_first_year(path, *, purpose, prepared_sha256, coaches_sha256, valued_sha256):
    """check metadata/history/control bindings; producer owns array validation."""
    path=Path(path)
    raw=(path/'manifest.json').read_bytes();manifest=json.loads(raw)
    assert manifest['kind']=='spatial_state' and manifest['purpose']==purpose
    assert manifest['season']=='20212022' and manifest['previous'] is None
    assert manifest['prepared']['sha256']==prepared_sha256 and manifest['coaches']['sha256']==coaches_sha256
    assert manifest['valued']['sha256']==valued_sha256 and manifest['valued']['season']=='20212022'
    assert manifest['recipe']==dict(name='experimental-v1',version='positive-spatial-v1-08-1',
        heads=list(HEADS),modes=40,batch_size=4096,solver=SOLVER,
        continuation=dict(maxiter=10000,ftol=1e-16,gtol=1e-7,maxcor=10),
        support_policy='ordinary-attempt-segment-valued-two-direction-v1')
    assert [row['head'] for row in manifest['heads']]==list(HEADS)
    assert not any(row['path'].startswith('probes/') for row in manifest['files']) and not (path/'probes').exists()
    heads={}
    for descriptor in manifest['heads']:
        name=descriptor['head'];metadata=json.loads((path/f'heads/{name}.json').read_bytes())
        assert metadata['head']==name and metadata['status']==descriptor['status']
        priors=metadata['priors']
        assert all(p['prior_kind']=='entry' and p['prior_anchor_season'] is None and p['prior_seasons']==[]
            and p['last_supported'] is None and p['age_delta']==[] and p['age_indices']==[]
            and p['transition_reason']=='entry' for p in priors)
        assert all(p['prior_only'] is (not p['current_season_information']) for p in priors)
        solver=metadata['solver']
        row=dict(status=metadata['status'],reasons=metadata['reasons'],
                 entry_prior_rows=len(priors),prior_only_rows=sum(p['prior_only'] for p in priors),
                 supported_current_rows=sum(p['current_season_information'] for p in priors),
                 prior_blocks=dict(Counter(p['block'] for p in priors)),
                 supported_ledger_rows=len(metadata['ledger']),solver=solver,
                 objective=metadata['objective'],resources=metadata['resources'])
        if metadata['status']=='complete':
            assert metadata['reasons']==[] and solver['converged'] is True
            assert solver['options']==SOLVER and solver['maxfun']==15000 and solver['maxls']==20
            assert math.isfinite(solver['raw_gradient_inf_norm']) and solver['raw_gradient_inf_norm']>=0
            objective=metadata['objective']
            assert all(math.isfinite(v) for v in objective.values())
            assert objective['total']==objective['likelihood']+objective['penalty']
            supported={(p['block'],p['id'],p['subblock']) for p in priors if p['current_season_information']}
            assert supported=={(p['block'],p['id'],p['subblock']) for p in metadata['ledger']}
            assert all(p['season']=='20212022' and p['support_seasons']==['20212022'] for p in metadata['ledger'])
            assert all(all(v==0. for v in p['mean']) and all(v==0. for v in p['prior_mean']) for p in priors)
            width={'volume':1,'shape':40,'quality':41}[name]
            assert len(metadata['reference_predictor'])==width
            assert all(math.isfinite(v) for v in metadata['reference_predictor'])
            row['reference_predictor_width']=width
            row['declared_coefficient_array_contract']=descriptor['arrays']
        heads[name]=row
    coverage=json.loads((path/'coverage.json').read_bytes())
    assert coverage['purpose']==purpose and coverage['season']=='20212022'
    assert coverage['directed_included_hours']==2*coverage['physical_included_hours']
    assert coverage['attempts']==manifest['resources']['design']['event_rows']
    member_bytes=sum((path/row['path']).stat().st_size for row in manifest['files'])
    assert member_bytes==manifest['resources']['output_bytes']
    complete=all(row['status']=='complete' for row in heads.values())
    return dict(kind='first-real-spatial-saved-metadata-acceptance',
        status='metadata_passed_pending_root_acceptance' if complete else 'incomplete_annual',
        eligible_as_predecessor=complete,manifest=dict(path=str(path/'manifest.json'),sha256=sha256(raw).hexdigest()),
        purpose=purpose,season='20212022',previous=None,final_probes=0,
        bindings={name:manifest[name] for name in ('prepared','coaches','valued','basis_identity','design_identity','implementation')},
        heads=heads,head_counts=dict(Counter(row['status'] for row in heads.values())),
        coverage={name:coverage[name] for name in ('physical_included_hours','directed_included_hours','attempts',
            'origin_mass','neutral_chance_mass','supported_players','zero_information_roster_players','unassigned_gap_game_ids')},
        coverage_game_rows=len(coverage['games']),producer_resources=manifest['resources'],
        stat_only_member_bytes=member_bytes,annual_bytes_including_manifest=member_bytes+len(raw),
        numerical_risk='real final-year volume continuation budget remains open; no stopping/tolerance changes selected',
        scope='saved json metadata and stat-only inventory; zero source/game/array/strict-reader/objective/gradient/projection calls',
        producer_owned_checks='canonical fit writer invokes one strict spatial reader; numeric arrays, centers, maps and closure are not independently re-evaluated here')


def main():
    began=perf_counter();stem=OUTPUT
    exit_code=int(Path(str(stem)+'-exit.txt').read_text())
    start=Path(str(stem)+'-start.txt').read_text().strip()
    finish=Path(str(stem)+'-finish.txt').read_text().strip()
    assert start and finish
    assert Path(str(stem)+'-launch-analysis-tree.txt').read_text().strip()==ANALYSIS
    assert Path(str(stem)+'-launch-analysis-status.txt').read_text()==''
    try:
        report=inspect_first_year(OUTPUT,purpose='real',
            prepared_sha256='63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c',
            coaches_sha256='102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0',
            valued_sha256='37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d')
        assert (exit_code==0)==report['eligible_as_predecessor']
    except Exception as error:
        report=dict(kind='first-real-spatial-saved-metadata-acceptance',status='not_accepted',
                    eligible_as_predecessor=False,error=repr(error),scope='saved json/stat-only readback failure; no numerical/source pass')
    log=Path(str(stem)+'.log').read_text()
    timing=re.findall(r'([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys',log)
    rss=re.findall(r'(\d+)\s+maximum resident set size',log)
    footprint=re.findall(r'(\d+)\s+peak memory footprint',log)
    report.update(recorded_utc=datetime.now(timezone.utc).isoformat(),launch=dict(exit=exit_code,start=start,finish=finish,
        head=Path(str(stem)+'-launch-head.txt').read_text().strip(),analysis_tree=ANALYSIS),
        whole_command=dict(timing=None if not timing else dict(zip(('wall_seconds','user_seconds','system_seconds'),map(float,timing[-1]))),
            maximum_resident_bytes=None if not rss else int(rss[-1]),peak_memory_footprint_bytes=None if not footprint else int(footprint[-1])),
        metadata_readback_wall_seconds=perf_counter()-began)
    destination=CAMPAIGN/'real/spatial-20212022-saved-metadata-acceptance.json'
    with destination.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=report['status'],receipt=str(destination))))
    return 0 if report['eligible_as_predecessor'] else 1


if __name__=='__main__':raise SystemExit(main())
