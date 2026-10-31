"""one authorized exclusive selection write from five fixed accepted manifests."""
import hashlib
import json
from pathlib import Path
import subprocess

WORK = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
ROOT = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/fixture')
DESTINATION = ROOT / 'states-selection.json'
PINS = (
    ('20212022', '91ccca92782e4c156cb6ebe55952b6ded7c20d865ce4efcc323267b674d11465', '78e029e06cfb50ebdc247117faeb3849459e291be2267c250a9c15858dac7d60'),
    ('20222023', '8444b539b8cf6bc61ac4ca78ab5c4dec9e4e885a1452b72da24fdf9ae1eccba1', '69bf4a4dede3a7ca3f0c0cca9897caaadd2330d40a2a2acbd5c902cf6484bdad'),
    ('20232024', '000b36e473a22b458acfefe4331ca88fe6780bba370fe0834841b4143e31ef4e', 'fb1d1ad1f3c5437eb050da0ebdc22cd6fca972af8756aa53c452c60d340df604'),
    ('20242025', 'c9fe5fb27c13dda61c8062104b8c977bd462931170f023d2fa48834a04b56416', '1f6ac613aa064692ce842c9a0c6bf144e7081c1cd762aff5143b741e7ab8e149'),
    ('20252026', 'af7cf9250b55d6a33e9badee037bd230604795c399846464c0853c0aba6d8b6a', '80f61f0dc1941042c5bf1e3488fdaaed9cc0fb303670f6780558ff11a603072a'),
)
PREPARED = '603ee00dfe069c99eb5fda3bda9f5d60ea9969fa3820a1df3b5bfcf16cefb7df'
COACHES = 'd876634925f7abaabc5e1300efd3a7837511a74628dd98943ffc682b69d7602c'
RECIPE = '04a9c15d868a764744c796fb82065f2d95d2efa27914f12ecb871806ccc91e8b'
ANALYSIS = 'c2412ac713b8c60e808dd71771f0812224b94439'
assert not DESTINATION.exists(), 'selection already exists; no overwrite'
selected, previous, basis, numerical_recipe, design_recipe = [], None, None, None, None
for season, expected, valued in PINS:
    path = ROOT / 'spatial' / season / 'manifest.json'
    payload = path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected, (season, 'manifest differs')
    manifest = json.loads(payload)
    assert manifest['purpose'] == 'fixture' and manifest['season'] == season
    assert manifest['prepared']['purpose'] == manifest['coaches']['purpose'] == 'fixture'
    assert manifest['prepared']['sha256'] == PREPARED and manifest['coaches']['sha256'] == COACHES
    assert manifest['valued']['sha256'] == valued and manifest['valued']['path'] == str(ROOT / 'scores' / season / 'manifest.json')
    assert [h['head'] for h in manifest['heads']] == ['volume', 'shape', 'quality']
    assert all(h['status'] == 'complete' for h in manifest['heads'])
    if previous is None:
        assert manifest['previous'] is None
        basis, numerical_recipe = manifest['basis_identity'], manifest['recipe']
    else:
        assert manifest['previous']['path'] == previous['path'] and manifest['previous']['sha256'] == previous['sha256']
        assert manifest['previous']['season'] == previous['season'] and manifest['previous']['usage'] == 'annual'
    assert manifest['basis_identity'] == basis and manifest['recipe'] == numerical_recipe
    design_bytes = (path.parent / 'design.json').read_bytes()
    binding = next(row for row in manifest['files'] if row['role'] == 'design')
    assert binding['path'] == 'design.json' and hashlib.sha256(design_bytes).hexdigest() == binding['sha256']
    design = json.loads(design_bytes)['definition']
    assert design['recipe']['sha256'] == RECIPE and design['basis_identity'] == basis
    if design_recipe is None:
        design_recipe = design['recipe']
    assert design['recipe'] == design_recipe
    assert subprocess.check_output(['git', 'rev-parse', manifest['implementation']['git_commit']+':analysis'], cwd=WORK, text=True).strip() == ANALYSIS
    if season == '20252026':
        for head in ('volume', 'shape', 'quality'):
            comparison = json.loads((path.parent / f'probes/{head}-comparison.json').read_bytes())
            assert comparison['status'] == 'passed' and not comparison['failures']
    previous = dict(season=season, path=str(path), sha256=expected)
    selected.append(previous)
selection = dict(schema_version=1, purpose='fixture', prepared_sha256=PREPARED, states=selected)
encoded = (json.dumps(selection, indent=2)+'\n').encode()
with DESTINATION.open('xb') as output:
    output.write(encoded)
assert DESTINATION.read_bytes() == encoded
print(json.dumps(dict(path=str(DESTINATION), sha256=hashlib.sha256(encoded).hexdigest(), bytes=len(encoded), states=len(selected), prepared_sha256=PREPARED, coaches_sha256=COACHES, design_recipe_sha256=RECIPE, basis_identity=basis, analysis_tree=ANALYSIS, array_reads=0, repeated_strict_reads=0), indent=2))
