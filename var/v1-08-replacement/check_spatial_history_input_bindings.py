"""tiny annual-header controls for the corrected saved-history precondition."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path

path=Path(__file__).with_name('independent_spatial_history_audit.py')
source=path.read_bytes();tree=ast.parse(source)
helper=next((node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='check_input_bindings'),None)
if helper is None:
    audit=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='audit')
    statement=next(node for node in audit.body if isinstance(node,ast.Assert) and ast.unparse(node.test)=="all((manifest[n] == old[n] for n in ('prepared', 'coaches')))")
    helper=ast.FunctionDef(name='check_input_bindings',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='manifest'),ast.arg(arg='old')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[statement],decorator_list=[])
namespace={};exec(compile(ast.fix_missing_locations(ast.Module(body=[helper],type_ignores=[])),str(path),'exec'),namespace)
check=namespace['check_input_bindings']

def annual(season):
    games=[season[:4]+'020001',season[:4]+'020002']
    return dict(season=season,purpose='real',prepared=dict(purpose='real',path='/prepared/manifest.json',sha256='a'*64,members=[dict(kind='people',season=season,game_id=None,path=season+'/people.json',sha256='b'*64),*[dict(kind='game',season=season,game_id=game,path=season+'/'+game+'.json',sha256='c'*64) for game in games]]),coaches=dict(purpose='real',path='/coaches/manifest.json',sha256='d'*64,selected_game_ids=games))

old=annual('20212022');current=annual('20222023')
check(current,old)
refused=[]
for name in ('prepared_path','prepared_sha256','prepared_purpose','coaches_path','coaches_sha256','coaches_purpose','own_purpose','cross_season_member','cross_season_game','duplicate_member','missing_people','wrong_member_kind','duplicate_selected','missing_selected','extra_selected','previous_membership'):
    now=deepcopy(current);before=deepcopy(old)
    if name.startswith(('prepared_','coaches_')):
        binding,field=name.split('_',1);now[binding][field]='wrong'
    elif name=='own_purpose':now['purpose']='fixture'
    elif name=='cross_season_member':now['prepared']['members'][0]['season']=old['season']
    elif name=='cross_season_game':now['coaches']['selected_game_ids'][0]='2021020001';now['prepared']['members'][1]['game_id']='2021020001'
    elif name=='duplicate_member':now['prepared']['members'].append(deepcopy(now['prepared']['members'][1]))
    elif name=='missing_people':now['prepared']['members'].pop(0)
    elif name=='wrong_member_kind':now['prepared']['members'][0]['kind']='reference'
    elif name=='duplicate_selected':now['coaches']['selected_game_ids'].append(now['coaches']['selected_game_ids'][0])
    elif name=='missing_selected':now['coaches']['selected_game_ids'].pop()
    elif name=='extra_selected':now['coaches']['selected_game_ids'].append('2022020003')
    elif name=='previous_membership':before['prepared']['members'][1]['season']=current['season']
    try:check(now,before)
    except AssertionError:refused.append(name)
    else:raise AssertionError('accepted '+name)
print(json.dumps(dict(status='passed',audit_sha256=hashlib.sha256(source).hexdigest(),legitimate_distinct_seasons_passed=True,refused=refused,actual_artifact_reads=0,production_imports=0,numerical_calls=0),indent=2))
