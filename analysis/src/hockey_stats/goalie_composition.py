"""replace the goalie family while preserving the checked combined exchange."""

from copy import deepcopy
import hashlib
from pathlib import Path
from time import perf_counter

from . import analysis_publication as publication
from .analysis_data import read_prepared
from .artifacts import implementation_identity, require, resources, write_json
from .captures import strict_json
from .chance_cli import identity, output_path

YEARS = ('20212022','20222023','20232024','20242025','20252026')
ACCEPTED_ROOT = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01/real')
ACCEPTED_RESULTS_SHA256 = 'a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5'
ACCEPTED_SCORES_SHA256 = '588376316a8b4d5311a1677bb3f1419f3754854f25dd2a28e09e3e8c000f9450'


def _accepted_source(results):
    """pin combined spatial/execution facts, permitting compatible added families."""
    if results.manifest['purpose'] != 'real':
        return None
    path = ACCEPTED_ROOT/'results'/'manifest.json'
    require(identity(path)['sha256'] == ACCEPTED_RESULTS_SHA256, 'accepted combined result manifest digest differs')
    accepted = strict_json(path.read_bytes())
    for field in ('purpose','seasons','observed_bindings','prepared_sha256'):
        require(results.manifest[field] == accepted[field], 'accepted combined '+field+' differs')
    require(results.manifest['catalogs']['people'] == accepted['catalogs']['people'], 'accepted combined person identities differ')
    families = {(row['season'],row['family']):row for row in results.manifest['families']}
    for row in accepted['families']:
        if row['family'] != 'goalie' and row['availability'] == 'provided':
            require(families[row['season'],row['family']] == row, 'accepted non-goalie '+row['family']+' differs')
    for name,catalog,key in (('sources','source','source_id'),('methods','method','method_id'),('supports','support','support_id')):
        member = accepted['catalogs'][name]
        source = publication.member_path(path.parent,member)
        require(identity(source)['sha256'] == member['sha256'], 'accepted combined '+name+' digest differs')
        with source.open('rb') as stream:
            for line in stream:
                row = strict_json(line)
                require(results.catalogs[catalog].get(row[key]) == row, 'accepted combined '+key+' differs')
    selection_path = ACCEPTED_ROOT/'scores-selection.json'
    require(identity(selection_path)['sha256'] == ACCEPTED_SCORES_SHA256, 'accepted execution selection digest differs')
    return {row['season']:row['sha256'] for row in strict_json(selection_path.read_bytes())['scores']}


def _annuals(selection_path, existing, prepared, base_scores):
    from .goalie_scores import read_goalie_scores

    selection = strict_json(Path(selection_path).read_bytes())
    publication.fields(selection,('schema_version','purpose','prepared_sha256','scores'))
    require(type(selection['schema_version']) is int and selection['schema_version'] == 1
            and selection['purpose'] == existing.manifest['purpose']
            and selection['prepared_sha256'] == existing.manifest['prepared_sha256'], 'goalie selection identity differs')
    require(type(selection['scores']) is list and selection['scores'], 'missing goalie score selection')
    years = []
    for selected in selection['scores']:
        publication.fields(selected,('season','path','sha256')); publication.digest(selected['sha256'])
        require(selected['season'] in YEARS and type(selected['path']) is str and Path(selected['path']).is_absolute(), 'invalid selected goalie score locator/year')
        years.append(selected['season'])
    require(years == sorted(set(years)) and years == list(YEARS[YEARS.index(years[0]):YEARS.index(years[-1])+1]), 'goalie score years must be unique ordered and consecutive')
    require(selection['purpose'] != 'real' or years == list(YEARS), 'real goalie composition requires five annual scores')
    require(set(existing.manifest['seasons']) <= set(years), 'goalie scores omit a displayed season')
    annuals = {}
    for selected in selection['scores']:
        path = Path(selected['path'])
        path = path/'manifest.json' if path.is_dir() else path
        require(identity(path)['sha256'] == selected['sha256'], 'selected goalie score digest differs')
        annual = read_goalie_scores(path,selection['purpose'])
        manifest = annual.manifest
        year = selected['season']
        require(manifest['season'] == year and manifest['prepared']['sha256'] == selection['prepared_sha256'], 'goalie annual preparation/year differs')
        require(manifest['prepared']['members'] == [row for row in prepared['files'] if row['season'] == year and row['kind'] in ('game','people')], 'goalie annual selected preparation members differ')
        if base_scores is not None:
            require(manifest['base_scores']['sha256'] == base_scores[year], 'goalie annual target differs from corrected execution')
        annuals[year] = annual
    for left,right in zip(years,years[1:]):
        before,after = annuals[left].manifest,annuals[right].manifest
        require(after['state']['previous'] == {key:before['state'][key] for key in ('path','sha256')}, 'goalie score history differs')
        require(after['base_state']['previous'] == {key:before['base_state'][key] for key in ('path','sha256')}, 'goalie base-state history differs')
        require(after['recipe'] == before['recipe'] and all(after['coaches'][field] == before['coaches'][field]
                for field in ('path','sha256','purpose')), 'goalie annual recipe/coaches differ')
    require(annuals[years[0]].manifest['state']['previous'] is None, 'first selected goalie year has undeclared history')
    for year in existing.manifest['seasons']:
        annual = annuals[year]
        method = existing.catalogs['method'].get('execution-v1-06-'+year)
        require(method is not None and any(row['sha256'] == annual.manifest['base_scores']['sha256'] for row in method['evidence']), 'goalie target is not bound to combined execution')
        require(any(row['role'] == 'coaches' and row['sha256'] == annual.manifest['coaches']['sha256'] for row in method['inputs']), 'goalie/combined execution coaches differ')
        public = {pid:person for (season,pid),person in existing.people.items() if season == year and person['kind'] == 'goalie'}
        saved = annual.people
        require(set(public) == set(saved), 'goalie score/publication person population differs')
        for pid,person in public.items():
            require(all(saved[pid][field] == person[field] for field in person if field not in ('source','identity_support'))
                    and saved[pid]['identity_support']['problems'] == person['identity_support']['problems'], 'goalie score/publication identity facts differ')
    return selection,annuals


def compose_goalie(prepared, combined_results, annual_goalie_scores, output):
    """copy inherited bytes, replace only goalie rows, and complete one strict exchange."""
    started = perf_counter()
    output = output_path(str(output),[])
    existing = publication.read_results(Path(combined_results))
    prepared = read_prepared(prepared,existing.manifest['purpose'])
    require(identity(prepared.directory/'manifest.json')['sha256'] == existing.manifest['prepared_sha256'], 'goalie composition preparation differs')
    prepared_selection = strict_json((prepared.directory/'selection.json').read_bytes())
    corpus = {row['season']:row['sha256'] for row in prepared_selection['seasons']}
    require(all(corpus.get(row['season']) == row['corpus_sha256'] for row in existing.manifest['observed_bindings']), 'goalie composition observed/source binding differs')
    base_scores = _accepted_source(existing)
    selection,annuals = _annuals(annual_goalie_scores,existing,prepared,base_scores)
    require(not any(output.is_relative_to(root) for root in
        [existing.directory,prepared.directory,*[annual.path.parent for annual in annuals.values()]]), 'goalie output must be outside input directories')
    if existing.manifest['purpose'] == 'real':
        require(output.is_relative_to('/Volumes/Expansion/hockey-stats'), 'expensive real outputs must be external')
    output.mkdir()
    manifest = deepcopy(existing.manifest)
    manifest['producer'] = implementation_identity()
    inherited,owned = [],[]

    def copy_member(member):
        source = publication.member_path(existing.directory,member)
        destination = output/member['path']
        destination.parent.mkdir(parents=True,exist_ok=True)
        sha = hashlib.sha256()
        with source.open('rb') as src,destination.open('xb') as dst:
            while chunk := src.read(1024*1024):
                dst.write(chunk); sha.update(chunk)
        require(sha.hexdigest() == member['sha256'], 'inherited member digest differs during goalie copy')
        inherited.append(dict(member))

    def write_member(path,rows,table):
        sha,count,previous = hashlib.sha256(),0,None
        with (output/path).open('xb') as destination:
            for row in rows:
                key = tuple(row[field] for field in publication.KEYS[table])
                require(previous is None or previous < key, 'goalie '+table+' rows duplicate or unordered')
                encoded = publication.json_bytes(row)+b'\n'
                destination.write(encoded); sha.update(encoded)
                previous,count = key,count+1
        member = dict(path=path,sha256=sha.hexdigest(),rows=count)
        owned.append(dict(member))
        return member

    for record in manifest['families']:
        if record['family'] != 'goalie':
            for member in record['tables'].values(): copy_member(member)
            continue
        year = record['season']
        annual = annuals[year]
        record.update(availability='provided',explanation=None,tables={table:write_member(
            year+'-goalie-'+table+'.jsonl',annual.rows(table),table) for table in publication.FAMILY_TABLES['goalie']})
    copy_member(manifest['catalogs']['people'])
    for table,catalog,key in (('sources','source','source_id'),('methods','method','method_id'),('supports','support','support_id')):
        additions = {}
        for year in manifest['seasons']:
            for row in annuals[year].catalogs[table]:
                previous = additions.get(row[key],existing.catalogs[catalog].get(row[key]))
                require(previous is None or previous == row, 'conflicting reused goalie '+key)
                if row[key] not in existing.catalogs[catalog]: additions[row[key]] = row
        if not additions:
            copy_member(manifest['catalogs'][table])
            continue
        source_member = existing.manifest['catalogs'][table]
        source_path = publication.member_path(existing.directory,source_member)
        pending = iter(sorted(additions))
        current = next(pending,None)
        path = 'goalie-'+table+'.jsonl'
        sha,count = hashlib.sha256(),0
        with source_path.open('rb') as source,(output/path).open('xb') as destination:
            for line in source:
                original = strict_json(line)
                while current is not None and current < original[key]:
                    encoded = publication.json_bytes(additions[current])+b'\n'
                    destination.write(encoded); sha.update(encoded); count += 1
                    current = next(pending,None)
                destination.write(line); sha.update(line); count += 1
            while current is not None:
                encoded = publication.json_bytes(additions[current])+b'\n'
                destination.write(encoded); sha.update(encoded); count += 1
                current = next(pending,None)
        manifest['catalogs'][table] = dict(path=path,sha256=sha.hexdigest(),rows=count)
        owned.append(dict(manifest['catalogs'][table]))
    write_json(output/'manifest.json.incomplete',manifest)
    read_started = perf_counter()
    publication._read_results(output,'manifest.json.incomplete')
    strict_read_seconds = perf_counter()-read_started
    (output/'manifest.json.incomplete').rename(output/'manifest.json')
    write_json(output/'goalie-composition.json',dict(schema_version=1,kind='goalie-composition',
        source_results=identity(existing.directory/'manifest.json'),selection=identity(Path(annual_goalie_scores).resolve()),
        output=identity(output/'manifest.json'),inherited_members=inherited,goalie_members=owned,
        source_families=existing.manifest['families'],output_families=manifest['families'],
        preserved='every non-goalie family and person row; existing source/method/support definitions remain exact',
        resources=dict(resources(started),strict_read_wall_seconds=strict_read_seconds,
            output_member_bytes=sum((output/member['path']).stat().st_size for member in [*inherited,*owned]))))
    return manifest
