"""held post-exit publication metadata binding; no semantic/strict-reader replay."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, re, resource, sqlite3, subprocess, time, uuid

release = 'released-after-publisher-exit-and-source-review'
project = Path('/Users/nnandal/Documents/code/hockey-stats-v1-08')
campaign = Path('/Volumes/Expansion/hockey-stats/runs/execution-spatial-replacement-20261031-01')
real = campaign / 'real'
candidate = real / 'candidate'
results_sha = 'a40ca1c0291579b773db22294f26998f154309b2b65926f00f901331ef0b17d5'
observed_sha = '5b6e3f0b8ae736260070549677a59bbf648ebab9a916729333eeb577611331e9'
prepared_sha = '63bd286135626baf2718582ddd0c9bcc8ea551f60f5e47ee48c5929b521de56c'
analysis_tree = '52bcae1c68161d4424cec672837e783eaeead673'
launch_head = 'b8cd0b29b22261f94645cdd3051706e1b884c6f2'
command_sha = '3f4e199326736bbd4b5326a87b4f33d8d7560381039c707d922235d273bfd6de'
command = project / 'var/v1-08-replacement/real-spatial-publish-command.sh.held'
observed = Path('/Volumes/Expansion/hockey-stats/runs/execution-v1-06-20261026-01/real/observed-selection.json')
years = ['20232024', '20242025', '20252026']
corpus_hashes = ['92392c80b145d72c3be759a94b8113db04a7e8d26a4404e1e15a40119db6a414', '46208ef0830949de4faf1e6695f052c9fdbc23bca5b86fa045c3552d3d467639', '8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43']


def main():
    assert release == 'released-after-publisher-exit-and-source-review', 'root post-exit release withheld; no file/database/git access'
    started = time.perf_counter()
    reads = []
    def read(path, expected=None):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert expected is None or digest == expected, path
        reads.append(dict(path=str(path), sha256=digest, bytes=len(raw)))
        return raw
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=project, text=True).strip()
    stamps = {suffix: read(real / ('publish-' + suffix + '.txt')).decode().strip() for suffix in ['exit', 'start', 'finish', 'launch-head', 'launch-analysis-tree', 'launch-analysis-status', 'launch-command-sha256', 'launch-inputs-sha256']}
    assert stamps['exit'] == '0', 'publisher must exit successfully before inspection'
    assert stamps['launch-head'] == launch_head and stamps['launch-analysis-tree'] == analysis_tree
    assert stamps['launch-analysis-status'] == ''
    assert datetime.fromisoformat(stamps['start'].replace('Z', '+00:00')) <= datetime.fromisoformat(stamps['finish'].replace('Z', '+00:00'))
    shell_pid = int(read(real / 'publish-shell.pid').decode().strip()); assert shell_pid > 0
    read(command, command_sha)
    assert stamps['launch-command-sha256'].split(maxsplit=1) == [command_sha, str(command)]
    input_lines = [line.split(maxsplit=1) for line in stamps['launch-inputs-sha256'].splitlines()]
    assert input_lines == [[observed_sha, str(observed)], [results_sha, str(real / 'results/manifest.json')]]
    assert git('rev-parse', launch_head + ':analysis') == analysis_tree
    assert git('rev-parse', 'HEAD:analysis') == analysis_tree
    assert git('status', '--porcelain', '--untracked-files=all', '--', 'analysis') == ''
    verification_bytes = read(candidate / 'verification.json')
    verification = json.loads(verification_bytes)
    assert (verification['schema_version'], verification['kind'], verification['purpose']) == (1, 'player_analysis_publication_verification', 'real')
    publication_id = verification['publication_id']; assert str(uuid.UUID(publication_id)) == publication_id
    assert verification['scientific_admission'] == 'not_performed'
    assert verification['checks'] == dict(integrity='passed', foreign_keys='passed', read_back='passed', per_season_conservation='passed')
    producer = verification['producer']
    assert producer['git_dirty'] is False
    producer_tree = git('rev-parse', producer['git_commit'] + ':analysis')
    assert producer_tree == analysis_tree
    # attribution is to the producing commit's analysis subtree; later doc-only heads are valid.
    selection_bytes = read(candidate / 'selection.json', observed_sha)
    assert read(observed, observed_sha) == selection_bytes
    selection = json.loads(selection_bytes)
    assert selection['schema_version'] == 1 and selection['purpose'] == 'real'
    assert [(r['season'], r['sha256']) for r in selection['corpora']] == list(zip(years, corpus_hashes))
    assert verification['selection'] == dict(path=str(observed), sha256=observed_sha, bytes=len(selection_bytes), copy='selection.json', document=selection)
    manifest_bytes = read(candidate / 'results/manifest.json', results_sha)
    assert read(real / 'results/manifest.json', results_sha) == manifest_bytes
    manifest = json.loads(manifest_bytes)
    assert (manifest['schema_version'], manifest['kind'], manifest['purpose'], manifest['seasons'], manifest['prepared_sha256']) == (2, 'player_analysis_results', 'real', years, prepared_sha)
    assert [(r['season'], r['corpus_sha256']) for r in manifest['observed_bindings']] == list(zip(years, corpus_hashes))
    family_headers = [{key:r[key] for key in ['season', 'family', 'availability', 'explanation']} for r in manifest['families']]
    assert verification['results'] == dict(manifest_sha256=results_sha, copy='results', prepared_sha256=prepared_sha, families=family_headers)
    assert [(r['season'], r['availability']) for r in family_headers if r['family'] == 'spatial'] == [(y, 'provided') for y in years]
    assert [r['season'] for r in verification['seasons']] == years
    season_receipts = []
    for year, corpus_sha, row in zip(years, corpus_hashes, verification['seasons']):
        assert row['corpus_sha256'] == corpus_sha
        assert row['receipt']['path'] == 'seasons/' + year + '/verification.json'
        assert re.fullmatch('[a-f0-9]{64}', row['receipt']['sha256'])
        checks = row['checks']
        assert checks['read_back'] == 'passed' and checks['conservation'] == 'passed'
        assert all(isinstance(checks[k], int) and checks[k] >= 0 for k in ['physical_seconds', 'player_seconds', 'physical_attempts', 'player_attempts_for', 'player_attempts_against', 'personal_physical_seconds', 'personal_player_seconds', 'deployment_pairs', 'teammate_pair_seconds', 'opponent_pair_seconds'])
        assert checks['player_seconds'] == 10 * checks['physical_seconds']
        assert checks['player_attempts_for'] == checks['player_attempts_against'] == 5 * checks['physical_attempts']
        assert checks['personal_player_seconds'] == 10 * checks['personal_physical_seconds']
        assert checks['teammate_pair_seconds'] == 20 * checks['physical_seconds'] and checks['opponent_pair_seconds'] == 25 * checks['physical_seconds']
        assert row['coverage']['inventory_games'] == row['spatial_coverage']['inventory_games'] == 1312
        path = candidate / row['receipt']['path']
        stat = path.stat()
        season_receipts.append(dict(season=year, path=str(path), sha256=row['receipt']['sha256'], bytes=stat.st_size, mtime_ns=stat.st_mtime_ns, checks=checks, digest_scope='publisher-owned exact digest/checks from top verification; existence/stat only here; no independent season-byte proof'))
    log = read(real / 'publish.log').decode()
    assert 'publication ' + publication_id + ': real' in log
    wall = re.search(r'^\s*([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys\s*$', log, re.M)
    rss = re.search(r'^\s*(\d+)\s+maximum resident set size\s*$', log, re.M)
    footprint = re.search(r'^\s*(\d+)\s+peak memory footprint\s*$', log, re.M)
    assert wall and rss and footprint
    process_cost = dict(wall_seconds=float(wall[1]), user_seconds=float(wall[2]), system_seconds=float(wall[3]), peak_rss_bytes=int(rss[1]), peak_memory_footprint_bytes=int(footprint[1]))
    cost = verification['cost']
    assert all(isinstance(cost[k], (int,float)) and math.isfinite(cost[k]) and cost[k] > 0 for k in ['wall_seconds', 'peak_rss_bytes', 'consumed_bytes', 'database_bytes'])
    assert all(math.isfinite(value) and value >= 0 for value in process_cost.values())
    assert cost['peak_rss_bytes'] <= process_cost['peak_rss_bytes']
    database = candidate / 'player-analysis.sqlite'
    assert verification['database']['path'] == str(database) and re.fullmatch('[a-f0-9]{64}', verification['database']['sha256'])
    stat = database.stat()
    assert stat.st_size == cost['database_bytes']
    absent = [candidate / 'player-analysis.sqlite.incomplete', *[candidate / (name + suffix) for name in ['player-analysis.sqlite', 'player-analysis.sqlite.incomplete'] for suffix in ['-wal', '-shm', '-journal']]]
    assert all(not p.exists() for p in absent)
    connection = sqlite3.connect('file:' + str(database) + '?mode=ro&immutable=1', uri=True)
    connection.row_factory = sqlite3.Row
    headers = connection.execute('select * from publication').fetchall()
    assert len(headers) == 1
    header = dict(headers[0]); connection.close()
    assert (header['id'], header['schema_version'], header['kind'], header['publication_id'], header['purpose'], header['game_type'], header['prepared_sha256']) == (1, 8, 'player_analysis', publication_id, 'real', 2, prepared_sha)
    assert json.loads(header['producer_json']) == producer
    assert (header['population_version'], header['personal_population_version'], header['spatial_population_version'], header['spatial_display_version']) == ('matched_attempts_v2', 'matched_personal_credits_v2', 'matched_unblocked_locations_v2', 'rect5_gaussian10_v1')
    assert (database.stat().st_size, database.stat().st_mtime_ns) == (stat.st_size, stat.st_mtime_ns)
    result = dict(kind='replacement-real-publication-post-exit-metadata-check', status='passed metadata/provenance/header binding; root candidate acceptance and semantic/api/native checks remain separate', recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                  publication_id=publication_id, purpose='real', schema_version=8, launch_head=launch_head, producer=producer, producer_analysis_tree=producer_tree, analysis_tree=analysis_tree, current_head=git('rev-parse','HEAD'), launch_stamps=stamps, shell_pid=shell_pid,
                  database=dict(path=str(database), bytes=stat.st_size, mtime_ns=stat.st_mtime_ns, accepted_publisher_sha256=verification['database']['sha256'], digest_scope='publisher single completed hash reused; zero extra database hash passes', header=header),
                  results_manifest_sha256=results_sha, prepared_sha256=prepared_sha, observed_selection_sha256=observed_sha,
                  publisher_checks=verification['checks'], seasons=season_receipts, measured_process_resources=process_cost, publisher_cost=cost, publisher_cost_scope=verification['cost_scope'],
                  checked_small_files=reads, small_file_read_bytes=sum(r['bytes'] for r in reads), season_receipt_byte_reads=0, database_hash_passes=0, database_queries=['select * from publication'],
                  source=dict(path=str(Path(__file__)), sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                  checker_resources=dict(wall_seconds=time.perf_counter()-started, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                  scope='small top verification, copied/canonical manifest and selection, launch stamps/log/command hashes; local git provenance, season receipt existence/stat, ordinary database stat and one immutable publication-header query only; publisher owns strict integrity/FK/readback/conservation and season digest checks',
                  limits=['no season receipt content/digest replay or consumed-source path read', 'no database hash, integrity/FK/schema-catalog/strict-reader replay, bulk row audit, map/array/source-game/model access', 'no API/browser/export/server/build/activation/serving-file mutation', 'actual source-to-API/CSV semantic equality remains separately assigned; metadata success is not scientific admission'])
    output = real / 'publication-post-exit-metadata-01.json'
    with output.open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(status='passed', output=str(output),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),publication_id=publication_id,database=result['database'] | {'header':'recorded in receipt'},resources=result['checker_resources'])))


if __name__ == '__main__':
    main()
