"""temporary ordered zero/tied maxima and actual/fixture/synthetic locator controls."""
from types import SimpleNamespace
from unittest.mock import patch
import json

import numpy as np

from hockey_stats import execution
from hockey_stats.chance import TYPES
from hockey_stats.execution_design import ExecutionPredictor, SetterCandidate

branches=(SetterCandidate(None,'none',.2),SetterCandidate('9','skater',.8))
actual=ExecutionPredictor('tiny:1',0,42,False,False,{}, {},branches,{})
fixture=ExecutionPredictor('synthetic-resolution:tiny:1:shooter:9',0,8,False,False,{}, {},branches,{})
base=object();variant=object()
results=[]
for mode in ('zero','fixture','synthetic'):
    def branch(state,predictor,cells,neutralize):
        count=len(cells);g=np.full((count,2),.5);goal=np.full((count,2),.0625);continuing=goal.copy()
        delta=0.
        if state is variant:
            if predictor.key==fixture.key and mode!='zero':delta=.1
            if predictor.key.startswith('synthetic:') and mode=='synthetic':delta=.2
        g[:,1]+=delta;goal[:,1]+=delta/10;continuing[:,1]-=delta/10
        return SimpleNamespace(origin_cells=tuple(map(int,cells)),setter_branches=branches,prior_probabilities=np.array([.2,.8]),
            u=np.full(count,.5),q=np.full(count,.5),r=np.full(count,.5),g=g,
            terminal_probabilities=dict(block=np.full((count,2),.5),miss=np.full((count,2),.25),stopped=np.full((count,2),.125),goal=goal,continuing=continuing))
    locators={}
    with patch.object(execution,'execution_branch_probabilities',branch):
        comparison=execution._probability_comparison(base,variant,(actual,fixture),locators=locators)
    for name in ('u','q','r'):
        assert locators['head_maximum_changes'][name]['key']==actual.key
        assert locators['head_maximum_changes'][name]['origin_cell']==42
        assert locators['head_maximum_changes'][name]['execution']=='actual'
    maximum=locators['maximum_probability_change']
    if mode=='zero':
        assert maximum['key']==actual.key and maximum['population']=='actual' and maximum['quantity']=='u'
        assert maximum['origin_cell']==42 and maximum['setter_branch'] is None
        assert locators['terminal_maximum_changes']['goal']['setter_branch']==0
        assert locators['terminal_maximum_changes']['goal']['setter_kind']=='none'
    else:
        assert maximum['population']==mode and maximum['execution']=='actual'
        assert maximum['key']==(fixture.key if mode=='fixture' else 'synthetic:'+TYPES[0])
        assert maximum['origin_cell']==(8 if mode=='fixture' else 0)
        assert maximum['setter_branch']==1 and maximum['setter_kind']=='skater' and maximum['setter_actor_id']=='9'
    assert maximum['change']==comparison['maximum_probability_change']
    results.append(dict(mode=mode,maximum=maximum))
print(json.dumps(dict(status='passed',scope='tiny injected probability arrays; no source, objective or solve',
    first_evaluated_zero_and_tie_locations=True,actual_fixture_synthetic_and_native_origins=True,setter_axis_and_identity=True,controls=results),indent=2))
