"""generated-only checks for additive spatial exchange finalization."""
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis/src'))
from hockey_stats import spatial_composition as s

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(s.publication.json_bytes(value)+b'\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()

with tempfile.TemporaryDirectory() as temp:
    root=Path(temp).resolve();result=root/'result';result.mkdir();base=root/'source';base.mkdir()
    base_sha=write(base/'manifest.json',{'purpose':'real','seasons':list(s.YEARS[2:]),'observed_bindings':[],'prepared_sha256':'a'*64})
    states={};previous=None
    for year in s.YEARS:
        directory=root/'states'/year;directory.mkdir(parents=True)
        support=directory/'support.json';support_sha=write(support,{'year':year})
        members=[dict(role='coefficient_support',path='support.json',sha256=support_sha)]
        if year==s.YEARS[-1]:
            for name in ('baseline','volume-comparison','shape-comparison','quality-comparison'):
                path=directory/'probes'/f'{name}.json';digest=write(path,{'status':'failed' if name=='volume-comparison' else 'passed'})
                members.append(dict(path=str(path.relative_to(directory)),sha256=digest,role='probe'))
        manifest=dict(season=year,purpose='real',prepared={'sha256':'a'*64},coaches={'sha256':'b'*64},valued={'sha256':s.ACCEPTED_VALUED[year]},
                      previous=previous,heads=[{'head':h,'status':'complete'} for h in ('volume','shape','quality')],recipe_id='experimental-v1',recipe={'version':'v1'},basis_identity={'test':1},design_identity='c'*64,training_cutoff='2026-01-01',files=members)
        digest=write(directory/'manifest.json',manifest);states[year]=s._AnnualProjection(directory,manifest,[],{},[])
        previous=dict(season=year,path=str(directory/'manifest.json'),sha256=digest,purpose='real',usage='annual')
    selection={'schema_version':1,'purpose':'real','prepared_sha256':'a'*64,'states':[dict(season=y,path=str(states[y].path/'manifest.json'),sha256=s.identity(states[y].path/'manifest.json')['sha256']) for y in s.YEARS]}
    selection_path=root/'selection.json';write(selection_path,selection)
    methods=[]
    for year in s.YEARS[2:]:
        receipt=result/f'{year}-spatial-composition.json';receipt_sha=write(receipt,{'season':year})
        methods.append(s._method(year,states[year],states,'real',base_sha,dict(uri=str(receipt),sha256=receipt_sha)))
    methods.append(dict(method_id='z-nonspatial',arbitrary='untouched'))
    old_bytes=b''.join(s.publication.json_bytes(row)+b'\n' for row in methods);(result/'methods.jsonl').write_bytes(old_bytes)
    donor={'purpose':'real','seasons':list(s.YEARS[2:]),'observed_bindings':[],'prepared_sha256':'a'*64,'producer':{'git_commit':None,'git_dirty':None,'python_version':'test'},
           'catalogs':{'methods':dict(path='methods.jsonl',sha256=hashlib.sha256(old_bytes).hexdigest(),rows=len(methods))},'families':[]}
    donor_sha=write(result/'manifest.json.incomplete',donor);original=(result/'manifest.json.incomplete').read_bytes()
    final=states[s.YEARS[-1]].path
    admission={'season':s.YEARS[-1], 'warning':'precision warning', 'baseline':s.identity(final/'probes/baseline.json'),
               'precision':{'status':'failed','comparisons':{h:s.identity(final/'probes'/f'{h}-comparison.json')|{'status':'failed' if h=='volume' else 'passed'} for h in ('volume','shape','quality')}},
               'evidence':[dict(uri='evidence',sha256='d'*64)],'receipt':dict(uri='receipt',sha256='e'*64),
               'actual_context_review':dict(uri='context',sha256='f'*64),'actual_context_warnings':{'20242025':'context 24','20252026':'context 25'}}
    write(root/'admission.json', {'synthetic':True})
    calls=[]
    def strict(directory,filename):
        calls.append((directory,filename));assert (directory/filename).exists()
    with patch.object(s,'ACCEPTED_RESULTS',base),patch.object(s,'ACCEPTED_RESULTS_SHA256',base_sha),patch.object(s,'_product_admission',return_value=admission),patch.object(s.publication,'_read_results',side_effect=strict),patch.object(s,'implementation_identity',return_value=donor['producer']):
        try: s.complete_results(result,'0'*64,selection_path,root/'admission.json')
        except Exception: pass
        else: raise AssertionError('wrong donor accepted')
        assert not (result/'methods-complete-01.jsonl').exists()
        wrong=dict(admission);wrong['precision']=dict(admission['precision']);wrong['precision']['comparisons']=dict(admission['precision']['comparisons'])
        wrong['precision']['comparisons']['volume']=dict(wrong['precision']['comparisons']['volume'])|{'status':'passed'}
        with patch.object(s,'_product_admission',return_value=wrong):
            try: s.complete_results(result,donor_sha,selection_path,root/'admission.json')
            except Exception: pass
            else: raise AssertionError('wrong status accepted')
        assert not (result/'methods-complete-01.jsonl').exists()
        with patch.object(s.publication,'_read_results',side_effect=ValueError('generated strict failure')):
            try: s.complete_results(result,donor_sha,selection_path,root/'admission.json')
            except ValueError: pass
            else: raise AssertionError('strict failure accepted')
        assert not (result/'manifest.json').exists() and (result/'manifest.json.incomplete').read_bytes()==original
        (result/'methods-complete-01.jsonl').unlink();(result/'manifest-complete-01.json.incomplete').unlink()
        s.complete_results(result,donor_sha,selection_path,root/'admission.json')
        assert calls==[(result,'manifest-complete-01.json.incomplete')]
        assert (result/'manifest.json').exists() and (result/'manifest.json.incomplete').read_bytes()==original and (result/'methods.jsonl').read_bytes()==old_bytes
        assert (result/'methods-complete-01.jsonl').read_bytes().splitlines()[-1]==old_bytes.splitlines()[-1]
        assert json.loads((result/'manifest.json').read_text())['catalogs']['methods']['path']=='methods-complete-01.jsonl'
        try: s.complete_results(result,donor_sha,selection_path,root/'admission.json')
        except Exception: pass
        else: raise AssertionError('repeat accepted')
print('generated additive completion and repeat refusal passed; strict reader replaced by spy')
