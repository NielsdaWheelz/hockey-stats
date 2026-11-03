"""one source reconstruction and frozen u capture, then bounded diagnosis."""
import argparse
from dataclasses import replace
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import subprocess
from time import perf_counter
from unittest.mock import patch

import numpy as np

from hockey_stats import execution_design as ed
from hockey_stats.analysis_data import read_prepared
from hockey_stats.artifacts import require, write_json
from hockey_stats.chance_cli import identity
from hockey_stats.execution_fit import annual_priors, prior_mean
from hockey_stats.execution_inputs import write_u_bundle, load_u_bundle
from hockey_stats.execution_state import read_execution_state

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
RUN=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
OUTPUT=RUN/'real/u-repair-01'
PINS={
    'prepared':(Path('/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json'),'63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'),
    'coaches':(Path('/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json'),'102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'),
    'previous':(RUN/'real/execution/20242025/manifest.json','1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe'),
    'donor':(RUN/'real/execution-final-02/20252026/manifest.json','cb075d5e59aea61589411e4573db7192c45fddd8265a807c2c39c2084b504e22'),
    'source_report':(RUN/'real/fit-20252026-final-02-source-check.json','59f4b00827ea736f0a374ba6f32a1ce7003f5f9ab7a131b84d5e4971f0624e9d'),
}
OBSERVER_SHA='ef4995e579855950cab475cc2ac237f6ce22538429cc1f04d675b48838a6fca4'
spec=importlib.util.spec_from_file_location('u_capture_source_observer',HERE/'consumed_start_check.py')
observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)


def source_design(prepared, coaches, expected):
    """reuse the frozen source oracle; derive other head populations from labels."""
    print('source pass started',flush=True)
    check=observer.StartCheck()
    original_context=ed._feature_context;original_head=ed._head_design
    original_read=ed.read_prepared_game;games_read=0
    def read_game(*args,**kwargs):
        nonlocal games_read
        result=original_read(*args,**kwargs)
        games_read+=1
        if games_read%100==0:print(f'prepared games read: {games_read}',flush=True)
        return result
    def context(attempt,game,shooter,goalie,strength,coaches,team_rest,history):
        before=observer.encoded(observer.responses(attempt))
        result=original_context(attempt,game,shooter,goalie,strength,coaches,team_rest,history)
        if not check.closed:
            require(before==observer.encoded(observer.responses(attempt)),'capture source response/membership mutated')
            check.observe(result,attempt,game,shooter,history)
        return result
    def head(name,predictors,labels,*args,**kwargs):
        require(name=='u','u capture requested another training head')
        check.close()
        for selected in ed.HEADS:
            rows=[i for i,label in enumerate(labels) if label[selected] is not None]
            check.head(dict(head=selected,rows=rows,keys=[predictors[i].key for i in rows]))
        report=check.report()
        for key,value in report.items():
            if key not in ('observer_seconds','head_admission'):
                require(observer.encoded(value)==observer.encoded(expected[key]),'capture source report differs before matrix construction: '+key)
        print('source parity accepted before u builder',flush=True)
        result=original_head(name,predictors,labels,*args,**kwargs)
        require(result['keys']==[predictors[i].key for i,label in enumerate(labels) if label['u'] is not None], 'u canonical head changed physical order')
        check.head(result)
        print(f"u builder complete: {len(result['keys'])} physical rows",flush=True)
        return result
    with patch.object(ed,'_feature_context',context),patch.object(ed,'_head_design',head),patch.object(ed,'read_prepared_game',read_game):
        design=ed.prepare_execution(prepared,coaches,ed.RECIPE,'20252026',training_heads=('u',))
    check.head_admission=design.coverage['heads']
    report=check.report()
    require(report['head_admission']==expected['head_admission'],'capture head admission differs')
    return design,report


def frozen_probes(design, donor, selector):
    """restore frozen keys and source projections without invoking selection."""
    by_key={predictor.key:predictor for predictor in design.predictors}
    require(all(key in by_key for key in selector['keys']),'frozen actual probe missing')
    probes=[by_key[key] for key in selector['keys']]
    # source projections use donor actor support metadata, never q/r/g matrices.
    witness_view=replace(design,heads=donor.heads)
    for frozen in selector['fixture_witnesses']:
        requirement=next(row for row in selector['requirements'] if row['key']==frozen['key'] and row['disposition']=='fixture')
        parts=requirement['requirement'].split(':')
        block,actor=(parts[2],parts[3]) if parts[0]=='sparse' else (None,None)
        built=ed.build_resolution_witness(witness_view,requirement['requirement'],block,actor)
        require(built is not None,'frozen source projection unavailable')
        predictor,attribution=built
        require(predictor.key==frozen['key'] and observer.encoded(attribution)==observer.encoded(frozen['attribution']),
                'frozen fixture projection identity differs')
        probes.append(predictor)
    require(len({probe.key for probe in probes})==len(probes),'frozen probes duplicate a key')
    return tuple(probes)


def capture(prepared, coaches, previous, donor, expected, output, bindings):
    """write numerical inputs without evaluating the objective."""
    design,report=source_design(prepared,coaches,expected)
    require(list(design.heads)==['u'],'capture built extra training heads')
    require(design.prepared==donor.manifest['prepared'] and design.coaches==donor.manifest['coaches']
            and design.training_cutoff==donor.manifest['training_cutoff'],'capture source references differ from donor')
    require({key:value for key,value in design.coverage.items() if key!='optional_features'}
            =={key:value for key,value in donor.coverage.items() if key!='optional_features'},'capture common population/coverage differs')
    head=design.heads['u'];saved=donor.heads['u'];incoming=previous.heads['u']['ledger']
    require(head['design']==saved['design'] and design.coverage['optional_features']['u']==donor.coverage['optional_features']['u'],
            'capture u layout/transforms/support differ')
    require(saved['origin']==dict(cells=656,distance_ft=20.,direction_strength=4.,law='uniform-release-forward-kernel'),
            'donor origin law differs')
    included=[row for row in donor.coverage['attempts'] if row['heads']['u']['included']]
    require(head['keys']==[row['key'] for row in included]
            and np.array_equal(head['target'],np.asarray([row['heads']['u']['target'] for row in included],dtype=np.float64)),
            'capture source keys/targets differ from donor')
    actors=annual_priors(head,incoming);initial=donor.arrays['u']['coefficients']
    require([{key:actor[key] for key in saved['actors'][i]} for i,actor in enumerate(actors)]==saved['actors'],
            'capture u actor axes/support differ')
    priors=[]
    last={(row['block'],str(row['id'])):row for row in incoming}
    for actor in actors:
        prior={key:actor.get(key) for key in ('block','id','mean','precision','age_delta','age_indices','transition_reason')}
        prior.update(prior_mean=prior_mean(actor,initial),last_supported=last.get((actor['block'],str(actor['id']))))
        priors.append(prior)
    require(priors==saved['priors'],'capture incoming conditional priors differ')
    selector=json.loads((donor.path.parent/'resolution/baseline.json').read_text())['selector']
    probes=frozen_probes(design,donor,selector)
    write_json(output/'source-check.json',report)
    metadata=dict(purpose=design.purpose,season=design.season,recipe=ed.RECIPE,
        prepared=design.prepared,coaches=design.coaches,training_cutoff=design.training_cutoff,
        incoming_ledger=incoming,bindings=bindings,donor=identity(donor.path),previous=identity(previous.path),
        source_check=identity(output/'source-check.json'),source_context_sha256=report['source_context_sha256'],
        source_response_sha256=report['source_response_sha256'],coefficient_names=head['design']['coefficient_names'],
        baseline_head=saved,coverage=dict(heads=donor.coverage['heads'],member=identity(donor.path.parent/'coverage.json')),
        origin=saved['origin'],anchor_objective=saved['resolution']['comparison']['base_objective'],
        anchor_gradient_max=saved['resolution']['comparison']['base_gradient_max'])
    path=write_u_bundle(output/'inputs',head,actors=actors,initial=initial,metadata=metadata,selector=selector,probes=probes)
    print(f'u input bundle written: {path}',flush=True)
    return path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--expected-commit',required=True)
    parser.add_argument('--expected-analysis-tree',required=True)
    parser.add_argument('--expected-capture-sha256',required=True)
    parser.add_argument('--expected-diagnosis-sha256',required=True)
    args=parser.parse_args()
    started=perf_counter()
    require(Path.cwd().resolve()==WORK,'capture must run in isolated v1-08 checkout')
    require(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==args.expected_commit,'capture commit differs')
    require(subprocess.check_output(['git','rev-parse','HEAD:analysis'],text=True).strip()==args.expected_analysis_tree,'capture analysis tree differs')
    require(not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','analysis'],text=True).strip(),'capture analysis tree is dirty')
    require(identity(Path(__file__))['sha256']==args.expected_capture_sha256,'capture source differs')
    require(identity(HERE/'consumed_start_check.py')['sha256']==OBSERVER_SHA,'frozen source observer differs')
    diagnosis_identity=identity(HERE/'diagnose_execution_u.py')
    require(diagnosis_identity['sha256']==args.expected_diagnosis_sha256,'diagnosis source differs')
    require(ed.RECIPE['sha256']=='47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674','capture recipe differs')
    require(not OUTPUT.exists(),'u capture campaign output already exists')
    bindings={}
    for name,(path,sha) in PINS.items():
        bindings[name]=identity(path)
        require(bindings[name]['sha256']==sha,'capture input identity differs: '+name)
    expected=json.loads(PINS['source_report'][0].read_text())
    require(expected['source_context_sha256']=='f96ee4a0eadeb2f5caa44db999c71b9ad0e6a178b8a3812f9895019dcdb065a3'
            and expected['source_response_sha256']=='63e224a6d8ac06729882bd05b1dcd817df49d39000fb8559817e0e1d01feef04',
            'frozen source report fingerprints differ')
    previous=read_execution_state(PINS['previous'][0],'real');donor=read_execution_state(PINS['donor'][0],'real')
    prepared=read_prepared(PINS['prepared'][0],'real')
    require(donor.manifest['season']=='20252026' and previous.manifest['season']=='20242025'
            and donor.manifest['previous']['path']==str(previous.path)
            and donor.manifest['previous']['sha256']==bindings['previous']['sha256']
            and donor.manifest['recipe']==previous.manifest['recipe']==ed.RECIPE
            and all(donor.manifest[name]['path']==previous.manifest[name]['path']==str(PINS[name][0])
                    and donor.manifest[name]['sha256']==previous.manifest[name]['sha256']==bindings[name]['sha256']
                    for name in ('prepared','coaches')),
            'capture donor/history/source lineage differs')
    require(all(donor.heads[name]['status']==previous.heads[name]['status']=='complete' for name in ed.HEADS)
            and donor.heads['u']['resolution']['status']=='failed'
            and all(donor.heads[name]['resolution']['status']=='passed' for name in ('q','r','g')),
            'capture donor dispositions differ')
    require(np.float64(donor.heads['u']['resolution']['comparison']['base_objective']).tobytes()==np.float64(69668.42305740231).tobytes()
            and np.float64(donor.heads['u']['resolution']['comparison']['base_gradient_max']).tobytes()==np.float64(0.002770559377087478).tobytes(),
            'donor saved u scalar anchors differ')
    OUTPUT.mkdir()
    write_json(OUTPUT/'capture-start.json',dict(bindings=bindings,actual_launch_head=args.expected_commit,
        reviewed_analysis_tree=args.expected_analysis_tree,capture=identity(Path(__file__)),diagnosis=diagnosis_identity,
        source_observer=identity(HERE/'consumed_start_check.py')))
    try:
        path=capture(prepared,PINS['coaches'][0],previous,donor,expected,OUTPUT,bindings)
        gc.collect()
        reload_started=perf_counter();loaded=load_u_bundle(path)
        require(loaded['metadata']['bindings']==bindings and loaded['metadata']['incoming_ledger']==previous.heads['u']['ledger'],
                'reloaded capture lineage differs')
        print(f'u input bundle reloaded: {path}',flush=True)
        manifest=json.loads(path.read_text())
        write_json(OUTPUT/'capture-reloaded.json',dict(status='serialized and reloaded; scalar anchors pending bounded diagnosis',
            bundle=identity(path),payload_bytes=manifest['payload_bytes'],physical_rows=len(loaded['design']['target']),
            batches=len(manifest['batches']),batch_order='original',fixed_csr_shape=list(loaded['design']['fixed_matrix'].shape),
            fixed_csr_dtypes={name:getattr(loaded['design']['fixed_matrix'],name).dtype.str for name in ('data','indices','indptr')},
            capture_reload_wall_seconds=perf_counter()-started,reload_wall_seconds=perf_counter()-reload_started,
            process_peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,objective_evaluations=0,
            reload_scope='first structural reload; released before bounded diagnosis performs its own reload and scalar anchors'))
        del loaded
        gc.collect()
    except BaseException as error:
        write_json(OUTPUT/'capture-failure.json',dict(status='unusable capture; no automatic rebuild',error_type=type(error).__name__,error=str(error)))
        raise
    from diagnose_execution_u import diagnose
    report=diagnose(path,OUTPUT/'diagnosis')
    print(json.dumps(dict(status=report['status'],bundle=str(path),diagnosis=str(OUTPUT/'diagnosis'))))
    return 0 if report['status']=='arithmetic_repair_permitted' else 1


if __name__=='__main__':raise SystemExit(main())
