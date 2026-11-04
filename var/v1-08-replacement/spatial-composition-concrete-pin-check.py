"""concrete candidate pin/guard checks; every artifact and reader is a tiny stub."""
from contextlib import ExitStack
from copy import deepcopy
import ast
import difflib
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from hockey_stats import spatial_composition as original, spatial_state
from hockey_stats.captures import InputContractError

here=Path(__file__).resolve().parent
source_path=Path(original.__file__);source=source_path.read_text()
assert sha256(source.encode()).hexdigest()=='bcd6f56a26e38b9bd96f8d5ee801a1909de2b37c5096dd1a664bdf4082540416'
new_path='/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real/execution-results'
base_digest='3441f784c11eb6a8eda38800806b8e4dc68e06e8587c91db24c5dffaadae4347'
replacement_scores=(
 '37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d',
 '296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20',
 'f13a1136c3df857a83d9f37aa10b919b64934e240515c3a8d5e2c556a778b238',
 '86e346f82d874748215f582c1a4445ab75b01358dd61d37fa4082254879c62de',
 '40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc')
edits=[(str(original.ACCEPTED_RESULTS),new_path),(original.ACCEPTED_RESULTS_SHA256,base_digest),*zip(original.ACCEPTED_VALUED.values(),replacement_scores)]
held=source
for before,after in edits:
 assert held.count(before)==1
 held=held.replace(before,after)
start=source.index('ACCEPTED_RESULTS =');end=source.index('\n\n\n@dataclass',start)
assert source[:start]==held[:start] and source[end:]==held[held.index('\n\n\n@dataclass',start):]
assert len(edits)==7
expected=''.join(difflib.unified_diff(source.splitlines(keepends=True),held.splitlines(keepends=True),fromfile='a/analysis/src/hockey_stats/spatial_composition.py',tofile='b/analysis/src/hockey_stats/spatial_composition.py'))
assert (here/'spatial-composition-pin-cutover.patch').read_text()==expected
before_ast,after_ast=ast.parse(source),ast.parse(held)
ast_changes=[]
for before,after in zip(before_ast.body,after_ast.body,strict=True):
 if ast.dump(before)!=ast.dump(after):
  assert isinstance(before,ast.Assign) and isinstance(after,ast.Assign)
  assert len(before.targets)==len(after.targets)==1 and ast.dump(before.targets[0])==ast.dump(after.targets[0])
  ast_changes.append(before.targets[0].id)
  before.value=after.value
assert ast_changes==['ACCEPTED_RESULTS','ACCEPTED_RESULTS_SHA256','ACCEPTED_VALUED']
assert ast.dump(before_ast)==ast.dump(after_ast)
protected=json.loads((here/'spatial-composition-pin-preparation-held.json').read_text())['protected_unchanged'][:3]
for member in protected:assert sha256(Path(member['path']).read_bytes()).hexdigest()==member['sha256']
candidate=ModuleType('hockey_stats._spatial_composition_concrete_candidate');candidate.__package__='hockey_stats'
sys.modules[candidate.__name__]=candidate
candidate_bytes=held.encode()
exec(compile(candidate_bytes,'<concrete pin-only candidate>','exec'),candidate.__dict__)
assert str(candidate.ACCEPTED_RESULTS)==new_path and candidate.ACCEPTED_RESULTS_SHA256==base_digest
assert list(candidate.ACCEPTED_VALUED.values())==list(replacement_scores)

base=Path(new_path);years=list(original.YEARS);scores=dict(zip(years,replacement_scores))
methods=[dict(method_id=f'execution-v1-06-{year}',evidence=[dict(sha256=scores[year])],inputs=[dict(role='coaches',sha256='c'*64)]) for year in years]
supports=[dict(support_id='fixed-support',value='unchanged')]
def encoded(rows):return b''.join((json.dumps(row)+'\n').encode() for row in rows)
method_bytes,support_bytes=encoded(methods),encoded(supports)
accepted=dict(purpose='real',seasons=years,observed_bindings={'fixed':'facts'},prepared_sha256='p'*64,
 catalogs=dict(people={'fixed':'people'},sources={'fixed':'sources'},methods=dict(path='catalogs/methods.jsonl',sha256=sha256(method_bytes).hexdigest(),rows=len(methods)),supports=dict(path='catalogs/supports.jsonl',sha256=sha256(support_bytes).hexdigest(),rows=1)),
 families=[dict(season=year,family=family,availability='provided',revision='replacement' if family=='execution' else 'fixed') for year in years for family in ('execution','descriptive')]+[dict(season=years[-1],family='goalie',availability='not_computed')])
blobs={base/'manifest.json':json.dumps(accepted).encode(),base/'catalogs/methods.jsonl':method_bytes,base/'catalogs/supports.jsonl':support_bytes}
digests={original.ACCEPTED_RESULTS/'manifest.json':base_digest,base/'manifest.json':base_digest,base/'catalogs/methods.jsonl':sha256(method_bytes).hexdigest(),base/'catalogs/supports.jsonl':sha256(support_bytes).hexdigest()}
selection_path=Path('/synthetic/spatial-selection.json');states={};items=[]
for i,year in enumerate(years):
 root=Path('/synthetic/spatial')/year;digest='3b7b51339b5ebb00a340a3f593347adf3a72ee137ad24739abd582b8290a5509' if i==0 else str(i)*64
 previous=None if i==0 else dict(path=items[-1]['path'],sha256=items[-1]['sha256'])
 manifest=dict(season=year,prepared=dict(sha256='p'*64),coaches=dict(sha256='c'*64),valued=dict(sha256=scores[year]),previous=previous,
  recipe_id='fixed-recipe',recipe={'fixed':'recipe04a9'},basis_identity={'fixed':'basis'},producer=dict(analysis_tree='fc716257eb118d1a091472cde4b214e8bca1f753'))
 states[root/'manifest.json']=SimpleNamespace(path=root,manifest=manifest,heads={head:dict(status='complete') for head in ('volume','shape','quality')},
  probes=dict(status='passed',heads=dict.fromkeys(('volume','shape','quality'))) if i==4 else None,projections=[],projection_arrays={},adjustments=[])
 items.append(dict(season=year,path=str(root/'manifest.json'),sha256=digest));digests[root/'manifest.json']=digest
selection=dict(schema_version=1,purpose='real',prepared_sha256='p'*64,states=items)
blobs[selection_path]=json.dumps(selection).encode()
def results(manifest):return SimpleNamespace(manifest=manifest,catalogs=dict(method={row['method_id']:row for row in methods},support={row['support_id']:row for row in supports}))

def io_stubs():
 stack=ExitStack()
 stack.enter_context(patch.object(Path,'read_bytes',lambda path:blobs[path]))
 stack.enter_context(patch.object(Path,'open',lambda path,*args,**kwargs:BytesIO(blobs[path])))
 stack.enter_context(patch.object(Path,'is_dir',lambda path:False))
 stack.enter_context(patch.object(original.publication,'member_path',lambda directory,member:directory/member['path']))
 for module in (original,candidate):
  stack.enter_context(patch.object(module,'identity',lambda path:dict(sha256=digests[Path(path)])))
 stack.enter_context(patch.object(spatial_state,'read_spatial_state',lambda path,purpose:states[Path(path)]))
 return stack

def refused(function):
 try:function()
 except InputContractError:return
 else:raise AssertionError('incompatible source/target was admitted')

with io_stubs():
 candidate._accepted_source(results(deepcopy(accepted)))
 digests[base/'manifest.json']=original.ACCEPTED_RESULTS_SHA256
 refused(lambda:candidate._accepted_source(results(deepcopy(accepted))))
 digests[base/'manifest.json']=base_digest
 selected,annuals=candidate._states(selection_path,results(deepcopy(accepted)))
 assert selected==selection and list(annuals)==years
 descendant=deepcopy(accepted);descendant['families'][-1].update(availability='provided',revision='independently-added-goalie')
 candidate._accepted_source(results(descendant))
 original_source=deepcopy(accepted)
 for row in original_source['families']:
  if row['family']=='execution':row['revision']='original-execution'
 refused(lambda:candidate._accepted_source(results(original_source)))
 changed=deepcopy(accepted);changed['families'][1]['revision']='changed-provided-descriptive'
 refused(lambda:candidate._accepted_source(results(changed)))
 for year,old_score in original.ACCEPTED_VALUED.items():
  state=states[Path('/synthetic/spatial')/year/'manifest.json'];state.manifest['valued']['sha256']=old_score
  refused(lambda:candidate._states(selection_path,results(deepcopy(accepted))))
  state.manifest['valued']['sha256']=scores[year]
 fixture=deepcopy(accepted);fixture['purpose']='fixture';fixture['seasons']=[years[0]]
 fixture_selection=dict(selection,purpose='fixture',states=items[:1]);blobs[selection_path]=json.dumps(fixture_selection).encode()
 first=states[Path(items[0]['path'])];first.manifest['valued']['sha256']='f'*64
 fixture_result=results(fixture);fixture_result.catalogs['method'][f'execution-v1-06-{years[0]}']['evidence']=[dict(sha256='f'*64)]
 candidate._accepted_source(fixture_result);original._accepted_source(fixture_result)
 a,b=candidate._states(selection_path,fixture_result);c,d=original._states(selection_path,fixture_result)
 assert a==c and list(b)==list(d) and b[years[0]].manifest==d[years[0]].manifest
print(json.dumps(dict(status='passed',scope='existing compositor guards with mocked IO and spatial reader; no real/fixture artifact, arrays, objective, source, fit or production reader call',
 seven_literal_pin_delta=True,changed_ast_assignments=ast_changes,all_other_source_bytes_identical=True,protected_numerical_files=protected,
 candidate_sha256=sha256(candidate_bytes).hexdigest(),actual_accepted_base_sha256=base_digest,old_base_digest_refused=True,replacement_source_and_all_five_targets_pass=True,compatible_descendant_pass=True,
 original_execution_family_refused=True,changed_provided_nonowned_family_refused=True,all_five_original_targets_refused=True,fixture_path_unchanged=True,
 accepted_first_state_identity_with_prior_analysis_tree_compatible=True,base_digest='actual accepted digest; mocked bytes only; no saved result read'),indent=2))
