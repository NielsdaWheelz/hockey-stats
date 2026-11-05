"""held exclusive selection from five root-admitted replacement spatial manifests."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
DESTINATION=ROOT/'states-selection.json'
YEARS=('20212022','20222023','20232024','20242025','20252026')
PATHS=dict(zip(YEARS,('spatial/20212022','spatial/20222023-complete-01','spatial/20232024','spatial/20242025','spatial/20252026')))
RUN_STEMS={**PATHS,'20212022':'spatial/20212022-resume-01'}
PINS={
 '20212022':'3b7b51339b5ebb00a340a3f593347adf3a72ee137ad24739abd582b8290a5509',
 '20222023':None,
 '20232024':None,
 '20242025':None,
 '20252026':None,
}
SCORES=dict(zip(YEARS,(
 '37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d',
 '296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20',
 'f13a1136c3df857a83d9f37aa10b919b64934e240515c3a8d5e2c556a778b238',
 '86e346f82d874748215f582c1a4445ab75b01358dd61d37fa4082254879c62de',
 '40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc')))
PREPARED='63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
COACHES='102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
RECIPE='04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b'
HEADS=('volume','shape','quality')


def bound_json(path,expected):
    assert type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected)
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected, f'digest differs: {path}'
    return json.loads(raw)


def main():
    if tuple(PINS)!=YEARS or not all(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) for value in PINS.values()):
        raise SystemExit('accepted spatial state pins remain withheld; no input/output access')
    assert not DESTINATION.exists(), 'selection already exists; no overwrite'
    selected=[];previous=None;basis=numerical_recipe=None;probe_bindings=[]
    for season in YEARS:
        path=ROOT/PATHS[season]/'manifest.json';manifest=bound_json(path,PINS[season])
        assert manifest['kind']=='spatial_state' and manifest['purpose']=='real' and manifest['season']==season
        for name,source,digest in (('prepared','/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json',PREPARED),('coaches','/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json',COACHES)):
            assert manifest[name]['purpose']=='real' and manifest[name]['path']==source and manifest[name]['sha256']==digest
        assert manifest['valued']['purpose']=='real' and manifest['valued']['season']==season
        assert manifest['valued']['path']==str(ROOT/'scores'/season/'manifest.json') and manifest['valued']['sha256']==SCORES[season]
        assert [row['head'] for row in manifest['heads']]==list(HEADS) and all(row['status']=='complete' for row in manifest['heads'])
        assert manifest['recipe_id']=='experimental-v1'
        if previous is None:
            assert manifest['previous'] is None
            basis,numerical_recipe=manifest['basis_identity'],manifest['recipe']
        else:
            assert manifest['previous']==dict(previous,purpose='real',usage='annual')
        assert manifest['basis_identity']==basis and manifest['recipe']==numerical_recipe
        assert Path(str(ROOT/RUN_STEMS[season])+'-launch-spatial-recipe.txt').read_text().strip()==RECIPE
        members={row['path']:row for row in manifest['files']}
        if season==YEARS[-1]:
            names={f'probes/{head}-comparison.json' for head in HEADS}
            assert {row['path'] for row in manifest['files'] if row['role']=='probe_comparison'}==names
            for head in HEADS:
                name=f'probes/{head}-comparison.json';comparison=bound_json(path.parent/name,members[name]['sha256'])
                assert comparison['status']=='passed' and comparison['failures']==[]
                probe_bindings.append(dict(path=str(path.parent/name),sha256=members[name]['sha256']))
        else:
            assert not any(name.startswith('probes/') for name in members) and not (path.parent/'probes').exists()
        previous=dict(season=season,path=str(path),sha256=PINS[season]);selected.append(previous)
    selection=dict(schema_version=1,purpose='real',prepared_sha256=PREPARED,states=selected)
    encoded=(json.dumps(selection,indent=2)+'\n').encode()
    with DESTINATION.open('xb') as output:output.write(encoded)
    assert DESTINATION.read_bytes()==encoded
    print(json.dumps(dict(path=str(DESTINATION),sha256=hashlib.sha256(encoded).hexdigest(),bytes=len(encoded),states=len(selected),
        prepared_sha256=PREPARED,coaches_sha256=COACHES,recorded_design_recipe_sha256=RECIPE,basis_identity=basis,final_probe_comparisons=probe_bindings,
        scope='root-admitted manifests, saved launch recipe records and final bound comparisons only; accepted canonical annual validation owns design contents; no design/head/array or repeated strict read')))
    return 0


if __name__=='__main__':raise SystemExit(main())
