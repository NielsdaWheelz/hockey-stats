"""held fixed real selection; pending pins refuse before input/output access."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
EXPECTED = {
    '20212022': '37263bfc650a06f09adc2c64588c19d3b61cd1e9cdb65dc2ba71a8f88ed5ca8d',
    '20222023': '296ae0173fb1256ddb91d14eee5a917d76c3e88f92cc3556a8647b1f10a8da20',
    '20232024': 'f13a1136c3df857a83d9f37aa10b919b64934e240515c3a8d5e2c556a778b238',
    '20242025': '86e346f82d874748215f582c1a4445ab75b01358dd61d37fa4082254879c62de',
    '20252026': '40e23b35ac9c8458229b076150366960c4a25d7a92ae028d2b45dc39c89104fc',
}
STATES = {
    '20212022': '7c740083469c9a16edf6d73552ea18b89425a52b2ea7f4deeea41f79a5043e61',
    '20222023': 'eb52909e32d051b205e9cd6ccdcb8227371202d469a52357cfb926c94cff599c',
    '20232024': 'dd8b638dd8eb3e8af25722f53f633202b5fa28ef3ce81ec45bb9a180d9f09bfa',
    '20242025': '1ba2c8af310d12239d6cabb89ee6cc92b6b98bd95e6834b4f44e303802a44cfe',
    '20252026': '59e3432df70366c4e058007f4396be7737f76afada4fad96c84896dd12a6f276',
}
FINAL_STATE = ROOT / 'u-repair-01/assembled-01/20252026/manifest.json'
FINAL_ACCEPTANCE = dict(path='/Users/nnandal/Documents/code/hockey-stats-v1-08/docs/research/spatial-v1-08/receipts/real-final-score-completion.json',
                        sha256='8f9163b53c07c264ef59d651bf4860b04333b70a61ec4a19abc7bd4fecfa1953')
PREPARED = '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
COACHES = '102bca4c24bbcf2ef5eb207274f13ba78030f5bef7e551b77c553d741ed7f0f0'
RECIPE = '47691110ac34bf7d63cdc32664335bd6579a5953545f0cefa8ebf0257bf88674'


def main():
    assert type(FINAL_ACCEPTANCE) is dict and set(FINAL_ACCEPTANCE) == {'path', 'sha256'}, 'accepted final score evidence remains pending'
    assert (type(FINAL_ACCEPTANCE['path']) is str and Path(FINAL_ACCEPTANCE['path']).is_absolute()
            and type(FINAL_ACCEPTANCE['sha256']) is str and re.fullmatch('[0-9a-f]{64}', FINAL_ACCEPTANCE['sha256'])), 'accepted final score evidence remains pending'
    assert all(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) for value in (*EXPECTED.values(), *STATES.values()))
    assert hashlib.sha256(Path(FINAL_ACCEPTANCE['path']).read_bytes()).hexdigest() == FINAL_ACCEPTANCE['sha256']
    destination = ROOT / 'scores-selection.json'
    assert not destination.exists()
    items, previous, recipe = [], None, None
    for season, digest in EXPECTED.items():
        path = ROOT / 'scores' / season / 'manifest.json'
        payload = path.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == digest
        manifest = json.loads(payload)
        assert manifest['purpose'] == 'real' and manifest['season'] == season
        assert manifest['prepared']['sha256'] == PREPARED and manifest['coaches']['sha256'] == COACHES
        assert manifest['prepared']['path'] == '/Volumes/Expansion/hockey-stats/prepared/evidence-v1-01-02/manifest.json'
        assert manifest['coaches']['path'] == '/Volumes/Expansion/hockey-stats/runs/coaches-v1-02-20261022-01/coaches-01/coaches.json'
        state_ref = dict(path=str(FINAL_STATE if season == '20252026' else ROOT / 'execution' / season / 'manifest.json'), sha256=STATES[season])
        assert all(manifest['state'][name] == value for name, value in state_ref.items())
        assert manifest['state']['previous'] == previous
        previous = state_ref
        if recipe is None:
            recipe = manifest['recipe']
        assert manifest['recipe'] == recipe and recipe['sha256'] == RECIPE
        assert recipe['name'] == 'experimental-v1' and recipe['version'] == 'execution-v1-05-2'
        assert manifest['scoring_version'] == 'execution-v1-06-1'
        assert manifest['numerical_resolution']['status'] == ('passed' if season == '20252026' else 'not_applicable')
        items.append(dict(season=season, path=str(path), sha256=digest))
    selection = dict(schema_version=1, purpose='real', prepared_sha256=PREPARED, scores=items)
    payload = (json.dumps(selection, indent=2)+'\n').encode()
    with destination.open('xb') as stream:
        stream.write(payload)
    assert destination.read_bytes() == payload
    print(json.dumps(dict(path=str(destination), bytes=len(payload), sha256=hashlib.sha256(destination.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
