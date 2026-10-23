"""prepare and consume explicitly selected, immutable common hockey evidence."""

from collections import Counter, defaultdict
from datetime import date
import hashlib
from pathlib import Path
import resource
import sys
import time

from . import analysis_records as records
from .artifacts import implementation_identity, write_json
from .captures import (
    InputContractError,
    REFERENCE_SOURCES,
    SOURCES,
    read_capture,
    read_reference_capture,
    strict_json,
)
from .corpus import STATUSES
from .corpus_inputs import load_corpus, read_document
from .feature_data import fact
from .feature_history import history_context, prepare_history

SEASONS = ("20212022", "20222023", "20232024", "20242025", "20252026")
PREPARATION_ID = "experimental-evidence-v1"
# the frozen 03n input table owns the real five-season source identity.
REAL_CORPORA = {
    "20212022": (
        "/Volumes/Expansion/hockey-stats/corpora/03m-20261010-02/20212022/corpus.json",
        "30eb12b290ccd9af9eae7ade8c7dcd5f285129b52b646eec3fced3e2628badc8",
    ),
    "20222023": (
        "/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20222023/corpus.json",
        "735c741115725e7c4fe8a28782f352c787895db5eea2123b2b7ec27b4db1e02a",
    ),
    "20232024": (
        "/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20232024/corpus.json",
        "92392c80b145d72c3be759a94b8113db04a7e8d26a4404e1e15a40119db6a414",
    ),
    "20242025": (
        "/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20242025/corpus.json",
        "46208ef0830949de4faf1e6695f052c9fdbc23bca5b86fa045c3552d3d467639",
    ),
    "20252026": (
        "/Volumes/Expansion/hockey-stats/corpora/03m-20261010/20252026/corpus.json",
        "8229fc6686fa03c4f6cc00d68d68aac1d1d2b83d6950d56eeebb7c9fc923fd43",
    ),
}


class PreparedManifest(dict):
    """validated manifest data with the directory needed for relative members."""

    directory: Path


def _read(path):
    try:
        return strict_json(path.read_bytes())
    except (OSError, ValueError) as error:
        raise InputContractError(f"{path}: {error}") from error


def _sha(path):
    try:
        with path.open("rb") as source:
            return hashlib.file_digest(source, "sha256").hexdigest()
    except OSError as error:
        raise InputContractError(f"{path}: {error}") from error


def _selection(value):
    records.validate(value, records.Selection, "selection")
    seasons = [row["season"] for row in value["seasons"]]
    records.require(
        bool(seasons)
        and seasons == sorted(set(seasons))
        and set(seasons) <= set(SEASONS),
        "selection",
        "seasons must be unique, admitted and ordered",
    )
    records.require(
        value["purpose"] != "real" or seasons == list(SEASONS),
        "selection",
        "real preparation requires all five ordered seasons",
    )
    for row in value["seasons"]:
        records.require(bool(row["corpus_manifest"]), "selection", "empty corpus path")
        records.require(
            len(row["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["sha256"]),
            "selection",
            "invalid corpus digest",
        )
        games = row["game_ids"]
        records.require(
            games is None
            if value["purpose"] == "real"
            else games is not None and bool(games),
            "selection",
            "real requires all inventory games; fixture requires explicit nonempty games",
        )
        if games is not None:
            records.require(
                len(games) == len(set(games))
                and all(
                    len(gid) == 10
                    and all(c in "0123456789" for c in gid)
                    and gid[:4] + str(int(gid[:4]) + 1) == row["season"]
                    and gid[4:6] == "02"
                    for gid in games
                ),
                "selection",
                "duplicate or invalid game identity",
            )
    return value


def _bind_sources(bound_inputs, identity, consumed, *, reference=False):
    """verify each admitted receipt/body once; absent sources remain explicit."""
    reader = read_reference_capture if reference else read_capture
    for bound in bound_inputs:
        path = Path(bound["capture_path"])
        records.require(
            path.is_absolute()
            and path.name == "capture.json"
            and path.parent.name == bound["source"],
            str(path),
            "source locator differs",
        )
        capture = reader(path.parent.parent, bound["source"])
        records.require(
            bound["status"] != "parsed" or capture.body is not None,
            str(path),
            "parsed native source has no admitted source body",
        )
        actual_identity = (
            capture.requested_season if reference else capture.requested_game_id
        )
        records.require(
            actual_identity in (None, identity), str(path), "receipt identity differs"
        )
        records.require(
            capture.capture_path == path.resolve()
            and (capture.requested_at, capture.http_status, capture.body_sha256)
            == (bound["requested_at"], bound["http_status"], bound["body_sha256"]),
            str(path),
            "receipt differs from consumed native input",
        )
        promised = (
            bound["requested_at"] is not None
            or bound["body_sha256"] is not None
            or bound["status"] != "unavailable"
        )
        records.require(
            not promised or path.is_file(), str(path), "promised receipt is missing"
        )
        if path.is_file():
            consumed.append(
                dict(
                    kind="reference-capture" if reference else "source-capture",
                    path=str(path.resolve()),
                    sha256=_sha(path),
                )
            )
        if capture.body_sha256 is not None:
            consumed.append(
                dict(
                    kind="reference-body" if reference else "source-body",
                    path=str((path.parent / "body.bin").resolve()),
                    sha256=capture.body_sha256,
                )
            )


def prepare_game(envelope, inventory_entry, references, input_ref):
    """compose one game through the authoritative product context owner."""
    from .analysis_context import prepare_game as compose

    return compose(envelope, inventory_entry, references, input_ref)


def _missing_game(entry, ledger, input_ref, ledger_index):
    evidence = [
        dict(input_ref=input_ref, source="corpus", path=f"/games/{ledger_index}")
    ]
    return dict(
        schema_version=1,
        season=entry["season"],
        game_id=entry["game_id"],
        game=dict(
            inventory=entry,
            ledger=dict(status=ledger["status"], reason=ledger["reason"]),
            identity=None,
            inputs=[],
            reported_results=[],
            checks=[],
            periods=None,
            native_intervals=None,
            report_rows=None,
            recording_observations=[],
            source_issues=[],
            native_issues=[],
        ),
        events=None,
        associations=None,
        segments=None,
        chunks=None,
        player_shifts=None,
        episodes=None,
        people=None,
        attempts=None,
        credits=None,
        ordinary_attempt_support=dict(
            segments=None, events=None, report_only=None, reasons=[]
        ),
        issues=[
            dict(
                code="source_unavailable",
                source="corpus",
                path=f"/games/{ledger_index}",
                message=ledger["reason"] or "native game evidence unavailable",
                evidence=evidence,
            )
        ],
    )


def _people_observations(game, accumulator):
    """retain compact dated identity observations, without event/game arrays."""
    day = game["game"]["inventory"]["game_date"]
    gid = game["game_id"]
    for key, person in (game["people"] or {}).items():
        values = person["people"]["values"]
        entry = accumulator.setdefault(
            int(key),
            dict(
                names=[],
                teams=set(),
                positions=set(),
                sweaters=[],
                births=set(),
                hands=set(),
                evidence=[],
            ),
        )
        names = {
            row["first_name"] + " " + row["last_name"]
            for row in person["roster"]
            if row["first_name"] and row["last_name"]
        }
        entry["names"].extend((day, gid, name) for name in names)
        for row in person["roster"] + person["boxscore"]:
            if row["team_id"] is not None:
                entry["teams"].add(row["team_id"])
            if row["reported_position"] is not None:
                entry["positions"].add(row["reported_position"])
        entry["sweaters"].extend(person["sweaters"])
        for bio in values["bio_observations"]:
            if bio["birth_date"] is not None:
                entry["births"].add(bio["birth_date"])
            if bio["shoots_catches"] is not None:
                entry["hands"].add(bio["shoots_catches"])
        entry["evidence"].extend(person["people"]["evidence"])


def _season_people(season, accumulator):
    result = []
    reference_date = season[4:] + "-02-01"
    for player, entry in sorted(accumulator.items()):
        latest = max((row[0] for row in entry["names"]), default=None)
        names = {row[2] for row in entry["names"] if row[0] == latest}
        groups = {
            "F" if p in ("C", "L", "R", "F") else p if p in ("D", "G") else None
            for p in entry["positions"]
        }
        birth = next(iter(entry["births"])) if len(entry["births"]) == 1 else None
        hand = next(iter(entry["hands"])) if len(entry["hands"]) == 1 else None
        age = (
            (date.fromisoformat(reference_date) - date.fromisoformat(birth)).days
            if birth is not None
            else None
        )
        values = dict(
            player_id=player,
            name=next(iter(names)) if len(names) == 1 else None,
            team_ids=sorted(entry["teams"]),
            reported_positions=sorted(entry["positions"]),
            position_group=next(iter(groups))
            if len(groups) == 1 and None not in groups
            else None,
            sweaters=sorted(
                entry["sweaters"],
                key=lambda row: (row["game_id"], row["team_id"], row["number"]),
            ),
            birth_date=birth,
            shoots_catches=hand,
            age_reference_date=reference_date,
            age_days=age if age is not None and age >= 0 else None,
            height_cm=None,
        )
        # identical source locators recur across games; retain each immutable locator once.
        evidence = []
        seen = set()
        for item in entry["evidence"]:
            marker = repr(sorted(item.items()))
            if marker not in seen:
                evidence.append(item)
                seen.add(marker)
        record = fact(
            values,
            evidence,
            reason="dated identity observations incomplete or conflicting",
        )
        record["problems"]["height_cm"]["reason"] = (
            "source height units are unverified; raw height remains in bio observations"
        )
        for field, conflict in (
            ("name", len(names) > 1),
            ("birth_date", len(entry["births"]) > 1),
            ("shoots_catches", len(entry["hands"]) > 1),
            ("position_group", len(groups) > 1),
        ):
            if conflict:
                record["problems"][field]["status"] = "conflict"
        result.append(record)
    document = dict(schema_version=1, season=season, people=result)
    return records.validate_people(document)


def _classify(values, *, exclude=()):
    """classify applicable leaves, preserving explicit not-applicable facts."""
    states = []

    def visit(value):
        if (
            isinstance(value, dict)
            and {"values", "problems", "evidence"} <= value.keys()
        ):
            for key, item in value["values"].items():
                if key in exclude:
                    continue
                problem = value["problems"].get(key)
                if problem:
                    if problem["status"] != "not_applicable":
                        states.append(False)
                elif isinstance(item, (dict, list)):
                    visit(item)
                else:
                    states.append(True)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(values)
    return (
        "not_applicable"
        if not states
        else "available"
        if all(states)
        else "partial"
        if any(states)
        else "unavailable"
    )


def _coverage_start(season, inventory_count, selected_count):
    return dict(
        season=season,
        inventory_games=inventory_count,
        selected_games=selected_count,
        game_status_counts={name: 0 for name in STATUSES},
        game_sources=[
            dict(source=source, available_games=0, unavailable_games=0)
            for source in SOURCES
        ],
        events=[],
        report_only_attempts=0,
        time=[],
        unknown_horizon_games=0,
        unresolved_known_seconds=0,
        completeness={
            name: {
                key: 0
                for key in ("available", "partial", "unavailable", "not_applicable")
            }
            for name in records.Completeness.__annotations__
        },
    )


def _coverage_game(coverage, game, event_counts, time_counts):
    coverage["game_status_counts"][game["game"]["ledger"]["status"]] += 1
    inputs = {row["source"]: row for row in game["game"]["inputs"]}
    for source in coverage["game_sources"]:
        available = (
            source["source"] in inputs
            and inputs[source["source"]]["status"] == "parsed"
        )
        source["available_games" if available else "unavailable_games"] += 1
    periods = game["game"]["periods"]
    identified = game["game"]["ledger"]["status"] == "reconstructed"
    if (
        not identified
        or periods is None
        or any(row["status"] != "supported" for row in periods)
    ):
        coverage["unknown_horizon_games"] += 1
    for interval in (game["game"]["native_intervals"] or []) if identified else []:
        if interval["classification"] == "unresolved":
            coverage["unresolved_known_seconds"] += (
                interval["end_seconds"] - interval["start_seconds"]
            )
    segments = game["segments"] or []
    support = game["ordinary_attempt_support"]
    included = {
        row["segment_index"]
        for row in support["segments"] or []
        if row["disposition"] == "included"
    }
    for segment in segments:
        membership = segment["membership"]
        if any(value is None for value in membership.values()):
            continue
        state = tuple(
            len(membership[field])
            for field in (
                "away_skaters",
                "home_skaters",
                "away_goalies",
                "home_goalies",
            )
        )
        seconds = segment["end_seconds"] - segment["start_seconds"]
        row = time_counts[state]
        row[0] += seconds
        row[1] += seconds if segment["segment_index"] in included else 0
    outcomes = {
        row["source_index"]: row["details"]["values"]["outcome"]
        for row in game["attempts"] or []
    }
    for event in game["events"] or []:
        source = event["source"]
        event_counts[source["type_key"], outcomes.get(source["source_index"])] += 1
    coverage["report_only_attempts"] += len(support["report_only"] or [])
    complete = coverage["completeness"]
    events = game["events"] or []
    for name, values in (
        (
            "order",
            [
                fact(
                    {"order_index": row["chronology"]["values"]["order_index"]},
                    row["chronology"]["evidence"],
                )
                for row in events
            ],
        ),
        ("score", [row["pre_score"] for row in events]),
        (
            "frame",
            [
                row["geometry"]
                for row in events
                if row["source"]["reported_x"] is not None
                and row["source"]["reported_y"] is not None
            ],
        ),
    ):
        status = (
            _classify(values, exclude=("location_kind",))
            if events
            else "unavailable"
            if game["events"] is None
            else "not_applicable"
        )
        complete[name][status] += 1
    for person in (game["people"] or {}).values():
        complete["history"][
            _classify(
                {
                    name: person[name]
                    for name in ("workload", "calendar_rest", "history")
                }
            )
        ] += 1
    for event in events:
        complete["event_context"][
            _classify(event["context"], exclude=("member_count", "known_count"))
        ] += 1
    for chunk in game["chunks"] or []:
        complete["elapsed_context"][
            _classify(
                {
                    key: chunk[key]
                    for key in (
                        "score",
                        "strength_transition",
                        "member_contexts",
                        "away_unit",
                        "home_unit",
                    )
                },
                exclude=("member_count", "known_count"),
            )
        ] += 1
    for attempt in game["attempts"] or []:
        outcomes = attempt["immediate_outcomes"]
        for name, field in (
            ("immediate_stop", "recorded_goalie_stop"),
            ("reattempt", "reattempt_within_5s"),
        ):
            problem = outcomes["problems"].get(field)
            status = (
                "available"
                if problem is None
                else "not_applicable"
                if problem["status"] == "not_applicable"
                else "unavailable"
            )
            complete[name][status] += 1


def _coverage_finish(coverage, event_counts, time_counts, people):
    coverage["events"] = [
        dict(kind=kind, outcome=outcome, count=count)
        for (kind, outcome), count in sorted(
            event_counts.items(), key=lambda row: (row[0][0] or "", row[0][1] or "")
        )
    ]
    coverage["time"] = [
        dict(
            zip(
                ("away_skaters", "home_skaters", "away_goalies", "home_goalies"), state
            ),
            physical_seconds=total,
            included_seconds=included,
            excluded_seconds=total - included,
            team_seconds=2 * included,
            skater_slot_seconds=(state[0] + state[1]) * included,
            goalie_slot_seconds=(state[2] + state[3]) * included,
        )
        for state, (total, included) in sorted(time_counts.items())
    ]
    for person in people["people"]:
        coverage["completeness"]["identity"][_classify(person)] += 1


def prepare_analysis(selection_path, output):
    """prepare selected games in date order; completion is the final manifest."""
    from .analysis_context import game_summary

    started = time.monotonic()
    selection_path = Path(selection_path).resolve(strict=True)
    selection_bytes = selection_path.read_bytes()
    selection = _selection(strict_json(selection_bytes))
    output = Path(output).resolve()
    records.require(not output.exists(), str(output), "output directory already exists")
    if selection["purpose"] == "real":
        records.require(
            Path("/Volumes/Expansion/hockey-stats") in output.parents,
            str(output),
            "real output must use external hockey-stats files",
        )
    consumed = [
        dict(
            kind="selection",
            path=str(selection_path),
            sha256=hashlib.sha256(selection_bytes).hexdigest(),
        )
    ]
    admitted = []
    all_inventory = []
    summaries = {}
    selected = []
    for selection_row in selection["seasons"]:
        path = (selection_path.parent / selection_row["corpus_manifest"]).resolve(
            strict=True
        )
        records.require(
            _sha(path) == selection_row["sha256"],
            str(path),
            "selected corpus digest differs",
        )
        if selection["purpose"] == "real":
            records.require(
                (str(path), selection_row["sha256"])
                == REAL_CORPORA[selection_row["season"]],
                str(path),
                "real input differs from frozen 03n corpus identity",
            )
        corpus, inventory, ledger = load_corpus(path, consumed)
        if selection["purpose"] == "real":
            records.require(
                len(inventory) == 1312
                and corpus.get("purpose") not in ("fixture", "fixture_exercise"),
                str(path),
                "real preparation requires the complete admitted inventory",
            )
        records.require(
            corpus["reference"]["requested_season"] == selection_row["season"],
            str(path),
            "selected season differs",
        )
        reference = corpus["reference"]
        corpus_ref = dict(path=str(path), sha256=selection_row["sha256"])
        _bind_sources(
            reference["inputs"], selection_row["season"], consumed, reference=True
        )
        reference = {
            **reference,
            "bio_observations": [
                {**row, "input_ref": corpus_ref}
                for row in reference["bio_observations"]
            ],
        }
        ids = (
            list(inventory)
            if selection_row["game_ids"] is None
            else selection_row["game_ids"]
        )
        records.require(
            set(ids) <= inventory.keys(),
            str(path),
            "selected game missing from inventory",
        )
        ids = sorted(ids, key=lambda gid: (inventory[gid]["game_date"], gid))
        all_inventory.extend(
            {
                **entry,
                "input_ref": corpus_ref,
                "selection_input_ref": dict(
                    path=str(selection_path),
                    sha256=hashlib.sha256(selection_bytes).hexdigest(),
                ),
                "history_admitted": True,
            }
            for entry in inventory.values()
        )
        admitted.append(
            dict(
                season=selection_row["season"],
                path=path,
                reference=reference,
                inventory=inventory,
                ledger=ledger,
                ledger_indices={
                    row["game_id"]: i for i, row in enumerate(corpus["games"])
                },
                game_ids=ids,
                input_ref=corpus_ref,
            )
        )
        selected.extend((inventory[gid]["game_date"], gid, admitted[-1]) for gid in ids)
    selected.sort(key=lambda row: (row[0], row[1]))
    envelopes = {}
    for _, gid, season in selected:
        ledger = season["ledger"][gid]
        if ledger["output_path"] is None:
            summaries[gid] = None
            continue
        path = (season["path"].parent / ledger["output_path"]).resolve(strict=True)
        envelope = read_document(path, "game", consumed)
        input_ref = dict(path=str(path), sha256=consumed[-1]["sha256"])
        if ledger["status"] == "reconstructed":
            summaries[gid] = game_summary(
                envelope, season["inventory"][gid], season["reference"], input_ref
            )
        else:
            summaries[gid] = None
            records.validate(envelope, records.NativeEnvelope, str(path))
            records.require(
                envelope["interpreted"]["requested_game_id"] == gid,
                str(path),
                "promised envelope requested identity differs",
            )
        _bind_sources(envelope["interpreted"]["inputs"], gid, consumed)
        envelopes[gid] = input_ref
    roots = [
        Path(row["path"]).parent.parent
        if row["kind"].endswith(("capture", "body"))
        else Path(row["path"]).parent
        for row in consumed
        if row["kind"] != "selection"
    ]
    records.require(
        all(output != root and root not in output.parents for root in roots),
        str(output),
        "output must be outside all inputs",
    )
    output.mkdir(parents=True)
    with (output / "selection.json").open("xb") as destination:
        destination.write(selection_bytes)
    prepared_history = history_context(all_inventory, summaries)
    files = []
    coverage_rows = []
    accumulators = {row["season"]: {} for row in admitted}
    coverages = {
        row["season"]: _coverage_start(
            row["season"], len(row["inventory"]), len(row["game_ids"])
        )
        for row in admitted
    }
    event_counts = {row["season"]: Counter() for row in admitted}
    time_counts = {row["season"]: defaultdict(lambda: [0, 0]) for row in admitted}
    for _, gid, season in selected:
        entry = season["inventory"][gid]
        ledger = season["ledger"][gid]
        if gid in envelopes and ledger["status"] == "reconstructed":
            ref = envelopes[gid]
            path = Path(ref["path"])
            records.require(
                _sha(path) == ref["sha256"],
                str(path),
                "envelope changed during preparation",
            )
            game = prepare_game(_read(path), entry, season["reference"], ref)
            game["game"]["ledger"] = dict(
                status=ledger["status"], reason=ledger["reason"]
            )
            history = prepare_history(
                all_inventory,
                summaries,
                [gid],
                missing_source_path="/seasons",
                prepared=prepared_history,
            )
            for player, groups in history["players"][gid].items():
                records.require(
                    game["people"] is not None and player in game["people"],
                    gid,
                    "history join lacks game person",
                )
                game["people"][player].update(groups)
        else:
            game = _missing_game(
                entry, ledger, season["input_ref"], season["ledger_indices"][gid]
            )
            if gid in envelopes:
                ref = envelopes[gid]
                records.require(
                    _sha(Path(ref["path"])) == ref["sha256"],
                    ref["path"],
                    "envelope changed during preparation",
                )
                envelope = _read(Path(ref["path"]))
                document = envelope["interpreted"]
                native = envelope["reconstruction"]
                game["game"].update(
                    identity=document["game"],
                    inputs=document["inputs"],
                    reported_results=document["reported_results"],
                    checks=document["checks"],
                    periods=native["periods"],
                    native_intervals=native["intervals"],
                    report_rows=document["report_rows"],
                    recording_observations=document["recording_observations"],
                    source_issues=document["issues"],
                    native_issues=native["issues"],
                )
                game["issues"][0]["evidence"].append(
                    dict(input_ref=ref, source="interpreted", path="/game")
                )
        records.validate_game(game)
        _people_observations(game, accumulators[season["season"]])
        _coverage_game(
            coverages[season["season"]],
            game,
            event_counts[season["season"]],
            time_counts[season["season"]],
        )
        member = Path("games") / season["season"] / (gid + ".json")
        (output / member).parent.mkdir(parents=True, exist_ok=True)
        write_json(output / member, game, compact=True)
        files.append(
            dict(
                kind="game",
                season=season["season"],
                game_id=gid,
                path=member.as_posix(),
                sha256=_sha(output / member),
            )
        )
    for season in admitted:
        year = season["season"]
        people = _season_people(year, accumulators[year])
        member = Path("people") / (year + ".json")
        (output / member).parent.mkdir(exist_ok=True)
        write_json(output / member, people, compact=True)
        files.append(
            dict(
                kind="people",
                season=year,
                game_id=None,
                path=member.as_posix(),
                sha256=_sha(output / member),
            )
        )
        coverage = coverages[year]
        _coverage_finish(coverage, event_counts[year], time_counts[year], people)
        coverage_rows.append(coverage)
    coverage = dict(schema_version=1, seasons=coverage_rows)
    records.validate(coverage, records.Coverage, "coverage")
    write_json(output / "coverage.json", coverage, compact=True)
    files.append(
        dict(
            kind="coverage",
            season=None,
            game_id=None,
            path="coverage.json",
            sha256=_sha(output / "coverage.json"),
        )
    )
    # shared capture references are immutable inputs, recorded once per identity.
    inputs = []
    seen = set()
    for row in consumed:
        marker = row["kind"], row["path"]
        records.require(
            marker not in seen
            or any(
                item["kind"] == row["kind"]
                and item["path"] == row["path"]
                and item["sha256"] == row["sha256"]
                for item in inputs
            ),
            row["path"],
            "input identity changed",
        )
        if marker not in seen:
            inputs.append(row)
            seen.add(marker)
    implementation = implementation_identity()
    code = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        code.update(path.name.encode() + b"\0" + path.read_bytes())
    implementation.update(
        preparation_policy_sha256=_sha(
            Path(__file__).resolve().parents[3] / "docs/specs/v1-01-shared-evidence.md"
        ),
        source_code_sha256=code.hexdigest(),
    )
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    manifest = dict(
        schema_version=1,
        kind="prepared-analysis",
        purpose=selection["purpose"],
        preparation_id=PREPARATION_ID,
        implementation=implementation,
        selection=dict(
            path="selection.json", sha256=hashlib.sha256(selection_bytes).hexdigest()
        ),
        inputs=inputs,
        seasons=[
            dict(
                season=row["season"],
                inventory_games=len(row["inventory"]),
                selected_game_ids=row["game_ids"],
            )
            for row in admitted
        ],
        files=files,
        resources=dict(
            wall_seconds=time.monotonic() - started,
            peak_memory_bytes=peak,
            output_bytes=sum(
                path.stat().st_size for path in output.rglob("*") if path.is_file()
            ),
        ),
    )
    _validate_manifest(manifest, output, selection)
    write_json(output / "manifest.json", manifest, compact=True)
    return read_prepared(output, selection["purpose"])


def _member_path(directory, member):
    path = Path(member)
    records.require(
        bool(member)
        and not path.is_absolute()
        and path.as_posix() == member
        and ".." not in path.parts
        and "." not in path.parts,
        "manifest/files",
        "member path must be contained and canonical",
    )
    resolved = (directory / path).resolve()
    records.require(
        directory in resolved.parents,
        "manifest/files",
        "member escapes output directory",
    )
    return resolved


def _validate_manifest(manifest, directory, selection):
    # selection.path is intentionally relative; all consumed input paths are absolute provenance.
    reference = (
        manifest["selection"]
        if type(manifest) is dict or isinstance(manifest, PreparedManifest)
        else None
    )
    if reference is not None:
        copy = dict(manifest)
        copy["selection"] = dict(reference, path=str(directory / "selection.json"))
        records.validate(copy, records.Manifest, "manifest")
    else:
        records.validate(manifest, records.Manifest, "manifest")
    records.require(
        reference["path"] == "selection.json"
        and manifest["purpose"] == selection["purpose"],
        "manifest",
        "selection identity differs",
    )
    records.require(
        [row["season"] for row in manifest["seasons"]]
        == [row["season"] for row in selection["seasons"]],
        "manifest",
        "season identities differ",
    )
    expected = {("coverage", None, None)}
    for row, chosen in zip(manifest["seasons"], selection["seasons"]):
        games = row["selected_game_ids"]
        records.require(
            len(games) == len(set(games))
            and bool(games)
            and all(gid[:4] + str(int(gid[:4]) + 1) == row["season"] for gid in games),
            "manifest",
            "duplicate or cross-season selected key",
        )
        records.require(
            manifest["purpose"] != "real" or row["inventory_games"] == 1312,
            "manifest",
            "real season inventory must contain 1,312 games",
        )
        records.require(
            row["inventory_games"] >= len(games),
            "manifest",
            "selected games exceed inventory",
        )
        records.require(
            set(games) == set(chosen["game_ids"])
            if chosen["game_ids"] is not None
            else len(games) == row["inventory_games"],
            "manifest",
            "selected membership differs",
        )
        expected.add(("people", row["season"], None))
        expected.update(("game", row["season"], gid) for gid in games)
    keys = [(row["kind"], row["season"], row["game_id"]) for row in manifest["files"]]
    records.require(
        len(keys) == len(set(keys)) and set(keys) == expected,
        "manifest/files",
        "extra, missing or duplicate member",
    )
    paths = [row["path"] for row in manifest["files"]]
    records.require(
        len(paths) == len(set(paths))
        and "selection.json" not in paths
        and "manifest.json" not in paths,
        "manifest/files",
        "duplicate or reserved member path",
    )
    identities = {}
    for item in manifest["inputs"]:
        records.require(
            item["path"] not in identities
            or identities[item["path"]] == item["sha256"],
            "manifest/inputs",
            "one input path has conflicting identities",
        )
        identities[item["path"]] = item["sha256"]
    for chosen in selection["seasons"]:
        if manifest["purpose"] == "real":
            expected_path, expected_hash = REAL_CORPORA[chosen["season"]]
            records.require(
                chosen["sha256"] == expected_hash
                and identities.get(expected_path) == expected_hash,
                "manifest/inputs",
                "real provenance differs from frozen 03n identity",
            )
    for row in manifest["files"]:
        _member_path(directory, row["path"])
        records.require(
            len(row["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["sha256"]),
            "manifest/files",
            "invalid member digest",
        )
    for value in manifest["resources"].values():
        records.require(value >= 0, "manifest/resources", "negative resource value")


def read_prepared(path, expected_purpose):
    """validate completion and selection without reopening original inputs."""
    path = Path(path).resolve()
    directory = path if path.is_dir() else path.parent
    manifest = _read(path / "manifest.json" if path.is_dir() else path)
    records.require(
        expected_purpose in ("real", "fixture"), "manifest", "invalid expected purpose"
    )
    records.require(
        type(manifest) is dict and manifest.get("purpose") == expected_purpose,
        "manifest",
        "preparation purpose differs",
    )
    selection = _selection(_read(directory / "selection.json"))
    records.require(
        type(manifest.get("selection")) is dict
        and manifest["selection"].get("sha256") == _sha(directory / "selection.json"),
        "manifest",
        "copied selection digest differs",
    )
    _validate_manifest(manifest, directory, selection)
    prepared = PreparedManifest(manifest)
    prepared.directory = directory
    return prepared


def _read_member(manifest, kind, season=None, game_id=None):
    records.require(
        isinstance(manifest, PreparedManifest),
        "prepared",
        "use read_prepared before consuming members",
    )
    found = [
        row
        for row in manifest["files"]
        if (row["kind"], row["season"], row["game_id"]) == (kind, season, game_id)
    ]
    records.require(len(found) == 1, "prepared", "member not selected")
    row = found[0]
    path = _member_path(manifest.directory, row["path"])
    records.require(_sha(path) == row["sha256"], str(path), "member digest differs")
    value = _read(path)
    _validate_evidence_inputs(value, manifest)
    return value


def _validate_evidence_inputs(value, manifest):
    identities = {(item["path"], item["sha256"]) for item in manifest["inputs"]}

    def visit(item):
        if isinstance(item, dict):
            if "input_ref" in item:
                reference = item["input_ref"]
                records.require(
                    type(reference) is dict
                    and set(reference) == {"path", "sha256"}
                    and (reference["path"], reference["sha256"]) in identities,
                    "prepared/evidence",
                    "source locator is not bound by manifest inputs",
                )
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)


def read_prepared_game(manifest, season, game_id):
    value = records.validate_game(_read_member(manifest, "game", season, game_id))
    _validate_bound_sources(value, manifest)
    records.require(
        (value["season"], value["game_id"]) == (season, game_id),
        "game",
        "member identity differs",
    )
    return value


def _validate_bound_sources(game, manifest):
    identities = {(item["path"], item["sha256"]) for item in manifest["inputs"]}
    paths = {item["path"] for item in manifest["inputs"]}
    sources = {row["source"]: row for row in game["game"]["inputs"]}
    records.require(
        len(sources) == len(game["game"]["inputs"]),
        "game/inputs",
        "duplicate source receipt",
    )
    for row in sources.values():
        path = Path(row["capture_path"])
        promised = (
            row["requested_at"] is not None
            or row["body_sha256"] is not None
            or row["status"] != "unavailable"
        )
        records.require(
            not promised or str(path) in paths,
            "game/inputs",
            "promised receipt is not bound by manifest",
        )
        if row["body_sha256"] is not None:
            records.require(
                (str(path.parent / "body.bin"), row["body_sha256"]) in identities,
                "game/inputs",
                "source body is not bound by manifest",
            )

    def source_fields(item):
        if isinstance(item, dict):
            if set(item) == {"field", "source", "path", "input_index"}:
                index = item["input_index"]
                if item["source"] in REFERENCE_SOURCES:
                    records.require(
                        0 <= index < len(REFERENCE_SOURCES)
                        and REFERENCE_SOURCES[index] == item["source"],
                        "game/source_fields",
                        "reference source input link differs",
                    )
                else:
                    records.require(
                        0 <= index < len(game["game"]["inputs"])
                        and game["game"]["inputs"][index]["source"] == item["source"],
                        "game/source_fields",
                        "game source input link differs",
                    )
            for child in item.values():
                source_fields(child)
        elif isinstance(item, list):
            for child in item:
                source_fields(child)

    source_fields(game)
    for credit in game["credits"] or []:
        for reference in credit["evidence_refs"]:
            bound = sources.get(reference["source"])
            records.require(
                bound is not None
                and all(
                    reference[field] == bound[field]
                    for field in ("capture_path", "body_sha256")
                ),
                "game/credits",
                "credit evidence differs from game source identity",
            )


def read_prepared_people(manifest, season):
    value = _read_member(manifest, "people", season)
    records.validate_people(value)
    records.require(value["season"] == season, "people", "member season differs")
    selected = next(
        row["selected_game_ids"]
        for row in manifest["seasons"]
        if row["season"] == season
    )
    for person in value["people"]:
        records.require(
            all(row["game_id"] in selected for row in person["values"]["sweaters"]),
            "people/sweaters",
            "sweater observation names an unselected game",
        )
    return value


def read_prepared_coverage(manifest):
    value = _read_member(manifest, "coverage")
    records.validate(value, records.Coverage, "coverage")
    records.require(
        [row["season"] for row in value["seasons"]]
        == [row["season"] for row in manifest["seasons"]],
        "coverage",
        "member seasons differ",
    )
    for row, selection in zip(value["seasons"], manifest["seasons"]):
        records.require(
            (row["inventory_games"], row["selected_games"])
            == (selection["inventory_games"], len(selection["selected_game_ids"]))
            and sum(row["game_status_counts"].values()) == row["selected_games"],
            "coverage",
            "selected inventory accounting differs",
        )
        records.require(
            [item["source"] for item in row["game_sources"]] == list(SOURCES)
            and all(
                item["available_games"] + item["unavailable_games"]
                == row["selected_games"]
                for item in row["game_sources"]
            ),
            "coverage/game_sources",
            "source coverage denominator differs",
        )
        event_keys = [(item["kind"], item["outcome"]) for item in row["events"]]
        records.require(
            len(event_keys) == len(set(event_keys)),
            "coverage/events",
            "duplicate event grouping",
        )
        state_keys = [
            tuple(
                item[field]
                for field in (
                    "away_skaters",
                    "home_skaters",
                    "away_goalies",
                    "home_goalies",
                )
            )
            for item in row["time"]
        ]
        records.require(
            len(state_keys) == len(set(state_keys)),
            "coverage/time",
            "duplicate exact state",
        )
        for field in ("order", "score", "frame"):
            records.require(
                sum(row["completeness"][field].values()) == row["selected_games"],
                "coverage/completeness",
                "game completeness denominator differs",
            )
        records.require(
            sum(row["completeness"]["event_context"].values())
            == sum(item["count"] for item in row["events"]),
            "coverage/completeness",
            "event completeness denominator differs",
        )
        attempts = sum(
            item["count"]
            for item in row["events"]
            if item["kind"] in ("goal", "shot-on-goal", "missed-shot", "blocked-shot")
        )
        for field in ("immediate_stop", "reattempt"):
            records.require(
                sum(row["completeness"][field].values()) == attempts,
                "coverage/completeness",
                "attempt completeness denominator differs",
            )
        for item in row["time"]:
            records.require(
                item["physical_seconds"]
                == item["included_seconds"] + item["excluded_seconds"]
                and item["team_seconds"] == 2 * item["included_seconds"]
                and item["skater_slot_seconds"]
                == (item["away_skaters"] + item["home_skaters"])
                * item["included_seconds"]
                and item["goalie_slot_seconds"]
                == (item["away_goalies"] + item["home_goalies"])
                * item["included_seconds"],
                "coverage",
                "physical/team/slot accounting differs",
            )
    return value
