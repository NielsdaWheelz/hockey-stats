"""bind exact reported coach names to dated inventory games, entirely offline."""

import argparse
from collections import Counter
from datetime import date, datetime
import math
from pathlib import Path
import re
import resource
import sys
import time
from typing import Literal, TypedDict
from urllib.parse import urlsplit

from .artifacts import implementation_identity, require, write_json
from .captures import InputContractError, read_supplemental_capture, strict_json
from .chance_cli import identity, output_path, read_json
from .cli import Once
from .corpus_inputs import load_corpus

Purpose = Literal['real', 'fixture']
Side = Literal['home', 'away']


class CaptureSelection(TypedDict):
    directory: str
    receipt_sha256: str


class CaptureDisposition(TypedDict):
    game_id: str
    capture: CaptureSelection | None
    not_acquired_reason: str | None
    explanation: str | None


class SeasonSelection(TypedDict):
    season: str
    corpus_manifest: str
    sha256: str
    game_ids: list[str] | None
    captures: list[CaptureDisposition]


class Selection(TypedDict):
    schema_version: int
    purpose: Purpose
    seasons: list[SeasonSelection]


class Occurrence(TypedDict):
    season: str
    game_id: str
    side: Side


class Anchor(Occurrence):
    receipt_sha256: str
    body_sha256: str
    pointer: str


class CoachIdentity(TypedDict):
    coach_id: str
    display_name: str


class Alias(TypedDict):
    reported_name: str
    applies_to: list[Occurrence] | None
    coach_id: str | None
    explanation: str
    anchors: list[Anchor]


class IdentityTable(TypedDict):
    schema_version: int
    purpose: Purpose
    coaches: list[CoachIdentity]
    aliases: list[Alias]


class Assignment(TypedDict):
    reported_name: str | None
    coach_id: str | None
    status: str
    reason: str | None
    source_pointer: str
    identity_entry: int | None


class Source(TypedDict):
    capture_path: str | None
    receipt_sha256: str | None
    body_sha256: str | None
    requested_at: str | None
    http_status: int | None
    capture_status: str
    parse_status: str
    explanation: str | None


class ContextCheck(TypedDict):
    pointer: str
    reported_value: object
    status: str


class Game(TypedDict):
    season: str
    game_id: str
    game_date: str
    home_team_id: int
    away_team_id: int
    source: Source
    context_checks: list[ContextCheck]
    home: Assignment
    away: Assignment


class Coaches(TypedDict):
    schema_version: int
    kind: str
    purpose: Purpose
    interpretation_id: str
    implementation: dict
    selection: dict
    identities: dict
    coverage: dict
    corpora: list[dict]
    games: list[Game]
    resources: dict


SEASONS = ('20212022', '20222023', '20232024', '20242025', '20252026')
REAL_CORPORA = {
    '20212022': ('/Volumes/Expansion/hockey-stats/corpora/03m-20261010-02/20212022/corpus.json', '30eb12b290ccd9af9eae7ade8c7dcd5f285129b52b646eec3fced3e2628badc8'),
    '20222023': ('/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20222023/corpus.json', '735c741115725e7c4fe8a28782f352c787895db5eea2123b2b7ec27b4db1e02a'),
    '20232024': ('/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20232024/corpus.json', '92392c80b145d72c3be759a94b8113db04a7e8d26a4404e1e15a40119db6a414'),
    '20242025': ('/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20242025/corpus.json', '46208ef0830949de4faf1e6695f052c9fdbc23bca5b86fa045c3552d3d467639'),
    '20252026': ('/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20252026/corpus.json', '8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43'),
}
CAPTURE_STATUSES = ('not_acquired', 'captured_2xx', 'captured_non2xx', 'incomplete')
PARSE_STATUSES = ('unavailable', 'parsed', 'malformed', 'identity_conflict')
ASSIGNMENT_STATUSES = ('resolved', 'source_unavailable', 'source_malformed', 'source_identity_conflict',
                       'coach_not_reported', 'coach_malformed', 'identity_unreviewed', 'identity_unresolved')
SIDES = ('home', 'away')
# candidate report-link paths; first usable original must pin these before expansion.
REPORT_POINTERS = tuple('/gameReports/' + field for field in (
    'gameSummary', 'eventSummary', 'playByPlay', 'faceoffSummary', 'faceoffComparison',
    'rosters', 'shotSummary', 'shiftChart', 'toiAway', 'toiHome'))
CONTEXT_POINTERS = ('/id', '/gameId', '/season', '/gameType', '/gameDate',
                    '/gameInfo/homeTeam/id', '/gameInfo/awayTeam/id', '/gameReports') + REPORT_POINTERS


def _closed(value, fields, label):
    require(type(value) is dict and set(value) == set(fields.split()), f'{label}: expected exact fields {fields}')


def _text(value):
    return type(value) is str and bool(value.strip())


def _digest(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'invalid sha256')


def _game_id(value, season):
    require(type(value) is str and re.fullmatch('[0-9]{4}02[0-9]{4}', value) is not None
            and value[:4] == season[:4], 'invalid regular-season game identity')


def _path(value, base):
    require(_text(value), 'path must be nonblank')
    return (base / value).resolve()


def _absolute(value):
    require(_text(value) and Path(value).is_absolute() and str(Path(value).resolve()) == value,
            'expected resolved absolute path')


def _date(value):
    try:
        return type(value) is str and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _utc(value):
    require(type(value) is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z', value),
            'expected receipt utc timestamp')
    try:
        datetime.fromisoformat(value)
    except ValueError as error:
        raise InputContractError('invalid receipt calendar timestamp') from error


def _selection(document, original_path, purpose):
    _closed(document, 'schema_version purpose seasons', 'selection')
    require(type(document['schema_version']) is int and document['schema_version'] == 1
            and document['purpose'] == purpose and purpose in ('real', 'fixture'), 'selection schema/purpose differs')
    seasons = document['seasons']
    require(type(seasons) is list and bool(seasons), 'selection seasons must be nonempty')
    result = []
    seen = []
    for row in seasons:
        _closed(row, 'season corpus_manifest sha256 game_ids captures', 'season selection')
        season = row['season']
        require(type(season) is str and season in SEASONS and season not in seen, 'unknown/duplicate season')
        seen.append(season)
        manifest = _path(row['corpus_manifest'], original_path.parent)
        _digest(row['sha256'])
        game_ids = row['game_ids']
        require(game_ids is None or purpose == 'fixture' and type(game_ids) is list and bool(game_ids),
                'explicit game ids require a nonempty fixture selection')
        if game_ids is not None:
            for gid in game_ids:
                _game_id(gid, season)
            require(len(set(game_ids)) == len(game_ids), 'duplicate selected game')
        if purpose == 'real':
            require((str(manifest), row['sha256']) == REAL_CORPORA[season], 'real corpus identity differs')
        require(type(row['captures']) is list and bool(row['captures']), 'capture dispositions must be nonempty')
        dispositions = {}
        for disposition in row['captures']:
            _closed(disposition, 'game_id capture not_acquired_reason explanation', 'capture disposition')
            gid = disposition['game_id']
            _game_id(gid, season)
            require(gid not in dispositions, 'duplicate capture game')
            selected = disposition['capture']
            if selected is None:
                require(type(disposition['not_acquired_reason']) is str and disposition['not_acquired_reason'] in ('not_requested', 'probe_deferred')
                        and _text(disposition['explanation']), 'unacquired disposition needs a reason and explanation')
            else:
                _closed(selected, 'directory receipt_sha256', 'selected capture')
                _path(selected['directory'], original_path.parent)
                _digest(selected['receipt_sha256'])
                require(disposition['not_acquired_reason'] is None and disposition['explanation'] is None,
                        'selected capture cannot also be unacquired')
            dispositions[gid] = disposition
        if game_ids is not None:
            require(set(dispositions) == set(game_ids), 'capture keys differ from selected games')
        result.append((row, manifest, dispositions))
    require(seen == sorted(seen) and (purpose == 'fixture' or tuple(seen) == SEASONS), 'season order/population differs')
    if purpose == 'real':
        require(sum(len(rows) for _, _, rows in result) == 6560, 'real selection requires 6560 games')
    return result


def _occurrence(row):
    require(type(row['season']) is str and row['season'] in SEASONS and type(row['side']) is str and row['side'] in SIDES,
            'invalid alias occurrence season/side')
    _game_id(row['game_id'], row['season'])
    return row['season'], row['game_id'], row['side']


def _identities(table, purpose, keys):
    _closed(table, 'schema_version purpose coaches aliases', 'identities')
    require(type(table['schema_version']) is int and table['schema_version'] == 1 and table['purpose'] == purpose,
            'identity schema/purpose differs')
    require(type(table['coaches']) is list and type(table['aliases']) is list, 'identity catalogue and aliases must be arrays')
    catalogue = {}
    for row in table['coaches']:
        _closed(row, 'coach_id display_name', 'coach identity')
        require(_text(row['coach_id']) and _text(row['display_name']) and row['coach_id'] not in catalogue,
                'invalid/duplicate coach catalogue identity')
        catalogue[row['coach_id']] = row['display_name']
    scopes = []
    for row in table['aliases']:
        _closed(row, 'reported_name applies_to coach_id explanation anchors', 'alias')
        require(_text(row['reported_name']) and _text(row['explanation']), 'alias needs exact nonblank name and explanation')
        require(row['coach_id'] is None or type(row['coach_id']) is str and row['coach_id'] in catalogue,
                'alias coach id is absent from catalogue')
        applies = row['applies_to']
        scope = None
        if applies is not None:
            require(type(applies) is list and bool(applies), 'alias scope must be null or nonempty')
            scope = set()
            for occurrence in applies:
                _closed(occurrence, 'season game_id side', 'alias scope')
                key = _occurrence(occurrence)
                require(key in keys and key not in scope, 'unknown/duplicate alias occurrence')
                scope.add(key)
        scopes.append(scope)
        require(type(row['anchors']) is list and bool(row['anchors']), 'alias needs source anchors')
        anchors = set()
        for anchor in row['anchors']:
            _closed(anchor, 'season game_id side receipt_sha256 body_sha256 pointer', 'alias anchor')
            key = _occurrence(anchor)
            require(key in keys and key not in anchors and (scope is None or key in scope), 'unknown/duplicate/out-of-scope anchor')
            anchors.add(key)
            _digest(anchor['receipt_sha256'])
            _digest(anchor['body_sha256'])
            require(anchor['pointer'] == f'/gameInfo/{key[2]}Team/headCoach/default', 'anchor pointer differs from coach field')
    return scopes


def _matching_alias(table, scopes, key, name):
    matches = [i for i, alias in enumerate(table['aliases']) if alias['reported_name'] == name
               and (scopes[i] is None or key in scopes[i])]
    require(len(matches) <= 1, 'multiple aliases match the same source occurrence')
    return matches[0] if matches else None


def _name(body, side):
    value = body.get('gameInfo')
    for field in (side + 'Team', 'headCoach', 'default'):
        if value is None:
            return None, 'coach_not_reported'
        if type(value) is not dict:
            return None, 'coach_malformed'
        value = value.get(field)
    if value is None or type(value) is str and not value.strip():
        return None, 'coach_not_reported'
    if type(value) is not str:
        return None, 'coach_malformed'
    return value, None


def _pointer(body, pointer):
    value = body
    for part in pointer.strip('/').split('/'):
        if type(value) is not dict or part not in value:
            return False, None
        value = value[part]
    return True, value


def _report_status(value, game):
    if type(value) is not str:
        return 'invalid'
    try:
        parsed = urlsplit(value)
    except ValueError:
        return 'invalid'
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('www.nhl.com', 'nhl.com'):
        return 'invalid'
    match = re.fullmatch(r'/scores/htmlreports/([0-9]{8})/([A-Z]{2})([0-9]{6})\.HTM', parsed.path)
    if match is None or parsed.query or parsed.fragment:
        return 'invalid'
    return 'agrees' if (match[1], match[3]) == (game['season'], game['game_id'][-6:]) else 'conflict'


def _context_status(pointer, value, game):
    expected = {'/id': game['game_id'], '/gameId': game['game_id'], '/season': game['season'],
                '/gameType': 2, '/gameDate': game['game_date'],
                '/gameInfo/homeTeam/id': game['home_team_id'], '/gameInfo/awayTeam/id': game['away_team_id']}
    if pointer == '/gameReports':
        return 'agrees' if type(value) is dict else 'invalid'
    if pointer.startswith('/gameReports/'):
        return _report_status(value, game)
    target = expected[pointer]
    if pointer in ('/id', '/gameId', '/season'):
        width = 8 if pointer == '/season' else 10
        valid = type(value) is int and value > 0 and len(str(value)) == width or type(value) is str and re.fullmatch('[0-9]{' + str(width) + '}', value)
        return ('agrees' if str(value) == target else 'conflict') if valid else 'invalid'
    if pointer == '/gameDate':
        return ('agrees' if value == target else 'conflict') if _date(value) else 'invalid'
    return ('agrees' if value == target else 'conflict') if type(value) is int and value > 0 else 'invalid'


def _context(body, game):
    checks = []
    for pointer in CONTEXT_POINTERS:
        present, value = _pointer(body, pointer)
        status = 'absent' if not present else 'unavailable' if value is None else _context_status(pointer, value, game)
        checks.append(dict(pointer=pointer, reported_value=value, status=status))
    return checks


def _assignment(status, side, name=None, reason=None, coach_id=None, entry=None):
    return dict(reported_name=name, coach_id=coach_id, status=status, reason=reason,
                source_pointer=f'/gameInfo/{side}Team/headCoach/default', identity_entry=entry)


def _interpret(game, capture, selected):
    if capture is None:
        source = dict(capture_path=None, receipt_sha256=None, body_sha256=None, requested_at=None, http_status=None,
                      capture_status='not_acquired', parse_status='unavailable',
                      explanation=selected['not_acquired_reason'] + ': ' + selected['explanation'])
    else:
        status = 'incomplete' if capture.body_sha256 is None else 'captured_2xx' if 200 <= capture.http_status <= 299 else 'captured_non2xx'
        source = dict(capture_path=str(capture.capture_path), receipt_sha256=selected['capture']['receipt_sha256'],
                      body_sha256=capture.body_sha256, requested_at=capture.requested_at, http_status=capture.http_status,
                      capture_status=status, parse_status='unavailable', explanation=capture.reason)
    game.update(source=source, context_checks=[])
    names = {side: (None, None) for side in SIDES}
    if source['capture_status'] != 'captured_2xx':
        overall = 'source_unavailable'
    else:
        try:
            body = strict_json(capture.body)
        except (ValueError, UnicodeDecodeError):
            body = None
        if type(body) is not dict or body.get('gameInfo') is not None and type(body['gameInfo']) is not dict:
            source.update(parse_status='malformed', explanation='right-rail body/root/gameInfo is malformed')
            overall = 'source_malformed'
        else:
            game['context_checks'] = _context(body, game)
            names = {side: _name(body, side) for side in SIDES}
            conflict = any(check['status'] in ('invalid', 'conflict') for check in game['context_checks'])
            source.update(parse_status='identity_conflict' if conflict else 'parsed',
                          explanation='right-rail context is invalid or conflicts with selected inventory' if conflict else None)
            overall = 'source_identity_conflict' if conflict else None
    for side in SIDES:
        name, missing = names[side]
        status = overall or missing or 'identity_unreviewed'
        reason = source['explanation'] if overall else ('coach field malformed' if missing == 'coach_malformed' else 'coach name not reported' if missing else 'reported name has no reviewed matching alias')
        game[side] = _assignment(status, side, name, reason)
    return game


def _validate_anchors(games, table):
    by_key = {(g['season'], g['game_id'], side): (g, g[side]) for g in games for side in SIDES}
    for alias in table['aliases']:
        for anchor in alias['anchors']:
            game, assignment = by_key[_occurrence(anchor)]
            source = game['source']
            require(source['capture_status'] == 'captured_2xx' and source['parse_status'] in ('parsed', 'identity_conflict')
                    and source['receipt_sha256'] == anchor['receipt_sha256'] and source['body_sha256'] == anchor['body_sha256']
                    and assignment['reported_name'] == alias['reported_name'], 'alias anchor does not match selected verified source name')


def _bind_aliases(games, table, scopes):
    for game in games:
        for side in SIDES:
            assignment = game[side]
            name = assignment['reported_name']
            if name is None:
                continue
            key = game['season'], game['game_id'], side
            index = _matching_alias(table, scopes, key, name)
            if assignment['status'] != 'identity_unreviewed' or index is None:
                continue
            alias = table['aliases'][index]
            assignment.update(coach_id=alias['coach_id'], identity_entry=index,
                              status='resolved' if alias['coach_id'] is not None else 'identity_unresolved',
                              reason=None if alias['coach_id'] is not None else alias['explanation'])


def _coverage(games, purpose, seasons):
    rows = []
    issues = []
    times = []
    for season in seasons:
        selected = [g for g in games if g['season'] == season]
        capture = Counter(g['source']['capture_status'] for g in selected)
        parsed = Counter(g['source']['parse_status'] for g in selected)
        assignments = Counter(g[side]['status'] for g in selected for side in SIDES)
        resolved = Counter(sum(g[side]['status'] == 'resolved' for side in SIDES) for g in selected)
        rows.append(dict(season=season, games=len(selected), slots=2*len(selected),
                         capture_counts={s: capture[s] for s in CAPTURE_STATUSES},
                         parse_counts={s: parsed[s] for s in PARSE_STATUSES},
                         assignment_counts={s: assignments[s] for s in ASSIGNMENT_STATUSES},
                         resolved_games=dict(both=resolved[2], one=resolved[1], neither=resolved[0]),
                         distinct_coaches=len({g[side]['coach_id'] for g in selected for side in SIDES if g[side]['coach_id'] is not None})))
        for game in selected:
            if game['source']['requested_at'] is not None:
                times.append(game['source']['requested_at'])
            for side in SIDES:
                assignment = game[side]
                if assignment['status'] != 'resolved':
                    issues.append(dict(season=season, game_id=game['game_id'], side=side, team_id=game[side+'_team_id'],
                                       status=assignment['status'], reported_name=assignment['reported_name'], reason=assignment['reason'],
                                       capture_path=game['source']['capture_path'], source_pointer=assignment['source_pointer']))
    ordered_times = sorted(times, key=datetime.fromisoformat)
    return dict(schema_version=1, purpose=purpose, seasons=rows,
                retrieval_range=dict(first=ordered_times[0] if times else None, last=ordered_times[-1] if times else None), issues=issues)


def bind_coaches(selection_path: Path | str, identity_path: Path | str, output: Path | str) -> Path:
    """validate original evidence once and write a new detached dated-coach artifact."""
    started = time.monotonic()
    selection_path = Path(selection_path).resolve(strict=True)
    identity_path = Path(identity_path).resolve(strict=True)
    selection_bytes = selection_path.read_bytes()
    identity_bytes = identity_path.read_bytes()
    selection = read_json(selection_path)
    require(type(selection) is dict and type(selection.get('purpose')) is str, 'selection purpose missing')
    purpose = selection['purpose']
    selected_seasons = _selection(selection, selection_path, purpose)
    table = read_json(identity_path)
    keys = {(row['season'], gid, side) for row, _, captures in selected_seasons for gid in captures for side in SIDES}
    scopes = _identities(table, purpose, keys)
    roots = [str(selection_path.parent), str(identity_path.parent)]
    games = []
    corpora = []
    for row, manifest, dispositions in selected_seasons:
        roots.append(str(manifest.parent))
        require(identity(manifest)['sha256'] == row['sha256'], 'corpus manifest sha256 differs')
        document, inventory, _ = load_corpus(manifest, [])
        require(document['reference']['requested_season'] == row['season'], 'selected corpus season differs')
        required = set(inventory) if row['game_ids'] is None else set(row['game_ids'])
        require(required <= inventory.keys() and set(dispositions) == required, 'capture dispositions do not cover selected admitted inventory')
        if purpose == 'real':
            require(len(inventory) == 1312, 'real corpus must contain 1312 inventory games')
        corpora.append(dict(season=row['season'], corpus_manifest=str(manifest), sha256=row['sha256']))
        for gid in required:
            disposition = dispositions[gid]
            selected = disposition['capture']
            capture = None
            if selected is not None:
                directory = _path(selected['directory'], selection_path.parent)
                roots.append(str(directory))
                receipt = directory / 'right-rail' / 'capture.json'
                capture = read_supplemental_capture(directory)
                require(identity(receipt)['sha256'] == selected['receipt_sha256'], 'selected receipt sha256 differs')
                require(capture.requested_game_id == gid, 'selected capture requested game differs from inventory')
            game = {key: inventory[gid][key] for key in ('season', 'game_id', 'game_date', 'home_team_id', 'away_team_id')}
            games.append(_interpret(game, capture, disposition))
    games.sort(key=lambda game: (game['season'], game['game_date'], game['game_id']))
    _bind_aliases(games, table, scopes)
    coverage = _coverage(games, purpose, [row['season'] for row, _, _ in selected_seasons])
    output = output_path(str(output), roots)
    output.mkdir()
    with (output / 'selection.json').open('xb') as destination:
        destination.write(selection_bytes)
    with (output / 'identities.json').open('xb') as destination:
        destination.write(identity_bytes)
    write_json(output / 'coverage.json', coverage)
    resources = dict(wall_seconds=time.monotonic()-started,
                     peak_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
                     output_bytes=sum((output/name).stat().st_size for name in ('selection.json', 'identities.json', 'coverage.json')))
    artifact = dict(schema_version=1, kind='dated-coaches', purpose=purpose, interpretation_id='reported-head-coach-v1',
                    implementation=implementation_identity(),
                    selection=dict(path='selection.json', sha256=identity(output/'selection.json')['sha256'], original_path=str(selection_path)),
                    identities=dict(path='identities.json', sha256=identity(output/'identities.json')['sha256'], original_path=str(identity_path)),
                    coverage=dict(path='coverage.json', sha256=identity(output/'coverage.json')['sha256']),
                    corpora=corpora, games=games, resources=resources)
    # validate the same closed contract the detached consumer will read, before success exists.
    _validate_artifact(artifact, selection, table, coverage)
    path = output / 'coaches.json'
    write_json(path, artifact)
    return path


def _validate_context(checks, game):
    require(type(checks) is list, 'context checks must be an array')
    seen = []
    for check in checks:
        _closed(check, 'pointer reported_value status', 'context check')
        pointer = check['pointer']
        require(type(pointer) is str and pointer in CONTEXT_POINTERS and pointer not in seen,
                'unknown/duplicate context pointer')
        seen.append(pointer)
        status = check['status']
        require(type(status) is str and status in ('agrees', 'absent', 'unavailable', 'invalid', 'conflict'), 'invalid context status')
        value = check['reported_value']
        if status == 'absent':
            require(value is None and pointer in CONTEXT_POINTERS, 'absent context must have null value')
        elif value is None:
            require(status == 'unavailable', 'explicit null context must be unavailable')
        else:
            require(status == _context_status(pointer, value, game), 'context check verdict differs from recorded value')
    if checks:
        require(seen[:len(CONTEXT_POINTERS)] == list(CONTEXT_POINTERS), 'context guard pointers/order differ')
        require(len(seen) == len(CONTEXT_POINTERS), 'context guard cardinality differs')
        reports = next(check['reported_value'] for check in checks if check['pointer'] == '/gameReports')
        for check in checks:
            if check['pointer'] in REPORT_POINTERS:
                field = check['pointer'].rsplit('/', 1)[1]
                present = type(reports) is dict and field in reports
                require(_same_json(check['reported_value'], reports[field] if present else None)
                        and (check['status'] == 'absent') == (not present),
                        'report child check differs from retained parent collection')


def _validate_source(source, disposition, selection_path):
    _closed(source, 'capture_path receipt_sha256 body_sha256 requested_at http_status capture_status parse_status explanation', 'game source')
    capture_status = source['capture_status']
    parse_status = source['parse_status']
    require(type(capture_status) is str and capture_status in CAPTURE_STATUSES and type(parse_status) is str and parse_status in PARSE_STATUSES,
            'invalid source status')
    selected = disposition['capture']
    if selected is None:
        require(capture_status == 'not_acquired' and parse_status == 'unavailable'
                and all(source[key] is None for key in ('capture_path', 'receipt_sha256', 'body_sha256', 'requested_at', 'http_status'))
                and source['explanation'] == disposition['not_acquired_reason'] + ': ' + disposition['explanation'], 'unacquired source contradicts selection')
        return
    require(capture_status != 'not_acquired', 'selected capture cannot be unacquired')
    require(source['capture_path'] == str(_path(selected['directory'], selection_path.parent)/'right-rail'/'capture.json')
            and source['receipt_sha256'] == selected['receipt_sha256'], 'source receipt link differs from selection')
    _absolute(source['capture_path'])
    _digest(source['receipt_sha256'])
    _utc(source['requested_at'])
    http = source['http_status']
    require(http is None or type(http) is int and 100 <= http <= 599, 'invalid source http status')
    if capture_status == 'incomplete':
        require(source['body_sha256'] is None and parse_status == 'unavailable', 'incomplete source cannot have body or parse')
    else:
        _digest(source['body_sha256'])
        require(http is not None and (200 <= http <= 299) == (capture_status == 'captured_2xx'), 'captured status disagrees with http')
        require((parse_status != 'unavailable') == (capture_status == 'captured_2xx'), 'parse status disagrees with captured source')
    require(source['explanation'] is None if parse_status == 'parsed' else _text(source['explanation']), 'source explanation disagrees with parse status')


def _same_json(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same_json(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    return left == right


def _validate_artifact(document, selection, table, coverage):
    _closed(document, 'schema_version kind purpose interpretation_id implementation selection identities coverage corpora games resources', 'coaches artifact')
    purpose = document['purpose']
    require(type(document['schema_version']) is int and document['schema_version'] == 1 and document['kind'] == 'dated-coaches'
            and document['interpretation_id'] == 'reported-head-coach-v1' and type(purpose) is str and purpose in ('real', 'fixture'), 'unsupported dated coaches artifact')
    for member in ('selection', 'identities'):
        _closed(document[member], 'path sha256 original_path', member+' identity')
        require(document[member]['path'] == member+'.json', 'artifact member path differs')
        _digest(document[member]['sha256'])
        _absolute(document[member]['original_path'])
    _closed(document['coverage'], 'path sha256', 'coverage identity')
    require(document['coverage']['path'] == 'coverage.json', 'coverage member path differs')
    _digest(document['coverage']['sha256'])
    original = Path(document['selection']['original_path'])
    selected_seasons = _selection(selection, original, purpose)
    expected_corpora = [dict(season=row['season'], corpus_manifest=str(path), sha256=row['sha256']) for row, path, _ in selected_seasons]
    require(type(document['corpora']) is list and document['corpora'] == expected_corpora, 'bound corpus identities differ')
    keys = {(row['season'], gid, side) for row, _, captures in selected_seasons for gid in captures for side in SIDES}
    scopes = _identities(table, purpose, keys)
    dispositions = {(row['season'], gid): disposition for row, _, captures in selected_seasons for gid, disposition in captures.items()}
    games = document['games']
    require(type(games) is list and len(games) == len(dispositions), 'game cardinality differs from selection')
    seen = set()
    order = []
    for game in games:
        _closed(game, 'season game_id game_date home_team_id away_team_id source context_checks home away', 'dated game')
        require(type(game['season']) is str and game['season'] in SEASONS, 'invalid game season')
        _game_id(game['game_id'], game['season'])
        key = (game['season'], game['game_id'])
        require(key in dispositions and key not in seen and _date(game['game_date']), 'unknown/duplicate game or invalid date')
        seen.add(key)
        order.append((game['season'], game['game_date'], game['game_id']))
        require(all(type(game[s+'_team_id']) is int and game[s+'_team_id'] > 0 for s in SIDES)
                and game['home_team_id'] != game['away_team_id'], 'invalid inventory side identity')
        source = game['source']
        _validate_source(source, dispositions[key], original)
        _validate_context(game['context_checks'], game)
        parsed = source['parse_status']
        conflict = any(check['status'] in ('invalid', 'conflict') for check in game['context_checks'])
        require((parsed in ('parsed', 'identity_conflict')) == bool(game['context_checks']), 'context checks disagree with parse availability')
        require(parsed != 'identity_conflict' or conflict, 'identity conflict has no conflicting context')
        require(parsed != 'parsed' or not conflict, 'parsed game retains invalid/conflicting context')
        required_status = {'unavailable': 'source_unavailable', 'malformed': 'source_malformed', 'identity_conflict': 'source_identity_conflict'}.get(parsed)
        for side in SIDES:
            assignment = game[side]
            _closed(assignment, 'reported_name coach_id status reason source_pointer identity_entry', 'coach assignment')
            status = assignment['status']
            require(type(status) is str and status in ASSIGNMENT_STATUSES
                    and assignment['source_pointer'] == f'/gameInfo/{side}Team/headCoach/default', 'assignment status/pointer differs')
            name = assignment['reported_name']
            require(name is None or _text(name), 'reported name must be null or exact nonblank string')
            require(assignment['reason'] is None if status == 'resolved' else _text(assignment['reason']), 'assignment reason disagrees with status')
            if required_status is not None:
                require(status == required_status, 'source parse status disagrees with assignment')
                if parsed != 'identity_conflict':
                    require(name is None, 'unavailable/malformed source cannot report a name')
            else:
                require(status in ('resolved', 'coach_not_reported', 'coach_malformed', 'identity_unreviewed', 'identity_unresolved'), 'parsed assignment has source failure')
            if status in ('resolved', 'identity_unreviewed', 'identity_unresolved'):
                require(_text(name), 'identity status requires a reported name')
                index = _matching_alias(table, scopes, (*key, side), name)
                require((assignment['identity_entry'] is None if index is None else type(assignment['identity_entry']) is int and assignment['identity_entry'] == index),
                        'assignment alias link differs from exact name/scope')
                if index is None:
                    require(status == 'identity_unreviewed' and assignment['coach_id'] is None, 'unreviewed identity cannot be assigned')
                else:
                    alias = table['aliases'][index]
                    require(assignment['coach_id'] == alias['coach_id'] and status == ('resolved' if alias['coach_id'] is not None else 'identity_unresolved'), 'assignment differs from reviewed alias')
                    if status == 'identity_unresolved':
                        require(assignment['reason'] == alias['explanation'], 'unresolved identity reason differs from review')
            else:
                require(assignment['coach_id'] is None and assignment['identity_entry'] is None, 'source/name failure cannot resolve identity')
                if status in ('coach_not_reported', 'coach_malformed'):
                    require(name is None, 'missing/malformed name cannot retain a valid source name')
                if name is not None:
                    _matching_alias(table, scopes, (*key, side), name)
    require(seen == set(dispositions) and order == sorted(order), 'game population/order differs')
    # anchors and coverage are checked against the validated stored observations, never raw files.
    _validate_anchors(games, table)
    require(_same_json(coverage, _coverage(games, purpose, [row['season'] for row, _, _ in selected_seasons])),
            'coverage differs from dated game dispositions')
    implementation = document['implementation']
    _closed(implementation, 'git_commit git_dirty python_version', 'implementation')
    commit = implementation['git_commit']
    require(commit is None or type(commit) is str and re.fullmatch('[0-9a-f]{40}', commit), 'invalid implementation commit')
    require(implementation['git_dirty'] is None or type(implementation['git_dirty']) is bool, 'invalid implementation dirty flag')
    require((commit is None) == (implementation['git_dirty'] is None) and _text(implementation['python_version']), 'incomplete implementation identity')
    _closed(document['resources'], 'wall_seconds peak_memory_bytes output_bytes', 'resources')
    require(type(document['resources']['wall_seconds']) in (int, float) and math.isfinite(document['resources']['wall_seconds'])
            and document['resources']['wall_seconds'] >= 0, 'invalid wall time')
    require(all(type(document['resources'][field]) is int and document['resources'][field] >= 0 for field in ('peak_memory_bytes', 'output_bytes')),
            'invalid memory/output bytes')


def read_coaches(coaches_path: Path | str, expected_purpose: Purpose) -> Coaches:
    """validate a detached artifact; external corpora and source captures stay unopened."""
    require(type(expected_purpose) is str and expected_purpose in ('real', 'fixture'), 'invalid expected purpose')
    path = Path(coaches_path).resolve(strict=True)
    document = read_json(path)
    require(type(document) is dict and document.get('purpose') == expected_purpose, 'coaches purpose differs from consumer')
    members = {}
    for name in ('selection', 'identities', 'coverage'):
        reference = document.get(name)
        require(type(reference) is dict and reference.get('path') == name+'.json', 'missing/invalid artifact member')
        _digest(reference.get('sha256'))
        member = path.parent / (name+'.json')
        require(identity(member)['sha256'] == reference['sha256'], 'artifact member sha256 differs')
        members[name] = read_json(member)
    _validate_artifact(document, members['selection'], members['identities'], members['coverage'])
    require(document['resources']['output_bytes'] == sum((path.parent/(name+'.json')).stat().st_size for name in members), 'output byte receipt differs')
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description='bind dated reported head coaches offline', allow_abbrev=False)
    for option in ('selection', 'identities', 'out'):
        parser.add_argument('--'+option, required=True, action=Once)
    args = parser.parse_args()
    try:
        path = bind_coaches(args.selection, args.identities, args.out)
    except (InputContractError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    coverage = read_json(path.parent / 'coverage.json')
    games = sum(row['games'] for row in coverage['seasons'])
    capture = Counter()
    parsed = Counter()
    assignments = Counter()
    for row in coverage['seasons']:
        capture.update(row['capture_counts'])
        parsed.update(row['parse_counts'])
        assignments.update(row['assignment_counts'])
    resolved = assignments['resolved']
    print(f"requested: {games-capture['not_acquired']}/{games} games; "
          f"captured: {capture['captured_2xx']+capture['captured_non2xx']}/{games} games "
          f"(2xx: {capture['captured_2xx']}; non2xx: {capture['captured_non2xx']}; incomplete: {capture['incomplete']})")
    print(f"parsed: {parsed['parsed']}/{games} games; identity conflicts: {parsed['identity_conflict']}/{games} games; "
          f"resolved: {resolved}/{2*games} game-team slots")
    print('quantity: nhl-reported head coach at recorded retrieval time; bench attendance, tenure and coaching quality are unverified.')
    if coverage['purpose'] == 'fixture':
        print('purpose: fixture; synthetic evidence does not establish real-source coverage.')
    for row in coverage['issues']:
        print(f"{row['season']} {row['game_id']} {row['side']} team={row['team_id']} "
              f"{row['status']} name={row['reported_name']!r}: {row['reason']} "
              f"source={row['capture_path']} pointer={row['source_pointer']}")
    print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
